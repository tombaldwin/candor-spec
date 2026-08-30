#!/usr/bin/env python3
"""
P3 — TRUST MONOTONICITY, as a GENERATED property (SCAN-BOUNDARY-WORK-QUEUE.md §3).

    a dependency report the engine cannot or should not trust may only ADD hedges.
    It may never buy CONFIDENCE, and it may never ERASE a fact the engine was given.

Same construction as P1 and P2 and for the same reason: the cross-engine suite asks "do the four engines
agree?", and four engines sharing one spec and one author's mental model agree just as readily when the
model is wrong — the coverage door was four-way. Here each engine is compared with ITSELF across two
renderings of the same trust question, so common-mode is excluded by construction. There is NO
EXPECTED-VALUE TABLE and there must never be one; the other arm is the expectation.

THE TWO REFERENCE ARMS — this property is a SANDWICH, not a single comparison
-----------------------------------------------------------------------------
    trusted     the report exactly as the dependency's own scan produced it     -- the KNOWLEDGE ceiling
    unchained   CANDOR_DEPS unset: the same program with no dep report at all   -- the HEDGE floor

Every degraded arm must sit between them. Its knowledge may not exceed `trusted` (a report you distrust
cannot teach you something the real one did not), and its DISCLOSURE may not fall below `unchained` (a
report you refuse to use cannot silence a blind spot you would otherwise have declared). The second bound
is the one with a body count: it is the **coverage door** — an engine that rejects a dep report for a
version mismatch and nonetheless registers the package as COVERED turns every function that report did not
mention into a confident purity claim. That defect was in all four engines.

WHY THE DIRECTION IS SPELT OUT PER ARM, AND WHY ONE ARM RUNS THE OPPOSITE WAY
------------------------------------------------------------------------------
  REPLACE  (stale_version, no_version, incomplete, malformed) — the degraded report stands INSTEAD of the
           good one. Losing effects is FINE if the loss is disclosed; going silent is not. A violation
           means: distrust manufactured confidence.
  FLOOR    (empty_zero) — the report is present, parses, is version-matched, and claims to have judged
           NOTHING (`functions: []`, `analyzed.count: 0`). It must not buy more confidence than having no
           report at all. A violation means: an empty report is read as an all-clear.
  BESIDE   (stale_beside) — the degraded report sits ALONGSIDE the good one, which is the ordinary
           accumulating-dep-directory case. Here the direction INVERTS: the trusted report is still there,
           so every effect it carries must still be in the answer, and a hedge does NOT license discarding
           it. A violation means: a report the engine refused to trust erased a fact from one it did.
           This is candor-java's measured `deny Fs` exit 1 -> exit 0 (ENTRY-COLLISION-DECISION.md).
  CONTROL  (empty_allpure) — never fails; see below.

Getting this wrong in either direction manufactures findings. Judging BESIDE by the REPLACE rule would
call java's erasure a legitimate disclosed loss and report nothing. Judging REPLACE by the BESIDE rule
would fail all four engines for the correct §2.1 downgrade to `Unknown`.

DISCLOSURE HAS TWO CHANNELS AND BOTH COUNT — measured, not assumed
------------------------------------------------------------------
An engine can say "there is something here I could not see" with `Unknown` or with the κ coverage ledger
(`invisible` + report-level `coverage.uncovered`). Handed an unparseable dep report, candor-rust and
candor-ts drop the inherited effects and record the package as uncovered — byte-identical to their answer
with no dep report at all, which is the CORRECT trust semantics (an unusable report contributes nothing).
A property counting only `Unknown` would file that as a cardinal loss on two engines. Both channels
therefore count as disclosure — and are still tracked separately, because `deny E Unknown` bites on one
and not the other, so a move from `Unknown` to κ is a gate-visible weakening (verdict `CHANNEL`, counted).

THE NEGATIVE CONTROL, and why it is in-band rather than in a comment
---------------------------------------------------------------------
`empty_allpure` is `empty_zero` with ONE integer changed back: `functions: []` but `analyzed.count` as
produced. That is a legitimate all-pure claim which §2 chaining rule 3 says a consumer SHOULD believe, so
the control must NEVER fail. Its job is to answer the question the FLOOR arm cannot answer alone — *is the
engine failing because the report is empty, or because it claims nothing?* If both arms give the same
verdicts, the engine is not reading `analyzed.count` and the two are indistinguishable to it; when
somebody fixes the door, the two arms MUST diverge. That comparison is printed every run (CONTROL
SEPARATION) because a control that is not looked at is not a control.

VACUITY (standing bar item 8) is computed from the ENGINE'S OWN output, never asserted: a cell whose
`trusted` arm carries no concrete effect demands nothing of the degraded arms and is counted VACUOUS. The
run FAILS if any engine's live count is zero, if a reference arm produced nothing, or if a degraded arm
produced no report while exiting 0 (that is the harness broken, and it must never read as a refusal).

USAGE
    python3 gen_trust_monotonicity.py                 # raw truth, exit non-zero on any violation
    python3 gen_trust_monotonicity.py --only field,lazy_init
    python3 gen_trust_monotonicity.py --keep
    python3 gen_trust_monotonicity.py --baseline trust-monotonicity-baseline.json   # the ratchet (PART 26)
"""
# THE CONTRACT THIS PROPERTY ENFORCES, quoted so clause_check.py can prove SPEC.md still says it. Unlike
# P1/P2/P4 this one is NOT a pure self-differential: its two reference arms bracket a rule the spec states
# — a distrusted report contributes `Unknown` rather than its claims, and coverage is what turns a
# report's silence into a purity claim.
SPEC_CLAUSES = [
    ("§2 rule 2", "Stale reports are not trusted"),
    ("§2 rule 3", "A chained package is COVERED, not blind, including its silence."),
]

