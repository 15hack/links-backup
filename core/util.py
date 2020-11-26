import json
from urllib.parse import urlparse
import ast
import os

def reader(*files):
    for file in files:
        if os.path.isfile(file):
            with open(file, "r") as f:
                for l in f.readlines():
                    l = l.strip()
                    if l and not l.startswith("#"):
                        yield l

def read_tuple(*files, size=None):
    for l in reader(*files):
        if size is None:
            yield l.split()
        else:
            l = l.split(None, size-1)
            if len(l)==size:
                yield l

def trunc_link(l):
    slp = l.split("://", 1)
    if len(slp)==2 and slp[0].lower() in ("http", "https"):
        l = slp[1]
    return l.rstrip("/")

def get_trunc_links(*files):
    for l in reader(*files):
        l = l.split()[0]
        yield trunc_link(l)

def get_dom(x):
    if not x.startswith("http"):
        x = "https://" + x
    return urlparse(x).netloc

def keydom(dom):
    k = reversed(dom.split("."))
    return tuple(k)

def keylink(l):
    arr=[
        keydom(get_dom(l)),
        trunc_link(l),
        l
    ]
    return tuple(arr)

def count_dom(*args):
    r = []
    for ls in args:
        i = {}
        for l in ls:
            dom = get_dom(l)
            if dom:
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
            lst[i] = s
            return lst
    lst.append(s)
    return lst

def renum(arr):
    count = len(arr)
    for i in arr:
        count = count - 1
        yield count, i

def safe_json(s, intento=0):
    try:
        return json.loads(s)
    except json.decoder.JSONDecodeError:
        if intento == 0:
            scp = '_-_-_' * 100
            s = s.replace("'", scp)
            s = s.replace('"', "'")
            s = s.replace(scp, '"')
            return safe_json(s, intento=intento+1)
    if intento == 1:
        try:
            js = ast.literal_eval(s)
            return js
        except:
            pass
    return None
