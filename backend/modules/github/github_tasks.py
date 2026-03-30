#!/usr/bin/env python

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
from factories.iKy_functions import analize_rrss, location_geo
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)

# Icon mapping for known social providers
SOCIAL_ICON_MAP = {
    "twitter": "fab fa-twitter",
    "linkedin": "fab fa-linkedin",
    "instagram": "fab fa-instagram",
    "facebook": "fab fa-facebook",
    "youtube": "fab fa-youtube",
    "mastodon": "fab fa-mastodon",
    "npm": "fab fa-npm",
    "twitch": "fab fa-twitch",
    "reddit": "fab fa-reddit",
}

# Providers that iKy has modules for (trigger chained tasks)
TASK_PROVIDERS = {"twitter", "instagram", "linkedin"}


def find_repos_from_username(session, username):
    safe_user = quote(username, safe="")
    response = session.get(
        f"https://api.github.com/users/{safe_user}/repos?per_page=100&sort=pushed",
        timeout=30,
    )
    repos_data = response.json()
    if not isinstance(repos_data, list):
        return []
    return [r["name"] for r in repos_data if not r.get("fork", True)]


def find_email_from_contributor(session, username, repo, contributor):
    response = session.get(
        f"https://github.com/{username}/{repo}/commits?author={contributor}",
        timeout=30,
    )
    latest_commit = re.search(rf'href="/{username}/{repo}/commit/(.*?)"', response.text)
    latest_commit = latest_commit.group(1) if latest_commit else "dummy"
    commit_details = session.get(
        f"https://github.com/{username}/{repo}/commit/{latest_commit}.patch",
        timeout=30,
    )
    email = re.search(r"<(.*)>", commit_details.text)
    if email:
        return email.group(1)
    return None


def find_email_from_username(session, username):
    repos = find_repos_from_username(session, username)
    for repo in repos:
        email = find_email_from_contributor(session, username, repo, username)
        if email:
            return email
    return False


def _parse_contribution_calendar(html_content: bytes) -> list:
    """Parse GitHub contribution calendar HTML fragment.

    Returns a list of dicts: [{"date": "YYYY-MM-DD", "level": int}, ...]
    where level 0 = no contributions, 4 = max contributions.

    Raises ValueError if the expected table structure is not found.
    """
    html_doc = BeautifulSoup(html_content, "html.parser")
    table = html_doc.find(
        "table", class_=lambda c: c and "ContributionCalendar-grid" in c
    )
    if table is None:
        raise ValueError("ContributionCalendar-grid table not found")
    cells = table.find_all("td", attrs={"data-date": True, "data-level": True})
    if not cells:
        raise ValueError("No contribution calendar cells found")
    return [{"date": td["data-date"], "level": int(td["data-level"])} for td in cells]


