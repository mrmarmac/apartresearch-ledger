## Recall test: does the model find new commitments?

The Meta v2.1 trace uses a model to find commitments with no counterpart in the earlier version. This test measures that step against the upstream coding.

Method: 4 version pairs where upstream coded the additions. The model got the two full documents, the definition of a commitment, and the definition of a counterpart. It did not get the upstream rows. Two independent runs for each pair. Same model and same instructions as the Meta run (`validation/recall/prompt.md`). An upstream addition counts as found if a model passage and the upstream quote share a long identical run (the `same_passage` rule, which the ledger had before this test).

| Pair | Upstream additions | Found by run 1 | Found by run 2 | Found by both |
|---|---|---|---|---|
| Google DeepMind v2.0 → v3.0 | 8 | 6 | 6 | 6 |
| Google DeepMind v3.0 → v3.1 | 11 | 9 | 9 | 9 |
| xAI Aug 2025 → Dec 2025 | 5 | 5 | 5 | 5 |
| xAI Dec 2025 → June 2026 | 10 | 6 | 5 | 5 |
| **Total** | **34** | **26 (76%)** | **25 (74%)** | **25 (74%)** |

**Result: the model found 26 of 34 upstream additions (76%, 95% CI 60 to 88). It did not find 8.**

The model also listed passages that upstream does not code as additions:

| | Run 1 | Run 2 |
|---|---|---|
| Passages listed | 56 | 47 |
| Match an upstream addition | 32 | 28 |
| Match an upstream row with a different code (upstream found a counterpart) | 13 | 11 |
| Match no upstream row | 11 | 8 |

How to read this:

- **The step misses about 1 addition in 4.** The 15 new Meta commitments are a lower bound, not a full list.
- **The step lists too many.** About 1 passage in 4 has a counterpart in the earlier version according to upstream. For Meta v2.1, a person confirmed each candidate, but he saw the model's reason first.
- "Match no upstream row" is not an error by itself. Upstream can have no row for a passage, or the units of text are different.
- All model quotes are verbatim in the later document (103 of 103).
- Upstream is not ground truth. A miss can be a disagreement about what a commitment is.
- More than one model passage can match one upstream row. That is why 32 passages match 26 rows.

Limits: 34 additions, 2 developers. No full rewrite is in the test (Anthropic v3.0, Meta v2, OpenAI v2). The match rule depends on shared words; no person checked the matches. The model runs had access to the machine that holds the upstream files; the instructions told them to use the four given files only.

Files: `validation/recall/`.
