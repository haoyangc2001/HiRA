# Experiment Console Architecture

## Confirmed Decisions

- Backend: FastAPI, with no dependency on the Isaac Gym runtime for read-only pages or mock validation.
- Frontend: native HTML, CSS, and JavaScript served as a single-page console; no React/Vue build chain in version one.
- Export scope: high-level navigation actor by default. Low-level locomotion files are displayed as referenced dependencies but are not exported by the first version.
- Configuration scope: only safe, existing command-line overrides are mapped initially: `task`, `resume`, `experiment_name`, `run_name`, `load_run`, `checkpoint`, `num_envs`, `seed`, and `max_iterations`. Environment geometry remains a read-only preset description.
- Process lifecycle: the console may stop only a training process created by its own process manager and recorded in its local state. It must not attach to or terminate external processes.
- Trajectory source: only JSON produced by the existing `test_reach_avoid.py` contract is supported in version one.

## Directory Boundary

```text
training_console/
├── backend/       FastAPI app, adapters, parsers, process manager
├── frontend/      Static console page and browser modules
├── configs/       JSON presets and schema documentation
├── exports/       Isolated policy export destination
└── docs/          Baseline, architecture, contracts and verification notes
```

No existing source, configuration, log, checkpoint, video, trajectory, or `webui/` file is an implementation dependency that may be edited.

## Development and Runtime Modes

1. **Mock/static mode:** uses fixed samples and does not require Isaac Gym, CUDA, or a trained policy.
2. **Read-only repository mode:** scans configured `logs/` and media roots and parses existing artifacts.
3. **Training mode:** starts the existing training entry point as a child process only when the user explicitly requests it through the API; this mode is not executed during local validation.

## Security Rules

- Build subprocess commands as argument arrays, never shell strings.
- Resolve all repository resources against configured roots and reject path traversal.
- Allow only known file extensions for media, logs, trajectory JSON, checkpoints, and exports.
- Keep process state in the console directory and use an ownership token generated per process record; never infer ownership from a PID alone.
- Do not expose arbitrary filesystem browsing or arbitrary command execution through the API.
