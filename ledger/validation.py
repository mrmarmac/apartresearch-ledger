"""Test a model against the upstream codes.

Question: if the ledger gives a model two versions of one commitment,
does the model give the same code as the upstream coding (R, S or W)?

The sample is fixed by SEED. The key is never written to disk before the
model answers. `score` makes the key again from the seed.
"""
import collections
import json
import os
import random

from . import config
from .corpus import NONE, final
from .textnorm import clean

SEED = 20261115
PER_CLASS = 40
CLASSES = ("R", "S", "W")
BATCHES = 3
NAMES = {"R": "kept", "S": "strengthened", "W": "weakened"}


def _sample(corpus):
    pool = collections.defaultdict(list)
    for row in corpus.tracing:
        if row["provider"] not in config.LABS:
            continue
        if row["v_i_text"].strip() in NONE or row["v_next_text"].strip() in NONE:
            continue
        if "example" in row["flags"].lower():
            continue  # the upstream codebook uses these rows as worked examples
        code = final(row, "outcome")
        if code in CLASSES:
            pool[code].append(row)
    rng = random.Random(SEED)
    chosen = []
    for code in CLASSES:
        rows = sorted(pool[code], key=lambda r: r["commitment_id"])
        chosen.extend(rng.sample(rows, PER_CLASS))
    rng.shuffle(chosen)
    items, key = [], {}
    for number, row in enumerate(chosen, 1):
        qid = f"q{number:03d}"
        items.append({
            "id": qid,
            "developer": row["provider"],
            "earlier_section": clean(row["v_i_section"]),
            "earlier_text": clean(row["v_i_text"]),
            "later_section": clean(row["v_next_section"]),
            "later_text": clean(row["v_next_text"]),
        })
        key[qid] = {
            "source_row": row["commitment_id"],
            "gold": final(row, "outcome"),
            "disputed_upstream": row["READJ_mode"].startswith("re-examined"),
            "upstream_confidence": row["confidence"],
            "mixed": "MIX" in (row["READJ_flags"] if row["READJ_mode"].startswith("re-examined") else row["ADJ_flags"]),
        }
    return items, key, {code: len(rows) for code, rows in pool.items()}


def write_items(corpus, out_dir):
    items, _, pool = _sample(corpus)
    os.makedirs(out_dir, exist_ok=True)
    size = len(items) // BATCHES
    for b in range(BATCHES):
        with open(os.path.join(out_dir, f"batch_{b + 1}.json"), "w", encoding="utf-8") as handle:
            json.dump(items[b * size:(b + 1) * size], handle, indent=1, ensure_ascii=False)
    print(f"wrote {BATCHES} batches of {size} items to {out_dir} (pool: {pool})")


def _kappa(pairs):
    n = len(pairs)
    agree = sum(g == p for g, p in pairs) / n
    gold = collections.Counter(g for g, _ in pairs)
    pred = collections.Counter(p for _, p in pairs)
    chance = sum(gold[c] * pred[c] for c in CLASSES) / (n * n)
    return (agree - chance) / (1 - chance) if chance < 1 else 1.0


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return (centre - half, centre + half)


def _load_run(folder):
    out = {}
    if not os.path.isdir(folder):
        return out
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json"):
            with open(os.path.join(folder, name), encoding="utf-8") as handle:
                for item in json.load(handle):
                    out[item["id"]] = item
    return out


