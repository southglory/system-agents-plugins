# discord-huddle


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![discord-huddle release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=discord-huddle-*&label=discord-huddle)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Discord 채널을 프로젝트의 **팀 채팅 · 회의록 · 공지 파이프**로 쓰게 해주는 [system-agents-template](https://github.com/southglory/system-agents-template) 플러그인.

- **Pull**: 채널 메시지를 로컬 JSONL로 덤프 (`/discord-huddle-sync`)
- **Push**: 에이전트·사용자가 메시지를 채널에 게시 (`/discord-huddle-post`)
- **Listen**: Gateway WebSocket으로 실시간 알림 (`/discord-huddle-listen`)
- **Summarize**: 에이전트가 직접 raw를 읽고 팀 회의록 md로 정리 (`/discord-huddle-summarize`). Claude Code 세션 외 별도 LLM API 호출 없음

## 🚀 한 줄 설치 (권장)

이 레포를 직접 clone하지 말고, 템플릿의 설치기를 써라:

롤링 (항상 `main` 최신):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

고정 릴리즈 (재현성 권장):

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


플러그인 목록이 뜨면 `discord-huddle` 선택. 설치기가 파일 복사 + 전역 슬래시 스킬 등록 + `.claude/secrets/discord-huddle.env.example` 씨드까지 자동. 설치 후 secrets 파일에 Bot Token + Channel ID만 채우면 끝.

상세 설치: [`docs/SETUP.md`](docs/SETUP.md). 수동 스모크 테스트: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## 주요 기능

### REST sync + 실시간 listener

- `sync`는 REST polling으로 last_read 이후 모든 메시지 수집
- `listen`(Gateway)은 WebSocket으로 실시간 신호 수신 → 파일 변경으로 Claude Code Monitor에 연결
- 둘은 병행 가능 — 리스너는 속도, sync는 완전성 (첨부 다운로드 등)

### 양방향

- 팀원 → 에이전트: Discord 채팅으로 기획 / 피드백 / 요청
- 에이전트 → 팀원: 분석 결과, 도식 이미지, 웹페이지 스냅샷, 빌드 릴리즈 URL 등을 채널에 게시

### 요약을 팀 자산으로

- 요약 md는 `docs/discord-huddle-summaries/`에 쌓이고 **git으로 트래킹됨**
- 새 팀원이 `git clone` 하면 과거 회의록을 바로 읽음
- 요약 진행 포인터(`index.json`)도 git에 포함 → 머지 충돌 나도 "더 뒤 msg_id 선택"으로 기계적 해결

### 결정론적 summarize 게이트

에이전트가 요약에 토큰을 쓰기 전에 먼저 호출:

```bash
python bot/discord_collab.py summarize-check
```

코드만으로 raw를 스캔해 `{ready, reason, stats}` JSON 반환. `ready:false`(메시지 수 부족, 짧은 독백 등)면 에이전트는 raw를 컨텍스트에 로드하지 않고 즉시 종료. 전체 규칙은 [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md).

### 경로 캡슐화 (비침습 설치)

- 런타임 데이터(`raw`, `inbox`, `local-state`, `vc-snapshots`)는 `.system-agents/discord-huddle/`에 격리 + 자동 `.gitignore: *` 드롭
- **프로젝트 `.gitignore`를 건드리지 않음**
- 같은 `.env` 에서 경로 오버라이드 가능 (별도 `export` 불필요):
  `SYSTEM_AGENTS_PROJECT_ROOT`, `DISCORD_HUDDLE_DATA_DIR`, `DISCORD_HUDDLE_SUMMARY_DIR`

### 친화적 에러 메시지

Raw Python traceback 노출 없음. 401/403/404/429 각각에 정확한 해결 안내 한 줄(Reset Token, 봇 재초대, 채널 ID 확인, 레이트 리밋 등) 포함.

## 스킬 목록

| 슬래시 명령 | 설명 |
|---|---|
| `/discord-huddle-sync` | 채널 새 메시지 → raw JSONL |
| `/discord-huddle-listen` | Gateway WebSocket 실시간 리스너 |
| `/discord-huddle-post` | 메시지/파일/웹 페이지 스냅샷을 채널에 게시 |
| `/discord-huddle-summarize` | 에이전트가 raw 읽고 요약 md 작성 |

각 스킬 상세는 `skills/*/SKILL.md` 참조.

## 웹 페이지 스냅샷 (선택 기능)

`/discord-huddle-post --vc-snapshot`으로 임의의 웹 페이지를 헤드리스 Chromium으로 렌더링해 PNG로 첨부.

- **URL 직접 지정**: `--vc-url https://my-dashboard.local`
- **자동 탐지 (선택)**: `--vc-url` 대신 `--vc-sessions-dir DIR` 또는 `VC_SESSIONS_DIR` env를 설정하면 `DIR/<session>/state/server-info` 구조에서 가장 최근 live URL을 자동 집는다. 어떤 도구가 그 구조로 서버 정보를 남기든 상관없음.
- **의존**: `pip install -r requirements-optional.txt` + `playwright install chromium` (최초 1회, 약 200MB)

어떤 외부 도구와도 결합하지 않는 범용 기능.

## 데이터 위치 (기본값)

| 경로 | 내용 | git 트래킹 |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Raw 메시지 덤프 | 자동 gitignore |
| `.system-agents/discord-huddle/inbox/` | Gateway 실시간 신호 | 자동 gitignore |
| `.system-agents/discord-huddle/local-state.json` | 개인 sync 포인터 | 자동 gitignore |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright PNG | 자동 gitignore |
| `docs/discord-huddle-summaries/*.md` | 팀 회의록 | **트래킹** |
| `docs/discord-huddle-summaries/index.json` | Forward-only 요약 포인터 | **트래킹** |
| `docs/discord-huddle-summaries/attachments/` | 요약이 참조하는 이미지 | **트래킹** |

## 조합 가능한 플러그인

| 대상 | 조합 효과 | 추가 설정 | Recipe |
|---|---|---|---|
| Claude Code 내장 `/schedule` | 정기 알림을 채널에 자동 게시 (스탠드업, 주간 리포트, 릴리즈 카운트다운 등) | `/schedule`로 `discord-huddle-post` 호출을 cron 등록 | — (얇은 조합이라 recipe 없음, 아래 예시 참고) |
| [`unity-gamedev`](../unity-gamedev/) | Unity 빌드 → GitHub 릴리즈 → 채널에 링크 자동 공지 | 두 플러그인 모두 설치, `publish-build` 출력 URL을 `discord-huddle-post`에 파이프 | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

### 예: Claude Code `/schedule`로 데일리 스탠드업 알림

```
/schedule name:daily-standup cron:"0 9 * * 1-5" \
  command:"python bot/discord_collab.py post --message '☀️ 데일리 스탠드업 시간입니다'"
```

주의: 실행 호스트가 해당 시각에 **켜져 있어야** 동작. 가정용 PC로 24/7 상시 알림이 필요하다면 Sesh 같은 서드파티 Discord 스케줄러 봇이나 서버리스 cron을 고려.

## 요구사항

- Python ≥ 3.10
- Discord Bot Token ([Developer Portal](https://discord.com/developers/applications)에서 발급)
- **Message Content Intent** 활성화 (Gateway listener 사용 시 필수)

## 라이선스

MIT — 레포 루트 [`LICENSE`](../LICENSE) 참조.

## 관련 문서

- [SETUP.md](docs/SETUP.md) — 설치 및 설정
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 수동 스모크 테스트 체크리스트
- 레포 루트 [README](../README.md) — 플러그인 생태계 개요

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
