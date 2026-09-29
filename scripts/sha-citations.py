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
never existed. It also cost real work: a review agent read f51eb27 off R372, could not resolve it,
and reported R372 as still open. It is closed — f51eb27 is `94dc8b5`, "R372 rust: a cfg-twinned
`use` used as a TYPE was resolved by SOURCE ORDER".

(Both mentions of the OLD sha above are spelled WITHOUT backticks on purpose — SOUNDNESS R638. This
passage exists to show an old->new PAIR, so `--apply` repairing the old one rewrites it to the new one
and leaves "`94dc8b5` is `94dc8b5`": a tautology where the worked example was. It did exactly that on
its first widened run, here and in `history/commit-maps/README.md`, and both were caught by reading the
diff rather than by any check. A document that deliberately quotes a pre-rewrite sha is the one place
this tool must not touch, and backticks are how it tells the difference.)

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
#
# SOUNDNESS R638 — AND FOR MOST OF THIS FILE'S LIFE THE SET WAS THREE FILES, WHICH DREW THE BOUNDARY
# AROUND ITS OWN TRIGGER (§9) IN THE INSTRUMENT BUILT TO ANSWER §9. The tool reported "795 citations
# checked, 0 dead" while 299 dead citations sat one directory over — 189 in SCAN-BOUNDARY-WORK-QUEUE.md,
# 35 in `conformance/run.sh` (the four-way suite's own evidence comments), and **20 in SPEC.md, the
# NORMATIVE document**, where `:1051` cites all four engines' commits for a clause and none resolved.
# `conformance/gen_chained_dispatch.py` cites the commit that EARNED each xfail retirement, and nothing
# checked any of them either.
#
# So the set is now DERIVED from `git ls-files` rather than listed: every tracked `.md`, `.py` and `.sh`
# in this repo, plus the umbrella's BACKLOG.md. Derived rather than enumerated on this file's own
# evidence — an enumerated list is what went stale, and a new design document would have joined the
# uncovered set silently.
_SKIP_NAMES = {"CHANGELOG.md"}


def _tracked_targets():
    import subprocess
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    if out.returncode != 0:
        return []                     # unknown, not empty — the caller refuses on a zero-citation run
    keep = []
    for rel in out.stdout.split():
        if pathlib.Path(rel).name in _SKIP_NAMES:
            continue
        if rel.endswith((".md", ".py", ".sh")):
            keep.append(ROOT / rel)
    return keep


TARGETS = [ROOT / "SOUNDNESS.md", ROOT / "SOUNDNESS-LOG.md", FAMILY / "candor" / "BACKLOG.md"] + [
    p for p in _tracked_targets()
    if p.name not in ("SOUNDNESS.md", "SOUNDNESS-LOG.md")]

NOT_SHAS = {
    "305647574":        "a GitHub workflow id (gh workflow list wfid for integrations.yml)",
    "34140458495":      "a GitHub run id (a workflow_dispatch run on main)",
    "d7608ec5a5adc4c4": "an analyzed.digest value from a coverage-refresh measurement",
    "6d35549032d3":     "a hash of a LINE, not a commit — BACKLOG.md hashes the byte-identical "
                        "`ENGINES = [...]` line across five files to show it is pure copy",
    # SOUNDNESS R638 — SELFTEST FIXTURE LITERALS, and they must be named here rather than left to the
    # widened TARGETS below, for TWO independent reasons. (1) Six of them can never resolve, so a
    # widened check would stay red forever on something correct, and "a checker that stays red on
    # something unfixable gets disabled" is this file's own stated rule one block down. (2) Worse, the
    # other three DO remap — `93cb988`, `aa280d1` and `ff6efad` — so `--apply` would have silently
    # REWRITTEN THE TEST FIXTURES that pin `bucket()`'s behaviour. A repair tool editing the tests that
    # judge it is not a repair. Measured before widening, which is the only reason it was caught.
    "0123456":          "soundness-status.py selftest fixture literal",
    "1234567":          "soundness-status.py selftest fixture literal",
    "1234abc":          "soundness-status.py selftest fixture literal",
    "abc1234":          "soundness-status.py selftest fixture literal — the most-used one",
    "deadbee":          "a fixture literal quoted in R527's own prose and in two selftests",
    "deadbee1":         "soundness-status.py selftest fixture literal",
    "93cb988":          "soundness-status.py selftest fixture (R190's PARTLY-CLOSED case) — REMAPPABLE, "
                        "which is exactly why it is listed: --apply would have rewritten the test",
    "aa280d1":          "soundness-status.py selftest fixture (the REOPENED case) — remappable, ditto",
    "ff6efad":          "soundness-status.py comment quoting R588's spelling — remappable, ditto",
}

