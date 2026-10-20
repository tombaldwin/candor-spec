#!/usr/bin/env python3
"""
PART 99 — THE POLICY-SEMANTICS DIFFERENTIAL: ONE REPORT, ONE POLICY, FOUR GATES, ONE EXPECTED ANSWER.

WHAT IT CHECKS
--------------
Every cell is a (report, policy) pair whose BYTES are held constant across the four engines: the same JSON
written under each engine's report naming (`gen_rung024.write_report`), the same policy file, handed to each
engine's `gate --report`. The only variable is the gate. Each cell carries an EXPECTED answer written from
SPEC.md BEFORE the first run (2026-10-20, from the clauses cited on each cell), and every engine is judged
against EXPECTED — not against the other engines. Four engines agreeing on an answer nobody pinned is
AGREE-UNPINNED, and it FAILS this part: agreement is the weakest signal this family has (memory
`candor-honesty-confidence`), and an unpinned cell that agrees today is a cell that will drift unseen.

It replaces `conformance/differential/policy_grammar_run.py` (SOUNDNESS R1240), which carried the `bom`,
`crlf`, `cr-only` and `nbsp` rows that would have caught R1224, was called by nothing, defaulted to the
0.27.0 jar, scored only "do the engines agree on the exit code" and had no expected values. Its battery is
re-pinned here row by row; the rows SPEC does not decide are listed in `NOT_PINNED` with the reason, printed
every run, and not run — a row that cannot be judged is not evidence either way.

What is compared, per (cell, engine): the exit code; the SET of violating `(hash, fn)`; whether the
document is a refusal (`refused: true`, and no `violations` key); the SET of `unevaluated[].rule` lines
where the cell pins it (or only that it is non-empty); the SET of `zeroMatch` rules; the SET of `ignored`
line numbers. Never prose, never order, never `detail`/`reason` text.

FAMILIES
  G  the §6.2 LEXICAL / GRAMMAR battery (ex `policy_grammar_gen.py`), over one neutral report. Includes the
     ⟨0.40⟩ BOM ruling (R1224): a U+FEFF at byte 0 is stripped (`bom`, `bom-multi` expect the first rule
     EVALUATED), one anywhere else stays a token character (`bom-mid`, `bom-twice`).
  Z  ZERO RULES and POLICY ERRORS: the refusal document and its `unevaluated` (§6.2 ⟨0.28⟩; §3.1 ⟨0.40⟩
     "a refusal caused by the policy discloses the policy", R1233).
  U  UNITS (§2 ⟨0.40⟩, R1219): two entries sharing a `hash` with different `fn` are two units; two entries
     equal in both are one unit, unioned.
  I  `interfaceUnion` ENTRIES (§3.1 ⟨0.40⟩, R1223/R1234): never a unit — no violation, no zeroMatch match,
     no answerability refusal — and a union beside a real entry is not merged into it.
  C  REASON-PREFIX CASE (§6.2 ⟨0.40⟩): off-case raw reasons project as their table spelling.
  X  CROSS-FED engine-written reports: each engine scans a small three-function tree, and that report is
     gated by all four. SCOPELESS rules only — scope matching splits on the LANGUAGE's separator (§6.2), so a
     scoped rule over another language's report has no SPEC answer (Fable's design objection, 2026-10-20).
     EXPECTED is derived from the written report's bytes: the non-union entries whose `inferred` carries E.

REACH: every (engine, report) pair carries a control cell that MUST exit 1 naming a known unit, so a gate
that never read the report cannot pass the pair's other cells; and per engine the run must see exit 0, 1
and 2 and at least one `zeroMatch`, or the engine is VACUOUS. There is no freshness switch to set: no gate
freshness-checks a `--report` locator handed to it explicitly (measured: every control cell fires on reports
written seconds earlier by this harness, never by a scan).

SEEDS, run every time (permanent, engine-side — they fire on whatever binary is under test):
  doc        one violation deleted from an engine's real `--gate-json` of a firing cell: MUST be caught.
  zeromatch  `zeroMatch` dropped from an engine's real document of a zeroMatch cell: MUST be caught.
  refused    `refused: true` added to an engine's real exit-1 document: MUST be caught.
  expected   one cell's EXPECTED exit flipped: EXACTLY that cell must diverge for that engine.
  unpinned   a cell with no EXPECTED on which the engines agree: MUST be classified AGREE-UNPINNED (failing).

XFAIL is keyed (cell, engine) and names an OPEN register row. A PASSING XFAIL IS A FAILURE: the engine that
fixes the row reddens this part until the entry is retired in the same commit as the fix.

USAGE
    python3 gen_policy_semantics.py [--keep] [--engine rust|java|ts|swift] [--cell ID]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_rung024 as G           # noqa: E402  engine presence + per-engine report spelling

SPEC_CLAUSES = [
    ("§6.2 Lexical", "A line is split into tokens on runs of **ASCII whitespace**"),
    ("§6.2 Lexical ⟨0.40⟩", "**A U+FEFF AT BYTE OFFSET 0 OF THE POLICY FILE IS AN ENCODING MARK, NOT A CHARACTER OF ITS FIRST"),
    ("§6.2 Lexical ⟨0.40⟩", "it stays an ordinary character of its token under the rule above, so that line is ignored-with-a-warning."),
    ("§6.2 ⟨0.28⟩", "when a policy is CONFIGURED and parsing yields NO RULES AT ALL, the run MUST refuse"),
    ("§3.1 ⟨0.40⟩", "**A REFUSAL CAUSED BY THE POLICY DISCLOSES THE POLICY**"),
    ("§3.1 ⟨0.24⟩", "on a whole-policy refusal that list carries EVERY rule of\nthe refused policy"),
    ("§2 ⟨0.40⟩", "**WITHIN ONE REPORT, `hash` IS THE JOIN KEY AND THE PAIR `(hash, fn)` IS THE UNIT**"),
    ("§2 ⟨0.40⟩", "**Two unit entries equal in BOTH fields are ONE unit and MUST be unioned**"),
    ("§3.1 ⟨0.40⟩", "**AN `interfaceUnion: true` ENTRY IS NEVER A UNIT OF A VERDICT, IT IS ALWAYS A CONTRIBUTOR TO THE"),
    ("§3.1 ⟨0.40⟩", "A consumer MUST NOT merge a separately published union entry into a real entry that shares its key"),
    ("§6.2 ⟨0.40⟩", "**The prefixes are matched without regard to ASCII case**"),
    ("§3.1 ⟨0.24⟩", "a typo'd effect token like `deny Nett app` is a policy ERROR at exit 2"),
]

ENGINES = list(G.ENGINES)
BOM = "﻿"

# ======================================================================================================
# REPORTS — the bytes held constant. `fn` names use `.` and every scoped rule below is written in `.`, the
# separator all four gates segment a dotted name on (measured: `deny Fs app.io` fires four-way).
# ======================================================================================================


def env(fns, package="app"):
    return {"candor": {"version": "handwritten", "spec": "0.40"}, "package": package,
            "analyzed": {"count": len(fns) + 1, "digest": "0"}, "functions": fns}


SAVE = {"fn": "app.io.save", "hash": "app#io.save", "inferred": ["Fs"], "direct": ["Fs"]}
GO = {"fn": "app.net.go", "hash": "app#net.go", "inferred": ["Net"], "direct": ["Net"],
      "netClass": ["unknown-host"]}
HOLE = {"fn": "app.svc.hole", "hash": "app#svc.hole", "inferred": ["Unknown"], "direct": ["Unknown"],
        "unknownWhy": ["dispatch:app.T.m"]}
K = lambda e: (e["hash"], e["fn"])           # noqa: E731  the unit key a row is judged on

REPORTS = {
    "base": env([SAVE, GO, HOLE]),
    # U — R1219's shape: two units of one report share a hash (candor-ts keys `<package>#<tail>`).
    "twins": env([
        {"fn": "src.billing.load", "hash": "app#load", "inferred": ["Fs"], "direct": ["Fs"]},
        {"fn": "src.ui.load", "hash": "app#load", "inferred": ["Net"], "direct": ["Net"],
         "netClass": ["unknown-host"]},
    ]),
    # U — two entries equal in (hash, fn): ONE unit, unioned (candor-scan's macro-expanded impls at one span).
    "equal": env([
        {"fn": "app.m.f", "hash": "app#m.f", "inferred": ["Fs"], "direct": ["Fs"]},
        {"fn": "app.m.f", "hash": "app#m.f", "inferred": ["Env"], "direct": ["Env"]},
        SAVE,
    ]),
    # I — a union-only key (no real entry claims it): reasonless Unknown + Net, as every producer writes it.
    "union_only": env([
        dict(SAVE),
        {"fn": "api.Sink.put", "hash": "app#api.Sink.put", "inferred": ["Net", "Unknown"],
         "interfaceUnion": True},
    ]),
    # I — the subclass-override shape (R867): a union published BESIDE the real entry, same hash and fn.
    "beside": env([
        {"fn": "app.B.m", "hash": "app#B.m", "inferred": ["Fs"], "direct": ["Fs"]},
        {"fn": "app.B.m", "hash": "app#B.m", "inferred": ["Env", "Fs"], "interfaceUnion": True},
    ]),
    # C — off-case and alias raw reasons, one leaf each (§6.2 ⟨0.40⟩ case; the table's alias spellings).
    "case": env([
        {"fn": "app.c.dml_off", "hash": "app#c.dml_off", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["DynamicMemberLookup:Root.p"]},
        {"fn": "app.c.native_up", "hash": "app#c.native_up", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["NATIVE:strlen"]},
        {"fn": "app.c.closure_cap", "hash": "app#c.closure_cap", "inferred": ["Unknown"],
         "direct": ["Unknown"], "unknownWhy": ["Closure:k"]},
        {"fn": "app.c.plain_fs", "hash": "app#c.plain_fs", "inferred": ["Fs"], "direct": ["Fs"]},
    ]),
}

# ======================================================================================================
# CELLS — EXPECTED written from SPEC before the first run. Keys of `want`:
#   exit        0 | 1 | 2                       (always pinned)
#   viol        set of (hash, fn)               (pinned on every exit 0/1 cell: exit 0 => empty)
#   refused     True | False                    (always pinned: exit 2 here is always a refusal document)
#   uneval      set of raw rule lines | "nonempty" | None   (None = this cell does not pin it)
#   zero        set of raw rules | None
#   ignored     set of line numbers | None
# ======================================================================================================
S, N, H = K(SAVE), K(GO), K(HOLE)


def cell(cid, report, policy, exit, viol=(), refused=None, uneval=None, zero=None, ignored=None, why=""):
    return {"id": cid, "report": report, "policy": policy,
            "want": {"exit": exit, "viol": set(viol), "refused": (exit == 2) if refused is None else refused,
                     "uneval": uneval, "zero": zero, "ignored": ignored}, "why": why}


WHOLE = "nonempty"     # a whole-policy refusal: one entry naming the policy (its text is engine-natural)

CELLS = [
    # ---- G: lexical / grammar (§6.2 Lexical; §3.1 ⟨0.24⟩ typo'd effect) ---------------------------------
    cell("g-deny-net", "base", "deny Net\n", 1, [N], zero=set(), why="control"),
    cell("g-deny-fs-scope", "base", "deny Fs app.io\n", 1, [S], zero=set(), why="segment scope, control"),
    cell("g-nomatch", "base", "deny Net zzz_no_such_layer\n", 0, zero={"deny Net zzz_no_such_layer"},
         why="§3.1 ⟨0.27⟩ zeroMatch"),
    cell("g-pure-scope", "base", "pure app\n", 1, [S, N], why="pure excludes Unknown (§4.0)"),
    cell("g-bare-pure", "base", "pure\n", 1, [S, N], why="absent scope = the whole unit"),
    cell("g-deny-two", "base", "deny Net Fs\n", 1, [S, N]),
    cell("g-deny-unknown", "base", "deny Unknown\n", 1, [H]),
    cell("g-filter-ok", "base", "deny Unknown[dispatch]\n", 1, [H]),
    cell("g-netclass-ok", "base", "deny Net[unknown-host]\n", 1, [N]),
    cell("g-scope-dots", "base", "deny Net a.b.c\n", 0, zero={"deny Net a.b.c"}),
    cell("g-leading-ws", "base", "   deny Net\n", 1, [N], why="ASCII whitespace separates"),
    cell("g-tab-sep", "base", "deny\tNet\n", 1, [N]),
    cell("g-trailing-ws", "base", "deny Net   \n", 1, [N]),
    cell("g-crlf", "base", "deny Net\r\n", 1, [N], why="CR is ASCII whitespace"),
    cell("g-cr-only", "base", "deny Net\r", 1, [N]),
    cell("g-no-final-nl", "base", "deny Net", 1, [N]),
    cell("g-inline-comment", "base", "deny Net  # why\n", 1, [N]),
    cell("g-hash-no-space", "base", "deny Net#why\n", 1, [N], why="a `#` begins a comment to end-of-line"),
    cell("g-dup-identical", "base", "deny Net\ndeny Net\n", 1, [N]),
    cell("g-nbsp-sep", "base", "deny Net\n", 2, uneval=WHOLE,
         why="NBSP is not a separator: one malformed token, zero rules"),
    cell("g-emsp-sep", "base", "deny Net\n", 2, uneval=WHOLE),
    cell("g-nbsp-twoline", "base", "deny Fs\ndeny Net\n", 1, [N], ignored={1},
         why="the NBSP line is ignored-with-a-warning; the second rule runs"),
    # the ⟨0.40⟩ BOM ruling (R1224)
    cell("g-bom", "base", BOM + "deny Net\n", 1, [N], ignored=set(), why="byte-0 U+FEFF stripped"),
    cell("g-bom-multi", "base", BOM + "deny Fs\ndeny Net\n", 1, [S, N], ignored=set(),
         why="the FIRST rule is evaluated — the case a kept BOM loses at exit 0"),
    cell("g-bom-mid", "base", "deny Net\n" + BOM + "deny Fs\n", 1, [N], ignored={2},
         why="a U+FEFF that is not at byte 0 stays a token character"),
    cell("g-bom-twice", "base", BOM + BOM + "deny Fs\ndeny Net\n", 1, [N], ignored={1},
         why="only ONE mark is stripped; the second stays in the first token"),
    cell("g-bom-crlf", "base", BOM + "deny Fs\r\ndeny Net\r\n", 1, [S, N], ignored=set()),
    # typo'd / missing effect: exit 2 (§3.1 ⟨0.24⟩ — "Both are exit 2")
    cell("g-unknown-effect", "base", "deny Nett\n", 2, uneval={"deny Nett"},
         why="a deny whose effect list is EMPTY is malformed under either reading"),
    cell("g-unknown-effect-scope", "base", "deny Nett app\n", 2, uneval={"deny Nett app"}),
    cell("g-only-scope", "base", "deny app\n", 2, uneval={"deny app"}),
    cell("g-semicolon", "base", "deny Net;\n", 2, uneval={"deny Net;"}),
    cell("g-very-long-effect", "base", "deny " + "N" * 200 + "\n", 2, uneval="nonempty"),
    cell("g-allow-typo", "base", "allow Nett host.example\n", 2, uneval="nonempty",
         why="`allow`'s effect position is a closed set: a typo is a policy error"),
    cell("g-filter-typo", "base", "deny Unknown[dispatc]\n", 2, uneval={"deny Unknown[dispatc]"},
         why="§6.2 ⟨0.24⟩ unrecognised class token is a policy error"),
    cell("g-filter-mixed", "base", "deny Unknown[dispatch,nativ]\n", 2,
         uneval={"deny Unknown[dispatch,nativ]"}),
    cell("g-netclass-typo", "base", "deny Net[unknown-hosts]\n", 2, uneval={"deny Net[unknown-hosts]"}),

    # ---- Z: zero rules and the policy-caused refusal document ------------------------------------------
    cell("z-empty", "base", "", 2, uneval=WHOLE, why="§6.2 ⟨0.28⟩"),
    cell("z-blank", "base", "\n\n", 2, uneval=WHOLE),
    cell("z-comment-only", "base", "# nothing\n", 2, uneval=WHOLE),
    cell("z-unknown-verb", "base", "denny Net\n", 2, uneval=WHOLE, why="an unknown KIND is ignored; zero rules"),
    cell("z-readme", "base", "This is a README.\nIt has no rules.\n", 2, uneval=WHOLE),
    cell("z-bad-token-beside", "base", "deny Fs\ndeny Unknown[dispach]\n", 2,
         uneval={"deny Fs", "deny Unknown[dispach]"},
         why="§3.1 ⟨0.40⟩: the bad-token refusal is whole-policy, so `unevaluated` carries EVERY rule"),
    cell("z-bad-token-alone", "base", "deny Unknown[dispach]\n", 2, uneval={"deny Unknown[dispach]"}),
    cell("z-bad-effect-beside", "base", "deny Fs\ndeny Nett app\n", 2, uneval={"deny Fs", "deny Nett app"}),

    # ---- U: units (§2 ⟨0.40⟩, R1219) ---------------------------------------------------------------------
    cell("u-twins-ctl", "twins", "deny Fs\n", 1, [("app#load", "src.billing.load")], why="control"),
    cell("u-twins-billing", "twins", "deny Fs src.billing\n", 1, [("app#load", "src.billing.load")],
         zero=set(), why="a hash-keyed gate reads billing as {Fs,Net} or loses it to its twin"),
    cell("u-twins-ui", "twins", "deny Fs src.ui\n", 0, zero=set(),
         why="ui.load performs no Fs: a hash-keyed gate FABRICATES here"),
    cell("u-twins-net-billing", "twins", "deny Net src.billing\n", 0, zero=set()),
    cell("u-equal-env", "equal", "deny Env app.m\n", 1, [("app#m.f", "app.m.f")],
         why="equal (hash, fn) entries are ONE unit, unioned: Env is not lost to the first row"),
    cell("u-equal-fs", "equal", "deny Fs app.m\n", 1, [("app#m.f", "app.m.f")]),

    # ---- I: interfaceUnion entries (§3.1 ⟨0.40⟩) ---------------------------------------------------------
    cell("i-ctl", "union_only", "deny Fs\n", 1, [S], why="control"),
    cell("i-scoped-net", "union_only", "deny Net api\n", 0, zero={"deny Net api"},
         why="a rule matching only union entries rides zeroMatch (R1234)"),
    cell("i-scoped-unknown-native", "union_only", "deny Unknown[native] api\n", 0,
         zero={"deny Unknown[native] api"},
         why="a union entry is never an answerability subject: no refusal (R1223)"),
    cell("i-unscoped-unknown-native", "union_only", "deny Unknown[native]\n", 0, zero=set(),
         why="no UNIT carries Unknown: answered, not refused (R1223)"),
    cell("i-unscoped-net", "union_only", "deny Net\n", 0, zero=set(), why="a union entry is never a violation row"),
    cell("i-beside-ctl", "beside", "deny Fs app.B\n", 1, [("app#B.m", "app.B.m")], why="control"),
    cell("i-beside-env", "beside", "deny Env app.B\n", 0, zero=set(),
         why="the real body performs no Env; the union beside it is not merged into the unit"),

    # ---- C: reason-prefix case (§6.2 ⟨0.40⟩) -------------------------------------------------------------
    cell("c-ctl", "case", "deny Fs\n", 1, [("app#c.plain_fs", "app.c.plain_fs")], why="control"),
    cell("c-reflect", "case", "deny Unknown[reflect]\n", 1, [("app#c.dml_off", "app.c.dml_off")]),
    cell("c-native", "case", "deny Unknown[native]\n", 1, [("app#c.native_up", "app.c.native_up")]),
    cell("c-indirect", "case", "deny Unknown[indirect]\n", 1, [("app#c.closure_cap", "app.c.closure_cap")]),
    cell("c-unresolved", "case", "deny Unknown[unresolved]\n", 0,
         why="no off-case token falls to the catch-all"),
]

# ROWS FROM THE OLD BATTERY THAT SPEC DOES NOT DECIDE — not run, printed every run. Pinning one is a SPEC
# clause first, then a cell here.
NOT_PINNED = {
    "case-verb `DENY Net`": "§6.2 does not say whether a rule KIND is case-sensitive",
    "case-effect `deny NET` / `deny net`": "§6.2 does not say whether an EFFECT token is case-sensitive",
    "unknown-effect-2 `deny Net Fss`": "§3.1 ⟨0.24⟩ leaves a valid effect + an unrecognised trailing token OPEN (a scope?)",
    "extra-tokens `deny Net app extra`": "the same open middle: a second scope token",
    "filter-empty `deny Unknown[]`": "PART 97 measured all-classes four-way; SPEC does not specify it",
    "filter-unclosed `deny Unknown[dispatch`": "not specified",
    "filter-spaces `deny Unknown[ dispatch ]`": "not specified (whitespace splits the token)",
    "scope-glob `deny Net app.*`": "§6.2 scope matching does not define `*`",
    "scope-leading-dot `deny Net .app`": "not specified",
    "two-on-one-line `deny Net; deny Fs`": "not specified beyond `Net;` being no effect",
    "allow/forbid on gate --report": "their report-route answer is §3.1's answerability refusal; pinned by the forbid/allow PARTs, not re-pinned here",
}

# (cell, engine) -> the OPEN register row the expectation rests on. A PASSING XFAIL IS A FAILURE.
# Written from the released 0.40.13 calibration (2026-10-20); each engine lane retires its entries in the
# commit that lands the fix.
XFAIL = {
    ('g-bom', 'rust'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom', 'java'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom', 'ts'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-multi', 'rust'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-multi', 'java'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-multi', 'ts'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-crlf', 'rust'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-crlf', 'java'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-bom-crlf', 'ts'):
        'R1224: the engine keeps a byte-0 U+FEFF as part of `deny`, so the first rule is ignored (a one-rule file refuses, a multi-rule file loses its first rule at exit 1/0)',
    ('g-unknown-effect', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-unknown-effect', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-unknown-effect-scope', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-unknown-effect-scope', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-only-scope', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-only-scope', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-semicolon', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-semicolon', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-very-long-effect', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-very-long-effect', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-allow-typo', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-allow-typo', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-filter-typo', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-filter-typo', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-filter-mixed', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-filter-mixed', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-netclass-typo', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('g-netclass-typo', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-token-beside', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-token-beside', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-token-alone', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-token-alone', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-effect-beside', 'rust'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('z-bad-effect-beside', 'swift'):
        'R1233: the policy-error refusal document carries no `unevaluated` (java and ts carry every rule)',
    ('u-twins-ctl', 'rust'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-ctl', 'java'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-ctl', 'swift'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-billing', 'rust'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-billing', 'java'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-billing', 'swift'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-ui', 'rust'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-ui', 'java'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-ui', 'swift'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-net-billing', 'rust'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-net-billing', 'java'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('u-twins-net-billing', 'swift'):
        'R1219: the gate keys units by `hash` alone, so two units sharing a hash collapse into one row named after one of them',
    ('i-scoped-net', 'java'):
        'R1234: a rule matching only `interfaceUnion` entries is not disclosed as zeroMatch',
    ('i-scoped-unknown-native', 'java'):
        'R1223: a reasonless `interfaceUnion` entry is treated as an answerability subject and the narrowed filter refuses',
    ('i-unscoped-unknown-native', 'java'):
        'R1223: a reasonless `interfaceUnion` entry is treated as an answerability subject and the narrowed filter refuses',
    ('i-scoped-net', 'ts'):
        'R1234: a rule matching only `interfaceUnion` entries is not disclosed as zeroMatch',
    ('i-scoped-unknown-native', 'ts'):
        'R1223: a reasonless `interfaceUnion` entry is treated as an answerability subject and the narrowed filter refuses',
    ('i-unscoped-unknown-native', 'ts'):
        'R1223: a reasonless `interfaceUnion` entry is treated as an answerability subject and the narrowed filter refuses',
    ('i-beside-env', 'java'):
        "R1223: java's report route merges a union entry into the real entry sharing its hash, so the union's Env is charged to the unit",
}

# ======================================================================================================
# X — cross-fed engine-written reports (scopeless rules only)
# ======================================================================================================
X_TREES = {
    "rust": {"Cargo.toml": '[package]\nname = "xfeed"\nversion = "0.0.0"\nedition = "2021"\n',
             "src/lib.rs": 'pub fn hit_fs() { let _ = std::fs::read("/tmp/x"); }\n'
                           'pub fn hit_net() { let _ = std::net::TcpStream::connect("h.example.com:80"); }\n'
                           'pub fn calm() -> u32 { 1 }\n'},
    "java": {"app/X.java": 'package app;\npublic class X {\n'
                           '  public static void hitFs() { try { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/x")); } catch (Exception e) {} }\n'
                           '  public static void hitNet() { try { new java.net.Socket("h.example.com", 80); } catch (Exception e) {} }\n'
                           '  public static int calm() { return 1; }\n}\n'},
    "ts": {"package.json": '{"name":"xfeed","version":"1.0.0"}\n',
           "x.ts": 'import * as fs from "fs";\n'
                   'export function hitFs(): void { fs.readFileSync("/tmp/x"); }\n'
                   'export function hitNet(): void { void fetch("https://h.example.com/x"); }\n'
                   'export function calm(): number { return 1; }\n'},
    "swift": {"x.swift": 'import Foundation\n'
                         'enum X {\n'
                         '  static func hitFs() { _ = FileManager.default.contents(atPath: "/tmp/x") }\n'
                         '  static func hitNet() { _ = URLSession.shared.dataTask(with: URL(string: "https://h.example.com/x")!) }\n'
                         '  static func calm() -> Int { 1 }\n}\n'},
}
X_RULES = ["deny Fs", "deny Net", "pure"]


def run(cmd, cwd=None):
    e = {k: v for k, v in os.environ.items()
         if k not in ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY", "CANDOR_BASELINE")}
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=e, timeout=300)
        return p.returncode, p.stdout.decode(errors="replace"), p.stderr.decode(errors="replace")
    except Exception as ex:          # noqa: BLE001 — a harness failure, labelled as such by the caller
        return None, "", str(ex)


def scan_x(eng, ws):
    """Scan the engine's own three-function tree; return the written report JSON (or None, a HARNESS fault)."""
    d = os.path.join(ws, "xsrc", eng)
    shutil.rmtree(d, ignore_errors=True)
    for rel, txt in X_TREES[eng].items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(txt)
    out = os.path.join(ws, "xrep", eng)
    os.makedirs(out, exist_ok=True)
    if eng == "rust":
        rc, _o, err = run([G.rust_scan(), d, "--out", os.path.join(out, "r")])
    elif eng == "java":
        cls = os.path.join(d, "classes")
        rc0, _o, err = run(["javac", "-d", cls, os.path.join(d, "app", "X.java")])
        if rc0 != 0:
            return None, "javac: " + err[:200]
        rc, _o, err = run(["java", "-jar", G.java_jar(), cls, "--json", os.path.join(out, "r.json")])
    elif eng == "ts":
        rc, _o, err = run(["node", os.path.join(G.ts_root(), "scan.mjs"), d, os.path.join(out, "r")])
    else:
        rc, _o, err = run([G.swift_bin(), d, "--out", os.path.join(out, "r")])
    cands = sorted(f for f in os.listdir(out) if f.endswith(".json")
                   and not any(s in f for s in (".callgraph.", ".hierarchy.", ".locs.", ".gate.", ".layerreach.", ".calibrated.")))
    if not cands:
        return None, f"scan exit {rc}, no report written: {err[:200]}"
    try:
        return json.load(open(os.path.join(out, cands[0]))), None
    except Exception as ex:         # noqa: BLE001
        return None, f"unreadable report {cands[0]}: {ex}"


