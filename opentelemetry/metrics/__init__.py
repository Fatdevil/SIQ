from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Dict, List, Optional


@dataclass
class Histogram:
    name: str
    unit: Optional[str] = None
    description: Optional[str] = None
    records: List[tuple[float, Dict[str, object]]] = field(default_factory=list)

    def record(self, value: float, attributes: Optional[Dict[str, object]] = None) -> None:
        attrs = dict(attributes or {})
        self.records.append((value, attrs))

    def reset(self) -> None:
        self.records.clear()


class Meter:
    def __init__(self, name: str) -> None:
        self._name = name
        self._histograms: Dict[str, Histogram] = {}

    def create_histogram(self, name: str, unit: Optional[str] = None, description: Optional[str] = None) -> Histogram:
        histogram = Histogram(name=name, unit=unit, description=description)
        self._histograms[name] = histogram
        return histogram

    def get_histogram(self, name: str) -> Optional[Histogram]:
        return self._histograms.get(name)


class MeterProvider:
    def __init__(self) -> None:
        self._lock = RLock()
        self._meters: Dict[str, Meter] = {}

    def get_meter(self, name: str) -> Meter:
        with self._lock:
            if name not in self._meters:
                self._meters[name] = Meter(name)
            return self._meters[name]


_global_meter_provider = MeterProvider()


def set_meter_provider(provider: MeterProvider) -> None:
    global _global_meter_provider
    _global_meter_provider = provider


def get_meter_provider() -> MeterProvider:
    return _global_meter_provider


def get_meter(name: str) -> Meter:
    return _global_meter_provider.get_meter(name)
