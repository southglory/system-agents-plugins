import json
from pathlib import Path

import pytest

from discord_lib.storage import Storage


def _sample_message(msg_id: str, ts: str = "2026-04-21T14:30:52.000000+00:00"):
    return {
        "id": msg_id,
        "content": "hello",
        "timestamp": ts,
        "author": {"username": "tester", "id": "u1"},
        "attachments": [],
        "reactions": [],
    }


def test_append_raw_creates_date_file(tmp_data_dir, tmp_summary_dir):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    m = _sample_message("1")
    storage.append_raw(m)
    path = tmp_data_dir / "raw" / "2026-04-21.jsonl"
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["id"] == "1"


def test_append_raw_appends_and_dedups(tmp_data_dir, tmp_summary_dir):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    storage.append_raw(_sample_message("1"))
    storage.append_raw(_sample_message("1"))  # dup
    storage.append_raw(_sample_message("2"))
    path = tmp_data_dir / "raw" / "2026-04-21.jsonl"
    ids = [json.loads(l)["id"] for l in path.read_text(encoding="utf-8").strip().splitlines()]
    assert ids == ["1", "2"]


def test_state_split_roundtrip(tmp_data_dir, tmp_summary_dir):
    """local-state.json and summary/index.json live in separate files now."""
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    assert storage.get_read_status("ch1") == {
        "last_read": None, "last_summarized": None, "last_file": None, "updated_at": None
    }

    # Discord snowflakes; int-comparable strings.
    storage.update_last_read("ch1", "1000000000000010000")
    storage.update_last_summarized("ch1", "1000000000000005000", last_file="2026-04-21_1430.md")

    got = storage.get_read_status("ch1")
    assert got["last_read"] == "1000000000000010000"
    assert got["last_summarized"] == "1000000000000005000"
    assert got["last_file"] == "2026-04-21_1430.md"

    # Files live where they should
    assert (tmp_data_dir / "local-state.json").exists()
    assert (tmp_summary_dir / "index.json").exists()


def test_state_forward_only(tmp_data_dir, tmp_summary_dir):
    """Neither pointer can move backwards."""
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    storage.update_last_read("ch1", "2000")
    storage.update_last_read("ch1", "1000")  # ignored, older snowflake
    assert storage.get_read_status("ch1")["last_read"] == "2000"

    storage.update_last_summarized("ch1", "500")
    storage.update_last_summarized("ch1", "100")  # ignored
    assert storage.get_read_status("ch1")["last_summarized"] == "500"


def test_ensure_data_dir_drops_gitignore(tmp_data_dir, tmp_summary_dir):
    """Constructing Storage creates data_dir/.gitignore='*' (self-isolating)."""
    Storage(tmp_data_dir, tmp_summary_dir)
    gi = tmp_data_dir / ".gitignore"
    assert gi.exists()
    assert gi.read_text(encoding="utf-8").strip() == "*"


def test_read_raw_range(tmp_data_dir, tmp_summary_dir):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    storage.append_raw(_sample_message("1"))
    storage.append_raw(_sample_message("2"))
    storage.append_raw(_sample_message("3"))
    msgs = storage.read_raw_after("0")  # marker absent → all
    ids = [m["id"] for m in msgs]
    assert ids == ["1", "2", "3"]
    msgs = storage.read_raw_after("1")
    assert [m["id"] for m in msgs] == ["2", "3"]


def test_download_attachment_writes_file(tmp_data_dir, tmp_summary_dir, monkeypatch):
    fake_bytes = b"\x89PNG\r\nfakebody"

    def fake_get(url, timeout):
        class R:
            content = fake_bytes
            def raise_for_status(self): pass
        return R()

    import discord_lib.storage as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)

    storage = Storage(tmp_data_dir, tmp_summary_dir)
    local = storage.download_attachment(
        url="https://cdn.discordapp.com/x.png",
        msg_id="99",
        filename="x.png",
    )
    assert local.read_bytes() == fake_bytes
    assert "attachments/99_x.png" in str(local).replace("\\", "/")


def test_write_summary_md(tmp_data_dir, tmp_summary_dir):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    body = "---\nsource: discord\n---\n\n## 요약\n- a"
    path = storage.write_summary("2026-04-21_1530.md", body)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == body


def test_copy_representative_attachment(tmp_data_dir, tmp_summary_dir):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    src = tmp_data_dir / "raw" / "attachments" / "99_img.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"data")

    dest = storage.copy_representative(
        raw_relative="attachments/99_img.png",
        summary_name="2026-04-21_1530",
    )
    expected = tmp_summary_dir / "attachments" / "2026-04-21_1530" / "99_img.png"
    assert dest == expected
    assert dest.read_bytes() == b"data"
