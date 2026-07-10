#!/usr/bin/env python

import argparse
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import requests
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.cookie_utils import convert_browser_cookies
from factories.iKy_functions import location_geo
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# Cookie persistence
# ---------------------------------------------------------------------------
_DEFAULT_COOKIE_DIR = Path(__file__).resolve().parents[2] / "cookies"
_COOKIE_DIR = Path(os.environ.get("LINKEDIN_COOKIE_DIR", str(_DEFAULT_COOKIE_DIR)))
_COOKIE_FILE = _COOKIE_DIR / "linkedin_cookies.json"


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


# Cookie conversion is shared across modules — see factories.cookie_utils.
# Keep the historical private name as an alias so existing call sites and the
# test suite resolve while the logic lives in exactly one place.
_convert_browser_cookies = convert_browser_cookies


def _authenticate_linkedin(session: requests.Session) -> None:
    """Three-tier auth chain. Mutates session.cookies + session.headers['csrf-token'].

    Auth chain (in order):
    1. ``_COOKIE_FILE`` on disk → load directly (fastest path)
    2. ``linkedin_cookies`` API key → Cookie-Editor JSON; convert + persist to disk
    3. Legacy ``linkedin_li_at`` + ``linkedin_JSESSIONID`` API keys
    4. All methods exhausted → raise a clear, actionable error

    Raises
    ------
    Exception
        With ``iKy - `` prefix referencing ``docs/COOKIES.md`` when all tiers fail.
    """
    # --- Tier 1: Cookie file already on disk ---
    if _COOKIE_FILE.exists():
        cookie_data = json.loads(_COOKIE_FILE.read_text())
        session.cookies["li_at"] = cookie_data["li_at"]
        session.cookies["JSESSIONID"] = cookie_data["JSESSIONID"]
        session.headers["csrf-token"] = cookie_data["JSESSIONID"].strip('"')
        return

    # --- Tier 2: Browser-exported cookies from linkedin_cookies API key ---
    raw_cookie_str = api_keys_search("linkedin_cookies")
    if raw_cookie_str:
        try:
            browser_cookies = json.loads(raw_cookie_str)
            cookie_data = convert_browser_cookies(browser_cookies)
            session.cookies["li_at"] = cookie_data["li_at"]
            session.cookies["JSESSIONID"] = cookie_data["JSESSIONID"]
            session.headers["csrf-token"] = cookie_data["JSESSIONID"].strip('"')
            # Persist so subsequent calls use tier 1 (faster, no re-parse)
            _COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _COOKIE_FILE.write_text(json.dumps(cookie_data))
            logger.info("LinkedIn authenticated via browser cookies from API key")
            return
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning(
                f"LinkedIn: invalid cookie JSON in linkedin_cookies key: {exc}"
            )
        except Exception as exc:
            logger.warning(f"LinkedIn: failed to load browser cookies: {exc}")

    # --- Tier 3: Legacy linkedin_li_at + linkedin_JSESSIONID API keys ---
    v_li_at = api_keys_search("linkedin_li_at")
    v_jsessionid = api_keys_search("linkedin_JSESSIONID")
    if v_li_at and v_jsessionid:
        session.cookies["li_at"] = v_li_at
        session.cookies["JSESSIONID"] = v_jsessionid
        session.headers["csrf-token"] = v_jsessionid.strip('"')
        logger.info("LinkedIn authenticated via legacy API keys")
        return

    # --- All tiers exhausted ---
    raise Exception(
        "iKy - LinkedIn requires browser cookies. Export cookies from linkedin.com "
        "using Cookie-Editor extension and paste the JSON in the linkedin_cookies "
        "API key field."
    )


# ---------------------------------------------------------------------------
# Date helper (unchanged)
# ---------------------------------------------------------------------------


def date_convert(date):
    date_conv = str(date.get("year", ""))
    if date.get("month"):
        date_conv = f"{date_conv}-{int(date.get('month')):02d}"
    return date_conv


# ---------------------------------------------------------------------------
# HTML + RSC extraction helpers  (new — Phase 2)
# ---------------------------------------------------------------------------

_RSC_MARKER = "window.__como_rehydration__ = "

