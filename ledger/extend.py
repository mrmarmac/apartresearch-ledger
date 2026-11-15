"""Extend Anthropic chains through version pairs that the upstream corpus does not trace.

Pairs: v2.0 -> v2.1 -> v2.2 and v3.0 -> v3.1 -> v3.2 -> v3.3 -> v3.4.
These are small revisions. v2.2 -> v3.0 is a rewrite, and stays upstream-coded.

Method, in this sequence:
1. Text: if the verbatim quote is in the next version, the commitment is kept.
2. Model: if not, two independent model runs find the counterpart (or none).
3. Model: two independent model runs code the direction of each changed pair.
An entry where the two runs do not agree gets needs_review = true.

Not done here: commitments that are new in the later version (status added).
"""
import json
import os

from .alignment import same_passage
from .textnorm import clean, quote_in_text, squash

PROVIDER = "Anthropic"
LAB = "anthropic"
FAMILIES = {"A": ["v2.0", "v2.1", "v2.2"], "B": ["v3.0", "v3.1", "v3.2", "v3.3", "v3.4"]}
EXTENDED_PAIRS = [["anthropic-v2.0", "anthropic-v2.1"], ["anthropic-v2.1", "anthropic-v2.2"],
                  ["anthropic-v3.0", "anthropic-v3.1"], ["anthropic-v3.1", "anthropic-v3.2"],
                  ["anthropic-v3.2", "anthropic-v3.3"], ["anthropic-v3.3", "anthropic-v3.4"]]


def vid(label):
    return f"{LAB}-{label}"


def _docs(corpus):
    return {label: squash(corpus.text(PROVIDER, label)) for labels in FAMILIES.values() for label in labels}


def _family_members(ledger, family):
    start = vid(FAMILIES[family][0])
    out = []
    for item in ledger["commitments"]:
        if item["lab"] != LAB:
            continue
        last = item["history"][-1]
        if last["version_id"] == start and last["quote"] and last["status"] not in ("removed", "relocated"):
            out.append(item)
    return out


