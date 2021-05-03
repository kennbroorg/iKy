#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import re
import os
# from time import time
from time import monotonic
from requests_futures.sessions import FuturesSession
from torrequest import TorRequest
from enum import Enum
from colorama import Fore, Style, init

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_sherlock(username):
    """ Task of Celery that get info from differents sites """

    data_file_path = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), "data_sherlock.json")

    with open(data_file_path, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    # Create notify object for query results.
    # query_notify = QueryNotifyPrint(result=None,
    #                                 verbose=True,
    #                                 print_all=True,
    #                                 color=not False)
    query_notify = QueryNotifyPrint(result=None,
                                    verbose=False,
                                    print_all=False,
                                    color=not True)
    raw_node = sherlock(username, data, query_notify, timeout=10)

    # Total
    total = []
    total.append({'module': 'sherlock'})
    total.append({'param': username})
    total.append({'validation': 'hard'})

    # Icons unicode
    font_list = fontawesome_cheat_5()

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []
    lists = []

    # Social
    social = []

    link = "Sherlock"
    gather_item = {"name-node": "Sherlock", "title": username,
                   "subtitle": "", "icon": "fas fa-share-alt",
                   "link": link}
    gather.append(gather_item)

    for rrss in raw_node:
        if (raw_node[rrss]["status"].status == QueryStatus.CLAIMED):
            status_resp = "Username Detected"
        elif (raw_node[rrss]["status"].status == QueryStatus.AVAILABLE):
            status_resp = "Username NOT Detected"
        elif (raw_node[rrss]["status"].status == QueryStatus.ILLEGAL):
            status_resp = "Username Not Allowable For This Site"
        else:
            status_resp = "Error Occurred While Trying To Detect Username"

        lists_item = {"title": rrss,
                      "subtitle": raw_node[rrss]["url_main"],
                      "status": raw_node[rrss]["http_status"],
                      "response": status_resp}
        lists.append(lists_item)
        if (raw_node[rrss]["status"].status == QueryStatus.CLAIMED):
            fa_icon = search_icon_5(rrss, font_list)
            if (fa_icon is None):
                fa_icon = search_icon_5("dot-circle", font_list)

            gather_item = {"name-node": rrss,
                           "title": rrss,
                           "icon": fa_icon,
                           "help": raw_node[rrss]["url_user"],
                           "link": link}
            gather.append(gather_item)
            social_item = {"name": rrss,
                           "url": raw_node[rrss]["url_user"],
                           "icon": fa_icon,
                           "source": "sherlock",
                           "username": username}
            social.append(social_item)
    profile.append({"social": social})

    # Please, respect the order of items in the total array
    # Because the frontend depend of that (By now)
    total.append({'raw': ""})
    # total.append({'raw': raw_node})
    # if (len(gather) != 1):
    #     graphic.append({'leaks': gather})
    graphic.append({'sherlock': gather})
    graphic.append({'lists': lists})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


class QueryNotify():
    def __init__(self, result=None):
        self.result = result
        return

    def start(self, message=None):
        return

    def update(self, result):
        self.result = result
        return

    def finish(self, message=None):
        return

    def __str__(self):
        result = str(self.result)
        return result


class QueryNotifyPrint(QueryNotify):
    def __init__(self, result=None, verbose=False, color=True,
                 print_all=False):
        # Colorama module's initialization.
        init(autoreset=True)

        super().__init__(result)
        self.verbose = verbose
        self.print_all = print_all
        self.color = color

        return

    def start(self, message):
        title = "Checking username"
        if self.color:
            print(Style.BRIGHT + Fore.GREEN + "[" + Fore.YELLOW + "*" +
                  Fore.GREEN + f"] {title}" + Fore.WHITE + f" {message}" +
                  Fore.GREEN + " on:")
        else:
            print(f"[*] {title} {message} on:")

        return

    def update(self, result):
        self.result = result

        if self.verbose == False or self.result.query_time is None:
            response_time_text = ""
        else:
            response_time_text = f" [{round(self.result.query_time * 1000)} ms]"

        # Output to the terminal is desired.
        if result.status == QueryStatus.CLAIMED:
            if self.color:
                print((Style.BRIGHT + Fore.WHITE + "[" +
                       Fore.GREEN + "+" +
                       Fore.WHITE + "]" +
                       response_time_text +
                       Fore.GREEN +
                       f" {self.result.site_name}: " +
                       Style.RESET_ALL +
                       f"{self.result.site_url_user}"))
            else:
                print(f"[+]{response_time_text} {self.result.site_name}: {self.result.site_url_user}")

        elif result.status == QueryStatus.AVAILABLE:
            if self.print_all:
                if self.color:
                    print((Style.BRIGHT + Fore.WHITE + "[" +
                        Fore.RED + "-" +
                        Fore.WHITE + "]" +
                        response_time_text +
                        Fore.GREEN + f" {self.result.site_name}:" +
                        Fore.YELLOW + " Not Found!"))
                else:
                    print(f"[-]{response_time_text} {self.result.site_name}: Not Found!")

        elif result.status == QueryStatus.UNKNOWN:
            if self.print_all:
                if self.color:
                    print(Style.BRIGHT + Fore.WHITE + "[" +
                          Fore.RED + "-" +
                          Fore.WHITE + "]" +
                          Fore.GREEN + f" {self.result.site_name}:" +
                          Fore.RED + f" {self.result.context}" +
                          Fore.YELLOW + f" ")
                else:
                    print(f"[-] {self.result.site_name}: {self.result.context} ")

        elif result.status == QueryStatus.ILLEGAL:
            if self.print_all:
                msg = "Illegal Username Format For This Site!"
                if self.color:
                    print((Style.BRIGHT + Fore.WHITE + "[" +
                           Fore.RED + "-" +
                           Fore.WHITE + "]" +
                           Fore.GREEN + f" {self.result.site_name}:" +
                           Fore.YELLOW + f" {msg}"))
                else:
                    print(f"[-] {self.result.site_name} {msg}")

        else:
            # It should be impossible to ever get here...
            raise ValueError(f"Unknown Query Status '{str(result.status)}' "
                             f"for site '{self.result.site_name}'")

        return

    def __str__(self):
        result = str(self.result)
        return result


class QueryStatus(Enum):
    CLAIMED = "Claimed"      # Username Detected
    AVAILABLE = "Available"  # Username Not Detected
    UNKNOWN = "Unknown"      # Error Occurred While Trying To Detect Username
    ILLEGAL = "Illegal"      # Username Not Allowable For This Site

    def __str__(self):
        return self.value


class QueryResult():
    def __init__(self, username, site_name, site_url_user, status,
                 query_time=None, context=None):
        self.username = username
        self.site_name = site_name
        self.site_url_user = site_url_user
        self.status = status
        self.query_time = query_time
        self.context = context

        return

    def __str__(self):
        status = str(self.status)
        if self.context is not None:
            # There is extra context information available about the results.
            # Append it to the normal response text.
            status += f" ({self.context})"

        return status


class SherlockFuturesSession(FuturesSession):
    def request(self, method, url, hooks={}, *args, **kwargs):
        """Request URL."""
        # Record the start time for the request.
        start = monotonic()

        def response_time(resp, *args, **kwargs):
            """Response Time Hook."""
            resp.elapsed = monotonic() - start

            return

        # Install hook to execute when response completes.
        # Make sure that the time measurement hook is first, so we will not
        # track any later hook's execution time.
        try:
            if isinstance(hooks['response'], list):
                hooks['response'].insert(0, response_time)
            elif isinstance(hooks['response'], tuple):
                # Convert tuple to list and insert time measurement hook first.
                hooks['response'] = list(hooks['response'])
                hooks['response'].insert(0, response_time)
            else:
                # Must have previously contained a single hook function,
                # so convert to list.
                hooks['response'] = [response_time, hooks['response']]
        except KeyError:
            # No response hook was already defined, so install it ourselves.
            hooks['response'] = [response_time]

        return super(SherlockFuturesSession, self).request(method,
                                                           url,
                                                           hooks=hooks,
                                                           *args, **kwargs)


def get_response(request_future, error_type, social_network):

    # Default for Response object if some failure occurs.
    response = None

    error_context = "General Unknown Error"
    expection_text = None
    try:
        response = request_future.result()
        if response.status_code:
            # Status code exists in response object
            error_context = None
    except requests.exceptions.HTTPError as errh:
        error_context = "HTTP Error"
        expection_text = str(errh)
    except requests.exceptions.ProxyError as errp:
        error_context = "Proxy Error"
        expection_text = str(errp)
    except requests.exceptions.ConnectionError as errc:
        error_context = "Error Connecting"
        expection_text = str(errc)
    except requests.exceptions.Timeout as errt:
        error_context = "Timeout Error"
        expection_text = str(errt)
    except requests.exceptions.RequestException as err:
        error_context = "Unknown Error"
        expection_text = str(err)

    return response, error_context, expection_text


def sherlock(username, site_data, query_notify,
             tor=False, unique_tor=False,
             proxy=None, timeout=None):
    """Run Sherlock Analysis."""

    # Notify caller that we are starting the query.
    # query_notify.start(username)

    # Create session based on request methodology
    if tor or unique_tor:
        # Requests using Tor obfuscation
        underlying_request = TorRequest()
        underlying_session = underlying_request.session
    else:
        # Normal requests
        underlying_session = requests.session()
        underlying_request = requests.Request()

    # Limit number of workers to 20.
    # This is probably vastly overkill.
    if len(site_data) >= 20:
        max_workers = 20
    else:
        max_workers = len(site_data)

    # Create multi-threaded session for all requests.
    session = SherlockFuturesSession(max_workers=max_workers,
                                     session=underlying_session)

    # Results from analysis of all sites
    results_total = {}

    # First create futures for all requests. This allows for the requests
    # to run in parallel
    for social_network, net_info in site_data.items():

        # Results from analysis of this specific site
        results_site = {}

        # Record URL of main site
        results_site['url_main'] = net_info.get("urlMain")

        # A user agent is needed because some sites don't return the correct
        # information since they think that we are bots
        # (Which we actually are...)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; ' +
            'rv:55.0) Gecko/20100101 Firefox/55.0',
        }

        if "headers" in net_info:
            # Override/append any extra headers required by a given site.
            headers.update(net_info["headers"])

        # URL of user on site (if it exists)
        url = net_info["url"].format(username)

        # Don't make request if username is invalid for the site
        regex_check = net_info.get("regexCheck")
        if regex_check and re.search(regex_check, username) is None:
            # No need to do the check at the site: this user name is not allowed.
            results_site['status'] = QueryResult(username,
                                                 social_network,
                                                 url,
                                                 QueryStatus.ILLEGAL)
            results_site["url_user"] = ""
            results_site['http_status'] = ""
            results_site['response_text'] = ""
            query_notify.update(results_site['status'])
        else:
            # URL of user on site (if it exists)
            results_site["url_user"] = url
            url_probe = net_info.get("urlProbe")
            if url_probe is None:
                # Probe URL is normal one seen by people out on the web.
                url_probe = url
            else:
                # There is a special URL for probing existence separate
                # from where the user profile normally can be found.
                url_probe = url_probe.format(username)

            if (net_info["errorType"] == 'status_code' and
                net_info.get("request_head_only", True) == True):
                # In most cases when we are detecting by status code,
                # it is not necessary to get the entire body:  we can
                # detect fine with just the HEAD response.
                request_method = session.head
            else:
                # Either this detect method needs the content associated
                # with the GET response, or this specific website will
                # not respond properly unless we request the whole page.
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

            # This future starts running the request in a new thread,
            # doesn't block the main thread
            if proxy is not None:
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

        # Add this site's results into final dictionary with all of the other
        # results.
        results_total[social_network] = results_site

    # Open the file containing account links
    # Core logic: If tor requests, make them here. If multi-threaded requests,
    # wait for responses
    for social_network, net_info in site_data.items():

        # Retrieve results again
        results_site = results_total.get(social_network)

        # Retrieve other site information again
        url = results_site.get("url_user")
        status = results_site.get("status")
        if status is not None:
            # We have already determined the user doesn't exist here
            continue

        # Get the expected error type
        error_type = net_info["errorType"]

        # Retrieve future and ensure it has finished
        future = net_info["request_future"]
        r, error_text, expection_text = get_response(request_future=future,
                                                     error_type=error_type,
                                                     social_network=social_network)

        # Get response time for response of our request.
        try:
            response_time = r.elapsed
        except AttributeError:
            response_time = None

        # Attempt to get request information
        try:
            http_status = r.status_code
        except Exception:
            http_status = "?"
        try:
            response_text = r.text.encode(r.encoding)
        except Exception:
            response_text = ""

        if error_text is not None:
            result = QueryResult(username,
                                 social_network,
                                 url,
                                 QueryStatus.UNKNOWN,
                                 query_time=response_time,
                                 context=error_text)
        elif error_type == "message":
            # error_flag True denotes no error found in the HTML
            # error_flag False denotes error found in the HTML
            error_flag = True
            errors = net_info.get("errorMsg")
            # errors will hold the error message
            # it can be string or list
            # by insinstance method we can detect that
            # and handle the case for strings as normal procedure
            # and if its list we can iterate the errors
            if isinstance(errors, str):
                # Checks if the error message is in the HTML
                # if error is present we will set flag to False
                if errors in r.text:
                    error_flag = False
            else:
                # If it's list, it will iterate all the error message
                for error in errors:
                    if error in r.text:
                        error_flag = False
                        break
            if error_flag:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        elif error_type == "status_code":
            # Checks if the status code of the response is 2XX
            if not r.status_code >= 300 or r.status_code < 200:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        elif error_type == "response_url":
            # For this detection method, we have turned off the redirect.
            # So, there is no need to check the response URL: it will always
            # match the request.  Instead, we will ensure that the response
            # code indicates that the request was successful (i.e. no 404, or
            # forward to some odd redirect).
            if 200 <= r.status_code < 300:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.CLAIMED,
                                     query_time=response_time)
            else:
                result = QueryResult(username,
                                     social_network,
                                     url,
                                     QueryStatus.AVAILABLE,
                                     query_time=response_time)
        else:
            # It should be impossible to ever get here...
            raise ValueError("Unknown Error Type '{}' for "
                             "site '{}'".format(error_type, social_network))

        # Notify caller about results of query.
        query_notify.update(result)

        # Save status of request
        results_site['status'] = result

        # Save results from request
        results_site['http_status'] = http_status
        results_site['response_text'] = response_text

        # Add this site's results into final dictionary with all of the
        # other results.
        results_total[social_network] = results_site

    # Notify caller that all queries are finished.
    query_notify.finish()

    return results_total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_sherlock(username)
    output(result)
