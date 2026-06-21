# autonomous-loop


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![autonomous-loop release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=autonomous-loop-*&label=autonomous-loop)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

A [system-agents-template](https://github.com/southglory/system-agents-template) plugin that runs an
**autonomous loop**: it processes `TODO.md` top-down and, when a decision would normally need the user,
it doesn't stop — it **simulates the user's persona** to answer and keeps going. Approval-gated risky
actions are deferred to a `## 승인 대기` list and the loop moves on to the next doable task.

- **Loop**: process `TODO.md` items without stopping (`/autonomous-loop`)
- **Persona self-answer**: respond as the user from a local persona profile, never pausing for routine decisions
- **Safety boundary**: reversible + in-sandbox work runs autonomously; public push / deploy / external send / irreversible deletes are deferred for real user approval
- **Persona builder**: build/refresh the persona from your Claude Code history (multi-account aware)

> The persona is **personal speech data and stays local** (`~/.claude/persona/`). It is never committed
> and never part of this plugin. This repo ships only the loop logic and the builder.

## 설치 (Install)

Don't clone this repo directly — use the template's installer and pick `autonomous-loop`:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh                       # choose "autonomous-loop" at the plugin prompt
```

Manual (copy-merge, matching the plugin model):

```bash
# from a checkout of system-agents-plugins
cp -r autonomous-loop/skills/autonomous-loop  <your-project>/skills/
cp autonomous-loop/samples/TODO.md            <your-project>/TODO.md
cp autonomous-loop/samples/LOOP_RULES.md      <your-project>/LOOP_RULES.md
mkdir -p <your-project>/.claude
cp autonomous-loop/samples/settings.local.json <your-project>/.claude/settings.local.json

# build the persona once (local only, never committed)
python3 autonomous-loop/bot/build_persona.py        # interactive: pick account(s)+project(s)
```

No `pip install` needed — the builder uses only the Python standard library.

## 스킬 목록 (Skills)

| Command | Description |
|---|---|
| `/autonomous-loop` | `TODO.md`를 위에서부터 자율 처리. 멈추지 않고 페르소나로 자가 응답하며 진행, 승인 필요한 건 미뤄둠 |

Builder/backup are CLI, not skills:

| Command | Description |
|---|---|
| `python3 bot/build_persona.py` | 계정/프로젝트를 골라(`--list`/`--all`/`--accounts`/`--projects`) 페르소나 생성·갱신 |
| `bot/backup_persona.sh [backup\|list\|restore]` | 수기 PERSONA.md를 비공개(`~/.persona-backups/`)로 백업/복원 |

## 요구사항 (Requirements)

- Python **3.10+** (standard library only — no third-party deps, no token/key)
- Claude Code with at least one config dir holding `history.jsonl` (`~/.claude`, or cc-switch dirs `~/.claude-*`)
- No external tools, no secrets.

## 데이터 위치 (Data locations)

| Path | What | Git tracked? |
|---|---|---|
| `~/.claude/persona/PERSONA.md` | 페르소나 프로필 (수기로 다듬음) | ❌ never (개인 정보) |
| `~/.claude/persona/PERSONA_POOL.md` | 실제 발화 풀 (빌더가 자동 생성) | ❌ never |
| `~/.persona-backups/<ts>/` | 페르소나 비공개 백업 | ❌ never (홈, git 밖) |
| `<project>/TODO.md` | goal 파일 (할 일 + 승인 대기) | ❌ ignored (개인 작업) |
| `<project>/LOOP_RULES.md` | 루프 운영 규칙 | ❌ ignored |
| `<project>/.claude/settings.local.json` | 권한 + bypassPermissions | ❌ local settings |
| `<project>/skills/autonomous-loop/SKILL.md` | 루프 로직 | ✅ 프로젝트가 원하면 추적 가능 (발화 없음) |

## 조합 가능한 플러그인 (Composable plugins)

| 플러그인 | 조합 효과 | 추가 설정 | Recipe |
|---|---|---|---|
| discord-huddle | 자율 루프 종료 시 완료 요약·승인 대기 목록을 디스코드 채널에 자동 공지 | 두 플러그인 모두 설치 | — (예정) |
| unity-gamedev | 루프가 빌드까지 자율 진행, 릴리스(공개)는 승인 대기로 미뤄 사용자 확인 | 두 플러그인 모두 설치 | — (예정) |

## 라이선스 (License)

MIT (repo 전체 통일).
