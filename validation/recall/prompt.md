# Task: find the commitments that are new in the later version

You get one folder with four files:

- `old.txt`: the earlier version of an AI developer's safety framework.
- `new.txt`: the later version.
- `scope.md`: what counts as a commitment, and the category codes.
- `definition.md`: what a "counterpart" is.

Read all four files completely. Use only these files. Do not read any other file on this machine, and do not search the web.

List each commitment in `new.txt` that has NO counterpart in `old.txt`.

Rules:
1. A commitment is a statement by the developer about its own practice, at any strength. A present-tense statement of practice is a commitment. A description of risk, a definition, or an aspiration for the field is not.
2. A counterpart is a passage in `old.txt` that governs the same category and the same object. New words, a new section or a new number do not make a commitment new. A commitment that is in `old.txt` in weaker, stronger or different words is NOT new.
3. Before you list a passage, search `old.txt` for its object with three or more different search terms. If you find a counterpart, do not list the passage.
4. One entry for each commitment. Do not join two commitments. Do not divide one commitment.
5. The quote must be verbatim from `new.txt`: copy the characters exactly, one continuous passage, 1 to 4 sentences.

Output: write a JSON file at the path given below. The content is a list. Each element:

{"quote": "<verbatim passage from new.txt>", "section": "<section heading in new.txt>", "category": "<EC1|EC2|EC3|EC4|EC5|EC6|G|S|M>", "why_new": "<what you searched for in old.txt and what you found>", "confidence": "<high|medium|low>"}

If there is no new commitment, write an empty list. Your final message: only the number of entries and the output path.
