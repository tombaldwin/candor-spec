#!/usr/bin/env python3
"""PART 110 — ONE CALL ANSWERED BY A CHAINED ROW AND A CURATED ENTRY: THE UNION, FOUR-WAY, SPEC §2 ⟨0.43⟩.

SOUNDNESS R1815 (the clause and this part), R1807 (rust, closed by union), R685 (java), R696 (ts). Three engines
found this one defect by hand, each fixing it by union, with nothing pinning the rule across the family: a call into
a CHAINED dependency that the engine's CURATED classifier also names. SPEC §2 used to say a dependency scan
"replaces" the curated entry, and read literally that sentence is the "row wins" rule; read the other way, an engine
skips the join because the classifier answered ("curated wins"). Both are toggles: each lets one source WITHDRAW the
other's answer. ⟨0.43⟩ makes the answer the UNION, on every spelling of the call.

THE FIXTURE, in every language. One dependency package under a name the engine's curated classifier knows
(rust `sqlx_core` → `Db` on `fetch_all`; java `org.slf4j.*` → `Log` on `info`; ts `winston` → `Log` on every
member; swift `HTTPClient` → `Net` on `get`/`post`/`put`), holding four members the consumer calls:

    c   the curated verb, body WRITES the file it is given            row: [Fs]          (concrete)
    u   the curated verb, body reads the clock; the producer report
        is DOCTORED so the row reads [Unknown] with a reason           row: [Unknown]     (Unknown-only)
    p   the curated verb, body pure                                    no row             (pure: the covered
                                                                                           report's purity claim)
    q   a member the classifier does NOT name, body pure               no row             (the pure twin)
        — except on ts, whose κ rule for `winston` names EVERY member of the module: there `q` is a second pure
        CURATED member (no non-curated member exists inside a whole-module rule) and still refuses a fabricated Fs

and a consumer that calls each one in every spelling its language has (typed parameter, path/UFCS, `let x: T`,
untyped `let x = make()`, a method on a returned value, a method on a constructed value). Every consumer function
also reads the environment — the CARRIER that proves the function was analysed and the row is the right one.

THE LAYOUTS. `ch` — the dependency report chained (the clause's case). `st` — the same report with its producing
version rewritten, so §2.1 downgrades every entry to `Unknown`: the clause's "an entry §2.1 downgraded is unioned
like any other" (Fable R1807 Q2 edit 2). `nc` — the dependency NOT chained: no loaded report covers it, the call
joins no entry, and the classifier's charge is the whole of what the clause requires (Fable edit 1).

WHAT EACH CELL ASSERTS (the effect SET of the consumer's row, `inferred`, not a gate exit):
    ch  c → ⊇ {cur, Fs};   u → ⊇ {cur, Unknown} AND `unknownWhy` carries the doctored reason;   p → ⊇ {cur};
        q → no curated, no Fs
    st  c,u → ⊇ {cur, Unknown};                        p → ⊇ {cur};   q → no curated, no Fs
    nc  c,u,p → ⊇ {cur};  q → no curated;  and on a CUR_NOT_TYPED spelling (no curated source at all) the cell MUST
        disclose — `Unknown` or `invisible` — because nothing charges the call (never `ok` over a silent cell)
and in every cell: Env (the carrier) present, and NO concrete effect outside what the cell's sources supply
(cur, the row's concrete effects, Env) — a `Clock` on `u` is a consumer that read the doctored body back, an `Fs`
on `p`/`q` a fabrication. An `Unknown` the cell does not require is permitted (SPEC §4: over-disclosure is never
the cardinal sin) and PRINTED as INFO, so a spelling-dependent hedge is visible without failing the part. On `st`,
an `Fs` carried from the downgraded `c` row is likewise PRINTED, not judged: §2.1 owns that question, not this
clause.

THE JUDGE IS SHOWN ABLE TO FAIL. Three wrong rules are computed from the same cell model and run through the same
judge, each of which MUST fail ≥1 cell, with its count printed: ROW-WINS (the row is the whole answer when the
dependency is chained), CURATED-WINS (the classifier's answer stops the join), HEDGE-DROPPED (the row's concrete
effects unioned, its `Unknown` dropped — Fable R1807 Q6's subtler C3). A judge that passes any of them is vacuous
and the part fails. Those seeds prove the judge rejects a wrong RULE. Three CELL-LEVEL seeds then mutate the
engine's OWN answers and must turn ≥1 green cell red: OWN-HEDGE (a `u` cell's row reason replaced by the engine's own
untyped-receiver hedge — the `Unknown` bytes are identical, only the reason tells them apart, Fable R1815 review §2),
HEDGE-DROPPED/CELL (the `u` row's `Unknown` and reason removed), SILENT-NC (a disclosure-required cell's `Unknown`
and `invisible` removed). A seed with no live green cell to act on says so; it is never counted as a pass.

RECEIVER TYPING IS NOT THIS CLAUSE. Where an engine's classifier cannot name a spelling at all (the unchained arm
shows no curated term there — swift's untyped `let r = makeClient()`), the curated term is not one of the cell's
sources: CUR_NOT_TYPED declares it with the reason, and every run checks the declaration against the `nc` arm, so an
engine that starts typing the receiver fails the part until the declaration is retired. The clause's observable
test is the monotone one: chaining a report must not remove a curated charge the unchained scan carries.

THE XFAIL TABLE is per (cell, engine), each naming its register row; A PASSING XFAIL IS A FAILURE.

EXECUTED GROUND TRUTH (outside the suite; Fable R1815 review, evidence copied to
~/candor-handoff/spec-r1815/evidence/): the fixture run in all four languages wrote 22 files, every one by member
`c` (rust 6, java 5, ts 5, swift 6 spellings) and none by `u`, `p` or `q`.

CALIBRATED: CANDOR_PROBE_FAULT=1 strips the joined row's Fs from every chained `c` answer after the scan (the
curated-wins rule), so every ch_c_* cell reddens; registered in probe_check.py on the java arm.
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
    ("§2 ⟨0.43⟩", "A CHAINED ROW AND A CURATED ENTRY THAT ANSWER ONE CALL ARE UNIONED"),
    ("§2 ⟨0.43⟩", "It MUST NOT skip the join because the classifier answered, and it MUST NOT withdraw the classifier's "
                  "charge because the join answered"),
    ("§2 ⟨0.43⟩", "An entry §2.1 downgraded joins like any other"),
    ("§2 ⟨0.43⟩", "A call that joins no entry adds nothing beyond the classifier's charge"),
    ("§2 ⟨0.43⟩", "chaining a report MUST NOT remove a curated charge for that member that the same call carries when "
                  "that report is not chained."),
    ("§2", "makes a hand-curated classifier entry unnecessary for what the scan covers"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
ENGINES = ("rust", "java", "ts", "swift")
LAYOUTS = ("ch", "st", "nc")
MEMBERS = ("c", "u", "p", "q")
CURATED = {"rust": "Db", "java": "Log", "ts": "Log", "swift": "Net"}
# The spellings each language has. A spelling a language lacks is NOT APPLICABLE, with the reason.
SPELLINGS = ("param", "ufcs", "annot", "untyped", "ret", "ctor")
NA = {
    ("java", "ufcs"): "Java has no uniform call syntax: an instance method is called on a receiver, and bytecode "
                      "names the owner identically for every receiver spelling",
    ("ts", "ufcs"): "TypeScript has no uniform call syntax; `T.prototype.m.call(x)` is a reflective call, a "
                    "different question (§4 reflection), not a spelling of this one",
}
# A member the curated classifier names, per engine. ts's κ rule for `winston` names EVERY member of the module, so
# its `q` is a second pure CURATED member there (the language has no non-curated member inside a whole-module rule).
def curated_names(lang, m):
    return m != "q" or lang == "ts"


# Spellings on which this engine's classifier cannot name the call AT ALL, measured on the unchained arm: the
# receiver is a value returned by a dependency function and the engine does not type it. The curated term is then
# not one of the cell's sources, and its absence is a receiver-typing limit, not this clause's union. Each entry is
# CHECKED every run against the `nc` arm: a declared spelling whose unchained answer DOES carry the curated term is a
# STALE declaration and fails the part (retire it).
CUR_NOT_TYPED = {
    ("swift", "untyped"): "candor-swift does not type `let r = makeClient()` from a dependency function's return, "
                          "so `r.get(p)` has no owner for the type-keyed classifier: unchained it reads [Env]",
    ("swift", "ret"): "as `untyped`: `makeClient().get(p)` — the receiver is an untyped returned value",
}

# Keyed by (cell, engine), each naming its row. MEASURED 2026-11-17 against the engine mains (candor-rust 61c66d4e,
# candor-java bc03641 jar 0.42.0 on JDK 21, candor-ts 59bf8ab, candor-swift 7215b50). The rust cells are existing rows
# (R1819, R1820), pre-existing on 0.42.0; R1865 and R1866 are the swift rows this part's measurement produced.
XFAIL = {
    ('ch_p_ret', 'rust'):
        'R1820 — `typeSurface.returns` publishes no factory for a type with no effectful own unit, so the untyped route cannot type the receiver and hedges it, dropping the curated Db: DISCLOSED, `deny Db` 1 unchained -> 0 chained; pre-existing on 0.42.0, byte-identical',
    ('ch_p_untyped', 'rust'):
        'R1820 — `typeSurface.returns` publishes no factory for a type with no effectful own unit, so the untyped route cannot type the receiver and hedges it, dropping the curated Db: DISCLOSED, `deny Db` 1 unchained -> 0 chained; pre-existing on 0.42.0, byte-identical',
    ('st_c_ret', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('st_c_untyped', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('st_p_ret', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('st_p_untyped', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('st_u_ret', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('st_u_untyped', 'rust'):
        'R1819 — chaining a §2.1-downgraded report withdraws the curated Db on the untyped and returned-value spellings: DISCLOSED (`Unknown` + `invisible`), `deny Db` 1 unchained -> 0 chained, `deny Db Unknown` stays 1; pre-existing on 0.42.0, byte-identical',
    ('ch_c_annot', 'swift'):
        'R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): SILENT, `deny Fs` and `deny Fs Unknown` exit 0 over a member that executes a file write',
    ('ch_c_ctor', 'swift'):
        'R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): SILENT, `deny Fs` and `deny Fs Unknown` exit 0 over a member that executes a file write',
    ('ch_c_param', 'swift'):
        'R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): SILENT, `deny Fs` and `deny Fs Unknown` exit 0 over a member that executes a file write',
    ('ch_c_ufcs', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): DISCLOSED only by the consumer's own Unknown on the unapplied-method spelling",
    ('ch_u_annot', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the row's `Unknown` and reason are dropped: SILENT, `deny Unknown` exits 0",
    ('ch_u_ctor', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the row's `Unknown` and reason are dropped: SILENT, `deny Unknown` exits 0",
    ('ch_u_param', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the row's `Unknown` and reason are dropped: SILENT, `deny Unknown` exits 0",
    ('ch_u_ufcs', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the cell's `Unknown` is the consumer's own unapplied-method hedge (`callback:computed`, present unchained too), not the row's — the doctored reason never arrives",
    ('nc_c_ret', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_c_untyped', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_p_ret', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_p_untyped', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_q_ret', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_q_untyped', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_u_ret', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('nc_u_untyped', 'swift'):
        "R1866 — swift: UNCHAINED, an untyped or returned-value receiver into an uncovered imported package reads ['Env'] with no `Unknown`, no `invisible` and no note — SILENT (`deny Fs` and `deny Fs Unknown` exit 0 over the `c` member's executed write); the same call chained discloses `dispatch:untyped cross-package receiver`",
    ('st_c_annot', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
    ('st_c_ctor', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
    ('st_c_param', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
    ('st_u_annot', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
    ('st_u_ctor', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
    ('st_u_param', 'swift'):
        "R1865 — swift: a CLASSIFIED typed call never reads the chained row, so the curated entry wins (the shape rust, java and ts each closed by union): the §2.1-downgraded entry's `Unknown` is dropped: SILENT",
}


# ----------------------------------------------------------------------------------------------- sinks
def fs_write(lang):
    """A WRITE to the path the caller passes: executable, and the same effect class in every engine."""
    return {"rust": 'let _ = std::fs::write(p, "hit");',
            "java": 'try { java.nio.file.Files.writeString(java.nio.file.Path.of(p), "hit"); } catch (Exception e) {}',
            "ts": 'fsm.writeFileSync(p, "hit");',
            "swift": 'FileManager.default.createFile(atPath: p, contents: nil)'}[lang]


def _sink(eid, lang):
    for e in gd.EFFECTS:
        if e["id"] == eid:
            return e["sink"][lang]
    raise KeyError(eid)


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


# ================================================================================================ rust
RS_DEP = '''pub mod raw_sql {
    pub struct RawC(pub String);
    pub fn raw_c(s: &str) -> RawC { RawC(s.to_string()) }
    impl RawC {
        pub fn new(s: &str) -> RawC { RawC(s.to_string()) }
        pub fn fetch_all(&self, p: &str) -> usize { %(FS)s self.0.len() + p.len() }
    }
    pub struct RawU(pub String);
    pub fn raw_u(s: &str) -> RawU { RawU(s.to_string()) }
    impl RawU {
        pub fn new(s: &str) -> RawU { RawU(s.to_string()) }
        pub fn fetch_all(&self, p: &str) -> usize { %(CLOCK)s self.0.len() + p.len() }
    }
    pub struct RawP(pub String);
    pub fn raw_p(s: &str) -> RawP { RawP(s.to_string()) }
    impl RawP {
        pub fn new(s: &str) -> RawP { RawP(s.to_string()) }
        pub fn fetch_all(&self, p: &str) -> usize { self.0.len() + p.len() }
    }
    pub struct RawQ(pub String);
    pub fn raw_q(s: &str) -> RawQ { RawQ(s.to_string()) }
    impl RawQ {
        pub fn new(s: &str) -> RawQ { RawQ(s.to_string()) }
        pub fn tally_zz(&self, p: &str) -> usize { self.0.len() + p.len() }
    }
}
'''
RS_VERB = {"c": "fetch_all", "u": "fetch_all", "p": "fetch_all", "q": "tally_zz"}
RS_CELL = {
    "param":   "pub fn cc_%(m)s_param(r: &%(T)s, p: &str) -> usize { %(ENV)s r.%(V)s(p) }",
    "ufcs":    "pub fn cc_%(m)s_ufcs(p: &str) -> usize { %(ENV)s %(T)s::%(V)s(&%(F)s(\"q\"), p) }",
    "annot":   "pub fn cc_%(m)s_annot(p: &str) -> usize { %(ENV)s let r: %(T)s = %(F)s(\"q\"); r.%(V)s(p) }",
    "untyped": "pub fn cc_%(m)s_untyped(p: &str) -> usize { %(ENV)s let r = %(F)s(\"q\"); r.%(V)s(p) }",
    "ret":     "pub fn cc_%(m)s_ret(p: &str) -> usize { %(ENV)s %(F)s(\"q\").%(V)s(p) }",
    "ctor":    "pub fn cc_%(m)s_ctor(p: &str) -> usize { %(ENV)s %(T)s::new(\"q\").%(V)s(p) }",
}


def _render_rust(root):
    dep = os.path.join(root, "sqlx_core")
    _w(os.path.join(dep, "Cargo.toml"), '[package]\nname="sqlx_core"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(dep, "src", "lib.rs"), RS_DEP % dict(FS=fs_write("rust"), CLOCK=_sink("clock", "rust")))
    app = os.path.join(root, "app")
    _w(os.path.join(app, "Cargo.toml"), '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n'
       '[dependencies]\nsqlx_core={path="../sqlx_core"}\n')
    lines = ["use sqlx_core::raw_sql::{raw_c, raw_u, raw_p, raw_q, RawC, RawU, RawP, RawQ};", ""]
    for m in MEMBERS:
        for sp in SPELLINGS:
            lines.append(RS_CELL[sp] % dict(m=m, T="Raw" + m.upper(), F="raw_" + m, V=RS_VERB[m],
                                            ENV=_sink("env", "rust")))
    _w(os.path.join(app, "src", "lib.rs"), "\n".join(lines) + "\n")
    return dep, app


# ================================================================================================ java
JV_DEP = '''package org.slf4j;
public class Log%(M)s {
  public static Log%(M)s make() { return new Log%(M)s(); }
  public int %(V)s(String p) { %(BODY)s return p.length(); }
}
'''
JV_VERB = {"c": "info", "u": "info", "p": "info", "q": "tally"}
JV_CELL = {
    "param":   "  public static int cc_%(m)s_param(org.slf4j.%(T)s r, String p) { %(ENV)s return r.%(V)s(p); }",
    "annot":   "  public static int cc_%(m)s_annot(String p) { %(ENV)s org.slf4j.%(T)s r = org.slf4j.%(T)s.make(); "
               "return r.%(V)s(p); }",
    "untyped": "  public static int cc_%(m)s_untyped(String p) { %(ENV)s var r = org.slf4j.%(T)s.make(); return r.%(V)s(p); }",
    "ret":     "  public static int cc_%(m)s_ret(String p) { %(ENV)s return org.slf4j.%(T)s.make().%(V)s(p); }",
    "ctor":    "  public static int cc_%(m)s_ctor(String p) { %(ENV)s return new org.slf4j.%(T)s().%(V)s(p); }",
}


def _render_java(root):
    src = os.path.join(root, "src")
    if os.path.isdir(src):
        shutil.rmtree(src)
    body = {"c": fs_write("java"), "u": _sink("clock", "java") + ";" if not _sink("clock", "java").endswith(";")
            else _sink("clock", "java"), "p": "", "q": ""}
    for m in MEMBERS:
        _w(os.path.join(src, "org", "slf4j", "Log%s.java" % m.upper()),
           JV_DEP % dict(M=m.upper(), V=JV_VERB[m], BODY=body[m]))
    lines = ["package app;", "public class App {"]
    for m in MEMBERS:
        for sp in SPELLINGS:
            if ("java", sp) in NA:
                continue
            lines.append(JV_CELL[sp] % dict(m=m, T="Log" + m.upper(), V=JV_VERB[m], ENV=_sink("env", "java")))
    lines.append("}")
    _w(os.path.join(src, "app", "App.java"), "\n".join(lines) + "\n")
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
    dep, app = os.path.join(root, "d_dep"), os.path.join(root, "d_app")
    for d in (dep, app):
        if os.path.isdir(d):
            shutil.rmtree(d)
    shutil.copytree(os.path.join(cls, "org"), os.path.join(dep, "org"))
    shutil.copytree(os.path.join(cls, "app"), os.path.join(app, "app"))
    return dep, app


# ================================================================================================== ts
TS_DEP = '''import * as fsm from "node:fs";
%(CLASSES)s'''
TS_CLASS = '''export class Log%(M)s {
  static make(): Log%(M)s { return new Log%(M)s(); }
  %(V)s(p: string): number { %(BODY)s return p.length; }
}
export function make%(M)s(): Log%(M)s { return new Log%(M)s(); }
'''
TS_VERB = {"c": "info", "u": "info", "p": "info", "q": "tally"}
TS_CELL = {
    "param":   "export function cc_%(m)s_param(r: %(T)s, p: string): number { %(ENV)s return r.%(V)s(p); }",
    "annot":   "export function cc_%(m)s_annot(p: string): number { %(ENV)s const r: %(T)s = make%(M)s(); "
               "return r.%(V)s(p); }",
    "untyped": "export function cc_%(m)s_untyped(p: string): number { %(ENV)s const r = make%(M)s(); return r.%(V)s(p); }",
    "ret":     "export function cc_%(m)s_ret(p: string): number { %(ENV)s return make%(M)s().%(V)s(p); }",
    "ctor":    "export function cc_%(m)s_ctor(p: string): number { %(ENV)s return new %(T)s().%(V)s(p); }",
}


def _render_ts(root):
    types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
    body = {"c": fs_write("ts"), "u": _sink("clock", "ts"), "p": "", "q": ""}
    classes = "".join(TS_CLASS % dict(M=m.upper(), V=TS_VERB[m], BODY=body[m]) for m in MEMBERS)
    dep = os.path.join(root, "winston")
    _w(os.path.join(dep, "package.json"), '{"name":"winston","version":"0.0.0","main":"src/index.ts"}\n')
    _w(os.path.join(dep, "src", "index.ts"), TS_DEP % dict(CLASSES=classes))
    if os.path.isdir(types):
        _link(os.path.join(dep, "node_modules", "@types"), types)
    app = os.path.join(root, "app")
    _w(os.path.join(app, "package.json"),
       '{"name":"app","version":"0.0.0","main":"src/index.ts","dependencies":{"winston":"file:../winston"}}\n')
    _link(os.path.join(app, "node_modules", "winston"), dep)
    if os.path.isdir(types):
        _link(os.path.join(app, "node_modules", "@types"), types)
    names = ", ".join("Log%s, make%s" % (m.upper(), m.upper()) for m in MEMBERS)
    lines = ['import { %s } from "winston";' % names, ""]
    for m in MEMBERS:
        for sp in SPELLINGS:
            if ("ts", sp) in NA:
                continue
            lines.append(TS_CELL[sp] % dict(m=m, M=m.upper(), T="Log" + m.upper(), V=TS_VERB[m],
                                            ENV=_sink("env", "ts")))
    _w(os.path.join(app, "src", "index.ts"), "\n".join(lines) + "\n")
    return dep, app


# =============================================================================================== swift
SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(pkg)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')
SW_DEP = '''import Foundation

public struct HTTPClient {
    public init() {}
    public func get(_ p: String) -> Int { %(FS)s; return p.count }
    public func post(_ p: String) -> Int { %(CLOCK)s; return p.count }
    public func put(_ p: String) -> Int { return p.count }
    public func tally(_ p: String) -> Int { return p.count }
}
public func makeClient() -> HTTPClient { HTTPClient() }
'''
SW_VERB = {"c": "get", "u": "post", "p": "put", "q": "tally"}
SW_CELL = {
    "param":   "public func cc_%(m)s_param(_ r: HTTPClient, _ p: String) -> Int {\n    %(ENV)s\n    return r.%(V)s(p)\n}",
    "ufcs":    "public func cc_%(m)s_ufcs(_ p: String) -> Int {\n    %(ENV)s\n    return HTTPClient.%(V)s(makeClient())(p)\n}",
    "annot":   "public func cc_%(m)s_annot(_ p: String) -> Int {\n    %(ENV)s\n    let r: HTTPClient = makeClient()\n"
               "    return r.%(V)s(p)\n}",
    "untyped": "public func cc_%(m)s_untyped(_ p: String) -> Int {\n    %(ENV)s\n    let r = makeClient()\n    return r.%(V)s(p)\n}",
    "ret":     "public func cc_%(m)s_ret(_ p: String) -> Int {\n    %(ENV)s\n    return makeClient().%(V)s(p)\n}",
    "ctor":    "public func cc_%(m)s_ctor(_ p: String) -> Int {\n    %(ENV)s\n    return HTTPClient().%(V)s(p)\n}",
}


def _render_swift(root):
    # The package, its directory and its module share one name: a swift join is gated on the call site's file
    # importing a COVERED package, and a package/module mismatch is a dead join (the R1523 lesson).
    dep = os.path.join(root, "AsyncHTTPClient")
    _w(os.path.join(dep, "Package.swift"), SW_MANIFEST % dict(pkg="AsyncHTTPClient", mod="AsyncHTTPClient", deps="",
                                                              prods=""))
    _w(os.path.join(dep, "Sources", "AsyncHTTPClient", "lib.swift"),
       SW_DEP % dict(FS=fs_write("swift"), CLOCK=_sink("clock", "swift")))
    app = os.path.join(root, "app")
    _w(os.path.join(app, "Package.swift"), SW_MANIFEST % dict(
        pkg="app", mod="App", deps='.package(path: "../AsyncHTTPClient")',
        prods='.product(name: "AsyncHTTPClient", package: "AsyncHTTPClient")'))
    lines = ["import Foundation", "import AsyncHTTPClient", ""]
    for m in MEMBERS:
        for sp in SPELLINGS:
            if ("swift", sp) in NA:
                continue
            lines.append(SW_CELL[sp] % dict(m=m, V=SW_VERB[m], ENV=_sink("env", "swift")))
    _w(os.path.join(app, "Sources", "App", "lib.swift"), "\n".join(lines) + "\n")
    return dep, app


RENDER = {"rust": _render_rust, "java": _render_java, "ts": _render_ts, "swift": _render_swift}
VERB = {"rust": RS_VERB, "java": JV_VERB, "ts": TS_VERB, "swift": SW_VERB}
OWNER = {"rust": lambda m: "Raw" + m.upper(), "java": lambda m: "Log" + m.upper(),
         "ts": lambda m: "Log" + m.upper(), "swift": lambda m: "HTTPClient"}


# ======================================================================================== producer doctor
# The reason the doctor writes. Every engine carries it to a consumer that READ the row, so it is what tells the row's
# `Unknown` apart from an engine's own hedge on an untyped receiver (`dispatch:untyped cross-package receiver`), which
# reads the same `inferred` bytes whether or not the join happened (Fable R1815 review §2).
DOCTOR_WHY = "reflection:part110-doctored"
WHY, INV = "why:", "inv:"     # answer elements that are not effects: an `unknownWhy` token, an `invisible` package
def _is_member_row(lang, f, m):
    """The producer row for member `m` (its owner and verb), however the engine spells `fn`."""
    fn = (f.get("fn") or "").replace("::", ".")
    parts = fn.split(".")
    return len(parts) >= 2 and parts[-1] == VERB[lang][m] and parts[-2] == OWNER[lang](m)


def doctor(lang, src, dst):
    """Rewrite the `u` row to an Unknown-only row with a reason. Returns the doctored row, or None when the
    producer published no `u` row (a harness fault: there is nothing to make Unknown-only)."""
    rep = json.load(open(src))
    hit = None
    for f in rep.get("functions") or []:
        if _is_member_row(lang, f, "u"):
            f["inferred"] = ["Unknown"]
            f["direct"] = ["Unknown"]
            f["unresolved"] = True
            f["unknownWhy"] = [DOCTOR_WHY]
            for k in ("fs", "incomplete", "undeclared"):
                f.pop(k, None)
            hit = f
    with open(dst, "w") as fh:
        json.dump(rep, fh)
    return hit


def producer_rows(lang, path):
    rep = json.load(open(path))
    out = {}
    for m in MEMBERS:
        rows = [f for f in rep.get("functions") or [] if _is_member_row(lang, f, m)]
        out[m] = set().union(*[set(f.get("inferred") or []) for f in rows]) if rows else None
    return out


# ============================================================================================ the model
def cells(lang):
    for layout in LAYOUTS:
        for m in MEMBERS:
            for sp in SPELLINGS:
                if (lang, sp) in NA:
                    continue
                yield "%s_%s_%s" % (layout, m, sp), layout, m, sp


def sources(lang, layout, m, sp=None):
    """(curated term, row term) the clause unions for this cell, from the fixture's design."""
    cur = {CURATED[lang]} if curated_names(lang, m) and (lang, sp) not in CUR_NOT_TYPED else set()
    if layout == "nc":
        return cur, None                      # no loaded report covers the dependency: nothing to join
    if layout == "st":
        return cur, ({"Unknown"} if m in ("c", "u") else None)   # §2.1: a downgraded entry is Unknown
    return cur, {"c": {"Fs"}, "u": {"Unknown"}, "p": None, "q": None}[m]


