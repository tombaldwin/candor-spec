#!/usr/bin/env python3
"""
P4 — SIGNATURE MONOTONICITY, as a GENERATED property (SCAN-BOUNDARY-WORK-QUEUE.md §3).

    adding a call to a function may only ADD to what its report says.
    It may never REMOVE an effect, and it may never remove a reason the report already gave.

The fourth and last of the self-differential properties, and the same construction as P1/P2/P3 for the
same reason: the cross-engine suite asks "do the four engines agree?", and four engines sharing one spec
and one author's mental model agree just as readily when the model is wrong — the coverage door and the
malformed manifest were both four-way. Here each engine is compared with ITSELF across two renderings of
one function, one of which is the other plus a call. There is NO EXPECTED-VALUE TABLE and there must
never be one; **the base arm is the expectation.** If a table ever appears in this file, this has stopped
being a property and become a fixture suite.

WHY THIS PROPERTY, AND WHAT SHAPE OF DEFECT IT CATCHES
-------------------------------------------------------
Every other property here varies the INPUT REPORTS (P2, P3) or the PACKAGING (P1). This one varies the
PROGRAM, and it is the only one that does. The defect it is built for is an engine that, on meeting a
call it cannot resolve, REPLACES a unit's answer instead of widening it:

    base                  f() { fs_sink(); }              -> ['Fs']
    plus an opaque call   f() { fs_sink(); opaque(); }    -> ['Unknown']        <-- the Fs is GONE

That is a silent under-report reached by ADDING code, which is the direction real programs move in. The
same shape hides behind every fan-out bound in the family: candor-ts's `fc8d297` publishes `['Unknown']`
once a CHA union passes `CHA_FANOUT_LIMIT`, and whether that ADDS to the union or REPLACES it is exactly
the question this property asks. A bound that replaces is a cardinal sin you reach by writing one more
implementation of an interface.

THE RELATION IS DIRECTIONAL — subset-or-equal, in the opposite direction from P3
--------------------------------------------------------------------------------
    effects(base)  ⊆  effects(base + a call)
    reasons(base)  ⊆  reasons(base + a call)
    base present in `functions`  ⟹  the augmented unit is present too

Equality would be WRONG here and would manufacture findings on every honest engine: the added call is
supposed to contribute. `plus_log` must gain `Log`, `plus_opaque` must gain `Unknown`. What is forbidden
is LOSS, in either channel.

The presence conjunct is the sharpest of the three and is why it is stated separately. Under ⟨0.21⟩ an
absent entry is a POSITIVE claim of purity, so a unit that drops out of `functions` when a call is added
has not become less informative — it has started making a stronger claim on less evidence.

REASONS ARE COMPARED AS TOKENS, NOT CLASSES, AND THAT IS DELIBERATE
--------------------------------------------------------------------
The queue filed this as blocked on `gate --report` "for the class half". It is not, and reading the
report directly is better: `unknownWhy` is on the wire already, per unit, and a token set is strictly
finer than the §6.2 class projection it feeds. A token lost from a unit is a class at risk of being lost
from a gate — `deny E Unknown[reflect]` stops biting the moment `reflect:` stops being published — and
catching it a projection earlier means the finding names the token that went missing rather than the
class that got thinner. The projection itself is PART 27's job and is already pinned there.

VACUITY (standing bar item 8) is computed from the ENGINE'S OWN output and never asserted: a cell whose
BASE arm carries no effect and no reason demands nothing of the augmented arms and is counted VACUOUS.
The run FAILS if any engine's live count is zero — a property that demands nothing of anybody passes
every time, and that failure mode has already been shipped once in this suite.

ONE TREE PER LANGUAGE, NOT ONE PER ARM. Every (effect, augmentation) pair is a separately-named function
in a single source file, so the whole matrix costs FOUR scans rather than four-times-N. Every helper a
cell declares is suffixed with that cell's id, so no cell can see another's types — which matters most
for the fan-out arm, whose whole job is to create implementers.

USAGE
    python3 gen_signature_monotonicity.py                  # raw truth, exit non-zero on any violation
    python3 gen_signature_monotonicity.py --only fs,net
    python3 gen_signature_monotonicity.py --keep
    python3 gen_signature_monotonicity.py --baseline signature-monotonicity-baseline.json   # PART 28
"""
# NO NORMATIVE CLAUSES — a pure self-differential. The base arm is the expectation; the spec does not state
# "adding a call may only add" as a MUST, and this property would be wrong to claim it does. Declared
# empty rather than omitted, so a missing declaration still fails clause_check.py.
SPEC_CLAUSES = []

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_differential as gd
import split_arms as sa

