#!/usr/bin/env python3
"""
PART 105 — `accept` LINES FOR KNOWN POLICY VIOLATIONS (SPEC §6.2 ⟨0.41⟩, §3.1/§3.3 ⟨0.41⟩, AS-EFF-012).

WHAT IT PINS
------------
An `accept <fn> [<Effect>…] for <rule tokens…> because <reason…>` line takes ONE named verdict row out of
`violations` and lists it in `accepted`. The rung's cardinal direction is a NEW violation silently accepted,
so most rows here (marked ◆ in ROWS) are OVER-ACCEPT DETECTORS: their expected exit is 1, and an engine that
passes one at 0 is accepting something the clause does not let it accept.

TWO ARMS
  R  a HAND-WRITTEN report, the same bytes for every engine (fn spelled `dao.a`), gated with
     `gate --report`. The classifier is out of the loop, so twins, reason classes and hosts are exact.
  S  a SOURCE fixture per engine, scanned with `scan --policy`, then the report that scan wrote is gated
     with `gate --report` — the two routes, a `forbid` (answerable only on the scan route), an unparseable
     file, a lambda/closure (the nested-unit rule), a baseline, the human channel and the advisory verbs.

REFERENCE-LED, AND THE SKIP IS PROBED, NEVER DECLARED. ⟨0.41⟩ lands in candor-java first. An engine is
IMPLEMENTING iff row r02's verdict document carries the `accepted` key; otherwise it must have listed the
`accept` line in `ignored` (the pre-rung posture, §6.2: an unrecognised kind is ignored with a warning) and
it is NOT YET IMPLEMENTING — one counted SKIP line per engine per arm, and its rows are NOT scored against
the ⟨0.41⟩ expectations. What IS scored on every engine, today included, is the MIXED-FLEET property the
rung's additivity rests on: a non-implementing engine's verdict over a policy with `accept` lines is its
verdict over the same policy with those lines commented out — same exit, same violations — and every
`accept` line is in `ignored`. So a pre-rung engine errs RED, never green, on every row. An engine that
neither carries `accepted` nor lists the line in `ignored` is BROKEN and fails.

CALIBRATED EVERY RUN — EACH OVER-ACCEPT ROW IS SHOWN ABLE TO FAIL. No engine implements the rung yet, so
the expectations are first checked against a REFERENCE MODEL of the clause (`model()`), computed from a
real engine's ⟨0.40⟩ output on the same bytes (the commented-out base verdict, one run per rule line for
per-line attribution, the report's own units). The model must pass EVERY row — that proves the
expectations are what the clause says, over data an engine really produced. Then each of MUTANTS — one
deliberately wrong reading of the clause (prefix match on `fn`, no effect-subset test, no rule line in the
key, matching after de-duplication, twins accepted, `allow` accepted, a malformed line honoured, accepted
rows counted as established, reason class ignored, a stale entry merely disclosed, an exceeded entry also
reported stale, consumed-token matching, the nested-unit rule without its subset condition, …) — must
make at least one row FAIL, and every ◆ row must be failed by at least one mutant. A row no mutant can
fail is VACUOUS and fails the part. The calibration runs on candor-scan's report route (the R arm) and on
the first of candor-java / candor-ts present for the nested-unit rows (the only engines that emit a
positional unit).

USAGE
    python3 gen_accept.py [--keep] [--engine E]
    python3 gen_accept.py --selftest      # the judge and the model on synthetic documents; no engine
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_rung024 as G                      # noqa: E402  engine presence/paths — one copy

SPEC_CLAUSES = [
    ("§6.2 ⟨0.41⟩", "accept <fn> [<Effect>…] for <rule tokens…> because <reason tokens…>"),
    ("§6.2 ⟨0.41⟩", "**`<fn>` is ONE token, compared by exact string equality with a verdict row's `fn`** (§3.3)."),
    ("§6.2 ⟨0.41⟩", "The tokens between them MUST equal, token for token, the RAW"),
    ("§6.2 ⟨0.41⟩", "**`<fn>` MUST NOT be a POSITIONAL key**"),
    ("§6.2 ⟨0.41⟩", "is **ignored with a warning and listed in `ignored`** (§6.2 ⟨0.28⟩) — and the violation it meant to accept STAYS in"),
    ("§6.2 ⟨0.41⟩", "Matching is per producing LINE, before any de-duplication of identical"),
    ("§6.2 ⟨0.41⟩", "the entry accepts NEITHER of them."),
    ("§6.2 ⟨0.41⟩", "and V's row effects are a subset of U's row effects."),
    ("§6.2 ⟨0.41⟩", "**An accepted row is not an established violation** for §3.1's precedence rule"),
    ("§6.2 ⟨0.41⟩", "**A STALE entry FAILS.**"),
    ("§6.2 ⟨0.41⟩", "A rule that bound nothing (`zeroMatch`) WAS evaluated, so its entries are stale too."),
    ("§6.2 ⟨0.41⟩", "Never also an AS-EFF-012"),
    ("§6.2 ⟨0.41⟩", "and is OMITTED when no `accept` line became an entry, so a policy without the directive keeps a byte-identical verdict."),
    ("§6.2 ⟨0.41⟩", "**A human channel MUST print the accepted COUNT on every run that has at least one accepted row**"),
    ("§6.2 ⟨0.41⟩", "they MUST NOT accept anything the gate would not"),
    ("§3.1 ⟨0.41⟩", "**`accepted` (§6.2) joins the EVALUATED PROJECTION.**"),
]

EFFECTS = {"Net", "Llm", "Fs", "Db", "Exec", "Env", "Clock", "Ipc", "Log", "Rand", "Clipboard"}
CLASSES = {"reflect", "dispatch", "indirect", "native", "unresolved", "setup"}
RULE_KINDS = {"deny", "pure", "allow", "forbid", "only"}
POLICY_CODES = {"AS-EFF-006", "AS-EFF-008", "AS-EFF-009", "AS-EFF-011"}
ADVISORY = {"AS-EFF-007"}


# =====================================================================================================
# the R arm's report — one document, every engine
# =====================================================================================================
def F(fn, inferred, h, **kw):
    e = {"fn": fn, "hash": h, "inferred": list(inferred), "direct": [x for x in inferred]}
    e.update(kw)
    return e


BASE_UNITS = [
    F("dao.a", ["Fs"], "ha"),
    F("dao.k", ["Clock"], "hk"),            # in `dao`, never violates `deny Fs dao`: keeps the rule bound
]


def report(*extra, drop=()):
    fns = [u for u in BASE_UNITS if u["fn"] not in drop] + list(extra)
    return {"candor": {"version": "handwritten", "spec": "0.40"}, "package": "dao",
            "analyzed": {"count": len(fns) + 1, "digest": "0"}, "functions": copy.deepcopy(fns)}


# =====================================================================================================
# ROWS. `want` fields: exit; doc ("verdict" | "refusal" | "incomplete"); viol — the full violations
# multiset as (rule, fn, effects); acc — None (the key must be ABSENT) or a list of (fn, status) or
# (fn, status, enclosing); ign — the 1-based policy lines that must be (exactly the accept lines) in
# `ignored`; because/policyRule on the first accepted item where given.
# =====================================================================================================
A_DENY = "accept dao.a Fs for deny Fs dao because known since 2026"
ROWS = [
    dict(id="r01_control", arm="R", rep=report(), pol=["deny Fs dao"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=None, ign=[])),
    dict(id="r02_accept", arm="R", rep=report(), pol=["deny Fs dao", A_DENY],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted")], ign=[],
                   because="known since 2026", policyRule="deny Fs dao", line=2)),
    dict(id="r03_other_fn", arm="R", dia=1, rep=report(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao", A_DENY],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.b", ["Fs"])], acc=[("dao.a", "accepted")], ign=[])),
    dict(id="r04_exceeded", arm="R", dia=1, rep=report(F("dao.a", ["Fs", "Rand"], "ha"), drop=("dao.a",)),
         pol=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs", "Rand"])], acc=[("dao.a", "exceeded")], ign=[])),
    dict(id="r05_no_prefix", arm="R", dia=1, rep=report(F("dao.ab", ["Fs"], "hab"), drop=("dao.a",)),
         pol=["deny Fs dao", A_DENY],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.ab", ["Fs"]), ("AS-EFF-012", "dao.a", ["Fs"])],
                   acc=[], ign=[])),
    dict(id="r06_second_line", arm="R", dia=1, rep=report(), pol=["deny Fs dao", "deny Fs", A_DENY],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=[("dao.a", "accepted")], ign=[])),
    dict(id="r07_twins", arm="R", dia=1, rep=report(F("dao.t", ["Fs"], "ht1"), F("dao.t", ["Fs"], "ht2")),
         pol=["deny Fs dao", "accept dao.t Fs for deny Fs dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"]), ("AS-EFF-006", "dao.t", ["Fs"], "ht1"),
                                 ("AS-EFF-006", "dao.t", ["Fs"], "ht2")], acc=[("dao.t", "ambiguous")], ign=[])),
    dict(id="r10_malformed", arm="R", dia=1, rep=report(),
         pol=["deny Fs dao", "accept dao.a Fs for deny Fs dao",
              "accept dao.a Fs for deny Fs app because x", "accept dao.a Fs deny Fs dao because x",
              "accept dao.a for deny Fs dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=None, ign=[2, 3, 4, 5])),
    dict(id="r10b_typo_effect", arm="R", dia=1, rep=report(), pol=["deny Fs dao", "accept dao.a Fss for deny Fs dao because x"],
         want=dict(exit=2, doc="refusal", viol=None, acc=None, ign=[])),
    dict(id="r11_stale", arm="R", rep=report(drop=("dao.a",)), pol=["deny Fs dao", A_DENY],
         want=dict(exit=1, viol=[("AS-EFF-012", "dao.a", ["Fs"])], acc=[], ign=[])),
    dict(id="r12_zeromatch", arm="R", rep=report(), pol=["deny Fs daoz", "accept dao.a Fs for deny Fs daoz because x"],
         want=dict(exit=1, viol=[("AS-EFF-012", "dao.a", ["Fs"])], acc=[], ign=[], zeroMatch=["deny Fs daoz"])),
    dict(id="r14_refused", arm="R", dia=1, rep=report(), pol=["deny Fs dao", A_DENY, "forbid dao -> infra"],
         want=dict(exit=2, doc="refusal", viol=None, acc=None, ign=[])),
    dict(id="r15_respaced", arm="R", rep=report(),
         pol=["deny   Fs\tdao   # the rule", "accept  dao.a   Fs for deny Fs   dao because known   since 2026  # why"],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted")], ign=[],
                   because="known since 2026", policyRule="deny Fs dao")),
    dict(id="r16_no_accept", arm="R", rep=report(), pol=["deny Fs dao", "forbid dao"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=None, ign=[], ignored_present=True)),
    dict(id="r18_only_accepts", arm="R", rep=report(), pol=[A_DENY],
         want=dict(exit=2, doc="refusal", viol=None, acc=None, ign=[])),
    dict(id="r19_class_ok", arm="R",
         rep=report(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m"])),
         pol=["deny Unknown[dispatch,native] dao", "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because x"],
         want=dict(exit=0, viol=[], acc=[("dao.c", "accepted")], ign=[])),
    dict(id="r19b_class_moved", arm="R", dia=1,
         rep=report(F("dao.c", ["Unknown"], "hc", unknownWhy=["native:strlen"])),
         pol=["deny Unknown[dispatch,native] dao", "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.c", ["Unknown"])], acc=[("dao.c", "exceeded")], ign=[])),
    dict(id="r19c_bare_unknown", arm="R", dia=1,
         rep=report(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m"])),
         pol=["deny Unknown[dispatch,native] dao", "accept dao.c Unknown for deny Unknown[dispatch,native] dao because x",
              "accept dao.c Unknown[*] for deny Unknown[dispatch,native] dao because x",
              "accept dao.c Unknown[dynamic] for deny Unknown[dispatch,native] dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.c", ["Unknown"])], acc=None, ign=[2, 3, 4])),
    dict(id="r19d_bad_class", arm="R", dia=1,
         rep=report(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m"])),
         pol=["deny Unknown[dispatch,native] dao", "accept dao.c Unknown[dispatchh] for deny Unknown[dispatch,native] dao because x"],
         want=dict(exit=2, doc="refusal", viol=None, acc=None, ign=[])),
    dict(id="r22_raw_tokens", arm="R", dia=1, rep=report(), pol=["deny Fs dao extra", A_DENY],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=None, ign=[2])),
    dict(id="r22b_raw_tokens_named", arm="R", rep=report(),
         pol=["deny Fs dao extra", "accept dao.a Fs for deny Fs dao extra because x"],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted")], ign=[], policyRule="deny Fs dao extra")),
    dict(id="r23_before_rule", arm="R", rep=report(), pol=[A_DENY, "deny Fs dao"],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted")], ign=[], line=1)),
    dict(id="r24_two_entries", arm="R", rep=report(),
         pol=["deny Fs dao", A_DENY, "accept dao.a Clock for deny Fs dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-012", "dao.a", ["Clock"])], acc=[("dao.a", "accepted")], ign=[])),
    dict(id="r25_stale_plus_real", arm="R", rep=report(), pol=["deny Fs dao", "accept dao.z Fs for deny Fs dao because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"]), ("AS-EFF-012", "dao.z", ["Fs"])], acc=[], ign=[])),
    dict(id="r28_twin_alone", arm="R", rep=report(F("dao.t", ["Fs"], "ht1")),
         pol=["deny Fs dao", "accept dao.t Fs for deny Fs dao because x", A_DENY],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted"), ("dao.t", "accepted")], ign=[]),
         note="the S2 residual made visible: alone, twin A is accepted on an entry r07 calls ambiguous"),
    dict(id="r30_hash_reason", arm="R", rep=report(), pol=["deny Fs dao", "accept dao.a Fs for deny Fs dao because see #1"],
         want=dict(exit=0, viol=[], acc=[("dao.a", "accepted")], ign=[], because="see")),
    dict(id="r30b_hash_only", arm="R", dia=1, rep=report(), pol=["deny Fs dao", "accept dao.a Fs for deny Fs dao because #1"],
         want=dict(exit=1, viol=[("AS-EFF-006", "dao.a", ["Fs"])], acc=None, ign=[2])),
    # ---- S arm (per-engine spellings: {a} {b} {lam} …) ------------------------------------------------
    dict(id="s01_control", arm="S", fx="base", pol=["deny Fs dao"],
         want=dict(exit=1, viol=[("AS-EFF-006", "{a}", ["Fs"])], acc=None, ign=[])),
    dict(id="s02_accept", arm="S", fx="base", pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=0, viol=[], acc=[("{a}", "accepted")], ign=[]), human=1, advisory=1),
    dict(id="s03_other_fn", arm="S", dia=1, fx="b_reads", pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=1, viol=[("AS-EFF-006", "{b}", ["Fs"])], acc=[("{a}", "accepted")], ign=[]), advisory=1),
    dict(id="s08_forbid", arm="S", dia=1, fx="crosses",
         pol=["deny Fs dao", "forbid dao -> infra", "accept {a} for forbid dao -> infra because x"],
         want=dict(exit=1, viol=[("AS-EFF-006", "{a}", ["Fs"])], acc=[("{a}", "accepted")], ign=[]),
         want_report=dict(exit=1, viol=[("AS-EFF-006", "{a}", ["Fs"])], acc=[("{a}", "unjudged")], ign=[])),
    dict(id="s09_allow", arm="S", dia=1, fx="net", scan_only=1,
         pol=["allow Net in dao ok.example", "accept {n} Net for allow Net in dao ok.example because x"],
         want=dict(exit=1, viol=[("AS-EFF-008", "{n}", ["Net"])], acc=None, ign=[2])),
    dict(id="s13_unparseable", arm="S", dia=1, fx="unparseable", pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=2, doc="incomplete", viol=None, acc=None, ign=[]), scan_only=1),
    dict(id="s21_nested", arm="S", fx="lambda", pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=0, viol=[], acc="NESTED", ign=[])),
    dict(id="s21b_inserted", arm="S", fx="lambda_inserted", pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=0, viol=[], acc="NESTED", ign=[])),
    dict(id="s21e_nested_exceeded", arm="S", dia=1, fx="lambda_clock",
         pol=["deny Fs Clock dao", "accept {a} Fs for deny Fs Clock dao because known"],
         want=dict(exit=1, viol=[("AS-EFF-006", "{a}", ["Clock", "Fs"]), ("AS-EFF-006", "{NESTED}", ["Fs"])],
                   acc=[("{a}", "exceeded")], ign=[])),
    dict(id="s21c_positional_key", arm="S", dia=1, fx="lambda", positional=1,
         pol=["deny Fs dao", "accept {lam} Fs for deny Fs dao because known"],
         want=dict(exit=1, viol="UNACCEPTED", acc=None, ign=[2])),
    dict(id="s29_baseline", arm="S", dia=1, fx="base", baseline="pure_a", scan_only=1,
         pol=["deny Fs dao", "accept {a} Fs for deny Fs dao because known"],
         want=dict(exit=1, viol=[("AS-EFF-005", "{a}", ["Fs"])], acc=[("{a}", "accepted")], ign=[])),
]
DIAMONDS = [r["id"] for r in ROWS if r.get("dia")]


# =====================================================================================================
# the S arm's sources
# =====================================================================================================
def rust_src(fx):
    a = 'pub fn a() { let _ = std::fs::read("/x"); }'
    if fx in ("lambda", "lambda_inserted", "lambda_clock"):
        pre = {'lambda_inserted': 'let g = || { let _ = 1 + 1; }; g(); ',
               'lambda_clock': 'let _ = std::time::SystemTime::now(); '}.get(fx, "")
        a = 'pub fn a() { ' + pre + 'let f = || { let _ = std::fs::read("/y"); }; f(); }'
    if fx == "pure_a":
        a = 'pub fn a() -> i32 { 1 }'
    b = 'pub fn b() { let _ = std::fs::read("/z"); }' if fx == "b_reads" else 'pub fn b() -> i32 { 2 }'
    if fx == "net":
        b = 'pub fn n() { let _ = std::net::TcpStream::connect("bad.example:80"); }'
    cross = ' crate::infra::q();' if fx == "crosses" else ""
    if cross:
        a = 'pub fn a() { let _ = std::fs::read("/x");' + cross + ' }'
    return ("pub mod dao { " + a + " " + b + " pub fn ab() -> i32 { 3 } }\n"
            "pub mod infra { pub fn q() -> i32 { 4 } }\n")


def java_src(fx):
    rd = 'java.nio.file.Files.readString(java.nio.file.Path.of("%s"));'
    a = 'public static void a() throws Exception { ' + rd % "/x" + ' }'
    if fx in ("lambda", "lambda_inserted", "lambda_clock"):
        pre = {'lambda_inserted': 'Runnable g = () -> { int z = 1 + 1; }; g.run(); ',
               'lambda_clock': 'long t = System.currentTimeMillis(); '}.get(fx, "")
        a = ('public static void a() throws Exception { ' + pre + 'Runnable f = () -> { try { ' + rd % "/y" +
             ' } catch (Exception e) { } }; f.run(); }')
    if fx == "pure_a":
        a = 'public static int a() { return 1; }'
    if fx == "crosses":
        a = 'public static void a() throws Exception { ' + rd % "/x" + ' infra.I.q(); }'
    b = ('public static void b() throws Exception { ' + rd % "/z" + ' }') if fx == "b_reads" else \
        'public static int b() { return 2; }'
    if fx == "net":
        b = 'public static void n() throws Exception { new java.net.Socket("bad.example", 80); }'
    return {"dao/D.java": "package dao;\npublic class D {\n  " + a + "\n  " + b +
            "\n  public static int ab() { return 3; }\n}\n",
            "infra/I.java": "package infra;\npublic class I { public static int q() { return 4; } }\n"}


def ts_src(fx):
    a = 'export function a(): void { fsm.readFileSync("/x"); }'
    if fx in ("lambda", "lambda_inserted", "lambda_clock"):
        pre = {'lambda_inserted': 'const g = () => { const z = 1 + 1; return z; }; g(); ',
               'lambda_clock': 'Date.now(); '}.get(fx, "")
        a = 'export function a(): void { ' + pre + 'const f = () => { fsm.readFileSync("/y"); }; f(); }'
    if fx == "pure_a":
        a = 'export function a(): number { return 1; }'
    if fx == "crosses":
        a = 'export function a(): void { fsm.readFileSync("/x"); q(); }'
    b = 'export function b(): void { fsm.readFileSync("/z"); }' if fx == "b_reads" else \
        'export function b(): number { return 2; }'
    if fx == "net":
        b = 'export function n(): void { netm.connect(80, "bad.example"); }'
    return {"dao/index.ts": 'import * as fsm from "node:fs";\nimport * as netm from "node:net";\nimport { q } from "../infra/index.js";\n' +
            a + "\n" + b + "\nexport function ab(): number { return 3; }\n",
            "infra/index.ts": "export function q(): number { return 4; }\n"}


def swift_src(fx):
    rd = '_ = FileManager.default.contents(atPath: "%s")'
    a = 'static func a() { ' + rd % "/x" + ' }'
    if fx in ("lambda", "lambda_inserted", "lambda_clock"):
        pre = {'lambda_inserted': 'let g = { let _ = 1 + 1 }; g(); ',
               'lambda_clock': '_ = Date(); '}.get(fx, "")
        a = 'static func a() { ' + pre + 'let f = { ' + rd % "/y" + ' }; f() }'
    if fx == "pure_a":
        a = 'static func a() -> Int { 1 }'
    if fx == "crosses":
        a = 'static func a() { ' + rd % "/x" + '; _ = infra.q() }'
    b = ('static func b() { ' + rd % "/z" + ' }') if fx == "b_reads" else 'static func b() -> Int { 2 }'
    if fx == "net":
        b = 'static func n() { _ = NWConnection(host: "bad.example", port: 80, using: .tcp) }'
    return ("import Foundation\nimport Network\nenum dao {\n  " + a + "\n  " + b + "\n  static func ab() -> Int { 3 }\n}\n"
            "enum infra { static func q() -> Int { 4 } }\n")


SPELL = {
    "rust": {"a": "dao::a", "b": "dao::b", "n": "dao::n", "lam": None},
    "java": {"a": "dao.D.a", "b": "dao.D.b", "n": "dao.D.n", "lam": "dao.D.lambda$a$0"},
    "ts": {"a": "dao.index.a", "b": "dao.index.b", "n": "dao.index.n", "lam": None},   # its arrow key holds `#`
    "swift": {"a": "dao.a", "b": "dao.b", "n": "dao.n", "lam": None},
}
UNPARSEABLE = {"rust": ("src/broken.rs", "pub fn (( {\n"), "java": ("classes/dao/Broken.class", "not a class file"),
               "ts": ("dao/broken.ts", "export function (( {\n"), "swift": ("broken.swift", "func (( {\n")}


def positional(eng, fn):
    """The REFERENCE MODEL's knowledge of each engine's positional spellings (the clause leaves it to the
    engine; measured 2026-11-02): javac lambdas, candor-ts position-keyed arrows, rust closures."""
    return bool(re.search(r"\.lambda\$", fn) or re.search(r"#\d+:\d+$", fn) or "{closure#" in fn)


# =====================================================================================================
# running engines
# =====================================================================================================
def run(cmd, cwd=None, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY",
                                                             "CANDOR_BASELINE", "CANDOR_UNKNOWN_RATCHET")}
    env.update(env_extra or {})
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
    return r.returncode, (r.stdout + r.stderr).decode(errors="replace")


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(text)


def load(p):
    try:
        return json.load(open(p)) if os.path.exists(p) else None
    except Exception:
        return None


def gate_cmd(eng, loc, pol):
    if eng == "rust":
        return [G.rust_query(), "gate", "--report", loc, "--policy", pol]
    if eng == "java":
        return ["java", "-jar", G.java_jar(), "gate", "--report", loc, "--policy", pol]
    if eng == "ts":
        return ["node", os.path.join(G.ts_root(), "query.mjs"), "gate", "--report", loc, "--policy", pol]
    return [G.swift_bin(), "gate", "--report", loc, "--policy", pol]


def advisory_cmd(eng, verb, loc, pol):
    c = gate_cmd(eng, loc, pol)
    i = c.index("gate")
    return c[:i] + [verb] + c[i + 1:] + ["--strict"]


def gate(eng, loc, pol_path, gj):
    if os.path.exists(gj):
        os.remove(gj)
    rc, out = run(gate_cmd(eng, loc, pol_path) + ["--gate-json", gj])
    return rc, load(gj), out


def build_fixture(ws, eng, fx):
    d = os.path.join(ws, f"{eng}-{fx}")
    if os.path.isdir(d):
        return d, None
    if eng == "rust":
        write(os.path.join(d, "Cargo.toml"), '[package]\nname = "p105"\nversion = "0.0.0"\nedition = "2021"\n')
        write(os.path.join(d, "src", "lib.rs"), rust_src("base" if fx == "unparseable" else fx))
    elif eng == "java":
        srcs = java_src("base" if fx == "unparseable" else fx)
        for rel, text in srcs.items():
            write(os.path.join(d, "src", rel), text)
        rc, out = run(["javac", "-d", os.path.join(d, "classes")] +
                      [os.path.join(d, "src", rel) for rel in srcs])
        if rc:
            return None, "javac failed: " + out[:200]
    elif eng == "ts":
        for rel, text in ts_src("base" if fx == "unparseable" else fx).items():
            write(os.path.join(d, "src", rel), text)
    else:
        write(os.path.join(d, "src", "a.swift"), swift_src("base" if fx == "unparseable" else fx))
    if fx == "unparseable":
        rel, text = UNPARSEABLE[eng]
        base = {"rust": d, "java": d, "ts": os.path.join(d, "src"), "swift": os.path.join(d, "src")}[eng]
        write(os.path.join(base, rel), text)
    return d, None


def scan_target(eng, d):
    return {"rust": d, "java": os.path.join(d, "classes"), "ts": os.path.join(d, "src"),
            "swift": os.path.join(d, "src")}[eng]


def scan(eng, d, out, pol, gj, baseline=None):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for f in os.listdir(os.path.dirname(out)):
        p = os.path.join(os.path.dirname(out), f)
        if os.path.isfile(p):
            os.remove(p)
    t = scan_target(eng, d)
    if eng == "rust":
        cmd, loc = [G.rust_scan(), t, "--out", out], out
    elif eng == "java":
        loc = out + ".json"
        cmd = ["java", "-jar", G.java_jar(), t, "--json", loc]
    elif eng == "ts":
        cmd, loc = ["node", os.path.join(G.ts_root(), "scan.mjs"), t, "--out", out], out
    else:
        cmd, loc = [G.swift_bin(), t, "--out", out], out
    if pol:
        cmd += ["--policy", pol, "--gate-json", gj]
    rc, text = run(cmd, env_extra={"CANDOR_BASELINE": baseline} if baseline else None)
    stem = os.path.basename(out)
    wrote = any(f.startswith(stem + ".") and f.endswith(".json") for f in os.listdir(os.path.dirname(out)))
    return rc, (load(gj) if pol else None), text, (loc if wrote else None)


def report_files(loc):
    if loc.endswith(".json"):
        return [loc]
    d, stem = os.path.dirname(loc), os.path.basename(loc)
    side = (".callgraph.json", ".hierarchy.json", ".locs.json", ".gate.json")
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.startswith(stem + ".") and f.endswith(".json") and not f.endswith(side)]


def report_units(loc):
    out = []
    for p in report_files(loc):
        j = load(p) or {}
        out += j.get("functions", [])
    return out


# =====================================================================================================
# policy text helpers
# =====================================================================================================
def lex(line):
    return line.split("#", 1)[0].split()


def commented(pol, keep=None):
    """Every `accept` line (and, with keep, every rule line not in keep) replaced by a comment, so line
    numbers do not move."""
    out = []
    for i, ln in enumerate(pol, 1):
        t = lex(ln)
        if t and t[0] == "accept":
            out.append("# (accept line withheld)")
        elif keep is not None and t and t[0] in RULE_KINDS and i not in keep:
            out.append("# (rule line withheld)")
        else:
            out.append(ln)
    return out


def accept_lines(pol):
    return [i for i, ln in enumerate(pol, 1) if lex(ln)[:1] == ["accept"]]


def rule_lines(pol):
    return [i for i, ln in enumerate(pol, 1) if lex(ln)[:1] and lex(ln)[0] in RULE_KINDS]


def ignored_lines(doc):
    return sorted({int(x.get("line")) for x in (doc or {}).get("ignored", []) if isinstance(x, dict)
                   and str(x.get("line", "")).isdigit()})


def unevaluated_texts(doc):
    out = []
    for x in (doc or {}).get("unevaluated", []) or []:
        if isinstance(x, str):
            out.append(" ".join(lex(x)))
        elif isinstance(x, dict):
            for k in ("rule", "text", "line"):
                if isinstance(x.get(k), str):
                    out.append(" ".join(lex(x[k])))
                    break
    return out


def vkey(v):
    return (v.get("rule"), v.get("fn"), tuple(sorted(v.get("effects") or [])))


def vset(doc):
    """The violations as a SET of (rule, fn, effects, hash) — §3.3 pins the `{rule, fn, effects}` SET, so a
    row two lines produce may appear once or twice; `hash` keeps (hash, fn) twins apart."""
    if doc is None or "violations" not in doc:
        return None
    return sorted({vkey(v) + (v.get("hash"),) for v in doc["violations"]}, key=str)


def vmatch(doc, want):
    """want: (rule, fn, effects) or (rule, fn, effects, hash). 3-tuples compare ignoring hash."""
    got = vset(doc)
    if got is None:
        return False
    nested = [w for w in want if w[1] == "{NESTED}"]
    if nested:
        pos = [g for g in got if positional(ENG[0], g[1])]
        if ENG[0] in ("java", "ts"):
            if not pos or {(g[0], g[2]) for g in pos} != {(w[0], w[2]) for w in nested}:
                return False
        got = [g for g in got if g not in pos]
        want = [w for w in want if w not in nested]
    if {g[:3] for g in got} != {w[:3] for w in want}:
        return False
    return all(w in got for w in want if len(w) == 4)


# =====================================================================================================
# the REFERENCE MODEL of §6.2 ⟨0.41⟩ — and its MUTANTS
# =====================================================================================================
def parse_accept(tokens, rule_toks, mut):
    """-> ("entry", dict) | ("ignored", why) | ("error", why)."""
    if len(tokens) < 2:
        return "ignored", "no fn"
    fn, rest = tokens[1], tokens[2:]
    if "for" not in rest:
        return "ignored", "no `for`"
    i = rest.index("for")
    effs, after = rest[:i], rest[i + 1:]
    if "because" in after:
        j = after.index("because")
        rtoks, reason = after[:j], after[j + 1:]
    else:
        rtoks, reason = after, []
    if not reason and "lenient" not in mut:
        return "ignored", "no reason"
    A, filt = set(), None
    for e in effs:
        m = re.match(r"^Unknown(?:\[(.*)\])?$", e)
        if m:
            if m.group(1) is None or m.group(1) in ("*", "dynamic"):
                if "classblind" in mut or "lenient" in mut:
                    A.add("Unknown"); filt = None; continue
                return "ignored", "Unknown needs an explicit class filter"
            cls = m.group(1).split(",")
            if any(c not in CLASSES for c in cls):
                if "classdrop" not in mut:
                    return "error", "unrecognised class token"
                cls = [c for c in cls if c in CLASSES]
            A.add("Unknown"); filt = set(cls)
        elif e in EFFECTS:
            A.add(e)
        elif "lenient" in mut:
            continue
        else:
            return "error", f"not an effect: {e}"
    targets = [ln for ln, toks in rule_toks.items() if toks == rtoks or
               ("consumed" in mut and toks[:len(rtoks)] == rtoks and len(rtoks) >= 3)]
    if not targets:
        return "ignored", "names no parsed rule"
    kinds = {rule_toks[t][0] for t in targets}
    if kinds & {"allow", "only"} and "allowok" not in mut:
        return "ignored", "allow/only cannot be accepted"
    if kinds & {"deny", "pure"} and not A and "lenient" not in mut:
        return "ignored", "deny/pure needs effects"
    if "forbid" in kinds and A:
        return "ignored", "forbid takes no effects"
    return "entry", dict(fn=fn, A=A, filt=filt, lines=targets, because=" ".join(reason),
                         policyRule=" ".join(rtoks))


def covers(e, r, mut, rclass):
    fn_ok = (r["fn"] == e["fn"]) or ("prefix" in mut and r["fn"].startswith(e["fn"])) or "codeonly" in mut
    if not fn_ok:
        return False
    if "noeffects" in mut or "fnmute" in mut:
        return True
    effs = set(r.get("effects") or [])
    for x in effs:
        if x == "Unknown":
            if "Unknown" not in e["A"]:
                return False
            if "classblind" not in mut and e["filt"] is not None and not set(rclass(r)) <= e["filt"]:
                return False
            if "classblind" not in mut and e["filt"] is None:
                return False
        elif x not in e["A"]:
            return False
    return True


def model(pol, base, per_line, units, eng, mut=frozenset()):
    """§6.2 ⟨0.41⟩ over an engine's ⟨0.40⟩ output. base = (rc, doc) for the policy with accept lines
    withheld; per_line = {rule line: doc with only that rule}; units = the report's functions.
    Returns (rc, doc)."""
    rc0, doc0 = base
    ign0 = set(ignored_lines(doc0))
    rule_toks = {ln: lex(pol[ln - 1]) for ln in rule_lines(pol) if ln not in ign0}
    entries, ign_acc = [], []
    for ln in accept_lines(pol):
        kind, x = parse_accept(lex(pol[ln - 1]), rule_toks, mut)
        if kind == "error":
            return 2, {"spec": (doc0 or {}).get("spec"), "ok": False, "refused": True}
        if kind == "ignored":
            ign_acc.append(ln); continue
        x["line"] = ln
        if positional(eng, x["fn"]) and "nestedany" not in mut:
            ign_acc.append(ln); continue
        entries.append(x)
    doc = copy.deepcopy(doc0) if doc0 else {}
    if ign_acc and doc0 is not None and "violations" in doc0:
        doc["ignored"] = sorted((doc.get("ignored") or []) + [{"line": ln, "text": pol[ln - 1]} for ln in ign_acc],
                                key=lambda x: int(x.get("line", 0)))
    if doc0 is None or "violations" not in doc0:
        return rc0, doc                                     # refusal / incomplete: nothing to accept
    rows = doc0["violations"]
    hashes = {}
    for u in units:
        hashes.setdefault(u.get("fn"), set()).add(u.get("hash"))
    ue = {u.get("fn"): u for u in units}
    rclass = lambda r: r.get("reasonClass") or []          # noqa: E731

    def producing(r):
        return [ln for ln, d in per_line.items() if any(vkey(v) == vkey(r) and v.get("hash") == r.get("hash")
                                                         for v in (d or {}).get("violations", []))]
    uneval = set(unevaluated_texts(doc0))
    accepted_rows, items, covered_by = set(), [], {}
    lines_of = {}
    for idx, r in enumerate(rows):
        if r.get("rule") not in POLICY_CODES:
            if "anycode" in mut and any(covers(e, r, mut, rclass) for e in entries):
                accepted_rows.add(idx)
            continue
        P = producing(r)
        lines_of[idx] = P
        if not P:
            continue
        ok_lines = 0
        for L in P:
            hit = None
            for e in entries:
                if L not in e["lines"] and "norule" not in mut and "fnmute" not in mut:
                    continue
                if (len(hashes.get(e["fn"], ())) > 1 or (e["fn"] != r["fn"] and "prefix" in mut and
                                                          len(hashes.get(r["fn"], ())) > 1)) and "twins" not in mut:
                    continue
                if covers(e, r, mut, rclass):
                    hit = e; break
                # nested-unit rule
                if positional(eng, r["fn"]) and e["fn"] in ue and r["fn"] in (ue[e["fn"]].get("calls") or []):
                    if "nestedany" in mut:
                        hit = e; break
                    for r2 in rows:
                        if r2["fn"] == e["fn"] and L in producing(r2) and covers(e, r2, mut, rclass) and \
                                set(r.get("effects") or []) <= set(r2.get("effects") or []):
                            hit = e; break
                    if hit:
                        break
            if hit:
                ok_lines += 1
                covered_by.setdefault(idx, hit)
            if "dedup" in mut and hit:
                ok_lines = len(P)
                break
        if ok_lines == len(P):
            accepted_rows.add(idx)
    remaining = [r for i, r in enumerate(rows) if i not in accepted_rows]
    stale = []
    for e in entries:
        tl = [" ".join(rule_toks[L]) for L in e["lines"]]
        mine = [i for i, h in covered_by.items() if h is e]
        direct = [i for i in mine if rows[i]["fn"] == e["fn"]]
        nested = [i for i in mine if rows[i]["fn"] != e["fn"] and i in accepted_rows]
        if any(t in uneval for t in tl):
            items.append(dict(fn=e["fn"], status="unjudged", line=e["line"])); continue
        if len(hashes.get(e["fn"], ())) > 1 and "twins" not in mut:
            items.append(dict(fn=e["fn"], status="ambiguous", line=e["line"])); continue
        if direct:
            r = rows[direct[0]]
            items.append(dict(fn=r["fn"], status="accepted", line=e["line"], because=e["because"],
                              policyRule=e["policyRule"], rule=r["rule"], effects=r.get("effects")))
            for i in nested:
                items.append(dict(fn=rows[i]["fn"], status="accepted", line=e["line"], enclosing=e["fn"]))
            continue
        exceeded = [r for i, r in enumerate(rows) if i not in accepted_rows and r["fn"] == e["fn"] and
                    any(L in e["lines"] for L in lines_of.get(i, []))]
        if exceeded and "exceededstale" not in mut:
            items.append(dict(fn=e["fn"], status="exceeded", line=e["line"])); continue
        zm = any(" ".join(lex(z)) in tl for z in (doc0.get("zeroMatch") or []))
        if zm and "zmunjudged" in mut:
            items.append(dict(fn=e["fn"], status="unjudged", line=e["line"])); continue
        if "stalesilent" not in mut:
            stale.append({"rule": "AS-EFF-012", "fn": e["fn"], "effects": sorted(e["A"])})
        if exceeded:
            items.append(dict(fn=e["fn"], status="exceeded", line=e["line"]))
    remaining += stale
    failing = [r for r in remaining if r.get("rule") not in ADVISORY]
    if failing or "established" in mut and accepted_rows:
        rc = 1
    elif uneval or doc0.get("incomplete"):
        rc = 0 if "suppress2" in mut else 2
    else:
        rc = 0
    if rc == 2:
        out = {k: v for k, v in doc.items() if k not in ("violations", "accepted", "zeroMatch")}
        out.update(ok=False, refused=True) if uneval else out.update(ok=False, incomplete=True)
        return 2, out
    doc["violations"] = remaining
    doc["ok"] = rc == 0
    if entries:
        doc["accepted"] = sorted(items, key=lambda x: (x["line"], x["fn"]))
    return rc, doc


MUTANTS = {
    "prefix": "an entry's fn matched as a PREFIX of the row's fn",
    "codeonly": "the fn left out of the key — the entry mutes every row of its rule (a code-keyed suppression)",
    "fnmute": "an entry read as a mute on its fn — every rule, every effect (a `forbid` entry silencing a `deny`)",
    "anycode": "an entry accepting a row no policy line produced (an AS-EFF-005 baseline gain)",
    "classdrop": "an unrecognised class token dropped with a warning instead of refusing",
    "noeffects": "no effect-subset test — any effect set accepted",
    "norule": "the rule line left out of the key — the entry accepts the fn under every rule",
    "dedup": "matched after de-duplication — one line's entry accepts a row two lines produce",
    "twins": "(hash, fn) twins accepted on one entry",
    "allowok": "`allow`/`only` entries honoured",
    "lenient": "a malformed line honoured (no reason, unknown token skipped, bare Unknown)",
    "established": "accepted rows counted as established violations (exit 1, not 2)",
    "suppress2": "accepted rows suppress the exit-2 refusal (exit 0)",
    "classblind": "reason class ignored on an accepted Unknown",
    "stalesilent": "a stale entry disclosed only — no AS-EFF-012",
    "exceededstale": "an exceeded entry ALSO reported as stale",
    "zmunjudged": "a zero-match rule's entries `unjudged` (the proposal's carve-out)",
    "consumed": "rule tokens matched against the tokens the rule kind CONSUMED, not the raw line",
    "nestedany": "a positional key accepted, and a nested unit accepted with no subset condition",
}


# =====================================================================================================
# the judge
# =====================================================================================================
def spell(x, eng):
    return x.format(NESTED="{NESTED}", **{k: (v or "") for k, v in SPELL[eng].items()}) if isinstance(x, str) else x


ENG = [None]                                     # the engine vmatch is judging (positional spellings)


def want_for(row, eng, route):
    w = copy.deepcopy(row["want"] if route != "report" or "want_report" not in row else row["want_report"])
    if isinstance(w.get("viol"), list):
        w["viol"] = sorted(((t[0], spell(t[1], eng), tuple(sorted(t[2]))) + tuple(t[3:]) for t in w["viol"]
                            if t[1] != "{NESTED}" or eng in ("java", "ts")), key=str)
    if w.get("acc") == "NESTED":
        a = [(spell("{a}", eng), "accepted")]
        if eng in ("java", "ts"):
            a.append(("{NESTED}", "accepted", spell("{a}", eng)))
        w["acc"] = a
    elif isinstance(w.get("acc"), list):
        w["acc"] = [tuple(spell(x, eng) for x in t) for t in w["acc"]]
    return w


def judge(row, eng, route, rc, doc, pol, units=None):
    """-> list of problems (empty = PASS)."""
    w = want_for(row, eng, route)
    ENG[0] = eng
    bad = []
    if rc != w["exit"]:
        bad.append(f"exit {rc}, want {w['exit']}")
    kind = w.get("doc", "verdict")
    if doc is None:
        bad.append("no --gate-json document"); return bad
    if kind == "verdict" and "violations" not in doc:
        bad.append("a verdict document must carry `violations`")
    if kind in ("refusal", "incomplete"):
        if "violations" in doc:
            bad.append(f"an exit-2 {kind} document carries `violations`")
        if kind == "refusal" and doc.get("refused") is not True:
            bad.append("`refused` is not true on the refusal document")
        if kind == "incomplete" and doc.get("incomplete") is not True:
            bad.append("`incomplete` is not true")
    if w.get("viol") == "UNACCEPTED":
        if not doc.get("violations"):
            bad.append("no violation stayed red")
    elif w.get("viol") is not None and not vmatch(doc, w["viol"]):
        bad.append(f"violations {vset(doc)}, want {w['viol']}")
    acc = doc.get("accepted")
    if w.get("acc") is None:
        if "accepted" in doc:
            bad.append(f"`accepted` present ({len(acc or [])} item(s)) where it must be OMITTED")
    else:
        if not isinstance(acc, list):
            bad.append("`accepted` missing")
        else:
            got = sorted(tuple(x for x in (i.get("fn"), i.get("status"), i.get("enclosing")) if x is not None)
                         for i in acc)
            want = []
            for t in w["acc"]:
                if t[0] == "{NESTED}":
                    nested = [i for i in acc if i.get("enclosing") == t[2]]
                    want.append((nested[0]["fn"] if nested else "<a nested unit>",) + t[1:])
                else:
                    want.append(t)
            if got != sorted(want):
                bad.append(f"accepted {got}, want {sorted(want)}")
            for i in acc:
                if i.get("status") == "accepted" and "enclosing" not in i:
                    if "because" in w and i.get("because") != w["because"]:
                        bad.append(f"because {i.get('because')!r}, want {w['because']!r}")
                    if "policyRule" in w and i.get("policyRule") != w["policyRule"]:
                        bad.append(f"policyRule {i.get('policyRule')!r}, want {w['policyRule']!r}")
                    if "line" in w and i.get("line") != w["line"]:
                        bad.append(f"line {i.get('line')!r}, want {w['line']}")
                    break
    exp_ign = set(w.get("ign") or [])
    got_ign = set(ignored_lines(doc)) & set(accept_lines(pol))
    if kind == "verdict" and got_ign != exp_ign:
        bad.append(f"accept lines in `ignored` {sorted(got_ign)}, want {sorted(exp_ign)}")
    if w.get("ignored_present") and "ignored" not in doc:
        bad.append("`ignored` absent although a malformed line was dropped")
    if w.get("zeroMatch") and [" ".join(lex(z)) for z in doc.get("zeroMatch") or []] != w["zeroMatch"]:
        bad.append(f"zeroMatch {doc.get('zeroMatch')}, want {w['zeroMatch']}")
    return bad


def mixed_fleet(rc, doc, rc0, doc0, pol):
    """A pre-rung engine: the policy with accept lines == the policy without them, and every accept line
    in `ignored`."""
    bad = []
    if rc != rc0:
        bad.append(f"exit {rc} with the accept lines, {rc0} without — a pre-rung engine must not move")
    if vset(doc) != vset(doc0):
        bad.append("violations differ from the accept-free policy's")
    if doc is not None and "violations" in doc:
        miss = set(accept_lines(pol)) - set(ignored_lines(doc))
        if miss:
            bad.append(f"accept line(s) {sorted(miss)} neither honoured nor listed in `ignored`")
    return bad


# =====================================================================================================
# driver
# =====================================================================================================
def pol_text(pol, eng):
    return "\n".join(spell(ln, eng) for ln in pol) + "\n"


class Run:
    def __init__(self, ws):
        self.ws = ws
        self.n = 0

    def path(self, tag):
        self.n += 1
        return os.path.join(self.ws, f"{self.n:04d}-{tag}")


def r_arm(R, eng, row, pol, calib=False):
    """-> dict(obs=(rc, doc, out), base=(rc, doc), per_line={...}|None, units=[...])"""
    d = os.path.join(R.ws, "rep", eng, row["id"])
    loc = G.write_report(d, eng, row["rep"])
    p = R.path("pol"); write(p, pol_text(pol, eng))
    p0 = R.path("pol0"); write(p0, pol_text(commented(pol), eng))
    rc, doc, out = gate(eng, loc, p, R.path("g.json"))
    rc0, doc0, _ = gate(eng, loc, p0, R.path("g0.json"))
    per = None
    if calib:
        per = {}
        for L in rule_lines(pol):
            pl = R.path("pl"); write(pl, pol_text(commented(pol, keep={L}), eng))
            per[L] = gate(eng, loc, pl, R.path("gl.json"))[1]
    return dict(obs=(rc, doc, out), base=(rc0, doc0), per_line=per, units=row["rep"]["functions"], loc=loc)


def s_arm(R, eng, row, pol, calib=False):
    d, why = build_fixture(R.ws, eng, row["fx"])
    if d is None:
        return dict(error=why)
    base_rep = None
    if row.get("baseline"):
        bd, why = build_fixture(R.ws, eng, row["baseline"])
        if bd is None:
            return dict(error=why)
        _, _, _, bloc = scan(eng, bd, os.path.join(R.ws, "bl", eng, row["id"], "r"), None, None)
        files = report_files(bloc) if bloc else []
        if not files:
            return dict(error="baseline scan wrote no report")
        base_rep = files[0]
    p = R.path("pol"); write(p, pol_text(pol, eng))
    p0 = R.path("pol0"); write(p0, pol_text(commented(pol), eng))
    gj = R.path("s.json")
    rc, doc, out, loc = scan(eng, d, os.path.join(R.ws, "so", eng, row["id"], "r"), p, gj, base_rep)
    rc0, doc0, _, loc0 = scan(eng, d, os.path.join(R.ws, "so0", eng, row["id"], "r"), p0, R.path("s0.json"), base_rep)
    res = dict(obs=(rc, doc, out), base=(rc0, doc0), loc=loc, units=report_units(loc) if loc else [])
    if not row.get("scan_only") and loc:
        res["robs"] = gate(eng, loc, p, R.path("r.json"))
        res["rbase"] = gate(eng, loc, p0, R.path("r0.json"))[:2]
    if calib:
        per = {}
        for L in rule_lines(pol):
            pl = R.path("pl"); write(pl, pol_text(commented(pol, keep={L}), eng))
            per[L] = scan(eng, d, os.path.join(R.ws, "spl", eng, row["id"], str(L), "r"), pl, R.path("sl.json"),
                          base_rep)[1]
        res["per_line"] = per
    if row.get("advisory") and loc:
        res["adv"] = {v: run(advisory_cmd(eng, v, loc, p)) for v in ("fix-gate", "unverified")}
    return res


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    fault = os.environ.get("CANDOR_PROBE_FAULT") == "1"
    ws = tempfile.mkdtemp(prefix="candor-p105-")
    R = Run(ws)
    wrong = 0
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in G.ENGINES if G.installed(e) and not G.alive(e)]
        print(f"  engines present: {', '.join(engines) or '(none)'}; {len(ROWS)} rows "
              f"({sum(1 for r in ROWS if r['arm'] == 'R')} report-arm, {sum(1 for r in ROWS if r['arm'] == 'S')} "
              f"scan-arm), {len(DIAMONDS)} over-accept detectors")
        if broken:
            print(f"  FAIL: installed but not responding: {', '.join(broken)} — HARNESS/INSTALL, not candor")
            wrong += 1
        if not engines:
            print("  FAIL: no engine present"); return 1
        calib_r = "rust" if "rust" in engines else engines[0]
        calib_s = next((e for e in ("java", "ts") if e in engines), None)
        data = {}
        for eng in engines:
            for row in ROWS:
                if row.get("positional") and not SPELL[eng]["lam"]:
                    continue
                pol = [spell(ln, eng) for ln in row["pol"]]
                if fault and row["id"] == "r01_control":
                    pol = ["deny Net dao"]             # probe fault: the control no longer fires
                    print(f"  PROBE: CANDOR_PROBE_FAULT — {eng}'s r01 control rewritten to a rule that cannot fire")
                if row["arm"] == "R":
                    data[(eng, row["id"])] = r_arm(R, eng, row, pol, calib=(eng == calib_r))
                else:
                    data[(eng, row["id"])] = s_arm(R, eng, row, pol,
                                                   calib=(eng == calib_r or
                                                          (eng == calib_s and row["id"].startswith("s21"))))
                data[(eng, row["id"])]["pol"] = pol
        # ---- 1. probe, then score -------------------------------------------------------------------
        for eng in engines:
            for arm, probe in (("R", "r02_accept"), ("S", "s02_accept")):
                rc, doc, _ = data[(eng, probe)]["obs"]
                implementing = isinstance(doc, dict) and "accepted" in doc
                listed = isinstance(doc, dict) and 2 in ignored_lines(doc)
                cells = [r for r in ROWS if r["arm"] == arm and (eng, r["id"]) in data]
                bad = []
                for row in cells:
                    x = data[(eng, row["id"])]
                    if "error" in x:
                        bad.append(f"{row['id']}: HARNESS — {x['error']}"); continue
                    rc, doc, out = x["obs"]
                    rc0, doc0 = x["base"]
                    if row["id"] in ("r01_control", "s01_control") and rc0 != 1:
                        bad.append(f"{row['id']}: VACUOUS — the control did not fire (exit {rc0}), so no row "
                                   f"here could see an acceptance")
                    if implementing:
                        for p in judge(row, eng, "scan" if arm == "S" else "report", rc, doc, x["pol"], x["units"]):
                            bad.append(f"{row['id']}{' ◆' if row.get('dia') else ''}: {p}")
                        if "robs" in x:
                            for p in judge(row, eng, "report", x["robs"][0], x["robs"][1], x["pol"], x["units"]):
                                bad.append(f"{row['id']} [gate --report]: {p}")
                        if row.get("human") and not re.search(r"\b1\b[^\n]*accepted|accepted[^\n]*\b1\b", out, re.I):
                            bad.append(f"{row['id']}: the human channel does not print the accepted count")
                        if "adv" in x and rc == 0 and re.search(r"provably clean", x["adv"]["unverified"][1], re.I):
                            bad.append(f"{row['id']}: `unverified --strict` calls the layer PROVABLY clean over an "
                                       f"ACCEPTED violation")
                    if "adv" in x and rc != 0 and x["adv"]["fix-gate"][0] == 0:
                        bad.append(f"{row['id']}: `fix-gate --strict` exits 0 where the gate exits {rc} (⟨0.24⟩)")
                    if not implementing:
                        for p in mixed_fleet(rc, doc, rc0, doc0, x["pol"]):
                            bad.append(f"{row['id']} (pre-rung): {p}")
                        if "robs" in x:
                            for p in mixed_fleet(x["robs"][0], x["robs"][1], x["rbase"][0], x["rbase"][1], x["pol"]):
                                bad.append(f"{row['id']} [gate --report] (pre-rung): {p}")
                if implementing:
                    status = "IMPLEMENTS ⟨0.41⟩"
                elif listed:
                    status = None
                else:
                    status = "BROKEN"
                    bad.append(f"{probe}: neither `accepted` nor the accept line in `ignored` — the line vanished")
                if status is None:
                    # `SKIP —` is the token skip_ratchet.py counts: a rung that ships and later un-ships flips
                    # this engine back to SKIP, which only a COUNTED skip can catch (skip-baseline.json).
                    print(f"  {eng:6s} [{arm}] SKIP — does not yet implement ⟨0.41⟩ accept (reference-led, probed); "
                          f"mixed-fleet posture scored on {len(cells)} row(s): "
                          + ("OK, every accept line ignored, verdict unmoved" if not bad else "DIVERGE"))
                else:
                    print(f"  {eng:6s} [{arm}] {status}: " + (f"OK — {len(cells)} row(s)" if not bad else "DIVERGE"))
                for b in bad:
                    print(f"    {eng:6s} {b}")
                wrong += len(bad)
        # ---- 2. calibration: the model passes, every mutant is caught, every ◆ row can fail -----------
        caught = {r["id"]: [] for r in ROWS}
        model_bad, mutant_hits = [], {m: 0 for m in MUTANTS}

        def calib_rows(eng, arm, pred):
            return [r for r in ROWS if r["arm"] == arm and pred(r) and (eng, r["id"]) in data
                    and "error" not in data[(eng, r["id"])]]

        sets = [(calib_r, calib_rows(calib_r, "R", lambda r: True), "report"),
                (calib_r, calib_rows(calib_r, "S", lambda r: True), "scan")]
        if calib_s and calib_s != calib_r:
            sets.append((calib_s, calib_rows(calib_s, "S", lambda r: r["id"].startswith("s21")), "scan"))
        for eng, rows, route in sets:
            for row in rows:
                x = data[(eng, row["id"])]
                per = x.get("per_line")
                if per is None:
                    continue
                units = x["units"]
                rc, doc = model(x["pol"], x["base"], per, units, eng)
                for p in judge(row, eng, route, rc, doc, x["pol"], units):
                    model_bad.append(f"{eng} {row['id']}: {p}")
                for m in MUTANTS:
                    mrc, mdoc = model(x["pol"], x["base"], per, units, eng, frozenset([m]))
                    if judge(row, eng, route, mrc, mdoc, x["pol"], units):
                        caught[row["id"]].append(m)
                        mutant_hits[m] += 1
        calibrated = {r["id"] for eng, rows, _ in sets for r in rows if data[(eng, r["id"])].get("per_line") is not None}
        if model_bad:
            print("  CALIBRATION FAIL — the reference model of the clause does not meet these expectations "
                  "(an expectation or the model is wrong; neither is a finding about an engine):")
            for b in model_bad:
                print(f"    {b}")
            wrong += len(model_bad)
        dead = [m for m, n in mutant_hits.items() if n == 0]
        if "nestedany" in dead and not any(e in ("java", "ts") for e, _, _ in sets):
            dead.remove("nestedany")
            print("  calibration NOTE — mutant `nestedany` not calibrated: no engine that emits a positional unit "
                  "(candor-java, candor-ts) is in this run")
        uncaught = [d for d in DIAMONDS if d in calibrated and not caught[d]]
        uncal = [d for d in DIAMONDS if d not in calibrated]
        for m in dead:
            print(f"  CALIBRATION FAIL — mutant `{m}` ({MUTANTS[m]}) fails NO row: the part cannot see it")
        for d in uncaught:
            print(f"  CALIBRATION FAIL — over-accept row {d} is failed by NO mutant: VACUOUS")
        wrong += len(dead) + len(uncaught)
        if not model_bad and not dead and not uncaught:
            print(f"  calibration ({calib_r} both arms"
                  + (f", {calib_s} nested-unit rows" if calib_s and calib_s != calib_r else "") +
                  f"): the reference model passes all {len(calibrated)} calibrated row(s); each of "
                  f"{len(MUTANTS)} mutants fails ≥1 row; each of {len([d for d in DIAMONDS if d in calibrated])} "
                  f"calibrated ◆ rows is failed by ≥1 mutant")
            for d in DIAMONDS:
                if d in calibrated:
                    print(f"    ◆ {d:22s} caught by: {', '.join(caught[d])}")
        for d in uncal:
            print(f"    ◆ {d:22s} NOT model-calibrated (scan-route only) — scored when an engine implements; "
                  f"its mixed-fleet posture is scored above")
        print("ACCEPT: OK — every pre-rung engine stays red over every accept line; the model passes; every "
              "over-accept row can fail" if not wrong else f"ACCEPT: {wrong} cell(s) wrong")
        return 1 if wrong else 0
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)


def selftest():
    """The judge and the model on SYNTHETIC ⟨0.40⟩ documents: no engine. Proves the judge FAILS a document
    that ignores accept lines on an implementing claim, and passes the model on row r02."""
    row = next(r for r in ROWS if r["id"] == "r02_accept")
    v = {"rule": "AS-EFF-006", "fn": "dao.a", "hash": "ha", "effects": ["Fs"]}
    base = (1, {"spec": "0.40", "ok": False, "violations": [v]})        # the accept-free policy's verdict
    rc, doc = model(row["pol"], base, {1: {"violations": [v]}}, row["rep"]["functions"], "rust")
    p1 = judge(row, "rust", "report", rc, doc, row["pol"])
    pre = dict(base[1], ignored=[{"line": 2, "text": A_DENY}], accepted=[])  # a pre-rung engine's, mislabelled
    p2 = judge(row, "rust", "report", base[0], pre, row["pol"])
    ok = not p1 and bool(p2)
    print(f"gen_accept selftest: model on r02 {'PASS' if not p1 else p1}; a pre-rung document judged as "
          f"implementing {'FAILS' if p2 else 'PASSES — the judge is blind'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
