#!/usr/bin/env python3
"""
CROSS-ENGINE COMPLETENESS-MANIFEST differential (FOUR-WAY) for the candor effect-checker family.

The completeness manifest (COMPLETENESS-MANIFEST-DESIGN.md, SPEC §2 + §3.3.1 ⟨0.21⟩) makes "absent ⇒ pure"
a BACKED convention and makes incompleteness MACHINE-legible. This pins the three gaps four-way over an
equivalent fixture in every engine: an effectful fn, a plain pure fn, a TRULY ISOLATED pure fn (uncalled,
calling nothing), and a SEPARATE file that fails to parse.

THE PROPERTIES (per engine):
  * Gap 1 — the report envelope carries `analyzed: {count, digest}`; the analyzed universe INCLUDES pure
    leaves, so `analyzed.count − |functions|` = the pure count ≥ 2 (the plain + the isolated pure fn). The
    digest is stable across a same-input re-scan.
  * Gap 2 — the parse-failing file appears in the report's `unanalyzed`; and a CONFIGURED gate over it FAILS
    CLOSED: exit 2 with a verdict `{ok:false, incomplete:true, unanalyzed:[…]}` (never a green gate over
    unseen code). The count also rides the verdict (`analyzed:{count}`).
  * Gap 3 — the isolated pure fn is a CALL-GRAPH NODE (empty adjacency), so its membership reads
    analyzed-pure, never never-seen.

A divergence — an engine whose analyzed count omits pure leaves, whose gate reads GREEN over the unparsed
file (the machine-consumer cardinal sin), or that drops the isolated leaf — is a DISAGREEMENT and exits
nonzero, named per engine.

Engine resolution / build / SKIP discipline mirror gen_netclass.py / gen_masking.py exactly (CANDOR /
CANDOR_JAVA / CANDOR_TS / CANDOR_SWIFT, the prebuilt CANDOR_SCAN_BIN / CANDOR_JAVA_JAR).

USAGE:
    python3 gen_completeness.py            # run every engine, exit nonzero on any disagreement
    python3 gen_completeness.py --keep     # keep the generated temp workspace (prints its path)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def envdir(var, default_rel):
    return os.environ.get(var, os.path.normpath(os.path.join(HERE, default_rel)))


CANDOR = envdir("CANDOR", "../../candor-rust")
CANDOR_JAVA = envdir("CANDOR_JAVA", "../../candor-java")
CANDOR_TS = envdir("CANDOR_TS", "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def _glob(d, suffix):
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suffix)]


# =====================================================================================================
# The per-language fixture: effectful() + pure() + isolatedPure() (uncalled, calls nothing) + a BROKEN
# file that fails to parse. The effect is Fs (std-only, the gen_masking vocabulary). The isolated fn is a
# separate top-level fn nothing calls — the Gap-3 case.
# =====================================================================================================
def write_rust(d):
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    open(os.path.join(d, "Cargo.toml"), "w").write('[package]\nname = "cm"\nversion = "0.0.0"\nedition = "2021"\n')
    open(os.path.join(d, "src", "lib.rs"), "w").write(
        "pub mod broken;\n"
        'pub fn effectful() { let _ = std::fs::read("/tmp/x"); }\n'
        "pub fn plain_pure(x: i32) -> i32 { x + 1 }\n"
        "pub fn isolated_pure(y: i32) -> i32 { y * 2 }\n")
    # a file syn cannot parse
    open(os.path.join(d, "src", "broken.rs"), "w").write("pub fn broken( { not valid rust @@@\n")


def write_java(d):
    # java reads bytecode: compile the good class, then drop a corrupt .class alongside.
    src = os.path.join(d, "src")
    os.makedirs(os.path.join(src, "app"), exist_ok=True)
    open(os.path.join(src, "app", "A.java"), "w").write(
        "package app;\npublic class A {\n"
        '  public void effectful() throws Exception { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); }\n'
        "  public int plainPure(int x){ return x + 1; }\n"
        "  public int isolatedPure(int y){ return y * 2; }\n"
        "}\n")


def write_ts(d):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "package.json"), "w").write('{"name":"cm","version":"0.0.0"}\n')
    open(os.path.join(d, "good.ts"), "w").write(
        'import * as fsm from "node:fs";\n'
        'export function effectful(): void { fsm.readFileSync("/tmp/x"); }\n'
        "export function plainPure(x: number): number { return x + 1; }\n"
        "export function isolatedPure(y: number): number { return y * 2; }\n")
    open(os.path.join(d, "broken.ts"), "w").write("export function broken( { this is not valid ts @@@\n")


def write_swift(d):
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "good.swift"), "w").write(
        "import Foundation\n"
        'func effectful() { _ = FileManager.default.contents(atPath: "/tmp/x") }\n'
        "func plainPure(_ x: Int) -> Int { return x + 1 }\n"
        "func isolatedPure(_ y: Int) -> Int { return y * 2 }\n")
    # SwiftSyntax is error-tolerant (never fails to parse); the "unanalyzed" case is an UNREADABLE file.
    with open(os.path.join(d, "unreadable.swift"), "wb") as f:
        f.write(b"\xff\xfe\x00 invalid utf-8 \xff\xff func x() {}\n")


# =====================================================================================================
# the engines — resolve/build like gen_netclass, plus `report(dir) -> dict` (parse --json) and
# `gate(dir, pol) -> (exit_code, verdict_dict|None)`.
# =====================================================================================================
class Engine:
    name = "?"

    def __init__(self):
        self.present = False
        self.ok = False
        self.err = None

    def prepare(self, ws):
        raise NotImplementedError

    def write_fixture(self, ws):
        raise NotImplementedError

    def report(self, ws):
        raise NotImplementedError

    def gate(self, ws, pol):
        raise NotImplementedError


def _load_report_stdout(out):
    try:
        return json.loads(out)
    except Exception:
        return None


class RustEngine(Engine):
    name = "rust"

    def prepare(self, ws):
        self.bin = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
        if not os.path.exists(self.bin):
            print("  [rust]  building candor-scan...")
            b = run(["cargo", "build", "-q", "--manifest-path", os.path.join(CANDOR, "Cargo.toml"), "-p", "candor-scan"])
            if b.returncode != 0:
                self.present, self.err = True, "cargo build failed (set CANDOR or CANDOR_SCAN_BIN)"
                return
        if not os.path.exists(self.bin):
            self.err = f"no candor-scan at {self.bin}"
            return
        self.present = self.ok = True

    def write_fixture(self, ws):
        self.d = os.path.join(ws, "rust")
        write_rust(self.d)

    def report(self, ws):
        return _load_report_stdout(run([self.bin, self.d, "--json"]).stdout.decode())

    def gate(self, ws, pol):
        vpath = os.path.join(self.d, "v.json")
        env = dict(os.environ, CANDOR_POLICY=pol)
        rc = run([self.bin, self.d, "--gate-json", vpath], env=env).returncode
        v = json.load(open(vpath)) if os.path.exists(vpath) else None
        return rc, v


class JavaEngine(Engine):
    name = "java"

    def prepare(self, ws):
        self.jar = os.environ.get("CANDOR_JAVA_JAR")
        if not self.jar:
            cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
            if not cands:
                print("  [java]  building candor-java (shadowJar)...")
                b = run(["./gradlew", "-q", "shadowJar"], cwd=CANDOR_JAVA)
                if b.returncode != 0:
                    self.present, self.err = True, "gradlew shadowJar failed (set CANDOR_JAVA or CANDOR_JAVA_JAR)"
                    return
                cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
            self.jar = max(cands, key=os.path.getmtime) if cands else None
        if not self.jar or not os.path.exists(self.jar):
            self.err = "no candor-java jar"
            return
        if not shutil.which("javac"):
            self.err = "no javac on PATH"
            return
        self.present = self.ok = True

    def write_fixture(self, ws):
        self.d = os.path.join(ws, "java")
        write_java(self.d)
        self.cls = os.path.join(self.d, "cls")
        os.makedirs(self.cls, exist_ok=True)
        c = run(["javac", "-d", self.cls, os.path.join(self.d, "src", "app", "A.java")])
        if c.returncode != 0:
            raise RuntimeError("javac failed: " + c.stderr.decode()[:300])
        # a class ASM cannot parse — java's "unanalyzed" case (a skipped .class).
        with open(os.path.join(self.cls, "Corrupt.class"), "wb") as f:
            f.write(bytes([0xca, 0xfe, 0xba, 0xbe, 0, 0, 0, 0, 9]))

    def report(self, ws):
        rpath = os.path.join(self.d, "r.json")
        run(["java", "-jar", self.jar, self.cls, "--json", rpath])
        return json.load(open(rpath)) if os.path.exists(rpath) else None

    def gate(self, ws, pol):
        vpath = os.path.join(self.d, "v.json")
        env = dict(os.environ, CANDOR_POLICY=pol)
        rc = run(["java", "-jar", self.jar, self.cls, "--gate-json", vpath], env=env).returncode
        v = json.load(open(vpath)) if os.path.exists(vpath) else None
        return rc, v


class TsEngine(Engine):
    name = "ts"

    def prepare(self, ws):
        if not shutil.which("node") or not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")):
            self.err = "no node / scan.mjs (set CANDOR_TS)"
            return
        if not os.path.isdir(os.path.join(CANDOR_TS, "node_modules")):
            run(["npm", "install", "--no-fund", "--no-audit"], cwd=CANDOR_TS)
        self.present = self.ok = True

    def write_fixture(self, ws):
        self.d = os.path.join(ws, "ts")
        write_ts(self.d)

    def report(self, ws):
        return _load_report_stdout(run(["node", os.path.join(CANDOR_TS, "scan.mjs"), self.d, "--json"]).stdout.decode())

    def gate(self, ws, pol):
        vpath = os.path.join(self.d, "v.json")
        env = dict(os.environ, CANDOR_POLICY=pol)
        rc = run(["node", os.path.join(CANDOR_TS, "scan.mjs"), self.d, "--gate-json", vpath], env=env).returncode
        v = json.load(open(vpath)) if os.path.exists(vpath) else None
        return rc, v


class SwiftEngine(Engine):
    name = "swift"

    def prepare(self, ws):
        if not shutil.which("swift") or not os.path.exists(os.path.join(CANDOR_SWIFT, "Package.swift")):
            self.err = "no swift toolchain / Package.swift (set CANDOR_SWIFT)"
            return
        self.bin = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
        if not os.path.exists(self.bin):
            print("  [swift] swift build...")
            b = run(["swift", "build"], cwd=CANDOR_SWIFT)
            if b.returncode != 0 or not os.path.exists(self.bin):
                self.present, self.err = True, "swift build failed"
                return
        self.present = self.ok = True

    def write_fixture(self, ws):
        self.d = os.path.join(ws, "swift")
        write_swift(self.d)

    def report(self, ws):
        return _load_report_stdout(run([self.bin, self.d, "--json"]).stdout.decode())

    def gate(self, ws, pol):
        vpath = os.path.join(self.d, "v.json")
        rc = run([self.bin, self.d, "--policy", pol, "--gate-json", vpath]).returncode
        v = json.load(open(vpath)) if os.path.exists(vpath) else None
        return rc, v


ENGINES = [RustEngine(), JavaEngine(), TsEngine(), SwiftEngine()]


def check_engine(eng, ws):
    """Return (ok: bool, notes: list[str]) — the four completeness properties for one engine."""
    notes = []
    ok = True

    def fail(msg):
        nonlocal ok
        ok = False
        notes.append("FAIL: " + msg)

    rep = eng.report(ws)
    if not isinstance(rep, dict):
        return False, ["FAIL: no parseable --json report"]
    analyzed = rep.get("analyzed")
    functions = rep.get("functions", [])
    unanalyzed = rep.get("unanalyzed", [])
    # Gap 1 — analyzed present, pure count ≥ 2 (plain_pure + isolated_pure are analyzed-but-omitted).
    if not isinstance(analyzed, dict) or "count" not in analyzed or not analyzed.get("digest"):
        fail(f"report has no `analyzed:{{count,digest}}` (got {analyzed})")
    else:
        pure = analyzed["count"] - len(functions)
        if pure < 2:
            fail(f"pure count = analyzed.count({analyzed['count']}) − |functions|({len(functions)}) = {pure}, want ≥ 2 (the plain + isolated pure fns)")
        else:
            notes.append(f"analyzed.count={analyzed['count']} |functions|={len(functions)} pure={pure} digest={analyzed['digest']}")
    # Gap 2 (report) — the broken/corrupt/unreadable file is in `unanalyzed`.
    if not unanalyzed:
        fail("the un-analyzable file is NOT in the report's `unanalyzed` (a machine sees a complete-looking report)")
    else:
        notes.append(f"unanalyzed={[u.get('path','?').split('/')[-1] for u in unanalyzed]}")
    # Gap 1 — the digest is stable across a same-input re-scan.
    rep2 = eng.report(ws)
    if isinstance(rep2, dict) and isinstance(rep2.get("analyzed"), dict) and isinstance(analyzed, dict):
        if rep2["analyzed"].get("digest") != analyzed.get("digest"):
            fail("the analyzed digest is NOT stable across a same-input re-scan")

    # Gap 2 (gate) — a CONFIGURED, non-firing gate over the incomplete scan fails closed: exit 2 + verdict
    # {ok:false, incomplete:true, unanalyzed:[…]}. `deny Db` does not fire (the fixture performs Fs).
    pol = os.path.join(ws, "cm.policy")
    if not os.path.exists(pol):
        open(pol, "w").write("deny Db\n")
    rc, v = eng.gate(ws, pol)
    if rc != 2:
        fail(f"a gate over unanalyzed code must exit 2 (could-not-evaluate); got exit {rc}")
    if not isinstance(v, dict):
        fail("no machine-legible verdict on the incomplete gate (exit 2 wrote nothing — the machine can't learn why)")
    else:
        if v.get("ok") is not False:
            fail(f"incomplete verdict ok must be false, got {v.get('ok')}")
        if v.get("incomplete") is not True:
            fail("incomplete verdict must carry incomplete:true")
        if not v.get("unanalyzed"):
            fail("incomplete verdict must carry the `unanalyzed` list (a machine learns WHY)")
        if not isinstance(v.get("analyzed"), dict) or "count" not in v.get("analyzed", {}):
            fail("the verdict must carry analyzed:{count}")
        else:
            notes.append(f"verdict ok={v.get('ok')} incomplete={v.get('incomplete')} analyzed.count={v['analyzed']['count']}")
    return ok, notes


def main():
    keep = "--keep" in sys.argv[1:]
    print("=" * 100)
    print("CROSS-ENGINE COMPLETENESS-MANIFEST differential (FOUR-WAY) — analyzed / unanalyzed (SPEC §2 + §3.3.1)")
    print("  property: analyzed.count includes pure leaves (pure = count − |functions| ≥ 2); the unparsed file")
    print("            is machine-legible in the report AND the verdict; a gate over it fails closed (exit 2).")
    print("=" * 100)

    ws = tempfile.mkdtemp(prefix="candor-completeness-")
    print("\npreparing each engine (resolve / build)...")
    available = []
    skipped, failed = {}, {}
    for eng in ENGINES:
        eng.prepare(ws)
        if not eng.present:
            skipped[eng.name] = eng.err
            print(f"  {eng.name:6s} SKIPPED -- {eng.err}")
        elif not eng.ok:
            failed[eng.name] = eng.err
            print(f"  {eng.name:6s} FAILED  -- present but broken: {eng.err}")
        else:
            try:
                eng.write_fixture(ws)
                available.append(eng)
                print(f"  {eng.name:6s} ok")
            except Exception as e:
                failed[eng.name] = str(e)
                print(f"  {eng.name:6s} FAILED  -- fixture: {e}")

    rc = 2 if failed else 0
    print("\nchecking the completeness properties per engine...")
    disagreements = []
    for eng in available:
        try:
            okk, notes = check_engine(eng, ws)
        except Exception as e:
            okk, notes = False, ["FAIL: " + str(e)]
        mark = "OK" if okk else "DISAGREE"
        print(f"\n  [{eng.name}] {mark}")
        for n in notes:
            print(f"     {n}")
        if not okk:
            disagreements.append(eng.name)

    print()
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print(f"FAIL (strict): engine '{e}' REQUIRED but absent -- {why}")
        rc = 2
    if failed:
        for e, why in failed.items():
            print(f"FAIL: engine '{e}' present but broken -- {why}")
    if disagreements:
        rc = rc or 1
        print(f"{len(disagreements)} ENGINE(S) DISAGREE with the completeness-manifest contract: {', '.join(disagreements)}")

    n = len(available)
    if rc == 0:
        print(f"\nCOMPLETENESS-MANIFEST differential: OK -- {n} engine(s) all carry `analyzed` (pure leaves included),")
        print("disclose the unparsed unit in the report + verdict, and fail a configured gate closed (exit 2).")
    else:
        print("\nCOMPLETENESS-MANIFEST differential: FAILED")

    if keep:
        print(f"\n(workspace kept: {ws})")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
