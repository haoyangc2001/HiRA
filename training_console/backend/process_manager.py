"""Console-owned training process manager with dry-run default."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .config_service import validate_config
from .errors import conflict, validation, ConsoleError
from .settings import Settings


class ProcessManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.state_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.settings.state_root / "process.json"
        self.process: subprocess.Popen[str] | None = None
        self.owner = uuid.uuid4().hex
        self.record: dict[str, Any] = self._read_record()

    def _read_record(self) -> dict[str, Any]:
        if not self.state_path.is_file():
            return {"status": "idle", "run_id": None, "owner": self.owner, "pid": None, "exit_code": None}
        try:
            record = json.loads(self.state_path.read_text(encoding="utf-8"))
            return record if isinstance(record, dict) else {"status": "unknown", "owner": self.owner}
        except (OSError, json.JSONDecodeError):
            return {"status": "unknown", "owner": self.owner}

    def _write(self) -> None:
        self.record["owner"] = self.owner
        self.state_path.write_text(json.dumps(self.record, indent=2), encoding="utf-8")

    def _refresh(self) -> None:
        if self.process is None:
            return
        code = self.process.poll()
        if code is not None:
            self.record.update({"status": "completed" if code == 0 else "failed", "exit_code": code})
            self._write()

    def build_command(self, config: Mapping[str, Any]) -> list[str]:
        validated = validate_config(config)
        if self.settings.training_script is None or not self.settings.training_script.is_file():
            raise validation("training entry point is unavailable")
        command = [self.settings.python_executable, str(self.settings.training_script)]
        for key in ("task", "experiment_name", "run_name", "load_run", "rl_device", "num_envs", "seed", "max_iterations"):
            value = validated.get(key)
            if value is None or value == "":
                continue
            command.extend([f"--{key}", str(value)])
        if validated.get("resume"):
            command.append("--resume")
        if validated.get("checkpoint") is not None:
            command.extend(["--checkpoint", str(validated["checkpoint"])])
        return command

    def start(self, config: Mapping[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
        self._refresh()
        if self.record.get("status") in {"starting", "running", "stopping"}:
            raise conflict("a console-owned training process is already active", self.record)
        command = self.build_command(config)
        run_id = f"console-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        if dry_run or not self.settings.allow_process_start:
            self.record = {"status": "idle", "run_id": run_id, "owner": self.owner, "pid": None, "exit_code": None, "dry_run": True, "command": command}
            self._write()
            return self.record
        self.record = {"status": "starting", "run_id": run_id, "owner": self.owner, "pid": None, "exit_code": None, "command": command}
        self._write()
        try:
            self.process = subprocess.Popen(command, shell=False, cwd=str(self.settings.repository_root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.record.update({"status": "running", "pid": self.process.pid, "started_at": datetime.now(timezone.utc).isoformat()})
            self._write()
            return self.record
        except OSError as exc:
            self.record.update({"status": "failed", "exit_code": None, "error": str(exc)})
            self._write()
            raise ConsoleError("TRAIN_START_FAILED", str(exc), "process", 500)

    def status(self) -> dict[str, Any]:
        self._refresh()
        return dict(self.record)

    def stop(self, timeout: float = 2.0) -> dict[str, Any]:
        self._refresh()
        if self.process is None or self.record.get("status") not in {"starting", "running"}:
            return dict(self.record)
        self.record["status"] = "stopping"
        self._write()
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=timeout)
        self.record.update({"status": "completed" if self.process.returncode == 0 else "failed", "exit_code": self.process.returncode})
        self._write()
        return dict(self.record)

    def logs(self, limit: int = 200) -> dict[str, Any]:
        bounded = max(1, min(int(limit), 2000))
        return {"run_id": self.record.get("run_id"), "lines": [], "truncated": False, "limit": bounded}

