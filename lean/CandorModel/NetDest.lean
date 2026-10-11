/-
  THE `Net` DESTINATION CLASS — the first carrier beyond `L` (LEAN-CHECKER-PLAN.md Phase 2(a)).

  SPEC §6.2 ⟨0.21⟩: in a `deny`, the `Net` token MAY carry a bracketed destination-class filter —
  `deny Net[unknown-host]` denies the `Net` part only for a function whose `Net` reaches a host of one of the
  listed classes; a concrete effect in the same rule is unaffected; bare `Net` and `Net[*]` mean all
  destinations. The datum is the per-entry `netClass` array (SPEC §2), which is the TRANSITIVE destination
  surface and is read as given — the gate never re-derives it (§3.1).

  So the signature grows a third component, `N ⊆ {known-telemetry, known-partner, unknown-host}`, and the
  `deny` verb becomes a RULE: plain effect tokens, an optional destination-filtered `Net` part, and an
  optional `Unknown[C]` part, fired as their disjunction. PART 97's lattice arm judged one-token rules only;
  this is the predicate for the whole `deny` body (scope aside — scope matching is not modelled, see the plan).

  What is PROVED here:
    · `lemma2_rule` — Lemma 2 on the new carrier: every rule is upward-closed in (S, D, N).
    · `rule_mono_netFilter` — widening a destination filter can only add rejections (the filter axis is
      monotone, which is what makes `Net[*]` the top of it).
    · `fullFilter_iff_bare` — on a reachable, netClass-well-formed entry, `Net[all three classes]` and bare
      `Net` are the same predicate. Off well-formedness they are not (`fullFilter_ne_bare_off_wf`).
    · the ⟨0.24⟩ ANSWERABILITY rule applied to an absent `netClass`: an answered verdict agrees with EVERY
      well-formed completion; a refusal could have fired; and the refusal is minimal EXACTLY when the filter
      omits some class — with the full filter, SPEC's text refuses a question every completion answers the
      same way (`refuse_overbroad_when_filter_full`). That last one is a statement about SPEC's wording, not
      an engine defect: all four engines refuse there, as the text says.
-/
import CandorModel.Exec

namespace Candor

/-- SPEC §6.2's closed destination-class vocabulary. -/
inductive NetClass where
  | knownTelemetry | knownPartner | unknownHost
  deriving DecidableEq, Repr

abbrev NSet := NetClass → Prop

/-- The carrier beyond `L`: a signature plus the entry's destination-class set. -/
structure NSig where
  σ : Sig
  N : NSet

/-- Componentwise plain subset, as Definition 7, extended to the third component. -/
def NSig.le (a b : NSig) : Prop := a.σ ⊑ b.σ ∧ Generic.gsub a.N b.N

/-- A `deny` rule's body, scope aside. `effs` are the plain tokens (a bare `Net`/`Net[*]` lives here);
    `net = some C` is a destination-filtered `Net[C]` part; `unk = some C` is `Unknown[C]` (bare `Unknown`
    is `C` true everywhere). -/
structure Rule where
  effs : ESet
  net  : Option NSet
  unk  : Option RSet

def effPart (ρ : Rule) (x : NSig) : Prop := ∃ e, ρ.effs e ∧ fires e x.σ.S

def netPart : Option NSet → NSig → Prop
  | none,   _ => False
  | some C, x => fires Effect.Net x.σ.S ∧ ∃ c, C c ∧ x.N c

def unkPart : Option RSet → NSig → Prop
  | none,   _ => False
  | some C, x => ∃ r, x.σ.D r ∧ C r

/-- SPEC §6.2 `deny` with a destination-class filter: the disjunction of its parts. -/
def rejectRule (ρ : Rule) (x : NSig) : Prop := effPart ρ x ∨ netPart ρ.net x ∨ unkPart ρ.unk x

/-- **Lemma 2 on the extended carrier.** Every `deny` rule — destination filter and reason scope included —
    is upward-closed in `(S, D, N)`. A newly-determined effect, a newly-disclosed reason, or a newly-reached
    destination class can only move a verdict toward red. -/
