"""The POLICY LAYER of candor's formal model, executable.

This is a transcription of PAPER3 (the formal reference, cited as `candormodel`) Definitions 4-7 and
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
# `Db ⊑ₑ Net` and `Llm ⊑ₑ Net` are the spec's documented refinements (SPEC §1: "Llm refines Net the
# way Db does"). PAPER3 Definition 4 uses exactly this: "`deny Net` fires on a determined `{Db}`".
# `Unknown` is NOT an effect in the model — it is the NAME of the `D ≠ ∅` posture (Definition 6), and
# treating it as a member of `E` is one of the ways an implementation drifts out of the model.
E = ("Clock", "Db", "Env", "Exec", "Fs", "Llm", "Log", "Net", "Rand")
_REFINES = {("Db", "Net"), ("Llm", "Net")}


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


def pure():
    """Definition 32 (`pure`). Any determined effect OR any disclosure fails it."""
    return lambda sig: sig != Sig()


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


def check_upward_closed(reject, points) -> list:
    """Lemma 2: `Reject(x) ∧ x ⊑ y ⇒ Reject(y)`. Returns the counterexamples, exhaustively."""
    return [(x, y) for x in points if reject(x)
            for y in points if x.leq(y) and not reject(y)]


def monotonicity_counterexample():
    """THE 2026-07-27 DEFECT, as a property failure rather than a gate exit code.

    The engines' rule was: if the reason-class set is EMPTY, default it to `unresolved`. Written as a
    predicate that is what `psi_with_absence_default` below does — and it is not upward-closed,
    because acquiring a reason REMOVES the default. The measured symptom was that adding a call to a
    function took `deny Unknown[unresolved]` from exit 1 to exit 0.
    """
    def psi_with_absence_default(C, sig):
        if not sig.D:                      # the rule that is not in the model
            return "unresolved" in C
        return bool(sig.D & frozenset(C))

    bad = lambda sig: phi("Net", sig) or psi_with_absence_default({"unresolved"}, sig)
    pts = _lattice(("Fs",), ("dispatch", "unresolved"))
    return check_upward_closed(bad, pts)


def selftest() -> int:
    pts = _lattice(("Db", "Fs", "Net"), ("dispatch", "reflect", "unresolved"))
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
    print(f"Lemma 2 over {len(pts)} signatures ({len(pts)**2} ordered pairs each):")
    for name, v in verbs.items():
        ce = check_upward_closed(v, pts)
        print(f"  {'OK  ' if not ce else 'FAIL'}  {name}" + (f"   {ce[0][0]} ⊑ {ce[0][1]}" if ce else ""))
        rc |= 1 if ce else 0

    # Definition 4's worked example, which pins the refinement preorder rather than assuming it.
    assert deny("Net")(Sig({"Db"})), "Definition 4: `deny Net` must fire on a determined {Db}"
    assert not deny("Db")(Sig({"Net"})), "refinement is directional: `deny Db` must NOT fire on {Net}"
    # Definition 30's second sentence, which is the one implementations get wrong.
    assert not deny("Net")(Sig((), {"dispatch"})), \
        "Definition 30: a non-empty D must NOT fire a bare `deny e`"
    assert deny_unknown("Net")(Sig((), {"dispatch"})), \
        "Definition 31: bare `deny e Unknown` is C = R, so any reason fires it"
    print("  OK    Definitions 4, 30, 31 worked examples")

    ce = monotonicity_counterexample()
    if not ce:
        print("  FAIL  the absence-default rule is upward-closed?! — this check has stopped working")
        rc |= 1
    else:
        x, y = ce[0]
        print(f"  OK    the absence-default rule is NOT upward-closed: Reject{x} but not Reject{y}")
        print("        ^ the 2026-07-27 engine defect, as a lattice property rather than an exit code")
    return rc


if __name__ == "__main__":
    raise SystemExit(selftest())
