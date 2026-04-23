"""Deterministic readiness check for the summarize skill.

The slash command ``/discord-huddle-summarize`` is performed by a Claude
Code agent reading raw JSONL directly. Agent tokens are expensive, so we
want a cheap, code-only gate that decides whether a summary is even
worth generating. The agent calls this first; on "not ready" it stops
immediately without pulling the raw into context.

Heuristics (any one passing → ready):

- ``msg_count >= MIN_MESSAGES and total_chars >= MIN_CHARS_MONOLOGUE``
  (a solo but substantive stretch of messages).

- ``unique_participants >= 2 and msg_count >= MIN_MESSAGES_DIALOG``
  (real back-and-forth compensates for fewer characters — short
  decisions like "A로 결정" still carry weight when two+ people are on
  the line).

- ``attachment_count >= MIN_ATTACHMENTS``
  (image-heavy discussions are worth summarizing even if text is thin).

Thresholds are conservative defaults tuned for small teams; override via
the ``summarize-check`` CLI if needed. The gate never generates
anything — it only returns a structured decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


MIN_MESSAGES = 5
MIN_CHARS_MONOLOGUE = 100
MIN_MESSAGES_DIALOG = 3
MIN_ATTACHMENTS = 2


@dataclass(frozen=True)
class Stats:
    message_count: int
    total_content_chars: int
    unique_participants: int
    attachment_count: int
    time_span_seconds: float
    first_msg_id: str | None
    last_msg_id: str | None


@dataclass(frozen=True)
class Decision:
    ready: bool
    reason: str      # e.g. "passed:messages+chars", "insufficient_content"
    stats: Stats


def compute_stats(messages: Iterable[dict]) -> Stats:
    """Walk messages once and extract the fields the gate needs."""
    authors: set[str] = set()
    total_chars = 0
    attachment_count = 0
    count = 0
    first_ts: str | None = None
    last_ts: str | None = None
    first_id: str | None = None
    last_id: str | None = None

    for m in messages:
        count += 1
        content = m.get("content") or ""
        total_chars += len(content)

        author = m.get("author") or {}
        aid = author.get("id") or author.get("username")
        if aid:
            authors.add(aid)

        atts = m.get("attachments") or []
        attachment_count += len(atts)

        ts = m.get("timestamp") or ""
        if ts:
            if first_ts is None:
                first_ts = ts
                first_id = m.get("id")
            last_ts = ts
            last_id = m.get("id")

    span_seconds = 0.0
    if first_ts and last_ts and first_ts != last_ts:
        try:
            t0 = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            span_seconds = max(0.0, (t1 - t0).total_seconds())
        except ValueError:
            span_seconds = 0.0

    return Stats(
        message_count=count,
        total_content_chars=total_chars,
        unique_participants=len(authors),
        attachment_count=attachment_count,
        time_span_seconds=span_seconds,
        first_msg_id=first_id,
        last_msg_id=last_id,
    )


def evaluate(stats: Stats) -> Decision:
    """Apply the readiness heuristics to a Stats snapshot."""
    if stats.message_count == 0:
        return Decision(ready=False, reason="no_new_messages", stats=stats)

    # Heuristic 1 — monologue but substantive
    if (
        stats.message_count >= MIN_MESSAGES
        and stats.total_content_chars >= MIN_CHARS_MONOLOGUE
    ):
        return Decision(ready=True, reason="passed:messages+chars", stats=stats)

    # Heuristic 2 — real dialog
    if (
        stats.unique_participants >= 2
        and stats.message_count >= MIN_MESSAGES_DIALOG
    ):
        return Decision(ready=True, reason="passed:dialog", stats=stats)

    # Heuristic 3 — image-heavy
    if stats.attachment_count >= MIN_ATTACHMENTS:
        return Decision(ready=True, reason="passed:attachments", stats=stats)

    # Failure: pick the most specific reason so the agent can tell the user why.
    if stats.message_count < MIN_MESSAGES_DIALOG:
        return Decision(ready=False, reason="too_few_messages", stats=stats)
    if stats.unique_participants < 2 and stats.total_content_chars < MIN_CHARS_MONOLOGUE:
        return Decision(ready=False, reason="short_monologue", stats=stats)
    return Decision(ready=False, reason="insufficient_content", stats=stats)


def decide(messages: Iterable[dict]) -> Decision:
    """Shortcut: compute_stats + evaluate."""
    return evaluate(compute_stats(messages))
