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
    parser.add_argument('-u', "--url",help='Url to test',)
    parser.add_argument('-p', "--payload",help='payload file',)
    parser.add_argument('-b', "--basePayload", help="Payload for base request", default="Sicarius")
    parser.add_argument("-f", "--filter", help="Filter positives match with httpcode, comma separated, to exclude one: n200", default='any')
    parser.add_argument("-l", "--lengthFilter", help='Specify the len range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument("-nl", "--excludeLength", help='Specify the len range that we\'ll use to deny responses (eg: 0,999 or any, if 3 values, we\'ll refuse EXACTLY this values)', default="none,none")
    parser.add_argument("-t", "--timeFilter", help='Specify the time range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument('-r', "--redir", dest="redir", default=False, action="store_true", help='Allow HTTP redirects')
    parser.add_argument("-m", '--matchBaseRequest', action="store_true", default=False)
    parser.add_argument("--forceEncode", help="Force URL encode", action="store_true")
    parser.add_argument("--quickRatio", help="Force quick ratio of pages (a bit faster)", action="store_true", default=False)
    parser.add_argument("--textDifference", help="Percentage difference to match pages default: 99%", default=0.99)
    parser.add_argument("--difftimer", help="Change the default matching timer (default 2000ms -> 2 seconds)", default=2000)
    parser.add_argument("--timeout", default=20)
    parser.add_argument("--threads", default=50)
    parser.add_argument("--verify", default=False, action="store_true")
    parser.add_argument("-d","--replaceStr", default="§")
    parser.add_argument('-o', '--dumpHtml', help='file to dump html content')
    args = parser.parse_args()

    if not args.url or not args.payload:
        print("Error, not enough args")
        parser.print_usage()
        exit(42)
    if args.replaceStr not in args.url:
        print(f"Error: Missing {args.replaceStr} in URL provided")
        parser.print_usage()
        exit(42)

    settings = Settings(args)
    set_global(settings)
    print(settings)
    del args

    base_request = get_base_request(settings.url, settings.redir, settings.basePayload)
    try:
        with open(settings.payloadFile, "r") as f:
            payloaddata = f.read()
    except Exception as e:
        print(f"Error: cannot read file {settings.payloadFile} Error: {e}")
        exit(42)

    print(f"\033[94mLoading wordlist, please wait...\n\033[0m")
    payload = set(payloaddata.split('\n'))
    print(f"\033[1mDone :}} !\033[0m\n")
    ### Attempt connection to each URL and print stats

    print("Time\tPayload_index\tStatus\tLength\tResponse_time\tUrl")
    print("-"*100)


    del payloaddata
    payload_len = len(payload)
    now = datetime.now()
    current_status = 0
    futures = set()
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        futures.update({executor.submit(get_, settings.url.replace(settings.replaceStr, quote(p) if settings.forceEncode else p), p) for p in payload } )
        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for futu in done:
                try:
                    r, p = futu.result()
                    current_status = payload.index(p)-1
                except Exception as e:
                    #print(f"An Unhandled error occured in thread: {e}")
                    pass
                else:
                    if r != None:
                        date_diff = datetime.now()-now
                        time_print = str(date_diff).split(".")[0]
                        if not (is_identical(r, base_request, p, settings.basePayload) ^ settings.matchBase):
                            status = r.status_code
                            response_len = len(r.text)-(len(p))
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
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{status}\t{length}\t{timer}\t\t{url}\033[0m")
                                if settings.out and len(r.content) != 0:
                                    try:
                                        with open(f"{settings.out}", 'ab+') as f:
                                            f.write(r.content)
                                    except Exception as e:
                                        print(f"Error: could not write file {settings.out} Error: {e}")
                            else:
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t   \t     \t     \t\t{settings.clean_url+' '*settings.termlength}"[:settings.termlength-100], end="\r")
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{r.status_code}\t{len(r.content)}\t{int(r.elapsed.total_seconds()*1000)}\t\t{r.url}"[:settings.termlength-100], end="\r")
                        else:
                            print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t   \t     \t     \t\t{settings.clean_url+' '*settings.termlength}"[:settings.termlength-100], end="\r")
                            print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{r.status_code}\t{len(r.content)}\t{int(r.elapsed.total_seconds()*1000)}\t\t{r.url}"[:settings.termlength-100], end="\r")

                    else:
                        print("Request == None ??")
    except KeyboardInterrupt:
        print(f"{' '*(settings.termlength-1)}", end="\r")
        print(f"\033[91m[-] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.\033[0m")
        executor._threads.clear()
        thread._threads_queues.clear()
    except Exception as e:
        print(f"\033[91m[FATAL] Unhandled exception : {e}\033[0m")
        executor._threads.clear()
        thread._threads_queues.clear()

    print("\033[94m[+] Done\033[0m" + " "* settings.termlength)

if __name__ == '__main__':
    main()
