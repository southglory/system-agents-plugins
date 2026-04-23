"""Tests for the summarize readiness gate."""
from __future__ import annotations

import pytest

from discord_lib.gate import decide, compute_stats, evaluate, Stats


def _msg(mid: str, author: str, content: str = "", ts: str = "2026-04-23T00:00:00+00:00",
         attachments: list | None = None) -> dict:
    return {
        "id": mid,
        "author": {"id": author, "username": author},
        "content": content,
        "timestamp": ts,
        "attachments": attachments or [],
    }


def test_no_messages_not_ready():
    d = decide([])
    assert d.ready is False
    assert d.reason == "no_new_messages"
    assert d.stats.message_count == 0


def test_too_few_messages():
    """A single short message shouldn't trigger a summary."""
    d = decide([_msg("1", "a", "hi")])
    assert d.ready is False
    assert d.reason == "too_few_messages"


def test_short_monologue_seven_single_words_stays_unready():
    """The exact failure case from E2E: 7 one-word messages by one author."""
    msgs = [_msg(str(i), "solo", content="a") for i in range(1, 8)]
    d = decide(msgs)
    assert d.ready is False
    # Not dialog (one participant) and chars well below MIN_CHARS_MONOLOGUE (100)
    assert d.reason in ("short_monologue", "insufficient_content")
    assert d.stats.message_count == 7
    assert d.stats.unique_participants == 1
    assert d.stats.total_content_chars == 7


def test_monologue_with_enough_chars_passes():
    msg = _msg("1", "solo", content="x" * 200)
    # 5 messages, each 200 chars — total 1000 chars well over MIN_CHARS_MONOLOGUE
    msgs = [_msg(str(i), "solo", content="x" * 200) for i in range(1, 6)]
    d = decide(msgs)
    assert d.ready is True
    assert d.reason == "passed:messages+chars"


def test_dialog_three_messages_passes():
    """Real back-and-forth with 2+ participants passes on just 3 short messages."""
    msgs = [
        _msg("1", "alice", "should we do A?"),
        _msg("2", "bob", "yes let's go with A"),
        _msg("3", "alice", "agreed"),
    ]
    d = decide(msgs)
    assert d.ready is True
    assert d.reason == "passed:dialog"
    assert d.stats.unique_participants == 2


def test_attachment_heavy_passes():
    """Two+ attachments across messages is reason enough (image review etc.)."""
    msgs = [
        _msg("1", "solo", attachments=[{"filename": "a.png"}]),
        _msg("2", "solo", attachments=[{"filename": "b.png"}, {"filename": "c.png"}]),
    ]
    d = decide(msgs)
    assert d.ready is True
    assert d.reason == "passed:attachments"


def test_dialog_wins_over_short_content():
    """2 participants + 3 messages must pass even if content is tiny."""
    msgs = [
        _msg("1", "a", "y"),
        _msg("2", "b", "n"),
        _msg("3", "a", "ok"),
    ]
    d = decide(msgs)
    assert d.ready is True
    assert d.stats.total_content_chars < 10


def test_stats_time_span():
    """Time span in seconds is computed from first and last ISO timestamp."""
    msgs = [
        _msg("1", "a", "first", ts="2026-04-23T00:00:00+00:00"),
        _msg("2", "a", "last",  ts="2026-04-23T00:10:00+00:00"),
    ]
    s = compute_stats(msgs)
    assert s.time_span_seconds == pytest.approx(600.0)
    assert s.first_msg_id == "1"
    assert s.last_msg_id == "2"


def test_evaluate_is_deterministic_on_same_stats():
    """Given identical stats, the decision is always the same."""
    stats = Stats(
        message_count=10, total_content_chars=500, unique_participants=3,
        attachment_count=0, time_span_seconds=300.0,
        first_msg_id="a", last_msg_id="b",
    )
    d1 = evaluate(stats)
    d2 = evaluate(stats)
    assert d1 == d2
    assert d1.ready is True
