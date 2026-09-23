"""Static export adapter checks using an injected fixture exporter."""

from pathlib import Path

import pytest

from training_console.backend.export_adapter import (
    ExportAdapterError,
    build_export_plan,
    execute_export,
    inspect_high_level_checkpoint,
)


FIXTURE = Path(__file__).parent / "fixtures" / "checkpoint_metadata.json"


def fixture_payload():
    import json

    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_inspection_and_plan_are_high_level_only(tmp_path):
    inspection = inspect_high_level_checkpoint(FIXTURE, fixture_payload())
    assert inspection["kind"] == "high_level_actor"
    plan = build_export_plan(FIXTURE, tmp_path, fixture_payload(), export_id="job-001")
    assert plan["output_path"].endswith("job-001\\policy.pt") or plan["output_path"].endswith("job-001/policy.pt")
    assert plan["inspection"]["runtime_required"] is True


def test_dry_run_does_not_create_output(tmp_path):
    plan = build_export_plan(FIXTURE, tmp_path, fixture_payload(), export_id="dry-run")
    result = execute_export(plan, lambda _: fixture_payload(), lambda _actor, _path: None, dry_run=True)
    assert result["status"] == "planned"
    assert not Path(plan["output_dir"]).exists()


def test_injected_exporter_writes_manifest(tmp_path):
    plan = build_export_plan(FIXTURE, tmp_path, fixture_payload(), export_id="success")

    def exporter(_actor, output_path):
        output_path.write_bytes(b"static-export-fixture")

    result = execute_export(plan, lambda _: fixture_payload(), exporter)
    assert result["status"] == "completed"
    assert Path(result["output_path"]).is_file()
    assert Path(result["output_dir"], "manifest.json").is_file()


def test_failed_export_cleans_only_new_job(tmp_path):
    plan = build_export_plan(FIXTURE, tmp_path, fixture_payload(), export_id="failure")

    with pytest.raises(ExportAdapterError, match="boom"):
        execute_export(plan, lambda _: fixture_payload(), lambda _actor, _path: (_ for _ in ()).throw(RuntimeError("boom")))
    assert not Path(plan["output_dir"]).exists()


def test_missing_actor_is_rejected(tmp_path):
    with pytest.raises(ExportAdapterError) as error:
        build_export_plan(FIXTURE, tmp_path, {"iteration": 1}, export_id="invalid")
    assert error.value.code == "ACTOR_CRITIC_MISSING"

