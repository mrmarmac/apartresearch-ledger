# Prompt given to each model run

Three runs. Each run got one batch of 40 items (`batch_1.json`, `batch_2.json`, `batch_3.json`;
together they are `items.json`) and `rules.md`. `N` is the batch number.

```
You are a coder in a blind coding test. Work alone and carefully.

FILES YOU MAY READ (and no others):
- rules.md  (the coding rules)
- batch_N.json  (40 items)

STRICT LIMITS: Do not read, list or search any other file or directory. Do not use the web. Do not run code other than to write your output file. Do not spawn agents. Use only the two texts in each item and the rules. If you break these limits the test is void.

TASK: Each item is one safety-framework commitment of an AI developer in two consecutive versions of its framework: `earlier_text` (with `earlier_section`) and `later_text` (with `later_section`). The two texts are already matched as counterparts. For each item, decide the outcome code under the rules:
- R = Retained: no material change.
- S = Strengthened: at least one materiality dimension moves toward greater obligation, and no dimension moves the other way.
- W = Weakened: at least one materiality dimension moves the other way. If both directions are present, code W (rule 11.3).
Only R, S or W are valid here. Apply the materiality rule (section 5) and rules 11.1 to 11.3 exactly. Judge each item independently. Do not try to balance the number of each code.

OUTPUT: Write a JSON file out_N.json containing a JSON array with exactly one object per item, in the same order:
{"id": "<item id>", "outcome": "R" | "S" | "W", "dims": [<materiality dimension numbers 1-6 that changed, empty for R>], "confidence": "high" | "medium" | "low", "reason": "<one sentence, max 30 words, quoting the decisive words>"}
The file must be valid JSON and contain all 40 ids. Then reply with only the count of R, S and W.
```
