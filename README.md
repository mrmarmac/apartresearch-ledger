# Commitment Ledger

A ledger of the safety-framework commitments of frontier AI developers.
Each commitment has one stable ID and a history across framework versions.

Status: work in progress (Apart Research AI x Epistemics sprint, November 2026).

## Build

```bash
pip install -r requirements.txt
python run.py all
```

Output: `data/ledger.json`. Schema: `schema.json`.

## Source and credit

The seed data is derived from the coding in
[Frontier Safety Framework Corpus](https://github.com/louisyzhu/frontier-safety-framework-corpus)
by Louis Yiven Zhu (CC BY 4.0), the data for
[Silent Revision, arXiv:2609.08789](https://arxiv.org/abs/2609.08789).
The ledger adds stable IDs across versions, an open JSON schema, and a feed.
Provider documents are not copied here. The ledger links to them by URL and SHA-256.
