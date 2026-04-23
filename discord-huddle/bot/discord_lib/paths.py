"""Path resolution for discord-huddle plugin.

Resolves three roots that the rest of the plugin uses:

1. ``project_root`` — the project the plugin is installed into.
   Detected from (highest priority first):
     - Explicit ``project_root`` argument (e.g. ``--project-root`` flag)
     - ``SYSTEM_AGENTS_PROJECT_ROOT`` from ``overrides`` (e.g. .env contents)
     - ``SYSTEM_AGENTS_PROJECT_ROOT`` from process env
     - CWD walk: first ancestor of ``Path.cwd()`` that contains ``.claude/``
     If none of the above apply the caller gets ``ProjectRootError``.

2. ``data_dir`` — runtime artifacts (gitignored).
   Defaults to ``{project_root}/.system-agents/discord-huddle/``.
   Override with ``DISCORD_HUDDLE_DATA_DIR`` (in ``overrides`` or process env).

3. ``summary_dir`` — team-tracked meeting summaries.
   Defaults to ``{project_root}/docs/discord-huddle-summaries/``.
   Override with ``DISCORD_HUDDLE_SUMMARY_DIR`` (in ``overrides`` or process env).

``overrides`` lets callers pass values loaded from a .env file without
polluting the process-wide environment. When both an override dict and a
matching env var exist, the dict wins (so .env stays authoritative for
plugin installs). Relative values are resolved against ``project_root``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


class ProjectRootError(RuntimeError):
    """Raised when the project root cannot be determined."""


DEFAULT_DATA_SUBDIR = Path(".system-agents") / "discord-huddle"
DEFAULT_SUMMARY_SUBDIR = Path("docs") / "discord-huddle-summaries"

_ENV_PROJECT_ROOT = "SYSTEM_AGENTS_PROJECT_ROOT"
_ENV_DATA_DIR = "DISCORD_HUDDLE_DATA_DIR"
_ENV_SUMMARY_DIR = "DISCORD_HUDDLE_SUMMARY_DIR"


def _lookup(key: str, overrides: Mapping[str, str] | None) -> str | None:
    """Return the value for ``key`` from overrides first, then process env."""
    if overrides is not None:
        v = overrides.get(key)
        if v:
            return v
    return os.environ.get(key) or None


def resolve_project_root(
    explicit: Path | str | None = None,
    overrides: Mapping[str, str] | None = None,
) -> Path:
    """Determine the project root using the documented precedence."""
    if explicit is not None:
        p = Path(explicit).expanduser().resolve()
        if not p.is_dir():
            raise ProjectRootError(f"explicit project_root is not a directory: {p}")
        return p

    env_val = _lookup(_ENV_PROJECT_ROOT, overrides)
    if env_val:
        p = Path(env_val).expanduser().resolve()
        if not p.is_dir():
            raise ProjectRootError(
                f"{_ENV_PROJECT_ROOT}={env_val!r} is not a directory"
            )
        return p

    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / ".claude").is_dir():
            return candidate.resolve()

    raise ProjectRootError(
        "project root undetermined; set SYSTEM_AGENTS_PROJECT_ROOT, pass "
        "--project-root, or run from a directory whose ancestor contains .claude/"
    )


def _resolve_subdir(
    project_root: Path,
    env_name: str,
    default_subdir: Path,
    overrides: Mapping[str, str] | None,
) -> Path:
    env_val = _lookup(env_name, overrides)
    if env_val:
        candidate = Path(env_val).expanduser()
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate.resolve()
    return (project_root / default_subdir).resolve()


def resolve_data_dir(
    project_root: Path,
    overrides: Mapping[str, str] | None = None,
) -> Path:
    return _resolve_subdir(project_root, _ENV_DATA_DIR, DEFAULT_DATA_SUBDIR, overrides)


def resolve_summary_dir(
    project_root: Path,
    overrides: Mapping[str, str] | None = None,
) -> Path:
    return _resolve_subdir(project_root, _ENV_SUMMARY_DIR, DEFAULT_SUMMARY_SUBDIR, overrides)


def ensure_data_dir(data_dir: Path) -> Path:
    """Create the runtime data dir and drop a '*' .gitignore inside it."""
    data_dir.mkdir(parents=True, exist_ok=True)
    gi = data_dir / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")
    return data_dir
