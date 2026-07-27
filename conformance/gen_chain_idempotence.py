#!/usr/bin/env python3
"""
P2 — CHAIN IDEMPOTENCE, as a GENERATED property (SCAN-BOUNDARY-WORK-QUEUE.md §3).

    chain(report R) twice   ==   chain(report R) once

Hand the consumer the SAME dependency report two times and it must answer exactly what it answers when
handed it once. This is a self-differential, like P1 and for the same reason: the cross-engine suite asks
"do the four engines agree?", and four engines that share one spec and one author's mental model agree
just as readily when the model is wrong (the coverage door and the malformed manifest were both four-way).
An engine cannot share a wrong model with ITSELF across two renderings of one input, so **the arm that
chains once is the oracle for the arm that chains twice** — no reference implementation, no second
opinion, and NO EXPECTED-VALUE TABLE. If one ever appears in this file, this has become a fixture suite.

WHY THIS PROPERTY, AND WHY IT IS REGRESSION-SHAPED
--------------------------------------------------
Two reports covering one package in one dep directory is ORDINARY, not pathological: measured at 7/167 dep
reports in candor-rust, 9/259 in pgman, 30/378 in ebman (ENTRY-COLLISION-DECISION.md). It arises from a
dep dir that accumulates, from `--workspace` prepending its own directory to `CANDOR_DEPS`, and from a
package scanned twice. And it has already bitten: candor-rust `6f2210c` — two byte-identical reports made
a consumer VANISH from `functions`, which under ⟨0.21⟩ is a positive purity CLAIM, not a gap.

DELIBERATELY NOT IN SCOPE: two reports under one key with DIFFERENT answers. That is a live design
question with a decision already recorded (ENTRY-COLLISION-DECISION.md — adopt the union) and four
engines that genuinely differ. This file tests the IDENTICAL case only, which is strictly easier and on
which every engine should already agree; folding the two together would make a settled property fail for
an unsettled reason. P3 covers the one sub-case of disagreement that is about TRUST rather than content.

THE RELATION IS EQUALITY — and that is the difference from P1
--------------------------------------------------------------
P1 had to be directional: a chained arm may legitimately carry MORE disclosure than a single-tree one,
because a boundary genuinely exists there and the engine can see less across it. Simplifying P1 to
equality would fail 32 cells the family has already ruled correct.

**No such asymmetry exists here.** Both arms are the same program, the same boundary, the same producing
engine and the same report — literally the same bytes, or the same JSON re-serialised. There is nothing
the two-copy arm can legitimately see less (or more) of. So equality is the whole property, over BOTH
what the report claims and what it discloses:

    effects  equal   +   Unknown equal   +   kappa `invisible` equal   +   presence equal

A disclosure-only divergence is a real divergence here, not slack: if the duplicate arm newly records the
dependency as `uncovered`, the engine is claiming a blind spot it demonstrably does not have, and the
`coverage` ledger is the field a consumer reads to decide whether a green verdict was earned.
The verdict letters below separate the severities so the OUTPUT still says which kind of break it is; the
RELATION does not.

**Measured, first run: on rust the duplicate loses the effect entirely; on java, ts and swift all three
duplication spellings are exactly equal, 80/80 cells. So equality is not a bar nobody can clear** — three
of four engines clear it on every live cell, which is the number that justifies the choice.

THE THREE DUPLICATION SPELLINGS, and why one of them is not redundant
---------------------------------------------------------------------
  same_path   — the identical path listed twice on CANDOR_DEPS
  two_files   — two files, byte-identical content, different names
  reserialised— two files, DIFFERENT bytes (sorted keys, different indent), identical content
The third is the one that matters. An engine that dedupes by hashing the file passes the first two and
is not idempotent at all: the real duplicate in a dep directory is *the same package scanned twice*, whose
bytes differ in ordering and whitespace. This is P1's own lesson — every hand-written fixture had picked
ONE spelling — applied to P2 before it could bite.

VACUITY (standing bar item 8). Live/vacuous is computed FROM THE ENGINE'S OWN OUTPUT, never asserted:
a cell whose reference arm carries no concrete effect demands little, and is counted VACUOUS — but only
when the duplicate arm agrees with it, so vacuity can never swallow a divergence. The run FAILS if any
engine's live count is zero, and FAILS if a non-reference arm produced no report while exiting 0.

USAGE
    python3 gen_chain_idempotence.py                    # raw truth, exit non-zero on any divergence
    python3 gen_chain_idempotence.py --only lazy_init,field
    python3 gen_chain_idempotence.py --keep
    python3 gen_chain_idempotence.py --baseline chain-idempotence-baseline.json   # the ratchet (PART 25)
"""
import json
import os
import shutil
import sys
import tempfile

