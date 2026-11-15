"""Render the static site and the RSS feed from ledger.json. No dependencies."""
import datetime
import difflib
import email.utils
import html
import json
import os
import shutil
from xml.sax.saxutils import escape as x

from . import config

E = html.escape


def _date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def _rfc822(iso):
    d = datetime.datetime.fromisoformat(iso).replace(tzinfo=datetime.timezone.utc)
    return email.utils.format_datetime(d)


def _short(text, limit=150):
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _badge(status):
    return f'<span class="badge s-{status}">{E(config.STATUS_LABEL[status])}</span>'


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


CSS = """
:root{--bg:#f6f4ee;--panel:#fffdf8;--ink:#1c1b18;--muted:#6a665c;--line:#d9d4c6;--accent:#1f4e79;
--removed:#a4262c;--removed-bg:#fbe9e7;--weakened:#8a5300;--weakened-bg:#fdf0d5;--strengthened:#1d6b3a;--strengthened-bg:#e3f3e6;
--added:#1f4e79;--added-bg:#e4eef8;--kept:#5d5a52;--kept-bg:#ebe8df;--relocated:#5b3a8c;--relocated-bg:#efe8f8}
:root:not([data-theme="light"]){color-scheme:light dark}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15161a;--panel:#1d1f24;--ink:#e9e6df;--muted:#a09c92;--line:#34363d;--accent:#8fbde8;
--removed:#ff9d96;--removed-bg:#4a1f1f;--weakened:#f2c26b;--weakened-bg:#43330f;--strengthened:#8fd6a4;--strengthened-bg:#173722;
--added:#8fbde8;--added-bg:#172f47;--kept:#b5b1a6;--kept-bg:#2b2d33;--relocated:#c9aef2;--relocated-bg:#32244a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;-webkit-text-size-adjust:100%}
a{color:var(--accent)}
.wrap{max-width:860px;margin:0 auto;padding:0 16px 56px}
header.top{border-bottom:1px solid var(--line);padding:14px 0;margin-bottom:22px;display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
header.top a.home{font-weight:700;color:var(--ink);text-decoration:none;letter-spacing:.01em}
header.top nav{margin-left:auto;display:flex;gap:14px;font-size:14px;flex-wrap:wrap}
h1{font-size:26px;line-height:1.25;margin:0 0 8px}
h2{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:30px 0 10px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:62ch}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}
.quote{font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-size:17px;line-height:1.5}
.badge{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:3px;white-space:nowrap;border:1px solid currentColor}
.s-removed{color:var(--removed);background:var(--removed-bg)}
.s-weakened{color:var(--weakened);background:var(--weakened-bg)}
.s-strengthened{color:var(--strengthened);background:var(--strengthened-bg)}
.s-added,.s-active{color:var(--added);background:var(--added-bg)}
.s-kept,.s-baseline,.s-merged,.s-not_traced{color:var(--kept);background:var(--kept-bg)}
.s-relocated{color:var(--relocated);background:var(--relocated-bg)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.chip{font-size:13px;padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--ink);text-decoration:none;cursor:pointer;font-family:inherit}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.filters{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0 6px}
.filters label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;display:block}
.filters select,.filters input{width:100%;font:inherit;font-size:16px;padding:8px;border:1px solid var(--line);border-radius:4px;background:var(--panel);color:var(--ink);margin-top:3px}
.filters .wide{grid-column:1/-1}
.count{color:var(--muted);font-size:14px;margin:12px 0 6px}
ul.rows{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
ul.rows li{border-bottom:1px solid var(--line)}
ul.rows a{display:block;padding:13px 2px;color:inherit;text-decoration:none}
ul.rows a:hover .rtext,ul.rows a:focus .rtext{text-decoration:underline}
.rmeta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-bottom:4px}
.rtext{font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-size:16px;line-height:1.45}
.strip{display:inline-flex;gap:2px;margin-left:auto}
.strip span{width:18px;height:18px;line-height:16px;text-align:center;font-size:12px;font-weight:700;border-radius:2px;border:1px solid currentColor}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px}
ol.timeline{list-style:none;margin:0;padding:0;border-left:2px solid var(--line);margin-left:6px}
ol.timeline>li{position:relative;padding:0 0 26px 20px}
ol.timeline>li::before{content:"";position:absolute;left:-7px;top:6px;width:12px;height:12px;border-radius:50%;background:var(--bg);border:2px solid var(--muted)}
ol.timeline>li.is-removed::before{background:var(--removed);border-color:var(--removed)}
ol.timeline>li.is-weakened::before{background:var(--weakened);border-color:var(--weakened)}
ol.timeline>li.is-strengthened::before{background:var(--strengthened);border-color:var(--strengthened)}
ol.timeline>li.is-added::before{background:var(--added);border-color:var(--added)}
.when{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:8px}
.when time{font-weight:700}
.when .doc{color:var(--muted);font-size:14px}
del{color:var(--removed);background:var(--removed-bg);text-decoration:line-through;padding:0 2px;border-radius:2px}
ins{color:var(--strengthened);background:var(--strengthened-bg);text-decoration:none;padding:0 2px;border-radius:2px}
.gone{color:var(--removed);text-decoration:line-through;text-decoration-thickness:1px}
.note{font-size:14px;color:var(--muted);margin:8px 0 0}
.note b{color:var(--ink);font-weight:600}
dl.src{display:grid;grid-template-columns:max-content 1fr;gap:3px 12px;font-size:13px;margin:10px 0 0;padding-top:10px;border-top:1px dashed var(--line)}
dl.src dt{color:var(--muted)}
dl.src dd{margin:0;min-width:0;overflow-wrap:anywhere}
.idline{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0}
button.copy{font:inherit;font-size:12px;padding:2px 8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:3px;cursor:pointer}
details.cov{margin:0 0 6px;font-size:14px}
details.cov summary{cursor:pointer;color:var(--accent)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;margin-top:8px;font-size:13px;min-width:520px}
th,td{text-align:left;padding:5px 12px 5px 0;border-bottom:1px solid var(--line);vertical-align:top}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.legend{display:flex;gap:6px 12px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin:6px 0 0}
.legend span span{display:inline-block;width:18px;height:18px;line-height:16px;text-align:center;font-weight:700;border:1px solid currentColor;border-radius:2px;margin-right:4px;font-size:12px}
@media (max-width:560px){h1{font-size:22px}.filters{grid-template-columns:1fr 1fr}.strip{margin-left:0;width:100%}.quote{font-size:16px}}
"""


