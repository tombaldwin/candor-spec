#!/usr/bin/env bash
# conformance/canary/cannot-fail.sh — DELIBERATELY BROKEN. DO NOT "FIX" THIS FILE.
#
# This is the mutation gate's own liveness control (see conformance/mutation-gate.sh). It carries the
# REAL nested-single-quote bug measured 2026-08-28 in PART 80 and PART 83's first drafts (SOUNDNESS-LOG,
# BACKLOG.md "Three instrument failures in one session"), not a synthetic stand-in — calibrating the
# instrument against a copy of the bug proves nothing about the real thing (AGENT-CORPUS-BRIEF.md rule
# 6 / rule 9: "0 violations is not evidence until the instrument is proven able to fail").
#
# THE BUG: an unescaped apostrophe nested inside a bash single-quoted `python3 -c '...'` body. Bash
# single quotes have no escape mechanism — the string ends at the very next literal `'`, full stop. Below,
# `d.get('zeroMatch')` inside the FAIL-message line closes the outer quote early, leaves the bare word
# `zeroMatch` sitting unquoted (its own quote characters stripped), then reopens a new quoted segment for
# the rest. The reassembled Python bash actually hands the interpreter is (verify with
# `bash -c 'source conformance/canary/cannot-fail.sh; declare -f cannot_fail_check'` — the ORIGINAL text is
# preserved for display, so this only shows up by actually invoking it, exactly like the real 2026-08-28
# bug did):
#
#   import json, sys
#   d = json.load(open(sys.argv[1]))
#   if d.get("ok") is not False:
#       print("FAIL: expected ok=false, got " + repr(d.get(zeroMatch)))
#       sys.exit(1)
#   sys.exit(0)
#
# `ok = d.get("ok")`-style checks are UNAFFECTED (that key is double-quoted, safe) — only the
# message-building line inside the failure branch is corrupted, which is exactly why the real bug hid: a
# document with `ok: false` never enters that branch, so the checker looks perfectly healthy on every
# passing input forever. Only a POISON document (one with `ok` NOT false) walks into the broken branch,
# where `zeroMatch` is an undefined Python name — a NameError, printed as a raw traceback on stderr, with
# no `FAIL:` line ever produced. That is the failure this canary exists to prove the gate can still catch:
# not a crash dressed as a clean run, but a crash dressed as NOTHING AT ALL where a FAIL was owed.
#
# If this file is ever edited to use a heredoc (or any other safe idiom) instead, IT STOPS BEING BROKEN —
# which is a DIFFERENT kind of failure for the gate to catch (see mutation-gate.sh's own "canary must be
# found broken, in BOTH directions" check). Do not "fix" this file; if it needs to change, change what bug
# it demonstrates, deliberately, and update the comment above to match.

cannot_fail_check() {   # $1 = document that must be rejected unless ok:false
  python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
if d.get("ok") is not False:
    print("FAIL: expected ok=false, got " + repr(d.get('zeroMatch')))
    sys.exit(1)
sys.exit(0)
' "$1"
}
