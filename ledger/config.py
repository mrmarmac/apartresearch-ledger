"""Fixed settings. Change these only on purpose."""

SCHEMA_VERSION = "0.1.0"

CORPUS_REPO = "https://github.com/louisyzhu/frontier-safety-framework-corpus"
CORPUS_COMMIT = "11cbeda80c5c526b7a8c2b19f64e07c13d420a49"
CORPUS_DOI = "10.5281/zenodo.22670700"
CORPUS_CITATION = (
    "Zhu, Louis Yiven (2026). Silent Revision: a versioned corpus of frontier AI "
    "safety frameworks and their revision accounts. Zenodo. arXiv:2609.08789."
)

# Upstream provider name -> ledger lab slug. The slug never changes,
# also when the company changes its name (xAI -> SpaceXAI).
LABS = {
    "xAI": "xai",
    "Anthropic": "anthropic",
    "Google DeepMind": "google",
    "Meta": "meta",
    "OpenAI": "openai",
}

# Upstream outcome code -> ledger status.
STATUS = {
    "R": "kept",
    "S": "strengthened",
    "W": "weakened",
    "X": "removed",
    "L": "relocated",
    "A": "added",
}

# Upstream category code -> ledger topic slug.
TOPIC = {
    "EC1": "eval-scope",
    "EC2": "eval-trigger",
    "EC3": "eval-method",
    "EC4": "third-party",
    "EC5": "disclosure",
    "EC6": "consequence",
    "G": "governance",
    "S": "security",
    "M": "mitigation",
}

DISCLOSURE = {
    "ANN": "announced",
    "ANN-P": "partly_announced",
    "SIL": "silent",
    "NCL": "no_account",
    "NA": "not_applicable",
}

# Keyword tags. Deterministic. No language model.
TAGS = {
    "whistleblower": r"whistle-?blow|retaliat|anonymous(ly)? report",
    "third-party-review": r"third[- ]part|external (review|evaluat|audit|red)|independent (review|audit|evaluat)",
    "benchmarks": r"benchmark",
    "thresholds": r"threshold",
    "security": r"information security|infosec|model weights|access control|cybersecurity",
    "transparency": r"transparen|publish|public(ly)? (disclos|releas|report)",
    "red-teaming": r"red[- ]team",
    "bio-chem": r"biolog|chemical|cbrn|pathogen|virolog",
    "cyber": r"cyber",
    "loss-of-control": r"loss of control|deception|deceiv|sycophan|controllab|misalign",
    "incident-reporting": r"incident",
    "regulators": r"government|regulator|authorit|agenc",
}

FUZZY_THRESHOLD = 0.9

SITE_URL = "https://mrmarmac.github.io/apartresearch-ledger"
REPO_URL = "https://github.com/mrmarmac/apartresearch-ledger"
SITE_TITLE = "Commitment Ledger"

STATUS_LABEL = {
    "baseline": "First seen",
    "added": "Added",
    "kept": "Kept",
    "strengthened": "Strengthened",
    "weakened": "Weakened",
    "removed": "Removed",
    "relocated": "Relocated",
    "active": "In force",
    "merged": "Merged",
    "not_traced": "Not traced",
}
STATUS_MARK = {
    "baseline": "•", "added": "+", "kept": "=", "strengthened": "↑",
    "weakened": "↓", "removed": "×", "relocated": "→",
}
TOPIC_LABEL = {
    "eval-scope": "Evaluation scope",
    "eval-trigger": "Triggers and thresholds",
    "eval-method": "Evaluation method",
    "third-party": "Third-party involvement",
    "disclosure": "Disclosure",
    "consequence": "Consequences of results",
    "governance": "Governance and oversight",
    "security": "Security",
    "mitigation": "Mitigations",
}
DISCLOSURE_LABEL = {
    "announced": "The developer's account identifies this change.",
    "partly_announced": "The developer's account identifies the area, but not the change.",
    "silent": "The developer published an account. It does not identify this change.",
    "no_account": "The developer published no account of this revision.",
}
# Events that go into the feed. "kept" and "baseline" are not changes.
FEED_STATUSES = ("added", "strengthened", "weakened", "removed", "relocated")

CODED_BY_LABEL = {
    "upstream": "Upstream coding (Zhu, 2026)",
    "text_match": "Text match: the same words are in this version",
    "model": "Model, two runs",
}
