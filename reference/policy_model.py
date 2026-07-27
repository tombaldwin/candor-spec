"""The POLICY LAYER of candor's formal model, executable.

This transcribes PAPER3's Definitions 4-7, 30-32, 35 and 36, and Lemma 2. It deliberately does NOT
transcribe Definitions 33 (`forbid`) and 34 (`allow`): a 2026-07-27 review established that both describe
verbs the deployment does not have — `forbid` is a call-graph dependency rule with no effect predicate, and
`allow` is a fail-closed literal-surface certification whose carrier is outside this lattice. PAPER3's
Proposition 5 has been rescoped accordingly, and a differential built on this file MUST NOT add rows for
them, nor for `deny E[dest...]`, nor for the `unknown-ratchet` (whose shipped form grandfathers a function
already disclosed at baseline, so Definition 35 as written rejects where every engine passes). Adding those
rows manufactures divergences out of the theory rather than finding them in the code.

Originally described as a transcription of PAPER3 Definitions 4-7 and
30-36, and of Lemma 2. It exists because those definitions are the one part of the system the paper
claims as PROVED, and until now nothing connected them to what the engines do.

WHY IT EXISTS, concretely. On 2026-07-27 a shipped engine took `deny Unknown[unresolved]` from a
REJECT to a PASS when a call was ADDED to the function under test — a direct counterexample to
Lemma 2's corollary ("a newly-determined effect or a newly-disclosed blind spot can only turn a green
verdict red"). The lemma was not wrong. The engine had reached a signature the model does not admit
(`Unknown` determined with an EMPTY disclosure set) and coped with a rule that is nowhere in the
model: default the reason class to `unresolved` when `D` is empty. That rule is keyed on ABSENCE, and
absence is not upward-closed.

Nothing in the toolchain could have caught that, because the model lived only in prose. This file is
the model as code, so an engine's gate can be differentially tested against the definitions rather
than against another engine's opinion.

THIS FILE IS NOT A GATE. It computes no effects and reads no report. It is a reference for `Reject`
alone — the part that is small, pure, total, and provable.
"""

from itertools import combinations, chain

# ---------------------------------------------------------------------------------------------
# Definition 1 (capability effects) and the refinement preorder ⊑ₑ.
#
# ⟨2026-07-27⟩ **`Llm ⊑ₑ Net` ONLY. `Db ⋢ₑ Net`, and that is a correction, not an omission.**
# PAPER3 Definition 2 carried both, on SPEC §1's sentence "Llm refines Net the way Db does". They are not
# the same relation. An effect refines a base channel only when EVERY occurrence of it is an occurrence of
# that channel: a model-provider call is an outbound request in every instance (and the engines co-emit
# both), whereas an embedded, file-backed or in-process store is a `Db` effect with NO egress at all (and
# the engines emit `Db` alone).
#
# It was extensional, not cosmetic. With `Db ⊑ₑ Net` here, a differential of the JVM engine against this
# file produced 100 disagreements over 1792 rows (256 signatures x 7 verbs) — every one that family, model
# REJECT and engine pass. The engines were right. Correcting the preorder rather than widening the verb
# also avoids the fabrication mirror: firing `deny Net` on `{Db}` charges every embedded-database user with
# network egress they do not have.
#
# NOT repaired by this: a NETWORKED database call is real egress a `deny Net` gate does not see. That is a
# classification question (can an analyzer tell a networked store from an embedded one at a call site), not
# a defect in this algebra. `Db` and `Net` OVERLAP without either refining the other, which a preorder on
# effect NAMES cannot express.
# `Unknown` is NOT an effect in the model — it is the NAME of the `D ≠ ∅` posture (Definition 6), and
# treating it as a member of `E` is one of the ways an implementation drifts out of the model.
# SPEC §1's effect vocabulary IN FULL. `Ipc` and `Clipboard` were missing until a review caught it —
# harmless to Lemma 2 (whose proof is vocabulary-independent) but fatal to this file's ACTUAL job: a real
# report carrying `Clipboard` would have tripped `Sig`'s assert on the first differential run against an
# engine. `Unknown` is deliberately NOT here — it is not an effect (Def 6); it is carried by `D ≠ ∅`.
E = ("Clipboard", "Clock", "Db", "Env", "Exec", "Fs", "Ipc", "Llm", "Log", "Net", "Rand")
_REFINES = {("Llm", "Net")}


