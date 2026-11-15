# Validation: a model against the upstream codes

**Question.** The ledger gives a model two versions of one commitment. Does the model give the same code as the upstream coding: kept, strengthened or weakened?

This test is for the future. A new framework version needs a classifier. The seed data in `data/ledger.json` does not use this model.

## Method

- **Gold standard:** final codes in `coding/tracing_FINAL_v3.csv` of the upstream corpus (commit `11cbeda80c5c`).
- **Pool:** rows of the 5 ledger labs with text in both versions: 190 kept, 59 strengthened, 107 weakened. Rows that the upstream codebook uses as worked examples are not in the pool.
- **Sample:** 40 rows for each code, 120 in total. Random, seed 20261115. Mixed sequence.
- **Model:** Claude Opus 5.5 (sub-agent), in 3 independent runs of 40 items.
- **Input to the model:** the two texts, their section headings, the developer name, and `validation/rules.md` (sections 4, 5 and 11.1 to 11.3 of the upstream codebook).
- **Not given to the model:** the upstream code, the rationale, the row ID, or the source documents.
- **Scoring:** `python run.py score`. The script makes the key again from the seed.

## Result

**Agreement: 105 of 120 (88%, 95% CI 80 to 92). Cohen's kappa: 0.81.**

**Opposite direction** (strengthened against weakened): 7 of 120. This is the most important error type for a ledger.

| Upstream code | Model: kept | Model: strengthened | Model: weakened | Recall |
|---|---|---|---|---|
| kept | 36 | 2 | 2 | 90% |
| strengthened | 3 | 33 | 4 | 82% |
| weakened | 1 | 3 | 36 | 90% |
| **Precision** | 90% | 87% | 86% | |

The sample has the same number of rows for each code. The pool does not. Thus the agreement figure is not the agreement that you get on a full framework revision.

## Agreement by row type

| Row type | Agreement |
|---|---|
| Upstream coding was stable (all re-runs agreed) | 67 of 73 (92%, 95% CI 83 to 96) |
| Upstream coding was disputed and re-examined | 38 of 47 (81%, 95% CI 67 to 90) |
| Upstream confidence high | 42 of 45 (93%, 95% CI 82 to 98) |
| Upstream confidence medium | 46 of 55 (84%, 95% CI 72 to 91) |
| Upstream confidence low | 17 of 20 (85%, 95% CI 64 to 95) |
| Mixed change (stronger and weaker) | 11 of 14 (79%, 95% CI 52 to 92) |
| xAI | 38 of 42 (90%, 95% CI 78 to 96) |
| Anthropic | 26 of 28 (93%, 95% CI 77 to 98) |
| Google DeepMind | 18 of 25 (72%, 95% CI 52 to 86) |
| Meta | 9 of 10 (90%, 95% CI 60 to 98) |
| OpenAI | 14 of 15 (93%, 95% CI 70 to 99) |

## Disagreements

