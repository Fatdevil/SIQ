from pathlib import Path
from unittest.mock import Mock

import pytest

from siq.highlights import HighlightContext, HighlightMaker, HighlightRequest


def test_plan_generates_expected_command(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    dest = tmp_path / "highlight.mp4"
    source.write_bytes(b"")
    context = HighlightContext(ball_speed_kph=112.4, label="TOP BINS")
    maker = HighlightMaker(ffmpeg_binary="ffmpeg-test", runner=Mock())
    plan = maker.plan(
        HighlightRequest(
            source=source,
            destination=dest,
            impact_time_s=1.5,
            fps=120,
            context=context,
        )
    )

    command = list(plan["command"])
    assert command[0] == "ffmpeg-test"
    assert "-vf" in command
    assert any("TOP BINS" in part for part in command)
    assert plan["duration"] == pytest.approx(7.0)


def test_make_rejects_invalid_duration(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    dest = tmp_path / "highlight.mp4"
    source.write_bytes(b"")
    maker = HighlightMaker(runner=Mock())
    with pytest.raises(ValueError):
        maker.make(
            HighlightRequest(
                source=source,
                destination=dest,
                impact_time_s=2.0,
                fps=90,
                clip_pre_seconds=1.0,
                clip_post_seconds=1.0,
            )
        )


def test_make_invokes_runner_with_expected_payload(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    dest = tmp_path / "highlight.mp4"
    source.write_bytes(b"")
    executed_commands: list[list[str]] = []

    def fake_runner(cmd, check):
        executed_commands.append(list(cmd))

    context = HighlightContext(ball_speed_kph=128.0)
    maker = HighlightMaker(runner=fake_runner)
    request = HighlightRequest(
        source=source,
        destination=dest,
        impact_time_s=3.0,
        fps=120,
        context=context,
        upload_descriptor={"target": "local"},
    )

    maker.make(request)

    ffmpeg_commands = [cmd for cmd in executed_commands if cmd[0] == "ffmpeg"]
    assert ffmpeg_commands, "ffmpeg command should be executed"
    assert executed_commands[-1][0] == "echo"
    assert executed_commands[-1][1] == '{"target": "local"}'
