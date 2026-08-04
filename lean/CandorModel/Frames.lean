/-
  §3's RUNS AND FRAMES — THE STRUCTURE THE CHARGING CONVENTION NEEDS, AND PROPOSITION 4.

  PAPER3 gives Definitions 16a–16c a transition system "so that they are definitions rather than appeals to
  intuition". Everything above this file took `obs`, `analyzed` and `ExecReaches` as primitive; here they
  get their content, at the one level of detail the theorems actually consume — a stack is a list of frames
  innermost-first, and charging is a walk down it.

  TWO THINGS ARE PROVED, and the second is why the file exists.

  **Proposition 4 (direct charging is functional).** Every covered-reached issue event is charged to
  exactly one analyzed frame: its nearest analyzed encloser. Written as a `List` walk the existence half is
  definitional — `chargeTo` is a function — so the content is that the function computes what the prose
  describes (`chargeTo_spec`) and that the prose describes at most one frame (`nearest_unique`). Uniqueness
  is the half worth having: it is what makes `obs` well-defined, and `obs` is what H and (A2) quantify over.

  **The decomposition lemma discharges an assumption I had to state and could not prove.**
  `Honesty.lean` flags this: Definition 19a's covered-reached relation (analyzed OR modelled frames
  between) is not Definition 27's single-hop collapse (modelled frames only), and the paper warns that
  substituting one for the other "would reduce Theorem 1(ii) to depth one and make transitive soundness
  non-transitive". `ExecReaches` is the reflexive TRANSITIVE closure of the collapsed edge, and the claim
  that this recovers covered-reached rested on a decomposition argument about stacks that the model did not
  contain. `decomposes_of_allCovered` is that argument: a segment with no uncovered frame splits into
  modelled-only runs separated by analyzed frames — i.e. into a chain of collapse steps, exactly.

  What remains after it is a definition rather than an assumption: by Definition 16b an executed call
  `f → g` is a `call` step pushing `g` directly onto a frame of `f`, so stack adjacency IS the call
  relation. The combinatorial gap is the one closed below.
-/
import CandorModel.Honesty

namespace Candor.Frames

variable {V : Type}

/-- **Definition 17 (coverage classes).** Exhaustive by construction, with `uncovered` as the catch-all —
    which is precisely what makes (A0)'s second conjunct load-bearing: an engine that silently drops a
    function has thereby classified it `uncovered`, legitimately. -/
inductive Class where
  | analyzed | modelled | uncovered
  deriving DecidableEq

/-- **Definition 16a.** A frame is a function plus an activation identifier, so two activations of the same
    function are distinct frames. -/
abbrev Frame (V : Type) := V × Nat

/-- **Definition 18 (charging convention).** Walk the enclosing chain innermost-first: an analyzed frame
    takes the charge, a modelled frame passes it outward, an uncovered frame TERMINATES the chain and the
    effect is carried by the coverage envelope instead.

    The three-way split is the whole accounting: a modelled target folds into `direct(f).S` (the load (A2)
    carries), an unresolvable site contributes a reason to `D(f)` ((A1)), an uncovered callee enters
    neither. -/
def chargeTo (cls : V → Class) : List (Frame V) → Option (Frame V)
  | [] => none
  | fr :: rest =>
    match cls fr.1 with
    | Class.analyzed => some fr
    | Class.modelled => chargeTo cls rest
    | Class.uncovered => none

/-- "`fr` is the nearest analyzed encloser of this issue": it sits in the chain, it is analyzed, and every
    frame inside it is modelled. Stated inductively because that is the shape of Definition 18's walk, and
    because the inductive form is what makes uniqueness an inversion rather than an index computation. -/
inductive NearestAnalyzed (cls : V → Class) : List (Frame V) → Frame V → Prop where
  | here {fr : Frame V} {rest : List (Frame V)} :
      cls fr.1 = Class.analyzed → NearestAnalyzed cls (fr :: rest) fr
  | skip {x fr : Frame V} {rest : List (Frame V)} :
      cls x.1 = Class.modelled → NearestAnalyzed cls rest fr → NearestAnalyzed cls (x :: rest) fr

/-- The function computes the prose. -/
theorem chargeTo_spec (cls : V → Class) :
    ∀ (chain : List (Frame V)) (fr : Frame V),
      chargeTo cls chain = some fr → NearestAnalyzed cls chain fr := by
  intro chain
  induction chain with
  | nil => intro fr h; nomatch h
  | cons x rest ih =>
      intro fr h
      unfold chargeTo at h
      cases hx : cls x.1 with
      | analyzed =>
          rw [hx] at h
          have : x = fr := Option.some.inj h
          exact this ▸ NearestAnalyzed.here hx
      | modelled =>
          rw [hx] at h
          exact NearestAnalyzed.skip hx (ih fr h)
      | uncovered => rw [hx] at h; nomatch h

/-- **Proposition 4's uniqueness half.** At most one frame answers the description, so `obs` is
    well-defined — and `obs` is what H and (A2) quantify over, so this is load-bearing rather than
    housekeeping. -/
theorem nearest_unique (cls : V → Class) :
    ∀ {chain : List (Frame V)} {a b : Frame V},
      NearestAnalyzed cls chain a → NearestAnalyzed cls chain b → a = b := by
  intro chain a b ha
  induction ha with
  | @here fr rest hfr =>
      intro hb
      cases hb with
      | here _ => rfl
      | skip hm _ => exact absurd (hfr.symm.trans hm) (by decide)
  | @skip x fr rest hm _ ih =>
      intro hb
      cases hb with
      | here ha' => exact absurd (ha'.symm.trans hm) (by decide)
      | skip _ hrest => exact ih hrest

