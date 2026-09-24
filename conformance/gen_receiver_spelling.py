#!/usr/bin/env python3
"""PART 93 — RECEIVER-SPELLING INVARIANCE, four-way.

ONE dispatch. SIX spellings of the receiver. The answer must not depend on which one you write.

WHY THIS PART EXISTS, and it is a whole day's evidence rather than a hypothesis. On 2026-09-23 four
separate rust defects were filed, closed, and found to be ONE question asked at six declaration sites:

  R556  a `let`-position `dyn`            `dyn_sig_traits` read `sig.inputs` only
  R561  a CLOSURE PARAMETER `&dyn T`      `visit_expr_closure` never asked `trait_leaves` at all
  R562  a `dyn` FIELD and a `dyn` RETURN  the erasure fact lived in crate-wide indexes
  R557  a `static`/`const` ITEM receiver  an item passes through no binding site
  R564  an Upper-initial BINDING NAME     read as a unit-struct literal

Every one read ABSENT or `eff=∅` — a ⟨0.21⟩ positive purity claim — while the SAME dispatch written as a
signature parameter resolved. One of them (R562) is a live AWS SDK HTTP dispatch entry point. And the
class is not rust's: swift's R550 was the same mistake in `FnInfo.genericBounds`, ts's R558 in a
first-class member reference, and rust's own R549 mechanism B in a function reference.

THE INVARIANT IS THE POINT. `via_param` is the CONTROL — every engine resolves it — so each other arm
differs from it in exactly one thing: how the receiver is spelled. An engine that resolves the control
and not an arm is not making a judgement about that program; it is failing to ask.

`disclosed` rather than `has`: ⟨0.35⟩ licenses COMPLETING the dispatch or DISCLOSING it. Demanding the
effect would score a licensed hedge as a failure and measure this part's preference instead of the
contract. What it forbids is SILENCE — an absent row, or a present row claiming purity.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_differential as gd      # noqa: E402
import split_arms as sa            # noqa: E402

EFFECT = "Net"

# THE FAULT IS AT THE FIXTURE, NOT THE COMPARISON — the convention `gen_chained_dispatch.py` sets, and the
# reason is that a probe which nobbles the judge proves only that the judge has an `if`. With
# CANDOR_PROBE_FAULT set the consumer's implementor is rendered PURE, so nothing in the program performs
# the effect: `via_param` — the CONTROL every engine resolves — then reads absent-or-silent and the part
# must report cells wrong through its OWN verdict. If it still prints OK, the property cannot fail.
FAULT = os.environ.get("CANDOR_PROBE_FAULT")


def _sink(lang):
    if FAULT:
        return ""
    return {
        "rust":  'let _ = std::net::TcpStream::connect("h:1");',
        "java":  'try { new java.net.Socket("h", 1); } catch (Exception e) {}',
        "ts":    'try { netm.connect(1, "h") } catch {}',
        "swift": '_ = URLSession.shared.dataTask(with: URL(string: "http://h")!);',
    }[lang]

# Every arm is a FUNCTION in ONE consumer file, not a separate fixture: the dependency, the implementor
# and the consumer text are then literally shared, so nothing but the spelling can explain a difference.
ARMS = [
    ("via_param",   "CONTROL — a signature parameter. Every engine resolves this, which is what makes "
                    "every other arm a one-variable comparison rather than a new program."),
    ("via_let",     "an annotated local binding (SOUNDNESS R556)"),
    ("via_field",   "a field typed as the abstraction (R562)"),
    ("via_return",  "the return of a local factory (R562)"),
    ("via_static",  "a static / module-level item — it passes through no binding site (R557)"),
    ("via_closure", "a closure parameter (R561)"),
    ("via_field_qualified",
                    "the SAME field, with the trait written INLINE as `dep::Q` instead of imported — the\n                     one variable that actually decides it (R577); rust only, others resolve both"),
]

# XFAIL is arm-keyed and names a ROW, never a bare engine: a PASSING xfail is a FAILURE here, so a line
# retires loudly the moment an engine closes it. Empty today — all four engines pass all six arms — and
# kept rather than deleted, because the next engine to regress lands exactly here.
XFAIL = {
    # SOUNDNESS R561/R562 — rust, and THIS PART IS HOW THE NARROWING WAS FOUND. Both rows were closed
    # 2026-09-23 and both fixes are real: with the abstraction declared LOCALLY, `via_param_field`,
    # `via_return` and `via_closure` all read `[Net]`. With the SAME six shapes over a FOREIGN
    # (chained-dependency) trait — the case ⟨0.39⟩ and cross-package scanning exist for — all three read
    # ABSENT. Measured on one fixture pair differing only in where the trait is declared, and the
    # `CANDOR_ALIAS_DEBUG` probe shows R562's own code path taking ZERO hits on the foreign arm.
    #
    # So the rows are closed for the local abstraction and open for the foreign one, which is why this
    # part uses a FOREIGN dep: a local-only fixture would have passed and reported the class fixed.
    # RETIRED 2026-09-24 by the code review of this very part. These three were declared on the belief
    # that R561/R562 were "closed for a LOCAL abstraction, open for a FOREIGN one". That was WRONG, and
    # the part's own fixture was what made it look right: it wrote the bound inline as `&dyn dep::Q`
    # while the local comparison used a bare leaf. With the trait IMPORTED all three resolve. The real
    # variable is the QUALIFICATION SPELLING at the declaration site, and it is carried below.
    # RETIRED 2026-09-24 — candor-rust `845cb32` (R577): a declaration site now carries its own crate
    # qualification, shared through one `syn::visit` that has no arm set of its own so it cannot drift
    # from the sites it serves. All four engines resolve this arm.
    #
    # AND THE ARM WAS NEVER MEASURING WHAT IT CLAIMED. Its consumer writes `use dep::Q;` at FILE scope
    # and puts the inline-qualified field in `mod noimport` below it — but rust's `use` map is FILE-scoped,
    # not module-scoped, so the submodule never escaped the import. It only ever read ABSENT because this
    # file's judge split a qualified name on `.` alone and could not find `noimport::via_field_qualified`
    # at all. A false xfail that looked exactly like the defect it was written for. Both are fixed; the
    # arm stays as a four-way regression pin for the qualification path.
    # `via_self_field` (a field reached through `self` inside an impl) is ABSENT in BOTH the local and
    # foreign arms — a smaller, separate gap recorded on R562 rather than given an arm here, because this
    # part varies the RECEIVER's spelling and that one varies the enclosing context too.
}

RUST_DEP = 'pub trait Q { fn fetch(&self) -> usize; }\n'
# THE `use` IS LOAD-BEARING AND WAS MISSING: without it `S.fetch()` does not COMPILE (`E0599` — a trait
# method needs its trait in scope), and this generator was asserting six results off a program rustc
# rejects. candor-scan is syntactic and analyses it happily, which is exactly why §E3 exists: the scan
# working is not the program building. Found by the code review of PART 93 itself.
#
# It also turned out to be the VARIABLE. Writing the bound inline as `&dyn dep::Q` makes `via_field`,
# `via_return` and `via_closure` read ABSENT; writing `use dep::Q;` + `&dyn Q` makes all six resolve —
# because `trait_fields`, `rets` and R561's closure arm record only the BARE LEAF, and the foreign branch
# is gated on `full.contains("::")` after expanding that leaf through the file's `use` map. So the arms
# below carry the IMPORTED spelling (which every engine resolves) and `via_field_qualified` carries the
# inline one, which is where the defect actually lives. R561/R562's "local vs foreign" framing was mine
# and was wrong: the local fixture happened to use a bare leaf.
RUST_APP_T = '''use dep::Q;
pub struct L;
impl Q for L { fn fetch(&self) -> usize { %s 0 } }
pub static S: L = L;
pub struct Holder { pub inner: Box<dyn Q> }
pub fn mk() -> Box<dyn Q> { Box::new(L) }
pub fn via_param(q: &dyn Q) -> usize { q.fetch() }
pub fn via_let() -> usize { let q: &dyn Q = &L; q.fetch() }
pub fn via_field(h: &Holder) -> usize { h.inner.fetch() }
pub fn via_return() -> usize { mk().fetch() }
pub fn via_static() -> usize { S.fetch() }
pub fn via_closure() -> usize { let f = |q: &dyn Q| q.fetch(); f(&L) }
// R577 — the inline-qualified spelling, in a module with NO `use` for the trait. That distinction is the
// whole arm: `trait_fields` records the bare LEAF, and the foreign branch expands it through the FILE's
// `use` map, so the same field resolves in a scope that imports the trait and vanishes in one that does
// not. A `dyn` receiver needs no import to compile (only the concrete `static` above does), so this is a
// program rustc accepts.
pub mod noimport {
    pub struct HolderQ { pub inner: Box<dyn dep::Q> }
    pub fn via_field_qualified(h: &HolderQ) -> usize { h.inner.fetch() }
}
'''

JAVA_DEP = 'package dep;\npublic interface Q { int fetch(); }\n'
JAVA_APP_T = '''package app;
public class App {
  public static class L implements dep.Q {
    public int fetch() { %s return 0; }
  }
  public static class Holder { public dep.Q inner = new L(); }
  public static final dep.Q S = new L();
  public static dep.Q mk() { return new L(); }
  public static int viaParam(dep.Q q) { return q.fetch(); }
  public static int viaLet() { dep.Q q = new L(); return q.fetch(); }
  public static int viaField(Holder h) { return h.inner.fetch(); }
  public static int viaReturn() { return mk().fetch(); }
  public static int viaStatic() { return S.fetch(); }
  public static int viaClosure() {
    java.util.function.Function<dep.Q, Integer> f = q -> q.fetch();
    return f.apply(new L());
  }
  // R577's arm: java has no inline-vs-imported distinction — the fully-qualified name IS the type —
  // so this is the same field spelling and MUST pass. It is the control that keeps rust's xfail honest.
  public static int viaFieldQualified(Holder h) { return h.inner.fetch(); }
}
'''

TS_DEP = 'export interface Q { fetch(): number }\n'
TS_APP_T = '''import * as netm from "node:net";
import { Q } from "dep";
export class L implements Q { fetch(): number { %s ; return 0 } }
export class Holder { inner: Q = new L() }
export const S: Q = new L();
export function mk(): Q { return new L() }
export function via_param(q: Q): number { return q.fetch() }
export function via_let(): number { const q: Q = new L(); return q.fetch() }
export function via_field(h: Holder): number { return h.inner.fetch() }
export function via_return(): number { return mk().fetch() }
export function via_static(): number { return S.fetch() }
export function via_closure(): number { const f = (q: Q) => q.fetch(); return f(new L()) }
export function via_field_qualified(h: Holder): number { return h.inner.fetch() }\n'''

SW_DEP = 'public protocol Q { func fetch() -> Int }\n'
SW_APP_T = '''import Dep
import Foundation
public struct L: Q {
    public init() {}
    public func fetch() -> Int { %s return 0 }
}
public struct Holder { public var inner: Q = L(); public init() {} }
public let S: Q = L()
public func mk() -> Q { return L() }
public func via_param(_ q: Q) -> Int { return q.fetch() }
public func via_let() -> Int { let q: Q = L(); return q.fetch() }
public func via_field(_ h: Holder) -> Int { return h.inner.fetch() }
public func via_return() -> Int { return mk().fetch() }
public func via_static() -> Int { return S.fetch() }
public func via_closure() -> Int { let f: (Q) -> Int = { q in q.fetch() }; return f(L()) }
public func via_field_qualified(_ h: Holder) -> Int { return h.inner.fetch() }\n'''

# The engines name the same function differently; the ARM is the question, not the identifier.
NAMES = {
    "rust":  lambda a: a,
    "ts":    lambda a: a,
    "swift": lambda a: a,
    "java":  lambda a: "via" + "".join(p.capitalize() for p in a.split("_")[1:]),
}


def judge(rows, arm, lang):
    """PRESENT, and either carrying the effect or disclosing. ABSENT is the defect this part is about."""
    want = NAMES[lang](arm)
    # SPLIT ON BOTH SEPARATORS. rust qualifies a module path with `::` and the others with `.`, so a
    # `.`-only split left `noimport::via_field_qualified` unmatched and this judge reported it ABSENT —
    # a FALSE xfail that looked exactly like the defect the arm was written for, and stayed hidden
    # because every other arm sits at file scope and has no module prefix at all. Found when a fix for
    # R577 did not retire the xfail it should have.
    def _leaf(name):
        return (name or "").replace("::", ".").split(".")[-1]
    hit = [f for f in rows if _leaf(f.get("fn")) == want]
    if not hit:
        return False, "ABSENT from functions[] — a purity claim (SPEC §2 rule 3)"
    f = hit[0]
    inf = set(f.get("inferred") or [])
    if EFFECT in inf:
        return True, "eff=[%s]" % EFFECT
    if "Unknown" in inf:
        return True, "disclosed Unknown (the ⟨0.35⟩ disjunction)"
    return False, "present but SILENT — inferred=%s, neither the effect nor a disclosure" % sorted(inf)


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def build(lang, root):
    """Lay the two packages out and return (dep_dirs, app_dir) ready to scan."""
    if lang == "rust":
        _w(os.path.join(root, "dep", "Cargo.toml"), '[package]\nname="dep"\nversion="0.0.0"\nedition="2021"\n')
        _w(os.path.join(root, "dep", "src", "lib.rs"), RUST_DEP)
        _w(os.path.join(root, "app", "Cargo.toml"),
           '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n[dependencies]\ndep={path="../dep"}\n')
        _w(os.path.join(root, "app", "src", "lib.rs"), RUST_APP_T % _sink("rust"))
        return [os.path.join(root, "dep")], os.path.join(root, "app")
    if lang == "ts":
        _w(os.path.join(root, "dep", "package.json"), '{"name":"dep","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "dep", "src", "index.ts"), TS_DEP)
        _w(os.path.join(root, "app", "package.json"), '{"name":"app","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "app", "src", "index.ts"), TS_APP_T % _sink("ts"))
        _link(os.path.join(root, "app", "node_modules", "dep"), os.path.join(root, "dep"))
        return [os.path.join(root, "dep")], os.path.join(root, "app")
    if lang == "swift":
        _w(os.path.join(root, "dep", "Package.swift"), SW_MANIFEST % dict(mod="Dep", deps="", prods=""))
        _w(os.path.join(root, "dep", "Sources", "Dep", "dep.swift"), SW_DEP)
        _w(os.path.join(root, "app", "Package.swift"),
           SW_MANIFEST % dict(mod="App", deps='.package(path: "../dep")',
                              prods='.product(name: "Dep", package: "dep")'))
        _w(os.path.join(root, "app", "Sources", "App", "app.swift"), SW_APP_T % _sink("swift"))
        return [os.path.join(root, "dep")], os.path.join(root, "app")
    # java — compile both packages together, then scan them as SEPARATE class directories, because a
    # package scanned with its sibling's classes on the same path is not a separate package at all.
    _w(os.path.join(root, "src", "dep", "Q.java"), JAVA_DEP)
    _w(os.path.join(root, "src", "app", "App.java"), JAVA_APP_T % _sink("java"))
    cls = os.path.join(root, "cls")
    os.makedirs(cls, exist_ok=True)
    srcs = []
    for d, _dd, fs in os.walk(os.path.join(root, "src")):
        srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
    c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
    if c.returncode != 0:
        raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
    import shutil
    dep_d, app_d = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
    os.makedirs(dep_d, exist_ok=True)
    os.makedirs(app_d, exist_ok=True)
    shutil.copytree(os.path.join(cls, "dep"), os.path.join(dep_d, "dep"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(cls, "app"), os.path.join(app_d, "app"), dirs_exist_ok=True)
    return [dep_d], app_d


def main():
    import tempfile
    print("=" * 100)
    print("RECEIVER-SPELLING INVARIANCE — one dispatch, six spellings, the answer must not change")
    print("  fixture : TWO packages — dep declares the abstraction, app implements it EFFECTFULLY and")
    print("            reaches the same dispatch six ways, all in ONE consumer file")
    print("  property: every arm is PRESENT and either carries %s or discloses Unknown (⟨0.35⟩)" % EFFECT)
    print("  control : via_param — a signature parameter; every other arm differs from it in one thing")
    print("=" * 100)
    if FAULT:
        # ANNOUNCED, because a fault that drifted past every live cell would otherwise look identical to a
        # property that cannot fail — `probe_check.py` requires this line and refuses the arm without it.
        print("PROBE: CANDOR_PROBE_FAULT is set — the consumer's implementor is rendered PURE, so nothing")
        print("       in the program performs %s and `via_param`, the CONTROL, must stop resolving." % EFFECT)
    bad = stale = 0
    ws = tempfile.mkdtemp(prefix="candor-recvspell-")
    for lang in ("rust", "java", "ts", "swift"):
        scanner = sa.SCANNERS[lang]()
        if not scanner.available:
            print("  %-6s -> SKIP (%s)" % (lang, scanner.err))
            continue
        root = os.path.join(ws, lang)
        os.makedirs(root, exist_ok=True)
        try:
            deps, app = build(lang, root)
        except RuntimeError as e:
            print("  %-6s -> FAIL to build the fixture: %s" % (lang, e))
            bad += 1
            continue
        dep_reports = []
        for d in deps:
            r = scanner.scan(d)
            if not r.produced:
                print("  %-6s -> FAIL: the dep scan produced no report" % lang)
                bad += 1
                break
            # `report` is the PATH the engine wrote, which is also what CANDOR_DEPS wants — passing
            # it straight through avoids a re-serialisation that could differ from what was chained.
            dep_reports.append(r.report)
        else:
            r = scanner.scan(app, deps=dep_reports)
            if not r.produced:
                print("  %-6s -> FAIL: the consumer scan produced no report" % lang)
                bad += 1
                continue
            # A HOLLOW consumer answers nothing and every arm would read ABSENT — which is exactly what
            # this part calls a defect. Refuse before reading a single arm (SOUNDNESS R242).
            rep = json.load(open(r.report))
            n = (rep.get("analyzed") or {}).get("count") or 0
            if n == 0:
                print("  %-6s -> FAIL: analyzed.count is 0 — a hollow report judges nothing" % lang)
                bad += 1
                continue
            rows = rep.get("functions") or []
            for arm, why in ARMS:
                ok, detail = judge(rows, arm, lang)
                key = (arm, lang)
                if ok and key in XFAIL:
                    print("  XFAIL ARM PASSED  %-12s %-6s — expectation is STALE: %s" % (arm, lang, XFAIL[key]))
                    stale += 1
                elif ok:
                    print("  OK    %-12s %-6s %s" % (arm, lang, detail))
                elif key in XFAIL:
                    print("  xfail %-12s %-6s %s  [%s]" % (arm, lang, detail, XFAIL[key]))
                else:
                    print("  FAIL  %-12s %-6s %s" % (arm, lang, detail))
                    print("        %s" % why)
                    bad += 1
    if stale:
        print("RECEIVER-SPELLING: %d xfail arm(s) PASSED — an expectation that has become true is a "
              "FAILURE here. Retire it in the same commit as the engine fix." % stale)
    if bad:
        print("RECEIVER-SPELLING: %d cell(s) wrong — the receiver's SPELLING decided whether a dispatch "
              "was seen. `via_param` is the control: if it resolves and another arm does not, the engine "
              "did not judge that program, it failed to ask." % bad)
    if not bad and not stale:
        print("RECEIVER-SPELLING: OK — every engine answers the same for all six spellings of one receiver")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
