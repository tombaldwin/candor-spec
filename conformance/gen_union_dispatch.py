#!/usr/bin/env python3
"""PART 102 — A UNION ENTRY'S CONTRIBUTOR DISPATCHES ON A FURTHER MEMBER, FOUR-WAY, SPEC §4 ⟨0.39⟩/⟨0.40⟩.

SOUNDNESS R1324 (rust; found on aws-smithy-types `Serializer::serialize_some`, whose contributor dispatches
`serde#ser::Serialize::serialize`), and the rows this part's first measurement filed for the other engines
(named in the XFAIL table). The shape, in every language:

    api:   abstraction Mapper { mapv; other }   abstraction Sink { put(Mapper v); fwd }   Nop: Mapper (pure)
    Doc:   implements Sink { put(v) { v.mapv(1) }   fwd() { <Fs> } }        -- in `api` (local) or `prod` (foreign)
    mid:   mid_via(s: Sink, v: Mapper) { s.put(v) }    mid_fwd(s: Sink) { s.fwd() }
    app:   Mine implements Mapper — ONE of its members performs Fs, which one is the variant
           Other is NOT a Mapper and has a `mapv` that performs Fs in every variant (the name-only control)
           c_via(s)    { <Env>; mid_via(s, Mine) }   -- reaches Sink.put through a DEPENDENCY's key (R1324's shape)
           c_direct(s) { <Env>; s.put(Mine) }        -- dispatches Sink.put itself (R1349's shape)
           c_fwd(s)    { <Env>; mid_fwd(s) }         -- the union's OWN effect: the ⟨0.39⟩ route, the chain proof

Executed (`~/candor-handoff/specagent-0416/B-groundtruth.txt`): `c_via(Doc)` and `c_direct(Doc)` run
`Doc.put`, which runs `Mine.mapv`, in all four languages; `c_fwd(Doc)` runs `Doc.fwd`. The consumer never
names `Doc`: it reaches it only through the abstraction, and in the foreign layout the abstraction's owner
(`api`) is neither the package holding the implementor (`prod`) nor the one dispatching (`mid`).

WHAT §4 SAYS, which this part pins. ⟨0.39⟩ obligation 1 requires a dispatched member to REACH the caller
transitively, and the ⟨0.40⟩ union clause (R1324) states what that means for an `interfaceUnion` entry: the
union stands for its contributors' bodies, so a member a contributor dispatches on is a member a dispatch
through the union's key reaches, and the union MUST name it in its own `dispatchesOn` — there is no `calls`
on a union for a consumer to walk. The consumer then joins it like any other key (obligation 3). A hedge
(`Unknown` + `dispatch:`) on the union is DISCLOSURE, not carrying: it turns `deny Fs Unknown` red and leaves
`deny Fs` green over code that executes the Fs, so this part asserts `deny Fs`, as PARTs 94 and 100 do.

THE PART NAMES NO WIRE ROUTE. It asserts the property at the consumer; the producer's union entries are
PRINTED as diagnostics (their `dispatchesOn`, `inferred`, `unknownWhy`) so a red cell says which leg moved.

THE ARMS, `<layout>_<shape>_<variant>_<function>`. Layout: `w` one tree (the engine's own unchained answer),
`l` chained with the abstraction LOCAL to the package holding Doc, `f` chained with it FOREIGN (keyed under its
owner by obligation 2). Shape: `bare`, Doc.put only dispatches (the aws-smithy shape, a pure union); `busy`,
Doc.put also reads the clock, so the union is published with an effect of its own and a consumer that finds
the key has nothing else to make it hedge. Variant: which of Mine's members does Fs. Across every fixture the
consumer FUNCTIONS and the abstraction text are byte-identical (asserted, not trusted).

  *_far_via, *_far_direct   DEFECT/REFERENCE — Mine.mapv does Fs: `deny Fs` and `deny Fs Unknown` MUST fire.
  *_fwd                     CONTROL — Doc.fwd's own Fs through the union: proves the chain reached it.
  *_near_via, *_near_direct CONTROL — Mine.mapv is pure and Mine.other does Fs, but nothing dispatches
                            `other`: `deny Fs` MUST stay 0. A fix that joins every member of a consumer
                            implementor, or every same-named body (Other.mapv, live in every report and
                            checked), fabricates here.
  `deny Env` fires on every cell — the carrier that proves the scope matched the row.
  `busy` via/direct/none cells also assert `deny Clock` 1: Doc.put's own effect, so a port that trades the union's
                            own effect for the key reddens (Fable B-E5; `*_fwd` is a different union entry).
  Layout `u` is `f` with the abstraction's owner `api` NOT chained to the consumer (Fable B-E3): a key that arrives
                            through the union under `api#…` then has no chained entry to hit.
  xn_*/xc_*                 the doctored-producer CROSS-SPELLING arm (Fable REVIEW3 B3-E1), on the `deep` shape
                            (Doc.put -> helper -> v.mapv): the engine's own Sink.put union re-spelled into its OWN
                            spelling (xn_, control) and the OTHER one (xc_, rule 2: every consumer follows both).
                            What the control does NOT prove (Fable REVIEW4): (i) the undoctored deep arm is not run
                            in-suite, so "the doctor reaches the consumer" rests on xn passing where V0 was measured
                            failing (B-E1-spellings.txt), not on a per-run comparison; (ii) the (b) doctor writes
                            `calls=[Doc.put]` and no `dispatchesOn`, right for this shape (Doc.put dispatches only
                            through its helper) and wrong for one whose contributor also dispatches directly — one
                            shape, as every doctored arm is.
  *_none (l/f/u only)       a second consumer `zapp` with NO Mapper implementor of its own (it passes api's pure
                            Nop; executed: no Fs). `deny Fs` MUST stay 0; the disclosure is RECORDED, not asserted —
                            it is where a port's removal lands, to be accounted for against the 0.40.15 column.

THE XFAIL TABLE is per (arm, engine), each naming a register row, and A PASSING XFAIL IS A FAILURE: the
engine that fixes its row reddens this part and retires its own lines in the same commit.
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
    ("§4 ⟨0.39⟩", "The obligation is that the member must REACH the caller transitively"),
    ("§4 ⟨0.40⟩", "AN `interfaceUnion` ENTRY CARRIES EVERY MEMBER ITS CONTRIBUTORS DISPATCH ON"),
    ("§4 ⟨0.40⟩", "hedge in its place is a disclosure, not a conforming alternative"),
    ("§4 ⟨0.39⟩", "A mechanism that makes reports better must not make silence cheaper."),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART102_NOBUILD")
EXEC_MARK = os.environ.get("CANDOR_PART102_EXEC")   # ground-truth mode: Mine.mapv / Doc.fwd WRITE this file

ENGINES = ("rust", "java", "ts", "swift")
LAYOUTS = ("one", "local", "foreign", "unchained")
LAYOUT_PREFIX = {"one": "w", "local": "l", "foreign": "f", "unchained": "u"}
SHAPES = ("bare", "busy")
VARIANTS = ("far", "near")
FUNCS = {"via": "c_via", "direct": "c_direct", "fwd": "c_fwd", "none": "c_none"}


def arms_for(lang):
    out = []
    for layout in LAYOUTS:
        for shape in SHAPES:
            for variant in VARIANTS:
                for fk in ("via", "direct", "fwd", "none"):
                    if fk == "none" and (layout == "one" or variant != "far"):
                        continue   # zapp has no Mine, so the variant cannot move it: one arm per (layout, shape)
                    if fk == "none":
                        out.append(("%s_%s_none" % (LAYOUT_PREFIX[layout], shape), layout, (shape, variant), fk,
                                    "none"))
                        continue
                    if fk == "fwd":
                        kind = "member"
                    elif variant == "far":
                        kind = "ref" if layout == "one" else "carry"
                    else:
                        kind = "clean"
                    out.append(("%s_%s_%s_%s" % (LAYOUT_PREFIX[layout], shape, variant, fk), layout,
                                (shape, variant), fk, kind))
    return out


WANT = {
    "ref":    {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "carry":  {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "member": {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "clean":  {"deny Env": 1, "deny Fs": 0},
    "none":   {"deny Env": 1, "deny Fs": 0},
    "spell":  {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
    "cross":  {"deny Env": 1, "deny Fs": 1, "deny Fs Unknown": 1},
}
WHY = {
    "ref":    "REFERENCE: one tree — the engine's own unchained answer charges Mine.mapv's Fs",
    "carry":  "DEFECT: a member the union's contributor dispatches on REACHES the consumer, whose implementor "
              "performs Fs — `deny Fs` MUST fire (§4 ⟨0.39⟩ obligation 1, ⟨0.40⟩ union `dispatchesOn`)",
    "member": "CONTROL: the union's own effect through the ⟨0.39⟩ route — if this is red the chain is broken",
    "clean":  "CONTROL: the member reached performs nothing — a Fs here is a FABRICATION",
    "none":   "CONTROL: the consumer supplies no implementor (it passes api's pure Nop) — a Fs here is a FABRICATION",
    "spell":  "CONTROL: the union doctored in this engine's OWN spelling — if red, the doctor never reached the consumer",
    "cross":  "DEFECT: a union in the OTHER spelling must be followed too (§4 ⟨0.40⟩ rule 2: every consumer, both spellings)",
}

# Keyed by (arm, engine), each naming its register row; measured 2026-10-22 at the four heads (candor-scan d10e401,
# candor-java b679b9a, candor-ts e6481ee, candor-swift 6d2031a). DISCLOSED = `deny Fs Unknown` already 1 (the cell
# fails on `deny Fs` only); SILENT = both 0 over code that wrote the file.
XFAIL = {
    ('f_bare_far_direct', 'java'):
        "R1355 — DISCLOSED by the consumer's own `dispatch:api.Sink.put` hedge over a pure union; no union carries `dispatchesOn`",
    ('f_bare_far_via', 'java'):
        "R1355 — DISCLOSED by the consumer's own `dispatch:api.Sink.put` hedge over a pure union; no union carries `dispatchesOn`",
    ('f_busy_far_direct', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('f_busy_far_via', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('l_bare_far_direct', 'java'):
        "R1355 — DISCLOSED by the consumer's own `dispatch:api.Sink.put` hedge over a pure union; no union carries `dispatchesOn`",
    ('l_bare_far_via', 'java'):
        "R1355 — DISCLOSED by the consumer's own `dispatch:api.Sink.put` hedge over a pure union; no union carries `dispatchesOn`",
    ('l_busy_far_direct', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('l_busy_far_via', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('f_bare_far_direct', 'ts'):
        "R1356 — DISCLOSED by the consumer's own hedge (no union under Sink.put locally; a reasonless `Unknown` union foreign)",
    ('f_bare_far_via', 'ts'):
        "R1356 — DISCLOSED by the consumer's own hedge (no union under Sink.put locally; a reasonless `Unknown` union foreign)",
    ('f_busy_far_direct', 'ts'):
        "R1356 — DISCLOSED only because the producer hedges Doc.put's own `Mapper.mapv` dispatch",
    ('f_busy_far_via', 'ts'):
        "R1356 — DISCLOSED only because the producer hedges Doc.put's own `Mapper.mapv` dispatch",
    ('l_bare_far_direct', 'ts'):
        "R1356 — DISCLOSED by the consumer's own hedge (no union under Sink.put locally; a reasonless `Unknown` union foreign)",
    ('l_bare_far_via', 'ts'):
        "R1356 — DISCLOSED by the consumer's own hedge (no union under Sink.put locally; a reasonless `Unknown` union foreign)",
    ('l_busy_far_direct', 'ts'):
        "R1356 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('l_busy_far_via', 'ts'):
        "R1356 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`, and the consumer trusts it",
    ('u_bare_far_via', 'java'):
        "R1355 — DISCLOSED by the consumer's own hedge; no union carries `dispatchesOn`",
    ('u_bare_far_direct', 'java'):
        'R1355 — SILENT with the owner unchained: no consumer hedge, no union key',
    ('u_busy_far_via', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`",
    ('u_busy_far_direct', 'java'):
        "R1355 — SILENT: the union carries Doc.put's Clock and no `dispatchesOn`",
    ('u_bare_far_via', 'ts'):
        "R1356 — DISCLOSED (the reasonless foreign union's Unknown); no `dispatchesOn`",
    ('u_bare_far_direct', 'ts'):
        "R1356 — DISCLOSED (the reasonless foreign union's Unknown); no `dispatchesOn`",
    ('u_busy_far_via', 'ts'):
        "R1356 — DISCLOSED only because the producer hedges Doc.put's own `Mapper.mapv` dispatch",
    ('u_busy_far_direct', 'ts'):
        "R1356 — DISCLOSED only because the producer hedges Doc.put's own `Mapper.mapv` dispatch",
    ('xc_local_via', 'rust'):
        "R1359 (LATENT) — SILENT since the 0.40.16 join: the consumer does not walk a union's `calls`, and the R1324 hedge that used to disclose it is gone",
    ('xc_local_direct', 'rust'):
        "R1359 (LATENT) — SILENT since the 0.40.16 join: the consumer does not walk a union's `calls`, and the R1324 hedge that used to disclose it is gone",
    ('xc_foreign_via', 'rust'):
        "R1359 (LATENT) — the consumer does not walk a union's `calls`; this cell alone stays disclosed (deny Fs Unknown 1)",
    ('xc_foreign_direct', 'rust'):
        "R1359 (LATENT) — SILENT since the 0.40.16 join: the consumer does not walk a union's `calls`, and the R1324 hedge that used to disclose it is gone",
    ('xc_local_via', 'ts'):
        "R1365 (LATENT) — SILENT: the consumer does not walk a union's `calls`",
    ('xc_foreign_via', 'ts'):
        "R1365 (LATENT) — the consumer does not walk a union's `calls`; disclosed by the reasonless foreign union (R1358)",
    ('xc_local_via', 'swift'):
        "R1366 (LATENT) — SILENT: the consumer does not walk a union's `calls`",
    ('xc_local_direct', 'ts'):
        "R1365 (LATENT) — SILENT: the consumer does not walk a union's `calls`",
    ('xc_foreign_direct', 'ts'):
        "R1365 (LATENT) — the consumer does not walk a union's `calls`; disclosed by the reasonless foreign union (R1358)",
    ('xc_local_direct', 'swift'):
        "R1366 (LATENT) — SILENT: the consumer does not walk a union's `calls`",
    ('xc_foreign_via', 'swift'):
        "R1366 (LATENT) — the consumer does not walk a union's `calls`; disclosed through the dependency-key route only",
    ('xc_foreign_direct', 'swift'):
        "R1366 (LATENT) — SILENT: the consumer does not walk a union's `calls`",
}



def _sink(effect_id, lang):
    if EXEC_MARK and effect_id == "fs":
        return {"rust": 'let _ = std::fs::write("%s", "hit");' % EXEC_MARK,
                "java": 'try { java.nio.file.Files.writeString(java.nio.file.Path.of("%s"), "hit"); } '
                        'catch (Exception e) {}' % EXEC_MARK,
                "ts": 'fsm.writeFileSync("%s", "hit");' % EXEC_MARK,
                "swift": 'FileManager.default.createFile(atPath: "%s", contents: nil)' % EXEC_MARK}[lang]
    for e in gd.EFFECTS:
        if e["id"] == effect_id:
            return e["sink"][lang]
    raise KeyError(effect_id)


def _st(lang, s):
    """A statement prefix for a one-line body."""
    if not s:
        return ""
    return (s + "; ") if lang == "swift" else (s + " ")


def _bodies(lang, variant):
    fs = _sink("fs", lang)
    far = fs if (variant == "far" and not FAULT) else ""
    near = fs if variant == "near" else ""
    return _st(lang, far), _st(lang, near)


# ===================================================================================================== rust
RS_API = '''pub trait Mapper {
    fn mapv(&self, x: i32) -> i32;
    fn other(&self) -> i32;
}
pub struct Nop;
impl Mapper for Nop {
    fn mapv(&self, x: i32) -> i32 { x }
    fn other(&self) -> i32 { 0 }
}
pub trait Sink {
    fn put<T: Mapper>(&self, v: &T) -> i32;
    fn fwd(&self) -> i32;
}
'''
RS_DOC = '''pub struct Doc;
impl Sink for Doc {
    fn put<T: Mapper>(&self, v: &T) -> i32 { %(BUSY)sv.mapv(1) }
    fn fwd(&self) -> i32 { %(FS)s0 }
}
'''
RS_MID = '''pub fn mid_via<S: Sink, T: Mapper>(s: &S, v: &T) -> i32 { s.put(v) }
pub fn mid_fwd<S: Sink>(s: &S) -> i32 { s.fwd() }
'''
RS_IMPL = '''pub struct Mine;
impl Mapper for Mine {
    fn mapv(&self, x: i32) -> i32 { %(FAR)sx }
    fn other(&self) -> i32 { %(NEAR)s0 }
}
pub struct Other;
impl Other {
    pub fn mapv(&self, x: i32) -> i32 { %(OTHER)sx }
}
'''
RS_FUNCS = '''pub fn c_via<S: Sink>(s: &S) -> i32 { %(ENV)s mid_via(s, &Mine) }
pub fn c_direct<S: Sink>(s: &S) -> i32 { %(ENV)s s.put(&Mine) }
pub fn c_fwd<S: Sink>(s: &S) -> i32 { %(ENV)s mid_fwd(s) }
'''

# ===================================================================================================== java
JV_MAPPER = 'package api;\npublic interface Mapper {\n  int mapv(int x);\n  int other();\n}\n'
JV_SINK = 'package api;\npublic interface Sink {\n  int put(Mapper v);\n  int fwd();\n}\n'
JV_NOP = ('package api;\npublic class Nop implements Mapper {\n  public int mapv(int x) { return x; }\n'
          '  public int other() { return 0; }\n}\n')
JV_DOC = '''package %(PKG)s;
public class Doc implements api.Sink {
  public int put(api.Mapper v) { %(BUSY)sreturn v.mapv(1); }
  public int fwd() { %(FS)sreturn 0; }
}
'''
JV_MID = '''package mid;
public class Mid {
  public static int via(api.Sink s, api.Mapper v) { return s.put(v); }
  public static int fwd(api.Sink s) { return s.fwd(); }
}
'''
JV_MINE = '''package app;
public class Mine implements api.Mapper {
  public int mapv(int x) { %(FAR)sreturn x; }
  public int other() { %(NEAR)sreturn 0; }
}
'''
JV_OTHER = 'package app;\npublic class Other {\n  public int mapv(int x) { %(OTHER)sreturn x; }\n}\n'
JV_FUNCS = '''package app;
public class App {
  public static int c_via(api.Sink s) { %(ENV)s return mid.Mid.via(s, new Mine()); }
  public static int c_direct(api.Sink s) { %(ENV)s return s.put(new Mine()); }
  public static int c_fwd(api.Sink s) { %(ENV)s return mid.Mid.fwd(s); }
}
'''

# ===================================================================================================== ts
TS_API = '''export interface Mapper {
  mapv(x: number): number;
  other(): number;
}
export class Nop implements Mapper {
  mapv(x: number): number { return x; }
  other(): number { return 0; }
}
export interface Sink {
  put(v: Mapper): number;
  fwd(): number;
}
'''
TS_DOC = '''export class Doc implements Sink {
  put(v: Mapper): number { %(BUSY)sreturn v.mapv(1); }
  fwd(): number { %(FS)sreturn 0; }
}
'''
TS_MID = '''export function mid_via(s: Sink, v: Mapper): number { return s.put(v); }
export function mid_fwd(s: Sink): number { return s.fwd(); }
'''
TS_IMPL = '''export class Mine implements Mapper {
  mapv(x: number): number { %(FAR)sreturn x; }
  other(): number { %(NEAR)sreturn 0; }
}
export class Other {
  mapv(x: number): number { %(OTHER)sreturn x; }
}
'''
TS_FUNCS = '''export function c_via(s: Sink): number { %(ENV)s return mid_via(s, new Mine()); }
export function c_direct(s: Sink): number { %(ENV)s return s.put(new Mine()); }
export function c_fwd(s: Sink): number { %(ENV)s return mid_fwd(s); }
'''

# ===================================================================================================== swift
SW_API = '''public protocol Mapper {
    func mapv(_ x: Int) -> Int
    func other() -> Int
}
public struct Nop: Mapper {
    public init() {}
    public func mapv(_ x: Int) -> Int { x }
    public func other() -> Int { 0 }
}
public protocol Sink {
    func put(_ v: any Mapper) -> Int
    func fwd() -> Int
}
'''
SW_DOC = '''public struct Doc: Sink {
    public init() {}
    public func put(_ v: any Mapper) -> Int { %(BUSY)sreturn v.mapv(1) }
    public func fwd() -> Int { %(FS)sreturn 0 }
}
'''
SW_MID = '''public func mid_via(_ s: any Sink, _ v: any Mapper) -> Int { s.put(v) }
public func mid_fwd(_ s: any Sink) -> Int { s.fwd() }
'''
SW_IMPL = '''public struct Mine: Mapper {
    public init() {}
    public func mapv(_ x: Int) -> Int { %(FAR)sreturn x }
    public func other() -> Int { %(NEAR)sreturn 0 }
}
public struct Other {
    public init() {}
    public func mapv(_ x: Int) -> Int { %(OTHER)sreturn x }
}
'''
SW_FUNCS = '''public func c_via(_ s: any Sink) -> Int {
    %(ENV)s
    return mid_via(s, Mine())
}
public func c_direct(_ s: any Sink) -> Int {
    %(ENV)s
    return s.put(Mine())
}
public func c_fwd(_ s: any Sink) -> Int {
    %(ENV)s
    return mid_fwd(s)
}
'''
SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')

TEXT = {
    "rust": (RS_API, RS_DOC, RS_MID, RS_IMPL, RS_FUNCS),
    "ts": (TS_API, TS_DOC, TS_MID, TS_IMPL, TS_FUNCS),
    "swift": (SW_API, SW_DOC, SW_MID, SW_IMPL, SW_FUNCS),
}


def consumer_funcs(lang):
    env = _sink("env", lang)
    if lang == "swift":
        return SW_FUNCS % dict(ENV=env)
    return {"rust": RS_FUNCS, "java": JV_FUNCS, "ts": TS_FUNCS}[lang] % dict(ENV=env)


def _impl_vars(lang, variant):
    far, near = _bodies(lang, variant)
    other = _st(lang, _sink("fs", lang))
    return dict(FAR=far, NEAR=near, OTHER=other)


def _doc_vars(lang, shape):
    """`busy`: Doc.put performs Clock of its own, so the union under Sink.put is NOT pure and is published
    with an effect — a consumer that finds the key and trusts the union then has nothing telling it the
    union's contributor dispatches further. `bare`: Doc.put only dispatches (the aws-smithy shape)."""
    return dict(FS=_st(lang, _sink("fs", lang)), BUSY=_st(lang, _sink("clock", lang)) if shape == "busy" else "")


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


