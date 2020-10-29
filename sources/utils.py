#!/usr/bin/python3

import os
import sys
import json
from requests import get, post, packages
from urllib.parse import unquote, quote
import difflib
import re
import argparse
from time import sleep
from .const import *


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def set_global(settings):
    """
    Set some globals for this file
    ## TODO: find a better solution to propagate the "settings" object accross multiple files
    """
    globals()["settings"] = settings


def request_handler(url, payload, data=None, method=None):
    """
    Do a GET or a POST depending on the method set in settings (can be overrite with the method argument)
    :returns the requests.response object
    """
    method = settings.method if not method else method
    if method == "GET":
        return get_(url, payload)
    if method == "POST":
        return post_(url, data, payload)


def load_tamper(module):
    module_path = f"tampers.{module}"

    if module_path in sys.modules:
        return sys.modules[module_path]
    try:
        load = __import__(module_path, fromlist=[module])
    except:
        print(f"{red} Failed to load the module {module}, please make sure you've put it in the tampers directory{end}")
        exit(42)
    try:

        dummyCheck = load.process("dummy")
        if settings.verbosity > 1:
            print(f"{dark_blue} Dummy check for the tamper module: 'dummy' became -> '{dummyCheck}'")
    except Exception as e:
        print(f"{red}Cannot find the 'process' function in your tamper script...{end}")
        exit(42)
    else:
        return load


