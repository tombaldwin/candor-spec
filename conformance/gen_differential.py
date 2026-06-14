#!/usr/bin/env python3
"""
GENERATIVE cross-engine differential for the candor effect-checker family.

run.sh checks ~22 FIXED hand-written fixtures. This is the complementary GENERATOR: it emits an
EFFECT x INDIRECTION matrix -- every effect reached through every indirection form -- rendered
semantically-equivalently in all four languages (rust / java / ts / swift), scans each with its own
engine, and asserts every engine infers the SAME effect set for every generated case.

This targets the receiver-indirection bugs the family just fixed: a for-loop / subscript / field /
callback receiver whose effect an engine silently DROPS (under-report) or FABRICATES (a different /
extra effect). The KILLER case is `loop_elem` (`for c in xs { c.sink() }`) -- engines used to drop it.

DESIGN -- extend in ONE place:
  * add an EFFECT  -> append to EFFECTS  (per-language sink expr + expected effect)
  * add an INDIRECTION -> append to INDIRECTIONS (a renderer per language + an acceptance rule)

USAGE:
    python3 gen_differential.py            # run the full matrix, exit non-zero on any disagreement
    python3 gen_differential.py --keep     # keep the generated temp workspace (prints its path)

Engine resolution mirrors run.sh:
    CANDOR        (rust)  default ../../candor-rust   ; reuse $CANDOR/target/debug/candor-scan
    CANDOR_JAVA   (jvm)   default ../../candor-java    ; reuse build/libs/*-all.jar, else ./gradlew shadowJar
    CANDOR_TS     (ts)    default ../../candor-ts       ; node scan.mjs <dir> --out <prefix>
    CANDOR_SWIFT  (swift) default ../../candor-swift    ; swift build -> .build/debug/candor-swift
A toolchain that is absent is SKIPPED LOUDLY (printed), never silently passed -- the TS_PRESENT /
SW_PRESENT discipline from run.sh: present-but-broken FAILS; genuinely-absent SKIPS.
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


CANDOR       = envdir("CANDOR",       "../../candor-rust")
CANDOR_JAVA  = envdir("CANDOR_JAVA",  "../../candor-java")
CANDOR_TS    = envdir("CANDOR_TS",    "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")

PURE = frozenset()          # the empty effect set; an inferred-empty fn is OMITTED from a report
UNKNOWN = "Unknown"

# =====================================================================================================
# EFFECTS -- one leaf sink per effect, in each language. The sink expressions reuse the exact std-only
# vocabulary of the curated fixtures (rust/src/lib.rs, java/Cases.java, candor-ts/Cases.ts,
# candor-swift/conformance/Cases.swift): fs_read / net_connect / exec_spawn / env_read / clock_now.
# Each entry: a stable id, the EXPECTED effect, and the per-language sink STATEMENT (no trailing ;).
# =====================================================================================================
EFFECTS = [
    dict(id="fs", effect="Fs", sink=dict(
        rust='let _ = std::fs::read("/tmp/x");',
        java='try { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); } catch (Exception e) {}',
        ts='try { fsm.readFileSync("/tmp/x"); } catch {}',
        swift='_ = FileManager.default.contents(atPath: "/tmp/x")',
    )),
    dict(id="net", effect="Net", sink=dict(
        rust='let _ = std::net::TcpStream::connect("h:1");',
        java='try { new java.net.Socket("h", 1); } catch (Exception e) {}',
        ts='try { netm.connect(1, "h"); } catch {}',
        swift='_ = URLSession.shared.dataTask(with: URL(string: "http://h")!)',
    )),
    dict(id="exec", effect="Exec", sink=dict(
        rust='let _ = std::process::Command::new("ls");',
        java='try { new ProcessBuilder("ls").start(); } catch (Exception e) {}',
        ts='try { cp.spawn("x"); } catch {}',
        swift='_ = Process()',
    )),
    dict(id="env", effect="Env", sink=dict(
        rust='let _ = std::env::var("PATH");',
        java='System.getenv("PATH");',
        ts='void process.env.X;',
        swift='_ = ProcessInfo.processInfo.environment["PATH"]',
    )),
    dict(id="clock", effect="Clock", sink=dict(
        rust='let _ = std::time::SystemTime::now();',
        java='long t = System.currentTimeMillis();',
        ts='void Date.now();',
        swift='_ = Date()',
    )),
]


# =====================================================================================================
# INDIRECTIONS -- how an entry fn REACHES the sink. Each renderer receives:
#   eff   : the EFFECTS entry  (eff["sink"][lang] is the sink statement)
#   name  : the deterministic entry-fn name (e.g. g_fs_loop_elem)
#   sfx   : a per-cell unique suffix (the effect id) to keep helper/type names from colliding
# and returns a string of top-level declarations for that language. EXACTLY ONE public/entry fn named
# `name` per cell; helper fns/types are private and suffixed.
#
# `accept(effect)` returns the SET of inferred-sets that count as agreement for that indirection:
#   * the strict indirections demand exactly {effect}.
#   * `callback` is honestly indeterminate from a generic HOF's standpoint, so it accepts
#     {effect} | {Unknown} | {effect,Unknown}; PURE (a silent drop) or a DIFFERENT effect is flagged.
# =====================================================================================================

def acc_exact(effect):
    return [frozenset({effect})]


def acc_callback(effect):
    # the sink OR Unknown OR both -- a generic callback is honestly indeterminate from the HOF.
    return [frozenset({effect}), frozenset({UNKNOWN}), frozenset({effect, UNKNOWN})]


# ---- renderers: direct ------------------------------------------------------------------------------
def r_direct(eff, name, sfx):
    return {
        "rust":  f'pub fn {name}() {{ {eff["sink"]["rust"]} }}',
        "java":  f'  public static void {name}() {{ {eff["sink"]["java"]} }}',
        "ts":    f'export function {name}(): void {{ {eff["sink"]["ts"]} }}',
        "swift": f'func {name}() {{ {eff["sink"]["swift"]} }}',
    }


# ---- renderers: local_call (entry calls a local helper that does the sink) ---------------------------
def r_local_call(eff, name, sfx):
    h = f"h_{sfx}_lc"
    return {
        "rust":  f'fn {h}() {{ {eff["sink"]["rust"]} }}\npub fn {name}() {{ {h}(); }}',
        "java":  f'  static void {h}() {{ {eff["sink"]["java"]} }}\n'
                 f'  public static void {name}() throws Exception {{ {h}(); }}',
        "ts":    f'function {h}(): void {{ {eff["sink"]["ts"]} }}\n'
                 f'export function {name}(): void {{ {h}(); }}',
        "swift": f'func {h}() {{ {eff["sink"]["swift"]} }}\nfunc {name}() {{ {h}() }}',
    }


# ---- renderers: method_recv (a method on a type does the sink; entry calls it via a TYPED param) -----
def r_method_recv(eff, name, sfx):
    W = f"W_{sfx}_mr"
    return {
        "rust":  f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                 f'pub fn {name}(w: &{W}) {{ w.run(); }}',
        "java":  f'  static class {W} {{ void run() {{ {eff["sink"]["java"]} }} }}\n'
                 f'  public static void {name}({W} w) throws Exception {{ w.run(); }}',
        "ts":    f'class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                 f'export function {name}(w: {W}): void {{ w.run(); }}',
        "swift": f'struct {W} {{ func run() {{ {eff["sink"]["swift"]} }} }}\n'
                 f'func {name}(_ w: {W}) {{ w.run() }}',
    }


# ---- renderers: loop_elem -- THE KILLER CASE. for c in xs { c.run() } over a typed collection --------
def r_loop_elem(eff, name, sfx):
    W = f"W_{sfx}_le"
    return {
        "rust":  f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                 f'pub fn {name}(xs: Vec<{W}>) {{ for c in xs {{ c.run(); }} }}',
        "java":  f'  static class {W} {{ void run() {{ {eff["sink"]["java"]} }} }}\n'
                 f'  public static void {name}(java.util.List<{W}> xs) throws Exception {{ for ({W} c : xs) {{ c.run(); }} }}',
        "ts":    f'class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                 f'export function {name}(xs: {W}[]): void {{ for (const c of xs) {{ c.run(); }} }}',
        "swift": f'struct {W} {{ func run() {{ {eff["sink"]["swift"]} }} }}\n'
                 f'func {name}(_ xs: [{W}]) {{ for c in xs {{ c.run() }} }}',
    }


# ---- renderers: field -- self.f.run(), a stored field whose method does the sink --------------------
def r_field(eff, name, sfx):
    W = f"W_{sfx}_fl"
    H = f"H_{sfx}_fl"
    return {
        "rust":  f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                 f'pub struct {H} {{ pub f: {W} }}\nimpl {H} {{ pub fn drive(&self) {{ self.f.run(); }} }}\n'
                 f'pub fn {name}(h: &{H}) {{ h.drive(); }}',
        "java":  f'  static class {W} {{ void run() {{ {eff["sink"]["java"]} }} }}\n'
                 f'  static class {H} {{ {W} f; void drive() {{ f.run(); }} }}\n'
                 f'  public static void {name}({H} h) throws Exception {{ h.drive(); }}',
        "ts":    f'class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                 f'class {H} {{ f: {W} = new {W}(); drive(): void {{ this.f.run(); }} }}\n'
                 f'export function {name}(h: {H}): void {{ h.drive(); }}',
        "swift": f'struct {W} {{ func run() {{ {eff["sink"]["swift"]} }} }}\n'
                 f'struct {H} {{ let f: {W}; func drive() {{ f.run() }} }}\n'
                 f'func {name}(_ h: {H}) {{ h.drive() }}',
    }


# ---- renderers: callback -- the sink fn passed (by NAME) to a HOF that invokes it -------------------
# The honest result is {effect} OR {Unknown} (a generic callback is indeterminate from the HOF's own
# standpoint), so acc_callback accepts either; only PURE (a silent drop) or a DIFFERENT effect flags.
def r_callback(eff, name, sfx):
    s = f"s_{sfx}_cb"
    hof = f"hof_{sfx}_cb"
    return {
        "rust":  f'fn {s}() {{ {eff["sink"]["rust"]} }}\nfn {hof}(cb: fn()) {{ cb(); }}\n'
                 f'pub fn {name}() {{ {hof}({s}); }}',
        "java":  f'  static void {s}() {{ {eff["sink"]["java"]} }}\n'
                 f'  static void {hof}(Runnable cb) {{ cb.run(); }}\n'
                 f'  public static void {name}() throws Exception {{ {hof}(Cases::{s}); }}',
        "ts":    f'function {s}(): void {{ {eff["sink"]["ts"]} }}\n'
                 f'function {hof}(cb: () => void): void {{ cb(); }}\n'
                 f'export function {name}(): void {{ {hof}({s}); }}',
        "swift": f'func {s}() {{ {eff["sink"]["swift"]} }}\nfunc {hof}(_ cb: () -> Void) {{ cb() }}\n'
                 f'func {name}() {{ {hof}({s}) }}',
    }


INDIRECTIONS = [
    dict(id="direct",      render=r_direct,      accept=acc_exact),
    dict(id="local_call",  render=r_local_call,  accept=acc_exact),
    dict(id="method_recv", render=r_method_recv, accept=acc_exact),
    dict(id="loop_elem",   render=r_loop_elem,   accept=acc_exact),
    dict(id="field",       render=r_field,       accept=acc_exact),
    dict(id="callback",    render=r_callback,    accept=acc_callback),
]


# =====================================================================================================
# the MATRIX -- one cell per (effect, indirection); the entry fn is g_<effectid>_<indirectionid>.
# =====================================================================================================
def build_cells():
    cells = []
    for eff in EFFECTS:
        for ind in INDIRECTIONS:
            name = f"g_{eff['id']}_{ind['id']}"
            cells.append(dict(
                name=name,
                effect=eff["effect"],
                effect_id=eff["id"],
                indirection=ind["id"],
                accept=[set(a) for a in ind["accept"](eff["effect"])],
                code=ind["render"](eff, name, eff["id"]),
            ))
    return cells


# =====================================================================================================
# rendering the four source trees into a temp workspace.
# =====================================================================================================
def write_sources(ws, cells):
    # ---- rust crate ----
    rs = os.path.join(ws, "rust")
    os.makedirs(os.path.join(rs, "src"), exist_ok=True)
    with open(os.path.join(rs, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "gendiff"\nversion = "0.0.0"\nedition = "2021"\n')
    with open(os.path.join(rs, "src", "lib.rs"), "w") as f:
        f.write("// GENERATED by gen_differential.py -- do not edit.\n\n")
        f.write("\n\n".join(c["code"]["rust"] for c in cells) + "\n")

    # ---- java Cases class ----
    jv = os.path.join(ws, "java")
    os.makedirs(jv, exist_ok=True)
    with open(os.path.join(jv, "Cases.java"), "w") as f:
        f.write("// GENERATED by gen_differential.py -- do not edit.\n")
        f.write("public class Cases {\n")
        f.write("\n".join(c["code"]["java"] for c in cells) + "\n")
        f.write("}\n")

    # ---- ts file + package.json ----
    ts = os.path.join(ws, "ts")
    os.makedirs(ts, exist_ok=True)
    with open(os.path.join(ts, "package.json"), "w") as f:
        f.write('{"name":"gendiff","version":"0.0.0"}\n')
    with open(os.path.join(ts, "cases.ts"), "w") as f:
        f.write("// GENERATED by gen_differential.py -- do not edit.\n")
        f.write('import * as fsm from "node:fs";\n')
        f.write('import * as netm from "node:net";\n')
        f.write('import * as cp from "node:child_process";\n\n')
        f.write("\n\n".join(c["code"]["ts"] for c in cells) + "\n")

    # ---- swift file ----
    sw = os.path.join(ws, "swift")
    os.makedirs(sw, exist_ok=True)
    with open(os.path.join(sw, "cases.swift"), "w") as f:
        f.write("// GENERATED by gen_differential.py -- do not edit.\n")
        f.write("import Foundation\n\n")
        f.write("\n\n".join(c["code"]["swift"] for c in cells) + "\n")
    return rs, jv, ts, sw


# =====================================================================================================
# locating / building the engines (mirrors run.sh). Each returns (present, ok, runner-or-None).
# present=False -> SKIP loudly; present=True & ok=False -> FAIL (present-but-broken).
# =====================================================================================================
def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def leaf_set(path, seps=(".", "::")):
    """{leaf-fn-name -> inferred set} from an engine report. Pure fns are OMITTED -> absent==pure."""
    d = json.load(open(path))
    fns = d["functions"] if isinstance(d, dict) else d
    out = {}
    for e in fns:
        n = e["fn"]
        for s in seps:
            n = n.split(s)[-1]
        out[n] = frozenset(e.get("inferred", []))
    return out


def scan_rust(ws):
    binp = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
    if not os.path.exists(binp):
        print("  [rust]  building candor-scan...")
        b = run(["cargo", "build", "-q", "--manifest-path", os.path.join(CANDOR, "Cargo.toml"),
                 "-p", "candor-scan"])
        if b.returncode != 0:
            return (True, False, None, "cargo build failed (set CANDOR or CANDOR_SCAN_BIN)")
    if not os.path.exists(binp):
        return (False, False, None, f"no candor-scan at {binp}")
    d = os.path.join(ws, "rust")
    r = run([binp, d])
    rep = [p for p in _glob(os.path.join(d, ".candor"), ".scan.json") if "callgraph" not in p]
    if r.returncode != 0 or not rep:
        return (True, False, None, f"candor-scan errored: {r.stderr.decode()[:300]}")
    return (True, True, leaf_set(rep[0], ("::",)), None)


def scan_java(ws):
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
        if not cands:
            print("  [java]  building candor-java (shadowJar)...")
            b = run(["./gradlew", "-q", "shadowJar"], cwd=CANDOR_JAVA)
            if b.returncode != 0:
                return (True, False, None, "gradlew shadowJar failed (set CANDOR_JAVA or CANDOR_JAVA_JAR)")
            cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None  # newest, not lexicographic
    if not jar or not os.path.exists(jar):
        return (False, False, None, "no candor-java jar")
    if not shutil.which("javac"):
        return (False, False, None, "no javac on PATH")
    cls = os.path.join(ws, "jout")
    os.makedirs(cls, exist_ok=True)
    c = run(["javac", "-d", cls, os.path.join(ws, "java", "Cases.java")])
    if c.returncode != 0:
        return (True, False, None, f"javac failed: {c.stderr.decode()[:400]}")
    out = os.path.join(ws, "java.json")
    j = run(["java", "-jar", jar, cls, "--json", out])
    if j.returncode != 0 or not os.path.exists(out):
        return (True, False, None, f"candor-java errored: {j.stderr.decode()[:300]}")
    return (True, True, leaf_set(out, (".",)), None)


def scan_ts(ws):
    if not shutil.which("node") or not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")):
        return (False, False, None, "no node / scan.mjs (set CANDOR_TS)")
    d = os.path.join(ws, "ts")
    if not os.path.isdir(os.path.join(CANDOR_TS, "node_modules")):
        run(["npm", "install", "--no-fund", "--no-audit"], cwd=CANDOR_TS)
    pfx = os.path.join(d, "out")
    t = run(["node", os.path.join(CANDOR_TS, "scan.mjs"), d, "--out", pfx])
    out = pfx + ".json"
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        return (True, False, None, f"candor-ts errored: {t.stderr.decode()[:300]}")
    return (True, True, leaf_set(out, (".",)), None)


def scan_swift(ws):
    if not shutil.which("swift") or not os.path.exists(os.path.join(CANDOR_SWIFT, "Package.swift")):
        return (False, False, None, "no swift toolchain / Package.swift (set CANDOR_SWIFT)")
    binp = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(binp):
        print("  [swift] swift build...")
        b = run(["swift", "build"], cwd=CANDOR_SWIFT)
        if b.returncode != 0 or not os.path.exists(binp):
            return (True, False, None, "swift build failed")
    src = os.path.join(ws, "swift", "cases.swift")
    pfx = os.path.join(ws, "swift", "out")
    s = run([binp, src, "--out", pfx])
    rep = [p for p in _glob(os.path.dirname(pfx), ".json") if "callgraph" not in p and os.path.basename(p).startswith("out.")]
    if s.returncode != 0 or not rep:
        return (True, False, None, f"candor-swift errored: {s.stderr.decode()[:300]}")
    return (True, True, leaf_set(rep[0], (".",)), None)  # swift fn names are bare or Type.method


def _glob(d, suffix):
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suffix)]


# =====================================================================================================
# the assertion + matrix print.
# =====================================================================================================
ENGINES = [("rust", scan_rust), ("java", scan_java), ("ts", scan_ts), ("swift", scan_swift)]


def fmt(s):
    return ",".join(sorted(s)) or "(pure)"


def classify(cell, got):
    """Return (ok, label). label in {ok, DROP, FABRICATION} for a single engine vs a cell."""
    if got in cell["accept"]:
        return True, "ok"
    # a DROP: the engine reports pure / is missing the expected effect entirely.
    if got == PURE or (cell["effect"] not in got and got != {UNKNOWN}):
        # pure, or a set with NEITHER the effect nor a lone Unknown -> under-report (missed it)
        if got == PURE:
            return False, "DROP"
        return False, "FABRICATION"  # has something, but not the effect and not bare Unknown
    # has the effect plus extra (and extra isn't the accepted Unknown) -> fabrication of an extra effect
    return False, "FABRICATION"


def main():
    keep = "--keep" in sys.argv[1:]
    cells = build_cells()

    print("=" * 100)
    print("GENERATIVE cross-engine differential -- EFFECT x INDIRECTION matrix")
    print(f"  effects      : {', '.join(e['effect'] for e in EFFECTS)}")
    print(f"  indirections : {', '.join(i['id'] for i in INDIRECTIONS)}")
    print(f"  cells        : {len(cells)}  (each rendered in rust / java / ts / swift)")
    print("=" * 100)

    ws = tempfile.mkdtemp(prefix="candor-gendiff-")
    write_sources(ws, cells)

    print("\nscanning each generated tree with its engine...")
    results = {}   # engine -> {leaf -> inferred set}
    skipped = {}   # engine -> reason
    failed = {}    # engine -> reason  (present-but-broken)
    for eng, fn in ENGINES:
        present, ok, got, err = fn(ws)
        if not present:
            skipped[eng] = err
            print(f"  {eng:6s} SKIPPED -- {err}")
        elif not ok:
            failed[eng] = err
            print(f"  {eng:6s} FAILED  -- present but broken: {err}")
        else:
            results[eng] = got
            print(f"  {eng:6s} ok -- {len(got)} fns reported")

    available = [e for e, _ in ENGINES if e in results]

    # ---- the matrix ----
    print("\n" + "MATRIX  (case x engine; expected per cell; (pure)=inferred-empty=omitted)")
    head = f"{'case':22s} {'expected':14s} " + " ".join(f"{e:14s}" for e in available)
    print(head)
    print("-" * len(head))
    disagreements = []   # (cell, engine, got, label)
    cross_div = []       # (cell, {engine:got}) where available engines disagree among themselves
    for c in cells:
        exp_disp = fmt(set(c["accept"][0])) if len(c["accept"]) == 1 else \
            " | ".join(fmt(a) for a in c["accept"])
        row = f"{c['name']:22s} {exp_disp:14s} "
        seen = {}
        for e in available:
            got = results[e].get(c["name"], PURE)
            seen[e] = got
            ok, label = classify(c, got)
            cell_disp = fmt(got) if ok else f"{fmt(got)}!{label[0]}"
            row += f"{cell_disp:14s} "
            if not ok:
                disagreements.append((c, e, got, label))
        # cross-engine divergence among AVAILABLE engines (independent of expected)
        if len({frozenset(v) for v in seen.values()}) > 1:
            cross_div.append((c, seen))
        print(row)
    print("-" * len(head))

    # ---- verdict ----
    print()
    if skipped:
        for e, why in skipped.items():
            print(f"NOTE: engine '{e}' SKIPPED (absent) -- {why}")
    rc = 0
    if failed:
        for e, why in failed.items():
            print(f"FAIL: engine '{e}' present but broken -- {why}")
        rc = 2
    if disagreements:
        rc = rc or 1
        print(f"\n{len(disagreements)} DISAGREEMENT(S) vs expected:")
        for c, e, got, label in disagreements:
            kind = {"DROP": "DROP (under-report -- engine missed the effect)",
                    "FABRICATION": "FABRICATION (a different/extra effect)"}[label]
            allat = {x: fmt(results[x].get(c["name"], PURE)) for x in available}
            print(f"  {c['name']:22s} [{c['indirection']}/{c['effect']}]  engine={e}  got={fmt(got)}  -> {kind}")
            print(f"      all engines: " + ", ".join(f"{k}={v}" for k, v in allat.items()))
    # cross-engine divergence that the per-cell accept rule might tolerate but is still worth NAMING
    pure_cross = [(c, seen) for c, seen in cross_div
                  if not any(d[0]["name"] == c["name"] for d in disagreements)]
    if pure_cross:
        print(f"\n{len(pure_cross)} CROSS-ENGINE DIVERGENCE(S) within the accepted band (NAMED, not failed):")
        for c, seen in pure_cross:
            print(f"  {c['name']:22s} [{c['indirection']}/{c['effect']}]  "
                  + ", ".join(f"{k}={fmt(v)}" for k, v in seen.items()))

    print()
    if rc == 0 and not disagreements:
        n = len(cells)
        print(f"GENERATIVE DIFFERENTIAL: OK -- all {len(available)} available engine(s) agree on every one "
              f"of the {n} cells ({', '.join(available)}).")
    else:
        print("GENERATIVE DIFFERENTIAL: FAILED -- see disagreements above.")

    if keep:
        print(f"\n[--keep] generated workspace retained at: {ws}")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
