#!/usr/bin/env python3
"""
GENERATED POLICY MATRIX — the PEEK must agree with the GATE about what a policy denies.

WHY THIS EXISTS, stated as it happened
--------------------------------------
⟨0.30⟩ made a non-empty `outOfScope` verdict-bearing, which promoted a previously-advisory question —
"does this policy deny this function's effects?" — into an exit code. That question was already answered
once, by the gate. Each engine then answered it a SECOND time inside its peek, and §6.2 already forbids
exactly that: *"THE GATE AND THE DISCLOSURE MUST APPLY THE SAME RULE, AND SHOULD SHARE THE SAME CODE."*

Three review rounds found defects in that second answer. Every one was a policy FORM the peek's
re-implementation had not accounted for, and every round I fixed the forms that were named and the next
round found adjacent ones:

  · `pure` — a deny rule with an EMPTY effect list, meaning every effect except Unknown. Flattened into
    a set of effect NAMES it denies nothing, so the STRICTEST policy silently disarmed the rung. All four.
  · `deny Net[known-partner]` — destination-class filters dropped, so the peek reddened hosts the rule
    does not deny. Found in ts/rust, fixed, then found again in swift and java.
  · `net-partner` config — the ts peek's child scan never saw the project's `.candor/config`, so the
    partner set was always empty: a false all-clear one way and an over-charge the other.
  · rule SCOPES — dropped entirely at first; later, in ts, matched against absolute checkout paths, so a
    verdict depended on which directory the repo was cloned into.

Hand-written conformance arms cannot close this class, and the reason is structural: an arm tests the
shape its author thought of, and the defect is always the shape they did not. So this file GENERATES the
matrix instead of enumerating it.

THE INVARIANT, and why it needs no expected values
--------------------------------------------------
For each policy shape, the same effect-performing code is placed BOTH in scope and out of scope. Then:

    the gate's judgement of the IN-SCOPE copy  ==  the peek's judgement of the OUT-OF-SCOPE copy

If the gate says "this violates" (exit 1), the peek must say "this is a finding" (exit 2). If the gate
says "clean" (exit 0), the peek must say nothing (exit 0). **No cell carries a hand-written expected
value** — the gate IS the oracle, so a policy form nobody anticipated is still covered the moment it is
added to SHAPES, and a shape the author misunderstands cannot produce a wrong expectation.

That single property subsumes every defect above: class filters, partner config, scopes and `pure` all
change what the gate does, so the peek is required to change with them.

TWO FURTHER INVARIANTS, same fixtures, free
-------------------------------------------
  · SINK INDEPENDENCE — the exit code must be identical with and without `--gate-json`. A machine-readable
    sink is an output channel; it must not decide a verdict. (candor-rust currently FAILS this: its
    cross-member violation record is populated only when the sink is requested, so the ⟨0.30⟩ precedence
    check goes blind without it — measured on `clap` under `pure`, exit 1 with the flag and 2 without.)
  · PRECEDENCE — a run holding a real violation exits 1, never 2. "I could not evaluate" must not
    displace "I judged this and it breaks your policy".

USAGE
    python3 gen_policy_matrix.py             # run the matrix, non-zero on any disagreement
    python3 gen_policy_matrix.py --keep      # keep the generated workspace (prints the path)
    python3 gen_policy_matrix.py --engine ts # one engine

Engine resolution mirrors run.sh: CANDOR / CANDOR_JAVA / CANDOR_TS / CANDOR_SWIFT, absent ⇒ SKIP LOUDLY.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _p(env, default):
    return os.environ.get(env) or os.path.join(ROOT, default)


# ── the policy SHAPES. Add one here and every engine is covered, in both placements. ────────────────
# `needs` names an optional `.candor/config` line the shape depends on, so a config-sensitive form
# (net-partner) is exercised rather than assumed.
SHAPES = [
    dict(id="bare-deny",        policy="deny Net\n",                     needs=None),
    dict(id="pure",             policy="pure\n",                         needs=None),
    dict(id="deny-unknown",     policy="deny Net Unknown\n",             needs=None),
    dict(id="class-known",      policy="deny Net[known-partner]\n",      needs="net-partner partner.example\n"),
    dict(id="class-unknown",    policy="deny Net[unknown-host]\n",       needs="net-partner partner.example\n"),
    dict(id="class-no-config",  policy="deny Net[known-partner]\n",      needs=None),
    dict(id="scoped-hit",       policy="deny Net grab\n",                 needs=None),
    dict(id="scoped-miss",      policy="deny Net zzznomatch\n",          needs=None),
    dict(id="other-effect",     policy="deny Db\n",                      needs=None),
]

# The effect-performing body, per language. It reaches a LITERAL host so destination-class filters have
# something to classify — a runtime host would fail closed everywhere and hide the distinction.
BODIES = {
    "ts":    'export async function grab(): Promise<Response> {\n  return fetch("https://partner.example/x");\n}\n',
    "rust":  'pub fn grab() -> std::io::Result<std::net::TcpStream> {\n    std::net::TcpStream::connect("partner.example:80")\n}\n',
    # `URLSession.dataTask` is what this engine's own classifier pins as Net with a host-carrying URL
    # (ClassifierTests: kappaMember(root:"URLSession", member:"dataTask") == "Net"). The first spelling
    # tried here — `Data(contentsOf:)` — infers Unknown with no host, so every destination-class cell was
    # VACUOUS for swift: it agreed 0<->0 and exercised nothing. Caught by calibrating the generator
    # against a defect known to be present, which is the only way a green matrix means anything.
    "swift": 'import Foundation\npublic func grab() {\n  let u = URL(string: "https://partner.example/x")!\n'
             '  URLSession.shared.dataTask(with: u).resume()\n}\n',
}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def build_ts(work, shape, placed_out):
    """in-scope: the body under src/ (the tsconfig's include). out-of-scope: under excluded/."""
    d = os.path.join(work, "tsp")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    os.makedirs(os.path.join(d, "excluded"), exist_ok=True)
    with open(os.path.join(d, "tsconfig.json"), "w") as f:
        json.dump({"compilerOptions": {"target": "ES2022", "module": "ESNext",
                                       "moduleResolution": "bundler", "skipLibCheck": True,
                                       "noEmit": True}, "include": ["src/**/*.ts"]}, f)
    open(os.path.join(d, "src", "app.ts"), "w").write("export function ok(a: number): number { return a + 1; }\n")
    body = BODIES["ts"]
    # SAME FILENAME in both placements — only the DIRECTORY differs. A scope naming the file stem then
    # binds identically in scope and out, so the agreement invariant is testing the peek rather than an
    # artefact of the fixture. (An earlier version renamed the file between placements and the scoped
    # shapes went red for that reason alone; the generator has to be fair before its reds mean anything.)
    open(os.path.join(d, "excluded" if placed_out else "src", "grab_net.ts"), "w").write(body)
    # A DECOY sharing the basename's tail. An engine attributing a finding by basename match instead of
    # by the locator it was given will name this provably-clean file as the reason the build broke —
    # measured in the wild as `noop-delay.js`'s finding reported against `delay.js`.
    if placed_out:
        # TWO excluded files, one basename a SUFFIX of the other. `noop_net.ts` holds the effect;
        # `net.ts` is provably clean. An engine attributing findings with `endsWith(basename)` names the
        # clean file — measured in the wild as `noop-delay.js`'s finding reported against `delay.js`,
        # which makes the release notes' remedy ("bring THOSE files into scope") impossible to follow.
        # `grab_net.ts` ENDS WITH `net.ts`, so an engine attributing by `endsWith(basename)` names this
        # provably-clean decoy as the file that performed the effect.
        open(os.path.join(d, "excluded", "net.ts"), "w").write(
            "export function decoy(a: number): number { return a + 2; }\n")
    if shape["needs"]:
        os.makedirs(os.path.join(d, ".candor"), exist_ok=True)
        open(os.path.join(d, ".candor", "config"), "w").write(shape["needs"])
    open(os.path.join(d, "pol"), "w").write(shape["policy"])
    return d


def build_rust(work, shape, placed_out):
    """in-scope: src/lib.rs. out-of-scope: build.rs (the build-script exclusion class)."""
    d = os.path.join(work, "rsp")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    open(os.path.join(d, "Cargo.toml"), "w").write(
        '[package]\nname = "app"\nversion = "0.1.0"\nedition = "2021"\n')
    open(os.path.join(d, "src", "lib.rs"), "w").write("pub fn ok() -> u32 { 41 + 1 }\n")
    body = BODIES["rust"]
    if placed_out:
        open(os.path.join(d, "build.rs"), "w").write(
            body.replace("pub fn grab", "fn grab") + "fn main() { let _ = grab(); }\n")
    else:
        open(os.path.join(d, "src", "lib.rs"), "a").write(body)
    if shape["needs"]:
        os.makedirs(os.path.join(d, ".candor"), exist_ok=True)
        open(os.path.join(d, ".candor", "config"), "w").write(shape["needs"])
    open(os.path.join(d, "pol"), "w").write(shape["policy"])
    return d


def build_swift(work, shape, placed_out):
    """in-scope: Sources/. out-of-scope: Tests/ (the harness-target exclusion class)."""
    d = os.path.join(work, "swp")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "Sources", "S"), exist_ok=True)
    os.makedirs(os.path.join(d, "Tests"), exist_ok=True)
    open(os.path.join(d, "Package.swift"), "w").write(
        '// swift-tools-version:5.9\nimport PackageDescription\n'
        'let package = Package(name: "S", targets: [.target(name: "S")])\n')
    open(os.path.join(d, "Sources", "S", "a.swift"), "w").write("public func ok(_ a: Int) -> Int { a + 1 }\n")
    body = BODIES["swift"]
    if placed_out:
        open(os.path.join(d, "Tests", "T.swift"), "w").write(body)
    else:
        open(os.path.join(d, "Sources", "S", "net.swift"), "w").write(body)
    if shape["needs"]:
        os.makedirs(os.path.join(d, ".candor"), exist_ok=True)
        open(os.path.join(d, ".candor", "config"), "w").write(shape["needs"])
    open(os.path.join(d, "pol"), "w").write(shape["policy"])
    return d


