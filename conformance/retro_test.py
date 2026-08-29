#!/usr/bin/env python3
"""
retro_test.py — CALIBRATION: does mutation_poison_gen.py rediscover the eleven comparison-shape
bypasses (A1-A5, S1-S6) mutation-gate.sh's own header documents finding by hand this session?

[[candor-oracle-disclosure-recall]] applied to itself: "0 violations is not evidence until the
instrument is proven able to fail" — a generator that cannot re-find a KNOWN bug is not calibrated,
however plausible its design reads.

METHOD. mutation-gate.sh's eleven bypasses were originally reproduced by degrading the GATE'S OWN
FIXTURES (an insufficiently-discriminating poison), never by editing conformance/run.sh's checkers —
those were correct throughout (confirmed: `git log --oneline -- conformance/run.sh` around the dates
in mutation-gate.sh's header shows no commit touching run.sh's checker bodies while the gate itself
was hardened three times). The generative equivalent of "a fixture too weak to catch this" is "a
CHECKER degraded to this shape would slip past the poison" — so this file takes the OPPOSITE
direction from the fixture history: classify the REAL (correct, current) checker source exactly as
mutation_poison_gen.py already does, generate poison from it, then apply the EXACT textual
degradation each bypass paragraph names to a COPY of the checker source and confirm:
    - the REAL checker REJECTS the generated poison (already proven by the main run — mutation_poison_
      gen.py's own over-charge control), and
    - the MUTATED checker WRONGLY ACCEPTS the SAME, mechanically-generated poison.
Finding the SAME divergence the hand-authored fixture found, from a poison NOBODY hand-wrote for that
bug, is what "the generator would have produced A1-S6 in one pass" (mutation-gate.sh's own closing
claim) actually means, made falsifiable rather than asserted.

SCOPE. Ten of the eleven are covered. A5 (VD_PY's `unev` mode, a list-comprehension projection) is a
documented, waived generalisation gap (see mutation_poison_configs.py's WAIVERS) — reported here as
NOT ATTEMPTED, not silently passed over. B1-B3 are a different kind of finding (the OLD gate's
fixtures were absence-shaped, not a checker degradation) and are not "mutant of the checker" shaped in
the first place; not reproduced here for that reason, stated rather than hidden.
"""
import dataclasses
import re
import sys
import tempfile

sys.path.insert(0, ".")
from mutation_poison_gen import Classifier, evaluate_checker, GeneratorError, ExtractionError
import mutation_poison_configs as cfgmod

# (bypass id, checker name, human description, regex pattern, replacement, finding-match predicate)
# finding-match: (lineno, shape, snippet-substring) — identifies WHICH finding's near-miss family
# must flip from PASS (against the real checker) to BROKEN (against the mutant) for this bypass to
# count as rediscovered. A mutation that does not even change the source text is a hard failure
# below (AGENT-CORPUS-BRIEF.md: "prove the fixture reached the code").
BYPASSES = [
    ("A1-ok0", "VD_PY", 'is-not-False degraded to plain truthiness',
     r'd\.get\("ok"\) is not False', r'd.get("ok")', 6),
    ("A1-okt", "VD_PY", 'is-not-True degraded to falsy check',
     r'd\.get\("ok"\) is not True', r'not d.get("ok")', 7),
    ("S1-refused", "VD_PY", 'is-True degraded to plain truthiness',
     r'd\.get\("refused"\) is True', r'd.get("refused")', 8),
    ("S2-zm", "VD_PY", 'exact list-equality degraded to membership',
     r'got!=\[want\[3:\]\]', r'want[3:] not in (got or [])', 18),
    ("S6-v005", "VD_PY", 'string equality (in any()) degraded to substring membership',
     r'v\.get\("rule"\)=="AS-EFF-005"', r'"AS-EFF-005" in (v.get("rule") or "")', 11),
    ("A2-functions", "RS_PY_FAILCLOSED", '== [] degraded to a falsy check',
     r'd\.get\("functions"\) == \[\]', r'not d.get("functions")', 4),
    ("A2-count", "RS_PY_FAILCLOSED", '== 0 degraded to a falsy check',
     r'\(d\.get\("analyzed"\) or \{\}\)\.get\("count"\) == 0',
     r'not (d.get("analyzed") or {}).get("count")', 5),
    ("A3-CHAN-isinstance", "CHAN_PY", 'isinstance(list) guard dropped',
     r'not isinstance\(d\.get\("judgedNothing"\),list\) or not d\["judgedNothing"\]',
     r'not d.get("judgedNothing")', 6),
    ("CHAN-incomplete-identity", "CHAN_PY", 'is-not-True degraded to falsy check (named in the '
     'header prose alongside A3, not lettered)',
     r'd\.get\("incomplete"\) is not True', r'not d.get("incomplete")', 7),
    ("A4-r_zm", "ck83_defect", 'exact list-equality degraded to membership',
     r'r_zm != \[scope\]', r'scope not in (r_zm or [])', 24),
    ("S3-s_ok", "ck83_defect", 'is-not-True degraded to plain-not',
     r's_ok is not True', r'not s_ok', 19),
    ("S3-r_ok", "ck83_defect", 'is-not-True degraded to plain-not',
     r'r_ok is not True', r'not r_ok', 22),
    ("S4-s_viol", "ck83_defect", '!= [] degraded to plain truthiness',
     r's_viol != \[\]', r's_viol', 20),
    ("S4-r_viol", "ck83_defect", '!= [] degraded to plain truthiness',
     r'r_viol != \[\]', r'r_viol', 23),
    ("S5-d_ok", "ck83_control", 'is-not-False degraded to plain truthiness',
     r'd_ok is not False', r'd_ok', 11),
]


