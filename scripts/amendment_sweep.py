#!/usr/bin/env python3
"""
WHEN A DEFINITION IS AMENDED, FIND EVERY PLACE THAT STILL REASONS FROM THE OLD ONE.

WHY, stated as it happened. PAPER3's Definition 2 was amended to remove `Db ⊑ₑ Net` — a database effect is
not a network effect, an embedded store has no egress. The amendment was written carefully, with its own
*Amended* note and a measured justification. It was not propagated. Six sites went on reasoning from the
retracted relation, and they were found one at a time over weeks:

  · Definition 3's own example ("an observed `Db` is covered by a declared `Net`") — the definition of
    covering, using the relation that had just been removed;
  · Definition 3's scope note (`{Net}` and `{Net, Db}` "become equivalent");
  · Definition 22 ("an observed `Db` against a declared `Net` is not a violation" — it is one now);
  · Proposition 6's PROOF, whose first step needs `Db ⊑ₑ Net` and therefore does not go through;
  · Escape 2's entire instance;
  · PAPER1's preorder definition, still listing `Db ⊑ₑ Net` outright, plus an EVIDENCE claim whose
    verdict flips.

Three of those are in the same document as the amendment. The failure is not carelessness — it is that
nothing looks. An amendment note says what changed; nothing enumerates what it changed *around*.

WHAT THIS DOES. Given the retracted text (a relation, a claim, a phrase), it greps every live document for
mentions and classifies each as ALREADY-AMENDED (inside an amendment note quoting the old form, which is
correct and must not be flagged) or LIVE (prose still asserting it). It cannot know which is which
perfectly, so it prints both and marks its guess — a sweep that silently swallowed a live site would be the
defect it exists to catch.

VERIFIED TO CATCH, against the six sites as they actually read before they were fixed: reconstructing
Definition 3's example, its scope note, Definition 22, Proposition 6's proof, Escape 2 and PAPER1's
preorder, the sweep flags every one as LIVE (`observed \`Db\` is covered by a declared \`Net\`` alone
returns 3). Run against the CORRECTED documents it returns zero LIVE rows — the last one, a past-tense
narrative in MANUSCRIPT.md, dropped out when that file gained its SUPERSEDED banner. Do not read zero as
proof: the split is a guess from nearby wording, which is why it prints its guess rather than filtering
silently. It DOES refuse outright when it read no files at all, which is a different thing from a clean
sweep and must never print like one.

    python3 amendment_sweep.py 'Db ⊑ₑ Net' [--dir ~/candor-paper] [--dir .]

The papers are deliberately local-only and not in this repo, so `--dir` takes their path.
"""
import argparse
import os
import re
import sys

# Lines inside an amendment/retraction note legitimately QUOTE the old form. Flagging them is noise, and
# noise is how a sweep stops being read.
AMENDED_MARKERS = (
    "amended", "previously read", "previously stated", "previously instantiated", "used to say",
    "used to read", "retracted", "no longer", "corrected", "correcting", "was wrong", "earlier version",
    "predates", "before this", "superseded", "originally", "reinstated", "erroneous",
    "the theory's fault", "not merely absent", "took the sentence at its word",
)

# CALIBRATED, not guessed. A first version used a 6-line window and the short marker list above's first
# row, and reported 12 LIVE rows against the `Db ⊑ₑ Net` amendment of which nearly all were narrative
# ABOUT the correction. A sweep with that signal-to-noise is not read, and an unread sweep is worse than
# none because it looks like coverage. The window and the extra markers below were chosen by running it
# against a real amendment and reading every row.
WINDOW = 14


def classify(lines, i):
    """Amendment-note or live? A guess from nearby wording, calibrated against a real amendment."""
    window = " ".join(lines[max(0, i - WINDOW): i + 3]).lower()
    if any(m in window for m in AMENDED_MARKERS):
        return "amended-note"
    # THE STRONGEST SINGLE SIGNAL, and a principled one rather than another keyword: if the NEGATED form
    # appears nearby, the passage is discussing the correction, not asserting the retracted claim.
    return "amended-note" if _negated_nearby(lines, i) else "LIVE"


