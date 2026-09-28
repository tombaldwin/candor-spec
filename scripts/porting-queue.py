#!/usr/bin/env python3
"""Which CLOSED defect classes has nobody asked of the other engines? SOUNDNESS R777.

    python3 scripts/porting-queue.py                 # counts per origin engine
    python3 scripts/porting-queue.py --emit out.tsv  # the question list itself
    python3 scripts/porting-queue.py --selftest

WHY. `candor` has four independent engines that must agree, and a defect found in one is a QUESTION
for the other three. Measured 2026-09-28: of **603 closed rows, only 24% mention a cross-engine check
at all**, so roughly 460 known classes have never been asked elsewhere. That pool is not theoretical —
R773 (a module qualifier silencing the classifier in swift) is ts's R239/R281 one language over, and it
was found by ACCIDENT while a lane measured something unrelated. Finding it deliberately would have
cost a grep.

The denominators say the same thing from the other side: rust has 193 closed rows and swift 92, java 69,
ts 53. rust does not carry the most open sins because it is the worst engine; it carries them because it
has been examined nearly four times as hard. The other three are under-examined, not clean.

WHAT THIS IS AND IS NOT. It emits QUESTIONS, never verdicts. A row appearing here means "nobody recorded
asking the other engines", not "the other engines have this defect" — the answer may well be no, and a
'no' recorded is worth as much as a hit because it stops the question being re-asked.

**IT IS DELIBERATELY OVER-INCLUSIVE, and that is the correct error direction.** A false positive costs
one cheap question; a false negative is a live sin nobody asks about for another year. So the sin filter
below is broad, and the cross-engine-checked filter is narrow — a row is only treated as ALREADY ASKED
when it says so plainly. Do not tune this toward a shorter list.

WHAT IT CANNOT SEE, stated in the same breath as its counts (R766's lesson: a probe that reports a
confident number over the wrong set is worse than no probe):
  - It reads the register, not the engines. A class checked in code review and never written down is
    invisible to it and will be re-asked. That is the cheap direction.
  - "Mentions a cross-engine check" is a TEXT test. A row saying "java reads bytecode so this cannot
    arise" counts as asked; a row that checked ts in a lane transcript does not.
  - Closed rows carry no `DIR=` token (that gate covers open rows only), so the sin filter here is
    lexical and will admit precision and fabrication rows. A lane working the list should expect to
    discard some as "not a silence class" and say so.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINES = ("rust", "swift", "java", "ts")

# Broad on purpose — see the docstring. Anything that smells like a silence class earns a question.
SIN = re.compile(r'SILENT UNDER-REPORT|CARDINAL SIN|silent under-report|cardinal sin|silently pure|'
                 r'reads? pure|certified pure|goes? silent|ABSENT FROM|absent from `functions|'
                 r'purity claim|exits? 0 over|no consumer can join|lost|erased|invisible to', re.I)

# Narrow on purpose — only a plain statement counts as "already asked".
ASKED = re.compile(r'four-way|all four engines|all four|verified immune|confirmed immune|'
                   r'(?:java|ts|rust|swift)\s+(?:and\s+\w+\s+)?(?:are\s+|is\s+|both\s+)?'
                   r'(?:verified\s+)?(?:clean|immune|unaffected)|'
                   r'does not arise in|swept in (?:all )?(?:three|four)', re.I)


# MECHANISM-BOUND: a class that cannot cross into a given target because the target's language or
# analysis route has no counterpart. Measured by the 2026-09-28 pilot (SOUNDNESS R784): of 201 rows
# facing ts, ~74 were bound this way — macros and `#[cfg]` (no TS equivalent), `Drop`/ownership/borrow,
# crate/npm ecosystem tables, harness rows, and rust/swift path-and-module resolution that the
# TypeScript checker simply answers. Asking those one at a time is waste; ONE structural answer retires
# the family. This is advisory, not a filter — the row is still emitted, flagged, so a lane can skip a
# group with its eyes open rather than have the queue quietly decide for it.
BOUND = (
    (re.compile(r'macro_rules|#\[cfg|proc-?macro|\bmacro-borne\b|\bmacro expansion\b|\bderive macro\b',
                re.I), "macro/cfg", ("ts", "java")),
    (re.compile(r'impl Drop\b|\bdrop glue\b|drop-glue|\bDrop impl|borrow check|\bownership\b|'
                r'\bmove semantics\b', re.I), "ownership/Drop", ("ts", "java", "swift")),
    (re.compile(r'\b(crate|npm|maven|registry)[- ](table|list|allowlist|denylist|census)\b|'
                r'\bknown[- ](crates|packages)\b', re.I), "ecosystem table", ()),
)

# CALIBRATED AGAINST THE PILOT, because the first cut of these patterns was wrong in the DANGEROUS
# direction. It flagged 148 of the 201 ts-facing rows as mechanism-bound where the pilot, having actually
# asked 42 of them, measured ~74 — because `crate` appears in nearly every rust row and `derive` in many,
# so "mentions an ecosystem word" was standing in for "is about an ecosystem table". Over-flagging makes a
# lane SKIP askable questions, which is the one error this whole tool exists to avoid; the docstring's
# over-inclusion argument applies to this filter too. The patterns above therefore require the row to be
# ABOUT the mechanism rather than to mention it, and the expected order of magnitude is ~70-80 for ts.
# If a future change pushes that number far above the pilot's, the patterns have drifted, not the register.


def bound_for(line, target):
    """Which mechanism, if any, stops this class reaching `target`. Advisory."""
    for rx, label, targets in BOUND:
        if rx.search(line) and (target in targets or not targets):
            return label
    return None


def scan(path=None, open_ids=None, target=None):
    """(questions, already_asked, not_sin) over CLOSED rows.

    `target` names the engine the questions are FOR. Two corrections the pilot measured:
      - a target engine's OWN rows are questions for the other three, never for itself. Emitting them
        overstated a ts lane's pool by 34 of 235.
      - mechanism-bound rows are flagged so a lane can retire a family in one answer.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import soundness_row
    q, asked, notsin = [], 0, 0
    for line in (path or ROOT / "SOUNDNESS.md").read_text().split("\n"):
        rid = soundness_row.row_id(line)
        if not rid:
            continue
        if open_ids is not None and rid in open_ids:
            continue
        m = re.match(r'^\|+ R\d+[a-z]? ([a-z][a-z -]{0,20}?):(?!:)', line)
        eng = m.group(1).strip() if m else None
        if eng not in ENGINES:
            continue          # instrument/spec/family rows port to nothing
        if not SIN.search(line):
            notsin += 1
            continue
        if ASKED.search(line):
            asked += 1
            continue
        if target and eng == target:
            continue      # a row's own engine is not asked about itself
        cells = re.split(r'(?<!\\)\|', line)
        claim = re.sub(r'\*\*|`|\[\[|\]\]', '', cells[1] if len(cells) > 1 else "").strip()
        claim = re.sub(r'^R\d+[a-z]?\s+[a-z -]+:\s*', '', claim)
        claim = re.sub(r'\s+', ' ', claim)[:160]
        q.append((eng, rid, claim, bound_for(line, target) if target else None))
    return q, asked, notsin