def _stability(val_dir, key, run1):
    run2 = _load_run(os.path.join(val_dir, "predictions_run2"))
    if not run2:
        return []
    ids = sorted(q for q in key if q in run1 and q in run2)
    n = len(ids)
    same = [q for q in ids if run1[q]["outcome"] == run2[q]["outcome"]]
    flips = [q for q in ids if q not in same]
    opposite = sum({run1[q]["outcome"], run2[q]["outcome"]} == {"S", "W"} for q in flips)
    gold2 = sum(run2[q]["outcome"] == key[q]["gold"] for q in ids)
    stable_ok = sum(run1[q]["outcome"] == key[q]["gold"] for q in same)
    lines = [
        "", "## Stability: a second run of the same model", "",
        "Same model, same items, same prompt, new sub-agents. Answers are in `validation/predictions_run2/`.", "",
        "| Comparison | Agreement | Cohen's kappa |", "|---|---|---|",
        f"| Run 2 against upstream | {gold2} of {n} ({100 * gold2 / n:.0f}%) | {_kappa([(key[q]['gold'], run2[q]['outcome']) for q in ids]):.2f} |",
        f"| Run 1 against run 2 | {len(same)} of {n} ({100 * len(same) / n:.0f}%) | {_kappa([(run1[q]['outcome'], run2[q]['outcome']) for q in ids]):.2f} |",
        "",
        f"- The model changed its answer on {len(flips)} of {n} items. {opposite} of those changes went to the opposite direction.",
        f"- On the {len(same)} items with the same answer in the two runs, the model agrees with upstream on {stable_ok} ({100 * stable_ok / len(same):.0f}%).",
        "- A practical rule follows: run the model two times and send each item with two different answers to a person.",
        "", "| Item | Upstream row | Upstream | Run 1 | Run 2 |", "|---|---|---|---|---|",
    ]
    for q in flips:
        lines.append(f"| {q} | `{key[q]['source_row']}` | {NAMES[key[q]['gold']]} | {NAMES[run1[q]['outcome']]} | {NAMES[run2[q]['outcome']]} |")
    return lines


def _human(val_dir, key, run1):
    folder = os.path.join(val_dir, "human")
    if not os.path.exists(os.path.join(folder, "answers.json")):
        return []
    with open(os.path.join(folder, "answers.json"), encoding="utf-8") as handle:
        record = json.load(handle)
    with open(os.path.join(folder, "mapping.json"), encoding="utf-8") as handle:
        mapping = json.load(handle)
    answers = record["answers"]
    lines = [
        "", "## Human check: one lawyer, 20 items", "",
        f"**Coder:** {record['coder']}. One person, no second human coder.", "",
        "**Design.** 20 of the 120 items: 10 drawn at random from the items where model run 1 agreed with upstream, "
        "and 10 drawn at random from the 15 items where it disagreed (seed 20261116). Mixed sequence. "
        "The coder did not see the upstream code, the model answers, or which group an item was in. "
        "The page (`validation/human/page.html`) showed the two texts, the headings, the developer name and a summary of the rules.", "",
        "**This is not a random sample of the 120.** Half of the items are disputed on purpose. Read the two groups separately. Do not combine them into one accuracy figure.", "",
        f"**Coded: {len(answers)} of {len(mapping)}.** The coder did not code {len(record['not_coded'])} items, because he did not accept that the two texts refer to the same commitment.", "",
        "| Group | Coded | Human = upstream | Human = model | Human = neither |", "|---|---|---|---|---|",
    ]
    for group, label in (("model_agreed", "Model agreed with upstream"), ("model_disagreed", "Model disagreed with upstream")):
        ids = [h for h in answers if mapping[h]["stratum"] == group]
        up = sum(answers[h] == key[mapping[h]["qid"]]["gold"] for h in ids)
        mo = sum(answers[h] == run1[mapping[h]["qid"]]["outcome"] for h in ids)
        neither = sum(answers[h] != key[mapping[h]["qid"]]["gold"] and answers[h] != run1[mapping[h]["qid"]]["outcome"] for h in ids)
        lines.append(f"| {label} | {len(ids)} | {up} | {mo} | {neither} |")
    kept = sum(v == "R" for v in answers.values())
    kept_up = sum(key[mapping[h]["qid"]]["gold"] == "R" for h in answers)
    opp_up = sum({answers[h], key[mapping[h]["qid"]]["gold"]} == {"S", "W"} for h in answers)
    opp_mo = sum({answers[h], run1[mapping[h]["qid"]]["outcome"]} == {"S", "W"} for h in answers)
    lines += [
        "",
        "Observations:", "",
        "- **Where the model and upstream disagree, the human agrees with upstream more often than with the model, but the numbers are very small.**",
        f"- **The human selects Kept more often:** {kept} of {len(answers)}, against {kept_up} of {len(answers)} for upstream on the same items. "
        "The human has a higher bar for a material change.",
        f"- **Opposite direction:** human against upstream, {opp_up} of {len(answers)}. Human against model, {opp_mo} of {len(answers)}.",
        f"- **Alignment doubt:** the coder rejected the pairing of {len(record['not_coded'])} of {len(mapping)} items. "
        "The upstream coding re-examined all of them as disputed. This supports limit 2 below: alignment is the weak step, and this test does not measure it.",
        "", "| Item | Upstream row | Group | Human | Upstream | Model run 1 |", "|---|---|---|---|---|---|",
    ]
    for h in sorted(mapping):
        q = mapping[h]["qid"]
        human = NAMES[answers[h]] if h in answers else "not coded: pairing rejected"
        group = "agreed" if mapping[h]["stratum"] == "model_agreed" else "disagreed"
        lines.append(f"| {h} ({q}) | `{key[q]['source_row']}` | {group} | {human} | {NAMES[key[q]['gold']]} | {NAMES[run1[q]['outcome']]} |")
    lines += [
        "",
        "Limits of the human check: one coder. The coder is the author of this project and is not independent of it. "
        f"{len(answers)} items. The coder took about 8 minutes for the {len(answers)} items, which is about 30 seconds for each item. "
        "The coder used a summary of the rules, not the full codebook.",
    ]
    return lines


