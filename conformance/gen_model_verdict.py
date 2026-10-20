#!/usr/bin/env python3
"""
PART 97 — EACH ENGINE'S `gate --report` VERDICT AGREES WITH THE REFERENCE MODEL (LEAN-CHECKER-PLAN.md Phase 0)

WHAT IT CHECKS
--------------
PART 23 proves the model (`reference/policy_model.py`) is internally monotone. It judges no engine. This
part feeds each engine signatures the model has ALREADY judged, through the one route SPEC §3.1 made a
pure function of the report and the policy (`gate --report`), and compares the verdict.

Four arms:

  A  THE LATTICE. One synthetic report, one leaf function per REACHABLE signature with |S| <= 2 and
     |D| <= 2 — the same slice `lean/` `emitRows` emits (1474 signatures; 1254 reachable once `Llm`
     without `Net` is removed, `policy_model.is_reachable`). One `gate --report` per (verb, effect, C):
     `pure`, `deny e` x 11, `deny e Unknown` x 11 (bare), `deny e Unknown[<all six classes spelled out>]`
     x 11, `deny e Unknown[c]` x 66 — 100 runs per engine. Per run: the SET of violating `fn` equals the
     model's REJECT set; |violations| equals the model's REJECT count (no duplicate rows); exit is 1 iff
     that count is > 0 and 0 otherwise, and NEVER 2 — every lattice row is answerable from its entry.

     WHY 100 RUNS OVER 1254 FUNCTIONS IS SUFFICIENT AND NOT A SAMPLE. Every verb here is a POINTWISE
     predicate of one entry's (S, D): a leaf with `direct == inferred` and no `calls` gives the gate
     nothing to combine, so the engine's verdict on one function cannot depend on another function in
     the report. Separate functions in one report are therefore separate trials. The effect axis is
     covered at |S| <= 2 (every effect alone and in every pair, so "fires on the wrong effect" and
     "fires only when alone" are both visible), and the class axis at every singleton plus the full R.
     What this slice cannot see is a predicate that depends on |S| >= 3 — none of SPEC §4.0's does.
     C = ∅ is omitted: `deny e Unknown[]` is not a model point, and is measured to read as ALL classes
     four-way (unspecified; fail-closed); the model's `deny_unknown(e, ∅)` is `deny e`, already covered.

  B  THE PROJECTION ROWS — the report -> (S, D) layer arm A deliberately bypasses, which is where every
     filed verdict-logic defect actually lived (the 2026-07-27 absence default, SPEC §6.2 CONTRIBUTES):
       B1 the three ⟨0.24⟩ repair rows (`policy_model.repair_reproduces_the_counterexample_correctly`) as a
          MULTI-FUNCTION report WITH `calls`: a reasonless source, a reasoned source, and a caller of each
          and of both. The transitive class set is computed by the model (`contribute_unresolved` +
          componentwise join over `calls`), never written down by hand.
       B2 a `direct:["Unknown"]` entry with NO reason (key absent, and `[]`): must FIRE
          `deny E Unknown[unresolved]` and must NOT fire `deny E Unknown[dispatch]` (SPEC §6.2: it
          CONTRIBUTES `unresolved`, and §3.1: "the rule fires and the answer is certain").
       B3 an INHERITED `Unknown` (`direct: []`), no reason, NO `calls`: a class-scoped deny is
          UNANSWERABLE and MUST be refused (exit 2, SPEC §3.1 ⟨0.24⟩ answerability) — including a list
          naming all six classes (⟨0.40⟩, answered as written); bare `deny E Unknown` and `Unknown[*]` fire
          from the entry alone (exit 1); `deny E` is untouched (exit 0).
  C  THE CLASS MAP, pinned as its own row: one leaf per raw `unknownWhy` token, gated under each of the
     six classes. The oracle is SPEC §6.2's table read as data (prefix -> class, catch-all `unresolved`).
     `indirect:x` is IN the row on purpose: `indirect` is a CLASS name, not a token prefix, so the raw
     token `indirect:x` maps to `unresolved` — a generator that used it as the canonical `indirect` token
     (as the first plan draft did) would manufacture divergences out of the harness.

  D  THE `Net` DESTINATION CLASS (LEAN-CHECKER-PLAN.md Phase 2(a); `policy_model.deny_rule` /
     `answer_absent`, Lean `NetDest.lean`). The first carrier beyond `L`: the per-entry `netClass` set N.
       D1 one report of 369 netClass-WELL-FORMED leaves (reachable |S| <= 2, D in {∅, {dispatch},
          {native}}, N every non-empty class set when Net ∈ S, else the key absent) under 40 WHOLE rules:
          `Net[C]` for each of the 7 non-empty class sets and `Net[*]`, each alone and with `Fs`, `Llm`,
          bare `Unknown` and `Unknown[dispatch]` beside it. Same four assertions as arm A, never exit 2.
       D2 single-function reports whose `Net` entry has NO usable `netClass` (key absent; `[]`, which
          contradicts the §3.1 floor; with `Fs`, with `Llm`, with a reasoned `Unknown`) plus a non-Net
          control, under 20 rules. The model's §3.1 answer per cell: REFUSE -> exit 2, REJECT -> exit 1
          naming the fn (another part of the rule fires from the entry alone), PASS -> exit 0. Under the
          FULL filter `Net[known-telemetry,known-partner,unknown-host]` the model refuses as SPEC's text
          does, although every completion would fire (Lean `refuse_overbroad_when_filter_full`); all four
          engines refuse there too. Those cells pin the RULED text (SPEC §3.1 ⟨0.40⟩, "a filter is
          answered as written", the owner's ruling of 2026-10-11); arm B3 pins the `Unknown` twin.

WHAT IT CANNOT SEE (stated so the green is not read as more): an ABSENT effect — the cardinal sin — and a
fabricated one (LEAN-CHECKER-PLAN.md §0); scope matching (gen_policy_match.py, the POLICY-MATCHING differential, owns it); every
analysis-side, producer-side (the ⟨0.30⟩ peek) and consumer-side (integrations refusal->pass) defect. It
also cannot see a REPORT-WRITING defect on the scan route: `gate --report` reads the report as given, so
whether the report says what the scan gated on is PART 98's question, not this one's.

IT IS SHOWN ABLE TO FAIL ON EVERY RUN, not once by hand — the controls run inside the part:
  model-side  the model with `Db ⊑ₑ Net` reinstated (the historical defect, reference/README.md) is
              compared against each engine's ACTUAL output: it must DIVERGE, and only on Db-bearing rows.
  diff-side   one row's expected verdict flipped: exactly that one row must diverge.
  document    an engine's own `--gate-json` with one violation removed must be caught.
  vacuity     a run over the same report truncated to zero functions must trip the vacuity floor.
  arm D       the model with the destination filter IGNORED (`Net[C]` read as bare `Net`) must diverge on
              D1, and the model reading an absent `netClass` as ∅ (the ⟨0.24⟩ fail-open SPEC §3.1 measured)
              must diverge on D2.
And once by hand against a real engine (recorded in run.sh's PART 97 header): a one-line fault in one
engine's SHARED evaluator, built in a throwaway worktree, turns this part red — for arm D, two ts seeds
(2026-10-11): `classFilterExcludes`'s Net branch returning false moved 30 D1 rules, and the `netClass`-absent
refusal disabled moved 63 D2 cells to exit 0; arms A-C unmoved by either.

USAGE
    python3 gen_model_verdict.py            [--keep]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference"))

import policy_model as M                     # noqa: E402  the oracle
import gen_rung024 as G                      # noqa: E402  engine presence + per-engine report spelling

# THE CONTRACT THIS PART ENFORCES (conformance/clause_check.py proves SPEC.md still says it).
SPEC_CLAUSES = [
    ("§4.0", "| `deny e` | `e ∈ S` |"),
    ("§4.0", "| `deny e Unknown` | `e ∈ S ∨ D ≠ ∅` |"),
    ("§4.0", "| `deny e Unknown[c…]` | `e ∈ S ∨ (D ∩ {c…}) ≠ ∅`"),
    ("§4.0", "`D ≠ ∅` alone is AS-EFF-003 disclosure, not AS-EFF-006"),
    ("§3.1 ⟨0.24⟩", "it reads `S` and `D` from the report as given and applies §6's matching"),
    ("§3.1 ⟨0.24⟩", "a report entry that is **absent** is absent"),
    ("§3.1 ⟨0.24⟩", "if the classes determinable from the entry ALONE already intersect the filter, **the rule FIRES**"),
    ("§3.1 ⟨0.24⟩", "only if it does NOT yet fire, and the missing datum could still make it fire, is the question genuinely unanswerable. **Refuse that.**"),
    ("§6.2", "a raw reason matching no listed prefix maps to `unresolved`"),
    ("§6.2", "A conforming implementation must therefore ADD `unresolved` to the class set of any function carrying an `Unknown` with no reason"),
    # arm D — the Net destination class (LEAN-CHECKER-PLAN.md Phase 2(a); lean/CandorModel/NetDest.lean)
    ("§6.2 ⟨0.21⟩", "denies the `Net` part only for a function whose `Net` reaches a host of one of the listed classes; a concrete effect in the same rule is unaffected"),
    ("§6.2 ⟨0.21⟩", "bare **`Net`** and **`Net[*]`** mean **all destinations**"),
    ("§3.1 ⟨0.24⟩", "**A CLASS-SCOPED `deny` whose scoping datum is an ABSENT OPTIONAL FIELD.**"),
    ("§3.1 ⟨0.24⟩", "`netClass` is emitted for every `Net`-bearing entry and is floored at `unknown-host`"),
    ("§3.1 ⟨0.24⟩", "per-(rule, function) for the scoped case, so a scoped rule whose own matches carry their evidence still evaluates"),
    ("§3.1 ⟨0.40⟩", "a class list spelled out in the policy is a **proper filter even when it names every class in"),
    ("§6.2 ⟨0.40⟩", "**The prefixes are matched without regard to ASCII case**"),
]

E = list(M.E)
R = list(M.R)
# One canonical raw token per class. Each is a LISTED prefix of SPEC §6.2's table for that class, so the
# map is the table's, not this file's. NOT `indirect:x` (a class name, not a prefix -> `unresolved`).
TOKEN = {"reflect": "reflect:x.Y.m", "dispatch": "dispatch:app.T.m", "indirect": "callback:x",
         "native": "native:x", "unresolved": "macro:x", "setup": "missing-config"}
assert set(TOKEN) == set(R), "every model reason needs exactly one canonical token"


def subsets(xs, k):
    return [c for n in range(k + 1) for c in combinations(xs, n)]


def fn_name(S, D):
    s = "_".join(sorted(S)) or "none"
    d = "_".join(sorted(D)) or "none"
    return f"app.L.s_{s}__d_{d}"


def entry(S, D):
    inferred = sorted(S) + (["Unknown"] if D else [])
    e = {"fn": fn_name(S, D), "inferred": inferred, "direct": list(inferred)}
    if D:
        e["unknownWhy"] = [TOKEN[r] for r in sorted(D)]
    return e


def lattice():
    sigs = [M.Sig(S, D) for S in subsets(E, 2) for D in subsets(R, 2)]
    return [s for s in sigs if M.is_reachable(s)], len(sigs)


def envelope(functions):
    return {"candor": {"version": "handwritten", "spec": "0.40"}, "package": "app",
            "analyzed": {"count": len(functions), "digest": "0"}, "functions": functions}


# --------------------------------------------------------------------------------------------------------
# the policy axis
# --------------------------------------------------------------------------------------------------------

def policies():
    """(label, policy text, model predicate). Rules are scopeless: §6.2 'absent scope = the whole unit'."""
    out = [("pure", "pure", M.pure())]
    for e in E:
        out.append((f"deny {e}", f"deny {e}", M.deny(e)))
        out.append((f"deny {e} Unknown", f"deny {e} Unknown", M.deny_unknown(e)))
        out.append((f"deny {e} Unknown[R]", f"deny {e} Unknown[{','.join(R)}]", M.deny_unknown(e, R)))
        for c in R:
            out.append((f"deny {e} Unknown[{c}]", f"deny {e} Unknown[{c}]", M.deny_unknown(e, [c])))
    return out


# --------------------------------------------------------------------------------------------------------
# one engine run
# --------------------------------------------------------------------------------------------------------

def gate_cmd(eng, locator, policy, gate_json):
    if eng == "rust":
        cmd = [G.rust_query(), "gate", "--report", locator, "--policy", policy]
    elif eng == "java":
        cmd = ["java", "-jar", G.java_jar(), "gate", "--report", locator, "--policy", policy]
    elif eng == "ts":
        cmd = ["node", os.path.join(G.ts_root(), "query.mjs"), "gate", "--report", locator, "--policy", policy]
    else:
        cmd = [G.swift_bin(), "gate", "--report", locator, "--policy", policy]
    return cmd + ["--gate-json", gate_json]


def run_gate(eng, locator, policy_text, ws, tag):
    pf = os.path.join(ws, f"pol.{tag}")
    with open(pf, "w") as fh:
        fh.write(policy_text + "\n")
    gj = os.path.join(ws, f"{eng}.{tag}.gate.json")
    if os.path.exists(gj):
        os.remove(gj)                                     # never read a stale document as this run's
    env = {k: v for k, v in os.environ.items() if k not in ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY")}
    r = subprocess.run(gate_cmd(eng, locator, pf, gj), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    doc = None
    if os.path.exists(gj):
        try:
            doc = json.load(open(gj))
        except Exception:
            doc = None
    return r.returncode, doc, r.stderr.decode(errors="replace")[:300]


def judge(rc, doc, want):
    """Compare one run against the model. Returns a list of problems (empty == agrees).

    `want` is the model's REJECT set of `fn`. The four assertions of LEAN-CHECKER-PLAN.md §3 Phase 0."""
    bad = []
    if rc == 2:
        return [f"exit 2 (refused or errored) on a lattice row — every lattice row is answerable from its entry"]
    if doc is None or not isinstance(doc.get("violations", None), list):
        return [f"exit {rc} but no readable --gate-json document with a `violations` array"]
    got_rows = [v.get("fn") for v in doc["violations"]]
    got = set(got_rows)
    if len(got_rows) != len(want):
        bad.append(f"|violations| = {len(got_rows)}, model REJECT count = {len(want)}")
    if len(got_rows) != len(got):
        bad.append(f"duplicate violation rows for one fn ({len(got_rows) - len(got)})")
    want_rc = 1 if want else 0
    if rc != want_rc:
        bad.append(f"exit {rc}, model says {want_rc}")
    extra, missing = sorted(got - want), sorted(want - got)
    if extra:
        bad.append(f"{len(extra)} fn the model PASSES were rejected, e.g. {extra[:3]}")
    if missing:
        bad.append(f"{len(missing)} fn the model REJECTS were passed, e.g. {missing[:3]}")
    return bad


