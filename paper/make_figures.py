"""Figures 3 to 8 for the paper. Reads data/ledger.json and the validation files.
Run: python paper/make_figures.py   (needs matplotlib)"""
import collections
import datetime
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(ROOT, "data", "ledger.json"), encoding="utf-8"))
LAB = {l["lab"]: l["name"] for l in L["labs"]}
V = {v["version_id"]: v for v in L["versions"]}
# Okabe-Ito palette: safe for colour-blind readers.
C = {"weakened": "#D55E00", "removed": "#7A1F1F", "relocated": "#CC79A7", "strengthened": "#0072B2",
     "added": "#56B4E9", "kept": "#BBBBBB", "upstream": "#999999", "text_match": "#009E73", "model": "#E69F00",
     "silent": "#D55E00", "no_account": "#7A1F1F", "partly_announced": "#E69F00", "announced": "#0072B2"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "figure.dpi": 150})
entries = [(c, h) for c in L["commitments"] for h in c["history"]]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote paper/" + name)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return 100 * (c - h) / d, 100 * (c + h) / d


# Figure 3: changes in each version, as a timeline.
def fig3():
    order = ["anthropic", "google", "openai", "meta", "xai"]
    kinds = ["weakened", "removed", "relocated", "strengthened", "added"]
    fig, axes = plt.subplots(len(order), 1, figsize=(9, 8.5), sharex=True)
    for ax, lab in zip(axes, order):
        versions = [v for v in L["versions"] if v["lab"] == lab][1:]
        for v in versions:
            date = datetime.date.fromisoformat(v["publication_date"])
            count = collections.Counter(h["status"] for c, h in entries if h["version_id"] == v["version_id"])
            down, up = 0, 0
            for kind in kinds:
                n = count[kind]
                if not n:
                    continue
                if kind in ("strengthened", "added"):
                    ax.bar(date, n, bottom=up, width=22, color=C[kind]); up += n
                else:
                    ax.bar(date, -n, bottom=-down, width=22, color=C[kind]); down += n
            ax.annotate(v["label"], (date, up), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7)
        ax.axhline(0, color="#333333", lw=0.8)
        ax.set_ylabel(LAB[lab], rotation=0, ha="right", va="center", fontsize=9)
        ax.set_yticks([t for t in ax.get_yticks() if t == int(t)])
        ax.yaxis.set_major_formatter(lambda x, _: f"{abs(int(x))}")
    axes[0].set_title("Each revision adds obligations (up) and takes obligations away (down)")
    axes[0].legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C[k]) for k in kinds], labels=kinds, ncol=5,
                   frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.12))
    axes[-1].set_xlabel("Publication date of the version. Bar height: number of commitments.")
    save(fig, "fig3_changes_by_version.png")


