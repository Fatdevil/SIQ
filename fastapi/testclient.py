"""Test client compatible with the simplified FastAPI implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - fallback when server.testing exists
    from server.testing import TestClient as MiniTestClient
except ModuleNotFoundError:  # pragma: no cover
    MiniTestClient = None  # type: ignore

from . import FastAPI, HTTPException


@dataclass
class Response:
    status_code: int
    body: Any

    def json(self) -> Any:
        return self.body


class TestClient:
    __test__ = False

    def __init__(self, app: FastAPI) -> None:
        self._app = app
        self._delegate = None
        if not hasattr(app, "call_handler") and MiniTestClient is not None:
            self._delegate = MiniTestClient(app)

    def __enter__(self) -> "TestClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None) -> Response:
        if self._delegate is not None:
            return self._delegate.get(path, params=params, headers=headers)
        try:
            body = self._app.call_handler("GET", path, json=None, query=params or {})
        except HTTPException as exc:
            return Response(status_code=exc.status_code, body={"detail": exc.detail})
        except KeyError:
            return Response(status_code=404, body={"detail": "Not found"})
        return Response(status_code=200, body=body)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Response:
        if self._delegate is not None:
            return self._delegate.post(path, json=json, headers=headers)
        try:
            body = self._app.call_handler("POST", path, json=json or {}, query=None)
        except HTTPException as exc:
            return Response(status_code=exc.status_code, body={"detail": exc.detail})
        except KeyError:
            return Response(status_code=404, body={"detail": "Not found"})
        return Response(status_code=200, body=body)
