# A per-report verdict checker compiled from the Lean model — plan

Status: PLAN, nothing built. Written 2026-10-09 against candor-spec `5e14689`. PAPER3 is not in any repo; it
is cited at `~/Library/Mobile Documents/com~apple~CloudDocs/candor-paper/PAPER3.md` (`P3:` below).

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

It can see one small slice of absence: an absence **contradicted by another fact in the same report**.
For example, a callee in `calls` that carries `Net` while the caller's `inferred` lacks it, which breaks
SPEC's transitivity MUST (`SPEC.md:1865-1867`). Another is `Unknown ∈ inferred` with no `unknownWhy` and
no `Unknown`-bearing callee, which breaks well-formedness (W) (`reference/policy_model.py:259-271`). This
is a consistency check on the report. It is worth having, but it misses the omitted edge, and that is the
sin's actual shape (`Chain.Witness.deny_passes_under_drop_fires_under_union`, `lean/README.md:186-191`).

## 1. Premise corrections (found while reading; the plan below is built on these)

1. **PAPER3 Defs 33–35 are already amended. The executable model is what lags.** P3:726-750 redefines
   `forbid` as a call-graph rule, `allow` as a fail-closed literal certification, and the ratchet as
   grandfathering. P3:780-822 rescopes Proposition 5 to the `L`-carried verbs. Two things lag behind.
   First, `reference/policy_model.py:185-188` still implements the *pre-amendment* ratchet
   (`D ⊄ D_b`). Second, its selftest lists that ratchet as a verb (`:372-373`), so PART 23 prints
   *"every shipped verb's rejection set is upward-closed"* (`conformance/run.sh:5621`) over a verb that was
   not shipped. The PART 23 header (`run.sh:5552-5557`) still reads as if PAPER3 were unreconciled.
2. **`only` (⟨0.29⟩, AS-EFF-011, `SPEC.md:5588-5592`) is in neither PAPER3 nor the model.**
3. **SEMANTICS.md §6 is stale in three places.** AS-EFF-005 is given as `I(f) \ B(f)` "never for new
   functions" (`SEMANTICS.md:195,204`). That contradicts ⟨0.40⟩ (`SPEC.md:2538-2545`) and the
   Unknown-only-advisory rule (`SPEC.md:2529-2532`). AS-EFF-008 lists four effects (`:198`) where SPEC lists
   five, including `Llm` (`SPEC.md:5576-5577`). AS-EFF-006 is written over the flat `I(f)`, with no reason
   scoping (`:196`).
4. **Reconciling the model does NOT make `allow`/`forbid`/`only` rows addable to a `gate --report`
   differential.** SPEC §3.1 *requires* that route to refuse all three with exit 2 (`SPEC.md:2847-2869`;
   `only` at `:5625-5629`; `forbid` at `:5633-5636`). The only correct engine row for them there is
   "refused". **AS-EFF-005 and `unknown-ratchet` are not reachable through `gate --report` at all.** The
   baseline guard is a scan-time mode (`SPEC.md:2519`), and the ratchet flag is *"per-engine tested rather
   than conformance-differential-pinned"* (`SPEC.md:4700-4701`). Those verbs need a different route
   (Phase 3b). The PART 23 extension covers them by refusal only.
