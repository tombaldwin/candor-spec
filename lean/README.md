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
| **Lemma 2 (monotone denial)** | `lemma2_deny/_denyUnknown/_pure` | **proved generically, then instantiated** |
| Lemma 2's corollary | `lemma2_corollary_deny` | **proved** |
| — (Lemma 2 over an arbitrary vocabulary) | `Generic.lean` `gLemma2_*` | **proved**; `Lattice`'s three are instantiations |
| — (executable twins of Defs 4, 30–32) | `Exec.lean` `refinesB`/`firesB`/`reject*B` | transcribed + **bridged to the `Prop` model by proof** |
| — (the enumerations are exhaustive) | `Effect.all_complete`, `Reason.all_complete` | **proved** |
| SPEC §4.0's `deny e` table ≡ Def 4 | `fires_iff_mem_of_reachable` | **proved**, over any co-emission map |
| §4.0 transitive set = least fixpoint | `Chain.T_fixpoint_le/_ge`, `Chain.T_least` | **proved** |
| — (chaining is idempotent; `T` is graph-monotone) | `Chain.T_rechain_le/_ge`, `Chain.T_mono` | **proved** |
| §2.2 rule 1 ⟨0.25⟩ (ambiguous key is unioned) | `Chain.drop_only_loosens` + `Chain.Witness.*` | **proved**, with a counterexample to ⟨0.24⟩ |
| Lemma 1 (callee ⊑ caller) | `Chain.T_callee_le` | **proved** |
| **Theorem 1 (conditional transitive soundness)** | `Soundness.thm1_i`, `thm1_ii` | **proved from (A2), (A3)** |
| Def 24 (A0) — "true but hollow" without it | `Soundness.A0Witness.*` | **proved** |
| — ((A3) is load-bearing; the theorem is not vacuous) | `Soundness.Control.*` | **proved** |
| **Def 21 (honesty invariant H), Def 22 (violation)** | `Honesty.H`, `Honesty.Violation` | transcribed |
| H⁺ ⇒ H; (A2)+(A3) ⇒ H | `Honesty.H_of_Hplus`, `H_of_A2_A3` | **proved** |
| Remarks 4(i), 5; Defs 16, 21's analyzed restriction | `Honesty.Boundaries.*` | **four witnesses** |
| Prop 6 (containment modulo `⊑ₑ` breaks Lemma 2) | `Counterexample.lemma2_fails_under_leModulo` | **counterexample** |
| §4.0 (the flat carrier is only a preorder) | `Counterexample.flat_not_antisymm` + `sig_le_antisymm` | **counterexample** |
| **Cor 1 (blame), Cases 1 and 2** | `Blame.violation_refutes_A2_at`, `Blame.locate_A3_failure` | **proved**, edge returned |
| Def 17–18 (coverage classes, charging) | `Frames.Class`, `Frames.chargeTo` | transcribed |
| **Prop 4 (direct charging is functional)** | `Frames.chargeTo_spec`, `Frames.nearest_unique` | **proved** |
| Def 19a (covered-reached = closure of the collapse) | `Frames.decomposes_of_allCovered` + converse | **proved** |
| **§8 Escapes 1–4** | `Escapes.escape1…escape4` | **four witnesses** |
| Prop 6 (as PAPER3 states it) | `Escapes.prop6_llm`, `prop6_db_witness_is_dead` | **proved + a defect found** |
| — (the reachability hypothesis is load-bearing) | `fires_ne_mem_off_reachable`, `llm_without_net_unreachable` | **proved** |

## Theorem 1, and the antecedent that carries it

The algebra of Theorem 1 is elementary, and the paper says so: *"Granted (A2)–(A3) the inequality is
elementary; the content of Theorem 1 is the **decomposition** into individually checkable and individually
attackable hypotheses."* The record agrees — every cardinal sin this family has fixed was an (A0)–(A3)
violation, and none was an error in the inequality. So mechanising it buys confidence in the *decomposition*,
not in the proof: the guarantee becomes unstatable without its antecedents, and the usual misuse (quoting
the conclusion where (A0) does not hold) stops typechecking.

**The (A0) witness is the point.** PAPER3's proof says in prose: *"Without it the theorem is true but
hollow… (i)–(ii) hold over a scope the engine itself chose by omission."*
`thm1_holds_but_is_hollow_without_A0` is that sentence as an object — a run where (A2) and (A3) hold,
`D(f) = ∅`, Theorem 1's conclusion holds in full, and a `Net` occurs inside `f`'s dynamic extent while `f`'s
signature is empty. Nothing is violated. **That is the cardinal sin, licensed by a true theorem** — which is
why (A0) is a precondition on the analyzed set, and why discharging it needs a completeness manifest at
*function* granularity rather than `{count, digest}`.

