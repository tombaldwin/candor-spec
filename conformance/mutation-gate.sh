#!/usr/bin/env bash
# conformance/mutation-gate.sh — proves the release-gating checkers can still FAIL.
#
# THE PROBLEM (measured 2026-08-28, twice in one day, in conformance/run.sh): a checker can silently stop
# asserting anything and still print a clean row. Bash single quotes have no escape mechanism, so a Python
# dict-key literal (`d.get('ok')`) nested inside a `python3 -c '...'` body truncates the script at that
# apostrophe — and the damage is invisible on the PASSING path, because the corrupted line usually lives
# in the message-building/failure branch, which only runs on a real divergence. "0 violations" from a row
# like that is not evidence of a clean codebase; it is evidence of nothing (AGENT-CORPUS-BRIEF.md rule 6).
#
# WHAT THIS GATE DOES. For each checker IN SCOPE (see the CHECKERS table below), it feeds a POISON
# document — one the checker MUST reject — pulled LIVE out of conformance/run.sh (never a frozen copy that
# could silently drift from what actually ships), and requires the checker to reject it LOUDLY: not by
# crashing, not by staying silent, not by exiting 0. Two checker SHAPES are in scope, each held to the
# rejection contract it actually has:
#   - "fail-line" checkers (PART 83's ck83_defect/ck83_control) print a literal `FAIL: ...` line on
#     rejection — that IS their contract, so this gate asserts the literal text.
#   - "exit-code" checkers (PART 36/37/38/39's *_PY predicates) reject via a SPECIFIC nonzero exit code
#     with no literal `FAIL:` text — that is THEIR contract (their calling code in run.sh supplies the
#     human-readable FAIL line), so this gate asserts that SPECIFIC code and the absence of a crash.
# Either way, "rejected" excludes a raw Python traceback: a checker that crashes on poison is exactly as
# broken as one that stays quiet about it (SOUNDNESS-LOG, PART 83: "a checker crash must not masquerade as
# an engine disagreement" — the same rule, one layer down, for the checker itself).
#
# SCOPE (see BOTH task instructions and the report this script's introduction shipped with): the
# RELEASE-GATING parts — verdict, route/sink-equality, disclosure/refusal — not all ~84 parts in
# conformance/run.sh. Covered: PART 36 (verdict document cells), PART 37 (report-sink fail-closed shape),
# PART 38 (zero-rule-policy refusal), PART 39 (report-consuming verb re-discloses the caveat), PART 83
# (the byte-equality quadrant — today's own PART, whose first draft carried this exact bug). NOT covered,
# stated explicitly rather than silently: PART 2/3/12 (other verdict differentials), PART 29/32/34/47/57/
# 59/60/61/62/67/68/69/70/72 (other refusal/disclosure/route-equality rows), and every TIER-2 part. Those
# rows drive real engine binaries rather than taking a document directly (PART 32's zm_probe, for example,
# has no "poison JSON" to feed — its input IS a source fixture scanned by four real toolchains), which is
# a different, larger mutation-testing project; extending this gate to them is future work, not silently
# assumed done here.
#
# THE CONTROL: the gate proves its OWN liveness every run via conformance/canary/cannot-fail.sh, a checker
# DELIBERATELY carrying this exact bug (not a synthetic stand-in for it — see that file's own comment).
# The canary is walked exactly like a real checker, IN THE SAME LOOP, with the SAME poison-feeding
# machinery. The outermost check (bottom of this file) is deliberately trivial to read: the gate's own
# output must be non-empty AND contain the line `BROKEN  canary  cannot-fail`. If the canary is not found
# broken — including if someone "fixes" its quoting later and it starts correctly rejecting poison — the
# gate fails on THAT alone, regardless of what else it found, because that is the one thing that proves
# this run could have caught something.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SH="$HERE/run.sh"
CHECKER_PY="$HERE/../scripts/check_nested_quotes.py"
CANARY_SH="$HERE/canary/cannot-fail.sh"
for f in "$RUN_SH" "$CHECKER_PY" "$CANARY_SH"; do
  [ -f "$f" ] || { echo "FAIL: mutation-gate: required file missing: $f"; exit 1; }
done
W="$(mktemp -d)"
trap 'rm -rf "$W"' EXIT INT TERM

