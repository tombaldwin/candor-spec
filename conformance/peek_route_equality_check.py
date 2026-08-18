#!/usr/bin/env python3
"""
PART 54 — THE ⟨0.30⟩ VERDICT REACHES BOTH ROUTES IDENTICALLY (SPEC §2 ⟨0.30⟩ / §3.1).

⟨0.30⟩ makes a non-empty `outOfScope` an INCOMPLETE verdict — `ok:false`, `incomplete:true`, exit 2 —
reversing ⟨0.29⟩'s "an out-of-scope finding MUST NOT move the verdict". PART 48 asserts that on the SCAN
route. This part asserts the half PART 48 cannot see, and the half that killed the previous attempt at a
peek-derived disclosure.

WHY A SEPARATE PART, rather than another arm on 48
--------------------------------------------------
§3.1 makes `scan --policy` and `gate --report` produce BYTE-EQUAL verdict documents. The two routes reach
the finding by different means and only one of them can peek: `scan --policy` runs the peek itself, while
`gate --report` has NO TARGET — it holds a document, not a tree, and cannot re-derive an exclusion set
from it. That asymmetry is exactly what killed the `net-partner` disclosure attempt (candor/BACKLOG.md):
emitting on the route that could compute it broke byte-equality with the route that could not.

⟨0.30⟩ survives it for one structural reason — `outOfScope` is a field OF THE REPORT, so the gate route
reads the entries the scan peeked instead of recomputing them. A part that only drove the scan route would
pass against an engine that moved the verdict on one route and left the other certifying, which is the
supply-chain half: a consumer gating a report someone else produced.

WHAT EACH ARM RULES OUT
-----------------------
  · (A) SAME EXIT      both routes answer 2 over the same finding. An engine that fixed only the scan
                       route leaves `gate --report` green over a resolved denied effect.
  · (B) BYTE-EQUAL     …and the two verdict documents are identical bytes, which is §3.1's own acceptance
                       test. Same exit with different documents is drift a consumer would read as two
                       different verdicts.
  · (C) ABSENT ≠ EMPTY a report produced with NO policy carries no `outOfScope` key, and gating it must
                       stay exit 0. ⟨0.26⟩ makes an absent key "this producer cannot answer"; treating it
                       as a trigger would fail-close every pre-⟨0.30⟩ report on contact, which is an
                       upgrade that breaks every existing pipeline rather than a rung.
  · (D) THE CONTROL    a tree whose peek is asked-and-clear exits 0 on BOTH routes with byte-equal
                       documents. Without it the part passes against an engine that answers 2 for
                       everything — the vacuous-pass shape this suite keeps measuring in its own work,
                       and the one this rung is most likely to regress into.

(C) AND (D) ARE NOT THE SAME CONTROL. (D) is "the peek ran and found nothing" (present-and-empty, a real
answer). (C) is "the peek never ran" (absent, no answer at all). ⟨0.26⟩/⟨0.27⟩ make those different
claims, and an engine that collapses them passes one while failing the other.
"""
import json
import sys


