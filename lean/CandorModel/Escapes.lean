/-
  §8 — THE MOVES THE SIGNATURE ORDER CANNOT SEE.

  Lemma 2 says a `⊑`-increase can only move a verdict toward red. §8 is about everything that is not a
  `⊑`-move. Four escapes, selected by one criterion: they are the **H-sound** ones — enumeration and
  signature changes the invariant is invisible to, which no oracle run can catch and only a ratchet can.

  Each is mechanised in the same three parts, because the three together are what make it an escape rather
  than a change:
    (a) the two signatures are `⊑`-INCOMPARABLE, so Lemma 2 and the ratchet corollaries say nothing;
    (b) a shipped gate RELAXES — red to green;
    (c) where the paper claims partial back-pressure, which channel still fires.

  TWO FINDINGS FELL OUT OF TRANSCRIBING THIS, both the same root cause: Definition 2's amendment
  (`Db ⋢ₑ Net`) did not propagate into §8.

    · **Proposition 6's proof is dead as written.** It reads "Under that order `({Db},∅) ≤ ({Net},∅)`, since
      every element of `{Db}` refines an element of `{Net}`." Under the amended Definition 2 that first step
      is false — `Db ⋢ₑ Net` is stated there explicitly. The PROPOSITION survives, on the surviving
      refinement pair; the witness in its proof does not. Both are below.

    · **Escape 2 has no realizable instance in the shipped vocabulary**, and needs both halves to see why.
      With `Db`: the move is no longer H-sound, because an observed `Db` is not covered by a declared `Net`
      — H catches it, so it is not an escape. With `Llm`, the only surviving refinement: engines CO-EMIT
      `Llm` and `Net`, so any reachable signature determining `Llm` also determines `Net`, and declassifying
      to bare `{Net}` is a plain `⊑`-DECREASE — comparable, and a baseline ratchet reads the loss. Escape 2
      needs a refinement pair that is neither co-emitted nor H-caught, and the vocabulary contains none.
      It is a hazard about a FUTURE vocabulary rung, not a present one.

      Note what closed it: reachability. The same co-emission constraint that makes SPEC §4.0's `deny e`
      table agree with PAPER3's Definition 4 also removes this escape's instance. That is not a coincidence
      — both are the observation that `Llm` never travels without `Net`.

      The escape's STRUCTURE remains live on the destination-CLASS axis (⟨0.20⟩), which §8's own text mixes
      into the same paragraph: a class is not a member of `E`, so H cannot see a class coarsening by
      construction. That axis is outside this model and is not claimed below.
-/
import CandorModel.Honesty

namespace Candor.Escapes

open Candor Candor.Generic Candor.Chain

/-! ## Proposition 6 — the subset order is load-bearing

    The `⊑ₑ`-induced Hoare order is the one that would make destination-coarsening a "gain". Lemma 2 fails
    under it, which is why Definition 7 is plain subset and why Escape 2 is the price of that choice. -/

/-- The Hoare lifting of `⊑ₑ` to effect sets: every member of `A` refines some member of `B`. -/
def hoareLe (A B : ESet) : Prop := ∀ e, A e → ∃ e', B e' ∧ e ⊑ₑ e'

/-- The two signatures Proposition 6 is stated on, and both are REACHABLE. -/
private def llmNetSig : Sig := ⟨fun e => e = Effect.Llm ∨ e = Effect.Net, fun _ => False⟩
private def netSig : Sig := ⟨fun e => e = Effect.Net, fun _ => False⟩

/-- **Proposition 6, on the surviving refinement pair — and on signatures an engine can actually emit.**
    `{Llm, Net}` is Hoare-below `{Net}`, `deny Llm` fires on the first and not the second: the rejection set
    is not upward-closed in that order.

    THE REACHABILITY IS NOT DECORATION. My first version of this used bare `{Llm}`, which is Hoare-below
    `{Net}` and makes the same point — but is a signature no implementation can produce, because engines
    co-emit `Llm` and `Net`. A counterexample on an unreachable point establishes nothing about a deployed
    gate, which is the standing rule this development mechanised two files ago and which I then walked
    straight into. `{Llm, Net}` is reachable and works identically. -/
