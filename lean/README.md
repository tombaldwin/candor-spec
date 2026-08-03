# The formal model, machine-checked

A Lean 4 transcription of PAPER3's disclosure lattice and policy layer. **Scope is deliberately small and
stated here rather than implied**, because an artifact that looks complete and is not would be the same
defect this exists to remove.

## What it covers today

| PAPER3 | here | status |
|---|---|---|
| Def 1 (capability effects) | `Effect` | transcribed |
| Def 2 (refinement preorder, **amended**) | `Refines` | transcribed + the amendment **proved** |
| Def 3 (covering; observation side) | `covered` | transcribed |
| Def 4 (firing; gate side) | `fires` | transcribed |
| Def 5 (disclosure reasons) | `Reason` | transcribed |
| Def 6 (effect signature) | `Sig` | transcribed |
| Def 7 (product order) | `Sig.le` | transcribed |
| Remark 1(i) (`Unknown` is not `⊤`) | two incomparability theorems | **proved** |
| Def 30 (`deny e`) | `rejectDeny` | transcribed |
| Def 31 (`deny e Unknown[C]`) | `rejectDenyUnknown` | transcribed |
| Def 32 (`pure`, **amended**) | `rejectPure` | transcribed + the amendment **proved** |
| **Lemma 2 (monotone denial)** | `lemma2_deny/_denyUnknown/_pure` | **proved, for all three shipped verbs** |
| Lemma 2's corollary | `lemma2_corollary_deny` | **proved** |
| — (executable twins of Defs 4, 30–32) | `Exec.lean` `refinesB`/`firesB`/`reject*B` | transcribed + **bridged to the `Prop` model by proof** |

**Not covered**, and not excused: §2's signatures and transitive rule, §3's honesty invariant, §4's
Theorem 1 and its A0–A3 antecedents, §5 blame, §8 escapes. Proposition 1's Boolean-lattice structure is
transcribed only as far as the order — the paper itself notes "only monotonicity and completeness are used
below; the Boolean structure is free", and monotonicity is what Lemma 2 needs.

## Why it is here

The theory↔spec↔code chain has machinery in two places and none in the third:

- `conformance/clause_check.py` — a property must quote a real **spec** clause;
- `conformance/` PART 23 — the engines are run against `reference/policy_model.py`;
- **nothing** relates the spec text to the **paper** text.

And `policy_model.py` is itself a hand transcription — an unverified, trusted artifact. Both documents
have been wrong in ways only a differential caught:

- Def 2 originally read `Db ⊑ₑ Net`, making `deny Net` fire on a determined `{Db}` — **100 disagreements
  over 1792 rows**, model REJECT, engine pass. `no_fires_net_of_db` now proves the corrected preorder has
  the property the amendment claims.
- Def 32 originally read `Reject ⇔ (S,D) ≠ (∅,∅)`, reporting all four **conforming** implementations as
  violating the theory on `(∅,{r})`. `pure_passes_bare_unknown` now proves the corrected verb passes it.

Neither was found by a proof. Both were found by running the model against real engines and being
surprised. This artifact does not replace that — it removes the *transcription* from the trusted base.

## The differential, and why the Bool twins exist

A second transcription is only worth having if the two are **checked against each other**; otherwise there
are simply two unverified files instead of one. So `Exec.lean` gives every definition a computable `Bool`
twin and **proves the twin agrees with the `Prop` one** (`refinesB_iff`, `firesB_iff`, `rejectDenyB_iff`,
`rejectPureB_iff`). That is what makes the emitted table the *proved* answer rather than a third guess: an
executable that disagreed with the model would fail to compile.

`lake exe emit` then walks the vocabulary and prints a verdict per row, and
`reference/differential_lean_vs_python.py` recomputes every one with `policy_model.py`:

```
rows compared : 147400     deny 16214 · deny_unknown 129712 · pure 1474
vocabulary    : 11 effects, 6 reasons        DIFFERENTIAL: OK
```

The `C` axis of `deny e Unknown[C]` is enumerated rather than fixed at `R`, because a differential that
only ever passed the full reason set would agree with a `ψ` that ignored its argument entirely — and
reason-scoping is the ⟨0.19⟩ rung.

**Verified to catch**, not asserted to: the differential was run against four planted faults in the Python
and failed on each — `Db ⊑ₑ Net` reinstated (1269 disagreements), `pure` reverted to the erroneous Def 32
reading (21), `ψ` ignoring its scope (67266), and `ψ_with_absence_default`, the old absence-keyed rule
(1212). A fifth attempt produced OK because the injecting regex did not match the real signature: *the
fault never fired*. That outcome is a broken probe, not a passing property, and the distinction is the
whole point of `conformance/probe_check.py` one level down.

## What the axiom check asserts, in two tiers

`check.sh` does not simply forbid axioms, because the two groups earn different bars and one bar would
weaken the strong one:

- **Tier A** — the headline theorems in `Lattice.lean`. Pure `Prop`, proved by case analysis, depending on
  **no axioms at all**, not even `propext`. A new axiom here means the argument changed shape.
- **Tier B** — the bridge lemmas. They state `Bool = true ↔ Prop`, so `simp` and the `List` lemmas pull in
  `propext` and `Quot.sound`: Lean's own core axioms, present in almost every non-trivial proof and not
  evidence of anything. Forbidden here are `sorryAx` (proves nothing) and `Classical.choice` (these
  arguments are constructive).

Both tiers were probed: promoting a `propext`-dependent lemma into tier A fails tier A, and a
`Classical.em` theorem in tier B fails tier B.

## Design notes

**Mathlib-free on purpose.** Lemma 2 needs monotonicity and nothing else, so sets are predicates
(`Effect → Prop`) and `⊆` is pointwise implication. The build has no dependencies, takes seconds, and is
auditable by someone who does not know Mathlib.

**`fires` and `covered` sit side by side deliberately.** Def 3's scope note is the subtlety most likely to
be transcribed wrongly: the *same* preorder is read in opposite directions — down-closure of `S` for
covering, down-closure of `{e}` for firing — and the paper warns that reading containment modulo `⊑ₑ`
everywhere makes Proposition 1's lattice structure and Lemma 2's upward-closure **fail** (Proposition 6 is
a proof of that failure). Every containment here is plain subset except `covered`.

**The amendment is checkable because `Refines` is inductive.** `Db ⊑ₑ Net` is not merely absent from the
definition — it is underivable, and `cases` discharges it.

## Running it

```sh
cd lean && lake build          # builds and checks every proof
lake exe emit                  # the decision table, one row per (verb, arg, C, S, D)
bash check.sh                  # + no `sorry`, the two axiom tiers, and the 147k-row differential
```

`check.sh` is the one to run in review: a proof that silently depends on `sorryAx` type-checks and proves
nothing, which is the Lean-shaped version of a property that cannot fail.
