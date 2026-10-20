#!/usr/bin/env python3
"""PART 100 — A FORMATTING MEMBER DISPATCHED ON A DEPENDENCY'S OWN ABSTRACTION, FOUR-WAY, SPEC §4 ⟨0.39⟩/⟨0.40⟩.

SOUNDNESS R1304 (java), R1308 (rust), R1309 (ts), R1310 (swift). The shape, in every language:

    dep:  abstraction Converter { convert }            -- rust adds `: Display`, swift `: CustomStringConvertible`
          ArrayConverter { elem: Converter;  run() { elem.convert() };  <format>() { format elem } }
    app:  MyConv implements Converter, and ITS formatting member reads the file system
          c_call(ac)   { ac.<format>() }               -- the holder formatted by an explicit call
          c_interp(ac) { "<interpolate ac>" }          -- the holder formatted by interpolation
          c_run(ac)    { ac.run() }                    -- the ORDINARY member, the ⟨0.39⟩ control

Executed (`~/candor-handoff/xeng-r1304/gt.txt`, `~/candor-handoff/javaab-a/fx/conv`): formatting an
`ArrayConverter` that holds a `MyConv` runs `MyConv`'s formatting member and the file is touched. Scanned
as ONE tree, all four engines charge `c_call` with `Fs`. CHAINED — the dependency scanned alone and its
report handed over on `CANDOR_DEPS` — all four read `c_call` pure, and `deny Fs` and `deny Fs Unknown`
both exit 0. The SAME shape through `convert` charges chained in all four, which is what isolates the
formatting member.

WHY THIS IS NOT A NEW OBLIGATION. ⟨0.39⟩'s headline already binds it: `MyConv` is an implementor visible
to the consumer (its own), `Converter` is the dependency's own abstraction, and the dependency's
`ArrayConverter` formatting row says a dispatch through it OCCURS. What looked like an exemption — §4's MAY
to treat formatting/equality/hashing/cloning as resolved-pure, and the ⟨0.39⟩ cost note's census wording —
is scoped by the ⟨0.40⟩ clarification this part pins: the MAY is judged by the RECEIVER's declared type,
and waives a hedge, never the name or a visible implementor's effects.

THE PART NAMES NO WIRE ROUTE. It asserts the clause's PROPERTY at the consumer, as PART 92 and PART 94 do:
the gate exits over code that executes the effect. The key spelling the clause states (under the
receiver's abstraction, never under `Object`/`Display`/`CustomStringConvertible`) is what an engine needs
to satisfy it; this part would equally pass a consumer that found the implementor another way.

WHY THE ASSERTION IS A GATE EXIT AND NOT A ROW. `deny Fs` must FIRE on the chained defect arms — ⟨0.39⟩
requires the effects to be CARRIED, and a hedge is not carrying (PART 94's reasoning) — and `deny Fs
Unknown` must fire too, which is the split-invariance property: the engine's own one-tree answer fires it.
Every consumer function first reads the environment, so `deny Env` is a CARRIER on every cell: the row is
present in every arm, its own `fn` (read back from the report) is the scope, and a policy that matched
nothing cannot pass here.

THE ARMS, per engine (`w_` = one tree, `c_` = chained; then the variant; then the consumer function).
The variant moves ONE thing — which of `MyConv`'s two members performs `Fs` — and the dependency's text
and the consumer FUNCTIONS are byte-identical across all of them (asserted, not trusted).

  w_fmt_*     REFERENCE — one tree, MyConv's formatting member does Fs. Every engine fires today.
  c_fmt_call  DEFECT    — chained, the same. Must fire `deny Fs` and `deny Fs Unknown`.
  c_fmt_interp
  *_conv_run  CONTROL   — MyConv.convert does Fs, reached through `run`: the ⟨0.39⟩ route every engine
              already implements. If this goes red the chain itself is broken, not the formatting leg.
  *_fmt_run, *_conv_call, *_conv_interp, *_pure_*
              CONTROL   — the member reached performs NOTHING, so `deny Fs` must stay 0: a fix that joins
              every member of MyConv onto any Converter dispatch reddens here. The consumer also declares
              `Other`, which is NOT a Converter and whose formatting member performs Fs in every variant and
              both layouts (its row must read Fs, or the run is BROKEN): a fix that keys the dependency's
              formatting call under the standard-library type, or joins every formatting body the consumer
              has, charges Other's Fs onto *_pure_call/*_conv_call and reddens them. `deny Fs Unknown`
              is NOT asserted on these: a hedge is permitted, and the zero-local-implementor hedge on
              `convert` surviving a consumer's pure implementor is a known disclosure (R1304's side note),
              not this part's subject.

THE XFAIL TABLE. Every engine fails the c_fmt_* arms today (executed, the rows above). Each is declared
per (arm, engine), and A PASSING XFAIL IS A FAILURE: the engine that fixes its row reddens this part and
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
    ("§4 ⟨0.40⟩", "A FORMATTING, EQUALITY, HASHING OR CLONING MEMBER CALLED ON A RECEIVER TYPED BY A PACKAGE'S OWN"),
    ("§4 ⟨0.40⟩", "they license omitting a HEDGE where no implementor is visible, never omitting the name or a visible"),
    ("§4 ⟨0.39⟩", "A mechanism that makes reports better must not make silence cheaper."),
]

# THE FAULT IS AT THE FIXTURE. With CANDOR_PROBE_FAULT set, MyConv's formatting member is rendered WITHOUT
# its Fs in the `fmt` variant, so nothing the consumer reaches touches the file system — the w_fmt_*
# REFERENCE arms, which every engine passes today, must then go red through this part's own verdict.
FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART100_NOBUILD")

ENGINES = ("rust", "java", "ts", "swift")
VARIANTS = ("fmt", "conv", "pure")
FUNCS = {"call": "c_call", "interp": "c_interp", "run": "c_run"}

def arms_for(lang):
    """[(arm_id, layout, variant, func_key, kind)]"""
    out = []
    for variant in VARIANTS:
        for fk in ("call", "interp", "run"):
            if variant == "fmt" and fk in ("call", "interp"):
                kinds = ("ref", "carry")
            elif variant == "conv" and fk == "run":
                kinds = ("member", "member")
            else:
                kinds = ("clean", "clean")
            out.append(("w_%s_%s" % (variant, fk), "one", variant, fk, kinds[0]))
            out.append(("c_%s_%s" % (variant, fk), "split", variant, fk, kinds[1]))
    return out


# policy effects -> expected exit, per kind. `deny Env` is the CARRIER on every arm (see header).
WANT = {
    "ref":    {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "carry":  {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "member": {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "clean":  {"deny Env": 1, "deny Fs": 0},
}
WHY = {
    "ref":    "REFERENCE: one tree — the engine's own unchained answer charges the formatting member's Fs",
    "carry":  "DEFECT: a consumer implementor reached through the dependency's formatting of its own "
              "abstraction is visible to the consumer, and its Fs MUST be carried (§4 ⟨0.39⟩/⟨0.40⟩)",
    "member": "CONTROL: the ordinary member through the ⟨0.39⟩ route — if this is red the chain is broken",
    "clean":  "CONTROL: the member reached performs nothing — a Fs here is a FABRICATION",
}

# An expectation keyed by (arm, engine), never by arm alone — one engine will fix this first.
XFAIL = {
    ("c_fmt_call", "rust"):    "R1308 — the producer names `convlib#Converter::fmt` but the consumer keys its "
                               "union only under `Converter::convert`: `impl Display for MyConv` is not joined",
    ("c_fmt_interp", "rust"):  "R1308 — the same join miss, reached through `format!`",
    ("c_fmt_call", "ts"):      "R1309 — no row and no `dispatchesOn` for `ArrayConverter.toString`, and no "
                               "consumer join for a member the interface does not declare",
    ("c_fmt_interp", "ts"):    "R1309 — the same, reached through template interpolation",
    ("c_fmt_call", "swift"):   "R1310 — the producer publishes no row/`dispatchesOn` for "
                               "`ArrayConverter.description`; the consumer's union is already right",
    ("c_fmt_interp", "swift"): "R1310 — the same, reached through string interpolation",
}


# =====================================================================================================
# THE FIXTURE. Sinks are gen_differential's, so the effect vocabulary stays in one place.
# =====================================================================================================
def _sink(effect_id, lang):
    for e in gd.EFFECTS:
        if e["id"] == effect_id:
            return e["sink"][lang]
    raise KeyError(effect_id)


def _bodies(lang, variant):
    """(formatting-member prefix, convert prefix): the Fs sink goes in exactly one of them, or neither."""
    fs = _sink("fs", lang) + " "
    fmt = fs if (variant == "fmt" and not FAULT) else ""
    conv = fs if variant == "conv" else ""
    return fmt, conv


RS_LIB = '''use std::fmt;

pub trait Converter: fmt::Display {
    fn convert(&self, s: &str) -> String;
}

pub struct ArrayConverter {
    elem: Box<dyn Converter>,
}
impl ArrayConverter {
    pub fn new(elem: Box<dyn Converter>) -> Self { ArrayConverter { elem } }
    pub fn run(&self, s: &str) -> String { self.elem.convert(s) }
}
impl fmt::Display for ArrayConverter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "AC[{}]", self.elem) }
}
'''

RS_IMPL = '''pub struct MyConv;
impl fmt::Display for MyConv {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { %(FMT)swrite!(f, "MyConv") }
}
impl Converter for MyConv {
    fn convert(&self, s: &str) -> String { %(CONV)ss.to_string() }
}
pub struct Other;
impl fmt::Display for Other {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { %(OTHER)swrite!(f, "Other") }
}
'''

RS_FUNCS = '''pub fn c_call(ac: &ArrayConverter) -> String { %(ENV)s ac.to_string() }
pub fn c_interp(ac: &ArrayConverter) -> String { %(ENV)s format!("{}", ac) }
pub fn c_run(ac: &ArrayConverter) -> String { %(ENV)s ac.run("x") }
'''

JAVA_CONVERTER = 'package convlib;\npublic interface Converter {\n  String convert(String s);\n}\n'
JAVA_ARRAY = '''package convlib;
public class ArrayConverter {
  private final Converter elem;
  public ArrayConverter(Converter elem) { this.elem = elem; }
  public String run(String s) { return elem.convert(s); }
  @Override public String toString() { return "AC[" + elem.toString() + "]"; }
}
'''
JAVA_IMPL = '''package app;
public class MyConv implements convlib.Converter {
  public String convert(String s) { %(CONV)sreturn s; }
  @Override public String toString() { %(FMT)sreturn "MyConv"; }
}
'''
JAVA_OTHER = '''package app;
public class Other {
  @Override public String toString() { %(OTHER)sreturn "Other"; }
}
'''
JAVA_FUNCS = '''package app;
import convlib.ArrayConverter;
public class App {
  public static String c_call(ArrayConverter ac) { %(ENV)s return ac.toString(); }
  public static String c_interp(ArrayConverter ac) { %(ENV)s return "" + ac; }
  public static String c_run(ArrayConverter ac) { %(ENV)s return ac.run("x"); }
}
'''

TS_LIB = '''export interface Converter {
  convert(s: string): string;
}

export class ArrayConverter {
  private elem: Converter;
  constructor(elem: Converter) { this.elem = elem; }
  run(s: string): string { return this.elem.convert(s); }
  toString(): string { return `AC[${this.elem}]`; }
}
'''
TS_IMPL = '''export class MyConv implements Converter {
  convert(s: string): string { %(CONV)sreturn s; }
  toString(): string { %(FMT)sreturn "MyConv"; }
}
export class Other {
  toString(): string { %(OTHER)sreturn "Other"; }
}
'''
TS_FUNCS = '''export function c_call(ac: ArrayConverter): string { %(ENV)s return ac.toString(); }
export function c_interp(ac: ArrayConverter): string { %(ENV)s return `${ac}`; }
export function c_run(ac: ArrayConverter): string { %(ENV)s return ac.run("x"); }
'''

SW_LIB = '''public protocol Converter: CustomStringConvertible {
    func convert(_ s: String) -> String
}

public struct ArrayConverter: CustomStringConvertible {
    let elem: any Converter
    public init(_ elem: any Converter) { self.elem = elem }
    public func run(_ s: String) -> String { elem.convert(s) }
    public var description: String { "AC[\\(elem)]" }
}
'''
SW_IMPL = '''public struct MyConv: Converter {
    public init() {}
    public func convert(_ s: String) -> String { %(CONV)sreturn s }
    public var description: String { %(FMT)sreturn "MyConv" }
}
public struct Other: CustomStringConvertible {
    public init() {}
    public var description: String { %(OTHER)sreturn "Other" }
}
'''
SW_FUNCS = '''public func c_call(_ ac: ArrayConverter) -> String {
    %(ENV)s
    return ac.description
}
public func c_interp(_ ac: ArrayConverter) -> String {
    %(ENV)s
    return "\\(ac)"
}
public func c_run(_ ac: ArrayConverter) -> String {
    %(ENV)s
    return ac.run("x")
}
'''
SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def _swift_sink(lang_sink):
    # Swift statements here sit inside a one-line body; a `;` keeps each on the body's line.
    return lang_sink + ";"


def consumer_funcs(lang):
    """The consumer FUNCTIONS — the text under test — identical in every variant and both layouts."""
    env = _sink("env", lang)
    return {"rust": RS_FUNCS, "java": JAVA_FUNCS, "ts": TS_FUNCS, "swift": SW_FUNCS}[lang] % dict(ENV=env)


def _impl(lang, variant):
    fmt, conv = _bodies(lang, variant)
    # THE STDLIB-KEY CONTROL'S SEED: `Other` is a consumer type that is NOT a Converter, whose formatting
    # member performs Fs in EVERY variant and both layouts. An engine that keys the dependency's formatting
    # call under the declaring standard-library type (`Display::fmt`, `Object.toString`,
    # `CustomStringConvertible.description`), or joins every formatting body the consumer has, charges
    # Other's Fs onto c_pure_call / c_conv_call — which must stay `deny Fs` 0.
    other = _sink("fs", lang) + " "
    if lang == "swift":
        fmt = (_swift_sink(fmt.strip()) + " ") if fmt else ""
        conv = (_swift_sink(conv.strip()) + " ") if conv else ""
        other = _swift_sink(other.strip()) + " "
    return {"rust": RS_IMPL, "java": JAVA_IMPL, "ts": TS_IMPL, "swift": SW_IMPL}[lang] % dict(
        FMT=fmt, CONV=conv, OTHER=other)


def other_text(lang):
    """java keeps Other in its own file; the other three carry it inside the impl text."""
    return JAVA_OTHER % dict(OTHER=_sink("fs", "java") + " ")


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


def render(lang, root, layout, variant):
    """Lay one fixture out. Returns (dep_dirs, app_dir, lib_text). `one` has no dep dirs."""
    funcs = consumer_funcs(lang)
    impl = _impl(lang, variant)
    if lang == "rust":
        cargo = '[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n'
        if layout == "one":
            app = os.path.join(root, "app")
            _w(os.path.join(app, "Cargo.toml"), cargo % "app")
            _w(os.path.join(app, "src", "lib.rs"), RS_LIB + "\n" + impl + "\n" + funcs)
            return [], app, RS_LIB
        dep, app = os.path.join(root, "convlib"), os.path.join(root, "app")
        _w(os.path.join(dep, "Cargo.toml"), cargo % "convlib")
        _w(os.path.join(dep, "src", "lib.rs"), RS_LIB)
        _w(os.path.join(app, "Cargo.toml"), (cargo % "app") + '\n[dependencies]\nconvlib={path="../convlib"}\n')
        # ONE preamble line differs from the one-tree layout (PART 24's convention): where the names bind.
        _w(os.path.join(app, "src", "lib.rs"),
           "use std::fmt;\nuse convlib::{ArrayConverter, Converter};\n\n" + impl + "\n" + funcs)
        return [dep], app, RS_LIB
    if lang == "java":
        src = os.path.join(root, "src")
        _w(os.path.join(src, "convlib", "Converter.java"), JAVA_CONVERTER)
        _w(os.path.join(src, "convlib", "ArrayConverter.java"), JAVA_ARRAY)
        _w(os.path.join(src, "app", "MyConv.java"), impl)
        _w(os.path.join(src, "app", "Other.java"), other_text("java"))
        _w(os.path.join(src, "app", "App.java"), funcs)
        cls = os.path.join(root, "cls")
        os.makedirs(cls, exist_ok=True)
        srcs = []
        for d, _dd, fs in os.walk(src):
            srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
        c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
        if c.returncode != 0:
            raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
        if layout == "one":
            return [], cls, JAVA_CONVERTER + JAVA_ARRAY
        # One class directory per package, from the SAME javac output: the layouts differ only in how the
        # class files are partitioned.
        dep_d, app_d = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
        shutil.copytree(os.path.join(cls, "convlib"), os.path.join(dep_d, "convlib"), dirs_exist_ok=True)
        shutil.copytree(os.path.join(cls, "app"), os.path.join(app_d, "app"), dirs_exist_ok=True)
        return [dep_d], app_d, JAVA_CONVERTER + JAVA_ARRAY
    if lang == "ts":
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        head = 'import * as fsm from "node:fs";\nimport { ArrayConverter, type Converter } from "%s";\n\n'
        if layout == "one":
            app = os.path.join(root, "app")
            _w(os.path.join(app, "package.json"), '{"name":"app","version":"0.0.0","main":"src/index.ts"}\n')
            _w(os.path.join(app, "src", "dep.ts"), TS_LIB)
            _w(os.path.join(app, "src", "index.ts"), (head % "./dep.js") + impl + "\n" + funcs)
            if os.path.isdir(types):
                _link(os.path.join(app, "node_modules", "@types"), types)
            return [], app, TS_LIB
        dep, app = os.path.join(root, "convlib"), os.path.join(root, "app")
        _w(os.path.join(dep, "package.json"), '{"name":"convlib","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(dep, "src", "index.ts"), TS_LIB)
        _w(os.path.join(app, "package.json"),
           '{"name":"app","version":"0.0.0","main":"src/index.ts","dependencies":{"convlib":"file:../convlib"}}\n')
        _w(os.path.join(app, "src", "index.ts"), (head % "convlib") + impl + "\n" + funcs)
        _link(os.path.join(app, "node_modules", "convlib"), dep)
        if os.path.isdir(types):
            for pkg in (dep, app):
                _link(os.path.join(pkg, "node_modules", "@types"), types)
        return [dep], app, TS_LIB
    # swift
    if layout == "one":
        app = os.path.join(root, "app")
        _w(os.path.join(app, "Package.swift"), SW_MANIFEST % dict(mod="App", deps="", prods=""))
        _w(os.path.join(app, "Sources", "App", "lib.swift"), SW_LIB)
        _w(os.path.join(app, "Sources", "App", "app.swift"), "import Foundation\n\n" + impl + "\n" + funcs)
        return [], app, SW_LIB
    dep, app = os.path.join(root, "convlib"), os.path.join(root, "app")
    _w(os.path.join(dep, "Package.swift"), SW_MANIFEST % dict(mod="ConvLib", deps="", prods=""))
    _w(os.path.join(dep, "Sources", "ConvLib", "lib.swift"), SW_LIB)
    _w(os.path.join(app, "Package.swift"),
       SW_MANIFEST % dict(mod="App", deps='.package(path: "../convlib")',
                          prods='.product(name: "ConvLib", package: "convlib")'))
    _w(os.path.join(app, "Sources", "App", "app.swift"),
       "import Foundation\nimport ConvLib\n\n" + impl + "\n" + funcs)
    return [dep], app, SW_LIB


def build_proof(lang, app):
    """An absence-asserting control over a program that does not build is no evidence at all. java is
    compiled by `render`; rust is checked, ts typechecked and swift built here."""
    if NOBUILD or lang == "java":
        return None
    if lang == "rust":
        if not shutil.which("cargo"):
            return "SKIPPED: no cargo — the rust fixture is UNCHECKED"
        r = gd.run(["cargo", "check", "--quiet", "--offline"], cwd=app,
                   env=dict(os.environ, CARGO_TARGET_DIR=os.path.join(app, "..", "target")))
    elif lang == "swift":
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
    every engine to honour CANDOR_POLICY when the flag is absent, so one spelling serves all four."""
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
    results, notes, libs, funcs_seen = {}, [], set(), set()
    arms = arms_for(lang)
    for variant in VARIANTS:
        for layout in ("one", "split"):
            root = os.path.join(ws, lang, variant, layout)
            os.makedirs(root, exist_ok=True)
            try:
                deps, app, lib = render(lang, root, layout, variant)
            except RuntimeError as e:
                return None, None, "%s/%s/%s: %s" % (lang, variant, layout, e)
            libs.add(lib)
            funcs_seen.add(consumer_funcs(lang))
            err = build_proof(lang, app)
            if err and err.startswith("SKIPPED"):
                notes.append("  NOTE  %s %s/%s %s" % (lang, variant, layout, err))
            elif err:
                return None, None, "%s (%s/%s)" % (err, variant, layout)
            dep_reports = []
            for d in deps:
                r = scanner.scan(d)
                if not r.produced:
                    return None, None, "%s/%s: dependency scan produced no report (rc=%d) %s" % (
                        variant, layout, r.rc, r.note)
                dep_reports.append(r.report)
            r = scanner.scan(app, deps=dep_reports)
            if not r.produced:
                return None, None, "%s/%s: consumer scan produced no report (rc=%d) %s" % (
                    variant, layout, r.rc, r.note)
            rep = json.load(open(r.report))
            # A HOLLOW consumer judges nothing, and every row below would read absent (SOUNDNESS R242).
            if not ((rep.get("analyzed") or {}).get("count") or 0):
                return None, None, "%s/%s: analyzed.count is 0 — a hollow report judges nothing" % (variant, layout)
            rows = {_leaf(f.get("fn")): f for f in rep.get("functions") or []}
            # The stdlib-key control is only evidence if its SEED is live: Other's formatting member must
            # read Fs in this very report. If it does not, the c_pure_call/c_conv_call zeros prove nothing.
            seeded = [f for f in rep.get("functions") or []
                      if "Other" in (f.get("fn") or "") and "Fs" in (f.get("inferred") or [])]
            if not seeded:
                return None, None, ("%s/%s: Other's formatting member is not charged Fs in the consumer report "
                                    "— the stdlib-key control's seed is dead, so its zeros would be vacuous"
                                    % (variant, layout))
            pol_dir = os.path.join(root, "pol")
            os.makedirs(pol_dir, exist_ok=True)
            for arm_id, lay, var, fk, kind in arms:
                if lay != layout or var != variant:
                    continue
                fn = FUNCS[fk]
                row = rows.get(fn)
                if row is None:
                    # Every consumer function reads the environment first, so an absent row is a purity
                    # claim over a function that performs Env — and the carrier cannot be scoped.
                    results[arm_id] = (False, "ABSENT from functions[] — the Env carrier is missing, a "
                                              "purity claim (SPEC §2 rule 3)")
                    continue
                got, bad = {}, []
                for i, (pol, want) in enumerate(sorted(WANT[kind].items())):
                    pp = os.path.join(pol_dir, "%s_%d.policy" % (fn, i))
                    # The scope is the row's OWN `fn`, read back from the report: it names exactly this
                    # function in this engine's spelling, and the Env carrier proves it matched.
                    with open(pp, "w") as f:
                        f.write("%s %s\n" % (pol, row["fn"]))
                    rc = gate(scanner, app, dep_reports, pp)
                    got[pol] = rc
                    if rc != want:
                        bad.append("`%s` exit %d want %d" % (pol, rc, want))
                detail = "inferred=%s gates=%s" % (sorted(row.get("inferred") or []),
                                                  " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items())))
                results[arm_id] = (not bad, detail + ("" if not bad else " — " + "; ".join(bad)))
    # THE CROSS, asserted: one dependency text and one set of consumer functions across every fixture.
    if len(libs) != 1 or len(funcs_seen) != 1:
        return None, None, ("the dependency text or the consumer functions differ between fixtures — the "
                            "comparison is FIXTURE-INDUCED and no cell here is evidence")
    return results, notes, None


def main():
    import tempfile
    print("=" * 100)
    print("FORMATTING-MEMBER DISPATCH ⟨0.39⟩/⟨0.40⟩ — a consumer's implementor reached through the")
    print("dependency's formatting of its OWN abstraction is visible to the consumer")
    print("  fixture : dep `Converter` + `ArrayConverter { elem: Converter }` formatting `elem`; app supplies")
    print("            `MyConv`, and formats / runs an ArrayConverter — explicit call, interpolation, `run`")
    print("  property: c_fmt_* chained, MyConv's formatting member does Fs -> `deny Fs` and `deny Fs Unknown` FIRE")
    print("            w_fmt_* the same as ONE tree -> the engine's own answer (reference, fires today)")
    print("            *_conv_run -> the ordinary member charges (the ⟨0.39⟩ route; proves the chain)")
    print("            every other cell reaches a member that does nothing -> `deny Fs` stays 0")
    print("            `deny Env` fires on every cell — the carrier that proves the scope matched")
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART100_NOBUILD is set — rust/ts/swift fixtures were NOT built. An absence-")
        print("      asserting control over an unbuilt program is not evidence; this run is for iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — MyConv's formatting member is rendered WITHOUT its Fs, so the")
        print("       w_fmt_* REFERENCE arms, which every engine passes clean, must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part100-")
    bad = stale = live = 0
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
        for arm_id, _lay, _var, _fk, kind in arms_for(lang):
            ok, detail = res[arm_id]
            key = (arm_id, lang)
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-13s %-6s — expectation is STALE: %s" % (arm_id, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-13s %-6s %s" % (arm_id, lang, detail))
            elif key in XFAIL:
                print("  xfail %-13s %-6s %s  [%s]" % (arm_id, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-13s %-6s %s  [%s]" % (arm_id, lang, detail, WHY[kind]))
                bad += 1
    shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("FORMAT-DISPATCH: no engine available — NOT a pass")
        return 2
    if stale:
        print("FORMAT-DISPATCH: %d xfail arm(s) PASSED — an expectation that has become true is a FAILURE "
              "here. Retire it in the same commit as the engine fix (SOUNDNESS R1304/R1308/R1309/R1310)." % stale)
    if bad:
        print("FORMAT-DISPATCH: %d cell(s) wrong — see SOUNDNESS R1304/R1308/R1309/R1310 and SPEC §4 ⟨0.40⟩" % bad)
    if not bad and not stale:
        print("FORMAT-DISPATCH: OK — every reference charges, every control stays exact, and every open "
              "defect cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
