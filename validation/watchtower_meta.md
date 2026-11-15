# Watchtower check: Meta v2 → v2.1

Reference: [Watchtower entry, Meta, 2 October 2026](https://www.themidasproject.com/watchtower/meta-10022026). The entry lists 17 changes. It says that the list is not complete.

**An AI system made this mapping. No person has checked it.** The row texts are short paraphrases of the Watchtower entry.

| # | Watchtower change | Ledger ID | Ledger status at v2.1 | In ledger? |
|---|---|---|---|---|
| 1 | Framework renamed | none | none | No. Not a commitment. |
| 2 | More board-level governance | `meta-governance-a27e` | added | Yes |
| 3 | Longer discussion of open-weight models | none | none | No. Not a commitment. |
| 4 | New "Loss of Control" outcome category | `meta-eval-scope-9f7e` | added | Yes |
| 5 | "Prospective assessment" before training | `meta-eval-trigger-25d2`, `meta-consequence-d229`, `meta-eval-method-c882`, `meta-eval-trigger-df00` | added | Yes |
| 6 | New safeguards: sandbox standards, red-teaming, remediation, logging, monitoring | `meta-security-7333`, `meta-security-5230`, `meta-mitigation-e95d`, `meta-eval-method-a199`, `meta-mitigation-8827`, `meta-mitigation-b6a1`, `meta-mitigation-65f5`, `meta-consequence-4b8e` | added | Yes |
| 7 | Approval by the Chief AI Officer or the Director of Alignment and Risk for monitoring exceptions | `meta-consequence-512f` | added | Yes |
| 8 | "Maximum elicitation" commitment deleted | `meta-eval-method-bc8b` | removed | Yes |
| 9 | Helpful-only testing language deleted | `meta-eval-method-bc8b` | removed | Yes, same commitment as row 8 |
| 10 | Domain-specific capability training deleted | `meta-eval-method-e80c` | removed | Yes |
| 11 | Review of agent transcripts deleted | `meta-eval-method-ea6c` | removed | Yes |
| 12 | Provisional "high risk" classification and hold deleted | `meta-consequence-8456` | removed | Yes |
| 13 | 75% pass@10 replaced with "sufficiently high performance" | `meta-eval-trigger-10c1` | weakened | Yes |
| 14 | "At least one" challenge becomes "sufficiently many" | `meta-eval-trigger-3907` | weakened | Yes |
| 15 | Robustness against adversarial attacks deleted | `meta-eval-method-911d`, `meta-consequence-32db` | weakened | Yes, see note |
| 16 | "Ensure consistent refusal" becomes research commitments | `meta-consequence-afe4` | weakened | Yes |
| 17 | Evidence of reliable refusal narrowed | `meta-consequence-afe4` | weakened | Yes, same commitment as row 16 |

**Result: 15 of 17 Watchtower changes are in the ledger. The other 2 are not commitments. The direction agrees for all 15.**

Notes:

- **Row 15.** Two ledger commitments lost adversarial-robustness words. The mapping does not decide which one Watchtower means.
- **Rows 5 and 6.** The ledger has more than one commitment for each Watchtower row. The ledger is finer-grained.
- **In the ledger, not in the Watchtower list:** `meta-eval-method-11e0` (weakened).
- **Not independent.** The person who confirmed the ledger entries saw a note on the Watchtower entry for each item. This check shows consistency. It is not a blind test.

Limits: one entry, one developer, an AI-made mapping, no second coder.
