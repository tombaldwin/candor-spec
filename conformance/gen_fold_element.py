#!/usr/bin/env python3
"""
PART 90 — THE FOLD-ELEMENT DIFFERENTIAL — ⟨0.21⟩, four-way.

A closure parameter that IS the element of a collection carries that element's effects into the caller.
This needs no new SPEC clause: ⟨0.21⟩ already says absence from `functions[]` is a purity claim, and a
fold over effectful elements reaches those effects. What it needs is a part, because the defect was live
in TWO engines at once (SOUNDNESS R349, fixed 2026-09-15 in rust `626f046` and swift `dd22413`) and
neither engine's fix was the one its own row prescribed.

WHY THE SHORTHAND/NAMED PAIR IS THE WHOLE POINT, and it is not a stylistic duplicate.
R349's filed remedy said "the LAST parameter is the element". Implementing that produces a GREEN TEST
OVER A LIVE CARDINAL SIN, and the swift agent found out by trying it: `closureParamNames` yields
`$0/$1/$2` for a SHORTHAND closure because its arity is not in the syntax, so "last" is `$2`, and
`{ $0 + $1.run() }` — the commonest spelling in real Swift — never binds. A part written with named
parameters only would have certified that fix. So f1 and f2 are the same program in two spellings, and
an engine must answer them identically. **If you add an arm to this part, add its other spelling too.**

THE DISCRIMINATOR IS `Exec` ON THE ELEMENT, AND NOTHING ELSE IN THE FIXTURE REACHES IT. The collection,
the accumulator and the fold itself are pure; only `G::run` spawns. So a pick, a drop or a
never-typed parameter is SILENT under `deny Exec probe`, and only a correct element binding fires. An
`Fs`-shaped question could not separate them — every arm touches Fs by some route once a real engine
models the collection.

THE CONTROLS ARE NOT AFTERTHOUGHTS. Typing an element is a WIDENING, and this family has twice shipped a
widening that over-reached and been caught only by a 500-crate A/B:

  f5pure   deny Exec -> 0   a PURE element through the SAME fold gains nothing. This is the arm that
                            fails if an engine charges the closure rather than the element.
  f6outer  deny Exec -> 0   a sibling function that folds over the SAME collection type without calling
                            the element's effectful method stays pure — i.e. the effect is attributed to
                            the CALL, not manufactured onto anything that touches the type.

f3order writes the element in a DIFFERENT parameter position. The rust fix is an INDEX (`reduce` -> 1)
rather than a name, and an index is exactly the kind of thing that is right for one arity and wrong for
the next; the reversed arm is this family's standing answer to that (PART 89 caught swift passing
b7mixed and failing b8mixedrev — the same program with its arms swapped).

EXPECTATION AT THE TIME OF WRITING (2026-09-15): rust and swift are FIXED and must pass every arm. java
reads bytecode and ts asks the type checker, so both were reported clean by inspection — **that is an
inference, not a measurement, and this part is what turns it into one.** If java or ts goes red here,
that is the finding and it is filed as a row, not silenced with an xfail.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_masking as gm       # noqa: E402  -- import-safe: its work is behind a __main__ guard
import gen_differential as gd  # noqa: E402

EFF = {"id": "fold"}
FAULT = os.environ.get("CANDOR_PROBE_FAULT")

# (arm, policy, expected-rc, why, skip-engines)
ARMS = [
    ("f1short",  "denyexec", 1, "the element is param 1 of a SHORTHAND closure — the commonest spelling", ()),
    ("f2named",  "denyexec", 1, "…and the identical program with NAMED parameters (R349's own remedy passed only this one)", ()),
    ("f3order",  "denyexec", 1, "…and with the element in a different POSITION — an index fix is arity-sensitive", ()),
    ("f4enum",   "denyexec", 1, "the element reached through an INDEXED pair (`enumerate`/`enumerated`)", ()),
    ("f5pure",   "denyexec", 0, "CONTROL: a PURE element through the SAME fold manufactures nothing",     ()),
    ("f6outer",  "denyexec", 0, "CONTROL: folding the same type WITHOUT calling the effectful member stays pure", ()),
]

POLICIES = {"denyexec": "deny Exec probe\n"}

# ---- rust -------------------------------------------------------------------------------------------
_R_PRE = """pub struct G;
impl G {
  pub fn run(&self) -> usize { let _ = std::process::Command::new("x").status(); 1 }
  pub fn calm(&self) -> usize { 1 }
}
"""
R_BODIES = {
  "f1short": _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { v.iter().fold(0, |a, g| a + g.run()) }\n',
  "f2named": _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { v.iter().fold(0, |acc, elem| acc + elem.run()) }\n',
  "f3order": _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { v.iter().enumerate().fold(0, |a, (_i, g)| a + g.run()) }\n',
  "f4enum":  _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { let mut n = 0; for (_i, g) in v.iter().enumerate() { n += g.run(); } n }\n',
  "f5pure":  _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { v.iter().fold(0, |a, g| a + g.calm()) }\n',
  "f6outer": _R_PRE + 'pub fn probe(v: Vec<G>) -> usize { v.iter().fold(0, |a, _g| a + 1) }\n',
}

# ---- swift ------------------------------------------------------------------------------------------
_S_PRE = """import Foundation
struct G {
  func run() -> Int { let p = Process(); p.launchPath = "/bin/x"; try? p.run(); return 1 }
  func calm() -> Int { return 1 }
}
"""
S_BODIES = {
  "f1short": _S_PRE + 'func probe(_ v: [G]) -> Int { return v.reduce(0) { $0 + $1.run() } }\n',
  "f2named": _S_PRE + 'func probe(_ v: [G]) -> Int { return v.reduce(0) { acc, elem in acc + elem.run() } }\n',
  "f3order": _S_PRE + 'func probe(_ v: [G]) -> Int { var n = 0; v.enumerated().forEach { n += $0.1.run() }; return n }\n',
  "f4enum":  _S_PRE + 'func probe(_ v: [G]) -> Int { var n = 0; for (_, g) in v.enumerated() { n += g.run() }; return n }\n',
  "f5pure":  _S_PRE + 'func probe(_ v: [G]) -> Int { return v.reduce(0) { $0 + $1.calm() } }\n',
  "f6outer": _S_PRE + 'func probe(_ v: [G]) -> Int { return v.reduce(0) { a, _ in a + 1 } }\n',
}

# ---- java (MEMBERS ONLY — write_java_tree supplies package + class) ---------------------------------
_J_PRE = """  public static class G {
    public int run() { try { new ProcessBuilder("x").start(); } catch (Exception e) {} return 1; }
    public int calm() { return 1; }
  }