# --------------------------------------------------------------------------------------------------------
# B — projection rows; C — the class map
# --------------------------------------------------------------------------------------------------------

def closure_D(fns):
    """The model's transitive (S, D) for each fn of a multi-function report: `contribute_unresolved` at each
    direct site (§6.2 CONTRIBUTES, gated on a DIRECT Unknown with no reason), then the least fixpoint of the
    componentwise join over `calls` (SPEC §4.0, 'a callee's (S, D) joins into its caller's')."""
    cls = {}
    for f in fns:
        d = set()
        for t in f.get("unknownWhy", []) or []:
            d.add(class_of(t))
        reasonless = "Unknown" in (f.get("direct") or []) and not (f.get("unknownWhy") or [])
        sig = M.contribute_unresolved(M.Sig((), d), reasonless)
        cls[f["fn"]] = set(sig.D)
    calls = {f["fn"]: f.get("calls", []) for f in fns}
    changed = True
    while changed:
        changed = False
        for f, cs in calls.items():
            for c in cs:
                if not cls[c] <= cls[f]:
                    cls[f] |= cls[c]; changed = True
    return cls


# SPEC §6.2's table as data. Prefix forms exactly as the table lists them.
CLASS_PREFIX = [("reflect", ("reflect:", "dynamicMemberLookup")),
                ("dispatch", ("dispatch:", "indy", "ambiguous:")),
                ("indirect", ("callback:", "closure", "task-handoff")),
                ("native", ("native:",)),
                ("unresolved", ("macro:",)),
                ("setup", ("missing-config", "no-tsconfig", "no-node_modules"))]


