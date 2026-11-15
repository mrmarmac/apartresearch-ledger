# Meta v2 → v2.1

The upstream corpus stops at Meta v2. The ledger traces v2 → v2.1 itself.
Source document: see `data/documents.json` (SHA-256 checked at `python run.py fetch`).

| File | Content |
|---|---|
| `trace_M_items.json` | The 22 commitments whose v2 words are not in v2.1 |
| `trace_M_run1.json`, `trace_M_run2.json` | Two model runs: the counterpart in v2.1, or none |
| `code_items.json`, `code_run1.json`, `code_run2.json` | Two model runs: the direction of the 18 pairs |
| `added_run1.json`, `added_run2.json` | Two model runs: passages in v2.1 with no counterpart in v2 |
| `adjudication_page.html`, `adjudication_mapping.json` | The review page for one person, and the item-to-ID map |
| `adjudication.json` | The person's 26 decisions |

Model: Claude Opus 5.5, as a sub-agent. Each run was independent. The runs got the full documents.
The review was not blind: the person saw the model answers, their reasons, and a note on the Watchtower entry.
