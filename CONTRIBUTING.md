# Contributing to system-agents-plugins

새 플러그인을 추가하거나 기존 플러그인을 수정할 때 따라야 할 규약.

## 플러그인 폴더 규약

각 플러그인은 레포 루트 하위 한 폴더로 배치한다. 내부 구조:

```
<plugin-name>/
├── README.md                ← 필수. 아래 규약 따름
├── requirements.txt         ← 기본 Python 의존 (있으면)
├── requirements-optional.txt ← 선택 기능용 (있으면)
├── requirements-dev.txt     ← 개발/테스트 (있으면)
├── bot/                     ← 실행 코드
├── skills/                  ← 슬래시 스킬 (SKILL.md)
├── docs/                    ← SETUP.md, SMOKE_TEST.md 등
└── samples/                 ← .env 템플릿 등 사용자 복사용
```

`tests/`가 있다면 `bot/tests/` 하위에 둔다 (플러그인 외부에서 `pytest`로 실행 가능하도록).

## 플러그인 README.md 필수 섹션

플러그인 README는 **최소 다음 섹션을 모두 포함**해야 한다:

1. **제목 + 한 문장 설명** — 이 플러그인이 뭘 해주는지
2. **설치** — `cp -r`, `pip install` 명령 구체적으로
3. **스킬 목록** — 제공하는 슬래시 명령 표 (command, description)
4. **요구사항** — Python 버전, 외부 도구(Unity CLI, ffmpeg 등), 토큰/키 필요 여부
5. **데이터 위치** — 플러그인이 만드는 파일들이 어디에 쌓이는지 표로. git 트래킹 여부 포함
6. **조합 가능한 플러그인** — 다른 플러그인과의 호환성 표 (하단 세부 규약 참조)
7. **라이선스** — MIT (레포 전체 통일)

세부 섹션은 유연하게 추가/변경 가능하나 위 7개는 필수.

## "조합 가능한 플러그인" 섹션 규약

표 형식:

```markdown
## 조합 가능한 플러그인

| 플러그인 | 조합 효과 | 추가 설정 | Recipe |
|---|---|---|---|
| unity-gamedev | Unity 빌드 → 릴리즈 → 채널 공지 | 두 플러그인 모두 설치 | `recipes/unity-build-to-discord/` |
| (예정) web-e2e | Playwright E2E 결과 채널 공지 | 두 플러그인 모두 설치 | — |
```

- "예정" 조합은 아직 실제 recipe가 없어도 표에 미리 적어둘 수 있음 (로드맵 가시화)
- 조합이 하나도 없으면 "없음" 으로 명시 — 섹션 자체를 빠뜨리면 안 됨

## Recipe 추가 규약

`recipes/<combo-name>/` 하위 구조:

```
recipes/<combo-name>/
├── README.md       ← 어떤 플러그인 조합인지, 설치 방법, 호출 예
├── skills/         ← 조합 실행 스킬 (필요 시)
└── requirements.txt ← 조합 전용 추가 의존 (거의 없을 것)
```

Recipe README는 반드시:
- **전제 플러그인** 목록 (버전 명시)
- **설치 순서**
- **최소 동작 예시** (실제로 돌아가는 커맨드)
- **알려진 제약** (예: 두 플러그인이 같은 채널을 공유해야 함)

## 버전 태그 규약

각 플러그인은 독립 릴리즈. 태그 형식: `<plugin-name>-vX.Y.Z`.

- 의미는 [SemVer](https://semver.org/)를 따른다
- `0.x.x` — 실험적, 호환성 파괴 변경 허용
- `1.0.0` 이후 — 메이저 버전업 없이는 호환성 파괴 금지

릴리즈 시 변경 요약은 GitHub Release Notes에.

## 경로/설정 파라미터화 원칙

플러그인은 **설치 프로젝트 구조를 강제하지 않는다**.

- 파일 경로는 환경변수로 오버라이드 가능해야 함
- 기본값은 `.system-agents/<plugin-name>/` (런타임) + `docs/<human-readable>/` (팀 자산) 패턴 권장
- 런타임 디렉토리는 자기 안에 `.gitignore: *` 를 자동으로 드롭해서 프로젝트 `.gitignore`를 건드리지 않는다

## PR 체크리스트

PR 제출 전 확인:

- [ ] 플러그인 README가 위 7개 필수 섹션을 모두 포함한다
- [ ] 스킬 SKILL.md가 있다 (슬래시 커맨드마다 하나씩)
- [ ] `bot/tests/`가 있고 `pytest` 통과한다 (CI가 아직 없다면 로컬에서)
- [ ] 경로 하드코딩이 없다 (`grep -rn "parents\[2\]\|Agent-system"` 결과 0줄)
- [ ] `samples/` 아래 `.env` 템플릿이 필요한 모든 키를 포함한다 (값은 비워둠)
- [ ] 라이선스 헤더/MIT 호환

## 이슈/피드백

- 플러그인별 버그: GitHub Issues에 `[plugin:<name>]` 접두사로 제목 작성
- 생태계 전반 제안: `[meta]` 접두사
