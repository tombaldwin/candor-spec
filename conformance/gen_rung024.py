#!/usr/bin/env python3
"""
PART 27 — the ⟨0.24⟩ RUNG'S BEHAVIOUR, as a cross-impl differential.

A whole rung of normative requirements shipped with nothing behind it: `grep -c` over `run.sh` returned
ZERO for `CONTRIBUTES`, `viaDispatchOn`, `dot-free`, `--class dynamic` and locale. This file is that
differential. A floor bump to 0.24 is gated on it existing AND on it having been seen to fail.

WHAT IT PINS, and on which engines. The ⟨0.24⟩ surfaces are NOT all four-way, and the rows say so in
their own output rather than skipping quietly:

  R1  §6.2 CONTRIBUTES — a reasonless `Unknown` ADDS `unresolved`, it does not DEFAULT to it   4-way + 4
  R2  §3.1 `viaDispatchOn` — the EXACT joined literal, sorted + deduplicated                   3-way
  R3  §3.1 the DOT-FREE frontier arm — disclosed verbatim, IDENTICALLY in both arms            3-way
  R4  §3.1 the SIDECAR TRIPLE — absent ≡ `{}` ≢ populated                                      3-way
  R5  §6.2 `--class` — `dynamic` excludes only `setup`, narrower filters DISCRIMINATE, and the
           flag's VALUE GRAMMAR refuses a filter it cannot honour                              4-way
  R6  §3.1 `gate --report` — byte-equality, the MUST NOT, and the three answerability refusals 4-way
  R8  §3.1 PRECEDENCE — a certain violation dominates a refusal; a refusal still writes a
           document that is fail-closed to a NAIVE reader                                      4-way
  R9  CROSS-ENGINE verdict KEY PARITY — byte-equality is WITHIN-engine and caught nothing when
           swift emitted `coverage.modules` for three years of `coverage.packages`                4-way
  R10 REPORT-ENVELOPE key parity — R9 compares the VERDICT; nothing compared the artifact that
           actually TRAVELS between engines and is chained as a dependency                        4-way
  R7  §2   LOCALE-INDEPENDENCE — the same input under two collations, byte for byte            4-way

  R2/R3/R4 are three-surface (rust, java, ts): candor-swift deliberately ships NO `callers` verb — it is
  a producer that writes the §2.2 hierarchy sidecar *for* the others. There is no swift frontier arm to
  write, and a "swift: SKIPPED" line would misdescribe that as a gap.
  R6 was two-engine until 2026-07-27 and this note said so for a week after it stopped being true.
  `gate --report` now ships in ALL FOUR, and the rust and ts branches were added to `q_gate` without this
  paragraph — or R1's gate cell — being revisited. That is the mundane half of a defect a review found:
  the NOSURF path those cells relied on became unreachable the moment every engine had a branch, so a
  cell that meant "this engine has no verb" silently started meaning nothing at all. **Coverage prose is
  load-bearing here** — it is what tells the next reader which cells are allowed to be empty.

WHY MOST ROWS RUN ON A HAND-WRITTEN REPORT. Every ⟨0.24⟩ surface here except R7 is a pure function of a
REPORT (plus its §2.2 sidecars) and a policy — that is the whole point of the rung: `gate --report`
exists precisely so the gate becomes reachable as a function of a GIVEN signature, and `callers
--include-unknown` / `unverified --class` were always report consumers. So the fixture is a report, not a
program, and the four engines are handed the SAME BYTES (under each one's own file-naming convention).
That removes the classifier from the loop entirely: a divergence here is a divergence in the CONSUMER,
which is exactly where ⟨0.24⟩ found its defects. It also means these rows need no compiler and no scan.

THE ORACLE IS THE SPEC, NOT ANOTHER ENGINE — and that is the difference from PARTs 24/25/26. Those are
self-differentials because the property is a relation between two runs of one engine. Here every clause
names a required ANSWER, and four engines agreeing on the wrong answer is the failure mode the ⟨0.24⟩
review actually found (the §6.2 divergence "every engine implemented faithfully"). So R1–R6 carry
expected values, taken verbatim from the clause text. R7 is the exception and IS a self-differential:
its oracle is the same engine's own output under a different `LC_ALL`.

RATCHET. `rung024-baseline.json`, same both-ways contract as PARTs 24–26: an unwaived failing cell fails
the suite, and a waiver whose cells ALL pass also fails it, so a waiver cannot outlive its defect.

VACUITY FLOOR (standing bar item 8). Three separate refusals, because "no failures" and "nothing ran"
print the same way if you let them:
  * a ROW with zero live cells FAILS — a fixture that stopped triggering is not a passing row;
  * the RUN with zero live cells overall FAILS;
  * a row whose own PRECONDITION collapsed (the unfiltered `unverified` selected nothing, the frontier
    came back empty, the equivalence policy found no violation) is VACUOUS, which is a FAILING verdict
    here, not a benign one.
A MIS-INVOCATION IS NEVER A FINDING. A CLI that exits non-zero with no parseable output, or a report
this harness failed to write, is verdict ERROR and prints "HARNESS/ENGINE INVOCATION" in the line. Both
prior property harnesses shipped a shape where a broken call rendered as a substantive statement about
candor; the guard is that ERROR never borrows a finding's wording and never reads as a refusal.

USAGE
    python3 gen_rung024.py
    python3 gen_rung024.py --only R2,R3 --keep
    python3 gen_rung024.py --baseline rung024-baseline.json      # the ratchet (PART 27)
"""
import json
import locale as _locale
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def envdir(var, rel):
    return os.environ.get(var) or os.path.normpath(os.path.join(HERE, rel))


CANDOR = envdir("CANDOR", "../../candor-rust")
CANDOR_JAVA = envdir("CANDOR_JAVA", "../../candor-java")
CANDOR_TS = envdir("CANDOR_TS", "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")

OK, FAIL, VACUOUS, ABSENT, NOSURF, ERROR = "OK", "FAIL", "VACUOUS", "ABSENT", "NOSURF", "ERROR"
# ABSENT  = the engine is not installed here. Not a pass, not a failure: it demands nothing.
# NOSURF  = the engine does not implement this surface AND that is the specified design (swift has no
#           `callers`; rust/ts have no `gate --report` yet). Named, never silently skipped.
# VACUOUS = the fixture stopped exercising the clause. FAILING, on purpose.
# ERROR   = this harness or the engine binary mis-fired. FAILING, and labelled as OUR fault, not a
#           statement about candor.
LIVE = (OK, FAIL, VACUOUS, ERROR)
FAILING = (FAIL, VACUOUS, ERROR)


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


# =====================================================================================================
# engines — presence, and the per-engine spelling of one shared report
# =====================================================================================================

def rust_query():
    b = os.environ.get("CANDOR_QUERY_BIN") or os.path.join(CANDOR, "target", "debug", "candor-query")
    return b if os.path.exists(b) else None


def rust_scan():
    b = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
    return b if os.path.exists(b) else None


def java_jar():
    j = os.environ.get("CANDOR_JAVA_JAR")
    if j and os.path.exists(j):
        return j
    d = os.path.join(CANDOR_JAVA, "build", "libs")
    c = [os.path.join(d, f) for f in os.listdir(d)] if os.path.isdir(d) else []
    c = [p for p in c if p.endswith("-all.jar")]
    return max(c, key=os.path.getmtime) if c else None


def ts_root():
    return CANDOR_TS if (shutil.which("node") and os.path.exists(os.path.join(CANDOR_TS, "query.mjs"))) else None


def swift_bin():
    b = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
    return b if os.path.exists(b) else None


def installed(engine):
    return {"rust": lambda: rust_query() and rust_scan(), "java": java_jar,
            "ts": ts_root, "swift": swift_bin}[engine]()


_ALIVE = {}


def alive(engine):
    """INSTALLED is not the same as WORKING, and the difference is the run.sh TS_PRESENT/TS_OK lesson: a
    present-but-broken engine must FAIL the suite, never read as absent — and, here, never read as an
    ANSWER. One `--help` per engine, cached. Measured with a zero-byte jar on `CANDOR_JAVA_JAR`: without
    this probe three cells printed "the frontier came back empty" and "unfiltered selected 0/7", which
    are sentences about candor produced by a CLI that never started."""
    if engine in _ALIVE:
        return _ALIVE[engine]
    cmd = {"rust": lambda: [rust_query(), "--help"],
           "java": lambda: ["java", "-jar", java_jar(), "--help"],
           "ts": lambda: ["node", os.path.join(ts_root(), "query.mjs"), "--help"],
           "swift": lambda: [swift_bin(), "--help"]}[engine]
    r = run(cmd())
    # STDOUT specifically. All four engines print `--help` to stdout; a corrupt jar or a missing entry
    # point writes to stderr and nothing else, and accepting stderr would call that alive.
    _ALIVE[engine] = bool(r.stdout.strip()) and r.returncode in (0, 1, 2)
    return _ALIVE[engine]


def present(engine):
    """Present == installed AND responsive. A cell for an installed-but-dead engine is BROKEN, and the
    caller turns that into ERROR rather than into a verdict."""
    return bool(installed(engine)) and alive(engine)


ENGINES = ["rust", "java", "ts", "swift"]

# Each engine discovers reports by its OWN naming convention (§3.3.1 + §2.2). One report, four spellings:
#   (stem written under the fixture dir, locator handed to the CLI)
STEM = {"rust": "report.app.scan", "java": "r", "ts": "r", "swift": "r.app.Swift"}
LOCATOR = {"rust": "report", "java": "r.json", "ts": "r", "swift": "r"}


def write_report(ws, engine, report, callgraph=None, hierarchy=None, hierarchy_raw=None):
    """Write ONE report (and its §2.2 sidecars) under `engine`'s naming. Returns the locator."""
    d = os.path.join(ws, engine)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):                     # delete outputs before measuring — no stale artefact
        p = os.path.join(d, f)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    stem = STEM[engine]
    with open(os.path.join(d, stem + ".json"), "w") as fh:
        json.dump(report, fh, indent=1)
    if callgraph is not None:
        with open(os.path.join(d, stem + ".callgraph.json"), "w") as fh:
            json.dump(callgraph, fh, indent=1)
    if hierarchy is not None:
        with open(os.path.join(d, stem + ".hierarchy.json"), "w") as fh:
            json.dump(hierarchy, fh, indent=1)
    elif hierarchy_raw is not None:
        with open(os.path.join(d, stem + ".hierarchy.json"), "w") as fh:
            fh.write(hierarchy_raw)
    return os.path.join(d, LOCATOR[engine])


def q_callers(engine, locator, target):
    """`callers <target> --include-unknown --json`. Returns (dict|None, stderr)."""
    if engine == "rust":
        r = run([rust_query(), "callers", "--report", locator, target, "--json", "--include-unknown"])
    elif engine == "java":
        r = run(["java", "-jar", java_jar(), "callers", "--report", locator, target, "--json",
                 "--include-unknown"])
    elif engine == "ts":
        r = run(["node", os.path.join(ts_root(), "query.mjs"), "callers", "--report", locator, target,
                 "--include-unknown"])
    else:
        return None, "no callers verb on this engine"
    # EMPTY STDOUT IS NOT AN EMPTY ANSWER. `json.loads(stdout or b"{}")` turns a CLI that never ran into
    # a well-formed document with no frontier — which this harness would then print as "the frontier came
    # back empty", a sentence about candor. Measured with a zero-byte jar on PATH: three rows read as
    # findings. A process that produced nothing gets ERROR, and ERROR says whose fault it is.
    if not r.stdout.strip():
        return None, f"exit {r.returncode}, no stdout: {r.stderr.decode()[:200]}"
    try:
        return json.loads(r.stdout), r.stderr.decode()[:200]
    except Exception:
        return None, (r.stderr.decode() or r.stdout.decode())[:200]


def _unverified_cmd(engine, locator, policy):
    if engine == "rust":
        return [rust_query(), "unverified", "--report", locator, "--policy", policy, "--json"]
    if engine == "java":
        return ["java", "-jar", java_jar(), "unverified", "--report", locator, "--policy", policy,
                "--json"]
    if engine == "ts":
        return ["node", os.path.join(ts_root(), "query.mjs"), "unverified", "--report", locator,
                "--policy", policy]
    return [swift_bin(), "unverified", "--report", locator, "--policy", policy]


def q_unverified(engine, locator, policy, klass=None):
    """`unverified --report … --policy … [--class …] --json`. Returns (dict|None, rc, stderr)."""
    cmd = _unverified_cmd(engine, locator, policy)
    if klass:
        cmd += ["--class", klass]
    r = run(cmd)
    if not r.stdout.strip():        # see q_callers: empty stdout is a mis-invocation, not an empty answer
        return None, r.returncode, f"exit {r.returncode}, no stdout: {r.stderr.decode()[:250]}"
    try:
        return json.loads(r.stdout), r.returncode, r.stderr.decode()[:300]
    except Exception:
        return None, r.returncode, (r.stderr.decode() or r.stdout.decode())[:300]


