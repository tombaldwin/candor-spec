#!/usr/bin/env python3
"""
P6 — SIDECAR MANIFEST FIDELITY, as a GENERATED property (SCAN-BOUNDARY-WORK-QUEUE.md §3).

    Removing information from a sidecar may only WIDEN a disclosure, never narrow it —
    and a producer's sidecar must SAY what it indexed, so that removal is detectable at all.

WHY THIS PROPERTY EXISTS, which is the useful part of the story
----------------------------------------------------------------
P2 and P3 degrade the chained DEP REPORT. Nothing degraded a SIDECAR, and a sidecar is not a dep report —
it is a second, differently-shaped input that no property varied. The ⟨0.26⟩ defect lived in that gap for
as long as the sidecar has existed: `hierarchy[t]` missing was read as "t has no supertypes" in all three
consumer engines, so a subtype question about a type NOBODY ANALYSED was answered NO. In the dispatch
frontier that silently removes a reacher from a disclosure — measured in candor-java and candor-ts as `[]`
where the control gives the dispatching function.

The sharpest form of that measurement, and the reason the repair had to be a FORMAT change rather than a
consumer patch: a PARTIAL sidecar was WORSE THAN NO SIDECAR AT ALL. With no sidecar the frontier falls
back to a documented simple-name match that over-lists (safe); with a sidecar missing one key it went
confidently silent. No consumer can patch around that on its own, because without a manifest it cannot
tell a producer's silence from its answer. Hence §2.2 ⟨0.26⟩: the KEY SET IS THE MANIFEST — a type WITH a
key was indexed and its array is complete; a type with NO key was never looked at.

THE TWO CONJUNCTS, and why each engine has the cells it has
------------------------------------------------------------
  A. CONSUMER MONOTONICITY (java, ts, rust — the three engines with a `callers --include-unknown` verb)

         frontier(full)  ⊆  frontier(full minus one key)  ⊆  frontier(no sidecar)

     Both bounds are load-bearing and they run in opposite directions. The LEFT says degrading the input
     may not ADD confidence — you cannot learn a type is unrelated by deleting what you knew about it.
     The RIGHT says a partial sidecar may not out-claim an absent one — that is the bound the defect
     broke. Every key present in the engine's own sidecar is removed in its own arm, so the property does
     not depend on guessing WHICH key matters.

     candor-swift has no `callers` verb, so this conjunct is NOT APPLICABLE there. That is a structural
     fact about the engine, not a waiver, and it is printed as such.

  B. PRODUCER MANIFEST CLOSURE (java, ts, swift — the three engines that WRITE a sidecar)

         { declaring type of u : u a unit in the engine's own callgraph }  ⊆  sidecar key set

     Self-referential on purpose: both sides are the SAME ENGINE'S OWN OUTPUT for the same scan, so there
     is no expected-value table and none may ever be added. A callgraph key is a unit whose body the
     engine walked, so its declaring type is by definition one the pass indexed — and under ⟨0.26⟩ an
     indexed type must carry a key. This is exactly the pre-rung shape: candor-ts's sidecar listed the 13
     implementers and omitted `Dispatcher` and `Sink`, both of which are declaring types in its own
     callgraph. Only callgraph KEYS count, never callee values: a callee may be an external type the
     engine never indexed, and demanding a key for it would be demanding a claim the engine cannot make.

     candor-scan writes no hierarchy sidecar, so this conjunct is NOT APPLICABLE to rust — which is also
     why rust's consumer arm matters: every hierarchy it walks was produced by another engine, so the
     producer's completeness is never its to assume.

Between them every engine carries at least one live conjunct, and the two that produce AND consume carry
both.

THE FIXTURES
--------------
Conjunct A runs on a HAND-WRITTEN report + callgraph + sidecar triple, in each engine's own file-naming
convention. That is deliberate and follows P3, which hand-writes its dep reports for the same reason:
this conjunct is about how a consumer READS a hierarchy, and driving it through a scanner would make the
result depend on whether that scanner happens to emit an unresolved dispatch for the fixture. The triple
is a TWO-LEVEL chain (Sub -> Mid -> Base) because a flat one cannot see the defect at all — the walk hits
the dispatch owner as an immediate supertype and returns YES before it ever reaches an unindexed type, so
pre-rung and post-rung code agree. This was learned by writing it flat first and watching it stay green
against a restored bug. The gap must be IN the path.

Conjunct B runs on a REAL SCAN of a small program with three shapes the manifest has to distinguish: a
type in a two-level chain, a type with no supertype at all, and a type that is only ever a supertype.

VACUITY (standing bar item 8) is computed from the engine's own output, never asserted. A conjunct-A cell
whose `full` arm produces an EMPTY frontier demands nothing of the degraded arms and is counted VACUOUS; a
conjunct-B cell whose callgraph has no dotted unit likewise. The run FAILS if an applicable conjunct has
no live cells anywhere, if a reference arm produced nothing while exiting 0 (the harness broken, which
must never read as engine behaviour), or if the sidecar the fixture depends on was never written.

USAGE
    python3 gen_sidecar_manifest.py                  # raw truth, exit non-zero on any violation
    python3 gen_sidecar_manifest.py --keep           # leave the scratch tree for inspection
    python3 gen_sidecar_manifest.py --baseline sidecar-manifest-baseline.json   # the ratchet (PART 30)
"""
# THE CONTRACT THIS PROPERTY ENFORCES, quoted so clause_check.py can prove SPEC.md still says it.
SPEC_CLAUSES = [
    ("§2.2", "THE KEY SET IS THE MANIFEST: an absent type is UNANSWERABLE, never \"has no supertypes\"."),
    ("§2.2", "A producer MUST emit a key for **every type it indexed**, carrying `[]` when that type has no supertypes"),
    ("§3.1", "unanswerable condition MUST NOT be scored as a failed one."),
]

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import gen_differential as gd

