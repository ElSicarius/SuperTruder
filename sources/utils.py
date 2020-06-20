#!/usr/bin/python3

import os
import sys
from requests import get, post
from urllib.parse import unquote, quote
import difflib
import re


def set_global(settings):
    globals()["settings"] = settings


class Settings:
    def __init__(self,args):
        self.termlength = int(os.get_terminal_size()[0])
        self.redir = args.redir
        self.replaceStr = args.replaceStr
        self.out = args.dumpHtml
        self.url = args.url
        self.clean_url = "".join(re.findall("https?:\/\/[a-z\dA-Z.-]+", args.url))
        self.payloadFile = args.payload
        self.basePayload = args.basePayload
        self.threads = int(args.threads)
        self.timeout = int(args.timeout)
        self.matchBase = args.matchBaseRequest
        self.httpcodesFilter = parse_filter(args.filter)
        self.lengthFilter = parse_length_time_filter(args.lengthFilter)
        self.timeFilter = parse_length_time_filter(args.timeFilter)
        self.excludeLength = parse_excluded_length(args.excludeLength)
        self.difftimer = args.difftimer
        self.forceEncode = args.forceEncode
        self.verify = args.verify
        self.quick_ratio = args.quickRatio
        self.difference = float(args.textDifference)
        self.payload_offset = int(args.offset)

    def __str__(self):
        if "any,any" in self.lengthFilter:
            length_message = "\033[1;36mSelecting length matching\033[0m: any"
        elif len(self.lengthFilter) == 2:
            length_message = f"\033[1;36mSelecting responses len following\033[0m: {self.lengthFilter[0]} <= len \033[0m<= {self.lengthFilter[1]}"
        else:
            length_message = f"\033[1;36mSelecting responses len is in\033[0m: {self.lengthFilter}"

        if "any,any" in self.timeFilter:
            time_message = "\033[1;36mSelecting response time matching\033[0m: any"
        elif len(self.timeFilter) == 2:
            time_message = f"\033[1;36mSelecting responses time following\033[0m: {self.timeFilter[0]} <= time \033[0m<= {self.timeFilter[1]}"
        else:
            time_message = f"\033[1;36mSelecting responses time is in\033[0m: {self.timeFilter}"


        return f"""
\033[92mCurrent global settings\033[0m:
        \033[1;36mUrl\033[0m: {self.url}
        \033[1;36mPayloads file\033[0m: {self.payloadFile}
        \033[1;36mBase payload\033[0m: {self.basePayload}
        \033[1;36mRedirections allowed\033[0m: {self.redir}
        \033[1;36mTimeout of requests\033[0m: {self.timeout}
        \033[1;36mThreads\033[0m: {self.threads}
        \033[1;36mForce Encoding\033[0m: {"True" if self.forceEncode else "False"}
        \033[1;36mDumping HTML pages\033[0m: {"True, outfile:"+self.out if self.out else "False"}

\033[92mCurrent Trigger settings\033[0m:
        \033[1;36mSelecting HTTP status code\033[0m: {self.httpcodesFilter}
        {length_message}
        {time_message}
        \033[1;36mExcluding length mathing\033[0m: {self.excludeLength}
        \033[1;36mTrigger time difference\033[0m: {self.difftimer}
        \033[1;36mMatch page techniques\033[0m: {"Quick ratio" if self.quick_ratio else "Strict ratio"}
        \033[1;36mMatch page difference\033[0m: difference <= {self.difference}"""


def get_base_request(url, redir, payload):
    try:
        req = get(url.replace(settings.replaceStr, payload), allow_redirects=settings.redir, verify=settings.verify)
    except Exception as e:
        print(f"An error occured while requesting base request, Stopping here. Error: {e}")
        exit(42)
    print(f"""
\033[92mBase request info\033[0m:
        \033[1;36mstatus\033[0m: {color_status(req.status_code)}\033[0m,
        \033[1;36mcontent-length\033[0m: {len(req.text)-len(payload)},
        \033[1;36mrequest time\033[0m: {round(req.elapsed.total_seconds()*1000, 3)}\n""")
    return req


