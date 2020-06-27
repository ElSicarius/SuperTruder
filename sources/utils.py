#!/usr/bin/python3

import os
import sys
from requests import get, post
from urllib.parse import unquote, quote
import difflib
import re
import json
import curses


def set_global(settings):
    globals()["settings"] = settings


class Settings:
    def __init__(self,args):
        self.termlength, self.termlength_y = int(os.get_terminal_size()[0]), int(os.get_terminal_size()[1])
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
        self.header = json.loads(args.header)
        #self.args = args
        self.data = args.data
        self.json = args.json
        if args.data:
            self.method = "POST"
        elif args.json:
            self.method = "JSON"
        else:
            self.method = "GET"

        # Then
        self.print_str = self.locate_str()
        self.check_if_go()
        self.init_curses()

    def locate_str(self):
        where = str()

        if self.replaceStr in self.url:
            indexPosList = [ i for i in range(len(self.url)) if self.url[i] == self.replaceStr ][-1]
            try:
                where += self.url[indexPosList-1:indexPosList+1]+"\t"
            except IndexError:
                where += self.replaceStr+"\t"

        if self.header != {} :
            if self.replaceStr in str(self.header):

                indexPosList = [ i for i in range(len(str(self.header))) if str(self.header)[i] == self.replaceStr ][-1]

                try:
                    where += str(self.header)[indexPosList-1:indexPosList+1]+"\t"

                except IndexError:
                    where += self.replaceStr+"\t"



        if self.data != None:
            if self.replaceStr in self.data:
                indexPosList = [ i for i in range(len(self.data)) if self.data[i] == self.replaceStr ][-1]
                try:
                    where += self.data[indexPosList-1:indexPosList+1]+"\t"
                except IndexError:
                    where += self.replaceStr+"\t"

        if self.json != None:
            if self.replaceStr in str(self.json):
                indexPosList = [ i for i in range(len(str(self.json))) if str(self.json)[i] == self.replaceStr ][-1]
                try:
                    where += str(self.json)[indexPosList-1:indexPosList+1]+"\t"
                except IndexError:
                    where += self.replaceStr+"\t"
        return where


    def dump_request(self):
        return_string = b""
        if self.method == "GET":
            return_string = f"URL:{settings.url:b}"
        if self.method == "POST":
            return_string = f"URL:{settings.url:b}; data:{settings.data:b}"
        if self.method == "JSON":
            return_string = f"URL:{settings.url:b}; json:{settings.json:b}"
        return return_string


    def check_if_go(self):
        if self.data and self.json:
            print(f"Error, you've provided json & data ? that's dumb")
            parser.print_help()
            exit(42)
        if (self.method == "GET" and (not self.replaceStr in self.url and not self.replaceStr in str(self.header))):
            print(f"Error: Missing {self.replaceStr} in URL/Header provided")
            exit(42)
        if (self.method == "POST" and (not self.replaceStr in self.url and not self.replaceStr in str(self.header) and not self.replaceStr in self.data)):
            print(f"Error: Missing {self.replaceStr} in URL/Data/Header provided")
            exit(42)
        if (self.method == "JSON" and (not self.replaceStr in self.url and not self.replaceStr in str(self.header) and not self.replaceStr in self.json)):
            print(f"Error: Missing {self.replaceStr} in URL/Json/Header provided")
            exit(42)


    def __str__(self):
        if "any,any" in self.lengthFilter:
            length_message = "Selecting length matching: any"
        elif len(self.lengthFilter) == 2:
            length_message = f"Selecting responses len following: {self.lengthFilter[0]} <= len <= {self.lengthFilter[1]}"
        else:
            length_message = f"Selecting responses len is in: {self.lengthFilter}"

        if "any,any" in self.timeFilter:
            time_message = "Selecting response time matching: any"
        elif len(self.timeFilter) == 2:
            time_message = f"Selecting responses time following: {self.timeFilter[0]} <= time <= {self.timeFilter[1]}"
        else:
            time_message = f"Selecting responses time is in: {self.timeFilter}"


        # massive printing but it's beautiful once rendered, I swear
        print_cursor("Current global settings:", y="c", x=0, color="b")
        print_cursor("Url: ", y="c", x=4, color="g");                  print_cursor(f"{self.url}", color="lb")
        print_cursor("Payloads file: ", y="c", x=4, color="g");        print_cursor(f"{self.payloadFile}", color="lb")
        print_cursor("Base payload: ", y="c", x=4, color="g");         print_cursor(f"{self.basePayload}", color="lb")
        print_cursor("Redirections allowed: ", y="c", x=4, color="g"); print_cursor(f"{self.redir}", color="lb")
        print_cursor("Timeout of requests: ", y="c", x=4, color="g");  print_cursor(f"{self.timeout}", color="lb")
        print_cursor("Threads: ", y="c", x=4, color="g");              print_cursor(f"{self.threads}", color="lb")
        print_cursor("Force Encoding: ", y="c", x=4, color="g");       print_cursor(f'{"True" if self.forceEncode else "False"}', color="lb")
        print_cursor("Dumping HTML pages: ", y="c", x=4, color="g");   print_cursor(f'{"True, outfile:"+self.out if self.out else "False"}', color="lb")

        print_cursor("Current Trigger settings:", y="c", x=0, color="b")
        print_cursor("Selecting HTTP status code: ", y="c",x=4, color="g"); print_cursor(f"{self.httpcodesFilter}", color="lb")
        print_cursor(f"{length_message}", y="c",x=4, color="g")
        print_cursor(f"{time_message}", y="c",x=4, color="g")
        print_cursor("Excluding length mathing: ", y="c",x=4, color="g");   print_cursor(f"{self.excludeLength}", color="lb")
        print_cursor("Trigger time difference: ", y="c",x=4, color="g");    print_cursor(f"{self.difftimer}", color="lb")
        print_cursor("Match page techniques: ", y="c",x=4, color="g");      print_cursor(f'{"Quick ratio" if self.quick_ratio else "Strict ratio"}', color="lb")
        print_cursor("Match page difference: ", y="c",x=4, color="g");      print_cursor(f"difference <= {self.difference}", color="lb")


    def init_curses(self):
        self.stdscr = curses.initscr()
        self.cursor = 0
        curses.noecho()
        self.stdscr.scrollok(True)
        curses.start_color()
        # define colors
        # fail
        curses.init_color(1, 240*4,  85*4,   85*4)
        # Green
        curses.init_color(2, 85*4,   250*4,   85*4)
        # light blue
        curses.init_color(3, 0,   215*4,   250*4)
        # warning
        curses.init_color(4, 250*4,   250*4,   170*4)
        # dark blue
        curses.init_color(5, 0, 85*4, 250*4)

        # init pairs
        # fail
        curses.init_pair(1, 1, curses.COLOR_BLACK)
        # Green
        curses.init_pair(2, 2, curses.COLOR_BLACK)
        # Light Blue
        curses.init_pair(3, 3, curses.COLOR_BLACK)
        # warning
        curses.init_pair(4, 4, curses.COLOR_BLACK)
        # dark blue
        curses.init_pair(5, 5, curses.COLOR_BLACK)
        # normal
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)