HERE = os.path.dirname(os.path.abspath(__file__))

# =====================================================================================================
# THE CONJUNCT-A TRIPLE. One report, one callgraph, one sidecar — written under each engine's own naming.
# `mod.Caller.run` is an Unknown-dispatch source on `mod.Base.handle`; `mod.Sub.handle` is a CONFIRMED
# reacher of the target. Whether the frontier discloses `mod.Caller.run` turns entirely on the subtype
# question "is mod.Sub a mod.Base?", which the sidecar answers through mod.Mid.
# =====================================================================================================
REPORT = {
    "candor": {"version": "p6-fixture", "toolchain": "n/a", "spec": "0.25"},
    "package": "app",
    "functions": [
        {"fn": "mod.Target.work", "inferred": ["Fs"], "direct": ["Fs"]},
        {"fn": "mod.Sub.handle", "inferred": ["Fs"], "calls": ["mod.Target.work"]},
        {"fn": "mod.Caller.run", "inferred": ["Unknown"], "unknownWhy": ["dispatch:mod.Base.handle"]},
    ],
}
CALLGRAPH = {"mod.Sub.handle": ["mod.Target.work"], "mod.Target.work": []}
SIDECAR = {"mod.Sub": ["mod.Mid"], "mod.Mid": ["mod.Base"], "mod.Base": []}
QUERY = "work"


def _write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


def _triple(d, kind, sidecar):
    """Write the triple into directory `d` under engine `kind`'s naming; return the locator to query."""
    if kind == "rust":
        pre = os.path.join(d, "r")
        _write(pre + ".app.scan.json", REPORT)
        _write(pre + ".app.scan.callgraph.json", CALLGRAPH)
        if sidecar is not None:
            _write(pre + ".app.hierarchy.json", sidecar)
        return pre
    # java and ts share the `<stem>.json` + `<stem>.callgraph.json` + `<stem>.hierarchy.json` layout.
    rep = os.path.join(d, "r.json")
    _write(rep, REPORT)
    _write(os.path.join(d, "r.callgraph.json"), CALLGRAPH)
    if sidecar is not None:
        _write(os.path.join(d, "r.hierarchy.json"), sidecar)
    return rep


