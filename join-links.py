#!/usr/bin/python3
import os
from urllib.parse import urlparse
from glob import glob
from socket import gethostbyname, gaierror
import re

re_file_ip = re.compile(r".*?/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\.txt$")
re_param = re.compile(r".+\?.+=(\d+)$")

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

def get_ip(dom):
    try:
        return gethostbyname(dom)
    except gaierror as e:
        print("%s %s" % (dom, e))
        return -1

def sort_links(l):
    l = l.replace("http://", "https://")
    m = re_param.match(l)
    if not m:
        m=-1
    else:
        m = m.group(1)
        l=l[:-len(m)]
        m = int(m)
    return (l, m)

ips={}
links=set()
for txt in glob("data/*.txt"):
    m = re_file_ip.match(txt)
    if m:
        IP = m.group(1)
        print(IP)
        for l in get_file(txt):
            dom = urlparse(l).netloc
            if dom not in ips:
                ips[dom] = get_ip(dom)
            if ips[dom] == IP:
                links.add(l)

links=sorted(links, key=sort_links)
with open(txt_links, "w") as f:
    f.write("\n".join(links))
