#!/usr/bin/env python3
"""
PART 48 — THE FILE SET: what a report says about code it never opened (SPEC §2 ⟨0.29⟩).

⟨0.21⟩ gave the report a completeness manifest, and `unanalyzed` names files an engine OPENED and could
not read. It says nothing about files never opened at all, and a consumer cannot tell the two apart:
`analyzed.count` is a NUMERATOR whose denominator — the engine's file selector — is invisible.

MEASURED FOUR-WAY, 2026-08-15/16, one fixture shape per engine: a same-language source performing `Exec`,
sitting outside that engine's selector, under a policy of `deny Exec`. All four answered `policy ✓` /
`no violations`, exit 0, with no note on stderr, no key in the report and no exit code — a false all-clear
under an explicit deny, in every engine. The four AGREED, which by this project's own standing rule is the
weakest evidence of correctness available: it is common-mode, and here it was common-mode wrong.

WHAT THIS ROW ASSERTS, and why each half is here rather than a subset of it
--------------------------------------------------------------------------
The rung's whole design is its BOUNDS. A part that only checked "the warning fires" would pass against an
engine that reports every file it ever skipped under every policy — which is the noise floor that makes a
gate one people scroll past, and the failure this rung is most likely to regress into. So:

  · the FINDING          `deny Exec` over the fixture reports the out-of-scope Exec, and the reason string
                         says the gate did not judge it — asked of the VALUE, not the key's presence.
  · the VERDICT ⟨0.30⟩   same run: exit 2 (`ok:false`, `incomplete:true`), and the out-of-scope fn STILL
                         absent from `functions` and from `violations`. ⟨0.29⟩ asserted the exit was
                         UNMOVED here; ⟨0.30⟩ reverses that half on the measurement that the peek resolves
                         a CONCRETE denied effect (axios 37 fns `performs Net`, exit 0, `policy ✓`). The
                         membership half is unchanged and is the reason the code is 2 and not 1: the gate
                         did not judge this unit, so a violation claim would be false the other way.
  · POLICY-BOUNDED       `deny Net` over the SAME tree says nothing about the same `Exec`.
  · POLICY-SCOPED        no policy at all ⇒ the key is ABSENT, not `[]`. Nothing was asked, so an empty
                         list would be a claim (⟨0.26⟩: absence means "this producer cannot answer").
  · the CONTROL          a project with nothing to exclude still EMITS `excluded`, as `[]`. Without this
                         the part passes against an engine that fails everything, which is the
                         vacuous-control shape this project keeps measuring in its own work.
  · `peeked` READ        the class carrying the finding declares `peeked: true`, and every entry carries
                         the four keys with `peeked` a real boolean. An empty `outOfScope` is a claim only
                         about classes marked true, so a block that omits the flag cannot be read at all.
  · the TWIN             the same code, scanned as an ORDINARY TARGET, carries the same effect set the
                         peek reported for it.

THE TWIN ARM IS HOW §2's "never a second analysis path" BECOMES OBSERVABLE. No row can read which code
path produced a finding, and a MUST no row can exercise is the shape this suite's own ledger exists to
stop accumulating. What a row CAN see is the property that constraint protects: a peek that drifted from
the gate answers differently about the same code. So each engine is asked the same question twice — once
through the peek, once by pointing an ordinary scan at that code — and the two effect sets must agree.
It does not prove one code path; it fails exactly when two of them have diverged, which is when the
distinction starts to matter to a reader.

DELIBERATELY NOT ASSERTED: the `class` TOKENS. They are engine-chosen by §2 — the selectors differ per
language (`build-script`, `harness-target`, `source-without-class`) — and pinning a shared enumeration
would force one engine to file its exclusion under another's name. The row takes the class from the
finding and checks the block agrees with itself, which is the property that actually has to hold.

FALSIFIED BOTH WAYS before it was trusted (2026-08-16): an engine that reports the finding under
`deny Net` DIVERGES on the bound; an engine that emits `outOfScope: []` with no policy DIVERGES on the
scope; an engine that omits `excluded` on a clean project DIVERGES on the control.
"""
import json
import sys


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:                                    # noqa: BLE001 — the diagnosis IS the message
        return {"__unreadable__": f"{path}: {e}"}


