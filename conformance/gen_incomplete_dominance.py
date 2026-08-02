#!/usr/bin/env python3
"""
P5 — INCOMPLETE-VS-VIOLATION DOMINANCE, as a GENERATED property.

SPEC §3.3.1, verbatim:

    A configured gate over incompletely-analyzed code MUST fail closed (exit != 0);
    **a real violation (exit 1) still dominates.**

Two clauses, and only the first one had a test. The second is the one with a body count.

WHY THIS EXISTS, AND WHY IT IS NOT A FIXTURE
---------------------------------------------
candor-rust's AS-EFF-005 baseline guard shipped with the second clause inverted: the incomplete-analysis
refusal ran BEFORE the baseline compare, so a crate carrying a real regression AND one unparseable file
exited 2 and wrote `{ok:false, incomplete:true, violations: []}`. The regression was not mis-coded, it was
**absent from the artifact a CI consumer reads** — a machine-consumer under-report wearing an exit code.

Its sibling, the POLICY gate, had exactly the same defect and was fixed a week earlier. The fix wrote its
whole reasoning into the policy gate's comment and never looked thirty lines up the same function. So:

    ONE SPEC CLAUSE. TWO GATES THAT MUST OBEY IT. ONLY ONE OF THEM WAS EVER TESTED.

That is the shape this file is built for, and a fixture cannot hold it — a fixture tests the gate its
author was thinking about. A property enumerates the gates.

THE RELATION IS A SELF-DIFFERENTIAL, so there is no expected-value table and there must never be one.
For each (engine, gate) the harness renders three arms of ONE program:

    violation_only    a real violation, everything parses          -> the CONTROL and the ORACLE
    incomplete_only   no violation, one unit that will not parse   -> must FAIL CLOSED
    both              the same violation, plus that same unit      -> must answer like `violation_only`
                                                                       AND disclose the incompleteness

`violation_only` is the expectation for `both`: whatever the engine reports when it can see everything,
it must still report when one extra unit is unreadable. Nothing here says what a `deny Net` verdict
should look like — only that adding an unreadable file does not delete it.

THE CONTROL IS LOAD-BEARING AND IS CHECKED FIRST. If `violation_only` does not exit 1 with a finding, the
`both` row proves nothing: it would be measuring a gate that never fires, and would pass. Every engine
whose control is dead is reported BROKEN rather than OK — a distinction this suite has had to add twice
before, after a harness mis-invocation printed as a finding about candor.

BOTH GATES, and the second is the point. `policy` is `deny <effect>`; `baseline` is the AS-EFF-005
ratchet, where the violation is an existing function GAINING an effect against a recorded report. They are
different code paths in all four engines, they answer to the same clause, and the defect that motivated
this file was in the one that had no test.

WHY EVALUATING OVER AN INCOMPLETE SCAN IS SOUND IN THE DIRTY DIRECTION — the asymmetry that licenses the
whole property, and without it this would be demanding a fabrication. A parse failure makes the scan see
LESS. A `deny` fires on effects PRESENT; AS-EFF-005 fires on effects GAINED. Less evidence can therefore
only MASK a violation, never manufacture one. So a violation found alongside unreadable source is real and
must be reported, while a CLEAN gate over unreadable source is exactly the false-pure that clause one
forbids. Both directions are asserted; a "fix" that simply dropped the refusal would satisfy one and
break the other, and `incomplete_only` is what catches it.

VACUITY (standing bar item 8) is earned from the engine's own output, never asserted: an engine whose
control arm does not fire has NO live cells and FAILS rather than passing quietly.

USAGE
    python3 gen_incomplete_dominance.py                   # raw truth, exit non-zero on any violation
    python3 gen_incomplete_dominance.py --only rust,java
    python3 gen_incomplete_dominance.py --keep
    python3 gen_incomplete_dominance.py --baseline incomplete-dominance-baseline.json   # PART 29
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_differential as gd

ARMS = ("violation_only", "incomplete_only", "both")


def run(cmd, env=None, cwd=None):
    e = dict(os.environ)
    # HERMETIC: the ambient environment must not smuggle in a gate, a baseline or a dep chain of its own.
    for k in ("CANDOR_POLICY", "CANDOR_BASELINE", "CANDOR_DEPS", "CANDOR_CONFIG"):
        e.pop(k, None)
    if env:
        e.update(env)
    try:
        p = subprocess.run(cmd, capture_output=True, env=e, cwd=cwd, timeout=300)
        return p.returncode, p.stdout.decode(errors="replace"), p.stderr.decode(errors="replace")
    except Exception as ex:
        return None, "", str(ex)


def verdict_of(path):
    """The --gate-json document, or None if the engine wrote none."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def violations_of(doc):
    if not isinstance(doc, dict):
        return []
    v = doc.get("violations")
    return v if isinstance(v, list) else []


