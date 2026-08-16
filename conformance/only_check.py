#!/usr/bin/env python3
"""
PART 49 — THE `only <A> -> <B> …` PERMISSION FORM (SPEC §6.2 ⟨0.29⟩, AS-EFF-009).

`forbid` can state a PROHIBITION but not a PERMISSION. It fails OPEN — the dependency you forgot to
prohibit is silently permitted — so "this package is a leaf" can only be spelled as an enumeration of what
it must not reach, a list that does not cover a package added tomorrow and says nothing about it. That is
the allowlist hazard the family refuses throughout the ANALYSIS, sitting in the POLICY LANGUAGE. Found by
pointing candor's own architecture gate at candor: the natural `forbid <pkg>.model -> <pkg>` SELF-FIRES,
because a scope matches a contiguous run of segments and `model` sits under the prefix it is protecting
itself from.

THE ROWS ARE THE THREE RULINGS, not the violation. Any engine that walks a call graph will produce the
violation; what a differential has to hold is the three decisions §6.2 pins, each of which could plausibly
have gone the other way and each of which SILENTLY changes what a policy means:

  · PERMITS + OMITS   the list is a LIST (several destinations), and what it omits is a violation.
  · the STOP RULE     a permitted callee's own dependencies are NOT this rule's business. Descending past
                      a permitted scope would demand the transitive closure of everything you permit —
                      the same enumeration-that-rots one level down, which would make the form useless
                      for the leaf case it exists for. THE FIXTURE PUTS AN UNPERMITTED SCOPE BEHIND A
                      PERMITTED ONE so an engine that descends fails here and nowhere else.
  · ZERO-MATCH ON `from`   measured on the leading scope ALONE, unlike `forbid` which counts either
                      endpoint. A rule whose destinations all resolve while its `from` names nothing has
                      bound nothing — precisely the typo that leaves an operator believing a leaf is
                      protected. The fixture's destination RESOLVES, so an engine counting either
                      endpoint stays silent and fails this row.
  · ARMED, NOT EMPTY  an `only`-only policy is a live gate; refusing it as a zero-rule file would turn
                      ⟨0.28⟩'s fail-closed guard into a false refusal by the rung that added the kind.
  · REPORT ROUTE      refused at exit 2, and NO AS-EFF-009 drawn. Stricter than `forbid`'s case: `forbid`
                      asks whether one named crossing is present, `only` asks whether EVERYTHING reached
                      is on a list, so a report that omits a crossing turns a green into a claim of
                      COMPLETENESS. The row checks BOTH — an engine that discloses the rule and evaluates
                      it anyway prints a violation beside the refusal, which is what a partial
                      implementation produces (measured in candor-java during the port: the removal site
                      and the disclosure site were fifty lines apart and only one was updated).

THE ARMS ARE NOT EQUALLY STRONG, and saying so is the point of writing it down. The report-route row was
FALSIFIED in candor-rust (it found a live defect — see below) and in candor-swift. It CANNOT fail in
candor-ts, because that engine hands `evaluatePolicy` an EMPTY call graph on the report route
(`evaluatePolicy(gwp.answerable, g.functions, {}, …)`), so a NAME-matching rule left in the policy has
nothing to walk whatever the removal does. That is a second, structural guarantee rather than a gap — but
a reader must not conclude the ts arm exercises the removal, because it does not.

WHAT THIS ROW CAUGHT, on the day it was written: candor-rust DISCLOSED the `only` rule as unanswerable and
then evaluated it anyway, printing `[AS-EFF-009] model::leaks reaches infra::db_read` beside its own
statement that the rule could not be evaluated. A rule evaluated from a report is the §3.1 MUST the
disclosure exists to enforce. The same defect shipped in candor-java for one build. Both had the same
shape: the removal site is fifty lines from where the kind is added, and only the one you are editing gets
updated.

`A -> A` IS IMPLICIT and is covered by construction rather than by its own row: every fixture's `from`
scope calls within itself, so an engine without the implicit self-permission fires on the permitted arm
and fails the first row. Stated here because a reader looking for the ruling should find where it is
tested, not conclude it is untested.
"""
import json
import sys


def fail(engine, msg):
    print(f"  {engine:6} -> DIVERGE  ({msg})")
    return 1


