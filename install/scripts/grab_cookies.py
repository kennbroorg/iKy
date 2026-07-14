#!/usr/bin/env python3
"""Host-side browser cookie grabber for iKy OSINT modules.

This script runs on the HOST (never inside the container): it reads cookies
from your local browser profiles via ``browser_cookie3`` and writes a flat
``{name: value}`` JSON file into ``backend/cookies/``, which is bind-mounted
into the backend container at ``/app/cookies``.

The decision / validation / logging logic lives in
``backend/factories/cookie_grab.py`` so it can be unit-tested under container
pytest (this file is not present in the backend image).  This wrapper only
wires ``argparse`` and the real ``browser_cookie3`` dependency to the core.

Examples
--------
    just cookies-grab linkedin linkedin.com
    just cookies-grab linkedin linkedin.com firefox

    # Or directly:
    .venv/bin/python install/scripts/grab_cookies.py \
        --module linkedin --domain linkedin.com \
        --out backend/cookies/linkedin_cookies.json [--browser firefox]
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# Make ``backend/`` importable so we reuse the shared converter + grab core
# instead of duplicating the flat-format contract.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from factories.cookie_grab import (  # noqa: E402
    BROWSER_ORDER,
    EXIT_INVALID_INPUT,
    MODULE_REQUIRED,
    run_grab,
    run_import,
)

# apikeys.json (Tier-2 / frontend store) lives next to the backend factories.
_APIKEYS_PATH = _REPO_ROOT / "backend" / "factories" / "apikeys.json"


def _build_loader_factory(
    browser_cookie3: object,
) -> Callable[[Sequence[str]], dict[str, Callable[..., object]]]:
    """Map browser names to ``browser_cookie3.<browser>`` callables."""

    def _factory(names: Sequence[str]) -> dict[str, Callable[..., object]]:
        return {name: getattr(browser_cookie3, name) for name in names}

    return _factory


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="grab_cookies.py",
        description="Extract local browser cookies into a flat iKy cookie file.",
    )
    parser.add_argument(
        "--module",
        required=True,
        choices=sorted(MODULE_REQUIRED),
        help="Target iKy module (defines required cookie keys + default domain).",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="Cookie domain to filter on (defaults to the module's domain).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Destination JSON path (e.g. backend/cookies/linkedin_cookies.json).",
    )
    parser.add_argument(
        "--browser",
        default=None,
        choices=BROWSER_ORDER,
        help="Only attempt this browser (default: try all in order).",
    )
    parser.add_argument(
        "--import-file",
        default=None,
        help=(
            "Import cookies from this Cookie-Editor JSON file instead of "
            "grabbing from local browsers."
        ),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    # Import mode: no browser access needed, so browser_cookie3 is not imported.
    if args.import_file:
        return run_import(
            module=args.module,
            file=args.import_file,
            out=args.out,
            apikeys_path=_APIKEYS_PATH,
        )

    try:
        import browser_cookie3
    except ImportError:
        logging.error(
            "browser_cookie3 is not installed. Install it with: just cookies-setup"
        )
        return EXIT_INVALID_INPUT

    return run_grab(
        module=args.module,
        domain=args.domain,
        browser=args.browser,
        out=args.out,
        loader_factory=_build_loader_factory(browser_cookie3),
        browser_error_types=(browser_cookie3.BrowserCookieError,),
        apikeys_path=_APIKEYS_PATH,
    )


if __name__ == "__main__":
    raise SystemExit(main())
