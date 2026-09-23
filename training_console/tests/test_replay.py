"""Static replay adapter checks; no video decoding or simulator is started."""

from pathlib import Path

import pytest

from training_console.backend.replay import (
    TrajectoryParseError,
    canvas_frame,
    discover_videos,
    parse_trajectory_file,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_trajectory_normalization_preserves_xy_and_reports_geometry_unknown():
    result = parse_trajectory_file(FIXTURES / "trajectory_sample.json")
    assert result["status"] == "ready"
    assert result["geometry_status"] == "geometry_unavailable"
    assert result["trajectories"][0]["bounds"] == {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0}
    frame = canvas_frame(result["trajectories"][0], 1)
    assert frame["point"] == [1.0, 0.0]
    assert frame["progress"] == 0.5


def test_invalid_trajectory_returns_parse_error():
    with pytest.raises(TrajectoryParseError):
        parse_trajectory_file(FIXTURES / "trajectory_invalid.json")


def test_video_discovery_is_extension_limited(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(b"fixture")
    (tmp_path / "notes.txt").write_text("not media", encoding="utf-8")
    result = discover_videos(tmp_path)
    assert len(result) == 1
    assert result[0]["id"] == "clip.mp4"
    assert result[0]["content_type"] == "video/mp4"

