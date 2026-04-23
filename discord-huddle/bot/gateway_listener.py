"""Discord Gateway WebSocket listener.

Subscribes to Discord Gateway and writes a small JSON file to the inbox
directory every time a new message arrives in the configured channel.

Claude Code (or any other watcher) can then Monitor the inbox directory
and react in near-real-time, instead of polling REST every 15 minutes.

Usage:
  python bot/gateway_listener.py [--project-root PATH]

Runs forever. Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord

from discord_lib.config import Config, ConfigError
from discord_lib.paths import ensure_data_dir


def _inbox_dir(data_dir: Path) -> Path:
    ensure_data_dir(data_dir)
    p = data_dir / "inbox"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _write_signal(inbox: Path, message: discord.Message) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    fname = f"{ts}_{message.id}.json"
    payload = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author_id": str(message.author.id),
        "author_name": message.author.global_name or message.author.name,
        "is_bot": message.author.bot,
        "content": message.content,
        "timestamp": message.created_at.isoformat(),
        "attachment_count": len(message.attachments),
    }
    path = inbox / fname
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class Listener(discord.Client):
    def __init__(self, cfg: Config):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.cfg = cfg
        self.target_channel_id = int(cfg.channel_id)
        self.inbox = _inbox_dir(cfg.data_dir)

    async def on_ready(self):
        me = self.user
        logging.info(f"gateway connected as {me} (id={me.id}) watching channel {self.target_channel_id}")

    async def on_message(self, message: discord.Message):
        if message.channel.id != self.target_channel_id:
            return
        try:
            path = _write_signal(self.inbox, message)
            logging.info(f"signal written: {path.name} from {message.author.global_name or message.author.name}")
        except Exception as exc:
            logging.error(f"failed to write inbox signal: {exc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gateway_listener")
    parser.add_argument(
        "--project-root",
        default=None,
        metavar="PATH",
        help="Override project root (else uses SYSTEM_AGENTS_PROJECT_ROOT or cwd walk)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        cfg = Config.load(project_root=args.project_root)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        print("see docs/SETUP.md for setup steps.", file=sys.stderr)
        return 3

    client = Listener(cfg)

    def _graceful_stop(signum, frame):
        logging.info("shutdown signal received, closing gateway")
        import asyncio

        loop = asyncio.get_event_loop()
        loop.create_task(client.close())

    signal.signal(signal.SIGINT, _graceful_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _graceful_stop)

    client.run(cfg.bot_token, log_handler=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
