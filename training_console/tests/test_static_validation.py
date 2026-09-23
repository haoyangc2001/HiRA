"""Final static/mock acceptance checks for the isolated console."""

import ast
import json
from pathlib import Path

from training_console.backend.parsers import parse_checkpoint, parse_training_log
from training_console.backend.replay import parse_trajectory_file


ROOT = Path(__file__).parents[1]
REPO = ROOT.parent


def test_required_console_structure_and_frontend_controls_exist():
    required = [
        ROOT / "backend" / "app.py",
        ROOT / "backend" / "process_manager.py",
        ROOT / "backend" / "parsers.py",
        ROOT / "backend" / "replay.py",
        ROOT / "frontend" / "index.html",
        ROOT / "frontend" / "app.js",
        ROOT / "frontend" / "replay.js",
        ROOT / "configs" / "schema.json",
        ROOT / "README.md",
    ]
    assert all(path.is_file() for path in required)
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    for control in ("config-form", "start-training", "video-player", "trajectory-canvas", "export-policy"):
        assert control in html


def test_backend_source_is_parseable_and_has_no_shell_string_execution():
    for path in (ROOT / "backend").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    process_source = (ROOT / "backend" / "process_manager.py").read_text(encoding="utf-8")
    assert "shell=False" in process_source
    assert "shell=True" not in process_source


def test_real_read_only_artifacts_are_parseable_without_training():
    log = REPO / "logs" / "high_level_go2" / "成功率收敛0.72_成本收敛79.1" / "training.log"
    result = parse_training_log(log)
    assert result["summary"]["latest_iteration"] == 1500
    assert result["summary"]["best_success_rate"] is not None

    checkpoint = REPO / "logs" / "high_level_go2" / "成功率收敛0.72_成本收敛79.1" / "model_1310.pt"
    metadata = parse_checkpoint(checkpoint)
    assert metadata["id"] == "model_1310.pt"
    assert metadata["size_bytes"] == checkpoint.stat().st_size


def test_fixture_trajectory_contract_is_complete():
    path = ROOT / "tests" / "fixtures" / "trajectory_sample.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = parse_trajectory_file(path)
    assert set(("checkpoint_path", "num_trajs", "max_steps", "low_level_model", "trajectories")) <= set(payload)
    assert result["num_trajs"] == 2


def test_no_tracked_existing_files_are_modified():
    import subprocess

    result = subprocess.run(["git", "diff", "--name-only"], cwd=REPO, text=True, capture_output=True, check=True)
    forbidden_prefixes = ("webui/", "legged_gym_go2/", "rsl_rl/", "unitree_rl_gym/", "isaacgym/", "logs/")
    assert not any(path.startswith(forbidden_prefixes) for path in result.stdout.splitlines())

