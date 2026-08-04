/-
  THEOREM 1 (CONDITIONAL TRANSITIVE SOUNDNESS), FROM ITS ANTECEDENTS.

  WHY THIS ONE IS WORTH MECHANISING, AND WHY THE PROOF IS NOT THE REASON.

  The algebra of Theorem 1 is elementary — the paper says so itself: "Granted (A2)–(A3) the inequality is
  elementary; the content of Theorem 1 is the DECOMPOSITION into individually checkable and individually
  attackable hypotheses, plus the localization that buys." And the record agrees. Every cardinal sin this
  family has ever fixed was an (A0)–(A3) violation. Not one was an error in this inequality.

  So the value here is not confidence in the proof. It is that once the theorem is stated in a language
  that will not let a hypothesis be omitted, the guarantee becomes UNSTATABLE without its antecedents. The
  ordinary way to misuse this result is to quote the conclusion — "an empty `D` means the whole reachable
  tree is accounted for" — in a setting where (A0) does not hold. Below, that quotation does not typecheck.

  THE (A0) WITNESS IS THE POINT OF THE FILE. PAPER3's proof says, in prose: "Without it the theorem is true
  but hollow. Suppose the engine silently drops a first-party function `d` from its analyzed set … (i)–(ii)
  hold over a scope THE ENGINE ITSELF CHOSE BY OMISSION." `thm1_holds_but_is_hollow_without_A0` is that
  sentence as a machine-checked object: a run in which (A2) and (A3) hold, `D(f) = ∅`, Theorem 1's
  conclusion holds in full — and a `Net` occurs inside `f`'s dynamic extent while `f`'s signature is empty.
  Nothing is violated. The theorem is simply about a smaller tree than the reader thinks.

  That is the cardinal sin, and it is licensed by a TRUE theorem. Which is exactly why (A0) is stated as a
  precondition on the analyzed set rather than as a runtime hypothesis, and why ⟨0.21⟩'s completeness
  manifest exists at function granularity.

  (A1) IS ABSENT ON PURPOSE, and its absence is checkable by reading the hypotheses below: PAPER3 Remark 7
  states "(A1) does not enter the proof, which uses (A0), (A2), (A3) only". Its job is to make a `D = ∅`
  hypothesis honestly ACHIEVABLE — an unresolved site in `f`'s own body must contribute a reason, so `D = ∅`
  cannot be reached by a silent own-body decline — and to refine blame. A mechanisation that quietly
  assumed it would have hidden that division of labour.
-/
import CandorModel.Chain

namespace Candor.Soundness

open Candor Candor.Generic Candor.Chain

variable {V E R : Type}

/-- What the RUN did, as opposed to what the report says.

    `execCall` is Definition 27's edge — already collapsed to the nearest analyzed ancestor, passing through
    modelled frames only and TERMINATING at an uncovered one. `rawCall` is the runtime edge before that
    collapse; it is carried here so the (A0) witness can say something the collapsed relation cannot,
    namely that a frame really was in `f`'s dynamic extent even though no collapsed edge reaches it.

    `obs h` is Definition 18: the effects charged to `h`, already including those reached through chains of
    modelled frames — which is the load (A2) carries about the library model being transitively closed. -/
structure Run (V E R : Type) where
  analyzed : V → Prop
  rawCall : V → V → Prop
  execCall : V → V → Prop
  obs : V → E → Prop
  /-- Definition 27 quantifies over calls BETWEEN ANALYZED FUNCTIONS. Making that a field rather than a
      side condition is what lets the (A0) witness be built at all: an engine that drops `d` from
      `analyzed` thereby deletes every collapsed edge through `d`, and the deletion is legitimate. -/
  execCall_analyzed : ∀ u v, execCall u v → analyzed u ∧ analyzed v

/-- Reachability along collapsed executed calls — the covered-reached dynamic call tree rooted at `f`. -/
inductive ExecReaches (ρ : Run V E R) : V → V → Prop where
  | refl (v : V) : ExecReaches ρ v v
  | step {u v w : V} : ρ.execCall u v → ExecReaches ρ v w → ExecReaches ρ u w

/-- Reachability along the RAW runtime edges — `f`'s actual dynamic extent, collapse or no collapse. -/
inductive RawReaches (ρ : Run V E R) : V → V → Prop where
  | refl (v : V) : RawReaches ρ v v
  | step {u v w : V} : ρ.rawCall u v → RawReaches ρ v w → RawReaches ρ u w

