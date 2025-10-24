"""Core SIQ package containing lightweight model definitions for export utilities."""

from .models.detector import DetectorModel
from .models.pose import PoseModel

__all__ = ["DetectorModel", "PoseModel"]
