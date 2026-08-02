#!/usr/bin/env python3
"""
P1 — SPLIT-INVARIANCE, as a GENERATED property (SCAN-BOUNDARY-WORK-QUEUE.md §3).

WHAT THIS IS, AND WHY IT IS NOT gen_differential.py
---------------------------------------------------
`gen_differential.py` asks *"do the four engines agree?"*. That question has a known blind spot: all four
engines share one spec, one set of design docs and one author's mental model, so when the model is wrong
all four implement the same wrong thing and the suite reports OK. It has done exactly that twice (the
coverage door, the malformed manifest — both four-way).

The sharpest example is not either of those, because neither requires you to take anyone's word for it.
It is `conformance/frontier_differential.py`, sitting in this directory. It runs three arms and prints
that three engines must AGREE — but `frontier_swift()` uses candor-swift as the PRODUCER only and then
runs **rust's `candor-query`** as the consumer, because candor-swift ships no `callers` verb. So the
three "independent" votes are java(producer+consumer), ts(producer+consumer), and swift(producer) +
rust(consumer): a common-mode defect in the rust consumer appears in two arms and reads as agreement.
A cross-engine differential presenting a SHARED CONSUMER as an independent third vote — in the suite
built to catch exactly that. (Found 2026-07-27; repair filed in the work queue, not this file's job.)
It is the cleanest possible statement of why an engine-agreement oracle is not enough on its own.

This file asks a different question, of ONE engine at a time:

    scan(A ∪ B)   ≡   scan(B) chained with report(A)          -- modulo disclosure

i.e. **does the engine agree with ITSELF** when the same program is rendered once as a single tree and
once as two chained packages? A self-differential is immune to common-mode BY CONSTRUCTION: four engines
can share a wrong model of the spec, but an engine cannot share a wrong model with ITSELF across two
renderings of one program. **The engine's own single-tree answer is the oracle for its chained answer** —
there is no reference implementation, no second opinion and no spec interpretation in the loop.

There is therefore NO EXPECTED-VALUE TABLE in this file, and there must never be one. If you find
yourself adding one you have turned a self-differential back into a hand-written fixture, which is the
thing this replaces. (The whole scan-boundary vein was ONE property hand-instantiated 44+ times; five of
those fixtures could not reach the code they named, because a human chose each shape.)

THE ASSERTION IS DIRECTIONAL — "modulo disclosure" is the subtle part
--------------------------------------------------------------------
The chained arm may LEGITIMATELY carry MORE disclosure than the single-tree arm (an `Unknown` with a
reason, a coverage hedge, an `invisible`) because a boundary genuinely exists there and the engine can
see less across it. What it must NEVER do is carry FEWER EFFECTS with NO disclosure, or turn a function
that was present ABSENT (under the ⟨0.21⟩ manifest an absent-but-analyzed function is a positive purity
CLAIM, not a gap). So:

    single-tree effect set  ⊆  chained effect set          ... is NOT the rule (too strong: see HEDGE)
    an effect present single-tree and gone chained
      with NO disclosure at all                            ... IS the cardinal sin           -> FAIL
    a function present single-tree and ABSENT chained      ... IS a ⟨0.21⟩ purity claim      -> FAIL
    an effect traded for a DIFFERENT effect                ... is a loss AND a fabrication   -> FAIL
    an effect traded for `Unknown`                         ... is a DISCLOSED precision loss -> counted
    extra `Unknown` / extra disclosure chained             ... is ALLOWED                    -> counted
    an effect the single-tree arm did NOT have             ... is a chained fabrication      -> counted

**DO NOT "SIMPLIFY" THIS TO EQUALITY.** Equality would fail every case the family has already decided is
correct — PART 21's ruling is precisely that a chained consumer which cannot form a key MUST disclose
`Unknown` where the single-tree arm resolves the effect. That is the HEDGE band below, and it is a
*designed* asymmetry, not slack. `--strict-hedge` fails on it too, for measuring how big the band is.

HOW THE TWO ARMS ARE BUILT SO THE COMPARISON MEANS SOMETHING
------------------------------------------------------------
Both arms are rendered from THE SAME per-cell source text, partitioned differently:

  * the effectful leaf (the helper fn / the type whose method does the I/O / the lazy holder / the
    Display impl) is the DEP half;
  * the entry fn that reaches it is the APP half.

  arm S (single tree)  : dep half + app half in ONE package, scanned once.
  arm C (split+chained): dep half in package A, app half in package B; A is scanned first and ITS REPORT
                         is chained into B's scan via CANDOR_DEPS.

java gets this exactly: one `javac` produces the class files and the two arms differ ONLY in how the
output directory is partitioned. The other three differ by ONE PREAMBLE LINE and nothing else — the app
half's declaration text is byte-identical in both arms, and every dep name it uses is spelled
unqualified, so the only thing that varies is where that name is bound:
    rust   arm S: dep decls at the crate root, no preamble  |  arm C: `use deplib::{…};`
    ts     arm S: `import { … } from "./dep";`              |  arm C: `… from "deplib";`
    swift  arm S: (same target, no import)                  |  arm C: `import DepLib`
    java   arm S and arm C: identical source AND identical class files.
Keeping the app half unqualified is not cosmetic. An earlier draft wrote the rust arm as `deplib::X` in
both arms (a `pub mod deplib { … }` wrapper in arm S) and that ALONE turned 16 of rust's 80 cells vacuous:
candor-scan does not resolve a module-path-qualified unit-struct value literal (`m::T.run()`), and does
not charge a module-path-qualified lazy-static read (`*m::L`) — so the single-tree ORACLE went silent and
the rows stopped demanding anything. A rendering choice that weakens the oracle is invisible in the
verdict and shows up only in the vacuity count; that is what the count is for.

VACUITY (standing bar item 8 — a generator that emits 200 cases of which 3 cross a boundary is measuring
nothing). Every cell is classified from the ENGINE'S OWN output, not asserted:
  * `direct` cannot be split at all (the sink is inline in the entry) — counted as STRUCTURALLY VACUOUS
    and not rendered.
  * a cell whose SINGLE-TREE arm reports the entry pure/absent demands nothing of the chained arm —
    counted VACUOUS, per engine, and printed.
  * the run FAILS if the live (non-vacuous) count is zero for any available engine.

USAGE
    python3 gen_split_invariance.py                 # full matrix, exit non-zero on any cardinal loss
    python3 gen_split_invariance.py --keep          # keep the generated workspace (prints its path)
    python3 gen_split_invariance.py --only lazy_init,field
    python3 gen_split_invariance.py --strict-hedge  # also fail on DISCLOSED precision loss
    python3 gen_split_invariance.py --baseline split-invariance-baseline.json   # the ratchet (PART 24)
Run it WITHOUT --baseline to see the raw truth; run.sh passes the baseline. See the RATCHET section near
the bottom of this file for why a waiver list is not an expected-value table.
Engine resolution is inherited from gen_differential.py (CANDOR / CANDOR_JAVA / CANDOR_TS / CANDOR_SWIFT,
and the *_BIN / *_JAR overrides), and so is the EFFECTS table — the effect vocabulary stays in ONE place.
"""

