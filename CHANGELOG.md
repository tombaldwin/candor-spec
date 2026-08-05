# Changelog

The **spec (contract) version** is bumped on additive changes (a minor: a new optional field, `AS-EFF`
code, or pinned tool surface) or breaking ones (a major: an envelope reshape or a removed field).
Implementations declare the version they implement via the report envelope's `spec` string. The version
moves as a **ladder**: the reference engine (candor-java) leads a new rung, it is written into
[SPEC.md](SPEC.md), then the other code engines implement it in turn and the cross-impl conformance suite
pins the floor. Each rung is **additive** over the last — an older-version consumer that ignores the newer
optional fields is unaffected.

This file is a one-line-per-rung index. The authoritative, surface-by-surface record is **[SPEC.md §8](SPEC.md#8-changelog)**
(each surface is also tagged inline with the ⟨0.8⟩/⟨0.7⟩/⟨0.6⟩ rung that introduced it); the adversarial
evidence behind the soundness posture is **[SOUNDNESS-LOG.md](SOUNDNESS-LOG.md)**.

## Unreleased

⟨0.28 PROPOSED, 2026-08-05⟩ **§3.4 — `engine [<impl>] <version>`: the engine↔baseline coupling becomes
a tool-enforced invariant.** The committed `baseline` records what one engine build saw; a newer engine
resolves more dispatch and legitimately reports more, so the AS-EFF-005 ratchet fires on functions
nobody touched — and the reflex under CI pressure is to regenerate, re-blessing whatever else moved.
The version lived in the consumer's CI configuration, decoupled from the baseline it is married to.
A mismatch now exits **2** (unevaluable, never 1 — a machine consumer must not read "I could not trust
this" as "your code broke a rule"), as does an unreadable pin: this is the one place §6.2's warn-and-skip
inverts, because skipping a PIN hands the operator a guard they believe is on. **Two answers must NOT
change the exit code** — an absent pin (opt-in by construction) and a pin a SOURCE BUILD cannot check,
which is §3.1's unanswerable-condition rule applied to configuration: disclosed, never scored, including
as satisfied. The qualified form exists because the family versions as a ladder, so a bare pin in a
polyglot repo would fail whichever engine had not yet caught up. No `CANDOR_ENGINE` env var and no
`--ignore` escape: an assertion an ambient environment can switch off is not one. candor-java enforces
it; the other four accept `engine` as a known key and disclose it as inert — a key this spec defines must
never be reported as an *unknown* one, which would tell an operator their pin was ignored while a
sibling engine enforced it.

⟨0.28 PROPOSED, 2026-08-05⟩ **§4 — a policy rule whose SCOPE matches no function is UNANSWERABLE, and
MUST be disclosed rather than scored as satisfied.** A `deny`/`forbid` naming a layer that binds nothing
was evaluated and bound nothing, so it cannot have caught anything — yet every engine scored it as
passing, which makes a one-character typo in a layer name a permanently green gate. Measured in three
engines: `deny Net orders` exits 1 on a real violation, `deny Net ordrs` exits 0 with `policy ✓`, and
`unverified` then calls the layer *"PROVABLY clean"*. The asymmetry is the tell — a typo'd **effect**
token already exits 2 naming the accepted vocabulary, while a typo'd **layer** token passes. The remedy
is disclosure, not refusal: a zero-match rule is legitimate when one policy is shared across repositories
and a layer exists in only some. candor-swift implements it; the other three now have a contract to build
against rather than three independently-invented shapes, and no conformance PART pins it yet.

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

## 0.27 — current floor (a producer declares which refinements it computes)

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
