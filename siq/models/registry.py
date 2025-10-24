"""Registry helper for lightweight export models."""

from __future__ import annotations

from typing import Dict, Iterable

from .detector import DetectorModel
from .pose import PoseModel

MODEL_REGISTRY = {
    DetectorModel.MODEL_ID: DetectorModel,
    PoseModel.MODEL_ID: PoseModel,
}


def create_default_models() -> Dict[str, object]:
    """Instantiate the default detector and pose models."""

    return {model_id: cls() for model_id, cls in MODEL_REGISTRY.items()}


def load_model_from_payload(model_name: str, payload: Dict[str, object]) -> object:
    """Rehydrate a model from serialized payload data."""

    if model_name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model name '{model_name}'")
    model_cls = MODEL_REGISTRY[model_name]
    return model_cls.from_payload(payload)


def available_models() -> Iterable[str]:
    return MODEL_REGISTRY.keys()


__all__ = [
    "MODEL_REGISTRY",
    "create_default_models",
    "load_model_from_payload",
    "available_models",
]
