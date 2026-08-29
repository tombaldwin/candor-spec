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
#
# THREE HARDENING FIXES (2026-08-29, adversarial review of the day this file was written):
#   A3 — the canary's self-proof was DEFEATABLE: `extract_func` matches only the exact literal `^fn() {`
#     on one line, so reformatting the canary's opening brace onto its own line made extraction fail —
#     which was recorded as a BROKEN row with the SAME text the outermost check greps for, making an
#     extraction failure indistinguishable from catching the real bug. Fixed two ways: (1) `require_extracted`
#     turns ANY extraction failure, canary or real checker alike, into an immediate hard FAIL distinct from
#     a BROKEN row; (2) the outermost check now ALSO requires the canary's actual captured output to contain
#     the specific `NameError`/`zeroMatch` text the real bug produces, not just the word BROKEN in a status
#     line built independently of it.
#   A2 — this gate only ever proved a checker REJECTS poison, never that it still ACCEPTS a valid document.
#     A checker degenerated to unconditional rejection (e.g. RS_PY_FAILCLOSED's body loosened to
#     `ok = False`) passed every poison leg while being dead — reproduced against the pre-fix version of
#     this file: all three isolated RS_PY_FAILCLOSED legs read PASS and the gate still printed
#     `mutation-gate: OK`. Fixed by `run_failline_bashfunc_accept`/`run_exitcode_pyvar_accept`: one
#     genuinely valid, checker-specific document per checker/mode, required to be ACCEPTED (accept code,
#     no FAIL line), run under the same "real" KIND so a regression here trips the same outermost check.
#   A4 — the standing nested-quote lint in run.sh scanned ONLY run.sh itself, so this very file and the
#     canary were never linted by it (moved to run.sh; see that file's own comment for the fix and why
#     `*.py` checkers are deliberately NOT included). Also fixed there: scripts/check_nested_quotes.py's
#     `$'\n'`-splice false positive (an ANSI-C-quoted segment was misread as the SAME corruption shape as a
#     real bareword split) — see that script's `_is_safe_variable_interpolation` and `--selftest`.
#
# A SECOND ADVERSARIAL PASS (2026-08-29) found none of A2/A3/A4 above closed the actual gap they were
# aimed at. THE ROOT CAUSE, one sentence: poison documents and accept-known-good documents differed in key
# PRESENCE, not key VALUE, so a checker degraded to presence-only testing passed BOTH halves. Three
# bypasses REPRODUCED with real output against the pre-fix version of this file (mutated source, actual
# exit codes — not analysis):
#   B1 — VD_PY: `vd_empty.json` (`{}`) poisoned SEVEN modes (ok0/okt/refused/viol/v005/unev/zm) by total
#     key absence, and the matching accept-known-good doc for each carried the key with its correct value.
#     Mutating the `ok0` arm to `if want=="ok0" and "ok" not in d: bad.append(...)` — dropping the VALUE
#     comparison entirely — still rejected `{}` (key genuinely absent, so the presence check ALSO fires)
#     and still accepted `{"ok": false}` (key present, so the presence check ALSO stays silent): PASS on
#     both legs, `mutation-gate: OK`, for a checker that no longer inspects the value at all. Fixed by
#     rewriting every affected poison as a NEAR-MISS: same shape a real engine would emit, every key the
#     mode cares about PRESENT, exactly one field's VALUE wrong (`vd_nm_*` fixtures below). `nozm` is left
#     as an absence poison because it is GENUINELY a presence rule — a fully-binding verdict must not carry
#     `zeroMatch` AT ALL, so there is no "wrong value" of a key that should not exist. `refused` is an AND
#     of two conditions (`refused is True`, `violations not in d`) and gets TWO near-miss legs, same as
#     RS_PY_FAILCLOSED's own per-leg treatment below.
#   B2 — ZR_PY_HAS_OK/ZR_PY_NO_OK (PART 38): two DIFFERENT bypasses, both closed by different means.
#     (i) ZR_PY_HAS_OK mutated to `sys.exit(0 if len(d)==2 else 1)` — dropping the isinstance AND key
#     checks — passed every leg, because the three documents in play (`{"incomplete": true}` len 1,
#     `["ok"]` len 1, `{"ok": true, "incomplete": true}` len 2) each happened to land on the side of `==2`
#     that made the mutant's verdict coincide with the real one. This is not a presence/value problem, it
#     is a CARDINALITY problem: any degenerate keyed off `len(d)` slips through when the poison and accept
#     fixtures do not share the same key count. Fixed by padding every fixture in play to the SAME
#     cardinality (`zr_missing_ok.json`/`zr_ok_not_a_dict.json` both padded to 2 keys with a harmless
#     `probe`), so a length-only mutant can no longer distinguish "must reject" from "must accept" by
#     counting. (ii) ZR_PY_NO_OK's 4-key marker OR narrowed to a single `"incomplete" in d` also passed
#     every existing leg — because the ONLY accept-known-good document exercised was one carrying
#     `incomplete`; none of the other three legitimate markers (`judgedNothing`, `noManifest`,
#     `unanalyzed`) had an accept-known-good document of its own, so a narrowing that silently stopped
#     recognizing three of the four had nothing to fail against. Fixed by adding one accept-known-good
#     document PER marker.
#   B3 — the canary's "positive evidence" check (A3 above) greps the canary's PRINTED OUTPUT for
#     `NameError`/`zeroMatch`, which is text, not causation. A `cannot_fail_check` body containing NO
#     nested-quote construct at all — just `echo "Traceback (most recent call last):"; echo "NameError:
#     name 'zeroMatch' is not defined"; exit 1` — satisfies every check in this file (BROKEN row, both
#     substrings present) and made this gate print `mutation-gate: OK`, reproduced against the pre-fix
#     version of this file. Fixed by tying the evidence to the canary's SOURCE, not its output: the
#     extracted `cannot_fail_check` function body is run back through `scripts/check_nested_quotes.py` —
#     the SAME independently-validated parser (cross-checked against `shfmt -tojson`) this gate already
#     depends on for extraction — and the gate now hard-fails unless that lint finds the real
#     multi-segment-single-quote corruption INSIDE the extracted function text. An echo-only fake has zero
#     such findings by construction: there is no inline-interpreter invocation in it at all. Extracting
#     ONLY the named function (not the whole canary file) also means a decoy nested-quote construct planted
#     elsewhere in the file cannot satisfy this on the real function's behalf.
#
# THE SAME COUNTER-ATTACK APPLIED TO THE FOUR CHECKERS NOT NAMED ABOVE (RS_PY_FAILCLOSED/STREAM, CHAN_PY,
# ck83_defect/ck83_control) found three more real, if narrower, gaps and one clean negative:
#   - RS_PY_STREAM_FAILCLOSED's `if not b: sys.exit(2)` empty-stdin guard was UNTESTED — no fixture in this
#     file ever sends empty stdin, so a mutant that deletes the guard entirely passes every existing leg.
#     Fixed: `rs_empty.json` (a genuinely empty file) piped via `--stdin`, expecting exit 2.
#   - CHAN_PY's `if d.get("incomplete") is not True: sys.exit(12)` — mutating `is not True` to `not
#     d.get("incomplete")` (identity to truthiness) passes every existing leg, because every fixture in
#     play only ever set `incomplete` to the JSON literals `true`/absent, never a truthy-but-not-`True`
#     value. Fixed: `chan_caveat_incomplete_truthy.json` sets `incomplete: 1` (truthy, not `True`) beside a
#     VALID `judgedNothing`, isolating the identity check specifically.
#   - ck83_control's byte-equality poison (`d83c_byte.*`) differed by ONE EXTRA SPACE, so it differs in
#     LENGTH as well as content — a mutant checking `len(sb) != len(rb)` instead of `sb != rb` still catches
#     it, by accident. Constructed a genuine same-length, different-BYTES pair (one space swapped for one
#     tab, verified equal `wc -c`) and confirmed the length-based mutant now passes it silently; replaced
#     the fixture with that pair.
#   - ck83_defect's `s_ok is not True`/`r_ok is not True` were attacked the same way as CHAN_PY's
#     (`is not True` → `not x`) and did NOT break: every fixture in play sets `ok` to a JSON boolean
#     (`true`/`false`), and for a plain boolean, identity and truthiness agree — there is no third value in
#     play the way CHAN_PY's `incomplete` can plausibly take one. Verified clean; left unchanged.
#     *** THIS LAST CLAIM WAS WRONG — see the THIRD pass below. Nothing stops a POISON DOCUMENT from using
#     a non-boolean value; the reasoning above mistook "every fixture we happened to write" for "every
#     value the checker could ever see." A verified-clean note is a snapshot of the fixtures on hand, not a
#     proof about the checker (AGENT-CORPUS-BRIEF.md rule 12) — re-attacking it with the missing fixture
#     broke it immediately. ***
#
# A THIRD ADVERSARIAL PASS (2026-08-29) found the B-pass hardening above had the identical shape problem
# ONE LAYER DOWN — the third time in one day this gate's newest fix closed exactly the mutant it was aimed
# at and left an adjacent, same-shape mutant standing. THE ROOT CAUSE, one sentence: every near-miss and
# accept-known-good document B introduced still puts a JSON BOOLEAN behind every `is True`/`is False`
# check, a genuine SUBSET (never a superset) behind every list/set-equality check, and a wholly-wrong
# STRING behind every string-equality check — so a checker degraded from IDENTITY to TRUTHINESS, from
# exact EQUALITY to MEMBERSHIP/SUBSET, or from equality to SUBSTRING, agrees with the real checker on
# every one of them for accidental reasons, and only diverges on a shape B never tried.
#
# FIVE bypasses were handed in, each reproduced with real mutated output against the pre-fix file (the
# mutant passes every existing leg) and each now fixed with the fixture named:
#   A1 — VD_PY `ok0`/`okt`: `is not False`/`is not True` degraded to plain truthiness (`d.get("ok")`/`not
#     d.get("ok")`) passes every B near-miss, because both are JSON booleans and identity/truthiness agree
#     for a boolean. Fixed with a FALSY-but-not-`False` value (`ok: 0`, `vd_falsy_ok0.json`) for `ok0` and
#     a TRUTHY-but-not-`True` value (`ok: 1`, `vd_truthy_okt.json`) for `okt`.
#   A2 — RS_PY_FAILCLOSED/STREAM: `== []`/`== 0` degraded to a falsy check (`not d.get("functions")`/`not
#     (...).get("count")`) passes every existing leg, because both existing poisons are PRESENT-and-truthy
#     wrong values — falsy and `!= []`/`!= 0` agree on a truthy wrong value for the same accidental reason.
#     The divergent case is the key genuinely ABSENT (`None` is falsy but is not `[]` or `0`); fixed with
#     `rs_leg_functions_absent.json`/`rs_leg_count_absent.json`, applied to both the file and stream variant.
#   A3 — CHAN_PY `caveat`: the `isinstance(...,list)` guard dropped from the leg-1 check passes every
#     existing fixture because they are all either a real list or a value that is ALSO falsy (absent). A
#     TRUTHY non-list value (`judgedNothing: "x"`, `chan_caveat_wrongtype.json`) isolates the type check
#     specifically — a real engine bug that serializes the field as a bare string rather than a
#     one-element list is exactly the shape this closes.
#   A4 — ck83_defect `r_zm`: exact list-equality (`r_zm != [scope]`) degraded to membership (`scope not in
#     r_zm`) passes the existing wrong-scope poison (scope genuinely absent either way) but wrongly accepts
#     a SUPERSET — the correct scope present PLUS one extra element. Fixed with `d83_r_zm_extra.json`.
#   A5 — VD_PY `unev`: exact set-equality (`sorted(got)!=sorted(exp)`) degraded to a subset check
#     (`not (set(exp)<=set(got))`) passes the existing missing-rule poison — a SUBSET of the required
#     rules either way — but wrongly accepts a SUPERSET: both required rules present PLUS one extra.
#     Fixed with `vd_superset_unev.json`.
#
# Sweeping every REMAINING mode of all eight checkers — not stopping at the five above, and re-deriving
# the vocabulary (identity, list/set-equality, string-equality, `isinstance`) rather than trusting any
# prior pass's list of what was already tried — found SIX more of the same shape, one of them only on a
# second sweep of this very comment:
#   S1 — VD_PY's other `is True` leg, `refused` (same shape as A1, unhanded): degraded to plain truthiness
#     passes every existing fixture; fixed with `refused: 1` (`vd_truthy_refused.json`).
#   S2 — VD_PY's other exact list-equality leg, `zm` (same shape as A4, unhanded): degraded to membership
#     passes the existing wrong-scope poison but wrongly accepts a superset; fixed with
#     `vd_superset_zm.json`.
#   S3 — ck83_defect `s_ok`/`r_ok`: `is not True` degraded to `not x` passes every existing boolean
#     fixture but wrongly accepts a TRUTHY-but-not-`True` value (`ok: 1`). **This directly CONTRADICTS
#     this file's own prior "verified clean" note (the *** annotation above)** — reproduced live, breaking
#     immediately once the missing fixture was tried. Fixed with `d83_s_ok_truthy.json`/
#     `d83_r_ok_truthy.json`.
#   S4 — ck83_defect `s_viol`/`r_viol` (never previously attacked): `!= []` degraded to plain truthiness
#     passes the existing non-empty-list poison (truthy either way) but wrongly accepts a FALSY-but-not-
#     `[]` value (`violations: ""`). Fixed with `d83_s_viol_falsy.json`/`d83_r_viol_falsy.json`.
#   S5 — ck83_control `d_ok is not False` (same shape as A1/S3, never previously attacked): degraded to
#     `if d_ok:` passes every existing boolean fixture but wrongly accepts a FALSY-but-not-`False` value
#     (`ok: 0`). Fixed with `d83c_ok_falsy.json`.
#   S6 — VD_PY `v005`: string EQUALITY (`v.get("rule")=="AS-EFF-005"`) degraded to substring membership
#     (`"AS-EFF-005" in v.get("rule","")`) passes the existing wrong-rule poison (`"OTHER"` contains no
#     substring match either way) but wrongly accepts `"AS-EFF-0050"`, which CONTAINS the wanted string
#     without being equal to it. Fixed with `vd_v005_substr.json`. **Caught only on a SECOND sweep pass**:
#     the first pass's own draft of this comment claimed `v005` was clean because it has "no boolean/list-
#     equality shape for this class to hide behind" — true, but incomplete, since the class also covers
#     STRING equality degraded to substring, which `v005` has. The lesson inside the lesson: "already
#     swept" is a claim about which shapes were TRIED, not a proof no shape remains.
# ZR_PY_HAS_OK/ZR_PY_NO_OK's `isinstance(d,dict)` guards were attacked the same way as A3 (drop the guard,
# feed a non-dict poison) and did NOT break: `zr_ok_not_a_dict.json`/`zr_not_a_dict.json` already exist as
# poison for exactly this leg and already fail with the WRONG exit code when the guard is dropped
# (`ZR_PY_HAS_OK` exits 0 instead of the wanted 1; `ZR_PY_NO_OK` exits 3 instead of 1) — reproduced live,
# genuinely clean. VD_PY's `viol`/`norefused`/`nozm` legs were re-swept and are deliberately
# presence/truthiness checks with no identity/equality to degrade in the first place.
#
# All ELEVEN reproduced bypasses (A1-A5 handed in, S1-S6 found by the sweep) now make `mutation-gate.sh`
# FAIL against the pre-fix file and pass against the fixed one; the unmodified tree still passes
# `mutation-gate: OK` (canary aside).
#
# THE STRUCTURAL POINT, not just eleven more fixtures: three same-day rounds each closed exactly the
# mutant an adversarial reviewer thought to try and left the next-shaped one standing, because every
# fixture in this file so far has been HAND-AUTHORED against a specific reproduced bypass rather than
# DERIVED from what the checker's own source can distinguish. S6 is evidence for this the hard way: it was
# missed on the FIRST sweep pass through this very comment, whose own note claimed `v005` clean by
# name-checking two shapes without re-deriving the full vocabulary — a human-authored "already swept"
# claim is exactly as easy to under-scope as a human-authored fixture set. A generative alternative — walk
# each checker's extracted source for its comparison shape (`is True`/`is False`, `== <literal>` over a
# bool/number/string, exact list/set equality, `isinstance`) and mechanically emit the canonical near-miss
# family for that shape (truthy-not-True, falsy-not-False, wrong-type, absent-key, superset, subset,
# substring) — would have produced A1-S6 in one pass, and B1-B3/A2/A3/A4 in one pass each before that,
# because the four comparison shapes above are the ENTIRE vocabulary every bypass in this file's history
# has used, and a mechanical walk cannot forget to check one the way a reviewer's memory can. It was not
# built here: the eight checkers in scope are few enough, and change rarely enough, that hand-authoring
# stayed cheaper than building and trusting a new code-reading tool — but a FOURTH round finding a same-
# shape gap should flip that trade, given this is already the third. Until then, the mitigation actually
# applied is a checklist, not a generator: any FUTURE `is True`/`is False`/`==`/list-or-set-equality/
# `isinstance` added to one of these eight checkers must be accompanied by the matching near-miss family
# from the A1-S6 list above, by hand, checked against this comment rather than reinvented — and re-derived
# from the vocabulary, not from what a prior pass happened to try.
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

