"""Container-testable core for the host-side browser cookie grab workflow.

The host CLI ``install/scripts/grab_cookies.py`` is a thin wrapper around this
module.  The logic lives here (under ``backend/``) so it can be unit-tested
under container pytest, because ``install/scripts/`` is not copied into the
backend Docker image.

Design notes
------------
* This module NEVER imports ``browser_cookie3``.  Callers inject browser loader
  callables (``loader(domain_name=...)``) plus the concrete
  ``browser_cookie3.BrowserCookieError`` type via ``browser_error_types``.  This
  keeps the core importable wherever ``browser_cookie3`` is absent and avoids
  the "cannot ``except`` a MagicMock" trap.
* Output is produced by the shared :func:`convert_browser_cookies`, guaranteeing
  the flat ``{name: value}`` string dict is byte-compatible with the in-container
  module auth chains.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from factories.cookie_utils import convert_browser_cookies, missing_required_cookies

# Browsers attempted, in priority order, when no single browser is requested.
BROWSER_ORDER: tuple[str, ...] = ("firefox", "chrome", "brave", "edge")

# Module -> default domain + cookies required for a usable Tier-1 session +
# the apikeys.json field name (Tier-2) that mirrors the cookies for the frontend.
# ``required`` is only the success gate; the written file keeps ALL cookies
# returned for the domain (so dependent cookies like ct0 are preserved).
MODULE_REQUIRED: dict[str, dict[str, object]] = {
    "linkedin": {
        "domain": "linkedin.com",
        "required": ["li_at", "JSESSIONID"],
        "apikey": "linkedin_cookies",
    },
    "twitter": {
        "domain": "x.com",
        "required": ["auth_token", "ct0"],
        "apikey": "twitter_cookies",
    },
    "tiktok": {
        "domain": "tiktok.com",
        "required": ["msToken"],
        "apikey": "tiktok_cookies",
    },
}

# Exit codes (documented contract).
EXIT_OK = 0
EXIT_NO_REQUIRED_KEYS = 1
EXIT_INVALID_INPUT = 2
EXIT_WRITE_FAILURE = 3

_log = logging.getLogger(__name__)

# Loader factory: given the browser names to try, return {name: loader}.
LoaderFactory = Callable[[Sequence[str]], Mapping[str, Callable[..., object]]]


@dataclass
class BrowserResult:
    """Outcome of attempting one browser.

    ``status`` is one of ``"success"`` (cookies extracted), ``"empty"`` (zero
    cookies for the domain), ``"locked"`` (profile DB locked — browser open), or
    ``"error"`` (keyring/decryption/profile failure).
    """

    name: str
    status: str
    cookies: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def count(self) -> int:
        return len(self.cookies)

    @property
    def valid(self) -> bool:
        """A browser is valid when it produced ALL required cookies."""
        return self.status == "success" and not self.missing


def _flatten_loaded(raw: object) -> dict[str, str]:
    """Normalize a browser loader's return value to a flat ``{name: value}`` dict.

    ``browser_cookie3`` loaders return an ``http.cookiejar.CookieJar`` — an
    iterable of ``Cookie`` objects exposing ``.name``/``.value``.  Cookie-Editor
    style payloads (``list[dict]`` / ``dict``) are routed through the shared
    :func:`convert_browser_cookies` so the grab path and the import path share a
    single flat-format contract.
    """
    if isinstance(raw, list | dict):
        return convert_browser_cookies(raw)
    # CookieJar (or any iterable of Cookie-like objects with .name/.value).
    return {str(cookie.name): str(cookie.value) for cookie in raw}  # type: ignore[union-attr]


def extract_browser_cookies(
    name: str,
    loader: Callable[..., object],
    domain: str,
    required: Iterable[str],
    *,
    browser_error_types: tuple[type[BaseException], ...] = (),
) -> BrowserResult:
    """Run one browser loader and classify the outcome.

    Never raises for the documented failure modes — they are folded into the
    returned :class:`BrowserResult` status.
    """
    required = list(required)
    error_types = (
        ValueError,
        RuntimeError,
        TypeError,
        AttributeError,
        *browser_error_types,
    )
    try:
        raw = loader(domain_name=domain)
        cookies = _flatten_loaded(raw)
    except sqlite3.OperationalError as exc:
        status = "locked" if "database is locked" in str(exc).lower() else "error"
        return BrowserResult(name, status, {}, list(required), detail=str(exc))
    except error_types as exc:
        return BrowserResult(name, "error", {}, list(required), detail=str(exc))

    status = "success" if cookies else "empty"
    missing = missing_required_cookies(cookies, required)
    return BrowserResult(name, status, cookies, missing)


def write_output(path: str, cookies: Mapping[str, str]) -> None:
    """Write the flat cookie dict to ``path`` as pretty JSON.

    Raises ``OSError`` (incl. ``NotADirectoryError``/``PermissionError``) on
    failure so the caller can map it to the write-failure exit code.
    """
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(dict(cookies), handle, indent=2, sort_keys=True)
        handle.write("\n")


def update_apikeys(
    apikey_name: str, cookies: Mapping[str, str], apikeys_path: str | Path
) -> bool:
    """Mirror the flat cookies into the ``apikey_name`` entry of apikeys.json.

    This lets the frontend API Keys editor (Tier-2) reflect cookies provisioned
    by the host grab/import.  The token values land in apikeys.json — which is
    gitignored (never committed) but IS visible/exportable in the UI by design.

    Returns ``True`` on update, ``False`` if apikeys.json is missing (skipped).
    Raises ``OSError``/``ValueError`` only on a corrupt/unwritable file.
    """
    path = Path(apikeys_path)
    if not path.exists():
        _log.warning("apikeys.json not found at %s — skipped apikeys update", path)
        return False
    items = json.loads(path.read_text(encoding="utf-8"))
    value = json.dumps(dict(cookies))
    for item in items:
        if item.get("name") == apikey_name:
            item["key"] = value
            break
    else:
        next_id = max((int(i.get("id", 0)) for i in items), default=0) + 1
        items.append({"id": next_id, "name": apikey_name, "key": value})
    path.write_text(json.dumps(items), encoding="utf-8")
    return True


def _maybe_update_apikeys(
    log: logging.Logger,
    spec: Mapping[str, object],
    cookies: Mapping[str, str],
    apikeys_path: str | Path | None,
) -> None:
    """Best-effort apikeys.json sync; never fails the provisioning run."""
    apikey_name = spec.get("apikey")
    if not (apikeys_path and apikey_name):
        return
    try:
        if update_apikeys(str(apikey_name), cookies, apikeys_path):
            log.info("apikeys.json updated: %s", apikey_name)
    except (OSError, ValueError) as exc:
        log.warning("Could not update apikeys.json (%s): %s", apikey_name, exc)


def _log_browser(log: logging.Logger, result: BrowserResult, domain: str) -> None:
    if result.status == "locked":
        log.info("%s: database is locked — skipped (close the browser)", result.name)
    elif result.status == "error":
        reason = result.detail or "unknown error"
        log.info(
            "%s: could not read cookies — skipped "
            "(browser not installed, profile not found, or keyring locked): %s",
            result.name,
            reason,
        )
    elif result.status == "empty":
        log.info("%s: zero cookies for %s", result.name, domain)
    else:  # success
        missing = f" (missing {result.missing})" if result.missing else ""
        log.info("%s: success: %d cookies%s", result.name, result.count, missing)


def run_grab(
    *,
    module: str,
    domain: str | None,
    browser: str | None,
    out: str,
    loader_factory: LoaderFactory,
    browser_error_types: tuple[type[BaseException], ...] = (),
    apikeys_path: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> int:
    """Grab cookies for ``module`` and write the flat JSON to ``out``.

    When ``apikeys_path`` is given, the cookies are also mirrored into that
    module's apikeys.json field so the frontend reflects them.

    Returns an exit code: ``0`` success, ``1`` no browser produced the required
    keys, ``2`` invalid module/browser, ``3`` write failure.
    """
    log = logger or _log

    spec = MODULE_REQUIRED.get(module)
    if spec is None:
        log.error(
            "Unknown module %r. Supported: %s",
            module,
            ", ".join(sorted(MODULE_REQUIRED)),
        )
        return EXIT_INVALID_INPUT

    required: list[str] = list(spec["required"])  # type: ignore[arg-type]
    domain = domain or str(spec["domain"])

    if browser is not None and browser not in BROWSER_ORDER:
        log.error(
            "Unknown browser %r. Supported: %s",
            browser,
            ", ".join(BROWSER_ORDER),
        )
        return EXIT_INVALID_INPUT

    names = [browser] if browser else list(BROWSER_ORDER)
    loaders = loader_factory(names)

    results: list[BrowserResult] = []
    for name in names:
        loader = loaders.get(name)
        if loader is None:
            results.append(BrowserResult(name, "error", {}, list(required)))
            log.info("%s: unavailable — skipped", name)
            continue
        result = extract_browser_cookies(
            name, loader, domain, required, browser_error_types=browser_error_types
        )
        _log_browser(log, result, domain)
        results.append(result)

    tried = [r.name for r in results]
    valid = [r.name for r in results if r.valid]
    selected = next((r for r in results if r.valid), None)

    if selected is None:
        log.error(
            "Summary: browsers tried=%s, valid=[], required keys missing=%s, "
            "no output written",
            tried,
            required,
        )
        return EXIT_NO_REQUIRED_KEYS

    try:
        write_output(out, selected.cookies)
    except OSError as exc:
        log.error("Failed to write %s: %s", out, exc)
        return EXIT_WRITE_FAILURE

    _maybe_update_apikeys(log, spec, selected.cookies, apikeys_path)

    log.info(
        "Summary: browsers tried=%s, valid=%s, missing required keys=[], output=%s",
        tried,
        valid,
        out,
    )
    return EXIT_OK


def run_import(
    *,
    module: str,
    file: str,
    out: str,
    apikeys_path: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> int:
    """Import a browser-exported cookie file for ``module``.

    Reads ``file`` (Cookie-Editor export or flat dict), converts it to the flat
    ``{name: value}`` format, writes it to ``out`` (Tier-1 file) and — when
    ``apikeys_path`` is given — mirrors it into apikeys.json (Tier-2 / frontend).

    Returns an exit code: ``0`` ok, ``2`` invalid module/file, ``3`` write
    failure.  Missing required keys only warn (import is permissive).
    """
    log = logger or _log

    spec = MODULE_REQUIRED.get(module)
    if spec is None:
        log.error(
            "Unknown module %r. Supported: %s",
            module,
            ", ".join(sorted(MODULE_REQUIRED)),
        )
        return EXIT_INVALID_INPUT

    try:
        raw = json.loads(Path(file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Could not read cookie file %s: %s", file, exc)
        return EXIT_INVALID_INPUT

    try:
        cookies = convert_browser_cookies(raw)
    except ValueError as exc:
        log.error("Invalid cookie format in %s: %s", file, exc)
        return EXIT_INVALID_INPUT

    try:
        write_output(out, cookies)
    except OSError as exc:
        log.error("Failed to write %s: %s", out, exc)
        return EXIT_WRITE_FAILURE

    _maybe_update_apikeys(log, spec, cookies, apikeys_path)

    missing = missing_required_cookies(cookies, list(spec["required"]))  # type: ignore[arg-type]
    if missing:
        log.warning(
            "Imported cookies for %s missing required keys: %s", module, missing
        )
    log.info("Imported cookies for %s -> %s", module, out)
    return EXIT_OK
