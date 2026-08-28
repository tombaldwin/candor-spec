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
run_exitcode_pyvar() {   # $1 label ; $2 varname ; $3 expected-reject-exit-code ; $4.. poison args
                         # (plain args are passed as argv; `--stdin <file>` feeds <file> on stdin instead
                         # and passes any FURTHER args as argv too — the file is explicit per call, not a
                         # shared global, so each leg of a multi-condition checker can carry its own poison)
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
    local stdin_file="$1"; shift
    out="$(python3 "$tmp" "$@" < "$stdin_file" 2>&1)"; rc=$?
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

# ── poison documents, ONE PER CONDITION, never one per checker (BACKLOG.md "B1" 2026-08-28) ─────────────
#
# THE B1 LESSON, why every block below is shaped the way it is: a poison document that violates every
# condition a checker enforces AT ONCE cannot tell you which one did the rejecting. Two reproduced defeats
# (scratch copy, both confirmed to still exit "mutation-gate: OK" against the PRE-FIX version of this
# file before this rewrite):
#   1. VD_PY's `ok0` branch loosened to `d.get("ok") is True` (accepting a MISSING `ok` key as
#      satisfying "ok is false") — undetected because the only VD_PY poison in scope exercised the
#      `norefused` mode, never `ok0`, even though `ok0` is the mode `vd_doc` actually drives 37 times.
#   2. RS_PY_FAILCLOSED's `bool(d.get("unanalyzed"))` loosened to `"unanalyzed" in d` (accepting a forged
#      all-clear `"unanalyzed": []` as fail-closed) — undetected because the single poison document also
#      violated the OTHER two ANDed conditions (`functions != []`, `analyzed.count != 0`), so the exit
#      code stayed 1 (rejected) via those two legs regardless of what the third leg's logic did.
# The fix is not a better poison document, it is MORE of them: for every checker below, each condition it
# enforces gets its OWN document, valid in every OTHER respect the checker would check, isolating that one
# condition. Where a checker collapses multiple conditions into a single ANDed exit branch (RS_PY_FAILCLOSED,
# ZR_PY_HAS_OK), isolating a leg means holding the OTHER legs at their PASSING value in that one document —
# the poison must still look like a real near-miss, not a document that happens to fail everywhere at once.
mkdir -p "$W/doc"

# ---- PART 36 (VD_PY, `vd_doc`) — 9 modes, ALL NINE covered here. Unlike the ANDed checkers below, VD_PY
# checks exactly the modes named in its OWN argv (`for want in sys.argv[2:]`), so isolation falls straight
# out of invoking it with ONE mode at a time — the document only needs to violate that single predicate;
# nothing else is evaluated in that call, so "valid in every other respect" is automatic. Two documents
# cover all nine: an empty object violates ok0/okt/refused/viol/v005/unev:*/zm:* (seven distinct checks,
# each exercised in its OWN separate call below), and two more supply the two modes that require a KEY BE
# PRESENT rather than absent (norefused, nozm).
printf '%s' '{}' > "$W/doc/vd_empty.json"                                             # ok0/okt/refused/viol/v005/unev/zm: each fails on a MISSING key — this is exactly the shape of defeat #1 above (ok0 loosened to accept a missing `ok`)
printf '%s' '{"violations": [], "refused": true}' > "$W/doc/vd_norefused_bad.json"    # norefused: carries the refusal discriminator BESIDE violations
printf '%s' '{"zeroMatch": ["x"]}' > "$W/doc/vd_zm_present.json"                      # nozm: zeroMatch present on what must be a fully-binding verdict

# ---- PART 37 (RS_PY_FAILCLOSED / RS_PY_STREAM_FAILCLOSED) — 3 ANDed legs, one poison per leg, the other
# two legs held at their PASSING value each time. `rs_leg_unanalyzed.json` is the exact document shape
# defeat #2 above needed and never got: functions==[] and analyzed.count==0 (the OTHER two legs pass) with
# unanalyzed==[] (present but empty/falsy) — a forged all-clear that only a checker still calling
# `bool(...)`, not `"unanalyzed" in d`, correctly rejects.
printf '%s' '{"functions": [{"fn": "x"}], "analyzed": {"count": 0}, "unanalyzed": ["x"]}' > "$W/doc/rs_leg_functions.json"    # ONLY `functions == []` violated
printf '%s' '{"functions": [], "analyzed": {"count": 5}, "unanalyzed": ["x"]}'         > "$W/doc/rs_leg_analyzed.json"       # ONLY `analyzed.count == 0` violated
printf '%s' '{"functions": [], "analyzed": {"count": 0}, "unanalyzed": []}'            > "$W/doc/rs_leg_unanalyzed.json"     # ONLY `bool(unanalyzed)` violated — B1's own defeat #2

# ---- PART 38 (ZR_PY_NO_OK / ZR_PY_HAS_OK) — ZR_PY_NO_OK is THREE sequential guards with DISTINCT exit
# codes (1/2/3), so each is already isolated by construction; only exit 2 had a poison before. ZR_PY_HAS_OK
# collapses `isinstance(d,dict) and "ok" in d` into ONE exit branch — the `ok`-absent leg is isolated for
# free (a JSON object trivially satisfies isinstance), but the dict-ness leg needs a document where the
# CONTENT check would pass if dict-ness weren't guarding it: a top-level JSON ARRAY containing the literal
# string "ok" as an element, so `"ok" in d` is True and only `isinstance(d,dict)` is left to catch it.
printf '%s' '[]'                                > "$W/doc/zr_not_a_dict.json"         # ZR_PY_NO_OK leg 1: must be a dict
printf '%s' '{"ok": true, "incomplete": true}'  > "$W/doc/zr_carries_ok.json"          # ZR_PY_NO_OK leg 2: an advisory doc must WITHHOLD ok over a judged-nothing report
printf '%s' '{"foo": "bar"}'                    > "$W/doc/zr_no_marker.json"           # ZR_PY_NO_OK leg 3: must carry at least one judged-nothing marker
printf '%s' '{"incomplete": true}'              > "$W/doc/zr_missing_ok.json"          # ZR_PY_HAS_OK: a gate-route doc must CARRY ok (dict-ness holds, isolates the `ok`-absent leg)
printf '%s' '["ok"]'                            > "$W/doc/zr_ok_not_a_dict.json"       # ZR_PY_HAS_OK: `"ok" in d` would be True here — isolates the dict-ness leg specifically

# ---- PART 39 (CHAN_PY) — `caveat` mode has two sequential legs (judgedNothing shape, then incomplete==true);
# `none` mode is an OR of two keys collapsed into one exit (13) — the ORIGINAL poison here set BOTH keys at
# once, which cannot tell you whether the checker still catches either key ALONE. Two documents replace it.
printf '%s' '{"incomplete": false}'                > "$W/doc/chan_no_caveat.json"       # caveat leg 1: judgedNothing must be a non-empty list (missing here)
printf '%s' '{"judgedNothing": ["x"]}'             > "$W/doc/chan_caveat_incomplete.json" # caveat leg 2: judgedNothing now valid, `incomplete` must still be True (missing here)
printf '%s' '{"incomplete": true}'                 > "$W/doc/chan_leaks_incomplete.json" # none leg 1: `incomplete` ALONE must still trip the leak check
printf '%s' '{"judgedNothing": ["x"]}'             > "$W/doc/chan_leaks_judgednothing.json" # none leg 2: `judgedNothing` ALONE must still trip it (same file as caveat leg 2 content-wise, different call/mode)

# ---- PART 83 (ck83_defect / ck83_control) — ck83_defect independently `bad.append()`s up to 8 conditions
# (3 on the scan doc, 3 on the report doc, 2 on the cross-document key-set diff) and only exits nonzero if
# the list is non-empty; the ORIGINAL poison violated the 3 scan-side conditions simultaneously, which
# masks a regression in any ONE of them behind the other two still firing. Baseline PASSING scan/report
# pair (SGOOD/RGOOD) lets each poison perturb exactly one condition while the rest stay at their correct
# value. `d83_missing` needs an extra harmless key on the scan side (`probe`) because the only two keys
# the scan doc otherwise carries (`ok`, `violations`) are ALSO each independently checked by name — so a
# missing-key poison built from just those two can't be told apart from the `r_ok`/`r_viol` conditions it
# would also trip; `probe` is checked by NO other condition, so its absence on the report side isolates
# the key-set diff alone.
D83_SCOPE='deny Fs poison'
SGOOD='{"ok": true, "violations": []}'
SGOOD2='{"ok": true, "violations": [], "probe": 1}'
RGOOD='{"ok": true, "violations": [], "zeroMatch": ["deny Fs poison"]}'
printf '%s' '{"ok": false, "violations": []}'                                > "$W/doc/d83_s_ok.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_s_ok.report.json"
printf '%s' '{"ok": true, "violations": [{"rule": "X"}]}'                    > "$W/doc/d83_s_viol.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_s_viol.report.json"
printf '%s' '{"ok": true, "violations": [], "zeroMatch": ["already-firing"]}' > "$W/doc/d83_s_zm.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_s_zm.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_ok.scan.json"
printf '%s' '{"ok": false, "violations": [], "zeroMatch": ["deny Fs poison"]}' > "$W/doc/d83_r_ok.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_viol.scan.json"
printf '%s' '{"ok": true, "violations": [{"rule": "X"}], "zeroMatch": ["deny Fs poison"]}' > "$W/doc/d83_r_viol.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_zm.scan.json"
printf '%s' '{"ok": true, "violations": [], "zeroMatch": ["wrong-scope"]}'    > "$W/doc/d83_r_zm.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_extra.scan.json"
printf '%s' '{"ok": true, "violations": [], "zeroMatch": ["deny Fs poison"], "bogus": 1}' > "$W/doc/d83_extra.report.json"
printf '%s' "$SGOOD2"                                                       > "$W/doc/d83_missing.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_missing.report.json"
# ck83_control: 4 independent conditions (byte-equality; ok==false; AS-EFF-006 present; zeroMatch absent).
# The three content conditions are checked ONLY off the scan document, so an identical-bytes pair isolates
# each one in turn; the byte-equality condition itself needs a pair that PARSES the same but is not
# byte-identical (a harmless extra space), so the content checks all still pass and only that leg trips.
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}]}'  > "$W/doc/d83c_byte.scan.json"
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}] }' > "$W/doc/d83c_byte.report.json"
printf '%s' '{"ok": true, "violations": [{"rule": "AS-EFF-006"}]}'   > "$W/doc/d83c_dok.scan.json"
cp "$W/doc/d83c_dok.scan.json" "$W/doc/d83c_dok.report.json"
printf '%s' '{"ok": false, "violations": [{"rule": "OTHER"}]}'       > "$W/doc/d83c_rule.scan.json"
cp "$W/doc/d83c_rule.scan.json" "$W/doc/d83c_rule.report.json"
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}], "zeroMatch": ["x"]}' > "$W/doc/d83c_zm.scan.json"
cp "$W/doc/d83c_zm.scan.json" "$W/doc/d83c_zm.report.json"