def build_java(work, shape, placed_out):
    """in-scope: the compiled classes dir. out-of-scope: a jar UNDER the scan root (PART 48's shape).

    Compiles, so it is the slowest cell — but the jar-under-root exclusion is candor-java's own peekable
    class, and leaving java out of this matrix is how B2 (its dropped destination-class filters) survived
    a review round that had already closed the same defect in two other engines.
    """
    d = os.path.join(work, "jvp")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    os.makedirs(os.path.join(d, "classes"), exist_ok=True)
    os.makedirs(os.path.join(d, "libs"), exist_ok=True)
    open(os.path.join(d, "src", "App.java"), "w").write(
        "package app;\npublic class App { public static int ok(int a){ return a + 1; } }\n")
    open(os.path.join(d, "src", "Net.java"), "w").write(
        "package app;\nimport java.net.Socket;\n"
        "public class Net { public static void grab() throws Exception { new Socket(\"partner.example\", 80); } }\n")
    subprocess.run(["javac", "-d", os.path.join(d, "classes"),
                    os.path.join(d, "src", "App.java"), os.path.join(d, "src", "Net.java")],
                   capture_output=True)
    if placed_out:
        # move the Net class into a jar under the root and out of the analysed classes dir
        stage = os.path.join(d, "stage")
        os.makedirs(os.path.join(stage, "app"), exist_ok=True)
        shutil.move(os.path.join(d, "classes", "app", "Net.class"), os.path.join(stage, "app", "Net.class"))
        subprocess.run(["jar", "cf", os.path.join(d, "libs", "net.jar"), "app"], cwd=stage, capture_output=True)
        shutil.rmtree(stage, ignore_errors=True)
    if shape["needs"]:
        os.makedirs(os.path.join(d, ".candor"), exist_ok=True)
        open(os.path.join(d, ".candor", "config"), "w").write(shape["needs"])
    open(os.path.join(d, "pol"), "w").write(shape["policy"])
    return d


