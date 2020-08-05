#!/usr/bin/python3

import os
import sys
import json
from requests import get, post, packages
from urllib.parse import unquote, quote
import difflib
import re
from time import sleep
from .const import *


import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def set_global(settings):
    globals()["settings"] = settings


class Settings:
    def __init__(self, args):
        if not args.url or not args.payload:
            print(f"{red}Error, not enough args, see help (-h) for more details{end}")
            exit(42)

        self.basePayload = args.basePayload
        self.url = args.url
        self.clean_url = "".join(re.findall(
            "https?:\/\/[a-z\dA-Z.-]+", self.url))
        self.difference = float(args.textDifference)
        self.difftimer = int(args.difftimer)
        self.excludeLength = parse_excluded_length(args.excludeLength)
        self.forceEncode = args.forceEncode
        self.throttle = float(args.throttle)
        self.httpcodesFilter, self.status_table_printable = parse_filter(args.filter)
        self.lengthFilter = parse_length_time_filter(args.lengthFilter)
        self.matchBase = args.matchBaseRequest
        self.out = args.dumpHtml
        if self.out:
            self.fileStream = open(self.out, "ab+")
        self.payloadFile = args.payload
        self.payload_offset = int(args.offset)
        self.quick_ratio = args.quickRatio
        self.redir = args.redir
        self.replaceStr = args.replaceStr
        self.termlength = int(os.get_terminal_size()[0])
        self.threads = int(args.threads)
        self.timeFilter = parse_length_time_filter(args.timeFilter)
        self.timeout = int(args.timeout)
        self.uselessprint = not args.uselessprint
        self.verify = args.verify
        self.headers = args.headers if args.headers == {
        } else self.loadHeaders(args.headers)

        self.forceTest = args.ignoreBaseRequest
        self.base_request = {"req": None, "text": "", "time": 0, "status": 0}
        self.retry = True
        self.method = "GET"
        self.data = None
        self.errors_count = 0
        self.retry_count = 0

        if args.data:
            self.method = "POST"
            self.data = args.data

        if self.replaceStr not in self.url and self.replaceStr not in str(self.headers):
            if self.method == "GET":
                print(f"{red}Error: Missing {self.replaceStr} in URL provided{end}")
                exit(42)
            if self.method == "POST" and self.replaceStr not in self.data:
                print(
                    f"{red}Error: Missing {self.replaceStr} in URL/Data provided{end}")
                exit(42)

    def loadHeaders(self, headers_string):
        headers = headers_string.split("\\n")
        header_final = {}
        for h in headers:
            splitted = h.replace("\\!", "!").split(": ")
            if len(splitted) != 2:
                print(f"{red} You have an error on the header syntax, exitting{end}")
                exit(42)
            header_final.update({splitted[0]: splitted[1]})
        return header_final

    def __str__(self):
        if "any,any" in self.lengthFilter:
            length_message = f"Selecting length matching: {end}any"
        elif len(self.lengthFilter) == 2:
            length_message = f"Selecting responses len following: {end}{self.lengthFilter[0]} {yellow}<= len <={end} {self.lengthFilter[1]}"
        else:
            length_message = f"Selecting responses len is in: {end}{self.lengthFilter}"

        if "any,any" in self.timeFilter:
            time_message = f"Selecting response time matching: {end}any"
        elif len(self.timeFilter) == 2:
            time_message = f"Selecting responses time following: {end}{self.timeFilter[0]} {yellow}<= time <={end} {self.timeFilter[1]}"
        else:
            time_message = f"Selecting responses time is in: {end}{self.timeFilter}"

        return f"""
{green}Current global settings:
        {light_blue}Url: {end}{self.url}
        {light_blue}HTTP Method: {end}{self.method}
        {light_blue}Additionnal data:
            {light_blue}Headers: {end}{self.headers}
            {light_blue}Data: {end}{self.data if self.data == None or len(self.data)<=20 else self.data[:10]+f"{yellow}[...]{end}"+self.data[-10:]}
        {light_blue}Payloads file: {end}{self.payloadFile}
        {light_blue}Base payload: {end}{self.basePayload}
        {light_blue}Redirections allowed: {end}{self.redir}
        {light_blue}Timeout of requests: {end}{self.timeout}
        {light_blue}Throttle between requests: {end}{self.throttle}
        {light_blue}Threads: {end}{self.threads}
        {light_blue}Force Encoding: {end}{"True" if self.forceEncode else "False"}
        {light_blue}Dumping HTML pages: {end}{"True, outfile:"+self.out if self.out else "False"}

{green}Current Trigger settings:
        {light_blue}Selecting HTTP status code: {end}{self.status_table_printable}
        {light_blue}{length_message}
        {light_blue}{time_message}
        {light_blue}Excluding length mathing: {end}{self.excludeLength}
        {light_blue}Trigger time difference: {end}{self.difftimer}
        {light_blue}Match page techniques: {end}{"Quick ratio" if self.quick_ratio else "Strict ratio"}
        {light_blue}Match page difference: {end}difference <= {self.difference}{end}"""


