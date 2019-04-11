#!/usr/bin/python3
import os
import requests
import savepagenow
import signal
from urllib.parse import urlparse
import urllib3
import sys
from glob import glob
from socket import gethostbyname, gaierror
import re

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

re_file_ip = re.compile(r".*?/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.txt$")

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
    url = url.replace("http://", "https://")
    r = requests.get(url, allow_redirects=False, verify=False)
    if int(r.status_code/100) in (4, 5):
        return None
    if r.headers and 'location' in r.headers:
        return r.headers['location']
    return url

def get_ip(dom):
    try:
        return gethostbyname(dom)
    except gaierror as e:
        print("%s %s" % (dom, e))
        return -1

done = set(get_file(web_archive, field=0))
done = done.union(set(get_file(web_archive_error, field=0)))

if not os.path.isfile(txt_links):
    ips={}
    links=set()
    for txt in glob("data/*.txt"):
        m = re_file_ip.match(txt)
        if m:
            IP = m.group(1)
            print(IP)
            for l in get_file(txt):
                if l not in done:
                    dom = urlparse(l).netloc
                    if dom not in ips:
                        ips[dom] = get_ip(dom)
                    if ips[dom] == IP:
                        links.add(l)
    links=sorted(links)
    with open(txt_links, "w") as f:
        f.write("\n".join(links))
    print("")
else:
    links = get_file("data/links.txt")

f = open(web_archive, "w+")
f_error = open(web_archive_error, "w+")

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
                save(l, _l, archive_url)
            except Exception as e:
                txt = "%s %s\n" % (type(e).__name__, e)
                f_error.write(l+" "+txt)
                print(txt)

f.close()
f_error.close()