# THE CROSS-SPELLING ARM (Fable REVIEW3 B3-E1). Rule 2 binds every consumer to follow BOTH union spellings. The
# `deep` shape puts the further dispatch one helper below the contributor (Doc.put -> helper -> v.mapv), so a union
# in spelling (b) (`calls` naming the contributor, no `dispatchesOn` — Doc.put dispatches nothing itself) reaches the
# member only through the consumer's walk of the union's `calls`, and spelling (a) only through its transitive key.
DEEP_DOC = {
    "rust": """pub struct Doc;
pub fn helper<T: Mapper>(v: &T) -> i32 { v.mapv(1) }
impl Sink for Doc {
    fn put<T: Mapper>(&self, v: &T) -> i32 { %(BUSY)shelper(v) }
    fn fwd(&self) -> i32 { %(FS)s0 }
}
""",
    "java": """package %(PKG)s;
public class Doc implements api.Sink {
  static int helper(api.Mapper v) { return v.mapv(1); }
  public int put(api.Mapper v) { %(BUSY)sreturn helper(v); }
  public int fwd() { %(FS)sreturn 0; }
}
""",
    "ts": """export function helper(v: Mapper): number { return v.mapv(1); }
export class Doc implements Sink {
  put(v: Mapper): number { %(BUSY)sreturn helper(v); }
  fwd(): number { %(FS)sreturn 0; }
}
""",
    "swift": """public func helper(_ v: any Mapper) -> Int { v.mapv(1) }
public struct Doc: Sink {
    public init() {}
    public func put(_ v: any Mapper) -> Int { %(BUSY)sreturn helper(v) }
    public func fwd() -> Int { %(FS)sreturn 0 }
}
""",
}
MAPV_KEY = {"rust": "api#Mapper::mapv", "java": "api/Mapper.mapv(I)I", "ts": "api#Mapper.mapv", "swift": "Api#Mapper.mapv"}
# The spelling each engine's OWN producer writes for rows today (measured, B-E1-spellings.txt): the native arm is the
# CONTROL that proves the doctored union reached the consumer; the cross arm is rule 2's other half.
NATIVE = {"rust": "a", "ts": "a", "swift": "a", "java": "b"}


