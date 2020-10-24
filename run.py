#!/usr/bin/env python3

from core.webarchive import BulkWebArchive
import os
from random import shuffle
from shutil import move
import sys

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

wa = BulkWebArchive("data", links="https://raw.githubusercontent.com/15hack/web-backup/master/out/links.txt")

loop = 1
if len(sys.argv)>1:
    loop = sys.argv[1]
    if loop == "check":
        wa.chek_ok()
        sys.exit()
    if loop == "reload":
        move(wa.f.ko, "ko.txt")
        wa.reload(hard_load=True)
        move("ko.txt", wa.f.ko)
        wa.reload()
        wa.log("ESTADISTICAS.md")
        sys.exit()
    loop = int(loop)

wa.reload(hard_load=True)
while loop!=0:
    loop = loop-1
    wa.reload()
    if len(wa.queue)==0:
        loop = 0
    else:
        print("\n=== INTENTO %s ===\n" % abs(loop+1))
        shuffle(wa.queue)
        wa.run()
    print("\n=== ESTADISTICAS.md ===\n")
    wa.log("ESTADISTICAS.md")
    if loop!=0:
        move(wa.f.ko, "ko.txt")