import concurrent.futures
import json
import os
import shutil
import sys
import tempfile

import gen_differential as gd
import split_arms as sa

HERE = os.path.dirname(os.path.abspath(__file__))

TRUSTED, UNCHAINED = "trusted", "unchained"
REPLACE, FLOOR, BESIDE, CONTROL = "REPLACE", "FLOOR", "BESIDE", "CONTROL"

# ---- the arms. The first two are the references; the rest are degradations, each with its direction. --
ARMS = [
    (TRUSTED, None, lambda dep, s: dep),
    (UNCHAINED, None, lambda dep, s: None),
    # §2.1: a producing version that does not match the running engine is unverifiable -> downgrade.
    ("stale_version", REPLACE, lambda dep, s: sa.with_version(dep, s, "stale.json", "NOT-THIS-BUILD-0.0.0")),
    # §2.1 again: "a MISSING version is as unverifiable as a mismatched one".
    ("no_version", REPLACE, lambda dep, s: sa.without_version(dep, s, "nover.json")),
    # ⟨0.21⟩: the producer's own source it could not read. Its "absent => pure" convention is unbacked.
    ("incomplete", REPLACE, lambda dep, s: sa.with_unanalyzed(dep, s, "incomplete.json")),
    ("malformed", REPLACE, lambda dep, s: sa.truncated(dep, s, "malformed.json")),
    # the live corpus shape: a chained report listing no functions and claiming to have judged none.
    ("empty_zero", FLOOR, lambda dep, s: sa.emptied(dep, s, "empty0.json", True)),
    # the negative control: the same file with `analyzed.count` left alone = a real all-pure claim.
    ("empty_allpure", CONTROL, lambda dep, s: sa.emptied(dep, s, "emptyN.json", False)),
    # the accumulating dep directory: a distrusted copy beside the good one.
    ("stale_beside", BESIDE,
     lambda dep, s: dep + " " + sa.with_version(dep, s, "beside-stale.json", "NOT-THIS-BUILD-0.0.0")),
]
RUN_ARMS = [(n, mk) for n, _, mk in ARMS]
CLASSOF = {n: c for n, c, _ in ARMS if c}
DEGRADED = [n for n, c, _ in ARMS if c]