def render(lang, root, layout, sv):
    if layout == "unchained":
        layout = "foreign"   # the same packages; only the consumer's CHAIN omits api (see run_engine)
    """Returns (packages, app_dir, api_text): `packages` is [(name, dir, [dep names])] in chain order,
    the consumer last. `one` is a single package."""
    shape, variant = sv
    if lang == "java":
        return _render_java(root, layout, shape, variant)
    api, doc, mid, impl, _funcs = TEXT[lang]
    if shape == "deep":
        doc, shape = DEEP_DOC[lang], "busy"
    doc_t = doc % _doc_vars(lang, shape)
    impl_t = impl % _impl_vars(lang, variant)
    funcs = consumer_funcs(lang)
    if lang == "rust":
        return _render_rust(root, layout, api, doc_t, mid, impl_t, funcs)
    if lang == "ts":
        return _render_ts(root, layout, api, doc_t, mid, impl_t, funcs)
    return _render_swift(root, layout, api, doc_t, mid, impl_t, funcs)


def _render_rust(root, layout, api, doc, mid, impl, funcs):
    cargo = '[package]\nname="%s"\nversion="0.0.0"\nedition="2021"\n'

    def crate(name, deps, text):
        d = os.path.join(root, name)
        toml = cargo % name
        if deps:
            toml += "\n[dependencies]\n" + "".join('%s={path="../%s"}\n' % (x, x) for x in deps)
        _w(os.path.join(d, "Cargo.toml"), toml)
        _w(os.path.join(d, "src", "lib.rs"), text)
        return d

    if layout == "one":
        app = crate("app", [], api + "\n" + doc + "\n" + mid + "\n" + impl + "\n" + funcs)
        return [("app", app, [])], app, api
    pk = []
    if layout == "local":
        pk.append(("api", crate("api", [], api + "\n" + doc), []))
    else:
        pk.append(("api", crate("api", [], api), []))
        pk.append(("prod", crate("prod", ["api"], "use api::{Mapper, Sink};\n\n" + doc), ["api"]))
    pk.append(("mid", crate("mid", ["api"], "use api::{Mapper, Sink};\n\n" + mid), ["api"]))
    deps = [p[0] for p in pk]
    app = crate("app", deps, "use api::{Mapper, Sink};\nuse mid::{mid_via, mid_fwd};\n\n" + impl + "\n" + funcs)
    pk.append(("app", app, deps))
    return pk, app, api


