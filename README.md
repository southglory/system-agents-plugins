# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Official plugins for [system-agents-template](https://github.com/southglory/system-agents-template).

Each plugin lives in its own subdirectory and is distributed independently. Users pick only the plugins they need.

## 🚀 One-line install (via the template's installer)

You don't clone this repo directly — the template's `install.sh` reads the plugin index here and copies the selected plugins into your project:

Rolling (always latest `main`):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Pinned to a stable template Release:

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


Answer "discord-huddle" (or any other listed plugin) when the installer asks which plugins to pull.

## Available plugins

| Folder | Summary | Status |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Team chat + tracked meeting summaries via Discord | ✅ Released (`discord-huddle-v0.1.0`) |
| [`unity-gamedev/`](unity-gamedev/) | Unity CLI build → GitHub Release publishing | ✅ Released (`unity-gamedev-v0.1.0`) |

Open a plugin folder to see its own README for detailed setup.

## Install model

Plugins are installed by file copy (`cp -r`), not by a package manager (pip/npm). The plugin files merge directly into your project tree, so managed installation belongs to the template's `install.sh`:

```bash
# 1. Clone this repo (installer does this automatically)
git clone https://github.com/southglory/system-agents-plugins.git

# 2. Copy the desired plugin into your project (installer does this)
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Register skills with Claude Code (installer does this)
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Install Python deps
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

The manual `cp -r` flow exists as a fallback for advanced users; the installer is recommended.

## Versioning

Each plugin is released independently. Tag format: `<plugin-name>-vX.Y.Z`.

- `discord-huddle-v0.1.0` — first public release
- `unity-gamedev-v0.1.0` — planned

There is no repo-wide single version. Template tags (`v2.x.x`) and plugin tags never collide.

## Combining plugins

Plugins are designed to work on their own, but some pair well. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the combo-matrix convention each plugin README is expected to document. Reusable cross-plugin combos live in [`recipes/`](recipes/).

## Compatibility

- Claude Code (slash skill system)
- system-agents-template v2.x or later (chatrooms, board.yaml, turn-bot)
- Python ≥ 3.10
- Windows / macOS / Linux

Plugins may add further requirements (for example discord-huddle needs a Discord Bot Token).

## License

[MIT](LICENSE) — same as system-agents-template.

## Contributing

- Bug reports and feedback: GitHub Issues
- New plugins: follow the structure conventions in [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
