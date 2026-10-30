# HiRA: Hierarchical Reach-Avoid Navigation for Quadruped Robots

[Project website](https://haoyangc2001.github.io/HiRA/)

HiRA is a hierarchical quadruped navigation project based on **Reach-Avoid** learning. A high-level policy generates body-frame velocity commands to reach a goal while avoiding unsafe regions; a pretrained low-level locomotion policy executes those commands through joint control.

## Key Ideas

- **Reach-Avoid learning.** Goal and safety functions, `g(s)` and `h(s)`, define the learning targets for navigation rather than a weighted sum of navigation rewards.
- **Policy and value learning.** The current high-level training entry uses a stochastic policy and one Reach-Avoid critic, with a custom multi-step target and PPO updates.
- **Hierarchical closed-loop control.** A robust frozen locomotion policy tracks low-dimensional velocity commands, allowing the high-level navigator to operate in a stable closed-loop action space instead of directly controlling high-dimensional joints.
- **Navigation evaluation.** The repository includes trained checkpoints, training logs, trajectory collection, visualization, and a standalone training console.

## Existing Artifacts

Go2 locomotion checkpoints and exported policies are included, alongside high-level navigation checkpoints and training logs. In the current training script, the logged `cost` is the mean first-arrival step index among successful trajectories; it is not a remaining-budget state or a separate cost critic objective. The website also contains demonstration media. Local availability of these files does not establish that they have been reproduced in the current environment.

## Repository Layout

```text
legged_gym_go2/   Go2 environments and hierarchical navigation implementation
rsl_rl/           Reinforcement learning components
isaacgym/          Isaac Gym dependencies and assets
unitree_rl_gym/    Unitree robot training utilities
webui/             Static project website for GitHub Pages
training_console/  Standalone training configuration, monitoring, replay, and export console
ALGORITHM_DESIGN.md  Algorithm design notes
```

`webui/` is the project website; `training_console/` is the separate local training interface. Algorithm details and source entry points are described in [ALGORITHM_DESIGN.md](ALGORITHM_DESIGN.md).

## Status

This repository uses Isaac Gym and the legged_gym / rsl_rl stack. Training and deployment require a compatible Python, CUDA, simulator, and robot software environment. Renaming the local folder does not migrate the implementation to Isaac Lab or change the trained policies.

In this workspace, HiRA is an independent reference project for [CaMRA](../CaMRA/README.md). The current HiRA training path does not implement CaMRA's budget-conditioned dual-critic learning or execution-data calibration of cost and geometry margins.

## Name and Repository

The project, local folder, and [GitHub repository](https://github.com/haoyangc2001/HiRA) are named **HiRA** (Hierarchical Reach-Avoid). The repository was originally named `Go2HierarchicalReachAvoidRL`; GitHub confirmed its new location during the rename synchronization. This folder retains its own Git history and remote, separate from the parent workspace.

Python package names, task IDs, checkpoint names, and existing training records are retained for compatibility and traceability. Historical materials under `output/copyright_materials/` remain archived under their original terminology.

## Acknowledgements

This project builds on the open-source ecosystems of [legged_gym_go2](https://github.com/littlebearqqq/legged_gym_go2), [rsl_rl](https://github.com/leggedrobotics/rsl_rl), Isaac Gym, and Unitree robot software.

## Citation

Citation information will be added after publication.