UNKNOWN = "Unknown"


# =====================================================================================================
# THE AUGMENTATIONS. Each returns (decls, stmt) per language: `decls` is prepended at file scope, `stmt`
# is appended to the entry function's body AFTER the base sink. The FIRST is the reference arm, and it
# adds nothing at all — the base against which every other arm is judged.
# =====================================================================================================
def _pure(sfx):
    h = f"pu_{sfx}"
    return dict(
        rust=(f"fn {h}() -> i32 {{ 1 }}", f"let _ = {h}();"),
        java=(f"  static int {h}() {{ return 1; }}", f"int _v_{sfx} = {h}();"),
        ts=(f"function {h}(): number {{ return 1; }}", f"void {h}();"),
        swift=(f"func {h}() -> Int {{ return 1 }}", f"_ = {h}()"),
    )


def _same(eff, sfx):
    h = f"sm_{sfx}"
    return dict(
        rust=(f'fn {h}() {{ {eff["sink"]["rust"]} }}', f"{h}();"),
        java=(f'  static void {h}() {{ {eff["sink"]["java"]} }}', f"{h}();"),
        ts=(f'function {h}(): void {{ {eff["sink"]["ts"]} }}', f"{h}();"),
        swift=(f'func {h}() {{ {eff["sink"]["swift"]} }}', f"{h}()"),
    )


def _other(sfx):
    """A SECOND, DIFFERENT effect. `Log` is chosen because every engine classifies it and it is the one
    effect that cannot be confused with any base sink in the matrix (there is a `log` row, and that row's
    `plus_other` degenerates to `plus_same`, which is harmless — it still forbids loss)."""
    h = f"ot_{sfx}"
    log = next(e for e in gd.EFFECTS if e["id"] == "log")
    return dict(
        rust=(f'fn {h}() {{ {log["sink"]["rust"]} }}', f"{h}();"),
        java=(f'  static void {h}() {{ {log["sink"]["java"]} }}', f"{h}();"),
        ts=(f'function {h}(): void {{ {log["sink"]["ts"]} }}', f"{h}();"),
        swift=(f'func {h}() {{ {log["sink"]["swift"]} }}', f"{h}()"),
    )


def _opaque(sfx):
    """THE ARM THIS PROPERTY EXISTS FOR: a call the engine cannot resolve, added beside a sink it can.
    The augmented unit must carry the base effect AND `Unknown` — never `Unknown` instead. Rendered as an
    indirect call through a value the engine cannot pin to one body."""
    t = f"Op_{sfx}"
    return dict(
        rust=(f"fn {t}_a() {{}}\nfn {t}_b() {{}}\n"
              f"fn {t}_pick(n: usize) -> fn() {{ if n > 0 {{ {t}_a }} else {{ {t}_b }} }}",
              f"({t}_pick(1))();"),
        java=(f"  interface {t}I {{ void go(); }}\n"
              f"  static {t}I {t}_pick() {{ return () -> {{}}; }}",
              f"{t}_pick().go();"),
        ts=(f"function {t}_a(): void {{}}\n"
            f"function {t}_pick(): () => void {{ return {t}_a; }}",
            f"{t}_pick()();"),
        swift=(f"func {t}_a() {{}}\nfunc {t}_pick() -> () -> Void {{ return {t}_a }}",
               f"{t}_pick()()"),
    )