theorem lemma2_rule (ρ : Rule) : ∀ a b : NSig, a.le b → rejectRule ρ a → rejectRule ρ b := by
  rintro a b ⟨⟨hS, hD⟩, hN⟩ h
  obtain ⟨effs, net, unk⟩ := ρ
  rcases h with ⟨e, he, hf⟩ | hn | hu
  · exact Or.inl ⟨e, he, fires_mono hS hf⟩
  · cases net with
    | none => exact hn.elim
    | some C =>
      obtain ⟨hf, c, hc, hNc⟩ := hn
      exact Or.inr (Or.inl ⟨fires_mono hS hf, c, hc, hN c hNc⟩)
  · cases unk with
    | none => exact hu.elim
    | some C =>
      obtain ⟨r, hr, hC⟩ := hu
      exact Or.inr (Or.inr ⟨r, hD r hr, hC⟩)

/-- **The filter axis is monotone.** Widening `Net[C]` to `Net[C']` (`C ⊆ C'`) can only add rejections —
    so `Net[*]`, all destinations, is the strictest filter, and a narrowing is exactly as safe as the
    classes it drops. -/
theorem rule_mono_netFilter (effs : ESet) (unk : Option RSet) {C C' : NSet} (h : Generic.gsub C C')
    (x : NSig) : rejectRule ⟨effs, some C, unk⟩ x → rejectRule ⟨effs, some C', unk⟩ x := by
  rintro (he | ⟨hf, c, hc, hNc⟩ | hu)
  · exact Or.inl he
  · exact Or.inr (Or.inl ⟨hf, c, h c hc, hNc⟩)
  · exact Or.inr (Or.inr hu)

