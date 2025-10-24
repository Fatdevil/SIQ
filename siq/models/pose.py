"""Lightweight pose model implemented without third-party dependencies."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence


class PoseModel:
    MODEL_ID = "pose"

    def __init__(
        self,
        weight: Sequence[Sequence[float]] | None = None,
        bias: Sequence[float] | None = None,
        joints: int = 8,
    ) -> None:
        self.joints = joints
        rng = random.Random(4321)
        if weight is None:
            weight = [[rng.gauss(0.0, 0.05) for _ in range(3)] for _ in range(joints * 2)]
        if bias is None:
            bias = [rng.gauss(0.0, 0.02) for _ in range(joints * 2)]
        self.weight = [[float(v) for v in row] for row in weight]
        self.bias = [float(v) for v in bias]

    def forward(self, tensor: List[List[List[List[float]]]]) -> Dict[str, List[List[List[float]]] | List[List[float]]]:
        features = [self._mean_channels(example) for example in tensor]
        flat_coords = [self._apply_linear(feature) for feature in features]
        keypoints = [self._reshape(coords) for coords in flat_coords]
        visibility = [[self._sigmoid(point[0]) for point in person] for person in keypoints]
        return {"keypoints": keypoints, "visibility": visibility}

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
            output.append(sum(f * w for f, w in zip(feature, row)) + bias)
        return output

    def _reshape(self, coords: List[float]) -> List[List[float]]:
        reshaped = []
        for index in range(0, len(coords), 2):
            reshaped.append([coords[index], coords[index + 1]])
        return reshaped

    def _sigmoid(self, value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def to_payload(self) -> Dict[str, object]:
        return {
            "model_id": self.MODEL_ID,
            "joints": self.joints,
            "weight": self.weight,
            "bias": self.bias,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, object]) -> "PoseModel":
        return cls(weight=payload["weight"], bias=payload["bias"], joints=int(payload["joints"]))


__all__ = ["PoseModel"]
