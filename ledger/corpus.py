"""Read the upstream corpus (Zhu 2026). Read only. Nothing here changes it."""
import csv
import os
import re

from . import config

NONE = ("", "NONE", "(none)")


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def base_label(label):
    """'2025-08-20-reupload-20250822' -> '2025-08-20'."""
    return re.sub(r"-reupload-\d+$", "", label)


def version_id(lab, label):
    slug = re.sub(r"[^a-z0-9.]+", "-", base_label(label).lower()).strip("-")
    return f"{lab}-{slug}"


def final(row, field):
    """The final code of a row. Rule from the upstream README:
    re-examined code, else adjudicated code, else first-pass code."""
    if row["READJ_mode"].startswith("re-examined") and row.get("READJ_" + field):
        return row["READJ_" + field]
    return row.get("ADJ_" + field) or row.get(field, "")


def final_mixed(row):
    if row["READJ_mode"].startswith("re-examined"):
        return "MIX" in row["READJ_flags"]
    return "MIX" in row["ADJ_flags"]


class Corpus:
    def __init__(self, root):
        self.root = root
        self.manifest = _rows(os.path.join(root, "corpus", "manifest.csv"))
        self.pairs = _rows(os.path.join(root, "corpus", "pairs.csv"))
        self.tracing = _rows(os.path.join(root, "coding", "tracing_FINAL_v3.csv"))
        self._text = {}

    def framework_rows(self, provider):
        """Manifest rows for the main framework documents of one provider."""
        return [r for r in self.manifest if r["provider"] == provider and r["is_companion"] == "no"]

    def manifest_row(self, provider, label):
        for row in self.framework_rows(provider):
            if row["version"] == label:
                return row
        raise KeyError(f"no manifest row for {provider} {label}")

    def traced_pairs(self, provider):
        """Traced pairs in date sequence, with their tracing rows."""
        out = []
        for pair in self.pairs:
            if pair["provider"] != provider or pair["traced"] != "yes":
                continue
            rows = [r for r in self.tracing
                    if r["provider"] == provider
                    and base_label(r["v_i"]) == base_label(pair["v_i"])
                    and base_label(r["v_next"]) == base_label(pair["v_next"])]
            date = self.manifest_row(provider, base_label(pair["v_i"]))["publication_date"]
            out.append((date, pair, rows))
        out.sort(key=lambda item: item[0])
        return [(pair, rows) for _, pair, rows in out]

    def text(self, provider, label):
        """Text extraction of one document, or None."""
        key = (provider, label)
        if key not in self._text:
            row = self.manifest_row(provider, label)
            path = os.path.join(self.root, "corpus", row["txt_filename"])
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    self._text[key] = handle.read()
            except OSError:
                self._text[key] = None
        return self._text[key]
