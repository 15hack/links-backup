import os

web_archive_ok = "data/webarchive_ok.txt"
web_archive_ko = "data/webarchive_ko.txt"
txt_links = "data/links.txt"

def reader(name):
    if os.path.isfile(name):
        with open(name, "r") as f:
            for l in f.readlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    yield l


def get_links(name):
    for l in reader(name):
        l = l.split()[0]
        if l.startswith("http"):
            l = l.split("://", 1)[-1]
        yield l
