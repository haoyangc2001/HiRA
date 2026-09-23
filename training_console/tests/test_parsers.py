"""Static parser checks; these tests never start Isaac Gym or a training process."""

from pathlib import Path

from training_console.backend.parsers import (
    discover_checkpoints,
    normalize_checkpoint_metadata,
    parse_checkpoint,
    parse_training_log,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_training_log_is_sorted_and_duplicate_iterations_use_last_value():
    result = parse_training_log(FIXTURES / "training_sample.log")
    assert [item["iteration"] for item in result["metrics"]] == [1, 2, 3, 4]
    assert result["metrics"][1]["success_rate"] == 0.25
    assert result["metrics"][2]["advantage_std"] is None
    assert result["summary"]["best_success_rate"] == 0.35
    assert result["summary"]["duration_seconds"] == 3.0


def test_checkpoint_json_loader_and_actor_metadata():
    result = parse_checkpoint(FIXTURES / "checkpoint_metadata.json")
    assert result["metadata_available"] is True
    assert result["iteration"] == 42
    assert result["success_rate"] == 0.75
    assert result["low_level_model_path"].endswith("policy_1.pt")
    assert result["actor"]["observation_dim"] == 3
    assert result["actor"]["action_dim"] == 3


def test_checkpoint_without_payload_remains_discoverable(tmp_path):
    checkpoint = tmp_path / "model_final.pt"
    checkpoint.write_bytes(b"not-a-pytorch-file")
    result = parse_checkpoint(checkpoint, loader=lambda _: (_ for _ in ()).throw(ValueError("bad payload")))
    assert result["id"] == "model_final.pt"
    assert result["metadata_available"] is False
    assert result["metadata_error"].startswith("ValueError:")


def test_normalization_accepts_missing_optional_fields(tmp_path):
    checkpoint = tmp_path / "model_10.pt"
    checkpoint.write_bytes(b"fixture")
    result = normalize_checkpoint_metadata(checkpoint, {"iteration": "10"})
    assert result["iteration"] == 10
    assert result["success_rate"] is None
    assert result["execution_cost"] is None


def test_discovery_returns_empty_for_missing_root(tmp_path):
    assert discover_checkpoints(tmp_path / "missing") == []