# ---- verdicts ----------------------------------------------------------------------------------------
CARDINAL = "CARDINAL"        # knowledge lost and NOTHING disclosed
DOOR = "DOOR"                # ... and the unchained arm DID disclose here: the hedge was available
ABSENT = "ABSENT"            # the function vanished from the degraded arm's report: a <0.21> purity claim
ERASED = "ERASED"            # BESIDE only: a fact from the still-present TRUSTED report is gone
LOST_HEDGE = "LOST_HEDGE"    # trusted hedged, the degraded arm does not: it became MORE confident
HEDGED_LOSS = "HEDGED_LOSS"  # knowledge lost, disclosed: the correct §2.1 behaviour
CHANNEL = "CHANNEL"          # same knowledge, hedge moved Unknown -> kappa: a gate-visible weakening
EXTRA_EFF = "EXTRA_EFF"      # the degraded arm has knowledge the trusted arm did not
OK = "OK"
VACUOUS = "VACUOUS"
REFUSED = "REFUSED"          # no report, engine exited non-zero: fail-closed, a legitimate answer
BROKEN = "BROKEN"            # no report and exit ZERO: the harness or the engine, NOT a statement about
                             # candor. Distinct from REFUSED on purpose — labelling it a refusal would
                             # print a mis-invocation as good fail-closed behaviour.

FAILING = (CARDINAL, DOOR, ABSENT, ERASED, LOST_HEDGE)
# ... except on a CONTROL arm, which is judged and printed and NEVER fails. `empty_allpure` legitimately
# makes a consumer read pure — that is §2 chaining rule 3, an all-pure dependency's empty report is a claim
# — so a run that failed it would be demanding a fix that breaks the chaining contract. It exists to say
# whether the FLOOR arm's failure is about EMPTINESS or about the report claiming nothing.
LETTER = {OK: ".", VACUOUS: "v", REFUSED: "-", BROKEN: "!", HEDGED_LOSS: "h", CHANNEL: "k",
          EXTRA_EFF: "f", CARDINAL: "X", DOOR: "D", ABSENT: "A", ERASED: "E", LOST_HEDGE: "U"}



# ⟨0.24⟩ KNOWN-VACUOUS SHAPES — the per-shape floor's ratchet. Measured 2026-08-01, the first run after the
# floor existed. A shape listed here produced cells and ZERO live ones for that engine, so those cells prove
# nothing today. Two different things live in this table and they MUST be told apart by triage, not by
# assumption:
#   * legitimately N/A for the language (a Rust `dyn` return has no Java analogue), where the honest fix is
#     to stop EMITTING the cells rather than to waive them — a cell that cannot fire is not coverage;
#   * a fixture that STOPPED TRIGGERING, which is a live defect wearing the same clothes.
# Neither is distinguishable from the other by looking at the count, which is why this needs a reason per
# row and why none is written yet. It ratchets: a shape going dead that is NOT listed fails the run.
KNOWN_VACUOUS = {
    "rust":  {"callback", "fn_returned_dyn"},
    "java":  {"fn_returned_dyn"},
    "swift": {"fn_returned_dyn"},
    "ts":    {"callback", "fn_returned_dyn", "lazy_init"},
}

# PROBE MODE — see probe_check.py / gen_split_invariance.py for why "verified to catch" must be a GATE,
# not a habit applied once at authoring time. Registered in probe_check.py's COVERED dict (closing the
# gap its own header used to name in UNCOVERED: "judge() takes four arms; the injection has to pick one
# without colliding with the BESIDE arm's inverted direction"). The injection is a VALUE corruption, not
# an absence: it does not drop the cell to `None` (gen_chain_idempotence.py already covers that branch of
# judge()) — it rewrites a REPLACE-class degraded arm's leaf_info in place so it reports full confidence
# with no hedge at all, the exact CARDINAL shape this property exists to catch (distrust manufacturing
# confidence). Firing only on a REPLACE cell also sidesteps the BESIDE arm's inverted direction the header
# above warns about.
_PROBE_FAULT = os.environ.get("CANDOR_PROBE_FAULT")
_probe_fired = []