def _recurse(name, sfx):
    """A guarded self-call. The fixpoint must converge to at least what the non-recursive body says; an
    engine that seeds a recursive unit as pure and then fails to re-widen it loses the base effect.

    THE GUARD MUST BE PURE, and the first version of this arm was not. It read `System.nanoTime() < 0` in
    java and `Date.now() < 0` in ts — both of which are CLOCK SINKS. The arm's activity report showed it
    changing 5/5 cells on exactly those two engines and 0/5 on the other two, which looked like an
    engine difference and was really this file adding an effect and then observing that an effect had
    been added. A guard that contributes an effect measures the guard.
    """
    g = f"g_{sfx}"
    return dict(
        rust=(f"static {g.upper()}: bool = false;", f"if {g.upper()} {{ {name}(); }}"),
        java=(f"  static final boolean {g.upper()} = false;", f"if ({g.upper()}) {{ {name}(); }}"),
        ts=(f"const {g} = false as boolean;", f"if ({g}) {{ {name}(); }}"),
        swift=(f"let {g} = false", f"if {g} {{ {name}() }}"),
    )


def _fanout(sfx, n=20):
    """MANY implementers behind one interface call, added beside the base sink. This is the arm that
    reaches a CHA fan-out bound, where an engine that publishes `['Unknown']` PAST the limit has to be
    adding to the union rather than replacing it. All implementers are pure, so the honest answers are
    `base` or `base + Unknown` — and never `Unknown` alone, which is what a replacing bound emits.

    `n` MUST EXCEED THE BOUND OR THIS ARM TESTS NOTHING. `CHA_FANOUT_LIMIT` is 12 in candor-ts
    (`scan.mjs`) and 12 in candor-java (`Rules.java`); the first version of this arm used exactly 12 and
    changed NOTHING on any engine, which the activity report below caught. Sitting on the boundary of the
    bound you are trying to cross is the same defect as the locale control that chose `tr_TR` — an
    experiment that returns "no difference" and licenses a conclusion it never tested. 20 clears both.
    """
    t = f"Fo_{sfx}"
    rs = "\n".join(f"pub struct {t}{i};\nimpl {t}T for {t}{i} {{ fn go(&self) {{}} }}" for i in range(n))
    jv = "\n".join(f"  static class {t}{i} implements {t}T {{ public void go() {{}} }}" for i in range(n))
    ts = "\n".join(f"class {t}{i} implements {t}T {{ go(): void {{}} }}" for i in range(n))
    sw = "\n".join(f"struct {t}{i}: {t}T {{ func go() {{}} }}" for i in range(n))
    return dict(
        rust=(f"pub trait {t}T {{ fn go(&self); }}\n{rs}\nfn {t}_use(x: &dyn {t}T) {{ x.go(); }}",
              f"{t}_use(&{t}0);"),
        java=(f"  interface {t}T {{ void go(); }}\n{jv}\n"
              f"  static void {t}_use({t}T x) {{ x.go(); }}",
              f"{t}_use(new {t}0());"),
        ts=(f"interface {t}T {{ go(): void }}\n{ts}\nfunction {t}_use(x: {t}T): void {{ x.go(); }}",
            f"{t}_use(new {t}0());"),
        swift=(f"protocol {t}T {{ func go() }}\n{sw}\nfunc {t}_use(_ x: {t}T) {{ x.go() }}",
               f"{t}_use({t}0())"),
    )


AUGMENTATIONS = [
    ("base", lambda eff, name, sfx: dict(rust=("", ""), java=("", ""), ts=("", ""), swift=("", ""))),
    ("plus_pure", lambda eff, name, sfx: _pure(sfx)),
    ("plus_same", lambda eff, name, sfx: _same(eff, sfx)),
    ("plus_other", lambda eff, name, sfx: _other(sfx)),
    ("plus_opaque", lambda eff, name, sfx: _opaque(sfx)),
    ("plus_recurse", lambda eff, name, sfx: _recurse(name, sfx)),
    ("plus_fanout", lambda eff, name, sfx: _fanout(sfx)),
]


def render(eff, aug_name, aug, name, sfx):
    d = aug(eff, name, sfx)
    rd, rs = d["rust"]
    jd, js = d["java"]
    td, tstmt = d["ts"]
    sd, ss = d["swift"]
    return {
        "rust": f'{rd}\npub fn {name}() {{ {eff["sink"]["rust"]} {rs} }}'.lstrip(),
        "java": f'{jd}\n  public static void {name}() throws Exception {{ {eff["sink"]["java"]} {js} }}'.lstrip(),
        "ts": f'{td}\nexport function {name}(): void {{ {eff["sink"]["ts"]} {tstmt} }}'.lstrip(),
        "swift": f'{sd}\nfunc {name}() {{ {eff["sink"]["swift"]}\n  {ss} }}'.lstrip(),
    }


