# discord-huddle

Discord 채널을 프로젝트의 **팀 채팅 · 회의록 · 공지 파이프**로 쓰게 해주는 [system-agents-template](https://github.com/southglory/system-agents-template) 플러그인.

- **Pull**: 채널 메시지를 로컬 JSONL로 덤프 (`/discord-huddle-sync`)
- **Push**: 에이전트·사용자가 메시지를 채널에 게시 (`/discord-huddle-post`)
- **Listen**: Gateway WebSocket으로 실시간 알림 (`/discord-huddle-listen`)
- **Summarize**: 에이전트가 직접 raw를 읽고 팀 회의록 md로 정리 (`/discord-huddle-summarize`, LLM API 호출 없음)

## 설치

프로젝트 루트에서:

```bash
# 1. 플러그인 파일 복사
cp -r discord-huddle/bot/* ./bot/
cp -r discord-huddle/skills/* ./skills/
# (system-agents-template 프로젝트에 설치한다면 ./bot, ./skills가 이미 있음)

# 2. Python 의존 설치
pip install -r discord-huddle/requirements.txt

# 3. 스킬을 Claude Code에 설치 (전역)
cp -r discord-huddle/skills/* ~/.claude/skills/
```

설정 파일 작성은 `docs/SETUP.md` 참조. 스모크 테스트는 `docs/SMOKE_TEST.md`.

## 주요 기능

### REST 동기화 + 실시간 리스너

- `sync`는 REST polling으로 last_read 이후 모든 메시지 수집
- `listen`(Gateway)은 WebSocket으로 실시간 신호 수신 → 파일 변경으로 Claude Code Monitor에 연결
- 둘은 병행 가능 — 리스너는 속도, sync는 완전성 (첨부 다운로드 등)

### 양방향

- 팀원 → 에이전트: Discord 채팅으로 기획 / 피드백 / 요청
- 에이전트 → 팀원: 분석 결과, 도식 이미지, Visual Companion 스냅샷, 빌드 릴리즈 URL 등을 채널에 게시

### 요약을 팀 자산으로

- 요약 md는 `docs/discord-huddle-summaries/`에 쌓이고 **git으로 트래킹됨**
- 새 팀원이 `git clone` 하면 과거 회의록을 바로 읽음
- 요약 진행 포인터(`index.json`)도 git에 포함 → 머지 충돌 나도 "더 뒤 msg_id 선택"으로 기계적 해결

### 경로 캡슐화

- 런타임 데이터(`raw`, `inbox`, `local-state`)는 `.system-agents/discord-huddle/`에 격리 + 자동 `.gitignore: *` 드롭
- 프로젝트 `.gitignore`를 **건드리지 않음**
- 환경변수로 경로 전부 재정의 가능

## 스킬 목록

| 슬래시 명령 | 설명 |
|---|---|
| `/discord-huddle-sync` | 채널 새 메시지 → raw JSONL |
| `/discord-huddle-listen` | Gateway WebSocket 실시간 리스너 |
| `/discord-huddle-post` | 메시지/파일/VC 스냅샷을 채널에 게시 |
| `/discord-huddle-summarize` | 에이전트가 raw 읽고 요약 md 작성 |

각 스킬 상세는 `skills/*/SKILL.md` 참조.

## 웹 페이지 스냅샷 (선택 기능)

`/discord-huddle-post --vc-snapshot`으로 임의의 웹 페이지를 헤드리스 Chromium으로 렌더링해 PNG로 첨부한다.

- **URL 직접 지정**: `--vc-url https://my-dashboard.local`
- **자동 탐지 (선택)**: `--vc-url` 대신 `--vc-sessions-dir DIR` 또는 `VC_SESSIONS_DIR` env를 설정하면 `DIR/<session>/state/server-info` 구조에서 가장 최근 live URL을 자동으로 집는다. 어떤 도구가 그 구조로 서버 정보를 남기든 상관 없음.
- **의존**: `pip install -r requirements-optional.txt` + `playwright install chromium` (최초 1회, 약 200MB)

어떤 외부 도구와도 결합하지 않는 범용 기능 — 대시보드, 내부 콘솔, 기획 도구 등 URL이 있는 건 모두 지원.

## 데이터 위치

| 경로 | 내용 | git 트래킹 |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Raw 메시지 덤프 | 자동 gitignore |
| `.system-agents/discord-huddle/inbox/` | Gateway 실시간 신호 | 자동 gitignore |
| `.system-agents/discord-huddle/local-state.json` | 개인 sync 포인터 | 자동 gitignore |
| `.system-agents/discord-huddle/vc-snapshots/` | VC 스냅샷 PNG | 자동 gitignore |
| `docs/discord-huddle-summaries/*.md` | 팀 회의록 | **트래킹** |
| `docs/discord-huddle-summaries/index.json` | 요약 진행 포인터 | **트래킹** |
| `docs/discord-huddle-summaries/attachments/` | 요약용 대표 이미지 | **트래킹** |

## 조합 가능한 플러그인

| 대상 | 조합 효과 | 추가 설정 | Recipe |
|---|---|---|---|
| Claude Code 내장 `/schedule` | 정기 알림을 채널에 자동 게시 (스탠드업, 주간 리포트, 릴리즈 카운트다운 등) | `/schedule`로 `discord-huddle-post` 호출을 cron 등록 | — (얇은 조합이라 recipe 없음, 아래 예시 참고) |
| (예정) unity-gamedev | Unity 빌드 → GitHub 릴리즈 → 채널에 링크 자동 공지 | 두 플러그인 모두 설치, `publish-build` 출력 URL을 `discord-huddle-post`에 파이프 | `recipes/unity-build-to-discord/` (unity-gamedev 공개 후 추가) |

### 예: Claude Code `/schedule`로 데일리 스탠드업 알림

```
/schedule name:daily-standup cron:"0 9 * * 1-5" \
  command:"python bot/discord_collab.py post --message '☀️ 데일리 스탠드업 시간입니다'"
```

주의: 실행 호스트가 해당 시각에 **켜져 있어야** 동작한다. 가정용 PC로 24/7 상시 알림이 필요하다면 Sesh 같은 서드파티 Discord 스케줄러 봇이나 서버리스 cron을 고려.

## 요구사항

- Python ≥ 3.10
- Discord Bot Token (Developer Portal에서 발급)
- **Message Content Intent** 활성화 (Gateway listener 사용 시 필수)

## 라이선스

MIT — `system-agents-plugins` 레포 루트 `LICENSE` 참조.

## 관련 문서

- [SETUP.md](docs/SETUP.md) — 설치 및 설정
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 수동 스모크 테스트 체크리스트
- 상위 레포 [README.md](../README.md) — 플러그인 생태계 개요