# ── extraction failure is a HARD ERROR, never a BROKEN row (A3 hardening, 2026-08-29) ──────────────────
# THE BUG THIS CLOSES: `extract_func` (below) matches only the exact literal `^fn() {` on ONE line —
# reformatting the canary's opening brace onto its own line (`cannot_fail_check()\n{`) makes extraction
# fail. Before this fix, a failed extraction was recorded as a BROKEN row with the SAME literal
# `BROKEN  canary  cannot-fail` shape the outermost check (bottom of this file) greps for as proof the
# canary was found broken BY THE INTENDED BUG — so an extraction failure was INDISTINGUISHABLE from
# catching the real NameError, and the gate printed `mutation-gate: OK` either way. That defeats the
# entire point of the canary: it is supposed to prove THIS RUN could have caught a broken checker, not
# merely that something, anything, went wrong. Fix: an extraction failure — for ANY function or variable,
# canary or real checker alike — aborts the whole gate immediately with its own distinct FAIL, so it can
# never masquerade as a canary catching its own bug (or as a real checker rejecting its poison). See
# canary/cannot-fail.sh's own header for why the canary's exact source shape is pinned and must not be
# reformatted; this hardening means a future reformat now fails LOUDLY and DIFFERENTLY instead of quietly
# printing OK.
require_extracted() {   # $1 = extracted text ; $2.. = description for the FAIL line
  if [ -z "$1" ]; then
    shift
    echo "FAIL: mutation-gate: EXTRACTION FAILURE — $*"
    echo "  This is a hard stop, not a BROKEN row: an extraction failure proves nothing about whether the"
    echo "  checker (or the canary) can detect poison, and a prior version of this gate recorded it as a"
    echo "  BROKEN row indistinguishable from the canary's own intended failure (A3 hardening 2026-08-29)."
    exit 1
  fi
}

