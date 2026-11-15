# Task: code the direction of change for each commitment

You get one folder with four files:

- `old.txt`: the full earlier version of an AI developer's safety framework.
- `new.txt`: the full later version.
- `rules.md`: the coding rules. Read them completely before you start.
- `items.json`: a list of commitments. Each has `item`, `earlier_text` (the commitment in `old.txt`), `later_text` (its counterpart in `new.txt`) and `later_section`.

Use only these four files. Do not read any other file on this machine, and do not search the web.

For each item, decide the change to the OBLIGATION from the earlier version to the later version: R (retained, no material change), S (strengthened) or W (weakened; also for a mixed change).

Rules:
1. Apply `rules.md` exactly. Code the obligation, not the words.
2. Read the full section around each text in BOTH documents, not only the quoted text. The quoted texts are extracts.
3. Before you code a W because words are no longer in `later_text`, search ALL of `new.txt` for those words and their meaning. A phrase can move to a different sentence or section. If the obligation is still in `new.txt`, it is not weakened by that change. Record what you searched for in `searched`, and where moved text is now in `moved`.
4. Before you code an S because words are new in `later_text`, search ALL of `old.txt` in the same way.
5. If the extract in `later_text` has text that is clearly a page header, footer or footnote, ignore that text.

Output: write a JSON file at the path given below. A list with one element for each item, in the same sequence:

{"item": "<item>", "outcome": "<R|S|W>", "dims": [<numbers 1-6 of the materiality dimensions that changed>], "mixed": <true|false>, "searched": "<terms you searched for in the full documents>", "moved": "<text that moved, and where it is now, or empty>", "confidence": "<high|medium|low>", "reason": "<one or two sentences with the deciding words quoted>"}

Your final message: only the number of entries and the output path.
