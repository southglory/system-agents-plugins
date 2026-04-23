---
name: discord-huddle-sync
description: Discord 채널의 새 메시지를 가져와 프로젝트에 저장한다
---

# Discord Huddle Sync

`/discord-huddle-sync` 명령이 수행하는 작업.

## 사전 조건

- `.claude/secrets/discord-huddle.env`가 존재하고 `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`가 채워져 있어야 한다.
- Bot이 해당 채널의 메시지 읽기 권한을 가지고 있어야 한다.
- Python 의존성 설치: `pip install -r bot/requirements.txt` (`requests`, `python-dotenv`, `discord.py`).

## 동작

1. `python bot/discord_collab.py sync` 실행.
2. 마지막 동기화 이후(`last_read`) 메시지를 Discord REST로 전부 수집.
3. 각 메시지를 `.system-agents/discord-huddle/raw/YYYY-MM-DD.jsonl`에 append-only 저장 (run-time 디렉토리는 자동 gitignore).
4. 첨부파일을 `.system-agents/discord-huddle/raw/attachments/{msg_id}_{filename}`에 다운로드.
5. `.system-agents/discord-huddle/local-state.json`의 `last_read` 갱신 (이 파일은 커밋되지 않음 — 개인 동기화 상태).

## 경로 커스터마이징

기본 경로는 다음 환경변수로 바꿀 수 있다 (`.claude/secrets/discord-huddle.env`에 추가):

- `SYSTEM_AGENTS_PROJECT_ROOT` — 프로젝트 루트 (미설정 시 CWD 또는 상위 `.claude/` 폴더 자동 탐색)
- `DISCORD_HUDDLE_DATA_DIR` — 런타임 데이터 루트 (기본 `.system-agents/discord-huddle/`)
- `DISCORD_HUDDLE_SUMMARY_DIR` — 요약 디렉토리 (기본 `docs/discord-huddle-summaries/`)

## 결과 해석

- `new_messages=N` — 신규 메시지 N건 저장.
- `failed_attachments=M` — M개 첨부파일 다운로드 실패. 재시도 가능.
- `config error` — 셋업 가이드(`docs/SETUP.md`) 참조.

## 한계 및 설계 주의

- **리액션/편집은 수신 시점의 스냅샷만 저장**: sync는 `last_read` 이후의 **새 메시지**만 가져오므로, 이미 raw JSONL에 저장된 메시지에 나중에 추가된 리액션이나 편집 내용은 재-sync로 갱신되지 않는다. 팀 협업 채널에서 이 점이 중요하면 요약을 좀 늦게 돌리거나, 사후 리액션은 분석 대상 외로 간주한다.
- **첫 실행은 채널 전체를 당겨옴**: last_read 포인터가 없으면 `after=0`부터 시작해 과거 메시지까지 수집한다 (시간·용량 주의).

## 트러블슈팅

- **`error: sync failed — HTTP 401 ...`**: 봇 토큰 무효/폐기. `.env`의 `DISCORD_BOT_TOKEN` 재설정. 에러 hint 줄에 Developer Portal 경로 안내됨.
- **`HTTP 403`**: 봇이 채널에 초대되지 않았거나 권한 부족. SETUP.md §2 재수행.
- **`HTTP 404`**: `DISCORD_CHANNEL_ID` 확인 (채널 삭제됐거나 오타).
- **`HTTP 429`**: 레이트 리밋. 잠시 후 재시도.
- **네트워크 실패**: 재실행 시 이어받기 (last_read 유지).