def get_base_request(url, redir, payload):
    h = settings.header
    if settings.replaceStr in str(settings.header):
        h = json.loads(replace_string(str(h), payload).replace("'",'"'))
    try:
        req = get(url.replace(settings.replaceStr, payload), allow_redirects=settings.redir, verify=settings.verify, headers=h, timeout=settings.timeout)
    except Exception as e:
        print(f"An error occured while requesting base request, Stopping here. Error: {e}")
        end_clean()

    print_cursor(f"Base request info:", y="c", x=0, color="b")
    color, status = color_status(req.status_code)
    print_cursor(f"status: ", y="c", x=4, color="g"); print_cursor(f"{status},",color=color)
    print_cursor(f"content-length: ", y="c", x=4, color="g"); print_cursor(f"{len(req.text)-(len(payload)) if payload in req.text else len(req.text)},",color="n")
    print_cursor(f"request time: ", y="c", x=4, color="g"); print_cursor(f"{round(req.elapsed.total_seconds()*1000, 3)}\n", color="n")
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
    if len(splitted) >2 :
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
            print_cursor(f"Error in excluded length argument, make sure it's like: 2566 or 2566,5550, Error: {e}", y="c", x=0, color="f")
            end_clean()

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
    color = "n"
    if status[0] == str(5):
        color = "f"
    elif status[0] == str(4) and status[2] != str(3):
        color = "w"
    elif status == "403":
        color = "b"
    elif status[0] == str(3):
        color = "lb"
    return color, status