def refines(a: str, b: str) -> bool:
    """`a ⊑ₑ b` — a is a refinement of b. Reflexive; the preorder of Definition 3."""
    return a == b or (a, b) in _REFINES


# Definition 5 (disclosure reasons). The closed set R.
R = ("reflect", "dispatch", "indirect", "native", "unresolved", "setup")


class Sig:
    """Definition 6 (effect signature): a pair `(S, D)`, `S ⊆ E`, `D ⊆ R`.

    `D = ∅` means SOUND-COMPLETE. `D ≠ ∅` means the signature carries `Unknown`, tagged with exactly
    the reasons `D`. Definition 6's last sentence is load-bearing and is asserted below: *the bare
    `Unknown` marker is the pair `(∅, {r})`* — a reason is CONSTITUTIVE of the marker, not decoration
    on it. A signature that is `Unknown` with no reason is not a point of this lattice at all.
    """

    __slots__ = ("S", "D")

    def __init__(self, S=(), D=()):
        self.S, self.D = frozenset(S), frozenset(D)
        assert self.S <= set(E), f"S ⊄ E: {self.S - set(E)}"
        assert self.D <= set(R), f"D ⊄ R: {self.D - set(R)}"
        # (W) well-formedness, from Definition 6. `Unknown` is not a member of E; if an implementation
        # hands us one it has already left the model, and saying so here is the whole point.
        assert "Unknown" not in self.S, (
            "`Unknown` is not an effect (Definition 6): it is the name of the `D ≠ ∅` posture. A "
            "signature carrying it in S has left the lattice — which is precisely the state the "
            "2026-07-27 monotonicity failure was reached through."
        )

    def leq(self, other) -> bool:
        """Definition 7 (product order): plain subset in BOTH components."""
        return self.S <= other.S and self.D <= other.D

    def join(self, other):
        """Proposition 1: join is componentwise union."""
        return Sig(self.S | other.S, self.D | other.D)

    def __repr__(self):
        return f"({sorted(self.S)}, {sorted(self.D)})"

    def __eq__(self, o):
        return self.S == o.S and self.D == o.D

    def __hash__(self):
        return hash((self.S, self.D))


# ---------------------------------------------------------------------------------------------
# Definition 36 (atomic gate predicates)

def phi(e: str, sig: Sig) -> bool:
    """`φₑ(S,D) := [ ∃ e' ∈ S. e' ⊑ₑ e ]` — Definition 4's firing condition."""
    return any(refines(x, e) for x in sig.S)


def psi(C, sig: Sig) -> bool:
    """`ψ_C(S,D) := [ D ∩ C ≠ ∅ ]`.

    NOTE WHAT IS ABSENT. There is no clause here for `D = ∅`, in the model or in this transcription.
    An implementation that reads an empty `D` as "class `unresolved`" has added a rule the model does
    not contain, and `monotonicity_counterexample()` below shows why that specific addition breaks
    Lemma 2.
    """
    return bool(sig.D & frozenset(C))


# ---------------------------------------------------------------------------------------------
# Definitions 30-32, 35 — the shipped verbs, as rejection predicates.

def deny(e: str):
    """Definition 30 (`deny e`). A non-empty `D` does NOT fire it — the analysis cannot assert `e`."""
    return lambda sig: phi(e, sig)


def deny_unknown(e: str, C=None):
    """Definition 31 (`deny e Unknown[c₁…cₖ]`). Bare `deny e Unknown` is `C = R`."""
    cs = frozenset(R if C is None else C)
    return lambda sig: phi(e, sig) or psi(cs, sig)


def pure_as_defined_in_paper3_def32():
    """PAPER3 Def 32 AS WRITTEN: reject `(S,D) ≠ (∅,∅)` — any effect OR any disclosure fails.

    **This is NOT the shipped verb.** Kept as an exhibit so the divergence stays visible rather than being
    quietly edited away. See `pure()` below for what the contract actually specifies, and the note there
    for which of the two was judged wrong.
    """
    return lambda sig: bool(sig.S) or bool(sig.D)


