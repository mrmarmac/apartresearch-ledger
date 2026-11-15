#!/usr/bin/env python3
"""Commitment Ledger. One entry point.

  python run.py fetch      Download the upstream corpus (pinned commit) into cache/.
  python run.py build      Write data/ledger.json.
  python run.py validate   Check data/ledger.json and examples/ against schema.json.
  python run.py site       Write the static site and feed.xml into docs/.
  python run.py score      Score validation/predictions/ against the upstream codes. Write validation.md.
  python run.py align      Score the alignment test. Write validation/alignment/report.md.
  python run.py check      Check that the demo path works.
  python run.py stats      Print a count table.
  python run.py all        fetch, build, validate, stats.
"""
import collections
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache", "corpus")
LEDGER = os.path.join(ROOT, "data", "ledger.json")
DEMO_ID = "xai-governance-673f"  # xAI whistleblower protection

sys.path.insert(0, ROOT)
from ledger import config  # noqa: E402
from ledger.build import build  # noqa: E402
from ledger.corpus import Corpus  # noqa: E402


def fetch():
    if not os.path.isdir(os.path.join(CACHE, ".git")):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", config.CORPUS_REPO, CACHE], check=True)
    subprocess.run(["git", "-C", CACHE, "checkout", "--quiet", config.CORPUS_COMMIT], check=True)
    print(f"corpus ready at commit {config.CORPUS_COMMIT[:12]}")


def do_build():
    ledger = build(Corpus(CACHE))
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    demo = [c for c in ledger["commitments"] if c["id"] == DEMO_ID]
    used = {h["version_id"] for c in demo for h in c["history"]}
    example = dict(ledger, commitments=demo, versions=[v for v in ledger["versions"] if v["version_id"] in used])
    with open(os.path.join(ROOT, "examples", "whistleblower.json"), "w", encoding="utf-8") as handle:
        json.dump(example, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}: "
          f"{len(ledger['commitments'])} commitments, {len(ledger['versions'])} versions")


def site():
    from ledger.site import render
    with open(LEDGER, encoding="utf-8") as handle:
        ledger = json.load(handle)
    out = os.path.join(ROOT, "docs")
    os.makedirs(out, exist_ok=True)
    pages = render(ledger, ROOT, out)
    print(f"wrote docs/: index, {pages} commitment pages, feed.xml")


def validate():
    import jsonschema
    with open(os.path.join(ROOT, "schema.json"), encoding="utf-8") as handle:
        schema = json.load(handle)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    targets = [LEDGER] + sorted(
        os.path.join(ROOT, "examples", name)
        for name in os.listdir(os.path.join(ROOT, "examples")) if name.endswith(".json"))
    failed = False
    for path in targets:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            errors = list(validator.iter_errors(json.load(handle)))
        print(f"{'FAIL' if errors else 'ok  '} {os.path.relpath(path, ROOT)}")
        for error in errors[:10]:
            print("     ", "/".join(str(p) for p in error.path), "-", error.message[:160])
        failed = failed or bool(errors)
    if failed:
        sys.exit(1)


def stats():
    with open(LEDGER, encoding="utf-8") as handle:
        ledger = json.load(handle)
    labs = collections.defaultdict(lambda: collections.Counter())
    for item in ledger["commitments"]:
        row = labs[item["lab"]]
        row["commitments"] += 1
        row["current:" + item["current_status"]] += 1
        for event in item["history"]:
            row["event:" + event["status"]] += 1
            if event["quote"]:
                row["quotes"] += 1
                row["quotes_verified"] += bool(event["quote_verified"])
            if event["link"] in ("prior_id", "exact_text", "fuzzy_text"):
                row["link:" + event["link"]] += 1
    for lab, row in sorted(labs.items()):
        print(f"\n{lab}")
        for key in sorted(row):
            print(f"  {key:<28}{row[key]:>5}")


def score():
    from ledger.validation import score as run_score
    run_score(Corpus(CACHE), os.path.join(ROOT, "validation"), "Claude Opus 5.5 (sub-agent)")


def align():
    from ledger.alignment import report, run as run_align
    folder = os.path.join(ROOT, "validation", "alignment")
    rows = run_align(Corpus(CACHE), folder, "Claude Opus 5.5 (sub-agent)")
    with open(os.path.join(folder, "results.json"), "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=1, ensure_ascii=False)
    with open(os.path.join(folder, "report.md"), "w", encoding="utf-8") as handle:
        text = "\n".join(report(rows, "Claude Opus 5.5 (sub-agent)")).lstrip() + "\n"
        review = os.path.join(folder, "review.md")
        note = open(review, encoding="utf-8").read().rstrip() if os.path.exists(review) else ""
        handle.write(text.replace("__REVIEW__", note))
    done = [r for r in rows if r["answered"]]
    ok = lambda f: sum(r[f] in ("same", "both_none") for r in done)
    print(f"alignment: model {ok('model_class')}/{len(done)}, text matching {ok('text_class')}/{len(done)}; wrote validation/alignment/report.md")


def check():
    """The demo path must always work."""
    with open(LEDGER, encoding="utf-8") as handle:
        ledger = json.load(handle)
    demo = [c for c in ledger["commitments"] if c["id"] == DEMO_ID]
    assert len(demo) == 1, "the whistleblower commitment must keep its stable ID"
    history = demo[0]["history"]
    assert "whistleblower" in demo[0]["tags"]
    assert [h["version_id"] for h in history] == [
        "xai-draft-2025-02-10", "xai-draft-2025-02-20", "xai-2025-08-20", "xai-2025-12-30", "xai-2026-06-30"]
    assert [h["status"] for h in history] == ["baseline", "kept", "kept", "kept", "removed"]
    assert history[-1]["quote"] is None and history[-1]["disclosure"] == "no_account"
    assert all(len(h["sha256"]) == 64 for h in history)
    events = [h["event_id"] for c in ledger["commitments"] for h in c["history"]]
    assert len(events) == len(set(events)), "event IDs must be unique"
    print("ok   demo path: whistleblower commitment, 5 versions, last status removed")


COMMANDS = {"check": [check], "site": [site], "score": [score], "align": [align], "fetch": [fetch], "build": [do_build], "validate": [validate], "stats": [stats],
            "all": [fetch, do_build, validate, check, site, stats]}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if name not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    for step in COMMANDS[name]:
        step()
