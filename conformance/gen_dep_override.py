#!/usr/bin/env python3
"""PART 94 — A CHAINED DEPENDENCY'S OWN SUBCLASS OVERRIDES, three-way (java, ts, swift), SPEC §4 ⟨0.39⟩.

SOUNDNESS R867. A call on a chained dependency's NON-FINAL class misses the overrides in that
dependency's own subclasses:

    dep:  class BaseO { m() { Fs } }      class SubO extends BaseO { override m() { Env } }
    app:  viaTyped(b: BaseO) { b.m() }    -- executed with a SubO: the program reads the environment

The chained consumer reads `[Fs]` — `BaseO.m`'s body alone — and `deny Env` and `deny Env Unknown` BOTH
exit 0. The same three engines, handed the SAME source as ONE package, read `[Env, Fs]` and both gates
exit 1. So chaining does not merely fail to improve the answer: it DELETES an effect the engine's own
unchained analysis attributes. That is the shape ⟨0.39⟩ was written against — *"A mechanism that makes
reports better must not make silence cheaper."*

WHY THIS IS A ⟨0.39⟩ OBLIGATION AND NOT A NEW ONE — the scope argument, made in SPEC's own words:

  1. ⟨0.39⟩'s headline binds "EVERY IMPLEMENTOR VISIBLE TO THE CONSUMER — its own and any chained
     report's". `SubO.m` is a row in the chained report the consumer reads. It is visible.
  2. "Implementor" is not defined afresh there: the clause opens by answering the bounded-CHA paragraph
     directly above it ("The paragraph above calls the invisible downstream implementor 'the accepted
     trade'"), and that paragraph's abstraction list is "a Rust `dyn`/`impl`/generic-bound trait, a TS
     interface, a JVM interface/supertype, a Swift protocol/class". A JVM SUPERTYPE and a Swift CLASS
     are abstractions there, and an overriding subclass is one of their implementors in the CHA sense
     the paragraph names. The reference engine's own unchained answer is that CHA union.
  3. What the clause does NOT spell out is a WIRE ROUTE for class overrides: §2's `interfaceUnion` is
     worded for "a value typed as an interface/protocol", and obligation 2 is about FOREIGN abstractions.
     This part therefore asserts the clause's PROPERTY at the consumer (as PART 92 does) and names no
     route — a consumer-side hierarchy walk, a producer union entry, whatever the engine chooses.

WHY THE ASSERTION IS A GATE EXIT AND NOT A ROW. The user-visible cost of this defect is that two gates
pass over code that performs `Env`; that is what this part pins. `deny Env` must FIRE (the effect must
be carried — a hedge does not satisfy "MUST CARRY THE EFFECTS", so `deny Env Unknown` alone is not
enough), and `deny Fs` is asserted on every cell as the CARRIER: the base body's own effect, which proves
the chained report reached the consumer and the scope names the row. Without it every `exit 0` below
could be a policy that matched nothing.

THE ARMS, per engine. Every consumer function is BYTE-IDENTICAL between the `o*` arms and the `k*` arms;
only the dependency moves (asserted, not trusted).

  w*  REFERENCE — dependency and consumer scanned as ONE package. Every engine attributes `Env` here
      today. It is what makes "chaining deletes the effect" a measurement, and it is the arm the
      CANDOR_PROBE_FAULT injection reddens.
  o*  DEFECT — chained, and the dependency's own `SubO` overrides `m` with `Env`. Must carry `Env`.
  k*  CONTROL — chained, and `SubO` does NOT override `m`: its `Env` lives in a sibling method `n` the
      consumer never reaches. Must stay `deny Env` = 0 AND `deny Env Unknown` = 0. This is the
      fabrication guard (an engine that unions every subclass's effects, or hedges on any non-final
      dependency class, reddens here and nowhere else), and its `Env` sink is what makes that `hasnt`
      reachable rather than vacuous. `deny Env Unknown` = 0 rests on SPEC §4's inherited-member rule:
      a member the subclass does not override "is a resolved call, not an `Unknown`".

  x1 typed parameter      viaTyped(b: BaseO) { b.m() }
  x2 factory, chained     viaChain() { mkO().m() }        (java: the static factory `BaseO.make()`)
  x3 factory, bound       viaBound() { let b = mkO(); b.m() }

RUST IS DECLARED N/A, NOT SKIPPED: Rust has no class inheritance. A method call on a concrete struct is
statically dispatched to exactly one body, and dynamic dispatch exists only through a trait — which is
PART 92's subject, not this one's. There is no Rust program with this shape to write.

THE XFAIL TABLE. java, ts and swift all fail every `o*` arm today (executed, R867). Each is declared per
(arm, engine), and A PASSING XFAIL IS A FAILURE: the engine that fixes R867 reddens this part and
retires its own lines in the same commit.
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
    ("§4 ⟨0.39⟩", "A CHAINED CONSUMER'S INHERITED SIGNATURE MUST CARRY THE EFFECTS OF EVERY IMPLEMENTOR "
                  "VISIBLE TO THE CONSUMER — its own and any chained report's"),
    ("§4 bounded-CHA", "a TS interface, a JVM interface/supertype, a Swift protocol/class"),
    ("§4 ⟨0.39⟩", "A mechanism that makes reports better must not make silence cheaper."),
    ("§4 inherited member", "it lands on that inherited body, whose effects MUST be attributed"),
]

# THE FAULT IS AT THE FIXTURE. With CANDOR_PROBE_FAULT set, `SubO.m`'s override is rendered with NO
# effect, so nothing in the program performs `Env` through `m` — the `w*` REFERENCE arms, which every
# engine passes today, must then go red through this part's own verdict. If they do not, the property
# cannot fail. (The `o*` arms are xfailed and cannot carry the probe.)
FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART94_NOBUILD")

ENGINES = ("java", "ts", "swift")
RUST_NA = ("Rust has no class inheritance — a method on a concrete type has exactly one body, and "
           "dynamic dispatch exists only through a trait, which PART 92 pins")

FUNCS = ("viaTyped", "viaChain", "viaBound")
ARMS = [
    # id,          fixture,   fn,         want {policy-effects: expected rc}
    ("w1_typed",   "whole",   "viaTyped", "ref"),
    ("w2_chain",   "whole",   "viaChain", "ref"),
    ("w3_bound",   "whole",   "viaBound", "ref"),
    ("o1_typed",   "override", "viaTyped", "carry"),
    ("o2_chain",   "override", "viaChain", "carry"),
    ("o3_bound",   "override", "viaBound", "carry"),
    ("k1_typed",   "sibling", "viaTyped", "control"),
    ("k2_chain",   "sibling", "viaChain", "control"),
    ("k3_bound",   "sibling", "viaBound", "control"),
]
# policy text -> expected exit code, per kind. `deny Fs` is the CARRIER on every arm (see header).
WANT = {
    "ref":     {"deny Env": 1, "deny Env Unknown": 1, "deny Fs": 1},
    "carry":   {"deny Env": 1, "deny Env Unknown": 1, "deny Fs": 1},
    "control": {"deny Env": 0, "deny Env Unknown": 0, "deny Fs": 1},
}
WHY = {
    "ref":     "REFERENCE: one package — the engine's own unchained answer carries the override's Env",
    "carry":   "DEFECT (R867): a chained dependency's own subclass override is an implementor visible to "
               "the consumer, and its Env MUST be carried",
    "control": "CONTROL: SubO does not override m — its Env is unreachable, so neither the effect nor a "
               "hedge may appear",
}

# An expectation keyed by (arm, engine), never by arm alone — one engine will fix this first.
XFAIL = {
}


# =====================================================================================================
# THE FIXTURE. `variant` is "override" (SubO overrides m with Env) or "sibling" (SubO declares n with
# Env and inherits m). The consumer text below is shared by both and never depends on the variant.
# =====================================================================================================
def _env_sink(lang):
    return {
        "java":  'System.getenv("HOME");',
        "ts":    'void process.env.HOME;',
        "swift": '_ = ProcessInfo.processInfo.environment["HOME"]',
    }[lang]


FS_SINK = {
    "java":  'new java.io.File("/tmp").exists();',
    "ts":    'fs.existsSync("/tmp");',
    "swift": '_ = FileManager.default.fileExists(atPath: "/tmp")',
}


def _override_body(lang, variant):
    """The body of SubO's override of m — present only in the override variant, emptied by the fault."""
    return "" if FAULT else _env_sink(lang)