# Figure 4: did the developer tell the reader about a material change?
def fig4():
    kinds = ["announced", "partly_announced", "silent", "no_account"]
    labels = ["Announced", "Partly announced", "Silent (account exists, change not in it)", "No account published"]
    rows = []
    for lab in LAB:
        count = collections.Counter(h["disclosure"] for c, h in entries if c["lab"] == lab and h["disclosure"] in kinds)
        total = sum(count.values())
        if total:
            rows.append((LAB[lab], [100 * count[k] / total for k in kinds], total))
    rows.sort(key=lambda r: r[1][0])
    fig, ax = plt.subplots(figsize=(9, 3.6))
    left = [0] * len(rows)
    for i, kind in enumerate(kinds):
        vals = [r[1][i] for r in rows]
        ax.barh([f"{r[0]} (n={r[2]})" for r in rows], vals, left=left, color=C[kind], label=labels[i])
        for y, (val, start) in enumerate(zip(vals, left)):
            if val >= 8:
                ax.text(start + val / 2, y, f"{val:.0f}%", ha="center", va="center", color="white", fontsize=8)
        left = [a + b for a, b in zip(left, vals)]
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of material changes (upstream coding only)")
    ax.set_title("Most material changes were not announced in full")
    ax.legend(ncol=2, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    save(fig, "fig4_disclosure_by_lab.png")


# Figure 5: direction of change in each topic.
def fig5():
    topics = collections.Counter()
    weak, strong = collections.Counter(), collections.Counter()
    for c, h in entries:
        if h["status"] in ("weakened", "removed", "relocated"):
            weak[c["topic"]] += 1
        if h["status"] == "strengthened":
            strong[c["topic"]] += 1
    names = sorted(set(weak) | set(strong), key=lambda t: weak[t] - strong[t])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(names, [-weak[t] for t in names], color=C["weakened"], label="Weakened, removed or relocated")
    ax.barh(names, [strong[t] for t in names], color=C["strengthened"], label="Strengthened")
    for y, t in enumerate(names):
        ax.text(-weak[t] - 1, y, str(weak[t]), ha="right", va="center", fontsize=8)
        ax.text(strong[t] + 1, y, str(strong[t]), ha="left", va="center", fontsize=8)
    ax.axvline(0, color="#333333", lw=0.8)
    ax.xaxis.set_major_formatter(lambda x, _: f"{abs(int(x))}")
    ax.set_xlabel("Number of recorded changes, all developers")
    ax.set_title("In each topic, more changes reduce an obligation than increase it")
    ax.legend(ncol=2, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    save(fig, "fig5_direction_by_topic.png")


# Figure 6: who decided each entry.
def fig6():
    kinds = ["upstream", "text_match", "model"]
    labels = ["Upstream coding (Zhu)", "Text match (same words)", "Model, two runs"]
    order = sorted(LAB, key=lambda lab: -sum(1 for c, h in entries if c["lab"] == lab))
    fig, ax = plt.subplots(figsize=(8, 3.4))
    left = [0] * len(order)
    for kind, label in zip(kinds, labels):
        vals = [sum(1 for c, h in entries if c["lab"] == lab and h["coded_by"] == kind) for lab in order]
        ax.barh([LAB[lab] for lab in order], vals, left=left, color=C[kind], label=label)
        for y, (val, start) in enumerate(zip(vals, left)):
            if val >= 25:
                ax.text(start + val / 2, y, str(val), ha="center", va="center", color="white", fontsize=8)
        left = [a + b for a, b in zip(left, vals)]
    ax.invert_yaxis()
    ax.set_xlabel("History entries")
    ax.set_title("Text match did most of the ledger's own tracing; a model did the remainder")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "fig6_who_decided.png")


# Figure 7: all validation results on one scale, with 95% intervals.
def fig7():
    rows = [("Direction test: model = upstream code", 105, 120),
            ("Stability: run 2 = run 1", 113, 120),
            ("Alignment test: model finds the counterpart", 48, 60),
            ("Alignment test: text matching only", 37, 60),
            ("Blind human check = model (Anthropic)", 34, 44),
            ("Recall: model finds upstream additions", 26, 34),
            ("Watchtower xAI changes in the ledger", 14, 17),
            ("Watchtower Meta changes in the ledger", 15, 17)]
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for y, (name, k, n) in enumerate(rows):
        lo, hi = wilson(k, n)
        ax.plot([lo, hi], [y, y], color="#666666", lw=1.5)
        ax.plot(100 * k / n, y, "o", color=C["strengthened"] if "text matching" not in name else C["upstream"], ms=7)
        ax.text(101.5, y, f"{k} of {n}", va="center", fontsize=8)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_xlim(30, 100)
    ax.set_xlabel("Agreement, percent. Line: 95% confidence interval (Wilson).")
    ax.set_title("No check reaches 100%; small samples give wide intervals")
    ax.grid(axis="x", color="#EEEEEE")
    save(fig, "fig7_validation_summary.png")


# Figure 8: how long do the first traced commitments of a developer last?
# Anthropic is not in this figure: 60 of its chains stop with status not_traced.
def fig8():
    fig, ax = plt.subplots(figsize=(8, 4))
    colours = {"xai": "#D55E00", "google": "#0072B2", "meta": "#009E73", "openai": "#CC79A7"}
    offsets = {"openai": (8, -11)}
    for lab, colour in colours.items():
        versions = [v["version_id"] for v in L["versions"] if v["lab"] == lab]
        start = min(versions.index(c["first_version_id"]) for c in L["commitments"] if c["lab"] == lab)
        versions = versions[start:]
        first = [c for c in L["commitments"] if c["lab"] == lab and c["first_version_id"] == versions[0]
                 and c["current_status"] != "not_traced"]
        xs, ys = [], []
        for n, vid in enumerate(versions):
            gone = 0
            for c in first:
                seen = [h for h in c["history"] if h["version_id"] in versions[:n + 1]]
                if seen[-1]["status"] in ("removed", "relocated"):
                    gone += 1
            xs.append(datetime.date.fromisoformat(V[vid]["publication_date"]))
            ys.append(100 * (len(first) - gone) / len(first))
        ax.plot(xs, ys, "-o", color=colour, ms=5)
        ax.annotate(f"{LAB[lab]} (n={len(first)})", (xs[-1], ys[-1]), xytext=offsets.get(lab, (6, 0)),
                    textcoords="offset points", va="center", fontsize=8, color=colour)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Not removed, percent")
    ax.set_xlabel("Publication date of the version")
    ax.set_title("xAI removed the largest share of its first commitments")
    ax.margins(x=0.18)
    save(fig, "fig8_survival_of_first_commitments.png")


# Figure 9: one row for each xAI commitment, one column for each version.
def fig9():
    from matplotlib.patches import Patch
    versions = [v for v in L["versions"] if v["lab"] == "xai"]
    vids = [v["version_id"] for v in versions]
    items = [c for c in L["commitments"] if c["lab"] == "xai"]
    colour = {"baseline": "#DDDDDD", "kept": "#DDDDDD", "added": C["added"], "strengthened": C["strengthened"],
              "weakened": C["weakened"], "removed": C["removed"], "merged": "#888888"}
    rank = {"removed": 0, "weakened": 1, "merged": 2, "kept": 3, "baseline": 3, "strengthened": 4, "added": 5}

    def key(c):
        last = c["history"][-1]["status"]
        return (vids.index(c["first_version_id"]), rank.get(last, 3), -len(c["history"]))
    items.sort(key=key)
    fig, ax = plt.subplots(figsize=(7.5, 10.5))
    for y, c in enumerate(items):
        by = {h["version_id"]: h["status"] for h in c["history"]}
        for x, vid in enumerate(vids):
            status = by.get(vid)
            if status is None:
                continue
            ax.add_patch(plt.Rectangle((x + 0.04, y + 0.1), 0.92, 0.8, color=colour.get(status, "#DDDDDD"), lw=0))
        if c["merged_into"]:
            x = vids.index(c["last_version_id"]) + 1
            if x < len(vids):
                ax.add_patch(plt.Rectangle((x + 0.04, y + 0.1), 0.92, 0.8, color=colour["merged"], lw=0))
        ax.text(-0.08, y + 0.5, c["id"].replace("xai-", ""), ha="right", va="center", fontsize=5.5, family="monospace")
    ax.set_xlim(0, len(vids))
    ax.set_ylim(len(items), 0)
    ax.set_xticks([x + 0.5 for x in range(len(vids))],
                  [v["label"].replace("draft-", "draft\n") for v in versions], fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks([])
    for side in ("left", "bottom", "top"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    handles = [Patch(color="#DDDDDD", label="present, no material change"), Patch(color=C["added"], label="added"),
               Patch(color=C["strengthened"], label="strengthened"), Patch(color=C["weakened"], label="weakened"),
               Patch(color=C["removed"], label="removed"), Patch(color="#888888", label="merged into another row")]
    ax.legend(handles=handles, ncol=3, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.45, -0.01))
    ax.set_title("64 xAI commitments across 5 versions: one row is one commitment", pad=28)
    save(fig, "fig9_xai_commitment_strip.png")


# Figure 10: validation results in two groups.
def fig10():
    groups = [("Model against a reference", [
                  ("Stability: model run 2 = run 1", 113, 120),
                  ("Direction: model = upstream code", 105, 120),
                  ("Counterpart: model = upstream", 48, 60),
                  ("Counterpart: text matching only (baseline)", 37, 60),
                  ("Direction: blind human = model (Anthropic)", 34, 44),
                  ("New commitments: model finds upstream additions", 26, 34)]),
              ("Ledger against an independent tracker", [
                  ("Watchtower Meta changes that are in the ledger", 15, 17),
                  ("Watchtower xAI changes that are in the ledger", 14, 17)])]
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 4.8), sharex=True, gridspec_kw={"height_ratios": [6, 2]})
    for ax, (title, rows) in zip(axes, groups):
        rows = rows[::-1]
        for y, (name, k, n) in enumerate(rows):
            lo, hi = wilson(k, n)
            base = "baseline" in name
            ax.plot([lo, hi], [y, y], color="#666666", lw=1.5)
            ax.plot(100 * k / n, y, "o", color=C["upstream"] if base else C["strengthened"], ms=7)
            ax.text(101.5, y, f"{k} of {n}", va="center", fontsize=8)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.set_ylim(-0.6, len(rows) - 0.4)
        ax.set_xlim(40, 100)
        ax.grid(axis="x", color="#EEEEEE")
        ax.set_title(title, loc="left", fontsize=10)
    axes[-1].set_xlabel("Agreement, percent. Line: 95% interval (Wilson). Do not compare the two groups.")
    fig.suptitle("No check reaches 100%, and small samples give wide intervals", fontweight="bold", fontsize=12, x=0.5)
    save(fig, "fig10_validation_two_groups.png")