def class_of(tok):
    low = tok.lower()                                     # §6.2 ⟨0.40⟩: ASCII case-insensitive prefixes
    for c, pfx in CLASS_PREFIX:
        if any(low.startswith(p.lower()) for p in pfx):
            return c
    return "unresolved"                                   # the catch-all


B1 = [  # the ⟨0.24⟩ repair rows, multi-function, WITH calls (no sidecar: the report's own `calls` is the edge set)
    {"fn": "app.P.src_reasonless", "inferred": ["Unknown"], "direct": ["Unknown"]},
    {"fn": "app.P.src_reasonless_empty", "inferred": ["Unknown"], "direct": ["Unknown"], "unknownWhy": []},
    {"fn": "app.P.src_reasoned", "inferred": ["Unknown"], "direct": ["Unknown"], "unknownWhy": ["dispatch:app.Base.run"]},
    {"fn": "app.P.a_reasonless_only", "inferred": ["Unknown"], "direct": [], "calls": ["app.P.src_reasonless"]},
    {"fn": "app.P.b_reasoned_only", "inferred": ["Unknown"], "direct": [], "calls": ["app.P.src_reasoned"]},
    {"fn": "app.P.c_both", "inferred": ["Unknown"], "direct": [],
     "calls": ["app.P.src_reasonless", "app.P.src_reasoned"]},
]
B3 = [{"fn": "app.Q.inherited_no_calls", "inferred": ["Unknown"], "direct": []}]
C_TOKENS = ["reflect:x.Y.m", "dispatch:app.T.m", "ambiguous:x", "callback:x", "native:x", "macro:x",
            "missing-config", "no-tsconfig", "indirect:x", "banana:x",
            # SOUNDNESS R1241 — ONE EMITTED SPELLING PER ALIAS PREFIX. `CLASS_PREFIX` listed every alias and
            # this list exercised none of them, so the arm could not see R1218 (candor-query tested
            # `dynamicmemberlookup` by EQUALITY, while candor-swift emits `dynamicMemberLookup:<Root>.<prop>`).
            # Each token is the spelling a producer actually writes: swift `dynamicMemberLookup:`/`closure`,
            # java `indy`/`task-handoff`, ts `no-node_modules`. CALIBRATED 2026-10-20: the released candor-query
            # 0.40.13 (pre-08a53ef) diverges on `dynamicMemberLookup:Root.p` under [reflect] and [unresolved].
            "dynamicMemberLookup:Root.p", "indy:java.lang.invoke.LambdaMetafactory", "closure:k",
            "task-handoff:Executor.submit", "no-node_modules",
            # §6.2 ⟨0.40⟩ — the prefixes match WITHOUT REGARD TO ASCII CASE (all four engines lowercase first).
            "DynamicMemberLookup:Root.q", "NATIVE:strlen", "Reflect:Method.invoke"]


