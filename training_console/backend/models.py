"""Small transport models shared by the API and mock clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ErrorBody:
    code: str
    message: str
    category: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessStatus:
    status: str = "idle"
    run_id: str | None = None
    owner: str = "training_console"
    pid: int | None = None
    exit_code: int | None = None


@dataclass
class ExportStatus:
    id: str
    status: str
    kind: str = "high_level_actor"
    output_path: str | None = None
    error: ErrorBody | None = None


@dataclass
class RunSummary:
    id: str
    name: str
    status: str
    latest_iteration: int | None = None
    best_success_rate: float | None = None
    latest_cost: float | None = None