/-- The excluded case, and it is a real one: no analyzed frame is charged, and the effect is carried by the
    coverage envelope. This is the clause that makes Theorem 1(ii)'s exclusion a partition of EVENTS rather
    than a stipulation. -/
theorem chargeTo_none_no_nearest (cls : V → Class) :
    ∀ (chain : List (Frame V)),
      chargeTo cls chain = none → ∀ fr, ¬ NearestAnalyzed cls chain fr := by
  intro chain
  induction chain with
  | nil => intro _ fr hn; cases hn
  | cons x rest ih =>
      intro h fr hn
      unfold chargeTo at h
      cases hx : cls x.1 with
      | analyzed => rw [hx] at h; nomatch h
      | modelled =>
          rw [hx] at h
          cases hn with
          | here ha => exact absurd (ha.symm.trans hx) (by decide)
          | skip _ hrest => exact ih h fr hrest
      | uncovered =>
          cases hn with
          | here ha => exact absurd (ha.symm.trans hx) (by decide)
          | skip hm _ => exact absurd (hm.symm.trans hx) (by decide)

/-! ## The decomposition lemma

    This is the one that discharges `Honesty.lean`'s stated assumption. -/

/-- Definition 19a's condition: no uncovered frame in the segment between two frames. -/
def AllCovered (cls : V → Class) (seg : List (Frame V)) : Prop :=
  ∀ x ∈ seg, cls x.1 ≠ Class.uncovered

/-- A segment presented as Definition 27's collapse would see it: modelled-only runs, separated by analyzed
    frames. Each `split` is one collapsed edge; the whole chain is their transitive composition. -/
inductive Decomposes (cls : V → Class) : List (Frame V) → Prop where
  | modelledOnly {seg : List (Frame V)} :
      (∀ x ∈ seg, cls x.1 = Class.modelled) → Decomposes cls seg
  | split {pre : List (Frame V)} {a : Frame V} {post : List (Frame V)} :
      (∀ x ∈ pre, cls x.1 = Class.modelled) → cls a.1 = Class.analyzed →
      Decomposes cls post → Decomposes cls (pre ++ a :: post)

/-- **COVERED-REACHED IS THE TRANSITIVE CLOSURE OF THE COLLAPSE.** A segment containing no uncovered frame
    decomposes into modelled-only runs separated by analyzed frames — so a covered-reached pair of analyzed
    frames is joined by a finite chain of Definition 27 edges, and nothing else is needed to identify
    `ExecReaches` with Definition 19a.

    The paper's warning is what this makes precise: substituting the single-hop collapse for covered-reached
    would keep only the FIRST `split` and discard the recursive tail, which is exactly "reduce Theorem 1(ii)
    to depth one". -/
theorem decomposes_of_allCovered (cls : V → Class) :
    ∀ (seg : List (Frame V)), AllCovered cls seg → Decomposes cls seg := by
  intro seg
  induction seg with
  | nil => intro _; exact Decomposes.modelledOnly (by intro x hx; cases hx)
  | cons x rest ih =>
      intro h
      have hx : cls x.1 ≠ Class.uncovered := h x (List.mem_cons_self ..)
      have hrest : AllCovered cls rest := fun y hy => h y (List.mem_cons_of_mem _ hy)
      cases hc : cls x.1 with
      | analyzed =>
          exact Decomposes.split (pre := []) (by intro y hy; cases hy) hc (ih hrest)
      | modelled =>
          cases ih hrest with
          | @modelledOnly seg hm =>
              refine Decomposes.modelledOnly ?_
              intro y hy
              cases hy with
              | head => exact hc
              | tail _ hy' => exact hm y hy'
          | @split pre a post hpre ha hpost =>
              refine Decomposes.split (pre := x :: pre) ?_ ha hpost
              intro y hy
              cases hy with
              | head => exact hc
              | tail _ hy' => exact hpre y hy'
      | uncovered => exact absurd hc hx

/-- Membership in an append, by hand. `List.mem_append` would do, but it is stated as an `Iff` and drags
    `propext` into every proof that uses it — which would put the theorem below in a weaker tier for a
    reason that has nothing to do with its content. -/
theorem mem_append_cases {α : Type} {y : α} :
    ∀ {l₁ l₂ : List α}, y ∈ l₁ ++ l₂ → y ∈ l₁ ∨ y ∈ l₂
  | [], _, h => Or.inr h
  | _ :: _, _, h => by
      cases h with
      | head => exact Or.inl (List.mem_cons_self ..)
      | tail _ h' =>
          rcases mem_append_cases h' with h'' | h''
          · exact Or.inl (List.mem_cons_of_mem _ h'')
          · exact Or.inr h''

/-- The converse direction, for completeness: a decomposed segment has no uncovered frame. Together these
    say `AllCovered` and `Decomposes` name the same segments, which is the equivalence the identification
    of `ExecReaches` with Definition 19a rests on. -/
theorem allCovered_of_decomposes (cls : V → Class) :
    ∀ {seg : List (Frame V)}, Decomposes cls seg → AllCovered cls seg := by
  intro seg hd
  induction hd with
  | modelledOnly hm => intro y hy; rw [hm y hy]; intro hc; cases hc
  | @split pre a post hpre ha _ ih =>
      intro y hy
      rcases mem_append_cases hy with h | h
      · rw [hpre y h]; intro hc; cases hc
      · cases h with
        | head => rw [ha]; intro hc; cases hc
        | tail _ h' => exact ih y h'

end Candor.Frames
