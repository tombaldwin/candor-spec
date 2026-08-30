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
# RELEASE-GATING parts — verdict, route/sink-equality, disclosure/refusal — not all ~86 addressable parts
# in conformance/run.sh. Covered: PART 36 (verdict document cells), PART 37 (report-sink fail-closed
# shape), PART 38 (zero-rule-policy refusal), PART 39 (report-consuming verb re-discloses the caveat),
# PART 83 (the byte-equality quadrant — today's own PART, whose first draft carried this exact bug), and,
# from the 2026-08-29 EMBEDDED-PARTS SURVEY (see that section far below for the full 68-part table and its
# numerator), PART 46 (a caller of a body-less local declaration is not pure) and PART 72 (byte-equality
# across both gate routes, SPEC §3.1 ⟨0.24⟩'s MUST). NOT covered, stated explicitly rather than silently:
# PART 2/3/12 (other verdict differentials — these three are not even independently addressable via
# `part.sh --list`; they ride inside a neighbouring slice), PART 29/32/34/47/57/59/60/61/62/67/68/69/70
# (other refusal/disclosure/route-equality rows), and every TIER-2 part. Most of those rows drive real
# engine binaries rather than taking a document directly (PART 32's zm_probe, for example, has no "poison
# JSON" to feed — its input IS a source fixture scanned by four real toolchains), which is a different,
# larger mutation-testing project; extending this gate to them is future work, not silently assumed done
# here.
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
# EXTERNAL CHECKER SCRIPTS (2026-08-29 survey — see this file's header, "EXTERNAL CHECKERS" section, for
# why these are a SEPARATE class from the run.sh-embedded checkers above and how far this covers them).
HONESTY_PY="$HERE/check_honesty.py"
FILE_SET_PY="$HERE/file_set_check.py"
PEEK_COMPLETENESS_PY="$HERE/peek_completeness_check.py"
REFUSED_PEEK_PY="$HERE/refused_peek_check.py"
PEEK_ROUTE_EQ_PY="$HERE/peek_route_equality_check.py"
EXEC_CAP_PY="$HERE/exec_capability_check.py"
ONLY_PY="$HERE/only_check.py"
for f in "$RUN_SH" "$CHECKER_PY" "$CANARY_SH" "$HONESTY_PY" "$FILE_SET_PY" "$PEEK_COMPLETENESS_PY" \
         "$REFUSED_PEEK_PY" "$PEEK_ROUTE_EQ_PY" "$EXEC_CAP_PY" "$ONLY_PY"; do
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
# ── the 2026-08-29 EMBEDDED-PARTS SURVEY added two more shapes (see "EMBEDDED RUN.SH SURVEY" section
# below): a `python3 - ARGS <<'DELIM'` heredoc (PART 46's PYBL) and a same-line-close `name() { python3 -c
# '<PY>' ARGS; }` function (PART 72's eq72/ck72/mut72) — the latter is NOT reachable by extract_func above,
# whose `/^}/` end-marker assumes the closing brace sits ALONE at column 0; eq72 closes with `' "$1" "$2";
# }` on the SAME line as the final quote, so extract_func would run past it to the file's next column-0
# `}` and silently extract the wrong, larger span. Both are pulled by check_nested_quotes.py — a heredoc
# body is lexically unambiguous (it ends at the line that IS the delimiter, no quote-parsing needed), and
# the oneline-func shape needs its own regex for the same reason extract_func's doesn't apply.
extract_heredoc() {   # $1 = heredoc delimiter, e.g. PYBL (from `<<'PYBL'`)
  python3 "$CHECKER_PY" --extract-heredoc "$1" "$RUN_SH"
}
extract_oneline_func() {   # $1 = function name, e.g. eq72 (from `eq72() { python3 -c '...' ...; }`)
  python3 "$CHECKER_PY" --extract-oneline-func "$1" "$RUN_SH"
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
# "heredoc": the PART 46 shape (`python3 - ARGS <<'PYBL' || VAR=1`) — same exit-code contract as
# run_exitcode_pyvar (the calling bash line supplies the human FAIL text, not the extracted script), but
# extracted via extract_heredoc rather than extract_pyvar since the source lives between two `<<'DELIM'`
# lines in run.sh, not inside a `NAME='...'` assignment.
run_exitcode_heredoc() {   # $1 label ; $2 delim ; $3 expected-reject-exit-code ; $4.. poison args
  local label="$1" delim="$2" want_rc="$3"; shift 3
  local src; src="$(extract_heredoc "$delim")"
  require_extracted "$src" "could not extract heredoc <<'$delim' from $RUN_SH — nothing to test"
  local tmp="$W/$delim.py"; printf '%s' "$src" > "$tmp"
  local out rc
  out="$(python3 "$tmp" "$@" 2>&1)"; rc=$?
  if [ "$rc" = "$want_rc" ] && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "poison was NOT rejected with the expected exit $want_rc (got exit=$rc)" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
run_exitcode_heredoc_accept() {   # $1 label ; $2 delim ; $3 accept-exit-code ; $4.. KNOWN-GOOD args
  local label="$1" delim="$2" want_rc="$3"; shift 3
  local src; src="$(extract_heredoc "$delim")"
  require_extracted "$src" "could not extract heredoc <<'$delim' from $RUN_SH for accept-check \"$label\""
  local tmp="$W/$delim.accept.py"; printf '%s' "$src" > "$tmp"
  local out rc
  out="$(python3 "$tmp" "$@" 2>&1)"; rc=$?
  if [ "$rc" = "$want_rc" ] && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label (accept-known-good)"
  else
    record BROKEN "$label (accept-known-good)" \
      "a VALID document was NOT accepted (want exit $want_rc, got exit=$rc) — checker may have degenerated to unconditional-reject" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
# "oneline-func stdout": the PART 72 shape (`eq72() { python3 -c '<PY>' "$1" "$2"; }`) — its contract is
# neither a FAIL: line (PART 83's convention) nor a distinguishing exit code (it always exits 0 unless the
# read itself fails) but a specific STDOUT token (`equal` / `diverge:<keys>`) that the CALLER (p72(), via
# `[ "$2" = 0 ]` on a 0/1 the caller derives from this text) turns into pass/fail — so THIS is the layer
# that must be proven to still discriminate a real difference from none.
run_stdout_oneline_func() {   # $1 label ; $2 funcname ; $3 expected-stdout ERE ; $4.. args
  local label="$1" fn="$2" want="$3"; shift 3
  local src; src="$(extract_oneline_func "$fn")"
  require_extracted "$src" "could not extract \`$fn\` from $RUN_SH — nothing to test"
  local tmp="$W/$fn.py"; printf '%s' "$src" > "$tmp"
  local out rc
  out="$(python3 "$tmp" "$@" 2>&1)"; rc=$?
  if printf '%s\n' "$out" | grep -Eq "$want" && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "stdout did not match /$want/ (rc=$rc, got: $(printf '%s' "$out" | head -c 200 | tr '\n' ' '))" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
# "ext-script": a checker that already lives as a standalone file (conformance/*.py), never pasted out of
# run.sh via extract_pyvar/extract_func — see this file's header, "EXTERNAL CHECKERS" section, for why
# these needed a THIRD runner shape rather than reusing run_exitcode_pyvar: there is no extraction step
# (require_extracted does not apply — the file itself IS the current source, so a future edit to it is
# picked up on the next run with no copy to go stale), and every one of these takes its poison as ARGV
# (paths to hand-written report/verdict JSON, or literal exit-code/output strings) rather than stdin.
run_ext_reject() {   # $1 label ; $2 script path ; $3 expected-reject-exit-code ; $4.. poison argv
  local label="$1" script="$2" want_rc="$3"; shift 3
  local out rc
  out="$(python3 "$script" "$@" 2>&1)"; rc=$?
  if [ "$rc" = "$want_rc" ] && ! printf '%s\n' "$out" | grep -q '^Traceback'; then
    record PASS "$label"
  else
    record BROKEN "$label" \
      "poison was NOT rejected with the expected exit $want_rc (got exit=$rc)" \
      "$(printf '%s\n' "$out" | head -5)"
  fi
}
run_ext_accept() {   # $1 label ; $2 script path ; $3 accept-exit-code ; $4.. KNOWN-GOOD argv
  local label="$1" script="$2" want_rc="$3"; shift 3
  local out rc
  out="$(python3 "$script" "$@" 2>&1)"; rc=$?
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

# ── EXTERNAL CHECKERS (2026-08-29 survey) ────────────────────────────────────────────────────────────
# WHY THESE EXIST, and why only these seven of the ~13 external checkers the survey found defeatable.
# `conformance/part.sh <id>` with each checker's `main()` body replaced by an unconditional `sys.exit(0)`
# — the SAME universal test this file's header recommends trying first — left EVERY row the checker feeds
# GREEN, with zero output difference, for: check_honesty.py (PART 1c), file_set_check.py (PART 48),
# only_check.py (PART 49), incomplete_check.py (PART 50), fs_position_check.py (PART 51),
# peek_completeness_check.py (PART 52), refused_peek_check.py (PART 53), peek_route_equality_check.py
# (PART 54), exec_capability_check.py (PART 66), clause_check.py, probe_check.py, must_ledger.py, and
# part_declarations.py — thirteen checkers, NONE of them reachable by this file's extract_pyvar/
# extract_func (they are standalone files run.sh calls by path, not variables or functions pasted out of
# it), so none had ever been attacked before this survey. check_honesty.py is the starkest: its own
# CONTROLS comment in run.sh reads "none — every row asserts document CONTENT", so a check_honesty.py that
# silently degenerated to `sys.exit(0)` would be caught by NOTHING in the ~15,800-line suite.
#
# SEVEN of the thirteen are hardened below with real near-miss poison, chosen for severity (the task that
# produced this survey named "verdict, route-equality, disclosure, refusal, completeness" as the
# properties whose green reads as a release signal): check_honesty.py (THE honesty-invariant detector —
# highest priority by a wide margin, zero backstop), file_set_check.py (PART 48, verdict),
# peek_completeness_check.py (PART 52, completeness), refused_peek_check.py (PART 53, refusal),
# peek_route_equality_check.py (PART 54, route-equality — the flagship byte-equality check, same historical
# bug shape as ck83_control's), exec_capability_check.py (PART 66, capability disclosure), and
# only_check.py (PART 49, the AS-EFF-011/009 collision this checker's OWN header documents as a REAL,
# SHIPPED bug in candor-rust and candor-java — the single highest-value poison in this block, since it
# reproduces a defect that already happened rather than a hypothetical one).
#
# NOT hardened here, stated explicitly rather than silently: incomplete_check.py (PART 50),
# fs_position_check.py (PART 51), clause_check.py, probe_check.py, must_ledger.py, part_declarations.py,
# and skip_ratchet.py (PART 84 — confirmed only INCONCLUSIVE in isolation via `part.sh 84`, since it reads
# a skip-tally log the full suite accumulates; a standalone unconditional-pass test could not even reach a
# conclusion, let alone a near-miss battery). The four meta-checkers (clause_check/probe_check/
# must_ledger/part_declarations) check SPEC.md and run.sh's own TEXT/structure rather than an engine's
# JSON report, which is a different poison shape than the near-miss discipline below and was left for a
# separate pass. This is a SURVEY BOUNDARY, not a claim these are safe.
#
# EACH POISON BELOW IS ONE PER CONDITION, holding every condition BEFORE it (in the checker's own
# sequential `if cond: return fail(...)` structure) at its PASSING value — a condition strictly AFTER the
# one under test never runs, by construction, so it needs no value at all. This is a shallower sweep than
# the multi-round C-hardening discipline PART 36-39/83 received above (one poison per condition, not the
# full truthy/falsy/superset/subset/substring family for every one) — stated as a boundary, not hidden.
mkdir -p "$W/ext"

# ---- check_honesty.py (PART 1c) — the two forms check() enforces: DIRECT (a function flagged `unresolved`
# must surface Unknown or a disclosure) and PROPAGATION (a certain function must not reach an uncertain
# callee). Each fixture pairs a report with its sibling `.callgraph.json` (check_honesty.py's own naming
# convention: report path with `.json` replaced by `.callgraph.json`).
printf '%s' '{"functions": [{"fn": "g", "inferred": ["Unknown"]}]}' > "$W/ext/ch_prop_poison.json"
printf '%s' '{"f": ["g"], "g": []}'                                  > "$W/ext/ch_prop_poison.callgraph.json"
printf '%s' '{"functions": [{"fn": "f", "inferred": ["Unknown"]}, {"fn": "g", "inferred": ["Unknown"]}]}' > "$W/ext/ch_prop_good.json"
printf '%s' '{"f": ["g"], "g": []}'                                  > "$W/ext/ch_prop_good.callgraph.json"
printf '%s' '{"functions": [{"fn": "h", "unresolved": true, "inferred": []}]}' > "$W/ext/ch_direct_poison.json"
printf '%s' '{"h": []}'                                              > "$W/ext/ch_direct_poison.callgraph.json"
printf '%s' '{"functions": [{"fn": "h", "unresolved": true, "inferred": ["Unknown"]}]}' > "$W/ext/ch_direct_good.json"
printf '%s' '{"h": []}'                                              > "$W/ext/ch_direct_good.callgraph.json"
run_ext_reject "PART1c/check_honesty(propagation)"  "$HONESTY_PY" 1 "$W/ext/ch_prop_poison.json"
run_ext_accept "PART1c/check_honesty(propagation)"  "$HONESTY_PY" 0 "$W/ext/ch_prop_good.json"
run_ext_reject "PART1c/check_honesty(direct-form)"  "$HONESTY_PY" 1 "$W/ext/ch_direct_poison.json"
run_ext_accept "PART1c/check_honesty(direct-form)"  "$HONESTY_PY" 0 "$W/ext/ch_direct_good.json"

# ---- file_set_check.py (PART 48) — two conditions on the FINDING half: the effect-membership filter
# (`hits`) and the reason-substring check ("did NOT judge"). GOOD is the full 8-condition accept shape;
# each poison holds every OTHER argument at GOOD and perturbs the one field the condition under test reads.
printf '%s' '{"outOfScope": [{"fn":"build::main","path":"build.rs","class":"build-script","effects":["Exec"],"reason":"the gate did NOT judge this file: excluded by policy"}], "functions": [], "violations": [], "excluded": [{"class":"build-script","count":1,"peeked":true,"reason":"build scripts run outside the crate scan and are not judged by this policy"}]}' > "$W/ext/fs_exec_good.json"
printf '%s' '{"outOfScope": []}'  > "$W/ext/fs_net_good.json"
printf '%s' '{}'                  > "$W/ext/fs_none_good.json"
printf '%s' '{"excluded": []}'    > "$W/ext/fs_ctl_good.json"
printf '%s' '{"functions": [{"fn":"build::main","inferred":["Exec"]}]}' > "$W/ext/fs_twin_good.json"
run_ext_accept "PART48/file_set_check(good)" "$FILE_SET_PY" 0 rust 2 "$W/ext/fs_exec_good.json" 0 "$W/ext/fs_net_good.json" "$W/ext/fs_none_good.json" "$W/ext/fs_ctl_good.json" "$W/ext/fs_twin_good.json" Exec
printf '%s' '{"outOfScope": [{"fn":"build::main","path":"build.rs","class":"build-script","effects":["Net"],"reason":"the gate did NOT judge this file: excluded by policy"}], "functions": [], "violations": [], "excluded": [{"class":"build-script","count":1,"peeked":true,"reason":"build scripts run outside the crate scan and are not judged by this policy"}]}' > "$W/ext/fs_exec_f1.json"
run_ext_reject "PART48/file_set_check(effect-membership)" "$FILE_SET_PY" 1 rust 2 "$W/ext/fs_exec_f1.json" 0 "$W/ext/fs_net_good.json" "$W/ext/fs_none_good.json" "$W/ext/fs_ctl_good.json" "$W/ext/fs_twin_good.json" Exec
printf '%s' '{"outOfScope": [{"fn":"build::main","path":"build.rs","class":"build-script","effects":["Exec"],"reason":"excluded by policy"}], "functions": [], "violations": [], "excluded": [{"class":"build-script","count":1,"peeked":true,"reason":"build scripts run outside the crate scan and are not judged by this policy"}]}' > "$W/ext/fs_exec_f2.json"
run_ext_reject "PART48/file_set_check(reason-substring)" "$FILE_SET_PY" 1 rust 2 "$W/ext/fs_exec_f2.json" 0 "$W/ext/fs_net_good.json" "$W/ext/fs_none_good.json" "$W/ext/fs_ctl_good.json" "$W/ext/fs_twin_good.json" Exec

# ---- peek_completeness_check.py (PART 52) — the three `is not False`/`is not True` IDENTITY checks
# (shapes A/B/C), attacked with the SAME truthy/falsy-but-wrong-type near-miss that broke VD_PY/ck83_defect/
# ck83_control above (falsy-but-not-`False` = `0`; truthy-but-not-`True` = `1`).
printf '%s' '{"excluded":[{"class":"harness-target","peeked":false}]}' > "$W/ext/pc_a_good.json"
printf '%s' '{"excluded":[{"class":"harness-target","peeked":true}], "outOfScope": []}' > "$W/ext/pc_b_good.json"
printf '%s' '{"excluded":[{"class":"harness-target","peeked":true}], "outOfScope": [{"class":"harness-target"}]}' > "$W/ext/pc_c_good.json"
run_ext_accept "PART52/peek_completeness(good)" "$PEEK_COMPLETENESS_PY" 0 rust "$W/ext/pc_a_good.json" "$W/ext/pc_b_good.json" "$W/ext/pc_c_good.json" harness-target
printf '%s' '{"excluded":[{"class":"harness-target","peeked":0}]}' > "$W/ext/pc_a_poison.json"
run_ext_reject "PART52/peek_completeness(A-falsy-not-False)" "$PEEK_COMPLETENESS_PY" 1 rust "$W/ext/pc_a_poison.json" "$W/ext/pc_b_good.json" "$W/ext/pc_c_good.json" harness-target
printf '%s' '{"excluded":[{"class":"harness-target","peeked":1}], "outOfScope": []}' > "$W/ext/pc_b_poison.json"
run_ext_reject "PART52/peek_completeness(B-truthy-not-True)" "$PEEK_COMPLETENESS_PY" 1 rust "$W/ext/pc_a_good.json" "$W/ext/pc_b_poison.json" "$W/ext/pc_c_good.json" harness-target
printf '%s' '{"excluded":[{"class":"harness-target","peeked":1}], "outOfScope": [{"class":"harness-target"}]}' > "$W/ext/pc_c_poison.json"
run_ext_reject "PART52/peek_completeness(C-truthy-not-True)" "$PEEK_COMPLETENESS_PY" 1 rust "$W/ext/pc_a_good.json" "$W/ext/pc_b_good.json" "$W/ext/pc_c_poison.json" harness-target

# ---- refused_peek_check.py (PART 53) — shape A's DEFECT check is `"outOfScope" in docs["A"]`, a
# PRESENCE test; a mutant degraded to a truthy VALUE test (`if docs["A"].get("outOfScope")`) would wrongly
# accept a present-but-empty `outOfScope` (falsy) as if the key were absent. `rp_a_poison` isolates exactly
# that: the key present, empty.
printf '%s' '{}'                    > "$W/ext/rp_a_good.json"
printf '%s' '{"outOfScope":[{"x":1}]}' > "$W/ext/rp_b_good.json"
printf '%s' '{"outOfScope":[]}'     > "$W/ext/rp_c_good.json"
run_ext_accept "PART53/refused_peek(good)" "$REFUSED_PEEK_PY" 0 rust 2 "$W/ext/rp_a_good.json" 2 "$W/ext/rp_b_good.json" 0 "$W/ext/rp_c_good.json"
printf '%s' '{"outOfScope":[]}'     > "$W/ext/rp_a_poison.json"
run_ext_reject "PART53/refused_peek(A-presence-not-truthy)" "$REFUSED_PEEK_PY" 1 rust 2 "$W/ext/rp_a_poison.json" 2 "$W/ext/rp_b_good.json" 0 "$W/ext/rp_c_good.json"

# ---- peek_route_equality_check.py (PART 54) — the flagship route-equality checker (14 argv positions).
# Three poisons: (B) byte-equality degraded to a LENGTH check — same shape ck83_control's byte-equality fix
# above closes, built the same way (one space swapped for one tab, verified equal length, so only a real
# `a != b` byte comparison catches it); (ok) `is not False` degraded to truthy (`ok: 0`, falsy-but-not-
# False); (incomplete) `is not True` degraded to truthy (`incomplete: 1`, truthy-but-not-True).
printf '%s' '{"ok": false, "incomplete": true, "violations": [], "outOfScope": [{"class":"x","effects":["Exec"]}]}' > "$W/ext/pre_v_good.json"
printf '%s' '{"excluded": []}' > "$W/ext/pre_absent_good.json"
printf '%s' '{"ok": true}'     > "$W/ext/pre_ctl_good.json"
run_ext_accept "PART54/peek_route_equality(good)" "$PEEK_ROUTE_EQ_PY" 0 rust \
  2 "$W/ext/pre_v_good.json" 2 "$W/ext/pre_v_good.json" \
  0 "$W/ext/pre_absent_good.json" \
  0 "$W/ext/pre_ctl_good.json" 0 "$W/ext/pre_ctl_good.json" \
  2 2 2 2
printf '%s' '{"ok": false, "incomplete": true, "violations": [], "outOfScope": [{"class":"x","effects":["Exec"]}]}' > "$W/ext/pre_scan_v.json"
printf '%s' $'{"ok": false,\t"incomplete": true, "violations": [], "outOfScope": [{"class":"x","effects":["Exec"]}]}' > "$W/ext/pre_gate_v.json"
run_ext_reject "PART54/peek_route_equality(byte-not-length-equal)" "$PEEK_ROUTE_EQ_PY" 1 rust \
  2 "$W/ext/pre_scan_v.json" 2 "$W/ext/pre_gate_v.json" \
  0 "$W/ext/pre_absent_good.json" \
  0 "$W/ext/pre_ctl_good.json" 0 "$W/ext/pre_ctl_good.json" \
  2 2 2 2
printf '%s' '{"ok": 0, "incomplete": true, "violations": [], "outOfScope": [{"class":"x","effects":["Exec"]}]}' > "$W/ext/pre_ok0.json"
run_ext_reject "PART54/peek_route_equality(ok-falsy-not-False)" "$PEEK_ROUTE_EQ_PY" 1 rust \
  2 "$W/ext/pre_ok0.json" 2 "$W/ext/pre_ok0.json" \
  0 "$W/ext/pre_absent_good.json" \
  0 "$W/ext/pre_ctl_good.json" 0 "$W/ext/pre_ctl_good.json" \
  2 2 2 2
printf '%s' '{"ok": false, "incomplete": 1, "violations": [], "outOfScope": [{"class":"x","effects":["Exec"]}]}' > "$W/ext/pre_inc1.json"
run_ext_reject "PART54/peek_route_equality(incomplete-truthy-not-True)" "$PEEK_ROUTE_EQ_PY" 1 rust \
  2 "$W/ext/pre_inc1.json" 2 "$W/ext/pre_inc1.json" \
  0 "$W/ext/pre_absent_good.json" \
  0 "$W/ext/pre_ctl_good.json" 0 "$W/ext/pre_ctl_good.json" \
  2 2 2 2

# ---- exec_capability_check.py (PART 66) — `"Exec" not in got` degraded to `not got` (truthy-degrade:
# a non-empty-but-wrong effect set would wrongly pass) on BOTH the must-be-Exec and must-NOT-be-Exec arms.
printf '%s' '{"functions": [{"fn":"armed","inferred":["Exec"]}, {"fn":"noExecFn","inferred":["Clock"]}]}' > "$W/ext/ec_good.json"
run_ext_accept "PART66/exec_capability(good)" "$EXEC_CAP_PY" 0 rust "$W/ext/ec_good.json" armed=Exec noExecFn=noExec
printf '%s' '{"functions": [{"fn":"armed","inferred":["Net"]}, {"fn":"noExecFn","inferred":["Clock"]}]}' > "$W/ext/ec_poison1.json"
run_ext_reject "PART66/exec_capability(Exec-membership)" "$EXEC_CAP_PY" 1 rust "$W/ext/ec_poison1.json" armed=Exec noExecFn=noExec
printf '%s' '{"functions": [{"fn":"armed","inferred":["Exec"]}, {"fn":"noExecFn","inferred":["Exec"]}]}' > "$W/ext/ec_poison2.json"
run_ext_reject "PART66/exec_capability(noExec-membership)" "$EXEC_CAP_PY" 1 rust "$W/ext/ec_poison2.json" armed=Exec noExecFn=noExec

# ---- only_check.py (PART 49) — the AS-EFF-011/AS-EFF-009 collision check. NOT a hypothetical: this
# checker's own header documents candor-rust and candor-java SHIPPING exactly this — a rule disclosed as
# unanswerable and evaluated anyway, printing BOTH codes. The poison reproduces that shape in `out_short`.
OC_SHORT_GOOD='[AS-EFF-011] model reaches infra via rule `only model -> util`'
OC_FULL_GOOD='gate: ok'
OC_ZERO_GOOD='only nosuch -> util matched NO function under from'
OC_GATE_GOOD='gate refused: only model -> util cannot be evaluated from a report'
run_ext_accept "PART49/only_check(good)" "$ONLY_PY" 0 rust 1 "$OC_SHORT_GOOD" 0 "$OC_FULL_GOOD" 0 "$OC_ZERO_GOOD" 2 "$OC_GATE_GOOD"
OC_SHORT_POISON='[AS-EFF-011] model reaches infra via rule `only model -> util`, also flagged [AS-EFF-009]'
run_ext_reject "PART49/only_check(011-009-collision)" "$ONLY_PY" 1 rust 1 "$OC_SHORT_POISON" 0 "$OC_FULL_GOOD" 0 "$OC_ZERO_GOOD" 2 "$OC_GATE_GOOD"

# ── EMBEDDED-PARTS SURVEY (2026-08-29) ──────────────────────────────────────────────────────────────
# WHY THIS EXISTS. This file's own header scoped itself to "PART 36/37/38/39/83 plus the standalone
# conformance/*.py checkers" and named the ~66 OTHER parts whose comparison is written directly into
# run.sh — bash `[ ]`, inline `python3 -c`, a literal `diff` — as never attacked. Measured today: 68 of
# them are individually addressable via `part.sh --list` once the 5 above and the 13 that map to a
# standalone checker (`check_honesty`=1c, `clause_check`=24, `probe_check`=30, `must_ledger`=42,
# `part_declarations`=44, `file_set_check`=48, `only_check`=49, `incomplete_check`=50,
# `fs_position_check`=51, `peek_completeness_check`=52, `refused_peek_check`=53,
# `peek_route_equality_check`=54, `exec_capability_check`=66 — `skip_ratchet.py` is a 14th standalone
# checker with no addressable id of its own, it runs once at the very end of a full run) are subtracted.
#
# THE TEST: for each of the 68, its verdict-controlling `sys.exit(N if COND else M)` (or the equivalent
# bash test) was replaced with an unconditional pass and the part re-run via `part.sh <id>` on the
# CURRENT, otherwise-unmodified fixtures — the same "replace the body with an unconditional pass, does
# the suite notice" test BACKLOG.md's standalone-checker survey ran, at PART granularity instead of
# per-file. RESULT: 15 of 68 were mechanically neutered this way and EVERY ONE still reported the part's
# own success line with no other row reacting — structurally inevitable, since none of the 68 touches
# this file's extract_pyvar/extract_func/extract_heredoc/extract_oneline_func, but reproduced with real
# exit codes here rather than asserted. 46 of 68 use a comparison SHAPE this file's mechanical neuter
# could not locate (a different `sys.exit` spelling, a bash `[ ]`/`-eq` chain, or one of a THIRD class
# this survey also found — external `gen_*.py` property generators such as
# `gen_chain_idempotence.py`/`gen_trust_monotonicity.py`/`gen_signature_monotonicity.py`/
# `gen_incomplete_dominance.py`/`gen_fs_kind.py`, invoked by PARTs 25/26/28/29/31, NONE of which were in
# BACKLOG's 14-item standalone-checker list and NONE of which are attacked by this file either — reported
# here rather than silently dropped) — UNRESOLVED, not "safe", exactly the distinction this file's own
# canary exists to keep honest. 7 of 68 read STILL-RED after neutering but every one was CONFIRMED, by
# re-running the SAME part on an unmutated run.sh, to fail IDENTICALLY without any mutation applied at
# all (PART 15/12b/12c: `part.sh`'s own documented isolation limit — they read state a neighbouring slice
# builds and cannot be run standalone; PART 16/34/4k/4n: a pre-existing, unrelated divergence live in the
# candor-rust/candor-java checkouts beside this repo at survey time) — INCONCLUSIVE, not "protected": none
# of the 7 demonstrated a second, independent check catching the neutered comparison.
#
# TWO of the 68 are hardened below, chosen for severity the same way the standalone survey chose its
# seven: PART 46 (A CALLER OF A BODY-LESS LOCAL DECLARATION IS NOT PURE — verdict/soundness; this is the
# candor-ts axios cardinal sin's own row) and PART 72 (byte-equality across both gate routes — SPEC §3.1
# ⟨0.24⟩'s MUST, which PART 72's own header states "has sat pre-ledger... no row anywhere in this suite
# has ever asked it" until PART 72 was written — the embedded route-equality flagship, same role as
# PART 54/peek_route_equality_check.py above). Both needed a NEW extraction shape (extract_heredoc,
# extract_oneline_func — see their definitions above) because neither is a bash `NAME='...'` assignment
# or an own-line-`}` function, the only two shapes this file could reach before today.
#
# FIVE MORE hardened below (2026-08-30, TASK 2 of the same survey's follow-on): PART 19 and PART 20, the
# two SOUNDNESS-VEIN verdict rows (the initializer edge and implicit-stringification-across-the-boundary
# cardinal sins, each with real production history — SOUNDNESS-VEIN-initializer-edge.md /
# SOUNDNESS-VEIN-crossing-the-scan-boundary.md); PART 21, the disclosure row (could-not-form-a-key must
# not read pure); PART 22, the completeness row (a chained dep join carries the whole surface, not just
# the effect — the row whose own header names four independent production defects, one per engine); and
# PART 56, the refusal+completeness row found by CORPUS-TESTING THE PUBLISHED 0.30.0 (a peek that must
# survive a fail-closed refusal, AND the mirror `refuse-before-envelope` rule that a refusal with nothing
# to disclose must leave no report at all). The first four are `python3 - ARGS <<'DELIM'` heredocs, the
# same PART 46 shape, extracted the same way; PART 56 is the same shape reading real DIRECTORY trees
# rather than bare file args, so its poison plants files under a synthetic `.candor/` rather than passing
# a path directly.
#
# NOT hardened here, stated explicitly rather than silently, mirroring the standalone survey's own
# boundary: the remaining 9 confirmed-DEFEATED parts (10, 14, 45, 4h, 57, 58, 59, 5b, 80 — disclosure,
# refusal and verdict properties among them, e.g. 58 "an outOfScope entry names the file its function is
# in" and 59 "what a refusal owes its reader"), and the 7 INCONCLUSIVE ones. This is a SURVEY BOUNDARY, not
# a claim the rest are safe — see BACKLOG.md for the full per-part table.
#
# 2026-08-30 (revert-test day, candor-spec's own first): the 46 UNRESOLVED bucket above was never actually
# 46 live unknowns — it was 46 parts the MECHANICAL neuter's exact-text pattern (`sys.exit(N if COND else
# N)`) could not locate, three different reasons bundled under one count. Resolved apart:
#   (a) the FIVE gen_*.py-driven properties (PART 25/26/28/29/31, driving gen_chain_idempotence.py/
#       gen_trust_monotonicity.py/gen_signature_monotonicity.py/gen_incomplete_dominance.py/
#       gen_fs_kind.py) are ALL FIVE now in probe_check.py's own COVERED dict as of 90cee30/7cddc1b —
#       confirmed live here (`python3 probe_check.py`: all 8 properties, these 5 among them, correctly
#       fail under `CANDOR_PROBE_FAULT`), not merely re-asserted. RESOLVED — genuinely backstopped.
#   (b) TWELVE more (67, 69, 71, 73, 74, 75, 76, 77, 78, 79, 81, 82) turned out to share ONE shape the
#       exact-text neuter missed only because of formatting, never a different mechanism: a bash function
#       `pNN() { if [ "$2" = "$3" ]; then <OK-line> else <FAIL-line>; fi; }` (73/74/75/76/77/78/79/81/82 —
#       a straight two-value equality) or a short `[ ]`/`&&` chain of the same shape (67, 69, 71). Hand-
#       generalising the neuter to this shape (`if [ ... ]; then` -> `if true; then`, in a throwaway
#       worktree, restored after each) and re-running `part.sh <id>` reproduced the SAME defeat the
#       original 15/16 showed: every one of the 12 still printed its own MATCH/OK line with zero other
#       row reacting. CONFIRMED DEFEATABLE, joining the 9 already-named-and-unhardened ones above — 21
#       total now known-and-named, not 9.
#   (c) PART 85 (357ace7's peek scope-match property) was checked a DIFFERENT way, not the mechanical
#       neuter: candor-rust was built at `27f4beb^` (the commit immediately before the fix this row pins)
#       in a throwaway worktree and substituted in via CANDOR_SCAN_BIN/CANDOR_QUERY_BIN for a full
#       `conformance/run.sh` run, java/ts/swift left at HEAD. Result: rust's row read DIVERGE (exit 0
#       under the scoped rule — the cardinal sin this row exists to catch), java/ts/swift stayed MATCH,
#       and the suite correctly printed `conformance: FAILED`. This is STRONGER evidence than a neuter
#       survives — it is the row catching the actual historical regression, not merely a synthetic
#       unconditional pass going unnoticed — so PART 85 is RESOLVED, not merely reclassified.
# NET: of the 40 parts this file's own count left in the 46-minus-5-gen bucket (recomputed here as 40, not
# 41, against the two IDs the original 15/16-vs-"15" count already disagreed on by one — see (b) above),
# 12 are now CONFIRMED DEFEATABLE and 1 (PART 85) is RESOLVED. 27 remain genuinely UNRESOLVED — never
# attacked by any mechanism, mechanical or manual: 4l, 7, 8, 9, 13, 13b, 15b, 15c, 18, 23, 27, 32, 33, 35,
# 40, 43, 47, 55, 60, 61, 62, 63, 64, 65, 68, 70, 84. None of the 12 newly-confirmed-defeatable are hardened
# with real poison here either, for the same reason the original 9 are not: this is a SURVEY, and hardening
# 21 more bash-comparison parts with per-condition poison (the B1 discipline PART 36-39/83/46/72/19-22/56
# above all follow) is real per-part fixture engineering, not a mechanical follow-on — left for the next
# session rather than rushed. An unresolved part is NOT a passing part; a confirmed-defeatable one is not
# either — both are named here so neither reads as safe by omission.
#
# THE FOLLOW-ON SESSION (2026-08-30, later the same day): the 27 UNRESOLVED above were the ones the
# mechanical AND-chain neuter (this file's own, plus the hand-generalised bash-equality-chain sweep that
# closed 12 more the same day) could not locate a comparison for at all — a genuinely different shape from
# both. Applied the unconditional-pass test BY HAND to all 27, one at a time, via `part.sh <id>` against a
# throwaway mutation of run.sh (reverted after each): find the verdict-controlling comparison — almost
# always a bash function (`p61_row`, `cfg_probe`, `vocab_probe`, `ep_probe`, `dp_probe`, `zm_probe`,
# `perow`, `peurow`, `p18fail`, `check_agents`, `check_polfail`, `p64_row`) or a small number of inline
# `if [ COND ]; then OK else BAD=1; rc=1; fi` blocks sharing one aggregator variable — force it to the pass
# branch, and confirm via a REAL `part.sh` run that the part still prints its own MATCH/OK line with zero
# other row reacting. RESULT: 26 of the 27 are CONFIRMED DEFEATABLE this way, each reproduced with a real
# part.sh run, not asserted: 4l, 7, 8, 13, 13b, 15b, 15c, 18, 23, 27, 32, 33, 35, 40, 43, 47, 55, 60, 61,
# 62, 63, 64, 65, 68, 70, 84. (Several needed a named co-dependency `part.sh` cannot see on its own — PART
# 13/13b/32/33/35/40/84 all read `$GDIR`, built by the unmarked PART 10 slice, so were run as `part.sh 10
# <id>`; 15b/15c similarly needed `10 14 15`; 18 needed `16`. Several of THOSE runs' overall exit code
# stayed 1 even after the neuter, but for a confirmed UNRELATED reason present identically on an unmutated
# run — PART 10's own `candor-rust` vocab arm and PART 16's java containment discovery form both fail on
# this checkout independent of anything here, matching the "live drift in a sibling checkout" class the
# 2026-08-29 survey already named for 4k/16/34/4n — never the part under test.) PART 9 is the exception,
# and not because the test failed to find its comparison: PART 9's own header says so directly — "CONTROLS:
# none — advisory rows print WARN and set nothing" — and a grep of its body confirms zero `rc=1`/`_OK=1`/
# `_BAD=1` anywhere in it. There is no verdict-controlling comparison to invert because PART 9 never
# controls the verdict; it is EQUIVALENT to an unconditional pass by design, not merely defeatable as one.
# So the honest numerator for this batch is 27 of 27: 26 with a comparison proven bypassable and 1 with no
# comparison at all.
#
# TWO OF THE 26 ARE HARDENED BELOW (PART 68, PART 61), chosen for severity against the same yardstick the
# earlier waves used — verdict/disclosure and refusal, both with a measured real-engine history (PART 68
# is the exact "two byte-identical rows" defect measured live on ts/java/swift 2026-08-24; PART 61 is the
# "typo'd effect scored as a confident negative" defect measured on all four engines). PART 68's check.py
# is a NEW extractable shape (a script written to disk via `cat > file <<'PYEOF'` rather than piped via
# `python3 - <<'DELIM'`) but needs no new extraction code: extract_heredoc is delimiter-driven, not
# preamble-driven, so it pulls check.py's body unchanged. PART 61's p61_row is the exact extract_func shape
# already used for ck83_defect/ck83_control, but it shells out to a REAL query binary for its three
# probes rather than reading a JSON document — poisoned here via a tiny STUB command keyed on the effect
# name, not a built engine, the same "no engine needed" discipline PART 19-22/56 use above.
#
# NOT hardened here, named rather than left silent: the other 24 confirmed-defeatable (4l, 7, 8, 13, 13b,
# 15b, 15c, 18, 23, 27, 32, 33, 35, 40, 43, 47, 55, 60, 62, 63, 64, 65, 70, 84) and PART 9's structural gap.
# Several of the highest-severity remaining ones — PART 63 (a sibling report cannot answer for another
# member, MEASURED as a real false-green on candor-query 0.31.0) and PART 62/70 (completeness/refusal) —
# are NOT function-shaped: their comparison is a single inline `if` over exit codes from several REAL
# per-engine invocations computed earlier in the same run.sh slice, which is a real per-part fixture-and-
# stub engineering job (as PART 63's own AND-chain spans five separate un-parameterised call sites, one
# per engine, not one reusable function called five times) rather than a mechanical follow-on from what
# PART 68/61 needed — left for the next session rather than rushed, exactly as the previous survey left its
# own residue rather than silently assuming it safe.
mkdir -p "$W/p46" "$W/p72" "$W/p19" "$W/p20" "$W/p21" "$W/p22" \
  "$W/p56a/rs_dirty/.candor" "$W/p56a/rs_clean/.candor" \
  "$W/p56b/rs_dirty/.candor" "$W/p56b/rs_clean/.candor" \
  "$W/p56g/rs_dirty/.candor" "$W/p56g/rs_clean/.candor"
# ---- PART 46 (PYBL) — condition (a) the under-report: a body-less declaration's caller with no `Unknown`
# must be rejected; condition (b) the CONTROL: a locally-bodied caller charged Unknown-only (or nothing)
# must ALSO be rejected, so the row cannot pass by fabricating Unknown onto everything.
printf '%s' '{"functions": [{"fn": "A.candorUnanswered", "inferred": []}, {"fn": "A.candorAnswered", "inferred": ["Fs"]}]}' > "$W/p46/poison_a.json"
printf '%s' '{"functions": [{"fn": "A.candorUnanswered", "inferred": ["Unknown"]}, {"fn": "A.candorAnswered", "inferred": ["Unknown"]}]}' > "$W/p46/poison_b.json"
printf '%s' '{"functions": [{"fn": "A.candorUnanswered", "inferred": ["Unknown"]}, {"fn": "A.candorAnswered", "inferred": ["Fs"]}]}' > "$W/p46/good.json"
run_exitcode_heredoc "PART46/PYBL(unanswered-must-carry-Unknown)" PYBL 1 "$W/p46/poison_a.json" /nonexistent /nonexistent /nonexistent
run_exitcode_heredoc "PART46/PYBL(control-must-not-be-Unknown-only)" PYBL 1 "$W/p46/poison_b.json" /nonexistent /nonexistent /nonexistent
run_exitcode_heredoc_accept "PART46/PYBL(good)" PYBL 0 "$W/p46/good.json" /nonexistent /nonexistent /nonexistent
# ---- PART 72 (eq72) — the byte-equality primitive itself: it must diverge on a genuine content
# difference (here, a superset — guards against a `<=`/subset-style degrade of `a == b`) and read equal
# on two byte-identical documents.
printf '%s' '{"ok": true, "outOfScope": ["x"]}' > "$W/p72/a.json"
printf '%s' '{"ok": true, "outOfScope": ["x", "y"]}' > "$W/p72/b_superset.json"
printf '%s' '{"ok": true, "outOfScope": ["x"]}' > "$W/p72/a_copy.json"
run_stdout_oneline_func "PART72/eq72(superset-must-diverge)" eq72 '^diverge:' "$W/p72/a.json" "$W/p72/b_superset.json"
run_stdout_oneline_func "PART72/eq72(identical-must-be-equal)" eq72 '^equal$' "$W/p72/a.json" "$W/p72/a_copy.json"

# ---- PART 19 (PYIE) — the initializer-edge soundness vein: a consumer that reaches a chained dependency's
# effectful initializer must not read pure. The heredoc's own `engines` list always includes `java` at
# argv[1] regardless of which other engines are built, so a java-only poison/good pair exercises the real
# comparison without needing rust/ts/swift fixtures. Poison A is the exact defect this row exists to catch
# (the consumer reads pure); poison B is the near-miss one field over — `Unknown`-only, still no CONCRETE
# effect — proving the row does not accept a bare hedge as the initializer's effect reaching the consumer.
printf '%s' '{"functions": [{"fn": "app.A", "inferred": []}]}' > "$W/p19/poison_pure.json"
printf '%s' '{"functions": [{"fn": "app.A", "inferred": ["Unknown"]}]}' > "$W/p19/poison_unknown_only.json"
printf '%s' '{"functions": [{"fn": "app.A", "inferred": ["Fs"]}]}' > "$W/p19/good.json"
run_exitcode_heredoc "PART19/PYIE(consumer-reads-pure)"      PYIE 1 "$W/p19/poison_pure.json" /nonexistent /nonexistent /nonexistent
run_exitcode_heredoc "PART19/PYIE(unknown-only-not-enough)"  PYIE 1 "$W/p19/poison_unknown_only.json" /nonexistent /nonexistent /nonexistent
run_exitcode_heredoc_accept "PART19/PYIE(good)"              PYIE 0 "$W/p19/good.json" /nonexistent /nonexistent /nonexistent

# ---- PART 20 (PYSB) — the implicit-stringification soundness vein, same shape and same java-only-arm
# strategy as PART 19 above (a different heredoc, an identical `effectful()` comparison).
printf '%s' '{"functions": [{"fn": "app.S.show", "inferred": []}]}' > "$W/p20/poison.json"
printf '%s' '{"functions": [{"fn": "app.S.show", "inferred": ["Clock"]}]}' > "$W/p20/good.json"
run_exitcode_heredoc "PART20/PYSB(consumer-reads-pure)" PYSB 1 "$W/p20/poison.json" /nonexistent /nonexistent /nonexistent
run_exitcode_heredoc_accept "PART20/PYSB(good)"         PYSB 0 "$W/p20/good.json" /nonexistent /nonexistent /nonexistent

# ---- PART 21 (PYUK) — could-not-form-a-key must disclose, not read pure. `engines` always includes java
# at argv[1] keyed on fn "app.Go.run" (the other args select the java-only arm: rust/ts/swift paths set to
# a nonexistent file, their "present" flags set to "0" so they are legitimately skipped rather than scored
# as a missing arm). Poison holds the function PRESENT with no Unknown and no concrete effect (`verdict()`'s
# "present but reads pure" branch — a value corruption, not the ABSENT-from-report branch this row also
# tests, which is a different, already-covered defect shape); good discloses via `Unknown` with a reason.
printf '%s' '{"functions": [{"fn": "app.Go.run", "inferred": []}]}' > "$W/p21/poison.json"
printf '%s' '{"functions": [{"fn": "app.Go.run", "inferred": ["Unknown"], "unknownWhy": "dispatch:lib.Store#save"}]}' > "$W/p21/good.json"
run_exitcode_heredoc "PART21/PYUK(present-but-reads-pure)" PYUK 1 "$W/p21/poison.json" /nonexistent /nonexistent 0 0 /nonexistent 0
run_exitcode_heredoc_accept "PART21/PYUK(good)"            PYUK 0 "$W/p21/good.json" /nonexistent /nonexistent 0 0 /nonexistent 0

# ---- PART 22 (PYDS) — a chained dep join carries the whole surface, not just the effect. Uses the rust
# triple (argv 1-3: dep, app, present) with java/ts/swift all marked absent. TWO independent poisons, since
# `check()` has two distinct failure branches this row must tell apart: an EFFECT dropped by the join
# (`Exec` present in the dep, absent from the consumer) and a LITERAL SURFACE dropped while the effect
# itself still travels (`paths` emptied while `cmds` and both effects survive) — the second is the sharper
# near-miss, since a comparison that only checked effect-set equality would pass it.
printf '%s' '{"functions": [{"fn": "work", "inferred": ["Fs","Exec"], "paths": ["/surface/path"], "cmds": ["surfacecmd"]}]}' > "$W/p22/dep.json"
printf '%s' '{"functions": [{"fn": "go", "inferred": ["Fs","Exec"], "paths": [], "cmds": ["surfacecmd"]}]}' > "$W/p22/app_poison_paths.json"
printf '%s' '{"functions": [{"fn": "go", "inferred": ["Fs"], "paths": ["/surface/path"], "cmds": ["surfacecmd"]}]}' > "$W/p22/app_poison_effect.json"
printf '%s' '{"functions": [{"fn": "go", "inferred": ["Fs","Exec"], "paths": ["/surface/path"], "cmds": ["surfacecmd"]}]}' > "$W/p22/app_good.json"
run_exitcode_heredoc "PART22/PYDS(surface-dropped-paths)" PYDS 1 "$W/p22/dep.json" "$W/p22/app_poison_paths.json" 1 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0
run_exitcode_heredoc "PART22/PYDS(effect-dropped)"        PYDS 1 "$W/p22/dep.json" "$W/p22/app_poison_effect.json" 1 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0
run_exitcode_heredoc_accept "PART22/PYDS(good)"           PYDS 0 "$W/p22/dep.json" "$W/p22/app_good.json" 1 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0 /nonexistent /nonexistent 0

# ---- PART 56 (PY56) — a target with no analyzable source still reads what it excluded, found by
# corpus-testing the PUBLISHED 0.30.0. Reads a real DIRECTORY tree (`<base>/<eng>_<arm>/.candor/
# report*.json`), not a bare file argument, so the poison plants files rather than passing paths. Only the
# rust arm is populated (ts/sw marked absent via argv[8]/argv[9] = "0"), matching PART 19-22's
# one-engine-is-enough strategy. TWO independent poisons for the two failure branches this row's own
# comment calls out as separately load-bearing: (a) the corpus-found defect itself — a DIRTY refusal
# (exit 2) whose report exists but whose `outOfScope` is empty, so the peek that justified the whole rung
# never reaches the reader — and (b) its mirror, a CLEAN refusal that nonetheless LEFT A REPORT, which
# `run.sh`'s own comment calls the `refuse-before-envelope` rule (§3.1 is quantified over "any report a
# scan produced"). Good holds the real shape: dirty exit 2 WITH a populated report, clean exit 2 with NO
# report at all — the asymmetry is deliberate, not an oversight, so the accept-known-good leg is the only
# thing standing between "hardened" and "encoded my own misreading of the asymmetry as ground truth".
printf '%s' '{"outOfScope": [{"fn":"build::main","path":"build.rs","effects":["Exec"]}]}' > "$W/p56g/rs_dirty/.candor/report.rs.scan.json"
printf '%s' '{"outOfScope": []}' > "$W/p56a/rs_dirty/.candor/report.rs.scan.json"
printf '%s' '{"outOfScope": [{"fn":"build::main","path":"build.rs","effects":["Exec"]}]}' > "$W/p56b/rs_dirty/.candor/report.rs.scan.json"
printf '%s' '{"outOfScope": []}' > "$W/p56b/rs_clean/.candor/report.rs.scan.json"
run_exitcode_heredoc "PART56/PY56(dirty-peek-empty)"      PY56 1 "$W/p56a" 2 2 x x x x 0 0
run_exitcode_heredoc "PART56/PY56(clean-left-a-report)"   PY56 1 "$W/p56b" 2 2 x x x x 0 0
run_exitcode_heredoc_accept "PART56/PY56(good)"           PY56 0 "$W/p56g" 2 2 x x x x 0 0

# ---- PART 68 (PYEOF/check.py) — 2026-08-30 EMBEDDED-PARTS SURVEY, second wave: a verdict row must carry
# the unit it is about (SPEC §2 ⟨0.32⟩) — the MEASURED 2026-08-24 defect on ts/java/swift, two BYTE-
# IDENTICAL violation rows for two distinct members sharing a name, a reader cannot tell apart. Unlike
# PART 46/72/19-22/56 above, check.py is not a `python3 - ARGS <<'DELIM'` pipe but a script WRITTEN to
# disk via `cat > "$P68/check.py" <<'PYEOF'` and invoked by path — extract_heredoc pulls it unchanged,
# since a heredoc body is lexically unambiguous regardless of what precedes the `<<'DELIM'`.
# THREE independent near-miss poisons, one per distinct branch check.py can fail on, each isolated from
# the others by giving `rev` the SAME (rule,hash) pairs as the poisoned `twin` so the REV comparison
# (a different, already-independently-tested branch) cannot fire first and mask which check caught it:
#   (a) THE HISTORICAL DEFECT ITSELF — twin's two rows are BYTE-IDENTICAL, same hash included.
#   (b) near-miss ONE FIELD OVER — the two rows are textually distinct (different `detail`) but share the
#       SAME hash: proves the hash-UNIQUENESS check is live independently of the whole-row-equality one,
#       which (a) alone cannot show (a dict-equality-only regression would still catch (a) but not (b)).
#   (c) near-miss on ORDER — two rows with correct, DISTINCT hashes but out of identity order: proves the
#       sort-key clause (the OTHER half of §2 ⟨0.32⟩'s MUST, the one PART 63 cannot see) is asked at all.
# `one`/`nohash` stay at their real accept-known-good shape in every poison call, since neither branch
# under test here touches them — changing an unrelated arg would not be a near-miss, it would be noise.
# FALSIFIED against a plausible regression (deleting the byte-identity AND hash-uniqueness checks from a
# scratch copy of check.py): poisons (a) and (b) both flip from CAUGHT to WRONGLY-ACCEPTED, and (c) is
# unaffected — proof the three poisons discriminate the branches they claim to, not merely trip on the
# REV check by coincidence (an earlier draft's poisons did exactly that before `rev` was pinned to match).
mkdir -p "$W/p68"
p68row() {   # $1 hash-or-empty ; $2 detail
  if [ -n "$1" ]; then printf '{"rule":"AS-EFF-006","fn":"go","effects":["Exec"],"detail":"%s","hash":"%s"}' "$2" "$1"
  else printf '{"rule":"AS-EFF-006","fn":"go","effects":["Exec"],"detail":"%s"}' "$2"; fi
}
printf '{"violations":[%s,%s]}' "$(p68row a#go D)" "$(p68row b#go D)"       > "$W/p68/good_twin.json"
printf '{"violations":[%s,%s]}' "$(p68row a#go D)" "$(p68row b#go D)"       > "$W/p68/good_rev.json"
printf '{"violations":[%s]}'    "$(p68row a#go D)"                          > "$W/p68/good_one.json"
printf '{"violations":[%s]}'    "$(p68row "" D)"                            > "$W/p68/good_nohash.json"
printf '{"violations":[%s,%s]}' "$(p68row a#go D)" "$(p68row a#go D)"       > "$W/p68/poison_identical_twin.json"
printf '{"violations":[%s,%s]}' "$(p68row a#go D)" "$(p68row a#go D)"       > "$W/p68/poison_identical_rev.json"
printf '{"violations":[%s,%s]}' "$(p68row a#go first)" "$(p68row a#go second)" > "$W/p68/poison_samehash_twin.json"
printf '{"violations":[%s,%s]}' "$(p68row a#go first)" "$(p68row a#go second)" > "$W/p68/poison_samehash_rev.json"
printf '{"violations":[%s,%s]}' "$(p68row b#go first)" "$(p68row a#go second)" > "$W/p68/poison_order_twin.json"
printf '{"violations":[%s,%s]}' "$(p68row b#go first)" "$(p68row a#go second)" > "$W/p68/poison_order_rev.json"
run_exitcode_heredoc "PART68/PYEOF(byte-identical-defect)" PYEOF 1 L "$W/p68/poison_identical_twin.json" "$W/p68/poison_identical_rev.json" "$W/p68/good_one.json" "$W/p68/good_nohash.json"
run_exitcode_heredoc "PART68/PYEOF(same-hash-distinct-text)" PYEOF 1 L "$W/p68/poison_samehash_twin.json" "$W/p68/poison_samehash_rev.json" "$W/p68/good_one.json" "$W/p68/good_nohash.json"
run_exitcode_heredoc "PART68/PYEOF(rows-out-of-identity-order)" PYEOF 1 L "$W/p68/poison_order_twin.json" "$W/p68/poison_order_rev.json" "$W/p68/good_one.json" "$W/p68/good_nohash.json"
run_exitcode_heredoc_accept "PART68/PYEOF(good)" PYEOF 0 L "$W/p68/good_twin.json" "$W/p68/good_rev.json" "$W/p68/good_one.json" "$W/p68/good_nohash.json"

# ---- PART 61 (p61_row) — 2026-08-30 EMBEDDED-PARTS SURVEY: a typo'd effect name must be REFUSED (exit 2),
# never silently answered (SPEC §3.1) — the same "unanswerable must be disclosed" shape as ⟨0.24⟩'s §3.1
# ruling, applied to `path`'s vocabulary guard. p61_row is a bash FUNCTION (extract_func's exact shape, a
# `name() {` opener with the closing `}` alone at column 0) that shells out to a REAL query binary three
# times ("$@" caller Fs/Fsz/Net --report …) and reduces each call to an exit code — there is no JSON
# document to poison here, only three exit codes, so the "poison" is a tiny STUB standing in for "$@" that
# returns a controlled code per effect name (keyed on argv[2], the effect), never a built engine. NEAR-MISS
# in the same sense as the JSON checkers above: exactly ONE of the three expected codes (0/2/0) is wrong.
#   (a) THE DEFECT ITSELF — the typo'd effect (`Fsz`) answers 0 instead of refusing at 2: a typo silently
#       scored as a confident negative, the exact live-engine bug PART 61 exists to catch.
#   (b) the CONTROL's own failure mode — the KNOWN-ABSENT effect (`Net`) also refuses at 2: indistinguishable
#       from "path always refuses", the failure PART 61's own header says the known-absent row exists to rule
#       out. Isolated from (a): only ONE field changes per call, the real effect stays 0 in both.
# FALSIFIED against a plausible regression (dropping the `$absent = 0` clause from a scratch copy of
# p61_row, keeping `$real`/`$typo`): poison (b) flips from CAUGHT (P61_BAD=1) to WRONGLY-ACCEPTED
# (P61_BAD=0); poison (a) and the accept-known-good leg are unaffected, proving (b) tests the clause (a)
# cannot see.
mkdir -p "$W/p61"
P61_SRC="$(extract_func p61_row "$RUN_SH")"
require_extracted "$P61_SRC" "could not extract p61_row from $RUN_SH — nothing to test"
printf '%s\n' "$P61_SRC" > "$W/p61/p61_row.sh"
cat > "$W/p61/stub.sh" <<'STUBEOF'
#!/bin/sh
# args: caller <Effect> --report <path> — exit code keyed on $2 (the effect name) via env vars, standing
# in for a real query binary so this row needs no built engine.
eff="$2"
case "$eff" in
  Fs)  exit "${STUB_REAL:-0}" ;;
  Fsz) exit "${STUB_TYPO:-2}" ;;
  Net) exit "${STUB_ABSENT:-0}" ;;
esac
exit 9
STUBEOF
chmod +x "$W/p61/stub.sh"
cat > "$W/p61/runner.sh" <<'RUNEOF'
#!/bin/bash
source "$1/p61_row.sh"
P61_OUT=""; P61_BAD=0; rc=0
p61_row eng /dev/null "$1/stub.sh"
echo "P61_BAD=$P61_BAD"
RUNEOF
chmod +x "$W/p61/runner.sh"
run_p61() {   # $1 label ; $2 want P61_BAD(0=accept/1=reject) ; $3 STUB_REAL ; $4 STUB_TYPO ; $5 STUB_ABSENT
  local label="$1" want="$2"
  local out; out="$(STUB_REAL="$3" STUB_TYPO="$4" STUB_ABSENT="$5" bash "$W/p61/runner.sh" "$W/p61" 2>&1)"
  local got; got="$(printf '%s\n' "$out" | grep -o 'P61_BAD=[01]' | tail -1 | cut -d= -f2)"
  if [ "$got" = "$want" ]; then record PASS "$label"
  else record BROKEN "$label" "expected P61_BAD=$want; runner said: $out"; fi
}
run_p61 "PART61/p61_row(typo-not-refused)"    1 0 0 0
run_p61 "PART61/p61_row(known-absent-broken)" 1 0 2 2
run_p61 "PART61/p61_row(good)"                0 0 2 0

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
