## Alignment test: find the counterpart

**Question.** A method gets one commitment from the earlier version and the full text of the later version. Does it find the same counterpart as the upstream coding, or correctly find none?

### Method

- **Sample:** 60 commitments from 3 version pairs, 20 for each pair. Random, seed 20261117. For each pair, up to 6 commitments with no upstream counterpart are included first. Two rows (`OAI-1-022`, `OAI-1-026`) are included on purpose: the human coder rejected their pairing.
- **Model:** Claude Opus 5.5 (sub-agent). One sub-agent for each pair. Input: the 20 earlier texts, the full later document, and section 3 of the upstream codebook (`validation/alignment/definition.md`).
- **Not given to the model:** the coding rules, the upstream counterpart, the outcome code, or the row ID.
- **Text matching:** the most similar window of one or two sentences in the later document (Python `difflib`). A ratio below 0.6 means no counterpart.
- **Same passage:** the two quotes share a run of identical characters of 40% of the shorter quote or more (30 characters minimum).
- **Scoring:** `python run.py align`.

### Result

**Model: 48 of 60 agree with upstream (80%). Text matching: 37 of 60 (62%).**

| Case | Model | Text matching |
|---|---|---|
| Upstream has a counterpart. Method found the same passage | 42 | 27 |
| Upstream has a counterpart. Method found a different passage | 5 | 0 |
| Upstream has a counterpart. Method said none | 3 | 23 |
| Upstream has none. Method said none | 6 | 10 |
| Upstream has none. Method found one | 4 | 0 |

| Version pair | Model agrees | Text matching agrees |
|---|---|---|
| xAI, 30 Dec 2025 to 30 Jun 2026 | 18 of 20 | 14 of 20 |
| Google DeepMind, v3.0 to v3.1 | 20 of 20 | 16 of 20 |
| OpenAI, Beta to v2 | 10 of 20 | 7 of 20 |

| Upstream outcome of the row | Model agrees | Text matching agrees |
|---|---|---|
| kept | 20 of 24 | 18 of 24 |
| strengthened | 9 of 9 | 4 of 9 |
| weakened | 13 of 19 | 7 of 19 |
| removed | 6 of 8 | 8 of 8 |

**Quote check:** 51 of 51 model quotes are in the later document text.

**The two pairings that the human coder rejected:**

- `OAI-1-026`: the model found the same passage as upstream.
- `OAI-1-022`: the model found the same passage as upstream.

### Cases where the model and upstream do not agree

