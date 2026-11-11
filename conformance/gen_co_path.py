#!/usr/bin/env python3
"""PART 107 — CO-PATH UNITS, SPEC §2 ⟨0.42⟩ (under the ⟨0.40⟩ `(hash, fn)` bullet) and §6.2 Scope matching ⟨0.42⟩.

SOUNDNESS R1537 (the rust merge census — candor-scan publishes an inherent/trait pair as one unit), R1548/R1549 (a
scope matched inside a parameter list), R1550 (swift's `only` route: a permission satisfied through a disambiguator),
R1551 (swift's chained join splits a disambiguator too, and goes SILENT), R1420 (c) (the caller fabrication the merge
causes), R567 (b) (swift's chained bare call, the sin this clause's consumer half exists to prevent).

THE SHAPE. Several separately-written bodies share one fully-qualified path: a JVM or Swift overload set; in Rust an
inherent method beside a trait implementation of the same name. ⟨0.42⟩ makes each body its own unit, spelled
`<bare path>(<disambiguator>)`, never the bare path alone; makes every scope matcher keep the disambiguator inside
the LAST segment; and makes a call that names only the bare path join the UNION of the members (or the one member
it can prove), never one picked by order and never a miss read as purity.

TWO ARMS.

  H — one HAND-WRITTEN report, the same bytes for every engine, through each engine's `gate --report`. This is the
      matcher half and it is four-way: every gate reads every engine's spelling. Two co-path pairs, a JVM-dotted
      one (`bank.Bank.pay(ua.user.User)` Fs / `bank.Bank.pay(ub.user.User)` Env) and a `::` one
      (`m::S::act(tm::Tr)` Fs / `m::S::act(S)` Env), plus a unique-name control `bank.Bank.solo`. EXPECTED is
      written from the clause: the bare path binds every member, an exact disambiguated scope binds one, and a token
      that occurs only INSIDE a disambiguator binds nothing (`zeroMatch`).

  S — a SOURCE fixture per engine with a co-path set, scanned ONE-TREE and CHAINED (the producer scanned alone and
      its report handed over on CANDOR_DEPS), gated on the engine's own scan route (CANDOR_POLICY):
        java   `dep.Box.act(ua.model.Rec)` Fs / `dep.Box.act(ub.model.Rec)` pure — java's fully-qualified overload
               spelling, so the token `model` sits in the middle of the disambiguator
        swift  `Box.act(Models.Inner.Rec)` Fs / `Box.act(Int,Int)` pure, and the free pair `shell(...)` — R567 (b)
               was a free function. The members differ by ARITY so the one-tree edge is exact: with `act(Int)` beside
               it candor-swift edges a typed-argument call to BOTH overloads, and the pure overload's edge then
               reddens `only` for an unrelated reason, masking the R1550 false green (measured)
        rust   inherent `m::S::act` pure / `impl tm::Tr for S { fn act }` Fs — class (c) of R1537
        ts     NO S ARM: candor-ts has no co-path set. An overload declaration set has ONE body; an accessor pair is
               spelled `C.get x` / `C.set x`, two distinct paths (measured 2026-11-09, SOUNDNESS R1552). ts runs
               the H arm, which is the half of the clause that binds it.
      Every consumer function first reads the environment, so `deny Env <fn>` is a CARRIER: the scope is the row's
      own `fn` read back from the report, and a policy that matched nothing cannot pass a cell.

S CELLS (per engine; `w` = one tree, `c` = chained):
  units        the producer report: no entry is spelled with the bare path, the members' `fn`s are pairwise distinct,
               one carries Fs, and the §2.2 sidecar has a key for EVERY member (the pure one included) — the
               sidecar is the only channel that can show a pure member is a unit
  deny_bare    `deny Fs <bare path>` exits 1 — a policy written before the split still covers the effectful member
  eff_caller   `deny Fs <caller of the effectful member>` exits 1: w, c, and c_rev (the producer's functions[]
               REVERSED — a loader that keeps the last entry under a shared key fails one of the two orders)
  pure_caller  w only: `deny Fs <caller of the pure member>` exits 0. Chained it is NOT asserted: the clause permits
               the union where the consumer cannot prove the member, and the union over-charges by design
  tok          `deny Fs <a token inside the disambiguator>` exits 0 (java, swift; rust has no disambiguator yet)
  only_tok     `only <caller> -> <token>` exits 1, with `only <caller> -> <real owner>` exiting 0 as its control
  stale        the producer report's `candor.version` changed: `deny Fs Unknown <eff caller>` exits 1 (§2.1)
  k_split      rust only: the producer report REWRITTEN to the ⟨0.42⟩ spelling (`m::S::act(tm::Tr)`, sidecar keys
               for both members), version kept: `deny Fs <eff caller>` exits 1; version changed: `deny Fs Unknown`
               exits 1. Pins what today's rust consumer does with the spelling its producer is about to publish.

SEEDS, run every time, and each must flip a cell or the part FAILS as VACUOUS:
  seed_drop    the producer report with the effectful member's entry DELETED (what a last-wins loader keeps when the
               pure member is written last): `deny Fs <eff caller>` must exit 0 on the chained consumer, proving the
               eff_caller cells read the producer report and could fail.
CALIBRATED: CANDOR_PROBE_FAULT=1 renders the effectful member WITHOUT its Fs, so deny_bare and eff_caller go red on
every engine with an S arm. Registered in probe_check.py (java arm).
"""
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd          # noqa: E402
import gen_rung024 as G                # noqa: E402
import gen_policy_semantics as PS      # noqa: E402
import split_arms as sa                # noqa: E402