def score(corpus, val_dir, model_name):
    items, key, pool = _sample(corpus)
    text = {i["id"]: i for i in items}
    preds = {}
    pred_dir = os.path.join(val_dir, "predictions")
    for name in sorted(os.listdir(pred_dir)):
        if name.endswith(".json"):
            with open(os.path.join(pred_dir, name), encoding="utf-8") as handle:
                for item in json.load(handle):
                    preds[item["id"]] = item
    missing = [q for q in key if q not in preds or preds[q].get("outcome") not in CLASSES]
    scored = [q for q in key if q not in missing]
    pairs = [(key[q]["gold"], preds[q]["outcome"]) for q in scored]
    n = len(pairs)
    hits = sum(g == p for g, p in pairs)
    lo, hi = _wilson(hits, n)
    matrix = collections.Counter(pairs)

    def rate(subset):
        k = sum(key[q]["gold"] == preds[q]["outcome"] for q in subset)
        a, b = _wilson(k, len(subset))
        return f"{k} of {len(subset)} ({100 * k / len(subset):.0f}%, 95% CI {100 * a:.0f} to {100 * b:.0f})" if subset else "none"

    lines = [
        "# Validation: a model against the upstream codes",
        "",
        "**Question.** The ledger gives a model two versions of one commitment. "
        "Does the model give the same code as the upstream coding: kept, strengthened or weakened?",
        "",
        "This test is for the future. A new framework version needs a classifier. "
        "The seed data in `data/ledger.json` does not use this model.",
        "",
        "## Method",
        "",
        f"- **Gold standard:** final codes in `coding/tracing_FINAL_v3.csv` of the upstream corpus (commit `{config.CORPUS_COMMIT[:12]}`).",
        f"- **Pool:** rows of the 5 ledger labs with text in both versions: {pool.get('R', 0)} kept, {pool.get('S', 0)} strengthened, {pool.get('W', 0)} weakened. "
        "Rows that the upstream codebook uses as worked examples are not in the pool.",
        f"- **Sample:** {PER_CLASS} rows for each code, {PER_CLASS * len(CLASSES)} in total. Random, seed {SEED}. Mixed sequence.",
        f"- **Model:** {model_name}, in {BATCHES} independent runs of {len(items) // BATCHES} items.",
        "- **Input to the model:** the two texts, their section headings, the developer name, and `validation/rules.md` (sections 4, 5 and 11.1 to 11.3 of the upstream codebook).",
        "- **Not given to the model:** the upstream code, the rationale, the row ID, or the source documents.",
        "- **Scoring:** `python run.py score`. The script makes the key again from the seed.",
        "",
        "## Result",
        "",
        f"**Agreement: {hits} of {n} ({100 * hits / n:.0f}%, 95% CI {100 * lo:.0f} to {100 * hi:.0f}). Cohen's kappa: {_kappa(pairs):.2f}.**",
        "",
        f"**Opposite direction** (strengthened against weakened): {matrix[('S', 'W')] + matrix[('W', 'S')]} of {n}. "
        "This is the most important error type for a ledger.",
        "",
        "| Upstream code | Model: kept | Model: strengthened | Model: weakened | Recall |",
        "|---|---|---|---|---|",
    ]
    for g in CLASSES:
        total = sum(matrix[(g, p)] for p in CLASSES)
        lines.append(f"| {NAMES[g]} | {matrix[(g, 'R')]} | {matrix[(g, 'S')]} | {matrix[(g, 'W')]} | {100 * matrix[(g, g)] / total:.0f}% |")
    prec = []
    for p in CLASSES:
        total = sum(matrix[(g, p)] for g in CLASSES)
        prec.append(f"{100 * matrix[(p, p)] / total:.0f}%" if total else "n/a")
    lines.append(f"| **Precision** | {prec[0]} | {prec[1]} | {prec[2]} | |")
    lines += [
        "",
        "The sample has the same number of rows for each code. The pool does not. "
        "Thus the agreement figure is not the agreement that you get on a full framework revision.",
        "",
        "## Agreement by row type",
        "",
        "| Row type | Agreement |",
        "|---|---|",
        f"| Upstream coding was stable (all re-runs agreed) | {rate([q for q in scored if not key[q]['disputed_upstream']])} |",
        f"| Upstream coding was disputed and re-examined | {rate([q for q in scored if key[q]['disputed_upstream']])} |",
        f"| Upstream confidence high | {rate([q for q in scored if key[q]['upstream_confidence'] == 'high'])} |",
        f"| Upstream confidence medium | {rate([q for q in scored if key[q]['upstream_confidence'] == 'medium'])} |",
        f"| Upstream confidence low | {rate([q for q in scored if key[q]['upstream_confidence'] == 'low'])} |",
        f"| Mixed change (stronger and weaker) | {rate([q for q in scored if key[q]['mixed']])} |",
    ]
    for lab in config.LABS:
        lines.append(f"| {lab} | {rate([q for q in scored if text[q]['developer'] == lab])} |")
    lines += ["", "## Disagreements", "",
              "| Item | Upstream row | Upstream | Model | Model's reason |", "|---|---|---|---|---|"]
    for q in scored:
        if key[q]["gold"] != preds[q]["outcome"]:
            reason = clean(str(preds[q].get("reason", ""))).replace("|", "/")
            lines.append(f"| {q} | `{key[q]['source_row']}` | {NAMES[key[q]['gold']]} | {NAMES[preds[q]['outcome']]} | {reason} |")
    lines += [
        "",
        "## Limits",
        "",
        "1. **The gold standard is not ground truth.** A language model helped with the upstream first pass. One human author adjudicated. "
        "Agreement thus shows consistency with that coding. It does not show that the code is correct.",
        "2. **This test does not include alignment.** The model gets a matched pair. To find the counterpart of a commitment in a new version is a different, harder step.",
        "3. **This test does not include Added, Removed or Relocated.** Those codes depend on alignment, not on direction.",
        "4. **Isolation was by instruction.** The model ran as a sub-agent with file tools. The instructions told it to read only its batch file and the rules. "
        "Each run made 4 tool calls, which agrees with: read rules, read batch, write answers, report.",
        "5. **Two runs only.** See the stability section. Two runs give a first estimate of how much the model changes, not a distribution.",
        "6. **The sample is 120 rows.** Read the confidence intervals.",
        "7. **The model is a high-capability model.** A low-cost model was not tested. Its agreement can be lower.",
    ]
    if missing:
        lines += ["", f"**Missing or invalid answers:** {len(missing)} ({', '.join(missing)}). They are not in the scores."]
    with open(os.path.join(val_dir, "key.json"), "w", encoding="utf-8") as handle:
        json.dump(key, handle, indent=1)
    with open(os.path.join(val_dir, "items.json"), "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=1, ensure_ascii=False)
    lines += _stability(val_dir, key, preds)
    lines += _human(val_dir, key, preds)
    from . import extend
    extend.DOC_DIR = os.path.join(os.path.dirname(val_dir), "cache", "documents")
    lines += extend.human_report(os.path.join(os.path.dirname(val_dir), "data", "extension", "anthropic"))
    extra = os.path.join(val_dir, "alignment", "report.md")
    if os.path.exists(extra):
        with open(extra, encoding="utf-8") as handle:
            lines += ["", handle.read().rstrip()]
    extra = os.path.join(val_dir, "watchtower.md")
    if os.path.exists(extra):
        with open(extra, encoding="utf-8") as handle:
            lines += ["", handle.read().rstrip()]
    out = os.path.join(os.path.dirname(val_dir), "validation.md")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"agreement {hits}/{n}, kappa {_kappa(pairs):.2f}, missing {len(missing)}; wrote validation.md")
