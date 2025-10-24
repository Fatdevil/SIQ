import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

DEFAULT_PATH = Path(os.environ.get("BILLING_STORE_PATH", "data/users.json"))


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_store(path: Path = DEFAULT_PATH) -> Dict[str, dict]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return {}


def save_store(store: Dict[str, dict], path: Path = DEFAULT_PATH) -> None:
    _ensure_parent(path)
    fd, tmp_name = tempfile.mkstemp(prefix="users_", suffix=".json", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def get_user(user_id: str, path: Path = DEFAULT_PATH) -> Optional[dict]:
    if not user_id:
        return None
    store = load_store(path)
    return store.get(user_id)


def set_tier(
    user_id: str,
    tier: str,
    expires_at: Optional[str],
    provider: str = "mock",
    path: Path = DEFAULT_PATH,
) -> dict:
    record = {
        "userId": user_id,
        "tier": tier,
        "expiresAt": expires_at,
        "provider": provider,
    }
    store = load_store(path)
    store[user_id] = record
    save_store(store, path)
    return record
