# Recipe: Unity build → Discord announcement

Pair [`unity-gamedev`](../../unity-gamedev/) with [`discord-huddle`](../../discord-huddle/) so a Unity build turns into a Discord channel announcement with the download link, in a single shell pipeline.

## Prerequisites

- Both plugins installed (use `install.sh` and pick both from the picker, or install them manually).
- `discord-huddle` is already configured (`DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` in `.claude/secrets/discord-huddle.env`).
- `unity-gamedev` prereqs: Unity Editor running + `unity-cli status = ready` + `gh` authenticated.
- [`jq`](https://jqlang.github.io/jq/) available for parsing the JSON (on Windows Git Bash, `jq` ships with most recent installs; otherwise `scoop install jq` or equivalent).

## One-liner

Build → Release → announce:

```bash
OUT=$(python bot/publish_build.py \
        --tag v0.1.0-alpha \
        --scene Assets/Scenes/Main.unity \
        --output-name MyGame \
        --notes "MVP α")

URL=$(echo "$OUT" | jq -r .url)
TAG=$(echo "$OUT" | jq -r .tag)

python bot/discord_collab.py post --message "🚀 새 빌드: \`$TAG\`

**다운로드**: $URL

zip 다운로드 → 압축 풀기 → \`MyGame.exe\` 실행."
```

Or, if the build already exists and you just want to re-release and re-announce:

```bash
OUT=$(python bot/publish_build.py --tag v0.1.0-alpha --skip-build --output-name MyGame)
URL=$(echo "$OUT" | jq -r .url)
python bot/discord_collab.py post --message "🔁 rebuilt + re-announced: $URL"
```

## Why these stay separate plugins

- `unity-gamedev` has no Discord knowledge. It can announce to anything — Slack, email, a Notion callout — as long as you can shell-pipe its JSON.
- `discord-huddle` has no Unity knowledge. It receives an already-formed message and posts it.
- They only meet in this recipe. If you swap Discord for something else next year, you keep `unity-gamedev` untouched.

## Windows Git Bash tip

Git Bash inherits CRLF-quirky argument passing. If the multiline message above produces weird output, write it to a file and use `--message-file`:

```bash
OUT=$(python bot/publish_build.py --tag v0.1.0 --skip-build --output-name MyGame)
URL=$(echo "$OUT" | jq -r .url)
TAG=$(echo "$OUT" | jq -r .tag)

cat > .cache/release-announce.md <<EOF
🚀 새 빌드: \`$TAG\`

**다운로드**: $URL

zip 다운로드 → 압축 풀기 → \`MyGame.exe\` 실행.
EOF

python bot/discord_collab.py post --message-file .cache/release-announce.md
```

## Optional: turn it into a slash combo-skill

If your team hits this flow often, copy the shell block into a new
`skills/publish-and-announce/SKILL.md` and have Claude Code run it. Both
plugins already ship their own skills, so this meta-skill would just be
the orchestration — five lines of documented shell.

## Limitations

- No atomic "build failed → don't announce". Pipeline behavior: if
  `publish_build.py` fails, `$OUT` is empty and `jq` errors out, so the
  `discord_collab.py post` never runs — but nothing rolls back the
  GitHub Release if the announce step is what fails. Re-run the post
  step manually if that happens (the Release URL is still valid).
- No variable-substitution friendliness across shells. Example above
  assumes Bash / Git Bash. On PowerShell, adjust `$OUT`/`$URL`/`$TAG`
  handling accordingly.
