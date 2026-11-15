"""Build ledger.json from the upstream coding sheet.

The upstream sheet gives each commitment a new ID in each version pair.
This module connects those rows into one chain for each commitment, and
gives each chain one stable ID.
"""
import difflib
import hashlib
import re

from . import config
from .corpus import NONE, base_label, final, final_mixed, version_id
from .textnorm import clean, quote_in_text, section_key, squash


def _present(text):
    return text.strip() not in NONE


def _tags(text):
    return sorted(tag for tag, pattern in config.TAGS.items() if re.search(pattern, text, re.I))


def build_versions(corpus, provider, lab):
    versions = {}
    for row in corpus.framework_rows(provider):
        vid = version_id(lab, row["version"])
        item = {
            "label": row["version"],
            "sha256": row["sha256"],
            "source_url": row["retrieval_url"],
            "wayback_timestamp": row["wayback_capture_timestamp"] or None,
        }
        if row["version"] == base_label(row["version"]):
            versions[vid] = {
                "version_id": vid,
                "lab": lab,
                "lab_name": provider,
                "document": row["document"],
                "label": row["version"],
                "publication_date": row["publication_date"],
                "source_url": item["source_url"],
                "wayback_timestamp": item["wayback_timestamp"],
                "sha256": row["sha256"],
                "reuploads": versions.get(vid, {}).get("reuploads", []),
            }
        else:
            versions.setdefault(vid, {"reuploads": []})["reuploads"].append(item)
    out = sorted(versions.values(), key=lambda v: (v["publication_date"], v["version_id"]))
    for version in out:
        if not version["reuploads"]:
            del version["reuploads"]
    return out


class _Chain:
    def __init__(self, lab, category):
        self.lab = lab
        self.category = category
        self.history = []
        self.rows = []
        self.merged_into = None

    @property
    def last(self):
        return self.history[-1]

    @property
    def open(self):
        return self.last["status"] != "removed"