@iky_task(module_name="github", dev_mode_sleep=15)
def p_github(email, from_m="Initial"):
    """Task of Celery that get info from github"""

    # Code
    username = email.split("@")[0] if "@" in email else email

    safe_user = quote(username, safe="")

    session = requests.Session()

    req = session.get(f"https://api.github.com/users/{safe_user}", timeout=30)
    logger.debug(req.json())

    if req.json().get("message", "") == "Not Found":
        raise Exception("iKy - User not found")

    # Fetch contribution calendar from the correct fragment endpoint
    cal_headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://github.com/{username}",
    }
    cal_url = (
        f"https://github.com/{username}"
        f"?action=show&controller=profiles&tab=contributions&user_id={username}"
    )
    cal_resp = session.get(cal_url, headers=cal_headers, timeout=30)

    try:
        cal_actual = _parse_contribution_calendar(cal_resp.content)
    except Exception as exc:
        logger.warning(f"Contribution calendar scraping failed: {exc}")
        cal_actual = ""

    # Raw Array
    raw_node = json.loads(req.text)

    # Get login
    try:
        login = raw_node["login"]
    except Exception:
        raise Exception("User not found") from None

    # Get email
    if ("email" in raw_node) and (raw_node["email"] is not None):
        email_github = raw_node["email"]
    else:
        email_github = find_email_from_username(session, login)

    # Get twitter account
    if ("twitter_username" in raw_node) and (raw_node["twitter_username"] is not None):
        twitter_username = raw_node["twitter_username"]
    else:
        twitter_username = False

    # --- New endpoints: per-endpoint graceful degradation ---

    # Social accounts
    social_accounts_data = []
    try:
        sa_resp = session.get(
            f"https://api.github.com/users/{safe_user}/social_accounts", timeout=30
        )
        sa_resp.raise_for_status()
        social_accounts_data = sa_resp.json()
        if not isinstance(social_accounts_data, list):
            social_accounts_data = []
    except Exception as exc:
        logger.warning(f"social_accounts fetch failed: {exc}")

    # Orgs
    orgs_data = []
    try:
        orgs_resp = session.get(
            f"https://api.github.com/users/{safe_user}/orgs", timeout=30
        )
        orgs_resp.raise_for_status()
        orgs_data = orgs_resp.json()
        if not isinstance(orgs_data, list):
            orgs_data = []
    except Exception as exc:
        logger.warning(f"orgs fetch failed: {exc}")

    # Public SSH keys
    keys_data = []
    try:
        keys_resp = session.get(
            f"https://api.github.com/users/{safe_user}/keys", timeout=30
        )
        keys_resp.raise_for_status()
        keys_data = keys_resp.json()
        if not isinstance(keys_data, list):
            keys_data = []
    except Exception as exc:
        logger.warning(f"keys fetch failed: {exc}")

    # Repos: already fetched implicitly via find_email_from_username — fetch
    # explicitly here for enrichment (cached by Session TCP reuse)
    repos_raw = []
    try:
        repos_resp = session.get(
            f"https://api.github.com/users/{safe_user}/repos?per_page=100&sort=pushed",
            timeout=30,
        )
        repos_resp.raise_for_status()
        repos_raw = repos_resp.json()
        if not isinstance(repos_raw, list):
            repos_raw = []
    except Exception as exc:
        logger.warning(f"repos fetch failed: {exc}")

    # Gists
    gists_data = []
    try:
        gists_resp = session.get(
            f"https://api.github.com/users/{safe_user}/gists", timeout=30
        )
        gists_resp.raise_for_status()
        gists_data = gists_resp.json()
        if not isinstance(gists_data, list):
            gists_data = []
    except Exception as exc:
        logger.warning(f"gists fetch failed: {exc}")

    # Total
    total = []
    total.append({"module": "github"})
    total.append({"param": username})
    # Evaluates the module that executed the task and set validation
    if from_m == "Initial":
        total.append({"validation": "no"})
    else:
        total.append({"validation": "soft"})

    if ("message" not in raw_node) or (raw_node["message"] != "Not Found"):
        # Graphic Array
        graphic = []

        # Profile Array
        presence = []
        profile = []

        # Timeline Array
        timeline = []

        # Gather Array
        gather = []

        # Tasks Array
        tasks = []

        link = "Github"
        gather_item = {
            "name-node": "Github",
            "title": "Github",
            "subtitle": "",
            "icon": "fab fa-github",
            "link": link,
        }
        gather.append(gather_item)

        if email_github:
            gather_item = {
                "name-node": "Gitemail",
                "title": "Git Email",
                "subtitle": email_github,
                "icon": "fas fa-at",
                "link": link,
            }
            profile_item = {"email": email_github}
            profile.append(profile_item)
            gather.append(gather_item)
        if "name" in raw_node:
            gather_item = {
                "name-node": "Gitname",
                "title": "Git Name",
                "subtitle": raw_node["name"],
                "icon": "fas fa-user",
                "link": link,
            }
            profile_item = {"name": raw_node["name"]}
            profile.append(profile_item)
            gather.append(gather_item)
        if email_github:
            gather_item = {
                "name-node": "GitEmail",
                "title": "Email",
                "subtitle": email_github,
                "icon": "fas fa-envelope",
                "link": link,
            }
            gather.append(gather_item)
            profile_item = {"email": raw_node.get("email")}
            profile.append(profile_item)
        if twitter_username:
            gather_item = {
                "name-node": "GitTwitter",
                "title": "Twitter",
                "subtitle": twitter_username,
                "icon": "fab fa-twitter",
                "link": link,
            }
            gather.append(gather_item)
            tasks.append({"module": "twitter", "param": twitter_username})
        if ("company" in raw_node) and (raw_node["company"] is not None):
            gather_item = {
                "name-node": "GitCompany",
                "title": "Company",
                "subtitle": raw_node["company"],
                "icon": "fas fa-building",
                "link": link,
            }
            gather.append(gather_item)
            profile_item = {"organization": raw_node["company"]}
            profile.append(profile_item)
        if (
            ("blog" in raw_node)
            and (raw_node["blog"] is not None)
            and (raw_node["blog"] != "")
        ):
            gather_item = {
                "name-node": "GitBlog",
                "title": "Blog",
                "subtitle": raw_node["blog"],
                "icon": "fas fa-globe",
                "link": link,
            }
            gather.append(gather_item)
            profile.append(
                {
                    "social": [
                        {
                            "name": "Blog",
                            "url": raw_node["blog"],
                            "icon": "fas fa-globe",
                            "source": "Github",
                            "username": username,
                        }
                    ]
                }
            )
        if ("bio" in raw_node) and (raw_node["bio"] is not None):
            gather_item = {
                "name-node": "GitBio",
                "title": "Bio",
                "subtitle": raw_node["bio"],
                "icon": "fas fa-heart",
                "link": link,
            }
            gather.append(gather_item)
            profile.append({"bio": raw_node["bio"]})
            analyze = analize_rrss(raw_node["bio"])
            for item in analyze:
                if item == "url":
                    for i in analyze["url"]:
                        profile.append(i)
                if item == "tasks":
                    for i in analyze["tasks"]:
                        tasks.append(i)

        # hireable field
        hireable_val = raw_node.get("hireable")
        if hireable_val is not None:
            gather_item = {
                "name-node": "GitHireable",
                "title": "Hireable",
                "subtitle": hireable_val,
                "icon": "fas fa-briefcase",
                "link": link,
            }
            gather.append(gather_item)
            profile.append({"hireable": hireable_val})

        # social_accounts → gather nodes + profile.social + tasks
        for sa in social_accounts_data:
            provider = sa.get("provider", "").lower()
            sa_url = sa.get("url", "")
            if not sa_url:
                continue
            icon = SOCIAL_ICON_MAP.get(provider, "fas fa-link")
            provider_title = provider.capitalize()
            node_name = f"GitSocial_{provider}"
            # Extract username from URL (last path segment)
            sa_username = sa_url.rstrip("/").split("/")[-1] if sa_url else sa_url
            gather_item = {
                "name-node": node_name,
                "title": provider_title,
                "subtitle": sa_url,
                "icon": icon,
                "link": link,
            }
            gather.append(gather_item)
            profile.append(
                {
                    "social": [
                        {
                            "name": provider_title,
                            "url": sa_url,
                            "icon": icon,
                            "source": "Github",
                            "username": sa_username,
                        }
                    ]
                }
            )
            if provider in TASK_PROVIDERS:
                tasks.append({"module": provider, "param": sa_username})

        # Language stats from repos
        if repos_raw:
            lang_counts: Counter = Counter()
            for r in repos_raw:
                lang = r.get("language")
                if lang:
                    lang_counts[lang] += 1
            if lang_counts:
                gather_item = {
                    "name-node": "GitLanguages",
                    "title": "Languages",
                    "subtitle": dict(lang_counts.most_common()),
                    "icon": "fas fa-code",
                    "link": link,
                }
                gather.append(gather_item)

        if "public_repos" in raw_node:
            gather_item = {
                "name-node": "GitRepos",
                "title": "Repos",
                "subtitle": raw_node["public_repos"],
                "icon": "fas fa-folder-open",
                "link": link,
            }
            gather.append(gather_item)
        if "public_gists" in raw_node:
            gather_item = {
                "name-node": "GitGists",
                "title": "Gists",
                "subtitle": raw_node["public_gists"],
                "icon": "fas fa-code",
                "link": link,
            }
            gather.append(gather_item)
        if "followers" in raw_node:
            gather_item = {
                "name-node": "GitFollowers",
                "title": "Followers",
                "subtitle": raw_node["followers"],
                "icon": "fas fa-users",
                "link": link,
            }
            gather.append(gather_item)
        if "following" in raw_node:
            gather_item = {
                "name-node": "GitFollowing",
                "title": "Following",
                "subtitle": raw_node["following"],
                "icon": "fas fa-users",
                "link": link,
            }
            gather.append(gather_item)
        if "id" in raw_node:
            gather_item = {
                "name-node": "GitId",
                "title": "Id",
                "subtitle": raw_node["id"],
                "icon": "fas fa-info",
                "link": link,
            }
            gather.append(gather_item)
        if "avatar_url" in raw_node:
            gather_item = {
                "name-node": "GitAvatar",
                "title": "Avatar",
                "picture": raw_node["avatar_url"],
                "subtitle": "",
                "link": link,
            }
            gather.append(gather_item)
            profile_item = {
                "photos": [{"picture": raw_node["avatar_url"], "title": "Github"}]
            }
            profile.append(profile_item)
        if ("location" in raw_node) and (raw_node["location"] is not None):
            profile_item = {"location": raw_node["location"]}
            profile.append(profile_item)
            loc = location_geo(raw_node["location"])
            logger.debug(f"LOC: {raw_node['location']} - {loc}")
            if loc:
                loc_item = {
                    "Caption": "Github",
                    "Accessibility": "",
                    "Latitude": loc["Latitude"],
                    "Longitude": loc["Longitude"],
                    "Name": loc["Caption"],
                    "Time": "",
                }
                profile.append({"geo": loc_item})
        if ("created_at" in raw_node) and (raw_node["created_at"] is not None):
            ctime = datetime.strptime(raw_node["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            timeline_item = {
                "date": ctime.strftime("%Y/%m/%d %H:%M:%S"),
                "action": "Github : Create Account",
                "icon": "fab fa-github",
            }
            timeline.append(timeline_item)
        if ("updated_at" in raw_node) and (raw_node["updated_at"] is not None):
            mtime = datetime.strptime(raw_node["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            timeline_item = {
                "date": mtime.strftime("%Y/%m/%d %H:%M:%S"),
                "action": "Github : Update Account",
                "icon": "fab fa-github",
            }
            timeline.append(timeline_item)

        # SSH key creation dates → timeline
        for key_entry in keys_data:
            created_at = key_entry.get("created_at", "")
            key_str = key_entry.get("key", "")
            key_type = key_str.split()[0] if key_str else "unknown"
            if created_at:
                try:
                    ktime = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                    timeline.append(
                        {
                            "date": ktime.strftime("%Y/%m/%d %H:%M:%S"),
                            "action": f"Github : SSH Key Added ({key_type})",
                            "icon": "fas fa-key",
                        }
                    )
                except ValueError:
                    logger.warning(f"Could not parse SSH key created_at: {created_at}")

        # Repo creation dates (top 5 by stars) → timeline
        if repos_raw:
            top_by_stars = sorted(
                repos_raw,
                key=lambda r: r.get("stargazers_count", 0),
                reverse=True,
            )[:5]
            for repo in top_by_stars:
                repo_created = repo.get("created_at", "")
                repo_name = repo.get("name", "")
                if repo_created and repo_name:
                    try:
                        rtime = datetime.strptime(repo_created, "%Y-%m-%dT%H:%M:%SZ")
                        timeline.append(
                            {
                                "date": rtime.strftime("%Y/%m/%d %H:%M:%S"),
                                "action": f"Github : Created repo '{repo_name}'",
                                "icon": "fab fa-github",
                            }
                        )
                    except ValueError:
                        logger.warning(
                            f"Could not parse repo created_at: {repo_created}"
                        )

        # Gist creation dates → timeline
        for gist in gists_data:
            gist_created = gist.get("created_at", "")
            gist_desc = gist.get("description", "") or "(no description)"
            if gist_created:
                try:
                    gtime = datetime.strptime(gist_created, "%Y-%m-%dT%H:%M:%SZ")
                    timeline.append(
                        {
                            "date": gtime.strftime("%Y/%m/%d %H:%M:%S"),
                            "action": f"Github : Created gist '{gist_desc}'",
                            "icon": "fab fa-github",
                        }
                    )
                except ValueError:
                    logger.warning(f"Could not parse gist created_at: {gist_created}")

        if "followers" in raw_node and "following" in raw_node:
            presence.append(
                {
                    "name": "github",
                    "children": [
                        {"name": "followers", "value": int(raw_node["followers"])},
                        {"name": "following", "value": int(raw_node["following"])},
                    ],
                }
            )
            profile.append({"presence": presence})

        # Merge all social entries into a single {"social": [...]} item.
        # Collect any existing social entries already appended piecemeal, then
        # add the GitHub profile link, and replace them with one merged entry.
        merged_social = []
        profile_without_social = []
        for p_item in profile:
            if "social" in p_item:
                merged_social.extend(p_item["social"])
            else:
                profile_without_social.append(p_item)
        profile = profile_without_social
        social_item = {
            "name": "Github",
            "url": "https://www.github.com/" + username,
            "icon": "fab fa-github",
            "source": "Github",
            "username": username,
        }
        merged_social.append(social_item)
        profile.append({"social": merged_social})

        # Deduplicate tasks: remove entries with the same module+param pair.
        seen_tasks: set[tuple[str, str]] = set()
        deduped_tasks = []
        for t in tasks:
            key = (t.get("module", ""), t.get("param", ""))
            if key not in seen_tasks:
                seen_tasks.add(key)
                deduped_tasks.append(t)
        tasks = deduped_tasks

        # Please, respect the order of items in the total array
        # Because the frontend depend of that (By now)
        total.append({"raw": raw_node})
        graphic.append({"github": gather})
        graphic.append({"cal_actual": cal_actual})
        graphic.append({"cal_previous": ""})

        # New graphic sections — appended after existing ones for backward compat
        if social_accounts_data:
            graphic.append({"social_accounts": social_accounts_data})

        if orgs_data:
            for org in orgs_data:
                org_login = org.get("login", "")
                if org_login:
                    gather_item = {
                        "name-node": f"GitOrg_{org_login}",
                        "title": "Organization",
                        "subtitle": org_login,
                        "icon": "fas fa-users",
                        "link": link,
                    }
                    gather.append(gather_item)
                    profile.append({"organization": org_login})
            graphic.append(
                {
                    "orgs": [
                        {
                            "name": o.get("login", ""),
                            "avatar": o.get("avatar_url", ""),
                            "description": o.get("description", ""),
                            "url": o.get("url", ""),
                        }
                        for o in orgs_data
                    ]
                }
            )

        if keys_data:
            graphic.append(
                {
                    "keys": [
                        {
                            "id": k.get("id"),
                            "key": k.get("key", ""),
                            "created_at": k.get("created_at", ""),
                        }
                        for k in keys_data
                    ]
                }
            )

        if repos_raw:
            top_repos = sorted(
                repos_raw, key=lambda r: r.get("stargazers_count", 0), reverse=True
            )[:10]
            graphic.append(
                {
                    "repos": [
                        {
                            "name": r.get("name", ""),
                            "description": r.get("description", ""),
                            "language": r.get("language", ""),
                            "stars": r.get("stargazers_count", 0),
                            "forks": r.get("forks_count", 0),
                            "topics": r.get("topics", []),
                            "fork": r.get("fork", False),
                        }
                        for r in top_repos
                    ]
                }
            )

            # Aggregate unique topics from all repos
            all_topics = []
            for r in repos_raw:
                for topic in r.get("topics", []):
                    if topic not in all_topics:
                        all_topics.append(topic)
            if all_topics:
                graphic.append({"topics": all_topics})

        if gists_data:
            graphic.append(
                {
                    "gists": [
                        {
                            "description": g.get("description", ""),
                            "created_at": g.get("created_at", ""),
                            "updated_at": g.get("updated_at", ""),
                            "public": g.get("public", True),
                        }
                        for g in gists_data
                    ]
                }
            )

        total.append({"graphic": graphic})
        total.append({"profile": profile})
        total.append({"timeline": timeline})
        total.append({"tasks": tasks})

    return total


# Backward-compatible alias: existing code references t_github
t_github = p_github


def output(data):
    logger.info(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query GitHub for a user")
    parser.add_argument("username", help="GitHub username or email to look up")
    args = parser.parse_args()

    result = t_github(args.username)
    output(result)