def q_gate(engine, locator, policy, gate_json=None):
    """`gate --report <locator> --policy <file> [--gate-json <f>]`. Returns rc (or None: no such verb)."""
    if engine == "rust":
        cmd = [rust_query(), "gate", "--report", locator, "--policy", policy]
    elif engine == "java":
        cmd = ["java", "-jar", java_jar(), "gate", "--report", locator, "--policy", policy]
    elif engine == "ts":
        cmd = ["node", os.path.join(ts_root(), "query.mjs"), "gate", "--report", locator,
               "--policy", policy]
    elif engine == "swift":
        cmd = [swift_bin(), "gate", "--report", locator, "--policy", policy]
    else:
        return None
    if gate_json:
        cmd += ["--gate-json", gate_json]
    return run(cmd).returncode


# =====================================================================================================
# R1 — §6.2 CONTRIBUTES: the counterexample the clause was written from
# =====================================================================================================
#
# The clause used to read "a function whose `Unknown` carries no recorded reason is TREATED AS
# `unresolved`" — keyed on the class set being EMPTY. Absence is not upward-closed, so acquiring a reason
# REMOVED the default, and the measured result was a counterexample to the monotone-denial corollary:
#
#     (a) calls ONE REASONLESS dep        -> REJECTED by deny Unknown[unresolved]
#     (b) calls ONE REASONED dep          -> correctly not rejected
#     (c) calls BOTH                      -> NOT REJECTED        <- adding a call turned red green
#
# (c) is the whole row. It is strictly worse-known than (a) and it used to PASS. (b) and (c) have the
# SAME CLASS SET under the absence reading ({dispatch} — because (c)'s set is non-empty, the default
# never fires), which is why NO rewriting of an absence-keyed rule can separate them: the rule has to
# CONTRIBUTE.
#
# THE DISCRIMINATION CONTROL IS NOT OPTIONAL. Without (d) and (b) this row cannot tell the fix from
# "contribute `unresolved` unconditionally" — the naive form, measured at 435 functions on a corpus whose
# legitimate count is 0. (d) carries a DIRECT `Unknown` it DID name, with two classes, neither of them
# `unresolved`; (e) inherits from (d). Both must stay OUT of the filter. Requirement (3): the
# contribution is gated on the function having a direct `Unknown` IT DID NOT NAME, never on emptiness.
#
# TWO SURFACES, ONE RULE. `unverified --class` is the four-way disclosure surface; `gate --report
# --policy 'deny Unknown[unresolved]'` is the four-way gate surface (two-way until 2026-07-27). §6.2: "THE GATE AND THE DISCLOSURE
# MUST APPLY THE SAME RULE". Where both exist the row asserts each against the clause AND against each
# other, so an engine that fixes one copy and not its open-coded twin is caught by the pair.

R1_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 7, "digest": "0"},
    "functions": [
        # (a) inherits Unknown from a dep that named no reason at all.
        {"fn": "app.a_reasonless_only", "inferred": ["Unknown"], "calls": ["app.src_reasonless"]},
        # (b) inherits from a dep whose Unknown IS classified. Class set {dispatch}.
        {"fn": "app.b_reasoned_only", "inferred": ["Unknown"], "calls": ["app.src_reasoned"]},
        # (c) BOTH. Strictly worse-known than (a); under the absence reading it was GREEN.
        {"fn": "app.c_both", "inferred": ["Unknown"],
         "calls": ["app.src_reasonless", "app.src_reasoned"]},
        # (d) the discrimination control: a DIRECT Unknown it DID name, two classes, no `unresolved`.
        {"fn": "app.d_named_direct", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["reflect:Method.invoke", "native:strlen"]},
        # (e) the same control one hop away: inherited, fully classified at the callee.
        {"fn": "app.e_named_inherited", "inferred": ["Unknown"], "calls": ["app.d_named_direct"]},
        # the two sources.
        {"fn": "app.src_reasonless", "inferred": ["Unknown"], "direct": ["Unknown"], "unknownWhy": []},
        {"fn": "app.src_reasoned", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run"]},
    ],
}
R1_CG = {e["fn"]: e.get("calls", []) for e in R1_REPORT["functions"]}
# The §6.2 answer, read off the clause. `unresolved` selects exactly the three functions whose Unknown
# reaches a hole nobody named; `dispatch` selects the three that reach the one that WAS named.
R1_EXPECT = {
    "unresolved": ["app.a_reasonless_only", "app.c_both", "app.src_reasonless"],
    "dispatch": ["app.b_reasoned_only", "app.c_both", "app.src_reasoned"],
    "reflect": ["app.d_named_direct", "app.e_named_inherited"],
}


def row_r1(ws, pol_pure, pol_unres, pol_fire, pol_quiet):
    cells = []
    for eng in ENGINES:
        if not present(eng):
            cells.append((eng, "disclosure", ABSENT, "", ""))
            cells.append((eng, "gate", ABSENT, "", ""))
            continue
        loc = write_report(ws, eng, R1_REPORT, callgraph=R1_CG)
        base, rc, err = q_unverified(eng, loc, pol_pure)
        if base is None:
            cells.append((eng, "disclosure", ERROR, f"rc={rc} {err}", "a parseable --json document"))
            cells.append((eng, "gate", ERROR, "skipped: the disclosure arm never ran", ""))
            continue
        allfn = sorted(x["fn"] for x in base.get("unverified", []))
        if len(allfn) != len(R1_REPORT["functions"]):
            # the precondition: `pure app` must leave every Unknown-bearing entry UNVERIFIED. If it does
            # not, every filtered count below is being compared against the wrong denominator.
            cells.append((eng, "disclosure", VACUOUS,
                          f"unfiltered selected {len(allfn)}/{len(R1_REPORT['functions'])}", "all 7"))
            cells.append((eng, "gate", VACUOUS, "precondition collapsed", ""))
            continue
        bad = []
        for klass, want in R1_EXPECT.items():
            got, _, e2 = q_unverified(eng, loc, pol_pure, klass)
            if got is None:
                bad.append(f"--class {klass}: no parseable output ({e2})")
                continue
            g = sorted(x["fn"] for x in got.get("unverified", []))
            if g != want:
                bad.append(f"--class {klass}: {g} != {want}")
        cells.append((eng, "disclosure", OK if not bad else FAIL, "; ".join(bad) or "a,c,src_reasonless",
                      "the §6.2 CONTRIBUTES partition"))

        # the gate half — §6.2's "THE GATE AND THE DISCLOSURE MUST APPLY THE SAME RULE".
        #
        # ⟨0.24⟩ THIS CELL USED TO BE VACUOUS TWO WAYS, and a review found both. It accepted
        # `rc_g in (1, 2)`, and **2 is also the generic usage-error code** — so an engine whose gate
        # verb was absent, or simply mis-invoked by this harness, scored OK. The `None -> NOSURF` path
        # that was supposed to catch that died the moment rust and ts branches were added to `q_gate`:
        # every engine now has a branch, so `None` is unreachable and only an unknown NAME returns it.
        # A cell that cannot distinguish "the rule holds" from "nothing ran" is not a test.
        #
        # Both halves are closed here, and the first closes on a SPEC correction rather than on
        # harness cleverness. §3.1 ⟨0.24⟩ now settles what exit 2 means on this input: the entries
        # carrying a reasonless direct `Unknown` CONTRIBUTE `unresolved`, so the rule FIRES from the
        # entry alone and the answer is certain — **exit 1 is the only correct code, and refusing is
        # "a worse answer than the correct one"**. Requiring exactly 1 is therefore both the stricter
        # reading of the clause AND, incidentally, immune to the usage-error code.
        #
        # The DISCRIMINATION CONTROLS close the second half, and they are the part that generalises:
        # a broken invocation returns ONE code, so demanding the gate return TWO DIFFERENT codes on
        # two inputs proves the verb ran and decided. `deny Unknown[reflect]` must FIRE (app.d names
        # `reflect` directly — no transitive step, no unanswerability); `deny Fs` must PASS (this
        # report carries no `Fs` anywhere). If either control misses, the cell is ERROR — a harness
        # or engine fault — and it MUST NOT be reported as either a pass or a defect of the rule.
        rc_fire = q_gate(eng, loc, pol_fire)
        rc_quiet = q_gate(eng, loc, pol_quiet)
        rc_g = q_gate(eng, loc, pol_unres)
        if rc_g is None or rc_fire is None or rc_quiet is None:
            cells.append((eng, "gate", NOSURF, "no `gate --report` verb on this engine", ""))
        elif rc_fire != 1 or rc_quiet != 0:
            cells.append((eng, "gate", ERROR,
                          f"CONTROLS did not discriminate: deny Unknown[reflect] -> {rc_fire} "
                          f"(want 1), deny Fs -> {rc_quiet} (want 0) — the verb did not run or did "
                          f"not decide, so the subject probe says nothing",
                          "controls 1 and 0"))
        else:
            cells.append((eng, "gate", OK if rc_g == 1 else FAIL,
                          f"deny Unknown[unresolved] -> exit {rc_g}"
                          + ("" if rc_g != 2 else "  (refusal — but §3.1 ⟨0.24⟩ says this entry "
                             "CONTRIBUTES `unresolved`, so the rule fires and the answer is certain)"),
                          "exit 1 — it fires"))
    return cells


# =====================================================================================================
# R2 — §3.1 the `viaDispatchOn` EXACT LITERAL
# =====================================================================================================
#
# `frontier_differential.py` only ever asked `"op" in p["viaDispatchOn"]`. A substring check cannot see
# an ORDERING or a DEDUP divergence, which is precisely what the ⟨0.24⟩ MIXED-SOURCE clause pins: the
# field is the SORTED, DEDUPLICATED, comma-joined union of the dispatched members (for each dotted
# reason that passed condition (3)) and the raw details (for each dot-free one).
#
# THE FEED ORDER IS NEITHER SORTED NOR KIND-GROUPED, deliberately. `write` sorts AFTER the dot-free
# phrase, so the expected string INTERLEAVES the two kinds:
#     run , untyped cross-package receiver , write
# An encounter-order join gives `untyped cross-package receiver,write,run`; a dotted-first join gives
# `run,write,untyped cross-package receiver`. Both are wrong and both are caught. A fixture fed in sorted
# order, or with the dot-free entry last, would pin neither.
#
# The DEDUP cell is the second half: two reasons on two different owners resolving to the same member,
# through a reacher that is a subtype of BOTH, must join to one token.

R2_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 5, "digest": "0"},
    "functions": [
        {"fn": "app.Sink.touch", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/tmp/x"]},
        {"fn": "app.Impl.run", "inferred": ["Fs"], "calls": ["app.Sink.touch"]},
        {"fn": "app.Zed.write", "inferred": ["Fs"], "calls": ["app.Sink.touch"]},
        {"fn": "app.Mixed.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:untyped cross-package receiver",   # dot-free, sorts SECOND
                        "dispatch:app.Base.write",                   # member `write`, sorts THIRD
                        "dispatch:app.Base.run"]},                   # member `run`,   sorts FIRST
        {"fn": "app.Dedup.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run", "dispatch:app.Other.run"]},
    ],
}
R2_CG = {e["fn"]: e.get("calls", []) for e in R2_REPORT["functions"]}
R2_HIER = {"app.Impl": ["app.Base", "app.Other"], "app.Zed": ["app.Base"]}
R2_EXPECT = {"app.Mixed.go": "run,untyped cross-package receiver,write", "app.Dedup.go": "run"}
FRONTIER_ENGINES = ["rust", "java", "ts"]   # swift ships no `callers` verb, by design


def _frontier(eng, loc, target="app.Sink.touch"):
    res, err = q_callers(eng, loc, target)
    if res is None:
        return None, err
    return {p["fn"]: p["viaDispatchOn"] for p in res.get("possibleViaUnknownDispatch", [])}, err


def row_r2(ws):
    cells = []
    for eng in ENGINES:
        if eng not in FRONTIER_ENGINES:
            cells.append((eng, "literal", NOSURF,
                          "candor-swift ships no `callers` verb — it PRODUCES the §2.2 sidecar", ""))
            continue
        if not present(eng):
            cells.append((eng, "literal", ABSENT, "", ""))
            continue
        loc = write_report(ws, eng, R2_REPORT, callgraph=R2_CG, hierarchy=R2_HIER)
        got, err = _frontier(eng, loc)
        if got is None:
            cells.append((eng, "literal", ERROR, err, "a parseable callers --json document"))
        elif not got:
            cells.append((eng, "literal", VACUOUS, "the frontier came back empty",
                          "two frontier entries"))
        elif got != R2_EXPECT:
            cells.append((eng, "literal", FAIL, json.dumps(got, sort_keys=True),
                          json.dumps(R2_EXPECT, sort_keys=True)))
        else:
            cells.append((eng, "literal", OK, json.dumps(got, sort_keys=True), ""))
    return cells


