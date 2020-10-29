#!/usr/bin/python3

from base64 import b64encode

def process(payload):
    if not isinstance(payload, bytes):
        return b64encode(payload.encode("utf-8")).decode("utf8")
    else:
         return b64encode(payload).decode("utf8")
