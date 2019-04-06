#!/usr/bin/python3
import savepagenow
import json
import os

web_archive = "data/webarchive.txt"

def get_file(name):
    lines = []
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    lines.append(l)
    return lines

done=[]
for l in get_file(web_archive):
    done.append(l.split()[0])

f = open(web_archive,"w+")
for l in get_file("data/links.txt"):
    if l not in done:
        print(l)
        try:
            archive_url = savepagenow.capture(l)
            f.write("%s %s\n" % (l, archive_url))
            print(archive_url)
            print("")
        except Exception as e:
            print(e)
            print("")
            f.flush()
            continue
            f.close()
            raise
f.close()
