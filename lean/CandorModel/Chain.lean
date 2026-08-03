/-
  THE TRANSITIVE RULE, AND WHY ⟨0.25⟩ HAD TO REVERSE ⟨0.24⟩.

  SPEC §4.0 asserts: "the transitive effect set (§2.2) is the LEAST FIXPOINT of the monotone componentwise
  join over this finite lattice (Knaster–Tarski) — a callee's `(S, D)` joins into its caller's, so both `S`
  and the reason set `D` propagate along the call graph." Nothing anywhere proves that. It is the load
  bearing sentence for every chained-dependency result the family ships, and it has been an assertion.

  This file is the first thing in the development that reaches the REPORT layer rather than the gate
  algebra. That matters because the last three rungs all lived here — ⟨0.24⟩ CONTRIBUTES, ⟨0.25⟩ the join
  key, ⟨0.26⟩ the sidecar manifest — and none of them is a statement about `Reject`.

  WHAT IT PROVES
    · `T` is a fixpoint of the join, and the LEAST one (Knaster–Tarski, in the form the spec needs).
    · `T` is IDEMPOTENT under chaining: re-chaining a report that already carries transitive signatures
      adds nothing.
    · `T` is MONOTONE in the graph: a newly-resolved callee, or a newly-determined effect, can only grow
      it. Composed with Lemma 2 this is the trust direction in full generality.

  WHAT THESE DO NOT DO, because the distinction is the point of having both. Conformance PARTs 25 and 26
  check that the four ENGINES are idempotent and monotone. The theorems here check that the RULE is. An
  engine can implement a sound rule incorrectly, and a correct engine can implement an unsound rule
  faithfully — those are different failures with different fixes, and neither instrument sees the other's.
  Before this file the second kind had no instrument at all, which is how ⟨0.24⟩'s drop rule reached four
  conforming implementations.
    · **The ⟨0.24⟩ drop rule was unsound in the gate direction, and here is the witness.** Dropping an
      ambiguous join key is the ⊥ of the three options; the union is the ⊤; picking sits between. All
      three are sound in the FABRICATION direction, which is what made the drop rule look conservative.
      Only the union is sound in the SILENCE direction, and `deny_passes_under_drop_fires_under_union`
      exhibits a two-node graph where the drop rule mandates a green gate over a call whose target the
      engine has just declared itself unable to name.

  That last theorem is the ⟨0.25⟩ floor bump. It was found by reading, argued in prose, and measured
  across three real dep trees. It is now also a proof.
-/
import CandorModel.Lattice

namespace Candor.Chain

open Candor.Generic

variable {V E R : Type}

/-- Componentwise join — the `⊔` of SPEC §4.0's product lattice. -/
def join (a b : GSig E R) : GSig E R :=
  ⟨fun e => a.S e ∨ b.S e, fun r => a.D r ∨ b.D r⟩

/-- The empty signature: determined-pure with no disclosure. `⊥`. -/
def bot : GSig E R := ⟨fun _ => False, fun _ => False⟩

/-- A call graph over units `V`: what each unit was directly classified as, and what it calls. `calls` is a
    relation rather than a list because a call site that resolves to SEVERAL candidates — the ambiguous key
    of ⟨0.25⟩ — is exactly a unit with several successors. -/
structure Graph (V E R : Type) where
  direct : V → GSig E R
  calls : V → V → Prop

/-- Reflexive-transitive reachability in the call graph. -/
inductive Reaches (g : Graph V E R) : V → V → Prop where
  | refl (v : V) : Reaches g v v
  | step {u v w : V} : g.calls u v → Reaches g v w → Reaches g u w

/-- **The transitive signature.** Everything reachable, joined — which is the closed form of the least
    fixpoint the spec names. Stated this way rather than as an iteration because the closed form is what
    the proofs below actually need, and because it makes `D` propagating alongside `S` visible rather than
    incidental: the two components are the same reachability, read at different fields. -/