def build_cells(only=None):
    cells = []
    for eff in gd.EFFECTS:
        if only and eff["id"] not in only:
            continue
        for aug_name, aug in AUGMENTATIONS:
            sfx = f"{eff['id']}_{aug_name}"
            name = f"p4_{sfx}"
            cells.append(dict(name=name, effect=eff["effect"], effect_id=eff["id"],
                              aug=aug_name, code=render(eff, aug_name, aug, name, sfx)))
    return cells


# =====================================================================================================
# scanning. Mirrors gen_differential's engine invocations, but returns the REPORT PATH so the richer
# `split_arms.leaf_info` (effects + `unknownWhy` + kappa) can be used rather than an effects-only view.
# =====================================================================================================
def _rust(ws):
    binp = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
    if not os.path.exists(binp):
        gd.run(["cargo", "build", "-q", "--manifest-path", os.path.join(gd.CANDOR, "Cargo.toml"),
                "-p", "candor-scan"])
    if not os.path.exists(binp):
        return None, "no candor-scan"
    d = os.path.join(ws, "rust")
    r = gd.run([binp, d])
    rep = [p for p in gd._glob(os.path.join(d, ".candor"), ".scan.json") if "callgraph" not in p]
    if r.returncode != 0 or not rep:
        return None, f"candor-scan errored: {r.stderr.decode()[:200]}"
    return (rep[0], ("::",)), None


def _java(ws):
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None
    if not jar or not os.path.exists(jar):
        return None, "no candor-java jar"
    if not shutil.which("javac"):
        return None, "no javac"
    cls = os.path.join(ws, "jout")
    os.makedirs(cls, exist_ok=True)
    c = gd.run(["javac", "-d", cls, os.path.join(ws, "java", "Cases.java")])
    if c.returncode != 0:
        return None, f"javac failed: {c.stderr.decode()[:400]}"
    out = os.path.join(ws, "java.json")
    j = gd.run(["java", "-jar", jar, cls, "--json", out])
    if j.returncode != 0 or not os.path.exists(out):
        return None, f"candor-java errored: {j.stderr.decode()[:200]}"
    return (out, (".",)), None


def _ts(ws):
    if not shutil.which("node") or not os.path.exists(os.path.join(gd.CANDOR_TS, "scan.mjs")):
        return None, "no node / scan.mjs"
    d = os.path.join(ws, "ts")
    pfx = os.path.join(d, "out")
    gd.run(["node", os.path.join(gd.CANDOR_TS, "scan.mjs"), d, "--out", pfx])
    out = pfx + ".json"
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        return None, "candor-ts errored"
    return (out, (".",)), None


def _swift(ws):
    if not shutil.which("swift") or not os.path.exists(os.path.join(gd.CANDOR_SWIFT, "Package.swift")):
        return None, "no swift toolchain"
    binp = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(binp):
        gd.run(["swift", "build"], cwd=gd.CANDOR_SWIFT)
    if not os.path.exists(binp):
        return None, "swift build failed"
    src = os.path.join(ws, "swift", "cases.swift")
    pfx = os.path.join(ws, "swift", "out")
    s = gd.run([binp, src, "--out", pfx])
    rep = [p for p in gd._glob(os.path.dirname(pfx), ".json")
           if "callgraph" not in p and "hierarchy" not in p and os.path.basename(p).startswith("out.")]
    if s.returncode != 0 or not rep:
        return None, f"candor-swift errored: {s.stderr.decode()[:200]}"
    return (rep[0], (".",)), None


ENGINES = [("rust", _rust), ("java", _java), ("ts", _ts), ("swift", _swift)]


