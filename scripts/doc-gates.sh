#!/usr/bin/env bash
# doc-gates.sh — every candor-spec gate that reads DOCUMENTS ONLY, runnable without an engine.
#
# WHY THIS EXISTS, measured 2026-09-17. SPEC ⟨0.39⟩ was written, gated on clause_check.py and
# check_soundness_tables.py, committed and PUSHED — and it left `must_ledger.py` RED, with four
# normative statements unclassified. The clause was correct; the gate that would have caught the
# omission runs at `conformance/run.sh:8782`, i.e. ONLY inside the four-way suite, and the suite
# reads engine WORKING TREES, so it could not be run at all while two engine agents had dirty trees.
#
# That is the whole trap: **the cheap gate for a documents-only change was reachable only through the
# expensive instrument that a documents-only change has no business running.** So the author ran the
# two gates they happened to think of, which is the failure mode `CLAUDE.md` already names for repos
# ("run ITS gates, from a fixed list, not from whatever the report mentioned") — here the fixed list
# existed but did not include must_ledger, because `bin/gates.sh candor-spec` prints CI `run:` steps
# and must_ledger is not one.
#
# None of the gates below builds, invokes, or reads an engine. They are safe to run at any time, on a
# dirty tree, mid-wave, while a conformance run is in flight. Run this after ANY edit to SPEC.md,
# SOUNDNESS.md, or a conformance generator's declarations — and before pushing one.
#
# Deliberately NOT here: probe_check.py (drives engines; it hangs without them) and everything in
# conformance/run.sh. If you changed engine BEHAVIOUR, this script is not sufficient and never was.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE" || exit 2

fail=0
run() {
  local label="$1"; shift
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ $rc -eq 0 ]; then
    printf '  %-28s OK\n' "$label"
  else
    printf '  %-28s FAIL (exit %d)\n' "$label" "$rc"
    printf '%s\n' "$out" | sed 's/^/      /' | head -20
    fail=1
  fi
}

echo "doc-gates — documents only, no engine is built or invoked"
run "must_ledger"          python3 conformance/must_ledger.py
run "clause_check"         python3 conformance/clause_check.py
run "part_declarations"    python3 conformance/part_declarations.py
run "field_audit"          python3 conformance/field_audit.py
run "reanchor_banner"      python3 conformance/reanchor_banner.py
run "rung_ladder"          python3 scripts/rung-ladder-check.py
run "check_soundness_tables" python3 scripts/check_soundness_tables.py
# …AND THE TOOL ITSELF, added 2026-09-25 (SOUNDNESS R640/R641). It had no selftest for its whole life,
# which is how it shipped blind to `|| R524` for twelve days and to `||| R900` / `| **R900** |` for
# four more — the second of those hides a DUPLICATE ROW ID, and the status tool keys its report by id.
# Both tools now share one row-recogniser (`scripts/soundness_row.py`) and both run its case table.
run "check_tables_selftest"  python3 scripts/check_soundness_tables.py --selftest
run "sha_citations"        python3 scripts/sha-citations.py --check
# The STATUS tool gates itself, added 2026-09-21. It is not a document check — it is the instrument that
# prints "THIS is the shipping-defect list" — and for its whole life it read `Not fixed.` as FIXED,
# because CLOSURE matched the word and nothing looked left of it. 43 rows were in the wrong bucket and 32
# were real open defects missing from the list. A tool nobody calibrates is a tool nobody can trust, and
# this one's failure direction was the register's own cardinal sin: under-reporting what is open.
run "soundness_status_selftest" python3 scripts/soundness-status.py --selftest
# PART 92's arm table, added 2026-09-25 (SOUNDNESS R677/R678). Also not a document check — it is the
# conformance part that pins ⟨0.39⟩, and two of its thirteen arms could be satisfied by an engine that
# said NOTHING, one of them added BECAUSE the other did not pin. `--selftest` drives `judge()` and
# RENDERS the fixtures to prove each `hasnt` names an effect the fixture can actually perform; it builds
# nothing and invokes no engine, so it belongs here rather than behind the four-way suite.
run "part92_arm_table"     python3 conformance/gen_chained_dispatch.py --selftest

if [ $fail -eq 0 ]; then
  echo "doc-gates: OK — every documents-only gate passed"
else
  echo "doc-gates: FAILED — see above. Do not push."
fi
exit $fail