def _frontier_cmd(kind, locator):
    if kind == "rust":
        binp = os.environ.get("CANDOR_SCAN_BIN")
        qbin = (os.path.join(os.path.dirname(binp), "candor-query") if binp
                else os.path.join(gd.CANDOR, "target", "debug", "candor-query"))
        if not os.path.exists(qbin):
            return None, "no candor-query at %s" % qbin
        return ([qbin, "callers", locator, QUERY, "1", "--include-unknown"], None), None
    if kind == "java":
        jar = os.environ.get("CANDOR_JAVA_JAR")
        if not jar:
            cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
            jar = max(cands, key=os.path.getmtime) if cands else None
        if not jar or not os.path.exists(jar):
            return None, "no candor-java jar"
        return (["java", "-jar", jar, "callers", QUERY, "--report", locator,
                 "--include-unknown", "--json"], None), None
    if kind == "ts":
        q = os.path.join(gd.CANDOR_TS, "query.mjs")
        if not shutil.which("node") or not os.path.exists(q):
            return None, "no node / query.mjs"
        return (["node", q, "callers", QUERY, "--report", locator, "--include-unknown"], None), None
    return None, "no frontier verb"


def frontier(kind, d, sidecar):
    """Run one arm. Returns (sorted fn list, note). `None` means the engine produced no parseable answer."""
    locator = _triple(d, kind, sidecar)
    got, err = _frontier_cmd(kind, locator)
    if got is None:
        return None, err
    cmd, _ = got
    r = gd.run(cmd, cwd=d)
    try:
        v = json.loads(r.stdout.decode().strip())
    except Exception:
        return None, "rc=%d %s" % (r.returncode, r.stderr.decode()[:160].replace("\n", " | "))
    poss = v.get("possibleViaUnknownDispatch")
    if poss is None:
        return None, "no possibleViaUnknownDispatch key (rc=%d)" % r.returncode
    return sorted(p["fn"] for p in poss), None


# =====================================================================================================
# CONJUNCT A — consumer monotonicity under per-key sidecar degradation.
# =====================================================================================================
def conjunct_a(kind, root):
    out = {"applicable": True, "cells": [], "note": None}
    base = os.path.join(root, "A_" + kind)

    full_d = os.path.join(base, "full")
    os.makedirs(full_d, exist_ok=True)
    full, err = frontier(kind, full_d, SIDECAR)
    if full is None:
        out["applicable"] = False
        out["note"] = err
        return out

    absent_d = os.path.join(base, "absent")
    os.makedirs(absent_d, exist_ok=True)
    absent, err = frontier(kind, absent_d, None)
    if absent is None:
        # A REFERENCE arm that produces nothing is the oracle missing, not a finding about the engine.
        out["applicable"] = False
        out["note"] = "reference arm `absent` produced nothing: %s" % err
        return out

    for key in sorted(SIDECAR):
        degraded = {k: v for k, v in SIDECAR.items() if k != key}
        d = os.path.join(base, "minus_" + key.replace(".", "_"))
        os.makedirs(d, exist_ok=True)
        got, err = frontier(kind, d, degraded)
        cell = {"arm": "minus:" + key, "full": full, "degraded": got, "absent": absent}
        if got is None:
            cell["verdict"] = "HARNESS"
            cell["note"] = err
        elif not full:
            # VACUOUS, computed not asserted: an empty `full` frontier demands nothing of any degraded arm.
            cell["verdict"] = "VACUOUS"
        elif not set(full) <= set(got):
            cell["verdict"] = "FAIL"
            cell["why"] = ("removing one key LOST a disclosure the full sidecar made — degrading an input "
                           "bought confidence: %s not in %s" % (sorted(set(full) - set(got)), got))
        elif not set(got) <= set(absent):
            cell["verdict"] = "FAIL"
            cell["why"] = ("a PARTIAL sidecar out-claimed an ABSENT one: %s not in the no-sidecar arm %s"
                           % (sorted(set(got) - set(absent)), absent))
        else:
            cell["verdict"] = "OK"
        out["cells"].append(cell)
    return out


# =====================================================================================================
# CONJUNCT B — producer manifest closure. Both sides are the engine's own output for one scan.
# =====================================================================================================
JAVA_SRC = """package app;
import java.io.*;
interface Base { void op(); }
interface Mid extends Base {}
class Impl implements Mid { public void op() { try { new FileInputStream("/etc/hosts").close(); } catch (Exception e) {} } }
class Loner { void idle() { System.out.print(""); } }
"""

TS_SRC = """import * as fs from 'fs';
interface Base { op(): void; }
interface Mid extends Base {}
class Impl implements Mid { op() { fs.readFileSync('/etc/hosts'); } }
class Loner { idle() { } }
"""