# CITATIONS THAT ARE GENUINELY LOST, NAMED RATHER THAN LEFT TO FAIL FOREVER. Each of these was written
# while the work sat on a BRANCH, and the branch was never a ref the 2026-09-16 rewrite walked — so
# `filter-repo` produced no mapping and there is nothing to recover. Listing them is the point: a
# checker that stays red on something unfixable gets disabled, and a checker that silently skips it
# tells you the register is sound when six of its citations lead nowhere. This is the same
# disclosed-not-silent rule the engines are held to.
# SOUNDNESS R747 — DEAD, REPAIRABLE, AND REPAIR IS BLOCKED. Every sha below is in `SPEC.md`, resolves
# nowhere, and HAS a mapping — `--apply` rewrites all twenty happily. Doing so takes `must_ledger` RED:
# it keys each normative statement by a HASH OF THE STATEMENT TEXT, and a citation sitting INSIDE a
# clause is part of that text, so a repair orphans the ledger entry that classified it. Measured: 11
# orphaned entries and 11 unclassified statements, and `reanchor_banner` correctly refuses to re-anchor
# more than one at a time ("More than the banner moved, so this is a classification question").
#
# So these are NOT `LOST` — nothing is unrecoverable — and they are not silently skipped either. Fixing
# them properly means keying the ledger on the statement's NORMATIVE TEXT with citations excluded, which
# re-keys every entry in the ledger and is not a change to make unreviewed at the end of a long session.
# Until then the debt is named here rather than absent, which is the same disclosed-not-silent rule the
# engines are held to.
REPAIR_BLOCKED = {
    "0075987": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "01d5c6b": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "05158db": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "107755b": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "1503368": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "1969559": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "27f4beb": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "2d004b6": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "37c9b10": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "4805fca": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "4fd140c": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "5a8cf48": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "7271c69": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "7378f4f": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "93ed0a1": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "9a17c4c": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "a034371": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "e4bc419": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "ec1a441": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
    "ec3e50f": "SPEC.md — repair blocked by the must_ledger statement-hash coupling (R747)",
}

LOST = {
    # SOUNDNESS R638 — surfaced the moment TARGETS stopped being three files. All four are cited in
    # SCAN-BOUNDARY-WORK-QUEUE.md, resolve in NO family repo, and have NO entry in any commit-map, so
    # there is nothing to repair. What each one WAS is recorded here from its own citation; the reason it
    # is unmappable was NOT established, and this comment says so rather than guessing a cause:
    #   2c90c8d — the PORTED half of a two-line fabrication fix, cited beside 47f460f "on main"
    #   97c1a2b — half of a clean outcome, cited beside a713186
    #   cb8c1aa — cited as candor-java, for `Cha#depDirectSupers`' refusal and its numbers
    #   eb1c76b — the `locatorNameIsStable` whole-body pre-pass fix, "without back-porting"
    # A branch commit and a pre-rewrite commit in an uncovered map look identical from here.
    "2c90c8d": "scan-boundary queue: ported fabrication fix; unmappable, cause not established",
    "97c1a2b": "scan-boundary queue: paired with a713186; unmappable, cause not established",
    "cb8c1aa": "scan-boundary queue: candor-java Cha#depDirectSupers; unmappable, cause not established",
    "eb1c76b": "scan-boundary queue: locatorNameIsStable pre-pass; unmappable, cause not established",
    "431c1f6": "a fix made ON A BRANCH, 2026-08-08 (BACKLOG: 'CLOSED on the branch')",
    "ef53a2a": "the hardening commit for 431c1f6, same branch, same day",
    "5f4736c": "candor-rust ci.yml wiring, cited from a branch",
    "5b01008": "candor-swift ci.yml wiring, cited from a branch",
    "6ed4901": "candor-java ci.yml wiring, cited from a branch",
    "80d3c48": "branch `rung/per-file-module-identity`, the NetNewsWire module-identity measurement",
}