def x_expected(report, rule):
    """EXPECTED for a scopeless rule over an engine-written report, from its bytes: the non-union UNITS
    (§2 ⟨0.40⟩: keyed (hash, fn); an entry without hash keyed by fn) whose `inferred` carries the effect.
    `pure` (§4.0) fires on any unit with a concrete effect; `Unknown` never fires it."""
    want = set()
    for e in report.get("functions", []):
        if e.get("interfaceUnion"):
            continue
        inf = set(e.get("inferred") or [])
        if rule == "pure":
            hit = bool(inf - {"Unknown"})
        else:
            hit = rule.split()[1] in inf
        if hit:
            want.add((e.get("hash"), e.get("fn")))
    return want


# ======================================================================================================
# one gate run + judging
# ======================================================================================================

def gate(eng, loc, policy_bytes, ws, tag):
    pf = os.path.join(ws, f"pol.{tag}")
    with open(pf, "wb") as fh:
        fh.write(policy_bytes.encode("utf-8"))
    gj = os.path.join(ws, f"{eng}.{tag}.gate.json")
    if os.path.exists(gj):
        os.remove(gj)                       # never read a stale document as this run's
    base = {"rust": [G.rust_query(), "gate"], "java": ["java", "-jar", G.java_jar(), "gate"],
            "ts": ["node", os.path.join(G.ts_root(), "query.mjs"), "gate"], "swift": [G.swift_bin(), "gate"]}[eng]
    rc, _o, err = run(base + ["--report", loc, "--policy", pf, "--gate-json", gj])
    doc = None
    if os.path.exists(gj):
        try:
            doc = json.load(open(gj, encoding="utf-8"))
        except Exception:                   # noqa: BLE001
            doc = None
    return rc, doc, err


