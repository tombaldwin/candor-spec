#!/usr/bin/env python3
"""
CROSS-ENGINE GATE-MASKING differential for the candor effect-checker family.

The cardinal sin of a deployable policy gate is the MASKED-LITERAL EVASION: a denied literal built
DYNAMICALLY (concat / format / runtime variable, not a static string) is structurally INVISIBLE to the
analyzer, so the effect's literal surface is INCOMPLETE / uncertifiable. An `allow <Effect> <benign>`
allowlist MUST therefore FAIL-CLOSED on it (AS-EFF-008's *opaque* failure mode, SEMANTICS §6) — else the
program reaches a host / command / path / table the author never allowed, invisibly, and the gate passes
it. A gate that PASSES a masked-denied program is the cardinal gate-evasion.

This was fixed per-engine this session (candor-scan/deep Fs+Db incomplete-marking; candor-swift two-path
FileManager + establishing-form guard; candor-java URL-split; candor-ts already closed). gen_differential.py
makes EFFECT-SET inference a cross-engine STANDING guarantee; THIS makes the masked-literal POLICY VERDICT
one. It is a sibling of gen_differential.py and reuses its engine resolution + SKIP-loudly / present-but-
broken-FAILS discipline + CONFORMANCE_REQUIRE_ALL strict mode.

THE PROPERTY (per covered (effect × engine) cell):
  * MASKED   program (benign ALLOWED literal + a runtime-MASKED denied literal of the SAME effect)
             -> the gate MUST FAIL (exit nonzero / violation): fail-closed.
  * COMPLIANT program (only the benign literal)
             -> the gate MUST PASS (exit 0): no false positive.
A divergence — an engine that PASSES the masked program (an EVASION) or FAILS the compliant one (a FALSE
POSITIVE) — is a DISAGREEMENT and exits nonzero, named per engine (the gen_differential discipline).

DESIGN — the four LITERAL-SURFACE effects {Net→host, Exec→cmd, Fs→path, Db→table}, rendered in each
language with the SAME std-only / curated-fixture vocabulary as gen_differential.py's EFFECTS and the
tables differential. The masked locator is derived from a FUNCTION PARAMETER (genuinely un-extractable —
exercises the incomplete-surface path, not the visible-but-unallowed path), so the engine marks the
surface incomplete and the gate fails closed on it.

USAGE:
    python3 gen_masking.py            # run every covered cell, exit nonzero on any evasion / false-positive
    python3 gen_masking.py --keep     # keep the generated temp workspace (prints its path)

Engine resolution / build / SKIP discipline mirror gen_differential.py exactly (CANDOR / CANDOR_JAVA /
CANDOR_TS / CANDOR_SWIFT, the prebuilt CANDOR_SCAN_BIN / CANDOR_JAVA_JAR; an absent engine SKIPs loudly,
present-but-broken FAILS, and CONFORMANCE_REQUIRE_ALL turns a SKIP into a FAIL).
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
# EFFECTS -- the four literal-surface effects, each with: a BENIGN allowed literal, the policy ALLOW
# rule that permits exactly that literal, and per-language renderers for the MASKED + COMPLIANT entry
# fns. The vocabulary is the std-only / curated-fixture vocabulary (the same establishing sinks as
# gen_differential.py's EFFECTS + the tables differential): Net host, Exec command head, Fs path, Db
# table. Each MASKED fn reaches the effect TWICE: once at the benign allowed literal, once at a locator
# derived from a function PARAMETER (`m`) -- a runtime value the analyzer cannot extract, so the surface
# is incomplete and an `allow <Effect> <benign>` gate must fail closed (it must NOT let the benign
# sibling literal certify the invisible masked endpoint). COMPLIANT reaches only the benign literal.
#
# NOTE on swift idioms: the host/command literal must be a DIRECT argument of the ESTABLISHING call for
# the engine to capture it (and to know it's incomplete when absent). So Net uses `NWConnection(host:)`
# (host is an arg; URLSession.dataTask(with: URL(string:…)) buries the host inside URL() and yields NO
# surface at all -- it would false-positive the COMPLIANT case), and Exec uses `posix_spawn` (the
# program path is an arg; `Process()` takes no command at construction, and `shellOut(to:)` is NOT in
# the engine's establishing-free set -- see the report's shellOut finding).
# =====================================================================================================

EFFECTS = [
    dict(
        id="net", effect="Net", benign="good.com", allow="allow Net good.com",
        # masked: connect to a benign host AND a host derived from a runtime param.
        rust=dict(
            masked='pub fn entry(m: &str) {{ '
                   'let _ = std::net::TcpStream::connect("good.com:80"); '
                   'let h = format!("{{}}.example", m); '
                   'let _ = std::net::TcpStream::connect(&h); }}',
            compliant='pub fn entry() {{ let _ = std::net::TcpStream::connect("good.com:80"); }}',
        ),
        java=dict(
            masked='  public static void entry(String m) throws Exception {{ '
                   'new java.net.Socket("good.com", 80); '
                   'String h = m + ".example"; '
                   'new java.net.Socket(h, 80); }}',
            compliant='  public static void entry() throws Exception {{ new java.net.Socket("good.com", 80); }}',
        ),
        ts=dict(
            masked='export function entry(m: string): void {{ '
                   'netm.connect(80, "good.com"); '
                   'const h = m + ".example"; '
                   'netm.connect(80, h); }}',
            compliant='export function entry(): void {{ netm.connect(80, "good.com"); }}',
        ),
        swift=dict(
            masked='func entry(_ m: String) {{ '
                   '_ = NWConnection(host: "good.com", port: 80, using: .tcp); '
                   'let h = m + ".example"; '
                   '_ = NWConnection(host: NWEndpoint.Host(h), port: 80, using: .tcp) }}',
            compliant='func entry() {{ _ = NWConnection(host: "good.com", port: 80, using: .tcp) }}',
        ),
    ),
    dict(
        id="exec", effect="Exec", benign="ls", allow="allow Exec ls",
        rust=dict(
            masked='pub fn entry(m: &str) {{ '
                   'let _ = std::process::Command::new("ls"); '
                   'let c = format!("/bin/{{}}", m); '
                   'let _ = std::process::Command::new(&c); }}',
            compliant='pub fn entry() {{ let _ = std::process::Command::new("ls"); }}',
        ),
        java=dict(
            masked='  public static void entry(String m) throws Exception {{ '
                   'new ProcessBuilder("ls").start(); '
                   'String c = "/bin/" + m; '
                   'new ProcessBuilder(c).start(); }}',
            compliant='  public static void entry() throws Exception {{ new ProcessBuilder("ls").start(); }}',
        ),
        ts=dict(
            masked='export function entry(m: string): void {{ '
                   'cp.spawn("ls"); '
                   'const c = "/bin/" + m; '
                   'cp.spawn(c); }}',
            compliant='export function entry(): void {{ cp.spawn("ls"); }}',
        ),
        swift=dict(
            masked='func entry(_ m: String) {{ '
                   '_ = posix_spawn(nil, "/bin/ls", nil, nil, nil, nil); '
                   'let c = "/bin/" + m; '
                   '_ = posix_spawn(nil, c, nil, nil, nil, nil) }}',
            compliant='func entry() {{ _ = posix_spawn(nil, "/bin/ls", nil, nil, nil, nil) }}',
        ),
    ),
    dict(
        id="fs", effect="Fs", benign="/var/app", allow="allow Fs /var/app",
        rust=dict(
            masked='pub fn entry(m: &str) {{ '
                   'let _ = std::fs::write("/var/app/ok", b"x"); '
                   'let p = format!("/etc/{{}}", m); '
                   'let _ = std::fs::write(&p, b"x"); }}',
            compliant='pub fn entry() {{ let _ = std::fs::write("/var/app/ok", b"x"); }}',
        ),
        java=dict(
            masked='  public static void entry(String m) throws Exception {{ '
                   'java.nio.file.Files.write(java.nio.file.Path.of("/var/app/ok"), new byte[0]); '
                   'String p = "/etc/" + m; '
                   'java.nio.file.Files.write(java.nio.file.Path.of(p), new byte[0]); }}',
            compliant='  public static void entry() throws Exception {{ '
                      'java.nio.file.Files.write(java.nio.file.Path.of("/var/app/ok"), new byte[0]); }}',
        ),
        ts=dict(
            masked='export function entry(m: string): void {{ '
                   'fsm.writeFileSync("/var/app/ok", "x"); '
                   'const p = "/etc/" + m; '
                   'fsm.writeFileSync(p, "x"); }}',
            compliant='export function entry(): void {{ fsm.writeFileSync("/var/app/ok", "x"); }}',
        ),
        swift=dict(
            masked='func entry(_ m: String) {{ '
                   '_ = FileManager.default.createFile(atPath: "/var/app/ok", contents: nil); '
                   'let p = "/etc/" + m; '
                   '_ = FileManager.default.createFile(atPath: p, contents: nil) }}',
            compliant='func entry() {{ _ = FileManager.default.createFile(atPath: "/var/app/ok", contents: nil) }}',
        ),
    ),
    dict(
        id="db", effect="Db", benign="customers", allow="allow Db customers",
        rust=dict(
            masked='pub fn entry(c: &rusqlite::Connection, m: &str) {{ '
                   'let _ = c.execute("SELECT x FROM customers", []); '
                   'let t = format!("DELETE FROM {{}}", m); '
                   'let _ = c.execute(&t, []); }}',
            compliant='pub fn entry(c: &rusqlite::Connection) {{ '
                      'let _ = c.execute("SELECT x FROM customers", []); }}',
        ),
        java=dict(
            masked='  public static void entry(java.sql.Connection c, String m) throws Exception {{ '
                   'c.prepareStatement("SELECT x FROM customers").executeQuery(); '
                   'String t = "DELETE FROM " + m; '
                   'c.prepareStatement(t).executeUpdate(); }}',
            compliant='  public static void entry(java.sql.Connection c) throws Exception {{ '
                      'c.prepareStatement("SELECT x FROM customers").executeQuery(); }}',
        ),
        ts=dict(
            masked='export function entry(db: DatabaseSync, m: string): void {{ '
                   'db.exec("SELECT x FROM customers"); '
                   'const t = "DELETE FROM " + m; '
                   'db.exec(t); }}',
            compliant='export function entry(db: DatabaseSync): void {{ db.exec("SELECT x FROM customers"); }}',
        ),
        swift=dict(
            masked='func entry(_ m: String) {{ '
                   '_ = sqlite3_exec(nil, "SELECT x FROM customers", nil, nil, nil); '
                   'let t = "DELETE FROM " + m; '
                   '_ = sqlite3_exec(nil, t, nil, nil, nil) }}',
            compliant='func entry() {{ _ = sqlite3_exec(nil, "SELECT x FROM customers", nil, nil, nil) }}',
        ),
    ),
]


# =====================================================================================================
# rendering one (effect, variant) program into a per-language source tree under <ws>/<lang>/<eff>_<var>.
# =====================================================================================================
def _rust_tree(d, body):
    os.makedirs(os.path.join(d, "src"), exist_ok=True)
    with open(os.path.join(d, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "mask"\nversion = "0.0.0"\nedition = "2021"\n')
    with open(os.path.join(d, "src", "lib.rs"), "w") as f:
        f.write("// GENERATED by gen_masking.py -- do not edit.\n" + body.format() + "\n")


def _java_tree(d, body):
    os.makedirs(os.path.join(d, "q"), exist_ok=True)
    with open(os.path.join(d, "q", "E.java"), "w") as f:
        f.write("// GENERATED by gen_masking.py -- do not edit.\n")
        f.write("package q;\npublic class E {\n" + body.format() + "\n}\n")


def _ts_tree(d, body):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "package.json"), "w") as f:
        f.write('{"name":"mask","version":"0.0.0"}\n')
    with open(os.path.join(d, "cases.ts"), "w") as f:
        f.write("// GENERATED by gen_masking.py -- do not edit.\n")
        f.write('import * as fsm from "node:fs";\n')
        f.write('import * as netm from "node:net";\n')
        f.write('import * as cp from "node:child_process";\n')
        f.write('import { DatabaseSync } from "node:sqlite";\n\n')
        f.write(body.format() + "\n")


def _swift_file(d, body):
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "cases.swift")
    with open(p, "w") as f:
        f.write("// GENERATED by gen_masking.py -- do not edit.\n")
        f.write("import Foundation\nimport Network\nimport SQLite3\n\n")
        f.write(body.format() + "\n")
    return p


def write_sources(ws):
    """Lay out <ws>/<lang>/<eff>_<masked|compliant>/ for every (effect, variant)."""
    for eff in EFFECTS:
        for var in ("masked", "compliant"):
            cell = f"{eff['id']}_{var}"
            _rust_tree(os.path.join(ws, "rust", cell), eff["rust"][var])
            _java_tree(os.path.join(ws, "java", cell), eff["java"][var])
            _ts_tree(os.path.join(ws, "ts", cell), eff["ts"][var])
            _swift_file(os.path.join(ws, "swift", cell), eff["swift"][var])


def policy_path(ws, eff):
    os.makedirs(os.path.join(ws, "pol"), exist_ok=True)
    p = os.path.join(ws, "pol", f"{eff['id']}.policy")
    with open(p, "w") as f:
        f.write(eff["allow"] + "\n")
    return p


# =====================================================================================================
# the engines. Each is a class with .present / .ok / .err set after prepare(), and a .gate(dir_or_src,
# policy) -> exit code. present=False -> SKIP loudly; present=True & ok=False -> FAIL (present-but-broken).
# Mirrors gen_differential.py's engine resolution + run.sh's gate-invocation forms (Part 2 / polfail):
#   rust   candor-scan <dir> --policy <pol> --out <pfx>          (exit 0 ok / 1 violation / 2 gateless)
#   java   env CANDOR_POLICY=<pol> java -jar <jar> <classdir>
#   ts     node scan.mjs <dir> --policy <pol> --out <pfx>
#   swift  <bin> <src> --policy <pol> --out <pfx>
# =====================================================================================================
def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


class Engine:
    name = "?"

    def __init__(self):
        self.present = False
        self.ok = False
        self.err = None

    def prepare(self, ws):  # set present/ok/err
        raise NotImplementedError

    def gate(self, ws, eff, variant, pol):
        """Return the gate exit code for this engine on <eff>_<variant> under policy <pol>."""
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

    def gate(self, ws, eff, variant, pol):
        d = os.path.join(ws, "rust", f"{eff['id']}_{variant}")
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
            self.jar = max(cands, key=os.path.getmtime) if cands else None  # newest, not lexicographic
        if not self.jar or not os.path.exists(self.jar):
            self.err = "no candor-java jar"
            return
        if not shutil.which("javac"):
            self.err = "no javac on PATH"
            return
        self.present = self.ok = True

    def gate(self, ws, eff, variant, pol):
        cell = f"{eff['id']}_{variant}"
        src = os.path.join(ws, "java", cell, "q", "E.java")
        cls = os.path.join(ws, "java", cell, "cls")
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

    def gate(self, ws, eff, variant, pol):
        d = os.path.join(ws, "ts", f"{eff['id']}_{variant}")
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

    def gate(self, ws, eff, variant, pol):
        src = os.path.join(ws, "swift", f"{eff['id']}_{variant}", "cases.swift")
        pfx = os.path.join(os.path.dirname(src), "out")
        return run([self.bin, src, "--policy", pol, "--out", pfx]).returncode


def _glob(d, suffix):
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suffix)]


ENGINES = [RustEngine(), JavaEngine(), TsEngine(), SwiftEngine()]


# =====================================================================================================
# the assertion: per covered (effect × engine), masked → FAIL (nonzero), compliant → PASS (exit 0).
# =====================================================================================================
def main():
    keep = "--keep" in sys.argv[1:]

    print("=" * 100)
    print("CROSS-ENGINE GATE-MASKING differential -- masked-literal allowlist evasion (AS-EFF-008 opaque)")
    print(f"  effects : {', '.join(e['effect'] + '→' + e['benign'] for e in EFFECTS)}")
    print("  property: MASKED (benign + runtime-masked denied literal) -> gate FAILS (fail-closed)")
    print("            COMPLIANT (only the benign literal)             -> gate PASSES (no false positive)")
    print("=" * 100)

    ws = tempfile.mkdtemp(prefix="candor-genmask-")
    write_sources(ws)
    pols = {e["id"]: policy_path(ws, e) for e in EFFECTS}

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

    # ---- run the gate over every covered (effect × engine) cell -------------------------------------
    # cover[(effect_id, engine)] = (masked_rc, compliant_rc) or ("ERR", msg)
    print("\nrunning the masked-literal gate over every (effect × engine) cell...")
    cover = {}
    for eff in EFFECTS:
        pol = pols[eff["id"]]
        for eng in available:
            try:
                m_rc = eng.gate(ws, eff, "masked", pol)
                c_rc = eng.gate(ws, eff, "compliant", pol)
                cover[(eff["id"], eng.name)] = (m_rc, c_rc)
            except Exception as e:
                cover[(eff["id"], eng.name)] = ("ERR", str(e))

    # ---- the coverage / verdict table ---------------------------------------------------------------
    names = [e.name for e in available]
    print("\nCOVERAGE  (per cell: masked→<rc> compliant→<rc>; want masked≠0, compliant=0)")
    head = f"{'effect':10s} " + " ".join(f"{n:22s}" for n in names)
    print(head)
    print("-" * len(head))
    evasions = []         # (effect, engine) -- masked PASSED the gate (the cardinal sin)
    false_pos = []        # (effect, engine) -- compliant FAILED the gate
    cell_errs = []        # (effect, engine, msg)
    covered = 0
    for eff in EFFECTS:
        row = f"{eff['effect']:10s} "
        for eng in available:
            v = cover[(eff["id"], eng.name)]
            if v[0] == "ERR":
                cell_errs.append((eff["effect"], eng.name, v[1]))
                row += f"{'ERR':22s} "
                continue
            m_rc, c_rc = v
            covered += 1
            m_ok = m_rc != 0           # masked must FAIL-closed
            c_ok = c_rc == 0           # compliant must PASS
            if not m_ok:
                evasions.append((eff["effect"], eng.name, m_rc, c_rc))
            if not c_ok:
                false_pos.append((eff["effect"], eng.name, m_rc, c_rc))
            mark = "ok" if (m_ok and c_ok) else ("EVASION" if not m_ok else "FALSE-POS")
            row += f"{f'm→{m_rc} c→{c_rc} [{mark}]':22s} "
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
    # STRICT mode (gen_differential discipline): a SKIPPED engine FAILS under CONFORMANCE_REQUIRE_ALL,
    # else the gate's "all N engines agree" verdict silently degrades.
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print(f"FAIL (strict): engine '{e}' REQUIRED (CONFORMANCE_REQUIRE_ALL set) but absent -- {why}")
        rc = 2

    if cell_errs:
        rc = rc or 2
        print(f"\n{len(cell_errs)} CELL ERROR(S) (an engine errored building/scanning a cell — present-but-broken):")
        for effname, eng, msg in cell_errs:
            print(f"  {effname:6s} / {eng:6s}: {msg}")

    if evasions:
        rc = rc or 1
        print(f"\n{len(evasions)} MASKED-LITERAL EVASION(S) -- the CARDINAL gate-evasion (an engine PASSED a "
              f"masked-denied program):")
        for effname, eng, m_rc, c_rc in evasions:
            print(f"  {effname:6s} / {eng:6s}: masked program PASSED the gate (exit {m_rc}) — a denied "
                  f"{effname} literal built at runtime slipped past `allow {effname} <benign>` invisibly")
    if false_pos:
        rc = rc or 1
        print(f"\n{len(false_pos)} FALSE POSITIVE(S) -- an engine FAILED a COMPLIANT program (only the benign "
              f"literal):")
        for effname, eng, m_rc, c_rc in false_pos:
            print(f"  {effname:6s} / {eng:6s}: compliant program FAILED the gate (exit {c_rc}) — the benign "
                  f"allowed literal should certify clean")

    print()
    if rc == 0 and not evasions and not false_pos and not cell_errs:
        print(f"GATE-MASKING DIFFERENTIAL: OK -- all {len(available)} available engine(s) "
              f"({', '.join(names)}) FAIL-CLOSE on a masked denied literal and PASS the compliant program, "
              f"across {covered} (effect × engine) cell(s).")
    else:
        print("GATE-MASKING DIFFERENTIAL: FAILED -- see evasions / false-positives / errors above.")

    if keep:
        print(f"\n[--keep] generated workspace retained at: {ws}")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
