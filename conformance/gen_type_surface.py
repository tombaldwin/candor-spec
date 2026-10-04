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
`typeSurface.returnsProtocol` (a function returning exactly one protocol), `typeSurface.types` (every
declared type's KIND and complete direct supertypes, as a MANIFEST) and `typeSurface.adds` (conformances
the package adds to FOREIGN types).

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
engine's own gate. Degraded arms (o*, u1, g1, c6) DOCTOR the producer's own report — strip, malform, re-
version, empty, withhold one key, rewrite one value, or chain a second copy beside it — with the consumer's
source byte-identical. A doctor that must WRITE a value writes the producer's own value with its last
segment swapped, never a spelling of ours. Producer arms (p*, w*) read the dependency report alone.

  r1_static     `Wrong.shared.ping()`, `shared: Other`                 -> Env, and swift keeps its Fs guess
  r2_bound      `let s = Wrong.shared; s.ping()`                       -> as r1 (R617)
  r3_property   `n.parent.ping()`, `parent: Other`                     -> as r1 (rust R857)
  r4_inherited  `Holder4.shared.tok4()`, `shared: Mid4`, `Mid4: Grand4` -> Env (the walk on absence)
  r5_refined    `(t: any PSub).pTok()`, `PSub: PBase`, pTok on PBase   -> Env      (R859/R865; rust R858)
  r6_proto_ret  `mkP().run()`, `mkP() -> any PSvc` (`returnsProtocol`) -> Env; rust `Box<dyn>` discloses
  r7a_holds_open `HolderO.shared.m()`, `shared: BaseO = SubO()`        -> Env      (override union)
  r7b_returns_open `let b = mkO(); b.m()`, `mkO() -> BaseO`            -> Env      (passes since R867)
  r8_adds       `Tok().pTok()`, Tok in a THIRD package, `extension Tok: PBase` in dep -> Env (`adds`)
  r9_walk       `HolderW.shared.tokw()`, `T9: PA, PM`, PM's default more specific -> Env (swift)
  r10_holds_proto `SvcHolder.svc.run()`, `svc: any PSvc`              -> Env; rust `&dyn` may disclose
  r11_computed  `Wrong3.computed.ping()`, a computed `static var computed: Other` -> Env (swift)
  r12_holds_dyn rust `SINK: &(dyn Sink + Sync) = &Loud`, Sink's DEFAULT reads Fs, Loud's override Env -> Env
  r13_returns_impl rust `mk_impl() -> impl Sink` (`returnsProtocol`) -> Env
  r14_lookup_miss `Wrong.shared.quiet2()`: `Wrong.quiet2` PURE, the declared `Other.quiet2` reads Env -> Env
  r16_deref     rust `w.leak()`, `w: &dep::WrapD`, a VISIBLE `impl Deref<Target = InnerD>` -> Env (the `deref`
                field resolves it)
  r15_kind_only `HolderK.shared.m2()`, `T2: PA2, PM2`, `PM2: PQ2`, PQ2's default (Env) more specific than
                PA2's (Fs) -> Env (swift; executed). `HolderK` DECLARES its own `m2` (Fs) on purpose: without
                it the singleton-convention lookup MISSES and swift's untyped-receiver disclosure supplies the
                `Unknown` whatever the walk does, which made o14 and c7b VACUOUS (measured by the swift port's
                calibration: both passed under the `?? []` mutant). With it the guess HITS, the guess is kept
                (`deny Fs` 1), and only the walk can supply the `Env` or the `Unknown`

  c1_convention `Client.shared.fetch()`, `shared: Client` (the convention RIGHT)   -> Env     (R826)
  c2_final/c2_value/c2_enum/c2_open   a right-typed singleton whose `m` reads Fs, while an UNRELATED
                member reads Env -> `deny Env` 0: the override union must add nothing it cannot reach
  c3_collision  `Dep.Client.shared.fetch()` in a file importing BOTH `Dep` and `DepB` -> union or disclose
  c4_cross      r1's consumer text BYTE-IDENTICAL, over a dependency where `shared: Wrong` -> `deny Env` 0
  c5_factory    `Client.make().fetch()` — ⟨0.23⟩'s `returns` (R832), pinned unchanged -> Env
  c6_disagree   r1 over TWO trusted copies of the dependency, one rewriting `Wrong.shared` to `Node` ->
                both targets joined: `deny Env` 1 — in BOTH load orders
  c7_types_one_copy r9 over two copies, PM's `types` key in ONE only (the short-closure case) -> disclose,
                both orders
  c7b_kind_only_one_copy r15 over two copies, PM2's key FULL in one and KIND-ONLY in the other -> disclose,
                both orders (a merge taking `supers` from whichever copy closes the type rebuilds the short
                closure). On r15/PM2, not r9/PM: PM DECLARES `tokw` itself, so PM's key never decides r9's walk

  o1_old        r1 over the report with the ⟨0.40⟩ keys STRIPPED -> `deny Env Unknown` 1 (swift: Fs kept)
  o1b_old_right c1 over the stripped report -> `deny Env` 1 AND `deny Unknown` 1
  o2_member_miss `Wrong.shared.quiet()`, `Other.quiet` PURE -> a hit then a member MISS: `deny Unknown` 1
  o3_malformed  r1 over a report whose keys are the wrong JSON type -> as o1, or a refusal (exit 2)
  o4_stale      r1 over a report whose `candor.version` no longer matches -> disclose, and no Env from it
  o5_nothing    r1 over a report that judged nothing but carries the surface -> disclose
  o6_walk_unkeyed r9 with PM's `types` key WITHHELD -> the path through PM is a miss: disclose
  o7_target_unkeyed r7a with BaseO's `types` key WITHHELD -> an unknown kind is open: Env or Unknown
  o8_sub_unkeyed r7a with SubO's `types` key WITHHELD -> overrides come from the ⟨0.39⟩ route: Env or Unknown
  o9_stale_beside r1 over a trusted copy AND a stale copy -> the resolution stands AND the stale copy
                discloses, in both load orders
  o10_adds_partial r8 with Tok's `adds` entry WITHHELD -> `adds` is never complete: disclose
  o11_proto_unkeyed rust r12 / swift r10 with the protocol's `types` key WITHHELD -> an unknown kind never
                takes Rust's empty override set: disclose (the silence the second review found)
  o12_retproto_unkeyed rust r13 / swift r6 with the protocol's key WITHHELD -> a `returnsProtocol` target
                is a protocol anyway: Env
  o13_lookup_miss_old r14 over the stripped report -> a guessed-owner lookup that MISSES discloses
  o15_deref_macro rust `w.leak()`, `w: &depb::WrapM`, whose `Deref` comes out of a `macro_rules!` -> disclose
                (d15: silent on rust f7f4c08 and ad30e26, `deny Env` and `deny Env Unknown` 0, executed Env)
  r17_platform_ext swift `e.eqLeak()`, `EqT: Equatable`, and the DEPENDENCY's `extension Equatable { func
                eqLeak() }` reads Env -> Env (silent on v0.39.3 and 2a3ddc6; executed)
  o16_dyn_member swift `_ = w.leakv` on a `@dynamicMemberLookup` DynW forwarding to InnerS's computed
                `leakv` (Env) -> disclose (silent on v0.39.3 and 2a3ddc6; executed)
  c8_closed_pure rust `q.q()` on a CLOSED `dep::Quiet` with no `Deref` and a pure `q` -> `deny Unknown` 0: the
                rust permission's cost pin (swift N/A — it keeps the default rule)
  t1_bound … t7_blanket  rust: the permission's FIRST ROW — a member reached only through a chained trait the
                consumer brings into scope: a bound (`<T: SubS>`), `&dyn SubS`, `impl SubS`, a re-exporting glob
                (`use depb::prelude::*`), `use … as _`, a plain glob (`use depb::*`) and a blanket impl called on
                a PRIMITIVE receiver (`x: &u8; x.bl()`, R887) -> joined or disclosed (`deny Env Unknown` 1). depb
                is unclosable, so no walk can settle them (the reviewer's d2-d12)
  o14_kind_only r15 with PM2's key cut down to its KIND (no `supers`) -> the PM2 path is a miss: disclose.
                A consumer that defaults a missing `supers` to `[]` reads `[Fs]` and fails both cells
  u1_bound      `Wrong2.shared2.q()`, `shared2: Quiet` (only pure members), with and without its `holds`
                key -> the same EFFECTS and the same GATE EXITS (never compared on reason strings)
  g1_keep_guess c1 over a report whose `holds` for `Client.shared` names `Decoy`, which HAS a `fetch` (Fs)
                -> a true HIT on a WRONG type: `deny Fs` 1 (the hit joined) AND `deny Env` 1 (the guess kept)

  p1_holds      `holds` for Wrong.shared -> Other; swift also a computed getter and a protocol value
  p2_types      every listed type's KIND (open/class/final/value/protocol) and required supers; Quiet,
                a type with only pure members, keyed (`types` is never bounded)
  p3_foreign    `adds` keyed in Base's namespace; SubThing's Base-owned supertype in Base's namespace
  p4_wrappers   `Other?`, `any PA & PSvc`, `Option<Other>` NOT published (and `holds` present at all)
  p6_deref      rust: WrapD keyed CLOSED with `deref` -> InnerD; Quiet carries none; WrapM (macro Deref) unclosed
  p5_returns_protocol `returns` NEVER names a protocol result (mkP / mk_impl), `returnsProtocol` does,
                and a `Box<dyn>` factory is in neither — the only guard a shipped ⟨0.23⟩ consumer has
  w1_macro      swift: an attached extension macro declared in ANOTHER package -> MacT omitted, witness
                PlainT keyed
  w2_macro      rust: `hide!(Y)`, `impl_q!()` (Q unnamed), `#[derive(Opaque)]`, `#[opaque_attr]` -> Y, Q,
                Z, W, Hidden, Hidden2 omitted; non-vacuity from the main dependency's `types`

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
    ("§2 ⟨0.40⟩", "the walk reads absence as \"may be inherited\""),
    ("§2 ⟨0.40⟩", "an unknown kind is never an exact kind"),
    ("§2 ⟨0.40⟩", "It MUST NOT take Rust's empty override set"),
    ("§2 ⟨0.40⟩", "A consumer MUST NOT read a missing `supers` as an empty list"),
    ("§2 ⟨0.40⟩", "A LANGUAGE-SCOPED PERMISSION FOR RUST"),
    ("§2 ⟨0.40⟩", "two copies union; a distrusted copy is a miss"),
    ("§2 ⟨0.40⟩", "It is a separate key and MUST NOT be folded into `returns`"),
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
    gf = "" if CAL == "guess" else f       # the GUESSED targets' own Fs (Wrong.ping, Node.ping, Holder4.tok4)
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
    public func ping() {{ {gf} {cal} }}
    public func quiet() {{ {f} }}
}}
public final class Node {{
    public init() {{}}
    public var parent: Other = Other()
    public func ping() {{ {gf} }}
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
    public func tok4() {{ {gf} }}
}}
public protocol PBase {{}}
extension PBase {{
    public func pTok() {{ {e} }}
}}
public protocol PSub: PBase {{}}
public protocol PSvc {{ func run() }}
extension PSvc {{
    public func run() {{ {f} }}
}}
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
extension Other {{
    public func quiet2() {{ {e} }}
}}
extension Wrong {{
    public func quiet2() {{}}
}}
public final class Decoy {{
    public init() {{}}
    public func fetch() {{ {f} }}
}}
public protocol PA {{}}
extension PA {{
    public func tokw() {{ {f} }}
}}
public protocol PM: PA {{}}
extension PM {{
    public func tokw() {{ {e} }}
}}
public final class T9: PA, PM {{
    public init() {{}}
}}
public final class HolderW {{
    public static let shared: T9 = T9()
}}
public protocol PA2 {{}}
extension PA2 {{
    public func m2() {{ {f} }}
}}
public protocol PQ2: PA2 {{}}
extension PQ2 {{
    public func m2() {{ {e} }}
}}
public protocol PM2: PQ2 {{}}
public final class T2: PA2, PM2 {{
    public init() {{}}
}}
public final class HolderK {{
    public static let shared: T2 = T2()
    public func m2() {{ {f} }}
}}
public final class SvcHolder {{
    public static let svc: any PSvc = SvcImpl()
}}
extension Equatable {{
    public func eqLeak() {{ {e} }}
}}
public struct EqT: Equatable {{
    public init() {{}}
}}
public struct InnerS {{
    public init() {{}}
    public var leakv: Int {{ {e}; return 1 }}
}}
@dynamicMemberLookup
public struct DynW {{
    public init() {{}}
    var inner = InnerS()
    public subscript<T>(dynamicMember kp: KeyPath<InnerS, T>) -> T {{ inner[keyPath: kp] }}
}}
public final class Wrong3 {{
    public static var computed: Other {{ Other() }}
    public func ping() {{ {f} }}
}}
public class ClsK {{
    public init() {{}}
}}
public final class SubThing: BaseThing {{
    public override init() {{ super.init() }}
}}
public final class Wraps {{
    public static let maybe: Other? = nil
    public static let comp: any PA & PSvc = Both()
}}
public final class Both: PA, PSvc {{
    public init() {{}}
    public func run() {{}}
}}
'''


SW_BASE = 'public struct Tok {\n    public init() {}\n}\nopen class BaseThing {\n    public init() {}\n}\n'
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
public func r9_walk() { carrier(); HolderW.shared.tokw() }
public func r10_holds_proto() { carrier(); SvcHolder.svc.run() }
public func r11_computed() { carrier(); Wrong3.computed.ping() }
public func r14_lookup_miss() { carrier(); Wrong.shared.quiet2() }
public func r15_kind_only() { carrier(); HolderK.shared.m2() }
public func c8_closed_pure(_ q: Quiet) { carrier(); q.q() }
public func r17_platform_ext(_ e: EqT) { carrier(); e.eqLeak() }
public func o16_dyn_member(_ w: DynW) { carrier(); _ = w.leakv }
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

# w1: an attached EXTENSION macro, declared in ANOTHER package (`MacLib`), adds `PMac` to `MacT`. The
# plugin is never built — the scan is a parse — and the producer of `MacDep` cannot even see the macro's
# `conformances:` list, which lives in MacLib. `PlainT` is the WITNESS: an attached macro extends only the
# declaration it is attached to, so PlainT's supertypes ARE closable, and a producer that publishes no
# `types` at all fails here rather than passing by absence.
SW_W1_LIB = '''public protocol PMac {}
@attached(extension, conformances: PMac)
public macro AddP() = #externalMacro(module: "MacImpl", type: "AddPMacro")
'''
SW_W1 = '''import MacLib
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
    pub fn q(&self) {{ {cal} }}
}}
pub static SHARED2: Quiet = Quiet;
pub static SVC: &(dyn PSvc + Sync) = &SvcImpl;
pub struct SubThing;
impl base::BaseTr for SubThing {{}}
pub static OPT: Option<Other> = None;
pub trait Sink {{
    fn emit(&self) {{ {f} }}
}}
pub struct Loud;
impl Sink for Loud {{
    fn emit(&self) {{ {e} }}
}}
pub static SINK: &(dyn Sink + Sync) = &Loud;
pub fn mk_impl() -> impl Sink {{ Loud }}
impl Other {{
    pub fn quiet2(&self) {{ {e} }}
}}
impl Wrong {{
    pub fn quiet2(&self) {{}}
}}
pub struct InnerD;
impl InnerD {{
    pub fn leak(&self) {{ {e} }}
}}
pub struct WrapD(pub InnerD);
impl std::ops::Deref for WrapD {{
    type Target = InnerD;
    fn deref(&self) -> &InnerD {{ &self.0 }}
}}
'''


RS_BASE = 'pub struct Tok;\nimpl Tok {\n    pub fn new() -> Tok { Tok }\n}\npub trait BaseTr {}\n'
RS_DEPB = ('pub struct Client;\nimpl Client {\n    pub fn fetch(&self) { %s }\n}\npub static CLIENT: Client = Client;\n' % FS["rust"]
           # d15: `WrapM`'s Deref comes out of a `macro_rules!`, so the producer cannot close WrapM — the
           # consumer's `w.leak()` forwards to `InnerM::leak` (Env) through an edge no report shows.
           + 'pub struct InnerM;\nimpl InnerM {\n    pub fn leak(&self) { %s }\n}\n' % ENV["rust"]
           + 'macro_rules! mk_deref {\n    ($t:ident, $u:ident) => {\n        impl std::ops::Deref for $t {\n'
             '            type Target = $u;\n            fn deref(&self) -> &$u { &self.0 }\n        }\n    };\n}\n'
           + 'pub struct WrapM(pub InnerM);\nmk_deref!(WrapM, InnerM);\n'
           # THE TRAIT-IN-SCOPE ARMS (the reviewer's d2-d12, R887): every member below reaches its `Env` only
           # through a trait the CONSUMER brings into scope. depb is unclosable (the macro above), so a walk
           # cannot settle these — the permission's first row must join or disclose.
           + 'pub trait GrandS {\n    fn g(&self) { %s }\n}\npub trait SubS: GrandS {}\npub struct InnerS;\n'
             'impl GrandS for InnerS {}\nimpl SubS for InnerS {}\n'
             'pub trait ExtS {\n    fn e(&self) { %s }\n}\nimpl ExtS for InnerS {}\n'
             'pub mod prelude {\n    pub use crate::ExtS;\n}\n'
             'pub trait Bl {\n    fn bl(&self) { %s }\n}\nimpl<T: ?Sized> Bl for T {}\n' % (ENV["rust"], ENV["rust"], ENV["rust"]))
RS_APP = '''use dep::{Grand4, Node, PBase, PSvc, Sink};
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
pub fn r10_holds_proto() { dep::carrier(); dep::SVC.run() }
pub fn r12_holds_dyn() { dep::carrier(); dep::SINK.emit() }
pub fn r13_returns_impl() { dep::carrier(); dep::mk_impl().emit() }
pub fn r14_lookup_miss() { dep::carrier(); dep::SHARED.quiet2() }
pub fn r16_deref(w: &dep::WrapD) { dep::carrier(); w.leak() }
pub fn o15_deref_macro(w: &depb::WrapM) { dep::carrier(); w.leak() }
pub fn c8_closed_pure(q: &dep::Quiet) { dep::carrier(); q.q() }
pub fn t1_bound<T: depb::SubS>(t: &T) { dep::carrier(); t.g() }
pub fn t2_dyn(t: &dyn depb::SubS) { dep::carrier(); t.g() }
pub fn t3_impl_arg(t: impl depb::SubS) { dep::carrier(); t.g() }
pub mod tg { use depb::prelude::*; pub fn t4_glob_reexport(i: &depb::InnerS) { dep::carrier(); i.e() } }
pub mod tu { use depb::prelude::ExtS as _; pub fn t5_underscore(i: &depb::InnerS) { dep::carrier(); i.e() } }
pub mod tk { use depb::*; pub fn t6_glob(i: &InnerS) { dep::carrier(); i.g() } }
pub mod tb { use depb::Bl; pub fn t7_blanket(x: &u8) { dep::carrier(); x.bl() } }
'''

# w2: four expansions the producer may not see through. `hide!(Y)` declares a trait AND implements it for
# the type NAMED in its arguments; `impl_q!()` implements a trait for `Q`, which its invocation never
# names; `#[derive(Opaque)]` and the attribute macro `#[opaque_attr]` are proc macros whose output is
# invisible. `Plain` is NOT a witness here: a proc macro may emit an `impl` for any type in the crate, so a
# producer that withholds every type in this crate is conformant. Non-vacuity comes from the MAIN
# dependency instead — the producer must publish `types` there (p2) or this arm is not evidence.
RS_W2 = '''pub trait Visible {}
macro_rules! hide {
    ($t:ident) => {
        pub trait Hidden {}
        impl Hidden for $t {}
    };
}
macro_rules! impl_q {
    () => {
        pub trait Hidden2 {}
        impl Hidden2 for Q {}
    };
}
pub struct Y;
impl Visible for Y {}
hide!(Y);
pub struct Q;
impl_q!();
#[derive(Opaque)]
pub struct Z;
impl Visible for Z {}
#[opaque_attr]
pub struct W;
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
    """Returns (scan order, the package whose report is judged)."""
    if lang == "swift":
        lib, dep = os.path.join(root, "maclib"), os.path.join(root, "macdep")
        _w(os.path.join(lib, "Package.swift"), SW_MANIFEST % dict(mod="MacLib", deps="", prods=""))
        _w(os.path.join(lib, "Sources", "MacLib", "lib.swift"), SW_W1_LIB)
        _w(os.path.join(dep, "Package.swift"),
           SW_MANIFEST % dict(mod="MacDep", deps='.package(path: "../maclib")',
                              prods='.product(name: "MacLib", package: "maclib")'))
        _w(os.path.join(dep, "Sources", "MacDep", "mac.swift"), SW_W1)
        return [lib, dep], dep
    _w(os.path.join(root, "Cargo.toml"), '[package]\nname="macdep"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(root, "src", "lib.rs"), RS_W2)
    return [root], root


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
# THE ARMS. (id, dependency variant, deps spec, consumer fn, want) where `want` maps a policy's effect
# text to the exit code(s) a conformant engine gives it; a per-engine form {engine: want} replaces it
# whole. Every consumer arm ALSO asserts the carrier, `deny Net` = 1, unless NO_CARRIER says why not.
#
# `deps spec` is None (the producer's report as written), a DOCTOR name (the producer's own report,
# mutated — see `doctor`), "u1" (the bound-equivalence pair), or one of the TWO-COPY specs ("beside_stale",
# "disagree"), which chain a second copy of the dependency's report beside the first.
# =====================================================================================================
ENV1 = {"deny Env": {1}}
ENV0 = {"deny Env": {0}}
DISCLOSE = {"deny Env Unknown": {1}}
# THE GUESS IS KEPT. Where swift's consumer charges a guessed target today (the convention owner's own
# `Fs` member), a hit must ADD the declared target and keep that charge — `deny Fs` = 1 beside `deny Env`
# = 1. A consumer that SWAPS the guess for the declared type passes `deny Env` and fails `deny Fs`.
KEEP = {"deny Env": {1}, "deny Fs": {1}}
ARMS = [
    # id                   variant  deps spec            fn                 want / {engine: want}
    ("r1_static",          "main",  None,                "r1_static",        {"swift": KEEP, "rust": ENV1}),
    ("r2_bound",           "main",  None,                "r2_bound",         {"swift": KEEP, "rust": ENV1}),
    ("r3_property",        "main",  None,                "r3_property",      {"swift": KEEP, "rust": ENV1}),
    ("r4_inherited",       "main",  None,                "r4_inherited",     {"swift": KEEP, "rust": ENV1}),
    ("r5_refined",         "main",  None,                "r5_refined",       ENV1),
    ("r6_proto_ret",       "main",  None,                "r6_proto_ret",     {"swift": ENV1, "rust": DISCLOSE}),
    ("r7a_holds_open",     "main",  None,                "r7a_holds_open",   ENV1),
    ("r7b_returns_open",   "main",  None,                "r7b_returns_open", ENV1),
    ("r8_adds",            "main",  None,                "r8_adds",          ENV1),
    ("r9_walk",            "main",  None,                "r9_walk",          ENV1),
    ("r10_holds_proto",    "main",  None,                "r10_holds_proto",  ENV1),
    ("r11_computed",       "main",  None,                "r11_computed",     ENV1),
    ("r12_holds_dyn",      "main",  None,                "r12_holds_dyn",    ENV1),
    ("r13_returns_impl",   "main",  None,                "r13_returns_impl", ENV1),
    ("r14_lookup_miss",    "main",  None,                "r14_lookup_miss",  ENV1),
    ("r15_kind_only",      "main",  None,                "r15_kind_only",    {"swift": KEEP, "rust": ENV1}),
    ("r16_deref",          "main",  None,                "r16_deref",        ENV1),
    ("r17_platform_ext",   "main",  None,                "r17_platform_ext", ENV1),
    ("c1_convention",      "main",  None,                "c1_convention",    ENV1),
    ("c2_final",           "main",  None,                "c2_final",         ENV0),
    ("c2_value",           "main",  None,                "c2_value",         ENV0),
    ("c2_enum",            "main",  None,                "c2_enum",          ENV0),
    ("c2_open",            "main",  None,                "c2_open",          ENV0),
    ("c3_collision",       "main",  None,                "c3_collision",     DISCLOSE),
    ("c4_cross",           "cross", None,                "r1_static",        ENV0),
    ("c5_factory",         "main",  None,                "c5_factory",       ENV1),
    ("c6_disagree",        "main",  "disagree",          "r1_static",        ENV1),
    ("c7_types_one_copy",  "main",  "one_copy_types:PM", "r9_walk",          DISCLOSE),
    ("c7b_kind_only_one_copy", "main", "one_copy_kindonly:PM2", "r15_kind_only", DISCLOSE),
    ("c8_closed_pure",     "main",  None,                "c8_closed_pure",   {"deny Unknown": {0}, "deny Env": {0}}),
    ("o1_old",             "main",  "strip",             "r1_static",        {"swift": {"deny Env Unknown": {1}, "deny Fs": {1}}, "rust": DISCLOSE}),
    ("o1b_old_right",      "main",  "strip",             "c1_convention",    {"deny Env": {1}, "deny Unknown": {1}}),
    ("o2_member_miss",     "main",  None,                "o2_member_miss",   {"swift": {"deny Unknown": {1}, "deny Fs": {1}}, "rust": {"deny Unknown": {1}}}),
    ("o3_malformed",       "main",  "malformed",         "r1_static",        {"deny Env Unknown": {1, 2}}),
    ("o4_stale",           "main",  "stale",             "r1_static",        {"deny Env Unknown": {1}, "deny Env": {0}}),
    ("o5_nothing",         "main",  "nothing",           "r1_static",        DISCLOSE),
    ("o6_walk_unkeyed",    "main",  "drop_types:PM",     "r9_walk",          DISCLOSE),
    ("o7_target_unkeyed",  "main",  "drop_types:BaseO",  "r7a_holds_open",   DISCLOSE),
    ("o8_sub_unkeyed",     "main",  "drop_types:SubO",   "r7a_holds_open",   DISCLOSE),
    ("o9_stale_beside",    "main",  "beside_stale",      "r1_static",        {"deny Env": {1}, "deny Env Unknown": {1}}),
    ("o10_adds_partial",   "main",  "drop_adds:Tok",     "r8_adds",          DISCLOSE),
    ("o11_proto_unkeyed",  "main",  {"rust": "drop_types:Sink", "swift": "drop_types:PSvc"},
                                                         {"rust": "r12_holds_dyn", "swift": "r10_holds_proto"}, DISCLOSE),
    ("o12_retproto_unkeyed", "main", {"rust": "drop_types:Sink", "swift": "drop_types:PSvc"},
                                                         {"rust": "r13_returns_impl", "swift": "r6_proto_ret"}, ENV1),
    ("o13_lookup_miss_old", "main", "strip",             "r14_lookup_miss",  DISCLOSE),
    ("o14_kind_only",      "main",  "kindonly:PM2",      "r15_kind_only",    DISCLOSE),
    ("o15_deref_macro",    "main",  None,                "o15_deref_macro",  DISCLOSE),
    # THE TRAIT-IN-SCOPE SET (the rust permission's first row): a member reached only through a chained
    # trait the consumer brings into scope — a bound, `dyn`, `impl` arg, a re-exporting glob, `as _`, a plain
    # glob, and a blanket impl on a PRIMITIVE receiver (R887) — must be joined or disclosed, never read pure.
    ("t1_bound",           "main",  None,                "t1_bound",         DISCLOSE),
    ("t2_dyn",             "main",  None,                "t2_dyn",           DISCLOSE),
    ("t3_impl_arg",        "main",  None,                "t3_impl_arg",      DISCLOSE),
    ("t4_glob_reexport",   "main",  None,                "t4_glob_reexport", DISCLOSE),
    ("t5_underscore",      "main",  None,                "t5_underscore",    DISCLOSE),
    ("t6_glob",            "main",  None,                "t6_glob",          DISCLOSE),
    ("t7_blanket",         "main",  None,                "t7_blanket",       DISCLOSE),
    ("o16_dyn_member",     "main",  None,                "o16_dyn_member",   DISCLOSE),
    ("u1_bound",           "main",  "u1",                "u1_bound",         {"deny Unknown": {1}}),
    ("g1_keep_guess",      "main",  "wrongholds",        "c1_convention",    {"deny Env": {1}, "deny Fs": {1}}),
]
# Producer-side arms — judged on the dependency report alone, never on a gate.
PRODUCER_ARMS = ("p1_holds", "p2_types", "p3_foreign", "p4_wrappers", "p5_returns_protocol", "p6_deref", "w1_macro", "w2_macro")

# (arm, engine) -> why the arm cannot be written in that engine. Each is a DECLARED N/A, not a skip.
_NO_CLASS = "Rust has no class inheritance — a `static` of a concrete type has exactly one body per method (PART 94's N/A)"
_NO_GUESS = ("Rust makes no singleton-convention guess — `dep::CLIENT` is a static ITEM typed only by this "
             "rung, which is r1's shape")
ARM_NA = {
    ("r7a_holds_open", "rust"): _NO_CLASS,
    ("r7b_returns_open", "rust"): _NO_CLASS,
    ("o7_target_unkeyed", "rust"): _NO_CLASS,
    ("o8_sub_unkeyed", "rust"): _NO_CLASS,
    ("r9_walk", "rust"): ("Rust has no specialisation: two in-scope trait defaults for one method name are a "
                          "compile error, and a subtrait cannot override its supertrait's default, so a walk "
                          "that hits one ancestor cannot be short a MORE SPECIFIC one"),
    ("o6_walk_unkeyed", "rust"): "as r9_walk",
    ("r11_computed", "rust"): "Rust has no computed properties — a getter is a function, which is ⟨0.23⟩'s `returns`",
    ("c1_convention", "rust"): _NO_GUESS,
    ("o1b_old_right", "rust"): "as c1_convention — there is no guess to keep",
    ("g1_keep_guess", "rust"): "as c1_convention — there is no guess for a hit to displace",
    ("c2_value", "rust"): "rust's c2_final is already a value type (a struct) — Rust has no reference classes",
    ("c2_open", "rust"): "Rust has no open classes",
    ("w1_macro", "rust"): "w2_macro is rust's withhold arm",
    ("r12_holds_dyn", "swift"): "swift's r10_holds_proto is this shape (`any PSvc`, whose extension default the implementor overrides)",
    ("r13_returns_impl", "swift"): "swift's r6_proto_ret is this shape (`-> any PSvc`)",
    ("r16_deref", "swift"): "Swift has no `Deref`; its implicit forwarding is `@dynamicMemberLookup`, which the DEFAULT rule covers (see SPEC §2 ⟨0.40⟩) — untested",
    ("o15_deref_macro", "swift"): "as r16_deref",
    ("r17_platform_ext", "rust"): "a Rust trait method needs its trait in scope — the permission's first row, not a supertype walk",
    ("o16_dyn_member", "rust"): "Rust has no dynamic member lookup; its forwarding edge is `Deref` (r16, o15)",
    ("p6_deref", "swift"): "as r16_deref — `deref` is a Rust-only field",
    **{(t, "swift"): ("the RUST permission's first row — a Swift protocol-extension member needs no import of "
                      "the protocol, so Swift keeps the default rule (r17_platform_ext)")
       for t in ("t1_bound", "t2_dyn", "t3_impl_arg", "t4_glob_reexport", "t5_underscore", "t6_glob", "t7_blanket")},
    ("c8_closed_pure", "swift"): ("the RUST permission's cost pin; Swift keeps the default rule, under which a member no closed path "
                                  "reaches is a member miss, because a platform-protocol extension member needs no import"),
    ("r15_kind_only", "rust"): "as r9_walk — in Rust a `[]`-defaulted `supers` can only cost a member miss, which already discloses",
    ("o14_kind_only", "rust"): "as r15_kind_only",
    ("c7b_kind_only_one_copy", "rust"): "as r9_walk",
    ("c7_types_one_copy", "rust"): "as r9_walk — the walk it shortens cannot be short a more specific default in Rust",
    ("w2_macro", "swift"): "w1_macro is swift's withhold arm",
}

WHY = {
    "r": "RESOLUTION: the declared type (or the dependency's own hierarchy) names the real target, and the "
         "consumer must reach it — keeping, beside it, whatever it already charged",
    "c": "CONTROL: an unrelated or unreachable `Env` must not be charged; a collision or a disagreement "
         "must union or disclose — never pick",
    "o": "DEGRADED: no trustworthy surface answers this hop, so the consumer keeps what it had and ADDS "
         "`Unknown`",
    "t": "TRAIT IN SCOPE (the rust permission's first row): a chained trait the consumer brings into scope "
         "carries the member, so it must be joined or disclosed — never read pure",
    "u": "BOUND EQUIVALENCE: a bounded and an unbounded producer must give the consumer the same effects "
         "and the same gate exits",
    "g": "KEEP THE GUESS: a HIT adds a target, it never displaces one — the displacement is rung B",
    "p": "PRODUCER: the surface the consumer needs must be on the wire, spelled and kinded as SPEC states",
    "w": "WITHHOLD: a `types` key is complete or absent — a type an unseen expansion may extend is "
         "omitted, never listed short",
}

# An expectation keyed by (arm, engine). A PASSING XFAIL IS A FAILURE. A pure LITERAL on purpose:
# scripts/xfail-register-agree.py reads it with ast.literal_eval and skips any table it cannot evaluate,
# so a note built from a variable would make every line below invisible to the register check.
XFAIL = {
}


# A distrusted (o4) or judged-nothing (o5) dependency report takes `carrier()` down with it — §2.1
# downgrades EVERY inherited effect to `Unknown` — so `deny Net` cannot be the carrier there. Neither arm
# needs one for its `1` cells (a gate that FIRES has proved its scope bound), and o4's `deny Env` = 0 is
# carried by its own `deny Env Unknown` = 1 on the same scope. o3 MAY be refused outright (exit 2, SPEC
# §2 ⟨0.40⟩), so its carrier accepts 2 as well as 1.
NO_CARRIER = ("o4_stale", "o5_nothing")
REFUSABLE = ("o3_malformed",)


def spec_of(arm, lang):
    return arm[2][lang] if isinstance(arm[2], dict) else arm[2]


def fn_of(arm, lang):
    return arm[3][lang] if isinstance(arm[3], dict) else arm[3]


def want_for(arm, lang):
    w = arm[4]
    if "rust" in w or "swift" in w:
        w = w[lang]
    w = dict(w)
    if arm[0] not in NO_CARRIER:
        w["deny Net"] = {1, 2} if arm[0] in REFUSABLE else {1}
    return w


# =====================================================================================================
# KEY LOOKUP, spelling-agnostic. The ⟨0.23⟩ spelling rule fixes keys in the OWNING package's namespace,
# which differs by engine (`Dep#Wrong.shared`, `dep#SHARED`). The part never spells a key itself: it
# finds the producer's own key by its last segment(s), and a value it must WRITE (a doctor) is the
# producer's own value with its last segment substituted — never a spelling of ours (⟨0.39⟩ obl. 2).
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


def relabel(v, leaf):
    """The producer's own spelling of a sibling type: `v` with its last segment replaced by `leaf`."""
    return v[: len(v) - len(leaf_of(v))] + leaf


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
RUNG_KEYS = ("holds", "types", "adds", "returnsProtocol")


def doctor(rep, kind, lang):
    d = copy.deepcopy(rep)
    ts = surface(d)
    if FAULT and kind in ("stale", "nothing"):
        # The fault makes these two doctors the IDENTITY, so the arm reads the undoctored report — which
        # proves the doctored document, not something else, is what reached the consumer (swift reddens
        # PRE-PORT; after a port the undoctored report RESOLVES r1 and this calibration goes vacuous —
        # the porting commit must re-calibrate o4/o5, see run.sh's CALIBRATED note).
        return d, None
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
        d["resolves"] = sorted(set(d.get("resolves") or []) | {"holds", "types", "adds"})
        return d, None
    if kind == "stale":
        d.setdefault("candor", {})["version"] = "part95-stale-0.0.0"
        return d, None
    if kind == "nothing":
        d["functions"] = []
        d["analyzed"] = {"count": 0, "digest": "cbf29ce484222325"}
        return d, None
    if kind.startswith("kindonly:"):
        # A KIND-ONLY key: `kind` kept, `supers` dropped — the shape a producer emits for a type whose
        # supertypes it cannot close. A consumer that defaults a missing `supers` to `[]` reads it as
        # "complete, no supertypes" and settles the walk short (R860's bug in the new state).
        leaf = kind.split(":", 1)[1]
        table = ts.get("types")
        k = find_key(table, leaf)
        if not k or not isinstance(table[k], dict) or "kind" not in table[k]:
            return None, "the producer publishes no `types` entry (with a kind) for %s to strip" % leaf
        table = dict(table)
        table[k] = {"kind": table[k]["kind"]}
        ts = dict(ts)
        ts["types"] = table
        d["typeSurface"] = ts
        return d, None
    if kind.startswith("drop_types:") or kind.startswith("drop_adds:"):
        field, leaf = kind.split(":")
        field = field[len("drop_"):]
        table = ts.get(field)
        k = find_key(table, leaf)
        if not k:
            return None, "the producer publishes no `%s` entry for %s to withhold" % (field, leaf)
        table = dict(table)
        del table[k]
        ts = dict(ts)
        ts[field] = table
        d["typeSurface"] = ts
        return d, None
    if kind in ("wrongholds", "disagree"):
        holds = ts.get("holds")
        k_wrong = find_key(holds, *SHARED[lang])
        if kind == "wrongholds":
            k_site = find_key(holds, *CLIENT[lang])
            target = "Decoy"            # HAS a `fetch` (Fs): the rewritten key is a HIT, not a member miss
        else:
            k_site = k_wrong
            target = "Node"             # HAS a `ping` (Fs): the second copy disagrees and still hits
        if not (k_site and k_wrong):
            return None, "the producer publishes no `holds` for the site to rewrite"
        holds = dict(holds)
        holds[k_site] = relabel(holds[k_wrong], target)
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
    with_["typeSurface"]["holds"][k_new] = relabel(holds[k1], "Quiet")
    return (with_, without), None


# =====================================================================================================
# THE PRODUCER JUDGES — each returns (ok, detail).
# =====================================================================================================
def judge_p1(rep, lang):
    holds = surface(rep).get("holds")
    if not isinstance(holds, dict):
        return False, "no `holds` published"
    want = [(SHARED[lang], "Other")]
    if lang == "swift":
        # a COMPUTED property's getter type, and a value of exactly one protocol (`any PSvc`)
        want += [(("computed", "Wrong3"), "Other"), (("svc", "SvcHolder"), "PSvc")]
    bad = []
    for (leaf, owner), ty in want:
        k = find_key(holds, leaf, owner)
        if not k:
            bad.append("no entry for %s.%s" % (owner or "", leaf))
        elif leaf_of(holds[k]) != ty:
            bad.append("`holds[%s]` = %r — the declared type is %s" % (k, holds[k], ty))
    if "holds" not in (rep.get("resolves") or []):
        bad.append("`holds` not listed in `resolves`")
    return (not bad), ("; ".join(bad) if bad else "%d entries as declared" % len(want))


def _sup_leaves(entry):
    return {leaf_of(s) for s in (entry.get("supers") or [])} if isinstance(entry, dict) else set()


# Each type's REQUIRED kind, and supertypes that must be among its `supers`. Quiet has ONLY pure members:
# its presence is the `types`-is-never-bounded check.
KINDS = {
    "swift": {"Mid4": ("open", {"Grand4"}), "BaseO": ("open", set()), "SubO": ("final", {"BaseO"}),
              "Client": ("final", set()), "ClsK": ("class", set()), "Val": ("value", set()),
              "En": ("value", set()), "PSub": ("protocol", {"PBase"}), "PM": ("protocol", {"PA"}),
              "T9": ("final", {"PA", "PM"}), "Quiet": ("final", set())},
    "rust": {"Mid4": ("value", {"Grand4"}), "Grand4": ("protocol", set()), "PSub": ("protocol", {"PBase"}),
             "En": ("value", set()), "SvcImpl": ("value", {"PSvc"}), "Quiet": ("value", set())},
}


def judge_p2(rep, lang):
    types = surface(rep).get("types")
    if not isinstance(types, dict):
        return False, "no `types` manifest"
    bad = []
    for name, (kind, sups) in sorted(KINDS[lang].items()):
        k = find_key(types, name)
        if not k:
            bad.append("%s absent" % name)
            continue
        e = types[k]
        if not isinstance(e, dict) or e.get("kind") != kind:
            bad.append("%s kind %r want %s" % (name, e.get("kind") if isinstance(e, dict) else e, kind))
        if not sups <= _sup_leaves(e):
            bad.append("%s supers %s lacks %s" % (name, sorted(_sup_leaves(e)), sorted(sups - _sup_leaves(e))))
    if "types" not in (rep.get("resolves") or []):
        bad.append("`types` not listed in `resolves`")
    return (not bad), ("; ".join(bad) if bad else "%d kinds and supers as declared" % len(KINDS[lang]))


def judge_p3(rep, base_pkg, lang):
    """A supertype or extended type owned by ANOTHER package keeps that package's spelling."""
    ts = surface(rep)
    pre = "%s#" % base_pkg
    bad = []
    adds = ts.get("adds")
    k = find_key(adds, "Tok")
    if not k:
        bad.append("no `adds` entry for Tok")
    else:
        if not k.startswith(pre):
            bad.append("`adds` key %r is not spelled in %s's namespace" % (k, base_pkg))
        if "PBase" not in {leaf_of(x) for x in (adds[k] or [])}:
            bad.append("`adds[%s]` lacks PBase" % k)
    types = ts.get("types")
    k = find_key(types, "SubThing")
    sup = "BaseThing" if lang == "swift" else "BaseTr"
    if not k:
        bad.append("no `types` entry for SubThing")
    else:
        hits = [x for x in (types[k] or {}).get("supers") or [] if leaf_of(x) == sup]
        if not hits or not all(x.startswith(pre) for x in hits):
            bad.append("SubThing's %s supertype %s is not spelled in %s's namespace" % (sup, hits, base_pkg))
    return (not bad), ("; ".join(bad) if bad else "Tok and SubThing's supertype keep %s's spelling" % base_pkg)


WRAPPED = {"swift": [("maybe", "Wraps"), ("comp", "Wraps")], "rust": [("OPT", None)]}


def judge_p4(rep, lang):
    """A wrapper is still a wrapper: `Other?`, `any PA & PSvc`, `Option<Other>` MUST NOT publish."""
    holds = surface(rep).get("holds")
    if not isinstance(holds, dict):
        return False, "no `holds` published — the refusal cannot be told from absence (VACUOUS)"
    leaked = [k for leaf, own in WRAPPED[lang] for k in [find_key(holds, leaf, own)] if k]
    if leaked:
        return False, "`holds` publishes a wrapped value: %s" % ["%s=%s" % (k, holds[k]) for k in leaked]
    return True, "no wrapped value published"


PROTO_FACTORY = {"swift": [("mkP", "PSvc")], "rust": [("mk_impl", "Sink")]}
WRAPPED_FACTORY = {"swift": [], "rust": ["mk_p"]}     # `-> Box<dyn PSvc>`: a wrapper, in neither key


def judge_p5(rep, lang):
    """`returns` NEVER names a protocol — the only guard a SHIPPED ⟨0.23⟩ consumer has (SPEC §2 ⟨0.40⟩,
    measured: candor-swift v0.39.3 goes silent on it) — and a one-protocol factory is in `returnsProtocol`."""
    ts = surface(rep)
    ret, rp = ts.get("returns") or {}, ts.get("returnsProtocol")
    bad = []
    for fn, proto in PROTO_FACTORY[lang]:
        if find_key(ret, fn):
            bad.append("`returns` names %s's protocol result — a shipped consumer joins it exactly" % fn)
        k = find_key(rp, fn)
        if not k:
            bad.append("no `returnsProtocol` entry for %s" % fn)
        elif leaf_of(rp[k]) != proto:
            bad.append("`returnsProtocol[%s]` = %r — want %s" % (k, rp[k], proto))
    for fn in WRAPPED_FACTORY[lang]:
        if find_key(ret, fn) or find_key(rp or {}, fn):
            bad.append("%s (a Box<dyn>) is published — a wrapper is still a wrapper" % fn)
    if rp is not None and "returnsProtocol" not in (rep.get("resolves") or []):
        bad.append("`returnsProtocol` not listed in `resolves`")
    return (not bad), ("; ".join(bad) if bad else "protocol results in `returnsProtocol` only")


def judge_p6(rep, depb_rep, lang):
    """Rust: a VISIBLE `impl Deref` is published as `deref` on a CLOSED key, so the consumer can follow it;
    a macro-generated one leaves its type unclosed (no `supers`, no `deref`)."""
    types = surface(rep).get("types")
    if not isinstance(types, dict):
        return False, "no `types` manifest"
    bad = []
    k = find_key(types, "WrapD")
    e = types.get(k) if k else None
    if not isinstance(e, dict) or "supers" not in e:
        bad.append("WrapD is not keyed closed (%s)" % e)
    elif leaf_of(e.get("deref") or "") != "InnerD":
        bad.append("WrapD's `deref` is %r — want InnerD" % e.get("deref"))
    k = find_key(types, "Quiet")
    if k and isinstance(types[k], dict) and types[k].get("deref"):
        bad.append("Quiet carries a `deref` it does not have")
    bt = surface(depb_rep).get("types") or {}
    k = find_key(bt, "WrapM")
    if k and isinstance(bt[k], dict) and ("supers" in bt[k] or "deref" in bt[k]):
        bad.append("WrapM is published CLOSED (%s) though its Deref comes from a macro_rules!" % bt[k])
    return (not bad), ("; ".join(bad) if bad else "WrapD -> InnerD; WrapM unclosed")


WITHHELD = {"swift": ("MacT",), "rust": ("Y", "Z", "W", "Q", "Hidden", "Hidden2")}


def inject_short(rep, lang):
    """THE CLASSIFIER-MUST-FIRE FAULT: a producer that emits what it CAN see — a short key for each type an
    unseen expansion may extend. The w arm must go red over this."""
    d = copy.deepcopy(rep)
    ts = d.setdefault("typeSurface", {})
    types = ts.setdefault("types", {})
    pkg = (d.get("package") or "MacDep")
    for name in WITHHELD[lang]:
        types["%s#%s" % (pkg, name)] = {"kind": "value" if lang == "rust" else "final", "supers": []}
    if lang == "swift":
        types["%s#PlainT" % pkg] = {"kind": "final", "supers": []}
    return d


def judge_w(rep, lang, main_rep):
    types = surface(rep).get("types")
    if types is not None and not isinstance(types, dict):
        return False, "`types` is not an object"
    # A withheld type MAY keep its `kind` (no expansion changes a declaration's kind); what it must not
    # carry is a `supers` list, which would read as complete.
    leaked = [n for n in WITHHELD[lang] for k in [find_key(types or {}, n)]
              if k and (not isinstance(types[k], dict) or "supers" in types[k])]
    if leaked:
        return False, "`types` lists `supers` for %s — a type an unseen expansion may extend must carry none" % leaked
    if lang == "swift":
        # An attached macro extends only its own declaration, so PlainT IS closable and MUST be keyed.
        w = find_key(types or {}, "PlainT")
        if not w or not isinstance(types[w], dict) or "supers" not in types[w]:
            return False, "the witness PlainT carries no `supers` — omission cannot be told from publishing nothing"
        return True, "MacT withheld, witness PlainT published"
    # rust: a proc macro may emit an `impl` for ANY type in its crate, so withholding everything here is
    # conformant; non-vacuity comes from the main dependency publishing `types` at all.
    if not isinstance(surface(main_rep).get("types"), dict):
        return False, "the producer publishes no `types` anywhere — omission cannot be told from absence"
    return True, "every macro-touched type withheld; the producer publishes `types` elsewhere"


# =====================================================================================================
# THE CONSUMER JUDGE — a pure function of the gate exits, so --selftest can attack it.
# =====================================================================================================
def judge_gates(want, got):
    bad = ["`%s` exit %s want %s" % (p, got.get(p), "/".join(map(str, sorted(w))))
           for p, w in sorted(want.items()) if got.get(p) not in w]
    return not bad, bad


def judge_u1(row_a, got_a, row_b, got_b, want):
    """THE EQUIVALENCE IS ON EFFECTS AND GATE EXITS, never on whole rows: an `unknownWhy` reason string may
    legitimately differ (a member miss and an absent key can name different reasons) and must not read as a
    broken equivalence."""
    eff_a, eff_b = sorted(row_a.get("inferred") or []), sorted(row_b.get("inferred") or [])
    bad = []
    if eff_a != eff_b:
        bad.append("the effects DIFFER: with=%s without=%s" % (eff_a, eff_b))
    if got_a != got_b:
        bad.append("the gate exits DIFFER: with=%s without=%s" % (got_a, got_b))
    for tag, got in (("with", got_a), ("without", got_b)):
        ok, b = judge_gates(want, got)
        bad += ["%s: %s" % (tag, x) for x in b]
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
    w = {"deny Unknown": {1}, "deny Net": {1}}
    g = {"deny Unknown": 1, "deny Net": 1}
    assert judge_u1({"inferred": ["Fs", "Unknown"], "unknownWhy": ["a"]}, g,
                    {"inferred": ["Unknown", "Fs"], "unknownWhy": ["b"]}, g, w)[0], "u1: a reason string failed it"
    assert not judge_u1({"inferred": ["Fs", "Unknown"]}, g, {"inferred": ["Unknown"]}, g, w)[0], "u1: effects"
    assert not judge_u1({"inferred": ["Fs"]}, g, {"inferred": ["Fs"]}, dict(g, **{"deny Unknown": 0}), w)[0]
    main_ok = {"typeSurface": {"types": {"dep#Mid4": {"kind": "value", "supers": []}}}}
    assert judge_w(inject_short({"package": "macdep"}, "rust"), "rust", main_ok)[0] is False
    assert judge_w({"package": "macdep"}, "rust", {})[0] is False, "w2 vacuity"
    assert judge_w({"typeSurface": {"types": {}}}, "swift", {})[0] is False, "w1 witness"
    assert judge_w(inject_short({"package": "MacDep"}, "swift"), "swift", {})[0] is False
    assert judge_w({"typeSurface": {"types": {"MacDep#PlainT": {"kind": "final", "supers": []}}}}, "swift", {})[0]
    assert judge_p1({"typeSurface": {"holds": {"dep#SHARED": "dep#Wrong"}}, "resolves": ["holds"]}, "rust")[0] is False
    assert judge_p1({"typeSurface": {"holds": {"dep#SHARED": "dep#Other"}}, "resolves": ["holds"]}, "rust")[0]
    t = {k: {"kind": v[0], "supers": ["dep#%s" % x for x in v[1]]} for k, v in KINDS["rust"].items()}
    assert judge_p2({"typeSurface": {"types": t}, "resolves": ["types"]}, "rust")[0]
    t["Mid4"] = {"kind": "protocol", "supers": ["dep#Grand4"]}
    assert judge_p2({"typeSurface": {"types": t}, "resolves": ["types"]}, "rust")[0] is False, "p2 kind"
    assert judge_p4({"typeSurface": {"holds": {"dep#OPT": "dep#Other"}}}, "rust")[0] is False
    assert judge_p5({"typeSurface": {"returns": {"dep#mk_impl": "dep#Sink"}, "returnsProtocol": {"dep#mk_impl": "dep#Sink"}},
                     "resolves": ["returnsProtocol"]}, "rust")[0] is False, "p5: protocol in returns"
    assert judge_p5({"typeSurface": {"returnsProtocol": {"dep#mk_impl": "dep#Sink"}}, "resolves": ["returnsProtocol"]}, "rust")[0]
    assert judge_w({"typeSurface": {"types": {"macdep#Y": {"kind": "value"}}}}, "rust", main_ok)[0], "w2: kind alone is fine"
    assert judge_p3({"typeSurface": {"adds": {"dep#Tok": ["dep#PBase"]},
                                     "types": {"dep#SubThing": {"supers": ["base#BaseTr"]}}}}, "base", "rust")[0] is False
    assert judge_p3({"typeSurface": {"adds": {"base#Tok": ["dep#PBase"]},
                                     "types": {"dep#SubThing": {"supers": ["base#BaseTr"]}}}}, "base", "rust")[0]
    full = {"typeSurface": {"types": {"Dep#PM2": {"kind": "protocol", "supers": ["Dep#PQ2"]}}}}
    ko, _ = doctor(full, "kindonly:PM2", "swift")
    assert ko["typeSurface"]["types"]["Dep#PM2"] == {"kind": "protocol"}, "kind-only doctor"
    # a consumer defaulting the missing `supers` to [] reads [Fs]: both o14 cells go 0 and must fail
    o14 = [a for a in ARMS if a[0] == "o14_kind_only"][0]
    assert not judge_gates(want_for(o14, "swift"), {"deny Env Unknown": 0, "deny Net": 1})[0]
    print("selftest: OK — %d flipped cells all fail; the u1, w, p1, p2, p3, p4 and p5 judges each fail their "
          "seeded poison and pass their clean input" % n)
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
    """Scan each package in order, each chained on every report before it. Returns {name: report path}."""
    reps = {}
    for d in order:
        name = os.path.basename(d)
        chain = [reps["base"]] if name == "dep" else ([reps[k] for k in reps] if name == "macdep" else [])
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
    base_pkg = json.load(open(reps["base"])).get("package") or "base"
    if CAL == "surface":
        # CALIBRATION ONLY: a HAND-SPELLED surface, so the arms that need one (u1, g1, c6, o6-o8, o10) can be
        # shown to construct and evaluate before any producer ports. Never used in a scored run.
        sp = {"swift": {"holds": {"Dep#Wrong.shared": "Dep#Other", "Dep#Client.shared": "Dep#Client"},
                        "types": {"Dep#PM": {"kind": "protocol", "supers": ["Dep#PA"]},
                                  "Dep#BaseO": {"kind": "open", "supers": []},
                                  "Dep#SubO": {"kind": "final", "supers": ["Dep#BaseO"]},
                                  "Dep#PSvc": {"kind": "protocol", "supers": []},
                                  "Dep#PM2": {"kind": "protocol", "supers": ["Dep#PQ2"]},
                                  "Dep#PQ2": {"kind": "protocol", "supers": ["Dep#PA2"]},
                                  "Dep#PA2": {"kind": "protocol", "supers": []},
                                  "Dep#T2": {"kind": "final", "supers": ["Dep#PA2", "Dep#PM2"]}},
                        "adds": {"Base#Tok": ["Dep#PBase"]}},
              "rust": {"holds": {"dep#SHARED": "dep#Other", "dep#CLIENT": "dep#Client"},
                       "types": {"dep#Sink": {"kind": "protocol", "supers": []}},
                       "adds": {"base#Tok": ["dep#PBase"]}}}[lang]
        dep_rep.setdefault("typeSurface", {}).update(sp)
    scratch = os.path.join(ws, lang, "doctored")
    os.makedirs(scratch, exist_ok=True)

    # Producer arms.
    results["p1_holds"] = judge_p1(dep_rep, lang)
    results["p2_types"] = judge_p2(dep_rep, lang)
    results["p3_foreign"] = judge_p3(dep_rep, base_pkg, lang)
    results["p4_wrappers"] = judge_p4(dep_rep, lang)
    results["p5_returns_protocol"] = judge_p5(dep_rep, lang)
    if lang == "rust":
        results["p6_deref"] = judge_p6(dep_rep, json.load(open(reps["depb"])), lang)
    wid = "w1_macro" if lang == "swift" else "w2_macro"
    worder, wjudged = render_w(lang, os.path.join(ws, lang, "withhold"))
    try:
        wreps = scan_chain(scanner, worder)
    except RuntimeError as e:
        return None, None, "withhold fixture: %s" % e
    wrep = json.load(open(wreps[os.path.basename(wjudged)]))
    if FAULT:
        wrep = inject_short(wrep, lang)
    results[wid] = judge_w(wrep, lang, dep_rep)

    pol_dir = os.path.join(ws, lang, "pol")
    os.makedirs(pol_dir, exist_ok=True)
    # The consumer's own spelling of every function, read ONCE from the undoctored scan — so an arm whose
    # consumer REFUSES (o3 may) can still be gated on the right scope.
    fn_names = {}

    def consumer_rows(deps, variant="main"):
        a = fixtures[variant][0]
        r = scanner.scan(a, deps=deps)
        if not r.produced:
            return None, "consumer scan produced no report (rc=%d) %s" % (r.rc, r.note), r.rc
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, "analyzed.count is 0 — a hollow report judges nothing", r.rc
        return {f.get("fn", "").replace("::", ".").split(".")[-1]: f for f in rep.get("functions") or []}, None, r.rc

    rows0, err0, _ = consumer_rows([reps["base"], reps["dep"], reps["depb"]])
    if err0:
        return None, None, "main consumer scan: " + err0
    fn_names.update({k: v["fn"] for k, v in rows0.items()})

    cache = {}

    def deps_for(arm):
        """-> (list of CANDOR_DEPS report paths | (with, without) for u1, None) or (None, why)."""
        variant, kind = arm[1], spec_of(arm, lang)
        rp = fixtures[variant][1]
        key = (variant, kind)
        if key in cache:
            return cache[key]
        out = None
        if kind is None:
            out = [rp["base"], rp["dep"], rp["depb"]]
        elif kind == "u1":
            pair, why = u1_pair(dep_rep, lang)
            if why:
                cache[key] = (None, why)
                return cache[key]
            out = tuple([rp["base"], _dump(os.path.join(scratch, "u1_%s.json" % t), d), rp["depb"]]
                        for t, d in zip(("with", "without"), pair))
        elif kind in ("beside_stale", "disagree") or kind.startswith("one_copy_"):
            # TWO COPIES, IN BOTH LOAD ORDERS: a consumer where the first copy wins passes one order and
            # goes silent in the other, so the arm is scored on both (SPEC §2 rule 1, order-independence).
            sub = {"beside_stale": "stale", "disagree": "disagree"}.get(kind) \
                or (("kindonly:" if kind.startswith("one_copy_kindonly:") else "drop_types:")
                    + kind.split(":", 1)[1])
            d, why = doctor(dep_rep, sub, lang)
            if why:
                cache[key] = (None, why)
                return cache[key]
            a_ = _dump(os.path.join(scratch, "dep.json"), dep_rep)
            b_ = _dump(os.path.join(scratch, "dep.%s-copy.json" % sub.replace(":", "-")), d)
            out = ("ORDERS", [[rp["base"], a_, b_, rp["depb"]], [rp["base"], b_, a_, rp["depb"]]])
        else:
            d, why = doctor(dep_rep, kind, lang)
            if why:
                cache[key] = (None, why)
                return cache[key]
            out = [rp["base"], _dump(os.path.join(scratch, "dep.%s.json" % kind.replace(":", "-")), d), rp["depb"]]
        cache[key] = (out, None)
        return cache[key]

    def gates_for(arm, deps, tag=""):
        rows, err, rc = consumer_rows(deps, arm[1])
        row = None
        if err:
            if not (arm[0] in REFUSABLE and rc == 2):
                return None, None, err
        else:
            row = rows.get(fn_of(arm, lang))
            if row is None:
                return None, None, "ABSENT from functions[] — the carrier alone makes it effectful"
        fn = row["fn"] if row else fn_names.get(fn_of(arm, lang))
        got = {}
        for i, pol in enumerate(sorted(want_for(arm, lang))):
            pp = os.path.join(pol_dir, "%s%s_%d.policy" % (arm[0], tag, i))
            with open(pp, "w") as f:
                f.write("%s %s\n" % (pol, fn))
            got[pol] = gate(scanner, fixtures[arm[1]][0], deps, pp)
        return row or {"inferred": ["<REFUSED exit 2>"]}, got, None

    for arm in ARMS:
        aid = arm[0]
        if (aid, lang) in ARM_NA:
            continue
        deps, why = deps_for(arm)
        if why:
            results[aid] = (False, "NOT CONSTRUCTIBLE: " + why)
            continue
        want = want_for(arm, lang)
        if arm[2] == "u1":
            row_a, got_a, err_a = gates_for(arm, deps[0], "_with")
            row_b, got_b, err_b = gates_for(arm, deps[1], "_without")
            if err_a or err_b:
                results[aid] = (False, err_a or err_b)
                continue
            ok, bad = judge_u1(row_a, got_a, row_b, got_b, want)
            results[aid] = (ok, "inferred=%s gates=%s" % (sorted(row_a.get("inferred") or []), got_a)
                            + ("" if ok else " — " + "; ".join(bad)))
            continue
        orders = deps[1] if isinstance(deps, tuple) and deps and deps[0] == "ORDERS" else [deps]
        oks, details, errs = [], [], []
        for oi, dl in enumerate(orders):
            row, got, err = gates_for(arm, dl, "_o%d" % oi)
            if err:
                errs.append(err)
                continue
            ok, bad = judge_gates(want, got)
            oks.append(ok)
            details.append(("%sinferred=%s gates=%s" % ("" if len(orders) == 1 else "order%d " % (oi + 1),
                                                       sorted(row.get("inferred") or []),
                                                       " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items()))))
                           + ("" if ok else " — " + "; ".join(bad)))
        if errs:
            results[aid] = (False, "; ".join(errs))
            continue
        results[aid] = (all(oks), " | ".join(details))
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
        print("       key is injected for every type an unseen expansion may extend (w1/w2).")
    if CAL:
        print("CALIBRATION: CANDOR_PART95_CAL=%s" % CAL)
        if CAL == "guess":
            print("  the GUESSED targets of r1-r4 (Wrong.ping, Node.ping, Holder4.tok4) are emptied: every swift")
            print("  `deny Fs` cell on r1-r4 must go red, or that cell is satisfied by something other than the guess")
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
                print("  n/a   %-19s %-6s %s" % (aid, lang, ARM_NA[key]))
                continue
            ok, detail = res[aid]
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-19s %-6s — expectation is STALE: %s" % (aid, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-19s %-6s %s" % (aid, lang, detail))
            elif key in XFAIL:
                print("  xfail %-19s %-6s %s  [%s]" % (aid, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-19s %-6s %s  [%s]" % (aid, lang, detail, WHY[aid[0]]))
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