def pure():
    """`pure` AS THE CONTRACT SPECIFIES IT: `Reject(S,D) ⇔ S ≠ ∅`. A disclosure alone PASSES.

    **PAPER3 Def 32 and SPEC §4.0 disagreed, and the CONTRACT was judged right.** Def 32 says
    `Reject ⇔ (S,D) ≠ (∅,∅)` — any effect *or any disclosure* fails. SPEC §4.0's verb table says `pure` is
    "violated when `S ≠ ∅` (an effect) — `D ≠ ∅` alone is AS-EFF-003 **disclosure**, not AS-EFF-006", and
    §6.2 makes `pure` shorthand for "deny every effect", which does not fire on `D ≠ ∅`.

    The contract wins because the divergence is not an oversight there: an entire verb (`unverified`) exists
    to name the holes a `pure` layer PASSES without proving anything, and the documented upgrade path for an
    author who wants provable purity is `pure` PLUS `deny Unknown`. Changing the contract to match Def 32
    would delete that design; changing Def 32 costs a sentence.

    Why this mattered enough to find: the divergence is benign for Lemma 2 (both predicates are upward-
    closed, and the model was merely STRICTER), so no monotonicity counterexample exists and nothing would
    have gone red. But this file's purpose is to judge ENGINES against the definitions — so on `(∅, {r})`
    the first differential run would have reported all four conforming engines as violating, and the
    conclusion "four engines disagree with the theory" would have been an artefact of the theory.
    """
    return lambda sig: bool(sig.S)


def unknown_ratchet(baseline_D):
    """Definition 35. Against a FIXED baseline: `Reject(S,D) ⇔ D ⊄ D_b`."""
    b = frozenset(baseline_D)
    return lambda sig: not (sig.D <= b)


# ---------------------------------------------------------------------------------------------
# Lemma 2, checked rather than assumed.

def _lattice(effects, reasons):
    """Every point of a small sub-lattice of `L = 𝒫(E) × 𝒫(R)`."""
    def subsets(xs):
        return chain.from_iterable(combinations(xs, k) for k in range(len(xs) + 1))
    return [Sig(s, d) for s in subsets(effects) for d in subsets(reasons)]


def covers(sig: Sig):
    """The immediate successors of `sig` in `⊑`: add exactly one effect, or exactly one reason."""
    for e in E:
        if e not in sig.S:
            yield Sig(sig.S | {e}, sig.D)
    for r in R:
        if r not in sig.D:
            yield Sig(sig.S, sig.D | {r})


def check_upward_closed(reject, points) -> list:
    """Lemma 2: `Reject(x) ∧ x ⊑ y ⇒ Reject(y)`. Returns counterexamples.

    CHECKED AGAINST COVERS, NOT ALL PAIRS, and that is what makes this COMPLETE rather than a sample.
    Upward-closure is equivalent to closure under immediate successors: if `Reject` survives every
    single-element step it survives every chain, by induction on the length of the step sequence, and
    every `x ⊑ y` in a finite Boolean lattice is such a chain. So this is a proof for the given `E` and
    `R` rather than bounded model-checking of them — the whole lattice is 2^|E| × 2^|R| points and the
    work is linear in that, where the naive pair check is quadratic (10^9 for the real vocabulary, which
    is why the first version of this file could only afford a toy sublattice).
    """
    return [(x, y) for x in points if reject(x)
            for y in covers(x) if not reject(y)]


def full_lattice():
    """Every point of `L = 𝒫(E) × 𝒫(R)` for the REAL vocabulary — 2^9 × 2^6 = 32768 signatures."""
    return _lattice(E, R)


def psi_with_absence_default(C, sig):
    """THE OLD RULE. If the reason-class set is EMPTY, default it to `unresolved`.

    Keyed on ABSENCE, and absence is not upward-closed: acquiring a second, classifiable reason
    REMOVES the default. Kept here as an executable exhibit, not as a definition.
    """
    if not sig.D:
        return "unresolved" in C
    return bool(sig.D & frozenset(C))