Because that witness satisfies the hypotheses with an *empty* call tree, two controls sit beside it:
`thm1_is_not_vacuous` (a live edge, a live observation, and a conclusion with content) and
`A3_is_load_bearing` (the same run against an engine that missed the edge and disclosed nothing — (A3)
false, `D` still empty, effect not in the set). A conditional whose hypotheses are only ever satisfied
trivially is not a guarantee.

**(A1) is absent on purpose**, and its absence is checkable by reading the hypotheses: Remark 7 states it
does not enter the proof. Its job is to make `D = ∅` honestly *achievable*.

## The honesty invariant, and the four things it is not

H is the cardinal sin as a property: *for every executed analyzed `f`, if `D = ∅` then `obs(f) ⊆ S`.* One
line — and almost everything that matters about it is a boundary. `Hplus_of_A2_A3` closes the loop from §4
back to §3: the antecedents are individually checkable, and between them they buy the property the family
actually sells.

The four boundaries are mechanised as objects rather than left as remarks, because each reads like a caveat
and functions as a design constraint:

- **H alone is worthless** (Remark 4(i)). An analyzer answering `(∅, {r})` everywhere satisfies it
  trivially. `H_is_trivial_under_total_disclosure` exhibits exactly that — every frame issuing `Net`, H
  green. So the object of interest is H *jointly* with the determined axis: the `D = ∅` fraction of a run
  and the precision of `S` there. Same shape as the (A0) hollowness witness.
- **The analyzed restriction is not cosmetic.** Unrestricted, H asserts `obs(f) ⊆ ∅` of a library primitive
  that genuinely issues an effect — false for every program that calls a library.
- **The per-reason-class residual is real** (Remark 5). A frame disclosing only a benign reason while hiding
  an undisclosed `dispatch` site that reaches `Net` passes H *and* passes `deny Net Unknown[dispatch]`. Two
  gates green over an undisclosed `Net`; the model does not close this.
- **Fabrication is outside H** (Def 16). A report charging every function with every effect over a run that
  does nothing satisfies H perfectly. Not an oversight — by Lemma 2 a fabrication is a false-*alarm* hazard,
  a different failure needing a different instrument (the A/B against real code, not this).

**The one modelling assumption here has since been discharged.** Def 19a's covered-reached relation
(analyzed *or* modelled frames between) is not Def 27's single-hop collapse (modelled only), and the paper
warns that substituting one for the other "would reduce Theorem 1(ii) to depth one and make transitive
soundness non-transitive". `ExecReaches` is the reflexive *transitive* closure of the collapsed edge, and
that this recovers covered-reached rested on a decomposition argument about stacks the model did not
contain. `Frames.decomposes_of_allCovered` is now that argument, with its converse: a segment with no
uncovered frame splits into modelled-only runs separated by analyzed frames, and nothing else. What remains
is a definition rather than an assumption — by Def 16b an executed call pushes the callee directly onto a
frame of the caller, so stack adjacency *is* the call relation.

**`no_violation_of_H` is stated one way only.** The converse needs excluded middle and would be the single
theorem here depending on `Classical.choice`, while carrying nothing: a violation is *defined* as a witness
to H's failure, so the converse is unfolding.

## Blame — a violation names a site

Corollary 1 is Theorem 1's contrapositive with an address. `violation_refutes_A2_at` locates Case 1 at the
frame; `locate_A3_failure` is Case 2's least-index walk as an induction that **returns the offending edge**,
carrying the `D = ∅` that makes it undisclosed. The induction *is* the paper's minimality argument — it
visits the chain in order, so minimality is not a side condition it could forget.

One hypothesis the paper does not need and this does: the call graph must be **decidable**. Locating an edge
means deciding `(f_k, f_{k+1}) ∈ call` at each step, which is free classically and not constructively. It is
honest rather than limiting — `call` is a finite computed artifact a consumer literally decides membership
in — and taking it as a hypothesis keeps the file free of `Classical.choice`.

`transitive_failure_with_A2_intact_locates_A3` is stated on `charged(f) ⊄ S(f)`, **not** `obs(f) ⊄ S(f)`.
My first version used the latter, which is vacuous: by Case 1 a violation at `f` already refutes (A2), so
"(A2) intact *and* a violation at `f`" is a contradictory hypothesis and the theorem would have proved
anything. Case 2's whole point is the run where every frame's own account is correct and the transitive sum
still escapes.

## §8's escapes, and two defects they turned up