def observe(rc, doc):
    """What a cell compares, read off one run."""
    o = {"exit": rc, "doc": doc is not None}
    if not isinstance(doc, dict):
        return o
    o["refused"] = bool(doc.get("refused")) and "violations" not in doc
    o["refused_key"] = "refused" in doc
    o["viol"] = {(v.get("hash"), v.get("fn")) for v in (doc.get("violations") or [])} \
        if isinstance(doc.get("violations"), list) else None
    ue = doc.get("unevaluated")
    o["uneval"] = {u.get("rule") for u in ue if isinstance(u, dict)} if isinstance(ue, list) else set()
    zm = doc.get("zeroMatch")
    o["zero"] = set(zm) if isinstance(zm, list) else set()
    ig = doc.get("ignored")
    o["ignored"] = {i.get("line") for i in ig if isinstance(i, dict)} if isinstance(ig, list) else set()
    return o


def judge(o, want):
    """Problems (empty == the engine gave the EXPECTED answer)."""
    bad = []
    if o["exit"] != want["exit"]:
        bad.append(f"exit {o['exit']}, EXPECTED {want['exit']}")
    if not o["doc"]:
        return bad + ["no readable --gate-json document"]
    if want["refused"]:
        if not o.get("refused"):
            bad.append("not a refusal document (`refused: true` and no `violations` key)")
    else:
        if o.get("refused_key"):
            bad.append("carries `refused` on a verdict (§3.1 ⟨0.27⟩: the two shapes are disjoint on it)")
        if o.get("viol") is None:
            bad.append("no `violations` array on a verdict")
        elif o["viol"] != want["viol"]:
            extra, missing = sorted(o["viol"] - want["viol"]), sorted(want["viol"] - o["viol"])
            if extra:
                bad.append(f"violation(s) EXPECTED to pass: {extra}")
            if missing:
                bad.append(f"violation(s) MISSING: {missing}")
    u = want["uneval"]
    if u == "nonempty":
        if not o.get("uneval"):
            bad.append("`unevaluated` absent or empty")
    elif u is not None and o.get("uneval") != u:
        bad.append(f"`unevaluated` rules {sorted(o.get('uneval') or [])}, EXPECTED {sorted(u)}")
    if want["zero"] is not None and o.get("zero") != want["zero"]:
        bad.append(f"`zeroMatch` {sorted(o.get('zero') or [])}, EXPECTED {sorted(want['zero'])}")
    if want["ignored"] is not None and o.get("ignored") != want["ignored"]:
        bad.append(f"`ignored` lines {sorted(o.get('ignored') or [])}, EXPECTED {sorted(want['ignored'])}")
    return bad


