"""Lightweight Pydantic-compatible utilities for request validation."""
from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

__all__ = [
    "BaseModel",
    "Field",
    "ValidationError",
    "constr",
    "validator",
]


_T = TypeVar("_T")


@dataclass
class _StringConstraints:
    strip_whitespace: bool = False
    min_length: Optional[int] = None


@dataclass
class FieldInfo:
    default: Any = ...
    ge: Optional[float] = None
    le: Optional[float] = None
    optional: bool = False
    type: Any = None
    str_constraints: Optional[_StringConstraints] = None

    def copy(self) -> "FieldInfo":
        return FieldInfo(
            default=self.default,
            ge=self.ge,
            le=self.le,
            optional=self.optional,
            type=self.type,
            str_constraints=self.str_constraints,
        )


def Field(default: Any = ..., *, ge: float | None = None, le: float | None = None) -> FieldInfo:
    return FieldInfo(default=default, ge=ge, le=le)


def constr(*, strip_whitespace: bool = False, min_length: int | None = None) -> Type[str]:
    namespace = {
        "strip_whitespace": strip_whitespace,
        "min_length": min_length,
    }
    return type("ConstrainedStr", (str,), namespace)  # type: ignore[type-abstract]


class ValidationError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        message = "; ".join(errors) if errors else "validation error"
        super().__init__(message)
        self._errors = errors

    def errors(self) -> List[str]:  # pragma: no cover - compatibility helper
        return list(self._errors)


def validator(*_fields: str, **_kwargs: Any):  # pragma: no cover - compatibility stub
    def decorator(func: Any) -> Any:
        return func

    return decorator


class _BaseModelMeta(type):
    def __new__(mcls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]) -> "BaseModel":
        cls = super().__new__(mcls, name, bases, dict(namespace))
        annotations: Dict[str, Any] = {}
        for base in reversed(bases):
            annotations.update(getattr(base, "__annotations__", {}))
        annotations.update(namespace.get("__annotations__", {}))

        module = sys.modules.get(cls.__module__)
        globalns = vars(module) if module else {}
        try:
            resolved_annotations = get_type_hints(
                cls,
                globalns=globalns,
                localns=dict(globalns),
                include_extras=True,
            )
        except Exception:  # pragma: no cover - fallback for edge cases
            resolved_annotations = {}

        fields: Dict[str, FieldInfo] = {}
        for base in reversed(bases):
            for key, info in getattr(base, "__fields__", {}).items():
                fields[key] = info.copy()

        for field_name, annotation in annotations.items():
            if field_name == "__fields__":
                continue
            default = getattr(cls, field_name, ...)
            if isinstance(default, FieldInfo):
                field_info = default
                if field_info.default is not ...:
                    setattr(cls, field_name, field_info.default)
                else:
                    if hasattr(cls, field_name):
                        delattr(cls, field_name)
            else:
                field_info = FieldInfo(default=default)

            actual_annotation = resolved_annotations.get(field_name, annotation)
            optional = False
            origin = get_origin(actual_annotation)
            if origin is Union:
                args = [arg for arg in get_args(actual_annotation) if arg is not type(None)]
                if args:
                    actual_annotation = args[0]
                optional = True

            if isinstance(actual_annotation, type) and issubclass(actual_annotation, str):
                constraints = _StringConstraints(
                    strip_whitespace=getattr(actual_annotation, "strip_whitespace", False),
                    min_length=getattr(actual_annotation, "min_length", None),
                )
                field_info.type = str
                field_info.str_constraints = constraints
            else:
                field_info.type = actual_annotation

            field_info.optional = optional or field_info.default is None
            fields[field_name] = field_info

        cls.__fields__ = fields  # type: ignore[attr-defined]
        return cls


class BaseModel(metaclass=_BaseModelMeta):
    __fields__: Dict[str, FieldInfo]

    def __init__(self, **data: Any) -> None:
        values: Dict[str, Any] = {}
        errors: List[str] = []
        for name, info in self.__fields__.items():
            provided = name in data
            value = data.get(name, ...)
            if not provided:
                if info.default is ...:
                    errors.append(f"{name} is required")
                    continue
                value = info.default

            try:
                values[name] = self._validate_field(name, value, info)
            except ValueError as exc:
                errors.append(f"{name}: {exc}")

        if errors:
            raise ValidationError(errors)

        for key, value in values.items():
            setattr(self, key, value)

    @classmethod
    def parse_obj(cls: Type[_T], obj: Dict[str, Any]) -> _T:
        return cls(**obj)

    def dict(self) -> Dict[str, Any]:  # pragma: no cover - helper
        return {name: getattr(self, name) for name in self.__fields__}

    def _validate_field(self, name: str, value: Any, info: FieldInfo) -> Any:
        if value is None:
            if info.optional:
                return None
            raise ValueError("value cannot be null")

        expected_type = info.type
        if isinstance(expected_type, str):
            if expected_type == "int":
                expected_type = int
            elif expected_type == "float":
                expected_type = float
            elif expected_type == "str":
                expected_type = str
        if expected_type is int:
            try:
                coerced = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("value is not a valid integer") from exc
            if info.ge is not None and coerced < info.ge:
                raise ValueError(f"ensure this value is >= {info.ge}")
            if info.le is not None and coerced > info.le:
                raise ValueError(f"ensure this value is <= {info.le}")
            return coerced

        if expected_type is float:
            try:
                coerced = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("value is not a valid float") from exc
            if info.ge is not None and coerced < info.ge:
                raise ValueError(f"ensure this value is >= {info.ge}")
            if info.le is not None and coerced > info.le:
                raise ValueError(f"ensure this value is <= {info.le}")
            return coerced

        if expected_type is str or isinstance(expected_type, type) and issubclass(expected_type, str):
            if not isinstance(value, str):
                value = str(value)
            constraints = info.str_constraints
            if constraints:
                if constraints.strip_whitespace:
                    value = value.strip()
                if constraints.min_length is not None and len(value) < constraints.min_length:
                    raise ValueError(f"ensure this value has at least {constraints.min_length} characters")
            return value

        return value