# ── one runner per checker SHAPE ─────────────────────────────────────────────────────────────────────
# "fail-line": literal `FAIL: ...` on rejection is the checker's own contract (PART 83's convention).
# LAST_RAW_OUT is set on every call (canary and real checkers alike) so a caller — specifically the canary
# call below — can inspect the checker's raw stdout/stderr AFTER record() has filed its PASS/BROKEN row,
# to require POSITIVE evidence of a SPECIFIC failure rather than trusting the row's status alone.
run_failline_bashfunc() {   # $1 label ; $2 funcname ; $3 srcfile ; $4.. poison args
  local label="$1" fn="$2" src="$3"; shift 3
  local defn; defn="$(extract_func "$fn" "$src")"
  require_extracted "$defn" "could not extract function \`$fn\` from $src — nothing to test"
  local tmp="$W/$fn.sh"; printf '%s\n' "$defn" > "$tmp"
  local out rc
  out="$( ( source "$tmp"; "$fn" "$@" ) 2>&1 )"; rc=$?
  LAST_RAW_OUT="$out"
  if [ "$rc" -ne 0 ] && printf '%s\n' "$out" | grep -q '^FAIL:' && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "poison was NOT rejected with a clean FAIL: line (exit=$rc)" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
# accept-known-good counterpart (A2 hardening, 2026-08-29): "rejects poison" is only half of a checker's
# contract — a checker degenerated to unconditional rejection (e.g. `ok = False` with no other logic)
# passes every poison leg above while being dead. Reproduced against the pre-fix gate: mutating
# RS_PY_FAILCLOSED's body to `ok = False` made all three isolated poison legs report PASS, and the overall
# gate still printed `mutation-gate: OK`. Feed the checker a document it MUST accept and require the
# accept code / absence of a FAIL line — a checker that fails this on a genuinely valid document is either
# dead (always-reject) or has drifted from its own documented accept shape, either of which is exactly as
# untrustworthy as never firing on poison.
run_failline_bashfunc_accept() {   # $1 label ; $2 funcname ; $3 srcfile ; $4.. KNOWN-GOOD args
  local label="$1" fn="$2" src="$3"; shift 3
  local defn; defn="$(extract_func "$fn" "$src")"
  require_extracted "$defn" "could not extract function \`$fn\` from $src for accept-check \"$label\""
  local tmp="$W/$fn.accept.sh"; printf '%s\n' "$defn" > "$tmp"
  local out rc
  out="$( ( source "$tmp"; "$fn" "$@" ) 2>&1 )"; rc=$?
  if [ "$rc" -eq 0 ] && ! printf '%s\n' "$out" | grep -q '^FAIL:' && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label (accept-known-good)"
  else
    record BROKEN "$label (accept-known-good)" \
      "a VALID document was REJECTED (exit=$rc) — checker may have degenerated to unconditional-reject" \
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
  require_extracted "$src" "could not extract \`$var\` from $RUN_SH — nothing to test"
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
# accept-known-good counterpart to run_exitcode_pyvar (A2 hardening — see run_failline_bashfunc_accept's
# comment above for the full reproduction). `want_rc` here is the checker's OWN documented accept code
# (0 for every exit-code checker in this file), not the reject code passed to the poison runner.
run_exitcode_pyvar_accept() {   # $1 label ; $2 varname ; $3 accept-exit-code ; $4.. KNOWN-GOOD args
                                 # (supports --stdin like run_exitcode_pyvar, same calling convention)
  local label="$1" var="$2" want_rc="$3"; shift 3
  local src; src="$(extract_pyvar "$var")"
  require_extracted "$src" "could not extract \`$var\` from $RUN_SH for accept-check \"$label\""
  local tmp="$W/$var.accept.py"; printf '%s' "$src" > "$tmp"
  local out rc
  if [ "${1:-}" = "--stdin" ]; then
    shift
    local stdin_file="$1"; shift
    out="$(python3 "$tmp" "$@" < "$stdin_file" 2>&1)"; rc=$?
  else
    out="$(python3 "$tmp" "$@" 2>&1)"; rc=$?
  fi
  if [ "$rc" = "$want_rc" ] && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label (accept-known-good)"
  else
    record BROKEN "$label (accept-known-good)" \
      "a VALID document was NOT accepted (want exit $want_rc, got exit=$rc) — checker may have degenerated to unconditional-reject" \
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
D83_SCOPE='deny Fs poison'   # moved up from the PART 83 block below (C hardening, 2026-08-29) — PART 36's
                             # new `zm` superset poison needs the correct scope literal, and PART 36's
                             # fixtures are built before PART 83's own further down this file.

# ---- PART 36 (VD_PY, `vd_doc`) — 9 modes, ALL NINE covered here. Unlike the ANDed checkers below, VD_PY
# checks exactly the modes named in its OWN argv (`for want in sys.argv[2:]`), so isolation falls straight
# out of invoking it with ONE mode at a time — the document only needs to violate that single predicate;
# nothing else is evaluated in that call, so "valid in every other respect" is automatic.
#
# NEAR-MISS REWRITE (B1 hardening, 2026-08-29 — see this file's header for the reproduced bypass): a total
# key-ABSENCE poison (`{}`) cannot distinguish a checker that inspects a key's VALUE from one degraded to
# checking only whether the key EXISTS — both reject `{}` correctly, for different reasons, and a
# presence-only mutant then also accepts the real accept-known-good document (which carries the key).
# Every mode below except `nozm` therefore gets a document with the key PRESENT and the WRONG value —
# `nozm` is left alone because it is the one mode that is genuinely ABOUT presence (a fully-binding verdict
# must carry no `zeroMatch` key at all; there is no "wrong value" of a key that must not exist), so an
# absence-shaped poison is the correct test for it, not a shortcut.
printf '%s' '{"ok": true, "violations": [{"rule": "AS-EFF-005"}]}' > "$W/doc/vd_nm_ok0.json"       # ok0: `ok` PRESENT, wrong value (true, not false)
printf '%s' '{"ok": false, "violations": []}'                      > "$W/doc/vd_nm_okt.json"        # okt: `ok` PRESENT, wrong value (false, not true)
printf '%s' '{"refused": false}'                                   > "$W/doc/vd_nm_refused1.json"   # refused leg 1 (of the AND): `refused` PRESENT, wrong value (false) — `violations` correctly absent, holding the OTHER leg at its passing value
printf '%s' '{"violations": []}'                                   > "$W/doc/vd_nm_viol.json"        # viol: `violations` PRESENT, wrong value (empty, not non-empty)
printf '%s' '{"violations": [{"rule": "OTHER"}]}'                  > "$W/doc/vd_nm_v005.json"        # v005: `violations` PRESENT and non-empty, wrong RULE value
printf '%s' '{"unevaluated": [{"rule": "deny Clock"}]}'            > "$W/doc/vd_nm_unev.json"        # unev: `unevaluated` PRESENT, wrong (partial) list value — one of the two required rules missing
printf '%s' '{"zeroMatch": ["some-other-scope"]}'                  > "$W/doc/vd_nm_zm.json"          # zm: `zeroMatch` PRESENT, wrong scope value
# `vd_norefused_bad.json` does DOUBLE DUTY: it is norefused's own poison (carries the refusal discriminator
# BESIDE violations, which norefused forbids) AND refused's second AND-leg (refused=True — its correct
# value — but `violations` is present, which that same leg also forbids) — reused rather than duplicated,
# same convention as the ZR_PY_NO_OK/ZR_PY_HAS_OK fixture reuse below.
printf '%s' '{"violations": [], "refused": true}' > "$W/doc/vd_norefused_bad.json"    # norefused poison AND refused-leg-2 poison: carries the refusal discriminator BESIDE violations
printf '%s' '{"zeroMatch": ["x"]}' > "$W/doc/vd_zm_present.json"                      # nozm: zeroMatch present on what must be a fully-binding verdict — the one GENUINELY presence-based mode, verified above, left as an absence poison deliberately

# IDENTITY/EXACTNESS REWRITE (C hardening, 2026-08-29 — see this file's header for all 5 reproduced
# bypasses plus the sweep's own finds): every near-miss document above still only ever puts a JSON
# BOOLEAN behind an `is True`/`is False` check, or a document that is a strict SUBSET of (unev) or
# disjoint from (zm) the correct answer behind a list/set-equality check. A checker degraded from
# IDENTITY to TRUTHINESS (`is not False` → truthy `d.get("ok")`; `is not True` → falsy `not d.get("ok")`)
# rejects every boolean poison above for the SAME reason the real checker does, and a checker degraded
# from exact list/set EQUALITY to membership/subset (`!= [x]` → `x not in`; `sorted(a)!=sorted(b)` →
# `set(exp)<=set(got)`) rejects every existing near-miss for the same accidental reason too — none of them
# is a SUPERSET of the correct answer, which is the one shape only the loosened check would wrongly wave
# through. Five more documents, one per condition, close the gap:
printf '%s' '{"ok": 0, "violations": [{"rule": "AS-EFF-005"}]}' > "$W/doc/vd_falsy_ok0.json"     # ok0: `ok` FALSY but not the literal `False` (0) — is-not-False vs plain truthiness
printf '%s' '{"ok": 1, "violations": []}'                        > "$W/doc/vd_truthy_okt.json"    # okt: `ok` TRUTHY but not the literal `True` (1) — is-not-True vs plain truthiness
printf '%s' '{"refused": 1}'                                     > "$W/doc/vd_truthy_refused.json" # refused leg 1: `refused` TRUTHY but not the literal `True` (1); `violations` correctly absent, holding the other AND-leg passing
printf '%s' '{"unevaluated": [{"rule": "deny Clock"}, {"rule": "deny Frobnicate"}, {"rule": "deny Extra"}]}' > "$W/doc/vd_superset_unev.json" # unev: both required rules present PLUS one extra — exact set-equality vs `set(exp)<=set(got)` subset check
printf '%s' "{\"zeroMatch\": [\"$D83_SCOPE\", \"extra-scope\"]}" > "$W/doc/vd_superset_zm.json"  # zm: correct scope present PLUS one extra — exact list-equality vs membership (`scope in got`)
printf '%s' '{"violations": [{"rule": "AS-EFF-0050"}]}' > "$W/doc/vd_v005_substr.json"           # v005 (sweep find): string EQUALITY (`==`) degraded to substring membership (`in`) — "AS-EFF-0050" contains "AS-EFF-005" as a substring but is not equal to it

# ---- PART 37 (RS_PY_FAILCLOSED / RS_PY_STREAM_FAILCLOSED) — 3 ANDed legs, one poison per leg, the other
# two legs held at their PASSING value each time. `rs_leg_unanalyzed.json` is the exact document shape
# defeat #2 above needed and never got: functions==[] and analyzed.count==0 (the OTHER two legs pass) with
# unanalyzed==[] (present but empty/falsy) — a forged all-clear that only a checker still calling
# `bool(...)`, not `"unanalyzed" in d`, correctly rejects.
printf '%s' '{"functions": [{"fn": "x"}], "analyzed": {"count": 0}, "unanalyzed": ["x"]}' > "$W/doc/rs_leg_functions.json"    # ONLY `functions == []` violated
printf '%s' '{"functions": [], "analyzed": {"count": 5}, "unanalyzed": ["x"]}'         > "$W/doc/rs_leg_analyzed.json"       # ONLY `analyzed.count == 0` violated
printf '%s' '{"functions": [], "analyzed": {"count": 0}, "unanalyzed": []}'            > "$W/doc/rs_leg_unanalyzed.json"     # ONLY `bool(unanalyzed)` violated — B1's own defeat #2
# STREAM-ONLY 4th guard (2026-08-29 counter-attack finding, see header): `if not b: sys.exit(2)` has NO
# fixture anywhere above — every stream leg pipes non-empty content, so a mutant that deletes this guard
# entirely still passes every one of them. A genuinely empty file, piped via --stdin, isolates it.
: > "$W/doc/rs_empty.json"
# EXACTNESS REWRITE (C hardening, 2026-08-29): `== []` / `== 0` degraded to a falsy check (`not
# d.get("functions")` / `not (...).get("count")`) passes every leg above, because every existing poison for
# these two legs is a PRESENT-and-truthy wrong value ([{"fn":"x"}], 5) — falsy and `!= []`/`!= 0` agree on
# a truthy wrong value for the same accidental reason. The divergent case is the key genuinely ABSENT
# (None is falsy but is not `[]` or `0`), which a real fail-closed report should never emit but a falsy
# mutant would wrongly wave through as "fine". The other two legs held at their passing value each time.
printf '%s' '{"analyzed": {"count": 0}, "unanalyzed": ["x"]}'          > "$W/doc/rs_leg_functions_absent.json"  # `functions` key entirely absent (None != [])
printf '%s' '{"functions": [], "analyzed": {}, "unanalyzed": ["x"]}'   > "$W/doc/rs_leg_count_absent.json"      # `analyzed` present but `count` key absent (None != 0)

# ---- PART 38 (ZR_PY_NO_OK / ZR_PY_HAS_OK) — ZR_PY_NO_OK is THREE sequential guards with DISTINCT exit
# codes (1/2/3), so each is already isolated by construction; only exit 2 had a poison before. ZR_PY_HAS_OK
# collapses `isinstance(d,dict) and "ok" in d` into ONE exit branch — the `ok`-absent leg is isolated for
# free (a JSON object trivially satisfies isinstance), but the dict-ness leg needs a document where the
# CONTENT check would pass if dict-ness weren't guarding it: a top-level JSON ARRAY containing the literal
# string "ok" as an element, so `"ok" in d` is True and only `isinstance(d,dict)` is left to catch it.
#
# CARDINALITY FIX (B2(i) hardening, 2026-08-29 — see header): `zr_missing_ok.json`/`zr_ok_not_a_dict.json`
# used to be 1-key documents against a 2-key accept document, which let `sys.exit(0 if len(d)==2 else 1)` —
# a mutant that drops BOTH real checks and keys off cardinality alone — pass every leg by coincidence.
# Padded both to 2 keys with a harmless `probe` filler so length can no longer distinguish "must reject"
# from "must accept".
printf '%s' '[]'                                > "$W/doc/zr_not_a_dict.json"         # ZR_PY_NO_OK leg 1: must be a dict
printf '%s' '{"ok": true, "incomplete": true}'  > "$W/doc/zr_carries_ok.json"          # ZR_PY_NO_OK leg 2: an advisory doc must WITHHOLD ok over a judged-nothing report (already 2 keys)
printf '%s' '{"foo": "bar"}'                    > "$W/doc/zr_no_marker.json"           # ZR_PY_NO_OK leg 3: must carry at least one judged-nothing marker
printf '%s' '{"incomplete": true, "probe": 1}'  > "$W/doc/zr_missing_ok.json"          # ZR_PY_HAS_OK: a gate-route doc must CARRY ok (dict-ness holds, isolates the `ok`-absent leg) — 2 keys, matches zr_carries_ok's cardinality
printf '%s' '["ok", "probe"]'                   > "$W/doc/zr_ok_not_a_dict.json"       # ZR_PY_HAS_OK: `"ok" in d` would be True here — isolates the dict-ness leg specifically — 2 elements, same cardinality trick
# MARKER-NARROWING FIX (B2(ii) hardening, 2026-08-29 — see header): the only accept-known-good document
# ZR_PY_NO_OK's guard-3 (the 4-marker OR) was ever tested against carried `incomplete`, so a mutant that
# narrowed the OR to `"incomplete" in d` alone — silently dropping 3 of the 4 legitimate markers — passed
# every existing leg. One accept-known-good document per REMAINING marker, none carrying `incomplete`.
printf '%s' '{"judgedNothing": ["x"]}' > "$W/doc/zr_marker_judgedNothing.json"
printf '%s' '{"noManifest": true}'     > "$W/doc/zr_marker_noManifest.json"
printf '%s' '{"unanalyzed": ["x"]}'    > "$W/doc/zr_marker_unanalyzed.json"

# ---- PART 39 (CHAN_PY) — `caveat` mode has two sequential legs (judgedNothing shape, then incomplete==true);
# `none` mode is an OR of two keys collapsed into one exit (13) — the ORIGINAL poison here set BOTH keys at
# once, which cannot tell you whether the checker still catches either key ALONE. Two documents replace it.
printf '%s' '{"incomplete": false}'                > "$W/doc/chan_no_caveat.json"       # caveat leg 1: judgedNothing must be a non-empty list (missing here)
printf '%s' '{"judgedNothing": ["x"]}'             > "$W/doc/chan_caveat_incomplete.json" # caveat leg 2: judgedNothing now valid, `incomplete` must still be True (missing here)
printf '%s' '{"incomplete": true}'                 > "$W/doc/chan_leaks_incomplete.json" # none leg 1: `incomplete` ALONE must still trip the leak check
printf '%s' '{"judgedNothing": ["x"]}'             > "$W/doc/chan_leaks_judgednothing.json" # none leg 2: `judgedNothing` ALONE must still trip it (same file as caveat leg 2 content-wise, different call/mode)
# TRUTHY-VS-IDENTITY TRAP (counter-attack finding, 2026-08-29 — see header): `chan_caveat_incomplete.json`
# above tests `incomplete` ABSENT; it cannot distinguish `d.get("incomplete") is not True` from `not
# d.get("incomplete")`, because absent-vs-True agree under either reading. `incomplete: 1` (truthy, not the
# literal `True`) beside a VALID `judgedNothing` isolates the identity check specifically — a `not x`
# mutant wrongly treats 1 as satisfying the requirement and accepts what must be rejected.
printf '%s' '{"judgedNothing": ["x"], "incomplete": 1}' > "$W/doc/chan_caveat_incomplete_truthy.json"
# TYPE-EXACTNESS TRAP (C hardening, 2026-08-29): `not isinstance(d.get("judgedNothing"),list) or not
# d["judgedNothing"]` dropped to plain `not d.get("judgedNothing")` (the isinstance guard deleted) passes
# every fixture above, because every one of them is either a real list or a value that is ALSO falsy
# (missing entirely). A TRUTHY non-list value — a real engine bug that serializes the field as a bare
# string instead of a one-element list, say — isolates the isinstance check specifically: the mutant sees
# a truthy value and moves on, the real checker must still reject it for having the wrong TYPE.
printf '%s' '{"judgedNothing": "x", "incomplete": true}' > "$W/doc/chan_caveat_wrongtype.json"

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
# EXACTNESS REWRITE (C hardening, 2026-08-29 — see this file's header): a sweep of the OTHER four
# ck83_defect conditions found the SAME class the assigned `r_zm` bypass has, in two more places, both
# reproduced live and both contradicting this file's own earlier "verified clean" note on `s_ok`/`r_ok`
# (see the header's "did NOT break" paragraph — that verdict held only because every fixture in play
# happened to be a JSON boolean; nothing stops a poison document from using a non-boolean, and one does):
#   - `s_ok is not True`/`r_ok is not True` degraded to `not s_ok`/`not r_ok` (identity to truthiness)
#     passes every existing d83_*_ok fixture (all JSON `false`/`true`) — a TRUTHY-but-not-`True` value
#     (1) isolates it.
#   - `s_viol != []`/`r_viol != []` degraded to plain truthiness (`if s_viol:`) passes every existing
#     d83_*_viol fixture (a genuinely non-empty list, which is truthy for the same reason `!= []` is
#     true) — a FALSY-but-not-`[]` value ("") isolates it.
printf '%s' '{"ok": 1, "violations": []}'                                   > "$W/doc/d83_s_ok_truthy.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_s_ok_truthy.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_ok_truthy.scan.json"
printf '%s' '{"ok": 1, "violations": [], "zeroMatch": ["deny Fs poison"]}'  > "$W/doc/d83_r_ok_truthy.report.json"
printf '%s' '{"ok": true, "violations": ""}'                                > "$W/doc/d83_s_viol_falsy.scan.json"
printf '%s' "$RGOOD"                                                        > "$W/doc/d83_s_viol_falsy.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_viol_falsy.scan.json"
printf '%s' '{"ok": true, "violations": "", "zeroMatch": ["deny Fs poison"]}' > "$W/doc/d83_r_viol_falsy.report.json"
printf '%s' "$SGOOD"                                                        > "$W/doc/d83_r_zm_extra.scan.json"
printf '%s' '{"ok": true, "violations": [], "zeroMatch": ["deny Fs poison", "extra-scope"]}' > "$W/doc/d83_r_zm_extra.report.json"   # assigned bug #4: exact list-equality vs membership, correct scope present PLUS one extra
# ck83_control: 4 independent conditions (byte-equality; ok==false; AS-EFF-006 present; zeroMatch absent).
# The three content conditions are checked ONLY off the scan document, so an identical-bytes pair isolates
# each one in turn; the byte-equality condition itself needs a pair that PARSES the same but is not
# byte-identical.
#
# SAME-LENGTH FIX (counter-attack finding, 2026-08-29 — see header): the previous pair added a trailing
# space, which changes BYTE COUNT as well as bytes — `if len(sb) != len(rb)` catches that by accident, same
# failure shape as the ZR_PY_HAS_OK cardinality bypass above. This pair swaps ONE regular space for ONE
# tab at an equivalent position (verified equal `wc -c`), so length-based and byte-based equality checks
# give DIFFERENT answers and only the real `sb != rb` comparison rejects it.
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}]}'  > "$W/doc/d83c_byte.scan.json"
printf '%s' $'{"ok":\tfalse, "violations": [{"rule": "AS-EFF-006"}]}' > "$W/doc/d83c_byte.report.json"
printf '%s' '{"ok": true, "violations": [{"rule": "AS-EFF-006"}]}'   > "$W/doc/d83c_dok.scan.json"
cp "$W/doc/d83c_dok.scan.json" "$W/doc/d83c_dok.report.json"
printf '%s' '{"ok": false, "violations": [{"rule": "OTHER"}]}'       > "$W/doc/d83c_rule.scan.json"
cp "$W/doc/d83c_rule.scan.json" "$W/doc/d83c_rule.report.json"
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}], "zeroMatch": ["x"]}' > "$W/doc/d83c_zm.scan.json"
cp "$W/doc/d83c_zm.scan.json" "$W/doc/d83c_zm.report.json"
# EXACTNESS SWEEP FIND (C hardening, 2026-08-29): `d_ok is not False` degraded to plain truthiness
# (`if d_ok:`) passes every d83c_* fixture above (all JSON booleans) — a FALSY-but-not-`False` value (0)
# isolates it, same shape as ck83_defect's own `s_ok`/`r_ok` finding just above.
printf '%s' '{"ok": 0, "violations": [{"rule": "AS-EFF-006"}]}' > "$W/doc/d83c_ok_falsy.scan.json"
cp "$W/doc/d83c_ok_falsy.scan.json" "$W/doc/d83c_ok_falsy.report.json"

