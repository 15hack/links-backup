#!/usr/bin/env python3
import os
import re
import signal
import sys
from urllib.parse import urlparse

import requests
import savepagenow
import urllib3

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

web_archive_ok = "data/webarchive_ok.txt"
web_archive_ko = "data/webarchive_ko.txt"
txt_links = "data/links.txt"


def reader(name):
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    yield l


def get_links(name):
    for l in reader(name):
        l = l.split()[0]
        if l.startswith("http"):
            l = l.split("://", 1)[-1]
        yield l


ok_list = list(get_links(web_archive_ok))
ko_list = list(get_links(web_archive_ko))

done = set(ok_list)  # +ko_list)

links = [l for l in reader(txt_links) if l.split("://", 1)[-1] not in done]


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


count_dom = {}
for l in ok_list:
    dom = urlparse(l).netloc
    ok, ko = count_dom.get(dom, (0, 0))
    count_dom[dom] = (ok+1, ko)
for l in ko_list:
    dom = urlparse(l).netloc
    ok, ko = count_dom.get(dom, (0, 0))
    count_dom[dom] = (ok, ko+1)
total = len(links)


for l in sorted(links):
    total = total - 1
    if l not in done:
        dom = urlparse(l).netloc
        ok, ko = count_dom.get(dom, (0, 0))
        if ok == 0 and ko > 50:
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
        # except savepagenow.api.WaybackRuntimeError as e:
        except Exception as e:
            if len(e.args) == 1 and isinstance(e.args[0], dict):
                r = e.args[0]
                txt = r.get("headers", {}).get("Link", None)
                if txt and r.get("status_code", None) == 200:
                    m = re.search(
                        "("+re.escape("https://web.archive.org/web") + r"/\d+/" + re.escape(l)+")", txt)
                    if m:
                        print(">", end=" ")
                        save(l, m.group(1))
                        continue
            txt = "%s %s\n" % (type(e).__name__, e)
            f_ko.write(l+" "+txt)
            print(txt)
            ko = ko + 1
        count_dom[dom] = (ok, ko)

f_ok.close()
f_ko.close()
