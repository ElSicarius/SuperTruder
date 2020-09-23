# SuperTruder
An intruder custom that gave me bounties

If the code is disgusting, it's okay, I can live with it :)

This program is pip-free ! no need to install any shitty pip package to work (excepted Requests ofc). You're welcome.

# Command examples

- fuzz anything in the url:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f 200 -u "https://example.com/id=§" `

- fuzz anything in the url & output only the results:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f 200 -u "https://example.com/id=§" -q `

- fuzz anything in the url but use a pattern (regex) to generate your payload list:
`python3 supertruder.py -R "[\d]{3}" -u "https://test.site/index.php?id=§" --threads 15 -f 200`

- Fuzz anything in the url with a distant payload file:
`python3 supertruder.py -u "https://google.fr/§" -P https://raw.githubusercontent.com/danielmiessler/SecLists/master/Fuzzing/1-4_all_letters_a-z.txt --threads 20 -f n50x`

- Fuzz anything in the POST data, and don't select 404 & 302 responses:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f n404,n302 -u "https://example.com/" -d "id=§"`

- Fuzz anything in the URL, and don't select 40x responses:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f n40x -u "https://example.com/§" `

- Fuzz anything in the URL, and select only 50x responses:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f 50x -u "https://example.com/§" `

- Fuzz a list of urls and save contents (useful in bughunting):
`python3 supertruder.py --threads 100 -p tests/urls.urls -u "§" --ignoreBaseRequest --timeout 30 -o htmldump.html`

- Fuzz something and match EXACTLY a response type, text and everything you know:
`python3 supertruder.py --threads 20 -p database/payloads.txt -u "http://example.com/specialparameter=§" -b "mySpecialValue" --matchBaseRequest`

- Fuzz something and match responses with content-length in range or matching values:
`python3 supertruder.py --threads 20 -p database/payloads.txt -u "http://example.com/lengthchanging=§" -l 2000,2300 -el 2250,2251`

- Fuzz something in the headers of the request:
`python3 supertruder.py --threads 30 -p database/3d.txt -u "https://google.fr/" -f n403,n404,n400 -H "IS-THIS-A-REAL-HEADER: §" -o reports/google_header_3digitspayload.html`

- Fuzz a list of urls but shuffle them before:
`python3 supertruder.py -t 10 --ignoreBaseRequest -u "§" -p /mnt/c/Users//BugBounty/program1/urls_multiple_hosts -f n30x -q --shuffle`

The limit is pretty much your imagination...

# Usage
```
usage: supertruder.py [-h] [-u URL] [-p PAYLOAD] [-P DISTANT_PAYLOAD]
                      [-d DATA] [-b BASEPAYLOAD] [-H HEADERS] [-S REPLACESTR]
                      [-f FILTER] [-l LENGTHFILTER] [-m] [-el EXCLUDELENGTH]
                      [-t TIMEFILTER] [-o DUMPHTML] [--offset OFFSET] [-r]
                      [--forceEncode] [--timeout TIMEOUT]
                      [--throttle THROTTLE] [--verify] [--difftimer DIFFTIMER]
                      [--textDifference TEXTDIFFERENCE] [--quickRatio]
                      [--threads THREADS] [--ignoreBaseRequest]
                      [--uselessprint]

SuperTruder: Fuzz something, somewhere in an URL, data or HTTP headers

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Url to test
  -p PAYLOAD, --payload PAYLOAD
                        payload file
  -P DISTANT_PAYLOAD, --distant_payload DISTANT_PAYLOAD
                        use an online wordlist instead of a local one (do not
                        use if your internet connection is shit, or the
                        wordlist weight is like To)
  -d DATA, --data DATA  Add POST data
  -b BASEPAYLOAD, --basePayload BASEPAYLOAD
                        Payload for base request
  -H HEADERS, --headers HEADERS
                        Add extra Headers (syntax: "header: value\nheader2:
                        value2")
  -S REPLACESTR, --replaceStr REPLACESTR
  -f FILTER, --filter FILTER
                        Filter positives match with httpcode, comma separated,
                        to exclude one: n200
  -l LENGTHFILTER, --lengthFilter LENGTHFILTER
                        Specify the len range that we'll use to accept
                        responses (eg: 0,999 or any, if 3 values, we'll accept
                        EXACTLY this values)
  -m, --matchBaseRequest
  -el EXCLUDELENGTH, --excludeLength EXCLUDELENGTH
                        Specify the len range that we'll use to deny responses
                        (eg: 0,999 or any, if 3 values, we'll refuse EXACTLY
                        this values)
  -t TIMEFILTER, --timeFilter TIMEFILTER
                        Specify the time range that we'll use to accept
                        responses (eg: 0,999 or any, if 3 values, we'll accept
                        EXACTLY this values)
  -o DUMPHTML, --dumpHtml DUMPHTML
                        file to dump html content
  --offset OFFSET       Start over where you stopped by giving the payload
                        offset
  -r, --redir           Allow HTTP redirects
  --forceEncode         Force URL encode
  --timeout TIMEOUT
  --throttle THROTTLE   throttle between the requests
  --verify
  --difftimer DIFFTIMER
                        Change the default matching timer (default 2000ms -> 2
                        seconds)
  --textDifference TEXTDIFFERENCE
                        Percentage difference to match pages default: 99%
  --quickRatio          Force quick ratio of pages (a bit faster)
  --threads THREADS
  --ignoreBaseRequest   Force testing even if base request failed
  --uselessprint        Disable useless self-rewriting print (with '\r')

Tired of using ffuf ? Tired of using burp's slow intruder ? Checkout SuperTruder, an intruder that isn't hard to use, or incredibly slow Made with love by Sicarius (@AMTraaaxX)
```

# Note
I'm using colored printing coz it's beautiful. you can't disable it (yet).
if you REALLLY want to disable it, replace the color values in const.py with empty values.

Not happy with \r printing ? use `--uselessprint` flag.

# Todo
?

# Ideas
-> for fuzzing -> create a raw request ?

# It's beautiful

<a href="https://asciinema.org/a/NxUbbjcZI4uCE2Y8ch2Ecw3s8"><img src="./images/asciinema.gif"/></a>