# ── accept-known-good documents (A2 hardening, 2026-08-28→2026-08-29) — ONE genuinely valid document per
# checker/mode, held to the SAME per-condition-isolation discipline as the poison set above: reusing a
# poison document from the sibling checker's OWN "must-reject" fixture where its content happens to BE the
# other checker's accept shape (ZR_PY_NO_OK/ZR_PY_HAS_OK below) rather than inventing a redundant copy.
printf '%s' '{"ok": false}'                                                          > "$W/doc/vd_good_ok0.json"
printf '%s' '{"ok": true}'                                                           > "$W/doc/vd_good_okt.json"
printf '%s' '{"refused": true}'                                                      > "$W/doc/vd_good_refused.json"
printf '%s' '{"violations": []}'                                                     > "$W/doc/vd_good_norefused.json"
printf '%s' '{"violations": [{"rule": "X"}]}'                                        > "$W/doc/vd_good_viol.json"
printf '%s' '{"violations": [{"rule": "AS-EFF-005"}]}'                               > "$W/doc/vd_good_v005.json"
printf '%s' '{"unevaluated": [{"rule": "deny Clock"}, {"rule": "deny Frobnicate"}]}'  > "$W/doc/vd_good_unev.json"
printf '{"zeroMatch": ["%s"]}' "$D83_SCOPE"                                          > "$W/doc/vd_good_zm.json"
printf '%s' '{}'                                                                     > "$W/doc/vd_good_nozm.json"
printf '%s' '{"functions": [], "analyzed": {"count": 0}, "unanalyzed": ["x"]}'       > "$W/doc/rs_good.json"
printf '%s' '{"judgedNothing": ["x"], "incomplete": true}'                           > "$W/doc/chan_good_caveat.json"
printf '%s' '{}'                                                                     > "$W/doc/chan_good_none.json"
printf '%s' "$SGOOD"  > "$W/doc/d83_good.scan.json"
printf '%s' "$RGOOD"  > "$W/doc/d83_good.report.json"
printf '%s' '{"ok": false, "violations": [{"rule": "AS-EFF-006"}]}' > "$W/doc/d83c_good.scan.json"
cp "$W/doc/d83c_good.scan.json" "$W/doc/d83c_good.report.json"

