"""Alignment test.

Question: given one commitment and the full text of the next framework
version, does a method find the same counterpart as the upstream coding?

Two methods are scored: a model (answers in validation/alignment/answers/)
and plain text matching (computed here).
"""
import difflib
import json
import os
import re

from .textnorm import clean, quote_in_text, squash

PAIRS = {
    "XAI-4": ("xAI", "2026-06-30", "xAI, 30 Dec 2025 to 30 Jun 2026"),
    "GDM-2": ("Google DeepMind", "v3.1", "Google DeepMind, v3.0 to v3.1"),
    "OAI-1": ("OpenAI", "v2", "OpenAI, Beta to v2"),
}
TEXT_THRESHOLD = 0.6


def same_passage(a, b):
    """True when two quotes share a long run of identical characters."""
    x, y = squash(a), squash(b)
    if not x or not y:
        return False
    short = min(len(x), len(y))
    match = difflib.SequenceMatcher(None, x, y, autojunk=False).find_longest_match(0, len(x), 0, len(y))
    return match.size >= max(30, 0.4 * short) or match.size == short


def text_match(earlier, document):
    """Baseline: the most similar one- or two-sentence window in the later document."""
    parts = [clean(p) for p in re.split(r"(?<=[.!?])\s+|\n\s*\n", document) if len(clean(p)) > 25]
    windows = parts + [parts[i] + " " + parts[i + 1] for i in range(len(parts) - 1)]
    target = squash(earlier)
    best, score = None, 0.0
    for window in windows:
        matcher = difflib.SequenceMatcher(None, target, squash(window), autojunk=False)
        if matcher.quick_ratio() <= score:
            continue
        ratio = matcher.ratio()
        if ratio > score:
            best, score = window, ratio
    return (best if score >= TEXT_THRESHOLD else None), score


def classify(gold, answer):
    if gold is None:
        return "both_none" if answer is None else "method_found_one"
    if answer is None:
        return "method_rejected"
    return "same" if same_passage(gold, answer) else "different"


LABELS = [
    ("same", "Upstream has a counterpart. Method found the same passage"),
    ("different", "Upstream has a counterpart. Method found a different passage"),
    ("method_rejected", "Upstream has a counterpart. Method said none"),
    ("both_none", "Upstream has none. Method said none"),
    ("method_found_one", "Upstream has none. Method found one"),
]


def run(corpus, folder, model_name):
    with open(os.path.join(folder, "key.json"), encoding="utf-8") as handle:
        key = json.load(handle)
    rows = []
    for pair, (provider, label, _) in PAIRS.items():
        document = corpus.text(provider, label)
        squashed = squash(document)
        with open(os.path.join(folder, "items", f"{pair}_items.json"), encoding="utf-8") as handle:
            items = json.load(handle)
        path = os.path.join(folder, "answers", f"{pair}.json")
        answers = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                answers = {a["id"]: a for a in json.load(handle)}
        for item in items:
            gold = key[item["id"]]["gold_quote"]
            given = answers.get(item["id"])
            model = None
            verified = None
            if given and given.get("counterpart", "").strip().upper() != "NONE":
                model = given["counterpart"]
                verified = quote_in_text(model, squashed)
            baseline, score = text_match(item["earlier_text"], document)
            rows.append({
                "id": item["id"], "pair": pair, "row": key[item["id"]]["source_row"],
                "outcome": key[item["id"]]["outcome"], "disputed": key[item["id"]]["disputed"],
                "forced": key[item["id"]]["forced"],
                "earlier": item["earlier_text"], "gold": gold, "model": model, "model_verified": verified,
                "model_reason": (given or {}).get("reason", ""), "answered": given is not None,
                "model_class": classify(gold, model) if given else None,
                "text": baseline, "text_score": score, "text_class": classify(gold, baseline),
            })
    return rows