/-- `D(f) = ∅` — the report discloses no blind spot anywhere in `f`'s transitive reach. Under ⟨0.21⟩ this
    is a positive claim, which is what makes the theorem's conclusion worth anything. -/
def Dempty (g : Graph V E R) (v : V) : Prop := ∀ r, ¬ (T g v).D r

/-- **(A2) direct soundness** (PAPER3 Definition 26). Note the restriction to own-body-complete frames:
    stated over EVERY executed `f`, this would be falsified by a perfectly honest engine, since a correctly
    disclosed unresolved site whose runtime dispatch reaches a modelled effect puts that effect in `obs(f)`
    while `direct(f).S` rightly excludes it. The restricted form is exactly what Theorem 1 consumes.

    THE CONTAINMENT IS `gcovered`, NOT MEMBERSHIP. Definition 3's scope note names `obs(f) ⊆ direct(f).S`
    and Theorem 1 explicitly among the containments read MODULO `⊑ₑ`. My first pass here used plain
    membership, which is not a tidier statement of the same theorem — it is a different one, with a
    stronger hypothesis and a stronger conclusion, and neither implies the paper's. An observed `Llm`
    against a declared `Net` satisfies the paper and fails the plain reading. -/
def A2 (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R) : Prop :=
  ∀ h, ρ.analyzed h → (∀ r, ¬ (g.direct h).D r) → ∀ e, ρ.obs h e → gcovered ref e (g.direct h).S

/-- **(A3) call-graph soundness modulo disclosure** (PAPER3 Definition 27). Either the edge is in the
    report's call graph, or a reason was contributed — the disjunction IS the disclosure discipline. -/
def A3 (g : Graph V E R) (ρ : Run V E R) : Prop :=
  ∀ f h, ρ.execCall f h → g.calls f h ∨ ¬ Dempty g f

/-! ## Theorem 1 -/

/-- **Theorem 1(i).** From an executed analyzed `f` with `D(f) = ∅`, every analyzed `h` in the
    covered-reached dynamic call tree has `D(h) = ∅` and `S(h) ⊆ S(f)`.

    The induction is the paper's, step for step: (A3) gives the edge or a reason; `D(f) = ∅` kills the
    reason; Lemma 1 (`T_callee_le`) carries the containment; the argument repeats at the callee. -/
theorem thm1_i (g : Graph V E R) (ρ : Run V E R) (hA3 : A3 g ρ) :
    ∀ {f h : V}, ExecReaches ρ f h → Dempty g f →
      Dempty g h ∧ gsub (T g h).S (T g f).S := by
  intro f h hr
  induction hr with
  | refl v => exact fun hD => ⟨hD, fun _ x => x⟩
  | step hc _ ih =>
      intro hD
      have hcall := (hA3 _ _ hc).resolve_right (fun hn => hn hD)
      have hle := T_callee_le g hcall
      have hDm : Dempty g _ := fun r hrd => hD r (hle.2 r hrd)
      obtain ⟨h1, h2⟩ := ih hDm
      exact ⟨h1, fun e x => hle.1 e (h2 e x)⟩

/-- **Theorem 1(ii).** Every effect observed at any such `h` is in `S(f)`.

    `Dᵈ(h) ⊆ D(h)` — the step the paper spells out — is here the reflexive case of reachability: `h`'s own
    direct disclosure is part of its transitive one, so `D(h) = ∅` forces `Dᵈ(h) = ∅`, which is precisely
    the class of frames (A2) quantifies over. -/