/-- `netClass` well-formedness (SPEC §3.1: *"`netClass` is emitted for every `Net`-bearing entry and is
    floored at `unknown-host`"*): a `Net`-bearing entry carries at least one class. A PRODUCER-side
    property of a well-formed report: `netClass` is OPTIONAL on the wire (SPEC §2), so the gate may not
    assume it — which is why an absent datum is refused rather than completed. -/
def NetWF (x : NSig) : Prop := x.σ.S Effect.Net → ∃ c, x.N c

/-- **`Net[known-telemetry,known-partner,unknown-host]` IS bare `Net`** on a reachable, well-formed entry. -/
theorem fullFilter_iff_bare (x : NSig) (hR : Reachable x.σ) (hW : NetWF x) :
    netPart (some (fun _ => True)) x ↔ fires Effect.Net x.σ.S := by
  constructor
  · rintro ⟨hf, _⟩; exact hf
  · intro hf
    obtain ⟨c, hc⟩ := hW ((fires_iff_mem_of_reachable Effect.Net hR).mp hf)
    exact ⟨hf, c, trivial, hc⟩

/-- …and the well-formedness hypothesis is load-bearing: a `Net` entry with an EMPTY class set fires bare
    `Net` and not the full filter. That is the shape of the measured ⟨0.24⟩ fail-open (an absent `netClass`
    matched against ∅, exit 0 where bare `deny Net` exits 1), which is why absence is refused, not read as ∅. -/
theorem fullFilter_ne_bare_off_wf :
    let x : NSig := ⟨⟨fun e => e = Effect.Net, fun _ => False⟩, fun _ => False⟩
    fires Effect.Net x.σ.S ∧ ¬ netPart (some (fun _ => True)) x := by
  refine ⟨⟨Effect.Net, rfl, Refines.refl _⟩, ?_⟩
  rintro ⟨_, c, _, hc⟩; exact hc

/-! ## The computable face, and the bridge -/

def NetClass.all : List NetClass := [.knownTelemetry, .knownPartner, .unknownHost]

theorem NetClass.all_complete : ∀ c : NetClass, c ∈ NetClass.all := by
  intro c; cases c <;> decide

def NetClass.name : NetClass → String
  | .knownTelemetry => "known-telemetry" | .knownPartner => "known-partner" | .unknownHost => "unknown-host"

structure RuleB where
  effs : List Effect
  net  : Option (List NetClass)
  unk  : Option (List Reason)

def RuleB.toRule (ρ : RuleB) : Rule :=
  ⟨fun e => e ∈ ρ.effs, ρ.net.map (fun C c => c ∈ C), ρ.unk.map (fun C r => r ∈ C)⟩

def effPartB (ρ : RuleB) (S : List Effect) : Bool := ρ.effs.any (fun e => firesB e S)

def netPartB : Option (List NetClass) → List Effect → List NetClass → Bool
  | none,   _, _ => false
  | some C, S, N => firesB Effect.Net S && N.any (fun c => C.contains c)

def unkPartB : Option (List Reason) → List Reason → Bool
  | none,   _ => false
  | some C, D => psiB C D

def rejectRuleB (ρ : RuleB) (S : List Effect) (D : List Reason) (N : List NetClass) : Bool :=
  effPartB ρ S || netPartB ρ.net S N || unkPartB ρ.unk D

/-- The Bool twin decides the `Prop` rule. -/
theorem rejectRuleB_iff (ρ : RuleB) (S : List Effect) (D : List Reason) (N : List NetClass) :
    rejectRuleB ρ S D N = true ↔
      rejectRule ρ.toRule ⟨⟨fun x => x ∈ S, fun r => r ∈ D⟩, fun c => c ∈ N⟩ := by
  obtain ⟨effs, net, unk⟩ := ρ
  have hE : effPartB ⟨effs, net, unk⟩ S = true ↔
      effPart (RuleB.toRule ⟨effs, net, unk⟩) ⟨⟨fun x => x ∈ S, fun r => r ∈ D⟩, fun c => c ∈ N⟩ := by
    simp only [effPartB, effPart, RuleB.toRule, List.any_eq_true]
    constructor
    · rintro ⟨e, he, hf⟩; exact ⟨e, he, (firesB_iff e S).mp hf⟩
    · rintro ⟨e, he, hf⟩; exact ⟨e, he, (firesB_iff e S).mpr hf⟩
  have hN : netPartB net S N = true ↔
      netPart (RuleB.toRule ⟨effs, net, unk⟩).net ⟨⟨fun x => x ∈ S, fun r => r ∈ D⟩, fun c => c ∈ N⟩ := by
    cases net with
    | none => simp [netPartB, netPart, RuleB.toRule]
    | some C =>
      simp only [netPartB, netPart, RuleB.toRule, Option.map, Bool.and_eq_true, List.any_eq_true,
        List.contains_iff_mem]
      constructor
      · rintro ⟨hf, c, hcN, hcC⟩; exact ⟨(firesB_iff _ S).mp hf, c, hcC, hcN⟩
      · rintro ⟨hf, c, hcC, hcN⟩; exact ⟨(firesB_iff _ S).mpr hf, c, hcN, hcC⟩
  have hU : unkPartB unk D = true ↔
      unkPart (RuleB.toRule ⟨effs, net, unk⟩).unk ⟨⟨fun x => x ∈ S, fun r => r ∈ D⟩, fun c => c ∈ N⟩ := by
    cases unk with
    | none => simp [unkPartB, unkPart, RuleB.toRule]
    | some C =>
      simp only [unkPartB, unkPart, RuleB.toRule, Option.map, psiB, List.any_eq_true,
        List.contains_iff_mem]
  simp only [rejectRuleB, rejectRule, Bool.or_eq_true]
  rw [hE, hN, hU]
  exact or_assoc

/-! ## Answerability over an ABSENT `netClass` (SPEC §3.1 ⟨0.24⟩)

    SPEC §3.1: a class-scoped `deny` whose scoping datum is an absent optional field is unanswerable — but
    the refusal is per (rule, function) and MINIMAL: *"if the classes determinable from the entry ALONE
    already intersect the filter, the rule FIRES … only if it does NOT yet fire, and the missing datum could
    still make it fire, is the question genuinely unanswerable. Refuse that."* For `netClass` the entry
    alone determines no class, so the rule is answered by its OTHER parts or refused. All four engines read
    `netClass: []` on a `Net` entry the same way as an absent key (measured 2026-10-11), and SPEC §3.1 now
    says so (present-and-empty contradicts the producer floor; read as ABSENT, never as ∅); the projection,
    not this function, makes that choice. -/

inductive Answer where
  | reject | pass | refuse
  deriving DecidableEq, Repr

def Answer.name : Answer → String
  | .reject => "reject" | .pass => "pass" | .refuse => "refuse"

def answerAbsentB (ρ : RuleB) (S : List Effect) (D : List Reason) : Answer :=
  if effPartB ρ S || unkPartB ρ.unk D then .reject
  else match ρ.net with
    | none => .pass
    | some C => if firesB Effect.Net S && !C.isEmpty then .refuse else .pass

/-- An ANSWERED reject holds under every completion of the missing `netClass`. -/
theorem answerAbsent_reject_sound (ρ : RuleB) (S : List Effect) (D : List Reason)
    (h : answerAbsentB ρ S D = .reject) (N : List NetClass) : rejectRuleB ρ S D N = true := by
  unfold answerAbsentB at h
  split at h
  · rename_i hr
    simp only [Bool.or_eq_true] at hr
    simp only [rejectRuleB, Bool.or_eq_true]
    rcases hr with hr | hr
    · exact Or.inl (Or.inl hr)
    · exact Or.inr hr
  · split at h <;> (try split at h) <;> cases h

/-- An ANSWERED pass holds under every completion. -/
theorem answerAbsent_pass_sound (ρ : RuleB) (S : List Effect) (D : List Reason)
    (h : answerAbsentB ρ S D = .pass) (N : List NetClass) : rejectRuleB ρ S D N = false := by
  obtain ⟨effs, net, unk⟩ := ρ
  unfold answerAbsentB at h
  split at h
  · cases h
  · rename_i hr
    simp only [Bool.or_eq_true, not_or, Bool.not_eq_true] at hr
    simp only [rejectRuleB, hr.1, hr.2, Bool.false_or, Bool.or_false]
    cases net with
    | none => rfl
    | some C =>
      simp only at h
      split at h
      · cases h
      · rename_i hc
        simp only [netPartB]
        cases hF : firesB Effect.Net S with
        | false => rfl
        | true =>
          cases C with
          | nil => simp
          | cons a t => simp [hF] at hc

/-- A REFUSAL is never gratuitous in one direction: some completion fires the rule (the listed classes
    themselves), so reading the absence as ∅ — the measured fail-open — could only ever err toward a pass. -/
theorem answerAbsent_refuse_could_fire (ρ : RuleB) (S : List Effect) (D : List Reason)
    (h : answerAbsentB ρ S D = .refuse) : ∃ N, N ≠ [] ∧ rejectRuleB ρ S D N = true := by
  obtain ⟨effs, net, unk⟩ := ρ
  unfold answerAbsentB at h
  split at h
  · cases h
  · cases net with
    | none => cases h
    | some C =>
      simp only at h
      split at h
      · rename_i hc
        simp only [Bool.and_eq_true, Bool.not_eq_true'] at hc
        obtain ⟨hF, hne⟩ := hc
        cases C with
        | nil => simp at hne
        | cons a t =>
          refine ⟨[a], by simp, ?_⟩
          simp [rejectRuleB, netPartB, hF]
      · cases h

/-- **The refusal is MINIMAL when the filter omits a class:** a one-class completion outside the filter
    passes, so the absent datum really could change the answer. -/
theorem refuse_minimal_when_filter_proper (effs : List Effect) (C : List NetClass) (unk : Option (List Reason))
    (S : List Effect) (D : List Reason) (h : answerAbsentB ⟨effs, some C, unk⟩ S D = .refuse)
    (c : NetClass) (hc : c ∉ C) : rejectRuleB ⟨effs, some C, unk⟩ S D [c] = false := by
  unfold answerAbsentB at h
  split at h
  · cases h
  · rename_i hr
    simp only [Bool.or_eq_true, not_or, Bool.not_eq_true] at hr
    simp only [rejectRuleB, hr.1, hr.2, Bool.false_or, Bool.or_false, netPartB, List.any_cons,
      List.any_nil, Bool.or_false]
    simp [hc]

/-- **…and OVER-BROAD when the filter names every class.** With `Net[known-telemetry,known-partner,
    unknown-host]` every non-empty completion fires the rule — the vocabulary is CLOSED, so any class a
    producer could write is listed (hypothesis `N ≠ []`, the classifier's `unknown-host` default) — yet the clause as
    written refuses, because "the entry alone" determines no class. The heading's own test — *refuse only
    when the absent datum could change the answer* — would answer it. All four engines follow the text
    (exit 2, measured 2026-10-11), so this is a wording gap in SPEC §3.1, recorded, not an engine defect;
    PART 97 arm D pins the literal text pending an owner ruling. -/
theorem refuse_overbroad_when_filter_full (effs : List Effect) (unk : Option (List Reason))
    (S : List Effect) (D : List Reason)
    (h : answerAbsentB ⟨effs, some NetClass.all, unk⟩ S D = .refuse)
    (N : List NetClass) (hN : N ≠ []) : rejectRuleB ⟨effs, some NetClass.all, unk⟩ S D N = true := by
  unfold answerAbsentB at h
  split at h
  · cases h
  · simp only at h
    split at h
    · rename_i hc
      simp only [Bool.and_eq_true] at hc
      cases N with
      | nil => exact absurd rfl hN
      | cons a t =>
        simp only [rejectRuleB, netPartB, hc.1, Bool.true_and, Bool.or_eq_true, List.any_cons]
        exact Or.inl (Or.inr (Or.inl (List.contains_iff_mem.mpr (NetClass.all_complete a))))
    · cases h

/-! ## Emission — the Net destination-class rows of the decision table -/

/-- The rule axis: every rule shape PART 97's arm D runs, and more. `Net` with a filter never also appears
    bare (that is one token in the grammar, `Net[C]` or `Net`). The empty rule is omitted. -/
def ruleAxis : List RuleB := Id.run do
  let netFilters : List (Option (List NetClass)) := none :: ((subsets NetClass.all).filter (· ≠ [])).map some
  let unks : List (Option (List Reason)) := [none, some Reason.all, some [.dispatch]]
  let mut out : List RuleB := []
  for effs in [[], [Effect.Fs], [Effect.Llm], [Effect.Net]] do
    for net in netFilters do
      for unk in unks do
        let hasNet := effs.contains Effect.Net
        let empty := effs.isEmpty && net.isNone && unk.isNone
        if !(hasNet && net.isSome) && !empty then
          out := ⟨effs, net, unk⟩ :: out
  return out.reverse

private def optName {α : Type} (f : α → String) : Option (List α) → String
  | none => "-"
  | some l => String.intercalate "," (l.map f)

/-- Two row kinds, nine tab-separated columns each:
    `deny_rule  effs net unk S D N verdict reach` — the rule over a present class set `N`;
    `deny_rule_absent effs net unk S D ? answer reach` — §3.1's answer over an absent `netClass`.
    `-` is "no such part"; an empty column is the empty set. `reach` for `deny_rule` is co-emission
    reachability AND `NetWF` both ways (`Net ∈ S ↔ N ≠ ∅`): an entry without `Net` carries no class. -/
def emitNetRows : List String := Id.run do
  let mut out : List String := []
  let effSubsets := (subsets Effect.all).filter (fun l => l.length ≤ 2)
  let rsnSubsets := (subsets Reason.all).filter (fun l => l.length ≤ 1)
  let ncSubsets := subsets NetClass.all
  for ρ in ruleAxis do
    let eName := String.intercalate "," (ρ.effs.map Effect.name)
    let head := s!"{eName}\t{optName NetClass.name ρ.net}\t{optName Reason.name ρ.unk}"
    for S in effSubsets do
      for D in rsnSubsets do
        let sName := String.intercalate "," (S.map Effect.name)
        let dName := String.intercalate "," (D.map Reason.name)
        let rch := reachableB S
        out := s!"deny_rule_absent\t{head}\t{sName}\t{dName}\t?\t{(answerAbsentB ρ S D).name}\t{rch}" :: out
        for N in ncSubsets do
          let nName := String.intercalate "," (N.map NetClass.name)
          let wf := rch && (S.contains Effect.Net == !N.isEmpty)
          out := s!"deny_rule\t{head}\t{sName}\t{dName}\t{nName}\t{rejectRuleB ρ S D N}\t{wf}" :: out
  return out.reverse

end Candor
