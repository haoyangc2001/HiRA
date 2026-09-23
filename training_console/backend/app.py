"""FastAPI application entry point for the isolated experiment console."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import FileResponse, JSONResponse
except ImportError:  # pragma: no cover - permits static checks without installing FastAPI
    FastAPI = None  # type: ignore[assignment]

from .config_service import ConfigService, validate_config
from .errors import ConsoleError
from .process_manager import ProcessManager
from .services import ConsoleServices
from .settings import Settings


def create_app(repository_root: str | Path | None = None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed; install training_console/requirements.txt to run the API")
    settings = Settings.from_repository(repository_root or Path(__file__).resolve().parents[2])
    services = ConsoleServices(settings)
    config_service = ConfigService(settings.config_root)
    process_manager = ProcessManager(settings)
    app = FastAPI(title="Experiment Console", version="0.1.0")

    @app.exception_handler(ConsoleError)
    async def handle_console_error(_request: Request, exc: ConsoleError):
        return JSONResponse(status_code=exc.status_code, content=exc.body())

    @app.get("/api/runs")
    def runs(): return {"items": services.runs()}

    @app.get("/api/runs/{run_id:path}/metrics")
    def metrics(run_id: str): return services.metrics(run_id)

    @app.get("/api/videos")
    def videos(): return {"items": services.videos()}

    @app.get("/api/videos/{video_id:path}")
    def video(video_id: str):
        path = services.video_path(video_id)
        if not path.is_file():
            raise ConsoleError("RESOURCE_NOT_FOUND", "video was not found", "not_found", 404)
        return FileResponse(path)

    @app.get("/api/trajectories")
    def trajectories(): return {"items": services.trajectories()}

    @app.get("/api/trajectories/{trajectory_id:path}")
    def trajectory(trajectory_id: str): return services.trajectory(trajectory_id)

    @app.get("/api/configs")
    def configs(): return {"items": config_service.list()}

    @app.post("/api/config/validate")
    def config_validate(config: dict[str, Any]): return {"valid": True, "config": validate_config(config)}

    @app.post("/api/configs/{name}")
    def config_save(name: str, config: dict[str, Any]): return config_service.save(name, config)

    @app.post("/api/train/start", status_code=201)
    def train_start(request: dict[str, Any]):
        return process_manager.start(request.get("config", request), dry_run=bool(request.get("dry_run", True)))

    @app.get("/api/train/status")
    def train_status(): return process_manager.status()

    @app.post("/api/train/stop")
    def train_stop(): return process_manager.stop()

    @app.get("/api/train/logs")
    def train_logs(limit: int = 200): return process_manager.logs(limit)

    @app.post("/api/export", status_code=201)
    def export(request: dict[str, Any]):
        return {"status": "planned", "kind": "high_level_actor", "dry_run": True, "request": request}

    @app.get("/health")
    def health(): return {"status": "ok", "mode": "static/mock-compatible"}

    return app


app = None
if FastAPI is not None:
    app = create_app()