# =====================================================================================================
# the verdict for ONE (effect, augmentation) cell against its base.
# =====================================================================================================
def verdict(base, arm):
    """base/arm are `leaf_info` records, or None when the unit is absent from `functions`."""
    if base is None:
        return "VACUOUS"                       # nothing claimed, nothing demanded (earned, not asserted)
    b_eff, b_why = base["eff"], base["why"]
    if not b_eff and not b_why and not base["unknown"]:
        return "VACUOUS"
    if arm is None:
        # ⟨0.21⟩: absence is a POSITIVE purity claim, so this is the strongest form of loss, not a gap.
        return "VANISHED"
    if b_eff - arm["eff"]:
        return "LOST_EFF"
    if base["unknown"] and not arm["unknown"]:
        return "LOST_UNKNOWN"
    if b_why - arm["why"]:
        return "LOST_WHY"
    return "OK"


CARDINAL = ("VANISHED", "LOST_EFF")
GATEVIS = ("LOST_UNKNOWN", "LOST_WHY")

# WHICH ARMS MUST DEMONSTRABLY DO SOMETHING, and which are must-NOT-change controls.
#
# This split is in-band rather than in a comment because both of this file's first-run defects were arms
# that quietly tested nothing, and the run reported OK on all four engines with 48/48 cells "live". A cell
# is counted live when its BASE claims something — which says nothing about whether the AUGMENTATION did.
#
#   MUST_CHANGE   the added call is supposed to contribute (a second effect, an unresolvable call, a
#                 fan-out past the CHA bound). If one of these changes NOTHING on ANY engine, the arm is
#                 inert and the run FAILS — that is a broken instrument, not a passing property.
#   MUST_NOT      the added call is supposed to contribute nothing (a pure helper, a duplicate of the
#                 same sink, a guarded self-call). These SHOULD read identical-to-base everywhere; they
#                 are what catches an engine that loses an effect on meeting a harmless call, and their
#                 changing nothing is the correct outcome, not an inert one.
MUST_CHANGE = ("plus_other", "plus_opaque", "plus_fanout")
MUST_NOT_CHANGE = ("plus_pure", "plus_same", "plus_recurse")


