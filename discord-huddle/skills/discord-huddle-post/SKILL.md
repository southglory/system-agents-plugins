---
name: discord-huddle-post
description: Claude Code가 구성한 텍스트/파일을 Discord 채널에 게시한다 (sync의 반대 방향)
---

# Discord Huddle Post

`/discord-huddle-post` 명령이 수행하는 작업.

## 사전 조건

- `.claude/secrets/discord-huddle.env`의 봇이 채널에 **Send Messages** 권한을 가지고 있어야 한다.
- 첨부가 있다면 로컬 파일 경로가 접근 가능해야 한다.
- `--vc-snapshot` 사용 시: `pip install -r bot/requirements-optional.txt` + `playwright install chromium` 1회 실행 필요 (약 200MB, 최초 1회).

## 동작

1. `python bot/discord_collab.py post --message "..." [--attach ...]` 실행.
2. Discord REST API `POST /channels/{id}/messages` 호출 — 첨부 없으면 JSON body, 있으면 multipart/form-data.
3. 전송된 message_id를 반환.
4. `--vc-snapshot` 플래그 사용 시: `--vc-url`로 지정한 URL(또는 `--vc-sessions-dir`/`VC_SESSIONS_DIR`로 자동 탐지한 URL)을 Playwright Chromium으로 렌더링해 `.system-agents/discord-huddle/vc-snapshots/{UTC-timestamp}.png`에 저장, 첨부 목록 맨 앞에 추가한다.

## 제한

- 본문 2000자 이내, 첨부 최대 10개 (Discord API 제약).
- 팀원 답은 다음 `/discord-huddle-sync`로 받아온다 (REST 폴링). 실시간 수신은 `/discord-huddle-listen`.

## 쓰임새

- 웹 대시보드/도구 화면 스크린샷을 팀원에게 공유
- 요약 md의 도식 이미지를 팀 회의용으로 전송
- Claude Code에서 생성한 옵션 리스트를 디스코드에서 검토받기
- 빌드 릴리즈 URL 같은 후속 파이프라인 결과 공지 (예: Unity 플러그인의 `/publish-build` 출력 URL을 받아 전송)

## 플러그인 조합 예

`/publish-build` (unity-gamedev 플러그인)가 릴리즈 URL을 JSON stdout으로 반환하면, 이 스킬로 파이프 연결해 팀에 공지:

```bash
OUT=$(python bot/publish_build.py --tag v0.1.0 --skip-build)
URL=$(echo "$OUT" | jq -r .url)
python bot/discord_collab.py post --message "🚀 새 빌드: $URL"
```
