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

web_archive_ok = "data/webarchive_ok.txt"
web_archive_ko = "data/webarchive_ko.txt"
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


ok_list = get_file(web_archive_ok, field=0)
ko_list = get_file(web_archive_ko, field=0)

done = set(ok_list)#+ko_list)

links = [l for l in get_file(txt_links) if l not in done]

f_ok = open(web_archive_ok, "a+")
f_ko = open(web_archive_ko, "a+")

def signal_handler(signal, frame):
    f_ok.close()
    f_ko.close()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def save(l, archive_url):
    f_ok.write("%s\n" % (l))
    print(archive_url+"\n")
    done.add(l)

count_dom={}
for l in ok_list:
    dom = urlparse(l).netloc
    ok, ko = count_dom.get(dom, (0, 0))
    count_dom[dom]=(ok+1, ko)
for l in ko_list:
    dom = urlparse(l).netloc
    ok, ko = count_dom.get(dom, (0, 0))
    count_dom[dom]=(ok, ko+1)
total = len(links)


for l in reversed(links):
    total = total - 1
    if l not in done:
        dom = urlparse(l).netloc
        ok, ko = count_dom.get(dom, (0, 0))
        if ok==0 and ko>10:
            continue
        print("%d %s" % (total, l))
        try:
            archive_url = savepagenow.capture(l)
            save(l, archive_url)
            ok = ok + 1
        except savepagenow.api.CachedPage as e:
            _, archive_url = str(e).rsplit(None, 1)
            print(">", end=" ")
            save(l, archive_url)
        except Exception as e:
            txt = "%s %s\n" % (type(e).__name__, e)
            f_ko.write(l+" "+txt)
            print(txt)
            ko = ko + 1
        count_dom[dom]=(ok, ko)

f_ok.close()
f_ko.close()
