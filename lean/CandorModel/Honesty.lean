/-
  THE HONESTY INVARIANT (PAPER3 §3), AND THE FOUR THINGS IT IS NOT.

  H is the cardinal sin stated as a property: *for every executed analyzed `f` with `inferred(f) = (S, D)`,
  if `D = ∅` then `obs(f) ⊆ S`.* A violation of it (Definition 22) is a false all-clear — the analysis
  committed to having seen everything, and had not.

  It is a one-line definition, and almost everything interesting about it is a boundary. The paper spends
  four remarks on those boundaries, and each is the kind of thing that reads as a caveat and functions as a
  load-bearing design constraint. So this file states H, connects it to Theorem 1, and then mechanises the
  four boundaries as objects:

    · **H alone is worthless** (Remark 4(i)). An analyzer answering `(∅, {r})` everywhere satisfies H
      trivially. So H is not the property to measure; H *jointly with the determined axis* is — the `D = ∅`
      fraction of a run, and the precision of `S` there. A green H over a report that discloses everywhere
      is not evidence of anything.
    · **The restriction to ANALYZED frames is not cosmetic.** Unrestricted, H would assert `obs(f) ⊆ ∅` of a
      library primitive that genuinely issues an effect — false for every program that calls a library.
    · **The per-reason-class residual is real** (Remark 5). A frame disclosing only a benign reason, while
      hiding an undisclosed `dispatch` site that reaches `Net`, passes H vacuously AND passes
      `deny Net Unknown[dispatch]`. Two gates green over an undisclosed `Net`.
    · **Fabrication is outside H** (Definition 16). H constrains the under-report direction only. That is
      not an oversight — it is why `pure` and the deny verbs are upward-closed, and why a fabrication is a
      false-ALARM hazard rather than a false all-clear.

  A NOTE ON THE REACHABILITY RELATION, because the paper flags this trap by name. Definition 19a's
  covered-reached relation (analyzed OR modelled frames between) is NOT Definition 27's single-hop collapse
  (modelled frames only), and the paper warns that substituting one for the other "would reduce Theorem
  1(ii) to depth one and make 'transitive soundness' non-transitive". `ExecReaches` is the reflexive
  TRANSITIVE closure of the collapsed edge, which is what recovers covered-reached between analyzed frames:
  decompose a covered chain at each analyzed frame and every consecutive pair has only modelled frames
  between it. That decomposition is an argument about stacks, which this development does not model — it is
  a stated modelling assumption, not a theorem, and saying so is the point of this paragraph.
-/
import CandorModel.Theorem1

namespace Candor.Honesty

open Candor Candor.Generic Candor.Chain Candor.Soundness

variable {V E R : Type}

/-- **Definition 20 (transitively-charged set).** The `obs` of every analyzed frame covered-reached from
    `f`. "Reached from `f`" is reflexive, so `obs(f) ⊆ charged(f)` — which is what makes the `h = f`
    instance of Theorem 1(ii) yield H. -/
def charged (ρ : Run V E R) (f : V) (e : E) : Prop :=
  ∃ h, ExecReaches ρ f h ∧ ρ.analyzed h ∧ ρ.obs h e

theorem obs_sub_charged (ρ : Run V E R) (f : V) (hf : ρ.analyzed f) :
    gsub (ρ.obs f) (charged ρ f) :=
  fun _ ho => ⟨f, ExecReaches.refl f, hf, ho⟩

/-- **Definition 21 (Honesty invariant H).** Containment read modulo `⊑ₑ` per Definition 3 — an observed
    `Llm` against a declared `Net` is not a violation. Vacuous wherever `D ≠ ∅`, by construction. -/
def H (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R) : Prop :=
  ∀ f, ρ.analyzed f → Dempty g f → ∀ e, ρ.obs f e → gcovered ref e (T g f).S

/-- **H⁺**, the transitive strengthening — the form the runtime oracle actually checks. Written as
    "`D(f) ≠ ∅` OR `charged(f) ⊆ S(f)`" rather than by unioning a pseudo-effect `{Unknown}` into a subset of
    `E`, which would put `Unknown` on the effect lattice and undo Remark 1. -/
def Hplus (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R) : Prop :=
  ∀ f, ρ.analyzed f → Dempty g f → ∀ e, charged ρ f e → gcovered ref e (T g f).S

/-- **Definition 22 (Violation).** An executed analyzed `f` with `D(f) = ∅` whose observation escapes its
    declared set. This is the false all-clear, and the thing every engine fix in this family has been
    about. -/
def Violation (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R) (f : V) : Prop :=
  ρ.analyzed f ∧ Dempty g f ∧ ∃ e, ρ.obs f e ∧ ¬ gcovered ref e (T g f).S

