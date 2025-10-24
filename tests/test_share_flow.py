from pathlib import Path
from typing import List

from siq.highlights import HighlightContext, HighlightMaker, HighlightRequest, ShareGateway, ShareOrchestrator


class FakeGateway(ShareGateway):
    def __init__(self) -> None:
        self.calls: List[dict[str, str]] = []

    def open(self, *, asset_path: Path, metadata: dict[str, str]) -> None:
        self.calls.append({"asset": str(asset_path), **metadata})


class RecordingMaker(HighlightMaker):
    def __init__(self) -> None:
        super().__init__(runner=lambda *args, **kwargs: None)
        self.requests: List[HighlightRequest] = []

    def make(self, request: HighlightRequest) -> None:  # type: ignore[override]
        self.requests.append(request)


def test_share_orchestrator_invokes_maker_and_gateway(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp4"
    dest = tmp_path / "highlight.mp4"
    source.write_bytes(b"")
    context = HighlightContext(ball_speed_kph=102.3, label="TOP BINS")

    maker = RecordingMaker()
    gateway = FakeGateway()
    orchestrator = ShareOrchestrator(maker=maker, gateway=gateway)
    request = HighlightRequest(
        source=source,
        destination=dest,
        impact_time_s=1.2,
        fps=120,
        context=context,
    )

    result_path = orchestrator.share_highlight(request)

    assert maker.requests[-1].destination == dest
    assert gateway.calls[-1]["asset"] == str(dest)
    assert gateway.calls[-1]["speed"] == "102.3 km/h"
    assert result_path == dest