def _maybe_probe_corrupt(cls, name, key, ar):
    if _PROBE_FAULT and not _probe_fired and cls == REPLACE and ar is not None and ar["eff"]:
        _probe_fired.append(True)
        print("  PROBE: rewrote one live REPLACE cell's degraded arm (%s/%s) into silent full confidence "
              "(effects dropped, no hedge) — this run MUST fail" % (name, key))
        return {"eff": frozenset(), "unknown": False, "invisible": frozenset(), "why": ar["why"]}
    return ar


def judge(cls, tr, un, ar):
    """tr/un/ar: leaf_info entries for the trusted, unchained and degraded arms; None = absent from that
    arm's report. Read the direction notes in the header before changing any branch here."""
    if tr is None:
        # the trusted arm makes no claim about this fn, so there is nothing to preserve. An arm that
        # invents one is still worth naming.
        return EXTRA_EFF if (ar is not None and ar["eff"]) else VACUOUS
    if ar is None:
        return ABSENT
    lost = tr["eff"] - ar["eff"]
    gained = ar["eff"] - tr["eff"]
    if cls == BESIDE and lost:
        # the trusted report is STILL in the dep directory. No hedge licenses dropping what it says.
        return ERASED
    if lost:
        if not sa.hedged(ar):
            # was the hedge even available? if the engine discloses here with NO report at all, then it
            # had the machinery and the degraded report silenced it: that is the coverage door.
            return DOOR if (un is not None and sa.hedged(un)) else CARDINAL
        return HEDGED_LOSS
    if sa.hedged(tr) and not sa.hedged(ar):
        return LOST_HEDGE
    if gained:
        return EXTRA_EFF
    if tr["unknown"] and not ar["unknown"] and ar["invisible"]:
        return CHANNEL
    return OK if tr["eff"] else VACUOUS


