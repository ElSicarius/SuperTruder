#!/usr/bin/python

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, CancelledError, thread
import os
import sys
from requests import get, post
from urllib.parse import unquote, quote
import argparse
import difflib



class Settings:
    def __init__(self,args):
        self.termlength = int(os.get_terminal_size()[0])
        self.redir = args.redir
        self.replaceStr = args.replaceStr
        self.out = args.dumpHtml
        self.url = args.url
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

\033[92mCurrent Trigger settings\033[0m:
        \033[1;36mSelecting HTTP status code\033[0m: {self.httpcodesFilter}
        {length_message}
        {time_message}
        \033[1;36mExcluding length mathing\033[0m: {self.excludeLength}
        \033[1;36mTrigger time difference\033[0m: {self.difftimer}"""


def get_base_request(url, redir, payload):
    try:
        req = get(url.replace(settings.replaceStr, payload), allow_redirects=settings.redir)
    except Exception as e:
        print(f"An error occured while requesting base request, Stopping here. Error: {e}")
        exit(42)
    print(f"""
\033[92mBase request info\033[0m:
        \033[1;36mstatus\033[0m: {color_status(req.status_code)}\033[0m,
        \033[1;36mcontent-length\033[0m: {len(req.text.replace(payload, ''))},
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
    difference_of_text = difflib.SequenceMatcher(None, req1.text, req2.text).quick_ratio()
    diff_timer_requests =  abs(round(req1.elapsed.total_seconds()*1000, 3) - round(req2.elapsed.total_seconds()*1000, 3))

    if diff_timer_requests >= settings.difftimer:
        return False
    #print(f"Text Similiratity: {(difference_of_text*100)}%")
    #print(f"Difference with len of page1 {len(req1.content)}, page2 {len(req2.content)}")

    if req1.status_code == req2.status_code and difference_of_text > 0.98:
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


def get_(url, allow_redirects, timeout, parameter):
    return (get(url, timeout=timeout, allow_redirects=allow_redirects), parameter)


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


def main():
    # Get Options
    parser = argparse.ArgumentParser(description='SuperTruder: Fuzz something, somewhere in an URL')
    parser.add_argument('-u', "--url",help='Url to test',)
    parser.add_argument('-p', "--payload",help='payload file',)
    parser.add_argument('-b', "--basePayload", help="Payload for base request", default="Sicarius")
    parser.add_argument("-f", "--filter", help="Filter positives match with httpcode, comma separated, to exclude one: n200", default='any')
    parser.add_argument("-l", "--lengthFilter", help='Specify the len range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument("-nl", "--excludeLength", help='Specify the len range that we\'ll use to deny responses (eg: 0,999 or any, if 3 values, we\'ll refuse EXACTLY this values)', default="none,none")
    parser.add_argument("-t", "--timeFilter", help='Specify the time range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument('-r', "--redir", dest="redir", default=False, action="store_true", help='Allow HTTP redirects',)
    parser.add_argument("-m", '--matchBaseRequest', action="store_true", default=False)
    parser.add_argument("--difftimer", help="Change the default matching timer (default 2000ms -> 2 seconds)", default=2000)
    parser.add_argument("--timeout", default=20)
    parser.add_argument("--threads", default=50)
    parser.add_argument("-d","--replaceStr", default="§")
    parser.add_argument('-o', '--dumpHtml', help='file to dump html content',)
    args = parser.parse_args()

    global settings
    settings = Settings(args)
    print(settings)
    del args

    if not settings.url or not settings.payloadFile:
        print("Error, not enough args")
        exit(42)
    if settings.replaceStr not in settings.url:
        print(f"Error: Missing {settings.replaceStr} in URL provided")
        exit(42)


    base_request = get_base_request(settings.url, settings.redir, settings.basePayload)
    try:
        with open(settings.payloadFile, "r") as f:
            payloaddata = f.read()
    except Exception as e:
        print(f"Error: cannot read file {settings.payloadFile} Error: {e}")
        exit(42)

    ### Attempt connection to each URL and print stats

    print("Status\tLength\tTime\t  Url")
    print("---------------------------------")
    payload = payloaddata.split('\n')
    futures = set()
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        futures.update({executor.submit(get_, settings.url.replace(settings.replaceStr, p), settings.redir, settings.timeout, p) for p in payload} )
        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for futu in done:
                try:
                    r, p = futu.result()
                except Exception as e:
                    #print(f"An Unhandled error occured in thread: {e}")
                    pass
                else:
                    if r != None:
                        #print( is_identical(r, base_request, p, basePayload),matchBase,not (is_identical(r, base_request, p, basePayload) ^ matchBase))
                        if not (is_identical(r, base_request, p, settings.basePayload) ^ settings.matchBase):
                            status = r.status_code
                            response_len = len(r.text.replace(p, ""))
                            response_time = int(r.elapsed.total_seconds()*1000)
                            # Determine if the http status code is good to be printed
                            go_status = status_matching(status)
                            # Determine if the length is good to be printed
                            go_length = length_matching(response_len)
                            # Determine if the time to response is good to be printed
                            go_time = time_matching(response_time)
                            # print status message only if httpcode & len are ok
                            if go_status and go_length and go_time:
                                status = str(status)
                                status = color_status(status)
                                length = str(response_len)
                                timer = str(response_time)
                                url = unquote(r.url)
                                print(f"{' '*(settings.termlength-1)}", end="\r")
                                print(f"{status}\t{length}\t{timer}\t{url}\033[0m")
                                if settings.out and len(r.content) != 0:
                                    try:
                                        with open(f"{settings.out}", 'wb') as f:
                                            f.write(r.content)
                                    except Exception as e:
                                        print(f"Error: could not write file {out} Error: {e}")
                            else:
                                print(f"{r.status_code}\t{len(r.content)}\t{round(r.elapsed.total_seconds()*1000,1)}\t{unquote(r.url)}"[:settings.termlength-50], end="\r")
                        else:
                            print(f"{r.status_code}\t{len(r.content)}\t{round(r.elapsed.total_seconds()*1000,1)}\t{unquote(r.url)}"[:settings.termlength-50], end="\r")

                    else:
                        print("Request == None ??")
    except CancelledError:
        print("cancelled thread")
    except KeyboardInterrupt:
        print(f"{' '*(settings.termlength-1)}", end="\r")
        print(f"\033[91m[-] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.\033[0m")
        executor._threads.clear()
        thread._threads_queues.clear()
    except Exception as e:
        print(f"\033[91m[FATAL] Unhandled exception : {e}\033[0m")


if __name__ == '__main__':
    main()
    print("\033[94m[+] Done\033[0m" + " "* settings.termlength)