def _negated_nearby(lines, i):
    """Is the retracted relation's NEGATION (⋢ for ⊑, "does NOT", "is not") in the neighbourhood?"""
    w = " ".join(lines[max(0, i - WINDOW): i + 4])
    return "⋢" in w or "does **not**" in w.lower() or "is **not**" in w.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", help="the retracted claim, verbatim (e.g. 'Db ⊑ₑ Net')")
    ap.add_argument("--dir", action="append", default=[],
                    help="a directory to sweep; repeatable. Defaults to this repo.")
    ap.add_argument("--ext", default=".md,.tex,.py,.rs,.java,.swift,.mjs,.sh")
    a = ap.parse_args()
    dirs = a.dir or [os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
    exts = tuple(a.ext.split(","))

    live, noted, superseded = [], [], set()
    swept = 0
    for d in dirs:
        d = os.path.expanduser(d)
        if not os.path.isdir(d):
            print(f"  (skipping {d} — not a directory)", file=sys.stderr)
            continue
        for root, dirnames, files in os.walk(d):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "node_modules", "target", ".build", "build", "archive")]
            for f in files:
                if not f.endswith(exts):
                    continue
                p = os.path.join(root, f)
                if os.path.abspath(p) == os.path.abspath(__file__):
                    continue   # this file quotes the example amendment in its own docstring
                try:
                    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
                except Exception:
                    continue
                swept += 1
                # A doc that has ALREADY been marked superseded is not a live site; flagging it every run
                # trains the reader to skim. Reported separately at the end instead.
                if any("SUPERSEDED" in x for x in lines[:40]):
                    superseded.add(p)
                    continue
                for i, ln in enumerate(lines):
                    if a.text in ln:
                        rec = (p, i + 1, ln.strip()[:118])
                        (noted if classify(lines, i) == "amended-note" else live).append(rec)

    # A sweep that read NOTHING must not print a clean bill. `--dir ~/candor-paper` points OUTSIDE this
    # repo by design (the papers are local-only), so a typo, a different machine, or a moved checkout all
    # produce zero files read — and the report below would have said "LIVE mentions (0)" and exited 0.
    # That is the same shape as the defect this script exists to find: an absent answer read as a negative
    # one. field_audit.py in this same family already refuses an empty table; this now matches it.
    if not swept:
        print(f"AMENDMENT SWEEP — {a.text!r}\n  swept: {', '.join(dirs)}", file=sys.stderr)
        print("  REFUSING: not one file was read. This is not a clean sweep, it is no sweep — check the\n"
              "  --dir paths and the --ext list.", file=sys.stderr)
        return 2

    print(f"AMENDMENT SWEEP — {a.text!r}")
    print(f"  swept: {', '.join(dirs)}  ({swept} files read)")
    print(f"\n  LIVE mentions ({len(live)}) — prose that may still be REASONING from the retracted form:")
    if not live:
        print("    (none)")
    for p, n, t in live:
        print(f"    {p}:{n}\n      {t}")
    print(f"\n  inside an amendment note ({len(noted)}) — quoting the old form, which is correct:")
    for p, n, t in noted[:20]:
        print(f"    {p}:{n}")
    if len(noted) > 20:
        print(f"    … and {len(noted) - 20} more")
    if superseded:
        print(f"\n  skipped ({len(superseded)}) — carry a SUPERSEDED banner, so a stale claim there is expected:")
        for p in sorted(superseded):
            print(f"    {p}")
    print("\n  The split is a GUESS from nearby wording, not a judgment. Read every LIVE row, and skim the")
    print("  other list too — a site that merely mentions 'amended' nearby is not thereby correct.")
    # Exit 1 when live mentions exist, so this can gate a commit that amends a definition.
    return 1 if live else 0


if __name__ == "__main__":
    sys.exit(main())
