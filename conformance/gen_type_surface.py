#!/usr/bin/env python3
"""PART 95 — DECLARED TYPES AND THE DEPENDENCY'S OWN HIERARCHY, FOR RESOLUTION (SPEC §2 ⟨0.40⟩). R843.

A chained consumer that types receivers FROM SOURCE (candor-scan, candor-swift) meets a hop into a
dependency whose type it cannot read off the consumer's own text:

    dep:  public final class Wrong { public static let shared: Other = Other();  func ping() { Fs } }
          public final class Other { func ping() { Env } }
    app:  func r1_static() { Wrong.shared.ping() }      -- executed: the program reads the ENVIRONMENT

Swift's convention guess types `Wrong.shared` as a `Wrong` and charges `[Fs]`; `deny Env` and
`deny Env Unknown` both exit 0 (SOUNDNESS R831). Rust discloses the hop as `Unknown` (R856/R857) and so
never charges the `Env` either. No report carries the fact that would settle it — the DECLARED type of
the hop — and ⟨0.40⟩ adds it: `typeSurface.holds` (a member/static/top-level value -> its declared type),
`typeSurface.types` (every declared type's KIND and complete direct supertypes, as a MANIFEST) and
`typeSurface.adds` (conformances the package adds to FOREIGN types).

THE RUNG IS PURE RESOLUTION, and this part is written to that shape:
  * a hit ADDS the resolved target and KEEPS whatever the consumer already charged (removing a guessed
    candidate is an EXCLUSION, a separate later rung);
  * every miss or degraded case keeps the guess and ADDS `Unknown` — an older producer, a malformed
    surface, a stale or judged-nothing report, and a `holds` hit followed by a member miss (§2 ⟨0.23⟩'s
    miss rule, which this rung inherits word for word);
  * a held/returned CLASS type dispatches as a typed receiver of it does under ⟨0.39⟩: the overrides of
    every subtype visible to the consumer join it (PART 94 / R867 is the typed-receiver half of this).

THE ARMS. Positive arms (r*) need the PRODUCER to publish the surface and the CONSUMER to read it, so
they are END-TO-END: a real producer scan of the dependency, a real chained consumer scan, and the
engine's own gate. Degraded arms (o*, u1, g1) DOCTOR the producer's own report — strip, malform, re-
version or empty it — so the consumer's answer is measured over a surface it must not trust, with the
consumer's source byte-identical. Producer arms (p*, w*) read the dependency report alone.

  r1_static     `Wrong.shared.ping()`, `shared: Other`                 -> Env      (R831; rust R856)
  r2_bound      `let s = Wrong.shared; s.ping()`                       -> Env      (R617)
  r3_property   `n.parent.ping()`, `parent: Other`                     -> Env      (rust R857)
  r4_inherited  `Holder4.shared.tok4()`, `shared: Mid4`, `Mid4: Grand4` -> Env     (walk `supers`)
  r5_refined    `(t: any PSub).pTok()`, `PSub: PBase`, pTok on PBase   -> Env      (R859/R865; rust R858)
  r6_proto_ret  `mkP().run()`, `mkP() -> any PSvc`                     -> Env      (R864; ⟨0.39⟩ union)
  r7a_holds_open `HolderO.shared.m()`, `shared: BaseO = SubO()`        -> Env      (override union)
  r7b_returns_open `let b = mkO(); b.m()`, `mkO() -> BaseO`            -> Env      (passes since R867)
  r8_adds       `Tok().pTok()`, Tok in a THIRD package, `extension Tok: PBase` in dep -> Env (`adds`)

  c1_convention `Client.shared.fetch()`, `shared: Client` (the convention RIGHT)   -> Env     (R826)
  c2_final/c2_value/c2_enum/c2_open   a right-typed singleton whose `m` reads Fs, while an UNRELATED
                `SubO.m`/`SubB.n` reads Env -> `deny Env` 0: the override union must add nothing it
                cannot reach (c2_open: `OpenB`'s subclass overrides `n`, never `m`)
  c3_collision  `Dep.Client.shared.fetch()` in a file importing BOTH `Dep` and `DepB`, each declaring
                `Client` — DepB's reads Fs and Dep's Env -> `deny Env` 1: union, never pick
  c4_cross      r1's consumer text BYTE-IDENTICAL, over a dependency where `shared: Wrong` (the
                convention right) -> `deny Env` 0. The one-variable cross of r1: only the declared type
                moves, so r1's answer is decided by the declared type and nothing else
  c5_factory    `Client.make().fetch()` — ⟨0.23⟩'s `returns` (R832), pinned unchanged -> Env

  o1_old        r1 over the dependency report with `typeSurface.{holds,types,adds}` STRIPPED -> the
                additive hedge: `deny Env Unknown` 1
  o1b_old_right c1 over the stripped report -> `deny Env` 1 (the guess KEPT) AND `deny Unknown` 1 (ADDED)
  o2_member_miss `Wrong.shared.quiet()`, `Other.quiet` PURE so absent from the report -> a holds HIT
                then a member MISS: `deny Unknown` 1 (§2 ⟨0.23⟩ "a miss on the entry lookup that
                follows a hit")
  o3_malformed  r1 over a report whose `holds`/`types`/`adds` are the wrong JSON type -> as o1
                (a refusal, exit 2, is also accepted — it fails closed)
  o4_stale      r1 over a report whose `candor.version` no longer matches the consumer -> as o1 (§2.1)
  o5_nothing    r1 over a report that judged nothing (`functions` [], `analyzed.count` 0) but still
                carries the surface -> as o1 (PART 26's coverage door; the surface must not reopen it)
  u1_bound      `Wrong2.shared2.q()`, `shared2: Quiet`, a type with ONLY pure members. The consumer row
                must be BYTE-IDENTICAL over a report that publishes `holds` for `shared2` and one that
                does not (a bounded producer may omit it), and must disclose (`deny Unknown` 1)
  g1_keep_guess c1 over a report whose `holds` for `Client.shared` is REWRITTEN to name `Other` (a WRONG
                declared type) -> `deny Env` 1: the guess `Client.fetch` is kept. A consumer that SWAPS
                the guess for the surface's answer fails here — the replacement is rung B, not this one

  p1_holds      the producer publishes `holds` for `Wrong.shared` naming `Other`, and lists `holds` in
                `resolves`
  p2_types      the producer publishes `types` for `Mid4` with `Grand4` among its supers, and for
                `PSub` with kind `protocol` and `PBase` among its supers
  w1_macro      swift: `@AddP public final class MacT {}`, where `AddP` is an attached EXTENSION macro
                adding a conformance the parser cannot expand -> `types` MUST NOT carry `MacT`
  w2_macro      rust: `hide!(Y)` expanding to `impl Hidden for Y`, and `#[derive(Opaque)] struct Z` ->
                `types` MUST NOT carry `Y` or `Z` (a MANIFEST key is complete or absent, never short)

THE CARRIER. Every consumer function also calls the dependency's free `carrier()` (Net). `deny Net` is
asserted on every gate cell: it proves the chained report reached THIS gate run and that the scope names
the row, so no `exit 0` below can be a policy that matched nothing (the PART 94 construction).

JAVA AND TS ARE DECLARED NOT APPLICABLE, not skipped: java reads call-site descriptors from bytecode, and
ts asks the type checker, which reads the dependency's `.d.ts` — both type every hop already. Neither
engine has a consumer that guesses a dependency type, so the rung has nothing to resolve there.

THE XFAIL TABLE is keyed (arm, engine) and A PASSING XFAIL IS A FAILURE: the engine that ports the rung
reddens this part and retires its own lines in the same commit.
"""
import copy
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402
import split_arms as sa            # noqa: E402