def get_arguments():
    """
    Parses the argparse object
    :returns the arguments object
    """
    parser = argparse.ArgumentParser(description='SuperTruder: Fuzz something, somewhere in an URL, data or HTTP headers',
                                     epilog="Tired of using ffuf ? Tired of using burp's slow intruder ? Checkout SuperTruder, an intruder that isn't hard to use, or incredibly slow\n Made with love by Sicarius (@AMTraaaxX) ")

    # Fuzzing stuff
    parser.add_argument('-u', "--url", help='Url to test',)
    parser.add_argument('-p', "--payload", help='payload file',)
    parser.add_argument('-P', "--distant_payload",
                        help="use an online wordlist instead of a local one (do not use if your internet connection is shit, or the wordlist weight is like To)", default=False)
    parser.add_argument("-R", "--regexPayload", help="use a regex to create your payload list")
    parser.add_argument("-d", "--data", default=None, help="Add POST data")
    parser.add_argument('-b', "--basePayload",
                        help="Payload for base request", default="Fuzzing")
    parser.add_argument("-H", "--headers", default={},
                        help="Add extra Headers (syntax: \"header: value\\nheader2: value2\")")
    parser.add_argument("-S", "--replaceStr", default="§")
    parser.add_argument("-T", "--tamper",help="Use tamper scripts located in the tamper directory (you can make your own)", default=None)

    # Sorting stuff
    parser.add_argument(
        "-f", "--filter", help="Filter positives match with httpcode, comma separated, to exclude one: n200", default='any')
    parser.add_argument("-l", "--lengthFilter",
                        help='Specify the len range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument("-m", '--matchBaseRequest',
                        action="store_true", default=False)
    parser.add_argument("-el", "--excludeLength",
                        help='Specify the len range that we\'ll use to deny responses (eg: 0,999 or any, if 3 values, we\'ll refuse EXACTLY this values)', default="none,none")
    parser.add_argument(
        "-t", "--timeFilter", help='Specify the time range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")

    # misc stuff
    parser.add_argument('-o', '--dumpHtml', help='file to dump html content')
    parser.add_argument(
        "--offset", help="Start over where you stopped by giving the payload offset", default=0)
    parser.add_argument("--shuffle", help="Shuffle the payload list", default=False, action="store_true")

    # request stuff
    parser.add_argument('-r', "--redir", dest="redir", default=False,
                        action="store_true", help='Allow HTTP redirects')
    parser.add_argument(
        "--forceEncode", help="Force URL encode", action="store_true")
    parser.add_argument("--timeout", default=20)
    parser.add_argument(
        "--throttle", help="throttle between the requests", default=0.01)
    parser.add_argument("--verify", default=False, action="store_true")

    # program functionnalities
    parser.add_argument(
        "--difftimer", help="Change the default matching timer (default 2000ms -> 2 seconds)", default=2000)
    parser.add_argument(
        "--textDifference", help="Percentage difference to match pages default: 99%%", default=0.99)
    parser.add_argument("--quickRatio", help="Force quick ratio of pages (a bit faster)",
                        action="store_true", default=False)
    parser.add_argument("--threads", default=5)
    parser.add_argument("--ignoreBaseRequest", default=False,
                        action="store_true", help="Force testing even if base request failed")
    parser.add_argument("--uselessprint", help="Disable useless self-rewriting print (with '\\r')",
                        default=False, action="store_true")
    parser.add_argument("-q", "--quiet", help="tell the program to output only the results",
                        default=False, action="store_true")
    parser.add_argument("-v",'--verbosity', help="Change the verbosity of the program (available: 1,2,3)", default=2)

    args = parser.parse_args()
    return args


def gen_payload():
    """
    Processes the args and generate the payload list with the infos given

    : returns the payload list object
    """
    print(f"\n{dark_blue}Loading wordlist, please wait...{end}",
          file=settings.stdout if settings.verbosity > 2 else settings.devnull)
    if not settings.payloadFile and settings.distant_payload and not settings.regexPayload:
        req = None
        print(f"{yellow}Downloading wordlist @ {settings.distant_payload}{end}",
              file=settings.stdout)
        try:
            req = get(settings.distant_payload, timeout=settings.timeout,
                      allow_redirects=settings.redir, verify=settings.verify)
        except Exception as e:
            print(f"{red}Error: cannot reach file at {settings.distant_payload} Error: {e}{end}",
                  file=settings.stdout)
            print(f"{red}Request info: {yellow} Status {req.status_code}{end}",
                  file=settings.stdout)
            exit(42)
        print(f"{dark_blue}Wordlist downloaded successfully{end}",
              file=settings.stdout)
        payloaddata = req.text
        payload = list(payloaddata.split('\n'))
    elif settings.payloadFile and not settings.distant_payload and not settings.regexPayload:
        try:
            with open(settings.payloadFile, "r") as f:
                payloaddata = f.read()
        except Exception as e:
            print(f"{red}Error: cannot read file {settings.payloadFile} Error: {e}{end}",
                  file=settings.stdout)
            exit(42)
        payload = list(payloaddata.split('\n'))
    else:
        try:
            import exrex
        except:
            print(f"{red}Missing dependency \"exrex\"! if you want to use the regex payload generation, you have to use this command first: 'pip3 install exrex'")
            exit(42)
        try:
            re.compile(settings.regexPayload)
        except:
            print(f"{red}Bad regex !! please check that your regex is correct !")
            exit(42)
        print(f"{dark_blue}Generating the payload list based on your regex{end}", file=settings.stdout)
        payloaddata = exrex.generate(settings.regexPayload)
        payload = list(payloaddata)
    del payloaddata

    if settings.tamper:
        temp = list()
        for item in payload:
            temp.append(settings.tamper.process(item))
        payload = temp
        del temp
    return payload


def get_base_request():
    """
    Generate a first request to the target with a dummy payload to determine the origin status, length and content

    this will set the settings request object to the request made
    """
    req = None
    if settings.method == "GET":
        try:
            req, payload = get_(replace_string(
                settings.url, settings.replaceStr, settings.basePayload), settings.basePayload)
        except Exception as e:
            print(
                f"{red}An error occured while requesting base request. Error: {e}{end}")
    elif settings.method == "POST":
        try:
            req, payload = post_(replace_string(settings.url, settings.replaceStr, settings.basePayload), replace_string(
                settings.data, settings.replaceStr, settings.basePayload), settings.basePayload)
        except Exception as e:
            print(
                f"{red}An error occured while requesting base request. Error: {e}{end}")

        print(f"{yellow}Forcing test (might be a total failure){end}")
    if req == None and not settings.forceTest:
        print(f"{red}Error in base request !")
        print(f"{red}Ignore base request not specified, Stopping here...{end}")
        exit(42)
    elif req != None:
        settings.base_request = {"req": req, "text": req.text, "time": int(
            req.elapsed.total_seconds() * 1000), "status": req.status_code}
        print(f"""
{green}Base request info:
        {light_blue}status: {color_status(req.status_code)}{end},
        {light_blue}content-length: {end}{len(req.text)-len(payload) if payload in req.text else len(req.text)},
        {light_blue}request time: {end}{round(req.elapsed.total_seconds()*1000, 3)}{end},
        {light_blue}Request text (trucated) was: {banner}{req.text if len(req.text)<=100 else req.text[:50]+f" {yellow}[...] "+req.text[-50:]}\n""", file=settings.stdout)

    elif req == None:
        settings.base_request = {"req": None,
                                 "text": None, "time": 0, "status": 0}


def is_identical(req, parameter):
    """
    Here we'll assume that two pages with text matching each other by > 98% are identical
    The purpose of this comparison is to assume that pages can contain variables like time,
    IP or the parameter itself, we don't want to match everything because there is a slightly difference between the origin request and the payloady request.

    So to be sure we don't match random things, we'll do a comparison with the value of args "textDifference"
    """
    # Low cost check
    if settings.base_request["req"] == None:
        return False

    if settings.base_request["text"].replace(settings.basePayload, "") == req.text.replace(parameter, ""):
        return True

    diff_timer_requests = abs(
        settings.base_request["time"] - int(req.elapsed.total_seconds() * 1000))

    if diff_timer_requests >= settings.difftimer:
        return False

    # Well not use "Real_quick_ratio" instead of "quick_ratio"
    # This would be needed because a page with a small length could be hard to match at +98% with an other page
    # Eg: page1 = "abcd" page2 = "abce"; difference = 1 caracter but match is 75% !
    # but MEH ! it's http pages we'll assume the content is > 4 caracters ;)
    if settings.quick_ratio:
        difference_of_text = difflib.SequenceMatcher(
            None, settings.base_request["text"], req.text).quick_ratio()
    else:
        difference_of_text = difflib.SequenceMatcher(
            None, settings.base_request["text"], req.text).ratio()

    if settings.base_request["status"] == req.status_code and difference_of_text > settings.difference:
        return True

    return False


def calc_remove_len(req1, parameter):
    """
    calculate the number of occurences of a given parameter in a requests.response object
    This is needed to remove them in order to process the differences in length
    """
    if settings.base_request["text"] != None:
        words_reflexions = settings.base_request["text"].count(parameter)
    else:
        words_reflexions = 0
    new_words_reflexions = req1.text.count(parameter)

    if new_words_reflexions == 0:
        return 0

    if new_words_reflexions > 0 and words_reflexions == 0:
        return new_words_reflexions

    if new_words_reflexions > 0 and words_reflexions > 0:
        return abs(new_words_reflexions - words_reflexions)


def parse_filter(arg):
    """
    Parse the input argument "-f" or "--filter"
    : returns the status_table that will be used to process the info
    : returns the status table that will be used to render the info
    """
    status_table = dict({"deny": [], "allow": []})
    status_table_printable = dict({"deny": [], "allow": []})
    if 'any' in arg.lower():
        status_table["allow"].append("any")
        status_table_printable["allow"].append("any")
        return status_table, status_table_printable
    arg = arg.split(",")
    for code in arg:
        # populate printable table
        if code.startswith("n"):
            status_table_printable["deny"].append(code)
        else:
            status_table_printable["allow"].append(code)
        # populate table used by script
        if code.endswith("x"):
            for dizaines in range(10):
                for iteration in range(10):
                    if code.startswith("n"):
                        status_table["deny"].append(
                            int(f"{code[1:2]}{dizaines}{iteration}", 10))
                    else:
                        status_table["allow"].append(
                            int(f"{code[:1]}{dizaines}{iteration}", 10))
        else:
            if code.startswith("n"):
                status_table["deny"].append(int(code[1:], 10))
            else:
                status_table["allow"].append(int(code, 10))

    if len(status_table["deny"]) > 0 and len(status_table["allow"]) == 0:
        status_table["allow"].append("any")
        status_table_printable["allow"].append("any")
    return status_table, status_table_printable


def parse_length_time_filter(args):
    """
    This parses the length and the time filters
    :returns the list of the differents values given
    """
    splitted = args.split(",")
    if len(splitted) > 2:
        length_table = set()
        for code in splitted:
            length_table.add(int(code, 10))
        return length_table
    else:
        return splitted


def parse_excluded_length(arg):
    """
    Parses the -el filter
    ## TODO: parle the -l filter like the -f filter and remove -el parameter
    """
    length_table = set()
    if "none" in arg:
        return []
    splitted = arg.split(",")
    if len(splitted) >= 2:
        for code in splitted:
            length_table.add(int(code, 10))
        return length_table
    else:
        try:
            splitted = int("".join(splitted))
        except Exception as e:
            print(
                f"{red}Error in excluded length argument, make sure it's like: 2566 or 2566,5550, Error: {e}{end}")
            exit(42)
        return [splitted]


def print_nothing(time_print, current_status, payload_len, r, parameter, end="\r"):
    """
    print the temp status message, this is called "print_nothing" coz it's kinda useless
    """
    if settings.uselessprint:
        print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t   \t     \t     \t\t{' '*settings.termlength}"[
              :settings.termlength - 50], end="\r", file=settings.stdout)
        print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{r.status_code}\t{len(r.content)}\t{int(r.elapsed.total_seconds()*1000)}\t\t{parameter}"[
              :settings.termlength - 50], end="\r", file=settings.stdout)