def _page(title, body, root, description):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="alternate" type="application/rss+xml" title="{E(config.SITE_TITLE)} changes" href="{root}feed.xml">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="home" href="{root}index.html">{E(config.SITE_TITLE)}</a>
<nav><a href="{root}ledger.json">ledger.json</a><a href="{root}feed.xml">RSS</a><a href="{config.REPO_URL}/blob/main/SCHEMA.md">Schema</a><a href="{config.REPO_URL}/blob/main/validation.md">Validation</a><a href="{config.REPO_URL}">GitHub</a></nav>
</header>
{body}
<footer>
<p>Seed data derived from the <a href="{config.CORPUS_REPO}">Frontier Safety Framework Corpus</a> by Louis Yiven Zhu
(<a href="https://arxiv.org/abs/2609.08789">Silent Revision, arXiv:2609.08789</a>), CC BY 4.0.
The upstream coding used a language model with one human author. Read each code as a reference, not as ground truth.
Quotes are the property of their publishers.</p>
</footer>
</div>
</body>
</html>
"""


def _strip(history):
    cells = "".join(
        f'<span class="s-{h["status"]}" title="{E(h["version_id"])}: {E(config.STATUS_LABEL[h["status"]])}">{config.STATUS_MARK[h["status"]]}</span>'
        for h in history)
    return f'<span class="strip" aria-hidden="true">{cells}</span>'


def _options(values, labels=None):
    return "".join(f'<option value="{E(v)}">{E((labels or {}).get(v, v))}</option>' for v in values)


def render_index(ledger, labs):
    items = ledger["commitments"]
    order = {"removed": 0, "relocated": 1, "merged": 3, "not_traced": 4, "active": 2}
    severity = {"removed": 0, "weakened": 1, "strengthened": 2, "added": 3, "relocated": 1, "kept": 4, "baseline": 5}

    def key(c):
        worst = min(severity[h["status"]] for h in c["history"])
        return (order[c["current_status"]], worst, c["lab"], c["id"])

    rows = []
    for c in sorted(items, key=key):
        statuses = sorted({h["status"] for h in c["history"]})
        rows.append(
            f'<li data-lab="{c["lab"]}" data-current="{c["current_status"]}" data-topic="{c["topic"]}" '
            f'data-tags="{" ".join(c["tags"])}" data-events="{" ".join(statuses)}" '
            f'data-text="{E((c["text"] + " " + c["id"]).lower())}">'
            f'<a href="c/{c["id"]}.html"><div class="rmeta">{_badge(c["current_status"])}'
            f'<span>{E(labs[c["lab"]])}</span><span>{E(config.TOPIC_LABEL[c["topic"]])}</span>'
            f'<span class="mono">{c["id"]}</span>{_strip(c["history"])}</div>'
            f'<div class="rtext">{E(_short(c["text"], 220))}</div></a></li>')
    tags = sorted({t for c in items for t in c["tags"]})
    chips = "".join(f'<button type="button" class="chip" data-tag="{E(t)}" aria-pressed="false">{E(t)}</button>' for t in tags)
    legend = "".join(
        f'<span><span class="s-{s}">{config.STATUS_MARK[s]}</span>{E(config.STATUS_LABEL[s])}</span>'
        for s in ("baseline", "added", "kept", "strengthened", "weakened", "removed", "relocated"))
    vmap = {v["version_id"]: v for v in ledger["versions"]}
    cov_rows = []
    for cov in ledger["labs"]:
        n = sum(1 for c in items if c["lab"] == cov["lab"])
        pairs = ", ".join(f'{E(vmap[a]["label"])} → {E(vmap[b]["label"])}' for a, b in cov["traced_pairs"])
        gaps = ", ".join(f'{E(vmap[a]["label"])} → {E(vmap[b]["label"])}' for a, b in cov["untraced_pairs"]) or "None"
        ext = ", ".join(f'{E(vmap[a]["label"])} → {E(vmap[b]["label"])}' for a, b in cov.get("extended_pairs", [])) or "None"
        cov_rows.append(f'<tr><th scope="row"><a href="?lab={cov["lab"]}">{E(cov["name"])}</a></th><td>{n}</td><td>{pairs}</td><td>{ext}</td><td>{gaps}</td></tr>')
    coverage = ('<details class="cov"><summary>Coverage: which version pairs are traced</summary><div class="scroll"><table>'
                '<thead><tr><th>Lab</th><th>Commitments</th><th>Traced by upstream</th><th>Traced by the ledger (text and model)</th><th>Not traced</th></tr></thead><tbody>'
                + "".join(cov_rows) + '</tbody></table></div>'
                '<p class="note">A commitment that is "In force" is in the last traced version. Versions after July 2026 are not in the ledger.</p></details>')
    n_events = sum(1 for c in items for h in c["history"] if h["status"] in config.FEED_STATUSES)
    body = f"""
