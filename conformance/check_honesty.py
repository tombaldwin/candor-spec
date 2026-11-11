#!/usr/bin/env python3
"""Honesty-invariant checker — the candor §4 trust contract, in executable form.

candor's ONE dangerous lie is the silent UNDER-report: reporting a function `pure`/effect-free when it
isn't. This checks one machine-verifiable necessary condition for honesty over a candor report:

    UNCERTAINTY MUST PROPAGATE CALLER-WARD.
    A function may look "certain" (no `Unknown`, no disclosure) only if EVERYTHING it transitively
    reaches is also certain. If f calls g and g is uncertain (Unknown / unresolved / invisible / blind /
    incomplete), then f must carry that uncertainty too — else f looks more trustworthy than its callees
    justify (a swallowed-uncertainty under-report).

Equivalently, for every internal call edge f -> g:  uncertain(g)  ⟹  uncertain(f).
(Checking every edge one-hop is complete: the first broken propagation in any chain is some edge.)

Also checks the direct form: a function flagged `unresolved` must surface `Unknown` (or a disclosure).

SCOPE / HONEST LIMITS: this is an INTERNAL-CONSISTENCY check on a report — it catches uncertainty that
candor HAD but failed to propagate. It CANNOT catch candor's own BLINDNESS (a call/effect candor never
registered, e.g. the log-macro under-report): from the report alone, that call is invisible. For that
class use the dynamic syscall oracle (soundness/oracle*.sh) or an independent-method differential.

CRITICAL: candor's main report OMITS pure functions (only effectful/disclosed ones appear), but a
PURE-LOOKING function reaching an uncertain callee is exactly the dangerous case. So edges are read from
the CALLGRAPH sidecar (spec §2.2: every function is a key), and uncertainty from the report — a function
in the callgraph but ABSENT from the report is pure-and-certain, and is checked like any other.

WHICH ROW JUDGES A CALLEE (SOUNDNESS R1673). A name can carry a unit row and a synthetic `interfaceUnion` row
beside it; the check keeps them apart and counts ANY uncertain row (see `check`). For candor-scan, positively
identified by its `scan-` build id, a callee with a body is judged by its unit rows only: its sidecar keys are
all bodies, and a dispatch is the caller's `dispatchesOn`. Every other report (java, swift, ts, unidentified)
keeps the union row in play, because those engines key body-less members too (java abstract methods, swift
protocol requirements) and an edge to one is a dispatch the union row alone exposes; only a static initializer
chain and a Scala `m$` forwarder are carved out. The wire cannot tell a static call from a dispatch, so this
oracle does not verify obligation 1 either way.

Works on ANY engine's report (rust/java/ts/swift — one spec format). Exit 0 iff honest.
Usage:  python3 check_honesty.py <report.json> [<report2.json> ...]
        (the sibling <report>.callgraph.json is loaded automatically.)
"""
import json
import os
import re
import sys


def uncertain(f):
    """True if the function's report DISCLOSES any incompleteness (the honest forms of 'I'm not sure').
    `None` (a fn absent from the report, i.e. pure) is certain by construction."""
    if f is None:
        return False
    if "Unknown" in (f.get("inferred") or []):
        return True
    return bool(f.get("unresolved") or f.get("invisible") or f.get("blind") or f.get("incomplete"))


def callgraph_path(report_path):
    return report_path[:-5] + ".callgraph.json" if report_path.endswith(".json") else report_path + ".callgraph.json"


_INIT = re.compile(r"(\.|^)(init|<init>)(\(|#\d+$|$)")


def static_edge(fn, callee):
    """An edge that is statically resolved by construction, so the callee's DISPATCH reach (its union row) is
    not the caller's: an initializer chaining to another initializer (`super.init`/`self.init`; never
    dispatched dynamically), and a Scala trait's static forwarder `m$` -> `m` (compiled to `invokespecial`).
    Ground truth, SOUNDNESS R1673: 14 of 24 distinct swift removals and 170 of 307 java ones were exactly these."""
    return (callee + "$" == fn) or (bool(_INIT.search(fn)) and bool(_INIT.search(callee)))


