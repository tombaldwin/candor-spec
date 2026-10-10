# A per-report verdict checker compiled from the Lean model — plan

Status: revised 2026-10-09 after a review (§6 lists what changed and what was refused). **Phase 0 is BUILT as
conformance PART 97 (`gen_model_verdict.py`) and Phase 0b as PART 98 (`gen_route_equality.py`), four-way green;
Phase 1's `lean/README.md:215` and PART 23 header fixes are done. Everything else is a plan.** Written against
candor-spec `5e14689`. PAPER3 itself is not in any repo; it is cited at
`~/Library/Mobile Documents/com~apple~CloudDocs/candor-paper/PAPER3.md` (`P3:` below, by line). Its
**Definitions** — all of §6–§7 plus every Definition `lean/`, `reference/` and this plan cite, and the
P3:741-748 amendment note — are in `MODEL-DEFINITIONS.md` (Tom's ruling, 2026-10-10: definitions only),
each headed by its PAPER3 line range, so a `P3:` line inside a definition can be mapped to diffable text.
Ranges outside the definitions (Proposition 5 at P3:780-822, P3:795-805, P3:801-802) are not extracted
and remain manuscript-only. Some `P3:` ranges below are off by one against that snapshot (Definition 35
is P3:736-739 there, cited below as 735-738); the extract's own line comments are authoritative.

## 0. What this would establish, and what it cannot

**It would establish one thing: the gate verdict an engine printed follows from the facts that engine's
report states.** Given a report, its sidecar, the policy and the vocabulary config, a checker built from the
Lean model recomputes the verdict and compares.

**It cannot detect an ABSENT fact, so it cannot detect the cardinal sin.** If an engine leaves `Net` out of a
function's `inferred`, the report says the function does no networking, the engine's verdict follows from
that correctly, and the checker agrees. The record says this is where the failures have been: *"every
cardinal sin this family has fixed was an (A0)–(A3) violation, and none was an error in the inequality"*
(`lean/README.md:52`), and `thm1_holds_but_is_hollow_without_A0` proves a run can satisfy every theorem
while hiding a `Net` (`lean/README.md:59-63`). Fabrication is outside it too (`lean/README.md:93-95`).
CLAUDE.md says the same about the corpus A/B, and it applies here: an absence produces no diff.

**A fact contradicted inside one report is a WELL-FORMEDNESS finding, never a verdict disagreement.** For
example, a callee in `calls` carries `Net` while the caller's `inferred` lacks it, which breaks SPEC's
transitivity MUST (`SPEC.md:1865-1867`); or `Unknown ∈ inferred` with no `unknownWhy` and no
`Unknown`-bearing callee, which breaks (W) (`reference/policy_model.py:259-271`). The gate is forbidden to
repair either: it *"MUST NOT re-derive, widen, or re-classify anything … it reads `S` and `D` from the report
as given"* (`SPEC.md:2806-2810`). So on such a report the engine's verdict over the stated `inferred` is the
CORRECT verdict, and a checker that recomputed `S` transitively and reported a disagreement would be
accusing a conforming engine. The two outputs are kept apart: a **report lint** (this report is internally
inconsistent; the producer is at fault) and a **verdict check** (this verdict does not follow from what the
report states; the gate is at fault). The lint is worth having, but it misses the omitted edge, which is the
sin's actual shape (`Chain.Witness.deny_passes_under_drop_fires_under_union`, `lean/README.md:186-191`).

**The upside to claim: one evaluator per engine serves both routes.** Every engine calls a single policy
evaluator from `scan --policy` and from `gate --report`: rust `candor_classify::gate::gate`
(`candor-classify/src/gate.rs:299`, called from `candor-scan/src/gate.rs:117` and
`candor-query/src/gate.rs:1659`), java `Policy.gate` (`Policy.java:793`, from `Policy.java:334` and
`Query.java:4564`), ts `evaluatePolicy` (`policy.mjs:1081`, from `scan.mjs:16014` and `query.mjs:2549`),
swift `evaluateGate` (`Gate.swift:628`, from `main.swift:3056` and `GateReportCLI.swift:1078`). So a
`gate --report` differential exercises the scan route's PREDICATE too. **Measured, not inferred** (Phase 0,
calibration (1)): a one-line fault planted in ts's `evaluatePolicy` moved `scan --policy pure` over an
idiomatic callback fixture from exit 0 to 1 AND moved the report route identically, with the two
`--gate-json` documents still byte-equal. What the report route does NOT exercise is each route's own
projection into that evaluator — which is why Phase 0 has a route-equality sibling.

