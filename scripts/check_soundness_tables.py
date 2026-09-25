#!/usr/bin/env python3
"""Every SOUNDNESS row must render as a table row, AND carry its table's number of cells.

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

SECOND PROPERTY, ADDED 2026-09-09 (SOUNDNESS R343) — CELL COUNT, and it is a different failure from
the one above rather than the pipe-counting mistake this docstring warns about. The warning is that
counting pipes cannot tell you whether a row RENDERS; that is still true, and contiguity is still
checked first. But a row that renders correctly can still be read wrong: the register is consumed BY
COLUMN — the status audit reads column 3 to decide whether a row is open — and an UNESCAPED PIPE
inside a cell (`|h|`, `matches!(a | b)`, `|| path.ends_with(..)`) splits it and shifts every column
after it one to the right. Nothing errors and the table still draws.

Measured the day this was added: 22 of 275 rows were malformed. Five had an EXTRA remedy cell,
appended over time as a new COLUMN rather than as more text in the existing one. One had no trailing
pipe at all and had been counting as four columns in a five-column table since 2026-09-04. Two were
written that same session by the agent that then found them.

The file has MORE THAN ONE TABLE, with different widths, so each row is checked against the header of
the table it is actually in — never against a global constant. The first audit run that day assumed
one table and produced 44 false positives.

    python3 scripts/check_soundness_tables.py [<file>]      # default: SOUNDNESS.md beside this repo

Exit 0 clean, 1 with the offending line numbers, 2 if the file cannot be read.
"""
import re
import sys
from pathlib import Path

# THE RECOGNISER IS SHARED NOW (SOUNDNESS R641). This file had TWO copies of it and
# `soundness-status.py` three more, and they disagreed: a `|| R524` row was seen here and NOT there, so
# it vanished from the shipping-defect list while this tool went red on its cell count. One module,
# imported by both, with one selftest table — `scripts/soundness_row.py`.
from soundness_row import row_id, split_cells   # noqa: E402
import soundness_row                            # noqa: E402
# …AND THE MALFORMED SPELLINGS, which is the whole point (added 2026-09-21).
# THIS CHECKER WAS VACUOUS AGAINST A DOUBLED LEADING PIPE. `|| R524 …` renders in GFM as a row with an
# EMPTY first cell, shifting every column one to the right — precisely the corruption the cell-count
# property exists to catch — and ROW_RE matched neither spelling, so the orphan scan skipped it AND the
# cell-count loop `continue`d past it. The file printed OK over a six-cell row in a five-column table.
# Measured, not suspected: injecting `||` before R524 left the verdict at OK.
#
# That is this docstring's own warning ("a validator that measures the wrong property is worse than
# none") committed inside the validator. A row is therefore identified by its ID appearing as the first
# NON-EMPTY cell, not by a literal prefix — so a malformed row is SEEN, and then fails on cell count
# like any other.


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
               if row_id(line) and i not in in_table]

    if orphans:
        print(f'check_soundness_tables: FAILED — {len(orphans)} row(s) render as RAW TEXT, not as table rows.')
        print('  A blank line, a paragraph or a heading between the separator and a row ends the table.')
        print('  Move the intervening prose BELOW the rows, or give the block its own header+separator.')
        for n, text in orphans:
            print(f'    line {n}: {text}')
        print('  NOTE: pipe counts are irrelevant here and checking them is how this was missed five times.')
        return 1

    # SECOND PROPERTY (R343): every row carries its OWN table's cell count. Checked only after the
    # contiguity check passes — a row that does not render as a row has no cells to count.
    shape = []
    for sep, rows in found:
        width = lines[sep].count('|') - 1
        for i in rows:
            if not row_id(lines[i]):
                continue
            # UNESCAPED pipes only: `\\|` inside a cell is content, and is the correct spelling.
            got = len(re.split(r'(?<!\\)\|', lines[i])) - 2
            if got != width:
                shape.append((row_id(lines[i]) or '?', i + 1, got, width))

    if shape:
        print(f'check_soundness_tables: FAILED — {len(shape)} row(s) do not carry their table\'s cell count.')
        print('  The register is read BY COLUMN. An unescaped pipe inside a cell shifts every column')
        print('  after it one to the right, and nothing errors — the table still draws.')
        for rid, n, got, width in shape:
            print(f'    {rid:<6} line {n}: has {got} cell(s), its header declares {width}')
        print('  Escape pipes inside the cell as \\| — backtick spans are NOT exempt. A row with one')
        print('  cell too many is almost always a remedy note appended as a new COLUMN instead of as')
        print('  more text in the existing one: merge it, do not widen the table.')
        return 1

    # THIRD PROPERTY (R588): A ROW ID IS UNIQUE, AND NOTHING CHECKED IT. On 2026-09-24 the register
    # held TWO rows numbered R540 — a swift ternary-receiver sin and a rust dispatch-guard sin, filed
    # nine lines apart in different batches, both OPEN. `soundness-status.py` keys its report by row id,
    # so one of the two was silently absent from every count and every listing it printed; the defect
    # surfaced only because a bucket-count taken two ways disagreed by one. `[[R540]]` in a third row
    # resolved to whichever the reader guessed.
    #
    # This is the failure CLAUDE.md's row-ID paragraph is written about ("a wrong ID silently conflates
    # two unrelated findings in every future grep") — measured there for AGENTS inventing an id, and it
    # happens to the coordinator appending one. The next free number is the MAXIMUM, not the last row:
    #     grep -oE '^\| R[0-9]+' SOUNDNESS.md | grep -oE '[0-9]+' | sort -n | tail -1
    # THE LETTER SUFFIX IS PART OF THE ID. R529, R529b and R529c are THREE different rows — the
    # register splits one finding into separately measurable parts that way, and on 2026-09-22 a base row
    # was CLOSED while its lettered sibling was open. Collapsing them reported four phantom duplicates on
    # the first run of this guard, which is how the point got made. This used to be a SECOND local scan
    # (`full_id`) because the first one dropped the suffix; both carried the `cells[:2]` bound that
    # SOUNDNESS R640 measured, so `||| R900` and `| **R900** |` escaped this property entirely. The
    # shared recogniser keeps the suffix and reads the first NON-EMPTY cell whatever its index.
    seen: dict = {}
    for _sep, rows in found:
        for i in rows:
            rid = row_id(lines[i])
            if rid:
                seen.setdefault(rid, []).append(i + 1)
    dupes = {r: ns for r, ns in seen.items() if len(ns) > 1}
    if dupes:
        print(f'check_soundness_tables: FAILED — {len(dupes)} row id(s) used more than once.')
        print('  Two rows with one id conflate two findings in every grep, and the status tool keys')
        print('  its report by id, so one of them is absent from the shipping-defect list entirely.')
        for rid, ns in sorted(dupes.items()):
            print(f'    {rid}: lines {", ".join(str(n) for n in ns)}')
        print('  Renumber the row with FEWER in-code references to the MAXIMUM id + 1, and update any')
        print('  [[link]] that meant it. Do not renumber the one whose id is baked into engine source.')
        return 1

    total = sum(len(r) for _s, r in found)
    print(f'check_soundness_tables: OK — {len(found)} table(s), {total} row(s), every row inside one '
          f'and carrying its own table\'s cell count.')
    return 0