<h1>What did each lab promise, and what happened to each promise?</h1>
<p class="lede">{len(items)} safety-framework commitments from {len(labs)} developer{"s" if len(labs) != 1 else ""}, across {len(ledger["versions"])} framework versions.
Each commitment has one stable ID. {n_events} recorded changes. Each change has the verbatim text and the SHA-256 of its source document.</p>
{coverage}
<div class="filters">
<div><label for="f-lab">Lab</label><select id="f-lab"><option value="">All</option>{_options(sorted(labs), labs)}</select></div>
<div><label for="f-current">Status now</label><select id="f-current"><option value="">All</option>{_options(["active", "removed", "relocated", "merged", "not_traced"], config.STATUS_LABEL)}</select></div>
<div><label for="f-event">Ever</label><select id="f-event"><option value="">All</option>{_options(["weakened", "strengthened", "removed", "added", "relocated"], config.STATUS_LABEL)}</select></div>
<div><label for="f-topic">Topic</label><select id="f-topic"><option value="">All</option>{_options(sorted({c["topic"] for c in items}), config.TOPIC_LABEL)}</select></div>
<div class="wide"><label for="f-q">Search text or ID</label><input id="f-q" type="search" placeholder="for example: benchmark" autocomplete="off"></div>
</div>
<div class="chips" id="tags" role="group" aria-label="Tags">{chips}</div>
<p class="count" id="count" aria-live="polite"></p>
<div class="legend" aria-label="Legend: one mark for each version">{legend}</div>
<ul class="rows" id="rows">{"".join(rows)}</ul>
<script>
(function(){{
var rows=[].slice.call(document.querySelectorAll('#rows li')),ids=['lab','current','event','topic','q'],tag='';
var chips=[].slice.call(document.querySelectorAll('#tags .chip'));
function el(k){{return document.getElementById('f-'+k)}}
function apply(){{
 var v={{}};ids.forEach(function(k){{v[k]=el(k).value.trim().toLowerCase()}});var n=0;
 rows.forEach(function(r){{var d=r.dataset;
  var ok=(!v.lab||d.lab===v.lab)&&(!v.current||d.current===v.current)&&(!v.topic||d.topic===v.topic)
   &&(!v.event||d.events.split(' ').indexOf(v.event)>=0)&&(!tag||d.tags.split(' ').indexOf(tag)>=0)&&(!v.q||d.text.indexOf(v.q)>=0);
  r.hidden=!ok;if(ok)n++}});
 document.getElementById('count').textContent=n+' of '+rows.length+' commitments';
 chips.forEach(function(c){{c.setAttribute('aria-pressed',c.dataset.tag===tag?'true':'false')}});
 var p=new URLSearchParams();ids.forEach(function(k){{if(v[k])p.set(k,el(k).value.trim())}});if(tag)p.set('tag',tag);
 var s=p.toString();try{{history.replaceState(null,'',s?'?'+s:location.pathname)}}catch(e){{}}
}}
var p=new URLSearchParams(location.search);ids.forEach(function(k){{if(p.get(k))el(k).value=p.get(k);el(k).addEventListener('input',apply)}});
tag=p.get('tag')||'';
chips.forEach(function(c){{c.addEventListener('click',function(){{tag=(tag===c.dataset.tag)?'':c.dataset.tag;apply()}})}});
apply();
}})();
</script>
"""
    return _page(config.SITE_TITLE, body, "", "An open ledger of AI lab safety-framework commitments, with stable IDs and a change feed.")


def _entry_html(c, i, versions):
    h = c["history"][i]
    prev = c["history"][i - 1] if i else None
    v = versions[h["version_id"]]
    parts = [f'<div class="when"><time datetime="{v["publication_date"]}">{_date(v["publication_date"])}</time>'
             f'{_badge(h["status"])}<span class="doc">{E(v["document"])}, version {E(v["label"])}</span></div>']
    if h["quote"] is None:
        if prev and prev["quote"]:
            parts.append(f'<div class="quote gone">{E(prev["quote"])}</div>')
        if h["status"] == "relocated":
            parts.append('<p class="note"><b>Relocated.</b> The framework no longer has this text. '
                         'The upstream coder found a counterpart in a companion document or a non-binding section.</p>')
        else:
            parts.append('<p class="note"><b>No counterpart in this version.</b></p>')
    elif prev and prev["quote"] and prev["quote"] != h["quote"]:
        ratio, marked = _diff(prev["quote"], h["quote"])
        if ratio >= 0.5:
            parts.append(f'<div class="quote">{marked}</div>')
        else:
            parts.append(f'<div class="quote">{E(h["quote"])}</div>'
                         f'<p class="note"><b>Before:</b> <span class="gone">{E(_short(prev["quote"], 400))}</span></p>')
    else:
        parts.append(f'<div class="quote">{E(h["quote"])}</div>')
    if h["status"] == "kept" and prev and prev["quote"] and prev["quote"] != h["quote"]:
        parts.append('<p class="note"><b>Kept.</b> The text changed. The upstream coder found no material change to the obligation.</p>')
    if h.get("mixed"):
        parts.append('<p class="note"><b>Mixed change.</b> Stronger in one dimension and weaker in a different dimension. The status is then Weakened.</p>')
    if h.get("rationale") and h["status"] not in ("kept", "baseline"):
        who = "model" if h.get("coded_by") == "model" else "upstream coder"
        parts.append(f'<p class="note"><b>Why this status ({who}):</b> {E(h["rationale"])}</p>')
    if h.get("disclosure") in config.DISCLOSURE_LABEL and h["status"] in config.FEED_STATUSES:
        parts.append(f'<p class="note"><b>Disclosure:</b> {E(config.DISCLOSURE_LABEL[h["disclosure"]])}</p>')
    if h.get("coded_by") == "model":
        check = h.get("human_check")
        if check == "agrees":
            tail = " One person checked it blind and gave the same code."
        elif check and check.startswith("disagrees:"):
            tail = f' <b>One person checked it blind and coded it "{E(check.split(":")[1])}". Not resolved. This entry needs review.</b>'
        elif check == "not_same_thing":
            tail = " <b>One person checked it blind and did not accept that the two texts are the same commitment. This entry needs review.</b>"
        elif check == "cannot_tell":
            tail = " <b>One person checked it blind and could not decide from the extracted text. This entry needs review.</b>"
        else:
            tail = " No person checked it." + (" <b>The two runs did not agree. This entry needs review.</b>" if h.get("needs_review") else "")
        parts.append('<p class="note"><b>Coded by a model.</b> Two runs of a language model found this counterpart and coded this change.' + tail + '</p>')
    if h.get("gap_before"):
        parts.append('<p class="note"><b>Gap.</b> One or more versions before this entry are not traced.</p>')
    src = [("Section", E(h["section"]) + (" (heading changed)" if h.get("section_changed") else "")) if h["section"] else None,
           ("Source", f'<a href="{E(h["source_url"])}">{E(_short(h["source_url"], 70))}</a>'
                      + (f' · <a href="{E(_wayback(h))}">Wayback</a>' if _wayback(h) else "")),
           ("SHA-256", f'<span class="mono">{h["sha256"]}</span>'),
           ("Quote check", "Found in the hashed document" if h.get("quote_verified") else "Not found by the automatic check") if h["quote"] else None,
           ("Coded by", E(config.CODED_BY_LABEL[h.get("coded_by", "upstream")])),
           ("Confidence", E(h["confidence"])) if h.get("confidence") else None,
           ("Upstream row", f'<span class="mono">{E(h["source_row"])}</span>') if h.get("source_row") else None,
           ("Event ID", f'<span class="mono">{E(h["event_id"])}</span>')]
    parts.append('<dl class="src">' + "".join(f"<dt>{k}</dt><dd>{val}</dd>" for k, val in filter(None, src)) + "</dl>")
    return f'<li class="is-{h["status"]}" id="{E(h["version_id"])}">{"".join(parts)}</li>'


def render_commitment(c, versions, labs, later=False):
    last = c["history"][-1]
    if c["current_status"] == "removed":
        headline = f'Removed on {_date(versions[last["version_id"]]["publication_date"])}'
    elif c["current_status"] == "merged":
        headline = f'Continues as <a href="{c["merged_into"]}.html" class="mono">{c["merged_into"]}</a>'
    elif c["current_status"] == "active":
        headline = (f'In the last traced version, {_date(versions[last["version_id"]]["publication_date"])}'
                    + (". Later versions are not traced." if later else ""))
    else:
        headline = f'Last traced on {_date(versions[last["version_id"]]["publication_date"])}'
    tags = "".join(f'<a class="chip" href="../index.html?tag={E(t)}">{E(t)}</a>' for t in c["tags"])
    gone = " gone" if c["current_status"] == "removed" else ""
    ids_note = ""
    if c.get("former_ids"):
        ids_note += '<p class="note"><b>Former ID:</b> ' + ", ".join(f'<span class="mono">{E(i)}</span>' for i in c["former_ids"]) + ". Two chains were joined into this one.</p>"
    if c.get("related_ids"):
        ids_note += '<p class="note"><b>Overlapping text:</b> ' + ", ".join(f'<a class="mono" href="{E(i)}.html">{E(i)}</a>' for i in c["related_ids"]) + ". These can be the same promise.</p>"
    body = f"""