5. **P3:801-802 may be wrong.** It says the grandfathering ratchet is "*not* upward-closed in `D` for a
   function already disclosed at baseline". For a fixed `D_b ≠ ∅` the amended rule never rejects, and the
   empty set *is* upward-closed. The non-monotonicity is in `D_b`. This is my derivation, not a
   measurement. Phase 1 must settle it by proof.

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
| `deny e` | `inferred`; scope-match on `fn` (§6.2 path-segment + nested-scope rule, `SPEC.md:5946-5950`) | **Yes.** One caveat: the model fires on refinement (Def 30, `Exec.lean:101`) while SPEC fires on membership (`SPEC.md:4793`). They agree only on co-emitting reports (`lean/README.md:253-265`). The checker must use SPEC's membership and *separately* flag an `Llm`-without-`Net` entry as ill-formed. |
| `deny e Unknown` (bare) | as above + `Unknown ∈ inferred` | **Yes** |
| `deny e Unknown[C]` | the transitive class set: `unknownWhy` → class map (`SPEC.md` §6.2 table incl. catch-all `unresolved`, ⟨0.39⟩ `macro:`), ⟨0.24⟩ CONTRIBUTES (reasonless ⇒ `unresolved`), `calls` for inherited classes, the `dynamic`/`*` aliases (`:5879`) and config `unknown-alias` | **Partly.** Where `calls` is absent the fixpoint is uncomputable. The engine must refuse per (rule, fn) unless the entry alone already fires (`SPEC.md:2877-2888`). The checker inherits that refusal; it is not a gap the checker can close. |
| `deny Net[dest…]` | `netClass` per entry (`:1858`), `netPartners` | **Partly.** An absent `netClass` must be refused (`SPEC.md:2869-2872`). This verb is outside `L` (P3:803), so the model must be extended first. |
| `pure` | `inferred` | **Yes.** `D` does not participate (`SPEC.md:4792`). |
| `allow E v…` (AS-EFF-008) | `hosts`/`cmds`/`paths`/`tables` + per-entry `incomplete` (`SPEC.md:1271-1288`) | **No, by ruling.** The marker is not guaranteed on the wire, and refusal is uniform even where an engine emits it (`SPEC.md:2855-2864`). |
| `forbid A -> B` | every call edge, including those into pure units | **No.** `calls` is effect-relevant only (`SPEC.md:2853-2854`). The §2.2 sidecar does carry pure edges (`SPEC.md:2253-2257`), but it is OPTIONAL and `gate --report` is forbidden to back-fill from it (`:2806-2808`). |
| `only A -> B…` | the same, plus completeness of the reached-scope set | **No**, for the stricter reason that a green would be a completeness claim (`SPEC.md:5625-5629`) |
| AS-EFF-005 + `unknown-ratchet` | current report, baseline report, baseline sidecar (for `origin`), the flag, ⟨0.40⟩ prior-∅ rule (`SPEC.md:2538-2597`) | **The facts are all published artifacts, but no report-only verb evaluates them.** Only the scan route does. |
| exit-2 causes | `analyzed`, `unanalyzed`, `excluded[].peeked`/`judgedElsewhere`, `outOfScope`, `scannedUnder` (`SPEC.md:1256-1600`) | **Yes for the report-borne causes** (`:1559-1560` makes `outOfScope` report-borne). The peek is producer-side and cannot be re-derived (`SPEC.md:43-45`). |
| `zeroMatch` | the full analysed set | **No, on the report alone.** Pure functions are not in `functions` (`SPEC.md:1867`), hence the ⟨0.34⟩ carve-out (`:4160-4180`). The sidecar would close it, but only by departing from `gate --report`'s output. |

**Gaps, concretely.** (a) The transitive `D` needs `calls`, which is optional. (b) The `allow` marker is
not mandatory on the wire. (c) `forbid`/`only` need a mandatory all-edges sidecar. (d) There is no
report-only route for the baseline guard. (e) `zeroMatch` needs the analysed name set. That is the open
format question at `SPEC.md:1251-1254`, and `analyzed.digest` is within-engine only (`:1256-1262`).

## 3. Phases, smallest first

Each phase has an acceptance criterion, stated as a property, and the evidence that would show it. Every
phase also carries the CLAUDE.md control: **the instrument must be shown able to fail before its green
counts.**

### Phase 0: extend PART 23 to judge engines on the `L`-carried fragment (deny, deny Unknown[C], pure)