def fail(engine, msg):
    print(f"  {engine:6} -> DIVERGE  ({msg})")
    return 1


def main():
    if len(sys.argv) != 10:
        print("usage: file_set_check.py <engine> <rc_exec> <rpt_exec> <rc_net> <rpt_net> "
              "<rpt_none> <rpt_control> <rpt_twin> <effect>")
        return 2
    engine, rc_exec, p_exec, rc_net, p_net, p_none, p_ctl, p_twin, effect = sys.argv[1:]
    engine = engine.strip()

    d_exec, d_net, d_none, d_ctl, d_twin = (load(p) for p in (p_exec, p_net, p_none, p_ctl, p_twin))
    for label, d in (("deny-" + effect, d_exec), ("bound", d_net), ("no-policy", d_none),
                     ("control", d_ctl), ("twin", d_twin)):
        if "__unreadable__" in d:
            # A MISSING REPORT MUST NOT READ AS A PASSING ROW. Every assertion below is about a key being
            # present, absent or empty, and an unreadable file answers "absent" to all of them — so the
            # scoped and bounded arms would both pass on a scan that never ran.
            return fail(engine, f"the {label} report is unreadable: {d['__unreadable__']}")

    # ── the FINDING ───────────────────────────────────────────────────────────────────────────────
    oos = d_exec.get("outOfScope")
    if not isinstance(oos, list):
        return fail(engine, f"`deny {effect}` produced no `outOfScope` list — a configured policy must "
                            "answer, even with []")
    hits = [f for f in oos if effect in (f.get("effects") or [])]
    if not hits:
        return fail(engine, f"the out-of-scope {effect} was not reported — this is the measured "
                            f"false all-clear the rung exists to close: {oos}")
    f0 = hits[0]
    if "did NOT judge" not in (f0.get("reason") or ""):
        return fail(engine, "the finding's reason does not say the gate did not judge it — a warning "
                            f"whose text a reader cannot act on: {f0.get('reason')!r}")
    if not (f0.get("path") or "").strip():
        return fail(engine, f"the finding names no file, so nobody can go and look: {f0}")

    # ── the VERDICT INCOMPLETE ⟨0.30⟩ ─────────────────────────────────────────────────────────────
    # ⟨0.29⟩ asserted the opposite here (exit UNMOVED). ⟨0.30⟩ reverses the exit-code half on the
    # measurement that the peek resolves a CONCRETE denied effect rather than uncertainty; the
    # STRUCTURAL half below is unchanged, because the gate still did not judge this unit.
    if rc_exec != "2":
        return fail(engine, f"exit {rc_exec} under `deny {effect}` — a peeked function performs the denied "
                            "effect, so the verdict is INCOMPLETE (exit 2), not a pass (⟨0.30⟩)")
    fns = {e.get("fn") for e in (d_exec.get("functions") or [])}
    if f0.get("fn") in fns:
        return fail(engine, f"`{f0.get('fn')}` is in `functions` as well — the peek folded an unjudged "
                            "unit into the judged set. ⟨0.30⟩ moves the EXIT CODE, not the membership: "
                            "exit 2 says `I could not see enough`, and claiming a violation over code the "
                            "gate never judged would be false in the other direction")
    viols = {(e.get("fn") if isinstance(e, dict) else e) for e in (d_exec.get("violations") or [])}
    if f0.get("fn") in viols:
        return fail(engine, f"`{f0.get('fn')}` was reported as a VIOLATION — ⟨0.30⟩ makes the verdict "
                            "incomplete, never a violation: the gate did not judge this unit")

    # ── POLICY-BOUNDED ────────────────────────────────────────────────────────────────────────────
    bound = d_net.get("outOfScope")
    if not isinstance(bound, list):
        return fail(engine, "the bound policy produced no `outOfScope` list — a configured policy still "
                            "answers, with []")
    if bound:
        return fail(engine, f"a policy denying a DIFFERENT effect reported {len(bound)} finding(s) — "
                            f"unbounded, the noise floor is everything you excluded: {bound}")
    if rc_net != "0":
        return fail(engine, f"exit {rc_net} under the bound policy, expected 0")

    # ── POLICY-SCOPED ─────────────────────────────────────────────────────────────────────────────
    if "outOfScope" in d_none:
        return fail(engine, "with NO policy the key is present — nothing was asked, so any value there "
                            f"is a claim (⟨0.26⟩): {d_none['outOfScope']!r}")

    # ── the CONTROL, the row that matters most ────────────────────────────────────────────────────
    ctl = d_ctl.get("excluded")
    if not isinstance(ctl, list):
        return fail(engine, "a project with nothing to exclude OMITS `excluded` — absence means "
                            "'cannot answer', which is a different claim from 'nothing was excluded'")
    if ctl:
        return fail(engine, f"the control project excluded {len(ctl)} class(es) — either the fixture is "
                            f"not clean or the block is inventing exclusions: {ctl}")

    # ── `peeked` READ, and the block agreeing with its own finding ────────────────────────────────
    exc = d_exec.get("excluded")
    if not isinstance(exc, list) or not exc:
        return fail(engine, "the fixture excluded a file and the block does not say so — the finding "
                            f"and the scope disagree: {exc!r}")
    for e in exc:
        missing = [k for k in ("class", "count", "peeked", "reason") if k not in e]
        if missing:
            return fail(engine, f"an `excluded` entry is missing {missing}: {e}")
        if not isinstance(e["peeked"], bool):
            return fail(engine, f"`peeked` is not a boolean, so a consumer cannot branch on it: {e}")
        if len((e.get("reason") or "").split()) < 6:
            return fail(engine, "a reason that short is a label, not a reason — a consumer reads it to "
                                f"decide whether the exclusion matches their question: {e}")
    owner = [e for e in exc if e.get("class") == f0.get("class")]
    if not owner:
        return fail(engine, f"the finding's class {f0.get('class')!r} appears in no `excluded` entry — "
                            f"the peek read a class the scope block never declared: {exc}")
    if not owner[0].get("peeked"):
        return fail(engine, f"the class the peek READ is declared `peeked: false`: {owner[0]}")

    # ── the TWIN: the same code as an ORDINARY TARGET answers the same way ────────────────────────
    # §2 requires the peek to reach its finding through the engine's ordinary analysis path over a
    # different FILE SET, never a second path. Nothing can observe which path ran; what IS observable is
    # the disagreement that constraint exists to prevent.
    want = set(f0.get("effects") or [])
    twin_sets = [set(e.get("inferred") or []) for e in (d_twin.get("functions") or [])]
    if not twin_sets:
        return fail(engine, "the twin scan found no effectful unit at all — the fixture's excluded code "
                            "reads as pure when scanned directly, so the arm cannot compare anything")
    if not any(want <= s for s in twin_sets):
        return fail(engine, f"the peek reported {sorted(want)} for `{f0.get('fn')}`, but the same code "
                            f"scanned as an ordinary target carries {[sorted(s) for s in twin_sets]} — "
                            "the peek and the gate disagree about identical code, which is the drifted "
                            "second opinion §2 forbids")

    unpeeked = [e["class"] for e in exc if not e["peeked"]]
    note = f"; unpeeked: {','.join(unpeeked)}" if unpeeked else ""
    print(f"  {engine:6} -> MATCH    (finds it: {f0['fn']} in {f0['path']}; verdict 2, not in functions; "
          f"bound: []; no policy: absent; control: []; twin agrees on {'+'.join(sorted(want))}{note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