def T (g : Graph V E R) (v : V) : GSig E R :=
  ⟨fun e => ∃ w, Reaches g v w ∧ (g.direct w).S e,
   fun r => ∃ w, Reaches g v w ∧ (g.direct w).D r⟩

/-- The join of the transitive signatures of `v`'s immediate callees. -/
def succJoin (g : Graph V E R) (v : V) : GSig E R :=
  ⟨fun e => ∃ w, g.calls v w ∧ (T g w).S e,
   fun r => ∃ w, g.calls v w ∧ (T g w).D r⟩

/-! ## `T` is a fixpoint of the join

    Stated as containment in both directions rather than as an equation. Predicates are equal only up to
    `funext`/`propext`, and asserting an equation would drag both axioms into every downstream proof for no
    gain — mutual `⊑` is also the form the spec's monotone-join phrasing actually means. -/

theorem T_fixpoint_le (g : Graph V E R) (v : V) :
    GSig.le (T g v) (join (g.direct v) (succJoin g v)) := by
  constructor
  · rintro e ⟨w, hr, hs⟩
    cases hr with
    | refl _ => exact Or.inl hs
    | step hc hrest => exact Or.inr ⟨_, hc, ⟨w, hrest, hs⟩⟩
  · rintro r ⟨w, hr, hd⟩
    cases hr with
    | refl _ => exact Or.inl hd
    | step hc hrest => exact Or.inr ⟨_, hc, ⟨w, hrest, hd⟩⟩

theorem T_fixpoint_ge (g : Graph V E R) (v : V) :
    GSig.le (join (g.direct v) (succJoin g v)) (T g v) := by
  constructor
  · intro e h
    cases h with
    | inl hd => exact ⟨v, Reaches.refl v, hd⟩
    | inr hs => obtain ⟨w, hc, ⟨x, hr, hx⟩⟩ := hs
                exact ⟨x, Reaches.step hc hr, hx⟩
  · intro r h
    cases h with
    | inl hd => exact ⟨v, Reaches.refl v, hd⟩
    | inr hs => obtain ⟨w, hc, ⟨x, hr, hx⟩⟩ := hs
                exact ⟨x, Reaches.step hc hr, hx⟩

/-- **`T` is the LEAST such fixpoint.** Anything that dominates the direct signatures and is closed under
    calls already dominates `T`. This is the half that makes "least fixpoint" mean something: without it,
    the top signature would satisfy the fixpoint equation too, and an engine could discharge the rule by
    charging every function with every effect. -/
theorem T_least (g : Graph V E R) (f : V → GSig E R)
    (hdirect : ∀ v, GSig.le (g.direct v) (f v))
    (hclosed : ∀ u v, g.calls u v → GSig.le (f v) (f u)) (v : V) :
    GSig.le (T g v) (f v) := by
  constructor
  · rintro e ⟨w, hr, hs⟩
    have : ∀ {a b : V}, Reaches g a b → (f b).S e → (f a).S e := by
      intro a b hab
      induction hab with
      | refl _ => exact fun h => h
      | step hc _ ih => exact fun h => (hclosed _ _ hc).1 e (ih h)
    exact this hr ((hdirect w).1 e hs)
  · rintro r ⟨w, hr, hd⟩
    have : ∀ {a b : V}, Reaches g a b → (f b).D r → (f a).D r := by
      intro a b hab
      induction hab with
      | refl _ => exact fun h => h
      | step hc _ ih => exact fun h => (hclosed _ _ hc).2 r (ih h)
    exact this hr ((hdirect w).2 r hd)

/-! ## Idempotence

    Chaining consumes dependency reports whose entries ALREADY carry transitive signatures, so the operator
    is applied to its own output. Conformance PART 25 (P2) checks four engines do not drift when that
    happens; this checks the OPERATOR does not, which is the premise that property is testing them
    against. -/

