#!/usr/bin/env python3
"""
PART 92 — THE CHAINED-DISPATCH UNION differential (FOUR-WAY, SPEC §4 ⟨0.39⟩).

THE DEFECT IS A TOGGLE, AND IT RUNS THE WRONG WAY.

  a library whose public abstraction has ZERO local implementors  -> a chained consumer gets a
                                                                     disclosed `Unknown`   (correct)
  add ONE PURE implementor to that same library                   -> the consumer is SILENTLY
                                                                     CERTIFIED PURE       (the sin)

So **adding a pure implementation to a library REMOVES a disclosure from every consumer of it.** That is
the ⟨0.21⟩ cardinal sin reached by a route no single scan can see: nothing is wrong with either package
on its own, and the loss only exists in the join.

  SOUNDNESS R475 (rust + java, identical, 2026-09-17)  LIVE ON REAL CODE. `ratatui-core`'s
      `Terminal::size` dispatches `Backend::size` over its sole local implementor `TestBackend` (pure);
      `ratatui-crossterm`'s `CrosstermBackend::size` performs `Ipc`. An application chained onto BOTH
      reports that function ABSENT, and `deny Ipc` and `pure` over it BOTH exit 0.

WHY THE FIXTURE MUST BE THREE PACKAGES — AND, FOR ONE ARM, FOUR. The effectful implementor lives in a
THIRD package — neither the dispatching dependency nor the consumer. No two-package arm can express the
finding, and §4 ⟨0.39⟩ says so in the clause itself: *"no two of them are separable — the effectful implementor in the measured case
lives in a THIRD package"*. `split_arms.py` was built for P1's two-package split; the `Scanner` layer it
now carries is the extension that made an N-package chain expressible without a second copy of the
engine plumbing (R288: fifteen copies of one instrument have no owner).

WHAT MAKES THE CROSS SOUND — stated because the coordinator got exactly this wrong on the day R475 was
filed, reporting a cross-engine contrast that was FIXTURE-INDUCED because the two arms differed in their
inputs rather than their engines.

  **The consumer's function under test is the SAME SOURCE TEXT in c1, c2, c3 and c5.** Byte-identical,
  asserted by the generator itself (`_assert_identical_consumers`), not by care. Between c2 and c3 the
  ONLY thing that differs in the entire experiment is the implementor set inside the dependency; between
  c3 and c1 the only thing that differs is the EXISTENCE of a third package and its report on
  CANDOR_DEPS. Nothing about the consumer moves, so nothing about the consumer can explain the answer
  moving.

THE CONTROL ARMS ARE NOT OPTIONAL. Widening a union is exactly where this family has repeatedly turned a
silence into a fabrication, and the ⟨0.39⟩ cost model is explicit that nothing may move from disclosed
to silent and no implementation may start hedging:

  c2_zero_impl  the zero-implementor case MUST REMAIN a disclosed `Unknown`. If a fix reddens this arm's
                sibling and greys this one, it has traded one silence for another — and this arm is also
                the left-hand side of the toggle, so a fix that quietly loses it has deleted the very
                contrast the part exists to pin.
  c3_pure_only  a consumer over a library whose only implementor ANYWHERE is pure is LEGITIMATELY pure
                and MUST STAY pure. This is the fabrication guard: an engine that unions indiscriminately
                — charging every consumer of a dispatching library for effects nobody implements —
                reddens here and nowhere else.
  c4_sealed     a sealed/private abstraction whose implementors are all local and visible keeps an EXACT
                union and gains NO hedge. §4 is explicit that this case stays exact; an engine that
                starts hedging on "this call dispatched" rather than on "an implementor is invisible"
                fails here.
  c6_middle_package  a FOURTH package, and the arm c1 cannot reach: the package that DISPATCHES owns
                neither the abstraction nor any implementor of it. See the note beside `ARMS` for why
                three packages cannot express this and why c6 is not in `CROSS_ARMS`. SOUNDNESS R504.
  c5_unchained  the same fixture as c1 with CANDOR_DEPS UNSET. Not a defect arm — a REFERENCE, and the
                one that makes the clause's central observation concrete: unchained, the consumer says
                `[]` + `invisible: [iface, effimpl]`; chained, it says nothing at all. **Chaining does
                not flip a gate here, it DELETES the disclosure** that ⟨0.30⟩'s non-gating ruling for
                `invisible` depends on being present. A mechanism that makes reports better must not make
                silence cheaper.

WHY THE ASSERTION IS AT THE CONSUMER AND NOT ON `dispatchesOn` / `interfaceUnion`. ⟨0.39⟩ imposes three
obligations and says no two are separable. Only their JOINT effect is observable without naming an
implementation strategy, so the part asserts the joint effect — what the consumer's row says — and PRINTS
the two producer-side legs as diagnostics (measured: `dispatchesOn` absent and `interfaceUnion` null in
all four engines' producer reports today, which is why c1 fails everywhere). Asserting the wire shape
would pin an engine to one route to the property; asserting the consumer's row pins the property.

EVERY FIXTURE COMPILES, AND THAT IS ENFORCED RATHER THAN CLAIMED. A control that asserts an ABSENCE over
a program that cannot be built is not weak evidence, it is NO evidence — absence is also what a broken
engine produces. `cargo build` / `javac` / `tsc --noEmit` / `swift build` run over every rendered arm,
and a build failure FAILS the part. Set CANDOR_PART92_NOBUILD=1 only to iterate; the run says loudly
when the proof was skipped.

THE XFAIL TABLE. `c1_foreign_effectful` fails on ALL FOUR engines today — measured against the released
artifacts, spec 0.38 (candor-scan 0.38.4, candor-java 0.38.3, candor-ts 0.38.3, candor-swift 0.38.3).
Every one is declared as an `(arm, engine)` expectation rather than hidden, and **A PASSING XFAIL IS A
FAILURE HERE**: the moment an engine ports ⟨0.39⟩ this part goes red and that engine retires its own
line, in the same commit as the fix. That mechanism is what made PART 91 catch R477 on its first
execution; it is the only thing in the suite that notices an expectation which has quietly become true.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402  -- import-safe: work is behind a __main__ guard
import split_arms as sa            # noqa: E402

SPEC_CLAUSES = [
    ("§4 ⟨0.39⟩", "A CHAINED CONSUMER'S INHERITED SIGNATURE MUST CARRY THE EFFECTS OF EVERY IMPLEMENTOR "
                  "VISIBLE TO THE CONSUMER — its own and any chained report's — so supplying an "
                  "effectful implementor to a dependency is never silent."),
    ("§4 ⟨0.39⟩", "adding a pure implementation to a library REMOVES a disclosure from every consumer "
                  "of it"),
    ("§4 ⟨0.39⟩", "The consumer's join MUST union, per key, its own visible implementors with every "
                  "chained entry carrying that key."),
    ("§4 bounded-CHA", "a local abstraction with no visible implementor, too many, or an ambiguous name "
                       "is disclosed indeterminacy, never silent purity"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART92_NOBUILD")

# =====================================================================================================
# THE ARMS.
#
#   iface     which variant of the dispatching dependency: "impl" (one PURE local implementor),
#             "zero" (none at all), "sealed" (a private abstraction with one local EFFECTFUL impl)
#   third     is the third package (a FOREIGN implementor, effectful) rendered and chained?
#   chained   is CANDOR_DEPS set at all? (c5 is the unchained reference)
#   entry     which consumer function the row is read from
#   want      the assertion, per disclosure channel:
#               has       effects that MUST appear in `inferred`
#               hasnt     effects that MUST NOT
#               unknown   True/False = the `Unknown` marker must/must not be present (None = unasserted)
#               invisible True/False = the kappa ledger must/must not be non-empty
#
# `has`/`hasnt` rather than an exact set on the defect arm ON PURPOSE: the soundness claim is that the
# effect REACHES the consumer, and an engine that also hedges while carrying it has not violated ⟨0.39⟩.
# The exactness demand belongs on c4, where the clause really does say the union stays exact.
# =====================================================================================================
EFFECT = "Net"
ARMS = [
    dict(id="c1_foreign_effectful", iface="impl", third=True, chained=True, entry="dispatch",
         want=dict(has={EFFECT}),
         why="DEFECT: a FOREIGN effectful implementor in a third package must reach the consumer"),
    dict(id="c2_zero_impl", iface="zero", third=False, chained=True, entry="dispatch",
         want=dict(hasnt={EFFECT}, unknown=True),
         why="CONTROL: zero implementors anywhere MUST stay a disclosed Unknown (the toggle's left side)"),
    dict(id="c3_pure_only", iface="impl", third=False, chained=True, entry="dispatch",
         want=dict(hasnt={EFFECT}, unknown=False, invisible=False),
         why="CONTROL: only-pure-implementor-anywhere is LEGITIMATELY pure — the fabrication guard"),
    dict(id="c4_sealed", iface="sealed", third=False, chained=True, entry="sealed",
         want=dict(has={EFFECT}, unknown=False, invisible=False),
         why="CONTROL: a sealed abstraction's union stays EXACT — the real effect, and no new hedge"),
    dict(id="c5_unchained", iface="impl", third=True, chained=False, entry="dispatch",
         want=dict(hasnt={EFFECT}, unknown=False, invisible=True),
         why="REFERENCE: unchained, the same consumer discloses via `invisible` — chaining DELETES it"),
    dict(id="c6_middle_package", iface="impl", third=True, chained=True, entry="dispatch", middle=True,
         want=dict(has={EFFECT}),
         why="DEFECT: the DISPATCHER owns nothing — a MIDDLE package must name its dependency's member"),
]

# THE FOURTH PACKAGE, and why three cannot express what it does (SOUNDNESS R504).
#
# In c1–c5 the package that DISPATCHES is also the package that OWNS the abstraction, so an engine that
# scopes obligation 1 to abstractions it DECLARES answers correctly and the hole never opens. `middle`
# owns neither the trait nor any implementor of it: it depends on `iface` and dispatches over `iface`'s
# abstraction, which is the ordinary shape of a library layered on another library. If it names nothing,
# the consumer never learns the member to union on and the chain breaks ONE HOP SHORT — the app's row is
# ABSENT, which under ⟨0.21⟩ is a positive claim of purity.
#
# Found by candor-java's port reading candor-rust's source (`dispatch_sites` recorded local-trait dispatch
# only), measured silent on a four-package chain, and closed in java first — which is why this arm's XFAIL
# table is NOT uniform and why the `(arm, engine)` keying is load-bearing rather than defensive.
#
# c6 IS DELIBERATELY NOT IN `CROSS_ARMS`. Its consumer calls `middle` where c1's calls `iface`, so its
# source text CANNOT be byte-identical to the others' — the dispatcher has to live somewhere. The cross it
# supports is a different one, stated so it is not mistaken for the c1/c2/c3/c5 cross: c6 differs from c1
# in exactly ONE structural fact, which package holds the dispatching function. Every other input — the
# abstraction, its pure local implementor, the foreign effectful implementor, the chained report set — is
# rendered from the same sources. So an engine that passes c1 and fails c6 has told you precisely that its
# obligation-1 pass is scoped to abstractions it owns.

# An expectation keyed by (arm, engine) — NEVER by arm alone. Today it happens to be uniform, and it will
# not stay uniform: the moment one engine ports ⟨0.39⟩ its line comes out and the others' stay, which is
# precisely the state an arm-keyed table cannot represent. A PASSING xfail is a FAILURE (see main()).
XFAIL = {
    # RETIRED 2026-09-17, candor-rust `df4cf3f` — the FIRST engine to port ⟨0.39⟩, which is what this
    # table was built to notice. rust's three legs are live: the producer emits `dispatchesOn` on a row
    # that is otherwise PURE, a crate implementing a FOREIGN abstraction publishes its `interfaceUnion`
    # entry keyed under the OWNING crate, and the consumer unions per key. The other three engines' lines
    # stay exactly as they were — an arm-keyed table could not have expressed this state, which is the
    # reason this one is keyed by (arm, engine).
    #
    # RETIRED 2026-09-18, candor-java — the SECOND engine, and the family's reference one, so this port is
    # the shape ts and swift copy. Its legs are the same three and its arithmetic is simpler: a JVM entry
    # hash is already fully qualified in the owning package's namespace, so obligation 2's key needs no
    # prefixing rule at all (`iface/backend/Backend.size()I`) and the consumer resolves `dispatchesOn`
    # through the ordinary `crossDeps` index. Un-gating ⟨0.23⟩ was part of the port here too: this engine's
    # union entries rode behind CANDOR_WORKSPACE_CHAIN, and that gate is why the toggle survived default
    # scans. swift's and ts's lines are untouched.
    ("c1_foreign_effectful", "ts"):    "R475 class — candor-ts 0.38.3: consumer ABSENT, same shape",
    ("c1_foreign_effectful", "swift"): "R475 class — candor-swift 0.38.3: consumer ABSENT, same shape",
    # c6 — THE MIDDLE PACKAGE (SOUNDNESS R504). java PASSES this arm: its port closed the hole in the same
    # commit that opened it, on the same four-package chain, keyed on INVOKEINTERFACE with a non-κ owner.
    # The other three lines are here for three different reasons, and the difference is the point of an
    # (arm, engine) table: ts and swift have not ported ⟨0.39⟩ at all, so c6 fails for the same reason c1
    # does; rust HAS ported it and still fails c6 alone, because its obligation-1 pass was scoped to
    # abstractions the producer DECLARES. A passing xfail is a FAILURE here — when rust closes it, this
    # line comes out in the same commit as the fix.
    ("c6_middle_package", "ts"):    "R475 class — candor-ts 0.38.3: ⟨0.39⟩ not ported; consumer ABSENT",
    ("c6_middle_package", "swift"): "R475 class — candor-swift 0.38.3: ⟨0.39⟩ not ported; consumer ABSENT",
}

# The consumer's dispatching function, per engine. rust keeps its own casing convention; the assertion is
# on the LEAF name after `leaf_info` strips module separators.
ENTRY = {
    "rust":  dict(dispatch="app_size", sealed="app_sealed"),
    "java":  dict(dispatch="appSize", sealed="appSealed"),
    "ts":    dict(dispatch="appSize", sealed="appSealed"),
    "swift": dict(dispatch="appSize", sealed="appSealed"),
}

# =====================================================================================================
# THE FIXTURE, four ways. Three packages:
#
#   iface     `trait/interface/protocol Backend { size() }` + `termSize(b)` which DISPATCHES over it.
#             variant "impl"   also declares ONE PURE implementor (ratatui-core's `TestBackend`)
#             variant "zero"   declares none
#             variant "sealed" a PRIVATE abstraction, one local EFFECTFUL implementor, dispatched from a
#                              public entry point — the exactness control, a different program on purpose
#   effimpl   implements iface's FOREIGN abstraction, effectfully (ratatui-crossterm's CrosstermBackend)
#   app       `appSize(b) { return iface.termSize(b) }` — the function under test, IDENTICAL in every arm
#             that uses it; `appRun()` supplies the foreign implementor, which is what makes the union
#             legitimate rather than a minted edge (⟨0.39⟩ REFUSES an escaping-value rule)
# =====================================================================================================
SINK = {  # one `Net` sink per language, the same vocabulary gen_differential.EFFECTS uses
    "rust":  'let _ = std::net::TcpStream::connect("h:1");',
    "java":  'try { new java.net.Socket("h", 1); } catch (Exception e) {}',
    "ts":    'try { netm.connect(1, "h") } catch {}',
    "swift": '_ = URLSession.shared.dataTask(with: URL(string: "http://h")!)',
}

RUST_IFACE = {
    "impl": ('pub trait Backend { fn size(&self) -> usize; }\n'
             'pub struct TestBackend;\n'
             'impl Backend for TestBackend { fn size(&self) -> usize { 7 } }\n'
             'pub fn term_size(b: &dyn Backend) -> usize { b.size() }\n'),
    "zero": ('pub trait Backend { fn size(&self) -> usize; }\n'
             'pub fn term_size(b: &dyn Backend) -> usize { b.size() }\n'),
    "sealed": ('trait Sealed { fn go(&self) -> usize; }\n'
               'struct LocalImpl;\n'
               'impl Sealed for LocalImpl { fn go(&self) -> usize { %s 0 } }\n'
               'pub fn sealed_dispatch() -> usize { let s: &dyn Sealed = &LocalImpl; s.go() }\n' % SINK["rust"]),
}
RUST_APP = {
    "dispatch": 'pub fn app_size(b: &dyn iface::Backend) -> usize { iface::term_size(b) }\n',
    "third":    'pub fn app_run() -> usize { app_size(&effimpl::Crossterm) }\n',
    "sealed":   'pub fn app_sealed() -> usize { iface::sealed_dispatch() }\n',
    # c6 — the ONLY line that differs from `dispatch`: the dispatching callee lives one package over.
    "middle":   'pub fn app_size(b: &dyn iface::Backend) -> usize { middle::mid_size(b) }\n',
}
# THE MIDDLE PACKAGE, four ways. It depends on `iface` and dispatches over `iface`'s abstraction; it
# declares no abstraction and implements none.
RUST_MIDDLE = 'pub fn mid_size(b: &dyn iface::Backend) -> usize { b.size() }\n'

JAVA_IFACE = {
    "impl": {
        "Backend.java": 'package iface; public interface Backend { int size(); }\n',
        "TestBackend.java": 'package iface; public class TestBackend implements Backend { public int size() { return 7; } }\n',
        "Terminal.java": 'package iface; public class Terminal { public static int termSize(Backend b) { return b.size(); } }\n',
    },
    "zero": {
        "Backend.java": 'package iface; public interface Backend { int size(); }\n',
        "Terminal.java": 'package iface; public class Terminal { public static int termSize(Backend b) { return b.size(); } }\n',
    },
    "sealed": {
        "Sealed.java": 'package iface; interface Sealed { int go(); }\n',
        "LocalImpl.java": 'package iface; class LocalImpl implements Sealed { public int go() { %s return 0; } }\n' % SINK["java"],
        "SealedDispatch.java": 'package iface; public class SealedDispatch { public static int sealedDispatch() { Sealed s = new LocalImpl(); return s.go(); } }\n',
    },
}
JAVA_APP = {
    "dispatch": '  public static int appSize(iface.Backend b) { return iface.Terminal.termSize(b); }\n',
    "third":    '  public static int appRun() { return appSize(new effimpl.Crossterm()); }\n',
    "sealed":   '  public static int appSealed() { return iface.SealedDispatch.sealedDispatch(); }\n',
    "middle":   '  public static int appSize(iface.Backend b) { return middle.Mid.midSize(b); }\n',
}
JAVA_MIDDLE = {
    "Mid.java": 'package middle; public class Mid { public static int midSize(iface.Backend b) { return b.size(); } }\n',
}

TS_IFACE = {
    "impl": ('export interface Backend { size(): number }\n'
             'export class TestBackend implements Backend { size(): number { return 7 } }\n'
             'export function termSize(b: Backend): number { return b.size() }\n'),
    "zero": ('export interface Backend { size(): number }\n'
             'export function termSize(b: Backend): number { return b.size() }\n'),
    "sealed": ('import * as netm from "node:net";\n'
               'interface Sealed { go(): number }\n'
               'class LocalImpl implements Sealed { go(): number { %s ; return 0 } }\n'
               'export function sealedDispatch(): number { const s: Sealed = new LocalImpl(); return s.go() }\n'
               % SINK["ts"]),
}
TS_APP = {
    "dispatch": ('import { Backend, termSize } from "iface";\n'
                 'export function appSize(b: Backend): number { return termSize(b) }\n'),
    "third":    ('import { Crossterm } from "effimpl";\n'
                 'export function appRun(): number { return appSize(new Crossterm()) }\n'),
    "sealed":   ('import { sealedDispatch } from "iface";\n'
                 'export function appSealed(): number { return sealedDispatch() }\n'),
    "middle":   ('import { Backend } from "iface";\n'
                 'import { midSize } from "middle";\n'
                 'export function appSize(b: Backend): number { return midSize(b) }\n'),
}
TS_MIDDLE = ('import { Backend } from "iface";\n'
             'export function midSize(b: Backend): number { return b.size() }\n')

SW_IFACE = {
    "impl": ('public protocol Backend { func size() -> Int }\n'
             'public struct TestBackend: Backend { public init() {}; public func size() -> Int { return 7 } }\n'
             'public func termSize(_ b: Backend) -> Int { return b.size() }\n'),
    "zero": ('public protocol Backend { func size() -> Int }\n'
             'public func termSize(_ b: Backend) -> Int { return b.size() }\n'),
    "sealed": ('import Foundation\n'
               'protocol Sealed { func go() -> Int }\n'
               'struct LocalImpl: Sealed { func go() -> Int { %s; return 0 } }\n'
               'public func sealedDispatch() -> Int { let s: Sealed = LocalImpl(); return s.go() }\n'
               % SINK["swift"]),
}
SW_APP = {
    "dispatch": 'import Iface\npublic func appSize(_ b: Backend) -> Int { return termSize(b) }\n',
    "third":    'import EffImpl\npublic func appRun() -> Int { return appSize(Crossterm()) }\n',
    "sealed":   'import Iface\npublic func appSealed() -> Int { return sealedDispatch() }\n',
    "middle":   'import Iface\nimport Middle\npublic func appSize(_ b: Backend) -> Int { return midSize(b) }\n',
}
SW_MIDDLE = ('import Iface\n'
             'public func midSize(_ b: Backend) -> Int { return b.size() }\n')


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def iface_variant(arm):
    """THE FAULT IS AT THE FIXTURE, NOT THE COMPARISON. With CANDOR_PROBE_FAULT set, c2_zero_impl's
    dependency is rendered with the "impl" variant — the one PURE implementor — so the arm that MUST
    remain a disclosed `Unknown` cannot be, and the run MUST go red.

    Chosen over inverting an expected value for the reason probe_check.py records at length: inverting
    proves only that the comparison can subtract, while corrupting the INPUT proves the cell is reading
    the fixture it names — and here it proves specifically that the CHAINED DEPENDENCY's content reached
    the consumer's scan, which is the one thing this part measures that no single-package part does.
    Chosen over swapping two must-fail arms because there are none to swap: c1 is xfailed on every
    engine, so a substitution into c1 would move no verdict (the vacuity recorded for gen_binding_union).
    """
    if FAULT and arm["id"] == "c2_zero_impl":
        return "impl"
    return arm["iface"]


# =====================================================================================================
# RENDERING. One workspace per (engine, arm): ws/<engine>/<arm>/{iface,effimpl,app}. Every arm gets its
# OWN copy of every package, so no arm can read another's `.candor` and no dependency scan can be
# attributed to the wrong arm — the same structural isolation split_arms.py enforces for P1/P2/P3.
# Returns the ordered list of (package_dir, is_dep) for the arm.
# =====================================================================================================
def app_body(arm):
    """Which consumer body this arm's app carries. `middle` is the c6 variant — the SAME function, the
    same signature, one call target over."""
    if arm["entry"] == "sealed":
        return "sealed"
    return "middle" if arm.get("middle") else "dispatch"


def dep_order(root, arm):
    """The dependency package directories, in scan order. `middle` sits between the abstraction's owner
    and its foreign implementor because that is where it sits in the dependency graph."""
    order = [os.path.join(root, "iface")]
    if arm.get("middle"):
        order.append(os.path.join(root, "middle"))
    if arm["third"]:
        order.append(os.path.join(root, "effimpl"))
    return order


def render_rust(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "Cargo.toml"), '[package]\nname="iface"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(root, "iface", "src", "lib.rs"), RUST_IFACE[var])
    deps = ['iface={path="../iface"}']
    if mid:
        _w(os.path.join(root, "middle", "Cargo.toml"),
           '[package]\nname="middle"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\niface={path="../iface"}\n')
        _w(os.path.join(root, "middle", "src", "lib.rs"), RUST_MIDDLE)
        deps.append('middle={path="../middle"}')
    if third:
        _w(os.path.join(root, "effimpl", "Cargo.toml"),
           '[package]\nname="effimpl"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\niface={path="../iface"}\n')
        _w(os.path.join(root, "effimpl", "src", "lib.rs"),
           'pub struct Crossterm;\nimpl iface::Backend for Crossterm { fn size(&self) -> usize { %s 0 } }\n'
           % SINK["rust"])
        deps.append('effimpl={path="../effimpl"}')
    body = RUST_APP[app_body(arm)]
    if third:
        body += RUST_APP["third"]
    _w(os.path.join(root, "app", "Cargo.toml"),
       '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\n' + "\n".join(deps) + "\n")
    _w(os.path.join(root, "app", "src", "lib.rs"), body)
    return dep_order(root, arm), os.path.join(root, "app")


def render_java(root, arm):
    """java scans BYTECODE, so the packages are class directories and javac is mandatory rather than a
    compile proof bolted on — the fixture cannot even be presented to the engine unbuilt."""
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    src = os.path.join(root, "src")
    for name, text in JAVA_IFACE[var].items():
        _w(os.path.join(src, "iface", name), text)
    if mid:
        for name, text in JAVA_MIDDLE.items():
            _w(os.path.join(src, "middle", name), text)
    if third:
        _w(os.path.join(src, "effimpl", "Crossterm.java"),
           'package effimpl; public class Crossterm implements iface.Backend { public int size() { %s return 0; } }\n'
           % SINK["java"])
    body = JAVA_APP[app_body(arm)]
    if third:
        body += JAVA_APP["third"]
    _w(os.path.join(src, "app", "App.java"), "package app;\npublic class App {\n" + body + "}\n")
    return src, [p for p, on in (("iface", True), ("middle", mid), ("effimpl", third)) if on]


def render_ts(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "package.json"), '{"name":"iface","version":"0.0.0","main":"src/index.ts"}\n')
    _w(os.path.join(root, "iface", "src", "index.ts"), TS_IFACE[var])
    if mid:
        _w(os.path.join(root, "middle", "package.json"),
           '{"name":"middle","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "middle", "src", "index.ts"), TS_MIDDLE)
        _link(os.path.join(root, "middle", "node_modules", "iface"), os.path.join(root, "iface"))
    if third:
        _w(os.path.join(root, "effimpl", "package.json"),
           '{"name":"effimpl","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "effimpl", "src", "index.ts"),
           'import * as netm from "node:net";\nimport { Backend } from "iface";\n'
           'export class Crossterm implements Backend { size(): number { %s ; return 0 } }\n' % SINK["ts"])
        _link(os.path.join(root, "effimpl", "node_modules", "iface"), os.path.join(root, "iface"))
    body = TS_APP[app_body(arm)]
    if third:
        body += TS_APP["third"]
    dep_decl = ('{"iface":"file:../iface"'
                + (',"middle":"file:../middle"' if mid else "")
                + (',"effimpl":"file:../effimpl"' if third else "") + "}")
    _w(os.path.join(root, "app", "package.json"),
       '{"name":"app","version":"0.0.0","dependencies":%s}\n' % dep_decl)
    _w(os.path.join(root, "app", "src", "index.ts"), body)
    _link(os.path.join(root, "app", "node_modules", "iface"), os.path.join(root, "iface"))
    if mid:
        _link(os.path.join(root, "app", "node_modules", "middle"), os.path.join(root, "middle"))
    if third:
        _link(os.path.join(root, "app", "node_modules", "effimpl"), os.path.join(root, "effimpl"))
    # `@types/node` is borrowed from the engine's own tree into EVERY package, not just the consumer:
    # tsc resolves the `node:net` sink's types relative to the file that imports it, so a link only on
    # `app` leaves the dependency unchecked and the typecheck fails there instead.
    types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
    if os.path.isdir(types):
        for pkg in ["iface", "app"] + (["middle"] if mid else []) + (["effimpl"] if third else []):
            _link(os.path.join(root, pkg, "node_modules", "@types"), types)
    return dep_order(root, arm), os.path.join(root, "app")


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def render_swift(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "Package.swift"), SW_MANIFEST % dict(mod="Iface", deps="", prods=""))
    _w(os.path.join(root, "iface", "Sources", "Iface", "iface.swift"), SW_IFACE[var])
    deps, prods = ['.package(path: "../iface")'], ['.product(name: "Iface", package: "iface")']
    if mid:
        _w(os.path.join(root, "middle", "Package.swift"),
           SW_MANIFEST % dict(mod="Middle", deps='.package(path: "../iface")',
                              prods='.product(name: "Iface", package: "iface")'))
        _w(os.path.join(root, "middle", "Sources", "Middle", "mid.swift"), SW_MIDDLE)
        deps.append('.package(path: "../middle")')
        prods.append('.product(name: "Middle", package: "middle")')
    if third:
        _w(os.path.join(root, "effimpl", "Package.swift"),
           SW_MANIFEST % dict(mod="EffImpl", deps='.package(path: "../iface")',
                              prods='.product(name: "Iface", package: "iface")'))
        _w(os.path.join(root, "effimpl", "Sources", "EffImpl", "eff.swift"),
           'import Foundation\nimport Iface\n'
           'public struct Crossterm: Backend { public init() {}; public func size() -> Int { %s; return 0 } }\n'
           % SINK["swift"])
        deps.append('.package(path: "../effimpl")')
        prods.append('.product(name: "EffImpl", package: "effimpl")')
    body = SW_APP[app_body(arm)]
    if third:
        body += SW_APP["third"]
    _w(os.path.join(root, "app", "Package.swift"),
       SW_MANIFEST % dict(mod="App", deps=", ".join(deps), prods=", ".join(prods)))
    _w(os.path.join(root, "app", "Sources", "App", "app.swift"), body)
    return dep_order(root, arm), os.path.join(root, "app")


# =====================================================================================================
# THE CROSS, ASSERTED RATHER THAN CLAIMED. If the consumer's source text ever stops being identical
# across the toggle's arms, every comparison below becomes fixture-induced and means nothing. This is the
# failure mode that produced three corrections to R475's original filing, so it is a hard check and not a
# comment.
# =====================================================================================================
CROSS_ARMS = ("c1_foreign_effectful", "c2_zero_impl", "c3_pure_only", "c5_unchained")


def _assert_identical_consumers(texts):
    """texts: {arm_id: consumer source text}. The c1/c5 consumers carry an EXTRA function (`appRun`,
    which supplies the foreign implementor); the function under test must be a verbatim prefix-line
    match, so compare the `dispatch` block alone."""
    ref = None
    for aid in CROSS_ARMS:
        t = texts.get(aid)
        if t is None:
            continue
        if ref is None:
            ref = (aid, t)
        elif t != ref[1]:
            return ("the consumer's dispatching source differs between %s and %s — the cross is "
                    "FIXTURE-INDUCED and no comparison below is evidence" % (ref[0], aid))
    return None


def build_proof(kind, path, extra=None):
    """Compile the rendered fixture. An absence-asserting control over an unbuildable program is NOT
    weak evidence, it is none: no correct engine could pass it differently and no broken one would be
    caught. Returns an error string, or None."""
    if NOBUILD:
        return None
    if kind == "rust":
        r = gd.run(["cargo", "build", "--offline", "-q"], cwd=path)
    elif kind == "swift":
        r = gd.run(["swift", "build"], cwd=path)
    elif kind == "ts":
        tsc = os.path.join(gd.CANDOR_TS, "node_modules", "typescript", "bin", "tsc")
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        if not os.path.exists(tsc) or not os.path.isdir(types):
            return "SKIPPED: no tsc / @types under CANDOR_TS/node_modules — the ts fixture is UNTYPECHECKED"
        # `--types node` explicitly: with nodenext the automatic @types sweep does not reach the linked
        # directory from an IMPORTED package's file, so the dependency's `node:net` sink fails to
        # typecheck while the consumer's passes — a compile proof that covers only half the fixture.
        r = gd.run(["node", tsc, "--noEmit", "--module", "nodenext", "--moduleResolution", "nodenext",
                    "--target", "es2022", "--types", "node",
                    os.path.join("src", "index.ts")] + (extra or []), cwd=path)
    else:
        return None
    if r.returncode != 0:
        return "%s build FAILED: %s" % (kind, (r.stderr or r.stdout).decode()[:300].replace("\n", " | "))
    return None


def producer_note(path):
    """Diagnostics for ⟨0.39⟩ obligations 1 and 2 — printed, never asserted (see the header)."""
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception:
        return "unreadable"
    fns = d["functions"] if isinstance(d, dict) else d
    disp = sum(1 for e in fns if e.get("dispatchesOn"))
    # SPEC §2 (:441, :3565) defines `interfaceUnion` as a PER-ENTRY field — the union is a synthetic
    # entry APPENDED TO `functions`, not a top-level key. Reading it at the top level made this
    # diagnostic print `absent` even for a conforming producer, which is how it read for rust right up
    # until the rung shipped. Diagnostic-only, but a wrong diagnostic misleads the NEXT engine, which
    # is the whole audience of this part.
    iu = any(f.get("interfaceUnion") for f in fns) if isinstance(d, dict) else None
    return "rows=%d dispatchesOn=%d interfaceUnion=%s" % (len(fns), disp, "present" if iu else "absent")


def facts(leaves, entry):
    """The consumer's row as a triple, with ABSENCE made explicit. `leaf_info` omits pure functions
    because the engines do — so a missing key is a POSITIVE purity claim, not a missing measurement, and
    conflating the two is the shape of the sin itself."""
    if leaves is None:
        return None
    e = leaves.get(entry)
    if e is None:
        return dict(eff=frozenset(), unknown=False, invisible=frozenset(), absent=True)
    return dict(eff=e["eff"], unknown=e["unknown"], invisible=e["invisible"], absent=False)


def judge(want, f):
    bad = []
    for x in sorted(want.get("has", ())):
        if x not in f["eff"]:
            bad.append("missing %s" % x)
    for x in sorted(want.get("hasnt", ())):
        if x in f["eff"]:
            bad.append("FABRICATED %s" % x)
    if want.get("unknown") is not None and f["unknown"] != want["unknown"]:
        bad.append("unknown=%s want %s" % (f["unknown"], want["unknown"]))
    if want.get("invisible") is not None and bool(f["invisible"]) != want["invisible"]:
        bad.append("invisible=%s want %s" % (sorted(f["invisible"]) or "∅", want["invisible"]))
    return bad


def show(f):
    if f["absent"]:
        return "ABSENT (a purity claim)"
    return "eff=%s unknown=%s invisible=%s" % (sorted(f["eff"]) or "∅", f["unknown"],
                                               sorted(f["invisible"]) or "∅")


def run_engine(name, ws):
    """Returns ({arm_id: facts-or-None}, notes, err)."""
    scanner = sa.SCANNERS[name]()
    if not scanner.available:
        return None, None, scanner.err
    out, notes, texts = {}, [], {}
    for arm in ARMS:
        root = os.path.join(ws, name, arm["id"])
        os.makedirs(root, exist_ok=True)
        if name == "java":
            src, pkgs = render_java(root, arm)
            texts[arm["id"]] = open(os.path.join(src, "app", "App.java")).read().replace(JAVA_APP["third"], "")
            cls = os.path.join(root, "cls")
            os.makedirs(cls, exist_ok=True)
            srcs = []
            for d, _dd, fs in os.walk(src):
                srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
            c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
            if c.returncode != 0:
                return None, None, "javac failed on %s: %s" % (arm["id"], c.stderr.decode()[:300])
            # ONE class directory per package, in the dependency order `pkgs` names — a package scanned
            # with its siblings' classes on the same path is not a separate package at all, which is the
            # isolation every arm here depends on.
            deps = [os.path.join(root, "d_" + pkg) for pkg in pkgs]
            for pkg, d in zip(pkgs, deps):
                os.makedirs(d, exist_ok=True)
                shutil.copytree(os.path.join(cls, pkg), os.path.join(d, pkg), dirs_exist_ok=True)
            app = os.path.join(root, "d_app")
            os.makedirs(app, exist_ok=True)
            shutil.copytree(os.path.join(cls, "app"), os.path.join(app, "app"), dirs_exist_ok=True)
        else:
            render = dict(rust=render_rust, ts=render_ts, swift=render_swift)[name]
            deps, app = render(root, arm)
            src_file = dict(rust=("app", "src", "lib.rs"), ts=("app", "src", "index.ts"),
                            swift=("app", "Sources", "App", "app.swift"))[name]
            whole = open(os.path.join(root, *src_file)).read()
            third_block = dict(rust=RUST_APP, ts=TS_APP, swift=SW_APP)[name]["third"]
            texts[arm["id"]] = whole.replace(third_block, "")
            # BUILD THE CONSUMER ONLY: it pulls every dependency package in transitively, so a build of
            # `app` is a build of the whole arm. Building each package separately would cost three
            # toolchain invocations to prove the same thing.
            err = build_proof(name, app)
            if err and err.startswith("SKIPPED"):
                notes.append("  NOTE  %s %-22s %s" % (name, arm["id"], err))
            elif err:
                return None, None, "%s (%s)" % (err, arm["id"])

        dep_reports = []
        for d in deps:
            r = scanner.scan(d)
            if not r.produced:
                return None, None, "%s: dependency scan produced no report for %s (rc=%d) %s" % (
                    arm["id"], d, r.rc, r.note)
            dep_reports.append(r.report)
            notes.append("  dep   %s %-22s %-8s %s" % (name, arm["id"], os.path.basename(d),
                                                       producer_note(r.report)))
        r = scanner.scan(app, deps=dep_reports if arm["chained"] else ())
        if not r.produced:
            return None, None, "%s: consumer scan produced no report (rc=%d) %s" % (arm["id"], r.rc, r.note)
        leaves, _unc = sa.leaf_info(r.report, ("::", "."))
        f = facts(leaves, ENTRY[name][arm["entry"]])
        if f is None:
            # ⟨0.21⟩ Row-1 fail-closed empty: the engine judged NOTHING. That is not "the consumer is
            # pure", and reading it as such is the fabrication mirror of the sin under test.
            return None, None, "%s: consumer report is a judged-nothing manifest (rc=%d)" % (arm["id"], r.rc)
        out[arm["id"]] = f
    cross = _assert_identical_consumers(texts)
    if cross:
        return None, None, cross
    return out, notes, None


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-part92-")
    print("=" * 100)
    print("CHAINED-DISPATCH UNION differential ⟨0.39⟩ — a consumer carries every implementor it can see")
    print("  fixture : THREE packages — iface (dispatches) · effimpl (a FOREIGN effectful impl) · app;")
    print("            c6 adds a FOURTH — `middle`, which dispatches over iface's abstraction and owns")
    print("            neither it nor any implementor of it (SOUNDNESS R504)")
    print("  property: c1 the foreign implementor's %s MUST reach the consumer;" % EFFECT)
    print("            c2 zero implementors MUST stay a disclosed Unknown (the toggle's other side);")
    print("            c3 an only-pure library MUST stay pure; c4 a sealed union stays EXACT;")
    print("            c5 unchained, the same consumer discloses via `invisible`;")
    print("            c6 a MIDDLE package that owns nothing must still name the member it dispatches on")
    print("  cross   : the consumer's dispatching source is BYTE-IDENTICAL across c1/c2/c3/c5, asserted")
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART92_NOBUILD is set — fixtures were NOT compiled. An absence-asserting")
        print("      control over an unbuilt program is not evidence; this run is for iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — c2_zero_impl's DEPENDENCY is being rendered with the")
        print("       'impl' variant (one pure implementor), so the arm that MUST stay a disclosed")
        print("       Unknown cannot be. This run's verdict MUST go red. A clean run never prints this.")

    results, all_notes = {}, []
    for name in ("rust", "java", "ts", "swift"):
        res, notes, err = run_engine(name, ws)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                print("  %-6s not available — skipped LOUDLY: %s" % (name, err))
            else:
                print("  %-6s BROKEN: %s" % (name, err))
                results[name] = "broken"
            continue
        results[name] = res
        all_notes += notes
    live = {k: v for k, v in results.items() if isinstance(v, dict)}
    if not live:
        print("\nCHAINED-DISPATCH: no engine available — NOT a pass")
        return 2
    if any(v == "broken" for v in results.values()):
        print("\nCHAINED-DISPATCH: an engine was present but broken — NOT a pass")
        return 2

    print("\nPRODUCER-SIDE DIAGNOSTICS (⟨0.39⟩ obligations 1 and 2 — printed, not asserted):")
    for n in all_notes:
        print(n)

    print()
    fails, xfail_passed = [], []
    for arm in ARMS:
        for name, res in sorted(live.items()):
            f = res[arm["id"]]
            bad = judge(arm["want"], f)
            exp = XFAIL.get((arm["id"], name))
            if not bad:
                if exp:
                    print("  XFAIL ARM PASSED  %-22s %-6s — expectation is STALE: %s" % (arm["id"], name, exp))
                    xfail_passed.append((arm["id"], name))
                else:
                    print("  OK    %-22s %-6s %s" % (arm["id"], name, show(f)))
            elif exp:
                print("  xfail %-22s %-6s %s — %s" % (arm["id"], name, show(f), "; ".join(bad)))
            else:
                print("  FAIL  %-22s %-6s %s — %s  [%s]" % (arm["id"], name, show(f), "; ".join(bad),
                                                            arm["why"]))
                fails.append((arm["id"], name))

    print()
    if xfail_passed:
        print("CHAINED-DISPATCH: %d xfail arm(s) PASSED — an expectation that has become true is a "
              "FAILURE here. Retire it from XFAIL in the same commit as the engine fix (SOUNDNESS R475)."
              % len(xfail_passed))
        return 1
    if fails:
        print("CHAINED-DISPATCH: %d cell(s) wrong — see SOUNDNESS R475 and SPEC §4 ⟨0.39⟩" % len(fails))
        return 1
    print("CHAINED-DISPATCH: OK — every engine's consumer carries the effects of every implementor "
          "visible to it, keeps the zero-implementor disclosure, and fabricates nothing over a "
          "legitimately-pure or sealed abstraction")
    return 0


if __name__ == "__main__":
    sys.exit(main())