def required(lang, layout, m, sp=None):
    cur, row = sources(lang, layout, m, sp)
    need = {"Env"} | cur | (row or set())
    if layout == "ch" and m == "u":
        need.add(WHY + DOCTOR_WHY)          # the row's Unknown, not one the engine made up for itself
    return need


def must_disclose(lang, layout, m, sp):
    """An UNCHAINED cell on a spelling the engine's classifier cannot name (CUR_NOT_TYPED: an untyped receiver into an
    uncovered imported package): nothing charges the call and nothing joins it, so the cell MUST disclose — `Unknown`
    or an `invisible` entry. A green cell over an undisclosed call is the shape this part must not print `ok` over
    (Fable R1815 review §6). A TYPED call to a non-verb member of a package the classifier covers (`q` on java's
    `org.slf4j`, swift's `HTTPClient`) is NOT asked here: there the classifier's coverage of the package is the
    answer, which is the curated-coverage calibration contract, not this clause."""
    return layout == "nc" and (lang, sp) in CUR_NOT_TYPED


def _disclosed(got):
    return "Unknown" in got or any(e.startswith(INV) for e in got)


def _model(lang, layout, m, sp):
    need = required(lang, layout, m, sp)
    return need | ({"Unknown"} if must_disclose(lang, layout, m, sp) else set())