| Item | Upstream row | Upstream | Model | Model's reason |
|---|---|---|---|---|
| q008 | `OAI-1-026` | strengthened | weakened | Forecast trigger "(or are forecasted to reach)" dropped; later applies only to systems that "cross this capability threshold". |
| q019 | `XAI-4-036` | strengthened | weakened | Drops "sufficient to prevent... stolen by a motivated non-state actor" and distillation measures; adds "NIST 800-171" and "SOC 2" (MIX). |
| q024 | `XAI-3-001` | strengthened | kept | Renaming to "FAIF" and adding "including catastrophic risks" within "significant risks" does not change coverage. |
| q039 | `GDM-2-030` | weakened | strengthened | Illustrative "may be triggered, for example" becomes fixed trigger: assessments "upon the completion of a post-training run". |
| q045 | `ANT-1-005` | weakened | strengthened | Pause commitment kept ('will pause training') and resumption now also requires having 'established it is sufficient for the model'. |
| q046 | `GDM-2-022` | strengthened | kept | Threshold text essentially identical ('work out' to 'discover'); only relabelled from exploratory CCL to 'Stealth and Situational Awareness TCL'. |
| q047 | `GDM-1-013` | strengthened | weakened | 'applied to models reaching a CCL' narrowed to 'external deployments' for misuse CCLs, though ML R&D adds 'large scale internal deployments'. |
| q063 | `META-1-028` | weakened | kept | 'significant uplift towards execution of a threat scenario' reworded as 'could substantially contribute to any threat scenario'; threshold level appears equivalent. |
| q069 | `XAI-2-017` | kept | weakened | 'evaluation and mitigation plans ... intend to improve' narrowed to 'developing naturalistic evaluation environments', dropping mitigation. |
| q072 | `GDM-1-022` | weakened | strengthened | 'fully automate the AI R&D pipeline' lowered to automating 'the work of any team of researchers at Google'. |
| q093 | `ANT-1-021` | kept | strengthened | "data should similarly be filtered" becomes present-tense standing commitment "data is filtered for harmfulness". |
| q097 | `XAI-4-047` | strengthened | weakened | Adds gate "will only proceed ... if systemic risks ... acceptable" but drops "Pre-deployment reviews include assessing benchmark results" and internal oversight-evasion review; mixed (MIX). |
| q098 | `GDM-2-020` | strengthened | kept | Both versions remain field recommendations ("We recommend", "define and recommend"), not self-commitments; no change in obligation. |
| q113 | `GDM-2-006` | kept | strengthened | Core retained and adds "we strive to learn from our post-market monitoring mechanisms, including ... incidents". |
| q115 | `GDM-2-025` | kept | weakened | Review scope changes from "systemic risk" to "significant and severe risk", plausibly narrower; conservative call. |

## Limits

1. **The gold standard is not ground truth.** A language model helped with the upstream first pass. One human author adjudicated. Agreement thus shows consistency with that coding. It does not show that the code is correct.
2. **This test does not include alignment.** The model gets a matched pair. To find the counterpart of a commitment in a new version is a different, harder step.
3. **This test does not include Added, Removed or Relocated.** Those codes depend on alignment, not on direction.
4. **Isolation was by instruction.** The model ran as a sub-agent with file tools. The instructions told it to read only its batch file and the rules. Each run made 4 tool calls, which agrees with: read rules, read batch, write answers, report.
5. **Two runs only.** See the stability section. Two runs give a first estimate of how much the model changes, not a distribution.
6. **The sample is 120 rows.** Read the confidence intervals.
7. **The model is a high-capability model.** A low-cost model was not tested. Its agreement can be lower.

## Stability: a second run of the same model

Same model, same items, same prompt, new sub-agents. Answers are in `validation/predictions_run2/`.

| Comparison | Agreement | Cohen's kappa |
|---|---|---|
| Run 2 against upstream | 104 of 120 (87%) | 0.80 |
| Run 1 against run 2 | 113 of 120 (94%) | 0.91 |

- The model changed its answer on 7 of 120 items. 2 of those changes went to the opposite direction.
- On the 113 items with the same answer in the two runs, the model agrees with upstream on 102 (90%).
- A practical rule follows: run the model two times and send each item with two different answers to a person.

| Item | Upstream row | Upstream | Run 1 | Run 2 |
|---|---|---|---|---|
| q045 | `ANT-1-005` | weakened | strengthened | kept |
| q048 | `ANT-2-024` | weakened | weakened | strengthened |
| q063 | `META-1-028` | weakened | kept | strengthened |
| q090 | `XAI-3-008` | weakened | weakened | kept |
| q097 | `XAI-4-047` | strengthened | weakened | strengthened |
| q115 | `GDM-2-025` | kept | weakened | kept |
| q117 | `GDM-2-033` | kept | kept | weakened |

## Human check: one lawyer, 20 items

**Coder:** M.R. (author, lawyer). One person, no second human coder.

**Design.** 20 of the 120 items: 10 drawn at random from the items where model run 1 agreed with upstream, and 10 drawn at random from the 15 items where it disagreed (seed 20261116). Mixed sequence. The coder did not see the upstream code, the model answers, or which group an item was in. The page (`validation/human/page.html`) showed the two texts, the headings, the developer name and a summary of the rules.

**This is not a random sample of the 120.** Half of the items are disputed on purpose. Read the two groups separately. Do not combine them into one accuracy figure.

**Coded: 17 of 20.** The coder did not code 3 items, because he did not accept that the two texts refer to the same commitment.

