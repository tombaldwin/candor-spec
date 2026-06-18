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

Works on ANY engine's report (rust/java/ts/swift — one spec format). Exit 0 iff honest.
Usage:  python3 check_honesty.py <report.json> [<report2.json> ...]
        (the sibling <report>.callgraph.json is loaded automatically.)
"""
import json
import os
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


def check(funcs, edges):
    """funcs: list of report function objects (effectful/disclosed only).
    edges: {fn_name: [callee_name, ...]} from the callgraph (ALL functions). Returns [(fn, reason)]."""
    rep = {f["fn"]: f for f in funcs}
    viols = []
    # (1) Direct form: an unresolved call must surface as Unknown (or a disclosure field).
    for f in funcs:
        if f.get("unresolved") and "Unknown" not in (f.get("inferred") or []) \
                and not (f.get("invisible") or f.get("blind") or f.get("incomplete")):
            viols.append((f["fn"], "flagged `unresolved` but inferred lacks Unknown and carries no disclosure"))
    # (2) Propagation over the FULL callgraph: a CERTAIN f (incl. a pure fn absent from the report)
    #     must not reach an UNCERTAIN callee g.
    for fn, callees in edges.items():
        if uncertain(rep.get(fn)):
            continue  # f already honest about its uncertainty
        for callee in callees:
            g = rep.get(callee)  # absent ⇒ pure ⇒ certain (no violation)
            if g is not None and callee != fn and uncertain(g):
                why = "Unknown" if "Unknown" in (g.get("inferred") or []) else "disclosed-incomplete"
                tag = "pure (omitted from report)" if fn not in rep else "reads certain"
                viols.append((fn, f"{tag} but calls `{callee}` which is {why}"))
                break
    return viols


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
        viols = check(funcs, edges)
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