/-- Re-chaining: the same call graph, but each unit's "direct" signature is the transitive one. -/
def rechain (g : Graph V E R) : Graph V E R := ⟨T g, g.calls⟩

theorem T_rechain_le (g : Graph V E R) (v : V) : GSig.le (T (rechain g) v) (T g v) := by
  constructor
  · rintro e ⟨w, hr, ⟨x, hrx, hx⟩⟩
    refine ⟨x, ?_, hx⟩
    have trans : ∀ {a b c : V}, Reaches (rechain g) a b → Reaches g b c → Reaches g a c := by
      intro a b c hab
      induction hab with
      | refl _ => exact fun h => h
      | step hc _ ih => exact fun h => Reaches.step hc (ih h)
    exact trans hr hrx
  · rintro r ⟨w, hr, ⟨x, hrx, hx⟩⟩
    refine ⟨x, ?_, hx⟩
    have trans : ∀ {a b c : V}, Reaches (rechain g) a b → Reaches g b c → Reaches g a c := by
      intro a b c hab
      induction hab with
      | refl _ => exact fun h => h
      | step hc _ ih => exact fun h => Reaches.step hc (ih h)
    exact trans hr hrx

theorem T_rechain_ge (g : Graph V E R) (v : V) : GSig.le (T g v) (T (rechain g) v) := by
  constructor
  · rintro e ⟨w, hr, hs⟩
    exact ⟨v, Reaches.refl v, ⟨w, hr, hs⟩⟩
  · rintro r ⟨w, hr, hd⟩
    exact ⟨v, Reaches.refl v, ⟨w, hr, hd⟩⟩

/-! ## Monotonicity in the graph — the trust direction

    A newly-resolved callee, or a newly-determined effect in a dependency, can only GROW `T`. Composed with
    Lemma 2 (which says a grown signature can only move a verdict toward red) this is the whole guarantee
    that improving an analysis never flips a gate from red to green. -/

theorem T_mono (g₁ g₂ : Graph V E R)
    (hd : ∀ v, GSig.le (g₁.direct v) (g₂.direct v))
    (hc : ∀ u v, g₁.calls u v → g₂.calls u v) (v : V) :
    GSig.le (T g₁ v) (T g₂ v) := by
  have hreach : ∀ {a b : V}, Reaches g₁ a b → Reaches g₂ a b := by
    intro a b h
    induction h with
    | refl x => exact Reaches.refl x
    | step hcall _ ih => exact Reaches.step (hc _ _ hcall) ih
  constructor
  · rintro e ⟨w, hr, hs⟩
    exact ⟨w, hreach hr, (hd w).1 e hs⟩
  · rintro r ⟨w, hr, hdd⟩
    exact ⟨w, hreach hr, (hd w).2 r hdd⟩

/-! ## ⟨0.25⟩ — the ambiguous join key

    An ambiguous key is a call site whose target the engine cannot name uniquely: two entries share the
    key. §2.2 rule 1 gives three conceivable responses, and ⟨0.24⟩ and earlier chose the wrong one.

      UNION  — resolve to every colliding entry.        ⟨0.25⟩, and what all four engines already did.
      PICK   — resolve to one of them.                  Forbidden in both texts: it fabricates.
      DROP   — resolve to nothing.                      ⟨0.24⟩'s rule. This is the cardinal sin.

    Ordering them is easy and is not the point: `drop ⊑ pick ⊑ union` falls straight out of `T_mono`,
    since each removes edges from the next. The point is what that ordering MEANS under ⟨0.21⟩, where
    absence from `functions` is a positive claim of purity. A smaller `T` is not a more cautious answer.
    It is a more confident one. -/

/-- Dropping edges out of `u` — ⟨0.24⟩'s rule, as a graph transformation. -/
def dropAt (g : Graph V E R) (u : V) : Graph V E R :=
  ⟨g.direct, fun a b => g.calls a b ∧ ¬ (a = u)⟩