# NO NORMATIVE CLAUSES, AND THAT IS THE HONEST DECLARATION. P1 is a pure self-differential: its oracle is
# the engine's OWN other arm, not the spec — which is what "there is NO EXPECTED-VALUE TABLE and there must
# never be one" means above. SPEC.md nowhere states that a split+chained scan must agree with the
# single-tree one; that is a property OF an engine, not a MUST the contract imposes. Declared EMPTY rather
# than omitted so that "enforces nothing normative" and "somebody forgot to cite" stay distinguishable
# (clause_check.py).
SPEC_CLAUSES = []

import json
import os
import shutil
import subprocess
import sys
import tempfile

import gen_differential as gd

HERE = os.path.dirname(os.path.abspath(__file__))
UNKNOWN = "Unknown"

# =====================================================================================================
# SPLIT RENDERERS.
#
# Each returns {"names": [...], <lang>: {"dep": <decls>, "app": <decls>}}.
# `names` is the list of dep identifiers the app half references UNQUALIFIED; the writers turn it into
# rust's `use deplib::{…};` and ts's `import { … } from …`. swift needs no name list (a module import
# brings everything in) and java is the exception that needs none either: it addresses the dep half as
# `dep.Dep.X`, which is the SAME text in both arms because both arms compile the same two packages.
#
# INVARIANT FOR ANY NEW RENDERER: every effectful statement goes in "dep"; the entry fn (and only helper
# scaffolding with no I/O of its own) goes in "app". A renderer that leaves a sink in the app half
# produces a cell that passes for free — it would show up as a live cell that can never fail.
# =====================================================================================================

# ---- local_call: a plain cross-package free function -------------------------------------------------

# ⟨0.24⟩ KNOWN-VACUOUS SHAPES — the per-shape floor's ratchet. Measured 2026-08-01, the first run after the
# floor existed. A shape listed here produced cells and ZERO live ones for that engine, so those cells prove
# nothing today. Two different things live in this table and they MUST be told apart by triage, not by
# assumption:
#   * legitimately N/A for the language (a Rust `dyn` return has no Java analogue), where the honest fix is
#     to stop EMITTING the cells rather than to waive them — a cell that cannot fire is not coverage;
#   * a fixture that STOPPED TRIGGERING, which is a live defect wearing the same clothes.
# Neither is distinguishable from the other by looking at the count, which is why this needs a reason per
# row and why none is written yet. It ratchets: a shape going dead that is NOT listed fails the run.
KNOWN_VACUOUS = {
    "rust":  {"callback", "fn_returned_dyn"},
    "java":  {"fn_returned_dyn"},
    "swift": {"fn_returned_dyn"},
    "ts":    {"callback", "fn_returned_dyn", "lazy_init"},
}

def s_local_call(eff, name, sfx):
    h = f"h_{sfx}_lc"
    return {
        "names": [h],
        "rust": dict(dep=f'pub fn {h}() {{ {eff["sink"]["rust"]} }}',
                     app=f'pub fn {name}() {{ {h}(); }}'),
        "java": dict(dep=f'  public static void {h}() {{ {eff["sink"]["java"]} }}',
                     app=f'  public static void {name}() {{ dep.Dep.{h}(); }}'),
        "ts":   dict(dep=f'export function {h}(): void {{ {eff["sink"]["ts"]} }}',
                     app=f'export function {name}(): void {{ {h}(); }}'),
        "swift": dict(dep=f'public func {h}() {{ {eff["sink"]["swift"]} }}',
                      app=f'func {name}() {{ {h}() }}'),
    }


# ---- method_recv: a dep TYPE whose method does the sink, reached through a typed parameter ------------
def s_method_recv(eff, name, sfx):
    W = f"W{sfx.capitalize()}Mr"
    return {
        "names": [W],
        "rust": dict(dep=f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}',
                     app=f'pub fn {name}(w: &{W}) {{ w.run(); }}'),
        "java": dict(dep=f'  public static class {W} {{ public void run() {{ {eff["sink"]["java"]} }} }}',
                     app=f'  public static void {name}(dep.Dep.{W} w) {{ w.run(); }}'),
        "ts":   dict(dep=f'export class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}',
                     app=f'export function {name}(w: {W}): void {{ w.run(); }}'),
        "swift": dict(dep=f'public struct {W} {{ public init() {{}} public func run() {{ {eff["sink"]["swift"]} }} }}',
                      app=f'func {name}(_ w: {W}) {{ w.run() }}'),
    }


# ---- loop_elem: iterate a collection of a DEP element type and invoke its method ---------------------
def s_loop_elem(eff, name, sfx):
    W = f"W{sfx.capitalize()}Le"
    return {
        "names": [W],
        "rust": dict(dep=f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}',
                     app=f'pub fn {name}(xs: Vec<{W}>) {{ for c in xs {{ c.run(); }} }}'),
        "java": dict(dep=f'  public static class {W} {{ public void run() {{ {eff["sink"]["java"]} }} }}',
                     app=f'  public static void {name}(java.util.List<dep.Dep.{W}> xs) {{ for (dep.Dep.{W} c : xs) {{ c.run(); }} }}'),
        "ts":   dict(dep=f'export class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}',
                     app=f'export function {name}(xs: {W}[]): void {{ for (const c of xs) {{ c.run(); }} }}'),
        "swift": dict(dep=f'public struct {W} {{ public init() {{}} public func run() {{ {eff["sink"]["swift"]} }} }}',
                      app=f'func {name}(_ xs: [{W}]) {{ for c in xs {{ c.run() }} }}'),
    }


