#!/usr/bin/env python3
"""soundness-status.py — how many defects are OPEN, and which.

    python3 scripts/soundness-status.py            # counts + the open list
    python3 scripts/soundness-status.py --ids      # open IDs only, one per line

WHY THIS EXISTS. Asked "how many known defects are we shipping", I could not answer it from the register.
SOUNDNESS.md records closure in PROSE — "**CLOSED candor-rust `abc1234`**" — and only 37 of 472 rows use
the strikethrough convention, so every row closed this week still read as OPEN by that convention. The
answer took forensic grepping and came out "approximately 25, derived". A register whose central question
needs forensics is a register that will be wrong when it matters.

This does not invent a new schema or ask anyone to backfill 472 rows. It reads the prose markers that are
ALREADY there, and — the important part — it reports what it CANNOT decide rather than guessing:

    CLOSED     a closure marker is present  (CLOSED / FIXED / REFUTED / RETIRED / ~~Rn~~ / WITHDRAWN)
    OPEN       no marker anywhere in the row
    UNCERTAIN  a marker appears, but so does an OPEN/LIVE marker — the row is arguing with itself,
               or it is citing another row's closure. These are listed individually and are NOT
               silently counted as either.

The UNCERTAIN bucket is the point. A status tool that resolves ambiguity by picking a side is how a
register starts lying; this one makes the ambiguity the output. If that bucket grows, the fix is to
sharpen the rows it names, not to sharpen the regex.
"""
import re, sys, pathlib

# `fail closed` / `fail-closed` / `closed-world` are ORDINARY VOCABULARY here — this contract is about
# failing closed — so a bare \bCLOSED\b marks half the register resolved. Measured: R520 was filed as an
# open defect and read as CLOSED purely because its evidence says "nothing to fail closed OVER". Strip
# those spellings before looking for the marker; a status tool that mistakes the subject matter for a
# verdict is worse than no tool.
_NOT_A_VERDICT = re.compile(r'fails?[- ]closed|failing[- ]closed|closed[- ]world|fail[- ]closed', re.I)
# …AND EXPLICIT NEGATION OF THE CLOSURE WORD, which is a different failure from the fail-closed idiom
# above. Measured 2026-09-21 on R524: the row says a defect was "surfaced by the R519 work and NOT closed
# by it" and cites R519's fix SHA to say WHICH work did not close it — so CLOSURE matched `closed`,
# FIXSHA matched the sha, and the row was filed under closed-with-fix. It never appeared in the OPEN list
# the tool exists to produce, and the row was one I had written an hour earlier and was about to escalate.
# A status tool that reads a row saying NOT CLOSED as CLOSED is the register's own cardinal-sin shape.
_NEGATED_CLOSURE = re.compile(r"\b(?:not|never|isn'?t|was\s?n'?t|are\s?n'?t)\s+(?:yet\s+)?"
                              r"(?:been\s+)?(?:closed|fixed|resolved|retired|withdrawn)\b", re.I)
CLOSURE = re.compile(r'\bCLOSED\b|\bFIXED\b|\bREFUTED\b|\bRETIRED\b|\bWITHDRAWN\b|\bDECLINED\b|~~R\d+~~', re.I)
FIXSHA  = re.compile(r'`?\b[0-9a-f]{7,40}\b`?')   # backticked OR bare: measured across all 476 rows,
                                                 # accepting bare hex added exactly 2 matches and no
                                                 # false positives, so the looser form is the correct one

# THE DISCRIMINATOR, and why it is this one. The first version of this script asked only "does a closure
# WORD appear anywhere in the row", and put 191 of 476 rows in an UNCERTAIN bucket — useless, because a
# closed row routinely discusses an open question and an open row routinely cites another row's closure.
# The signal that actually separates them is whether the row CITES A FIX: a defect closed by a code change
# names the commit. That takes the ambiguous bucket from 191 to 92, and the 92 are a REAL category rather
# than a parsing failure — resolved with no code change (declined, refuted, accepted as a limit).
#
# Sharpening this further would be the wrong move. The remaining ambiguity is in the ROWS, and the honest
# output is four buckets that say which question each row leaves open.

# AN EXPLICIT DECLARATION BEATS INFERENCE. A row whose outcome cell OPENS with `OPEN` is its author
# saying so in as many words, and no amount of SHA-spotting should overrule that. R524 says
# "**OPEN — needs a family-level ruling, not a patch**" and cites R519's fix SHA to name the work that
# did NOT close it; the tool read the sha and filed it under "cites a sha, read it" — better than the
# closed-with-fix it started in, but still not the list its author put it on. Anchored to the START of
# the cell so the WORD "open" in ordinary prose ("an open question", "left open by") cannot trigger it.
_DECLARED_OPEN = re.compile(r'^\s*(?:\*\*|__)?\s*OPEN\b')