theorem thm1_ii (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    (hA2 : A2 ref g ρ) (hA3 : A3 g ρ)
    {f h : V} (hD : Dempty g f) (hr : ExecReaches ρ f h) (hh : ρ.analyzed h)
    {e : E} (ho : ρ.obs h e) : gcovered ref e (T g f).S := by
  obtain ⟨hDh, hsub⟩ := thm1_i g ρ hA3 hr hD
  have hdd : ∀ r, ¬ (g.direct h).D r := fun r hrd => hDh r ⟨h, Reaches.refl h, hrd⟩
  have hdirect : gsub (g.direct h).S (T g h).S := fun x hx => ⟨h, Reaches.refl h, hx⟩
  exact gcovered_mono hsub (gcovered_mono hdirect (hA2 h hh hdd e ho))

end Candor.Soundness

/-! ## (A0), and what the theorem is worth without it

    PAPER3's proof of Theorem 1 pauses to say that (A0)'s first conjunct — every executed function is
    covered or envelope-carried — is definitionally true given the trichotomy, and therefore proves nothing.
    The content is the SECOND conjunct: every function of the report's claimed scope is in the analyzed set.

    Here is what its absence costs, as an object rather than as a warning. -/

namespace Candor.Soundness.A0Witness

open Candor Candor.Generic Candor.Chain Candor.Soundness

/-- Three units. `caller` is analyzed and reported pure. `dropped` is a first-party function the engine
    silently omitted from its analyzed set. `sink` performs `Net`, and is reached only through `dropped`. -/
private inductive U where
  | caller | dropped | sink
  deriving DecidableEq

/-- The report: `caller` analyzed, determined-pure, calling nothing. Exactly what an engine emits after
    dropping `dropped` — and under ⟨0.21⟩ that empty entry is a positive claim of purity. -/
private def g : Graph U Effect Reason :=
  ⟨fun _ => ⟨fun _ => False, fun _ => False⟩, fun _ _ => False⟩

/-- The run. The RAW chain `caller → dropped → sink` really happened. The COLLAPSED relation is empty,
    because Definition 27's collapse terminates at an uncovered frame and `dropped` is uncovered — by the
    engine's own omission, which is the whole point. -/
private def ρ : Run U Effect Reason where
  analyzed := fun v => v = U.caller
  rawCall := fun a b => (a = U.caller ∧ b = U.dropped) ∨ (a = U.dropped ∧ b = U.sink)
  execCall := fun _ _ => False
  obs := fun v e => v = U.sink ∧ e = Effect.Net
  execCall_analyzed := fun _ _ h => h.elim

/-- **THE HOLLOWNESS, MACHINE-CHECKED.** Every antecedent the theorem uses holds; its conclusion holds in
    full; `caller` is claimed determined-pure — and a `Net` occurred inside `caller`'s dynamic extent.

    Nothing here is violated. Theorem 1 is simply about a smaller tree than a reader assumes, and the engine
    chose that tree by omission. This is the cardinal sin licensed by a TRUE theorem, which is why (A0) is a
    precondition on the analyzed set rather than a runtime hypothesis, and why discharging it needs a
    completeness manifest at FUNCTION granularity — a `{count, digest}` manifest cannot see this. -/
theorem thm1_holds_but_is_hollow_without_A0 :
    A2 Refines g ρ
    ∧ A3 g ρ
    ∧ Dempty g U.caller
    ∧ (∀ h : U, ∀ e : Effect, ExecReaches ρ U.caller h → ρ.analyzed h → ρ.obs h e →
        gcovered Refines e (T g U.caller).S)
    ∧ RawReaches ρ U.caller U.sink
    ∧ ρ.obs U.sink Effect.Net
    ∧ ¬ gcovered Refines Effect.Net (T g U.caller).S := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · intro h hh _ e ho
    -- the only analyzed frame is `caller`, and `caller` observes nothing
    rcases ho with ⟨hs, _⟩
    subst hs
    exact absurd (show U.sink = U.caller from hh) (by decide)
  · intro _ _ hc
    exact hc.elim
  · rintro r ⟨w, _, hd⟩
    exact hd
  · intro h e hr _ ho
    -- the collapsed tree rooted at `caller` is `{caller}`, and `caller` observes nothing
    cases hr with
    | refl _ => rcases ho with ⟨hs, _⟩; exact absurd hs (by decide)
    | step hc _ => exact hc.elim
  · exact RawReaches.step (Or.inl ⟨rfl, rfl⟩) (RawReaches.step (Or.inr ⟨rfl, rfl⟩) (RawReaches.refl _))
  · exact ⟨rfl, rfl⟩
  · rintro ⟨e', ⟨w, _, hs⟩, _⟩
    exact hs

end Candor.Soundness.A0Witness

/-! ## Non-vacuity, and (A3)

    The (A0) witness above satisfies (A2) and (A3) with an EMPTY call tree, which is exactly what makes it
    a hollowness witness — and exactly why it is not evidence that the theorem says anything. A conditional
    whose hypotheses are only ever satisfied trivially is not a guarantee. So: one run where the antecedents
    hold with a real edge and a real observed effect, and the conclusion has content; and one where (A3)
    genuinely fails and the conclusion fails with it. -/

namespace Candor.Soundness.Control

open Candor Candor.Generic Candor.Chain Candor.Soundness

private inductive W where
  | caller | callee
  deriving DecidableEq

private def directW : W → Sig
  | .caller => ⟨fun _ => False, fun _ => False⟩
  | .callee => ⟨fun e => e = Effect.Net, fun _ => False⟩

/-- The engine RESOLVED the edge. -/
private def gOk : Graph W Effect Reason :=
  ⟨directW, fun a b => a = W.caller ∧ b = W.callee⟩

/-- The engine MISSED the edge, and disclosed nothing — an (A3) violation. Same run, same observation. -/
private def gMiss : Graph W Effect Reason :=
  ⟨directW, fun _ _ => False⟩

private def run : Run W Effect Reason where
  analyzed := fun _ => True
  rawCall := fun a b => a = W.caller ∧ b = W.callee
  execCall := fun a b => a = W.caller ∧ b = W.callee
  obs := fun v e => v = W.callee ∧ e = Effect.Net
  execCall_analyzed := fun _ _ _ => ⟨trivial, trivial⟩

/-- **POSITIVE CONTROL.** Both antecedents hold with a live edge and a live observation, `D(caller) = ∅`,
    and Theorem 1(ii) then puts the observed `Net` in `caller`'s transitive set — where it belongs. Without
    this the two theorems above would be compatible with a model in which nothing is ever reached. -/
theorem thm1_is_not_vacuous :
    A2 Refines gOk run ∧ A3 gOk run ∧ Dempty gOk W.caller
      ∧ ExecReaches run W.caller W.callee
      ∧ run.obs W.callee Effect.Net
      ∧ gcovered Refines Effect.Net (T gOk W.caller).S := by
  have hexec : ExecReaches run W.caller W.callee :=
    ExecReaches.step ⟨rfl, rfl⟩ (ExecReaches.refl _)
  refine ⟨?_, ?_, ?_, hexec, ⟨rfl, rfl⟩, ?_⟩
  · intro h _ _ e ho
    rcases ho with ⟨hs, he⟩
    subst hs; subst he
    exact ⟨Effect.Net, rfl, Refines.refl _⟩
  · intro _ _ hc
    exact Or.inl hc
  · rintro r ⟨w, _, hd⟩
    cases w <;> exact hd
  · exact thm1_ii Refines gOk run (by
      intro h _ _ e ho
      rcases ho with ⟨hs, he⟩
      subst hs; subst he
      exact ⟨Effect.Net, rfl, Refines.refl _⟩) (fun _ _ hc => Or.inl hc)
      (by rintro r ⟨w, _, hd⟩; cases w <;> exact hd) hexec trivial ⟨rfl, rfl⟩

/-- **(A3) IS LOAD-BEARING.** The same run against an engine that missed the edge and disclosed nothing.
    (A3) is false, `D(caller)` is still empty — the report claims completeness it has not earned — and the
    observed `Net` is NOT in `caller`'s set. The theorem is not violated; its hypothesis is.

    This is the cardinal sin as the antecedents see it, and it is why the disjunction in (A3) is the whole
    disclosure discipline: an engine may miss an edge, or it may stay silent, but not both. -/
theorem A3_is_load_bearing :
    ¬ A3 gMiss run
      ∧ Dempty gMiss W.caller
      ∧ run.obs W.callee Effect.Net
      ∧ ¬ gcovered Refines Effect.Net (T gMiss W.caller).S := by
  have hDe : Dempty gMiss W.caller := by
    rintro r ⟨w, hr, hd⟩
    cases hr with
    | refl _ => exact hd
    | step hc _ => exact hc
  refine ⟨?_, hDe, ⟨rfl, rfl⟩, ?_⟩
  · intro hA3
    rcases hA3 W.caller W.callee ⟨rfl, rfl⟩ with hc | hn
    · exact hc
    · exact hn hDe
  · rintro ⟨e', ⟨w, hr, hs⟩, _⟩
    cases hr with
    | refl _ => exact hs
    | step hc _ => exact hc

end Candor.Soundness.Control
