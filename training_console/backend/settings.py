"""Controlled roots and environment-independent console settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repository_root: Path
    console_root: Path
    logs_root: Path
    media_roots: tuple[Path, ...]
    trajectory_roots: tuple[Path, ...]
    exports_root: Path
    config_root: Path
    state_root: Path
    python_executable: str = "python"
    training_script: Path | None = None
    allow_process_start: bool = False

    @classmethod
    def from_repository(cls, repository_root: str | Path) -> "Settings":
        repository = Path(repository_root).resolve()
        console = repository / "training_console"
        return cls(
            repository_root=repository,
            console_root=console,
            logs_root=repository / "logs",
            media_roots=(repository / "logs", repository / "webui" / "assets"),
            trajectory_roots=(repository / "logs", console / "fixtures"),
            exports_root=console / "exports",
            config_root=console / "configs",
            state_root=console / ".state",
            training_script=repository / "legged_gym_go2" / "legged_gym" / "scripts" / "train_reach_avoid.py",
        )

