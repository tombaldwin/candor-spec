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
    # EXACT MATCH FIRST, ALWAYS. A bare `endswith("." + caller)` picks the FIRST suffix match in
    # report order, with no regard for which package it came from — two classes with the same simple
    # name in different packages (a real, previously-shipped class: same-named units merging across
    # modules) both end in `.Widget.fire`, and the matcher would silently score whichever happens to
    # sort first, never noticing the actual target under test might be a DIFFERENT entry that is
    # ABSENT — the exact sin this file exists to catch, hidden behind an unrelated same-named function.
    # So: an exact `fn` match is unambiguous and wins outright; short of that, MULTIPLE distinct
    # suffix matches are an inconclusive collision, not a pick — never guess between them.
    exact = [f for f in fns if (f.get("fn") or "") == caller]
    if exact:
        hit = exact[0]
    else:
        suffix_hits = [f for f in fns if (f.get("fn") or "").endswith("." + caller)
                       or (f.get("fn") or "").endswith("::" + caller)]
        distinct = sorted({f.get("fn") for f in suffix_hits})
        if len(distinct) > 1:
            return False, (
                "`%s` matches MULTIPLE distinct functions[] entries by suffix, and none exactly: %s. "
                "Picking the first would silently judge a different function's report as this one's — "
                "possibly masking the real target's absence behind an unrelated same-named entry. "
                "Qualify `caller` enough to match exactly." % (caller, distinct)
            )
        hit = suffix_hits[0] if suffix_hits else None

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
            # THE CLAUSE'S TEXT NAMES A THIRD REQUIREMENT, NOT JUST TWO. ⟨0.35⟩(b) reads "contain
            # Unknown, with unresolved:true AND an unknownWhy whose kind is callback:… or dispatch:…" —
            # three conjuncts, not two. This branch used to stop at `unresolved is True` and only ever
            # READ `why` for the message, never gated on it. MEASURED against a real report: a genuine
            # swift dispatch site (`Widget.fire` calling a protocol-typed field through which a
            # synthesised conformer is reachable) carries Unknown + unresolved:true with `unknownWhy`
            # entirely ABSENT, and this checker said OK. An engine that emits unresolved:true with no
            # unknownWhy, an empty one, or one drawn from the wrong vocabulary (`reflect:`/`native:`
            # are real kinds elsewhere in the spec, just not the two this clause licenses) has disclosed
            # THAT it doesn't know, never WHY — which is exactly the gap `callers --include-unknown`
            # exists to close, and a consumer reading this report has no way to tell a genuine ⟨0.35⟩
            # hedge from a bare Unknown that happens to have the flag set.
            kinds = {str(w).split(":", 1)[0] for w in why if isinstance(w, str) and ":" in str(w)}
            if not why or not (kinds & {"callback", "dispatch"}):
                return False, (
                    "`%s` carries Unknown + unresolved:true but `unknownWhy` is %r — the clause requires "
                    "unresolved:true AND an unknownWhy whose kind is callback: or dispatch:, not either "
                    "alone. A missing, empty, or off-vocabulary unknownWhy discloses THAT the engine does "
                    "not know, never WHY, which is not what (b) asks for." % (caller, why)
                )
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

    The two PASSING shapes the disjunction allows, and the FAILING ones the clause forbids — including
    ABSENCE, which is the shape this file exists for, and three unknownWhy-shaped failures added after
    a real swift report was found carrying Unknown + unresolved:true with `unknownWhy` MISSING
    entirely: the clause's (b) names three conjuncts (Unknown, unresolved:true, AND an unknownWhy of
    the right kind), and this file used to check only the first two.
    """
    import tempfile, os
    cases = [
        ("completed",  {"functions": [{"fn": "app.Caller.go", "inferred": ["Fs"]}]},                       True),
        ("disclosed",  {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"], "unresolved": True,
                                       "unknownWhy": ["callback:java.lang.Runnable.run"]}]},               True),
        ("ABSENT",     {"functions": [{"fn": "app.Other.x", "inferred": ["Fs"]}]},                         False),
        ("present-pure", {"functions": [{"fn": "app.Caller.go", "inferred": []}]},                         False),
        ("unknown-no-flag", {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"]}]},             False),
        # MEASURED shape: a real candor-swift report, `unknownWhy` key entirely absent.
        ("unknown-flag-no-why", {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"],
                                                 "unresolved": True}]},                                    False),
        ("unknown-flag-empty-why", {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"],
                                                    "unresolved": True, "unknownWhy": []}]},                False),
        # Off-vocabulary kind: `reflect:`/`native:` are real ⟨0.7⟩ kinds elsewhere, just not the two
        # ⟨0.35⟩(b) licenses (callback:/dispatch:) — so this must fail, not pass on "any kind present".
        ("unknown-flag-wrong-kind-why", {"functions": [{"fn": "app.Caller.go", "inferred": ["Unknown"],
                                                         "unresolved": True,
                                                         "unknownWhy": ["reflect:some.reflective.call"]}]},
         False),
        # SAME-SIMPLE-NAME COLLISION, different packages, caller passed unqualified as the fixture
        # would. TWO distinct functions both end in `.Widget.fire` and neither is an exact match — the
        # old first-match-wins `endswith` matcher silently scored whichever sorted first (report
        # order), with no way for a reader to know a second, DIFFERENT candidate existed. Note the
        # narrower thing this closes: it catches ambiguity WITHIN one report (two candidates present).
        # It cannot detect the harder residual — a single confusable look-alike present while the real
        # target is simply absent from the report entirely, which is indistinguishable from "there is
        # only one candidate and it matched" without an a-priori fully-qualified name.
        ("suffix-collision-two-candidates", {"functions": [
            {"fn": "pkgA.Widget.fire", "inferred": ["Unknown"], "unresolved": True,
             "unknownWhy": ["dispatch:pkgA.Widget.task"]},
            {"fn": "pkgB.Widget.fire", "inferred": []},
        ]}, False, "Widget.fire"),
        # CONTROL: an EXACT match must win even when a same-simple-name collision is also present in
        # the same report — the collision guard must not become its own false red.
        ("exact-match-wins-over-collision", {"functions": [
            {"fn": "pkgA.Widget.fire", "inferred": ["Unknown"], "unresolved": True,
             "unknownWhy": ["dispatch:pkgA.Widget.task"]},
            {"fn": "pkgB.Widget.fire", "inferred": ["Fs"]},
        ]}, True, "pkgB.Widget.fire"),
    ]
    bad = 0
    for case in cases:
        label, doc, want = case[0], case[1], case[2]
        caller = case[3] if len(case) > 3 else "app.Caller.go"
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh)
        got, reason = verdict(path, caller, "Fs")
        os.unlink(path)
        mark = "ok " if got == want else "FAIL"
        if got != want:
            bad += 1
        print("  %s %-30s want=%-5s got=%-5s  %s" % (mark, label, want, got, reason[:88]))
    if bad:
        print("CHA CHECK SELFTEST: FAILED — %d case(s) wrong" % bad)
        return 1
    print("CHA CHECK SELFTEST: OK — %d cases, both passing shapes and every failing shape (including "
          "ABSENCE, the three unknownWhy gaps, and the suffix-collision hazard) are distinguished"
          % len(cases))
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