# =====================================================================================================
# R3 — §3.1 the DOT-FREE frontier arm
# =====================================================================================================
#
# A `dispatch:` detail with no dot names no owner, so condition (3) — "is some confirmed reacher an
# override of OWNER.M?" — is UNANSWERABLE, and an unanswerable condition MUST NOT be scored as a failed
# one. The entry is DISCLOSED with `viaDispatchOn` = the raw detail verbatim, in BOTH arms.
#
# THREE SHAPES, because the clause's whole point is that a wording-based check is an allowlist and the
# real defect is STRUCTURAL. Each had a different pre-fix outcome on the reference engine:
#   phrase     `untyped cross-package receiver`   dropped in BOTH arms — the plain silent drop.
#   eq_qual    equals a reacher's WHOLE qual      disclosed, but in the hierarchy arm the subtype test
#                                                 passed only BY REFLEXIVITY over a string that is not a
#                                                 type name. Right answer, wrong reason — the shape that
#                                                 hides a gap instead of showing one, so it is pinned.
#   eq_simple  equals a dotted reacher's SIMPLE
#              METHOD name                        matched in the no-hierarchy arm, DROPPED in the
#                                                 hierarchy arm: ARM-DEPENDENCE, decided by nothing but
#                                                 whether a sidecar happens to exist.
# For `eq_simple` the row pins ARM-EQUALITY rather than a fixed answer — the defect is the DIFFERENCE
# between the arms, and asserting a literal there would pin a second thing and mask the first.

R3_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 8, "digest": "0"},
    "functions": [
        {"fn": "app.Sink.touch", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/tmp/x"]},
        {"fn": "app.Impl.run", "inferred": ["Fs"], "calls": ["app.Sink.touch"]},   # dotted reacher
        {"fn": "bare_reacher", "inferred": ["Fs"], "calls": ["app.Sink.touch"]},   # DOT-FREE qual
        {"fn": "app.Phrase.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:untyped cross-package receiver"]},
        {"fn": "app.EqQual.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:bare_reacher"]},
        {"fn": "app.EqSimple.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:run"]},
        # the two DOTTED sources, which is what makes R4's arms differ at all.
        {"fn": "app.Dotted.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run"]},
        {"fn": "app.Unrel.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Unrelated.run"]},
    ],
}
R3_CG = {e["fn"]: e.get("calls", []) for e in R3_REPORT["functions"]}
R3_HIER = {"app.Impl": ["app.Base"]}
DOTFREE_VERBATIM = {"app.Phrase.go": "untyped cross-package receiver",
                    "app.EqQual.go": "bare_reacher"}
ARM_EQ_ONLY = "app.EqSimple.go"


def _r3_arms(ws, eng):
    """(hierarchy arm, no-hierarchy arm) frontiers over one report."""
    loc = write_report(ws, eng, R3_REPORT, callgraph=R3_CG, hierarchy=R3_HIER)
    hier, e1 = _frontier(eng, loc)
    loc = write_report(ws, eng, R3_REPORT, callgraph=R3_CG)          # sidecar ABSENT
    nohier, e2 = _frontier(eng, loc)
    return hier, nohier, (e1 or e2)


def row_r3(ws):
    cells = []
    for eng in ENGINES:
        if eng not in FRONTIER_ENGINES:
            cells.append((eng, "dot-free", NOSURF,
                          "candor-swift ships no `callers` verb — it PRODUCES the §2.2 sidecar", ""))
            continue
        if not present(eng):
            cells.append((eng, "dot-free", ABSENT, "", ""))
            continue
        hier, nohier, err = _r3_arms(ws, eng)
        if hier is None or nohier is None:
            cells.append((eng, "dot-free", ERROR, err, "two parseable frontier documents"))
            continue
        if not hier and not nohier:
            cells.append((eng, "dot-free", VACUOUS, "both arms empty", "three dot-free entries"))
            continue
        bad = []
        for fn, want in DOTFREE_VERBATIM.items():
            for arm, got in (("hier", hier), ("nohier", nohier)):
                if got.get(fn) != want:
                    bad.append(f"{arm}:{fn}={got.get(fn)!r} want {want!r}")
        # eq_simple: ARM-EQUALITY, and present at all. No literal is asserted.
        if ARM_EQ_ONLY not in hier or ARM_EQ_ONLY not in nohier:
            bad.append(f"{ARM_EQ_ONLY} disclosed in hier={ARM_EQ_ONLY in hier} "
                       f"nohier={ARM_EQ_ONLY in nohier} — must be in BOTH")
        elif hier[ARM_EQ_ONLY] != nohier[ARM_EQ_ONLY]:
            bad.append(f"{ARM_EQ_ONLY} arm-dependent: {hier[ARM_EQ_ONLY]!r} vs {nohier[ARM_EQ_ONLY]!r}")
        cells.append((eng, "dot-free", OK if not bad else FAIL,
                      "; ".join(bad) or "phrase + eq_qual verbatim in both arms, eq_simple arm-equal",
                      "disclosed verbatim, identically in both arms"))
    return cells


# =====================================================================================================
# R4 — §3.1 the SIDECAR TRIPLE: absent ≡ `{}` ≢ populated
# =====================================================================================================
#
# An EMPTY §2.2 hierarchy sidecar and an ABSENT one are the SAME INPUT, and both take the over-listing
# fallback. Reading `{}` as the positive claim "no type has a supertype" scores condition (3) as FAILED
# across every dotted dispatch source at once — and a consumer reads an empty frontier as "no function
# may reach the target through an unresolved dispatch". Measured on the reference engine pre-fix: `{}`
# collapsed the frontier to `[]` ENTIRELY, taking the dotted entries with it.
#
# The row is a TRIPLE and every leg carries weight:
#   absent == empty      the equivalence the clause states;
#   empty non-empty      the collapse it was written from — an equivalence alone would be satisfied by
#                        two arms that are both `[]`;
#   populated != absent  the CONTROL. Without it, "always over-list" passes the first two legs, and the
#                        sidecar would be provably ignored. `app.Unrel.go` dispatches on
#                        `app.Unrelated.run`, which no reacher's type sits under: it must be OUT of the
#                        populated arm and IN of the other two.
# `unparseable` rides along as a fourth arm, since the clause names absent, empty and unparseable as one
# input; it must equal `absent` exactly.

R4_ARMS = ["absent", "empty", "unparseable", "populated"]


def row_r4(ws):
    cells = []
    for eng in ENGINES:
        if eng not in FRONTIER_ENGINES:
            cells.append((eng, "sidecar-triple", NOSURF,
                          "candor-swift ships no `callers` verb — it PRODUCES the §2.2 sidecar", ""))
            continue
        if not present(eng):
            cells.append((eng, "sidecar-triple", ABSENT, "", ""))
            continue
        got, err = {}, ""
        for arm in R4_ARMS:
            kw = {"absent": {}, "empty": {"hierarchy": {}},
                  "unparseable": {"hierarchy_raw": "{ this is not json"},
                  "populated": {"hierarchy": R3_HIER}}[arm]
            loc = write_report(ws, eng, R3_REPORT, callgraph=R3_CG, **kw)
            got[arm], e = _frontier(eng, loc)
            err = err or e
        if any(v is None for v in got.values()):
            cells.append((eng, "sidecar-triple", ERROR, err, "four parseable frontier documents"))
            continue
        if not got["absent"]:
            cells.append((eng, "sidecar-triple", VACUOUS, "the reference (absent) arm is empty",
                          "a non-empty fallback frontier"))
            continue
        bad = []
        if got["empty"] != got["absent"]:
            bad.append(f"empty != absent: {sorted(got['empty'])} vs {sorted(got['absent'])}")
        if not got["empty"]:
            bad.append("the `{}` arm collapsed the frontier to [] — the measured pre-fix defect")
        # The unanswerable arms must OVER-LIST BY SIMPLE NAME, not merely agree with each other. Two
        # arms that agree on a SMALLER set satisfy the equivalence and still drop what the fallback is
        # specified to keep — and an engine whose absent-sidecar path already normalises to `{}` would
        # degrade both arms together, so the equivalence alone cannot see it. `app.Unrel.go` dispatches
        # on `app.Unrelated.run`: unanswerable without a hierarchy, so it is IN; answerable and FAILED
        # with one, so it is OUT.
        for arm in ("absent", "empty", "unparseable"):
            if "app.Unrel.go" not in got[arm]:
                bad.append(f"{arm} arm DROPPED app.Unrel.go — with no usable hierarchy the subtype test "
                           f"is unanswerable and the specified behaviour is to over-list by simple name")
        if got["unparseable"] != got["absent"]:
            bad.append(f"unparseable != absent: {sorted(got['unparseable'])} vs {sorted(got['absent'])}")
        if got["populated"] == got["absent"]:
            bad.append("populated == absent: the sidecar is not being consulted at all "
                       "(app.Unrel.go must be dropped only when the hierarchy can answer)")
        if "app.Unrel.go" in got["populated"]:
            bad.append("app.Unrel.go survived the POPULATED arm — no reacher's type sits under "
                       "app.Unrelated, so condition (3) is answerable and FAILED")
        cells.append((eng, "sidecar-triple", OK if not bad else FAIL,
                      "; ".join(bad) or f"absent==empty==unparseable ({len(got['absent'])} entries) "
                                        f"!= populated ({len(got['populated'])})",
                      "absent ≡ {} ≡ unparseable ≢ populated"))
    return cells


# =====================================================================================================
# R5 — §6.2 `--class`: `dynamic` excludes nothing, the narrower filters DISCRIMINATE, and the
#      flag's VALUE GRAMMAR refuses what it cannot honour
# =====================================================================================================
#
# STATED CORRECTLY, because the obvious phrasing is FALSE and the clause says so in its own margin.
# `dynamic` aliases every GENUINE class, which by definition EXCLUDES `setup` — and `setup` entries are
# reachable (`missing-config`, `no-tsconfig`). So the invariant is
#       filtered  ==  unfiltered MINUS the entries whose ONLY class is `setup`
# and it is run BOTH ways: on a setup-free report (exact equality, the clean form) and on a report
# carrying a setup-only entry (the subtraction). "dynamic must exclude nothing", flatly, fails
# spuriously on any corpus carrying a `setup` reason and would pressure an implementer into folding
# `setup` INTO `dynamic`, contradicting its definition.
#
# THE DISCRIMINATION CONTROL IS THE OTHER HALF and is the one a blanket "keep everything" fails: after
# repair, `--class unresolved` selects a small SUBSET (measured: 6 of 387 on one engine, 0 for
# `native`), so a row that only checked convergence would pass a filter that had stopped filtering.
# Here `unresolved` must be a PROPER non-empty subset and `indirect` must be EMPTY — no entry in the
# fixture carries a `callback:`.

R5_SETUP_REPORT = json.loads(json.dumps(R1_REPORT))
R5_SETUP_REPORT["functions"] = R5_SETUP_REPORT["functions"] + [
    {"fn": "app.f_setup_only", "inferred": ["Unknown"], "direct": ["Unknown"],
     "unknownWhy": ["missing-config"]},
]
R5_SETUP_REPORT["analyzed"]["count"] = len(R5_SETUP_REPORT["functions"])
R5_SETUP_CG = {e["fn"]: e.get("calls", []) for e in R5_SETUP_REPORT["functions"]}