def _render_ts(root, layout, api, doc, mid, impl, funcs):
    types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
    fsimp = 'import * as fsm from "node:fs";\n'

    def pkg(name, deps, text):
        d = os.path.join(root, name)
        dj = ',"dependencies":{%s}' % ",".join('"%s":"file:../%s"' % (x, x) for x in deps) if deps else ""
        _w(os.path.join(d, "package.json"), '{"name":"%s","version":"0.0.0","main":"src/index.ts"%s}\n' % (name, dj))
        _w(os.path.join(d, "src", "index.ts"), text)
        for x in deps:
            _link(os.path.join(d, "node_modules", x), os.path.join(root, x))
        if os.path.isdir(types):
            _link(os.path.join(d, "node_modules", "@types"), types)
        return d

    imp = 'import { type Mapper, type Sink } from "%s";\n'
    if layout == "one":
        d = os.path.join(root, "app")
        _w(os.path.join(d, "src", "api.ts"), api)
        _w(os.path.join(d, "src", "doc.ts"), fsimp + (imp % "./api.js") + "\n" + doc)
        _w(os.path.join(d, "src", "mid.ts"), (imp % "./api.js") + "\n" + mid)
        app = pkg("app", [], fsimp + (imp % "./api.js") + 'import { mid_via, mid_fwd } from "./mid.js";\n'
                  'export { Doc } from "./doc.js";\n\n' + impl + "\n" + funcs)
        return [("app", app, [])], app, api
    pk = []
    if layout == "local":
        pk.append(("api", pkg("api", [], fsimp + api + "\n" + doc), []))
    else:
        pk.append(("api", pkg("api", [], api), []))
        pk.append(("prod", pkg("prod", ["api"], fsimp + (imp % "api") + "\n" + doc), ["api"]))
    pk.append(("mid", pkg("mid", ["api"], (imp % "api") + "\n" + mid), ["api"]))
    deps = [p[0] for p in pk]
    app = pkg("app", deps, fsimp + (imp % "api") + 'import { mid_via, mid_fwd } from "mid";\n\n' + impl + "\n" + funcs)
    pk.append(("app", app, deps))
    return pk, app, api


