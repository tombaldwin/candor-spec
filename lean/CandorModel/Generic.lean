/-
  LEMMA 2, PROVED WITHOUT THE VOCABULARY.

  `Lattice.lean` proves monotone denial for candor's eleven effects and six reasons. That is the statement
  the engines are judged against — but it is not the statement the paper is making, and the difference
  matters in a specific, practical way.

  Every rung that adds a channel adds a constructor to `Effect`. `Llm` did (⟨0.13⟩). The privacy work
  queues `Health` and `Motion`. A `Db`-precedent refinement adds an edge to `⊑ₑ`. If Lemma 2 is proved
  about a fixed eleven-element type, each of those changes re-opens the question, and re-opening a question
  is exactly how a property quietly stops being true while its proof still compiles — because the proof was
  about the OLD type.

  So this file proves the lemma about an ARBITRARY effect type, an ARBITRARY reason type, and — this is the
  part that surprised me — an ARBITRARY relation. Not an arbitrary preorder: an arbitrary relation. Nothing
  below uses reflexivity or transitivity of `⊑ₑ`. The paper says "only monotonicity and completeness are
  used below; the Boolean structure is free"; the mechanisation says something slightly stronger, which is
  that the ORDER AXIOMS are free too. Lemma 2 holds because `fires` is an existential over `S` and `⊑`
  grows `S` — the preorder is carried along and never consulted.

  That is worth having as a machine-checked fact rather than an observation, because it converts "will
  adding Health break monotone denial?" from a question into an instantiation. `Lattice.lean` now derives
  its three concrete Lemma 2s from these, so there is ONE argument, not two that could drift apart.
-/

namespace Candor.Generic

variable {E R : Type}

/-- **Definition 6**, with the vocabulary abstracted away. -/
structure GSig (E R : Type) where
  S : E → Prop
  D : R → Prop

/-- Pointwise implication — the paper's "plain subset". Def 3's scope note insists on it for every
    containment except the observation side, and reading it modulo `⊑ₑ` is what Proposition 6 proves
    breaks upward-closure. Keeping it plain, and generic, keeps that mistake unavailable here. -/
def gsub {α : Type} (A B : α → Prop) : Prop := ∀ x, A x → B x

/-- **Definition 7 (product order)**, abstractly. -/
def GSig.le (a b : GSig E R) : Prop := gsub a.S b.S ∧ gsub a.D b.D

/-- **Definition 4 (firing)**, over an arbitrary relation `ref`. Note it is never assumed to be a preorder;
    see the header. -/
def gfires (ref : E → E → Prop) (e : E) (S : E → Prop) : Prop := ∃ e', S e' ∧ ref e' e

/-- **Definition 3 (covering; observation side)**, generically. An observed `e` is covered by `S` when it
    REFINES some member — the opposite reading of the same preorder from `gfires`, and the reading PAPER3's
    Definition 3 scope note mandates for `obs(f) ⊆ S(f)`, `charged(f) ⊆ S(f)`, H, Definition 22 and
    **Theorem 1**. Every other containment in the paper is plain subset. -/
def gcovered (ref : E → E → Prop) (e : E) (S : E → Prop) : Prop := ∃ e', S e' ∧ ref e e'

theorem gcovered_mono {ref : E → E → Prop} {A B : E → Prop} (h : gsub A B) {e : E} :
    gcovered ref e A → gcovered ref e B := by
  rintro ⟨e', hm, hr⟩
  exact ⟨e', h e' hm, hr⟩

/-- Plain membership implies the modulo reading — the paper's "plain-`⊆` steps compose with modulo-`⊑ₑ`
    steps in the sound direction, since `⊑ₑ` is a preorder and plain containment implies the modulo
    form". The converse fails, which is why stating a theorem in the plain form is stating a DIFFERENT
    theorem and not a tidier one. -/
theorem gcovered_of_mem {ref : E → E → Prop} (hrefl : ∀ x, ref x x) {S : E → Prop} {e : E} (h : S e) :
    gcovered ref e S := ⟨e, h, hrefl e⟩

def GUpwardClosed (Reject : GSig E R → Prop) : Prop :=
  ∀ a b : GSig E R, GSig.le a b → Reject a → Reject b

/-- The whole engine of Lemma 2, in three lines and with no hypothesis on `ref`: firing is an existential
    over `S`, and a larger `S` can only make an existential easier to satisfy. -/
theorem gfires_mono {ref : E → E → Prop} {e : E} {A B : E → Prop} (h : gsub A B) :
    gfires ref e A → gfires ref e B := by
  rintro ⟨e', hmem, href⟩
  exact ⟨e', h e' hmem, href⟩

/-- **Lemma 2** for `deny e`, for any vocabulary and any refinement relation. -/
theorem gLemma2_deny (ref : E → E → Prop) (e : E) :
    GUpwardClosed (R := R) (fun σ => gfires ref e σ.S) := by
  rintro a b ⟨hS, _⟩ h
  exact gfires_mono hS h

