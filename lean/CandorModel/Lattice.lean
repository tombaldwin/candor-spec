/-
  candor's disclosure lattice and policy layer, MACHINE-CHECKED.

  A transcription of PAPER3 §1 (Definitions 1–7, Proposition 1) and §6 (Definitions 30–32, Lemma 2).

  WHY THIS FILE EXISTS. The theory↔spec↔code chain has machinery in two places and none in the third.
  `clause_check.py` proves a conformance property cites a real SPEC clause. Conformance PART 23 runs the
  engines against `reference/policy_model.py`. But `policy_model.py` is a HAND TRANSCRIPTION of the paper
  into Python — an unverified, trusted artifact — and nothing at all relates the spec text to the paper
  text. So the link the whole edifice rests on is two prose documents kept in agreement by human reading.

  Both documents have been wrong. Definition 2 originally read `Db ⊑ₑ Net`, which made `deny Net` fire on a
  determined `{Db}`; a differential against the Python transcription produced 100 disagreements over 1792
  rows, every one that family, model REJECT and engine pass. Definition 32 originally read
  `Reject ⇔ (S,D) ≠ (∅,∅)`, which reported all four CONFORMING implementations as violating the theory on
  the signature `(∅,{r})`. Neither was found by a proof; both were found by running the model against real
  engines and being surprised.

  This file is deliberately Mathlib-free. Lemma 2 needs monotonicity and nothing else — the paper says so
  itself ("Only monotonicity and completeness are used below; the Boolean structure is free") — so sets are
  predicates and the build has no dependencies, stays fast, and is auditable end to end by someone who does
  not know Mathlib.
-/

namespace Candor

/-- **Definition 1 (Capability effects).** Coarse, named world-interactions. Finite by construction here;
    the paper's `…` is closed off at the vocabulary the spec actually ships. -/
inductive Effect where
  | Clipboard | Clock | Db | Env | Exec | Fs | Ipc | Llm | Log | Net | Rand
  deriving DecidableEq, Repr

/-- **Definition 5 (Disclosure reasons).** The causes an analyzer can fail to resolve. -/
inductive Reason where
  | reflect | dispatch | indirect | native | unresolved | setup
  deriving DecidableEq, Repr

/-- **Definition 2 (Refinement preorder), AS AMENDED.** `e ⊑ₑ e'` holds only when *every occurrence of `e`
    is an occurrence of `e'`*. `Llm ⊑ₑ Net` — a model-provider call is an outbound request in every
    instance. Everything else is incomparable; in particular `Db ⋢ₑ Net`, because an embedded, file-backed
    or in-process store is a `Db` effect with no egress whatsoever.

    Declaring this as an inductive relation with exactly two constructors is what makes the amendment
    *checkable*: `Db ⊑ₑ Net` is not merely absent, it is underivable, and `no_db_refines_net` below proves
    it. -/
inductive Refines : Effect → Effect → Prop where
  /-- reflexivity: the preorder is flat among the base channels -/
  | refl (e : Effect) : Refines e e
  /-- the one genuine refinement in the vocabulary -/
  | llmNet : Refines Effect.Llm Effect.Net

infix:50 " ⊑ₑ " => Refines

/-- Effect sets and reason sets as predicates. `⊆` is pointwise implication — the paper's "plain subset",
    which Definition 3's scope note insists on for every containment except the observation side. -/
abbrev ESet := Effect → Prop
abbrev RSet := Reason → Prop

def subE (A B : ESet) : Prop := ∀ e, A e → B e
def subR (A B : RSet) : Prop := ∀ r, A r → B r

/-- **Definition 6 (Effect signature).** `S` determined, `D` the reasons the determination is incomplete.
    `D = ∅` is sound-complete; `D ≠ ∅` carries `Unknown`, tagged with exactly the reasons `D`. -/
structure Sig where
  S : ESet
  D : RSet

/-- **Definition 7 (Product order).** Componentwise plain subset. -/
def Sig.le (a b : Sig) : Prop := subE a.S b.S ∧ subR a.D b.D

infix:50 " ⊑ " => Sig.le

/-- **Definition 4 (Firing; gate side).** A denial of `e` fires on `S` iff `S` contains a *refinement* of
    `e`. Note the direction: down-closure of `{e}`, not of `S`. -/
def fires (e : Effect) (S : ESet) : Prop := ∃ e', S e' ∧ e' ⊑ₑ e

/-- **Definition 3 (Covering; observation side).** An observed `e` is covered by `S` iff `e` refines some
    member. The *opposite* reading of the same preorder — covering is generous to the analyzer, denial to
    the policy. Included so the two directions sit side by side and cannot be conflated by a reader. -/
def covered (e : Effect) (S : ESet) : Prop := ∃ e', S e' ∧ e ⊑ₑ e'

/-! ## The amendment, machine-checked -/

