"""Tests for the change watcher. No network. Run: python tests/test_watch.py"""
import json
import os
import shutil
import sys
import tempfile
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ledger import watch  # noqa: E402

PAGE = '<a href="/docs/framework-v1.pdf">v1</a><script src="/app.js?x=1"></script><div id="cookie-123"></div>'


def main():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "watch"))
    sources = [
        {"id": "p", "lab": "x", "name": "page", "kind": "page", "url": "https://ex.test/safety"},
        {"id": "f", "lab": "x", "name": "file", "kind": "file", "url": "https://ex.test/a.pdf"},
        {"id": "g", "lab": "x", "name": "gone", "kind": "file", "url": "https://ex.test/gone.pdf"},
    ]
    with open(os.path.join(root, "watch", "sources.json"), "w") as handle:
        json.dump({"sources": sources}, handle)
    world = {"https://ex.test/safety": PAGE.encode(), "https://ex.test/a.pdf": b"PDF-1"}

    def getter(url):
        if url not in world:
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        return world[url], ""

    def types():
        return [event["type"] for event in watch.run(root, getter)]

    assert types() == ["baseline", "baseline"], "run 1 records a first hash and makes no issue"
    assert types() == [], "run 2: nothing changed"
    world["https://ex.test/safety"] = PAGE.replace("cookie-123", "cookie-999").encode()
    assert types() == ["unreachable"], "run 3: page noise is not a change; the third failure is reported one time"
    world["https://ex.test/safety"] = (PAGE + '<a href="/docs/framework-v2.pdf">v2</a>').encode()
    world["https://ex.test/a.pdf"] = b"PDF-2!"
    events = watch.run(root, getter)
    assert [e["type"] for e in events] == ["changed", "changed"], "run 4: a new link and new bytes"
    assert events[0]["added"] == ["https://ex.test/docs/framework-v2.pdf"] and events[0]["removed"] == []
    assert (events[1]["old_bytes"], events[1]["new_bytes"]) == (5, 6)
    assert types() == [], "run 5: no second report"
    world["https://ex.test/gone.pdf"] = b"back"
    assert types() == ["baseline"], "run 6: an address that works again gets its first hash"
    title, body = watch.issue_text(events[0])
    assert title.startswith("Framework change detected") and "framework-v2.pdf" in body and "- none" in body
    with open(os.path.join(root, "watch", "issues.json")) as handle:
        assert json.load(handle) == []
    shutil.rmtree(root)
    print("ok   watcher: 6 runs, baseline, noise, change, failure, recovery")


if __name__ == "__main__":
    main()
