"""File IO: raw JSONL, attachments, split state files, summary md.

Paths are resolved by ``paths.py`` and passed in. This module itself does not
know about project roots or env vars — callers decide where runtime data and
team-shared summaries live.

State is split into two files (rationale: gitignore operates per-file):

- ``{data_dir}/local-state.json`` — gitignored.
  Keys per channel: ``last_read`` (raw sync pointer), ``updated_at``.

- ``{summary_dir}/index.json`` — tracked by git.
  Keys per channel: ``last_summarized``, ``last_file``, ``updated_at``.

Both pointers are forward-only: setter refuses to regress to an older snowflake.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests

from .paths import ensure_data_dir


LOCAL_STATE_FILENAME = "local-state.json"
SUMMARY_INDEX_FILENAME = "index.json"


def _snowflake_ge(new: str, existing: str | None) -> bool:
    """Return True if ``new`` is newer or equal to ``existing`` (forward-only guard).

    Discord snowflakes are numeric strings; int compare is correct.
    """
    if existing is None or existing == "":
        return True
    try:
        return int(new) >= int(existing)
    except (TypeError, ValueError):
        # Fall back to lexicographic if either is non-numeric (shouldn't happen).
        return new >= existing


class Storage:
    """File operations for raw/attachments/state/summary.

    Directories passed in are created on demand. ``data_dir`` additionally
    gets a '*' .gitignore dropped inside so the whole runtime dir is excluded
    without touching the project's root .gitignore.
    """

    def __init__(self, data_dir: Path, summary_dir: Path):
        self.data_dir = ensure_data_dir(Path(data_dir))
        self.summary_dir = Path(summary_dir)

        self.raw_dir = self.data_dir / "raw"
        self.raw_attach_dir = self.raw_dir / "attachments"
        self.inbox_dir = self.data_dir / "inbox"
        self.vc_snapshot_dir = self.data_dir / "vc-snapshots"
        self.local_state_file = self.data_dir / LOCAL_STATE_FILENAME

        self.summary_attach_dir = self.summary_dir / "attachments"
        self.summary_index_file = self.summary_dir / SUMMARY_INDEX_FILENAME

        for d in (
            self.raw_dir,
            self.raw_attach_dir,
            self.inbox_dir,
            self.summary_dir,
            self.summary_attach_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    # ---------- Raw JSONL ----------

    def _date_file(self, iso_timestamp: str) -> Path:
        # Discord timestamp: 2026-04-21T14:30:52.000000+00:00
        date_str = iso_timestamp.split("T", 1)[0]
        return self.raw_dir / f"{date_str}.jsonl"

    def _existing_ids(self, file: Path) -> set[str]:
        if not file.exists():
            return set()
        ids = set()
        for line in file.read_text(encoding="utf-8").splitlines():
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                continue
        return ids

    def append_raw(self, message: dict) -> bool:
        """Append raw message to dated JSONL; skip (return False) if msg_id already present."""
        ts = message.get("timestamp", "")
        if not ts:
            raise ValueError("message missing timestamp")
        file = self._date_file(ts)
        if message["id"] in self._existing_ids(file):
            return False
        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")
        return True

    def read_raw_after(self, exclusive_id: str | None) -> list[dict]:
        """Return all raw messages after ``exclusive_id``, sorted by timestamp.

        If ``exclusive_id`` is None or empty, return everything.
        """
        messages: list[dict] = []
        for file in sorted(self.raw_dir.glob("*.jsonl")):
            for line in file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        messages.sort(key=lambda m: m.get("timestamp", ""))
        if exclusive_id is None or exclusive_id == "":
            return messages
        out = []
        seen_marker = False
        for m in messages:
            if seen_marker:
                out.append(m)
            elif m.get("id") == exclusive_id:
                seen_marker = True
        if not seen_marker:
            # Marker absent → treat as first-time read.
            return messages
        return out

    # ---------- Attachments ----------

    def download_attachment(self, url: str, msg_id: str, filename: str, timeout: float = 30.0) -> Path:
        """Save attachment flat as ``raw/attachments/{msg_id}_{filename}`` (no nesting)."""
        self.raw_attach_dir.mkdir(parents=True, exist_ok=True)
        dest = self.raw_attach_dir / f"{msg_id}_{filename}"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return dest

    def copy_representative(self, raw_relative: str, summary_name: str) -> Path:
        """Copy ``raw/attachments/{msg_id}_{filename}`` → ``summary/attachments/{summary_name}/``."""
        src = self.raw_dir / raw_relative
        if not src.exists():
            raise FileNotFoundError(src)
        dest_dir = self.summary_attach_dir / summary_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        return dest

    # ---------- State (split: local + index) ----------

    def _load_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get_read_status(self, channel_id: str) -> dict:
        """Combined view across both state files (for backwards-compatible reads)."""
        local = self._load_json(self.local_state_file).get(channel_id, {})
        index = self._load_json(self.summary_index_file).get(channel_id, {})
        return {
            "last_read": local.get("last_read"),
            "last_summarized": index.get("last_summarized"),
            "last_file": index.get("last_file"),
            "updated_at": max(
                filter(None, (local.get("updated_at"), index.get("updated_at"))),
                default=None,
            ),
        }

    def update_last_read(self, channel_id: str, last_read: str) -> None:
        """Forward-only update of the local raw-sync pointer."""
        data = self._load_json(self.local_state_file)
        bucket = data.setdefault(channel_id, {})
        if not _snowflake_ge(last_read, bucket.get("last_read")):
            return
        bucket["last_read"] = last_read
        bucket["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_json(self.local_state_file, data)

    def update_last_summarized(
        self,
        channel_id: str,
        last_summarized: str,
        last_file: str | None = None,
    ) -> None:
        """Forward-only update of the tracked summary pointer."""
        data = self._load_json(self.summary_index_file)
        bucket = data.setdefault(channel_id, {})
        if not _snowflake_ge(last_summarized, bucket.get("last_summarized")):
            return
        bucket["last_summarized"] = last_summarized
        if last_file is not None:
            bucket["last_file"] = last_file
        bucket["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_json(self.summary_index_file, data)

    # ---------- Summary md ----------

    def write_summary(self, filename: str, body: str) -> Path:
        path = self.summary_dir / filename
        path.write_text(body, encoding="utf-8")
        return path
