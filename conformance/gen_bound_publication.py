#!/usr/bin/env python3
"""PART 103 — A UNION PAST THE BOUNDED-CHA LIMIT IS PUBLISHED WITH ITS HEDGE, NEVER PURE, NEVER OMITTED, FOUR-WAY.
SPEC §4 ⟨0.40⟩ (the bound-counts-implementors paragraph and its fallback), §3.1 ⟨0.40⟩ (the union's own dispatch hedge).

The ⟨0.40⟩ fallback says a chained consumer that cannot count a dependency's implementors is no more resolved than
what the dependency PUBLISHES under the member's key. That is sound against the truth only if publication honours the
bound (Fable REVIEW4 C4-E1). The neighbour case is the one this part pins: a member with MORE THAN 12 implementors, ALL
of them pure. In-scan, the bounded-CHA paragraph makes that dispatch read `Unknown` ("MUST otherwise read Unknown"); a
producer that published a PURE union for it — or omitted the union because it is pure — would hand every chained
consumer a purity claim the producer's own scan does not make.

    dep:  abstraction Sink { put }, implemented by K1..K<N>, every `put` pure
    app:  c_b(s: Sink) { <Env>; s.put() }   -- the consumer has no implementor of its own

Arms: `w_<N>` one tree (the engine's own in-scan answer), `c_<N>` chained (dependency scanned alone, report handed over).
  N = 13  DEFECT/REFERENCE — past the bound: `deny Unknown` MUST fire, chained exactly as in one tree.
  N = 12  CONTROL — within the bound, every implementor pure: `deny Unknown` MUST stay 0 (PART 92 `c3_pure_only`'s
          shape); a fix that hedges every dependency dispatch reddens here.
  `deny Env` fires on every cell — the carrier that proves the scope matched the row.
Nothing is executed: every implementor is pure, so there is no effect to observe; the property is the DISCLOSURE of an
indeterminacy the SPEC requires, judged against the engine's own one-tree answer.

The producer's union entry for Sink.put is PRINTED per engine (published or not, inferred, unknownWhy), not asserted:
the part asserts the property at the consumer, as PARTs 92, 94, 100 and 102 do.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402
import split_arms as sa            # noqa: E402

SPEC_CLAUSES = [
    ("§4 bounded-CHA", "visible implementor, too many, or an ambiguous name is disclosed indeterminacy, never silent purity"),
    ("§4 ⟨0.40⟩", "A UNION FOR A MEMBER WHOSE VISIBLE IMPLEMENTORS EXCEED THE BOUND IS PUBLISHED BROAD"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")   # the 13-implementor fixture is rendered with 12: the w_13 REFERENCE goes red
ENGINES = ("rust", "java", "ts", "swift")
SIZES = (13, 12)
WANT = {13: {"deny Env": 1, "deny Unknown": 1}, 12: {"deny Env": 1, "deny Unknown": 0}}
WHY = {13: "past the bound with every implementor pure: the dispatch MUST read Unknown (§4 bounded-CHA), chained as "
           "in one tree — a pure or omitted union here is a purity claim the producer's own scan does not make",
       12: "CONTROL: within the bound and every implementor pure — an Unknown here is a hedge on 'a dispatch occurred'"}

XFAIL = {
    ("c_13", "rust"):
        "R1367 — SILENT: the producer publishes the union past the bound PURE (`inferred: []`), and the consumer trusts it",
    ("c_13", "swift"):
        "R1368 — SILENT: the producer does not publish the union past the bound, and the consumer reads pure",
    ("c_12", "ts"):
        "R1369 — NOTSILENT: the producer omits the pure narrow union, and the consumer hedges on the missing key",
}


def n_impls(size):
    return 12 if (FAULT and size == 13) else size


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


def env(lang):
    for e in gd.EFFECTS:
        if e["id"] == "env":
            return e["sink"][lang]


def render(lang, root, layout, size):
    """Returns (dep_dir or None, app_dir). `one` lays dep and app out as one package."""
    n = n_impls(size)
    E = env(lang)
    if lang == "rust":
        lib = "pub trait Sink { fn put(&self) -> i32; }\n" + "".join(
            "pub struct K%d;\nimpl Sink for K%d { fn put(&self) -> i32 { %d } }\n" % (k, k, k) for k in range(1, n + 1))
        fn = "pub fn c_b<S: Sink>(s: &S) -> i32 { %s s.put() }\n" % E
        cargo = '[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n'
        if layout == "one":
            _w(os.path.join(root, "app", "Cargo.toml"), cargo % "app")
            _w(os.path.join(root, "app", "src", "lib.rs"), lib + "\n" + fn)
            return None, os.path.join(root, "app")
        _w(os.path.join(root, "dep", "Cargo.toml"), cargo % "dep")
        _w(os.path.join(root, "dep", "src", "lib.rs"), lib)
        _w(os.path.join(root, "app", "Cargo.toml"), (cargo % "app") + '\n[dependencies]\ndep={path="../dep"}\n')
        _w(os.path.join(root, "app", "src", "lib.rs"), "use dep::Sink;\n\n" + fn)
        return os.path.join(root, "dep"), os.path.join(root, "app")
    if lang == "java":
        src = os.path.join(root, "src")
        _w(os.path.join(src, "api", "Sink.java"), "package api;\npublic interface Sink { int put(); }\n")
        for k in range(1, n + 1):
            _w(os.path.join(src, "api", "K%d.java" % k),
               "package api;\npublic class K%d implements Sink { public int put() { return %d; } }\n" % (k, k))
        _w(os.path.join(src, "app", "App.java"),
           "package app;\npublic class App {\n  public static int c_b(api.Sink s) { %s return s.put(); }\n}\n" % E)
        cls = os.path.join(root, "cls")
        os.makedirs(cls, exist_ok=True)
        srcs = [os.path.join(d, f) for d, _x, fs in os.walk(src) for f in fs if f.endswith(".java")]
        c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
        if c.returncode != 0:
            raise RuntimeError("javac failed: " + c.stderr.decode()[:300])
        if layout == "one":
            return None, cls
        dd, ad = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
        shutil.copytree(os.path.join(cls, "api"), os.path.join(dd, "api"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(cls, "app"), os.path.join(ad, "app"), dirs_exist_ok=True)
        return dd, ad
    if lang == "ts":
        lib = "export interface Sink { put(): number; }\n" + "".join(
            "export class K%d implements Sink { put(): number { return %d; } }\n" % (k, k) for k in range(1, n + 1))
        fn = "export function c_b(s: Sink): number { %s return s.put(); }\n" % E
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        if layout == "one":
            app = os.path.join(root, "app")
            _w(os.path.join(app, "package.json"), '{"name":"app","version":"0.0.0","main":"src/index.ts"}\n')
            _w(os.path.join(app, "src", "dep.ts"), lib)
            _w(os.path.join(app, "src", "index.ts"), 'import { type Sink } from "./dep.js";\nexport * from "./dep.js";\n\n' + fn)
            if os.path.isdir(types):
                _link(os.path.join(app, "node_modules", "@types"), types)
            return None, app
        dep, app = os.path.join(root, "dep"), os.path.join(root, "app")
        _w(os.path.join(dep, "package.json"), '{"name":"dep","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(dep, "src", "index.ts"), lib)
        _w(os.path.join(app, "package.json"),
           '{"name":"app","version":"0.0.0","main":"src/index.ts","dependencies":{"dep":"file:../dep"}}\n')
        _w(os.path.join(app, "src", "index.ts"), 'import { type Sink } from "dep";\n\n' + fn)
        _link(os.path.join(app, "node_modules", "dep"), dep)
        if os.path.isdir(types):
            for p in (dep, app):
                _link(os.path.join(p, "node_modules", "@types"), types)
        return dep, app
    lib = "public protocol Sink { func put() -> Int }\n" + "".join(
        "public struct K%d: Sink { public init() {}\n    public func put() -> Int { %d } }\n" % (k, k) for k in range(1, n + 1))
    fn = "public func c_b(_ s: any Sink) -> Int {\n    %s\n    return s.put()\n}\n" % E
    man = ('// swift-tools-version:5.9\nimport PackageDescription\n'
           'let package = Package(name: "%(m)s", products: [.library(name: "%(m)s", targets: ["%(m)s"])], '
           'dependencies: [%(d)s], targets: [.target(name: "%(m)s", dependencies: [%(p)s])])\n')
    if layout == "one":
        app = os.path.join(root, "app")
        _w(os.path.join(app, "Package.swift"), man % dict(m="App", d="", p=""))
        _w(os.path.join(app, "Sources", "App", "dep.swift"), lib)
        _w(os.path.join(app, "Sources", "App", "app.swift"), "import Foundation\n\n" + fn)
        return None, app
    dep, app = os.path.join(root, "dep"), os.path.join(root, "app")
    _w(os.path.join(dep, "Package.swift"), man % dict(m="Dep", d="", p=""))
    _w(os.path.join(dep, "Sources", "Dep", "lib.swift"), lib)
    _w(os.path.join(app, "Package.swift"), man % dict(m="App", d='.package(path: "../dep")',
                                                      p='.product(name: "Dep", package: "dep")'))
    _w(os.path.join(app, "Sources", "App", "app.swift"), "import Foundation\nimport Dep\n\n" + fn)
    return dep, app


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
    return (name or "").replace("::", ".").split(".")[-1]


def run_engine(lang, ws, diag):
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, scanner.err
    res = {}
    for size in SIZES:
        for layout in ("one", "split"):
            arm = "%s_%d" % ("w" if layout == "one" else "c", size)
            root = os.path.join(ws, lang, arm)
            try:
                dep, app = render(lang, root, layout, size)
            except RuntimeError as e:
                return None, "%s: %s" % (arm, e)
            deps = []
            if dep:
                r = scanner.scan(dep)
                if not r.produced:
                    return None, "%s: dependency scan produced no report (rc=%d) %s" % (arm, r.rc, r.note)
                keep = os.path.join(root, "dep.report.json")
                shutil.copy(r.report, keep)
                deps = [keep]
                un = [f for f in json.load(open(keep)).get("functions") or []
                      if f.get("interfaceUnion") and _leaf(f.get("fn")) == "put"]
                diag.append("  [%s %s] Sink.put union: %s" % (lang, arm, "; ".join(
                    "inferred=%s why=%s" % (f.get("inferred"), f.get("unknownWhy")) for f in un) or "NOT PUBLISHED"))
            r = scanner.scan(app, deps=deps)
            if not r.produced:
                return None, "%s: consumer scan produced no report (rc=%d) %s" % (arm, r.rc, r.note)
            rep = json.load(open(r.report))
            if not ((rep.get("analyzed") or {}).get("count") or 0):
                return None, "%s: analyzed.count is 0 — a hollow report judges nothing" % arm
            row = next((f for f in rep.get("functions") or [] if _leaf(f.get("fn")) == "c_b"), None)
            if row is None:
                res[arm] = (False, "ABSENT from functions[] — the Env carrier is missing, a purity claim", size)
                continue
            got, bad = {}, []
            for i, (pol, want) in enumerate(sorted(WANT[size].items())):
                pp = os.path.join(root, "p%d.policy" % i)
                with open(pp, "w") as f:
                    f.write("%s %s\n" % (pol, row["fn"]))
                rc = gate(scanner, app, deps, pp)
                got[pol] = rc
                if rc != want:
                    bad.append("`%s` exit %d want %d" % (pol, rc, want))
            res[arm] = (not bad, "inferred=%s why=%s gates=%s%s" % (
                sorted(row.get("inferred") or []), row.get("unknownWhy"),
                " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items())),
                "" if not bad else " — " + "; ".join(bad)), size)
    return res, None


def main():
    import tempfile
    print("=" * 100)
    print("BOUND PUBLICATION §4 ⟨0.40⟩ — a union past the bounded-CHA limit is published with its hedge, never pure,")
    print("never omitted: 13 PURE implementors of one member read Unknown chained, as in one tree; 12 read pure")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the 13-implementor fixture is rendered with 12, so the w_13 REFERENCE")
        print("       arm, which every engine passes clean, must go red.")
    only = [sys.argv[sys.argv.index("--engine") + 1]] if "--engine" in sys.argv[1:] else []
    ws = tempfile.mkdtemp(prefix="candor-part103-")
    bad = stale = live = 0
    diag = []
    for lang in ENGINES:
        if only and lang not in only:
            continue
        res, err = run_engine(lang, ws, diag)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                print("  %-6s -> SKIP (%s)" % (lang, err))
            else:
                print("  %-6s -> BROKEN: %s" % (lang, err))
                bad += 1
            continue
        live += 1
        for arm in ("w_13", "c_13", "w_12", "c_12"):
            ok, detail, size = res[arm]
            key = (arm, lang)
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-6s %-6s — expectation is STALE: %s" % (arm, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-6s %-6s %s" % (arm, lang, detail))
            elif key in XFAIL:
                print("  xfail %-6s %-6s %s  [%s]" % (arm, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-6s %-6s %s  [%s]" % (arm, lang, detail, WHY[size]))
                bad += 1
    print("  producer union entries (diagnostic, not asserted):")
    for d in diag:
        print(d)
    shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("BOUND-PUBLICATION: no engine available — NOT a pass")
        return 2
    if stale:
        print("BOUND-PUBLICATION: %d xfail arm(s) PASSED — retire them in the same commit as the engine fix." % stale)
    if bad:
        print("BOUND-PUBLICATION: %d cell(s) wrong — see SPEC §4 ⟨0.40⟩ (bound publication)" % bad)
    if not bad and not stale:
        print("BOUND-PUBLICATION: OK — every reference hedges past the bound, every control stays pure, and every open "
              "defect cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
