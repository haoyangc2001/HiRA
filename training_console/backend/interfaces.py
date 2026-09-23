"""Stable adapter interfaces used by the FastAPI layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence


class MetricsAdapter(Protocol):
    def parse_log(self, path: Path) -> Mapping[str, Any]: ...

    def parse_checkpoint(self, path: Path) -> Mapping[str, Any]: ...


class ReplayAdapter(Protocol):
    def discover_videos(self, root: Path) -> Sequence[Mapping[str, Any]]: ...

    def parse_trajectory(self, path: Path) -> Mapping[str, Any]: ...


class TrainingAdapter(Protocol):
    def start(self, config: Mapping[str, Any], dry_run: bool = False) -> Mapping[str, Any]: ...

    def status(self) -> Mapping[str, Any]: ...

    def stop(self) -> Mapping[str, Any]: ...

    def logs(self, limit: int = 200) -> Mapping[str, Any]: ...


class ExportAdapter(Protocol):
    def inspect(self, checkpoint: Path) -> Mapping[str, Any]: ...

    def plan(self, checkpoint: Path, output_root: Path, **options: Any) -> Mapping[str, Any]: ...

    def execute(self, plan: Mapping[str, Any], dry_run: bool = False) -> Mapping[str, Any]: ...