def _load(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _answers(folder, kind):
    """{(commitment_id, version_label): [run1 answer, run2 answer]} for kind 'trace' or 'code'."""
    out = {}
    for run in (1, 2):
        for family in FAMILIES:
            data = _load(folder, f"{kind}_{family}_run{run}.json")
            if kind == "code":
                data = _load(folder, f"code_run{run}.json") if family == "A" else None
            for row in data or []:
                if kind == "trace":
                    for step in row["steps"]:
                        out.setdefault((row["id"], step["version"]), [None, None])[run - 1] = step
                else:
                    out.setdefault((row["id"], row["version"]), [None, None])[run - 1] = row
    return out


def _none(step):
    return step is None or str(step.get("counterpart", "")).strip().upper() in ("", "NONE")


def walk(item, family, docs, trace, code):
    """Yield new history facts for one commitment: (label, fact dict)."""
    labels = FAMILIES[family]
    quote = item["history"][-1]["quote"]
    for label in labels[1:]:
        if quote_in_text(quote, docs[label]):
            yield label, {"status": "kept", "quote": clean(quote), "coded_by": "text_match", "link": "exact_text", "needs_review": False}
            continue
        runs = trace.get((item["id"], label))
        if not runs or runs[0] is None:
            return  # no model answer yet: the chain stops here
        first, second = runs
        if _none(first):
            agree = second is not None and _none(second)
            yield label, {"status": "removed", "quote": None, "coded_by": "model", "link": "model",
                          "needs_review": not agree, "rationale": clean(first.get("reason", "")) or None,
                          "previous_quote": quote}
            return
        found = clean(first["counterpart"])
        agree = second is not None and not _none(second) and same_passage(found, second["counterpart"])
        if squash(found) == squash(quote):
            yield label, {"status": "kept", "quote": found, "coded_by": "text_match", "link": "exact_text", "needs_review": False}
            quote = found
            continue
        codes = code.get((item["id"], label)) or [None, None]
        fact = {"quote": found, "coded_by": "model", "link": "model", "previous_quote": quote,
                "section": clean(first.get("later_section", "")) or None,
                "verified": quote_in_text(found, docs[label])}
        if codes[0] is None:
            fact.update(status=None, needs_review=True)
        else:
            status = {"R": "kept", "S": "strengthened", "W": "weakened"}[codes[0]["outcome"]]
            same_code = codes[1] is not None and codes[1]["outcome"] == codes[0]["outcome"]
            fact.update(status=status, needs_review=not (agree and same_code),
                        rationale=clean(codes[0].get("reason", "")) or None)
        yield label, fact
        quote = found


def plan(ledger, corpus, folder):
    """Return the trace items and the coding items that still need model answers."""
    docs = _docs(corpus)
    trace, code = _answers(folder, "trace"), _answers(folder, "code")
    trace_items = {family: [] for family in FAMILIES}
    code_items = []
    for family, labels in FAMILIES.items():
        for item in _family_members(ledger, family):
            last_label, last_quote = labels[0], item["history"][-1]["quote"]
            stopped = False
            for label, fact in walk(item, family, docs, trace, code):
                if fact["status"] is None:
                    code_items.append({"id": item["id"], "version": label, "developer": PROVIDER,
                                       "earlier_section": "", "earlier_text": fact["previous_quote"],
                                       "later_section": fact.get("section") or "", "later_text": fact["quote"]})
                if fact["status"] == "removed":
                    stopped = True
                if fact["quote"]:
                    last_label, last_quote = label, fact["quote"]
            reached = last_label == labels[-1] or stopped
            if not reached and (item["id"], labels[labels.index(last_label) + 1]) not in trace:
                trace_items[family].append({
                    "id": item["id"], "from_version": last_label, "earlier_text": last_quote,
                    "later_versions": labels[labels.index(last_label) + 1:]})
    return trace_items, code_items


def _entry(versions, label, fact):
    version = versions[vid(label)]
    status = fact["status"]
    return {
        "event_id": None, "version_id": vid(label), "status": status,
        "quote": fact["quote"], "section": fact.get("section"), "section_changed": False,
        "mixed": False, "material": status in ("strengthened", "weakened", "removed"),
        "disclosure": None, "confidence": None, "rationale": fact.get("rationale"),
        "link": fact["link"], "gap_before": False,
        "quote_verified": fact.get("verified", True) if fact["quote"] else None,
        "source_row": None, "source_url": version["source_url"],
        "wayback_timestamp": version["wayback_timestamp"], "sha256": version["sha256"],
        "coded_by": fact["coded_by"], "needs_review": bool(fact.get("needs_review")), "human_check": None,
    }


def apply(ledger, corpus, folder, tags_for):
    """Add the extension entries to the ledger. Returns a dict of counts."""
    import collections
    stats = collections.Counter()
    for item in ledger["commitments"]:
        item.setdefault("former_ids", [])
        item.setdefault("related_ids", [])
        for entry in item["history"]:
            entry.setdefault("coded_by", "upstream")
            entry.setdefault("needs_review", False)
            entry.setdefault("human_check", None)
    # Apply nothing until the tracing answers and the coding answers are both in the folder.
    if not os.path.isdir(folder) or _load(folder, "trace_A_run1.json") is None or _load(folder, "code_run1.json") is None:
        return stats
    docs = _docs(corpus)
    trace, code = _answers(folder, "trace"), _answers(folder, "code")
    versions = {v["version_id"]: v for v in ledger["versions"]}
    kept = {"status": "kept", "coded_by": "text_match", "link": "exact_text", "needs_review": False}

    # 1. Chains that upstream text already connects from v2.0 to v3.0: fill v2.1 and v2.2.
    for item in ledger["commitments"]:
        if item["lab"] != LAB:
            continue
        hist = item["history"]
        for i in range(1, len(hist)):
            if hist[i - 1]["version_id"] == vid("v2.0") and hist[i]["version_id"] == vid("v3.0") and hist[i - 1]["quote"]:
                quote = hist[i - 1]["quote"]
                if quote_in_text(quote, docs["v2.1"]) and quote_in_text(quote, docs["v2.2"]):
                    hist[i]["gap_before"] = False
                    hist[i:i] = [_entry(versions, "v2.1", dict(kept, quote=quote)), _entry(versions, "v2.2", dict(kept, quote=quote))]
                    stats["bridged_filled"] += 1
                else:
                    stats["bridged_not_filled"] += 1
                break

    # 2. Walk each family forward.
    carried = []
    for family, labels in FAMILIES.items():
        for item in _family_members(ledger, family):
            for label, fact in walk(item, family, docs, trace, code):
                if fact["status"] is None:
                    stats["waiting_for_code"] += 1
                    break
                item["history"].append(_entry(versions, label, fact))
                stats[f"{fact['coded_by']}:{fact['status']}"] += 1
                stats["needs_review"] += bool(fact.get("needs_review"))
            if family == "A" and item["history"][-1]["version_id"] == vid("v2.2") and item["history"][-1]["quote"]:
                carried.append(item)

    # 3. Join a chain carried to v2.2 with the upstream chain that starts at v2.2, when the texts overlap one to one.
    bases = [c for c in ledger["commitments"] if c["lab"] == LAB and c["first_version_id"] == vid("v2.2")
             and c["history"][0]["status"] == "baseline"]
    hits = {c["id"]: [b for b in bases if same_passage(c["history"][-1]["quote"], b["history"][0]["quote"])] for c in carried}
    back = collections.defaultdict(list)
    for cid, found in hits.items():
        for base in found:
            back[base["id"]].append(cid)
    gone = set()
    for chain in carried:
        found = hits[chain["id"]]
        if len(found) == 1 and len(back[found[0]["id"]]) == 1:
            base = found[0]
            tail = base["history"][1:]
            if tail:
                tail[0]["link"] = "text_overlap"
                tail[0]["gap_before"] = False
            chain["history"].extend(tail)
            chain["former_ids"].append(base["id"])
            gone.add(base["id"])
            stats["joined"] += 1
        elif found:
            for base in found:
                if base["id"] not in chain["related_ids"]:
                    chain["related_ids"].append(base["id"])
                if chain["id"] not in base["related_ids"]:
                    base["related_ids"].append(chain["id"])
            stats["overlap_not_joined"] += 1
    ledger["commitments"] = [c for c in ledger["commitments"] if c["id"] not in gone]

    # 4. An upstream chain that starts at v2.2 with words that are already in v2.1 or v2.0: move its first entry back.
    for base in bases:
        if base["id"] in gone:
            continue
        quote = base["history"][0]["quote"]
        earlier = []
        if quote_in_text(quote, docs["v2.1"]):
            earlier = ["v2.1"]
            if quote_in_text(quote, docs["v2.0"]):
                earlier = ["v2.0", "v2.1"]
        if earlier:
            first = base["history"][0]
            first.update(status="kept", coded_by="text_match", link="exact_text")
            new = [_entry(versions, label, dict(kept, quote=quote)) for label in earlier]
            new[0].update(status="baseline", link=None)
            base["history"][0:0] = new
            stats[f"moved_back_to_{earlier[0]}"] += 1

    # 4b. One person checked the model-coded entries, blind. Record the result. Do not overwrite the model code.
    human = _load(folder, "human_check.json")
    if human:
        names = {"R": "kept", "S": "strengthened", "W": "weakened"}
        given = {(a["id"], vid(a["version"])): a["code"] for a in human["answers"]}
        for item in ledger["commitments"]:
            for old in [item["id"]] + item["former_ids"]:
                for entry in item["history"]:
                    code = given.get((old, entry["version_id"]))
                    if code is None or entry["coded_by"] != "model":
                        continue
                    if code == "N":
                        entry["human_check"] = "not_same_thing"
                    elif code == "U":
                        entry["human_check"] = "cannot_tell"
                    elif names[code] == entry["status"]:
                        entry["human_check"] = "agrees"
                    else:
                        entry["human_check"] = "disagrees:" + names[code]
                    if entry["human_check"] != "agrees":
                        entry["needs_review"] = True
                    stats["human:" + entry["human_check"].split(":")[0]] += 1

    # 4c. Adjudication: a second look by a person, not blind. The final code replaces the model code.
    final = _load(folder, "adjudication.json")
    if final:
        names = {"R": "kept", "S": "strengthened", "W": "weakened"}
        decided = {(d["id"], vid(d["version"])): d for d in final["decisions"] if not d.get("held")}
        for item in ledger["commitments"]:
            for old in [item["id"]] + item["former_ids"]:
                for entry in item["history"]:
                    decision = decided.get((old, entry["version_id"]))
                    if decision is None or entry["coded_by"] != "model":
                        continue
                    code = decision["final"]
                    if code in names:
                        entry["status"] = names[code]
                        entry["material"] = code != "R"
                        entry["human_check"] = "adjudicated"
                        entry["needs_review"] = False
                    else:
                        entry["human_check"] = "adjudicated:" + {"N": "not_same_thing", "U": "cannot_tell"}[code]
                        entry["needs_review"] = True
                    stats["adjudicated"] += 1

    # 5. Recompute the fields that depend on the history.
    last_traced = vid(FAMILIES["B"][-1])
    for item in ledger["commitments"]:
        if item["lab"] != LAB:
            continue
        hist = item["history"]
        for entry in hist:
            entry["event_id"] = f"{item['id']}@{entry['version_id']}"
        quotes = [h["quote"] for h in hist if h["quote"]]
        item["text"] = quotes[-1]
        item["tags"] = tags_for(" ".join(quotes))
        item["first_version_id"], item["last_version_id"] = hist[0]["version_id"], hist[-1]["version_id"]
        if hist[-1]["status"] == "removed":
            item["current_status"] = "removed"
        elif hist[-1]["status"] == "relocated":
            item["current_status"] = "relocated"
        elif hist[-1]["version_id"] == last_traced:
            item["current_status"] = "active"
        else:
            item["current_status"] = "not_traced"
    for cov in ledger["labs"]:
        if cov["lab"] == LAB:
            cov["extended_pairs"] = EXTENDED_PAIRS
            cov["last_traced_version_id"] = last_traced
            cov["untraced_pairs"] = [p for p in cov["untraced_pairs"] if p not in EXTENDED_PAIRS]
    return stats


def human_report(folder):
    """Lines for validation.md: the human check of the model-coded extension entries."""
    human = _load(folder, "human_check.json")
    run1, run2 = _load(folder, "code_run1.json"), _load(folder, "code_run2.json")
    if not (human and run1 and run2):
        return []
    one = {(r["id"], r["version"]): r for r in run1}
    two = {(r["id"], r["version"]): r for r in run2}
    names = dict(human["codes"])
    rows = [(a, one[(a["id"], a["version"])], two[(a["id"], a["version"])]) for a in human["answers"]]
    decided = [r for r in rows if r[0]["code"] in "RSW"]
    agree = sum(r[0]["code"] == r[1]["outcome"] for r in decided)
    opposite = sum({r[0]["code"], r[1]["outcome"]} == {"S", "W"} for r in decided)
    both = [r for r in decided if r[1]["outcome"] == r[2]["outcome"]]
    agree_both = sum(r[0]["code"] == r[1]["outcome"] for r in both)
    pairs = [(r[1]["outcome"], r[0]["code"]) for r in decided]
    n = len(pairs)
    chance = sum(sum(g == c for g, _ in pairs) * sum(h == c for _, h in pairs) for c in "RSW") / (n * n)
    kappa = (agree / n - chance) / (1 - chance)
    lines = [
        "", "## Human check of the Anthropic extension: 47 model-coded entries", "",
        f"**Coder:** {human['coder']}. One person. Blind: the page showed the two texts, the version pair and the text around the later passage. "
        "It did not show the model's code or the commitment ID. Random sequence. Five answers: kept, strengthened, weakened, not the same thing, cannot tell. "
        "Page: `data/extension/anthropic/human_check_page.html`.", "",
        f"**Result: the human agrees with the model on {agree} of {n} decided entries ({100 * agree / n:.0f}%, Cohen's kappa {kappa:.2f}). "
        f"Opposite direction: {opposite} of {n}.** "
        f"Not decided: {sum(r[0]['code'] == 'N' for r in rows)} \"not the same thing\", {sum(r[0]['code'] == 'U' for r in rows)} \"cannot tell\".", "",
        f"Where the two model runs agree with each other ({len(both)} decided entries), the human agrees with them on {agree_both} ({100 * agree_both / len(both):.0f}%).", "",
        "| Model run 1 | Human: kept | Human: strengthened | Human: weakened | Human: not the same thing | Human: cannot tell |", "|---|---|---|---|---|---|",
    ]
    for code in "RSW":
        sub = [r for r in rows if r[1]["outcome"] == code]
        lines.append(f"| {names[code]} ({len(sub)}) | " + " | ".join(str(sum(r[0]["code"] == h for r in sub)) for h in "RSWNU") + " |")
    weak = [r for r in rows if r[1]["outcome"] == "W"]
    lines += [
        "",
        f"- **The model codes \"weakened\" more often than the human.** Of the {len(weak)} entries that the model coded weakened, the human coded "
        f"{sum(r[0]['code'] == 'W' for r in weak)} weakened, {sum(r[0]['code'] == 'R' for r in weak)} kept and {sum(r[0]['code'] == 'S' for r in weak)} strengthened.",
        "- **The ledger does not overwrite the model code.** An entry where the human agrees has `human_check: agrees`. Each other entry has `needs_review: true` and records the human answer.",
        "- **The blind disagreements are adjudicated below.**",
        "", "| Item | Commitment | Version | Model run 1 | Model run 2 | Human | Model's reason |", "|---|---|---|---|---|---|---|",
    ]
    for a, x, y in rows:
        if a["code"] != x["outcome"]:
            reason = clean(x.get("reason", "")).replace("|", "/")
            lines.append(f"| {a['item']} | `{a['id']}` | {a['version']} | {names[x['outcome']]} | {names[y['outcome']]} | {names[a['code']]} | {reason} |")
    final = _load(folder, "adjudication.json")
    if final:
        done = [d for d in final["decisions"] if not d.get("held")]
        held = [d for d in final["decisions"] if d.get("held")]
        coded = [d for d in done if d["final"] in "RSW"]
        k = lambda d: (d["id"], d["version"])
        runs_agree = [d for d in coded if one[k(d)]["outcome"] == two[k(d)]["outcome"]]
        runs_differ = [d for d in coded if one[k(d)]["outcome"] != two[k(d)]["outcome"]]
        first = {(a["id"], a["version"]): a["code"] for a in human["answers"]}
        lines += [
            "", "### Adjudication: a second look at the entries without agreement", "",
            f"**Method.** {final['method']} Page: `{final.get('page', '')}`. "
            f"{len(done)} entries adjudicated. {len(held)} held open.", "",
            "| Group | Entries | Final = model run 1 | Final = model run 2 | Final = first human answer |", "|---|---|---|---|---|",
            f"| The two model runs agreed | {len(runs_agree)} | {sum(d['final'] == one[k(d)]['outcome'] for d in runs_agree)} | {sum(d['final'] == two[k(d)]['outcome'] for d in runs_agree)} | {sum(d['final'] == first[k(d)] for d in runs_agree)} |",
            f"| The two model runs disagreed | {len(runs_differ)} | {sum(d['final'] == one[k(d)]['outcome'] for d in runs_differ)} | {sum(d['final'] == two[k(d)]['outcome'] for d in runs_differ)} | {sum(d['final'] == first[k(d)] for d in runs_differ)} |",
            "",
            f"- **Where the two model runs agreed, the adjudicated code is the model code in {sum(d['final'] == one[k(d)]['outcome'] for d in runs_agree)} of {len(runs_agree)} adjudicated entries.** "
            f"With the 34 entries where the blind check agreed, that is {34 + sum(d['final'] == one[k(d)]['outcome'] for d in runs_agree)} of {34 + len(runs_agree)} decided entries.",
            "- **One error passed two model runs (e19).** The two runs coded weakened, because a phrase was gone from the start of the passage. "
            "The phrase had moved to a new final sentence, outside the text that the model got, and it was stronger there. The blind human answer (kept) was also wrong. "
            "The error was found only when the full section was read.",
            f"- **Where the two model runs disagreed, the final code differs from model run 1 in {sum(d['final'] != one[k(d)]['outcome'] for d in runs_differ)} of {len(runs_differ)} entries.** "
            "The rule \"run two times, send disagreements to a person\" finds most errors, but not each one.",
            "- **The blind first answers were less reliable than the second look.** The adjudicator changed his own first answer in "
            f"{sum(d['final'] != first[k(d)] for d in coded)} of {len(coded)} adjudicated entries.",
            f"- Not coded on second look: {', '.join(d['item'] + ' (' + names[d['final']] + ')' for d in done if d['final'] not in 'RSW') or 'none'}. "
            f"Held open: {', '.join(d['item'] for d in held) or 'none'}.",
            "- **The second look was not blind.** The adjudicator saw the model's reasons. Agreement with the model after that is weaker evidence than blind agreement.",
            "", "| Item | Commitment | Version | Model run 1 | Model run 2 | First human answer | Final |", "|---|---|---|---|---|---|---|",
        ]
        for d in final["decisions"]:
            tail = " (held, not applied)" if d.get("held") else ""
            lines.append(f"| {d['item']} | `{d['id']}` | {d['version']} | {names[one[k(d)]['outcome']]} | {names[two[k(d)]['outcome']]} | {names[first[k(d)]]} | {names[d['final']]}{tail} |")
    lines += [
        "",
        "Limits: one coder, who is the author and is not independent. "
        f"The coder took about 28 minutes for {len(rows)} entries, which is about 36 seconds for each entry of about 900 characters plus context. "
        "The later text comes from a PDF extraction, and some extracts are cut by a page break. The coder used a summary of the rules.",
    ]
    return lines
