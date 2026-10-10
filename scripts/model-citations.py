#!/usr/bin/env python3
"""model-citations.py — every PAPER3 DEFINITION the model cites must be in MODEL-DEFINITIONS.md.

WHY. `lean/`, `reference/` and LEAN-CHECKER-PLAN.md cite the formal model by number ("Def 32",
"Lemma 2", "Propositions 4–6"). Until 2026-10-10 the thing they cited was an unpublished manuscript
outside every repo, so no citation could be diffed and none could be checked. Tom's ruling that day put
the DEFINITIONS (not the paper) in this repo as MODEL-DEFINITIONS.md. This gate keeps the two in step: a
citation to a numbered Definition the extract does not carry fails, so a new citation forces a decision —
extract the definition, or stop citing it — instead of quietly pointing at a file nobody here can read.

ONLY DEFINITION CITATIONS ARE CHECKED. A citation of a Lemma, Theorem, Proposition, Corollary, Remark or
Escape is parsed (so a list like "Lemma 2, 3" is not misread as definitions) but NOT checked: those are
results and commentary, which the ruling kept out of the repo, so they still cite the manuscript.

WHAT IT DOES NOT CHECK. That the Lean or Python transcription MEANS what the extracted text says. That
is a reading, not a lookup; this only proves the cited item exists in a file a reviewer can open.

    python3 scripts/model-citations.py            # the gate
    python3 scripts/model-citations.py --selftest # proves the parser and the gate can fail
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXTRACT = ROOT / "MODEL-DEFINITIONS.md"

KINDS = {
    "def": "Definition", "defs": "Definition", "definition": "Definition", "definitions": "Definition",
    "lemma": "Lemma", "lemmas": "Lemma",
    "theorem": "Theorem", "theorems": "Theorem", "thm": "Theorem",
    "prop": "Proposition", "props": "Proposition", "proposition": "Proposition", "propositions": "Proposition",
    "remark": "Remark", "remarks": "Remark",
    "cor": "Corollary", "corollary": "Corollary", "corollaries": "Corollary",
    "escape": "Escape", "escapes": "Escape",
}
NUM = r"\d+(?:[a-f](?![a-z]))?(?:\([ivx]+\))?"  # "16a", "1(i)"; NOT the plural in "Lemma 2s"
ITEM = rf"{NUM}(?:\s*[–-]\s*{NUM})?"
CITE = re.compile(
    r"\b(" + "|".join(sorted(KINDS, key=len, reverse=True)) + r")\.?\s+"
    rf"({ITEM}(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+){ITEM})*)",
    re.IGNORECASE,
)
DEFINED = re.compile(r"^> \*\*(Definition|Lemma|Theorem|Proposition|Remark|Corollary|Escape) (\d+[a-z]?) ")


def _bare(tok):
    return re.sub(r"\([ivx]+\)$", "", tok.strip())


def expand(numlist):
    """'4-7, 30–32, 35 and 36' -> ['4',...,'7','30','31','32','35','36']; '16a–16c' -> 16a,16b,16c."""
    out = []
    for part in re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+", numlist.strip()):
        if not part:
            continue
        m = re.fullmatch(rf"({NUM})\s*[–-]\s*({NUM})", part)
        if not m:
            out.append(_bare(part))
            continue
        a, b = _bare(m.group(1)), _bare(m.group(2))
        ma, mb = re.fullmatch(r"(\d+)([a-z]?)", a), re.fullmatch(r"(\d+)([a-z]?)", b)
        if ma.group(1) == mb.group(1) and ma.group(2) and mb.group(2):
            out += [ma.group(1) + chr(c) for c in range(ord(ma.group(2)), ord(mb.group(2)) + 1)]
        else:
            out += [str(n) for n in range(int(ma.group(1)), int(mb.group(1)) + 1)]
    return out


def citations(text):
    for m in CITE.finditer(text):
        kind = KINDS[m.group(1).lower()]
        for n in expand(m.group(2)):
            yield kind, n


def defined(text):
    return {(m.group(1), m.group(2)) for line in text.splitlines() if (m := DEFINED.match(line))}


def sources():
    files = [ROOT / "lean" / "README.md", ROOT / "reference" / "README.md", ROOT / "LEAN-CHECKER-PLAN.md"]
    files += sorted((ROOT / "lean").rglob("*.lean"))
    files += sorted((ROOT / "reference").glob("*.py"))
    return [f for f in files if ".lake" not in f.parts]


def check(have, files):
    missing, n = [], 0
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for kind, num in citations(line):
                if kind != "Definition":
                    continue  # results/remarks are not extracted — see the header
                n += 1
                if (kind, num) not in have:
                    missing.append(f"{f.relative_to(ROOT)}:{i}: cites {kind} {num}, absent from MODEL-DEFINITIONS.md")
    return n, missing


def main():
    if not EXTRACT.exists():
        print("model-citations: MODEL-DEFINITIONS.md is missing", file=sys.stderr)
        return 2
    have = defined(EXTRACT.read_text(encoding="utf-8"))
    files = sources()
    n, missing = check(have, files)
    # A gate that read NOTHING must not print a clean bill.
    if not have or n == 0:
        print(f"model-citations: VACUOUS — {len(have)} items defined, {n} citations read", file=sys.stderr)
        return 1
    if missing:
        print("\n".join(missing))
        print(f"model-citations: FAIL — {len(missing)} of {n} definition citations name a Definition the extract does not carry")
        return 1
    print(f"model-citations: OK — {n} definition citations over {len(files)} files, all among {len(have)} extracted definitions")
    return 0


def selftest():
    bad = []
    def eq(got, want, what):
        if got != want:
            bad.append(f"{what}: got {got!r}, want {want!r}")
    eq(expand("4-7, 30-32, 35 and 36"), ["4", "5", "6", "7", "30", "31", "32", "35", "36"], "list+ranges")
    eq(expand("16a–16c"), ["16a", "16b", "16c"], "lettered range")
    eq(expand("1(i)"), ["1"], "sub-clause stripped")
    eq(list(citations("PAPER3's Definitions 33–35 and Prop 5, with Lemma 2s")),
       [("Definition", "33"), ("Definition", "34"), ("Definition", "35"), ("Proposition", "5"), ("Lemma", "2")],
       "citation scan")
    eq(list(citations("Phase 1 and §1 item 5")), [], "non-citations ignored")
    have = defined("> **Definition 2 (x).** y\n> **Lemma 2 (Monotone denial).** z\nDefinition 9 in prose\n")
    eq(have, {("Definition", "2"), ("Lemma", "2")}, "only headed items count as defined")
    # The gate must FAIL on a citation to an absent item, against the REAL extract.
    import tempfile
    real = defined(EXTRACT.read_text(encoding="utf-8"))
    for must in [("Definition", "35"), ("Definition", "16b"), ("Definition", "19a"), ("Definition", "25")]:
        if must not in real:
            bad.append(f"real extract lacks {must} — the defined-item parser is not reading it")
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "x.lean"
        p.write_text("-- PAPER3 Definition 99, Def 32 and Lemma 99\n", encoding="utf-8")
        global ROOT
        old, ROOT = ROOT, pathlib.Path(d)
        try:
            n, missing = check(real, [p])
        finally:
            ROOT = old
        # Def 99 absent -> caught; Def 32 present -> not; Lemma 99 -> not checked at all (n counts defs only)
        eq((n, len(missing)), (2, 1), "seeded absent definition is caught, present one and a Lemma are not")
    if bad:
        print("\n".join(bad))
        print(f"model-citations selftest: FAIL ({len(bad)})")
        return 1
    print("model-citations selftest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else main())