def selftest() -> int:
    """CALIBRATED, not asserted. Until 2026-09-25 this file had no selftest at all, which is how it
    shipped blind to `|| R524` for twelve days and to `||| R900` / `| **R900** |` for four more. Each
    case below is a row shape the tool was once green over."""
    print('check_soundness_tables selftest — the shared recogniser, then this tool on a poisoned file')
    bad = soundness_row.selftest()

    import tempfile
    good = ['# fixture', '', '| entry | date | engine | class | outcome |',
            '|---|---|---|---|---|',
            '| R900 a row | d | e | c | o |',
            '| R901 another | d | e | c | o |', '']

    def verdict(body, label, want):
        nonlocal bad
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as fh:
            fh.write('\n'.join(body))
            p = fh.name
        argv = sys.argv
        sys.argv = [argv[0], p]
        try:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main()
        finally:
            sys.argv = argv
        ok = rc == want
        bad += not ok
        print('  %s rc=%d want %d  %s' % ('ok  ' if ok else 'FAIL', rc, want, label))

    verdict(good, 'a clean fixture', 0)
    # R641 — one leading empty cell. The 2026-09-21 fix was written for this and it must stay caught.
    verdict(good[:5] + ['|| R901 a doubled leading pipe | d | e | c | o |', ''],
            'a doubled leading pipe is CAUGHT on cell count', 1)
    # R640 — two leading empty cells, and a bolded id. Both escaped every property before the shared
    # recogniser; the second is a DUPLICATE ID, which is the property that matters most here.
    verdict(good[:6] + ['||| R900 two leading empty cells, a duplicate id | d | e | c | o |', ''],
            'two leading empty cells + duplicate id is CAUGHT', 1)
    verdict(good[:6] + ['| **R900** a bolded duplicate id | d | e | c | o |', ''],
            'a bolded duplicate id is CAUGHT', 1)
    # The contiguity property, which is the one this file was written for.
    verdict(good[:5] + ['', '| R901 orphaned by a blank line | d | e | c | o |', ''],
            'a row orphaned by a blank line is CAUGHT', 1)
    # And the control for the widened recogniser: a row whose id sits past the first non-empty cell is
    # NOT a register row, so widening must not have swept prose in.
    verdict(good + ['| a paragraph mentioning R900 | and a second cell |', ''],
            'prose naming a row is NOT read as one', 0)

    if bad:
        print('check_soundness_tables SELFTEST: %d FAILED' % bad)
    else:
        print('check_soundness_tables SELFTEST: OK')
    return 1 if bad else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
