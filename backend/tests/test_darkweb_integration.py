"""Live, network-gated integration test for the darkweb module.

This is the test that proves the module ACTUALLY works against the real Tor
network — the unit suite mocks every fetch and (as the engine spike showed) a
fully-green mock suite can still ship a module that returns empty real results.

It is OPT-IN: it only runs when ``RUN_NETWORK_TESTS`` is set, so CI and the
default ``pytest`` run stay fully offline. It requires the ``tor`` service to be
up and routing (``socks5h://tor:9050``).

Run it with::

    docker compose exec -T -e RUN_NETWORK_TESTS=1 backend \
        pytest -v tests/test_darkweb_integration.py
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from modules.darkweb.darkweb_tasks import p_darkweb

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_NETWORK_TESTS"),
    reason="live Tor network test; set RUN_NETWORK_TESTS=1 to enable",
)


@pytest.fixture(autouse=True)
def _no_dev_mode(tmp_path):
    """Make sure no stray golden file masks the real network call."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


def test_darkweb_returns_real_onion_results():
    """A live search must return at least one real .onion hit with a title."""
    result = p_darkweb("elonmusk")

    # Output contract still holds on a live run.
    assert result[0]["module"] == "darkweb"
    assert result[2]["validation"] in {"hard", "no"}

    raw = result[3]["raw"]
    assert isinstance(raw, list)

    onion_hits = [item for item in raw if ".onion" in item.get("link", "")]
    assert onion_hits, (
        "No .onion links returned from a live search — the module is NOT "
        f"working. validation={result[2]['validation']}, raw_len={len(raw)}"
    )
    assert any(item.get("title") for item in onion_hits), "All onion titles empty"

    # Every hit is tagged unfiltered (no filtered tier exists).
    assert all(item["filtered"] is False for item in raw)
