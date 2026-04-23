"""Sync 파이프라인 — api로 수집 → storage에 영속화."""

from __future__ import annotations

import logging
from typing import Any

from .storage import Storage


log = logging.getLogger(__name__)


def run_sync(config, client, storage: Storage) -> dict[str, Any]:
    """config.channel_id의 새 메시지를 전부 당겨와 raw에 저장.

    반환: {new_messages, new_attachments, failed_attachments, last_read}
    """
    status = storage.get_read_status(config.channel_id)
    last_id = status.get("last_read") or None

    messages = client.fetch_all_new(channel_id=config.channel_id, last_id=last_id)
    stats = {
        "new_messages": 0,
        "new_attachments": 0,
        "failed_attachments": 0,
        "last_read": last_id,
    }

    for msg in messages:
        enriched_attachments = []
        for att in msg.get("attachments", []) or []:
            url = att.get("url")
            filename = att.get("filename") or f"{att.get('id', 'file')}.bin"
            try:
                local = storage.download_attachment(
                    url=url, msg_id=msg["id"], filename=filename
                )
                rel = local.relative_to(storage.raw_dir)
                att["local_path"] = str(rel).replace("\\", "/")
                stats["new_attachments"] += 1
            except Exception as exc:  # download-only failure, keep message
                log.warning("attachment download failed for msg=%s: %s", msg["id"], exc)
                stats["failed_attachments"] += 1
            enriched_attachments.append(att)
        msg["attachments"] = enriched_attachments

        if storage.append_raw(msg):
            stats["new_messages"] += 1
        stats["last_read"] = msg["id"]

    if stats["last_read"]:
        storage.update_last_read(config.channel_id, stats["last_read"])

    return stats