RESULTS=""
KIND="real"   # overridden to "canary" for the one canary call below — read by record(), not passed
              # positionally, so the two runner functions don't need a canary-vs-real branch of their own
record() {   # $1 status(PASS|BROKEN) ; $2 name ; $3.. diagnostic lines
  local status="$1" name="$2"; shift 2
  RESULTS="$RESULTS$status  $KIND  $name
"
  if [ "$#" -gt 0 ]; then
    printf '%s\n' "$@" | sed 's/^/    /'
  fi
}

# ── extraction: pull each checker's CURRENT source straight out of run.sh ───────────────────────────
extract_pyvar() {   # $1 = variable name (e.g. RS_PY_FAILCLOSED)
  python3 "$CHECKER_PY" --extract-var "$1" "$RUN_SH"
}
extract_func() {   # $1 = function name (e.g. ck83_defect) ; $2 = source file ; prints the def to stdout
  awk -v fn="$1" '
    $0 ~ "^" fn "\\(\\) \\{" { printing=1 }
    printing { print }
    printing && /^}/ { exit }
  ' "$2"
}

# ── one runner per checker SHAPE ─────────────────────────────────────────────────────────────────────
# "fail-line": literal `FAIL: ...` on rejection is the checker's own contract (PART 83's convention).
run_failline_bashfunc() {   # $1 label ; $2 funcname ; $3 srcfile ; $4.. poison args
  local label="$1" fn="$2" src="$3"; shift 3
  local defn; defn="$(extract_func "$fn" "$src")"
  if [ -z "$defn" ]; then
    record BROKEN "$label" "could not extract function \`$fn\` from $src — nothing to test"
    return
  fi
  local tmp="$W/$fn.sh"; printf '%s\n' "$defn" > "$tmp"
  local out rc
  out="$( ( source "$tmp"; "$fn" "$@" ) 2>&1 )"; rc=$?
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q '^FAIL:' && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "poison was NOT rejected with a clean FAIL: line (exit=$rc)" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
# "exit-code": rejection is a SPECIFIC nonzero exit, no FAIL: text (the calling bash code in run.sh
# supplies that) — asserting a fixed literal exit code, not merely "nonzero", is deliberate: a checker
# that returns exit 1 for every possible reason (parse error, wrong shape, AND real rejection alike) has
# quietly become as uninformative as one that never fails, even though it still "fails" in the loose sense.
run_exitcode_pyvar() {   # $1 label ; $2 varname ; $3 expected-reject-exit-code ; $4.. poison args (files/stdin marker)
  local label="$1" var="$2" want_rc="$3"; shift 3
  local src; src="$(extract_pyvar "$var")"
  if [ -z "$src" ]; then
    record BROKEN "$label" "could not extract \`$var\` from $RUN_SH — nothing to test"
    return
  fi
  local tmp="$W/$var.py"; printf '%s' "$src" > "$tmp"
  local out rc
  if [ "${1:-}" = "--stdin" ]; then
    shift
    out="$(python3 "$tmp" "$@" < "$STDIN_POISON" 2>&1)"; rc=$?
  else
    out="$(python3 "$tmp" "$@" 2>&1)"; rc=$?
  fi
  if [ "$rc" = "$want_rc" ] && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "poison was NOT rejected with the expected exit $want_rc (got exit=$rc)" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}

# ── poison documents, one per checker, each violating exactly the property that checker exists to pin ──
mkdir -p "$W/doc"
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-999"}], "zeroMatch": ["already firing"]}' > "$W/doc/ck83_defect.scan.json"
printf '%s' '{}' > "$W/doc/ck83_defect.report.json"
printf '%s' '{"a": 1}' > "$W/doc/ck83_control.scan.json"
printf '%s' '{"a": 2}' > "$W/doc/ck83_control.report.json"
printf '%s' '{"refused": true, "violations": []}' > "$W/doc/vd_norefused.json"        # PART 36: carries the refusal discriminator BESIDE violations
printf '%s' '{"functions": [{"fn": "x"}], "analyzed": {"count": 1}, "unanalyzed": []}' > "$W/doc/rs_notfailclosed.json"  # PART 37: none of the three fail-closed conditions hold
printf '%s' '{"ok": true, "incomplete": true}' > "$W/doc/zr_carries_ok.json"          # PART 38: an advisory doc must WITHHOLD ok over a judged-nothing report
printf '%s' '{"incomplete": true}' > "$W/doc/zr_missing_ok.json"                      # PART 38: a gate-route doc must CARRY ok
printf '%s' '{"incomplete": false}' > "$W/doc/chan_no_caveat.json"                    # PART 39: over a Row-1 report, the caveat must be present
printf '%s' '{"incomplete": true, "judgedNothing": ["x"]}' > "$W/doc/chan_leaks.json" # PART 39: over an INTACT report, neither key may appear
STDIN_POISON="$W/doc/rs_notfailclosed.json"

# ── run every real checker in scope ──────────────────────────────────────────────────────────────────
run_failline_bashfunc "PART83/ck83_defect"  ck83_defect  "$RUN_SH" "$W/doc/ck83_defect.scan.json" "$W/doc/ck83_defect.report.json" "deny Fs poison"
run_failline_bashfunc "PART83/ck83_control" ck83_control "$RUN_SH" "$W/doc/ck83_control.scan.json" "$W/doc/ck83_control.report.json"
run_exitcode_pyvar "PART36/VD_PY(norefused)"        VD_PY               1  "$W/doc/vd_norefused.json" norefused
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED"        RS_PY_FAILCLOSED    1  "$W/doc/rs_notfailclosed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED" RS_PY_STREAM_FAILCLOSED 1 --stdin
run_exitcode_pyvar "PART38/ZR_PY_NO_OK"             ZR_PY_NO_OK         2  "$W/doc/zr_carries_ok.json"
run_exitcode_pyvar "PART38/ZR_PY_HAS_OK"            ZR_PY_HAS_OK        1  "$W/doc/zr_missing_ok.json"
run_exitcode_pyvar "PART39/CHAN_PY(caveat)"         CHAN_PY             11 "$W/doc/chan_no_caveat.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(none)"           CHAN_PY             13 "$W/doc/chan_leaks.json" none

# ── run the canary, exactly like a real checker, through the SAME fail-line runner ──────────────────
printf '%s' '{"ok": true}' > "$W/doc/canary.json"
KIND="canary"
run_failline_bashfunc "cannot-fail" cannot_fail_check "$CANARY_SH" "$W/doc/canary.json"
KIND="real"

echo "$RESULTS"

# ── THE OUTERMOST CHECK. Deliberately the simplest thing in this file — see the report this script ────
# shipped with for why: the regress this gate exists to stop only terminates if SOMETHING in the chain is
# trivially verifiable by eye, and everything above this point is complex enough that a bug in it is
# exactly as plausible as a bug in what it's checking. This is not: "the gate's own output is non-empty
# AND contains the one exact line `BROKEN  canary  cannot-fail`." That's it. No JSON, no counting, no
# nested predicate — a human can grep for that string as fast as bash can.
if [ -z "$RESULTS" ]; then
  echo "mutation-gate: FAIL — produced NO output at all. A gate that prints nothing is indistinguishable"
  echo "  from one that never ran; treat this exactly like the canary-missing case below."
  exit 1
fi
if ! printf '%s\n' "$RESULTS" | grep -qx "BROKEN  canary  cannot-fail"; then
  echo "mutation-gate: FAIL — the canary line \"BROKEN  canary  cannot-fail\" is missing (or the canary"
  echo "  now reads PASS). Either way this run could not prove it can detect a broken checker, so nothing"
  echo "  else in this output is trustworthy — including every PASS above. If the canary now reads PASS,"
  echo "  someone corrected its quoting; per this gate's own design that is ALSO an error (a canary that"
  echo "  can pass is no longer a control) — give it a new, deliberately broken body instead of removing"
  echo "  the check."
  exit 1
fi
if printf '%s\n' "$RESULTS" | grep '  real  ' | grep -q '^BROKEN'; then
  echo "mutation-gate: FAIL — at least one real checker did not reject its poison document (see BROKEN"
  echo "  lines above). The canary line proves this run's detection machinery works, so this is a genuine"
  echo "  finding about the checker, not a broken gate."
  exit 1
fi
echo "mutation-gate: OK — every real checker in scope rejected its poison document, and the canary line"
echo "  proves this run could have caught one that didn't."
exit 0
