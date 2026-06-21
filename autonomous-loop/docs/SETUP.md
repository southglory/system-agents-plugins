# autonomous-loop — SETUP

## 1. 설치 확인
설치 후 프로젝트에 다음이 있어야 한다:
- `skills/autonomous-loop/SKILL.md`
- `TODO.md`, `LOOP_RULES.md`
- `.claude/settings.local.json` (`defaultMode: bypassPermissions`)

## 2. 페르소나 빌드 (1회, 로컬 전용)
```bash
python3 bot/build_persona.py --list     # 어떤 계정/프로젝트가 있는지 확인
python3 bot/build_persona.py            # 계정+프로젝트 골라서 생성 (중복선택)
# 또는
python3 bot/build_persona.py --all      # 모든 계정/프로젝트
```
결과: `~/.claude/persona/PERSONA.md`, `~/.claude/persona/PERSONA_POOL.md`.

다중 계정(cc-switch): `~/.claude`, `~/.claude-work`, `~/.claude-<이름>`가 자동 탐지된다.

## 3. PERSONA.md 다듬기 + 백업
`PERSONA.md`의 말투·성향·**안전경계**를 검토/수정한 뒤 백업:
```bash
bot/backup_persona.sh backup
```

## 4. 루프 시작
프로젝트에서 Claude Code를 열고:
```
/autonomous-loop
```
또는 직접:
```
/loop TODO.md 위에서부터 처리해줘. LOOP_RULES.md와 ~/.claude/persona/ 따라서,
승인 필요한 건 미루고 계속 진행해
```

## 안전 경계 (반드시 이해)
- ✅ 자율: 커밋, 비공개 push, 로컬 변경, 빌드/테스트 (가역적 + 샌드박스 안)
- ⛔ 확인: 공개 push·배포·외부전송·복구불가 삭제·force push·큰 비용
- ⛔는 멈추지 않고 `TODO.md`의 `## 승인 대기`로 미뤄둔 뒤 다음 작업으로 진행한다.