def contribute_unresolved(sig, reasonless: bool):
    """THE ⟨0.24⟩ REPAIR, and modelling it correctly is the whole point of this function.

    The repair is NOT a different consumer predicate. It is a PRODUCER-side rule: an engine that has an
    `Unknown` it cannot account for puts `unresolved` INTO `D`. The consumer predicate is then plain ψ
    (Def 36) with no special case at all — which is why the spec says the repair "returns the system to
    the model rather than amending it", and why its soundness follows from `deny_unknown`'s existing
    upward-closure rather than needing a new proof.

    Modelling this needs a bit the `(S, D)` pair does not carry. `D` is a SET of classes, so it cannot
    distinguish "one Unknown, reasoned `dispatch`" from "two Unknowns, one reasoned `dispatch` and one
    reasonless" — both are `D = {dispatch}`. That distinction is exactly what the ⟨0.24⟩ change turns
    on, so it is passed in explicitly as `reasonless` rather than inferred from `D` being empty.
    Inferring it from emptiness is the OLD RULE wearing new clothes, and an earlier draft of this file
    did precisely that: it produced a green check that verified a strictly weaker property than the one
    the spec change makes, because with `D` empty the two rules coincide.

    AND THERE IS A SHARPER POINT UNDERNEATH, found by writing that draft and watching it fail. Def 6
    makes `D` the CARRIER of the Unknown: `D = ∅` *means* sound-complete, and `Sig` asserts
    `Unknown ∉ S` for exactly that reason. So a **reasonless Unknown is not representable in this model
    at all** — the report says "this function has an `Unknown`" and the only signature available to
    describe it, `(S, ∅)`, is the model's way of saying it has none.

    That is the real defect, and monotonicity was its symptom. The spec was carrying a rule about a
    state its own formal model says cannot exist, so no consumer-side predicate could have been written
    that handled it correctly — the old rule was not badly written, it was answering an ill-formed
    question. ⟨0.24⟩ is the PRODUCER-side repair that makes the state unreachable: an engine with an
    `Unknown` it cannot account for records `unresolved`, so `D ≠ ∅` whenever an `Unknown` is present,
    and the well-formedness condition (W) holds by construction. Monotone denial then follows from
    `deny_unknown`'s existing upward-closure with no new proof.
    """
    return Sig(sig.S, frozenset(sig.D | {"unresolved"}) if reasonless else sig.D)


# ---------------------------------------------------------------------------------------------
# REACHABILITY. `L` contains signatures no engine can produce, and a differential must know which.

# `Llm ⊑ₑ Net` (Definition 2) and every engine CO-EMITS both at an LLM call site — a model-provider
# request IS an outbound request, and that is the very fact that makes the refinement hold. So
# `Llm ∈ S ∧ Net ∉ S` describes 32768 of the lattice's 131072 points and NONE of them is reachable.
CO_EMIT = {"Llm": "Net"}


def is_reachable(sig) -> bool:
    """Well-formedness on REACHABLE signatures: a refinement never appears without its base channel.

    THIS IS THE CONDITION PAPER1's (W) WAS REACHING FOR AND MIS-STATED. (W) was written
    `Unknown ∈ S ⇒ D ≠ ∅`, whose antecedent is unsatisfiable because `Unknown ∉ E` — so it constrained
    nothing. The same *shape* stated over the refinement preorder is satisfiable and constrains a
    quarter of the lattice, which is the difference between a well-formedness condition and a sentence.

    WHY IT MATTERS OPERATIONALLY: without it an engine differential reports 100 disagreements on
    `deny Net` over `{Llm}`-without-`Net`, every one on a signature the engine cannot emit — the model
    firing correctly on a point that does not exist. Measured on candor-swift: 100 of 1280 rows, and
    ZERO once restricted here.
    """
    return all(base in sig.S for refined, base in CO_EMIT.items() if refined in sig.S)


def reachable_lattice():
    """`full_lattice()` minus the signatures co-emission forbids — the domain a DIFFERENTIAL may use."""
    return [x for x in full_lattice() if is_reachable(x)]


