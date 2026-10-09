#!/usr/bin/env python3
"""
PART 98 — ROUTE EQUALITY OVER THE PROJECTION: `scan --policy` == `gate --report` on the report that scan
wrote, for class-scoped, layer-scoped and inherited-`Unknown` rules (SPEC §3.1 ⟨0.24⟩, ⟨0.40⟩ R682)

WHAT IT CHECKS
--------------
SPEC §3.1: for any report a scan produced, `gate --report <it> --policy P` MUST produce a `--gate-json`
document BYTE-EQUAL to `scan --policy P`'s (over the evaluated projection), and ⟨0.40⟩: "the entries it
gates are the entries it writes". Per engine, one idiomatic source fixture holding

    repo.load        a direct Fs
    app.entry        Fs, INHERITED over a call (direct carries no Fs)
    app.hole         a direct `Unknown` of class `indirect` (a call through a function value)
    app.viaHole      the same `Unknown` INHERITED (class reachable only over `calls`)
    app.dynHole      a direct `Unknown` of class `dispatch` (a protocol/trait/interface member, no body)
    app.viaDyn       the same `Unknown` INHERITED
    app.pureFn       nothing (absent from `functions`, the ⟨0.21⟩ purity claim)
  (+ java: a reflective `hole` of class `reflect` and a `Runnable` callback pair)

is scanned once per policy with `--policy P --gate-json A --out X`, then `gate --report X --policy P
--gate-json B` is run over the report THAT scan wrote. A == B byte-for-byte, the exit codes are equal, and
no policy in the matrix is refused (exit 2) — every datum the class fixpoint needs is on a scan-written
report (§3.1: "an inherited `Unknown` always has its callee in `calls`").

WHAT THIS REACHES THAT PART 97 DOES NOT. PART 97 feeds hand-written reports and so never asks whether a
REPORT an engine wrote carries what the engine's own scan gated on. Here the scan route projects from its
in-memory analysis and the report route from the written report's `inferred`/`unknownWhy`/`calls`: a
`calls` edge the writer drops, a class the writer does not serialise, a merged entry the scan route did
not gate (R682), or a scope matched on a different name on the two routes (R1028) all break the equality.

WHAT IT CANNOT SEE, measured rather than assumed: a fault in the EVALUATOR the two routes SHARE. All four
engines call one policy evaluator from both routes (rust `candor_classify::gate::gate`, java
`Policy.gate`, ts `evaluatePolicy`, swift `evaluateGate`); a one-line fault planted there (ts, `pure`
counting `Unknown`) moved BOTH routes to exit 1 and left the documents byte-equal. That fault is PART
97's to catch, and it does. The two parts are complementary, not redundant.

VACUITY FLOORS (failing, not benign): per engine, at least one policy must exit 1 and one exit 0; at least
one CLASS-SCOPED rule must fire on an entry whose report carries no DIRECT `Unknown` (so the transitive
class fixpoint ran on the report route — else the part never exercised the projection it is for); and at
least one class-scoped rule must reject strictly fewer functions than bare `Unknown` (the filter
discriminates).

CONTROLS, run every time:
  document     the report route's own document with one violation deleted must read NOT byte-equal.
  report-side  the scan's report with `calls` stripped from the inherited-`Unknown` entries, re-gated:
               the class-scoped rule that fired by inheritance must no longer agree (refused or
               different) — the part can see a report that does not carry what the scan gated on.

USAGE
    python3 gen_route_equality.py [--keep]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_rung024 as G                      # noqa: E402  engine presence/paths — one copy, not a sixteenth

SPEC_CLAUSES = [
    ("§3.1 ⟨0.24⟩", "MUST produce a `--gate-json` document **byte-equal** to `scan --policy P`'s"),
    ("§3.1 ⟨0.40⟩", "**A function's report entry, including any interface union merged into it, is the policy subject on BOTH routes**"),
    ("§3.1 ⟨0.40⟩", "the entries it gates are the entries it writes."),
    ("§3.1 ⟨0.24⟩", "an inherited `Unknown` always has its callee in `calls`"),
    ("§6.2", "The reason class **propagates transitively** along the"),
]

POLICIES = [
    "deny Fs", "deny Fs app", "deny Fs repo", "deny Net", "pure", "pure app",
    "deny Exec Unknown", "deny Exec Unknown[*]", "deny Exec Unknown[dynamic]",
    "deny Exec Unknown[reflect]", "deny Exec Unknown[dispatch]", "deny Exec Unknown[indirect]",
    "deny Exec Unknown[native]", "deny Exec Unknown[unresolved]", "deny Exec Unknown[setup]",
    "deny Fs Unknown[dispatch] app", "deny Exec Unknown[indirect,reflect] app",
]
CLASS_SCOPED = [p for p in POLICIES if "Unknown[" in p and "[*]" not in p and "[dynamic]" not in p]

RS_SRC = """pub mod repo { pub fn load() { let _ = std::fs::read("/x"); } }
pub mod app {
    pub trait Plugin { fn run(&self); }
    pub fn entry() { crate::repo::load(); }
    pub fn hole(f: fn()) { f(); }
    pub fn via_hole(f: fn()) { hole(f); }
    pub fn dyn_hole(p: &dyn Plugin) { p.run(); }
    pub fn via_dyn(p: &dyn Plugin) { dyn_hole(p); }
    pub fn pure_fn() -> i32 { 1 }
}
"""
JV_REPO = """package q.repo;
public class R { public static void load() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); } }
"""
JV_APP = """package q.app;
public class A {
    public interface Plugin { void run(); }
    public static void entry() throws Exception { q.repo.R.load(); }
    public static void hole() throws Exception { Class.forName(System.getProperty("x")).getMethod("run").invoke(null); }
    public static void viaHole() throws Exception { hole(); }
    public static void cb(Runnable r) { r.run(); }
    public static void viaCb(Runnable r) { cb(r); }
    public static void dynHole(Plugin p) { p.run(); }
    public static void viaDyn(Plugin p) { dynHole(p); }
    public static int pureFn() { return 1; }
}
"""
TS_REPO = 'import * as fsm from "node:fs";\nexport function load(): void { fsm.readFileSync("/x"); }\n'
TS_APP = """import { load } from "../repo/index.js";
export interface Plugin { run(): void; }
export function entry(): void { load(); }
export function hole(f: () => void): void { f(); }
export function viaHole(f: () => void): void { hole(f); }
export function dynHole(p: Plugin): void { p.run(); }
export function viaDyn(p: Plugin): void { dynHole(p); }
export function pureFn(): number { return 1; }
"""
SW_SRC = """import Foundation
protocol Plugin { func run() }
enum repo { static func load() { _ = FileManager.default.contents(atPath: "/x") } }
enum app {
    static func entry() { repo.load() }
    static func hole(_ f: () -> Void) { f() }
    static func viaHole(_ f: () -> Void) { hole(f) }
    static func dynHole(_ p: Plugin) { p.run() }
    static func viaDyn(_ p: Plugin) { dynHole(p) }
    static func pureFn() -> Int { 1 }
}
"""


def run(cmd, cwd=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY")}
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(text)


def build_fixture(ws, eng):
    """Returns (scan target, report-locator for a given out stem fn) or (None, why)."""
    d = os.path.join(ws, eng)
    if eng == "rust":
        write(os.path.join(d, "Cargo.toml"), '[package]\nname = "p98"\nversion = "0.0.0"\nedition = "2021"\n')
        write(os.path.join(d, "src", "lib.rs"), RS_SRC)
        return d, None
    if eng == "java":
        write(os.path.join(d, "src", "q", "repo", "R.java"), JV_REPO)
        write(os.path.join(d, "src", "q", "app", "A.java"), JV_APP)
        out = os.path.join(d, "classes")
        r = run(["javac", "-d", out, os.path.join(d, "src", "q", "repo", "R.java"),
                 os.path.join(d, "src", "q", "app", "A.java")])
        return (out, None) if r.returncode == 0 else (None, "javac failed: " + r.stderr.decode()[:200])
    if eng == "ts":
        write(os.path.join(d, "src", "repo", "index.ts"), TS_REPO)
        write(os.path.join(d, "src", "app", "index.ts"), TS_APP)
        return os.path.join(d, "src"), None
    write(os.path.join(d, "src", "a.swift"), SW_SRC)
    return os.path.join(d, "src"), None


def scan(eng, target, out, policy, gate_json):
    """`scan --policy P --gate-json A`, writing its report under `out`. Returns (rc, report locator|None)."""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if eng == "rust":
        r = run([G.rust_scan(), target, "--out", out, "--policy", policy, "--gate-json", gate_json])
        loc = out
    elif eng == "java":
        loc = out + ".json"
        r = run(["java", "-jar", G.java_jar(), target, "--json", loc, "--policy", policy, "--gate-json", gate_json])
    elif eng == "ts":
        r = run(["node", os.path.join(G.ts_root(), "scan.mjs"), target, "--out", out, "--policy", policy,
                 "--gate-json", gate_json])
        loc = out
    else:
        r = run([G.swift_bin(), target, "--out", out, "--policy", policy, "--gate-json", gate_json])
        loc = out
    d, stem = os.path.dirname(out), os.path.basename(out)
    wrote = any(f.startswith(stem + ".") and f.endswith(".json") for f in os.listdir(d))
    return r.returncode, (loc if wrote else None)


def gate(eng, loc, policy, gate_json):
    if eng == "rust":
        cmd = [G.rust_query(), "gate", "--report", loc, "--policy", policy]
    elif eng == "java":
        cmd = ["java", "-jar", G.java_jar(), "gate", "--report", loc, "--policy", policy]
    elif eng == "ts":
        cmd = ["node", os.path.join(G.ts_root(), "query.mjs"), "gate", "--report", loc, "--policy", policy]
    else:
        cmd = [G.swift_bin(), "gate", "--report", loc, "--policy", policy]
    return run(cmd + ["--gate-json", gate_json]).returncode


def report_files(loc):
    """The main report JSON file(s) a locator names (not sidecars)."""
    if loc.endswith(".json"):
        return [loc]
    d, stem = os.path.dirname(loc), os.path.basename(loc)
    side = (".callgraph.json", ".hierarchy.json", ".locs.json")
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.startswith(stem + ".") and f.endswith(".json") and not f.endswith(side)]


def entries(loc):
    out = {}
    for p in report_files(loc):
        for f in json.load(open(p)).get("functions", []):
            out[f["fn"]] = f
    return out


def fns(doc):
    return [v.get("fn") for v in (doc or {}).get("violations", [])]


def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    # probe_check.py's fault: the FIRST firing report-route document loses one violation before the
    # comparison — the report route corrupted in the direction this property forbids.
    fault = bool(os.environ.get("CANDOR_PROBE_FAULT"))
    ws = tempfile.mkdtemp(prefix="candor-p98-")
    rc_all = 0
    wrong = 0
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in G.ENGINES if G.installed(e) and not G.alive(e)]
        print(f"  engines present: {', '.join(engines) or '(none)'}; {len(POLICIES)} policies per engine")
        if broken:
            print(f"  FAIL: installed but not responding: {', '.join(broken)} — HARNESS/INSTALL, not candor")
            rc_all = 1
        if not engines:
            print("  FAIL: no engine present"); return 1
        ctl_done = False
        for eng in engines:
            target, why = build_fixture(ws, eng)
            if target is None:
                print(f"  {eng:6s} ERROR  HARNESS — {why}"); rc_all = 1; continue
            bad, codes, inherited_hit, discriminates = [], {}, [], False
            res = {}
            for i, text in enumerate(POLICIES):
                pf = os.path.join(ws, f"{eng}.pol{i}")
                write(pf, text + "\n")
                a = os.path.join(ws, f"{eng}.{i}.scan.gate.json")
                b = os.path.join(ws, f"{eng}.{i}.report.gate.json")
                out = os.path.join(ws, f"{eng}-out{i}", "r")
                rc_s, loc = scan(eng, target, out, pf, a)
                if loc is None or not os.path.exists(a):
                    bad.append(f"[{text}] the scan wrote no report or no --gate-json (exit {rc_s}) — HARNESS/ENGINE INVOCATION")
                    continue
                rc_g = gate(eng, loc, pf, b)
                if not os.path.exists(b):
                    bad.append(f"[{text}] gate --report wrote no --gate-json (exit {rc_g})"); continue
                if fault and rc_g == 1:
                    dd = json.load(open(b))
                    if dd.get("violations"):
                        print(f"  PROBE: CANDOR_PROBE_FAULT — deleting one violation from {eng}'s report-route `{text}` document")
                        dd["violations"] = dd["violations"][1:]
                        write(b, json.dumps(dd, indent=1))
                        fault = False
                ab, bb = open(a, "rb").read(), open(b, "rb").read()
                if ab != bb:
                    bad.append(f"[{text}] NOT byte-equal (scan exit {rc_s} {sorted(fns(json.loads(ab)))}, "
                               f"report exit {rc_g} {sorted(fns(json.loads(bb)))})")
                if rc_s != rc_g:
                    bad.append(f"[{text}] exit {rc_s} (scan) vs {rc_g} (gate --report)")
                if 2 in (rc_s, rc_g):
                    bad.append(f"[{text}] refused/errored (scan {rc_s}, report {rc_g}) — nothing in this matrix is unanswerable on a scan-written report")
                codes[text] = rc_g
                ents = entries(loc)
                res[text] = (loc, pf, json.loads(bb), ents)
                if text in CLASS_SCOPED:
                    for f in fns(json.loads(bb)):
                        e = ents.get(f, {})
                        if "Unknown" not in (e.get("direct") or []) and "Unknown" in (e.get("inferred") or []):
                            inherited_hit.append((text, f))
            # floors
            if 1 not in codes.values() or 0 not in codes.values():
                bad.append(f"VACUOUS: exits seen {sorted(set(codes.values()))} — need at least one 1 and one 0")
            if not inherited_hit:
                bad.append("VACUOUS: no class-scoped rule fired on an INHERITED Unknown — the report route's "
                           "transitive class fixpoint was never exercised")
            bare = set(fns(res.get("deny Exec Unknown", (None, None, {}, {}))[2]))
            for t in CLASS_SCOPED:
                if t in res and set(fns(res[t][2])) < bare:
                    discriminates = True
            if not discriminates:
                bad.append("VACUOUS: no class-scoped rule rejected strictly fewer functions than bare Unknown")
            print(f"  {eng:6s} " + (f"OK  {len(POLICIES)} policies byte-equal; exits {sorted(set(codes.values()))}; "
                                    f"{len(inherited_hit)} class-scoped hit(s) on an inherited Unknown, e.g. "
                                    f"{inherited_hit[0][1]} under `{inherited_hit[0][0]}`" if not bad else "DIVERGE"))
            for x in bad:
                print(f"    {eng:6s} {x}")
            rc_all |= 1 if bad else 0
            wrong += len(bad)

            # ---- controls, on the first engine with a usable inherited hit -------------------------
            if not ctl_done and inherited_hit and not bad:
                ctl_done = True
                t, f_inh = inherited_hit[0]
                loc, pf, doc, ents = res[t]
                cbad = []
                # document seed
                b = os.path.join(ws, f"{eng}.ctl.doc.json")
                d2 = dict(doc); d2["violations"] = doc["violations"][1:]
                write(b, json.dumps(d2))
                i = POLICIES.index(t)
                if open(os.path.join(ws, f"{eng}.{i}.scan.gate.json"), "rb").read() == open(b, "rb").read():
                    cbad.append("document seed: a deleted violation still read byte-equal")
                # report-side seed: strip `calls` from every inherited-Unknown entry, re-gate the SAME policy
                for p in report_files(loc):
                    j = json.load(open(p))
                    for e in j.get("functions", []):
                        if "Unknown" in (e.get("inferred") or []) and "Unknown" not in (e.get("direct") or []):
                            e.pop("calls", None)
                    write(p, json.dumps(j, indent=1))
                # The §2.2 callgraph sidecar is LEFT in place: §3.1 forbids the report route to back-fill
                # from it, so a seed that still reads byte-equal would mean the route read the sidecar.
                c =os.path.join(ws, f"{eng}.ctl.report.json")
                rc_c = gate(eng, loc, pf, c)
                same = os.path.exists(c) and open(c, "rb").read() == open(os.path.join(ws, f"{eng}.{i}.scan.gate.json"), "rb").read()
                if same:
                    cbad.append(f"report-side seed: `calls` stripped from inherited entries and `{t}` still read byte-equal (exit {rc_c})")
                if cbad:
                    for x in cbad:
                        print(f"  CONTROL FAIL ({eng}): {x}")
                    rc_all = 1
                    wrong += len(cbad)
                else:
                    print(f"  controls ({eng}): a deleted violation reads NOT byte-equal; stripping `calls` from the "
                          f"inherited entries moves `{t}` (report route exit {rc_c}) — the part sees a report "
                          f"that does not carry what the scan gated on")
        if not ctl_done:
            print("  CONTROL FAIL: no engine produced a usable inherited hit, so the controls never ran"); rc_all = 1
            wrong += 1
        print(f"ROUTE EQUALITY: OK — {len(engines)} engine(s), {len(POLICIES)} policies each, byte-equal"
              if not rc_all else f"ROUTE EQUALITY: {max(wrong, 1)} cell(s) wrong")
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