# A BACKTICKED HEX TOKEN INTRODUCED AS A `sha1`/`sha256`/`digest` IS NOT A COMMIT CITATION, and the
# convention alone did not hold: on 2026-09-26 the register acquired THREE of them in one day — two jar
# sha1 prefixes proving an A/B's two arms differed, and one proving a rebuilt jar matched a lane's. Each
# time this checker correctly reported a dead commit, and each time the honest repair was to drop the
# backticks, because the register's convention is that backticks mean "a commit a reader can follow".
#
# Rather than keep paying that, the CONTEXT is read: a token immediately preceded by one of these words
# is excluded from the commit check. It is deliberately narrow — the word must be adjacent, so a commit
# mentioned in a sentence that happens to contain "sha1" elsewhere is still checked.
_NOT_A_COMMIT_CONTEXT = re.compile(
    r"(?:jar\s+)?sha-?(?:1|256)|digest|checksum"
    r"(?:\s+prefix(?:es)?)?"
    r"(?:\s*(?:,|vs\.?|and|or)\s*|\s+)$", re.I)
TOKEN = re.compile(r"`([0-9a-f]{7,40})`")


def _is_commit_citation(text, m):
    """False when the token is introduced as a hash of something that is not a commit."""
    return not _NOT_A_COMMIT_CONTEXT.search(text[max(0, m.start() - 28):m.start()])


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


# SOUNDNESS R638 — the two instrument sources contain `scratchpad/...` strings BY CONSTRUCTION: they are
# the fixtures that prove the extractor and the R600 ratchet can fail. Widening TARGETS to every tracked
# source pulled those fixtures in as live citations (`alpha`, `beta`, `brandnew-lane`, `x`), which is the
# same mistake as letting `--apply` rewrite a selftest's sha literal — a check reading its own test data
# as evidence. Narrow by NAME, not by directory, so a real document is never skipped.
_FIXTURE_SOURCES = {"sha-citations.py", "soundness-status.py"}


def scratchpad_citations(paths=None):
    """The set of top-level scratchpad directory names the documents cite as evidence."""
    out = set()
    for path in (paths or TARGETS):
        if not path.exists() or path.name in _FIXTURE_SOURCES:
            continue
        for c in set(re.findall(r'scratchpad/[A-Za-z0-9_./*-]+', path.read_text())):
            out.add(c.split("/")[1].rstrip("*") if "/" in c else c)
    return out


SCRATCH_BASELINE = ROOT / "history" / "scratchpad-citations.baseline"


def scratchpad_baseline(path=None):
    """The grandfathered set — SOUNDNESS R600. Comments and blanks ignored."""
    p = path or SCRATCH_BASELINE
    if not p.exists():
        return None                  # unknown, NOT empty: the caller must refuse rather than pass
    return {l.strip() for l in p.read_text().splitlines()
            if l.strip() and not l.lstrip().startswith("#")}


def new_scratchpad_citations(paths=None, baseline_path=None):
    """Citations not on the grandfather list. A RATCHET: the 34 dead ones cannot be repaired, so the
    only thing left to protect is the 35th.

    SOUNDNESS R600, and the cost is measured rather than argued: R655 was re-verified on 2026-09-27,
    could not be reproduced on FIVE binaries, and is now un-actionable because what was load-bearing
    lived in a scratchpad that no longer exists. `git filter-repo` leaves a commit-map; a deleted temp
    directory leaves nothing, so there is no --apply for this class and there never will be.
    """
    base = scratchpad_baseline(baseline_path)
    if base is None:
        return None                  # see scratchpad_baseline: unknown, not clean
    return scratchpad_citations(paths) - base


