"""Isolated high-level actor export planning and execution boundary."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from .parsers import normalize_checkpoint_metadata


class ExportAdapterError(ValueError):
    """User-visible export validation error with a stable category."""

    category = "unsupported"

    def __init__(self, code: str, message: str, category: str = "unsupported"):
        super().__init__(message)
        self.code = code
        self.category = category


_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _safe_child(root: Path, name: str) -> Path:
    if not _SAFE_NAME.fullmatch(name):
        raise ExportAdapterError("EXPORT_NAME_INVALID", "export names may contain only letters, numbers, dot, underscore and hyphen", "validation")
    candidate = (root / name).resolve()
    if candidate.parent != root.resolve() and root.resolve() not in candidate.parents:
        raise ExportAdapterError("EXPORT_PATH_ESCAPE", "export path is outside the controlled output root", "security")
    return candidate


def _actor_value(actor_critic: Any) -> Any:
    if isinstance(actor_critic, Mapping) and "actor" in actor_critic:
        return actor_critic["actor"]
    actor = getattr(actor_critic, "actor", None)
    return actor if actor is not None else actor_critic


def _actor_hidden_dims(actor: Any) -> list[int]:
    state_dict: Mapping[str, Any] | None = None
    if isinstance(actor, Mapping):
        nested = actor.get("state_dict")
        state_dict = nested if isinstance(nested, Mapping) else actor
    elif hasattr(actor, "state_dict"):
        try:
            candidate = actor.state_dict()
            state_dict = candidate if isinstance(candidate, Mapping) else None
        except Exception:
            state_dict = None
    shapes: list[tuple[str, tuple[int, ...]]] = []
    if state_dict:
        for name, value in state_dict.items():
            shape = getattr(value, "shape", None)
            if shape is not None and len(shape) == 2:
                shapes.append((str(name), tuple(int(item) for item in shape)))
            elif isinstance(value, (list, tuple)) and value and isinstance(value[0], (list, tuple)):
                shapes.append((str(name), (len(value), len(value[0]))))
    shapes.sort(key=lambda item: item[0])
    if len(shapes) <= 2:
        return []
    return [shape[0] for _, shape in shapes[1:-1]]


def inspect_high_level_checkpoint(path: str | Path, payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate the high-level actor shape without running inference."""

    source = Path(path)
    if not source.is_file():
        raise ExportAdapterError("CHECKPOINT_NOT_FOUND", f"checkpoint not found: {source}", "not_found")
    if not isinstance(payload, Mapping) or "actor_critic" not in payload:
        raise ExportAdapterError(
            "ACTOR_CRITIC_MISSING",
            "checkpoint does not contain an actor_critic object",
            "unsupported",
        )
    actor = _actor_value(payload["actor_critic"])
    metadata = normalize_checkpoint_metadata(source, payload)
    return {
        "kind": "high_level_actor",
        "checkpoint": metadata,
        "hidden_dims": _actor_hidden_dims(actor),
        "actor_available": actor is not None,
        "runtime_required": True,
    }


def build_export_plan(
    checkpoint_path: str | Path,
    output_root: str | Path,
    payload: Mapping[str, Any] | None,
    *,
    export_id: str | None = None,
    output_name: str = "policy.pt",
) -> dict[str, Any]:
    """Create an isolated, non-overwriting export plan."""

    source = Path(checkpoint_path).resolve()
    root = Path(output_root).resolve()
    if not source.is_file():
        raise ExportAdapterError("CHECKPOINT_NOT_FOUND", f"checkpoint not found: {source}", "not_found")
    inspection = inspect_high_level_checkpoint(source, payload)
    chosen_id = export_id or f"export-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    job_dir = _safe_child(root, chosen_id)
    output_file = _safe_child(job_dir, output_name)
    if job_dir.exists():
        raise ExportAdapterError("EXPORT_EXISTS", f"export job already exists: {chosen_id}", "conflict")
    if output_file.suffix.lower() not in {".pt", ".jit"} and not output_file.name.endswith(".jit.pt"):
        raise ExportAdapterError("EXPORT_EXTENSION_INVALID", "high-level actor export must be a .pt or .jit file", "validation")
    return {
        "id": chosen_id,
        "status": "planned",
        "checkpoint": str(source),
        "kind": "high_level_actor",
        "output_root": str(root),
        "output_dir": str(job_dir),
        "output_path": str(output_file),
        "inspection": inspection,
    }


def execute_export(
    plan: Mapping[str, Any],
    payload_loader: Callable[[Path], Mapping[str, Any] | None],
    exporter: Callable[[Any, Path], None],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute an injected exporter, keeping model/runtime concerns out of the adapter.

    The production integration can supply an exporter that wraps the project's
    actor and TorchScript semantics.  Static validation uses a fixture exporter;
    this function itself never imports the training project or selects a GPU.
    """

    output_dir = Path(str(plan["output_dir"])).resolve()
    output_path = Path(str(plan["output_path"])).resolve()
    root = Path(str(plan["output_root"])).resolve()
    if root not in output_dir.parents:
        raise ExportAdapterError("EXPORT_PATH_ESCAPE", "export directory is outside the controlled root", "security")
    if dry_run:
        return {**dict(plan), "status": "planned", "dry_run": True, "error": None}
    if output_dir.exists():
        raise ExportAdapterError("EXPORT_EXISTS", "export output directory already exists", "conflict")
    output_dir.mkdir(parents=True, exist_ok=False)
    try:
        checkpoint = Path(str(plan["checkpoint"])).resolve()
        payload = payload_loader(checkpoint)
        if not isinstance(payload, Mapping) or "actor_critic" not in payload:
            raise ExportAdapterError("ACTOR_CRITIC_MISSING", "checkpoint actor is unavailable", "unsupported")
        exporter(_actor_value(payload["actor_critic"]), output_path)
        if not output_path.is_file():
            raise ExportAdapterError("EXPORT_OUTPUT_MISSING", "exporter did not create the output file", "process")
        manifest = {
            "id": plan["id"],
            "status": "completed",
            "checkpoint": plan["checkpoint"],
            "kind": plan["kind"],
            "output_path": plan["output_path"],
            "size_bytes": output_path.stat().st_size,
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {**dict(plan), **manifest, "error": None}
    except Exception as exc:
        shutil.rmtree(output_dir, ignore_errors=True)
        if isinstance(exc, ExportAdapterError):
            raise
        raise ExportAdapterError("EXPORT_FAILED", str(exc), "process") from exc