## 1. Premise corrections (found while reading; the plan below is built on these)

1. **PAPER3 Defs 33–35 are already amended. The executable model is what lags.** P3:726-750 redefines
   `forbid` as a call-graph rule, `allow` as a fail-closed literal certification, and the ratchet as
   grandfathering. P3:780-822 rescopes Proposition 5 to the `L`-carried verbs. Two things lag behind.
   First, `reference/policy_model.py:185-188` still implements the *pre-amendment* ratchet
   (`D ⊄ D_b`). Second, its selftest lists that ratchet as a verb (`:372-373`), so PART 23 prints
   *"every shipped verb's rejection set is upward-closed"* over a verb that was not shipped. The PART 23
   header still reads as if PAPER3 were unreconciled and as if no engine could be fed a signature.
2. **`only` (⟨0.29⟩, AS-EFF-011, `SPEC.md:5588-5592`) is in neither PAPER3 nor the model.**
3. **SEMANTICS.md §6 is stale in three places.** AS-EFF-005 is given as `I(f) \ B(f)` "never for new
   functions" (`SEMANTICS.md:195,204`). That contradicts ⟨0.40⟩ (`SPEC.md:2538-2545`) and the
   Unknown-only-advisory rule (`SPEC.md:2529-2532`). AS-EFF-008 lists four effects (`:198`) where SPEC lists
   five, including `Llm` (`SPEC.md:5576-5577`). AS-EFF-006 is written over the flat `I(f)`, with no reason
   scoping (`:196`).
4. **Reconciling the model does NOT make `allow`/`forbid`/`only` rows addable to a `gate --report`
   differential.** SPEC §3.1 *requires* that route to refuse all three with exit 2 (`SPEC.md:2847-2869`;
   `only` at `:5625-5629`; `forbid` at `:5633-5636`). **AS-EFF-005 and `unknown-ratchet` are not reachable
   through `gate --report` at all.** The baseline guard is a scan-time mode (`SPEC.md:2519`), and the ratchet
   flag is *"per-engine tested rather than conformance-differential-pinned"* (`SPEC.md:4700-4701`).
5. **P3:801-802 is wrong, and the correct statement is this.** Amended Definition 35 (P3:735-738) rejects
   iff `D_b = ∅ ∧ D ≠ ∅`. For every fixed `D_b` that predicate is **upward-closed in `D`** (for `D_b ≠ ∅` it
   is the empty set, which is upward-closed; for `D_b = ∅` it is `D ≠ ∅`). It is **anti-monotone in `D_b`**:
   growing the baseline can only remove rejections. P3's sentence *"it is not upward-closed in `D` for a
   function already disclosed at baseline"* puts the non-monotonicity on the wrong argument. Phase 1 makes
   the model say this and amends the sentence.
6. **PAPER3 Corollary 3 (P3:818-820) still cites the pre-amendment ratchet.** Its parenthetical — *"For
   `unknown-ratchet` the hypothesis is vacuous at the baseline itself, where `D_b ⊄ D_b` is false"* — is
   written against the old `Reject ⇔ D ⊄ D_b`, which amended Definition 35 no longer has. Found while
   extracting `MODEL-DEFINITIONS.md` (2026-10-10). Phase 1's PAPER3 amendment should fix it alongside item 5.

## 2. Inputs the checker needs, per verb, and whether today's wire is sufficient

The checker's contract is the one SPEC already fixes for `gate --report`. That route is *"a pure function
of the report and the policy"* (`SPEC.md:2806-2810`). Its `--gate-json` must be byte-equal to
`scan --policy`'s over the evaluated projection (`SPEC.md:2820-2829`). The closure includes the policy file's
config vocabulary (`unknown-alias`), anchored at the policy's directory (`SPEC.md:2907-2936`). So the input
set is **(report set, policy, config vocabulary) plus, for some verbs, the sidecar and the baseline**.

