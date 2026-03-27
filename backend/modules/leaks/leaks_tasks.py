#!/usr/bin/env python

import argparse
import json

import requests
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


@iky_task(module_name="leaks")
def p_leaks(email):
    """Task of Celery that get info from XposedOrNot."""

    url = f"https://api.xposedornot.com/v1/breach-analytics?email={email}"
    req = requests.get(
        url,
        headers={"User-Agent": "iKy-OSINT"},
        timeout=15,
    )

    if req.status_code == 404:
        raise Exception("iKy - No leak found")
    elif req.status_code == 429:
        raise Exception("iKy - Rate limited, try again later")
    elif req.status_code != 200:
        raise Exception(f"iKy - XposedOrNot API Error ({req.status_code})")

    data = req.json()
    exposed = data.get("ExposedBreaches") or {}
    breaches = exposed.get("breaches_details") or []

    if not breaches:
        raise Exception("iKy - No leak found")

    metrics = data.get("BreachMetrics") or {}
    risk_list = metrics.get("risk") or []
    risk_entry = risk_list[0] if risk_list else {}

    risk_label = str(risk_entry.get("risk_label") or "Unknown")
    risk_score = int(risk_entry.get("risk_score") or 0)

    total_records = 0
    for breach in breaches:
        total_records += int(breach.get("xposed_records") or 0)

    sorted_breaches = sorted(
        breaches,
        key=lambda b: int(b.get("xposed_records") or 0),
        reverse=True,
    )
    top_breach = sorted_breaches[0] if sorted_breaches else {}

    years = []
    for breach in breaches:
        year_raw = str(breach.get("xposed_date") or "")
        if year_raw.isdigit() and len(year_raw) == 4:
            years.append(int(year_raw))
    last_year = max(years) if years else 0

    # Total
    total = []
    total.append({"module": "leaks"})
    total.append({"param": email})
    total.append({"validation": "hard"})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    link = "Leaks"
    gather_item = {
        "name-node": "Leaks",
        "title": "Leaks",
        "subtitle": "",
        "icon": "fas fa-unlock-alt",
        "link": link,
    }
    gather.append(gather_item)

    for breach in breaches:
        name = breach.get("breach", "")
        date = breach.get("xposed_date", "")
        desc = breach.get("details", "")
        logo = breach.get("logo", "")
        records = breach.get("xposed_records", 0)
        subtitle_parts = []
        if date:
            subtitle_parts.append(f"Date: {date}")
        if records:
            subtitle_parts.append(f"Records: {records:,}")

        gather_item = {
            "name-node": name,
            "title": name,
            "subtitle": " · ".join(subtitle_parts),
            "link": link,
        }
        if logo:
            gather_item["picture"] = f"https://xposedornot.com/img/{logo}"
        gather.append(gather_item)

        timeline.append(
            {
                "action": "Leak : " + name,
                "date": date,
                "icon": "fa-exclamation-circle",
                "desc": desc,
            }
        )

    # Raw — full XON response for detail views
    raw_node = data

    total.append({"raw": raw_node})
    graphic.append({"leaks": gather})
    graphic.append(
        {
            "summary": {
                "breach_count": len(breaches),
                "risk_label": risk_label,
                "risk_score": risk_score,
                "total_records": total_records,
                "top_breach": str(top_breach.get("breach") or ""),
                "last_year": str(last_year) if last_year else "",
            }
        }
    )
    graphic.append(
        {
            "risk": {
                "risk_label": risk_label,
                "risk_score": risk_score,
            }
        }
    )
    graphic.append({"passwords_strength": metrics.get("passwords_strength") or []})
    graphic.append({"industry": metrics.get("industry") or []})
    graphic.append({"yearwise_details": metrics.get("yearwise_details") or []})
    graphic.append({"xposed_data": metrics.get("xposed_data") or []})
    graphic.append(
        {
            "top_breaches": [
                {
                    "breach": str(breach.get("breach") or ""),
                    "records": int(breach.get("xposed_records") or 0),
                    "year": str(breach.get("xposed_date") or ""),
                    "industry": str(breach.get("industry") or ""),
                }
                for breach in sorted_breaches[:8]
            ]
        }
    )
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_leaks
t_leaks = p_leaks


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query XposedOrNot for email breaches")
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_leaks(args.email)
    output(result)