def main():
    args = sys.argv[1:]
    keep = "--keep" in args
    only = None
    for a in args:
        if a.startswith("--only"):
            only = set((a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]).split(","))
    if only:
        # A misspelled --only is a USAGE error, never a silently-empty run: an empty run trips the vacuity
        # floor and prints a sentence that is true of zero cells and misleading about the engines.
        unknown = sorted(only - set(sa.split_ids()))
        if unknown:
            print("usage error: --only names no such split shape: %s\n  available: %s"
                  % (", ".join(unknown), ", ".join(sa.split_ids())))
            sys.exit(2)
    baseline_path = None
    for a in args:
        if a.startswith("--baseline"):
            baseline_path = a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]

    cells = sa.build_cells("p3", only)
    by_split = {}
    for c in cells:
        by_split.setdefault(c["split"], []).append(c)

    print("=" * 118)
    print("P3 — TRUST MONOTONICITY  (each engine vs ITSELF: a report it cannot trust may only ADD hedges)")
    print("  effects : %s" % ", ".join(e["effect"] for e in gd.EFFECTS))
    print("  splits  : %s" % ", ".join(sorted(by_split)))
    print("  refs    : %s (knowledge ceiling), %s (hedge floor)" % (TRUSTED, UNCHAINED))
    print("  degraded: %s" % ", ".join("%s[%s]" % (n, CLASSOF[n]) for n in DEGRADED))
    print("  cells   : %d   (%d split shapes x %d effects), each scanned once per arm per engine"
          % (len(cells), len(by_split), len(gd.EFFECTS)))
    print("=" * 118)

    ws = tempfile.mkdtemp(prefix="candor-p3trust-")
    results, skipped, broken, depinfo, refnote = {}, {}, {}, {}, {}
    armstate = {}
    # THE FOUR ENGINES RUN CONCURRENTLY. `split_arms.run_engine` scopes every fixture to
    # `<ws>/<engine>/<split>`, so the engines share no path and no state; each is scored only against
    # ITSELF. Sequentially this generator was the single most expensive thing in the suite.
    #
    # Only the expensive call is moved. Everything below — the scoring, the ratchet, every print —
    # still runs in the main thread in engine order, so the output is byte-identical to the sequential
    # version and a reader diffing two runs sees nothing move.
    _pre = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as _ex:
        _f = {_ex.submit(sa.run_engine, e, r, ws, by_split, RUN_ARMS): e for e, r in sa.ENGINES}
        for _fut in concurrent.futures.as_completed(_f):
            _pre[_f[_fut]] = _fut.result()
    for eng, runner in sa.ENGINES:
        per_split, deps, err = _pre[eng]
        if err:
            (skipped if sa.engine_absent(err) else broken)[eng] = err
            print("  %-6s %s -- %s" % (eng, "SKIPPED" if sa.engine_absent(err) else "FAILED ", err))
            continue
        per_cell, bad_ref = {}, None
        for sid, arms in per_split.items():
            tr, un = arms[TRUSTED], arms[UNCHAINED]
            if tr.leaves is None or un.leaves is None:
                bad_ref = "%s: a REFERENCE arm produced no report (trusted rc=%s, unchained rc=%s) — the " \
                          "oracle is missing, so nothing can be concluded" % (sid, tr.rc, un.rc)
                break
            for name in DEGRADED:
                a = arms[name]
                st = "refused" if a.refused else ("broken" if a.broken else "ok")
                prev = armstate.setdefault(eng, {}).get(name)
                armstate[eng][name] = st if prev in (None, st) else "mixed"
                if a.leaves is None:
                    for c in by_split[sid]:
                        per_cell[(c["name"], name)] = (REFUSED if a.refused else BROKEN,
                                                       None, None, None)
                    refnote.setdefault((eng, name), a.note)
                    continue
                for c in by_split[sid]:
                    k = c["name"]
                    a_leaf = _maybe_probe_corrupt(CLASSOF[name], name, k, a.leaves.get(k))
                    per_cell[(k, name)] = (judge(CLASSOF[name], tr.leaves.get(k), un.leaves.get(k),
                                                 a_leaf),
                                           tr.leaves.get(k), a_leaf, un.leaves.get(k))
            depinfo.setdefault(eng, {})[sid] = sa.dep_stats(deps[sid])
        if bad_ref:
            broken[eng] = bad_ref
            print("  %-6s FAILED  -- %s" % (eng, bad_ref))
            continue
        results[eng] = per_cell
        print("  %-6s ok -- %d cells x %d degraded arms" % (eng, len(cells), len(DEGRADED)))

    available = [e for e, _ in sa.ENGINES if e in results]

    # ---- the matrix ----
    print("\nMATRIX  (cell x engine; the %d letters per engine are the arms, in order:\n    %s)"
          % (len(DEGRADED), "  ".join("%d=%s" % (i + 1, n) for i, n in enumerate(DEGRADED))))
    print("  .=OK  v=VACUOUS  -=REFUSED(fail-closed: no report, non-zero exit)  "
          "!=BROKEN(no report, exit 0: the harness)  h=HEDGED_LOSS(disclosed, correct)\n  k=CHANNEL(hedge moved Unknown->kappa)  f=EXTRA_EFF\n"
          "  X=CARDINAL(knowledge lost, nothing disclosed)  D=DOOR(...and unchained DID disclose here)  "
          "A=ABSENT(fn vanished)\n  E=ERASED(a still-present trusted fact dropped)  "
          "U=LOST_HEDGE(became more confident)")
    head = "%-30s " % "cell" + " ".join("%-9s" % e for e in available)
    print(head)
    print("-" * len(head))
    for c in cells:
        row = "%-30s " % c["name"]
        for e in available:
            row += "%-9s " % "".join(LETTER[results[e].get((c["name"], n), (VACUOUS, None, None, None))[0]]
                                     for n in DEGRADED)
        print(row)
    print("-" * len(head))

    # ---- counts ----
    print("\nCOUNTS per engine x degraded arm")
    # ERAS+U is ERASED plus LOST_HEDGE: both are "the degraded arm ended up MORE confident", and the
    # findings section below separates them. The header says so rather than reading as one verdict.
    print("  %-8s %-14s %-8s %6s %6s %8s %7s %5s %5s %5s %5s %5s %5s %5s %6s"
          % ("engine", "arm", "class", "cells", "live", "vacuous", "refused", "ok", "hedge", "chan",
             "xeff", "CARD", "DOOR", "ABS", "ERAS+U"))
    rc = 0
    for e in available:
        for n in DEGRADED:
            t = {}
            for c in cells:
                v = results[e].get((c["name"], n), (VACUOUS, None, None, None))[0]
                t[v] = t.get(v, 0) + 1
            live = len(cells) - t.get(VACUOUS, 0) - t.get(REFUSED, 0)
            print("  %-8s %-14s %-8s %6d %6d %8d %7d %5d %5d %5d %5d %5d %5d %5d %6d"
                  % (e, n, CLASSOF[n], len(cells), live, t.get(VACUOUS, 0), t.get(REFUSED, 0),
                     t.get(OK, 0), t.get(HEDGED_LOSS, 0), t.get(CHANNEL, 0), t.get(EXTRA_EFF, 0),
                     t.get(CARDINAL, 0), t.get(DOOR, 0), t.get(ABSENT, 0),
                     t.get(ERASED, 0) + t.get(LOST_HEDGE, 0)))
            # ARM FLOOR. Zero live cells proves nothing and looks exactly like passing. REFUSED is the one
            # benign way to have none: the engine saw the input and said no, loudly, with a non-zero exit.
            if live == 0 and t.get(REFUSED, 0) != len(cells):
                print("  FAIL (vacuity floor): %s/%s produced ZERO live cells and did not refuse -- %s"
                      % (e, n, "no cells were generated at all" if not cells else
                         "every trusted arm read the entry pure, so nothing was demanded of the degraded arm"))
                rc = 2
            # ⟨0.24⟩ PER-SHAPE FLOOR — see the sibling in gen_split_invariance.py. The arm floor above
            # only sees an ENTIRE arm going dead; one split shape rotting to vacuous is invisible while the
            # others carry the count, and the per-shape numbers were printed and never asserted.
            by_split = {}
            for c in cells:
                v = results[e].get((c["name"], n), (VACUOUS, None, None, None))[0]
                tt = by_split.setdefault(c.get("split", "?"), [0, 0])
                tt[0] += 1
                if v not in (VACUOUS, REFUSED):
                    tt[1] += 1
            dead = sorted(sp for sp, (tot, lv) in by_split.items() if tot and lv == 0)
            dead = [d for d in dead if d not in KNOWN_VACUOUS.get(e, set())]
            if dead and t.get(REFUSED, 0) != len(cells):
                print("  FAIL (per-shape vacuity floor): %s/%s has shape(s) with cells but ZERO live: %s"
                      % (e, n, ", ".join(dead)))
                rc = 2
            if armstate.get(e, {}).get(n) == "broken":
                print("  FAIL: %s/%s produced NO report while exiting 0 -- the harness or the engine is "
                      "broken, and that must never read as a fail-closed refusal." % (e, n))
                rc = 2
        for n in DEGRADED:
            if (e, n) in refnote:
                print("      %s/%s REFUSED, engine said: %s" % (e, n, refnote[(e, n)][:150]))

    print("\nDEP-HALF COVERAGE  (is the witness even IN the dependency's own report? if not, this property "
          "is\n  measuring the wrong thing)")
    for e in available:
        print("  %-8s %s" % (e, ", ".join("%s:%d/%d" % (s, eff, tot)
                                          for s, (tot, eff) in sorted(depinfo.get(e, {}).items()))))

    # ---- CONTROL SEPARATION. The FLOOR arm and the CONTROL arm differ by ONE integer. Whether an engine
    # can tell them apart is the whole diagnosis, and it is printed rather than asserted. ----
    ctl = [n for n, c, _ in ARMS if c == CONTROL]
    flr = [n for n, c, _ in ARMS if c == FLOOR]
    if ctl and flr:
        print("\nCONTROL SEPARATION  (`%s` vs `%s` differ ONLY in ⟨0.21⟩ `analyzed.count`: 0 = 'I judged "
              "nothing'\n  vs the produced count = 'I judged N units and none has an effect', which §2 "
              "chaining rule 3 says a\n  consumer SHOULD believe. An engine that reads the manifest must "
              "answer them DIFFERENTLY.)" % (flr[0], ctl[0]))
        for e in available:
            same = sum(1 for c in cells
                       if results[e].get((c["name"], flr[0]), (VACUOUS,))[0]
                       == results[e].get((c["name"], ctl[0]), (VACUOUS,))[0])
            verdict = ("INDISTINGUISHABLE — the engine is not reading `analyzed.count`"
                       if same == len(cells) else
                       "SEPARATED on %d/%d cells — the engine distinguishes them" % (len(cells) - same,
                                                                                     len(cells)))
            print("  %-8s %s" % (e, verdict))

    # ---- findings ----
    buckets = {k: [] for k in FAILING + (HEDGED_LOSS, CHANNEL, EXTRA_EFF)}
    control_rows = []
    for e in available:
        for n in DEGRADED:
            for c in cells:
                v, tr, ar, un = results[e].get((c["name"], n), (VACUOUS, None, None, None))
                if CLASSOF[n] == CONTROL:
                    if v in FAILING:
                        control_rows.append((e, n, c, tr, ar, un, v))
                    continue          # a CONTROL arm is observed, never failed -- see FAILING above
                if v in buckets:
                    buckets[v].append((e, n, c, tr, ar, un))

    def fmt(i):
        if i is None:
            return "(ABSENT)"
        s = ",".join(sorted(i["eff"]) + (["Unknown"] if i["unknown"] else [])) or "(pure)"
        return s + (" +invisible=" + ",".join(sorted(i["invisible"])) if i["invisible"] else "")

    for kind, header in (
        (DOOR, "COVERAGE DOOR — knowledge lost with NO disclosure, on a cell where the SAME engine with "
               "no dep report at all does disclose. The report it would not use silenced the hedge:"),
        (CARDINAL, "CARDINAL — knowledge lost with no disclosure in either channel:"),
        (ABSENT, "ABSENT — the function vanished from the degraded arm's report (a ⟨0.21⟩ purity claim):"),
        (ERASED, "ERASED — a distrusted report sitting BESIDE the trusted one removed an effect the "
                 "trusted report still carries:"),
        (LOST_HEDGE, "LOST_HEDGE — the trusted arm hedged and the degraded arm does not: the less "
                     "trustworthy input produced the MORE confident answer:"),
        (CHANNEL, "CHANNEL — same knowledge, but the hedge moved from `Unknown` to the κ ledger. Not a "
                  "loss; counted because `deny E Unknown` bites on one and not the other:"),
        (EXTRA_EFF, "EXTRA EFFECT — the degraded arm carries knowledge the trusted arm did not (named, "
                    "not failed: the cardinal sin is the other direction):"),
    ):
        rows = buckets.get(kind) or []
        if not rows:
            continue
        print("\n%d %s" % (len(rows), header))
        for e, n, c, tr, ar, un in rows[:24]:
            print("  %-6s %-14s %-30s [%s/%s]  trusted=%s  degraded=%s  |unchained=%s"
                  % (e, n, c["name"], c["split"], c["effect"], fmt(tr), fmt(ar), fmt(un)))
        if len(rows) > 24:
            print("  ... and %d more (same shape)" % (len(rows) - 24))

    if control_rows:
        by = {}
        for e, n, c, tr, ar, un, v in control_rows:
            by[(e, n, v)] = by.get((e, n, v), 0) + 1
        print("\nCONTROL ARM — verdicts that WOULD be violations on a degraded arm, and are NOT counted "
              "here.\n  On `empty_allpure` the consumer reading pure is §2 chaining rule 3 working as "
              "specified (an all-pure\n  dependency's empty report is a CLAIM, not a blind spot). Printed "
              "so the exemption is visible rather\n  than silent — if this block is empty while the FLOOR "
              "arm still fails, the two have SEPARATED:")
        for (e, n, v), k in sorted(by.items()):
            print("  %-8s %-14s %-10s %d cell(s)  [exempt]" % (e, n, v, k))

    # ---- the RATCHET. Records DEFECTS, not expected answers: the baseline never tells the property what
    # an engine SHOULD say — the engine's own reference arms remain the only oracle. It ratchets BOTH
    # ways: an unwaived failure fails the run, and a waiver whose cells all pass ALSO fails it, so a
    # waiver cannot outlive its defect and start masking the defect's return. `"split": "*"` waives every
    # shape for an (engine, arm) pair — a trust defect is a property of the JOIN, not of the call shape —
    # and the failing shapes are printed every run, so a shrinking defect stays visible.
    waived = set()
    if baseline_path:
        try:
            with open(baseline_path) as f:
                bl = json.load(f)
        except Exception as ex:
            print("\nFAIL: --baseline %s is unreadable (%s). A baseline that cannot be read must not read "
                  "as 'nothing is waived'." % (baseline_path, ex))
            rc = 2
            bl = {"known": []}
        known = [(k["engine"], k["arm"], k.get("split", "*"), k.get("why", "")) for k in bl.get("known", [])]
        failing = {}
        for k in FAILING:
            for e, n, c, _, _, _ in buckets[k]:
                failing.setdefault((e, n), set()).add(c["split"])
        print("\nRATCHET  (baseline: %s)" % baseline_path)
        for eng, arm, sid, why in sorted(known):
            if eng not in available:
                print("  %-6s %-14s %-12s -- engine not available this run, waiver not checked"
                      % (eng, arm, sid))
                continue
            hit = failing.get((eng, arm), set())
            hit = hit if sid == "*" else (hit & {sid})
            if hit:
                n_cells = sum(1 for k in FAILING for e, a, c, _, _, _ in buckets[k]
                              if e == eng and a == arm and (sid == "*" or c["split"] == sid))
                print("  %-6s %-14s %-12s WAIVED  %d cell(s) over %d shape(s) [%s] -- %s"
                      % (eng, arm, sid, n_cells, len(hit), ",".join(sorted(hit)), why))
                for s in hit:
                    waived.add((eng, arm, s))
            else:
                print("  %-6s %-14s %-12s FAIL (STALE WAIVER): baselined as known-broken but every cell "
                      "now passes. Delete the entry — a waiver that outlives its defect masks the "
                      "defect's return." % (eng, arm, sid))
                rc = 2
        unwaived = sorted({(e, n, c["split"]) for k in FAILING for e, n, c, _, _, _ in buckets[k]} - waived)
        if unwaived:
            print("  NEW DEBT (not in the baseline): " + ", ".join("%s/%s/%s" % t for t in unwaived))

    n_fail = sum(1 for k in FAILING for e, n, c, _, _, _ in buckets[k] if (e, n, c["split"]) not in waived)
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
        n_w = sum(1 for k in FAILING for e, n, c, _, _, _ in buckets[k] if (e, n, c["split"]) in waived)
        tail = (", EXCEPT %d cell(s) waived by the ratchet in %s"
                % (n_w, ", ".join(sorted({"%s/%s" % (e, n) for e, n, _ in waived})))) if waived else ""
        print("P3 TRUST MONOTONICITY: OK — %d engine(s) (%s): every degraded dep report only ADDED hedges, "
              "on every live cell%s." % (len(available), ", ".join(available), tail))
    else:
        print("P3 TRUST MONOTONICITY: FAILED — see the findings above.")

    if keep:
        print("\n[--keep] generated workspace retained at: %s" % ws)
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
