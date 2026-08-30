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

WHAT IT CHECKS, AND WHY IT IS NOW TWO-ARMED
-------------------------------------------
Each registered generator honours `CANDOR_PROBE_FAULT`. When set, it corrupts the FIRST live cell in the
direction its property forbids — a total undisclosed loss for split-invariance, a dropped arm for chain
idempotence, a lost disclosure for the sidecar manifest — announces the injection, and continues.

THIS FILE ONCE ACCEPTED "`PROBE:` APPEARED IN THE OUTPUT, AND THE EXIT WAS NON-ZERO". That is a claim
about a run's OUTPUT SHAPE, not about the property, and a four-agent review on 2026-08-30 broke it in one
move: replace all eight generators with three-line bodies that `print("PROBE: …"); sys.exit(1)` and this
check printed `PROBE CHECK: OK — 8 propert(ies)`, exit 0. REPRODUCED before this rewrite. The instrument
built to prove our instruments can fail was the one instrument that could not.

The evidence is now the PROPERTY'S OWN VERDICT, measured in both directions, with `CANDOR_PROBE_FAULT`
the only thing that differs between the two runs:

    CLEAN arm (no fault)   MUST exit 0, MUST print the property's own PASS verdict (`holds`),
                           MUST NOT print its FAILURE verdict (`breaks`), and MUST NOT announce a PROBE.
    FAULT arm              MUST announce `PROBE:`, MUST exit non-zero, MUST print the property's own
                           FAILURE verdict, and MUST NOT still print its PASS verdict.

The clean arm is not ceremony — it is the arm that catches the realistic drift. A generator whose fixture
moved under it CRASHES with a traceback: it prints `PROBE:` on the way past the injection point and exits
1, which the old check scored `✔ fails under its own fault`. It is not failing under its fault; it is
failing regardless, and the property behind it is dead. Only a green unfaulted run distinguishes the two.

`holds`/`breaks` are the generator's own verdict sentences, not this file's opinion of them. Where a
property has no OK/FAILED token its COUNT is the discriminator and the pattern pins the value (`0
disagreement(s)` vs `[1-9]… disagreement(s)`), which is the near-miss discipline the mutation gate uses:
presence of a key proves the checker looked, only its VALUE proves the checker read.

WHAT THIS STILL CANNOT DO, stated rather than implied: a generator deliberately written to fake both
verdict sentences under the exact env var would pass. That is forgery, not drift, and no cheap check
distinguishes it. What the two arms DO bind is every way a property stops discriminating by accident.

COVERAGE IS PARTIAL AND SAYS SO — AND IT HAS A FLOOR. `COVERED` lists the generators that honour the
fault; `UNCOVERED` names the rest with the reason; every generator on disk must be in exactly one. The
same review found the table had no minimum: move two entries back to UNCOVERED and it printed
`OK — 6 properties`, exit 0, a shrinking coverage table rendered as a smaller green number. `COVERED_FLOOR`
below is an EXACT-MATCH ratchet, so a table that grows fails too until the floor is raised in the same
commit. A floor that follows its own measurement is not a floor.

    python3 probe_check.py            # exit non-zero if any covered property fails either arm
    python3 probe_check.py --selftest # attack judge() with synthetic arms; runs no generator
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# generator -> how to probe it.
#   args    — the flags that keep the probe run SHORT. A probe needs one live cell, not the full matrix.
#   holds   — the property's OWN pass verdict. Required in the clean arm, forbidden in the fault arm.
#   breaks  — the property's OWN failure verdict. Required in the fault arm, forbidden in the clean arm.
COVERED = {
    "gen_split_invariance.py": {
        "args":   ["--only", "local_call"],
        "holds":  r"P1 SPLIT-INVARIANCE: OK",
        "breaks": r"P1 SPLIT-INVARIANCE: FAILED",
    },
    "gen_chain_idempotence.py": {
        "args":   ["--only", "local_call"],
        "holds":  r"P2 CHAIN IDEMPOTENCE: OK",
        "breaks": r"P2 CHAIN IDEMPOTENCE: FAILED",
    },
    "gen_trust_monotonicity.py": {
        "args":   ["--only", "local_call"],
        "holds":  r"P3 TRUST MONOTONICITY: OK",
        "breaks": r"P3 TRUST MONOTONICITY: FAILED",
    },
    "gen_signature_monotonicity.py": {
        "args":   [],
        "holds":  r"P4 SIGNATURE MONOTONICITY: OK",
        "breaks": r"P4 SIGNATURE MONOTONICITY: FAILED",
    },
    "gen_incomplete_dominance.py": {
        "args":   ["--only", "rust"],
        "holds":  r"P5 INCOMPLETE-VS-VIOLATION DOMINANCE: OK",
        "breaks": r"P5 INCOMPLETE-VS-VIOLATION DOMINANCE: FAILED",
    },
    "gen_sidecar_manifest.py": {
        "args":   [],
        "holds":  r"P6 OK — \d+ live consumer cells",
        "breaks": r"^FAIL: ",
    },
    # No OK/FAILED token: the summary line is the same sentence in both arms and the COUNT is the
    # verdict, so the patterns pin the VALUE. `[1-9]\d*` deliberately, never `\d+` — a `breaks` that
    # also matches `0 divergence(s)` would be satisfied by the passing arm.
    "gen_fs_kind.py": {
        "args":   [],
        "holds":  r"fs read/write refinement agrees on \d+ cell\(s\)",
        "breaks": r"-> [1-9]\d* divergence\(s\) over \d+ cell\(s\)",
    },
    # One engine is enough to reach a live cell; the fault fires on the first out-of-scope exit 2.
    "gen_policy_matrix.py": {
        "args":   ["--engine", "rust"],
        "holds":  r"policy matrix: \d+ cell\(s\) over \d+ engine\(s\), 0 disagreement\(s\)",
        "breaks": r"policy matrix: \d+ cell\(s\) over \d+ engine\(s\), [1-9]\d* disagreement\(s\)",
    },
}