| Group | Coded | Human = upstream | Human = model | Human = neither |
|---|---|---|---|---|
| Model agreed with upstream | 9 | 7 | 7 | 2 |
| Model disagreed with upstream | 8 | 4 | 2 | 2 |

Observations:

- **Where the model and upstream disagree, the human agrees with upstream more often than with the model, but the numbers are very small.**
- **The human selects Kept more often:** 11 of 17, against 8 of 17 for upstream on the same items. The human has a higher bar for a material change.
- **Opposite direction:** human against upstream, 1 of 17. Human against model, 3 of 17.
- **Alignment doubt:** the coder rejected the pairing of 3 of 20 items. The upstream coding re-examined all of them as disputed. This supports limit 2 below: alignment is the weak step, and this test does not measure it.

| Item | Upstream row | Group | Human | Upstream | Model run 1 |
|---|---|---|---|---|---|
| h01 (q075) | `ANT-1-013` | agreed | kept | kept | kept |
| h02 (q092) | `XAI-4-007` | agreed | kept | kept | kept |
| h03 (q046) | `GDM-2-022` | disagreed | kept | strengthened | kept |
| h04 (q030) | `OAI-1-022` | agreed | not coded: pairing rejected | weakened | weakened |
| h05 (q051) | `GDM-2-028` | agreed | kept | kept | kept |
| h06 (q045) | `ANT-1-005` | disagreed | weakened | weakened | strengthened |
| h07 (q047) | `GDM-1-013` | disagreed | kept | strengthened | weakened |
| h08 (q115) | `GDM-2-025` | disagreed | weakened | kept | weakened |
| h09 (q069) | `XAI-2-017` | disagreed | not coded: pairing rejected | kept | weakened |
| h10 (q093) | `ANT-1-021` | disagreed | kept | kept | strengthened |
| h11 (q049) | `ANT-1-064` | agreed | weakened | weakened | weakened |
| h12 (q097) | `XAI-4-047` | disagreed | strengthened | strengthened | weakened |
| h13 (q094) | `XAI-3-024` | agreed | kept | kept | kept |
| h14 (q002) | `GDM-2-016` | agreed | kept | kept | kept |
| h15 (q059) | `ANT-1-039` | agreed | weakened | weakened | weakened |
| h16 (q031) | `ANT-1-059` | agreed | kept | strengthened | strengthened |
| h17 (q084) | `OAI-1-014` | agreed | strengthened | weakened | weakened |
| h18 (q039) | `GDM-2-030` | disagreed | kept | weakened | strengthened |
| h19 (q113) | `GDM-2-006` | disagreed | kept | kept | strengthened |
| h20 (q008) | `OAI-1-026` | disagreed | not coded: pairing rejected | strengthened | weakened |

Limits of the human check: one coder. The coder is the author of this project and is not independent of it. 17 items. The coder took about 8 minutes for the 17 items, which is about 30 seconds for each item. The coder used a summary of the rules, not the full codebook.

## Human check of the Anthropic extension: 47 model-coded entries

**Coder:** M.R. (author, lawyer). One person. Blind: the page showed the two texts, the version pair and the text around the later passage. It did not show the model's code or the commitment ID. Random sequence. Five answers: kept, strengthened, weakened, not the same thing, cannot tell. Page: `data/extension/anthropic/human_check_page.html`.