def length_matching(response_len):
    """
    Check if the length of the response is in the filters given
    returns True or False
    """
    if response_len in settings.excludeLength:
        return False
    go_length = False
    if len(settings.lengthFilter) == 2:
        if "any" in settings.lengthFilter[0] and "any" in settings.lengthFilter[1]:
            go_length = True
        elif settings.lengthFilter[0] == "any":
            if response_len <= int(settings.lengthFilter[1], 10):
                go_length = True
        elif settings.lengthFilter[1] == "any":
            if int(settings.lengthFilter[0], 10) <= response_len:
                go_length = True
        else:
            if int(settings.lengthFilter[0], 10) <= response_len <= int(settings.lengthFilter[1], 10):
                go_length = True
    elif response_len in settings.lengthFilter:
        go_length = True
    return go_length


def time_matching(response_len_time):
    """
    Check if the time of the response is in the filters given
    returns True or False
    """
    go_length = False
    if len(settings.timeFilter) == 2:
        if "any" in settings.timeFilter[0] and "any" in settings.timeFilter[1]:
            go_length = True
        elif settings.timeFilter[0] == "any":
            if response_len_time <= int(settings.timeFilter[1], 10):
                go_length = True
        elif settings.timeFilter[1] == "any":
            if int(settings.timeFilter[0], 10) <= response_len_time:
                go_length = True
        else:
            if int(settings.timeFilter[0], 10) <= response_len_time <= int(settings.timeFilter[1], 10):
                go_length = True
    elif response_len_time in settings.timeFilter:
        go_length = True
    return go_length


