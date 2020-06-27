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
    parser.add_argument("-d", "--data", help="data for post request", default=None)
    parser.add_argument("-j", "--json", help="json for post request", default=None)
    parser.add_argument("-H", "--header", help="Give some extra headers, format: {'header_name': 'header Value'}", default='{}')
    parser.add_argument('-b', "--basePayload", help="Payload for base request", default="Sicarius")
    parser.add_argument("-f", "--filter", help="Filter positives match with httpcode, comma separated, to exclude one: n200", default='any')
    parser.add_argument("-l", "--lengthFilter", help='Specify the len range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument("-nl", "--excludeLength", help='Specify the len range that we\'ll use to deny responses (eg: 0,999 or any, if 3 values, we\'ll refuse EXACTLY this values)', default="none,none")
    parser.add_argument("-t", "--timeFilter", help='Specify the time range that we\'ll use to accept responses (eg: 0,999 or any, if 3 values, we\'ll accept EXACTLY this values)', default="any,any")
    parser.add_argument('-r', "--redir", dest="redir", default=False, action="store_true", help='Allow HTTP redirects')
    parser.add_argument("-m", '--matchBaseRequest', action="store_true", default=False)
    parser.add_argument("--offset", help="Start over where you stopped by giving the payload offset", default=0)
    parser.add_argument("--forceEncode", help="Force URL encode", action="store_true")
    parser.add_argument("--quickRatio", help="Force quick ratio of pages (a bit faster)", action="store_true", default=False)
    parser.add_argument("--textDifference", help="Percentage difference to match pages default: 99%%", default=0.99)
    parser.add_argument("--difftimer", help="Change the default matching timer (default 2000ms -> 2 seconds)", default=2000)
    parser.add_argument("--timeout", default=20)
    parser.add_argument("--threads", default=50)
    parser.add_argument("--verify", default=False, action="store_true")
    parser.add_argument("-S","--replaceStr", default="§")
    parser.add_argument('-o', '--dumpHtml', help='file to dump html content')
    args = parser.parse_args()

    if not args.url or not args.payload:
        print("Error, not enough args")
        parser.print_help()
        end_clean()
        exit(42)

    settings = Settings(args)
    set_global(settings)
    settings.__str__()
    del args

    base_request = get_base_request(settings.url, settings.redir, settings.basePayload)
    try:
        with open(settings.payloadFile, "r") as f:
            payloaddata = f.read()
    except Exception as e:
        print(f"Error: cannot read file {settings.payloadFile} Error: {e}")
        end_clean()
        exit(42)

    # payload file processing
    print_cursor("Loading wordlist, sorting uniq etc. please wait...", y="c", color="b")
    payload = list(payloaddata.split('\n'))
    del payloaddata
    payload_len = len(payload)
    if settings.payload_offset > 0:
        print(f"\033[93mStarting from the payload n°{settings.payload_offset}/{payload_len}: '{payload[settings.payload_offset]}'\033[0m")
    print_cursor(f"Loading done :}} !", y="c", color="n")
    ### Attempt connection to each URL and print stats

    print_header()

    now = datetime.now()
    current_status = 0
    futures = set()
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        if settings.method == "GET":
            futures.update({executor.submit(get_, replace_string(settings.url, p), p) for p in payload[settings.payload_offset:] } )

        if settings.method == "POST":
            replacePost = True if settings.replaceStr in settings.data else False
            replaceUrl = True if settings.replaceStr in settings.url else False

            futures.update({executor.submit(post_, data.replace(settings.url,p) if replaceUrl else settings.url\
                , data.replace(settings.data) if replacePost else settings.data, p) for p in payload[settings.payload_offset:] } )

        if settings.method == "JSON":
            replaceJson = True if settings.replaceStr in settings.json else False
            replaceUrl = True if settings.replaceStr in settings.url else False

            futures.update({executor.submit(json_, data.replace(settings.url,p) if replaceUrl else settings.url\
                , data.replace(settings.json) if replaceJson else settings.data, p) for p in payload[settings.payload_offset:] } )

        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for futu in done:
                try:
                    r, p = futu.result()
                    current_status = payload.index(p)
                except Exception as e:
                    print(f"An Unhandled error occured in thread: {e}")
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
                                color, status = color_status(status)
                                length = str(response_len)
                                timer = str(response_time)
                                url = unquote(r.url)
                                print_cursor(f"{' '*(settings.termlength)}", y="c", x=0)
                                print_cursor(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{status}\t{length}\t{timer}\t\t{p}", y="c", x=0, color=color, pad=(-1))
                                if settings.out and len(r.content) != 0:
                                    try:
                                        with open(f"{settings.out}", 'ab+') as f:
                                            f.write(settings.dump_request())
                                            f.write(r.content)
                                    except Exception as e:
                                        print(f"Error: could not write file {settings.out} Error: {e}")
                            else:
                                print_nothing(time_print,current_status, payload_len, r, p)
                        else:
                            print_nothing(time_print,current_status, payload_len, r, p)

    except KeyboardInterrupt:
        print_cursor(f"{' '*(settings.termlength)}", y="c", x=0)
        print_cursor(f"{' '*(settings.termlength)}", y="c", x=0)
        print_cursor(f"[KILLED] Process cancelled. Info:", y="c", x=0, color="f", pad=(-1))
        print_cursor("time: ", y="c", x=0, color="f"); print_cursor(f"{time_print}", color="w", pad=(-1))
        print_cursor("Payload index: ", y="c", x=0, color="f"); print_cursor(f"{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} ", color="w")
        print_cursor("Current URL: ", y="c", x=0, color="f"); print_cursor(f"{r.url}"[:settings.termlength-100], color="w")
        print_cursor(f"\n[FATAL] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.", color="f")

        executor._threads.clear()
        thread._threads_queues.clear()
        end_clean()
    except Exception as e:
        print_cursor(f"{' '*(settings.termlength)}", y="c", x=0)
        print_cursor(f"{' '*(settings.termlength)}", y="c", x=0)
        print_cursor(f"[KILLED] Process killed. Info: ", y="c", x=0, color="f", pad=(-1))
        print_cursor("time: ", y="c", x=0, color="f"); print_cursor(f"{time_print}", color="w")
        print_cursor(f"Payload index: {format(current_status, f'0{len(str(payload_len))}')}/{payload_len}", y="c", x=0, color="f")
        print_cursor(f"Current URL: {r.url}"[:settings.termlength-100], y="c", x=0, color="f")
        print_cursor(f"[FATAL] Unhandled exception : {e}", y="c", x=0, color="f")

        executor._threads.clear()
        thread._threads_queues.clear()
        end_clean()

    # reset terminal -> dirty



    print("\033[94m[+] Done\033[0m" + " "* settings.termlength)

if __name__ == '__main__':

    main()
