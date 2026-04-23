# Setup Guide — unity-gamedev plugin

Turn a Unity Editor + `unity-cli` + `gh` trio into a one-command release pipeline.

Assumes the plugin is already installed into your project (see repo-root README for `install.sh` usage).

## 1. External tools

- **Unity Editor** (any version where `unity-cli` exec works; the plugin is target-agnostic as long as the `BuildTarget` name is valid).
- **unity-cli** on `PATH`. `unity-cli v0.3+`. Verify with `unity-cli --version`.
- **GitHub CLI** (`gh`), authenticated with `repo` scope. Verify with `gh auth status`.

If `unity-cli` or `gh` is missing, the corresponding step fails with a clear error message.

## 2. Unity-side prerequisites

Open your Unity project in the Editor. Run `unity-cli status`; it must report `ready`. If you see `busy (Play Mode)` or `busy (Compilation)`, stop Play Mode or wait for a compile to finish.

## 3. GitHub side

The plugin uses whichever repo `gh` determines from the current working directory's git remote. So `cd` into the Unity project's git repo before invoking the plugin, or pass `--project-root` pointing at that repo.

## 4. First release

From your Unity project root:

```bash
python bot/publish_build.py \
  --tag v0.1.0-alpha \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --notes "MVP α"
```

Expected: stderr shows each step, stdout prints one JSON line with `url`, `zip`, `tag`, etc.

If something fails partway, re-running with the same `--tag` is safe: the gh step falls back to `release upload --clobber`.

## 5. Rebuild-free reshare (`--skip-build`)

When your `Builds/{NAME}.*` is already up to date and you just want to re-publish with a different tag or notes:

```bash
python bot/publish_build.py --tag v0.1.0-alpha-patch --skip-build \
  --output-name MyGame --notes "typo fix in notes"
```

## 6. Multi-scene builds

Repeat `--scene`:

```bash
python bot/publish_build.py --tag v0.2.0 \
  --scene Assets/Scenes/Boot.unity \
  --scene Assets/Scenes/Main.unity \
  --scene Assets/Scenes/Credits.unity \
  --output-name MyGame
```

Scene order matters (Unity treats the first as the startup scene).

## 7. Non-Windows targets

Pass `--target` with the Unity `BuildTarget` enum name:

- `StandaloneWindows64` (default)
- `StandaloneOSX`
- `StandaloneLinux64`
- `Android`, `WebGL`, `iOS` — accepted, but make sure the Editor has the target module installed.

The plugin auto-derives the output extension from the target (`.exe` / `.app` / no extension on Linux).

## Path customization

| Need | How |
|---|---|
| Run from outside the project | `--project-root /abs/path` |
| Pin a project globally (CI) | `export SYSTEM_AGENTS_PROJECT_ROOT=/abs/path` |
| Different Builds/ or dist/ location | Not customizable yet — file an issue if you need this |

## Combining with discord-huddle

The typical flow: build → release → announce on Discord. See `recipes/unity-build-to-discord/README.md` in this repo.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Unity project root undetermined` | Pass `--project-root` or run from a directory tree with `Assets/` + `ProjectSettings/`. |
| `unity-cli exec failed: ...` | Unity Editor not running, not ready, or `unity-cli` not on PATH. |
| `Unity build did not succeed: result=Failed ...` | Scene has compile errors. Fix in Editor first. `unity-cli console --type error` lists them. |
| `gh release create failed: authentication required` | `gh auth refresh -h github.com -s repo`. |
| `gh release create failed: ... not found` | The git remote points at a repo that doesn't exist or that your token can't access. |
| `expected build artifact not found` (skip-build mode) | `--output-name` doesn't match the file actually in `Builds/`. Run once without `--skip-build` or correct the name. |