def java_dep(variant):
    if variant == "sibling":
        sub = ('package dep;\npublic class SubO extends BaseO {\n'
               '  public void n() { %s }\n}\n' % _env_sink("java"))
    else:
        sub = ('package dep;\npublic class SubO extends BaseO {\n'
               '  @Override public void m() { %s }\n}\n' % _override_body("java", variant))
    base = ('package dep;\npublic class BaseO {\n'
            '  public void m() { %s }\n'
            '  public static BaseO make() { return new SubO(); }\n}\n' % FS_SINK["java"])
    return {"BaseO.java": base, "SubO.java": sub}


JAVA_APP = '''package app;
import dep.BaseO;
public class App {
  public static void viaTyped(BaseO b) { b.m(); }
  public static void viaChain() { BaseO.make().m(); }
  public static void viaBound() { BaseO b = BaseO.make(); b.m(); }
}
'''


def ts_dep(variant):
    if variant == "sibling":
        sub = 'export class SubO extends BaseO { n(): void { %s } }\n' % _env_sink("ts")
    else:
        sub = 'export class SubO extends BaseO { m(): void { %s } }\n' % _override_body("ts", variant)
    return ('import * as fs from "node:fs";\n'
            'export class BaseO { m(): void { %s } }\n' % FS_SINK["ts"]
            + sub
            + 'export function mkO(): BaseO { return new SubO(); }\n')