def c_entries():
    return [{"fn": f"app.C.t{i}", "inferred": ["Unknown"], "direct": ["Unknown"], "unknownWhy": [t]}
            for i, t in enumerate(C_TOKENS)]


# --------------------------------------------------------------------------------------------------------
# D — the Net destination class (Phase 2(a)): the whole-rule `deny` with a `Net[C]` filter, over the
# per-entry `netClass` carrier, and SPEC §3.1's answer when that carrier is absent.
# --------------------------------------------------------------------------------------------------------

NC = list(M.NC)
NC_ABBR = {"known-telemetry": "tel", "known-partner": "par", "unknown-host": "uh"}
D_SIGS_D = [(), ("dispatch",), ("native",)]          # D: none, the class Unknown[dispatch] names, one it does not


def _rule(extra, C):
    """(label, policy text, model rule). `extra` is a plain token or an Unknown part; `C` a class list or '*'."""
    effs, unk = [], None
    if extra in ("Fs", "Llm"):
        effs = [extra]
    elif extra == "Unknown":
        unk = R
    elif extra == "Unknown[dispatch]":
        unk = ["dispatch"]
    net_tok = "Net[*]" if C == "*" else f"Net[{','.join(C)}]"
    pre = f"{extra} " if extra in ("Fs", "Llm") else ""
    post = f" {extra}" if extra and extra.startswith("Unknown") else ""
    text = f"deny {pre}{net_tok}{post}"
    rule = M.deny_rule(effs + ["Net"], None, unk) if C == "*" else M.deny_rule(effs, C, unk)
    # the model-side SEED (controls): the same rule with its destination filter IGNORED
    rule.ignore_filter = M.deny_rule(effs + ["Net"], None, unk)
    return text, rule