def _render_swift(root, layout, api, doc, mid, impl, funcs):
    mods = {"api": "Api", "prod": "Prod", "mid": "Mid", "app": "App"}

    def pkg(name, deps, text):
        d = os.path.join(root, name)
        mod = mods[name]
        _w(os.path.join(d, "Package.swift"), SW_MANIFEST % dict(
            mod=mod, deps=", ".join('.package(path: "../%s")' % x for x in deps),
            prods=", ".join('.product(name: "%s", package: "%s")' % (mods[x], x) for x in deps)))
        _w(os.path.join(d, "Sources", mod, "lib.swift"), text)
        return d

    if layout == "one":
        d = os.path.join(root, "app")
        _w(os.path.join(d, "Package.swift"), SW_MANIFEST % dict(mod="App", deps="", prods=""))
        _w(os.path.join(d, "Sources", "App", "api.swift"), api)
        _w(os.path.join(d, "Sources", "App", "doc.swift"), "import Foundation\n\n" + doc)
        _w(os.path.join(d, "Sources", "App", "mid.swift"), mid)
        _w(os.path.join(d, "Sources", "App", "app.swift"), "import Foundation\n\n" + impl + "\n" + funcs)
        return [("app", d, [])], d, api
    pk = []
    if layout == "local":
        pk.append(("api", pkg("api", [], "import Foundation\n\n" + api + "\n" + doc), []))
    else:
        pk.append(("api", pkg("api", [], api), []))
        pk.append(("prod", pkg("prod", ["api"], "import Foundation\nimport Api\n\n" + doc), ["api"]))
    pk.append(("mid", pkg("mid", ["api"], "import Api\n\n" + mid), ["api"]))
    deps = [p[0] for p in pk]
    app = pkg("app", deps, "import Foundation\nimport Api\nimport Mid\n\n" + impl + "\n" + funcs)
    pk.append(("app", app, deps))
    return pk, app, api