SPEC_CLAUSES = [
    ("§2 ⟨0.40⟩", "A CONSUMER USES THE SURFACE TO ADD A RESOLUTION, NEVER TO REMOVE ONE"),
    ("§2 ⟨0.40⟩", "`types` is a MANIFEST"),
    ("§2 ⟨0.40⟩", "every miss keeps the guess and ADDS `Unknown`"),
    ("§4 ⟨0.39⟩", "\"Implementor\" in this clause includes a SUBCLASS that overrides a class's member."),
    ("§2 ⟨0.23⟩", "This holds for a miss on `returns` AND for a miss on the entry lookup that follows a `returns` hit"),
    ("§4 ⟨0.39⟩", "A mechanism that makes reports better must not make silence cheaper."),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
CAL = os.environ.get("CANDOR_PART95_CAL")
NOBUILD = os.environ.get("CANDOR_PART95_NOBUILD")
DUMP = "--dump" in sys.argv

ENGINES = ("rust", "swift")
NA = {
    "java": "bytecode carries every call site's static receiver type (the INVOKEVIRTUAL descriptor), so "
            "no hop into a dependency is ever guessed",
    "ts":   "the consumer asks the TypeScript checker, which reads the dependency's own `.d.ts` and "
            "types every hop",
}

ENV = {"swift": '_ = ProcessInfo.processInfo.environment["HOME"]', "rust": 'let _ = std::env::var("HOME");'}
FS = {"swift": '_ = FileManager.default.fileExists(atPath: "/tmp")', "rust": 'let _ = std::fs::metadata("/tmp");'}
NET = {"swift": '_ = URLSession.shared.dataTask(with: URL(string: "http://h")!)',
       "rust": 'let _ = std::net::TcpStream::connect("h:1");'}


# =====================================================================================================
# THE FIXTURE. Three packages — `base` (owns `Tok`, the FOREIGN type `adds` is about), `dep` (the
# dependency under test), `depb` (the collision twin) — and the consumer `app`. `dep` has two variants:
# "main" and "cross", which differ ONLY in the declared type of `Wrong.shared` (c4).
# =====================================================================================================
def sw_dep(variant):
    e, f, n = ENV["swift"], FS["swift"], NET["swift"]
    shared = "public static let shared: Wrong = Wrong()" if variant == "cross" \
        else "public static let shared: Other = Other()"
    # CANDOR_PROBE_FAULT empties `Client.fetch`, so c5_factory (both engines) and c1_convention (swift),
    # which pass today, cannot reach Env. CANDOR_PART95_CAL=controls puts Env INTO the bodies the c2/c4
    # controls must not charge it from, so a control that cannot fail is caught by running it.
    fetch = "" if FAULT else e
    cal = ("; " + e) if CAL == "controls" else ""
    subo = "" if FAULT else e          # the fault also empties the override r7b_returns_open must reach
    other_ping = e
    return f'''import Foundation
import Base
public func carrier() {{ {n} }}
public final class Other {{
    public init() {{}}
    public func ping() {{ {other_ping} }}
    public func quiet() {{}}
}}
public final class Wrong {{
    {shared}
    public init() {{}}
    public func ping() {{ {f} {cal} }}
    public func quiet() {{ {f} }}
}}
public final class Node {{
    public init() {{}}
    public var parent: Other = Other()
    public func ping() {{ {f} }}
}}
open class Grand4 {{
    public init() {{}}
    public func tok4() {{ {e} }}
}}
open class Mid4: Grand4 {{
    public override init() {{ super.init() }}
}}
public final class Holder4 {{
    public static let shared: Mid4 = Mid4()
    public func tok4() {{ {f} }}
}}
public protocol PBase {{}}
extension PBase {{
    public func pTok() {{ {e} }}
}}
public protocol PSub: PBase {{}}
public protocol PSvc {{ func run() }}
public final class SvcImpl: PSvc {{
    public init() {{}}
    public func run() {{ {e} }}
}}
public func mkP() -> any PSvc {{ SvcImpl() }}
open class BaseO {{
    public init() {{}}
    open func m() {{ {f} }}
}}
public final class SubO: BaseO {{
    public override init() {{ super.init() }}
    public override func m() {{ {subo} }}
}}
public final class HolderO {{
    public static let shared: BaseO = SubO()
}}
public func mkO() -> BaseO {{ SubO() }}
extension Tok: PBase {{}}
public final class Client {{
    public static let shared: Client = Client()
    public init() {{}}
    public static func make() -> Client {{ Client() }}
    public func fetch() {{ {fetch} }}
}}
public final class FinT {{
    public static let shared: FinT = FinT()
    public init() {{}}
    public func m() {{ {f} {cal} }}
}}
public struct Val {{
    public static let shared: Val = Val()
    public init() {{}}
    public func m() {{ {f} {cal} }}
}}
public enum En {{
    case a
    public static let shared: En = .a
    public func m() {{ {f} {cal} }}
}}
open class OpenB {{
    public static let shared: OpenB = OpenB()
    public init() {{}}
    open func m() {{ {f} {cal} }}
    open func n() {{}}
}}
public final class SubB: OpenB {{
    public override init() {{ super.init() }}
    public override func n() {{ {e} }}
}}
public final class Quiet {{
    public init() {{}}
    public func q() {{}}
}}
public final class Wrong2 {{
    public static let shared2: Quiet = Quiet()
    public func q() {{ {f} }}
}}
'''


SW_BASE = 'public struct Tok {\n    public init() {}\n}\n'
SW_DEPB = ('import Foundation\npublic final class Client {\n    public static let shared: Client = Client()\n'
           '    public init() {}\n    public func fetch() { %s }\n}\n' % FS["swift"])

# The consumer. r1/r2 are ALSO c4's functions (the cross), so their text must not depend on the variant.
SW_APP_A = '''import Dep
public func r1_static() { carrier(); Wrong.shared.ping() }
public func r2_bound() { carrier(); let s = Wrong.shared; s.ping() }
public func r3_property(_ n: Node) { carrier(); n.parent.ping() }
public func r4_inherited() { carrier(); Holder4.shared.tok4() }
public func r5_refined(_ t: any PSub) { carrier(); t.pTok() }
public func r6_proto_ret() { carrier(); mkP().run() }
public func r7a_holds_open() { carrier(); HolderO.shared.m() }
public func r7b_returns_open() { carrier(); let b = mkO(); b.m() }
public func c1_convention() { carrier(); Client.shared.fetch() }
public func c2_final() { carrier(); FinT.shared.m() }
public func c2_value() { carrier(); Val.shared.m() }
public func c2_enum() { carrier(); En.shared.m() }
public func c2_open() { carrier(); OpenB.shared.m() }
public func c5_factory() { carrier(); Client.make().fetch() }
public func o2_member_miss() { carrier(); Wrong.shared.quiet() }
public func u1_bound() { carrier(); Wrong2.shared2.q() }
'''
SW_APP_B = '''import Dep
import DepB
public func c3_collision() { Dep.carrier(); Dep.Client.shared.fetch() }
'''
SW_APP_C = '''import Base
import Dep
public func r8_adds() { carrier(); Tok().pTok() }
'''

SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')

# w1: an attached EXTENSION macro adds `PMac` to `MacT`. The plugin is never built — the scan is a parse,
# and the question is what the PRODUCER publishes for a type whose conformances it cannot see. `PlainT`
# is the sibling the producer CAN close, so a `types` that omits MacT is distinguishable from no `types`.
SW_W1 = '''public protocol PMac {}
@attached(extension, conformances: PMac)
public macro AddP() = #externalMacro(module: "MacImpl", type: "AddPMacro")
@AddP
public final class MacT { public init() {} }
public final class PlainT: PMac { public init() {} }
'''


def rs_dep(variant):
    e, f, n = ENV["rust"], FS["rust"], NET["rust"]
    shared = "pub static SHARED: Wrong = Wrong;" if variant == "cross" else "pub static SHARED: Other = Other;"
    fetch = "" if FAULT else e
    cal = e if CAL == "controls" else ""
    other_ping = e
    return f'''pub fn carrier() {{ {n} }}
pub struct Other;
impl Other {{
    pub fn ping(&self) {{ {other_ping} }}
    pub fn quiet(&self) {{}}
}}
pub struct Wrong;
impl Wrong {{
    pub fn ping(&self) {{ {f} {cal} }}
    pub fn quiet(&self) {{ {f} }}
}}
{shared}
pub struct Node {{ pub parent: Other }}
impl Node {{
    pub fn ping(&self) {{ {f} }}
}}
pub trait Grand4 {{
    fn tok4(&self) {{ {e} }}
}}
pub struct Mid4;
impl Grand4 for Mid4 {{}}
pub static HOLDER4: Mid4 = Mid4;
pub trait PBase {{
    fn p_tok(&self) {{ {e} }}
}}
pub trait PSub: PBase {{}}
pub trait PSvc {{
    fn run(&self);
}}
pub struct SvcImpl;
impl PSvc for SvcImpl {{
    fn run(&self) {{ {e} }}
}}
pub fn mk_p() -> Box<dyn PSvc> {{ Box::new(SvcImpl) }}
impl PBase for base::Tok {{}}
pub struct Client;
impl Client {{
    pub fn make() -> Client {{ Client }}
    pub fn fetch(&self) {{ {fetch} }}
}}
pub static CLIENT: Client = Client;
pub struct FinT;
impl FinT {{
    pub fn m(&self) {{ {f} {cal} }}
}}
pub static FIN: FinT = FinT;
pub enum En {{ A }}
impl En {{
    pub fn m(&self) {{ {f} {cal} }}
}}
pub static EN: En = En::A;
pub struct Bait;
impl Bait {{
    pub fn m(&self) {{ {e} }}
}}
pub struct Quiet;
impl Quiet {{
    pub fn q(&self) {{}}
}}
pub static SHARED2: Quiet = Quiet;
'''


RS_BASE = 'pub struct Tok;\nimpl Tok {\n    pub fn new() -> Tok { Tok }\n}\n'
RS_DEPB = 'pub struct Client;\nimpl Client {\n    pub fn fetch(&self) { %s }\n}\npub static CLIENT: Client = Client;\n' % FS["rust"]
RS_APP = '''use dep::{Grand4, Node, PBase};
#[allow(unused_imports)]
use depb::Client;
pub fn r1_static() { dep::carrier(); dep::SHARED.ping() }
pub fn r2_bound() { dep::carrier(); let s = &dep::SHARED; s.ping() }
pub fn r3_property(n: &Node) { dep::carrier(); n.parent.ping() }
pub fn r4_inherited() { dep::carrier(); dep::HOLDER4.tok4() }
pub fn r5_refined(t: &dyn dep::PSub) { dep::carrier(); t.p_tok() }
pub fn r6_proto_ret() { dep::carrier(); dep::mk_p().run() }
pub fn c2_final() { dep::carrier(); dep::FIN.m() }
pub fn c2_enum() { dep::carrier(); dep::EN.m() }
pub fn c3_collision() { dep::carrier(); dep::CLIENT.fetch() }
pub fn c5_factory() { dep::carrier(); dep::Client::make().fetch() }
pub fn o2_member_miss() { dep::carrier(); dep::SHARED.quiet() }
pub fn u1_bound() { dep::carrier(); dep::SHARED2.q() }
pub fn r8_adds() { dep::carrier(); base::Tok.p_tok() }
'''

# w2: a `macro_rules!` expansion declares a trait AND implements it for `Y`; `Z` derives an unknown trait.
# `Plain` is the sibling whose supertypes ARE visible. Never built — `Opaque` has no proc macro.
RS_W2 = '''pub trait Visible {}
macro_rules! hide {
    ($t:ident) => {
        pub trait Hidden {}
        impl Hidden for $t {}
    };
}
pub struct Y;
impl Visible for Y {}
hide!(Y);
#[derive(Opaque)]
pub struct Z;
impl Visible for Z {}
pub struct Plain;
impl Visible for Plain {}
'''


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def render(lang, root, variant):
    """Lay out base, dep, depb, app. Returns (ordered dep dirs, {name: dir}, app dir, consumer text)."""
    if lang == "swift":
        _w(os.path.join(root, "base", "Package.swift"), SW_MANIFEST % dict(mod="Base", deps="", prods=""))
        _w(os.path.join(root, "base", "Sources", "Base", "base.swift"), SW_BASE)
        _w(os.path.join(root, "dep", "Package.swift"),
           SW_MANIFEST % dict(mod="Dep", deps='.package(path: "../base")',
                              prods='.product(name: "Base", package: "base")'))
        _w(os.path.join(root, "dep", "Sources", "Dep", "dep.swift"), sw_dep(variant))
        _w(os.path.join(root, "depb", "Package.swift"), SW_MANIFEST % dict(mod="DepB", deps="", prods=""))
        _w(os.path.join(root, "depb", "Sources", "DepB", "depb.swift"), SW_DEPB)
        deps = ", ".join('.package(path: "../%s")' % d for d in ("base", "dep", "depb"))
        prods = ", ".join('.product(name: "%s", package: "%s")' % (m, d)
                          for m, d in (("Base", "base"), ("Dep", "dep"), ("DepB", "depb")))
        _w(os.path.join(root, "app", "Package.swift"), SW_MANIFEST % dict(mod="App", deps=deps, prods=prods))
        _w(os.path.join(root, "app", "Sources", "App", "a.swift"), SW_APP_A)
        _w(os.path.join(root, "app", "Sources", "App", "b.swift"), SW_APP_B)
        _w(os.path.join(root, "app", "Sources", "App", "c.swift"), SW_APP_C)
        text = SW_APP_A + SW_APP_B + SW_APP_C
    else:
        def cargo(name, deps):
            return ('[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\n' % name
                    + "".join('%s={path="../%s"}\n' % (d, d) for d in deps))
        _w(os.path.join(root, "base", "Cargo.toml"), cargo("base", []))
        _w(os.path.join(root, "base", "src", "lib.rs"), RS_BASE)
        _w(os.path.join(root, "dep", "Cargo.toml"), cargo("dep", ["base"]))
        _w(os.path.join(root, "dep", "src", "lib.rs"), rs_dep(variant))
        _w(os.path.join(root, "depb", "Cargo.toml"), cargo("depb", []))
        _w(os.path.join(root, "depb", "src", "lib.rs"), RS_DEPB)
        _w(os.path.join(root, "app", "Cargo.toml"), cargo("app", ["base", "dep", "depb"]))
        _w(os.path.join(root, "app", "src", "lib.rs"), RS_APP)
        text = RS_APP
    dirs = {d: os.path.join(root, d) for d in ("base", "dep", "depb")}
    return [dirs["base"], dirs["dep"], dirs["depb"]], dirs, os.path.join(root, "app"), text


def render_w(lang, root):
    if lang == "swift":
        _w(os.path.join(root, "Package.swift"), SW_MANIFEST % dict(mod="MacDep", deps="", prods=""))
        _w(os.path.join(root, "Sources", "MacDep", "mac.swift"), SW_W1)
    else:
        _w(os.path.join(root, "Cargo.toml"), '[package]\nname="macdep"\nversion="0.0.0"\nedition="2021"\n')
        _w(os.path.join(root, "src", "lib.rs"), RS_W2)
    return root


def build_proof(lang, app):
    if NOBUILD:
        return None
    if lang == "swift":
        r = gd.run(["swift", "build"], cwd=app)
    else:
        r = gd.run(["cargo", "build", "--offline", "-q"], cwd=app)
    if r.returncode != 0:
        return "%s build FAILED: %s" % (lang, (r.stderr or r.stdout).decode()[:400].replace("\n", " | "))
    return None




# =====================================================================================================
# THE ARMS. (id, dependency variant, doctor, consumer fn, want) where `want` maps a policy's effect text
# to the exit code(s) a conformant engine gives it; a per-engine override replaces the whole want. Every
# consumer arm ALSO asserts the carrier, `deny Net` = 1 (see the header).
# =====================================================================================================
ENV1 = {"deny Env": {1}}
ENV0 = {"deny Env": {0}}
DISCLOSE = {"deny Env Unknown": {1}}
ARMS = [
    # id                 variant  doctor        fn                 want / {engine: want}
    ("r1_static",        "main",  None,        "r1_static",        ENV1),
    ("r2_bound",         "main",  None,        "r2_bound",         ENV1),
    ("r3_property",      "main",  None,        "r3_property",      ENV1),
    ("r4_inherited",     "main",  None,        "r4_inherited",     ENV1),
    ("r5_refined",       "main",  None,        "r5_refined",       ENV1),
    ("r6_proto_ret",     "main",  None,        "r6_proto_ret",     {"swift": ENV1, "rust": DISCLOSE}),
    ("r7a_holds_open",   "main",  None,        "r7a_holds_open",   ENV1),
    ("r7b_returns_open", "main",  None,        "r7b_returns_open", ENV1),
    ("r8_adds",          "main",  None,        "r8_adds",          ENV1),
    ("c1_convention",    "main",  None,        "c1_convention",    ENV1),
    ("c2_final",         "main",  None,        "c2_final",         ENV0),
    ("c2_value",         "main",  None,        "c2_value",         ENV0),
    ("c2_enum",          "main",  None,        "c2_enum",          ENV0),
    ("c2_open",          "main",  None,        "c2_open",          ENV0),
    ("c3_collision",     "main",  None,        "c3_collision",     DISCLOSE),
    ("c4_cross",         "cross", None,        "r1_static",        ENV0),
    ("c5_factory",       "main",  None,        "c5_factory",       ENV1),
    ("o1_old",           "main",  "strip",     "r1_static",        DISCLOSE),
    ("o1b_old_right",    "main",  "strip",     "c1_convention",    {"deny Env": {1}, "deny Unknown": {1}}),
    ("o2_member_miss",   "main",  None,        "o2_member_miss",   {"deny Unknown": {1}}),
    ("o3_malformed",     "main",  "malformed", "r1_static",        {"deny Env Unknown": {1, 2}}),
    ("o4_stale",         "main",  "stale",     "r1_static",        {"deny Env Unknown": {1}, "deny Env": {0}}),
    ("o5_nothing",       "main",  "nothing",   "r1_static",        DISCLOSE),
    ("u1_bound",         "main",  "u1",        "u1_bound",         {"deny Unknown": {1}}),
    ("g1_keep_guess",    "main",  "wrongholds", "c1_convention",   ENV1),
]
# Producer-side arms — judged on the dependency report alone, never on a gate.
PRODUCER_ARMS = ("p1_holds", "p2_types", "w1_macro", "w2_macro")

# (arm, engine) -> why the arm cannot be written in that engine. Each is a DECLARED N/A, not a skip.
ARM_NA = {
    ("r7a_holds_open", "rust"): "Rust has no class inheritance — a `static` of a concrete type has exactly one body per method (PART 94's N/A)",
    ("r7b_returns_open", "rust"): "as r7a_holds_open",
    ("c1_convention", "rust"): "Rust makes no singleton-convention guess — `dep::CLIENT` is a static ITEM typed only by this rung, which is r1's shape",
    ("o1b_old_right", "rust"): "as c1_convention — there is no guess to keep",
    ("g1_keep_guess", "rust"): "as c1_convention — there is no guess for a wrong `holds` to displace",
    ("c2_value", "rust"): "rust's c2_final is already a value type (a struct) — Rust has no reference classes",
    ("c2_open", "rust"): "Rust has no open classes",
    ("w1_macro", "rust"): "w2_macro is rust's withhold arm",
    ("w2_macro", "swift"): "w1_macro is swift's withhold arm",
}

WHY = {
    "r": "RESOLUTION: the declared type (or the dependency's own hierarchy) names the real target, and the "
         "consumer must reach it",
    "c": "CONTROL: an unrelated or unreachable `Env` must not be charged, and a collision must union or "
         "disclose — never pick",
    "o": "DEGRADED: no trustworthy surface answers this hop, so the consumer keeps what it had and ADDS "
         "`Unknown`",
    "u": "BOUND EQUIVALENCE: a bounded and an unbounded producer must give the consumer the same row",
    "g": "KEEP THE GUESS: a hit ADDS a target, it never displaces one — the displacement is rung B",
    "p": "PRODUCER: the surface the consumer needs must be on the wire",
    "w": "WITHHOLD: a `types` key is complete or absent — a type whose supertypes a macro may extend is "
         "omitted, never listed short",
}

# An expectation keyed by (arm, engine). A PASSING XFAIL IS A FAILURE. A pure LITERAL on purpose:
# scripts/xfail-register-agree.py reads it with ast.literal_eval and skips any table it cannot evaluate,
# so a note built from a variable would make every line below invisible to the register check.
XFAIL = {
    ('r1_static', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r1_static', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r2_bound', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r2_bound', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r3_property', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r3_property', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r4_inherited', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r4_inherited', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r5_refined', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r5_refined', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r6_proto_ret', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r7a_holds_open', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r8_adds', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('r8_adds', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('o1_old', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (the convention guess is kept SILENTLY)',
    ('o1b_old_right', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (the convention guess is kept SILENTLY)',
    ('o2_member_miss', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (the convention guess is kept SILENTLY)',
    ('o3_malformed', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (the convention guess is kept SILENTLY)',
    ('u1_bound', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (no `holds` to vary — the equivalence cannot be constructed)',
    ('u1_bound', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (no `holds` to vary — the equivalence cannot be constructed)',
    ('g1_keep_guess', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet (no `holds` to rewrite — the arm cannot be constructed)',
    ('p1_holds', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('p1_holds', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('p2_types', 'rust'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
    ('p2_types', 'swift'): 'SOUNDNESS R843 — no engine publishes or reads `holds`/`types`/`adds` yet',
}


# A distrusted (o4) or judged-nothing (o5) dependency report takes `carrier()` down with it — §2.1
# downgrades EVERY inherited effect to `Unknown` — so `deny Net` cannot be the carrier there. Neither arm
# needs one for its `1` cells (a gate that FIRES has proved its scope bound), and o4's `deny Env` = 0 is
# carried by its own `deny Env Unknown` = 1 on the same scope, which cannot fire on a scope that binds
# nothing.
NO_CARRIER = ("o4_stale", "o5_nothing")


def want_for(arm, lang):
    w = arm[4]
    if "rust" in w or "swift" in w:
        w = w[lang]
    w = dict(w)
    if arm[0] not in NO_CARRIER:
        w["deny Net"] = {1}
    return w


# =====================================================================================================
# KEY LOOKUP, spelling-agnostic. The ⟨0.23⟩ spelling rule fixes keys in the OWNING package's namespace,
# which differs by engine (`Dep#Wrong.shared`, `dep#SHARED`). The part never spells a key itself: it
# finds the producer's own key by its last segment(s), so it cannot invent a spelling (⟨0.39⟩ obl. 2).
# =====================================================================================================
def _segs(key):
    tail = str(key).split("#", 1)[-1]
    return [s for s in re.split(r"::|\.", tail) if s]


def find_key(d, leaf, owner=None):
    if not isinstance(d, dict):
        return None
    for k in d:
        sg = _segs(k)
        if sg and sg[-1] == leaf and (owner is None or (len(sg) >= 2 and sg[-2] == owner)):
            return k
    return None


def leaf_of(v):
    sg = _segs(v)
    return sg[-1] if sg else None


SHARED = {"swift": ("shared", "Wrong"), "rust": ("SHARED", None)}
SHARED2 = {"swift": ("shared2", "Wrong2"), "rust": ("SHARED2", None)}
CLIENT = {"swift": ("shared", "Client"), "rust": ("CLIENT", None)}


def surface(rep):
    ts = rep.get("typeSurface")
    return ts if isinstance(ts, dict) else {}


# =====================================================================================================
# THE DOCTORS. Each takes the producer's own dependency report and returns (doctored, None) or
# (None, why-not-constructible). The consumer's source never moves.
# =====================================================================================================
RUNG_KEYS = ("holds", "types", "adds")


def doctor(rep, kind, lang):
    d = copy.deepcopy(rep)
    ts = surface(d)
    if kind == "strip":
        for k in RUNG_KEYS:
            ts.pop(k, None)
        if ts:
            d["typeSurface"] = ts
        else:
            d.pop("typeSurface", None)
        d["resolves"] = [r for r in d.get("resolves") or [] if r not in RUNG_KEYS]
        return d, None
    if kind == "malformed":
        ts = dict(ts)
        ts.update({"holds": 42, "types": [], "adds": "x"})
        d["typeSurface"] = ts
        d["resolves"] = sorted(set(d.get("resolves") or []) | set(RUNG_KEYS))
        return d, None
    if FAULT and kind in ("stale", "nothing"):
        # The fault makes these two doctors the IDENTITY, so the arm reads the undoctored report — which
        # proves the doctored document, not something else, is what reached the consumer (swift reddens).
        return d, None
    if kind == "stale":
        d.setdefault("candor", {})["version"] = "part95-stale-0.0.0"
        return d, None
    if kind == "nothing":
        d["functions"] = []
        d["analyzed"] = {"count": 0, "digest": "cbf29ce484222325"}
        return d, None
    if kind == "wrongholds":
        holds = ts.get("holds")
        k_client = find_key(holds, *CLIENT[lang])
        k_wrong = find_key(holds, *SHARED[lang])
        if not (k_client and k_wrong):
            return None, "the producer publishes no `holds` for Client.shared and Wrong.shared"
        holds = dict(holds)
        holds[k_client] = holds[k_wrong]     # names `Other`, which has no `fetch`
        ts = dict(ts)
        ts["holds"] = holds
        d["typeSurface"] = ts
        return d, None
    raise ValueError(kind)


def u1_pair(rep, lang):
    """(with, without) the `holds` entry for Wrong2.shared2, or (None, why). If the producer published it
    the bounded form is that entry removed; if it bounded it out, the unbounded form is synthesised from
    its OWN key for Wrong.shared by substituting the two names — the producer's spelling, never ours."""
    holds = surface(rep).get("holds")
    if not isinstance(holds, dict):
        return None, "the producer publishes no `holds`"
    leaf2, own2 = SHARED2[lang]
    k2 = find_key(holds, leaf2, own2)
    with_, without = copy.deepcopy(rep), copy.deepcopy(rep)
    if k2:
        del without["typeSurface"]["holds"][k2]
        return (with_, without), None
    k1 = find_key(holds, *SHARED[lang])
    if not k1:
        return None, "the producer publishes no `holds` for Wrong.shared to derive the spelling from"
    leaf1, own1 = SHARED[lang]
    k_new = k1.replace(own1, own2) if own1 else k1
    k_new = k_new[: len(k_new) - len(leaf1)] + leaf2
    v = holds[k1]
    with_["typeSurface"]["holds"][k_new] = v[: len(v) - len(leaf_of(v))] + "Quiet"
    return (with_, without), None


# =====================================================================================================
# THE PRODUCER JUDGES — each returns (ok, detail).
# =====================================================================================================
def judge_p1(rep, lang):
    holds = surface(rep).get("holds")
    k = find_key(holds, *SHARED[lang])
    if not k:
        return False, "no `holds` entry for Wrong.shared (holds=%s)" % ("absent" if holds is None else "present")
    if leaf_of(holds[k]) != "Other":
        return False, "`holds[%s]` = %r — the declared type is Other" % (k, holds[k])
    if "holds" not in (rep.get("resolves") or []):
        return False, "`holds` published but not listed in `resolves`"
    return True, "holds[%s] = %s" % (k, holds[k])


def _sup_leaves(entry):
    return {leaf_of(s) for s in (entry.get("supers") or [])} if isinstance(entry, dict) else set()


def judge_p2(rep, lang):
    types = surface(rep).get("types")
    if not isinstance(types, dict):
        return False, "no `types` manifest"
    mid, psub = find_key(types, "Mid4"), find_key(types, "PSub")
    bad = []
    if not mid or "Grand4" not in _sup_leaves(types[mid]):
        bad.append("Mid4 must list Grand4 among its supers (%s)" % (types.get(mid) if mid else "absent"))
    if not psub or types[psub].get("kind") != "protocol" or "PBase" not in _sup_leaves(types[psub]):
        bad.append("PSub must be kind protocol with PBase among its supers (%s)"
                   % (types.get(psub) if psub else "absent"))
    if "types" not in (rep.get("resolves") or []):
        bad.append("`types` not listed in `resolves`")
    return (not bad), ("; ".join(bad) if bad else "Mid4 -> %s, PSub -> %s" % (types[mid], types[psub]))


WITHHELD = {"swift": ("MacT",), "rust": ("Y", "Z", "Hidden")}
WITNESS = {"swift": "PlainT", "rust": "Plain"}


def inject_short(rep, lang):
    """THE CLASSIFIER-MUST-FIRE FAULT: a producer that emits what it CAN see — a short key for each type a
    macro may extend. The w arm must go red over this."""
    d = copy.deepcopy(rep)
    ts = d.setdefault("typeSurface", {})
    types = ts.setdefault("types", {})
    pkg = (d.get("package") or "MacDep")
    for name in WITHHELD[lang]:
        types["%s#%s" % (pkg, name)] = {"kind": "value" if lang == "rust" else "final", "supers": []}
    return d


def judge_w(rep, lang):
    types = surface(rep).get("types")
    if types is not None and not isinstance(types, dict):
        return False, "`types` is not an object"
    leaked = [n for n in WITHHELD[lang] if find_key(types or {}, n)]
    if leaked:
        return False, "`types` carries %s — a type a macro may extend must be OMITTED, never listed short" % leaked
    if not types:
        return True, "no `types` published — conformant by absence (VACUOUS until the producer ports)"
    wit = find_key(types, WITNESS[lang])
    return True, "withheld %s; witness %s %s" % (list(WITHHELD[lang]),
                                                  WITNESS[lang], "present" if wit else "ABSENT (note)")


# =====================================================================================================
# THE CONSUMER JUDGE — a pure function of the gate exits, so --selftest can attack it.
# =====================================================================================================
def judge_gates(want, got):
    bad = ["`%s` exit %s want %s" % (p, got.get(p), "/".join(map(str, sorted(w))))
           for p, w in sorted(want.items()) if got.get(p) not in w]
    return not bad, bad


def selftest():
    """Every arm's verdict must be able to go BOTH ways: the want itself passes, and flipping any one
    policy's exit fails. A judge that cannot fail is the vacuity this suite exists to catch."""
    n = 0
    for arm in ARMS:
        for lang in ENGINES:
            if (arm[0], lang) in ARM_NA:
                continue
            want = want_for(arm, lang)
            good = {p: min(w) for p, w in want.items()}
            ok, _ = judge_gates(want, good)
            assert ok, (arm[0], lang, "the want itself fails")
            for p in want:
                flipped = dict(good)
                flipped[p] = 0 if 1 in want[p] else 1
                if flipped[p] in want[p]:
                    continue
                ok, _ = judge_gates(want, flipped)
                assert not ok, (arm[0], lang, p, "a flipped exit still passes")
                n += 1
    assert judge_w({"typeSurface": {"types": {"MacDep#MacT": {"kind": "final", "supers": []}}}}, "swift")[0] is False
    assert judge_w(inject_short({"package": "macdep"}, "rust"), "rust")[0] is False
    assert judge_p1({"typeSurface": {"holds": {"Dep#Wrong.shared": "Dep#Wrong"}}, "resolves": ["holds"]}, "swift")[0] is False
    print("selftest: OK — %d flipped cells all fail, the producer judges reject a short key and a wrong type" % n)
    return 0


# =====================================================================================================
# THE RUN
# =====================================================================================================
def _dump(path, d):
    with open(path, "w") as f:
        json.dump(d, f)
    return path


def gate(scanner, pkgdir, deps, policy_path):
    out = os.path.join(os.path.dirname(pkgdir.rstrip(os.sep)), "gate.report.json")
    scanner._clear(pkgdir, out)
    env = dict(os.environ, CANDOR_POLICY=policy_path, CANDOR_DEPS=" ".join(deps))
    return gd.run(scanner._argv(pkgdir, out), cwd=scanner._cwd(pkgdir), env=env).returncode


def scan_chain(scanner, order):
    """Scan base, then dep chained on base, then depb. Returns {name: report path} or raises."""
    reps = {}
    for d in order:
        name = os.path.basename(d)
        chain = [reps["base"]] if name == "dep" else []
        r = scanner.scan(d, deps=chain)
        if not r.produced:
            raise RuntimeError("%s: dependency scan produced no report (rc=%d) %s" % (name, r.rc, r.note))
        reps[name] = r.report
    return reps


def run_engine(lang, ws):
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, None, scanner.err
    results, notes, texts, fixtures = {}, [], {}, {}
    for variant in ("main", "cross"):
        root = os.path.join(ws, lang, variant)
        order, dirs, app, text = render(lang, root, variant)
        texts[variant] = text
        err = build_proof(lang, app)
        if err:
            return None, None, "%s (%s)" % (err, variant)
        try:
            reps = scan_chain(scanner, order)
        except RuntimeError as e:
            return None, None, "%s: %s" % (variant, e)
        fixtures[variant] = (app, reps)
    # THE CROSS, asserted: c4 reads r1's consumer text over a dependency that moved one declaration.
    if texts["main"] != texts["cross"]:
        return None, None, "the consumer differs between the main and cross fixtures — c4 is FIXTURE-INDUCED"

    app, reps = fixtures["main"]
    dep_rep = json.load(open(reps["dep"]))
    if CAL == "surface":
        # CALIBRATION ONLY: a HAND-SPELLED `holds`, so the arms that need a published surface (u1, g1) can
        # be shown to construct and evaluate before any producer ports. Never used in a scored run.
        sp = {"swift": {"Dep#Wrong.shared": "Dep#Other", "Dep#Client.shared": "Dep#Client"},
              "rust": {"dep#SHARED": "dep#Other", "dep#CLIENT": "dep#Client"}}[lang]
        dep_rep.setdefault("typeSurface", {})["holds"] = sp
    scratch = os.path.join(ws, lang, "doctored")
    os.makedirs(scratch, exist_ok=True)

    # Producer arms.
    for pid, judge in (("p1_holds", judge_p1), ("p2_types", judge_p2)):
        results[pid] = judge(dep_rep, lang)
    wid = "w1_macro" if lang == "swift" else "w2_macro"
    wroot = render_w(lang, os.path.join(ws, lang, "withhold"))
    wr = scanner.scan(wroot)
    if not wr.produced:
        return None, None, "withhold fixture: producer wrote no report (rc=%d) %s" % (wr.rc, wr.note)
    wrep = json.load(open(wr.report))
    if FAULT:
        wrep = inject_short(wrep, lang)
    results[wid] = judge_w(wrep, lang)

    def consumer_rows(dep_path, variant="main"):
        a, rp = fixtures[variant]
        deps = [rp["base"], dep_path, rp["depb"]]
        r = scanner.scan(a, deps=deps)
        if not r.produced:
            return None, deps, "consumer scan produced no report (rc=%d) %s" % (r.rc, r.note)
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, deps, "analyzed.count is 0 — a hollow report judges nothing"
        return {f.get("fn", "").replace("::", ".").split(".")[-1]: f for f in rep.get("functions") or []}, deps, None

    cache = {}

    def deps_for(arm):
        variant, kind = arm[1], arm[2]
        key = (variant, kind)
        if key in cache:
            return cache[key]
        if kind is None:
            path = fixtures[variant][1]["dep"]
        elif kind == "u1":
            pair, why = u1_pair(dep_rep, lang)
            if why:
                cache[key] = (None, why)
                return cache[key]
            path = (_dump(os.path.join(scratch, "u1_with.json"), pair[0]),
                    _dump(os.path.join(scratch, "u1_without.json"), pair[1]))
        else:
            d, why = doctor(dep_rep, kind, lang)
            if why:
                cache[key] = (None, why)
                return cache[key]
            path = _dump(os.path.join(scratch, "dep.%s.json" % kind), d)
        cache[key] = (path, None)
        return cache[key]

    pol_dir = os.path.join(ws, lang, "pol")
    os.makedirs(pol_dir, exist_ok=True)

    def gates_for(arm, dep_path, tag=""):
        rows, deps, err = consumer_rows(dep_path, arm[1])
        if err:
            return None, None, err
        row = rows.get(arm[3])
        if row is None:
            return None, None, "ABSENT from functions[] — the carrier alone makes it effectful"
        got = {}
        for i, pol in enumerate(sorted(want_for(arm, lang))):
            pp = os.path.join(pol_dir, "%s%s_%d.policy" % (arm[0], tag, i))
            with open(pp, "w") as f:
                f.write("%s %s\n" % (pol, row["fn"]))
            got[pol] = gate(scanner, fixtures[arm[1]][0], deps, pp)
        return row, got, None

    for arm in ARMS:
        aid = arm[0]
        if (aid, lang) in ARM_NA:
            continue
        path, why = deps_for(arm)
        if why:
            results[aid] = (False, "NOT CONSTRUCTIBLE: " + why)
            continue
        want = want_for(arm, lang)
        if arm[2] == "u1":
            row_a, got_a, err_a = gates_for(arm, path[0], "_with")
            row_b, got_b, err_b = gates_for(arm, path[1], "_without")
            if err_a or err_b:
                results[aid] = (False, err_a or err_b)
                continue
            strip = lambda r: {k: v for k, v in r.items() if k not in ("hash",)}
            same = json.dumps(strip(row_a), sort_keys=True) == json.dumps(strip(row_b), sort_keys=True)
            ok_a, bad_a = judge_gates(want, got_a)
            ok_b, bad_b = judge_gates(want, got_b)
            bad = ([] if same else ["the row DIFFERS: with=%s without=%s" % (row_a.get("inferred"), row_b.get("inferred"))]) \
                + ["with: " + b for b in bad_a] + ["without: " + b for b in bad_b]
            results[aid] = (not bad, "inferred=%s %s" % (sorted(row_a.get("inferred") or []),
                                                         "identical" if same else "DIFFERENT")
                            + ("" if not bad else " — " + "; ".join(bad)))
            continue
        row, got, err = gates_for(arm, path)
        if err:
            results[aid] = (False, err)
            continue
        ok, bad = judge_gates(want, got)
        detail = "inferred=%s gates=%s" % (sorted(row.get("inferred") or []),
                                          " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items())))
        results[aid] = (ok, detail + ("" if ok else " — " + "; ".join(bad)))
    notes.append("  NOTE  %s producer: typeSurface keys %s, resolves %s"
                 % (lang, sorted(surface(dep_rep)), dep_rep.get("resolves")))
    return results, notes, None


def all_arm_ids():
    return [a[0] for a in ARMS] + list(PRODUCER_ARMS)


def main():
    if "--selftest" in sys.argv:
        return selftest()
    import tempfile
    print("=" * 100)
    print("DECLARED TYPES FOR RESOLUTION ⟨0.40⟩ — `typeSurface.holds` / `types` / `adds` (SOUNDNESS R843)")
    print("  r* a hop typed by a DECLARATION in the dependency reaches its real target (deny Env FIRES)")
    print("  c* controls — nothing unreachable is charged, a collision unions or discloses")
    print("  o*/u1/g1 a missing, malformed, stale or wrong surface keeps the guess and ADDS Unknown")
    print("  p*/w* the producer publishes the surface, and OMITS a type it cannot close")
    print("  `deny Net` (the dependency's `carrier()`) must fire on every consumer cell")
    for e, why in sorted(NA.items()):
        print("  %-6s: N/A — %s" % (e, why))
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART95_NOBUILD is set — fixtures were NOT built; for iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — `Client.fetch` and `SubO.m` are emptied (c5_factory, c1_convention,")
        print("       r7b_returns_open), the stale/nothing doctors become the identity (o4, o5), and a short `types`")
        print("       key is injected for every macro-extended type (w1/w2). Every one of those cells must go red.")
    if CAL:
        print("CALIBRATION: CANDOR_PART95_CAL=%s" % CAL)
    ws = tempfile.mkdtemp(prefix="candor-part95-")
    bad = stale = live = 0
    for lang in ENGINES:
        res, notes, err = run_engine(lang, ws)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no swift" in err:
                print("  %-6s -> SKIP (%s)" % (lang, err))
            else:
                print("  %-6s -> BROKEN: %s" % (lang, err))
                bad += 1
            continue
        live += 1
        for n in notes:
            print(n)
        for aid in all_arm_ids():
            key = (aid, lang)
            if key in ARM_NA:
                print("  n/a   %-17s %-6s %s" % (aid, lang, ARM_NA[key]))
                continue
            ok, detail = res[aid]
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-17s %-6s — expectation is STALE: %s" % (aid, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-17s %-6s %s" % (aid, lang, detail))
            elif key in XFAIL:
                print("  xfail %-17s %-6s %s  [%s]" % (aid, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-17s %-6s %s  [%s]" % (aid, lang, detail, WHY[aid[0]]))
                bad += 1
    for e, why in sorted(NA.items()):
        print("  %-6s -> N/A (declared): %s" % (e, why))
    shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("TYPE-SURFACE: no engine available — NOT a pass")
        return 2
    if stale:
        print("TYPE-SURFACE: %d xfail arm(s) PASSED — an expectation that has become true is a FAILURE here. "
              "Retire it in the same commit as the engine change (SOUNDNESS R843)." % stale)
    if bad:
        print("TYPE-SURFACE: %d cell(s) wrong — see SOUNDNESS R843 and SPEC §2 ⟨0.40⟩" % bad)
    if not bad and not stale:
        print("TYPE-SURFACE: OK — every control holds, every degraded surface discloses where it must, and "
              "every open resolution cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