SWIFT_SRC = """import Foundation
protocol Base { func op() }
protocol Mid: Base {}
struct Impl: Mid { func op() { _ = try? String(contentsOfFile: "/etc/hosts") } }
struct Loner { func idle() {} }
"""


def _declaring_types(callgraph, sep):
    """Declaring types of the units the engine WALKED — callgraph KEYS only, never callee values.

    A unit whose MEMBER component is BRACKETED (`<module>`, `<clinit>`, `<lazy>`, `<init>`) is synthesized
    rather than declared, and the top-level ones are keyed by MODULE, not by type: candor-ts emits
    `Cases.<module>` for the ⟨0.14⟩ top-level initializer unit, whose prefix `Cases` is the FILE. Demanding
    a sidecar key for it would be demanding a key for a module — the same modules-counted-as-types error
    that once turned a 24.3% measurement into a 94.3% one. Found by reading the callgraph rather than
    assuming, after this conjunct flagged `Cases` on a conforming engine.

    Everything unbracketed is a genuine member of a genuine type, which is what keeps the conjunct sharp:
    the pre-rung shape this property exists to catch (candor-ts omitting `Dispatcher` and `Sink`) is named
    by `Dispatcher.run` and `Sink.touch`, both unbracketed and both still demanded.
    """
    out = set()
    for unit in callgraph:
        if sep not in unit:
            continue
        owner, member = unit.rsplit(sep, 1)
        if member.startswith("<") and member.endswith(">"):
            continue
        out.add(owner)
    return out


def _produce_java(d):
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None
    if not jar or not os.path.exists(jar):
        return None, "no candor-java jar"
    if not shutil.which("javac"):
        return None, "no javac on PATH"
    src = os.path.join(d, "src", "app")
    os.makedirs(src, exist_ok=True)
    with open(os.path.join(src, "App.java"), "w") as f:
        f.write(JAVA_SRC)
    cls = os.path.join(d, "classes")
    c = gd.run(["javac", "-nowarn", "-d", cls, os.path.join(src, "App.java")])
    if c.returncode != 0:
        return None, "javac failed: %s" % c.stderr.decode()[:200]
    out = os.path.join(d, "out.json")
    gd.run(["java", "-jar", jar, cls, "--json", out])
    return (out[:-5] + ".hierarchy.json", out[:-5] + ".callgraph.json", "."), None


def _produce_ts(d):
    scan = os.path.join(gd.CANDOR_TS, "scan.mjs")
    if not shutil.which("node") or not os.path.exists(scan):
        return None, "no node / scan.mjs"
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "Cases.ts"), "w") as f:
        f.write(TS_SRC)
    with open(os.path.join(d, "package.json"), "w") as f:
        json.dump({"name": "p6", "version": "0.0.0"}, f)
    out = os.path.join(d, "out.json")
    gd.run(["node", scan, d, "--out", out])
    return (out + ".hierarchy.json", out + ".callgraph.json", "."), None


def _produce_swift(d):
    binp = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not shutil.which("swift") or not os.path.exists(binp):
        return None, "no swift toolchain / candor-swift binary"
    src = os.path.join(d, "Sources", "App")
    os.makedirs(src, exist_ok=True)
    with open(os.path.join(d, "Package.swift"), "w") as f:
        f.write('// swift-tools-version: 6.0\nimport PackageDescription\n'
                'let package = Package(name: "App", targets: [.executableTarget(name: "App")])\n')
    with open(os.path.join(src, "main.swift"), "w") as f:
        f.write(SWIFT_SRC)
    out = os.path.join(d, "out")
    gd.run([binp, d, "--out", out], cwd=d)
    return (out + ".App.Swift.hierarchy.json", out + ".App.Swift.callgraph.json", "."), None


PRODUCERS = {"java": _produce_java, "ts": _produce_ts, "swift": _produce_swift}