def load(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:                                    # noqa: BLE001 — the diagnosis IS the message
        return None if path else str(e)


def main():
    if len(sys.argv) < 9:
        print("usage: peek_route_equality_check.py <engine> <scan_rc> <scan_verdict> <gate_rc> "
              "<gate_verdict> <absent_rc> <ctl_scan_rc> <ctl_scan_verdict> <ctl_gate_rc> <ctl_gate_verdict>")
        return 2
    engine = sys.argv[1].strip()
    (scan_rc, scan_v, gate_rc, gate_v, absent_rc,
     ctl_scan_rc, ctl_scan_v, ctl_gate_rc, ctl_gate_v) = sys.argv[2:11]

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    # ── (A) SAME EXIT ─────────────────────────────────────────────────────────────────────────────
    if scan_rc != "2":
        return fail(f"`scan --policy` over a peeked function performing the denied effect exited {scan_rc}, "
                    "not 2 — ⟨0.30⟩ makes that verdict INCOMPLETE (PART 48 asserts this too; if that part "
                    "is green and this is not, the fixture here is wrong, not the engine)")
    if gate_rc != "2":
        return fail(f"`gate --report` over the SAME report exited {gate_rc}, not 2 — the finding rides the "
                    "report, so the route that reads it must reach the same verdict. This is the "
                    "supply-chain half: a consumer gating a report someone else produced")

    a, b = load(scan_v), load(gate_v)
    if a is None or b is None:
        return fail(f"a verdict document is missing (scan={scan_v} gate={gate_v}) — both routes must WRITE "
                    "one, and a document a consumer never receives cannot be compared")

    # ── (B) BYTE-EQUAL ────────────────────────────────────────────────────────────────────────────
    if a != b:
        try:
            da, db = json.loads(a), json.loads(b)
            diff = sorted(set(da) ^ set(db)) or [k for k in set(da) & set(db) if da[k] != db[k]]
            why = f"keys/values differing: {diff}"
        except Exception:                                     # noqa: BLE001
            why = "one of them is not even JSON"
        return fail(f"the two verdict documents are NOT byte-equal ({why}) — §3.1 makes that the acceptance "
                    "test, and this is the constraint the `net-partner` attempt failed. It holds only "
                    "because `outOfScope` is a field OF THE REPORT rather than something the gate route "
                    "would have to re-derive from a target it does not have")

    # …and the document must actually say WHY, in the machine channel. A bare exit 2 with a silent
    # document is the stderr-only disclosure ⟨0.21⟩ exists to stop.
    try:
        doc = json.loads(a)
    except Exception:                                         # noqa: BLE001
        return fail("the verdict document is not JSON")
    if doc.get("ok") is not False:
        return fail(f"the verdict says ok={doc.get('ok')!r} beside exit 2 — a consumer keying on `ok` alone "
                    "must land on FAIL, which is the whole fail-closed standard of this format")
    if doc.get("incomplete") is not True:
        return fail("the verdict omits `incomplete: true` — ⟨0.30⟩ reports this cause through the SAME key "
                    "⟨0.21⟩ uses, so a consumer branching on `incomplete` alone is safe under both causes")
    if doc.get("violations"):
        return fail(f"the verdict lists {len(doc['violations'])} violation(s) — the gate did NOT judge these "
                    "functions, so reporting them as violations is false in the other direction. That "
                    "distinction is why the code is 2 and not 1")
    if not (doc.get("outOfScope") or []):
        return fail("the verdict carries no `outOfScope` — exit 2 with a silent document is the stderr-only "
                    "disclosure a machine consumer cannot see, which is the defect ⟨0.21⟩ was built for")

    # ── (C) ABSENT IS NOT A TRIGGER ───────────────────────────────────────────────────────────────
    if absent_rc != "0":
        return fail(f"gating a report produced with NO policy exited {absent_rc}, not 0 — that report was "
                    "never ASKED the scope question, so its missing key is ⟨0.26⟩'s 'cannot answer', not a "
                    "finding. Treating absence as a trigger fail-closes every pre-⟨0.30⟩ report on contact")

    # ── (D) THE CONTROL ───────────────────────────────────────────────────────────────────────────
    if ctl_scan_rc != "0" or ctl_gate_rc != "0":
        return fail(f"the asked-and-clear control exited {ctl_scan_rc}/{ctl_gate_rc} rather than 0/0 — a peek "
                    "that ran and found nothing must NOT move the verdict, or the rung reddens every "
                    "project with an exclusion and the gate stops being worth running")
    ca, cb = load(ctl_scan_v), load(ctl_gate_v)
    if ca is None or cb is None or ca != cb:
        return fail("the control's two verdict documents are missing or not byte-equal — §3.1 binds the "
                    "clean path as tightly as the failing one, and a rung that only keeps byte-equality "
                    "when it fires has broken the verb it rode in on")

    print(f"  {engine:6} -> OK        (both routes exit 2 on the finding, byte-equal; ok:false + incomplete "
          "+ no violations; absent key ⇒ 0; asked-and-clear ⇒ 0/0 byte-equal)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
