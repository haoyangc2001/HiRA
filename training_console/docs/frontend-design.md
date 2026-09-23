# Frontend Information Architecture

The console is a single page with three product areas. It uses native browser APIs and does not reuse the existing `webui/` markup or styles.

## Navigation

```text
实验控制台
├── 训练 Training
│   ├── run selector and status
│   ├── configuration form
│   ├── metric cards and charts
│   └── live log tail
├── 回放 Replay
│   ├── video selector and player
│   ├── trajectory selector
│   └── 2D canvas timeline
└── 导出 Export
    ├── checkpoint selector
    ├── export status
    └── download result
```

## Visual States

| Component | Empty | Loading | Success | Failure |
| --- | --- | --- | --- | --- |
| Run list | “暂无实验” and refresh action | skeleton rows | selectable run rows | resource error with retry |
| Training status | idle and start action | starting/running badge | completed badge and final metrics | failed badge with categorized message |
| Config form | safe preset defaults | submit disabled | saved preset confirmation | field-level validation |
| Metrics | no data panel | chart placeholder | line charts and summary cards | parser error with source path |
| Video | no video panel | metadata loading | native video controls | unsupported/missing media message |
| Canvas | no trajectory panel | loading timeline | animated path and legend | malformed JSON message |
| Export | checkpoint selector | exporting progress | download action | incompatible checkpoint message |

## Layout

- Desktop: fixed narrow navigation rail, flexible main content, two-column metric/replay panels.
- Mobile: navigation becomes horizontal tabs; panels become one column; controls remain at least 44px tall.
- Status colors are semantic: teal for safe/running/success, amber for warnings, red for failure/unsafe, neutral gray for idle.
- The interface uses compact operational typography and avoids marketing hero sections or decorative cards inside cards.

## Interaction Rules

- Training polling starts only after a run is selected or started and stops when the process reaches a terminal state.
- Start, stop, export, save, and delete actions require an explicit busy state and must be idempotent from the browser's perspective.
- Canvas playback supports play/pause, step forward/back, reset, speed selection, and trajectory selection.
- All async errors are rendered in the same alert region and include a retry action when retry is safe.
- The UI never displays a raw server filesystem path as an executable action; it shows a short label and optional diagnostic path.
