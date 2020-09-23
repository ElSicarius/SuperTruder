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
import random

__version__ = "1.0"
__author__ = "Sicarius (@AMTraaaxX)"


def main():
    packages.urllib3.disable_warnings()

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
                        help="Payload for base request", default="Sicarius")
    parser.add_argument("-H", "--headers", default={},
                        help="Add extra Headers (syntax: \"header: value\\nheader2: value2\")")
    parser.add_argument("-S", "--replaceStr", default="§")

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

    args = parser.parse_args()

    settings = Settings(args)
    print(f"\n{banner}########## SuperTruder v{__version__}, made with love by {__author__} ##########{end}", file=settings.stdout)
    set_global(settings)
    print(settings, file=settings.stdout)
    del args

    base_request = get_base_request()

    print(f"\n{dark_blue}Loading wordlist, please wait...{end}",
          file=settings.stdout)
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
    # payload file processing

    if settings.shuffle:
        random.shuffle(payload)
    payload_len = len(payload)
    if settings.payload_offset > 0:
        print(
            f"{yellow}Starting from the payload n°{settings.payload_offset}/{payload_len}: '{payload[settings.payload_offset]}'{end}", file=settings.stdout)
    print(f"{dark_blue}Wordlist loaded ! We have {yellow}{payload_len}{dark_blue} items in this wordlist :}} {end}\n", file=settings.stdout)
    # Attempt connection to each URL and print stats

    # ugly stuff here
    printstr = "Time\tPayload_index\tStatus\tLength\tResponse_time\tPayload" if not settings.quietmode else "Payload"
    print(f"{bold}{printstr}",
          file=settings.stdout)
    print("-" * 100 + end, file=settings.stdout)

    # We're not like chrome
    del payloaddata

    now = datetime.now()
    current_status = 0
    futures = set()
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        if settings.method == "GET":
            futures.update({executor.submit(get_, replace_string(
                settings.url, settings.replaceStr, p), p) for p in payload[settings.payload_offset:]})
        elif settings.method == "POST":
            futures.update({executor.submit(post_, replace_string(settings.url, settings.replaceStr, p), replace_string(
                settings.data, settings.replaceStr, p), p) for p in payload[settings.payload_offset:]})
        while futures:
            done, futures = wait(futures, return_when=FIRST_COMPLETED)
            for futu in done:
                try:
                    r, p = futu.result()
                    current_status = payload.index(p)
                except Exception as e:
                    print(
                        f"{red}An Unhandled error occured in thread: {e}{end}", file=settings.stdout)
                    pass
                else:
                    if r != None:
                        date_diff = datetime.now() - now
                        time_print = str(date_diff).split(".")[0]
                        if not (is_identical(r, p) ^ settings.matchBase):
                            status = r.status_code
                            response_len = len(r.text) - \
                                (len(p) * calc_remove_len(r, p))
                            response_time = int(
                                r.elapsed.total_seconds() * 1000)
                            # Determine if the http status code is good to be printed
                            go_status = status_matching(status)
                            # Determine if the length is good to be printed
                            go_length = length_matching(response_len)
                            # Determine if the time to response is good to be printed
                            go_time = time_matching(response_time)
                            # print status message only if httpcode & len are ok
                            if go_status and go_length and go_time:
                                status = color_status(status)
                                length = str(response_len)
                                timer = str(response_time)
                                url = r.url if not settings.forceEncode else unquote(
                                    r.url)
                                print(f"{' '*(settings.termlength)}",
                                      end="\r", file=settings.stdout)
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{status}\t{length}\t{timer}\t\t{p}{end}" if not settings.quietmode else f"{p}{end}")

                                if settings.out and len(r.content) != 0:
                                    try:
                                        settings.fileStream.write(
                                            bytes(f"###########################  {r.url}  #######################", "utf-8"))
                                        settings.fileStream.write(r.content)
                                    except Exception as e:
                                        print(
                                            f"{red}Error: could not write file {settings.out} Error: {e}{end}", file=settings.stdout)
                            else:
                                print_nothing(
                                    time_print, current_status, payload_len, r, p)
                        else:
                            print_nothing(
                                time_print, current_status, payload_len, r, p)

                    else:
                        pass
    except KeyboardInterrupt:
        print(" " * settings.termlength, end="\r", file=settings.stdout)
        print(f"{red}[KILLED] Process cancelled. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL (encoded): {yellow}{r.url}{end}", file=settings.stdout)
        print(
            f"\n{red}[-] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.{end}", file=settings.stdout)
        executor._threads.clear()
        thread._threads_queues.clear()
    except Exception as e:
        print(" " * settings.termlength, end="\r", file=settings.stdout)
        print(f"{red}[KILLED] Process killed. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL (encoded): {yellow}{r.url}{end}", file=settings.stdout)
        print(f"\n{red}[FATAL] Unhandled exception : {e}{end}",
              file=settings.stdout)
        executor._threads.clear()
        thread._threads_queues.clear()

    print(f"{dark_blue}[+] Done{end}" + " " *
          settings.termlength, file=settings.stdout)
    print(f"{dark_blue}[+] Time elapsed: {yellow}{time_print}",
          file=settings.stdout)
    print(
        f"{dark_blue}Errors encountered: {yellow}{settings.errors_count}, {dark_blue}requests retryed: {yellow}{settings.retry_count}{end}\n", file=settings.stdout)


if __name__ == '__main__':
    main()