def conjunct_b(kind, root):
    out = {"applicable": True, "cells": [], "note": None}
    mk = PRODUCERS.get(kind)
    if mk is None:
        out["applicable"] = False
        out["note"] = "writes no hierarchy sidecar"
        return out
    d = os.path.join(root, "B_" + kind)
    os.makedirs(d, exist_ok=True)
    paths, err = mk(d)
    if paths is None:
        out["applicable"] = False
        out["note"] = err
        return out
    hpath, cpath, sep = paths
    if not os.path.exists(hpath) or not os.path.exists(cpath):
        out["applicable"] = False
        out["note"] = "scan wrote no %s" % ("hierarchy sidecar" if not os.path.exists(hpath) else "callgraph")
        return out
    hier = json.load(open(hpath))
    cg = json.load(open(cpath))
    types = _declaring_types(cg, sep)
    keys = {k for k in hier if not k.startswith("@")}   # `@`-prefixed keys are metadata, not types
    missing = sorted(types - keys)
    cell = {"arm": "closure", "declaringTypes": sorted(types), "keys": sorted(keys)}
    if not types:
        cell["verdict"] = "VACUOUS"      # computed: no dotted callgraph unit demands anything
    elif missing:
        cell["verdict"] = "FAIL"
        cell["why"] = ("the engine WALKED these types' bodies but its sidecar gives them no key, so a "
                       "consumer cannot tell them from types it never analysed: %s" % missing)
    else:
        cell["verdict"] = "OK"
    out["cells"].append(cell)
    return out


# =====================================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--baseline")
    args = ap.parse_args()

    root = tempfile.mkdtemp(prefix="candor-p6-")
    fails, live_a, live_b = [], 0, 0
    report = {}
    try:
        for kind in ("rust", "java", "ts", "swift"):
            a = conjunct_a(kind, root)
            b = conjunct_b(kind, root)
            report[kind] = {"A": a, "B": b}
            for tag, res in (("A", a), ("B", b)):
                if not res["applicable"]:
                    print("  %-5s conjunct %s  NOT APPLICABLE — %s" % (kind, tag, res["note"]))
                    continue
                for c in res["cells"]:
                    v = c["verdict"]
                    if v == "OK":
                        if tag == "A":
                            live_a += 1
                        else:
                            live_b += 1
                    elif v == "FAIL":
                        fails.append((kind, tag, c))
                    elif v == "HARNESS":
                        fails.append((kind, tag, dict(c, why="HARNESS: " + c.get("note", ""))))
                ok = sum(1 for c in res["cells"] if c["verdict"] == "OK")
                vac = sum(1 for c in res["cells"] if c["verdict"] == "VACUOUS")
                print("  %-5s conjunct %s  %d live, %d vacuous, %d cells" % (kind, tag, ok, vac, len(res["cells"])))

        # VACUITY FLOOR. An applicable conjunct with no live cell anywhere means the property proved
        # nothing, and a property that proves nothing must never print as a pass.
        if live_a == 0:
            fails.append(("*", "A", {"why": "conjunct A produced NO live cell on any engine — the "
                                            "frontier fixture stopped exercising the subtype test"}))
        if live_b == 0:
            fails.append(("*", "B", {"why": "conjunct B produced NO live cell on any engine — no engine's "
                                            "scan yielded a dotted callgraph unit"}))

        waived = set()
        if args.baseline:
            if not os.path.exists(args.baseline):
                print("FAIL: baseline %s is missing — an absent baseline must never read as "
                      "'nothing is waived'" % args.baseline)
                return 2
            bl = json.load(open(args.baseline))
            waived = {(w["engine"], w["conjunct"], w["arm"]) for w in bl.get("waivers", [])}

        unwaived, used = [], set()
        for kind, tag, c in fails:
            key = (kind, tag, c.get("arm", "*"))
            if key in waived:
                used.add(key)
                print("  WAIVED %s/%s %s" % (kind, tag, c.get("arm", "*")))
            else:
                unwaived.append((kind, tag, c))

        # BOTH-WAYS RATCHET: a waiver that no longer fires is stale and FAILS, so the baseline cannot
        # quietly outlive the defect it documents.
        stale = sorted(waived - used)
        for s in stale:
            print("FAIL: STALE WAIVER %s — the cell it covers now passes; delete it" % (s,))

        for kind, tag, c in unwaived:
            print("FAIL: %s conjunct %s [%s] — %s" % (kind, tag, c.get("arm", "*"), c.get("why", "")))
            if "full" in c:
                print("        full=%s degraded=%s absent=%s" % (c["full"], c["degraded"], c["absent"]))

        if unwaived or stale:
            return 1
        print("  P6 OK — %d live consumer cells, %d live producer cells" % (live_a, live_b))
        return 0
    finally:
        if args.keep:
            print("  scratch kept at %s" % root)
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