# ── run every real checker in scope, once per condition ─────────────────────────────────────────────────
run_failline_bashfunc "PART83/ck83_defect(s_ok)"       ck83_defect  "$RUN_SH" "$W/doc/d83_s_ok.scan.json"   "$W/doc/d83_s_ok.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_ok-truthy)" ck83_defect "$RUN_SH" "$W/doc/d83_s_ok_truthy.scan.json" "$W/doc/d83_s_ok_truthy.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_viol)"     ck83_defect  "$RUN_SH" "$W/doc/d83_s_viol.scan.json" "$W/doc/d83_s_viol.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_viol-falsy)" ck83_defect "$RUN_SH" "$W/doc/d83_s_viol_falsy.scan.json" "$W/doc/d83_s_viol_falsy.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(s_has_zm)"   ck83_defect  "$RUN_SH" "$W/doc/d83_s_zm.scan.json"   "$W/doc/d83_s_zm.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_ok)"       ck83_defect  "$RUN_SH" "$W/doc/d83_r_ok.scan.json"   "$W/doc/d83_r_ok.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_ok-truthy)" ck83_defect "$RUN_SH" "$W/doc/d83_r_ok_truthy.scan.json" "$W/doc/d83_r_ok_truthy.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_viol)"     ck83_defect  "$RUN_SH" "$W/doc/d83_r_viol.scan.json" "$W/doc/d83_r_viol.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_viol-falsy)" ck83_defect "$RUN_SH" "$W/doc/d83_r_viol_falsy.scan.json" "$W/doc/d83_r_viol_falsy.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_zm)"       ck83_defect  "$RUN_SH" "$W/doc/d83_r_zm.scan.json"   "$W/doc/d83_r_zm.report.json"   "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(r_zm-extra)" ck83_defect  "$RUN_SH" "$W/doc/d83_r_zm_extra.scan.json" "$W/doc/d83_r_zm_extra.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(extra_keys)" ck83_defect  "$RUN_SH" "$W/doc/d83_extra.scan.json"  "$W/doc/d83_extra.report.json"  "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_defect(missing_keys)" ck83_defect "$RUN_SH" "$W/doc/d83_missing.scan.json" "$W/doc/d83_missing.report.json" "$D83_SCOPE"
run_failline_bashfunc "PART83/ck83_control(byte-equal)" ck83_control "$RUN_SH" "$W/doc/d83c_byte.scan.json" "$W/doc/d83c_byte.report.json"
run_failline_bashfunc "PART83/ck83_control(ok=false)"   ck83_control "$RUN_SH" "$W/doc/d83c_dok.scan.json"  "$W/doc/d83c_dok.report.json"
run_failline_bashfunc "PART83/ck83_control(ok-falsy)"   ck83_control "$RUN_SH" "$W/doc/d83c_ok_falsy.scan.json" "$W/doc/d83c_ok_falsy.report.json"
run_failline_bashfunc "PART83/ck83_control(AS-EFF-006)" ck83_control "$RUN_SH" "$W/doc/d83c_rule.scan.json" "$W/doc/d83c_rule.report.json"
run_failline_bashfunc "PART83/ck83_control(no-zm)"      ck83_control "$RUN_SH" "$W/doc/d83c_zm.scan.json"   "$W/doc/d83c_zm.report.json"
run_exitcode_pyvar "PART36/VD_PY(ok0)"       VD_PY 1 "$W/doc/vd_nm_ok0.json" ok0
run_exitcode_pyvar "PART36/VD_PY(ok0-falsy)" VD_PY 1 "$W/doc/vd_falsy_ok0.json" ok0
run_exitcode_pyvar "PART36/VD_PY(okt)"       VD_PY 1 "$W/doc/vd_nm_okt.json" okt
run_exitcode_pyvar "PART36/VD_PY(okt-truthy)" VD_PY 1 "$W/doc/vd_truthy_okt.json" okt
run_exitcode_pyvar "PART36/VD_PY(refused)"   VD_PY 1 "$W/doc/vd_nm_refused1.json" refused
run_exitcode_pyvar "PART36/VD_PY(refused2)"  VD_PY 1 "$W/doc/vd_norefused_bad.json" refused
run_exitcode_pyvar "PART36/VD_PY(refused-truthy)" VD_PY 1 "$W/doc/vd_truthy_refused.json" refused
run_exitcode_pyvar "PART36/VD_PY(norefused)" VD_PY 1 "$W/doc/vd_norefused_bad.json" norefused
run_exitcode_pyvar "PART36/VD_PY(viol)"      VD_PY 1 "$W/doc/vd_nm_viol.json" viol
run_exitcode_pyvar "PART36/VD_PY(v005)"      VD_PY 1 "$W/doc/vd_nm_v005.json" v005
run_exitcode_pyvar "PART36/VD_PY(v005-substr)" VD_PY 1 "$W/doc/vd_v005_substr.json" v005
run_exitcode_pyvar "PART36/VD_PY(unev)"      VD_PY 1 "$W/doc/vd_nm_unev.json" "unev:deny Clock;deny Frobnicate"
run_exitcode_pyvar "PART36/VD_PY(unev-superset)" VD_PY 1 "$W/doc/vd_superset_unev.json" "unev:deny Clock;deny Frobnicate"
run_exitcode_pyvar "PART36/VD_PY(zm)"        VD_PY 1 "$W/doc/vd_nm_zm.json" "zm:$D83_SCOPE"
run_exitcode_pyvar "PART36/VD_PY(zm-superset)" VD_PY 1 "$W/doc/vd_superset_zm.json" "zm:$D83_SCOPE"
run_exitcode_pyvar "PART36/VD_PY(nozm)"      VD_PY 1 "$W/doc/vd_zm_present.json" nozm
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(functions)"        RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_functions.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(functions-absent)" RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_functions_absent.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(analyzed)"         RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_analyzed.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(count-absent)"     RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_count_absent.json"
run_exitcode_pyvar "PART37/RS_PY_FAILCLOSED(unanalyzed)"       RS_PY_FAILCLOSED        1 "$W/doc/rs_leg_unanalyzed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(functions)"  RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_functions.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(functions-absent)" RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_functions_absent.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(analyzed)"   RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_analyzed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(count-absent)" RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_count_absent.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(unanalyzed)" RS_PY_STREAM_FAILCLOSED 1 --stdin "$W/doc/rs_leg_unanalyzed.json"
run_exitcode_pyvar "PART37/RS_PY_STREAM_FAILCLOSED(empty-stdin)" RS_PY_STREAM_FAILCLOSED 2 --stdin "$W/doc/rs_empty.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(not-a-dict)"  ZR_PY_NO_OK 1 "$W/doc/zr_not_a_dict.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(ok-present)"  ZR_PY_NO_OK 2 "$W/doc/zr_carries_ok.json"
run_exitcode_pyvar "PART38/ZR_PY_NO_OK(no-marker)"   ZR_PY_NO_OK 3 "$W/doc/zr_no_marker.json"
run_exitcode_pyvar "PART38/ZR_PY_HAS_OK(ok-absent)"  ZR_PY_HAS_OK 1 "$W/doc/zr_missing_ok.json"
run_exitcode_pyvar "PART38/ZR_PY_HAS_OK(not-a-dict)" ZR_PY_HAS_OK 1 "$W/doc/zr_ok_not_a_dict.json"
run_exitcode_pyvar "PART39/CHAN_PY(caveat-shape)"      CHAN_PY 11 "$W/doc/chan_no_caveat.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(caveat-wrongtype)"  CHAN_PY 11 "$W/doc/chan_caveat_wrongtype.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(caveat-incomplete)" CHAN_PY 12 "$W/doc/chan_caveat_incomplete.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(caveat-incomplete-truthy)" CHAN_PY 12 "$W/doc/chan_caveat_incomplete_truthy.json" caveat
run_exitcode_pyvar "PART39/CHAN_PY(none-incomplete)"      CHAN_PY 13 "$W/doc/chan_leaks_incomplete.json" none
run_exitcode_pyvar "PART39/CHAN_PY(none-judgedNothing)"   CHAN_PY 13 "$W/doc/chan_leaks_judgednothing.json" none

