# `reference/` — the formal model, executable

`policy_model.py` is PAPER3 (the formal reference, cited as `candormodel`) Definitions 4–7 and 30–36
plus Lemma 2, as code. It exists because those definitions are the one part of the system the paper
claims as **proved**, and nothing connected them to the engines: the model lived in prose, the engines
in four languages, and the only thing between them was a differential suite comparing engines **to each
other**.

That gap has a measured cost. On 2026-07-27 an engine took `deny Unknown[unresolved]` from a REJECT to a
PASS when a call was **added** — a counterexample to Lemma 2's corollary. The lemma was fine; the engine
had reached a signature the model does not admit and coped with a rule that is nowhere in the model.

## What it verifies today, and how completely

`python3 reference/policy_model.py` checks **Lemma 2 over the entire lattice** for the real vocabulary —
2¹¹ × 2⁶ = 131 072 signatures — in a few seconds.

It is complete, not a sample, because upward-closure is checked against **covers** (immediate
successors) rather than all ordered pairs. If `Reject` survives every single-element step it survives
every chain, by induction on step count, and in a finite Boolean lattice every `x ⊑ y` is such a chain.
That turns a quadratic check (≈10⁹ pairs, which is why the first version could only afford a toy
sublattice) into a linear one.

**So for finite `E` and `R` this discharges the finite case outright.** A mechanised proof (Lean,
Isabelle) would add generality over *arbitrary* `E` and `R` and machine-checked rigour — worth having,
and it would have forced the well-formedness condition into the open — but it is not needed to decide
the finite instance the engines actually implement.

It also encodes the defect: `monotonicity_counterexample()` implements the engines' absence-keyed rule
("if the class set is empty, default it to `unresolved`") and shows it is **not** upward-closed.

## What it does NOT verify, and the blocker for the other half

Nothing here touches the **analysis** — no effects are computed and no report is read. That stays
empirical, and the runtime oracle is its instrument. This is `Reject` alone: small, pure, total, finite.

The natural next step is a differential — *does each engine's gate agree with the model on a given
`(S, D)`?* — and this file recorded it as **blocked**, because no engine exposed a way to gate a GIVEN
signature: the gate was reachable only through `scan --policy` (which recomputes `S` from source, so the
classifier is back in the loop) and `whatif` (which reports only what a hypothetical *introduces*, so a
pre-existing violation reads green).

**UNBLOCKED, 2026-07-27.** SPEC §3.1 ⟨0.24⟩ specifies `gate --report <locator> --policy <file>` and
candor-java has shipped it. The first differential ran 1792 rows (256 signatures × 7 verbs).

**And it immediately found the failure mode this file is most exposed to: the THEORY being wrong.** Two of
its four disagreeing verbs were the model's fault, not the engine's.

- `pure` disagreed on 15 of 256 signatures — every one `S = ∅, D ≠ ∅`. PAPER3's Definition 32 rejected any
  disclosure; the contract, the conformance suite and all four engines pass it. **0 of 256 after the
  definition was amended.**
- `deny Net` disagreed on 100 rows, all one family: a signature containing `Db`. Definition 2 carried
  `Db ⊑ₑ Net` on the strength of one sentence in SPEC §1 ("`Llm` refines `Net` the way `Db` does"). It does
  not — an embedded store has no egress — and correcting the preorder took 100 to 0 **without touching an
  engine**.

That is the standing hazard for anything built on this file, and it is worth stating plainly: **a theory
that is wrong in the STRICT direction produces a review finding shaped exactly like a real defect in the
code.** Nothing goes red, no monotonicity breaks, and the differential reports conforming engines as
violating. Before treating any disagreement as an engine defect, check which side the contract and the
conformance suite are on.

**Do not add rows for `forbid`, `allow`, `deny E[dest…]` or the `unknown-ratchet`.** A review established
that Definitions 33–35 describe verbs the deployment does not have (`forbid` is a call-graph rule with no
effect predicate; `allow` is a fail-closed literal-surface certification; the shipped ratchet grandfathers
a function already disclosed at baseline, so Definition 35 rejects where every engine passes). Proposition 5
has been rescoped to the `L`-carried verbs. Those rows would manufacture divergences out of the theory
rather than find them in the code.

Two obligations the differential itself carries, both learned the same day: keep the model's `E` in step
with SPEC §1's vocabulary (it was missing `Ipc` and `Clipboard`, which would have crashed on the first
report carrying either — conformance PART 23 now checks this), and derive the lattice-size floor rather
than hardcoding it.

The alternative route stays available and needs no engine: **inject via the chain** — a synthetic
*dependency* report carrying the chosen `(S, D)` and a consumer that calls it, so the signature is
inherited rather than computed. It is how the 2026-07-27 collision defects were measured, but it exercises
the join as well as the gate, so a divergence needs a second step to localise.