def is_identical(req1, req2, parameter, basePayload):
    ## Here we'll assume that two pages with text matching each other by > 98% are identical
    ## The purpose of this comparison is to assume that pages can contain variables like time
    ## , IP or the parameter itself.
    ## Low cost check
    if req1.text.replace(parameter, "") == req2.text.replace(basePayload, ""):
        return True
    ## Well use "Real_quick_ratio" instead of "quick_ratio"
    ## This is needed because a page with a small length could be hard to match at +98% with an other page
    ## Eg: page1 = "abcd" page2 = "abce"; difference = 1 caracter but match is 75% !
    if settings.quick_ratio:
        difference_of_text = difflib.SequenceMatcher(None, req1.text, req2.text).quick_ratio()
    else:
        difference_of_text = difflib.SequenceMatcher(None, req1.text, req2.text).ratio()
    diff_timer_requests =  abs(round(req1.elapsed.total_seconds()*1000, 3) - round(req2.elapsed.total_seconds()*1000, 3))

    if diff_timer_requests >= settings.difftimer:
        return False
    #print(f"Text Similiratity: {(difference_of_text*100)}%")
    #print(f"Difference with len of page1 {len(req1.content)}, page2 {len(req2.content)}")

    if req1.status_code == req2.status_code and difference_of_text > settings.difference:
        return True
    return False


def parse_filter(arg):
    status_table = dict({"deny": [], "allow": []})
    if 'any' in arg.lower():
        status_table["allow"].append("any")
        return status_table
    arg = arg.split(",")
    for code in arg:
        if code.startswith("n"):
            status_table["deny"].append(int(code[1:], 10))
        else:
            status_table["allow"].append(int(code, 10))
    return status_table


def parse_length_time_filter(args):
    splitted = args.split(",")
    if len(splitted)>2:
        length_table = set()
        for code in splitted:
            length_table.add(int(code,10))
        return length_table
    else:
        return splitted


def parse_excluded_length(arg):
    length_table = set()
    if "none" in arg:
        return []
    splitted = arg.split(",")
    if len(splitted)>=2:
        for code in splitted:
            length_table.add(int(code,10))
        return length_table
    else:
        try:
            splitted = int("".join(splitted))
        except Exception as e:
            print(f"Error in excluded length argument, make sure it's like: 2566 or 2566,5550, Error: {e}")
            exit(42)

        return [splitted]


def length_matching(response_len):
    if response_len in settings.excludeLength:
        return False
    go_length = False
    if len(settings.lengthFilter) == 2:
        if "any" in settings.lengthFilter[0] and "any" in settings.lengthFilter[1]:
            go_length = True
        elif settings.lengthFilter[0] == "any":
            if response_len <= int(settings.lengthFilter[1],10):
                go_length = True
        elif settings.lengthFilter[1] == "any":
            if int(settings.lengthFilter[0],10) <= response_len :
                go_length = True
        else:
            if int(settings.lengthFilter[0],10) <= response_len <= int(settings.lengthFilter[1],10):
                go_length = True
    elif response_len in settings.lengthFilter:
        go_length = True
    return go_length


def time_matching(response_len_time):
    go_length = False
    if len(settings.timeFilter) == 2:
        if "any" in settings.timeFilter[0] and "any" in settings.timeFilter[1]:
            go_length = True
        elif settings.timeFilter[0] == "any":
            if response_len_time <= int(settings.timeFilter[1],10):
                go_length = True
        elif settings.timeFilter[1] == "any":
            if int(settings.timeFilter[0],10) <= response_len_time :
                go_length = True
        else:
            if int(settings.timeFilter[0],10) <= response_len_time <= int(settings.timeFilter[1],10):
                go_length = True
    elif response_len_time in settings.timeFilter:
        go_length = True
    return go_length


def color_status(status):
    status = str(status)
    if status[0] == str(5):
        status = f"\033[91m{status}"
    elif status[0] == str(4) and status[2] != str(3):
        status = f"\033[93m{status}"
    elif status == "403":
        status = f"\033[94m{status}"
    elif status[0] == str(3):
        status = f"\033[1;36m{status}"
    else:
        status = f"\033[92m{status}"
    return status


def get_(url, parameter):
    return (get(url, timeout=settings.timeout, allow_redirects=settings.redir, verify=settings.verify), parameter)


def status_matching(status):
    # return True if:
    #  any or not blacklisted
    # else return false
    if status in settings.httpcodesFilter["deny"]:
        return False

    if "any" in settings.httpcodesFilter["allow"]:
        return True

    if status in settings.httpcodesFilter["allow"]:
        return True

    return True
