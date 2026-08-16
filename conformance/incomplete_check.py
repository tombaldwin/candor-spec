#!/usr/bin/env python3
"""
PART 50 — `incomplete` CROSSES THE SCAN BOUNDARY (SPEC §2 ⟨0.29⟩).

An absent `paths` is overloaded between *"reaches no path"* and *"reaches a path I could not see"*, and the
per-unit `incomplete` field is the only thing that separates them.

WHY THIS ROW EXISTS, stated as it happened. §2 named `incomplete` in the CHAINED-JOIN clause — "a join that
carries the effect and drops `incomplete` lets a benign literal in the consumer certify what the dependency
declared uncertifiable" — and never said a PRODUCER had to emit it. candor-rust and candor-swift did;
candor-ts and candor-java computed the fact internally and published nothing, so the join had nothing to
carry and the rule about the join was vacuous for half the family. A rule stated over one USE of a field
rather than over the CONDITION that produces it, which is a shape this document has now produced four times.

THE HARM IS A FALSE ALL-CLEAR ON A CONFIGURED GATE, and it is only visible ACROSS A BOUNDARY:

    dependency:  depWrite(p)  writes to a PARAMETER      → no `paths`, and (before this rung) no marker
    consumer:    writes "/tmp/lit"  AND calls depWrite("/etc/passwd")
    policy:      allow Fs /tmp/lit

    candor-rust / candor-swift → AS-EFF-008, exit 1        the dep's `incomplete` joins and taints
    candor-ts   / candor-java  → `policy ✓`, exit 0        the consumer's own literal certifies everything

WHY THE ROW IS THE VERDICT AND NOT THE FIELD. In ONE package every engine already fails closed on the same
code — AS-EFF-008 keys on "no visible literal", and a function whose only Fs is a parameter path has none.
So a single-crate row passes on all four and proves nothing; the defect lives entirely at the boundary,
where the consumer's own allowed literal is what makes the joined surface look complete. The field's
presence is asserted too, as the CONTROL: without it the row could pass on an engine that charges
AS-EFF-008 for some unrelated reason, and the two halves would not be measuring the same mechanism.
"""
import json
import sys


def main():
    if len(sys.argv) != 5:
        print("usage: incomplete_check.py <engine> <dep-report> <consumer-rc> <consumer-output>")
        return 2
    engine, dep_path, rc, out = sys.argv[1].strip(), sys.argv[2], sys.argv[3], sys.argv[4]

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    try:
        with open(dep_path) as f:
            dep = json.load(f)
    except Exception as e:                                    # noqa: BLE001 — the diagnosis IS the message
        return fail(f"the dependency report is unreadable ({dep_path}: {e}) — the fixture did not scan, "
                    "and every assertion below would be about a file that is not there")

    fns = dep.get("functions") or []
    if not fns:
        return fail("the dependency report has NO entries — its `Fs` writer is missing, so the row would "
                    "be comparing a consumer against an empty dependency")
    marked = [f for f in fns if "Fs" in (f.get("incomplete") or [])]
    if not marked:
        seen = [{k: f.get(k) for k in ("fn", "paths", "incomplete")} for f in fns]
        return fail("the dependency writes to a PARAMETER path and its report says nothing about it: "
                    "`incomplete` is absent, so a consumer joining this entry cannot tell 'reaches no "
                    f"path' from 'reaches a path I could not see'. entries={seen}")
    if any(f.get("paths") for f in marked):
        return fail("an entry declares an effect's locator UNDETERMINED and publishes a determined path "
                    f"for it in the same breath: {marked}")

    if rc != "1" or "AS-EFF-008" not in out:
        return fail(f"the CONSUMER exited {rc} with no AS-EFF-008. It writes ONE allowed literal and "
                    "calls a dependency whose path is a runtime value, so certifying it is a false "
                    f"all-clear one package boundary along: {out[:200]}")

    print(f"  {engine:6} -> MATCH    (dep declares incomplete:['Fs'] and no paths; the chained consumer "
          f"charges AS-EFF-008 rather than certifying on its own literal)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
