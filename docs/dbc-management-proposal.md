# 魔兽世界DBC文件管理方案

> **版本**: v1.1  
> **日期**: 2026-06-06  
> **目标**: 建立规范的DBC文件管理体系，实现GitHub远程仓库托管，便于团队协作与持续维护
>
> **v1.1 变更说明**: 模型文件（creature）与图标资源（interface）体积过大（合计~983MB，29,000+文件），不纳入Git仓库管理，改为通过 **GitHub Release附件 + 国内网盘** 分发。仓库内通过 `assets-manifest.json` 维护资源索引与版本对应关系。

---

## 一、现状分析

### 1.1 项目当前结构

```
patch_project_lokta/
├── .git/                   # 本地Git仓库
├── .gitignore              # 忽略规则（排除MPQ、creature、interface）
├── DBFilesClient/          # DBC二进制文件（部分被Git追踪）
│   ├── Achievement.dbc
│   ├── Achievement_Criteria.dbc
│   ├── CharTitles.dbc
│   ├── CreatureDisplayInfo.dbc
│   ├── CreatureModelData.dbc
│   ├── CurrencyCategory.dbc
│   ├── CurrencyTypes.dbc
│   ├── Item.dbc
│   ├── ItemDisplayInfo.dbc
│   ├── ItemExtendedCost.dbc
│   ├── Map.dbc
│   ├── MapDifficulty.dbc
│   ├── ScalingStatDistribution.dbc
│   ├── ScalingStatValues.dbc
│   ├── Spell.dbc
│   └── SpellIcon.dbc
├── creature/               # 自定义坐骑/生物模型资源（~802MB，3,380文件）
│                           # 【不纳入Git，通过Release/网盘分发】
├── interface/              # 界面图标资源（~181MB，25,845文件）
│   ├── icon_inv.txt        # 【不纳入Git，通过Release/网盘分发】
│   ├── icon_spell.txt
│   └── icons/
└── src_data_csv/           # CSV源数据（未入Git）
    ├── Achievement.csv
    ├── CreatureDisplayInfo.csv
    ├── CreatureModelData.csv
    ├── Item.csv
    ├── ItemDisplayInfo.csv
    ├── Spell.csv
    └── SpellIcon.csv
```

### 1.2 资源规模分析

| 资源目录 | 大小 | 文件数 | 主要文件类型 |
|:---|:---|:---|:---|
| `creature/` | **802 MB** | 3,380 | .m2, .skin, .blp, .anim, .phys |
| `interface/` | **181 MB** | 25,845 | .blp, .txt |
| **合计** | **~983 MB** | **~29,225** | — |

### 1.3 已识别问题

| 问题编号 | 问题描述 | 当前影响 |
|:---:|:---|:---|
| P1 | **Git管理范围不完整** — creature、interface、src_data_csv 被排除在版本控制外 | 源码数据无版本历史，丢失后无法恢复；大资源无版本对应关系 |
| P2 | **目录结构不符合开源规范** — 缺乏README、LICENSE、docs、tools等标准目录 | 项目可维护性差，新成员难以快速上手 |
| P3 | **无远程仓库** — 仅有本地Git记录 | 单点故障风险高，无法跨机器协作，无备份 |
| P4 | **二进制DBC直接入仓** — DBC作为二进制文件被Git直接管理 | 提交记录膨胀，diff不可读，冲突难以解决 |
| P5 | **缺乏构建流程** — CSV到DBC的转换依赖手动操作 | 容易出错，无法复现，无法审计变更 |
| P6 | **缺少文档与规范** — 无贡献指南、变更记录、版本说明 | 协作成本高，变更原因不可追溯 |
| P7 | **大资源管理缺失** — 983MB资源无版本化分发机制 | 新成员无法快速获取完整资源，版本对应混乱 |

---

## 二、方案总体设计

### 2.1 核心原则

1. **源码即真理（Source of Truth）**：以**CSV文本文件**作为唯一可编辑的源码，DBC二进制文件作为**构建产物**
2. **Git友好**：所有人类可读的元数据、配置、文档均用文本格式，确保Git diff/blame有效
3. **大文件外置**：二进制资源（~983MB模型/图标）**不进入Git仓库**，通过 **GitHub Release附件 + 网盘镜像** 分发
4. **可复现构建**：提供自动化脚本，确保任何人都能从CSV重建出一致的DBC
5. **开源就绪**：目录结构、文档、License符合开源社区标准

### 2.2 资源分层管理策略