def _render_java(root, layout, shape, variant):
    src = os.path.join(root, "src")
    if os.path.isdir(src):
        shutil.rmtree(src)
    docpkg = "prod" if layout == "foreign" else "api"
    _w(os.path.join(src, "api", "Mapper.java"), JV_MAPPER)
    _w(os.path.join(src, "api", "Sink.java"), JV_SINK)
    _w(os.path.join(src, "api", "Nop.java"), JV_NOP)
    jdoc, jshape = (DEEP_DOC["java"], "busy") if shape == "deep" else (JV_DOC, shape)
    _w(os.path.join(src, docpkg, "Doc.java"), jdoc % dict(PKG=docpkg, **_doc_vars("java", jshape)))
    _w(os.path.join(src, "mid", "Mid.java"), JV_MID)
    iv = _impl_vars("java", variant)
    _w(os.path.join(src, "app", "Mine.java"), JV_MINE % iv)
    _w(os.path.join(src, "app", "Other.java"), JV_OTHER % iv)
    _w(os.path.join(src, "app", "App.java"), consumer_funcs("java"))
    if EXEC_MARK:
        _w(os.path.join(src, "app", "Run.java"),
           "package app;\npublic class Run { public static void main(String[] a) { "
           "api.Sink s = new %s.Doc(); System.out.println(a[0].equals(\"via\") ? App.c_via(s) : "
           "a[0].equals(\"direct\") ? App.c_direct(s) : App.c_fwd(s)); } }\n" % docpkg)
    cls = os.path.join(root, "cls")
    if os.path.isdir(cls):
        shutil.rmtree(cls)
    os.makedirs(cls)
    srcs = []
    for d, _dd, fs in os.walk(src):
        srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
    c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
    if c.returncode != 0:
        raise RuntimeError("javac failed: " + c.stderr.decode()[:400])
    api_text = JV_MAPPER + JV_SINK + JV_NOP
    if layout == "one":
        return [("app", cls, [])], cls, api_text
    groups = [("api", ["api"])]
    if layout == "foreign":
        groups.append(("prod", ["prod"]))
    groups += [("mid", ["mid"]), ("app", ["app"])]
    pk = []
    for name, pkgs in groups:
        d = os.path.join(root, "d_" + name)
        for p in pkgs:
            shutil.copytree(os.path.join(cls, p), os.path.join(d, p), dirs_exist_ok=True)
        pk.append((name, d, [x[0] for x in pk]))
    return pk, pk[-1][1], api_text

# THE ZERO-IMPLEMENTOR CONSUMER (Fable B-E2/B-E3). A second consumer package, `zapp`, beside `app` in every chained
# layout, with the same dependencies and NO implementor of Mapper of its own: it passes api's pure `Nop`. Under the
# clause, a key it reaches through the union joins nothing visible but `Nop`, so `deny Fs` MUST stay 0 and the
# DISCLOSURE is what a port may remove — recorded per engine, not asserted (see `none` in WANT).
Z_FUNCS = {
    "rust": "use api::{Nop, Sink};\nuse mid::mid_via;\n\npub fn c_none<S: Sink>(s: &S) -> i32 { %(ENV)s mid_via(s, &Nop) }\n",
    "java": ("package zapp;\npublic class Z {\n  public static int c_none(api.Sink s) { %(ENV)s return mid.Mid.via(s, new "
             "api.Nop()); }\n}\n"),
    "ts": ('import { type Sink, Nop } from "api";\nimport { mid_via } from "mid";\n\n'
           "export function c_none(s: Sink): number { %(ENV)s return mid_via(s, new Nop()); }\n"),
    "swift": "import Foundation\nimport Api\nimport Mid\n\npublic func c_none(_ s: any Sink) -> Int {\n    %(ENV)s\n    return mid_via(s, Nop())\n}\n",
}


def render_zero(lang, root, deps):
    """Lay `zapp` out beside the chained packages; returns its scan target."""
    text = Z_FUNCS[lang] % dict(ENV=_sink("env", lang))
    d = os.path.join(root, "zapp")
    if lang == "rust":
        _w(os.path.join(d, "Cargo.toml"), '[package]\nname="zapp"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\n'
           + "".join('%s={path="../%s"}\n' % (x, x) for x in deps))
        _w(os.path.join(d, "src", "lib.rs"), text)
        return d
    if lang == "java":
        src = os.path.join(root, "zsrc", "zapp", "Z.java")
        _w(src, text)
        c = gd.run(["javac", "-nowarn", "-cp", os.path.join(root, "cls"), "-d", os.path.join(root, "d_zapp"), src])
        if c.returncode != 0:
            raise RuntimeError("javac (zapp) failed: " + c.stderr.decode()[:400])
        return os.path.join(root, "d_zapp")
    if lang == "ts":
        dj = ",".join('"%s":"file:../%s"' % (x, x) for x in deps)
        _w(os.path.join(d, "package.json"), '{"name":"zapp","version":"0.0.0","main":"src/index.ts","dependencies":{%s}}\n' % dj)
        _w(os.path.join(d, "src", "index.ts"), text)
        for x in deps:
            _link(os.path.join(d, "node_modules", x), os.path.join(root, x))
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        if os.path.isdir(types):
            _link(os.path.join(d, "node_modules", "@types"), types)
        return d
    mods = {"api": "Api", "prod": "Prod", "mid": "Mid"}
    _w(os.path.join(d, "Package.swift"), SW_MANIFEST % dict(
        mod="Zapp", deps=", ".join('.package(path: "../%s")' % x for x in deps),
        prods=", ".join('.product(name: "%s", package: "%s")' % (mods[x], x) for x in deps)))
    _w(os.path.join(d, "Sources", "Zapp", "lib.swift"), text)
    return d


def build_proof(lang, app):
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


def union_diag(report_path, pkgname):
    """The producer leg, PRINTED: every union entry and every row naming Sink.put / Mapper.mapv."""
    out = []
    try:
        rep = json.load(open(report_path))
    except Exception as e:      # noqa: BLE001
        return ["    %s: unreadable report (%s)" % (pkgname, e)]
    for f in rep.get("functions") or []:
        fn, h = f.get("fn") or "", f.get("hash") or ""
        if f.get("interfaceUnion") or ("Doc" in fn and _leaf(fn) == "put"):
            out.append("    %-5s %s%s inferred=%s why=%s dispatchesOn=%s" % (
                pkgname, "UNION " if f.get("interfaceUnion") else "", h or fn, f.get("inferred"),
                f.get("unknownWhy"), f.get("dispatchesOn")))
    return out or ["    %-5s (no union entry, no Doc.put row)" % pkgname]


