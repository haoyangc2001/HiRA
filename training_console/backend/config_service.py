"""Small JSON preset service with conservative field validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .errors import validation


_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
_FIELDS = {
    "task", "resume", "experiment_name", "run_name", "load_run", "checkpoint",
    "num_envs", "seed", "max_iterations", "rl_device", "low_level_model",
    "trajectory_root", "video_roots",
}


def validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(config) - _FIELDS)
    if unknown:
        raise validation("unsupported configuration fields", {"fields": unknown})
    result = dict(config)
    if result.get("task", "go2_high_level") != "go2_high_level":
        raise validation("only go2_high_level is supported")
    for field in ("experiment_name", "run_name"):
        value = result.get(field)
        if value is not None and (not isinstance(value, str) or not _NAME.fullmatch(value)):
            raise validation(f"{field} must contain only letters, numbers, dot, underscore and hyphen")
    for field, minimum, maximum in (("num_envs", 1, 4096), ("max_iterations", 1, 1_000_000), ("seed", -1, 2_147_483_647)):
        if field in result and (not isinstance(result[field], int) or isinstance(result[field], bool) or not minimum <= result[field] <= maximum):
            raise validation(f"{field} is outside its allowed range")
    if "checkpoint" in result and result["checkpoint"] is not None and (not isinstance(result["checkpoint"], int) or result["checkpoint"] < 0):
        raise validation("checkpoint must be a non-negative integer or null")
    device = result.get("rl_device", "cpu")
    if not isinstance(device, str) or not re.fullmatch(r"(?:cpu|cuda(?::\d+)?)", device):
        raise validation("rl_device must be cpu or cuda[:index]")
    if not isinstance(result.get("resume", False), bool):
        raise validation("resume must be a boolean")
    return result


class ConfigService:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.root.glob("*.json")):
            try:
                records.append({"id": path.stem, "config": json.loads(path.read_text(encoding="utf-8"))})
            except (OSError, json.JSONDecodeError):
                continue
        return records

    def get(self, name: str) -> dict[str, Any]:
        path = self.root / f"{name}.json"
        if path.resolve().parent != self.root:
            raise validation("invalid preset name")
        if not path.is_file():
            raise validation(f"preset not found: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name: str, config: Mapping[str, Any]) -> dict[str, Any]:
        if not _NAME.fullmatch(name):
            raise validation("invalid preset name")
        validated = validate_config(config)
        path = self.root / f"{name}.json"
        path.write_text(json.dumps(validated, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"id": name, "config": validated}

