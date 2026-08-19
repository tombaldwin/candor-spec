#!/usr/bin/env python3
"""
A PROPERTY MUST STILL BE ABLE TO FAIL. THIS RUNS EACH ONE WITH A DELIBERATE FAULT AND CHECKS THAT IT DOES.

WHY THIS EXISTS — the failure it is built for, stated as it happened
--------------------------------------------------------------------
"Verified to catch" has been the standing bar for every property in this suite, and it has always been a
habit applied ONCE, by hand, at authoring time: break the engine, watch the property go red, restore,
never check again. Nothing re-ran it. So a property that quietly stops discriminating — because a fixture
drifted, a guard was widened, or the shape it keys on moved — keeps printing MATCH forever, and the suite
reports a green that means nothing.

That is not hypothetical. On 2026-08-03 a single session found:
  · THREE waivers accusing engines that CONFORM (two in `rung024`, one in trust-monotonicity's framing);
  · row R10 demanding report fields that §2 marks OPTIONAL, for its entire existence;
  · P6's conjunct B falsely accusing candor-swift on an ordinary `extension Process { … }`;
  · the dispatch-frontier differential running TWO independent consumers while printing three arms.
Every one was an instrument that had stopped meaning what it claimed, and every one was found by
accident — while doing something else. None was found by the suite.

WHAT IT CHECKS
--------------
Each registered generator honours `CANDOR_PROBE_FAULT`. When set, it corrupts the FIRST live cell in the
direction its property forbids — a total undisclosed loss for split-invariance, a dropped arm for chain
idempotence, a lost disclosure for the sidecar manifest — announces the injection, and continues. The
property MUST then fail. If it passes, the property is not discriminating and this check fails the suite.

Run WITHOUT a baseline, deliberately: a ratchet waiver could otherwise mask the injected cell and make
the probe flaky. Raw truth is the right oracle for "can this still fail at all".

COVERAGE IS PARTIAL AND SAYS SO. `COVERED` lists the generators that honour the fault; `UNCOVERED` names
the rest with the reason. A silent gap here would be the same defect one level up — an instrument that
looks complete and is not — so the gap is printed on every run.

    python3 probe_check.py            # exit non-zero if any covered property survives its fault
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# generator -> the flags that keep the probe run SHORT. A probe needs one live cell, not the full matrix.
COVERED = {
    "gen_split_invariance.py":        ["--only", "local_call"],
    "gen_chain_idempotence.py":       ["--only", "local_call"],
    "gen_signature_monotonicity.py":  [],
    "gen_sidecar_manifest.py":        [],
    "gen_fs_kind.py":                 [],
    # One engine is enough to reach a live cell; the fault fires on the first out-of-scope exit 2.
    "gen_policy_matrix.py":           ["--engine", "rust"],
}

# Not yet wired, with the reason. These are NOT excused — they are the next batch of work.
UNCOVERED = {
    "gen_trust_monotonicity.py":   "judge() takes four arms; the injection has to pick one without "
                                   "colliding with the BESIDE arm's inverted direction — needs care",
    "gen_incomplete_dominance.py": "verdict is read from an exit code + a verdict file, so the fault "
                                   "belongs at the gate-invocation layer, not in a judge()",
    "gen_rung024.py":              "27 heterogeneous rows; each needs its own fault to be meaningful",
    "gen_differential.py":         "expected-value table — a wrong answer IS the failing case, so the "
                                   "fault must corrupt an ENGINE's answer rather than a comparison",
    "gen_completeness.py":         "as gen_differential.py",
    "gen_masking.py":              "as gen_differential.py",
    "gen_netclass.py":             "as gen_differential.py",
    "gen_policy_match.py":         "as gen_differential.py",
    # Filed by the disk enumeration the day it was added — both had been in NEITHER set, which is the
    # state the enumeration exists to make impossible.
    "gen_key_shapes.py":           "harvests the wire vocabulary from live documents and asserts one "
                                   "JSON type per key; a fault must corrupt a HARVESTED document rather "
                                   "than a comparison, so the injection belongs at the emitter",
    "gen_sink_surface.py":         "derives its matrix from each binary's --help and drives real argv; "
                                   "the fault has to make a BINARY mishandle a sink, which is the "
                                   "gen_differential.py shape one layer out",
}


def main():
    print("PROBE CHECK — every registered property must FAIL when its own assertion is violated")
    # EVERY GENERATOR ON DISK MUST BE IN ONE SET OR THE OTHER. This iterated COVERED alone, so a
    # generator in neither was invisible: not probed, and not listed as unprobed either. That is the
    # allowlist failure this suite argues against everywhere else — `gen_policy_matrix.py` sat in that
    # gap the day it was written, which is exactly when a new property is least trustworthy.
    on_disk = {f for f in os.listdir(HERE) if f.startswith("gen_") and f.endswith(".py")}
    unfiled = sorted(on_disk - set(COVERED) - set(UNCOVERED))
    if unfiled:
        print(f"  ✘ generator(s) in NEITHER set — probe-covered or listed as not-yet with a reason, "
              f"there is no third option: {', '.join(unfiled)}")
        return 1
    env = dict(os.environ, CANDOR_PROBE_FAULT="1")
    bad = []
    for gen, args in sorted(COVERED.items()):
        path = os.path.join(HERE, gen)
        if not os.path.exists(path):
            print(f"  ✘ {gen}: missing — a registered probe target that is not there is a broken registry")
            bad.append(gen)
            continue
        r = subprocess.run([sys.executable, path, *args], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = r.stdout.decode(errors="replace")
        injected = "PROBE:" in out
        if r.returncode != 0 and injected:
            print(f"  ✔ {gen}: fails under its own fault (exit {r.returncode})")
        elif not injected:
            # The fault never fired: the property ran, but nothing was corrupted, so the exit code says
            # nothing either way. Distinguished from a real survival because the fixes differ.
            print(f"  ✘ {gen}: the fault NEVER FIRED — no live cell reached the injection point, so this "
                  f"probe proves nothing (fixture drift, or the injection is in the wrong place)")
            bad.append(gen)
        else:
            print(f"  ✘ {gen}: SURVIVED its own fault (exit 0) — the property is not discriminating")
            bad.append(gen)

    print(f"\n  not yet probed ({len(UNCOVERED)}), with reasons — this gap is printed, never implied:")
    for gen, why in sorted(UNCOVERED.items()):
        print(f"    · {gen}: {why}")

    if bad:
        print(f"\nPROBE CHECK: FAILED — {len(bad)} property(ies) did not demonstrate they can fail.")
        return 1
    print(f"\nPROBE CHECK: OK — {len(COVERED)} propert(ies) each failed when its own assertion was violated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