def permitted_concrete(lang, layout, m, sp=None):
    """Concrete effects a cell may carry: the carrier, the curated term, the row's concrete effects. On `st` the
    downgraded `c` row's Fs is PRINTED, not judged (§2.1's question); on `nc` the dependency's own source may be
    read by an engine that types it (⟨0.42⟩ dependencySources), so `c`'s Fs is permitted there too."""
    cur, row = sources(lang, layout, m, sp)
    if (lang, sp) in CUR_NOT_TYPED and curated_names(lang, m):
        cur = {CURATED[lang]}          # not required there, but never a fabrication when an engine does charge it
    ok = {"Env"} | cur | ((row or set()) - {"Unknown"})
    if m == "c" and layout in ("st", "nc"):
        ok |= {"Fs"}
    return ok


def judge(lang, answers):
    """answers: cell -> set(inferred) or None (the function absent from `functions`). Returns
    ([(cell, why)] failures, [(cell, note)] info)."""
    fails, info = [], []
    for cell, layout, m, sp in cells(lang):
        got = answers.get(cell)
        got = set() if got is None else set(got)
        need = required(lang, layout, m, sp)
        miss = need - got
        extra = {e for e in got if e != "Unknown" and not e.startswith((WHY, INV))} - \
            permitted_concrete(lang, layout, m, sp)
        if layout == "nc" and (lang, sp) in CUR_NOT_TYPED and curated_names(lang, m) and CURATED[lang] in got:
            fails.append((cell, "STALE CUR_NOT_TYPED: the unchained answer carries %s, so the classifier DOES name "
                                "this spelling — retire the declaration" % CURATED[lang]))
        if miss:
            fails.append((cell, "MISSING %s (got %s, the union needs %s)" % (sorted(miss), sorted(got), sorted(need))))
        if must_disclose(lang, layout, m, sp) and not _disclosed(got):
            fails.append((cell, "SILENT: an unchained call no curated term answers carries neither `Unknown` nor "
                                "`invisible` (got %s)" % sorted(got)))
        if extra:
            fails.append((cell, "FABRICATED %s (got %s; no source of this cell supplies it)" % (sorted(extra), sorted(got))))
        if "Unknown" in got and "Unknown" not in need and not must_disclose(lang, layout, m, sp):
            info.append((cell, "over-disclosure: Unknown not required (got %s)" % sorted(got)))
        if layout == "st" and m == "c" and "Fs" in got:
            info.append((cell, "carried the DOWNGRADED row's Fs (a §2.1 question, not this clause's)"))
    return fails, info