"""
J_BODIES = {
  "f1short": _J_PRE + '  public static int probe(java.util.List<G> v) { return v.stream().reduce(0, (a, g) -> a + g.run(), Integer::sum); }\n',
  "f2named": _J_PRE + '  public static int probe(java.util.List<G> v) { int acc = 0; for (G elem : v) { acc += elem.run(); } return acc; }\n',
  "f3order": _J_PRE + '  public static int probe(java.util.List<G> v) { int n = 0; for (int i = 0; i < v.size(); i++) { n += v.get(i).run(); } return n; }\n',
  "f4enum":  _J_PRE + '  public static int probe(java.util.List<G> v) { int n = 0; java.util.Iterator<G> it = v.iterator(); while (it.hasNext()) { n += it.next().run(); } return n; }\n',
  "f5pure":  _J_PRE + '  public static int probe(java.util.List<G> v) { return v.stream().reduce(0, (a, g) -> a + g.calm(), Integer::sum); }\n',
  "f6outer": _J_PRE + '  public static int probe(java.util.List<G> v) { return v.stream().reduce(0, (a, g) -> a + 1, Integer::sum); }\n',
}

# ---- ts ---------------------------------------------------------------------------------------------
_T_PRE = """import { execSync } from "node:child_process";
export class G {
  run(): number { try { execSync("x"); } catch (e) {} return 1; }
  calm(): number { return 1; }
}
"""
T_BODIES = {
  "f1short": _T_PRE + 'export function probe(v: G[]): number { return v.reduce((a, g) => a + g.run(), 0); }\n',
  "f2named": _T_PRE + 'export function probe(v: G[]): number { return v.reduce(function (acc: number, elem: G) { return acc + elem.run(); }, 0); }\n',
  "f3order": _T_PRE + 'export function probe(v: G[]): number { return v.map((g, _i) => g.run()).reduce((a, n) => a + n, 0); }\n',
  "f4enum":  _T_PRE + 'export function probe(v: G[]): number { let n = 0; for (const [_i, g] of v.entries()) { n += g.run(); } return n; }\n',
  "f5pure":  _T_PRE + 'export function probe(v: G[]): number { return v.reduce((a, g) => a + g.calm(), 0); }\n',
  "f6outer": _T_PRE + 'export function probe(v: G[]): number { return v.reduce((a, _g) => a + 1, 0); }\n',
}

BODIES = {"rust": R_BODIES, "swift": S_BODIES, "java": J_BODIES, "ts": T_BODIES}

# An expectation keyed by (arm, engine) — NEVER by arm alone. PART 89's finding was swift passing one arm
# order and failing its reverse; an xfail written per-arm cannot express that and would have hidden it.
# A PASSING xfail is a FAILURE here: it is the only thing in the suite that notices an expectation which
# has quietly become true.
XFAIL = {}


def _swift_tree(d, body):
    """A BARE `cases.swift` in the cell directory — `SwiftEngine.gate` scans that path directly and does
    NOT build a package. A first draft wrapped it in Sources/ + Package.swift and every swift arm
    returned rc=2 UNIFORMLY, controls included, which is the tell: a uniform failure across arms that are
    supposed to disagree is the harness, not the engine."""
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "cases.swift"), "w") as f:
        f.write("// GENERATED by gen_fold_element.py -- do not edit.\n" + body + "\n")


def render(ws):
    for arm, _pol, _rc, _why, skip in ARMS:
        cell = f"{EFF['id']}_{arm}"
        # THE FAULT HOOK. `CANDOR_PROBE_FAULT=1` writes f1short's cell with f5pure's body — a pure
        # element, so the arm that MUST fire under `deny Exec` now cannot, and a clean run must go red.
        # A part whose failure has never been observed is not evidence (candor-oracle-disclosure-recall).
        src = "f5pure" if (FAULT and arm == "f1short") else arm
        if "rust" not in skip:
            gd.write_rust_tree(os.path.join(ws, "rust", cell), "fold", "gen_fold_element.py", BODIES["rust"][src])
        if "java" not in skip:
            gd.write_java_tree(os.path.join(ws, "java", cell), "gen_fold_element.py", BODIES["java"][src])
        if "ts" not in skip:
            gd.write_ts_tree(os.path.join(ws, "ts", cell), "fold", "gen_fold_element.py", BODIES["ts"][src])
        if "swift" not in skip:
            _swift_tree(os.path.join(ws, "swift", cell), BODIES["swift"][src])


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-foldelem-")
    pols = {}
    for k, text in POLICIES.items():
        p = os.path.join(ws, f"{k}.policy")
        with open(p, "w") as f:
            f.write(text)
        pols[k] = p

    print("=" * 100)
    print("FOLD-ELEMENT differential ⟨0.21⟩ — a closure parameter that IS the element carries its effects")
    print("  property: f1short/f2named/f3order/f4enum must FAIL under `deny Exec probe` (a never-typed")
    print("            element parameter is SILENT); f5pure/f6outer must PASS (nothing manufactured).")
    print("  the f1/f2 PAIR is the point: R349's own filed remedy passed f2 and left f1 a live sin.")
    print("=" * 100)

    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — f1short's cell carries f5pure's body (a PURE element), "
              "so the arm that MUST fail under `deny Exec` cannot. This run's verdict MUST go red. "
              "A clean run must never print this line.")
    render(ws)

    available = []
    for eng in gm.ENGINES:
        eng.prepare(ws)
        if eng.present and eng.ok:
            available.append(eng)
        else:
            print(f"  SKIP {eng.name}: {eng.err}")
    if not available:
        print("FOLD-ELEMENT: no engine available — NOT a pass")
        return 2

    bad = 0
    xfail_passed = []
    for arm, pol, want, why, skip in ARMS:
        for eng in available:
            if eng.name in skip:
                continue
            got = eng.gate(ws, EFF, arm, pols[pol])
            key = (arm, eng.name)
            exp = XFAIL.get(key)
            if got == want:
                if exp:
                    xfail_passed.append(key)
                    print(f"  XFAIL ARM PASSED  {arm:9s} {eng.name:6s} — expectation is STALE: {exp}")
                else:
                    print(f"  OK    {arm:9s} {eng.name:6s} rc={got}  {why}")
            else:
                if exp:
                    print(f"  xfail {arm:9s} {eng.name:6s} rc={got} (want {want}) — {exp}")
                else:
                    print(f"  FAIL  {arm:9s} {eng.name:6s} rc={got}, want {want}  {why}")
                    bad += 1

    if xfail_passed:
        print(f"FOLD-ELEMENT: {len(xfail_passed)} xfail arm(s) PASSED — an expectation that has become "
              "true is a FAILURE here; retire it from XFAIL in the same commit as the engine fix.")
        return 1
    if bad:
        print(f"FOLD-ELEMENT: {bad} arm(s) wrong — a fold over an effectful element is not charging")
        return 1
    print("  -> MATCH — every engine charges the element's effects through a fold, in BOTH the shorthand")
    print("     and named spellings and in both parameter positions, and neither control manufactures one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
