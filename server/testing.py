from __future__ import annotations

import asyncio
import inspect
import json as json_module
from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

from fastapi import HTTPException, Request


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

    def post(
        self,
        path: str,
        json: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        data: bytes | str | None = None,
    ) -> Response:
        handler = self._app.routes.get(("POST", path))
        if handler is None:
            return Response(status_code=404, body={"detail": "Not found"})
        raw_body: bytes
        if data is not None:
            raw_body = data if isinstance(data, bytes) else data.encode("utf-8")
        elif json is not None:
            raw_body = json_module.dumps(json).encode("utf-8")
        else:
            raw_body = b""
        payload = json
        if payload is None:
            if raw_body:
                try:
                    maybe_json = json_module.loads(raw_body.decode("utf-8"))
                    payload = maybe_json if isinstance(maybe_json, dict) else {}
                except Exception:  # pragma: no cover - defensive
                    payload = {}
            else:
                payload = {}
        try:
            signature = inspect.signature(handler)
            if "request" in signature.parameters and len(signature.parameters) == 1:
                request = Request(body=raw_body, headers=headers or {})
                result = handler(request)
            else:
                result = handler(payload or {}, headers or {})
            if inspect.iscoroutine(result):
                result = asyncio.run(result)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
            return Response(status_code=exc.status_code, body=detail)
        except Exception as exc:  # pragma: no cover - surfaced in tests
            return Response(status_code=500, body={"detail": str(exc)})
        if isinstance(result, tuple) and len(result) == 2:
            body, status_code = result
            return Response(status_code=status_code, body=body)
        return Response(status_code=200, body=result)


class MiniAPI:
    def __init__(self) -> None:
        self.routes: Dict[Tuple[str, str], Callable[[Dict[str, Any], Dict[str, str]], Any]] = {}

    def post(self, path: str) -> Callable[[Callable[[Dict[str, Any], Dict[str, str]], Any]], Callable[[Dict[str, Any], Dict[str, str]], Any]]:
        def decorator(func: Callable[[Dict[str, Any], Dict[str, str]], Any]) -> Callable[[Dict[str, Any], Dict[str, str]], Any]:
            self.routes[("POST", path)] = func
            return func

        return decorator