ENGINES = {}


def discover():
    rust = _p("CANDOR", "candor-rust")
    for cand in ("target/release/candor-scan", "target/debug/candor-scan"):
        b = os.path.join(rust, cand)
        if os.path.exists(b):
            ENGINES["rust"] = dict(build=build_rust,
                                   cmd=lambda d, sink: [b, d, "--out", os.path.join(d, "o"),
                                                        "--policy", os.path.join(d, "pol")]
                                   + (["--gate-json", os.path.join(d, "g.json")] if sink else []))
            break
    if "rust" in ENGINES:
        rq = None
        for cand in ("target/release/candor-query", "target/debug/candor-query"):
            c = os.path.join(_p("CANDOR", "candor-rust"), cand)
            if os.path.exists(c):
                rq = c
                break
        if rq:
            ENGINES["rust"]["query"] = lambda d, rep, verb, rq=rq: [
                rq, verb, "--report", rep, "--policy", os.path.join(d, "pol"), "--strict"]
    ts = _p("CANDOR_TS", "candor-ts")
    if os.path.exists(os.path.join(ts, "scan.mjs")):
        ENGINES["ts"] = dict(build=build_ts,
                             cmd=lambda d, sink: ["node", os.path.join(ts, "scan.mjs"),
                                                  os.path.join(d, "tsconfig.json"),
                                                  "--out", os.path.join(d, "o"),
                                                  "--policy", os.path.join(d, "pol")]
                             + (["--gate-json", os.path.join(d, "g.json")] if sink else []))
    if "ts" in ENGINES:
        ENGINES["ts"]["query"] = lambda d, rep, verb, ts=ts: [
            "node", os.path.join(ts, "query.mjs"), verb, "--report", rep,
            "--policy", os.path.join(d, "pol"), "--strict"]
    jv = _p("CANDOR_JAVA", "candor-java")
    jars = []
    libs = os.path.join(jv, "build", "libs")
    if os.path.isdir(libs):
        jars = sorted((os.path.join(libs, x) for x in os.listdir(libs) if x.endswith("-all.jar")),
                      key=os.path.getmtime, reverse=True)
    if jars and shutil.which("javac"):
        jar = jars[0]
        ENGINES["java"] = dict(build=build_java,
                               cmd=lambda d, sink: ["java", "-jar", jar, d,
                                                    "--json", os.path.join(d, "o.json"),
                                                    "--policy", os.path.join(d, "pol")]
                               + (["--gate-json", os.path.join(d, "g.json")] if sink else []))
    if "java" in ENGINES and jars:
        ENGINES["java"]["query"] = lambda d, rep, verb, jar=jars[0]: [
            "java", "-jar", jar, verb, "--report", rep, "--policy", os.path.join(d, "pol"), "--strict"]
    sw = _p("CANDOR_SWIFT", "candor-swift")
    swb = os.path.join(sw, ".build", "debug", "candor-swift")
    if os.path.exists(swb):
        ENGINES["swift"] = dict(query=lambda d, rep, verb, swb=swb: [
                                    swb, verb, "--report", rep, "--policy", os.path.join(d, "pol"),
                                    "--strict"],
                                build=build_swift,
                                cmd=lambda d, sink: [swb, d, "--out", os.path.join(d, "o"),
                                                     "--policy", os.path.join(d, "pol")]
                                + (["--gate-json", os.path.join(d, "g.json")] if sink else []))


