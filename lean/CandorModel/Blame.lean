/-
  §5 — BLAME. A VIOLATION DOES NOT JUST EXIST; IT NAMES A SITE.

  Theorem 1 says: given the antecedents, no false all-clear. Corollary 1 is the contrapositive with an
  address attached — a run that witnesses a violation refutes a SPECIFIC antecedent at a SPECIFIC place.
  That is the property that makes the decomposition worth having rather than an academic tidiness: an
  engine maintainer gets a site, not a verdict.

  Two cases, and the paper is careful that they are cases of a split on the `direct` form:

    · **Case 1 (own frame).** `D(f) = ∅` and `obs(f) ⊄ S(f)` refutes **(A2)** at `f`. Lemma 1 gives
      `direct(f).S ⊆ S(f)`, so the shortfall pushes down to the direct signature, and `Dᵈ(f) ⊆ D(f) = ∅`
      puts `f` in exactly the class (A2)'s restricted form quantifies over. The mechanism then splits — a
      pure (A2) miss, or an (A1) failure whose undisclosed site let the effect surface — but that is one
      refutation with two mechanisms, not two refuted antecedents.

    · **Case 2 (transitive).** (A2) intact everywhere and the transitive containment still fails: then
      **(A3)** fails at a specific executed collapsed edge, and fails UNDISCLOSED. The paper locates it by a
      least-index argument along the chain, and is explicit about why the index must be chosen on the
      CONJUNCTION (`D(f_k) ≠ ∅` or `S(f_k) ⊄ S(f)`): minimality is what licenses using `D(f_{k-1}) = ∅`
      without assuming the very conclusion Case 2 denies.

  Mechanised, that least-index walk becomes an induction along `ExecReaches` that carries `D = ∅` forward
  and returns the first edge where the disjunction of (A3) fails. The "least index" and the induction are
  the same argument; the induction just cannot forget to check minimality.

  ONE HYPOTHESIS THE PAPER DOES NOT NEED AND THIS DOES: the call graph must be DECIDABLE. Locating the edge
  means deciding, at each step, whether `(f_k, f_{k+1}) ∈ call` — classically free, constructively not. The
  hypothesis is honest rather than a limitation: `call` is a finite computed artifact that the engine
  serializes into the report, so deciding membership is what a consumer literally does. Taking it as a
  hypothesis keeps this file free of `Classical.choice`, and makes the assumption visible.

  (A4) IS CONSUMED HERE AND IS NOT MODELLED. Remark 7a: every domination step reads `inferred` off the
  EMITTED report, while Theorem 1's containments are over the COMPUTED fixpoint. A report that
  mis-serializes its own fixpoint breaks the split with (A1)–(A3) all intact. That is a serialization
  property checked by a different instrument, and nothing below claims it.
-/
import CandorModel.Honesty

namespace Candor.Blame

open Candor Candor.Generic Candor.Chain Candor.Soundness Candor.Honesty

variable {V E R : Type}

/-! ## Case 1 — a violation at `f` refutes (A2) at `f` -/

/-- **Corollary 1, Case 1.** The refutation is *located*: not "some antecedent fails" but "(A2) fails at
    this frame". `Dᵈ(f) ⊆ D(f)` is the reflexive case of reachability, and it is what puts `f` inside the
    restricted class (A2) quantifies over — the restriction that would otherwise make (A2) unfalsifiable
    here. -/
