#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import urllib
import re
import os
from time import time
from requests_futures.sessions import FuturesSession

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_sherlock(username):
    """ Task of Celery that get info from differents sites """

    data_file_path = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "data.json")

    with open(data_file_path, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    raw_node = sherlock(username, data)

    # Total
    total = []
    total.append({'module': 'sherlock'})
    total.append({'param': username})
    total.append({'validation': 'hard'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    # Social
    social = []

    link = "Sherlock"
    gather_item = {"name-node": "Sherlock", "title": username,
                   "subtitle": "", "icon": "fas fa-unlock-alt",
                   "link": link}
    gather.append(gather_item)

    for rrss in raw_node:
        if (raw_node[rrss]["exists"] == 'yes'):
            gather_item = {"name-node": rrss,
                           "title": rrss,
                           "subtitle": raw_node[rrss]["url_user"],
                           "link": link}
            gather.append(gather_item)
            social_item = {"name": rrss,
                           "url": raw_node[rrss]["url_user"],
                           "username": username}
            social.append(social_item)
    profile.append({"social": social})

    # Please, respect the order of items in the total array
    # Because the frontend depend of that (By now)
    total.append({'raw': raw_node})
    # if (len(gather) != 1):
    #     graphic.append({'leaks': gather})
    graphic.append({'sherlock': gather})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


class ElapsedFuturesSession(FuturesSession):
    """
    Extends FutureSession to add a response time metric to each request.

    This is taken (almost) directly from here: https://github.com/ross/requests-futures#working-in-the-background
    """

    def request(self, method, url, hooks={}, *args, **kwargs):
        start = time()

        def timing(r, *args, **kwargs):
            elapsed_sec = time() - start
            r.elapsed = round(elapsed_sec * 1000)

        try:
            if isinstance(hooks['response'], (list, tuple)):
                # needs to be first so we don't time other hooks execution
                hooks['response'].insert(0, timing)
            else:
                hooks['response'] = [timing, hooks['response']]
        except KeyError:
            hooks['response'] = timing

        return super(ElapsedFuturesSession, self).request(method, url, hooks=hooks, *args, **kwargs)


def get_response(request_future, error_type, social_network, verbose=False, retry_no=None, color=True):

    global proxy_list

    try:
        rsp = request_future.result()
        if rsp.status_code:
            return rsp, error_type, rsp.elapsed
    except requests.exceptions.HTTPError as errh:
        print(f'HTTP Error: {errh} - {social_network} - {verbose}')

    # In case our proxy fails, we retry with another proxy.
    except requests.exceptions.ProxyError as errp:
        if retry_no>0 and len(proxy_list)>0:
            #Selecting the new proxy.
            new_proxy = random.choice(proxy_list)
            new_proxy = f'{new_proxy.protocol}://{new_proxy.ip}:{new_proxy.port}'
            print(f'Retrying with {new_proxy}')
            request_future.proxy = {'http':new_proxy,'https':new_proxy}
            get_response(request_future,error_type, social_network, verbose,retry_no=retry_no-1, color=color)
        else:
            print(f'Proxy Error: {errp} - {social_network} - {verbose}')
    except requests.exceptions.ConnectionError as errc:
        print(f'Error Connecting: {errc} - {social_network} - {verbose}')
    except requests.exceptions.Timeout as errt:
        print(f'Error Connecting: {errt} - {social_network} - {verbose}')
    except requests.exceptions.RequestException as err:
        print(f'Error Connecting: {err} - {social_network} - {verbose}')
    return None, "", -1


def sherlock(username, site_data, verbose=False, tor=False, unique_tor=False,
             proxy=None, print_found_only=False, timeout=5, color=True):

    print("Checking username %s\n", username)

    underlying_session = requests.session()
    underlying_request = requests.Request()

    #Limit number of workers to 20.
    #This is probably vastly overkill.
    if len(site_data) >= 20:
        max_workers=20
    else:
        max_workers=len(site_data)

    #Create multi-threaded session for all requests.
    session = ElapsedFuturesSession(max_workers=max_workers,
                                    session=underlying_session)

    # Results from analysis of all sites
    results_total = {}

    # First create futures for all requests. This allows for the requests to run in parallel
    for social_network, net_info in site_data.items():

        # Results from analysis of this specific site
        results_site = {}

        # Record URL of main site
        results_site['url_main'] = net_info.get("urlMain")

        # A user agent is needed because some sites don't return the correct
        # information since they think that we are bots (Which we actually are...)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
        }

        if "headers" in net_info:
            # Override/append any extra headers required by a given site.
            headers.update(net_info["headers"])

        # Don't make request if username is invalid for the site
        regex_check = net_info.get("regexCheck")
        if regex_check and re.search(regex_check, username) is None:
            # No need to do the check at the site: this user name is not allowed.
            if not print_found_only:
                print("%s - Illegal Username Format For This Site!", social_network)

            results_site["exists"] = "illegal"
            results_site["url_user"] = ""
            results_site['http_status'] = ""
            results_site['response_text'] = ""
            results_site['response_time_ms'] = ""
        else:
            # URL of user on site (if it exists)
            url = net_info["url"].format(username)
            results_site["url_user"] = url
            url_probe = net_info.get("urlProbe")
            if url_probe is None:
                # Probe URL is normal one seen by people out on the web.
                url_probe = url
            else:
                # There is a special URL for probing existence separate
                # from where the user profile normally can be found.
                url_probe = url_probe.format(username)

            #If only the status_code is needed don't download the body
            if net_info["errorType"] == 'status_code':
                request_method = session.head
            else:
                request_method = session.get

            if net_info["errorType"] == "response_url":
                # Site forwards request to a different URL if username not
                # found.  Disallow the redirect so we can capture the
                # http status from the original URL request.
                allow_redirects = False
            else:
                # Allow whatever redirect that the site wants to do.
                # The final result of the request will be what is available.
                allow_redirects = True

            # This future starts running the request in a new thread, doesn't block the main thread
            if proxy != None:
                proxies = {"http": proxy, "https": proxy}
                future = request_method(url=url_probe, headers=headers,
                                        proxies=proxies,
                                        allow_redirects=allow_redirects,
                                        timeout=timeout
                                        )
            else:
                future = request_method(url=url_probe, headers=headers,
                                        allow_redirects=allow_redirects,
                                        timeout=timeout
                                        )

            # Store future in data for access later
            net_info["request_future"] = future

            # Reset identify for tor (if needed)
            if unique_tor:
                underlying_request.reset_identity()

        # Add this site's results into final dictionary with all of the other results.
        results_total[social_network] = results_site

    # Open the file containing account links
    # Core logic: If tor requests, make them here. If multi-threaded requests, wait for responses
    for social_network, net_info in site_data.items():

        # Retrieve results again
        results_site = results_total.get(social_network)

        # Retrieve other site information again
        url = results_site.get("url_user")
        exists = results_site.get("exists")
        if exists is not None:
            # We have already determined the user doesn't exist here
            continue

        # Get the expected error type
        error_type = net_info["errorType"]

        # Default data in case there are any failures in doing a request.
        http_status = "?"
        response_text = ""

        # Retrieve future and ensure it has finished
        future = net_info["request_future"]
        r, error_type, response_time = get_response(request_future=future,
                                                    error_type=error_type,
                                                    social_network=social_network,
                                                    verbose=verbose,
                                                    retry_no=3,
                                                    color=color)

        # Attempt to get request information
        try:
            http_status = r.status_code
        except:
            pass
        try:
            # response_text = r.text.encode(r.encoding)
            response_text = ""
        except:
            pass

        if error_type == "message":
            error = net_info.get("errorMsg")
            # Checks if the error message is in the HTML
            if not error in r.text:
                print(f'FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "yes"
            else:
                if not print_found_only:
                    print(f'NOT FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "no"

        elif error_type == "status_code":
            # Checks if the status code of the response is 2XX
            if not r.status_code >= 300 or r.status_code < 200:
                print(f'FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "yes"
            else:
                if not print_found_only:
                    print(f'NOT FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "no"

        elif error_type == "response_url":
            # For this detection method, we have turned off the redirect.
            # So, there is no need to check the response URL: it will always
            # match the request.  Instead, we will ensure that the response
            # code indicates that the request was successful (i.e. no 404, or
            # forward to some odd redirect).
            if 200 <= r.status_code < 300:
                print(f'FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "yes"
            else:
                if not print_found_only:
                    print(f'NOT FOUND! - {social_network} - {url} - {response_time} - {verbose}')
                exists = "no"

        elif error_type == "":
            if not print_found_only:
                print(f'ERROR! - {social_network}')
            exists = "error"

        # Save exists flag
        results_site['exists'] = exists

        # Save results from request
        results_site['http_status'] = http_status
        results_site['response_text'] = ""
        results_site['response_time_ms'] = response_time

        # Add this site's results into final dictionary with all of the other results.
        results_total[social_network] = results_site
    return results_total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_sherlock(username)
    output(result)
