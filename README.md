# Commitment Ledger

**What did each AI lab promise in its safety framework, and what happened to each promise?**

An open ledger of 446 safety-framework commitments from 5 frontier AI developers, across 22 framework versions.
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
| Anthropic | 170 | 9 | 2 |
| Google DeepMind | 55 | 4 | 2 |
| Meta | 106 | 2 | 1 |
| OpenAI | 51 | 2 | 1 |

Recorded changes: 161 weakened, 69 strengthened, 41 removed, 156 added, 8 relocated.

## Validation

Full results: [`validation.md`](validation.md).

- **Model test.** Claude Opus 5.5 coded 120 matched pairs as kept, strengthened or weakened.
  It agreed with the upstream code on 105 (88%, 95% CI 80 to 92). Cohen's kappa is 0.81.
  7 of the 120 had the opposite direction.
- **Stability.** A second run of the same model gave the same answer on 113 of 120 items (kappa 0.91). 2 of the 7 changes went to the opposite direction.
- **Human check.** One lawyer (the author) coded 20 items blind: 10 where the model agreed with upstream and 10 where it disagreed. He coded 17, and rejected the pairing of 3. In the disagreed group (8 coded), he agreed with upstream on 4, with the model on 2, and with neither on 2. This is not a random sample.
- **Alignment test.** Given one commitment and the full next version, the model found the same counterpart as upstream, or correctly found none, for 48 of 60 items (80%). Plain text matching: 37 of 60 (62%). Google DeepMind v3.0 to v3.1: 20 of 20. OpenAI Beta to v2, a full rewrite: 10 of 20.
- **Watchtower check.** The ledger has 14 of the 17 sub-changes in the Watchtower entry for the xAI revision of June 2026.
- **Quote check.** 855 of 871 quotes (98%) are in the text extraction of the hashed source document.
- **Count check.** The ledger has one event for each of the 636 upstream rows of the 5 labs.

## Known limits

1. **The codes are not ground truth.** A language model helped with the upstream coding, and one human author adjudicated it. Read each status as a reference.
2. **Anthropic has a break.** RSP v2.0 → v2.1 → v2.2 is not traced. 71 commitments stop at v2.0 with status `not_traced`. 49 start at v2.2 with new IDs. Some are the same promise.
3. **Anthropic stops at v3.0.** Versions v3.1 to v3.4 are in the corpus but are not traced.
4. **Nothing after July 2026.** The ledger is a seed dataset. It does not update automatically.
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
| `python run.py stats` | Prints a count table. |

The build has no language-model step and no network step after `fetch`. Two builds give the same files.

## Repository

```
schema.json          JSON Schema
SCHEMA.md            field definitions, status meanings, ID rules
run.py               entry point
ledger/              corpus reader, builder, site and feed, validation
data/ledger.json     the dataset
examples/            one full record
validation/          test items, rules, prompt, model answers (2 runs), key, human check, Watchtower check
validation.md        results
docs/                the site (GitHub Pages)
```

## Next steps

- Trace the untraced Anthropic pairs, to close the break.
- Add an alignment step for new versions, and test it against the upstream rows.
- Add a scheduled job that looks for new framework versions.
- Ask a second person to code a sample.

## Credit and licence

The seed data is derived from the coding in the
[Frontier Safety Framework Corpus](https://github.com/louisyzhu/frontier-safety-framework-corpus)
by Louis Yiven Zhu, [DOI 10.5281/zenodo.22670700](https://doi.org/10.5281/zenodo.22670700),
the data for [Silent Revision, arXiv:2609.08789](https://arxiv.org/abs/2609.08789). That coding is CC BY 4.0.

- **Data** (`data/`, `validation/`, `docs/ledger.json`): CC BY 4.0. Credit this repository and the upstream corpus.
- **Code:** MIT.
- **Quotes** from provider documents are the property of their publishers. The ledger does not copy the documents. It links to them by URL and SHA-256.

The idea for a commitment-level record comes from [Watchtower](https://www.themidasproject.com/watchtower) by The Midas Project. This project is independent of The Midas Project.
