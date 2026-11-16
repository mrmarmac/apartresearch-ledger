"""Render the static site and the RSS feed from ledger.json. No dependencies.

Pages:
  index.html            overview: what the Ledger is, developers, latest revisions
  browse.html           every commitment, with search, filters and sorting
  d/{developer}.html    one developer: versions, outcomes, every commitment at a glance
  v/{version_id}.html   one framework version: everything that changed in it
  revisions.html        every framework version, newest first
  c/{commitment_id}.html  one commitment: its history, wording and sources
  about.html            method, definitions, checks, limits, reuse
  assets/site.css, assets/site.js

The build has no clock and no network: two builds give the same files.
"""
import collections
import datetime
import difflib
import email.utils
import html
import os
import shutil
from xml.sax.saxutils import escape as x

from . import config

E = html.escape

DEMO_ID = "xai-governance-673f"
CHANGES = config.FEED_STATUSES  # added, strengthened, weakened, removed, relocated
# Most serious first. Used for lists of changes.
CHANGE_ORDER = ("removed", "relocated", "weakened", "strengthened", "added")
CELL_ORDER = ("baseline", "added", "kept", "strengthened", "weakened", "removed", "relocated")

# Site wording. The paper says "developer", "source" and "Ledger".
CODED_BY = {
    "upstream": "Source coding (Zhu, 2026): a language model first pass, adjudicated by that study's author",
    "text_match": "Text match: the same words are in this version",
    "model": "Language model, two runs",
}
CODED_BY_SHORT = {"upstream": "Source coding", "text_match": "Text match", "model": "Language model"}
STATUS_MEANING = {
    "baseline": "The first version where the Ledger sees the commitment. No claim of change.",
    "added": "In this version, with no counterpart in the version before.",
    "kept": "A counterpart exists and nothing material changed. The words can differ.",
    "strengthened": "The obligation became larger in one or more ways, and smaller in none.",
    "weakened": "The obligation became smaller in one or more ways. Also used for mixed changes.",
    "removed": "No counterpart in this version.",
    "relocated": "The counterpart moved to a companion document or a non-binding section.",
}
CURRENT_MEANING = {
    "active": "In the last version that the Ledger traces for this developer. It says nothing about compliance.",
    "removed": "The last entry in the history is a removal.",
    "relocated": "The last entry moved the text to a companion document or a non-binding section.",
    "merged": "The source coding merged this commitment into another one.",
    "not_traced": "The record stops. The Ledger could not follow the commitment further. This is not a removal.",
}
DISCLOSURE_SHORT = {
    "announced": "Identified in the developer's account",
    "partly_announced": "Area identified, change not identified",
    "silent": "Not identified in the developer's account",
    "no_account": "No account published",
}


def _date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def _date_short(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.strftime('%y')}"


def _rfc822(iso):
    d = datetime.datetime.fromisoformat(iso).replace(tzinfo=datetime.timezone.utc)
    return email.utils.format_datetime(d)


def _short(text, limit=150):
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _plural(n, word, many=None):
    return f"{n:,} {word if n == 1 else (many or word + 's')}"


def _badge(status):
    mark = config.STATUS_MARK.get(status)
    lead = f'<span aria-hidden="true">{mark}</span> ' if mark else ""
    return f'<span class="badge s-{status}">{lead}{E(config.STATUS_LABEL[status])}</span>'


def _diff(old, new):
    """Word diff. Returns (ratio, html)."""
    a, b = old.split(), new.split()
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for op, a0, a1, b0, b1 in matcher.get_opcodes():
        if op == "equal":
            out.append(E(" ".join(a[a0:a1])))
        else:
            if a1 > a0:
                out.append(f"<del>{E(' '.join(a[a0:a1]))}</del>")
            if b1 > b0:
                out.append(f"<ins>{E(' '.join(b[b0:b1]))}</ins>")
    return matcher.ratio(), " ".join(out)


def _wayback(entry):
    if "web.archive.org/web/" in entry["source_url"]:
        return None
    if entry["wayback_timestamp"]:
        return f"https://web.archive.org/web/{entry['wayback_timestamp']}/{entry['source_url']}"
    return f"https://web.archive.org/web/*/{entry['source_url']}"


def _vlabel(v):
    """Short column label for a version: its own label when that is short, else its date."""
    label = v["label"]
    return label if len(label) <= 6 else _date_short(v["publication_date"])


def _vname(v):
    """Readable version name: 'v3.4' or '30 Jun 2026'."""
    label = v["label"]
    return label if len(label) <= 6 else _date(v["publication_date"])


class Site:
    """Everything the pages need, worked out one time from the ledger."""

    def __init__(self, ledger):
        self.ledger = ledger
        self.items = ledger["commitments"]
        self.versions = {v["version_id"]: v for v in ledger["versions"]}
        self.cov = {c["lab"]: c for c in ledger["labs"]}
        self.labs = {c["lab"]: c["name"] for c in ledger["labs"]}
        for v in ledger["versions"]:
            self.labs.setdefault(v["lab"], v.get("lab_name", v["lab"]))
        self.lab_versions = collections.defaultdict(list)
        for v in sorted(ledger["versions"], key=lambda v: (v["publication_date"], v["version_id"])):
            self.lab_versions[v["lab"]].append(v)
        self.by_lab = collections.defaultdict(list)
        for c in self.items:
            self.by_lab[c["lab"]].append(c)
        # version_id -> [(commitment, index in history)]
        self.at = collections.defaultdict(list)
        for c in self.items:
            for i, h in enumerate(c["history"]):
                self.at[h["version_id"]].append((c, i))
        self.pair = {}
        for cov in ledger["labs"]:
            for a, b in cov["traced_pairs"]:
                self.pair[(a, b)] = "source"
            for a, b in cov.get("extended_pairs", []):
                self.pair[(a, b)] = "ledger"
            for a, b in cov["untraced_pairs"]:
                self.pair[(a, b)] = "untraced"
        self.n_changes = sum(1 for c in self.items for h in c["history"] if h["status"] in CHANGES)
        self.newest = max(ledger["versions"], key=lambda v: (v["publication_date"], v["version_id"]))

    def counts(self, version_id):
        return collections.Counter(c["history"][i]["status"] for c, i in self.at[version_id])

    def previous(self, version_id):
        row = self.lab_versions[self.versions[version_id]["lab"]]
        n = [v["version_id"] for v in row].index(version_id)
        return (row[n - 1] if n else None), (row[n + 1] if n + 1 < len(row) else None)

    def traced_by(self, version_id):
        before, _ = self.previous(version_id)
        if before is None:
            return "first"
        return self.pair.get((before["version_id"], version_id), "untraced")


def _cells(site, c):
    """One cell for each version of the developer. An empty cell means no record in that version."""
    by_version = {h["version_id"]: h for h in c["history"]}
    out = []
    for v in site.lab_versions[c["lab"]]:
        h = by_version.get(v["version_id"])
        name = f'{_vname(v)}, {_date(v["publication_date"])}' if _vname(v) != _date(v["publication_date"]) else _vname(v)
        if h:
            out.append(f'<i class="k s-{h["status"]}" title="{E(name)}: {E(config.STATUS_LABEL[h["status"]])}">'
                       f'{config.STATUS_MARK[h["status"]]}</i>')
        else:
            out.append(f'<i class="k s-none" title="{E(name)}: no record"></i>')
    return f'<span class="strip" aria-hidden="true">{"".join(out)}</span>'


def _legend(statuses=CELL_ORDER, none=True):
    rows = "".join(f'<span><i class="k s-{s}">{config.STATUS_MARK[s]}</i>{E(config.STATUS_LABEL[s])}</span>' for s in statuses)
    if none:
        rows += '<span><i class="k s-none"></i>No record</span>'
    return f'<div class="legend" role="note" aria-label="Legend: one square for each framework version">{rows}</div>'


def _count_chips(counts, order=CHANGE_ORDER, zero=False):
    out = []
    for s in order:
        if counts.get(s) or zero:
            out.append(f'<span class="num s-{s}"><b>{counts.get(s, 0)}</b> {E(config.STATUS_LABEL[s].lower())}</span>')
    return "".join(out)


def _bar(counts, order, total=None):
    """A stacked proportion bar. Widths are whole-number shares of the total."""
    total = total or sum(counts.get(s, 0) for s in order)
    if not total:
        return ""
    parts = "".join(
        f'<i class="s-{s}" style="flex:{counts[s]} 0 0" title="{E(config.STATUS_LABEL[s])}: {counts[s]}"></i>'
        for s in order if counts.get(s))
    return f'<span class="bar" aria-hidden="true">{parts}</span>'