def _nc_subsets():
    return [list(c) for c in subsets(NC, 3) if c]


D1_POLICIES = [(_rule(x, C)[0], _rule(x, C)[1]) for C in _nc_subsets() + ["*"]
               for x in (None, "Fs", "Llm", "Unknown", "Unknown[dispatch]")]


def d1_leaves():
    """Every netClass-WELL-FORMED leaf (`policy_model.net_wf`): reachable S with |S| <= 2, D from D_SIGS_D,
    and N every non-empty class set when Net ∈ S, else the key absent. Cached."""
    if getattr(d1_leaves, "_c", None) is None:
        out = []
        for S in subsets(E, 2):
            for D in D_SIGS_D:
                sig = M.Sig(S, D)
                if not M.is_reachable(sig):
                    continue
                for N in (_nc_subsets() if "Net" in S else [[]]):
                    assert M.net_wf(sig, frozenset(N))
                    f = entry(S, D)
                    f["fn"] = fn_name(S, D) + "__n_" + ("_".join(NC_ABBR[c] for c in N) or "none")
                    f["fn"] = f["fn"].replace("app.L.", "app.ND.")
                    if N:
                        f["netClass"] = list(N)
                    out.append((f, (sig, frozenset(N))))
        d1_leaves._c = out
    return d1_leaves._c


# D2: single-function reports whose entry carries `Net` with NO usable `netClass` — the key absent, or `[]`
# (SPEC §3.1: present-and-empty contradicts the producer floor and is read as ABSENT, never as ∅) — plus a
# non-Net control.
D2_LEAVES = [
    ("net_absent",      {"inferred": ["Net"]}),
    ("net_empty",       {"inferred": ["Net"], "netClass": []}),
    ("fs_net_absent",   {"inferred": ["Fs", "Net"]}),
    ("llm_net_absent",  {"inferred": ["Llm", "Net"]}),
    ("net_disp_absent", {"inferred": ["Net", "Unknown"], "unknownWhy": [TOKEN["dispatch"]]}),
    ("fs_absent",       {"inferred": ["Fs"]}),
]
# THE FULL-FILTER CELLS (C == NC) PIN THE RULED TEXT (SPEC §3.1 ⟨0.40⟩ "A FILTER IS ANSWERED AS WRITTEN",
# the owner's ruling of 2026-10-11). Over a `Net` entry with no `netClass`,
# `Net[known-telemetry,known-partner,unknown-host]` is a proper filter and is refused (exit 2), although every
# completion would fire (Lean `refuse_overbroad_when_filter_full`); `Net[*]` is answered. Answering when every
# completion agrees was considered and deferred to a future rung (it ties the answer to vocabulary closure).
D2_POLICIES = [(_rule(x, C)[0], _rule(x, C)[1])
               for C in (["unknown-host"], ["known-telemetry", "known-partner"], NC, "*")
               for x in (None, "Fs", "Llm", "Unknown", "Unknown[dispatch]")]


