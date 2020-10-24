#!/usr/bin/env python3

from core.webarchive import BulkWebArchive
import os
from random import shuffle
from shutil import move

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

loop = 1
try:
    loop = int(sys.argv[1])
except:
    pass

while loop!=0:
    loop = loop-1
    wa = BulkWebArchive("data", links="https://raw.githubusercontent.com/15hack/web-backup/master/out/links.txt")
    if len(wa.queue)==0:
        loop = 0
    else:
        print("\n=== INTENTO %s ===\n" % abs(loop+1))
        shuffle(wa.queue)
        wa.run()
    print("\n=== ESTADISTICAS.md ===\n")
    wa.log("ESTADISTICAS.md")
    move(wa.f.ko, "ko.txt")