theorem violation_refutes_A2_at (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    {f : V} (hv : Violation ref g ρ f) :
    ¬ (∀ e, ρ.obs f e → gcovered ref e (g.direct f).S) := by
  obtain ⟨_, hD, e, ho, hn⟩ := hv
  intro hA2f
  exact hn (gcovered_mono (fun x hx => ⟨f, Reaches.refl f, hx⟩) (hA2f e ho))

/-- …and therefore refutes (A2) outright. Stated separately because the located form is the useful one and
    the global form is the one a reader expects to see. -/
theorem violation_refutes_A2 (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    {f : V} (hv : Violation ref g ρ f) : ¬ A2 ref g ρ := by
  intro hA2
  have hf := hv.1
  have hD := hv.2.1
  have hdd : ∀ r, ¬ (g.direct f).D r := fun r hrd => hD r ⟨f, Reaches.refl f, hrd⟩
  exact violation_refutes_A2_at ref g ρ hv (fun e ho => hA2 f hf hdd e ho)

/-! ## Case 2 — locating the (A3) failure -/

/-- **Corollary 1, Case 2.** If the transitive conclusion fails somewhere below `f`, then some executed
    collapsed edge on the chain is neither in `call` nor disclosed — and the theorem returns it.

    The induction IS the paper's least-index walk. At each step it either finds the missing edge (and the
    `D = ∅` it carries is precisely the "undisclosed" half of the conclusion) or uses Lemma 1 to push
    `D = ∅` and the containment forward and continues. Minimality is not an extra check here; it is the
    order the induction visits the chain in. -/
theorem locate_A3_failure (g : Graph V E R) (ρ : Run V E R)
    (hdec : ∀ u v, Decidable (g.calls u v)) :
    ∀ {f h : V}, ExecReaches ρ f h → Dempty g f →
      ¬ (Dempty g h ∧ gsub (T g h).S (T g f).S) →
      ∃ u v, ρ.execCall u v ∧ ¬ g.calls u v ∧ Dempty g u := by
  intro f h hr
  induction hr with
  | refl v =>
      intro hD hbad
      exact absurd ⟨hD, fun _ x => x⟩ hbad
  | @step u m w hc _ ih =>
      intro hD hbad
      cases hdec u m with
      | isFalse hn => exact ⟨u, m, hc, hn, hD⟩
      | isTrue hy =>
          have hle := T_callee_le g hy
          have hDm : Dempty g m := fun r hrd => hD r (hle.2 r hrd)
          refine ih hDm ?_
          rintro ⟨h1, h2⟩
          exact hbad ⟨h1, fun e x => hle.1 e (h2 e x)⟩

/-- **The located edge refutes (A3).** Spelled out because "(A3) fails somewhere" and "(A3)'s disjunction
    fails at THIS edge" are different statements, and only the second is blame. -/
theorem located_edge_refutes_A3 (g : Graph V E R) (ρ : Run V E R)
    {u v : V} (hc : ρ.execCall u v) (hn : ¬ g.calls u v) (hD : Dempty g u) : ¬ A3 g ρ := by
  intro hA3
  cases hA3 u v hc with
  | inl h => exact hn h
  | inr h => exact h hD

/-! ## Exhaustiveness

    The two cases cover every violating run. The paper's argument is that a run failing "both" is not a
    third case but Case 1 located at the innermost offending frame. The form below is the operational one:
    with (A2) intact everywhere, a violation forces an (A3) failure — so a maintainer holding a violation
    and a clean (A2) audit knows to look for a missing edge, and where. -/

/-- **Case 2 in the form a maintainer uses it.** (A2) intact everywhere and the TRANSITIVE containment
    failing below `f` forces an (A3) failure at a named edge.

    The hypothesis is `charged(f) ⊄ S(f)`, not `obs(f) ⊄ S(f)` — and the distinction is not pedantic. My
    first version of this used the latter, which makes the statement VACUOUS: by Case 1 a violation at `f`
    already refutes (A2), so "(A2) intact AND a violation at `f`" is a contradictory hypothesis and the
    theorem would have proved anything. Case 2's whole point is the run where every frame's OWN account is
    correct and the transitive sum still escapes. -/
theorem transitive_failure_with_A2_intact_locates_A3 (ref : E → E → Prop)
    (g : Graph V E R) (ρ : Run V E R) (hdec : ∀ u v, Decidable (g.calls u v))
    (hA2 : A2 ref g ρ) {f : V} (hD : Dempty g f)
    {e : E} (hch : charged ρ f e) (hesc : ¬ gcovered ref e (T g f).S) :
    ∃ u v, ρ.execCall u v ∧ ¬ g.calls u v ∧ Dempty g u := by
  obtain ⟨h, hr, hh, ho⟩ := hch
  refine locate_A3_failure g ρ hdec hr hD ?_
  rintro ⟨hDh, hsub⟩
  have hdd : ∀ r, ¬ (g.direct h).D r := fun r hrd => hDh r ⟨h, Reaches.refl h, hrd⟩
  have hdirect : gsub (g.direct h).S (T g h).S := fun x hx => ⟨h, Reaches.refl h, hx⟩
  exact hesc (gcovered_mono hsub (gcovered_mono hdirect (hA2 h hh hdd e ho)))

end Candor.Blame

namespace Candor.Blame.Witness

open Candor Candor.Generic Candor.Chain Candor.Soundness Candor.Blame

private inductive W where
  | caller | callee
  deriving DecidableEq

private def directW : W → Sig
  | .caller => ⟨fun _ => False, fun _ => False⟩
  | .callee => ⟨fun e => e = Effect.Net, fun _ => False⟩

/-- The engine missed the edge and disclosed nothing — the (A3) failure Case 2 localises. -/
private def gMiss : Graph W Effect Reason := ⟨directW, fun _ _ => False⟩

private def run : Run W Effect Reason where
  analyzed := fun _ => True
  rawCall := fun a b => a = W.caller ∧ b = W.callee
  execCall := fun a b => a = W.caller ∧ b = W.callee
  obs := fun v e => v = W.callee ∧ e = Effect.Net
  execCall_analyzed := fun _ _ _ => ⟨trivial, trivial⟩

/-- **Blame lands on the right edge.** The transitive conclusion fails below `caller`, and
    `locate_A3_failure` returns `caller → callee` — the edge the engine actually missed, carrying the
    `D = ∅` that makes it undisclosed. This is what "the counterexample names the site" means. -/
theorem blame_names_the_site :
    ∃ u v, run.execCall u v ∧ ¬ gMiss.calls u v ∧ Dempty gMiss u := by
  refine locate_A3_failure gMiss run (fun _ _ => instDecidableFalse)
    (ExecReaches.step ⟨rfl, rfl⟩ (ExecReaches.refl _))
    (by rintro r ⟨w, hr, hd⟩; cases hr with
        | refl _ => exact hd
        | step hc _ => exact hc) ?_
  rintro ⟨_, hsub⟩
  have : (T gMiss W.caller).S Effect.Net :=
    hsub Effect.Net ⟨W.callee, Reaches.refl _, rfl⟩
  obtain ⟨w, hr, hs⟩ := this
  cases hr with
  | refl _ => exact hs
  | step hc _ => exact hc

end Candor.Blame.Witness
