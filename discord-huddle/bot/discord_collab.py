"""Discord remote collab CLI.

Usage:
  python bot/discord_collab.py sync        # Discord → raw JSONL
  python bot/discord_collab.py status      # current read/summary state
  python bot/discord_collab.py post ...    # send message to Discord

Add ``--project-root PATH`` to any subcommand to override project root
detection (falls back to SYSTEM_AGENTS_PROJECT_ROOT env or cwd walk).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from discord_lib.api import DiscordAPIError, DiscordClient
from discord_lib.config import Config, ConfigError
from discord_lib.post import run_post
from discord_lib.storage import Storage
from discord_lib.sync import run_sync
from discord_lib.vc_snapshot import find_latest_server_url, take_snapshot


_ENV_VC_SESSIONS_DIR = "VC_SESSIONS_DIR"


def _load_config(args) -> Config:
    return Config.load(project_root=getattr(args, "project_root", None))


def _resolve_vc_sessions_dir(cfg: Config, explicit: str | None) -> Path | None:
    """Resolve the sessions directory for auto VC URL detection, or None if unset.

    Precedence: ``--vc-sessions-dir`` flag → ``VC_SESSIONS_DIR`` env var.
    No default. Auto-detection is opt-in — callers without a sessions dir must
    pass ``--vc-url`` directly.
    """
    raw = explicit or os.environ.get(_ENV_VC_SESSIONS_DIR)
    if not raw:
        return None
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = cfg.project_root / p
    return p.resolve()


def _print_discord_error(exc: DiscordAPIError, *, action: str) -> None:
    """Render a DiscordAPIError as a short, friendly stderr message.

    No Python traceback; structured enough for a user to know what to fix.
    """
    print(f"error: {action} failed — {exc}", file=sys.stderr)
    if exc.hint:
        print(f"hint : {exc.hint}", file=sys.stderr)


def cmd_sync(args) -> int:
    cfg = _load_config(args)
    storage = Storage(cfg.data_dir, cfg.summary_dir)
    client = DiscordClient(bot_token=cfg.bot_token)
    try:
        stats = run_sync(cfg, client, storage)
    except DiscordAPIError as exc:
        _print_discord_error(exc, action="sync")
        return 1
    print(
        f"[sync] channel={cfg.channel_id} "
        f"new_messages={stats['new_messages']} "
        f"attachments={stats['new_attachments']} "
        f"failed_attachments={stats['failed_attachments']} "
        f"last_read={stats['last_read']}"
    )
    return 0


def cmd_post(args) -> int:
    # Priority: --message-file > --message. At least one must resolve to non-empty, OR --attach present.
    message: str = ""
    if args.message_file:
        mf = Path(args.message_file)
        if not mf.exists():
            print(f"error: --message-file not found: {mf}", file=sys.stderr)
            return 2
        message = mf.read_text(encoding="utf-8")
    elif args.message is not None:
        message = args.message

    attach_strs: list[str] = args.attach or []

    # Handle --vc-snapshot
    cfg_for_snapshot: Config | None = None
    if args.vc_snapshot:
        cfg_for_snapshot = _load_config(args)
        vc_url: str | None = getattr(args, "vc_url", None)
        if not vc_url:
            sessions_dir = _resolve_vc_sessions_dir(
                cfg_for_snapshot, getattr(args, "vc_sessions_dir", None)
            )
            if sessions_dir is not None:
                vc_url = find_latest_server_url(sessions_dir)
        if not vc_url:
            print(
                "error: No URL available for --vc-snapshot. "
                "Pass --vc-url, or set --vc-sessions-dir / VC_SESSIONS_DIR "
                "to a directory containing '<session>/state/server-info' files.",
                file=sys.stderr,
            )
            return 2
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap_dest = cfg_for_snapshot.data_dir / "vc-snapshots" / f"{ts}.png"
        print(f"[post] capturing page snapshot from {vc_url} → {snap_dest}")
        snap_path = take_snapshot(vc_url, snap_dest)
        # Prepend snapshot so it appears first in Discord
        attach_strs = [str(snap_path)] + list(attach_strs)
        snap_note = "(첨부: 현재 페이지 스냅샷)"
        if message:
            message = message.rstrip("\n") + "\n\n" + snap_note
        else:
            message = snap_note

    if not message and not attach_strs:
        print("error: at least one of --message / --message-file / --attach must be provided", file=sys.stderr)
        return 2

    attach_paths = [Path(p) for p in attach_strs]
    missing = [str(p) for p in attach_paths if not p.exists()]
    if missing:
        print(f"error: attachment file(s) not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    cfg = cfg_for_snapshot or _load_config(args)
    client = DiscordClient(bot_token=cfg.bot_token)
    try:
        msg = run_post(cfg, client, message, attach_paths)
    except DiscordAPIError as exc:
        _print_discord_error(exc, action="post")
        return 1
    print(f"[post] message_id={msg['id']}")
    return 0


def cmd_status(args) -> int:
    cfg = _load_config(args)
    storage = Storage(cfg.data_dir, cfg.summary_dir)
    status = storage.get_read_status(cfg.channel_id)
    print(json.dumps({cfg.channel_id: status}, ensure_ascii=False, indent=2))
    return 0


def cmd_summarize_check(args) -> int:
    """Deterministic readiness gate for /discord-huddle-summarize.

    Inspects messages not yet covered by last_summarized and prints a JSON
    decision. Rationale: let the summarize agent skip without loading raw
    into its context when nothing is worth summarizing.

    Stdout: single JSON object with fields ready, reason, stats.
    Exit code is always 0 unless configuration itself failed — the agent
    reads the JSON to decide what to do next.
    """
    from discord_lib.gate import decide  # local import keeps base CLI light

    cfg = _load_config(args)
    storage = Storage(cfg.data_dir, cfg.summary_dir)
    read_status = storage.get_read_status(cfg.channel_id)
    last_summarized = read_status.get("last_summarized")

    messages = storage.read_raw_after(last_summarized)
    decision = decide(messages)

    payload = {
        "ready": decision.ready,
        "reason": decision.reason,
        "channel_id": cfg.channel_id,
        "after_msg_id": last_summarized,
        "stats": {
            "message_count": decision.stats.message_count,
            "total_content_chars": decision.stats.total_content_chars,
            "unique_participants": decision.stats.unique_participants,
            "attachment_count": decision.stats.attachment_count,
            "time_span_seconds": decision.stats.time_span_seconds,
            "first_msg_id": decision.stats.first_msg_id,
            "last_msg_id": decision.stats.last_msg_id,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _add_project_root_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--project-root",
        default=None,
        metavar="PATH",
        help="Override project root (else uses SYSTEM_AGENTS_PROJECT_ROOT or cwd walk)",
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="discord_collab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sync_parser = sub.add_parser("sync", help="Fetch new Discord messages into raw archive")
    _add_project_root_flag(sync_parser)

    status_parser = sub.add_parser("status", help="Show current read/summary status")
    _add_project_root_flag(status_parser)

    check_parser = sub.add_parser(
        "summarize-check",
        help="Deterministic readiness gate for /discord-huddle-summarize (no LLM).",
    )
    _add_project_root_flag(check_parser)

    post_parser = sub.add_parser("post", help="Post a message to Discord channel")
    post_parser.add_argument("--message", default=None, help="Text body of the message (short)")
    post_parser.add_argument("--message-file", default=None, help="Path to a file whose contents are used as the message body (recommended for multi-line)")
    post_parser.add_argument("--attach", nargs="*", metavar="FILE", help="File paths to attach")
    post_parser.add_argument("--vc-snapshot", action="store_true", help="Render a web page as PNG with headless Chromium and attach it")
    post_parser.add_argument("--vc-url", default=None, metavar="URL", help="URL to snapshot. If omitted, falls back to --vc-sessions-dir / VC_SESSIONS_DIR auto-detection")
    post_parser.add_argument("--vc-sessions-dir", default=None, metavar="DIR", help="Directory of '<session>/state/server-info' files to auto-detect the newest live URL. Also settable via VC_SESSIONS_DIR env var. No default.")
    _add_project_root_flag(post_parser)

    args = parser.parse_args(argv)

    handlers = {
        "sync": cmd_sync,
        "status": cmd_status,
        "post": cmd_post,
        "summarize-check": cmd_summarize_check,
    }
    try:
        return handlers[args.cmd](args)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        print("see docs/SETUP.md for setup steps.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
