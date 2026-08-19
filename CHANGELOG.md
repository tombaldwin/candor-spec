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

## Unreleased

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