def _idkey(rid):
    """Sort R529 before R529b before R530. `int(rid[1:])` raised on a lettered sub-row and the OPEN
    listing died after printing its counts — 52 open, none named. Added 2026-09-22 with the suffix fix."""
    m = re.match(r'R(\d+)([a-z]*)$', rid)
    return (int(m.group(1)), m.group(2)) if m else (0, rid)


def bucket(line, outcome=None):
    if outcome is not None and _DECLARED_OPEN.match(outcome):
        return "open"
    line = _NOT_A_VERDICT.sub(" ", line)
    line = _NEGATED_CLOSURE.sub(" ", line)
    w, s = bool(CLOSURE.search(line)), bool(FIXSHA.search(line))
    if w and s:  return "closed-with-fix"      # a defect, and here is the commit
    if w:        return "resolved-no-fix"      # declined / refuted / accepted limit — a DECISION, not a fix
    if s:        return "cites-a-sha-only"     # odd; read it
    return "open"                              # nothing claims this is resolved

def main(argv):
    ids_only = "--ids" in argv
    p = pathlib.Path(__file__).resolve().parent.parent / "SOUNDNESS.md"
    # ONLY THE REGISTER TABLE. SOUNDNESS.md holds seven tables with different schemas, and matching
    # `^| R\d+` across the whole file swept in the ACCEPTED-FLOOR table (R2–R9 and friends), whose shape
    # is `| id | engine | description | SILENT | low | remedy |`. Its 5th cell is a SEVERITY ("low"),
    # not an outcome, so every one of those rows carried no closure word and printed as OPEN — 38 rows
    # of garbled text at the top of the list this tool exists to produce, which is also why its row count
    # (491) disagreed with `grep -c '^| R' SOUNDNESS.md` (453). An accepted, documented limit is not a
    # shipping defect, and padding the open list with them makes the real ones harder to see.
    #
    # The register table is identified by its HEADER, not by a line number or a row count: find
    # `| entry | date | engine | class | outcome |` and take the contiguous rows under its separator,
    # which is the same contiguity rule check_soundness_tables.py enforces.
    all_lines = p.read_text().splitlines()
    rows, in_register = [], False
    for ln in all_lines:
        low = ln.lower().replace(" ", "")
        if low.startswith("|entry|date|engine|class|outcome|"):
            in_register = True
            continue
        if in_register:
            if not ln.startswith("|"):
                in_register = False
                continue
            if re.match(r'^\| ~?~?R\d+', ln):
                rows.append(ln.rstrip("\n"))
    if not rows:
        print("soundness-status: REFUSING — no `| entry | date | engine | class | outcome |` table found.",
              file=sys.stderr)
        print("  A silent empty list is exactly the under-report this tool exists to prevent.", file=sys.stderr)
        return 2
    by = {}
    for l in rows:
        # THE LETTER SUFFIX IS PART OF THE ID. `(R\d+)` dropped it, so R529c printed as "R529", R531b as
        # "R531" and R532b as "R532" — and on 2026-09-22 all three of those BASE rows were CLOSED while
        # their lettered siblings were open. The shipping-defect list was therefore naming rows that are
        # fixed: a reader looking up "R529" finds a closed row and concludes the list is wrong, or worse
        # re-opens work that is done. Sub-rows are how this register splits one finding into its separate
        # measurable parts, so collapsing them loses exactly the distinction they were created to make.
        rid = re.match(r'^\| ~?~?(R\d+[a-z]?)', l).group(1)
        # The outcome is the LAST cell of the register table; pass it separately so a declared OPEN
        # is read as a declaration rather than hunted for in the whole row's prose.
        _c = re.split(r'(?<!\\)\|', l)
        _outcome = _c[5] if len(_c) > 5 else None
        by.setdefault(bucket(l, _outcome), []).append((rid, l))

    if ids_only:
        for rid, _ in sorted(by.get("open", []), key=lambda t: _idkey(t[0])):
            print(rid)
        return 0

    print(f"SOUNDNESS status — {len(rows)} rows")
    for k in ("closed-with-fix", "resolved-no-fix", "cites-a-sha-only", "open"):
        print(f"  {k:18s} {len(by.get(k, []))}")
    print()
    print("OPEN — nothing in the row claims it is resolved. THIS is the shipping-defect list:")
    for rid, l in sorted(by.get("open", []), key=lambda t: _idkey(t[0])):
        cells = re.split(r'(?<!\\)\|', l)
        eng = cells[3].strip()[:20] if len(cells) > 3 else "?"
        claim = " ".join(cells[1].split())[len(rid) + 1:][:86]
        print(f"  {rid:6s} {eng:20s} {claim}")
    if by.get("cites-a-sha-only"):
        print()
        print("CITES A SHA BUT NO CLOSURE WORD — read these, they are neither clearly:")
        for rid, _ in sorted(by["cites-a-sha-only"], key=lambda t: _idkey(t[0])):
            print(f"  {rid}")
    return 0

