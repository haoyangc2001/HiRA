# 独立训练控制台

这是一个与仓库现有 `webui/`、训练代码和产物隔离的 FastAPI + 原生 HTML/CSS/JavaScript 控制台。第一版覆盖配置校验、dry-run 训练控制、日志/指标读取、视频发现、二维轨迹 Canvas 回放和高层导航 Actor 导出计划。

## 目录

```text
training_console/
├── backend/       FastAPI 入口、受控文件服务、解析器、进程管理和适配器
├── frontend/      单页控制台与 Canvas 回放控制器
├── configs/       schema 与默认预设
├── docs/          基线、架构、契约和实现设计
├── exports/       控制台自己的导出目录
└── tests/         固定样例与静态测试
```

## 启动

在已安装 Python 依赖的环境中，从仓库根目录执行：

```text
python -m pip install -r training_console/requirements.txt
python -m training_console.backend
```

后端默认监听 `127.0.0.1:8787`。前端可以由任意静态文件服务器提供 `training_console/frontend/`；开发时直接打开 `index.html` 会进入 mock 模式，展示配置、空资源和二维样例回放，不需要 Isaac Gym。

## 数据来源与限制

- `logs/**/training.log`、checkpoint、视频和轨迹均按只读方式扫描。
- 训练默认是 dry-run；真实子进程启动需要显式开启设置，且只允许控制台自己创建的进程。
- 轨迹只接受 `test_reach_avoid.py` 的 JSON 结构；缺少几何信息时显示 `geometry_unavailable`。
- 导出第一版只针对高层导航 Actor，结果写入 `training_console/exports/`，不覆盖已有文件。
- 静态模式不会自动导入 PyTorch；只有显式设置 `EXPERIMENT_CONSOLE_ENABLE_TORCH_LOAD=1` 才尝试读取 checkpoint 内部元数据。
- 本地没有 Isaac Gym/CUDA 实验环境，因此本交付只进行静态、mock、解析器和 API 契约验证，不运行训练、评估或机器人部署。

详细 API 和边界见 `docs/api-contracts.md`、`docs/backend-design.md` 与 `docs/replay-design.md`。

## 最小操作示例

配置校验请求只包含已允许的 CLI 风格字段：

```json
{
  "task": "go2_high_level",
  "num_envs": 1,
  "seed": 1,
  "max_iterations": 1,
  "rl_device": "cpu",
  "resume": false
}
```

训练控制台先调用 `/api/config/validate`，再以 `dry_run: true` 调用
`/api/train/start`；返回的命令计划只用于预览。真实子进程启动需要显式开启
服务设置，并且只能停止本控制台创建的进程。

轨迹回放使用 `tests/fixtures/trajectory_sample.json` 这种现有采集格式：
`trajectories` 是按时间顺序排列的 XY 点数组。前端支持轨迹选择、播放/暂停、
单步、重置和速度调整；没有几何字段时显示 `geometry_unavailable`。

导出流程是：选择已发现的高层 checkpoint → 创建 `/api/export` 计划 → 查看状态
和 manifest → 从 `/api/export/{id}/download` 下载。导出结果只允许写入
`training_console/exports/`，不会覆盖 `logs/` 中的源文件。

## API 概览

资源读取：`GET /api/runs`、`GET /api/runs/{id}/metrics`、`GET /api/videos`、
`GET /api/trajectories`；训练控制：`POST /api/train/start`、
`GET /api/train/status`、`POST /api/train/stop`、`GET /api/train/logs`；
配置和导出：`POST /api/config/validate`、`POST /api/export`、
`GET /api/export/{id}`、`GET /api/export/{id}/download`。

## 已知限制与后续边界

- 当前版本不提供 Isaac Gym 三维实时画面、远程 GPU 调度、多用户权限或真实机器人部署。
- 轨迹回放不重新运行环境，也不从坐标猜测障碍物、目标和成功状态。
- checkpoint 内部 PyTorch 元数据默认不读取；需要运行时适配时必须显式设置
  `EXPERIMENT_CONSOLE_ENABLE_TORCH_LOAD=1`，并由部署环境自行确认依赖安全。
- 高层导航 Actor 是唯一导出对象，低层 locomotion 模型只作为依赖信息展示。
- 本计划未运行本地 Isaac Gym、CUDA、训练、评估或部署实验；验收证据仅来自静态、mock、固定样例和只读产物解析。
