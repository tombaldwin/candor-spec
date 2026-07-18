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
    # Rand / Db / Log — the 3 effects the curated fixtures already prove agree across all 4 engines
    # (expected.json: Fs/Net/Exec/Env/Clock + Rand/Db/Log; Ipc/Clipboard are STRUCTURALLY per-engine —
    # no JDK std IPC primitive, no node clipboard model — so they stay out of the cross-engine matrix).
    # Same idiomatic vocab as rust/src/lib.rs · java/Cases.java · candor-ts/Cases.ts · swift Cases.swift.
    dict(id="rand", effect="Rand", sink=dict(
        rust='let _: u64 = rand::random();',
        java='try { byte[] b = new byte[16]; java.security.SecureRandom.getInstanceStrong().nextBytes(b); } catch (Exception e) {}',
        ts='void cryptom.randomBytes(16);',
        swift='_ = Int.random(in: 0..<100)',
    )),
    dict(id="db", effect="Db", sink=dict(
        rust='let _ = rusqlite::Connection::open("x.db");',
        java='try { java.sql.DriverManager.getConnection("jdbc:sqlite:x.db"); } catch (Exception e) {}',
        ts='void new DatabaseSync(":memory:").exec("SELECT 1");',
        swift='var _db: OpaquePointer?; _ = sqlite3_open("x.db", &_db)',
    )),
    dict(id="log", effect="Log", sink=dict(
        rust='log::info!("m");',
        java='java.util.logging.Logger.getLogger("c").info("m");',
        ts='winstonm.info("m");',
        swift='NSLog("m")',
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


# ---- renderers: implicit_conv -- the sink lives in an effectful Display/toString/description, reached
# IMPLICITLY by putting the value in a string context (format/concat/interpolation). No visible call to
# the effectful method -- the engine must resolve the operand's type to its conversion impl. (seam class:
# implicit-conversion, closed 2026-06-18 in all 4 engines.)
def r_implicit_conv(eff, name, sfx):
    W = f"W_{sfx}_ic"
    return {
        "rust":  f'pub struct {W};\n'
                 f'impl std::fmt::Display for {W} {{ fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {{ {eff["sink"]["rust"]} write!(f, "w") }} }}\n'
                 f'pub fn {name}(w: &{W}) -> String {{ format!("{{}}", w) }}',
        "java":  f'  static class {W} {{ public String toString() {{ {eff["sink"]["java"]} return "w"; }} }}\n'
                 f'  public static String {name}({W} w) {{ return "v=" + w; }}',
        "ts":    f'class {W} {{ toString(): string {{ {eff["sink"]["ts"]} return "w"; }} }}\n'
                 f'export function {name}(w: {W}): string {{ return `${{w}}`; }}',
        "swift": f'struct {W}: CustomStringConvertible {{ var description: String {{ {eff["sink"]["swift"]}; return "w" }} }}\n'
                 f'func {name}(_ w: {W}) -> String {{ return "v=\\(w)" }}',
    }


# ---- renderers: fire_forget -- the sink runs in an INLINE closure handed to a spawn/schedule primitive
# (thread/Task/setTimeout). The spawning fn should carry the effect (the closure runs as a direct
# consequence). (seam class: fire-and-forget, closed 2026-06-18.)
def r_fire_forget(eff, name, sfx):
    return {
        "rust":  f'pub fn {name}() {{ std::thread::spawn(|| {{ {eff["sink"]["rust"]} }}); }}',
        "java":  f'  public static void {name}() {{ new Thread(() -> {{ {eff["sink"]["java"]} }}).start(); }}',
        "ts":    f'export function {name}(): void {{ setTimeout(() => {{ {eff["sink"]["ts"]} }}, 0); }}',
        "swift": f'func {name}() {{ Task {{ {eff["sink"]["swift"]} }} }}',
    }


# NOTE: deferred-iterator (a custom Iterator whose next() does the sink, consumed by a for-loop) does NOT
# fit this shared-compilation-unit matrix: the java cells would each declare a class `implements
# java.util.Iterator`, and java's whole-program CHA over `Iterator.next()` then fans out across ALL of
# them (and pollutes the unrelated loop_elem for-each too), unioning every effect — a sound
# over-approximation that the matrix's all-cells-in-one-file layout amplifies. It stays a per-engine test
# (🟡), alongside gate-masking (a POLICY-verdict seam, not an effect-set one) and FFI (expected {Unknown}).


# ---- renderers: lazy_init -- a deferred initializer whose body does the sink, FORCED at an access site
# (the language's idiomatic lazy: LazyLock / static-holder / memoized getter / lazy var). The forcing fn
# must carry it. (seam class: lazy-init.)
def r_lazy_init(eff, name, sfx):
    L = f"L_{sfx}_li"
    return {
        "rust":  f'pub static {L}: std::sync::LazyLock<u8> = std::sync::LazyLock::new(|| {{ {eff["sink"]["rust"]} 0u8 }});\n'
                 f'pub fn {name}() {{ let _ = *{L}; }}',
        "java":  f'  static class {L} {{ static final Object V = init(); static Object init() {{ {eff["sink"]["java"]} return new Object(); }} }}\n'
                 f'  public static void {name}() {{ Object o = {L}.V; }}',
        "ts":    f'class {L} {{ private _v: number | undefined; get v(): number {{ if (this._v === undefined) {{ {eff["sink"]["ts"]} this._v = 1; }} return this._v; }} }}\n'
                 f'export function {name}(l: {L}): number {{ return l.v; }}',
        "swift": f'struct {L} {{ lazy var v: Int = {{ {eff["sink"]["swift"]}; return 1 }}() }}\n'
                 f'func {name}(_ l: inout {L}) -> Int {{ return l.v }}',
    }


# ---- renderers: concrete_trait_recv (Case C) -- a trait/interface/protocol method invoked via method
# syntax on a VALUE LITERAL of a concrete type (no binding, no typed param): `T0().run()` where T0 is a
# unit-struct/class with `impl Task for T0`. The engine must resolve the value-literal receiver's type to
# its trait-method impl and infer the effect -- NOT silent-pure. (candor-rust silent-pure bug, fixed
# 0c9f218 Case C; java/ts/swift already resolved it.)
def r_concrete_trait_recv(eff, name, sfx):
    # Type names MUST be Upper-initial and UNDERSCORE-FREE: the value-literal receiver `T0.run()` is the
    # crux of Case C, and an engine (candor-scan) distinguishes a unit-struct value literal from a
    # SCREAMING_SNAKE const by "Upper-initial WITHOUT an underscore", so an underscore-suffixed type name
    # (e.g. `T0_fs_cr`) would read as a const and silently NOT resolve — hiding the very bug this pins.
    cap = sfx.capitalize()  # fs -> Fs ; net -> Net ; ...  (unique per cell, no underscore)
    Tr = f"TaskCr{cap}"     # the trait / interface / protocol
    T0 = f"CrT{cap}"        # the concrete impl, used as a VALUE LITERAL at the call site
    return {
        "rust":  f'pub trait {Tr} {{ fn run(&self); }}\n'
                 f'pub struct {T0};\n'
                 f'impl {Tr} for {T0} {{ fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                 f'pub fn {name}() {{ {T0}.run(); }}',
        "java":  f'  interface {Tr} {{ void run() throws Exception; }}\n'
                 f'  static class {T0} implements {Tr} {{ public void run() {{ {eff["sink"]["java"]} }} }}\n'
                 f'  public static void {name}() throws Exception {{ new {T0}().run(); }}',
        "ts":    f'interface {Tr} {{ run(): void; }}\n'
                 f'class {T0} implements {Tr} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                 f'export function {name}(): void {{ new {T0}().run(); }}',
        "swift": f'protocol {Tr} {{ func run() }}\n'
                 f'struct {T0}: {Tr} {{ func run() {{ {eff["sink"]["swift"]} }} }}\n'
                 f'func {name}() {{ {T0}().run() }}',
    }


# ---- renderers: fn_returned_dyn (Case D) -- dispatch through a FACTORY fn returning a boxed/existential
# trait object: `fn get() -> Box<dyn Task> { .. } ; get().run()`. The factory-call receiver has no nominal
# type; the engine must resolve it via CHA to the visible impl and infer the effect -- NOT silent-pure.
# (candor-rust silent-pure bug, fixed 0c9f218 Case D; java/ts/swift already resolved it.)
def r_fn_returned_dyn(eff, name, sfx):
    # Underscore-free Upper-initial type names (same rationale as Case C: keep the concrete impl from
    # reading as a const in any engine's value-literal heuristic).
    cap = sfx.capitalize()
    Tr = f"TaskFd{cap}"     # the trait / interface / protocol
    T0 = f"FdT{cap}"        # the sole concrete impl (CHA resolves to it)
    get = f"getFd{cap}"     # the factory returning the trait-object type
    return {
        "rust":  f'pub trait {Tr} {{ fn run(&self); }}\n'
                 f'struct {T0};\n'
                 f'impl {Tr} for {T0} {{ fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                 f'fn {get}() -> Box<dyn {Tr}> {{ Box::new({T0}) }}\n'
                 f'pub fn {name}() {{ {get}().run(); }}',
        "java":  f'  interface {Tr} {{ void run() throws Exception; }}\n'
                 f'  static class {T0} implements {Tr} {{ public void run() {{ {eff["sink"]["java"]} }} }}\n'
                 f'  static {Tr} {get}() {{ return new {T0}(); }}\n'
                 f'  public static void {name}() throws Exception {{ {get}().run(); }}',
        "ts":    f'interface {Tr} {{ run(): void; }}\n'
                 f'class {T0} implements {Tr} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                 f'function {get}(): {Tr} {{ return new {T0}(); }}\n'
                 f'export function {name}(): void {{ {get}().run(); }}',
        "swift": f'protocol {Tr} {{ func run() }}\n'
                 f'struct {T0}: {Tr} {{ func run() {{ {eff["sink"]["swift"]} }} }}\n'
                 f'func {get}() -> any {Tr} {{ return {T0}() }}\n'
                 f'func {name}() {{ {get}().run() }}',
    }


INDIRECTIONS = [
    dict(id="direct",              render=r_direct,              accept=acc_exact),
    dict(id="local_call",          render=r_local_call,          accept=acc_exact),
    dict(id="method_recv",         render=r_method_recv,         accept=acc_exact),
    dict(id="loop_elem",           render=r_loop_elem,           accept=acc_exact),
    dict(id="field",               render=r_field,               accept=acc_exact),
    dict(id="callback",            render=r_callback,            accept=acc_callback),
    dict(id="implicit_conv",       render=r_implicit_conv,       accept=acc_exact),
    dict(id="fire_forget",         render=r_fire_forget,         accept=acc_exact),
    dict(id="lazy_init",           render=r_lazy_init,           accept=acc_exact),
    dict(id="concrete_trait_recv", render=r_concrete_trait_recv, accept=acc_exact),
    dict(id="fn_returned_dyn",     render=r_fn_returned_dyn,     accept=acc_exact),
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
        f.write('import * as cp from "node:child_process";\n')
        f.write('import * as cryptom from "node:crypto";\n')
        f.write('import { DatabaseSync } from "node:sqlite";\n')
        f.write('import * as winstonm from "winston";\n\n')
        f.write("\n\n".join(c["code"]["ts"] for c in cells) + "\n")

    # ---- swift file ----
    sw = os.path.join(ws, "swift")
    os.makedirs(sw, exist_ok=True)
    with open(os.path.join(sw, "cases.swift"), "w") as f:
        f.write("// GENERATED by gen_differential.py -- do not edit.\n")
        f.write("import Foundation\n")
        f.write("import SQLite3\n\n")
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
    rep = [p for p in _glob(os.path.dirname(pfx), ".json") if "callgraph" not in p and "hierarchy" not in p and os.path.basename(p).startswith("out.")]
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
    # STRICT mode: a SKIPPED (absent) engine must FAIL, not silently pass with fewer engines — else the
    # gate's "all N engines agree" verdict can quietly degrade (a misconfigured CI missing node/swift gets
    # a false multi-engine green). CI sets CONFORMANCE_REQUIRE_ALL=1; local dev leaves it unset (lenient).
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print(f"FAIL (strict): engine '{e}' REQUIRED (CONFORMANCE_REQUIRE_ALL set) but absent -- {why}")
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
