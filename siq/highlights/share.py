"""Share flow orchestration for one-tap highlights."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .maker import HighlightMaker, HighlightRequest


class ShareGateway(Protocol):
    """Surface the share sheet on the client platform."""

    def open(self, *, asset_path: Path, metadata: dict[str, str]) -> None:  # pragma: no cover - protocol
        """Trigger native share sheet with highlight metadata."""


@dataclass
class ShareOrchestrator:
    maker: HighlightMaker
    gateway: ShareGateway

    def share_highlight(self, request: HighlightRequest) -> Path:
        self.maker.make(request)
        self.gateway.open(
            asset_path=request.destination,
            metadata={
                "speed": f"{request.context.ball_speed_kph:.1f} km/h",
                "label": request.context.label,
            },
        )
        return request.destination
