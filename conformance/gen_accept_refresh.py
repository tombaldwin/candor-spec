#!/usr/bin/env python3
"""
PART 106 — `accepts`: REFRESHING `accept` LINES AFTER AN UPGRADE, AND ADOPTING THEM (SPEC §6.2 ⟨0.41⟩, §3.3.1).

WHAT IT PINS
------------
`<cmd> accepts [--report <loc>] [--policy <file>] [--json] [--adopt --because <reason>]` prints a PROPOSED policy:
the input with its STALE entries deleted, its over-wide ACCEPTED entries narrowed to the rows they accepted, the
verb's own earlier comments regenerated, an `exceeded` entry left as it is with a COMMENT proposing the wider line,
and — under `--adopt` only — one appended `accept` line, carrying the operator's reason, per violation row no
entry names. It never writes a file and never accepts more than the policy it read: the property this part checks
on every row, through the engine's own GATE over the proposed text, is

    refresh:  accepted(proposed) == accepted(input),   violations(proposed) == violations(input) − AS-EFF-012
    adopt:    accepted(proposed) ⊆ accepted(input) ∪ the rows the created lines name (and nested rows riding them)

The cardinal direction is a NEW violation silently accepted, so most rows (◆) are OVER-ACCEPT detectors: a
refresh that writes a line for a new violation, widens an exceeded entry, re-keys a stale entry onto a renamed
function with the old reason, honours `--because` without `--adopt`, invents a reason, covers an exceeded row
under `--adopt`, writes the rule's Unknown filter instead of the row's classes, or leaves an over-wide entry
pre-signed for an effect the function no longer has.

ONE ARM: a HAND-WRITTEN report (gen_accept.py's R arm — same bytes for every engine, `fn` spelled `dao.a`),
because the verb is a report-route query (§3.3.1) and the classifier is out of the loop.

REFERENCE-LED, AND THE SKIP IS PROBED, NEVER DECLARED. An engine IMPLEMENTS iff `accepts --json` over row q01
exits 0 with a JSON object carrying `text`. Otherwise one counted SKIP per engine, and what is scored is the
pre-rung posture: the unknown verb exits NON-ZERO, prints no plan, and leaves the policy file's bytes unchanged.

CALIBRATED EVERY RUN. The expectations are checked against a REFERENCE MODEL of the verb (`model()`), computed
from a real ⟨0.41⟩ engine's GATE output on the same bytes (the verdict over the input policy, one run per rule
line for per-line attribution and `reasonClass`, the report's units) — and the model's proposed text is then
GATED by that same engine, so the over-accept property above is judged by an engine, not by this file. The model
must pass EVERY row. Each of MUTANTS (a wrong reading of the clause) must fail ≥1 row, and every ◆ row must be
failed by ≥1 mutant; a row no mutant fails is VACUOUS and fails the part.

USAGE
    python3 gen_accept_refresh.py [--keep] [--engine E]
    python3 gen_accept_refresh.py --selftest      # the model and the judge on synthetic documents; no engine
"""
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
import gen_accept as A                       # noqa: E402  the ⟨0.41⟩ report arm, gate driver and lexer — one copy

SPEC_CLAUSES = [
    ("§6.2 ⟨0.41⟩", "**`accepts` — REFRESHING `accept` LINES IS A VERB THAT PRINTS A PROPOSED POLICY, AND IT CAN ONLY"),
    ("§6.2 ⟨0.41⟩", "<cmd> accepts [--report <locator>] [--policy <file>] [--json] [--adopt --because <reason>]"),
    ("§6.2 ⟨0.41⟩", "**A stale entry's line is DELETED**"),
    ("§6.2 ⟨0.41⟩", "An accepted entry wider than what it accepted is NARROWED to it."),
    ("§6.2 ⟨0.41⟩", "**What it only PROPOSES — an `exceeded` entry.**"),
    ("§6.2 ⟨0.41⟩", "# candor-accepts: exceeded (adds <added tokens>) — REPLACE the line above with: accept <fn> <the row's effects> for <rule tokens> because <reason>"),
    ("§6.2 ⟨0.41⟩", "**Taking the proposal is ONE human edit: replace the line above with the text after `with: ` and delete the comment.**"),
    ("§6.2 ⟨0.41⟩", "a refusal because the policy holds no rules MUST say that a shell redirect onto the policy empties it"),
    ("§6.2 ⟨0.41⟩", "**Its route is the report route, and what that cannot see is listed.**"),
    ("§6.2 ⟨0.41⟩", "`unnamed` is present in BOTH modes and holds exactly the rows `--adopt` writes a line for"),
    ("§6.2 ⟨0.41⟩", "whose message MUST name `accepts`."),
    ("§6.2 ⟨0.41⟩", "and `--adopt` changes its SCALE, not its kind"),
    ("§6.2 ⟨0.41⟩", "**What it never does.** It never writes an `accept` line for a row that no entry names"),
    ("§6.2 ⟨0.41⟩", "**Adoption — `--adopt --because <reason>`.**"),
    ("§6.2 ⟨0.41⟩", "the classes the row has, never the rule's filter"),
    ("§6.2 ⟨0.41⟩", "**When it answers.**"),
    ("§6.2 ⟨0.41⟩", "**The property, which conformance pins.**"),
    ("§3.3.1 ⟨0.41⟩", "and `accepts` (§6.2 ⟨0.41⟩)"),
    ("§6.2 ⟨0.41⟩", "**The SOLE refusal is a refusal.**"),
    ("§6.2 ⟨0.41⟩", "**Lines are numbered as the gate numbers them: a line ends at LF, at CR, or at CRLF, which is"),
    ("§6.2 ⟨0.41⟩", "**A row whose `Unknown` carries no reason class is written nowhere.**"),
]

MARK = "# candor-accepts:"
F, report, A_DENY = A.F, A.report, A.A_DENY
UNAN = A.UNAN
REASON = "pre-existing at adoption"


def rd(*extra, drop=(), unanalyzed=None):
    r = report(*extra, drop=drop)
    if unanalyzed:
        r["unanalyzed"] = unanalyzed
    return r


