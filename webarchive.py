#!/usr/bin/python3
import os
import requests
import savepagenow
import signal
from urllib.parse import urlparse
import urllib3
import sys
from glob import glob

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

web_archive = "data/webarchive.txt"
web_archive_error = "data/webarchive_error.txt"
txt_links = "data/links.txt"

def get_file(name, field=None):
    lines = []
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    if field is not None:
                        l = l.split()
                        lines.append(l[field])
                    else:
                        lines.append(l)
    return lines

def parse_url(url):
    #url = url.replace("http://", "https://")
    r = requests.get(url, allow_redirects=False, verify=False)
    if int(r.status_code/100) in (4, 5):
        return None
    if r.headers and 'location' in r.headers:
        return r.headers['location']
    return url

done = set(
    get_file(web_archive, field=0) +
    get_file(web_archive_error, field=0)
)

links = get_file(txt_links)

f = open(web_archive, "a+")
f_error = open(web_archive_error, "a+")

def signal_handler(signal, frame):
       f.close()
       f_error.close()
       sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def save(l, _l, archive_url):
    f.write("%s %s\n" % (l, archive_url))
    print(archive_url+"\n")
    done.add(_l)

for l in links:
    if l not in done:
        _l = parse_url(l)
        if _l and _l not in done:
            print(_l)
            try:
                archive_url = savepagenow.capture(_l)
                save(l, _l, archive_url)
            except savepagenow.api.CachedPage as e:
                _, archive_url = str(e).rsplit(None, 1)
                print(">", end=" ")
                save(l, _l, archive_url)
            except Exception as e:
                txt = "%s %s\n" % (type(e).__name__, e)
                f_error.write(l+" "+txt)
                print(txt)

f.close()
f_error.close()
