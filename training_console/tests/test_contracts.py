"""Contract smoke checks independent of FastAPI and Isaac Gym."""

import json
from pathlib import Path

from training_console.backend.interfaces import ExportAdapter, MetricsAdapter, ReplayAdapter, TrainingAdapter


def test_api_samples_have_shared_error_and_terminal_shapes():
    sample = json.loads((Path(__file__).parent / "fixtures" / "api_samples.json").read_text(encoding="utf-8"))
    assert set(sample["error"]) == {"code", "message", "category", "details"}
    assert sample["train_status"]["owner"] == "training_console"
    assert sample["export_status"]["kind"] == "high_level_actor"


def test_protocols_are_importable_without_runtime_dependencies():
    assert MetricsAdapter and ReplayAdapter and TrainingAdapter and ExportAdapter