*What.* A generator in `reference/` takes rows from the Lean/Python decision table: only rows where both
agree (`differential_lean_vs_python.py` already requires this, `lean/README.md:281-288`), restricted to
reachable signatures. It renders **one synthetic report holding one function per signature**. `D` is
carried only as *direct* `unknownWhy` tokens (one canonical raw token per class), so no class fixpoint is
needed and the `calls` refusal cannot trigger. It then runs `gate --report <it> --policy <one rule>
--gate-json -` once per (verb, effect, C) on each engine and reads the per-function verdict from
`violations[].fn` (`SPEC.md:4548`). Rules stay scopeless, which keeps the per-language scope-separator
difference out of the comparison. The envelope must carry the fields that otherwise trip an exit-2 cause:
`analyzed`, `excluded: []`, and an omitted `outOfScope`. The generator must assert the run did not refuse.
The route was already run once, ad hoc, on candor-java (1792 rows, `reference/README.md:43-61`), and never
landed in the suite. `gate --report` is four-way (`run.sh:5987`; `SPEC.md:6412-6415`).

*Acceptance properties.*
- For every engine and every emitted row, the engine's verdict equals the model's verdict. A disagreement
  is reported per row with its `(verb, S, D)`.
- **The PART can fail, shown three ways, in the suite rather than once by hand.** First, reinstate
  `Db ⊑ₑ Net` in a copy of the model: the PART must report DIVERGE on the `Db` family. That is the
  historical defect (`reference/README.md:55-58`). Second, swap one row's expected verdict: exactly that
  row must diverge. Third, run an engine on a report the generator truncated to zero functions: it must
  fail on a vacuity floor, not pass.
- **The rows reached the gate.** Per verb, the count of `violations` from each engine is non-zero wherever
  the model's REJECT count is non-zero. A green PART with zero violations everywhere is a hollow fixture.
- The reason axis covers ∅, every singleton and the full `R` for `C` (as `Exec.lean:162-163` already does),
  so a ψ that ignores `C` cannot pass.

*Not in Phase 0:* `allow`/`forbid`/`only` beyond a single "refused, exit 2" row each; `deny Net[dest]`;
the ratchet. *Cost:* a lane of roughly 1–2 days in candor-spec. Measuring it needs the four engines built
and every engine tree clean (CLAUDE.md conformance rule).

### Phase 1: reconcile the model with the shipped verbs

*What.* Make PAPER3, `policy_model.py`, SEMANTICS.md §6 and the Lean model say what SPEC says:
- replace `unknown_ratchet` with the amended Def 35, plus the ⟨0.40⟩ absent-function prior ∅ and the
  Unknown-only-advisory default;
- add AS-EFF-005's effect-gain predicate (`S_c ⊄ S_b`, `Unknown` excluded) as its own verb;
- write a definition for `only`;
- fix the three SEMANTICS rows (§1 item 3);
- resolve P3:801's claim by proof (§1 item 5).

*Acceptance properties.* Every verb the model names is a verb SPEC §6 or §3 names, with SPEC's predicate.
Checking this means **reading SPEC's clause beside each definition**, not counting definitions. PART 23's
"shipped verb" list contains no unshipped verb. Each amended definition comes with one executed
counterexample to its old reading that all four engines pass, in the form P3:744-747 already uses for the
ratchet. *Cost:* small in code. The judgement is in reading. PAPER3 is outside version control, which is a
question for Tom (§5).

### Phase 2: extend the Lean model to the full policy language

*What.* Three layers the model does not have today:
- **(a) A carrier beyond `L`.** That means edges for `forbid`/`only`, literal surfaces plus `incomplete`
  for `allow`, `netClass` for `deny Net[dest]`, and a baseline pair for AS-EFF-005. Each gets its own
  monotonicity statement on its own carrier, or a proof that none holds. P3:795-805 lists what is unproved.
- **(b) The projection report → model.** This covers the `unknownWhy` class map with its catch-all, the
  CONTRIBUTES rule, the transitive class fixpoint over `calls` (reusing `Chain.T`), the
  `dynamic`/`*`/`unknown-alias` expansion, and §6.2 scope matching.
- **(c) The refusal and exit-2 rules as functions of the input.** These are the answerability refusals,
  their minimality via Lemma 2 (`SPEC.md:2877-2899`), and the report-borne exit-2 causes.

