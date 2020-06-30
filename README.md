# SuperTruder
An intruder custom that gave me bounties

# Command examples

- fuzz anything in the url:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f 200 -u "https://example.com/id=§" `

- Fuzz anything in the POST data, and don't select 404 & 302 responses:
`python3 supertruder.py -p database/3digits.txt --threads 15 -f n404,n302 -u "https://example.com/" -d "id=§"`

- Fuzz a list of urls and save contents:
`python3 supertruder.py --threads 100 -p tests/urls.urls -u "§" --ignoreBaseRequest --timeout 30 -o htmldump.html`

- Fuzz something and match EXACTLY a response type, text and everything you know:
`python3 supertruder.py --threads 20 -p database/payloads.txt -u "http://example.com/specialparameter=§" -b "mySpecialParameter" --matchBaseRequest`

- Fuzz something and match responses with content-length in range or matching values:
`python3 supertruder.py --threads 20 -p database/payloads.txt -u "http://example.com/lengthchanging=§" -l 2000,2300 -nl 2250,2251`

[...]

# Usage
```
usage: supertruder.py [-h] [-S REPLACESTR] [-d DATA] [-f FILTER] [-l LENGTHFILTER] [-m] [-el EXCLUDELENGTH] [-t TIMEFILTER] [-b BASEPAYLOAD] [-o DUMPHTML] [-p PAYLOAD] [-r] [-u URL] [-H HEADERS]
                      [--difftimer DIFFTIMER] [--forceEncode] [--offset OFFSET] [--quickRatio] [--textDifference TEXTDIFFERENCE] [--threads THREADS] [--timeout TIMEOUT] [--uselessprint] [--verify]
                      [--ignoreBaseRequest]

SuperTruder: Fuzz something, somewhere in an URL

optional arguments:
  -h, --help            show this help message and exit
  -S REPLACESTR, --replaceStr REPLACESTR
  -d DATA, --data DATA  Add POST data
  -f FILTER, --filter FILTER
                        Filter positives match with httpcode, comma separated, to exclude one: n200
  -l LENGTHFILTER, --lengthFilter LENGTHFILTER
                        Specify the len range that we'll use to accept responses (eg: 0,999 or any, if 3 values, we'll accept EXACTLY this values)
  -m, --matchBaseRequest
  -el EXCLUDELENGTH, --excludeLength EXCLUDELENGTH
                        Specify the len range that we'll use to deny responses (eg: 0,999 or any, if 3 values, we'll refuse EXACTLY this values)
  -t TIMEFILTER, --timeFilter TIMEFILTER
                        Specify the time range that we'll use to accept responses (eg: 0,999 or any, if 3 values, we'll accept EXACTLY this values)
  -b BASEPAYLOAD, --basePayload BASEPAYLOAD
                        Payload for base request
  -o DUMPHTML, --dumpHtml DUMPHTML
                        file to dump html content
  -p PAYLOAD, --payload PAYLOAD
                        payload file
  -r, --redir           Allow HTTP redirects
  -u URL, --url URL     Url to test
  -H HEADERS, --headers HEADERS
                        Add extra Headers (syntax: "header: value,header2: value2")
  --difftimer DIFFTIMER
                        Change the default matching timer (default 2000ms -> 2 seconds)
  --forceEncode         Force URL encode
  --offset OFFSET       Start over where you stopped by giving the payload offset
  --quickRatio          Force quick ratio of pages (a bit faster)
  --textDifference TEXTDIFFERENCE
                        Percentage difference to match pages default: 99%
  --threads THREADS
  --timeout TIMEOUT
  --uselessprint        Enable Louka-friendly program
  --verify
  --ignoreBaseRequest   Force testing even if base request failed
```

# Note
I'm using colored printing coz it's beautiful. you can't disable it (yet).

Not happy with \r printing ? use `--uselessprint` flag.

# Todo

- Add headers to request

- Work on a post fuzzing feature
- Work on a headers fuzzing feature

# Ideas
-> for fuzzing -> create a raw request ?

# It's beautiful

https://asciinema.org/a/8ISmRJSnqop9j0cBW6GlpB5Wr
