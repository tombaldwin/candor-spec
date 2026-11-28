#!/usr/bin/env python3
"""PARTs 111–114 — COMPILER-TYPED PRODUCERS, SPEC §2.3 ⟨0.45⟩ DRAFT (S-A, S-D, S-F, S-G).

THE RUNG IS A DRAFT AND NO ENGINE IMPLEMENTS IT. Two kinds of cell, and the difference is the point:

  SCORED   — what every engine must already do under the draft, measured today. Reader tolerance of the new keys,
             the ⟨0.21⟩ fail-closed verdict over an `untyped` entry, the absence of `typedBy`/`usr` on a syntactic
             producer, and a scan that executes nothing from the tree. A FAIL here is a finding.
  PENDING  — a producer obligation no engine has ported. It runs, its result is printed, and it does not fail the
             part. A PENDING CELL THAT PASSES IS A FAILURE, exactly as a passing xfail is in every other generator:
             the engine that lands its port reddens this part and retires its own line in PENDING below.

WHY `PENDING` AND NOT `XFAIL`. Every `XFAIL` table in this directory names a SOUNDNESS row, and
scripts/xfail-register-agree.py requires that row to exist, to be open and to mention the engine (R475, R647). A
DRAFT clause has no row: it is not a defect in a shipped contract. This lane files no rows, so the expectations
cite the DRAFT clause instead, under a different name, so that the register gate is not asked a question it cannot
answer. When the coordinator files a row for a pending cell (candor-swift's `g_sw_target` is a real violation of
the invariant, measured below), the entry moves to `XFAIL` with the row id.

  PART 111  S-A `typedBy`
    a_tol     H, four-way: one hand-written report with a Net row, and the same report plus a full `typedBy`
              (with an unknown future member). `gate --report deny Net` exits 1 on both, same violations.
    a_absent  S, rust/java/swift: the engine's own report of a three-function fixture carries no `typedBy` — these
              producers type syntactically or read bytecode, and the clause forbids the key over answers no typer
              gave.
    a_emit    S, ts, PENDING: candor-ts asks the TypeScript checker, so the draft binds it: its report must carry
              `typedBy` with every required member.
  PART 112  S-D `usr`
    d_tol     H, four-way: the Net report with `usr` on the row and `typedBy.identity`; same verdict as without.
    d_absent  S, rust/java/swift: no row of the engine's own report carries `usr`.
  PART 113  S-F `untyped`
    f_ctl     H, four-way CONTROL: a report with no rows and no `unanalyzed` — `deny Net` exits 0.
    f_untyped H, four-way: the same report plus `unanalyzed: [{path, reason: "untyped:module-refused"}]` — exit 2,
              `incomplete: true`, the entry echoed in the verdict with its reason byte-for-byte.
    f_viol    H, four-way: plus a Net row — exit 1 (a certain violation dominates, §3.3 ⟨0.24⟩).
  PART 114  S-G no execution
    g_rs_buildrs  S, rust: a crate whose build.rs writes a sentinel. candor-scan over it: no sentinel.
                  CONTROL g_rs_live: `cargo build` over a copy writes the sentinel, so the trap is live.
    g_sw_whole    S, swift: a package whose `Package.swift` and `Package@swift-5.9.swift` both sleep SLEEP seconds.
                  A whole-repo candor-swift scan is not slower than the same scan of the same package without the
                  sleep (timing is the observable because SwiftPM's macOS manifest sandbox blocks a sentinel write).
    g_sw_target   S, swift, PENDING: the same with `--target Lib`. MEASURED 2026-11-28 on candor-swift 0.44.0
                  (release build of 1e81824): 9 s with the trap, 0 s without — main.swift `dumpSwiftPackageJSON`
                  runs `swift package dump-package`, which executes the manifest.
                  CONTROL g_sw_live: `swift package dump-package` over a fresh copy takes >= SLEEP-1 s.
    java and ts have no S-G cell yet (GAP): java's only compile is the ⟨0.32⟩ peek derivation, whose live trap is an
    annotation-processor jar under the scanned root, and ts's would be a TypeScript-plugin or package-script trap;
    neither engine has a route that reaches one today, and a trap with no route is decoration, so each waits for a
    lane that can show its trap firing.

CALIBRATED: CANDOR_PROBE_FAULT=1 strips the Net from the H reports that carry a new key and drops the `untyped`
entry from f_untyped, so a_tol, d_tol, f_untyped and f_viol go red on every engine; it writes the build.rs sentinel
after candor-scan returns, so g_rs_buildrs goes red; and it scans g_sw_whole through `--target`, the route that
executes, so g_sw_whole goes red. Registered in probe_check.py (java arm).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_rung024 as G                # noqa: E402
import gen_policy_semantics as PS      # noqa: E402

SPEC_CLAUSES = [
    ("§2.3 ⟨0.45⟩ S-A", "A producer MUST NOT emit the key over answers no typer gave."),
    ("§2.3 ⟨0.45⟩ S-A", "When it does emit the key, every member above except `identity` MUST be present."),
    ("§2.3 ⟨0.45⟩ S-D", "A row that carries `usr` MUST carry the `fn` and `hash` it would carry without it"),
    ("§2.3 ⟨0.45⟩ S-F", "THE ⟨0.21⟩ VERDICT APPLIES UNCHANGED, AND A CONSUMER MUST NOT NEED THE REASON TO APPLY IT."),
    ("§2.3 ⟨0.45⟩ S-F", "A certain violation still dominates (exit 1, §3.3 ⟨0.24⟩)."),
    ("§2.3 ⟨0.45⟩ S-G", "A SCAN MUST NOT EXECUTE ANYTHING FROM THE SCANNED TREE."),
    ("§2", "a consumer MUST tolerate (ignore) envelope or entry fields it does not recognize."),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
SLEEP = 6
TYPED_MEMBERS = ("typer", "target", "configurations", "plan", "environment", "dependencies")

# (cell, engine) -> the DRAFT clause the cell waits on. A PASSING PENDING CELL IS A FAILURE: retire the line.
PENDING = {
    ("a_emit", "ts"): "S-A DRAFT — candor-ts asks the TypeScript checker and records no typing environment",
    ("g_sw_target", "swift"): "S-G DRAFT — `--target` runs `swift package dump-package` (main.swift "
                              "dumpSwiftPackageJSON), executing the scanned manifest; measured 2026-11-28, no row "
                              "filed yet (coordinator assigns)",
}

PART_OF = {"a_tol": 111, "a_absent": 111, "a_emit": 111, "d_tol": 112, "d_absent": 112,
           "f_ctl": 113, "f_untyped": 113, "f_viol": 113,
           "g_rs_live": 114, "g_rs_buildrs": 114, "g_sw_live": 114, "g_sw_whole": 114, "g_sw_target": 114}


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(s)


# =====================================================================================================
# H ARMS — hand-written reports through every engine's `gate --report`
# =====================================================================================================
NET = {"fn": "app::f", "hash": "app#app::f", "inferred": ["Net"], "direct": ["Net"]}


def base(functions, count=1):
    return {"candor": {"version": "handwritten", "spec": "0.44"}, "package": "app",
            "analyzed": {"count": count, "digest": "0"}, "functions": functions}


TYPED_BY = {"typer": "swift-frontend 6.4.2", "target": "arm64-apple-macosx15.0 MacOSX15.2.sdk",
            "configurations": [{"id": "debug", "conditions": ["DEBUG", "SWIFT_PACKAGE"]}],
            "plan": ["evaluated"], "environment": {},
            "dependencies": [{"package": "swift-numerics", "revision": "0c0290f", "origin": "pin"}],
            "futureMember": {"ignored": True}}
UNTYPED = {"path": "src/untyped.swift", "reason": "untyped:module-refused"}


def gate(eng, rep, ws, tag):
    loc = G.write_report(os.path.join(ws, "h-%s-%s" % (eng, tag)), eng, rep)
    rc, doc, _err = PS.gate(eng, loc, "deny Net\n", ws, "h-%s-%s" % (eng, tag))
    return rc, doc


def viol(doc):
    return sorted((x.get("hash"), x.get("fn")) for x in (doc or {}).get("violations") or [])


def tolerance(eng, ws, cid, extra_env, extra_row, why):
    """A report with the new key(s) must gate exactly as the same report without them."""
    plain = base([dict(NET)])
    keyed = base([dict(NET, **extra_row)])
    keyed.update(extra_env)
    if FAULT:
        keyed["functions"][0]["inferred"] = []
        keyed["functions"][0]["direct"] = []
    r0, d0 = gate(eng, plain, ws, cid + "-plain")
    r1, d1 = gate(eng, keyed, ws, cid + "-keyed")
    p = []
    if r0 != 1:
        p.append("plain report: exit %s, EXPECTED 1 (the control did not fire)" % r0)
    if r1 != 1:
        p.append("report with the key: exit %s, EXPECTED 1" % r1)
    if viol(d0) != viol(d1):
        p.append("violations differ: %s vs %s" % (viol(d0), viol(d1)))
    return (cid, eng, not p, "; ".join(p) if p else "exit 1 on both, same violations", why)


def run_h(engines, ws):
    out = []
    for eng in engines:
        out.append(tolerance(eng, ws, "a_tol", {"typedBy": TYPED_BY}, {},
                             "§2 forward compatibility: a reader ignores `typedBy`"))
        out.append(tolerance(eng, ws, "d_tol", {"typedBy": dict(TYPED_BY, identity="swift")},
                             {"usr": ["s:3app1fyyF"]}, "§2 forward compatibility: a reader ignores `usr`"))
        # S-F: the control, the untyped entry, and dominance.
        rc, doc = gate(eng, base([], count=2), ws, "f_ctl")
        out.append(("f_ctl", eng, rc == 0, "exit %s (expected 0: nothing to deny, nothing unread)" % rc,
                    "control — the exit 2 below must come from the entry"))
        rep = base([], count=2)
        if not FAULT:
            rep["unanalyzed"] = [dict(UNTYPED)]
        rc, doc = gate(eng, rep, ws, "f_untyped")
        p = []
        if rc != 2:
            p.append("exit %s, EXPECTED 2" % rc)
        if not isinstance(doc, dict) or doc.get("incomplete") is not True:
            p.append("verdict lacks `incomplete: true`")
        echoed = [u for u in ((doc or {}).get("unanalyzed") or []) if isinstance(u, dict)]
        if not any(u.get("path") == UNTYPED["path"] and u.get("reason") == UNTYPED["reason"] for u in echoed):
            p.append("entry not echoed verbatim (got %s)" % json.dumps(echoed)[:160])
        out.append(("f_untyped", eng, not p, "; ".join(p) if p else "exit 2, incomplete, entry echoed verbatim",
                    "S-F: the ⟨0.21⟩ verdict applies unchanged, keyed on non-emptiness"))
        rep = base([dict(NET)], count=2)
        rep["unanalyzed"] = [dict(UNTYPED)]
        if FAULT:
            rep["functions"] = []
        rc, doc = gate(eng, rep, ws, "f_viol")
        out.append(("f_viol", eng, rc == 1, "exit %s (expected 1: the violation dominates)" % rc,
                    "S-F + §3.3 ⟨0.24⟩: a certain violation dominates the incomplete verdict"))
    return out


# =====================================================================================================
# S ARMS — the engines' own reports
# =====================================================================================================
def own_reports(eng, ws):
    """Scan the shared three-function fixture with the engine itself; return every report document it wrote."""
    pol = os.path.join(ws, "s-pol-%s" % eng)
    write(pol, "deny Net\n")
    gj = os.path.join(ws, "s-%s.gate.json" % eng)
    scan = {"rust": G._rust_scan, "java": G._java_scan, "ts": G._ts_scan, "swift": G._swift_scan}[eng]
    sws = os.path.join(ws, "s-" + eng)
    os.makedirs(sws, exist_ok=True)
    loc, _rc = scan(sws, pol, gj)
    if loc is None:
        return None
    if eng == "java":
        paths = [loc]
    else:
        d = os.path.dirname(loc)
        paths = [p for p in glob.glob(os.path.join(d, "*.json"))
                 if not any(t in os.path.basename(p) for t in ("callgraph", "hierarchy", "calibrated", "gate"))]
    docs = []
    for p in paths:
        try:
            j = json.load(open(p, encoding="utf-8"))
        except Exception:                   # noqa: BLE001
            continue
        if isinstance(j, dict) and "functions" in j:
            docs.append(j)
    return docs or None


def run_s(engines, ws):
    out = []
    for eng in engines:
        docs = own_reports(eng, ws)
        if docs is None:
            out.append(("a_absent" if eng != "ts" else "a_emit", eng, False, "BROKEN: the scan wrote no report",
                        "harness"))
            continue
        if eng == "ts":
            tb = [d.get("typedBy") for d in docs]
            ok = all(isinstance(t, dict) and all(m in t for m in TYPED_MEMBERS) for t in tb)
            out.append(("a_emit", eng, ok, "typedBy %s" % ("present, complete" if ok else "absent or incomplete"),
                        "S-A: an engine that asks a type checker records the typing environment"))
            continue
        has_tb = [d for d in docs if "typedBy" in d]
        out.append(("a_absent", eng, not has_tb,
                    "no typedBy" if not has_tb else "typedBy present on a syntactic report: %s"
                    % json.dumps(has_tb[0]["typedBy"])[:120],
                    "S-A: a producer MUST NOT emit the key over answers no typer gave"))
        with_usr = [f.get("fn") for d in docs for f in d.get("functions") or [] if isinstance(f, dict) and "usr" in f]
        out.append(("d_absent", eng, not with_usr,
                    "no row carries usr" if not with_usr else "usr on %s" % with_usr[:3],
                    "S-D: a usr is the typer's identity; a producer with no typer has none to publish"))
    return out


# ---------------------------------------------------------------------------------------------------- S-G rust
def rust_trap(d, sentinel):
    write(os.path.join(d, "Cargo.toml"),
          "[package]\nname = \"sgtrap\"\nversion = \"0.0.0\"\nedition = \"2021\"\nbuild = \"build.rs\"\n")
    write(os.path.join(d, "build.rs"),
          "fn main() { std::fs::write(%s, b\"executed\").unwrap(); }\n" % json.dumps(sentinel))
    write(os.path.join(d, "src", "lib.rs"), "pub fn f() { let _ = std::fs::read(\"/etc/hosts\"); }\n")


def run_g_rust(ws):
    out = []
    live_dir = os.path.join(ws, "g-rs-live")
    live_sent = os.path.join(ws, "g-rs-live.sentinel")
    rust_trap(live_dir, live_sent)
    env = dict(os.environ, CARGO_TARGET_DIR=os.path.join(ws, "g-rs-live-target"))
    r = run(["cargo", "build", "--offline", "--quiet"], cwd=live_dir, env=env)
    live = os.path.exists(live_sent)
    out.append(("g_rs_live", "rust", live, "cargo build wrote the sentinel" if live
                else "the trap did not fire under cargo build (rc %s) — g_rs_buildrs is VACUOUS" % r.returncode,
                "control — the build.rs trap is live"))
    scan_dir = os.path.join(ws, "g-rs")
    sent = os.path.join(ws, "g-rs.sentinel")
    rust_trap(scan_dir, sent)
    os.makedirs(os.path.join(scan_dir, "out"), exist_ok=True)
    rs = run([G.rust_scan(), scan_dir, "--out", os.path.join(scan_dir, "out", "r")])
    if FAULT:
        write(sent, "executed")             # the fault: behave as an engine that ran build.rs
    wrote = bool(glob.glob(os.path.join(scan_dir, "out", "r.*")))
    p = []
    if not wrote:
        p.append("BROKEN: candor-scan wrote no report (rc %s)" % rs.returncode)
    if os.path.exists(sent):
        p.append("the build script RAN: the sentinel exists")
    out.append(("g_rs_buildrs", "rust", live and not p, "; ".join(p) if p else "report written, build.rs not run",
                "S-G: a scan executes nothing from the tree"))
    return out


# --------------------------------------------------------------------------------------------------- S-G swift
def swift_pkg(d, nonce, sleep):
    body = ("import PackageDescription\nimport Foundation\n%s"
            "let package = Package(name: \"Lib\", targets: [.target(name: \"Lib\")])\n"
            % ("Thread.sleep(forTimeInterval: %d)\n" % sleep if sleep else ""))
    # A fresh nonce per evaluation: SwiftPM caches manifest results by content, and a cached manifest is not run.
    write(os.path.join(d, "Package.swift"), "// swift-tools-version:5.9\n// nonce %s-base\n%s" % (nonce, body))
    write(os.path.join(d, "Package@swift-5.9.swift"),
          "// swift-tools-version:5.9\n// nonce %s-versioned\n%s" % (nonce, body))
    write(os.path.join(d, "Sources", "Lib", "Lib.swift"), "public func f() { print(\"x\") }\n")


def timed(cmd, cwd=None):
    t0 = time.monotonic()
    r = run(cmd, cwd=cwd)
    return time.monotonic() - t0, r


def run_g_swift(ws):
    out = []
    stamp = "%d-%d" % (os.getpid(), int(time.time() * 1000))
    live_dir = os.path.join(ws, "g-sw-live")
    swift_pkg(live_dir, stamp + "-live", SLEEP)
    if shutil.which("swift"):
        dt, r = timed(["swift", "package", "dump-package", "--package-path", live_dir])
        live = r.returncode == 0 and dt >= SLEEP - 1
        why = "dump-package took %.1fs" % dt
    else:
        live, why = False, "no `swift` on PATH, so the trap cannot be shown live"
    out.append(("g_sw_live", "swift", live, why + ("" if live else " — the g_sw_* cells are VACUOUS"),
                "control — the manifest trap is live when SwiftPM evaluates it"))
    sw = G.swift_bin()
    # The fault scans g_sw_whole through the route that executes (`--target`), so the detector is shown to read it.
    for cid, extra in (("g_sw_whole", ["--target", "Lib"] if FAULT else []), ("g_sw_target", ["--target", "Lib"])):
        times = {}
        broken = None
        for arm, sleep in (("trap", SLEEP), ("plain", 0)):
            d = os.path.join(ws, "%s-%s" % (cid, arm))
            swift_pkg(d, "%s-%s-%s" % (stamp, cid, arm), sleep)
            dt, r = timed([sw, d] + extra + ["--out", os.path.join(d, "out")])
            if not glob.glob(os.path.join(d, "out.*")):
                broken = "BROKEN: candor-swift wrote no report on the %s arm (rc %s)" % (arm, r.returncode)
            times[arm] = dt
        delta = times["trap"] - times["plain"]
        executed = delta >= SLEEP - 2
        if broken:
            ok, detail = False, broken
        else:
            ok = live and not executed
            detail = "trap %.1fs vs plain %.1fs: %s" % (times["trap"], times["plain"],
                                                          "the manifest was EXECUTED" if executed
                                                          else "not executed")
        out.append((cid, "swift", ok, detail, "S-G: a scan executes nothing from the tree"))
    return out


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    part = int(argv[argv.index("--part") + 1]) if "--part" in argv else None
    print("=" * 100)
    print("COMPILER-TYPED PRODUCERS ⟨0.45⟩ DRAFT — S-A typedBy (111), S-D usr (112), S-F untyped (113), S-G no "
          "execution (114)%s" % ("" if part is None else "; this run: PART %d only" % part))
    print("  SCORED cells must hold today; PENDING cells wait on a port, and a PENDING cell that PASSES fails")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the H reports carrying a new key lose their Net and f_untyped loses")
        print("       its entry, the build.rs sentinel is written after the scan, and g_sw_whole is scanned through")
        print("       --target, so a_tol, d_tol, f_untyped, f_viol, g_rs_buildrs and g_sw_whole must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part111-114-")
    bad = stale = npend = 0
    rows = []
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        for e in G.ENGINES:
            if G.installed(e) and not G.alive(e) and (only is None or e == only):
                print("  %-6s -> BROKEN: installed but not responding" % e)
                bad += 1
        if not engines:
            print("TYPING-ENV: no engine available — NOT a pass")
            return 2
        want = (lambda n: part is None or part == n)
        if want(111) or want(112) or want(113):
            rows += run_h(engines, ws)
        if want(111) or want(112):
            rows += run_s(engines, ws)
        if want(114):
            if "rust" in engines:
                rows += run_g_rust(ws)
            if "swift" in engines:
                rows += run_g_swift(ws)
        rows = [r for r in rows if part is None or PART_OF[r[0]] == part]
        for cid, eng, ok, detail, why in rows:
            key = (cid, eng)
            if key in PENDING:
                npend += 1
                if ok:
                    print("  PENDING CELL PASSED %-12s %-6s — the port landed: retire the PENDING line (%s)"
                          % (cid, eng, PENDING[key]))
                    stale += 1
                else:
                    print("  pending %-12s %-6s %s  [%s]" % (cid, eng, detail, PENDING[key]))
            elif ok:
                print("  OK      %-12s %-6s %s" % (cid, eng, detail))
            else:
                print("  FAIL    %-12s %-6s %s  [%s]" % (cid, eng, detail, why))
                bad += 1
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    if bad or stale:
        print("TYPING-ENV: %d cell(s) wrong, %d pending cell(s) PASSED — SPEC §2.3 ⟨0.45⟩ DRAFT" % (bad, stale))
        return 1
    print("TYPING-ENV: OK — %d cell(s), %d engine(s), %d pending (each names its DRAFT clause)"
          % (len(rows), len(engines), npend))
    return 0


if __name__ == "__main__":
    sys.exit(main())
