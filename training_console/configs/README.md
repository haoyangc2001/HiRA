# Configuration Presets

`schema.json` describes the version-one preset contract. `default.json` is intentionally conservative for local UI development: one environment, one iteration, and CPU selection. It is a preview configuration and is not run automatically.

## Mapped fields

The adapter maps `task`, `resume`, `experiment_name`, `run_name`, `load_run`, `checkpoint`, `num_envs`, `seed`, and `max_iterations` to the existing `get_args`/`update_cfg_from_args` interface. `rl_device` is validated and displayed, but the console does not run a local experiment during development.

`low_level_model`, `trajectory_root`, and `video_roots` are controlled read-only resource selectors. They are never written into existing project configuration files.

## Validation

- `task` is restricted to the registered high-level task.
- Numeric fields have explicit minimum and maximum values.
- Experiment/run names use safe filename characters only.
- Resource paths are resolved by the backend against configured roots.
- A preset is saved atomically under `training_console/configs/` and never overwrites repository logs or checkpoints.
