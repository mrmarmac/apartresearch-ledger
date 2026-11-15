"""Tests for the ledger data and the text rules. No network. Run: python tests/test_ledger.py"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from ledger.textnorm import clean, quote_in_text, squash  # noqa: E402

CHANGE = {"added", "strengthened", "weakened", "removed", "relocated"}


def test_text_rules():
    assert squash("The Model-Weights, 2026!") == "themodelweights2026"
    assert clean("a" + chr(0x200b) + "b" + chr(0x202c) + chr(0x202d) + "c") == "ab c"
    source = squash("We will publish a report. It names each evaluation that we did.")
    assert quote_in_text("We will publish a report", source)
    assert quote_in_text("We will publish ... each evaluation", source)
    assert not quote_in_text("each evaluation ... We will publish", source), "fragments must be in sequence"
    assert not quote_in_text("We will not publish", source)


def test_ledger():
    import jsonschema
    ledger = json.load(open(os.path.join(ROOT, "data", "ledger.json"), encoding="utf-8"))
    jsonschema.validate(ledger, json.load(open(os.path.join(ROOT, "schema.json"), encoding="utf-8")))
    versions = {v["version_id"]: v for v in ledger["versions"]}
    order = {vid: n for n, vid in enumerate(versions)}
    ids, former, events = set(), set(), set()
    for item in ledger["commitments"]:
        assert re.fullmatch(r"[a-z]+-[a-z-]+-[0-9a-f]{4,}", item["id"]), item["id"]
        assert item["id"] not in ids, "commitment IDs must be unique"
        ids.add(item["id"])
        former.update(item["former_ids"])
        history = item["history"]
        assert history[0]["status"] in ("baseline", "added"), item["id"]
        assert history[0]["version_id"] == item["first_version_id"]
        assert history[-1]["version_id"] == item["last_version_id"]
        steps = [order[h["version_id"]] for h in history]
        assert steps == sorted(steps) and len(set(steps)) == len(steps), "history must be oldest first: " + item["id"]
        for entry in history:
            assert entry["event_id"] == f"{item['id']}@{entry['version_id']}"
            assert entry["event_id"] not in events
            events.add(entry["event_id"])
            assert versions[entry["version_id"]]["lab"] == item["lab"]
            assert entry["sha256"] == versions[entry["version_id"]]["sha256"]
            if entry["status"] == "removed":
                assert entry["quote"] is None, entry["event_id"]
            if entry["status"] in ("baseline", "added", "kept", "strengthened"):
                assert entry["quote"], entry["event_id"]  # upstream codes some "weakened" rows with no quote
            if entry["coded_by"] == "text_match":
                assert entry["status"] == "kept", "a text match makes no judgement: " + entry["event_id"]
        if item["current_status"] == "removed":
            assert history[-1]["status"] == "removed"
        if item["merged_into"]:
            assert item["merged_into"] in {c["id"] for c in ledger["commitments"]}
    assert not former & ids, "a former ID is never used again"
    return ledger, events


def test_feed(ledger):
    feed = ET.parse(os.path.join(ROOT, "docs", "feed.xml")).getroot()
    guids = [g.text for g in feed.iter("guid")]
    assert len(guids) == len(set(guids)), "feed GUIDs must be unique"
    expected = {h["event_id"] for c in ledger["commitments"] for h in c["history"] if h["status"] in CHANGE}
    assert set(guids) == expected, "the feed has one item for each change, and no other item"


def test_links_report():
    from ledger import links
    import tempfile
    import urllib.error
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "data")), os.makedirs(os.path.join(root, "validation"))
    import hashlib
    good = hashlib.sha256(b"A").hexdigest()
    versions = [{"version_id": "x-1", "source_url": "u1", "sha256": good},
                {"version_id": "x-2", "source_url": "u2", "sha256": good},
                {"version_id": "x-3", "source_url": "u3", "sha256": good}]
    json.dump({"versions": versions}, open(os.path.join(root, "data", "ledger.json"), "w"))

    def getter(url):
        if url == "u3":
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        return (b"A" if url == "u1" else b"B"), ""
    rows = links.check(root, getter)
    assert [r[2].split()[0] for r in rows] == ["same", "DIFFERENT", "HTTP"]
    assert links.report(root, rows)[1] == 1


if __name__ == "__main__":
    test_text_rules()
    ledger, events = test_ledger()
    test_feed(ledger)
    test_links_report()
    print(f"ok   ledger tests: {len(ledger['commitments'])} commitments, {len(events)} entries")
