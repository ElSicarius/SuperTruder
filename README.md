# SuperTruder
An intruder custom that gave me bounties

```
usage: intruder.py [-h] [-u URL] [-p PAYLOAD] [-b BASEPAYLOAD] [-f FILTER] [-l LENGTHFILTER] [-nl EXCLUDELENGTH] [-t TIMEFILTER] [-r] [-m] [--difftimer DIFFTIMER] [--timeout TIMEOUT] [--threads THREADS] [-d REPLACESTR] [-o DUMPHTML]

Enumerate all domains for a target

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Url to test
  -p PAYLOAD, --payload PAYLOAD
                        payload file
  -b BASEPAYLOAD, --basePayload BASEPAYLOAD
                        Payload for base request
  -f FILTER, --filter FILTER
                        Filter positives match with httpcode, comma separated, to exclude one: n200
  -l LENGTHFILTER, --lengthFilter LENGTHFILTER
                        Specify the len range that we'll use to accept responses (eg: 0,999 or any, if 3 values, we'll accept EXACTLY this values)
  -nl EXCLUDELENGTH, --excludeLength EXCLUDELENGTH
                        Specify the len range that we'll use to deny responses (eg: 0,999 or any, if 3 values, we'll refuse EXACTLY this values)
  -t TIMEFILTER, --timeFilter TIMEFILTER
                        Specify the time range that we'll use to accept responses (eg: 0,999 or any, if 3 values, we'll accept EXACTLY this values)
  -r, --redir           Allow HTTP redirects
  -m, --matchBaseRequest
  --difftimer DIFFTIMER
                        Change the default matching timer (default 2000ms -> 2 seconds)
  --timeout TIMEOUT
  --threads THREADS
  -d REPLACESTR, --replaceStr REPLACESTR
  -o DUMPHTML, --dumpHtml DUMPHTML
                        file to dump html content
```

# Note
I'm using colored printing coz it's beautiful.

# Todo
