"""Backend structure and security checks that do not require FastAPI."""

from pathlib import Path

import pytest

from training_console.backend.config_service import validate_config
from training_console.backend.errors import ConsoleError
from training_console.backend.file_registry import contained_path
from training_console.backend.models import ExportStatus, ProcessStatus


def test_config_validation_accepts_default_shape_and_rejects_unknown_field():
    config = validate_config({"task": "go2_high_level", "num_envs": 1, "seed": 1, "max_iterations": 1, "rl_device": "cpu"})
    assert config["task"] == "go2_high_level"
    with pytest.raises(ConsoleError) as error:
        validate_config({"shell": "rm -rf"})
    assert error.value.category == "validation"


def test_contained_path_rejects_traversal(tmp_path):
    assert contained_path(tmp_path, "logs/file.txt") == (tmp_path / "logs/file.txt").resolve()
    with pytest.raises(ConsoleError) as error:
        contained_path(tmp_path, "../outside.txt")
    assert error.value.category == "security"


def test_transport_models_have_stable_defaults():
    assert ProcessStatus().status == "idle"
    assert ExportStatus(id="fixture", status="planned").kind == "high_level_actor"