import gen_differential as gd
import split_arms as sa

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the arms. The FIRST is the reference; the rest are the duplications. -----------------------------
ARMS = [
    ("once", lambda dep, scratch: dep),
    ("same_path", lambda dep, scratch: dep + " " + dep),
    ("two_files", lambda dep, scratch: dep + " " + sa.copy_as(dep, scratch, "dup-copy.json")),
    ("reserialised", lambda dep, scratch: dep + " " + sa.reserialise(dep, scratch, "dup-reser.json")),
]
REF = ARMS[0][0]
DUPS = [a for a, _ in ARMS[1:]]

# ---- verdicts, in severity order ---------------------------------------------------------------------
LOST = "LOST"            # the duplicate arm dropped a concrete effect the single-copy arm had
ABSENT = "ABSENT"        # the fn itself vanished from the duplicate arm's report — a <0.21> purity claim
GAINED = "GAINED"        # the duplicate arm invented a concrete effect
APPEARED = "APPEARED"    # the fn exists only in the duplicate arm
DISC = "DISC"            # effects agree; the DISCLOSURE (Unknown / kappa invisible) differs
OK = "OK"
VACUOUS = "VACUOUS"      # arms agree and the reference carries no concrete effect
REFUSED = "REFUSED"      # the arm produced no report and the engine exited non-zero (fail-closed)
BROKEN = "BROKEN"        # no report and exit ZERO: the harness or the engine, NOT a statement about candor.
                         # It gets its own letter because the first draft reused GAINED here, and a run
                         # with a mis-invoked arm then printed "the duplicate arm invented an effect ...
                         # once=(ABSENT) twice=(ABSENT)" — a usage failure dressed as a finding, which is
                         # the exact defect P1's own harness shipped with.

FAILING = (LOST, ABSENT, GAINED, APPEARED, DISC)
LETTER = {OK: ".", VACUOUS: "v", REFUSED: "-", BROKEN: "!", DISC: "d", LOST: "X", ABSENT: "A",
          GAINED: "f", APPEARED: "p"}


def judge(ref, arm):
    """ref/arm are leaf_info entries, or None when the fn is absent from that arm's report."""
    if ref is None and arm is None:
        return VACUOUS
    if ref is None:
        return APPEARED if (arm["eff"] or sa.hedged(arm)) else VACUOUS
    if arm is None:
        return ABSENT
    if ref["eff"] - arm["eff"]:
        return LOST
    if arm["eff"] - ref["eff"]:
        return GAINED
    if ref["unknown"] != arm["unknown"] or ref["invisible"] != arm["invisible"] or ref["why"] != arm["why"]:
        return DISC
    return OK if ref["eff"] else VACUOUS


