#!/usr/bin/env python3
"""PART 104 — THE CALL-TARGET TAXONOMY: one sample cell per class, four-way, plus the R764 cell.
SKELETON (call-target round 1, 2026-10-25). SPEC §4 (bounded-CHA, ⟨0.39⟩ chained consumer + obligations 1-3,
the ⟨0.40⟩ receiver-type sentence of the conventionally-pure MAY). SOUNDNESS R764, R1405-R1428.

WHY THIS PART EXISTS. Four engine lanes built call-target matrices of 2k-30k cells each
(`~/candor-handoff/calltarget-analysis/<engine>/`) and found the same four-stage structure in every engine:
SITE (an implicit call into user code that produces no edge and no Unknown), WIRE (a producer publishes no
joinable key, or chaining deletes a disclosure), IDENTITY (a unit key coarser than the language's), TYPE (an
operand the engine cannot type). The suite cannot carry 2k-30k cells per engine (~476 s for 151 parts), so the
structure is two-tier (FABLE-SYNTHESIS §2.4): each engine's matrix moves into its own repo as the EXHAUSTIVE
silence instrument, and this part pins the cross-engine PROPERTY per class with ONE sample cell per class per
engine. A cell here is the fixed point a lane's matrix must agree with; it is not a census.

THE TAXONOMY (language-neutral; a lane maps a register row to one of these coordinates BEFORE fixing it):

    site kind     explicit dispatch · implicit hook (formatting, comparison, hashing, cloning, iteration,
                  conversion, deferred-force, drop/close) · operator · callback (platform runs a function
                  value) · recognised-but-untyped (a recognised implicit site whose operand is typed only by an
                  abstraction that does not declare the hook member)
    placement     same unit · same package · chained dependency's own · third package · consumer-of-dependency
                  (the dependency dispatches, the consumer supplies the implementor) · unseen
    count         1 · several · pure-only · past the bound (13)
    closedness    closed (final/sealed/private/value type/non-`pub`/non-`open`) · open
    wire          none (one tree) · chained, key published · chained, key absent · `invisible`-only (an unchained
                  dependency: the row carries only the ledger, which passes every `deny` on the scan route)

MODES, because the SPEC does not yet bind every class (the site clause is PROPOSED, not normative —
`proposals/call-target-site-and-wire.md` item 1):

    assert   the SPEC binds the property today; a wrong verdict is a FAIL unless the (cell, engine) is in XFAIL,
             and an XFAIL that passes is a FAILURE (retire it in the engine-fix commit).
    ledger   the `invisible`-only class: SPEC requires the unchained package to be disclosed in the ledger; the
             cell asserts the ledger (or an Unknown) is present and RECORDS the gates, which read 0 by design.
    record   the property depends on the pending site clause (option A asserts every recognised implicit site,
             option B only the iteration/callback/I/O/conversion/deferred class); the verdict is PRINTED with
             the option that would decide it, never scored. These cells are where the PROPOSED clause will bite.
    control  a CLEAN program (EXECUTED: the effectful body is reachable by name and never runs). `deny Fs` must
             exit 0 — a charge is a FABRICATION — and a POSITIVE TWIN arm (the effect moved onto the body that does
             run, or the stored value invoked; executed) must reach the caller, so the control is shown able to fail
             on every run. A silent twin is a FAIL unless TWIN_SILENT names the row that makes it so (VACUOUS).
    rcontrol a `control` the SPEC does not bind yet: both arms are run and PRINTED, never scored.
    r764     a newly published / pure-only union must not delete an unchained owner's disclosure (SPEC §4
             ⟨0.39⟩: "A mechanism that makes reports better must not make silence cheaper"). Two arms over the
             same three packages: `base` (the producer's report as written) and `pure` (the producer's report
             with the owner's union entry DOCTORED to pure-only, re-using the spelling the owner's OWN report
             gives that key, so the doctor cannot invent a spelling). Both must disclose.

ROUND 2 (2026-10-25) adds CONTROL cells — CLEAN programs, executed — because the round-3/4 key-publishing work widens
exactly the surface that fabricates (FABLE-REVIEW §3.1/§3.2/§3.4): `wx_unrelated_override`, `wx_exact_producer`,
`cb_stored_not_run` (scored) and `wx_sibling_override` (recorded: ⟨0.39⟩ obligation 3 as written REQUIRES that union),
plus the scored POSITIVE `wx_heldvalue_sibling`, which pins why that union may not be narrowed by the consumer.

Every consumer function `c_go` reads the environment first: `deny Env` is the carrier on every cell, so a policy
that matched nothing cannot pass. Truth: every effectful body performs `Fs` directly (the same sink every engine
charges in its own row); the cells were also EXECUTED once by hand for the evidence file
(`~/candor-handoff/calltarget-round1/spec/`), not in-suite.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402
import split_arms as sa            # noqa: E402

SPEC_CLAUSES = [
    ("§4 bounded-CHA", "visible implementor, too many, or an ambiguous name is disclosed indeterminacy, never silent purity"),
    ("§4 ⟨0.39⟩ chained consumer", "A CHAINED CONSUMER'S INHERITED SIGNATURE MUST CARRY THE EFFECTS OF EVERY IMPLEMENTOR VISIBLE"),
    ("§4 ⟨0.39⟩ R764", "A mechanism that makes reports better must not make silence cheaper."),
    ("§4 ⟨0.39⟩ subclass", "\"Implementor\" in this clause includes a SUBCLASS that overrides a class's member."),
    ("§4 ⟨0.40⟩ receiver type", "The set is judged by the RECEIVER's declared type"),
    ("§4 named miss", "MAY remain unflagged, but then MUST be documented as a named miss"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")   # ex_local_one's implementor loses its Fs: the reference goes red
ENGINES = ("rust", "java", "ts", "swift")


def _fx(lang, eid):
    for e in gd.EFFECTS:
        if e["id"] == eid:
            return e["sink"][lang]


# ------------------------------------------------------------------------------------------------- the cells
# Each builder returns {"pkgs": {name: (deps, text)}, "chain": [names chained into app], "doctor": None|name}.
# `text` for java is {ClassName: source}; for the other languages one source file per package.
# `FS` is replaced by the effect, `ENV` by the carrier. A builder returning a str is a DECLARED EXCLUSION.

def _ex_local(n_eff, n_pure):
    def b(lang):
        eff = ["E"] if n_eff else []
        pures = ["P%d" % k for k in range(1, n_pure + 1)]
        if lang == "rust":
            t = "pub trait Tr { fn act(&self) -> i32; }\n"
            t += "".join("pub struct %s;\nimpl Tr for %s { fn act(&self) -> i32 { FS 1 } }\n" % (x, x) for x in eff)
            t += "".join("pub struct %s;\nimpl Tr for %s { fn act(&self) -> i32 { %d } }\n" % (x, x, k)
                         for k, x in enumerate(pures))
            t += "pub fn c_go(t: &dyn Tr) -> i32 { ENV t.act() }\n"
            return {"pkgs": {"app": ([], t)}, "chain": []}
        if lang == "java":
            cl = {"Tr": "package app;\npublic interface Tr { int act(); }\n"}
            for x in eff:
                cl[x] = "package app;\npublic class %s implements Tr { public int act() { FS return 1; } }\n" % x
            for k, x in enumerate(pures):
                cl[x] = "package app;\npublic class %s implements Tr { public int act() { return %d; } }\n" % (x, k)
            cl["App"] = "package app;\npublic class App { public static int c_go(Tr t) { ENV return t.act(); } }\n"
            return {"pkgs": {"app": ([], cl)}, "chain": []}
        if lang == "ts":
            t = "export interface Tr { act(): number; }\n"
            t += "".join("export class %s implements Tr { act(): number { FS return 1; } }\n" % x for x in eff)
            t += "".join("export class %s implements Tr { act(): number { return %d; } }\n" % (x, k)
                         for k, x in enumerate(pures))
            t += "export function c_go(t: Tr): number { ENV return t.act(); }\n"
            return {"pkgs": {"app": ([], t)}, "chain": []}
        t = "public protocol Tr { func act() -> Int }\n"
        t += "".join("public struct %s: Tr { public init() {}\n  public func act() -> Int { FS\n    return 1 } }\n" % x
                     for x in eff)
        t += "".join("public struct %s: Tr { public init() {}\n  public func act() -> Int { %d } }\n" % (x, k)
                     for k, x in enumerate(pures))
        t += "public func c_go(_ t: any Tr) -> Int {\n  ENV\n  return t.act()\n}\n"
        return {"pkgs": {"app": ([], t)}, "chain": []}
    return b


def _wx_consumer_impl(lang):
    if lang == "rust":
        return {"pkgs": {"api": ([], "pub trait Tr { fn act(&self) -> i32; }\npub fn run(t: &dyn Tr) -> i32 { t.act() }\n"),
                         "app": (["api"], "use api::{Tr, run};\npub struct Mine;\nimpl Tr for Mine { fn act(&self) -> i32 { FS 2 } }\n"
                                          "pub fn c_go() -> i32 { ENV run(&Mine) }\n")}, "chain": ["api"]}
    if lang == "java":
        return {"pkgs": {"api": ([], {"Tr": "package api;\npublic interface Tr { int act(); }\n",
                                      "Run": "package api;\npublic class Run { public static int run(Tr t) { return t.act(); } }\n"}),
                         "app": (["api"], {"Mine": "package app;\npublic class Mine implements api.Tr { public int act() { FS return 2; } }\n",
                                           "App": "package app;\npublic class App { public static int c_go() { ENV return api.Run.run(new Mine()); } }\n"})},
                "chain": ["api"]}
    if lang == "ts":
        return {"pkgs": {"api": ([], "export interface Tr { act(): number; }\nexport function run(t: Tr): number { return t.act(); }\n"),
                         "app": (["api"], 'import { type Tr, run } from "api";\nexport class Mine implements Tr { act(): number { FS return 2; } }\n'
                                          "export function c_go(): number { ENV return run(new Mine()); }\n")}, "chain": ["api"]}
    return {"pkgs": {"api": ([], "public protocol Tr { func act() -> Int }\npublic func run(_ t: any Tr) -> Int { t.act() }\n"),
                     "app": (["api"], "import Api\npublic struct Mine: Tr { public init() {}\n  public func act() -> Int { FS\n    return 2 } }\n"
                                      "public func c_go() -> Int {\n  ENV\n  return run(Mine())\n}\n")}, "chain": ["api"]}


def _wx_concrete_subclass(lang):
    if lang == "rust":
        return "no class inheritance — a consumer-supplied implementor of a dependency's abstraction is wx_consumer_impl"
    if lang == "java":
        return {"pkgs": {"api": ([], {"Base": "package api;\npublic class Base { public int m() { return 1; } }\n",
                                      "Run": "package api;\npublic class Run { public static int run(Base b) { return b.m(); } }\n"}),
                         "app": (["api"], {"Mine": "package app;\npublic class Mine extends api.Base { public int m() { FS return 2; } }\n",
                                           "App": "package app;\npublic class App { public static int c_go() { ENV return api.Run.run(new Mine()); } }\n"})},
                "chain": ["api"]}
    if lang == "ts":
        return {"pkgs": {"api": ([], "export class Base { m(): number { return 1; } }\nexport function run(b: Base): number { return b.m(); }\n"),
                         "app": (["api"], 'import { Base, run } from "api";\nexport class Mine extends Base { m(): number { FS return 2; } }\n'
                                          "export function c_go(): number { ENV return run(new Mine()); }\n")}, "chain": ["api"]}
    return {"pkgs": {"api": ([], "open class Base { public init() {}\n  open func m() -> Int { 1 } }\npublic func run(_ b: Base) -> Int { b.m() }\n"),
                     "app": (["api"], "import Api\nfinal class Mine: Base { override func m() -> Int { FS\n    return 2 } }\n"
                                      "public func c_go() -> Int {\n  ENV\n  return run(Mine())\n}\n")}, "chain": ["api"]}


# ---- the three CONTROL cells (call-target round 2, FABLE-REVIEW §3.1/§3.2/§3.4). Every one is CLEAN by execution: the
# effectful body exists, is reachable by NAME, and never runs. Each also renders a POSITIVE TWIN (`twin=True`): the
# same program with the effect on the body that DOES run, or with the stored value invoked — executed, the effect
# runs. The twin arm runs EVERY time (mode `control`) and must reach the caller (charge or disclose), so a control
# that passes only because the engine never reads the site is visible: a twin that stays silent is either a row in
# TWIN_SILENT (the control is VACUOUS on that engine until the row is fixed) or a FAIL.


def _tw(lang, twin):
    return ("FS\n    " if lang == "swift" else "FS ") if twin else ""


def _wx_override(leg):
    """api: an open base whose OWN member `run` dispatches `self.m()` (so the dependency publishes the key `Base.m`).
    app: the receiver is a CLOSED subclass `Left` (final / no visible subclass / a struct) with a pure `m`, plus one
    effectful `m` that cannot run at `Left().run()`, instantiated by `c_mk` so reachability cannot excuse it:

      leg "unrelated"  on `Other`, a class that is NOT a subtype of `Base` (rust: an inherent method). No SPEC sentence
                       makes `Other` an implementor of `Base.m`, so a charge is a FABRICATION — scored (`control`).
                       java's `c_ct_unrelated_*` shape; FABLE-REVIEW §3.1.
      leg "sibling"    on `Right`, a SIBLING subclass of `Base`. Executed CLEAN, but ⟨0.39⟩ obligation 3 says the
                       consumer's join MUST union, PER KEY, its own visible implementors, and `Right.m` is one: as
                       written, the SPEC does not scope that union to the consumer call site's receiver subtree, so
                       this charge is the sound over-approximation it requires, not a non-conformance. RECORDED
                       (`rcontrol`), and it must stay charged: the consumer MUST NOT narrow by its own call-site
                       receiver, because `wx_heldvalue_sibling` publishes the same key and its sibling RUNS (proposal
                       §3.1; FABLE-OBLIGATION3). swift R1436 and rust R1420 (a) are this shape."""
    def b(lang, twin=False):
        t = _tw(lang, twin)
        r = ("FS\n    " if lang == "swift" else "FS ") if leg == "sibling" else ""
        o = ("FS\n    " if lang == "swift" else "FS ") if leg == "unrelated" else ""
        if lang == "rust":
            return {"pkgs": {"api": ([], "pub trait Tr { fn m(&self) -> i32; fn run(&self) -> i32 { self.m() } }\n"),
                             "app": (["api"], ("use api::Tr;\npub struct Left;\nimpl Tr for Left { fn m(&self) -> i32 { %s2 } }\n"
                                               "pub struct Right;\nimpl Tr for Right { fn m(&self) -> i32 { %s3 } }\n"
                                               "pub struct Other;\nimpl Other { pub fn m(&self) -> i32 { %s4 } }\n"
                                               "pub fn c_go() -> i32 { ENV Left.run() }\n"
                                               "pub fn c_mk() -> (Right, Other) { (Right, Other) }\n") % (t, r, o))}, "chain": ["api"]}
        if lang == "java":
            return {"pkgs": {"api": ([], {"Base": "package api;\npublic class Base { public int m() { return 1; } "
                                                  "public int run() { return m(); } }\n"}),
                             "app": (["api"], {"Left": "package app;\npublic final class Left extends api.Base { public int m() { %sreturn 2; } }\n" % t,
                                               "Right": "package app;\npublic class Right extends api.Base { public int m() { %sreturn 3; } }\n" % r,
                                               "Other": "package app;\npublic class Other { public int m() { %sreturn 4; } }\n" % o,
                                               "App": JV_APP % ("public static int c_go() { ENV return new Left().run(); } "
                                                                "public static Object[] c_mk() { return new Object[] { new Right(), new Other() }; }")})},
                    "chain": ["api"]}
        if lang == "ts":
            # No `final` in TypeScript; `Left` has no visible subclass, so its subtree is {Left}. Not closed with a
            # private constructor as wx_exact_producer is: an explicit `constructor() { super(); }` adds an unrelated
            # `Unknown[callback:super]` (measured on 0.40.17) that would cloud the cell's detail.
            return {"pkgs": {"api": ([], "export class Base { m(): number { return 1; } run(): number { return this.m(); } }\n"),
                             "app": (["api"], ('import { Base } from "api";\n'
                                               "class Left extends Base { m(): number { %sreturn 2; } }\n"
                                               "export class Right extends Base { m(): number { %sreturn 3; } }\n"
                                               "export class Other { m(): number { %sreturn 4; } }\n"
                                               "export function c_go(): number { ENV return new Left().run(); }\n"
                                               "export function c_mk(): object[] { return [new Right(), new Other()]; }\n") % (t, r, o))},
                    "chain": ["api"]}
        return {"pkgs": {"api": ([], "open class Base { public init() {}\n  open func m() -> Int { 1 }\n  public func run() -> Int { m() } }\n"),
                         "app": (["api"], ("import Api\nfinal class Left: Base { override func m() -> Int { %sreturn 2 } }\n"
                                           "class Right: Base { override func m() -> Int { %sreturn 3 } }\n"
                                           "final class Other { func m() -> Int { %sreturn 4 } }\n"
                                           "public func c_go() -> Int {\n  ENV\n  return Left().run()\n}\n"
                                           "public func c_mk() -> [Any] { [Right(), Other()] }\n") % (t, r, o))}, "chain": ["api"]}
    return b


def _wx_heldvalue_sibling(lang):
    """The scored POSITIVE that pins why `wx_sibling_override` must stay charged (FABLE-OBLIGATION3 §3; the swift
    round-2 lane's control K14h). The dependency's own member `walk(other)` dispatches `other.visit()` on a HELD
    VALUE, so it publishes the same key `Base.visit` as `wx_sibling_override`'s self-dispatch — the wire does not
    say which receiver was dispatched on. The consumer calls `Left().walk(Right())` on a CLOSED `Left`, and the
    sibling `Right.visit` RUNS (executed). A consumer that narrowed the per-key union by its own call-site receiver
    (`Left`'s subtree) would be SILENT here: the reason the narrowing is refused (proposal §3.1)."""
    if lang == "rust":
        return {"pkgs": {"api": ([], "pub trait V { fn visit(&self) -> i32; fn walk(&self, other: &dyn V) -> i32 { other.visit() } }\n"),
                         "app": (["api"], "use api::V;\npub struct Left;\nimpl V for Left { fn visit(&self) -> i32 { 2 } }\n"
                                          "pub struct Right;\nimpl V for Right { fn visit(&self) -> i32 { FS 3 } }\n"
                                          "pub fn c_go() -> i32 { ENV Left.walk(&Right) }\n")}, "chain": ["api"]}
    if lang == "java":
        return {"pkgs": {"api": ([], {"Base": "package api;\npublic class Base { public int visit() { return 1; } "
                                              "public int walk(Base other) { return other.visit(); } }\n"}),
                         "app": (["api"], {"Left": "package app;\npublic final class Left extends api.Base { public int visit() { return 2; } }\n",
                                           "Right": "package app;\npublic class Right extends api.Base { public int visit() { FS return 3; } }\n",
                                           "App": JV_APP % "public static int c_go() { ENV return new Left().walk(new Right()); }"})},
                "chain": ["api"]}
    if lang == "ts":
        return {"pkgs": {"api": ([], "export class Base { visit(): number { return 1; } walk(other: Base): number { return other.visit(); } }\n"),
                         "app": (["api"], 'import { Base } from "api";\n'
                                          "class Left extends Base { visit(): number { return 2; } }\n"
                                          "export class Right extends Base { visit(): number { FS return 3; } }\n"
                                          "export function c_go(): number { ENV return new Left().walk(new Right()); }\n")},
                "chain": ["api"]}
    return {"pkgs": {"api": ([], "open class Base { public init() {}\n  open func visit() -> Int { 1 }\n"
                                 "  public func walk(_ other: Base) -> Int { other.visit() } }\n"),
                     "app": (["api"], "import Api\nfinal class Left: Base { override func visit() -> Int { 2 } }\n"
                                      "class Right: Base { override func visit() -> Int { FS\n    return 3 } }\n"
                                      "public func c_go() -> Int {\n  ENV\n  return Left().walk(Right())\n}\n")}, "chain": ["api"]}


def _wx_exact_producer(lang, twin=False):
    """api: an open base, a CLOSED subclass `Fin` (final / non-`open` / private-constructor / concrete struct) with a
    pure override, and `run(f: Fin)` dispatching `f.m()`. app: a consumer subclass (rust: implementor) of the BASE with
    an effectful `m`, instantiated by `c_mk`. `run`'s receiver is exact, so the consumer's override cannot run there —
    a producer that publishes a class-wide key for this site, or a consumer that joins one, fabricates."""
    t = _tw(lang, twin)
    if lang == "rust":
        return {"pkgs": {"api": ([], "pub trait Tr { fn m(&self) -> i32; }\npub struct Fin;\n"
                                     "impl Tr for Fin { fn m(&self) -> i32 { %s1 } }\npub fn run(f: &Fin) -> i32 { f.m() }\n" % t),
                         "app": (["api"], "use api::{Tr, Fin, run};\npub struct Mine;\nimpl Tr for Mine { fn m(&self) -> i32 { FS 2 } }\n"
                                          "pub fn c_go() -> i32 { ENV run(&Fin) }\npub fn c_mk() -> Mine { Mine }\n")}, "chain": ["api"]}
    if lang == "java":
        return {"pkgs": {"api": ([], {"Base": "package api;\npublic class Base { public int m() { return 1; } }\n",
                                      "Fin": "package api;\npublic final class Fin extends Base { public int m() { %sreturn 3; } }\n" % t,
                                      "Run": "package api;\npublic class Run { public static int run(Fin f) { return f.m(); } }\n"}),
                         "app": (["api"], {"Mine": "package app;\npublic class Mine extends api.Base { public int m() { FS return 2; } }\n",
                                           "App": JV_APP % ("public static int c_go() { ENV return api.Run.run(new api.Fin()); } "
                                                            "public static Object c_mk() { return new Mine(); }")})},
                "chain": ["api"]}
    if lang == "ts":
        # TypeScript has no `final`; a PRIVATE constructor forbids `extends Fin` (TS2675) and the private field makes
        # the type nominal, so no consumer value can be passed as a `Fin`.
        return {"pkgs": {"api": ([], "export class Base { m(): number { return 1; } }\n"
                                     "export class Fin extends Base { private k = 0; private constructor() { super(); } "
                                     "static make(): Fin { return new Fin(); } m(): number { %sreturn 3; } }\n"
                                     "export function run(f: Fin): number { return f.m(); }\n" % t),
                         "app": (["api"], 'import { Base, Fin, run } from "api";\nexport class Mine extends Base { m(): number { FS return 2; } }\n'
                                          "export function c_go(): number { ENV return run(Fin.make()); }\n"
                                          "export function c_mk(): Mine { return new Mine(); }\n")}, "chain": ["api"]}
    return {"pkgs": {"api": ([], "open class Base { public init() {}\n  open func m() -> Int { 1 } }\n"
                                 "public final class Fin: Base { public override init() {}\n  public override func m() -> Int { %sreturn 3 } }\n"
                                 "public func run(_ f: Fin) -> Int { f.m() }\n" % t),
                     "app": (["api"], "import Api\nfinal class Mine: Base { override func m() -> Int { FS\n    return 2 } }\n"
                                      "public func c_go() -> Int {\n  ENV\n  return run(Fin())\n}\n"
                                      "public func c_mk() -> Any { Mine() }\n")}, "chain": ["api"]}


def _cb_stored_not_run(lang, twin=False):
    """A platform-shaped function value (rust `fn()`, java `Runnable`, ts `() => void`, swift `() -> Void`) naming an
    effectful function is created and STORED in a field, and never invoked. The NON-INVOKING LOOK-ALIKE axis (java
    R1442 is its live instance). Calibration twin: the stored value is invoked.

    A NAMED function, never a closure LITERAL: SPEC §4 (⟨0.39⟩, "What this clause deliberately does NOT do") records
    that engines charge a closure by SYNTACTIC CONTAINMENT — `keep(|| net)` yields `Net` where `keep` never calls it —
    as the precedent the escaping-value rule was refused against. A stored-not-run closure literal is therefore
    charged BY DESIGN and would be a wrong control; a reference to a function declared elsewhere contains no body."""
    if lang == "rust":
        call = "(h.f)(); " if twin else ""
        return _one(lang, "fn eff() { FS }\npub struct H { pub f: fn() }\npub fn c_go() { ENV let h = H { f: eff }; %slet _k = &h; }\n" % call,
                    None, None, None)
    if lang == "java":
        call = "h.r.run(); " if twin else ""
        return _one(lang, None, {"H": "package app;\npublic class H { Runnable r; public H(Runnable r) { this.r = r; } }\n",
                                 "App": JV_APP % ("static void eff() { FS } public static void c_go() { ENV H h = new H(App::eff); %s}" % call)},
                    None, None)
    if lang == "ts":
        call = "h.r(); " if twin else ""
        return _one(lang, None, None, "function eff(): void { FS }\nclass H { r: () => void; constructor(r: () => void) { this.r = r; } }\n"
                    "export function c_go(): void { ENV const h = new H(eff); %svoid h; }\n" % call, None)
    call = "  h.r()\n" if twin else ""
    return _one(lang, None, None, None, "func eff() { FS\n}\nstruct H { let r: () -> Void }\n"
                "public func c_go() {\n  ENV\n  let h = H(r: eff)\n%s  _ = h\n}\n" % call)


def _one(lang, rust, java, ts, swift):
    t = {"rust": rust, "java": java, "ts": ts, "swift": swift}[lang]
    if t is None or isinstance(t, str) and t.startswith("EXCL:"):
        return t[5:] if t else "no such construct"
    if lang == "java":
        return {"pkgs": {"app": ([], t)}, "chain": []}
    return {"pkgs": {"app": ([], t)}, "chain": []}


RS_FMT = "use std::fmt;\n"
JV_APP = "package app;\npublic class App { %s }\n"


def _hk_fmt_local(lang):
    return _one(lang,
                RS_FMT + "pub struct S;\nimpl fmt::Display for S { fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result { FS write!(f, \"s\") } }\n"
                "pub fn c_go() -> String { ENV format!(\"{}\", S) }\n",
                {"S": "package app;\npublic class S { public String toString() { FS return \"s\"; } }\n",
                 "App": JV_APP % "public static String c_go() { ENV return \"\" + new S(); }"},
                "export class S { toString(): string { FS return \"s\"; } }\nexport function c_go(): string { ENV return `${new S()}`; }\n",
                "struct S: CustomStringConvertible { var description: String { FS\n    return \"s\" } }\n"
                "public func c_go() -> String {\n  ENV\n  return \"\\(S())\"\n}\n")


def _hk_fmt_container(lang):
    return _one(lang,
                RS_FMT + "pub struct S;\nimpl fmt::Debug for S { fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result { FS write!(f, \"s\") } }\n"
                "pub fn c_go() -> String { ENV format!(\"{:?}\", vec![S]) }\n",
                {"S": "package app;\npublic class S { public String toString() { FS return \"s\"; } }\n",
                 "App": JV_APP % "public static String c_go() { ENV return String.valueOf(java.util.List.of(new S())); }"},
                "export class S { toString(): string { FS return \"s\"; } }\nexport function c_go(): string { ENV return `${[new S()]}`; }\n",
                "struct S: CustomStringConvertible { var description: String { FS\n    return \"s\" } }\n"
                "public func c_go() -> String {\n  ENV\n  return \"\\([S()])\"\n}\n")


def _hk_iter_local(lang):
    return _one(lang,
                "pub struct It(u8);\nimpl Iterator for It { type Item = u8; fn next(&mut self) -> Option<u8> { FS None } }\n"
                "pub fn c_go() { ENV for _x in It(0) {} }\n",
                {"It": "package app;\npublic class It implements Iterable<Integer> { public java.util.Iterator<Integer> iterator() "
                       "{ FS return java.util.Collections.emptyIterator(); } }\n",
                 "App": JV_APP % "public static void c_go() { ENV for (Integer x : new It()) { } }"},
                "export class It { [Symbol.iterator](): Iterator<number> { FS return [][Symbol.iterator](); } }\n"
                "export function c_go(): void { ENV for (const _x of new It()) { } }\n",
                "struct It: Sequence, IteratorProtocol { mutating func next() -> Int? { FS\n    return nil } }\n"
                "public func c_go() {\n  ENV\n  for _ in It() { }\n}\n")


def _hk_callback(lang):
    return _one(lang,
                "fn eff(_x: &u8) { FS }\npub fn c_go() { ENV [1u8].iter().for_each(eff); }\n",
                {"App": JV_APP % "static void eff(Integer x) { FS } public static void c_go() { ENV java.util.List.of(1).forEach(App::eff); }"},
                "function eff(_x: number): void { FS }\nexport function c_go(): void { ENV [1].forEach(eff); }\n",
                "func eff(_ x: Int) { FS }\npublic func c_go() {\n  ENV\n  [1].forEach(eff)\n}\n")


def _op_local(lang):
    return _one(lang,
                "pub struct V(u8);\nimpl std::ops::Add for V { type Output = V; fn add(self, _o: V) -> V { FS V(0) } }\n"
                "pub fn c_go() { ENV let _v = V(1) + V(2); }\n",
                "EXCL:Java has no user-defined operators (string `+` is the formatting hook, hk_fmt_local)",
                "EXCL:TypeScript has no operator overloading (`+`/`==` coercion through valueOf is an implicit hook, R1248)",
                "struct V { let x: Int\n  static func + (a: V, b: V) -> V { FS\n    return a } }\n"
                "public func c_go() {\n  ENV\n  _ = V(x: 1) + V(x: 2)\n}\n")


def _ut_fmt_abstraction(lang):
    return _one(lang,
                RS_FMT + "pub trait Tr: fmt::Display {}\npub struct S;\nimpl fmt::Display for S { fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result { FS write!(f, \"s\") } }\n"
                "impl Tr for S {}\npub fn c_go(x: &dyn Tr) -> String { ENV format!(\"{}\", x) }\n",
                {"I": "package app;\npublic interface I { int k(); }\n",
                 "S": "package app;\npublic class S implements I { public int k() { return 1; } public String toString() { FS return \"s\"; } }\n",
                 "App": JV_APP % "public static String c_go(I i) { ENV return \"\" + i; }"},
                "export interface I { k(): number; }\nexport class S implements I { k(): number { return 1; } toString(): string { FS return \"s\"; } }\n"
                "export function c_go(i: I): string { ENV return `${i}`; }\n",
                "public protocol P { func k() -> Int }\nstruct S: P, CustomStringConvertible { func k() -> Int { 1 }\n  var description: String { FS\n    return \"s\" } }\n"
                "public func c_go(_ p: any P) -> String {\n  ENV\n  return \"\\(p)\"\n}\n")


def _inv_unchained(lang):
    if lang == "rust":
        return {"pkgs": {"dep": ([], "pub fn work() -> i32 { FS 1 }\n"),
                         "app": (["dep"], "pub fn c_go() -> i32 { ENV dep::work() }\n")}, "chain": []}
    if lang == "java":
        return {"pkgs": {"dep": ([], {"Work": "package dep;\npublic class Work { public static int work() { FS return 1; } }\n"}),
                         "app": (["dep"], {"App": JV_APP % "public static int c_go() { ENV return dep.Work.work(); }"})}, "chain": []}
    if lang == "ts":
        return {"pkgs": {"dep": ([], "export function work(): number { FS return 1; }\n"),
                         "app": (["dep"], 'import { work } from "dep";\nexport function c_go(): number { ENV return work(); }\n')}, "chain": []}
    return {"pkgs": {"dep": ([], "public func work() -> Int { FS\n  return 1 }\n"),
                     "app": (["dep"], "import Dep\npublic func c_go() -> Int {\n  ENV\n  return work()\n}\n")}, "chain": []}


def _r764(lang):
    """own: the abstraction + an EFFECTFUL implementor, NEVER chained. pimpl: a PURE implementor of own's abstraction,
    chained. app: dispatches on own's abstraction. The `pure` arm doctors pimpl's report with own's union entry
    (spelling from own's own report) made pure-only — the entry R613/R609-style publication would add."""
    if lang == "rust":
        return {"pkgs": {"own": ([], "pub trait Iface { fn m(&self) -> i32; }\npub struct OwnImpl;\nimpl Iface for OwnImpl { fn m(&self) -> i32 { FS 1 } }\n"),
                         "pimpl": (["own"], "use own::Iface;\npub struct PImpl;\nimpl Iface for PImpl { fn m(&self) -> i32 { 2 } }\n"),
                         "app": (["own", "pimpl"], "use own::Iface;\npub fn c_go(i: &dyn Iface) -> i32 { ENV i.m() }\n"
                                                   "pub fn c_mk() -> pimpl::PImpl { pimpl::PImpl }\n")},
                "chain": ["pimpl"], "doctor": "own"}
    if lang == "java":
        return {"pkgs": {"own": ([], {"Iface": "package own;\npublic interface Iface { int m(); }\n",
                                      "OwnImpl": "package own;\npublic class OwnImpl implements Iface { public int m() { FS return 1; } }\n"}),
                         "pimpl": (["own"], {"PImpl": "package pimpl;\npublic class PImpl implements own.Iface { public int m() { return 2; } }\n"}),
                         "app": (["own", "pimpl"], {"App": JV_APP % ("public static int c_go(own.Iface i) { ENV return i.m(); } "
                                                                     "public static Object c_mk() { return new pimpl.PImpl(); }")})},
                "chain": ["pimpl"], "doctor": "own"}
    if lang == "ts":
        return {"pkgs": {"own": ([], "export interface Iface { m(): number; }\nexport class OwnImpl implements Iface { m(): number { FS return 1; } }\n"),
                         "pimpl": (["own"], 'import { type Iface } from "own";\nexport class PImpl implements Iface { m(): number { return 2; } }\n'),
                         "app": (["own", "pimpl"], 'import { type Iface } from "own";\nimport { PImpl } from "pimpl";\n'
                                                   "export function c_go(i: Iface): number { ENV return i.m(); }\n"
                                                   "export function c_mk(): PImpl { return new PImpl(); }\n")},
                "chain": ["pimpl"], "doctor": "own"}
    return {"pkgs": {"own": ([], "public protocol Iface { func m() -> Int }\npublic struct OwnImpl: Iface { public init() {}\n  public func m() -> Int { FS\n    return 1 } }\n"),
                     "pimpl": (["own"], "import Own\npublic struct PImpl: Iface { public init() {}\n  public func m() -> Int { 2 } }\n"),
                     "app": (["own", "pimpl"], "import Own\nimport Pimpl\npublic func c_go(_ i: any Iface) -> Int {\n  ENV\n  return i.m()\n}\n"
                                               "public func c_mk() -> PImpl { PImpl() }\n")},
            "chain": ["pimpl"], "doctor": "own"}


NS = "deny Fs Unknown"   # "not silent": the effect OR a disclosure
CELLS = [
    # id, taxonomy coordinates, mode, want, builder, why
    ("ex_local_one", "explicit · same package · 1 · open · none", "assert", {"deny Env": 1, "deny Fs": 1}, _ex_local(1, 0),
     "REFERENCE: explicit dispatch over a local abstraction with one effectful implementor charges (bounded CHA)"),
    ("ex_local_bound", "explicit · same package · past bound (1 effectful + 12 pure) · open · none", "assert",
     {"deny Env": 1, NS: 1}, _ex_local(1, 12),
     "past the bound the dispatch MUST read Unknown or charge — never silent purity (§4 bounded-CHA)"),
    ("ex_local_pure", "explicit · same package · pure-only (3) · open · none", "assert", {"deny Env": 1, "deny Fs": 0},
     _ex_local(0, 3), "CONTROL: every implementor pure — a charged Fs is a FABRICATION"),
    ("wx_consumer_impl", "explicit · consumer-of-dependency · 1 · open · chained, key published", "assert",
     {"deny Env": 1, "deny Fs": 1}, _wx_consumer_impl,
     "the dependency dispatches, the consumer supplies the implementor: the chained consumer MUST carry it (§4 ⟨0.39⟩)"),
    ("wx_concrete_subclass", "explicit · consumer-of-dependency · 1 · open class · chained", "assert",
     {"deny Env": 1, "deny Fs": 1}, _wx_concrete_subclass,
     "a consumer SUBCLASS overriding a dependency class's member is an implementor (§4 ⟨0.39⟩ subclass sentence)"),
    ("wx_unrelated_override", "explicit · consumer-of-dependency · closed receiver, effectful `m` on an UNRELATED class · chained",
     "control", {"deny Env": 1, "deny Fs": 0}, _wx_override("unrelated"),
     "CONTROL: a class that is not a subtype of the key's abstraction is not an implementor of it — joining it by "
     "member NAME is a FABRICATION (executed: `Other.m` never runs)"),
    ("wx_sibling_override", "explicit · consumer-of-dependency · closed receiver, effectful `m` on a SIBLING subclass · chained",
     "rcontrol", {"deny Env": 1, "deny Fs": 0}, _wx_override("sibling"),
     "RECORDED CONTROL: executed CLEAN, but ⟨0.39⟩ obligation 3 unions PER KEY, not per call-site receiver subtree"),
    ("wx_heldvalue_sibling", "explicit · consumer-of-dependency · dispatch on a HELD VALUE (same key as a self-dispatch) · sibling runs · chained",
     "assert", {"deny Env": 1, "deny Fs": 1}, _wx_heldvalue_sibling,
     "the sibling override RUNS (executed); the wire key is byte-identical to wx_sibling_override's, so the per-key "
     "union MUST charge it — a consumer that narrowed by its own call-site receiver would be silent (§4 ⟨0.39⟩ obl. 3)"),
    ("wx_exact_producer", "explicit · chained dependency's own · exact (final/closed) receiver · consumer subclass of the base",
     "control", {"deny Env": 1, "deny Fs": 0}, _wx_exact_producer,
     "CONTROL: a dispatch on a CLOSED receiver has one target; the consumer's subclass of the base cannot run there — "
     "a charged Fs is a FABRICATION (executed)"),
    ("cb_stored_not_run", "callback look-alike · same package · function value stored, never invoked",
     "control", {"deny Env": 1, "deny Fs": 0}, _cb_stored_not_run,
     "CONTROL: creating and storing a function value runs nothing — a charged Fs is a FABRICATION (executed)"),
    ("hk_fmt_local", "implicit hook (formatting) · same package · 1 · closed concrete type · none", "assert",
     {"deny Env": 1, NS: 1}, _hk_fmt_local,
     "formatting a LOCAL concrete type runs a user body; the conventionally-pure MAY covers only receivers typed by "
     "the standard-library type itself (§4 ⟨0.40⟩), so this is not licensed silence"),
    ("ut_fmt_abstraction", "recognised-but-untyped · same package · 1 · open abstraction lacking the hook member", "assert",
     {"deny Env": 1, NS: 1}, _ut_fmt_abstraction,
     "formatting on a receiver typed by the package's OWN abstraction is a dispatch through it (§4 ⟨0.40⟩) — "
     "resolve to the implementors or disclose"),
    ("op_local", "operator · same package · 1 · closed value type · none", "assert", {"deny Env": 1, NS: 1}, _op_local,
     "a user operator is a resolved call to a user body"),
    ("hk_fmt_container", "implicit hook (formatting) through a platform container · same package · 1", "record",
     {"deny Env": 1, NS: 1}, _hk_fmt_container,
     "OPTION-DEPENDENT: the receiver is a standard-library type, which the conventionally-pure MAY covers today; "
     "site-clause option A asserts it, option B does not"),
    ("hk_iter_local", "implicit hook (iteration) · same package · 1", "record", {"deny Env": 1, NS: 1}, _hk_iter_local,
     "OPTION-DEPENDENT: today an unmodelled stdlib iterator protocol MAY stay silent as a documented named miss; "
     "both site-clause options assert it"),
    ("hk_callback", "callback (platform runs a named function value) · same package · 1", "record",
     {"deny Env": 1, NS: 1}, _hk_callback,
     "OPTION-DEPENDENT: the callback class — both site-clause options assert it; today a named miss MAY cover it"),
    ("inv_unchained", "explicit · dependency NOT chained · 1 · `invisible`-only", "ledger", {"deny Env": 1}, _inv_unchained,
     "the unchained package MUST be named in the row's ledger (or the row must disclose Unknown); `deny Fs` reads 0 "
     "on the scan route BY DESIGN and is recorded, which is why every lane's 'silent' count excludes this cell"),
    ("r764", "explicit · owner unchained, pure implementor chained · pure-only union · wire", "r764", {"deny Env": 1},
     _r764, "a newly published or pure-only union must not delete the unchained owner's disclosure (R764)"),
]

# (cell, engine) -> the row it rests on. MEASURED 2026-10-25 against the engines' main checkouts at v0.40.16 (see
# the run.sh NOTE). A passing xfail is a FAILURE.
XFAIL = {
    # Round-2 CONTROLS (CLEAN by execution; ~/candor-handoff/calltarget-round2/spec/exec-*.json). MEASURED 2026-10-25
    # against the engines' main checkouts at v0.40.17. Each is a FABRICATION: `deny Fs` exits 1 over a program that
    # performs no Fs. wx_unrelated_override and wx_exact_producer pass on all four engines.
    ("cb_stored_not_run", "java"):
        "R1442 — FABRICATED: the method reference `App::eff` stored in `H` is charged at creation though never run",
    ("cb_stored_not_run", "swift"):
        "R1447 — FABRICATED: the function reference `eff` passed as an ARGUMENT to `H(r:)` is edged as a call (the "
        "fn-reference argument arm that also makes hk_callback charge), though `H` only stores it",
    ("wx_heldvalue_sibling", "java"):
        "R1317 — SILENT: `Base.walk` dispatches `other.visit()` on a public CONCRETE non-final dependency class and names "
        "no member, so the consumer's `Right.visit` that RUNS (executed) never joins",
    ("wx_heldvalue_sibling", "ts"):
        "R1417 — SILENT: `Base.walk`'s row is [] with no dispatchesOn for the concrete-class member; `Right.visit` RUNS "
        "(executed)",
    ("wx_concrete_subclass", "java"):
        "R1317 — SILENT: a dispatch on a public CONCRETE non-final dependency class is not named (obligation 1), so the "
        "consumer subclass's override never joins; executed (the override runs)",
    ("wx_concrete_subclass", "ts"):
        "R1417 — SILENT: the dependency row is [] with no dispatchesOn for a concrete-class member (T7); executed",
    ("r764", "ts"):
        "R764 — DIR=NOTSILENT at HEAD (no ts producer publishes a pure-only entry today): with the entry doctored in, "
        "chaining deletes the unchained owner's invisible and leaves the row silent",
}

# (control cell, engine) -> the row whose SILENCE makes the control's positive twin silent, so the control passes
# VACUOUSLY there until that row is fixed — which is exactly when the control starts to bite (FABLE-REVIEW §3.2: the
# negative cells must exist BEFORE the key ships). MEASURED 2026-10-25 on v0.40.17; the twin's effect EXECUTED. A twin
# listed here that reaches the caller is a FAILURE (retire the line with the row); a silent twin NOT listed is a FAILURE.
TWIN_SILENT = {
    ("wx_unrelated_override", "java"):
        "R1317 — the dependency's `Base.run` dispatches `this.m()` on a public concrete non-final class and names no "
        "member, so the consumer override `Left.m` that runs is never joined (wx_concrete_subclass's xfail)",
    ("wx_unrelated_override", "ts"):
        "R1417 — `Base.run`'s row is [] with no dispatchesOn for the concrete-class member (wx_concrete_subclass's xfail)",
}

# ------------------------------------------------------------------------------------------------- rendering
def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


def _subst(lang, text, fault):
    fs = "" if fault else _fx(lang, "fs")
    return text.replace("FS", fs + ("" if lang == "swift" else " ") if fs else "").replace("ENV", _fx(lang, "env") + ("" if lang == "swift" else " "))


SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def materialise(lang, root, spec, fault):
    """Returns {name: package dir}. Java compiles every class together, then splits per package directory."""
    pk = spec["pkgs"]
    dirs = {}
    if lang == "rust":
        cargo = '[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n'
        for name, (deps, text) in pk.items():
            d = os.path.join(root, name)
            toml = cargo % name + ("\n[dependencies]\n" + "".join('%s={path="../%s"}\n' % (x, x) for x in deps) if deps else "")
            _w(os.path.join(d, "Cargo.toml"), toml)
            _w(os.path.join(d, "src", "lib.rs"), "#![allow(unused)]\n" + _subst(lang, text, fault))
            dirs[name] = d
        return dirs
    if lang == "ts":
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        for name, (deps, text) in pk.items():
            d = os.path.join(root, name)
            dj = ',"dependencies":{%s}' % ",".join('"%s":"file:../%s"' % (x, x) for x in deps) if deps else ""
            _w(os.path.join(d, "package.json"), '{"name":"%s","version":"0.0.0","main":"src/index.ts"%s}\n' % (name, dj))
            _w(os.path.join(d, "src", "index.ts"), 'import * as fsm from "node:fs";\n' + _subst(lang, text, fault))
            for x in deps:
                _link(os.path.join(d, "node_modules", x), os.path.join(root, x))
            if os.path.isdir(types):
                _link(os.path.join(d, "node_modules", "@types"), types)
            dirs[name] = d
        return dirs
    if lang == "swift":
        mod = lambda n: n[0].upper() + n[1:]   # noqa: E731
        for name, (deps, text) in pk.items():
            d = os.path.join(root, name)
            _w(os.path.join(d, "Package.swift"), SW_MANIFEST % dict(
                mod=mod(name), deps=", ".join('.package(path: "../%s")' % x for x in deps),
                prods=", ".join('.product(name: "%s", package: "%s")' % (mod(x), x) for x in deps)))
            _w(os.path.join(d, "Sources", mod(name), "lib.swift"), "import Foundation\n" + _subst(lang, text, fault))
            dirs[name] = d
        return dirs
    src = os.path.join(root, "src")
    for name, (deps, classes) in pk.items():
        for cn, text in classes.items():
            _w(os.path.join(src, name, cn + ".java"), _subst(lang, text, fault))
    cls = os.path.join(root, "cls")
    os.makedirs(cls, exist_ok=True)
    srcs = sorted(os.path.join(d, f) for d, _x, fs in os.walk(src) for f in fs if f.endswith(".java"))
    c = gd.run(["javac", "-nowarn", "-d", cls] + srcs)
    if c.returncode != 0:
        raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
    for name in pk:
        d = os.path.join(root, "d_" + name)
        shutil.copytree(os.path.join(cls, name), os.path.join(d, name), dirs_exist_ok=True)
        dirs[name] = d
    return dirs


# ------------------------------------------------------------------------------------------------- judging
def gate(scanner, pkgdir, deps, policy_path):
    out = os.path.join(os.path.dirname(pkgdir.rstrip(os.sep)), "gate.report.json")
    scanner._clear(pkgdir, out)
    e = dict(os.environ, CANDOR_POLICY=policy_path)
    if deps:
        e["CANDOR_DEPS"] = " ".join(deps)
    else:
        e.pop("CANDOR_DEPS", None)
    return gd.run(scanner._argv(pkgdir, out), cwd=scanner._cwd(pkgdir), env=e).returncode


def _leaf(name):
    return (name or "").replace("::", ".").replace("#", ".").split(".")[-1].split("(")[0]


def _row(report, leaf):
    rows = [f for f in (report.get("functions") or []) if _leaf(f.get("fn")) == leaf and not f.get("interfaceUnion")]
    return rows[0] if rows else None


def disclosure(row):
    """What the row says about the effect: concrete Fs, Unknown, or a ledger entry. Empty = silent."""
    if row is None:
        return set()
    inf = set(row.get("inferred") or [])
    d = set()
    if "Fs" in inf:
        d.add("Fs")
    if "Unknown" in inf:
        d.add("Unknown")
    for x in row.get("invisible") or []:
        d.add("invisible:" + (x if isinstance(x, str) else json.dumps(x, sort_keys=True)))
    return d


def scan_set(scanner, dirs, spec, ws_cell, doctor=None):
    """Scan every chained producer (and the doctor's owner, for its key spelling), then the app. Returns
    (app_dir, dep_report_paths, note) or raises RuntimeError."""
    reports = {}
    order = list(spec["pkgs"])
    for name in order:
        if name == "app":
            continue
        if name not in spec["chain"] and name != spec.get("doctor"):
            continue
        deps = [reports[d] for d in spec["pkgs"][name][0] if d in reports and d in spec["chain"]]
        r = scanner.scan(dirs[name], deps=deps)
        if not r.produced:
            raise RuntimeError("%s: producer scan produced no report (rc=%d) %s" % (name, r.rc, r.note))
        keep = os.path.join(ws_cell, "%s.report.json" % name)
        shutil.copy(r.report, keep)
        reports[name] = keep
    note = ""
    if doctor:
        own = json.load(open(reports[spec["doctor"]]))
        ent = [f for f in own.get("functions") or [] if f.get("interfaceUnion") and _leaf(f.get("fn")) == "m"]
        if not ent:
            raise RuntimeError("doctor: the owner's own report publishes no union entry for Iface.m — no spelling to reuse")
        e = dict(ent[0])
        for k in list(e):
            if k not in ("fn", "hash", "loc", "interfaceUnion", "ns"):
                e.pop(k)
        e["inferred"] = [] if doctor == "pure" else ["Fs"]
        prod = spec["chain"][0]
        pr = json.load(open(reports[prod]))
        fns = [f for f in pr.get("functions") or [] if f.get("fn") != e["fn"]]
        fns.append(e)
        pr["functions"] = fns
        doc = os.path.join(ws_cell, "%s.doctored-%s.report.json" % (prod, doctor))
        with open(doc, "w") as f:
            json.dump(pr, f, indent=1)
        reports[prod] = doc
        note = "doctored %s: %s %s" % (prod, e.get("fn"), e["inferred"])
    return [reports[n] for n in spec["chain"]], note


def judge_policies(scanner, app, deps, row, wants, ws_cell):
    got, bad = {}, []
    for i, (pol, want) in enumerate(sorted(wants.items())):
        pp = os.path.join(ws_cell, "p%d.policy" % i)
        with open(pp, "w") as f:
            f.write("%s %s\n" % (pol, row["fn"]))
        rc = gate(scanner, app, deps, pp)
        got[pol] = rc
        if want is not None and rc != want:
            bad.append("`%s` exit %d want %d" % (pol, rc, want))
    return got, bad


def run_cell(lang, scanner, ws, cid, mode, wants, builder):
    spec = builder(lang)
    if isinstance(spec, str):
        return ("EXCLUDED", spec)
    fault = bool(FAULT) and cid == "ex_local_one"
    arms = ("base", "pure", "fx") if mode == "r764" else ("base", "twin") if mode in ("control", "rcontrol") else ("base",)
    out = {}
    for arm in arms:
        wsc = os.path.join(ws, lang, cid, arm)
        os.makedirs(wsc, exist_ok=True)
        aspec = builder(lang, twin=True) if arm == "twin" else spec
        dirs = materialise(lang, os.path.join(wsc, "src"), aspec, fault)
        deps, note = scan_set(scanner, dirs, aspec, wsc, doctor=(arm if arm in ("pure", "fx") else None))
        r = scanner.scan(dirs["app"], deps=deps)
        if not r.produced:
            raise RuntimeError("%s/%s: consumer scan produced no report (rc=%d) %s" % (cid, arm, r.rc, r.note))
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            raise RuntimeError("%s/%s: analyzed.count is 0 — a hollow report judges nothing" % (cid, arm))
        row = _row(rep, "c_go")
        if row is None:
            out[arm] = (False, "c_go ABSENT from functions[] — the Env carrier is missing", {}, set(), note)
            continue
        all_w = dict(wants)
        for extra in ("deny Fs", NS):
            all_w.setdefault(extra, None)
        if mode not in ("assert", "control") or arm == "twin":   # rcontrol: scored nowhere
            all_w = {k: (v if k == "deny Env" else None) for k, v in all_w.items()}
        got, bad = judge_policies(scanner, dirs["app"], deps, row, all_w, wsc)
        out[arm] = (not bad, "; ".join(bad), got, disclosure(row), note)
    return ("RAN", out)


def verdict(mode, res, key=None):
    """(ok, detail) for a scored mode; (None, detail) for record."""
    def fmt(arm, v):
        ok, bad, got, disc, note = v
        g = " ".join("[%s]=%s" % (p, c) for p, c in sorted(got.items()))
        return "%s{%s}%s%s" % ("" if arm == "base" else arm + ":", ",".join(sorted(disc)) or "silent", " " + g if g else "",
                               (" — " + bad) if bad else "") + ((" (" + note + ")") if note else "")
    if mode == "r764":
        b, p, x = res["base"], res["pure"], res["fx"]
        detail = fmt("base", b) + " | " + fmt("pure", p) + " | " + fmt("fx", x)
        ok = b[0] and p[0] and bool(b[3]) and bool(p[3])
        if b[3] and not p[3]:
            detail += " — the pure-only union DELETED the disclosure"
        elif not b[3]:
            detail += " — the base arm is already silent (the owner's absence is not disclosed at all)"
        # The fx arm is the CONTROL that the doctored entry REACHES the consumer: the same entry carrying Fs must
        # charge (§4 ⟨0.39⟩ obligation 3). Without it a passing `pure` arm may only mean the entry was never read.
        if "Fs" not in x[3]:
            detail += " — CONTROL: the doctored entry carrying Fs did not charge, so this engine never joins it and the pure arm's pass is VACUOUS (recorded)"
        return ok, detail
    if mode in ("control", "rcontrol"):
        b, tw = res["base"], res["twin"]
        detail = fmt("base", b) + " | " + fmt("twin", tw)
        if mode == "rcontrol":
            return None, detail + (" — base CHARGES the sibling (the SPEC-required per-key union; R1436/R1420 (a) shape)"
                                   if "Fs" in b[3] else "") + (" — twin SILENT" if not tw[3] else "")
        ok = b[0]
        silent_twin = not tw[3]
        if silent_twin and key in TWIN_SILENT:
            detail += " — VACUOUS on this engine: the positive twin is silent too (%s)" % TWIN_SILENT[key]
        elif silent_twin:
            ok = False
            detail += " — the POSITIVE TWIN (effect executed) is SILENT: the control cannot fail here, and the twin is a silence"
        elif key in TWIN_SILENT:
            ok = False
            detail += " — TWIN_SILENT is STALE: the twin now reaches the caller; retire %s" % (key,)
        return ok, detail
    v = res["base"]
    detail = fmt("base", v)
    if mode == "record":
        return None, detail
    if mode == "ledger":
        ok = v[0] and bool(v[3])
        return ok, detail + ("" if v[3] else " — no ledger and no Unknown: the unchained package is not disclosed")
    return v[0], detail


def main():
    print("=" * 100)
    print("CALL-TARGET TAXONOMY (PART 104, skeleton) — one sample cell per class, four-way, plus the R764 cell")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — ex_local_one's implementor is rendered without its Fs, so the")
        print("       REFERENCE cell, which every engine passes, must go red.")
    only = [sys.argv[sys.argv.index("--engine") + 1]] if "--engine" in sys.argv[1:] else []
    ws = tempfile.mkdtemp(prefix="candor-part104-")
    bad = stale = live = 0
    for lang in ENGINES:
        if only and lang not in only:
            continue
        scanner = sa.SCANNERS[lang]()
        if not scanner.available:
            print("  %-6s -> SKIP (%s)" % (lang, scanner.err))
            continue
        live += 1
        for cid, coord, mode, wants, builder, why in CELLS:
            key = (cid, lang)
            try:
                kind, res = run_cell(lang, scanner, ws, cid, mode, wants, builder)
            except RuntimeError as e:
                print("  BROKEN %-20s %-6s %s" % (cid, lang, e))
                bad += 1
                continue
            if kind == "EXCLUDED":
                print("  excl  %-20s %-6s %s" % (cid, lang, res))
                continue
            ok, detail = verdict(mode, res, key)
            if ok is None:
                print("  rec   %-20s %-6s %s  [%s]" % (cid, lang, detail, why.split(":")[0]))
            elif ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-20s %-6s — expectation is STALE: %s" % (cid, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-20s %-6s %s" % (cid, lang, detail))
            elif key in XFAIL:
                print("  xfail %-20s %-6s %s  [%s]" % (cid, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-20s %-6s %s  [%s]" % (cid, lang, detail, why))
                bad += 1
    shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("CALL-TARGET: no engine available — NOT a pass")
        return 2
    if stale:
        print("CALL-TARGET: %d xfail arm(s) PASSED — retire them in the same commit as the engine fix." % stale)
    if bad:
        print("CALL-TARGET: %d cell(s) wrong — see SPEC §4 (bounded-CHA, ⟨0.39⟩ chained consumer, ⟨0.40⟩ receiver type)" % bad)
    if not bad and not stale:
        print("CALL-TARGET: OK — every reference charges, every control stays pure, every scored defect cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