def get_(url, parameter):
    h = settings.header
    if settings.replaceStr in settings.header:
        h = json.loads(replace_string(str(h), parameter).replace("'",'"'))
    try:
        req = get(url, timeout=settings.timeout, allow_redirects=settings.redir, verify=settings.verify, headers=h)
    except Exception as e:
        print_cursor(f"Error with arg {parameter}: {e}", y="c", x=0, color="f")
        req = None
    return (req, parameter)


def post_(url, data, parameter):
    h = settings.header
    if settings.replaceStr in settings.header:
        h = json.loads(replace_string(str(h), parameter).replace("'",'"'))
    try:
        req = post(url, timeout=settings.timeout, allow_redirects=settings.redir, verify=settings.verify, headers=h, data=data)
    except Exception as e:
        print_cursor(f"Error with arg {parameter}: {e}", y="c", x=0, color="f")
        req = None
    return (req, parameter)


def json_(url, json, parameter):
    h = settings.header
    if settings.replaceStr in settings.header:
        h = json.loads(replace_string(str(h), parameter).replace("'",'"'))
    try:
        req = post(url, timeout=settings.timeout, allow_redirects=settings.redir, verify=settings.verify, headers=h, json=json)
    except Exception as e:
        print_cursor(f"Error with arg {parameter}: {e}", y="c", x=0, color="f")
        req = None
    return (req, parameter)


def replace_string(data, repl):
    return data.replace(settings.replaceStr, quote(repl) if settings.forceEncode else repl)


def print_nothing(time_print,current_status, payload_len, r, parameter, end="\r"):
    pay = replace_string(settings.print_str, parameter)
    # clean the line but not everything
    print_cursor(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t \t \t \t\t "[:settings.termlength-50], y="c",x=0)
    # print over the cleaned line
    print_cursor(f"{time_print}\t{format(current_status, f'0{len(str(payload_len))}')}/{payload_len}\t{r.status_code}\t{len(r.content)}\t{int(r.elapsed.total_seconds()*1000)}\t\t{pay}"[:settings.termlength-50], y="c",x=0, pad=(-1))
    # print url
    print_cursor(r.url, y="c",x=0,)
    # go back 2 lines above to rewrite the lines
    settings.cursor -= 2

def print_cursor(what, y=None, x=None, color="n", pad=0):
    # choosing the color pair with the letter given in parameter
    # I wanted to keep letters to choose the colors -> easy to remember
    # Neutral
    if color.lower() == "n":
        color = curses.color_pair(6)
    # Fail
    elif color.lower() == "f":
        color = curses.color_pair(1)
    # Green
    elif color.lower() == "g":
        color = curses.color_pair(2)
    # Blue (dark)
    elif color.lower() == "b":
        color = curses.color_pair(5)
    # Warning
    elif color.lower() == "w":
        color = curses.color_pair(4)
    # Light blue
    elif color.lower() == "lb":
        color = curses.color_pair(3)
    # take off the moufles
    else:
        exit("Unrecognized color")

    # "c" == current cursor in my mind
    if y == "c" :
        y = settings.cursor + 1 + pad
        settings.cursor = y
        x = x if x != None else 0
    else:
        t_y, t_x = settings.stdscr.getyx()
        x = t_x if x == None else x
        y = t_y if y == None else y

    # end of line -> go back at 0
    if x > settings.termlength - 1:
        x = 0
        y += 1
    # don't print on the last 3 lines
    if y >= settings.termlength_y - 3:
        settings.stdscr.scroll()
        t_y, t_x = settings.stdscr.getyx()
        y = t_y
        settings.cursor = y

    try:
        settings.stdscr.addstr(y, x, what, color)
        settings.stdscr.refresh()
    except curses.error:
        print("error")


def print_header():
    temp = "Time\tPayload_index\tStatus\tLength\tResponse_time\t"
    if settings.replaceStr in settings.url:
        temp += "Url\t"
    if settings.header != {} :
        if settings.replaceStr in str(settings.header):
            temp += "Header\t"
    if settings.data != None:
        if settings.replaceStr in settings.data:
            temp += "Data\t"
    if settings.json != None:
        if settings.replaceStr in settings.json:
            temp += "Json\t"

    print_cursor(temp, y="c", color="n")
    print_cursor("-"*150, y="c", color="n")


def end_clean():
    os.system("stty sane")
    print("\n")
    exit(42)


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
