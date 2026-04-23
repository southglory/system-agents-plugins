# Manual smoke test — unity-gamedev

Run through this checklist on a real Unity project + a sacrificial GitHub repo (don't use your production game's repo).

## Pre-flight

- [ ] Unity Editor open on a project that has at least one scene under `Assets/Scenes/`
- [ ] `unity-cli status` reports `ready`
- [ ] `gh auth status` is logged in with `repo` scope
- [ ] A throwaway GitHub repo is configured as the git remote of the Unity project (or pass `--project-root` to a different repo)

## 1. Happy path — fresh build

- [ ] Run:
      ```
      python bot/publish_build.py --tag smoke-v1 \
        --scene Assets/Scenes/<YourScene>.unity --output-name Smoke
      ```
- [ ] stderr shows the build step, then the zip step, then the release step
- [ ] stdout ends with one JSON line containing `url`, `zip`, `tag=smoke-v1`
- [ ] Visit the `url`; the release page exists with `Smoke_smoke-v1.zip` attached
- [ ] `Builds/Smoke.exe` (or `.app`/no-ext for other targets) exists
- [ ] `dist/Smoke_smoke-v1.zip` exists

## 2. Re-run with same tag (`--clobber` fallback)

- [ ] Edit the scene trivially (add a comment somewhere doesn't count; change something cosmetic)
- [ ] Run the same command again with `--tag smoke-v1`
- [ ] stderr notes `tag smoke-v1 exists, uploading asset with --clobber`
- [ ] Release page now has the newer zip

## 3. `--skip-build`

- [ ] `rm dist/Smoke_smoke-v2.zip` (if it exists)
- [ ] `python bot/publish_build.py --tag smoke-v2 --skip-build --output-name Smoke`
- [ ] Build step is skipped (no Unity CPU spike)
- [ ] Release `smoke-v2` created with the same binary zipped

## 4. Missing scene is rejected

- [ ] `python bot/publish_build.py --tag smoke-v3` (no `--scene`, no `--skip-build`)
- [ ] rc=2, stderr says "at least one `--scene` is required"

## 5. Missing project root is rejected

- [ ] `cd` into a directory without `Assets/` and `ProjectSettings/`
- [ ] `python /abs/path/to/bot/publish_build.py --tag smoke-v4 --scene Assets/S.unity`
- [ ] rc=3, stderr mentions `--project-root`

## 6. Scenes argument order

- [ ] Build with two scenes: `--scene Assets/Scenes/Boot.unity --scene Assets/Scenes/Main.unity`
- [ ] The built game starts from `Boot` (Unity treats scene 0 as startup)

## 7. Cleanup

- [ ] Delete the smoke-v1, v2 (and v3 if any) releases on GitHub
- [ ] Delete the corresponding tags: `git tag -d smoke-v1; git push --delete origin smoke-v1` etc.

## Known not-tested-here

- Multi-platform builds beyond the host OS (needs target module installed in Editor)
- Very large zips (hundreds of MB) — GitHub upload will slow down but should succeed
- Private repo with a token lacking `repo` scope — `gh` will report the exact permission needed
