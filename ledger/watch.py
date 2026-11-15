"""Change watcher.

Reads watch/sources.json, gets each address, and compares a SHA-256 with
watch/state.json. It reports what is different. It does not say what the
change means: a person must look.

kind "file": the hash of the bytes.
kind "page": the hash of the sorted list of document links on the page.

Standard library only.
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "commitment-ledger-watcher/0.1 (+https://github.com/mrmarmac/apartresearch-ledger)"
DOC_LINK = re.compile(r"""(?:href|src)\s*=\s*["']([^"'#]+)["']""", re.I)
DOC_HINT = re.compile(r"\.pdf(\?|$)|/files/|static-resource|/static/|framework|scaling-policy|preparedness", re.I)
FAILS_BEFORE_REPORT = 3


def fetch(url, timeout=60):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def document_links(html, base):
    """Links on a page that look like a policy document. Query strings stay; fragments go."""
    found = set()
    for raw in DOC_LINK.findall(html):
        if DOC_HINT.search(raw):
            found.add(urllib.parse.urljoin(base, raw.strip()))
    return sorted(found)


def fingerprint(source, body):
    if source["kind"] == "page":
        links = document_links(body.decode("utf-8", errors="replace"), source["url"])
        digest = hashlib.sha256("\n".join(links).encode()).hexdigest()
        return digest, {"links": links}
    return hashlib.sha256(body).hexdigest(), {"bytes": len(body)}


def check(sources, state, getter=fetch):
    """Return (new_state, events). An event is a dict with a 'type'."""
    events = []
    new_state = {}
    for source in sources:
        sid = source["id"]
        old = state.get(sid, {})
        entry = dict(old)
        entry["url"] = source["url"]
        try:
            body, _ = getter(source["url"])
            digest, detail = fingerprint(source, body)
        except Exception as error:  # network errors and HTTP errors
            code = getattr(error, "code", None)
            entry["fails"] = old.get("fails", 0) + 1
            entry["last_error"] = f"HTTP {code}" if code else type(error).__name__
            if entry["fails"] == FAILS_BEFORE_REPORT:
                events.append({"type": "unreachable", "source": source, "error": entry["last_error"]})
            new_state[sid] = entry
            continue
        entry["fails"] = 0
        entry.pop("last_error", None)
        if "sha256" not in old:
            events.append({"type": "baseline", "source": source, "sha256": digest})
        elif old["sha256"] != digest:
            event = {"type": "changed", "source": source, "old": old["sha256"], "new": digest}
            if source["kind"] == "page":
                before, after = set(old.get("links", [])), set(detail["links"])
                event["added"], event["removed"] = sorted(after - before), sorted(before - after)
            else:
                event["old_bytes"], event["new_bytes"] = old.get("bytes"), detail["bytes"]
            events.append(event)
        entry["sha256"] = digest
        entry.update(detail)
        new_state[sid] = entry
    return new_state, events


def issue_text(event):
    """(title, body) of the GitHub issue for one event."""
    source = event["source"]
    if event["type"] == "unreachable":
        title = f"Watcher cannot get: {source['lab']}, {source['name']}"
        body = (f"The watcher could not get this address {FAILS_BEFORE_REPORT} times in sequence.\n\n"
                f"- Address: {source['url']}\n- Last error: {event['error']}\n\n"
                "Possible causes: the document moved, or the site blocks automated requests. "
                "Open the address in a browser. If the document moved, update `watch/sources.json`.")
        return title, body
    title = f"Framework change detected: {source['lab']}, {source['name']}"
    lines = [f"The watcher found a difference at a watched address.", "",
             f"- Address: {source['url']}", f"- SHA-256 before: `{event['old']}`", f"- SHA-256 now: `{event['new']}`"]
    if source["kind"] == "page":
        lines += ["", "Document links that are new on the page:", ""] + ([f"- {u}" for u in event["added"]] or ["- none"])
        lines += ["", "Document links that are gone from the page:", ""] + ([f"- {u}" for u in event["removed"]] or ["- none"])
    else:
        lines += [f"- Size before: {event['old_bytes']} bytes", f"- Size now: {event['new_bytes']} bytes"]
    lines += ["", "**The watcher does not know what the change means.** A re-upload with the same words also changes the hash.",
              "", "To do:", "", "- [ ] Download the document and keep the file.",
              "- [ ] Compare it with the last version in the ledger.",
              "- [ ] If the words changed: trace the new version and add it to the ledger.",
              "- [ ] If a new version has a new address: update `watch/sources.json`."]
    return title, "\n".join(lines)


def run(root, getter=fetch):
    folder = os.path.join(root, "watch")
    with open(os.path.join(folder, "sources.json"), encoding="utf-8") as handle:
        sources = json.load(handle)["sources"]
    path = os.path.join(folder, "state.json")
    state = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
    new_state, events = check(sources, state, getter)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(new_state, handle, indent=1, sort_keys=True)
        handle.write("\n")
    issues = [dict(zip(("title", "body"), issue_text(e))) for e in events if e["type"] in ("changed", "unreachable")]
    with open(os.path.join(folder, "issues.json"), "w", encoding="utf-8") as handle:
        json.dump(issues, handle, indent=1)
    for source in sources:
        entry = new_state[source["id"]]
        mark = {"baseline": "first record", "changed": "CHANGED", "unreachable": "cannot get"}
        kind = next((mark[e["type"]] for e in events if e["source"]["id"] == source["id"]), None)
        if kind is None:
            kind = f"error ({entry['last_error']}, {entry['fails']})" if entry.get("fails") else "no change"
        print(f"{kind:<22} {source['id']:<24} {entry.get('sha256', '')[:12]}")
    return events