*Be clear about which parts are proofs.* Layer (a) is where Lean adds proof. Layers (b) and (c) are
**mostly an implementation written in Lean**. Their correctness is checked only against SPEC prose, the
same way the four engines are. The measured defects in the gate layer lived in exactly (b) and (c): the
NBSP separator, typo'd effect tokens, scope matching and the absence-keyed `unresolved` default
(`SPEC.md:5471-5481`, `:2938-2945`; `reference/README.md:8-10`). So (b) and (c) earn their keep as a
**fifth, independent implementation in a differential**, not as verified code. Where a property *can* be
stated, do it: answerability refusal is minimal, the transitive class fixpoint is least (as `T_least`
does for `S`), and alias expansion is monotone.

*Acceptance properties.* No `sorry`. Tier A and tier B axiom bars as `check.sh` sets them today
(`lean/check.sh` TIER_A/TIER_B). Every new verb has a Bool twin proved equal to its `Prop` definition, as
`lean/README.md:273-278` requires. The Lean-vs-Python differential is extended to the new verbs and seeded
with a planted fault per verb that it must catch, as `lean/README.md:302-307` did for four.
*Cost:* weeks rather than days. (b) and (c) are the bulk of it.

### Phase 3: the checker binary and CI

*What.* A `lake exe` named, for example, `candor-check`. It takes `--report <locator> --policy <file>
[--config <file>] [--sidecar …] [--baseline …]` and emits a `--gate-json` document in SPEC's shape, then
diffs it against the engine's. Two routes:
- **3a, report route.** Compare against each engine's `gate --report` on the same inputs. Byte-equality
  over the evaluated projection is SPEC's own bar (`SPEC.md:2820-2829`). The `zeroMatch` carve-out is
  inherited (`:4160`).
- **3b, scan route.** For every conformance fixture and corpus row that already runs `scan --policy
  --out`, re-check the scan's verdict against the report that same scan wrote, plus its sidecar and
  baseline. That is the only route covering AS-EFF-005, `unknown-ratchet`, and `forbid`/`only` (via the
  sidecar). It also checks ⟨0.40⟩'s rule that the scan gates the entries it writes (`SPEC.md:2834-2844`).
  Where the sidecar is absent or the `incomplete` marker unpublished, the checker answers "unanswerable",
  never pass.

*CI.* The checker runs in candor-spec's `lean.yml` (today path-filtered to `lean/**` and `reference/**`,
`.github/workflows/lean.yml:28-30`) and in `conformance/run.sh` as a PART, four-way, every engine, over
every fixture already in the suite. It is not a per-engine-repo dependency. *Acceptance property:* on
every fixture where the checker returns a verdict, it equals each engine's verdict. Each engine's
disagreements are listed individually. A seeded wrong verdict, for example an engine verdict file edited
before the diff, must fail the PART. *Cost:* about a week once Phase 2 exists. Each fixture adds one Lean
process run.

