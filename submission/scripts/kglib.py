"""Shared helpers for the literature-kg Skill (stdlib only).

Text normalisation, quote matching, name keys, stable ids, JSON I/O.
"""
import hashlib
import json
import os
import re
import unicodedata

VERSION = "0.1.0"

# ---------------------------------------------------------------- schema ---
# Concept types may be shared across papers (one node, provenance from each).
# Instance types are always scoped to one paper: the same label in two papers
# is NOT the same physical sample / model run / dataset split / result.
CONCEPT_TYPES = {"Material", "Method", "Task", "Metric", "Instrument", "Researcher", "Mechanism"}
INSTANCE_TYPES = {"Sample", "Measurement", "Conclusion", "Dataset", "Model", "Condition", "Paper"}
ENTITY_TYPES = CONCEPT_TYPES | INSTANCE_TYPES

ANY = set(ENTITY_TYPES)
# predicate -> (allowed subject types, allowed object types, description)
PREDICATES = {
    "AUTHOR_OF": ({"Researcher"}, {"Paper"}, "researcher wrote the paper (manifest/byline evidence)"),
    "STUDIES": ({"Paper", "Method", "Sample", "Model"}, {"Task", "Material"}, "work addresses a task / studies a material"),
    "USES": ({"Paper", "Method", "Sample", "Model", "Task", "Measurement"}, {"Method", "Material", "Dataset", "Instrument", "Model", "Metric"}, "uses a method, material, dataset, instrument"),
    "PREPARED_FROM": ({"Sample", "Material"}, {"Material", "Sample"}, "made from / modified with"),
    "INSTANCE_OF": ({"Sample", "Model", "Dataset"}, {"Material", "Method", "Dataset"}, "paper-specific instance of a general concept"),
    "CHARACTERIZED_BY": ({"Sample", "Material", "Model"}, {"Method", "Instrument"}, "characterised / analysed with"),
    "HAS_RESULT": ({"Sample", "Material", "Method", "Model", "Paper"}, {"Measurement"}, "reported value / observation for the subject"),
    "MEASURED_BY": ({"Measurement"}, {"Metric", "Method", "Instrument"}, "what quantity / method the value is"),
    "UNDER_CONDITION": ({"Measurement", "Conclusion", "Sample"}, {"Condition"}, "value or claim holds under this condition"),
    "FITS": ({"Method", "Model"}, {"Measurement", "Sample"}, "model describes the data (e.g. isotherm/kinetic model fits)"),
    "OUTPERFORMS": (ANY - {"Researcher", "Paper"}, ANY - {"Researcher", "Paper"}, "subject better than object on a stated criterion"),
    "COMPARED_WITH": (ANY - {"Researcher"}, ANY - {"Researcher"}, "explicit comparison without a winner"),
    "SUPPORTS": ({"Measurement", "Conclusion", "Method", "Sample"}, {"Conclusion"}, "evidence supports the claim"),
    "CONTRADICTS": ({"Measurement", "Conclusion"}, {"Conclusion", "Measurement"}, "evidence contradicts the claim"),
    "CONCLUDES": ({"Paper"}, {"Conclusion"}, "paper states this conclusion"),
    "PART_OF": (ANY, ANY, "component / sub-step of"),
    "TESTED_ON": ({"Sample", "Material", "Method", "Model"}, {"Material", "Sample", "Dataset", "Task"}, "adsorbent/method tested with a target substance, dataset or task"),
    "ATTRIBUTED_TO": ({"Measurement", "Conclusion", "Sample"}, {"Mechanism", "Conclusion", "Material", "Metric"}, "authors explain the result by this mechanism / cause"),
    "INVOLVES": ({"Sample", "Material", "Method", "Conclusion"}, {"Mechanism"}, "process or interaction involves this mechanism"),
    "APPLIED_TO": ({"Method", "Material", "Sample", "Model"}, {"Task", "Material", "Sample", "Dataset"}, "applied to a target / task"),
}
STRENGTHS = ["direct", "indirect", "hedged", "cited"]
ATTRIBUTIONS = ["author", "cited", "metadata"]

HEDGE_RE = re.compile(r"\b(may|might|could|possibly|likely|suggest(?:s|ed|ing)?|presumably|appear(?:s|ed)? to|probabl[ey]|potential(?:ly)?|it is (?:believed|thought))\b", re.I)
CITE_RE = re.compile(r"(\[\s*\d+(?:\s*[,–—-]\s*\d+)*\s*\]|\(\s*\d+(?:\s*[,–-]\s*\d+)*\s*\)|\bet al\.|\b(?:previously|earlier) (?:reported|shown|described)|\b(?:has|have) been reported|\breported (?:by|in)\b)", re.I)