# =====================================================================================================
# ROWS. args: the verb's flags beyond --report/--policy/--json. want: exit; text — the proposed file as
# a list of lines (each ends with "\n"); removed — input lines deleted; narrowed — {line: [tokens]};
# proposals — {line: [added tokens]}; created — [fn …]; after — the gate's exit over the proposed text.
# future — a LATER report, the function having regained what the proposal stopped accepting: the gate over the
# proposed text and THAT report must exit 1 (the proposal makes no future row easier to accept).
# ◆ (dia) = an over-accept detector.
# =====================================================================================================
ROWS = [
    dict(id="q01_fresh", rep=rd(), pol=["deny Fs dao", A_DENY], args=[],
         want=dict(exit=0, text=["deny Fs dao", A_DENY], removed=[], narrowed={}, proposals={}, after=0,
                   unnamed=[], unjudged=[])),
    dict(id="q02_stale", rep=rd(drop=("dao.a",)), pol=["deny   Fs  dao   # keep me", A_DENY, "", "# a note"], args=[],
         want=dict(exit=0, text=["deny   Fs  dao   # keep me", "", "# a note"], removed=[2], narrowed={},
                   proposals={}, after=0)),
    dict(id="q03_new_violation", dia=1, rep=rd(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao", A_DENY], args=[],
         want=dict(exit=0, text=["deny Fs dao", A_DENY], removed=[], narrowed={}, proposals={}, after=1,
                   unnamed=["dao.b"])),
    dict(id="q03b_because_without_adopt", dia=1, rep=rd(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao", A_DENY],
         args=["--because", "known"], want=dict(exit=2)),
    dict(id="q04_exceeded", dia=1, rep=rd(F("dao.a", ["Fs", "Rand"], "ha"), drop=("dao.a",)),
         pol=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because x"], args=[],
         want=dict(exit=0, text=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because x",
                                 MARK + " exceeded (adds Rand) — REPLACE the line above with: accept dao.a Fs Rand for deny Fs Rand dao because x"],
                   removed=[], narrowed={}, proposals={2: ["Rand"]}, after=1, unnamed=[]), take=0),
    dict(id="q05_renamed_key", dia=1, rep=rd(F("dao.a2", ["Fs"], "ha2"), drop=("dao.a",)),
         pol=["deny Fs dao", A_DENY], args=[],
         want=dict(exit=0, text=["deny Fs dao"], removed=[2], narrowed={}, proposals={}, after=1, unnamed=["dao.a2"])),
    dict(id="q05b_renamed_key_adopt", rep=rd(F("dao.a2", ["Fs"], "ha2"), drop=("dao.a",)),
         pol=["deny Fs dao", A_DENY], args=["--adopt", "--because", "renamed by the upgrade, reviewed"],
         want=dict(exit=0, text=["deny Fs dao", "accept dao.a2 Fs for deny Fs dao because renamed by the upgrade, reviewed"],
                   removed=[2], narrowed={}, proposals={}, created=["dao.a2"], after=0)),
    dict(id="q06_class_moved", dia=1, rep=rd(F("dao.c", ["Unknown"], "hc", unknownWhy=["native:strlen"])),
         pol=["deny Unknown[dispatch,native] dao",
              "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because x  # why"], args=[],
         want=dict(exit=0, text=["deny Unknown[dispatch,native] dao",
                                 "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because x  # why",
                                 MARK + " exceeded (adds Unknown[native]) — REPLACE the line above with: accept dao.c Unknown[native] for "
                                        "deny Unknown[dispatch,native] dao because x # why"],
                   removed=[], narrowed={}, proposals={2: ["Unknown[native]"]}, after=1), take=0),
    dict(id="q07_twins_kept", rep=rd(F("dao.t", ["Fs"], "ht1"), F("dao.t", ["Fs"], "ht2")),
         pol=["deny Fs dao", A_DENY, "accept dao.t Fs for deny Fs dao because x"], args=[],
         want=dict(exit=0, text=["deny Fs dao", A_DENY, "accept dao.t Fs for deny Fs dao because x"],
                   removed=[], narrowed={}, proposals={}, after=1)),
    dict(id="q08_adopt", rep=rd(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao"],
         args=["--adopt", "--because", "  pre-existing   at adoption "],
         want=dict(exit=0, text=["deny Fs dao", "accept dao.a Fs for deny Fs dao because " + REASON,
                                 "accept dao.b Fs for deny Fs dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a", "dao.b"], after=0,
                   unnamed=["dao.a", "dao.b"])),
    dict(id="q08b_adopt_no_reason", dia=1, rep=rd(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao"], args=["--adopt"],
         want=dict(exit=2)),
    dict(id="q08c_adopt_hash_reason", rep=rd(F("dao.b", ["Fs"], "hb")), pol=["deny Fs dao"],
         args=["--adopt", "--because", "see #1"], want=dict(exit=2, stderr_re=r"#[^\n]*comment|comment[^\n]*#")),
    dict(id="q09_adopt_exceeded", dia=1, rep=rd(F("dao.a", ["Fs", "Rand"], "ha"), F("dao.b", ["Fs"], "hb"), drop=("dao.a",)),
         pol=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because x"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because x",
                                 MARK + " exceeded (adds Rand) — REPLACE the line above with: accept dao.a Fs Rand for deny Fs Rand dao because x",
                                 "accept dao.b Fs for deny Fs Rand dao because " + REASON],
                   removed=[], narrowed={}, proposals={2: ["Rand"]}, created=["dao.b"], after=1)),
    dict(id="q10_adopt_twins", rep=rd(F("dao.t", ["Fs"], "ht1"), F("dao.t", ["Fs"], "ht2")), pol=["deny Fs dao"],
         args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao", "accept dao.a Fs for deny Fs dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a"], after=1)),
    dict(id="q11_adopt_nested", only=("rust", "java", "ts"), rep=A.nested_rep(["Fs"]), pol=["deny Fs Clock dao"],
         args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs Clock dao", "accept {a} Fs for deny Fs Clock dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["{a}"], after=0)),
    dict(id="q12_incomplete", rep=rd(F("dao.b", ["Fs"], "hb"), drop=("dao.a",), unanalyzed=UNAN),
         pol=["deny Fs dao", A_DENY], args=[], want=dict(exit=2)),
    dict(id="q13_forbid_unjudged", rep=rd(F("dao.b", ["Fs"], "hb")),
         pol=["deny Fs dao", "forbid dao -> infra", "accept dao.a for forbid dao -> infra because x"], args=[],
         want=dict(exit=0, text=["deny Fs dao", "forbid dao -> infra", "accept dao.a for forbid dao -> infra because x"],
                   removed=[], narrowed={}, proposals={}, after=1, unjudged=[3], unnamed=["dao.a", "dao.b"])),
    dict(id="q14_ignored_kept", rep=rd(drop=("dao.a",)), pol=["deny Fs dao", "accept dao.a Fs for deny Fs dao", A_DENY],
         args=[], want=dict(exit=0, text=["deny Fs dao", "accept dao.a Fs for deny Fs dao"], removed=[3], narrowed={},
                            proposals={}, after=0, ignored=[2])),
    dict(id="q15_own_comments", rep=rd(),
         pol=["deny Fs dao", A_DENY, "  " + MARK + " exceeded (adds Rand): accept dao.a Fs Rand for deny Fs dao because x"],
         args=[], want=dict(exit=0, text=["deny Fs dao", A_DENY], removed=[], narrowed={}, proposals={}, after=0)),
    dict(id="q16_narrow", dia=1, rep=rd(), pol=["deny Fs Rand dao", "accept dao.a Rand Fs for deny Fs Rand dao because known  # why"],
         args=[], want=dict(exit=0, text=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because known # why"],
                            removed=[], narrowed={2: ["Fs"]}, proposals={}, after=0),
         future=(rd(F("dao.a", ["Fs", "Rand"], "ha"), drop=("dao.a",)), 1)),
    dict(id="q16b_narrow_class", dia=1, rep=rd(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m"])),
         pol=["deny Unknown[dispatch,native] dao",
              "accept dao.c Unknown[dispatch,native] for deny Unknown[dispatch,native] dao because x"], args=[],
         want=dict(exit=0, text=["deny Unknown[dispatch,native] dao",
                                 "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because x"],
                   removed=[], narrowed={2: ["Unknown[dispatch]"]}, proposals={}, after=0),
         future=(rd(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m", "native:strlen"])), 1)),
    dict(id="q16c_narrow_keeps_reason", rep=rd(F("dao.b", ["Fs"], "hb")),
         pol=["deny Fs Rand dao", "accept dao.a Fs Rand for deny Fs Rand dao because known"],
         args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs Rand dao", "accept dao.a Fs for deny Fs Rand dao because known",
                                 "accept dao.b Fs for deny Fs Rand dao because " + REASON],
                   removed=[], narrowed={2: ["Fs"]}, proposals={}, created=["dao.b"], after=0)),
    dict(id="q17_adopt_row_class", dia=1, rep=rd(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m"])),
         pol=["deny Unknown[dispatch,native] dao"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Unknown[dispatch,native] dao",
                                 "accept dao.c Unknown[dispatch] for deny Unknown[dispatch,native] dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.c"], after=0),
         future=(rd(F("dao.c", ["Unknown"], "hc", unknownWhy=["dispatch:dao.I.m", "native:strlen"])), 1)),
    dict(id="q18_adopt_two_lines", rep=rd(), pol=["deny Fs dao", "deny Fs"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao", "deny Fs", "accept dao.a Fs for deny Fs dao because " + REASON,
                                 "accept dao.a Fs for deny Fs because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a", "dao.a"], after=0)),
    dict(id="q19_stale_zeromatch", rep=rd(), pol=["deny Fs daoz", "accept dao.a Fs for deny Fs daoz because x"], args=[],
         want=dict(exit=0, text=["deny Fs daoz"], removed=[2], narrowed={}, proposals={}, after=0)),
    dict(id="q20_strict", rep=rd(), pol=["deny Fs dao", A_DENY], args=["--strict"], want=dict(exit=2)),
    # ---- round 2 (FABLE-REVIEW-accepts §3) ------------------------------------------------------------
    dict(id="q22_two_entries_one_stale", dia=1, rep=rd(),
         pol=["deny Fs dao", A_DENY, "accept dao.a Clock for deny Fs dao because y"], args=[],
         want=dict(exit=0, text=["deny Fs dao", A_DENY], removed=[3], narrowed={}, proposals={}, after=0)),
    dict(id="q23_adopt_beside_forbid", rep=rd(F("dao.b", ["Fs"], "hb")),
         pol=["deny Fs dao", "forbid dao -> infra", "accept dao.a for forbid dao -> infra because x"],
         args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao", "forbid dao -> infra", "accept dao.a for forbid dao -> infra because x",
                                 "accept dao.a Fs for deny Fs dao because " + REASON,
                                 "accept dao.b Fs for deny Fs dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a", "dao.b"], after=2, unjudged=[3])),
    dict(id="q24_adopt_pure", rep=rd(), pol=["pure dao"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["pure dao", "accept dao.a Fs for pure dao because " + REASON,
                                 "accept dao.k Clock for pure dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a", "dao.k"], after=0)),
    dict(id="q25_adopt_identical_rules", rep=rd(), pol=["deny Fs dao", "deny  Fs dao"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao", "deny  Fs dao", "accept dao.a Fs for deny Fs dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.a"], after=0)),
    dict(id="q26_crlf", rep=rd(drop=("dao.a",)), pol=["deny Fs dao\r", A_DENY + "\r", "# note\r"], args=[],
         want=dict(exit=0, text=["deny Fs dao\r", "# note\r"], removed=[2], narrowed={}, proposals={}, after=0)),
    dict(id="q28_empty_policy", rep=rd(), pol=[], args=[],
         want=dict(exit=2, stderr_re=r"(?i)redirect|truncat")),
    dict(id="q29_out_of_scope", rep=dict(rd(F("dao.b", ["Fs"], "hb")), outOfScope=[{"fn": "dao.x", "path": "src/x", "effects": ["Fs"], "class": "excluded", "reason": "excluded by config"}]), pol=["deny Fs dao", A_DENY], args=[], want=dict(exit=2)),
    # the cross-module (hash, fn) twin under --adopt: a DISCLOSED residual, measured (not an over-accept detector) —
    # adopt over module A alone, then gate module B alone, whose same-named unit is accepted on A's line
    dict(id="q30_twin_across_runs", rep=rd(F("dao.t", ["Fs"], "ht1"), drop=("dao.a",)), pol=["deny Fs dao"],
         args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao", "accept dao.t Fs for deny Fs dao because " + REASON],
                   removed=[], narrowed={}, proposals={}, created=["dao.t"], after=0),
         future=(rd(F("dao.t", ["Fs"], "ht2"), drop=("dao.a",)), 0)),
    # ---- round 3 (the accepts follow-up lane, 2026-11-03) ---------------------------------------------
    # The SOLE refusal: an unevaluated `forbid` and nothing established. The gate exits 2 with the refusal document, so
    # the verb exits 2 with no proposal (§6.2 "When it answers"); q13/q23 above pin the other half, the same rule beside
    # an exit-1 verdict, where the verb answers and lists the entry as `unjudged`.
    dict(id="q31_sole_refusal", rep=rd(drop=("dao.a",)),
         pol=["deny Fs dao", "forbid dao -> infra", "accept dao.a for forbid dao -> infra because x"], args=[],
         want=dict(exit=2)),
    dict(id="q31b_sole_refusal_narrowable", dia=1, rep=rd(),
         pol=["deny Fs Rand dao", "accept dao.a Fs Rand for deny Fs Rand dao because x", "forbid dao -> infra"], args=[],
         want=dict(exit=2)),
    # A lone CR ends a line (the gate's numbering): the `accept` is line 2, stale, and deleted WITH its terminator —
    # the surviving line keeps the CR it was written with.
    dict(id="q32_lone_cr", dia=1, rep=rd(drop=("dao.a",)),
         pol=["deny Fs dao", "accept dao.a Fs for deny Fs dao because x"], terms=["\r", "\n"], args=[],
         want=dict(exit=0, text=["deny Fs dao"], terms=["\r"], removed=[2], narrowed={}, proposals={}, after=0)),
    # An `Unknown` row with no reason class (a report whose `inferred` holds Unknown that no `direct` accounts for):
    # no filter covers it, so the entry is exceeded and stays red; the verb proposes nothing and adopts nothing.
    dict(id="q33_classless_unknown", rep=rd(dict(F("dao.c", ["Unknown"], "hc"), direct=[]), drop=("dao.a",)),
         pol=["deny Unknown dao", "accept dao.c Unknown[dispatch] for deny Unknown dao because x"], args=[],
         want=dict(exit=0, text=["deny Unknown dao", "accept dao.c Unknown[dispatch] for deny Unknown dao because x"],
                   removed=[], narrowed={}, proposals={}, after=1, unnamed=[])),
    dict(id="q33b_classless_unknown_adopt", rep=rd(dict(F("dao.c", ["Unknown"], "hc"), direct=[]), drop=("dao.a",)),
         pol=["deny Unknown dao"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Unknown dao"], removed=[], narrowed={}, proposals={}, created=[], after=1,
                   unnamed=[])),
    # `--adopt` writes no line for a fn holding whitespace or `#` — on EVERY engine, so a single-engine run (swift,
    # which has no nested unit for q11) still calibrates `adoptpositional`.
    dict(id="q11b_adopt_unwritable_fn", rep=rd(F("dao.w x", ["Fs"], "hw"), F("dao.h#z", ["Fs"], "hh"), drop=("dao.a",)),
         pol=["deny Fs dao"], args=["--adopt", "--because", REASON],
         want=dict(exit=0, text=["deny Fs dao"], removed=[], narrowed={}, proposals={}, created=[], after=1,
                   unnamed=[])),
]
DIAMONDS = [r["id"] for r in ROWS if r.get("dia")]


# =====================================================================================================
# the REFERENCE MODEL of the verb — and its MUTANTS
# =====================================================================================================
def parse_entry(line):
    """An `accept` line the gate did NOT ignore -> (fn, concrete set, Unknown filter set|None, rule tokens,
    reason tokens). The gate already applied the clause's checks; this only splits the fields."""
    t = A.lex(line)
    fn, rest = t[1], t[2:]
    i = rest.index("for")
    effs, after = rest[:i], rest[i + 1:]
    j = after.index("because")
    conc, filt = set(), None
    for e in effs:
        m = re.match(r"^Unknown\[(.*)\]$", e)
        if m:
            filt = set(m.group(1).split(","))
        else:
            conc.add(e)
    return fn, conc, filt, after[:j], after[j + 1:]


def canon(conc, classes):
    """The effect tokens, in Unicode code-point order; an Unknown as `Unknown[<classes, sorted>]`."""
    toks = sorted(conc)
    if classes is not None:
        toks.append("Unknown[" + ",".join(sorted(classes)) + "]")
    return sorted(toks)


def comment_of(line):
    return (" " + line[line.index("#"):]) if "#" in line else ""


def is_mark(line):
    return line.lstrip(" \t").startswith(MARK)


def model(pol, args, gate_in, per_line, units, eng, gate_text, mut=frozenset(), terms=None):
    """-> (rc, plan|None). gate_doc: the ⟨0.41⟩ gate's verdict over the input policy; per_line: {rule line:
    verdict with only that rule (accept lines withheld)}; gate_text(text) -> (rc, doc): the gate over a
    proposed policy text."""
    adopt = "--adopt" in args
    because = args[args.index("--because") + 1] if "--because" in args else None
    if "--strict" in args:
        return 2, None
    if because is not None and not adopt:
        if "refreshbecause" not in mut:
            return 2, None
        adopt = True
    if adopt and because is None:
        if "inventreason" not in mut:
            return 2, None
        because = "adopted"
    if because is not None:
        if "rawreason" in mut:
            rtoks_new = [because.strip()]
        else:
            rtoks_new = because.split()
        if not rtoks_new or (any("#" in x for x in rtoks_new) and "hashreason" not in mut):
            return 2, None
        reason_new = " ".join(rtoks_new)
    else:
        reason_new = None
    if "adoptsilent" in mut and not adopt:
        adopt, reason_new = True, "accepted by refresh"
    rc_in, d = gate_in
    if "answerrefusal" in mut and isinstance(d, dict) and d.get("refused"):
        d = dict(d, refused=False)
        d.setdefault("violations", [])
    if d is None or "violations" not in d or d.get("refused") or (d.get("incomplete") and "incompleteanswer" not in mut):
        return 2, None
    ign = set(A.ignored_lines(d))
    items = d.get("accepted") or []
    rule_tok = {ln: A.lex(pol[ln - 1]) for ln in A.rule_lines(pol)}
    hashes = {}
    for u in units:
        hashes.setdefault(u.get("fn"), set()).add(u.get("hash"))

    def rows_of(lines, fn):
        out = []
        for L in lines:
            for v in (per_line.get(L) or {}).get("violations", []):
                if v.get("fn") == fn:
                    out.append(v)
        return out

    entries = {}                                  # line -> dict
    for L in A.accept_lines(pol):
        if L in ign:
            continue
        fn, conc, filt, rtoks, reason = parse_entry(pol[L - 1])
        lines = [ln for ln, t in rule_tok.items() if t == rtoks]
        own = [i for i in items if i.get("line") == L and "enclosing" not in i]
        status = own[0]["status"] if own else "stale"
        entries[L] = dict(fn=fn, conc=conc, filt=filt, rtoks=rtoks, reason=reason, lines=lines, status=status,
                          items=own)
    removed, narrowed, proposals, created = [], {}, {}, []
    for L, e in sorted(entries.items()):
        rule = " ".join(e["rtoks"])
        why = " ".join(e["reason"]) if not ("reasonrewrite" in mut and reason_new) else reason_new
        if e["status"] == "stale":
            if "noprune" in mut:
                continue
            removed.append(dict(line=L, fn=e["fn"], policyRule=rule, because=" ".join(e["reason"])))
            if "prunebyfn" in mut:
                for L2, e2 in entries.items():
                    if L2 != L and e2["fn"] == e["fn"]:
                        removed.append(dict(line=L2, fn=e2["fn"], policyRule=" ".join(e2["rtoks"]),
                                            because=" ".join(e2["reason"])))
        elif e["status"] == "accepted":
            if "nonarrow" in mut:
                continue
            E = set()
            for i in e["items"]:
                if i.get("status") == "accepted":
                    E |= set(i.get("effects") or [])
            classes = None
            if "Unknown" in E:
                classes = set()
                for v in rows_of(e["lines"], e["fn"]):
                    classes |= set(v.get("reasonClass") or [])
                if not classes:
                    classes = set(e["filt"] or [])
            to = canon(E - {"Unknown"}, classes)
            if set(to) != set(canon(e["conc"], e["filt"])):
                narrowed[L] = dict(line=L, fn=e["fn"], policyRule=rule, because=why,
                                   **{"from": canon(e["conc"], e["filt"]), "to": to},
                                   text=f"accept {e['fn']} {' '.join(to)} for {rule} because {why}" + comment_of(pol[L - 1]))
        elif e["status"] == "exceeded":
            if "prunexceeded" in mut:
                removed.append(dict(line=L, fn=e["fn"], policyRule=rule, because=" ".join(e["reason"])))
                continue
            rows = rows_of(e["lines"], e["fn"])
            E, classes = set(), set()
            for v in rows:
                E |= set(v.get("effects") or [])
                classes |= set(v.get("reasonClass") or [])
            if "Unknown" in E and not classes and "classlessproposal" not in mut:
                continue                         # no class to name: the line stays, nothing is proposed
            prop = canon(E - {"Unknown"}, classes if "Unknown" in E else None)
            adds = sorted(E - {"Unknown"} - e["conc"])
            if "Unknown" in E:
                extra = classes - (e["filt"] or set()) if e["filt"] is not None else classes
                if extra:
                    adds = sorted(adds + ["Unknown[" + ",".join(sorted(extra)) + "]"])
            line = f"accept {e['fn']} {' '.join(prop)} for {rule} because {why}" + comment_of(pol[L - 1])
            proposals[L] = dict(line=L, fn=e["fn"], policyRule=rule, because=why, adds=adds, text=line)
        elif e["status"] == "ambiguous" and "pruneambiguous" in mut:
            removed.append(dict(line=L, fn=e["fn"], policyRule=rule, because=" ".join(e["reason"])))
        elif e["status"] == "unjudged" and "prununjudged" in mut:
            removed.append(dict(line=L, fn=e["fn"], policyRule=rule, because=" ".join(e["reason"])))
    if "pruneignored" in mut:
        for L in A.accept_lines(pol):
            if L in ign:
                removed.append(dict(line=L, fn=A.lex(pol[L - 1])[1], policyRule="", because=""))
    # the REKEY mutant: a stale entry rewritten onto an unaccepted row of the same rule, keeping the old reason
    rekeyed = {}
    if "rekey" in mut:
        for r in list(removed):
            e = entries.get(r["line"])
            if not e or e["status"] != "stale":
                continue
            for v in d["violations"]:
                if v.get("rule") in A.POLICY_CODES and v.get("fn") != e["fn"] and \
                        set(v.get("effects") or []) <= e["conc"] and rows_of(e["lines"], v.get("fn")):
                    rekeyed[r["line"]] = f"accept {v['fn']} {' '.join(canon(e['conc'], e['filt']))} for " \
                                         f"{' '.join(e['rtoks'])} because {' '.join(e['reason'])}"
                    removed.remove(r)
                    break
    if True:                                     # the candidates are computed in both modes: `unnamed`
        seen = set()
        for v in d["violations"]:
            if v.get("rule") not in ("AS-EFF-006", "AS-EFF-009"):
                continue
            fn = v.get("fn")
            prod = sorted(L for L, pd in per_line.items()
                          if any(A.vkey(w) == A.vkey(v) and w.get("hash") == v.get("hash") for w in (pd or {}).get("violations", [])))
            if "adoptdedup" in mut:
                prod = prod[:1]
            for L in prod:
                named = [e for e in entries.values() if e["fn"] == fn and L in e["lines"]]
                if "adoptexceeded" in mut:
                    named = [e for e in named if e["status"] != "exceeded"]
                key = (L if "adoptdupe" in mut else tuple(rule_tok[L]), fn)
                if named or key in seen:
                    continue
                if len(hashes.get(fn, ())) > 1 and "adopttwins" not in mut:
                    continue
                if (A.positional(eng, fn) or re.search(r"[#\s]", fn)) and "adoptpositional" not in mut:
                    continue
                effs = set(v.get("effects") or [])
                classes = None
                if "Unknown" in effs:
                    classes = set(v.get("reasonClass") or [])
                    if "adoptwideclass" in mut:
                        m = re.search(r"Unknown\[([^\]]*)\]", pol[L - 1])
                        classes = set(m.group(1).split(",")) if m else classes
                    if not classes and "classlessadopt" not in mut:
                        continue
                toks = canon(effs - {"Unknown"}, classes)
                rule = " ".join(rule_tok[L])
                seen.add(key)
                created.append(dict(fn=fn, hash=v.get("hash"), policyRule=rule, because=reason_new, effects=toks,
                                    text=f"accept {fn} {' '.join(toks)} for {rule} because {reason_new}", _line=L))
        created.sort(key=lambda c: (c["_line"], c["fn"]))
    unnamed = [dict(fn=c["fn"], policyRule=c["policyRule"], effects=c["effects"], **({"hash": c["hash"]} if c.get("hash") else {}))
               for c in created]
    if not adopt:
        created = []
    # ---- the proposed text --------------------------------------------------------------------------
    tl = list(terms or []) + ["\n"] * (len(pol) - len(terms or []))
    src = list(zip(pol, tl))
    if "lfonly" in mut:                          # a reader that numbers lines at LF alone: a lone CR stays inside its line
        src = [(l, "\n") for l in join_terms(pol, terms).split("\n")[:-1]]
    out = []                                     # (line, terminator)
    gone = {r["line"] for r in removed}
    for idx, (ln, tm) in enumerate(src, 1):
        if is_mark(ln) and "keepmarkers" not in mut:
            continue
        if idx in gone:
            continue
        if idx in rekeyed:
            out.append((rekeyed[idx], tm)); continue
        if idx in narrowed:
            out.append((narrowed[idx]["text"], tm)); continue
        if idx in proposals and "widen" in mut:
            out.append((proposals[idx]["text"], tm)); continue
        out.append((ln, tm))
        if idx in proposals:
            p = proposals[idx]
            if "appendwording" in mut:
                out.append((f"{MARK} exceeded (adds {' '.join(p['adds'])}): {p['text']}", "\n"))
            else:
                out.append((f"{MARK} exceeded (adds {' '.join(p['adds'])}) — REPLACE the line above with: {p['text']}", "\n"))
    text = "".join(l + t for l, t in out)
    if created:
        if text and not text.endswith("\n"):
            text += "\n"
        text += "".join(c["text"] + "\n" for c in created)
    for c in created:
        c.pop("_line", None)
    rc2, d2 = gate_text(text)
    ref = d if "afterlie" in mut else d2
    after = dict(exit=(rc_in if "afterlie" in mut else rc2),
                 violations=len((ref or {}).get("violations") or []),
                 accepted=sum(1 for i in (ref or {}).get("accepted") or [] if i.get("status") == "accepted"))
    plan = dict(mode="adopt" if adopt else "refresh", text=text,
                removed=sorted(removed, key=lambda r: r["line"]),
                narrowed=[narrowed[k] for k in sorted(narrowed)],
                proposals=[proposals[k] for k in sorted(proposals)], after=after)
    if adopt:
        plan["created"] = [{k: v for k, v in c.items() if v is not None} for c in created]
    if "nounnamed" not in mut:
        plan["unnamed"] = unnamed
    if "nounjudged" not in mut:
        plan["unjudged"] = [dict(line=L, fn=e["fn"], policyRule=" ".join(e["rtoks"]))
                            for L, e in sorted(entries.items()) if e["status"] == "unjudged"]
    plan["ignored"] = [dict(line=L) for L in A.accept_lines(pol) if L in ign]
    return 0, plan


MUTANTS = {
    "adoptsilent": "refresh writes an accept line for every unaccepted violation (a new violation silently accepted)",
    "refreshbecause": "`--because` honoured without `--adopt` — a reason supplied turns a refresh into an adoption",
    "widen": "an exceeded entry rewritten in place to the wider set instead of PROPOSED in a comment",
    "rekey": "a stale entry re-keyed onto an unaccepted row of the same rule, carrying the old reason",
    "adoptexceeded": "`--adopt` covers an exceeded row with a second line (a widening nobody asked for)",
    "adoptwideclass": "`--adopt` writes the RULE's Unknown filter instead of the row's classes (pre-accepts a new class)",
    "inventreason": "`--adopt` without `--because` writes a reason the engine composed",
    "hashreason": "a `#` in `--because` honoured — the comment rule then cuts the reason the operator wrote",
    "rawreason": "the reason written raw instead of as its tokens single-spaced",
    "noprune": "a stale entry kept",
    "nonarrow": "an accepted entry wider than its rows kept pre-signed for an effect (or class) the fn no longer has",
    "prunexceeded": "an exceeded entry deleted (its reason lost, the known violation forgotten)",
    "pruneambiguous": "an ambiguous entry deleted",
    "prununjudged": "an unjudged entry deleted (a `forbid` entry pruned on the route that cannot evaluate it)",
    "pruneignored": "a malformed (ignored) accept line deleted instead of left for the operator",
    "incompleteanswer": "answers over an incomplete analysis (entries for unread code look stale and are pruned)",
    "adopttwins": "`--adopt` writes a line for a (hash, fn) twin (it can only be ambiguous)",
    "adoptpositional": "`--adopt` writes a line for a positional or unwritable fn",
    "adoptdedup": "`--adopt` writes one line per ROW, not one per producing rule line",
    "keepmarkers": "the verb's own earlier comments kept (a second run is not idempotent)",
    "reasonrewrite": "a narrowed or proposed line carries the `--because` reason instead of its own",
    "afterlie": "`after` reports the input policy's verdict, not the proposed text's",
    "prunebyfn": "every entry on a fn deleted once one of them is stale (the accepted sibling lost)",
    "adoptdupe": "`--adopt` writes one line per producing LINE even where two rule lines carry identical tokens",
    "appendwording": "the exceeded proposal worded as an ADDITIONAL line, so taking it leaves the old line stale (a second red cycle)",
    "nounnamed": "the plan omits `unnamed` — the reviewer cannot see what `--adopt` would write",
    "answerrefusal": "the verb answers over a SOLE refusal (the gate's refusal document claims nothing about violations, yet entries are pruned and narrowed beside it)",
    "lfonly": "lines numbered at LF alone — a lone CR stays inside its line, so the entry on the next line is never seen",
    "classlessproposal": "an exceeded entry on an Unknown row with no reason class proposed as `Unknown[]` (a line the gate does not honour: a second red run)",
    "classlessadopt": "`--adopt` writes `Unknown[]` for an Unknown row with no reason class",
    "nounjudged": "the plan omits `unjudged` — an entry this route cannot judge reads as fresh",
}


# =====================================================================================================
# the judge
# =====================================================================================================
def spell(x, eng):
    return A.spell(x, eng)


def acc_set(doc):
    return {(i.get("fn"), i.get("enclosing")) for i in (doc or {}).get("accepted") or [] if i.get("status") == "accepted"}


def take(text):
    """Do what each `# candor-accepts: exceeded` comment SAYS: replace the line above (or, worded as an extra line,
    uncomment it). The operator's one edit; the result is gated to see whether it reaches green."""
    lines, out = text.split("\n"), []
    for ln in lines:
        if is_mark(ln) and " — REPLACE the line above with: " in ln:
            if out:
                out[-1] = ln.split(" — REPLACE the line above with: ", 1)[1]
            continue
        if is_mark(ln) and "exceeded" in ln and ": accept " in ln:
            out.append("accept " + ln.split(": accept ", 1)[1]); continue
        out.append(ln)
    return "\n".join(out)


def judge(row, eng, rc, plan, gate_in, gate_out, gate_future=None, gate_take=None):
    """-> list of problems (empty = PASS). gate_in: (rc, doc) over the input policy; gate_out: (rc, doc) over
    plan['text'] (None when the verb refused)."""
    w = row["want"]
    bad = []
    if rc != w["exit"]:
        bad.append(f"exit {rc}, want {w['exit']}")
    if w["exit"] == 2:
        if plan is not None and "text" in plan:
            bad.append("a refusal carried a proposed policy")
        return bad
    if not isinstance(plan, dict):
        return bad + ["no plan document"]
    wt = list(w.get("terms") or []) + ["\n"] * (len(w["text"]) - len(w.get("terms") or []))
    want_text = "".join(spell(x, eng) + t for x, t in zip(w["text"], wt))
    if plan.get("text") != want_text:
        bad.append(f"proposed text {plan.get('text')!r}, want {want_text!r}")
    adopt = "--adopt" in row["args"]
    if plan.get("mode") != ("adopt" if adopt else "refresh"):
        bad.append(f"mode {plan.get('mode')!r}")
    got_rm = [r.get("line") for r in plan.get("removed") or []]
    if got_rm != w["removed"]:
        bad.append(f"removed lines {got_rm}, want {w['removed']}")
    got_nw = {n.get("line"): n.get("to") for n in plan.get("narrowed") or []}
    if got_nw != w["narrowed"]:
        bad.append(f"narrowed {got_nw}, want {w['narrowed']}")
    got_pr = {p.get("line"): p.get("adds") for p in plan.get("proposals") or []}
    if got_pr != w["proposals"]:
        bad.append(f"proposals {got_pr}, want {w['proposals']}")
    pol = [spell(x, eng) for x in row["pol"]]
    for lst in ("removed", "narrowed", "proposals"):                 # every existing reason is preserved
        for it in plan.get(lst) or []:
            L = it.get("line")
            toks = A.lex(pol[L - 1]) if isinstance(L, int) and 1 <= L <= len(pol) else []
            if "because" in toks:
                orig = " ".join(toks[toks.index("because") + 1:])
                if it.get("because") != orig:
                    bad.append(f"{lst} line {L} carries reason {it.get('because')!r}, the line's own is {orig!r}")
    if adopt:
        got_cr = [c.get("fn") for c in plan.get("created") or []]
        if got_cr != [spell(x, eng) for x in w.get("created", [])]:
            bad.append(f"created {got_cr}, want {w.get('created')}")
    elif "created" in plan and plan["created"]:
        bad.append(f"refresh mode created {len(plan['created'])} line(s)")
    rc2, d2 = gate_out
    if rc2 != w["after"]:
        bad.append(f"the gate over the proposed text exits {rc2}, want {w['after']}")
    a = plan.get("after") or {}
    real = dict(exit=rc2, violations=len((d2 or {}).get("violations") or []),
                accepted=sum(1 for i in (d2 or {}).get("accepted") or [] if i.get("status") == "accepted"))
    if a != real:
        bad.append(f"`after` {a}, the gate over the proposed text says {real}")
    if row.get("future") and gate_future is not None and gate_future[0] != row["future"][1]:
        bad.append(f"LATER REPORT: the gate over the proposed text and the row's later report exits {gate_future[0]}, "
                   f"want {row['future'][1]}" + (" — a LATENT OVER-ACCEPT" if row["future"][1] == 1 else ""))
    if "take" in row and gate_take is not None and gate_take[0] != row["take"]:
        bad.append(f"TAKING THE PROPOSAL (one edit, as its comment says) leaves the gate at exit {gate_take[0]}, "
                   f"want {row['take']} — a second red cycle")
    for k in ("unnamed",):
        if k in w and [i.get("fn") for i in plan.get(k) or []] != [spell(x, eng) for x in w[k]] or (k in w and k not in plan):
            bad.append(f"`{k}` {[i.get('fn') for i in plan.get(k) or []] if k in plan else 'ABSENT'}, want {w[k]}")
    for k in ("unjudged", "ignored"):
        if k in w and (k not in plan or [i.get("line") for i in plan.get(k) or []] != w[k]):
            bad.append(f"`{k}` {[i.get('line') for i in plan.get(k) or []] if k in plan else 'ABSENT'}, want {w[k]}")
    # THE PROPERTY — judged by the engine's own gate
    rc1, d1 = gate_in
    a1, a2 = acc_set(d1), acc_set(d2)
    if adopt:
        cr = {spell(x, eng) for x in w.get("created", [])}
        extra = {x for x in a2 - a1 if not (x[0] in cr and x[1] is None) and x[1] not in cr}
        if extra:
            bad.append(f"OVER-ACCEPT: the proposed policy accepts {sorted(extra, key=str)}, which no created line names")
    else:
        if a2 != a1:
            bad.append(f"OVER-ACCEPT/LOSS: accepted {sorted(a2, key=str)} over the proposed text, {sorted(a1, key=str)} over the input")
        v1 = [v for v in (A.vset(d1) or []) if v[0] != "AS-EFF-012"]
        if A.vset(d2) != v1:
            bad.append(f"violations over the proposed text {A.vset(d2)}, want the input's minus AS-EFF-012 {v1}")
    return bad


# =====================================================================================================
# driver
# =====================================================================================================
def verb_cmd(eng, loc, pol, args, json_out=True):
    c = A.gate_cmd(eng, loc, pol)
    i = c.index("gate")
    return c[:i] + ["accepts"] + c[i + 1:] + (["--json"] if json_out else []) + list(args)


def run_stdout(cmd, cwd):
    """STDOUT alone (A.run merges the streams): without --json the proposed file IS stdout."""
    env = {k: v for k, v in os.environ.items() if k not in ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY",
                                                             "CANDOR_BASELINE", "CANDOR_UNKNOWN_RATCHET")}
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
    return r.returncode, r.stdout.decode(errors="replace")


