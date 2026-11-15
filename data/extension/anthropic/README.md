# Anthropic extension data

The ledger's own tracing of 6 Anthropic version pairs that the upstream corpus does not trace:
v2.0 → v2.1 → v2.2 and v3.0 → v3.1 → v3.2 → v3.3 → v3.4.

| File | Content |
|---|---|
| `trace_A_items.json`, `trace_B_items.json` | Commitments whose words are not in the next version. A = v2.x, B = v3.x. |
| `trace_*_run1.json`, `trace_*_run2.json` | Two independent model runs: the counterpart in each later version. |
| `code_items.json` | The 47 pairs where the text changed, with context from the later document. |
| `code_run1.json`, `code_run2.json` | Two independent model runs: kept (R), strengthened (S) or weakened (W). |

Model: Claude Opus 5.5, as sub-agents. The tracing runs got the definition of a counterpart
(`validation/alignment/definition.md`) and the full later documents, and not the coding rules.
The coding runs got `validation/rules.md` and `code_items.json`.

`ledger/extend.py` applies these files in the build. Run 1 gives the value. Run 2 is the check:
where the two runs do not agree, the entry gets `needs_review: true`.

No person checked these answers.
