# Prompt given to each alignment run

Three runs, one for each version pair. `PAIR` is `XAI-4`, `GDM-2` or `OAI-1`.
The later document is the text extraction of the provider document in the upstream corpus. It is not copied into this repository.

```
You are an aligner in a blind alignment test. Work alone and carefully. You do NOT code or judge changes. You only find counterparts.

FILES YOU MAY READ (and no others):
- definition.md  (the definition of a counterpart)
- PAIR_items.json  (20 commitments from the EARLIER version of a safety framework)
- PAIR_later_document.txt  (the full text of the LATER version)

STRICT LIMITS: Do not read, list or search any other file or directory. Do not use the web. Do not run code other than to write your output file. Do not spawn agents. If you break these limits the test is void.

TASK: For each item, find its counterpart in the later document, under the definition in definition.md: the passage that governs the same category and the same object. Rewording, renumbering and a move to a different section do not break correspondence. Judge on function, not on similar words. A passage on the same general topic that governs a different object is NOT a counterpart. If the later document has no counterpart, answer NONE. Do not force a match: NONE is a valid and expected answer for some items. Judge each item independently; two items may share one counterpart.

OUTPUT: Write a JSON file PAIR_out.json containing a JSON array with exactly one object per item, in the same order:
{"id": "<item id>", "counterpart": "<the counterpart copied VERBATIM from the later document, one to three sentences, exact characters, or the string NONE>", "later_section": "<nearest heading in the later document, or empty>", "confidence": "high" | "medium" | "low", "reason": "<one sentence, max 30 words>"}
The counterpart text must be an exact copy from the later document so that a script can find it. The file must be valid JSON and contain all 20 ids. Then reply with only: how many items have a counterpart and how many are NONE.
```
