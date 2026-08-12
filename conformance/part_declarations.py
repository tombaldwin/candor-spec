#!/usr/bin/env python3
"""
EVERY SLICE OF run.sh DECLARES WHICH ENGINES IT DRIVES AND WHAT PROVES ITS ROWS COULD ANSWER.

This enforces an INTERNAL INVARIANT OF THE SUITE, not a SPEC clause — it is listed in clause_check.py's
register with an empty SPEC_CLAUSES so "no clauses" is a recorded fact rather than an omission.

WHY THIS EXISTS — the two failures it is built for, stated as they happened
---------------------------------------------------------------------------
(1) A PART SILENTLY COVERING FEWER ENGINES THAN IT CLAIMS. PART 39 shipped green covering three of four
    engines — swift has `gains` and simply was not invoked. Falsification cannot catch this: a row that
    never runs for swift still fails correctly when rust breaks. And it is not unique: writing these
    declarations found PART 40 probing ONLY rust's query binary while java/ts/swift all ship the same
    read verbs, and PART 4n's `tolerant` rows asking rust/java/ts under a claim that says "every OTHER
    engine".

(2) A ROW CREDITING A REFUSAL WITH NOTHING PROVING IT COULD ANSWER. PART 37 row (e) accepted any
    non-zero exit as "discloses in the machine channel" — it queried `pure_a`, a name in NO gate
    fixture, so every engine said "no function matching 'pure_a'" at exit 2 and scored PASS. The row
    had never once asked its question.

WHY DECLARATION, NOT INFERENCE — measured. An inference prototype (flag (part, verb, engine) where the
engine drives that verb elsewhere but not here) was measured against the real PART 39 bug: it caught it,
and emitted 8 PERMANENT false positives from PART 4k, whose loops a static scan cannot attribute.
1 true positive : 8 steady false — an ignored checker is worse than none, so it was deliberately not
built (BACKLOG, 2026-08-11). A DECLARATION has no attribution problem: the human states the contract,
and the machine checks it BOTH WAYS against a deliberately simple marker scan.

THE DECLARATION, one per slice, in the slice's own lines:

    # ENGINES: rust java ts; swift: no `tolerant` probe — <why, or GAP>
    # ENGINES: none — a static check; no engine binary runs
    # CONTROLS: rs_intact_control ti_control — <what the controls prove>
    # CONTROLS: none — <why no refusal or hedge is credited here>

  · ENGINES must account for ALL FOUR of rust/java/ts/swift — listed, or excluded WITH A REASON.
    That is the whole value: PART 39's shape (an engine with the verb, neither invoked nor named)
    becomes UNWRITABLE without this check naming it. A gap stays a gap, but a visible one.
  · a LISTED engine must have an invocation marker in the slice (declared-but-not-invoked = the
    vacuous claim, the worst kind, because the declaration is what a reader trusts);
  · an EXCLUDED engine must have NO marker (invoked-but-not-declared = drift; the part grew an
    engine and nobody updated its contract);
  · every un-annotated slice is an ERROR, never a skip — a half-annotated file makes this checker
    lie, so the set was completed in one pass and can only stay complete.

CONTROLS is mandatory-but-honest-about-being-weak: this file checks PRESENCE and that each named
identifier exists in the slice's EXECUTABLE lines (a control that exists only in a comment is the
vacuity again). It does NOT check that the control proves what the prose says — no script can. What it
can do is force the author to hold "what proves this row could answer?" in view at write time, which is
the step PART 37 (e) skipped — the same construction as clause_check.py's "the act of finding the quote
IS the check".

MARKERS, deliberately simple and printed on failure: an engine is "invoked" if a non-comment line of
the slice touches its binaries, its report artifacts, or its presence guards ($SCAN/$QUERY/$RUST_REPORT,
$JAR, $TS_DIR/TS_OK/TS_PRESENT, $SW_BIN/$SW_DIR/SW_OK/SW_PRESENT, and the CANDOR_* exports the
generator parts use). A guard-only mention counts as coverage-aware on purpose: every current slice
that branches on a guard drives the engine behind it, and a future counterexample should FAIL here and
force the declaration to say what is really going on.

KNOWN LIMIT, stated rather than papered over: the unit is the ADDRESSABLE SLICE — what part.sh runs and
what its --check validates — plus the preamble; the tail must stay engine-free. A slice whose RIDER
drives all four can mask a headline part covering three (PART 4n is the live example); the declaration's
prose is where a human records that, and this file cannot see it.

BOUNDARIES come from `part.sh --sections` — the one slicing implementation, the one --check validates —
never from a second parser that can drift from it.

    python3 part_declarations.py          # exit non-zero on any violation, 2 if it cannot even look
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINES = ("rust", "java", "ts", "swift")

# One pattern per engine. Scanned over NON-COMMENT lines only — the declarations themselves are
# comments, and a comment mentioning $SCAN is prose, not coverage.
MARKERS = {
    "rust":  re.compile(r'\$\{?(SCAN|QUERY)\b|CANDOR_SCAN_BIN|CANDOR_QUERY_BIN|\$RUST_REPORT\b'),
    "java":  re.compile(r'\$\{?JAR\b|CANDOR_JAVA_JAR'),
    "ts":    re.compile(r'\$\{?TS_DIR\b|\bTS_PRESENT\b|\bTS_OK\b|\bCANDOR_TS\b'),
    "swift": re.compile(r'\$\{?SW_(BIN|DIR|REPORT)\b|\bSW_PRESENT\b|\bSW_OK\b|\bCANDOR_SWIFT\b'),
}

DECL_ENGINES = re.compile(r'^# ENGINES:\s*(.*\S)\s*$')
DECL_CONTROLS = re.compile(r'^# CONTROLS:\s*(.*\S)\s*$')
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*$')

# Registered in clause_check.py; empty on purpose — this gate binds the suite to ITSELF, not to SPEC.md.
SPEC_CLAUSES = []


def sections():
    """(id, start, end) 1-based inclusive, from the slicing part.sh --check already validates."""
    part_sh = os.path.join(HERE, "part.sh")
    if not os.path.exists(part_sh):
        print("part_declarations: no part.sh beside me — refusing to invent slice boundaries")
        raise SystemExit(2)
    r = subprocess.run(["bash", part_sh, "--sections"], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.stderr.write(r.stderr)
        print("part_declarations: part.sh --sections failed — this check would pass over nothing")
        raise SystemExit(2)
    out = []
    for line in r.stdout.strip().split("\n"):
        pid, s, e = line.split("\t")
        out.append((pid, int(s), int(e)))
    return out


def parse_engines(text, pid, fails):
    """Return (listed, excluded) engine sets, or None after recording failures."""
    if text.startswith("none"):
        rest = text[len("none"):].strip()
        if not (rest.startswith("—") or rest.startswith("--")) or len(rest) < 4:
            fails.append(f"{pid}: `ENGINES: none` needs a reason (`none — <why no engine runs here>`)")
            return None
        return set(), set(ENGINES)
    fields = [f.strip() for f in text.split(";")]
    listed = fields[0].split()
    bad = [e for e in listed if e not in ENGINES]
    if bad or not listed:
        fails.append(f"{pid}: ENGINES lists {bad or 'nothing'} — the vocabulary is {list(ENGINES)}")
        return None
    if len(set(listed)) != len(listed):
        fails.append(f"{pid}: ENGINES lists an engine twice")
        return None
    excluded = set()
    for f in fields[1:]:
        if ":" not in f:
            fails.append(f"{pid}: exclusion `{f}` has no reason — the reason is the entire value here")
            return None
        names, reason = f.split(":", 1)
        if not reason.strip():
            fails.append(f"{pid}: exclusion of `{names.strip()}` carries an EMPTY reason")
            return None
        for n in names.replace(",", " ").split():
            if n not in ENGINES:
                fails.append(f"{pid}: exclusion names `{n}`, not an engine")
                return None
            excluded.add(n)
    listed = set(listed)
    if listed & excluded:
        fails.append(f"{pid}: {sorted(listed & excluded)} both listed and excluded — pick one")
        return None
    missing = set(ENGINES) - listed - excluded
    if missing:
        fails.append(f"{pid}: does not account for {sorted(missing)} — every engine is listed or "
                     f"excluded WITH A REASON. Writing that reason is the PART 39 prevention: an "
                     f"unmentioned engine is exactly how three-of-four ships as four.")
        return None
    return listed, excluded


def main():
    src = os.path.join(HERE, "run.sh")
    if not os.path.exists(src):
        print("FAIL: no run.sh beside part_declarations.py")
        return 2
    lines = open(src).read().split("\n")
    secs = sections()
    ids = [pid for pid, _, _ in secs]
    if len(set(ids)) != len(ids):
        print("FAIL: part.sh --sections reports a duplicate part id — declarations cannot be attributed")
        return 2
    # Vacuity floor: this suite has 44 addressable slices + preamble + tail today. Shrinking far below
    # that means the boundary source broke, not that the suite got small — refuse to bless it.
    if len(secs) < 20:
        print(f"FAIL: only {len(secs)} sections enumerated — the boundary source is broken, "
              f"and a green run over a fraction of the file is the vacuity this gate exists to stop")
        return 2

    fails = []
    checked = 0
    for pid, s, e in secs:
        body = lines[s - 1:e]
        code = [l for l in body if not l.strip().startswith("#")]
        code_text = "\n".join(code)
        invoked = {eng for eng, rx in MARKERS.items() if rx.search(code_text)}

        if pid == "tail":
            # The verdict printer is outside the declaration regime and must STAY engine-free.
            if invoked:
                fails.append(f"tail: run.sh's verdict tail now touches {sorted(invoked)} — either move "
                             f"that into a declared part or extend this regime to the tail")
            continue

        eng_decls = [l for l in body if DECL_ENGINES.match(l)]
        ctl_decls = [l for l in body if DECL_CONTROLS.match(l)]
        if len(eng_decls) != 1 or len(ctl_decls) != 1:
            fails.append(f"{pid}: found {len(eng_decls)} ENGINES / {len(ctl_decls)} CONTROLS "
                         f"declarations — every slice carries exactly one of each. An un-annotated "
                         f"slice is an ERROR, not a skip: a half-annotated file makes this checker lie.")
            continue
        checked += 1

        parsed = parse_engines(DECL_ENGINES.match(eng_decls[0]).group(1), pid, fails)
        if parsed:
            listed, excluded = parsed
            for eng in sorted(listed - invoked):
                fails.append(f"{pid}: declares {eng} but no {eng} marker appears in the slice — a "
                             f"VACUOUS CLAIM, the worst kind: the declaration is what a reader trusts. "
                             f"(markers: {MARKERS[eng].pattern})")
            for eng in sorted(invoked & excluded):
                fails.append(f"{pid}: invokes {eng} (marker: {MARKERS[eng].pattern}) while declaring "
                             f"it out — DRIFT: the part grew an engine, or the exclusion reason is false")

        ctext = DECL_CONTROLS.match(ctl_decls[0]).group(1)
        if ctext.startswith("none"):
            rest = ctext[len("none"):].strip()
            if not (rest.startswith("—") or rest.startswith("--")) or len(rest) < 4:
                fails.append(f"{pid}: `CONTROLS: none` needs a reason — say why no refusal or hedge "
                             f"is credited here, or name what proves the rows can answer")
        else:
            head = ctext.split("—")[0].split("--")[0].strip()
            names = head.split()
            prose = ctext[len(head):].strip()
            if not names or not all(IDENT.match(n) for n in names):
                fails.append(f"{pid}: CONTROLS must name identifiers then ` — <prose>` (got `{ctext[:60]}`)")
            elif not prose:
                fails.append(f"{pid}: CONTROLS names {names} with no prose — say what the control proves")
            else:
                for n in names:
                    if not re.search(r'(?<![A-Za-z0-9_-])' + re.escape(n) + r'(?![A-Za-z0-9_-])',
                                     code_text):
                        fails.append(f"{pid}: CONTROLS names `{n}` but it appears in no executable "
                                     f"line of the slice — a control that does not exist is the "
                                     f"PART 37 (e) shape restated as documentation")

    print(f"DECLARED COVERAGE — {checked} slices checked against their `# ENGINES:`/`# CONTROLS:` lines")
    if checked == 0:
        print("FAIL: zero declarations checked — this gate refuses to report success having asked nothing")
        return 2
    if fails:
        for f in fails:
            print(f"  ✘ {f}")
        print(f"DECLARED COVERAGE: FAILED — {len(fails)} violation(s)")
        return 1
    print(f"  every listed engine is invoked, every exclusion holds, every named control exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
