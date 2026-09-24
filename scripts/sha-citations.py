#!/usr/bin/env python3
"""sha-citations.py — every commit this register CITES must resolve. Check it, or repair it.

    python3 scripts/sha-citations.py --check     # exit 1 if any citation is dead
    python3 scripts/sha-citations.py --apply     # rewrite dead citations through the commit-maps

WHY THIS EXISTS, measured 2026-09-24. On 2026-09-16 six of the seven repos were rewritten with
`git filter-repo` to redact a private client codebase. Every sha the register had ever cited in those
repos changed. Nothing failed, because **a sha in a markdown table is not checked by anything** — so
the register silently became a document whose evidence could not be followed: of 460 distinct
backticked sha-like tokens in SOUNDNESS.md, **313 no longer resolved anywhere**.

That is not a cosmetic problem. This register's whole claim on a reader is "here is the commit that
closed it"; a row citing a dead sha is indistinguishable, by `grep`, from a row citing a commit that
never existed. It also cost real work: a review agent read `f51eb27` off R372, could not resolve it,
and reported R372 as still open. It is closed — `f51eb27` is `94dc8b5`, "R372 rust: a cfg-twinned
`use` used as a TYPE was resolved by SOURCE ORDER".

THE RECOVERY DATA IS NOT IN ANY CLONE. `git filter-repo` leaves `.git/filter-repo/commit-map` in the
rewritten working copy, and `.git/` is not cloned, not pushed, and not on the second machine. When
this was found, 310 citations were recoverable and existed in exactly one place on one laptop. They
are now committed under `history/commit-maps/` — that copy, not the `.git/` one, is what this script
reads by default, so a fresh clone can repair and verify without privileged local state.

NOT EVERY BACKTICKED HEX TOKEN IS A SHA, and guessing costs a false repair. Three in this register are
not commits at all and are allowlisted BY VALUE with their reason, because a length rule would not
have caught the third:

  305647574         a GitHub WORKFLOW id (`gh workflow list` wfid for integrations.yml)
  34140458495       a GitHub RUN id (a workflow_dispatch run on main)
  d7608ec5a5adc4c4  an `analyzed.digest` value from a coverage-refresh measurement

candor-ts has NO commit-map: it was not rewritten, so its citations never died and need no repair.
An absent map is therefore not an error here — but a dead citation with no map entry IS.
"""
import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent          # candor-spec
FAMILY = ROOT.parent                                            # ~/git
REPOS = ["candor", "candor-spec", "candor-rust", "candor-java",
         "candor-ts", "candor-swift", "candor-agents"]

# Files whose sha citations are load-bearing EVIDENCE. Deliberately NOT the per-repo CHANGELOGs: those
# are published release notes, a rewrite of them edits what was shipped, and their shas are narrative
# rather than a reader's route to the fix.
TARGETS = [ROOT / "SOUNDNESS.md", ROOT / "SOUNDNESS-LOG.md", FAMILY / "candor" / "BACKLOG.md"]

NOT_SHAS = {
    "305647574":        "a GitHub workflow id (gh workflow list wfid for integrations.yml)",
    "34140458495":      "a GitHub run id (a workflow_dispatch run on main)",
    "d7608ec5a5adc4c4": "an analyzed.digest value from a coverage-refresh measurement",
    "6d35549032d3":     "a hash of a LINE, not a commit — BACKLOG.md hashes the byte-identical "
                        "`ENGINES = [...]` line across five files to show it is pure copy",
}

# CITATIONS THAT ARE GENUINELY LOST, NAMED RATHER THAN LEFT TO FAIL FOREVER. Each of these was written
# while the work sat on a BRANCH, and the branch was never a ref the 2026-09-16 rewrite walked — so
# `filter-repo` produced no mapping and there is nothing to recover. Listing them is the point: a
# checker that stays red on something unfixable gets disabled, and a checker that silently skips it
# tells you the register is sound when six of its citations lead nowhere. This is the same
# disclosed-not-silent rule the engines are held to.
LOST = {
    "431c1f6": "a fix made ON A BRANCH, 2026-08-08 (BACKLOG: 'CLOSED on the branch')",
    "ef53a2a": "the hardening commit for 431c1f6, same branch, same day",
    "5f4736c": "candor-rust ci.yml wiring, cited from a branch",
    "5b01008": "candor-swift ci.yml wiring, cited from a branch",
    "6ed4901": "candor-java ci.yml wiring, cited from a branch",
    "80d3c48": "branch `rung/per-file-module-identity`, the NetNewsWire module-identity measurement",
}