def row_r5(ws, pol_pure):
    cells = []
    for eng in ENGINES:
        if not present(eng):
            cells.append((eng, "dynamic", ABSENT, "", ""))
            cells.append((eng, "discriminates", ABSENT, "", ""))
            continue

        # -- leg 1: the SETUP-FREE fixture. `dynamic` must equal unfiltered, exactly. --------------
        loc = write_report(ws, eng, R1_REPORT, callgraph=R1_CG)
        base, _, e1 = q_unverified(eng, loc, pol_pure)
        dyn, _, e2 = q_unverified(eng, loc, pol_pure, "dynamic")
        if base is None or dyn is None:
            cells.append((eng, "dynamic", ERROR, e1 or e2, "two parseable --json documents"))
            cells.append((eng, "discriminates", ERROR, "skipped: leg 1 never ran", ""))
            continue
        b = sorted(x["fn"] for x in base.get("unverified", []))
        d = sorted(x["fn"] for x in dyn.get("unverified", []))
        if not b:
            cells.append((eng, "dynamic", VACUOUS, "unfiltered selected nothing", "7 entries"))
            cells.append((eng, "discriminates", VACUOUS, "precondition collapsed", ""))
            continue
        bad = [] if d == b else [f"setup-free: dynamic {len(d)} != unfiltered {len(b)} "
                                 f"(missing {sorted(set(b) - set(d))})"]

        # -- leg 2: the SETUP-BEARING fixture. dynamic == unfiltered MINUS setup-only. --------------
        loc2 = write_report(ws, eng, R5_SETUP_REPORT, callgraph=R5_SETUP_CG)
        base2, _, _ = q_unverified(eng, loc2, pol_pure)
        dyn2, _, _ = q_unverified(eng, loc2, pol_pure, "dynamic")
        if base2 is None or dyn2 is None:
            bad.append("setup arm: no parseable output")
        else:
            b2 = set(x["fn"] for x in base2.get("unverified", []))
            d2 = set(x["fn"] for x in dyn2.get("unverified", []))
            if "app.f_setup_only" not in b2:
                bad.append("setup arm VACUOUS: the setup-only entry was not unverified to begin with")
            elif d2 != b2 - {"app.f_setup_only"}:
                bad.append(f"setup arm: dynamic {sorted(d2)} != unfiltered-minus-setup-only "
                           f"{sorted(b2 - {'app.f_setup_only'})}")
        cells.append((eng, "dynamic", OK if not bad else FAIL,
                      "; ".join(bad) or f"{len(d)}=={len(b)} setup-free, and −1 with a setup-only entry",
                      "filtered == unfiltered − setup-only"))

        # -- the discrimination control -------------------------------------------------------------
        unres, _, _ = q_unverified(eng, loc, pol_pure, "unresolved")
        indir, _, _ = q_unverified(eng, loc, pol_pure, "indirect")
        if unres is None or indir is None:
            cells.append((eng, "discriminates", ERROR, "no parseable output", ""))
            continue
        u = sorted(x["fn"] for x in unres.get("unverified", []))
        i = sorted(x["fn"] for x in indir.get("unverified", []))
        bad2 = []
        if not u:
            bad2.append("--class unresolved selected NOTHING — the filter fails open the other way")
        if set(u) >= set(b):
            bad2.append(f"--class unresolved selected all {len(u)} — a filter that kept everything "
                        f"would pass a convergence-only row")
        if i:
            bad2.append(f"--class indirect selected {i} — no fixture entry carries a `callback:`")
        cells.append((eng, "discriminates", OK if not bad2 else FAIL,
                      "; ".join(bad2) or f"unresolved {len(u)}/{len(b)}, indirect 0", "a proper subset"))

        # -- THE FLAG'S VALUE GRAMMAR ---------------------------------------------------------------
        # ⟨0.24⟩ "`--class <c>[,<c>…]` takes ONE comma-separated list; it is not repeatable (a second
        # occurrence is a usage error, not a union) … An UNRECOGNISED token is a usage error: exit 2,
        # naming the token and listing the accepted set. It is NOT the policy-side drop-with-warning
        # behaviour, and the difference is the point: on the policy side a dropped token leaves a WIDER
        # rule standing, whereas here it leaves a NARROWER filter — so `--class dyanmic` would silently
        # answer a question the user did not ask, with a smaller number." The clause names this as where
        # the next divergence would have gone; it is measured here rather than assumed.
        _, rc_bad, _ = q_unverified(eng, loc, pol_pure, "dyanmic")
        r_rep = run(_unverified_cmd(eng, loc, pol_pure) + ["--class", "unresolved", "--class", "native"])
        bad3 = []
        if rc_bad != 2:
            bad3.append(f"`--class dyanmic` (a typo) exited {rc_bad}, not 2 — a filter that cannot be "
                        f"honoured answers a narrower question than the one asked")
        if r_rep.returncode != 2:
            bad3.append(f"a repeated `--class` exited {r_rep.returncode}, not 2 — the flag takes ONE "
                        f"comma-separated list and a second occurrence is a usage error, not a union")
        cells.append((eng, "value-grammar", OK if not bad3 else FAIL,
                      "; ".join(bad3) or "bad token and a repeated flag both exit 2",
                      "exit 2 on an unrecognised token and on a repeated flag"))
    return cells


# =====================================================================================================
# R6 — §3.1 `gate --report`: byte-equality, the MUST NOT, and the three refusals
# =====================================================================================================
#
# TWO ENGINES TODAY. `gate --report <locator> --policy <file>` is implemented in candor-java and
# candor-swift; rust and ts have not landed the verb. Those cells print NOSURF with that reason, because
# a silent skip on a verb the spec makes a MUST is the thing this suite exists to prevent.
#
# THREE CELLS:
#   equivalence  For any report a scan produced, `gate --report it --policy P` MUST produce a
#                `--gate-json` document BYTE-EQUAL to `scan --policy P`'s. Anything less lets the two
#                routes drift into two gates. Run over a policy matrix, and the row is VACUOUS unless at
#                least one policy actually produced a violation — byte-equal empty verdicts prove little.
#   must-not     An engine MUST NOT re-derive, widen or re-classify while serving this verb: an ABSENT
#                entry is the ⟨0.21⟩ purity claim and MUST NOT be back-filled. The fixture supplies the
#                missing effect through ALL THREE channels at once — a `.callgraph.json` sidecar naming
#                the absent function and its effectful callee, a chained dep report on CANDOR_DEPS, and
#                a `.candor/config` `deps` key — and `deny Fs` must still exit 0. A NEGATIVE CONTROL
#                runs beside it with the same effect written INTO the report, which must exit 1; without
#                it, an engine that ignores the policy entirely would pass.
#   refusals     A rule whose evidence the wire does not carry MUST be refused (exit 2), never
#                evaluated. `forbid` (whole-policy: `calls` is effect-relevant, so a crossing into a
#                pure unit is invisible), `allow` (whole-policy: the AS-EFF-008 completeness marker does
#                not ride the wire) and a CLASS-SCOPED `deny` whose scoping datum is an absent optional
#                field (per-(rule, function): `deny Net[unknown-host]` over a `Net` entry with no
#                `netClass` matched the empty set and returned exit 0, where bare `deny Net` returns 1 —
#                an absent optional field silently un-scoping a fail-closed security gate). The bare
#                rule rides along as the control that proves the fixture can fire at all.

# ⟨0.24⟩ ALL FOUR now implement `gate --report`. This list was ["java","swift"] while rust and ts had not
# landed it, and the row printed NOSURF for them — which is honest but does not FAIL, so the suite stayed
# green while a clause §3.1 calls a MUST was pinned 2-of-4. That gap is closed (rust `93ed0a1`, ts `c2b8ce4`).
GATE_ENGINES = ["rust", "java", "ts", "swift"]

R6_ABSENT_REPORT = {          # `app.hidden` is NOT here. Absent is absent.
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 3, "digest": "0"},
    "functions": [{"fn": "app.visible", "inferred": ["Net"], "direct": ["Net"], "hosts": ["example.com"],
                   "netClass": ["unknown-host"]}],
}
R6_ABSENT_CG = {"app.visible": [], "app.hidden": ["dep.readCfg"], "dep.readCfg": []}
R6_PRESENT_REPORT = json.loads(json.dumps(R6_ABSENT_REPORT))     # the negative control
R6_PRESENT_REPORT["functions"].append(
    {"fn": "app.hidden", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/etc/hosts"]})

R6_SCOPED_REPORT = {          # a Net-bearing entry with NO `netClass`: the absent optional field
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 1, "digest": "0"},
    "functions": [{"fn": "app.egress", "inferred": ["Net"], "direct": ["Net"], "hosts": ["example.com"]}],
}


def _java_scan(ws, policy, gate_json):
    src = os.path.join(ws, "gsrc", "app")
    os.makedirs(src, exist_ok=True)
    with open(os.path.join(src, "Cases.java"), "w") as fh:
        fh.write("package app;\nimport java.io.*;\npublic class Cases {\n"
                 "  public static void reader() throws Exception { new FileInputStream(\"/etc/hosts\").close(); }\n"
                 "  public static void caller() throws Exception { reader(); }\n"
                 "  public static void pureFn() { int x = 1; }\n}\n")
    cls = os.path.join(ws, "gout")
    if run(["javac", "-d", cls, os.path.join(src, "Cases.java")]).returncode:
        return None, None
    rep = os.path.join(ws, "grep.json")
    rc = run(["java", "-jar", java_jar(), cls, "--json", rep, "--policy", policy,
              "--gate-json", gate_json]).returncode
    return (rep, rc) if os.path.exists(rep) else (None, None)


def _swift_scan(ws, policy, gate_json):
    d = os.path.join(ws, "gsw")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "cases.swift")
    with open(src, "w") as fh:
        fh.write("import Foundation\n"
                 "func reader() { _ = FileManager.default.contents(atPath: \"/etc/hosts\") }\n"
                 "func caller() { reader() }\n"
                 "func pureFn() { let _ = 1 }\n")
    pfx = os.path.join(d, "out")
    for f in os.listdir(d):
        if f.startswith("out."):
            os.remove(os.path.join(d, f))
    rc = run([swift_bin(), src, "--out", pfx, "--policy", policy, "--gate-json", gate_json]).returncode
    return (pfx, rc) if any(f.startswith("out.") and f.endswith(".Swift.json")
                            for f in os.listdir(d)) else (None, None)


def _rust_scan(ws, policy, gate_json):
    d = os.path.join(ws, "grs")
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    with open(os.path.join(d, "Cargo.toml"), "w") as fh:
        fh.write("[package]\nname = \"gcases\"\nversion = \"0.0.0\"\nedition = \"2021\"\n")
    with open(os.path.join(d, "src", "lib.rs"), "w") as fh:
        fh.write("pub fn reader() { let _ = std::fs::read(\"/etc/hosts\"); }\n"
                 "pub fn caller() { reader(); }\n"
                 "pub fn pure_fn() { let _x = 1; }\n")
    pfx = os.path.join(d, "out", "r")
    os.makedirs(os.path.join(d, "out"), exist_ok=True)
    for f in os.listdir(os.path.join(d, "out")):
        os.remove(os.path.join(d, "out", f))          # never read a stale report back as this arm's result
    rc = run([rust_scan(), d, "--out", pfx, "--policy", policy, "--gate-json", gate_json]).returncode
    return (pfx, rc) if any(f.startswith("r.") for f in os.listdir(os.path.join(d, "out"))) else (None, None)


def _ts_scan(ws, policy, gate_json):
    d = os.path.join(ws, "gts")
    os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "cases.ts")
    with open(src, "w") as fh:
        fh.write("import * as fs from 'fs';\n"
                 "export function reader() { fs.readFileSync('/etc/hosts'); }\n"
                 "export function caller() { reader(); }\n"
                 "export function pureFn() { const x = 1; return x; }\n")
    pfx = os.path.join(d, "out")
    for f in os.listdir(d):
        if f.startswith("out."):
            os.remove(os.path.join(d, f))
    rc = run(["node", os.path.join(ts_root(), "scan.mjs"), d, "--out", pfx,
              "--policy", policy, "--gate-json", gate_json]).returncode
    return (pfx, rc) if any(f.startswith("out.") for f in os.listdir(d)) else (None, None)


def row_r6(ws, pols):
    cells = []
    for eng in ENGINES:
        if eng not in GATE_ENGINES:
            for c in ("equivalence", "must-not", "refusals"):
                cells.append((eng, c, NOSURF,
                              "`gate --report` is not implemented on this engine yet "
                              "(§3.1 ⟨0.24⟩ makes it a MUST; java + swift have it)", ""))
            continue
        if not present(eng):
            for c in ("equivalence", "must-not", "refusals"):
                cells.append((eng, c, ABSENT, "", ""))
            continue

        # -- equivalence ------------------------------------------------------------------------------
        bad, fired = [], 0
        for name in ("deny_fs", "deny_net", "pure"):
            pol = pols[name]
            a = os.path.join(ws, f"{eng}.scan.gate.json")
            b = os.path.join(ws, f"{eng}.gate.gate.json")
            for p in (a, b):
                if os.path.exists(p):
                    os.remove(p)            # delete outputs before measuring the control
            _scan = {"rust": _rust_scan, "java": _java_scan, "ts": _ts_scan, "swift": _swift_scan}[eng]
            rep, rc_scan = _scan(ws, pol, a)
            if rep is None:
                bad.append(f"{name}: the scan produced no report (harness)")
                continue
            rc_gate = q_gate(eng, rep, pol, gate_json=b)
            if not (os.path.exists(a) and os.path.exists(b)):
                bad.append(f"{name}: a --gate-json document was not written")
                continue
            if open(a, "rb").read() != open(b, "rb").read():
                bad.append(f"{name}: --gate-json NOT byte-equal (scan exit {rc_scan}, gate exit {rc_gate})")
            if rc_scan != rc_gate:
                bad.append(f"{name}: exit {rc_scan} (scan) vs {rc_gate} (gate)")
            if rc_scan == 1:
                fired += 1
        if not bad and fired == 0:
            cells.append((eng, "equivalence", VACUOUS, "no policy in the matrix produced a violation",
                          "at least one exit-1 row"))
        else:
            cells.append((eng, "equivalence", OK if not bad else FAIL,
                          "; ".join(bad) or f"3 policies byte-equal, {fired} of them with violations",
                          "byte-equal --gate-json + identical exit"))

        # -- the MUST NOT, with all three back-fill channels open, and its negative control ----------
        depdir = os.path.join(ws, "depreports")
        os.makedirs(depdir, exist_ok=True)
        deprep = os.path.join(depdir, "dep.json")
        with open(deprep, "w") as fh:
            json.dump({"candor": {"version": "handwritten", "spec": "0.23"}, "package": "dep",
                       "analyzed": {"count": 1, "digest": "0"},
                       "functions": [{"fn": "dep.readCfg", "inferred": ["Fs"], "direct": ["Fs"],
                                      "paths": ["/etc/hosts"]}]}, fh)
        def open_all_channels(locator):
            """The `.candor/config` `deps` key, beside the report. The other two channels — the
            `.callgraph.json` sidecar and CANDOR_DEPS — are already open."""
            cfgdir = os.path.join(os.path.dirname(locator), ".candor")
            os.makedirs(cfgdir, exist_ok=True)
            with open(os.path.join(cfgdir, "config"), "w") as fh:
                fh.write(f"deps = {deprep}\n")

        loc_absent = write_report(ws, eng, R6_ABSENT_REPORT, callgraph=R6_ABSENT_CG)
        open_all_channels(loc_absent)
        prev = os.environ.get("CANDOR_DEPS")
        os.environ["CANDOR_DEPS"] = deprep
        try:
            rc_absent = q_gate(eng, loc_absent, pols["deny_fs"])
            loc_present = write_report(ws, eng, R6_PRESENT_REPORT, callgraph=R6_ABSENT_CG)
            open_all_channels(loc_present)
            rc_present = q_gate(eng, loc_present, pols["deny_fs"])
        finally:
            if prev is None:
                os.environ.pop("CANDOR_DEPS", None)
            else:
                os.environ["CANDOR_DEPS"] = prev
        bad = []
        if rc_absent != 0:
            bad.append(f"an ABSENT entry was back-filled: `deny Fs` -> exit {rc_absent} over a report "
                       f"carrying no Fs (callgraph sidecar + CANDOR_DEPS + config `deps` all supplied it)")
        if rc_present != 1:
            bad.append(f"NEGATIVE CONTROL: the same policy over a report that DOES carry Fs -> exit "
                       f"{rc_present}, expected 1 — the row cannot distinguish 'not back-filled' from "
                       f"'policy never evaluated'")
        cells.append((eng, "must-not", OK if not bad else FAIL,
                      "; ".join(bad) or "absent stays absent (exit 0); control fires (exit 1)",
                      "exit 0 absent / exit 1 present"))

        # -- the three answerability refusals, plus the bare-rule control ---------------------------
        loc_sc = write_report(ws, eng, R6_SCOPED_REPORT)
        bad = []
        for name, want in (("forbid", 2), ("allow", 2), ("scoped", 2), ("bare_net", 1)):
            rc = q_gate(eng, loc_sc, pols[name])
            if rc != want:
                what = ("the bare rule must FIRE, or the scoped fixture proves nothing"
                        if name == "bare_net" else "must be REFUSED, never evaluated")
                bad.append(f"{name}: exit {rc}, expected {want} — {what}")
        cells.append((eng, "refusals", OK if not bad else FAIL,
                      "; ".join(bad) or "forbid/allow/scoped all exit 2, bare deny Net exits 1",
                      "exit 2 / exit 2 / exit 2 / exit 1"))
    return cells


