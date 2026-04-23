"""Path resolution for the unity-gamedev plugin.

Determines the Unity project root, where Builds/ and dist/ live. The plugin
itself has no state; this module just centralizes precedence rules so all
subcommands agree on where to operate.

``project_root`` precedence (highest to lowest):

1. Explicit ``--project-root PATH`` on the CLI.
2. ``SYSTEM_AGENTS_PROJECT_ROOT`` environment variable.
3. CWD walk: first ancestor of ``Path.cwd()`` that contains **both** an
   ``Assets/`` directory **and** a ``ProjectSettings/`` directory (the
   standard Unity project fingerprint).
4. Raises ``ProjectRootError`` otherwise — the installer's docs point the
   user at the three escape hatches above.

This is deliberately narrower than the discord-huddle plugin's
``resolve_project_root``: a Unity build only makes sense inside a Unity
project, so we require the fingerprint rather than settling for any
``.claude/`` ancestor.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


class ProjectRootError(RuntimeError):
    """Raised when the Unity project root cannot be determined."""


_ENV_PROJECT_ROOT = "SYSTEM_AGENTS_PROJECT_ROOT"


def _is_unity_project(d: Path) -> bool:
    return (d / "Assets").is_dir() and (d / "ProjectSettings").is_dir()


def _lookup_env(key: str, overrides: Mapping[str, str] | None) -> str | None:
    if overrides is not None:
        v = overrides.get(key)
        if v:
            return v
    return os.environ.get(key) or None


def resolve_project_root(
    explicit: Path | str | None = None,
    overrides: Mapping[str, str] | None = None,
) -> Path:
    """Determine the Unity project root using the documented precedence."""
    if explicit is not None:
        p = Path(explicit).expanduser().resolve()
        if not p.is_dir():
            raise ProjectRootError(f"explicit project_root is not a directory: {p}")
        return p

    env_val = _lookup_env(_ENV_PROJECT_ROOT, overrides)
    if env_val:
        p = Path(env_val).expanduser().resolve()
        if not p.is_dir():
            raise ProjectRootError(
                f"{_ENV_PROJECT_ROOT}={env_val!r} is not a directory"
            )
        return p

    for candidate in (Path.cwd(), *Path.cwd().parents):
        if _is_unity_project(candidate):
            return candidate.resolve()

    raise ProjectRootError(
        "Unity project root undetermined. Set SYSTEM_AGENTS_PROJECT_ROOT, "
        "pass --project-root PATH, or run this command from inside a "
        "directory tree that contains Assets/ + ProjectSettings/."
    )
