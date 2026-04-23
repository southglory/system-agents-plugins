# discord-huddle


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![discord-huddle release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=discord-huddle-*&label=discord-huddle)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

一个 [system-agents-template](https://github.com/southglory/system-agents-template) 插件，把 Discord 频道变成项目的团队聊天、会议纪要和公告渠道。

- **拉取**：将频道消息存档为本地 JSONL (`/discord-huddle-sync`)
- **发送**：让智能体或用户向频道发送消息 (`/discord-huddle-post`)
- **监听**：通过 Discord Gateway WebSocket 实时接收通知 (`/discord-huddle-listen`)
- **总结**：智能体阅读原始日志并生成被 git 追踪的会议纪要 Markdown，除 Claude Code 会话外不消耗额外 LLM API 成本 (`/discord-huddle-summarize`)

## 🚀 一行安装（推荐）

不要直接克隆本仓库。使用模板的安装器：

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


选择插件时挑选 `discord-huddle`。安装器会将文件复制到你的项目中，全局注册斜杠技能，并生成 `.claude/secrets/discord-huddle.env.example`。安装后，填好 secrets 文件（Bot Token + 频道 ID）即可。

详细设置：[`docs/SETUP.md`](docs/SETUP.md)。手动冒烟测试：[`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md)。

## 主要特性

### REST sync + 实时 listener

- `sync` 通过 REST 拉取 `last_read` 之后的所有消息
- `listen`（Gateway）以 WebSocket 接收推送事件，写出小型信号文件供 Claude Code 的 Monitor 工具捕获
- 两者并用：listener 提供速度，sync 保证完整性（首次收取时的附件、反应等）

### 双向频道

- 团队 → 智能体：Discord 聊天提出需求、反馈、问题
- 智能体 → 团队：智能体将分析、图示、网页截图、构建发布链接直接发回频道

### 总结即团队资产

- 总结 Markdown 落在 `docs/discord-huddle-summaries/`，**被 git 追踪**
- 新队员只要 `git clone` 项目就立即可读取历史会议纪要
- 总结进度指针（`index.json`）也被追踪，因此合并冲突可按确定性规则解决（前进专属：取较新的 msg_id）

### 确定性的 summarize 门槛

在智能体花费 token 进行总结之前，先调用：

```bash
python bot/discord_collab.py summarize-check
```

一次仅依靠代码的扫描返回 `{ready, reason, stats}`。如果 `ready:false`（消息太少、短独白等），智能体立即停止而不会加载原始到上下文。完整规则见 [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md)。

### 非侵入式安装

- 运行时数据（`raw/`、`inbox/`、`local-state.json`、`vc-snapshots/`）放在 `.system-agents/discord-huddle/`，插件会自动在其中放入 `.gitignore: *` —— **不会修改你项目根的 `.gitignore`**
- 路径可以通过同一个 `.env` 覆盖（无需另外 `export`）：
  `SYSTEM_AGENTS_PROJECT_ROOT`、`DISCORD_HUDDLE_DATA_DIR`、`DISCORD_HUDDLE_SUMMARY_DIR`

### 友好的错误信息

不会泄漏原始的 Python 回溯。401/403/404/429 各自附带一行提示，直接指向确切的解决方案（重置 Token、重新邀请机器人、检查频道 id、限流等待）。

## 斜杠技能

| 命令 | 用途 |
|---|---|
| `/discord-huddle-sync` | 拉取频道新消息到原始 JSONL |
| `/discord-huddle-listen` | Gateway WebSocket 实时 listener |
| `/discord-huddle-post` | 发送消息（可选附件或网页截图） |
| `/discord-huddle-summarize` | 智能体读取 raw 并写会议纪要 |

每个技能的精确合约见 `skills/<name>/SKILL.md`。

## 网页截图（可选功能）

`/discord-huddle-post --vc-snapshot` 使用无头 Chromium 将任意 URL 渲染为 PNG 并附加：

- 显式 URL：`--vc-url https://my-dashboard.local`
- 自动检测（可选）：通过 `--vc-sessions-dir DIR` 或 `VC_SESSIONS_DIR` 指向 `<session>/state/server-info` 结构的目录（JSON 包含 `url` 字段）。插件并不在乎是哪个工具生成这些文件。
- 需要：`pip install -r requirements-optional.txt` + `playwright install chromium`（约 200MB，首次安装）。

## 数据位置（默认）

| 路径 | 内容 | 是否 git 追踪 |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | 原始消息转储 | 否（自动 gitignore） |
| `.system-agents/discord-huddle/inbox/` | Gateway 实时信号 | 否 |
| `.system-agents/discord-huddle/local-state.json` | 单机 sync 指针 | 否 |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright PNG | 否 |
| `docs/discord-huddle-summaries/*.md` | 团队会议纪要 | **是** |
| `docs/discord-huddle-summaries/index.json` | 前进专属的总结指针 | **是** |
| `docs/discord-huddle-summaries/attachments/` | 总结引用的图片 | **是** |

## 与其他插件组合

| 目标 | 效果 | 设置 | Recipe |
|---|---|---|---|
| 内置的 `/schedule`（Claude Code） | 在频道发送定期公告（每日站会、周报） | 使用 `/schedule` 为 `discord-huddle-post` 设置 cron | 仅文档组合（示例见 [README.ko.md](README.ko.md#조합-가능한-플러그인)） |
| （计划中）`unity-gamedev` | Unity 构建 → GitHub Release → 自动公告频道链接 | 同时安装两个插件；将 `publish-build` JSON 管道到 `discord-huddle-post` | `recipes/unity-build-to-discord/`（待与 unity-gamedev 一同新增） |

## 要求

- Python ≥ 3.10
- Discord Bot Token（在 [Developer Portal](https://discord.com/developers/applications) 创建）
- 启用 **Message Content Intent**（Gateway listener 必需）

## 许可证

MIT — 见仓库根的 [`LICENSE`](../LICENSE)。

## 相关文档

- [SETUP.md](docs/SETUP.md) — 安装与配置
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 手动冒烟测试清单
- 仓库根 [README](../README.md) — 插件生态概览

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
