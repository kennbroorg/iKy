#!/usr/bin/env python

import re

from geopy.geocoders import Nominatim


def location_geo(location, time=""):
    geolocator = Nominatim(user_agent="iKy")
    try:
        latlong = geolocator.geocode(location)
    except Exception:
        latlong = False

    if latlong:
        return {
            "Caption": latlong.raw["display_name"],
            "Accessability": latlong.raw["class"],
            "Latitude": latlong.latitude,
            "Longitude": latlong.longitude,
            "Name": latlong.address,
            "Time": time,
        }
    else:
        return False


def extract_hashtags(text):
    hashtags = []
    regex = r"#[a-zA-Z0-9_]+"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        if match.group() != "":
            hashtags.append(match.group().strip().replace("#", ""))
    return hashtags


def extract_mentions(text):
    mentions = []
    regex = r"^|[^\w]@([\w\_\.]+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        if match.group() != "":
            mentions.append(match.group().strip().replace("@", ""))
    return mentions


def extract_url(text):
    urls = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?([\w\-\.\/])*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        urls.append({"url": match.group()})
    return urls


def extract_mails(text):
    mails = []
    regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        mails.append({"email": match.group()})
    return mails


def extract_url_linkedin(text):
    tasks = []
    # regex = r"((http(s)?(\:\/\/))+(www\.)?(linkedin)*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    regex = r"http[s]?\:\/\/+www\.?linkedin*\.[a-zA-Z]{2,3}\/?\/in\/([^\s\b\n|]*[^.,;:\?\!\@\^\$ -])\/"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "linkedin", "param": match.group(1)})
    return tasks


def extract_url_instagram(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(instagram)(\.[a-zA-Z]{2,3}\/?))(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "instagram", "param": match.group(8)})
    return tasks


def extract_url_twitter(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(twitter)(\.[a-zA-Z]{2,3}\/?))(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "twitter", "param": match.group(8)})
    return tasks


def extract_url_tiktok(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(tiktok)(\.[a-zA-Z]{2,3}\/?))(@)?(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "tiktok", "param": match.group(9)})
    return tasks


def extract_url_github(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(github)(\.[a-zA-Z]{2,3}\/?))(@)?(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github", "param": match.group(9)})
    return tasks


def extract_url_githubio(text):
    tasks = []
    regex = r"http[s]?\:\/\/+(\w+)\.github.io"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github", "param": match.group(1)})
    return tasks


def extract_github(text):
    tasks = []
    regex = r"(?i)github(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github", "param": match.group(4)})
    return tasks


def extract_tiktok(text):
    tasks = []
    regex = r"(?i)tiktok(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "tiktok", "param": match.group(4)})
    return tasks


def extract_twitter(text):
    tasks = []
    regex = r"(?i)twitter(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "twitter", "param": match.group(4)})
    return tasks


def extract_instagram(text):
    tasks = []
    regex = r"(?i)instagram(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "instagram", "param": match.group(4)})
    return tasks


def extract_linkedin(text):
    tasks = []
    regex = r"(?i)linkedin(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for _matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "linkedin", "param": match.group(4)})
    return tasks


def analize_rrss(text):
    analized = {}

    hashtags = extract_hashtags(text)
    analized["hashtags"] = hashtags
    mentions = extract_mentions(text)
    analized["mentions"] = mentions
    urls = extract_url(text)
    analized["url"] = urls
    mails = extract_mails(text)
    analized["email"] = mails
    tasks_temp = []
    tasks_temp.append(extract_url_linkedin(text))
    tasks_temp.append(extract_url_instagram(text))
    tasks_temp.append(extract_url_twitter(text))
    tasks_temp.append(extract_url_tiktok(text))
    tasks_temp.append(extract_url_github(text))
    tasks_temp.append(extract_url_githubio(text))
    tasks_temp.append(extract_github(text))
    tasks_temp.append(extract_twitter(text))
    tasks_temp.append(extract_tiktok(text))
    tasks_temp.append(extract_instagram(text))
    tasks_temp.append(extract_linkedin(text))

    # Flatten and deduplicate: both extract_url_* and extract_*
    # can match the same user for a platform, producing duplicate
    # Celery tasks. Keep only one task per (module, param) pair.
    seen: set[tuple[str, str]] = set()
    tasks = []
    for task in (val for sublist in tasks_temp for val in sublist):
        key = (task["module"], task["param"])
        if key not in seen:
            seen.add(key)
            tasks.append(task)

    analized["tasks"] = tasks

    return analized


