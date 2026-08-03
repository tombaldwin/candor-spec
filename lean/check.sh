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

THEOREMS="no_fires_net_of_db fires_net_of_llm pure_passes_bare_unknown lemma2_deny lemma2_denyUnknown
          lemma2_pure lemma2_corollary_deny determined_not_below_undetermined undetermined_not_below_determined"
{ echo "import CandorModel.Lattice"; echo "open Candor"; for t in $THEOREMS; do echo "#print axioms $t"; done; } > /tmp/candor-axioms.lean
out="$(lake env lean /tmp/candor-axioms.lean 2>&1)"
if printf '%s' "$out" | grep -qv "does not depend on any axioms"; then
  bad="$(printf '%s\n' "$out" | grep -v "does not depend on any axioms" || true)"
  [ -n "$bad" ] && { echo "✘ a theorem depends on axioms (or failed to print):"; printf '%s\n' "$bad"; exit 1; }
fi
n=$(printf '%s\n' "$out" | grep -c "does not depend on any axioms")
echo "✔ $n theorem(s) proved with no axiom dependencies"
echo
echo "lean model: OK"
