#!/usr/bin/env python3
"""Every SOUNDNESS row must actually render as a table row.

WHY THIS EXISTS, and it is not the reason you would guess. This project has shipped a broken
SOUNDNESS table FIVE times. Four were caught late by a reviewer. The fifth was caught only after a
commit that CLAIMED to fix it (`97cfbfe`, "R116 was an orphaned table row, rendering as raw text")
moved the row from one orphaned block into the SAME orphaned block, and reported success — because
its verification counted PIPES.

Pipe counts were never the failure. Every row in the file had the right pipe count the whole time.
In GitHub-flavoured markdown a table is a header, a separator, and then CONTIGUOUS pipe lines: a
blank line, a paragraph, or a heading ENDS it, and every `| ... |` line after that renders as
literal text. At its worst this file had 26 consecutive rows — the entire ⟨0.35⟩ round's register,
R108 through R133 — rendering as one paragraph of raw pipes, plus six older rows split off by three
stray blank lines.

So the property to check is CONTIGUITY, not shape, and a validator that measures the wrong property
is worse than none: it reports green over exactly the defect it was written for. That is this
project's own cardinal-sin shape pointed at its own instrument, which is why this is a script and
not a habit.

    python3 scripts/check_soundness_tables.py [<file>]      # default: SOUNDNESS.md beside this repo

Exit 0 clean, 1 with the offending line numbers, 2 if the file cannot be read.
"""
import re
import sys
from pathlib import Path

# A row we care about: `| R12 ...` or `| ~~R12~~ ...` (struck-through rows are retracted, still rows).
ROW_RE = re.compile(r'^\| ~{0,2}R\d+')
# A GFM delimiter row: `|---|---|`, optionally with alignment colons and spaces.
SEP_RE = re.compile(r'^\|[\s:-]+\|[\s|:\-]*$')


def tables(lines):
    """Yield (separator_index, [row_indices]) for each GFM table, by the contiguity rule."""
    for i, line in enumerate(lines):
        if not SEP_RE.match(line):
            continue
        rows, j = [], i + 1
        while j < len(lines) and lines[j].startswith('|'):
            rows.append(j)
            j += 1
        yield i, rows


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path(__file__).resolve().parent.parent / 'SOUNDNESS.md'
    try:
        lines = path.read_text(encoding='utf-8').split('\n')
    except OSError as exc:
        print(f'check_soundness_tables: cannot read {path}: {exc}', file=sys.stderr)
        return 2

    in_table = set()
    found = list(tables(lines))
    for _sep, rows in found:
        in_table.update(rows)

    orphans = [(i + 1, lines[i][:70]) for i, line in enumerate(lines)
               if ROW_RE.match(line) and i not in in_table]

    if orphans:
        print(f'check_soundness_tables: FAILED — {len(orphans)} row(s) render as RAW TEXT, not as table rows.')
        print('  A blank line, a paragraph or a heading between the separator and a row ends the table.')
        print('  Move the intervening prose BELOW the rows, or give the block its own header+separator.')
        for n, text in orphans:
            print(f'    line {n}: {text}')
        print('  NOTE: pipe counts are irrelevant here and checking them is how this was missed five times.')
        return 1

    total = sum(len(r) for _s, r in found)
    print(f'check_soundness_tables: OK — {len(found)} table(s), {total} row(s), every row inside one.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