def judge(engine, shape, placed_out, sink, parent=None):
    e = ENGINES[engine]
    d = e["build"](parent or WORK, shape, placed_out)
    rc, out = run(e["cmd"](d, sink), cwd=d)
    # PROBE HOOK (conformance/probe_check.py). Under CANDOR_PROBE_FAULT this corrupts the PEEK's answer —
    # the exact defect the matrix exists to catch, a peek that drops a finding the gate would make — so
    # the suite can confirm this property still discriminates instead of trusting that it does. Without
    # it this generator was in neither COVERED nor UNCOVERED, i.e. invisible to the check that asks
    # whether a property can fail, which is the state every vacuous cell in here started from.
    if os.environ.get("CANDOR_PROBE_FAULT") and placed_out and rc == 2:
        print("PROBE: peek verdict forced to 0 (simulating a peek that drops the finding)")
        rc = 0
    return rc, out, d


def report_at(d):
    """The report the run just wrote, whatever the engine names it."""
    cands = []
    for root, _dirs, files in os.walk(d):
        for f in files:
            if not f.endswith(".json"):
                continue
            if any(k in f for k in ("callgraph", "hierarchy", "locs", "gate", "tsconfig")):
                continue
            cands.append(os.path.join(root, f))
    cands.sort(key=os.path.getmtime, reverse=True)
    for c in cands:
        try:
            j = json.load(open(c))
        except Exception:                                  # noqa: BLE001
            continue
        if isinstance(j, dict) and "functions" in j:
            return c, j
    return None, None


