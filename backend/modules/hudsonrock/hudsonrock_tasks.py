#!/usr/bin/env python

import argparse
import json

import requests
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)

# Hudson Rock Cavalier free, unauthenticated OSINT endpoints.
BASE_URL = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/"

# Static, maintainable infostealer family context. Known families map to a
# short human-readable description; unknown / missing families fall back to a
# generic "infostealer" label (see ``_enrich_family``).
STEALER_FAMILY_CONTEXT: dict[str, str] = {
    "RedLine": (
        "RedLine Stealer - malware-as-a-service harvesting browser credentials, "
        "cookies, and cryptocurrency wallets."
    ),
    "Raccoon": (
        "Raccoon Stealer - subscription infostealer grabbing passwords, cookies, "
        "autofill data, and wallets."
    ),
    "Vidar": (
        "Vidar - infostealer collecting browser data, documents, and "
        "cryptocurrency wallets."
    ),
    "Lumma": (
        "Lumma (LummaC2) - modern infostealer targeting browsers, 2FA artifacts, "
        "and crypto wallets."
    ),
    "LummaC2": (
        "Lumma (LummaC2) - modern infostealer targeting browsers, 2FA artifacts, "
        "and crypto wallets."
    ),
    "META": (
        "META Stealer - RedLine-derived infostealer focused on browser and wallet "
        "credentials."
    ),
    "Azorult": (
        "AZORult - infostealer collecting credentials, cookies, browser history, "
        "and crypto wallets."
    ),
    "Mars": (
        "Mars Stealer - infostealer focused on browser data and cryptocurrency wallets."
    ),
    "Taurus": (
        "Taurus Stealer - infostealer targeting browser credentials, files, and "
        "wallets."
    ),
    "StealC": (
        "StealC - lightweight infostealer for browser, wallet, and application "
        "credentials."
    ),
    "Rhadamanthys": (
        "Rhadamanthys - advanced infostealer targeting browsers, wallets, and "
        "installed applications."
    ),
    "Generic Stealer": (
        "Generic Stealer - unattributed infostealer; specific family not "
        "identified by Hudson Rock."
    ),
}


# ---------------------------------------------------------------------------
# Module-private helpers (pure where possible)
# ---------------------------------------------------------------------------
def _local_part(param: str) -> str:
    """Return the local-part of an email (substring before ``@``)."""
    return param.split("@")[0]


def _request(url: str) -> dict:
    """GET a Cavalier endpoint and return the parsed JSON body.

    Status handling (raw responses are NEVER logged):
      - 404 -> ``{}`` (no data from this endpoint; merged-empty becomes a
        no-compromise warning at the call site)
      - 429 -> ``iKy - Rate limited``
      - other non-200 -> ``iKy - Hudson Rock API Error ({status})``
    """
    req = requests.get(
        url,
        headers={"User-Agent": "iKy-OSINT"},
        timeout=15,
    )

    if req.status_code == 404:
        return {}
    if req.status_code == 429:
        raise Exception("iKy - Rate limited")
    if req.status_code != 200:
        raise Exception(f"iKy - Hudson Rock API Error ({req.status_code})")

    return req.json()


def _stealer_key(stealer: dict) -> tuple:
    """Stable physical identity for a stealer record.

    Identity is the machine fingerprint only:
    ``(computer_name, date_compromised, ip, operating_system)``. ``stealer_family``
    is deliberately EXCLUDED: live Cavalier data proved ``search-by-email`` omits
    the family while ``search-by-username`` includes it for the SAME machine, so
    keying on family would split one physical compromise into two records.
    """
    return (
        stealer.get("computer_name"),
        stealer.get("date_compromised"),
        stealer.get("ip"),
        stealer.get("operating_system"),
    )


def _dedup_stealers(stealers: list[dict]) -> list[dict]:
    """Deduplicate by physical key, preserving order and merging family.

    On a key collision the first-seen record is kept. If that kept record lacks a
    ``stealer_family`` (missing / ``None`` / empty) and the duplicate carries one,
    the family is backfilled onto the kept record. This reconciles the
    email+username dual lookup into ONE record that keeps the populated family.
    """
    seen: dict[tuple, dict] = {}
    unique: list[dict] = []
    for stealer in stealers:
        key = _stealer_key(stealer)
        kept = seen.get(key)
        if kept is None:
            seen[key] = stealer
            unique.append(stealer)
            continue
        if not kept.get("stealer_family") and stealer.get("stealer_family"):
            kept["stealer_family"] = stealer["stealer_family"]
    return unique