# ── run every real checker in scope, once per condition ─────────────────────────────────────────────────
run_failline_bashfunc "PART83/ck83_defect(s_ok)"       ck83_defect  "$RUN_SH" "$W/doc/d83_s_ok.scan.json"   "$W/doc/d83_s_ok.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_viol)"     ck83_defect  "$RUN_SH" "$W/doc/d83_s_viol.scan.json" "$W/doc/d83_s_viol.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_has_zm)"   ck83_defect  "$RUN_SH" "$W/doc/d83_s_zm.scan.json"   "$W/doc/d83_s_zm.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_ok)"       ck83_defect  "$RUN_SH" "$W/doc/d83_r_ok.scan.json"   "$W/doc/d83_r_ok.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_viol)"     ck83_defect  "$RUN_SH" "$W/doc/d83_r_viol.scan.json" "$W/doc/d83_r_viol.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_zm)"       ck83_defect  "$RUN_SH" "$W/doc/d83_r_zm.scan.json"   "$W/doc/d83_r_zm.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(extra_keys)" ck83_defect  "$RUN_SH" "$W/doc/d83_extra.scan.json"  "$W/doc/d83_extra.report.json"  "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(missing_keys)" ck83_defect "$RUN_SH" "$W/doc/d83_missing.scan.json" "$W/doc/d83_missing.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_control(byte-equal)" ck83_control "$RUN_SH" "$W/doc/d83c_byte.scan.json" "$W/doc/d83c_byte.report.json"
run_failline_bashfunc "PART83/ck83_control(ok=false)"   ck83_control "$RUN_SH" "$W/doc/d83c_dok.scan.json"  "$W/doc/d83c_dok.report.json"
run_failline_bashfunc "PART83/ck83_control(AS-EFF-006)" ck83_control "$RUN_SH" "$W/doc/d83c_rule.scan.json" "$W/doc/d83c_rule.report.json"
run_failline_bashfunc "PART83/ck83_control(no-zm)"      ck83_control "$RUN_SH" "$W/doc/d83c_zm.scan.json"   "$W/doc/d83c_zm.report.json"
run_exitcode_pyvar "PART36/VD_PY(ok0)"       VD_PY 1 "$W/doc/vd_empty.json" ok0
run_exitcode_pyvar "PART36/VD_PY(okt)"       VD_PY 1 "$W/doc/vd_empty.json" okt
run_exitcode_pyvar "PART36/VD_PY(refused)"   VD_PY 1 "$W/doc/vd_empty.json" refused
run_exitcode_pyvar "PART36/VD_PY(norefused)" VD_PY 1 "$W/doc/vd_norefused_bad.json" norefused
run_exitcode_pyvar "PART36/VD_PY(viol)"      VD_PY 1 "$W/doc/vd_empty.json" viol
run_exitcode_pyvar "PART36/VD_PY(v005)"      VD_PY 1 "$W/doc/vd_empty.json" v005
run_exitcode_pyvar "PART36/VD_PY(unev)"      VD_PY 1 "$W/doc/vd_empty.json" "unev:deny Clock;deny Frobnicate"
run_exitcode_pyvar "PART36/VD_PY(zm)"        VD_PY 1 "$W/doc/vd_empty.json" "zm:$D83_SCOPE"
run_exitcode_pyvar "PART36/VD_PY(nozm)"      VD_PY 1 "$W/doc/vd_zm_present.json" nozm
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(functions)"        RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_functions.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(analyzed)"         RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_analyzed.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(unanalyzed)"       RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_unanalyzed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(functions)"  RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_functions.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(analyzed)"   RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_analyzed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(unanalyzed)" RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_unanalyzed.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(not-a-dict)"  ZR_PY_NO_OK 1 "$W/doc/zr_not_a_dict.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(ok-present)"  ZR_PY_NO_OK 2 "$W/doc/zr_carries_ok.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(no-marker)"   ZR_PY_NO_OK 3 "$W/doc/zr_no_marker.json"
run_exitcode_pyvar "PART38/ZR_PY_HAS_OK(ok-absent)"  ZR_PY_HAS_OK 1 "$W/doc/zr_missing_ok.json"
run_exitcode_pyvar "PART38/ZR_PY_HAS_OK(not-a-dict)" ZR_PY_HAS_OK 1 "$W/doc/zr_ok_not_a_dict.json"
run_exitcode_pyvar "PART39/CHAN_PY(caveat-shape)"      CHAN_PY 11 "$W/doc/chan_no_caveat.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(caveat-incomplete)" CHAN_PY 12 "$W/doc/chan_caveat_incomplete.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(none-incomplete)"      CHAN_PY 13 "$W/doc/chan_leaks_incomplete.json" none
run_exitcode_pyvar "PART39/CHAN_PY(none-judgedNothing)"   CHAN_PY 13 "$W/doc/chan_leaks_judgednothing.json" none

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