def main():
    global WORK
    keep = "--keep" in sys.argv
    only = None
    if "--engine" in sys.argv:
        only = sys.argv[sys.argv.index("--engine") + 1]
    discover()
    if not ENGINES:
        print("  gen_policy_matrix: NO ENGINE FOUND — set CANDOR / CANDOR_TS / CANDOR_SWIFT")
        return 2
    for name in ("rust", "ts", "java", "swift"):
        if name not in ENGINES:
            print(f"  {name:6} -> SKIP     (engine not built — NOT asked)")
    WORK = tempfile.mkdtemp(prefix="candor-polmatrix-")
    bad = 0
    cells = 0
    for engine in sorted(ENGINES):
        if only and engine != only:
            continue
        # ── CALIBRATION FLOOR — run BEFORE any cell of this engine is believed. ────────────────────
        # Every arm below compares the peek to the gate, so an engine that sees NOTHING agrees with
        # itself perfectly: a stub classifying nothing and exiting 0 passes every cell, and so does one
        # answering 2 for everything. That is not hypothetical — the swift fixture in this very file
        # once inferred `Unknown` instead of `Net`, so every destination-class cell agreed 0<->0 while
        # exercising nothing, and the repair was a one-off manual edit that left no guard behind.
        # This is that guard: the bare `deny Net` cell MUST gate RED in scope, and the in-scope report
        # MUST carry Net on the fixture function. If either fails, this engine's whole column is
        # UNCALIBRATED and its greens mean nothing.
        cal_rc, _cal_out, cal_dir = judge(engine, SHAPES[0], placed_out=False, sink=True)
        _crp, cal_doc = report_at(cal_dir)
        cal_net = any("Net" in (f.get("inferred") or [])
                      for f in (cal_doc or {}).get("functions") or [])
        if cal_rc != 1 or not cal_net:
            bad += 1
            print(f"  {engine:6} CALIBRATION      the in-scope `deny Net` fixture gated {cal_rc} "
                  f"(want 1) and {'carries' if cal_net else 'does NOT carry'} Net in its report — this "
                  f"engine's column tests NOTHING until that holds, because every arm compares the peek "
                  f"to a gate that is not firing")
            continue
        for shape in SHAPES:
            cells += 1
            gate_rc, gate_out, _gd = judge(engine, shape, placed_out=False, sink=True)
            peek_rc, peek_out, peek_dir = judge(engine, shape, placed_out=True, sink=True)
            # THE AGREEMENT INVARIANT. The gate is the oracle: whatever it decides about the in-scope
            # copy, the peek must decide about the identical out-of-scope copy. 1 <-> 2 because the
            # gate JUDGED it and the peek did not; 0 <-> 0 because neither found anything to say.
            want = {0: 0, 1: 2, 2: 2}.get(gate_rc)
            if peek_rc == 2 and want == 2:
                # "I refused because incomplete" and "I found the finding" are both exit 2. Compare the
                # EVIDENCE too, or a peek that always answers 2 with an empty block passes every cell.
                _rp2, d2 = report_at(peek_dir)
                if not ((d2 or {}).get("outOfScope") or []):
                    bad += 1
                    print(f"  {engine:6} {shape['id']:16} EMPTY-FINDING  exit 2 with an EMPTY "
                          f"`outOfScope` — the exit is right for the wrong reason, which is how a peek "
                          f"that refuses everything passes a matrix that only compares exit codes")
                    continue
            if peek_rc != want:
                bad += 1
                print(f"  {engine:6} {shape['id']:16} DISAGREE  in-scope gate={gate_rc} -> peek should be "
                      f"{want}, got {peek_rc}")
                print(f"         policy: {shape['policy'].strip()!r}"
                      + (f"  config: {shape['needs'].strip()!r}" if shape["needs"] else ""))
                continue
            # SINK INDEPENDENCE — same tree, same policy, no `--gate-json`.
            nosink_rc, _, _ = judge(engine, shape, placed_out=True, sink=False)
            if nosink_rc != peek_rc:
                bad += 1
                print(f"  {engine:6} {shape['id']:16} SINK-DEPENDENT  exit {peek_rc} with --gate-json, "
                      f"{nosink_rc} without — a machine sink must not decide a verdict")

            # ── ATTRIBUTION — a finding must name a file that HOLDS the effect. ────────────────────
            # The verdict is what an operator acts on: the release notes say "read the ⚠ lines, bring
            # those files into scope". A finding naming a file with no effect in it makes that remedy
            # impossible to follow, and a fuzzy basename match is how that happens (candor-ts attributed
            # `noop-delay.js`'s finding to `delay.js`, and charged `.d.ts` declaration files with Env).
            if peek_rc == 2:
                _rp, doc = report_at(peek_dir)
                for f in (doc or {}).get("outOfScope") or []:
                    named = os.path.join(peek_dir, f.get("path") or "")
                    if not f.get("path") or not os.path.exists(named):
                        bad += 1
                        print(f"  {engine:6} {shape['id']:16} ATTRIBUTION  finding names "
                              f"{f.get('path')!r}, which is not a file in the scanned tree")
                        break
                    # TEXT SOURCES ONLY. An archive legitimately names the .jar/.zip as the locator —
                    # the effect lives in a compressed member, so the marker is not findable by reading
                    # the file, and requiring it would fail candor-java for being right. (This check
                    # asserted it anyway on first run: the generator's own false positive, caught by
                    # reading the finding rather than trusting the red.)
                    if os.path.splitext(named)[1] in (".jar", ".zip", ".class"):
                        continue
                    body_marker = "partner.example"
                    if body_marker not in open(named, errors="ignore").read():
                        bad += 1
                        print(f"  {engine:6} {shape['id']:16} ATTRIBUTION  finding names "
                              f"{f.get('path')!r}, which does not contain the effect — the remedy the "
                              f"notes advertise cannot be followed from it")
                        break

            # ── PATH INDEPENDENCE — the same tree, built under a differently-NAMED parent. ─────────
            # A verdict must not depend on where the repo was cloned. candor-ts evaluated rule scopes
            # against the child scan's ABSOLUTE paths, so `deny Net src` armed on any checkout whose path
            # contained a `src` segment — and CI checkouts live under names nobody chose (Bitbucket uses
            # `agent/build`). Only meaningful for scoped shapes, which is where it bites.
            if shape["id"] == "bare-deny":
                # A scope naming a CHECKOUT DIRECTORY, which is in no module graph — a correct engine binds
                # nothing under either parent. An engine matching scopes against ABSOLUTE paths binds under
                # the parent whose name it matches and not the other, which is a verdict decided by where
                # CI happened to clone. Generated per parent rather than listed in SHAPES: the policy text
                # has to NAME the directory, so it cannot be a static row.
                seen = {}
                # ONE fixed scope name, run under two differently-named parents. Generating the policy
                # PER PARENT was the bug: it named whichever directory it ran under, so an absolute-path
                # matcher bound under both and the exits agreed — the arm written to pin that defect
                # could not fail. `aaa_checkout_one` is a segment of one parent and not the other, so a
                # path matcher arms once and a correct engine arms never.
                scoped = dict(shape, id="path-scope", policy="deny Net aaa_checkout_one\n")
                for pname in ("aaa_checkout_one", "zzz_checkout_two"):
                    par = os.path.join(WORK, pname)
                    os.makedirs(par, exist_ok=True)
                    rc_p, _, _ = judge(engine, scoped, placed_out=True, sink=True, parent=par)
                    seen[pname] = rc_p
                if len(set(seen.values())) != 1:
                    bad += 1
                    print(f"  {engine:6} path-scope       PATH-DEPENDENT  {seen} — a rule scoped to a "
                          f"checkout DIRECTORY armed under the parent whose name it matched; the verdict "
                          f"depends on where the tree was cloned")

            q = ENGINES[engine].get("query")
            # Resolved ONCE, before the corrupt variants are written beside it — `report_at` picks the
            # newest report in the directory, so writing a corrupt one first made the advisory arm below
            # test THAT file and report a failure the engine had not made. The generator's own artefact,
            # found by reproducing an ADVISORY red by hand and getting exit 2.
            good_rp, good_doc = report_at(peek_dir) if peek_rc == 2 else (None, None)
            # ── CORRUPT KEY — fail closed on the GATE and on every advisory verb beside it. ────────
            # `outOfScope` non-emptiness is a fail-closed trigger, so a present-but-garbled key coerced to
            # its empty default becomes the claim "I looked and nothing was there". Both positions are
            # tested because the two engines found holed in review were holed in DIFFERENT ones, each
            # passing the shape the other refused.
            if peek_rc == 2 and q:
                rp, doc = good_rp, good_doc
                if rp and doc is not None:
                    for label, bad_val in (("not-a-list", "oops"), ("bad-element", [123])):
                        cp = os.path.join(peek_dir, f"corrupt_{label}.json")
                        json.dump({**doc, "outOfScope": bad_val}, open(cp, "w"))
                        grc, _ = run(q(peek_dir, cp, "unverified"), cwd=peek_dir)
                        if grc == 0:
                            bad += 1
                            print(f"  {engine:6} {shape['id']:16} CORRUPT-OPEN  `unverified --strict` "
                                  f"exits 0 over a report whose `outOfScope` is {label} — read as empty, "
                                  f"a garbled key turns NOT-certified into certified")
                            break

            # ── ADVISORY VERBS — never LESS pessimistic than the gate over the same bytes (⟨0.24⟩). ─
            if q and peek_rc == 2:
                rp = good_rp
                if rp:
                    for verb in ("unverified", "fix-gate"):
                        arc, _ = run(q(peek_dir, rp, verb), cwd=peek_dir)
                        if arc == 0:
                            bad += 1
                            print(f"  {engine:6} {shape['id']:16} ADVISORY  `{verb} --strict` exits 0 over "
                                  f"the report the gate refuses at 2")
                            break
    print(f"  policy matrix: {cells} cell(s) over {len(ENGINES) if not only else 1} engine(s), "
          f"{bad} disagreement(s)")
    if keep:
        print(f"  workspace kept: {WORK}")
    else:
        shutil.rmtree(WORK, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