The projection to the model's `(S, D)` is defined by `SPEC.md:4769-4774`. `S` is `inferred` minus
`Unknown`, and `inferred` is FULL TRANSITIVE (`:1757`). `D` is the reason classes of `unknownWhy`, which is
present only when the function introduces `Unknown` **directly** (`:1776`). The *transitive* `D` is
therefore not on the entry. It needs a class fixpoint over `calls` (`SPEC.md:2872-2875`).

| verb | needs from the wire | sufficient today? |
|---|---|---|
| `deny e` | `inferred`; scope-match on `fn` (§6.2 path-segment + nested-scope rule, `SPEC.md:5946-5950`) | **Yes.** The model fires on refinement (Def 30, `Exec.lean:101`) while SPEC fires on membership (`SPEC.md:4793`). They agree only on co-emitting reports (`lean/README.md:253-265`). The checker uses SPEC's membership and flags an `Llm`-without-`Net` entry in the report lint (§0). |
| `deny e Unknown` (bare) | as above + `Unknown ∈ inferred` | **Yes** |
| `deny e Unknown[C]` | the transitive class set: `unknownWhy` → class map (`SPEC.md` §6.2 table incl. catch-all `unresolved`, ⟨0.39⟩ `macro:`), ⟨0.24⟩ CONTRIBUTES (reasonless direct ⇒ `unresolved`), `calls` for inherited classes, the `dynamic`/`*` aliases (`:5879`) and config `unknown-alias` | **Partly.** Where `calls` is absent the fixpoint is uncomputable. The engine must refuse per (rule, fn) unless the entry alone already fires (`SPEC.md:2877-2888`). The checker inherits that refusal; it is not a gap the checker can close. |
| `deny Net[dest…]` | `netClass` per entry (`:1858`), `netPartners` | **Partly.** An absent `netClass` must be refused (`SPEC.md:2869-2872`). Outside `L` (P3:803). |
| `pure` | `inferred` | **Yes.** `D` does not participate (`SPEC.md:4792`). |
| `allow E v…` (AS-EFF-008) | `hosts`/`cmds`/`paths`/`tables` + per-entry `incomplete` (`SPEC.md:1271-1288`) | **No, by ruling.** Refusal is uniform even where an engine emits the marker (`SPEC.md:2855-2864`). |
| `forbid A -> B` | every call edge, including those into pure units | **No.** `calls` is effect-relevant only (`SPEC.md:2853-2854`); the sidecar is OPTIONAL and the route may not back-fill from it (`:2806-2808`). |
| `only A -> B…` | the same, plus completeness of the reached-scope set | **No**, for the stricter reason that a green would be a completeness claim (`SPEC.md:5625-5629`) |
| AS-EFF-005 + `unknown-ratchet` | current report, baseline report, baseline sidecar, the flag, ⟨0.40⟩ prior-∅ rule (`SPEC.md:2538-2597`) | **The facts are published artifacts, but no report-only verb evaluates them.** |
| exit-2 causes | `analyzed`, `unanalyzed`, `excluded[].peeked`/`judgedElsewhere`, `outOfScope`, `scannedUnder` (`SPEC.md:1256-1600`) | **Yes for the report-borne causes** (`:1559-1560`). The peek is producer-side (`SPEC.md:43-45`). |
| `zeroMatch` | the full analysed set | **No, on the report alone** — the ⟨0.34⟩ carve-out (`SPEC.md:4160-4205`). |

**Gaps, concretely.** (a) The transitive `D` needs `calls`, which is optional. (b) The `allow` marker is
not mandatory on the wire. (c) `forbid`/`only` need a mandatory all-edges sidecar. (d) There is no
report-only route for the baseline guard. (e) `zeroMatch` needs the analysed NAME set. (e) is not a new
question for this plan: it is the zeroMatch item already on Tom's queue at
`/Users/tom/git/candor/BACKLOG.md:6926`, ruled as the ⟨0.34⟩ carve-out, whose own last paragraph names the
name set as the only real close (`SPEC.md:4196-4205`).