/-- `deny Net` fires on a determined `{Llm}`. (Definition 4's worked example.) -/
theorem fires_net_of_llm : fires Effect.Net (fun e => e = Effect.Llm) := by
  exact ⟨Effect.Llm, rfl, Refines.llmNet⟩

/-- **THE AMENDMENT.** `deny Net` does *not* fire on a determined `{Db}`.

    This is the proposition whose negation cost 100 disagreements over 1792 rows. Under the original
    `Db ⊑ₑ Net` it was false; under the corrected preorder it is provable, and the proof is a case
    analysis showing no constructor derives `Db ⊑ₑ Net`. -/
theorem no_fires_net_of_db : ¬ fires Effect.Net (fun e => e = Effect.Db) := by
  rintro ⟨e', rfl, h⟩
  cases h

/-! ## Policy verbs (Definitions 30–32) -/

/-- **Definition 30 (`deny e`).** A non-empty `D` does not fire it — the analysis cannot assert `e` — but
    is surfaced as an advisory: green *with a disclosure*, never a silent pass. -/
def rejectDeny (e : Effect) (σ : Sig) : Prop := fires e σ.S

/-- **Definition 31 (`deny e Unknown[C]`).** The reason-scoped strict gate. Bare `deny e Unknown` is
    `C = R`, i.e. `C` true everywhere. -/
def rejectDenyUnknown (e : Effect) (C : RSet) (σ : Sig) : Prop :=
  fires e σ.S ∨ ∃ r, σ.D r ∧ C r

/-- **Definition 32 (`pure`), AS AMENDED.** A determined effect fails it; a disclosure alone does not.

    The pre-amendment reading was `(S,D) ≠ (∅,∅)` — which reported all four CONFORMING implementations as
    violating the theory on `(∅,{r})`. Both readings are upward-closed, which is exactly why Lemma 2 did
    not surface the error and a differential did. -/
def rejectPure (σ : Sig) : Prop := ∃ e, σ.S e

/-- `pure` passes a bare `Unknown` — the signature `(∅, {r})`. The fixture the cross-implementation suite
    pins four ways, now also a theorem. -/
theorem pure_passes_bare_unknown (r : Reason) :
    ¬ rejectPure ⟨fun _ => False, fun x => x = r⟩ := by
  rintro ⟨e, h⟩
  exact h

/-! ## Lemma 2 (Monotone denial) -/

/-- A rejection predicate is **upward-closed** when a larger signature can only stay rejected. -/
def UpwardClosed (Reject : Sig → Prop) : Prop :=
  ∀ a b : Sig, a ⊑ b → Reject a → Reject b

/-- `fires` is monotone in `S`: the engine of Lemma 2 for both deny verbs. -/
theorem fires_mono {e : Effect} {A B : ESet} (h : subE A B) : fires e A → fires e B := by
  rintro ⟨e', hmem, href⟩
  exact ⟨e', h e' hmem, href⟩

/-- **Lemma 2** for `deny e`. -/
theorem lemma2_deny (e : Effect) : UpwardClosed (rejectDeny e) := by
  rintro a b ⟨hS, _⟩ h
  exact fires_mono hS h

/-- **Lemma 2** for `deny e Unknown[C]`. -/
theorem lemma2_denyUnknown (e : Effect) (C : RSet) : UpwardClosed (rejectDenyUnknown e C) := by
  rintro a b ⟨hS, hD⟩ h
  cases h with
  | inl hf => exact Or.inl (fires_mono hS hf)
  | inr hr => obtain ⟨r, hrD, hrC⟩ := hr
              exact Or.inr ⟨r, hD r hrD, hrC⟩

/-- **Lemma 2** for `pure`. -/
theorem lemma2_pure : UpwardClosed rejectPure := by
  rintro a b ⟨hS, _⟩ ⟨e, he⟩
  exact ⟨e, hS e he⟩

/-- **Lemma 2's corollary**, the one a shipped engine violated: a newly-determined effect or a
    newly-disclosed blind spot can only move a verdict from green toward red — never back. Stated as the
    contrapositive, which is the form the engines are actually judged against. -/
theorem lemma2_corollary_deny (e : Effect) (a b : Sig) (hle : a ⊑ b) :
    ¬ rejectDeny e b → ¬ rejectDeny e a :=
  fun hnb ha => hnb (lemma2_deny e a b hle ha)

/-! ## Remark 1(i): `Unknown` is not `⊤`

    "Determined to do everything" is `(E, ∅)`; "undetermined" is `(∅, D)` with `D ≠ ∅`. By Definition 7
    these are **incomparable** — a single top element would identify them. Proved rather than asserted,
    because the whole point of the pair is that this distinction survives. -/
theorem determined_not_below_undetermined (r : Reason) :
    ¬ (Sig.le ⟨fun _ => True, fun _ => False⟩ ⟨fun _ => False, fun x => x = r⟩) := by
  rintro ⟨hS, _⟩
  exact hS Effect.Net trivial

theorem undetermined_not_below_determined (r : Reason) :
    ¬ (Sig.le ⟨fun _ => False, fun x => x = r⟩ ⟨fun _ => True, fun _ => False⟩) := by
  rintro ⟨_, hD⟩
  exact hD r rfl

end Candor
