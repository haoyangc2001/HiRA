# Frozen API and Adapter Contracts

All endpoints return JSON. Errors use the shared shape from `contracts.md`:
`error.code`, `error.message`, `error.category` and `error.details`.

| Method | Route | Success | Purpose |
| --- | --- | --- | --- |
| GET | `/api/runs` | 200 | List read-only experiment runs |
| GET | `/api/runs/{run_id}/metrics` | 200 | Return parsed metrics and summary |
| GET | `/api/videos` | 200 | List controlled video resources |
| GET | `/api/videos/{video_id}` | 200/206 | Stream a controlled video |
| GET | `/api/trajectories` | 200 | List configured trajectory files |
| GET | `/api/trajectories/{trajectory_id}` | 200 | Return normalized Canvas data |
| POST | `/api/train/start` | 201/409 | Start one console-owned process or dry-run |
| GET | `/api/train/status` | 200 | Return process state and ownership |
| POST | `/api/train/stop` | 200/409 | Stop only the console-owned process |
| GET | `/api/train/logs` | 200 | Return bounded stdout/stderr tail |
| POST | `/api/config/validate` | 200/422 | Validate a safe CLI-style preset |
| POST | `/api/export` | 201/422/409 | Plan or execute a high-level actor export |
| GET | `/api/export/{export_id}` | 200 | Return export manifest/status |
| GET | `/api/export/{export_id}/download` | 200 | Download a completed export |

## Adapter mapping

| API concern | Adapter boundary | Static implementation |
| --- | --- | --- |
| Metrics and checkpoints | `MetricsAdapter` | `backend.parsers` |
| Videos and trajectories | `ReplayAdapter` | `backend.replay` |
| Training lifecycle | `TrainingAdapter` | `backend.process_manager` in TASK-012 |
| High-level actor export | `ExportAdapter` | `backend.export_adapter` |

## Minimal call sequence

```text
validate config -> start (dry_run or process) -> poll status/logs
       -> select run -> read metrics -> select video/trajectory -> replay
       -> select checkpoint -> export plan -> export status -> download
```

The frontend only sends IDs and validated configuration fields. It never sends
an executable shell string or uses a raw filesystem path as an action target.