LOGO = ('<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="2" width="5" height="5" rx="1" fill="currentColor"/>'
        '<rect x="8" y="2" width="5" height="5" rx="1" fill="currentColor" opacity=".55"/><rect x="15" y="2" width="5" height="5" rx="1" fill="currentColor" opacity=".25"/>'
        '<rect x="1" y="9" width="5" height="5" rx="1" fill="currentColor"/><rect x="8" y="9" width="5" height="5" rx="1" fill="currentColor"/>'
        '<rect x="15" y="9" width="5" height="5" rx="1" fill="currentColor" opacity=".55"/><rect x="1" y="16" width="5" height="5" rx="1" fill="currentColor"/>'
        '<rect x="8" y="16" width="5" height="5" rx="1" fill="currentColor" opacity=".25"/></svg>')
FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700"
         "&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap")


def _page(title, body, root, description, active=""):
    def nav(key, href, text):
        current = ' aria-current="page"' if key == active else ""
        return f'<a href="{root}{href}"{current}>{text}</a>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:type" content="website">
<link rel="alternate" type="application/rss+xml" title="{E(config.SITE_TITLE)}: changes" href="{root}feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{root}assets/site.css">
<script>try{{var t=localStorage.getItem('ledger-theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
<script src="{root}assets/site.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
<a class="brand" href="{root}index.html">{LOGO}{E(config.SITE_TITLE)}</a>
<nav class="nav" aria-label="Main">
{nav("browse", "browse.html", "Browse")}{nav("developers", "index.html#developers", "Developers")}{nav("revisions", "revisions.html", "Revisions")}{nav("about", "about.html", "About")}
<span class="sep wideonly" aria-hidden="true"></span>
<a class="wideonly" href="{root}ledger.json">Data</a><a class="wideonly" href="{root}feed.xml">RSS</a><a class="wideonly" href="{config.REPO_URL}">GitHub</a>
</nav>
<button type="button" id="theme" class="themebtn" aria-label="Switch between light and dark">Dark</button>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p class="links"><a href="{root}browse.html">Browse commitments</a><a href="{root}revisions.html">Revisions</a><a href="{root}about.html">Method and limits</a>
<a href="{root}ledger.json">ledger.json</a><a href="{root}schema.json">schema.json</a><a href="{root}feed.xml">RSS feed</a><a href="{config.REPO_URL}">GitHub</a></p>
<p>Statuses are a reference, not ground truth. Most come from the coding of the
<a href="{config.CORPUS_REPO}">Frontier Safety Framework Corpus</a> by Louis Yiven Zhu
(<a href="https://arxiv.org/abs/2609.08789">Silent Revision, arXiv:2609.08789</a>, CC BY 4.0): a language model first pass, adjudicated by that study's author.</p>
<p>Ledger data: CC BY 4.0. Code: MIT. Quoted framework text belongs to its publisher; each quote links to its source document by address and SHA-256.
Builds on <a href="https://www.themidasproject.com/watchtower">Watchtower</a> by The Midas Project, which did not take part in this work.</p>
</div></footer>
</body>
</html>
"""


def _story(site, c):
    """One plain sentence on what happened to a commitment."""
    first, last = c["history"][0], c["history"][-1]
    when = lambda h: _date(site.versions[h["version_id"]]["publication_date"])
    kept = sum(1 for h in c["history"][1:] if h["status"] == "kept")
    parts = [f"First seen on {when(first)}."]
    if kept:
        parts.append(f"Kept in {_plural(kept, 'later version')}.")
    if last["status"] == "removed":
        parts.append(f"Removed on {when(last)}.")
        if last.get("disclosure") == "no_account":
            parts.append("The developer published no account of that revision.")
        elif last.get("disclosure") == "silent":
            parts.append("The developer's account of that revision does not identify the removal.")
    return " ".join(parts)


def _seen(site, c, root=""):
    by_version = {h["version_id"]: h for h in c["history"]}
    out = []
    for v in site.lab_versions[c["lab"]]:
        h = by_version.get(v["version_id"])
        label = E(_vlabel(v))
        if h:
            out.append(f'<li><a href="{root}c/{c["id"]}.html#{E(v["version_id"])}" title="{E(config.STATUS_LABEL[h["status"]])}">'
                       f'<i class="k s-{h["status"]}">{config.STATUS_MARK[h["status"]]}</i>{label}</a></li>')
        else:
            out.append(f'<li><a href="{root}v/{E(v["version_id"])}.html" title="No record in this version"><i class="k s-none"></i>{label}</a></li>')
    return f'<ol class="seen">{"".join(out)}</ol>'


def _version_row(site, v, root="", with_lab=True):
    counts = site.counts(v["version_id"])
    traced = site.traced_by(v["version_id"])
    if traced == "first":
        right = f'<span class="num s-baseline"><b>{counts.get("baseline", 0)}</b> first seen</span>'
    elif traced == "untraced":
        right = '<span class="num s-not_traced">not traced</span>'
    else:
        right = _count_chips(counts) or '<span class="num s-kept">no change recorded</span>'
    parts = ([site.labs[v["lab"]]] if with_lab else []) + ([_vname(v)] if _vname(v) != _date(v["publication_date"]) else [])
    title = " · ".join(parts)
    small = f' <small>{E(v["document"])}</small>' if title else ""
    return (f'<li><a class="vrow" href="{root}v/{E(v["version_id"])}.html"><time datetime="{v["publication_date"]}">{_date(v["publication_date"])}</time>'
            f'<span class="vt">{E(title) if title else E(v["document"])}{small}</span>'
            f'<span class="nums">{right}</span></a></li>')


def render_home(site):
    items = site.items
    cards = []
    for lab, name in site.labs.items():
        mine = site.by_lab[lab]
        versions = site.lab_versions[lab]
        now = collections.Counter(c["current_status"] for c in mine)
        now["not_traced"] += now.pop("merged", 0)
        events = collections.Counter(h["status"] for c in mine for h in c["history"] if h["status"] in CHANGES)
        span = f'{versions[0]["publication_date"][:4]} to {versions[-1]["publication_date"][:4]}'
        cards.append(
            f'<a class="card dev" href="d/{lab}.html"><h3>{E(name)} <span>{_plural(len(versions), "version")}, {span}</span></h3>'
            f'<p>{E(versions[-1]["document"])}</p>'
            f'{_bar(now, ("active", "removed", "relocated", "not_traced"))}'
            f'<p><b style="color:var(--ink)">{len(mine)}</b> commitments: {now.get("active", 0)} in force, {now.get("removed", 0)} removed'
            + (f', {now["relocated"]} relocated' if now.get("relocated") else "")
            + (f', {now["not_traced"]} not traced' if now.get("not_traced") else "") + "</p>"
            f'<div class="nums">{_count_chips(events)}</div></a>')
    recent = [v for v in sorted(site.ledger["versions"], key=lambda v: (v["publication_date"], v["version_id"]), reverse=True)
              if site.traced_by(v["version_id"]) != "first"][:6]
    demo = next((c for c in items if c["id"] == DEMO_ID), None)
    example = ""
    if demo:
        example = f"""
<h2>One commitment, start to finish</h2>
<p class="sub">Every commitment has a page like this one: its wording in each version, what changed, and the source file behind each entry.</p>
<div class="card">
<div class="rmeta">{_badge(demo["current_status"])}<span>{E(site.labs[demo["lab"]])}</span><span>{E(config.TOPIC_LABEL[demo["topic"]])}</span><span class="mono">{demo["id"]}</span></div>
<div class="quote"><a href="c/{demo["id"]}.html" style="text-decoration:none">{E(demo["text"])}</a></div>
<p class="note">{E(_story(site, demo))}</p>
{_seen(site, demo)}
<p style="margin:12px 0 0"><a class="btn sm" href="c/{demo["id"]}.html">Open this commitment</a></p>
</div>"""
    meanings = "".join(f'<tr><td>{_badge(s)}</td><td>{E(STATUS_MEANING[s])}</td></tr>' for s in ("kept", "strengthened", "weakened", "removed", "relocated", "added", "baseline"))
    n_model = sum(1 for c in items for h in c["history"] if h.get("coded_by") == "model")
    n_checked = sum(1 for c in items for h in c["history"] if h.get("coded_by") == "model" and h.get("human_check"))
    n_ledger_pairs = sum(1 for kind in site.pair.values() if kind == "ledger")
    newest = site.newest
    body = f"""
<section class="hero">
<p class="eyebrow">An open record of AI safety framework commitments</p>
<h1>What did each AI developer promise, and what happened to each promise?</h1>
<p class="lede">The Commitment Ledger follows {len(items)} commitments from the safety frameworks of {len(site.labs)} AI developers across {len(site.ledger["versions"])} framework versions.
Each commitment has a permanent ID, its exact wording in every version, and a link to the hashed source document.</p>
<form class="searchline" action="browse.html" method="get" role="search">
<input type="search" name="q" placeholder="Search the commitments, for example: whistleblower" aria-label="Search the commitments" autocomplete="off">
<button class="btn primary" type="submit">Search</button>
</form>
<p class="small muted">Or <a href="browse.html">browse all {len(items)}</a>, see <a href="browse.html?current=removed">what was removed</a>, or <a href="browse.html?event=weakened">what was weakened</a>.</p>
<div class="stats">
<div><b>{len(items)}</b><span>commitments with a permanent ID</span></div>
<div><b>{len(site.labs)}</b><span>developers</span></div>
<div><b>{len(site.ledger["versions"])}</b><span>framework versions, {min(v["publication_date"] for v in site.ledger["versions"])[:4]} to {newest["publication_date"][:4]}</span></div>
<div><b>{site.n_changes}</b><span>recorded changes</span></div>
</div>
</section>

<h2 id="developers">Developers</h2>
<p class="sub">Open a developer to see every version of its framework and every commitment at a glance.</p>
<div class="grid g3">{"".join(cards)}</div>
<div class="keyline" style="margin-top:10px"><span><i class="dot s-active"></i>In force</span><span><i class="dot s-removed"></i>Removed</span><span><i class="dot s-relocated"></i>Relocated</span><span><i class="dot s-not_traced"></i>Not traced</span><span class="muted">The bar shows where each developer's commitments stand now. The counts below it are changes over time.</span></div>

<h2>Latest revisions</h2>
<p class="sub">Each framework version has a page that lists what changed in it. The newest version in the Ledger is {E(site.labs[newest["lab"]])} {E(_vname(newest))}, {_date(newest["publication_date"])}.</p>
<ul class="rows">{"".join(_version_row(site, v) for v in recent)}</ul>
<p style="margin-top:12px"><a class="btn sm" href="revisions.html">All {len(site.ledger["versions"])} versions</a></p>
{example}

<h2 id="read">How to read a status</h2>
<div class="grid g2" style="align-items:start">
<div class="card"><div class="scroll"><table style="min-width:0"><tbody>{meanings}</tbody></table></div>
<p class="note">A status describes the change from the version before. Rules: <a href="about.html#statuses">definitions</a>.</p></div>
<div class="callout" style="margin:0">
<h3>Read this before you cite a status</h3>
<ul>
<li><b>Statuses are a reference, not ground truth.</b> Most come from the coding of Zhu (2026): a language model first pass, adjudicated by that study's author. No second person coded independently.</li>
<li><b>The Ledger traced {n_ledger_pairs} version pairs itself</b>, with text matching and a language model. {n_model} entries were coded by the model. One person checked {n_checked} of them.</li>
<li><b>"In force" means "in the last traced version".</b> It says nothing about whether the developer complies.</li>
<li><b>"Not traced" is not a removal.</b> The record stops because the Ledger could not follow the commitment further.</li>
</ul>
<p class="note"><a href="about.html#limits">All known limits</a></p>
</div>
</div>

<h2>Use the data</h2>
<div class="grid g3">
<div class="card"><h3 style="margin-top:0">Cite a commitment</h3><p class="small muted">Use its ID. It never changes and is never reused.</p>
<p><span class="mono">{DEMO_ID}</span> <button class="btn sm" type="button" data-copy="{config.SITE_URL}/c/{DEMO_ID}.html">Copy link</button></p></div>
<div class="card"><h3 style="margin-top:0">Download</h3><p class="small muted">One JSON file with every commitment and every history entry.</p>
<p><a class="btn sm" href="ledger.json">ledger.json</a> <a class="btn sm" href="schema.json">schema.json</a></p></div>
<div class="card"><h3 style="margin-top:0">Follow changes</h3><p class="small muted">One feed item for each recorded change, with stable identifiers.</p>
<p><a class="btn sm" href="feed.xml">RSS feed</a> <a class="btn sm" href="{config.REPO_URL}">GitHub</a></p></div>
</div>
<script>
// Links made before the redesign pointed filters at this page. Send them to the browse page.
(function(){{var p=new URLSearchParams(location.search);if(['lab','current','event','topic','q','tag'].some(function(k){{return p.get(k)}}))location.replace('browse.html'+location.search)}})();
</script>
"""
    return _page(f"{config.SITE_TITLE}: AI safety framework commitments, version by version", body, "",
                 "An open ledger of AI developer safety-framework commitments. Each has a permanent ID, a history across versions, and hashed sources.")


def _options(values, labels=None):
    return "".join(f'<option value="{E(v)}">{E((labels or {}).get(v, v))}</option>' for v in values)


def render_browse(site):
    items = site.items
    order = {"removed": 0, "relocated": 1, "active": 2, "merged": 3, "not_traced": 4}
    severity = {"removed": 0, "weakened": 1, "relocated": 1, "strengthened": 2, "added": 3, "kept": 4, "baseline": 5}
    lab_order = {lab: n for n, lab in enumerate(site.labs)}
    topic_order = {t: n for n, t in enumerate(sorted(config.TOPIC_LABEL, key=config.TOPIC_LABEL.get))}

    def key(c):
        worst = min(severity[h["status"]] for h in c["history"])
        return (order[c["current_status"]], worst, c["lab"], c["id"])

    by_dev = {c["id"]: n for n, c in enumerate(sorted(items, key=lambda c: (lab_order[c["lab"]], topic_order[c["topic"]], c["id"])))}
    rows = []
    for n, c in enumerate(sorted(items, key=key)):
        changes = [h for h in c["history"] if h["status"] in CHANGES]
        statuses = sorted({h["status"] for h in c["history"]})
        last = max((site.versions[h["version_id"]]["publication_date"] for h in changes), default="0000-00-00").replace("-", "")
        rows.append(
            f'<li data-lab="{c["lab"]}" data-current="{c["current_status"]}" data-topic="{c["topic"]}" '
            f'data-tags="{" ".join(c["tags"])}" data-events="{" ".join(statuses)}" data-o="{n}" data-od="{by_dev[c["id"]]}" '
            f'data-last="{last}" data-n="{len(changes)}" data-text="{E((c["text"] + " " + c["id"] + " " + site.labs[c["lab"]]).lower())}">'
            f'<a class="row" href="c/{c["id"]}.html"><div class="rmeta">{_badge(c["current_status"])}'
            f'<span>{E(site.labs[c["lab"]])}</span><span>{E(config.TOPIC_LABEL[c["topic"]])}</span>'
            f'<span class="mono">{c["id"]}</span>{_cells(site, c)}</div>'
            f'<div class="rtext">{E(_short(c["text"], 240))}</div></a></li>')
    tags = sorted({t for c in items for t in c["tags"]})
    chips = "".join(f'<button type="button" class="chip" data-tag="{E(t)}" aria-pressed="false">{E(t)}</button>' for t in tags)
    body = f"""
<p class="crumbs"><a href="index.html">Home</a><span aria-hidden="true">›</span><span>Browse</span></p>
<h1>Browse the commitments</h1>
<p class="sub">{len(items)} commitments. Search the wording, or narrow by developer, status and topic. The address of this page records your filters, so you can share a view.</p>
<div class="filters">
<div class="wide"><label class="f" for="f-q">Search wording, ID or developer</label><input id="f-q" type="search" placeholder="for example: benchmark, or xai-governance-673f" autocomplete="off"></div>
<div><label class="f" for="f-lab">Developer</label><select id="f-lab"><option value="">All developers</option>{_options(list(site.labs), site.labs)}</select></div>
<div><label class="f" for="f-current">Status now</label><select id="f-current"><option value="">Any status</option>{_options(["active", "removed", "relocated", "merged", "not_traced"], config.STATUS_LABEL)}</select></div>
<div><label class="f" for="f-event">Was at some point</label><select id="f-event"><option value="">Anything</option>{_options(["weakened", "strengthened", "removed", "added", "relocated"], config.STATUS_LABEL)}</select></div>
<div><label class="f" for="f-topic">Topic</label><select id="f-topic"><option value="">All topics</option>{_options(sorted(config.TOPIC_LABEL, key=config.TOPIC_LABEL.get), config.TOPIC_LABEL)}</select></div>
</div>
<details class="more" id="tagbox"><summary>Keyword tags ({len(tags)})</summary>
<div class="chips" id="tags" role="group" aria-label="Keyword tags" style="margin:8px 0">{chips}</div>
<p class="small muted" style="margin:0 0 8px">Tags come from fixed keyword rules, not from a model. They can miss or over-match.</p></details>
<div class="resultbar"><span id="count" aria-live="polite"><b>{len(items)}</b> of {len(items)} commitments</span>
<button class="btn sm" type="button" id="reset" hidden>Clear filters</button>
<span class="right"><label for="f-sort">Sort</label><select id="f-sort">
<option value="serious">Most serious change first</option><option value="recent">Most recently changed</option>
<option value="changes">Most changes</option><option value="developer">Developer, then topic</option></select></span></div>
{_legend()}
<ul class="rows" id="rows">{"".join(rows)}</ul>
<p class="empty" id="empty" hidden>No commitment matches these filters. Clear a filter, or search for a shorter word.</p>
<noscript><p class="note">Filters need JavaScript. Without it this page lists every commitment.</p></noscript>
"""
    return _page(f"Browse commitments · {config.SITE_TITLE}", body, "",
                 f"Search and filter {len(items)} AI safety framework commitments by developer, status, topic and wording.", "browse")


def _pairs_text(site, pairs):
    return ", ".join(f'{E(_vname(site.versions[a]))} → {E(_vname(site.versions[b]))}' for a, b in pairs) or "None"


STRIP_LABEL = {
    "kept": "Present, no material change", "added": "Added", "strengthened": "Strengthened", "weakened": "Weakened",
    "removed": "Removed", "relocated": "Relocated to another document", "merged": "Merged into another row",
    "not_traced": "Not traced after this version",
}
STRIP_RANK = {"removed": 0, "relocated": 1, "weakened": 2, "merged": 3, "kept": 4, "baseline": 4, "strengthened": 5, "added": 6}


def _strip_chart(site, lab):
    """The strip figure of the paper, as links. One row for each commitment, one column for each version.

    Same order and colours as paper/make_figures.py strip(). Each cell opens that entry in the commitment's history.
    """
    name = site.labs[lab]
    items = list(site.by_lab[lab])
    versions = site.lab_versions[lab]
    firsts = {c["first_version_id"] for c in items}
    start = min(n for n, v in enumerate(versions) if v["version_id"] in firsts)
    skipped, versions = versions[:start], versions[start:]
    vids = [v["version_id"] for v in versions]

    def key(c):
        end = 0 if c["current_status"] in ("removed", "relocated") else 1 if c["current_status"] in ("not_traced", "merged") else 2
        return (vids.index(c["first_version_id"]), end, vids.index(c["last_version_id"]), STRIP_RANK.get(c["history"][-1]["status"], 4))

    items.sort(key=key)
    used = set()
    rows = []
    for c in items:
        by_version = {h["version_id"]: h for h in c["history"]}
        after = vids.index(c["last_version_id"]) + 1
        text = E(_short(c["text"], 150))
        cells = []
        for n, v in enumerate(versions):
            h = by_version.get(v["version_id"])
            if h:
                kind = "kept" if h["status"] in ("baseline", "kept") else h["status"]
                label = config.STATUS_LABEL[h["status"]]
                href = f'../c/{c["id"]}.html#{E(v["version_id"])}'
            elif n == after and c["current_status"] in ("merged", "not_traced"):
                kind = c["current_status"]
                label = STRIP_LABEL[kind]
                href = f'../c/{c["id"]}.html'
            else:
                cells.append("<i></i>")
                continue
            used.add(kind)
            tip = f'{c["id"]} · {_vname(v)} · {label}'
            cells.append(f'<a class="b-{kind}" href="{href}" title="{E(tip)}" aria-label="{E(tip)}" data-t="{text}"></a>')
        short_id = c["id"][len(lab) + 1:] if c["id"].startswith(lab + "-") else c["id"]
        rows.append(f'<div class="sc-row"><a class="sc-id" href="../c/{c["id"]}.html" title="{text}" data-t="{text}" '
                    f'aria-label="{c["id"]}">{E(short_id)}</a>{"".join(cells)}</div>')
    heads = "".join(f'<a href="../v/{E(v["version_id"])}.html" title="{E(_vname(v))}, {_date(v["publication_date"])}: everything that changed">'
                    f'{E(_vlabel(v))}</a>' for v in versions)
    legend = "".join(f'<span><i class="b-{k}"></i>{E(STRIP_LABEL[k])}</span>' for k in STRIP_LABEL if k in used)
    note = ""
    if skipped:
        names = ", ".join(E(_vname(v)) for v in skipped)
        note = f' {"Version" if len(skipped) == 1 else "Versions"} {names} {"is" if len(skipped) == 1 else "are"} not traced, and not shown.'
    return f"""<h2 id="strip">Strip chart</h2>
<p class="sub">{len(items)} {E(name)} commitments across {_plural(len(versions), "version")}. One row is one commitment, in order of first appearance. One bar is one version, oldest on the left. Select a bar to open that entry, or a version name to see everything that changed in it.{note}</p>
<div class="sc-legend" role="note" aria-label="Legend">{legend}</div>
<div class="sc" style="--n:{len(versions)}">
<div class="sc-row sc-head"><span class="sc-id">ID</span>{heads}</div>
<p class="sc-info" id="sc-info" aria-live="polite">Point at a bar, or move to it with the Tab key, to read the commitment here.</p>
{"".join(rows)}
</div>
"""


def render_developer(site, lab):
    name = site.labs[lab]
    mine = site.by_lab[lab]
    versions = site.lab_versions[lab]
    cov = site.cov[lab]
    now = collections.Counter(c["current_status"] for c in mine)
    events = collections.Counter(h["status"] for c in mine for h in c["history"] if h["status"] in CHANGES)
    docs = []
    for v in versions:
        if v["document"] not in docs:
            docs.append(v["document"])
    earlier = (" Earlier names: " + "; ".join(E(d) for d in docs[:-1]) + ".") if len(docs) > 1 else ""
    stopped = [c for c in mine if c["current_status"] == "not_traced"]
    overlap = sum(1 for c in stopped if c.get("related_ids"))
    notes = [f'<li><b>Traced by the source study (Zhu, 2026):</b> {_pairs_text(site, cov["traced_pairs"])}.</li>']
    if cov.get("extended_pairs"):
        notes.append(f'<li><b>Traced by the Ledger</b> (text matching and a language model, with checks by one person): {_pairs_text(site, cov["extended_pairs"])}.</li>')
    if cov["untraced_pairs"]:
        notes.append(f'<li><b>Not traced:</b> {_pairs_text(site, cov["untraced_pairs"])}.</li>')
    if stopped:
        text = f'<li><b>{_plural(len(stopped), "history", "histories")} stop before the last version</b> and show as "Not traced". This is not a removal.'
        if overlap:
            text += f' {overlap} of them overlap a later history that could not be joined one to one, so the total of {len(mine)} may count some commitments twice.'
        notes.append(text + "</li>")
    last = site.versions[cov["last_traced_version_id"]]
    which = (f'{E(_vname(last))}</b>, published {_date(last["publication_date"])},' if _vname(last) != _date(last["publication_date"])
             else f'the version of {_date(last["publication_date"])}</b>,')
    notes.append(f'<li><b>"In force" means in {which} the last version the Ledger traces for {E(name)}.</li>')
    heads = "".join(f'<span title="{E(_vname(v))}, {_date(v["publication_date"])}">{E(_vlabel(v))}</span>' for v in versions)
    first_order = {v["version_id"]: n for n, v in enumerate(versions)}
    groups = []
    for topic in sorted(config.TOPIC_LABEL, key=config.TOPIC_LABEL.get):
        rows = sorted((c for c in mine if c["topic"] == topic), key=lambda c: (first_order[c["first_version_id"]], c["id"]))
        if not rows:
            continue
        body = "".join(
            f'<a class="grow{" gone" if c["current_status"] in ("removed", "relocated") else ""}" href="../c/{c["id"]}.html" title="{c["id"]}">'
            f'<span class="gt">{E(_short(c["text"], 170))}</span>{_cells(site, c)}</a>' for c in rows)
        groups.append(f'<h3><span>{E(config.TOPIC_LABEL[topic])}</span><span>{len(rows)}</span></h3>{body}')
    others = "".join(f'<a class="chip" href="{other}.html">{E(n)}</a>' for other, n in site.labs.items() if other != lab)
    body = f"""
<p class="crumbs"><a href="../index.html">Home</a><span aria-hidden="true">›</span><a href="../index.html#developers">Developers</a><span aria-hidden="true">›</span><span>{E(name)}</span></p>
<p class="eyebrow">Developer</p>
<h1>{E(name)}</h1>
<p class="lede">{len(mine)} commitments across {_plural(len(versions), "version")} of the {E(docs[-1])}, from {_date(versions[0]["publication_date"])} to {_date(versions[-1]["publication_date"])}.{earlier}</p>
<div class="stats">
<div><b>{len(mine)}</b><span>commitments</span></div>
<div><b>{now.get("active", 0)}</b><span>in force in the last traced version</span></div>
<div><b>{now.get("removed", 0)}</b><span>removed</span></div>
<div><b>{events.get("weakened", 0)}</b><span>weakenings recorded</span></div>
<div><b>{events.get("strengthened", 0)}</b><span>strengthenings recorded</span></div>
</div>
<p style="margin-top:14px"><a class="btn sm" href="../browse.html?lab={lab}">Search {E(name)} commitments</a>
<a class="btn sm" href="#strip">Strip chart</a>
<a class="btn sm" href="../browse.html?lab={lab}&amp;current=removed">Removed</a> <a class="btn sm" href="../browse.html?lab={lab}&amp;event=weakened">Weakened at some point</a></p>

<h2>Versions</h2>
<p class="sub">Open a version to see everything that changed in it.</p>
<ul class="rows">{"".join(_version_row(site, v, "../", False) for v in reversed(versions))}</ul>

<div class="callout"><h3>Coverage for {E(name)}</h3><ul>{"".join(notes)}</ul></div>

{_strip_chart(site, lab)}
<h2 id="topics">Every commitment, by topic</h2>
<p class="sub">The same data with the wording, grouped by topic. One square is one version, oldest on the left. Select a row to open its history.</p>
{_legend()}
<div class="sheet"><div class="sheet-head"><span class="small muted">Commitment</span><span class="cols" aria-hidden="true">{heads}</span></div>{"".join(groups)}</div>
<h2>Other developers</h2>
<div class="chips">{others}</div>
"""
    return _page(f"{name} · {config.SITE_TITLE}", body, "../",
                 f"{name}: {len(mine)} safety framework commitments across {len(versions)} versions, with what changed in each version.", "developers")


def _change_text(prev, h):
    """The wording of one history entry, with the change from the entry before marked."""
    before = prev["quote"] if prev and prev["quote"] else None
    if h["quote"] is None:
        out = f'<div class="quote gone-text">{E(before)}</div>' if before else ""
        if h["status"] == "relocated":
            return out + ('<p class="note"><b>Relocated.</b> The framework no longer has this text. The source coding records a counterpart '
                          'in a companion document or a non-binding section.</p>')
        return out + '<p class="note"><b>No counterpart in this version.</b></p>'
    if before and before != h["quote"]:
        ratio, marked = _diff(before, h["quote"])
        if ratio >= 0.5:
            return f'<div class="quote">{marked}</div>'
        return (f'<div class="quote">{E(h["quote"])}</div>'
                f'<p class="note"><b>Before:</b> <span class="gone-text">{E(_short(before, 400))}</span></p>')
    return f'<div class="quote">{E(h["quote"])}</div>'


def _model_note(h):
    """What a person checked, for an entry that a model coded. Empty for other entries."""
    if h.get("coded_by") != "model":
        return ""
    check = h.get("human_check")
    if h["status"] == "added" and check != "adjudicated":
        runs = h.get("found_by_runs", 1)
        return (f'<p class="note"><b>Candidate for a new commitment.</b> {"Two runs" if runs == 2 else "One of two runs"} of a language model found this passage '
                'and found no counterpart in the version before. <b>No person confirmed it. This entry needs review.</b></p>')
    if check == "adjudicated":
        tail = " One person then reviewed it with the model's reasons in view (not blind). The status here is his final code."
    elif check and check.startswith("adjudicated:"):
        tail = " <b>One person took a second look and did not give a code (" + E(check.split(":")[1].replace("_", " ")) + "). This entry needs review.</b>"
    elif check == "agrees":
        tail = " One person checked it blind and gave the same code."
    elif check and check.startswith("disagrees:"):
        tail = f' <b>One person checked it blind and coded it "{E(check.split(":")[1])}". Not resolved. This entry needs review.</b>'
    elif check == "not_same_thing":
        tail = " <b>One person checked it blind and did not accept that the two texts are the same commitment. This entry needs review.</b>"
    elif check == "cannot_tell":
        tail = " <b>One person checked it blind and could not decide from the extracted text. This entry needs review.</b>"
    else:
        tail = " No person checked it." + (" <b>The two runs did not agree. This entry needs review.</b>" if h.get("needs_review") else "")
    what = ("found no counterpart for this commitment" if h["status"] == "removed"
            else ("found this passage" if h["status"] == "added" else "found this counterpart and coded this change"))
    return f'<p class="note"><b>Coded by a language model.</b> Two runs {what}.{tail}</p>'


def _why(h, account=True):
    out = ""
    if h.get("mixed"):
        out += '<p class="note"><b>Mixed change.</b> Stronger in one way and weaker in another. The status is then Weakened.</p>'
    if h.get("rationale") and h["status"] not in ("kept", "baseline"):
        who = "language model" if h.get("coded_by") == "model" else "source coding"
        out += f'<p class="note"><b>Why this status ({who}):</b> {E(h["rationale"])}</p>'
    if account and h.get("disclosure") in config.DISCLOSURE_LABEL and h["status"] in CHANGES:
        out += f'<p class="note"><b>Developer\'s account:</b> {E(config.DISCLOSURE_LABEL[h["disclosure"]])}</p>'
    return out


def _entry_html(site, c, i):
    h = c["history"][i]
    prev = c["history"][i - 1] if i else None
    v = site.versions[h["version_id"]]
    parts = [f'<div class="when"><time datetime="{v["publication_date"]}">{_date(v["publication_date"])}</time>'
             f'{_badge(h["status"])}<span class="doc">{E(v["document"])}'
             + (f', {E(_vname(v))}' if _vname(v) != _date(v["publication_date"]) else "") + '</span></div>',
             _change_text(prev, h)]
    if h["status"] == "kept" and prev and prev["quote"] and h["quote"] and prev["quote"] != h["quote"]:
        parts.append('<p class="note"><b>Kept.</b> The wording changed. No material change to the obligation is recorded.</p>')
    parts.append(_why(h))
    parts.append(_model_note(h))
    if h.get("gap_before"):
        parts.append('<p class="note"><b>Gap.</b> One or more versions before this entry are not traced.</p>')
    later = [r for r in v.get("reuploads", []) if r.get("note")]
    wayback = _wayback(h)
    src = [("Section", E(h["section"]) + (" (heading changed)" if h.get("section_changed") else "")) if h["section"] else None,
           ("Source file", f'<a href="{E(h["source_url"])}">{E(_short(h["source_url"], 80))}</a>'
                           + (f' · <a href="{E(wayback)}">Wayback Machine</a>' if wayback else "")),
           ("SHA-256", f'<span class="mono">{h["sha256"]}</span>'),
           ("Later file", "<br>".join(f'<a href="{E(r["source_url"])}">{E(_short(r["source_url"], 80))}</a> · SHA-256 <span class="mono">{r["sha256"][:16]}…</span><br>{E(r["note"])}' for r in later)) if later else None,
           ("Quote check", "Found in the hashed document" if h.get("quote_verified") else "Not found by the automatic check") if h["quote"] else None,
           ("Decided by", E(CODED_BY[h.get("coded_by", "upstream")])),
           ("Confidence", E(h["confidence"]) + " (grade from the source first pass)") if h.get("confidence") else None,
           ("Source row", f'<span class="mono">{E(h["source_row"])}</span>') if h.get("source_row") else None,
           ("Entry ID", f'<span class="mono">{E(h["event_id"])}</span>')]
    verified = "" if not h["quote"] else (" · quote found in the file" if h.get("quote_verified") else " · quote not found by the automatic check")
    parts.append(
        f'<details class="src"><summary><span>Source and provenance</span><span class="mono">sha256 {h["sha256"][:12]}…</span>'
        f'<span>{E(CODED_BY_SHORT[h.get("coded_by", "upstream")])}{verified}</span></summary><dl>'
        + "".join(f"<dt>{k}</dt><dd>{val}</dd>" for k, val in filter(None, src)) + "</dl></details>")
    parts.append(f'<p class="note"><a href="../v/{E(h["version_id"])}.html">Everything that changed in this version</a></p>')
    return f'<li class="is-{h["status"]}" id="{E(h["version_id"])}"><div class="entry">{"".join(parts)}</div></li>'


def render_commitment(site, c, later=False):
    lab = site.labs[c["lab"]]
    last = c["history"][-1]
    when = _date(site.versions[last["version_id"]]["publication_date"])
    if c["current_status"] == "removed":
        headline = f"Removed on {when}"
    elif c["current_status"] == "relocated":
        headline = f"Relocated on {when}"
    elif c["current_status"] == "merged":
        headline = f'Continues as <a href="{c["merged_into"]}.html" class="mono">{c["merged_into"]}</a>'
    elif c["current_status"] == "active":
        headline = f"In the last traced version, {when}" + (". Later versions are not traced." if later else "")
    else:
        headline = f"Last traced on {when}. This is not a removal: the record stops here."
    tags = "".join(f'<a class="chip" href="../browse.html?tag={E(t)}">{E(t)}</a>' for t in c["tags"])
    ids_note = ""
    if c.get("former_ids"):
        ids_note += '<p class="note"><b>Former ID:</b> ' + ", ".join(f'<span class="mono">{E(i)}</span>' for i in c["former_ids"]) + ". Two histories were joined into this one.</p>"
    if c.get("related_ids"):
        ids_note += '<p class="note"><b>Overlapping text:</b> ' + ", ".join(f'<a class="mono" href="{E(i)}.html">{E(i)}</a>' for i in c["related_ids"]) + ". These can be the same promise.</p>"
    url = f'{config.SITE_URL}/c/{c["id"]}.html'
    changes = collections.Counter(h["status"] for h in c["history"] if h["status"] in CHANGES)
    body = f"""
<p class="crumbs"><a href="../index.html">Home</a><span aria-hidden="true">›</span><a href="../d/{c["lab"]}.html">{E(lab)}</a><span aria-hidden="true">›</span><a href="../browse.html?lab={c["lab"]}&amp;topic={c["topic"]}">{E(config.TOPIC_LABEL[c["topic"]])}</a></p>
<p class="eyebrow">Commitment</p>
<h1 class="quote ctitle">{E(c["text"])}</h1>
<div class="idline">{_badge(c["current_status"])}<span>{headline}</span></div>
<div class="card">
<dl class="facts">
<dt>Permanent ID</dt><dd><span class="mono" id="cid">{c["id"]}</span> <button class="btn sm" type="button" data-copy="{c["id"]}">Copy ID</button> <button class="btn sm" type="button" data-copy="{url}">Copy link</button></dd>
<dt>Developer</dt><dd><a href="../d/{c["lab"]}.html">{E(lab)}</a></dd>
<dt>Topic</dt><dd>{E(config.TOPIC_LABEL[c["topic"]])}</dd>
<dt>Changes</dt><dd><span class="nums">{_count_chips(changes) or '<span class="muted">No change recorded</span>'}</span></dd>
{"<dt>Tags</dt><dd><span class='chips'>" + tags + "</span></dd>" if tags else ""}
</dl>
{ids_note}
<p class="eyebrow" style="margin:16px 0 0">Version by version</p>
{_seen(site, c, "../")}
</div>
<h2>History, oldest first</h2>
<ol class="timeline">{"".join(_entry_html(site, c, i) for i in range(len(c["history"])))}</ol>
<p class="note">Statuses are a reference, not ground truth. See <a href="../about.html#limits">method and limits</a>.</p>
"""
    title = f'{_short(c["text"], 70)} · {lab} · {config.SITE_TITLE}'
    return _page(title, body, "../", f'{lab} commitment {c["id"]}: {_short(c["text"], 140)}', "browse")


def render_version(site, v):
    vid = v["version_id"]
    lab, name = v["lab"], site.labs[v["lab"]]
    before, after = site.previous(vid)
    traced = site.traced_by(vid)
    counts = site.counts(vid)
    entries = site.at[vid]
    title = f'{name}: {v["document"]}' + (f', {_vname(v)}' if _vname(v) != _date(v["publication_date"]) else f', {_date(v["publication_date"])}')
    sections, jump = [], []
    kinds = {c["history"][i].get("disclosure") for c, i in entries
             if c["history"][i]["status"] in CHANGES and c["history"][i].get("disclosure") in DISCLOSURE_SHORT}
    each = len(kinds) > 1  # say it on each change only when the changes differ
    if traced == "first":
        lede = f'The first {E(name)} version in the Ledger. {_plural(counts.get("baseline", 0), "commitment")} first seen here. No change is claimed for a first version.'
    elif traced == "untraced":
        lede = f'The Ledger does not trace the change from {E(_vname(before))} to this version.'
    else:
        bits = [f'{counts[s]} {config.STATUS_LABEL[s].lower()}' for s in CHANGE_ORDER if counts.get(s)]
        lede = (f'Compared with {E(_vname(before))}: ' + (", ".join(bits) if bits else "no change recorded")
                + f'. {_plural(counts.get("kept", 0), "commitment")} kept.')
    for status in CHANGE_ORDER:
        rows = sorted(((c, i) for c, i in entries if c["history"][i]["status"] == status), key=lambda r: (r[0]["topic"], r[0]["id"]))
        if not rows:
            continue
        jump.append(f'<a class="chip" href="#{status}">{E(config.STATUS_LABEL[status])} ({len(rows)})</a>')
        cards = []
        for c, i in rows:
            h = c["history"][i]
            prev = c["history"][i - 1] if i else None
            model = '<span class="tag-model">coded by a language model</span>' if h.get("coded_by") == "model" else ""
            cards.append(
                f'<article class="chg is-{status}"><div class="chg-head">{_badge(status)}<a class="mono" href="../c/{c["id"]}.html#{E(vid)}">{c["id"]}</a>'
                f'<span>{E(config.TOPIC_LABEL[c["topic"]])}</span>{model}</div>{_change_text(prev, h)}{_why(h, each)}{_model_note(h)}</article>')
        sections.append(f'<h2 id="{status}">{E(config.STATUS_LABEL[status])} <span class="muted" style="font-weight:400">{len(rows)}</span></h2>'
                        f'<p class="sub">{E(STATUS_MEANING[status])}</p><div class="stack">{"".join(cards)}</div>')
    kept = [(c, i) for c, i in entries if c["history"][i]["status"] == "kept"]
    kept_text = sum(1 for c, i in kept if c["history"][i].get("coded_by") == "text_match")
    notes = []
    if kept:
        how = f' {kept_text} were carried by text match: the same words are in this version.' if kept_text else ""
        notes.append(f'<li><b>{_plural(len(kept), "commitment")} kept.</b>{how} They are not listed here. See the <a href="../d/{lab}.html">{E(name)} overview</a>.</li>')
    if traced == "ledger":
        notes.append('<li><b>The Ledger traced this version itself</b>, with text matching and a language model, with checks by one person. '
                     'The source study does not cover it.</li>')
        if not counts.get("added"):
            notes.append('<li><b>New commitments are not detected for this version.</b> The method used here follows existing commitments only.</li>')
        elif any(c["history"][i].get("coded_by") == "model" for c, i in entries if c["history"][i]["status"] == "added"):
            notes.append('<li><b>The list of new commitments is a lower bound.</b> In a test on four other version pairs, the same step found 26 of 34 additions.</li>')
    elif traced == "source":
        notes.append('<li><b>Traced by the source study</b> (Zhu, 2026): a language model first pass, adjudicated by that study\'s author.</li>')
    disclosure = collections.Counter(c["history"][i].get("disclosure") for c, i in entries
                                     if c["history"][i]["status"] in CHANGES and c["history"][i].get("disclosure") in DISCLOSURE_SHORT)
    account = ""
    if disclosure:
        if set(disclosure) == {"no_account"}:
            account = "The developer published no account of this revision."
        else:
            account = "; ".join(f"{disclosure[k]} {DISCLOSURE_SHORT[k].lower()}" for k in ("announced", "partly_announced", "silent", "no_account") if disclosure.get(k)) + "."
    wayback = _wayback(v)
    later = [r for r in v.get("reuploads", []) if r.get("note")]
    facts = [("Published", f'<time datetime="{v["publication_date"]}">{_date(v["publication_date"])}</time>'),
             ("Document", E(v["document"]) + (f', version {E(v["label"])}' if _vname(v) == v["label"] else "")),
             ("Compared with", f'<a href="{E(before["version_id"])}.html">{E(_vname(before))}</a>'
              + (f', {_date(before["publication_date"])}' if _vname(before) != _date(before["publication_date"]) else "")) if before else None,
             ("Developer's account", E(account[0].upper() + account[1:])
              + ('' if set(disclosure) == {"no_account"} else ' <span class="muted">Counts are of the material changes recorded.</span>')) if account else None,
             ("Source file", f'<a href="{E(v["source_url"])}">{E(_short(v["source_url"], 80))}</a>' + (f' · <a href="{E(wayback)}">Wayback Machine</a>' if wayback else "")),
             ("SHA-256", f'<span class="mono">{v["sha256"]}</span> <button class="btn sm" type="button" data-copy="{v["sha256"]}">Copy</button>'),
             ("Later file", "<br>".join(f'<a href="{E(r["source_url"])}">{E(_short(r["source_url"], 80))}</a> · SHA-256 <span class="mono">{r["sha256"][:16]}…</span><br>{E(r["note"])}' for r in later)) if later else None]
    pager = ((f'<a class="btn" href="{E(before["version_id"])}.html">← {E(_vname(before))}</a>' if before else "<span></span>")
             + (f'<a class="btn" href="{E(after["version_id"])}.html">{E(_vname(after))} →</a>' if after else "<span></span>"))
    body = f"""
<p class="crumbs"><a href="../index.html">Home</a><span aria-hidden="true">›</span><a href="../d/{lab}.html">{E(name)}</a><span aria-hidden="true">›</span><span>{E(_vname(v))}</span></p>
<p class="eyebrow">{E(name)} · framework version</p>
<h1>{E(v["document"])}, {E(_vname(v))}</h1>
<p class="lede">{lede}</p>
<div class="card"><dl class="facts">{"".join(f"<dt>{k}</dt><dd>{val}</dd>" for k, val in filter(None, facts))}</dl></div>
{'<div class="jump">' + "".join(jump) + "</div>" if jump else ""}
{'<div class="callout"><ul>' + "".join(notes) + "</ul></div>" if notes else ""}
{"".join(sections)}
<div class="pager">{pager}</div>
"""
    return _page(f"{title} · {config.SITE_TITLE}", body, "../",
                 f'{name}, {v["document"]}, {_date(v["publication_date"])}: what changed in this version of the safety framework.', "revisions")


def render_revisions(site):
    versions = sorted(site.ledger["versions"], key=lambda v: (v["publication_date"], v["version_id"]), reverse=True)
    out, year = [], None
    for v in versions:
        if v["publication_date"][:4] != year:
            if year:
                out.append("</ul>")
            year = v["publication_date"][:4]
            out.append(f'<h2>{year}</h2><ul class="rows">')
        out.append(_version_row(site, v))
    out.append("</ul>")
    devs = "".join(f'<a class="chip" href="d/{lab}.html">{E(n)}</a>' for lab, n in site.labs.items())
    body = f"""
<p class="crumbs"><a href="index.html">Home</a><span aria-hidden="true">›</span><span>Revisions</span></p>
<h1>Every framework version, newest first</h1>
<p class="sub">{len(versions)} versions from {len(site.labs)} developers. Open one to see what was removed, weakened, strengthened and added in it.
For changes as a feed, use the <a href="feed.xml">RSS feed</a>.</p>
<div class="chips" style="margin-bottom:6px"><span class="small muted" style="align-self:center">By developer:</span>{devs}</div>
{"".join(out)}
"""
    return _page(f"Revisions · {config.SITE_TITLE}", body, "",
                 f"All {len(versions)} framework versions in the Commitment Ledger, with the changes recorded in each.", "revisions")


def render_about(site):
    items = site.items
    entries = [h for c in items for h in c["history"]]
    coded = collections.Counter(h.get("coded_by", "upstream") for h in entries)
    checked = sum(1 for h in entries if h.get("coded_by") == "model" and h.get("human_check"))
    quotes = [h for h in entries if h["quote"]]
    verified = sum(1 for h in quotes if h.get("quote_verified"))
    now = collections.Counter(c["current_status"] for c in items)
    status_rows = "".join(f'<tr><td>{_badge(s)}</td><td>{E(STATUS_MEANING[s])}</td></tr>' for s in CELL_ORDER)
    current_rows = "".join(f'<tr><td>{_badge(s)}</td><td class="n">{now.get(s, 0)}</td><td>{E(CURRENT_MEANING[s])}</td></tr>'
                           for s in ("active", "removed", "relocated", "merged", "not_traced"))
    coded_rows = "".join(f'<tr><td>{E(CODED_BY_SHORT[k])}</td><td class="n">{coded.get(k, 0):,}</td><td>{E(text)}</td></tr>' for k, text in (
        ("upstream", "The coding of the Silent Revision study (Zhu, 2026): a first pass by a Claude model, adjudicated by that study's author. No independent human coder."),
        ("text_match", "The same words are in this version. The status is Kept. No judgement by a person or a model."),
        ("model", f"A language model found the counterpart and coded the change, in two runs. One person checked {checked} of these entries. Each entry says whether it was checked.")))
    cov_rows = []
    for lab, name in site.labs.items():
        cov = site.cov[lab]
        last = site.versions[cov["last_traced_version_id"]]
        cov_rows.append(f'<tr><th scope="row"><a href="d/{lab}.html">{E(name)}</a></th><td class="n">{len(site.by_lab[lab])}</td><td class="n">{len(site.lab_versions[lab])}</td>'
                        f'<td>{_pairs_text(site, cov["traced_pairs"])}</td><td>{_pairs_text(site, cov.get("extended_pairs", []))}</td>'
                        f'<td>{_pairs_text(site, cov["untraced_pairs"])}</td><td>{E(_vname(last))}, {_date(last["publication_date"])}</td></tr>')
    stopped = [c for c in items if c["current_status"] == "not_traced"]
    overlap = sum(1 for c in stopped if c.get("related_ids"))
    joined = sum(1 for c in items if c.get("former_ids"))
    disclosure_rows = "".join(f"<tr><td>{E(DISCLOSURE_SHORT[k])}</td><td>{E(config.DISCLOSURE_LABEL[k])}</td></tr>" for k in ("announced", "partly_announced", "silent", "no_account"))
    val = f"{config.REPO_URL}/blob/main/validation.md"
    body = f"""
<p class="crumbs"><a href="index.html">Home</a><span aria-hidden="true">›</span><span>About</span></p>
<h1>Method, definitions and limits</h1>
<p class="lede">What the Ledger records, where each entry comes from, how far to trust it, and how to reuse it.</p>
<div class="toc"><a class="chip" href="#what">What it is</a><a class="chip" href="#ids">Identifiers</a><a class="chip" href="#statuses">Statuses</a><a class="chip" href="#who">Who decided</a>
<a class="chip" href="#coverage">Coverage</a><a class="chip" href="#checks">Checks</a><a class="chip" href="#limits">Limits</a><a class="chip" href="#reuse">Reuse</a></div>
<div class="prose">

<h2 id="what">What it is</h2>
<p>AI developers publish safety frameworks: documents that set capability thresholds, the evaluations used to test against them, and what the developer will do when a threshold is crossed.
Developers revise these documents. The Ledger follows each commitment through those revisions.</p>
<p>A <b>commitment</b> is a statement in a safety framework in which the developer commits itself to a practice. Admissions and descriptions are not commitments, and are not in the Ledger.</p>
<p>The Ledger holds {len(items)} commitments from {len(site.labs)} developers across {len(site.ledger["versions"])} framework versions, with {site.n_changes} recorded changes.
It does not code the frameworks afresh. The seed data is the coding of the <a href="{config.CORPUS_REPO}">Frontier Safety Framework Corpus</a>
(Zhu, 2026, <a href="https://arxiv.org/abs/2609.08789">Silent Revision</a>). That study gives a commitment a new row in each pair of versions. The Ledger connects those rows into one history and gives it one ID.</p>

<h2 id="ids">Identifiers</h2>
<p>A commitment ID has the form <span class="mono">developer-topic-hash</span>, for example <a class="mono" href="c/{DEMO_ID}.html">{DEMO_ID}</a>.</p>
<ul>
<li>The developer part does not change when a company changes its name.</li>
<li>The topic is the topic at first appearance.</li>
<li>The hash is the first 4 hexadecimal characters of the SHA-256 of the developer, the first version and the normalised first quote. If two IDs collide, the later one takes one more character.</li>
<li>The ID is assigned at first appearance. A later change of wording or topic does not change it. An ID is never reused.</li>
<li>When two histories are joined, the older ID continues. The other becomes a former ID, and its page points to the new one. {joined} histories were joined this way on 15 November 2026.</li>
</ul>
<p>Each history entry also has an ID: <span class="mono">commitment-id@version-id</span>. It is the identifier of the matching item in the RSS feed.</p>

<h2 id="statuses">Statuses</h2>
<p>A status on a history entry describes the change from the version before.</p>
<div class="scroll"><table><thead><tr><th>Status</th><th>Meaning</th></tr></thead><tbody>{status_rows}</tbody></table></div>
<p>The source study judges a change on six dimensions: scope, threshold or trigger, actor, obligation strength, disclosure scope, and consequence.
"Relocated" does not mean "moved to a different section" of the same document.</p>
<h3>Where a commitment stands now</h3>
<div class="scroll"><table><thead><tr><th>Status now</th><th>Commitments</th><th>Meaning</th></tr></thead><tbody>{current_rows}</tbody></table></div>
<h3>The developer's own account</h3>
<p>For each material change, the source study records whether the developer's own account of the revision identifies it.</p>
<div class="scroll"><table><thead><tr><th>Label</th><th>Meaning</th></tr></thead><tbody>{disclosure_rows}</tbody></table></div>

<h2 id="who">Who decided each entry</h2>
<p>The Ledger has {len(entries):,} history entries. Each one says who decided it.</p>
<div class="scroll"><table><thead><tr><th>Decided by</th><th>Entries</th><th>What that means</th></tr></thead><tbody>{coded_rows}</tbody></table></div>
<p>Histories are connected across versions by text: a note in the source data that names the earlier row, then identical text after normalisation, then a similarity ratio of 0.9 or more.
For the version pairs that the Ledger traced itself, a language model found the counterpart. A commitment that was fully rewritten gets a new ID.</p>

<h2 id="coverage">Coverage</h2>
<div class="scroll"><table><thead><tr><th>Developer</th><th>Commitments</th><th>Versions</th><th>Traced by the source study</th><th>Traced by the Ledger</th><th>Not traced</th><th>Last traced version</th></tr></thead>
<tbody>{"".join(cov_rows)}</tbody></table></div>
<p>The source study also traced Microsoft and Naver. They are not in the Ledger. The newest version in the Ledger is {E(site.labs[site.newest["lab"]])} {E(_vname(site.newest))}, {_date(site.newest["publication_date"])}.</p>

<h2 id="checks">Checks</h2>
<p>Full results, with the test items and model answers: <a href="{val}">validation.md</a>. The language model in every test was Claude Opus 5.5.</p>
<div class="scroll"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
<tr><td>Quotes found in the hashed source document</td><td class="n">{verified:,} of {len(quotes):,}</td></tr>
<tr><td>Direction of change: the model gives the source code for a matched pair</td><td>105 of 120 (88%, Cohen's kappa 0.81)</td></tr>
<tr><td>Stability: a second model run gives the same answer</td><td>113 of 120</td></tr>
<tr><td>Counterpart: the model finds the same counterpart as the source</td><td>48 of 60. Text matching alone: 37 of 60</td></tr>
<tr><td>Counterpart on an incremental revision, and on a full rewrite</td><td>20 of 20, and 10 of 20</td></tr>
<tr><td>New commitments: a model run finds the additions in the source coding</td><td>26 of 34</td></tr>
<tr><td>Blind check by one person of the model-coded Anthropic entries</td><td>Agrees on 34 of 44 decided</td></tr>
<tr><td>Changes listed by Watchtower that are in the Ledger</td><td>xAI, June 2026: 14 of 17. Meta v2.1: 15 of 17</td></tr>
</tbody></table></div>
<p>The model tests are not independent of the source coding. Both sides used Claude models, so agreement between them shows consistency within one model family.</p>

<h2 id="limits">Known limits</h2>
<ul>
<li><b>The statuses are not ground truth.</b> A Claude model made the source study's first pass and that study's author adjudicated it. No other person coded independently.</li>
<li><b>One person checked the Ledger's own tracing.</b> That person is the Ledger's author. For Meta v2.1 he saw the model's answers first.</li>
<li><b>Tracing is weaker at a rewrite.</b> The model found the source's counterpart in 20 of 20 cases on an incremental revision, and in 10 of 20 on a full rewrite.</li>
<li><b>New commitments can be missed.</b> The step that looks for them found 26 of 34 in a test. For Anthropic v2.1, v2.2 and v3.1 to v3.4 the Ledger does not look for new commitments at all.</li>
<li><b>{len(stopped)} histories stop early</b> with the status "Not traced". {overlap} of them overlap a later history that could not be joined one to one, so some commitments may be counted twice.</li>
<li><b>"In force" means "in the last traced version".</b> A new version starts to count only after someone traces it. A daily watcher reports when a framework file or page changes.</li>
<li><b>Frameworks only.</b> Model cards, usage policies and violations are not in the Ledger. <a href="https://www.themidasproject.com/watchtower">Watchtower</a> covers those.</li>
<li><b>Tags are keyword rules.</b> They can miss or over-match.</li>
<li><b>{len(quotes) - verified} quotes were not found</b> by the automatic check against the text extracted from the source file. Each entry says whether its quote was found.</li>
</ul>

<h2 id="reuse">Reuse</h2>
<ul>
<li><b>Data:</b> <a href="ledger.json">ledger.json</a>, described by <a href="schema.json">schema.json</a> and <a href="{config.REPO_URL}/blob/main/SCHEMA.md">SCHEMA.md</a>. Licence: CC BY 4.0. Credit this project and the source corpus.</li>
<li><b>Feed:</b> <a href="feed.xml">feed.xml</a>, one item for each recorded change.</li>
<li><b>Code:</b> <a href="{config.REPO_URL}">GitHub</a>, MIT licence. The site and the feed are built from ledger.json with no language model step.</li>
<li><b>Quotes</b> from framework documents belong to their publishers. The Ledger links to each document by address and SHA-256.</li>
</ul>
<p>Source corpus: {E(config.CORPUS_CITATION)} DOI <a href="https://doi.org/{config.CORPUS_DOI}">{config.CORPUS_DOI}</a>.</p>
<p>The Ledger builds on <a href="https://www.themidasproject.com/watchtower">Watchtower</a> by The Midas Project and extends the idea to a record for each commitment. The Midas Project did not take part in this work and has not endorsed it.
Made for the Apart Research AI x Epistemics sprint, November 2026.</p>
</div>
"""
    return _page(f"Method, definitions and limits · {config.SITE_TITLE}", body, "",
                 "How the Commitment Ledger is built: identifiers, status definitions, who decided each entry, coverage, checks and known limits.", "about")


def render_feed(ledger, labs):
    versions = {v["version_id"]: v for v in ledger["versions"]}
    events = []
    for c in ledger["commitments"]:
        for i, h in enumerate(c["history"]):
            if h["status"] in config.FEED_STATUSES:
                events.append((versions[h["version_id"]]["publication_date"], c, i))
    events.sort(key=lambda e: (e[0], e[1]["id"]), reverse=True)
    items = []
    for date, c, i in events:
        h = c["history"][i]
        prev = c["history"][i - 1] if i else None
        v = versions[h["version_id"]]
        before = prev["quote"] if prev and prev["quote"] else None
        desc = []
        if before and before != h["quote"]:
            desc.append(f"<p><b>Before:</b> {E(before)}</p>")
        desc.append(f"<p><b>Now:</b> {E(h['quote'])}</p>" if h["quote"] else "<p><b>Now:</b> no counterpart in this version.</p>")
        desc.append(f"<p>{E(v['document'])}, version {E(v['label'])}. SHA-256 {h['sha256']}.</p>")
        marker = " (model-coded)" if h.get("coded_by") == "model" else ""
        title = f"{labs[c['lab']]}: {config.STATUS_LABEL[h['status']]}{marker}: {_short(h['quote'] or before or c['text'], 90)}"
        items.append(
            "<item>"
            f"<title>{x(title)}</title>"
            f"<link>{config.SITE_URL}/c/{c['id']}.html#{h['version_id']}</link>"
            f"<guid isPermaLink=\"false\">{x(h['event_id'])}</guid>"
            f"<pubDate>{_rfc822(date)}</pubDate>"
            f"<category>{x(h['status'])}</category><category>{x(c['lab'])}</category>"
            f"<description>{x(''.join(desc))}</description>"
            "</item>")
    newest = events[0][0] if events else "2026-01-01"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        f"<title>{x(config.SITE_TITLE)}: changes</title>"
        f"<link>{config.SITE_URL}/</link>"
        f'<atom:link href="{config.SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>'
        "<description>One item for each change to a safety-framework commitment of a frontier AI developer. GUIDs are stable.</description>"
        "<language>en</language>"
        f"<lastBuildDate>{_rfc822(newest)}</lastBuildDate>"
        + "\n".join(items) + "</channel></rss>\n")


def render(ledger, root, out):
    site = Site(ledger)
    later_untraced = {}
    for cov in ledger["labs"]:
        last = cov["last_traced_version_id"]
        later_untraced[cov["lab"]] = any(a == last for a, _ in cov["untraced_pairs"])
    for folder in ("c", "d", "v", "assets"):
        if os.path.isdir(os.path.join(out, folder)):
            shutil.rmtree(os.path.join(out, folder))
        os.makedirs(os.path.join(out, folder), exist_ok=True)

    def write(name, text):
        with open(os.path.join(out, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    for name in ("site.css", "site.js"):
        shutil.copyfile(os.path.join(assets, name), os.path.join(out, "assets", name))
    write("index.html", render_home(site))
    write("browse.html", render_browse(site))
    write("revisions.html", render_revisions(site))
    write("about.html", render_about(site))
    for lab in site.labs:
        write(os.path.join("d", lab + ".html"), render_developer(site, lab))
    for v in ledger["versions"]:
        write(os.path.join("v", v["version_id"] + ".html"), render_version(site, v))
    for c in ledger["commitments"]:
        write(os.path.join("c", c["id"] + ".html"), render_commitment(site, c, later_untraced[c["lab"]]))
    for c in ledger["commitments"]:
        for old in c.get("former_ids", []):
            body = (f'<p class="eyebrow">Former ID</p><h1>This ID was joined into a different commitment</h1><p class="lede"><span class="mono">{E(old)}</span> is now '
                    f'<a class="mono" href="{c["id"]}.html">{c["id"]}</a>. The Ledger does not use the former ID again.</p>'
                    f'<p><a class="btn primary" href="{c["id"]}.html">Open {c["id"]}</a></p>')
            write(os.path.join("c", old + ".html"), _page(f"{old} · {config.SITE_TITLE}", body, "../", f"Former ID {old}, now {c['id']}."))
    write("feed.xml", render_feed(ledger, site.labs))
    write(".nojekyll", "")
    shutil.copyfile(os.path.join(root, "data", "ledger.json"), os.path.join(out, "ledger.json"))
    shutil.copyfile(os.path.join(root, "schema.json"), os.path.join(out, "schema.json"))
    return len(ledger["commitments"])