# =====================================================================================================
# R8 — §3.1 PRECEDENCE: a CERTAIN violation dominates a refusal, and a refusal still writes a document
# =====================================================================================================
#
# ⟨0.24⟩ Two clauses, one fixture, and the row exists because FOUR-WAY AGREEMENT WAS THE WRONG ANSWER.
# Measured on rust, java, ts and swift alike: a policy carrying a firing `deny Fs` PLUS one unanswerable
# scoped rule exits 2 and writes NO `--gate-json` document. The spec first ratified that, then corrected
# it within the hour — `Reject` is upward-closed (PAPER3 Lemma 2), so if a rule already fires on evidence
# the report carries, however the unanswerable rule would have resolved CANNOT UN-REJECT IT. Exit 1 is
# therefore certain, not merely fail-closed, and it names the violation where exit 2 does not.
#
# THE HARM IS IN THE DOCUMENT, NOT THE EXIT CODE, and that is why this row asserts on both. A refusal
# writes no document, so refusing over a firing rule DELETES A CERTAIN VIOLATION from the machine-consumer
# channel — the identical harm to candor-rust's incomplete-analysis path, which this same rung is fixing.
# A row that checked only `exit == 1` would pass on an engine that emitted an empty violation list.
#
# TWO CONTROLS, AND NEITHER IS OPTIONAL:
#   - `deny Net[unknown-host]` ALONE must exit 2. Without it the row cannot distinguish "the violation
#     dominated the refusal" from "the scoped rule was answerable all along and there was never a
#     refusal to dominate" — the fixture would prove nothing and would look identical.
#   - `deny Fs` ALONE must exit 1. Without it a gate that has stopped evaluating anything scores OK.
# A broken invocation returns ONE code; these three probes demand 1, 2 and 1 across different inputs.
#
# THE REFUSAL DOCUMENT is the second cell. On the refuse-only policy a document MUST exist, MUST carry
# `ok: false` (so a consumer keying only on `ok` lands on FAIL), MUST carry `refused: true`, and MUST NOT
# carry a `violations` key at all — the gate is making no claim about violations, and an empty array is
# precisely the claim a refusal cannot make. ABSENT-vs-EMPTY is the whole assertion; `== []` would pass
# on the fail-open shape.

R8_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 2, "digest": "0"},
    "functions": [
        # the FIRING half: unambiguous, evidence in the entry, no transitive step.
        {"fn": "app.writes", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/etc/hosts"]},
        # the UNANSWERABLE half: Net with NO `netClass`, so `deny Net[unknown-host]` cannot be decided.
        {"fn": "app.calls", "inferred": ["Net"], "direct": ["Net"]},
    ],
}


def row_r8(ws, pols):
    cells = []
    for eng in ENGINES:
        if not present(eng):
            cells.append((eng, "precedence", ABSENT, "", ""))
            cells.append((eng, "refusal-doc", ABSENT, "", ""))
            continue
        loc = write_report(ws, eng, R8_REPORT)

        rc_fire = q_gate(eng, loc, pols["r8_fire_only"])
        rc_refuse = q_gate(eng, loc, pols["r8_refuse_only"])
        gj = os.path.join(ws, "r8.%s.mixed.json" % eng)
        if os.path.exists(gj):
            os.remove(gj)    # DELETE BEFORE MEASURING — a stale artifact here reads as a pass.
        rc_mixed = q_gate(eng, loc, pols["r8_mixed"], gate_json=gj)

        if rc_fire is None:
            cells.append((eng, "precedence", NOSURF, "no `gate --report` verb on this engine", ""))
            cells.append((eng, "refusal-doc", NOSURF, "no `gate --report` verb on this engine", ""))
            continue
        if rc_fire != 1 or rc_refuse != 2:
            cells.append((eng, "precedence", ERROR,
                          "CONTROLS did not separate: `deny Fs` alone -> %s (want 1), "
                          "`deny Net[unknown-host]` alone -> %s (want 2). Without both, the mixed probe "
                          "cannot distinguish domination from there having been no refusal to dominate"
                          % (rc_fire, rc_refuse), "controls 1 and 2"))
            cells.append((eng, "refusal-doc", ERROR, "precedence controls failed; document cell moot", ""))
            continue

        bad = []
        if rc_mixed != 1:
            bad.append("firing + unanswerable in one policy -> exit %s, want 1 (Lemma 2: an absent datum "
                       "cannot un-reject a rule that already fires)" % rc_mixed)
        doc = None
        if os.path.exists(gj):
            try:
                doc = json.load(open(gj))
            except Exception as e:
                bad.append("the verdict document did not parse: %s" % e)
        else:
            bad.append("no `--gate-json` document was written at all")
        if doc is not None and not isinstance(doc, dict):
            bad.append("the verdict document is not a JSON OBJECT (%r) — every content assertion below "
                       "would silently skip" % type(doc).__name__)
        if isinstance(doc, dict):
            vs = doc.get("violations")
            if not vs:
                bad.append("the document carries NO violations — the certain `deny Fs` finding was "
                           "deleted from the machine-consumer channel, which IS the harm this row is "
                           "about; the exit code alone would not have shown it")
            elif not any("writes" in json.dumps(v) for v in vs):
                bad.append("the document's violations do not name `app.writes`: %r" % (vs,))
        cells.append((eng, "precedence", OK if not bad else FAIL,
                      "; ".join(bad) or "exit 1 and `app.writes` present in the document",
                      "exit 1 + violation in document"))

        # -- the refusal document ------------------------------------------------------------------
        gj2 = os.path.join(ws, "r8.%s.refusal.json" % eng)
        if os.path.exists(gj2):
            os.remove(gj2)
        rc_doc = q_gate(eng, loc, pols["r8_refuse_only"], gate_json=gj2)
        bad = []
        # ⟨0.24⟩ CHECK THE EXIT CODE OF *THIS* RUN. The `rc_refuse == 2` control above ran WITHOUT
        # `--gate-json`, and a review shimmed an engine that delegates normally but exits 0 whenever
        # `--gate-json` is present: the document was written correctly, both R8 cells scored OK, and the
        # suite exited 0 — while a CI wrapper keying on the exit code saw PASS on EVERY refusal. Measuring
        # a run's document without measuring that run's exit code assumes the flag cannot change the
        # verdict, which is exactly what the mutation falsified.
        if rc_doc != 2:
            bad.append("the run that produced this document exited %s, want 2 — `--gate-json` must not "
                       "change the verdict (the control above ran WITHOUT the flag, so it cannot see "
                       "this)" % rc_doc)
        if not os.path.exists(gj2):
            bad.append("a refusal wrote NO document, so a CI wrapper reading this path re-reads the "
                       "PREVIOUS run's verdict as current")
        else:
            try:
                d2 = json.load(open(gj2))
            except Exception as e:
                d2 = None
                bad.append("the refusal document did not parse: %s" % e)
            if d2 is not None and not isinstance(d2, dict):
                bad.append("the refusal document is not a JSON OBJECT (%r) — every content assertion "
                           "below would silently skip" % type(d2).__name__)
            if isinstance(d2, dict):
                if d2.get("ok") is not False:
                    bad.append("`ok` is %r, want false — a consumer keying only on `ok` must land on FAIL"
                               % d2.get("ok"))
                if d2.get("refused") is not True:
                    bad.append("`refused` is %r, want true" % d2.get("refused"))
                if "violations" in d2:
                    bad.append("the document carries a `violations` key (%r) — a refusal makes NO claim "
                               "about violations, and an empty array is exactly the claim it cannot "
                               "make. ABSENT, not empty." % (d2["violations"],))
        cells.append((eng, "refusal-doc", OK if not bad else FAIL,
                      "; ".join(bad) or "ok:false + refused:true, no `violations` key",
                      "document exists, fail-closed to a naive reader"))
    return cells


# =====================================================================================================
# R9 — CROSS-ENGINE VERDICT KEY PARITY: the four documents must have the SAME SHAPE
# =====================================================================================================
#
# ⟨0.24⟩ THIS ROW EXISTS BECAUSE OF A HOLE THE OTHER ROWS CANNOT SEE, AND THE HOLE WAS FOUND BY A MISS.
# candor-swift emitted the verdict's uncovered-package list as `coverage.modules` where rust, java and ts
# emit `coverage.packages`. Nothing caught it for the life of the field:
#
#   - §3.1's byte-equality MUST is WITHIN-ENGINE — `scan --policy` vs `gate --report` on the SAME engine.
#     swift was perfectly self-consistent, so R6's equivalence cell was green and correct.
#   - the spec never normatively defined the verdict's `coverage` block at all (§2 defines the REPORT's
#     ledger, which is a DIFFERENT SHAPE), so there was no clause to check against. The one mention was
#     descriptive prose that said `modules` — written, almost certainly, with swift's output open.
#   - and no PART compared the KEY SET across engines. Every cell compared an engine to a clause, or to
#     itself.
#
# So a field can be emitted by all four, mentioned in the spec, and covered by a byte-level equivalence
# test, and still be UNSPECIFIED AND DIVERGENT. What was missing is the cheapest comparison available:
# do the four documents have the same shape?
#
# WHAT THIS ROW DOES NOT DO. It does not compare VALUES. `detail` is free text and legitimately differs
# in wording per engine; the counts differ with the fixture. Cross-engine value equality is not a
# property this family claims, and asserting it would produce a row that fails for correct reasons.
# The claim is narrower and it is the one that was broken: THE SAME SITUATION MUST PRODUCE THE SAME KEYS.
#
# THE FIRST ARM'S FIXTURE IS CHOSEN SO EVERY OPTIONAL BLOCK IS UNIFORMLY ABSENT — one plain `Fs` entry, no
# `Unknown` (so no `reasonClass`), no `Net` (so no `netClass`), no `unanalyzed`, nothing uncovered.
# Otherwise the row would flag legitimate per-situation differences as divergence. `deny Fs` then fires on
# all four, which is also the vacuity guard: a document with no violations cannot exercise the record's
# key set.
#
# ⟨0.24⟩ **AND THAT CHOICE MADE THE ROW BLIND TO EXACTLY THE FIELDS MOST LIKELY TO DIVERGE — measured, on
# the very next field after the one this row was built for.** A single uniformly-minimal fixture only ever
# compares the keys that are ALWAYS present. The optional blocks — the ones an engine adds when a
# particular thing happened — are absent in every arm and therefore uniform for free. candor-ts measured
# the ⟨0.24⟩ policy-vocabulary disclosure and found **three engines, three names**:
#
#     rust  "vocabulary":       {config, aliases}
#     java  "policyVocabulary": {config, aliases}
#     swift "configSources":    [path]            ← an ARRAY, and it drops the alias names entirely
#
# `coverage.modules` again, one field later, and arm 1 cannot see it because its policy has no alias so
# the block is uniformly absent. Same for `unevaluated`: java puts it in the DOCUMENT, rust and swift
# disclose only on stderr.
#
# So the row is a LIST OF SITUATIONS, not one fixture, and the rule for adding to it is: **every optional
# block needs an arm that makes it PRESENT.** A parity row that only exercises the mandatory keys is
# checking the half of the document that was never going to drift.