The four escapes are the moves the signature order cannot see — H-sound changes that no oracle run catches
and only a ratchet can. Each is mechanised as incomparability + a gate relaxing + which channel (if any)
still fires. Transcribing them surfaced two problems, both the same root cause: **Definition 2's amendment
(`Db ⋢ₑ Net`) did not propagate into §8.**

- **Proposition 6's proof is dead as written.** It reads "Under that order `({Db},∅) ≤ ({Net},∅)`, since
  every element of `{Db}` refines an element of `{Net}`" — false under the amended Definition 2, which says
  `Db ⋢ₑ Net` in as many words. `prop6_llm` proves the proposition survives on the surviving refinement
  pair; `prop6_db_witness_is_dead` proves the witness in its proof does not.
- **Escape 2 has no realizable instance in the shipped vocabulary**, and it takes both halves to see why.
  With `Db` the move is no longer H-sound — an observed `Db` is not covered by a declared `Net`, so H
  catches it and it is not an escape. With `Llm`, the only surviving refinement, engines *co-emit* `Llm` and
  `Net`, so any reachable signature determining `Llm` determines `Net` too and declassifying to bare
  `{Net}` is a plain `⊑`-**decrease** — comparable, and a baseline ratchet reads the loss.

  Note what closed it: **reachability**. The same co-emission constraint that reconciles SPEC §4.0's table
  with Def 4 removes this escape's instance. The escape's *structure* remains live on the destination-class
  axis (⟨0.20⟩) — a class is not a member of `E`, so H cannot see a class coarsening by construction — and
  that axis is outside this model and not claimed here.

## Two counterexamples — the mistakes a careful reader makes

Everything else here proves the model is right; `Counterexamples.lean` proves two nearby models are wrong,
which for a specification is the more useful statement. Both are reached by reasoning that feels like
tidying up.

- **Reading containment modulo `⊑ₑ` everywhere.** Def 3 restricts the preorder to the observation side and
  the instinct is to make the order uniform. `lemma2_fails_under_leModulo`: `{Llm}` sits below `{Net}` under
  the uniform reading, `deny Llm` fires on the first and not the second — Lemma 2 gone, and with it the
  guarantee that a better analysis never turns a red gate green. Under the plain order the two are simply
  incomparable, so the counterexample is *manufactured by the tidying*.
- **The flat carrier.** `flat_not_antisymm`: `{Net, Unknown}` and `{Unknown}` sit below each other and are
  not equal, so the order §4.0 warns about is a preorder, never partial. `sig_le_antisymm` shows the pair
  carrier is antisymmetric, and `flat_confusion_is_observable` shows the two confused points are separated
  by a shipped gate — so the pair is the carrier, not a presentational choice.

## The transitive rule, and ⟨0.25⟩ as a proof

`Chain.lean` is the first part of this development that reaches the **report** layer rather than the gate
algebra — which matters because the last three rungs all lived there (⟨0.24⟩ CONTRIBUTES, ⟨0.25⟩ the join
key, ⟨0.26⟩ the sidecar manifest) and none of them is a statement about `Reject`.

SPEC §4.0 asserts the transitive effect set is *"the least fixpoint of the monotone componentwise join over
this finite lattice (Knaster–Tarski)"*. Nothing proved it. `T_fixpoint_le`/`_ge` and `T_least` now do — and
`T_least` is the half that makes "least" mean something, since without it the top signature satisfies the
fixpoint equation too and an engine could discharge the rule by charging every function with every effect.

**⟨0.25⟩'s correction is now a theorem.** §2.2 rule 1 admits three responses to an ambiguous join key:

| | | sound against fabrication | sound against silence |
|---|---|---|---|
| **union** | resolve to every colliding entry | ✔ | ✔ |
| **pick** | resolve to one | ✘ | ✔ |
| **drop** | resolve to nothing — ⟨0.24⟩'s rule | ✔ | **✘** |

`drop_only_loosens` proves the general statement, for *every* verb at once: composing `drop_le_union` with
Lemma 2, a violation found under the drop rule is still one under the union — dropping never invents a
violation, it only loses them. `Witness.deny_passes_under_drop_fires_under_union` then exhibits a two-node
graph where the loss is real: one graph, one gate, two verdicts, decided entirely by which text the
implementation follows. Under ⟨0.21⟩ the caller is not merely missing from the report, it is *claimed pure*.

That is why the drop rule survived two rungs looking conservative — it fails in the silence direction only,
and every fabrication check passes.