def family_repos_present(family=None):
    """Which family repos have a `.git` this process could interrogate.

    SOUNDNESS R643. `resolves()` answers "does this sha name a commit in ANY family repo" by running
    `git cat-file` in each sibling — so on a candor-spec-ONLY checkout it returns None for every sha
    and this check reports EVERY citation dead. Measured in an isolated worktree 2026-09-27: 12 of the
    register's doc-gates, and this one alone produced hundreds of "unresolvable" lines.

    That is the same shape as R639 one level up — a check that looked nowhere and called everything
    missing — so the answer is the same: test the ENVIRONMENT directly and refuse, rather than infer
    absence from a result. Inferring it from "nothing resolved" would be wrong in the one case that
    matters: a register whose citations really are all dead must still go RED.
    """
    fam = pathlib.Path(family) if family else FAMILY
    return [r for r in REPOS if (fam / r / ".git").exists() and not _is_shallow(fam / r)]


def _is_shallow(d):
    """A depth-1 clone cannot resolve an old commit, so it cannot answer this check either.

    SOUNDNESS R643. Without this, placement in CI decides the verdict: `conformance.yml`'s documents
    job checks out every sibling repo SHALLOW (for check_agents_vocabulary), so a doc-gates step placed
    after those checkouts would find six `.git` directories, run the check, resolve nothing, and go RED —
    while the same step one line earlier would self-skip. A gate whose answer depends on where in a
    workflow it sits is not a gate. Ask git instead.
    """
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "--is-shallow-repository"],
                       capture_output=True, text=True)
    return r.returncode != 0 or r.stdout.strip() == "true"


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


# SOUNDNESS R600 — A PATH CITATION IS A PROMISE A READER CAN FOLLOW, AND MOST OF THEM CANNOT BE.
# The register cites scratchpad directories as evidence ("fixture at `scratchpad/agsw/f5`"). Those live
# in a SESSION-SCOPED temp dir: a new session gets a new path, and the old one is gone. Measured
# 2026-09-25: 33 distinct scratchpad citations, **26 of them point at nothing**.
#
# This is the same class as the 531 dead sha citations repaired above, with one difference that decides
# the remedy: THOSE WERE RECOVERABLE and these are not. There is no commit-map for a deleted temp
# directory. So this reports rather than repairs, and it is ADVISORY rather than fatal — a checker that
# is permanently red on something unfixable gets disabled, and then it is not a checker.
#
# The real remedy is a CONVENTION, and it belongs in the row that cites: put the decisive artefact IN
# the row (the numbers, the fixture source, the exact command), and treat the path as a courtesy, never
# as the evidence. A row whose claim can only be checked by opening a directory that no longer exists
# is, to a reader, indistinguishable from a row with no evidence at all.
def ephemeral_citations(paths=None):
    """(total, dead, sample) for scratchpad path citations.

    `dead` is None — NOT 0 — when this run could not look. SOUNDNESS R639: returning 0
    made "no session dir" indistinguishable from "every citation resolves", and since
    nothing in either repo sets CANDOR_SCRATCH, the unlookable case was EVERY case. The
    total is still counted in that state, because how many citations exist is knowable
    without a session dir and is the number that makes the advisory worth printing."""
    import os
    # WITHOUT A SESSION DIR THIS CANNOT ANSWER, AND MUST NOT ANSWER "ALL DEAD". The first cut read
    # `CANDOR_SCRATCH` and, when doc-gates did not set it, reported 32 of 32 citations dead — a check
    # that looks nowhere and calls everything missing. It is the vacuous-guard shape this register
    # keeps finding in its own instruments, and it fired on the very commit that added the check.
    sess = os.environ.get("CANDOR_SCRATCH", "")
    can_look = bool(sess) and os.path.isdir(sess)
    seen, dead = scratchpad_citations(paths), []
    for top in seen:
        if can_look and not os.path.exists(os.path.join(sess, top)):
            dead.append(top)
    if not can_look:
        return len(seen), None, []     # counted, NOT judged — and the caller must say so
    return len(seen), len(set(dead)), sorted(set(dead))[:8]


