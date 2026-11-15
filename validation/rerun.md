## Rerun of the Anthropic coding with the full documents

One error (entry e19) passed two model runs and a blind check by a person, because a phrase moved outside the extract that the model got. This test codes the same 47 entries again. Each run gets the two full documents and must search the full later document before it codes "weakened". Two independent runs. The runs did not see the earlier answers or the final codes. Reference: the final codes as they were before this rerun (29 kept, 14 weakened, 4 strengthened).

| | Extract, run 1 | Extract, run 2 | Full documents, run A | Full documents, run B |
|---|---|---|---|---|
| Same as the final code | 42 of 47 | 45 of 47 | 43 of 47 | 42 of 47 |
| Coded weakened | 14 | 15 | 15 | 19 |

| | Extract | Full documents |
|---|---|---|
| The two runs agree with each other | 43 of 47 | 42 of 47 |
| The two runs agree, and the code is the final code | 42 | 40 |

**Result: the full documents corrected the known error. They did not increase the agreement with the final codes.**

- **Entry e19** (`anthropic-third-party-cef3`, v3.2): the two extract runs coded "weakened". The two full-document runs code "strengthened", which is the final code. Each found the moved phrase.
- **Two entries where the two full-document runs agree with each other and not with the final code:** `anthropic-consequence-3e7e` and `anthropic-eval-scope-704a`, both v3.1. The final code is "strengthened". The two runs code "weakened", because they find a change in two directions, and the codebook codes a mixed change as weakened. The adjudicator then examined the two entries and changed both to "weakened" (mixed). The final codes are now 29 kept, 16 weakened, 2 strengthened. Against these codes, the agreement is 43 and 44 of 47 for the extract runs, and 45 and 44 of 47 for the full-document runs. That comparison is not independent, because the rerun caused the change.
- **Run B codes "weakened" more often** (19, against 14 in the final codes). Three of its "weakened" codes have no support from the other three runs.

How to read this: the reference favours the extract runs, because the adjudicator saw the extract answers on his second look. The test has 47 entries and one developer. It shows that the full-document method corrects the one known error of this type. It does not show a general gain.

Files: `data/extension/anthropic/rerun/`.