**What these theorems do not do.** Conformance PARTs 25 and 26 check the four **engines** are idempotent
and monotone. These check the **rule** is. An engine can implement a sound rule incorrectly, and a correct
engine can implement an unsound rule faithfully — different failures, different fixes, and neither
instrument sees the other's. Before `Chain.lean` the second kind had no instrument at all, which is how
⟨0.24⟩'s drop rule reached four conforming implementations.

**Not covered**, and not excused: Definition 16b's *labelled transition system* itself (call/ret/spawn/
issue/exit steps and the per-thread state map). `Frames.lean` models the enclosing chain — the structure
Definitions 18–20 and Proposition 4 actually consume — but not the step relation that produces it, so the
cross-thread boundary of Definition 19 and Remark 6's thread-pool limit are outside this development.
Definition 28's (A4) report fidelity is also absent by design: it is a serialization property checked by a
different instrument. Proposition 1's Boolean-lattice structure is
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

## Lemma 2 is proved without the vocabulary

`Generic.lean` proves monotone denial over an **arbitrary** effect type, an **arbitrary** reason type, and
an **arbitrary relation** — not an arbitrary preorder. Nothing in the proof uses reflexivity or
transitivity of `⊑ₑ`. The paper says "only monotonicity and completeness are used below; the Boolean
structure is free"; the mechanisation says the *order axioms* are free too, because firing is an
existential over `S` and `⊑` only grows `S`.

`Lattice.lean`'s three concrete Lemma 2s are those generic ones **instantiated**, not re-proved. That is
deliberate: two proofs of one statement can drift apart, and the claim being made is precisely that the
argument never mentions the vocabulary. So a rung that adds a channel — `Llm` did at ⟨0.13⟩; the privacy
work queues `Health` and `Motion` — is an instantiation, not a re-opened question.

**Measured, because "it should still work" is not a result.** Adding a constructor to `Effect` breaks the
build in exactly one place: `Effect.name`'s match goes non-exhaustive. No proof breaks. But the
enumeration `Effect.all` is a *list literal*, and a list literal is happy to be short — so a new channel
could enter the vocabulary, force a one-line name edit, and never appear in a single emitted row while the
differential kept reporting OK. `Effect.all_complete` and `Reason.all_complete` make that a compile error.
That gap is not hypothetical: this model shipped with **seven** effects while the engines were judged in
**eleven**, and nothing said so.

## Reachability — the hypothesis SPEC §4.0's table does not state

SPEC §4.0 says `deny e` fires iff **`e ∈ S`**. PAPER3 Def 4 says it fires iff **some member of `S` refines
`e`**. Those are different predicates, and over the full lattice they disagree on **220** of the emitted
`deny` rows — every one a signature with `Llm ∈ S` and `Net ∉ S`.

No engine can produce such a signature: all four **co-emit** `Llm` and `Net` at a model-provider call site,
which is the fact that makes the refinement hold in the first place. So both texts are right, and
`fires_iff_mem_of_reachable` proves it — over any `coemit` map, so a future refinement rung inherits it.

`fires_ne_mem_off_reachable` and `llm_without_net_unreachable` prove the hypothesis is load-bearing: drop
it and the two readings come apart on exactly the excluded shape. Without those, "restrict to the reachable
lattice" would read as a convenient way to make a disagreement go away rather than as a precondition.

**`coemit` is enumerated, not wildcarded.** Written `| _ => none` it pulls `propext` into every downstream
proof *and* makes a new refined channel default silently to "co-emits with nothing" — which widens the
reachable lattice, and a wider reachable lattice is a weaker precondition on every differential quantifying
over it. Spelling out all eleven cases makes the next vocabulary rung a compile error in the one place it
has to be a decision.

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
vocabulary    : 11 effects, 6 reasons
reachable     : 125400 / 147400  (22000 excluded by co-emission {'Llm': 'Net'})
SPEC §4.0 `e ∈ S` vs PAPER3 `⊑` on deny: 220 differ over the full lattice, 0 over the reachable part
DIFFERENTIAL: OK
```

Three arms, not one. **(1)** the verdicts agree on every row; **(2)** Lean's `coemit` and `policy_model`'s
`CO_EMIT` — independent copies of the same data — agree on which signatures are reachable; **(3)** the two
readings of `deny e` agree everywhere reachable *and* differ somewhere unreachable. Arm 3's second half is
the anti-vacuity clause: a domain restriction that excludes nothing interesting is not a precondition, it
is a narrower test wearing one's clothes.

The vocabularies are reconciled in **both** directions before any row is compared. A Lean-only name would
not raise on its own — `refines` is False on an unknown string, so the two sides would agree by *accident*
on every row mentioning it. The `C` axis of `deny e Unknown[C]` is enumerated rather than fixed at `R`, because a differential that
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