def selftest():
    """Prove this checker's two judgement calls can FAIL — SOUNDNESS R643.

    Until 2026-09-27 this script had no selftest and no fixture. Its only input was the live,
    currently-clean documents, so `attack B` was trivial: replace the body with `sys.exit(0)` and
    every gate it appears in stays green. Two things here are real judgement calls rather than
    plumbing, and both were got WRONG once already:

      - `_is_commit_citation`'s CONTEXT window. The first cut of it looked back 40 characters and
        suppressed GENUINE citations, which its own calibration caught; it is now 28 and requires
        the introducing word to be ADJACENT. Cases 5 and 6 below are that narrowness — a commit in
        a sentence that merely CONTAINS "sha1" must still be checked.
      - `ephemeral_citations`' THREE states. It returned 0 for "could not look", which made a
        missing session dir indistinguishable from a clean result, and since nothing sets
        CANDOR_SCRATCH the unlookable case was every case (R639). `dead is None` is now the
        cannot-look state and the caller must say so.
    """
    import os, tempfile
    bad = []

    ctx = [
        ("the jar sha1 `aa08496` proves the arms differ",            False, "jar sha1, adjacent"),
        ("sha256 `f955ecd` of the rebuilt jar",                      False, "sha256, adjacent"),
        ("digest `4081edf9` of the artifact",                        False, "digest, adjacent"),
        ("checksum `abc1234` recomputed",                            False, "checksum, adjacent"),
        ("candor-java `46f69ad` fixes it",                           True,  "an ordinary citation"),
        ("the sha1 mismatch was noted; the fix is `46f69ad`",         True,
         "NARROWNESS: sha1 appears but is NOT adjacent — still a citation"),
        ("jar sha1 prefixes `aa08496` vs `f955ecd`",                 False, "prefixes + vs, both excluded"),
    ]
    for text, want, why in ctx:
        for m in TOKEN.finditer(text):
            got = _is_commit_citation(text, m)
            # in case 7 both tokens must be excluded; elsewhere there is exactly one token
            if got != want:
                bad.append(f"_is_commit_citation({text!r}, {m.group(1)}) = {got}, want {want} — {why}")

    # SOUNDNESS R600's ratchet, both directions. Without these the gate is exactly the shape this file
    # keeps finding in its own instruments: a check whose only input is the currently-clean documents.
    import tempfile as _t0
    with _t0.TemporaryDirectory() as _d0:
        _p0 = pathlib.Path(_d0)
        _bl = _p0 / "baseline"
        _bl.write_text("# a comment that must be ignored\n\nagsw\ncarveout\n")
        _doc = _p0 / "DOC.md"
        _doc.write_text("fixture at `scratchpad/agsw/f5` and `scratchpad/carveout/x`\n")
        if new_scratchpad_citations([_doc], _bl) != set():
            bad += 1
            print("  FAIL a document citing ONLY grandfathered names must report no new citations")
        _doc.write_text("fixture at `scratchpad/agsw/f5` and `scratchpad/brandnew-lane/out.json`\n")
        if new_scratchpad_citations([_doc], _bl) != {"brandnew-lane"}:
            bad += 1
            print("  FAIL an UNGRANDFATHERED citation must be reported — this is the 35th, the only "
                  "one a ratchet can still prevent")
        if scratchpad_baseline(_p0 / "nope") is not None:
            bad += 1
            print("  FAIL a MISSING baseline must read as unknown (None), never as an empty set — "
                  "an empty set would silently make every citation look new, and a caller that "
                  "treated None as clean would make every citation look grandfathered")
        print("  ok   R600 ratchet: grandfathered pass, ungrandfathered reported, missing baseline "
              "is unknown rather than empty")

    # family_repos_present: the environmental predicate the R643 self-skip rests on. Tested over REAL
    # clones rather than inferred, because the WRONG way to detect this is "nothing resolved" — a
    # register whose citations really are all dead must still go RED.
    #
    # AND THESE CASES CAUGHT A STALE EXPECTATION OF MINE, which is the only reason the distinction got
    # made: the first cut of them created an EMPTY `.git` DIRECTORY and asserted it counted as a repo.
    # Once `_is_shallow` started asking git, an empty `.git` correctly stopped counting and both cases
    # failed. An unusable `.git` is not a family repo, and now that is pinned rather than assumed.
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _p = pathlib.Path(_td)
        if family_repos_present(_p) != []:
            bad.append("an EMPTY dir must give [] — otherwise the self-skip never fires")
        _fake = _p / "fake"
        (_fake / "candor-spec" / ".git").mkdir(parents=True)
        if family_repos_present(_fake) != []:
            bad.append("a `.git` that is not a usable repo must NOT count — a directory git cannot "
                       "answer for is the same as no repo at all")
        _src = _p / "src"
        _src.mkdir()
        subprocess.run(["git", "init", "-q", str(_src)], capture_output=True)
        # HERMETIC: this throwaway fixture repo must not inherit the user's GLOBAL git config. Measured
        # 2026-09-29: a global `commit.gpgsign=true` whose signing program had gone missing made both
        # fixture commits fail SILENTLY (output captured, exit ignored), so the "shallow" clone was of an
        # EMPTY repo and this case failed for a reason that had nothing to do with `_is_shallow`. Signing
        # is switched off for THIS temporary repo only, and a fixture commit that fails is now reported
        # as an unrun calibration rather than left to masquerade as a verdict.
        for _k, _v in (("user.email", "t@e"), ("user.name", "t"), ("commit.gpgsign", "false")):
            subprocess.run(["git", "-C", str(_src), "config", _k, _v], capture_output=True)
        _fixture_ok = True
        for _i in (1, 2):
            (_src / "f").write_text(str(_i))
            subprocess.run(["git", "-C", str(_src), "add", "f"], capture_output=True)
            _cm = subprocess.run(["git", "-C", str(_src), "commit", "-qm", f"c{_i}"], capture_output=True)
            _fixture_ok = _fixture_ok and _cm.returncode == 0
        if not _fixture_ok:
            bad.append("the fixture repo could not be COMMITTED to — the shallow/deep cases below did NOT "
                       "measure anything, and an unrun calibration case is not a passing one")
        _deep, _shal = _p / "deep" / "candor-rust", _p / "shal" / "candor-rust"
        _deep.parent.mkdir(); _shal.parent.mkdir()
        _c1 = subprocess.run(["git", "clone", "-q", str(_src), str(_deep)], capture_output=True)
        _c2 = subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{_src}", str(_shal)],
                             capture_output=True)
        if _c1.returncode or _c2.returncode:
            bad.append("could not build the shallow/deep clone pair — the _is_shallow cases did NOT "
                       "run, and an unrun calibration case is not a passing one")
        else:
            if family_repos_present(_p / "deep") != ["candor-rust"]:
                bad.append("a FULL clone must count — otherwise the gate self-skips everywhere and "
                           "never runs at all, which is worse than the red it replaced")
            if family_repos_present(_p / "shal") != []:
                bad.append("a SHALLOW clone must NOT count: it cannot resolve an old commit, so "
                           "whether this gate passes would depend on CI step ORDER")

    # ephemeral_citations' three states, over a throwaway target file so the live register is not read.
    with tempfile.TemporaryDirectory() as td:
        tgt = pathlib.Path(td) / "FAKE.md"
        tgt.write_text("evidence in scratchpad/alpha/ and scratchpad/beta/x.json\n")
        saved = os.environ.pop("CANDOR_SCRATCH", None)
        try:
            t, d, _ = ephemeral_citations([tgt])
            if (t, d) != (2, None):
                bad.append(f"cannot-look state gave (total={t}, dead={d}), want (2, None) — "
                           "R639: returning 0 dead is what made silence look like success")
            sess = pathlib.Path(td) / "sess"
            (sess / "alpha").mkdir(parents=True)
            os.environ["CANDOR_SCRATCH"] = str(sess)
            t, d, _ = ephemeral_citations([tgt])
            if (t, d) != (2, 1):
                bad.append(f"half-alive state gave (total={t}, dead={d}), want (2, 1)")
            empty = pathlib.Path(td) / "empty"
            empty.mkdir()
            os.environ["CANDOR_SCRATCH"] = str(empty)
            t, d, _ = ephemeral_citations([tgt])
            if (t, d) != (2, 2):
                bad.append(f"all-dead state gave (total={t}, dead={d}), want (2, 2)")
        finally:
            os.environ.pop("CANDOR_SCRATCH", None)
            if saved is not None:
                os.environ["CANDOR_SCRATCH"] = saved

    for b in bad:
        print("  FAIL " + b)
    print("sha-citations selftest: " + ("OK" if not bad else f"FAILED ({len(bad)})"))
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv[1:])

    if args.selftest:
        return selftest()

    maps = load_maps()
    if not maps:
        print("sha-citations: REFUSING — no commit-maps found, under history/commit-maps/ or any "
              ".git/filter-repo/. A check that cannot find its evidence must not pass.", file=sys.stderr)
        return 2

    present = family_repos_present()
    if len(present) < 2:
        print("sha-citations: SKIPPED — it did not run. Only %d family repo(s) have a `.git` here (%s), "
              "and this check answers `does this sha name a commit in ANY family repo` by interrogating "
              "each one. On a single-repo checkout it would report every engine citation dead, which is "
              "a check that looked nowhere calling everything missing — the R639 shape. Run it where the "
              "family is cloned WITH HISTORY; a shallow clone cannot resolve an old commit either."
              % (len(present), ", ".join(present) or "none"), file=sys.stderr)
        return 3

    total = dead = repaired = 0
    unresolved = []
    for path in TARGETS:
        if not path.exists():
            continue
        text = path.read_text()
        seen = sorted({m.group(1) for m in TOKEN.finditer(text)
                       if _is_commit_citation(text, m)})
        edits = {}
        for sha in seen:
            if sha in NOT_SHAS or sha in LOST or sha in REPAIR_BLOCKED:
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

    if total == 0:
        print("sha-citations: REFUSING — ZERO citations checked. This register cites hundreds of commits;"
              " a run that finds none has a broken token pattern or an over-wide context exclusion, and"
              " an empty check must not read as a clean one.", file=sys.stderr)
        return 2
    print(f"sha-citations: {total} citation(s) checked, {dead} dead, {repaired} "
          f"{'repaired' if args.apply else 'repairable'}, {len(unresolved)} unresolvable")
    _t, _d, _s = ephemeral_citations()
    if _d is None and _t:
        # R639: a stated non-result. This branch is the whole point of the row — the check
        # spent two days reporting nothing at all, which read as a clean result.
        print(f"  NOT CHECKED (R600/R639): {_t} scratchpad path citation(s) in the register "
              f"were not resolved — CANDOR_SCRATCH is unset, so this run could not look.")
        print("  Set CANDOR_SCRATCH to the session scratchpad to check them, and read the "
              "absence of a verdict as an absence, not as a pass.")
    elif _d:
        print(f"  ADVISORY (R600): {_d} of {_t} scratchpad path citation(s) point at nothing — "
              f"session-scoped evidence, NOT recoverable. e.g. {', '.join(_s[:5])}")
        print("  Put the decisive artefact IN the row; a path is a courtesy, never the evidence.")
    # R638 — REPORT BEFORE RETURNING. The first cut of the R600 block below `return`ed 1 while the
    # UNRESOLVABLE list was still unprinted, so widening TARGETS produced "4 unresolvable" as a COUNT
    # with no names and no way to act on it. A guard that hides the finding it sits in front of is worth
    # less than no guard. Both are now reported and either can fail the run.
    _rc = 0
    if unresolved:
        print("  UNRESOLVABLE — these cite a commit no map can recover:")
        for f, sh in unresolved[:40]:
            print(f"    {f}: {sh}")
        _rc = 1

    # SOUNDNESS R600 — the ratchet. A new scratchpad citation is a promise nobody can keep.
    _new = new_scratchpad_citations()
    if _new is None:
        print(f"sha-citations: REFUSING — the R600 grandfather list is missing at "
              f"{SCRATCH_BASELINE}. A ratchet with no baseline cannot say whether the set grew, and "
              f"an absent baseline must not read as a clean one.", file=sys.stderr)
        return 2
    if _new:
        _rc = 1
        print(f"  NEW SCRATCHPAD CITATION(S) (R600): {len(_new)} — {', '.join(sorted(_new))}")
        print("  A scratchpad path is session-scoped: it is dead the moment the session ends, and")
        print("  unlike a dead sha it CANNOT be repaired. R655 is the measured cost — un-actionable")
        print("  on five binaries because what was load-bearing lived in a directory that is gone.")
        print("  Put the decisive artefact IN the row. Do not add a baseline line to pass this gate.")

    if _rc:
        return _rc
    if args.check and dead:
        print("  Run `python3 scripts/sha-citations.py --apply`. A row whose closing commit cannot be")
        print("  resolved is, to `grep`, indistinguishable from a row citing a commit that never was.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