| 层级 | 内容 | 管理方式 | 理由 |
|:---|:---|:---|:---|
| **核心源码** | `src/csv/*.csv` + schemas | **Git直接追踪** | 文本diff友好，人类可编辑，是主要变更对象 |
| **构建产物** | `build/DBFilesClient/*.dbc` | **Git忽略** | CI自动生成，从CSV可复现 |
| **大型资源** | `creature/` + `interface/` | **Git忽略 + Release分发** | 单文件/总体积远超GitHub限制，29,000+文件用LFS性能极差 |
| **发布包** | `patches/*.mpq` | **Git忽略 + Release分发** | 最终用户分发物，无需版本控制 |
| **资源索引** | `assets-manifest.json` | **Git直接追踪** | 记录资源版本、校验和、下载链接，确保源码与资源版本对应 |

### 2.3 目标架构

```
patch_project_lokta/                 # 根项目
│
├── 📄 README.md                     # 项目说明、快速开始
├── 📄 LICENSE                       # 开源协议（建议MIT或GPL）
├── 📄 CHANGELOG.md                  # 版本变更记录
├── 📄 CONTRIBUTING.md               # 贡献指南
├── 📄 assets-manifest.json          # 资源清单（版本、校验和、下载链接）
│
├── 📁 .github/                      # GitHub配置
│   ├── workflows/                   # CI/CD自动化工作流
│   │   └── release.yml              # 自动构建、打包资源、发布Release
│   ├── PULL_REQUEST_TEMPLATE.md     # PR模板
│   └── ISSUE_TEMPLATE/              # Issue模板
│
├── 📁 docs/                         # 文档中心
│   ├── architecture.md              # 架构设计说明
│   ├── dbc-format-guide.md          # DBC文件格式与字段说明
│   ├── csv-editing-guide.md         # CSV编辑指南
│   ├── workflow.md                  # 工作流规范（分支、评审、发布）
│   └── faq.md                       # 常见问题
│
├── 📁 tools/                        # 构建工具链
│   ├── csv-to-dbc/                  # CSV转DBC转换器
│   │   ├── converter.py             # 主转换脚本
│   │   ├── requirements.txt         # Python依赖
│   │   └── README.md                # 工具使用说明
│   ├── dbc-diff/                    # DBC差异分析工具
│   └── mpq-patcher/                 # MPQ打包工具
│
├── 📁 src/                          # 源码数据（核心资产）
│   ├── csv/                         # CSV源文件（Git直接管理）
│   │   ├── Achievement.csv
│   │   ├── Achievement_Criteria.csv
│   │   ├── CharTitles.csv
│   │   ├── CreatureDisplayInfo.csv
│   │   ├── CreatureModelData.csv
│   │   ├── CurrencyCategory.csv
│   │   ├── CurrencyTypes.csv
│   │   ├── Item.csv
│   │   ├── ItemDisplayInfo.csv
│   │   ├── ItemExtendedCost.csv
│   │   ├── Map.csv
│   │   ├── MapDifficulty.csv
│   │   ├── ScalingStatDistribution.csv
│   │   ├── ScalingStatValues.csv
│   │   ├── Spell.csv
│   │   └── SpellIcon.csv
│   └── schemas/                     # DBC表结构定义（JSON/YAML）
│       ├── Spell.schema.json        # 字段名、类型、约束
│       ├── Item.schema.json
│       └── ...
│
├── 📁 build/                        # 构建输出（Git忽略）
│   └── DBFilesClient/               # 生成的DBC文件
│       ├── Achievement.dbc
│       ├── ...
│       └── Spell.dbc
│
├── 📁 patches/                      # 发布补丁包（Git忽略）
│   └── README.md                    # 补丁列表与安装说明
│
├── 📁 creature/                     # 坐骑模型资源（Git忽略，本地运行时目录）
│   └── ...                          # 从Release/网盘获取
│
├── 📁 interface/                    # 图标资源（Git忽略，本地运行时目录）
│   ├── icon_inv.txt
│   ├── icon_spell.txt
│   └── icons/
│
└── 📄 .gitignore                    # Git忽略规则
```

---

## 三、关键问题解决方案

### 3.1 问题1/7：Git管理范围不完整 + 大资源管理缺失 → CSV源码入仓 + Release资源分发

**方案**：

