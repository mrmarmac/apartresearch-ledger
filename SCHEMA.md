# Commitment Ledger schema

Machine-readable schema: [`schema.json`](schema.json) (JSON Schema, draft 2020-12).
Data: [`data/ledger.json`](data/ledger.json).
Schema version: `0.1.0`.

## Structure

```
ledger.json
├── schema_version
├── source          the upstream coding that the ledger is derived from
├── labs[]          coverage for each lab
├── versions[]      one record for each framework version
└── commitments[]   one record for each commitment
    └── history[]   one entry for each traced version
```

## Commitment

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable ID. See "ID rules". |
| `lab` | string | Lab slug: `xai`, `anthropic`, `google`, `meta`, `openai`. |
| `text` | string | The most recent verbatim text. |
| `topic` | enum | One of 9 topics. See "Topics". |
| `tags` | string[] | Keyword tags. Made by fixed rules, not by a model. |
| `current_status` | enum | See "Current status". |
| `merged_into` | string or null | The ID that continues this commitment. |
| `first_version_id` | string | First version in the history. |
| `last_version_id` | string | Last version in the history. |
| `history` | array | One or more history entries, oldest first. |

## History entry

| Field | Type | Meaning |
|---|---|---|
| `event_id` | string | `{commitment_id}@{version_id}`. Stable. It is the RSS GUID. |
| `version_id` | string | The version that this entry describes. |
| `status` | enum | The change from the previous traced version. See "Status". |
| `quote` | string or null | Verbatim text in this version. `null` when there is no counterpart. |
| `section` | string or null | Section heading in this version. |
| `section_changed` | boolean | The heading is different from the previous entry. A renamed heading also sets it. |
| `mixed` | boolean | Stronger in one dimension, weaker in a different dimension. Status is then `weakened`. |
| `material` | boolean or null | The upstream coder found a material change. |
| `disclosure` | enum or null | Did the developer's own account identify the change? See "Disclosure". |
| `confidence` | `high`, `medium`, `low` or null | Confidence grade from the upstream first pass. |
| `rationale` | string or null | The upstream coder's reason. |
| `link` | enum or null | How the ledger connected this entry to the previous entry. See "Links". |
| `gap_before` | boolean | One or more versions before this entry are not traced. |
| `quote_verified` | boolean or null | The quote is in the text extraction of the hashed document. |
| `source_row` | string or null | Row ID in the upstream sheet, for example `XAI-4-042`. |
| `source_url` | string | Where the document came from. |
| `wayback_timestamp` | string or null | 14-digit Wayback Machine capture time, when there is one. |
| `sha256` | string | SHA-256 of the document file as retrieved. |

## Status

`status` tells you what changed between the previous traced version and this version.

| Status | Meaning | Upstream code |
|---|---|---|
| `baseline` | The first version where the ledger sees the commitment. No change claim. | none |
| `added` | In this version. No counterpart in the previous version. | A |
| `kept` | Counterpart exists. No material change. The words can be different. | R |
| `strengthened` | One or more dimensions move to a larger obligation. No dimension moves the other way. | S |
| `weakened` | One or more dimensions move to a smaller obligation. Also used for mixed changes. | W |
| `removed` | No counterpart in this version. | X |
| `relocated` | The counterpart is now in a companion document or a non-binding section. | L |

The six materiality dimensions are scope, threshold or trigger, actor, obligation strength, disclosure scope, and consequence.
The full rules are in the upstream codebook, `codebook_v0.2_FROZEN.md`.

`relocated` does not mean "moved to a different section". For that, read `section_changed`.

## Current status

| Value | Meaning |
|---|---|
| `active` | In the last traced version of the lab. The site shows it as "In force". |
| `removed` | The last entry is `removed`. |
| `relocated` | The last entry is `relocated`. |
| `merged` | The upstream coder merged this row into a different row. Read `merged_into`. |
| `not_traced` | The ledger has no record after `last_version_id`. This is not a removal. |

**Read `labs[]` before you interpret `active`.** A lab can have later versions that the ledger does not trace.

## Disclosure