<p class="rmeta"><a href="../index.html?lab={c["lab"]}">{E(labs[c["lab"]])}</a><span>·</span><span>{E(config.TOPIC_LABEL[c["topic"]])}</span></p>
<h1 class="quote{gone}" style="font-weight:400">{E(c["text"])}</h1>
<div class="idline">{_badge(c["current_status"])}<span>{headline}</span></div>
<div class="idline"><span class="mono" id="cid">{c["id"]}</span><button class="copy" type="button" data-copy="{c["id"]}">Copy ID</button>{_strip(c["history"])}</div>
<div class="chips">{tags}</div>
{ids_note}
<h2>History, oldest first</h2>
<ol class="timeline">{"".join(_entry_html(c, i, versions) for i in range(len(c["history"])))}</ol>
<script>
[].forEach.call(document.querySelectorAll('button.copy'),function(b){{b.addEventListener('click',function(){{
 if(navigator.clipboard){{navigator.clipboard.writeText(b.dataset.copy).then(function(){{b.textContent='Copied'}})}}}})}});
</script>
"""
    title = f'{_short(c["text"], 70)} · {labs[c["lab"]]} · {config.SITE_TITLE}'
    return _page(title, body, "../", f'{labs[c["lab"]]} commitment {c["id"]}: {_short(c["text"], 140)}')


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
    labs = {}
    for v in ledger["versions"]:
        labs[v["lab"]] = v.get("lab_name", v["lab"])
    versions = {v["version_id"]: v for v in ledger["versions"]}
    later_untraced = {}
    for cov in ledger["labs"]:
        last = cov["last_traced_version_id"]
        later_untraced[cov["lab"]] = any(a == last for a, _ in cov["untraced_pairs"])
    if os.path.isdir(os.path.join(out, "c")):
        shutil.rmtree(os.path.join(out, "c"))
    os.makedirs(os.path.join(out, "c"), exist_ok=True)

    def write(name, text):
        with open(os.path.join(out, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    write("index.html", render_index(ledger, labs))
    for c in ledger["commitments"]:
        write(os.path.join("c", c["id"] + ".html"), render_commitment(c, versions, labs, later_untraced[c["lab"]]))
    for c in ledger["commitments"]:
        for old in c.get("former_ids", []):
            body = (f'<h1>This ID was joined into a different commitment</h1><p class="lede"><span class="mono">{E(old)}</span> is now '
                    f'<a class="mono" href="{c["id"]}.html">{c["id"]}</a>. The ledger does not use the former ID again.</p>')
            write(os.path.join("c", old + ".html"), _page(f"{old} · {config.SITE_TITLE}", body, "../", f"Former ID {old}, now {c['id']}."))
    write("feed.xml", render_feed(ledger, labs))
    write(".nojekyll", "")
    shutil.copyfile(os.path.join(root, "data", "ledger.json"), os.path.join(out, "ledger.json"))
    shutil.copyfile(os.path.join(root, "schema.json"), os.path.join(out, "schema.json"))
    return len(ledger["commitments"])