def _d2_entry(name, spec):
    e = {"fn": f"app.NA.{name}", "inferred": list(spec["inferred"]), "direct": list(spec["inferred"])}
    for k in ("netClass", "unknownWhy"):
        if k in spec:
            e[k] = spec[k]
    return e


def _d2_sig(spec):
    D = [class_of(t) for t in spec.get("unknownWhy", [])]
    return M.Sig([x for x in spec["inferred"] if x != "Unknown"], D)


def d2_answer(key):
    pol_i, name = key
    return M.answer_absent(D2_POLICIES[pol_i][1], _d2_sig(dict(D2_LEAVES)[name]))


def d2_judge(rc, doc, name, answer):
    """One absent-netClass cell against the model's §3.1 answer: refuse -> exit 2; reject -> exit 1 naming
    the fn; pass -> exit 0 with no violation."""
    if answer == "refuse":
        return [] if rc == 2 else [f"exit {rc}, model REFUSES (§3.1: the filter's datum is absent and only it could fire)"]
    want = {f"app.NA.{name}"} if answer == "reject" else set()
    return judge(rc, doc, want)


def arm_d(eng, ws):
    bad = []
    leaves = d1_leaves()
    loc = G.write_report(ws, eng, envelope([f for f, _ in leaves]))
    d1 = []
    n_fire = n_pass = 0
    for i, (text, rule) in enumerate(D1_POLICIES):
        want = {f["fn"] for f, (sig, N) in leaves if rule(sig, N)}
        n_fire += len(want); n_pass += len(leaves) - len(want)
        rc, doc, err = run_gate(eng, loc, text, ws, f"d1_{i}")
        d1.append((rc, doc))
        for p in judge(rc, doc, want):
            bad.append(f"D1 {text}: {p}" + (f" [stderr: {err.strip()[:160]}]" if rc == 2 else ""))
    if not n_fire or not n_pass:
        bad.append(f"D1 VACUOUS: {n_fire} model rejections, {n_pass} passes — the filter is not being exercised")
    d2 = {}
    answers = set()
    for name, spec in D2_LEAVES:
        locn = G.write_report(ws, eng, envelope([_d2_entry(name, spec)]))
        for i, (text, rule) in enumerate(D2_POLICIES):
            a = d2_answer((i, name))
            answers.add(a)
            rc, doc, err = run_gate(eng, locn, text, ws, f"d2_{name}_{i}")
            d2[(i, name)] = (rc, doc)
            for p in d2_judge(rc, doc, name, a):
                bad.append(f"D2 {name} `{text}`: {p}")
    if answers != {"reject", "pass", "refuse"}:
        bad.append(f"D2 VACUOUS: the model's answers over the absent cells were only {sorted(answers)}")
    return bad, (d1, d2)


# --------------------------------------------------------------------------------------------------------

