# Task: find the counterpart of each commitment in the later version, and code the change

Your folder has these files:

- `old.txt`: the full earlier version of an AI developer's safety framework.
- `new.txt`: the full later version. It is a full rewrite of the earlier version.
- `definition.md`: what a counterpart is.
- `rules.md`: the coding rules. Read them completely before you start.
- one items file (its name is given below): a list of commitments from `old.txt`. Each has `item`, `earlier_section`, `earlier_text`.

Use only these files. Do not read any other file on this machine, and do not search the web.

For each item:

1. Read the full section around `earlier_text` in `old.txt`.
2. Search ALL of `new.txt` for the counterpart: the passage that governs the same category and the same object. New words, a new section or a new structure do not break correspondence. Use three or more different search terms. Record them in `searched`.
3. If there is a counterpart, copy it verbatim from `new.txt` (one continuous passage, 1 to 4 sentences, exact characters) and code the change to the OBLIGATION: R (retained), S (strengthened) or W (weakened; also for a mixed change). Apply `rules.md` exactly.
4. If `new.txt` has no counterpart, the outcome is X and `counterpart` is null. Use X only after the search. A general statement in `new.txt` that does not govern the same object is not a counterpart.
5. Do not guess. If you find a passage but you are not sure that it governs the same object, give it, and set `confidence` to low.

Output: write a JSON file at the path given below. A list with one element for each item, in the same sequence:

{"item": "<item>", "counterpart": "<verbatim passage from new.txt, or null>", "section": "<section heading in new.txt, or null>", "outcome": "<R|S|W|X>", "dims": [<numbers 1-6 of the materiality dimensions that changed>], "mixed": <true|false>, "searched": "<terms you searched for in new.txt>", "confidence": "<high|medium|low>", "reason": "<one or two sentences with the deciding words quoted>"}

Your final message: only the number of entries and the output path.
