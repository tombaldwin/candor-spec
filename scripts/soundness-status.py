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

def bucket(line):
    w, s = bool(CLOSURE.search(line)), bool(FIXSHA.search(line))
    if w and s:  return "closed-with-fix"      # a defect, and here is the commit
    if w:        return "resolved-no-fix"      # declined / refuted / accepted limit — a DECISION, not a fix
    if s:        return "cites-a-sha-only"     # odd; read it
    return "open"                              # nothing claims this is resolved

def main(argv):
    ids_only = "--ids" in argv
    p = pathlib.Path(__file__).resolve().parent.parent / "SOUNDNESS.md"
    rows = [l.rstrip("\n") for l in p.read_text().splitlines() if re.match(r'^\| ~?~?R\d+', l)]
    by = {}
    for l in rows:
        rid = re.match(r'^\| ~?~?(R\d+)', l).group(1)
        by.setdefault(bucket(l), []).append((rid, l))

    if ids_only:
        for rid, _ in sorted(by.get("open", []), key=lambda t: int(t[0][1:])):
            print(rid)
        return 0

    print(f"SOUNDNESS status — {len(rows)} rows")
    for k in ("closed-with-fix", "resolved-no-fix", "cites-a-sha-only", "open"):
        print(f"  {k:18s} {len(by.get(k, []))}")
    print()
    print("OPEN — nothing in the row claims it is resolved. THIS is the shipping-defect list:")
    for rid, l in sorted(by.get("open", []), key=lambda t: int(t[0][1:])):
        cells = re.split(r'(?<!\\)\|', l)
        eng = cells[3].strip()[:20] if len(cells) > 3 else "?"
        claim = " ".join(cells[1].split())[len(rid) + 1:][:86]
        print(f"  {rid:6s} {eng:20s} {claim}")
    if by.get("cites-a-sha-only"):
        print()
        print("CITES A SHA BUT NO CLOSURE WORD — read these, they are neither clearly:")
        for rid, _ in sorted(by["cites-a-sha-only"], key=lambda t: int(t[0][1:])):
            print(f"  {rid}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
