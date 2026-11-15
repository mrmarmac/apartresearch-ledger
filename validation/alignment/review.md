### Review of the 12 disagreements

An AI assistant read each disagreement and sorted it. The author did not check this sorting yet.

| Type | Count | Items | Meaning |
|---|---|---|---|
| Same object, different sentence | 2 | oai08, oai12 | The two quotes are different sentences about the same thing (the evaluations programme, the Safety Advisory Group). Not a real disagreement. |
| Model found the notice of removal | 2 | oai11, oai16 | Upstream says "removed". The model points at the sentence in the later version that announces the removal (persuasion, safety drills). The two agree that the commitment is gone. |
| Upstream paired to a general passage, model said none | 3 | xai01, oai01, oai20 | Upstream treats a broad replacement as the counterpart and codes it weakened or kept. The model treats the commitment as removed. |
| Upstream said none, model found a candidate | 2 | xai02, oai03 | The model's candidate governs a similar object. For oai03 (external access for testing) the candidate looks like a real counterpart. |
| Different passages, both arguable | 3 | oai13, oai14, oai17 | The later version restructured the mechanism. More than one passage can be the counterpart. |

- **Strict agreement: 48 of 60 (80%).** If the first two types count as agreement: 52 of 60 (87%).
- **The disagreements are not spread evenly.** OpenAI Beta to v2 is a full rewrite, and it has 10 of the 12. Google DeepMind v3.0 to v3.1 is an incremental revision, and it has none.
- **"Removed" against "weakened" depends on the pairing.** In 3 cases the same change is "weakened" if a general passage counts as the counterpart, and "removed" if it does not. The Watchtower entry calls two such xAI changes "removed"; upstream codes them "weakened".
- **The model accepted the two pairings that the human coder rejected.** For `OAI-1-022` and `OAI-1-026` it found the same passage as upstream. So the model and upstream agree with each other, and the lawyer disagrees with both.