def name_match(names, data):
    min_matching = max(1, len(names) - 1)
    matchs = 0
    for name in names:
        if name in data:
            matchs = matchs + 1
    return matchs >= min_matching


def _extract_user_default(match):
    """Standard username extraction: group 4, split on / and ?."""
    raw = match.group(5)
    user = raw.split("/")[0] if "/" in raw else raw
    if "?" in user:
        user = user.split("?")[0]
    return user


def _extract_user_twitter(match):
    """Twitter: standard extraction plus %40 decode."""
    user = _extract_user_default(match)
    return user.replace("%40", "")


def _extract_user_facebook(match):
    """Facebook: handle /public/ URLs.

    NOTE: The original code tried ``match.groups()[6]`` for "public"
    URLs, but the regex only captures 5 groups so that would always
    raise IndexError.  We preserve the intent by returning an empty
    string for "/public/" paths (the URL format changed long ago).
    """
    raw = match.group(5)
    if "public" in raw:
        return ""
    user = raw.split("/")[0] if "/" in raw else raw
    if "?" in user:
        user = user.split("?")[0]
    return user


def _extract_user_strip(match):
    """Pinterest / TikTok: strip slashes, skip /pin/ paths."""
    raw = match.group(5)
    stripped = raw.strip("/")
    if "/" in stripped:
        user = raw.split("/")[0]
    elif "/pin/" not in stripped:
        user = stripped
    else:
        user = ""
    if "?" in user:
        user = user.split("?")[0]
    return user


def _extract_user_keybase(match):
    """Keybase: split on / only, no ? cleanup."""
    raw = match.group(5)
    return raw.split("/")[0] if "/" in raw else raw


# Each name-extraction rule: (regex_pattern, group_index_for_name).
# A platform may list multiple rules; all matching rules append names.
_NAME_RULES: dict[str, list[tuple[str, int]]] = {
    "twitter": [
        (r"^(Media Tweets by )?(.*)\(@(.*)\) \| Twitter", 2),
        (r"^(.*) on Twitter: (.*)$", 1),
    ],
    "github": [(r"(.*)\((.*)\) · GitHub", 2)],
    "instagram": [(r"(.*)\((.*)\)(.*)?Instagram(.*)?", 1)],
    "linkedin": [(r"^(.*?) \- (.*)", 1)],
    "facebook": [(r"^(.*?)( News - Home)? \| (.*)", 1)],
    "pinterest": [(r"^(.*?) \((.*)\)(.*)?Pinterest(.*)?$", 1)],
    "tiktok": [(r"^(.*) \(@(\w+)\) Official TikTok .*", 1)],
}