R9_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 1, "digest": "0"},
    "functions": [{"fn": "app.writes", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/etc/hosts"]}],
}


def _shape(doc):
    """The document's SHAPE: every key path, to any depth, plus each value's TYPE.

    ⟨0.24⟩ THIS DESCENDED INTO A HARDCODED `("analyzed", "coverage")` AND WAS THEREFORE BLIND TO THE
    ONE BLOCK THIS ROW EXISTS FOR. A review measured a live divergence one level below the compared
    surface: candor-ts emits `policyVocabulary.aliases` as an OBJECT `{"corp": ["reflect"]}` where
    rust, java and swift emit the ARRAY `["corp"]` — inside the very block whose three-way naming
    history this row's own comment narrates. It scored `key-parity(opt) OK` on all four. A shim
    replacing swift's whole `policyVocabulary` with `{"sources": […], "count": 1}` also passed.

    The author's blind spot and the check's blind spot were the same set, which is this suite's
    recurring defect. So the walk is GENERIC — no key list to forget to extend — and it records the
    TYPE at each leaf, because `["corp"]` and `{"corp": …}` differ in type, not in key path, and a
    key-only comparison is blind to exactly the divergence measured. `effects: null` (key kept, array
    dropped) is caught by the same addition.
    """
    def walk(node, prefix, out):
        if isinstance(node, dict):
            for k, v in node.items():
                out.add(prefix + k + ":" + type(v).__name__)
                walk(v, prefix + k + ".", out)
        elif isinstance(node, list):
            # the ELEMENT type, not each index — a list of 1 and a list of 9 are the same shape.
            for v in node:
                out.add(prefix + "[]:" + type(v).__name__)
                walk(v, prefix + "[].", out)

    top = set()
    for k, v in doc.items():
        if k == "violations":
            top.add("violations:" + type(v).__name__)
            continue                       # records are compared separately, below
        top.add(k + ":" + type(v).__name__)
        walk(v, k + ".", top)
    rec = set()
    for v in (doc.get("violations") or []):
        if isinstance(v, dict):
            for k2, v2 in v.items():
                rec.add(k2 + ":" + type(v2).__name__)
                walk(v2, k2 + ".", rec)
    return top, rec


def _parity(shapes, second="violation-record"):
    """{eng: (topkeys, secondkeys)} -> {eng: [complaint, ...]}. Extracted so it is testable without engines.

    `second` NAMES the second key set, because this is shared between R9 (whose second set is a violation
    record) and R10 (whose second set is a report ENTRY). It was hardcoded to "violation-record", so R10's
    first run reported a report-entry divergence as a "violation-record keys differ" — a message that
    would have sent the next reader to the wrong file. A conformance suite's failure text is part of the
    check: a true finding described wrongly costs the same hour as a false one.

    The majority shape is the reference, and DISAGREEMENT IS REPORTED ON EVERY ENGINE THAT DIFFERS — not
    on "the odd one out". A tie has NO majority and fails on ALL engines, loudly, naming the split: this
    family has twice this week found the outlier to be the CORRECT one (candor-ts on both contested
    `gate --report` questions), so the row reports the disagreement and REFUSES TO NOMINATE A WINNER.
    Adjudicating belongs to the clause, not to a headcount.
    """
    from collections import Counter
    out = {}
    top_counts = Counter(frozenset(t) for t, _ in shapes.values())
    rec_counts = Counter(frozenset(r) for _, r in shapes.values())
    top_ref, top_n = top_counts.most_common(1)[0]
    rec_ref, rec_n = rec_counts.most_common(1)[0]
    tie_top = sum(1 for _, n in top_counts.items() if n == top_n) > 1
    tie_rec = sum(1 for _, n in rec_counts.items() if n == rec_n) > 1
    for eng, (top, rec) in shapes.items():
        bad = []
        if tie_top:
            bad.append("NO MAJORITY on the top-level shape %s — the engines split evenly, so this row "
                       "will not nominate a winner; adjudicate from the clause"
                       % [sorted(x) for x in top_counts])
        elif frozenset(top) != top_ref:
            bad.append("top-level keys differ: extra %s, missing %s (majority of %d: %s)"
                       % (sorted(set(top) - set(top_ref)), sorted(set(top_ref) - set(top)),
                          top_n, sorted(top_ref)))
        if tie_rec:
            bad.append("NO MAJORITY on the %s shape %s" % (second, [sorted(x) for x in rec_counts]))
        elif frozenset(rec) != rec_ref:
            bad.append(second + " keys differ: extra %s, missing %s (majority of %d: %s)"
                       % (sorted(set(rec) - set(rec_ref)), sorted(set(rec_ref) - set(rec)),
                          rec_n, sorted(rec_ref)))
        out[eng] = bad
    return out


# ARM 2's report carries an `Unknown` with a NAMED reason, gated through an ALIAS defined in a
# `.candor/config` beside the policy — so every engine must emit its policy-vocabulary disclosure, and the
# arm compares the shape of a block that arm 1 cannot reach. The alias resolves to the reason the entry
# actually carries, so the rule FIRES: a refusal here would make the arm vacuous.
R9_ALIAS_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 1, "digest": "0"},
    "functions": [{"fn": "app.dyn", "inferred": ["Unknown"], "direct": ["Unknown"],
                   "unknownWhy": ["reflect:Method.invoke"]}],
}


def _r9_alias_policy(ws):
    """A policy in its OWN directory with a `.candor/config` alias beside it — per §3.1 ⟨0.24⟩ the
    vocabulary anchors at the policy file, so this is where an engine must look."""
    d = os.path.join(ws, "r9alias")
    os.makedirs(os.path.join(d, ".candor"), exist_ok=True)
    pol = os.path.join(d, "p.policy")
    with open(pol, "w") as fh:
        fh.write("deny Unknown[corp] app\n")
    with open(os.path.join(d, ".candor", "config"), "w") as fh:
        fh.write("unknown-alias corp = reflect\n")
    return pol


def row_r9(ws, pols):
    cells = []
    shapes = {}
    alias_shapes = {}
    alias_pol = _r9_alias_policy(ws)
    for eng in ENGINES:
        if not present(eng):
            cells.append((eng, "key-parity", ABSENT, "", ""))
            cells.append((eng, "key-parity(opt)", ABSENT, "", ""))
            continue

        # -- ARM 2: the OPTIONAL blocks, which arm 1 is structurally blind to --------------------
        loc2 = write_report(ws, eng, R9_ALIAS_REPORT)
        gj2 = os.path.join(ws, "r9alias.%s.json" % eng)
        if os.path.exists(gj2):
            os.remove(gj2)
        rc2 = q_gate(eng, loc2, alias_pol, gate_json=gj2)
        if rc2 is None:
            cells.append((eng, "key-parity(opt)", NOSURF, "no `gate --report` verb on this engine", ""))
        elif rc2 != 1:
            cells.append((eng, "key-parity(opt)", ERROR,
                          "aliased `deny Unknown[corp]` over a `reflect` entry -> exit %s, want 1. The "
                          "alias must RESOLVE and the rule must FIRE, or the vocabulary block is never "
                          "emitted and this arm is vacuous." % rc2, "exit 1"))
        elif not os.path.exists(gj2):
            cells.append((eng, "key-parity(opt)", ERROR, "no `--gate-json` document written", ""))
        else:
            try:
                alias_shapes[eng] = _shape(json.load(open(gj2)))
            except Exception as e:
                cells.append((eng, "key-parity(opt)", ERROR, "verdict did not parse: %s" % e, ""))

        loc = write_report(ws, eng, R9_REPORT)
        gj = os.path.join(ws, "r9.%s.json" % eng)
        if os.path.exists(gj):
            os.remove(gj)
        rc = q_gate(eng, loc, pols["r9_fs"], gate_json=gj)
        if rc is None:
            cells.append((eng, "key-parity", NOSURF, "no `gate --report` verb on this engine", ""))
            continue
        if rc != 1:
            cells.append((eng, "key-parity", ERROR,
                          "`deny Fs` over a plain Fs entry -> exit %s, want 1. Without a violation the "
                          "record's key set is never exercised and the row would compare empty sets." % rc,
                          "exit 1"))
            continue
        if not os.path.exists(gj):
            cells.append((eng, "key-parity", ERROR, "no `--gate-json` document written", ""))
            continue
        try:
            shapes[eng] = _shape(json.load(open(gj)))
        except Exception as e:
            cells.append((eng, "key-parity", ERROR, "verdict did not parse: %s" % e, ""))

    if len(shapes) < 2:
        for eng in shapes:
            cells.append((eng, "key-parity", VACUOUS,
                          "only one engine produced a comparable verdict — parity needs two",
                          "two or more engines"))
        return cells

    for eng, bad in sorted(_parity(shapes).items()):
        cells.append((eng, "key-parity", OK if not bad else FAIL,
                      "; ".join(bad) or "shape matches the other %d" % (len(shapes) - 1),
                      "the same situation produces the same keys"))
    if len(alias_shapes) >= 2:
        for eng, bad in sorted(_parity(alias_shapes).items()):
            cells.append((eng, "key-parity(opt)", OK if not bad else FAIL,
                          "; ".join(bad) or "optional-block shape matches the other %d"
                          % (len(alias_shapes) - 1),
                          "the vocabulary disclosure has one name"))
    else:
        for eng in alias_shapes:
            cells.append((eng, "key-parity(opt)", VACUOUS,
                          "only one engine produced a comparable aliased verdict", "two or more"))
    return cells


# =====================================================================================================
# R10 — REPORT-ENVELOPE KEY PARITY: the four engines must describe the same code with the same SHAPE
# =====================================================================================================
#
# ⟨0.24⟩ R9 compares the VERDICT document. Nothing compared the REPORT — the artifact that actually
# travels between engines, gets chained as a dependency, and is the whole premise of the supply-chain
# route. A review enumerated what the four engines emit and cross-checked it against what any PART
# asserts; the report envelope came back with a list of live divergences that no cell could see:
#
#   - `declared` / `undeclared` / `overdeclared`: java emits `undeclared: ["Exec","Fs","Net"]` where ts
#     and swift emit `undeclared: []` for the SAME situation — OPPOSITE SEMANTICS for "no declaration" —
#     and rust emits none of the three keys at all.
#   - top-level `packages` (plural, java) vs `package` (singular, the other three).
#   - the AS-EFF-008 `incomplete` marker: rust PUBLISHES it per-fn on the wire; ts models it and
#     deliberately does not; swift CONSUMES it from chained deps but never produces it; java has nothing
#     — while every engine's own allow-refusal message asserts the marker "does not ride the report wire
#     in any form", which is untrue of rust's wire.
#   - omit-vs-explicit-empty: rust omits `unresolved: false`, `direct: []` and empty surfaces where the
#     others emit them, so a consumer writing `e.unresolved === false` behaves differently per engine.
#
# Every one of those is a consumer-visible difference in the format this family exists to standardise,
# and each was invisible because the suite compared ANSWERS (effect sets, verdicts) and never SHAPE.
#
# THIS ROW IS A RATCHET, NOT A CLIFF. The engines diverge today and cannot all be fixed at once, so the
# measured divergences go in the baseline WITH A REASON EACH and the row fails on anything NEW. A waiver
# whose divergence is repaired then reads STALE and fails, which is what makes it a ratchet rather than a
# permanent exemption.
#
# WHY IT COMPARES TYPES AND NOT VALUES: the four engines scan four different languages, so counts, names,
# `loc` strings and hashes legitimately differ. The claim is the narrow one — the same SITUATION produces
# the same KEY PATHS carrying the same TYPES. `undeclared: []` vs `undeclared: ["Fs"]` is a value
# difference this row deliberately does NOT judge; `undeclared` present vs absent, or list vs dict, is
# what it catches. (The semantic inversion above is therefore reported by the review, not by this row —
# a limit worth stating rather than pretending away.)

def _report_shape(rep):
    """Envelope key paths + types, and the UNION of per-function entry key paths."""
    top = set()
    for k, v in rep.items():
        if k == "functions":
            top.add("functions:" + type(v).__name__)
            continue
        top.add(k + ":" + type(v).__name__)
    ent = set()
    for f in (rep.get("functions") or []):
        if isinstance(f, dict):
            for k2, v2 in f.items():
                ent.add(k2 + ":" + type(v2).__name__)
    return top, ent