| 类别 | 内容 | Git管理方式 | 分发方式 |
|:---|:---|:---|:---|
| **核心源码** | `src/csv/*.csv` + `src/schemas/*.json` | **直接追踪** | 随Git仓库克隆 |
| **资源索引** | `assets-manifest.json` | **直接追踪** | 随Git仓库克隆 |
| **构建产物** | `build/DBFilesClient/*.dbc` | **Git忽略** | CI自动生成，Release附件 |
| **大型资源** | `creature/`, `interface/` | **Git忽略** | GitHub Release zip + 网盘镜像 |
| **发布包** | `patches/*.mpq` | **Git忽略** | GitHub Release附件 |

**迁移步骤**：
1. 将现有 `src_data_csv/` 迁移至 `src/csv/`
2. 编写 `assets-manifest.json` 记录资源元数据
3. 更新 `.gitignore` 排除所有二进制资源与构建产物

```gitignore
# ============================================
# 魔兽世界DBC补丁项目 - Git忽略规则
# ============================================

# --- 大文件资源（通过GitHub Release/网盘分发，不进入仓库） ---
/creature
/interface

# --- 构建产物（通过CI自动生成） ---
/build
/DBFilesClient

# --- 发布包 ---
*.mpq
*.zip
*.7r
*.rar

# --- 运行时/临时文件 ---
*.tmp
*.temp
*.bak
*.log
*.cache

# --- IDE与编辑器配置 ---
/.vscode
/.idea
*.swp
*.swo
*~

# --- Python虚拟环境与缓存 ---
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/lib/
venv/
.env

# --- OS生成的文件 ---
.DS_Store
Thumbs.db
desktop.ini
```

**`assets-manifest.json` 设计**：

```json
{
  "schema_version": "1.0",
  "last_updated": "2026-06-06",
  "project": {
    "name": "WoW DBC Patch Project - Assets",
    "description": "坐骑模型与图标资源清单（不纳入Git仓库，通过Release/网盘分发）"
  },
  "assets": {
    "creature": {
      "description": "自定义坐骑与生物模型资源",
      "local_path": "creature/",
      "total_size_mb": 802,
      "file_count": 3380,
      "file_types": { "blp": 1609, "anim": 823, "skin": 690, "m2": 190, "M2": 41, "BLP": 18, "phys": 9 },
      "mount_count": 170,
      "download": {
        "github_release": "https://github.com/<username>/<repo>/releases/latest",
        "baidu_pan": null,
        "quark": null
      }
    },
    "interface": {
      "description": "界面图标资源",
      "local_path": "interface/",
      "total_size_mb": 181,
      "file_count": 25845,
      "download": {
        "github_release": "https://github.com/<username>/<repo>/releases/latest",
        "baidu_pan": null,
        "quark": null
      }
    }
  }
}
```

### 3.2 问题2：目录结构不符合开源规范 → 标准化重组

**方案**：按照上述"目标架构"进行目录重组。关键改进点：

