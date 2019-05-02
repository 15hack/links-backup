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
txt_links_dict = "data/links_dict.txt"

def get_file(name, field=None, dict=False):
    lines = {} if dict else []
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    if dict:
                        k, v = l.split()
                        lines[k]=v
                    elif field is not None:
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

def isRoot(p):
    return not(p.path or p.params or p.query or p.fragment)

ok_list = get_file(web_archive, field=0)
ko_list = get_file(web_archive_error, field=0)

done = set(ok_list+ko_list)
ban_dom=set()

links = get_file(txt_links)
links_dict = get_file(txt_links_dict, dict=True)
if not links_dict:
    with open(txt_links_dict, "w") as f:
        for l in links:
            l_parse = urlparse(l)
            dom = l_parse.netloc
            if dom in ban_dom:
                continue
            n = parse_url(l)
            if not n:
                continue
            n_parse = urlparse(n)
            if dom!=n_parse.netloc:
                ban_dom.add(dom)
                continue
            if not isRoot(l_parse) and isRoot(n_parse):
                continue
            links_dict[l]=n
            f.write(l+" "+n+"\n")


links = [l for l in links_dict.keys() if l not in done]

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


for l in links:
    total = total - 1
    if l not in done:
        dom = urlparse(l).netloc
        ok, ko = count_dom.get(dom, (0, 0))
        if ok==0 and ko>10:
            continue
        _l = links_dict[l]
        if _l in done:
            continue
        print("%d %s" % (total, _l))
        try:
            archive_url = savepagenow.capture(_l)
            save(l, _l, archive_url)
            ok = ok + 1
        except savepagenow.api.CachedPage as e:
            _, archive_url = str(e).rsplit(None, 1)
            print(">", end=" ")
            save(l, _l, archive_url)
        except Exception as e:
            txt = "%s %s\n" % (type(e).__name__, e)
            f_error.write(l+" "+txt)
            print(txt)
            ko = ko + 1
        count_dom[dom]=(ok, ko)

f.close()
f_error.close()
