#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate-schemas.py
从 WoWDBDefs 的 .dbd 定义文件中提取指定版本的字段结构，
生成 src/schemas/*.json 供 DBC 编辑和 CSV 导出工具使用。

用法:
    python script/generate-schemas.py
    python script/generate-schemas.py --version 3.3.5.12340
    python script/generate-schemas.py --table Spell

依赖:
    无（纯标准库）

数据来源:
    third-party/WoWDBDefs/definitions/*.dbd
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path


# =============================================================================
# 配置
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DBD_DIR = PROJECT_ROOT / "third-party" / "WoWDBDefs" / "definitions"
SCHEMAS_DIR = PROJECT_ROOT / "src" / "schemas"
DBC_DIR = PROJECT_ROOT / "src" / "dbc"

# 默认目标版本（WotLK 3.3.5）
DEFAULT_TARGET_VERSION = "3.3.5.12340"

# =============================================================================
# DBD 解析器
# =============================================================================

def parse_build_version(version_str: str) -> tuple:
    """将版本字符串解析为 (major, minor, patch, build) 元组"""
    parts = version_str.strip().split(".")
    return tuple(int(p) for p in parts)


def version_in_range(target: tuple, build_def: str) -> bool:
    """
    检查目标版本是否在 BUILD 定义范围内。
    支持格式:
      BUILD x.x.x.x              (精确匹配)
      BUILD x.x.x.x-y.y.y.y      (范围匹配)
      BUILD a.a.a.a, b.b.b.b     (多个精确匹配)
    """
    # 去掉 "BUILD " 前缀
    content = build_def.replace("BUILD", "", 1).strip()

    # 检查是否是范围 (包含 "-")
    if "-" in content:
        left, right = content.split("-", 1)
        left_ver = parse_build_version(left)
        right_ver = parse_build_version(right)
        return left_ver <= target <= right_ver

    # 检查是否是多个精确版本 (包含 ",")
    if "," in content:
        versions = [v.strip() for v in content.split(",")]
        return any(parse_build_version(v) == target for v in versions)

    # 单个精确版本
    return parse_build_version(content) == target


def parse_column_line(line: str) -> dict:
    """
    解析 COLUMNS 部分的字段定义行。
    格式: type<ForeignTable::ForeignCol> ColumnName? // comment
    返回: {name, type, foreign_table, foreign_column, is_confirmed, comment}
    """
    result = {
        "name": None,
        "type": None,
        "foreign_table": None,
        "foreign_column": None,
        "is_confirmed": True,
        "comment": None,
    }

    # 提取行尾注释
    if "//" in line:
        parts = line.split("//", 1)
        line = parts[0].strip()
        result["comment"] = parts[1].strip()

    # 匹配外键: type<Table::Column> Name
    fk_match = re.match(r"(\w+)<(\w+)::(\w+)>\s+(\S+)", line)
    if fk_match:
        result["type"] = fk_match.group(1)
        result["foreign_table"] = fk_match.group(2)
        result["foreign_column"] = fk_match.group(3)
        result["name"] = fk_match.group(4)
    else:
        # 匹配无外键: type Name
        simple_match = re.match(r"(\w+)\s+(\S+)", line)
        if simple_match:
            result["type"] = simple_match.group(1)
            result["name"] = simple_match.group(2)

    # 检查是否为未确认字段名 (以 ? 结尾)
    if result["name"] and result["name"].endswith("?"):
        result["name"] = result["name"][:-1]
        result["is_confirmed"] = False

    return result


def parse_entry_line(line: str) -> dict:
    """
    解析 BUILD 定义中的字段列表行。
    格式:
      ColumnName
      ColumnName<size>
      ColumnName[array_size]
      ColumnName<size>[array_size]
      $id$ColumnName
      $relation$ColumnName
      $noninline,id$ColumnName
    返回: {name, int_width, is_unsigned, array_size, annotation, comment}
    """
    result = {
        "name": None,
        "int_width": None,
        "is_unsigned": False,
        "array_size": None,
        "annotation": [],
        "comment": None,
    }

    # 提取行尾注释
    if "//" in line:
        parts = line.split("//", 1)
        line = parts[0].strip()
        result["comment"] = parts[1].strip()

    # 提取 annotation: $...$ColumnName
    annot_match = re.match(r"\$([^$]+)\$(.+)", line)
    if annot_match:
        result["annotation"] = [a.strip() for a in annot_match.group(1).split(",")]
        line = annot_match.group(2)

    # 匹配数组大小: Name[size]
    arr_match = re.search(r"\[(\d+)\]$", line)
    if arr_match:
        result["array_size"] = int(arr_match.group(1))
        line = line[:arr_match.start()]

    # 匹配整数宽度: Name<32> 或 Name<u32>
    width_match = re.search(r"<(u?)(\d+)>$", line)
    if width_match:
        result["is_unsigned"] = width_match.group(1) == "u"
        result["int_width"] = int(width_match.group(2))
        line = line[:width_match.start()]

    result["name"] = line.strip()
    return result


def parse_dbd(content: str, target_version: str) -> dict:
    """
    解析 .dbd 文件内容，提取目标版本的字段定义。
    返回: {table_name, version, columns: [{name, type, annotation, array_size, comment, foreign_table, foreign_column}]}
    """
    lines = content.splitlines()
    target = parse_build_version(target_version)

    # 阶段1: 解析 COLUMNS 部分
    columns_def = {}  # name -> column_info
    in_columns = False
    build_sections = []  # [(build_lines, entry_lines)]
    current_build_lines = []
    current_entry_lines = []
    in_build = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            # 空行表示 BUILD 定义之间的分隔
            if in_build and (current_build_lines or current_entry_lines):
                build_sections.append((current_build_lines, current_entry_lines))
                current_build_lines = []
                current_entry_lines = []
                in_build = False
            continue

        if stripped == "COLUMNS":
            in_columns = True
            continue

        if stripped.startswith("BUILD "):
            # 如果当前已在BUILD段落中且已有字段列表，说明这是新段落
            if in_build and current_entry_lines:
                build_sections.append((current_build_lines, current_entry_lines))
                current_build_lines = []
                current_entry_lines = []
            # 否则（仅有build_lines无entry_lines），继续归入同一段落
            # 多个连续BUILD行共享同一个字段列表
            in_columns = False
            in_build = True
            current_build_lines.append(stripped)
            continue

        if stripped.startswith("LAYOUT ") or stripped.startswith("COMMENT "):
            if in_build:
                current_build_lines.append(stripped)
            continue

        # 字段定义行
        if in_columns:
            col = parse_column_line(stripped)
            if col["name"]:
                columns_def[col["name"]] = col
        elif in_build:
            current_entry_lines.append(stripped)

    # 保存最后一个 BUILD 段
    if in_build and (current_build_lines or current_entry_lines):
        build_sections.append((current_build_lines, current_entry_lines))

    # 阶段2: 找到匹配的 BUILD 定义
    matched_entries = None
    for build_lines, entry_lines in build_sections:
        for build_line in build_lines:
            if build_line.startswith("BUILD "):
                if version_in_range(target, build_line):
                    matched_entries = entry_lines
                    break
        if matched_entries is not None:
            break

    if matched_entries is None:
        return None

    # 阶段3: 合并 COLUMNS 定义和 BUILD 字段列表
    fields = []
    for entry_line in matched_entries:
        entry = parse_entry_line(entry_line)
        name = entry["name"]
        if not name:
            continue

        # 从 COLUMNS 定义中获取类型和注释
        col_info = columns_def.get(name, {})

        field = {
            "name": name,
            "type": col_info.get("type", "unknown"),
            "annotation": entry["annotation"],
            "array_size": entry["array_size"],
            "int_width": entry["int_width"],
            "is_unsigned": entry["is_unsigned"],
            "comment": entry["comment"] or col_info.get("comment"),
            "foreign_table": col_info.get("foreign_table"),
            "foreign_column": col_info.get("foreign_column"),
            "is_confirmed": col_info.get("is_confirmed", True),
        }
        fields.append(field)

    return {"columns": fields}


# =============================================================================
# Schema 生成
# =============================================================================

def generate_schema(table_name: str, target_version: str = DEFAULT_TARGET_VERSION) -> dict:
    """为指定表生成JSON schema"""
    dbd_path = DBD_DIR / f"{table_name}.dbd"

    if not dbd_path.exists():
        print(f"  ⚠️  未找到定义文件: {dbd_path}")
        return None

    with open(dbd_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_dbd(content, target_version)

    if parsed is None:
        print(f"  ⚠️  未找到版本 {target_version} 的定义")
        return None

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"{table_name} Schema",
        "description": f"魔兽世界 {table_name}.dbc 字段定义 (版本 {target_version})",
        "source": "https://github.com/wowdev/WoWDBDefs",
        "table_name": table_name,
        "version": target_version,
        "type": "object",
        "properties": {},
        "field_order": [],
    }

    for field in parsed["columns"]:
        name = field["name"]
        schema["field_order"].append(name)

        prop = {
            "type": field["type"],
            "description": field["comment"] or "",
        }

        if field["array_size"]:
            prop["array_size"] = field["array_size"]
        if field["int_width"]:
            prop["int_width"] = field["int_width"]
            prop["is_unsigned"] = field["is_unsigned"]
        if field["foreign_table"]:
            prop["foreign_key"] = {
                "table": field["foreign_table"],
                "column": field["foreign_column"],
            }
        if field["annotation"]:
            prop["annotation"] = field["annotation"]
        if not field["is_confirmed"]:
            prop["is_confirmed"] = False

        schema["properties"][name] = prop

    return schema


def get_project_tables() -> list:
    """获取项目中实际使用的表名（从DBC文件名推断）"""
    tables = []
    if DBC_DIR.exists():
        for dbc_file in sorted(DBC_DIR.glob("*.dbc")):
            tables.append(dbc_file.stem)
    return tables


def main():
    parser = argparse.ArgumentParser(
        description="从 WoWDBDefs 生成 DBC 字段 Schema"
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_TARGET_VERSION,
        help=f"目标游戏版本 (默认: {DEFAULT_TARGET_VERSION})",
    )
    parser.add_argument(
        "--table",
        help="仅生成指定表的schema（默认: 项目DBC目录下的所有表）",
    )
    parser.add_argument(
        "--output",
        default=str(SCHEMAS_DIR),
        help=f"输出目录 (默认: {SCHEMAS_DIR})",
    )
    parser.add_argument(
        "--list-all",
        action="store_true",
        help="列出 WoWDBDefs 中所有可用的表",
    )
    args = parser.parse_args()

    # 检查 WoWDBDefs 子模块是否存在
    if not DBD_DIR.exists():
        print(f"❌ 错误: 未找到 WoWDBDefs 子模块")
        print(f"   请运行: git submodule update --init --recursive")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 列出所有可用表
    if args.list_all:
        print("WoWDBDefs 中可用的表定义:")
        for dbd_file in sorted(DBD_DIR.glob("*.dbd")):
            print(f"  {dbd_file.stem}")
        return

    # 确定要生成的表
    if args.table:
        tables = [args.table]
    else:
        tables = get_project_tables()
        if not tables:
            print(f"⚠️  未在 {DBC_DIR} 找到DBC文件，请指定 --table 参数")
            sys.exit(1)

    print(f"目标版本: {args.version}")
    print(f"输出目录: {output_dir}")
    print(f"生成表数: {len(tables)}")
    print("-" * 50)

    generated = 0
    failed = 0

    for table_name in tables:
        print(f"生成: {table_name}.schema.json ...", end=" ")
        schema = generate_schema(table_name, args.version)

        if schema:
            output_path = output_dir / f"{table_name}.schema.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
            print(f"✅ ({len(schema['field_order'])} 个字段)")
            generated += 1
        else:
            print("❌ 失败")
            failed += 1

    print("-" * 50)
    print(f"完成: 成功 {generated} 个, 失败 {failed} 个")
    print(f"输出: {output_dir}")


if __name__ == "__main__":
    main()