def says_incomplete(doc):
    """Either channel counts. `incomplete: true` is the ⟨0.21⟩ flag; a non-empty `unanalyzed` is the
    manifest that names WHICH units — an engine may lead with either, and a property that demanded one
    spelling would be testing a spelling."""
    if not isinstance(doc, dict):
        return False
    return bool(doc.get("incomplete")) or bool(doc.get("unanalyzed"))


# =====================================================================================================
# PER-ENGINE TREES. Each builder writes the arm's sources and returns (target, extra_env) for the run.
# The three arms differ in exactly two bits — does a violation exist, does an unparseable unit exist —
# so any difference in the answer is attributable to those and nothing else.
# =====================================================================================================
NET = {
    "rust": 'let _ = std::net::TcpStream::connect("h.example.com:80");',
    "java": 'try { new java.net.Socket("h.example.com", 80); } catch (Exception e) {}',
    "ts": 'void fetch("https://h.example.com/x");',
    "swift": '_ = URLSession.shared.dataTask(with: URL(string: "https://h.example.com/x")!)',
}
FS = {
    "rust": 'let _ = std::fs::read("/tmp/x");',
    "java": 'try { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); } catch (Exception e) {}',
    "ts": 'void (globalThis as any).require?.("fs")?.readFileSync?.("/tmp/x");',
    "swift": '_ = FileManager.default.contents(atPath: "/tmp/x")',
}


def _rust_tree(ws, body, incomplete):
    d = os.path.join(ws, "rust")
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    with open(os.path.join(d, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "p5"\nversion = "0.0.0"\nedition = "2021"\n')
    with open(os.path.join(d, "src", "lib.rs"), "w") as f:
        f.write(f"pub fn hit() {{ {body} }}\n")
    broken = os.path.join(d, "src", "broken.rs")
    if incomplete:
        with open(broken, "w") as f:
            f.write("pub fn nope( {{{ this is not rust\n")
    elif os.path.exists(broken):
        os.remove(broken)
    return d


def _java_tree(ws, body, incomplete):
    src = os.path.join(ws, "jsrc")
    out = os.path.join(ws, "jout")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(src, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(src, "Hit.java"), "w") as f:
        f.write(f"public class Hit {{ public static void hit() {{ {body} }} }}\n")
    c = run(["javac", "-d", out, os.path.join(src, "Hit.java")])
    if c[0] != 0:
        return None
    if incomplete:
        # A .class the loader cannot parse — java's incompleteness is a BYTECODE fact, not a syntax one,
        # so the arm has to be spelled in the engine's own terms rather than by copying rust's.
        with open(os.path.join(out, "Broken.class"), "wb") as f:
            f.write(b"\xca\xfe\xba\xbe" + b"\x00" * 8 + b"garbage-not-a-constant-pool")
    return out


def _ts_tree(ws, body, incomplete):
    d = os.path.join(ws, "ts")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "package.json"), "w") as f:
        f.write('{"name":"p5","version":"1.0.0"}\n')
    with open(os.path.join(d, "hit.ts"), "w") as f:
        f.write(f"export function hit(): void {{ {body} }}\n")
    broken = os.path.join(d, "broken.ts")
    if incomplete:
        with open(broken, "w") as f:
            f.write("export function nope( {{{ <<< not typescript\n")
    elif os.path.exists(broken):
        os.remove(broken)
    return d


