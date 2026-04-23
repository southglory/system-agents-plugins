# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

一个 [system-agents-template](https://github.com/southglory/system-agents-template) 插件，把 Unity Editor + `unity-cli` + `gh` 组合变成**一行命令即可发布**的流水线。

- **Build**：`unity-cli exec BuildPipeline.BuildPlayer(...)` —— 场景、产物名、目标平台全部由调用方指定。**没有项目名写死**
- **Zip**：`Builds/{NAME}{后缀}` → `dist/{NAME}_{tag}.zip`
- **Release**：`gh release create {tag}`（重跑时回退为 `gh release upload --clobber`）
- **即用公告**：stdout 的一行 JSON 可直接管道到 `discord-huddle-post` 等公告技能

## 🚀 一行安装（推荐）

不要直接克隆本仓库，使用模板的安装器：

滚动（始终跟随 `main`）：

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

固定到稳定 Release（推荐以便重现）：

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```

安装器询问插件时选择 `unity-gamedev`。安装后不需要填写任何密钥 —— 插件直接用你已有的 `gh` 登录。

详细安装：[`docs/SETUP.md`](docs/SETUP.md)。冒烟测试：[`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md)。

## 一切皆 CLI 参数

本插件的核心是**不写死任何项目名**。场景路径、产物名、Unity 构建目标、项目根目录全部来自调用方：

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` 可重复（多场景构建）。`--skip-build` 复用已有的 `Builds/{NAME}.*`。完整参数表见 `skills/publish-build/SKILL.md`。

## 输出：stdout 单行 JSON

```json
{
  "tag": "v0.1.0",
  "title": "MVP α",
  "url": "https://github.com/owner/repo/releases/tag/v0.1.0",
  "zip": "dist/MyGame_v0.1.0.zip",
  "output_name": "MyGame",
  "target": "StandaloneWindows64"
}
```

stderr 输出给人阅读的进度。这个分离让后续"公告"步骤的脚本化很容易。

## 与其他插件的组合

| 目标 | 效果 | 设置 | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Unity 构建 → GitHub Release → 频道自动公告链接 | 两个插件都装；将 `publish-build` JSON 管道给 `discord-huddle-post` | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## 斜杠技能

| 命令 | 作用 |
|---|---|
| `/publish-build` | 一条命令完成 Build + zip + Release |

契约见 [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md)。

## 依赖

- **Python ≥ 3.10**（仅标准库 —— 无需 `pip install`）
- Unity Editor 正在运行，且 `unity-cli` 已连接（`unity-cli status = ready`）
- `unity-cli v0.3+` 在 `PATH` 中
- `gh` CLI，已用 `repo` scope 登录

## 本插件不做的事

- 不安装 Unity 自身、`unity-cli`、`gh`
- 不推送 git 标签 —— 只创建 GitHub Release。如需匹配的 git 标签，在 Release 之前 `git tag vX.Y.Z && git push --tags`
- 不签名 / 公证二进制。这是平台特定工具链范畴
- 不上传到 Steam / itch.io / 应用商店。应作为独立插件

## 许可证

MIT —— 见仓库根 [`LICENSE`](../LICENSE)。

## 相关文档

- [SETUP.md](docs/SETUP.md) —— 安装 + 首次发布流程
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) —— 7 步手动测试清单
- 仓库根 [README](../README.md) —— 插件生态概览
