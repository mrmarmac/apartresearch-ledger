## Meta v2 → v2.1: trace, new commitments, and review

Meta v2.1 is not in the upstream corpus. The ledger traced this pair itself. Files: `data/extension/meta/`.

| Step | Result |
|---|---|
| Text match | 82 of 104 commitments carried |
| Tracing, two model runs, full document | 18 counterparts, 4 none. Same passage in both runs for 16 of 18. Both runs agree on the 4 "none". |
| Direction, two model runs, full section | 12 kept, 6 weakened. 18 of 18 agreement between the runs. |
| New commitments, two model runs | 15 candidates. 14 in both runs, 1 in run 2 only. |
| Review by one person, not blind | 26 items: 6 weakened, 4 removed, 15 candidates, 2 tracing disagreements. He confirmed all 26. |

How to read this:

- The review is a confirmation. The person saw the two model answers, their reasons, and a note on the Watchtower entry. He did not code blind.
- 11 model-coded "kept" entries had no review by a person.
- There is no reference for new commitments in this pair. The recall test above gives the miss rate on 4 other pairs: 8 of 34.
- Comparison with Watchtower: 15 of 17 listed changes are in the ledger, and the other 2 are not commitments. See [`validation/watchtower_meta.md`](validation/watchtower_meta.md). The mapping is AI-made.
