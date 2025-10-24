from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple


@dataclass
class Response:
    status_code: int
    body: Any

    def json(self) -> Any:
        return self.body

    @property
    def text(self) -> str:
        return str(self.body)


class TestClient:
    __test__ = False

    def __init__(self, app: "MiniAPI") -> None:
        self._app = app

    def post(self, path: str, json: Dict[str, Any], headers: Dict[str, str] | None = None) -> Response:
        handler = self._app.routes.get(("POST", path))
        if handler is None:
            return Response(status_code=404, body={"detail": "Not found"})
        try:
            payload = handler(json, headers or {})
        except Exception as exc:  # pragma: no cover - surfaced in tests
            return Response(status_code=500, body={"detail": str(exc)})
        return Response(status_code=200, body=payload)


class MiniAPI:
    def __init__(self) -> None:
        self.routes: Dict[Tuple[str, str], Callable[[Dict[str, Any], Dict[str, str]], Any]] = {}

    def post(self, path: str) -> Callable[[Callable[[Dict[str, Any], Dict[str, str]], Any]], Callable[[Dict[str, Any], Dict[str, str]], Any]]:
        def decorator(func: Callable[[Dict[str, Any], Dict[str, str]], Any]) -> Callable[[Dict[str, Any], Dict[str, str]], Any]:
            self.routes[("POST", path)] = func
            return func

        return decorator