def selftest():
    """Prove the bucketing can distinguish a claim of closure from a denial of one.

    WHY THIS EXISTS. For its whole life this tool read `Not fixed.` as FIXED. `CLOSURE` matched the word
    `fixed`, nothing looked left of it, and a row whose outcome cell opens "Not fixed." was filed as
    resolved — so on 2026-09-21, 43 rows were in the wrong bucket and 32 of them were REAL OPEN DEFECTS
    absent from the list this tool exists to print. The docstring called the OPEN bucket "the
    shipping-defect list" while the shipping-defect list was missing a third of itself.

    Each case below is a string this tool got wrong, or a near-miss that must NOT move. The domain cases
    are the ones that matter: `unresolved` and "could not be resolved" are candor's own vocabulary for
    DISPATCH, not for a row's status, and a strip that ate them would empty the resolved bucket instead.
    """
    cases = [
        # (text, expected bucket)
        ("Not fixed. One producer, or a normalisation at the writer.",          "open"),
        ("Not yet fixed — the remedy is known.",                                "open"),
        # R524's exact shape, and the bucket is `cites-a-sha-only` rather than `open` ON PURPOSE: it
        # cites a SHA (to name the work that did NOT close it) while making no closure claim, so the
        # honest answer is "neither clearly — read it", which is what that bucket means. This expectation
        # was written as `open` first and the selftest caught it. What matters is that it is no longer
        # filed under closed-with-fix, where it was invisible.
        ("surfaced by the R519 work and NOT closed by it. See `82da250`.",      "cites-a-sha-only"),
        ("**CLOSED — candor-ts `82da250`, shipped and verified.**",             "closed-with-fix"),
        ("**REFUTED** — measured, the premise was wrong.",                      "resolved-no-fix"),
        # NEAR-MISSES that must NOT be stripped: domain vocabulary, not a status claim.
        ("**CLOSED — `abc1234`.** The callee is not resolved through the alias.", "closed-with-fix"),
        ("**CLOSED — `abc1234`.** fails-closed on an unresolved import.",        "closed-with-fix"),
        ("the dispatch could not be resolved, so the row stands. `deadbee`",     "cites-a-sha-only"),
        # DECLARED OPEN beats a SHA. R524's real shape: it names the work that did NOT close it.
        ("**OPEN — needs a family-level ruling, not a patch.** See `82da250`.",  "open"),
        # …but only as a DECLARATION at the start of the cell. "open" in ordinary prose must not move a
        # closed row, or the bucket fills with rows that merely discuss open questions.
        ("**CLOSED — `abc1234`.** This left an open question for R99.",          "closed-with-fix"),
    ]
    bad = 0
    # The ID parse is part of the contract too — see the comment at `rid`. A base row and its lettered
    # sibling are DIFFERENT rows and routinely have different verdicts.
    for line, want_id in (("| R529c rust: a body-local struct's field type…", "R529c"),
                          ("| R529 rust: an implementor written inside a block…", "R529"),
                          ("| ~~R116~~ retracted", "R116")):
        got = re.match(r'^\| ~?~?(R\d+[a-z]?)', line).group(1)
        flag = "ok  " if got == want_id else "FAIL"
        if got != want_id:
            bad += 1
        print(f"  {flag} id={got:7s} want {want_id:7s} {line[:46]!r}")
    for text, want in cases:
        got = bucket(text, text)   # in a real row the outcome IS the last cell
        flag = "ok  " if got == want else "FAIL"
        if got != want:
            bad += 1
        print(f"  {flag} {got:17s} want {want:17s} {text[:64]!r}")
    print("soundness-status selftest: " + ("OK" if not bad else f"FAILED ({bad})"))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    sys.exit(main(sys.argv))
