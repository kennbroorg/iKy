"""Shared cookie conversion helpers for OSINT modules.

This module consolidates the previously-duplicated per-module converters
(``linkedin_tasks._convert_browser_cookies``,
``twitter_tasks._convert_browser_cookies``,
``tiktok_tasks._convert_tiktok_cookies``) into one place so the in-container
auth chains and the host-side ``grab_cookies.py`` script produce a single,
byte-compatible flat-format cookie dict.

Pure standard library only — safe to import from the host script by adding
``<repo>/backend`` to ``sys.path``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def convert_browser_cookies(raw: list[dict] | dict) -> dict[str, str]:
    """Convert a browser cookie export to a flat ``{name: value}`` dict.

    Browser extensions (Cookie-Editor, EditThisCookie) export cookies as a
    list of objects with ``name``/``value`` keys.  Module auth chains expect a
    flat ``{cookie_name: cookie_value}`` mapping where every key and value is a
    string.  An already-flat dict is passed through with string coercion.

    Parameters
    ----------
    raw:
        Either a list of cookie objects (browser export) or a flat dict.

    Returns
    -------
    dict[str, str]
        Flat mapping with string keys and string values.

    Raises
    ------
    ValueError
        If ``raw`` is neither a list nor a dict.
    """
    if isinstance(raw, dict):
        # Already in flat format — pass through with string coercion.
        return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, list):
        result: dict[str, str] = {}
        for item in raw:
            name = item.get("name") or item.get("Name")
            value = item.get("value") or item.get("Value") or ""
            if name:
                result[str(name)] = str(value)
        return result
    raise ValueError(
        f"Unexpected cookie format: {type(raw).__name__}. "
        "Expected list (browser export) or dict (flat format)."
    )


def missing_required_cookies(
    cookies: Mapping[str, str], required: Iterable[str]
) -> list[str]:
    """Return the required cookie keys that are absent or empty.

    A key counts as missing when it is not present in ``cookies`` or maps to a
    falsy value (e.g. an empty string).  The returned list preserves the order
    in which keys appear in ``required``.

    Parameters
    ----------
    cookies:
        Flat cookie mapping (typically from :func:`convert_browser_cookies`).
    required:
        Cookie names that must be present with non-empty values.

    Returns
    -------
    list[str]
        Missing/empty required keys, in ``required`` order.  Empty when all
        required keys are present and non-empty.
    """
    return [key for key in required if not cookies.get(key)]
