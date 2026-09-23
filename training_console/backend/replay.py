"""Read-only video discovery and trajectory normalization for replay views."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping


class TrajectoryParseError(ValueError):
    """Raised when a trajectory file is not the supported collector format."""

    code = "TRAJECTORY_FORMAT_INVALID"
    category = "parse"


_VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
}


def _finite_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TrajectoryParseError(f"point coordinate is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise TrajectoryParseError(f"point coordinate is not finite: {value!r}")
    return number


def _bounds(points: list[list[float]]) -> dict[str, float] | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}


def normalize_trajectory_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize the exact JSON shape emitted by ``test_reach_avoid.py``."""

    if not isinstance(payload, Mapping):
        raise TrajectoryParseError("trajectory root must be a JSON object")
    raw_trajectories = payload.get("trajectories")
    if not isinstance(raw_trajectories, list):
        raise TrajectoryParseError("trajectory root must contain a trajectories array")

    normalized: list[dict[str, Any]] = []
    for trajectory_id, raw_points in enumerate(raw_trajectories):
        if not isinstance(raw_points, list):
            raise TrajectoryParseError(f"trajectory {trajectory_id} must be an array of XY points")
        points: list[list[float]] = []
        for point_index, raw_point in enumerate(raw_points):
            if not isinstance(raw_point, (list, tuple)) or len(raw_point) < 2:
                raise TrajectoryParseError(
                    f"trajectory {trajectory_id} point {point_index} must contain x and y"
                )
            points.append([_finite_number(raw_point[0]), _finite_number(raw_point[1])])
        normalized.append(
            {
                "trajectory_id": trajectory_id,
                "points": points,
                "bounds": _bounds(points),
                "status": "unknown",
                "point_count": len(points),
            }
        )

    declared_count = payload.get("num_trajs")
    count_warning = None
    if declared_count is not None:
        try:
            if int(declared_count) != len(normalized):
                count_warning = "num_trajs does not match trajectories length"
        except (TypeError, ValueError):
            count_warning = "num_trajs is not an integer"

    geometry = payload.get("geometry")
    geometry_status = "available" if isinstance(geometry, Mapping) else "geometry_unavailable"
    return {
        "checkpoint_path": payload.get("checkpoint_path"),
        "num_trajs": len(normalized),
        "max_steps": payload.get("max_steps"),
        "low_level_model": payload.get("low_level_model"),
        "trajectories": normalized,
        "geometry": geometry if isinstance(geometry, Mapping) else None,
        "geometry_status": geometry_status,
        "status": "empty" if not normalized else "ready",
        "warnings": [count_warning] if count_warning else [],
    }


def parse_trajectory_file(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"trajectory file not found: {source}")
    try:
        payload = json.loads(source.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise TrajectoryParseError(f"invalid trajectory JSON: {exc.msg}") from exc
    result = normalize_trajectory_payload(payload)
    result["source"] = str(source)
    return result


def discover_videos(root: str | Path) -> list[dict[str, Any]]:
    """Return controlled static video resources below ``root``."""

    base = Path(root)
    if not base.exists():
        return []
    resources: list[dict[str, Any]] = []
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _VIDEO_TYPES:
            continue
        relative = path.relative_to(base).as_posix()
        resources.append(
            {
                "id": relative,
                "path": str(path),
                "content_type": _VIDEO_TYPES[path.suffix.lower()],
                "size_bytes": path.stat().st_size,
            }
        )
    resources.sort(key=lambda item: item["id"])
    return resources


def canvas_frame(trajectory: Mapping[str, Any], frame_index: int) -> dict[str, Any]:
    """Build a serializable frame for a Canvas renderer."""

    points = trajectory.get("points")
    if not isinstance(points, list):
        raise TrajectoryParseError("normalized trajectory is missing points")
    if not points:
        return {"index": 0, "point": None, "progress": 0.0, "points": []}
    index = max(0, min(int(frame_index), len(points) - 1))
    return {
        "index": index,
        "point": points[index],
        "progress": index / max(1, len(points) - 1),
        "points": points[: index + 1],
    }

