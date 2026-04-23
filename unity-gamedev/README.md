# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

A [system-agents-template](https://github.com/southglory/system-agents-template) plugin that turns a Unity Editor + `unity-cli` + `gh` trio into a one-command release pipeline.

- **Build**: `unity-cli exec BuildPipeline.BuildPlayer(...)` with scenes/output/target supplied by the caller — **nothing project-specific is hardcoded**
- **Zip**: `Builds/{NAME}{ext}` → `dist/{NAME}_{tag}.zip`
- **Release**: `gh release create {tag}` (or `gh release upload --clobber` on re-run)
- **Announce-ready**: one-line JSON on stdout is meant to be piped straight into `discord-huddle-post` or any other announcer

## 🚀 One-line install (recommended)

Don't clone this repo directly. Use the template's installer:

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

When asked, pick `unity-gamedev` from the plugin list. After install, no secrets to fill — the plugin uses your existing `gh` login.

Detailed setup: [`docs/SETUP.md`](docs/SETUP.md). Smoke test: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Everything is a CLI flag

The whole point of this plugin is **no hardcoded project names**. Scene paths, output binary name, Unity build target, and project root all come from the caller. There's nothing specific to any one game baked in:

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` can be repeated for multi-scene builds. `--skip-build` reuses whatever's already in `Builds/{NAME}.*`. Full flag table is in `skills/publish-build/SKILL.md`.

## Output: one JSON line on stdout

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

stderr carries human-readable progress. This separation makes the next step (announcing the release somewhere) trivial to script.

## Combining with other plugins

| Target | Effect | Setup | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Unity build → GitHub Release → auto-announced link in a Discord channel | Install both plugins; pipe `publish-build` JSON into `discord-huddle-post` | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## Slash skill

| Command | What it does |
|---|---|
| `/publish-build` | Build + zip + Release in one go |

Exact contract in [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md).

## Requirements

- **Python ≥ 3.10** (stdlib only — no `pip install` step)
- **Unity Editor** running, with `unity-cli` connected (`unity-cli status = ready`)
- **`unity-cli v0.3+`** on `PATH`
- **`gh` CLI**, authenticated with `repo` scope

## What this plugin does NOT do

- Does not install Unity itself, `unity-cli`, or `gh`.
- Does not push git tags — it creates GitHub Releases. If you want a matching git tag, run `git tag vX.Y.Z && git push --tags` before the Release step (the `--clobber` fallback means order is flexible).
- Does not sign / notarize binaries. That's platform-specific tooling and out of scope.
- Does not upload to Steam, itch.io, or app stores. Consider that a separate plugin.

## License

MIT — see the repo-root [`LICENSE`](../LICENSE).

## Related docs

- [SETUP.md](docs/SETUP.md) — install + first release walkthrough
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 7-step manual test checklist
- Repo-root [README](../README.md) — plugin ecosystem overview