/-- **Lemma 2** for `deny e Unknown[C]`, for any vocabulary, any relation, and any reason-scope. -/
theorem gLemma2_denyUnknown (ref : E → E → Prop) (e : E) (C : R → Prop) :
    GUpwardClosed (fun σ : GSig E R => gfires ref e σ.S ∨ ∃ r, σ.D r ∧ C r) := by
  rintro a b ⟨hS, hD⟩ h
  cases h with
  | inl hf => exact Or.inl (gfires_mono hS hf)
  | inr hr => obtain ⟨r, hrD, hrC⟩ := hr
              exact Or.inr ⟨r, hD r hrD, hrC⟩

/-- **Lemma 2** for `pure`, for any vocabulary. Neither `ref` nor `R` appears — `pure` does not consult
    the refinement relation at all, which is the mechanised form of the ⟨Def 32⟩ amendment's point that a
    disclosure alone does not fail it. -/
theorem gLemma2_pure : GUpwardClosed (fun σ : GSig E R => ∃ e, σ.S e) := by
  rintro a b ⟨hS, _⟩ ⟨e, he⟩
  exact ⟨e, hS e he⟩

/-! ## Reachability, and why `deny e` can be read two different ways and be right both times

    SPEC §4.0's table says `deny e` fires iff **`e ∈ S`**. PAPER3 Def 4 says it fires iff **some member of
    `S` refines `e`**. Those are different predicates and they disagree on 220 of the emitted `deny` rows —
    every one of them a signature with `Llm ∈ S` and `Net ∉ S`.

    No engine can produce such a signature. All four CO-EMIT `Llm` and `Net` at a model-provider call site,
    which is the very fact that makes the refinement hold. So the two readings coincide exactly where it
    matters, and the spec's table is correct — CONDITIONALLY, on a hypothesis the table does not state.

    That condition is not a detail. Stated as a standing rule in SPEC §2.2: *a model quantifying over all of
    `L` will fire correctly on points that do not exist.* It cost 100 spurious disagreements on candor-swift
    before anyone noticed, and it is what PAPER1's well-formedness condition (W) was reaching for and
    mis-stated — (W) read `Unknown ∈ S ⇒ D ≠ ∅`, whose antecedent is unsatisfiable because `Unknown ∉ E`, so
    it constrained nothing at all.

    Below it is a hypothesis you cannot forget, because the theorem does not typecheck without it. -/

/-- A signature is REACHABLE when no refined channel appears without the base channel it co-emits with.
    `coemit` is data, not structure: `Llm ↦ Net` today, and whatever a future refinement rung adds. -/
def GReachable (coemit : E → Option E) (S : E → Prop) : Prop :=
  ∀ e b, S e → coemit e = some b → S b

/-- **THE RECONCILIATION.** On reachable signatures, firing over the refinement preorder and plain
    membership are the SAME PREDICATE — so SPEC §4.0's table and PAPER3's Def 4 are two spellings of one
    rule, not two rules.

    The hypotheses say only that `ref` is reflexive and that its non-trivial edges are co-emission edges.
    Nothing here is specific to `Llm`/`Net`, so a future refinement rung inherits this the moment it is
    added to `coemit` — which is the whole reason it is stated generically. -/
theorem gfires_iff_mem_of_reachable
    (coemit : E → Option E) (ref : E → E → Prop)
    (hrefl : ∀ x, ref x x)
    (hgen : ∀ a b, ref a b → a = b ∨ coemit a = some b)
    {S : E → Prop} (hR : GReachable coemit S) (e : E) :
    gfires ref e S ↔ S e := by
  constructor
  · rintro ⟨e', hmem, href⟩
    rcases hgen e' e href with rfl | h
    · exact hmem
    · exact hR e' e hmem h
  · intro h
    exact ⟨e, h, hrefl e⟩

/-! ## What genericity buys, stated as a check rather than a claim

    A vocabulary rung is now an INSTANTIATION. The type below is candor's eleven plus the two channels the
    privacy work queues; the three Lemma 2s hold of it with no new proof, because they never mentioned the
    old type. If a future rung DID break monotone denial, it would have to do so by changing the shape of a
    verb — not by adding a channel — and that change would land in `Lattice.lean` where it is visible. -/

private inductive EffectPlus where
  | Clipboard | Clock | Db | Env | Exec | Fs | Ipc | Llm | Log | Net | Rand
  | Health | Motion

private example (ref : EffectPlus → EffectPlus → Prop) (e : EffectPlus) :
    GUpwardClosed (R := Unit) (fun σ => gfires ref e σ.S) := gLemma2_deny ref e

private example : GUpwardClosed (fun σ : GSig EffectPlus Unit => ∃ e, σ.S e) := gLemma2_pure

end Candor.Generic
