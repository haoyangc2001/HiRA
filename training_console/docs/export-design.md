# High-Level Actor Export Adapter

The first export target is the high-level navigation actor. The low-level
locomotion checkpoint is displayed as a dependency only and is not exported by
this adapter.

`inspect_high_level_checkpoint` checks for an `actor_critic` key and reports
checkpoint metadata plus any inferable actor hidden dimensions. It does not
construct the environment, run inference, select a GPU or modify the source
checkpoint.

`build_export_plan` validates a controlled checkpoint and creates a unique job
directory below `training_console/exports/`. Names are restricted to a safe
allow-list, existing job directories are rejected, and only `.pt`/`.jit` output
files are accepted.

`execute_export` accepts an injected payload loader and exporter. This keeps the
adapter independent from the existing training modules and makes dry-run and
fixture validation possible without Isaac Gym. On failure, only the newly
created job directory is removed; existing checkpoints and exports are never
overwritten.