theorem prop6_llm :
    Reachable llmNetSig ∧ Reachable netSig
    ∧ hoareLe llmNetSig.S netSig.S
    ∧ rejectDeny Effect.Llm llmNetSig
    ∧ ¬ rejectDeny Effect.Llm netSig := by
  refine ⟨?_, ?_, ?_, ⟨Effect.Llm, Or.inl rfl, Refines.refl _⟩, ?_⟩
  · intro e b he hc
    cases e <;> (try cases hc)
    exact Or.inr rfl
  · intro e b he hc
    cases e <;> (try cases hc)
    exact absurd he (by rintro (h : Effect.Llm = Effect.Net); cases h)
  · rintro e (he | he)
    · exact ⟨Effect.Net, rfl, by rw [he]; exact Refines.llmNet⟩
    · exact ⟨Effect.Net, rfl, by rw [he]; exact Refines.refl _⟩
  · rintro ⟨e', he, hr⟩
    rw [he] at hr
    cases hr

/-- **AND THE PROOF AS WRITTEN NO LONGER GOES THROUGH.** PAPER3's Proposition 6 instantiates on `Db`, whose
    first step needs `Db ⊑ₑ Net` — removed by Definition 2's amendment, which says so in as many words.
    `{Db}` is not Hoare-below `{Net}`, so the witness is dead even though the proposition is not.

    Fourth instance of the same pattern in this project's record: a corrected assertion outliving its
    correction in a second location, and the second location is a *proof* this time. -/
theorem prop6_db_witness_is_dead :
    ¬ hoareLe (fun e => e = Effect.Db) (fun e => e = Effect.Net) := by
  intro h
  obtain ⟨e', he, hr⟩ := h Effect.Db rfl
  rw [he] at hr
  cases hr

/-! ## Escape 1 — the enumeration dual

    A function that stops being enumerated leaves every layer AND a ratchet's per-function comparison. No
    `D` shrinks anywhere; no signature changes at all. It is the (A0) drop of Definition 24, seen from the
    gate rather than from the theorem. -/

/-- A gate runs over the ENUMERATED units. Making the enumeration a parameter is the whole point: Lemma 2
    quantifies over signatures for a FIXED analyzed universe, and Escape 1 moves the universe. -/
def gateFires {V E R : Type} (enum : V → Prop) (Reject : GSig E R → Prop) (g : Graph V E R) : Prop :=
  ∃ v, enum v ∧ Reject (T g v)

private inductive One where
  | f
  deriving DecidableEq

private def gNet : Graph One Effect Reason :=
  ⟨fun _ => ⟨fun e => e = Effect.Net, fun _ => False⟩, fun _ _ => False⟩

/-- **The same report, the same signature, two verdicts.** Drop `f` from the enumeration and `deny Net`
    goes green — with no `D`-shrink, no `⊑`-move, and nothing for a per-function ratchet to compare
    against, because the function it would compare is gone. Only an enumeration ratchet sees this, which is
    the function-granularity completeness manifest. -/
theorem escape1_enumeration :
    gateFires (fun _ => True) (rejectDeny Effect.Net) gNet
    ∧ ¬ gateFires (fun _ => False) (rejectDeny Effect.Net) gNet := by
  refine ⟨⟨One.f, trivial, ⟨Effect.Net, ⟨One.f, Reaches.refl _, rfl⟩, Refines.refl _⟩⟩, ?_⟩
  rintro ⟨v, hv, _⟩
  exact hv

/-! ## Escape 2 — the refinement dual, and why it has no instance today -/

/-- With `Db`: the declassification is **not H-sound**, so H catches it and it is not an escape at all.
    An observed `Db` is not covered by a declared `Net` under the amended Definition 2. -/
theorem escape2_db_is_caught_by_H :
    ¬ gcovered Refines Effect.Db (fun e => e = Effect.Net) := by
  rintro ⟨e', he, hr⟩
  rw [he] at hr
  cases hr

/-- With `Llm`: the declassification is H-sound, but **not `⊑`-incomparable**. Co-emission forces any
    reachable signature determining `Llm` to determine `Net` too, so the declassified `({Net}, ∅)` sits
    BELOW it — a plain `⊑`-decrease, which a baseline ratchet reads as the loss it is.

    So Escape 2 needs a refinement pair that is neither co-emitted nor H-caught. The vocabulary has none. -/