### 2.1 What a report-route checker can and cannot reach, against the defects actually filed

The value of a verdict checker is bounded by where the verdict-logic defects lived. Read against the
register, not against the plan's own phases:

**Reachable by a report-route checker (and what reaches each):**
- **The 2026-07-27 absence default** (`SPEC.md:5861-5866`, CONTRIBUTES): a class set defaulted to
  `unresolved` only when EMPTY, so adding a reasoned call turned a red verdict green. Reached by the ⟨0.24⟩
  repair rows run as a multi-function report with `calls` (Phase 0 arm B).
- **R448** (rust): reason classes looked up by bare `fn` in a map keyed by `hash`, so a narrowing
  `Unknown[class]` never saw its classes — a KEY-JOIN miss in the projection. Reached by Phase 0's
  route-equality sibling over a real scan-written report (hashes present), not by hand-written leaves.
- **R682** (java): the two routes read different inputs (a union merged into a real entry was gated on
  one route only). Reached only by route equality over a fixture that produces a merged entry — still OWED
  (`conformance/must-ledger.json`, the R682 entry).
- **R1028** (rust lint route): scope matching across routes disagreed on a crate-qualified scope. Reached by
  route equality with scoped rules on that route; scope matching itself is owned by `gen_policy_match.py`.
- **R154 / R525** (ts / rust): an alias line or a config `unknown-alias` parsed one way by one consumer and
  another way by the gate. Reachable only once the checker parses policy + config vocabulary (Phase 2(b)).

**Unreachable by any report-route checker, whatever is built:**
- **R208** — analysis-side (which `macro_rules!` twin the analysis saw depends on file order). The report
  is wrong; the verdict follows from it.
- **The ⟨0.30⟩ peek** — producer-side: the scan reads excluded files the gate never sees (`SPEC.md:43-45`).
- **The integrations refusal→pass class** — consumer-side: a wrapper turning an exit 2 into a pass is
  downstream of every verdict a checker could compute.

## 3. Phases, smallest first

Each phase has an acceptance criterion, stated as a property, and the evidence that would show it. Every
phase carries the CLAUDE.md control: **the instrument must be shown able to fail before its green counts.**

### Phase 0: each engine's `gate --report` verdict against the model, plus the projection

*Why it was re-aimed.* The first draft fed one function per signature, carried `D` as direct `unknownWhy`
only, emitted no `calls`, and kept rules scopeless. It would have been green on the engines of 2026-07-27:
every verdict-logic defect actually filed lived in the report→(S,D) PROJECTION — class map, key join,
transitive fixpoint over `calls`, reasonless-`Unknown` contribution, scope matching — and that draft
executed none of it. The lattice arm stays (it is the model differential and costs little); arms B and C
and the route-equality sibling are what reach the projection.

*What.* A generator in `conformance/` runs `gate --report <report> --policy <one rule> --gate-json` on each
engine and compares against `reference/policy_model.py`. Three arms:

- **A — the lattice.** One report holding one LEAF per reachable signature of the slice the Lean emitter
  emits (`lean/CandorModel/Exec.lean` `emitRows`: `|S| ≤ 2`, `|D| ≤ 2`) — 1474 signatures, **1254 reachable**
  once `Llm`-without-`Net` is removed. Every leaf has `direct` = `inferred` and a unique `fn` (two entries
  sharing a `fn` are UNIONED by every engine, which would merge two trials). `D` is carried as one canonical
  raw token per class, each a LISTED prefix of §6.2's table: `reflect:x`, `dispatch:T.m`, `callback:x`
  (class `indirect`), `native:x`, `macro:x` (class `unresolved`), `missing-config` (class `setup`).
  **Not `indirect:x`**: `indirect` is a class NAME, not a token prefix, so the raw token `indirect:x` maps to
  `unresolved` through the catch-all, and using it would manufacture divergences out of the harness.
  Policies: `pure`, `deny e` ×11, `deny e Unknown` ×11, `deny e Unknown[<all six>]` ×11, `deny e Unknown[c]`
  ×66 — **100 runs per engine**. `C = ∅` is omitted: `Unknown[]` is not a model point, and measured four-way
  it reads as all classes (unspecified, fail-closed); the model's `deny_unknown(e, ∅)` is `deny e`, already
  covered.
