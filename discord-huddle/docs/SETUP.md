# Setup Guide — discord-huddle plugin

Discord 채널의 대화를 프로젝트로 동기화하고, 반대로 플러그인에서 메시지를 게시하기 위한 설정 절차.

전제: 이 플러그인을 이미 프로젝트 루트 아래에 설치한 상태. 설치 자체는 `README.md` 참고.

## 1. Discord Bot 생성

1. <https://discord.com/developers/applications> → **New Application**.
2. 이름 지정 → Create.
3. 왼쪽 메뉴 **Bot** → **Reset Token** → 생성된 토큰 복사 (1회만 표시됨).
4. 같은 Bot 페이지에서 **Privileged Gateway Intents → Message Content Intent** 활성화.

## 2. Bot 채널 초대

1. 왼쪽 메뉴 **OAuth2 → URL Generator**.
2. **Scopes**: `bot` 체크.
3. **Bot Permissions**: `View Channels`, `Read Messages/View Channel History`, `Send Messages` 체크.
4. 생성된 URL을 브라우저에 붙여넣기 → 협업용 서버 선택 → 초대.

## 3. 채널 ID 확인

1. Discord 설정 → **Advanced → Developer Mode ON**.
2. 대상 채널 우클릭 → **Copy Channel ID**.

## 4. `.claude/secrets/discord-huddle.env` 작성

프로젝트 루트에서:

```bash
mkdir -p .claude/secrets
cp discord-huddle/samples/discord-huddle.env.example .claude/secrets/discord-huddle.env
```

그리고 토큰·채널 ID 채우기:

```
DISCORD_BOT_TOKEN=여기_봇_토큰
DISCORD_CHANNEL_ID=여기_채널_ID
```

`.claude/secrets/`는 프로젝트 `.gitignore`에 포함돼 있어야 한다 (system-agents-template의 기본 관례). 없다면 추가:

```
.claude/secrets/
```

## 5. Python 의존성 설치

기본 의존 (sync/listen/post):

```bash
pip install -r discord-huddle/requirements.txt
```

선택 의존 (`--vc-snapshot` 사용 시):

```bash
pip install -r discord-huddle/requirements-optional.txt
playwright install chromium   # 약 200MB, 최초 1회
```

개발/테스트:

```bash
pip install -r discord-huddle/requirements-dev.txt
```

## 6. 첫 동기화

Claude Code 세션에서:

```
/discord-huddle-sync
```

또는 직접:

```bash
python bot/discord_collab.py sync
```

초기 실행 시 채널의 최근 메시지를 수집. 첫 실행 후 `.system-agents/discord-huddle/raw/*.jsonl`에 누적되기 시작한다.

## 7. (선택) 실시간 Gateway listener

polling 대신 실시간 push로 받고 싶을 때:

```bash
python bot/gateway_listener.py
```

- `discord.py>=2.3` 필요 (기본 requirements.txt에 포함)
- Discord Developer Portal의 **Message Content Intent** 활성화 필수
- 상주 프로세스 — 별도 터미널이나 Windows Task Scheduler로 백그라운드 실행
- 새 메시지 도달 시 `.system-agents/discord-huddle/inbox/{ts}_{msg_id}.json` signal 파일 생성
- Claude Code에서 `/discord-huddle-listen`으로 Monitor tool에 연결하면 즉시 반응

`/discord-huddle-sync`(REST 폴링)와 병행 가능 — listener는 실시간 알림, sync는 전체 보정.

## 8. 요약 생성

충분한 메시지(기본 5건 이상)가 쌓였다면:

```
/discord-huddle-summarize
```

에이전트가 직접 raw JSONL을 읽고 요약 md 작성 — 별도 LLM API 호출 없음.

**결과 위치**: `docs/discord-huddle-summaries/YYYY-MM-DD_HHMM.md` (git 트래킹 대상, 팀원이 pull로 공유).

## 경로 커스터마이징 (선택)

기본 경로가 프로젝트 구조와 안 맞을 때 `.claude/secrets/discord-huddle.env`에 추가:

```
# 런타임 데이터 (raw, inbox, local-state) — 기본 .system-agents/discord-huddle/
DISCORD_HUDDLE_DATA_DIR=custom/runtime

# 팀 자산 (요약 md, index.json) — 기본 docs/discord-huddle-summaries/
DISCORD_HUDDLE_SUMMARY_DIR=custom/summaries

# 프로젝트 루트를 CLI가 자동 탐지 못 할 때
SYSTEM_AGENTS_PROJECT_ROOT=/absolute/path
```

상대 경로는 프로젝트 루트 기준. 절대 경로도 OK.

### Agent-system(SaveThePenguin) 호환 모드

기존 `Agent-system` 경로를 유지하고 싶다면:

```
DISCORD_HUDDLE_DATA_DIR=docs/discord-huddle-logs
DISCORD_HUDDLE_SUMMARY_DIR=docs/discord-huddle-logs/summary
```

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `config error: secrets file not found` | .env 없음 | 위 단계 4 수행 |
| `project root undetermined` | CWD에서 `.claude/` 자동 탐지 실패 | `--project-root PATH` 또는 `SYSTEM_AGENTS_PROJECT_ROOT` 설정 |
| `missing required keys: DISCORD_BOT_TOKEN` | 값 누락 | .env 편집 |
| `error: sync failed — HTTP 401 ...` + hint | 토큰 무효/폐기됨 | Developer Portal → Bot → Reset Token → `.env` 업데이트. 에러 메시지 hint 줄에 정확한 안내 포함됨 |
| `error: ... HTTP 403 ...` + hint | 봇이 채널에 없거나 권한 부족 | OAuth URL로 재초대하거나 채널별 권한 오버라이드 확인 |
| `error: ... HTTP 404 ...` + hint | 채널 ID 오타 or 존재 안 함 | `.env`의 `DISCORD_CHANNEL_ID` 재확인 |
| `error: ... HTTP 429 ...` + hint | 레이트 리밋 | 잠시 후 재시도. 다른 프로세스가 같은 토큰을 쓰고 있지 않은지 확인 |
| `No URL available for --vc-snapshot` | 스냅샷 대상 URL 미지정 | `--vc-url URL` 직접 지정, 또는 `--vc-sessions-dir DIR`/`VC_SESSIONS_DIR` 설정 |

## 데이터 위치 요약

| 경로 | 내용 | git 트래킹 |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Raw 메시지 덤프 | NO (자동 gitignore) |
| `.system-agents/discord-huddle/raw/attachments/` | 첨부 원본 | NO |
| `.system-agents/discord-huddle/inbox/` | Gateway 실시간 신호 | NO |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright PNG | NO |
| `.system-agents/discord-huddle/local-state.json` | 개인 sync 포인터 | NO |
| `docs/discord-huddle-summaries/*.md` | 팀 회의록 (YAML frontmatter + md) | YES |
| `docs/discord-huddle-summaries/index.json` | 요약 진행 포인터 (forward-only) | YES |
| `docs/discord-huddle-summaries/attachments/` | 요약용 대표 이미지 | YES |
