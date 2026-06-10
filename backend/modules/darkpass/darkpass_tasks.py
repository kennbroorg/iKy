#!/usr/bin/env python

import argparse
import json
import random

import requests

# urllib3 warning suppression kept intentionally: TOR .onion hidden
# services use self-signed certificates, so verify=False is expected
# when routing through a SOCKS proxy to the Tor network.
import urllib3
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_task_logger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
]


@iky_task(module_name="darkpass", dev_mode_sleep=2)
def p_darkpass(email, from_m="Initial", proxy="127.0.0.1:9050"):
    """Task of Celery that gets leaked passwords from pwndb via TOR."""

    # Total
    total = []
    total.append({"module": "darkpass"})
    total.append({"param": email})
    # Evaluates the module that executed the task and set validation
    total.append({"validation": "soft" if from_m != "Initial" else "no"})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    # Tor proxy
    session = requests.session()
    session.proxies = {"http": f"socks5h://{proxy}", "https": f"socks5h://{proxy}"}

    url = "http://pwndb2am4tzkvold.onion/"
    username = email
    domain = "%"

    if "@" in email:
        username = email.split("@")[0]
        domain = email.split("@")[1]
        if not username:
            username = "%"

    request_data = {
        "luser": username,
        "domain": domain,
        "luseropr": 1,
        "domainopr": 1,
        "submitform": "em",
    }

    try:
        req = session.post(
            url,
            data=request_data,
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=60,
        )
    except Exception as err:
        raise Exception(
            f"iKy - TOR is not enabled in {proxy} or pwndb is offline ({type(err).__name__})"
        ) from err

    raw_node = {}

    if "Array" in req.text:
        leaks = req.text.split("Array")[1:]
        emails = []

        for leak in leaks:
            leaked_email = ""
            leak_domain = ""
            password = ""
            try:
                leaked_email = leak.split("[luser] =>")[1].split("[")[0].strip()
                leak_domain = leak.split("[domain] =>")[1].split("[")[0].strip()
                password = leak.split("[password] =>")[1].split(")")[0].strip()
            except Exception:
                pass
            if leaked_email and leaked_email != "donate":
                emails.append(
                    {
                        "username": leaked_email,
                        "domain": leak_domain,
                        "password": password,
                    }
                )

        if len(emails) > 0:
            raw_node = {"pass": emails}
        else:
            raw_node = {"status": "No password leaked"}
    else:
        raw_node = {"status": "No password leaked"}

    if raw_node.get("pass", "") != "":
        for passwords in raw_node["pass"]:
            gather_item = {"username": email, "password": passwords["password"]}
            gather.append(gather_item)
            profile_item = {"password": passwords["password"]}
            profile.append(profile_item)

    graphic.append({"darkpass": gather})
    total.append({"raw": raw_node})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_darkpass
t_darkpass = p_darkpass


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query pwndb for leaked passwords via TOR"
    )
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_darkpass(args.email)
    output(result)
