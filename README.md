# Commitment Ledger

**What did each AI lab promise in its safety framework, and what happened to each promise?**

An open ledger of 447 safety-framework commitments from 5 frontier AI developers, across 23 framework versions.
Each commitment has one stable ID and a history: kept, strengthened, weakened, removed or relocated.

- **Site:** https://mrmarmac.github.io/apartresearch-ledger/
- **Data:** [`data/ledger.json`](data/ledger.json) ([public URL](https://mrmarmac.github.io/apartresearch-ledger/ledger.json))
- **Feed:** [`feed.xml`](https://mrmarmac.github.io/apartresearch-ledger/feed.xml), one item for each change, stable GUIDs
- **Schema:** [`schema.json`](schema.json), explained in [`SCHEMA.md`](SCHEMA.md)
- **Validation:** [`validation.md`](validation.md)

Made for the Apart Research AI x Epistemics sprint, November 2026.

## Demo

1. Open the [index with the filter `xAI` + `whistleblower`](https://mrmarmac.github.io/apartresearch-ledger/index.html?lab=xai&tag=whistleblower).
2. Open [`xai-governance-673f`](https://mrmarmac.github.io/apartresearch-ledger/c/xai-governance-673f.html).
3. The clause is in 4 versions from February 2025. It is not in the version of 30 June 2026.
   Each entry has the verbatim text, the source link, and the SHA-256 of the document.

[Watchtower](https://www.themidasproject.com/watchtower/xai-07112026) reported this revision on 11 July 2026.

## What is new here

This project does not do new coding of the frameworks. It builds on existing work.

| Existing work | What it gives | What it does not give |
|---|---|---|
| [Watchtower](https://www.themidasproject.com/watchtower) (The Midas Project) | A log of policy changes and violations, written by people | One entry for each revision. No record for each commitment. No data feed. |
| [Silent Revision corpus](https://github.com/louisyzhu/frontier-safety-framework-corpus) (Zhu, 2026) | 710 commitments, coded for each version pair, with hashes | A new row ID in each pair. CSV only. No history for one commitment. |

The ledger adds four things:

1. **Stable IDs across versions.** One ID follows one commitment through all traced versions.
2. **An open JSON schema** with defined status values and ID rules.
3. **A change feed** (RSS) with stable GUIDs, and one page for each commitment.
4. **A test of a model** against the upstream codes, as a first step to trace new versions.

## Data

| Lab | Commitments | Versions | Traced version pairs |
|---|---|---|---|
| xAI | 64 | 5 | 4 |
| Anthropic | 156 | 9 | 2 by upstream, 6 by the ledger |
| Google DeepMind | 55 | 4 | 2 |
| Meta | 121 | 3 | 1 by upstream, 1 by the ledger |
| OpenAI | 51 | 2 | 1 |

Recorded changes from the upstream coding: 161 weakened, 69 strengthened, 41 removed, 156 added, 8 relocated.
Recorded changes from the ledger's own extension of Anthropic (model-coded, then checked by a person): 16 weakened, 2 strengthened.
Recorded changes from the ledger's own trace of Meta v2 → v2.1 (model-coded, then confirmed by a person): 6 weakened, 4 removed, 15 added.

### The Anthropic extension

The upstream corpus does not trace 6 small Anthropic revisions: v2.0 → v2.1 → v2.2 and v3.0 → v3.1 → v3.2 → v3.3 → v3.4.
The ledger traces them itself. Each entry says who decided it (`coded_by`).

| Step | Method | Result |
|---|---|---|
| 1 | Text match: the same words are in the next version | 490 entries, status kept |
| 2 | Model, two runs: find the counterpart of a changed commitment | 85 steps. The two runs found the same passage in all 85. No removal. |
| 3 | Model, two runs: code the direction of each changed pair | 47 entries: 31 kept, 14 weakened, 2 strengthened. The runs agree on 43. |
| 3b | One person: blind check of the 47 entries, then a second look at the 13 without agreement | Final: 29 kept, 16 weakened, 2 strengthened. No entry is open. For one entry, the person compared the two PDFs. He changed two entries from strengthened to weakened (mixed) after the full-document rerun. |
| 4 | Join a chain that ends at v2.2 with the upstream chain that starts at v2.2, when the texts overlap one to one | 14 chains joined. The former ID is in `former_ids`. |

- 68 Anthropic commitments now reach v3.4. 11 of them have a history from v1.0 (2023) to v3.4 (2026).
- 25 chains overlap an upstream chain, but not one to one. They are not joined. See `related_ids`.
- The ledger does not detect commitments that are new in v2.1, v2.2 or v3.1 to v3.4.
- One person (the author) checked the 47 model-coded entries blind. He agreed with the model on 34 of 44 decided entries (77%). He then took a second look at the others, not blind. Where the two model runs agreed, his final code is the model code in 41 of 42 decided entries. The one error that passed two runs was a phrase that moved outside the text that the model got. Where the two runs disagreed (4 entries), the final code differs from model run 1 in 3.
- **Full-document rerun.** Two new runs coded the 47 entries again with the two full documents. They corrected the one known error of the moved-phrase type (e19). Their agreement with the final codes was not higher than before (42 and 43 of 47, against 42 and 45). See `validation.md`.
- Data and prompts: `data/extension/anthropic/`.

## Validation

Full results: [`validation.md`](validation.md).

- **Model test.** Claude Opus 5.5 coded 120 matched pairs as kept, strengthened or weakened.
  It agreed with the upstream code on 105 (88%, 95% CI 80 to 92). Cohen's kappa is 0.81.
  7 of the 120 had the opposite direction.
### The Meta v2.1 trace

Meta published v2.1 after the upstream corpus was frozen. The ledger traces v2 → v2.1 itself. This is the first pair where the ledger also looks for new commitments.

| Step | Method | Result |
|---|---|---|
| 1 | Text match | 82 of 104 commitments have the same words in v2.1. Status kept. |
| 2 | Model, two runs, full document: find the counterpart of the other 22 | 18 counterparts, 4 with none. The runs found the same passage for 16 of the 18. |
| 3 | Model, two runs, full section: code the direction of the 18 pairs | 12 kept, 6 weakened. The runs agree on all 18. |
| 4 | Model, two runs, both full documents: list passages in v2.1 with no counterpart in v2 | 15 candidates. 14 are in both runs. |
| 5 | One person, not blind: decide the 6 weakened, the 4 removed, the 15 candidates and the 2 tracing disagreements | He confirmed all 26. No entry has `needs_review`. |

- The person saw the two model answers and a note on the Watchtower entry. This step is a confirmation, not an independent check.
- The 11 model-coded "kept" entries without a tracing disagreement were not checked by a person.
- Comparison with the Watchtower entry for this revision: [`validation/watchtower_meta.md`](validation/watchtower_meta.md).
- Files: `data/extension/meta/`.

- **Stability.** A second run of the same model gave the same answer on 113 of 120 items (kappa 0.91). 2 of the 7 changes went to the opposite direction.
- **Human check.** One lawyer (the author) coded 20 items blind: 10 where the model agreed with upstream and 10 where it disagreed. He coded 17, and rejected the pairing of 3. In the disagreed group (8 coded), he agreed with upstream on 4, with the model on 2, and with neither on 2. This is not a random sample.
- **Alignment test.** Given one commitment and the full next version, the model found the same counterpart as upstream, or correctly found none, for 48 of 60 items (80%). Plain text matching: 37 of 60 (62%). Google DeepMind v3.0 to v3.1: 20 of 20. OpenAI Beta to v2, a full rewrite: 10 of 20.
- **Watchtower check.** The ledger has 14 of the 17 sub-changes in the Watchtower entry for the xAI revision of June 2026.
- **Quote check.** 1,459 of 1,475 quotes (99%) are in the text extraction of the hashed source document.
- **Recall test.** The model step that finds new commitments found 26 of 34 upstream additions in 4 pairs (76%). About 1 listed passage in 4 has a counterpart according to upstream.
- **Link check.** 21 of 23 source addresses give a file with the recorded SHA-256 (15 November 2026). The xAI address of 30 June 2026 gives HTTP 404, because xAI published the file again at a new address. The archive address for Meta v1.1 gives different bytes. A person opened it and saw the framework PDF. The cause of the different hash is not known. See [`validation/links.md`](validation/links.md).
- **Tests.** `python run.py test` checks the ID rules, the history order, the hashes and the feed. One known defect: `google-eval-scope-6326` starts with a change, because the ledger did not find its earlier row.
- **Count check.** The ledger has one event for each of the 636 upstream rows of the 5 labs.

## Change watcher

A GitHub Action runs one time each day. It gets 10 addresses (framework files and the pages that list them) and compares a SHA-256 with the last one.
If a hash is different, it opens an issue in this repository. Details and limits: [`watch/README.md`](watch/README.md).

First result (15 November 2026): 4 of 5 framework files are identical to the corpus files. The xAI framework dated 30 June 2026 is a different file at a new address ([issue 1](https://github.com/mrmarmac/apartresearch-ledger/issues/1)). The words are identical. The PDF title changed: the earlier file had the title "Privileged/Confidential DRAFT working FRAMEWORK DOC".

## Known limits

1. **The codes are not ground truth.** A language model helped with the upstream coding, and one human author adjudicated it. Read each status as a reference.
2. **Anthropic is joined in part only.** The upstream coding cut the v2.0 text and the v2.2 text into different units. The ledger joined 14 chains and already had 20. 55 chains stop at v2.2 with status `not_traced`, and 25 of those overlap an upstream chain that the ledger could not join one to one.
3. **Anthropic v2.1, v2.2 and v3.1 to v3.4 are traced by the ledger, not by upstream.** Text match and a model did this work. One person checked the model-coded entries. The pair v2.0 → v2.1 has no official redline from Anthropic. New commitments in those versions are not detected.
3a. **Meta v2.1 is traced by the ledger, not by upstream.** One person confirmed the changes, but he saw the model answers first. In a test on 4 other pairs, the search for new commitments found 26 of 34 upstream additions (76%). The 15 new Meta commitments are thus a lower bound.
4. **Nothing after July 2026.** The ledger is a seed dataset. A daily watcher reports when a framework file or page is different (see `watch/`), but a person must then trace the new version.
5. **Frameworks only.** Model cards, usage policies and violations are not in the ledger. Watchtower covers those.
6. **Commitments only.** Admissions and descriptions are not commitments, and are not in the ledger.
7. **Links across versions use text.** For xAI, the upstream notes give the links. For Google DeepMind and Anthropic, the ledger uses exact text, then similarity of 0.9 or more. A commitment that was fully rewritten gets a new ID.
8. **Tags are keyword rules.** They can miss or over-match.
9. **"In force" means "in the last traced version".** See the `labs` section of the ledger for coverage.

## Build

Python 3.10 or later.

```bash
pip install -r requirements.txt
python run.py all
```

| Command | Result |
|---|---|
| `python run.py fetch` | Downloads the upstream corpus at a pinned commit into `cache/`. |
| `python run.py build` | Writes `data/ledger.json`. |
| `python run.py validate` | Checks the ledger against `schema.json`. |
| `python run.py check` | Checks that the demo path works. |
| `python run.py site` | Writes the site and `feed.xml` into `docs/`. |
| `python run.py align` | Scores the alignment test and writes `validation/alignment/report.md`. |
| `python run.py score` | Scores `validation/predictions/` and writes `validation.md`. |
| `python run.py watch` | Gets each watched address and compares its hash with `watch/state.json`. |
| `python run.py stats` | Prints a count table. |

The build has no language-model step and no network step after `fetch`. Two builds give the same files.

## Repository

```
schema.json          JSON Schema
SCHEMA.md            field definitions, status meanings, ID rules
run.py               entry point
ledger/              corpus reader, builder, site and feed, validation
data/ledger.json     the dataset
data/extension/      tracing and coding answers for the Anthropic and Meta pairs that upstream does not trace
examples/            one full record
validation/          test items, rules, prompt, model answers (2 runs), key, human check, Watchtower check
validation.md        results
watch/               the change watcher: addresses, last hashes
tests/               tests
docs/                the site (GitHub Pages)
```

## Next steps

- Ask an independent second person to check the model-coded Anthropic entries, and resolve the 25 overlaps.
- Add an alignment step for new versions, and test it against the upstream rows.
- Trace a new version when the watcher reports one.
- Ask a second person to code a sample.

## Credit and licence

The seed data is derived from the coding in the
[Frontier Safety Framework Corpus](https://github.com/louisyzhu/frontier-safety-framework-corpus)
by Louis Yiven Zhu, [DOI 10.5281/zenodo.22670700](https://doi.org/10.5281/zenodo.22670700),
the data for [Silent Revision, arXiv:2609.08789](https://arxiv.org/abs/2609.08789). That coding is CC BY 4.0.

- **Data** (`data/`, `validation/`, `docs/ledger.json`): CC BY 4.0. Credit this repository and the upstream corpus.
- **Code:** MIT. See [`LICENSE`](LICENSE). Data licence: [`LICENSE-DATA.md`](LICENSE-DATA.md).
- **Quotes** from provider documents are the property of their publishers. The ledger does not copy the documents. It links to them by URL and SHA-256.

Commitment Ledger builds on [Watchtower](https://www.themidasproject.com/watchtower) by The Midas Project. It extends the Watchtower idea to a record for each commitment. The Midas Project did not take part in this work and has not endorsed it.
