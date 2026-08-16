#!/usr/bin/env python3
"""
PART 53 — THE PEEK IS A PRODUCER READING THE POLICY, SO §3.1 BINDS IT (SPEC §2 ⟨0.29⟩).

§2 already states this: *"Over a policy the engine REFUSES, the key is ABSENT for the reason §3.1
withholds `ok` — the peek is a producer reading the policy, and it may not certify relative to a gate that
evaluated nothing."* The clause shipped with the rung. Three of the four engines did not implement it.

MEASURED on the ⟨0.29⟩ pre-release panel, with `deny Net` beside a typo'd effect token:

    candor-java                            → exit 2, `outOfScope` ABSENT        the clause, implemented
    candor-rust / candor-ts / candor-swift → exit 2, `outOfScope` PUBLISHED     the clause, in prose only

THE HARM IS NOT THE FINDING, IT IS THE KEY. `outOfScope: []` beside a refusal reads *"a policy was
configured, I looked at what it denies, and there is nothing"* — a look that was taken against rules no
route would honour. The denied set the peek searched for is the parser's SALVAGE of an unhonourable file:
the typo'd token is dropped and the remaining rules are searched as though the operator had written them,
which is precisely the silent rewriting that `fatal_messages` / `gateRefusals` exist to refuse one layer
up. A consumer reading exit 2 plus an empty `outOfScope` learns something false about a file nobody judged.

THREE SHAPES, and the two controls are the row:

  A  the policy is REFUSED                    → key ABSENT                      THE DEFECT
  B  the policy STANDS and denies the effect  → key PRESENT with the finding    CONTROL
  C  the policy STANDS and denies another     → key PRESENT and EMPTY           CONTROL

Without B and C an engine passes A by never publishing the key at all — deleting the ⟨0.29⟩ peek while
looking maximally cautious, which is the same failure shape PART 52's control exists for. C matters
separately: present-and-empty is *asked-and-clear* (⟨0.27⟩), and an engine that collapses it to ABSENT has
turned a real answer into "cannot answer" (⟨0.26⟩) — the overload the whole rung is built to remove.
"""
import json
import sys


def main():
    if len(sys.argv) != 8:
        print("usage: refused_peek_check.py <engine> <A rc> <A report> <B rc> <B report> "
              "<C rc> <C report>")
        return 2
    engine = sys.argv[1].strip()
    a_rc, a_p, b_rc, b_p, c_rc, c_p = sys.argv[2:8]

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    docs = {}
    for shape, p in (("A", a_p), ("B", b_p), ("C", c_p)):
        try:
            with open(p) as f:
                docs[shape] = json.load(f)
        except Exception as e:                                # noqa: BLE001 — the diagnosis IS the message
            return fail(f"shape {shape}'s report is unreadable ({p}: {e}) — the fixture did not scan, so "
                        "a green result below would be about a file that is not there")

    # The refusal has to actually happen, or shape A asserts nothing. An engine that HONOURED the typo'd
    # token would pass "key absent" for a completely different reason.
    if a_rc != "2":
        return fail(f"the refused policy answered exit {a_rc}, not 2 — this engine did not refuse it, so "
                    "the absence asserted below would be about a policy that stood")
    if b_rc != "0" or c_rc != "0":
        return fail(f"a policy that STANDS answered exit {b_rc}/{c_rc} rather than 0 — the controls are "
                    "not measuring a run whose peek was allowed to publish")

    # (A) THE DEFECT.
    if "outOfScope" in docs["A"]:
        oos = docs["A"].get("outOfScope") or []
        shape = "empty" if not oos else f"{len(oos)} finding(s)"
        return fail(f"`outOfScope` is PUBLISHED ({shape}) over a policy this engine REFUSED — the key is a "
                    "claim relative to a gate that evaluated nothing, and the denied set it searched was "
                    "the parser's salvage of an unhonourable file")

    # (B) THE PEEK STILL WORKS. Without this, never publishing the key passes (A) and deletes the feature.
    if "outOfScope" not in docs["B"]:
        return fail("`outOfScope` is ABSENT over a policy that STANDS and denies the effect sitting in an "
                    "excluded file — the key is being withheld unconditionally, so shape A above says "
                    "nothing and the ⟨0.29⟩ peek is gone")
    if not (docs["B"].get("outOfScope") or []):
        return fail("the peek published an EMPTY `outOfScope` over an excluded file that holds the denied "
                    "effect — asked-and-clear is being claimed where there is a finding")

    # (C) …AND PRESENT-AND-EMPTY SURVIVES. Collapsing it to absent turns a real answer into "cannot answer".
    if "outOfScope" not in docs["C"]:
        return fail("`outOfScope` is ABSENT over a policy that STANDS and denies an effect the excluded "
                    "files do not hold — ⟨0.27⟩ makes that a positive answer (asked-and-clear), and "
                    "⟨0.26⟩ makes the absent key mean 'cannot answer'; the two are not interchangeable")
    if (docs["C"].get("outOfScope") or []) != []:
        return fail("the peek reports a finding for an effect the policy does not deny — the block is not "
                    "bounded by the policy, which is what keeps it from becoming noise")

    print(f"  {engine:6} -> OK        (refused ⇒ key absent; honoured-and-dirty ⇒ the finding; "
          "honoured-and-clean ⇒ present-and-empty)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
