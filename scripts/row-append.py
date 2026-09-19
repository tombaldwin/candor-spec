#!/usr/bin/env python3
"""row-append.py — append text to one CELL of one SOUNDNESS row, without widening the table.

    python3 scripts/row-append.py R507 evidence "text …"
    python3 scripts/row-append.py R507 notes    "text …"     # or: claim | date | engine

WHY THIS EXISTS. I widened the SOUNDNESS table three times in three days, the same way each time:
appending prose that contained a literal `|`. The register is read BY COLUMN, so an unescaped pipe shifts
every column after it and **nothing errors — the table still draws**. Once I even pushed the broken result,
having printed the checker's exit code and then committed anyway.

The mistake is mechanical and recurring, so the answer is a tool rather than more care. This script:

  * ESCAPES every `|` in the appended text (backtick spans are NOT exempt — the checker says so, and a
    Rust closure `||` or an alternation in a regex is the usual carrier);
  * ASSERTS the row's cell count is unchanged, and refuses to write if it moved;
  * exits NON-ZERO on any problem, so `&&` in a shell line is a real gate.

It deliberately does not know how to CREATE a row — appending to an existing one is the operation that
kept going wrong.
"""
import re, sys, pathlib

# Count cells the way the CHECKER reads them: an ESCAPED pipe (`\\|`) is cell CONTENT, not a boundary.
# The first version of this guard used a plain `split("|")`, which still sees the `|` inside `\\|` — so it
# REFUSED correctly-escaped text. It failed closed, which is the right direction, but it blocked the exact
# operation the tool exists to make safe. Caught by calibrating the tool instead of trusting it.
def cells_of(row):
    return re.split(r'(?<!\\)\|', row)

CELLS = {"claim": 1, "date": 2, "engine": 3, "evidence": 4, "notes": 5}

def main(argv):
    if len(argv) != 4:
        print(__doc__.strip()); return 2
    rid, cellname, text = argv[1], argv[2], argv[3]
    if cellname not in CELLS:
        print(f"row-append: unknown cell {cellname!r}; want one of {', '.join(CELLS)}"); return 2
    idx = CELLS[cellname]

    p = pathlib.Path(__file__).resolve().parent.parent / "SOUNDNESS.md"
    s = p.read_text()
    m = re.search(rf'^\| ~?~?{re.escape(rid)} ', s, re.M)
    if not m:
        print(f"row-append: no row {rid} in {p.name}"); return 1
    i = m.start(); j = s.index("\n", i)
    cells = cells_of(s[i:j])
    before = len(cells)
    if idx >= before - 1:
        print(f"row-append: {rid} has {before-2} content cells; no {cellname!r} cell to append to")
        return 1

    # THE WHOLE POINT: escape pipes in the INCOMING text before it can become a column boundary.
    safe = text.replace("\\|", "|").replace("|", "\\|")
    cells[idx] = cells[idx].rstrip() + " " + safe.strip() + " "
    row = "|".join(cells)
    if len(cells_of(row)) != before:
        print(f"row-append: REFUSING — cell count would move {before} -> {len(cells_of(row))}")
        return 1

    p.write_text(s[:i] + row + s[j:])
    print(f"row-append: {rid}.{cellname} += {len(safe)} chars; cells unchanged at {before-2}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