# ======================================================================================================

def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    only_cell = argv[argv.index("--cell") + 1] if "--cell" in argv else None
    ws = tempfile.mkdtemp(prefix="candor-p99-")
    fails = 0
    fault = [bool(os.environ.get("CANDOR_PROBE_FAULT"))]
    try:
        engines = [e for e in ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in ENGINES if G.installed(e) and not G.alive(e)]
        print(f"  engines present: {', '.join(engines) or '(none)'}")
        if broken:
            print(f"  FAIL: installed but not responding: {', '.join(broken)} — HARNESS/INSTALL, not candor")
            fails += 1
        if not engines:
            print("  FAIL: no engine present — a part that ran nothing is not a pass")
            return 1
        ids = [c["id"] for c in CELLS]
        assert len(ids) == len(set(ids)), "duplicate cell id"
        for (cid, eng), row in XFAIL.items():
            assert cid in ids and eng in ENGINES and "R" in row, f"bad XFAIL entry {(cid, eng)}"
        cells = [c for c in CELLS if only_cell is None or c["id"] == only_cell]

        results = {}                          # (cid, eng) -> (observation, problems)
        for eng in engines:
            locs = {name: G.write_report(os.path.join(ws, f"r-{name}"), eng, rep) for name, rep in REPORTS.items()}
            for c in cells:
                rc, doc, err = gate(eng, locs[c["report"]], c["policy"], ws, f"{c['id']}")
                if fault[0] and c["id"] == "g-deny-two" and doc and doc.get("violations"):
                    # probe_check.py's fault (PART 30): an engine answer corrupted in the direction this part
                    # forbids — one violation silently missing from a real document.
                    print(f"  PROBE: CANDOR_PROBE_FAULT — deleting one violation from {eng}'s g-deny-two document")
                    doc = dict(doc); doc["violations"] = doc["violations"][1:]
                    fault[0] = False
                o = observe(rc, doc)
                o["_doc"], o["_err"] = doc, err
                results[(c["id"], eng)] = (o, judge(o, c["want"]))

        # ---- report: per cell, EXPECTED vs each engine --------------------------------------------------
        n_ok = n_xfail = 0
        ctl_dead = set()
        for c in cells:
            for eng in engines:
                o, bad = results[(c["id"], eng)]
                xf = XFAIL.get((c["id"], eng))
                if not bad and xf:
                    print(f"    {c['id']:28s} {eng:6s} XFAIL ARM PASSED — expectation is STALE ({xf}); retire it")
                    fails += 1
                elif bad and xf:
                    n_xfail += 1
                elif bad:
                    fails += 1
                if c["why"].startswith("control") and o["exit"] != c["want"]["exit"]:
                    ctl_dead.add((c["report"], eng))
                if bad:
                    tag = f"xfail [{xf.split(':')[0]}]" if xf else "DIVERGE from EXPECTED"
                    print(f"    {c['id']:28s} {eng:6s} {tag} — {'; '.join(bad)}"
                          + (f"  [stderr: {o['_err'].strip()[:140]}]" if o["exit"] == 2 and c["want"]["exit"] != 2 else ""))
                else:
                    n_ok += 1
        for rep, eng in sorted(ctl_dead):
            print(f"    CONTROL DEAD  {eng:6s} report `{rep}`: its control cell's EXIT was wrong, so this engine's other "
                  f"cells over `{rep}` measured a gate that may never have read the report")
            fails += 1

        # ---- floors (vacuity, from the engines' own output) ----------------------------------------------
        if only_cell is None:
            for eng in engines:
                exits = {results[(c['id'], eng)][0]["exit"] for c in cells}
                zeros = sum(1 for c in cells if results[(c["id"], eng)][0].get("zero"))
                if not {0, 1, 2} <= exits or not zeros:
                    print(f"    VACUOUS {eng}: exits seen {sorted(x for x in exits if x is not None)}, "
                          f"{zeros} zeroMatch document(s) — the battery stopped exercising a verdict shape")
                    fails += 1

        # ---- X: cross-fed engine-written reports ----------------------------------------------------------
        x_ok = x_bad = 0
        if only_cell is None:
            for src in engines:
                rep, why = scan_x(src, ws)
                if rep is None:
                    print(f"    X  {src:6s} HARNESS — could not produce a report to cross-feed: {why}")
                    fails += 1
                    continue
                if not x_expected(rep, "deny Fs") or not x_expected(rep, "deny Net"):
                    print(f"    X  {src:6s} VACUOUS — the {src} report carries no Fs or no Net unit; the cross-feed proves nothing")
                    fails += 1
                    continue
                for eng in engines:
                    loc = G.write_report(os.path.join(ws, f"x-{src}"), eng, rep)
                    for i, rule in enumerate(X_RULES):
                        want = {"exit": 1, "viol": x_expected(rep, rule), "refused": False,
                                "uneval": None, "zero": None, "ignored": None}
                        rc, doc, err = gate(eng, loc, rule + "\n", ws, f"x-{src}-{i}")
                        bad = judge(observe(rc, doc), want)
                        if bad:
                            x_bad += 1
                            print(f"    X  {src}-report  {eng:6s} `{rule}` DIVERGE — {'; '.join(bad)}"
                                  + (f" [stderr: {err.strip()[:140]}]" if rc == 2 else ""))
                        else:
                            x_ok += 1
            fails += x_bad

        # ---- SEEDS: the comparator must be able to say DIVERGE, every run ---------------------------------
        seed_bad = []
        if only_cell is None:
            e0 = engines[0]
            def real(cid):
                return results[(cid, e0)][0]
            want_of = {c["id"]: c["want"] for c in cells}
            o = dict(real("g-deny-two"))
            doc = o["_doc"]
            if doc and len(doc.get("violations") or []) >= 1:
                d2 = dict(doc); d2["violations"] = doc["violations"][1:]
                if not judge(observe(o["exit"], d2), want_of["g-deny-two"]):
                    seed_bad.append("doc seed: a violation deleted from a real --gate-json was NOT caught")
            else:
                seed_bad.append(f"doc seed could not run: {e0}'s g-deny-two document has no violations")
            o = real("g-nomatch")
            doc = o["_doc"]
            if doc and doc.get("zeroMatch"):
                d2 = {k: v for k, v in doc.items() if k != "zeroMatch"}
                if not judge(observe(o["exit"], d2), want_of["g-nomatch"]):
                    seed_bad.append("zeromatch seed: a dropped zeroMatch was NOT caught")
            else:
                seed_bad.append(f"zeromatch seed could not run: {e0}'s g-nomatch document has no zeroMatch")
            o = real("g-deny-net")
            doc = o["_doc"]
            if doc:
                d2 = dict(doc); d2["refused"] = True
                if not judge(observe(o["exit"], d2), want_of["g-deny-net"]):
                    seed_bad.append("refused seed: `refused` added to an exit-1 verdict was NOT caught")
            moved = []
            for c in cells:
                w = dict(c["want"])
                if c["id"] == "g-tab-sep":
                    w["exit"] = 0 if w["exit"] else 1
                if bool(judge(results[(c["id"], e0)][0], w)) != bool(results[(c["id"], e0)][1]):
                    moved.append(c["id"])
            if moved != ["g-tab-sep"]:
                seed_bad.append(f"expected seed: flipping g-tab-sep's EXPECTED exit moved {moved}, want exactly it")
            # unpinned: a cell with no EXPECTED on which every engine agrees must classify AGREE-UNPINNED.
            obs = {eng: results[("g-deny-net", eng)][0]["exit"] for eng in engines}
            if not (len(set(obs.values())) == 1 and classify_unpinned(obs) == "AGREE-UNPINNED"):
                seed_bad.append(f"unpinned seed: agreement {obs} was not classified AGREE-UNPINNED")
            for s in seed_bad:
                print(f"  SEED FAIL: {s}")
            fails += len(seed_bad)
            if not seed_bad:
                print(f"  seeds ({e0}): a deleted violation, a dropped zeroMatch and an added `refused` are caught; "
                      f"one flipped EXPECTED moves exactly one cell; agreement with no EXPECTED is AGREE-UNPINNED")

        print(f"  not pinned by SPEC, not run ({len(NOT_PINNED)}):")
        for k, v in NOT_PINNED.items():
            print(f"    · {k}: {v}")
        print(f"  {len(cells)} cell(s) x {len(engines)} engine(s): {n_ok} agree with EXPECTED, {n_xfail} xfail; "
              f"cross-fed: {x_ok} agree, {x_bad} diverge")
        print("POLICY-SEMANTICS DIFFERENTIAL: " + ("OK" if not fails else f"{fails} FAILURE(S)"))
        return 1 if fails else 0
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)


def classify_unpinned(observed):
    """A cell with no EXPECTED: agreement is AGREE-UNPINNED (a failure), disagreement DISAGREE-UNPINNED."""
    return "AGREE-UNPINNED" if len(set(observed.values())) == 1 else "DISAGREE-UNPINNED"


if __name__ == "__main__":
    sys.exit(main())
