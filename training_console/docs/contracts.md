# Experiment Console Data Contracts

The first version uses JSON over HTTP. Every error response has the same shape:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "A user-readable message",
    "category": "not_found",
    "details": {}
  }
}
```

## Run

```json
{
  "id": "high_level_go2/20260105-102613",
  "name": "20260105-102613",
  "experiment_name": "high_level_go2",
  "root": "logs/high_level_go2/20260105-102613",
  "status": "completed",
  "latest_iteration": 1500,
  "best_success_rate": 0.743,
  "latest_cost": 79.1,
  "log_file": "training.log",
  "checkpoints": [],
  "videos": [],
  "trajectories": []
}
```

Allowed process statuses are `idle`, `starting`, `running`, `stopping`, `completed`, `failed`, and `unknown`.

## Metric

```json
{
  "iteration": 1500,
  "success_rate": 0.691,
  "execution_cost": 79.1,
  "policy_loss": 0.06821,
  "value_loss": 896.34966,
  "value_mean": -231.38,
  "return_mean": -231.471,
  "value_rmse": 41.553,
  "explained_variance": 0.896,
  "advantage_std": 41.553
}
```

Unknown or missing metric fields are represented as `null` and do not invalidate the rest of a log line.

## Checkpoint

```json
{
  "id": "model_1300.pt",
  "path": "logs/high_level_go2/run/model_1300.pt",
  "kind": "high_level",
  "iteration": 1300,
  "success_rate": 0.72,
  "execution_cost": 79.1,
  "low_level_model_path": "logs/rough_go2/run/model_18500.pt",
  "size_bytes": 8697
}
```

Checkpoint metadata is optional because reading a PyTorch file may be unavailable in a lightweight deployment. File discovery must still work when metadata is unavailable.

## Trajectory

The adapter accepts the existing collector shape:

```json
{
  "checkpoint_path": "...",
  "num_trajs": 1,
  "max_steps": 500,
  "low_level_model": "...",
  "trajectories": [[[0.0, 0.0], [0.1, 0.0]]]
}
```

The normalized response adds `trajectory_id`, `points`, `bounds`, and optional `status`. XY uses meters in the environment/world frame. Missing obstacle or goal geometry is reported as `geometry_unavailable`, not guessed by the browser.

## Video and Export

```json
{
  "id": "play_go2_20260105.mp4",
  "path": "videos/play_go2_20260105.mp4",
  "content_type": "video/mp4",
  "size_bytes": 12345
}
```

```json
{
  "id": "export-20260918-120000",
  "status": "completed",
  "checkpoint": "model_final.pt",
  "kind": "high_level_actor",
  "output_path": "training_console/exports/export-20260918-120000/policy_1.pt",
  "error": null
}
```

## Error Categories

`validation`, `not_found`, `conflict`, `process`, `parse`, `unsupported`, `security`, and `infrastructure` are the only user-visible categories in version one.