def _aggregate_totals(stealers: list[dict]) -> tuple[int, int]:
    """Derive (corporate, user) service totals from the deduped records."""
    corporate = sum(int(s.get("total_corporate_services") or 0) for s in stealers)
    user = sum(int(s.get("total_user_services") or 0) for s in stealers)
    return corporate, user


def _enrich_family(stealer: dict) -> tuple[str, str]:
    """Resolve (family_label, description) for a stealer record.

    - Known family -> mapped description.
    - Present but unknown family -> raw name + generic ``"infostealer"``.
    - Absent / ``None`` family -> ``"Unknown"`` + generic ``"infostealer"``.
    """
    family = stealer.get("stealer_family")
    if family:
        return family, STEALER_FAMILY_CONTEXT.get(family, "infostealer")
    return "Unknown", "infostealer"


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------
@iky_task(module_name="hudsonrock", dev_mode_sleep=5)
def p_hudsonrock(param):
    """Task of Celery that gets infostealer intel from Hudson Rock Cavalier."""

    queries: list[dict] = []

    if "@" in param:
        local = _local_part(param)
        email_data = _request(f"{BASE_URL}search-by-email?email={param}")
        queries.append({"type": "email", "param": param, "response": email_data})
        user_data = _request(f"{BASE_URL}search-by-username?username={local}")
        queries.append({"type": "username", "param": local, "response": user_data})
    else:
        local = None
        user_data = _request(f"{BASE_URL}search-by-username?username={param}")
        queries.append({"type": "username", "param": param, "response": user_data})

    merged: list[dict] = []
    for query in queries:
        merged.extend(query["response"].get("stealers") or [])

    stealers = _dedup_stealers(merged)
    if not stealers:
        raise Exception("iKy - No infostealer compromise found")

    corporate_total, user_total = _aggregate_totals(stealers)

    # Total
    total = []
    total.append({"module": "hudsonrock"})
    total.append({"param": param})
    total.append({"validation": "hard"})

    # Containers
    graphic = []
    profile = []
    timeline = []
    gather = []

    parent = {
        "name-node": "HudsonRock",
        "title": "HudsonRock",
        "subtitle": "",
        "icon": "fas fa-bug",
        "link": "HudsonRock",
    }
    gather.append(parent)

    for index, stealer in enumerate(stealers):
        family_label, family_desc = _enrich_family(stealer)
        date = stealer.get("date_compromised", "")
        computer = stealer.get("computer_name", "")
        operating_system = stealer.get("operating_system", "")
        ip = stealer.get("ip", "")
        record_services = int(stealer.get("total_corporate_services") or 0) + int(
            stealer.get("total_user_services") or 0
        )

        subtitle = " · ".join(
            part
            for part in (
                date,
                family_label,
                operating_system,
                ip,
                f"Services: {record_services}",
            )
            if part
        )

        gather.append(
            {
                "name-node": f"HR-{index}",
                "title": computer or family_label,
                "subtitle": subtitle,
                "icon": "fas fa-bug",
                "link": "HudsonRock",
                "help": family_desc,
                "date_compromised": date,
                "stealer_family": family_label,
                "computer_name": computer,
                "operating_system": operating_system,
                "malware_path": stealer.get("malware_path", ""),
                "antiviruses": stealer.get("antiviruses") or [],
                "ip": ip,
                "top_passwords": stealer.get("top_passwords") or [],
                "top_logins": stealer.get("top_logins") or [],
                "total_services": record_services,
            }
        )

        timeline.append(
            {
                "date": date,
                "action": f"Infostealer compromise : {family_label}",
                "icon": "fas fa-bug",
                "desc": " · ".join(
                    part
                    for part in (computer, operating_system, ip, family_desc)
                    if part
                ),
            }
        )

    # Profile (flat single-key dicts)
    profile.append(
        {
            "presence": [
                {
                    "name": "hudsonrock",
                    "children": [
                        {"name": "stealers", "value": len(stealers)},
                        {"name": "total_user_services", "value": user_total},
                        {
                            "name": "total_corporate_services",
                            "value": corporate_total,
                        },
                    ],
                }
            ]
        }
    )
    if local:
        profile.append({"username": local})

    # Raw — normalized, JSON-serializable, never logged.
    raw_node = {
        "queries": queries,
        "stealers": stealers,
        "total_corporate_services": corporate_total,
        "total_user_services": user_total,
    }

    total.append({"raw": raw_node})
    graphic.append({"hudsonrock": gather})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_hudsonrock
t_hudsonrock = p_hudsonrock


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Hudson Rock Cavalier for infostealer compromise"
    )
    parser.add_argument("param", help="Email or username to look up")
    args = parser.parse_args()

    result = t_hudsonrock(args.param)
    output(result)
