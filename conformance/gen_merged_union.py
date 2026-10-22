#!/usr/bin/env python3
"""PART 101 — A UNION MERGED INTO A REAL ENTRY AT WRITE TIME CARRIES THE UNION'S REASONS, AND BOTH ROUTES
PROPAGATE THEM ALIKE (SPEC §3.1 ⟨0.40⟩, the merged-entry paragraph; SOUNDNESS R1330, R1338, R1354).

ONLY candor-java MERGES. SPEC §3.1 ⟨0.40⟩ (R682) names it: for a member with a body that its subclasses or
implementors override — an interface DEFAULT, or a bodiless abstract member whose class declares a capability
— candor-java writes ONE entry under the member's hash holding the body's own effects AND the override union's.
candor-scan, candor-ts and candor-swift publish the union BESIDE the real entry instead (measured for this
part, `~/candor-handoff/specagent-0416/A-measure.txt`: a trait provided method / a class method / a protocol
extension default, each overridden with Fs, gives a real `Shape.name` entry carrying only the default's Env and
a separate `interfaceUnion` entry under the same hash). So the property this part pins has no case in them,
and the ENGINES declaration says so rather than skipping them.

THE SEAM, measured on the reference engine (the javaagent-0415 lane's ANALYSIS.md, Fable's REVIEW.md §4). The
merged entry takes the union's EFFECTS but none of its REASONS, and a merged entry is not a union entry, so
§3.1's "one entry whose `unknownWhy` is not direct-only" did not reach it. Three readings followed:

  * the producer's own gate projects a narrowed filter over the merged UNIT to a strict SUBSET — the override's
    `reflect` is in the unit's `inferred` and in no class set (`deny Unknown[reflect] lib.Shape.name` 0);
  * a chained consumer, finding `Unknown` with no reason, synthesises `dep:` and reads a false `unresolved`
    (R1330);
  * where the merge is BROAD, the hedge token IS written into the merged entry, and the report route hands it to
    an EXACT caller (`I.super.m()`) through `calls` while the scan route does not (R1338, scan 0 / report 1).

The clause resolves all three the same way: the merge-derived part of the merged entry's `Unknown` takes the
union rule — its reasons are the contributors' transitive reasons — and the scan route seeds its class
fixpoint with the merged entry's reasons BEFORE propagating, so both routes walk the same input. The cost is
named in the clause and pinned here as CONSEQUENCE cells: an exact caller of a merged entry that carries
`Unknown` of its own also reads the union's classes, on both routes, because one `hash` holds the default body
and the merge and `calls` cannot tell the two edges apart. That is a superset (NOTSILENT); its EFFECTS stay
exact, which the `*_fs` controls pin.

EXECUTED (`~/candor-handoff/specagent-0416/A-groundtruth.txt`): `app.Main.go(new RShape())` runs the override
(the reflective load and the file read); `ctl.Main.go(new PShape())` runs the default body and `plain`'s own
native call only; `appb.Main.go(new K1())` runs K1's file read.

EVERY CELL IS JUDGED ON BOTH ROUTES — `scan --policy` and `gate --report` over the report that very scan wrote
— and the two `--gate-json` documents must be byte-equal (§3.1 ⟨0.24⟩), as well as the exit matching the
EXPECTED value. A cell whose routes disagree is printed as such, so R1338 reads as a route split, not a value.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402

SPEC_CLAUSES = [
    ("§3.1 ⟨0.40⟩", "A function's report entry, including any interface union merged into it, is the policy subject on"),
    ("§3.1 ⟨0.40⟩", "A UNION MERGED INTO A REAL ENTRY AT WRITE TIME BRINGS ITS REASONS WITH IT"),
    ("§3.1 ⟨0.40⟩", "scan route MUST seed its class fixpoint with the merged entry's reasons"),
    ("§3.1 ⟨0.24⟩", "MUST produce a `--gate-json` document **byte-equal** to `scan --policy P`'s"),
]

# THE FAULT IS AT THE FIXTURE: with CANDOR_PROBE_FAULT set, RShape's override is rendered WITHOUT its reflective
# load, so the union contributes no `reflect` and every cell expecting one must go red.
FAULT = os.environ.get("CANDOR_PROBE_FAULT")
EXEC = os.environ.get("CANDOR_PART101_EXEC")   # ground-truth mode: each body prints what ran

REFLECT = 'Class.forName(System.getProperty("cn", "java.lang.String"));'


def _say(what):
    return ('System.out.println("%s"); ' % what) if EXEC else ""


def narrow_sources():
    refl = "" if FAULT else REFLECT + " "
    return {
        "lib/Shape.java": 'package lib;\npublic interface Shape {\n  default String name() { %sreturn System.getenv("X"); }\n}\n'
                          % _say("default"),
        "lib/H.java": "package lib;\npublic class H { static native int nat(); }\n",
        "lib/RShape.java": 'package lib;\npublic class RShape implements Shape {\n  public String name() {\n'
                           '    try { %s%sjava.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); }\n'
                           '    catch (Exception e) {}\n    return "r";\n  }\n}\n' % (_say("override"), refl),
        "lib/PShape.java": 'package lib;\npublic class PShape implements Shape {\n'
                           '  public String plain() { try { H.nat(); } catch (Throwable t) { %s} return Shape.super.name(); }\n}\n'
                           % _say("native-attempted"),
        "app/Main.java": 'package app;\npublic class Main {\n  public static String go(lib.Shape s) { return s.name(); }\n'
                         '  public static void main(String[] a) { go(new lib.RShape()); }\n}\n',
        "ctl/Main.java": 'package ctl;\npublic class Main {\n  public static String go(lib.PShape p) { return p.plain(); }\n'
                         '  public static void main(String[] a) { go(new lib.PShape()); }\n}\n',
    }


BROAD_N = 13   # above candor-java's bounded-CHA limit, so the merged union is the BROAD hedge (fx3-broad-merge-route)


def broad_sources():
    refl = "" if FAULT else REFLECT + " "
    src = {
        "p/I.java": 'package p;\npublic interface I { default String m() { %sreturn System.getenv("X"); } }\n'
                    % _say("default"),
        "p/Ex.java": 'package p;\npublic class Ex implements I {\n  public String m() { return "ex"; }\n'
                     '  public String call() { try { %s} catch (Exception e) {} return I.super.m(); }\n}\n' % refl,
        "appb/Main.java": 'package appb;\npublic class Main {\n  public static String go(p.I i) { return i.m(); }\n'
                          '  public static void main(String[] a) { go(new p.K1()); }\n}\n',
    }
    for k in range(1, BROAD_N + 1):
        src["p/K%d.java" % k] = ('package p;\npublic class K%d implements I { public String m() { try { %s'
                                 'java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/k%d")); } '
                                 'catch (Exception e) {} return "k%d"; } }\n' % (k, _say("K%d" % k), k, k))
    return src


# (cell, fixture, target package, fn, policy, expected exit, kind). Fixtures: n = narrow, b = broad.
# kind: DEFECT (a cell the clause decides), CONSEQUENCE (an exact caller of the merged entry: rule 3 makes the
# superset mandatory — the report route cannot tell the exact edge from a dispatch, so rule 2's seeding is the
# only reading under which the routes agree — and the cell pins it on BOTH routes, so a port that writes the
# reasons without seeding the scan route reads scan 0 / report 1 and fails here: the PShape.plain guard),
# CONTROL (unchanged by the clause). Every cell compares the two `--gate-json` documents as well as the exits,
# and a refusal (exit 2) fails every cell, since none expects 2.
CELLS = [
    ("n_merged_reflect", "n", "lib", "lib.Shape.name", "deny Unknown[reflect]", 1, "DEFECT"),
    ("n_merged_unres", "n", "lib", "lib.Shape.name", "deny Unknown[unresolved]", 0, "DEFECT"),
    ("n_merged_fs", "n", "lib", "lib.Shape.name", "deny Fs", 1, "CONTROL"),
    ("n_exact_reflect", "n", "lib", "lib.PShape.plain", "deny Unknown[reflect]", 1, "CONSEQUENCE"),
    ("n_exact_native", "n", "lib", "lib.PShape.plain", "deny Unknown[native]", 1, "CONTROL"),
    ("n_exact_fs", "n", "lib", "lib.PShape.plain", "deny Fs", 0, "CONTROL"),
    ("n_app_reflect", "n", "app", "app.Main.go", "deny Unknown[reflect]", 1, "CONTROL"),
    ("n_app_unres", "n", "app", "app.Main.go", "deny Unknown[unresolved]", 0, "DEFECT"),
    ("n_app_fs", "n", "app", "app.Main.go", "deny Fs", 1, "CONTROL"),
    ("n_ctl_reflect", "n", "ctl", "ctl.Main.go", "deny Unknown[reflect]", 1, "CONSEQUENCE"),
    ("n_ctl_native", "n", "ctl", "ctl.Main.go", "deny Unknown[native]", 1, "CONTROL"),
    ("n_ctl_fs", "n", "ctl", "ctl.Main.go", "deny Fs", 0, "CONTROL"),
    ("b_merged_dispatch", "b", "p", "p.I.m", "deny Unknown[dispatch]", 1, "CONTROL"),
    ("b_exact_dispatch", "b", "p", "p.Ex.call", "deny Unknown[dispatch]", 1, "CONSEQUENCE"),
    ("b_exact_reflect", "b", "p", "p.Ex.call", "deny Unknown[reflect]", 1, "CONTROL"),
    ("b_exact_fs", "b", "p", "p.Ex.call", "deny Fs", 0, "CONTROL"),
    ("b_app_dispatch", "b", "appb", "appb.Main.go", "deny Unknown[dispatch]", 1, "CONTROL"),
    ("b_app_unres", "b", "appb", "appb.Main.go", "deny Unknown[unresolved]", 0, "CONTROL"),
]
WHY = {
    "DEFECT": "the merged entry's merge-derived Unknown takes the union rule (§3.1 ⟨0.40⟩)",
    "CONSEQUENCE": "an exact caller of a merged entry reads the union's classes on BOTH routes — the superset the "
                   "clause names; a route split here is R1338's inequality",
    "CONTROL": "unchanged by the clause — if this is red the fixture or the chain is broken",
}

# Keyed by (cell, engine) like every generator's table (scripts/xfail-register-agree.py reads it as a literal).
XFAIL = {
    ("n_merged_reflect", "java"):
        ("R1354 — the merged entry `lib.Shape.name` carries RShape's Unknown in `inferred` and no reason for it: "
         "the scan route projects a strict SUBSET and the report route refuses the narrowed filter"),
    ("n_merged_unres", "java"):
        "R1354 — the reasonless merged Unknown projects to the `unresolved` catch-all (scan) or refuses (report)",
    ("n_app_unres", "java"):
        ("R1330 — the chained consumer synthesises `dep:` for the merged entry's reasonless Unknown and reads a "
         "false `unresolved` beside the true reflect"),
    ("n_exact_reflect", "java"):
        "R1354 — no reflect reason is on the merged entry, so neither route propagates it to the exact caller",
    ("n_ctl_reflect", "java"):
        "R1354 — the same, one chain hop further: the chained exact caller has nothing to inherit",
    ("b_exact_dispatch", "java"):
        ("R1338 — the BROAD merge writes its `dispatch:` hedge into the merged entry; the report route hands it to "
         "the exact caller through `calls`, the scan route does not"),
    ("b_exact_reflect", "java"):
        ("R1338 — the exits agree, but the report route's violation carries the BROAD merge's `dispatch` class "
         "and the scan route's does not, so the documents differ"),
}
# What each xfail expects wrong: "scan"/"report" (that route's exit, and so the documents), "doc" (the exits are
# right and only the documents differ), "both" (default: either exit, either way).
XFAIL_ROUTE = {"b_exact_dispatch": "scan", "b_exact_reflect": "doc"}


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def compile_tree(root, sources):
    src = os.path.join(root, "src")
    for rel, text in sources.items():
        _w(os.path.join(src, rel), text)
    cls = os.path.join(root, "cls")
    os.makedirs(cls, exist_ok=True)
    c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(os.path.join(src, r) for r in sources))
    if c.returncode != 0:
        raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
    return cls


def split(root, cls, pkgs):
    out = {}
    for p in pkgs:
        d = os.path.join(root, "d_" + p)
        shutil.copytree(os.path.join(cls, p), os.path.join(d, p), dirs_exist_ok=True)
        out[p] = d
    return out


def jar():
    j = os.environ.get("CANDOR_JAVA_JAR")
    if not j:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        j = max(cands, key=os.path.getmtime) if cands else None
    return j if j and os.path.exists(j) else None


def scan_report(j, target, out, deps):
    env = dict(os.environ)
    env.pop("CANDOR_POLICY", None)
    if deps:
        env["CANDOR_DEPS"] = " ".join(deps)
    else:
        env.pop("CANDOR_DEPS", None)
    r = gd.run(["java", "-jar", j, target, "--json", out], env=env)
    return r.returncode if os.path.exists(out) else None


def two_routes(j, target, deps, policy, work):
    """(scan rc, report rc, scan doc, report doc). The report route reads the report the scan route wrote."""
    env = dict(os.environ)
    env.pop("CANDOR_POLICY", None)
    if deps:
        env["CANDOR_DEPS"] = " ".join(deps)
    else:
        env.pop("CANDOR_DEPS", None)
    rep, ga, gb = (os.path.join(work, n) for n in ("r.json", "a.gate.json", "b.gate.json"))
    for p in (rep, ga, gb):
        if os.path.exists(p):
            os.remove(p)
    s = gd.run(["java", "-jar", j, target, "--json", rep, "--policy", policy, "--gate-json", ga], env=env).returncode
    g = gd.run(["java", "-jar", j, "gate", "--report", rep, "--policy", policy, "--gate-json", gb], env=env).returncode
    da = open(ga, "rb").read() if os.path.exists(ga) else None
    db = open(gb, "rb").read() if os.path.exists(gb) else None
    return s, g, da, db


def main():
    import tempfile
    print("=" * 100)
    print("MERGED UNION ENTRY §3.1 ⟨0.40⟩ — a union merged into a real entry at write time brings its reasons, and")
    print("both routes propagate them alike (candor-java: the only producer that merges)")
    print("  narrow: lib.Shape.name (default: Env) merged with RShape's override (reflect + Fs);")
    print("          PShape.plain = own native + exact Shape.super.name(); app dispatches s.name(); ctl calls plain")
    print("  broad : p.I.m (default: Env) merged with %d Fs overrides -> the bounded-CHA hedge; Ex.call = own" % BROAD_N)
    print("          reflect + exact I.super.m(); appb dispatches i.m()")
    print("  every cell: scan --policy AND gate --report over the report that scan wrote; exits AND documents equal")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the overrides are rendered WITHOUT their reflective load, so every")
        print("       cell expecting a `reflect` must go red.")
    j = jar()
    if not j or not shutil.which("javac"):
        print("  java   -> SKIP (no candor-java jar or no javac)")
        print("MERGED-UNION: no engine available — NOT a pass")
        return 2
    ws = tempfile.mkdtemp(prefix="candor-part101-")
    bad = stale = 0
    try:
        ncls = compile_tree(os.path.join(ws, "n"), narrow_sources())
        bcls = compile_tree(os.path.join(ws, "b"), broad_sources())
    except RuntimeError as e:
        print("  java   -> BROKEN: %s" % e)
        return 1
    nd = split(os.path.join(ws, "n"), ncls, ["lib", "app", "ctl"])
    bd = split(os.path.join(ws, "b"), bcls, ["p", "appb"])
    reports = {}
    for name, d in (("lib", nd["lib"]), ("p", bd["p"])):
        out = os.path.join(ws, name + ".report.json")
        if scan_report(j, d, out, []) is None:
            print("  java   -> BROKEN: the %s scan wrote no report" % name)
            return 1
        reports[name] = out
    targets = {"lib": (nd["lib"], []), "app": (nd["app"], [reports["lib"]]), "ctl": (nd["ctl"], [reports["lib"]]),
               "p": (bd["p"], []), "appb": (bd["appb"], [reports["p"]])}
    # The merge must actually happen, or every cell below measures an ordinary row. Read it off the report.
    import json
    for name, fn in (("lib", "lib.Shape.name"), ("p", "p.I.m")):
        rows = [f for f in json.load(open(reports[name])).get("functions") or [] if f.get("fn") == fn]
        real = [f for f in rows if not f.get("interfaceUnion")]
        # narrow: the default body has no Fs, so Fs on the real entry is the override union's; broad: the default has
        # no Unknown, so Unknown on the real entry is the merged bounded-CHA hedge.
        mark = "Fs" if name == "lib" else "Unknown"
        if not real or mark not in (real[0].get("inferred") or []):
            print("  java   -> BROKEN: %s carries no merged union (%s) — the fixture no longer exercises a "
                  "write-time merge, and no cell here is evidence" % (fn, rows))
            return 1
        print("  merged: %-15s inferred=%s unknownWhy=%s" % (fn, real[0].get("inferred"), real[0].get("unknownWhy")))
    for cell, _fx, tgt, fn, pol, want, kind in CELLS:
        work = os.path.join(ws, "cells", cell)
        os.makedirs(work, exist_ok=True)
        pp = os.path.join(work, "p.policy")
        with open(pp, "w") as f:
            f.write("%s %s\n" % (pol, fn))
        d, deps = targets[tgt]
        s, g, da, db = two_routes(j, d, deps, pp, work)
        problems = []
        if s != want:
            problems.append("scan")
        if g != want:
            problems.append("report")
        docs_equal = da is not None and da == db
        detail = "`%s %s` scan=%d report=%d want=%s%s" % (pol, fn, s, g, want,
                                                       "" if docs_equal else " — --gate-json documents DIFFER")
        if not docs_equal and "doc" not in problems:
            problems.append("doc")
        ok = not problems
        why = XFAIL.get((cell, "java"))
        if why:
            route = XFAIL_ROUTE.get(cell, "both")
            # A route-scoped xfail says WHICH route is wrong: the other one must already be right.
            other_wrong = ((route == "scan" and "report" in problems) or (route == "report" and "scan" in problems)
                           or (route == "doc" and ("scan" in problems or "report" in problems)))
            if ok:
                print("  XFAIL ARM PASSED  %-18s java   — expectation is STALE: %s" % (cell, why))
                stale += 1
            elif other_wrong:
                print("  FAIL  %-18s java   %s  [declared a %s-route xfail, but the other route is wrong too: %s]"
                      % (cell, detail, route, why))
                bad += 1
            else:
                print("  xfail %-18s java   %s  [%s]" % (cell, detail, why))
        elif ok:
            print("  OK    %-18s java   %s  (%s)" % (cell, detail, kind))
        else:
            print("  FAIL  %-18s java   %s  [%s: %s]" % (cell, detail, kind, WHY[kind]))
            bad += 1
    if os.environ.get("CANDOR_PART101_KEEP"):
        print("  workspace kept: %s" % ws)
    else:
        shutil.rmtree(ws, ignore_errors=True)
    if stale:
        print("MERGED-UNION: %d xfail cell(s) PASSED — retire them in the same commit as the engine fix." % stale)
    if bad:
        print("MERGED-UNION: %d cell(s) wrong — see SPEC §3.1 ⟨0.40⟩ (merged entry) and SOUNDNESS R1330/R1338/R1354" % bad)
    if not bad and not stale:
        print("MERGED-UNION: OK — every control holds and every open defect cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
