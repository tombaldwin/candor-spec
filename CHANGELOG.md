# Changelog

The **spec (contract) version** is bumped on additive changes (a minor: a new optional field, `AS-EFF`
code, or pinned tool surface) or breaking ones (a major: an envelope reshape or a removed field).
Implementations declare the version they implement via the report envelope's `spec` string. The version
moves as a **ladder**: the reference engine (candor-java) leads a new rung, it is written into
[SPEC.md](SPEC.md), then the other code engines implement it in turn and the cross-impl conformance suite
pins the floor. Each rung through ⟨0.29⟩ is **additive** over the last — an older-version consumer that
ignores the newer optional fields is unaffected. **⟨0.30⟩ is the first exception**: it adds no field and
removes none, but it changes what a gate DOES with an existing one, so a tree that passed under ⟨0.29⟩ can
exit 2 under ⟨0.30⟩. Upgrading to it is a decision, not a drop-in.

This file is a one-line-per-rung index. The authoritative, surface-by-surface record is **[SPEC.md §8](SPEC.md#8-changelog)**
(each surface is also tagged inline with the ⟨0.8⟩/⟨0.7⟩/⟨0.6⟩ rung that introduced it); the adversarial
evidence behind the soundness posture is **[SOUNDNESS-LOG.md](SOUNDNESS-LOG.md)**.

**A `## [X.Y.Z]` heading here is a build, not a new GitHub release.** This repo's GitHub release is
tagged at the floor alone (`vX.Y`, no patch component — the spec has no patch axis), so
`release.sh` cuts one release per rung and correctly skips every patch build after it: the tag already
exists. That leaves a real question — where does a patch cycle's own notes get published? — answered by
`scripts/publish-floor-notes.sh`: it folds every `## [X.Y.<patch>]` section for the current floor into
that floor's existing release notes (never a new tag, never touching SPEC.md), so the release stays the
complete record of everything shipped while that floor held, not a snapshot frozen at the day it was cut.
Run it after any patch-cycle commit that adds a section here.

## Unreleased

## [0.35.0] — 2026-09-03

- **`scripts/check_agents_vocabulary.py` — a CI gate that derives the effect vocabulary from SPEC §1 and
  checks every sibling's `AGENTS.md`/`README.md` copy and every embedded `--agents` contract against it
  (SOUNDNESS R155: `Llm` was missing from every agent-facing copy, and the old drift gate pinned the
  copies to EACH OTHER, so they drifted together). Wired into `conformance.yml` with sibling checkouts.
- **Five findings from the 2026-08-30 four-agent review panel on ⟨0.34⟩, closed in conformance/run.sh,
  SPEC.md and SOUNDNESS.md — no spec-version change, all conformance/documentation hardening.**
  - **PART 84's remedy leg had no teeth.** Its `--policy`-names-a-remedy check was `*[Pp]olicy*` — a bare
    substring test that passes on the FLAG'S OWN NAME being echoed back (`unknown flag \`--policy\``
    contains "policy"), so an engine that never wrote a remedy sentence at all could still pass. Now
    strips the literal `--policy` token first and requires "polic" to still appear in what remains — a
    message that only ever said the word as part of the flag has nothing left to match. Falsified against
    a real pre-fix state on both sides: candor-swift `73a2417^` (`path`/`tour` printed the bare
    "unknown flag" shape) reddens, `73a2417` (already committed locally) greens; candor-rust's `diff`/
    `rewire` — unfixed as of this writing — currently redden live, which is the row doing its job, not a
    false alarm.
  - **`conformance/part.sh 85` could not run PART 85** — `P85: unbound variable`. PART 84 prints only an
    opening `[84]` header with no closing `PART 84 —` verdict, so `part.sh`'s "a header-only part owns
    everything up to the next marker" rule swallowed PART 85's own fixture setup (which precedes PART
    85's `[85]` header) into PART 84's slice. Gave PART 84 the closing marker every other TIER-1 part
    already has; `part.sh 85` now runs standalone and `part.sh --check` still resolves all slices to
    exactly one part.
  - **PART 80's header comment was stale in the good direction.** It said candor-rust and candor-swift had
    not yet ported the whitespace-tolerant `spec`-ladder parse; both now have (candor-rust `7401af9`,
    candor-swift's ⟨0.34⟩ CHANGELOG entry) and the row itself already reads `ws=PASS` on all four engines
    — it is probed live, never hard-coded, so the row was never wrong, only the prose above it. Corrected
    to record both the original measurement and the close, dated.
  - **`peek-classpath` had no SPEC clause.** candor-java's declared peek classpath (`--peek-classpath`,
    its `.candor/config` key, `CANDOR_PEEK_CLASSPATH`) is a §3.3.1 INPUT the moment it is declared — a
    sink writing over it once destroyed a real dependency jar at exit 0 (fixed `9a17c4c`) — and nothing
    pinned that cross-engine. Written as an addition to §3.3.1(3)'s open input list, explicitly NOT a
    four-way MUST: rust/ts/swift derive their peek's file set from the project's own manifest and have no
    externally-declared classpath to protect, so a row demanding the same behaviour of all four would be
    vacuous for three of them. New conformance PART 86 pins it candor-java-scoped, the same shape PART 81
    already uses for a mechanism only one engine has; falsified against candor-java `dc1f934` (immediately
    pre-fix): the flag spelling wrote a 576-byte report over a 909-byte dependency jar (MD5 moved) at exit
    0, where HEAD refuses at exit 2 with the jar byte-identical.
  - **SOUNDNESS.md's R21 row had 8 columns where every other row has 6** — an unprotected literal pipe
    inside a code span (`` `\|\| true` ``; a code span does not apply backslash escapes, so the raw `|`
    characters split the table row). Reworded to describe the shell idiom without a literal pipe, pointing
    at SOUNDNESS-LOG.md's 2026-07-09 entry for the exact `|| true` spelling.

- **⟨0.35⟩ — the rung this release cuts. SPEC §4 gains *"A NON-EMPTY CANDIDATE SET IS NOT A COMPLETE ONE"*:**
  at a dispatch site whose visible implementor set may be incomplete — a synthesised or structural
  implementor, a conformer the scan did not open — an engine must either carry the candidates' effects or
  disclose `Unknown`; it must never resolve silently to the candidates it happened to see. **PART 87**
  (tier 1) pins it four-way: instance, static and inherited field bindings, zero and one implementor each,
  with an over-charge control per shape proving a PURE lambda through the same site gains nothing and is
  not blanket-hedged. Opened in `047363a`; the ts arm and the declared-coverage ledger classification landed
  in `da04869`.
- **PART 87 was then hardened four times before it was trusted, and each time the defect was in the
  instrument, not an engine.** `08e557c`: the part and its checker (`cha_completeness_check.py`) could not
  FAIL on a hedging engine — a mutation gate now proves the checker still reddens (replace `verdict()` with
  `return True` → exactly 7 rows red). `56b019a`: it pinned one spelling of the property it asserts.
  `4c89751`: its declared controls named a directory nothing built. `4ebffa5`: its three over-charge
  controls passed over a fixture that never compiled — a liveness guard now diverges loudly when `javac`
  produces no classes or the engine writes no report, rather than judging an absent output as clean.
- **`scripts/check_soundness_tables.py` is a CI gate: every SOUNDNESS row must render as a table row.**
  Measured with a GFM lexer, **32 rows** — the entire R108–R133 register plus six older ones — were
  rendering as raw paragraphs, split from their tables by a prose block and three stray blank lines. A
  prior fix had counted PIPES, which were never the failure, and reported success while 26 rows stayed
  orphaned. The gate tests CONTIGUITY, and is proven in both directions: rc 0 on the fixed file, rc 1
  naming all 35 orphans on the pre-fix one (`30d0799`).
- **`conformance/run.sh` now reads the swift build's exit status (SOUNDNESS R149).** It ran
  `swift build` in a subshell, discarded the status, and proceeded on the mere existence of
  `.build/debug/candor-swift` — so a failed build silently measured whatever binary the previous run had
  left. A present-but-unbuildable swift is now a hard FAIL, exit 2, never a skip and never a pass; the
  guard is proven to fire against a non-existent tree (`4b84f2b`).
- **SOUNDNESS.md rows R117–R157 record this round.** Five regressions the wave's own fixes introduced (all
  closed before push), published cardinal sins found and closed in all four engines while fixing them
  (rust R122/R123/R128/R130/R139, swift R125/R130/R135, java R130, ts R130/R137/R138), and the open rows
  that remain. Each row marks what was MEASURED and what was taken on report.
- **SPEC.md's versioning narrative had no ⟨0.35⟩ paragraph, and §8 stopped at 0.30 — so the document's
  own claim that "the changelog lists every rung's contents" was FALSE for five rungs.** Found by the
  0.35.0 release panel's spec lens. Two fixes, both in SPEC.md: the [Versioning policy](SPEC.md#versioning-policy)
  narrative gains its ⟨0.35⟩ paragraph in the same form as ⟨0.30⟩–⟨0.34⟩ — NON-ADDITIVE, fail-closed, and
  the first whose flip comes not from a field but from a caller APPEARING in `functions[]` where it was
  absent, so `deny Unknown` / `deny <Effect> <fn>` / `pure <fn>` can go exit 0 → 1 on identical bytes with
  no upgrade note, because the finding is the remedy; and §8 is BACKFILLED with 0.31, 0.32, 0.33, 0.34 and
  0.35, one entry each, naming the conformance parts that pin each rung. Backfill rather than a
  "see the narrative paragraphs" pointer at §8's head, because only the backfill makes "§8 is
  authoritative" (CHANGELOG.md's own claim, and SPEC.md's) TRUE.