# Noise filters for RSC text blocks
_BLOCK_NOISE_PREFIXES = ("_", "$", "proto.", "com.linkedin")
_BLOCK_NOISE_CONTAINS = ("{:", "function", "return ", "var ")
_BLOCK_UI_LABELS = {
    "contact info",
    "message",
    "connect",
    "more",
    "follow",
    "about",
    "view settings",
    "save to pdf",
    "open to",
    "pending",
    "dismiss",
    "block",
    "report",
    "share",
    # Spanish UI labels
    "información de contacto",
    "mensaje",
    "conectar",
    "más",
    "seguir",
    "acerca de",
    "guardar en pdf",
    # Footer / legal links (appear as text blocks in RSC)
    "accessibility",
    "talent solutions",
    "community guidelines",
    "careers",
    "marketing solutions",
    "privacy policy",
    "user agreement",
    "pages terms",
    "cookie policy",
    "copyright policy",
    "ad choices",
    "advertising",
    "sales solutions",
    "mobile",
    "small business",
    "safety center",
    "questions?",
    # Spanish footer
    "accesibilidad",
    "soluciones de talento",
    "directrices de la comunidad",
    "empleo",
    "soluciones de marketing",
    "política de privacidad",
    "acuerdo del usuario",
    "política de cookies",
    "política de derechos de autor",
    "opciones de anuncios",
    "publicidad",
    "centro de seguridad",
}


def _fetch_profile_html(session: requests.Session, username: str) -> str:
    """GET /in/{username}/ → HTML text.

    Raises
    ------
    Exception
        With 'iKy -' prefix if response is non-200 or request fails.
    """
    url = f"https://www.linkedin.com/in/{username}/"
    try:
        resp = session.get(url)
    except Exception as exc:
        raise Exception(
            f"iKy - LinkedIn: failed to fetch profile page for '{username}': {exc}. "
            "Check that your cookies are valid and not expired."
        ) from exc

    if resp.status_code != 200:
        raise Exception(
            f"iKy - LinkedIn: profile page returned HTTP {resp.status_code} "
            f"for '{username}'. Your cookies may be invalid or expired. "
            "See docs/COOKIES.md."
        )
    return resp.text


def _parse_rsc_payload(html_text: str) -> str:
    """Extract window.__como_rehydration__ array, concatenate, return RSC string.

    Raises
    ------
    Exception
        With 'iKy -' prefix if the marker is missing or JSON is malformed.
    """
    start = html_text.find(_RSC_MARKER)
    if start == -1:
        raise Exception(
            "iKy - LinkedIn: __como_rehydration__ marker not found in HTML. "
            "The LinkedIn frontend may have been updated and changed the RSC "
            "rehydration format. Check for a newer version of iKy."
        )

    end = html_text.find("</script>", start)
    rsc_raw = html_text[start + len(_RSC_MARKER) : end].strip().rstrip(";")
    rsc_array = json.loads(rsc_raw)
    return "".join(rsc_array)


def _extract_text_blocks(rsc_text: str) -> list[str]:
    """Extract \"children\":[\"text\"] snippets from RSC text, filtered of noise."""
    raw_blocks = re.findall(r'"children":\["([^"]{3,500})"\]', rsc_text)
    result = []
    for block in raw_blocks:
        # Skip blocks starting with noise prefixes
        if any(block.startswith(p) for p in _BLOCK_NOISE_PREFIXES):
            continue
        # Skip blocks with noise substrings
        if any(n in block for n in _BLOCK_NOISE_CONTAINS):
            continue
        # Skip very short or blocks with 3+ underscores
        if len(block) < 5 or block.count("_") >= 3:
            continue
        result.append(block)
    return result


def _extract_name(html_text: str) -> str:
    """Extract profile name from <title>Name | LinkedIn</title>.

    Returns '' on failure.
    """
    try:
        m = re.search(r"<title>([^<]+?)\s*\|\s*LinkedIn</title>", html_text)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""