# The wrong rules, computed from the same model. Each MUST fail the judge.
def _row_why(layout, m):
    return {WHY + DOCTOR_WHY} if (layout == "ch" and m == "u") else set()


def _mut_row_wins(lang, layout, m, sp):
    cur, row = sources(lang, layout, m, sp)
    if layout == "nc":
        return _model(lang, layout, m, sp)
    return {"Env"} | (row or set()) | _row_why(layout, m)   # chained: the row (or the report's silence) is the answer


def _mut_curated_wins(lang, layout, m, sp):
    cur, row = sources(lang, layout, m, sp)
    if layout == "nc":
        return _model(lang, layout, m, sp)
    # the join is read only when the classifier is silent
    return {"Env"} | (cur if cur else ((row or set()) | _row_why(layout, m)))


def _mut_hedge_dropped(lang, layout, m, sp):
    cur, row = sources(lang, layout, m, sp)
    if layout == "nc":
        return _model(lang, layout, m, sp)
    return {"Env"} | cur | ((row or set()) - {"Unknown"})


MUTANTS = (("row-wins", _mut_row_wins), ("curated-wins", _mut_curated_wins), ("hedge-dropped", _mut_hedge_dropped))


def calibrate(lang):
    """The judge on the CORRECT model must pass every cell, and on each wrong rule must fail ≥1. Returns lines and
    a broken flag."""
    lines, broken = [], False
    model = {c: _model(lang, la, m, sp) for c, la, m, sp in cells(lang)}
    f, _ = judge(lang, model)
    if f:
        broken = True
        lines.append("  BROKEN %s: the judge FAILS the clause's own model on %d cell(s): %s" % (lang, len(f), f[:3]))
    for name, fn in MUTANTS:
        ans = {c: fn(lang, la, m, sp) for c, la, m, sp in cells(lang)}
        f, _ = judge(lang, ans)
        n = len({c for c, _ in f})
        if n == 0:
            broken = True
            lines.append("  BROKEN %s: seeded wrong rule %s PASSES the judge — the part is vacuous" % (lang, name))
        else:
            lines.append("  SEED   %-5s %-13s fails %d cell(s) (e.g. %s)" % (lang, name, n, f[0][0]))
    # The disclosure rule, seeded at the model level so it is shown able to fail on every engine that HAS a
    # disclosure-required cell (live, those are swift's R1866 cells, which are red, so no live seed can act on them).
    nd = [c for c, la, m, sp in cells(lang) if must_disclose(lang, la, m, sp)]
    if nd:
        ans = {c: (_model(lang, la, m, sp) - ({"Unknown"} if c in nd else set())) for c, la, m, sp in cells(lang)}
        n = len({c for c, _ in judge(lang, ans)[0]})
        if n == 0:
            broken = True
            lines.append("  BROKEN %s: seeded silent-nc PASSES the judge — the disclosure rule is vacuous" % lang)
        else:
            lines.append("  SEED   %-5s %-13s fails %d cell(s) (e.g. %s)" % (lang, "silent-nc", n, nd[0]))
    return lines, broken


