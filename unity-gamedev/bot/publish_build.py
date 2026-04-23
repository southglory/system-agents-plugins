"""Build a playtest binary via unity-cli, zip it, and publish as a GitHub Release.

Nothing about this script is project-specific. Scene paths, output name,
target platform, and project root all come from CLI flags or env vars.

Usage:
    python bot/publish_build.py \\
        --tag v0.1.0-alpha \\
        --scene Assets/Scenes/Main.unity \\
        --output-name MyGame \\
        --notes "MVP α"

    python bot/publish_build.py --tag v0.1.1 --skip-build

stdout emits one JSON object on success:
    {"tag":"v0.1.0","title":"MVP α","url":"https://...","zip":"dist/MyGame_v0.1.0.zip"}

stderr carries human-readable progress. This separation lets callers pipe
stdout into /discord-huddle-post --message or any other announcer without
parsing log spam.

Exit codes:
    0  success
    1  build / zip / release step failed
    2  invalid input (missing notes file, no scene, no build artifact, etc.)
    3  project root could not be determined
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from unity_lib.build import (
    DEFAULT_TARGET,
    UnityBuildError,
    build_location,
    run_unity_build,
)
from unity_lib.paths import ProjectRootError, resolve_project_root
from unity_lib.release import ReleaseError, create_release, make_zip


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="publish_build")
    p.add_argument("--tag", required=True, help="Release tag, e.g. v0.1.0-alpha")
    p.add_argument("--title", default="", help="Release title; defaults to tag")
    p.add_argument("--notes", default="", help="Release notes markdown (inline)")
    p.add_argument("--notes-file", default=None,
                   help="Path to a file containing release notes (preferred for multi-line)")
    p.add_argument("--skip-build", action="store_true",
                   help="Skip the Unity build step; reuse what is already in Builds/")
    p.add_argument("--scene", action="append", default=[], metavar="PATH",
                   help="Scene path relative to project root, e.g. Assets/Scenes/Main.unity. "
                        "Repeat to include multiple scenes. Required unless --skip-build.")
    p.add_argument("--output-name", default="Build", metavar="NAME",
                   help="Base name for the built binary and zip (default: Build). "
                        "e.g. 'MyGame' → Builds/MyGame.exe → dist/MyGame_v0.1.0.zip")
    p.add_argument("--target", default=DEFAULT_TARGET,
                   help=f"Unity BuildTarget enum value (default: {DEFAULT_TARGET})")
    p.add_argument("--project-root", default=None, metavar="PATH",
                   help="Override Unity project root (else SYSTEM_AGENTS_PROJECT_ROOT "
                        "or cwd walk for Assets/+ProjectSettings/)")
    p.add_argument("--release-repo", default=None, metavar="OWNER/REPO",
                   help="Publish the Release to a specific GitHub repo. "
                        "If omitted, gh uses the project's git remote.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # Resolve project root
    try:
        project_root = resolve_project_root(args.project_root)
    except ProjectRootError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3

    builds_dir = project_root / "Builds"
    dist_dir = project_root / "dist"
    built_binary = build_location(project_root, args.output_name, args.target)

    # Resolve notes
    notes = args.notes
    if args.notes_file:
        nf = Path(args.notes_file)
        if not nf.exists():
            print(f"error: --notes-file not found: {nf}", file=sys.stderr)
            return 2
        notes = nf.read_text(encoding="utf-8")

    # Unity build (unless skipped)
    if not args.skip_build:
        if not args.scene:
            print("error: at least one --scene is required unless --skip-build is used",
                  file=sys.stderr)
            return 2
        try:
            run_unity_build(
                project_root=project_root,
                scenes=args.scene,
                output_name=args.output_name,
                target=args.target,
            )
        except UnityBuildError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    # Verify the binary exists (whether we just built it or --skip-build'd)
    if not built_binary.exists():
        print(
            f"error: expected build artifact not found: {built_binary}\n"
            f"Run without --skip-build to produce it, or pass --output-name "
            f"matching an existing artifact under Builds/.",
            file=sys.stderr,
        )
        return 2

    # Zip + Release
    try:
        zip_path = make_zip(builds_dir, dist_dir, args.output_name, args.tag)
        url = create_release(
            project_root, args.tag, zip_path, notes, args.title,
            release_repo=args.release_repo,
        )
    except ReleaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        zip_display = zip_path.relative_to(project_root).as_posix()
    except ValueError:
        zip_display = zip_path.as_posix()

    result = {
        "tag": args.tag,
        "title": args.title or args.tag,
        "url": url,
        "zip": zip_display,
        "output_name": args.output_name,
        "target": args.target,
    }
    print(json.dumps(result, ensure_ascii=False))
    _log(f"[publish] done. tag={args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
