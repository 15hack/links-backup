import re
from bunch import Bunch

import os
from urllib.request import urlretrieve
import random
from textwrap import dedent
import savepagenow
from .writer import MDWriter
from urllib.parse import urlparse

def reader(name):
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    yield l

def trunc_link(l):
    slp = l.split("://", 1)
    if len(slp)==2 and slp[0].lower() in ("http", "https"):
        l = slp[1]
    return l

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

class WebArchive:
    def __init__(self, tryhard=False):
        self.tryhard = tryhard

    def _alt_link(self, link):
        spl = link.split("://", 1)
        if len(spl)!=2 or not spl[1]:
            return None
        pro, url = spl
        pro = pro.lower()
        if pro == "http":
            return "https://" + url
        if pro == "https":
            return "http://" + url
        return None

    def save(self, link, tryhard=None):
        if tryhard is None:
            tryhard = self.tryhard
        r = self._save(link)
        if r.ok<0 and tryhard:
            link = self._alt_link(link)
            if link:
                alt_r = self._save(link)
                if alt_r.ok>=0:
                    return alt_r
        return r


    def _save(self, l):
        try:
            archive_url, _ = savepagenow.capture_or_cache(l)
            return Bunch(
                url=l,
                archive_url=archive_url,
                ok=1
            )
        except savepagenow.api.CachedPage as e:
            _, archive_url = str(e).rsplit(None, 1)
            return Bunch(
                url=l,
                archive_url=archive_url,
                ok=0
            )
        # except savepagenow.api.WaybackRuntimeError as e:
        except Exception as e:
            status_code = None
            if len(e.args) == 1 and isinstance(e.args[0], dict):
                r = e.args[0]
                txt = r.get("headers", {}).get("Link", None)
                status_code = r.get("status_code", None)
                if txt:# and r.get("status_code", None) in (200, 206):
                    _re=re.compile("("+re.escape("https://web.archive.org/web/") + r"\d+/.*?"+re.escape(get_dom(l))+".*?)>;")
                    archive_url = _re.findall(txt)
                    if archive_url:
                        archive_url = sorted(archive_url)[-1]
                        return Bunch(
                            url=l,
                            archive_url=archive_url,
                            ok=0
                        )
            out = Bunch(
                url=l,
                archive_url=None,
                ok=-1,
                error=e,
                code=status_code
            )
            return out

class BulkWebArchive:
    def __init__(self, work_dir, *args, links=None, tryhard=False, **kargv):
        self.wa = WebArchive(tryhard=tryhard)
        os.makedirs(work_dir, exist_ok=True)
        work_dir = work_dir.rstrip("/")+"/"
        self.f=Bunch(
            links = work_dir+"links.txt",
            ok = work_dir+"ok.txt",
            ko = work_dir+"ko.txt",
        )
        if not os.path.isfile(self.f.links) and links:
            print(links, "->", self.f.links, end="\n\n")
            urlretrieve(links, self.f.links)
        self.reload()

    def reload(self):
        self.links = set(i for i in get_trunc_links(self.f.links) if get_dom(i))
        self.ok = set(i for i in get_trunc_links(self.f.ok) if i in self.links)
        self.ko = set(i for i in get_trunc_links(self.f.ko) if i in self.links and i not in self.ok)
        done = self.ok.union(self.ko)
        self.queue = set(l for l in reader(self.f.links) if trunc_link(l) not in done)
        for k in "links ok ko queue".split():
            a = getattr(self, k)
            a = sorted(a, key=lambda x: (sort_dom(get_dom(x)), trunc_link(x)))
            setattr(self, k, a)

    def write(self, file, line):
        with open(file, "a") as f:
            f.write(line+"\n")

    def run(self, tryhard=None):
        for count, l in renum(self.queue):
            print("%d %s" % (count, l))
            r = self.wa.save(l, tryhard=tryhard)
            if r.ok < 0:
                txt = "%s %s" % (type(r.error).__name__, r.error)
                print("-", txt, end="\n\n")
                self.write(self.f.ko, r.url+" "+txt)
            else:
                flag = "+"
                if r.ok == 0:
                    flag = "="
                print(flag, (r.archive_url or ""), end="\n\n")
                self.write(self.f.ok, r.url)

    def log(self, out):
        self.reload()

        links_ko = {}
        for l in reader(self.f.ko):
            l, e = l.split(None, 1)
            l = trunc_link(l)
            if l in self.links and l not in self.ok:
                links_ko[l] = e

        re_http = re.compile(r":\s*\bhttps?://\S+\s*:?\s*")
        re_http2 = re.compile(r":\s*\bht?t?p?s?:?/?/?$")
        re_date = re.compile(r",\s*'Date':\s*'.*?'")
        re_sp = re.compile(r"\s+")
        errores = {}
        for lnk, e in links_ko.items():
            dom = get_dom(lnk)
            e = re_http.sub(" ", e)
            e = re_http2.sub("", e)
            e = re_date.sub(" ", e)
            e = re_sp.sub(" ", e).strip()
            lst = errores.get(dom, None)
            errores[dom] = add(e, lst)

        count_total, count_ok = count_dom(self.links, self.ok)
        l_ok = len(self.ok)
        l_ko = len(self.ko)
        f = MDWriter(out)
        f.write(f,
            dedent(
                '''
                Enlaces totales: {total}

                **OK**: {ok} ({p_ok:.0f} %)
                **KO**: {ko} ({p_ko:.0f} %)
                '''
            ),
            total=total,
            ok=l_ok,
            ko=l_ko,
            p_ok=(l_ok*100/total),
            p_ko=(l_ko*100/total)
        )

        doms = sorted(set(get_dom(l) for l in self.links), key=sort_dom)
        level = []
        for dom in doms:
            while len(level) > 0 and not dom.endswith(level[-1]):
                level.pop()
            s_dom = dom if len(level) == 0 else dom[:-len(level[-1])-1]
            l = count_total[dom]
            l_ok = count_ok.get(dom, 0)
            l_level = len(level)
            f.write(("    " * l_level) +
                  "* [{0}](https://web.archive.org/web/*/https://{1}/*)", s_dom, dom, end="")
            if l_ok < l:
                v = l_ok*100/l
                por = "{0:.2f}" if (v > 0 and v < 1) or (
                    v > 99.5 and v < 100) else "{0:.0f}"
                por = por.format(v)
                f.write(" `{0} %`", por)
                err = errores.get(dom, None) or []
                l_level = l_level + 1
                for v in sorted(err):
                    f.write(("    " * l_level) + "* "+v)
            else:
                f.write("")
            level.append(dom)
        f.close()
