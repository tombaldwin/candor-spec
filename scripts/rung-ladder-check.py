#!/usr/bin/env python3
"""rung-ladder-check.py — do not mint a rung against an UNRELEASED rung.

A rung is a RELEASED contract version. Authoring ⟨0.N+2⟩ while ⟨0.N+1⟩ has never been tagged buys
nothing — no engine ever declared the skipped number and no consumer has a report stamped with it — and
it costs a hole in the ladder that a reader later has to explain.

**THIS HAS HAPPENED TWICE.**
  * ⟨0.22⟩ — has a rung marker AND a §8 changelog entry, and NO tag. The floor went v0.21.0 → v0.23.
  * ⟨0.40⟩ — drafted as its own rung on 2026-09-20 while ⟨0.39⟩ was still unreleased, and folded back
    into ⟨0.39⟩ the same day, before either shipped. Caught by Tom asking why we needed 0.40 at all.

Twice is a class, and this project's own rule is that a rule which has failed twice is not a rule, it is
a note. So this is a check rather than a paragraph.

THE DISCRIMINATOR: the highest rung marker in SPEC.md may be at most ONE above the highest released tag.
  highest tag 0.38, highest rung ⟨0.39⟩  -> fine, a rung is being authored
  highest tag 0.38, highest rung ⟨0.40⟩  -> FAIL, ⟨0.39⟩ was never released
It deliberately does NOT walk the whole ladder: historical skips are frozen, and reddening on ⟨0.22⟩
forever would train the reader to ignore this check — which is how a guard becomes decoration.

Release-preflight [12] is the sibling and catches the SYMPTOM at the cut (text ahead of its number). This
catches the CAUSE at authoring time, which is where the decision actually gets made.
"""
import re, subprocess, sys, pathlib

def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    spec = (root / "SPEC.md").read_text()
    rungs = sorted({int(m) for m in re.findall(r'⟨0\.(\d+)⟩', spec)})
    if not rungs:
        print("rung-ladder: no rung markers in SPEC.md — this check would pass over nothing"); return 1
    top = rungs[-1]

    tags = subprocess.run(["git", "-C", str(root), "tag"], capture_output=True, text=True).stdout.split()
    minors = sorted({int(m.group(1)) for m in (re.match(r'^v0\.(\d+)', t) for t in tags) if m})
    if not minors:
        print("rung-ladder: no v0.N tags found — cannot tell released from unreleased"); return 1
    released = minors[-1]

    if top - released > 1:
        print(f"rung-ladder: FAILED — SPEC.md's highest rung is ⟨0.{top}⟩ but the highest released floor "
              f"is 0.{released}.")
        print(f"  ⟨0.{released + 1}⟩ has never been tagged, so ⟨0.{top}⟩ is being minted against an "
              f"UNRELEASED rung.")
        print("  A rung is a RELEASED contract version. Fold the new clauses into "
              f"⟨0.{released + 1}⟩, or release it first.")
        print("  This is the failure ⟨0.22⟩ and ⟨0.40⟩ both took; see this script's header.")
        return 1
    print(f"rung-ladder: OK — highest rung ⟨0.{top}⟩, highest released floor 0.{released} "
          f"({'authoring a rung' if top > released else 'no rung in flight'})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