def row_r10(ws, pols):
    cells = []
    shapes = {}
    for eng in ENGINES:
        if not present(eng):
            cells.append((eng, "report-parity", ABSENT, "", ""))
            continue
        scan = {"rust": _rust_scan, "java": _java_scan, "ts": _ts_scan, "swift": _swift_scan}[eng]
        gj = os.path.join(ws, "r10.%s.gate.json" % eng)
        if os.path.exists(gj):
            os.remove(gj)
        rep, rc = scan(ws, pols["pure"], gj)
        if rep is None:
            cells.append((eng, "report-parity", ERROR,
                          "the scan produced no report (harness/toolchain)", "a report on disk"))
            continue
        try:
            d = json.load(open(rep))
        except Exception as e:
            cells.append((eng, "report-parity", ERROR, "report did not parse: %s" % e, ""))
            continue
        # VACUITY GUARD: an empty report has no entry keys to compare, so the row would pass by
        # describing nothing — the exact failure mode this suite exists to avoid.
        if not (d.get("functions") or []):
            cells.append((eng, "report-parity", VACUOUS,
                          "the scan produced a report with NO functions — nothing to compare",
                          "at least one entry"))
            continue
        shapes[eng] = _report_shape(d)

    if len(shapes) < 2:
        for eng in shapes:
            cells.append((eng, "report-parity", VACUOUS,
                          "only one engine produced a comparable report — parity needs two", "two or more"))
        return cells
    for eng, bad in sorted(_parity(shapes, second="report-entry").items()):
        cells.append((eng, "report-parity", OK if not bad else FAIL,
                      "; ".join(bad) or "envelope + entry shape match the other %d" % (len(shapes) - 1),
                      "the same situation produces the same report shape"))
    return cells


# =====================================================================================================
# R7 — §2 LOCALE-INDEPENDENCE
# =====================================================================================================
#
# Every ordering, in a report AND in a query output, must be locale-INDEPENDENT: sort by Unicode code
# point. A locale-sensitive comparator makes the SAME input produce a DIFFERENT byte sequence on a
# different machine, or on the same machine under a different environment — at which point "a default
# report is byte-identical" is not even a checkable claim and the effects-fingerprint has no ground.
#
# THE LOCALE MUST BE ONE THAT REORDERS ASCII. `et_EE` collates `z` between `s` and `t`; `da_DK` sorts
# `aa` as `å`, after `z`. `tr_TR` DOES NOT WORK and using it is how this row gets written wrong: Turkish
# inserts its extra letters BETWEEN the ASCII ones, so it leaves pure-ASCII order alone and a C-vs-tr_TR
# control comes back "no difference" — a false all-clear about a real defect. That mistake was made
# during this rung's own review.
#
# CALIBRATE THE INSTRUMENT FIRST. If this machine has no Estonian collation data, nothing in the
# environment can move any engine's bytes and the row proves nothing — so it says so (NON-DISCRIMINATING
# GUARD) instead of passing quietly. The probe names the locale explicitly through `strcoll`, so it
# answers "does this box carry the data?" independently of the parent's environment.
#
# THREE CELLS, because the clause covers report bytes AND query output, and the measured defect (seven
# `localeCompare` sites on one engine) spanned both: one ordered the κ-coverage ledger INSIDE the emitted
# report, six ordered query output — including the `callers --include-unknown` frontier's entry order.
#
#   report-bytes    the same tree scanned under C / et_EE / da_DK must give byte-identical reports.
#                   CALIBRATED: the fixture calls into two uncovered packages `tpad` and `zpad` ONCE
#                   EACH, so the κ ledger's primary key (count, descending) ties and hands the decision
#                   to the NAME comparator. With unequal counts the fixture would pass under
#                   `localeCompare` and pin nothing, so the tie is asserted before the bytes are
#                   compared: no tie, no cell.
#   query-bytes     the same for a query document (`unverified --json`) over a hand-written report.
#   codepoint-order the frontier's ENTRY ORDER on `app.Zed.go` vs `app.alpha.go`. ICU compares letters
#                   case-INSENSITIVELY at the primary level, so `localeCompare` puts `Zed` second while
#                   code point puts it first ('Z' U+005A < 'a' U+0061). This one disagrees in EVERY
#                   locale including C, so unlike the two differential cells it catches the defect on a
#                   runtime with no Estonian data at all. The `unverified` list order rides with it,
#                   which is how candor-swift — which has no `callers` verb — gets a cell here.

LOCALES = ["C", "et_EE.UTF-8", "da_DK.UTF-8"]


def locale_probe():
    """Does THIS machine carry a collation that reorders pure ASCII? Returns the discriminating locales.

    NOT `tr_TR`, and this is the trap. Turkish inserts its extra letters BETWEEN the ASCII ones, so it
    leaves pure-ASCII order alone: a C-vs-tr_TR control comes back "no difference" and licenses a false
    all-clear over a live defect. `et_EE` collates `z` between `s` and `t`; `da_DK` sorts `aa` as `å`,
    after `z`. The probe names the locale through `strcoll` explicitly, so it answers "does this box
    carry the data?" independently of the parent process's own environment."""
    good = []
    for loc in LOCALES[1:]:
        try:
            _locale.setlocale(_locale.LC_COLLATE, loc)
            if _locale.strcoll("zpad", "tpad") < 0 or _locale.strcoll("aardvark", "zebra") > 0:
                good.append(loc)
        except Exception:
            pass
        finally:
            try:
                _locale.setlocale(_locale.LC_COLLATE, "C")
            except Exception:
                pass
    return good


# The locale fixture, per engine. Two uncovered packages called ONCE EACH (the κ-ledger tie), plus
# function names that differ exactly where Estonian and Danish disagree with code point.
RUST_LOC_SRC = """pub fn zpad() { tpad::a(); }
pub fn tpad_call() { zpad::b(); }
pub fn spad() { let _ = std::fs::read("/tmp/s"); }
pub fn aardvark() { zpad(); }
pub fn zebra() { spad(); }
"""
JAVA_LOC_SRC = """package app;
public class Loc {
  public static void zpad() { tpad.A.a(); }
  public static void tpadCall() { zpad.B.b(); }
  public static void spad() { }
  public static void aardvark() { zpad(); }
  public static void zebra() { spad(); }
}
"""
TS_LOC_SRC = """import { a } from 'tpad';
import { b } from 'zpad';
export function zpad() { a(); }
export function tpadCall() { b(); }
export function spad() { }
export function aardvark() { zpad(); }
export function zebra() { spad(); }
"""
SWIFT_LOC_SRC = """import tpad
import zpad
func zpad_call() { tpad.a() }
func tpadCall() { zpad.b() }
func spad() { }
func aardvark() { zpad_call() }
func zebra() { spad() }
"""


def _build_loc_fixture(d, eng):
    """Write the locale fixture into `d` and return the scan invocation's inputs."""
    if eng == "rust":
        os.makedirs(os.path.join(d, "src"), exist_ok=True)
        open(os.path.join(d, "Cargo.toml"), "w").write(
            "[package]\nname = \"lp\"\nversion = \"0.1.0\"\nedition = \"2021\"\n"
            "[dependencies]\ntpad = \"1\"\nzpad = \"1\"\n")
        open(os.path.join(d, "src", "lib.rs"), "w").write(RUST_LOC_SRC)
    elif eng == "java":
        for pkg, cls, body in (("app", "Loc", JAVA_LOC_SRC),
                               ("tpad", "A", "package tpad; public class A { public static void a() {} }"),
                               ("zpad", "B", "package zpad; public class B { public static void b() {} }")):
            os.makedirs(os.path.join(d, pkg), exist_ok=True)
            open(os.path.join(d, pkg, cls + ".java"), "w").write(body)
    elif eng == "ts":
        open(os.path.join(d, "package.json"), "w").write('{"name":"lp","version":"0.0.0"}')
        open(os.path.join(d, "cases.ts"), "w").write(TS_LOC_SRC)
        for p in ("tpad", "zpad"):
            m = os.path.join(d, "node_modules", p)
            os.makedirs(m, exist_ok=True)
            open(os.path.join(m, "package.json"), "w").write(
                '{"name":"%s","version":"1.0.0","main":"index.js","types":"index.d.ts"}' % p)
            open(os.path.join(m, "index.js"), "w").write("exports.a=function(){};exports.b=function(){};")
            open(os.path.join(m, "index.d.ts"), "w").write(
                "export declare function a(): void;\nexport declare function b(): void;\n")
    else:
        open(os.path.join(d, "cases.swift"), "w").write(SWIFT_LOC_SRC)


def _scan_bytes(ws, eng, locales):
    """Scan the locale fixture under each locale; return {locale: report bytes} or None.

    ONE DIRECTORY, REUSED, wiped between locales — never one directory per locale. The first cut of this
    used `…/loc/<engine>/<locale>/` and reported candor-swift as locale-DEPENDENT: swift derives the
    package name from the containing directory, so `"hash": "C#zpad"` vs `"hash": "et_EE_UTF-8#zpad"`
    was the harness's own path leaking into the bytes it was diffing. A row that varies two things at
    once measures neither."""
    out = {}
    d = os.path.join(ws, "loc", eng)
    for loc in locales:
        shutil.rmtree(d, ignore_errors=True)      # delete outputs before measuring
        os.makedirs(d, exist_ok=True)
        env = dict(os.environ, LC_ALL=loc, LANG=loc)
        _build_loc_fixture(d, eng)
        if eng == "rust":
            run([rust_scan(), d], env=env)
            cdir = os.path.join(d, ".candor")
            cand = [os.path.join(cdir, f) for f in os.listdir(cdir)] if os.path.isdir(cdir) else []
        elif eng == "java":
            allc = os.path.join(d, "all")
            srcs = [os.path.join(d, p, c + ".java")
                    for p, c in (("app", "Loc"), ("tpad", "A"), ("zpad", "B"))]
            if run(["javac", "-d", allc] + srcs, env=env).returncode:
                return None
            # Scan ONLY `app`: tpad/zpad are then off the analyzed set, which is what makes them
            # UNCOVERED packages rather than analyzed ones.
            only = os.path.join(d, "only", "app")
            os.makedirs(only, exist_ok=True)
            for f in os.listdir(os.path.join(allc, "app")):
                shutil.copy(os.path.join(allc, "app", f), only)
            rep = os.path.join(d, "r.json")
            run(["java", "-jar", java_jar(), os.path.join(d, "only"), "--json", rep], env=env)
            cand = [rep] if os.path.exists(rep) else []
        elif eng == "ts":
            run(["node", os.path.join(ts_root(), "scan.mjs"), d, "--out", os.path.join(d, "r")], env=env)
            cand = [os.path.join(d, "r.json")] if os.path.exists(os.path.join(d, "r.json")) else []
        else:
            run([swift_bin(), os.path.join(d, "cases.swift"), "--out", os.path.join(d, "r")], env=env)
            cand = [os.path.join(d, f) for f in os.listdir(d) if f.startswith("r.")]
        cand = [p for p in cand if p.endswith(".json") and "callgraph" not in p
                and "hierarchy" not in p and "locs" not in p]
        if not cand:
            return None
        out[loc] = open(sorted(cand)[0], "rb").read()
    return out


def _tie_present(report_bytes):
    """The CALIBRATION: did the fixture actually produce the κ-ledger tie the cell relies on? Without
    two uncovered packages at EQUAL call counts, the primary key decides the order and the name
    comparator is never consulted — the cell would pass under `localeCompare` and pin nothing."""
    try:
        unc = json.loads(report_bytes).get("coverage", {}).get("uncovered", [])
    except Exception:
        return False
    by = {e.get("name"): e.get("calls") for e in unc}
    return "tpad" in by and "zpad" in by and by["tpad"] == by["zpad"]


# The ORDER fixture. `Zed` vs `alpha`: code point puts `Zed` first ('Z' U+005A < 'a' U+0061); ICU's
# primary level is case-insensitive, so every locale-aware comparator puts `alpha` first.
R7_ORDER_REPORT = {
    "candor": {"version": "handwritten", "spec": "0.23"},
    "package": "app",
    "analyzed": {"count": 4, "digest": "0"},
    "functions": [
        {"fn": "app.Sink.touch", "inferred": ["Fs"], "direct": ["Fs"], "paths": ["/tmp/x"]},
        {"fn": "app.Impl.run", "inferred": ["Fs"], "calls": ["app.Sink.touch"]},
        {"fn": "app.Zed.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run"]},
        {"fn": "app.alpha.go", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run"]},
    ],
}
R7_ORDER_CG = {e["fn"]: e.get("calls", []) for e in R7_ORDER_REPORT["functions"]}
R7_ORDER_EXPECT = ["app.Zed.go", "app.alpha.go"]


