#!/usr/bin/python3

import re
import requests
from .utils import *

class Settings:
    def __init__(self, args):
        """
        Arguments parsing, we put everything into variables that will be accessible via the "settings" object.

        We will do some checks of the coherency of the arguments given.

        we will also preprocess some of the arguments.
        """
        if not args.url or not (args.payload or args.distant_payload or args.regexPayload):
            print(f"{red}Error, not enough args, see help (-h) for more details{end}")
            exit(42)
        if args.shuffle and args.offset:
            print(f"{yellow} WARNING: you're offseting shuffled payloads, thats dumb :/{end}", )

        self.verbosity = int(args.verbose)
        self.basePayload = args.basePayload
        self.url = args.url
        self.clean_url = "".join(re.findall(
            "https?:\/\/[a-z\dA-Z.-]+", self.url))
        self.difference = float(args.textDifference)
        self.difftimer = int(args.difftimer)
        self.excludeLength = parse_excluded_length(args.excludeLength)
        self.forceEncode = args.forceEncode
        self.throttle = float(args.throttle)
        self.httpcodesFilter, self.status_table_printable = parse_filter(
            args.filter)
        self.lengthFilter = parse_length_time_filter(args.lengthFilter)
        self.matchBase = args.matchBaseRequest
        self.devnull = open(os.devnull, 'w')
        self.stdout = self.devnull if self.verbosity < 2 else sys.__stdout__
        self.out = args.dumpHtml
        if self.out:
            self.fileStream = open(self.out, "ab+")
        self.payloadFile = args.payload
        self.distant_payload = args.distant_payload
        self.regexPayload = args.regexPayload
        self.payload_offset = int(args.offset)
        self.quick_ratio = args.quickRatio
        self.redir = args.redir
        self.replaceStr = args.replaceStr
        try:
            self.termlength = int(os.get_terminal_size()[0])
        except OSError:
            if self.verbosity < 2:
                self.termlength = 1
            else:
                exit(f"{red}You can't use pipe using this verbosity level, go down a little bit ! -v 1 is recommended. Thats for your own safety :){end}")
        self.threads = int(args.threads)
        self.timeFilter = parse_length_time_filter(args.timeFilter)
        self.timeout = int(args.timeout)
        self.uselessprint = not args.uselessprint
        self.verify = args.verify
        self.shuffle = True if args.shuffle else False
        self.headers = args.headers if args.headers == {} else self.loadHeaders(args.headers)
        self.headerprocess = True if self.replaceStr in str(self.headers) else False
        self.forceTest = args.ignoreBaseRequest
        self.base_request = {"req": None, "text": "", "time": 0, "status": 0}
        self.retry = True
        self.method = "GET"
        self.data = ""
        self.errors_count = 0
        self.retry_count = 0
        self.session = requests.Session()
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
        {light_blue}Payload URL: {end}{self.distant_payload}
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
