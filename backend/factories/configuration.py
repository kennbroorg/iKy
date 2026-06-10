import json
from pathlib import Path
from typing import Any

_FACTORIES_DIR = Path(__file__).resolve().parent


def _api_keys_path() -> Path:
    """Return the absolute path to apikeys.json."""
    return _FACTORIES_DIR / "apikeys.json"


def api_keys_read() -> list[dict[str, Any]]:
    with _api_keys_path().open() as f:
        return json.load(f)


def api_keys_write(
    api_keys: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    with _api_keys_path().open("w") as f:
        json.dump(api_keys, f)
    return api_keys


def api_keys_search(api_name: str) -> str | bool:
    with _api_keys_path().open() as f:
        items = json.load(f)
    for item in items:
        if item["name"] == api_name:
            return item["key"]
    return False