def monotonicity_counterexample():
    """THE 2026-07-27 DEFECT, as a property failure rather than a gate exit code.

    NOT an implementation defect, which is how it was first filed and how the first version of this
    docstring described it. The absence-keyed rule was IN THE SPECIFICATION (§6.2, "a function whose
    `Unknown` carries no recorded reason is TREATED AS `unresolved`"), with the sound intention that a
    narrowed filter never silently tolerates a hole it could not classify. Every engine was conforming.
    The divergence was between the MODEL and the CONTRACT — which is why four independent
    implementations agreeing with each other could never have surfaced it, and why this file exists.

    The measured symptom was that adding a call to a function took `deny Unknown[unresolved]` from
    exit 1 to exit 0: a signature that is strictly WORSE-KNOWN passed where a better-known one failed.
    """
    bad = lambda sig: phi("Net", sig) or psi_with_absence_default({"unresolved"}, sig)
    pts = _lattice(("Fs",), ("dispatch", "unresolved"))
    return check_upward_closed(bad, pts)


def repair_reproduces_the_counterexample_correctly():
    """THE OTHER HALF: on the three signatures that broke, the repair gives the RIGHT verdicts.

    Showing the old rule broken does not show the new one sound, and the full-lattice check alone is
    not enough either — plain ψ is ALREADY proven upward-closed by `selftest`, so re-running it on the
    repair would be a tautology dressed as evidence. What actually needs checking is that the repair
    assigns the right verdict to the three concrete rows, INCLUDING the one that used to pass.

    Rows, all under `deny Unknown[unresolved]`. `Sig(S, D)` — `Unknown` is carried by `D`, never by `S`.
      1. one reasonless dep          -> D = {}          + reasonless -> {unresolved}          -> REJECT
      2. one correctly-reasoned dep  -> D = {dispatch}              -> {dispatch}             -> pass
      3. BOTH (strictly worse-known) -> D = {dispatch}  + reasonless -> {dispatch,unresolved} -> REJECT

    Row 3 is the defect: strictly worse-known than row 1, and it PASSED. Rows 2 and 3 have the SAME `D`,
    which is why the `reasonless` bit cannot be inferred from it and why no rewriting of the old rule
    could have separated them. Row 1 is the ill-formed one: without the contribution its signature is
    `(∅, ∅)`, which Def 6 reads as sound-complete — the model's way of saying the function has no
    `Unknown` at all, about a function whose report says it does.
    """
    v = deny_unknown("Net", {"unresolved"})
    rows = [("reasonless only",        Sig((), ()),           True,  True),
            ("reasoned only",          Sig((), ("dispatch",)), False, False),
            ("both (worse-known)",     Sig((), ("dispatch",)), True,  True)]
    out = []
    for name, sig, reasonless, want_reject in rows:
        got = v(contribute_unresolved(sig, reasonless))
        out.append((name, got, want_reject))
    return out


def repair_is_upward_closed():
    """And the repair is upward-closed over the FULL lattice — every point of L, not the slice.

    This holds for free (the repair only ever ENLARGES `D`, and `deny_unknown` is monotone in `D`), so
    it is a regression guard rather than the load-bearing check. It would catch a future repair that
    tried to *remove* a class from `D` under some condition.
    """
    return check_upward_closed(deny_unknown("Net", {"unresolved"}), full_lattice())