# CELL-LEVEL SEEDS, run over the engine's OWN answers after the scan. The model seeds above prove the judge rejects a
# wrong RULE; these prove it rejects a wrong CELL in the exact bytes this engine produced, which is where a `u` cell
# could be satisfied by the engine's own receiver hedge. Each must turn ≥1 live cell red that the real answer kept
# green; a seed with no live cell to act on is reported as such, never as a pass.
def _seed_own_hedge(lang, cell, la, m, sp, got):
    if la == "ch" and m == "u":
        return {e for e in got if not e.startswith(WHY)} | {"Unknown", WHY + "dispatch:untyped cross-package receiver"}
    return got


def _seed_hedge_dropped_cell(lang, cell, la, m, sp, got):
    if la in ("ch", "st") and m == "u":
        return {e for e in got if e != "Unknown" and not e.startswith(WHY)}
    return got


def _seed_silent(lang, cell, la, m, sp, got):
    if must_disclose(lang, la, m, sp):
        return {e for e in got if e != "Unknown" and not e.startswith(INV)}
    return got


CELL_SEEDS = (("own-hedge", _seed_own_hedge), ("hedge-dropped/cell", _seed_hedge_dropped_cell),
              ("silent-nc", _seed_silent))


def cell_seeds(lang, answers):
    lines, broken = [], False
    base = {c for c, _ in judge(lang, answers)[0]}
    for name, fn in CELL_SEEDS:
        mut = {}
        for c, la, m, sp in cells(lang):
            got = set(answers.get(c) or ())
            mut[c] = fn(lang, c, la, m, sp, got)
        acted = [c for c, la, m, sp in cells(lang) if mut[c] != set(answers.get(c) or ()) and c not in base]
        if not acted:
            lines.append("  SEEDc  %-5s %-18s no live green cell to act on (nothing to show)" % (lang, name))
            continue
        newly = sorted({c for c, _ in judge(lang, mut)[0]} - base)
        if not newly:
            broken = True
            lines.append("  BROKEN %s: cell seed %s altered %d green cell(s) and the judge PASSED them all" % (
                lang, name, len(acted)))
        else:
            lines.append("  SEEDc  %-5s %-18s turns %d of %d altered green cell(s) red (e.g. %s)" % (
                lang, name, len(newly), len(acted), newly[0]))
    return lines, broken


