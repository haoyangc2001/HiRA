"""Read-only adapters for existing training logs and checkpoints.

The adapters deliberately return plain dictionaries so the API layer can use them
without importing the project's training packages.  They never mutate source
files and checkpoint loading is always CPU-only.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_FIELD_PATTERN = re.compile(rf"(?P<key>[A-Za-z][A-Za-z0-9_]*)\s+(?P<value>{_NUMBER})")
_ITER_PATTERN = re.compile(r"\biter\s+(?P<value>\d+)")
_ELAPSED_PATTERN = re.compile(rf"\belapsed\s+(?P<value>{_NUMBER})s\b")

_FIELD_NAMES = {
    "success": "success_rate",
    "cost": "execution_cost",
    "policy_loss": "policy_loss",
    "value_loss": "value_loss",
    "Vmean": "value_mean",
    "Rmean": "return_mean",
    "Vrmse": "value_rmse",
    "VexpVar": "explained_variance",
    "adv_std": "advantage_std",
}


def _number(value: Any) -> float | None:
    """Convert numeric values while treating non-finite values as missing."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_training_log(path: str | Path) -> dict[str, Any]:
    """Parse ``training.log`` into sorted, de-duplicated metrics and a summary.

    A line is accepted when it contains an integer ``iter`` token.  Other fields
    are optional and become ``None``.  If an iteration appears more than once,
    the last complete observation wins, which is useful for logs resumed from a
    checkpoint.  Incomplete trailing lines are skipped without failing the log.
    """

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"training log not found: {source}")

    by_iteration: dict[int, dict[str, Any]] = {}
    warnings: list[str] = []
    for line_number, line in enumerate(_read_text(source).splitlines(), start=1):
        iteration_match = _ITER_PATTERN.search(line)
        if not iteration_match:
            if line.strip():
                warnings.append(f"line {line_number}: missing iteration")
            continue
        iteration = int(iteration_match.group("value"))
        metric: dict[str, Any] = {
            "iteration": iteration,
            "success_rate": None,
            "execution_cost": None,
            "policy_loss": None,
            "value_loss": None,
            "value_mean": None,
            "return_mean": None,
            "value_rmse": None,
            "explained_variance": None,
            "advantage_std": None,
            "elapsed_seconds": None,
        }
        for match in _FIELD_PATTERN.finditer(line):
            target = _FIELD_NAMES.get(match.group("key"))
            if target:
                metric[target] = _number(match.group("value"))
        elapsed_match = _ELAPSED_PATTERN.search(line)
        if elapsed_match:
            metric["elapsed_seconds"] = _number(elapsed_match.group("value"))
        by_iteration[iteration] = metric

    metrics = [by_iteration[key] for key in sorted(by_iteration)]
    successes = [item["success_rate"] for item in metrics if item["success_rate"] is not None]
    costs = [item["execution_cost"] for item in metrics if item["execution_cost"] is not None]
    elapsed = [item["elapsed_seconds"] for item in metrics if item["elapsed_seconds"] is not None]
    summary = {
        "metric_count": len(metrics),
        "first_iteration": metrics[0]["iteration"] if metrics else None,
        "latest_iteration": metrics[-1]["iteration"] if metrics else None,
        "best_success_rate": max(successes) if successes else None,
        "latest_success_rate": successes[-1] if successes else None,
        "latest_execution_cost": costs[-1] if costs else None,
        "min_execution_cost": min(costs) if costs else None,
        "max_execution_cost": max(costs) if costs else None,
        "elapsed_seconds_first": elapsed[0] if elapsed else None,
        "elapsed_seconds_last": elapsed[-1] if elapsed else None,
        "duration_seconds": (elapsed[-1] - elapsed[0]) if len(elapsed) > 1 else None,
    }
    return {
        "source": str(source),
        "metrics": metrics,
        "summary": summary,
        "warnings": warnings,
    }


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _shape(value: Any) -> tuple[int, ...] | None:
    if hasattr(value, "shape"):
        try:
            return tuple(int(item) for item in value.shape)
        except (TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)):
        dimensions: list[int] = []
        current: Any = value
        while isinstance(current, (list, tuple)):
            dimensions.append(len(current))
            current = current[0] if current else None
        return tuple(dimensions) if dimensions else None
    return None


def infer_actor_dimensions(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Infer useful actor metadata without constructing or running a model."""

    actor = payload.get("actor_critic")
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

    weights: list[tuple[str, tuple[int, ...]]] = []
    if state_dict:
        for name, value in state_dict.items():
            shape = _shape(value)
            if shape and len(shape) == 2 and "actor" in str(name).lower():
                weights.append((str(name), shape))
    weights.sort(key=lambda item: item[0])
    return {
        "actor_weight_shapes": [{"name": name, "shape": list(shape)} for name, shape in weights],
        "observation_dim": weights[0][1][1] if weights else None,
        "action_dim": weights[-1][1][0] if weights else None,
    }


def normalize_checkpoint_metadata(path: str | Path, payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize known checkpoint keys; ``payload`` may be unavailable."""

    source = Path(path)
    result: dict[str, Any] = {
        "id": source.name,
        "path": str(source),
        "kind": "high_level" if source.name.startswith("model_") else "unknown",
        "iteration": None,
        "success_rate": None,
        "execution_cost": None,
        "low_level_model_path": None,
        "size_bytes": source.stat().st_size if source.exists() else None,
        "metadata_available": isinstance(payload, Mapping),
        "metadata_error": None,
        "actor": {"actor_weight_shapes": [], "observation_dim": None, "action_dim": None},
    }
    if not isinstance(payload, Mapping):
        return result
    result["iteration"] = _safe_int(payload.get("iteration"))
    result["success_rate"] = _number(payload.get("success_rate"))
    result["execution_cost"] = _number(payload.get("execution_cost"))
    low_level = payload.get("low_level_model_path")
    result["low_level_model_path"] = str(low_level) if low_level is not None else None
    result["actor"] = infer_actor_dimensions(payload)
    return result


def _default_checkpoint_loader(path: Path) -> Mapping[str, Any] | None:
    if path.suffix.lower() in {".json", ".jsonl"}:
        loaded = json.loads(_read_text(path))
        return loaded if isinstance(loaded, Mapping) else None
    # Keep static/mock deployments independent of native experiment runtimes.
    # Torch deserialization is enabled only when explicitly requested.
    if os.environ.get("EXPERIMENT_CONSOLE_ENABLE_TORCH_LOAD") != "1":
        return None
    try:
        import torch
    except ImportError:
        return None
    try:
        return torch.load(str(path), map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(str(path), map_location="cpu")


def parse_checkpoint(
    path: str | Path,
    loader: Callable[[Path], Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    """Discover a checkpoint and optionally read metadata using a safe loader."""

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"checkpoint not found: {source}")
    try:
        payload = (loader or _default_checkpoint_loader)(source)
        return normalize_checkpoint_metadata(source, payload)
    except Exception as exc:  # metadata failure must not hide a discoverable file
        result = normalize_checkpoint_metadata(source, None)
        result["metadata_error"] = f"{type(exc).__name__}: {exc}"
        return result


def discover_checkpoints(root: str | Path) -> list[dict[str, Any]]:
    """Find model checkpoints under a read-only root without modifying files."""

    base = Path(root)
    if not base.exists():
        return []
    candidates = [
        path
        for path in base.rglob("*.pt")
        if path.is_file() and (path.name.startswith("model_") or path.name == "model_final.pt")
    ]
    records = [parse_checkpoint(path) for path in candidates]
    records.sort(key=lambda item: (item["iteration"] is None, item["iteration"] or -1, item["id"]))
    return records
