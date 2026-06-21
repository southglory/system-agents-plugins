#!/usr/bin/env python3
"""
build_persona.py — Claude Code 발화를 분석해 페르소나를 생성/갱신한다.

다중 계정 지원: cc-switch 방식(CLAUDE_CONFIG_DIR)으로 계정마다 config 디렉터리가
다르다(~/.claude, ~/.claude-work, ~/.claude-<이름> ...). 각 디렉터리에 history.jsonl이 있다.
이 스크립트는 ~/.claude* 를 자동 탐지하고, 계정/프로젝트를 골라 페르소나를 만든다.

사용:
    python3 build_persona.py                      # 인터랙티브: 계정+프로젝트 선택
    python3 build_persona.py --all                # 모든 계정+모든 프로젝트, 묻지 않음
    python3 build_persona.py --accounts ~/.claude,~/.claude-work
    python3 build_persona.py --projects A,B        # project 경로에 부분일치하는 것만
    python3 build_persona.py --list                # 계정/프로젝트 목록만 출력
    python3 build_persona.py --out DIR             # 출력 위치(기본 ~/.claude/persona)
    python3 build_persona.py --dry-run

출력:
    <out>/PERSONA.md       (없을 때만 골격 생성; 수기 섹션 보존)
    <out>/PERSONA_POOL.md  (자동 생성/갱신)
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter

HOME = os.path.expanduser("~")
DEFAULT_OUT = os.path.join(HOME, ".claude", "persona")


# ---------- 계정(config 디렉터리) 탐지 ----------
def discover_accounts():
    """~/.claude, ~/.claude-* 중 history.jsonl 을 가진 디렉터리를 반환."""
    cands = [os.path.join(HOME, ".claude")] + sorted(glob.glob(os.path.join(HOME, ".claude-*")))
    out = []
    seen = set()
    for d in cands:
        if d in seen:
            continue
        seen.add(d)
        h = os.path.join(d, "history.jsonl")
        if os.path.isdir(d) and os.path.isfile(h):
            out.append(d)
    return out


def history_path(account_dir):
    return os.path.join(account_dir, "history.jsonl")


# ---------- 발화 로드 ----------
def load_records(account_dirs):
    """선택된 계정들의 history.jsonl 에서 (project, display) 레코드를 모은다."""
    recs = []
    for d in account_dirs:
        p = history_path(d)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                t = (rec.get("display") or "").strip()
                if t and not t.startswith("/") and not t.startswith("["):
                    recs.append((rec.get("project", "?"), t, d))
    return recs


def project_counts(recs):
    c = Counter(proj for proj, _, _ in recs)
    return c.most_common()


def filter_projects(recs, substrings):
    if not substrings:
        return recs
    subs = [s.strip() for s in substrings if s.strip()]
    return [(p, t, d) for (p, t, d) in recs if any(s in p for s in subs)]


# ---------- 풀 생성 ----------
def top(prompts, pred, lim=20, maxlen=45):
    c = Counter(p for p in prompts if pred(p) and len(p) <= maxlen and "\n" not in p)
    return c.most_common(lim)


def build_pool(prompts, sources_note):
    cats = {
        "승인 / 계속 진행": lambda p: any(k in p for k in ["그렇게", "계속", "진행"]) and not p.endswith("?"),
        "칭찬 / 만족": lambda p: any(k in p for k in ["좋", "고맙", "감사", "최고", "훌륭"]) and not p.endswith("?"),
        "검증 되묻기 (의심날 때)": lambda p: p.endswith("?") and any(k in p for k in ["아니", "없", "맞", "되", "문제", "별로", "괜찮"]),
        "진척 체크 / 선택 위임": lambda p: p.endswith("?") and any(k in p for k in ["됐", "얼마", "지금", "추천", "뭐", "어때", "나아"]),
    }
    out = ["# PERSONA POOL — 실제 발화 풀 (자동 생성)", ""]
    out.append(f"> {sources_note}")
    out.append("> 자율 루프가 사용자 응답을 자가 생성할 때 상황에 맞는 표현을 여기서 고른다.")
    out.append("")
    for title, pred in cats.items():
        out.append(f"## {title}")
        rows = top(prompts, pred)
        if not rows:
            out.append("- (해당 발화 없음)")
        for p, n in rows:
            out.append(f"- {p} ({n})")
        out.append("")
    return "\n".join(out)


def write_if_changed(path, content, dry):
    if dry:
        print(f"--- [dry-run] {path} ---")
        print(content[:1500])
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    if old == content:
        print(f"unchanged: {path}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"written: {path}")


# ---------- 인터랙티브 선택 ----------
def choose_multi(title, items, labels):
    """번호 중복선택. 'a'=전체, 빈입력=전체. items와 labels 길이 동일."""
    print(f"\n{title}")
    for i, lab in enumerate(labels, 1):
        print(f"  {i}. {lab}")
    print("  (쉼표로 여러 개, 'a'=전체, 엔터=전체)")
    raw = input("선택> ").strip()
    if raw == "" or raw.lower() == "a":
        return list(items)
    picked = []
    for tok in raw.replace(" ", "").split(","):
        if tok.isdigit() and 1 <= int(tok) <= len(items):
            picked.append(items[int(tok) - 1])
    return picked or list(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="모든 계정+프로젝트, 묻지 않음")
    ap.add_argument("--accounts", default="", help="콤마구분 계정 config 디렉터리")
    ap.add_argument("--projects", default="", help="콤마구분 project 부분일치 필터")
    ap.add_argument("--list", action="store_true", help="계정/프로젝트 목록만 출력")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    accounts = discover_accounts()
    if not accounts:
        print("오류: history.jsonl을 가진 Claude config 디렉터리를 찾지 못함.", file=sys.stderr)
        sys.exit(1)

    if args.list:
        print("=== 탐지된 계정 (config 디렉터리) ===")
        for d in accounts:
            print(f"  {d}  ({wc(history_path(d))} lines)")
        recs = load_records(accounts)
        print("\n=== 프로젝트(세션 소스)별 발화 수 ===")
        for proj, n in project_counts(recs):
            print(f"  {n:5d}  {proj}")
        return

    # 계정 선택
    if args.accounts:
        sel_accounts = [os.path.expanduser(a.strip()) for a in args.accounts.split(",") if a.strip()]
    elif args.all:
        sel_accounts = accounts
    else:
        labels = [f"{d}  ({wc(history_path(d))} lines)" for d in accounts]
        sel_accounts = choose_multi("어떤 계정(config 디렉터리)을 쓸까요?", accounts, labels)

    recs = load_records(sel_accounts)

    # 프로젝트 선택
    if args.projects:
        recs = filter_projects(recs, args.projects.split(","))
        sources_note = f"계정: {', '.join(sel_accounts)} / 프로젝트 필터: {args.projects}"
    elif args.all:
        sources_note = f"계정: {', '.join(sel_accounts)} / 모든 프로젝트"
    else:
        pcounts = project_counts(recs)
        projs = [p for p, _ in pcounts]
        labels = [f"{p}  ({n})" for p, n in pcounts]
        chosen = choose_multi("어떤 프로젝트 세션을 페르소나 재료로 쓸까요?", projs, labels)
        recs = [(p, t, d) for (p, t, d) in recs if p in set(chosen)]
        sources_note = f"계정: {', '.join(sel_accounts)} / 프로젝트 {len(chosen)}개 선택"

    prompts = [t for _, t, _ in recs]
    print(f"\n분석한 발화 수: {len(prompts)}  ({sources_note})")
    if not prompts:
        print("경고: 선택된 조건에 발화가 없음.", file=sys.stderr)

    pool = build_pool(prompts, sources_note)
    write_if_changed(os.path.join(args.out, "PERSONA_POOL.md"), pool, args.dry_run)

    persona_path = os.path.join(args.out, "PERSONA.md")
    if not os.path.exists(persona_path) and not args.dry_run:
        seed = (
            "# PERSONA — 사용자 페르소나 프로필\n\n"
            "> 자율 루프가 사용자 대신 응답을 자가 생성할 때 따르는 프로필.\n"
            "> 말투/성향/안전경계는 수기로 다듬는다. 응답 풀은 PERSONA_POOL.md(자동).\n\n"
            "## 말투 / 문체\n- 짧고 단정적. \"~합시다/~하자\" 혼용.\n\n"
            "## 의사결정 성향\n- 큰 흐름은 잘 맡김. 의심나면 거절 대신 \"~아니지?\"로 되묻는다.\n\n"
            "## 안전 경계 — 가역성 + 외부 영향 기준\n"
            "- ✅ 자율 OK: 커밋, 비공개 push, 로컬 변경, 빌드/테스트\n"
            "- ⛔ 실제 사용자 확인: 공개 push·배포·외부전송·복구불가 삭제\n"
        )
        write_if_changed(persona_path, seed, args.dry_run)
    else:
        print(f"keep (수기 보존): {persona_path}")


def wc(path):
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


if __name__ == "__main__":
    main()
