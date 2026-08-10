#!/usr/bin/env bash
# Run ONE part of the conformance suite, for iterating on that part.
#
# WHY: a full run is ~476s, but the shared setup is 8s and every part builds its own fixtures under its
# own $W subdirectory. Iterating on PART 36 costs 476s of wall clock for ~44s of relevant work, and the
# other 432s says nothing about the row being edited. Measured, by timestamping a real run's stdout.
#
# HOW THE BOUNDARIES ARE FOUND, and why not the obvious way. run.sh is 5,800 lines written over months
# and its COMMENT headers are not a grammar: 65 comment lines name a part, two of them only because they
# mention one in prose, and the sets do not line up with the sections that actually score. A filter built
# on them sliced at the wrong line and mislabelled a section — so boundaries come instead from the two
# markers that are unambiguous because the suite PRINTS them:
#
#   echo "[35] …"        a part's OPENING header   (25 of these)
#   echo "PART 35 — …"   a part's CLOSING verdict  (19 of these; 5 parts have both)
#
# A part runs from the end of the previous part's block to its own last marker. Every slice is then
# CHECKED rather than trusted: it must contain markers for exactly one part id — zero would pass
# vacuously, two would run a neighbour and score it under the wrong name — and it must parse.
#
# WHAT A SLICE MAY CARRY: an id's slice can include adjacent work that has NO marker of its own (PARTs
# 1–6 print their results a different way). That makes a filtered run slower than the part alone, never
# narrower than it. It can never carry a part that does have its own id — that is what the check enforces.
#
# IF IT DIES ON AN UNSET VARIABLE: that part reads state an earlier part built. Ask for both ids, or run
# the full suite. run.sh is `set -u`, so this fails loudly rather than testing nothing.
#
# A FILTERED RUN IS NOT A CONFORMANCE RESULT and refuses to print `conformance: OK`. The suite's value is
# that the parts constrain each other, and a green subset is the exact shape a false all-clear takes here.
#
# Usage:   conformance/part.sh 36   · conformance/part.sh 24 25   · --list   · --check
# Exit:    the extracted run's rc · 2 if a part could not be located or its slice failed the check
#
# `--check` extracts EVERY part and syntax-checks it without running anything (~10s). Run it
# after editing run.sh: it is what catches a new section whose shape this file's boundary rules miss,
# before the miss shows up as a filtered run that quietly tested less than it claimed.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/run.sh"
[ -f "$SRC" ] || { echo "part.sh: no run.sh beside me" >&2; exit 2; }
[ $# -gt 0 ] || { echo "usage: part.sh <part-id…>   e.g. part.sh 36 · part.sh --list" >&2; exit 2; }

# The extract MUST live beside run.sh. run.sh derives `HERE` from `BASH_SOURCE[0]` and then resolves the
# engines (`$HERE/../../candor-rust`) and every tracked fixture (`$HERE/gate`, `$HERE/policy`, …) from it,
# so an extract run out of /tmp looks for candor-rust in /tmp and dies at the build step. It is gitignored
# and removed on exit, including on interrupt — a leftover here is the kind of stray file the suite's own
# porcelain guard exists to catch.
OUT="$HERE/.part-run.$$.sh"
trap 'rm -f "$OUT"' EXIT INT TERM

if [ "$1" = "--check" ]; then
  # "$HERE/part.sh", NOT "$0". Invoked as `bash part.sh --check` from this directory, `$0` is the bare
  # name, which is not on PATH — so `ids` came back EMPTY, the loop never ran, and this printed
  # "all 0 slices resolve to exactly one part and parse" at exit 0. A checker that reports success having
  # checked nothing is the exact vacuity this file exists to prevent, in the file itself.
  ids=$("$HERE/part.sh" --list | sed -n '3p')
  [ -n "$ids" ] || { echo "part.sh --check: could not enumerate the parts — refusing to report a result" >&2; exit 2; }
  bad=0; n=0
  for id in $ids; do
    n=$((n+1))
    if ! out=$("$HERE/part.sh" --extract-only "$id" 2>&1); then
      printf "  %-6s ✘ %s\n" "$id" "$(printf '%s' "$out" | head -1)"; bad=1
    fi
  done
  if [ "$bad" = 0 ]; then
    echo "part.sh --check: all $n slices resolve to exactly one part and parse"
  else
    echo "part.sh --check: FAILURES above — the boundary rules do not cover run.sh's current shape" >&2
  fi
  exit "$bad"
fi

EXTRACT_ONLY=
if [ "$1" = "--extract-only" ]; then EXTRACT_ONLY=1; shift; fi

python3 - "$SRC" "$OUT" "$@" <<'PY' || exit 2
import re, sys
src, out, argv = sys.argv[1], sys.argv[2], sys.argv[3:]
L = open(src).read().split("\n")

HDR = re.compile(r'^echo "\[([0-9]+[a-z]?)\]')
VER = re.compile(r'^echo "PART ([0-9]+[a-z]?)\b')

marks = []                                    # (line, id, kind)
for i, l in enumerate(L):
    m = HDR.match(l)
    if m:
        marks.append((i, m.group(1), "hdr")); continue
    m = VER.match(l)
    if m:
        marks.append((i, m.group(1), "ver"))
if not marks:
    sys.exit("part.sh: run.sh prints no part headers or verdicts — has its format changed?")

tail_at = next((i for i, l in enumerate(L) if l.startswith('[ "$rc" -eq 0 ]')), None)
if tail_at is None:
    sys.exit("part.sh: could not find run.sh's final verdict gate — refusing to guess where the parts end")

# Consecutive markers naming the same id are ONE part (a header and its verdict; PART 5b opens twice).
groups = []
for line_no, pid, kind in marks:
    if groups and groups[-1][0] == pid:
        groups[-1][1].append((line_no, kind))
    else:
        groups.append((pid, [(line_no, kind)]))

# A verdict is scored by an `if … fi` that must travel with its own part, never head the next slice.
def block_end(i):
    j, depth, opened = i + 1, 0, False
    while j < len(L):
        s = L[j].strip()
        if re.match(r'^(if|for|while|case)\b', s):
            depth += 1; opened = True
        elif s in ("fi", "done", "esac"):
            depth -= 1
            if opened and depth <= 0:
                return j
        elif not opened and s and not s.startswith(("&&", "||", "echo", "#")):
            return j - 1            # the verdict echo was not followed by a block at all
        j += 1
    return min(i + 1, len(L) - 1)

# The PREAMBLE is everything before the first marker: `set -u`, rc=0, $W, engine discovery, and PART 1's
# own body. It is prepended to every filtered run — without it a part fails on an unset variable, which
# is loud but useless. The first section therefore starts AT its marker, not at line 0.
preamble = list(range(0, marks[0][0]))

sections, prev_end = [], marks[0][0] - 1
for idx, (pid, ms) in enumerate(groups):
    last_line, last_kind = ms[-1]
    if last_kind == "ver":
        end = block_end(last_line)
    else:
        end = (groups[idx + 1][1][0][0] - 1) if idx + 1 < len(groups) else tail_at - 1
    end = min(end, tail_at - 1)
    sections.append((pid, prev_end + 1, end))
    prev_end = end

if argv == ["--list"]:
    print(f"  {len(sections)} addressable parts of conformance/run.sh:\n")
    print("  " + "  ".join(pid for pid, _, _ in sections))
    print("\n  Parts printing no `[id]` header and no `PART id` verdict (1–6, 11, 12, 17 …) have no id here;")
    print("  they ride along inside a neighbouring slice rather than being addressable on their own.")
    sys.exit(0)

want = {a.lower() for a in argv}
by_id = {}
for pid, s, e in sections:
    by_id.setdefault(pid, []).append((s, e))
missing = want - set(by_id)
if missing:
    sys.exit(f"part.sh: run.sh names no part {sorted(missing)} — `part.sh --list` shows what is addressable")

keep = list(preamble)
chosen = []
for pid in sorted(want):
    for s, e in by_id[pid]:
        chosen.append((pid, s, e))
        keep.extend(range(s, e + 1))

# CHECK, do not trust: a slice must carry markers for exactly one id.
for pid, s, e in chosen:
    # A SET cannot see a DUPLICATE. `sorted({…})` deduped, so an id appearing twice in run.sh produced two
    # slices that each looked clean, `--check` said "all 40 slices resolve to exactly one part", and
    # asking for that id extracted BOTH ranges — a neighbouring part's body scored under the wrong name,
    # which is verbatim what the header of this file says the check prevents.
    if sum(1 for p2, _, _ in sections if p2 == pid) != 1:
        sys.exit(f"part.sh: run.sh names part {pid} more than once — a filtered run would extract every "
                 f"one of them and score a neighbour under this name. Fix the duplicate id.")
    inside = sorted({p for i, p, _ in marks if s <= i <= e})
    if inside != [pid]:
        sys.exit(f"part.sh: the slice computed for part {pid} carries markers for {inside} — refusing to "
                 f"run a range this file cannot justify. Run conformance/run.sh.")

# Keep the trailing crash-vs-divergence diagnosis; drop the `conformance: OK / FAILED` verdict itself — a
# filtered run has no standing to print either. It is backslash-continued, so consume the continuation.
i = tail_at
while i < len(L) and L[i].rstrip().endswith("\\"):
    i += 1
tail_lines = [j for j in range(i + 1, len(L)) if L[j].strip() != 'exit "$rc"']
if len(tail_lines) == len(range(i + 1, len(L))):
    sys.exit("part.sh: run.sh's tail no longer ends in `exit \"$rc\"` — the FILTERED banner would either "
             "be unreachable or change the exit code. Check the boundary rules before trusting this.")
keep.extend(tail_lines)

body = [L[i] for i in sorted(set(keep))]
body += [
    'echo',
    'echo "part.sh: FILTERED RUN — part(s) ' + " ".join(sorted(want)) + f' of {len(sections)}."',
    'echo "  Not a conformance result. The parts constrain each other, and a green subset is the shape a"',
    'echo "  false all-clear takes here. Run conformance/run.sh before believing anything."',
    'exit "$rc"',
]
open(out, "w").write("\n".join(body) + "\n")
PY

[ -s "$OUT" ] || exit 0   # --list printed; nothing to run

bash -n "$OUT" || {
  echo "part.sh: the extracted script does not parse — a boundary probably falls inside a heredoc or a" >&2
  echo "         block form this file does not recognise. Run conformance/run.sh; do not patch around it." >&2
  exit 2
}
[ -n "$EXTRACT_ONLY" ] && exit 0

# A part that reads state an EARLIER part built dies on `set -u` — but not before printing FAIL lines
# computed from fixtures that were never made. Measured: filtering to PART 32 alone prints two candor-java
# FAILs and then dies on an unbound $GDIR, and PART 32 is green in the full suite. So a filtered run can
# manufacture a false RED as easily as a vacuous green, and bash's own exit for an unbound variable is 1 —
# indistinguishable from a real divergence. Catch it and say the run decided nothing.
LOG="$(mktemp)"; trap 'rm -f "$OUT" "$LOG"' EXIT INT TERM
cd "$HERE" || exit 2
bash "$OUT" 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
if grep -q "unbound variable" "$LOG"; then
  echo
  echo "part.sh: INCONCLUSIVE — this part reads state an earlier part builds, and died on it."
  echo "  Nothing above is evidence, including any FAIL lines: they were computed against fixtures"
  echo "  this run never made. Name the part it depends on too, or run conformance/run.sh."
  exit 2
fi
exit "$rc"