def main():
    args = sys.argv[1:]
    keep = "--keep" in args
    only = None
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    baseline = None
    if "--baseline" in args:
        baseline = args[args.index("--baseline") + 1]

    cells = build_cells(only)
    ws = tempfile.mkdtemp(prefix="candor-p4sig-")
    gd.write_sources(ws, cells)
    if keep:
        print(f"  workspace kept: {ws}")

    print("P4 — SIGNATURE MONOTONICITY  (each engine vs ITSELF: adding a call may only ADD)")
    print("  .=OK  v=VACUOUS(base claims nothing)  E=LOST_EFF  X=VANISHED  u=LOST_UNKNOWN  w=LOST_WHY")

    by_eff = {}
    for c in cells:
        by_eff.setdefault(c["effect_id"], {})[c["aug"]] = c

    rows, findings, absent = [], [], []
    for eng, runner in ENGINES:
        got, err = runner(ws)
        if got is None:
            absent.append((eng, err))
            continue
        info, _unc = sa.leaf_info(got[0], got[1])
        live = vac = ok = 0
        counts = {k: 0 for k in CARDINAL + GATEVIS}
        act = {a: 0 for a, _ in AUGMENTATIONS if a != "base"}
        for eid, augs in by_eff.items():
            base_cell = augs["base"]
            base = info.get(base_cell["name"])
            for aug_name, cell in augs.items():
                if aug_name == "base":
                    continue
                arm = info.get(cell["name"])
                # ACTIVITY, recorded independently of the verdict: did this augmentation change the
                # engine's answer at all? A cell is "live" when its BASE claims something, which says
                # nothing about whether the ADDED CALL did — and an arm that never changes an answer
                # cannot fail, so it passes for free.
                if base is not None:
                    b = (base["eff"], base["unknown"])
                    a = (arm["eff"], arm["unknown"]) if arm is not None else None
                    if a != b:
                        act[aug_name] += 1
                v = verdict(base, arm)
                if v == "VACUOUS":
                    vac += 1
                    continue
                live += 1
                if v == "OK":
                    ok += 1
                else:
                    counts[v] += 1
                    findings.append((eng, eid, aug_name, v, base, arm))
        rows.append((eng, live, vac, ok, counts, act))

    print(f"  {'engine':<8}{'live':>6}{'vac':>5}{'ok':>5}{'LOST_EFF':>10}{'VANISHED':>10}"
          f"{'LOST_UNK':>10}{'LOST_WHY':>10}")
    for eng, live, vac, ok, counts, _act in rows:
        print(f"  {eng:<8}{live:>6}{vac:>5}{ok:>5}{counts['LOST_EFF']:>10}{counts['VANISHED']:>10}"
              f"{counts['LOST_UNKNOWN']:>10}{counts['LOST_WHY']:>10}")
    for eng, err in absent:
        print(f"  {eng:<8}ABSENT — {err}")

    # ---- ARM ACTIVITY: printed every run, because a control nobody looks at is not a control. --------
    print("\nARM ACTIVITY — cells where the added call CHANGED the engine's answer")
    print("  MUST_CHANGE arms are supposed to contribute; an inert one cannot fail and passes for free.")
    print("  MUST_NOT arms are supposed to contribute nothing; 0 everywhere is the CORRECT reading.")
    inert = []
    for aug, _ in AUGMENTATIONS:
        if aug == "base":
            continue
        per = {eng: act.get(aug, 0) for eng, _l, _v, _o, _c, act in rows}
        kind = "MUST_CHANGE" if aug in MUST_CHANGE else "must-not "
        cells = "  ".join(f"{e}={n}" for e, n in per.items())
        flag = ""
        if aug in MUST_CHANGE and not any(per.values()):
            flag = "   <== INERT: this arm tests nothing"
            inert.append(aug)
        print(f"  {kind} {aug:<14} {cells}{flag}")

    def show(b, a):
        f = lambda i: "(ABSENT)" if i is None else (
            ",".join(sorted(i["eff"])) + ("+Unknown" if i["unknown"] else "") or "(pure)")
        return f"base={f(b)}  arm={f(a)}"

    if findings:
        print(f"\n{len(findings)} VIOLATION(S) — adding a call REMOVED something the base arm published:")
        for eng, eid, aug, v, b, a in findings[:40]:
            print(f"  {eng:<6} {eid:<6} {aug:<14} {v:<13} {show(b, a)}")
        if len(findings) > 40:
            print(f"  ... and {len(findings) - 40} more")

    # VACUITY GUARD (standing bar item 8): a property that demands nothing of an engine passes for free.
    broken = [eng for eng, live, _v, _o, _c, _a in rows if live == 0]
    if broken:
        print(f"\nFAIL — no live cells for {', '.join(broken)}: this property demanded nothing of them.")
    if inert:
        print(f"\nFAIL — inert arm(s): {', '.join(inert)}. An augmentation that never changes any "
              f"engine's answer cannot fail, so its 'OK' is an artefact of the fixture rather than a "
              f"fact about the engines. Both of this file's first-run defects were this.")
    if not rows:
        print("\nFAIL — no engine produced a report; nothing was measured.")

    if not keep:
        shutil.rmtree(ws, ignore_errors=True)

    waived = 0
    if baseline and os.path.exists(baseline):
        with open(baseline) as f:
            bl = json.load(f)
        known = {(k["engine"], k["aug"]) for k in bl.get("known", [])}
        hit = {(e, a) for e, _i, a, _v, _b, _r in findings}
        stale = known - hit
        waived = len([1 for e, _i, a, _v, _b, _r in findings if (e, a) in known])
        findings = [f for f in findings if (f[0], f[2]) not in known]
        print(f"\nRATCHET  (baseline: {baseline})")
        for e, a in sorted(known):
            mark = "STALE — every cell now passes; DELETE the entry" if (e, a) in stale else "WAIVED"
            print(f"  {e:<6} {a:<14} {mark}")
        if stale:
            print("\nFAIL — a waiver that outlives its defect masks the defect's return.")
            return 2

    bad = bool(findings) or bool(broken) or bool(inert) or not rows
    print(f"\nP4 SIGNATURE MONOTONICITY: {'FAILED — see above.' if bad else 'OK'}"
          + (f" — {len(rows)} engine(s), every added call only ADDED"
             + (f" (except {waived} waived)" if waived else "") if not bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