# ---- field: the dep type is a FIELD of a local holder; the crossing is holder.drive -> W.run ---------
# (the holder stays in the app half deliberately: it puts the boundary on the FIELD READ, which is the
# sharper of the two placements — with the holder in the dep half the crossing degenerates to a plain
# method call already covered by method_recv.)
def s_field(eff, name, sfx):
    W = f"W{sfx.capitalize()}Fl"
    H = f"H{sfx.capitalize()}Fl"
    dr = f"drive_{sfx}_fl"
    return {
        "names": [W],
        "rust": dict(dep=f'pub struct {W};\nimpl {W} {{ pub fn run(&self) {{ {eff["sink"]["rust"]} }} }}',
                     app=f'pub struct {H} {{ pub f: {W} }}\n'
                         f'impl {H} {{ pub fn {dr}(&self) {{ self.f.run(); }} }}\n'
                         f'pub fn {name}(h: &{H}) {{ h.{dr}(); }}'),
        "java": dict(dep=f'  public static class {W} {{ public void run() {{ {eff["sink"]["java"]} }} }}',
                     app=f'  static class {H} {{ dep.Dep.{W} f; void {dr}() {{ f.run(); }} }}\n'
                         f'  public static void {name}({H} h) {{ h.{dr}(); }}'),
        "ts":   dict(dep=f'export class {W} {{ run(): void {{ {eff["sink"]["ts"]} }} }}',
                     app=f'class {H} {{ f: {W} = new {W}(); {dr}(): void {{ this.f.run(); }} }}\n'
                         f'export function {name}(h: {H}): void {{ h.{dr}(); }}'),
        "swift": dict(dep=f'public struct {W} {{ public init() {{}} public func run() {{ {eff["sink"]["swift"]} }} }}',
                      app=f'struct {H} {{ let f: {W}; func {dr}() {{ f.run() }} }}\n'
                          f'func {name}(_ h: {H}) {{ h.{dr}() }}'),
    }


# ---- callback: the dep's sink fn is passed BY NAME to a local higher-order fn ------------------------
def s_callback(eff, name, sfx):
    s = f"s_{sfx}_cb"
    hof = f"hof_{sfx}_cb"
    return {
        "names": [s],
        "rust": dict(dep=f'pub fn {s}() {{ {eff["sink"]["rust"]} }}',
                     app=f'fn {hof}(cb: fn()) {{ cb(); }}\npub fn {name}() {{ {hof}({s}); }}'),
        "java": dict(dep=f'  public static void {s}() {{ {eff["sink"]["java"]} }}',
                     app=f'  static void {hof}(Runnable cb) {{ cb.run(); }}\n'
                         f'  public static void {name}() {{ {hof}(dep.Dep::{s}); }}'),
        "ts":   dict(dep=f'export function {s}(): void {{ {eff["sink"]["ts"]} }}',
                     app=f'function {hof}(cb: () => void): void {{ cb(); }}\n'
                         f'export function {name}(): void {{ {hof}({s}); }}'),
        "swift": dict(dep=f'public func {s}() {{ {eff["sink"]["swift"]} }}',
                      app=f'func {hof}(_ cb: () -> Void) {{ cb() }}\nfunc {name}() {{ {hof}({s}) }}'),
    }


# ---- implicit_conv: PART 20's shape, generated. the dep type's Display/toString/description does the
#      sink; the app half only puts the value in a string context, with no visible call. ---------------
def s_implicit_conv(eff, name, sfx):
    W = f"W{sfx.capitalize()}Ic"
    return {
        "names": [W],
        "rust": dict(dep=f'pub struct {W};\n'
                         f'impl std::fmt::Display for {W} {{ fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {{ {eff["sink"]["rust"]} write!(f, "w") }} }}',
                     app=f'pub fn {name}(w: &{W}) -> String {{ format!("{{}}", w) }}'),
        "java": dict(dep=f'  public static class {W} {{ public String toString() {{ {eff["sink"]["java"]} return "w"; }} }}',
                     app=f'  public static String {name}(dep.Dep.{W} w) {{ return "v=" + w; }}'),
        "ts":   dict(dep=f'export class {W} {{ toString(): string {{ {eff["sink"]["ts"]} return "w"; }} }}',
                     app=f'export function {name}(w: {W}): string {{ return `${{w}}`; }}'),
        "swift": dict(dep=f'public struct {W}: CustomStringConvertible {{ public init() {{}} public var description: String {{ {eff["sink"]["swift"]}; return "w" }} }}',
                      app=f'func {name}(_ w: {W}) -> String {{ return "v=\\(w)" }}'),
    }


# ---- fire_forget: the app spawns a closure that calls the dep's sink fn ------------------------------
def s_fire_forget(eff, name, sfx):
    s = f"s_{sfx}_ff"
    return {
        "names": [s],
        "rust": dict(dep=f'pub fn {s}() {{ {eff["sink"]["rust"]} }}',
                     app=f'pub fn {name}() {{ std::thread::spawn(|| {{ {s}(); }}); }}'),
        "java": dict(dep=f'  public static void {s}() {{ {eff["sink"]["java"]} }}',
                     app=f'  public static void {name}() {{ new Thread(() -> {{ dep.Dep.{s}(); }}).start(); }}'),
        "ts":   dict(dep=f'export function {s}(): void {{ {eff["sink"]["ts"]} }}',
                     app=f'export function {name}(): void {{ setTimeout(() => {{ {s}(); }}, 0); }}'),
        "swift": dict(dep=f'public func {s}() {{ {eff["sink"]["swift"]} }}',
                      app=f'func {name}() {{ Task {{ {s}() }} }}'),
    }


# ---- lazy_init: PART 19's shape, generated. the dep holds a deferred initializer; the app FORCES it. --
def s_lazy_init(eff, name, sfx):
    L = f"L{sfx.capitalize()}Li"
    return {
        "names": [L],
        "rust": dict(dep=f'pub static {L}: std::sync::LazyLock<u8> = std::sync::LazyLock::new(|| {{ {eff["sink"]["rust"]} 0u8 }});',
                     app=f'pub fn {name}() {{ let _ = *{L}; }}'),
        "java": dict(dep=f'  public static class {L} {{ public static final Object V = init(); static Object init() {{ {eff["sink"]["java"]} return new Object(); }} }}',
                     app=f'  public static void {name}() {{ Object o = dep.Dep.{L}.V; }}'),
        "ts":   dict(dep=f'export class {L} {{ private _v: number | undefined; get v(): number {{ if (this._v === undefined) {{ {eff["sink"]["ts"]} this._v = 1; }} return this._v; }} }}',
                     app=f'export function {name}(l: {L}): number {{ return l.v; }}'),
        "swift": dict(dep=f'public struct {L} {{ public init() {{}} public lazy var v: Int = {{ {eff["sink"]["swift"]}; return 1 }}() }}',
                      app=f'func {name}(_ l: inout {L}) -> Int {{ return l.v }}'),
    }


