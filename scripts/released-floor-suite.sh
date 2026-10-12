#!/usr/bin/env bash
# released-floor-suite.sh — WHICH candor-spec COMMIT WAS A PUBLISHED FAMILY BUILD RELEASED UNDER?
#
#   bash scripts/released-floor-suite.sh <version> <published-at> [<rev>]   # prints the commit sha
#   bash scripts/released-floor-suite.sh --selftest                        # calibrates against real tags
#
# `conformance.yml`'s `released-floor` job runs the PUBLISHED engines (the latest candor-java release jar,
# the latest crates.io candor-scan/candor-query) against the conformance suite. Which suite is the whole
# question, and this script answers it.
#
# ── THE DEFECT THIS REPLACES ─────────────────────────────────────────────────────────────────────────
#
# The job used to pin the suite with `git describe --tags --abbrev=0`. candor-spec is tagged only at the
# CONTRACT version (`v0.40`), never at a family build (`v0.40.6`) — deliberately; see release.sh's
# `rel candor-spec "v$SPEC"` and scripts/publish-floor-notes.sh. So for a whole patch line the floor ran
# the published v0.40.6 engines against the suite as of v0.40.0, and every engine fix that the suite was
# updated to pin read as a regression. Measured: run 38253719502 (2026-10-12), rust 0.40.6 against v0.40's
# PART 10 `macrohidden`, which R1004 (0.40.1) correctly started expanding — `DIVERGE [rust(macro)] … saw
# []`. The selection pointed at the wrong commit, in the false-RED direction, for six patch releases.
#
# ── WHAT IT SELECTS, AND WHY THAT IS THE RIGHT QUESTION ───────────────────────────────────────────────
#
# The suite the build was RELEASED UNDER: the last commit on candor-spec's first-parent line whose
# committer date is at or before the moment the build was published. The release ladder runs four-way
# conformance against candor-spec's HEAD after the last edit and before publishing, so that commit is the
# contract the published engines were last measured against and are owed. A LATER suite is not: main
# accrues parts that pin behaviour in unreleased engine work, which the published binary cannot have, so
# floor-checking against main fails the released engine for being released.
#
# Calibration, not assertion: `release.sh` creates the spec's `v$SPEC` tag on candor-spec's HEAD at the
# moment of a contract cut, so for every `vX.Y.0` the tag IS the ground truth this script must reproduce
# from the publish time alone. `--selftest` checks exactly that for every contract tag it can price.
#
# ── WHY IT REFUSES RATHER THAN GUESSES ───────────────────────────────────────────────────────────────
#
# A time anchor alone could drift — a local commit dated before the publish but pushed after it, or a
# patch cut that never staged candor-spec. So the selected commit must also AGREE with the release on a
# marker the ladder writes: its CHANGELOG.md's newest released heading must be `## [<version>]`
# (release-stage.sh's `_stage_changelogs.py` opens it). Too OLD (the build's own section is not there yet)
# and too NEW (the next build's section is already open) both refuse. A refusal exits 2 with no sha on
# stdout, so the caller cannot `git checkout ""` and run whatever it happens to be standing on.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

refuse() { echo "released-floor-suite: REFUSING — $*" >&2; exit 2; }

