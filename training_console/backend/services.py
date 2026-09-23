"""Read-only resource services used by app.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .file_registry import list_files
from .parsers import parse_training_log
from .replay import discover_videos, parse_trajectory_file
from .settings import Settings


class ConsoleServices:
    def __init__(self, settings: Settings):
        self.settings = settings

    def videos(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for root_index, root in enumerate(self.settings.media_roots):
            for item in discover_videos(root):
                item = dict(item)
                item["id"] = f"media-{root_index}/{item['id']}"
                item["url"] = f"/api/videos/{item['id']}"
                result.append(item)
        return result

    def trajectories(self) -> list[dict[str, Any]]:
        result = []
        for root_index, root in enumerate(self.settings.trajectory_roots):
            paths = list_files((root,), {".json"})
            for path in paths:
                try:
                    parsed = parse_trajectory_file(path)
                except Exception:
                    continue
                relative = path.relative_to(root).as_posix()
                result.append({"id": f"trajectory-{root_index}/{relative}", "source": relative, "root_index": root_index, "status": parsed["status"], "num_trajs": parsed["num_trajs"]})
        return result

    def _trajectory_path(self, trajectory_id: str) -> Path:
        if not trajectory_id.startswith("trajectory-") or "/" not in trajectory_id:
            raise ValueError("invalid trajectory id")
        prefix, relative = trajectory_id.split("/", 1)
        try:
            root_index = int(prefix.removeprefix("trajectory-"))
            root = self.settings.trajectory_roots[root_index]
        except (ValueError, IndexError):
            raise ValueError("invalid trajectory root") from None
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents or candidate.suffix.lower() != ".json":
            raise ValueError("trajectory path outside controlled root")
        return candidate

    def runs(self) -> list[dict[str, Any]]:
        records = []
        if not self.settings.logs_root.exists():
            return records
        for log in self.settings.logs_root.rglob("training.log"):
            try:
                parsed = parse_training_log(log)
            except OSError:
                continue
            records.append({"id": str(log.parent.relative_to(self.settings.logs_root)).replace("\\", "/"), "name": log.parent.name, "root": str(log.parent), "status": "completed", "latest_iteration": parsed["summary"]["latest_iteration"], "best_success_rate": parsed["summary"]["best_success_rate"], "latest_cost": parsed["summary"]["latest_execution_cost"], "log_file": str(log)})
        return sorted(records, key=lambda item: item["id"])

    def metrics(self, run_id: str) -> dict[str, Any]:
        candidate = (self.settings.logs_root / run_id / "training.log").resolve()
        if self.settings.logs_root.resolve() not in candidate.parents:
            raise ValueError("run path outside logs root")
        return parse_training_log(candidate)

    def trajectory(self, source: str) -> dict[str, Any]:
        return parse_trajectory_file(self._trajectory_path(source))

    def video_path(self, video_id: str) -> Path:
        if not video_id.startswith("media-") or "/" not in video_id:
            raise ValueError("invalid video id")
        prefix, relative = video_id.split("/", 1)
        try:
            root = self.settings.media_roots[int(prefix.removeprefix("media-"))]
        except (ValueError, IndexError):
            raise ValueError("invalid media root") from None
        candidate = (root / relative).resolve()
        if root.resolve() not in candidate.parents or candidate.suffix.lower() not in {".mp4", ".webm", ".ogg"}:
            raise ValueError("video path outside controlled root")
        return candidate
