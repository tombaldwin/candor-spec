#!/usr/bin/env python3
"""ONE recogniser for "is this line a SOUNDNESS register row, and which row is it?".

SOUNDNESS R641 + R640. There were FIVE copies of this question in two files and they did not agree:

  · `check_soundness_tables.py:row_id`   — tolerated leading empty cells, DROPPED the letter suffix
  · `check_soundness_tables.py:full_id`  — same scan, kept the suffix (added because the first drops it)
  · `soundness-status.py`, three sites   — `^\\| ~?~?R\\d+`, which sees NEITHER malformed spelling

That is attack G and Sec F1 q3 in the two tools that read the shipping-defect list. The measured cost:
a row written `|| R524 …` — a doubled leading pipe, which GFM renders as a row with an empty first
cell — is seen by `check_soundness_tables.py` and NOT by `soundness-status.py`, so it **vanishes from
the counts, the OPEN list and `--ids` entirely** and the list is silently one row short. The direction
is the register's own cardinal sin: under-reporting what is open.

AND THE SHARED RECOGNISER MUST NOT INHERIT THE BOUND THE OLD ONE HAD (R640). Both `check_` copies read
only `cells[:2]`, so a row with TWO or more leading empty cells (`||| R900 …`) or a **bolded** id
escaped all three of that tool's properties — including the duplicate-id check, which is what makes two
rows with one number invisible. Its own docstring already claimed the right rule (*a row is identified
by its ID appearing as the first NON-EMPTY cell*); this is that sentence made executable, with markdown
emphasis and strike markers stripped before the match.

    row_id("| R529c rust: …")        -> "R529c"     the ordinary spelling
    row_id("|| R524 …")              -> "R524"      one leading empty cell
    row_id("| | | R900 …")           -> "R900"      several
    row_id("| **R900** …")           -> "R900"      a bolded id
    row_id("| ~~R116~~ retracted …") -> "R116"      struck through — retracted, still a row
    row_id("| entry | date | …")     -> None        the header
    row_id("| a note | R900 … |")    -> None        an id past the first NON-EMPTY cell is not a row

Every caller wants the FULL id including its letter suffix: R529, R529b and R529c are three different
rows, and on 2026-09-22 a base row was CLOSED while its lettered sibling was open.
"""
import re

# UNESCAPED pipes only: `\|` inside a cell is content and is the correct spelling for a pipe in prose.
_SPLIT = re.compile(r'(?<!\\)\|')
# Leading markdown noise, then the id. `[\s*_~]*` covers **bold**, __bold__, ~~strike~~ and any spacing
# between them; the trailing guard stops `R12x` or `R123abc` being read as `R12`/`R123a`.
_ID = re.compile(r'^[\s*_~]*(R\d+[a-z]?)(?![A-Za-z0-9])')


def split_cells(line):
    """The row's cells, escaped-pipe-aware. The leading fragment before the first `|` is dropped; a
    trailing empty fragment after the final `|` is kept, and is empty, so callers scanning for content
    are unaffected."""
    return _SPLIT.split(line)[1:]


def row_id(line):
    """The register ID of `line` if it is a table row whose FIRST NON-EMPTY cell is one, else None."""
    if not line.startswith('|'):
        return None
    for cell in split_cells(line):
        if not cell.strip():
            continue                       # a leading empty cell is malformed, not disqualifying
        m = _ID.match(cell)
        return m.group(1) if m else None   # first non-empty cell is not an id -> not our row
    return None


CASES = [
    # (line, expected id) — the contract, shared by both tools' selftests so neither can drift from it.
    ("| R529c rust: a body-local struct's field type… | a | b | c | d |", "R529c"),
    ("| R529 rust: an implementor written inside a block… | a | b | c | d |", "R529"),
    ("| ~~R116~~ retracted | a | b | c | d |", "R116"),
    ("| R524 the ordinary spelling | a | b | c | d |", "R524"),
    ("|| R524 one leading empty cell | a | b | c | d |", "R524"),               # R641
    ("| | R524 one leading empty cell, spaced | a | b | c | d |", "R524"),      # R641
    ("||| R900 two leading empty cells | a | b | c | d |", "R900"),             # R640
    ("| **R900** a bolded id | a | b | c | d |", "R900"),                       # R640
    ("| ~~**R900**~~ struck AND bolded | a | b | c | d |", "R900"),
    ("| entry | date | engine | class | outcome |", None),                      # the header
    ("|---|---|---|---|---|", None),                                            # the separator
    ("| a note about R900 that is not a row | a | b |", None),
    ("| some prose | R900 an id past the first non-empty cell | a |", None),
    # A SINGLE trailing letter IS a sub-row id (R529c); two or more is not one.
    ("| R900x a lettered sub-row | a |", "R900x"),
    ("| R900abc not an id | a |", None),
    ("| Rx900 not an id | a |", None),
    ("plain prose mentioning R900", None),
    # An escaped pipe in the id cell must not split it: `move \| i \|` is real register content.
    ("| R571 rust: `move \\| i: Input \\|` | a | b | c | d |", "R571"),
]


def selftest(prefix="  "):
    """Returns the number of failures, printing one line each. Called by BOTH tools' selftests."""
    bad = 0
    for line, want in CASES:
        got = row_id(line)
        ok = got == want
        bad += not ok
        print("%s%s row_id=%-7s want %-7s %r" % (prefix, "ok  " if ok else "FAIL",
                                                 got, want, line[:52]))
    return bad


if __name__ == "__main__":
    import sys
    print("soundness_row — the shared register-row recogniser (SOUNDNESS R640/R641)")
    sys.exit(1 if selftest() else 0)
