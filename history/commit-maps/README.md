# `git filter-repo` commit-maps — the only route from a pre-2026-09-16 sha to a live one

On **2026-09-16** six of the seven candor repos were rewritten with `git filter-repo` to redact a
private client codebase from public history. Every sha those repos had ever published changed.

Nothing failed, because **a sha in a markdown table is checked by nothing**. The register silently
became a document whose evidence could not be followed: of 460 distinct backticked sha-like tokens in
`SOUNDNESS.md`, **313 resolved nowhere**. It cost real work before it was noticed — a review agent
read `f51eb27` off R372, could not resolve it, and reported the row as still open. It is closed;
`f51eb27` is `94dc8b5`.

`filter-repo` writes its old→new mapping to `.git/filter-repo/commit-map` **in the rewritten working
copy**. `.git/` is not cloned, not pushed, and not on the second machine — so when this was found,
310 recoverable citations existed in exactly one place, on one laptop, behind nothing but that
laptop's continued existence. These files are that mapping, committed so the recovery survives the
working copy and a fresh clone can verify a citation without privileged local state.

`candor-ts` has no map: it was not rewritten, and its citations never died.

Format: `<old-40-char-sha> <new-40-char-sha>` per line, verbatim as `filter-repo` wrote it. A line
whose new sha is all zeros is a commit the rewrite DROPPED.

Read by `scripts/sha-citations.py`, which prefers these committed copies over the `.git/` originals
for exactly the reason above. Run `--check` after any history rewrite; run `--apply` to repair.
