"""Utilities for assembling short highlight reels using ffmpeg."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class HighlightContext:
    """Metadata to decorate the rendered highlight."""

    ball_speed_kph: float
    label: str = "TOP BINS"
    music_track: Optional[Path] = None
    overlay_color: str = "white"

    def overlay_lines(self) -> List[str]:
        speed_line = f"{self.ball_speed_kph:.1f} KM/H"
        return [speed_line, self.label]


@dataclass(frozen=True)
class HighlightRequest:
    """Describe the input/output requirements for highlight rendering."""

    source: Path
    destination: Path
    impact_time_s: float
    fps: float
    context: HighlightContext = field(default_factory=lambda: HighlightContext(ball_speed_kph=0.0))
    clip_pre_seconds: float = 3.0
    clip_post_seconds: float = 4.0
    vertical_resolution: tuple[int, int] = (1080, 1920)
    upload_descriptor: Optional[Mapping[str, str]] = None

    @property
    def clip_length(self) -> float:
        return self.clip_pre_seconds + self.clip_post_seconds


class HighlightMaker:
    """Construct ffmpeg commands to generate highlight clips."""

    def __init__(self, *, ffmpeg_binary: str = "ffmpeg", runner=subprocess.run) -> None:
        self._ffmpeg = ffmpeg_binary
        self._runner = runner

    def _build_filter_graph(self, request: HighlightRequest) -> str:
        width, height = request.vertical_resolution
        overlay_lines = request.context.overlay_lines()
        text_lines = "\\n".join(overlay_lines)
        drawtext = (
            f"drawtext=fontcolor={request.context.overlay_color}:fontsize=72:"
            "font=Arial:text='" + text_lines.replace("'", "\\'" ) + "':"
            "x=(w-text_w)/2:y=h-200"
        )
        filters: List[str] = [
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        ]
        filters.append(drawtext)
        return ",".join(filters)

    def _build_command(self, request: HighlightRequest, start_time: float) -> List[str]:
        cmd = [
            self._ffmpeg,
            "-y",
            "-ss",
            f"{start_time:.3f}",
            "-i",
            str(request.source),
            "-t",
            f"{request.clip_length:.3f}",
            "-vf",
            self._build_filter_graph(request),
        ]
        if request.context.music_track:
            cmd.extend([
                "-i",
                str(request.context.music_track),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
            ])
        else:
            cmd.extend(["-an", "-c:v", "libx264"])
        cmd.append(str(request.destination))
        return cmd

    def _notify_upload(self, request: HighlightRequest) -> None:
        if not request.upload_descriptor:
            return
        descriptor_json = json.dumps(dict(request.upload_descriptor))
        self._runner(
            ["echo", descriptor_json],
            check=True,
        )

    def make(self, request: HighlightRequest) -> None:
        if request.clip_length < 6 or request.clip_length > 8:
            raise ValueError("highlight clip must be between 6 and 8 seconds")

        start_time = max(request.impact_time_s - request.clip_pre_seconds, 0.0)
        command = self._build_command(request, start_time)
        self._runner(command, check=True)
        self._notify_upload(request)

    # Exposed for tests
    def plan(self, request: HighlightRequest) -> Mapping[str, Iterable[str] | float]:
        start_time = max(request.impact_time_s - request.clip_pre_seconds, 0.0)
        return {
            "command": self._build_command(request, start_time),
            "start_time": start_time,
            "duration": request.clip_length,
        }
