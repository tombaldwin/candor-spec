#!/usr/bin/env python3
"""
CROSS-ENGINE NET DESTINATION-CLASS differential (FOUR-WAY) for the candor effect-checker family.

The §6.2 `Net[dest…]` GRAMMAR is diffed by run.sh PART 4 (parsepolicy). This is its sibling on the
*applied* axis (like gen_policy_match.py for the base matchers): given the SAME `deny Net[unknown-host]`
security policy and an EQUIVALENT fixture, do all four engines reach the SAME gate verdict — and is that
verdict FAIL-CLOSED? (NET-DESTINATION-CLASS-DESIGN.md.)

THE CARDINAL PROPERTY the security gate must hold, four-way:
  * a `known-telemetry` host (curated TELEMETRY_HOSTS — sentry.io) under `deny Net[unknown-host]`  -> PASS
  * a `known-partner`   host (a MODEL host, api.openai.com)         under `deny Net[unknown-host]`  -> PASS
  * a config `net-partner` host (api.stripe.com + .candor/config)   under `deny Net[unknown-host]`  -> PASS
  * an `unknown-host`   (evil.example.com — on NEITHER list)        under `deny Net[unknown-host]`  -> FAIL
  * a RUNTIME-masked host (no visible literal → fail-closed unknown-host) under the same rule      -> FAIL
  * ANY of the above under a BARE `deny Net` (all destinations, backward-compat)                    -> FAIL
An engine that PASSES the exfil / runtime case is the cardinal sin (an exfiltration Net slips the security
gate); one that FAILS a telemetry / partner case is a false positive. Either is a DISAGREEMENT and exits
nonzero, named per engine — the same discipline as gen_policy_match.py / gen_masking.py.

The Net host-establishing forms are shared VERBATIM with gen_masking.py / gen_policy_match.py (TcpStream::
connect / java.net.Socket / net.connect / NWConnection), so the host literal is captured identically; the
runtime case derives the host from a function PARAMETER, so the surface is genuinely incomplete and the
engine fails closed to unknown-host.

USAGE:
    python3 gen_netclass.py            # run every case, exit nonzero on any disagreement
    python3 gen_netclass.py --keep     # keep the generated temp workspace (prints its path)

Engine resolution / build / SKIP discipline mirror gen_masking.py / gen_policy_match.py exactly (CANDOR /
CANDOR_JAVA / CANDOR_TS / CANDOR_SWIFT, the prebuilt CANDOR_SCAN_BIN / CANDOR_JAVA_JAR).
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def envdir(var, default_rel):
    return os.environ.get(var, os.path.normpath(os.path.join(HERE, default_rel)))


CANDOR       = envdir("CANDOR",       "../../candor-rust")
CANDOR_JAVA  = envdir("CANDOR_JAVA",  "../../candor-java")
CANDOR_TS    = envdir("CANDOR_TS",    "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")


# =====================================================================================================
# CASES -- each connects a single fn `entry` to ONE host and gates it. `expect` is the verdict the SPEC's
# destination-class rules dictate. `config`, when set, is written to `.candor/config` in the fixture cell
# (an ancestor of every engine's scan target) so `net-partner` is discovered. The runtime case derives the
# host from a param `m` (no visible literal -> fail-closed unknown-host), the others use a static literal.
# =====================================================================================================
def _bodies(host):
    """The four-language `entry` that connects to a STATIC host literal (host captured verbatim)."""
    return dict(
        rust=f'pub fn entry() {{{{ let _ = std::net::TcpStream::connect("{host}:80"); }}}}',
        java=f'  public static void entry() throws Exception {{{{ new java.net.Socket("{host}", 80); }}}}',
        ts=f'export function entry(): void {{{{ netm.connect(80, "{host}"); }}}}',
        swift=f'func entry() {{{{ _ = NWConnection(host: "{host}", port: 80, using: .tcp) }}}}',
    )


# the RUNTIME-masked host: derived from a param, so no literal is visible -> the Net surface is incomplete
# and the engine fails closed to unknown-host (never guessed onto a safe class).
_RUNTIME_BODIES = dict(
    rust='pub fn entry(m: &str) {{ let h = format!("{{}}.example", m); let _ = std::net::TcpStream::connect(&h); }}',
    java='  public static void entry(String m) throws Exception {{ new java.net.Socket(m + ".example", 80); }}',
    ts='export function entry(m: string): void {{ netm.connect(80, m + ".example"); }}',
    swift='func entry(_ m: String) {{ _ = NWConnection(host: NWEndpoint.Host(m + ".example"), port: 80, using: .tcp) }}',
)


def _case(id, rule, policy, expect, host=None, runtime=False, config=None):
    d = dict(id=id, rule=rule, policy=policy, expect=expect, config=config)
    d.update(_RUNTIME_BODIES if runtime else _bodies(host))
    return d


CASES = [
    _case("telemetry_tolerated", "known-telemetry (sentry.io) tolerated", "deny Net[unknown-host]",
          "pass", host="sentry.io"),
    _case("posthog_telemetry_tolerated", "known-telemetry (posthog.com subdomain, 0.20.1 corpus-grown) tolerated",
          "deny Net[unknown-host]", "pass", host="us.i.posthog.com"),
    _case("model_partner_tolerated", "known-partner (model host api.openai.com) tolerated", "deny Net[unknown-host]",
          "pass", host="api.openai.com"),
    _case("config_partner_tolerated", "config net-partner (api.stripe.com) tolerated", "deny Net[unknown-host]",
          "pass", host="api.stripe.com", config="net-partner api.stripe.com"),
    _case("exfil_denied", "unknown-host (evil.example.com) DENIED", "deny Net[unknown-host]",
          "fail", host="evil.example.com"),
    _case("runtime_failclosed", "runtime-masked host fails CLOSED to unknown-host", "deny Net[unknown-host]",
          "fail", runtime=True),
    _case("bare_deny_all", "bare `deny Net` denies ALL destinations (backward-compat)", "deny Net",
          "fail", host="sentry.io"),
]


# =====================================================================================================
# rendering one CASE into a per-language source tree under <ws>/<lang>/<case_id>/. Mirrors gen_masking.py /
# gen_policy_match.py; when a case declares `config`, it is written to `.candor/config` in the CELL dir (an
# ancestor of every engine's scan target — rust/ts dir, swift file's dir, java's compiled `cls` subdir).
# =====================================================================================================
def _write_config(cell_dir, case):
    if case.get("config"):
        os.makedirs(os.path.join(cell_dir, ".candor"), exist_ok=True)
        with open(os.path.join(cell_dir, ".candor", "config"), "w") as f:
            f.write(case["config"] + "\n")


def _rust_tree(d, case):
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    with open(os.path.join(d, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "netclass"\nversion = "0.0.0"\nedition = "2021"\n')
    with open(os.path.join(d, "src", "lib.rs"), "w") as f:
        f.write("// GENERATED by gen_netclass.py -- do not edit.\n" + case["rust"].format() + "\n")
    _write_config(d, case)


def _java_tree(d, case):
    os.makedirs(os.path.join(d, "q"), exist_ok=True)
    with open(os.path.join(d, "q", "E.java"), "w") as f:
        f.write("// GENERATED by gen_netclass.py -- do not edit.\n")
        f.write("package q;\npublic class E {\n" + case["java"].format() + "\n}\n")
    _write_config(d, case)


def _ts_tree(d, case):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "package.json"), "w") as f:
        f.write('{"name":"netclass","version":"0.0.0"}\n')
    with open(os.path.join(d, "cases.ts"), "w") as f:
        f.write("// GENERATED by gen_netclass.py -- do not edit.\n")
        f.write('import * as netm from "node:net";\n\n')
        f.write(case["ts"].format() + "\n")
    _write_config(d, case)


def _swift_file(d, case):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "cases.swift")
    with open(p, "w") as f:
        f.write("// GENERATED by gen_netclass.py -- do not edit.\n")
        f.write("import Foundation\nimport Network\n\n")
        f.write(case["swift"].format() + "\n")
    _write_config(d, case)
    return p


def write_sources(ws):
    for case in CASES:
        cell = case["id"]
        _rust_tree(os.path.join(ws, "rust", cell), case)
        _java_tree(os.path.join(ws, "java", cell), case)
        _ts_tree(os.path.join(ws, "ts", cell), case)
        _swift_file(os.path.join(ws, "swift", cell), case)


def policy_path(ws, case):
    os.makedirs(os.path.join(ws, "pol"), exist_ok=True)
    p = os.path.join(ws, "pol", f"{case['id']}.policy")
    with open(p, "w") as f:
        f.write(case["policy"] + "\n")
    return p


# =====================================================================================================
# the engines -- IDENTICAL to gen_masking.py / gen_policy_match.py (same gate-invocation forms / exit-code
# semantics: 0 = pass, nonzero = violation, 2 = gateless/unreadable).
# =====================================================================================================
def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def _glob(d, suffix):
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suffix)]


class Engine:
    name = "?"

    def __init__(self):
        self.present = False
        self.ok = False
        self.err = None

    def prepare(self, ws):
        raise NotImplementedError

    def gate(self, ws, case, pol):
        raise NotImplementedError


class RustEngine(Engine):
    name = "rust"

    def prepare(self, ws):
        self.bin = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
        if not os.path.exists(self.bin):
            print("  [rust]  building candor-scan...")
            b = run(["cargo", "build", "-q", "--manifest-path", os.path.join(CANDOR, "Cargo.toml"),
                     "-p", "candor-scan"])
            if b.returncode != 0:
                self.present, self.err = True, "cargo build failed (set CANDOR or CANDOR_SCAN_BIN)"
                return
        if not os.path.exists(self.bin):
            self.err = f"no candor-scan at {self.bin}"
            return
        self.present = self.ok = True

    def gate(self, ws, case, pol):
        d = os.path.join(ws, "rust", case["id"])
        pfx = os.path.join(d, ".out")
        return run([self.bin, d, "--policy", pol, "--out", pfx]).returncode


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

    def gate(self, ws, case, pol):
        cell = case["id"]
        d = os.path.join(ws, "java", cell)
        src = os.path.join(d, "q", "E.java")
        cls = os.path.join(d, "cls")
        os.makedirs(cls, exist_ok=True)
        c = run(["javac", "-d", cls, src])
        if c.returncode != 0:
            raise RuntimeError(f"javac failed on {cell}: {c.stderr.decode()[:300]}")
        env = dict(os.environ, CANDOR_POLICY=pol)
        return run(["java", "-jar", self.jar, cls], env=env).returncode


class TsEngine(Engine):
    name = "ts"

    def prepare(self, ws):
        if not shutil.which("node") or not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")):
            self.err = "no node / scan.mjs (set CANDOR_TS)"
            return
        if not os.path.isdir(os.path.join(CANDOR_TS, "node_modules")):
            run(["npm", "install", "--no-fund", "--no-audit"], cwd=CANDOR_TS)
        self.present = self.ok = True

    def gate(self, ws, case, pol):
        d = os.path.join(ws, "ts", case["id"])
        pfx = os.path.join(d, "out")
        return run(["node", os.path.join(CANDOR_TS, "scan.mjs"), d, "--policy", pol, "--out", pfx]).returncode


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

    def gate(self, ws, case, pol):
        src = os.path.join(ws, "swift", case["id"], "cases.swift")
        pfx = os.path.join(os.path.dirname(src), "out")
        return run([self.bin, src, "--policy", pol, "--out", pfx]).returncode


ENGINES = [RustEngine(), JavaEngine(), TsEngine(), SwiftEngine()]


# =====================================================================================================
# the assertion: per CASE × engine, the gate verdict MUST equal the case's EXPECTED verdict, and the
# engines MUST agree. exit 2 (gateless / unreadable) is itself a hard cell error.
# =====================================================================================================
def main():
    keep = "--keep" in sys.argv[1:]

    print("=" * 100)
    print("CROSS-ENGINE NET DESTINATION-CLASS differential (FOUR-WAY) -- `deny Net[unknown-host]` (SPEC §6.2)")
    print("  property: telemetry / model-partner / config-partner -> PASS; unknown-host / runtime-masked -> FAIL")
    print("            (a PASS on exfil / runtime is the cardinal sin -- an exfiltration Net slips the gate)")
    print("=" * 100)

    ws = tempfile.mkdtemp(prefix="candor-netclass-")
    write_sources(ws)
    pols = {c["id"]: policy_path(ws, c) for c in CASES}

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
            available.append(eng)
            print(f"  {eng.name:6s} ok")

    rc = 2 if failed else 0

    cover = {}  # (case_id, engine) -> rc or ("ERR", msg)
    for case in CASES:
        pol = pols[case["id"]]
        for eng in available:
            try:
                cover[(case["id"], eng.name)] = eng.gate(ws, case, pol)
            except Exception as e:
                cover[(case["id"], eng.name)] = ("ERR", str(e))

    names = [e.name for e in available]
    print("\nVERDICTS  (per cell: exit code; 0 = PASS, nonzero = FAIL; want it to equal `expect`)")
    head = f"{'case':52s} {'expect':7s} " + " ".join(f"{n:14s}" for n in names)
    print(head)
    print("-" * len(head))
    disagreements = []   # (case, engine, got, expected)
    cell_errs = []       # (case, engine, msg)
    for case in CASES:
        exp = case["expect"]
        row = f"{case['rule']:52s} {exp:7s} "
        for eng in available:
            v = cover[(case["id"], eng.name)]
            if isinstance(v, tuple) and v[0] == "ERR":
                cell_errs.append((case["rule"], eng.name, v[1]))
                row += f"{'ERR':14s} "
                continue
            if v == 2:
                cell_errs.append((case["rule"], eng.name, "gate exit 2 (gateless/unreadable policy)"))
                row += f"{'exit2!':14s} "
                continue
            got = "pass" if v == 0 else "fail"
            mark = "ok" if got == exp else "DISAGREE"
            if got != exp:
                disagreements.append((case["rule"], eng.name, got, exp))
            row += f"{f'{got}[{mark}]':14s} "
        print(row)
    print("-" * len(head))

    print()
    if skipped:
        for e, why in skipped.items():
            print(f"NOTE: engine '{e}' SKIPPED (absent) -- {why}")
    if failed:
        for e, why in failed.items():
            print(f"FAIL: engine '{e}' present but broken -- {why}")
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print(f"FAIL (strict): engine '{e}' REQUIRED (CONFORMANCE_REQUIRE_ALL set) but absent -- {why}")
        rc = 2

    if cell_errs:
        rc = rc or 2
        print(f"\n{len(cell_errs)} CELL ERROR(S) (an engine errored / ran gateless on a cell):")
        for rule, eng, msg in cell_errs:
            print(f"  {eng:6s}: {rule} -- {msg}")

    if disagreements:
        rc = rc or 1
        print(f"\n{len(disagreements)} NET DESTINATION-CLASS DISAGREEMENT(S) (an engine's verdict != the SPEC's "
              f"expected verdict -- a PASS on exfil/runtime is the cardinal sin):")
        for rule, eng, got, exp in disagreements:
            print(f"  {eng:6s}: {rule} -- got {got}, expected {exp}")

    n_engines = len(available)
    if rc == 0:
        print(f"\nNET DESTINATION-CLASS differential: OK -- {len(CASES)} cases, {n_engines} engine(s) all agree "
              f"with the §6.2 `deny Net[unknown-host]` fail-closed posture (telemetry/partner tolerated, "
              f"unknown-host/masked denied)")
    else:
        print("\nNET DESTINATION-CLASS differential: FAILED")

    if keep:
        print(f"\n(workspace kept: {ws})")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