# THE COVERAGE RATCHET. Exact match, and deliberately a hand-written constant rather than anything
# derived from the table it guards: `len(COVERED)` compared against itself is the two-sided drift that
# makes a ratchet vacuous. Moving a generator to UNCOVERED, or adding one, must edit THIS LINE too — the
# shrink cannot be a side effect of an ordinary-looking edit somewhere else.
COVERED_FLOOR = 8

# Not yet wired, with the reason. These are NOT excused — they are the next batch of work.
UNCOVERED = {
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


def judge(spec, clean_rc, clean_out, fault_rc, fault_out):
    """The whole verdict, as a pure function of two arms. Returns a list of problem strings; empty = OK.

    Kept separate from the running so `--selftest` can attack it directly with synthetic arms — the
    generator run is UPSTREAM of the comparison, so its cost is not this check's cost (AGENT-CORPUS-BRIEF
    attack M). Every condition below was reproduced against a real degenerate generator before it was
    written; none is here on the theory that it might matter."""
    holds, breaks = spec["holds"], spec["breaks"]
    p = []
    # ── the CLEAN arm: the property must be GREEN with nothing wrong. ───────────────────────────────
    if clean_rc != 0:
        p.append(f"the UNFAULTED run already fails (exit {clean_rc}) — its failure under the fault says "
                 f"nothing, because it fails either way (fixture drift, a crash, or a real divergence)")
    if "PROBE:" in clean_out:
        p.append("the UNFAULTED run announced a PROBE — the injection is not gated on CANDOR_PROBE_FAULT, "
                 "so the suite has been running corrupted cells")
    if not re.search(holds, clean_out, re.M):
        p.append(f"the UNFAULTED run never printed its own pass verdict /{holds}/ — this run's evidence is "
                 f"not the property's verdict, so a non-zero exit under the fault proves nothing")
    if re.search(breaks, clean_out, re.M):
        p.append(f"the UNFAULTED run printed its own FAILURE verdict /{breaks}/ — the two arms are not "
                 f"distinguishable, so the fault arm cannot be evidence")
    # ── the FAULT arm: red, and red THROUGH THE PROPERTY. ──────────────────────────────────────────
    if "PROBE:" not in fault_out:
        p.append("the fault NEVER FIRED — no live cell reached the injection point (fixture drift, or the "
                 "injection is in the wrong place)")
    if fault_rc == 0:
        p.append("SURVIVED its own fault (exit 0) — the property is not discriminating")
    if not re.search(breaks, fault_out, re.M):
        p.append(f"failed, but NOT through its own verdict /{breaks}/ — a non-zero exit with no property "
                 f"failure behind it is a crash wearing a green tick")
    if re.search(holds, fault_out, re.M):
        p.append(f"still printed its PASS verdict /{holds}/ under the fault — the corrupted cell did not "
                 f"reach the assertion")
    return p


def _selftest():
    """Attack judge() with the exact shapes that defeated this file, plus the one that must pass.

    A checker whose only proof is 'the real thing was green today' is the habit this file exists to
    replace, so its own comparison is asserted against synthetic arms that need no engine."""
    spec = {"holds": r"P9 THING: OK", "breaks": r"P9 THING: FAILED"}
    OKC, OKF = "rows\nP9 THING: OK\n", "  PROBE: injected\nrows\nP9 THING: FAILED\n"
    cases = [
        ("known-good two arms", (spec, 0, OKC, 1, OKF), True),
        # THE 2026-08-30 REVIEW'S STUB, verbatim in behaviour: PROBE text plus a non-zero exit, no
        # property anywhere. The whole reason this file was rewritten.
        ("stub: PROBE text + exit 1, no verdict", (spec, 1, "PROBE: honest\n", 1, "PROBE: honest\n"), False),
        # The same stub made cleverer: silent and green when unfaulted. Still has no verdict to show.
        ("stub: green clean, red fault, no verdict", (spec, 0, "", 1, "PROBE: x\n"), False),
        # The realistic drift: the generator crashes, printing PROBE on the way past the injection.
        ("crashes in BOTH arms", (spec, 1, "Traceback\n", 1, "  PROBE: injected\nTraceback\n"), False),
        ("fault never fired", (spec, 0, OKC, 1, "P9 THING: FAILED\n"), False),
        ("survived its fault", (spec, 0, OKC, 0, "  PROBE: injected\nP9 THING: OK\n"), False),
        ("injection not gated on the env var", (spec, 0, "PROBE: x\n" + OKC, 1, OKF), False),
        ("clean arm already prints the failure", (spec, 0, "P9 THING: FAILED\n" + OKC, 1, OKF), False),
    ]
    bad = 0
    for name, args, want_ok in cases:
        got_ok = not judge(*args)
        mark = "ok " if got_ok == want_ok else "BAD"
        if got_ok != want_ok:
            bad += 1
        print(f"  {mark} judge() {'accepts' if got_ok else 'rejects'} — {name}")
    # The floor must itself be able to fail, or it is the defect one level up.
    if COVERED_FLOOR != len(COVERED):
        print(f"  BAD the coverage ratchet is already out of step: COVERED_FLOOR={COVERED_FLOOR}, "
              f"len(COVERED)={len(COVERED)}")
        bad += 1
    else:
        print(f"  ok  the coverage ratchet is armed at exactly {COVERED_FLOOR}")
    print("PROBE CHECK SELFTEST: " + ("OK" if not bad else f"FAILED — {bad} case(s)"))
    return 1 if bad else 0


def main():
    if "--selftest" in sys.argv[1:]:
        return _selftest()
    print("PROBE CHECK — every registered property must PASS clean and FAIL, through its own verdict, "
          "when its assertion is violated")
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
    # THE COVERAGE RATCHET, before any probe runs: a table that shrank has already lost the property it
    # is about to report on, and reporting a smaller green number is exactly how that goes unnoticed.
    if len(COVERED) != COVERED_FLOOR:
        direction = ("SHRANK — a probe-covered property was moved back to UNCOVERED (or deleted). That is "
                     "a LOSS of coverage and must never render as a smaller green number"
                     if len(COVERED) < COVERED_FLOOR else
                     "GREW — raise COVERED_FLOOR in the same commit, so the next shrink still has a floor "
                     "to fail against")
        print(f"  ✘ COVERAGE RATCHET: COVERED holds {len(COVERED)} propert(ies), COVERED_FLOOR says "
              f"{COVERED_FLOOR}. The table {direction}.")
        return 1
    env_fault = dict(os.environ, CANDOR_PROBE_FAULT="1")
    env_clean = {k: v for k, v in os.environ.items() if k != "CANDOR_PROBE_FAULT"}
    bad = []
    for gen, spec in sorted(COVERED.items()):
        path = os.path.join(HERE, gen)
        if not os.path.exists(path):
            print(f"  ✘ {gen}: missing — a registered probe target that is not there is a broken registry")
            bad.append(gen)
            continue
        # The registry names the property's verdict sentences; the generator must be the thing that
        # honours the fault at all. A COVERED entry whose file never reads the env var is a registry
        # that has drifted off its source, and it would otherwise surface only as "the fault never fired".
        src = open(path, encoding="utf-8", errors="replace").read()
        if "CANDOR_PROBE_FAULT" not in src:
            print(f"  ✘ {gen}: registered as probe-covered, but its SOURCE never reads CANDOR_PROBE_FAULT "
                  f"— there is no injection here to prove anything with")
            bad.append(gen)
            continue

        def run(env):
            r = subprocess.run([sys.executable, path, *spec["args"]], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode(errors="replace")

        # THE ONLY THING THAT DIFFERS BETWEEN THE ARMS IS CANDOR_PROBE_FAULT. Same argv, same cwd, same
        # environment otherwise — a comparison whose arms differ in two variables is not evidence.
        clean_rc, clean_out = run(env_clean)
        fault_rc, fault_out = run(env_fault)
        problems = judge(spec, clean_rc, clean_out, fault_rc, fault_out)
        if not problems:
            print(f"  ✔ {gen}: green unfaulted (exit 0, own pass verdict), and its own FAILURE verdict "
                  f"under the fault (exit {fault_rc})")
        else:
            bad.append(gen)
            print(f"  ✘ {gen}: (clean exit {clean_rc}, fault exit {fault_rc})")
            for why in problems:
                print(f"      · {why}")

    print(f"\n  not yet probed ({len(UNCOVERED)}), with reasons — this gap is printed, never implied:")
    for gen, why in sorted(UNCOVERED.items()):
        print(f"    · {gen}: {why}")

    if bad:
        print(f"\nPROBE CHECK: FAILED — {len(bad)} property(ies) did not demonstrate they can fail.")
        return 1
    print(f"\nPROBE CHECK: OK — {len(COVERED)} propert(ies) (floor {COVERED_FLOOR}) each passed clean and "
          f"failed through its own verdict when its assertion was violated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