# ------------------------------------------------------------------ I/O ---
def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(*parts, n=10):
    return hashlib.sha1("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:n]


# --------------------------------------------------------- normalisation ---
_QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"', "′": "'", "´": "'"}
_DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−﹣－"), "-")


def norm_text(s):
    """Loose form for quote matching: NFKC, unified quotes/dashes, no case, single spaces."""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(_DASHES)
    for a, b in _QUOTES.items():
        s = s.replace(a, b)
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def squash(s):
    """Very loose form: letters and digits only (handles linearised sub/superscripts)."""
    return re.sub(r"[^0-9a-zͰ-Ͽ一-鿿]+", "", norm_text(s))


def quote_match(quote, text):
    """Return (status, score). status in exact|normalized|approx|absent."""
    if not quote or not text:
        return "absent", 0.0
    if quote in text:
        return "exact", 1.0
    nq, nt = norm_text(quote), norm_text(text)
    if nq and nq in nt:
        return "normalized", 1.0
    sq, st = squash(quote), squash(text)
    if len(sq) >= 8 and sq in st:
        return "normalized", 0.98
    # approximate: share of quote tokens found in order-insensitive window
    qt = re.findall(r"\w+", nq)
    if len(qt) < 4:
        return "absent", 0.0
    tt = set(re.findall(r"\w+", nt))
    score = sum(1 for t in qt if t in tt) / len(qt)
    # require a long contiguous anchor as well
    anchor = max(_longest_common_run(qt, re.findall(r"\w+", nt)), 0)
    if score >= 0.9 and anchor >= min(6, len(qt)):
        return "approx", round(score, 3)
    return "absent", round(score, 3)


def _longest_common_run(a, b):
    best = 0
    pos = {}
    for j, t in enumerate(b):
        pos.setdefault(t, []).append(j)
    for i, t in enumerate(a):
        for j in pos.get(t, []):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            best = max(best, k)
    return best


GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "μ": "mu", "λ": "lambda", "π": "pi", "σ": "sigma", "θ": "theta"}


def name_key(name):
    """Canonical key for alias matching: case-, hyphen-, space-, plural-insensitive."""
    s = unicodedata.normalize("NFKC", name or "").translate(_DASHES)
    for g, w in GREEK.items():
        s = s.replace(g, w)
    s = s.lower()
    s = re.sub(r"[\s\-_/,.;:'\"()\[\]{}]+", " ", s).strip()
    toks = []
    for t in s.split():
        if len(t) > 4 and t.endswith("ies"):
            t = t[:-3] + "y"
        elif len(t) > 3 and t.endswith("s") and not t.endswith("ss") and not t.endswith("is") and not t.endswith("us"):
            t = t[:-1]
        toks.append(t)
    return "".join(toks)


def is_abbrev(name):
    n = (name or "").strip()
    if not n or " " in n or len(n) > 10:
        return False
    letters = [c for c in n if c.isalpha()]
    return len(letters) >= 2 and sum(c.isupper() for c in letters) >= max(2, int(0.6 * len(letters)))


def slug(s, n=40):
    k = re.sub(r"[^0-9a-z]+", "-", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()).strip("-")
    return (k[:n].strip("-") or "x") + ("" if k else "-" + short_hash(s, n=6))


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", norm_text(s)))


def jaccard(a, b):
    a, b = tokens(a), tokens(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def numbers_in(s):
    return re.findall(r"\d+(?:\.\d+)?", (s or "").replace(",", ""))


GENERIC = set("model models method methods isotherm kinetic analysis spectroscopy sample samples composite reference material based "
              "the of and a an in on for with by from initial modified".split())
DESCRIPTIVE_TYPES = {"Paper", "Conclusion", "Measurement", "Condition", "Task"}


def _stems(s):
    return {t[:5] for t in re.findall(r"[a-z0-9Ͱ-Ͽ]+", norm_text(s)) if len(t) >= 2}


def mentioned(names, text):
    """True if any name/alias occurs in text: exact (squashed) or >=60% of its distinctive word stems."""
    st, stems = squash(text), _stems(text)
    for n in names:
        if not n:
            continue
        if squash(n) and squash(n) in st:
            return True
        toks = [t[:5] for t in re.findall(r"[a-z0-9Ͱ-Ͽ]+", norm_text(n)) if t not in GENERIC and len(t) >= 2]
        if toks and sum(t in stems for t in toks) / len(toks) >= 0.6:
            return True
    return False


def distinct_jaccard(a, b):
    ta = {t for t in tokens(a) if t not in GENERIC}
    tb = {t for t in tokens(b) if t not in GENERIC}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)
