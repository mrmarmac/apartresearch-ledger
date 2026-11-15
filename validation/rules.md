# Coding rules

Excerpt from `codebook_v0.2_FROZEN.md` of the Frontier Safety Framework Corpus by Louis Yiven Zhu (CC BY 4.0). Sections 4, 5 and 11.1 to 11.3. Unchanged.

## 4. Outcome codes (one per traced commitment)

| Code | Outcome | Definition |
|---|---|---|
| **R** | Retained | Counterpart exists; no material change (rewording, reformatting, renumbering only) |
| **S** | Strengthened | Counterpart exists; at least one materiality dimension moves toward greater obligation, broader scope, lower threshold, more third-party involvement, or more disclosure |
| **W** | Weakened | Counterpart exists; at least one materiality dimension moves the other way |
| **X** | Removed | No counterpart in v_{i+1} and the commitment is not relocated |
| **L** | Relocated | Counterpart exists only in a separate companion document, or is moved from "company commitment" to "industry recommendation" or equivalent non-binding section |
| **A** | Added | Present in v_{i+1} with no counterpart in v_i |

If both strengthening and weakening dimensions are present in one commitment, code **W** and note both in the free-text field. Weakening on any dimension is the conservative call and the one reviewers will expect.

**L counts as a material change** and is analysed alongside W in the direction breakdown, but is reported separately so a reader can see how much "weakening" is relocation rather than deletion.

---

## 5. Materiality rule

A change is **material** if it alters at least one of:

1. **Scope** — the set of capabilities, risk domains, or model classes the commitment covers
2. **Threshold or trigger** — the level, timing, or condition at which evaluation or action is required
3. **Actor** — who conducts, verifies, or must be given access (including the addition or removal of a third party)
4. **Obligation strength** — the modal force of the commitment. Ordered scale for reference: *must / will / commit to* > *intend to / aim to / expect to* > *may / could / consider* > *recommend / encourage* (the last is not a self-commitment)
5. **Disclosure scope** — what is published, to whom, when, or with what redaction
6. **Consequence** — what action a result obligates, or the conditions under which that action can be deferred or overridden

Not material: rewording with the same modal force, reorganisation, typographical changes, updated cross-references, changes to examples that do not alter the rule.

**Conditional commitments.** Broadening the condition under which a commitment can be suspended or adjusted (e.g. adding "if a competitor deploys without comparable safeguards") is a change to *consequence* and is coded W even if the core commitment is untouched.

**Modal drift.** "We will" → "we aim to" is material (obligation strength). "We will" → "we commit to" is not.

---

## 11. Decisions made after the first pass (v0.2)

**11.1 Present-tense practice statements.** "We conduct X before deployment", "xAI utilizes Y", "evaluations are run" are commitments: in a policy document the descriptive present is the standing-commitment register. They sit at the **top rung** of the obligation scale, equal to *will / must / commit to*. A change between present tense and *will* is not material on dimension 4. A change from present tense or *will* to *may / aim to / consider* is material on dimension 4.

**11.2 Enumerations.** An enumeration is **scope-defining** when it is introduced by "including", "comprising", "consists of", or when it is the operative content of the commitment (the list *is* what is committed to). Removing or shortening a scope-defining enumeration is material on dimension 1 (Example G). An enumeration is **illustrative** when introduced by "e.g.", "for example", "such as", and the rule stands independently of it; changes to an illustrative enumeration are not material unless the rule text itself changes (section 5, "changes to examples").

**11.3 Both directions in one commitment.** Code the outcome **W** (section 4 rule) and add `MIX` to flags. The paper reports the MIX count so readers can see how much weakening is mixed.