# ---- concrete_trait_recv: a dep trait/interface/protocol impl invoked on a VALUE LITERAL -------------
def s_concrete_trait_recv(eff, name, sfx):
    cap = sfx.capitalize()
    Tr, T0 = f"TaskCr{cap}", f"CrT{cap}"
    return {
        "names": [Tr, T0],
        "rust": dict(dep=f'pub trait {Tr} {{ fn run(&self); }}\npub struct {T0};\n'
                         f'impl {Tr} for {T0} {{ fn run(&self) {{ {eff["sink"]["rust"]} }} }}',
                     app=f'pub fn {name}() {{ {T0}.run(); }}'),
        "java": dict(dep=f'  public interface {Tr} {{ void run(); }}\n'
                         f'  public static class {T0} implements {Tr} {{ public void run() {{ {eff["sink"]["java"]} }} }}',
                     app=f'  public static void {name}() {{ new dep.Dep.{T0}().run(); }}'),
        "ts":   dict(dep=f'export interface {Tr} {{ run(): void; }}\n'
                         f'export class {T0} implements {Tr} {{ run(): void {{ {eff["sink"]["ts"]} }} }}',
                     app=f'export function {name}(): void {{ new {T0}().run(); }}'),
        "swift": dict(dep=f'public protocol {Tr} {{ func run() }}\n'
                          f'public struct {T0}: {Tr} {{ public init() {{}} public func run() {{ {eff["sink"]["swift"]} }} }}',
                      app=f'func {name}() {{ {T0}().run() }}'),
    }


# ---- fn_returned_dyn: dispatch through a dep FACTORY returning an existential ------------------------
# (this is the DEP-RECEIVER-TYPING half-1 shape; PART 21's ruling means a chained `Unknown` here is a
# CORRECT answer, so expect this row to sit in the HEDGE band rather than the OK band on some engines.)
def s_fn_returned_dyn(eff, name, sfx):
    cap = sfx.capitalize()
    Tr, T0, get = f"TaskFd{cap}", f"FdT{cap}", f"getFd{cap}"
    return {
        "names": [Tr, get],
        "rust": dict(dep=f'pub trait {Tr} {{ fn run(&self); }}\npub struct {T0};\n'
                         f'impl {Tr} for {T0} {{ fn run(&self) {{ {eff["sink"]["rust"]} }} }}\n'
                         f'pub fn {get}() -> Box<dyn {Tr}> {{ Box::new({T0}) }}',
                     app=f'pub fn {name}() {{ {get}().run(); }}'),
        "java": dict(dep=f'  public interface {Tr} {{ void run(); }}\n'
                         f'  public static class {T0} implements {Tr} {{ public void run() {{ {eff["sink"]["java"]} }} }}\n'
                         f'  public static {Tr} {get}() {{ return new {T0}(); }}',
                     app=f'  public static void {name}() {{ dep.Dep.{get}().run(); }}'),
        "ts":   dict(dep=f'export interface {Tr} {{ run(): void; }}\n'
                         f'export class {T0} implements {Tr} {{ run(): void {{ {eff["sink"]["ts"]} }} }}\n'
                         f'export function {get}(): {Tr} {{ return new {T0}(); }}',
                     app=f'export function {name}(): void {{ {get}().run(); }}'),
        "swift": dict(dep=f'public protocol {Tr} {{ func run() }}\n'
                          f'public struct {T0}: {Tr} {{ public init() {{}} public func run() {{ {eff["sink"]["swift"]} }} }}\n'
                          f'public func {get}() -> any {Tr} {{ return {T0}() }}',
                      app=f'func {name}() {{ {get}().run() }}'),
    }


SPLITS = [
    dict(id="local_call",          render=s_local_call),
    dict(id="method_recv",         render=s_method_recv),
    dict(id="loop_elem",           render=s_loop_elem),
    dict(id="field",               render=s_field),
    dict(id="callback",            render=s_callback),
    dict(id="implicit_conv",       render=s_implicit_conv),
    dict(id="fire_forget",         render=s_fire_forget),
    dict(id="lazy_init",           render=s_lazy_init),
    dict(id="concrete_trait_recv", render=s_concrete_trait_recv),
    dict(id="fn_returned_dyn",     render=s_fn_returned_dyn),
]

# `direct` from gen_differential's INDIRECTIONS has NO dep half — the sink is inline in the entry fn — so
# it cannot cross a boundary and is not rendered. Named here (rather than silently dropped) so the
# vacuity accounting below covers the whole EFFECT x INDIRECTION space.
UNSPLITTABLE = ["direct"]

TS_SINK_IMPORTS = (
    'import * as fsm from "node:fs";\n'
    'import * as netm from "node:net";\n'
    'import * as cp from "node:child_process";\n'
    'import * as cryptom from "node:crypto";\n'
    'import { DatabaseSync } from "node:sqlite";\n'
    'import * as winstonm from "winston";\n'
)


def build_cells(only):
    cells = []
    for sp in SPLITS:
        if only and sp["id"] not in only:
            continue
        for eff in gd.EFFECTS:
            name = f"p1_{eff['id']}_{sp['id']}"
            cells.append(dict(name=name, effect=eff["effect"], effect_id=eff["id"],
                              split=sp["id"], code=sp["render"](eff, name, eff["id"])))
    return cells


# =====================================================================================================
# WRITING THE TWO ARMS. One package-pair PER SPLIT (all 8 effects inside), not per cell: per-cell would
# be 8x the scans for no extra signal, and one-pair-for-everything would let an engine's whole-program
# CHA fan out across UNRELATED indirections in the single-tree arm only (java's `Runnable`/`Iterator`
# case), making arm S artificially richer and manufacturing false losses. Per-split keeps every shared
# supertype inside one indirection, where both arms see it.
# =====================================================================================================

def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


HDR = "// GENERATED by gen_split_invariance.py -- do not edit.\n"


