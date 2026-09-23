# Training Orchestration Contract

The console launches only the existing high-level entry point through a controlled argument vector. It does not import or rewrite the training loop.

## Start

`POST /api/train/start`

```json
{
  "preset": "default",
  "dry_run": true
}
```

The adapter validates the preset, resolves the configured Python executable and script path against the repository root, then builds an argument list. The first version exposes `dry_run` for static verification; it prints the command plan without launching a process.

## Ownership and Mutual Exclusion

- Only one console-owned training process may be active at a time.
- A second start returns `409 CONFLICT` with the existing process id and status.
- Each process record has a random ownership marker stored in the console state directory.
- Stop requests require a matching owned record; unknown or external PIDs are rejected.

## Status

`GET /api/train/status` returns:

```json
{
  "status": "running",
  "run_id": "console-20260918-120000",
  "pid": 1234,
  "started_at": "2026-09-18T12:00:00+08:00",
  "exit_code": null,
  "latest_checkpoint": null,
  "latest_iteration": null
}
```

The manager recognizes `starting`, `running`, `stopping`, `completed`, `failed`, and `unknown`. It reads the generated log only after a run directory is known and never treats a partial log as completion.

## Stop and Recovery

- Stop transitions an owned process to `stopping`, sends a graceful termination request, waits for a bounded interval, and records the final exit code.
- Repeated stop calls are idempotent.
- Recovery is represented by a preset with `resume=true` and a validated checkpoint/load-run selection; the existing script receives the supported flags.
- Process stdout and stderr are written to an isolated console run log with no credentials or raw environment dump.

## Static Verification

Tests use a short fixture process and `dry_run=true`. They do not call the Isaac Gym training script or require CUDA.
