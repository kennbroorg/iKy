#!/usr/bin/env python

import collections
import contextlib
import json
import sys

from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.iKy_functions import deep_analysis, simple_analysis
from factories.search_orchestrator import SearchOrchestrator, post_process_results
from factories.search_providers import (
    BraveSearchProvider,
    DeprecatedProvider,
    DuckDuckGoProvider,
    GoogleCSEProvider,
    GoogleProvider,
)
from factories.task_wrapper import iky_task
from thefuzz import process

logger = get_task_logger(__name__)

# Failure messages per active engine (preserved for frontend compatibility)
_FAILURE_MSGS = {
    "google": (
        "Engine_failure Google",
        "Detected and flagged as unusual traffic (Google)",
        "fab fa-google",
    ),
    "duckduckgo": (
        "Engine_failure duckduckgo",
        "Detected and flagged as unusual traffic (duckduckgo)",
        "fas fa-kiwi-bird",
    ),
    "brave": (
        "Engine_failure brave",
        "Detected and flagged as unusual traffic (Brave)",
        "fas fa-shield-alt",
    ),
}


@iky_task(module_name="search")
def p_search(username, from_m="Initial"):
    """Task of Celery that get info from searchers"""

    brave_key = api_keys_search("brave_key")
    cse_api_key = api_keys_search("cse_api_key")
    cse_cx = api_keys_search("cse_cx")

    providers = [
        DuckDuckGoProvider(),
        GoogleProvider(),
    ]
    if brave_key:
        providers.append(BraveSearchProvider(brave_key))
    if cse_api_key and cse_cx:
        providers.append(GoogleCSEProvider(cse_api_key, cse_cx))

    # Deprecated stubs — preserve name/icon metadata for the search graph
    # without executing any actual search
    providers.extend(
        [
            DeprecatedProvider("yahoo", "fab fa-yahoo"),
            DeprecatedProvider("bing", "fab fa-windows"),
            DeprecatedProvider("yandex", "fab fa-yandex-international"),
            DeprecatedProvider("baidu", "fas fa-paw"),
        ]
    )
    orchestrator = SearchOrchestrator(providers)
    all_results = orchestrator.search_all(username)

    output: dict = {}

    # Simple analysis pass — extract social signals from each result
    for provider_name, results in all_results.items():
        for r in results:
            try:
                output = simple_analysis(
                    provider_name,
                    "username",
                    username,
                    [r.title, r.url, r.description],
                    output,
                )
            except Exception:
                continue

    # Collect names to tokenise
    try:
        names = [item["name"].strip() for item in output["names"]]
        collections.Counter(names)
    except Exception:
        names = []

    try:
        best_match = process.extractBests(
            collections.Counter(names).most_common(2)[0][0],
            names,
            limit=len(names),
            score_cutoff=80,
        )
    except Exception:
        best_match = []

    # Tokenize the best-matching name
    name_tokens: list[str] = []
    for n_ext in best_match:
        for n_int in n_ext[0].split(" "):
            if n_int not in name_tokens:
                name_tokens.append(n_int)

    # Shared social-refinement + output assembly
    (
        social_raw,
        socialp,
        username_refined,
        name_complete,
        tasks,
        name_cloud,
        username_cloud,
    ) = post_process_results(output, name_tokens)

    # Deep analysis pass — match results against known tokens/usernames
    for provider_name, results in all_results.items():
        for r in results:
            with contextlib.suppress(Exception):
                output = deep_analysis(
                    name_tokens,
                    username_refined,
                    provider_name,
                    [r.title, r.url, r.description],
                    output,
                )

    # Flag failed engines
    if "rawresult" not in output:
        output["rawresult"] = []
    if "search" not in output:
        output["search"] = []

    for engine_name, (node_name, title, icon) in _FAILURE_MSGS.items():
        # Only flag as failed when the engine was actually configured
        # (present in all_results) but returned zero results.
        if engine_name in all_results and not all_results[engine_name]:
            failure_item = {
                "name-node": node_name,
                "title": title,
                "subtitle": "",
                "icon": icon,
                "link": engine_name,
            }
            output["rawresult"].append(failure_item)
            output["search"].append(failure_item)

    # Append searcher-node entries to the search graph
    analized_results = list(output["search"])
    output["search"].append(
        {
            "name-node": "searcher",
            "title": "searcher",
            "subtitle": "",
            "icon": "fas fa-search",
            "link": "searcher",
        }
    )
    for provider in providers:
        output["search"].append(
            {
                "name-node": provider.name,
                "title": "Searcher",
                "subtitle": "",
                "icon": provider.icon,
                "link": provider.name,
            }
        )

    # Build output arrays (same contract as before)
    graphic = []
    profile = []
    timeline = []

    profile.append({"name": name_complete})

    graphic.append({"names": name_cloud})
    graphic.append({"username": username_cloud})
    graphic.append({"social": social_raw})
    graphic.append({"rawresults": output["rawresult"]})
    graphic.append({"results": analized_results})
    graphic.append({"searches": output["search"]})
    graphic.append({"mentions": output.get("users", [])})
    graphic.append({"hashtags": output.get("hashtags", [])})
    graphic.append({"emails": output.get("emails", [])})

    total = [
        {"module": "search"},
        {"param": username},
        {"validation": "no"},
        {"raw": {k: [r.__dict__ for r in v] for k, v in all_results.items()}},
        {"graphic": graphic},
        {"profile": profile},
        {"timeline": timeline},
        {"tasks": tasks},
    ]

    return total


# Backward-compatible alias
t_search = p_search


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_search(username)
    output(result)