- **B — the projection rows.** (B1) The three ⟨0.24⟩ repair rows
  (`policy_model.repair_reproduces_the_counterexample_correctly`) as a MULTI-FUNCTION report WITH `calls`: a
  reasonless source, a reasoned source, a caller of each and of both; expected verdicts under
  `Unknown[unresolved]` and `Unknown[dispatch]` come from the model (`contribute_unresolved` + the join over
  `calls`), never written by hand. (B2) A `direct:["Unknown"]` entry with no reason, both key-absent and
  `[]`: must FIRE `deny E Unknown[unresolved]` and must NOT fire `[dispatch]`. (B3) An inherited `Unknown`
  (`direct: []`), no reason, NO `calls`: class-scoped deny is unanswerable and MUST be refused (exit 2,
  `SPEC.md:2877-2888`); bare `deny E Unknown` fires (exit 1); `deny E` exits 0.
  *Note on provenance:* candor-java's `GateReportVerbTest.java:475-480` cites the three repair rows but
  carries them as SINGLE entries (row 3 via an unrecognised token), not with `calls`; PART 27 R1 does carry
  them with `calls`, four-way, under one policy and an exit code. Arm B judges the violation SET under two
  filters against the model's fixpoint.
- **C — the class map, its own sub-row.** One leaf per raw token (`reflect:`, `dispatch:`, `ambiguous:`,
  `callback:`, `native:`, `macro:`, `missing-config`, `no-tsconfig`, `indirect:x`, an unrecognised
  `banana:x`) gated under each of the six classes; the oracle is §6.2's table read as data.

*Assertions, per run* (arm A; arm B/C where a verdict is expected): the violating `fn` SET equals the model's
REJECT set; **|violations| equals the model's REJECT count** (no duplicate rows); **exit 1 iff that count is
> 0, exit 0 otherwise, never 2 on a lattice row**. The envelope carries `analyzed: {count}` but it is not
required: measured four-way, a report with no `analyzed` key is gated normally (exit 0/1 unchanged).

*Why this sample is sufficient rather than a sample.* Every verb here is a POINTWISE predicate of one
entry's `(S, D)`. A leaf with `direct = inferred` and no `calls` gives the gate nothing to combine, so its
verdict on one function cannot depend on another function in the same report, and 1254 functions in one
report are 1254 independent trials per policy. The effect axis is covered at `|S| ≤ 2` — every effect alone
and in every pair, so "fires on the wrong effect" and "fires only when alone" are both visible — and the
class axis at every singleton plus the full set. A predicate that depends on `|S| ≥ 3` would escape; none of
SPEC §4.0's does. **Scope matching is excluded on purpose**: rules are scopeless here, and per-language
segment matching is covered by `conformance/gen_policy_match.py` (the POLICY-MATCHING differential).

*The oracle.* `reference/policy_model.py`, not the Lean emitter: the conformance job has no Lean toolchain,
and `lean.yml`'s 147,400-row differential (`lean/check.sh`) is what keeps the two transcriptions equal on
exactly this slice and more.

*Acceptance properties.*
- For every engine and every row, the engine's verdict equals the model's; a disagreement is reported with
  its `(verb, S, D)`.
- **The PART can fail, shown in the suite on every run:** (i) model-side — `Db ⊑ₑ Net` reinstated must
  DIVERGE on the `deny Net*` policies (the historical defect, `reference/README.md:55-58`); (ii) diff-side —
  one row's expected verdict flipped moves exactly one row; (iii) document — an engine's own `--gate-json`
  with one violation deleted is caught; (iv) vacuity — the report truncated to zero functions trips the
  floor. It is also registered with `conformance/probe_check.py` (`CANDOR_PROBE_FAULT`).
- **And shown once against a real engine**: a one-line fault in one engine's SHARED evaluator, built in a
  THROWAWAY worktree of that engine (never the main tree), must turn the PART red, and the record must say
  which function the fault reached.
- **`SPEC_CLAUSES` declared** for `conformance/clause_check.py`, quoting §4.0's verb table
  (`SPEC.md:4782-4787`) and the pure-function / answerability clauses (`SPEC.md:2806-2810`, `:2877-2888`).

