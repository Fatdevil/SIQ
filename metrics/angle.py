from __future__ import annotations

import math
from typing import Sequence, Tuple

Point = Tuple[int, float, float]


def side_angle_deg(points: Sequence[Point]) -> float:
    if len(points) < 2:
        return 0.0
    start = points[0]
    end = points[-1]
    dx = end[1] - start[1]
    dy = end[2] - start[2]
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dy, dx))