def get_base_request():
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
        {light_blue}Request text (trucated) was: {banner}{req.text if len(req.text)<=100 else req.text[:50]+f" {yellow}[...] "+req.text[-50:]}\n""")

    elif req == None:
        settings.base_request = {"req": None,
                                 "text": None, "time": 0, "status": 0}


def is_identical(req, parameter):
    # Here we'll assume that two pages with text matching each other by > 98% are identical
    # The purpose of this comparison is to assume that pages can contain variables like time
    # , IP or the parameter itself.
    # Low cost check
    if settings.base_request["req"] == None:
        return False

    if settings.base_request["text"].replace(settings.basePayload, "") == req.text.replace(parameter, ""):
        return True

    diff_timer_requests = abs(
        settings.base_request["time"] - int(req.elapsed.total_seconds() * 1000))

    if diff_timer_requests >= settings.difftimer:
        return False

    #print(f"Text Similiratity: {(difference_of_text*100)}%")
    #print(f"Difference with len of page1 {len(req1.content)}, page2 {len(req2.content)}")

    # Well use "Real_quick_ratio" instead of "quick_ratio"
    # This is needed because a page with a small length could be hard to match at +98% with an other page
    # Eg: page1 = "abcd" page2 = "abce"; difference = 1 caracter but match is 75% !
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
    if settings.base_request["text"] != None :
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
    status_table = dict({"deny": [], "allow": []})
    status_table_printable = dict({"deny": [], "allow": []})
    if 'any' in arg.lower():
        status_table["allow"].append("any")
        status_table_printable["allow"].append("any")
        return status_table
    arg = arg.split(",")
    for code in arg:
        #populate printable table
        if code.startswith("n"):
            status_table_printable["deny"].append(code)
        else:
            status_table_printable["allow"].append(code)
        #populate table used by script
        if code.endswith("x"):
            for dizaines in range(10):
                for iteration in range(10):
                    if code.startswith("n"):
                        status_table["deny"].append(int(f"{code[1:2]}{dizaines}{iteration}", 10))
                    else:
                        status_table["allow"].append(int(f"{code[:1]}{dizaines}{iteration}", 10))
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
    splitted = args.split(",")
    if len(splitted) > 2:
        length_table = set()
        for code in splitted:
            length_table.add(int(code, 10))
        return length_table
    else:
        return splitted


def parse_excluded_length(arg):
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
    if settings.uselessprint:
        print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t   \t     \t     \t\t{' '*settings.termlength}"[
              :settings.termlength - 50], end="\r")
        print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{r.status_code}\t{len(r.content)}\t{int(r.elapsed.total_seconds()*1000)}\t\t{parameter}"[
              :settings.termlength - 50], end="\r")


def length_matching(response_len):
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


def color_status(status):
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
    return data.replace(focus, quote(new_data) if settings.forceEncode else new_data)


def get_(url, parameter):
    sleep(settings.throttle)
    temp_headers = settings.headers if not settings.replaceStr in str(settings.headers) else json.loads(
        replace_string(json.dumps(settings.headers, ensure_ascii=False), settings.replaceStr, "parameter"))
    try:
        req = get(url, timeout=settings.timeout, allow_redirects=settings.redir,
                  verify=settings.verify, headers=temp_headers)
        if req.status_code == 429:
            print(
                f"Rate limit reached, increase --throttle! Current is {settings.throttle}")
    except:
        settings.errors_count += 1
        if settings.retry:
            try:
                req = get(url, timeout=settings.timeout, allow_redirects=settings.redir,
                          verify=settings.verify, headers=temp_headers)
                if req.status_code == 429:
                    print(
                        f"Rate limit reached, increase --throttle! Current is {settings.throttle}")
            except:
                settings.retry_count += 1
                req = None
        else:
            req = None

    return (req, parameter)


def post_(url, data, parameter):
    sleep(settings.throttle)
    temp_headers = settings.headers if not settings.replaceStr in str(settings.headers) else json.loads(
        replace_string(json.dumps(settings.headers, ensure_ascii=False), settings.replaceStr, "parameter"))

    try:
        req = post(url, data=data, timeout=settings.timeout, allow_redirects=settings.redir,
                   verify=settings.verify, headers=temp_headers)
        if req.status_code == 429:
            print(
                f"Rate limit reached, increase --throttle! Current is {settings.throttle}")
    except:
        settings.errors_count += 1
        if settings.retry:
            try:
                req = post(url, data=data, timeout=settings.timeout, allow_redirects=settings.redir,
                           verify=settings.verify, headers=temp_headers)
                if req.status_code == 429:
                    print(
                        f"Rate limit reached, increase --throttle! Current is {settings.throttle}")
            except:
                settings.retry_count += 1
                req = None
        else:
            req = None

    return (req, parameter)


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

    return False
