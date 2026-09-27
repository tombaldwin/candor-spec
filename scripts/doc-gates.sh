#!/usr/bin/env bash
# doc-gates.sh — the candor-spec gates that need no four-way suite. TWO OF THEM ARE NOT DOCUMENTS-ONLY.
#
# SOUNDNESS R643, measured 2026-09-27 — THIS HEADER SAID "every candor-spec gate that reads DOCUMENTS
# ONLY, runnable without an engine" AND IT WAS FALSE, in the direction that matters:
#
#   * `field_audit.py` BUILDS AND INVOKES ENGINES — it runs `candor-scan` and the candor-java jar, and
#     its own refusal says so ("no engine could run — an empty table must never read as agreement").
#     It passed here for its whole life only because the engines HAPPEN to be built on this machine.
#     Two consequences the old header actively hid: this script is NOT safe to run during a conformance
#     run (it reads engine trees, which is the contamination that file documents three times over), and
#     it cannot be dropped into a documents-only CI job.
#   * `sha-citations.py --check` needs the SIBLING REPOS' git history — it answers "does this sha name a
#     commit in ANY family repo" by interrogating each one.
#
# Measured in an isolated candor-spec-only worktree: 10 of 12 gates pass, and exactly those two fail.
# Both now SELF-SKIP with a stated reason when their prerequisite is absent, and this script reports
# INCOMPLETE rather than OK when anything was skipped — green over an unrun gate is the whole hazard.
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
skipped=0
run() {
  local label="$1"; shift
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ $rc -eq 0 ]; then
    printf '  %-28s OK\n' "$label"
  elif [ $rc -eq 3 ]; then
    # The self-skip convention `gate-run.sh` already uses: exit 3 means IT DID NOT RUN and said why.
    # Counted as UNRUN, never as passed — the verdict below goes INCOMPLETE.
    printf '  %-28s SELFSKIP — it did not run:\n' "$label"
    printf '%s\n' "$out" | sed 's/^/      /' | head -6
    skipped=$((skipped+1))
  else
    printf '  %-28s FAIL (exit %d)\n' "$label" "$rc"
    printf '%s\n' "$out" | sed 's/^/      /' | head -20
    fail=1
  fi
}

echo "doc-gates — no four-way suite; field_audit INVOKES ENGINES and sha_citations needs the family"
run "must_ledger"          python3 conformance/must_ledger.py
run "clause_check"         python3 conformance/clause_check.py
run "part_declarations"    python3 conformance/part_declarations.py
# field_audit INVOKES ENGINES (see the header). Its own exit 2 — "no engine could run: an empty table
# must never read as agreement" — is CORRECT and is deliberately not softened; the decision about whether
# to ASK it belongs here instead. Without a built engine this is an unrun gate, not a passing one.
# DOC_GATES_NO_ENGINE=1 forces the skip. This exists because of what the header above establishes: a
# gate that invokes engines READS ENGINE WORKING TREES, so the only safe time to run field_audit is when
# no lane owns an engine — and the engine-presence test below cannot tell "no engine built" from "three
# agents mid-edit with engines built". Measured 2026-09-27: I ran this script four times with three lanes
# holding dirty engine trees before noticing. It passed each time, so nothing was lost; a FAIL would have
# been indistinguishable from a real one, which is the hazard `CLAUDE.md` documents three times over.
if [ -n "${DOC_GATES_NO_ENGINE:-}" ]; then
  printf '  %-28s SELFSKIP — it did not run:\n' "field_audit"
  echo "      DOC_GATES_NO_ENGINE is set. field_audit INVOKES ENGINES and so reads engine working"
  echo "      trees; run it when no lane owns an engine."
  skipped=$((skipped+1))
elif [ -x "$HERE/../candor/target/debug/candor-scan" ] \
   || [ -x "$HERE/../candor-rust/target/debug/candor-scan" ] \
   || ls "$HERE"/../candor-java/build/libs/*-all.jar >/dev/null 2>&1; then
  run "field_audit"        python3 conformance/field_audit.py
else
  printf '  %-28s SELFSKIP — it did not run:\n' "field_audit"
  echo "      no engine binary is built here, and field_audit INVOKES ENGINES. Build one, or run"
  echo "      this gate where the four-way suite runs. Its own exit-2 refusal is correct."
  skipped=$((skipped+1))
fi
run "reanchor_banner"      python3 conformance/reanchor_banner.py
# rung_ladder NEEDS `v0.N` TAGS. It reads `git tag` to tell a released rung from an authored one, and
# refuses when it finds none rather than guessing — which is right, and means a SHALLOW, TAGLESS
# checkout makes it FAIL rather than self-skip. That is R746: it went red in CI on the very commit
# that wired this script into `conformance.yml`, and the workflow now passes `fetch-tags: true`.
run "rung_ladder"          python3 scripts/rung-ladder-check.py
run "check_soundness_tables" python3 scripts/check_soundness_tables.py
# …AND THE TOOL ITSELF, added 2026-09-25 (SOUNDNESS R640/R641). It had no selftest for its whole life,
# which is how it shipped blind to `|| R524` for twelve days and to `||| R900` / `| **R900** |` for
# four more — the second of those hides a DUPLICATE ROW ID, and the status tool keys its report by id.
# Both tools now share one row-recogniser (`scripts/soundness_row.py`) and both run its case table.
run "check_tables_selftest"  python3 scripts/check_soundness_tables.py --selftest
run "sha_citations"        python3 scripts/sha-citations.py --check
# …AND ITS SELFTEST, added 2026-09-27 (SOUNDNESS R643). `sha-citations.py` ran as a gate for its whole
# life with NO selftest and NO fixture — its only input was the live, currently-clean documents, so
# attack B on it was trivial: replace the body with `sys.exit(0)` and every gate it appears in stays
# green. It has two real judgement calls and both were wrong once: the context window that decides a
# `sha1`-introduced token is not a commit citation (first cut too WIDE, suppressing real citations),
# and `ephemeral_citations` returning 0-dead for "could not look" (R639), which made silence read as
# success. Both are pinned, and both cases FAIL when their subject is degraded.
run "sha_citations_selftest" python3 scripts/sha-citations.py --selftest
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

if [ $fail -ne 0 ]; then
  echo "doc-gates: FAILED — see above. Do not push."
elif [ $skipped -ne 0 ]; then
  # SOUNDNESS R643 — this branch is the point of the row. Two of these gates need something a
  # documents-only checkout does not have, and for their whole life they simply went RED there, which
  # is why nine of twelve were in no CI workflow at all. Skipping them is honest; calling the run OK
  # afterwards would not be, and `gate-run.sh` has said INCOMPLETE over an unrun gate since 2026-08-30.
  echo "doc-gates: INCOMPLETE — $skipped gate(s) did not run (see SELFSKIP above). No gate FAILED."
else
  echo "doc-gates: OK — all $(( 12 )) gates ran and passed"
fi
exit $fail
