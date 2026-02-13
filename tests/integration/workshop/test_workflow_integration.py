from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures" / "python"


def _cli(env: dict[str, str], cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["confidantic", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def _make_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    confidantic_bin = bin_dir / "confidantic"
    confidantic_bin.write_text(
        "#!/usr/bin/env bash\n"
        "exec python -c 'from confidantic.cli import main; main()' \"$@\"\n",
        encoding="utf-8",
    )
    confidantic_bin.chmod(0o755)

    cue_log = tmp_path / "cue.log"
    cue_bin = bin_dir / "cue"
    cue_bin.write_text(
        "#!/usr/bin/env bash\n"
        "set -eu -o pipefail\n"
        "echo \"$*\" >> \"${CONFIDANTIC_CUE_LOG:?}\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    cue_bin.chmod(0o755)

    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["CONFIDANTIC_CUE_LOG"] = str(cue_log)
    env["CONFIDANTIC_ROOT"] = str(tmp_path / ".devman" / ".config")
    return env


def _make_project(tmp_path: Path) -> Path:
    node_types_target = tmp_path / "build" / "treesitter" / "python"
    node_types_target.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_ROOT / "node-types.json", node_types_target / "node-types.json")
    shutil.copytree(FIXTURES_ROOT / "queries", node_types_target / "queries")
    return tmp_path


def test_workflow_happy_path_generate_fmt_vet(tmp_path: Path) -> None:
    env = _make_env(tmp_path)
    project = _make_project(tmp_path)

    assert _cli(env, project, "workflow", "generate", "python").returncode == 0
    assert _cli(env, project, "workflow", "fmt", "python").returncode == 0
    assert _cli(env, project, "workflow", "vet", "python").returncode == 0

    generated_dir = project / "build" / "schemas" / "cue" / "python"
    assert sorted(path.name for path in generated_dir.glob("*.cue")) == ["captures.cue", "metadata.cue", "node_types.cue"]


def test_generate_fails_with_missing_required_inputs(tmp_path: Path) -> None:
    env = _make_env(tmp_path)
    missing_node_types = _cli(env, tmp_path, "workflow", "generate", "python")
    assert missing_node_types.returncode == 1

    treesitter_dir = tmp_path / "build" / "treesitter" / "python"
    treesitter_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_ROOT / "node-types.json", treesitter_dir / "node-types.json")

    missing_queries = _cli(env, tmp_path, "workflow", "generate", "python")
    assert missing_queries.returncode == 1


def test_workshop_one_shot_runs_generate_and_vet(tmp_path: Path) -> None:
    env = _make_env(tmp_path)
    project = _make_project(tmp_path)

    result = _cli(env, project, "workflow", "workshop", "python")
    assert result.returncode == 0, result.stderr

    invocations = Path(env["CONFIDANTIC_CUE_LOG"]).read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("fmt ") for line in invocations)
    assert any(line.startswith("vet ") for line in invocations)