### Phase 0b: the four-way ROUTE-EQUALITY part

*What.* Per engine, one idiomatic source fixture with a direct and an INHERITED `Unknown` of two classes,
a layer, and an inherited `Fs`; for each of ~17 policies (bare/class-scoped/`dynamic`/`*` `Unknown`, layer-
scoped `deny`, `pure`), `scan --policy P --gate-json A` and then `gate --report <the report that scan wrote>
--policy P --gate-json B`. A and B byte-equal (`SPEC.md:2820-2829`), exits equal, nothing refused. This
covers the projection layer the model differential skips: the scan route projects from memory, the report
route from the written `inferred`/`unknownWhy`/`calls`, so a dropped edge, an unserialised class, a merged
entry gated on one route only (R682, `SPEC.md:2834-2844`) or a scope matched on a different name breaks it.

*What exists already, so this is an extension and not a first.* PART 27 R6 pins byte-equality four-way over
three unscoped policies on a fixture with no `Unknown`; PARTs 54 and 72 pin it for the ⟨0.30⟩ peek and for
violation-vs-incompleteness. The OWED cell recorded against `SPEC.md:2834-2844` is narrower than "route
equality": it is the R682 MERGED-UNION fixture, four-way (`conformance/must-ledger.json`). Phase 0b does not
close that cell unless a fixture produces a merged entry.