def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    # probe_check.py's fault: delete one violation from the FIRST firing run's real document before it is
    # judged — an engine answer corrupted in the direction this property forbids (a silent pass).
    fault = bool(os.environ.get("CANDOR_PROBE_FAULT"))
    ws = tempfile.mkdtemp(prefix="candor-p97-")
    rc_all = 0
    wrong = 0
    try:
        sigs, total = lattice()
        # DERIVED floor, the PART 23 lesson: from the model's own vocabulary, never a literal.
        n_s = sum(1 for _ in subsets(E, 2)); n_d = sum(1 for _ in subsets(R, 2))
        if total != n_s * n_d or len(sigs) == 0 or len(sigs) == total:
            print(f"  FAIL: lattice slice is {len(sigs)}/{total}, expected {n_s}x{n_d} with co-emission removing some")
            return 1
        fns = [entry(s.S, s.D) for s in sigs]
        assert len({f["fn"] for f in fns}) == len(fns), "fn names must be unique (same-fn entries are UNIONED)"
        rep = envelope(fns)
        pols = policies()
        print(f"  lattice: {len(sigs)} reachable of {total} signatures (|S|<=2 over {len(E)} effects, "
              f"|D|<=2 over {len(R)} reasons); {len(pols)} policies per engine")
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        broken = [e for e in G.ENGINES if G.installed(e) and not G.alive(e)]
        print(f"  engines present: {', '.join(engines) or '(none)'}")
        if broken:
            print(f"  FAIL: installed but not responding: {', '.join(broken)} — HARNESS/INSTALL, not candor")
            rc_all = 1
        if not engines:
            print("  FAIL: no engine present — a part that ran nothing is not a pass"); return 1

        cache = {}          # (eng, label) -> (rc, doc, want)
        for eng in engines:
            loc = G.write_report(ws, eng, rep)
            n_bad, n_viol, n_fire = 0, 0, 0
            for i, (label, text, pred) in enumerate(pols):
                want = {fn_name(s.S, s.D) for s in sigs if pred(s)}
                rc, doc, err = run_gate(eng, loc, text, ws, f"a{i}")
                if fault and want and doc and doc.get("violations"):
                    print(f"  PROBE: CANDOR_PROBE_FAULT — deleting one violation from {eng}'s `{text}` document")
                    doc = dict(doc); doc["violations"] = doc["violations"][1:]
                    fault = False
                cache[(eng, label)] = (rc, doc, want)
                bad = judge(rc, doc, want)
                if doc and isinstance(doc.get("violations"), list):
                    n_viol += len(doc["violations"])
                n_fire += 1 if want else 0
                if bad:
                    n_bad += 1
                    print(f"    {eng:6s} A  {label:28s} DIVERGE  {'; '.join(bad)}" + (f"  [stderr: {err.strip()[:120]}]" if rc == 2 else ""))
            # the rows reached the gate: violations seen wherever the model rejects anything
            if n_viol == 0:
                print(f"    {eng:6s} A  VACUOUS — zero violations over {len(pols)} runs; the model rejects in {n_fire}")
                n_bad += 1
            print(f"  {eng:6s} A  lattice: {len(pols) - n_bad if n_bad <= len(pols) else 0}/{len(pols)} policies agree "
                  f"({n_viol} violation rows read)" + ("" if not n_bad else "  -> DIVERGE"))
            rc_all |= 1 if n_bad else 0
            wrong += n_bad

            # ---- B: projection rows ----------------------------------------------------------------
            locb = G.write_report(ws, eng, envelope(B1))
            D = closure_D(B1)
            bbad = []
            for c in ("unresolved", "dispatch"):
                want = {f for f, d in D.items() if c in d}
                rc, doc, err = run_gate(eng, locb, f"deny Net Unknown[{c}]", ws, f"b1{c}")
                for p in judge(rc, doc, want):
                    bbad.append(f"B1/B2 deny Net Unknown[{c}]: {p}" + (f" [stderr: {err.strip()[:160]}]" if rc == 2 else ""))
            locq = G.write_report(ws, eng, envelope(B3))
            # ⟨0.40⟩ ruled (§3.1 "a filter is answered as written"): a list naming every class is a PROPER
            # filter and is refused like a singleton; `*` is the all-classes spelling and is answered.
            for text, want_rc in (("deny Net Unknown[dispatch]", 2), ("deny Net Unknown[unresolved]", 2),
                                  (f"deny Unknown[{','.join(R)}]", 2), ("deny Unknown[*]", 1),
                                  ("deny Net Unknown", 1), ("deny Net", 0)):
                rc, doc, err = run_gate(eng, locq, text, ws, "b3" + text.replace(" ", "_"))
                if rc != want_rc:
                    bbad.append(f"B3 {text}: exit {rc}, want {want_rc}"
                                + (" (an inherited Unknown with no `calls` cannot be class-scoped: §3.1 refuse)" if want_rc == 2 else ""))
            print(f"  {eng:6s} B  projection rows: " + ("OK (repair rows, reasonless direct, refusal)" if not bbad else "DIVERGE"))
            for b in bbad:
                print(f"    {eng:6s} B  {b}")
            rc_all |= 1 if bbad else 0
            wrong += len(bbad)

            # ---- C: the class map ------------------------------------------------------------------
            ce = c_entries()
            locc = G.write_report(ws, eng, envelope(ce))
            cbad = []
            for c in R:
                want = {e["fn"] for e in ce if class_of(e["unknownWhy"][0]) == c}
                rc, doc, err = run_gate(eng, locc, f"deny Clock Unknown[{c}]", ws, f"c{c}")
                p = judge(rc, doc, want)
                if p:
                    tok = {e["fn"]: e["unknownWhy"][0] for e in ce}
                    got = {v.get("fn") for v in (doc or {}).get("violations", [])}
                    cbad.append(f"[{c}] want {sorted(tok[f] for f in want)} got {sorted(tok.get(f, f) for f in got)}"
                                + (f" (exit {rc})" if rc == 2 else ""))
            print(f"  {eng:6s} C  class map ({len(C_TOKENS)} tokens x {len(R)} classes): " + ("OK" if not cbad else "DIVERGE"))
            for b in cbad:
                print(f"    {eng:6s} C  {b}")
            rc_all |= 1 if cbad else 0
            wrong += len(cbad)

            # ---- D: the Net destination class --------------------------------------------------------
            dbad, d_cache = arm_d(eng, ws)
            cache[(eng, "D")] = d_cache
            print(f"  {eng:6s} D  Net destination class ({len(D1_POLICIES)} answerable rules over "
                  f"{len(d1_leaves())} leaves; {len(D2_POLICIES)} x {len(D2_LEAVES)} absent-netClass cells): "
                  + ("OK" if not dbad else "DIVERGE"))
            for b in dbad:
                print(f"    {eng:6s} D  {b}")
            rc_all |= 1 if dbad else 0
            wrong += len(dbad)

        # ---- CONTROLS: the comparator must be able to say DIVERGE, on every run -----------------------
        ctl_bad = []
        eng0 = engines[0]
        # (computed on the cached, possibly PROBE-corrupted, answers — the controls judge the comparator)
        # model-side: Db ⊑ₑ Net reinstated. Must diverge, only on Db-bearing / non-Net rows of Net verbs.
        mut = {fn_name(s.S, s.D) for s in sigs if "Db" in s.S and "Net" not in s.S}
        hits = 0
        for label, text, pred in pols:
            rc, doc, want = cache[(eng0, label)]
            if not label.startswith("deny Net"):
                continue
            want_mut = want | mut
            p = judge(rc, doc, want_mut)
            if p:
                hits += 1
        if hits == 0:
            ctl_bad.append("model-side seed (Db ⊑ Net reinstated) produced NO divergence")
        # diff-side: flip one row of one run; exactly one row must move.
        rc, doc, want = cache[(eng0, "deny Fs")]
        one = fn_name(frozenset(["Fs"]), frozenset())
        flipped = want ^ {one}
        got = {v.get("fn") for v in doc["violations"]} if doc else set()
        if len(got ^ flipped) != 1:
            ctl_bad.append(f"diff-side seed (one expected verdict flipped) moved {len(got ^ flipped)} rows, want exactly 1")
        # document seed: an engine's own --gate-json with one violation removed must be caught.
        if doc and doc.get("violations"):
            doc2 = dict(doc); doc2["violations"] = doc["violations"][1:]
            if not judge(rc, doc2, want):
                ctl_bad.append("document seed (one violation deleted from a real --gate-json) was NOT caught")
        else:
            ctl_bad.append("document seed could not run: the control run has no violations")
        # vacuity: the same report truncated to zero functions.
        loc0 = G.write_report(ws, eng0, envelope([]))
        rc0, doc0, _ = run_gate(eng0, loc0, "deny Fs", ws, "vac")
        want_full = cache[(eng0, "deny Fs")][2]
        if not judge(rc0, doc0, want_full):
            ctl_bad.append("vacuity seed: an engine run over ZERO functions agreed with the model — the floor is blind")
        # arm D, model-side: (i) the destination filter ignored — `Net[C]` read as bare `Net`, the shape of
        # every narrowing a filter exists for — must diverge on the answerable runs; (ii) an absent
        # `netClass` read as ∅ — the ⟨0.24⟩ fail-open SPEC §3.1 measured — must diverge on the absent cells.
        d1c, d2c = cache[(eng0, "D")]
        f1 = sum(1 for (lab, pred), (rc, doc) in zip(D1_POLICIES, d1c)
                 if judge(rc, doc, {f["fn"] for f, (sig, N) in d1_leaves() if pred.ignore_filter(sig, N)}))
        f2 = sum(1 for (key, (rc, doc)) in d2c.items()
                 if d2_judge(rc, doc, key[1], "pass" if d2_answer(key) == "refuse" else d2_answer(key)))
        if not f1:
            ctl_bad.append("arm D model-side seed (Net[C] read as bare Net) produced NO divergence")
        if not f2:
            ctl_bad.append("arm D model-side seed (absent netClass read as ∅, the ⟨0.24⟩ fail-open) produced NO divergence")
        if ctl_bad:
            for c in ctl_bad:
                print(f"  CONTROL FAIL: {c}")
            rc_all = 1
            wrong += len(ctl_bad)
        else:
            print(f"  controls ({eng0}): model-side seed diverges on {hits} Net polic(ies); diff-side seed moves "
                  f"exactly 1 row; a deleted violation is caught; a zero-function report trips the floor;")
            print(f"    arm D: `Net[C]`-as-bare diverges on {f1} rule(s), absent-as-∅ on {f2} absent cell(s)")
        print(f"MODEL VERDICT: OK — {len(engines)} engine(s) agree with the model on every run"
              if not rc_all else f"MODEL VERDICT: {max(wrong, 1)} run(s) wrong")
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
