"""Link check. Gets the source address of each framework version and compares the SHA-256
with the hash in the ledger. Writes validation/links.md. Standard library only.

Run it where the network is open (the GitHub Action does this): python run.py links
"""
import datetime
import hashlib
import json
import os
import urllib.error

from .watch import fetch


def check(root, getter=fetch):
    with open(os.path.join(root, "data", "ledger.json"), encoding="utf-8") as handle:
        ledger = json.load(handle)
    rows = []
    for version in ledger["versions"]:
        url = version["source_url"]
        known = {version["sha256"]} | {r["sha256"] for r in version.get("reuploads", [])}
        try:
            body, _ = getter(url)
            digest = hashlib.sha256(body).hexdigest()
            result = "same file" if digest in known else "DIFFERENT FILE " + digest[:12]
        except urllib.error.HTTPError as error:
            result = f"HTTP {error.code}"
        except Exception as error:  # timeout, DNS, TLS
            result = "no answer: " + type(error).__name__
        rows.append((version["version_id"], url, result))
    return rows


def report(root, rows):
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ok = sum(1 for r in rows if r[2] == "same file")
    lines = ["# Link check", "",
             f"Checked: {today}. The check gets each source address and compares the SHA-256 with the ledger.", "",
             f"**Result: {ok} of {len(rows)} addresses give the same file.**", "",
             "| Version | Result | Address |", "|---|---|---|"]
    lines += [f"| `{v}` | {r} | <{u}> |" for v, u, r in rows]
    lines += ["", "- `same file`: the address works, and the bytes have the hash that the ledger records.",
              "- `DIFFERENT FILE`: the address works, but the bytes are different. A person must look.",
              "- `HTTP 403` or `no answer`: the site refused the check. Open the address in a browser.", ""]
    path = os.path.join(root, "validation", "links.md")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path, ok