theorem escape2_llm_is_comparable_under_reachability
    (B : Sig) (hR : Reachable B) (hLlm : B.S Effect.Llm) :
    Sig.le ⟨fun e => e = Effect.Net, fun _ => False⟩ B := by
  constructor
  · intro e he
    rw [he]
    exact hR Effect.Llm Effect.Net hLlm rfl
  · intro _ h
    exact h.elim

/-! ## Escape 3 — the reclassification escape (determination axis)

    `({e}, ∅) → (∅, {dispatch})`. `S` shrinks while `D` grows, so the move is `⊑`-incomparable and a ratchet
    reads "no gain". A plain `deny e` RELAXES, because `deny e` fires only on determined effects. The reach
    did not go away; it became un-determined. -/

private def before3 : Sig := ⟨fun e => e = Effect.Net, fun _ => False⟩
private def after3 : Sig := ⟨fun _ => False, fun r => r = Reason.dispatch⟩

theorem escape3_determined_to_disclosed :
    ¬ Sig.le before3 after3 ∧ ¬ Sig.le after3 before3
    ∧ rejectDeny Effect.Net before3
    ∧ ¬ rejectDeny Effect.Net after3
    ∧ rejectDenyUnknown Effect.Net (fun _ => True) after3 := by
  refine ⟨?_, ?_, ⟨Effect.Net, rfl, Refines.refl _⟩, ?_, ?_⟩
  · rintro ⟨hS, _⟩; exact hS Effect.Net rfl
  · rintro ⟨_, hD⟩; exact hD Reason.dispatch rfl
  · rintro ⟨e, he, _⟩; exact he
  · exact Or.inr ⟨Reason.dispatch, rfl, trivial⟩

/-! ## Escape 4 — the reason-class escape (taxonomy axis)

    `(∅, {dispatch}) → (∅, {indirect})`, with no change to what the analysis knows. `D` neither grows nor
    shrinks, so the move is `⊑`-incomparable. A reason-scoped gate relaxes; the bare form still fires, but
    names the wrong defect.

    Measured, not hypothetical: reclassifying an owner-less unresolved dispatch from `dispatch:` to
    `callback:` took a deployed `deny E Unknown[dispatch]` gate from 58 of 200 packages to 0 of 200. It was
    rejected by inspection. Nothing in this algebra would have objected. -/

private def before4 : Sig := ⟨fun _ => False, fun r => r = Reason.dispatch⟩
private def after4 : Sig := ⟨fun _ => False, fun r => r = Reason.indirect⟩

theorem escape4_reason_class :
    ¬ Sig.le before4 after4 ∧ ¬ Sig.le after4 before4
    ∧ rejectDenyUnknown Effect.Net (fun r => r = Reason.dispatch) before4
    ∧ ¬ rejectDenyUnknown Effect.Net (fun r => r = Reason.dispatch) after4
    ∧ rejectDenyUnknown Effect.Net (fun _ => True) after4 := by
  refine ⟨?_, ?_, Or.inr ⟨Reason.dispatch, rfl, rfl⟩, ?_, Or.inr ⟨Reason.indirect, rfl, trivial⟩⟩
  · rintro ⟨_, hD⟩
    exact absurd (show Reason.dispatch = Reason.indirect from hD Reason.dispatch rfl) (by decide)
  · rintro ⟨_, hD⟩
    exact absurd (show Reason.indirect = Reason.dispatch from hD Reason.indirect rfl) (by decide)
  · rintro (⟨e, he, _⟩ | ⟨r, hr, hc⟩)
    · exact he
    · exact absurd (hr.symm.trans hc) (by decide)

/-- **What all four have in common**, and the reason §8 exists: each is invisible to Lemma 2 because Lemma 2
    is upward-closure over `⊑`, and none of these is a `⊑`-move. Escapes 1 and 2 have no back-pressure in
    any channel; 3 and 4 have partial back-pressure that names the wrong defect. The closure in every case
    is a ratchet against a baseline, never an invariant. -/
theorem escapes_are_not_le_moves :
    (¬ Sig.le before3 after3 ∧ ¬ Sig.le after3 before3)
    ∧ (¬ Sig.le before4 after4 ∧ ¬ Sig.le after4 before4) :=
  ⟨⟨escape3_determined_to_disclosed.1, escape3_determined_to_disclosed.2.1⟩,
   ⟨escape4_reason_class.1, escape4_reason_class.2.1⟩⟩

end Candor.Escapes
