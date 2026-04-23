"""End-to-end CLI tests for publish_build — wholesale monkeypatched (no unity-cli, no gh)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BOT_DIR = HERE.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))


def _patch_everything(monkeypatch, fake_unity_project, *, url="https://fake/rel/X"):
    """Stub run_unity_build, make_zip, create_release so main() can run end-to-end."""
    import publish_build as cli_mod
    import unity_lib.build as build_mod
    import unity_lib.release as rel_mod

    def fake_run_unity_build(**kwargs):
        project_root = kwargs["project_root"]
        output_name = kwargs["output_name"]
        built = project_root / "Builds" / f"{output_name}.exe"
        built.parent.mkdir(parents=True, exist_ok=True)
        built.write_bytes(b"fake exe")
        return built

    def fake_make_zip(builds_dir, dist_dir, output_name, tag):
        dist_dir.mkdir(parents=True, exist_ok=True)
        zp = dist_dir / f"{output_name}_{tag}.zip"
        zp.write_bytes(b"zip")
        return zp

    def fake_create_release(project_root, tag, zip_path, notes, title, release_repo=None):
        return url

    monkeypatch.setattr(cli_mod, "run_unity_build", fake_run_unity_build)
    monkeypatch.setattr(cli_mod, "make_zip", fake_make_zip)
    monkeypatch.setattr(cli_mod, "create_release", fake_create_release)


def _run_cli(args, capsys) -> tuple[int, str, str]:
    import publish_build as cli_mod
    rc = cli_mod.main(args)
    out = capsys.readouterr()
    return rc, out.out, out.err


def test_full_flow_emits_json_on_stdout(fake_unity_project, monkeypatch, capsys):
    _patch_everything(monkeypatch, fake_unity_project)

    rc, stdout, stderr = _run_cli(
        [
            "--tag", "v0.1.0",
            "--scene", "Assets/Scenes/Main.unity",
            "--output-name", "MyGame",
            "--notes", "first cut",
            "--project-root", str(fake_unity_project),
        ],
        capsys,
    )

    assert rc == 0, stderr
    # One JSON line on stdout
    payload = json.loads(stdout.strip().splitlines()[-1])
    assert payload["tag"] == "v0.1.0"
    assert payload["output_name"] == "MyGame"
    assert payload["url"].startswith("https://")
    assert payload["zip"].endswith("MyGame_v0.1.0.zip")


def test_title_defaults_to_tag(fake_unity_project, monkeypatch, capsys):
    _patch_everything(monkeypatch, fake_unity_project)
    rc, stdout, _ = _run_cli(
        ["--tag", "v2", "--scene", "Assets/S.unity", "--project-root", str(fake_unity_project)],
        capsys,
    )
    assert rc == 0
    payload = json.loads(stdout.strip().splitlines()[-1])
    assert payload["title"] == "v2"


def test_skip_build_requires_existing_binary(fake_unity_project, monkeypatch, capsys):
    """--skip-build with no Builds/<name>.exe → rc=2 with helpful message."""
    _patch_everything(monkeypatch, fake_unity_project)

    rc, _, stderr = _run_cli(
        ["--tag", "v3", "--skip-build", "--output-name", "Missing",
         "--project-root", str(fake_unity_project)],
        capsys,
    )
    assert rc == 2
    assert "Missing.exe" in stderr or "not found" in stderr


def test_skip_build_uses_preexisting_binary(fake_unity_project, monkeypatch, capsys):
    """Artifact is already there; --skip-build should proceed straight to zip/release."""
    _patch_everything(monkeypatch, fake_unity_project)
    (fake_unity_project / "Builds" / "PreBuilt.exe").write_bytes(b"pre")

    rc, stdout, _ = _run_cli(
        ["--tag", "v4", "--skip-build", "--output-name", "PreBuilt",
         "--project-root", str(fake_unity_project)],
        capsys,
    )
    assert rc == 0
    payload = json.loads(stdout.strip().splitlines()[-1])
    assert payload["output_name"] == "PreBuilt"


def test_missing_scene_without_skip_build_is_usage_error(fake_unity_project, monkeypatch, capsys):
    _patch_everything(monkeypatch, fake_unity_project)
    rc, _, stderr = _run_cli(
        ["--tag", "v5", "--project-root", str(fake_unity_project)],
        capsys,
    )
    assert rc == 2
    assert "--scene" in stderr


def test_missing_notes_file_is_usage_error(fake_unity_project, monkeypatch, capsys):
    _patch_everything(monkeypatch, fake_unity_project)
    rc, _, stderr = _run_cli(
        ["--tag", "v6", "--skip-build", "--notes-file", str(fake_unity_project / "missing.md"),
         "--project-root", str(fake_unity_project)],
        capsys,
    )
    assert rc == 2
    assert "--notes-file" in stderr


def test_project_root_undetermined_returns_3(tmp_path, monkeypatch, capsys):
    """No explicit arg, no env, cwd has no Unity fingerprint → rc=3."""
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    import publish_build as cli_mod
    rc = cli_mod.main(["--tag", "v7", "--scene", "Assets/X.unity"])
    _, err = capsys.readouterr().out, capsys.readouterr().err
    assert rc == 3


def test_multiple_scenes_all_forwarded(fake_unity_project, monkeypatch, capsys):
    """--scene can be repeated; run_unity_build must receive all of them."""
    captured = {}

    import publish_build as cli_mod
    def fake_run_unity_build(**kwargs):
        captured["scenes"] = list(kwargs["scenes"])
        built = kwargs["project_root"] / "Builds" / f"{kwargs['output_name']}.exe"
        built.parent.mkdir(parents=True, exist_ok=True)
        built.write_bytes(b"e")
        return built

    monkeypatch.setattr(cli_mod, "run_unity_build", fake_run_unity_build)
    monkeypatch.setattr(cli_mod, "make_zip",
                        lambda builds_dir, dist_dir, output_name, tag: (dist_dir.mkdir(parents=True, exist_ok=True), (dist_dir / f"{output_name}_{tag}.zip"))[1]
                        if True else None)
    # Simpler form: write a zip inline and return it
    def fake_make_zip(builds_dir, dist_dir, output_name, tag):
        dist_dir.mkdir(parents=True, exist_ok=True)
        zp = dist_dir / f"{output_name}_{tag}.zip"
        zp.write_bytes(b"zip")
        return zp
    monkeypatch.setattr(cli_mod, "make_zip", fake_make_zip)
    monkeypatch.setattr(cli_mod, "create_release", lambda *a, **kw: "https://fake/rel")

    rc = cli_mod.main([
        "--tag", "v8",
        "--scene", "Assets/A.unity",
        "--scene", "Assets/B.unity",
        "--scene", "Assets/C.unity",
        "--project-root", str(fake_unity_project),
    ])
    assert rc == 0
    assert captured["scenes"] == [
        "Assets/A.unity", "Assets/B.unity", "Assets/C.unity",
    ]
