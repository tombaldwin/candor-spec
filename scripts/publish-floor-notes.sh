#!/usr/bin/env bash
# publish-floor-notes.sh — REFRESH THE FLOOR'S GITHUB RELEASE with the patch-cycle CHANGELOG sections
# that `release.sh` never gets to publish.
#
#   bash scripts/publish-floor-notes.sh              # updates the live GitHub release
#   bash scripts/publish-floor-notes.sh --dry-run    # prints the body it would publish, no network call
#
# ── THE GAP THIS CLOSES ──────────────────────────────────────────────────────────────────────────────
#
# candor-spec is the one repo in the family whose GitHub release is tagged at the CONTRACT version
# (`v0.33`), not the family BUILD version (`v0.33.1`) — deliberately: the spec has no patch component,
# and SPEC.md's versioning policy is explicit that a patch changes neither tier's contract. `release.sh`
# tags candor-spec `v$SPEC` and correctly SKIPS it once that tag exists (`rel()`'s
# `gh release view "$tag" … already released` branch) — that skip is right, not a bug: cutting a second
# `v0.33` release, or a `v0.33.1` tag, would fabricate a contract axis that does not exist.
#
# But `release-stage.sh` still opens `## [0.33.1] — <date>` in CHANGELOG.md for every patch build,
# because CHANGELOG headings are keyed to the family build version, not the floor — and every patch
# cycle's conformance rows, fixes and soundness notes land inside that section. Once `v0.33`'s release
# already exists, nothing in the ladder ever looks at that section again: it sits in CHANGELOG.md,
# correctly written, permanently unpublished. Surfaced by 0.33.1 (PARTs 71-76, six new conformance rows,
# added in the CHANGELOG the same day `release.sh` skipped candor-spec for exactly this reason).
#
# ── WHY THIS IS THE RIGHT FIX, AND WHAT IT DELIBERATELY DOES NOT DO ─────────────────────────────────
#
# The three-axis distinction (spec/contract vs build id vs crate semver) is deliberate and this script
# does not blur it:
#   - it NEVER creates or moves a git tag — `v0.33` stays exactly what it was, still the contract's own
#     release point;
#   - it NEVER touches SPEC.md, a rung marker, or `spec-bump.sh`'s territory — the floor does not move;
#   - it edits ONLY the release NOTES (`gh release edit -F`, which touches nothing but the body) of the
#     release that already exists for that floor.
# The contract release becomes what its own tag already implies: the one page describing everything
# that happened while 0.33 was the floor, not a snapshot frozen at the day it was cut. That is a better
# fit than the two alternatives considered:
#   - a decoupled build tag on candor-spec (`v0.33+build.1`) would put a patch-shaped axis on the one tag  ⟨0.33⟩
#     this repo deliberately has none of, and would need release.sh/release-verify.sh (both
#     umbrella-owned) to learn a second tag scheme for one repo out of seven;
#   - rolling the notes forward into the next contract rung's release would publish them dated and
#     described as work done under a version they were not shipped with, for however long the next rung
#     takes to arrive — arbitrarily long, since a patch cycle has no schedule tied to the next rung.
#
# ── WHAT IT DOES ─────────────────────────────────────────────────────────────────────────────────────
#
# 1. Reads the floor from SPEC.md's `**Version X.Y**` header.
# 2. Confirms a GitHub release already exists at `vX.Y` — this script REFRESHES an existing release, it
#    never creates one; if the floor has no release yet, that is `release.sh`'s job, not this script's.
# 3. Collects every CHANGELOG.md section whose heading is `## [X.Y.<patch>]` for that floor (in the
#    file's existing order, which is newest-first) and concatenates them into one body.
# 4. Writes that body over the release's existing notes (`gh release edit -F`), changing nothing else.
#
# Idempotent: re-running with no new CHANGELOG.md section is a no-op (same bytes republished). Safe to
# run after every patch-cycle commit that adds a `## [X.Y.<patch>]` section under the current floor —
# there is no harm in running it more than once, and no harm in running it before the section it would
# pick up exists (it refuses rather than publishing an empty or stale body).
#
# What the umbrella would need to make this automatic rather than a manual step: `release.sh` could call
# this script (or fold its logic in) right after the `rel candor-spec "v$SPEC" …` line skips — that line
# already runs in the exact state (`v$SPEC` released, a patch just staged) this script exists for. Not
# done here because it means editing `release.sh`, which candor-spec does not own.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
REPO="${CANDOR_SPEC_REPO:-tombaldwin/candor-spec}"
CL="$ROOT/CHANGELOG.md"
DRY=0
for a in "$@"; do case "$a" in --dry-run) DRY=1 ;; esac; done

FLOOR="$(grep -oE '^\*\*Version [0-9]+\.[0-9]+' "$ROOT/SPEC.md" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)"
[ -n "$FLOOR" ] || { echo "publish-floor-notes: could not read the floor version from SPEC.md's '**Version X.Y**' header" >&2; exit 2; }
TAG="v$FLOOR"

if [ "$DRY" -eq 0 ]; then
  gh release view "$TAG" -R "$REPO" >/dev/null 2>&1 || {
    echo "publish-floor-notes: no GitHub release exists at $TAG on $REPO yet — that is release.sh's job, not this script's. Nothing to refresh." >&2
    exit 3
  }
fi

[ -f "$CL" ] || { echo "publish-floor-notes: no CHANGELOG.md at $CL" >&2; exit 2; }

# Sections keyed `## [X.Y.<patch>]` for the current floor, in file order (newest first — the file is
# written that way). A floor prefix match, not an exact-version match: this is meant to pick up EVERY
# patch section ever staged under this floor, so a second and third patch both fold in on re-run.
OUT="$(mktemp "${TMPDIR:-/tmp}/floor-notes.XXXXXX")"
trap 'rm -f "$OUT"' EXIT
awk -v pfx="## [$FLOOR." '
  index($0, pfx) == 1 { f = 1; if (n++) print ""; print; next }
  /^## / { f = 0 }
  f { print }
' "$CL" > "$OUT"

grep -q '[^[:space:]]' "$OUT" || {
  echo "publish-floor-notes: no non-empty '## [$FLOOR.<patch>]' section found in CHANGELOG.md — nothing to publish. (If a patch just landed, check release-stage.sh actually opened a section and it has a body.)" >&2
  exit 3
}

if [ "$DRY" -eq 1 ]; then
  cat "$OUT"
  exit 0
fi

gh release edit "$TAG" -R "$REPO" -F "$OUT" \
  && echo "publish-floor-notes: $REPO $TAG notes refreshed — https://github.com/$REPO/releases/tag/$TAG"