def build_lab(corpus, provider, lab):
    versions = build_versions(corpus, provider, lab)
    by_id = {v["version_id"]: v for v in versions}
    order = [v["version_id"] for v in versions]
    squashed = {}

    def source_text(label):
        if label not in squashed:
            raw = corpus.text(provider, label)
            squashed[label] = squash(raw) if raw else None
        return squashed[label]

    def entry(vid, status, quote, section, row, label, **extra):
        version = by_id[vid]
        text = source_text(label) if quote else None
        item = {
            "event_id": None,
            "version_id": vid,
            "status": status,
            "quote": clean(quote) if quote else None,
            "section": clean(section) if section and _present(section) else None,
            "section_changed": False,
            "mixed": False,
            "material": None,
            "disclosure": None,
            "confidence": None,
            "rationale": None,
            "link": None,
            "gap_before": False,
            "quote_verified": quote_in_text(quote, text) if (quote and text) else None,
            "source_row": row["commitment_id"] if row else None,
            "source_url": version["source_url"],
            "wayback_timestamp": version["wayback_timestamp"],
            "sha256": version["sha256"],
        }
        item.update(extra)
        return item

    chains = []
    by_row = {}
    traced_last = None

    for pair, rows in corpus.traced_pairs(provider):
        vid_i = version_id(lab, pair["v_i"])
        vid_next = version_id(lab, pair["v_next"])
        traced_last = vid_next
        candidates = [c for c in chains if c.open and c.last["quote"]]
        used = set()

        for row in rows:
            chain, link = None, None
            if _present(row["v_i_text"]):
                target = squash(row["v_i_text"])
                # The upstream sheet sometimes names the earlier row: "prior id XAI-3-038".
                # Two or more IDs mean that the upstream coder merged rows.
                priors = []
                if "prior id" in row["flags"]:
                    note = row["flags"].split("prior id", 1)[1].split(".")[0]
                    priors = [by_row[p] for p in re.findall(r"[A-Z]+-\d+-\d+", note) if p in by_row]
                for found in priors:
                    if chain is None and found.open and id(found) not in used:
                        chain, link = found, "prior_id"
                for found in priors:
                    if chain is not None and found is not chain and found.merged_into is None:
                        found.merged_into = chain
                        used.add(id(found))
                if chain is None:
                    for cand in candidates:
                        if id(cand) not in used and squash(cand.last["quote"]) == target:
                            chain, link = cand, "exact_text"
                            break
                if chain is None:
                    best, score = None, 0.0
                    for cand in candidates:
                        if id(cand) in used:
                            continue
                        ratio = difflib.SequenceMatcher(None, squash(cand.last["quote"]), target).ratio()
                        if ratio > score:
                            best, score = cand, ratio
                    if best is not None and score >= config.FUZZY_THRESHOLD:
                        chain, link = best, "fuzzy_text"
                if chain is None:
                    chain = _Chain(lab, row["category"])
                    chains.append(chain)
                    chain.history.append(entry(vid_i, "baseline", row["v_i_text"], row["v_i_section"], row, row["v_i"]))
                    link = "same_row"
                used.add(id(chain))
            else:
                chain = _Chain(lab, row["category"])
                chains.append(chain)

            outcome = final(row, "outcome")
            status = config.STATUS[outcome]
            quote = row["v_next_text"] if _present(row["v_next_text"]) else None
            previous = chain.history[-1] if chain.history else None
            gap = bool(previous) and order.index(vid_next) - order.index(previous["version_id"]) > 1
            new = entry(
                vid_next, status, quote, row["v_next_section"], row, row["v_next"],
                mixed=final_mixed(row),
                material=final(row, "material") == "yes",
                disclosure=config.DISCLOSURE.get(final(row, "announcement")),
                confidence=row["confidence"] or None,
                rationale=clean(row["rationale"]) or None,
                link=link,
                gap_before=gap,
            )
            if previous and new["section"] and previous["section"]:
                new["section_changed"] = section_key(new["section"]) != section_key(previous["section"])
            chain.history.append(new)
            chain.rows.append(row["commitment_id"])
            by_row[row["commitment_id"]] = chain

    commitments = []
    taken = set()
    ids = {}
    for chain in chains:
        first = chain.history[0]
        seed = first["quote"] or ""
        digest = hashlib.sha256(f"{lab}|{first['version_id']}|{squash(seed)}".encode()).hexdigest()
        topic = config.TOPIC[chain.category]
        size = 4
        while f"{lab}-{topic}-{digest[:size]}" in taken:
            size += 1
        cid = f"{lab}-{topic}-{digest[:size]}"
        taken.add(cid)
        ids[id(chain)] = cid
        for item in chain.history:
            item["event_id"] = f"{cid}@{item['version_id']}"
        quotes = [h["quote"] for h in chain.history if h["quote"]]
        last = chain.history[-1]
        if last["status"] == "removed":
            current = "removed"
        elif last["status"] == "relocated":
            current = "relocated"
        elif chain.merged_into is not None:
            current = "merged"
        elif last["version_id"] == traced_last:
            current = "active"
        else:
            current = "not_traced"
        commitments.append({
            "id": cid,
            "lab": lab,
            "text": quotes[-1],
            "topic": topic,
            "tags": _tags(" ".join(quotes)),
            "current_status": current,
            "merged_into": chain.merged_into,
            "first_version_id": first["version_id"],
            "last_version_id": last["version_id"],
            "history": chain.history,
        })
    for item in commitments:
        target = item["merged_into"]
        item["merged_into"] = ids[id(target)] if target is not None else None
    return versions, commitments


def build(corpus, labs=None):
    labs = labs or config.LABS
    ledger = {
        "schema_version": config.SCHEMA_VERSION,
        "source": {
            "name": "Frontier Safety Framework Corpus (Silent Revision)",
            "repo": config.CORPUS_REPO,
            "commit": config.CORPUS_COMMIT,
            "doi": config.CORPUS_DOI,
            "licence": "CC BY 4.0 (coding and manifest). Provider documents belong to their publishers.",
            "citation": config.CORPUS_CITATION,
        },
        "versions": [],
        "commitments": [],
    }
    for provider, lab in labs.items():
        versions, commitments = build_lab(corpus, provider, lab)
        ledger["versions"].extend(versions)
        ledger["commitments"].extend(commitments)
    ids = [c["id"] for c in ledger["commitments"]]
    assert len(ids) == len(set(ids)), "commitment IDs must be unique"
    return ledger
