from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from server.models import Entitlement

DEFAULT_PATH = Path(os.environ.get("ENTITLEMENTS_STORE_PATH", "data/entitlements.json"))


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_raw(path: Path) -> Dict[str, List[dict]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                return {key: value if isinstance(value, list) else [] for key, value in data.items()}
    except json.JSONDecodeError:
        pass
    return {}


def _save_raw(payload: Dict[str, List[dict]], path: Path) -> None:
    _ensure_parent(path)
    fd, tmp_name = tempfile.mkstemp(prefix="entitlements_", suffix=".json", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


class EntitlementStore:
    """File-backed store for entitlement records."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_PATH

    @property
    def path(self) -> Path:
        return self._path

    def list_for_user(self, user_id: str) -> List[Entitlement]:
        raw = _load_raw(self._path)
        entries = raw.get(user_id, [])
        return [Entitlement.from_dict(item) for item in entries]

    def upsert(self, entitlement: Entitlement) -> Entitlement:
        raw = _load_raw(self._path)
        entries = raw.setdefault(entitlement.user_id, [])
        updated = entitlement
        for idx, item in enumerate(entries):
            if item.get("productId") == entitlement.product_id:
                existing = Entitlement.from_dict(item)
                updated = existing.update(
                    status=entitlement.status,
                    source=entitlement.source,
                    expires_at=entitlement.expires_at,
                    last_verified_at=entitlement.last_verified_at,
                    revoked_at=entitlement.revoked_at,
                    source_status=entitlement.source_status,
                    meta=entitlement.meta,
                )
                entries[idx] = updated.to_dict()
                break
        else:
            entries.append(entitlement.to_dict())
        raw[entitlement.user_id] = entries
        _save_raw(raw, self._path)
        return updated

    def grant(
        self,
        *,
        user_id: str,
        product_id: str,
        status: str,
        source: str,
        expires_at: str | None,
        last_verified_at: str | None = None,
        revoked_at: str | None = None,
        source_status: str | None = None,
        meta: Mapping[str, Any] | None = None,
    ) -> Entitlement:
        normalized = product_id.lower()
        entitlement = Entitlement.new(
            user_id=user_id,
            product_id=normalized,
            status=status,  # type: ignore[arg-type]
            source=source,  # type: ignore[arg-type]
            expires_at=expires_at,
            last_verified_at=last_verified_at,
            revoked_at=revoked_at,
            source_status=source_status,
            meta=meta,
        )
        return self.upsert(entitlement)

    def get(self, user_id: str, product_id: str) -> Optional[Entitlement]:
        raw = _load_raw(self._path)
        for item in raw.get(user_id, []):
            if item.get("productId") == product_id:
                return Entitlement.from_dict(item)
        return None

    def has_active(self, user_id: str, product_id: str) -> bool:
        entitlement = self.get(user_id, product_id)
        return entitlement is not None and entitlement.status == "active"

    def iter_all(self) -> Iterable[Entitlement]:  # pragma: no cover - not used in tests
        raw = _load_raw(self._path)
        for entries in raw.values():
            for item in entries:
                yield Entitlement.from_dict(item)