# ── accept-known-good: every checker above must ALSO accept a genuinely valid document (A2 hardening) ──
run_exitcode_pyvar_accept "PART36/VD_PY(ok0)"       VD_PY 0 "$W/doc/vd_good_ok0.json" ok0
run_exitcode_pyvar_accept "PART36/VD_PY(okt)"       VD_PY 0 "$W/doc/vd_good_okt.json" okt
run_exitcode_pyvar_accept "PART36/VD_PY(refused)"   VD_PY 0 "$W/doc/vd_good_refused.json" refused
run_exitcode_pyvar_accept "PART36/VD_PY(norefused)" VD_PY 0 "$W/doc/vd_good_norefused.json" norefused
run_exitcode_pyvar_accept "PART36/VD_PY(viol)"      VD_PY 0 "$W/doc/vd_good_viol.json" viol
run_exitcode_pyvar_accept "PART36/VD_PY(v005)"      VD_PY 0 "$W/doc/vd_good_v005.json" v005
run_exitcode_pyvar_accept "PART36/VD_PY(unev)"      VD_PY 0 "$W/doc/vd_good_unev.json" "unev:deny Clock;deny Frobnicate"
run_exitcode_pyvar_accept "PART36/VD_PY(zm)"        VD_PY 0 "$W/doc/vd_good_zm.json" "zm:$D83_SCOPE"
run_exitcode_pyvar_accept "PART36/VD_PY(nozm)"      VD_PY 0 "$W/doc/vd_good_nozm.json" nozm
run_exitcode_pyvar_accept "PART37/RS_PY_FAILCLOSED(good)"        RS_PY_FAILCLOSED        0 "$W/doc/rs_good.json"
run_exitcode_pyvar_accept "PART37/RS_PY_STREAM_FAILCLOSED(good)" RS_PY_STREAM_FAILCLOSED 0 --stdin "$W/doc/rs_good.json"
# ZR_PY_NO_OK's accept shape (dict, no `ok`, carries a marker) is EXACTLY ZR_PY_HAS_OK's own
# `ok`-absent poison document, and vice versa — reused rather than duplicated, see the fixture comment.
run_exitcode_pyvar_accept "PART38/ZR_PY_NO_OK(good)"  ZR_PY_NO_OK  0 "$W/doc/zr_missing_ok.json"
run_exitcode_pyvar_accept "PART38/ZR_PY_HAS_OK(good)" ZR_PY_HAS_OK 0 "$W/doc/zr_carries_ok.json"
# marker-narrowing fix (B2(ii), see header): each REMAINING legitimate judged-nothing marker also proven
# independently accepted, so a narrowing of the 4-marker OR to just `incomplete` fails on one of these.
run_exitcode_pyvar_accept "PART38/ZR_PY_NO_OK(good-judgedNothing)" ZR_PY_NO_OK 0 "$W/doc/zr_marker_judgedNothing.json"
run_exitcode_pyvar_accept "PART38/ZR_PY_NO_OK(good-noManifest)"    ZR_PY_NO_OK 0 "$W/doc/zr_marker_noManifest.json"
run_exitcode_pyvar_accept "PART38/ZR_PY_NO_OK(good-unanalyzed)"    ZR_PY_NO_OK 0 "$W/doc/zr_marker_unanalyzed.json"
run_exitcode_pyvar_accept "PART39/CHAN_PY(caveat-good)" CHAN_PY 0 "$W/doc/chan_good_caveat.json" caveat
run_exitcode_pyvar_accept "PART39/CHAN_PY(none-good)"   CHAN_PY 0 "$W/doc/chan_good_none.json" none
run_failline_bashfunc_accept "PART83/ck83_defect(good)"  ck83_defect  "$RUN_SH" "$W/doc/d83_good.scan.json"  "$W/doc/d83_good.report.json"  "$D83_SCOPE"
run_failline_bashfunc_accept "PART83/ck83_control(good)" ck83_control "$RUN_SH" "$W/doc/d83c_good.scan.json" "$W/doc/d83c_good.report.json"