# Platform configs for the URL-parsing loop inside simple_analysis.
# Fields:
#   rrss          - social-network identifier
#   url_pattern   - regex matched against data[1] (the URL)
#   extract_user  - callable(match) -> username string
#   user_guard    - optional callable(user) -> bool; if it returns
#                   False the platform is skipped (linkedin dash rule)
_PLATFORM_CONFIGS = [
    {
        "rrss": "twitter",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/\w+\.|https:\/\/\w+\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(twitter+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/(\w+)"
        ),
        "extract_user": _extract_user_twitter,
    },
    {
        "rrss": "github",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/\w+\.|https:\/\/\w+\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(github+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/(\w+)"
        ),
        "extract_user": _extract_user_default,
    },
    {
        "rrss": "instagram",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/www\.|https:\/\/www\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(instagram+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/([^p].*?)(%3|\/)(.*)"
        ),
        "extract_user": _extract_user_default,
    },
    {
        "rrss": "keybase",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/www\.|https:\/\/www\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(keybase+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/(\w+)"
        ),
        "extract_user": _extract_user_keybase,
    },
    {
        "rrss": "linkedin",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/www\.|https:\/\/www\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(linkedin+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/in\/?\/(\w+)"
        ),
        "extract_user": _extract_user_default,
        "user_guard": lambda u: u.count("-") < 2,
    },
    {
        "rrss": "facebook",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/\w+\.|https:\/\/\w+\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]?"
            r"(facebook+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/(\w+)"
        ),
        "extract_user": _extract_user_facebook,
    },
    {
        "rrss": "pinterest",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/www\.|https:\/\/www\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(pinterest+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/(.*?)(%3|\/|&)(.*)"
        ),
        "extract_user": _extract_user_strip,
    },
    {
        "rrss": "tiktok",
        "url_pattern": (
            r"^(https:\/\/www.google.com\/url\?q=|)"
            r"(http:\/\/www\.|https:\/\/www\."
            r"|http:\/\/|https:\/\/)?[a-z0-9\.]*?"
            r"(tiktok+)\.[a-z]{2,5}"
            r"(:[0-9]{1,5})?\/%40(\w+)"
        ),
        "extract_user": _extract_user_strip,
    },
]


def simple_analysis(source, type_s, username, data, output):
    """
    Social Networks :
        - twitter
        - github
        - instagram
        - keybase
        - linkedin
        - facebook
        - pinterest
        - tiktok
    TODO :
        - gitlab
        - tinder
        - bitbucket
        - reddit
        - youtube
        - twitch
    """
    # Resolve
    # https://www.facebook.com/public/Jezer-Ferreira
    # https://www.instagram.com/p/BtRNU3vlf1I/ (Ignore)
    # Initialize
    urls = output.get("urls", [])
    usernames = output.get("usernames", [])
    names = output.get("names", [])
    social = output.get("social", [])
    users = output.get("users", [])
    hashtags = output.get("hashtags", [])
    emails = output.get("emails", [])

    for cfg in _PLATFORM_CONFIGS:
        rrss = cfg["rrss"]
        url_match = re.match(cfg["url_pattern"], data[1])
        if not url_match:
            continue

        platform_user = cfg["extract_user"](url_match)

        # Optional guard (e.g. linkedin rejects users with >= 2 dashes)
        guard = cfg.get("user_guard")
        if guard and not guard(platform_user):
            continue

        usernames.append(
            {
                "source": source,
                "type": type_s,
                "usernames": platform_user,
                "rrss": rrss,
            }
        )

        # Extract display name from the page title (data[0]).
        # Some platforms have multiple title patterns (e.g. twitter).
        platform_name = ""
        for pattern, group_idx in _NAME_RULES.get(rrss, []):
            name_match = re.match(pattern, data[0])
            if name_match:
                platform_name = name_match.group(group_idx).strip()
                names.append(
                    {
                        "source": source,
                        "type": type_s,
                        "name": platform_name,
                        "rrss": rrss,
                    }
                )

        social.append(
            {
                "source": source,
                "type": type_s,
                "name": platform_name,
                "user": platform_user,
                "rrss": rrss,
            }
        )

    if username in data[1]:
        urls.append(data[1])

    # Hashtags and emails
    s_tags = re.findall(r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", data[0])
    s_tags = s_tags + re.findall(r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", data[2])
    # s_email = re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[0])
    s_email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}", data[0])
    # s_email = s_email + re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[2])
    s_email = s_email + re.findall(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}", data[2]
    )
    s_user = re.findall(r"(\@[\w\-]+)", data[0])
    s_user = s_user + re.findall(r"(\@[\w\-]+)", data[2])

    if s_tags:
        for h in s_tags:
            hashtags.append({"label": h})
    if s_email:
        for e in s_email:
            emails.append({"label": e})
    if s_user:
        for u in s_user:
            users.append({"label": u})

    output["urls"] = urls
    output["usernames"] = usernames
    output["names"] = names
    output["social"] = social
    output["users"] = users
    output["emails"] = emails
    output["hashtags"] = hashtags

    return output