**Result: the human agrees with the model on 34 of 44 decided entries (77%, Cohen's kappa 0.54). Opposite direction: 5 of 44.** Not decided: 1 "not the same thing", 2 "cannot tell".

Where the two model runs agree with each other (42 decided entries), the human agrees with them on 34 (81%).

| Model run 1 | Human: kept | Human: strengthened | Human: weakened | Human: not the same thing | Human: cannot tell |
|---|---|---|---|---|---|
| kept (31) | 27 | 1 | 0 | 1 | 2 |
| strengthened (2) | 0 | 1 | 1 | 0 | 0 |
| weakened (14) | 4 | 4 | 6 | 0 | 0 |

- **The model codes "weakened" more often than the human.** Of the 14 entries that the model coded weakened, the human coded 6 weakened, 4 kept and 4 strengthened.
- **The ledger does not overwrite the model code.** An entry where the human agrees has `human_check: agrees`. Each other entry has `needs_review: true` and records the human answer.
- **The blind disagreements are adjudicated below.**

| Item | Commitment | Version | Model run 1 | Model run 2 | Human | Model's reason |
|---|---|---|---|---|---|---|
| e01 | `anthropic-security-06a3` | v3.3 | kept | kept | cannot tell | Extract cut at 'maintain logs' by column extraction; no wording change shown in 'Achieve an eyes on everything state'. |
| e09 | `anthropic-governance-d559` | v3.4 | weakened | weakened | strengthened | Disclosure narrowed from mitigations 'we are implementing' to those 'we have implemented as of the coverage date', excluding ongoing work and later developments. |
| e14 | `anthropic-consequence-9c90` | v3.3 | weakened | weakened | strengthened | Trigger raised from 'significantly help threat actors (... moderately resourced ...)' to 'functionally substitute for' expertise of 'world-leading specialists' for a 'well-resourced team'. |
| e16 | `anthropic-security-d7b4` | v2.2 | kept | kept | strengthened | Same 'Aligning where appropriate with existing guidance' list; footnote text interleaved by extraction, standards list continues after page break. |
| e19 | `anthropic-third-party-cef3` | v3.2 | weakened | weakened | kept | 'In consultation with the Board and LTBT, we will select external reviewers' becomes 'We will select external reviewers', removing Board/LTBT involvement. |
| e25 | `anthropic-eval-scope-704a` | v3.1 | weakened | kept | strengthened | Internal-model comparator changed from 'those posed by our public models' to 'models that are covered by a prior Risk Report', potentially excluding some internal models. |
| e26 | `anthropic-consequence-3e7e` | v3.1 | kept | strengthened | not the same thing | 'We will: Resource and complete significant moonshot R&D for security' unchanged; revised trigger wording is truncated in context and cannot be verified. |
| e29 | `anthropic-security-8ada` | v2.2 | weakened | weakened | strengthened | Out-of-scope insiders broadened from 'highly sophisticated state-compromised' to 'sophisticated or state-compromised', defined as anyone with 'persistent access or can request time-limited access'. |
| e34 | `anthropic-eval-trigger-5482` | v2.1 | kept | weakened | cannot tell | Assessment moved to 'in parallel with upgrading', but Section 6.1 still requires confirming model 'sufficiently far away from the next set of Capability Thresholds' before deploying. |
| e40 | `anthropic-third-party-38ba` | v3.1 | weakened | weakened | kept | 'Separate internal reviewers will provide' becomes 'We will solicit comprehensive internal feedback'; external feedback sentence unchanged. |
| e41 | `anthropic-consequence-a1d2` | v2.1 | weakened | weakened | kept | 'update our list of Capability Thresholds to consider additional risks' replaced by 'begin testing for ... any additional risks'; context only says 'we may identify additional thresholds'. |
| e45 | `anthropic-governance-4adb` | v3.1 | weakened | weakened | kept | 'Separate internal reviewers will provide comprehensive feedback' becomes 'We will solicit comprehensive internal feedback', dropping reviewer separateness and guaranteed feedback. |
| e46 | `anthropic-eval-trigger-efa4` | v2.1 | strengthened | weakened | weakened | AI R&D-5 now requires 'At minimum, the ASL-4 Security Standard' (was ASL-3), and AI R&D-4 adds 'we will develop an affirmative case' on misalignment. |

### Adjudication: a second look at the entries without agreement

**Method.** Second look, not blind. The adjudicator saw both texts, the context, the two model answers with reasons, and his first answer. Page: `data/extension/anthropic/adjudication_page.html`. 13 entries adjudicated. 0 held open.

| Group | Entries | Final = model run 1 | Final = model run 2 | Final = first human answer |
|---|---|---|---|---|
| The two model runs agreed | 9 | 8 | 8 | 0 |
| The two model runs disagreed | 4 | 1 | 2 | 1 |

- **Where the two model runs agreed, the adjudicated code is the model code in 8 of 9 adjudicated entries.** With the 34 entries where the blind check agreed, that is 42 of 43 decided entries.
- **One error passed two model runs (e19).** The two runs coded weakened, because a phrase was gone from the start of the passage. The phrase had moved to a new final sentence, outside the text that the model got, and it was stronger there. The blind human answer (kept) was also wrong. The error was found only when the full section was read.
- **Where the two model runs disagreed, the final code differs from model run 1 in 3 of 4 entries.** The rule "run two times, send disagreements to a person" finds most errors, but not each one.
- **The blind first answers were less reliable than the second look.** The adjudicator changed his own first answer in 12 of 13 adjudicated entries.
- Not coded on second look: none. Held open: none.
- **The second look was not blind.** The adjudicator saw the model's reasons. Agreement with the model after that is weaker evidence than blind agreement.

| Item | Commitment | Version | Model run 1 | Model run 2 | First human answer | Final |
|---|---|---|---|---|---|---|
| e14 | `anthropic-consequence-9c90` | v3.3 | weakened | weakened | strengthened | weakened |
| e29 | `anthropic-security-8ada` | v2.2 | weakened | weakened | strengthened | weakened |
| e01 | `anthropic-security-06a3` | v3.3 | kept | kept | cannot tell | kept |
| e09 | `anthropic-governance-d559` | v3.4 | weakened | weakened | strengthened | weakened |
| e16 | `anthropic-security-d7b4` | v2.2 | kept | kept | strengthened | kept |
| e19 | `anthropic-third-party-cef3` | v3.2 | weakened | weakened | kept | strengthened |
| e25 | `anthropic-eval-scope-704a` | v3.1 | weakened | kept | strengthened | weakened |
| e26 | `anthropic-consequence-3e7e` | v3.1 | kept | strengthened | not the same thing | weakened |
| e34 | `anthropic-eval-trigger-5482` | v2.1 | kept | weakened | cannot tell | weakened |
| e40 | `anthropic-third-party-38ba` | v3.1 | weakened | weakened | kept | weakened |
| e41 | `anthropic-consequence-a1d2` | v2.1 | weakened | weakened | kept | weakened |
| e45 | `anthropic-governance-4adb` | v3.1 | weakened | weakened | kept | weakened |
| e46 | `anthropic-eval-trigger-efa4` | v2.1 | strengthened | weakened | weakened | weakened |

Limits: one coder, who is the author and is not independent. The coder took about 28 minutes for 47 entries, which is about 36 seconds for each entry of about 900 characters plus context. The later text comes from a PDF extraction, and some extracts are cut by a page break. The coder used a summary of the rules.

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

## Second check: one Watchtower entry

**Question.** Watchtower describes the xAI revision of 30 June 2026 in prose. Does the ledger have each change, in the same direction?

**Source.** [Watchtower, xAI, 11 July 2026](https://www.themidasproject.com/watchtower/xai-07112026), read on 15 November 2026.

**Method.** One person divided the entry into sub-changes by hand, and then searched the ledger for each one. This check uses the seed data. It does not use a model.

| # | Watchtower sub-change | Ledger commitment | Ledger status | Found |
|---|---|---|---|---|
| 1 | Whistleblower protection clause removed | `xai-governance-673f` | removed | Yes |
| 2 | Anonymous internal report channel removed | `xai-governance-0724` | removed | Yes |
| 3 | References to California's TFAIA removed | `xai-governance-291c` | removed | Yes |
| 4 | The term "catastrophic risk" removed | `xai-governance-5bc2` | weakened | Yes |
| 5 | MASK honesty criterion removed | `xai-mitigation-6d2e` | weakened | Yes |
| 6 | Biology and chemistry answer-rate criterion removed | `xai-mitigation-7539` | weakened | Yes |
| 7 | Named benchmarks replaced with "may utilize" | `xai-eval-method-d279` | weakened | Yes |
| 8 | Honesty and instruction-hierarchy training statement removed | `xai-mitigation-68cf` | weakened | Yes |
| 9 | System-prompt instruction not to deceive removed | `xai-mitigation-68cf` | weakened | Yes |
| 10 | "Public transparency and third-party review" section removed | `xai-disclosure-f8c3` | removed | Yes |
| 11 | New information security detail (NIST 800-171, SOC 2) | `xai-security-adf9` | strengthened | Yes |
| 12 | New annual full systemic risk assessment | `xai-eval-trigger-cebf` | added | Yes |
| 13 | Incident reports to authorities when the law requires | `xai-governance-9e90` | strengthened | Yes |
| 14 | New paragraph on loss-of-control practice | `xai-mitigation-d832` | strengthened | Yes, see note |
| 15 | Statement removed: a model can change its behaviour in an evaluation | none | none | No |
| 16 | Statement removed: AIs can develop misaligned value systems | none | none | No |
| 17 | New "Harmful Manipulation Risks" domain | none | none | No |

**Result: 14 of 17 sub-changes are in the ledger (82%). For all 14, the direction agrees or is compatible.**

Notes:

- **Rows 5 and 6.** Watchtower says "removed". The ledger says "weakened", because the upstream coder found a qualitative replacement. The direction is the same.
- **Row 14.** Watchtower says that the new paragraph has no commitment, evaluation or trigger. The ledger records it two times: as "strengthened" against a vague earlier sentence, and as "weakened" against the specific training statement (rows 8 and 9).
- **Rows 15 and 16** are admissions, not commitments. The upstream codebook traces commitments only. A ledger of commitments will not have them.
- **Row 17** is a true miss. A new risk domain is a change of scope.
- **Not in the test:** the AB 2013 training-data disclosure. It was on the xAI website, not in the framework.

Limits: one entry, one developer, one person, no second coder. The seed versions and the Watchtower entry describe the same revision, so this check cannot find a revision that the ledger does not have.

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

## Recall test: does the model find new commitments?

The Meta v2.1 trace uses a model to find commitments with no counterpart in the earlier version. This test measures that step against the upstream coding.

Method: 4 version pairs where upstream coded the additions. The model got the two full documents, the definition of a commitment, and the definition of a counterpart. It did not get the upstream rows. Two independent runs for each pair. Same model and same instructions as the Meta run (`validation/recall/prompt.md`). An upstream addition counts as found if a model passage and the upstream quote share a long identical run (the `same_passage` rule, which the ledger had before this test).

| Pair | Upstream additions | Found by run 1 | Found by run 2 | Found by both |
|---|---|---|---|---|
| Google DeepMind v2.0 → v3.0 | 8 | 6 | 6 | 6 |
| Google DeepMind v3.0 → v3.1 | 11 | 9 | 9 | 9 |
| xAI Aug 2025 → Dec 2025 | 5 | 5 | 5 | 5 |
| xAI Dec 2025 → June 2026 | 10 | 6 | 5 | 5 |
| **Total** | **34** | **26 (76%)** | **25 (74%)** | **25 (74%)** |

**Result: the model found 26 of 34 upstream additions (76%, 95% CI 60 to 88). It did not find 8.**

The model also listed passages that upstream does not code as additions:

| | Run 1 | Run 2 |
|---|---|---|
| Passages listed | 56 | 47 |
| Match an upstream addition | 32 | 28 |
| Match an upstream row with a different code (upstream found a counterpart) | 13 | 11 |
| Match no upstream row | 11 | 8 |

How to read this:

- **The step misses about 1 addition in 4.** The 15 new Meta commitments are a lower bound, not a full list.
- **The step lists too many.** About 1 passage in 4 has a counterpart in the earlier version according to upstream. For Meta v2.1, a person confirmed each candidate, but he saw the model's reason first.
- "Match no upstream row" is not an error by itself. Upstream can have no row for a passage, or the units of text are different.
- All model quotes are verbatim in the later document (103 of 103).
- Upstream is not ground truth. A miss can be a disagreement about what a commitment is.
- More than one model passage can match one upstream row. That is why 32 passages match 26 rows.

### Review of the 8 misses

One person (the author) examined the 8 upstream additions that the model did not list. Options: real miss, not new, not a commitment, unit difference, cannot tell.

**Result: he classified all 8 as real misses.** None is a unit difference, and none is a disagreement about what a commitment is. The 76% is thus a fair measure of the step on these pairs, not an artefact of the match rule.

The review was not blind. The page did not show the earlier document, so "not new" was hard to select. File: `validation/recall/review.json`.

Limits: 34 additions, 2 developers. No full rewrite is in the test (Anthropic v3.0, Meta v2, OpenAI v2). The match rule depends on shared words; no person checked the matches. The model runs had access to the machine that holds the upstream files; the instructions told them to use the four given files only.

Files: `validation/recall/`.

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
