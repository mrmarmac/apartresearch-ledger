# Validation: a model against the upstream codes

**Question.** The ledger gives a model two versions of one commitment. Does the model give the same code as the upstream coding: kept, strengthened or weakened?

This test is for the future. A new framework version needs a classifier. The seed data in `data/ledger.json` does not use this model.

## Method

- **Gold standard:** final codes in `coding/tracing_FINAL_v3.csv` of the upstream corpus (commit `11cbeda80c5c`).
- **Pool:** rows of the 5 ledger labs with text in both versions: 190 kept, 59 strengthened, 107 weakened. Rows that the upstream codebook uses as worked examples are not in the pool.
- **Sample:** 40 rows for each code, 120 in total. Random, seed 20261115. Mixed sequence.
- **Model:** Claude Opus 5.5 (sub-agent), in 3 independent runs of 40 items.
- **Input to the model:** the two texts, their section headings, the developer name, and `validation/rules.md` (sections 4, 5 and 11.1 to 11.3 of the upstream codebook).
- **Not given to the model:** the upstream code, the rationale, the row ID, or the source documents.
- **Scoring:** `python run.py score`. The script makes the key again from the seed.

## Result

**Agreement: 105 of 120 (88%, 95% CI 80 to 92). Cohen's kappa: 0.81.**

**Opposite direction** (strengthened against weakened): 7 of 120. This is the most important error type for a ledger.

| Upstream code | Model: kept | Model: strengthened | Model: weakened | Recall |
|---|---|---|---|---|
| kept | 36 | 2 | 2 | 90% |
| strengthened | 3 | 33 | 4 | 82% |
| weakened | 1 | 3 | 36 | 90% |
| **Precision** | 90% | 87% | 86% | |

The sample has the same number of rows for each code. The pool does not. Thus the agreement figure is not the agreement that you get on a full framework revision.

## Agreement by row type

| Row type | Agreement |
|---|---|
| Upstream coding was stable (all re-runs agreed) | 67 of 73 (92%, 95% CI 83 to 96) |
| Upstream coding was disputed and re-examined | 38 of 47 (81%, 95% CI 67 to 90) |
| Upstream confidence high | 42 of 45 (93%, 95% CI 82 to 98) |
| Upstream confidence medium | 46 of 55 (84%, 95% CI 72 to 91) |
| Upstream confidence low | 17 of 20 (85%, 95% CI 64 to 95) |
| Mixed change (stronger and weaker) | 11 of 14 (79%, 95% CI 52 to 92) |
| xAI | 38 of 42 (90%, 95% CI 78 to 96) |
| Anthropic | 26 of 28 (93%, 95% CI 77 to 98) |
| Google DeepMind | 18 of 25 (72%, 95% CI 52 to 86) |
| Meta | 9 of 10 (90%, 95% CI 60 to 98) |
| OpenAI | 14 of 15 (93%, 95% CI 70 to 99) |

## Disagreements

| Item | Upstream row | Upstream | Model | Model's reason |
|---|---|---|---|---|
| q008 | `OAI-1-026` | strengthened | weakened | Forecast trigger "(or are forecasted to reach)" dropped; later applies only to systems that "cross this capability threshold". |
| q019 | `XAI-4-036` | strengthened | weakened | Drops "sufficient to prevent... stolen by a motivated non-state actor" and distillation measures; adds "NIST 800-171" and "SOC 2" (MIX). |
| q024 | `XAI-3-001` | strengthened | kept | Renaming to "FAIF" and adding "including catastrophic risks" within "significant risks" does not change coverage. |
| q039 | `GDM-2-030` | weakened | strengthened | Illustrative "may be triggered, for example" becomes fixed trigger: assessments "upon the completion of a post-training run". |
| q045 | `ANT-1-005` | weakened | strengthened | Pause commitment kept ('will pause training') and resumption now also requires having 'established it is sufficient for the model'. |
| q046 | `GDM-2-022` | strengthened | kept | Threshold text essentially identical ('work out' to 'discover'); only relabelled from exploratory CCL to 'Stealth and Situational Awareness TCL'. |
| q047 | `GDM-1-013` | strengthened | weakened | 'applied to models reaching a CCL' narrowed to 'external deployments' for misuse CCLs, though ML R&D adds 'large scale internal deployments'. |
| q063 | `META-1-028` | weakened | kept | 'significant uplift towards execution of a threat scenario' reworded as 'could substantially contribute to any threat scenario'; threshold level appears equivalent. |
| q069 | `XAI-2-017` | kept | weakened | 'evaluation and mitigation plans ... intend to improve' narrowed to 'developing naturalistic evaluation environments', dropping mitigation. |
| q072 | `GDM-1-022` | weakened | strengthened | 'fully automate the AI R&D pipeline' lowered to automating 'the work of any team of researchers at Google'. |
| q093 | `ANT-1-021` | kept | strengthened | "data should similarly be filtered" becomes present-tense standing commitment "data is filtered for harmfulness". |
| q097 | `XAI-4-047` | strengthened | weakened | Adds gate "will only proceed ... if systemic risks ... acceptable" but drops "Pre-deployment reviews include assessing benchmark results" and internal oversight-evasion review; mixed (MIX). |
| q098 | `GDM-2-020` | strengthened | kept | Both versions remain field recommendations ("We recommend", "define and recommend"), not self-commitments; no change in obligation. |
| q113 | `GDM-2-006` | kept | strengthened | Core retained and adds "we strive to learn from our post-market monitoring mechanisms, including ... incidents". |
| q115 | `GDM-2-025` | kept | weakened | Review scope changes from "systemic risk" to "significant and severe risk", plausibly narrower; conservative call. |