def open_id_set():
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "soundness-status.py"), "--ids"],
                       capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("soundness-status.py --ids exited %d" % r.returncode)
    return {l.strip() for l in r.stdout.split("\n") if re.match(r'^R\d+[a-z]?$', l.strip())}


def main(argv):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--emit")
    ap.add_argument("--for", dest="target", choices=ENGINES)
    ap.add_argument("--selftest", action="store_true")
    a, _ = ap.parse_known_args(argv[1:])
    if a.selftest:
        return selftest()
    q, asked, notsin = scan(open_ids=open_id_set(), target=a.target)
    from collections import Counter
    by = Counter(e for e, _, _, _ in q)
    print("PORTING QUESTIONS — closed rows whose class nobody recorded asking elsewhere")
    for e in ENGINES:
        print("  from %-6s %4d question(s)" % (e, by.get(e, 0)))
    print("  %d closed row(s) already state a cross-engine check; %d are not silence-class" % (asked, notsin))
    if a.target:
        bnd = Counter(b for _, _, _, b in q if b)
        askable = sum(1 for _, _, _, b in q if not b)
        print("\n  FOR %s: %d row(s) after excluding its own; %d are MECHANISM-BOUND and retire in groups:"
              % (a.target, len(q), sum(bnd.values())))
        for lab, n in bnd.most_common():
            print("      %-18s %d" % (lab, n))
        print("  GENUINELY ASKABLE: %d" % askable)
    print("\n  TOTAL %d. Each is a QUESTION for the other three engines, not a claim about them." % len(q))
    print("  A recorded 'no' is worth as much as a hit: it stops the question being re-asked.")
    if a.emit:
        with open(a.emit, "w") as fh:
            fh.write("# origin\trow\tclass (truncated) — QUESTIONS, not verdicts. See scripts/porting-queue.py\n")
            for e, rid, claim, b in sorted(q, key=lambda t: (t[0], int(re.sub(r'\D', '', t[1])))):
                fh.write("%s\t%s\t%s\t%s\n" % (e, rid, b or "askable", claim))
        print("\n  wrote %s" % a.emit)
    return 0


def selftest():
    import tempfile
    bad = 0

    def drive(name, body, want_q, want_asked=None):
        nonlocal bad
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "REG.md"
            f.write_text("| id | date | engine | evidence | notes |\n|---|---|---|---|---|\n" + body)
            q, asked, _n = scan(f, open_ids=set())
            ok = len(q) == want_q and (want_asked is None or asked == want_asked)
            print("  %s %-56s q=%d asked=%d" % ("ok  " if ok else "FAIL", name, len(q), asked))
            if not ok:
                bad += 1

    drive("a closed sin-class row becomes a question",
          "| R900 rust: **a SILENT UNDER-REPORT** | d | rust — CLOSED | e | n |\n", 1)
    drive("a row stating a four-way check is NOT re-asked",
          "| R901 rust: **a SILENT UNDER-REPORT** | d | rust — CLOSED four-way | e | n |\n", 0, 1)
    drive("a row saying java is verified immune is NOT re-asked",
          "| R902 rust: **reads pure** | d | rust — CLOSED; java verified immune | e | n |\n", 0, 1)
    drive("a non-silence row is not a question",
          "| R903 rust: a precision nicety | d | rust — CLOSED | e | n |\n", 0)
    drive("an instrument row ports to nothing",
          "| R904 instrument: **a SILENT UNDER-REPORT** | d | instrument — CLOSED | e | n |\n", 0)
    # OVER-INCLUSION IS THE POINT: a row that merely says "lost" earns a question rather than being
    # filtered away. If this case ever "fails", do not narrow the regex — read the docstring first.
    drive("a vaguely-worded row STILL earns a question (by design)",
          "| R905 swift: an effect was lost at the boundary | d | swift — CLOSED | e | n |\n", 1)
    print("porting-queue selftest: " + ("OK" if not bad else "FAILED (%d)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