def status_matching(status):
    """
    Check if the status of the response is in the filters given
    returns True or False
    """
    if status in settings.httpcodesFilter["deny"]:
        return False

    if "any" in settings.httpcodesFilter["allow"]:
        return True

    if status in settings.httpcodesFilter["allow"]:
        return True

    return False


def color_status(status):
    """
    Add some colors depending on the status returned
    :returns a string with some colors around it
    """
    status = str(status)
    if status[0] == str(5):
        status = f"{red}{status}"
    elif status[0] == str(4) and status[2] != str(3):
        status = f"{yellow}{status}"
    elif status == "403":
        status = f"{dark_blue}{status}"
    elif status[0] == str(3):
        status = f"{light_blue}{status}"
    else:
        status = f"{green}{status}"
    return status


def replace_string(data, focus, new_data):
    """
    Replace some data into an other data and check if we need to the force encode the replace string parameter*
    :returns the original string with the parameter replaced
    """
    return data.replace(focus, quote(new_data) if settings.forceEncode else new_data)


def get_(url, parameter):
    """
    Do a GET request in the session object
    check if we timeout or if we have a status 429 (rate limit reached)
    resend the request if it is set in the settings
    :returns a tuple with the request object and the parameter requested
    """
    if settings.throttle > 0:
        sleep(settings.throttle)
    temp_headers = settings.headers
    if settings.headerprocess:
        temp_headers = json.loads(replace_string(json.dumps(settings.headers, ensure_ascii=False), settings.replaceStr, parameter))
    try:
        req = settings.session.get(url, timeout=settings.timeout, allow_redirects=settings.redir,
                  verify=settings.verify, headers=temp_headers)
        if req.status_code == 429:
            print(
                f"Rate limit reached, increase --throttle! Current is {settings.throttle}", file=settings.stdout)
    except:
        settings.errors_count += 1
        if settings.retry:
            try:
                req = settings.session.get(url, timeout=settings.timeout, allow_redirects=settings.redir,
                          verify=settings.verify, headers=temp_headers)
                if req.status_code == 429:
                    print(
                        f"Rate limit reached, increase --throttle! Current is {settings.throttle}", file=settings.stdout)
            except:
                settings.retry_count += 1
                req = None
        else:
            req = None
    return (req, parameter)


def post_(url, data, parameter):
    """
    Do a POST request in the session object
    check if we timeout or if we have a status 429 (rate limit reached)
    resend the request if it is set in the settings
    :returns a tuple with the request object and the parameter requested
    """
    if settings.throttle > 0:
        sleep(settings.throttle)
    temp_headers = settings.headers
    if settings.headerprocess:
        temp_headers = json.loads(replace_string(json.dumps(settings.headers, ensure_ascii=False), settings.replaceStr, parameter))
    try:
        req = settings.session.post(url, data=data, timeout=settings.timeout, allow_redirects=settings.redir,
                   verify=settings.verify, headers=temp_headers)
        if req.status_code == 429:
            print(
                f"Rate limit reached, increase --throttle! Current is {settings.throttle}", file=settings.stdout)
    except:
        settings.errors_count += 1
        if settings.retry:
            try:
                req = settings.session.post(url, data=data, timeout=settings.timeout, allow_redirects=settings.redir,
                           verify=settings.verify, headers=temp_headers)
                if req.status_code == 429:
                    print(
                        f"Rate limit reached, increase --throttle! Current is {settings.throttle}", file=settings.stdout)
            except:
                settings.retry_count += 1
                req = None
        else:
            req = None

    return (req, parameter)