select_suite() { # $1 version ; $2 published-at (ISO 8601) ; $3 rev
  local ver="$1" at="$2" rev="$3" sel top
  [[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || refuse "version '$ver' is not X.Y.Z"
  # A strict ISO-8601 shape, because `git rev-list --before` takes approxidate and reads garbage as NOW —
  # which would select HEAD, the exact suite this script exists not to pick.
  [[ "$at" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$ ]] \
    || refuse "published-at '$at' is not an ISO-8601 timestamp"
  git -C "$REPO" rev-parse --verify -q "$rev^{commit}" >/dev/null || refuse "rev '$rev' does not resolve"
  sel="$(git -C "$REPO" rev-list -1 --first-parent --before="$at" "$rev")"
  [ -n "$sel" ] || refuse "no commit on $rev's first-parent line is dated at or before $at"
  top="$(git -C "$REPO" show "$sel:CHANGELOG.md" 2>/dev/null \
         | sed -n 's/^## \[\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\)\].*/\1/p' | head -1)"
  [ -n "$top" ] || refuse "CHANGELOG.md at ${sel:0:12} has no released '## [X.Y.Z]' heading"
  if [ "$top" != "$ver" ]; then
    refuse "the last commit at or before $at is ${sel:0:12}, whose CHANGELOG's newest released section is
  [$top], not [$ver] — the time anchor and the release ladder disagree about which suite $ver shipped
  under. Either candor-spec was not staged for $ver (a scoped cut), or a commit is dated across the
  publish. Find the commit by hand and dispatch with it:
    gh workflow run conformance.yml -R tombaldwin/candor-spec --ref main -f floor_suite=<sha>"
  fi
  printf '%s\n' "$sel"
}

selftest() {
  local fails=0 n=0 tag ver at want got
  # The ONE ground truth: release.sh tags v$SPEC on spec HEAD while publishing X.Y.0. Each row is a contract
  # tag and its candor-java vX.Y.0 publishedAt (gh release view vX.Y.0 -R tombaldwin/candor-java), frozen
  # here so the selftest needs no network and cannot drift with a re-run.
  while read -r tag ver at; do
    [ -n "$tag" ] || continue
    git -C "$REPO" rev-parse -q --verify "$tag^{commit}" >/dev/null || { echo "  - $tag: tag not present here, skipped"; continue; }
    n=$((n+1))
    want="$(git -C "$REPO" rev-parse "$tag^{commit}")"
    got="$(select_suite "$ver" "$at" HEAD 2>/dev/null)" || got="(refused)"
    if [ "$got" = "$want" ]; then echo "  ✔ $ver published $at → ${got:0:12} = $tag"
    else echo "  ✘ $ver published $at → ${got:0:12}, but $tag is ${want:0:12}"; fails=$((fails+1)); fi
  done <<'ROWS'
v0.40 0.40.0 2026-10-08T01:14:13Z
v0.39 0.39.0 2026-09-20T18:50:38Z
v0.38 0.38.0 2026-09-14T21:33:29Z
v0.37 0.37.0 2026-09-13T18:24:17Z
ROWS
  # The refusals must FIRE, or a clean calibration above proves nothing about the guard.
  local r
  for r in "0.40.6 2026-10-08T01:14:13Z|too old: 0.40.0's suite named as 0.40.6's" \
           "0.40.0 2026-10-11T15:05:11Z|too new: 0.40.6's suite named as 0.40.0's" \
           "0.40.6 yesterday|non-ISO time (approxidate would read it)" \
           "0.40|a version with no patch component" \
           "0.40.6 1999-01-01T00:00:00Z|a time before the repo existed"; do
    n=$((n+1))
    # shellcheck disable=SC2086  # the row's first field is deliberately word-split into args
    if ( select_suite ${r%%|*} HEAD ) >/dev/null 2>&1; then
      echo "  ✘ did NOT refuse: ${r#*|}"; fails=$((fails+1))
    else echo "  ✔ refuses: ${r#*|}"; fi
  done
  if [ "$fails" = 0 ] && [ "$n" -ge 5 ]; then echo "released-floor-suite selftest: OK ($n checks)"; return 0; fi
  echo "released-floor-suite selftest: FAILED ($fails of $n)" >&2; return 1
}

case "${1:-}" in
  --selftest) selftest ;;
  ""|-h|--help) sed -n '2,5p' "$0"; exit 2 ;;
  *) [ $# -ge 2 ] || refuse "usage: released-floor-suite.sh <version> <published-at> [<rev>]"
     select_suite "$1" "$2" "${3:-HEAD}" ;;
esac
