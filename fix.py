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
txt_links_dic = "../get-links/data/links_dict.txt"

def get_file(name, field=None, dict=True):
    lines = {} if dict else []
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    if dict:
                        k, v = l.split(None, 1)
                        lines[k]=v
                    elif field is not None:
                        l = l.split()
                        lines.append(l[field])
                    else:
                        lines.append(l)
    return lines


ok_list = get_file(web_archive, field=0)
ko_list = get_file(web_archive_error, dict=True)
dict_lk = get_file(txt_links_dic, dict=True)

visto = set()
with open("data/webarchive_ok.txt", "w") as f:
    for ok in ok_list:
        ok = dict_lk.get(ok, None)
        if ok and ok not in visto:
            visto.add(ok)
            f.write(ok+"\n")

with open("data/webarchive_ko.txt", "w") as f:
    for l, e in ko_list.items():
        l = dict_lk.get(l, None)
        if l:
            f.write("%s %s\n" % (l, e))
