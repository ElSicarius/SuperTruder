#!/usr/bin/python3

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, CancelledError, thread
import os
import sys
from requests import get, post, packages
from urllib.parse import unquote, quote
import argparse
import difflib
from datetime import datetime
from .utils import *


def main():
    packages.urllib3.disable_warnings()

    parser = argparse.ArgumentParser(description='SuperTruder: Fuzz something, somewhere in an URL')
    parser.add_argument("-S","--replaceStr", default="§")
    parser.add_argument("-d", "--data", default=None, help="Add POST data")
    parser.add_argument("-f", "--filter", help="Filter positives match with httpcode, comma separated, to exclude one: n200", default='any')
    parser.add_argument("-l", "--lengthFilter", help='Specify the len range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument("-m", '--matchBaseRequest', action="store_true", default=False)
    parser.add_argument("-el", "--excludeLength", help='Specify the len range that we\'ll use to deny responses (eg: 0,999 or any, if 3 values, we\'ll refuse EXACTLY this values)', default="none,none")
    parser.add_argument("-t", "--timeFilter", help='Specify the time range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument('-b', "--basePayload", help="Payload for base request", default="Sicarius")
    parser.add_argument('-o', '--dumpHtml', help='file to dump html content')
    parser.add_argument('-p', "--payload",help='payload file',)
    parser.add_argument('-r', "--redir", dest="redir", default=False, action="store_true", help='Allow HTTP redirects')
    parser.add_argument('-u', "--url",help='Url to test',)
    parser.add_argument("-H", "--headers", default={}, help="Add extra Headers (syntax: \"header: value,header2: value2\")")
    parser.add_argument("--difftimer", help="Change the default matching timer (default 2000ms -> 2 seconds)", default=2000)
    parser.add_argument("--forceEncode", help="Force URL encode", action="store_true")
    parser.add_argument("--offset", help="Start over where you stopped by giving the payload offset", default=0)
    parser.add_argument("--quickRatio", help="Force quick ratio of pages (a bit faster)", action="store_true", default=False)
    parser.add_argument("--textDifference", help="Percentage difference to match pages default: 99%%", default=0.99)
    parser.add_argument("--threads", default=50)
    parser.add_argument("--timeout", default=20)
    parser.add_argument("--uselessprint", help="Enable Louka-friendly program", default=False, action="store_true")
    parser.add_argument("--verify", default=False, action="store_true")
    args = parser.parse_args()



    settings = Settings(args)
    set_global(settings)
    print(settings)
    del args

    base_request = get_base_request()
    try:
        with open(settings.payloadFile, "r") as f:
            payloaddata = f.read()
    except Exception as e:
        print(f"{red}Error: cannot read file {settings.payloadFile} Error: {e}{end}")
        exit(42)

    # payload file processing
    print(f"{dark_blue}Loading wordlist, please wait...{end}")
    payload = list(payloaddata.split('\n'))
    payload_len = len(payload)
    if settings.payload_offset > 0:
        print(f"{yellow}Starting from the payload n°{settings.payload_offset}/{payload_len}: '{payload[settings.payload_offset]}'{end}")
    print(f"{dark_blue}Loading done :}} !{end}\n")
    ### Attempt connection to each URL and print stats

    print(f"{bold}Time\tPayload_index\tStatus\tLength\tResponse_time\tPayload")
    print("-"*100+end)


    del payloaddata



    now = datetime.now()
    current_status = 0
    futures = set()
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        if settings.method == "GET":
            futures.update({executor.submit(get_, replace_string(settings.url, settings.replaceStr, p), p) for p in payload[settings.payload_offset:] } )
        elif settings.method == "POST":
            futures.update({executor.submit(post_, replace_string(settings.url, settings.replaceStr, p), replace_string(settings.data, settings.replaceStr, p), p) for p in payload[settings.payload_offset:] } )
        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for futu in done:
                try:
                    r, p = futu.result()
                    current_status = payload.index(p)
                except Exception as e:
                    print(f"{red}An Unhandled error occured in thread: {e}{end}")
                    pass
                else:
                    if r != None:
                        date_diff = datetime.now()-now
                        time_print = str(date_diff).split(".")[0]
                        if not (is_identical(r, base_request, p, settings.basePayload) ^ settings.matchBase):
                            status = r.status_code
                            response_len = len(r.text)-(len(p)) if p in r.text else len(r.text)
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
                                print(f"{' '*(settings.termlength)}", end="\r")
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{status}\t{length}\t{timer}\t\t{p}{end}")
                                if settings.out and len(r.content) != 0:
                                    try:
                                        with open(f"{settings.out}", 'ab+') as f:
                                            f.write(r.content)
                                    except Exception as e:
                                        print(f"{red}Error: could not write file {settings.out} Error: {e}{end}")
                            else:
                                print_nothing(time_print,current_status, payload_len, r, p)
                        else:
                            print_nothing(time_print,current_status, payload_len, r, p)

                    else:
                        print(f"{red}Request == None ??{end}")
    except KeyboardInterrupt:
        print(" "*settings.termlength, end="\r")
        print(f"{red}[KILLED] Process cancelled. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL: {yellow}{r.url}{end}"[:settings.termlength-20])
        print(f"\n{red}[-] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.{end}")
        executor._threads.clear()
        thread._threads_queues.clear()
    except Exception as e:
        print(" "*settings.termlength, end="\r")
        print(f"{red}[KILLED] Process killed. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL: {yellow}{r.url}{end}"[:settings.termlength-20])
        print(f"\n{red}[FATAL] Unhandled exception : {e}{end}")
        executor._threads.clear()
        thread._threads_queues.clear()

    print(f"{dark_blue}[+] Done{end}" + " "* settings.termlength)

if __name__ == '__main__':
    main()
