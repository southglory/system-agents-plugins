"""Zip artifact + GitHub Release via gh CLI.

This module has no hardcoded project names. Callers supply ``output_name``
(e.g. "MyGame") and the functions stamp it into file paths / asset names.

Requires:
  - ``gh`` on PATH, authenticated with ``repo`` scope for the target repo.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class ReleaseError(RuntimeError):
    """Raised when zipping or the gh release step fails."""


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def make_zip(builds_dir: Path, dist_dir: Path, output_name: str, tag: str) -> Path:
    """Compress ``builds_dir`` into ``dist_dir/{output_name}_{tag}.zip``.

    Returns the path to the resulting zip.
    """
    if not builds_dir.exists():
        raise ReleaseError(f"builds directory missing: {builds_dir}")
    dist_dir.mkdir(parents=True, exist_ok=True)
    stem = dist_dir / f"{output_name}_{tag}"
    _log(f"[publish] zipping {builds_dir} → {stem.with_suffix('.zip')}")
    archive = shutil.make_archive(str(stem), "zip", root_dir=str(builds_dir))
    archive_path = Path(archive)
    size_mb = archive_path.stat().st_size / 1024 / 1024
    _log(f"[publish] zip created: {archive_path.name} ({size_mb:.1f} MB)")
    return archive_path


def create_release(
    project_root: Path,
    tag: str,
    zip_path: Path,
    notes: str,
    title: str,
    release_repo: str | None = None,
) -> str:
    """Create (or update) a GitHub Release and upload the zip.

    Returns the public URL of the release.

    If ``release_repo`` is given (e.g. ``"owner/repo"``), gh targets that
    repo with ``--repo``. Otherwise gh uses the cwd's git remote. This lets
    callers build from one project but publish to a different repo — useful
    for test flows and for teams where the build artifacts live in one
    repo and Releases live in another.

    If the tag already exists on the target repo, this function re-uploads
    the zip with --clobber instead of failing. Callers can retry a failed
    upload without having to bump the tag.
    """
    notes_file = project_root / "dist" / f".notes_{tag}.md"
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    notes_file.write_text(notes or f"Auto-generated build {tag}", encoding="utf-8")

    repo_flag = ["--repo", release_repo] if release_repo else []

    _log(f"[publish] creating GitHub release {tag}" + (f" on {release_repo}" if release_repo else ""))
    cmd = [
        "gh", "release", "create", tag,
        str(zip_path),
        "--title", title or tag,
        "--notes-file", str(notes_file),
        *repo_flag,
    ]
    result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        if "already exists" in result.stderr:
            _log(f"[publish] tag {tag} exists, uploading asset with --clobber")
            up = subprocess.run(
                ["gh", "release", "upload", tag, str(zip_path), "--clobber", *repo_flag],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if up.returncode != 0:
                raise ReleaseError(f"gh release upload failed: {up.stderr.strip()}")
        else:
            raise ReleaseError(f"gh release create failed: {result.stderr.strip()}")

    view = subprocess.run(
        ["gh", "release", "view", tag, "--json", "url", *repo_flag],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if view.returncode != 0:
        raise ReleaseError(f"gh release view failed: {view.stderr.strip()}")
    url = json.loads(view.stdout).get("url", "")
    _log(f"[publish] release URL: {url}")
    return url