def join_terms(lines, terms=None):
    """The file's bytes: each logical line then its terminator (default LF). A row's `terms` gives the ones that are not."""
    t = list(terms or []) + ["\n"] * (len(lines) - len(terms or []))
    return "".join(l + x for l, x in zip(lines, t))


def sha(p):
    with open(p, "rb") as fh:
        return fh.read()


class Ctx:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    def path(self, tag):
        self.n += 1
        return os.path.join(self.ws, f"{self.n:04d}-{tag}")


def gate_text_fn(C, eng, loc):
    def g(text):
        p = C.path("prop.pol")
        with open(p, "w") as fh:
            fh.write(text)
        rc, doc, _ = A.gate(eng, loc, p, C.path("gp.json"))
        return rc, doc
    return g


def collect(C, eng, row, calib):
    pol = [spell(x, eng) for x in row["pol"]]
    d = os.path.join(C.ws, "rep", eng, row["id"])
    loc = G.write_report(d, eng, A.rep_of(row, eng))
    p = C.path("pol")
    A.write(p, join_terms(pol, row.get("terms")))
    before = sha(p)
    cwd = C.path("cwd")
    os.makedirs(cwd)
    rc, out = A.run(verb_cmd(eng, loc, p, row["args"]), cwd=cwd)
    plan = A.first_json(out)
    rct, outt = run_stdout(verb_cmd(eng, loc, p, row["args"], json_out=False), cwd)
    gin = A.gate(eng, loc, p, C.path("gi.json"))[:2]
    res = dict(pol=pol, loc=loc, polpath=p, obs=(rc, plan, out), text_run=(rct, outt), unchanged=(sha(p) == before), gin=gin)
    res["cwd_clean"] = not os.listdir(cwd)
    floc = None
    if row.get("future"):
        floc = G.write_report(os.path.join(C.ws, "fut", eng, row["id"]), eng, row["future"][0])
        res["gate_future"] = gate_text_fn(C, eng, floc)
    if isinstance(plan, dict) and isinstance(plan.get("text"), str):
        res["gout"] = gate_text_fn(C, eng, loc)(plan["text"])
        if floc:
            res["gfut"] = res["gate_future"](plan["text"])
        if "take" in row:
            res["gtake"] = gate_text_fn(C, eng, loc)(take(plan["text"]))
    if calib:
        per = {}
        for L in A.rule_lines(pol):
            pl = C.path("pl")
            A.write(pl, "\n".join(A.commented(pol, keep={L})) + "\n")
            per[L] = A.gate(eng, loc, pl, C.path("gl.json"))[1]
        res["per_line"] = per
        res["units"] = A.rep_of(row, eng)["functions"]
        res["gate_text"] = gate_text_fn(C, eng, loc)
    return res


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    fault = os.environ.get("CANDOR_PROBE_FAULT") == "1"
    ws = tempfile.mkdtemp(prefix="candor-p106-")
    C = Ctx(ws)
    wrong = 0
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in G.ENGINES if G.installed(e) and not G.alive(e)]
        print(f"  engines present: {', '.join(engines) or '(none)'}; {len(ROWS)} rows, {len(DIAMONDS)} over-accept detectors")
        if broken:
            print(f"  FAIL: installed but not responding: {', '.join(broken)} — HARNESS/INSTALL, not candor")
            wrong += 1
        if not engines:
            print("  FAIL: no engine present"); return 1
        data = {}
        for eng in engines:
            for row in ROWS:
                if row.get("only") and eng not in row["only"]:
                    continue
                data[(eng, row["id"])] = collect(C, eng, row, calib=True)
        # the calibration engine: the first that implements the ⟨0.41⟩ GATE (r02 shape: q01's verdict carries `accepted`)
        gate41 = [e for e in engines if isinstance(data[(e, "q01_fresh")]["gin"][1], dict)
                  and "accepted" in data[(e, "q01_fresh")]["gin"][1]]
        calib = ("rust" if "rust" in gate41 else (gate41[0] if gate41 else None))
        # ---- 1. probe, then score --------------------------------------------------------------------
        for eng in engines:
            rc, plan, _ = data[(eng, "q01_fresh")]["obs"]
            implementing = rc == 0 and isinstance(plan, dict) and isinstance(plan.get("text"), str)
            if fault:
                print(f"  PROBE: CANDOR_PROBE_FAULT — {eng}'s q01 policy bytes reported as rewritten")
            cells = [r for r in ROWS if (eng, r["id"]) in data]
            bad = []
            for row in cells:
                x = data[(eng, row["id"])]
                unchanged = x["unchanged"] and not (fault and row["id"] == "q01_fresh")
                if not unchanged:
                    bad.append(f"{row['id']}: the policy file's bytes CHANGED — the verb has no in-place mode")
                rc, plan, out = x["obs"]
                if implementing:
                    if not x["cwd_clean"]:
                        bad.append(f"{row['id']}: the verb wrote a file into its working directory — it writes none")
                    if row["want"].get("stderr_re") and not re.search(row["want"]["stderr_re"], out):
                        bad.append(f"{row['id']}: the refusal does not name its remedy (want /{row['want']['stderr_re']}/)")
                    for p in judge(row, eng, rc, plan, x["gin"], x.get("gout", (None, None)), x.get("gfut"), x.get("gtake")):
                        bad.append(f"{row['id']}{' ◆' if row.get('dia') else ''}: {p}")
                    rct, outt = x["text_run"]
                    if row["want"]["exit"] == 0 and isinstance(plan, dict) and (rct != 0 or outt != plan.get("text")):
                        bad.append(f"{row['id']}: without --json, stdout is not the plan's `text` byte for byte (exit {rct})")
                else:
                    if rc == 0:
                        bad.append(f"{row['id']} (pre-rung): an unknown verb answered exit 0")
                    if isinstance(plan, dict) and "text" in plan:
                        bad.append(f"{row['id']} (pre-rung): a plan document without the probe passing")
            if implementing:
                # `accept` (the line kind) typed as a verb: a usage error that NAMES `accepts`, never an answer
                x = data[(eng, "q01_fresh")]
                c = verb_cmd(eng, x["loc"], x["polpath"], [])
                c[c.index("accepts")] = "accept"
                trc, tout = A.run(c, cwd=tempfile.mkdtemp(dir=ws))
                if trc != 2 or "accepts" not in tout:
                    bad.append(f"`accept` as a verb exits {trc}" + ("" if "accepts" in tout else " and does not name `accepts`"))
                print(f"  {eng:6s} IMPLEMENTS ⟨0.41⟩ accepts: " + (f"OK — {len(cells)} row(s)" if not bad else "DIVERGE"))
            else:
                # `SKIP —` is the token skip_ratchet.py counts (skip-baseline.json).
                # One line, short enough that the ratchet's 120-character key ends before anything per-engine.
                print(f"  {eng:6s} SKIP — does not yet implement ⟨0.41⟩ `accepts` (reference-led, probed)")
                print(f"  {eng:6s} pre-rung posture on {len(cells)} row(s): "
                      + ("OK, unknown verb refused, policy bytes unchanged" if not bad else "DIVERGE"))
            for b in bad:
                print(f"    {eng:6s} {b}")
            wrong += len(bad)
        # ---- 2. calibration ---------------------------------------------------------------------------
        if calib is None:
            print("  CALIBRATION FAIL — no engine here implements the ⟨0.41⟩ gate, so the reference model has no data")
            wrong += 1
        else:
            caught = {r["id"]: [] for r in ROWS}
            model_bad, hits = [], {m: 0 for m in MUTANTS}
            rows = [r for r in ROWS if (calib, r["id"]) in data]
            for row in rows:
                x = data[(calib, row["id"])]

                def run_model(mut):
                    rc, plan = model(x["pol"], row["args"], x["gin"], x["per_line"], x["units"], calib,
                                     x["gate_text"], mut, row.get("terms"))
                    gout = x["gate_text"](plan["text"]) if plan else (None, None)
                    gfut = x["gate_future"](plan["text"]) if plan and "gate_future" in x else None
                    gtk = x["gate_text"](take(plan["text"])) if plan and "take" in row else None
                    return judge(row, calib, rc, plan, x["gin"], gout, gfut, gtk)
                for p in run_model(frozenset()):
                    model_bad.append(f"{calib} {row['id']}: {p}")
                for m in MUTANTS:
                    if run_model(frozenset([m])):
                        caught[row["id"]].append(m)
                        hits[m] += 1
            if model_bad:
                print("  CALIBRATION FAIL — the reference model of the clause does not meet these expectations "
                      "(an expectation or the model is wrong; neither is a finding about an engine):")
                for b in model_bad:
                    print(f"    {b}")
                wrong += len(model_bad)
            dead = [m for m, n in hits.items() if n == 0]
            cal = {r["id"] for r in rows}
            uncaught = [d for d in DIAMONDS if d in cal and not caught[d]]
            for m in dead:
                print(f"  CALIBRATION FAIL — mutant `{m}` ({MUTANTS[m]}) fails NO row: the part cannot see it")
            for d in uncaught:
                print(f"  CALIBRATION FAIL — over-accept row {d} is failed by NO mutant: VACUOUS")
            wrong += len(dead) + len(uncaught)
            if not model_bad and not dead and not uncaught:
                print(f"  calibration ({calib}'s gate): the reference model passes all {len(rows)} row(s); each of "
                      f"{len(MUTANTS)} mutants fails ≥1 row; each of {len([d for d in DIAMONDS if d in cal])} ◆ rows "
                      f"is failed by ≥1 mutant")
                for d in DIAMONDS:
                    if d in cal:
                        print(f"    ◆ {d:28s} caught by: {', '.join(caught[d])}")
        print("ACCEPTS: OK — every pre-rung engine refuses the verb and leaves the policy untouched; the model passes; "
              "every over-accept row can fail" if not wrong else f"ACCEPTS: {wrong} cell(s) wrong")
        return 1 if wrong else 0
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)


def selftest():
    """The model and the judge on SYNTHETIC ⟨0.41⟩ documents: no engine. Row q02 (one stale entry): the model
    deletes it, and a plan that keeps it is judged a FAILURE."""
    row = next(r for r in ROWS if r["id"] == "q02_stale")
    d = {"ok": False, "violations": [{"rule": "AS-EFF-012", "fn": "dao.a", "effects": ["Fs"]}], "accepted": []}
    clean = (0, {"ok": True, "violations": []})
    rc, plan = model(row["pol"], row["args"], (1, d), {1: {"violations": []}}, [], "rust", lambda t: clean)
    p1 = judge(row, "rust", rc, plan, (1, d), clean)
    kept = dict(plan, text="\n".join(row["pol"]) + "\n", removed=[])
    p2 = judge(row, "rust", 0, kept, (1, d), clean)
    ok = not p1 and bool(p2)
    print(f"gen_accept_refresh selftest: model on q02 {'PASS' if not p1 else p1}; a plan that keeps the stale line "
          f"{'FAILS' if p2 else 'PASSES — the judge is blind'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
