#!/usr/bin/env python3
"""⟨0.35⟩ A NON-EMPTY CANDIDATE SET IS NOT A COMPLETE ONE — the checker for PART 87.

THE PROPERTY. At a dispatch site whose visible implementor set includes a compiler-synthesised or
structural implementor (a lambda coerced to an interface, a method reference, an object literal
satisfying a shape), the CALLING function's `inferred` MUST either include that implementor's own
effects, or contain `Unknown` with `unresolved: true`. Effects OR disclosure — a disjunction,
because an engine may legitimately COMPLETE the candidate set instead of hedging, and a clause that
mandated the hedge would outlaw the better fix.

WHY THIS FILE EXISTS RATHER THAN AN INLINE grep. The failure's signature is ABSENCE. Measured on
published 0.34.0: with one pure unrelated implementor added, java's and ts's calling function is
simply MISSING from `functions[]` — no effects, no Unknown, no row at all. Every engine omits pure
functions from the report, so `absent` and `analysed, genuinely pure` are the SAME BYTES. A checker
that looks the caller up and skips when it cannot find it is green on a broken engine forever, in a
suite whose checkers have already survived exit-0 replacement 13/13 times.

So: ABSENCE IS A FAILURE HERE, stated once, in code, with its own self-test proving the checker can
report it. That is the whole reason for a named helper.
"""
import json
import sys

UNKNOWN = "Unknown"


def verdict(report_path, caller, effect):
    """Return (ok: bool, reason: str) for one arm.

    `caller` MUST appear in functions[] and MUST carry either `effect` or Unknown+unresolved.
    """
    try:
        with open(report_path) as fh:
            doc = json.load(fh)
    except Exception as exc:                                    # noqa: BLE001 - any read/parse failure
        return False, "report at %s could not be read as JSON (%s)" % (report_path, exc)

    fns = doc.get("functions") or []
    hit = None
    for f in fns:
        name = f.get("fn") or ""
        if name == caller or name.endswith("." + caller) or name.endswith("::" + caller):
            hit = f
            break

    if hit is None:
        # THE LOAD-BEARING BRANCH. Not a skip, not "inconclusive" — a FAILURE.
        return False, (
            "`%s` is ABSENT from functions[] — the engine reported it as resolved with no effects. "
            "That is the sin's exact signature: a pure function and a wrongly-resolved one are the "
            "same bytes, so absence must be read as the claim it is ('analysed, nothing here'), "
            "never as 'not analysed'. Expected %s in `inferred`, or Unknown with unresolved:true."
            % (caller, effect)
        )

    inferred = hit.get("inferred") or hit.get("effects") or []
    if effect in inferred:
        return True, "`%s` carries %s — the candidate set was COMPLETED (effects flow)" % (caller, effect)
    if UNKNOWN in inferred:
        if hit.get("unresolved") is True:
            why = hit.get("unknownWhy") or []
            return True, "`%s` carries Unknown + unresolved:true %s — the incompleteness is DISCLOSED" % (
                caller, why)
        return False, (
            "`%s` carries Unknown but `unresolved` is %r, not true. The clause binds the EFFECT SET and "
            "requires the flag to accompany it; a bare Unknown without the flag leaves a consumer unable "
            "to tell a modelled Unknown from an unresolved one." % (caller, hit.get("unresolved"))
        )
    return False, (
        "`%s` is PRESENT with inferred=%s — neither %s (candidate set completed) nor Unknown "
        "(incompleteness disclosed). The engine claimed a complete answer over a dispatch whose "
        "implementor set it cannot show to be complete." % (caller, inferred, effect)
    )


def selftest():
    """PROVE THE CHECKER CAN FAIL. A row whose checker cannot report a defect is worse than no row.

    Four synthetic reports: the two PASSING shapes the disjunction allows, and the two FAILING ones
    the clause forbids — including ABSENCE, which is the shape this file exists for.
    """
    import tempfile, os
    cases = [
        ("completed",  {"functions": [{"fn": "app.Caller.go", "inferred": ["Fs"]}]},                       True),
        ("disclosed",  {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"], "unresolved": True,
                                       "unknownWhy": ["callback:java.lang.Runnable.run"]}]},               True),
        ("ABSENT",     {"functions": [{"fn": "app.Other.x", "inferred": ["Fs"]}]},                         False),
        ("present-pure", {"functions": [{"fn": "app.Caller.go", "inferred": []}]},                         False),
        ("unknown-no-flag", {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"]}]},             False),
    ]
    bad = 0
    for label, doc, want in cases:
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh)
        got, reason = verdict(path, "app.Caller.go", "Fs")
        os.unlink(path)
        mark = "ok " if got == want else "FAIL"
        if got != want:
            bad += 1
        print("  %s %-16s want=%-5s got=%-5s  %s" % (mark, label, want, got, reason[:88]))
    if bad:
        print("CHA CHECK SELFTEST: FAILED — %d case(s) wrong" % bad)
        return 1
    print("CHA CHECK SELFTEST: OK — 5 cases, both passing shapes and all three failing shapes "
          "(including ABSENCE) are distinguished")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) != 4:
        print("usage: cha_completeness_check.py <report.json> <caller-fn> <effect>", file=sys.stderr)
        print("       cha_completeness_check.py --selftest", file=sys.stderr)
        sys.exit(2)
    ok, reason = verdict(sys.argv[1], sys.argv[2], sys.argv[3])
    print(("OK  " if ok else "DIVERGE — ") + reason)
    sys.exit(0 if ok else 1)
