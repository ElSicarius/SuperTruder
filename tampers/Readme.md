
# How to make your own tamper script 

It's very simple ! you only need to create a function named "process" that takes **one** parameter in input and returns a single **string** *(Make sure it is not bytes)*.

for example:
```
#!/usr/bin/python3

from urllib.parse import quote

def process(payload):
    """
    Takes a payload in input
    :returns the string quoted
    """
    return quote(payload)
```