#!/usr/bin/env python3
"""
CROSS-ENGINE POLICY-MATCHING differential (FOUR-WAY) for the candor effect-checker family.

The §6.2 policy GRAMMAR is diffed by run.sh PART 4 (parsepolicy). This is its sibling on the *applied
matching* axis: given the SAME policy and an EQUIVALENT fixture, do all four engines reach the SAME gate
verdict? That is where the live divergences hid — candor-swift's `Net` host:port match and its `::`-vs-`.`
scope segmentation both diverged from the others and slipped past the (rust+java+ts-only) coverage. This
makes the verdict a STANDING four-way gate so those can't regress.

It deliberately mirrors gen_masking.py exactly: the same Engine classes (rust / java / ts / swift, each
gating via `--policy` and returning an exit code: 0 = pass, nonzero = violation), the same present/ok /
SKIP-loudly / present-but-broken-FAILS / CONFORMANCE_REQUIRE_ALL discipline.

THE PROPERTY (per CASE × engine): the engine's gate verdict (PASS / FAIL) MUST equal the case's EXPECTED
verdict, which is what SPEC §6.2's matching rules dictate. An engine that disagrees with the expected
verdict — or with the OTHER engines — is a DISAGREEMENT and exits nonzero, named per engine.

CASES — the four matching rules item-9 of the spec-review names, each with a MATCH (expect PASS) and a
NON-MATCH (expect FAIL) variant where the rule's boundary bites:

  * net_port      — `allow Net api.example.com` certifies `connect(api.example.com:8080)`: hosts match by
                    HOSTNAME, the literal PORT is ignored (the live candor-java/swift port divergence).
                    MATCH: reach api.example.com:8080 under `allow Net api.example.com`  -> PASS.
                    NOMATCH: reach api.example.com:8080 under `allow Net other.example.com` -> FAIL.
  * scope_segment — scope matching is BY PATH SEGMENT, not substring (`::` in Rust, `.` on the JVM, the
                    language separator elsewhere). `deny Net client` must hit a function in a `client`
                    segment but NOT one in a `network`/`netclient` cousin. (The `::`-vs-`.` Swift bug.)
                    MATCH: a Net fn in scope `client` under `deny Net client`  -> FAIL.
                    NOMATCH: a Net fn in scope `network` under `deny Net client` -> PASS.
  * fs_path       — `allow Fs /etc/app` covers everything BENEATH /etc/app but is PATH-BOUNDARY-respecting:
                    it must NOT cover the sibling `/etc/apppwned`.
                    MATCH: write /etc/app/ok under `allow Fs /etc/app`        -> PASS.
                    NOMATCH: write /etc/apppwned/x under `allow Fs /etc/app`  -> FAIL.
  * exec_base     — `allow Exec git` matches a command by BASENAME (`/usr/bin/git` ≡ git).
                    MATCH: spawn /usr/bin/git under `allow Exec git`          -> PASS.
                    NOMATCH: spawn /usr/bin/curl under `allow Exec git`       -> FAIL.
  * db_schema     — `allow Db ledger.*` covers every table in schema `ledger` but is BOUNDARY-respecting:
                    it must NOT cover `ledgerx.entries`.
                    MATCH: query ledger.entries under `allow Db ledger.*`      -> PASS.
                    NOMATCH: query ledgerx.entries under `allow Db ledger.*`   -> FAIL.

NOTE — running in parallel with engine fixes: the engines' own port/scope/path/schema matching fixes are
being made by other agents. If a NON-MATCH case PASSES (or a MATCH case FAILS) on an as-yet-unfixed engine,
this differential FLAGS it (that is the point — it is the regression guard). A flagged engine prints its
disagreement; the run exits nonzero so the gap is visible, not silent.

USAGE:
    python3 gen_policy_match.py            # run every case, exit nonzero on any disagreement
    python3 gen_policy_match.py --keep     # keep the generated temp workspace (prints its path)

Engine resolution / build / SKIP discipline mirror gen_masking.py / gen_differential.py (CANDOR /
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
# CASES -- each has: a `policy` (the §6.2 rule text), an `expect` verdict ("pass"/"fail"), and a
# per-language body for a single fn `entry` (scope cases place it inside a `client`/`network` module/type
# so the scope segment is part of the qualified name). The std-only / curated-fixture vocabulary is shared
# with gen_masking.py: Net = TcpStream/Socket/net.connect/NWConnection, Exec = Command/ProcessBuilder/
# spawn/posix_spawn, Fs = fs::write/Files.write/writeFileSync/createFile, Db = rusqlite/JDBC/DatabaseSync/
# sqlite3_exec. `entry` is the gated unit; the gate's exit code is the verdict.
# =====================================================================================================
CASES = [
    dict(
        id="net_port_match", rule="net host:port ignored (MATCH)", effect="Net",
        policy="allow Net api.example.com", expect="pass",
        rust='pub fn entry() {{ let _ = std::net::TcpStream::connect("api.example.com:8080"); }}',
        java='  public static void entry() throws Exception {{ new java.net.Socket("api.example.com", 8080); }}',
        ts='export function entry(): void {{ netm.connect(8080, "api.example.com"); }}',
        swift='func entry() {{ _ = NWConnection(host: "api.example.com", port: 8080, using: .tcp) }}',
    ),
    dict(
        id="net_port_nomatch", rule="net host:port — denied host (NOMATCH)", effect="Net",
        policy="allow Net other.example.com", expect="fail",
        rust='pub fn entry() {{ let _ = std::net::TcpStream::connect("api.example.com:8080"); }}',
        java='  public static void entry() throws Exception {{ new java.net.Socket("api.example.com", 8080); }}',
        ts='export function entry(): void {{ netm.connect(8080, "api.example.com"); }}',
        swift='func entry() {{ _ = NWConnection(host: "api.example.com", port: 8080, using: .tcp) }}',
    ),
    dict(
        id="scope_match", rule="scope by segment — `client` (MATCH)", effect="Net",
        policy="deny Net client", expect="fail", scope="client",
        rust='pub fn entry() {{ let _ = std::net::TcpStream::connect("api.example.com:80"); }}',
        java='    public static void entry() throws Exception {{ new java.net.Socket("api.example.com", 80); }}',
        ts='export function entry(): void {{ netm.connect(80, "api.example.com"); }}',
        swift='func entry() {{ _ = NWConnection(host: "api.example.com", port: 80, using: .tcp) }}',
    ),
    dict(
        id="scope_nomatch", rule="scope by segment — `network` cousin (NOMATCH)", effect="Net",
        policy="deny Net client", expect="pass", scope="network",
        rust='pub fn entry() {{ let _ = std::net::TcpStream::connect("api.example.com:80"); }}',
        java='    public static void entry() throws Exception {{ new java.net.Socket("api.example.com", 80); }}',
        ts='export function entry(): void {{ netm.connect(80, "api.example.com"); }}',
        swift='func entry() {{ _ = NWConnection(host: "api.example.com", port: 80, using: .tcp) }}',
    ),
    dict(
        id="fs_path_match", rule="fs path-boundary prefix — beneath (MATCH)", effect="Fs",
        policy="allow Fs /etc/app", expect="pass",
        rust='pub fn entry() {{ let _ = std::fs::write("/etc/app/ok", b"x"); }}',
        java='  public static void entry() throws Exception {{ java.nio.file.Files.write(java.nio.file.Path.of("/etc/app/ok"), new byte[0]); }}',
        ts='export function entry(): void {{ fsm.writeFileSync("/etc/app/ok", "x"); }}',
        swift='func entry() {{ _ = FileManager.default.createFile(atPath: "/etc/app/ok", contents: nil) }}',
    ),
    dict(
        id="fs_path_nomatch", rule="fs path-boundary prefix — sibling /etc/apppwned (NOMATCH)", effect="Fs",
        policy="allow Fs /etc/app", expect="fail",
        rust='pub fn entry() {{ let _ = std::fs::write("/etc/apppwned/x", b"x"); }}',
        java='  public static void entry() throws Exception {{ java.nio.file.Files.write(java.nio.file.Path.of("/etc/apppwned/x"), new byte[0]); }}',
        ts='export function entry(): void {{ fsm.writeFileSync("/etc/apppwned/x", "x"); }}',
        swift='func entry() {{ _ = FileManager.default.createFile(atPath: "/etc/apppwned/x", contents: nil) }}',
    ),
    dict(
        id="exec_base_match", rule="exec basename match — /usr/bin/git ≡ git (MATCH)", effect="Exec",
        policy="allow Exec git", expect="pass",
        rust='pub fn entry() {{ let _ = std::process::Command::new("/usr/bin/git").spawn(); }}',
        java='  public static void entry() throws Exception {{ new ProcessBuilder("/usr/bin/git").start(); }}',
        ts='export function entry(): void {{ cp.spawn("/usr/bin/git"); }}',
        swift='func entry() {{ _ = posix_spawn(nil, "/usr/bin/git", nil, nil, nil, nil) }}',
    ),
    dict(
        id="exec_base_nomatch", rule="exec basename match — /usr/bin/curl ≠ git (NOMATCH)", effect="Exec",
        policy="allow Exec git", expect="fail",
        rust='pub fn entry() {{ let _ = std::process::Command::new("/usr/bin/curl").spawn(); }}',
        java='  public static void entry() throws Exception {{ new ProcessBuilder("/usr/bin/curl").start(); }}',
        ts='export function entry(): void {{ cp.spawn("/usr/bin/curl"); }}',
        swift='func entry() {{ _ = posix_spawn(nil, "/usr/bin/curl", nil, nil, nil, nil) }}',
    ),
    dict(
        id="db_schema_match", rule="db schema.* — ledger.entries (MATCH)", effect="Db",
        policy="allow Db ledger.*", expect="pass",
        rust='pub fn entry(c: &rusqlite::Connection) {{ let _ = c.execute("SELECT x FROM ledger.entries", []); }}',
        java='  public static void entry(java.sql.Connection c) throws Exception {{ c.prepareStatement("SELECT x FROM ledger.entries").executeQuery(); }}',
        ts='export function entry(db: DatabaseSync): void {{ db.exec("SELECT x FROM ledger.entries"); }}',
        swift='func entry() {{ _ = sqlite3_exec(nil, "SELECT x FROM ledger.entries", nil, nil, nil) }}',
    ),
    dict(
        id="db_schema_nomatch", rule="db schema.* boundary — ledgerx.entries (NOMATCH)", effect="Db",
        policy="allow Db ledger.*", expect="fail",
        rust='pub fn entry(c: &rusqlite::Connection) {{ let _ = c.execute("SELECT x FROM ledgerx.entries", []); }}',
        java='  public static void entry(java.sql.Connection c) throws Exception {{ c.prepareStatement("SELECT x FROM ledgerx.entries").executeQuery(); }}',
        ts='export function entry(db: DatabaseSync): void {{ db.exec("SELECT x FROM ledgerx.entries"); }}',
        swift='func entry() {{ _ = sqlite3_exec(nil, "SELECT x FROM ledgerx.entries", nil, nil, nil) }}',
    ),
]


# =====================================================================================================
# rendering one CASE into a per-language source tree under <ws>/<lang>/<case_id>/. For the scope cases a
# `scope` segment is woven into the qualified name in each language's idiom (a Rust module, a Java nested
# class, a TS namespace, a Swift enum namespace) so `deny Net <scope>` segment-matching is exercised.
# =====================================================================================================
def _rust_tree(d, case):
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    with open(os.path.join(d, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "polmatch"\nversion = "0.0.0"\nedition = "2021"\n')
    body = case["rust"].format()
    scope = case.get("scope")
    if scope:
        body = f"pub mod {scope} {{ {body} }}"
    with open(os.path.join(d, "src", "lib.rs"), "w") as f:
        f.write("// GENERATED by gen_policy_match.py -- do not edit.\n" + body + "\n")


# Java: a scope segment is a real PACKAGE named for it (`package <scope>;` -> qual `<scope>.E.entry`, a
# clean `.`-separated segment), not a nested class (whose `$`-fused `E$<scope>` is not a `.`-segment, so
# `deny Net <scope>` could not match it by the §6.2 split-on-`.` rule). java_src() recomputes the path.
def java_pkg(case):
    return case.get("scope") or "q"


def java_src(d, case):
    return os.path.join(d, java_pkg(case), "E.java")


def _java_tree(d, case):
    pkg = java_pkg(case)
    os.makedirs(os.path.join(d, pkg), exist_ok=True)
    body = case["java"].format()
    with open(java_src(d, case), "w") as f:
        f.write("// GENERATED by gen_policy_match.py -- do not edit.\n")
        f.write(f"package {pkg};\npublic class E {{\n" + body + "\n}\n")


# TS: candor-ts qualifies a unit by its module = the file's relative path (path.sep -> `.`); a namespace
# block is NOT a qualification segment (its members are top-level units). So a scope segment is the file's
# DIRECTORY named for it (`<scope>/cases.ts` -> module `<scope>`, qual `<scope>.entry`), not a namespace.
def ts_dir(d, case):
    return os.path.join(d, case["scope"]) if case.get("scope") else d


def _ts_tree(d, case):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "package.json"), "w") as f:
        f.write('{"name":"polmatch","version":"0.0.0"}\n')
    sub = ts_dir(d, case)
    os.makedirs(sub, exist_ok=True)
    body = case["ts"].format()
    with open(os.path.join(sub, "cases.ts"), "w") as f:
        f.write("// GENERATED by gen_policy_match.py -- do not edit.\n")
        f.write('import * as fsm from "node:fs";\n')
        f.write('import * as netm from "node:net";\n')
        f.write('import * as cp from "node:child_process";\n')
        f.write('import { DatabaseSync } from "node:sqlite";\n\n')
        f.write(body + "\n")


def _swift_file(d, case):
    os.makedirs(d, exist_ok=True)
    body = case["swift"].format()
    scope = case.get("scope")
    if scope:
        body = f"enum {scope} {{ static {body} }}"
    p = os.path.join(d, "cases.swift")
    with open(p, "w") as f:
        f.write("// GENERATED by gen_policy_match.py -- do not edit.\n")
        f.write("import Foundation\nimport Network\nimport SQLite3\n\n")
        f.write(body + "\n")
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
# the engines -- IDENTICAL to gen_masking.py (same gate-invocation forms / exit-code semantics).
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
        """Return the gate exit code for this engine on <case> under policy <pol>."""
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
        src = java_src(d, case)
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
# engines MUST agree. An exit code of 2 (gateless / unreadable policy) is itself a failure for the case.
# =====================================================================================================
def main():
    keep = "--keep" in sys.argv[1:]

    print("=" * 100)
    print("CROSS-ENGINE POLICY-MATCHING differential (FOUR-WAY) -- applied literal & scope matching (SPEC §6.2)")
    print("  property: each case's gate verdict (PASS/FAIL) == the rule's EXPECTED verdict, in every engine")
    print("=" * 100)

    ws = tempfile.mkdtemp(prefix="candor-polmatch-")
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

    # ---- run the gate over every (case × engine) cell ----------------------------------------------
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
    head = f"{'case':34s} {'expect':7s} " + " ".join(f"{n:14s}" for n in names)
    print(head)
    print("-" * len(head))
    disagreements = []   # (case, engine, got_verdict, expected_verdict)
    cell_errs = []       # (case, engine, msg)
    for case in CASES:
        exp = case["expect"]
        row = f"{case['rule']:34s} {exp:7s} "
        verdicts = {}
        for eng in available:
            v = cover[(case["id"], eng.name)]
            if isinstance(v, tuple) and v[0] == "ERR":
                cell_errs.append((case["rule"], eng.name, v[1]))
                row += f"{'ERR':14s} "
                continue
            # exit 2 = gateless/unreadable -> the case is not actually gated; treat as a hard cell error.
            if v == 2:
                cell_errs.append((case["rule"], eng.name, "gate exit 2 (gateless/unreadable policy)"))
                row += f"{'exit2!':14s} "
                continue
            got = "pass" if v == 0 else "fail"
            verdicts[eng.name] = got
            mark = "ok" if got == exp else "DISAGREE"
            if got != exp:
                disagreements.append((case["rule"], eng.name, got, exp))
            row += f"{f'{got}[{mark}]':14s} "
        print(row)
    print("-" * len(head))

    # ---- verdict ------------------------------------------------------------------------------------
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
        print(f"\n{len(disagreements)} POLICY-MATCH DISAGREEMENT(S) (an engine's verdict != the rule's expected "
              f"verdict -- a matching divergence, the class that hid the live Net-port / scope bugs):")
        for rule, eng, got, exp in disagreements:
            print(f"  {eng:6s}: {rule} -- got {got}, expected {exp}")

    n_engines = len(available)
    if rc == 0:
        print(f"\nPOLICY-MATCHING differential: OK -- {len(CASES)} cases, {n_engines} engine(s) all agree with the "
              f"§6.2 expected verdict (host:port, scope-segment, fs path-boundary, exec basename, db schema.*)")
    else:
        print("\nPOLICY-MATCHING differential: FAILED")

    if keep:
        print(f"\n(workspace kept: {ws})")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
