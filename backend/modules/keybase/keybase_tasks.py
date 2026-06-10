#!/usr/bin/env python

import json
import re
import time
from urllib.parse import quote

import requests
from celery.utils.log import get_task_logger
from factories.fontcheat import search_icon_5
from factories.iKy_functions import analize_rrss
from factories.task_wrapper import iky_task
from requests_html import HTMLSession

logger = get_task_logger(__name__)


@iky_task(module_name="keybase", dev_mode_sleep=15)
def p_keybase(username, from_m="Initial"):
    # Code
    safe_user = quote(username, safe="")
    url = f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={safe_user}"
    req = requests.get(url, timeout=30)
    raw_node = json.loads(req.text)

    # Get Followers and Following throw crawling
    url_user = f"https://keybase.io/{safe_user}"
    session = HTMLSession()
    r_html = session.get(url_user, timeout=30)
    follow = r_html.html.find("#profile-tracking-section", first=True)

    following = "Undefined"
    following_num = 0
    try:
        regex = r"Following \(([0-9]*)\)"
        matches = re.finditer(regex, follow.text, re.MULTILINE)
        for match in matches:
            if match.group() != "":
                following = match.group(1)
                following_num = int(following)
    except Exception:
        pass

    followers = "Undefined"
    followers_num = 0
    try:
        regex = r"Followers \(([0-9]*)\)"
        matches = re.finditer(regex, follow.text, re.MULTILINE)
        for match in matches:
            if match.group() != "":
                followers = match.group(1)
                followers_num = int(followers)
    except Exception:
        pass

    # Total
    total = []
    total.append({"module": "keybase"})
    total.append({"param": username})
    # Evaluates the module that executed the task
    if from_m == "Initial":
        total.append({"validation": "no"})
    else:
        total.append({"validation": "soft"})

    if (raw_node["status"]["code"] == 0) and (raw_node["them"][0] is not None):
        raw = raw_node["them"][0]

        # Graphic Array
        graphic = []

        # Profile Array
        profile = []
        social_profile = []

        # Timeline Array
        timeline = []

        # Tasks Array
        tasks = []

        # Devices Array
        devices = []

        # Social Array
        social = []

        # Graph Array
        graph = []

        # Presence Array
        presence = []

        link_graph = "KeybaseGraph"
        graph_item = {
            "name-node": "KeybaseGraph",
            "title": "KeybaseGraphs",
            "subtitle": "",
            "icon": "fab fa-keybase",
            "link": link_graph,
        }
        graph.append(graph_item)

        link_device = "Devices"
        device_item = {
            "name-node": "Devices",
            "title": "Devices",
            "subtitle": "",
            "icon": "fas fa-laptop",
            "link": link_device,
        }
        devices.append(device_item)

        link_social = "KeybaseSocial"
        social_item = {
            "name-node": "KeybaseSocial",
            "title": "KeybaseSocial",
            "subtitle": "",
            "icon": "fas fa-child",
            "link": link_social,
        }
        social.append(social_item)

        graph_item = {
            "name-node": "GraphUsername",
            "title": "Username",
            "subtitle": username,
            "icon": "fas fa-user",
            "link": link_graph,
        }
        graph.append(graph_item)

        graph_item = {
            "name-node": "GraphFollowers",
            "title": "Followers",
            "subtitle": followers,
            "icon": "fas fa-users",
            "link": link_graph,
        }
        graph.append(graph_item)

        graph_item = {
            "name-node": "GraphFollowing",
            "title": "Following",
            "subtitle": following,
            "icon": "fas fa-users",
            "link": link_graph,
        }
        graph.append(graph_item)

        if raw.get("profile", "") != "":
            if raw.get("profile", "").get("full_name", "") != "":
                profile_item = {"name": raw.get("profile", "").get("full_name", "")}
                profile.append(profile_item)
                graph_item = {
                    "name-node": "GraphName",
                    "title": "Name",
                    "subtitle": raw.get("profile", "").get("full_name", ""),
                    "icon": "fas fa-user",
                    "link": link_graph,
                }
                graph.append(graph_item)

            if (raw.get("profile", "").get("location", "") is not None) and (
                raw.get("profile", "").get("location", "") != ""
            ):
                profile_item = {"location": raw.get("profile", "").get("location", "")}
                profile.append(profile_item)
                graph_item = {
                    "name-node": "GraphLocation",
                    "title": "Location",
                    "subtitle": raw.get("profile", "").get("location", ""),
                    "icon": "fas fa-map-marker-alt",
                    "link": link_graph,
                }
                graph.append(graph_item)

            if raw.get("profile", "").get("bio", "") != "":
                profile_item = {"bio": raw.get("profile", "").get("bio", "")}
                profile.append(profile_item)

                analyze = analize_rrss(raw.get("profile", "").get("bio", ""))
                for item in analyze:
                    if item == "url":
                        for i in analyze["url"]:
                            profile.append(i)
                    if item == "tasks":
                        for i in analyze["tasks"]:
                            tasks.append(i)

        if (
            raw.get("pictures", "") != ""
            and raw.get("pictures", "").get("primary", "") != ""
            and raw.get("pictures", "").get("primary", "").get("url", "") != ""
        ):
            profile_item = {
                "photos": [
                    {
                        "picture": raw.get("pictures", "")
                        .get("primary", "")
                        .get("url", ""),
                        "title": "Keybase",
                    }
                ]
            }
            profile.append(profile_item)

            graph_item = {
                "name-node": "KeyAvatar",
                "title": "Avatar",
                "picture": raw.get("pictures", "").get("primary", "").get("url", ""),
                "subtitle": "",
                "link": link_graph,
            }
            graph.append(graph_item)

        if raw.get("basics", "") != "":
            if raw.get("basics", "").get("ctime", "") != "":
                ctime = time.strftime(
                    "%Y/%m/%d %H:%M:%S",
                    time.gmtime(raw.get("basics", "").get("ctime")),
                )
                timeline_item = {
                    "action": "Keybase: Create Account",
                    "date": ctime,
                    "icon": "fas fa-key",
                }
                timeline.append(timeline_item)

                graph_item = {
                    "name-node": "GraphJoin",
                    "title": "Join Date",
                    "subtitle": ctime,
                    "icon": "fas fa-calendar-check",
                    "link": link_graph,
                }
                graph.append(graph_item)

            if raw.get("basics", "").get("mtime", "") != "":
                mtime = time.strftime(
                    "%Y/%m/%d %H:%M:%S",
                    time.gmtime(raw.get("basics", "").get("mtime")),
                )
                timeline_item = {
                    "action": "Keybase : Update Account",
                    "date": mtime,
                    "icon": "fas fa-key",
                }
                timeline.append(timeline_item)

            # Additive: track_version (cryptographic trust indicator)
            track_version = raw.get("basics", {}).get("track_version")
            if track_version is not None:
                graph_item = {
                    "name-node": "GraphTrackers",
                    "title": "Trackers",
                    "subtitle": str(track_version),
                    "icon": "fas fa-user-check",
                    "link": link_graph,
                }
                graph.append(graph_item)

        for dev in raw.get("devices", ""):
            fa_icon = search_icon_5(raw.get("devices").get(dev).get("type", ""))
            if fa_icon is None:
                fa_icon = search_icon_5("question")

            device_item = {
                "name-node": raw.get("devices").get(dev).get("type", ""),
                "title": raw.get("devices").get(dev).get("type", ""),
                "subtitle": "Name : " + raw.get("devices").get(dev).get("name", ""),
                "icon": fa_icon,
                "link": link_device,
            }
            devices.append(device_item)

        # Additive: Signature chain length (sigs.last.seqno = activity indicator)
        sigs_last = raw.get("sigs", {}).get("last", {}) or {}
        seqno = sigs_last.get("seqno")
        if seqno is not None:
            graph_item = {
                "name-node": "GraphSigChain",
                "title": "Signature Chain",
                "subtitle": str(seqno),
                "icon": "fas fa-link",
                "link": link_graph,
            }
            graph.append(graph_item)

        # Additive: PGP key metadata (public_keys.primary)
        public_keys = raw.get("public_keys", {}) or {}
        pgp_primary = public_keys.get("primary", {}) or {}
        key_fingerprint = pgp_primary.get("key_fingerprint")
        if key_fingerprint:
            profile.append({"key_fingerprint": key_fingerprint})
            graph_item = {
                "name-node": "GraphPGPFingerprint",
                "title": "PGP Fingerprint",
                "subtitle": key_fingerprint,
                "icon": "fas fa-fingerprint",
                "link": link_graph,
            }
            graph.append(graph_item)

        key_bits = pgp_primary.get("key_bits")
        key_algo = pgp_primary.get("key_algo")
        if key_bits is not None:
            algo_name = "RSA" if key_algo == 1 else str(key_algo)
            graph_item = {
                "name-node": "GraphPGPKeyBits",
                "title": "PGP Key",
                "subtitle": f"{algo_name} {key_bits} bits",
                "icon": "fas fa-key",
                "link": link_graph,
            }
            graph.append(graph_item)

        pgp_ctime = pgp_primary.get("ctime")
        if pgp_ctime:
            pgp_ctime_str = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime(pgp_ctime))
            timeline_item = {
                "action": "Keybase: PGP Key Created",
                "date": pgp_ctime_str,
                "icon": "fas fa-fingerprint",
            }
            timeline.append(timeline_item)

        # Additive: PGP public key URL (link only — no key content fetched)
        pgp_key_url = f"https://keybase.io/{username}/pgp_keys.asc"
        profile.append({"pgp_key_url": pgp_key_url})

        # Additive: Signing and encryption key counts (sibkeys / subkeys)
        sibkeys = public_keys.get("sibkeys", {}) or {}
        signing_count = len(sibkeys)
        if signing_count > 0:
            graph_item = {
                "name-node": "GraphSigningKeys",
                "title": "Signing Keys",
                "subtitle": str(signing_count),
                "icon": "fas fa-pen-nib",
                "link": link_graph,
            }
            graph.append(graph_item)

        subkeys = public_keys.get("subkeys", {}) or {}
        encryption_count = len(subkeys)
        if encryption_count > 0:
            graph_item = {
                "name-node": "GraphEncryptionKeys",
                "title": "Encryption Keys",
                "subtitle": str(encryption_count),
                "icon": "fas fa-lock",
                "link": link_graph,
            }
            graph.append(graph_item)

        if raw.get("proofs_summary", "") != "":
            for soc in raw.get("proofs_summary", "").get("all"):
                fa_icon = search_icon_5(soc.get("proof_type"))
                if fa_icon is None:
                    fa_icon = search_icon_5("question")

                social_item = {
                    "name-node": "keybase" + soc.get("proof_type", ""),
                    "title": soc.get("proof_type", ""),
                    "subtitle": soc.get("nametag", ""),
                    "icon": fa_icon,
                    "link": link_social,
                }
                # Additive: include proof state when present
                proof_state = soc.get("state")
                if proof_state is not None:
                    social_item["state"] = proof_state
                # Additive: include proof URLs when present
                human_url = soc.get("human_url")
                if human_url:
                    social_item["url"] = human_url
                proof_url = soc.get("proof_url")
                if proof_url:
                    social_item["proof_url"] = proof_url
                social.append(social_item)

                social_profile_item = {
                    "name": soc.get("proof_type"),
                    "username": soc.get("nametag"),
                    "Source": "Keybase",
                    "icon": fa_icon,
                    "url": soc.get("service_url"),
                }
                social_profile.append(social_profile_item)

                tasks.append(
                    {
                        "module": soc.get("proof_type", "").lower(),
                        "param": soc.get("nametag", ""),
                    }
                )

        # Crypto icon map — fallback to generic "coins" icon for unknown currencies
        _crypto_icons = {
            "bitcoin": "fab fa-btc",
            "ethereum": "fab fa-ethereum",
        }

        # Keybase : TODO : Find an example of webs
        crypto_addresses = raw.get("cryptocurrency_addresses") or {}
        wallets: list[dict[str, str]] = []
        for currency, addresses in crypto_addresses.items():
            if not addresses:
                continue
            fa_crypto_icon = _crypto_icons.get(currency.lower(), "fas fa-coins")
            for address in addresses:
                addr_str = address.get("address", "")
                social_item = {
                    "name-node": f"keybase{currency.upper()}",
                    "title": f"Cryptocurrency ({currency})",
                    "subtitle": addr_str,
                    "icon": fa_crypto_icon,
                    "link": link_social,
                }
                social.append(social_item)
                if addr_str:
                    wallets.append({"currency": currency, "address": addr_str})
        if wallets:
            profile.append({"wallet": wallets})

        presence.append(
            {
                "name": "keybase",
                "children": [
                    {"name": "followers", "value": followers_num},
                    {"name": "following", "value": following_num},
                ],
            }
        )
        profile.append({"presence": presence})

        total.append({"raw": raw_node})
        if len(social) > 1:
            graphic.append({"keysocial": social})
        if len(devices) > 1:
            graphic.append({"devices": devices})
        if len(graph) > 1:
            graphic.append({"keygraph": graph})
        total.append({"graphic": graphic})
        if social_profile:
            profile.append({"social": social_profile})
        if profile:
            total.append({"profile": profile})
        if timeline:
            total.append({"timeline": timeline})

        # Keybase : TODO : Before send task,
        # code the validation for duplicate proccess
        if tasks:
            total.append({"tasks": tasks})

    else:
        total = []
        total.append({"module": "keybase"})
        total.append({"param": username})
        total.append({"validation": "not_used"})

        raw_node = []
        raw_node.append(
            {
                "status": "Fail",
                "reason": "User not found",
                "traceback": "User not found",
            }
        )
        total.append({"raw": raw_node})

    return total


# Backward-compatible alias: existing code references t_keybase
t_keybase = p_keybase