def run_engine(lang, ws, diag):
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, None, scanner.err
    results, notes, apis, funcs_seen = {}, [], set(), set()
    arms = arms_for(lang)
    for layout, shape, variant in ((la, sh, va) for la in LAYOUTS for sh in SHAPES for va in VARIANTS):
        sv = (shape, variant)
        root = os.path.join(ws, lang, layout, shape, variant)
        os.makedirs(root, exist_ok=True)
        try:
            pk, app, api = render(lang, root, layout, sv)
        except RuntimeError as e:
            return None, None, "%s/%s/%s/%s: %s" % (lang, layout, shape, variant, e)
        apis.add(api)
        funcs_seen.add(consumer_funcs(lang))
        err = build_proof(lang, app)
        if err and err.startswith("SKIPPED"):
            notes.append("  NOTE  %s %s/%s %s" % (lang, layout, variant, err))
        elif err:
            return None, None, "%s (%s/%s)" % (err, layout, variant)
        reports = {}
        for name, d, deps in pk[:-1]:
            r = scanner.scan(d, deps=[reports[x] for x in deps])
            if not r.produced:
                return None, None, "%s/%s: %s scan produced no report (rc=%d) %s" % (
                    layout, variant, name, r.rc, r.note)
            # Copy out: a later scan of a sibling must not be able to overwrite what we chain.
            keep = os.path.join(root, "rep_%s.json" % name)
            shutil.copy(r.report, keep)
            reports[name] = keep
            if variant == "far":
                diag.extend("  [%s %s %s] %s" % (lang, layout, shape, x) for x in union_diag(keep, name))
        # `unchained`: the consumer chains the implementor's package and the dispatcher but NOT the abstraction's
        # owner, so a key a union names under `api#…` has no chained entry to hit (Fable B-E3, the owner-unchained
        # removal bucket). Every producer scan is unchanged.
        app_deps = [reports[x] for x in pk[-1][2] if not (layout == "unchained" and x == "api")]
        r = scanner.scan(app, deps=app_deps)
        if not r.produced:
            return None, None, "%s/%s: consumer scan produced no report (rc=%d) %s" % (
                layout, variant, r.rc, r.note)
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, None, "%s/%s: analyzed.count is 0 — a hollow report judges nothing" % (layout, variant)
        rows = {_leaf(f.get("fn")): f for f in rep.get("functions") or []
                if _leaf(f.get("fn")) in FUNCS.values()}
        ztarget = None
        if layout != "one" and variant == "far":
            try:
                ztarget = render_zero(lang, root, pk[-1][2])
            except RuntimeError as e:
                return None, None, "%s/%s/%s zapp: %s" % (lang, layout, shape, e)
            zerr = build_proof(lang, ztarget)
            if zerr and not zerr.startswith("SKIPPED"):
                return None, None, "%s (zapp %s/%s)" % (zerr, layout, shape)
            zr = scanner.scan(ztarget, deps=app_deps)
            if not zr.produced:
                return None, None, "%s/%s: zapp scan produced no report (rc=%d) %s" % (layout, shape, zr.rc, zr.note)
            # NO Other.mapv seed check here, deliberately (Fable REVIEW2): `Other` lives in `app`, which zapp neither
            # contains nor chains, so a name-only join on zapp has nothing to join and the seed cannot exist. Do not
            # "fix" the app-side seed check to cover zapp; it would make this arm BROKEN on every engine.
            for f in json.load(open(zr.report)).get("functions") or []:
                if _leaf(f.get("fn")) == "c_none":
                    rows["c_none"] = f
        seeded = [f for f in rep.get("functions") or []
                  if "Other" in (f.get("fn") or "") and "Fs" in (f.get("inferred") or [])]
        if not seeded:
            return None, None, ("%s/%s: Other.mapv is not charged Fs in the consumer report — the name-only "
                                "control's seed is dead, so the near-arm zeros would be vacuous" % (layout, variant))
        pol_dir = os.path.join(root, "pol")
        os.makedirs(pol_dir, exist_ok=True)
        for arm_id, lay, var, fk, kind in arms:
            if lay != layout or var != sv:
                continue
            fn = FUNCS[fk]
            row = rows.get(fn)
            if row is None:
                results[arm_id] = (False, "ABSENT from functions[] — the Env carrier is missing, a "
                                          "purity claim (SPEC §2 rule 3)")
                continue
            got, bad = {}, []
            wants = dict(WANT[kind])
            # `busy`: Doc.put's own Clock reaches every consumer that runs Doc.put, so a port that trades the
            # union's own effect for the key (B-E5) reddens here — `*_fwd` is a different union entry.
            if sv[0] == "busy" and fk in ("via", "direct", "none"):
                wants["deny Clock"] = 1
            # `none`: the DISCLOSURE is recorded, not asserted — a key with no visible implementor may correctly
            # read pure (every visible implementor is pure) or stay hedged; a port's move here is a removal to
            # account for against this column (the 0.40.15 values are in the NOTE beside the part in run.sh).
            if kind == "none":
                wants["deny Fs Unknown"] = None
            for i, (pol, want) in enumerate(sorted(wants.items())):
                pp = os.path.join(pol_dir, "%s_%d.policy" % (fn, i))
                with open(pp, "w") as f:
                    f.write("%s %s\n" % (pol, row["fn"]))
                rc = gate(scanner, ztarget if fk == "none" else app, app_deps, pp)
                got[pol] = rc
                if want is not None and rc != want:
                    bad.append("`%s` exit %d want %d" % (pol, rc, want))
            detail = "inferred=%s gates=%s" % (sorted(row.get("inferred") or []),
                                              " ".join("[%s]=%d" % (p, c) for p, c in sorted(got.items())))
            results[arm_id] = (not bad, detail + ("" if not bad else " — " + "; ".join(bad)))
    if len(apis) != 1 or len(funcs_seen) != 1:
        return None, None, ("the abstraction text or the consumer functions differ between fixtures — the "
                            "comparison is FIXTURE-INDUCED and no cell here is evidence")
    return results, notes, None


def cross_arms():
    out = []
    for which in ("n", "c"):
        for layout in ("local", "foreign"):
            for fk in ("via", "direct"):
                out.append(("x%s_%s_%s" % (which, layout, fk), layout, which, fk, "spell" if which == "n" else "cross"))
    return out


def _spell(f, spelling, lang, contributor_fn):
    """Re-spell ONE union entry. (a): the transitive key, no `calls`. (b): `calls` naming the contributor, and the
    contributor's DIRECT members in `dispatchesOn` — none here, since Doc.put dispatches only through its helper."""
    f.pop("calls", None)
    f.pop("dispatchesOn", None)
    if spelling == "a":
        f["dispatchesOn"] = [MAPV_KEY[lang]]
    else:
        f["calls"] = [contributor_fn]


