"""Minimal FastAPI-compatible surface for offline testing."""
from __future__ import annotations

import asyncio
import inspect
import json as json_module
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class _Dependency:
    dependency: Callable[[], Any]


def Depends(dependency: Callable[[], Any]) -> _Dependency:
    return _Dependency(dependency=dependency)


@dataclass
class Query:
    default: Any
    enum: Optional[Tuple[str, ...]] = None

class Request:
    def __init__(self, *, body: bytes, headers: Dict[str, Any] | None = None) -> None:
        self._body = body
        self.headers = headers or {}

    async def body(self) -> bytes:
        return self._body

    async def json(self) -> Any:
        if not self._body:
            return {}
        return json_module.loads(self._body.decode("utf-8"))


class FastAPI:
    def __init__(self, *, title: str | None = None) -> None:
        self.title = title
        self.routes: Dict[Tuple[str, str], Callable[..., Any]] = {}
        self.response_models: Dict[Tuple[str, str], Any] = {}
        self.dependency_overrides: Dict[Callable[[], Any], Callable[[], Any]] = {}

    def _add_route(self, method: str, path: str, handler: Callable[..., Any], response_model: Any | None) -> Callable[..., Any]:
        self.routes[(method.upper(), path)] = handler
        if response_model is not None:
            self.response_models[(method.upper(), path)] = response_model
        return handler

    def get(self, path: str, *, response_model: Any | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._add_route("GET", path, func, response_model)

        return decorator

    def post(self, path: str, *, response_model: Any | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._add_route("POST", path, func, response_model)

        return decorator

    def resolve_dependency(self, dependency: _Dependency) -> Any:
        func = self.dependency_overrides.get(dependency.dependency, dependency.dependency)
        return func()

    def call_handler(
        self,
        method: str,
        path: str,
        *,
        json: Dict[str, Any] | None,
        query: Dict[str, Any] | None,
        headers: Dict[str, Any] | None = None,
        raw: bytes | None = None,
    ) -> Any:
        handler = self.routes.get((method.upper(), path))
        if handler is None:
            raise KeyError("route not registered")

        signature = inspect.signature(handler)
        bound_args: Dict[str, Any] = {}

        for name, param in signature.parameters.items():
            if isinstance(param.default, _Dependency):
                bound_args[name] = self.resolve_dependency(param.default)
                continue
            if name == "request":
                bound_args[name] = Request(body=raw or b"", headers=headers or {})
                continue
            if name == "headers":
                bound_args[name] = headers or {}
                continue
            if method.upper() == "GET":
                value = None
                if query and name in query:
                    value = query[name]
                elif isinstance(param.default, Query):
                    value = param.default.default
                elif param.default is not inspect._empty:
                    value = param.default
                bound_args[name] = value
            else:  # POST
                if name == "payload" or name == "submission":
                    bound_args[name] = json or {}
                else:
                    bound_args[name] = json.get(name) if json else None

        result = handler(**bound_args)
        if inspect.iscoroutine(result):  # pragma: no cover - async compatibility
            return asyncio.run(result)
        return result
