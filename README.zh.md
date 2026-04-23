# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

[system-agents-template](https://github.com/southglory/system-agents-template) 的官方插件集合。

每个插件位于独立的子目录中，独立分发。用户只挑选自己需要的插件。

## 🚀 一行安装（通过模板安装器）

不直接克隆本仓库 —— 模板的 `install.sh` 会读取这里的插件索引，并将所选插件复制到你的项目：

滚动（始终跟随 `main`）:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

固定到稳定 Release（推荐以便重现）:

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


当安装器询问要安装哪些插件时，选择 `discord-huddle`（或其他列出的插件）。

## 可用插件

| 目录 | 简介 | 状态 |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | 基于 Discord 的团队聊天 + 追踪型会议纪要 | ✅ 已发布 (`discord-huddle-v0.1.0`) |
| `unity-gamedev/` | Unity CLI 构建 → GitHub Release 发布 | 🚧 计划中 |

打开每个插件文件夹查看各自的 README 获取详细安装说明。

## 安装模型

插件通过文件复制（`cp -r`）安装，不使用包管理器（pip/npm）。插件文件直接合并到你的项目树中，因此托管式安装由模板的 `install.sh` 负责：

```bash
# 1. 克隆本仓库（安装器自动完成）
git clone https://github.com/southglory/system-agents-plugins.git

# 2. 将所需插件复制到你的项目（安装器自动完成）
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. 注册 Claude Code 技能（安装器自动完成）
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. 安装 Python 依赖
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

手动 `cp -r` 流程仅作为高级用户的备用路径；推荐使用安装器。

## 版本管理

每个插件独立发布。标签格式：`<插件名>-vX.Y.Z`。

- `discord-huddle-v0.1.0` — 首次公开发布
- `unity-gamedev-v0.1.0` — 计划中

整个仓库没有统一版本号。模板标签（`v2.x.x`）与插件标签永不冲突。

## 组合插件

插件设计为独立工作，但部分组合效果更佳。每个插件 README 都应按 [`CONTRIBUTING.md`](CONTRIBUTING.md) 约定列出组合矩阵。跨插件的可复用组合存放在 [`recipes/`](recipes/)。

## 兼容性

- Claude Code（斜杠技能系统）
- system-agents-template v2.x 及以上
- Python ≥ 3.10
- Windows / macOS / Linux

部分插件还有额外要求（例如 discord-huddle 需要 Discord Bot Token）。

## 许可证

[MIT](LICENSE) —— 与 system-agents-template 相同。

## 贡献

- 缺陷报告与反馈：GitHub Issues
- 新插件：参照 [`CONTRIBUTING.md`](CONTRIBUTING.md) 中的结构约定

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