- **The MUST ledger's classification for the versioning block was RE-CONFIRMED, not re-hashed.** The whole
  narrative is one block (`must_ledger.py` extracts at paragraph granularity), so adding the ⟨0.35⟩
  paragraph moved its sha `df8fa25c43ee6913` → `6f4cf68741907c21` and failed the gate, which is the gate
  working as designed. It stays `unenforced`, and the reason now records WHY no row is possible rather than
  only that none exists: each paragraph asserts what an UPGRADE does — a verdict that moves BETWEEN two
  engine versions on identical bytes — and every conformance row measures one build. The remedy is named
  (the "released floor" conformance job already holds a published binary beside HEAD's), so the debt is
  recorded rather than left as a silence. Ledger still 529/529 classified, 12 unenforced.

## [0.34.0] — 2026-08-31

- **UPGRADING FROM 0.33.1 — re-baselining is not review.** ⟨0.34⟩ is NON-ADDITIVE and this wave
  corrects the classifier in BOTH directions. After regenerating a baseline, **diff it against the
  old one**: effects this release REMOVES will never trip any gate, because `gains` and the baseline
  guard alarm only on effects appearing. A scoped `deny` that went quiet needs eyes, not a re-run.
  Full note, with the measured per-engine numbers and the loud-vs-quiet split, is in the
  [umbrella changelog](https://github.com/tombaldwin/candor/blob/main/CHANGELOG.md).

- **⟨0.33⟩ era markers on permanent prior-floor literals.** `release-preflight [2]` hunts the prior
  floor to catch a bump-miss, and a rung's own ladder comparisons (`spec_predates(spec, "0.33")`)
  reference 0.33 FOREVER by design — so [2] could never go green by fixing anything. Those sites now
  carry a `⟨0.33⟩` marker saying the literal is the RUNG this code names, not a version that bumps.
  Comment-only; no behaviour change.
  **SPEC.md itself was deliberately NOT marked.** Adding the marker there edited the body of a
  normative statement, which moved its ledger SHA and correctly failed the MUST LEDGER — and the
  flag turned out to be a FALSE POSITIVE: `[2b]` applied its `spec` word test to grep's
  `path:line:content` output, so `candor-spec/SPEC.md` matched on the FILENAME and every line in
  this file carrying the prior floor was flagged whatever it said. Marker reverted, gate fixed in
  the umbrella. SPEC.md is byte-unchanged by this cut's era-marker work, and the ledger reports
  521 statements classified.


- **PART 63, PART 62, PART 70 and PART 65 hardened in `conformance/mutation-gate.sh` — the three
  highest-severity parts the 2026-08-30 embedded-parts survey left with no backstop, a fourth that came
  along free behind them, a new attack shape, and a correction to the survey's own reasoning.** The survey's residue named 24 confirmed-defeatable parts and
  singled out these three, deferring them because *"their comparison is a single inline `if` over exit
  codes from several REAL per-engine invocations … not one reusable function called five times."* Checked
  rather than inherited (AGENT-CORPUS-BRIEF.md rule 12), that is right for 63 and 62 and **WRONG for 70**:
  PART 70's verdict runs through `w70` (the per-cell checker — the same `name() { python3 -c '` shape
  `extract_oneline_func` was built for at PART 72) and `p70` (the aggregator), both already extractable,
  and `w70` takes JSON documents and exit-code strings as argv so it needs no engine at all. Three parts
  were deferred on a property that had been measured on two of them.
  - **The new shape: `run_ifblock_sweep`.** Where a part's verdict IS an inline
    `if [ "$a" = X ] && [ "$b" = Y ]; then <OK row> else <FAIL row>; FLAG=1; rc=1; fi` written out once per
    engine, the block is extracted from `run.sh` live (same "never a frozen copy" discipline as every other
    runner) and re-executed in a scratch shell with the per-engine exit-code variables bound to poison
    values. **The near-miss legs are GENERATED, not listed**: one per conjunct, each holding every other
    conjunct at its passing value, plus the accept-known-good — which is this file's own stated mitigation
    for four rounds of hand-authored poison closing exactly the mutant its author imagined. An **arity
    ratchet** hard-stops the gate if a future rung adds a conjunct without its leg, so "already swept"
    becomes structural instead of remembered. Both new hard stops were probed rather than assumed: adding
    a fourth conjunct to a swept chain printed `ARITY DRIFT … holds 3 test(s) but 2 expectation(s)`, and
    giving a conjunct a passing value the near-miss table does not know printed `NO NEAR-MISS DEFINED`,
    each exit 1 without reaching a PASS/BROKEN row.
  - **Both the part's flag AND `rc` must move.** `rc` is the suite's exit code; the part's own `_BAD` flag
    only picks MATCH vs DIVERGE. Deleting `rc=1` from PART 63's ambiguous-callee arm while leaving
    `P63_BAD=1` makes the part print DIVERGE while `conformance/run.sh` **exits 0** — reproduced, and
    caught only because both are asserted.
  - **Coverage: 12 if-blocks (76 conjuncts) across PART 63, PART 62 and PART 65, 21 `w70` legs and 8
    `p70` aggregator legs for PART 70** — 117 new rows (88 if-block: 76 near-miss + 12 accept-known-good;
    21 `w70`; 8 `p70`), every one falsified. **PART 65 is the evidence that a SHAPE beats a fixture**: once
    `run_ifblock_sweep` existed it cost two call lines and ten legs with no new harness — ⟨0.32⟩'s other
    side (a derived file set may certify, and must not certify past a FAILED derivation), whose own header
    warns that *"the certify row is the one that can go silent: it asserts exit 0, so an engine that
    quietly stopped peeking would still pass it."* PART 63 is the MEASURED candor-query
    0.31.0 false green (gate a member beside an unrelated sibling and a refusal becomes `policy ✓`); PART
    62's conjuncts each name a distinct measured mechanism, including candor-java's Gson `getAsBoolean`
    reading `"peeked": "true"` as true and carving an unread class out silently; PART 70's
    `ctl-violating(ok-absent)` leg is the over-charge control that stops an engine passing all three cause
    cells by withdrawing `ok` unconditionally, i.e. by deleting the verb.
  - **Falsified exhaustively, not spot-checked.** A harness that SOURCES the shipped runner functions out
    of `mutation-gate.sh` (never a reimplementation) and re-issues the shipped call lines against a
    scratch-degraded `run.sh`: **76/76 conjuncts** neutered in turn (`[ "$v" = X ]` -> `[ "$v" = "$v" ]`, and
    `-ge` likewise, which keeps arity so the ratchet does not short-circuit it) each flipped **exactly**
    its own leg;
    **17/17 `w70` branches** degraded across the full comparison vocabulary (identity->truthiness,
    `isinstance` dropped, emptiness dropped, each presence/exit-code branch neutered) each flipped exactly
    the intended leg(s); **3/3 `p70` aggregator mutations** likewise. Two findings came out of the sweep
    itself: the anchors now name a VARIABLE and never its expected value, because with the value in the
    anchor one conjunct per block was covered by the anchor guard rather than by a leg of its own; and a
    whole-file substitution meant to degrade `w70` silently hit `CHAN_PY`'s identically spelled line ~5,000
    lines earlier, producing a "no change" that reads exactly like "the leg does not discriminate".
  - **Extraction is now memoised per run.** `--extract-var` parses all ~16,000 lines of `run.sh` through
    `check_nested_quotes.py`'s quote-aware scanner, once per leg — measured at **29 seconds for a single
    extraction** on a loaded machine, with the gate unfinished after seven minutes. The cache lives in the
    run's own `$W` (fresh per invocation, deleted on exit), so the source is still read live from `run.sh`,
    just once per name per run; a failed extraction still caches empty and still hard-stops.
  - **NOT reached, named rather than left silent:** the other 20 confirmed-defeatable embedded parts (4l,
    7, 8, 13, 13b, 15b, 15c, 18, 23, 27, 32, 33, 35, 40, 43, 47, 55, 60, 64, 84) and PART 9's structural
    gap. PART 64 and the `cfg_probe`/`check_polfail`/`check_agents`/`p64_row` family among them are the
    same two shapes this wave built, so they are where the next session starts. Also not attacked here: PART 70's `ck70` instrument check, and PART 62's `mut62`/
    `mut62p` mutation helpers with their own vacuity guards.

- **THE 2026-08-30 REVERT-TEST DAY: candor-spec's own conformance/mutation machinery, revert-tested for
  the first time.** Every other family repo has run the "revert the fix, does a test go red" attack
  (engines 24/24 protected, the umbrella 3/9 gaps now closed) — the repo where the machinery itself lives
  never had. Thirteen same-day fixes to `conformance/run.sh`/`conformance/mutation-gate.sh` (7cddc1b,
  e1ce567, 357ace7, 746a42c, 90cee30, d268537, 6b38130, d3ca815, 9c1b6fb, 01c7fd5, 292d8f9, 0b015d3,
  d202f42) were revert-tested. Method note first: most of these fixes are hardenings to the GATE's OWN
  poison generation, not to a checker under test — reverting a poison-hardening commit and re-running
  `mutation-gate.sh` against the CURRENT (already-correct) checkers is GUARANTEED green regardless, since
  a correct checker rejects weak and strong poison alike. The real test (matching what each commit's own
  message already claimed) is: degrade a COPY of the real checker exactly as the commit describes, and
  confirm the OLD poison set wrongly accepted it while the NEW one catches it — done directly (seconds
  each, via `extract_pyvar`/`extract_func` against the live `run.sh`) rather than through the full 8-minute
  scripts for every one of the ~20 individual bypasses this surfaced. RESULT: every fix checked came back
  GREEN — genuinely defended, not decorative — with two additionally checked against real pre-fix engine
  binaries in throwaway clones: candor-rust `27f4beb^` (PART 85, peek scope-match) read DIVERGE against
  the fixed java/ts/swift's MATCH, and candor-spec's own `probe_check.py` genuinely fails naming a stubbed
  `gen_trust_monotonicity.py` (7cddc1b's own claimed repro, reproduced independently). Full detail —
  including the retro_test.py 15/15 calibration run and the direct A1-A5/S1-S6/B1-B3 bypass reproductions
  — is in the session record; nothing required a code fix, because nothing was found undefended.
  Standing controls reconfirmed on a clean tree throughout: `conformance/run.sh` OK, `mutation-gate.sh` OK,
  `must_ledger.py` 521/521 classified, `retro_test.py` 15/15, skip-ratchet unrisen.

- **THE 46-UNRESOLVED EMBEDDED-PARTS BUCKET, corrected.** e1ce567's 2026-08-29 survey left 46 of
  `run.sh`'s 68 embedded parts UNRESOLVED by its mechanical neuter (a different `sys.exit` spelling or a
  bash `[ ]`/`-eq` chain). That bucket was never 46 uniform unknowns: 5 (the gen_*.py-driven PARTs
  25/26/28/29/31) are now genuinely backstopped by `probe_check.py`'s COVERED wiring (90cee30/7cddc1b);
  12 more (PART 67/69/71/73/74/75/76/77/78/79/81/82) share one bash-equality/AND-chain shape the neuter
  missed only on formatting, and hand-generalising it to them reproduced the SAME defeat the original
  15/16 showed — CONFIRMED DEFEATABLE, not hardened; and PART 85 was independently RESOLVED via the
  pre-fix-binary method above. 18 of 46 resolved this session (numbers and per-part detail in
  `conformance/mutation-gate.sh`'s EMBEDDED-PARTS SURVEY comment); 27 remain genuinely unattacked. An
  unresolved part is not a passing part, and neither is a merely-confirmed-defeatable one — both buckets
  are now named rather than folded into one count.

- **THE 27 UNRESOLVED EMBEDDED PARTS, ATTACKED: 27 of 27 have no working backstop, 2 now hardened.**
  The 2026-08-29 survey's mechanical AND-chain neuter — and the follow-on hand-generalised sweep that
  closed 12 more the same day — could not locate a comparison at all for 27 parts: 4l, 7, 8, 9, 13, 13b,
  15b, 15c, 18, 23, 27, 32, 33, 35, 40, 43, 47, 55, 60, 61, 62, 63, 64, 65, 68, 70, 84. Applied the
  unconditional-pass test to each BY HAND: find the verdict-controlling comparison (almost always one
  bash function — `p61_row`, `cfg_probe`, `vocab_probe`, `ep_probe`, `dp_probe`, `zm_probe`, `perow`,
  `peurow`, `p18fail`, `check_agents`, `check_polfail`, `p64_row` — or a small number of inline
  `if [ COND ]; then OK else BAD=1; rc=1; fi` blocks sharing one aggregator variable, or a delegated
  `python3 gen_*.py || VAR=1` call for PART 27/43/55), force it to the pass branch in a throwaway
  mutation of `run.sh`, and confirm via a REAL `part.sh <id>` run that the part still prints its own
  MATCH/OK line with nothing else reacting. **26 of 27 are CONFIRMED DEFEATABLE this way, each
  reproduced, not asserted** (13/13b/32/33/35/40/84 needed the unmarked PART 10 slice as a named
  co-dependency for `$GDIR`; 15b/15c needed `10 14 15`; 18 needed `16` — several of those runs' overall
  exit code stayed nonzero even after the neuter, confirmed via an UNMUTATED run to be PART 10's own
  vocab-arm drift and PART 16's java containment discovery form, both pre-existing on this checkout and
  unrelated to the part under test, the same "live drift in a sibling checkout" class the 2026-08-29
  survey named for 4k/16/34/4n). **PART 9 is the 27th, and it is not a test failure**: its own header
  already says "CONTROLS: none — advisory rows print WARN and set nothing", and a grep of its body
  confirms zero `rc=1`/`_OK=1`/`_BAD=1` anywhere in it — there is no comparison to invert because PART 9
  never controls the verdict, so it is EQUIVALENT to an unconditional pass by design rather than merely
  defeatable as one. The honest numerator: 27 of 27.

  **Two of the 26 are hardened in `conformance/mutation-gate.sh`**, chosen for severity the same way
  earlier waves did — verdict/disclosure and refusal, both with a measured real-engine history. **PART
  68** (a verdict row must carry the unit it is about, SPEC §2 ⟨0.32⟩ — the exact "two byte-identical
  rows a reader cannot tell apart" defect measured live on candor-ts/java/swift 2026-08-24) gets THREE
  independent near-miss poisons for its three distinct failure branches — byte-identical rows (the
  historical defect itself), same hash with distinct text (isolates hash-UNIQUENESS from whole-row
  equality), and correct-but-out-of-order hashes (isolates the sort-key clause PART 63 cannot see) —
  each poison's `rev` arm pinned to the SAME (rule,hash) pairs as its `twin` so the independent REV check
  cannot mask which branch actually caught it (an earlier draft's poisons tripped on REV by coincidence
  before this was fixed). Extracted via the EXISTING `extract_heredoc` — PART 68's `check.py` is written
  to disk via `cat > file <<'PYEOF'` rather than piped via `python3 - <<'DELIM'`, but `extract_heredoc`
  is delimiter-driven, not preamble-driven, so no new extraction code was needed. **PART 61** (a typo'd
  effect name must be refused, exit 2, never silently answered, SPEC §3.1 — measured on all four engines)
  is the exact `extract_func` shape already used for `ck83_defect`/`ck83_control`, but `p61_row` shells
  out to a real query binary for its three probes rather than reading a JSON document, so it is poisoned
  via a tiny STUB command keyed on the effect name (never a built engine) rather than a document, with a
  near-miss per historically-load-bearing exit code: the typo answering 0 instead of 2 (the defect
  itself) and the known-absent effect ALSO refusing at 2 (indistinguishable from "path always refuses",
  the exact failure mode PART 61's own header says its control exists to rule out). **Both falsified
  against a plausible regression** in a scratch copy of the relevant function/script (dropping PART 68's
  byte-identity-and-hash-uniqueness checks; dropping PART 61's `$absent = 0` clause): the poisons built to
  isolate each dropped check flip from CAUGHT to WRONGLY-ACCEPTED, and the others are unaffected — proof
  the near-misses test the branch they claim to, not merely trip a neighbour by coincidence.

  **Not hardened, named rather than left silent**: the other 24 confirmed-defeatable parts, and PART 9's
  structural gap. The highest-severity of those — **PART 63** (a sibling report cannot answer for another
  member, SPEC §2.2/§3.3.1 ⟨0.32⟩ — MEASURED as a real false-green on candor-query 0.31.0) and PART
  62/70 (completeness/refusal) — are not function-shaped: their comparison is a single inline `if` over
  exit codes from several REAL per-engine invocations computed earlier in the same `run.sh` slice (PART
  63's AND-chain alone spans five separate un-parameterised call sites, one per engine, not one reusable
  function called five times), which is real per-part fixture-and-stub engineering rather than a
  mechanical follow-on from what PART 68/61 needed. Left for the next session rather than rushed, per
  BACKLOG.md's own per-part table.

  Controls held throughout: `conformance/run.sh` OK, `mutation-gate.sh` OK (the 7 new PASS lines plus the
  canary's own `BROKEN canary cannot-fail` line), `must_ledger.py` 521/521 classified (12 unenforced,
  unchanged), `retro_test.py` 15/15, `probe_check.py` 8/8 properties, skip-ratchet baseline unrisen (3
  skips over 7 keys, 6 fell, none risen).

- **PART 79 gains a fourth cell: a `dlopen`/`dlsym`-resolved (or `transmute`-of-a-raw-pointer)
  function pointer, INVOKED, must disclose `Unknown`/`callback:*`, never `"functions": []`.** Closes
  two BACKLOG.md OWED items with one fixture, because the shapes coincide (both are "a function
  pointer this engine cannot see the definition of, invoked"): (1) PART 79 pinned `ec3e50f`'s
  mechanisms 1 (`@_silgen_name` bodyless linkage) and 3 (the raw-syscall allowlist) but had no
  fixture for its THIRD swift mechanism, `dlsym`/`unsafeBitCast` — added as `swift-defect-bitcast`
  (`unsafeBitCast(raw, to: (@convention(c) () -> Void).self); fn()` → `Unknown`/`callback:fn`) plus
  its over-charge control `swift-ctrl-bitcast-uncalled` (the same cast, never invoked, must carry only
  its own `dlopen`'s `native:dlopen` and nothing more). (2) `grep "callback:fn-pointer" candor-spec`
  returned nothing — rust-deep's own correct disclosure for a runtime-resolved fn-pointer invocation
  (`callback:fn-pointer / closure`, verified against candor-rust's own multi-spelling test suite) had
  no conformance row, sound but unguarded against regression. Added as `rust-deep-ctrl-dlsym`/
  `rust-deep-ctrl-dlsym-uncalled`, sharing the SAME new rust fixture functions (`dlsym_call`/
  `dlsym_uncalled`, a `std::mem::transmute::<_, unsafe extern "C" fn(i32) -> i32>` of an opaque
  pointer — the libc-primitive twin of `libloading::Symbol<T>`) as `rust-scan-defect-dlsym`, which
  pins candor-rust `defe53d`'s OWN fix: rust-scan silently dropped this exact call shape until today.
  **Falsified against pre-fix binaries, both built in throwaway clones:** candor-rust `defe53d^` reads
  `dlsym_call` absent from `functions` entirely (HEAD: `["Unknown"]|["callback:unresolved call"]|-`);
  candor-swift `ec3e50f^` reads BOTH the bitcast defect and its control absent (HEAD:
  `["Unknown"]|["callback:fn"]|-` and `["Unknown"]|["native:dlopen"]|-`). rust-deep's cell is
  **explicitly a PIN of pre-existing correct behaviour, not a regression fixture** — `defe53d` touched
  only rust-scan's source, and rust-deep already read the correct value on the `defe53d^` binary;
  stated as such rather than implying a falsification that does not exist.

- **`conformance/mutation-gate.sh` gains two new checker shapes and two new PARTs, from the
  2026-08-29 EMBEDDED-PARTS SURVEY (see below): `extract_heredoc`/`run_exitcode_heredoc[_accept]` for
  a `python3 - ARGS <<'DELIM'` differential (PART 46, a caller of a body-less local declaration must
  not be certified pure), and `extract_oneline_func`/`run_stdout_oneline_func` for a same-line-close
  `name() { python3 -c '<PY>' ARGS; }` function (PART 72's `eq72`, the byte-equality primitive behind
  SPEC §3.1 ⟨0.24⟩'s route-equality MUST) — the latter is a genuinely new extraction shape,
  unreachable by `extract_func`'s existing own-line-`}` assumption. Both new extractors live in
  `scripts/check_nested_quotes.py` (`--extract-heredoc`, `--extract-oneline-func`) rather than as
  inline `python3 -c` calls inside `mutation-gate.sh` itself, deliberately avoiding the exact
  nested-single-quote hazard this whole file exists to police.

- **THE 2026-08-29 EMBEDDED-PARTS SURVEY.** `mutation-gate.sh` covered PARTs 36/37/38/39/83 plus the
  14 standalone `conformance/*.py` checkers; the other ~66 PARTs whose comparison is written directly
  into `run.sh` had never been attacked (BACKLOG.md "THE BIGGEST STRUCTURAL FINDING"). Measured: **68
  of `run.sh`'s 86 `part.sh --list`-addressable PARTs are embedded and outside both gates.** For each,
  its verdict-controlling comparison was replaced with an unconditional pass and the part re-run via
  `part.sh <id>` against the CURRENT, otherwise-unmodified fixtures: **15 of 68 were confirmed
  mechanically defeatable** (the row's own success line survived neutering with zero other row
  reacting — structurally inevitable, since none of the 68 touches this file's extraction machinery,
  but reproduced with real exit codes rather than asserted); **46 of 68 are UNRESOLVED** by the
  mechanical neuter (a different `sys.exit` spelling, a bash `[ ]`/`-eq` chain, or a THIRD,
  previously-unnamed class this survey also found — external `gen_*.py` property generators, e.g.
  `gen_chain_idempotence.py`/`gen_trust_monotonicity.py`/`gen_signature_monotonicity.py`/
  `gen_incomplete_dominance.py`/`gen_fs_kind.py`, driving PARTs 25/26/28/29/31, none of them in
  BACKLOG's 14-item standalone list and none attacked here either); **7 of 68 read STILL-RED after
  neutering, but every one was CONFIRMED — by re-running the same part on an unmutated `run.sh` — to
  fail IDENTICALLY with no mutation applied at all**, so none demonstrates a real backstop: 3
  (PART 15/12b/12c) hit `part.sh`'s own documented cross-slice isolation limit, and 4 (PART 16/34/4k/
  4n) reflect an unrelated, pre-existing divergence live in the candor-rust/candor-java checkouts
  beside this repo at survey time (both repos were under concurrent, unrelated edits during the
  survey). Two of the 15 confirmed-defeatable are hardened in `mutation-gate.sh` above (PART 46,
  verdict/soundness; PART 72, route-equality — SPEC §3.1 ⟨0.24⟩'s MUST, whose own header states no row
  anywhere in this suite had ever asked it before today). **Not hardened, stated explicitly rather
  than silently:** the other 13 confirmed-defeatable parts (10, 14, 19, 20, 21, 22, 45, 4h, 56, 57,
  58, 59, 5b, 80 — disclosure/completeness/refusal properties among them), the 46 UNRESOLVED parts,
  and the 7 INCONCLUSIVE ones. This is a survey boundary, not a claim the rest are safe.

- **`conformance/mutation_poison_gen.py` (new) + `mutation_poison_configs.py` + `retro_test.py` +
  `generator_canary.py`: THE GENERATOR mutation-gate.sh's own header judged owed on a fourth
  same-shape round (see the entry below) is built.** It walks a checker's OWN Python source via
  `ast` — never a maintained list of past bypasses — classifies every comparison into one of the
  four historical shapes (`is True`/`is False` identity, exact `==`/`!=` including numeric/string,
  exact list/set equality, an `isinstance` guard, plus bare key/element PRESENCE), resolves each one
  to a concrete field of a human-supplied accept-known-good baseline document (the one piece of
  domain knowledge no source-reader can derive — "what does a real report look like" — kept separate
  from the poison, which is 100% mechanical), and emits the matching near-miss family named in the
  brief (truthy-not-True, falsy-but-present, genuinely-absent-key, wrong-type, superset, subset,
  substring) by perturbing ONLY that one field and holding the baseline's other fields constant — the
  same per-condition-isolation discipline "B1" forced into every hand-authored fixture. **Reaches BOTH
  checker shapes named in the task**, via extraction paths that stay bug-for-bug with the ones
  `mutation-gate.sh` already trusts: `--extract-var` for a bash-variable checker (`VD_PY`), a small
  same-convention brace-matcher for a bash-function-wrapping-`python3 -c` checker (`ck83_defect`/
  `ck83_control`), and direct file reads for standalone `conformance/*.py` files (never a frozen
  copy). **An unclassifiable comparison is reported LOUDLY, per file/line/source-text, and is either
  waived in `mutation_poison_configs.py`'s `WAIVERS` with a stated reason (the same convention
  `clause_check.py`'s citations and `must_ledger.py`'s `unenforced` already use) or left FAILING the
  run — never silently dropped.**

  **Retro-test (`retro_test.py`), the calibration control** (`[[candor-oracle-disclosure-recall]]`
  applied to the generator itself): the eleven historical comparison-shape bypasses (A1-A5, S1-S6)
  were originally reproduced by degrading `mutation-gate.sh`'s OWN fixtures, never the checkers —
  confirmed unaffected in `git log -- conformance/run.sh` across those dates. The generative mirror
  of "a fixture too weak to catch this" is "a CHECKER degraded to this shape would slip past the
  poison": each bypass's exact textual degradation (e.g. `d.get("ok") is not False` → `d.get("ok")`)
  is applied to a COPY of the real, correct checker source, and the SAME mechanically-generated
  poison (derived from the real source, never re-tuned per bypass) is asserted to flip from correctly
  REJECTED (real checker) to wrongly ACCEPTED (mutant). **15/15 attempted rediscovered** (ten named
  A/S items plus the CHAN_PY identity-degrade the header names in prose without a letter); A5 (`VD_PY`
  `unev`, a list-comprehension projection) is a documented, waived generalisation gap, not silently
  passed over; B1-B3 are a different finding shape (absence-based fixtures, not a checker
  degradation) and are named as not-attempted rather than force-fit.

  **Its own canary (`generator_canary.py`), both directions, across all three invocation shapes**
  (embedded/pyvar, embedded/bashfunc, standalone/extfile): an unconditional-accept mutant of a real
  checker (body replaced with `sys.exit(0)`/`return 0` regardless of input) is FOUND (never silently
  absent from the report — evaluate_checker always returns rows) and FOUND BROKEN (every poison-
  rejection row flips to BROKEN; the accept-known-good row correctly stays PASS, since accepting a
  valid document is not itself wrong for an unconditional-accept checker). A second canary — a
  checker that raises on every input, including its own accept-known-good document — is BROKEN with
  explicit crash evidence in every row, never silently read as a correct rejection (mirrors
  `mutation-gate.sh`'s own "a checker crash must not masquerade as an engine disagreement"). Caught
  live while building this: the "extfile" invocation path (`run_checker`) executed the checker's REAL
  path on disk directly rather than routing through `source_fn()`, so every mutation test against a
  standalone file silently ran the UNMUTATED checker and reported its ordinary, correct behaviour —
  fixed by writing `source_fn()`'s content to a scratch file (in the checker's own directory, so
  `HERE`-relative sibling lookups still resolve) and executing that instead; in ordinary,
  non-mutated operation this is behaviourally identical to running the file in place.

  **Run against the six previously-confirmed-defeatable, unhardened checkers** (`incomplete_check`,
  `fs_position_check`, `clause_check`, `probe_check`, `must_ledger`, `part_declarations`) — its first
  real test, not a demo on checkers already known to be clean:
  - **`incomplete_check.py` and `fs_position_check.py` fit the generator's document-via-argv shape
    directly and are now FULLY mechanically covered** — every comparison the classifier can resolve
    (7 of 9, 7 of 8 respectively; the remainder are argc guards and one inline comprehension-loop-
    variable filter, both waived with reasons) correctly rejects its generated near-miss and accepts
    the known-good baseline. `fs_position_check.py` needed two real classifier extensions built
    against it: (1) a "select" key-path step — resolving a helper like `paths(fns["exfil"])` back to
    "the `functions` entry whose leaf name is `exfil`, then its `paths` field" by COMPILING the
    checker's own comprehension filter (`str(f.get("fn","")).replace("::",".").split(".")[-1]==leaf`)
    into a real callable via `ast.unparse`+`compile`, never reimplementing the leaf-matching
    convention by hand; (2) runtime disambiguation of a bare `"X" in Y"` between dict-key PRESENCE and
    LIST-ELEMENT membership from the baseline's actual type at that position, since both parse to an
    identical `ast.Compare` and only the DATA distinguishes them (a checker that tests
    `"incomplete" not in resolves`, a list, is a different mutation shape from `"ok" in d`, a dict).
  - **`clause_check.py`, `probe_check.py`, `must_ledger.py`, `part_declarations.py` are OUT OF REACH
    for this generator's design, and it says so rather than shipping a partial pass over them.**
    Measured, not assumed: classifying all four found ZERO comparisons resolving to an injectable
    document (`clause_check`: 1 comparison, a deliberate substring test with no equality to degrade;
    `probe_check`: 2, plain-scalar/subprocess-exit-code checks with no document at all — this
    checker's entire JOB is running OTHER scripts under an env var, there is nothing to poison;
    `part_declarations`: 4, all cardinality/count guards over locally-parsed text; `must_ledger`: 5,
    all over ledger-entry dicts loaded from a file path bound through a MANUAL `while args: ... pop(0)`
    flag parser (`--spec`/`--ledger`), a materially different CLI shape from every `sys.argv[N]`
    checker this generator's argv-tracer already handles, compounded by a real cross-document sha256
    binding a poison would need to preserve to look like anything other than "unreadable input"). The
    common cause: these four read SPEC.md/run.sh/part.sh's own OUTPUT directly, hardcoded relative to
    `HERE`, with no CLI seam a poison document could occupy — the SAME structural boundary this
    session's own survey already named ("a different, larger mutation-testing project"). Extending
    reach to them would mean modelling manual argv-flag parsing and, for two of the four, mutating
    real SPEC.md/run.sh content in a mirrored scratch directory rather than swapping one JSON field —
    named as the concrete next step, not silently assumed impossible forever.
  - Two REAL, pre-existing generalisation gaps were found and waived with reasons rather than forced:
    `VD_PY`'s `unev` mode and `ck83_control`'s AS-EFF-006 membership both feed a list/set-equality or
    membership check through a per-item PROJECTION (`[u.get("rule") for u in ...]` /
    `sorted(v.get("rule") for v in ...)`) one level before the comparison — reconstructing the object
    shape a superset/subset poison would need means inverting the projection, which this generator
    declines rather than guesses at. Both conditions are independently covered elsewhere (`unev` by
    mutation-gate.sh's own hand-authored A5 fixture; ck83_control's OWN byte-equality check, a
    structurally different whole-document comparison with no single key path, is the row that already
    catches the case AS-EFF-006 membership would otherwise miss on its own).

  **Controls:** the over-charge control — the unmodified tree still passes `mutation_poison_gen.py`
  cleanly across all ten registered checkers (0 broken, 0 unresolved after every waiver) — was
  falsified against itself repeatedly while building this: three real generator bugs were caught by
  its OWN output before being trusted (a presence-shape poison direction that ignored which state the
  baseline was already in, silently mutating an already-absent key to itself; a "subset of an
  already-empty expected collection" no-op; a cross-document byte-equality check tripping as a side
  effect of poisoning only one of two documents that must stay byte-identical for `ck83_control`'s
  OTHER conditions to be isolated at all). `bash conformance/mutation-gate.sh` and
  `bash conformance/run.sh` both pass, run serially in the foreground, unaffected by these additions
  (no existing checker body touched). `must_ledger.py`: unaffected (no SPEC.md clause touched — these
  are new tooling files, not a spec surface). **Filed, not fixed, in the umbrella `candor` repo's
  BACKLOG.md** (out of this repo's ownership): the "generator now owed" entry there should be updated
  to reflect this closure and its stated residual (the four meta-checkers, `must_ledger.py`, and the
  two waived projection gaps).

- **`conformance/mutation-gate.sh`: a survey of all 85 addressable PARTs found `mutation-gate.sh` had only ever attacked 5 of them (36/37/38/39/83), and found a WHOLE UNCOVERED CLASS — 14 standalone external checker scripts (`conformance/*.py`, invoked by `run.sh` with report paths/exit codes/output strings as plain argv) that `mutation-gate.sh`'s extraction machinery (`extract_pyvar`/`extract_func`) structurally cannot reach, because it only pastes code out of `run.sh` itself and these are separate files.** The universal test this file's own header recommends trying first — replace the checker's body with an unconditional `sys.exit(0)`, see whether any row goes red — was executed (not reasoned about) against all 14 via `conformance/part.sh <id>`; 13 gave a conclusive result (the 14th, `skip_ratchet.py`/PART 84, reads a skip-tally log the full suite accumulates, so `part.sh 84` alone is INCONCLUSIVE by its own unbound-variable guard regardless of the checker — not tested standalone). **All 13 tested SURVIVED it: `check_honesty.py` (PART 1c), `file_set_check.py` (48), `only_check.py` (49), `incomplete_check.py` (50), `fs_position_check.py` (51), `peek_completeness_check.py` (52), `refused_peek_check.py` (53), `peek_route_equality_check.py` (54), `exec_capability_check.py` (66), `clause_check.py`, `probe_check.py`, `must_ledger.py`, `part_declarations.py`.** `check_honesty.py` is the starkest: it is candor's ONE machine-verifiable check for the family's cardinal sin (a silent under-report), and its own CONTROLS comment in `run.sh` reads "none — every row asserts document CONTENT" — a `check_honesty.py` silently degenerated to `sys.exit(0)` would be caught by NOTHING in the ~15,800-line suite. **Seven of the 13 are now hardened** — chosen for severity, matching "verdict, route-equality, disclosure, refusal, completeness": `check_honesty.py` (2 conditions: the DIRECT form and the PROPAGATION form of the honesty invariant), `file_set_check.py` (the effect-membership filter and the reason-substring check), `peek_completeness_check.py` (all three `is not False`/`is not True` identity checks, attacked with the SAME truthy/falsy-but-wrong-type near-miss that broke VD_PY/ck83_defect/ck83_control previously — `peeked: 0`/`peeked: 1` instead of JSON `false`/`true`), `refused_peek_check.py` (the `"outOfScope" in docs["A"]` PRESENCE check, attacked with a present-but-empty value a truthy-degraded mutant would misread as absent), `peek_route_equality_check.py` (the flagship route-equality checker: byte-equality degraded to a LENGTH check — same shape as `ck83_control`'s fix, a same-length space-for-tab swap — plus the `ok`/`incomplete` identity checks), `exec_capability_check.py` (the `"Exec" not in got` effect-membership check on both the must-be-Exec and must-not-be-Exec arms), and `only_check.py` (the AS-EFF-011/AS-EFF-009 collision check — NOT a hypothetical: this checker's own header documents candor-rust and candor-java SHIPPING exactly that defect, a rule disclosed as unanswerable and evaluated anyway). Every poison/accept fixture was individually validated by direct invocation against the live, unmodified checker before being wired into the gate (`run_ext_reject`/`run_ext_accept`, a third runner shape alongside the existing `run_failline_bashfunc`/`run_exitcode_pyvar` — no extraction needed, since these files already ARE their own current source). **Six remain confirmed-defeatable and NOT yet hardened, stated as an open boundary rather than silently assumed safe:** `incomplete_check.py` (PART 50), `fs_position_check.py` (PART 51), `clause_check.py`, `probe_check.py`, `must_ledger.py`, `part_declarations.py`. **The other ~66 of the 85 addressable PARTs decide pass/fail via checker logic embedded DIRECTLY in `run.sh`** (a bash `[ "$a" = "$b" ]`, an inline `python3 -c` snippet, or a literal `diff`) rather than a separately-invokable unit, and were NOT executed against in this survey — spot-reading three of them (PART 33's engine-pin exit-code equalities, PART 59's shared `p59` refusal checker, PART 84's `skip_ratchet` caller) found the same nameable-checker shape recurs, which is evidence the technique likely generalizes, not proof it does; this is INFERRED, not measured, and stated as such. **The four comparison shapes behind every bypass in this file's history — identity-to-truthiness, exact-equality-to-membership/subset, a dropped `isinstance` guard, absent-key blindness — recurred YET AGAIN today, for a fourth independent round, this time across an entirely new class of checker (standalone files, not `run.sh`-embedded ones) that had never been attacked at all.** This file's own header already named the threshold for building a generator that derives poison mechanically from a checker's own comparison shape rather than hand-authoring it ("a FOURTH round finding a same-shape gap should flip that trade, given this is already the third") — today's round clears that threshold, on a new surface, and the generator is now judged worth building rather than continuing to hand-author against a fixed checklist. **Controls:** every new poison fixture reproduced with real output against the live, unmodified checker before being added (rejects the poison, accepts the known-good document); `bash conformance/mutation-gate.sh` and `bash conformance/run.sh` both pass (`mutation-gate: OK`, `conformance: OK`), run serially in the foreground. `must_ledger.py`: unaffected (no SPEC.md clause touched).

- **`conformance/mutation-gate.sh` + `scripts/check_nested_quotes.py`: three more defects in the SAME-DAY mutation gate (`73173de`/B1), all found by an adversarial review and reproduced before touching anything.** (1) **A3, the sharpest — the canary's self-proof was DEFEATABLE.** `extract_func` matches only the exact literal `^fn() {` on one line; reformatting the canary's opening brace onto its own line (`cannot_fail_check()\n{`) makes extraction fail, and a failed extraction was recorded as a BROKEN row with the SAME text (`BROKEN  canary  cannot-fail`) the outermost check greps for as proof the intended NameError fired — so an extraction failure was indistinguishable from catching the real bug, and the gate printed `mutation-gate: OK` either way. Reproduced live: the reformatted-brace canary passed `mutation-gate: OK` on the pre-fix gate. Fixed two ways: `require_extracted` turns ANY extraction failure (canary or real checker) into an immediate hard FAIL distinct from a BROKEN row, and the outermost check now additionally requires the canary's actual captured output to contain the specific `NameError`/`zeroMatch` text its own header documents, not merely the word BROKEN in a status line built independently of it. (2) **A2 — the gate proved rejection, never acceptance.** A checker degenerated to unconditional "always reject" (e.g. RS_PY_FAILCLOSED's body loosened to `ok = False`) passed every poison leg while being dead. Reproduced live: mutating `RS_PY_FAILCLOSED` this way left all three isolated poison legs reading PASS and the gate still printing `mutation-gate: OK`. Fixed with `run_failline_bashfunc_accept`/`run_exitcode_pyvar_accept`: one genuinely valid, checker-specific document per checker/mode (17 new accept-known-good assertions across PART 36/37/38/39/83), required to be ACCEPTED, run under the same `real` KIND so a regression trips the same outermost check. (3) **A4 — the nested-quote lint protected only itself.** `conformance/run.sh`'s standing lint scanned `"$HERE/run.sh"` alone, so `mutation-gate.sh`, `canary/cannot-fail.sh`, `part.sh`, `publish-floor-notes.sh`, and `lean/check.sh` — every one a real bash script capable of the identical `python3 -c '...'` corruption — were never checked. Widened to every `*.sh` file in the repo, discovered fresh each run (`find`, not a hand-list), excluding `conformance/canary/` (its one file deliberately carries this exact bug as the gate's own liveness control and must never be "fixed"). Deliberately NOT widened to `*.py`: tried it first — pointing the lint at the `.py` generators produced 93 findings, none real, because this lint implements BASH quote-removal grammar and a plain `.py` file has no shell-quoting layer for this bug class to live in at all (e.g. a Python dict literal `'rust=pub fn entry() {{ ... }}'` reads exactly like a bash `NAME='...'` assignment to a parser that doesn't know it's looking at Python) — attacking the brief's literal "every shell and python checker" phrasing rather than implementing it as stated, confirmed by grepping every `conformance/*.py`/`scripts/*.py` for a self-shelling `python3 -c '...'` shape and finding none. Also fixed in the same lint: a false positive on the `'...'$'\n''...'` ANSI-C splice idiom (used to embed a literal newline between two ordinary single-quoted script pieces) — the lint had no notion of `$'...'` at all and misread it as the same multi-segment corruption shape as a real bareword split; added `scan_ansic_quoted` and an `ansic` segment kind, proved both directions in `--selftest` (`ansic-splice`: clean; `ansic-splice-plus-real-bug`: the splice stays silent AND a genuine corruption in the SAME file is still caught). **Controls, falsified against the pre-fix files before touching anything and re-confirmed after:** A3 — the reformatted-brace canary now makes the gate FAIL (was `OK`); A2 — the `ok = False` degenerate checker is now caught via its accept-known-good row going BROKEN (was `OK`); A4 — a real corruption planted in a file other than `run.sh` (`conformance/`, non-canary) is now caught by the exact widened-scan command (was invisible to it); over-charge control — the unmodified tree still passes `mutation-gate: OK` (canary aside) and `check_nested_quotes.py --selftest` passes all 8 cases. `must_ledger.py`: unaffected (no SPEC.md clause touched). `conformance/run.sh`: OK. `conformance/mutation-gate.sh`: OK.

- **`conformance/mutation-gate.sh`: three MORE bypasses, in the SAME gate the previous entry just hardened, all reproduced with real mutated output before touching anything.** The A2/A3/A4 fixes above closed the holes they targeted but not the one this entry closes — THE ROOT CAUSE, one sentence: poison documents and accept-known-good documents differed in key PRESENCE, not key VALUE, so a checker degraded to presence-only testing passed both halves. (1) **VD_PY, worst — up to 8 of 9 modes.** `vd_empty.json` (`{}`) poisoned seven modes by total key absence, and each mode's accept-known-good document carried the same key with its correct value. Mutating the `ok0` arm to `if want=="ok0" and "ok" not in d: bad.append(...)` — dropping the value comparison — still rejected `{}` (key genuinely absent) and still accepted `{"ok": false}` (key present): PASS on both legs, `mutation-gate: OK`, reproduced live. Fixed by rewriting every affected poison as a near-miss (same shape, every key present, exactly one field's value wrong); `nozm` is left as an absence poison because it is genuinely a presence rule (a fully-binding verdict must carry no `zeroMatch` at all), verified rather than assumed. (2) **ZR_PY_HAS_OK/ZR_PY_NO_OK (PART 38), two distinct bypasses.** `ZR_PY_HAS_OK` mutated to `sys.exit(0 if len(d)==2 else 1)` — dropping the isinstance and key checks — passed every leg because the fixtures in play (lengths 1, 1, 2) happened to land on the side of `==2` that matched the real verdict; fixed by padding the length-1 fixtures to match, closing off length as a distinguishing signal. Separately, `ZR_PY_NO_OK`'s 4-key marker OR narrowed to a single `"incomplete" in d` also passed every leg, because the only accept-known-good document ever exercised carried `incomplete`; fixed by adding one accept-known-good document per remaining marker (`judgedNothing`, `noManifest`, `unanalyzed`). (3) **The canary's "positive evidence" check was a substring grep.** A `cannot_fail_check` body of nothing but `echo "Traceback...="; echo "NameError: name 'zeroMatch' is not defined"; exit 1` — no nested-quote construct anywhere in it — satisfied the BROKEN row and the NameError/zeroMatch grep alike, and made the gate print `mutation-gate: OK`, reproduced live against the pre-fix file. Fixed by tying the evidence to the canary's SOURCE: the extracted `cannot_fail_check` function body is now also run through `scripts/check_nested_quotes.py` (the same independently-validated, shfmt-cross-checked parser this gate already trusts for extraction), and the gate hard-fails unless that lint finds the real corruption INSIDE the extracted function text — an echo-only fake has zero such findings by construction, and extracting only the named function means a decoy elsewhere in the file can't satisfy this on the real function's behalf. **The same counter-attack applied to the four checkers a first pass could not break** (`RS_PY_FAILCLOSED`/`STREAM`, `CHAN_PY`, `ck83_defect`/`ck83_control`) found three more real gaps and one clean negative: `RS_PY_STREAM_FAILCLOSED`'s `if not b: sys.exit(2)` empty-stdin guard had no fixture at all (added one); `CHAN_PY`'s `is not True` on `incomplete` degrades to `not x` undetected because no fixture ever set a truthy-non-`True` value (added `incomplete: 1`); `ck83_control`'s byte-equality poison differed by length as well as content, so `len(sb)!=len(rb)` catches it by accident (replaced with a same-length space-for-tab swap, verified equal `wc -c`); `ck83_defect`'s `is not True` on `ok` was attacked the same way and did NOT break, because every fixture sets a JSON boolean and identity/truthiness agree for booleans — verified clean, left unchanged. **Controls, falsified against the pre-fix file before touching anything and re-confirmed after:** all three reproduced bypasses (VD_PY presence-only, ZR_PY_HAS_OK cardinality, canary fabrication) now make the gate FAIL; the unmodified tree still passes `mutation-gate: OK` (canary aside); `check_nested_quotes.py --selftest` and `conformance/run.sh`'s standing lint both still pass over the rewritten file. `must_ledger.py`: unaffected (no SPEC.md clause touched). `conformance/run.sh`: OK. `conformance/mutation-gate.sh`: OK.

- **`conformance/mutation-gate.sh`: FIVE more bypasses in the SAME gate the previous two entries hardened, all reproduced with real mutated output before touching anything, plus SIX more found by sweeping every remaining checker/mode instead of stopping at the five handed in — including one found only on a SECOND sweep pass, after the first pass's own "clean" note turned out to be wrong.** THE ROOT CAUSE, one sentence: every near-miss and accept-known-good document the prior two rounds introduced still puts a JSON BOOLEAN behind every `is True`/`is False` check, a genuine SUBSET (never a superset) behind every list/set-equality check, and a wholly-wrong STRING behind every string-equality check, so a checker degraded from IDENTITY to TRUTHINESS, from exact EQUALITY to MEMBERSHIP/SUBSET, or from equality to SUBSTRING agrees with the real checker on every existing fixture for accidental reasons and only diverges on a shape no one had tried yet — the third same-day round to close exactly its target and leave the adjacent same-shape gap open. The five assigned: (1) **VD_PY `ok0`/`okt`** — `is not False`/`is not True` degraded to plain truthiness passes every existing near-miss; fixed with a falsy-but-not-`False` value (`ok: 0`) and a truthy-but-not-`True` value (`ok: 1`). (2) **RS_PY_FAILCLOSED/STREAM** — `== []`/`== 0` degraded to a falsy check passes every leg because both existing poisons are present-and-truthy wrong values; fixed with the key genuinely ABSENT (`None` is falsy but not `[]`/`0`), for both the file and stream variant. (3) **CHAN_PY `caveat`** — dropping the `isinstance(...,list)` guard passes every leg because all existing fixtures are either a real list or also-falsy; fixed with a truthy non-list value (`judgedNothing: "x"`). (4) **ck83_defect `r_zm`** — exact list-equality degraded to membership passes the existing wrong-scope poison (absent either way) but wrongly accepts a superset (correct scope plus one extra element); fixed with that superset fixture. (5) **VD_PY `unev`** — exact set-equality degraded to a subset check (`set(exp)<=set(got)`) passes the existing missing-rule poison (a subset either way) but wrongly accepts a superset (both required rules plus one extra); fixed with that superset fixture. **Sweeping the same question — truthy/falsy/wrong-type/superset/subset/substring missing? — across every remaining mode of all eight checkers (not stopping at the five handed in) found six more:** VD_PY's other `is True` leg, `refused`, had the identical unhanded gap (fixed with `refused: 1`); VD_PY's other exact list-equality leg, `zm`, had the identical superset gap as `unev` (fixed the same way); and, most notably, **this file's own prior "verified clean" claim about `ck83_defect`'s `s_ok`/`r_ok` was WRONG** — it reasoned "every fixture in play sets a JSON boolean... there is no third value in play," which is a claim about the fixtures on hand, not about the checker, and re-attacking it with the missing truthy-not-`True` fixture (`ok: 1`) broke it immediately, live. The same shape, never previously attacked, also broke `ck83_defect`'s `s_viol`/`r_viol` (`!= []` degraded to truthiness, closed with a falsy-but-not-`[]` value, `violations: ""`) and `ck83_control`'s `d_ok is not False` (closed with `ok: 0`). **A sixth sweep find turned up only on a SECOND pass through this very entry's own reasoning:** VD_PY's `v005` was first written off as clean ("a string-equality membership test with no boolean/list-equality shape for this class to hide behind") — true as far as it went, but incomplete, because exact STRING equality (`v.get("rule")=="AS-EFF-005"`) degrading to substring membership (`"AS-EFF-005" in v.get("rule","")`) is the identical class one shape over: the existing wrong-rule poison (`"OTHER"`) contains no substring match either way, but `"AS-EFF-0050"` — which CONTAINS the wanted string without equalling it — is wrongly accepted; fixed with `vd_v005_substr.json`. The lesson inside the lesson: "already swept" is a claim about which shapes were tried, not a proof no shape remains. **Verified genuinely clean, not merely untested:** `ZR_PY_HAS_OK`/`ZR_PY_NO_OK`'s `isinstance(d,dict)` guards were attacked the same way as CHAN_PY's (drop the guard, feed a non-dict poison) and did not break — the existing not-a-dict poison already fails with the wrong exit code (0 instead of 1, and 3 instead of 1) the moment the guard is dropped, reproduced live rather than assumed; VD_PY's `viol`/`norefused`/`nozm` are deliberately presence/truthiness checks with no identity/equality to degrade in the first place. **Controls:** all eleven reproduced bypasses now make the gate FAIL against the pre-fix file and pass against the fixed one; the unmodified tree still passes `mutation-gate: OK` (canary aside). **The structural question this raises, not just eleven more fixtures:** every fixture in this file's history has been hand-authored against a specific reproduced bypass rather than derived from the checker's own comparison shape (`is True`/`is False`, `==` over a bool/number/string, list/set-equality, `isinstance`) — a generative approach that mechanically emits the canonical near-miss family (truthy-not-True, falsy-not-False, wrong-type, absent-key, superset, subset, substring) for each shape found in a checker's extracted source would have produced this round's fixtures and the prior two rounds' in one pass each, including the `v005` finding this round's own first sweep pass missed, because those four shapes are the entire vocabulary every bypass in this file's history has used and a mechanical walk cannot forget to check one. Not built here — eight checkers, changing rarely, kept hand-authoring cheaper than trusting a new code-reading tool — but recorded as a checklist in the gate's own header so a future addition to any of the eight is checked against the shape list by hand rather than reinvented, and as the point at which a fourth round finding a same-shape gap should flip that trade, given this is already the third. `must_ledger.py`: unaffected (no SPEC.md clause touched). `conformance/run.sh`: OK. `conformance/mutation-gate.sh`: OK.

- **Declare `0.34`** (`bin/spec-bump.sh 0.34`): all seven declarations now read `0.34`. The MUST ledger
  flagged the versioning-narrative paragraph (SPEC.md Contents, "**Version 0.33** — all code engines
  declare `0.33`...") as changed, since its sha is content-keyed and the bump touched two digits in it.
  Compared word-for-word against the prior `0.33` text: the ONLY difference is the version literal in the
  bold lead-in and the backticked declare-string — every ⟨0.30⟩/⟨0.31⟩/⟨0.32⟩/⟨0.33⟩ rung marker inside the
  paragraph's own reasoning is untouched, because those name specific historical rungs, not the current
  declared version, and the paragraph gained no new rung sentence this time (unlike the 0.31/0.32/0.33
  bumps, each of which added one). Re-hashed and carried the existing `unenforced` classification forward
  with that comparison recorded in `conformance/must-ledger.json` rather than assumed from "it's a version
  bump". Checked candor-spec (SPEC.md, `conformance/`) for the adjacent hazard the family flagged on this
  rung — a `spec-bump.sh` literal rewrite landing on a *semantic* reference to ⟨0.33⟩ (e.g. "a report
  produced before ⟨0.33⟩") rather than a version declaration: none found — every `0.33` left untouched by
  the bump is a rung marker or a version-floor comparison (PART 80's `cur`/`ws` control values, the
  `skip-baseline.json` dated notes), and every occurrence the bump touched (`spec": "0.33"` envelope
  examples, `shipped (spec 0.33)` status cells, the Contents header) was a genuine current-version
  declaration. `must_ledger.py`: 517/517 classified, 12 unenforced. `conformance/run.sh`: OK.
  `conformance/mutation-gate.sh`: OK.

- **`conformance/mutation-gate.sh`: poison documents rebuilt ONE PER CONDITION, not one per checker — BACKLOG.md "B1", reproduced then closed.** The gate built the same day (`73173de`) caught only TOTAL breaks: a poison document that violates every condition a checker enforces at once cannot tell you which one did the rejecting. Reproduced live before touching anything: (1) VD_PY's `ok0` branch loosened to `d.get("ok") is True` (accepting a MISSING `ok` key as satisfying "ok is false") still printed `mutation-gate: OK` — the only VD_PY poison in scope drove the `norefused` mode, never `ok0`, though `vd_doc` calls `ok0` 37 times across PART 36; (2) RS_PY_FAILCLOSED's `bool(d.get("unanalyzed"))` loosened to `"unanalyzed" in d` (accepting a forged all-clear `"unanalyzed": []` as fail-closed) also passed unnoticed — the single poison document violated the other two ANDed legs (`functions != []`, `analyzed.count != 0`) at the same time, so the exit code stayed rejecting regardless of what the third leg's logic did. Rebuilt every checker in scope (PART 36/37/38/39/83, 8 checkers, 36 conditions total) with one poison per condition, each valid in every OTHER respect the checker checks — VD_PY's 9 modes (all covered, none left out) are isolated for free since the checker only evaluates the modes named in its own argv; the ANDed checkers (RS_PY_FAILCLOSED/STREAM, ZR_PY_HAS_OK) get a poison per leg holding the other legs at their PASSING value; ck83_defect/control (8 + 4 conditions, independently `bad.append()`-ing) get a baseline passing scan/report pair perturbed one field at a time. Both reproduced mutations are now caught and pinpointed to the exact condition (`PART36/VD_PY(ok0)`, `PART37/RS_PY_FAILCLOSED(unanalyzed)`) while every sibling condition on the same checker still reads PASS — falsified both directions against the pre-fix gate (prints `OK` on both mutations, reproduced in a scratch copy) and the post-fix gate (fails on exactly the mutated leg, clean otherwise). Over-charge control: the unmodified tree still passes with `mutation-gate: OK`, canary aside. Canary control re-verified both ways: the deliberately-broken canary still reads `BROKEN` (required for a PASS), and a canary whose quoting is "fixed" makes the whole gate FAIL rather than silently reading as one more passing checker. `run_exitcode_pyvar`'s `--stdin` form now takes an explicit poison-file argument instead of one shared global, so each leg of `RS_PY_STREAM_FAILCLOSED` can carry its own document.

- **RETAG: the two clauses added at `3601c04` are ⟨0.34⟩, not ⟨0.35⟩ — there was no 0.34 release to close it against.** `git tag -l`/`gh release list` show v0.33 is latest; ⟨0.34⟩ Item 1 (the refusal-cause wording fix, `0b015d3`) was written into SPEC.md but never cut, so it was still the OPEN rung per the family's own precedent (`eaab823`: "do not open a new rung while the previous one is unreleased"). The `zeroMatch` §3.1 carve-out and the twelve-verb `--policy` rule are now both tagged ⟨0.34⟩ alongside Item 1. Re-classified in the MUST ledger (two statements re-hashed, sha moved, same PART 83/PART 84 classification — the underlying rule didn't change, only its tag) and corrected in `conformance/run.sh`'s PART 84 header comment and `skip-baseline.json`'s ratchet log. `must_ledger.py`: 517/517 classified. `conformance/run.sh`: OK.

- **The `zeroMatch` §3.1 carve-out (Tom's ruling: option D) — BACKLOG "CURRENT QUEUE" item 1, CLOSED.**
  A policy rule scoped to a REAL function that is pure on both the `scan --policy` and `gate --report`
  routes counts as bound on the scan route (silent, correctly) and as unbound on the report route
  (`zeroMatch` fires, incorrectly), because §2.1's report omits pure functions entirely and the report
  route has nothing else to consult — a FALSE DISCLOSURE, never a hidden effect, and advisory-only per
  ⟨0.27⟩'s own MUST NOT (it cannot change `ok` or the exit code). SPEC §3.1 ⟨0.34⟩ now states a NARROW
  carve-out on §3.1's byte-equality MUST, scoped exactly to `zeroMatch` under this one condition, modelled
  on the ⟨0.24⟩ "manifest does not travel" precedent: the scan route's silence is the trustworthy answer,
  the report route's `zeroMatch` entry is evidence of the artifact's limitation, not of a typo'd rule. An
  advisory keyed on `analyzed.count > |functions|` was considered and explicitly REJECTED — that
  comparison is already-known noise (the same `count − |functions|` arithmetic the ⟨0.24⟩ manifest clause
  names as the report's pure-function count, positive on nearly every real report), not a signal scoped to
  the false-`zeroMatch` case. No new wire key. Conformance **PART 83** is rewritten from "records the
  measured divergence, unruled" to asserting the carve-out as SPEC'd behaviour, keeping its
  effectful-sibling control (byte-equal on both routes, proving the divergence stays confined to the
  pure-matched quadrant).

- **The `--policy` usage-error rule, extended from `gains` alone to the full twelve-verb set with no
  policy-derived field, and its conformance loop.** BACKLOG "`--policy` accept-and-drop is THREE engines,
  not one" fixed today (java `37c9b10`, rust `e4bc419`, ts `2c2147e`; swift already conformant) had no
  SPEC clause and no conformance row — the exact gap that let rust and ts drift on ⟨0.34⟩ this morning.
  SPEC §3.3.1 ⟨0.34⟩ now names the full set — `show`/`where`/`callers`/`map`/`diff`/`containment`/
  `reachable`/`path`/`impact`/`blindspots`/`tour`/`rewire` — checked individually against each verb's own
  pinned §3.1/§3.2 JSON shape (not assumed): none carries a policy-derived field, so `--policy` there MUST
  be a usage error (exit 2) naming `gate --report`/`whatif`/`fix`/`fix-gate`/`unverified` as the
  policy-relative alternative, exactly as `gains` already required. Verified per-engine exposure rather
  than copied from BACKLOG's table: candor-java exposes all twelve, candor-rust all twelve (`diff`/`rewire`
  already rejected `--policy` pre-existing, through their own bespoke parsers, untouched by today's fix),
  candor-ts eleven (no `rewire` verb), candor-swift three (`path`/`tour`/`gains` — the other nine/ten
  confirmed structurally absent, not assumed). New conformance **PART 84** (`verb_reject`) mirrors the
  existing `gains_reject` battery with a differential check (a bare-form run vs. a `--policy` run for the
  identical command, so no fixture needs to be independently correct for every verb's own query
  semantics) and was falsified against the pre-fix commits (java `802efe4`, rust `caca530`, ts `b4c3a22`)
  in throwaway clones: every one of the fixed cells silently accepted and dropped `--policy` there (exit
  0/1 unchanged, no diagnostic), and the pre-existing controls (rust `diff`/`rewire`; all four engines'
  `gains`) already correctly rejected it, unmoved.

- **SOUNDNESS.md R64 (ts decorator-argument shapes): two of three closed, verified independently, and the
  third's rejection rationale is now MEASURED rather than folklore.** candor-ts `b4c3a22` mints a
  `<decorator-arg>@<pos>` unit for a raw effect or closure embedded directly in a decorator's own ARGUMENT
  DATA (`@Decorate(fs.readFileSync(...))`; `@Factory({ init: () => { fs.readFileSync(...) } })`, the real
  TypeORM `@Column({ default: () => … })` idiom) — shapes R57's own fix (`0a5d493`) left uncovered because
  it only reached the decorator VALUE, never its arguments. RE-VERIFIED HERE, not taken on the commit or its
  suite: built candor-ts `9a8a5c7` (immediately pre-fix) and `b4c3a22` in a throwaway clone, ran both fixed
  shapes, the still-open third shape (an external body-less decorator reference), and two over-charge
  controls (a literal decorator argument; an argument calling a genuinely pure local function) against both
  binaries. Pre-fix: all five read `functions: []`/`ok:true`/no violations. Post-fix: the two fixed shapes
  disclose `Fs` and fail `deny Fs` (AS-EFF-006); the third shape and both controls are UNCHANGED. The third
  shape's rejection is no longer an unmeasured assumption: `b4c3a22`'s own experiment found a blanket
  variant simulating the rejected fix byte-identical to the shipped fix on 2 of 3 real corpora (a real
  NestJS+TypeORM app, TypeORM's own 513-file functional suite) but **+42 report rows on a base of 80
  (+52%)** on a real Angular app — every bare `@Injectable()`/`@Component()`/`@Pipe()` gained its own row.
  PART 82 (conformance/run.sh) pins both fixed shapes, both over-charge controls, and the third shape as a
  DOCUMENTED-OPEN cell (asserts the CURRENT silent value, not a wanted one — a conformance row pins wanted
  behaviour, not a sin). Cross-engine: structurally ts-only — rust's attribute-macro arguments are
  unevaluated token streams, swift's compiler-plugin macro arguments are compile-time AST, and java
  requires annotation element values to be compile-time constants (JLS 9.7.1), so none of the three permits
  an arbitrary runtime call inside a decorator/attribute argument for an effect to hide inside.

- **The four-way byte-equality blind spot: every family suite tested the wrong kind of miss, never the
  wrong kind of hit — and the missing quadrant does not pass cleanly.** Verified independently before
  acting on it: this suite's own PART 32/36 scope their zero-match fixtures to `zzz_no_such_layer`/
  `zzz.nomatch`; java's `GateReportVerbTest` uses `pure app.Nothing`; ts's `POLICIES` corpus has
  `scoped_none` (`pure ZzzNoSuchScope`) beside `scoped` (`deny Fs src.app.readIt`, a real but EFFECTFUL
  function); swift's `testGateJsonIsByteEqualToTheScanRoute` uses `pure ZzzNoSuchScope` only — four
  independent suites, all exercising a rule that binds NOTHING ANYWHERE, none exercising a rule that binds
  a REAL function that is genuinely pure on both routes. PART 83 (conformance/run.sh) adds that quadrant,
  built fresh in throwaway clones of all four engines rather than against whatever binary happened to be on
  disk, and it does NOT pass cleanly: the persisted report's `functions` array omits pure entries entirely
  (§2.1's purity-by-absence design), so `gate --report`'s `zeroMatch` computation — built from that array
  alone — cannot tell "bound a real, pure function" from "bound nothing", and wrongly emits
  `zeroMatch: ["<rule>"]` for a rule the SCAN route (which sees the full in-memory analysed-function set
  before pure entries are dropped) correctly reads as bound. Measured, fresh, in all four engines; `ok`,
  `violations` and `analyzed.count` never move, so this is a FALSE DISCLOSURE, never an under-report. PART
  83 records this as the CURRENT measured state rather than resolving it — the §3.1 ruling on how to treat
  it is Tom's, open in BACKLOG.md's "CURRENT QUEUE" item 1 — and pairs each defect cell with a control
  scoped to the sibling EFFECTFUL function, proving the divergence stays confined to the pure-matched
  quadrant (both routes byte-equal, `AS-EFF-006`, no `zeroMatch`) rather than a general scan/report split.
  Not gated behind the pending ruling and not scoped away from the quadrant — either would recreate the
  exact blind spot this row exists to close.

- **⟨0.34⟩ ITEM 1 gets its SPEC clause and its conformance PART, after shipping four-way with neither.**
  candor-rust `f10bb82`, candor-ts `9a8a5c7`, candor-swift `fd704b5` and candor-java `fee92bd` all cited
  "SPEC §2 ⟨0.34⟩" in comments the same day `grep -c '0\.34' SPEC.md` returned 0 — the port ran ahead of the
  row, inverting the family's own rule that conformance ROWS beat review panels. That gap had ALREADY
  produced a divergence: candor-rust's `parse_spec_ladder` does not strip surrounding ASCII whitespace
  before parsing the envelope `spec`; candor-ts's does. SPEC §2 now states, normatively, what all four
  engines DO for the ⟨0.33⟩ cross-policy refusal's human-channel message when every report contributing to
  it predates ⟨0.33⟩ — name that cause and remedy ("re-scan with a 0.33+ engine under THE SAME policy")
  instead of the ⟨0.33⟩ "peeked under a different deny set" sentence, which is false of a report that never
  had `scannedUnder` to hold ANY deny set in. Message-only: mints no wire key, moves neither the verdict nor
  the exit code, and `--gate-json`/`whatif --json` MUST be byte-identical between the two sentences — the
  property most at risk from a later well-meaning edit.

  **THE WHITESPACE RULING.** Surrounding ASCII whitespace around the `spec` value MUST be stripped before
  the unparseable test — the same rule §3.4 already states for a config version token ("a trailing `\r` is
  whitespace, not part of the version"). `" 0.33"` is the version 0.33 with incidental padding, not a
  corrupt value; refusing to strip it manufactures the exact false "predates ⟨0.33⟩" diagnosis this rung
  exists to retire, on a report that is not, in fact, old — and this key is explicitly outside the general
  present-but-unparseable-is-a-refusal rule (it is not a verdict input), so a garbled value falls back to
  "cannot answer ⇒ predates" rather than impeaching the document. **candor-java and candor-ts already
  conform (measured); candor-rust and candor-swift do not** (`" 0".parse::<u32>()` errs; Swift's
  `Int(" 0")` is `nil` — neither trims by itself) — filed against each, not fixed here.

  PART 80 (conformance/run.sh): one tree per engine, a genuine ⟨0.33⟩ cross-policy mismatch, and the
  envelope `spec` mutated to five values (`"0.33"` unmodified — the OVER-CHARGE CONTROL — `absent`, `"0.32"`,
  the `"0.9"` lexicographic-ladder trap, and `" 0.33"` for the whitespace ruling) across otherwise-identical
  bytes. Asserts the two sentences, the unchanged verdict/exit code, `--gate-json` byte-equality across all
  five, and PROBES (never hard-codes) the whitespace cell so a currently-unported engine SKIPs, reference-led,
  rather than reddening the suite for a divergence this repo does not own the fix for. Falsified against the
  pre-⟨0.34⟩ commits (candor-rust `3a32fdf`, candor-ts `0a5d493`, candor-swift `ec3e50f`, candor-java
  `802efe4`, built in throwaway clones): all four read `old` on every mutated `spec` value, confirming the
  row measures the fix rather than passing vacuously.

- **SOUNDNESS.md's FFI/extern scorecard row had the same "—"-pasted-across-non-rust-cells shape the macro
  row was just corrected for, and it was NOT the same verdict on every cell.** Measured per engine against
  live fixtures and published/HEAD binaries rather than reasoned from the row's prose: rust-scan's direct
  `extern "C"` handling is genuinely sound (`native:extern fn`), but a `libc`/`nix`/`rustix` call the
  syscall-name table deliberately leaves unclassified silently vanishes with zero disclosure when no
  classified sibling call is nearby (R59, open). rust-deep's prior "verified by construction" claim was
  **false** — its own callgraph proves it visits a local `extern "C"` declaration, but the effect layer
  attaches nothing to it (R60, open) — worse than rust-scan on the identical seam, in the engine positioned
  as the soundness backstop. swift's "—" was as false as the macro row's: raw `import Darwin`/`Glibc`
  free-function calls, `@_silgen_name`, and `dlopen`/`dlsym` + a function-pointer call all read silent-pure,
  `deny Exec`/`deny Fs` passing at exit 0 over code that performs the effect (R61, open). java and ts were
  independently re-measured across native methods / JNA-style zero-impl dispatch / Panama (java) and native
  addons (untyped + `.d.ts`-typed) / WASM / `process.binding` (ts) and are genuinely CLOSED. None of
  R59/R60/R61 is fixed here — candor-spec doesn't own candor-rust or candor-swift; filed against each.
  Full prose: SOUNDNESS-LOG.md, 2026-08-27 FFI-row entry.

- **§4.0's own vocabulary section had gone stale one rung after the FFI row above did.** "Swift's
  syntactic model produces neither `reflect:` nor `native:`" (SPEC.md, the conformance-binding/per-language
  split) was falsified by the SAME candor-swift fix (`ec3e50f`) that closed R61: swift now emits
  `native:<symbol>` for `@_silgen_name`/`@_extern` C-symbol-linkage declarations and an allowlisted set of
  raw C free-function calls. Corrected to state what swift emits instead of what it doesn't, without
  weakening the surrounding MUST — a consumer still cannot assume all four kinds appear in every report,
  since ts folding `native:` into `reflect:` and swift still emitting no bare `reflect:` (its dynamic-member
  access mints its own off-vocabulary `dynamicMemberLookup:` kind instead) both remain true. The must-ledger
  entry for this block was re-hashed by hand after re-reading it (`sha` `0787bc89cdd78787` ->
  `27156e1361006c42`; classification unchanged, `pre-ledger`).

- **R59/R60/R61 all closed the day after this file's audit recorded them open** — verified against the
  fix commits rather than carried over from the prior entry's summary. R59/R60 together in candor-rust
  `3cb1906` (rust-scan's `CALIBRATED_BUT_PARTIAL_CRATES` carve-out for libc/nix/rustix's generic fd verbs;
  rust-deep's unconditional `Unknown`/`native:extern fn` on `is_foreign_item()`, deliberately mirroring
  rust-scan's mechanism rather than the crate-name-keyed `invisible` machinery, so the two engines' answers
  for this seam are byte-identical, not just equivalent). R61 in candor-swift `ec3e50f` (raw Darwin/Glibc
  free-function calls and `@_silgen_name`/`@_extern` disclose `native:<symbol>` via a deliberately
  incomplete allowlist, `dlsym`+`unsafeBitCast` reuses the existing opaque-closure `callback:` path). A
  same-day follow-on audit of the ~79 other `CALIBRATED_CRATES` R59's own fix had left unaudited
  (candor-rust `2feb264`) found three further real gaps, none of them FFI (`clap::Arg::env` -> `Env`,
  `console::Term`'s raw I/O -> `Ipc`, `arboard::file_list`/`Clear::default` -> `Clipboard`) — closed as R62,
  with one low-severity item filed rather than fixed (`wild::ArgsOs`'s Windows-only `Fs` leak, R63). New
  conformance PART 79 pins the R59/R60 byte-parity shape across rust-scan and rust-deep (rust-deep's leg
  SKIPs loudly on a runner without the pinned nightly + `cargo-dylint`, never silently) plus swift's two
  allowlisted mechanisms, falsified against the pre-fix commits (candor-rust `763e51a`, candor-swift
  `52d24b9`) before landing. SOUNDNESS.md's FFI scorecard cells move ⚫->🟡 (closed, regression +
  conformance-gated; not a cross-engine SEAM-matrix cell, matching java/ts's existing convention). None of
  the three fixes claims general closure — each fix's stated limit is recorded beside it.

- **R57 (SOUNDNESS.md) closed and pinned, re-verified independently rather than taken on the fix's own
  commit message or test suite.** candor-ts `0a5d493` mints a position-keyed `<decorator>@<offset>` unit
  for an anonymous decorator function/arrow value before `enclosing()`'s `ts.isDecorator` guard stops the
  climb dead — the guard is correct for a NAMED decorator factory (its effects already land on its own
  unit) but previously dropped an anonymous one's effects with nothing behind it: `deny Fs` over a real
  `fs.readFileSync` sitting directly in an anonymous decorator's body read `ok:true` at exit 0. Rebuilt the
  pre-fix commit (`fbb9ea2`) and HEAD in a throwaway clone and ran the filed repro plus two controls against
  both: the defect cell flips from silent to a caught `AS-EFF-006` violation; a named-factory control is
  byte-identical between the two binaries (the already-sound path is untouched); a genuinely pure anonymous
  decorator stays `ok:true`/`violations: []` on both (the over-charge control — the fix mints a unit without
  fabricating an effect). Ts-only, structurally: a TS/JS decorator is a function the language runtime calls
  at class-definition time, which none of rust's attribute macros, swift's compiler-plugin macros (R56), or
  java's reflection-read annotations have an equivalent of. New conformance PART 81 pins the three cells,
  falsified against the pre-fix binary (two cells move, four do not). **Residual found live-reproducing this
  row, filed as R64, not fixed**: the identical guard still drops a raw effect evaluated directly as a
  decorator argument, a closure nested in a named factory's argument data, and a call through an external
  bodyless decorator reference — all three deliberately left uncovered by `0a5d493`'s own commit message (a
  blanket fix would mint an entry for nearly every decorated declaration in real Angular/NestJS/TypeORM
  code). PART 81 does not assert these stay silent; a conformance row pins wanted behaviour, not a sin.

- **The R55 "ride the documented channel" principle is written down once, non-normatively, at the end of
  SPEC.md §3.1.** Tom's ruling on R55 (candor/BACKLOG.md, option (a): closed rust-local, no SPEC change, no
  MUST, no PART, no four-engine port) asked for the reasoning behind ⟨0.21⟩'s and ⟨0.27⟩'s stderr-to-JSON
  moves to be recorded once as a rationale note, because it had already been re-derived from scratch three
  times (most recently R55's own `receipt` TSV fix). Added as a plain-prose paragraph — no MUST, no
  REQUIRED, no bold kernel — so `must_ledger.py` does not pick it up as a new normative statement needing a
  row (confirmed: 511 statements classified before and after). States what ⟨0.21⟩/⟨0.27⟩ already do inside
  the JSON envelope as description, not as a new obligation over arbitrary formats, and names the promotion
  condition the ruling set: a second non-JSON consumer surface, with a row.

- **PART 78 pins candor-ts's dynamic-re-export disclosure fix (`2365827`), the fifth "neither voice
  fired" instance.** `Object.keys(impl).forEach(k => exports[k] = impl[k])` (and its
  `Object.defineProperty` descriptor twin) binds an export name to a runtime string no static matcher
  can read, so three individually-correct decisions — the alias join finds no match, the covered-package
  arm (SPEC §2 rule 3) declines because the package IS chained, and `unanswerableKey` correctly says the
  key is answerable — compounded into total silence: a real `fs.writeFileSync` reachable only through the
  forwarded name read `policy ✓` at exit 0. Fixed by naming the pattern in the producer's own report
  (`dynamicReexport.count`, never a fabricated per-name entry) and disclosing `Unknown`
  (`reflect:dynamic-reexport:<pkg>`) on every consumer call into a package that set it, at
  `disclosureTail`. Falsified against candor-ts `73100d9` (immediately before the fix, built in a
  throwaway clone): the producer's own `dynamicReexport` key and both consumer calls (`defect-run`,
  `defect-runOther`) all read `absent` where HEAD discloses. THE OVER-CHARGE CONTROL IS HALF THE ROW: the
  genuinely pure `other()`, forwarded through the identical loop, gains the same `Unknown` and never a
  fabricated `Fs`. Three further controls travel both binaries UNCHANGED: an ordinary CJS export gains no
  `dynamicReexport` key, a `Symbol.toStringTag` ESM-interop stamp (a MEASURED real false-positive source
  on a published bundle) is never mistaken for a dynamic forward, and ordinary (non-dynamic) dep-chaining
  stays concrete end-to-end. TS-only — no module-object export surface exists to mutate this way in
  rust/java/swift, structurally absent rather than unaudited.

- **PART 77 pins candor-swift's macro-disclosure fix (`dc27915`) and, with it, corrects a FALSE immunity
  claim in SOUNDNESS.md.** The "macro / codegen reach" scorecard row had read "—" (immune by
  construction) for swift since its first commit, reasoned about only for rust's `macro_rules!`; Swift's
  own compiler-plugin macro system (`@Observable`, `#Preview`, Swift Testing, any `#freestanding`/
  `#attached` macro) was never examined. A freestanding macro with no trailing closure and any attached
  macro attribute (func or type) scanned clean under `deny Net`: exit 0, `functions: []` — no visitor
  existed for `MacroExpansionExprSyntax` at all. Fixed by routing both forms into the existing
  `Unknown`/`unknownWhy` vocabulary (`macro:<name>` / `macro:@<Attr>`); a trailing-closure macro is
  unaffected (already caught concretely). Falsified against candor-swift `70274c3` (immediately before
  the fix): all three defect cells (freestanding, attached-func, attached-type) read `absent` where HEAD
  discloses `Unknown`. Five controls travel both binaries UNCHANGED, incl. the over-charge control that
  mattered most in practice — the compiler-builtin freestanding-literal denylist (`#file`/`#fileID`/
  `#isolation`/…) and a local `@resultBuilder`/`@globalActor` gain nothing; the first denylist cut had
  missed `fileID`/`isolation` and produced 101 hits of noise across swift-nio and Nimble before that gap
  was closed. SOUNDNESS.md's row is corrected to reflect all four non-rust engines were re-audited, not
  assumed clean: swift's cell moves `—` → `🟡` (fixed, R56 closed); ts's own macro-adjacent mechanism
  (an anonymous decorator minting no unit) is a DIFFERENT, still-open finding (R57, `—` → `⚫`, filed
  against candor-ts, not fixed here); java's bytecode-based construction holds for Lombok but is
  UNMEASURED for annotation-processor-generated separate-file codegen (R58, `—` → `🔴`). Full prose:
  SOUNDNESS-LOG.md, 2026-08-27 entry.

- **`conformance/part_declarations.py`'s `# ENGINES:` parser had a silent-misparse trap: a reason
  containing its own `;` could mint a bogus exclusion clause with zero errors.** The parser splits an
  `# ENGINES:` line's exclusions on `;`, so a reason needing its own semicolon for ordinary prose
  ("...macro path; java has no macro system") got cut there — and if the accidental tail happened to
  start with a real engine name followed by `:` (an easy coincidence: "rust"/"java"/"ts"/"swift" are all
  ordinary English words), the tail silently parsed as its OWN, unintended exclusion clause. PLANTED AND
  CONFIRMED: `rust swift; ts: ...macro path; java: has no macro system` parsed with ZERO errors to
  `listed={rust,swift} excluded={ts,java}` — a fully-accounted-for, checker-green declaration nobody
  wrote, the exact "green row asserting less than it claims" shape this project has found four times
  before, now living in the tool that checks for it. Fixed by requiring a literal `;` inside a reason to
  be escaped as `\;`; the parser now splits only on an UN-escaped `;`, so a bare `;` is unambiguously
  always a new clause. Checked every existing `# ENGINES:`/`# CONTROLS:` declaration in `run.sh` (78 at
  the time) for the coincidence: none is currently misparsing — the two agents who hit this while writing
  PARTs 74-76 restructured around it (an em dash for the aside) rather than shipping the ambiguous form.

- **The patch-cycle notes above had nowhere to be announced, and now do.** This section's six
  conformance rows (PARTs 71-76) were the first CHANGELOG content added after `release.sh` cut
  `v0.33` — a patch build for a repo whose GitHub release is tagged at the floor alone, so the cut
  correctly SKIPPED candor-spec (`v0.33` already released) and this section sat written but
  unpublished. Added `scripts/publish-floor-notes.sh`: it folds every `## [0.33.<patch>]` section into
  the existing `v0.33` release's notes (`gh release edit -F`, body only — no tag, title, or SPEC.md
  touched), so the release becomes the running record of everything shipped under the floor rather than
  a snapshot of the day it was cut. Run once against this repo's real `v0.33` release as part of this
  change: the notes above are now live at
  https://github.com/tombaldwin/candor-spec/releases/tag/v0.33. Considered and rejected: a decoupled
  build tag on candor-spec (`v0.33+build.1`) puts a patch-shaped axis on the one tag this repo
  deliberately has none of, and needs the umbrella's `release.sh`/`release-verify.sh` to learn a second
  tag scheme for one repo out of seven; rolling the notes into the next contract rung's release instead
  would publish them, whenever that rung lands, described as work done under a version they were not
  shipped with. Same gap does NOT exist for candor-agents or any other family repo — every other repo's
  GitHub release is tagged at the family build version (`vX.Y.Z`, e.g. candor-agents' `v0.33.1`), which
  moves on every cut, so `release.sh` never skips them for this reason. Filed for the umbrella: `rel
  candor-spec "v$SPEC"` in `bin/release.sh` could call this script right after its skip branch, so the
  fold-in happens automatically on every cut instead of by hand; not done here since that file is
  umbrella-owned.

- **PART 76 pins candor-ts's own-`.d.ts`-shadow fix (the got@15.1.0 corpus find).** npm ships
  `dist/foo.js` beside `dist/foo.d.ts`, and TypeScript's module resolution treats the co-located
  `.d.ts` as authoritative for every CROSS-FILE importer of `foo.js` — even one this scan
  (`--allow-js`) is analysing as its own project source. `declModule` correctly called that `.d.ts`
  foreign, and `crossesPackageBoundary` correctly called it the scan's own package, so neither
  disclosure fired and the call vanished with no edge and no `Unknown`. Fixed by asking the sibling
  IMPLEMENTATION file for its own module symbol and redirecting an unambiguous match onto the real
  declaration; an ambiguous or unminted match still discloses `Unknown` rather than dropping.
  Falsified against candor-ts `965a521` (immediately before the fix): the unambiguous-resolution cell
  and the disclose-rather-than-guess cell both read `absent` where HEAD reads `["Rand"]` and
  `["Unknown"]` respectively. Two controls travel both binaries UNCHANGED: a `.js` with no co-located
  `.d.ts` was never broken, and a same-file reference (never crossing the module boundary) is
  unaffected. TS-only in this pass — java/rust/swift have no comparable declaration-vs-implementation
  split for their OWN source (reasoning recorded, not exhaustively audited); filed to BACKLOG.md.
- **PART 75 pins candor-swift's overloaded-protocol-extension-provided-member fix, a sibling of PART
  73 from the same fix wave but a different code path.** A concrete (non-protocol-typed) receiver
  reaching a protocol extension's provided member called bare `resolveQual` with no `overloadedBases`
  check, unlike its own sibling dispatch arms — so a protocol extension declaring a SECOND, unrelated
  overload of the same member name made the lookup ambiguous and the call's only edge vanished, not
  even `Unknown`. Fixed by routing the same branch through `matchOverloads`: an arity-discriminated
  call resolves precisely, and a genuinely ambiguous one (this engine does not model argument labels)
  gets the sound UNION rather than a drop. Falsified against candor-swift `a9ab1a6` (immediately
  before the fix): the defect cell and a genuinely-ambiguous-pair cell both read `absent` where HEAD
  reads `["Exec"]` and `["Env", "Exec"]` respectively. Two controls travel both binaries UNCHANGED: a
  genuine local override still wins over both provided overloads, and the non-overloaded case (a
  single provided member, no sibling) is unmoved. Swift-only in this pass — an analogous shape in the
  other three engines' own overload-resolution-through-a-default-member code paths is UNAUDITED, filed
  to BACKLOG.md rather than assumed unique to swift.
- **PART 74 pins candor-rust's WalkDir construction-site charging fix.** `walkdir::WalkDir`'s lazy
  disk read happens in `IntoIter::next`, but candor-scan's receiver-typing hard-blocks the
  `.into_iter()` verb everywhere (a guard against fabricating onto a different std type, with no
  per-crate exception for a same-crate return) — so no idiomatic usage (a for-loop, `.count()`, an
  untyped `.next()`) ever reached a typed `IntoIter` receiver, and `deny Fs` exited 0 over code that
  walks the filesystem. Fixed by charging at `WalkDir::new` (construction) instead, mirroring the
  already-modeled `ignore::WalkBuilder::build`/`glob::glob`. Falsified against candor-rust `8734b87`
  (immediately before the fix): three independently-idiomatic silent forms (for-loop, `.count()`,
  untyped `.next()`) all read `absent` where HEAD reads `["Fs"]`. Three controls travel both binaries
  UNCHANGED: the narrower typed-annotation shape the old rule already caught, the sibling `ignore`
  crate's already-modeled construction charge, and the std-`Vec` iterator the receiver-typing
  blocklist exists to protect. Rust-only — java's bytecode charges the producing call directly so the
  mechanism does not apply there; ts resolves through a real type-checker rather than a syntactic verb
  blocklist; swift's third-party-package analogue is UNAUDITED, filed to BACKLOG.md.
- **PART 72 pins §3.1's byte-level route-equality MUST — unclassified in must-ledger.json since the
  ledger was frozen, and unexercised by any row despite PART 48/62/69 already driving `scan --policy`
  against `gate --report` exhaustively.** None of those puts a REAL violation in the analysed code at
  the same time as a peeked, matching-policy exclusion and then compares the two routes' `--gate-json`
  documents BYTE-FOR-BYTE rather than by exit code alone — exactly the gap the SPEC paragraph names and
  a corpus round would hit first (one real crossing, one class it could not fully read). MEASURED: the
  property already holds at HEAD and on each engine's own pre-⟨0.32⟩ route-split commit, so this row is
  MUTANT-FALSIFIED rather than pre-fix-binary-falsified — two independent corruptions of an otherwise
  genuine two-step report (stripping the violation; emptying `outOfScope`/`excluded`) both change the
  verdict document, one of them (`outOfScope`/`excluded`) WITHOUT changing the exit code, which is the
  concrete reason this row asserts document equality and not exit parity. Four-way; the clean tree is
  the over-charge control.
- **PART 73 pins candor-swift's `#if`-gated free-function shadow fix (the ifhedge-A corpus find).** A
  same-module `#if os(Windows) func getenv(_:) { … } #endif` with no `#else` permanently shadowed the
  `Env` heuristic for every build, including the one that never contains the stub — `deny Env` exited 0
  over code that reaches `Env` on every real platform. Fixed by tracking conditionally-compiled
  declarations separately, so a name shadowed ONLY by a conditional declaration unions the heuristic's
  charge with the declaration's own effects instead of suppressing it. Falsified against candor-swift
  `bcb4bc8` (immediately before the fix): the defect cell read `absent` where HEAD reads `["Env"]`, and
  a fourth cell (the conditional stub performing a real `Log` effect of its own) read `["Log"]` where
  HEAD unions to `["Env", "Log"]`. Two controls travel the same pre/post-fix binaries UNCHANGED: an
  unconditional same-module `getenv` still shadows exactly as before, and the same call with no `#if`
  block at all is unmoved. Swift-only — candor-rust's `#[cfg(...)]` analogue is UNAUDITED, filed to
  BACKLOG.md rather than assumed clean; java and ts have no compile-time conditional-declaration
  construct.
- **PART 71 pins the ⟨0.30⟩/⟨0.33⟩ emission rule that two engines contradicted on day one.**
  `outOfScope` and `scannedUnder` are present **iff a policy was CONFIGURED and HONOURED** — and
  present-and-empty is a claim ("asked and clear"), which must not collapse into the ⟨0.26⟩ *cannot
  answer* an ABSENT key means. Measured over a policy-scanned tree with NO exclusions: java and rust
  emitted both keys; **candor-ts and candor-swift emitted neither.** Both were code defects, not
  fixture gaps — each gated its emission block on an extra clause with no basis in SPEC (`policyPath
  && excludedFiles.length`, `!peekRules.isEmpty && !peekable.isEmpty`), so "nothing to exclude" was
  read as "nobody asked". Fixed in candor-ts `a34b273` and candor-swift `5f5240b`. The row's controls
  are the deliverable: NO policy → both keys ABSENT, and a REFUSED policy → both ABSENT, because
  emitting `[]` there would be a fresh false claim in the opposite direction. Falsified against
  pre-fix worktrees of both engines rather than against already-fixed code.
- **A checker that cannot fail is the same defect one layer up — closed with a standing lint plus a
  mutation gate, both proven able to fail.** Measured twice in one day (PART 80 and PART 83's first
  drafts, both already fixed before landing): a bash single quote has no escape, so a Python dict-key
  literal (`d.get('ok')`) nested inside a `python3 -c '...'` body (or a `NAME='...'` variable later fed
  to one) silently truncates the script at that apostrophe, and the damage is invisible on the PASSING
  path because the corrupted line is usually the message-building/failure branch, which only runs on a
  real divergence — a checker built this way prints a clean OK forever and cannot report FAIL.
  `scripts/check_nested_quotes.py` is a standing lint for the class: it implements bash's real
  single/double-quote and heredoc rules (not an approximation — its own build caught itself on three
  separate real bugs, including one that hung the lint outright on `conformance/run.sh`'s own
  `HERE="$(cd "$(dirname …)" …)"` line before the fix), tells the corruption shape apart from the one
  deliberate, correct use of the same quote-splitting idiom already in this file (`$HERE` spliced into
  PART 23's `sys.path.insert`), and is cross-checked against `shfmt -tojson` (a real, independent bash
  parser) rather than trusted on its own say-so. Swept `conformance/run.sh` (the only checker script in
  this repo using inline interpreters): **zero live instances of the bug** — both known cases had
  already been fixed same-session, per SOUNDNESS-LOG — and 2 correctly-recognised safe interpolations,
  matching shfmt's AST exactly. Wired into `conformance/run.sh` itself, ahead of any engine build, so a
  future regression fails the whole suite before ~8 minutes of engine builds are spent on it.
  `conformance/mutation-gate.sh` goes one level further: for the release-gating checkers (PART 36
  verdict-document cells, PART 37 report-sink fail-closed shape, PART 38 zero-rule-policy refusal, PART
  39 report-consuming-verb re-disclosure, PART 83 byte-equality quadrant — 9 checkers total, pulled LIVE
  out of `run.sh` rather than a frozen copy), it feeds a poison document each checker MUST reject and
  requires a clean rejection (a literal `FAIL:` line where that is the checker's own contract, a specific
  nonzero exit code with no traceback where it is not) — never a crash, never silence, never an accepted
  poison. `conformance/canary/cannot-fail.sh` carries the REAL bug (not a synthetic stand-in) as the
  gate's own liveness proof: the gate's outermost check is the single readable assertion that its output
  contains the line `BROKEN  canary  cannot-fail`, in BOTH directions — missing OR the canary reading
  PASS are both treated as the gate having gone dark. Falsified before shipping: a real checker
  (`RS_PY_FAILCLOSED`) was deliberately given the same bug shape and the gate caught it (then the file
  was restored); the unmodified tree passes with only the canary showing broken; the canary's own crash
  (a `NameError`, not a `FAIL:` line) is reported as broken, not as a pass. NOT covered, stated rather
  than assumed: PART 2/3/12 and PART 29/32/34/47/57/59/60/61/62/67/68/69/70/72 — those rows drive real
  engine binaries over source fixtures rather than taking a JSON document directly, so "feed it a poison
  document" does not apply the same way; extending the gate to them is future work.

- **The versioning-narrative paragraph gains its ⟨0.34⟩ sentence — the gap `bin/spec-bump.sh 0.34`
  left behind, closed.** The bare declare-bump above landed the version literal but, unlike the
  ⟨0.31⟩/⟨0.32⟩/⟨0.33⟩ bumps, added no sentence saying ⟨0.34⟩ is non-additive, even though it genuinely
  is. Added, checked word-for-word against ⟨0.34⟩'s own SPEC clauses and against PART 80/83/84 rather
  than assumed from its own wording: two of ⟨0.34⟩'s three parts cost a consumer nothing (the ⟨0.33⟩
  cross-policy refusal's cause-naming fix for a report predating ⟨0.33⟩ is message-only — verdict, exit
  code and the gate document stay byte-identical; the `zeroMatch` §3.1 carve-out RELAXES byte-equality
  rather than tightening it), and the third breaks: `--policy` on any of the twelve verbs with no
  policy-derived field is now an exit-2 usage error where it was silently accepted before, bounded to
  invocations that pass the flag. The first draft of this insertion added a blank line before the
  following `**0.23 is a tier-1...**` block, splitting what has always been ONE continuous
  versioning-narrative paragraph (every ⟨0.30⟩–⟨0.33⟩ sentence was appended with no blank line) into
  two — which orphaned the existing MUST-ledger entry AND left the `0.23...` rung-history block
  unclassified for the first time, three findings from one formatting slip. Fixed by removing the
  blank line (restoring the single block, matching every prior rung's own shape) rather than writing a
  second classification entry for a split that should never have existed; `conformance/must-ledger.json`
  re-hashed to the merged block's new sha, with PART 80/83/84 added to the entry's exercised-by list
  for ⟨0.34⟩'s three parts. Also corrected PART 83's own header comment and its two `echo`/`print`
  lines in `conformance/run.sh`, which still read "records the divergence rather than resolving it" /
  "the §3.1 ruling is Tom's, open" / "unruled" — stale since `3601c04` landed the ruling itself, despite
  that commit's own message claiming the rewrite had happened. `must_ledger.py`: 517/517 classified, 12
  unenforced. `conformance/run.sh`: OK. `conformance/mutation-gate.sh`: OK.

- **⟨0.34⟩ gains its fourth part, and the OWED row for it: the PEEK SCOPE-MATCH PROPERTY, plus the
  conditional `dispatch-widened` fallback — SPEC §2/§6.2, conformance PART 85, four-way.** Closes the
  FOUR-WAY CARDINAL SIN found 2026-08-29 and fixed same-day with four genuinely different mechanisms
  (swift `7378f4f`, rust `27f4beb`, java `a034371`, ts `8584572`), which had landed in all four engines
  with no SPEC clause and no conformance row under it — exactly the ⟨0.34⟩ mistake ("ports ahead of
  rows") CLAUDE.md now names, at three times the scale that cost the first two follow-up fixes.

  **The property**, stated so the fix does not re-narrow to the instance that found it: a peek finding
  MUST be scope-matched against, or attributed to, any in-scope caller whose own analysis over the union
  of context and excluded material reaches the effect — not only the excluded declaration's own
  qualified name. §6.2's `<scope>` test now runs against the finding's attributed name AND against every
  in-scope function the peek's own resolution shows reaching it. Attribution (which declaration a finding
  NAMES) is unchanged; only the scope test widens.

  **`dispatch-widened`** is the conditional fallback where the responsible excluded declaration cannot be
  named with confidence: the finding is disclosed against the in-scope call site, as an `outOfScope[].class`
  value (never `excluded[].class` — the two `class` fields stay independent vocabularies), rather than
  dropped. It is CONDITIONAL, not mandatory four-way: only an engine whose peek unions in-scope and
  excluded material can ever reach the ambiguous case it exists for. candor-rust's peek never re-analyses
  in-scope files — it cross-references facts the primary scan already computed — so its attribution is
  never ambiguous and it MUST NOT be required to emit the class; swift, java and ts DO union and DO need
  it. An engine MUST NOT emit `dispatch-widened` where the declaration COULD be named with confidence
  (the over-charge direction).

  **PART 85** pins both, four-way, with the fixture shape all four fix commits share (an in-scope
  dispatcher through a shared interface/protocol/trait, a pure visible implementer, and a SEPARATE excluded
  conformer performing the denied effect, reached only through that dispatcher): a `deny Net Runner`-shaped
  scoped rule now catches it (the defect, closed); the unscoped form of the same rule stays a single
  finding (the pre-existing control, unaffected); a scope matching neither the declaration nor any reaching
  caller stays silent (the over-charge control). Each engine's cell also asserts `dispatch-widened` does
  NOT fire in this unambiguous fixture — the BACKLOG's own over-charge requirement — and a separate ts-only
  arm proves the class genuinely fires when attribution is truly unresolvable (an unattributable
  `paths`-mapped interface reference, reusing ts's own regression fixture shape). **Falsified against each
  engine's own pre-fix commit** in throwaway worktrees before being trusted: rust, java and swift all
  reproduce the exact silent exit-0 shape on `27f4beb^`/`a034371^`/`7378f4f^`; ts required `npm install` in
  its pre-fix worktree to run at all, then reproduced identically. The java fixture uses a FLAT
  compiled-output layout rather than a nested one, deliberately: a nested `classes/` subdirectory trips an
  unrelated, ancillary classpath-resolution bug the same fix commit also happens to close, which would
  have conflated two different defects in one row.

  MUST ledger: 4 new part-named entries (the property clause, the fallback clause, and the conditional
  clause, all PART 85) plus a re-hash of the ⟨0.34⟩ versioning-narrative block for its now-FOUR parts;
  521/521 classified, 12 unenforced (unchanged). `conformance/run.sh`: OK (see the run log). No existing
  row weakened; the skip-ratchet baseline is untouched.

- **SOUNDNESS.md and SOUNDNESS-LOG.md: seven entries for 2026-08-29's cardinal sins**, each with its
  commit and its measured evidence — the four-way peek scope-match sin above; rust-deep's `Drop` in
  move-captured closures and `drop(x)` container walking (`3e9848c`); swift's R33 deinit-glue binder-shape
  gap (`10dc79e`); java's record `ObjectMethods` contract-method reentry, falsified on 388 real jars
  (`3a84522`); candor-agents' `deny Unknown` compiling to nothing (`69e9e98`), the first time that repo had
  been attacked; the consumer-refusal class across `integrations/` (candor `0d483a8`/`ac4a71b`), the most
  consequential class found this session because it sits downstream of every completeness rung ever
  shipped; and the 13-of-13 standalone-checker survey (`90cee30`), the third "instrument that cannot fail"
  found in overlapping investigations the same week.

- **`conformance/gen_differential.py`: the multi-caller callback row, now unblocked** (ts `d5f6c0c`, swift
  `7a89dbc` both fixed the underlying fabrication first, per the BACKLOG's own ordering — "fix the engines
  before extending the generator here, or the generator will bless it"). A new compound shape,
  `callback_multi` (two entry fns sharing ONE HOF: one caller's callback performs the effect, the sibling's
  is pure), built directly in `build_cells()` since a single name/single accept-set cell cannot express two
  entry points sharing one declaration. **The acceptance rule is split, deliberately, because reusing the
  existing single-caller `acc_callback` tolerance here would rubber-stamp the exact fabrication this row
  exists to catch**: the effectful caller keeps the existing tolerance ({effect} | {Unknown} |
  {effect,Unknown}), but the pure sibling's accept set EXCLUDES the effect entirely ({} | {Unknown} only) —
  reporting the sibling's effect, with or without an `Unknown` alongside it, can only mean the engine
  inherited its neighbour's resolved target rather than resolving its own call site. Verified against the
  current (fixed) engines: all 4 agree on all 117 cells including the 9 new multi-caller ones, matching the
  BACKLOG's own measured table (rust hedges `Unknown` on both callers; java resolves per call site
  precisely; ts/swift now correctly answer pure on the sibling). **Falsified against the pre-fix binaries**
  in throwaway worktrees (`d5f6c0c^`, `7a89dbc^`): every sibling cell reddens as FABRICATION on both ts and
  swift, while the effectful-caller cells and the pre-existing single-caller `callback` cells stay in the
  accepted band — proving the new row would have caught the original bug without touching any existing one.

## [0.33.0] — 2026-08-26
- **SOUNDNESS.md closes R54 and R55, and a MUST-ledger sentence that was false is corrected.**
  R54 (`diff`) and R55 (`receipt`) still read `SILENT (open)` while four commits had closed them.
  The ledger entry for ⟨0.33⟩'s strictly-absent `scannedUnder` case claimed it was "pinned in the
  engines' own suites" — true of rust, java and swift, and not of candor-ts, which had no such test.
  A register that reads as considered is worse than one that reads as open.

- **MIGRATING TO ⟨0.33⟩ — who it breaks, what it costs, and the one command that discharges it.**
  ⟨0.33⟩ is NOT ADDITIVE. The cost was measured before the cut rather than estimated: **32 real
  third-party projects, 67 reports, 402 report×policy pairs, all four engines**, published **0.32.1**
  binaries as the producer against **0.33** HEAD as the consumer.

  **WHO IS AFFECTED.** Anyone gating a **STORED** report that a pre-0.33 engine produced — a report
  committed to a repo, cached between CI jobs, or published by a dependency and gated downstream. A
  pipeline that scans and gates in ONE run under ONE policy is **unaffected**: producer and consumer
  are the same run, so the recorded deny set IS the gate's, `P ⊆ P` holds by construction, and §3.1
  route equality means the scan route's verdict is byte-unchanged.

  **THE COST.** Of the 265 pairs that exit 0 under 0.32.1, **202 — 76.2% — become exit 2** under 0.33
  with the policy unchanged. That is not a rate to sample against; it is decided by one bit in the
  report. A report carrying any `peeked: true` class refuses **202 of 202**. A report carrying none
  passes **63 of 63**. **26 of the 32 projects** have at least one such class, so most repositories
  with a stored report will meet this on their first 0.33 gate.

  **THE REMEDY, and it discharges the cost in full.** Re-scan with a 0.33 engine **under the SAME
  policy the gate applies** — not merely *a* policy. That loose wording is the reading this rung
  exists to close: it is what let a peek bounded by `deny Net` be read as an answer about `Exec`.
  All **265 of 265** pairs green under 0.32.1 are green again after the re-scan. No residual tax, no
  permanently-refusing configuration, nothing to suppress or waive.

  **AND THE UNCOMFORTABLE PART, stated rather than softened.** The operators this hits are precisely
  the ones who followed ⟨0.32⟩'s own remedy — *scan with the policy* — because that is what puts a
  `peeked: true` class into a report in the first place. They migrated one rung ago and are being
  asked to migrate again, for a hole that remedy did not close. The wording was the defect and the
  wording is the fix: the rule is now the SAME policy, and `scannedUnder` is what makes it checkable
  instead of advisory.

  **WHICH WAY IT FAILS: CLOSED.** An absent `scannedUnder` is the EMPTY SET for the subset test, so a
  pre-⟨0.33⟩ report beside a `peeked: true` class refuses rather than certifies. Two controls say the
  refusal is not indiscriminate: **62 pairs** whose producer's deny set genuinely covers the gate's
  produced **0 refusals** — legitimate narrowing is not over-charged — and over the full cross-policy
  sweep of **918 gates**, **529 refuse correctly and none fails open**.

- **⟨0.33⟩ THE CROSS-POLICY HOLE — `scannedUnder`, and a gate that refuses a peek it did not
  commission.** `excluded[].peeked: true` was only ever true *relative to the deny set the producer
  held* — ⟨0.29⟩ bounds the peek to effects that policy DENIES — and the report never recorded what that
  set was. A consumer gating with a different deny set therefore got a definite answer to a question
  nobody asked, and it failed OPEN on `gate --report`, the supply-chain route, past every ⟨0.32⟩
  control, because the class really was read. Measured on candor-java 0.32.1 over a tree whose excluded
  source runs `Runtime.exec("id")`: `scan --policy 'deny Net'` exits 0 with `peeked: true` and
  `outOfScope: []`; `scan --policy 'deny Exec'` over the same tree exits 2; and
  `gate --report <the first report> --policy 'deny Exec'` answered exit 0, `no violations`.

  The envelope gains **`scannedUnder: { "deny": [ "<expanded rule>", … ] }`** under exactly
  `outOfScope`'s emission rule — present iff a policy was CONFIGURED and HONOURED, absent when none was
  configured, absent over a policy the engine REFUSED. The rules are recorded in the **expanded form the
  matcher used**, one element per rule, deduplicated and sorted: effect NAMES would reintroduce the
  flattening defect ⟨0.30⟩ closed one layer down (`pure` names nothing), and raw policy text fails OPEN —
  two configs defining `unknown-alias corp` differently give the identical line `deny Unknown[corp]` two
  meanings, so comparing raw text reads a producer that asked the weaker question as having answered the
  stronger one. A gate whose own expanded deny set is not a
  subset of it, over a report carrying any `peeked: true` class, answers `ok: false`, `incomplete: true`,
  exit 2, names the rules that went unasked, and points at re-scanning under **the SAME** policy. The
  ⟨0.24⟩ advisory verbs follow, as ⟨0.30⟩ and ⟨0.32⟩ each had to be amended to say.

  **NOT ADDITIVE, in the ⟨0.32⟩ direction and for the same reason.** An absent `scannedUnder` is the
  EMPTY SET for the subset test, so a pre-⟨0.33⟩ report carrying `peeked: true` fails closed — the
  producer's silence about the QUESTION must not be read as an answer about the CODE. It identifies a
  pre-rung producer precisely (under the ⟨0.29⟩ bound a class reaches `peeked: true` only when the
  producing scan held a deny rule) and the remedy is exact. §3.1 route equality holds BY CONSTRUCTION:
  on `scan --policy P` the producer and the consumer are one run, so `P ⊆ P` and the rule cannot fire.
  Conformance PART 69, reference-led — candor-java shipped it first, and candor-scan, candor-ts and
  candor-swift have since ported it. Each row PROBES that engine's own policy-scanned report for
  `scannedUnder` rather than reading a list here, so every one started asserting on its porting commit
  with no edit to `run.sh`; the three baseline entries were then deleted one at a time, each with the
  measurement that attributed the fall. **The DECLARATION has moved and the FLOOR has not.** SPEC.md's
  header now reads `**Version 0.33**` and all four code engines print `spec 0.33`; the released floor
  stays 0.32, because the spec repo tags `vX.Y` when the floor rises and there is no `v0.33`. *These two
  sentences said the opposite through the declaration bump — that the rung was reference-led and that
  the header still read 0.32 — which is the same sequencing error the bump made in the MUST ledger: a
  claim about the current state, written before the commit that changed it, and not re-read after.*

- **`check_agents_drift.py` now sweeps README.md and AGENTS.md for prose spec claims.** Checks 2 and 3
  read one JSON envelope in AGENTS.md and every JSON fence in SPEC.md; nothing ever read README.md, whose
  family table states the contract FIVE times as `**shipped (spec X.Y)**` and which is the first document
  a reader of the spec meets. Each of the four code engines gained a sweep of its own README at ⟨0.32⟩;
  the repo that DEFINES the version was the one left without one. The floor is derived from SPEC.md's
  `**Version X.Y**` line, the `(spec X.Y, informative)` marker is the escape hatch for a deliberate
  historical note, and a control fixture runs first so a silent sweep cannot be read as a clean one.
  SPEC.md itself stays JSON-only, for the reason check 3 already states: its prose is dense with true
  statements about past rungs.

- **The claim grammar's own example carries the `, informative)` marker.** The comment explaining why the
  grammar takes one to EIGHT separators quotes SPEC.md's aligned `"spec":    "0.32"` as the six-separator
  case — a historical illustration, not a claim about this repo's floor. `release-preflight` [2b] cannot
  tell the two apart, and from 0.33 onward it read that line as a bare-literal spec assertion left behind
  by the bump. The family's escape hatch is the marker this very file implements, so it is applied here:
  the illustration keeps its concrete version (which spellings were live in shipped documents at 0.32 is
  the point of the sentence) without becoming a release-day false positive at every rung.

## [0.32.1] — 2026-08-25

- **No contract change — the floor stays 0.32, and a patch is a build id rather than a rung.**
  `git diff v0.32..HEAD -- SPEC.md` is empty, which is how this family decides a patch mechanically, and
  the conformance suite pins the same floor on both sides of it. An engine declaring `spec 0.32` is
  conformant across 0.32.1 in either direction; no consumer needs to do anything.

  The tag exists because the family line carries ONE number. candor-java's v0.32.0 native binaries were
  never published — `native.yml`'s parity gate failed the build after the image reported `0 functions`
  over a tree the jar found 210 in — and `ENGINE_PIN`, which `candor update` and the Homebrew formula
  resolve for every engine at once, cannot move for one repo alone. So the family moves together, and the
  contract sits still while it does.

## [0.32.0] — 2026-08-25

- **The ⟨0.32⟩ bump left `spec 0.31` in five README rows and three SPEC.md envelope examples.** The rows
  described what was *published*, which is why they read as correct — but they move with the cut, like
  every other staged version string. The three envelope fences sat under a `**Version 0.32**` header:
  the drift gate holds AGENTS.md *against* SPEC.md and never read SPEC.md back, so the document defining
  the contract was internally inconsistent and no gate could see it. `check_agents_drift.py` now sweeps
  SPEC.md's own `"spec": "X.Y"` fences against its declared floor, with a control proving the
  `, informative)` exemption discriminates.

- **⟨0.32⟩ THE DESCRIPTIVE HEDGE NAMES `callers`, `impact` AND `path` — AND THE PIN THAT WAS MISSING IS
  THE ONE THAT CATCHES A REVERT.** §2 Rung A's ⟨0.32⟩ narrowing shipped for `show`/`map`, which OVER-hedged
  (the caveat replaced the answer). These three are the same clause read from the other side: they answered
  FLAT at exit 0 with no caveat on either channel over a report declaring an unread `excluded` class, in
  candor-rust, candor-ts and candor-java alike — an empty `direct` saying *nothing calls this*, an
  `affectedCount: 0` saying *safe to edit*, an empty `path` saying *this function does not reach that
  effect*, each asserted over code nobody read. That is the cardinal-sin direction, and §2 now says so
  beside the over-hedge one rather than filing it as more of the same. Their root key sets are already
  fixed, so nothing nests and the caveat keys join them at the root; candor-swift ships only `path` of the
  three and already hedged on both the populated and the EMPTY arm.

  **Conformance now fails BOTH reverts, and neither guard covers the other.** PART 40's oracle scored any
  document carrying a live disclosure key as `PASS hedged` before looking at anything else, so a hedge that
  ATE the answer was invisible; the two-entry `_rk` map that closed that for `show`/`map` is now
  `DESCRIPTIVE_RESULT`, derived from the oracle's own result-key table so the two cannot drift, with
  `whatif` the single deliberate omission because it answers `ok`. The OPPOSITE revert — back to a flat
  answer — never reaches that guard at all: carrying no disclosure key, the document falls through to
  `SKIP answers-from-the-stale-half`, and at the old baseline of 1/1/3/0 a full revert would have scored
  EXACTLY THE BASELINE and passed. Those four PART 40 tallies are now 0 (the 5 skips were precisely these
  cells), so a rise reddens the run. Both directions were falsified with a mutant engine rather than
  asserted: one shim produced `FAIL … descriptive-hedge-substituted-for-the-result` with PART 40 the only
  red part in the suite; the other left PART 40 GREEN and reddened the skip ratchet instead.

  **Filed, measured, and NOT fixed** (SOUNDNESS.md R54/R55): `diff` has no completeness reader in any of
  the three engines that ship it, and needs `gains`' PREFIXED dual-locator shape rather than this one —
  a bare `incomplete` cannot say WHICH of its two reports was partial. rust's `receipt` has none either,
  and TSV has nowhere a caveat has been *ruled* to go; the three candidate shapes and their costs are in
  the register, to be ruled in SPEC before any engine moves.

- **⚠ PART 68 SCORED A CRASHED ENGINE ON THE PREVIOUS ENGINE'S LEFTOVER BYTES.** Its rust, java and ts
  legs ran SEQUENTIALLY into the same four verdict paths, never deleted between engines, with every
  engine's stderr discarded. An engine emitting WRONG rows was caught, because it overwrote; an engine
  that CRASHED BEFORE WRITING was scored on whatever its predecessor had left there. MEASURED 2026-08-25:
  with the java leg pointed at a nonexistent jar, the part printed `java … OK` and the suite exited 0.
  The swift leg was immune only by accident — it lays its reports under its own `sw-` spelling for
  PART 63's reason, and so happened to write its own sinks.

  This is the false all-clear the suite exists to prevent, arriving inside the suite. A green cell has to
  mean *this engine answered*; here it could mean *some engine answered, once*.

  The sinks are now per-engine and deleted before each run, an absent or empty document FAILS THE CELL
  NAMING THE ENGINE instead of falling through, and the engine's stderr is kept so the failure quotes the
  reason rather than sending the reader back to re-run the suite by hand. **Falsified in both directions**:
  with a nonexistent jar the java cell reads `FAIL — wrote no verdict document for: twin rev one nohash …
  Error: Unable to access jarfile`, the part prints `-> DIVERGE` and the run exits 1; with the jar
  restored all four engines are green again. The swift leg now goes through the SAME runner, with its
  report-dir spelling as an argument rather than a private copy of the loop — a discipline an engine can
  be added without is one the next engine WILL be added without, which is exactly how this leg came to be
  the only safe one and to be so by accident.

  **The class was swept, and PART 68 was the only instance.** Everywhere else that drives several engines
  into a sink either derives the path from the engine label, uses a per-engine scratch directory, or
  already does delete-then-assert-non-empty (`zr_probe`, `ign_probe`, `vd_gate_probe`, `lr_probe`). That
  last is the harness's house pattern; PART 68 was the one place carrying neither half of it.

- **⟨0.32⟩ THE VERDICT-ROW IDENTITY MUST NOW HAS AN ARM — PART 68 — AND THE MUST LEDGER HAD BEEN
  OVERSTATING ITS COVERAGE.** §2 ⟨0.32⟩ states TWO MUSTs in one block: a multi-report verdict must be
  computed over `hash`-keyed units, AND *"a verdict row MUST carry enough identity for a consumer to
  tell two units apart… the sort key MUST include that identity."* The ledger classified the whole block
  as `"part": "PART 63"` — and PART 63 drives EXIT CODES only; it never opens the verdict document. The
  row half was recorded as exercised by a part that structurally cannot see it, which is the shape this
  ledger exists to make unwritable, arriving inside the ledger itself.

  MEASURED 2026-08-24, the row half was live in ONE engine: `gate --report` over two reports whose
  members both declare `go` and both violate `deny Exec` gave candor-java, candor-ts and candor-swift two
  BYTE-IDENTICAL rows (candor-rust had closed it the day before). All three have since shipped `hash`
  beside `fn`. PART 68 drives four engines over four cells — TWIN (two rows, DISTINCT, each carrying a
  non-empty identity, in identity order), REV, ONE and NOHASH. `rev` re-lays the SAME two bodies under
  SWAPPED file stems, which is what separates *the sort key includes the identity* from *the discovery
  walk happened to be alphabetical*; `one` pins a single-unit row's key set EXACTLY; `nohash` requires a
  producer with no identity to OMIT the field, without which the cheapest way to pass is to synthesise
  one from the name — the §2.2 join the clause forbids, wearing the new key's clothes. The instrument was
  proven with three mutants over a PASSING document before it was believed. The ledger now names both
  parts and says why the old value was wrong.

- **PART 5's ts fixture had drifted into incompleteness, and the ⟨0.32⟩ descriptive hedge found it.** The
  same day's four-way ruling made the descriptive verbs hedge over an `excluded` class the scan never
  opened. candor-ts's fixture is scanned IN PLACE inside its own checkout, so a scan of the single file
  `Cases.ts` publishes `excluded: [{class: "not-a-parsed-source", count: 29, peeked: false}]` — 29 sibling
  files this run never opened, which is TRUE and is what the key is for. `show` and `map` then correctly
  answered with §2 Rung A's CAVEAT DOCUMENT instead of their result document, and PART 5 — which
  compares the HEALTHY shapes — died with `KeyError: 0`. (⟨0.32⟩ has since NARROWED Rung A: those two now
  answer their result AND the caveat, so the shape PART 5 refuses is `{"functions"|"modules": …,
  "incomplete": true}` rather than the caveat alone. The root is an object either way, so the fixture
  finding and both halves of the fix below are unchanged.) The fixture is now scanned from a copy under
  `$W/tsfx`, exactly as the rust and java fixtures already are, carrying a `package.json` that keeps the
  report's `package` (and every entry `hash`) byte-identical; measured, the only difference is
  `excluded: []`. And PART 5's loader now recognises the Rung A shape and FAILS with a sentence naming
  the cause, because a fixture drifting into incompleteness is a recurring event and `KeyError: 0` says
  nothing about it.

- **⟨0.32⟩ UPGRADE IN THIS ORDER — POLICY FIRST, ENGINE SECOND.** ⟨0.32⟩ is not additive, and the shape
  that flips is the commonest CI layout there is: a SCAN step that produces a report and a LATER GATE step
  that judges it. The order below is the difference between a zero-red upgrade and a pipeline that goes
  red on artifacts nobody can repair.

  1. **FIRST, while still on 0.31**, add your policy to the SCAN step — `--policy <file>`, or
     `CANDOR_POLICY` — the SAME policy the gate step already uses. This is safe on 0.31: the peek runs, the
     excluded classes come back `peeked: true`, and if anything DOES go red it is a real finding in code
     the scan was previously not asked about. Nothing about it depends on the new engine.
  2. **THEN bump the engine pin.** Nothing new goes red: the reports your scan step now produces already
     carry the evidence ⟨0.32⟩ asks for.

  **Upgrading the engine FIRST instead** makes `gate --report` exit 2 (INCOMPLETE) over any report produced
  without a policy on a tree that has tests, build scripts, `.d.ts` files or a `dist/` — because the report
  says, correctly, that the scan never opened them. That INCLUDES reports ARCHIVED BEFORE the upgrade, and
  **no consumer can repair one**: the remedy is to re-produce it with the policy, which needs the sources.

  Measured end to end on candor-ts, with the control beside it — a tree carrying a `.d.ts` and a test file,
  under `deny Exec`:

      0.31 scan WITH the policy   -> exit 0, `peeked: true`  ->  gate at ⟨0.32⟩ -> exit 0   ← the ordered path
      0.31 scan with NO policy    -> exit 0, `peeked: false` ->  gate at ⟨0.32⟩ -> exit 2   ← the control

  **Scan and gate with the SAME policy.** A report produced under one policy does not answer another: the
  peek reads a class only as far as the PRODUCER'S deny set required, and the report does not record what
  that set was, so `peeked: true` earned under `deny Net` can certify nothing about `Exec`. That hole is
  FILED, not implemented — `FILE-SET-DESIGN.md` §8 — and until it is closed the same-policy discipline is
  the only thing standing in for it.

  **candor-ts carries one extra caveat, and it reaches ONE-STEP pipelines too.** ⟨0.32⟩ widened its
  excluded census to walk what the analysis walk walks: `dist`, `build`, `out`, `coverage`, `.next` and
  dot-directories used to be skipped by the census alone, so the two halves of one report disagreed about
  which files exist. Those files now appear in `excluded` (as `not-a-parsed-source`, or
  `outside-the-tsconfig-program` when a tsconfig is in play), and the peek reads them. Measured, byte-
  identical `child_process` code under `deny Exec` in one `candor-ts <dir> --policy` invocation:
  `candor-ts@0.31.0` answered exit 0 `policy ✓`; ⟨0.32⟩ answers exit 2 naming `dist/shipped.js`. So do NOT
  read "one-step pipelines are untouched" as covering ts — a shipped `dist/` that performs a denied effect
  was invisible and now is not. That is the rung working, and it is still a new red.

- **⟨0.32⟩ CODE THE SCAN DID NOT READ MAKES THE VERDICT INCOMPLETE (§2, §3.3).** ⟨0.30⟩'s arm keys on what
  the peek FOUND, and a peek that cannot open a file finds nothing — byte-identical to finding it clean.
  Measured: an unreadable `build.rs` holding `Command::new("curl")` answered exit 0 under `deny Exec`. A
  class the scan did not read now refuses on BOTH routes with byte-equal documents. Bounded to policies
  that carry a DENY rule: `peeked: false` also means "never asked", and reading that as unread code
  refused trees nobody had put a question to. PART 62, with the never-asked control on both engine rows.

- **⟨0.32⟩ THE CARVE-OUT IS THE QUESTION BEING ASKED NOW, NEVER THE PRODUCER'S HISTORY (§2, §3.1).** The
  clause above says the rule fires only under a policy holding a deny rule; it did not say how that is
  DECIDED, and two engines decided it by asking whether the producing scan had emitted `outOfScope`. That
  spelling deletes the rule in exactly the case it exists for: `excluded` is MANDATORY from ⟨0.29⟩ while
  `outOfScope` is omitted when nothing was asked, so a no-policy report over a tree with exclusions
  carries `peeked: false` with no `outOfScope` beside it. Measured 2026-08-24 — candor-rust and candor-ts
  refused it, candor-java and candor-swift certified it, on identical evidence; candor-rust's own A/B over
  795 crate×policy pairs found 90 that went scan=2 → gate=0. Such reports now fail closed, and that is the
  rung rather than collateral: the remedy is to SCAN WITH THE POLICY, which no consumer can do for itself.
  ⟨0.32⟩ is therefore **not additive**, and reaches further than ⟨0.30⟩ did. `pure` counts as a deny rule
  (empty effect list). The fail direction of the carve-out is stated in §2 and is a real limitation: an
  excluded file can hold a forbidden EDGE, and the peek is deny-only, so refusing `forbid`/`only` policies
  would be permanent with no remedy — a disclosure obligation is written in its place, and measured as
  implemented by NO engine today. PART 62 gains the arm four-way, plus `judgedElsewhere: true` ⇒ 0, a
  non-boolean `judgedElsewhere` ⇒ 2, and `pure` over a no-policy report ⇒ 2.

- **PART 67 — THE ADVISORY VERBS REFUSE WHEREVER THE GATE DOES (§3.1 ⟨0.24⟩), four-way.** ⟨0.32⟩ shipped
  its new verdict cause into `gate --report` on all four engines and into NEITHER of the two advisory
  verbs that answer `ok` over the identical bytes: `fix-gate --strict` exited 0 printing *"no deny/pure
  boundary crossings ✓"* and `unverified --strict` exited 0 printing *"every function … PROVABLY clean ✓"*
  over reports the gate beside them refused. Fixed four-way the same day (candor-rust `9bf3f2f`,
  candor-swift `2bf8de7`, candor-java `3682835`, candor-ts `9f22581`) with **nothing asserting it** — PART
  62 pins the CAUSE and drives the gate route only. The part is named for the RELATION rather than for
  ⟨0.32⟩ because this is the third time a new verdict cause reached the gate and not these two verbs
  (⟨0.24⟩ `unanalyzed`, ⟨0.30⟩ `outOfScope`, ⟨0.32⟩ `excluded[].peeked`), so the fourth needs a fixture
  here and not a rewrite. One tree per engine scanned TWICE — once with `deny Exec`, once with no policy —
  so the only difference between the two reports is whether the peek was ever put the question; the
  excluded file is CLEAN in both, which is what makes the refusal attributable to the document rather than
  to content. Six cells per engine: 2/2/2 over the unread report, 0/0/0 over the peeked control, the
  control being half the row because an engine that refuses everything scores a perfect 2/2/2. Falsified
  against binaries built from the commits BEFORE the fixes (rust `9bf3f2f^` reddens at 2/0/0, java
  `3682835^` at 0/0/0), and guarded by an instrument check that FAILS a fixture carrying any `Unknown` —
  `unverified --strict` has its own exit 1 there, which is neither 2 nor 0 and reads as the verb handling
  the case. Two §3.1 statements move from `pre-ledger` to part-named in the MUST ledger. Two further
  routes are pinned in the same part: candor-java's `--parallel`, which cannot gate and is therefore
  asserted on the DOCUMENT it writes (`excluded` byte-equal to a standalone scan, all three verbs
  refusing over it), and candor-ts's MCP `candor_gate`, measured rather than assumed to inherit from the
  reader it shares with the CLI.

- **PART 54's absent-key arm was measuring the opposite of ⟨0.32⟩, and the FIXTURE was what was wrong.**
  It scanned PART 48's DIRTY tree with no policy and asserted the gate stays green — `policy ✓` over the
  rung's own central case — so it went red the day the four engines closed their route split. The two
  rules never collided: an ABSENT `outOfScope` means *never asked* and triggers nothing (⟨0.30⟩), while a
  PRESENT `excluded[].peeked == false` triggers ⟨0.32⟩, and that clause needs an ENTRY. The arm now runs
  on the CONTROL trees, whose `excluded` is `[]`, with an INSTRUMENT CHECK asserting that before it gates —
  without one the arm silently degrades back into measuring ⟨0.32⟩. The original error was mapping ⟨0.26⟩
  *cannot answer* onto exit 0: in this family cannot-answer at VERDICT level is exit 2 INCOMPLETE.

- **FILED — the CROSS-POLICY hole (`FILE-SET-DESIGN.md` §8).** `peeked: true` is true only relative to the
  deny set the PRODUCER held, and the report does not record what that was. Scan with `deny Net` (the peek
  reads the class in full, `peeked: true`), gate with `deny Exec`: the `Exec` in the excluded file was seen
  and discarded as outside the producer's question, and the gate exits 0 where `scan --policy 'deny Exec'`
  exits 2. Undetectable from the document, and it survives every ⟨0.32⟩ control because the class really
  was read. Proposed fix: record the scan policy's deny set, or a digest, in the report.

- **⟨0.32⟩ A CONSUMER JOINS REPORTS BY `hash`, NEVER BY BARE `fn` (§2.2).** Measured in every engine:
  `gate --report` over one member refused a scoped rule at exit 2, and the SAME member gated beside an
  unrelated sibling exited 0 with `policy ✓` — adding a report, strictly more information, turned a red
  verdict green. Union is safe for EFFECTS and not for REASON CLASSES: a reason set is what makes an
  `Unknown` answerable, so borrowing one from an unrelated same-named function converts a refusal into an
  answer. The call graph needs the same treatment — `calls` names callees by bare `fn` — and an ambiguous
  callee CONTRIBUTES `Unknown[dispatch]` rather than vanishing. PART 63, four-way.

- **⟨0.32⟩ A PEEK MAY DERIVE THE FILE SET IT READS, AND CERTIFY FROM IT (§2).** An engine that reads
  compiled artifacts cannot otherwise answer for a tree that has not been built. Compiling a source and
  analysing the RESULT satisfies ⟨0.29⟩'s one-judgement-path MUST exactly — one classifier, resolved
  receivers. Two conditions: every file's derivation succeeds (a compiler that recovers from an error
  emits a body that throws where the untranslatable code was, so effects VANISH), and the derivation runs
  no code from the tree (this is the tool that certifies `deny Exec`; a scan must not become an
  execution). candor-java implements it; the source-reading engines have no case. PART 65.

- **⟨0.32⟩ `Exec` REACHES THE SUBPROCESS CAPABILITY, NOT ONLY THE LAUNCH (§1).** An invocation object
  carries its own payload — program, argv, environment — and travels fully armed, so constructing or
  configuring one is `Exec` exactly as spawning it is. Measured on candor-java, the family's lone
  launch-verb allowlist: `ProcessBuilder arm(String[] argv) { return new ProcessBuilder(argv); }` reported
  `inferred: []` and passed `deny Exec` at exit 0 — a fully-armed invocation assembled from caller-supplied
  argv, certified clean, because splitting build from launch across two functions left nobody holding the
  effect. Stated as a DENYLIST (read-backs like `get_program`/`command()` carved out) with an explicit MUST
  NOT on the allowlist form, which under-reports every verb it forgets. Bounded to invocation objects:
  option-builders for other effects (`OpenOptions`, request builders) stay pure, their resource arriving at
  a terminal verb charged at its own call site. PART 66, whose `readBack` and `lookalike` over-charge
  controls are what an engine that answers `Exec` for everything fails. Corpus A/B on candor-java: 933 JVM
  jars, 0 verdict flips and 0 functions losing an effect.

- **⟨0.32⟩ …AND THE CLASSPATH IT DERIVED AGAINST IS PART OF THE CLAIM (§2).** A compile that succeeds
  against the wrong version of a dependency emits bytecode the project does not build: a `static final`
  guard folds to `false`, javac deletes the branch as unreachable, and the effect disappears. So the
  classpath MUST come from the scanned root or an operator declaration — never from the tree's own build
  metadata, which would let the artifact being scanned choose the inputs that shape its own derived
  bytecode. candor-java adds `--peek-classpath`, the `peek-classpath` config key, and
  `CANDOR_PEEK_CLASSPATH`; a declared jar registering an annotation processor withdraws certification
  exactly as one under the root does. PART 65's dependency-outside-the-root row.

- **⟨0.32⟩ A CLASS OLDER THAN ITS SOURCE IS DISCLOSED (candor-java).** Compiled is not the same question
  as current. Measured as a live false all-clear: edit a file to add `Runtime.exec`, do not rebuild, scan
  under `deny Exec` — exit 0, certified, because every disclosure in the report was true of the bytes
  that were read and only which bytes those were was wrong. Rides `excluded` as `source-newer-than-class`.
  Claimed against the NEWEST copy of a class, never the last one read: a real project's exploded war held
  a second copy of nearly every class 14 months older, and last-one-wins reported 374 current sources
  stale against stale copies of their own classes.

- **⟨0.32⟩ A REFUSAL IS RECORDED BESIDE THE REPORTS IT WOULD HAVE WRITTEN (§3.3.1).** §3.3.1's arming
  rules cover a prefix the operator NAMED. A run given no `--out` still writes reports — to its default
  prefix — and a refusal leaves whatever the last successful run put there, readable as current. Measured
  in all four engines: scan a tree green, change it so it now violates, refuse for any reason, and
  `gate --report <tree>` answers `policy ✓` at exit 0 off the previous run's bytes. The only thing
  separating that from the covered case is whether a flag was typed.

  **Arming the default prefix is NOT the answer, and the clause records why, because it was tried:** a
  run that died in argv parsing replaced a COMMITTED report in candor-rust's own repository. Naming a
  prefix is a declaration; a default is a convention, and a convention does not license destroying a file
  the operator may be keeping. So the refusal is written BESIDE the reports, at `<prefix>.refused.json`,
  and overwrites nothing. `refused` joins §2.2's family-wide reserved segment set.

  Because it destroys nothing it can be written at the EARLIEST moment the prefix is known — during argv
  parsing — which is what lets it cover the argv-death case arming structurally cannot. The earliest safe
  moment and the earliest useful moment turn out to be the same moment.

  The marker carries its own `prefix` so §3.3.1's DIRECT-FILE locator is answerable: that form accepts any
  `.json` name whatever its dot-segments, so a consumer handed one file cannot recover the prefix from the
  filename and reads it out of the marker instead.

  **Failure direction, deliberately:** a lost marker fails OPEN (the status quo, so this is never worse
  than what it replaces); a stale one fails CLOSED, which is correct — the reports under it are from a
  scan whose successor refused. Pinned by PART 60, whose two controls are a completing run CLEARING the
  marker (or every later gate refuses off it for ever — the permanent-red mirror) and a normal answer when
  none is present (or "refuse always" passes every other row while deleting the tool).

  **Complete across the family.** candor-rust, candor-ts and candor-swift ship it and assert. **candor-java
  is N/A, measured rather than assumed:** a bare `candor-java <target>` persists NO report, so it has no
  default prefix for a refusal to leave stale, and its `--json <file>` sink is a NAMED one already armed
  under §3.3.1 — verified by seeding a green report there and watching a refusal replace it. A marker
  would record a hazard that engine does not have. Both obsolete skip-baseline entries were removed with
  it: a skip that is really an N/A erodes the ratchet exactly as a stale one does.

- **A RUNNER-ABSENCE SKIP IS NOT A RUNG, and PARTs 63 and 68 spelled it as though it were.** Both new
  ⟨0.32⟩ rows printed `swift SKIP — engine absent`, which is the ratchet's COUNTED form. The ubuntu leg
  carries three engines by design (no swift toolchain on those runners), so it reddened at
  `line:swift SKIP — engine absent` skipped 2, baseline 0 — while the macOS leg scored all four cells of
  both parts OK. The coverage had not dropped; the wording had.

  **Re-baselining would have been the wrong fix, and this is the argument.** There is one baseline file
  and two legs, so a count of swift's absence is true on one and false on the other — a runner condition
  filed where rungs live, and one that would need raising again for every future part that gains a swift
  row. That is the number "drifting upward one unremarkable commit at a time" `skip_ratchet.py`'s own
  header warns about. **Nothing is lost by declining to count it, because absence is already ratcheted
  harder:** `[6]`/`[6c]` FAIL outright when an engine is PRESENT but produced no report (the
  `TS_PRESENT`-vs-`TS_OK` split), and `CONFORMANCE_REQUIRE_ALL=1` on the macOS leg FAILs when one is
  absent at all. A row's `if [ -n "$SW_OK" ]` can only fall through when the engine is structurally absent
  on this leg, or the suite is already red.

  So the four rows move to the PARENTHESISED `-> SKIP     (…)` form the other fifteen absence sites (PART
  47's rows, PART 67's) have always used, which the LOOSE pattern does not match — still loud in the log,
  no longer a rung. The distinction is now written where the next person classifying a skip will be:
  reference-led ("this engine has not shipped the rung") takes the em dash and is COUNTED; runner-absence
  takes the parentheses and is not. **The ratchet keeps its teeth** — measured on a run with `CANDOR_TS`
  and `CANDOR_SWIFT` pointed at nonexistent paths: both rows print, the suite's own "not present on this
  runner" declaration is picked up, and the counted set is EMPTY where it was 2, while a reference-led
  `candor-scan (a) SKIP — …` line still keys and counts unchanged.

- **The drift gate held AGENTS.md against SPEC.md and never read SPEC.md back, so three of this file's own
  envelope examples still said `"spec": "0.31"` under a `**Version 0.32**` header.** Those fences are what
  an implementer copies, so a stale one teaches the wrong contract from the document that defines it — and
  this is the second bump it has happened on: at 0.30 candor-java's release preflight caught
  `"spec":    "0.30"` by hand, whose alignment padding had also defeated a sweep for the exact string.

  `check_agents_drift.py` now sweeps SPEC.md's own `"spec": "X.Y"` fences against the floor SPEC.md
  declares. Deliberately JSON-only, unlike the sweep the engines now run over their READMEs: this file is
  dense with prose rung references that are true about the past and must not move, so a prose sweep here
  would be a false-positive machine — while `"spec": "X.Y"` inside a fence is always a CURRENT-contract
  claim. Historical illustrations keep the `(measured at spec X.Y, informative)` marker §3.3.1 already
  uses, exempted per LINE because that is where this document puts it. A CONTROL exercises both halves on
  a fixture first: the check reads clean when the document is clean, when the pattern has stopped
  matching, and when the exemption swallows everything, and those three must not be one output.

## [0.31.0] — 2026-08-20

- **PART 59 — what a refusal owes its reader.** PART 56 scores the exit code and the absence of a NEW
  report. A four-lens release panel found three things it therefore could not see, all in the staged 0.31
  build: a single-FILE target of the wrong kind (PART 56 only ever passes a directory) certified green on
  one engine; the refusal document's `reason` misdescribed the cause on three of four (one said the gate
  config failed to load when the config loaded fine; two left the arming stub, which says the run
  crashed); and a PREVIOUS run's report survived the refusal at a named prefix, so `gate --report`
  certified it — PART 56 checks that no new report appears and cannot see an old one surviving, which was
  the whole defect.

  Row D is the control and is not decoration: every other row is satisfied by an engine that refuses
  EVERYTHING, so D scans a real target of each engine's kind and requires a real report with no
  placeholder. Calibrated against both original defects.

  The first version of row C seeded ts and swift at their DEFAULT prefix while seeding rust at a named
  one, and duly reported a divergence that does not exist — rust leaves a stale report at its default
  prefix too. §3.3.1 says "every prefix NAMED", so the row now compares like with like and the
  default-prefix question is filed rather than asserted here. A part that asserts behaviour the spec does
  not require is how a suite starts inventing the contract.

- The §2 envelope example declared `spec: "0.30"`. It is written with alignment padding, so the floor
  bump's sweep — which matched a single space — walked past it; `release-preflight [2]`'s separate
  bare-literal check is what caught it.

- **PART 57 arm E — the ⟨0.30⟩ peek must not feed `netPartners`.** The peek re-enters the scanner over
  the files a scan EXCLUDED, and `netPartners` is not policy-derived: it comes from the participating
  hosts plus the discovered config, and the peek walks the same target. An engine accumulating into
  shared state therefore files the excluded set's partner into the verdict, where the report cannot carry
  it and `gate --report` can only answer null. Measured in candor-rust the day the key landed.

  Two traps this row walked into, both of which produced a green that meant nothing. It first used the
  part's `deny Net[unknown-host]`, but once a partner is declared the host classifies as known-partner,
  so nothing matched and the policy-bounded peek stayed silent — arm E uses a bare `deny Net` and carries
  its own setup control. It then checked the REPORT, and had no teeth at all: rebuilding candor-scan with
  the guard deleted left the part green, because the report was always the correct half. The defect is in
  the verdict, and both documents are compared now.

- **PART 58 — an `outOfScope` entry names the file its function is in.** Found in candor-ts: two excluded
  files sharing a basename, and one function disclosed at the other's path. It gets its own part
  precisely because it is not a silent under-report — both functions were disclosed with the right
  effects and class, and every existing assertion passed. What was wrong was a locator, and a disclosure
  nobody can act on is worth little more than none. The control row requires both functions still
  present, since naming each function's own file is trivially satisfied by disclosing nothing. ts, rust
  and swift assert; java is excluded with a reason (its locator is the jar, so it has no per-source-file
  locator to get wrong).

- **PART 57 asserts ALL FOUR ENGINES — the ⟨0.31⟩ `netPartners` rung is complete.** Every engine names
  the config and the participating host, agrees byte-for-byte across `scan --policy` and `gate --report`,
  omits the key when no partner was declared, and omits it when a declared partner never matched. No
  engine skips this row.

- **PART 57 now asserts candor-java too**, and **conformance no longer runs on doc-only pushes.** Three
  CHANGELOG-only commits each bought a full 15-minute four-way suite tonight; the workflow now ignores
  root `CHANGELOG.md`/`README.md`/`BACKLOG.md` — the same licensed set `release-preflight [11]` already
  reasons about. Deliberately narrow: `conformance/README.md` is NOT ignored, because the ledger resolves
  `part` references out of files under `conformance/` and a README edit there can break it. An omission
  costs a run, never a false green.

- **PART 57 now asserts candor-rust too.** Two engines score all four properties; java and swift still
  SKIP with a stated reason and stay ratchet-counted, so the rung cannot un-ship unnoticed.

- **⟨0.31⟩ — `netPartners`: the ambient config that moved a verdict is named in it (§2 + §3.1).**
  MEASURED in candor-ts and candor-rust alike: under `deny Net[unknown-host]` a call to `partner.example`
  exits 1; adding `net-partner partner.example` to an ambient `.candor/config` exits 0 with `ok: true`,
  and no key names the file, its path, or the host. §3.1 already refuses that for `unknown-alias` —
  *"an operator reading a verdict changed by an ambient definition needs to see what the definition was"*
  — and its reasoning reaches this key while its MUST did not.

  The report envelope carries `netPartners: { config, hosts }`; the verdict carries the list of those
  records on both routes. **`hosts` is what PARTICIPATED, not what was declared** — a config listing
  twenty partners of which one matched discloses the one, because a list of everything declared buries
  the line that moved the verdict.

  **It is recorded in the REPORT, which is what makes it emittable at all.** `net-partner` anchors at the
  target and `gate --report` has no target; re-classifying through the consumer's own config would make a
  verdict depend on the reader's working directory. A verdict-only disclosure is therefore computable on
  one route and not the other — this was implemented that way once and reverted, the producing engine's
  own suite reporting *"pure: NOT byte-equal"*. The producer records it, both routes copy it, and they
  agree by construction.

  Separate key from `policyVocabulary` because the two ANCHOR differently (policy directory vs target),
  so one `config` field naming one source would be false about one of them. And the match must be the
  classifier's own: the first attempt normalised differently and `partner.example:443` never equalled the
  declared `partner.example`, so the disclosure was silently empty on every real run while the verdicts it
  reported on had flipped.

  **PART 57** asserts four properties on candor-ts — named, byte-equal across routes, additive, and a
  declared-but-unmatched partner disclosed nowhere. rust, java and swift SKIP with a stated reason and are
  ratchet-counted; the ports are open work.

- **⟨0.31⟩ — AN UNEVALUABLE TARGET IS THE FOURTH EXIT-2 CAUSE (§3.3).** A target that exists but holds no
  file the engine can read is a REFUSAL, not a clean scan: *"I found nothing to open"* and *"I opened
  everything and judged it"* are different claims, and exit 0 makes the second. ts, swift and java already
  refused this shape **without it being enumerated** — by ⟨0.24⟩'s own doctrine that is an engine minting
  a cause — and candor-rust answered `policy ✓`. The clause writes the cause down and brings rust into
  line.

  **It supersedes ⟨0.24⟩'s judged-nothing ruling for the SCAN ROUTE'S OWN TARGET, and only there.** A
  judged-nothing report presented to a verb, or chained as a dependency, stays verdict-preserving — the
  facade table in §2 depends on it. The distinction is **the walk versus the report**, and it is
  load-bearing: a produced `count: 0` report travels into the gate route, so a refusal keyed on it splits
  the verb (measured — an attempt keyed that way answered `scan --policy` 2 against `gate --report` 0 on
  its first run); a refusal keyed on the walk never reaches that route, because §3.1's byte-equality is
  quantified over *any report a scan produced* and this refusal produces none.

  Three boundaries in the clause, each of which a naive form gets wrong: a project of the engine's kind
  yielding ZERO UNITS is still an ANSWER (⟨0.24⟩'s premise, unchanged); the cause is PER-INVOCATION, never
  per-member (a scaffolded workspace member must not redden a real workspace, and swift `binary` targets,
  maven aggregators and ts solution roots all carry zero sources legitimately); and the ⟨0.30⟩ peek runs
  FIRST, so an effect in an unread file is named rather than silenced by the target being unreadable.

  Five locations moved together — the cause, the ⟨0.28⟩ carve-out it reconciles with, §3.1's lean on the
  enumeration, and the exit-2 **count**, whose own footnote records that a stale count has shipped three
  times. Seven statements classified in the MUST ledger; one recorded as unenforced with its reason (no
  row asserts remedy TEXT, and pinning prose is something this suite deliberately does not do).

- **PART 56 pins REFUSE-BEFORE-ENVELOPE.** §3.1's byte-equality is quantified over "any report a scan
  produced", so an engine that refuses at exit 2 must leave no report — once one exists, the scan route
  owns the gate route's answer over it. Measured the same day: the first ts/swift fix exited 2 from an arm
  after the verdict was written, leaving `--gate-json` saying `ok: true` and a report `gate --report`
  answered 0 over. Both directions are asserted (a dirty run MUST leave a report for its findings; a
  refusing run MUST NOT), and the row was calibrated by inverting the assertion.

- **PART 56 — a target with no analyzable source still reads what it excluded.** Found by corpus-testing
  the PUBLISHED 0.30.0 hours after it shipped: a declarations-only package whose `.js` performs the denied
  effect answered `no TypeScript sources`, exit 2, and named nothing, where candor-rust over the analogous
  shape named the function. Fixed in candor-ts and candor-swift; this pins it. Two shapes, and the second
  is the point: the IDENTICAL tree with a CLEAN excluded sibling must still exit 2 and name nothing —
  without it, a fix that merely stops refusing passes shape A while answering `policy ✓` at exit 0 over a
  tree with zero analyzed files, which is exactly what candor-ts's first attempt did. That control then
  caught the same false green in **candor-rust**, which is NAMED as a divergence every run and filed in
  candor/BACKLOG.md rather than asserted away. java is excluded with a reason: its class-directory/jar
  target has nothing beside it to peek.
  **Correction, same day:** the row first called candor-rust's exit 0 here a filed defect. It is the
  spec's ruling — §⟨0.24⟩ makes `analyzed.count == 0` a DISCLOSURE obligation, "verdict-preserving, exit
  unchanged", and candor-rust's own `gate-equivalence` row `judged-nothing` pins it. A fix was written
  before the contract was read and broke §3.1 route equality on its first run (scan 2 vs gate 0), which is
  how the ruling surfaced. The row now names the ts/swift-vs-rust split as an open SPEC question — which
  convention the family wants — rather than as an engine defect.

- **The self-differential generators run their four engines concurrently.** Profiling the suite by its
  silent gaps (rather than by part headers — see below) put 168s of 386s in five generators, each
  driving four engines in sequence over workspaces that share nothing. PART 55's matrix, P3
  trust-monotonicity and P2 chain-idempotence now run theirs in a thread pool: **386s → 351s** locally,
  output byte-identical, and both probed generators still fail under their own injected fault, which is
  the only thing that makes a faster gate worth having.
- **A faster version of this was written and thrown away, correctly.** Launching all five generators from
  the top of run.sh gave 234s — and 20 `DECLARED COVERAGE` violations, because a part's slice must name
  the engines it declares and hoisting the invocations out left five parts claiming four engines they no
  longer mentioned. The regex could have been satisfied with a comment naming `$JAR`; that is gaming an
  honesty check. The audit is worth more than the 117 seconds.
- **Two profiling methods were wrong before one was right.** Timestamping between `[NN]` headers
  attributes a part's cost to its neighbour (work happens before the header prints), and `part.sh`
  slices do not reproduce it — `part.sh 32` runs in 2s where the profile claimed 154s. Measuring the
  raw silent gaps and naming the section each precedes is what actually located the cost.

## [0.30.0] — 2026-08-19

- **PART 55 — the generated policy matrix.** The peek must reach the GATE's own judgement over identical
  code, placed in scope and out. No cell carries a hand-written expected value, so a policy form nobody
  anticipated is covered the moment it is added. It found three defects on its first run (swift and java
  dropping a rule's class filters; java's peek running with an empty config, so `net-partner` was never
  seen) and then the ts/swift corrupt-key hole in the advisory verbs.
- **§2 now states what conformance pins**: `pure` denies every effect except `Unknown`; a rule's class
  filters and scope narrow the peek exactly as they narrow the gate, matched against a project-relative
  qualifier rather than an absolute path; and the advisory verbs follow the gate's incompleteness. §3.3(c)
  states the no-`violations`-key property explicitly, as (a) already did for its own shape.
- **PART 55 declared four engines and had never asked the fourth.** run.sh passed the generator
  `$(dirname "$SW_BIN")/../..` — correct under the shell's LOGICAL `..`, wrong under the kernel's
  physical one, because SwiftPM makes `.build/debug` a symlink to `.build/<triple>/debug`. It resolved
  to `.build`, the generator probed one level too deep, found nothing and printed `swift -> SKIP (engine
  not built)` on every run, including full runs on a machine with swift built and passing. Swift's peek
  is a hand-mirror of the gate rather than shared code, so it is the engine the matrix most exists to
  hold. Fixed to pass the package directory, and the generator now **exits** when `CANDOR_SWIFT` names an
  engine whose binary is absent, rather than dropping the column — run.sh's own SW_PRESENT/SW_OK note
  makes that distinction and this file did not honour it. Now 40 cells over 4 engines, 0 disagreements.
- **A new shape and a vacuity ledger.** `deny Net Unknown[unresolved]` pins the reason-scoped-Unknown
  form, unpinned until now and most consequential in the two engines whose peek is a hand-mirror. And
  the matrix now reports how many shapes are **load-bearing** (6/10) and names the inert ones: a cell
  whose GATE answers 0 is satisfied by a peek that also answers 0, including a peek that does nothing,
  so a cell count alone overstates what the matrix knows. The four inert shapes are inert by design;
  the point is that a shape going inert by ACCIDENT can no longer read as coverage.

- **PART 55 answers under its own fault, and the probe registry now enumerates from disk.**
  `gen_policy_matrix.py` grew a fault hook, so `probe_check.py` can force its peek verdict to 0 and
  watch the matrix go red — a generated matrix that cannot be seen to fail is a green with no evidence
  behind it. `probe_check.py` also lists `gen_*.py` from the directory instead of from its own two
  tables, which immediately surfaced two generators filed in neither; both now carry a stated reason.
  Every workflow here declares `timeout-minutes` (release-preflight [7b]).
- FILE-SET-DESIGN.md opens with the ⟨0.30⟩ reversal — it described the ⟨0.29⟩ design in present tense
  under a "not yet built" header, and SPEC.md sends readers to it. README.md's engine table claimed spec
  0.8. AGENTS.md gains the peek.

- **Spec floor 0.30.** The declaration this build emits as `candor.spec` moves with the family; see
  candor-spec's changelog for the rung.

### ⟨0.30⟩ — a non-empty `outOfScope` makes the verdict INCOMPLETE (exit 2)

The **first non-additive rung**: no field is added or removed, but a tree that passed under ⟨0.29⟩ can
exit 2 under ⟨0.30⟩, so upgrading is a decision rather than a drop-in. §2's peek block is unchanged in
shape and in emission rule; what changes is what a gate DOES with it.

⟨0.29⟩ required that an out-of-scope finding MUST NOT move the verdict, on the assumption that the peek
surfaces uncertainty. Measured on published 0.29.1 it resolves a CONCRETE denied effect and names the
function — `axios` 37 functions `performs Net` at exit 0 with `policy ✓`, plus `node-fetch` 15, `ky` 9,
`execa` 9, `zx` 3, `ofetch` 1. The reversal is that measurement, not a preference.

Exit 2 rather than exit 1: the findings are never `violations` and never `functions`, because the gate
did not judge those units. §3.3 gains **(c) an INCOMPLETE SCOPE** as a third exit-2 cause — neither a
broken gate CONFIG nor an unreadable file, but files that were readable and deliberately not opened —
and §3.1's clause that leaned on there being exactly two is updated with it.

Bounded by the ⟨0.29⟩ rule that `outOfScope` carries only effects the policy DENIES: across 27 real
packages the rung flips 6 and leaves 14 green. Present-and-empty stays exit 0; an ABSENT key is ⟨0.26⟩
*cannot answer* and does not trigger, so pre-⟨0.30⟩ and no-policy reports are unaffected.

Conformance: **PART 48**'s verdict arm amended (the exit-code half reverses; the membership half stands,
and a new arm asserts the finding is never reported as a violation), **PART 53**'s controls now assert
the split (a peek that finds the denied effect answers 2, an asked-and-clear peek answers 0), and
**PART 54** is new — both routes reach the same exit with byte-equal verdict documents, a corrupt key
fails closed in both positions, `pure` answers 2, and `unverified --strict` follows the gate.

### Backfilled — the changelog was missing two rungs

§8 jumped from 0.30 to 0.27 while the header promised it "lists every rung's contents", so the ⟨0.29⟩
rule this release reverses had no entry to reverse. **0.28** (the REPORT-sink arming: the report sink is
armed on exit-2 exactly as the verdict sink is, so a fail-closed manifest-carrying empty replaces the
previous run's report; plus §6.2's `ignored` disclosure for policy lines the parse dropped) and **0.29**
(the FILE SET: `excluded`/`outOfScope`/`peeked`, the per-function `incomplete` surface, and the rule
that a class is `peeked` only if every file of it was read) are now recorded.

## [0.29.1] — 2026-08-18

- **The generative differential asks about `argv`.** It did not, and that absence is why the four engines
  answered one question two ways without a green run ever noticing: candor-rust charged
  `std::env::args()` as `Env` from the start, while candor-ts's `process.argv`, candor-swift's
  `CommandLine.arguments` and candor-java's `ProcessHandle.Info.arguments()` all read PURE until a
  cross-engine parity sweep asked directly. §1 already decides it — `Env` is "reading environment
  variables / **the process environment**", and argv is process-startup state delivered by the same
  `exec` as envp, which is how a secret reaches a program as `--token=…`. So the engines were moved to
  §1's existing wording; **SPEC.md is unchanged, and this stays a within-spec patch.** The new case
  generates four shapes per engine, and is calibrated: removing ts's arm prints `(pure)!D` for ts on all
  four while the others say `Env`.

## [0.29.0] — 2026-08-17

- **§3.3.1's sink-arming transcript is marked `informative`.** The `spec 0.28` inside it is a
  MEASURED capture, not a template: rewriting it at each floor bump would falsify the record of what
  was observed. The marker is `release-preflight [2]`'s own, so the string can stay honest and the
  bump-miss detector stays sharp.

- **⟨0.29⟩ PART 51 gained `twoLit`: both path positions literal, both published.** The row shipped with
  three functions and could not see the case where a two-path op's positions are BOTH literal —
  candor-rust and candor-ts published position 0, observed that every position was a literal, and
  therefore called the surface COMPLETE, so `allow Fs /tmp/lit` certified a copy into `/tmp/dst` at exit
  0. A false all-clear assembled from two correct-looking halves: the right completeness verdict computed
  over more positions than the surface lists. Found by generating a case per `fs` export in each engine
  and diffing the four — which is exactly what a hand-written row cannot do, and what the row itself was
  written from.
- **⟨0.29⟩ two conformance instruments that could not fail, and a verdict line that ran its own words.**
  PART 47 asserted `unverified:fix-gate --strict` == 2:2 over a `forbid` policy with nothing showing those
  verbs ever exit otherwise — an engine refusing UNCONDITIONALLY satisfied it while answering nothing, and
  2 is the CAUTIOUS value, so the failure would have looked like rigour. The same verbs now also run over
  the answerable deny-only policy: 0:0, four-way. `only_check.py`'s report-route arm grepped `AS-EFF-009`
  — `forbid`'s code — for a form that emits `AS-EFF-011`, i.e. it was aimed one identifier to the left of
  the leak it exists to catch. And the three summary fragments added for PARTs 51–53 carried unescaped
  backticks inside a double-quoted `echo`, so bash ran `Fs`, `peeked` and `ok` as commands and the words
  vanished from the line the suite prints as its verdict.

- **⟨0.29⟩ §2 a literal surface is read from the LOCATOR POSITION.** §4 already stated it for the `Exec`
  head — argv[0] is the program, and `spawn(tool, "curl")` with a dynamic head must not refine — and the
  same rule was never written for the other three surfaces. MEASURED: `write(userPath, "/tmp/lit")`
  published `paths: ["/tmp/lit"]`, the BYTES, so `allow Fs /tmp/lit` certified a write to a
  runtime-controlled destination at exit 0 in two engines while the other two failed closed. Where an
  operation takes several locator positions the surface is complete only when EVERY one is a literal.
  Conformance PART 51, over-charge control included: a fully-literal write must still certify, or the
  rule is satisfied by giving up the surface.
- **⟨0.29⟩ §2 `peeked: true` means every file of the class was READ.** The rung made the flag an outcome
  and stopped one level short: the peek runs the engine's ordinary path, so it writes its own ⟨0.21⟩
  `unanalyzed` manifest, and every engine discarded it — an excluded file that failed to parse inside the
  peek published `peeked: true` beside `outOfScope: []`. A producer publishing a claim it holds the
  disproof of. Withdrawn PER CLASS; an unattributable unread file withdraws all. Conformance PART 52.
- **⟨0.29⟩ §2's refused-policy clause had one implementation.** "Over a policy the engine REFUSES, the
  key is ABSENT" shipped WITH the rung; three of four engines published `outOfScope` at exit 2 anyway.
  A MUST can exist in the spec and in one engine. Conformance PART 53 — and the §2 statement's MUST-ledger
  entry now names PART 48 + PART 53, because PART 48 owned the clause and could not see this half of it.
- **⟨0.29⟩ §6 `AS-EFF-011` — `only` gets its own code.** It charged `AS-EFF-009` for one commit, on the
  reasoning that the code already means "calls into a layer a declared dependency rule forbids" and an
  `only` is one — true about the ENGINE, wrong about the CONSUMER. A code is what a CI suppression, a
  dashboard link and an alert filter key on, and the two forms are opposite constructs with opposite
  remedies. **Decisive argument: timing.** An existing `AS-EFF-009` suppression means "I accepted a
  `forbid` crossing"; shipping `only` under it would make that suppression silently begin muting a class
  its author never accepted — a fail-open change to an operator's config, made by us and invisible to
  them. Free before release, breaking after. PART 49 asserts both halves (011 present, 009 absent).
- **⟨0.29⟩ §3.1's answerability list was a CLOSED ENUMERATION and `only` had nowhere to join it.** It
  read "exactly three refusals", so §6.2's `only` clause pointed back at a list that did not contain the
  rule it was pointing about. *A rule stated as a COUNT of its members stops being true the next time the
  domain grows* — the count is gone and the members carry it. `only` is now the fourth entry, with the
  stricter reason it is unanswerable for.
- **⟨0.29⟩ PART 4 could not see a new rule kind.** The four-way grammar differential — the part that
  exists to catch exactly the divergence where two engines omitted `only` from `parsepolicy` — read three
  keys and stopped, over a battery containing no `only` line. Both fixed: the battery gained well-formed
  AND malformed `only` lines (every engine must DROP the same lines, not just accept the same ones), and
  the comparison a fourth key, read with `.get` so an engine that has not shipped the kind DIVERGES rather
  than crashing the differential.
- **⟨0.29⟩ §2.1 `resolves` names `incomplete`.** The rung that closed an overloaded absence INSIDE a
  report (`paths` absent = "no path" or "a path I could not see") left an overloaded absence ABOUT the
  report: a consumer could not tell a producer that computes undetermined locators and found none from one
  that never computes them. That is what `resolves` is for, and the `fs` clause beside it makes the same
  argument. All four declare it; PART 50 asserts the declaration before reading any absence as meaningful.
- **⟨0.29⟩ §2 `incomplete` — STATED OVER THE CONDITION, not over one use of it**, and pinned four-way by
  **PART 50**. The field was named only in §2's chained-JOIN clause ("a join that carries the effect and
  drops `incomplete` lets a benign literal in the consumer certify what the dependency declared
  uncertifiable"), and nothing said a PRODUCER had to emit it — so candor-ts and candor-java computed it
  internally and published nothing, the join had nothing to carry, and the rule about the join was vacuous
  for half the family. **A rule written over the instance that was measured rather than over the condition
  that produces it, for the fourth time in this document.**
  The harm is a FALSE ALL-CLEAR on a configured gate, and only across a boundary: a dependency whose `Fs`
  path is a runtime value published nothing to say so, and a consumer that ALSO wrote one allowed literal
  joined `paths: ["/tmp/lit"]` with no marker — `allow Fs /tmp/lit` answered `policy ✓` in two engines and
  AS-EFF-008 in the other two, on identical code. `Net` was already covered because ⟨0.20⟩ gave it a wire
  form of its own (`netClass ∋ unknown-host`); `Fs`/`Exec`/`Db` had none. **PART 50's row is the CHAINED
  VERDICT, not the field**: in one package every engine already fails closed (AS-EFF-008 keys on "no
  visible literal"), so a single-crate row passes on all four and proves nothing. Falsified two ways —
  not emitting the field, and emitting it without joining, fail with different diagnoses.
- **⟨0.29⟩ §6.2 `only <A> -> <B> [<C> …]` — the PERMISSION form** (AS-EFF-009), pinned four-way by
  **PART 49**. `forbid` can state a prohibition but not a permission, and it **fails OPEN**: the
  dependency you forgot to prohibit is silently permitted, so "this package is a leaf" could only be
  spelled as an enumeration that does not cover a package added tomorrow and says nothing about it — the
  allowlist hazard this document refuses throughout the ANALYSIS, sitting in the POLICY LANGUAGE. `only`
  fails SAFE. Found by pointing candor's own architecture gate at candor, where the natural
  `forbid <pkg>.model -> <pkg>` self-fires because a scope matches a contiguous run of segments.
  Three rulings an implementation MUST follow, each of which could plausibly have gone the other way:
  `A -> A` is IMPLICIT; the walk STOPS at a permitted scope and DESCENDS THROUGH `from`; and zero-match is
  measured on `from` ALONE, unlike `forbid`'s either-endpoint count. `only` is unanswerable from a report
  for a stricter reason than `forbid` — it asks whether EVERYTHING reached is on a list, so an omitted
  crossing turns a green into a claim of COMPLETENESS — and a route that discloses it MUST also REMOVE it.
  **That last sentence is in the clause because two engines failed it.** candor-rust and candor-java each
  disclosed the rule and evaluated it anyway, printing a violation beside their own statement that the
  rule could not be evaluated; both had the removal site fifty lines from where the kind was added.
  **PART 49 found the rust one, but only after the row was falsified and rebuilt twice**: with an
  `only`-only policy every engine refuses before evaluating anything, and over a wholly pure fixture the
  report carries no graph to walk — so the row needed an answerable rule beside it AND an effect in the
  tree before a leak could show itself. Its checker records that the ts arm still cannot fail (that
  engine passes an empty call graph on the report route, a second structural guarantee), because a reader
  must not take four MATCHes for four equally strong arms.
- **⟨0.29⟩ PART 47's naming row STRENGTHENED — from "the word `forbid` appears" to the RULE TEXT.** The
  weaker form carried a comment saying it was weaker than it looked and why: two engines could not
  satisfy the stronger one. Re-measured before changing anything, and the filing was half wrong — rust,
  java **and candor-ts** all printed `forbid model -> model`; only candor-swift printed a bare count. A
  two-engine item was a one-engine item. Both engines' messages now carry the rule in `why` itself rather
  than relying on a caller's prefix, because three ts callers print `why` alone (including the MCP agent
  channel). Falsified: reverting swift to the count-only message fires the new arm, with a diagnosis
  distinct from the never-says-`forbid` one.
- **⟨0.29⟩ §2 THE FILE SET — what a report says about code it never opened** (FILE-SET-DESIGN.md, rung 2
  of 4: *disclose + peek*), pinned four-way by **PART 48**. ⟨0.21⟩'s `unanalyzed` names files an engine
  OPENED and could not read; nothing named files it never opened at all, and a consumer cannot tell the
  two apart because `analyzed.count` is a NUMERATOR whose denominator — the file selector — is invisible.
  Measured 2026-08-15/16, one fixture shape per engine (a same-language `Exec` outside the selector, under
  `deny Exec`): **all four answered `policy ✓` / `no violations` at exit 0**, with no stderr note, no key
  and no exit code. A false all-clear under an explicit deny, in every engine — and the four AGREED, which
  by this project's own rule is the weakest evidence available: common-mode, and here common-mode wrong.
  - `excluded: [{class, count, peeked, reason}]` — the scope, ALWAYS emitted including `[]` (⟨0.27⟩'s
    zero-match rule; under ⟨0.26⟩ an absent key means *cannot answer*). Counts, never file lists.
  - `outOfScope: [{fn, path, effects, class, reason}]` — the peek. **MUST NOT move the verdict**: never a
    `violation`, never in `functions`, exit code unchanged. Emitted only when a policy is configured AND
    honoured, and only for effects it DENIES.
  - `peeked` is load-bearing, not descriptive: an empty `outOfScope` is a claim about the classes marked
    `true` and no others. candor-java cannot read an uncompiled `.java`; candor-swift will not read
    `.build/`. Without the flag their `[]` certifies files nobody opened.
  - `class` tokens are **engine-chosen and not interchange vocabulary** — the selectors differ per
    language, and a shared enumeration would force one engine to file its exclusion under another's name.

  **PART 48's rows are the BOUNDS, not the finding**, because a part asserting only "the warning fires"
  passes against an engine that reports every file it ever skipped: policy-bounded (`deny Net` says
  nothing about the same `Exec`), policy-scoped (no policy ⇒ the key is ABSENT, since `[]` would be a
  claim), verdict-unmoved, and the CONTROL — a project with nothing to exclude still emits `excluded: []`,
  without which the part passes against an engine that fails everything. **Falsified five ways on the real
  harness before it was trusted**, each perturbation producing its own diagnosis.

  **The TWIN arm is how the "never a second analysis path" MUST became observable at all.** No row can
  read which code path produced a finding, and a MUST no row exercises is what the ledger exists to stop
  accumulating — so each engine is asked the same question twice, through the peek and by scanning that
  code as an ordinary target, and the two effect sets must agree. It does not prove one path; it fails
  exactly when two have diverged.

  *Not covered, and recorded as a decision rather than left to be discovered: a file in no language the
  engine reads. A project whose `Exec` lives in `scripts/deploy.sh` is still one where "candor says no
  Exec" is a dangerous sentence (FILE-SET-DESIGN §3, N3).*
- **PART 47 now binds the ADVISORY siblings of the report route, not the gate alone.** §3.1's
  answerability MUST covers every verb reading a §2 report; the part pinned `gate --report`, so the
  siblings drifted in silence. Measured over a `forbid`-only policy: `unverified` and `fix-gate` emitted
  `{"ok": true, …}` at exit 0 in rust, ts and swift — rust in prose, *"no deny/pure boundary crossings in
  this report ✓"* — while candor-java, the reference engine, disclosed and withheld `ok`. All four now
  reach exit 2 under `--strict`, which is the form where the exit IS the answer, and the row asserts it.

- **RETRACTED, one commit after it landed: the §6.2 `forbid`-on-a-report clause.** It was wrong in three
  ways a review found and the commit that wrote it did not. (1) It said the behaviour was "specified
  nowhere" — §3.1's ⟨0.24⟩ ANSWERABILITY rule had specified it since 0.24 and names `forbid A -> B` in its
  own list, so the register briefly held two entries for one MUST, one pinned and one not: a drift channel
  dressed as a pin. (2) Its stated ground was FALSE and had already been retracted one section up — it
  claimed a report's `calls` graph is effect-relevant so a crossing into a pure unit is invisible, but
  §2.2 requires the SIDECAR to carry every project function's edges including pure ones, and PART 1b pins
  that; §3.1's `allow` bullet had already corrected exactly this reasoning ("Uniform refusal is the
  requirement; the wire's contents are not the reason"). (3) It stated the refusal UNCONDITIONALLY, which
  contradicts §3.1's precedence ruling — where a certain violation stands beside the refused rule the gate
  exits 1 with the rule disclosed as `unevaluated`, and all four engines do exactly that. A rule stated
  over the INSTANCE that was measured rather than over the CONDITION, for the fourth time in this
  document, in the section whose own commentary names that hazard. §6.2 now POINTS at §3.1, and the
  retraction note stays in place: a wrong clause deleted without its reason is a clause somebody rewrites.
- The descriptive scope-matching paragraph went with it. It described matching as a segment-prefix; the
  normative rule is a CONTIGUOUS RUN of segments anywhere in the FQN, exact but for a prefix-matching last
  segment — an infix rule. Its conclusion was right and its mechanism was not, and the mechanism is what a
  reader generalises from. The limitation it described lives in the umbrella backlog as the ⟨0.29⟩ `only`
  proposal, which is where the fix is.
- **PART 47 hardened, after a review showed its report-route assertion could pass for two unrelated
  reasons.** It asserted one integer. Now: the report must EXIST and be non-empty (an absent or empty
  `--report` path also exits 2 in all four engines, so an `ls` glob that missed would have printed MATCH);
  the SAME report under a deny-only policy must exit 0 (otherwise a broken report route refuses everything
  and the row proves nothing); a `deny Fs` + `forbid` policy must still exit 2, which is the row that
  separates REFUSED from SILENTLY DROPPED — a one-rule policy could not, because dropping the only rule
  trips the ⟨0.28⟩ zero-rule refusal at the same exit code. Calibrated rather than reasoned: an unknown
  rule kind every engine really does drop exits 0 beside the same deny, where `forbid` exits 2. Plus the
  refusal must say `forbid`, and an absent engine now prints SKIP instead of being counted silently in a
  summary that said "every engine".
- The ledger binds PART 47 to §3.1's statement, which was `pre-ledger` and unbound — the statement the
  part actually exercises.


- **§6.2: a `forbid` rule MUST NOT be evaluated from a REPORT, and conformance PART 47 pins it.** A
  report's `calls` sidecar is EFFECT-RELEVANT — an engine keeps the edges that carry an effect — while
  `forbid` matches on NAME, so a crossing into a wholly PURE unit is absent from the graph and the rule
  reads GREEN where a scan fails. An engine given `forbid` on a report route must refuse at exit 2 and
  name the rule, never evaluate it and never drop it silently.

  **This records behaviour all four engines had already converged on independently**, each naming the
  effect-relevant call graph as the reason, and which nothing specified or pinned. Written down because
  unanimous good judgement is not a contract: a refactor of any of the four could regress it to a silent
  green with no row to notice — the "a pinned clause with no row still drifts" lesson from PART 39, one
  level earlier. PART 47 carries the SCAN route as its control, so a refusal cannot pass on an engine
  with no layering support at all, and both directions were falsified.

- **§6.2 also states a consequence of scope matching** that writing a real layering policy hits at once:
  a scope is a segment-prefix, so it contains its own sub-scopes, and `forbid a.b.model -> a.b`
  self-fires on every call inside `a.b.model`. "This package may depend on nothing outside itself" is
  not directly expressible; a leaf can only be protected by enumerating what it may not reach, and that
  list does not cover a package added later.

  Both found by pointing candor's own architecture gate at candor for the first time.
## [0.28.2] — 2026-08-15


- **`conformance/.gitignore` covers the preflight's reuse stamp.** A local cache of which SHAs were
  green, so `release-preflight` [11] can tell whether anything that could change the answer moved.
  It has to be ignored or it defeats itself: an untracked file makes the tree dirty, and a dirty tree
  correctly forbids reuse — so the stamp would have forbidden reuse on its own first write.
## [0.28.0] — 2026-08-14

- **SPEC §2 envelope example** carried the previous floor in one spelling the bump's pattern missed.

- **Conformance PART 46 — a caller of a body-less local declaration is not pure, four-way.** candor-ts
  certified callers of declarations it had never seen a body for and nothing here could see it: the same
  shape crossing a PACKAGE boundary has been pinned since the scan-boundary work (PART 21), while the
  LOCAL case was never asked. The row asserts on the CALLER's transitive set — what a gate reads — because
  the engines legitimately differ on where the disclosure lands (java charges the declaration, rust and
  swift the edge) and §4 makes the reason class per-language. Calibrated: with the candor-ts fix reverted
  it reddens on ts alone.
- **PART 38 (`ignored`) and PART 39 (the caveat's channel)** — two ⟨0.28⟩ clauses that were ruled, written
  down, implemented four-way, and asserted by nobody. PART 39's first draft was wrong twice in one day.
- **The skip ratchet** — a reference-led SKIP means "this engine has not shipped the rung", so a rung that
  UN-SHIPS looks identical to one that never shipped. Deleting a whole rung left the suite green; the
  ratchet caught three parts, not the one it was built for. An engine the runner does not HAVE is not a
  missing tally.

- **⟨0.28⟩ `--json` beside `--gate-json -` on the SCAN route is refused.** On the gate verbs `--json` IS
  `--gate-json -` (one artifact, named twice); on a scan `--json` writes the REPORT to stdout, so asking
  for both puts a report and a verdict on one stream. Measured: four engines concatenated them, so
  `json.load()` on stdout over violating code returned `Extra data` and no verdict at all; the fifth
  refused but only after the report had gone out. Now exit 2 with the fail-closed document as the stream's
  only content, decided before the report is written. `--json <file>` beside `--gate-json -` is unaffected
  — two artifacts in two places is what the operator asked for.

- **⚠ ⟨0.28⟩ The artifact rule was implemented in the COMPARISON and not in the WRITE.** With a SINGLE
  `--gate-json` pointed at a symlink — one `artifacts/verdict.json` linked into a shared directory, an
  ordinary CI layout — two engines published by temp-and-rename, replacing the link instead of following
  it, so the real artifact kept a previous run's `{"ok": true}` while the gate FIRED. A stale green with
  no duplicate and no operator mistake. The sink is now resolved to its final artifact before writing.
- **⟨0.28⟩ Device+inode is not optional where the platform offers it.** Two HARDLINKS to one inode were
  refused as two sinks by three engines and gated as one by the fourth; a dangling symlink beside its
  target split the other way. Both are one artifact, so refusing is a FALSE refusal of a legal command —
  the mirror of the stale green.

- **Conformance: PART 36 grows (b18)/(b19)/(b20), PART 4l pins the CAUSE, and the agents shim runs the
  entry users run.** (b18) an extra positional after an armed stream sink — the first row here that came
  out of a GENERATED argv sweep rather than a hand-written cause list. (b19) the same unreadable-config
  cause on the `gate` VERB route, which had no cell for any refusal cause at all. (b20a–d) the ⟨0.28⟩
  two-sink rung. PART 4l had pinned the Unknown COUNTS but never the cause sentence, which is exactly
  where all four engines drifted for four engine-versions. And the candor-agents shim imported
  `scan.main` while the CLI runs a wrapper around it — so those rows were exercising a different program
  than anyone ships.
- **`conformance/part.sh`** — run ONE part in ~6s instead of the suite's 476s (measured: the shared
  preamble is 8s and each part builds its own fixtures). Boundaries come from the markers the suite
  PRINTS, not from its comment headers, which are not a grammar; every slice is checked to carry exactly
  one part and to parse (`--check`, ~10s). A filtered run refuses to print `conformance: OK`, and a part
  that dies on state an earlier part built exits 2 as INCONCLUSIVE — a filtered run can manufacture a
  false RED as easily as a vacuous green.


- **⟨0.28⟩ One run names one sink: a repeated `--gate-json` is refused, and every path named gets the
  refusal** (§3.3.1). `--gate-json A --gate-json B` is a broken gate configuration — the operator has said
  where the verdict goes, twice, and both statements cannot be honoured — so the run exits 2 and the
  refusal document is written to *each* path given.

  Writing to each is the load-bearing half. Measured across all four code engines before this rung: **every
  one took the last path, wrote the verdict there, and left the first exactly as it found it**. (An earlier
  draft said one engine refused; that came from a contaminated measurement — it had been handed a second
  POSITIONAL, and its extra-argument refusal was recorded as a duplicate-sink one. Re-measured against a
  pre-rung build.) The rung binds EVERY route that accepts `--gate-json`, and the (2) input exemption
  covers the offending PATH, not the run. Pre-seed `A` with a previous run's `{"ok": true}`, run a gate that fires, and `A`
  still reports the code clean — the ⟨0.27⟩ stale green reached by a spelling nobody had considered, and
  worse than the case that motivated it: the run did not fail, the gate *did* fire, and the operator's own
  command named the path that lies. A CI wrapper appending `--gate-json artifacts/verdict.json` to an
  already-configured command produces it on every run.

  Two identical spellings of one path are ONE sink and are not refused — the §3.3.1 artifact rule applies
  here too. Conformance PART 36; no report-schema change, so a 0.27 consumer is unaffected.
## 0.27 — current floor (the engine pin, the zero-match rule, and a producer's declared refinements)










- **PART 36 (b16)/(b17): an engine pin the build does not satisfy, and an empty scan.** Both are
  ordinary CI accidents and §3.1 exempts no cause; neither had a row, and both left the stream empty in
  at least one engine. (b16) also caught a fix that emitted TWO documents where one was intended — a
  byte count had made it look right.
- **PART 36 (b15): the FILE sink's form of the config cause.** Every stream row poses stdout; the file
  sink has a different property — arming leaves a placeholder and the refusal must REPLACE it — and an
  engine can satisfy one form while failing the other. One did: it streamed the refusal for an
  unreadable config and left a previous run's `ok: true` on disk.
- **PART 36 (b14): a sink inside a dep DIRECTORY.** The guard registered the directory token; the loader
  reads the files inside it. No row posed the directory spelling, so all four engines destroyed the
  operator's dep report and exited 0 with `ok: true` over it, while the FILE spelling of the same
  channel had been guarded for a release. The row asserts both the refusal AND that nothing was written
  — a refusal that arrives after the input is already gone is not a refusal.
- **PART 36 (b13): a gate-adjacent flag with NO VALUE.** §3.1 names this cause beside the unknown flag,
  and (b1) posed only the unknown one — so an engine could route that and leave this raw. One had.
- **PART 36 (b12): the nonexistent-target cause, posed at last.** It was written once, found unposeable
  with the shared probe's calling convention — the slice removed the OUT-DIR for two engines, which then
  scanned a VALID tree and "passed" at exit 0 — removed, and named as uncovered in a comment. `VD_BAD`
  poses it properly: the engine's own invocation, supplied by the caller who knows its argument shape.
  An engine that supplies none now says so AT RUN TIME rather than in a source comment, because a cause
  disclosed only to someone reading the generator is disclosed to nobody running the suite. Green
  four-way.
- **PART 36 rows (b9)/(b10)/(b11) — the cells every earlier stream row skipped.** (b1)/(b2)/(b5)/(b6)/(b8)
  all pose REFUSAL causes, so an engine could dedupe its refusal writer and leave the VERDICT writer
  writing per-flag: one did, for a round, and a refusal-path row cannot see it. (b9) poses a CLEAN
  verdict and (b10) a FIRING one, both with `--json --gate-json -` — one artifact named twice, which
  §3.1 says must still be exactly one document. (b11) poses an UNREADABLE CONFIG, the earliest exit-2
  cause and the one the sink is least likely to be armed for; it found the last engine still leaving
  that stream empty. All three were written BEFORE the fixes they now hold.
- **PART 36 rows (b5)/(b6)/(b8), and a cause named as UNCOVERED rather than left green.** (b5) poses a
  post-parse refusal on the `gate` verb — (b4)'s unknown flag dies inside the flag loop, a different path,
  and the difference caught a DOUBLE document. (b6) poses `--json --gate-json -`, one artifact named
  twice. (b8) poses the configured-dep cause on the machine channel, and found three engines refusing
  correctly while leaving the stream empty. A row for a nonexistent TARGET path was written, found
  unposeable with this probe's calling convention — it sliced the OUT-DIR for two engines, which then
  scanned a valid tree and passed at exit 0 — and removed in favour of a comment naming the gap. A row
  that cannot pose its condition is worse than no row.
- **PART 35 rows (d)/(e) and PART 36 rows (b4)-(b6) — the cells that were missing.** PART 35s title
  is "a configured dep that cannot be read" and its rows only ever tested a dep that was NOT THERE; two
  engines shipped the wrong answer for the other clause of §2s disjunction, straight through a green
  suite. PART 36s stream rows all ran the SCAN route, so three engines left stdout empty on the `gate`
  verb and passed; row (b5) then caught a DOUBLE document that (b4) could not see, because an unknown
  flag dies before the second sink registration, and (b6) caught `--json --gate-json -` naming one sink
  twice. Every row was written after the defect it catches was measured.
- **The conformance suite was dirtying the repo it lives in — and my first fix was to the wrong arm.**
  An engine arm that runs a scan with no `--out` writes its report into the CURRENT directory, which is
  this repo when the suite is run the documented way. Not untidy: `bin/release.sh` step 0 refuses a dirty
  tree, so the suite you MUST run before a release was making the release refuse to start.

  I put `--out` on PART 32's candor-agents arm, saw a clean run, and moved on. The files came back on the
  next run: the real site was PART 34's, which I had not looked for because I fixed the instance I had
  rather than sweeping for the class. PART 34 resisted `--out` — its probe drives several invocations and
  some read the report back from its DEFAULT location, so redirecting the output made four assertions
  vacuous. Moving the WORKING DIRECTORY instead leaves every default intact and simply stops "the current
  directory" being this repo.

  **The durable part is that the suite now checks ITSELF**: it snapshots `git status --porcelain` at the
  start, compares at exit, and FAILS naming any new entry. Grepping for the class does not work — every
  engine invocation looks alike — and I could not have found the second site by reading. Validated the
  only way an instrument can be: a deliberate stray write planted right after the snapshot, which it
  caught and named. A tree that was already dirty when you started stays your business.
- **§4's zeroMatch clause claimed too much.** "Byte-identical to a pre-⟨0.27⟩ verdict" is not true — the
  envelope's `spec` moves with the floor either way. The claim worth making is that no input where every
  rule bound something gains a field, and that is what it now says.

- **§3.1/§4 ⟨0.27⟩ THREE VERDICT-DOCUMENT CELLS PINNED, five-way (conformance PART 36).** A cross-engine
  review found three cells where the engines agreed on the exit code and diverged on the `--gate-json`
  DOCUMENT — the artifact a CI wrapper actually reads. (1) **The composed document** (a certain
  AS-EFF-005 regression beside an unhonourable policy) had FOUR spellings; ruled: it is a VERDICT —
  `refused`/`reason` are the refusal document's discriminator and MUST NOT ride beside `violations`; the
  refusal travels as `unevaluated`, one entry PER RULE of the refused policy (an unreadable policy gets
  one entry naming the whole file). (2) **The stream sink**: `--gate-json -` cannot be armed, so the
  fail-closed document is written to stdout on EVERY exit-2 cause — measured, engines answered or left
  the stream EMPTY according to which early exit fired. (3) **`zeroMatch`**: §4's zero-match list was
  stderr-only in all five engines; it now rides the verdict document (raw lines, code-point sorted,
  deduplicated, omitted when empty, both routes), never the refusal document. PART 36 carries four
  vacuity floors; run against the pre-fix engines it fails on every group.

- **§2 ⟨0.27⟩ RULING: a configured dep that cannot be read is UNEVALUABLE, not reduced coverage.** java
  and swift refused; rust and ts continued at exit 0. Both postures were internally coherent, which is
  why it needed a ruling — and one `.candor/config` meaning two things is the defect whichever way it
  goes. What decides it is where the answer LANDS: with the dep chained a caller reads
  `inferred: ["Fs"]`; with the same config and the report missing, a continuing run publishes
  `inferred: []` — a ⟨0.21⟩ purity claim, in the artifact, about a function whose dependency the operator
  configured precisely so it would not be one. The coverage note travels on stderr, which the consumer
  does not read. Pinned by new conformance **PART 35**, whose (b) and (c) rows keep it about the DEP
  rather than the key: absence of `deps` is still a complete answer about what was seen.

- **PARTs 32 and 34 cover candor-agents now, and it failed both on the first run.** Each part ran four
  engines while candor-agents declares the same `spec 0.27` and exposes the same `--policy` and
  `--gate-json` — so it shipped the ⟨0.27⟩ rung's own false all-clear (`--policy P --gate-json P`
  destroyed the policy and the next run went green on a violating fleet) and scored a zero-match rule as
  satisfied. A part that covers four engines covers four engines; the fifth's claim to the contract was
  taken on trust.
- **The shared probes now take the FIRING rule as a parameter.** They hardcoded `deny Fs`, which binds
  nothing in a fleet whose units are agents — so the agents arm's vacuity floors fired correctly and said
  so, rather than passing over a rule that could never match. And the zero-match assertion accepts
  "matched NO function" or "matched NO unit": the property is that the zero match is DISCLOSED, and
  making a domain engine describe agents in another engine's nouns would cost accuracy for nothing.


- **Conformance PART 34 gains the config×gate cell, and it was empty and defective.** The scan group's
  row (f) pinned the config channel on the scan route; the gate group pinned the FLAG channel on the gate
  route; the cell where they cross had no row — and `gate --report R --gate-json <config-declared
  policy>` overwrote the policy at exit 0 in rust, ts and swift, while java refused for the opposite
  reason (its gate verb never read the config at all — a 3-vs-1 split). "A part that pins a rule on one
  route pins it on one route" recursed once. The new row asserts the config-declared policy GATES before
  asserting anything about the sink, and that control is what caught java.
- **The suite now cleans up after itself on an interrupt.** PART 34 row (f) must write a `.candor/config`
  INTO the scan target — the point of the row is that the engine discovers it — and the target for three
  engines is the TRACKED `conformance/gate/` tree. A review measured what an interrupt in that window
  costs: a leftover config declaring a dangling policy makes a later run's flagless rows exit 2 for the
  wrong reason, so a defective engine passes them. Now an `EXIT INT TERM` trap, not a tidy-up line that
  only runs when nothing goes wrong.
- **`conformance/differential/` (new): generative grammar differentials.** Every config-layer defect
  found this week was found by hand, one spelling at a time, and they are all instances of one property:
  the engines must read the same config the same way. 2546 generated configs and 61 generated policies,
  compared on exit code with no expected-value table. Both are CALIBRATED against real regressions — a
  pre-fix candor-agents (27 rows light up) and a candor-ts with its unrecognised-token error swallowed
  (14 rows) — because a differential that has never failed is not evidence. The README records the two
  traps the harness itself fell into: a shared target directory measures the harness, and a differential
  is only about the thing you vary.

- **Conformance PART 34 grows the rows that would have caught this round.** As shipped it probed the four
  SCAN CLIs with a `--policy` FLAG, and a review then found two cardinal sins it was blind to by
  construction: the reference engine's `gate` VERB had none of the guard (`gate --report R --policy P
  --gate-json P` → exit 0, `"ok": true`, policy destroyed), and in ALL FOUR engines a policy declared by
  `.candor/config` — the checked-in form CI uses — was invisible to a guard that keyed on the flag. Two
  new row groups: the config-declared-policy channel with its own control, and the `gate` verb on four
  engines, including the sink naming the `--report` (which §3.3.1 lists as an input and no engine
  checked). The report rows immediately failed rust and ts. Row (c) now also asserts the EXIT CODE on the
  relative-spelling retry, not just the policy's bytes.

- **Conformance PART 33 gains an ASCII-digit row.** `Character.isNumber` (Swift) and `str.isdigit()`
  (Python) are Unicode-wide, so `engine ٣.٣` NORMALISED as a version in two engines — a MISMATCH rather
  than MALFORMED, which is the difference that decides whether the "unreadable unqualified line is not
  hidden by a qualified pin" rule fires. Beside a good qualified pin the run passed at exit 0 while three
  engines exited 2. ALONE it was already refused everywhere, so only the PAIRED shape is diagnostic —
  the row uses it.

- **§3.3.1 — WHEN the gate sink is armed, and the one thing never written to it.** The refusal rule said
  WHAT to write and never said WHEN, and every engine got the timing wrong differently. Two MUSTs now:
  arm at the instant `--gate-json <path>` is accepted and before any other exit (engines armed after the
  config load, after pin resolution, and — in the reference engine — mid-flag-loop, which made the
  contract depend on argv ORDER); and refuse, writing nothing, a sink that names an INPUT of this run.
  `--policy P --gate-json P` armed over the policy, which then parsed as zero rules, and a gate that
  exits 1 exited 0 with `"ok": true`. That refusal is the only exempt cause and it is not a carve-out:
  the path was never a sink, so no verdict at it can go stale. Sameness is resolved as ARTIFACTS, not
  strings — the engine that already had this guard was defeated by `./P` against an absolute `--policy`.
- **The §3.3 flag table still carried a reading ⟨0.24⟩ superseded** — "on exit 2 it writes a verdict only
  for an INCOMPLETE analysis, never for a broken gate config" — 2000 lines from the note recording the
  supersession, so the stale rule was still there to be implemented, and one engine implemented it. The
  paragraph making that correction observes the defect class had "now been produced three times"; this
  was the fourth, in the table the first three were about.
- **Conformance PART 34 (new): the gate sink is armed, and never armed over an input.** A release review
  found a machine-readable false all-clear in four engines and this suite would have passed every one —
  nothing in it had ever seeded a stale document or pointed `--gate-json` at a file the run reads. Five
  rows, every one seeding a green document first, plus the control that stops an engine passing by
  arming and never disarming.
- **Conformance PART 33 gains a Unicode-whitespace row.** Two of five engines split config lines on
  ASCII space/tab only, so a NO-BREAK SPACE between `engine` and its version made the line an unknown
  key: a false disclosure over a silently unenforced pin, with a MISMATCHED version passing at exit 0.
  The part's own comment says a row that pins one spelling pins one spelling.


- **PART 33 pinned one spelling of its own rule.** The malformed-unqualified row used a two-token junk
  value, which every engine catches by arity — so it was green five-way while the one-token spelling
  split the family four-against-java, silently. Both spellings run now. The candor-agents checkout also
  went to one of two differential legs, turning the strict one red.

- **PART 33's candor-agents row certified what CI never ran.** candor-spec's conformance workflow never
  checked the engine out, and the row was guarded by a bare `if` that vanished when the repo was absent —
  so CI printed "the engine pin is enforced identically in EVERY engine" over four. The checkout is now
  fatal like the other three, and an absent repo is reported rather than skipped. A new row also pins the
  malformed-unqualified case the reference engine was getting wrong.

- **Conformance PART 33 now probes candor-agents.** Its headline said "every engine" and the changelog
  said "ALL FIVE now enforce it (PART 33 pins that)" while it tested four — and agents was one of the two
  engines whose normaliser accepted `vv0.27.0`, so the row written about that defect never ran for one of
  the engines that had it.

- **Panel review: SPEC §3.4 gains the ruling for a collision two MUSTs created.** "Ignore a pin
  qualified for another implementation" and "an unreadable pin exits 2" disagree on
  `engine swift 0.99.0 junk`, and a differential found the family split three ways on it. The skip is
  now WHOLE-LINE and takes precedence: read the qualifier first, and a malformed line naming another
  engine is that engine's problem. Also stated: a version carries AT MOST ONE leading `v`, and config
  parsing must tolerate CRLF. **Conformance PART 33 gains a row for each — plus the VACUITY FLOOR it
  lacked**: every row compared against the no-pin baseline, so an engine that always exited 2 would
  have passed the whole part. PART 32 had a floor; this one did not until a review said so.


⟨0.27, 2026-08-06⟩ **§3.4 — `engine [<impl>] <version>`: the engine↔baseline coupling becomes
a tool-enforced invariant.** Engines already refuse a baseline whose §2.1 provenance BUILD ID differs
from the running one — but a build hash is not something a consumer can DECLARE, so the version lived
in CI configuration, decoupled from the baseline it is married to, and a mismatch was found only after
running the wrong engine. A pin is declarative (so tooling can also read it to FETCH the right engine)
and it reaches the case the existing refusal cannot: a run with NO baseline configured, since that
refusal lives inside the baseline comparison. Scope is stated: this binds a producer that ANALYSES
code, never a verb that merely reads an existing report, where the running engine is an evaluator and
its version says nothing about the artifact.
A mismatch now exits **2** (unevaluable, never 1 — a machine consumer must not read "I could not trust
this" as "your code broke a rule"), as does an unreadable pin: this is the one place §6.2's warn-and-skip
inverts, because skipping a PIN hands the operator a guard they believe is on. **Two answers must NOT
change the exit code** — an absent pin (opt-in by construction) and a pin a SOURCE BUILD cannot check,
which is §3.1's unanswerable-condition rule applied to configuration: disclosed, never scored, including
as satisfied. The qualified form exists because the family versions as a ladder, so a bare pin in a
polyglot repo would fail whichever engine had not yet caught up. No `CANDOR_ENGINE` env var and no
`--ignore` escape: an assertion an ambient environment can switch off is not one. Implemented and enforced identically by ALL FIVE engines,
pinned by conformance **PART 33**; **PART 13b** separately pins that the key is recognized rather than
reported unknown — a key this spec defines must never be called unknown, which would tell an operator
their pin was ignored while a sibling engine enforced it.

⟨0.27, 2026-08-06⟩ **§4 — a policy rule whose SCOPE matches no function is UNANSWERABLE, and
MUST be disclosed rather than scored as satisfied.** A `deny`/`forbid` naming a layer that binds nothing
was evaluated and bound nothing, so it cannot have caught anything — yet every engine scored it as
passing, which makes a one-character typo in a layer name a permanently green gate. Measured in three
engines: `deny Net orders` exits 1 on a real violation, `deny Net ordrs` exits 0 with `policy ✓`, and
`unverified` then calls the layer *"PROVABLY clean"*. The asymmetry is the tell — a typo'd **effect**
token already exits 2 naming the accepted vocabulary, while a typo'd **layer** token passes. The remedy
is disclosure, not refusal: a zero-match rule is legitimate when one policy is shared across repositories
and a layer exists in only some. Implemented FOUR-WAY (candor-swift led it; java, rust and ts
followed) and pinned by conformance **PART 32**, which pins the disclosure, that the verdict and exit
code are unchanged by it, and that a scopeless `deny` is exempt — it binds every function by
construction, so it can never be this kind of typo.

**Conformance PART 13b ran no engine, for its entire existence.** It located the scan target by shifting
the other arguments away, so the probe executed the target DIRECTORY instead of the engine, got
`env: /path: Permission denied`, and matched that against `unknown config key '<k>'` — which it can never
contain. Both checks passed unconditionally and all four engines were reported clean, always. This is the
part written *after* the `net-partner` false disclosure, and it could not have caught it. Repaired; the
repair then reported seven failures that were all false (an engine *honouring* `policy` says `policy ✓`,
which the bare-name match read as a malformed disclosure), so it now matches the quoted `config key '<k>'`
form that every engine uses for a diagnostic about a key. Verified able to fail before being believed.
`engine` is pinned there in the asymmetric state it ships.

Repo tooling in this cut, both about gates that could not fail:

- **`scripts/check_agents_vs_engine.py`** — the AGENTS.md drift direction nothing covered. The existing
  gate compares A DOCUMENT TO A DOCUMENT, so a claim stale in the file is stale in the embedded copy too
  and the two agree perfectly while both are wrong. This one RUNS each engine on a fixture and reads the
  facts the engine states about itself: `spec`, `extensions`, `resolves`. Found by hand first —
  candor-swift's contract taught `privacy/1` while the engine had emitted `privacy/2` for weeks. An
  earlier design comparing DOCUMENTED FLAGS against accepted ones is kept in the header as a rejected
  one: it reported 20 phantoms, of which zero were real and two were `git`'s.
- **Its own spec row was vacuous on the first run**, and the amendment sweep before it printed a clean
  bill after reading no files. A bare `\b0.27\b` search matched the build version `candor-swift-0.27.0`
  carried by every contract, so the row could not fail however stale the claim was.

⟨0.27, 2026-08-05⟩ **§2.1 — `resolves`: a top-level envelope array naming the optional per-function
refinement surfaces this producer actually computes.** §2's optional fields are omitted when the answer
is undetermined, so absence carried two meanings a consumer could not separate — *"I looked, and it is
undetermined"* versus *"I do not compute this at all"* — and only the first licenses reading the absence
as an answer. A producer MUST NOT list a surface it does not compute; a consumer MUST NOT read an absent
field as "undetermined" unless the surface is declared. Same construction as `extensions`, different
scope: `extensions` declares an ecosystem surface, `resolves` declares a refinement of a floor field.

Also in this rung: **§2 `fs` kinds now TRAVEL the call graph**, with an undetermined contributor
suppressing the whole field rather than emitting a partial one (a partial `fs` reads as the positive
claim "reads but never writes"). Pinned four-way by conformance **PART 31**, which found all four engines
wrong on its first run.

## 0.26 (a sidecar's KEY SET is its manifest)

⟨0.26, 2026-08-02⟩ **§2.2 — an absent type in the hierarchy sidecar is UNANSWERABLE, never "has no
supertypes".** A producer MUST emit a key for every type it indexed, `[]` included; a consumer MUST read
the key set as the closed set of types it can answer for, and a type absent from a present sidecar MUST
disclose rather than drop. Adds the optional `@unanalyzed` diagnostic key beside it.

**Why a rung and not a clarification: absence carried two meanings and the format could not tell them
apart.** A type with no supertypes was omitted, and so was a type the pass never looked at. A consumer
asking `isSubtypeOf(t, owner)` about an unindexed `t` got `false` — indistinguishable from a true
negative, and a positive claim about a type nobody analysed.

**The measurement that made it a format change.** On a real scan with only the sidecar doctored, removing
ONE entry dropped the dispatching function from `callers --include-unknown` (`[]` where the control gives
it), while removing the sidecar ENTIRELY left the answer correct. A PARTIAL sidecar was worse than an
ABSENT one — and no consumer can patch around that alone, because without a manifest it cannot tell a
producer's silence from its answer. java and ts behaved identically, which is evidence about the format
rather than either engine: neither had a third answer available.

**Engine work in all four**, unlike 0.25. java `78aad6d`, ts `caeda66`, swift `ea3de21`, rust `4cae735`.
swift's half was larger than filed — protocols were absent from its sidecar entirely, as keys AND as
edges, so every `Impl: Mid` / `Mid: Base` chain dead-ended at the middle. rust is consumer-only
(candor-scan writes no sidecar), which is precisely why its tri-state matters: every hierarchy it walks
was produced by another engine.

Pinned by conformance **PART 30 (P6, sidecar manifest fidelity)** — the property the self-differential
family was missing, since P2 and P3 degrade the chained dep REPORT and nothing degraded a SIDECAR.

## 0.25 — (an ambiguous join key is UNIONED, not dropped)

⟨0.25, 2026-08-02⟩ **§2 chaining rule 1 is REVERSED, and this is a correction rather than a preference.**
Through 0.24 the rule read: *"An ambiguous key (two dep functions sharing it) is dropped, not picked
from — §4's under-report-don't-fabricate rule, applied at the join."* All four engines now UNION such a
key, and conformance PARTs 25/26 pin the union — so an engine conforming to the 0.24 TEXT would fail the
suite, and a third party implementing to it would build the cardinal sin deliberately.

**What the old rule cost.** A dropped key resolves to nothing, so the CALLING function leaves `functions`
entirely — and under ⟨0.21⟩ an absent entry is a *positive claim of purity*. It prescribed silence over a
call whose target the engine had just declared itself unable to name, and cited §4 to license the one
thing §4 forbids. Named live instance, on one of the most-depended-upon crates there is:
`hyper#client::conn::http1::Builder::handshake` = `['Log']` @0.14.32 vs `[]` @1.9.0 — both in the build,
key withdrawn, consumer reads it absent = pure.

**The union is measured, not argued.** Across candor-rust/pgman/ebman every one of the 123 colliding keys
whose entries disagreed is one function at two VERSIONS of one package. Cost: 7 effect-items to close 123
purity claims; on the consumer side 11 functions recovered, 0 lost, 0 narrowed, and **every one of the 65
added effect-items was `Unknown`** — no concrete effect charged to a function that did not have it.

**Also normative:** trust levels do NOT rank at the join (a §2.1-downgraded entry joins the union rather
than being discarded under a trusted one — the distrusted report is the only evidence a second,
unverifiable version is present), and the observable invariant is **order-independence**, which
withdrawal and trust-ranking both fail.

**The prohibition on PICKING is unchanged.** Only the prescription to DROP is reversed.

**No engine work.** All four already ship the rung; 0.25 is the contract catching up with the
implementations, so adoption is a floor bump and nothing else.

## 0.24 — current floor (contributes, ambiguity, and a gate that can now go red)

⟨0.24, added 2026-08-01⟩ **CONTRIBUTES**, **`ambiguous:` as a fifth reason kind**, the frontier's
**unanswerable-condition rule**, **`gate --report`**, **locale-independent ordering**, and **`--class`
semantics**. Pinned four-way by conformance **PARTs 24–27**.

**This is the first rung that can turn a GREEN GATE RED.** A `--strict` step on `unverified` or `fix-gate`
that read green over a report `gate --report` refuses now exits 2. That green was the defect, not the fix:
the advisory verb was reporting a cleaner answer than the gate would have given over the same evidence.
Measured at 0 flips against trusted dependency reports and 36% against stale ones — so a green that flips
red here is telling you the reports it read were stale, which is the thing it was always supposed to say.

The governing law, §3.2: **an advisory verb may be LESS certain than the gate, never MORE.** It is stated as
a containment (`U_clear ⊆ G_clear`) rather than a behaviour because the three defects that produced it
differed entirely in mechanism and shared only the direction of the error.

Also in this rung: an **unanswerable condition must be DISCLOSED, never scored as a failed one** — extended
from PART 21's three-row rule to query outputs, after the `callers` dispatch frontier was found silently
dropping every dot-free `dispatch:` reason, which is rust's dominant form.

**Conformance additions:** PART 24 is the first **SELF-differential** — each engine against itself across a
package split, so common-mode failure is excluded by construction. 320 live cells, zero vacuous. It found 5
defects on its first run that 44 hand-written fixtures could not see, because every one of those fixtures had
picked a single spelling.

## 0.23 — current floor (cross-package interface dispatch)

⟨0.23, added 2026-07-27, restated the same day⟩ **The type-hierarchy sidecar's extension point is a
constraint on WRITERS: every value in the file is an ARRAY of strings, metadata goes under a key beginning
`@`, and a metadata key is never the file's only key.** It was first written as a requirement on READERS —
"skip any entry whose value is not an array" — and that framing is the mistake the rung now records: it
obliges every already-deployed reader to have been updated, which is exactly what did not happen, twice
over, for the one key it was written for. candor-java's own *second* reader threw on the object value and
discarded the whole hierarchy (539 tests green through it); its *third*, candor-rust's
`candor-query::load_hierarchy`, deserializes the file as `BTreeMap<String, Vec<String>>` in one typed call
and cannot skip anything at all — **0 of 18 sidecars parsed there** on a real chained JVM corpus. And
writing the key unconditionally turned `{}` into `{"@superclass":{}}`, which flipped candor-ts's and
candor-rust's non-empty gate off the safe over-listing frontier fallback. Both failures are impossible
under the writer-side rule and neither was prevented by the reader-side one. The first such key is
candor-java's `"@superclass"`, now a **flat array** `[type, superclass, …]`: without it a consumer walking
a *dependency's* own chain cannot apply "the class wins at any depth" (JLS 15.12.2.5 / 8.4.8), and an
interface `default` shadows the superclass body the runtime actually executes. Its PRESENCE licenses the
split; a sidecar without it MUST keep the reader's previous order rather than guess. Additive and
version-gate-free in both directions. See **SPEC.md §2.2**.

The **cross-package interface-dispatch** rung — the optional `interfaceUnion` report entry (a synthetic
`pkg#Iface.method` union over a package's local implementers) + the `--workspace`/`--deps` auto-discovery
convention, so a CHAINED consumer's cross-package interface/protocol/trait dispatch resolves to the impl's
effect instead of reading pure. Gated behind `CANDOR_WORKSPACE_CHAIN` (a default report is byte-identical),
**four-way** conformance-pinned (PART 18: candor-java + candor-scan + candor-ts + candor-swift). See
**SPEC.md §2** + **WORKSPACE-CHAINING-DESIGN.md**. candor-java was recorded N/A here at first ("whole-classpath
bytecode resolves cross-module dispatch natively") — true of an UNCHAINED scan and false at the boundary; its
consumer needed no change (it keys entries by `owner.name+desc`, which is the INVOKEINTERFACE key), only the
producer, which landed 2026-07-26.

The 0.23 floor also carries two soundness-increasing, report-shape-neutral additions (contract unchanged):
the **synchronous-callback-invoker** rung — an opaque callback handed to a sync higher-order invoker
(`forEach`/`for_each`) discloses `Unknown`, machine-pinned FOUR-way (PART 1 `sync_callback_opaque`); and the
verify oracle's **coverage crediting** — transitive attribution stops at an unanalyzed frame, so it honours
the coverage envelope (§7.1) rather than false-positiving on a library's unmodelled-dependency effects. Both
are documented in **SOUNDNESS-LOG.md** (the 2026-07-18/20 reconcile-against-reality arc + value provenance).

## 0.22 — the `verify` oracle

The **`verify` oracle** rung — candor's dynamic honesty check (`observed(f) ⊆ inferred(f) ∪ {Unknown}` per
executed function), shipped per-engine as `candor verify` with a fail-closed exit-2 incomplete-attribution
verdict; the report and verdict schema are unchanged from 0.21. See **SPEC.md §8** for the authoritative,
full changelog (this file summarizes).

## 0.18 — the trust-trio

A pinned-tool-surface rung (no report-schema or verdict change; a 0.17 report and gate verdict are
byte-identical under 0.18). Two TIER-2 required additions, both enforcing §4 "never a false all-clear" at the
tool surface: **(1)** the `--strict` advisory-verb CI gate (§3.3.1) — `fix-gate`/`gains`/`unverified` advisory
at exit 0, `--strict` → exit 1 while a finding remains; a typo'd/not-applicable flag is an exit-2 error (never
a silent swallow), and `gains` has no `--policy` (a passed one names the `deny <E> gained` scan gate); **(2)**
the surface/`tour` mostly-Unknown disclosure — never "nothing hidden" (nor a `tour --json` `{"reaches":[]}`)
over a ≥⅓-Unknown graph. Pinned four-way by conformance PARTs 4l, 5b, 12b, 12c. (Rungs 0.16/0.17 are recorded
in [SPEC.md §8](SPEC.md#8-changelog).)

## 0.15

All code engines declare `0.15`; the floor is conformance-pinned (PARTs 4q/4r/4s). A **tier-1 additive**
rung, wire-compatible with 0.14. Three groups, all found/driven by real-world corpus testing:

- The **`coverage` envelope field** (§2) — the κ-coverage ledger travels WITH the report
  (`{"uncovered": [{"name", "calls"}]}`, omitted when empty — a fully-covered report is byte-identical),
  the per-function **`invisible`** field formalized, and **verb conditionality**: every engine's
  `--gate-json` re-discloses coverage as a verdict-preserving advisory, `gains --json` carries the ledger
  + `coverageDelta {nowUncovered, noLongerUncovered}`, and candor-swift's `privacy-manifest` marks its
  verdict `conditional: true` with a human ⚠ when uncovered modules could hide sensor usage (the
  wikipedia-ios false-confidence fix). Design: [COVERAGE-DESIGN.md](COVERAGE-DESIGN.md). **PART 4s** pins
  it four-way (+ the omitted-when-covered byte-compat leg).
- **Host-resolution recall** (§1, "a statically-known request") — a model/Db/Net host that is statically
  knowable but not a bare literal now resolves like an inline literal, both halves: a CONST-anchored head
  (`const API_BASE = "…"; fetch(`${API_BASE}/x`)`; java was already sound via static-final inlining) and
  a LITERAL-COMPLETE head with an interpolated path (`https://api.openai.com/v1/${p}`, `format!`, runtime
  concat from bytecode — all four engines). Sound boundaries pinned: a split authority, an interpolated
  port, and a non-model (CDN) host stay bare `Net`. **PARTs 4q + 4r**.
- **Soundness fixes** (candor-scan: cross-crate glob-reexport/use-rebind silent drop — sqlx-postgres's
  TCP-to-Postgres read pure; cfg_if! macro arms now expanded; block-nested `use` resolved. candor-ts:
  `process.env` via bracket/alias/destructure/`in` now classifies Env). Zero fabrication across the
  1337-crate realworld-oracle.

## 0.14

All code engines declare `0.14`; the floor is conformance-pinned (PART 4p). A **tier-1 additive**
rung, wire-compatible with 0.13 — a **soundness fix** for the cardinal sin (silent under-report).

- The **top-level / initializer unit** (§2 `unitKind`) — a module whose **top-level executable code**
  performs an effect is now attributed to an INITIALIZER unit (`unitKind:"initializer"`), never a
  false-`"pure"` empty report. A module-load-time model call — top-level `await fetch("…api.openai.com…")`,
  an IIFE, a bare `readFileSync`, a JVM static initializer — was **silently dropped** by candor-ts and
  candor-swift (a `deny Llm`/`deny Net`/`deny Fs` gate passed it). Found by dogfooding a real OSS LLM app.
  candor-java's `<clinit>` was already sound (the reference); rust is **N/A** (no top-level executable
  code — a `const`/`static` is const-evaluated). Each engine's unit NAME differs (java `<clinit>`, ts
  `<module>`, swift `<main>`); the effect model is identical. Conformance **PART 4p** pins it. Report bytes
  change where a previously-empty top-level module now carries a unit.

## 0.13

All code engines declare `0.13`; the floor is conformance-pinned (PARTs 4m/4n). A **tier-1 additive**
rung (a new §1 effect + a new envelope field), wire- and invocation-compatible with 0.12 (a consumer
already tolerates unknown effect names, so a pre-0.13 report/policy is unaffected). Two additions:

- The **`Llm` effect** (§1) — a machine-learning model-provider call (chat/completion/embedding/
  moderation), a **boundary effect refining `Net`** the way `Db` does. Classified from a known
  **model-host literal** (`api.openai.com`, `api.anthropic.com`, Bedrock runtime, a loopback Ollama
  `:11434`, …) OR a curated **model-SDK surface** per ecosystem; an unknown host/SDK stays bare `Net`,
  never guessed. Gate-able (`deny Llm ai/`), the sharpest `gains`/`origin` supply-chain alarm ("a
  dependency bump added an `Llm` call"), high surprising-reach salience. Conformance **PART 4m** pins it
  four-way including negative fabrication cases (an S3 bucket named "bedrock", a remote `:11434`).
- The **`extensions` envelope field** (§2) — an engine classifying effects from a **spec extension**
  discloses `"extensions": ["<name>/<version>"]`; omitted when inactive. The first extension is
  candor-swift's **`privacy/1`** — six Apple privacy-sensor effects (Location/Camera/Mic/Contacts/Photos/
  Notify) + the **`privacy-manifest`** verb (verify an app's Info.plist against its code-level sensor
  reach). Its contract lives in candor-swift/SPEC-EXTENSION-privacy.md; **PART 4n** pins that every other
  engine TOLERATES an extension report.

## 0.12

All code engines declare `0.12`; conformance-pinned (PART 5b). A **tier-2
(pinned-tool-surface)** rung, additive over 0.11 and invocation-compatible with it. The **§3.1 `gains`
`origin` field**: each `byFunction` entry separates the supply-chain *attack* signal (`existing` — a fn
that shipped pure at the baseline now performs the effect) from a feature (`new`) and from the
undecidable case (`unknown` — the baseline callgraph is absent OR partial: a corrupt sidecar must never
downgrade the alarm). Existence keys on the baseline callgraph because reports omit pure functions;
`gains --json` also carries `baseline_version`/`engine_version` + the §2.1 producing-build mismatch
disclosure in every engine. Alongside the rung: the corrupt-report loudness rule completed across the
comparative verbs and the MCP surface (the 0.11 rule applied engine × verb × surface), and candor-swift
gained the `gains` verb (its first). Conformance **PART 5b** pins the differential four-way, including
the partial-sidecar and no-baseline cases.

## 0.11

All code engines declare `0.11`; conformance-pinned (PARTs 4f–4k). Another **tier-2
(pinned-tool-surface)** rung, additive over 0.10 and invocation-compatible with it. The **§3.1
surprising-reach surface**: the scan-time opener (the single most surprising transitive reach — a
mundane-named function inheriting a boundary effect from hops away — with a ready-to-run `path`
command), the **`tour [<N>]`** verb (the same ranking on demand, top-N, + a pinned JSON shape), and
`path`'s human-readable default. One deterministic shared heuristic (salience × benignity × hops ×
crossing) with a **salience floor** (`Clock`/`Log`/`Rand` never surface), **module-segment test
exclusion** (never the leaf name), and the explicit "nothing hidden" fallback over a manufactured
surprise. Also ⟨0.11⟩: **found-but-corrupt loudness** — a located report yielding no trustworthy
functions fails loudly, syntactic and semantic corruption alike (a well-formed `functions: []` stays a
valid pure report); the coverage-ledger marker de-jargoned (**`classifier doesn't cover`**, was `κ
doesn't know` — a consumer grepping the old marker must update); and the plural-`packages` tour-header
label. Design: candor-rust SURFACE-BEST-FIND-DESIGN.md.

## 0.10

All code engines declare `0.10`; conformance-pinned (PART 17). Another **tier-2
(pinned-tool-surface)** rung, additive over 0.9 and invocation-compatible with it. The
**§3.3.1 canonical query grammar**: for every §3.1 query verb an engine exposes, one invocation shape in
every language — the report **discovered** from `.candor/` (walk-up, §3.4) with a `--report <locator>`
override, `--json` selecting JSON, `--policy <file>` a flag never a positional. Pre-0.10 positional forms (a
leading report, the `0|1` JSON sentinel, a positional policy) stay accepted as **deprecated aliases** with a
stderr note, removed no earlier than the next major. Conformance **PART 17** pins it four-way. Design +
per-engine impact: [CLI-GRAMMAR-DESIGN.md](CLI-GRAMMAR-DESIGN.md).

## 0.9

All code engines declare `0.9`; conformance-pinned (PART 12b/12c/12d). A **tier-2
(pinned-tool-surface)** rung, additive and wire-compatible with 0.8 (a 0.8 report and `--gate-json` verdict
are byte-identical under 0.9). It promotes the **remedial tool loop** into the pinned §3.1/§3.3 surface:
`fix`/`fix-gate` (compute the boundary hoist-refactor), `unverified` (the provable-purity disclosure), and
the gate's provable-purity **auto-disclosure** (a verdict-preserving advisory note on a `--policy` scan).
Full surface-by-surface record in [SPEC.md §8](SPEC.md#8-changelog).

## 0.8

All four code engines declare `0.8`; conformance-pinned (PART 12, the gate-verdict
differential). Additive and wire-compatible with 0.7.

- **The structured gate verdict** (§3.3) — `--gate-json` emits `{ spec, ok, violations:[{rule, fn, effects,
  detail?}] }` from the same check that sets the exit code, so a consumer can never see a verdict that
  disagrees with the gate. Powers the PR-native SARIF surface.
- **The `.candor/config` file** (§3.4, amendment) — a checked-in alternative to the `CANDOR_*` env wiring:
  shared key vocabulary, target-anchored discovery, fail-closed when configured-but-unusable, unknown keys
  warn. Relative values anchor to the config's home directory; recognized-but-unimplemented keys are
  disclosed.
- **The stale-baseline posture** (§2.1, amendment) — a baseline *guard* given a baseline from a different
  (or absent) producing build MUST fail closed without evaluating; a comparison *query* discloses and still
  answers.
- **AS-EFF-008 reconciled** to the machine-checked contract (§6) — the rule fails closed on an
  uncertifiable masked/opaque literal surface, as every engine implements and the masking + gate-verdict
  differentials pin.

## 0.7

Additive, wire-compatible with 0.6; all four engines implement it, two conformance differentials pin it.

- The canonical **`unknownWhy` vocabulary** (§4) — four kinds `reflect:`/`native:`/`dispatch:`/`callback:`,
  superseding the divergent per-engine prefixes.
- A compact **type-hierarchy sidecar** (§2.2) and the **`callers --include-unknown`** modifier (§3.1) — the
  disclosed unresolved-dispatch frontier, resolved precisely against the hierarchy.
- The **required command-line surface** (§3.3) pinned across engines.

## 0.6 and earlier

The report envelope, the effect vocabulary, the `AS-EFF-00x` diagnostics, the §6.2 policy DSL, the §3.1
query shapes (including `gains`), and the §5.1 effect manifest landed across the 0.4–0.6 rungs. See
**[SPEC.md §8](SPEC.md#8-changelog)** for the full per-rung surface list and the ⟨rung⟩ inline tags, and the
repo's git tags (`v0.4`, `v0.4.1`, `v0.5`, `v0.8`) for the contract snapshots.
