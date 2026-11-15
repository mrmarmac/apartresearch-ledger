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