# ============================================================================================ the engines
def build_proof(lang, app):
    if lang == "java":
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


def _leaf(name):
    return (name or "").replace("::", ".").split(".")[-1]


def run_engine(lang, ws):
    scanner = sa.SCANNERS[lang]()
    if not scanner.available:
        return None, scanner.err, []
    root = os.path.join(ws, lang)
    os.makedirs(root, exist_ok=True)
    try:
        dep, app = RENDER[lang](root)
    except RuntimeError as e:
        return None, "render: %s" % e, []
    notes = []
    err = build_proof(lang, app)
    if err and err.startswith("SKIPPED"):
        notes.append("  NOTE  %s %s" % (lang, err))
    elif err:
        return None, err, notes
    r = scanner.scan(dep)
    if not r.produced:
        return None, "dependency scan produced no report (rc=%d) %s" % (r.rc, r.note), notes
    plain = os.path.join(root, "rep_dep.json")
    shutil.copy(r.report, plain)
    pre = producer_rows(lang, plain)
    if pre["c"] != {"Fs"} or pre["u"] != {"Clock"} or pre["p"] is not None or pre["q"] is not None:
        return None, ("the producer rows are not the fixture's (c [Fs], u [Clock], p and q absent): %s"
                      % {k: sorted(v) if v is not None else None for k, v in pre.items()}), notes
    chained = os.path.join(root, "rep_dep_doctored.json")
    if doctor(lang, plain, chained) is None:
        return None, "no `u` row to doctor", notes
    stale = sa.with_version(chained, root, "rep_dep_stale.json", "part110-not-this-engine")
    deps = {"ch": [chained], "st": [stale], "nc": []}
    answers = {}
    for layout in LAYOUTS:
        r = scanner.scan(app, deps=deps[layout])
        if not r.produced:
            return None, "%s: consumer scan produced no report (rc=%d) %s" % (layout, r.rc, r.note), notes
        rep = json.load(open(r.report))
        if not ((rep.get("analyzed") or {}).get("count") or 0):
            return None, "%s: analyzed.count is 0 — a hollow report judges nothing" % layout, notes
        rows = {}
        for f in rep.get("functions") or []:
            leaf = _leaf(f.get("fn"))
            if leaf.startswith("cc_"):
                got = rows.setdefault(leaf, set())
                got.update(f.get("inferred") or [])
                got.update(WHY + str(w) for w in f.get("unknownWhy") or [])
                got.update(INV + str(i) for i in f.get("invisible") or [])
        for cell, la, m, sp in cells(lang):
            if la == layout:
                answers[cell] = rows.get("cc_%s_%s" % (m, sp))
    # THE CHAIN IS SHOWN LIVE before any cell is read (the R1523 lesson: a dead join reads exactly like a
    # curated-wins engine). Some chained `c` spelling must carry the row's Fs, which nothing but the join supplies.
    if not any("Fs" in (answers.get("ch_c_%s" % sp) or ()) for sp in SPELLINGS if (lang, sp) not in NA):
        return None, ("DEAD JOIN: no chained `c` spelling carries the row's Fs, so the dependency report never "
                      "reached the consumer — nothing this part reads would measure the clause"), notes
    return answers, None, notes


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    if "--selftest" in argv:
        # The judge against the clause's model and the three wrong rules, per engine, with no engine run.
        bad = 0
        for lang in ENGINES:
            lines, broken = calibrate(lang)
            for ln in lines:
                print(ln)
            bad += broken
        print("CHAINED-CURATED selftest: %s" % ("OK" if not bad else "BROKEN"))
        return 1 if bad else 0
    print("CHAINED ROW x CURATED ENTRY (PART 110) — one call answered by both sources carries their UNION, on every "
          "spelling (SPEC §2 ⟨0.43⟩; SOUNDNESS R1815)")
    spec = " ".join(open(os.path.join(HERE, "..", "SPEC.md")).read().replace("**", "").split())
    for where, text in SPEC_CLAUSES:
        if " ".join(text.split()) not in spec:
            print("  BROKEN: SPEC.md no longer contains the %s text this part pins: %r" % (where, text))
            print("CHAINED-CURATED: BROKEN")
            return 1
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — every chained `c` answer has the joined row's Fs removed after the "
              "scan (the curated-wins rule), so those cells must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part110-")
    rc, total, failed, xfailed, passed_x, broken_n = 0, 0, 0, 0, 0, 0
    try:
        for lang in ENGINES:
            if only and lang != only:
                continue
            lines, broken = calibrate(lang)
            for ln in lines:
                print(ln)
            if broken:
                rc, broken_n = 1, broken_n + 1
                continue
            for (c, s_), why in sorted(NA.items()):
                if c == lang:
                    print("  N/A    %-5s %-8s %s" % (lang, s_, why))
            for (c, s_), why in sorted(CUR_NOT_TYPED.items()):
                if c == lang:
                    print("  NOTYPE %-5s %-8s the curated term is not required here: %s" % (lang, s_, why))
            answers, err, notes = run_engine(lang, ws)
            for n in notes:
                print(n)
            if err:
                if sa.engine_absent(err):
                    print("  SKIP   %s: %s" % (lang, err))
                    continue
                print("  BROKEN %s: %s" % (lang, err))
                rc, broken_n = 1, broken_n + 1
                continue
            lines, cbroken = cell_seeds(lang, answers)
            for ln in lines:
                print(ln)
            if cbroken:
                rc, broken_n = 1, broken_n + 1
            if FAULT:
                for cell, la, m, _sp in cells(lang):
                    if la == "ch" and m == "c" and answers.get(cell):
                        answers[cell] = set(answers[cell]) - {"Fs"}
            fails, info = judge(lang, answers)
            bad = {}
            for cell, why in fails:
                bad.setdefault(cell, []).append(why)
            for cell, la, m, sp in cells(lang):
                total += 1
                x = XFAIL.get((cell, lang))
                got = sorted(answers.get(cell) or [])
                if cell in bad and x:
                    xfailed += 1
                    print("  xfail  %-5s %-16s %s — %s" % (lang, cell, "; ".join(bad[cell]), x))
                elif cell in bad:
                    failed += 1
                    rc = 1
                    print("  FAIL   %-5s %-16s %s" % (lang, cell, "; ".join(bad[cell])))
                elif x:
                    passed_x += 1
                    rc = 1
                    print("  XFAIL CELL PASSED %-5s %-16s got %s — retire: %s" % (lang, cell, got, x))
                else:
                    print("  ok     %-5s %-16s %s" % (lang, cell, got))
            for cell, note in info:
                print("  INFO   %-5s %-16s %s" % (lang, cell, note))
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    print("  %d cell(s): %d FAIL, %d xfail, %d xfail passed, %d engine(s) BROKEN" % (
        total, failed, xfailed, passed_x, broken_n))
    if failed or passed_x:
        print("CHAINED-CURATED: %d cell(s) wrong" % (failed + passed_x))
    elif broken_n:
        print("CHAINED-CURATED: BROKEN")
    elif total == 0:
        print("CHAINED-CURATED: NOTHING RAN — no engine was available, which is not a pass")
        rc = 1
    else:
        print("CHAINED-CURATED: OK")
    return rc


if __name__ == "__main__":
    sys.exit(main())