| 新增目录/文件 | 作用 |
|:---|:---|
| `README.md` | 项目一句话介绍 + 功能特性 + 快速开始 + 资源下载指引 |
| `LICENSE` | 法律授权，建议采用 **MIT** 或 **GPL-3.0** |
| `CHANGELOG.md` | 按 [Keep a Changelog](https://keepachangelog.com/) 格式记录每个版本的变更 |
| `CONTRIBUTING.md` | 告诉贡献者如何提Issue、提PR、编码规范 |
| `assets-manifest.json` | 资源版本索引，确保源码与资源版本对应 |
| `docs/` | 所有技术文档集中存放 |
| `tools/` | 工具脚本集中存放，带独立README |
| `src/` | 源码数据与结构定义分离 |
| `.github/` | Issue/PR模板、CI工作流 |

### 3.3 问题3：无远程仓库 → GitHub托管 + 备份策略

**方案**：

#### 步骤1：创建GitHub仓库

1. 登录 GitHub，新建仓库（如 `wow-dbc-patch`）
2. 不勾选 "Initialize this repository with a README"（本地已有仓库）
3. 记录仓库地址：`https://github.com/<your-username>/wow-dbc-patch.git`

#### 步骤2：关联远程仓库并推送

```bash
# 在本地仓库根目录执行
cd patch_project_lokta

# 添加远程仓库（建议用SSH）
git remote add origin git@github.com:<your-username>/wow-dbc-patch.git

# 若当前分支为master，可重命名为main（GitHub默认）
git branch -M main

# 首次推送（注意：creature/ 和 interface/ 已被.gitignore排除，不会上传）
git push -u origin main
```

> ⚠️ **重要**：由于 `.gitignore` 已排除 `creature/` 和 `interface/`，首次推送的仓库体积仅包含文本文件（< 10MB），推送到GitHub无压力。

#### 步骤3：启用GitHub功能

| 功能 | 配置建议 |
|:---|:---|
| **Branch Protection** | 保护 `main` 分支：要求PR评审、要求状态检查通过、禁止强制推送 |
| **GitHub Actions** | 启用免费Runner，配置自动构建与Release发布 |
| **GitHub Issues** | 开启，用于Bug跟踪和功能请求 |
| **GitHub Discussions** | 可选开启，用于社区讨论 |

#### 步骤4：资源上传至Release

1. 在本地将 `creature/` 和 `interface/` 分别打包为zip
2. 打Tag触发GitHub Actions自动打包，或手动上传至Release
3. 同时上传至国内网盘（百度网盘/夸克），在 `assets-manifest.json` 和 README 中提供链接

#### 步骤5：本地备份策略

- GitHub仓库本身即为备份（仅文本文件，体积小）
- 资源文件zip保留本地副本 + 网盘备份
- 可选：设置Gitee码云镜像仓库（仅同步文本文件）

### 3.4 问题4：二进制DBC直接入仓 → CSV源码 + 自动构建

**方案**：DBC二进制文件不再直接提交到Git仓库，改为：

```
开发者编辑 CSV → 本地/CI 运行转换脚本 → 生成 DBC → 测试验证 → 随Release发布
```

#### 转换工具设计（`tools/csv-to-dbc/`）

```python
# tools/csv-to-dbc/converter.py 功能概要
"""
功能：
1. 读取 src/schemas/*.json 获取表结构定义（字段名、类型、长度）
2. 读取 src/csv/*.csv 数据
3. 按WoW DBC格式规范生成二进制 .dbc 文件到 build/DBFilesClient/
4. 输出构建报告（行数、变更摘要、校验值）

用法：
    python converter.py --schema src/schemas/Spell.schema.json \
                        --input src/csv/Spell.csv \
                        --output build/DBFilesClient/Spell.dbc
    
    # 批量构建
    python converter.py --all --src src/csv/ --schemas src/schemas/ --out build/DBFilesClient/
"""
```

> **说明**：若已有现成的转换工具（如WDBX Editor命令行、MyWowTools等），可直接封装调用，无需从零开发。

#### 本地工作流

```bash
# 1. 编辑CSV
vim src/csv/Spell.csv

# 2. 构建DBC
python tools/csv-to-dbc/converter.py --all

# 3. 本地测试（将 build/DBFilesClient/ 复制到客户端/服务器）
# ...

# 4. 提交CSV变更（不提交DBC）
git add src/csv/Spell.csv
git commit -m "fix(Spell): 修正强化法术反射作用人数与说明不一致

- 技能59088和59089的作用人数修正为与技能描述一致
- 关联Issue: #42"
```

### 3.5 问题5：缺乏构建流程 → CI/CD自动化

#### CI自动构建与Release发布（`.github/workflows/release.yml`）

```yaml
name: Build and Release

on:
  push:
    branches: [main, master]
    tags: ['v*']
  pull_request:
    branches: [main, master]

jobs:
  validate:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Validate CSV format
        run: |
          # TODO: 接入 csv-to-dbc/validate.py
          echo "CSV校验通过（待接入转换工具后启用完整校验）"
      - name: Check assets-manifest.json
        run: python -m json.tool assets-manifest.json > /dev/null

  build:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      # --- DBC构建（待接入转换工具后启用） ---
      # - uses: actions/setup-python@v5
      #   with: { python-version: '3.11' }
      # - run: pip install -r tools/csv-to-dbc/requirements.txt
      # - run: python tools/csv-to-dbc/converter.py --all

      - name: Pack creature assets
        run: |
          if [ -d "creature" ] && [ "$(ls -A creature)" ]; then
            zip -r creature-${{ github.ref_name }}.zip creature/
          fi

      - name: Pack interface assets
        run: |
          if [ -d "interface" ] && [ "$(ls -A interface)" ]; then
            zip -r interface-${{ github.ref_name }}.zip interface/
          fi

      - name: Generate checksums
        run: |
          if ls *.zip 1> /dev/null 2>&1; then
            sha256sum *.zip > assets-${{ github.ref_name }}.sha256
          fi

      - uses: actions/upload-artifact@v4
        with:
          name: patch-assets-${{ github.ref_name }}
          path: |
            build/DBFilesClient/
            *.zip
            *.sha256
          retention-days: 30

  release:
    runs-on: ubuntu-latest
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    permissions: { contents: write }
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: patch-assets-${{ github.ref_name }}
          path: dist/
      - uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 3.6 问题6：缺少文档与规范 → 文档体系化

已在2.2目标架构中规划 `docs/` 目录。文档编写优先级：

| 优先级 | 文档 | 说明 |
|:---:|:---|:---|
| P0 | `README.md` | 项目门面，必须第一时间完成 |
| P0 | `docs/workflow.md` | 分支策略、提交流程、发布流程 |
| P1 | `docs/csv-editing-guide.md` | 如何安全地编辑CSV、常见陷阱 |
| P1 | `CONTRIBUTING.md` | 降低外部贡献者门槛 |
| P1 | `CHANGELOG.md` | 从git历史整理出初始版本记录 |
| P2 | `docs/dbc-format-guide.md` | 各DBC表字段含义、关联关系 |
| P2 | `docs/architecture.md` | 整体架构、数据流、工具链说明 |

---

## 四、Git工作流规范

### 4.1 分支模型（GitHub Flow简化版）

```
main .............................................. 稳定分支，始终可构建
  │
  ├── feature/add-mount-xxx ........................ 新功能分支
  │   └── PR → Review → Merge ──┘
  │
  ├── fix/spell-reflect-target-count ............... Bug修复分支
  │   └── PR → Review → Merge ──┘
  │
  └── release/v1.2.0 ............................... 发布分支（可选）
      └── Tag v1.2.0 → GitHub Release
```

| 分支名 | 用途 | 保护规则 |
|:---|:---|:---|
| `main` | 稳定代码，随时可发布 | 禁止直接推送，必须通过PR合并 |
| `feature/*` | 新功能开发 | 无 |
| `fix/*` | Bug修复 | 无 |
| `release/*` | 版本发布准备 | 无 |

### 4.2 提交信息规范（Conventional Commits）

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | 含义 | 示例 |
|:---|:---|:---|
| `feat` | 新功能 | `feat(Spell): 新增商栈币兑换价格配置` |
| `fix` | Bug修复 | `fix(Item): 修正原始火刃豹图标显示异常` |
| `docs` | 仅文档变更 | `docs: 更新CSV编辑指南` |
| `chore` | 构建/工具链 | `chore(tools): 升级csv-to-dbc转换器` |
| `refactor` | 代码重构 | `refactor(schemas): 统一字段命名规范` |

**Scope约定**：对应修改的DBC表名（`Spell`、`Item`、`CreatureDisplayInfo`等），或多表用`*`。

### 4.3 发布流程

1. 在 `main` 分支确认所有变更已合并并通过CI
2. 更新 `CHANGELOG.md` 和 `assets-manifest.json`（如有资源变更）
3. 打Tag并推送：
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0 - 新增坐骑与法术修复"
   git push origin v1.2.0
   ```
4. GitHub Actions 自动：
   - 构建DBC（如有转换工具）
   - 打包 `creature/` 和 `interface/` 为zip
   - 生成SHA256校验文件
   - 创建Release并上传所有附件
5. 手动补充：
   - Release说明（中文）
   - 国内网盘镜像链接（更新 `assets-manifest.json` 后提交）

---

## 五、实施路线图

### Phase 1：基础设施（建议1周内完成）

| 序号 | 任务 | 产出 |
|:---:|:---|:---|
| 1.1 | 注册GitHub账号，创建远程仓库 | 仓库地址 |
| 1.2 | 配置SSH Key，推送现有代码到GitHub | 远程main分支（仅文本文件，<10MB） |
| 1.3 | 启用Branch Protection | 分支保护规则 |
| 1.4 | 更新 `.gitignore` | 排除所有二进制资源与构建产物 |

### Phase 2：目录重组与资源索引（建议1周内完成）

| 序号 | 任务 | 产出 |
|:---:|:---|:---|
| 2.1 | 创建标准目录结构（docs, tools, src, build, patches, .github） | 新目录树 |
| 2.2 | 迁移 `src_data_csv/` → `src/csv/` | CSV文件就位 |
| 2.3 | 编写 `assets-manifest.json` | 资源索引文件 |
| 2.4 | 编写基础文档（README, LICENSE, CHANGELOG, CONTRIBUTING） | 文档文件 |
| 2.5 | 配置 `.github/workflows/release.yml` | CI工作流 |
| 2.6 | 首次手动打包资源并上传GitHub Release | creature-v*.zip, interface-v*.zip |
| 2.7 | 上传资源至国内网盘，更新README下载链接 | 网盘链接 |

### Phase 3：工具链建设（建议2周内完成）

| 序号 | 任务 | 产出 |
|:---:|:---|:---|
| 3.1 | 调研并选定CSV→DBC转换方案（现有工具或自研） | 技术选型决定 |
| 3.2 | 开发/封装转换脚本 `tools/csv-to-dbc/` | 可运行的转换器 |
| 3.3 | 开发CSV校验脚本 | 校验规则 |
| 3.4 | 更新CI工作流，启用自动DBC构建 | 完整的release.yml |
| 3.5 | 测试完整工作流：编辑CSV → 提交 → CI构建 → 下载DBC+资源 | 端到端验证通过 |

### Phase 4：规范化运营（持续）

| 序号 | 任务 | 产出 |
|:---:|:---|:---|
| 4.1 | 完善技术文档（dbc-format-guide, csv-editing-guide, architecture） | 完整docs |
| 4.2 | 为历史提交补充分支和PR记录（后续新变更严格执行） | 规范流程落地 |
| 4.3 | 建立Issue标签体系（bug, enhancement, documentation等） | GitHub标签 |
| 4.4 | 设置Gitee等国内镜像仓库（仅文本文件） | 备份仓库 |
| 4.5 | 邀请协作者，推广项目 | 团队协作启动 |

---

## 六、大文件管理方案对比（决策记录）

### 为什么不用 Git LFS？

| 维度 | Git LFS 免费版 | Git LFS 付费版 | Release附件（选中方案） |
|:---|:---|:---|:---|
| **存储成本** | 1GB上限（983MB已接近） | $5/月 = 50GB | **完全免费** |
| **带宽成本** | 1GB/月 | $5包50GB/月 | **完全免费** |
| **29,000+文件体验** | 极差（每个文件一个LFS指针） | 极差 | **无影响** |
| **国内下载速度** | 慢（GitHub CDN） | 慢 | **可配网盘镜像** |
| **仓库clone速度** | 慢（需拉取LFS对象） | 慢 | **clone仅文本文件（<10MB）** |
| **版本历史** | 有（但占用存储配额） | 有 | 按Release版本 |
| **与CI集成** | 复杂 | 复杂 | **简单直接** |

### 为什么不用 Git Submodule？

Git Submodule要求子模块也是一个Git仓库，资源文件仍然面临同样的Git大文件限制，无法解决根本问题。

### 为什么不用独立资源仓库？

即使创建独立的 `wow-patch-assets` 仓库，仍然需要用Git LFS管理983MB资源，面临相同的配额和性能问题，且增加维护两个仓库的复杂度。

---

## 七、预期收益

| 维度 | 改善前 | 改善后 |
|:---|:---|:---|
| **版本控制** | 部分DBC入仓，creature/interface/csv被忽略 | CSV源码与资源索引纳入版本控制，历史可追溯 |
| **协作效率** | 无远程仓库，单机器工作 | GitHub托管，多人PR协作，Code Review |
| **可维护性** | 目录混乱，无文档 | 标准开源结构，文档齐全，新人可快速上手 |
| **构建可靠性** | 手动转换DBC，易出错 | 自动化构建，CI校验，发布可复现 |
| **数据安全** | 本地单点，丢失风险高 | 文本仓库多地备份（GitHub + 镜像）；资源zip本地+网盘备份 |
| **变更审计** | DBC二进制diff不可读 | CSV文本diff清晰，变更原因通过提交信息记录 |
| **资源分发** | 无版本化分发机制，新成员无法获取资源 | Release附件 + 网盘镜像，版本对应清晰 |

---

## 八、附录

### A. 推荐工具清单

| 用途 | 工具 | 备注 |
|:---|:---|:---|
| DBC编辑/查看 | WDBX Editor, MyDBCEditor | GUI工具，适合调试 |
| CSV编辑 | VS Code + Excel Viewer插件, Excel | 注意保存为UTF-8无BOM |
| MPQ打包 | MPQ Editor, ladik's MPQ Editor | 制作最终补丁包 |
| Git客户端 | Git Bash, GitHub Desktop, VS Code内置 | 任选 |
| 资源压缩 | 7-Zip, WinRAR | 打包creature/interface为zip |

### B. 参考链接

- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Documentation](https://docs.github.com/cn/actions)
- [GitHub Release 附件限制](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases#storage-and-bandwidth-quotas)
- [WoWDev Wiki - DBC](https://wowdev.wiki/DBC)

---

*本文档由项目维护团队制定，后续可根据实际执行情况进行迭代调整。*