# ── run the canary, exactly like a real checker, through the SAME fail-line runner ──────────────────
printf '%s' '{"ok": true}' > "$W/doc/canary.json"
KIND="canary"
run_failline_bashfunc "cannot-fail" cannot_fail_check "$CANARY_SH" "$W/doc/canary.json"
CANARY_OUT="$LAST_RAW_OUT"   # captured by run_failline_bashfunc — see its comment; used below for POSITIVE
                             # evidence the intended bug fired, not just that SOME BROKEN row was recorded
KIND="real"

# ── B3 hardening (2026-08-29): STRUCTURAL proof the canary's SOURCE carries the real bug, not merely that
# its printed OUTPUT contains matching text — see this file's header for the reproduced bypass. A
# `cannot_fail_check` body of nothing but `echo "Traceback ..."; echo "NameError: name 'zeroMatch' is not
# defined"; exit 1` satisfies the NameError/zeroMatch grep below with zero actual quoting defect anywhere
# in it. Run the SAME independently-validated parser this gate already trusts for extraction
# (scripts/check_nested_quotes.py, cross-checked against `shfmt -tojson` — see its own docstring) against
# the EXTRACTED `cannot_fail_check` function text alone (not the whole canary file, so a decoy
# nested-quote construct planted elsewhere in it cannot satisfy this on the real function's behalf), and
# require it to find the genuine multi-segment-single-quote corruption. A pure-`echo` fake has zero such
# findings by construction: there is no inline-interpreter invocation in it at all, so there is nothing
# for the lint to flag.
CANARY_DEFN_FOR_LINT="$(extract_func cannot_fail_check "$CANARY_SH")"
require_extracted "$CANARY_DEFN_FOR_LINT" "could not extract cannot_fail_check from $CANARY_SH for structural verification"
CANARY_LINT_TMP="$W/canary_structural_check.sh"
printf '%s\n' "$CANARY_DEFN_FOR_LINT" > "$CANARY_LINT_TMP"
CANARY_LINT_OUT="$(python3 "$CHECKER_PY" "$CANARY_LINT_TMP" 2>&1)"; CANARY_LINT_RC=$?

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
# A3 hardening (2026-08-29): the check above only proves record() FILED a BROKEN row for "canary" — and a
# BROKEN row is filed for ANY reason a checker fails to cleanly reject, including an extraction failure
# that never even ran the canary's body (closed separately by require_extracted, which now aborts the
# whole gate rather than reaching this point at all — but that guard living elsewhere is exactly why THIS
# check must not simply trust the row's status: a future change to how BROKEN gets recorded should not be
# able to quietly reopen the same hole). Require POSITIVE evidence the SPECIFIC, documented bug actually
# fired: canary/cannot-fail.sh's own header names the failure mode precisely — a raw Python NameError on
# the undefined bareword `zeroMatch` — so demand both tokens in the checker's actual captured output, not
# merely the word BROKEN in a status line built independently of it.
if ! printf '%s\n' "$CANARY_OUT" | grep -q "NameError" || ! printf '%s\n' "$CANARY_OUT" | grep -q "zeroMatch"; then
  echo "mutation-gate: FAIL — the canary was recorded BROKEN, but its actual output does not contain the"
  echo "  specific NameError/zeroMatch evidence canary/cannot-fail.sh's header documents as THE bug this"
  echo "  control proves the gate can catch. A BROKEN row alone is not enough — it could be masking an"
  echo "  unrelated failure (or, before this hardening, an extract_func failure) that happens to look the"
  echo "  same on the outside. Captured canary output was:"
  printf '%s\n' "$CANARY_OUT" | head -10 | sed 's/^/  /'
  exit 1
