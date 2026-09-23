# Backend Boundary Design

## Modules

```text
backend/
├── app.py               FastAPI application and route registration
├── settings.py          Controlled repository roots and runtime settings
├── models.py            Pydantic-compatible request/response models
├── errors.py            Typed API errors and exception handlers
├── file_registry.py     Read-only discovery under allowed roots
├── parsers.py           Log, checkpoint metadata and trajectory parsers
├── process_manager.py   Owned training subprocess lifecycle
├── adapters.py          Training and export adapter interfaces
└── services.py          Run, replay, export and configuration orchestration
```

## API Groups

| Group | Routes | Responsibility |
| --- | --- | --- |
| Runs | `GET /api/runs`, `GET /api/runs/{run_id}` | Discover and summarize experiments |
| Metrics | `GET /api/runs/{run_id}/metrics` | Parse and return metrics |
| Replay | `GET /api/videos`, `GET /api/trajectories/{id}` | Serve controlled media and trajectory data |
| Training | `POST /api/train/start`, `GET /api/train/status`, `POST /api/train/stop`, `GET /api/train/logs` | Manage only console-owned child processes |
| Config | `GET/POST/DELETE /api/configs` | Validate and persist console presets |
| Export | `POST /api/export`, `GET /api/export/{id}`, `GET /api/export/{id}/download` | Isolated high-level actor export |

## Resource Roots

The server resolves paths from explicit roots only:

- `repository_root`: the checkout containing the existing project.
- `logs_root`: `repository_root/logs` for read-only training artifacts.
- `media_root`: configured video roots, restricted to media extensions.
- `trajectory_root`: configured trajectory JSON roots.
- `console_root`: `training_console` for presets, process state and exports.

Every requested relative path is normalized and must remain under its selected root. Absolute paths, `..` traversal, symlinks escaping a root, and unlisted extensions are rejected with `security` errors.

## Process State

The process manager persists a small JSON state record with an opaque run id, PID, command vector, start time, current status, exit code, and ownership marker. It only accepts stop requests for records created by the current manager instance. Commands are passed to `subprocess.Popen` as a list with `shell=False`.

## Static Validation Strategy

- Import and route tests use FastAPI's test client with mocked adapters.
- File registry tests use temporary directories and never touch the existing project artifacts.
- Parser tests use fixed log/checkpoint/trajectory samples.
- Process manager tests use a short safe fixture process, not the Isaac Gym training entry point.
- PyTorch checkpoint deserialization is opt-in via `EXPERIMENT_CONSOLE_ENABLE_TORCH_LOAD=1`; default static mode only discovers files and reports metadata as unavailable.
