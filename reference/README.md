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
2⁹ × 2⁶ = 32 768 signatures — in about two seconds.

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
`(S, D)`?* — and it is **blocked on a testability gap worth recording:**

> **No engine exposes a way to gate a GIVEN signature.** The gate is reachable only through
> `scan --policy` (which computes `S` from source, so the classifier is back in the loop and the test
> is no longer about the gate) and through `whatif` (which reports only violations the hypothetical
> *introduces*, so a pre-existing violation reads green). There is no `candor-query gate <report>
> <policy>`.

That gap is plausibly *why* the model and the engines could drift this far: the gate is only ever
exercised end-to-end, so no test could isolate it. Two ways forward, neither yet taken:

1. **Add a gate-a-report verb** to each engine. Smallest, and it makes the gate independently testable
   for the first time — but it is a CLI surface change in four engines.
2. **Inject via the chain**: a synthetic *dependency* report carrying the chosen `(S, D)` and a
   consumer that calls it, so the signature is inherited rather than computed. Needs no engine change
   and works today — it is how the 2026-07-27 collision defects were measured — but it exercises the
   join as well as the gate, so a divergence needs a second step to localise.

Until one of those lands, this file verifies the **spec-implements-theory** direction only. The
**code-implements-spec** direction remains what it has always been: the differential conformance suite,
which compares engines to each other.