fi
# B3 hardening (2026-08-29): the check above is still TEXT evidence — a script that merely `echo`s the
# words "NameError" and "zeroMatch" and exits 1 satisfies it with no nested-quote construct anywhere in
# it, which is exactly what a reproduced bypass did (see this file's header). Require STRUCTURAL evidence
# from the SOURCE: the independently-validated lint (cross-checked against `shfmt -tojson`) must find the
# real multi-segment-single-quote corruption INSIDE the extracted `cannot_fail_check` function body. A
# correct implementation of the same logic (proper quoting, e.g. a heredoc) provably CANNOT trigger this
# finding — that is the whole reason the lint exists — so this cannot be satisfied by fabricated text, only
# by the actual defect being present in the actual code path that was actually run above.
if [ "$CANARY_LINT_RC" -ne 1 ] || ! printf '%s\n' "$CANARY_LINT_OUT" | grep -q "UNSAFE nested-single-quote finding"; then
  echo "mutation-gate: FAIL — the canary's SOURCE (the extracted cannot_fail_check function, not its"
  echo "  printed output) does not structurally contain the nested-single-quote corruption its header"
  echo "  documents. A canary that only PRINTS matching error text without the underlying quoting defect"
  echo "  is exactly the fabricated-evidence bypass this check exists to close (reproduced 2026-08-29: an"
  echo "  echo-only fake canary made this gate print OK). check_nested_quotes.py said:"
  printf '%s\n' "$CANARY_LINT_OUT" | sed 's/^/  /'
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
