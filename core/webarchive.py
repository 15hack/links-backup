import re
from bunch import Bunch

import requests
import os
from urllib.request import urlretrieve
from textwrap import dedent
import savepagenow
from .writer import MDWriter
from .util import *

re_http = re.compile(r":\s*\bhttps?://\S+\s*:?\s*")
re_http2 = re.compile(r":\s*\bht?t?p?s?:?/?/?$")
re_date = re.compile(r",\s*'Date':\s*'.*?'")
re_sp = re.compile(r"\s+")

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

    def get_visited(self, *doms):
        status = {}
        for dom in doms:
            url = "".join([
                "http://web.archive.org/cdx/search/cdx?url=",
                dom,
                "/*&output=json&fl=original,statuscode"
            ])
            try:
                r = requests.get(url)
                r = r.json()
            except:
                print(url)
                continue
            for url, code in r[1:]:
                if code == "-":
                    code = -1
                elif code == "":
                    code = -2
                elif isinstance(code, str) and code.isdigit():
                    code = int(code)
                if code not in status:
                    status[code]=set()
                status[code].add(url)
        return status

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

    def parse_error(self, e):
        js = None
        if isinstance(e, dict):
            js = e
        elif isinstance(e, Exception):
            if len(e.args) == 1 and isinstance(e.args[0], dict):
                js = e.args[0]
            e = "%s %s" % (type(e).__name__, e)
        if js is None and isinstance(e, str):
            pr = str(e).strip()
            if not pr.startswith("{") and " " in pr:
                pr = pr.split(None, 1)[1]
            js = safe_json(pr)
        if js and "status_code" in js:
            return js["status_code"]
        if js and "X-ts" in js and js['X-ts'] and js['X-ts'].isdigit():
            return int(js['X-ts'])
        if isinstance(e, str) and " " in e.strip():
            name, desc = e.strip().split(None, 1)
            if name == "ConnectionError" and "Max retries exceeded" in desc:
                return "ConnectionError Max retries exceeded"
            if name == "WaybackRuntimeError":
                if "LiveDocumentNotAvailableException" in desc and ": Status 500" in desc:
                    return 500
        if isinstance(e, str):
            e = re_http.sub(" ", e)
            e = re_http2.sub("", e)
            e = re_date.sub(" ", e)
            e = re_sp.sub(" ", e).strip()

            if " " in e.strip():
                name, desc = e.strip().split(None, 1)
                if desc.startswith("LiveDocumentNotAvailableException"):
                    desc = desc.replace("org.archive.wayback.exception.LiveDocumentNotAvailableException", "")
                    k = "live document unavailable:"
                    desc = desc.replace(k, "").strip()
                    desc = re_sp.sub(" ", desc).strip()
                    for k in ("live document unavailable", "org.archive.wayback.exception."):
                        while len(k)>0:
                            if desc.endswith(" "+k):
                                desc = desc[:-len(k)].rstrip()
                                break
                            k = k[:-1]
                e = name+" "+desc
                e = re_sp.sub(" ", e).strip()
        return e


