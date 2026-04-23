---
name: discord-huddle-summarize
description: 쌓인 Discord Huddle raw JSONL을 Claude Code 에이전트가 직접 읽고 요약 md로 작성한다 (LLM API 호출 없음)
---

# Discord Huddle Summarize

`/discord-huddle-summarize` 명령이 수행하는 작업.

## 사전 조건

- `/discord-huddle-sync`가 최소 1회 성공해 `.system-agents/discord-huddle/raw/*.jsonl`이 있다.
- `summarize-check`가 `ready:true` 를 반환하는 수준의 내용이 쌓여 있다 (아래 참조).

## 반드시 첫 단계로 — 결정론적 게이트 호출

요약 본문을 작성하기 전에 에이전트는 반드시 다음을 먼저 실행하여 **요약할 가치가 있는지** 코드 수준에서 확인한다. 이 호출은 LLM을 전혀 쓰지 않고 raw JSONL을 직접 스캔하므로, `ready:false`면 에이전트는 바로 사용자에게 결과를 전달하고 종료한다(토큰 거의 소비하지 않음).

```bash
python bot/discord_collab.py summarize-check
```

표준출력은 JSON 한 덩어리:

```json
{
  "ready": false,
  "reason": "short_monologue",
  "channel_id": "...",
  "after_msg_id": "...",
  "stats": {
    "message_count": 7,
    "total_content_chars": 42,
    "unique_participants": 1,
    "attachment_count": 0,
    "time_span_seconds": 420.0,
    "first_msg_id": "...",
    "last_msg_id": "..."
  }
}
```

### 게이트 규칙 (OR 조합, 결정론적)

다음 중 **하나라도 만족**하면 `ready:true`:

1. `message_count >= 5` **AND** `total_content_chars >= 100` — 독백이지만 내용 있음.
2. `unique_participants >= 2` **AND** `message_count >= 3` — 실제 대화가 오감. 짧은 결정도 가치 있음.
3. `attachment_count >= 2` — 시각 자료 기반 논의.

위 세 조건 모두 탈락하면 `ready:false` + 다음 `reason` 중 하나:

- `no_new_messages` — 마지막 요약 이후 새 메시지가 전혀 없음.
- `too_few_messages` — 3건 미만. 대화라 보기도 어려움.
- `short_monologue` — 한 명이 짧게 몇 마디 한 수준. 요약 의미 없음.
- `insufficient_content` — 위 분류 어디에도 안 맞는 애매한 부족.

에이전트는 `reason`을 사용자에게 전달하여 왜 요약을 건너뛰었는지 설명한다.

## 동작

1. `summarize-check` 호출 → JSON 파싱. `ready:false`면 즉시 종료(토큰 절약).
2. `ready:true`일 때만 다음으로 진행. `docs/discord-huddle-summaries/index.json`의 `last_summarized`를 기준으로 raw 메시지 선별 (forward-only 포인터).
3. 에이전트(Claude Code 세션)가 직접 JSONL을 읽고 `docs/discord-huddle-summaries/YYYY-MM-DD_HHMM.md`로 요약 작성. 본문 섹션 순서: `## 요약` → `## 도식` → `## 주요 주제별 정리` → `## 타임라인`.
4. 파일 상단에 YAML frontmatter로 range 메타데이터를 **반드시** 기록 (`source`, `channel`, `from_msg`, `to_msg`, `start`, `end`, `participants`, `message_count`, `attachments`).
5. 대표 이미지를 `docs/discord-huddle-summaries/attachments/{summary_stem}/`로 복사 (필요 시).
6. `index.json`의 `last_summarized`, `last_file`을 forward-only로 갱신 (더 오래된 msg_id로는 되돌려지지 않음).

## 요약 md frontmatter 예

```yaml
---
source: discord
channel: general
from_msg: "1496056458826219600"
to_msg: "1496057987075281037"
start: "2026-04-21T07:54:15.169000+00:00"
end: "2026-04-21T08:00:19.532000+00:00"
participants:
  - Alice
  - Bob
message_count: 3
attachments: []
---
```

## 도식 작성 원칙

원본 Discord 대화에 이미지가 없더라도, 결정된 **게임 루프 / 씬 구조 / 상태 분기 / 결정 타임라인** 같은 추상 개념은 에이전트가 직접 시각화해 `## 도식` 섹션에 넣는다.

- 흐름/분기/사이클 → mermaid `flowchart`
- 시간 흐름 → mermaid `timeline`
- 공간·레이아웃 → ASCII 박스

Claude Code 세션이 직접 md를 작성하므로 LLM API 키가 필요 없다. 슬래시 커맨드가 에이전트에게 지시하는 형태.

## 수동 범위 지정

특정 구간을 채우고 싶으면:

```bash
# 현재 last_summarized 이후 → 이 구간을 건너뛰고 더 뒤를 먼저 요약하고 싶을 때
#   → 그냥 실행하면 됨 (forward 자동)
# 빈 구간을 보충하고 싶으면 수동 범위 지정 (state는 더 큰 값일 때만 forward)
python bot/discord_collab.py summarize --from-msg <ID> --to-msg <ID>
```

현재 구현에선 summarize CLI는 에이전트가 직접 md를 작성하는 구조라 범위 지정은 에이전트가 결정하며, 상태 갱신은 `storage.update_last_summarized()`가 forward-only를 강제한다.

## 결과

- 요약 md 경로와 간단한 미리보기가 사용자에게 출력됨.
- 이후 다른 에이전트들도 해당 md를 맥락으로 읽을 수 있다.
- `docs/discord-huddle-summaries/`는 git 트래킹 대상 — 팀원이 pull 받으면 회의록이 따라옴.
