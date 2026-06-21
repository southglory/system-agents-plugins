#!/usr/bin/env bash
#
# backup_persona.sh — 수기로 다듬은 페르소나(PERSONA.md 등)를 비공개로 백업/복원.
#
# 페르소나는 개인 발화 기반이라 공개 repo에 올리면 안 된다.
# 그래서 git 밖, 홈 아래 비공개 디렉터리에 타임스탬프 사본을 둔다.
# PERSONA_POOL.md 는 build_persona.py 로 언제든 재생성되므로 함께 떠두되 핵심은 PERSONA.md.
#
# 사용:
#   ./backup_persona.sh            # 현재 공용 페르소나를 백업
#   ./backup_persona.sh restore    # 가장 최근 백업으로 복원
#   ./backup_persona.sh list       # 백업 목록
#
set -euo pipefail

PERSONA_DIR="$HOME/.claude/persona"
BACKUP_ROOT="$HOME/.persona-backups"   # git 밖, 비공개

cmd="${1:-backup}"

case "$cmd" in
  backup)
    if [ ! -f "$PERSONA_DIR/PERSONA.md" ]; then
      echo "백업할 PERSONA.md 가 없습니다: $PERSONA_DIR" >&2; exit 1
    fi
    # 타임스탬프는 셸에서 생성(스크립트라 OK)
    ts="$(date +%Y%m%d-%H%M%S)"
    dest="$BACKUP_ROOT/$ts"
    mkdir -p "$dest"
    chmod 700 "$BACKUP_ROOT"
    cp -p "$PERSONA_DIR"/PERSONA.md "$dest/" 2>/dev/null || true
    cp -p "$PERSONA_DIR"/PERSONA_POOL.md "$dest/" 2>/dev/null || true
    # latest 심볼릭 링크 갱신
    ln -sfn "$dest" "$BACKUP_ROOT/latest"
    echo "✅ 백업 완료: $dest"
    ls -la "$dest"
    ;;
  restore)
    src="$BACKUP_ROOT/latest"
    if [ ! -e "$src/PERSONA.md" ]; then
      echo "복원할 백업이 없습니다: $src" >&2; exit 1
    fi
    mkdir -p "$PERSONA_DIR"
    cp -p "$src/PERSONA.md" "$PERSONA_DIR/"
    [ -f "$src/PERSONA_POOL.md" ] && cp -p "$src/PERSONA_POOL.md" "$PERSONA_DIR/" || true
    echo "✅ 복원 완료 ($(readlink -f "$src")) → $PERSONA_DIR"
    ;;
  list)
    echo "백업 위치: $BACKUP_ROOT"
    ls -1 "$BACKUP_ROOT" 2>/dev/null | grep -vx latest || echo "(백업 없음)"
    ;;
  *)
    echo "사용: $0 [backup|restore|list]" >&2; exit 1
    ;;
esac