class BulkWebArchive:
    def __init__(self, work_dir, *args, ignore=None, links=None, tryhard=False, **kargv):
        self.wa = WebArchive(tryhard=tryhard)
        if ignore is None:
            ignore = tuple()
        elif isinstance(ignore, str):
            ignore = (ignore, )
        self.ignore = ignore
        os.makedirs(work_dir, exist_ok=True)
        work_dir = work_dir.rstrip("/")+"/"
        self.f=Bunch(
            links = work_dir+"links.txt",
            ok = work_dir+"ok.txt",
            ko = work_dir+"ko.txt",
            hard_ko = work_dir+"hard_ko.txt",
            falta = work_dir+"falta.txt",
        )
        if not os.path.isfile(self.f.links) and links:
            print(links, "->", self.f.links, end="\n\n")
            urlretrieve(links, self.f.links)
        self.reload()

    def chek_ok(self):
        ok = set(reader(self.f.ok))
        ok = sorted(ok, key=keylink)
        st = self.wa.get_visited(*set(get_dom(x) for x in ok))
        for k, v in list(st.items()):
            st[k]=set(trunc_link(i) for i in v)
        ks = tuple(sorted((k for k in st.keys() if k!=200), key=lambda x:str(x)))
        dn = st.get(200, [])
        fail = []
        for i in ok:
            _i = trunc_link(i)
            if _i not in dn:
                cds = []
                for k in ks:
                    if _i in st[k]:
                        cds.append(k)
                print(*cds, end=" ")
                print(i)

    def reload(self, hard_load=False):
        self.links = set(i for i in get_trunc_links(self.f.links) if get_dom(i))
        self.ok = set()
        self.ok = set(i for i in get_trunc_links(self.f.ok) if i in self.links)
        if hard_load:
            self.ko = set()
        else:
            self.ko = set(i for i in get_trunc_links(self.f.ko, self.f.hard_ko) if i in self.links and i not in self.ok)
        done = self.ok.union(self.ko)
        self.queue = set(l for l in reader(self.f.links) if trunc_link(l) not in done)
        for k in "links ok ko queue".split():
            a = getattr(self, k)
            a = sorted(a, key=keylink)
            setattr(self, k, a)
        if hard_load:
            queue = set(trunc_link(l) for l in self.queue)
            queue = queue.union(self.ko)
            doms = set(get_dom(x) for x in queue)
            doms = (d for d in doms if d not in self.ignore)
            done = self.wa.get_visited(*doms)
            done = done.get(200, [])
            for url in done:
                p = trunc_link(url)
                if p in queue:
                    self.write(self.f.ok, url)
            ok = set(reader(self.f.ok))
            ok = sorted(ok, key=keylink)
            with open(self.f.ok, "w") as f:
                for l in ok:
                    f.write(l+"\n")
            self.reload()
        with open(self.f.falta, "w") as f:
            f.write("# FALTA\n")
            for l in sorted(self.queue):
                f.write(l+"\n")
            f.write("\n# KO\n")
            for l in sorted(l for l in reader(self.f.links) if trunc_link(l) in self.ko):
                f.write(l+"\n")
        self.queue = [l for l in self.queue if get_dom(l) not in self.ignore]

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

        errores = {}
        status_codes={}
        for lnk, e in read_tuple(self.f.ko, self.f.hard_ko, size=2):
            lnk = trunc_link(lnk)
            e = self.wa.parse_error(e)
            if lnk in self.ko and e is not None:
                dom = get_dom(lnk)
                lst = errores.get(dom, None)
                if isinstance(e, int):
                    if dom not in status_codes:
                        status_codes[dom]=set()
                    status_codes[dom].add(e)
                else:
                    errores[dom] = add(e, lst)
        for dom, st in status_codes.items():
            lst = errores.get(dom, None)
            e = "Fail HTTP status_code: %s" % ", ".join(str(i) for i in sorted(st))
            errores[dom] = add(e, lst)

        count_total, count_ok = count_dom(self.links, self.ok)
        l_ok = len(self.ok)
        l_ko = len(self.ko)
        total = len(self.links)
        f = MDWriter(out)
        f.write(
            dedent(
                '''
                Enlaces totales: {total}

                * **OK**: {ok} ({p_ok:.0f} %)
                * **KO**: {ko} ({p_ko:.0f} %)
                * Falta: {falta}
                '''
            ),
            total=total,
            ok=l_ok,
            ko=l_ko,
            p_ok=(l_ok*100/total),
            p_ko=(l_ko*100/total),
            falta=(total-l_ok-l_ko)
        )

        doms = sorted(set(get_dom(l) for l in self.links), key=keydom)
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
        f.write(dedent('''
            **OJO**: cuando un código 2XX es contabilizado como error
            no se debe a un falso positivo si no a que aunque la
            petición devolvió un código 2XX no se pudo verificar que la
            url fuera guardada con éxito.
        '''))
        f.close()
