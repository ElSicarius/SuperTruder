#!/usr/bin/python3

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, CancelledError, thread
import os
import sys
from requests import get, post, packages
from urllib.parse import unquote, quote

import difflib
from datetime import datetime
from .utils import *
from .settings_class import *
import random

__version__ = "1.0"
__author__ = "Sicarius (@AMTraaaxX)"

# disable annoying warnings
packages.urllib3.disable_warnings()

def main():
    """
    Main process of the intruder
    """
    args = get_arguments()
    settings = Settings(args)
    print(f"\n{banner}########## SuperTruder v{__version__}, made with love by {__author__} ##########{end}", file=settings.stdout)
    set_global(settings)
    print(settings, file=settings.stdout if settings.verbosity > 2 else settings.devnull)
    del args

    
    base_request = get_base_request()
    payload = gen_payload()

    # payload processing
    if settings.shuffle:
        random.shuffle(payload)
    payload_len = len(payload)
    if settings.payload_offset > 0:
        print(
            f"{yellow}Starting from the payload n°{settings.payload_offset}/{payload_len}: '{payload[settings.payload_offset]}'{end}", file=settings.stdout)
    print(f"{dark_blue}Wordlist loaded ! We have {yellow}{payload_len}{dark_blue} items in this wordlist :}} {end}\n", file=settings.stdout)
    # Attempt connection to each URL and print stats

    # ugly stuff here
    printstr = "Time\tPayload_index\tStatus\tLength\tResponse_time\tPayload" if settings.verbosity > 1 else "Payload"
    print(f"{bold}{printstr}",
          file=settings.stdout)
    print("-" * 100 + end, file=settings.stdout)

    now = datetime.now()
    current_status = 0
    futures = set()
    # Starting requests
    try:
        executor = ThreadPoolExecutor(max_workers=settings.threads)
        futures.update({\
            executor.submit(request_handler\
                            , settings.url.replace(settings.replaceStr, p)\
                            , p\
                            , data=settings.data.replace(settings.replaceStr, p)\
                            ) for p in payload[settings.payload_offset:] })
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
                            # print status message(verbose > 2) only if httpcode, len & time are ok
                            if go_status and go_length and go_time:
                                status = color_status(status)
                                length = str(response_len)
                                timer = str(response_time)
                                url = r.url
                                print(f"{' '*(settings.termlength)}",
                                      end="\r", file=settings.stdout)
                                print(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{status}\t{length}\t{timer}\t\t{p}{end}" if not settings.verbosity < 2 else f"{p}{end}")

                                if settings.out and len(r.content) != 0:
                                    try:
                                        # write separator in the file
                                        settings.fileStream.write(
                                            bytes(f"###########################  {r.url}  #######################", "utf-8"))
                                        # write content
                                        settings.fileStream.write(r.content)
                                    except Exception as e:
                                        print(
                                            f"{red}Error: could not write file {settings.out} Error: {e}{end}", file=settings.stdout)
                            else:
                                #print the temmp thing
                                print_nothing(
                                    time_print, current_status, payload_len, r, p)
                        else:
                            #print the temps thing
                            print_nothing(
                                time_print, current_status, payload_len, r, p)
                    else:
                        pass
    except KeyboardInterrupt:
        # clear the line
        print(" " * settings.termlength, end="\r", file=settings.stdout)
        print(f"{red}[KILLED] Process cancelled. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL (encoded): {yellow}{r.url}{end}", file=settings.stdout)
        print(
            f"\n{red}[-] Keyboard interrupt recieved, gracefully exiting........... Nah kill everything.{end}", file=settings.stdout)
        executor._threads.clear()
        thread._threads_queues.clear()
    except Exception as e:
        #clear the line
        print(" " * settings.termlength, end="\r", file=settings.stdout)
        print(f"{red}[KILLED] Process killed. Info: \n{red}time: {yellow}{time_print} \n{red}Payload index: {yellow}{format(current_status, f'0{len(str(payload_len))}')}/{payload_len} -> \"{payload[current_status]}\" \n{red}Current URL (encoded): {yellow}{r.url}{end}", file=settings.stdout)
        print(f"\n{red}[FATAL] Unhandled exception : {e}{end}",
              file=settings.stdout)
        executor._threads.clear()
        thread._threads_queues.clear()


    #clear the line and print "Done" then more stats
    print(f"{dark_blue}[+] Done{end}" + " " *
          settings.termlength, file=settings.stdout)
    print(f"{dark_blue}[+] Time elapsed: {yellow}{time_print}",
          file=settings.stdout)
    print(
        f"{dark_blue}Errors encountered: {yellow}{settings.errors_count}, {dark_blue}requests retryed: {yellow}{settings.retry_count}{end}\n", file=settings.stdout)
    settings.session.close()

if __name__ == '__main__':
    main()
