"""Config loading — secrets file + resolved paths.

Default secrets path is ``{project_root}/.claude/secrets/discord-huddle.env``;
override by passing ``secrets_path`` or setting ``DISCORD_HUDDLE_ENV``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from .paths import (
    resolve_data_dir,
    resolve_project_root,
    resolve_summary_dir,
)


class ConfigError(Exception):
    """Configuration related error."""


REQUIRED_KEYS = ("DISCORD_BOT_TOKEN", "DISCORD_CHANNEL_ID")

DEFAULT_SECRETS_SUBPATH = Path(".claude") / "secrets" / "discord-huddle.env"
_ENV_SECRETS = "DISCORD_HUDDLE_ENV"


def _resolve_secrets_path(project_root: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    env_val = os.environ.get(_ENV_SECRETS)
    if env_val:
        p = Path(env_val).expanduser()
        if not p.is_absolute():
            p = project_root / p
        return p.resolve()
    return (project_root / DEFAULT_SECRETS_SUBPATH).resolve()


def _filter_non_empty(values: dict) -> dict[str, str]:
    """dotenv_values can yield None / empty strings for commented lines."""
    return {k: v for k, v in values.items() if v}


@dataclass(frozen=True)
class Config:
    bot_token: str
    channel_id: str
    project_root: Path
    data_dir: Path
    summary_dir: Path

    @classmethod
    def load(
        cls,
        *,
        project_root: Path | str | None = None,
        secrets_path: Path | str | None = None,
    ) -> "Config":
        """Resolve paths and load required secrets.

        Precedence for path-related env vars (``SYSTEM_AGENTS_PROJECT_ROOT``,
        ``DISCORD_HUDDLE_DATA_DIR``, ``DISCORD_HUDDLE_SUMMARY_DIR``):
          1. Explicit argument (e.g. ``project_root`` kwarg).
          2. Values set inside the secrets .env file.
          3. Process environment variables.
          4. Built-in defaults.

        Values live in the secrets file because that's where the plugin
        already reads its Discord token/channel — users shouldn't have to
        ``export`` separately.
        """
        # Pre-resolve root from process env so we can find the .env file at all.
        root = resolve_project_root(project_root)
        spath = _resolve_secrets_path(root, Path(secrets_path) if secrets_path else None)
        if not spath.exists():
            raise ConfigError(f"secrets file not found: {spath}")
        values = _filter_non_empty(dict(dotenv_values(spath)))
        missing = [k for k in REQUIRED_KEYS if not values.get(k)]
        if missing:
            raise ConfigError(
                f"missing required keys in {spath}: {', '.join(missing)}"
            )
        # Re-resolve root now that we have .env overrides too — in case the user
        # set SYSTEM_AGENTS_PROJECT_ROOT inside the .env itself. Explicit arg
        # still wins; overrides beat process env.
        root = resolve_project_root(project_root, overrides=values)
        return cls(
            bot_token=values["DISCORD_BOT_TOKEN"],
            channel_id=values["DISCORD_CHANNEL_ID"],
            project_root=root,
            data_dir=resolve_data_dir(root, overrides=values),
            summary_dir=resolve_summary_dir(root, overrides=values),
        )
