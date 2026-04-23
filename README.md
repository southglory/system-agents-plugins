# system-agents-plugins

[system-agents-template](https://github.com/southglory/system-agents-template)을 위한 공식 플러그인 모음.

각 플러그인은 이 레포의 하위 폴더로 독립적으로 배포된다. 사용자는 필요한 플러그인만 골라 설치한다.

## 플러그인 목록

| 폴더 | 설명 | 상태 |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Discord 채널을 팀 채팅 + 회의록 파이프로 | ✅ 배포 (v0.1.0) |
| `unity-gamedev/` | Unity CLI 빌드 + GitHub Release 퍼블리시 | 🚧 준비 중 |

## 설치 모델

플러그인은 `cp -r` 방식의 파일 복사로 설치된다. npm·pypi 같은 패키지 매니저는 쓰지 않는다 — 이 플러그인 생태계는 **사용자의 프로젝트 파일 트리와 직접 결합**하기 때문.

```bash
# 1. 이 레포 clone
git clone https://github.com/southglory/system-agents-plugins.git
cd system-agents-plugins

# 2. 원하는 플러그인을 대상 프로젝트로 복사
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. 스킬을 Claude Code에 등록
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Python 의존
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

각 플러그인의 상세 설치는 해당 폴더의 `README.md` 참고.

## 버전 태그 규약

플러그인별 독립 릴리즈. 태그 형식: `<plugin-name>-vX.Y.Z`

- `discord-huddle-v0.1.0` — discord-huddle 첫 배포
- `unity-gamedev-v0.1.0` — (예정)

레포 전체 단일 버전은 쓰지 않는다.

## 조합 전략

플러그인은 서로 **독립적으로 동작**하지만 함께 쓰면 더 강력한 경우가 있다. 세 레벨이 있다:

- **레벨 1 — 조합 표**: 각 플러그인 `README.md`의 "조합 가능한 플러그인" 섹션에 호환성 매트릭스 명시. 필수.
- **레벨 2 — Recipe**: 자주 쓰이는 조합은 `recipes/<combo-name>/`에 레시피 폴더로 제공. 선택.
- **레벨 3 — 자동 설치**: 도입 계획 없음. 사용자가 어떤 조합을 쓸지는 선택의 문제.

상세 규약은 [`CONTRIBUTING.md`](CONTRIBUTING.md) 참조.

## 호환성

- Claude Code 환경 (슬래시 스킬 시스템)
- system-agents-template v2.x 이상 (chatrooms, board.yaml, turn-bot)
- Python ≥ 3.10
- Windows/macOS/Linux

각 플러그인이 추가 요구사항을 명시할 수 있다 (예: discord-huddle은 Discord Bot Token 필요).

## 라이선스

[MIT](LICENSE) — system-agents-template과 동일.

## 기여

- 버그·피드백은 GitHub Issues로
- 새 플러그인 PR은 [`CONTRIBUTING.md`](CONTRIBUTING.md)의 구조 규약을 따라야 한다