def run_cross(lang, ws):
    """The doctored-producer arm: real producer reports for the `deep` shape, the Sink.put union re-spelled in the
    engine's NATIVE spelling (control) and in the OTHER one (rule 2's cross-spelling duty)."""
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, scanner.err
    results = {}
    for layout in ("local", "foreign"):
        root = os.path.join(ws, lang, "cross", layout)
        os.makedirs(root, exist_ok=True)
        try:
            pk, app, _ = render(lang, root, layout, ("deep", "far"))
        except RuntimeError as e:
            return None, "cross %s: %s" % (layout, e)
        err = build_proof(lang, app)
        if err and not err.startswith("SKIPPED"):
            return None, "%s (cross %s)" % (err, layout)
        reps = {}
        for name, d, deps in pk[:-1]:
            r = scanner.scan(d, deps=[reps[x] for x in deps])
            if not r.produced:
                return None, "cross %s: %s scan produced no report" % (layout, name)
            keep = os.path.join(root, "rep_%s.json" % name)
            shutil.copy(r.report, keep)
            reps[name] = keep
        holder = "api" if layout == "local" else "prod"
        base = json.load(open(reps[holder]))
        contrib = [f.get("fn") for f in base.get("functions") or []
                   if not f.get("interfaceUnion") and "Doc" in (f.get("fn") or "") and _leaf(f.get("fn")) == "put"]
        unions = [f for f in base.get("functions") or [] if f.get("interfaceUnion") and _leaf(f.get("fn")) == "put"]
        if not contrib or not unions:
            return None, ("cross %s: the producer report has no Doc.put row or no Sink.put union (%d/%d) — the doctor "
                          "has nothing to re-spell, so no cell here is evidence" % (layout, len(contrib), len(unions)))
        for which in ("n", "c"):
            spelling = NATIVE[lang] if which == "n" else ("b" if NATIVE[lang] == "a" else "a")
            rep_ = json.loads(json.dumps(base))
            for f in rep_["functions"]:
                if f.get("interfaceUnion") and _leaf(f.get("fn")) == "put":
                    _spell(f, spelling, lang, contrib[0])
            dfile = os.path.join(root, "rep_%s_%s.json" % (holder, spelling))
            json.dump(rep_, open(dfile, "w"))
            deps = [(dfile if x == holder else reps[x]) for x in pk[-1][2]]
            r = scanner.scan(app, deps=deps)
            if not r.produced:
                return None, "cross %s: consumer scan produced no report" % layout
            rows = {_leaf(f.get("fn")): f for f in json.load(open(r.report)).get("functions") or []}
            for fk in ("via", "direct"):
                arm = "x%s_%s_%s" % (which, layout, fk)
                row = rows.get(FUNCS[fk])
                if row is None:
                    results[arm] = (False, "ABSENT from functions[] — the Env carrier is missing")
                    continue
                got, bad = {}, []
                for i, (pol, want) in enumerate(sorted(WANT["carry"].items())):
                    pp = os.path.join(root, "x_%s_%s_%d.policy" % (which, fk, i))
                    with open(pp, "w") as fh:
                        fh.write("%s %s\n" % (pol, row["fn"]))
                    rc = gate(scanner, app, deps, pp)
                    got[pol] = rc
                    if rc != want:
                        bad.append("`%s` exit %d want %d" % (pol, rc, want))
                results[arm] = (not bad, "spelling (%s) inferred=%s gates=%s%s" % (
                    spelling, sorted(row.get("inferred") or []),
                    " ".join("[%s]=%d" % (p_, c) for p_, c in sorted(got.items())),
                    "" if not bad else " — " + "; ".join(bad)))
    return results, None


def main():
    import tempfile
    print("=" * 100)
    print("UNION-ENTRY FURTHER DISPATCH §4 ⟨0.39⟩/⟨0.40⟩ — a member an interfaceUnion's contributor dispatches on")
    print("reaches the consumer that reaches the union")
    print("  fixture : api Mapper{mapv,other} + Sink{put(Mapper),fwd}; Doc: Sink { put(v){ v.mapv() } fwd(){Fs} };")
    print("            mid dispatches Sink.put / Sink.fwd; app supplies Mine: Mapper and never names Doc")
    print("  property: *_far_via / *_far_direct -> `deny Fs` and `deny Fs Unknown` FIRE (Mine.mapv does Fs)")
    print("            *_fwd -> Doc.fwd's own Fs through the union (proves the chain)")
    print("            *_near_via / *_near_direct -> `deny Fs` stays 0 (Mine.other does Fs, nobody dispatches it)")
    print("            `deny Env` fires on every cell — the carrier that proves the scope matched")
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART102_NOBUILD is set — rust/ts/swift fixtures were NOT built; iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — Mine.mapv is rendered WITHOUT its Fs, so the w_far_via /")
        print("       w_far_direct REFERENCE arms, which every engine passes clean, must go red.")
    only = [e for e in (os.environ.get("CANDOR_PART102_ONLY") or "").split(",") if e]
    if "--engine" in sys.argv[1:]:
        # probe_check.py's short arm: one engine is enough to reach live REFERENCE cells for the fault.
        only = [sys.argv[sys.argv.index("--engine") + 1]]
    ws = tempfile.mkdtemp(prefix="candor-part102-")
    bad = stale = live = 0
    diag = []
    for lang in ENGINES:
        if only and lang not in only:
            continue
        res, notes, err = run_engine(lang, ws, diag)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                print("  %-6s -> SKIP (%s)" % (lang, err))
            else:
                print("  %-6s -> BROKEN: %s" % (lang, err))
                bad += 1
            continue
        xres, xerr = run_cross(lang, ws)
        if xerr:
            print("  %-6s -> BROKEN (cross-spelling arm): %s" % (lang, xerr))
            bad += 1
            xres = {}
        res.update(xres)
        live += 1
        for n in notes:
            print(n)
        for arm_id, _lay, _var, _fk, kind in arms_for(lang) + (cross_arms() if xres else []):
            ok, detail = res[arm_id]
            key = (arm_id, lang)
            if ok and key in XFAIL:
                print("  XFAIL ARM PASSED  %-20s %-6s — expectation is STALE: %s" % (arm_id, lang, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-20s %-6s %s" % (arm_id, lang, detail))
            elif key in XFAIL:
                print("  xfail %-20s %-6s %s  [%s]" % (arm_id, lang, detail, XFAIL[key]))
            else:
                print("  FAIL  %-20s %-6s %s  [%s]" % (arm_id, lang, detail, WHY[kind]))
                bad += 1
    if diag:
        print("  producer union entries (diagnostic, the `far` variant; the part asserts none of this):")
        for d in diag:
            print(d)
    if os.environ.get("CANDOR_PART102_KEEP"):
        print("  workspace kept: %s" % ws)
    else:
        shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("UNION-DISPATCH: no engine available — NOT a pass")
        return 2
    if stale:
        print("UNION-DISPATCH: %d xfail arm(s) PASSED — an expectation that has become true is a FAILURE here. "
              "Retire it in the same commit as the engine fix." % stale)
    if bad:
        print("UNION-DISPATCH: %d cell(s) wrong — see SPEC §4 ⟨0.40⟩ (union `dispatchesOn`) and SOUNDNESS R1324"
              % bad)
    if not bad and not stale:
        print("UNION-DISPATCH: OK — every reference charges, every control stays exact, and every open defect "
              "cell is declared")
    return 1 if (bad or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