| Item | Upstream row | Case | Earlier text | Upstream counterpart | Model counterpart | Model's reason |
|---|---|---|---|---|---|---|
| xai01 | `XAI-4-017` | Method said none | Thresholds: We developed an internal benchmark of benign and restricted biology and chemistry related queries in collaboration with SecureBio. Our risk acceptance criter… | xAI applies a systemic risk acceptance criteria to each identified risk, incorporating a margin of security, to determine whether each identified systemic risk and the o… | none | The SecureBio benchmark and the under 1-in-20 answer-rate acceptance threshold are gone; only generic acceptance criteria remain. |
| xai02 | `XAI-4-015` | Method found one | In the setting of biological and chemical weapons, xAI considers critical steps where we restrict xAI models from providing detailed information or substantial assistanc… | none | Under this FAIF, xAI’s models apply heightened safeguards if they receive user prompts that demonstrate intent to engage in the development, use, , or proliferation of w… | Governs the same object: restricting model assistance toward chem/bio weapons steps, now framed as heightened CBRN safeguards. |
| oai01 | `OAI-1-004` | Method said none | Tasking the Preparedness team with on-the-ground work. The team will drive the technical work and maintenance of the Preparedness Framework. This includes conducting res… | Our team develops or adopts evaluations designed to track progress on each of these capabilities and to indicate when the identified capability thresholds may have been … | none | Later version no longer assigns a Preparedness team the research, monitoring, forecasting and regular reporting role to SAG. |
| oai03 | `OAI-1-040` | Method found one | External access: We will also continue to enable external research and government access for model releases to increase the depth of red-teaming and testing of frontier … | none | • Third-party evaluation of tracked model capabilities: If we deem that a deployment warrants deeper testing of Tracked Categories of capability (as described in Section… | Governs external third-party testing of frontier model capabilities, now conditional on discretion and availability. |
| oai08 | `OAI-1-001` | Method found a different passage | We will be building and continually improving suites of evaluations and other monitoring solutions along several Tracked Risk Categories, and indicating our current leve… | We invest deeply in developing or adopting new science-backed evaluations that provide high precision and high recall indications of whether a covered system has reached… | Our team develops or adopts evaluations designed to track progress on each of these capabilities and to indicate when the identified capability thresholds may have been … | Same commitment to build evaluations per tracked category; the Scorecard reporting element is gone. |
| oai11 | `OAI-1-013` | Method found one | Persuasion is focused on risks related to convincing people to change their beliefs (or act on) both static and interactive model-generated content. ... Note that we inc… | none | Going forward we will handle risks related to persuasion outside the Preparedness Framework, including via our Model Spec and policy prohibitions on the use of our tools… | Governs the persuasion risk category, explicitly removing it from the Framework. |
| oai12 | `OAI-1-006` | Method found a different passage | We are creating a Safety Advisory Group (SAG) that brings together expertise from across the company to help OpenAI’s leadership and Board of Directors be best prepared … | The Safety Advisory Group (SAG) is responsible for: • Overseeing the effective design, implementation, and adherence to the Preparedness Framework in partnership with th… | An internal, cross-functional group of OpenAI leaders called the Safety Advisory Group (SAG) oversees the Preparedness Framework and makes expert recommendations on the … | Same establishment and remit of the Safety Advisory Group. |
| oai13 | `OAI-1-025` | Method found a different passage | Our mitigation strategy will involve both containment measures, which help reduce risks related to possession of a frontier model, as well as deployment mitigations, whi… | We consider separate safeguards for two of the main ways in which risks can be realized: a malicious user, who can leverage the model to cause the severe harm, and a mis… | Covered systems that cross this capability threshold are required to have robust and effective safeguards that sufficiently minimize the associated risk of severe harm b… | Two-part mitigation structure persists as deployment safeguards plus security controls during development (containment). |
| oai14 | `OAI-1-029` | Method found a different passage | Additionally, to protect against “critical” pre-mitigation risk, we need dependable evidence that the model is sufficiently aligned that it does not initiate “critical”-… | If a model has High or Critical capabilities in any of the Tracked Categories, require a “misalignment” safeguards report (see Section 4.2). | Our approach to Critical capabilities will need to be robust to both malicious actors (either internal or external) and model misalignment risks. | Governs misalignment protection required at Critical level; the dependable alignment evidence requirement is softened. |
| oai16 | `OAI-1-041` | Method found one | Therefore, the SAG will call for safety drills at a recommended minimum yearly basis | none | 10. Deprioritize safety drills, as we are shifting our attention to a more durable approach of continu- ously red-teaming and assessing the effectiveness of our safeguar… | Governs the same safety drills commitment, explicitly deprioritizing it. |
| oai17 | `OAI-1-020` | Method found a different passage | We will be running these evaluations continually, i.e., as often as needed to catch any non-trivial capability change, including before, during, and after training. This… | If justified by our forecasts and threat models as potentially posing a severe risk during development and prior to external deployment, we will select an appropriate ch… | The Preparedness Framework applies to any new or updated deployment that has a plausible chance of reaching a capability threshold whose corresponding risks are not addr… | Governs when evaluations are triggered; replaces continual and >2x compute triggers with deployment-based scope. |
| oai20 | `OAI-1-018` | Method said none | Our procedural commitments are triggered when any of the tracked risk categories increase in severity, rather than only when they all increase together. | Covered systems that cross this capability threshold are required to have robust and effective safeguards that sufficiently minimize the associated risk of severe harm b… | none | Later version contains no explicit statement that procedural commitments trigger when any single category increases. |

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

### Limits

1. **The upstream counterpart is not ground truth.** A disagreement can be an upstream error. The human check found 3 doubtful pairings in 20.
2. **"Same passage" is a text rule.** Two adjacent sentences of one paragraph can count as different passages. I read each disagreement; see the notes below the table.
3. **Three version pairs, 60 items, one run.**
4. **Few items with no counterpart** (10 of 60). The figure for removed commitments has a wide interval.
5. **Isolation was by instruction**, as in the direction test.
6. **The test goes one way only.** It does not test if a method finds commitments that are new in the later version.