*Acceptance.* Floors: an exit 1 and an exit 0 per engine; a class-scoped rule firing on an entry with no
direct `Unknown` (the report route's fixpoint ran); a class-scoped rule rejecting strictly fewer than bare
`Unknown`. Controls in the suite: a deleted violation reads NOT byte-equal; the scan's own report with
`calls` stripped from inherited entries (sidecar left in place) re-gates differently. It **cannot** see a
fault in the shared evaluator (both routes move together) — that is Phase 0's.

### Phase 1: reconcile the model with the shipped verbs

*What.* Make PAPER3, `policy_model.py`, SEMANTICS.md §6 and the Lean model say what SPEC says:
- replace `unknown_ratchet` with the amended Def 35 (`Reject ⇔ D_b = ∅ ∧ D ≠ ∅`), plus the ⟨0.40⟩
  absent-function prior ∅ and the Unknown-only-advisory default;
- add AS-EFF-005's effect-gain predicate (`S_c ⊄ S_b`, `Unknown` excluded) as its own verb;
- write a definition for `only`;
- fix the three SEMANTICS rows (§1 item 3);
- prove §1 item 5 (upward-closed in `D` for every fixed `D_b`, anti-monotone in `D_b`) and amend P3:801-802 (and Corollary 3's parenthetical, §1 item 6);
- **fix `lean/README.md:215`**, which says PART 23 runs the engines against `policy_model.py` — PART 23 runs
  no engine; and **fix the PART 23 header** in `conformance/run.sh`, which still says no engine can be fed a
  signature.

*Acceptance properties.* Every verb the model names is a verb SPEC §6 or §3 names, with SPEC's predicate.
Checking this means **reading SPEC's clause beside each definition**, not counting definitions. PART 23's
"shipped verb" list contains no unshipped verb. Each amended definition comes with one executed
counterexample to its old reading that all four engines pass, in the form P3:744-747 already uses.
*Cost:* small in code; the judgement is in reading.

### Phase 2: extend the Lean model to the full policy language

*What.* Three layers the model does not have today:
- **(a) A carrier beyond `L`.** Edges for `forbid`/`only`, literal surfaces plus `incomplete` for `allow`,
  `netClass` for `deny Net[dest]`, and a baseline pair for AS-EFF-005. Each gets its own monotonicity
  statement on its own carrier, or a proof that none holds. P3:795-805 lists what is unproved.
- **(b) The projection report → model.** The `unknownWhy` class map with its catch-all, the CONTRIBUTES
  rule, the transitive class fixpoint over `calls` (reusing `Chain.T`), the `dynamic`/`*`/`unknown-alias`
  expansion, and §6.2 scope matching.
- **(c) The refusal and exit-2 rules as functions of the input.** The answerability refusals, their
  minimality via Lemma 2 (`SPEC.md:2877-2899`), and the report-borne exit-2 causes.

*Be clear about which parts are proofs.* Layer (a) is where Lean adds proof. Layers (b) and (c) are
**mostly an implementation written in Lean**, checked only against SPEC prose, the same way the four
engines are. §2.1 says which filed defects (b) and (c) can reach — and which no report-route layer can — so
(b) and (c) earn their keep as a **fifth, independent implementation in a differential**, not as verified
code. Where a property *can* be stated, do it: answerability refusal is minimal, the transitive class
fixpoint is least (as `T_least` does for `S`), and alias expansion is monotone.

*Acceptance properties.* No `sorry`. Tier A and tier B axiom bars as `check.sh` sets them today. Every new
verb has a Bool twin proved equal to its `Prop` definition (`lean/README.md:273-278`). The Lean-vs-Python
differential is extended to the new verbs and seeded with a planted fault per verb that it must catch
(`lean/README.md:302-307`). *Cost:* weeks rather than days; (b) and (c) are the bulk of it.

### Phase 3: the checker binary and CI

*What.* A `lake exe` named, for example, `candor-check`. It takes `--report <locator> --policy <file>
[--config <file>] [--sidecar …] [--baseline …]` and emits a `--gate-json` document in SPEC's shape plus a
separate report-lint document (§0), then diffs the verdict against the engine's. Two routes:
- **3a, report route.** Compare against each engine's `gate --report` on the same inputs. Byte-equality
  over the evaluated projection is SPEC's own bar (`SPEC.md:2820-2829`). The `zeroMatch` carve-out is
  inherited (`:4160`).
- **3b, scan route.** For every conformance fixture and corpus row that already runs `scan --policy
  --out`, re-check the scan's verdict against the report that same scan wrote, plus its sidecar and
  baseline. That is the only route covering AS-EFF-005, `unknown-ratchet`, and `forbid`/`only` (via the
  sidecar). Where the sidecar is absent or the `incomplete` marker unpublished, the checker answers
  "unanswerable", never pass.

*CI.* The checker runs in candor-spec's `lean.yml` and in `conformance/run.sh` as a PART, four-way, over
every fixture already in the suite. It is not a per-engine-repo dependency. *Acceptance property:* on
every fixture where the checker returns a verdict, it equals each engine's verdict; a seeded wrong verdict
must fail the PART. *Cost:* about a week once Phase 2 exists.

**Could the checker become the SINGLE gate implementation?** Not decided here. *For:* the gate layer stops
drifting four ways. *Against, structural:* the scan route reads state that is not in the report (the
in-memory analysed set, the peek, every call edge for `forbid`/`only`). *Against, epistemic:* **a single
gate cannot be checked by itself** — PART 23's own header records the suite going "OK while all four were
wrong the same way". *Against, distribution:* a Lean runtime would ship inside cargo, npm, a jar and a
SwiftPM package.

### Phase 4: upkeep, and keeping a spec rung from leaving the model behind

A rung that touches §6.2 or §4 verb semantics lands as: **SPEC clause → model definition and Bool twin →
Python twin → checker → conformance rows**. Gates that stop drift:
- **Vocabulary.** PART 23 already fails when E drifts from SPEC §1, and `Effect.all_complete` makes a new
  effect a compile error. Extend both to `R`, the §6.2 class table (Phase 0 arm C reads it as data — a
  parsed copy is the next step), the `allow` effect set and the rule-kind set.
- **Verb coverage.** A clause-check style gate that fails when SPEC §6.2's rule-kind list, or §6's code
  table (`SPEC.md:5301-5313`), names a kind or code the model has no definition or explicit exclusion for.
  It must parse the list, not count it.
- **Checker vs engines.** Phase 3's PART, four-way, on every suite run.

The acceptance property: adding a rule kind to SPEC without touching the model turns the suite red. Show
this once by doing exactly that on a branch.

## 4. Public claims: what would be wrong, and a safe sentence

- **"Formally verified gate."** Only the `(S,D)` predicates and their algebra are proved. The parser,
  scope matching, report projection and refusals are unverified code written in Lean (Phase 2(b)/(c)).
- **"Machine-checked analysis" / "proved sound."** The checker never looks at code. Theorem 1 is
  conditional on (A0)–(A3), which no report can discharge.
- **"Catches silent under-reports."** It cannot (§0). Its report lint catches only an absence contradicted
  inside the same report.
- **"Covers the whole policy language."** Until Phase 3b, `allow`/`forbid`/`only`/AS-EFF-005 are refused
  or unchecked.
- **"Verified against the paper."** The paper has been wrong in the strict direction twice, and §1 item 5
  is a third. The proofs are about the model's definitions.

**Safe sentence:** *"For `deny`, `deny … Unknown[…]` and `pure` rules, each engine's gate verdict is
re-computed in CI against an executable model of candor's policy semantics that is machine-checked against
a Lean formalisation. Given the effects a report states, the verdict must match. This checks the gate, not
the analysis: it cannot see an effect a report leaves out."*

## 5. Risks and open questions

Decided by evidence, inside the phases:
- **The model itself may be wrong.** It has been wrong in the strict direction twice. Rule: the contract
  and the conformance suite outrank the model (`reference/README.md:61-66`), and every disagreement is
  triaged model-first.
- **Synthetic reports exercise a corner real producers never emit.** Arm A's "never exit 2" assertion is
  what shows the envelope is one the engines accept; Phase 0b and 3b bring real reports.
- **Reachability.** Rows where `Llm` appears without `Net` are excluded, or 220 phantom deny
  disagreements appear (`lean/README.md:253-265`).
- **The `unknownWhy` class map is per-token engine data.** Arm C pins the canonical tokens; Phase 2(b)
  needs every token each engine emits, and that list is not closed — the catch-all exists for this reason.

**For Tom — answered 2026-10-10.** *May PAPER3.md, or its §6–§7 definitions, be committed to
candor-spec?* — *"Just the defs in the spec pls."* The Definitions are now `MODEL-DEFINITIONS.md` (all of
§6–§7's, plus every earlier one cited here and in `lean/`/`reference/`); results, remarks, proofs and prose
stay local. P3:801-802 sits in Proposition 5's rescoping note, which is not extracted, so Phase 1's
amendment of it lands in the manuscript only; an amended Definition 35 would also need a re-extract. The
rest of the first draft's list is not a question for him: the single-gate idea is undecided above and has no measurement to
decide it; the wire-growth items are gaps (a)–(e), of which (e) is already on his queue
(`/Users/tom/git/candor/BACKLOG.md:6926`); and the site question waits until Phase 3a exists.

## 6. What the 2026-10-09 review changed, and what it did not

Accepted, each verified against the files before it was written in: Phase 0's added rows (arm B), leaf
shape and canonical tokens (arm A, with `indirect:x` measured four-way as `unresolved` in arm C), engine-side
calibration, the per-run exit and count assertions, the stated sample, `SPEC_CLAUSES`, the route-equality
sibling, the can/cannot-reach list, the one-question Tom list, the `lean/README.md:215` and PART 23 header
fixes, the corrected ratchet sentence, and the report-lint vs verdict split.

Corrected rather than accepted as given:
- *"`analyzed` is required"* was the first draft's claim; the review said drop it. Measured four-way: a
  report with no `analyzed` key is gated with exit 0/1 unchanged. (The `--gate-json` then prints
  `analyzed: {count: 0}` over a report that declared nothing, on all four engines — recorded as a lead, not
  a finding: the SPEC clause it would breach was not located.)
- *"candor-java GateReportVerbTest.java:475-480 carries [the repair rows] … WITH `calls`"* — it carries them
  as single entries; PART 27 R1 is the one that carries them with `calls`.
- *"Route equality recorded OWED at SPEC.md:2834-2844"* — those lines are the ⟨0.40⟩ R682 clause; the OWED
  record is the ledger's, and it names only the merged-union cell. Generic byte-equality is already pinned
  in PARTs 27 (R6), 54 and 72.
- *"gap (e) → BACKLOG.md:6926 (already Tom's queue)"* — that item was ruled by the ⟨0.34⟩ carve-out; the
  pointer stands because the carve-out itself names the name set as the remaining close.
