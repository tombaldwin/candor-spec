#!/usr/bin/env bash
# Build the model AND assert the proofs are real.
#
# `lake build` succeeding is necessary and NOT sufficient: a proof closed with `sorry` type-checks and
# proves nothing, which is the Lean-shaped version of a conformance property that cannot fail. So this
# also asserts (a) no `sorry` in the sources, and (b) every headline theorem depends on NO axioms — not
# even Classical.choice, since these proofs are constructive and a new dependency would mean the argument
# quietly changed.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
export PATH="$HOME/.elan/bin:$PATH"
command -v lake >/dev/null || { echo "check: no lean toolchain (elan) — install with elan-init.sh"; exit 2; }

lake build >/tmp/lean-build.txt 2>&1 || { echo "✘ lake build FAILED"; tail -20 /tmp/lean-build.txt; exit 1; }
echo "✔ lake build"

if grep -rn "sorry" CandorModel/ >/dev/null 2>&1; then
  echo "✘ a source contains \`sorry\` — the proof is a placeholder:"; grep -rn "sorry" CandorModel/; exit 1
fi
echo "✔ no \`sorry\`"

# TWO TIERS, because they earn different bars and collapsing them would weaken the strong one.
#
# TIER A — the model's headline theorems. These live in `Lattice.lean`, are pure `Prop`, and are proved by
# case analysis on inductive types. They depend on NO axioms at all, not even `propext`. That is a real
# property worth pinning: a new axiom appearing here means the argument quietly changed shape.
TIER_A="no_fires_net_of_db fires_net_of_llm pure_passes_bare_unknown lemma2_deny lemma2_denyUnknown
        lemma2_pure lemma2_corollary_deny determined_not_below_undetermined undetermined_not_below_determined
        Generic.gfires_mono Generic.gLemma2_deny Generic.gLemma2_denyUnknown Generic.gLemma2_pure
        Generic.gfires_iff_mem_of_reachable refines_gen fires_iff_mem_of_reachable
        fires_ne_mem_off_reachable llm_without_net_unreachable
        Chain.T_fixpoint_le Chain.T_fixpoint_ge Chain.T_least Chain.T_rechain_le Chain.T_rechain_ge
        Chain.T_mono Chain.drop_le_union Chain.drop_only_loosens
        Chain.Witness.union_fires Chain.Witness.drop_passes
        Chain.Witness.deny_passes_under_drop_fires_under_union Chain.T_callee_le
        Counterexample.llm_leModulo_net Counterexample.lemma2_fails_under_leModulo
        Counterexample.llm_not_le_net Counterexample.flat_le_both_ways
        Counterexample.flat_not_antisymm Counterexample.sig_le_antisymm
        Counterexample.flat_confusion_is_observable
        Soundness.thm1_i Soundness.thm1_ii
        Soundness.A0Witness.thm1_holds_but_is_hollow_without_A0
        Soundness.Control.thm1_is_not_vacuous Soundness.Control.A3_is_load_bearing
        Honesty.obs_sub_charged Honesty.no_violation_of_H Honesty.H_of_Hplus
        Honesty.Hplus_of_A2_A3 Honesty.H_of_A2_A3
        Honesty.Boundaries.H_is_trivial_under_total_disclosure
        Honesty.Boundaries.analyzed_restriction_is_load_bearing
        Honesty.Boundaries.per_reason_class_residual
        Honesty.Boundaries.fabrication_satisfies_H
        Escapes.prop6_llm Escapes.prop6_db_witness_is_dead Escapes.escape1_enumeration
        Escapes.escape2_db_is_caught_by_H Escapes.escape2_llm_is_comparable_under_reachability
        Escapes.escape3_determined_to_disclosed Escapes.escape4_reason_class
        Escapes.escapes_are_not_le_moves
        Blame.violation_refutes_A2_at Blame.violation_refutes_A2 Blame.locate_A3_failure
        Blame.located_edge_refutes_A3 Blame.transitive_failure_with_A2_intact_locates_A3
        Blame.Witness.blame_names_the_site
        Frames.chargeTo_spec Frames.nearest_unique Frames.chargeTo_none_no_nearest
        Frames.mem_append_cases Frames.decomposes_of_allCovered Frames.allCovered_of_decomposes"
#
# TIER B — the BRIDGE lemmas, which are what make the emitted decision table the PROVED answer rather than
# a second unverified transcription sitting beside the first. They state `Bool = true ↔ Prop`, so `simp`
# and the `List` lemmas pull in `propext` and `Quot.sound` — Lean's own core axioms, present in essentially
# every non-trivial proof and NOT evidence of anything. What is forbidden here is `sorryAx` (a placeholder
# that proves nothing) and `Classical.choice` (these arguments are constructive; needing choice would mean
# something is being asserted rather than computed).
TIER_B="reachableB_iff Effect.all_complete Reason.all_complete refinesB_iff firesB_iff rejectDenyB_iff rejectPureB_iff"
CORE_OK="propext|Quot.sound"

axioms_of() { { echo "import CandorModel"; echo "open Candor"; for t in $1; do echo "#print axioms $t"; done; } > /tmp/candor-axioms.lean; lake env lean /tmp/candor-axioms.lean 2>&1; }

out="$(axioms_of "$TIER_A")"
bad="$(printf '%s\n' "$out" | grep -v "does not depend on any axioms" || true)"
[ -n "$bad" ] && { echo "✘ tier A: a headline theorem depends on axioms (or failed to print):"; printf '%s\n' "$bad"; exit 1; }
n=$(printf '%s\n' "$out" | grep -c "does not depend on any axioms")
echo "✔ tier A: $n headline theorem(s) proved with NO axiom dependencies"

out="$(axioms_of "$TIER_B")"
# Anything that is neither "no axioms" nor a line whose axiom list is drawn only from the core set.
bad="$(printf '%s\n' "$out" | grep -v "does not depend on any axioms" \
        | grep -vE "^'Candor\.[A-Za-z_.]+' depends on axioms: \[($CORE_OK)(, ($CORE_OK))*\]$" || true)"
[ -n "$bad" ] && { echo "✘ tier B: a bridge lemma depends on more than Lean's core axioms:"; printf '%s\n' "$bad"; exit 1; }
m=$(printf '%s\n' "$out" | grep -c "Candor\.")
echo "✔ tier B: $m bridge lemma(s) proved from at most [$CORE_OK] — no sorryAx, no Classical.choice"

# The proofs above say the Lean model is internally sound. They say NOTHING about the OTHER transcription
# of the same definitions — `reference/policy_model.py`, which conformance PART 23 judges the four engines
# against and which nobody has ever checked. Both errors the model has actually had lived there. So run
# the two against each other on every row before calling this OK.
echo
if ! python3 ../reference/differential_lean_vs_python.py; then
  echo "✘ the Lean model and reference/policy_model.py DISAGREE"; exit 1
fi

echo
echo "lean model: OK"
