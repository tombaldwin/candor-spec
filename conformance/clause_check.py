#!/usr/bin/env python3
"""
A PROPERTY MUST QUOTE THE CLAUSE IT ENFORCES, AND THE QUOTE MUST RESOLVE IN SPEC.md.

WHY THIS EXISTS — the failure it is built for, stated as it happened
--------------------------------------------------------------------
PART 29 (P5) was extended with a ROUTE x TRIGGER matrix. It put 8 cells red across all four engines, and
those 8 were waived in the ratchet as known-broken engine defects, with per-cell prose explaining each.
Reading the clauses AFTERWARDS, all eight were the property being STRICTER THAN THE CONTRACT:

  · the `count0` trigger asserted that a judged-nothing report must not exit 0 from `gate --report`.
    SPEC §2 binds that rule to the verb "AS A DISCLOSURE, NOT AS AN EXIT CODE" — *"The exit code and the
    verdict document are UNCHANGED"*, and *"Refusing with exit 2 is not an available reading"*. The
    clause even records that it FIRST said the opposite and was corrected. All four engines were right.
  · the `malformed` trigger demanded a violation "dominate" over a document whose signature key was
    unreadable. §2 says such a document is impeached — *"One unreadable among them means the document's
    claim cannot be trusted … Refuse."* Three engines emitted the §3.1 refusal shape and were right.

**The act of finding the quote IS the check.** To write the citation for `count0`, someone must open §2
and read the sentence that contradicts the assertion. Ten minutes went into those waivers; two minutes
would have gone into the clauses.

WHY A WRONG WAIVER IS WORSE THAN A WRONG QUEUE ENTRY, which is what makes this worth a gate rather than a
resolution: a waiver records a CONFORMING engine as known-broken, inside the file whose entire job is to
be trusted later, **and it makes the suite go green over the accusation.** It is a wrong diagnosis with an
expiry date attached.

WHAT THIS CHECKS
----------------
1. Every generator listed below declares `SPEC_CLAUSES` — (anchor, verbatim fragment) pairs naming the
   normative text it enforces. Each fragment MUST appear in SPEC.md, whitespace-normalised.
2. Every baseline waiver's `why` MUST cite a section (`§…`). A waiver says "this engine violates the
   contract"; it should name the part of the contract it violates.

DELIBERATELY NOT CHECKED: that the fragment *implies* the assertion. No script can do that. What it can
do is force a human to hold the sentence and the assertion in view at the same moment, which is the step
that was skipped — and it fails LOUDLY when a clause is later reworded, which is the other way a property
drifts away from the contract it claims to test.

    python3 clause_check.py            # exit non-zero on any unresolvable citation
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "..", "SPEC.md")

# Generators that assert a normative MUST. A property that enforces nothing normative (a pure
# self-differential over one engine's own output, say) is exempt and simply declares no clauses — but it
# must still be LISTED, so "I forgot to add my generator" and "my generator needs no clauses" are
# distinguishable.
GENERATORS = [
    "gen_split_invariance.py",
    "gen_chain_idempotence.py",
    "gen_trust_monotonicity.py",
    "gen_signature_monotonicity.py",
    "gen_incomplete_dominance.py",
    "gen_sidecar_manifest.py",
]

BASELINES = [
    "split-invariance-baseline.json",
    "chain-idempotence-baseline.json",
    "trust-monotonicity-baseline.json",
    "signature-monotonicity-baseline.json",
    "incomplete-dominance-baseline.json",
    "sidecar-manifest-baseline.json",
]


def norm(s):
    """Whitespace-normalised, so a fragment survives the spec being re-wrapped."""
    return re.sub(r"\s+", " ", s).strip()


def load_module(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    m = importlib.util.module_from_spec(spec)
    # The generators run their work inside main(); importing is side-effect free.
    spec.loader.exec_module(m)
    return m


def main():
    if not os.path.exists(SPEC):
        print(f"FAIL: cannot find SPEC.md at {SPEC} — this check would pass over nothing")
        return 2
    spec_text = norm(open(SPEC).read())
    fails = 0
    checked = 0

    print("CLAUSE CHECK — every property must quote the contract it enforces")
    for g in GENERATORS:
        p = os.path.join(HERE, g)
        if not os.path.exists(p):
            print(f"  ✘ {g}: listed here but missing from the tree")
            fails += 1
            continue
        try:
            m = load_module(p)
        except Exception as e:
            print(f"  ✘ {g}: could not import to read SPEC_CLAUSES — {e}")
            fails += 1
            continue
        clauses = getattr(m, "SPEC_CLAUSES", None)
        if clauses is None:
            print(f"  ✘ {g}: declares no SPEC_CLAUSES. A property that enforces a MUST must name it; "
                  f"one that enforces nothing normative must say so with an empty list.")
            fails += 1
            continue
        if not clauses:
            print(f"  · {g}: declares NO normative clauses (self-differential only) — allowed, recorded")
            continue
        for anchor, fragment in clauses:
            checked += 1
            if norm(fragment) in spec_text:
                print(f"  ✔ {g}: {anchor} — “{norm(fragment)[:64]}…”")
            else:
                print(f"  ✘ {g}: {anchor} — THIS FRAGMENT IS NOT IN SPEC.md:\n"
                      f"        “{norm(fragment)[:110]}”\n"
                      f"        Either the property is testing something the contract does not say, or the "
                      f"clause was reworded and the property now drifts from it. Both are findings.")
                fails += 1

    print("\nWAIVER CITATIONS — a waiver accuses an engine of violating the contract; it must name it")
    for b in BASELINES:
        p = os.path.join(HERE, b)
        if not os.path.exists(p):
            continue
        try:
            known = json.load(open(p)).get("known", [])
        except Exception as e:
            print(f"  ✘ {b}: unreadable — {e}")
            fails += 1
            continue
        if not known:
            print(f"  · {b}: no waivers")
            continue
        for k in known:
            why = k.get("why", "")
            who = f"{k.get('engine','?')}/{k.get('arm') or k.get('gate') or k.get('aug') or '*'}"
            if "§" in why:
                print(f"  ✔ {b}: {who} cites a clause")
            else:
                print(f"  ✘ {b}: {who} — waived as known-broken with NO clause cited. Name the sentence "
                      f"it violates, or the waiver is an assertion that an engine is wrong.")
                fails += 1

    print()
    if fails:
        print(f"CLAUSE CHECK: FAILED — {fails} citation(s) unresolved.")
    else:
        print(f"CLAUSE CHECK: OK — {checked} clause fragment(s) resolve in SPEC.md, every waiver cites one.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
