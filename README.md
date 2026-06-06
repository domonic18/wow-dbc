# WoW DBC 补丁项目

> 魔兽世界 3.3.5 自定义DBC数据补丁项目

## 项目简介

本项目用于管理和维护魔兽世界 WotLK (3.3.5) 客户端的自定义DBC数据补丁，包括：

- **自定义坐骑** — 新增多种坐骑模型与数据配置
- **法术修复** — 修正技能数值、效果与描述不一致的问题
- **物品与图标** — 自定义物品数据与界面图标资源

## 仓库范围

本仓库仅管理**可版本控制的文本源码**，不包含大型二进制资源文件：

| 内容 | 是否入仓 | 说明 |
|:---|:---:|:---|
| `src/csv/*.csv` | ✅ | DBC源数据（核心资产） |
| `tools/` | ✅ | 构建工具与脚本 |
| `docs/` | ✅ | 项目文档 |
| `creature/` | ❌ | 坐骑模型资源（~802MB），通过Release/网盘分发 |
| `interface/` | ❌ | 图标资源（~181MB），通过Release/网盘分发 |
| `build/DBFilesClient/*.dbc` | ❌ | DBC构建产物，通过CI自动生成 |
| `*.mpq` | ❌ | 最终补丁包，通过Release分发 |

## 目录结构

```
patch_project_lokta/
├── 📁 .github/workflows/      # GitHub Actions CI/CD 工作流
├── 📁 docs/                   # 项目文档
│   └── dbc-management-proposal.md
├── 📁 src_data_csv/           # CSV源数据（待迁移至 src/csv/）
│   ├── Achievement.csv
│   ├── CreatureDisplayInfo.csv
│   ├── Item.csv
│   ├── Spell.csv
│   └── ...
├── 📄 assets-manifest.json    # 资源清单（版本、校验和、下载链接）
├── 📄 .gitignore              # Git忽略规则
└── 📄 README.md               # 本文件
```

## 快速开始

### 1. 克隆源码仓库

```bash
git clone https://github.com/<username>/<repo>.git
cd patch_project_lokta
```

### 2. 下载资源文件

由于 `creature/` 和 `interface/` 为大型二进制资源，**不纳入Git管理**，请通过以下方式获取：

#### 方式A：GitHub Release（推荐，海外网络）

访问 [Releases页面](https://github.com/<username>/<repo>/releases)，下载对应版本的：
- `creature-v*.zip` — 坐骑模型资源
- `interface-v*.zip` — 图标资源

解压到项目根目录：
```bash
unzip creature-v1.0.0.zip
unzip interface-v1.0.0.zip
```

#### 方式B：国内网盘（推荐，国内网络）

- **百度网盘**：`https://pan.baidu.com/s/xxxx`（待补充）
- **夸克网盘**：`https://pan.quark.cn/xxxx`（待补充）

### 3. 本地目录结构（完整）

```
patch_project_lokta/
├── 📁 src_data_csv/           # CSV源数据 ← Git管理
├── 📁 creature/               # 坐骑模型 ← 从Release/网盘获取
├── 📁 interface/              # 图标资源 ← 从Release/网盘获取
└── 📁 build/                  # 构建输出（运行时生成）
    └── DBFilesClient/         # 生成的DBC文件
```

### 4. 构建DBC（待接入转换工具）

```bash
# 安装Python依赖
pip install -r tools/csv-to-dbc/requirements.txt

# 构建所有DBC
python tools/csv-to-dbc/converter.py --all

# 输出到 build/DBFilesClient/
```

## 资源清单

详见 [`assets-manifest.json`](./assets-manifest.json)，包含：

| 资源 | 大小 | 文件数 | 说明 |
|:---|:---|:---|:---|
| `creature/` | ~802 MB | 3,380 | 约170种自定义坐骑模型（.m2/.skin/.blp/.anim） |
| `interface/` | ~181 MB | 25,845 | 图标文件（.blp）及索引（icon_inv.txt / icon_spell.txt） |

## 变更记录

详见 [GitHub Releases](https://github.com/<username>/<repo>/releases)。

主要变更：

- **v1.x** — 修复强化法术反射作用人数与说明不一致
- **v1.x** — 修复屠魔者的破邪尖啸者在太阳之井可以飞行的问题
- **v1.x** — 修复狡狐魔使在海加尔山可以飞行的问题
- **v1.x** — 增加商栈币的候选价格列表

## 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 编辑 `src_data_csv/*.csv` 文件
4. 提交变更（遵循 Conventional Commits 规范）
5. 发起 Pull Request

## 技术文档

- [`docs/dbc-management-proposal.md`](./docs/dbc-management-proposal.md) — DBC文件管理方案

## 许可证

[MIT](LICENSE) 或 [GPL-3.0](LICENSE)（待确定）

---

*本项目为学习和研究用途，所有魔兽世界相关素材版权归 Blizzard Entertainment 所有。*
