from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from opentelemetry import metrics, trace
from opentelemetry.metrics import Histogram
from opentelemetry.trace import Span


_TRACER = trace.get_tracer("siq.cv")
_METER = metrics.get_meter("siq.cv")

FRAME_INFERENCE_HISTOGRAM: Histogram = _METER.create_histogram(
    "frame_inference_ms",
    unit="ms",
    description="Latency to process one frame through the CV pipeline.",
)


@contextmanager
def cv_stage(name: str) -> Iterator[Span]:
    """Context manager that records a span for a CV processing stage."""
    with _TRACER.start_as_current_span(f"cv.{name}") as span:
        start = perf_counter()
        try:
            yield span
        finally:
            duration_ms = (perf_counter() - start) * 1000.0
            span.set_attribute("cv.stage", name)
            span.set_attribute("cv.stage.duration_ms", duration_ms)


def record_frame_inference(total_duration_ms: float, frame_count: int) -> None:
    """Record per-frame inference latency in milliseconds."""
    normalized_count = max(frame_count, 1)
    per_frame_ms = total_duration_ms / float(normalized_count)
    FRAME_INFERENCE_HISTOGRAM.record(
        per_frame_ms,
        attributes={"cv.frame_count": normalized_count},
    )