def check(funcs, edges, full_graph=True, keys_are_bodies=False):
    """funcs: list of report function objects (effectful/disclosed only).
    edges: {fn_name: [callee_name, ...]} from the callgraph (ALL functions). Returns [(fn, reason)].
    full_graph: False when `edges` was rebuilt from the report itself (no sidecar).
    keys_are_bodies: the engine's sidecar keys are ONLY units with a body (candor-scan: a body-less trait member
      is never a key). Set ONLY on positive identification of such an engine (see `main`).

    A NAME can carry two kinds of row (SOUNDNESS R1673): the unit's own row, and a synthetic
    `interfaceUnion: true` row published BESIDE it under the same `fn` (SPEC §3.1: a union entry "is never a
    unit of a verdict"; it says what a DISPATCH on that member can reach). A name-keyed dict let one shadow the
    other in BOTH directions, so the rows are kept apart, and ANY uncertain row of a name counts (a last-wins
    dict hid a real `Unknown` behind a pure sibling). Which rows judge a callee:
      - keys_are_bodies: a callee with a body (a unit row, or a callgraph key) is judged by its UNIT rows only.
        A dispatch through the member is the CALLER's `dispatchesOn` (§4 obligation 1), so the union's
        `Unknown` is not the callee's. A callee that is neither a unit nor a key is body-less: its union row.
      - otherwise (java, swift, ts, anything unidentified): EVERY row of the name, unit and union. These
        engines key body-less members too (java's abstract methods, swift's protocol requirements), and an
        edge to one is a dispatch whose only uncertainty is the union row, so dropping it blinds the oracle.
        MEASURED: swift `ByteToMessageHandler.handlerRemoved` and ReactiveSwift `Observer.process` are real
        under-reports (no dispatch edges, no dispatchesOn) that only the union row exposes. The one carve-out is
        `static_edge`. The wire cannot tell a static call from a dispatch otherwise, so the strict reading is
        the default and the relaxation needs positive identification: a mis-identified engine can only keep
        false positives, never lose a catch.
    Without a sidecar (full_graph False) every row of the name is read."""
    units, unions = {}, {}
    for f in funcs:
        (unions if f.get("interfaceUnion") else units).setdefault(f["fn"], []).append(f)
    relaxed = keys_are_bodies and full_graph

    def callee_rows(name, caller):
        rows = units.get(name, [])
        if relaxed:
            if rows:
                return rows
            return [] if name in edges else unions.get(name, [])
        return rows if static_edge(caller, name) else rows + unions.get(name, [])

    viols = []
    # (1) Direct form: an unresolved call must surface as Unknown (or a disclosure field).
    for f in funcs:
        if f.get("unresolved") and "Unknown" not in (f.get("inferred") or []) \
                and not (f.get("invisible") or f.get("blind") or f.get("incomplete")):
            viols.append((f["fn"], "flagged `unresolved` but inferred lacks Unknown and carries no disclosure"))
    # (2) Propagation over the FULL callgraph: a CERTAIN f (incl. a pure fn absent from the report)
    #     must not reach an UNCERTAIN callee g.
    for fn, callees in edges.items():
        if any(uncertain(r) for r in units.get(fn, [])):
            continue  # f already honest about its uncertainty
        for callee in callees:
            if callee == fn:
                continue
            g = next((r for r in callee_rows(callee, fn) if uncertain(r)), None)
            if g is not None:
                why = "Unknown" if "Unknown" in (g.get("inferred") or []) else "disclosed-incomplete"
                tag = "pure (omitted from report)" if fn not in units else "reads certain"
                viols.append((fn, f"{tag} but calls `{callee}` which is {why}"))
                break
    return viols


def is_candor_scan(report):
    """True only for candor-scan, positively identified by its build id (`scan-<ver>`)."""
    c = report.get("candor") if isinstance(report, dict) else None
    return isinstance(c, dict) and str(c.get("version", "")).startswith("scan-")


def main(argv):
    total = 0
    for path in argv:
        try:
            d = json.load(open(path))
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {path}: cannot read report ({e})")
            total += 1
            continue
        funcs = d.get("functions", [])
        full_graph = True
        try:
            edges = json.load(open(callgraph_path(path)))
        except Exception:  # noqa: BLE001
            # No callgraph sidecar. The inline-`calls` fallback MISSES pure-fn callers — exactly the
            # dangerous case (a pure-looking fn reaching uncertainty). So this is a SILENT WEAKENING of the
            # check. In strict mode (CONFORMANCE_REQUIRE_ALL) that's a FAILURE, not a quiet degrade.
            if os.environ.get("CONFORMANCE_REQUIRE_ALL"):
                print(f"FAIL (strict) {path}: no callgraph sidecar — the honesty check cannot cover pure-fn "
                      f"callers without it (CONFORMANCE_REQUIRE_ALL set)")
                total += 1
                continue
            print(f"  (no callgraph sidecar for {path} — using inline `calls`; pure-fn callers NOT covered, "
                  f"the check is WEAKENED; set CONFORMANCE_REQUIRE_ALL=1 to make this a failure)")
            edges = {f["fn"]: (f.get("calls") or []) for f in funcs}
            full_graph = False
        viols = check(funcs, edges, full_graph, is_candor_scan(d))
        if viols:
            print(f"DISHONEST {path} — {len(viols)} violation(s) of the propagation invariant:")
            for fn, reason in viols[:50]:
                print(f"  ✗ {fn}: {reason}")
            if len(viols) > 50:
                print(f"  … and {len(viols) - 50} more")
            total += len(viols)
        else:
            print(f"honest  {path} — {len(edges)} fns ({len(funcs)} effectful), uncertainty propagates ✓")
    if total:
        print(f"\nHONESTY CHECK FAILED: {total} violation(s) — uncertainty was swallowed somewhere.")
        return 1
    print("\nhonesty check OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