SPEC_CLAUSES = [
    ("§2 ⟨0.42⟩", "CO-PATH UNITS: SEVERAL SEPARATELY-WRITTEN BODIES UNDER ONE FULLY-QUALIFIED PATH ARE SEVERAL UNITS"),
    ("§2 ⟨0.42⟩", "no member of the set is spelled with the bare path alone"),
    ("§2 ⟨0.42⟩", "MUST keep the disambiguator inside the LAST name-segment and never split inside it"),
    ("§2 ⟨0.42⟩", "it MUST NOT pick one member by order, and a miss on the members' keys MUST NOT read as purity"),
    ("§6.2 ⟨0.42⟩", "A DISAMBIGUATOR IS PART OF THE LAST SEGMENT"),
    ("§2.1", "MUST compare `version`"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART107_NOBUILD")
S_ENGINES = ("rust", "java", "swift")

# An expectation keyed by (cell, engine), never by cell alone — engines fix their rows one at a time, and A PASSING
# XFAIL IS A FAILURE: the engine that fixes its row reddens this part and retires its own line in the same commit.
XFAIL = {
    # H arm — the matcher splits a disambiguator into path segments (fail-closed fabrication).
    ("h_tok_mid", "rust"):   "R1549 — candor-query `name_segments` (policy.rs:880 / matching.rs:38) splits inside the parameter list",
    ("h_tok_last", "rust"):  "R1549 — the same split; `User` prefix-matches the segment `User)`",
    ("h_tok_rs", "rust"):    "R1549 — the same split over a `::` disambiguator; `Tr` prefix-matches `Tr)`",
}

# =====================================================================================================
# H ARM — one hand-written report, four gates
# =====================================================================================================
PAY_A = {"fn": "bank.Bank.pay(ua.user.User)", "hash": "app#bank.Bank.pay(ua.user.User)",
         "inferred": ["Fs"], "direct": ["Fs"]}
PAY_B = {"fn": "bank.Bank.pay(ub.user.User)", "hash": "app#bank.Bank.pay(ub.user.User)",
         "inferred": ["Env"], "direct": ["Env"]}
SOLO = {"fn": "bank.Bank.solo", "hash": "app#bank.Bank.solo", "inferred": ["Fs"], "direct": ["Fs"]}
ACT_T = {"fn": "m::S::act(tm::Tr)", "hash": "app#m::S::act(tm::Tr)", "inferred": ["Fs"], "direct": ["Fs"]}
ACT_S = {"fn": "m::S::act(S)", "hash": "app#m::S::act(S)", "inferred": ["Env"], "direct": ["Env"]}
H_REPORT = {"candor": {"version": "handwritten", "spec": "0.42"}, "package": "app",
            "analyzed": {"count": 5, "digest": "0"}, "functions": [PAY_A, PAY_B, SOLO, ACT_T, ACT_S]}
K = lambda e: (e["hash"], e["fn"])     # noqa: E731


def _h(cid, policy, exit, viol=(), zero=None, why=""):
    c = PS.cell(cid, "h", policy, exit, viol=viol, zero=zero, why=why)
    return c


H_CELLS = [
    _h("h_bare_fs", "deny Fs bank.Bank.pay\n", 1, [K(PAY_A)], zero=set(),
       why="control: the bare path binds every member — the effectful one fires"),
    _h("h_bare_env", "deny Env bank.Bank.pay\n", 1, [K(PAY_B)], zero=set(),
       why="the bare path binds the OTHER member too (a policy written before the split still covers it)"),
    _h("h_exact", "deny Fs bank.Bank.pay(ua.user.User)\n", 1, [K(PAY_A)], zero=set(),
       why="a scope carrying the disambiguator binds that member"),
    _h("h_exact_other", "deny Fs bank.Bank.pay(ub.user.User)\n", 0, [], zero=set(),
       why="a scope carrying the disambiguator binds ONLY that member (Env, not Fs) — bound, so no zeroMatch"),
    _h("h_tok_first", "deny Fs ua\n", 0, [], zero={"deny Fs ua"},
       why="the first token of a parameter list is not a segment — guards a fix that splits on `(`"),
    _h("h_tok_mid", "deny Fs user\n", 0, [], zero={"deny Fs user"},
       why="a token INSIDE the disambiguator is not a segment (R1549)"),
    _h("h_tok_last", "deny Fs User\n", 0, [], zero={"deny Fs User"},
       why="the last token of the disambiguator is not a segment, and is not a prefix of one (R1549)"),
    _h("h_rs_bare", "deny Fs m::S::act\n", 1, [K(ACT_T)], zero=set(),
       why="control: the `::` pair — the bare path binds the effectful member"),
    _h("h_rs_tok_first", "deny Fs tm\n", 0, [], zero={"deny Fs tm"},
       why="a `::` inside the disambiguator is not a path separator"),
    _h("h_tok_rs", "deny Fs Tr\n", 0, [], zero={"deny Fs Tr"},
       why="a trait named inside a disambiguator is not a segment (R1549)"),
]


def run_h(engines, ws):
    """[(cell, engine, ok, detail)]"""
    out = []
    for eng in engines:
        loc = G.write_report(os.path.join(ws, "h-" + eng), eng, H_REPORT)
        for c in H_CELLS:
            rc, doc, err = PS.gate(eng, loc, c["policy"], ws, "h-%s-%s" % (eng, c["id"]))
            bad = PS.judge(PS.observe(rc, doc), c["want"])
            out.append((c["id"], eng, not bad, "; ".join(bad) if bad else "exit %s" % rc, c["why"]))
    return out


# =====================================================================================================
# S ARM — a source fixture per engine
# =====================================================================================================
def _sink(effect_id, lang):
    for e in gd.EFFECTS:
        if e["id"] == effect_id:
            return e["sink"][lang]
    raise KeyError(effect_id)


def _fs(lang):
    return "" if FAULT else _sink("fs", lang) + " "


RS_LIB = '''pub mod m {
    pub mod tm { pub trait Tr { fn act(&self) -> usize; } }
    pub struct S;
    impl S { pub fn act(&self) -> usize { 1 } }
    impl tm::Tr for S { fn act(&self) -> usize { %(FS)s2 } }
}
'''
RS_APP = '''pub fn call_pure(s: &S) -> usize { %(ENV)s s.act() }
pub fn call_eff(s: &S) -> usize { %(ENV)s <S as Tr>::act(s) }
'''
JAVA_BOX = '''package dep;
public class Box {
  public static int act(ua.model.Rec r) { %(FS)sreturn 1; }
  public static int act(ub.model.Rec r) { return 2; }
}
'''
JAVA_REC = 'package %s.model;\npublic class Rec {}\n'
JAVA_APP = '''package app;
public class App {
  public static int callEff(ua.model.Rec r) { %(ENV)s return dep.Box.act(r); }
  public static int callPure(ub.model.Rec r) { %(ENV)s return dep.Box.act(r); }
}
'''
SW_LIB = '''import Foundation
public enum Models { public enum Inner { public struct Rec { public init() {} } } }
public enum Box {
    public static func act(_ r: Models.Inner.Rec) -> Int { %(FS)sreturn 1 }
    public static func act(_ n: Int, _ m: Int) -> Int { return n + m }
}
public func shell(_ r: Models.Inner.Rec) -> Int { %(FS)sreturn 1 }
public func shell(_ n: Int, _ m: Int) -> Int { return n + m }
public enum Pad {
    public static func put(_ s: String) -> Int { %(FS)sreturn s.count }
    public static func put(_ n: Int, _ m: Int) -> Int { return n + m }
}
public func tell(_ s: String) -> Int { %(FS)sreturn s.count }
public func tell(_ n: Int, _ m: Int) -> Int { return n + m }
'''
SW_APP = '''public func callEff(_ r: Models.Inner.Rec) -> Int { %(ENV)s; return Box.act(r) }
public func callPure() -> Int { %(ENV)s; return Box.act(3, 4) }
public func freeEff(_ r: Models.Inner.Rec) -> Int { %(ENV)s; return shell(r) }
public func freePure() -> Int { %(ENV)s; return shell(3, 4) }
public func putEff() -> Int { %(ENV)s; return Pad.put("x") }
public func putPure() -> Int { %(ENV)s; return Pad.put(3, 4) }
public func tellEff() -> Int { %(ENV)s; return tell("x") }
public func tellPure() -> Int { %(ENV)s; return tell(3, 4) }
'''
SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')

# Per engine: the bare paths of the co-path sets, the (effectful caller, pure caller) leaves, the disambiguator token,
# and the real owner an `only` rule may legitimately permit.
SPEC_S = {
    "rust":  {"paths": ["m::S::act"], "callers": [("call_eff", "call_pure")], "tok": None, "owner": None},
    "java":  {"paths": ["dep.Box.act"], "callers": [("callEff", "callPure")], "tok": "model", "owner": "dep",
              "from": "app"},
    "swift": {"paths": ["Box.act", "shell", "Pad.put", "tell"],
              "callers": [("callEff", "callPure"), ("freeEff", "freePure"), ("putEff", "putPure"), ("tellEff", "tellPure")],
              "tok": "Inner", "owner": "Box", "from": "callEff"},
}
WHY_RUST_NO_TOK = ("rust: no tok/only_tok cell — candor-scan's disambiguator (R1537 (c), candor-rust f6c278e8) is the "
                   "trait LEAF or the self-type leaf, and both are also real segments of other published fns "
                   "(`m::tm::Tr::act`), so no token occurs ONLY inside a disambiguator; a rust tok cell needs a fixture "
                   "whose trait module path never carries the trait leaf as a segment")


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def render(lang, root, layout):
    """Returns (dep_dirs, app_dir). `one` has no dep dirs; its single tree is producer and consumer at once."""
    env = _sink("env", lang)
    fs = _fs(lang)
    if lang == "rust":
        cargo = '[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n'
        lib = RS_LIB % dict(FS=fs)
        app_fns = RS_APP % dict(ENV=env)
        if layout == "one":
            app = os.path.join(root, "app")
            _w(os.path.join(app, "Cargo.toml"), cargo % "app")
            _w(os.path.join(app, "src", "lib.rs"), lib + "\nuse m::{S, tm::Tr};\n" + app_fns)
            return [], app
        dep, app = os.path.join(root, "cplib"), os.path.join(root, "app")
        _w(os.path.join(dep, "Cargo.toml"), cargo % "cplib")
        _w(os.path.join(dep, "src", "lib.rs"), lib)
        _w(os.path.join(app, "Cargo.toml"), (cargo % "app") + '\n[dependencies]\ncplib={path="../cplib"}\n')
        _w(os.path.join(app, "src", "lib.rs"), "use cplib::m::{S, tm::Tr};\n" + app_fns)
        return [dep], app
    if lang == "java":
        src = os.path.join(root, "src")
        _w(os.path.join(src, "dep", "Box.java"), JAVA_BOX % dict(FS=fs))
        _w(os.path.join(src, "ua", "model", "Rec.java"), JAVA_REC % "ua")
        _w(os.path.join(src, "ub", "model", "Rec.java"), JAVA_REC % "ub")
        _w(os.path.join(src, "app", "App.java"), JAVA_APP % dict(ENV=env))
        cls = os.path.join(root, "cls")
        os.makedirs(cls, exist_ok=True)
        srcs = []
        for d, _dd, fs_ in os.walk(src):
            srcs += [os.path.join(d, f) for f in fs_ if f.endswith(".java")]
        c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
        if c.returncode != 0:
            raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
        if layout == "one":
            return [], cls
        dep_d, app_d = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
        for p in ("dep", "ua", "ub"):
            shutil.copytree(os.path.join(cls, p), os.path.join(dep_d, p), dirs_exist_ok=True)
        shutil.copytree(os.path.join(cls, "app"), os.path.join(app_d, "app"), dirs_exist_ok=True)
        return [dep_d], app_d
    # swift: a statement in a one-line body needs its own `;`
    lib = SW_LIB % dict(FS=(fs.strip() + "; ") if fs else "")
    app_fns = SW_APP % dict(ENV=env)
    if layout == "one":
        app = os.path.join(root, "app")
        _w(os.path.join(app, "Package.swift"), SW_MANIFEST % dict(mod="App", deps="", prods=""))
        _w(os.path.join(app, "Sources", "App", "lib.swift"), lib)
        _w(os.path.join(app, "Sources", "App", "app.swift"), "import Foundation\n\n" + app_fns)
        return [], app
    dep, app = os.path.join(root, "dep"), os.path.join(root, "app")
    _w(os.path.join(dep, "Package.swift"), SW_MANIFEST % dict(mod="Dep", deps="", prods=""))
    _w(os.path.join(dep, "Sources", "Dep", "lib.swift"), lib)
    _w(os.path.join(app, "Package.swift"),
       SW_MANIFEST % dict(mod="App", deps='.package(path: "../dep")', prods='.product(name: "Dep", package: "dep")'))
    _w(os.path.join(app, "Sources", "App", "app.swift"), "import Foundation\nimport Dep\n\n" + app_fns)
    return [dep], app


def build_proof(lang, app):
    """An absence-asserting control over a program that does not build is no evidence. java is compiled by render."""
    if NOBUILD or lang == "java":
        return None
    if lang == "rust":
        if not shutil.which("cargo"):
            return "SKIPPED: no cargo — the rust fixture is UNCHECKED"
        r = gd.run(["cargo", "check", "--quiet", "--offline"], cwd=app,
                   env=dict(os.environ, CARGO_TARGET_DIR=os.path.join(app, "..", "target")))
    else:
        r = gd.run(["swift", "build"], cwd=app)
    if r.returncode != 0:
        return "%s build FAILED: %s" % (lang, (r.stderr or r.stdout).decode()[:300].replace("\n", " | "))
    return None


def bare(fn):
    """The ⟨0.42⟩ bare path: `fn` with its disambiguator removed — a trailing `#<N>`, then a balanced parenthesised
    group that ENDS the name and opens directly after the last segment's name. A group that begins a segment of its
    own (candor-scan's tuple self type, `row::convert::(T1,T2)::from_row_opt`) is not a disambiguator."""
    t = re.sub(r"#\d+$", "", fn or "")
    if not t.endswith(")"):
        return t
    depth = 0
    for j in range(len(t) - 1, -1, -1):
        if t[j] == ")":
            depth += 1
        elif t[j] == "(":
            depth -= 1
            if depth == 0:
                return t[:j] if j > 0 and t[j - 1] not in ".:" else t
    return t


def _leaf(name):
    return bare(name).replace("::", ".").split(".")[-1]


def _sidecar(report_path):
    p = report_path[:-len(".json")] + ".callgraph.json"
    try:
        return json.load(open(p))
    except Exception:          # noqa: BLE001
        return None


def judge_units(report_path, paths):
    """The producer-report cell. Returns a list of problems (empty == conforms)."""
    rep = json.load(open(report_path))
    side = _sidecar(report_path)
    bad = []
    for P in paths:
        ents = [e for e in rep.get("functions") or [] if not e.get("interfaceUnion") and bare(e.get("fn")) == P]
        fns = [e.get("fn") for e in ents]
        if any(f == P for f in fns):
            bad.append("`%s` is published under the BARE path (%d entr%s) — a merged unit, not a co-path set"
                       % (P, fns.count(P), "y" if fns.count(P) == 1 else "ies"))
        if len(set(fns)) != len(fns):
            bad.append("two entries share a `fn` under `%s`: %s" % (P, sorted(fns)))
        if not any("Fs" in (e.get("inferred") or []) for e in ents):
            bad.append("no member of `%s` carries Fs" % P)
        keys = [k for k in (side or {}) if bare(k) == P]
        if side is None:
            bad.append("no §2.2 sidecar beside the report — cannot show the pure member is a unit")
        elif len(set(keys)) < 2 or P in keys:
            bad.append("sidecar keys under `%s` are %s — every member needs its own disambiguated key" % (P, sorted(keys)))
    return bad


def gate(scanner, pkgdir, deps, policy_text, pol_dir, tag):
    pp = os.path.join(pol_dir, tag + ".policy")
    with open(pp, "w") as f:
        f.write(policy_text + "\n")
    out = os.path.join(os.path.dirname(pkgdir.rstrip(os.sep)), "gate.report.json")
    scanner._clear(pkgdir, out)
    env = dict(os.environ, CANDOR_POLICY=pp)
    if deps:
        env["CANDOR_DEPS"] = " ".join(deps)
    else:
        env.pop("CANDOR_DEPS", None)
    return gd.run(scanner._argv(pkgdir, out), cwd=scanner._cwd(pkgdir), env=env).returncode


def doctor(report_path, ws, tag, fns=None, version=None, sidecar=None):
    """A copy of a producer report (and its sidecars, same basenames) in a fresh directory, transformed."""
    d = os.path.join(ws, "doctored", tag)
    os.makedirs(d, exist_ok=True)
    base = report_path[:-len(".json")]
    for suf in (".callgraph.json", ".hierarchy.json"):
        if os.path.exists(base + suf):
            shutil.copy(base + suf, os.path.join(d, os.path.basename(base) + suf))
    rep = json.load(open(report_path))
    if fns is not None:
        rep["functions"] = fns(rep.get("functions") or [])
    if version is not None:
        rep.setdefault("candor", {})["version"] = version
    if sidecar is not None:
        sp = os.path.join(d, os.path.basename(base) + ".callgraph.json")
        sc = json.load(open(sp))
        sc, count = sidecar(sc)
        json.dump(sc, open(sp, "w"))
        rep.setdefault("analyzed", {})["count"] = count
    out = os.path.join(d, os.path.basename(report_path))
    json.dump(rep, open(out, "w"), indent=1)
    return out


def rust_split(fns_list, P="m::S::act"):
    """Rewrite candor-scan's merged pair to the ⟨0.42⟩ spelling: the trait member keeps the effects, the inherent
    member is pure (absent from functions[], present in the sidecar)."""
    out, done = [], False
    for e in fns_list:
        if e.get("fn") == P and not e.get("interfaceUnion"):
            if not done:
                e = dict(e)
                e["fn"] = P + "(tm::Tr)"
                e["hash"] = e.get("hash", "").replace("#" + P, "#" + P + "(tm::Tr)")
                out.append(e)
                done = True
            continue
        out.append(e)
    return out


def rust_split_sidecar(sc, P="m::S::act"):
    sc = dict(sc)
    v = sc.pop(P, [])
    sc[P + "(tm::Tr)"] = v
    sc[P + "(S)"] = []
    return sc, len(sc)


def run_s(lang, ws):
    """[(cell, engine, ok, detail, why)], notes, err"""
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, None, scanner.err
    spec = SPEC_S[lang]
    out, notes = [], []
    reports = {}
    for layout in ("one", "split"):
        root = os.path.join(ws, lang, layout)
        os.makedirs(root, exist_ok=True)
        try:
            deps, app = render(lang, root, layout)
        except RuntimeError as e:
            return None, None, "%s/%s: %s" % (lang, layout, e)
        err = build_proof(lang, app)
        if err and err.startswith("SKIPPED"):
            notes.append("  NOTE  %s %s %s" % (lang, layout, err))
        elif err:
            return None, None, "%s (%s)" % (err, layout)
        dep_reports = []
        for d in deps:
            r = scanner.scan(d)
            if not r.produced:
                return None, None, "%s: producer scan produced no report (rc=%d) %s" % (layout, r.rc, r.note)
            dep_reports.append(r.report)
        r = scanner.scan(app, deps=dep_reports)
        if not r.produced:
            return None, None, "%s: consumer scan produced no report (rc=%d) %s" % (layout, r.rc, r.note)
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, None, "%s: analyzed.count is 0 — a hollow report judges nothing" % layout
        reports[layout] = (deps, app, dep_reports, r.report, rep)

    def row_fn(rep, leaf):
        for f in rep.get("functions") or []:
            if _leaf(f.get("fn")) == leaf and not f.get("interfaceUnion"):
                return f.get("fn")
        return None

    def cell(cid, ok, detail, why):
        out.append((cid, lang, ok, detail, why))

    # ---- one tree ------------------------------------------------------------------------------------
    deps, app, _dr, rpath, rep = reports["one"]
    pol = os.path.join(ws, lang, "pol")
    os.makedirs(pol, exist_ok=True)
    bad = judge_units(rpath, spec["paths"])
    seen = sorted(k for k in (_sidecar(rpath) or {}) if bare(k) in spec["paths"])
    cell("units", not bad, "; ".join(bad) or "every member its own disambiguated unit: %s" % seen,
         "§2 ⟨0.42⟩: each body its own unit, no member spelled bare, a sidecar key per member")
    for P in spec["paths"]:
        rc = gate(scanner, app, [], "deny Fs " + P, pol, "bare_" + _leaf(P))
        cell("deny_bare[%s]" % P, rc == 1, "`deny Fs %s` exit %d (want 1)" % (P, rc),
             "a scope that named the path before the split still covers the effectful member")
    for eff, pure in spec["callers"]:
        for leaf, want_fs, cid in ((eff, 1, "eff_caller"), (pure, 0, "pure_caller")):
            fn = row_fn(rep, leaf)
            cid = "%s[%s]" % (cid, leaf)
            if fn is None:
                cell(cid, False, "%s ABSENT from functions[] — the Env carrier is missing" % leaf, "carrier")
                continue
            c_env = gate(scanner, app, [], "deny Env " + fn, pol, "env_" + leaf)
            c_fs = gate(scanner, app, [], "deny Fs " + fn, pol, "fs_" + leaf)
            cell(cid, c_env == 1 and c_fs == want_fs,
                 "w: `deny Env %s`=%d (carrier, want 1) `deny Fs`=%d (want %d)" % (fn, c_env, c_fs, want_fs),
                 "one tree: the call resolves to the member it names" +
                 ("" if want_fs else " — a sibling's Fs here is a FABRICATION (R1420 (c))"))
    if spec["tok"]:
        rc = gate(scanner, app, [], "deny Fs " + spec["tok"], pol, "tok")
        cell("tok", rc == 0, "`deny Fs %s` exit %d (want 0)" % (spec["tok"], rc),
             "a token inside a disambiguator is not a path segment (fail-closed direction)")
        frm = spec["from"]
        c_tok = gate(scanner, app, [], "only %s -> %s" % (frm, spec["tok"]), pol, "only_tok")
        c_own = gate(scanner, app, [], "only %s -> %s" % (frm, spec["owner"]), pol, "only_own")
        cell("only_tok", c_tok == 1 and c_own == 0,
             "`only %s -> %s`=%d (want 1) control `only %s -> %s`=%d (want 0)"
             % (frm, spec["tok"], c_tok, frm, spec["owner"], c_own),
             "a permission is never satisfied through a disambiguator — the SILENT direction")
    else:
        notes.append("  NOTE  " + WHY_RUST_NO_TOK)

    # ---- chained ---------------------------------------------------------------------------------------
    deps, app, dep_reports, rpath, rep = reports["split"]
    prod = dep_reports[0]
    bad = judge_units(prod, spec["paths"])
    seen = sorted(k for k in (_sidecar(prod) or {}) if bare(k) in spec["paths"])
    cell("units_c", not bad, "; ".join(bad) or "the producer scanned alone: every member its own unit: %s" % seen,
         "§2 ⟨0.42⟩ over the producer scanned ALONE")

    base = {}

    def eff_cells(cid0, dep_list, policy_effects="Fs", want=1, label=""):
        for eff, _pure in spec["callers"]:
            cid = "%s[%s]" % (cid0, eff)
            fn = row_fn(rep, eff)
            if fn is None:
                cell(cid, False, "%s ABSENT from the chained consumer — the Env carrier is missing" % eff, "carrier")
                continue
            c_env = gate(scanner, app, dep_list, "deny Env " + fn, pol, "c_env_" + eff + cid0)
            c = gate(scanner, app, dep_list, "deny %s %s" % (policy_effects, fn), pol, "c_" + eff + cid0)
            if cid0 == "eff_caller_c":
                base[eff] = c
            cell(cid, c_env == 1 and c == want,
                 "%s`deny Env %s`=%d (carrier) `deny %s`=%d (want %d)" % (label, fn, c_env, policy_effects, c, want),
                 "chained: a call naming the bare path joins the union (or the proven member), never a miss")

    eff_cells("eff_caller_c", dep_reports)
    rev = doctor(prod, ws, lang + "-rev", fns=lambda fs: list(reversed(fs)))
    eff_cells("eff_caller_c_rev", [rev], label="producer reversed: ")
    stale = doctor(prod, ws, lang + "-stale", version="candor-part107-other-build")
    eff_cells("stale", [stale], policy_effects="Fs Unknown", label="producer from another build: ")
    for eff, pure in spec["callers"]:
        fn = row_fn(rep, pure)
        if fn:
            c = gate(scanner, app, dep_reports, "deny Fs " + fn, pol, "c_pure_" + pure)
            notes.append("  INFO  %s c pure_caller %s `deny Fs`=%d (not asserted: the union is permitted chained)"
                         % (lang, pure, c))
    if lang == "rust":
        k = doctor(prod, ws, "rust-k", fns=rust_split, sidecar=rust_split_sidecar)
        eff_cells("k_split", [k], label="producer rewritten to ⟨0.42⟩: ")
        ks = doctor(k, ws, "rust-k-stale", version="candor-part107-other-build")
        eff_cells("k_split_stale", [ks], policy_effects="Fs Unknown", label="⟨0.42⟩ producer, other build: ")

    # ---- the seed: the chained eff cells must be able to fail ---------------------------------------------
    paths = spec["paths"]
    leaves = {_leaf(P) for P in paths}
    # Every entry under the member's LEAF that carries Fs goes — the member's own entry and, for rust, the trait's
    # union entry (`m::tm::Tr::act`), which also answers the UFCS call; leaving it would make the seed prove nothing
    # about the member's own entry.
    dropped = doctor(prod, ws, lang + "-drop",
                     fns=lambda fs: [e for e in fs if not (_leaf(e.get("fn")) in leaves
                                                            and "Fs" in (e.get("inferred") or []))])
    flipped = 0
    for eff, _pure in spec["callers"]:
        fn = row_fn(rep, eff)
        if fn is None:
            continue
        if base.get(eff) != 1:
            # The seed proves a cell CAN fail by flipping a 1 to 0; over a cell that already reads 0 it proves nothing.
            notes.append("  NOTE  %s seed not applicable to %s: its chained eff cell already reads %s"
                         % (lang, eff, base.get(eff)))
            continue
        c = gate(scanner, app, [dropped], "deny Fs " + fn, pol, "seed_" + eff)
        flipped += 1
        out.append(("seed_drop[%s]" % eff, lang, c == 0,
                    "effectful member DELETED from the producer: `deny Fs %s`=%d (want 0)" % (fn, c),
                    "SEED: the chained eff cell must be able to fail — it reads the producer report"))
    if not flipped:
        out.append(("seed_drop", lang, False, "no chained eff cell read 1, so no seed could flip — the chained "
                    "half of this engine's S arm is UNCALIBRATED", "SEED: at least one chained cell must be live"))
    return out, notes, None


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    print("=" * 100)
    print("CO-PATH UNITS ⟨0.42⟩ — several bodies under one fully-qualified path are several units, each `fn` carries a")
    print("disambiguator on its LAST segment, no matcher splits inside it, and a bare-path call joins the union")
    print("  H arm : one hand-written report, four `gate --report`s (the matcher half, four-way)")
    print("  S arm : rust (inherent/trait), java and swift (overloads), one tree and chained; ts has no co-path set")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the effectful member is rendered WITHOUT its Fs, so deny_bare and")
        print("       eff_caller must go red on every engine with an S arm.")
    if NOBUILD:
        print("NOTE: CANDOR_PART107_NOBUILD is set — fixtures were NOT built; this run is for iteration only.")
    ws = tempfile.mkdtemp(prefix="candor-part107-")
    bad = stale = live = xf = 0
    rows = []
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in G.ENGINES if G.installed(e) and not G.alive(e) and (only is None or e == only)]
        for e in broken:
            print("  %-6s -> BROKEN: installed but not responding" % e)
            bad += 1
        for (cid, eng), row in XFAIL.items():
            assert eng in G.ENGINES and re.search(r"\bR\d+", row), "bad XFAIL entry %r" % ((cid, eng),)
        rows += run_h(engines, ws)
        for lang in S_ENGINES:
            if only is not None and lang != only:
                continue
            res, notes, err = run_s(lang, ws)
            if err:
                if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                    print("  %-6s -> SKIP S arm (%s)" % (lang, err))
                else:
                    print("  %-6s -> BROKEN S arm: %s" % (lang, err))
                    bad += 1
                continue
            live += 1
            for n in notes:
                print(n)
            rows += res
        live += len(engines)
        if not engines:
            print("CO-PATH: no engine available — NOT a pass")
            return 2
        for cid, eng, ok, detail, why in rows:
            key = (cid, eng)
            # A chained `units_c` shares its engine's xfail with the one-tree `units` cell: one producer defect.
            xk = key if key in XFAIL else ((cid[:-2], eng) if cid.endswith("_c") and (cid[:-2], eng) in XFAIL else None)
            if ok and xk:
                print("  XFAIL ARM PASSED  %-18s %-6s — expectation is STALE: %s" % (cid, eng, XFAIL[xk]))
                stale += 1
            elif ok:
                print("  OK    %-18s %-6s %s" % (cid, eng, detail))
            elif xk:
                xf += 1
                print("  xfail %-18s %-6s %s  [%s]" % (cid, eng, detail, XFAIL[xk].split(" — ")[0]))
            else:
                print("  FAIL  %-18s %-6s %s  [%s]" % (cid, eng, detail, why))
                bad += 1
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    if stale:
        print("CO-PATH: %d xfail arm(s) PASSED — retire the line in the same commit as the engine fix "
              "(SOUNDNESS R1420/R1537/R1549/R1550/R1551)." % stale)
    if bad:
        print("CO-PATH: %d cell(s) wrong — SPEC §2 ⟨0.42⟩ / §6.2 ⟨0.42⟩" % bad)
    if not bad and not stale:
        seeds = sum(1 for r in rows if r[0].startswith("seed_drop"))
        print("CO-PATH: OK — %d cell(s), %d declared xfail, %d seed cell(s) flipped" % (len(rows), xf, seeds))
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
