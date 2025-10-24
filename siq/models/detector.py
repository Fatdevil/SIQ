"""Lightweight detector model implemented with pure Python math."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass
class DetectorOutputs:
    boxes: List[List[float]]
    scores: List[float]


class DetectorModel:
    MODEL_ID = "detector"

    def __init__(self, weight: Sequence[Sequence[float]] | None = None, bias: Sequence[float] | None = None) -> None:
        rng = random.Random(1234)
        if weight is None:
            weight = [[rng.gauss(0.0, 0.1) for _ in range(3)] for _ in range(4)]
        if bias is None:
            bias = [rng.gauss(0.0, 0.05) for _ in range(4)]
        self.weight = [[float(v) for v in row] for row in weight]
        self.bias = [float(v) for v in bias]

    def forward(self, tensor: List[List[List[List[float]]]]) -> Dict[str, List[List[float]] | List[float]]:
        if len(tensor) == 0:
            raise ValueError("DetectorModel expects a non-empty batch")
        features = [self._mean_channels(example) for example in tensor]
        logits = [self._apply_linear(feature) for feature in features]
        boxes = [self._to_boxes(vec) for vec in logits]
        scores = [self._sigmoid(vec[0]) for vec in logits]
        return {"boxes": boxes, "scores": scores}

    def _mean_channels(self, example: List[List[List[float]]]) -> List[float]:
        height = len(example)
        width = len(example[0]) if height > 0 else 0
        channels = len(example[0][0]) if width > 0 else 0
        totals = [0.0 for _ in range(channels)]
        count = max(height * width, 1)
        for row in example:
            for pixel in row:
                for c, value in enumerate(pixel):
                    totals[c] += value
        return [total / count for total in totals]

    def _apply_linear(self, feature: List[float]) -> List[float]:
        output = []
        for row, bias in zip(self.weight, self.bias):
            value = sum(f * w for f, w in zip(feature, row)) + bias
            output.append(value)
        return output

    def _to_boxes(self, vector: List[float]) -> List[float]:
        return [min(max(value, 0.0), 1.0) for value in vector]

    def _sigmoid(self, value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def to_payload(self) -> Dict[str, object]:
        return {
            "model_id": self.MODEL_ID,
            "weight": self.weight,
            "bias": self.bias,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "DetectorModel":
        weight = payload["weight"]
        bias = payload["bias"]
        return cls(weight=weight, bias=bias)


__all__ = ["DetectorModel", "DetectorOutputs"]