/-- "H says there are none" — as a theorem rather than as a gloss.

    ONE DIRECTION ONLY, and the omission is deliberate rather than an oversight. The converse — no
    violations implies H — is true but needs excluded middle: from `¬∃ e, obs e ∧ ¬covered e` you reach
    `∀ e, obs e → covered e` only through double-negation elimination. It would be the single theorem in
    this development depending on `Classical.choice`, and it carries nothing: a violation is *defined* as a
    witness to H's failure, so the converse is unfolding, not content. The direction below is the one that
    means something — if the invariant holds, no run exhibits a false all-clear. -/
theorem no_violation_of_H (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    (h : H ref g ρ) : ∀ f, ¬ Violation ref g ρ f := by
  rintro f ⟨hf, hD, e, ho, hn⟩
  exact hn (h f hf hD e ho)

/-- **H⁺ implies H**, because reachability is reflexive. The paper's "`obs(f) ⊆ charged(f)`, which is what
    makes the `h = f` instance of Theorem 1(ii) yield H". -/
theorem H_of_Hplus (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R) (h : Hplus ref g ρ) :
    H ref g ρ :=
  fun f hf hD e ho => h f hf hD e (obs_sub_charged ρ f hf e ho)

/-- **(A2) and (A3) imply H⁺** — the bridge from §4's antecedents back to §3's invariant. This is the whole
    reason the antecedents are worth decomposing: they are individually checkable, and between them they
    buy the property the family is actually selling. -/
theorem Hplus_of_A2_A3 (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    (hA2 : A2 ref g ρ) (hA3 : A3 g ρ) : Hplus ref g ρ := by
  rintro f _ hD e ⟨h, hr, hh, ho⟩
  exact thm1_ii ref g ρ hA2 hA3 hD hr hh ho

theorem H_of_A2_A3 (ref : E → E → Prop) (g : Graph V E R) (ρ : Run V E R)
    (hA2 : A2 ref g ρ) (hA3 : A3 g ρ) : H ref g ρ :=
  H_of_Hplus ref g ρ (Hplus_of_A2_A3 ref g ρ hA2 hA3)

end Candor.Honesty

/-! ## The four boundaries, as objects -/

namespace Candor.Honesty.Boundaries

open Candor Candor.Generic Candor.Chain Candor.Soundness Candor.Honesty

private inductive U where
  | f | lib
  deriving DecidableEq

/-! ### 1. H alone is worthless (Remark 4(i))

    An analyzer that answers `(∅, {r})` everywhere satisfies H trivially, because H is vacuous on every
    `D ≠ ∅` frame. So a green H is not evidence: the object of interest is H **jointly** with the determined
    axis — the `D = ∅` fraction of a run, and the precision of `S` there.

    This is the same shape as the (A0) hollowness witness one file over, and it is the reason the syscall
    oracle reports a `D = ∅` denominator rather than a pass rate. -/

/-- Discloses `unresolved` everywhere, determines nothing. -/
private def gAllUnknown : Graph U Effect Reason :=
  ⟨fun _ => ⟨fun _ => False, fun r => r = Reason.unresolved⟩, fun _ _ => False⟩

private def runAny : Run U Effect Reason where
  analyzed := fun _ => True
  rawCall := fun _ _ => False
  execCall := fun _ _ => False
  obs := fun _ e => e = Effect.Net
  execCall_analyzed := fun _ _ _ => ⟨trivial, trivial⟩

/-- **H holds, and says nothing.** Every frame issues `Net`, no frame determines anything, and the
    invariant is satisfied — vacuously, everywhere, because no frame has `D = ∅`. -/
theorem H_is_trivial_under_total_disclosure :
    H Refines gAllUnknown runAny ∧ (∀ v : U, runAny.obs v Effect.Net) := by
  refine ⟨?_, fun _ => rfl⟩
  intro f _ hD
  exact absurd (⟨f, Reaches.refl f, rfl⟩ : (T gAllUnknown f).D Reason.unresolved) (hD Reason.unresolved)

/-! ### 2. The restriction to ANALYZED frames is not cosmetic

    A modelled frame carries no signature, so Definition 12's convention gives it `(∅, ∅)`. Unrestricted, H
    would assert `obs(lib) ⊆ ∅` of a library primitive that genuinely issues an effect — false for every
    program that calls a library. Modelled frames are accounted for by charging THROUGH them, never by H
    binding them. -/

private def gModelled : Graph U Effect Reason :=
  ⟨fun _ => ⟨fun _ => False, fun _ => False⟩, fun _ _ => False⟩

/-- `lib` is modelled: covered, but not analyzed, and it issues `Net`. -/
private def runModelled : Run U Effect Reason where
  analyzed := fun v => v = U.f
  rawCall := fun a b => a = U.f ∧ b = U.lib
  execCall := fun _ _ => False
  obs := fun v e => v = U.lib ∧ e = Effect.Net
  execCall_analyzed := fun _ _ h => h.elim

/-- **H holds; the unrestricted form fails.** Dropping `ρ.analyzed f` from H's quantifier makes it assert
    that a modelled primitive with no signature performs nothing. -/
theorem analyzed_restriction_is_load_bearing :
    H Refines gModelled runModelled
    ∧ ¬ (∀ f : U, Dempty gModelled f → ∀ e, runModelled.obs f e →
          gcovered Refines e (T gModelled f).S) := by
  constructor
  · intro f hf _ e ho
    rcases ho with ⟨hs, _⟩
    subst hs
    exact absurd (show U.lib = U.f from hf) (by decide)
  · intro h
    rcases h U.lib (by rintro r ⟨w, _, hd⟩; exact hd) Effect.Net ⟨rfl, rfl⟩ with ⟨e', ⟨w, _, hs⟩, _⟩
    exact hs

/-! ### 3. The per-reason-class residual (Remark 5)

    Because H is vacuous on every `D ≠ ∅` frame, an external observer can falsify WHETHER a frame disclosed,
    but not the per-reason-class CORRECTNESS of what it disclosed. A frame carrying only a benign reason,
    while hiding an undisclosed `dispatch` site that reaches `Net`, passes H vacuously and passes
    `deny Net Unknown[dispatch]` because `dispatch ∉ D`.

    Two gates green over an undisclosed `Net`. This is a residual the model does not close, and stating it
    as a theorem is the difference between a known limitation and a limitation that reads as considered. -/

/-- Discloses `setup` — benign, and true as far as it goes. The `dispatch` site reaching `Net` is not
    disclosed at all, which is an (A1) violation the observer cannot see. -/
private def gBenign : Graph U Effect Reason :=
  ⟨fun _ => ⟨fun _ => False, fun r => r = Reason.setup⟩, fun _ _ => False⟩

private def runHidden : Run U Effect Reason where
  analyzed := fun _ => True
  rawCall := fun _ _ => False
  execCall := fun _ _ => False
  obs := fun v e => v = U.f ∧ e = Effect.Net
  execCall_analyzed := fun _ _ _ => ⟨trivial, trivial⟩

theorem per_reason_class_residual :
    H Refines gBenign runHidden
    ∧ ¬ rejectDenyUnknown Effect.Net (fun r => r = Reason.dispatch) (T gBenign U.f)
    ∧ runHidden.obs U.f Effect.Net := by
  refine ⟨?_, ?_, ⟨rfl, rfl⟩⟩
  · intro f _ hD
    exact absurd (⟨f, Reaches.refl f, rfl⟩ : (T gBenign f).D Reason.setup) (hD Reason.setup)
  · rintro (⟨e', ⟨w, _, hs⟩, _⟩ | ⟨r, ⟨w, _, hd⟩, hc⟩)
    · exact hs
    · exact absurd (hd.symm.trans hc) (by decide)

/-! ### 4. Fabrication is outside H (Definition 16)

    H constrains the under-report direction only, and that is deliberate. A fabrication — growth of `S`
    beyond what any run performs — satisfies H and always will, because H is a containment of `obs` INTO
    `S`. The model gives fabrication no invariant.

    Not an oversight: by Lemma 2 a larger `S` can only move a verdict from green toward red, so a
    fabrication is a false-ALARM hazard that lifts along the call graph, not a false all-clear. Different
    failure, different direction, different instrument — the A/B against real code, not this. -/

private def gFabricated : Graph U Effect Reason :=
  ⟨fun _ => ⟨fun _ => True, fun _ => False⟩, fun _ _ => False⟩

private def runQuiet : Run U Effect Reason where
  analyzed := fun _ => True
  rawCall := fun _ _ => False
  execCall := fun _ _ => False
  obs := fun _ _ => False
  execCall_analyzed := fun _ _ _ => ⟨trivial, trivial⟩

/-- **H holds of a report that charges every function with every effect over a run that does nothing.**
    Perfect honesty, zero precision, and every gate red. -/
theorem fabrication_satisfies_H :
    H Refines gFabricated runQuiet
    ∧ (∀ v : U, ∀ e : Effect, ¬ runQuiet.obs v e)
    ∧ rejectDeny Effect.Net (T gFabricated U.f) := by
  refine ⟨fun _ _ _ _ ho => ho.elim, fun _ _ ho => ho, ?_⟩
  exact ⟨Effect.Net, ⟨U.f, Reaches.refl _, trivial⟩, Refines.refl _⟩

end Candor.Honesty.Boundaries
