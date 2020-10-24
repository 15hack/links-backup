import json
from urllib.parse import urlparse
import ast

def reader(name):
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    yield l

def read_tuple(name, size=None):
    for l in reader(name):
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

def get_trunc_links(name):
    for l in reader(name):
        l = l.split()[0]
        yield trunc_link(l)

def get_dom(x):
    if not x.startswith("http"):
        x = "https://" + x
    return urlparse(x).netloc

def sort_dom(dom):
    k = reversed(dom.split("."))
    return tuple(k)

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
import re
from bunch import Bunch

import os
from urllib.request import urlretrieve
import random
from textwrap import dedent
import savepagenow

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
