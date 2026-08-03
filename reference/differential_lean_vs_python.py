#!/usr/bin/env python3
"""
THE MACHINE-CHECKED MODEL vs THE HAND TRANSCRIPTION. EVERY ROW, BOTH ANSWERS, NO SAMPLING.

WHY THIS EXISTS
---------------
Conformance PART 23 judges the four ENGINES against `policy_model.py`. That makes `policy_model.py` a
trusted artifact sitting in the middle of the chain — and it is a HAND transcription of PAPER3's
definitions into Python, checked by nobody but the person who typed it.

Twice that has been wrong, and both times the error had the same shape — a definition read slightly
askew, then reasoned from confidently for weeks:

  · Def 2 read `Db ⊑ₑ Net`, so `deny Net` fired on a determined `{Db}`: 100 disagreements over 1792
    rows, model REJECT and engine pass, every one that family.
  · Def 32 read `Reject ⇔ (S,D) ≠ (∅,∅)`, which reported all four CONFORMING engines as violating the
    theory on the signature `(∅,{r})`.

Neither was caught by a proof. Both were caught by running the model against something else and being
surprised. `lean/` now states the same definitions in Lean and proves the properties the amendments
claim — but a second transcription is only worth having if the two are CHECKED against each other.
Otherwise there are simply two unverified files instead of one.

So: Lean enumerates the vocabulary and emits its verdict for every (verb, argument, scope, signature);
this script recomputes each row with `policy_model.py` and fails on any disagreement. The Lean side
carries `Exec.lean`'s bridge lemmas, so its Bool answers are the PROVED ones — a disagreement is
therefore evidence against the Python, not a coin toss between two guesses.

WHAT IT CANNOT CHECK, said plainly: both files are transcriptions of a paper that is not in this repo.
Agreement here means the two readings match; it cannot mean either matches PAPER3. Model↔paper drift
stays a human check, and this closes the transcription↔transcription half of it.

    python3 differential_lean_vs_python.py                 # builds + runs the Lean emitter itself
    python3 differential_lean_vs_python.py rows.tsv        # or reads a pre-emitted table
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEAN_DIR = os.path.join(os.path.dirname(HERE), "lean")

sys.path.insert(0, HERE)
import policy_model as pm  # noqa: E402


def emit_rows():
    """Build and run the Lean emitter. Returns its stdout, or exits 2 if the toolchain is absent.

    Exit 2, not 0: a differential that silently reports success when it could not obtain one of its two
    sides is exactly the instrument-that-cannot-fail this whole layer exists to remove.
    """
    elan_bin = os.path.expanduser("~/.elan/bin")
    env = dict(os.environ)
    if os.path.isdir(elan_bin) and elan_bin not in env.get("PATH", ""):
        env["PATH"] = elan_bin + os.pathsep + env.get("PATH", "")
    try:
        b = subprocess.run(["lake", "build", "emit"], cwd=LEAN_DIR, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print("DIFFERENTIAL: no `lake` on PATH — the Lean side cannot be produced.", file=sys.stderr)
        print("  install: curl -sSfL https://elan.lean-lang.org/elan-init.sh | sh", file=sys.stderr)
        sys.exit(2)
    if b.returncode != 0:
        print(b.stdout.decode(errors="replace"), file=sys.stderr)
        print("DIFFERENTIAL: the Lean model does not build — fix that before comparing.", file=sys.stderr)
        sys.exit(2)
    r = subprocess.run([os.path.join(LEAN_DIR, ".lake", "build", "bin", "emit")], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        print(r.stdout.decode(errors="replace"), file=sys.stderr)
        sys.exit(2)
    return r.stdout.decode()


def parse_set(field):
    """An empty column is the empty set. No effect or reason name is ever the empty string, so this is
    unambiguous — but it is the one place the two sides could silently disagree about NOTHING, so the
    vocabulary check below verifies every non-empty name against `policy_model`'s own tuples."""
    return () if not field else tuple(field.split(","))


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            text = f.read()
    else:
        text = emit_rows()

    rows = [ln for ln in text.splitlines() if ln.strip()]
    if not rows:
        print("DIFFERENTIAL: the Lean side emitted NO rows — nothing was compared.", file=sys.stderr)
        return 2

    # PRE-PASS: the vocabularies are reconciled BEFORE any row is compared. Not a stylistic choice —
    # `policy_model.Sig` asserts `S ⊆ E` in its constructor, so a Lean-only effect raises an AssertionError
    # from inside the model on the first row that mentions it. That IS a failure, but it reports as a stack
    # trace from a helper rather than as the drift it is, and a confusing failure is one somebody explains
    # away. Check the thing you mean to check, in the words you mean to say it.
    parsed = []
    seen_effects, seen_reasons = set(), set()
    for i, ln in enumerate(rows, 1):
        parts = ln.split("\t")
        if len(parts) != 7:
            print(f"DIFFERENTIAL: row {i} has {len(parts)} columns, expected 7: {ln!r}", file=sys.stderr)
            return 2
        verb, arg, cs, ss, ds, verdict_s, reach_s = parts
        C, S, D = parse_set(cs), parse_set(ss), parse_set(ds)
        seen_effects.update(S)
        if arg:
            seen_effects.add(arg)
        seen_reasons.update(C)
        seen_reasons.update(D)
        parsed.append((i, verb, arg, C, S, D, verdict_s, reach_s))

    py_only = (set(pm.E) - seen_effects) | (set(pm.R) - seen_reasons)
    lean_only = (seen_effects - set(pm.E)) | (seen_reasons - set(pm.R))
    if py_only or lean_only:
        if py_only:
            print(f"DIFFERENTIAL: policy_model names {sorted(py_only)}, which the Lean side never "
                  f"emitted — the vocabularies have drifted apart.", file=sys.stderr)
        if lean_only:
            print(f"DIFFERENTIAL: the Lean side emitted {sorted(lean_only)}, which policy_model does not "
                  f"name — every row mentioning it would agree only because `refines` is False on an "
                  f"unknown string, not because the models match.", file=sys.stderr)
        return 2

    disagree = []
    reach_disagree = []
    spec_reading_off = []      # deny rows where SPEC §4.0's `e ∈ S` differs from PAPER3's `⊑` reading
    spec_reading_off_reachable = []
    n_reachable = 0
    seen_verbs = {}
    for (i, verb, arg, C, S, D, verdict_s, reach_s) in parsed:
        lean = {"true": True, "false": False}[verdict_s.strip().lower()]
        lean_reach = {"true": True, "false": False}[reach_s.strip().lower()]

        sig = pm.Sig(frozenset(S), frozenset(D))
        if verb == "pure":
            py = pm.pure()(sig)
        elif verb == "deny":
            py = pm.deny(arg)(sig)
        elif verb == "deny_unknown":
            py = pm.deny_unknown(arg, C)(sig)
        else:
            print(f"DIFFERENTIAL: row {i} names an unknown verb {verb!r}", file=sys.stderr)
            return 2
        seen_verbs[verb] = seen_verbs.get(verb, 0) + 1

        if py != lean:
            disagree.append((i, verb, arg, C, S, D, lean, py))

        # ARM 2 — the reachability predicate itself. `coemit` in Lean and `CO_EMIT` here are independent
        # copies of the same DATA, and a refinement rung edits both. If they drift, arm 3 below silently
        # partitions the domain along the wrong line.
        if pm.is_reachable(sig) != lean_reach:
            reach_disagree.append((i, S, lean_reach))
        if lean_reach:
            n_reachable += 1

        # ARM 3 — SPEC §4.0's table reads `deny e` as plain membership `e ∈ S`; PAPER3 Def 4 reads it as
        # firing over the refinement preorder. Lean PROVES these coincide on reachable signatures
        # (`fires_iff_mem_of_reachable`). This is the executable side of that theorem, and it is also what
        # stops "restrict to the reachable lattice" from being a way to make a disagreement go away: the
        # two readings MUST agree everywhere reachable, and MUST differ somewhere unreachable.
        if verb == "deny":
            if (arg in sig.S) != lean:
                spec_reading_off.append(i)
                if lean_reach:
                    spec_reading_off_reachable.append((i, arg, S))

    print("DIFFERENTIAL — Lean model (proved) vs reference/policy_model.py (hand transcription)")
    print(f"  rows compared : {len(rows)}")
    for v, n in sorted(seen_verbs.items()):
        print(f"    {v:<14} {n}")
    print(f"  vocabulary    : {len(seen_effects)} effects, {len(seen_reasons)} reasons "
          f"(policy_model: {len(pm.E)}, {len(pm.R)})")
    print(f"  reachable     : {n_reachable} / {len(rows)} "
          f"({len(rows) - n_reachable} excluded by co-emission {dict(pm.CO_EMIT)})")
    print(f"  SPEC §4.0 `e ∈ S` vs PAPER3 `⊑` on deny: {len(spec_reading_off)} differ over the full "
          f"lattice, {len(spec_reading_off_reachable)} over the reachable part")

    if reach_disagree:
        print(f"\n  REACHABILITY DISAGREEMENTS: {len(reach_disagree)} — Lean's `coemit` and "
              f"policy_model's CO_EMIT have drifted apart.")
        for (i, S, lr) in reach_disagree[:10]:
            print(f"    row {i}: S={set(S) or '∅'} — Lean reachable={lr}, policy_model={not lr}")
        return 1

    if spec_reading_off_reachable:
        print(f"\n  SPEC/PAPER RECONCILIATION BROKEN: {len(spec_reading_off_reachable)} REACHABLE rows "
              f"where `e ∈ S` and the refinement reading disagree. Lean proves this set is empty "
              f"(`fires_iff_mem_of_reachable`), so one of the two models no longer matches its proof.")
        for (i, arg, S) in spec_reading_off_reachable[:10]:
            print(f"    row {i}: deny {arg} on S={set(S) or '∅'}")
        return 1

    if not spec_reading_off:
        print("\n  VACUOUS: the two readings of `deny e` never differ ANYWHERE, so restricting to the "
              "reachable lattice tests nothing. Expected them to differ on unreachable signatures — "
              "the refinement pair has gone missing from one of the models.")
        return 1

    if disagree:
        print(f"\n  DISAGREEMENTS: {len(disagree)}")
        for (i, verb, arg, C, S, D, lean, py) in disagree[:40]:
            print(f"    row {i}: {verb} {arg or '-'} C={set(C) or '∅'} on "
                  f"S={set(S) or '∅'} D={set(D) or '∅'} — Lean {lean}, Python {py}")
        if len(disagree) > 40:
            print(f"    … and {len(disagree) - 40} more")
        print("\nDIFFERENTIAL: FAILED. The Lean side is the proved one — read the Python first.")
        return 1

    print("\nDIFFERENTIAL: OK — the two transcriptions agree on every row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
