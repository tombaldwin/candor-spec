#!/usr/bin/env python3
"""
PART 85 — THE PEEK SCOPE-MATCH PROPERTY, and the CONDITIONAL `dispatch-widened` fallback (SPEC §2 ⟨0.34⟩).

FOUR-WAY CARDINAL SIN, found and closed 2026-08-29 (swift `7378f4f`, rust `27f4beb`, java `a034371`,
ts `8584572`): a peek finding is attributed to the EXCLUDED declaration (correct, unchanged by any of the
four fixes), but the `<scope>` test a `deny`/`pure` rule runs (SPEC §6.2 "Scope matching") was run ONLY
against that declaration's own qualified name. So a rule scoped to the IN-SCOPE CALLER that reaches the
excluded declaration only through dynamic dispatch (an interface/protocol/trait/structural-conformer typed
receiver) could never match, and a real, denied effect passed silently at exit 0 — while the identical tree
under the UNSCOPED form of the same rule already caught it, isolating the SCOPE STRING as the only variable
that mattered.

THE FIXTURE, one shape, four languages: an in-scope dispatcher (`Runner`/`RunnerCaller`/`RunnerMain`)
reaches a shared interface-typed value through a factory or direct dispatch; the only conformer/implementer
VISIBLE to the primary scan is pure (`PureDoer`); a SEPARATE, EXCLUDED declaration (`EvilDoer`, in a
test-source / non-library-target / `source-without-class` / `.test.ts` file — each engine's own ⟨0.29⟩
exclusion class) conforms to the SAME interface and performs `Net`. Three policies over the identical tree:

  scoped   `deny Net Runner`       — the defect. Must now name the excluded declaration and exit 2.
  unscoped `deny Net`              — the pre-existing control: already caught before any of the four
                                      fixes (the excluded declaration's own name matches trivially), and
                                      must stay EXACTLY ONE finding — a widened scope test must not also
                                      double-report the declaration it already named on its own.
  nomatch  `deny Net NoSuchCaller` — the OVER-CHARGE CONTROL on the SAME tree: a scope matching neither the
                                      excluded declaration NOR any function that reaches it must stay
                                      exit 0, `outOfScope: []` — proving the widened test does not degrade
                                      into "any exclusion, any scope".

THE `dispatch-widened` CONDITIONAL. In THIS fixture, attribution is never ambiguous — exactly one excluded
declaration (`EvilDoer.work`) explains the new effect — so every engine that can name it MUST do so, and
MUST NOT fall back to `dispatch-widened`: an engine disclosing an ambiguity that was never there degrades
the class into the blanket "everything is Unknown" hedge SPEC ⟨0.19⟩ exists to prevent. This is the
OVER-CHARGE control the BACKLOG item asks for, checked on every engine that runs this row. Separately,
`--forbid-widened-corpus` (rust only) asserts the class appears in NONE of the three reports at all: rust's
peek never unions in-scope and excluded material, so its attribution is never ambiguous by construction and
it MUST NOT be required to carry vocabulary for a case it can never reach (SPEC §2 ⟨0.34⟩).

DELIBERATELY NOT ASSERTED HERE: a genuine `dispatch-widened`-FIRING case (an excluded declaration's identity
that cannot be named with confidence). That shape is engine-mechanism-specific (ts's own regression suite
exercises it via an unresolvable `paths`-mapped interface reference: `8584572`); reproducing an equally
load-bearing ambiguous case for swift/java here would pin an implementation detail of ONE mechanism as if
it were the four-way property, which it is not. The property this row pins is the one all four fixes share:
the scope test widens, attribution does not, and the fallback only fires when attribution genuinely cannot.
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
    if len(sys.argv) != 8:
        print("usage: peek_scope_check.py <engine> <rc_scoped> <rpt_scoped> <rc_unscoped> <rpt_unscoped> "
              "<rc_nomatch> <rpt_nomatch>")
        return 2
    engine, rc_sc, p_sc, rc_un, p_un, rc_nm, p_nm = sys.argv[1:]
    engine = engine.strip()

    d_sc, d_un, d_nm = (load(p) for p in (p_sc, p_un, p_nm))
    for label, d in (("scoped", d_sc), ("unscoped", d_un), ("nomatch", d_nm)):
        if "__unreadable__" in d:
            return fail(engine, f"the {label} report is unreadable: {d['__unreadable__']}")

    # ── THE DEFECT, closed: `deny Net Runner` must now catch it ──────────────────────────────────────
    if rc_sc != "2":
        return fail(engine, f"exit {rc_sc} under the scope-matched rule — a rule scoped to the IN-SCOPE "
                            "CALLER must still catch an effect reached only through it via dynamic "
                            f"dispatch into excluded code: this is the cardinal sin: {json.dumps(d_sc)[:400]}")
    oos_sc = d_sc.get("outOfScope")
    if not isinstance(oos_sc, list):
        return fail(engine, "a configured policy must answer `outOfScope`, even with []")
    hits_sc = [e for e in oos_sc if "Net" in (e.get("effects") or [])]
    if len(hits_sc) != 1:
        return fail(engine, f"expected exactly one Net finding, got {len(hits_sc)}: {oos_sc}")
    h = hits_sc[0]
    ident = f"{h.get('fn', '')} {h.get('path', '')}".lower()
    if "runner" in ident:
        return fail(engine, f"ATTRIBUTION CONTROL failed — the finding names the in-scope CALLER, not "
                            f"the excluded declaration: {h}")

    # ── THE OVER-CHARGE CONTROL: attribution is UNAMBIGUOUS here, so `dispatch-widened` MUST NOT fire ──
    if h.get("class") == "dispatch-widened":
        return fail(engine, "attribution is unambiguous in this fixture (exactly one excluded declaration "
                            "explains the new effect) — the engine fell back to `dispatch-widened` instead "
                            f"of naming it, which is the over-charge direction SPEC ⟨0.34⟩ forbids: {h}")

    # ── THE UNSCOPED CONTROL: already caught, and not doubled now two attribution routes could match ──
    if rc_un != "2":
        return fail(engine, f"exit {rc_un} under the UNSCOPED rule — this was ALREADY caught before any "
                            f"of the four fixes; if this fires the fixture itself is unsound: {d_un}")
    oos_un = d_un.get("outOfScope")
    if not isinstance(oos_un, list):
        return fail(engine, "the unscoped policy produced no `outOfScope` list — a configured policy must "
                            "answer, even with []")
    hits_un = [e for e in oos_un if "Net" in (e.get("effects") or [])]
    if len(hits_un) != 1:
        return fail(engine, f"expected exactly ONE finding under the unscoped rule (no duplicate from the "
                            f"widened scope test running ALONGSIDE the declaration's own matching name), "
                            f"got {len(hits_un)}: {oos_un}")

    # ── THE OVER-CHARGE CONTROL, the row that matters most: a scope matching NOTHING reachable ────────
    if rc_nm != "0":
        return fail(engine, f"exit {rc_nm} under a scope matching neither the excluded declaration nor any "
                            f"reaching caller — the widened scope test degraded to \"any exclusion, any "
                            f"scope\": {d_nm}")
    oos_nm = d_nm.get("outOfScope")
    if not isinstance(oos_nm, list):
        return fail(engine, "a configured (non-matching) policy must still answer `outOfScope`, even []")
    if oos_nm:
        return fail(engine, f"a scope matching nothing reachable reported {len(oos_nm)} finding(s) — the "
                            f"over-charge control this row exists for: {oos_nm}")

    print(f"  {engine:6} -> MATCH    (scoped rule catches {h.get('fn')!r} via caller dispatch, exit 2, "
          f"class={h.get('class')!r}; unscoped stays a single finding; non-matching scope stays silent)")
    return 0


def forbid_widened_corpus(engine, *paths):
    """rust ONLY: its peek never unions in-scope and excluded material (SPEC §2 ⟨0.34⟩ — attribution is
    never ambiguous by construction), so it MUST NOT be required to carry `dispatch-widened` and this
    asserts it never does, across every report this row produced — not merely absent from one fixture."""
    for p in paths:
        d = load(p)
        if "__unreadable__" in d:
            return fail(engine, f"cannot check for a structural absence in an unreadable report: {p}")
        for e in (d.get("outOfScope") or []):
            if e.get("class") == "dispatch-widened":
                return fail(engine, f"rust's peek never unions — it MUST NOT emit `dispatch-widened` at "
                                    f"all, and it just did: {e}")
    print(f"  {engine:6} -> MATCH    (structural: `dispatch-widened` appears in none of its reports, as "
          f"SPEC ⟨0.34⟩'s conditional requires for an engine whose peek never unions)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--forbid-widened-corpus":
        sys.exit(forbid_widened_corpus(sys.argv[2], *sys.argv[3:]))
    sys.exit(main())
