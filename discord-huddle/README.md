# discord-huddle

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

A [system-agents-template](https://github.com/southglory/system-agents-template) plugin that turns a Discord channel into your project's team chat, meeting-notes pipe, and announcement surface.

- **Pull**: archive channel messages as local JSONL (`/discord-huddle-sync`)
- **Push**: let agents or users post messages to the channel (`/discord-huddle-post`)
- **Listen**: real-time notifications over the Discord Gateway WebSocket (`/discord-huddle-listen`)
- **Summarize**: an agent reads the raw log and produces a tracked markdown meeting note — no LLM API cost beyond your Claude Code session (`/discord-huddle-summarize`)

## 🚀 One-line install (recommended)

Don't clone this repo directly. Use the template's installer:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

When asked, pick `discord-huddle` from the plugin list. The installer copies files into your project, registers slash skills globally, and seeds `.claude/secrets/discord-huddle.env.example`. After install, fill the secrets file (Bot Token + Channel ID) and you're done.

Detailed setup: [`docs/SETUP.md`](docs/SETUP.md). Manual smoke test: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Key features

### REST sync + real-time listener

- `sync` pulls everything after `last_read` via REST polling
- `listen` (Gateway) gets events pushed over WebSocket and writes tiny signal files that Claude Code's Monitor tool picks up
- Use them together: listener gives speed, sync guarantees completeness (attachments, reactions on first receive)

### Two-way channel

- Team → agent: chat drops requirements, feedback, questions in Discord
- Agent → team: agents post analysis, diagrams, webpage screenshots, build-release links right back into the channel

### Summaries as a team asset

- Summary markdowns land in `docs/discord-huddle-summaries/` and are **git-tracked**
- A new teammate who `git clone`s the project immediately reads past meeting notes
- The summary progress pointer (`index.json`) is also tracked, so merge conflicts resolve deterministically (forward-only: "take the newer msg_id")

### Deterministic summarize gate

Before an agent spends tokens summarizing, it calls:

```bash
python bot/discord_collab.py summarize-check
```

A code-only scan returns `{ready, reason, stats}`. If `ready:false` (too few messages, short monologue, etc.), the agent stops immediately without loading raw into its context. The full rules live in [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md).

### Non-invasive installation

- Runtime data (`raw/`, `inbox/`, `local-state.json`, `vc-snapshots/`) lives in `.system-agents/discord-huddle/` and the plugin auto-drops a `.gitignore: *` inside — **your project's root `.gitignore` is never touched**
- Path overrides via the same `.env` (no separate `export` needed):
  `SYSTEM_AGENTS_PROJECT_ROOT`, `DISCORD_HUDDLE_DATA_DIR`, `DISCORD_HUDDLE_SUMMARY_DIR`

### Friendly error messages

No raw Python tracebacks. 401/403/404/429 each come with a one-line hint pointing at the exact remediation (Reset Token, re-invite bot, check channel id, rate limit).

## Slash skills

| Command | What it does |
|---|---|
| `/discord-huddle-sync` | Fetch new channel messages into raw JSONL |
| `/discord-huddle-listen` | Gateway WebSocket real-time listener |
| `/discord-huddle-post` | Post a message (with optional attachments or web-page snapshot) |
| `/discord-huddle-summarize` | Agent reads raw and writes a meeting note |

Each skill's exact contract is in `skills/<name>/SKILL.md`.

## Web page snapshot (optional feature)

`/discord-huddle-post --vc-snapshot` renders an arbitrary URL as a PNG using headless Chromium and attaches it:

- Explicit URL: `--vc-url https://my-dashboard.local`
- Auto-detection (opt-in): set `--vc-sessions-dir DIR` or `VC_SESSIONS_DIR` to a directory laid out as `<session>/state/server-info` (JSON containing a `url` field). The plugin doesn't care which tool produces those files.
- Requires: `pip install -r requirements-optional.txt` + `playwright install chromium` (~200 MB, one time).

## Data locations (default)

| Path | Contents | Git-tracked? |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Raw message dumps | No (auto-gitignore) |
| `.system-agents/discord-huddle/inbox/` | Gateway real-time signals | No |
| `.system-agents/discord-huddle/local-state.json` | Per-user sync pointer | No |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright PNGs | No |
| `docs/discord-huddle-summaries/*.md` | Team meeting notes | **Yes** |
| `docs/discord-huddle-summaries/index.json` | Forward-only summary pointer | **Yes** |
| `docs/discord-huddle-summaries/attachments/` | Images referenced by summaries | **Yes** |

## Combining with other plugins

| Target | Effect | Setup | Recipe |
|---|---|---|---|
| Built-in `/schedule` (Claude Code) | Recurring announcements in the channel (daily standups, weekly reports) | Use `/schedule` to cron `discord-huddle-post` | Docs-only combo (see [README.ko.md](README.ko.md#조합-가능한-플러그인) for a cron example) |
| (planned) `unity-gamedev` | Unity build → GitHub Release → auto-announced channel link | Install both plugins; pipe `publish-build` JSON into `discord-huddle-post` | `recipes/unity-build-to-discord/` (to be added with unity-gamedev) |

## Requirements

- Python ≥ 3.10
- Discord Bot Token (create in [Developer Portal](https://discord.com/developers/applications))
- **Message Content Intent** enabled (required for Gateway listener)

## License

MIT — see the repo-root [`LICENSE`](../LICENSE).

## Related docs

- [SETUP.md](docs/SETUP.md) — install and configuration
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — manual smoke-test checklist
- Repo-root [README](../README.md) — the plugin ecosystem overview
