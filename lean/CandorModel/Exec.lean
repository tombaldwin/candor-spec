/-
  The COMPUTABLE face of the model, and the bridge lemmas that make it trustworthy.

  `Lattice.lean` states the model in `Prop`, which is the right form for proving Lemma 2 and the
  amendments but cannot be RUN. This file gives each definition a `Bool`-valued twin and proves the twin
  agrees with it — `firesB e S = true ↔ fires e (· ∈ S)` and so on. The proofs are what stop this being a
  second, unverified transcription sitting beside the first: an executable that disagreed with the model
  would fail to compile, not merely produce different output.

  Why bother: `reference/policy_model.py` is a HAND transcription of the same definitions, and conformance
  PART 23 judges the ENGINES against it. So the Python file is a trusted artifact in the middle of the
  chain, and the two errors the model has actually had (`Db ⊑ₑ Net`, and `pure` rejecting a bare
  `Unknown`) were both of exactly that kind — a definition read slightly wrong. With this file the Lean
  model can be EXECUTED over every signature in the vocabulary and the Python checked against it, which
  turns "someone read both carefully" into a differential.
-/
import CandorModel.Lattice

namespace Candor

/-- The vocabulary, closed at what the spec ships (matching `reference/policy_model.py`'s `E`). -/
def Effect.all : List Effect :=
  [.Clipboard, .Clock, .Db, .Env, .Exec, .Fs, .Ipc, .Llm, .Log, .Net, .Rand]

def Reason.all : List Reason :=
  [.reflect, .dispatch, .indirect, .native, .unresolved, .setup]

/-- THE ENUMERATIONS ARE PROVED COMPLETE, not trusted to be.

    Measured: adding a constructor to `Effect` breaks the build in exactly one place — `Effect.name`'s
    match goes non-exhaustive. It does NOT break these two list literals, because a list literal is happy
    to be short. So without these theorems a new channel could enter the vocabulary, force a one-line name
    edit, and never appear in a single emitted row — the differential would keep reporting OK over a table
    that silently omitted it.

    That is not hypothetical: this model shipped with SEVEN effects while the engines were judged in
    ELEVEN, and nothing said so. `decide` turns the omission into a compile error. -/
theorem Effect.all_complete : ∀ e : Effect, e ∈ Effect.all := by
  intro e; cases e <;> decide

theorem Reason.all_complete : ∀ r : Reason, r ∈ Reason.all := by
  intro r; cases r <;> decide

/-- Definition 2, computably. Reflexive, plus the single genuine refinement. -/
def refinesB (a b : Effect) : Bool :=
  (a == b) || (a == Effect.Llm && b == Effect.Net)

/-- The bridge: the decidable twin agrees with the inductive relation, in both directions. -/
theorem refinesB_iff (a b : Effect) : refinesB a b = true ↔ a ⊑ₑ b := by
  constructor
  · intro h
    simp only [refinesB, Bool.or_eq_true, beq_iff_eq, Bool.and_eq_true] at h
    rcases h with h | ⟨ha, hb⟩
    · subst h; exact Refines.refl a
    · subst ha; subst hb; exact Refines.llmNet
  · intro h
    cases h with
    | refl e => simp [refinesB]
    | llmNet => simp [refinesB]

/-- Definition 4, computably: sets are lists, membership is `List.Mem`. -/
def firesB (e : Effect) (S : List Effect) : Bool :=
  S.any (fun x => refinesB x e)

theorem firesB_iff (e : Effect) (S : List Effect) :
    firesB e S = true ↔ fires e (fun x => x ∈ S) := by
  constructor
  · intro h
    obtain ⟨x, hx, hr⟩ := List.any_eq_true.mp h
    exact ⟨x, hx, (refinesB_iff x e).mp hr⟩
  · rintro ⟨x, hx, hr⟩
    exact List.any_eq_true.mpr ⟨x, hx, (refinesB_iff x e).mpr hr⟩

/-- Definition 31's `ψ_C`, computably: `D ∩ C ≠ ∅`. -/
def psiB (C D : List Reason) : Bool :=
  D.any (fun r => C.contains r)

/-! ## The three shipped verbs, computably -/

def rejectDenyB (e : Effect) (S : List Effect) : Bool := firesB e S

def rejectDenyUnknownB (e : Effect) (C : List Reason) (S : List Effect) (D : List Reason) : Bool :=
  firesB e S || psiB C D

def rejectPureB (S : List Effect) : Bool := !S.isEmpty

/-- `rejectDenyB` decides `rejectDeny`. The other two follow the same shape; this is the one whose
    predicate is non-trivial. -/
theorem rejectDenyB_iff (e : Effect) (S : List Effect) (D : List Reason) :
    rejectDenyB e S = true ↔ rejectDeny e ⟨fun x => x ∈ S, fun r => r ∈ D⟩ := by
  simpa [rejectDenyB, rejectDeny] using firesB_iff e S

theorem rejectPureB_iff (S : List Effect) (D : List Reason) :
    rejectPureB S = true ↔ rejectPure ⟨fun x => x ∈ S, fun r => r ∈ D⟩ := by
  constructor
  · intro h
    cases S with
    | nil => simp [rejectPureB] at h
    | cons a t => exact ⟨a, by simp⟩
  · rintro ⟨e, he⟩
    cases S with
    | nil => cases he
    | cons a t => simp [rejectPureB]

/-! ## Enumeration — every signature in the vocabulary

    Subsets as lists, so the whole lattice can be walked and emitted. `2^11 × 2^6 = 131 072` signatures;
    the emitter below samples the verb axis rather than the signature axis, because a disagreement in
    these predicates is pointwise and shows up on small sets. -/

def subsets {α : Type} : List α → List (List α)
  | [] => [[]]
  | a :: t => let r := subsets t; r ++ r.map (a :: ·)

/-- Bare names matching `reference/policy_model.py`'s `E` and `R` strings exactly — the differential joins
    on these, so a mismatch here would show up as a spurious disagreement rather than a real one. -/
def Effect.name : Effect → String
  | .Clipboard => "Clipboard" | .Clock => "Clock" | .Db => "Db" | .Env => "Env"
  | .Exec => "Exec" | .Fs => "Fs" | .Ipc => "Ipc" | .Llm => "Llm"
  | .Log => "Log" | .Net => "Net" | .Rand => "Rand"

def Reason.name : Reason → String
  | .reflect => "reflect" | .dispatch => "dispatch" | .indirect => "indirect"
  | .native => "native" | .unresolved => "unresolved" | .setup => "setup"

/-- A row of the decision table: verb, its effect argument, the verb's reason-scope `C`, then the
    signature `(S, D)` and the verdict. Emitted as TSV for the differential against
    `reference/policy_model.py`. An empty column is the empty set — no name is ever the empty string.

    The `C` axis is emitted rather than fixed at `R`, because `deny e Unknown[C]` with a PROPER `C` is the
    ⟨0.19⟩ reason-scoping rung, and a differential that only ever passed the full `R` would agree with a
    Python `psi` that ignored its argument entirely. -/
def emitRows : List String := Id.run do
  let mut out : List String := []
  let effSubsets := (subsets Effect.all).filter (fun l => l.length ≤ 2)
  let rsnSubsets := (subsets Reason.all).filter (fun l => l.length ≤ 2)
  -- ∅, each singleton, and the full R: enough to separate "ψ ignores C" from "ψ intersects with C".
  let cScopes := [] :: Reason.all :: Reason.all.map (fun r => [r])
  for S in effSubsets do
    for D in rsnSubsets do
      let sName := String.intercalate "," (S.map Effect.name)
      let dName := String.intercalate "," (D.map Reason.name)
      out := s!"pure\t\t\t{sName}\t{dName}\t{rejectPureB S}" :: out
      for e in Effect.all do
        out := s!"deny\t{e.name}\t\t{sName}\t{dName}\t{rejectDenyB e S}" :: out
        for C in cScopes do
          let cName := String.intercalate "," (C.map Reason.name)
          out := s!"deny_unknown\t{e.name}\t{cName}\t{sName}\t{dName}\t{rejectDenyUnknownB e C S D}" :: out
  return out.reverse

end Candor