def selftest() -> int:
    pts = full_lattice()
    verbs = {
        "deny Net": deny("Net"),
        "deny Net Unknown": deny_unknown("Net"),
        "deny Net Unknown[dispatch]": deny_unknown("Net", {"dispatch"}),
        "deny Fs Unknown[reflect,unresolved]": deny_unknown("Fs", {"reflect", "unresolved"}),
        "pure": pure(),
        "unknown-ratchet(∅)": unknown_ratchet(()),
        "unknown-ratchet({dispatch})": unknown_ratchet({"dispatch"}),
    }
    rc = 0
    print(f"Lemma 2 over the FULL lattice: {len(pts)} signatures, "
          f"{sum(1 for x in pts for _ in covers(x))} cover-steps each verb:")
    for name, v in verbs.items():
        ce = check_upward_closed(v, pts)
        print(f"  {'OK  ' if not ce else 'FAIL'}  {name}" + (f"   {ce[0][0]} ⊑ {ce[0][1]}" if ce else ""))
        rc |= 1 if ce else 0

    # Definition 4's worked example, which pins the refinement preorder rather than assuming it.
    # Definition 4's worked example, AMENDED 2026-07-27 with Definition 2. It used to read
    # `deny Net` must fire on {Db}` — the assertion that produced 100 model-vs-engine disagreements over
    # 1792 rows, every one that family. `Db` is not a refinement of `Net` (an embedded store has no egress);
    # `Llm` is (a provider call is an outbound request in every instance).
    assert deny("Net")(Sig({"Llm"})), "Definition 4: `deny Net` must fire on a determined {Llm}"
    assert not deny("Net")(Sig({"Db"})), \
        "Definition 2 (amended): `Db` does NOT refine `Net` — an embedded store has no egress"
    assert not deny("Db")(Sig({"Net"})), "refinement is directional: `deny Db` must NOT fire on {Net}"
    assert deny("Db")(Sig({"Db"})), "and plain membership still fires"
    # Definition 30's second sentence, which is the one implementations get wrong.
    assert not deny("Net")(Sig((), {"dispatch"})), \
        "Definition 30: a non-empty D must NOT fire a bare `deny e`"
    assert deny_unknown("Net")(Sig((), {"dispatch"})), \
        "Definition 31: bare `deny e Unknown` is C = R, so any reason fires it"
    print("  OK    Definitions 2, 4, 30, 31 worked examples (incl. `Db` NOT refining `Net`)")

    ce = monotonicity_counterexample()
    if not ce:
        print("  FAIL  the absence-default rule is upward-closed?! — this check has stopped working")
        rc |= 1
    else:
        x, y = ce[0]
        print(f"  OK    the absence-default rule is NOT upward-closed: Reject{x} but not Reject{y}")
        print("        ^ the 2026-07-27 SPEC defect (§6.2, not the engines — they were conforming),")
        print("          as a lattice property rather than an exit code")
    # The refinement clause and the contract's plain membership must AGREE over reachable signatures.
    # Where they disagree, the disagreement must be confined to unreachable ones — otherwise the contract
    # and the model differ on something an engine can actually produce, which is a real finding.
    reach = reachable_lattice()
    refine_v, member_v = deny("Net"), (lambda sg: "Net" in sg.S)
    split = [x for x in reach if refine_v(x) != member_v(x)]
    if split:
        print(f"  FAIL  refinement vs membership disagree on {len(split)} REACHABLE signatures, e.g. {split[0]}")
        rc = 1
    else:
        print(f"  OK    refinement ≡ plain membership over all {len(reach)} REACHABLE signatures")
        print(f"        ^ they differ on {len(full_lattice()) - len(reach)} UNREACHABLE ones (`Llm` without")
        print("          `Net`); a differential that does not exclude those reports 100 phantom failures")
    if [x for x in full_lattice() if not is_reachable(x) and refine_v(x) == member_v(x)]:
        pass  # unreachable points may agree or not; only the reachable ones are load-bearing

    rows = repair_reproduces_the_counterexample_correctly()
    bad = [(n, g, w) for n, g, w in rows if g != w]
    for n, g, w in rows:
        print(f"  {'OK  ' if g == w else 'FAIL'}  ⟨0.24⟩ repair, {n:22} -> "
              f"{'REJECT' if g else 'pass'} (want {'REJECT' if w else 'pass'})")
    if bad:
        rc = 1
    else:
        print("        ^ row 3 is the defect: same D as row 2, strictly worse-known than row 1, and it")
        print("          USED TO PASS. The `reasonless` bit cannot be inferred from D — rows 2 and 3")
        print("          share D={dispatch} — which is why no rewriting of the old rule could fix it.")
        print("          Deeper: without the contribution, row 1 is (∅,∅), which Def 6 reads as")
        print("          SOUND-COMPLETE. A reasonless Unknown is not representable in this model at")
        print("          all, so the old rule was answering an ill-formed question. ⟨0.24⟩ is the")
        print("          producer-side repair that makes the state unreachable and (W) hold.")
    if repair_is_upward_closed():
        print("  FAIL  the repair broke upward-closure"); rc = 1
    else:
        print("  OK    plain ψ over the enlarged D is upward-closed (regression guard, holds for free)")
    return rc


if __name__ == "__main__":
    raise SystemExit(selftest())
