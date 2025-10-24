from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from time import perf_counter
from typing import Dict, List, Optional


@dataclass
class Span:
    name: str
    parent: Optional["Span"] = None
    attributes: Dict[str, object] = field(default_factory=dict)
    start_time: float = field(default_factory=perf_counter)
    end_time: Optional[float] = None

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value

    def end(self) -> None:
        if self.end_time is None:
            self.end_time = perf_counter()

    def __enter__(self) -> "Span":
        _push_span(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.end()
        _pop_span(self)


class Tracer:
    def __init__(self, instrumentation_scope: str) -> None:
        self._scope = instrumentation_scope

    @contextmanager
    def start_as_current_span(self, name: str) -> Span:
        span = Span(name=name, parent=current_span())
        with span:
            try:
                yield span
            finally:
                span.end()


class TracerProvider:
    def __init__(self) -> None:
        self._lock = RLock()
        self._tracers: Dict[str, Tracer] = {}

    def get_tracer(self, name: str) -> Tracer:
        with self._lock:
            if name not in self._tracers:
                self._tracers[name] = Tracer(name)
            return self._tracers[name]


_global_tracer_provider = TracerProvider()
_finished_spans: List[Span] = []
_current_span_stack: List[Span] = []


def set_tracer_provider(provider: TracerProvider) -> None:
    global _global_tracer_provider
    _global_tracer_provider = provider


def get_tracer_provider() -> TracerProvider:
    return _global_tracer_provider


def get_tracer(name: str) -> Tracer:
    return _global_tracer_provider.get_tracer(name)


def _push_span(span: Span) -> None:
    _current_span_stack.append(span)


def _pop_span(span: Span) -> None:
    if _current_span_stack and _current_span_stack[-1] is span:
        _current_span_stack.pop()
    _finished_spans.append(span)


def current_span() -> Optional[Span]:
    return _current_span_stack[-1] if _current_span_stack else None


def get_finished_spans() -> List[Span]:
    return list(_finished_spans)


def reset() -> None:
    _finished_spans.clear()
    _current_span_stack.clear()
