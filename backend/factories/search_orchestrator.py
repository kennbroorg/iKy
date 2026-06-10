"""Search orchestrator — runs providers and aggregates results.

Also exports ``post_process_results``, a shared helper that encapsulates
the social-refinement + output-assembly logic that is otherwise identical
in search_tasks.py and dorks_tasks.py.
"""

from __future__ import annotations

import logging

from factories.fontcheat import search_icon_5
from factories.iKy_functions import name_match
from factories.search_providers import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Runs multiple search providers and aggregates results.

    NOTE: Sequential execution for now.  Phase 3 could add async
    parallelism via asyncio/ThreadPoolExecutor.  Failed providers return
    empty lists — no exceptions propagate to callers.
    """

    def __init__(self, providers: list[SearchProvider]) -> None:
        self.providers = providers

    def search_all(
        self, query: str, max_results: int = 10
    ) -> dict[str, list[SearchResult]]:
        """Run all providers sequentially.

        Returns
        -------
        dict[provider_name, list[SearchResult]]
            Keys are provider names; value is an empty list when the
            provider failed or returned no results.
        """
        results: dict[str, list[SearchResult]] = {}
        for provider in self.providers:
            try:
                results[provider.name] = provider.search(query, max_results)
            except Exception:
                logger.warning("Provider %s failed", provider.name, exc_info=True)
                results[provider.name] = []
        return results

    def failed_providers(self, results: dict[str, list[SearchResult]]) -> list[str]:
        """Return list of provider names that returned empty results."""
        return [name for name, res in results.items() if not res]


# ---------------------------------------------------------------------------
# Shared post-processing helper
# ---------------------------------------------------------------------------


def post_process_results(
    output: dict,
    name_tokens: list[str],
) -> tuple[
    list[dict],  # social_raw
    list[dict],  # socialp
    list[str],  # username_refined
    str,  # name_complete
    list[dict],  # tasks
    list[dict],  # name_cloud  (built from output["names"])
    list[dict],  # username_cloud  (built from output["usernames"])
]:
    """Shared social-refinement and output-assembly logic.

    Both ``search_tasks.p_search`` and ``dorks_tasks.p_dorks`` perform
    identical post-processing after their respective analysis passes.
    This function centralises that logic so there is a single source of
    truth.

    Parameters
    ----------
    output:
        The ``output`` dict accumulated by ``simple_analysis`` /
        ``deep_analysis`` calls.
    name_tokens:
        The tokenised best-match name list produced by the caller after
        running ``thefuzz.process.extractBests``.

    Returns
    -------
    A 7-tuple:
        social_raw, socialp, username_refined, name_complete,
        tasks, name_cloud, username_cloud
    """
    # ------------------------------------------------------------------ #
    # Collect raw names / usernames from the output dict                   #
    # ------------------------------------------------------------------ #
    try:
        users = [item["usernames"].strip() for item in output["usernames"]]
    except Exception:
        users = []

    try:
        names = [item["name"].strip() for item in output["names"]]
    except Exception:
        names = []

    name_complete = " ".join(name_tokens)

    # ------------------------------------------------------------------ #
    # Build social graph (raw pass — all hits)                             #
    # ------------------------------------------------------------------ #
    social = sorted(output.get("social", []), key=lambda k: k["rrss"])
    social_count: dict[str, int] = {}
    social_raw: list[dict] = [
        {
            "name-node": "Social",
            "title": "Social",
            "subtitle": "",
            "icon": search_icon_5("child"),
            "link": "Social",
        }
    ]
    nounce = ""
    prev = ""
    for title_count, s in enumerate(social):
        key = s["rrss"] + "-|-" + s["user"] + "-|-" + s["name"]
        social_count[key] = social_count.get(key, 0) + 1
        social_item = {
            "name-node": "Social" + s["rrss"] + str(title_count),
            "title": s["rrss"] + " (" + s["source"] + ")" + nounce,
            "subtitle": s["user"],
            "icon": search_icon_5(s["rrss"]),
            "link": "Social",
        }
        social_raw.append(social_item)
        if s["rrss"] + s["source"] == prev:
            nounce = nounce + " "
        prev = s["rrss"] + s["source"]

    # ------------------------------------------------------------------ #
    # Refine social — keep best candidate per network                      #
    # ------------------------------------------------------------------ #
    socialp: list[dict] = []
    rrss = ""
    social_refined: list[str] = []
    a = -1
    count = 0
    for s_c in social_count:
        if s_c.split("-|-")[0] != rrss:
            a += 1
            social_refined.append(s_c)
            rrss = s_c.split("-|-")[0]
            count = social_count[s_c]
        elif (count < social_count[s_c]) or (
            count >= social_count[s_c] and name_match(name_tokens, s_c.split("-|-")[2])
        ):
            social_refined[a] = s_c
            rrss = s_c.split("-|-")[0]
            count = social_count[s_c]

    username_refined: list[str] = []
    if social_refined:
        socialp.append(
            {
                "name-node": "Social",
                "title": "Social",
                "subtitle": "",
                "icon": search_icon_5("child"),
                "link": "Social",
            }
        )
        for social_entry in social_refined:
            parts = social_entry.split("-|-")
            if parts[1] not in username_refined and parts[1] != "":
                username_refined.append(parts[1])
            socialp.append(
                {
                    "name-node": parts[0],
                    "title": parts[0],
                    "subtitle": parts[1],
                    "icon": search_icon_5(parts[0]),
                    "link": "Social",
                }
            )

    # ------------------------------------------------------------------ #
    # Build task list and word-cloud lists                                 #
    # ------------------------------------------------------------------ #
    tasks: list[dict] = []
    for soc in socialp:
        if soc["subtitle"] != "":
            tasks.append({"module": soc["title"], "param": soc["subtitle"]})

    name_cloud = [{"label": n} for n in names]
    username_cloud = [{"label": u} for u in users]

    return (
        social_raw,
        socialp,
        username_refined,
        name_complete,
        tasks,
        name_cloud,
        username_cloud,
    )