def report(rows, model_name):
    done = [r for r in rows if r["answered"]]
    n = len(done)

    def count(field, name, subset=None):
        return sum(r[field] == name for r in (subset if subset is not None else done))

    def agree(field, subset=None):
        subset = subset if subset is not None else done
        return count(field, "same", subset) + count(field, "both_none", subset)

    quotes = [r for r in done if r["model"]]
    lines = [
        "", "## Alignment test: find the counterpart", "",
        "**Question.** A method gets one commitment from the earlier version and the full text of the later version. "
        "Does it find the same counterpart as the upstream coding, or correctly find none?", "",
        "### Method", "",
        f"- **Sample:** {len(rows)} commitments from 3 version pairs, 20 for each pair. Random, seed 20261117. "
        "For each pair, up to 6 commitments with no upstream counterpart are included first. "
        "Two rows (`OAI-1-022`, `OAI-1-026`) are included on purpose: the human coder rejected their pairing.",
        f"- **Model:** {model_name}. One sub-agent for each pair. Input: the 20 earlier texts, the full later document, and section 3 of the upstream codebook (`validation/alignment/definition.md`).",
        "- **Not given to the model:** the coding rules, the upstream counterpart, the outcome code, or the row ID.",
        f"- **Text matching:** the most similar window of one or two sentences in the later document (Python `difflib`). A ratio below {TEXT_THRESHOLD} means no counterpart.",
        "- **Same passage:** the two quotes share a run of identical characters of 40% of the shorter quote or more (30 characters minimum).",
        "- **Scoring:** `python run.py align`.", "",
        "### Result", "",
        f"**Model: {agree('model_class')} of {n} agree with upstream ({100 * agree('model_class') / n:.0f}%). "
        f"Text matching: {agree('text_class')} of {n} ({100 * agree('text_class') / n:.0f}%).**", "",
        "| Case | Model | Text matching |", "|---|---|---|",
    ]
    for name, label in LABELS:
        lines.append(f"| {label} | {count('model_class', name)} | {count('text_class', name)} |")
    lines += ["", "| Version pair | Model agrees | Text matching agrees |", "|---|---|---|"]
    for pair, (_, _, title) in PAIRS.items():
        subset = [r for r in done if r["pair"] == pair]
        if subset:
            lines.append(f"| {title} | {agree('model_class', subset)} of {len(subset)} | {agree('text_class', subset)} of {len(subset)} |")
    lines += ["", "| Upstream outcome of the row | Model agrees | Text matching agrees |", "|---|---|---|"]
    for code, name in (("R", "kept"), ("S", "strengthened"), ("W", "weakened"), ("X", "removed")):
        subset = [r for r in done if r["outcome"] == code]
        if subset:
            lines.append(f"| {name} | {agree('model_class', subset)} of {len(subset)} | {agree('text_class', subset)} of {len(subset)} |")
    if quotes:
        ok = sum(bool(r["model_verified"]) for r in quotes)
        lines += ["", f"**Quote check:** {ok} of {len(quotes)} model quotes are in the later document text."]
    forced = [r for r in done if r["forced"]]
    if forced:
        lines += ["", "**The two pairings that the human coder rejected:**", ""]
        for r in forced:
            verdict = {"same": "found the same passage as upstream", "different": "found a different passage",
                       "method_rejected": "said no counterpart"}[r["model_class"]]
            lines.append(f"- `{r['row']}`: the model {verdict}.")
    lines += ["", "### Cases where the model and upstream do not agree", "",
              "| Item | Upstream row | Case | Earlier text | Upstream counterpart | Model counterpart | Model's reason |", "|---|---|---|---|---|---|---|"]

    def cell(text, limit=170):
        text = clean(text or "none").replace("|", "/")
        return text if len(text) <= limit else text[: limit - 1] + "…"

    for r in done:
        if r["model_class"] not in ("same", "both_none"):
            label = dict(LABELS)[r["model_class"]].split(". ")[1]
            lines.append(f"| {r['id']} | `{r['row']}` | {label} | {cell(r['earlier'])} | {cell(r['gold'])} | {cell(r['model'])} | {cell(r['model_reason'], 200)} |")
    lines += ["", "__REVIEW__"]
    lines += [
        "", "### Limits", "",
        "1. **The upstream counterpart is not ground truth.** A disagreement can be an upstream error. The human check found 3 doubtful pairings in 20.",
        "2. **\"Same passage\" is a text rule.** Two adjacent sentences of one paragraph can count as different passages. I read each disagreement; see the notes below the table.",
        "3. **Three version pairs, 60 items, one run.**",
        "4. **Few items with no counterpart** (10 of 60). The figure for removed commitments has a wide interval.",
        "5. **Isolation was by instruction**, as in the direction test.",
        "6. **The test goes one way only.** It does not test if a method finds commitments that are new in the later version.",
    ]
    return lines