| Value | Meaning |
|---|---|
| `announced` | The developer's account identifies this change and its direction. |
| `partly_announced` | The account identifies the commitment or its class, but not the direction or substance. |
| `silent` | The developer published an account. It does not identify this change. |
| `no_account` | The developer published no account of this revision. |
| `not_applicable` | No material change. |

## Links

The upstream sheet gives a commitment a new row ID in each version pair.
The ledger connects those rows. `link` records the method.

| Value | Meaning |
|---|---|
| `same_row` | The previous entry and this entry come from one upstream row. |
| `prior_id` | The upstream sheet names the earlier row in its notes. |
| `exact_text` | The earlier text and the later text are identical after normalisation. |
| `fuzzy_text` | Similarity of 0.9 or more (Python `difflib`), best match only. |
| `null` | First entry of the history. |

Normalisation for comparison: lower case, letters and digits only. Stored quotes do not change.

## ID rules

Commitment ID: `{lab}-{topic}-{hash}`. Example: `xai-governance-673f`.

- `lab` is the lab slug. It does not change when the company changes its name.
- `topic` is the topic at first appearance.
- `hash` is the first 4 hexadecimal characters of
  `sha256("{lab}|{first_version_id}|{normalised first quote}")`.
  If two IDs collide, the later one gets one more character.
- The ID is assigned at first appearance. A later change of text or topic does not change it.

Version ID: `{lab}-{version label}`. Example: `xai-2026-06-30`, `anthropic-v3.0`.
A file that the developer published again under the same label is in `reuploads`, not a new version.

Event ID: `{commitment_id}@{version_id}`. Example: `xai-governance-673f@xai-2026-06-30`.

## Topics

| Topic | Covers | Upstream code |
|---|---|---|
| `eval-scope` | Which capabilities or risk domains are evaluated | EC1 |
| `eval-trigger` | When evaluations occur, and thresholds | EC2 |
| `eval-method` | How evaluations are done | EC3 |
| `third-party` | External evaluation, audit, government access | EC4 |
| `disclosure` | What is published, to whom, when | EC5 |
| `consequence` | What action a result requires | EC6 |
| `governance` | Decision bodies, officers, whistleblowing, review | G |
| `security` | Weight security, access controls | S |
| `mitigation` | Safeguards, monitoring, staged deployment | M |

## Example record

Full file: [`examples/whistleblower.json`](examples/whistleblower.json). Shortened here.

```json
{
  "id": "xai-governance-673f",
  "lab": "xai",
  "text": "xAI employees have whistleblower protections enabling them to raise concerns to relevant government agencies regarding imminent threats to public safety.",
  "topic": "governance",
  "tags": ["regulators", "whistleblower"],
  "current_status": "removed",
  "merged_into": null,
  "first_version_id": "xai-draft-2025-02-10",
  "last_version_id": "xai-2026-06-30",
  "history": [
    { "event_id": "xai-governance-673f@xai-draft-2025-02-10", "version_id": "xai-draft-2025-02-10", "status": "baseline", "...": "..." },
    { "event_id": "xai-governance-673f@xai-draft-2025-02-20", "version_id": "xai-draft-2025-02-20", "status": "kept", "...": "..." },
    { "event_id": "xai-governance-673f@xai-2025-08-20", "version_id": "xai-2025-08-20", "status": "kept", "...": "..." },
    { "event_id": "xai-governance-673f@xai-2025-12-30", "version_id": "xai-2025-12-30", "status": "kept", "...": "..." },
    {
      "event_id": "xai-governance-673f@xai-2026-06-30",
      "version_id": "xai-2026-06-30",
      "status": "removed",
      "quote": null,
      "section": null,
      "material": true,
      "disclosure": "no_account",
      "confidence": "high",
      "link": "prior_id",
      "source_row": "XAI-4-042",
      "sha256": "2c3c6313bd2fb6eeffcafedb38013c34d92c53331ddedbfa331821c75055df53"
    }
  ]
}
```

## Feed

`feed.xml` is RSS 2.0. It has one item for each entry with status
`added`, `strengthened`, `weakened`, `removed` or `relocated`.

- `guid` is the `event_id`. It does not change between builds.
- `pubDate` is the publication date of the framework version. It is not the date when the change was found.
- `link` goes to the commitment page, at the anchor of the version.