def _extract_member_id(rsc_text: str) -> str:
    """Extract member ID from urn:li:member:DIGITS pattern.

    Returns '' on failure.
    """
    try:
        m = re.search(r"urn:li:member:(\d+)", rsc_text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def _extract_connections(rsc_text: str) -> str:
    """Extract connections count from '500+ connections' or '500+ conexiones'.

    Returns '' on failure.
    """
    try:
        m = re.search(
            r"(\d+\+?)\s*(?:connections?|conexiones?)", rsc_text, re.IGNORECASE
        )
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def _extract_photo_urls(rsc_text: str) -> list[str]:
    """Extract media.licdn.com profile photo URLs from RSC text.

    Returns [] on failure.
    """
    try:
        return re.findall(
            r"https://media\.licdn\.com/dms/image/[^\"\\]*profile-displayphoto[^\"\\]*",
            rsc_text,
        )
    except Exception:
        return []


def _extract_headline(text_blocks: list[str]) -> str:
    """Return first block >20 chars that is not a UI label and not the name.

    Returns '' on failure.
    """
    try:
        for block in text_blocks:
            if len(block) <= 20:
                continue
            if block.lower() in _BLOCK_UI_LABELS:
                continue
            return block
    except Exception:
        pass
    return ""


def _extract_location(text_blocks: list[str]) -> str:
    """Return block matching location pattern (comma + capitalized words).

    Returns '' on failure.
    """
    _LOCATION_WORDS = (
        "United States",
        "United Kingdom",
        "Canada",
        "Australia",
        "Germany",
        "France",
        "Spain",
        "Italy",
        "Brazil",
        "Mexico",
        "Argentina",
        "India",
        "China",
        "Japan",
        "Korea",
        "Netherlands",
        "Sweden",
        "Norway",
        "Denmark",
        "Finland",
        "Switzerland",
        "Austria",
        "Belgium",
        "Portugal",
        "Poland",
        "Russia",
        "Turkey",
        "Israel",
        "Singapore",
        "New Zealand",
        "Ireland",
        "South Africa",
        "Nigeria",
        "Egypt",
        "Colombia",
        "Chile",
        "Peru",
    )
    try:
        for block in text_blocks:
            # Must have a comma (city, region pattern)
            if "," not in block:
                continue
            # Must not look like a job title (no | character typical in headlines)
            if "|" in block:
                continue
            # Check for known country names
            if any(country in block for country in _LOCATION_WORDS):
                return block
            # Fallback: comma-separated capitalized words pattern
            parts = [p.strip() for p in block.split(",")]
            if all(p and p[0].isupper() for p in parts) and len(parts) >= 2:
                return block
    except Exception:
        pass
    return ""


def _extract_company(text_blocks: list[str]) -> str:
    """Return company name using block immediately before location in sequence.

    Heuristic: find the location block index, take the block before it.
    Returns '' on failure.
    """
    try:
        loc = _extract_location(text_blocks)
        if not loc:
            return ""
        idx = text_blocks.index(loc)
        if idx > 0:
            candidate = text_blocks[idx - 1]
            # Company name: short (<50 chars), no commas, no | (not a headline)
            if len(candidate) < 50 and "," not in candidate and "|" not in candidate:
                return candidate
    except Exception:
        pass
    return ""


def _extract_profile_urn(rsc_text: str) -> str:
    """Extract profile URN from urn:li:fsd_profile:TOKEN pattern.

    Returns '' on failure.
    """
    try:
        m = re.search(r"urn:li:fsd_profile:([^\"\\]+)", rsc_text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ""


def _extract_verified(rsc_text: str) -> bool:
    """Check if the profile has a verification badge.

    Looks for 'verification' keyword in RSC text near profile context.
    Returns False on failure.
    """
    try:
        return bool(re.search(r"has a verification", rsc_text, re.IGNORECASE))
    except Exception:
        return False


def _extract_profile_fields(rsc_text: str, html_text: str) -> dict:
    """Extract all profile fields from RSC text and HTML.

    Each field is individually fault-isolated — a failure in one field
    does not affect others. All string fields default to ''.

    Returns
    -------
    dict with keys: name, headline, location, connections, company,
                    photo_urls, member_id, profile_urn, verified
    """
    text_blocks = _extract_text_blocks(rsc_text)

    name = _extract_name(html_text)
    member_id = _extract_member_id(rsc_text)
    connections = _extract_connections(rsc_text)
    photo_urls = _extract_photo_urls(rsc_text)
    profile_urn = _extract_profile_urn(rsc_text)
    headline = _extract_headline(text_blocks)
    location = _extract_location(text_blocks)
    company = _extract_company(text_blocks)
    verified = _extract_verified(rsc_text)

    return {
        "name": name,
        "headline": headline,
        "location": location,
        "connections": connections,
        "company": company,
        "photo_urls": photo_urls,
        "member_id": member_id,
        "profile_urn": profile_urn,
        "verified": verified,
    }


# ---------------------------------------------------------------------------
# Main task  (rewired — Phase 3)
# ---------------------------------------------------------------------------


@iky_task(module_name="linkedin", dev_mode_sleep=10)
def p_linkedin(user, from_m="Initial"):
    """Task of Celery that get info from LinkedIn (HTML + surviving Voyager calls)."""

    s = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
        + "AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 "
        + "Safari/7046A194A"
    }
    s.headers.update(headers)

    _authenticate_linkedin(s)

    # Total
    total = []
    total.append({"module": "linkedin"})
    total.append({"param": user})

    found = False
    # Get profile from username
    if "http" in user:
        total.append({"validation": "hard" if from_m == "Initial" else "soft"})
        raise Exception("iKy - Linkedin don't work with url")
    # Get profile from email
    elif "@" in user:
        raise Exception("iKy - Linkedin don't work with email")
    else:
        total.append({"validation": "hard" if from_m == "Initial" else "soft"})
        found = True

    if found:
        # --- Call 1: HTML page fetch (replaces profileView + networkinfo + skillCategory) ---
        html_text = _fetch_profile_html(s, user)
        rsc_text = _parse_rsc_payload(html_text)
        fields = _extract_profile_fields(rsc_text, html_text)

        # Voyager endpoints require the vanityName (username), not the member_id
        voyager_id = user

        # --- Call 2: /following (surviving Voyager endpoint) ---
        url = (
            "https://www.linkedin.com/voyager/api/identity/profiles/"
            + voyager_id
            + "/following?q=followedEntities&count=17"
        )
        req = s.get(url, headers=headers)
        following_view = json.loads(req.text)

        # --- Call 3: /recommendations?q=received (surviving Voyager endpoint) ---
        url = (
            "https://www.linkedin.com/voyager/api/identity/profiles/"
            + voyager_id
            + "/recommendations?q=received&recommendationStatuses=List(VISIBLE)"
        )
        req = s.get(url, headers=headers)
        recommend_received = json.loads(req.text)

        # --- Call 4: /recommendations?q=given (surviving Voyager endpoint) ---
        url = (
            "https://www.linkedin.com/voyager/api/identity/profiles/"
            + voyager_id
            + "/recommendations?q=given"
        )
        req = s.get(url, headers=headers)
        recommend_given = json.loads(req.text)

        # --- Enrich profile fields from Voyager data ---
        # The recommendations endpoint returns the recommendee's occupation
        # (which IS the headline). This is more reliable than RSC text parsing.
        if not fields["headline"] or len(fields["headline"]) < 10:
            try:
                elements = recommend_received.get("elements", [])
                if elements:
                    recommendee = elements[0].get("recommendee", {})
                    occupation = recommendee.get("occupation", "")
                    if occupation:
                        fields["headline"] = occupation
            except Exception:
                pass

        # Extract connections from RSC — fallback to looking in the HTML text
        if not fields["connections"]:
            try:
                # Try matching in the raw HTML (not just RSC) for broader coverage
                m = re.search(
                    r"(\d[\d,.]*\+?)\s*(?:connections?|conexiones?)",
                    html_text,
                    re.IGNORECASE,
                )
                if m:
                    fields["connections"] = m.group(1)
            except Exception:
                pass

        # --- Assemble output ---

        # Social presence array
        socialp = []
        link_social = "Linkedin"
        social_item = {
            "name-node": "Linkedin",
            "title": "Linkedin",
            "subtitle": "",
            "icon": "fab fa-linkedin-in",
            "link": link_social,
        }
        socialp.append(social_item)

        # Name social entry
        name = fields["name"]
        name_parts = name.split(" ", 1) if name else ["", ""]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        social_item = {
            "name-node": "Name",
            "title": "Name",
            "subtitle": name,
            "icon": "fas fa-user-circle",
            "link": link_social,
        }
        socialp.append(social_item)

        social_item = {
            "name-node": "Headline",
            "title": "Headline",
            "subtitle": fields["headline"],
            "icon": "fas fa-building",
            "link": link_social,
        }
        socialp.append(social_item)

        social_item = {
            "name-node": "Location",
            "title": "Location",
            "subtitle": fields["location"],
            "icon": "fas fa-map-marker-alt",
            "link": link_social,
        }
        socialp.append(social_item)

        # Following (from surviving Voyager endpoint)
        social_item = {
            "name-node": "Following",
            "title": "Following",
            "subtitle": following_view.get("paging", {}).get("total", ""),
            "icon": "fas fa-users",
            "link": link_social,
        }
        socialp.append(social_item)

        # Recommendations received
        social_item = {
            "name-node": "Received",
            "title": "Received",
            "subtitle": recommend_received.get("paging", {}).get("total", ""),
            "icon": "fas fa-thumbs-up",
            "link": link_social,
        }
        socialp.append(social_item)

        # Recommendations given
        social_item = {
            "name-node": "Given",
            "title": "Given",
            "subtitle": recommend_given.get("paging", {}).get("total", ""),
            "icon": "fas fa-thumbs-up",
            "link": link_social,
        }
        socialp.append(social_item)

        # --- Build relationship graph from recommendations ---
        link_users = "Users"
        users = [
            {
                "name-node": "Users",
                "title": "Users",
                "subtitle": "",
                "link": link_users,
            }
        ]
        # People who recommended this user
        for elem in recommend_received.get("elements", []):
            try:
                rec = elem.get("recommender", {})
                rec_name = f"{rec.get('firstName', '')} {rec.get('lastName', '')}"
                rec_occ = rec.get("occupation", "")
                rel_type = elem.get("relationship", "")
                users.append(
                    {
                        "name-node": rec_name.strip(),
                        "title": rec_name.strip(),
                        "subtitle": f"{rec_occ} ({rel_type})",
                        "link": link_users,
                    }
                )
            except Exception:
                continue
        # People this user recommended
        for elem in recommend_given.get("elements", []):
            try:
                rec = elem.get("recommendee", {})
                rec_name = f"{rec.get('firstName', '')} {rec.get('lastName', '')}"
                rec_occ = rec.get("occupation", "")
                rel_type = elem.get("relationship", "")
                users.append(
                    {
                        "name-node": rec_name.strip(),
                        "title": rec_name.strip(),
                        "subtitle": f"{rec_occ} ({rel_type})",
                        "link": link_users,
                    }
                )
            except Exception:
                continue

        # --- Build timeline from recommendation timestamps ---
        timeline = []
        for elem in recommend_received.get("elements", []):
            try:
                created_ms = elem.get("created", 0)
                if created_ms:
                    dt = datetime.fromtimestamp(created_ms / 1000, tz=UTC)
                    rec = elem.get("recommender", {})
                    rec_name = (
                        f"{rec.get('firstName', '')} {rec.get('lastName', '')}"
                    ).strip()
                    timeline.append(
                        {
                            "action": f"Recommendation from {rec_name}",
                            "desc": (elem.get("recommendationText", "") or "")[:100],
                            "icon": "fas fa-thumbs-up",
                            "date": dt.strftime("%Y-%m-%d"),
                        }
                    )
            except Exception:
                continue
        for elem in recommend_given.get("elements", []):
            try:
                created_ms = elem.get("created", 0)
                if created_ms:
                    dt = datetime.fromtimestamp(created_ms / 1000, tz=UTC)
                    rec = elem.get("recommendee", {})
                    rec_name = (
                        f"{rec.get('firstName', '')} {rec.get('lastName', '')}"
                    ).strip()
                    timeline.append(
                        {
                            "action": f"Recommendation to {rec_name}",
                            "desc": (elem.get("recommendationText", "") or "")[:100],
                            "icon": "fas fa-thumbs-up",
                            "date": dt.strftime("%Y-%m-%d"),
                        }
                    )
            except Exception:
                continue

        # --- Build following/interests visualization ---
        following_companies = []
        following_groups = []
        following_people = []
        for elem in following_view.get("elements", []):
            try:
                entity = elem.get("entity", {})
                info = elem.get("followingInfo", {})
                followers = info.get("followerCount", 0)

                if "MiniCompany" in str(entity):
                    comp = entity.get(
                        "com.linkedin.voyager.entities.shared.MiniCompany", {}
                    )
                    logo_data = comp.get("logo", {}).get(
                        "com.linkedin.common.VectorImage", {}
                    )
                    logo_url = ""
                    if logo_data.get("rootUrl") and logo_data.get("artifacts"):
                        logo_url = logo_data["rootUrl"] + logo_data["artifacts"][0].get(
                            "fileIdentifyingUrlPathSegment", ""
                        )
                    following_companies.append(
                        {
                            "name": comp.get("name", ""),
                            "url": f"https://www.linkedin.com/company/{comp.get('universalName', '')}",
                            "logo": logo_url,
                            "followers": followers,
                        }
                    )
                elif "MiniGroup" in str(entity):
                    grp = entity.get(
                        "com.linkedin.voyager.entities.shared.MiniGroup", {}
                    )
                    following_groups.append(
                        {
                            "name": grp.get("groupName", ""),
                            "description": (grp.get("groupDescription", "") or "")[
                                :100
                            ],
                            "followers": followers,
                        }
                    )
                elif "MiniProfile" in str(entity):
                    prof = entity.get(
                        "com.linkedin.voyager.identity.shared.MiniProfile", {}
                    )
                    following_people.append(
                        {
                            "name": f"{prof.get('firstName', '')} {prof.get('lastName', '')}".strip(),
                            "occupation": prof.get("occupation", ""),
                            "url": f"https://www.linkedin.com/in/{prof.get('publicIdentifier', '')}",
                            "followers": followers,
                        }
                    )
            except Exception:
                continue

        # Graphic array
        graphic = []

        # Skills — empty defaults (source endpoint removed)
        skill_tmp = {"name": "", "value": 100, "children": []}

        # Profile array
        profile = []
        profile.append({"firstName": first_name})
        profile.append({"lastName": last_name})
        profile.append({"organization": fields["headline"]})
        profile.append({"location": fields["location"]})

        # Geolocation
        if fields["location"]:
            try:
                geo_item = location_geo(fields["location"])
                logger.info(
                    "iKy - LinkedIn: geo result for '%s': %s",
                    fields["location"],
                    geo_item,
                )
                if geo_item:
                    profile.append({"geo": geo_item})
            except Exception as exc:
                logger.warning(
                    "iKy - LinkedIn: geo lookup failed for '%s': %s",
                    fields["location"],
                    exc,
                )

        # Photos
        photo_urls = fields["photo_urls"]
        if photo_urls:
            photo_item = {
                "name-node": "Linkedin",
                "title": "Linkedin",
                "subtitle": "",
                "picture": photo_urls[0],
                "link": "Photos",
            }
            profile.append({"photos": [photo_item]})

        # Presence
        presence = []
        presence.append(
            {
                "name": "Linkedin",
                "children": [
                    {
                        "name": "following",
                        "value": following_view.get("paging", {}).get("total", ""),
                    },
                ],
            }
        )
        profile.append({"presence": presence})

        # Raw data (updated to reflect HTML-based extraction)
        raw = []
        raw.append({"code": 0})
        raw.append({"profile_fields": fields})
        raw.append({"recommend_received": recommend_received})
        raw.append({"recommend_given": recommend_given})
        raw.append({"following_view": following_view})

        total.append({"raw": raw})

        graphic.append({"social": socialp})
        graphic.append({"skills": skill_tmp})
        graphic.append({"certificationView": []})
        graphic.append({"positionGroupView": []})
        graphic.append({"users": users})
        graphic.append(
            {
                "following": {
                    "companies": following_companies,
                    "groups": following_groups,
                    "people": following_people,
                }
            }
        )

        total.append({"graphic": graphic})
        total.append({"profile": profile})
        total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_linkedin
t_linkedin = p_linkedin


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query LinkedIn for a username")
    parser.add_argument("username", help="LinkedIn username to look up")
    args = parser.parse_args()

    result = t_linkedin(args.username, "Initial")
    output(result)
