#!/usr/bin/env python3
"""
PART 52 — A CLASS IS `peeked` ONLY IF EVERY FILE OF IT WAS READ (SPEC §2 ⟨0.29⟩).

`excluded[].peeked` exists so that `outOfScope: []` cannot overclaim: `[]` beside `peeked: true` means
*"I opened those files and there is nothing in them"*, and `[]` beside `peeked: false` means *"I did not
look"*. The ⟨0.29⟩ rung already made the flag an OUTCOME rather than a lookup on the exclusion class —
a peek that never ran, could not spawn, or returned nothing unparseable no longer claims a read.

IT STOPPED ONE LEVEL SHORT, and the panel that shipped the rung found it. The peek reuses the engine's own
entry point, so the child produces its own ⟨0.21⟩ completeness manifest — `unanalyzed`, the files it could
not read. Every engine read the child's `functions` and threw its `unanalyzed` away. So:

    an excluded file that FAILED TO PARSE INSIDE THE PEEK  →  `peeked: true`, `outOfScope: []`

which is byte-identical to a clean peek of the same tree. MEASURED on candor-rust, candor-ts, candor-java
and candor-swift — all four. The stderr warning the child prints is the only reason a human could notice,
and it is suppressed on three of the four engines because a peek is supposed to be quiet; the machine
consumer, reading the report, gets the opposite of the truth. This is the ⟨0.26⟩ partial-manifest rule
(*a partial answer is worse than an absent one*) failing inside the rung built to enforce it, for the
second time in the same field.

THREE SHAPES, and the two controls are what make the row mean anything:

  A  the excluded file does not parse       → `peeked: false`     THE DEFECT
  B  it parses and holds no denied effect   → `peeked: true`, `outOfScope: []`     OVER-CHARGE CONTROL
  C  it parses and HOLDS the denied effect  → `peeked: true`, and the finding is published

Without B an engine satisfies this row by never claiming a peek at all, which silently deletes the whole
feature — the failure mode is invisible precisely because `peeked: false` is the SAFE value. Without C the
row passes on an engine whose peek finds nothing at all.

The claim is withdrawn PER CLASS, not wholesale: a parse failure is a fact about one file, and candor-swift
peeks `harness-target` and `manifest` in the same run. Charging both for one unreadable test file would be
the crude rule this project keeps having to replace with the precise one.
"""
import json
import sys


def main():
    if len(sys.argv) != 6:
        print("usage: peek_completeness_check.py <engine> <shape A report> <shape B report> "
              "<shape C report> <class>")
        return 2
    engine, a_path, b_path, c_path, cls = (sys.argv[1].strip(), sys.argv[2], sys.argv[3],
                                           sys.argv[4], sys.argv[5].strip())

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    docs = {}
    for shape, p in (("A", a_path), ("B", b_path), ("C", c_path)):
        try:
            with open(p) as f:
                docs[shape] = json.load(f)
        except Exception as e:                                # noqa: BLE001 — the diagnosis IS the message
            return fail(f"shape {shape}'s report is unreadable ({p}: {e}) — the fixture did not scan, and "
                        "a green result below would be about a file that is not there")

    def entry(shape):
        for e in docs[shape].get("excluded") or []:
            if e.get("class") == cls:
                return e
        return None

    for shape in ("A", "B", "C"):
        if entry(shape) is None:
            return fail(f"shape {shape} does not report the `{cls}` exclusion class at all — the fixture "
                        "did not exclude what this row is about, so nothing was measured")

    # (A) THE DEFECT. An unreadable file inside the peek means the class was not examined, and the empty
    # `outOfScope` beside it must not be readable as "there is nothing there".
    if entry("A")["peeked"] is not False:
        return fail(f"an excluded file that FAILED TO PARSE inside the peek still leaves `{cls}` marked "
                    "`peeked: true` — `outOfScope: []` beside it claims a look that did not happen, which "
                    "is byte-identical to a clean peek")

    # (B) THE OVER-CHARGE CONTROL. `peeked: false` is the SAFE value, so an engine that simply stopped
    # claiming a read passes (A) and deletes the feature. This is the assertion that notices.
    if entry("B")["peeked"] is not True:
        return fail(f"a peek that READ every `{cls}` file and found nothing does not claim it "
                    "(`peeked: false`) — the safe value is being published unconditionally, so the flag "
                    "carries no information and the whole peek is invisible")
    if (docs["B"].get("outOfScope") or []) != []:
        return fail("the clean shape reports a finding — the control fixture is not clean, so shape C "
                    "below proves nothing about the peek")

    # (C) …AND THE PEEK STILL WORKS. Without this the row passes on an engine whose peek finds nothing.
    if entry("C")["peeked"] is not True:
        return fail(f"a peek that READ the `{cls}` file holding the denied effect does not claim it")
    oos = docs["C"].get("outOfScope") or []
    if not oos:
        return fail("the peek did not report the denied effect sitting in the excluded file — this row's "
                    "two `peeked: true` assertions are then about a peek that reads nothing")
    if not any(e.get("class") == cls for e in oos):
        return fail(f"the finding is not attributed to `{cls}` — it and its `excluded` entry disagree "
                    "about which class was looked at")

    print(f"  {engine:6} -> OK        (unparseable ⇒ not peeked; read-and-clean ⇒ peeked with an empty "
          "`outOfScope` that means it; read-and-dirty ⇒ peeked with the finding)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