def row_r7(ws, pol_pure, discriminating):
    cells = []
    locales = ["C"] + discriminating
    for eng in ENGINES:
        if not present(eng):
            for c in ("report-bytes", "query-bytes", "codepoint-order"):
                cells.append((eng, c, ABSENT, "", ""))
            continue

        # -- codepoint-order: runs on ANY box, discriminating or not -------------------------------
        loc = write_report(ws, eng, R7_ORDER_REPORT, callgraph=R7_ORDER_CG, hierarchy=R3_HIER)
        seen, bad = [], []
        if eng in FRONTIER_ENGINES:
            res, err = q_callers(eng, loc, "app.Sink.touch")
            if res is None:
                bad.append(f"frontier: no parseable document ({err})")
            else:
                order = [p["fn"] for p in res.get("possibleViaUnknownDispatch", [])]
                seen.append(f"frontier {order}")
                if not order:
                    bad.append("frontier came back empty")
                elif order != R7_ORDER_EXPECT:
                    bad.append(f"frontier entry order {order} != code point {R7_ORDER_EXPECT}")
        uv, _, e2 = q_unverified(eng, loc, pol_pure)
        if uv is None:
            bad.append(f"unverified: no parseable document ({e2})")
        else:
            order = [x["fn"] for x in uv.get("unverified", []) if x["fn"] in R7_ORDER_EXPECT]
            seen.append(f"unverified {order}")
            if not order:
                bad.append("unverified selected neither ordering probe")
            elif order != R7_ORDER_EXPECT:
                bad.append(f"unverified order {order} != code point {R7_ORDER_EXPECT}")
        cells.append((eng, "codepoint-order", VACUOUS if not seen else (OK if not bad else FAIL),
                      "; ".join(bad) or "; ".join(seen), "Zed before alpha, by code point"))

        # -- the two locale differentials ------------------------------------------------------------
        if not discriminating:
            note = ("no ASCII-reordering collation on this box (et_EE / da_DK absent) — a "
                    "NON-DISCRIMINATING regression guard here, asserting nothing. The codepoint-order "
                    "cell above still bites.")
            cells.append((eng, "report-bytes", NOSURF, note, ""))
            cells.append((eng, "query-bytes", NOSURF, note, ""))
            continue

        got = _scan_bytes(ws, eng, locales)
        if got is None:
            cells.append((eng, "report-bytes", ERROR, "the locale fixture produced no report",
                          "one report per locale"))
        elif not _tie_present(got["C"]):
            cells.append((eng, "report-bytes", VACUOUS,
                          "no κ-ledger tie (tpad/zpad at equal call counts) in the report — the name "
                          "comparator is never reached, so byte-equality here would pin nothing",
                          "coverage.uncovered = [tpad:n, zpad:n]"))
        else:
            diff = [l for l in locales if got[l] != got["C"]]
            cells.append((eng, "report-bytes", OK if not diff else FAIL,
                          f"report bytes differ under {diff}" if diff
                          else f"identical under {', '.join(locales)} (κ tie present)",
                          "byte-identical across locales"))

        loc = write_report(ws, eng, R2_REPORT, callgraph=R2_CG, hierarchy=R2_HIER)
        outs, err = {}, ""
        for l in locales:
            env = dict(os.environ, LC_ALL=l, LANG=l)
            if eng == "rust":
                cmd = [rust_query(), "unverified", "--report", loc, "--policy", pol_pure, "--json"]
            elif eng == "java":
                cmd = ["java", "-jar", java_jar(), "unverified", "--report", loc, "--policy", pol_pure,
                       "--json"]
            elif eng == "ts":
                cmd = ["node", os.path.join(ts_root(), "query.mjs"), "unverified", "--report", loc,
                       "--policy", pol_pure]
            else:
                cmd = [swift_bin(), "unverified", "--report", loc, "--policy", pol_pure]
            r = run(cmd, env=env)
            outs[l] = r.stdout
            err = err or r.stderr.decode()[:200]
        if not any(outs.values()):
            cells.append((eng, "query-bytes", ERROR, err, "one query document per locale"))
        else:
            diff = [l for l in locales if outs[l] != outs["C"]]
            cells.append((eng, "query-bytes", OK if not diff else FAIL,
                          f"query bytes differ under {diff}" if diff
                          else f"identical under {', '.join(locales)}",
                          "byte-identical across locales"))
    return cells



# =====================================================================================================
# the ratchet + the print
# =====================================================================================================

ROWS = [
    ("R1", "§6.2 CONTRIBUTES — a reasonless Unknown ADDS `unresolved`, it does not default to it"),
    ("R2", "§3.1 viaDispatchOn — the EXACT joined literal (sorted, deduplicated)"),
    ("R3", "§3.1 the DOT-FREE frontier arm — disclosed verbatim, identically in both arms"),
    ("R4", "§3.1 the SIDECAR TRIPLE — absent ≡ {} ≡ unparseable ≢ populated"),
    ("R5", "§6.2 --class — dynamic excludes only setup-only entries, narrower filters\n        discriminate, and an unhonourable filter value is refused"),
    ("R6", "§3.1 gate --report — byte-equality, the MUST NOT, and the three answerability refusals"),
    ("R8", "§3.1 PRECEDENCE — a certain violation dominates a refusal; a refusal still writes a document"),
    ("R9", "CROSS-ENGINE verdict KEY PARITY — the same situation must produce the same keys"),
    ("R10", "REPORT-ENVELOPE key parity — the artifact that TRAVELS between engines"),
    ("R7", "§2 locale-independence — the same input under two collations, byte for byte"),
]


def load_baseline(path):
    """⟨0.24⟩ An UNREADABLE baseline must not read as 'nothing is waived'.

    PARTs 24, 25 and 26 all say this explicitly and print a FAIL line naming the parse error. PART 27 —
    the newest, and the one whose author wrote the other three — just let `json.load` raise. A crash is
    caught upstream by run.sh's `|| P27_OK=1`, so this was never fail-OPEN; what it cost was the
    diagnosis. The run reported a Python traceback where its three siblings report which file could not
    be read and why, and 'the ratchet is misconfigured' then looks exactly like 'an engine regressed'.

    Found by auditing the four ratchets for the shape that produced three of five harness defects this
    week — a check whose subject and oracle come from the same source. That shape was ABSENT here (the
    baselines are hand-maintained and never regenerated from live output, and all four hard-fail when
    the file is missing). This inconsistency is what the audit turned up instead, and a sweep whose main
    result is 'three of four were already right' is worth the same as one that finds a defect: it says
    the pattern is not systemic.
    """
    if not path:
        return []
    try:
        with open(path) as fh:
            return json.load(fh).get("known", [])
    except Exception as ex:
        print(f"\nFAIL: --baseline {path} is unreadable ({ex}). A baseline that cannot be read must "
              f"not read as 'nothing is waived'.")
        raise SystemExit(2)


def waived(known, row, engine, cell, verdict=FAIL):
    """`engine: "*"` waives every engine — used only where the defect is a CLAUSE no engine implements,
    never to blanket a defect that differs per engine (that is what hides a shrinking one).

    ⟨0.24⟩ A WAIVER PINS A DEFECT, NOT A CELL — and it may only absorb the verdict KIND it was written
    for. A review defeated the two strongest guards in this file with one waiver: `FAILING` contains
    `ERROR` and `VACUOUS` as well as `FAIL`, so a waiver written for a known wrong ANSWER also absorbed
    "the engine emitted garbage" (ERROR — the verdict that exists precisely so a mis-invocation cannot
    read as a statement about candor) and "the fixture stopped triggering" (VACUOUS). Measured: with
    `CANDOR_QUERY_BIN` shimmed to return non-JSON and one `{"row":"R1","engine":"rust","cell":"*"}`
    waiver, an engine emitting pure garbage exited 0, the waiver was CONSUMED so it never read stale,
    and the cells still counted as LIVE. The mechanism built to stop a waiver outliving its defect is
    the mechanism that hid the defect's replacement.

    So a waiver carries `kind` (default `FAIL`) and matches only that verdict. Waiving an ERROR or a
    VACUOUS is still possible, but it must be written down as such, where a reader will see it.
    """
    for k in known:
        if (k["row"] == row and k["engine"] in ("*", engine)
                and k.get("cell", "*") in ("*", cell)
                and k.get("kind", FAIL) == verdict):
            return k
    return None


def main():
    args = sys.argv[1:]
    baseline = None
    only = None
    keep = False
    i = 0
    while i < len(args):
        if args[i] == "--baseline":
            baseline = args[i + 1]; i += 2
        elif args[i] == "--only":
            only = set(args[i + 1].split(",")); i += 2
        elif args[i] == "--keep":
            keep = True; i += 1
        else:
            print(f"gen_rung024.py: unknown argument {args[i]!r}", file=sys.stderr)
            return 2
    known = load_baseline(baseline)

    ws = tempfile.mkdtemp(prefix="candor-rung024-")
    pol = {}
    for name, text in (("pure", "pure app"), ("unres", "deny Unknown[unresolved] app"),
                       ("deny_fs", "deny Fs"), ("deny_net", "deny Net"),
                       ("forbid", "forbid app -> infra"), ("allow", "allow Net in app example.com"),
                       ("scoped", "deny Net[unknown-host] app"), ("bare_net", "deny Net app"),
                       ("r1_fire", "deny Unknown[reflect] app"),
                       # R8: a FIRING rule and an UNANSWERABLE rule in the SAME policy.
                       ("r8_mixed", "deny Fs\ndeny Net[unknown-host] app"),
                       ("r8_refuse_only", "deny Net[unknown-host] app"),
                       ("r8_fire_only", "deny Fs"),
                       ("r9_fs", "deny Fs")):
        p = os.path.join(ws, "pol." + name)
        open(p, "w").write(text + "\n")
        pol[name] = p

    print("PART 27 — the ⟨0.24⟩ rung's BEHAVIOUR (SPEC §2 / §3.1 / §6.2)")
    here = [e for e in ENGINES if present(e)]
    # INSTALLED BUT DEAD is its own state and must never render as "absent — nothing demanded of it".
    broken = [e for e in ENGINES if installed(e) and not alive(e)]
    print(f"  engines present: {', '.join(here) if here else '(none)'}")
    disc = locale_probe()
    disc_note = ", ".join(disc) if disc else "NONE — R7 is a non-discriminating guard on this box"
    print(f"  ASCII-reordering collation here: {disc_note}")

    results = {}
    try:
        gate_pols = {k: pol[k] for k in ("deny_fs", "deny_net", "pure", "forbid", "allow", "scoped",
                                         "bare_net")}
        plan = [("R1", lambda: row_r1(ws, pol["pure"], pol["unres"], pol["r1_fire"], pol["deny_fs"])),
                ("R2", lambda: row_r2(ws)),
                ("R3", lambda: row_r3(ws)),
                ("R4", lambda: row_r4(ws)),
                ("R5", lambda: row_r5(ws, pol["pure"])),
                ("R6", lambda: row_r6(ws, gate_pols)),
                ("R8", lambda: row_r8(ws, pol)),
                ("R9", lambda: row_r9(ws, pol)),
                ("R10", lambda: row_r10(ws, pol)),
                ("R7", lambda: row_r7(ws, pol["pure"], disc))]
        for name, fn in plan:
            if only and name not in only:
                continue
            results[name] = fn()
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)

    # ---- print + judge -------------------------------------------------------------------------
    rc = 0
    total_live = 0
    # A waiver for a row this invocation did not RUN is not stale — it is untested. `--only R2` must not
    # report R1's live defect as a defect that has been fixed.
    stale = [k for k in known if k["row"] in results]
    for name, title in ROWS:
        if name not in results:
            continue
        print(f"\n  {name}  {title}")
        live = 0
        for eng, cell, verdict, got, want in results[name]:
            if verdict in LIVE:
                live += 1
            mark = verdict
            w = waived(known, name, eng, cell, verdict)
            if verdict in FAILING and w:
                mark = "FAIL(waived)"
                stale = [k for k in stale if k is not w]
            elif verdict in FAILING:
                rc = 1
            note = got if got else ""
            if verdict == ERROR:
                note = f"HARNESS/ENGINE INVOCATION — not a statement about candor: {note}"
            if verdict == FAIL and want:
                note = f"{note}   [want: {want}]"
            print(f"    {eng:6s} {cell:15s} {mark:13s} {note}")
        total_live += live
        if live == 0:
            print(f"    -> ROW VACUOUS: no live cell. A fixture that stopped triggering is not a pass.")
            rc = 1

    if broken:
        print(f"\n  ENGINE PRESENT BUT NOT RESPONDING: {', '.join(broken)}. Its cells above read ABSENT, "
              "which demands nothing — so the run FAILS here instead. This is a HARNESS/INSTALL problem, "
              "not a statement about candor.")
        rc = 1
    if total_live == 0:
        print("\n  VACUITY FLOOR: not one live cell in the whole run. Reporting success here would be "
              "reporting that nothing ran.")
        rc = 1
    if stale:
        print("\n  STALE WAIVERS — these baseline entries no longer have a failing cell. A waiver that "
              "outlives its defect masks the defect's return; delete them:")
        for k in stale:
            print(f"    {k['row']} {k['engine']} {k.get('cell', '*')}")
        rc = 1

    print(f"\n  {total_live} live cell(s).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