def _swift_tree(ws, body, incomplete):
    d = os.path.join(ws, "swift")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "cases.swift"), "w") as f:
        f.write("import Foundation\n")
        f.write(f"enum Api {{ static func hit() {{ {body} }} }}\n")
    broken = os.path.join(d, "broken.swift")
    if incomplete:
        with open(broken, "w") as f:
            f.write("func nope( {{{ <<< not swift\n")
    elif os.path.exists(broken):
        os.remove(broken)
    return d


TREES = {"rust": _rust_tree, "java": _java_tree, "ts": _ts_tree, "swift": _swift_tree}


def engine_bin(eng):
    """(available, invoker) — invoker(target, policy, verdict, baseline) -> (rc, out, err)."""
    if eng == "rust":
        b = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
        if not os.path.exists(b):
            return None, "no candor-scan"

        def go(target, policy, verdict, baseline, out_prefix=None):
            cmd = [b, target]
            if policy:
                cmd += ["--policy", policy]
            if verdict:
                cmd += ["--gate-json", verdict]
            if out_prefix:
                cmd += ["--out", out_prefix]
            return run(cmd, env={"CANDOR_BASELINE": baseline} if baseline else None)
        return go, None

    if eng == "java":
        jar = os.environ.get("CANDOR_JAVA_JAR")
        if not jar:
            c = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
            jar = max(c, key=os.path.getmtime) if c else None
        if not jar or not os.path.exists(jar) or not shutil.which("javac"):
            return None, "no candor-java jar / javac"

        def go(target, policy, verdict, baseline, out_prefix=None):
            cmd = ["java", "-jar", jar, target]
            if policy:
                cmd += ["--policy", policy]
            if verdict:
                cmd += ["--gate-json", verdict]
            if out_prefix:
                cmd += ["--json", out_prefix + ".json"]
            return run(cmd, env={"CANDOR_BASELINE": baseline} if baseline else None)
        return go, None

    if eng == "ts":
        s = os.path.join(gd.CANDOR_TS, "scan.mjs")
        if not shutil.which("node") or not os.path.exists(s):
            return None, "no node / scan.mjs"

        def go(target, policy, verdict, baseline, out_prefix=None):
            cmd = ["node", s, target]
            if policy:
                cmd += ["--policy", policy]
            if verdict:
                cmd += ["--gate-json", verdict]
            if out_prefix:
                cmd += ["--out", out_prefix]
            return run(cmd, env={"CANDOR_BASELINE": baseline} if baseline else None)
        return go, None

    if eng == "swift":
        b = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
        if not shutil.which("swift") or not os.path.exists(b):
            return None, "no swift toolchain"

        def go(target, policy, verdict, baseline, out_prefix=None):
            # THE TARGET IS THE DIRECTORY, NOT `cases.swift`. Pointing candor-swift at the single file
            # made `broken.swift` invisible, so the "incomplete" arms were not incomplete — and the run
            # reported swift FALSE-GREEN on both gates, a §3.3.1 clause-1 breach that did not exist.
            # `candor-swift [<dir|file.swift>]` takes either; a fixture that cannot show the gap is not a
            # control, and here it manufactured a finding instead of missing one.
            cmd = [b, target]
            if policy:
                cmd += ["--policy", policy]
            if verdict:
                cmd += ["--gate-json", verdict]
            if out_prefix:
                cmd += ["--out", out_prefix]
            return run(cmd, env={"CANDOR_BASELINE": baseline} if baseline else None)
        return go, None
    return None, "unknown engine"