TS_APP = '''import { BaseO, mkO } from "%s";
export function viaTyped(b: BaseO): void { b.m(); }
export function viaChain(): void { mkO().m(); }
export function viaBound(): void { const b = mkO(); b.m(); }
'''


def swift_dep(variant):
    if variant == "sibling":
        sub = ('public final class SubO: BaseO {\n    public override init() { super.init() }\n'
               '    public func n() { %s }\n}\n' % _env_sink("swift"))
    else:
        sub = ('public final class SubO: BaseO {\n    public override init() { super.init() }\n'
               '    public override func m() { %s }\n}\n' % _override_body("swift", variant))
    return ('import Foundation\n'
            'open class BaseO {\n    public init() {}\n    open func m() { %s }\n}\n' % FS_SINK["swift"]
            + sub
            + 'public func mkO() -> BaseO { SubO() }\n')


SW_APP = '''%spublic func viaTyped(_ b: BaseO) { b.m() }
public func viaChain() { mkO().m() }
public func viaBound() { let b = mkO(); b.m() }
'''

SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


def render(lang, root, fixture):
    """Lay the fixture out. Returns (dep_dirs, app_dir, consumer_text). `whole` has no dep dirs."""
    variant = "override" if fixture in ("whole", "override") else "sibling"
    if lang == "java":
        src = os.path.join(root, "src")
        for name, text in java_dep(variant).items():
            _w(os.path.join(src, "dep", name), text)
        _w(os.path.join(src, "app", "App.java"), JAVA_APP)
        cls = os.path.join(root, "cls")
        os.makedirs(cls, exist_ok=True)
        srcs = []
        for d, _dd, fs in os.walk(src):
            srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
        c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
        if c.returncode != 0:
            raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
        if fixture == "whole":
            return [], cls, JAVA_APP
        # One class directory per package: a package scanned with its sibling's classes on the same path
        # is not a separate package at all, which is the isolation the chained arms depend on.
        dep_d, app_d = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
        shutil.copytree(os.path.join(cls, "dep"), os.path.join(dep_d, "dep"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(cls, "app"), os.path.join(app_d, "app"), dirs_exist_ok=True)
        return [dep_d], app_d, JAVA_APP
    if lang == "ts":
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        if fixture == "whole":
            app = os.path.join(root, "app")
            _w(os.path.join(app, "package.json"), '{"name":"app","version":"0.0.0","main":"src/index.ts"}\n')
            _w(os.path.join(app, "src", "dep.ts"), ts_dep(variant))
            text = TS_APP % "./dep.js"
            _w(os.path.join(app, "src", "index.ts"), text)
            if os.path.isdir(types):
                _link(os.path.join(app, "node_modules", "@types"), types)
            return [], app, text
        dep, app = os.path.join(root, "dep"), os.path.join(root, "app")
        _w(os.path.join(dep, "package.json"), '{"name":"dep","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(dep, "src", "index.ts"), ts_dep(variant))
        _w(os.path.join(app, "package.json"),
           '{"name":"app","version":"0.0.0","main":"src/index.ts","dependencies":{"dep":"file:../dep"}}\n')
        text = TS_APP % "dep"
        _w(os.path.join(app, "src", "index.ts"), text)
        _link(os.path.join(app, "node_modules", "dep"), dep)
        if os.path.isdir(types):
            for pkg in (dep, app):
                _link(os.path.join(pkg, "node_modules", "@types"), types)
        return [dep], app, text
    # swift
    if fixture == "whole":
        app = os.path.join(root, "app")
        _w(os.path.join(app, "Package.swift"), SW_MANIFEST % dict(mod="App", deps="", prods=""))
        _w(os.path.join(app, "Sources", "App", "dep.swift"), swift_dep(variant))
        text = SW_APP % ""
        _w(os.path.join(app, "Sources", "App", "app.swift"), text)
        return [], app, text
    dep, app = os.path.join(root, "dep"), os.path.join(root, "app")
    _w(os.path.join(dep, "Package.swift"), SW_MANIFEST % dict(mod="Dep", deps="", prods=""))
    _w(os.path.join(dep, "Sources", "Dep", "dep.swift"), swift_dep(variant))
    _w(os.path.join(app, "Package.swift"),
       SW_MANIFEST % dict(mod="App", deps='.package(path: "../dep")',
                          prods='.product(name: "Dep", package: "dep")'))
    text = SW_APP % "import Dep\n"
    _w(os.path.join(app, "Sources", "App", "app.swift"), text)
    return [dep], app, text


def build_proof(lang, app):
    """An absence-asserting control over a program that does not build is no evidence at all. java is
    already compiled by `render`; ts and swift are typechecked/built here."""
    if NOBUILD or lang == "java":
        return None
    if lang == "swift":
        r = gd.run(["swift", "build"], cwd=app)
    else:
        tsc = os.path.join(gd.CANDOR_TS, "node_modules", "typescript", "bin", "tsc")
        if not os.path.exists(tsc):
            return "SKIPPED: no tsc under CANDOR_TS/node_modules — the ts fixture is UNTYPECHECKED"
        r = gd.run(["node", tsc, "--noEmit", "--module", "nodenext", "--moduleResolution", "nodenext",
                    "--target", "es2022", "--types", "node", os.path.join("src", "index.ts")], cwd=app)
    if r.returncode != 0:
        return "%s build FAILED: %s" % (lang, (r.stderr or r.stdout).decode()[:300].replace("\n", " | "))
    return None


def gate(scanner, pkgdir, deps, policy_path):
    """The engine's own gate over the consumer, chained exactly as the report scan was. SPEC §3 requires
    every engine to honour CANDOR_POLICY when the flag is absent, so one spelling serves all three."""
    out = os.path.join(os.path.dirname(pkgdir.rstrip(os.sep)), "gate.report.json")
    scanner._clear(pkgdir, out)
    env = dict(os.environ, CANDOR_POLICY=policy_path)
    if deps:
        env["CANDOR_DEPS"] = " ".join(deps)
    else:
        env.pop("CANDOR_DEPS", None)
    return gd.run(scanner._argv(pkgdir, out), cwd=scanner._cwd(pkgdir), env=env).returncode


def _leaf(name):
    return (name or "").replace("::", ".").split(".")[-1]


def run_engine(lang, ws):
    """Returns ({arm_id: (ok, detail)}, notes, err)."""
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, None, scanner.err
    results, notes, texts = {}, [], {}
    for fixture in ("whole", "override", "sibling"):
        root = os.path.join(ws, lang, fixture)
        os.makedirs(root, exist_ok=True)
        try:
            deps, app, text = render(lang, root, fixture)
        except RuntimeError as e:
            return None, None, "%s/%s: %s" % (lang, fixture, e)
        texts[fixture] = text
        err = build_proof(lang, app)
        if err and err.startswith("SKIPPED"):
            notes.append("  NOTE  %s %s %s" % (lang, fixture, err))
        elif err:
            return None, None, "%s (%s)" % (err, fixture)
        dep_reports = []
        for d in deps:
            r = scanner.scan(d)
            if not r.produced:
                return None, None, "%s: dependency scan produced no report (rc=%d) %s" % (fixture, r.rc, r.note)
            dep_reports.append(r.report)
        r = scanner.scan(app, deps=dep_reports)
        if not r.produced:
            return None, None, "%s: consumer scan produced no report (rc=%d) %s" % (fixture, r.rc, r.note)
        rep = json.load(open(r.report))
        # A HOLLOW consumer judges nothing, and every row below would read absent (SOUNDNESS R242).
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, None, "%s: analyzed.count is 0 — a hollow report judges nothing" % fixture
        rows = {_leaf(f.get("fn")): f for f in rep.get("functions") or []}
        pol_dir = os.path.join(root, "pol")
        os.makedirs(pol_dir, exist_ok=True)
        for arm_id, fx, fn, kind in ARMS:
            if fx != fixture:
                continue
            row = rows.get(fn)
            if row is None:
                # Every consumer function calls `m`, whose base body performs Fs in every variant, so an
                # absent row is a purity claim over a function that reads the file system.
                results[arm_id] = (False, "ABSENT from functions[] — a purity claim (SPEC §2 rule 3)")
                continue
            got, bad = {}, []
            for i, (pol, want) in enumerate(sorted(WANT[kind].items())):
                pp = os.path.join(pol_dir, "%s_%d.policy" % (fn, i))
                # The scope is the row's OWN `fn`, read back from the report: it names exactly this
                # function in this engine's spelling, so a scope that matched nothing cannot hide here.
                with open(pp, "w") as f:
                    f.write("%s %s\n" % (pol, row["fn"]))
                rc = gate(scanner, app, dep_reports, pp)
                got[pol] = rc
                if rc != want:
                    bad.append("`%s` exit %d want %d" % (pol, rc, want))
            detail = "inferred=%s gates=%s" % (sorted(row.get("inferred") or []),
                                              " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items())))
            results[arm_id] = (not bad, detail + ("" if not bad else " — " + "; ".join(bad)))
    # THE CROSS, asserted: the chained consumer is the same text over both dependencies.
    if texts.get("override") != texts.get("sibling"):
        return None, None, ("the consumer source differs between the override and sibling fixtures — the "
                            "control is FIXTURE-INDUCED and no comparison here is evidence")
    return results, notes, None


def main():
    import tempfile
    print("=" * 100)
    print("DEPENDENCY SUBCLASS OVERRIDES ⟨0.39⟩ — a chained consumer carries the overrides it can see")
    print("  fixture : dep declares `BaseO.m` (Fs) and its own subclass `SubO`; app calls `b.m()` on a")
    print("            BaseO three ways — typed parameter, factory result, factory-bound local")
    print("  property: o* chained + SubO overrides m with Env -> `deny Env` and `deny Env Unknown` FIRE")
    print("            k* chained + SubO does NOT override m -> both stay 0 (no fabrication, no hedge)")
    print("            w* the same source as ONE package -> the engine's own unchained answer (reference)")
    print("            `deny Fs` must fire on every cell — the carrier that proves the chain and the scope")
    print("  rust    : N/A — %s" % RUST_NA)
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART94_NOBUILD is set — ts/swift fixtures were NOT built. An absence-asserting")
        print("      control over an unbuilt program is not evidence; this run is for iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — SubO's override of m is rendered with NO effect, so the")
        print("       w* REFERENCE arms, which every engine passes clean, must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part94-")
    bad = stale = 0
    live = 0
    for lang in ENGINES:
        res, notes, err = run_engine(lang, ws)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                print("  %-6s -> SKIP (%s)" % (lang, err))
            else:
                print("  %-6s -> BROKEN: %s" % (lang, err))
                bad += 1
            continue
        live += 1
        for n in notes:
            print(n)
        for arm_id, _fx, _fn, kind in ARMS:
            ok, detail = res[arm_id]
            key = (arm_id, lang)
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-9s %-6s — expectation is STALE: %s" % (arm_id, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-9s %-6s %s" % (arm_id, lang, detail))
            elif key in XFAIL:
                print("  xfail %-9s %-6s %s  [%s]" % (arm_id, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-9s %-6s %s  [%s]" % (arm_id, lang, detail, WHY[kind]))
                bad += 1
    print("  rust   -> N/A (declared): %s" % RUST_NA)
    shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("DEP-OVERRIDE: no engine available — NOT a pass")
        return 2
    if stale:
        print("DEP-OVERRIDE: %d xfail arm(s) PASSED — an expectation that has become true is a FAILURE "
              "here. Retire it in the same commit as the engine fix (SOUNDNESS R867)." % stale)
    if bad:
        print("DEP-OVERRIDE: %d cell(s) wrong — see SOUNDNESS R867 and SPEC §4 ⟨0.39⟩" % bad)
    if not bad and not stale:
        print("DEP-OVERRIDE: OK — every engine's reference carries the override, every control stays "
              "exact, and every open defect cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
