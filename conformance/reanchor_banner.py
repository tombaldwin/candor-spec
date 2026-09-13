#!/usr/bin/env python3
"""RE-ANCHOR the Contents version banner's must-ledger entry after a floor bump.

WHY THIS EXISTS. SPEC.md's Contents carries "**Version X.Y** — all code engines declare `X.Y`", so a
floor bump REWORDS a normative statement and its `must-ledger.json` sha moves with it. The ledger then
reports one unclassified statement plus one orphaned entry — a correct catch that needs a mechanical
re-anchor, not a judgement.

It needed that hand step at ⟨0.35⟩, ⟨0.36⟩ AND ⟨0.37⟩, and the only guard each time was a NOTE
`spec-bump.sh` printed for a human to read. `spec-bump.sh`'s own leftover-mentions scan cannot see the
problem: that scan greps `spec.\{0,3\}0.36` and `"0.36"`, while the ledger records a BACKTICKED excerpt
(``declare `0.36` ``), so the two never meet. Three bumps, three re-anchors, one guard made of someone
remembering to read a line. CLAUDE.md's own rule applies — a rule the operator must remember to APPLY
is weaker than one that removes the option.

WHAT IT REFUSES TO DO, which is the point. It re-anchors ONLY when the situation is unambiguous:
exactly one orphaned entry, exactly one unclassified statement, and that statement is recognisably the
banner. Anything else is a real classification question and it exits 1 saying so, leaving the work to a
human. A tool that "fixed" an ambiguous ledger would be laundering an unclassified MUST into a
classified one, which is precisely the failure the ledger exists to prevent.

It imports `must_ledger` and uses ITS extract/hash rather than reimplementing them. A second copy of a
hashing rule is the R288 shape: two implementations that agree until they don't, and the disagreement
is silent.

    python3 reanchor_banner.py [--spec P] [--ledger P] [--dry-run]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import must_ledger as ml  # noqa: E402

# The banner is identified by the INVARIANT half of its own sentence — the half a bump does not touch.
BANNER_MARK = "all code engines declare"


def main(argv):
    spec = ml.DEFAULT_SPEC
    ledger = ml.DEFAULT_LEDGER
    dry = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--spec":
            i += 1; spec = argv[i]
        elif a == "--ledger":
            i += 1; ledger = argv[i]
        elif a == "--dry-run":
            dry = True
        else:
            print(f"reanchor_banner.py: unknown argument {a!r}")
            return 2
        i += 1

    stmts = ml.extract(spec)
    doc = json.load(open(ledger))
    entries = doc.get("entries", [])
    by_sha = {e.get("sha", ""): e for e in entries}

    orphans = [e for e in entries if e.get("sha") not in stmts]
    unclassified = [(sha, text) for sha, text in stmts.items() if sha not in by_sha]

    if not orphans and not unclassified:
        print("reanchor_banner: nothing to do — every statement is classified and no entry is orphaned")
        return 0

    if len(orphans) != 1 or len(unclassified) != 1:
        print(f"reanchor_banner: REFUSING — {len(orphans)} orphaned entr(ies) and "
              f"{len(unclassified)} unclassified statement(s); this is only safe at exactly one of each.")
        print("  More than the banner moved, so this is a classification question, not a re-anchor.")
        print("  Run `python3 must_ledger.py` and classify them by hand.")
        return 1

    new_sha, new_text = unclassified[0]
    old = orphans[0]
    # `ml.extract` yields (lineno, section, text). Take the TEXT element by position rather than
    # stringifying the tuple: the section name would otherwise be searched for the marker too, so a
    # section that happened to contain the phrase could satisfy the check for a statement that does not.
    body = new_text[-1] if isinstance(new_text, (tuple, list)) else new_text
    flat = " ".join(str(body).split())
    if BANNER_MARK not in flat:
        print("reanchor_banner: REFUSING — the one unclassified statement is not the Contents version "
              f"banner (no {BANNER_MARK!r} in it):")
        print(f"    {flat[:160]}")
        print("  A statement that moved for some other reason needs a human to say what exercises it.")
        return 1

    if dry:
        print(f"reanchor_banner: WOULD move {old['sha']} -> {new_sha}")
        return 0

    old_sha = old["sha"]
    old["sha"] = new_sha
    with open(ledger, "w") as f:
        f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    kind = "part" if "part" in old else ("unenforced" if "unenforced" in old else "status")
    print(f"reanchor_banner: the Contents version banner moved — re-anchored its ledger entry")
    print(f"    sha   {old_sha}  ->  {new_sha}")
    print(f"    kept  {kind}: {str(old.get(kind))[:90]}…")
    print(f"    text  {flat[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