def main():
    if len(sys.argv) != 10:
        print("usage: only_check.py <engine> <rc_short> <out_short> <rc_full> <out_full> "
              "<rc_zero> <err_zero> <gate_rc> <gate_out>")
        return 2
    # The report route's exit code and output are TWO arguments, deliberately. They were one, joined on a
    # NUL — which bash strips from a command substitution, so the checker read "2candor-query gate: …" as
    # an exit code and every engine DIVERGED with an unreadable diagnostic. The instrument was broken in a
    # way that looked like four engines failing identically.
    engine, rc_short, out_short, rc_full, out_full, rc_zero, err_zero, gate_rc, gate_out = sys.argv[1:]
    engine = engine.strip()

    # ── PERMITS + OMITS ───────────────────────────────────────────────────────────────────────────
    if rc_short != "1":
        return fail(engine, f"`only A -> B` exited {rc_short} over a tree where A reaches an UNLISTED "
                            "scope, expected 1 — the form's entire purpose is that what the list omits "
                            "is a violation")
    # ⟨0.29⟩ ITS OWN CODE, and the row asserts BOTH halves: 011 present AND 009 absent. A rule code is the
    # handle a CI suppression keys on, so sharing `forbid`'s would make an existing suppression silently
    # mute a class of violation its author never accepted. Asserting only "011 appears" would pass on an
    # engine that emitted both, which is the same collision wearing a second label.
    if "AS-EFF-011" not in out_short:
        return fail(engine, f"the violation is not charged as AS-EFF-011: {out_short[:200]}")
    if "AS-EFF-009" in out_short:
        return fail(engine, "an `only` violation is ALSO charged as AS-EFF-009 — `forbid`'s code. A "
                            "suppression written for a forbid crossing would silently mute this: "
                            f"{out_short[:200]}")
    if "infra" not in out_short:
        return fail(engine, "the message never names what was reached, so an operator is told a rule "
                            f"fired and not what tripped it: {out_short[:200]}")
    if "only model -> util" not in out_short:
        return fail(engine, f"…and it never names the RULE that says so: {out_short[:200]}")

    # ── the LIST, and the STOP RULE, on one run ───────────────────────────────────────────────────
    if rc_full != "0":
        return fail(engine, f"`only A -> B C` exited {rc_full}, expected 0. Either the tail is not read "
                            "as a LIST, or the walk descended PAST a permitted scope — `util` is "
                            "permitted and reaches `deep`, which no rule permits, and a rule that "
                            "demands the closure of everything you permit is unusable for a leaf")
    if "deep" in out_full:
        return fail(engine, f"`deep` sits BEYOND a permitted scope and must not be reported: {out_full[:200]}")

    # ── ZERO-MATCH ON `from` ──────────────────────────────────────────────────────────────────────
    if rc_zero != "0":
        return fail(engine, f"a zero-match rule exited {rc_zero} — it is a DISCLOSURE beside the verdict, "
                            "never a verdict change (a shared policy legitimately names layers a given "
                            "repo does not have)")
    if "matched NO function" not in err_zero:
        return fail(engine, "a rule whose `from` names nothing was NOT disclosed. Its destination "
                            "resolves, so an engine counting either endpoint the way `forbid` does "
                            f"stays silent here — which is the typo that leaves a leaf unprotected: {err_zero[:200]}")
    if "only nosuch -> util" not in err_zero:
        return fail(engine, f"the disclosure never names the rule: {err_zero[:200]}")

    # ── ARMED, NOT EMPTY ──────────────────────────────────────────────────────────────────────────
    if "NO RULES" in out_full:
        return fail(engine, "an `only`-only policy was refused as a zero-rule file — ⟨0.28⟩'s "
                            "fail-closed guard turned into a false refusal by the rung that added the kind")

    # ── the REPORT ROUTE ──────────────────────────────────────────────────────────────────────────
    if gate_rc != "2":
        return fail(engine, f"`gate --report` exited {gate_rc} over an `only` policy, expected 2. §3.1: a "
                            "rule whose evidence the wire does not carry MUST be refused, never evaluated")
    if "only model -> util" not in gate_out:
        return fail(engine, f"the refusal never names the rule: {gate_out[:200]}")
    if "AS-EFF-009" in gate_out:
        return fail(engine, "a violation was drawn from a REPORT. The rule was disclosed as unanswerable "
                            "and then evaluated anyway, which is what a partial implementation produces: "
                            "the disclosure stands beside the very evaluation it says did not happen")

    print(f"  {engine:6} -> MATCH    (omits: exit 1 naming the reach and the rule; list+stop: exit 0, "
          f"`deep` unreported; zero-match on `from`: disclosed, exit 0; armed; report route: refused, "
          f"no 009)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
