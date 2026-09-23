# Replay Adapter Design

## Video resources

`discover_videos(root)` scans only the configured read-only media root and
returns relative IDs, MIME types and file sizes for `.mp4`, `.webm` and `.ogg`.
The API serves those IDs through a controlled static-file route; the browser
never submits an arbitrary filesystem path.

## Canvas data flow

`parse_trajectory_file` accepts only the JSON object emitted by
`test_reach_avoid.py`. It normalizes every XY point to finite numbers, computes
per-trajectory bounds, and emits `geometry_unavailable` when the file has no
explicit geometry. The browser must not infer obstacle or goal geometry.

The native `TrajectoryCanvas` controller supports play, pause, reset, single
step, speed selection and trajectory selection. It derives a stable fit-to-view
scale from the selected points, draws the visible path and highlights the
current point. Empty and malformed data are represented by explicit states in
the API layer.

## Static verification

The fixtures cover a valid collector payload, malformed coordinates and a media
extension allow-list. No video decoder, Isaac Gym process or training process
is required.