# SPEC §2.2's RESERVED trailing segments — the sidecars a report-locator glob MUST exclude. Copied from
# candor-java's `Loader.RESERVED_SIDECAR_SEGMENTS`, which is the canonical list.
#
# THIS HARNESS FELL INTO EXACTLY THE DEFECT THE RULE EXISTS FOR, on its first run. `find_report` excluded
# `callgraph` and `hierarchy` and not `locs`, so the ts baseline snapshot resolved to `<prefix>.locs.json`
# — a sidecar handed to the engine as a BASELINE, which then exited 2 and printed as `ts/baseline
# CONTROL-DEAD`, i.e. as a finding about candor-ts. §2.2 was written after candor-rust discriminated
# sidecars by SEGMENT COUNT and claimed one as a report; a hand-rolled two-name exclusion here is the same
# mistake in a third spelling. Enumerate the reserved set or do not filter at all.
RESERVED_SIDECAR_SEGMENTS = ("callgraph", "hierarchy", "calibrated", "layerreach", "locs", "gate")


def is_sidecar(name):
    if ".encountered-" in name or not name.endswith(".json"):
        return ".encountered-" in name
    stem = name[: -len(".json")]
    return stem.rsplit(".", 1)[-1] in RESERVED_SIDECAR_SEGMENTS if "." in stem else False


def find_report(prefix_dir, prefix):
    cands = [p for p in gd._glob(prefix_dir, ".json")
             if not is_sidecar(os.path.basename(p))
             and os.path.basename(p).startswith(os.path.basename(prefix))]
    return cands[0] if cands else None


def measure(eng, go, ws, gate):
    """Run the three arms for one (engine, gate). Returns {arm: (rc, doc)}."""
    res = {}
    pol = os.path.join(ws, "policy.txt")
    for arm in ARMS:
        violating = arm in ("violation_only", "both")
        incomplete = arm in ("incomplete_only", "both")
        verdict = os.path.join(ws, f"{eng}.{gate}.{arm}.verdict.json")
        if os.path.exists(verdict):
            os.remove(verdict)          # standing bar: delete the output before measuring
        if gate == "policy":
            body = NET[eng] if violating else ""
            target = TREES[eng](ws, body, incomplete)
            if target is None:
                return None
            with open(pol, "w") as f:
                f.write("deny Net\n")
            rc, _o, _e = go(target, pol, verdict, None)
        else:
            # BASELINE: record a snapshot of the FS-only body, then (for the violating arms) add Net on
            # top of it — an EXISTING function gaining an effect, which is what AS-EFF-005 fires on.
            base_prefix = os.path.join(ws, f"{eng}.base")
            for f in gd._glob(os.path.dirname(base_prefix), ".json"):
                if os.path.basename(f).startswith(os.path.basename(base_prefix)):
                    os.remove(f)
            target = TREES[eng](ws, FS[eng], False)
            if target is None:
                return None
            rc0, _o, _e = go(target, None, None, None, out_prefix=base_prefix)
            snap = find_report(os.path.dirname(base_prefix), base_prefix)
            if rc0 != 0 or not snap:
                return None
            body = FS[eng] + " " + NET[eng] if violating else FS[eng]
            target = TREES[eng](ws, body, incomplete)
            rc, _o, _e = go(target, None, verdict, snap)
        res[arm] = (rc, verdict_of(verdict))
    return res


def judge(res):
    """The three clauses, as findings. Returns (control_ok, [finding…])."""
    out = []
    rc1, d1 = res["violation_only"]
    base_v = violations_of(d1)
    control_ok = (rc1 == 1 and len(base_v) > 0)
    if not control_ok:
        return False, [("CONTROL-DEAD",
                        f"violation_only exited {rc1} with {len(base_v)} violation(s) — the gate never "
                        f"fired, so the rows below would pass while measuring nothing")]
    rc2, d2 = res["incomplete_only"]
    if rc2 == 0:
        out.append(("FALSE-GREEN",
                    "incomplete_only exited 0 — a gate certified code it could not read (§3.3.1 clause 1)"))
    elif not says_incomplete(d2) and d2 is not None:
        out.append(("UNDISCLOSED",
                    f"incomplete_only exited {rc2} but its document neither sets `incomplete` nor names "
                    f"`unanalyzed` — the refusal is not machine-readable"))
    rc3, d3 = res["both"]
    got_v = violations_of(d3)
    if rc3 != 1:
        out.append(("NOT-DOMINANT",
                    f"both exited {rc3}, not 1 — §3.3.1 says a real violation still dominates; this "
                    f"reports 'I could not analyse' over 'your code violates'"))
    if len(got_v) < len(base_v):
        out.append(("DROPPED",
                    f"both carries {len(got_v)} violation(s) where violation_only carries {len(base_v)} — "
                    f"the finding is ABSENT FROM THE ARTIFACT, not merely mis-coded"))
    elif not says_incomplete(d3):
        out.append(("SWAPPED",
                    "both reports the violation but NOT the incompleteness — the two halves are "
                    "additive, and dropping clause 1 to satisfy clause 2 is the mirror defect"))
    return True, out