/-- Ordering, from monotonicity: the drop rule always under-approximates the union. Sound against
    FABRICATION — which is exactly why it read as the conservative choice for two rungs. -/
theorem drop_le_union (g : Graph V E R) (u v : V) :
    GSig.le (T (dropAt g u) v) (T g v) := by
  refine T_mono (dropAt g u) g (fun w => ⟨fun _ h => h, fun _ h => h⟩) ?_ v
  intro a b h
  exact h.1

/-- **The general form, for EVERY policy verb at once.** Compose `drop_le_union` with Lemma 2 — upward
    closure is the only property of `Reject` used, and all three shipped verbs have it (`lemma2_deny`,
    `lemma2_denyUnknown`, `lemma2_pure`), as does any verb a future rung adds under the same discipline.

    Read the direction carefully, because it is the whole argument. A violation found under the DROP rule
    is still a violation under the union: dropping never invents one. What it does is lose them. So the
    drop rule is sound against fabrication and unsound against silence, which is precisely the trade this
    family does not permit — and precisely why it survived two rungs looking conservative. -/
theorem drop_only_loosens (g : Graph V E R) (u v : V) (Reject : GSig E R → Prop)
    (hup : GUpwardClosed Reject) :
    Reject (T (dropAt g u) v) → Reject (T g v) :=
  fun h => hup _ _ (drop_le_union g u v) h

end Candor.Chain

/-! ## The witness: the ⟨0.24⟩ text mandated a green gate over an unnamed target

    Two units. `caller` calls `callee`; `callee` performs `Net`. The call site's key is ambiguous, so
    ⟨0.24⟩ dropped it. Under the union `deny Net` fires; under the drop it does not — and under ⟨0.21⟩ the
    caller is not merely missing from the report, it is *claimed pure*.

    This is the shape the ⟨0.25⟩ bump was written to correct, and the reason the correction is not a
    preference. Note which direction it fails in: no effect is charged to a function that lacks one, so
    every fabrication check passes. The failure is silence, and silence is the one thing this family's
    reports are not allowed to be wrong about. -/

namespace Candor.Chain.Witness

open Candor Candor.Generic Candor.Chain

private inductive Unit2 where
  | caller | callee
  deriving DecidableEq

private def netAt : Unit2 → Sig
  | .caller => ⟨fun _ => False, fun _ => False⟩
  | .callee => ⟨fun e => e = Effect.Net, fun _ => False⟩

private def g : Graph Unit2 Effect Reason :=
  ⟨netAt, fun a b => a = Unit2.caller ∧ b = Unit2.callee⟩

/-- Resolved (⟨0.25⟩ union): the caller reaches the `Net`, and `deny Net` fires. -/
theorem union_fires : rejectDeny Effect.Net (T g Unit2.caller) :=
  ⟨Effect.Net, ⟨Unit2.callee, Reaches.step ⟨rfl, rfl⟩ (Reaches.refl _), rfl⟩, Refines.refl _⟩

/-- Dropped (⟨0.24⟩): the caller reaches nothing, and `deny Net` passes. -/
theorem drop_passes : ¬ rejectDeny Effect.Net (T (dropAt g Unit2.caller) Unit2.caller) := by
  rintro ⟨e, ⟨w, hr, hs⟩, _⟩
  cases hr with
  | refl _ => exact hs
  | step hc _ => exact hc.2 rfl

/-- **The two together.** One graph, one gate, two verdicts — decided entirely by which of the two texts
    the implementation follows. -/
theorem deny_passes_under_drop_fires_under_union :
    rejectDeny Effect.Net (T g Unit2.caller) ∧
      ¬ rejectDeny Effect.Net (T (dropAt g Unit2.caller) Unit2.caller) :=
  ⟨union_fires, drop_passes⟩

end Candor.Chain.Witness