**Could the checker become the SINGLE gate implementation?** This is not decided here. The trade-offs:
- *For.* The gate layer stops drifting four ways, and that is where the §6.2 grammar defects lived.
  `gate --report` already *requires* engine-independence ("one report and one policy give one verdict
  everywhere", `SPEC.md:2859-2860`).
- *Against, structural.* The scan route reads state that is not in the report: the in-memory analysed set
  (`zeroMatch`), the peek (`SPEC.md:43-45`), and every call edge for `forbid`/`only`. A report-only gate
  cannot be the scan gate unless the wire grows to carry all of that, which is gaps (b)–(e).
- *Against, epistemic.* **A single gate cannot be checked by itself.** The checker is only useful while it
  is independent of what it checks. PART 23's own header records the suite going "OK while all four were
  wrong the same way" (`run.sh:5529-5530`). One gate makes that failure total and removes the
  instrument that would see it.
- *Against, distribution.* A Lean runtime would ship inside cargo, npm, a jar and a SwiftPM package.

### Phase 4: upkeep, and keeping a spec rung from leaving the model behind

A rung that touches §6.2 or §4 verb semantics lands as follows: **SPEC clause → model definition and Bool
twin → Python twin → checker → conformance rows**. This is CLAUDE.md's "write the row before the port",
with the model as a row. Gates that stop drift:
- **Vocabulary.** PART 23 already fails when E drifts from SPEC §1 (`run.sh:5594-5609`), and
  `Effect.all_complete` makes a new effect a compile error (`lean/README.md:247-252`). Extend both to `R`,
  the §6.2 class table, the `allow` effect set and the rule-kind set.
- **Verb coverage.** A clause-check style gate that fails when SPEC §6.2's rule-kind list, or §6's code
  table (`SPEC.md:5301-5313`), names a kind or code the model has no definition or explicit exclusion for.
  It must parse the list, not count it (the lesson at `run.sh:5577-5594`).
- **Checker vs engines.** Phase 3's PART, four-way, on every suite run.

The acceptance property for this phase: adding a rule kind to SPEC without touching the model turns the
suite red. Show this once by doing exactly that on a branch.

## 4. Public claims: what would be wrong, and a safe sentence

Wording that would be false or misleading, and why:
- **"Formally verified gate" / "candor's verdicts are proved correct."** Only the `(S,D)` predicates and
  their algebra are proved. The parser, scope matching, report projection and refusals are unverified
  code written in Lean (Phase 2(b)/(c)).
- **"Machine-checked analysis" / "proved sound."** The checker never looks at code. Theorem 1 is
  conditional on (A0)–(A3) (`lean/README.md:46-53`), which no report can discharge.
- **"Catches silent under-reports."** It cannot (§0). It catches only an absence contradicted inside the
  same report.
- **"Covers the whole policy language."** Until Phase 3b, `allow`/`forbid`/`only`/AS-EFF-005 are refused
  or unchecked.
- **"Verified against the paper."** The paper has been wrong in the strict direction twice
  (`lean/README.md:220-228`). The proofs are about the model's definitions, and those definitions are only
  as right as their last reconciliation with SPEC.

**Safe sentence:** *"For `deny`, `deny … Unknown[…]` and `pure` rules, each engine's gate verdict is
re-computed in CI by an independent checker built from a Lean model of candor's policy semantics. Given
the effects a report states, the verdict must match. This checks the gate, not the analysis: it cannot
see an effect a report leaves out."*

## 5. Risks and open questions

Most of these are decided by evidence, inside the phases:
- **The model itself may be wrong.** It has been wrong in the strict direction twice. Rule: the contract
  and the conformance suite outrank the model (`reference/README.md:61-66`), and every Phase 0
  disagreement is triaged model-first.
- **Synthetic reports exercise a corner real producers never emit.** The generator's envelope must be one
  the engines accept as well-formed, and Phase 0's "did not refuse" assertion is what shows that. Real
  corpus reports enter at Phase 3b.
- **Reachability.** Rows where `Llm` appears without `Net` must be excluded, or 220 phantom deny
  disagreements appear (`lean/README.md:253-265`).
- **The `unknownWhy` class map is per-token engine data.** Canonical tokens are sufficient for Phase 0.
  Phase 2(b) needs every token each engine emits, and that list is not closed: the catch-all exists for
  this reason.

**Genuinely Tom's:**
1. **Should PAPER3 move into version control?** It lives in iCloud, outside any repo. Phase 1 amends it,
   and every model citation points at a file nobody can diff.
2. **Single-gate implementation (Phase 3):** a product and distribution decision. The trade-offs are
   above, and none of them is a measurement.
3. **Whether the wire should grow** to close gaps (a)–(e): mandatory `calls` and `incomplete`, a
   mandatory all-edges sidecar, the analysed name set. Each is a spec rung with its own cost. Without
   them the checker stays fragment-only on the report route.
4. **Whether the site should mention any of this before Phase 3a is green four-way.**