## Limits

1. **The gold standard is not ground truth.** A language model helped with the upstream first pass. One human author adjudicated. Agreement thus shows consistency with that coding. It does not show that the code is correct.
2. **This test does not include alignment.** The model gets a matched pair. To find the counterpart of a commitment in a new version is a different, harder step.
3. **This test does not include Added, Removed or Relocated.** Those codes depend on alignment, not on direction.
4. **Isolation was by instruction.** The model ran as a sub-agent with file tools. The instructions told it to read only its batch file and the rules. Each run made 4 tool calls, which agrees with: read rules, read batch, write answers, report.
5. **One run for each item.** The test does not measure how much the model changes between runs.
6. **The sample is 120 rows.** Read the confidence intervals.
7. **The model is a high-capability model.** A low-cost model was not tested. Its agreement can be lower.

## Second check: one Watchtower entry

**Question.** Watchtower describes the xAI revision of 30 June 2026 in prose. Does the ledger have each change, in the same direction?

**Source.** [Watchtower, xAI, 11 July 2026](https://www.themidasproject.com/watchtower/xai-07112026), read on 15 November 2026.

**Method.** One person divided the entry into sub-changes by hand, and then searched the ledger for each one. This check uses the seed data. It does not use a model.

| # | Watchtower sub-change | Ledger commitment | Ledger status | Found |
|---|---|---|---|---|
| 1 | Whistleblower protection clause removed | `xai-governance-673f` | removed | Yes |
| 2 | Anonymous internal report channel removed | `xai-governance-0724` | removed | Yes |
| 3 | References to California's TFAIA removed | `xai-governance-291c` | removed | Yes |
| 4 | The term "catastrophic risk" removed | `xai-governance-5bc2` | weakened | Yes |
| 5 | MASK honesty criterion removed | `xai-mitigation-6d2e` | weakened | Yes |
| 6 | Biology and chemistry answer-rate criterion removed | `xai-mitigation-7539` | weakened | Yes |
| 7 | Named benchmarks replaced with "may utilize" | `xai-eval-method-d279` | weakened | Yes |
| 8 | Honesty and instruction-hierarchy training statement removed | `xai-mitigation-68cf` | weakened | Yes |
| 9 | System-prompt instruction not to deceive removed | `xai-mitigation-68cf` | weakened | Yes |
| 10 | "Public transparency and third-party review" section removed | `xai-disclosure-f8c3` | removed | Yes |
| 11 | New information security detail (NIST 800-171, SOC 2) | `xai-security-adf9` | strengthened | Yes |
| 12 | New annual full systemic risk assessment | `xai-eval-trigger-cebf` | added | Yes |
| 13 | Incident reports to authorities when the law requires | `xai-governance-9e90` | strengthened | Yes |
| 14 | New paragraph on loss-of-control practice | `xai-mitigation-d832` | strengthened | Yes, see note |
| 15 | Statement removed: a model can change its behaviour in an evaluation | none | none | No |
| 16 | Statement removed: AIs can develop misaligned value systems | none | none | No |
| 17 | New "Harmful Manipulation Risks" domain | none | none | No |

**Result: 14 of 17 sub-changes are in the ledger (82%). For all 14, the direction agrees or is compatible.**

Notes:

- **Rows 5 and 6.** Watchtower says "removed". The ledger says "weakened", because the upstream coder found a qualitative replacement. The direction is the same.
- **Row 14.** Watchtower says that the new paragraph has no commitment, evaluation or trigger. The ledger records it two times: as "strengthened" against a vague earlier sentence, and as "weakened" against the specific training statement (rows 8 and 9).
- **Rows 15 and 16** are admissions, not commitments. The upstream codebook traces commitments only. A ledger of commitments will not have them.
- **Row 17** is a true miss. A new risk domain is a change of scope.
- **Not in the test:** the AB 2013 training-data disclosure. It was on the xAI website, not in the framework.

Limits: one entry, one developer, one person, no second coder. The seed versions and the Watchtower entry describe the same revision, so this check cannot find a revision that the ledger does not have.