def run():
    tmproot = tempfile.mkdtemp(prefix="retro-test-")
    results = []
    source_cache = {}   # extract_pyvar/extract_bashfunc_pyc parse the WHOLE of run.sh (~7s) — several
                         # bypasses share a checker, so cache per checker name rather than re-extract.
    for bid, checker_name, desc, pattern, repl, target_lineno in BYPASSES:
        cfg = cfgmod.CHECKERS[checker_name]
        try:
            if checker_name not in source_cache:
                source_cache[checker_name] = cfg.source_fn()
            real_source = source_cache[checker_name]
        except (ExtractionError, GeneratorError) as e:
            results.append((bid, "ERROR", f"could not extract {checker_name}: {e}"))
            continue
        mutant_source, n = re.subn(pattern, repl, real_source, count=1)
        if n == 0:
            results.append((bid, "ERROR", f"the retro-test's OWN mutation pattern {pattern!r} did not "
                                           f"match {checker_name}'s CURRENT source — the checker was "
                                           f"edited since this bypass was documented, or the pattern is "
                                           f"wrong. This is a hard failure of the CONTROL, not a finding."))
            continue
        if mutant_source == real_source:
            results.append((bid, "ERROR", "pattern matched but produced an IDENTICAL string — the "
                                           "mutation did not reach the code (prove-the-fixture-reaches rule)"))
            continue

        findings = Classifier(real_source, filename=checker_name).run()
        target = [f for f in findings if f.lineno == target_lineno and f.path is not None]
        if not target:
            results.append((bid, "ERROR", f"no resolved finding at {checker_name}:{target_lineno} — "
                                           f"the classifier no longer sees this condition at all"))
            continue

        mutant_cfg = dataclasses.replace(cfg, source_fn=(lambda s=mutant_source: s))
        rows, unresolved = evaluate_checker(mutant_cfg, findings, tmproot)
        # a row's label embeds "L{lineno} {shape}[...]" — match on the target line to find the
        # specific near-miss legs this bypass's finding produced against the MUTANT.
        relevant_rows = [r for r in rows if f"L{target_lineno} " in r.label and "(accept-known-good)" not in r.label]
        if not relevant_rows:
            results.append((bid, "ERROR", f"no rows were generated for L{target_lineno} against the mutant"))
            continue
        flipped = [r for r in relevant_rows if r.status != "PASS"]  # PASS here means "correctly rejected" —
        # against a MUTATED (buggy) checker we WANT the opposite: a poison that used to be correctly
        # rejected by the real checker must now be wrongly ACCEPTED, i.e. this tool's own PASS/BROKEN
        # semantics (which are keyed to "checker behaves correctly") report the desired rediscovery as
        # a BROKEN row — that IS the finding, not a defect in this run.
        if flipped:
            results.append((bid, "REDISCOVERED", f"{desc} — {len(flipped)}/{len(relevant_rows)} near-miss "
                                                  f"leg(s) at L{target_lineno} now pass the MUTANT (would "
                                                  f"have been silently accepted): "
                                                  + "; ".join(r.label.split(") ", 1)[-1] for r in flipped)))
        else:
            results.append((bid, "MISSED", f"{desc} — the mutant STILL correctly rejected every generated "
                                            f"near-miss at L{target_lineno}; this generator would NOT have "
                                            f"caught this historical bypass"))
    return results


def main():
    results = run()
    print("RETRO-TEST — does the generator rediscover the eleven known comparison-shape bypasses?\n")
    for bid, status, detail in results:
        print(f"  {status:14} {bid:20} {detail}")
    rediscovered = [r for r in results if r[1] == "REDISCOVERED"]
    missed = [r for r in results if r[1] == "MISSED"]
    errors = [r for r in results if r[1] == "ERROR"]
    print(f"\n  {len(rediscovered)}/{len(results)} rediscovered, {len(missed)} missed, {len(errors)} control error(s)")
    print("  NOT attempted (documented, waived generalisation gap): A5 (VD_PY `unev`, list-comprehension "
          "projection) — see mutation_poison_configs.py's WAIVERS.")
    print("  NOT attempted (different finding shape, not a checker-comparison degradation): B1, B2, B3 — "
          "see this file's own header.")
    if errors or missed:
        print("\nretro_test: FAILED — the generator is not calibrated (or the control itself is stale).")
        return 1
    print("\nretro_test: OK — every attempted historical bypass was independently rediscovered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
