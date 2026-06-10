#!/usr/bin/env python

import collections
import json
import sys

from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.iKy_functions import deep_analysis, simple_analysis
from factories.search_orchestrator import post_process_results
from factories.search_providers import (
    BraveSearchProvider,
    GoogleCSEProvider,
    GoogleProvider,
)
from factories.task_wrapper import iky_task
from thefuzz import process

logger = get_task_logger(__name__)


@iky_task(module_name="dorks")
def p_dorks(username, from_m="Initial"):
    """Task of Celery that get info from google dorks.

    Social Networks :
        - twitter
        - github
        - instagram
        - keybase
        - linkedin
        - tiktok
    TODO :
        - gitlab
        - tinder
        - bitbucket
        - reddit
        - youtube
        - twitch
        - facebook
        - pinterest
    """

    # Build fallback chain: GoogleCSE → BraveSearch → Google scraper
    cse_api_key = api_keys_search("cse_api_key")
    cse_cx = api_keys_search("cse_cx")
    brave_key = api_keys_search("brave_key")

    raw_node: list[dict] = []

    # 1. Try GoogleCSE first (requires both keys)
    if cse_api_key and cse_cx:
        logger.info("Dorks - trying GoogleCSEProvider for %r", username)
        raw_node = GoogleCSEProvider(cse_api_key, cse_cx).search_with_dorks(username)
        if not raw_node:
            logger.warning(
                "Dorks - GoogleCSEProvider returned no results for %r, falling back",
                username,
            )

    # 2. Fallback to BraveSearchProvider (requires brave_key)
    if not raw_node and brave_key:
        logger.info("Dorks - trying BraveSearchProvider for %r", username)
        raw_node = BraveSearchProvider(brave_key).search_with_dorks(username)
        if not raw_node:
            logger.warning(
                "Dorks - BraveSearchProvider returned no results for %r, falling back",
                username,
            )

    # 3. Final fallback: GoogleProvider scraper (no key needed)
    if not raw_node:
        logger.info("Dorks - trying GoogleProvider (scraper) for %r", username)
        raw_node = GoogleProvider().search_with_dorks(username)
        if not raw_node:
            logger.warning(
                "Dorks - GoogleProvider returned no results for %r", username
            )

    output_dict: dict = {}
    for i in raw_node:
        try:
            output_dict = simple_analysis(
                i["dork"],
                "username",
                username,
                [i["titles"], i["links"], i["descriptions"]],
                output_dict,
            )
        except Exception:
            continue

    # Collect names to tokenise
    try:
        names = [item["name"].strip() for item in output_dict["names"]]
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
    ) = post_process_results(output_dict, name_tokens)

    # Deep analysis
    for i in raw_node:
        try:
            output_dict = deep_analysis(
                name_tokens,
                username_refined,
                i["dork"],
                [i["titles"], i["links"], i["descriptions"]],
                output_dict,
            )
        except Exception:
            continue

    # Build output arrays (same contract as before)
    graphic = []
    profile = []
    timeline = []

    profile.append({"name": name_complete})

    graphic.append({"names": name_cloud})
    graphic.append({"username": username_cloud})
    graphic.append({"social": social_raw})
    graphic.append({"rawresults": output_dict.get("rawresult", [])})
    graphic.append({"searches": output_dict.get("search", [])})
    graphic.append({"mentions": output_dict.get("users", [])})
    graphic.append({"hashtags": output_dict.get("hashtags", [])})
    graphic.append({"emails": output_dict.get("emails", [])})

    total = [
        {"module": "dorks"},
        {"param": username},
        {"validation": "no"},
        {"raw": raw_node},
        {"graphic": graphic},
        {"profile": profile},
        {"timeline": timeline},
        {"tasks": tasks},
    ]

    return total


# Backward-compatible alias
t_dorks = p_dorks


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_dorks(username)
    output(result)
