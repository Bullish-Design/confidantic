from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIDANTIC_JUSTFILE = REPO_ROOT / "scripts" / "confidantic.just"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures" / "python"


@pytest.fixture
def workshop_env(tmp_path: Path) -> dict[str, str]:
    if shutil.which("just") is None:
        pytest.skip("just is required for workflow integration tests")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    confidantic_bin = bin_dir / "confidantic"
    confidantic_bin.write_text(
        "#!/usr/bin/env bash\n"
        "exec python -m confidantic.cli \"$@\"\n",
        encoding="utf-8",
    )
    confidantic_bin.chmod(0o755)

    cue_log = tmp_path / "cue-wrapper.log"
    cue_wrapper = bin_dir / "confidantic-cue"
    cue_wrapper.write_text(
        "#!/usr/bin/env bash\n"
        "set -eu -o pipefail\n"
        "echo \"$*\" >> \"${CONFIDANTIC_CUE_LOG:?}\"\n"
        "cmd=${1:-}\n"
        "target=${2:-}\n"
        "if [[ -z \"$cmd\" || -z \"$target\" ]]; then\n"
        "  exit 4\n"
        "fi\n"
        "if [[ ! -e \"$target\" ]]; then\n"
        "  exit 2\n"
        "fi\n"
        "if [[ \"$cmd\" == \"vet\" ]] && ! compgen -G \"$target/*.cue\" >/dev/null; then\n"
        "  exit 3\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    cue_wrapper.chmod(0o755)

    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["CONFIDANTIC_CUE_LOG"] = str(cue_log)
    env["CONFIDANTIC_ROOT"] = str(tmp_path / ".devman" / ".config")

    return env


@pytest.fixture
def workshop_project(tmp_path: Path) -> Path:
    node_types_target = tmp_path / "build" / "treesitter" / "python"
    node_types_target.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_ROOT / "node-types.json", node_types_target / "node-types.json")
    shutil.copytree(FIXTURES_ROOT / "queries", node_types_target / "queries")
    return tmp_path


def _run_just(args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["just", "--justfile", str(CONFIDANTIC_JUSTFILE), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_workflow_happy_path_generate_fmt_vet(
    workshop_project: Path,
    workshop_env: dict[str, str],
) -> None:
    result_generate = _run_just(["cue-from-ts-generate", "python"], workshop_project, workshop_env)
    assert result_generate.returncode == 0, result_generate.stderr

    result_fmt = _run_just(["cue-from-ts-fmt", "python"], workshop_project, workshop_env)
    assert result_fmt.returncode == 0, result_fmt.stderr

    result_vet = _run_just(["cue-from-ts-vet", "python"], workshop_project, workshop_env)
    assert result_vet.returncode == 0, result_vet.stderr

    generated_dir = workshop_project / "build" / "schemas" / "cue" / "python"
    assert sorted(path.name for path in generated_dir.glob("*.cue")) == [
        "captures.cue",
        "metadata.cue",
        "node_types.cue",
    ]


def test_generate_fails_with_missing_required_inputs(
    tmp_path: Path,
    workshop_env: dict[str, str],
) -> None:
    missing_node_types = _run_just(["cue-from-ts-generate", "python"], tmp_path, workshop_env)
    assert missing_node_types.returncode == 1

    treesitter_dir = tmp_path / "build" / "treesitter" / "python"
    treesitter_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES_ROOT / "node-types.json", treesitter_dir / "node-types.json")

    missing_queries = _run_just(["cue-from-ts-generate", "python"], tmp_path, workshop_env)
    assert missing_queries.returncode == 1


def test_workshop_one_shot_runs_generate_fmt_and_vet(
    workshop_project: Path,
    workshop_env: dict[str, str],
) -> None:
    result = _run_just(["cue-from-ts-workshop", "python"], workshop_project, workshop_env)
    assert result.returncode == 0, result.stderr

    cue_log = Path(workshop_env["CONFIDANTIC_CUE_LOG"])
    invocations = cue_log.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith("fmt ") for line in invocations)
    assert any(line.startswith("vet ") for line in invocations)
