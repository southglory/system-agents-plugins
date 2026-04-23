# Manual Smoke Test — discord-huddle plugin

`SETUP.md`를 완료한 뒤, 아래 순서로 실제 작동을 검증한다. 운영 Discord 서버 말고 **테스트 전용 서버**에 전용 봇 토큰을 쓸 것 — 운영 채널에 테스트 메시지가 흘러가지 않도록.

## 사전 준비

- [ ] 개인 테스트 서버 생성 후 봇 초대
- [ ] 테스트 채널 하나 만들기 (예: `#collab-test`)
- [ ] `.claude/secrets/discord-huddle.env`에 이 채널의 ID 기입
- [ ] `pip install -r discord-huddle/requirements.txt` 완료

## 1. 빈 상태 sync

- [ ] 테스트 채널에 메시지 없는 상태에서 `/discord-huddle-sync` 실행
- [ ] 출력: `new_messages=0 attachments=0 failed_attachments=0 last_read=None`
- [ ] `.system-agents/discord-huddle/raw/` 디렉토리는 비어 있음
- [ ] `.system-agents/discord-huddle/.gitignore` 파일이 자동 생성됨 (내용: `*`)

## 2. 텍스트 메시지 1건

- [ ] 테스트 채널에 "hello"라고 보냄
- [ ] `/discord-huddle-sync`
- [ ] 출력: `new_messages=1`
- [ ] `.system-agents/discord-huddle/raw/YYYY-MM-DD.jsonl`에 한 줄 추가, `content: "hello"`
- [ ] `.system-agents/discord-huddle/local-state.json`의 `last_read` 업데이트됨

## 3. 첨부 이미지

- [ ] 테스트 채널에 PNG 이미지 첨부 전송
- [ ] `/discord-huddle-sync`
- [ ] `new_attachments=1`
- [ ] `.system-agents/discord-huddle/raw/attachments/{msg_id}_{filename}` 존재
- [ ] raw 메시지의 `attachments[0].local_path`에 해당 상대경로 기록됨

## 4. 답장/이모지

- [ ] 기존 메시지에 답장 보냄 + 이모지 리액션 2개
- [ ] `/discord-huddle-sync`
- [ ] raw 메시지의 `message_reference.message_id`가 원본 ID와 일치
- [ ] raw 메시지의 `reactions` 배열에 이모지 엔트리 존재

## 5. 중복 방지

- [ ] 곧바로 다시 `/discord-huddle-sync`
- [ ] `new_messages=0`
- [ ] jsonl 파일에 중복 줄 없음
- [ ] `local-state.json.last_read` 값 동일 (forward-only는 같은 값 허용)

## 6. 요약 (메시지 부족)

- [ ] 메시지 5건 미만인 상태에서 `/discord-huddle-summarize`
- [ ] 에이전트가 "요약할 내용이 부족하다"고 알림
- [ ] `docs/discord-huddle-summaries/`에 새 파일 없음

## 7. 요약 (충분한 메시지)

- [ ] 메시지 5건 이상 쌓인 뒤 `/discord-huddle-summarize`
- [ ] 에이전트가 직접 JSONL을 읽고 요약 md 작성
- [ ] `docs/discord-huddle-summaries/YYYY-MM-DD_HHMM.md` 생성됨
- [ ] frontmatter에 `from_msg`, `to_msg`, `start`, `end`, `participants`, `message_count`, `attachments` 전부 존재
- [ ] 대표 이미지 지정된 경우 `docs/discord-huddle-summaries/attachments/<summary_stem>/` 폴더에 복사되어 있음
- [ ] `docs/discord-huddle-summaries/index.json`의 `last_summarized` + `last_file`이 최신 값으로 갱신됨

## 8. Forward-only 확인

- [ ] 곧바로 다시 `/discord-huddle-summarize`
- [ ] 에이전트가 "요약할 내용이 부족하다"고 알림 (새로 쌓인 메시지가 없음)
- [ ] `index.json`의 `last_summarized`는 뒤로 되돌아가지 않음

## 9. 상태 조회

- [ ] `python bot/discord_collab.py status`
- [ ] 현재 `last_read`(local-state), `last_summarized` + `last_file`(summary/index), `updated_at`이 JSON으로 출력됨

## 10. Post (게시)

- [ ] `python bot/discord_collab.py post --message "smoke test"` 실행
- [ ] 테스트 채널에 "smoke test" 메시지 나타남
- [ ] stdout에 `[post] message_id=...` 출력

## 11. 경로 오버라이드

- [ ] `.claude/secrets/discord-huddle.env`에 `DISCORD_HUDDLE_DATA_DIR=custom/data` 추가
- [ ] `/discord-huddle-sync`
- [ ] 이번엔 `custom/data/raw/*.jsonl`에 기록됨 (기본 경로가 아님)
- [ ] 확인 후 오버라이드 라인 제거하여 기본 경로로 복귀

## 12. Gateway listener (선택)

- [ ] 별도 터미널에서 `python bot/gateway_listener.py`
- [ ] 테스트 채널에 메시지 전송
- [ ] 1초 내 `.system-agents/discord-huddle/inbox/*.json` 생성
- [ ] listener 종료 (Ctrl+C) → 정상 종료 로그 출력
