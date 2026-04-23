---
name: discord-huddle-listen
description: Discord Gateway WebSocket listener 기반 실시간 메시지 감지 + Monitor 연결
---

# Discord Huddle Listen (Gateway)

기존 REST polling(`/discord-huddle-sync`)을 **실시간 push**로 대체한다.

## 아키텍처

```
discord.com
    │ (WebSocket Gateway)
    ▼
gateway_listener.py  (상주 Python 프로세스)
    │
    │ on_message 이벤트
    ▼
.system-agents/discord-huddle/inbox/{ts}_{msg_id}.json  (작은 signal 파일, gitignore 대상)
    │
    │ 파일 변경 감지
    ▼
Claude Code Monitor tool  →  task-notification  →  에이전트 즉시 반응
    │
    │ signal 받으면 전체 raw 보정
    ▼
python bot/discord_collab.py sync  (기존 REST, attachments 등 다운로드)
```

## 사전 조건

- `pip install -r bot/requirements.txt` — `discord.py>=2.3` 포함
- Discord Developer Portal에서 Bot의 **Message Content Intent** 활성화
- `.claude/secrets/discord-huddle.env`에 `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`

## 실행 (사용자 수동)

별도 터미널에서 상주 실행:

```
python bot/gateway_listener.py
```

또는 Windows Task Scheduler 등록 (세션 독립적으로 동작). Ctrl+C로 중단.

`--project-root PATH`로 프로젝트 루트 명시 가능 (미지정 시 `SYSTEM_AGENTS_PROJECT_ROOT` 또는 CWD 상위 `.claude/` 자동 탐색).

## Claude Code 연결

이 스킬은 Claude Code에서 Monitor tool을 통해 inbox 디렉토리를 감시하도록 지시한다:

1. Monitor로 `.system-agents/discord-huddle/inbox/` 경로에 파일 생성 이벤트 등록 (`persistent: true`)
2. task-notification 도달 시:
   - 새 signal json 읽어서 `author_name`, `content` 파악
   - `/discord-huddle-sync` 호출해서 raw JSONL + 첨부 다운로드
   - signal 파일은 처리 후 삭제(또는 별도 `processed/` 이동)
   - 즉시 에이전트가 반응 (기획 답변 / 다음 단계 진행)

## 신호 파일 포맷

`.system-agents/discord-huddle/inbox/20260422T012345_1234567890.json`:

```json
{
  "id": "1234567890",
  "channel_id": "1486972648364970104",
  "author_id": "640947969947860992",
  "author_name": "강현명",
  "is_bot": false,
  "content": "메시지 본문",
  "timestamp": "2026-04-22T01:23:45.123456+00:00",
  "attachment_count": 0
}
```

`is_bot=true`이면 봇 자신의 메시지 — skip 권장.

## 주의

- Gateway listener는 **세션 독립적** 프로세스. 재부팅/종료 시 수동 재시작 필요.
- 실시간 signal은 있지만 attachments 다운로드는 여전히 `sync` 몫.
- Listener가 다운되어 있어도 `sync`로 뒤늦게 복구 가능.

## 트러블슈팅

- **PrivilegedIntentsRequired**: Discord Portal에서 Message Content Intent 미활성화.
- **TCP 연결 끊김**: discord.py가 자동 재연결. 로그 확인.
- **signal 파일이 쌓임**: Monitor가 안 돌거나 에이전트가 세션 중 아님. 수동 `/discord-huddle-sync`로 복구.