def main():
    args = sys.argv[1:]
    keep = "--keep" in args
    only = None
    for a in args:
        if a.startswith("--only"):
            only = set((a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]).split(","))
    if only:
        # A misspelled --only must be a USAGE error, never a silently-empty run. An empty run trips the
        # vacuity floor and prints a sentence about the engines that is true of zero cells and false of
        # everything else — P1's harness had exactly this defect and it read as a substantive finding.
        unknown = sorted(only - set(sa.split_ids()))
        if unknown:
            print("usage error: --only names no such split shape: %s\n  available: %s"
                  % (", ".join(unknown), ", ".join(sa.split_ids())))
            sys.exit(2)
    baseline_path = None
    for a in args:
        if a.startswith("--baseline"):
            baseline_path = a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]

    cells = sa.build_cells("p2", only)
    by_split = {}
    for c in cells:
        by_split.setdefault(c["split"], []).append(c)

    print("=" * 112)
    print("P2 — CHAIN IDEMPOTENCE  (each engine vs ITSELF: one copy of a dep report  ==  two copies)")
    print("  effects : %s" % ", ".join(e["effect"] for e in gd.EFFECTS))
    print("  splits  : %s" % ", ".join(sorted(by_split)))
    print("  arms    : %s   (reference = %s)" % (", ".join(a for a, _ in ARMS), REF))
    print("  cells   : %d   (%d split shapes x %d effects), each scanned once per arm per engine"
          % (len(cells), len(by_split), len(gd.EFFECTS)))
    print("=" * 112)

    ws = tempfile.mkdtemp(prefix="candor-p2chain-")
    results, skipped, broken, depinfo = {}, {}, {}, {}
    armstate = {}          # engine -> arm -> "ok" | "refused" | "broken"
    ledger = []            # report-level kappa divergences: (engine, arm, split, ref_uncovered, arm_uncovered)
    for eng, runner in sa.ENGINES:
        per_split, deps, err = sa.run_engine(eng, runner, ws, by_split, ARMS)
        if err:
            (skipped if sa.engine_absent(err) else broken)[eng] = err
            print("  %-6s %s -- %s" % (eng, "SKIPPED" if sa.engine_absent(err) else "FAILED ", err))
            continue
        per_cell, bad_ref = {}, None
        for sid, arms in per_split.items():
            ref = arms[REF]
            if ref.leaves is None:
                # The REFERENCE arm is the only oracle this property has. If it produced nothing, the run
                # concluded nothing — and must say so rather than label every cell REFUSED, which would
                # read as the engine deliberately declining perfectly good input.
                bad_ref = ("%s: the `%s` REFERENCE arm produced no report (rc=%s) — the oracle is missing, "
                           "so nothing can be concluded about the duplicate arms" % (sid, REF, ref.rc))
                break
            for dup in DUPS:
                a = arms[dup]
                st = "refused" if a.refused else ("broken" if a.broken else "ok")
                prev = armstate.setdefault(eng, {}).get(dup)
                armstate[eng][dup] = st if prev in (None, st) else "mixed"
                for c in by_split[sid]:
                    if a.leaves is None:
                        per_cell[(c["name"], dup)] = (REFUSED if a.refused else BROKEN, None, None)
                        continue
                    r, x = ref.leaves.get(c["name"]), a.leaves.get(c["name"])
                    per_cell[(c["name"], dup)] = (judge(r, x), r, x)
            for dup in DUPS:
                a = arms[dup]
                if a.leaves is not None and a.uncovered != ref.uncovered:
                    ledger.append((eng, dup, sid, sorted(ref.uncovered), sorted(a.uncovered)))
            depinfo.setdefault(eng, {})[sid] = sa.dep_stats(deps[sid])
        if bad_ref:
            broken[eng] = bad_ref
            print("  %-6s FAILED  -- %s" % (eng, bad_ref))
            continue
        results[eng] = per_cell
        print("  %-6s ok -- %d cells x %d duplication arms" % (eng, len(cells), len(DUPS)))

    available = [e for e, _ in sa.ENGINES if e in results]

    # ---- the matrix: one column per engine, one letter per duplication arm ----
    print("\nMATRIX  (cell x engine; the %d letters per engine are the arms %s, each compared with `%s`)"
          % (len(DUPS), "/".join(DUPS), REF))
    print("  .=OK  v=VACUOUS(reference carries no effect and the arms agree)  -=REFUSED(no report, "
          "engine exited non-zero)\n"
          "  !=BROKEN(no report, exit 0: the harness, not a finding)  X=LOST(effect dropped)  A=ABSENT(fn vanished)  f=GAINED(effect invented)  "
          "p=APPEARED(fn only in the duplicate)  d=DISC(disclosure differs)")
    head = "%-30s " % "cell" + " ".join("%-6s" % e for e in available)
    print(head)
    print("-" * len(head))
    for c in cells:
        row = "%-30s " % c["name"]
        for e in available:
            row += "%-6s " % "".join(LETTER[results[e].get((c["name"], d), (VACUOUS, None, None))[0]]
                                     for d in DUPS)
        print(row)
    print("-" * len(head))

    # ---- counts. Per (engine, arm), because "which duplication spelling breaks it" is the finding. ----
    print("\nCOUNTS per engine x duplication arm")
    print("  %-8s %-13s %6s %6s %8s %7s %5s %5s %5s %5s %5s %5s"
          % ("engine", "arm", "cells", "live", "vacuous", "refused", "ok", "LOST", "ABS", "GAIN", "APP",
             "DISC"))
    rc = 0
    for e in available:
        for d in DUPS:
            t = {}
            for c in cells:
                v = results[e].get((c["name"], d), (VACUOUS, None, None))[0]
                t[v] = t.get(v, 0) + 1
            live = len(cells) - t.get(VACUOUS, 0) - t.get(REFUSED, 0)
            print("  %-8s %-13s %6d %6d %8d %7d %5d %5d %5d %5d %5d %5d"
                  % (e, d, len(cells), live, t.get(VACUOUS, 0), t.get(REFUSED, 0), t.get(OK, 0),
                     t.get(LOST, 0), t.get(ABSENT, 0), t.get(GAINED, 0), t.get(APPEARED, 0),
                     t.get(DISC, 0)))
            # ARM FLOOR. An arm with no live cells proves nothing, and looks exactly like one that passes.
            # REFUSED is the one benign way to have none: the engine saw the input and said no.
            if live == 0 and t.get(REFUSED, 0) != len(cells):
                print("  FAIL (vacuity floor): %s/%s produced ZERO live cells and did not refuse -- %s"
                      % (e, d, "no cells were generated at all" if not cells else
                         "every reference arm read the entry pure, so nothing was demanded of the duplicate"))
                rc = 2
        st = armstate.get(e, {})
        for d in DUPS:
            if st.get(d) == "broken":
                print("  FAIL: %s/%s produced NO report while exiting 0 -- that is the harness or the "
                      "engine broken, not a refusal, and it must never read as benign." % (e, d))
                rc = 2

    print("\nDEP-HALF COVERAGE  (is the witness even IN the dependency's own report? if not, the loss is "
          "on the\n  PRODUCER side and this property is measuring the wrong thing)")
    for e in available:
        print("  %-8s %s" % (e, ", ".join("%s:%d/%d" % (s, eff, tot)
                                          for s, (tot, eff) in sorted(depinfo.get(e, {}).items()))))

    # ---- findings ----
    buckets = {k: [] for k in FAILING}
    for e in available:
        for d in DUPS:
            for c in cells:
                v, r, x = results[e].get((c["name"], d), (VACUOUS, None, None))
                if v in buckets:
                    buckets[v].append((e, d, c, r, x))

    def fmt(i):
        if i is None:
            return "(ABSENT)"
        bits = sorted(i["eff"]) + (["Unknown"] if i["unknown"] else [])
        s = ",".join(bits) or "(pure)"
        return s + ("  invisible=" + ",".join(sorted(i["invisible"])) if i["invisible"] else "")

    for kind, header in ((LOST, "LOST — chaining the identical report twice DROPPED an effect the single "
                                "copy inherited:"),
                         (ABSENT, "ABSENT — the function vanished from the duplicate arm's report "
                                  "(a <0.21> purity claim):"),
                         (GAINED, "GAINED — the duplicate arm invented an effect the single copy did not "
                                  "have:"),
                         (APPEARED, "APPEARED — the function exists only in the duplicate arm:"),
                         (DISC, "DISC — the effects agree but the DISCLOSURE differs (a blind spot claimed "
                                "or dropped on identical input):")):
        rows = buckets[kind]
        if not rows:
            continue
        print("\n%d %s" % (len(rows), header))
        for e, d, c, r, x in rows[:24]:
            print("  %-6s %-13s %-30s [%s/%s]  once=%s  twice=%s"
                  % (e, d, c["name"], c["split"], c["effect"], fmt(r), fmt(x)))
        if len(rows) > 24:
            print("  ... and %d more (same shape)" % (len(rows) - 24))

    # ---- the report-level half of idempotence. The per-cell verdicts above compare each entry's `invisible`
    # set; this compares the whole report's `coverage.uncovered`, which is the field a consumer reads to
    # decide whether a green verdict was earned. They move together in everything measured so far — which is
    # exactly why checking only one of them would be an untested assumption rather than a decision.
    ledger_pairs = {(e, d, sid) for e, d, sid, _, _ in ledger}
    # ONE failing-key set, used by the ratchet, the NEW-DEBT list and the exit code alike, so a divergence
    # cannot be reported in one place and forgotten in another.
    fail_keys = {(e, d, c["split"]) for k in FAILING for e, d, c, _, _ in buckets[k]} | ledger_pairs
    if ledger:
        print("\n%d REPORT-LEVEL LEDGER divergence(s) — the report's `coverage.uncovered` set changed when "
              "the\n  SAME report was chained twice, i.e. the engine claimed (or dropped) a blind spot on "
              "identical input:" % len(ledger))
        for e, d, sid, ru, au in ledger:
            print("  %-6s %-13s %-22s once=%s  twice=%s"
                  % (e, d, sid, ",".join(ru) or "(none)", ",".join(au) or "(none)"))

    # ---- the RATCHET. Records DEFECTS, not expected answers: nothing in the baseline tells the property
    # what an engine SHOULD say — the single-copy arm is still the only oracle. It says "this (engine,
    # arm, shape) is known-broken and someone wrote down why", so the row stays green while the debt stays
    # visible and countable. It ratchets BOTH ways: unwaived failures fail the run, AND a waiver whose
    # cells all pass fails the run, so a waiver cannot outlive its defect and start masking its return.
    # `"split": "*"` waives every shape for a pair — the defect here is a property of the JOIN, not of the
    # shape, and the failing-shape list is printed on every run so a shrinking defect is visible.
    waived = set()
    if baseline_path:
        try:
            with open(baseline_path) as f:
                bl = json.load(f)
        except Exception as ex:
            print("\nFAIL: --baseline %s is unreadable (%s). A baseline that cannot be read must not "
                  "read as 'nothing is waived'." % (baseline_path, ex))
            rc = 2
            bl = {"known": []}
        known = [(k["engine"], k["arm"], k.get("split", "*"), k.get("why", "")) for k in bl.get("known", [])]
        failing = {}
        for e, d, sid in fail_keys:
            failing.setdefault((e, d), set()).add(sid)
        print("\nRATCHET  (baseline: %s)" % baseline_path)
        for eng, arm, sid, why in sorted(known):
            if eng not in available:
                print("  %-6s %-13s %-12s -- engine not available this run, waiver not checked"
                      % (eng, arm, sid))
                continue
            hit = failing.get((eng, arm), set())
            hit = hit if sid == "*" else (hit & {sid})
            if hit:
                n = sum(1 for k in FAILING for e, d, c, _, _ in buckets[k]
                        if e == eng and d == arm and (sid == "*" or c["split"] == sid))
                print("  %-6s %-13s %-12s WAIVED  %d cell(s) over %d shape(s) [%s] -- %s"
                      % (eng, arm, sid, n, len(hit), ",".join(sorted(hit)), why))
                for s in hit:
                    waived.add((eng, arm, s))
            else:
                print("  %-6s %-13s %-12s FAIL (STALE WAIVER): baselined as known-broken but every cell "
                      "now passes. Delete the entry — a waiver that outlives its defect masks the "
                      "defect's return." % (eng, arm, sid))
                rc = 2
        unwaived = sorted(fail_keys - waived)
        if unwaived:
            print("  NEW DEBT (not in the baseline): "
                  + ", ".join("%s/%s/%s" % t for t in unwaived))

    n_fail = len(fail_keys - waived)
    if n_fail:
        rc = rc or 1
    if broken:
        for e, why in broken.items():
            print("\nFAIL: engine '%s' present but broken -- %s" % (e, why))
        rc = 2
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print("FAIL (strict): engine '%s' REQUIRED but absent -- %s" % (e, why))
        rc = 2

    print()
    if rc == 0:
        n_w = sum(1 for k in FAILING for e, d, c, _, _ in buckets[k] if (e, d, c["split"]) in waived)
        tail = (", EXCEPT %d cell(s) waived by the ratchet in %s"
                % (n_w, ", ".join(sorted({"%s/%s" % (e, d) for e, d, _ in waived})))) if waived else ""
        print("P2 CHAIN IDEMPOTENCE: OK — %d engine(s) (%s) each give the SAME answer chaining a report "
              "twice as chaining it once, on every live cell%s."
              % (len(available), ", ".join(available), tail))
    else:
        print("P2 CHAIN IDEMPOTENCE: FAILED — see the findings above.")

    if keep:
        print("\n[--keep] generated workspace retained at: %s" % ws)
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