def write_rust(root, cells):
    dep = "\n\n".join(c["code"]["rust"]["dep"] for c in cells)
    app = "\n\n".join(c["code"]["rust"]["app"] for c in cells)
    names = sorted({n for c in cells for n in c["code"]["names"]})
    use = ("use deplib::{" + ", ".join(names) + "};\n") if names else ""
    # arm S: dep decls at the CRATE ROOT beside the app decls — one flat crate, which is what
    # `scan(A u B)` means. NOT a `pub mod deplib { … }` wrapper: see the vacuity note in the header.
    _w(os.path.join(root, "single", "Cargo.toml"), '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(root, "single", "src", "lib.rs"), HDR + dep + "\n\n" + app + "\n")
    # arm C: the same app text, one `use` line, a real crate boundary.
    _w(os.path.join(root, "split", "deplib", "Cargo.toml"), '[package]\nname="deplib"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(root, "split", "deplib", "src", "lib.rs"), HDR + dep + "\n")
    _w(os.path.join(root, "split", "app", "Cargo.toml"),
       '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\ndeplib={path="../deplib"}\n')
    _w(os.path.join(root, "split", "app", "src", "lib.rs"), HDR + use + "\n" + app + "\n")


def write_java(root, cells):
    dep = "\n".join(c["code"]["java"]["dep"] for c in cells)
    app = "\n".join(c["code"]["java"]["app"] for c in cells)
    _w(os.path.join(root, "src", "dep", "Dep.java"), HDR + "package dep;\npublic class Dep {\n" + dep + "\n}\n")
    _w(os.path.join(root, "src", "app", "App.java"), HDR + "package app;\npublic class App {\n" + app + "\n}\n")


def write_ts(root, cells):
    dep = "\n\n".join(c["code"]["ts"]["dep"] for c in cells)
    app = "\n\n".join(c["code"]["ts"]["app"] for c in cells)
    names = sorted({n for c in cells for n in c["code"]["names"]})
    imp = "import { " + ", ".join(names) + " } from %s;\n" if names else "%s;\n"
    # arm S: one package, dep half in a sibling module (the intra-project import edge).
    _w(os.path.join(root, "single", "package.json"), '{"name":"app","version":"0.0.0"}\n')
    _w(os.path.join(root, "single", "src", "dep.ts"), HDR + TS_SINK_IMPORTS + "\n" + dep + "\n")
    _w(os.path.join(root, "single", "src", "index.ts"), HDR + (imp % '"./dep"') + "\n" + app + "\n")
    # arm C: a real package boundary, resolved through node_modules (PART 20's shape).
    _w(os.path.join(root, "split", "deplib", "package.json"),
       '{"name":"deplib","version":"0.0.0","main":"src/index.ts"}\n')
    _w(os.path.join(root, "split", "deplib", "src", "index.ts"), HDR + TS_SINK_IMPORTS + "\n" + dep + "\n")
    _w(os.path.join(root, "split", "app", "package.json"),
       '{"name":"app","version":"0.0.0","dependencies":{"deplib":"file:../deplib"}}\n')
    _w(os.path.join(root, "split", "app", "src", "index.ts"), HDR + (imp % '"deplib"') + "\n" + app + "\n")
    nm = os.path.join(root, "split", "app", "node_modules")
    os.makedirs(nm, exist_ok=True)
    link = os.path.join(nm, "deplib")
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(os.path.join(root, "split", "deplib"), link)


SW_IMPORTS = "import Foundation\nimport SQLite3\n"


def write_swift(root, cells):
    dep = "\n\n".join(c["code"]["swift"]["dep"] for c in cells)
    app = "\n\n".join(c["code"]["swift"]["app"] for c in cells)
    pkg_lib = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "DepLib", products: [.library(name: "DepLib", targets: ["DepLib"])],'
               ' targets: [.target(name: "DepLib")])\n')
    pkg_app_split = ('// swift-tools-version:5.9\nimport PackageDescription\n'
                     'let package = Package(name: "App", dependencies: [.package(path: "../deplib")],'
                     ' targets: [.executableTarget(name: "App", dependencies: [.product(name: "DepLib", package: "deplib")])])\n')
    pkg_app_single = ('// swift-tools-version:5.9\nimport PackageDescription\n'
                      'let package = Package(name: "App", targets: [.executableTarget(name: "App")])\n')
    # arm S
    _w(os.path.join(root, "single", "Package.swift"), pkg_app_single)
    _w(os.path.join(root, "single", "Sources", "App", "dep.swift"), HDR + SW_IMPORTS + "\n" + dep + "\n")
    _w(os.path.join(root, "single", "Sources", "App", "main.swift"), HDR + SW_IMPORTS + "\n" + app + "\n")
    # arm C
    _w(os.path.join(root, "split", "deplib", "Package.swift"), pkg_lib)
    _w(os.path.join(root, "split", "deplib", "Sources", "DepLib", "dep.swift"), HDR + SW_IMPORTS + "\n" + dep + "\n")
    _w(os.path.join(root, "split", "app", "Package.swift"), pkg_app_split)
    _w(os.path.join(root, "split", "app", "Sources", "App", "main.swift"),
       HDR + SW_IMPORTS + "import DepLib\n\n" + app + "\n")


# =====================================================================================================
# RUNNING THE ENGINES. Each returns (single_map, chained_map, dep_map, err) with maps leaf-name ->
# frozenset(inferred), or (None, None, None, reason).
#
# Item 7 of the standing bar ("delete the output before you measure a control") is enforced structurally:
# every arm gets a FRESH directory tree under a fresh mkdtemp, so no arm can ever read the other's report.
# =====================================================================================================

def _report(d, *, exclude=("callgraph",), suffix=".json", startswith=None):
    if not os.path.isdir(d):
        return None
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(suffix):
            continue
        if any(x in f for x in exclude):
            continue
        if startswith and not f.startswith(startswith):
            continue
        out.append(os.path.join(d, f))
    return out[0] if out else None


def _leaf(path, seps):
    try:
        return gd.leaf_set(path, seps)
    except Exception:
        return None


def _dep_stats(path):
    """(entries, effectful entries) read from the RAW report, not from a leaf-keyed map. The leaf-keyed
    map collapses every cell's `W.run` into one key `run`, which made this instrument read `1/1` where
    the dep report actually carried 8 witnesses -- an instrument that quietly under-counts is worse than
    none, because its output is plausible (standing bar 7e)."""
    try:
        d = json.load(open(path))
    except Exception:
        return (0, 0)
    fns = d["functions"] if isinstance(d, dict) else d
    return (len(fns), sum(1 for e in fns if set(e.get("inferred", [])) - {UNKNOWN}))


def run_rust(root):
    binp = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
    if not os.path.exists(binp):
        b = gd.run(["cargo", "build", "-q", "--manifest-path", os.path.join(gd.CANDOR, "Cargo.toml"), "-p", "candor-scan"])
        if b.returncode != 0 or not os.path.exists(binp):
            return None, None, None, f"no candor-scan at {binp}"
    single = os.path.join(root, "single")
    gd.run([binp, "."], cwd=single)
    sp = _report(os.path.join(single, ".candor"), suffix=".scan.json")
    dep = os.path.join(root, "split", "deplib")
    gd.run([binp, "."], cwd=dep)
    dp = _report(os.path.join(dep, ".candor"), suffix=".scan.json")
    if not dp:
        return None, None, None, "rust dep scan produced no report"
    app = os.path.join(root, "split", "app")
    env = dict(os.environ, CANDOR_DEPS=dp)
    gd.run([binp, "."], cwd=app, env=env)
    cp_ = _report(os.path.join(app, ".candor"), suffix=".scan.json")
    if not sp or not cp_:
        return None, None, None, "rust scan produced no report"
    return _leaf(sp, ("::",)), _leaf(cp_, ("::",)), _dep_stats(dp), None


def run_java(root):
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None
    if not jar or not os.path.exists(jar):
        return None, None, None, "no candor-java jar"
    if not shutil.which("javac"):
        return None, None, None, "no javac on PATH"
    allcls = os.path.join(root, "classes")
    os.makedirs(allcls, exist_ok=True)
    c = gd.run(["javac", "-nowarn", "-d", allcls,
                os.path.join(root, "src", "dep", "Dep.java"), os.path.join(root, "src", "app", "App.java")])
    if c.returncode != 0:
        return None, None, None, f"javac failed: {c.stderr.decode()[:400]}"
    # arm S: BOTH packages in one scanned tree. arm C: the SAME class files, partitioned.
    depd, appd = os.path.join(root, "jdep"), os.path.join(root, "japp")
    os.makedirs(depd, exist_ok=True)
    os.makedirs(appd, exist_ok=True)
    shutil.copytree(os.path.join(allcls, "dep"), os.path.join(depd, "dep"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(allcls, "app"), os.path.join(appd, "app"), dirs_exist_ok=True)
    sj, dj, aj = (os.path.join(root, x) for x in ("single.json", "dep.json", "app.json"))
    gd.run(["java", "-jar", jar, allcls, "--json", sj])
    gd.run(["java", "-jar", jar, depd, "--json", dj])
    gd.run(["java", "-jar", jar, appd, "--json", aj], env=dict(os.environ, CANDOR_DEPS=dj))
    if not all(os.path.exists(p) for p in (sj, dj, aj)):
        return None, None, None, "candor-java produced no report"
    return _leaf(sj, (".",)), _leaf(aj, (".",)), _dep_stats(dj), None


def run_ts(root):
    ts_dir = gd.CANDOR_TS
    if not shutil.which("node") or not os.path.exists(os.path.join(ts_dir, "scan.mjs")):
        return None, None, None, "no node / scan.mjs"
    if not os.path.isdir(os.path.join(ts_dir, "node_modules")):
        gd.run(["npm", "install", "--no-fund", "--no-audit"], cwd=ts_dir)
    single = os.path.join(root, "single")
    gd.run(["node", "scan.mjs", single], cwd=ts_dir)
    dep = os.path.join(root, "split", "deplib")
    gd.run(["node", "scan.mjs", dep], cwd=ts_dir)
    dp = os.path.join(dep, ".candor", "report.json")
    if not os.path.exists(dp):
        return None, None, None, "ts dep scan produced no report"
    app = os.path.join(root, "split", "app")
    gd.run(["node", "scan.mjs", app], cwd=ts_dir, env=dict(os.environ, CANDOR_DEPS=dp))
    sp, cp_ = os.path.join(single, ".candor", "report.json"), os.path.join(app, ".candor", "report.json")
    if not os.path.exists(sp) or not os.path.exists(cp_):
        return None, None, None, "ts scan produced no report"
    return _leaf(sp, (".",)), _leaf(cp_, (".",)), _dep_stats(dp), None


def run_swift(root):
    if not shutil.which("swift") or not os.path.exists(os.path.join(gd.CANDOR_SWIFT, "Package.swift")):
        return None, None, None, "no swift toolchain"
    binp = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(binp):
        b = gd.run(["swift", "build"], cwd=gd.CANDOR_SWIFT)
        if b.returncode != 0 or not os.path.exists(binp):
            return None, None, None, "swift build failed"
    single = os.path.join(root, "single")
    gd.run([binp, "."], cwd=single)
    sp = _report(os.path.join(single, ".candor"), exclude=("callgraph", "hierarchy"), suffix=".Swift.json")
    dep = os.path.join(root, "split", "deplib")
    gd.run([binp, "."], cwd=dep)
    dp = _report(os.path.join(dep, ".candor"), exclude=("callgraph", "hierarchy"), suffix=".Swift.json")
    if not dp:
        return None, None, None, "swift dep scan produced no report"
    app = os.path.join(root, "split", "app")
    gd.run([binp, "."], cwd=app, env=dict(os.environ, CANDOR_DEPS=dp))
    cp_ = _report(os.path.join(app, ".candor"), exclude=("callgraph", "hierarchy"), suffix=".Swift.json")
    if not sp or not cp_:
        return None, None, None, "swift scan produced no report"
    return _leaf(sp, (".",)), _leaf(cp_, (".",)), _dep_stats(dp), None


ENGINES = [("rust", write_rust, run_rust), ("java", write_java, run_java),
           ("ts", write_ts, run_ts), ("swift", write_swift, run_swift)]


# =====================================================================================================
# THE PROPERTY. Read the asymmetry note at the top of the file before touching this function.
# =====================================================================================================
# verdicts, in severity order:
CARDINAL = "CARDINAL"      # an effect the single-tree arm had is gone chained, with NO disclosure at all
ABSENT = "ABSENT"          # the fn itself vanished chained -- a <0.21> purity claim over a fn with effects
SWAPPED = "SWAPPED"        # an effect was replaced by a DIFFERENT effect: a loss and a fabrication at once
HEDGE = "HEDGE"            # an effect became `Unknown`: a DISCLOSED precision loss (PART 21's ruling)
EXTRA_EFF = "EXTRA_EFF"    # the chained arm has an effect the single-tree arm did not (chained fabrication)
EXTRA_DISC = "EXTRA_DISC"  # the chained arm carries extra `Unknown` on top of the same effects -- allowed
OK = "OK"
VACUOUS = "VACUOUS"        # the single-tree arm demands nothing: it reports the entry pure or absent
REVERSE = "REVERSE"        # ... and yet the CHAINED arm found an effect: the single-tree arm is the weaker
                           # one. Not a split-invariance failure (the property is directional) but the
                           # only channel in which a SINGLE-TREE miss shows up here, so it is named.

FAILING = (CARDINAL, ABSENT, SWAPPED)


def judge(single, chained):
    """single/chained are frozensets, or None when the fn is ABSENT from that arm's report.
    ABSENT is NOT the same as pure for the chained arm (it is still a purity claim) but IS the same as
    pure for the single-tree arm (nothing to demand)."""
    s = frozenset() if single is None else single
    if not s:
        return REVERSE if (chained and (chained - {UNKNOWN})) else VACUOUS
    if chained is None:
        return ABSENT
    real_s, real_c = s - {UNKNOWN}, chained - {UNKNOWN}
    lost = real_s - real_c
    if lost:
        if not chained:
            return CARDINAL
        if UNKNOWN in chained and not (real_c - real_s):
            return HEDGE
        if real_c - real_s:
            return SWAPPED
        return CARDINAL          # kept SOME effects, dropped others, disclosed nothing
    if real_c - real_s:
        return EXTRA_EFF
    if UNKNOWN in chained and UNKNOWN not in s:
        return EXTRA_DISC
    return OK


def main():
    args = sys.argv[1:]
    keep = "--keep" in args
    strict_hedge = "--strict-hedge" in args
    only = None
    for a in args:
        if a.startswith("--only"):
            v = a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]
            only = set(v.split(","))
    if only:
        # A misspelled --only must be a USAGE error, never a silently-empty run: an empty run hits the
        # vacuity floor and reports "every single-tree arm read pure", which is a true statement about
        # zero cells and a completely misleading one about the engines.
        unknown = sorted(only - {sp["id"] for sp in SPLITS})
        if unknown:
            print(f"usage error: --only names no such split shape: {', '.join(unknown)}\n"
                  f"  available: {', '.join(sp['id'] for sp in SPLITS)}\n"
                  f"  (`direct` exists in gen_differential.py but has no dep half, so it is not split here)")
            sys.exit(2)
    cells = build_cells(only)
    by_split = {}
    for c in cells:
        by_split.setdefault(c["split"], []).append(c)

    print("=" * 108)
    print("P1 — SPLIT-INVARIANCE  (each engine vs ITSELF: one tree  ==  split + chained, modulo disclosure)")
    print(f"  effects : {', '.join(e['effect'] for e in gd.EFFECTS)}")
    print(f"  splits  : {', '.join(sorted(by_split))}")
    print(f"  cells   : {len(cells)}   ({len(by_split)} split shapes x {len(gd.EFFECTS)} effects), "
          f"each scanned TWICE per engine")
    print(f"  not rendered (no dep half -- the sink is inline in the entry): "
          f"{', '.join(UNSPLITTABLE)} x {len(gd.EFFECTS)} effects = {len(UNSPLITTABLE) * len(gd.EFFECTS)} cells")
    print("=" * 108)

    ws = tempfile.mkdtemp(prefix="candor-p1split-")
    # engine -> cell name -> (verdict, single, chained)
    results, skipped, broken, depinfo = {}, {}, {}, {}
    for eng, writer, runner in ENGINES:
        per_cell, err = {}, None
        for sid, cs in sorted(by_split.items()):
            root = os.path.join(ws, eng, sid)
            os.makedirs(root, exist_ok=True)
            writer(root, cs)
            s_map, c_map, d_map, e = runner(root)   # d_map is (entries, effectful) from the dep report
            if e:
                err = f"{sid}: {e}"
                break
            depinfo.setdefault(eng, {})[sid] = d_map
            for c in cs:
                per_cell[c["name"]] = (judge(s_map.get(c["name"]), c_map.get(c["name"])),
                                       s_map.get(c["name"]), c_map.get(c["name"]))
        if err:
            # "present but broken FAILS, genuinely absent SKIPS" -- the TS_PRESENT discipline from run.sh.
            absent = any(k in err for k in ("no candor-scan", "no candor-java jar", "no javac",
                                            "no node / scan.mjs", "no swift toolchain"))
            (skipped if absent else broken)[eng] = err
            print(f"  {eng:6s} {'SKIPPED' if absent else 'FAILED '} -- {err}")
        else:
            results[eng] = per_cell
            print(f"  {eng:6s} ok -- {len(per_cell)} cells, both arms")

    available = [e for e, _, _ in ENGINES if e in results]

    # ---- the matrix ----
    print("\nMATRIX  (cell x engine; S=single-tree arm, C=chained arm; verdict letter)")
    legend = ("  .=OK  v=VACUOUS(single-tree demands nothing)  r=REVERSE(only the CHAINED arm found it)  "
              "h=HEDGE(effect -> Unknown, disclosed)  +=EXTRA_DISC  f=EXTRA_EFF\n"
              "  X=CARDINAL(effect gone, nothing disclosed)  A=ABSENT(fn vanished)  S=SWAPPED(effect -> other effect)")
    print(legend)
    letter = {OK: ".", VACUOUS: "v", REVERSE: "r", HEDGE: "h", EXTRA_DISC: "+", EXTRA_EFF: "f",
              CARDINAL: "X", ABSENT: "A", SWAPPED: "S"}
    head = f"{'cell':30s} " + " ".join(f"{e:6s}" for e in available)
    print(head)
    print("-" * len(head))
    for c in cells:
        row = f"{c['name']:30s} "
        for e in available:
            v = results[e].get(c["name"], (VACUOUS, None, None))[0]
            row += f"{letter[v]:6s} "
        print(row)
    print("-" * len(head))

    # ---- counts (standing bar item 8: a generator whose cases are mostly vacuous measures nothing) ----
    print("\nCOUNTS per engine")
    print(f"  {'engine':8s} {'cells':>6s} {'live':>6s} {'vacuous':>8s} {'rev':>4s} {'ok':>5s} {'hedge':>6s} "
          f"{'xdisc':>6s} {'xeff':>5s} {'CARD':>5s} {'ABS':>5s} {'SWAP':>5s}")
    rc = 0
    for e in available:
        tally = {}
        for c in cells:
            v = results[e].get(c["name"], (VACUOUS, None, None))[0]
            tally[v] = tally.get(v, 0) + 1
        live = len(cells) - tally.get(VACUOUS, 0) - tally.get(REVERSE, 0)
        print(f"  {e:8s} {len(cells):6d} {live:6d} {tally.get(VACUOUS,0):8d} {tally.get(REVERSE,0):4d} "
              f"{tally.get(OK,0):5d} "
              f"{tally.get(HEDGE,0):6d} {tally.get(EXTRA_DISC,0):6d} {tally.get(EXTRA_EFF,0):5d} "
              f"{tally.get(CARDINAL,0):5d} {tally.get(ABSENT,0):5d} {tally.get(SWAPPED,0):5d}")
        # VACUITY FLOOR. A run in which the single-tree arm never attributes an effect is not a passing
        # run, it is a run that tested nothing -- and it looks exactly like a passing one.
        if live == 0:
            why = ("no cells were generated at all" if not cells else
                   "every single-tree arm read the entry pure, so nothing was demanded of the chained arm")
            print(f"  FAIL (vacuity floor): engine '{e}' produced ZERO live cells -- {why}.")
            rc = 2
        # ⟨0.24⟩ PER-SHAPE FLOOR. The total-only floor above trips at `live == 0` ACROSS ALL SPLITS, so a
        # review neutered ONE split shape's sink in all four languages -- 8 cells per engine going dead --
        # and the run stayed green, because the other shapes carried the total. In a full 10-shape run up to
        # NINE could rot to vacuous with exit 0. The per-shape `live` counts were already PRINTED below and
        # never ASSERTED, which is the recurring defect in this suite: the number a reader needs is on the
        # screen and nothing fails when it goes wrong.
        by_split = {}
        for c in cells:
            v = results[e].get(c["name"], (VACUOUS, None, None))[0]
            t = by_split.setdefault(c["split"], [0, 0])
            t[0] += 1
            if v not in (VACUOUS, REVERSE):
                t[1] += 1
        dead = sorted(sp for sp, (tot, lv) in by_split.items() if tot and lv == 0)
        dead = [d for d in dead if d not in KNOWN_VACUOUS.get(e, set())]
        if dead:
            print(f"  FAIL (per-shape vacuity floor): engine '{e}' has split shape(s) with cells but ZERO "
                  f"live: {', '.join(dead)}. A shape that stopped triggering tests nothing, and the total "
                  f"floor cannot see it while other shapes carry the count.")
            rc = 2

    print("\nDEP-HALF COVERAGE  (does the dependency's OWN report carry the witness? a dep report with no "
          "effects\n  means the loss is on the PRODUCER side, not at the join)")
    for e in available:
        rows = ", ".join(f"{s}:{eff}/{tot}" for s, (tot, eff) in sorted(depinfo.get(e, {}).items()))
        print(f"  {e:8s} {rows}")

    # ---- findings ----
    def dump(kind, header, cells_of):
        if not cells_of:
            return
        print(f"\n{len(cells_of)} {header}")
        for e, c, s, ch in cells_of:
            fs = ",".join(sorted(s)) if s else "(pure)"
            fc = "(ABSENT)" if ch is None else (",".join(sorted(ch)) or "(pure)")
            print(f"  {e:6s} {c['name']:30s} [{c['split']}/{c['effect']}]  single={fs}  chained={fc}")

    buckets = {k: [] for k in (CARDINAL, ABSENT, SWAPPED, HEDGE, EXTRA_EFF, EXTRA_DISC, REVERSE)}
    for e in available:
        for c in cells:
            v, s, ch = results[e].get(c["name"], (VACUOUS, None, None))
            if v in buckets:
                buckets[v].append((e, c, s, ch))

    dump(CARDINAL, "CARDINAL LOSS — an effect the engine's OWN single-tree arm found is gone across the "
                   "split, with no disclosure:", buckets[CARDINAL])
    dump(ABSENT, "ABSENT — a function present single-tree vanished from the chained report (a <0.21> "
                 "purity claim):", buckets[ABSENT])
    dump(SWAPPED, "SWAPPED — an effect was replaced by a DIFFERENT effect across the split:", buckets[SWAPPED])
    dump(HEDGE, "HEDGE — effect -> Unknown across the split: a DISCLOSED precision loss (allowed by "
                "PART 21's ruling; counted, not failed unless --strict-hedge):", buckets[HEDGE])
    dump(EXTRA_EFF, "EXTRA EFFECT — the chained arm has an effect the single-tree arm did not (a chained "
                    "fabrication; named, not failed — the cardinal sin is the other direction):",
         buckets[EXTRA_EFF])

    dump(REVERSE, "REVERSE — the single-tree arm read the entry PURE while the CHAINED arm found the "
                  "effect: a SINGLE-TREE miss, out of this property's scope but worth naming:", buckets[REVERSE])

    # ---- the RATCHET.
    #
    # Without a baseline this property fails on current HEAD, because it found live defects the first time
    # it ran. Two bad options and one good one: never wire it in (then it protects nothing), or wire it in
    # red (then the whole suite's signal is gone and everyone learns to ignore it). The third is a RATCHET,
    # the pattern candor-java already uses for `deny E Unknown` on legacy code.
    #
    # The baseline records DEFECTS, not expected answers. Nothing in it tells the property what an engine
    # SHOULD say — the engine's own single-tree arm is still the only oracle. All it says is "this
    # (engine, split) pair is known-broken and someone wrote down why", so the run stays green while the
    # debt stays visible and countable.
    #
    # It ratchets BOTH ways, which is the part that stops it rotting into a permanent excuse:
    #   * a failing cell OUTSIDE the baseline fails the run  -- new debt is caught;
    #   * a baselined pair with NO failing cells ALSO fails  -- fixed debt must be removed from the file,
    #     so the baseline can never quietly outlive the defect and start masking its return.
    # Granularity is (engine, split), not (engine, cell): the defect is a property of the SHAPE, and all
    # eight effects of a shape fail or pass together. A per-cell file would be 32 lines saying one thing.
    baseline_path = None
    for a in args:
        if a.startswith("--baseline"):
            baseline_path = a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]
    waived = set()
    if baseline_path:
        try:
            with open(baseline_path) as f:
                bl = json.load(f)
        except Exception as ex:
            print(f"\nFAIL: --baseline {baseline_path} is unreadable ({ex}). A baseline that cannot be "
                  f"read must not read as 'nothing is waived'.")
            rc = 2
            bl = {"known": []}
        known = {(k["engine"], k["split"]): k.get("why", "") for k in bl.get("known", [])}
        failing_pairs = {(e, c["split"]) for k in FAILING for e, c, _, _ in buckets[k]}
        print(f"\nRATCHET  (baseline: {baseline_path})")
        for (eng, sid), why in sorted(known.items()):
            if eng not in available:
                print(f"  {eng:6s} {sid:22s} -- engine not available this run, waiver not checked")
                continue
            if (eng, sid) in failing_pairs:
                n = sum(1 for k in FAILING for e, c, _, _ in buckets[k] if e == eng and c["split"] == sid)
                print(f"  {eng:6s} {sid:22s} WAIVED  {n} cell(s) -- {why}")
                waived.add((eng, sid))
            else:
                print(f"  {eng:6s} {sid:22s} FAIL (STALE WAIVER): this pair is baselined as known-broken "
                      f"but every cell now passes. Delete the entry -- a waiver that outlives its defect "
                      f"masks the defect's return.")
                rc = 2
        unwaived = sorted(failing_pairs - waived)
        if unwaived:
            print("  NEW DEBT (not in the baseline): " + ", ".join(f"{e}/{s}" for e, s in unwaived))

    n_fail = sum(1 for k in FAILING for e, c, _, _ in buckets[k] if (e, c["split"]) not in waived)
    if n_fail:
        rc = rc or 1
    if strict_hedge and buckets[HEDGE]:
        print("\n[--strict-hedge] failing on the HEDGE band as well.")
        rc = rc or 1

    if broken:
        for e, why in broken.items():
            print(f"\nFAIL: engine '{e}' present but broken -- {why}")
        rc = 2
    if os.environ.get("CONFORMANCE_REQUIRE_ALL") and skipped:
        for e, why in skipped.items():
            print(f"FAIL (strict): engine '{e}' REQUIRED but absent -- {why}")
        rc = 2

    print()
    if rc == 0:
        # Say what was WAIVED in the same breath as the OK. "every live cell" while 32 of them are
        # baselined would be a false all-clear in the summary of a suite whose subject is false all-clears.
        n_waived = sum(1 for k in FAILING for e, c, _, _ in buckets[k] if (e, c["split"]) in waived)
        tail = (f", EXCEPT {n_waived} cell(s) waived by the ratchet in "
                f"{', '.join(f'{e}/{s}' for e, s in sorted(waived))}") if waived else ""
        print(f"P1 SPLIT-INVARIANCE: OK — {len(available)} engine(s) ({', '.join(available)}) each agree "
              f"with THEMSELVES across the split on every live cell{tail}.")
    else:
        print("P1 SPLIT-INVARIANCE: FAILED — see the findings above.")

    if keep:
        print(f"\n[--keep] generated workspace retained at: {ws}")
    else:
        shutil.rmtree(ws, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
