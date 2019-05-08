#!/usr/bin/python3
import os
import sys
from urllib.parse import urlparse
import re

web_archive_ok = "data/webarchive_ok.txt"
web_archive_ko = "data/webarchive_ko.txt"
txt_links = "data/links.txt"

re_http = re.compile(r":\s*\bhttps?://\S+\s*:?\s*")
re_http2 = re.compile(r":\s*\bht?t?p?s?:?/?$")
re_date = re.compile(r",\s*'Date':\s*'.*?'")
re_sp = re.compile(r"\s+")

def get_file(name):
    lines = []
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    lines.append(l)
    return lines

last_line = ""
out = open("ESTADISTICAS.md", "w")
def write(s, *args, end="\n"):
    global last_line
    if len(args)>0:
        s = s.format(*args)
    if s.startswith("#"):
        if len(last_line)>0:
            s = "\n" + s
        s = s + "\n"
    last_line = s.split("\n")[-1]
    out.write(s+end)

def sort_dom(dom):
    k = reversed(dom.split("."))
    return tuple(k)

def count_dom(*args):
    r = []
    for ls in args:
        i = {}
        for l in ls:
            dom = urlparse(l).netloc
            i[dom] = i.get(dom, 0) + 1
        r.append(i)
    return tuple(r)

def add(s, lst):
    if lst is None:
        lst = []
    for i, v in enumerate(lst):
        if v == s or v.startswith(s):
            return lst
        if s.startswith(v):
            lst[i]=s
            return lst
    lst.append(s)
    return lst

links = set(get_file(txt_links))
links_ok = set(l for l in get_file(web_archive_ok) if l in links)
links_ko = {}
for l in get_file(web_archive_ko):
    l, e = l.split(None, 1)
    if l in links and l not in links_ok:
        links_ko[l]=e
l = len(links)
l_ok = len(links_ok)
l_ko = len(links_ko)

errores={}
for lnk, e in links_ko.items():
    dom = urlparse(lnk).netloc
    e = re_http.sub(" ", e)
    e = re_http2.sub("", e)
    e = re_date.sub(" ", e)
    e = re_sp.sub(" ", e).strip()
    lst = errores.get(dom, None)
    errores[dom]=add(e, lst)

count_total, count_ok = count_dom(links, links_ok)

write("Enlaces totales: {0}", l)
write("# [Web Archive](https://web.archive.org)")
write('''
* **OK**: {0} ({2:.0f} %)
* **KO**: {1} ({3:.0f} %)
''', l_ok, l_ko, (l_ok*100/l), (l_ko*100/l))

doms = set([urlparse(l).netloc for l in links])
level = []
for dom in sorted(doms, key=sort_dom):
    while len(level)>0 and not dom.endswith(level[-1]):
        level.pop()
    s_dom = dom if len(level)==0 else dom[:-len(level[-1])-1]
    l = count_total[dom]
    l_ok = count_ok.get(dom, 0)
    l_level = len(level)
    write(("    "* l_level) + "* [{0}](https://web.archive.org/web/*/https://{1}/*)", s_dom, dom, end="")
    if l_ok<l:
        v = l_ok*100/l
        por = "{0:.2f}" if (v > 0 and v < 1) or (v>99.5 and v<100) else "{0:.0f}"
        por = por.format(v)
        write(" `{0} %`", por)
        err = errores.get(dom, None) or []
        l_level = l_level + 1
        for v in sorted(err):
            write(("    "* l_level) + "* "+v)
    else:
        write("")
    level.append(dom)

out.close()