# Figure 11: one commitment, two versions, the change marked. The texts are verbatim.
# Each marked phrase is on its own line, so that the figure needs no text measurement.
def fig11():
    old = [("For example, if a model under test achieves", False),
           ("< 75% pass@10 success on all categories", True),
           ("of simple capture the flag (CTF) challenges", False),
           ("in unguided mode, we conclude that it does", False),
           ('not exceed the "moderate or lower" risk level.', False)]
    new = [("As discussed above, if a model under test achieves", False),
           ("sufficiently high performance", True),
           ("on simple suite challenges, we proceed to", False),
           ('evaluation on "Complex" challenges to determine', False),
           ('risk level. Otherwise, we rate its risk as', False),
           ('"moderate or lower."', False)]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    panels = [("Version 2, April 2026", old, C["removed"], "#F6DCD6"),
              ("Version 2.1, October 2026", new, C["weakened"], "#FFE9C2")]
    for ax, (head, lines, colour, tint) in zip(axes, panels):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#F7F7F7", lw=0))
        ax.text(0.05, 0.9, head, fontsize=10, fontweight="bold", va="center")
        y = 0.74
        for line, flag in lines:
            ax.text(0.05, y, line, fontsize=10, va="center", family="serif", color=colour if flag else "#222222",
                    fontweight="bold" if flag else "normal",
                    bbox=dict(facecolor=tint, edgecolor="none", pad=2.5) if flag else None)
            y -= 0.105
    fig.suptitle('A number becomes a judgement: "75% pass@10" is now "sufficiently high performance"',
                 fontweight="bold", fontsize=12)
    fig.text(0.5, -0.03, "Meta, cyber risk threshold. Commitment meta-eval-trigger-10c1. Ledger status at v2.1: weakened. "
             "Texts are verbatim; footnote marks are left out.", ha="center", fontsize=8, color="#555555")
    save(fig, "fig11_meta_text_change.png")


if __name__ == "__main__":
    for make in (fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11):
        make()