TOKEN = re.compile(r"`([0-9a-f]{7,40})`")


def load_maps(prefer_committed=True):
    """old-full-sha -> (repo, new-full-sha), from the COMMITTED maps when present."""
    out = {}
    for repo in REPOS:
        src = None
        committed = ROOT / "history" / "commit-maps" / f"{repo}.tsv"
        live = FAMILY / repo / ".git" / "filter-repo" / "commit-map"
        if prefer_committed and committed.exists():
            src = committed
        elif live.exists():
            src = live
        if src is None:
            continue
        for line in src.read_text().split("\n"):
            parts = line.split()
            if len(parts) == 2 and len(parts[0]) == 40 and len(parts[1]) == 40:
                out.setdefault(parts[0], (repo, parts[1]))
    return out


def resolves(sha):
    """Does this sha name a commit in ANY family repo? The register does not say which repo a sha
    belongs to, so the question is genuinely family-wide."""
    for repo in REPOS:
        d = FAMILY / repo
        if not (d / ".git").exists():
            continue
        r = subprocess.run(["git", "-C", str(d), "cat-file", "-e", sha + "^{commit}"],
                           capture_output=True)
        if r.returncode == 0:
            return repo
    return None


def remap_one(sha, maps):
    """(repo, new_short) for a dead sha, or None. A PREFIX may hit several map entries; that is fine
    only while they all point at ONE new commit — otherwise the abbreviation is genuinely ambiguous
    and repairing it would be a guess."""
    hits = {(repo, new) for old, (repo, new) in maps.items() if old.startswith(sha)}
    if not hits:
        return None
    news = {h[1] for h in hits}
    if len(news) != 1:
        return None
    repo, new = sorted(hits)[0]
    return repo, new[:len(sha)]


def main(argv):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv[1:])

    maps = load_maps()
    if not maps:
        print("sha-citations: REFUSING — no commit-maps found, under history/commit-maps/ or any "
              ".git/filter-repo/. A check that cannot find its evidence must not pass.", file=sys.stderr)
        return 2

    total = dead = repaired = 0
    unresolved = []
    for path in TARGETS:
        if not path.exists():
            continue
        text = path.read_text()
        seen = sorted(set(TOKEN.findall(text)))
        edits = {}
        for sha in seen:
            if sha in NOT_SHAS or sha in LOST:
                continue
            total += 1
            if resolves(sha):
                continue
            dead += 1
            got = remap_one(sha, maps)
            if got is None:
                unresolved.append((path.name, sha))
                continue
            repo, new = got
            if not resolves(new):
                unresolved.append((path.name, f"{sha} -> {new} (remapped, still unresolvable)"))
                continue
            edits[sha] = new
        if args.apply and edits:
            for old, new in edits.items():
                text = text.replace(f"`{old}`", f"`{new}`")
            path.write_text(text)
            repaired += len(edits)
            print(f"  {path.name}: repaired {len(edits)} citation(s)")
        elif edits:
            repaired += len(edits)
            print(f"  {path.name}: {len(edits)} dead citation(s) WOULD be repaired")

    print(f"sha-citations: {total} citation(s) checked, {dead} dead, {repaired} "
          f"{'repaired' if args.apply else 'repairable'}, {len(unresolved)} unresolvable")
    if unresolved:
        print("  UNRESOLVABLE — these cite a commit no map can recover:")
        for f, s in unresolved[:40]:
            print(f"    {f}: {s}")
        return 1
    if args.check and dead:
        print("  Run `python3 scripts/sha-citations.py --apply`. A row whose closing commit cannot be")
        print("  resolved is, to `grep`, indistinguishable from a row citing a commit that never was.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
