"""Text normalisation for comparison. The ledger never changes stored quotes."""
import re
import unicodedata


def squash(text):
    """Lower case, letters and digits only. Use it to compare, not to store."""
    text = unicodedata.normalize("NFKD", text).lower()
    text = re.sub(r"-\s*\n\s*", "", text)  # hyphen at a line break
    return re.sub(r"[^a-z0-9]+", "", text)


def fragments(quote):
    """Split a quote at an ellipsis. Each part must be in the source."""
    parts = re.split(r"\.\.\.|…|\[\.\.\.\]", quote)
    return [p for p in (squash(x) for x in parts) if len(p) >= 12]


def quote_in_text(quote, squashed_source):
    """True when all parts of the quote are in the source, in sequence."""
    parts = fragments(quote)
    if not parts:
        return False
    pos = 0
    for part in parts:
        found = squashed_source.find(part, pos)
        if found < 0:
            return False
        pos = found + len(part)
    return True


def clean(text):
    """Tidy white space for display. Words do not change."""
    return re.sub(r"\s+", " ", text).strip()


def section_key(section):
    """Section heading without numbers, for the section_changed test."""
    return re.sub(r"[^a-z]+", "", (section or "").lower())