def main():
    args = sys.argv[1:]
    keep = "--keep" in args
    only = set(args[args.index("--only") + 1].split(",")) if "--only" in args else None
    baseline = args[args.index("--baseline") + 1] if "--baseline" in args else None

    print("P5 — INCOMPLETE-VS-VIOLATION DOMINANCE  (SPEC §3.3.1, over EVERY gate)")
    print("  a gate over unreadable code must fail closed — AND a real violation must still dominate")

    rows, findings, absent = [], [], []
    for eng in ("rust", "java", "ts", "swift"):
        if only and eng not in only:
            continue
        go, err = engine_bin(eng)
        if go is None:
            absent.append((eng, err))
            continue
        for gate in ("policy", "baseline"):
            ws = tempfile.mkdtemp(prefix=f"candor-p5-{eng}-{gate}-")
            try:
                res = measure(eng, go, ws, gate)
                if res is None:
                    rows.append((eng, gate, "HARNESS", 0))
                    findings.append((eng, gate, "HARNESS",
                                     "could not build the arms (compile/snapshot failed) — this is the "
                                     "harness, and it must never read as a refusal by the engine"))
                    continue
                ok, fs = judge(res)
                rows.append((eng, gate, "live" if ok else "control-dead", len(fs)))
                for kind, why in fs:
                    findings.append((eng, gate, kind, why))
            finally:
                if keep:
                    print(f"    kept: {ws}")
                else:
                    shutil.rmtree(ws, ignore_errors=True)

    print(f"\n  {'engine':<8}{'gate':<10}{'status':<14}{'findings':>9}")
    for eng, gate, status, n in rows:
        print(f"  {eng:<8}{gate:<10}{status:<14}{n:>9}")
    for eng, err in absent:
        print(f"  {eng:<8}{'—':<10}ABSENT — {err}")

    if findings:
        print(f"\n{len(findings)} VIOLATION(S) of §3.3.1:")
        for eng, gate, kind, why in findings:
            print(f"  {eng:<6} {gate:<9} {kind:<13} {why}")

    dead = [(e, g) for e, g, s, _ in rows if s != "live"]
    if not rows:
        print("\nFAIL — no engine produced a measurement; nothing was tested.")

    waived = 0
    if baseline and os.path.exists(baseline):
        with open(baseline) as f:
            bl = json.load(f)
        known = {(k["engine"], k["gate"]) for k in bl.get("known", [])}
        hit = {(e, g) for e, g, _k, _w in findings}
        stale = known - hit
        waived = len([1 for e, g, _k, _w in findings if (e, g) in known])
        findings = [f for f in findings if (f[0], f[1]) not in known]
        print(f"\nRATCHET  (baseline: {baseline})")
        for e, g in sorted(known):
            mark = "STALE — every cell now passes; DELETE the entry" if (e, g) in stale else "WAIVED"
            print(f"  {e:<6} {g:<9} {mark}")
        if stale:
            print("\nFAIL — a waiver that outlives its defect masks the defect's return.")
            return 2

    bad = bool(findings) or bool(dead) or not rows
    n_live = len([1 for _e, _g, s, _n in rows if s == "live"])
    print(f"\nP5 INCOMPLETE-VS-VIOLATION DOMINANCE: "
          + ("FAILED — see above." if bad else
             f"OK — {n_live} (engine, gate) pair(s): a violation survived an incomplete scan in every one"
             + (f" (except {waived} waived)" if waived else "")))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
