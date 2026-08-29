#!/usr/bin/env python3
"""
generator_canary.py — mutation_poison_gen.py's OWN liveness control, the same idea as mutation-
gate.sh's canary/cannot-fail.sh applied one layer up: a generator that never reports BROKEN is
indistinguishable from one that never ran, so this proves it CAN, deliberately, across every
invocation shape it claims to cover and every failure mode it claims to distinguish.

THREE SHAPES (the task's own requirement: "catch an unconditional-pass checker in every class it
claims to cover"):
  - EMBEDDED / pyvar   (VD_PY, pulled out of run.sh as a bash variable)
  - EMBEDDED / bashfunc (ck83_defect, a bash function wrapping `python3 -c`)
  - STANDALONE / extfile (incomplete_check.py, a real conformance/*.py file)
For each, the REAL (correct) source is classified as usual, then a MUTANT that replaces the entire
body with an unconditional accept (`sys.exit(0)` / `return 0` regardless of input) is evaluated
against the SAME mechanically-generated poison. Every poison leg must come back BROKEN — a generator
that reported PASS here would be rubber-stamping a checker that checks nothing.

TWO DIRECTIONS ("found, and found broken"):
  (1) FOUND — the canary is not silently absent from the report: evaluate_checker() must return at
      least one row per canary, never an empty list (which would be indistinguishable from "this
      checker was skipped").
  (2) FOUND BROKEN — every one of those rows must be BROKEN, not PASS.
A THIRD canary (CRASH, not unconditional-accept) checks the OTHER failure mode this tool's own
run_checker() promises to fail closed on: a checker that raises an exception on every input,
including its own accept-known-good document, must be reported BROKEN with a raw-traceback detail —
never silently treated as "PASS" (a crash is not evidence of a correct rejection) and never treated
as an ordinary poison-was-accepted BROKEN row without saying so.
"""
import dataclasses
import re
import sys
import tempfile

sys.path.insert(0, ".")
from mutation_poison_gen import Classifier, evaluate_checker
import mutation_poison_configs as cfgmod


def unconditional_accept(source, entry_is_main):
    """Replace the checker's entire logic with something that accepts everything, keeping the
    source PARSEABLE (so extraction/classification of the REAL source, done separately, is
    unaffected — only the code that actually RUNS against poison is replaced)."""
    if entry_is_main:
        return "import sys\ndef main():\n    return 0\nif __name__=='__main__':\n    sys.exit(main())\n"
    return "import sys\nsys.exit(0)\n"


def always_crash(source, entry_is_main):
    if entry_is_main:
        return "import sys\ndef main():\n    raise ValueError('generator_canary: deliberate crash')\nif __name__=='__main__':\n    sys.exit(main())\n"
    return "import sys\nraise ValueError('generator_canary: deliberate crash')\n"


def run_canary(name, checker_name, entry_is_main, tmproot):
    cfg = cfgmod.CHECKERS[checker_name]
    real_source = cfg.source_fn()
    findings = Classifier(real_source, filename=checker_name).run()

    results = {}
    for label, builder in (("unconditional-accept", unconditional_accept), ("crash", always_crash)):
        mutant_source = builder(real_source, entry_is_main)
        mutant_cfg = dataclasses.replace(cfg, source_fn=(lambda s=mutant_source: s))
        rows, unresolved = evaluate_checker(mutant_cfg, findings, tmproot)
        results[label] = rows
    return results


def main():
    tmproot = tempfile.mkdtemp(prefix="generator-canary-")
    shapes = [
        ("EMBEDDED/pyvar", "VD_PY", False),
        ("EMBEDDED/bashfunc", "ck83_defect", False),
        ("STANDALONE/extfile", "incomplete_check.py", True),
    ]
    ok = True
    print("GENERATOR CANARY — proves mutation_poison_gen.py can report BROKEN, in every shape it "
          "covers, and does not mistake a crash for a pass\n")
    for shape, checker_name, entry_is_main in shapes:
        print(f"--- {shape} ({checker_name}) ---")
        results = run_canary(shape, checker_name, entry_is_main, tmproot)

        rows = results["unconditional-accept"]
        if not rows:
            print(f"  FAIL: unconditional-accept mutant produced ZERO rows — a canary that is not even "
                  f"FOUND (evaluated) is worse than one found broken")
            ok = False
        else:
            # the accept-known-good row is EXPECTED to stay PASS here — an unconditional-accept
            # mutant correctly (if vacuously) accepts a valid document too, same as it accepts
            # everything else. Only the POISON-rejection rows are the signal: those must ALL flip to
            # BROKEN, because a checker that accepts everything necessarily fails to reject poison.
            # "recognised, not degradable" rows are a synthetic PASS the generator emits for a
            # presence-over-SCALAR container (a free-text CLI arg, e.g. `"X" in out`) — no checker
            # invocation happens for them at all (see evaluate_checker's SHAPE_PRESENCE branch), so
            # they can never flip to BROKEN and are not part of this control's claim.
            poison_rows = [r for r in rows if "(accept-known-good)" not in r.label
                           and r.detail != "recognised, not degradable"]
            broken = [r for r in poison_rows if r.status != "PASS"]
            if poison_rows and len(broken) == len(poison_rows):
                print(f"  OK: unconditional-accept mutant — ALL {len(poison_rows)} poison row(s) "
                      f"reported BROKEN (found, and found broken); the accept-known-good row still "
                      f"correctly reads PASS")
            else:
                still_pass = [r.label for r in poison_rows if r.status == "PASS"]
                print(f"  FAIL: unconditional-accept mutant — {len(poison_rows) - len(broken)}/"
                      f"{len(poison_rows)} poison row(s) still read PASS against a checker that "
                      f"accepts EVERYTHING: {still_pass}")
                ok = False

        rows = [r for r in results["crash"] if r.detail != "recognised, not degradable"]
        if not rows:
            print(f"  FAIL: crash mutant produced ZERO rows")
            ok = False
        else:
            all_broken_with_crash_evidence = all(
                r.status != "PASS" and ("CRASHED" in r.detail or "generator_canary: deliberate crash" in r.detail)
                for r in rows)
            if all_broken_with_crash_evidence:
                print(f"  OK: crash mutant — ALL {len(rows)} row(s) reported BROKEN with crash evidence "
                      f"(never silently treated as a correct rejection)")
            else:
                bad = [(r.label, r.status, r.detail[:80]) for r in rows
                       if r.status == "PASS" or "CRASHED" not in r.detail and "deliberate crash" not in r.detail]
                print(f"  FAIL: crash mutant — {len(bad)} row(s) did not carry BROKEN+crash-evidence: {bad}")
                ok = False
        print()

    if ok:
        print("generator_canary: OK — every shape reports BROKEN on an unconditional-pass checker, and "
              "a crash is never mistaken for a correct rejection.")
        return 0
    print("generator_canary: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