def deep_analysis(names, usernames, searcher, data, output):
    # Initialize
    urls = output.get("urls", [])
    search = output.get("search", [])
    rawresult = output.get("rawresult", [])

    if searcher == "google":
        icon = "fab fa-google"
    elif searcher == "yahoo":
        icon = "fab fa-yahoo"
    elif searcher == "bing":
        icon = "fab fa-windows"
    elif searcher == "duckduckgo":
        icon = "fas fa-kiwi-bird"
    elif searcher == "yandex":
        icon = "fab fa-yandex-international"
    elif searcher == "baidu":
        icon = "fas fa-paw"
    elif searcher == "dorks":
        icon = "fas fa-searchengin"
    else:
        icon = "fas fa-search"

    # Build a unique title that includes the searcher name, so that
    # the d3 graph (which uses title as a cache key) keeps separate
    # nodes for the same headline coming from different search engines.
    unique_title = f"{data[0]} [{searcher}]"

    rawresult_item = {
        "name-node": "References",
        "title": unique_title,
        "subtitle": "",
        "icon": icon,
        "simple": data[0],
        "url": data[1],
        "desc": data[2],
        "link": searcher,
    }
    rawresult.append(rawresult_item)

    search_included = False
    # Evaluate usernames in urls
    for user in usernames:
        if user in data[1]:
            if data[1] not in urls:
                urls.append(data[1])
                output["urls"] = urls

            search_included = True
            search_item = {
                "name-node": "References",
                "title": unique_title,
                "subtitle": "",
                "icon": icon,
                "help": "Title : "
                + data[0]
                + "\nURL : "
                + data[1]
                + "\nDesc : "
                + data[2],
                "simple": data[0],
                "url": data[1],
                "desc": data[2],
                "link": searcher,
            }
            search.append(search_item)

    # Evaluate names in urls
    if not search_included:
        # Title
        if name_match(names, data[0]):
            search_included = True
            search_item = {
                "name-node": "References",
                "title": unique_title,
                "subtitle": "",
                "icon": icon,
                "help": "Title : "
                + data[0]
                + "\nURL : "
                + data[1]
                + "\nDesc : "
                + data[2],
                "simple": data[0],
                "url": data[1],
                "desc": data[2],
                "link": searcher,
            }
            search.append(search_item)
        # Url (This makes no sense)
        if not search_included and name_match(names, data[1]):
            search_included = True
            search_item = {
                "name-node": "References",
                "title": unique_title,
                "subtitle": "",
                "icon": icon,
                "help": "Title : "
                + data[0]
                + "\nURL : "
                + data[1]
                + "\nDesc : "
                + data[2],
                "simple": data[0],
                "url": data[1],
                "desc": data[2],
                "link": searcher,
            }
            search.append(search_item)
        # Desc
        if not search_included and name_match(names, data[2]):
            search_included = True
            search_item = {
                "name-node": "References",
                "title": unique_title,
                "subtitle": data[1],
                "icon": icon,
                "help": "Title : "
                + data[0]
                + "\nURL : "
                + data[1]
                + "\nDesc : "
                + data[2],
                "simple": data[0],
                "url": data[1],
                "desc": data[2],
                "link": searcher,
            }
            search.append(search_item)

    output["rawresult"] = rawresult
    output["search"] = search
    return output
