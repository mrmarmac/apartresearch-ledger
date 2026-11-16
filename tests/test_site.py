"""Tests for the static site in docs/. No network. Run: python run.py site, then python tests/test_site.py"""
import collections
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOCS = os.path.join(ROOT, "docs")
CHANGE = {"added", "strengthened", "weakened", "removed", "relocated"}


def read(name):
    with open(os.path.join(DOCS, name), encoding="utf-8") as handle:
        return handle.read()


def test_pages_exist():
    ledger = json.load(open(os.path.join(ROOT, "data", "ledger.json"), encoding="utf-8"))
    for name in ("index.html", "browse.html", "revisions.html", "about.html", "feed.xml", "ledger.json", "schema.json",
                 "assets/site.css", "assets/site.js"):
        assert os.path.exists(os.path.join(DOCS, name)), name
    for c in ledger["commitments"]:
        assert os.path.exists(os.path.join(DOCS, "c", c["id"] + ".html")), c["id"]
        for old in c.get("former_ids", []):
            assert os.path.exists(os.path.join(DOCS, "c", old + ".html")), old
    for v in ledger["versions"]:
        assert os.path.exists(os.path.join(DOCS, "v", v["version_id"] + ".html")), v["version_id"]
    for lab in {v["lab"] for v in ledger["versions"]}:
        assert os.path.exists(os.path.join(DOCS, "d", lab + ".html")), lab


def test_strip_chart():
    """Each developer page has one strip row for each commitment and one linked bar for each history entry."""
    ledger = json.load(open(os.path.join(ROOT, "data", "ledger.json"), encoding="utf-8"))
    for lab in {c["lab"] for c in ledger["commitments"]}:
        mine = [c for c in ledger["commitments"] if c["lab"] == lab]
        page = read(f"d/{lab}.html")
        chart = page.split('<h2 id="strip">')[1].split('<h2 id="topics">')[0]
        assert chart.count('class="sc-row"') == len(mine), lab
        entries = sum(len(c["history"]) for c in mine)
        assert len(re.findall(r'href="\.\./c/[^"#]+\.html#[^"]+"', chart)) == entries, lab
        open_ends = sum(1 for c in mine if c["current_status"] in ("merged", "not_traced"))
        assert chart.count('<a class="b-not_traced"') + chart.count('<a class="b-merged"') <= open_ends, lab


def test_internal_links():
    """Every link to a page or a file of this site must have a target."""
    missing = []
    for folder, _, names in os.walk(DOCS):
        for name in names:
            if not name.endswith(".html"):
                continue
            path = os.path.join(folder, name)
            text = open(path, encoding="utf-8").read()
            ids = set(re.findall(r'\bid="([^"]+)"', text))
            for href in set(re.findall(r'(?:href|src)="([^"]+)"', text)):
                if re.match(r"^(https?:|mailto:|data:)", href):
                    continue
                target, _, fragment = href.partition("#")
                target = target.split("?")[0]
                if not target:
                    if fragment and fragment not in ids:
                        missing.append((os.path.relpath(path, DOCS), href))
                    continue
                full = os.path.normpath(os.path.join(folder, urllib.parse.unquote(target)))
                if not os.path.exists(full):
                    missing.append((os.path.relpath(path, DOCS), href))
                elif fragment and full.endswith(".html"):
                    if f'id="{fragment}"' not in open(full, encoding="utf-8").read():
                        missing.append((os.path.relpath(path, DOCS), href))
    assert not missing, missing[:10]


def test_numbers_match_the_ledger():
    ledger = json.load(open(os.path.join(ROOT, "data", "ledger.json"), encoding="utf-8"))
    items = ledger["commitments"]
    home = read("index.html")
    changes = sum(1 for c in items for h in c["history"] if h["status"] in CHANGE)
    for number, label in ((len(items), "commitments with a permanent ID"), (len(ledger["versions"]), "framework versions"),
                          (changes, "recorded changes")):
        assert re.search(rf"<b>{number}</b><span>{label}", home), (number, label)
    browse = read("browse.html")
    assert browse.count("<li data-lab=") == len(items)
    for v in ledger["versions"]:
        page = read(os.path.join("v", v["version_id"] + ".html"))
        counts = collections.Counter(h["status"] for c in items for h in c["history"] if h["version_id"] == v["version_id"])
        for status in CHANGE:
            assert page.count(f'<article class="chg is-{status}">') == counts.get(status, 0), (v["version_id"], status)
        assert v["sha256"] in page
    for c in items:
        page = read(os.path.join("c", c["id"] + ".html"))
        assert page.count('<div class="entry">') == len(c["history"]), c["id"]
        for h in c["history"]:
            assert h["sha256"] in page and f'id="{h["version_id"]}"' in page, h["event_id"]


def test_old_links_still_work():
    """Before the redesign, filters were on index.html. The home page sends those links to browse.html."""
    assert "location.replace('browse.html'+location.search)" in read("index.html")
    for key in ("f-q", "f-lab", "f-current", "f-event", "f-topic", "f-sort"):
        assert f'id="{key}"' in read("browse.html"), key


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok  ", name)
