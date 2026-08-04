/-
  THE TWO MISTAKES A CAREFUL READER MAKES, AS COUNTEREXAMPLES.

  Everything else in this development proves the model is right. This file proves two nearby models are
  WRONG — which is a different and, for a specification, more useful kind of statement. Both of these are
  things the spec and the paper assert in prose, in the two places a reimplementer is most likely to
  "simplify" the design and be quietly punished for it.

  1. READING CONTAINMENT MODULO `⊑ₑ` EVERYWHERE. Definition 3's scope note is emphatic that the refinement
     preorder governs the OBSERVATION side only, and that every other containment is plain subset. It is a
     strange-looking restriction, and the natural instinct is to make the order uniform. PAPER3's
     Proposition 6 proves that instinct breaks Lemma 2. Here is the witness.

  2. THE FLAT CARRIER. SPEC §4.0: "The naïve 'one flat set with `Unknown` in it, ordered by `⊆`-or-
     `Unknown ∈ T`' is only a PREORDER (it cannot tell `{Net, Unknown}` from `{Unknown}`, which
     reason-scoping relies on)". A flat set is obviously simpler than a pair, and every engine's report
     serializes something that looks exactly like one. The pair carrier is antisymmetric and the flat one
     is not, and the two points it confuses are separated by a shipped gate.

  Why bother mechanising a negative. A prose warning is followed when it is understood; these two are
  reached by reasoning that feels like cleaning up. A counterexample that must typecheck is the form of
  warning that survives someone disagreeing with it.
-/
import CandorModel.Lattice

namespace Candor.Counterexample

open Candor Candor.Generic

/-! ## 1. Containment modulo `⊑ₑ` breaks upward closure (PAPER3 Proposition 6) -/

/-- Containment read MODULO the refinement preorder — Definition 3's `covered`, lifted to sets. Every
    member of `A` is covered by some member of `B`. This is the correct reading on the observation side. -/
abbrev subModulo (A B : ESet) : Prop := Generic.gsubModulo Refines A B

/-- …and the order you get by using it for the `S` component of the product order too. -/
def leModulo (a b : Sig) : Prop := subModulo a.S b.S ∧ subR a.D b.D

/-- `{Llm}` is below `{Net}` under the modulo reading — an `Llm` occurrence is a `Net` occurrence. -/
theorem llm_leModulo_net :
    leModulo ⟨fun e => e = Effect.Llm, fun _ => False⟩ ⟨fun e => e = Effect.Net, fun _ => False⟩ :=
  ⟨fun _ h => ⟨Effect.Net, rfl, by rw [h]; exact Refines.llmNet⟩, fun _ h => h⟩

/-- **THE COUNTEREXAMPLE.** `deny Llm` fires on `{Llm}` and not on `{Net}`, yet `{Llm}` is below `{Net}`
    under the modulo reading. So `deny Llm` is NOT upward-closed for `leModulo`: Lemma 2 fails, and with it
    the guarantee that a better analysis never turns a red gate green.

    Note where it bites. Under the *plain* order the two signatures are simply incomparable, and nothing is
    claimed. It is making the order uniform — the tidying instinct — that manufactures a comparison the
    verbs cannot honour. -/
theorem lemma2_fails_under_leModulo :
    ¬ (∀ a b : Sig, leModulo a b → rejectDeny Effect.Llm a → rejectDeny Effect.Llm b) := by
  intro h
  have fires_a : rejectDeny Effect.Llm ⟨fun e => e = Effect.Llm, fun _ => False⟩ :=
    ⟨Effect.Llm, rfl, Refines.refl _⟩
  have := h _ _ llm_leModulo_net fires_a
  obtain ⟨e', he, hr⟩ := this
  rw [he] at hr
  cases hr

/-- The plain order, by contrast, does not relate them at all — so Lemma 2 has nothing to say and says
    nothing. The counterexample above is manufactured entirely by the uniform reading. -/
theorem llm_not_le_net :
    ¬ (Sig.le ⟨fun e => e = Effect.Llm, fun _ => False⟩ ⟨fun e => e = Effect.Net, fun _ => False⟩) := by
  rintro ⟨hS, _⟩
  cases hS Effect.Llm rfl

/-! ## 2. The flat carrier is only a preorder (SPEC §4.0) -/

/-- One flat set over the effects PLUS an `Unknown` marker — what a report's `inferred` array looks like,
    and therefore the carrier a reimplementer reaches for. -/
inductive FlatItem where
  | eff : Effect → FlatItem
  | unknown
  deriving DecidableEq

abbrev Flat := FlatItem → Prop

/-- The order §4.0 names: plain containment, OR the right-hand side carries `Unknown` (on the intuition
    that an `Unknown` "could be anything", so it dominates). -/
def flatLe (a b : Flat) : Prop := (∀ x, a x → b x) ∨ b FlatItem.unknown

private def netAndUnknown : Flat := fun x => x = FlatItem.eff Effect.Net ∨ x = FlatItem.unknown
private def justUnknown : Flat := fun x => x = FlatItem.unknown

theorem flat_le_both_ways :
    flatLe netAndUnknown justUnknown ∧ flatLe justUnknown netAndUnknown :=
  ⟨Or.inr rfl, Or.inr (Or.inr rfl)⟩

/-- **NOT ANTISYMMETRIC.** `{Net, Unknown}` and `{Unknown}` sit below each other and are not the same set.
    So `flatLe` is a preorder, never a partial order, and the two points are indistinguishable to anything
    that only sees the order. -/
theorem flat_not_antisymm :
    ¬ (∀ x, netAndUnknown x ↔ justUnknown x) := by
  intro h
  have : justUnknown (FlatItem.eff Effect.Net) := (h _).mp (Or.inl rfl)
  cases this

/-- The pair carrier, for contrast: mutual containment forces the components to agree pointwise. Stated
    pointwise rather than as `a = b` deliberately — predicate equality needs `funext` and `propext`, and
    pointwise agreement is what antisymmetry MEANS here without dragging either in. -/
theorem sig_le_antisymm (a b : Sig) (h₁ : a ⊑ b) (h₂ : b ⊑ a) :
    (∀ e, a.S e ↔ b.S e) ∧ (∀ r, a.D r ↔ b.D r) :=
  ⟨fun e => ⟨h₁.1 e, h₂.1 e⟩, fun r => ⟨h₁.2 r, h₂.2 r⟩⟩

/-- **AND THE CONFUSION IS OBSERVABLE.** The two points `flatLe` identifies are separated by a shipped
    gate: `deny Net` fires on the pair-carrier signature carrying `Net` alongside a disclosure, and passes
    on the one carrying only the disclosure. A carrier that cannot tell them apart cannot implement the
    verb — which is why the pair is the carrier and not a presentational choice.

    This is also exactly what reason-scoping needs: `deny Net Unknown[c]` must consult `D` and `S`
    separately, and a flat set has already merged them. -/
theorem flat_confusion_is_observable (r : Reason) :
    rejectDeny Effect.Net ⟨fun e => e = Effect.Net, fun x => x = r⟩ ∧
      ¬ rejectDeny Effect.Net ⟨fun _ => False, fun x => x = r⟩ :=
  ⟨⟨Effect.Net, rfl, Refines.refl _⟩, by rintro ⟨e, he, _⟩; exact he⟩

end Candor.Counterexample
