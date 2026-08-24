# The candor specification

A candor *implementation* analyzes a codebase in one language and reports, per function, the set of
side effects it performs. This document defines what every implementation must produce, so that a
report is interchangeable across languages — for an AI agent, a human, or a CI gate.

## Contents

- [The family, named precisely](#the-family-named-precisely) · [Versioning policy](#versioning-policy)
- [1. Effects](#1-effects)
- [2. The report](#2-the-report) — [2.1 Provenance](#21-provenance-the-candor-header) · [2.2 The sidecars](#22-the-call-graph-sidecar)
- [3. Modes](#3-modes) — [3.1 Read-only queries](#31-read-only-queries-should) · [3.2 Pre-edit and structural tools](#32-pre-edit-and-structural-tools-should) · [3.3 The command-line surface](#33-the-command-line-surface-required) · [3.4 The configuration file](#34-the-configuration-file--candorconfig-should)
- [4. The trust contract](#4-the-trust-contract--the-core-of-candor) — [4.0 The disclosure model `(S, D)`](#40-the-disclosure-model-formally--a-signature-is-a-pair-s-d)
- [5. Capabilities](#5-capabilities-conformance) — [5.1 The effect manifest](#51-the-effect-manifest--declared-effects-for-an-opaque-dependency-05)
- [6. Diagnostics](#6-diagnostics-as-eff-00x) — [6.1 Containment](#61-containment--the-architecture-quality-signal-deliberately-not-a-score) · [6.2 The policy DSL](#62-the-policy-dsl-normative)
- [7. Conformance checklist](#7-conformance-checklist-for-an-implementation)
- [8. Changelog](#8-changelog)
- [Appendix — Implementing 0.8: the checklist](#appendix--implementing-08-the-checklist)

**Version 0.31** — all code engines declare `0.31`; the floor is conformance-pinned. How versions
move (the ladder, the floor, who may lead a rung) is stated once, in **[Versioning policy](#versioning-policy)**
below. The ⟨0.23⟩/⟨0.22⟩/⟨0.21⟩/⟨0.20⟩/⟨0.19⟩/⟨0.12⟩/⟨0.11⟩/⟨0.10⟩/⟨0.9⟩/⟨0.8⟩ markers through this document tag each surface with the rung that
introduced it; the [changelog](#8-changelog) lists every rung's contents. Each rung through ⟨0.29⟩ is additive over the last,
so an older-version consumer that ignores the newer optional fields is unaffected. **⟨0.30⟩ is the first
exception and is deliberately not additive**: it adds no field and removes none, but it changes what a gate
DOES with an existing one, and a tree that passed under ⟨0.29⟩ can exit 2 under ⟨0.30⟩. An upgrade is
therefore a decision, not a drop-in — see the changelog entry for what flips and what provably does not.
**⟨0.31⟩ is additive in one half and not in the other, and the halves are independent.** `netPartners`
(§2, §3.1) is a new optional key: absent unless an ambient `net-partner` declaration actually moved a
classification, so a consumer that ignores it is unaffected. The fourth exit-2 cause (§3.3, an
UNEVALUABLE TARGET) is not additive for the same reason ⟨0.30⟩ is not: a target that exists and holds no
file the engine can read was a clean pass on one engine and is a refusal on every engine now, so a
green that came from a typo'd path becomes an exit 2. That is the direction the change exists to fix,
and it is still a verdict that moves.
**⟨0.32⟩ IS NOT ADDITIVE EITHER, and its non-additivity reaches further than ⟨0.30⟩'s.** `judgedElsewhere`
(§2) is a new optional field, but the clause beside it changes what a gate DOES with `excluded`, a key
MANDATORY since ⟨0.29⟩: an entry with `peeked: false` and no `judgedElsewhere: true` now suppresses `ok`
and exits 2 under any policy holding a deny rule. So a ⟨0.29⟩-era report written with NO policy over a
tree that has exclusions — a build script, a tests directory, a jar under the root — was a clean pass and
is a refusal now, on the `gate --report` route in particular. **The upgrade note is the remedy: SCAN WITH
THE POLICY.** A report produced under the same deny set carries `peeked: true` (or names what it found in
`outOfScope`), and the refusal turns back into a definite answer; re-gating the old report cannot, because
the peek is a producer-side act and no consumer can re-derive it from a document. A pipeline that scans
once with no policy and gates the artifact later is the shape that flips, and it is the shape ⟨0.32⟩ exists
to stop certifying. **0.23 is a tier-1 additive
rung — cross-package interface dispatch** (§2, `WORKSPACE-CHAINING-DESIGN.md`): the optional `interfaceUnion`
report entry — a synthetic `pkg#Iface.method` union over a package's local implementers, emitted (gated behind
`CANDOR_WORKSPACE_CHAIN`) so a CHAINED consumer's cross-package interface/protocol/trait dispatch resolves to
the impl's effect instead of reading pure — plus the `--workspace`/`--deps` auto-discovery convention.
Four-way conformance-pinned (PART 18: candor-java + candor-scan + candor-ts + candor-swift). Because it is
gated, a default report is byte-identical and a 0.22 consumer is unaffected. **0.22 is a tier-2 rung — the
`verify` oracle**: candor's dynamic honesty check — `observed(f) ⊆ inferred(f) ∪ {Unknown}` per executed function —
shipped per-engine as `candor verify` with mechanism-independent capture arms and a fail-closed exit-2 verdict
when runtime attribution is incomplete; per-engine, not conformance-differential. The report and verdict schema
are unchanged from 0.21, so a 0.21 consumer is unaffected. **0.21 is a tier-1 additive
rung — the completeness manifest** (§2 + §3.3.1): the envelope carries **`analyzed: {count, digest}`** and
**`unanalyzed: [{path, reason}]`** so a consumer distinguishes *provably-pure* (analyzed, omitted) from
*never-seen*, and incompleteness is **machine-legible** — a configured gate over source that failed to parse
now fails closed (exit 2) with an `{ok:false, incomplete:true, unanalyzed}` verdict instead of a stderr-only
warning a JSON consumer couldn't see. Additive: a pre-0.21 consumer ignoring the fields is unaffected. **0.20
is an additive rung**: it adds the **`Net` destination-class** (§2/§6.2) — a per-function **`netClass`** field
(`known-telemetry`/`known-partner`/`unknown-host`) and a **`deny Net[unknown-host]`** security gate (egress
only to known destinations; fail-closed on a masked/runtime host) — plus a reason-class **query surface**
(`blindspots --stats`/`--class`, `unverified --class`, §3.1). A pre-0.20 report/policy is unaffected (the
field + bracket syntax are additive). **0.19 is a tool-surface
rung** (no report-schema change): it adds **reason-scoped `Unknown` policies** (§6.2) — `deny E Unknown[class…]`
narrows the `Unknown` part of a deny to a fixed reason-class vocabulary {reflect,dispatch,indirect,native,unresolved,setup}
(with the `dynamic`/`*` aliases and config `unknown-alias` names); bare `deny E Unknown` is unchanged
(`Unknown[*]`, soundness-by-default), the reason class propagates transitively like the effect, and an
AS-EFF-006 `Unknown` verdict carries a **`reasonClass`** field (§3.3) — so a pre-0.19 policy/consumer is
unaffected. **0.18 is a pinned-tool-surface
rung** (no report-schema or verdict change): it pins the **`--strict` advisory-verb CI gate** (§3.3.1) — `fix-gate`,
`gains`, and `unverified` are advisory (exit 0) and `--strict` makes each a CI gate (exit 1 while a finding
remains); a typo'd or not-applicable flag (notably `--policy` on `gains`) is an exit-2 error, never a silent
swallow; and the surface/`tour` **mostly-Unknown disclosure** — never a bare "nothing hidden" (nor a
`tour --json` `{"reaches":[]}`) over a graph whose Unknowns are the hidden part. **0.13 adds the `Llm` effect** (§1) — a machine-learning model-provider call, a boundary effect refining `Net`; a tier-1 additive vocabulary rung (a consumer already tolerates unknown effect names, so a pre-0.13 report/policy is unaffected). It also adds the `extensions` envelope field (§2) for engine spec extensions (the candor-swift `privacy/1` sensor cluster). **0.12 was a
pinned-tool-surface rung**: it adds no report-schema or verdict change (a 0.11 report and a 0.11 gate verdict
are byte-identical under 0.12), but promotes the §3.1 `gains` **`origin`** field — the supply-chain
existing-fn/new-fn/unknown split, keyed on the baseline callgraph, with the partial-graph rule and the
§2.1 provenance fields — into the pinned surfaces (conformance PART 5b pins it four-way). The prior rung
**0.11** promoted the surprising-reach surface (the scan opener, `tour`, `path`'s human default), the
found-but-corrupt loudness rule, and the de-jargoned coverage-ledger marker (PARTs 4f–4k); **0.10** promoted
the §3.3.1 canonical query grammar — report discovery with a `--report` override, `--json` selection,
`--policy` as a flag — into the pinned §3.3 surface, so a conformant engine drives every exposed query
verb the same way (additive and deprecated-alias-compatible, so a 0.9 invocation still runs; PART 17
pins the grammar four-way); **0.9** promoted the remedial tool surface (`fix`/`fix-gate`, `unverified`,
the gate's provable-purity auto-disclosure) into §3.1/§3.3. See the [tier note](#conformance-tiers) for
why a tier-2 promotion is a contract bump and not merely a patch.

The **spec/contract version** — the report schema, the effect vocabulary, the `AS-EFF` codes, and the
**pinned tool surfaces** (the §3.1 query shapes, the §3.3 command-line surface, the §6.2 policy grammar) —
that a conformant implementation declares it implements (the envelope's `spec`). It is
distinct from an engine's *build id* (a git hash, §2.1) and from its *release semver*. An engine's
release **major.minor tracks the spec it implements** — `candor-java 0.9.x` declares spec `0.9`, a sibling
still on the previous floor declares `0.8` — with
the patch floating per-engine. A candor implementation's **internal library crates** (e.g. the Rust repo's
`candor-report` schema types and `candor-classify` policy/classifier) MAY keep an independent semver, but
where they publish to a public registry alongside the engines they SHOULD align to the toolchain version, so
a registry visitor doesn't read a just-updated internal crate as lagging — they carry no external-consumer
contract to protect. (The candor-rust crates align to the spec minor as of 0.9.)

### Conformance tiers

The contract has two tiers, and they carry different stakes — the distinction is what decides whether a
change is a spec bump or a patch:

- **Tier 1 — the interop floor.** The report envelope and schema, the effect vocabulary, the `Unknown`
  trust marker, and the gate **verdict** (`--gate-json` `ok` + the `{rule, fn, effects}` set and the exit
  code). An engine that diverges here produces output another engine or a consumer **cannot trust** —
  a report that means something different, a verdict that disagrees. Cross-engine agreement on tier 1 is
  what "the gate means the same thing in every language" rests on.
- **Tier 2 — the pinned tool surfaces.** The §3.1 query shapes, the §3.3 command-line surface, and the
  §3.3.1 query grammar — `whatif`, `fix`/`fix-gate`, `unverified`, `rewire`, `--agents`, the advisory gate
  disclosures, and the uniform way a query is invoked (report discovery, `--report`, `--json`). An engine
  missing or diverging on a tier-2 surface is **non-conformant to the rung**, but its reports and verdicts
  are still trustworthy — a consumer just can't reach for that tool there.

Both tiers are part of the `spec` a conformant engine declares, and both are conformance-pinned. The
version rule follows from the tiers: a **tier-1 breaking** change bumps the major and moves lockstep;
a **tier-1 additive** change (a new optional field/code) or a **tier-2 addition promoted to required**
bumps the minor — the floor ratchets and every engine implements it. A patch changes neither tier's
contract (a bug fix, an internal refactor, prose). **0.9 is exactly a tier-2 promotion**: the remedial
surface (`fix`/`fix-gate`, `unverified`, the auto-disclosure) moves from shipped-but-not-required into the
pinned §3.1/§3.3 surface, with tier 1 untouched — so a 0.8 report/verdict is byte-identical under 0.9.
The conformance suite tags each PART with the tier it pins.

## The family, named precisely

This document uses four terms for the implementations, and every other candor document follows them:

- **The reference engine** is **candor-java** — the ladder-leading engine: a new minor rung is
  implemented there first, written into this document, and declared by candor-java ahead of the rest.
- **candor-rust** is the Rust repo, which ships two backends: the deep Rust engine (the nightly dylint
  lint, the §7 *sound engine* profile) and the stable syntactic floor, **candor-scan** (the §7
  *disclosed syntactic floor* profile).
- **The four code engines** are the conformance-pinned set — candor-java, candor-scan, candor-ts,
  candor-swift — the engines whose shared floor the cross-impl conformance suite proves.
- **candor-agents** is the **domain engine** (§4): its units are agents, not functions; it rides the
  ladder on its own schedule and never holds the code-engine floor back.

## Versioning policy

The spec version is a *cross-engine* contract, but it is a **version ladder, not a
lockstep stamp**. Two guarantees, kept distinct:

- **The floor is conformance-pinned.** Every conformant engine implements a common *floor* version
  **identically**, proven by the conformance differential — that cross-language identity is the project's
  defining guarantee (a per-language tool cannot offer it). The floor is the highest version *every* engine
  implements — where "every engine" means the **four code engines the cross-impl conformance suite
  pins** (candor-java, candor-scan, candor-ts, candor-swift). A **domain engine** (§4 — e.g. the
  agent-fleet engine) rides the ladder on its own schedule and declares its own `spec`; it does not hold
  the code-engine floor back, and a floor claim never speaks for it.
- **The version each engine declares is disclosed, not assumed.** An engine emits in every report the exact
  spec version it implements (the envelope's `spec`, §2.1), which MAY be **ahead of the floor**. A consumer
  reads that field rather than assuming uniformity — candor's own disclose-don't-paper-over discipline (§4)
  applied to its own versioning.

Because minor bumps are **additive-only**, engines at different rungs never *conflict*: a newer feature is a
new optional query/field, so an older-version engine simply lacks it (disclosed via `spec`), never
contradicts it. That is what makes a leading reference safe, and it splits the policy by change kind:

- **Minor (additive) bump → the reference MAY lead.** A new optional field/query/artifact, a refinement
  that narrows an upper bound, or an **obligation tightening** (a SHOULD→MUST, a field made required on
  producers — the 0.4/0.6 precedent): none of these can put two rungs in conflict — an engine on the older
  rung simply doesn't yet meet the new obligation, and says so via `spec`. The **reference engine
  (candor-java)** implements it, it is written into this
  document, and candor-java declares the new minor **ahead of** the other engines (release
  `major.minor` tracks the spec, as above), while a sibling
  still on the floor stays fully interoperable there. The other engines raise to the new version as
  they implement it; **the floor rises when the last one lands**, and the conformance differential pins the
  new feature across the engines that declare it (its cross-engine agreement is proven incrementally, not
  gated on all four at once). A capability MAY additionally incubate as an *unspecced* experimental engine
  feature before it is written into the spec (e.g. `callers --include-unknown` ran in candor-java `0.5.43`
  before it was specced into `0.7`).
- **Major (breaking) bump → lockstep.** A breaking change (the envelope reshape, a removed/retyped field)
  is a **major** bump and moves **all engines together**: a consumer of the prior line could break, so it
  needs coordinated migration and is never shipped by one engine alone. This is where "everyone moves at
  once" earns its cost.
- A genuinely **language-specific** capability (e.g. JVM/Spring-only semantics) stays an engine feature, or
  at most an explicitly-optional engine-specific section — it does **not** advance the shared ladder.
- **Engine SPEC EXTENSIONS (2026-07-14).** An **ecosystem-specific surface** — one whose sources exist in
  a single engine's world (e.g. iOS privacy-sensor effects) — MAY be led by the **motivated engine** rather
  than the reference, as a **spec extension**: a standalone contract document living in that engine's repo
  (`SPEC-EXTENSION-<name>.md`), written spec-first with the same rigor as this document (vocabulary,
  classification sources, disclosure posture, fabrication fences). Extension effects ride the normal §2
  forward-compatibility rule (a consumer tolerates unknown effect names), and the report envelope SHOULD
  disclose active extensions (`"extensions": ["<name>/<version>"]`) so a consumer can tell an extension
  effect from a typo. An extension can later be **promoted into this document** as a shared rung (when a
  second engine implements it, or by decision) — its text moves here, the ⟨rung⟩ marker records the
  promotion, and the conformance suite picks it up; or it can be **adopted by another engine** directly
  (both implement the same extension doc; the extension's own text is then their differential's oracle).
  An extension never holds the shared floor back and a floor claim never speaks for it — the same posture
  as a domain engine's schedule.

So `spec 0.8` released on candor-java while the other engines are still at `0.7` does **not** fork the
contract: `0.7` remains a complete, frozen floor every engine still meets, and `0.8` is the next rung —
reached first by the reference, additively — so nothing a `0.7` consumer relies on changes. The envelope's
`spec` is the exact, per-report statement of which rung produced it. The spec repo **tags `vX.Y` when the
floor rises** to X.Y (the rung's release point); while a rung is reference-led the header names the rung
and the released floor separately, untagged.

See the [changelog](#8-changelog) for what each version added. An implementation MUST emit the spec
version it conforms to in every report (the envelope's `spec`, §2/§2.1) and SHOULD expose it as a
constant. The report is wrapped in a self-describing `{ candor, functions }` envelope (§2); the legacy
v0.1 bare array is still accepted by conformant readers during migration.

> This document fixes the **interface** an implementation must produce. For the **analysis** behind
> it — the effect lattice, call-site resolution rules, the transitive fixpoint, cross-crate
> composition, and the soundness/precision properties — see [SEMANTICS.md](SEMANTICS.md).

## 1. Effects

An **effect** is an observable interaction with the world outside pure computation. The shared
vocabulary:

| Effect | Meaning |
|---|---|
| `Net` | network I/O — sockets, HTTP clients, cloud-SDK request dispatch |
| `Llm` | a call to a machine-learning MODEL provider — the outbound request a model SDK or a known model host dispatches ⟨0.13⟩ |
| `Fs` | filesystem read/write |
| `Db` | database query execution |
| `Exec` | spawning / controlling a subprocess |
| `Env` | reading environment variables / the process environment |
| `Clock` | reading wall-clock or monotonic time |
| `Ipc` | local inter-process communication (e.g. Unix-domain sockets) |
| `Log` | logging / tracing |
| `Rand` | randomness / entropy |
| `Clipboard` | system clipboard access |
| `Unknown` | a call the implementation **could not resolve** — see §4 |

An implementation MAY add language-specific effects, but SHOULD use these names where they apply.
`Unknown` is mandatory and special — a **visibility marker**, not a declarable effect: where this document
says "a §1 effect name" (the §5.1 manifest, §6.1 containment, a policy `deny` set), it means **every effect
in the table above, excluding `Unknown`** — stated that way ⟨0.24⟩ because it previously said "the ten",
which went stale when `Llm` was added at ⟨0.13⟩ and left §5.1's manifest-voiding MUST answering differently
depending on whether you counted or read. Never `Unknown` (which `deny Unknown` addresses explicitly, §6.2).

Plain **console writes** (`println!`, `System.out.println`, bare stdout/stderr) are deliberately **not**
classified — not as `Log`, not as `Fs`. Classifying them would flood every CLI tool's report (printing
*is* a CLI's purpose, the way `Db` is a database app's — the §6.1 argument), drowning the signal. `Log`
is for calls into a logging/tracing *framework*, whose presence is an architectural fact. The four code
engines agree on this; an implementation that does classify console output MUST use a
language-specific effect name, not `Log`.

**`Llm`** ⟨0.13⟩ refines `Net`: a call whose SINK is a machine-learning model
provider (a chat/completion/embedding/moderation request) is `Llm`, not bare `Net` — the question
"which functions in this code (or in a dependency) talk to a model provider" is a distinct
supply-chain surface (whatever reaches the prompt leaves the process; the response is an
injection ingress; it is a cost/latency boundary). Two classification sources, mirroring the existing
machinery:
(a) a **model-SDK surface** — the provider clients each ecosystem curates (OpenAI / Anthropic /
Google-GenAI / AWS Bedrock / Mistral / Cohere / Ollama and the LangChain invoke surfaces); and
(b) a **host-literal refinement** — a statically-known request to a recognized model host
(`api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com`, `*.bedrock*.amazonaws.com`,
a local `…:11434` Ollama endpoint) classifies `Llm` exactly as a jdbc URL classifies `Db`. An UNKNOWN
host, or an SDK the engine's curated list does not cover, stays bare `Net` (or `Unknown`) — never
guessed, and the coverage ledger (§7) discloses an uncovered provider package like any other.
`Llm` is a **boundary effect** (§6.1) and scores high in the §3.1 surprising-reach salience set.
Embeddings and moderation calls count (one effect, no sub-taxonomy); a LOCAL model endpoint counts too
(the host literal discloses localhost — the question is "does this consult a model", not "does it pay a
provider"). As a §1 vocabulary addition it is tier-1 ADDITIVE: a consumer already tolerates unknown
effect names (§2 forward-compatibility), and a pre-⟨0.13⟩ policy simply never names `Llm`. Both sources
are pinned four-way by conformance: **PART 4m** the host-literal refinement (with fabrication guards — an
S3 bucket named "bedrock", a remote host on `:11434` stay bare `Net`) and **PART 4o** the per-ecosystem
model-SDK surface (a curated client call is `Llm+Net`; a plain non-model `Net` call in the same module
stays bare `Net` — the surface never bleeds).

⟨0.32⟩ **`Exec` charges reach to the subprocess capability, not only the launch.** Constructing or
configuring an invocation (`Command::new`, `new ProcessBuilder(…)`, `Process()`, and their argument/env/
redirect setters) is `Exec`, exactly as launching (`spawn`/`start`/`run`) and controlling a live child
(`waitFor`, `kill`, its stdio streams) are. An invocation object carries its own payload — program, argv,
environment — and travels fully armed, so splitting build from launch across functions or crates MUST NOT
make the builder invisible: the assembled argv is precisely what `cmds` reports, and a dependency that
grows invocation-assembly is a supply-chain fact. This is specific to invocation objects; option-builders
for other effects (`OpenOptions`, request builders) stay pure because their resource arrives at the
terminal verb, which is charged at its own call site. Pure read-backs of stored state (`get_program`,
`exitValue`, …) are carved out as named denylists; an engine MUST NOT instead enumerate launch verbs — an
allowlist whose omissions under-report silently. Pinned four-way by **PART 66**, whose over-charge control
holds the boundary: a read-back-only function, and a project-local type that merely shares the name, gain
nothing. (MEASURED on candor-java, the lone engine that enumerated launch verbs: a method returning
`new ProcessBuilder(argv)` for caller-supplied `argv` reported no effects at all and passed `deny Exec`
with exit 0.)

## 2. The report

An implementation emits, per compilation unit, a self-describing **envelope**: a provenance header
plus one entry per analyzed **unit**. ⟨0.5⟩ A *unit* (named an **effector** in the domain model,
[MODEL.md](MODEL.md)) is the smallest body the engine attributes effects to. For a code engine that is
a function or method (and throughout this document "function" means "unit"). But the family's units are
wider than functions, and each kind earned its place by hiding effects when it was NOT a unit: a computed **accessor** body (a Swift getter
performing I/O read silently pure until accessors became units), a static/class **initializer**
(`<clinit>` runs at class load, no call site in sight), a CJS **export** surface (a dist bundle's
module boundary), and an agent-fleet's **agents**, **session** root and **hooks** (commands a
harness runs automatically). The entry's name field stays `fn` for wire compatibility. Write
one file per package, named so multiple reports don't collide (the Rust impl uses
`<prefix>.<crate>.<type>.json`):

```json
{
  "candor":    { "version": "<engine build id>", "toolchain": "<channel>", "spec":    "0.31" },
  "resolves":  ["fs", "incomplete"],                             // §2.1 ⟨0.27⟩ optional refinements this producer computes
  "functions": [ /* the entries below */ ]
}
```

The `candor` header records which engine produced the report (§2.1). A bare top-level array (no
envelope) remains accepted as the legacy **v0.1** form; readers MUST accept both during migration.

**One report covers ONE package** (crate / npm package / JVM module / SwiftPM package / fleet). An
engine MUST NOT fold several packages' functions into one `functions` array: function names are
only unique *within* a package (every binary crate has a `main`), and a consumer keys the report's
`calls` edges and the sidecar by name, so merged packages collide those names and cross-wire the
inferred sets. (Found live: a repo-root scan that folded 194 fixture packages into one report
produced one `main` entry with 194 functions' unioned effects.) A multi-package project emits a
**report set**: one report per package under a shared `--out` prefix. A consumer SHOULD treat all
reports under one prefix as a single analysis world, and MUST join *across* reports by `hash`,
never by bare `fn` (names may legitimately repeat across packages).

The envelope SHOULD also name the package the report covers, as `"package": "<name>"` (or
`"packages": ["<name>", …]` where one compilation unit genuinely spans several, the JVM shape), so
a consumer (and the §2 chaining coverage rule) can tell what an **empty** report covers without
parsing entry hashes.

**Cross-package interface dispatch** (design: `WORKSPACE-CHAINING-DESIGN.md`, prototype in candor-ts 0.22).
A call on a value typed as an interface/protocol *imported from a chained package* resolves to the interface
method signature, which has no body — so the chain join can miss it. An engine MAY expose the
implementation-union as a synthetic `interfaceUnion: true` report entry (`hash: pkg#Iface.method`, effects =
the union over local implementers), so the consumer's existing chain lookup resolves; and MAY auto-discover
workspace deps with `--workspace`/`--deps`. Gated/opt-in until a floor rung pins it. NB the *silent-pure*
form of this miss was candor-ts-specific; the other engines already fall to a disclosed `Unknown` here. When the field is absent, coverage is derivable from the entries' `hash`
prefixes (`pkg#…`), which an all-pure empty report does not have; emit the field.

**The factory-bound receiver — `typeSurface`** ⟨0.23⟩ (design: `DEP-RECEIVER-TYPING-DESIGN.md`; produced and
consumed by candor-scan, optional for every engine). `let c = dep::build(); c.fetch()` types `c` from
`build`'s RETURN type — and a pure `build` is **absent from the dependency's report entirely** (§2 rule 3),
so no consumer can recover it from the entries. An engine MAY publish a top-level

    "typeSurface": { "returns": { "<pkg>#<fn qual>": "<pkg>#<type qual>", … } }

whose keys and values are **fully qualified in the producing package's own namespace — the same namespace
the entry hashes use**, so a consumer forms `<pkg>#<type qual>::<method>` and asks the ordinary chained
lookup. Qualification is not a naming nicety: a leaf-keyed surface makes `sync::Client` and `mock::Client`
one string, and a PURE `mock_client()` then charges `sync::Client`'s effects to a caller that cannot reach
them. Three rules, each from a defect that shipped and was reverted:

- the producer publishes a **plain nominal** return only. A `Result<Conn,E>`/`Option<Conn>`/`Vec<Conn>`
  return MUST NOT publish `Conn`: the binding holds the WRAPPER, and keying its `map`/`unwrap`/`is_ok`
  against the payload charges effects nobody runs. Refusing is the safe direction;
- **a miss falls back to the disclosure of the unformed key, never to silence** (the three-row rule — a
  lookup that finds nothing is only a purity claim when the key names something that could have had a
  body). This holds for a miss on `returns` AND for a miss on the entry lookup that follows a `returns`
  hit, because a chained index legitimately WITHDRAWS keys it cannot disambiguate;
- the join applies **every** surface the ordinary chained join applies (`hosts`/`cmds`/`paths`/`tables`/
  `invisible`/`incomplete`), not just the effects — a join that carries the effect and drops `incomplete`
  lets a benign literal in the consumer certify what the dependency declared uncertifiable.

An empty surface omits the field, so a report with nothing to say is **byte-identical** to a pre-rung one
and a 0.22 consumer is unaffected. `typeSurface.implements` was designed alongside `returns` and dropped:
the `interfaceUnion` entry above already carries the implementer set it would have published.

**Spec extensions** ⟨0.13⟩. An engine that classifies effects from a **spec extension** (§"Versioning
policy" — an ecosystem-specific effect surface led by the motivated engine, e.g. the candor-swift
`privacy/1` Apple-sensor cluster) MUST disclose the active extensions in the envelope as
`"extensions": ["<name>/<version>", …]`, a top-level array of `name/version` strings — omitted when no
extension effect is active (so a plain report is byte-unchanged). This lets a consumer tell an extension
effect name from a typo and know the surface was computed; the effect names themselves ride the
forward-compatibility rule below (a consumer tolerates them like any unknown effect). An extension's own
contract document (in the leading engine's repo, `SPEC-EXTENSION-<name>.md`) fixes its vocabulary and
classification; it MAY later be promoted into this document as a shared rung.

⟨0.15⟩ **The `coverage` envelope field** — the κ-coverage ledger (§7 item 14) as data, so "what the
scan couldn't see" travels WITH the report instead of evaporating on stderr:
`"coverage": { "uncovered": [ { "name": "<package>", "calls": <n> }, … ] }` — one entry per uncovered
external package/module this code demonstrably calls (language-natural names, the same list and counts
as the stderr disclosure), **omitted entirely when nothing is uncovered** (a fully-covered scan's
report is byte-identical to a pre-⟨0.15⟩ one). Motivation (SOUNDNESS-LOG 2026-07-15): a report that
reads as total lets a downstream verb answer with false confidence — a `privacy-manifest` "ok" over an
app whose sensor usage lives in an uncovered framework module, a `gains` "no gains" over an uncovered
dep. A report-consuming verb whose verdict could change under uncovered reach MUST re-disclose this
field in its own output (verdict-preserving — the ⟨0.9⟩ gate auto-disclosure precedent; §3.1/§3.3):
the verdict/exit does not change, the caveat travels. Closing the gap remains chaining's job (§2
CANDOR_DEPS); `coverage` is how an unclosed gap stays visible.

⟨0.28⟩ **AND THE SAME MUST CARRIES THE ⟨0.21⟩ MANIFEST, WHICH IS THE STRONGER CAVEAT AND THE ONE THAT DOES
NOT TRAVEL.** The rule above is stated over `coverage`, and it is implemented: measured, `gains` over a
baseline carrying `coverage.uncovered` emits `coverageDelta` naming the uncovered dependency. **The same
verb, on the same report, in the same output, drops `unanalyzed` entirely.** So the mechanism exists and
works; it was pointed at the weaker of the two caveats. `coverage.uncovered` says *I could not see into
this dependency*; `unanalyzed` says *I could not read this file of your own code*, and `analyzed.count: 0`
says *I judged nothing at all*.

So: **a report-consuming verb MUST re-disclose a non-empty `unanalyzed`, and an `analyzed.count` of 0, on
the same terms** — verdict-preserving, exit unchanged, the caveat travels.

**AND THE SCOPE IS ANSWERS, NOT ONLY VERDICTS — the wording above is narrower than its own argument.** It
binds a verb "whose VERDICT could change", and the two cases it reasons from are a `privacy-manifest` "ok"
and a `gains` "no gains": both are ANSWERS THAT READ AS ALL-CLEARS, which is the property that makes the
disclosure load-bearing. The descriptive verbs produce the same shape and are not covered by the wording:
over a report declaring `unanalyzed`, measured, `show` answers `[]`, `where Fs` answers
`{"directly":[],"inherited":[]}`, `map` answers `{}` and `blindspots` answers `{"totalUnknown":0}` — that
last one reporting *no blind spots* out of a report whose own manifest names a file it could not read.
None carries a hedge. A consumer cannot distinguish *nobody performs Fs* from *nothing was examined*.

The obligation therefore binds **any verb whose output could be read as a negative finding about the
code** — a verdict, an empty result set, a zero count. A verb that genuinely cannot be misread this way
(`--version`, `parsepolicy` over a policy file, a verb reporting only on its own arguments) is unaffected.

*This is the third time in this document a rule has been stated over the instance it was found in rather
than the condition that makes it true — see §3.3.1's two ⟨0.24⟩ corrections. The tell is the same each
time: the clause's own justification is broader than the clause. `coverage` was the field in front of the
author, and `verdict` was the verb in front of the author.*

⟨0.28⟩ **AND HERE IS WHAT THE TRAVELLING CAVEAT IS CALLED — because the clause above shipped without
saying, and four engines guessed.** §3.3.1's ⟨0.24⟩ general rule requires a field entering a
machine-consumed document to have its name and shape pinned *in the rung that introduces it*, on the
stated ground that a MUST saying "disclose X" without saying what X is called "is not a requirement, it is
four independent guesses with a conformance failure scheduled". The re-disclosure MUST above was written
in the same rung, in this document, and pinned nothing. Measured outcome, inside one day:

    rust    judgedNothing: [ "<report path>", … ]        java   judgedNothing: [ "<report path>", … ]
    swift   judgedNothing: [ "<report path>", … ]        ts     judgedNothing: true

and on `gains`, which rests on two reports, **three answers**: rust and swift emitted `baselineIncomplete`
alone, java added `baselineJudgedNothing` as an array, ts added it as a boolean. A consumer written
against the majority (`doc.judgedNothing.length`) throws on ts; one written against ts (`=== true`)
silently misses the other three. Both java and ts had green unit tests asserting their own side of it.
The cost fell hardest on the engine that was most careful: candor-swift *withheld* the key, reasoning in a
comment that "a key one engine emits and another does not is a divergence a consumer sees" — correct, and
defeated because its premise (the reference does not emit it) was already stale by the time it was written.

So the caveat's wire form is pinned here, and it is ONE key set whatever verb carries it:

    "incomplete":    true                                        // the flag EITHER cause raises
    "unanalyzed":    [ { "path": "<file>", "reason": "<why>" } ] // files the scan could not READ
    "judgedNothing": [ "<report path>", … ]                      // reports declaring `analyzed.count: 0`

`incomplete` is the one key a consumer may branch on alone and be safe under both causes; the other two
name WHICH, because the two want different repairs — `unanalyzed` wants a scan that can read a file,
`judgedNothing` wants a scan that reached a conclusion. **`judgedNothing` is an ARRAY, not a boolean**: a
verb reading a prefix answers over many sibling reports, and *which* of them judged nothing is the whole
of the actionable content. Each key is **omitted when it does not apply**, so a verb's output over an
intact report stays byte-identical to its pre-⟨0.28⟩ form — the property every engine measured for this
rung and the one it must not spend.

**A verb resting on TWO reports discloses both sides separately, `baseline`-prefixed** —
`baselineIncomplete`, `baselineUnanalyzed`, `baselineJudgedNothing`, `baselineNoManifest`, same shapes. Not one merged flag: the
sides fail in opposite directions and want different responses. An incomplete CURRENT means the answer may
be SHORT — effects the reader is not being told about. An incomplete BASELINE means the comparison floor
is soft, so the existing-vs-new split the verb exists for is unreliable. "Something here is incomplete"
leaves a supply-chain reviewer unable to act on either. This mirrors the `coverage`/`coverageDelta` shape
already in use rather than minting a second convention.

**The channel is the machine document itself** — the same document the answer is in, not stderr beside it.
That is the whole of the clause: the human channel was already fine in every engine measured, and a caveat
on the other stream is one `2>/dev/null` from gone. Where a verb's pinned output shape has nowhere to put
a key — `show` emits a top-level ARRAY, `map` keys its object by the user's own module names, so a
reserved key there collides with a real symbol — that shape needs its own ruling before the obligation can
be met, and until it has one those two are **known-open cells, not silently non-compliant ones**.

⟨0.28⟩ **AND HERE IS THAT RULING, AND IT IS ONE RULE, NOT ONE PER VERB.** The two cells above were opened
separately and would have been closed separately — a shape decision for `show`, another for `map`, a third
for `privacy-manifest` — which is how this document has come to correct "a rule stated over the instance in
front of the author" five times. They are one question: *what does a verb emit when it cannot support the
document it is supposed to emit?*

⟨0.28⟩ has already answered that, one level down, for `unanswerable`: **the hedge REPLACES the result set,
it does not accompany one**, because a consumer reading `direct` beside a hedge is still told nobody calls
the function. The same reasoning applies to the document as a whole, so the rule generalises rather than
being invented:

> **A verb whose pinned shape cannot carry the caveat MUST emit the CAVEAT DOCUMENT INSTEAD of its result
> document.** Not a result document with the caveat omitted, and not an empty result of the pinned shape.

    show      healthy → [ … ]            hedging → { "incomplete": true, "unanalyzed": […] }
    map       healthy → { "<mod>": … }   hedging → { "incomplete": true, "judgedNothing": […] }

Three properties make this the right shape rather than merely a shape:

- **Healthy output is untouched.** The document changes only on the path that is currently answering
  falsely. Every engine measured byte-identity for this rung and none of it is spent.
- **The type change is LOUD, and that is the point.** A consumer doing `for (const x of doc)` over `show`
  gets a TypeError, not a silent zero-iteration loop. Today `show` answers `[]` over a report whose own
  manifest names a file it could not read — *nothing performs this effect*, asserted about code nobody
  examined. Trading a silent wrong answer for a noisy stop is this document's standing preference, and it
  is the one case where breaking a consumer is the CORRECT outcome: the consumer was being lied to.
- **It needs no reserved-key convention**, which matters because §2.2's `@`-prefix precedent DOES NOT
  TRANSFER here. That convention is safe for the sidecar because a `@`-prefixed key cannot collide with a
  TYPE name. `map` is keyed by MODULE names, and an npm scoped package is spelled `@scope/name` — so
  `@incomplete` is a key a real ts module could own. A convention that is airtight in one namespace and
  merely unlikely in another is not a convention; it is a deferred collision.

⟨0.28⟩ **AND `privacy-manifest`'s OWN TWO KEYS, PINNED HERE BECAUSE DRIVING THE VERB IS WHAT FOUND THEM.**
The verb's document is `{ "reached": [ … ], "required": { … } }` — `reached` the privacy-relevant surfaces
this scan actually reached, `required` the manifest entries they imply, keyed by the platform's own
declaration name. Both were emitted and named nowhere; conformance PART 42 could not see them because it
did not DRIVE the verb, and it did not drive the verb because only one engine ships it. Coverage bounded
by what an instrument runs is the same finding as the missing row-3 fixture two clauses up, arriving from
the verb axis instead of the state axis. `required` is keyed by USER-FACING declaration names, so it is a
namespace and not vocabulary — a reserved key may not be added beside its entries.

**`privacy-manifest` is the same MUST and NOT the same shape problem** — it has an envelope and simply
never consults completeness, so a "no sensors reached" ships over a partial report. It carries the pinned
keys in its envelope like any other verb. Recorded here because it was filed alongside the other two and is
a different defect: *has nowhere to put the caveat* and *never looks for it* need different fixes, and
grouping them by symptom is how one gets the other's remedy.

⟨0.28⟩ **AND AN ADVISORY VERB OVER A ZERO-RULE POLICY ANSWERS THE SAME WAY.** §6.2 makes a configured
policy that yields no rules an exit-2 refusal for the GATE, on the ground that `ok: true` is a claim about
the code that no such run is entitled to make. `whatif`, `fix-gate` and `unverified` share that loader and
were not touched by the rung. They are ADVISORY — they set no verdict, so `ok: true` is not the exposure
and the gate's refusal posture is the wrong import.

What they DO produce is an answer *relative to a policy*, and relative to no rules that answer is not a
finding, it is an absence of questions. So they take the rule above: **the caveat document, and the result
keys withheld** — `unverified` does not emit an empty `unverified` list over a policy that asked nothing,
for the same reason ⟨0.27⟩'s refusal document must not carry `violations`. The exit is UNCHANGED; this is
a disclosure, per ⟨0.24⟩'s standing ruling that count-0 reaches both disclosure channels and stops at the
exit code.

⟨0.28⟩ **AND HERE IS WHAT THAT CAVEAT DOCUMENT CONTAINS — because the paragraph above said "the caveat
document" and never said what is in it.** That is the ⟨0.24⟩ general rule ("a MUST that says 'disclose X'
without saying what X is called is four independent guesses") broken by the clause written to enforce it,
in the same rung, for the second time. Caught by candor-rust, which implemented it, noticed the gap, chose
the conservative reading and flagged it rather than minting a name.

No new key: the document carries **`unevaluated`** with a single entry naming the whole policy, in the
exact spelling §3.1 already pins for the gate's own zero-rule refusal. The gate and the advisory verbs then
say the same thing about the same policy in the same words, which is the property that makes a
cross-engine consumer possible at all.

⟨0.28⟩ **AND THE LIST OF ADVISORY VERBS IS ILLUSTRATIVE, NOT CLOSED — `fix` takes this too.** The clause
names `whatif`, `fix-gate` and `unverified` because those were the three in front of the author. `fix`
shares the same policy loader and its answer is equally policy-relative: over a configured policy that
yielded no rules it emits `{"crossing": false, "reason": "not-forbidden"}` at exit 0, and *not-forbidden*
by a policy that forbids nothing is vacuously true — an all-clear produced by deleting the question.
candor-rust extended the rule to it and flagged the extension; candor-swift read the list as closed and did
not; **the divergence was created by the clause, not by either engine.**

So: every verb that answers relative to a CONFIGURED policy takes this rule. Composed with the `crossing`
ruling below, `fix` over a zero-rule policy emits **no `crossing` key** — that key is present exactly when
the verb answered, and here it did not. A policy that is not configured at all remains the honest way to
say "I am not gating" (§6.2) and is untouched.

⟨0.28⟩ **AND A HEDGING DOCUMENT WITHDRAWS `ok` — with one carve-out that is already ruled.** Measured:
candor-swift's `privacy-manifest --verify` emits `ok: true` beside `incomplete: true`. A consumer keying on
`ok` — which is what `ok` is FOR — reads a determined all-clear out of a document that is simultaneously
saying it could not see everything. That is ⟨0.27⟩'s `violations` problem under a different key.

**The carve-out is the GATE VERDICT, and it is not an exception so much as a different question.** ⟨0.24⟩
ruled explicitly that a judged-nothing report leaves the verdict and exit UNCHANGED — *and it still does;
⟨0.31⟩'s unevaluable-target cause supersedes that ruling only for the SCAN route's own target, never for a
report presented to a verb or chained as a dependency, which is the shape this passage is about* — and candor-rust's own
note gives the reason: *"this report makes no claim, and inventing one for it would be the opposite
defect."* The gate's `ok` is scoped to *did a rule I could evaluate fire* — a question a partial report can
still answer — and `unevaluated` / `zeroMatch` / `ignored` carry what it could not evaluate. An advisory
verb's `ok` is scoped to *is this code clean in the sense I check*, which a partial input cannot support.

So the rule is stated over the scope, not the verb: **`ok` is withdrawn wherever it is a claim about the
CODE that the hedged input cannot support, and kept where a clause has scoped it to the rules actually
evaluated.** Written this way because the tempting form — "a hedging document never carries `ok`" — is
false, and would have reopened the ⟨0.24⟩ count-0 ruling from the other side.

⟨0.21⟩ **The completeness manifest — `analyzed` + `unanalyzed`** (COMPLETENESS-MANIFEST-DESIGN.md). The
report **omits pure functions** (§2 lists only effectful/`Unknown` units), so the consuming convention is
"absent ⇒ pure." Two envelope fields make that convention *backed* rather than a universal claim the report
can't support — distinguishing **provably-pure** (analyzed, no effects) from **never-seen** (a unit the scan
never judged, the cardinal-sin drop), and making incompleteness **machine-legible**:

⟨0.24⟩ **`analyzed.count == 0` IS "I JUDGED NOTHING", AND A CONSUMER MUST NOT READ IT AS FULL COVERAGE.**
A chained report carrying `functions: []` and `analyzed.count: 0` currently buys a consumer **MORE
confidence than not chaining the package at all** — the caller drops out of `functions`, which under ⟨0.21⟩
is a **positive purity claim**, with **no advisory anywhere**. Measured on all four engines by conformance
PART 26, and strictly more confident than the unchained arm, which correctly discloses `invisible` +
`coverage.uncovered`.

**State the harm precisely, because the loose form is misleading.** The empty report carries no effects, so
the count-0 arm cannot itself *trip* a gate; both it and the unchained arm exit 0 on `deny Fs`. **What the
count-0 arm deletes is the DISCLOSURE** — the `invisible` marker, `coverage.uncovered`, the verdict caveat
and `--gate-json`'s `coverage.packages`, which is the machine-consumer channel. The gate flip appears only
against the *trusted* arm (a real report would have said `Fs`, exit 1). So this is a silent under-report in
its purest form: not a wrong answer, but a **confident** one where the honest answer was a hedge — and it is
the disclosure channel, not the verdict, that a fix must restore.

**The wire ALREADY distinguishes the two cases and no engine reads it.** A `pub use`-only facade package
emits `count: 0`; an all-pure two-function package emits `count: 2` with the same empty `functions`. So:

| `analyzed.count` | `functions` | what it means | what a consumer MUST do |
|---|---|---|---|
| `0` | `[]` | **nothing was judged** | treat the package as **NOT COVERED** — the κ ledger records it `invisible`, exactly as if unchained. It MUST NOT license a purity claim for any unit in it. |
| `n > 0` | `[]` | **n units judged, all pure** | believe it (§2 rule 3). This is a legitimate all-pure claim and MUST NOT be hedged. |
| absent | `[]` | pre-⟨0.21⟩ producer | fall back to the unchained reading — no manifest, no claim. |

⟨0.28⟩ **AND THE THIRD ROW IS NOT THE FIRST ROW — measured, two engines report it as one.** Over
`{"candor":{…},"functions":[]}` with no `analyzed` key at all, candor-java's note says the report *"declares
`analyzed.count: 0`"* and candor-rust lists it under `judgedNothing`. **The report declares nothing.** The
hedge is the right DIRECTION — row 3's own instruction is *no manifest, no claim* — but the disclosure is
false, and this document rates a false disclosure worse than a missing one (§3.4's `net-partner` finding:
an engine reported "ignoring unknown config key" *while honouring it*).

It is also a hole in ⟨0.28⟩'s own pin, which defines `judgedNothing` as *reports declaring
`analyzed.count: 0`* — a row-3 report is not one, so putting it there makes the key mean two things and
loses the distinction the three-row table exists to draw. The repairs differ: row 1 wants a scan that
reaches a conclusion, row 3 wants a producer that emits a manifest at all.

So row 3 gets its own name, pinned here in the rung that introduces it:

    "noManifest": [ "<report path>", … ]   // consulted reports carrying no `analyzed` key

It raises `incomplete` like the others and is omitted when empty, and it takes the `baseline`-prefixed
form on a two-report verb like every other member of the set — `baselineNoManifest`.

*Pinned in the same breath as `noManifest` itself because the alternative was measured: all four engines
derived the prefixed form MECHANICALLY from the one key set the moment `noManifest` existed, so it was
emitted four-way and named nowhere within minutes of the rung landing. That is `judgedNothing`'s opening
condition exactly, and it survived PART 42's vocabulary gate — not through a hole in the check but because
the gate's corpus carries no row-3 artifact state, so it could not provoke the key it would have caught.
An instrument's FIXTURES are part of its coverage, and a new artifact state has to reach them.* Note candor-rust's GATE note already
says "`analyzed.count` is 0, **or absent with no entries**" — naming both conditions honestly on that one
route while the query route asserts the wrong one, which is how a message drifts from what the code checks.

The second row is the control that makes the first meaningful: a fix that hedges *both* has not implemented
the rule, it has disabled the feature. Conformance PART 26 prints `CONTROL SEPARATION`, and a correct
implementation makes the two arms **diverge** where today all four print INDISTINGUISHABLE.

⟨0.24⟩ **`count` MUST BE A NON-NEGATIVE INTEGER; anything else is UNREADABLE and fails closed.** A review
found four engines reading a fractional `0.5` three different ways (covered / hedged / covered) and a
`2.5` two ways — all in the safe direction, but an unpinned disagreement on **the exact integer this whole
rung keys on**. A non-integral, negative, non-numeric or otherwise unparseable `count` is a manifest that
made no readable claim: treat it exactly as `present-but-unreadable` and withhold coverage.
**A BOOLEAN IS NOT AN INTEGER, and this one was live.** candor-swift read `analyzed: {count: true}` as
`1` — Foundation bridges `NSNumber(bool:)` through an `as? Int` cast — and therefore as *judged*, granting
full coverage byte-identically to `count: 2`. The caller then dropped out of `functions`: **a ⟨0.21⟩
positive purity claim licensed by a manifest that made no readable claim at all.** That is the
fabrication mirror this rung exists to close, arriving through a language's type bridge rather than a
logic error, and it contradicted that engine's own documented row. An implementation MUST reject a boolean
before the integer cast, and its shape-table test MUST carry a boolean row — three engines fail closed here
only because their JSON readers are stricter, not because anyone tested it.

⟨0.24⟩ **THE GENERAL RULE THESE TWO ARE INSTANCES OF: A KEY THAT IS PRESENT BUT UNPARSEABLE IS CORRUPT
INPUT, AND MUST NEVER BE COERCED TO ITS EMPTY VALUE.** `count: true` and a missing `functions` are the two
that were caught by hand; the shape that generalises them is *a reader that recovers from a type mismatch
by substituting the default*. That default is always the permissive value — `0`, `[]`, absent — so the
coercion converts corrupt input into a claim, and on every one of these keys the claim is the safe-looking
one. Measured, the sharpest case is `unanalyzed`:

- `unanalyzed: [{"unit":…,"why":…}]` — right shape, wrong field names, exactly what a hand-built or
  foreign-produced report yields. candor-rust ran it through `from_value(u).ok().unwrap_or_default()` and
  got `[]`. **`unanalyzed` non-emptiness IS the fail-closed trigger**, so dropping it turns exit 2 into
  `policy ✓`. The other three refused.
- `unanalyzed: ["src/broken.rs"]` — a bare string list. **All four dropped it and exited 0.**

So: on `analyzed`, `unanalyzed`, `functions`, and every §2 key a verdict reads, an implementation MUST
distinguish ABSENT from PRESENT-BUT-UNPARSEABLE. Absent may take a documented default. Present-but-
unparseable is a refusal — exit 2, naming the key. `unwrap_or_default`, `?? []`, `optional(...).orElse(…)`
and their siblings are the exact idiom to grep for, and finding one on a §2 key is a defect until proven
otherwise: **the language's convenience default is the fail-open direction on every key in this format.**

⟨0.24⟩ **A report with NO `functions` KEY is MALFORMED, and MUST be refused LOUDLY — not believed, not
silently dropped.** `functions` is §2-required. The same review found a four-way split on
`{"package":"p","analyzed":{"count":5}}`: rust and java `continue` past it before the judged-nothing
predicate — **no coverage and no advisory of any kind, the user's chained file discarded in total
silence** — while swift and ts default it to `[]`, see `count > 0`, and **grant a purity licence from a
malformed report.** Both are wrong in different directions. The safe direction is rust's and java's, but
silence is not a disclosure: withholding coverage without saying so is the same failure the rest of this
rung is about. Refuse it the way §3.3 refuses a corrupt report, and name the file.

**KEY THE RULE ON THE INTEGER, NEVER ON THE EMPTINESS OF `functions` — and here is the number.** Measured
over 1997 deduplicated JVM dependency jars: **79 (4.0%) emit `count: 0`**, of which only **6** actually
granted coverage — all annotation/marker-only artifacts with no methods. But **104 (5.2%) are the
LEGITIMATE all-pure kind**, every one carrying packages. **A fix keyed on emptiness would have withdrawn
104 real claims to catch 6.** That ratio is why the second row of the table is a control and not a
footnote: the plausible-but-wrong fix is *more* destructive than the defect. Cross-checked on a Rust chained
tree (69 dep reports): 5 `count: 0`, all genuine facade or platform-stub crates.

**Two structural traps for an implementer**, both found the same way. **Coverage is anchored TWICE** — the
envelope's `packages` key, and each entry's `hash` prefix for reports carrying no `packages` — so *"gating
one is a no-op wearing a fix's clothes."* And the CHAINED set (which only ever adds disclosure) must stay
**ungated**; only the COVERED set takes the new conjunct.

**Row 3 retires a pre-⟨0.21⟩ affordance, and that is deliberate.** A manifest-less empty report previously
DID buy coverage — one engine had a test pinning exactly that. Under this rule it no longer does, because a
producer that emits no manifest gives a consumer nothing to distinguish "judged nothing" from "judged and
found nothing", and the unchained reading is the only honest one. An engine carrying such a pin should
re-point it at a manifest-bearing fixture rather than delete it.

⟨0.24⟩ **THE SAME RULE BINDS `gate --report` (§3.1) — AS A DISCLOSURE, NOT AS AN EXIT CODE.** A report
presented *directly* to the gate with `analyzed.count: 0` makes the same claim as a chained one and must be
read the same way: it has judged nothing, so it licenses no purity claim and **the verb MUST SAY SO**. The
obligation is on the reading, not on the route the report arrived by.

**The exit code and the verdict document are UNCHANGED.** ⟨0.24⟩ *This clause first read "MUST say so
rather than reporting 'no violations, exit 0'", which forbade exit 0 — and that contradicted §3.1's own
byte-equality MUST, because a scan of an empty facade package exits 0 with a clean verdict, so the gate
route must too. Two engines then implemented the two halves of my contradiction: one refused with exit 2
and no verdict document (breaking byte-equality on ~7–10% of real dependency reports, measured), the other
added a stderr caveat and left the verdict alone. **The second is right, and it is what §2 already said
about this defect: the harm is the DELETED DISCLOSURE, not the verdict — restoring a verdict would assert
an effect the consumer has no evidence for.** Corrected here rather than in the engines.*

So: an advisory naming the package, on the channel a corrupt report already uses. Exit code untouched,
`--gate-json` byte-equal to `scan --policy`. Refusing with exit 2 is **not** an available reading — §3.3
enumerates the exit-2 causes (a broken gate CONFIG; an INCOMPLETE analysis of the target's own code; ⟨0.30⟩
an INCOMPLETE SCOPE; ⟨0.31⟩ an UNEVALUABLE TARGET, which is about the WALK and so cannot arise on a route
that is handed a report) and a judged-nothing DEPENDENCY is none of them, so an engine that refuses here has
minted a cause of its own and **split the verb**. *The argument is that the cause must be ENUMERATED, not
that the list has a particular length: ⟨0.30⟩ added one deliberately, in §3.3, with a row exercising it —
which is the difference between minting a cause and an engine inventing one.*

⟨0.24⟩ **THE CONFLICT CASE — a package chained TWICE, once judged and once not.** A `count: 0` report makes
**no claim**, so it neither adds nor subtracts: the judged report's coverage **stands**. That is the rule,
and it follows directly from what row 1 means — "I judged nothing" is silence, not a denial.

Note it runs OPPOSITE to the ⟨0.21⟩ `incomplete` reconciliation, and deliberately: an `incomplete` report
makes a **negative claim about its own source**, so it beats a complete sibling; a `count: 0` report makes
none, so it loses to one. Two reconciliations, opposite directions, each following what the second report
*says*.

**One engine diverges here on purpose and the reason generalises.** candor-rust keeps the HEDGE on conflict
rather than the coverage, because its dependency index **drops a key two entries disagree under** (the
never-guess rule) — so granting coverage on the judged report's authority can leave the consumer reading
*confidently pure* on the very key nobody answered. That is a correct local compensation for a collision
behaviour that is **itself scheduled to be replaced by the union** (`ENTRY-COLLISION-DECISION.md`), and it
should be revisited when that lands: with a union there is no dropped key, so the compensation stops being
needed and the divergence should close. Recorded rather than reconciled away, because an engine that
deviates from a rule for a stated, measured reason is doing something different from one that deviates by
accident — and the difference is only visible if the reason is written down.

**Note what this does NOT fix.** It separates *judged nothing* from *judged and found nothing*. It does not
separate *judged n and dropped one* from *judged n−1* — that needs the per-unit analysed NAME SET, which
§3.1's `gate --report` clause records as the open format question. This rule is the half the wire can
already carry.

- `"analyzed": { "count": <n>, "digest": "<hex>" }` — the ANALYZED UNIVERSE: `count` = the units candor
  formed an effect judgment for (effectful + pure) = the §2.2 call-graph node set (pure leaves included). So a
  consumer reading the **bare envelope** computes the pure count = `analyzed.count − |functions|` and reads a
  unit's membership: in `functions` ⇒ effectful/`Unknown`; a §2.2 node not in `functions` ⇒ **provably pure**;
  in **neither** ⇒ **never analyzed** (candor makes no purity claim). `digest` is an opaque, **within-engine**-
  stable fingerprint of the sorted analyzed-qual set (a same-input re-scan agrees; compare same-engine only —
  qualifiers differ across engines). Present whenever the engine can enumerate its analyzed set.
- ⟨0.31⟩ `"netPartners": { "config": "<path>", "hosts": [ "<host>", … ] }` — ENVELOPE-level, beside
  `analyzed`: **the ambient `net-partner` declaration that MOVED a `netClass`** — the config file that
  declared it, and the declared hosts that actually PARTICIPATED in this scan. Anchored at the TARGET, not
  at the policy file; §3.1 sets out the two anchors and why they cannot share a key. **Omitted when
  empty**, so a project declaring no partners — or declaring some that never matched — is byte-identical
  to a pre-rung report. Recorded by the PRODUCER because a report-reading consumer cannot compute it: it
  has no target to anchor at, and re-classifying these hosts through its OWN config would make the verdict
  depend on the reader's working directory.
- ⟨0.29⟩ `"incomplete": [ "<Effect>", … ]` — **the effects whose LOCATOR this unit could not determine**:
  its own `Fs` write whose path is a parameter, its own exec whose command is computed, its own `Db` call
  whose table is built at runtime. **Omitted when empty**, so a scan that determined everything is
  byte-identical to a pre-rung report.
  **A PRODUCER THAT COMPUTES THIS FACT MUST PUBLISH IT**, and this clause states the CONDITION rather than
  any one use of it — because for a long time the document stated only the use. §2's chained-join rule
  named `incomplete` among the surfaces a join must carry, and nothing said a producer had to emit it, so
  two engines computed it internally and published nothing: the join had nothing to carry and the rule
  about the join was vacuous for half the family.
  **The harm is a FALSE ALL-CLEAR on a configured gate, measured across the scan boundary.** An absent
  `paths` is overloaded between *"reaches no path"* and *"reaches a path I could not see"*, and this field
  is the only thing separating them. A dependency whose `Fs` path is a runtime value published nothing to
  say so; a consumer that ALSO wrote one allowed literal joined `paths: ["/tmp/lit"]` with no marker, and
  `allow Fs /tmp/lit` answered **`policy ✓`** where the engines that publish the field charge AS-EFF-008
  on identical code. The same shape holds for `Exec` and `Db`; `Net` was already covered, because
  ⟨0.20⟩ gave it a wire form of its own (`netClass ∋ unknown-host`) and the other three effects had none.
  A consumer MUST read the pair: a literal surface is a complete account of what a unit reaches only when
  `incomplete` does not name that effect.
- `"unanalyzed": [ { "path": "<file>", "reason": "<why>" } ]` — the TARGET's own source candor could NOT
  analyze (a file that failed to read/parse; a skipped unparseable class). Its units are absent NOT because
  pure but because never seen — disclosed on stderr today but INVISIBLE to a machine reading the JSON, so a
  bare report *looked* complete. **Omitted entirely when empty** (a complete scan is byte-identical to a
  pre-⟨0.21⟩ report). Distinct from `coverage` (an unmodeled *dependency*): `unanalyzed` is the target's own
  unseen source. A truly-isolated pure unit (uncalled, calling nothing) MUST still be a §2.2 call-graph node
  (empty adjacency), so its membership reads *analyzed-pure*, never *never-seen*.
- ⟨0.29⟩ `"excluded": [ { "class": "<token>", "count": <n>, "peeked": <bool>, "reason": "<why>" } ]` — **THE
  SCOPE: the files this scan chose not to OPEN.** A different claim from `unanalyzed`, which names files it
  opened and could not read, and one no report could previously make at all: `analyzed.count` is a
  NUMERATOR whose denominator — the engine's file selector — is invisible, so a consumer cannot tell the two
  apart. **Absence of a file from the report licenses a purity claim about that file only if the report says
  the file was CONSIDERED** — the ⟨0.21⟩/⟨0.24⟩ three-row rule applied one level out. **`excluded` MUST be
  emitted whenever the engine can enumerate its own file selection, `[]` INCLUDED**: an empty list is the
  positive statement *I looked and excluded nothing*, and under ⟨0.26⟩ an ABSENT key means *this producer
  cannot answer*, which is a different claim. That is the opposite rule from `coverage`/`unanalyzed` above,
  deliberately: for a LEDGER, empty and absent can mean the same thing; for a SCOPE they cannot.
  **CLASSES WITH COUNTS, NEVER FILE LISTS** — an excluded set can contain a build tree, which is unbounded,
  and a gate that routinely prints thousands of paths is one people learn to scroll past. `reason` is what a
  consumer reads to decide whether the exclusion matches the question they are asking, so it MUST say why
  the class exists, in the engine's own terms; a conformance row asserts its VALUE, not the key's presence.
  `class` tokens are ENGINE-CHOSEN and are NOT interchange vocabulary: the selectors differ per language
  (`build-script`, `harness-target`, `source-without-class`), and a shared enumeration would force one
  engine to file its exclusion under another's name.
- ⟨0.29⟩ `"outOfScope": [ { "fn": …, "path": …, "effects": ["<Effect>"…], "class": …, "reason": … } ]` —
  **THE PEEK: an effect found in a file the gate did NOT judge.** ⟨0.29⟩ ruled that **an out-of-scope
  finding MUST NOT move the verdict** — the exit code had to be what it would have been without it, because
  a file the gate declined to judge must not decide an exit code. ⟨0.30⟩ **REVERSES that**: see the ⟨0.30⟩
  clause below. It remains its own kind: never a member of `violations`, never a member of `functions`.
  **Emitted only when a policy is CONFIGURED and HONOURED, and only for effects that policy
  DENIES** — that bound is what keeps the block from becoming the noise it would otherwise be, because the
  floor is then "things you have already said you care about" rather than "everything you excluded". With no
  policy the key is ABSENT: nothing was asked, so `[]` would be a claim. Over a policy the engine REFUSES,
  the key is ABSENT for the reason §3.1 withholds `ok` — the peek is a producer reading the policy, and it
  may not certify relative to a gate that evaluated nothing. **Present-and-empty is asked-and-clear, and it
  is a claim about the classes `excluded` marks `peeked: true` AND NO OTHERS.** That is what makes `peeked`
  load-bearing rather than descriptive: an engine that cannot read one of its own excluded classes —
  candor-java reads BYTECODE, so an uncompiled `.java` is unreadable to its peek — would otherwise publish
  `[]` over files nobody opened, which is the ⟨0.26⟩ partial-manifest failure exactly.
- ⟨0.29⟩ **`peeked: true` MUST mean every file of that class was READ on this run**, not that the class is
  one the engine is willing to peek. A file the peek OPENED and could not read — a parse failure, an
  archive whose members will not load — withdraws the claim, because `outOfScope: []` beside `peeked: true`
  is the sentence *there is nothing in those files* and an unread file cannot support it. Since the peek
  runs the engine's ordinary path (clause above), it produces its own `unanalyzed` manifest, and that
  manifest is the evidence: a producer that discards it publishes a claim it holds the disproof of.
  **The claim is withdrawn PER CLASS**, not for the whole report — a parse failure is a fact about one
  file, and an engine peeking several classes in one run (candor-swift reads `harness-target` and
  `manifest` together) must not let one unreadable test file delete what it did read. An unread file the
  producer cannot attribute to a class withdraws the claim for ALL of them: fail closed.

- ⟨0.32⟩ **A MULTI-REPORT VERDICT MUST BE COMPUTED OVER `hash`-KEYED UNITS, NEVER OVER BARE `fn`.** §2.2
  already binds the consumer; this states the consequence for the VERDICT, because the route that
  violated it was the gate. MEASURED on candor-query 0.31.0: `gate --report` over one member refused a
  scoped rule at exit 2, and gating the SAME member alongside an unrelated sibling exited 0 with
  `policy ✓` — the filter read the sibling's Unknown-class set through the name join and tolerated. The
  same join was measured charging one member's function with a class it inherits from another's. A
  FALSE GREEN produced by adding a report, which is why this is a MUST and not a SHOULD.
  Names legitimately repeat across packages, and they are not unique even WITHIN one report: an inherent
  method and a trait implementation of the same name emit two entries sharing `fn`. So the unit of a
  verdict is the `hash`-identified unit, and a verdict row MUST carry enough identity for a consumer to
  tell two units apart — a row a reader cannot attribute to a package is not actionable, and a consumer
  that fingerprints on name alone (candor's own SARIF action did) silently hides one finding behind
  another. The document's ORDER is part of §3.3.1 byte-equality, so the sort key MUST include that
  identity: without it the twin rows tie and the two routes, which accumulate in different orders,
  produce unequal documents — the ⟨0.31⟩ `outOfScope` hazard repeated.

- ⟨0.32⟩ **A CLASS THE SCAN DID NOT READ MAKES THE VERDICT INCOMPLETE.** An `excluded` entry with
  `peeked: false` and without `judgedElsewhere: true` (below) MUST suppress `ok` and exit 2, on BOTH the
  `scan --policy` and `gate --report` routes. ⟨0.30⟩ already ruled that a non-empty `outOfScope` does so,
  but that keys the verdict on what the peek FOUND — and a peek that cannot open a file finds nothing,
  which is byte-identical to finding it clean. MEASURED on candor-java: `deny Exec` answered a green pass
  at exit 0 over a tree holding an uncompiled `Deploy.java` calling `Runtime.exec("curl … | sh")`, with
  `excluded` reporting `peeked: false` beside it — the engine stating plainly that it never read those
  files, and that statement moving no verdict anywhere. This is the same three-row rule the `excluded`
  clause above already states, applied to the VERDICT rather than to the report: absence licenses a claim
  only if the key COULD have had a body, and `peeked: false` is exactly the case where it could not.
  A MISSING `peeked` key counts as NOT peeked — the fail-open reading of an absent disclosure is the
  failure the key exists to prevent. This MUST NOT fire on a run whose policy was REFUSED: a refusal is
  not a verdict, so there is nothing for incompleteness to qualify (§3.1).

  ⟨0.32⟩ **IT FIRES ONLY WHEN THE POLICY IN FORCE HOLDS AT LEAST ONE `deny` RULE, and the condition is the
  QUESTION BEING ASKED NOW — never the producing scan's history.** `pure` IS a deny rule — a deny with an
  EMPTY effect list, denying every effect except `Unknown` (§2.2 ⟨0.30⟩) — and counts. A policy carrying
  only `forbid`/`allow`/`only` never put the peek's question, so `peeked: false` under one means UNASKED,
  not unread, and MUST NOT refuse. **The condition MUST NOT be spelled as "did the producer emit
  `outOfScope`".** That spelling reads the producer's silence about the QUESTION as an answer about the
  CODE, and it deletes the rule in exactly the case it exists for: `excluded` is MANDATORY from ⟨0.29⟩
  (§2.2 above) while `outOfScope` is omitted when no policy was configured, so a ⟨0.29⟩-era no-policy
  report over a tree that HAS exclusions carries `peeked: false` with no `outOfScope` beside it. Such a
  report DOES fail closed on contact with a deny policy. **That is the rung, not collateral damage** — the
  producer never opened those files, the gate cannot open them from a document, and the hole in the
  evidence is the same hole whichever cause put it there.

  **THE FAIL DIRECTION OF THE CARVE-OUT, stated rather than left to be discovered.** It is FORCED, not
  chosen: the peek is deny-only by the ⟨0.29⟩ bound above, so a `forbid`/`allow`/`only` policy runs no peek
  on ANY route, and refusing such a policy would be a permanent refusal with no remedy — re-scanning with
  that policy runs no peek either. But an excluded file can hold a forbidden EDGE or a destination no
  `allow` list covers exactly as easily as a denied effect, so this is a REAL LIMITATION and not a proof of
  safety. It MUST therefore be DISCLOSED rather than silent: where a policy with no deny rule is applied
  over a report carrying unpeeked, non-`judgedElsewhere` classes, an engine MUST emit an advisory naming
  those classes and saying this policy cannot ask about them. Exit codes do not move. *Measured
  2026-08-24, `forbid ui -> db` over a tree with an unpeeked class: candor-rust and candor-swift print
  `policy ✓` and say nothing about the class; candor-java prints its scan-completeness advisory naming
  the unread files, but UNCONDITIONALLY — it is the same line a no-policy scan prints, so it carries no
  statement that the POLICY could not ask. So **no engine emits this advisory today**, and the obligation
  is written here to make the gap a recorded debt with a named remedy rather than an unasked question. A
  limitation carried only as a code comment reads as CONSIDERED, which is what stops it being measured.* This is the same
  shape as the `only`/`forbid` bound across a chained dependency — a name rule cannot see a crossing the
  join does not carry, because the join carries EFFECTS and not EDGES — which is filed and closed on the
  advisory channel for the identical reason: the verdict cannot move, so the bound must be visible
  (candor `BACKLOG.md`, `[P1]`).

- ⟨0.32⟩ `"judgedElsewhere": <bool>` — OPTIONAL in an `excluded` entry, default false. TRUE means *the
  files of this class are copies of code this same scan already judged*, so the class hides nothing and
  the rule above does not fire for it. The motivating case is a build tree: a jar under `build/` is a
  derived copy of the classes just analysed, and failing a gate on it would redden every project that
  builds one.
  **ONLY THE PRODUCER MAY SET IT, and a consumer MUST NOT infer it from the `class` token.** The clause
  above already says `class` tokens are ENGINE-CHOSEN and are NOT interchange vocabulary, and this is
  where that bites: the same concept is spelled `build-output-archive` by candor-java and `build-output`
  by candor-rust and candor-swift, so a consumer carrying its own list of "derived" names gates another
  engine's report differently from the engine that wrote it — route equality one level up. MEASURED on a
  candor-java build carrying such a list: an `excluded` class of `build-output-archive` exited 0 and the
  identical entry named `build-output` exited 2.
  The distinction is not cosmetic and cannot be recovered from a name: candor-rust's `build-script` is
  `build.rs`, code that RUNS at build time and can perform any effect, and it MUST fail closed; its
  `build-output` MUST NOT. Only the engine that made the exclusion knows which it made, so it MUST say
  so in the report rather than leave every consumer to guess.

- ⟨0.29⟩ **The peek MUST reach its finding through the engine's ordinary analysis path over a different FILE
  SET, never through a second one.** Two judgement paths drift, and a drifted second opinion reported as a
  warning is worse than no warning: the reader cannot tell a real finding from two code paths disagreeing.
  The engines satisfy this structurally rather than by review — a recursive call into the scan entry point
  where that entry point is a callable function, and a child process of the same binary where it is not.

- ⟨0.32⟩ **A peek MAY derive the file set it reads, and a class it derived may reach `peeked: true` —
  provided every file's derivation succeeded and the derivation runs no code from the scanned tree.** The
  clause above says the peek must not hold a SECOND judgement path; it does not say the file set must be
  found rather than made. Compiling a source the engine cannot otherwise read, then analysing the result
  through the ordinary path, satisfies the ⟨0.29⟩ MUST exactly — one classifier, resolved receivers, one
  semantics — and it is the only way an engine that reads compiled artifacts can answer for a tree that
  has not been built.

  The two conditions are not decoration. **Every file, or none of the class**: a derivation that half
  succeeded is the ⟨0.26⟩ partial-read overclaim in a new place, and a compiler that recovers from an
  error emits a body that throws where the code it could not translate would have gone — effects VANISH
  from that bytecode, a false all-clear with a compiler's authority behind it. **No code from the tree**:
  the derivation must not run annotation processors, build scripts, or plugins, because this is the tool
  that certifies `deny Exec` and a scan MUST NOT become an execution. An engine whose derivation therefore
  cannot see generated code MUST withdraw the claim where such generation is possible rather than certify
  on less evidence than a real build has.

  ⟨0.32⟩ **A derived set certifies the source against the CLASSPATH the derivation used, and that
  classpath MUST come from the scanned root or from an operator declaration — never from the tree's own
  build metadata — with its provenance disclosed.** The two conditions above cover whether the derivation
  COMPLETED; this one covers what it compiled AGAINST, and the difference is a false all-clear. A compile
  that succeeds against the wrong version of a dependency emits bytecode the project does not build: a
  `static final` constant guarding an effect folds to `false`, javac deletes the branch as unreachable,
  and the effect VANISHES from the derived set. That is the same disappearance error recovery causes,
  arriving through the classpath instead.
  
  Resolving the classpath from the tree's own `pom.xml`, lockfile, or build script is forbidden for a
  reason that survives any care taken over the resolver: it lets the artifact being scanned choose the
  inputs that shape its own derived bytecode — an artifact could compile itself innocent. An operator
  declaration puts that choice with the operator, where a wrong version is a wrong declaration in the
  same class as a wrong `net-partner` list, rather than something the engine silently picked.

  *Reported as the derived class's own name, never as the analysed one: the operator asked about
  `src/com/x/Deploy.java`, and a finding filed under a scratch directory names a file they cannot open.*

  *⟨0.29⟩ What this does NOT cover, recorded so it is a decision rather than a discovery: a file in no
  language the engine reads. A project whose `Exec` lives in `scripts/deploy.sh` is one where "candor says
  no Exec" remains a dangerous sentence, and no engine counts those files today — enumerating them would
  cost this block the bound that keeps it readable. See FILE-SET-DESIGN.md §3 (N3).*

- ⟨0.30⟩ **A NON-EMPTY `outOfScope` MAKES THE VERDICT INCOMPLETE — `ok: false`, `incomplete: true`, EXIT 2.**
  This reverses ⟨0.29⟩'s "an out-of-scope finding MUST NOT move the verdict", and the reversal is a
  measurement, not a preference. That clause assumed the peek would surface UNCERTAINTY, which a gate can
  reasonably decline to act on. It does not. Measured on published 0.29.1 under `deny Net`, the peek
  resolves a CONCRETE DENIED EFFECT and names the function: `axios` 37 functions `performs Net`,
  `node-fetch` 15, `ky` 9, `execa` 9, `zx` 3, `ofetch` 1 — every one exit 0, `policy ✓`. An engine that
  concludes a function performs the denied effect, prints that conclusion, and then certifies the tree is
  committing the cardinal sin with the evidence already in its hand.

  **Exit 2, NOT exit 1, and the distinction is the point.** These functions are still never members of
  `violations` and never members of `functions` — the gate did not judge them, so reporting a violation
  would be a second false claim in the opposite direction. Exit 2 says *I could not see enough of this tree
  to answer*, which is exactly what happened, and it reuses the fail-closed vocabulary already established
  by ⟨0.21⟩ (`{ok:false, incomplete:true, unanalyzed}`) and ⟨0.27⟩ (a configured dep that cannot be read is
  UNEVALUABLE, not reduced coverage). A consumer branching on `incomplete` alone is safe under both.

  **The bound in the ⟨0.29⟩ clause above is what makes this affordable**: `outOfScope` is emitted only for
  effects the policy DENIES, so the trigger is never "you excluded something" but always "you excluded
  something that does the thing you said must not happen." Measured across 27 real packages, that flips the
  6 above and leaves 14 green untouched — every one with an empty peek because the scan read it in full.
  Present-and-empty remains asked-and-clear and remains exit 0; the over-charge control is structural.

  ⟨0.30⟩ **THE PEEK ASKS THE GATE'S OWN MATCHER, NOT A SECOND ONE.** §6.2 already requires the gate and
  the disclosure to apply the same rule and share the same code; this clause states what that means for
  the block now that it is verdict-bearing. "Effects that policy DENIES" is decided per (rule, function)
  exactly as the gate decides it — so **`pure`, a deny rule with an EMPTY effect list, denies every effect
  except `Unknown`** and cannot be weaker than a `deny <Effect>` over the same code; a rule's `[class]`
  filters narrow the peek as they narrow the gate; and a rule's SCOPE binds the peek against the same
  project-relative qualifier, never an absolute path (a verdict must not depend on the checkout
  directory). Measured cost of leaving this unsaid: all four engines flattened the rules into a set of
  effect NAMES, so the STRICTEST policy silently disarmed the rung while class-filtered rules reddened
  destinations they do not deny. Exercised by the generated matrix, PART 55, which asserts the peek's
  judgement equals the gate's over identical code rather than any hand-written expectation.

  ⟨0.30⟩ **AND THE ADVISORY VERBS FOLLOW IT.** ⟨0.24⟩ binds every verb that answers `ok` — `unverified`,
  `fix-gate`, and any later sibling — to be *at least as pessimistic as the gate over the same bytes*.
  A non-empty `outOfScope`, and a PRESENT-but-unreadable one, are therefore incompleteness to those verbs
  too: `--strict` answers 2 wherever `gate --report` would. Measured: the rung moved the gate and left
  the siblings certifying `PROVABLY clean` over the identical report.

  **§3.1 ROUTE EQUALITY IS SATISFIED BY CONSTRUCTION, and unlike the `net-partner` attempt it needs no new
  anchor:** `outOfScope` is a field OF THE REPORT, so `gate --report` reads the same entries `scan --policy`
  peeked, and both routes derive one verdict document from identical input. An ABSENT key is the ⟨0.26⟩
  *cannot answer*, not a clear one, and it does NOT trigger this clause — a report produced with no policy
  was never asked the question, and pre-⟨0.30⟩ reports predate the key. A gate that wants this assurance
  must be given a report whose producer was configured with the policy.
  ⟨0.32⟩ **AND AN ABSENT `outOfScope` LICENSES NOTHING IN EITHER DIRECTION.** THIS clause does not fire on
  it; the ⟨0.32⟩ unread-class clause above may still refuse the SAME report, through the PRESENT
  `excluded[].peeked == false`. The two keys carry different claims under opposite emission rules —
  `outOfScope` is OMITTED when nothing was asked, `excluded` is MANDATORY from ⟨0.29⟩ whenever the engine
  can enumerate its own file selection — so reading the absence of the first as an answer about the second
  is the ⟨0.26⟩ collapse this format exists to prevent, and it deletes the ⟨0.32⟩ rule in precisely the
  case that rule was written for.

  ⟨0.32⟩ **A GATE CERTIFIES ONLY RELATIVE TO A REPORT WHOSE PRODUCER HELD THE GATE'S DENY SET, so a
  producer in a scan-then-gate pipeline MUST scan with the policy.** The peek is a producer-side act over
  a file set the consumer does not have: no consumer can re-derive it from a document, and the strongest
  thing a gate can say over a report scanned under a weaker deny set — or none — is that it could not see
  enough of the tree. It is the remedy a ⟨0.32⟩ refusal points at, and it is the **SAME** policy rather
  than merely *a* policy: a report scanned under `deny Net` answers nothing about `deny Exec` in the files
  it excluded, because the peek's own ⟨0.29⟩ bound filtered what it looked for to the PRODUCER's denied
  effects. *A report does not today record the deny set it was scanned under, so that mismatch is not
  detectable from the document — filed with its proposed fix (record the deny set, or a digest of it, in
  the report) in `FILE-SET-DESIGN.md` §8 rather than asserted away.*

**Forward compatibility:** a consumer MUST tolerate (ignore) envelope or entry fields it does not
recognize. An engine MAY add extension fields (e.g. a mode marker on an observed-fleet report);
the fields this document defines are the interchange contract, not a closed schema.

Each entry:

```json
{
  "fn":           "<fully-qualified function name>",
  "loc":          "<file:line:col>",
  "inferred":     ["Net", "Fs", "..."],  // FULL TRANSITIVE effect set (this fn + everything it calls)
  "direct":       ["Fs"],                // effects performed in this fn's own body only
  "declared":     [],                    // OPTIONAL ⟨0.26⟩ — effects the signature declares it may
                                         // perform (§5). PRESENT means a §5 reconciliation pass RAN;
                                         // ABSENT means it did not. See the rule below: an engine that
                                         // does not run one MUST OMIT all three, never emit `[]`.
  "undeclared":   [],                    // OPTIONAL ⟨0.26⟩ — inferred − declared (the AS-EFF-001 set)
  "overdeclared": [],                    // OPTIONAL ⟨0.26⟩ — declared − inferred (unused declarations)
  "unresolved":   true,                  // true if `inferred` may be incomplete (contains Unknown)
  "entryPoint":   false,                  // OPTIONAL: true if the RUNTIME invokes this fn, not (only)
                                         // project code — a reachability ROOT. The language/framework
                                         // surface that has no in-project caller: `main`, test/exported
                                         // (`#[no_mangle]`) fns; on the JVM the much larger reflective
                                         // surface — finalize, Runnable/Callable task bodies, servlet
                                         // and Spring lifecycle (@PostConstruct/@PreDestroy, web/queue
                                         // handlers, JPA callbacks). Lets a consumer compute the effects
                                         // reachable from the roots; its body's effects are NEVER
                                         // orphaned. Population is runtime-specific — far richer on a
                                         // reflection/framework runtime than on Rust. Default false.
  "unknownWhy":   ["dispatch:Foo.bar"],  // ⟨0.6⟩ REQUIRED when this fn introduces `Unknown` DIRECTLY (a source); absent if purely inherited. Why —
                                         // `reflect:<callee>` (reflection / dynamic invoke),
                                         // `native:<method>` (no analysable body),
                                         // `dispatch:<type>.<method>` (a project abstraction with no
                                         // visible impl), or `callback:<what>` (a call through a
                                         // function-typed value — a closure/fn-pointer parameter or
                                         // field whose target isn't statically known), or ⟨0.24⟩
                                         // `ambiguous:<what>` (the analyser's own NAME RESOLUTION was
                                         // ambiguous — two same-named local definitions, so no owner
                                         // could be formed at all). Lets a consumer
                                         // tell irreducible opacity (reflection, native) from the
                                         // IMPROVABLE kind (`dispatch:`/`callback:` — a missing impl or
                                         // an unresolved higher-order target, often resolved by widening
                                         // the analysed inputs). Omitted when this fn introduces no
                                         // direct Unknown.
  "invisible":    ["somepkg"],           // OPTIONAL ⟨0.15⟩ (formalizes what engines already emit):
                                         // the UNCOVERED external packages this fn DEMONSTRABLY
                                         // calls — the per-function attribution of the envelope
                                         // `coverage` ledger. `inferred: []` with a non-empty
                                         // `invisible` means "pure as far as candor could see, but
                                         // it calls into N packages the classifier doesn't cover" —
                                         // NOT a purity claim. Direct calls only; transitive reach
                                         // is the consumer's join over `calls`. An engine MAY
                                         // instead mark such a fn `Unknown` (a STRONGER posture —
                                         // it participates in gating); an engine MUST do at least
                                         // one, never silently pure.
  "unitKind":     "accessor",            // OPTIONAL ⟨0.5⟩: what KIND of unit this entry is, when it
                                         // is not an ordinary function/method. Absent = "function".
                                         // Recommended values: "initializer" (static/class init —
                                         // a JVM <clinit>, a lazy/static initializer), "accessor"
                                         // (computed property get/set/observer bodies), "export"
                                         // (a module-boundary export surface, the CJS shape),
                                         // "agent"/"command"/"skill"/"cron"/"session"/"hooks"
                                         // (an agent-fleet report).
                                         // ⟨0.14⟩ A module's TOP-LEVEL executable code (module-load
                                         // statements, a JVM static initializer) that performs an
                                         // effect MUST be attributed to an "initializer" unit — a
                                         // silently-dropped top-level effect is the cardinal sin (a
                                         // false-pure report). Conformance PART 4p pins it; N/A for a
                                         // language with no top-level executable code (Rust).
                                         // INFORMATIVE, never semantic: effects, edges and joins
                                         // mean exactly the same for every kind — the field lets a
                                         // consumer render/filter sensibly when reports from
                                         // different domains share one prefix (a fleet `session`
                                         // beside a crate's `main`). An unknown value is tolerated
                                         // (§2 forward compatibility), never an error.
  "hash":         "<stable cross-crate id>", // a stable identity (e.g. DefPathHash, pkg#LocalName) so
                                         // a dependent's analysis can inherit this fn's effects
                                         // across the package boundary. Producers MUST emit it
                                         // (0.4 — a hashless report is silently unchainable);
                                         // consumers may ignore it.
  "calls":        ["..."],               // OPTIONAL: effectful local functions this one calls — the
                                         // effect-relevant call graph, so a consumer can answer
                                         // "who calls X?" from the report without re-analysis.
  "fs":           ["read", "write"],     // OPTIONAL: when `Fs` is present, which kinds — `read`
                                         // and/or `write`. Omitted when the kind can't be
                                         // determined (see below); never a partial claim.
  "hosts":        ["api.example.com"],   // OPTIONAL: when `Net` is present, the LITERAL endpoints
                                         // statically visible (`host[:port]`). Omitted when the
                                         // address is runtime-computed (see below); never complete.
  "cmds":         ["git"],               // OPTIONAL: when `Exec` is present, the LITERAL subprocess
                                         // commands statically visible. Same rules as `hosts`.
  "paths":        ["/etc/app"],          // OPTIONAL: when `Fs` is present, the LITERAL filesystem
                                         // paths statically visible. Same rules as `hosts`.
  "tables":       ["ledger.entries"],    // OPTIONAL: when `Db` is present, the LITERAL database
                                         // tables statically visible (table-position identifiers
                                         // in a SQL string literal). Same rules as `hosts`.
  "netClass":     ["unknown-host"]       // ⟨0.20⟩ OPTIONAL: when `Net` is present, the DESTINATION
                                         // classes in the fn's transitive Net surface —
                                         // known-telemetry / known-partner / unknown-host (§6.2).
                                         // Fail-closed: a masked/runtime host is unknown-host.
}
```

`inferred` MUST be transitive: if A calls B and B performs `Net`, A's `inferred` includes `Net` —
**including when B lives in another crate of the same project**. `direct` is the non-transitive
subset. Effect-free items MAY be omitted from the report.

`hash` is the join key a dependent uses to inherit a function's effects across a package boundary —
both within a multi-crate project (the transitivity rule above) and when a report is CHAINED as a
dependency's (below). A producer MUST emit it (0.4; previously SHOULD for single-crate reports):
any report can become a chained sibling, and a hashless one is silently unchainable — every
cross-boundary call drops and the consumer *under*-reports, the dangerous direction. A consumer may
still ignore `hash`.

**Report chaining** (the `CANDOR_DEPS` convention, consumed by all four code engines as of
2026-07-09 — candor-swift joined last, with a deliberately conservative import-gated join: a file must
import the covered module before its unresolved calls are candidates): a
scan accepts *sibling reports* — previously-produced reports for the scanned code's dependencies —
and an unresolved/unclassified call into a package one of them covers inherits that function's
recorded transitive effects AND its literal surfaces (`hosts`/`cmds`/`paths`/`tables`). Three rules
make the chain trustworthy:

⟨0.27⟩ **A CONFIGURED DEP THAT CANNOT BE READ IS UNEVALUABLE (exit 2), NOT REDUCED COVERAGE.** Measured
across four engines on the same input: java and swift refuse; rust and ts continued at exit 0, rust
qualifying the omission with a coverage line and ts with only a "skipped" note. One `.candor/config`,
two meanings, on a condition CI meets routinely — a dep not yet scanned, a path that moved.

Both postures were internally coherent, which is why this needed a ruling rather than a bug report. The
continuing arm reads a missing dep as reduced COVERAGE, which is exactly what the ⟨0.15⟩ envelope exists
to qualify. **What decides it is where the answer LANDS.** Measured with a real path dependency:

    dep report chained    → caller `inferred: ["Fs"]`
    same config, report missing, run continues → caller `inferred: []`

`[]` is a ⟨0.21⟩ purity claim, and it travels in the REPORT — the artifact a chained consumer and a
`gate --report` both read. The coverage disclosure travels on stderr, which they do not read. So the
continuing arm publishes an unqualified purity claim about a function whose dependency the operator
explicitly configured precisely so it would not be one. That is the cardinal sin with a note attached
somewhere else, and a note in a channel the consumer cannot see is not a qualification.

It is also the §6.2 posture the family already applies to a *policy* that cannot be read: configured-
but-unusable fails loud, because a silently-dropped config is a silently-dropped guard. A dep is
configured the same way and for the same reason.

So: a dep path named by `deps`/`CANDOR_DEPS` that does not exist or cannot be read MUST exit 2, naming
it. Genuine ABSENCE of the key is unaffected — an unchained scan is a complete answer about what it
saw, and its uncovered calls are Unknown and disclosed. This binds the configured case only.

1. **Joins never guess.** The `hash` key must identify the target the way the *consumer's* view of
   the call names it (a `package#LocalName`, a `crate#qual` tail, a full method reference:
   per-language, but derivable from both sides).

   ⟨0.25⟩ **An ambiguous key — two entries sharing it — MUST be UNIONED. It MUST NOT be picked from,
   and it MUST NOT be dropped.** The consumer inherits the union of every colliding entry's effects,
   literal surfaces, coverage ledger and reason tags.

   **This REVERSES ⟨0.24⟩ and earlier, which said such a key "is dropped, not picked from — §4's
   under-report-don't-fabricate rule, applied at the join". The prohibition on PICKING was right and is
   unchanged. The prescription to DROP was the cardinal sin, and it invoked §4 to license the very thing
   §4 forbids:** a dropped key resolves to nothing, so the calling function leaves `functions` entirely,
   and under ⟨0.21⟩ an absent entry is a *positive claim of purity*. The rule mandated silence over a call
   whose target the engine had just declared itself unable to name. Any implementation still conforming to
   the ⟨0.24⟩ text is emitting a silent under-report; this is a correction, not a preference.

   **The union is not a hedge, and that is measured rather than argued.** Across three real `.candor/deps`
   trees (candor-rust, pgman, ebman) every one of the 123 colliding keys whose entries disagreed was **one
   function at two VERSIONS of one package** — cargo and npm both permit semver-major duplicates, and the
   package-scoped key cannot express which copy a given caller resolves to. Both bodies are in the build,
   the runtime may execute either, and their union is therefore simply *what the key means*. Cost of the
   union across all three: **seven effect-items**, to close 123 purity claims. On the consumer side: 11
   previously-absent functions recovered, **0 lost, 0 narrowed, and every one of the 65 added effect-items
   was `Unknown`** — no concrete effect was charged to a function that did not have it.

   **The collision the drop rule was written for — two UNRELATED functions sharing an imprecise key — is
   real, and the union is still correct for it.** It does not arise between reports (the corpus above
   contains none) but it does arise WITHIN one, wherever an engine keys an entry by a leaf or a tail as
   well as by its full qualification: `sync::Client::fetch` performing `Net` and a pure
   `mock::Client::fetch` share the key `fetch`. Union charges `Net` to that key — and that is the honest
   answer, because the key is only ever consulted by a consumer that could NOT name its target. A consumer
   that CAN asks the fully-qualified key and still gets the precise entry, so precision is preserved by the
   KEY SCHEME rather than by withdrawal. Dropping it was measured on a real engine as the caller vanishing
   from `functions` with no `Unknown`, no coverage note and no hedge of any kind — the same silence, over a
   call that may genuinely reach the effectful body.

   **TRUST LEVELS DO NOT RANK HERE.** A §2.1-downgraded entry (rule 2) joins the union like any other; an
   implementation MUST NOT prefer a trusted entry and discard an untrusted one. The collision exists
   *because* one package name spans two versions, so the distrusted report is the only evidence that a
   second, unverifiable copy is present — preferring the trusted entry deletes exactly that, and the
   consumer reads the surviving version's `[]` as a purity claim over a call that may reach the other.
   The observable invariant is **order-independence**: the joined result MUST NOT depend on the order
   reports are loaded or walked in. Union is commutative, associative and idempotent; withdrawal and
   trust-ranking are none of the three, and both were observed to make the answer depend on a *filename*.

   Chaining one report twice is therefore not observable (conformance PART 25), and an untrusted report
   beside a trusted one may only ADD (PART 26). Rationale and the full measurement:
   `ENTRY-COLLISION-DECISION.md`.
2. **Stale reports are not trusted**: §2.1's version-trust rule applies at the join, and a
   report whose producing version is MISSING is as unverifiable as a mismatched one: downgrade to
   `Unknown`. (§2.1 is the single normative statement; this rule only locates where it bites.)
3. **A chained package is COVERED, not blind, including its silence.** Reports omit pure
   functions, so a call that joins *no* entry in a loaded sibling report is that report's affirmative
   purity claim (modulo the producer's own §4 standing). A coverage disclosure (item 14, §7) must
   therefore treat every package a loaded report covers as accounted for, even with zero joins:
   an all-pure dependency's *empty* report is a claim, not a blind spot.

Chaining is what shrinks the curated classifier's job to the **builtin/FFI frontier**: a
dependency's effects derive from *its own* calls into the platform, so one dep scan replaces a
hand-curated classifier entry, transitively.

`fs` refines the `Fs` effect into `read` / `write` kinds: the detail a consumer needs to tell a
read-only function from one that mutates the disk. It applies only when `inferred` contains `Fs`. An
implementation that resolves the kind SHOULD emit it; one that can't (or doesn't track it) MAY omit
it. Crucially, when `Fs` is reached but its kind is *unknown* (e.g. inherited from a sibling/dep
report, §2.1, that carried no `fs`, so no read/write is locally observable), the field MUST be
**omitted rather than guessed**. An empty or partial `fs` would be read as a positive claim ("reads
but never writes"), which is the §4 trust contract's forbidden direction (under-claiming an effect).
Omission says "`Fs`, kind undetermined"; a present `fs` is an affirmative read/write classification.

⟨0.29⟩ **`incomplete` is named by `resolves` too, on the same argument.** An absent `incomplete` is
overloaded between *"this producer does not compute undetermined locators"* and *"it computed them and
found none"* — exactly the ambiguity `resolves` exists to remove, one field over. A producer that computes
the field declares it; one that does not MUST NOT, since listing it would turn "unimplemented" into a false
"nothing undetermined", which is the inversion in the direction that certifies.

⟨0.27⟩ `fs` is the first surface named by the envelope's **`resolves`** array (§2.1). Read the two
together: `resolves` containing `fs` is what makes an absent `fs` mean "reached, kind undetermined" rather
than "this engine does not track kinds". Without the declaration the omission is unreadable, which is how
the field came to be emitted by one engine of four with nobody noticing.

`hosts` refines the `Net` effect with the endpoint(s) a call talks to, but **only the statically
decidable subset**: a string-*literal* address or URL (`connect("rates.internal:7070")`,
`get("https://api.example.com/v1")`) yields a host (`host[:port]`, scheme and path stripped); a
runtime-computed address yields none. It applies only when `inferred` contains `Net`. Unlike `fs`,
`hosts` is **never a completeness claim**: host-by-runtime-value is undecidable, so an absent or
partial `hosts` means "these are the endpoints I could see," NOT "the function talks to no others."
A consumer MUST treat it as informative, never as a closed allow-list; and an implementation MUST
NOT emit a host it merely inferred (only ones it read from a literal), so a present entry is always
sound. This keeps it within the §4 trust contract: `Net` already carries the "performs network I/O"
claim; `hosts` only ever *narrows* it with what's provably visible.

`cmds` (for `Exec`), `paths` (for `Fs`) and `tables` (for `Db`) follow the **same rules as `hosts`**:
the statically-decidable literal subset only (a `Command::new("git")` / `fs::read("/etc/x")` literal;
or, for `tables`, the table-position identifiers of a SQL string *literal*, never a dynamically-built
query), informative-not-complete, never emitted unless read from a literal. A producer MAY also feed
`tables` from a *declarative* mapping the source makes statically visible (a JPA `@Table(name=…)` /
TypeORM `@Entity('…')` entity reached through a typed repository): the same decidability bar, read
from an annotation literal instead of a SQL one.

⟨0.29⟩ **A literal surface MUST be read from the POSITION that names the locator, never from whichever
argument of the call happens to be a literal.** §4's subprocess-boundary clause already states this for the
`Exec` head — argv[0] is the program, and `spawn(tool, "curl")` with a dynamic `tool` must not refine —
and the rule is the same for every surface: the path, the host, the command and the query each sit at a
known argument position, and a literal anywhere else is DATA. Reading it as the locator FABRICATES a
destination, which is worse than reading none: `write(userPath, "/tmp/lit")` publishing
`paths: ["/tmp/lit"]` lets `allow Fs /tmp/lit` certify a write to a runtime-controlled destination, so the
operator's own allow-rule becomes the mechanism of the false all-clear. **Where an operation takes SEVERAL
locator positions — a copy, a rename, a link — the surface is complete only when EVERY one of them is a
literal**; one literal beside one runtime path is an unseen destination, and the unit MUST carry
`incomplete` for that effect (§2) rather than publish the half it can see as though it were the whole.

Two engines extracting different tables from the same SQL would split the policy verdict, so the SQL
extraction is pinned token-for-token; the cross-impl vector battery
(`conformance/tables/vectors.json`) is its executable form:

1. Lowercase the literal; replace `(` `)` `;` with spaces; surround each `,` with spaces (the comma
   survives as its own token); split on any whitespace run.
2. If the first token is not a statement keyword (`select insert update delete create drop alter
   truncate merge replace with`), the string is not SQL: extract **nothing** (conservative in the
   fabrication direction).
3. A token introduces a table position if it is `from`, `join`, `into` or `table` anywhere, or
   `update`/`truncate` as the statement's FIRST token only (a mid-statement `UPDATE` is a
   `FOR UPDATE` locking clause and introduces no table).
4. After the introducer, skip the noise words `only` `if` `not` `exists` `table`.
5. Trim surrounding quote characters (`"`, backtick, `'`) from the candidate. Reject it unless it
   begins with `[a-z_]` and consists only of letters, digits, `_`, `.`, `$` and quote characters;
   reject grammar words in identifier position (`select set where values on using group order by
   limit returning as inner outer left right cross lateral natural union all distinct case when null
   default skip nowait of from join into update delete insert`). Remove any interior quote
   characters and emit in first-occurrence order, deduplicated.
6. After a captured table, a **comma-adjacent** identifier continues the table list (`FROM t1, t2,
   t3` yields all three), and anything else breaks the chain: an alias (`FROM t1 a1, t2` yields only
   `t1`, an under-report, never a guess) or a rejected candidate. The adjacency requirement is the
   fabrication guard: by this stage a column list rides commas too (`INSERT INTO t (a, b)` once
   parens are spaces), and skipping an alias to chase the comma would mint tables from it.

The four together are the literal surfaces an `allow <Effect>` policy rule (AS-EFF-008) enforces; a
producer SHOULD emit them so a dependent crate's allowlist can see a value that lives across the
crate boundary; and an implementation that ENFORCES `allow <Effect>` rules MUST emit that effect's
surface (0.4): an allow gate over an unemitted surface fails every rule as uncertifiable (lits = ∅),
which is worse than no gate at all.

### 2.1 Provenance (the `candor` header)

A report is only meaningful relative to the engine that produced it: a richer classifier or a new
resolution rule changes the effect set for the *same* source, so a baseline is comparable only to its
own producing version, and a dependent crate must not silently trust a sibling report from a different
engine (the trust contract, §4, applied to candor's own output). For a baseline **GUARD** (the
AS-EFF-005 gate) this is load-bearing: a baseline whose producing version differs from the running
engine, or that carries no provenance at all, is **invalid gate input**, and the guard MUST fail the
run (the §6.2 unreadable-policy class: a distinct non-violation exit, the code engines' CLIs use `2`)
**without evaluating**. Never a silent skip (an unbounded fail-open window), and never a stale
comparison (an unmasking wave with any real regression hidden inside it). Read-only comparison
*queries* (`diff`/`gains`, §3.1) instead **disclose** the mismatch (a warning plus
`baseline_version`/`engine_version` provenance fields in their JSON) and still answer: a comparison
the user explicitly asked for should inform, not refuse. The envelope's `candor` header
carries this (`version`, the engine build id, plus `toolchain`), so the report is self-describing.

The header has THREE fields, on two distinct axes. Keep them separate:

- `version`: the engine **build identity** (a build id / git hash / release tag). It answers "which
  binary produced this?" and MUST reflect the binary that **actually ran**, not the source tree it was
  built from: those diverge when the source is updated without a rebuild, and a source-derived version
  would call a stale engine "current" and mask a stale baseline. A consumer performing cross-crate
  inheritance (§2, `hash`) MUST compare `version` (0.4; a MISSING version is as unverifiable as a
  mismatched one) and, on a mismatch, treat the inherited effects as
  unverified (downgrade to `Unknown`) rather than trust them.
- `toolchain`: the language/runtime channel (`nightly-…`, `stable`, `jdk-21`).
- `spec`: the **candor-spec contract version** this engine implements (`"0.15"`). This is the version
  *this document* carries, NOT the engine's build id or the package's release version; they evolve
  independently (a binary-only scanner fix bumps the release, not the spec). An implementation MUST emit
  `spec` so a consumer can tell which contract a report conforms to, and SHOULD source it from a single
  constant (the Rust implementation: `candor_report::SPEC_VERSION`). A report without `spec` predates this
  field and is treated as spec ≤ 0.2.

The Rust implementation additionally embeds `version` in the dylib itself (so a tool can read the
*true* build version without running the engine) and mirrors `version`/`toolchain` into its
`<prefix>.calibrated.json` sidecar; for a **legacy v0.1 bare-array** report that has no header, an
implementation MAY fall back to that sidecar for provenance.

⟨0.27⟩ **`resolves` — WHICH OPTIONAL REFINEMENTS THIS PRODUCER COMPUTES.** A top-level array beside
`extensions`, naming the optional per-function refinement surfaces the engine actually resolves:

```json
{ "candor": { "version": "…", "toolchain": "…", "spec": "0.31" },
  "resolves": ["fs", "incomplete"],
  "functions": [ … ] }
```

**Why it exists: without it, the absence of an optional field is OVERLOADED and a consumer cannot read it.**
An absent `fs` means either *"this producer does not compute kinds"* or *"it computed and could not
determine one"*. Those are different facts — the second is information, the first is nothing — and the
whole value of the omit-rather-than-guess rule depends on knowing which you are looking at.

That overloading is not hypothetical and it is what motivated this rung. `fs` had been in this document for
a long time; on 2026-08-04 it was found to be emitted by ONE of four engines. One had no such field at all,
one emitted nothing, and one carried the field in its wire model with a hardcoded empty value — **never
populated**, which is worse than absent, because a present-but-always-empty field asserts "kind
undetermined" on every function forever while wearing a schema that implies support. Nobody noticed for as
long as the field had existed, precisely because every empty answer was individually defensible. **A field
whose absence is always excusable is a field nobody checks.**

The rules:

- A producer **MUST NOT** list a surface it does not compute. Doing so converts "unimplemented" into a
  false "undetermined", which is the exact inversion this field exists to prevent, and is worse than
  omitting `resolves` entirely.
- A producer that computes a surface **SHOULD** list it. Omitting the declaration is safe but lossy: it
  makes every one of that engine's omissions unreadable.
- A consumer **MUST NOT** read an absent optional field as "the producer looked and could not tell" unless
  that surface is named in `resolves`. Absent `resolves`, an absent field carries no information at all.
- `resolves` says nothing about *per-function* completeness. It is a statement about the PRODUCER, not
  about any function's answer — exactly as `extensions` is.

**Eligible surfaces are those whose PRESENCE is a positive claim.** `fs` is: a present `fs` is an
affirmative read/write classification, so its absence had to mean something. `hosts`/`cmds`/`paths`/
`tables` are explicitly *never* completeness claims (an absent or partial `hosts` means "these are the
endpoints I could see"), so their absence already means nothing and they need no declaration. The initial
vocabulary is therefore `["fs"]`; the mechanism is general and a later rung adding an optional surface with
claim-bearing presence adds its name here rather than inventing a second channel.

**Relationship to `extensions`.** Same shape, different scope: `extensions` declares an ecosystem surface
led by one engine (`privacy/2`), `resolves` declares an optional refinement of the shared floor. Both are
*positive declarations of what is active*, which is the only construction under which optional structure is
safe — the alternative, inferring capability from absence, is the defect above.

### 2.2 The call-graph sidecar

Alongside each report, an implementation that provides the blast-radius or structural tools (§3.1–3.2)
emits a **call-graph sidecar** named alongside its report so the two are paired (the Rust impl uses
`<prefix>.<crate>.<type>.callgraph.json`; the JVM impl appends `.callgraph.json` to the report stem —
each consumer pairs sidecar to report by its own naming, as with the §2 report file) — a JSON object
mapping each function (by the same fully-qualified name used in the report) to the functions it directly
calls:

```json
{ "a::caller": ["b::callee", "b::other"], "b::callee": ["c::leaf"] }
```

Crucially, unlike the report — which omits pure functions and records only effect-relevant `calls` — the
sidecar records EVERY project function's edges, **including pure ones**. That is what lets a consumer
answer *"who transitively calls X?"* for a function that is currently **pure** — the blast radius an agent
needs *before* introducing an effect. The sidecar is OPTIONAL, but an implementation that provides the
`callers` / `whatif` / `rewire` tools (§3.1–3.2) MUST emit it: those cannot answer the pre-edit question
from the report alone (a pure X is absent from the report). It carries no provenance of its own and is read
together with its report.

⟨0.24⟩ **`Llm` REFINES `Net`; `Db` DOES NOT — and this sentence used to say they did so alike.** It read
"`Llm` refines `Net` **the way `Db` does**". They are not the same relation, and the difference is the test
for what "refines" may mean here: **an effect refines a base channel only when EVERY occurrence of it is an
occurrence of that channel.** A model-provider call is an outbound request in every instance — which is why
the engines **co-emit `Llm` and `Net`**. An embedded, file-backed or in-process store is a `Db` effect with
**no egress at all** — which is why the engines emit **`Db` alone**. The two encodings were already
opposite; only this sentence claimed otherwise.

It was not a wording problem. PAPER3's Definition 2 took the sentence at its word and carried `Db ⊑ₑ Net`,
Definition 4 fires `deny e` on any refinement of `e`, and a differential of the JVM engine against the
executable model produced **100 disagreements over 1792 rows — every one that family**, model REJECT and
engine pass. The engines were right; the theory has been corrected to match, not the reverse. Widening the
gate instead would have been the fabrication mirror: `deny Net` firing on `{Db}` charges every
embedded-database user with network egress they do not have.

**The residual is real and is a CLASSIFIER question, not a gate one.** A *networked* database call is
genuine egress that `deny Net` does not see. `Db` and `Net` **overlap without either refining the other**,
which a relation over effect *names* cannot express — closing it means extending the destination
classification the gate already carries for `Net` (§6.2's `netClass`) to `Db`, so a networked store is
distinguishable from an embedded one at the call site. Filed, not attempted here.

⟨0.24⟩ **`callgraph` and `hierarchy` are RESERVED trailing segments, and a report-locator glob MUST
exclude them at the GLOB — not diagnose them at the parse.** Sidecar names are per-engine (this section
lets each engine pair a sidecar to its own report stem), so a discriminator based on SEGMENT COUNT alone
excludes an engine's own 3-segment sidecars and not a 2-segment one from another producer. Measured on the
reference implementation: `<prefix>.<pkg>.hierarchy.json` landed exactly on the `<crate>.<type>` report
shape, so **two globs in one binary disagreed about one file** — the sidecar loader read it as a sidecar
while the report locator claimed it as a report, then reported its own mistake as the user's data loss
("failed to parse — its functions are OMITTED; re-run the scan", about a file that was neither).

That is a FALSE DISCLOSURE, and it was not cosmetic. Three measured consequences, each against a
sidecar-removed control: an **effect-free crate was REFUSED** (the bogus parse failure set the hard-fail
bit that distinguishes "no effects" from "every report was corrupt", so a well-formed `functions: []`
report beside a sidecar exited 2 and answered nothing); **provenance was lost** (the build-version reader
takes the first report by sorted path, and the sidecar sorts first, emptying `baseline_version` /
`engine_version` — which in turn **silences the §2.1 producing-build mismatch disclosure**, a false
disclosure suppressing a true one); and the `reports` verb, the canonical "what counts as a report" oracle,
listed sidecars as reports.

The exclusion MUST be a **denylist** — carve out the reserved segments, keep accepting everything else.
The inversion (accept only known `<type>` values) is an ALLOWLIST, and any report whose type segment an
implementer failed to anticipate becomes silently invisible to every query: a false all-clear. A denylist
can only be *incomplete*, and incompleteness here is **loud** — an unregistered suffix falls back into the
candidate set and prints a disclosure on every query. Noise, never a swallowed report. A crate legitimately
*named* `hierarchy` must still resolve: it sits in the `<crate>` position, not the reserved one.

**The reserved set, family-wide:** `callgraph`, `hierarchy`, `calibrated`, `layerreach`, `locs`, `gate`,
⟨0.32⟩ `refused`, and the `encountered-*` family. It is stated here because **the engines were already drifting on it** and
nothing said they should not: three of the four excluded these by name and one discriminated by segment
count, but the by-name lists disagreed — one engine carved out six suffixes, another two. Cross-engine
reading is not hypothetical (the conformance frontier differential has one engine produce and another
consume), so a consumer with the shorter list will claim another engine's sidecar as a report. This
paragraph exists because the convention was real, correct, undocumented, and unevenly implemented — which
is the state in which a rule is most likely to be quietly lost.

**Not covered, deliberately:** the §3.3.1 **direct-file** locator. `--report path/to/x.hierarchy.json`
loads that file whatever its internal dot-segments, so one engine can query another's report by path;
refusing it there would break that. The rule above is about *prefix discovery*, where the engine chose the
file and is therefore accountable for the choice.

⟨0.7⟩ **The type-hierarchy sidecar.** Alongside the report, an engine whose language has class/interface/
protocol dispatch SHOULD also emit a **type-hierarchy sidecar** — a separate `<stem>.hierarchy.json`
(the Rust/JVM impls append `.hierarchy.json` to the report stem; candor-swift uses
`<prefix>.<package>.Swift.hierarchy.json`) — a JSON object mapping each **project type** to its **direct
supertypes and implemented interfaces/protocols** (project types only — `O(classes)`, not `O(edges)`):

```json
{ "app.Impl7": ["app.Base"], "app.Base": [], "app.Dispatcher": ["app.AbstractSvc", "app.Closeable"] }
```

The type name keys match the owner type in the report's `dispatch:<owner>.<member>` reasons (§4) and the
function-name quals, so a query can resolve *"is this confirmed reacher an override of `OWNER.M`?"* — a
method whose simple name is `M` declared on a subtype of `OWNER` per this map — **without** the engine
storing the candidate edges bounded-CHA deliberately dropped. That precise subtype resolution is what the
`callers --include-unknown` frontier (§3.1) keys off. The sidecar is OPTIONAL — but an engine that exposes
`callers --include-unknown` over a dispatching language MUST emit it (the frontier degrades to an imprecise
simple-name match without it). It carries no provenance of its own and is read with its report. A language
with no class/protocol dispatch (the Rust scanner) has nothing to populate it and MAY omit it entirely.

⟨0.26⟩ **THE KEY SET IS THE MANIFEST: an absent type is UNANSWERABLE, never "has no supertypes".**

A producer MUST emit a key for **every type it indexed**, carrying `[]` when that type has no supertypes —
which is what the example above has always shown (`"app.Base": []`). A consumer MUST therefore read the key
set as the closed set of types the pass can answer for, and treat a type **absent** from a present sidecar
as **unanswerable**: the subtype test MUST NOT resolve to `false`, and a query depending on it MUST
disclose rather than drop. Same trigger as §3.1's dot-free `dispatch:` detail and §2's unreadable manifest —
*disclose, do not drop*.

**Why this is a rung and not a clarification: absence carried two meanings and the format could not tell
them apart.** A type with no supertypes was omitted, and so was a type the pass never looked at — an
out-of-scan reacher being the ordinary case. A consumer asking `isSubtypeOf(t, owner)` about an unindexed
`t` got `false`, indistinguishable from a true negative, and the ⟨0.24⟩ per-FILE ruling cannot reach it
because the file is present and non-empty.

**Measured, and the shape is the argument.** On the `callers --include-unknown` frontier fixture (13
implementors past the fan-out bound, one reaching the sink, a dispatcher dispatching on the base), scanned
for real and then only the sidecar doctored:

| sidecar | java frontier | ts frontier |
|---|---|---|
| intact | `[Dispatcher.run]` | `[Dispatcher.run]` |
| the REACHING implementor's entry removed | **`[]`** | **`[]`** |
| a NON-reaching implementor's entry removed | `[Dispatcher.run]` | — |
| **wholly absent** | `[Dispatcher.run]` | — |

Removing MORE information — the whole sidecar — yields a SAFER answer than removing ONE entry. That
non-monotonicity is the defect. The third row is what makes the second attributable: removing an irrelevant
type changes nothing. Both engines that ship the verb behave identically, which is evidence about the
FORMAT rather than either engine — neither had a third answer available.

⟨0.26⟩ **`@unanalyzed` — types the pass TRIED and could not index.** Reserved keys are `@`-prefixed, so they
cannot collide with a type name (the convention `@superclass` already establishes):

```json
{ "@unanalyzed": [ { "type": "app.Broken", "reason": "class file failed to parse" } ],
  "app.Impl7": ["app.Base"], "app.Base": [] }
```

OPTIONAL; its absence means only that the producer records no such failures. It changes no verdict — an
unindexed type is unanswerable whether or not the sidecar says why — but it is the difference between a
consumer reporting *"the hierarchy cannot answer for `app.Broken`"* and *"…for a type I cannot name."*
The asymmetry with §2's report manifest is deliberate: a report's unanalyzed set is ENUMERABLE (the files
it failed to read), while a sidecar's complement is every type in the world. So the positive key set is the
manifest, and `@unanalyzed` is a diagnostic rather than the closed set.

⟨0.26⟩ **THE §5 RECONCILIATION TRIO IS PRESENT-OR-ABSENT, NEVER EMPTY-AS-A-CLAIM.**

`declared` / `undeclared` / `overdeclared` are the outputs of the §5 capability-reconciliation pass. An
engine that runs one emits all three. **An engine that does not run one MUST OMIT all three. Emitting
`[]` is forbidden**, and a consumer MUST read their ABSENCE as *"no declaration contract was computed"* —
never as *"this function declares nothing and violates nothing"*.

This is §2.2 ⟨0.26⟩'s rule one layer up, and ⟨0.21⟩'s before that: **an empty set is a positive claim.**
`undeclared: []` says *no function performs an undeclared effect* — an AS-EFF-001 all-clear. An engine
with no §5 pass has not established that and must not assert it.

**Measured, and the shape is the argument.** Only one engine implements the §5 codes (AS-EFF-001/002/004)
at all; the others implement the analysis- and policy-side codes and no conformance pass. On one function
performing `Fs` while declaring nothing, the reference engine reports `undeclared: ["Fs"]` and raises
AS-EFF-001 under `strict`, while two engines emitted a hardcoded `undeclared: []` — a green conformance
answer from a check that never ran. One of them said so in a source comment: *"analyze-only … no
DI-conformance pass — kept in the wire shape for cross-engine schema parity."*

**That admission is the load-bearing part, and it indicts a CHECK rather than an engine.** A schema-parity
comparison is what made emitting the constant look like the conforming thing to do. A parity check over an
OPTIONAL field manufactures exactly this: agreement on shape purchased with a claim nobody computed. So a
conformance suite MUST NOT require these three of an engine, and MUST reject `[]` from an engine that
computed nothing — which is the falsifiable form of this rule.

**Deserialization is half the contract.** A reader that defaults an absent array to `[]` destroys the
distinction the producer just made, so *"absent"* must survive into the consumer's own model (an
`Option`/nullable, not a defaulted empty vector). A producer omitting the field and a reader defaulting it
back is the same claim with extra steps.

⟨0.24⟩ **EVERY ORDERING — in a report and in a query output — MUST be locale-INDEPENDENT.** Sort by
Unicode code point (equivalently UTF-8 byte order). A **locale-sensitive** comparator is forbidden:
JavaScript's `String.prototype.localeCompare` and `Intl.Collator`, ICU collation, `strcoll`, and anything
else that consults an ambient locale. Such a comparator makes the SAME input produce a DIFFERENT byte
sequence on a different machine, or on the same machine under a different environment.

This clause is written because the whole document already depends on it without saying so. Every
compatibility argument here is phrased as *"a default report is **byte-identical**"* — a claim that is not
even checkable if two runs of one version can disagree. The deterministic effects-fingerprint rests on the
same assumption. It was an unstated premise of a dozen normative claims, which is the same condition that
produced the §2.2 sidecar convention and the `--class` filter: load-bearing, relied upon, unwritten.

Measured: one engine used `localeCompare` at **seven** call sites, one of them ordering the coverage ledger
*inside the emitted report* rather than in a query output — so report bytes, not just presentation. The
reference engine sorts the corresponding query output by byte order, so the two already disagreed.

**ASCII DOES NOT PROTECT YOU HERE, and that is what makes this clause separate from the collation one.**
The collation rule can be reasoned about as "our identifiers are ASCII, so UTF-16 and code-point order
agree" — true, and it is why that rule's risk is latent. **Locale collation reorders pure ASCII.** Observed,
same build, same unchanged tree, differing only in the environment: under `LC_ALL=C` the ledger reads
`[tpad, zpad]` and under `LC_ALL=et_EE.UTF-8` it reads `[zpad, tpad]` — Estonian collates `z` between `s`
and `t`. Two different report md5s. Danish breaks a second all-ASCII pair (`aa` sorts as `å`, so `aardvark`
follows `z`). The keys in that ledger are lowercase npm package names: **exactly the case the "ASCII is
unaffected" argument declares safe.**

A CONTROL FOR THIS MUST BE CHOSEN AGAINST A LOCALE THAT ACTUALLY REORDERS ASCII. Turkish is the intuitive
choice — the dotless-i is the famous case-folding break — and it **does not discriminate here**: Turkish
inserts its extra letters *between* the ASCII ones, leaving pure-ASCII relative order unchanged. A
`C`-versus-`tr_TR` experiment on ASCII keys returns "no difference" and licenses the conclusion "latent, not
observed", which is false. Use `et_EE` or `da_DK`.

Note this is **separate from, and orthogonal to, the collation rule** for a single joined field. They are
different obligations and it is worth being exact about which binds where, because the clause as first
written could be read two ways:

- **This rule (locale-independence) binds EVERY ordering**, in every report and every query output. It is
  satisfied by any environment-independent comparator — including UTF-16 code-unit order, which is what a
  bare `Array.sort` or `String.compareTo` gives. Deterministic is the whole requirement.
- **Code-point order is required ONLY where a field's collation is pinned** (§3.1's `viaDispatchOn`). It is
  the stricter obligation and it is deliberately narrow, because the cost of a cross-engine byte difference
  is only felt where something is compared across engines — and `analyzed.digest`, the field most likely to
  invite that, is defined as *within-engine*-comparable precisely so it is not.

Read the other way — code-point mandatory everywhere — this clause would make a bare `.sort()` in any
UTF-16 language non-conformant on every array in the report, which is a sweeping obligation the per-field
mandate in §3.1 shows was not intended. Measured on the engine where this was found: seven sites were
locale-sensitive and were fixed; roughly seventy more use UTF-16 order, of which about ten write report
bytes from user-derived strings. **Those ten are conformant** — deterministic, environment-independent, and
comparable within their producer. An implementation can satisfy the collation rule and violate this one, and
one did; the converse is fine.

⟨0.23⟩ **EVERY VALUE IN THIS FILE IS AN ARRAY OF STRINGS, and that is a constraint on WRITERS.** A
producer MUST NOT write a value of any other type, and MUST NOT write a metadata key as the file's *only*
key. Metadata about the map goes under a key beginning `@`, the reserved namespace; readers SHOULD ignore
`@` keys, and MUST tolerate — skip, not abort on — any value that is not an array.

*This was first written the other way round, as a requirement on readers, and that is the mistake the rule
now records.* A reader requirement obliges every already-deployed reader to have been updated, which is
precisely what did not happen — **twice, for one key**. candor-java added `"@superclass"` with an object
value on the argument that "a reader skips any non-array value": true of one of its own readers, false of
the second (`getAsJsonArray()` threw, its own `catch` swallowed it into "no sidecar", and the **whole**
hierarchy was discarded with no diagnostic — 539 tests green through it), and false of the **third**, in
another language, which nobody had looked for. candor-rust's `candor-query::load_hierarchy` deserializes
the file as `BTreeMap<String, Vec<String>>` in one typed call and drops it entirely when that fails; a
strictly typed reader has no per-entry loop and *cannot* skip anything. Measured on 7 real chained JVM
targets: **0 of 18 sidecars parsed there** while the object value was being written. Separately, writing
the key unconditionally turned an empty `{}` into `{"@superclass":{}}`, and two consumers take the precise
frontier iff the map is non-empty (candor-ts `Object.keys(h).length > 0`, candor-rust `!hier.is_empty()`) —
so a key carrying nothing withdrew a disclosure in a different engine. Both failures are impossible under
the writer-side rule and neither was prevented by the reader-side one.

The one metadata key defined so far is candor-java's `"@superclass"` — a **flat array** `[type,
superclass, type, superclass, …]`, type-sorted, naming for each type the one supertype that is its
**superclass**, the fact a sorted list of supertypes throws away. JVM and Swift method resolution put the
whole class chain ahead of any interface/protocol at any depth (JLS 15.12.2.5 / 8.4.8), so a consumer
walking a *dependency's* chain cannot apply that rule without it. Flat rather than delimited because a JVM
binary name may legally contain almost any character. Its **presence** is what says the kinds are known —
including when it carries no pair, which is the positive fact "no type here has a superclass" — so it is
written whenever the sidecar names any type at all, and omitted only when the sidecar is empty, where a
consumer reads it zero times. A sidecar without it MUST keep whatever order the reader used before, never a
guess: reading an unmarked list as all-interfaces puts a real superclass below an interface, which is the
silent under-report the ordering exists to prevent. An engine whose language has no such rule needs neither
the key nor the marker.

⟨0.24⟩ **RULED — see §3.1: an EMPTY sidecar, an ABSENT one and an UNPARSEABLE one are the SAME INPUT, and
all three take the over-listing fallback.** This paragraph previously read "NOT YET RULED", describing three
engines and two answers and deferring "pending a four-way ruling rather than a unilateral edit". The ruling
was then made in §3.1 as a MUST — and it *forbids* the behaviour this paragraph listed as one of the two
live options (gating on the file's absence, so a sidecar parsing to `{}` is honoured and collapses the
frontier). An implementer reading only this section would have preserved a behaviour the document elsewhere
prohibits. Left standing for several hours after the ruling; caught on review. The reasoning is in §3.1 —
`{}` cannot distinguish "no type has a supertype" from "the pass never ran", so the subtype test is
unanswerable and an unanswerable condition is disclosed, never scored as failed.

## 3. Modes

An implementation SHOULD support:

- **audit** (default): report each function's `inferred` set; no judgement.
- **JSON**: write the §2 report to a file for machine/agent consumption.
- **conformance**: given functions that *declare* capabilities (§5), flag mismatches (§6). MAY be
  scoped to a module/path prefix for incremental adoption.
- **no-ambient**: flag any *direct* use of ambient authority (an effect performed without holding a
  matching capability), pushing toward a capability-passing / capability-secure style.
- **baseline guard**: diff against a saved report and flag functions that *gained* an effect.
  ⟨0.16⟩ Existence is keyed on the **baseline callgraph sidecar when present** (§2.2 — it lists
  pure leaves, which reports omit): a function in the baseline callgraph whose baseline effect set is
  therefore ∅ and which now performs ANY effect is a GAIN violation — the formerly-pure→effectful
  transition is the sharpest supply-chain shape and must not read as exempt "new code". Without the
  sidecar, existence degrades to report-only (a formerly-pure fn reads as new — the pre-⟨0.16⟩
  semantics); a PRESENT-but-corrupt sidecar fails closed like a corrupt baseline (a broken sidecar
  must not silently narrow the guard). This is the `gains` `origin` existence rule (§3.1 ⟨0.12⟩)
  applied to the scan-time ratchet. **The ratchet (exit 1) fires only on gaining a REAL boundary
  effect**; a gain of `Unknown` ALONE — the §4 trust marker, not an effect (`pure` policies already
  exclude it) — is DISCLOSED as advisory (a note, exit unchanged), never a hard failure. Rationale
  (2026-07-16 corpus test, SOUNDNESS-LOG): on real dependency bumps an Unknown-only gain is dominated
  by noise — syntactic dispatch-resolution variance, and unstable synthetic-member identity (a JVM
  anonymous class's positional `$N` differs across versions) — so ratcheting on it would break CI on
  innocuous bumps. A gain that includes any real effect still fails; the disclosure of the Unknown-gain
  keeps the "say what changed" ethos without the false alarm.
- **policy**: enforce declared effect boundaries (e.g. "the `domain` layer must perform no `Net`/`Db`",
  "module `parse` must be pure"); flag any function that *transitively* violates one. The architectural
  invariant an agent can't see from a local edit.
- **risk** (optional, **heuristic**): flag an effect whose argument derives from a function parameter
  (e.g. `fs::read(path_from_param)`) — the injection class (path traversal, command injection, SSRF).
  Unlike the others this is *advisory and imprecise*: a syntactic, intra-procedural nudge that over- and
  under-flags; it MUST NOT gate. An implementation MAY support it; if so it MUST document its limits.
  (Enabled by the `taint` config key / `CANDOR_TAINT` env var, §3.4 — two names, one mode: `risk` is
  the mode, `taint` is its switch.)
- **containment** (optional): a diagnostic over the report — for each *boundary* effect, how concentrated
  it is in one architectural layer (§6.1). With a baseline it becomes a *ratchet* (AS-EFF-010). It is
  deliberately **not** a single "score"; see §6.1.

### 3.1 Read-only queries (SHOULD)

A written report (§2) plus its call-graph sidecar (§2.2) answers structural questions WITHOUT re-analysis.
An implementation SHOULD expose them so an agent reaches for them in one cheap call instead of grepping:

- **show `<fn>`**: a function's effects (own/direct vs inherited).
- **where `<Effect>`**: which functions perform an effect (direct sources vs transitive inheritors).
- **callers `<fn>`**: the **blast radius** — every TRANSITIVE caller of `<fn>` (works for ANY function,
  including a still-**pure** one) — *who is affected if you change it*. ⟨0.7⟩ With the **`--include-unknown`**
  modifier it additionally discloses the *unresolved-dispatch frontier* (`possibleViaUnknownDispatch`, below):
  callers that reach `<fn>` only through an unresolved `dispatch:` — a disclosed lower-bound, never asserted.
- **map**: a module → effects overview.
- **diff `<current>` `<baseline>`**: the per-function effect delta (gained / lost) between two saved
  reports: the current one and the baseline, in that argument order.
- **gains `<current>` `<baseline>`**: same two inputs; the package-level **gained-capability alarm** — the effects present now but
  absent from the baseline (`gained`), each with the functions introducing it (`byFunction`). The
  supply-chain view of `diff` (§5.1): a dependency release that quietly grew `Net`/`Exec` is exactly
  what this surfaces, and a stable surface raises no alarm (`gained: []`). *(Recorded ⟨0.8⟩ as a
  documentation catch-up: the engines have shipped it and the conformance suite has pinned its shape
  since the ⟨0.5⟩ query parts — the §2.1 and §5.1 references resolve here.)* ⟨0.12⟩ Each `byFunction`
  entry carries **`origin`**, separating the two alarms a bare gain conflates: a fn that **existed at
  the baseline** and gained the effect (shipped pure, now does `Net` — the supply-chain *attack*
  signal) vs a **new** fn that performs it (a feature). Reports omit pure functions (§2), so baseline
  existence is keyed on the **baseline callgraph sidecar**: `"existing"` = in the baseline report OR a
  baseline-callgraph node (caller or callee); `"new"` = in neither; `"unknown"` = absent from the
  baseline report while the baseline callgraph is absent OR incomplete (a matched sidecar failed to
  load — a partial graph must not downgrade an existing-fn gain to a feature-looking "new") —
  existence undecidable, disclosed rather than guessed (§4). The vocabulary is closed (those three values); the human/TSV output is unchanged
  (`origin` is the machine surface).
- **reachable / path / impact**: the runtime effect surface (union over entry points), an effect's
  provenance (the call chain to its source), and the blast radius from entry points. ⟨0.11⟩ `path`'s
  default output is the human-readable indented chain (it is the command the §3.1 *surprising-reach*
  surfaces hand to a cold reader); `--json` selects the pinned shape below.
- **tour `[<N>]`** ⟨0.11⟩: the N (default 10) most *surprising* transitive reaches in the report — each a
  benign-named function that inherits a high-salience effect from hops away — with a ready-to-run
  `path` command per entry. The on-demand form of the scan-time opener (below); both MUST rank with the
  same heuristic so they cannot disagree. `N` MUST be a positive integer: `tour 0` is a usage error
  (exit 2), because an empty tour over an effectful package would read as an all-clear.
- **blindspots** ⟨0.6⟩: the Unknown SOURCES — the calls the engine genuinely could not resolve (each
  carries `unknownWhy` — reflection, an over-wide dispatch, a fn-pointer), ranked by how many functions
  transitively inherit `Unknown` through each. The actionable inverse of a widely-propagated `Unknown`: a
  report can read 60% `Unknown` from a dozen root causes — this names those dozen, so they can be declared
  (§5.1), resolved, or accepted, instead of the smear reading as analysis failure.
- **parsepolicy `<file>`**: the engine's canonical parse of a §6.2 policy file, as JSON. Not a user
  workflow: it makes the grammar *diffable* — the cross-impl conformance suite feeds every engine
  that exposes it the same policy text and asserts the parses agree, which is what keeps one policy
  file meaning the same gate in every language. An implementation that enforces any policy mode
  SHOULD expose it (an enforcer without it is still exercised through the applied `--policy`
  verdict differentials, but its grammar is only indirectly diffed).

  ⟨0.24⟩ **`parsepolicy` MUST NOT REFUSE A POLICY IT CAN READ AND CANNOT HONOUR. It REPORTS that parse,
  including what it could not honour.** ⟨0.24⟩ *This was first written absolutely, and all four engines
  correctly exit 2 on a MISSING file — so as written every engine was nonconformant and the conformant
  behaviour would have been harmful: exit 0 with an empty rule list is the silent-empty this document
  forbids everywhere else. A file with no parse to report is not the case this clause is about.*
  When ⟨0.24⟩ made an unrecognised policy token a policy error (§6.2), two engines applied it in the
  PARSER and `parsepolicy` began exiting 2 on the conformance battery — which contains such tokens
  deliberately. The suite **halted at PART 4**, so one ruling took the whole differential offline.

  The refusal belongs to the **gate**, which must not enforce a policy it cannot honour as written. It does
  not belong to the **witness**, whose entire job is to answer *what did this engine make of my policy?* —
  a question that is most valuable exactly when the answer is "not what you meant". A diagnostic that
  declines to explain the thing being diagnosed has inverted its purpose, and it would remove the four-way
  pin on token handling at the one input where the engines are most likely to differ.

  So: `parsepolicy` emits its parse **and an `errors` list**, and exits 0. Each entry is
  `{ "kind", "token", "accepted", "rule", "message" }` — `kind` names the vocabulary
  (`reason-class/alias`, `Net destination-class`, …), `token` the thing not recognised, `accepted` the
  admissible set, `rule` the source line verbatim, `message` the human sentence. `errors` is **omitted when
  empty**, so a clean parse stays byte-identical and the existing four-way `deny`/`allow`/`forbid`
  comparison is untouched.

  ⟨0.24⟩ **`errors` CARRIES EVERY LINE THE ENGINE DID NOT HONOUR AS WRITTEN — not only unrecognised
  tokens.** Measured on the reference engine the moment the list existed: `parsepolicy` reported **2** token
  errors while its stderr reported **8 further policy lines dropped entirely** — an unknown effect name
  (`deny notaneffect`), an `allow` on an effect that takes no operand, malformed `forbid` lines, an unknown
  rule kind. None appeared in the machine output. **A dropped rule is the limit case of "silently rewritten
  into a different policy": the rewritten policy is the one without that line**, and it is a bigger rewrite
  than a narrowed filter, not a smaller one. The witness was disclosing the two cases that happened to
  prompt the clause and staying silent on the four that did not.

  This is deliberately **additive to the witness and silent about the gate.** Whether a dropped rule should
  also make the GATE refuse is a harder question and stays open: `deny Net Exex app` cannot be told from a
  legitimate scope by the parser, so treating unknown effect names as errors is a GRAMMAR change rather
  than a token change. Reporting what was dropped requires no such decision, and until it is reported
  nobody can measure how often it happens. The unrecognised token MUST appear in that output rather than being
  silently dropped from the parse — the pre-⟨0.24⟩ behaviour was *drop with a warning*, and a diff that
  cannot see the difference between "dropped" and "rejected" cannot pin this rung at all.

These bind **engines, not consumers**: a consumer that only reads the JSON report is fully conformant.
For an engine that exposes them, the query names and JSON shapes ARE part of the versioned contract (a new
query shape is a minor bump, §8's own rule; 0.6's `blindspots` moved the version). An implementation
SHOULD keep query **names and output shapes consistent across languages**, so an agent uses a report from any language identically; the cross-language conformance suite
verifies this. **Name-query matching SHOULD follow the same ladder in every language**: exact match, else
segment-suffix (the query sits after a path-separator boundary: `Pricing::quote` or bare `quote` matches
`pricing::Pricing::quote`, never `quote_bulk`), else substring, resolved at the best tier any candidate
reaches. Substring-widening a precise query silently inflates a blast radius (a measured red-team caught
`whatif` seeding from a name-cousin), so the more precise tier always wins.

When a query emits JSON, it SHOULD use these shapes (the field a consumer parses is the same in every
language; only the function-name *value* is language-natural — `a::b` vs `a.b`):

```text
show     [ { "fn", "inferred":[…], "direct":[…], "unresolved":bool, "fs"?:[…], "hosts"?:[…] } ]
where    { "effect", "directly":[fn…], "inherited":[fn…] }
callers  { "of":[fn…], "direct":[fn…], "transitive":[fn…] }
         // ⟨0.7⟩ with --include-unknown, also: "possibleViaUnknownDispatch":[ { "fn", "viaDispatchOn" } ]
map      { "<module>": { "effects":[…], "functions":int } }
diff     { "changes": [ { "fn", "gained":[…], "introduced":[…], "inherited":[…], "lost":[…],
           "status": "changed"|"new"|"removed" } ], …optional provenance fields }
gains    { "gained":[Effect…], "byFunction":[ { "effect", "fn", "origin":"existing"|"new"|"unknown" } ], …optional provenance fields }   ⟨0.12⟩ origin
reachable { "entryPoints":int, "effects": { "<Effect>": { "count":int, "via":[fn…] } } }
path      { "effect", "fn", "path":[ { "fn", "loc", "source":bool } ] }
tour      { "reaches":[ { "effect", "fn", "hops":int, "loc", "score":int, "source" } ] }   ⟨0.11⟩
impact    { "fn", "affectedCount":int, "affected":[fn…], "entryPoints":[ { "fn", "inferred":[…] } ] }
blindspots { "sources":[ { "fn", "why":[…], "reaches":int, "affected"?:[fn…] } ], "totalUnknown":int }   ⟨0.6⟩
```

`show` carries the report's optional refinement fields (`fs`/`hosts`/…) only when the engine resolved
them (§2 omission rules apply); the four required fields are always present. `map` buckets by module —
a function with no module beyond the root goes to `(root)` (§6.1), never its own pseudo-module. In
`diff`, a gained effect is `introduced` if it is in the function's own `direct` set, else `inherited`
from a callee (the source vs the blast radius); the envelope MAY carry additional provenance fields
(e.g. baseline/engine versions), which a consumer must tolerate. A `diff` whose current or baseline
input names **no report** MUST fail loudly rather than read as an empty report — a typo'd current path
would otherwise show zero gains (silently passing a gained-effect gate), and a typo'd baseline would
show every effect as newly gained.

`impact` is the backward dual of `reachable`: `affected` is the blast radius itself — every effectful
unit that transitively calls the target (the same names `affectedCount` counts, sorted) — and
`entryPoints` are the runtime roots downstream, each with its effect set so a consumer sees *what*
surfaces, not just that something does. Emitting only the count forces an agent to re-derive the list
it just computed, so the list is required. `path` is the forward dual: a shortest call chain from `fn`
to the nearest unit performing `effect` **directly** (`source: true`), each step carrying its `loc`;
an empty `path` is the correct "no local source on a path" answer (the source is cross-boundary,
framework-synthesised, or `Unknown`), never an error.

**The surprising-reach surface** ⟨0.11⟩ (`tour`, and the scan-time opener). An engine SHOULD surface,
at scan time, the single most surprising transitive reach in what it just analyzed — a mundane-named
function that inherits a boundary effect from hops away — as one line with a ready-to-run `path`
command; `tour` is the same ranking on demand, top-N. The heuristic is deterministic and shared (no
model, no network): `score = salience × benignity × hops-factor × crossing`, where **salience** classes
the reached effect (`Net`/`Exec`/`Db`/`Ipc` high; `Fs`/`Env` mid; `Clock`/`Log`/`Rand` and everything
else **zero** — a mundane reach is never presented as surprising), **benignity** prefers a function
whose leaf name reads effect-free (a `load`/`settings`/`get…` lexicon) and excludes names that already
announce the effect (`fetch`, `exec`, `write…`), **hops-factor** rewards distance to the source, and
**crossing** rewards a module boundary on the chain. Functions in **test contexts are excluded** (a
module segment named `test`/`tests`, or the language's test-file/`…Tests`-type idiom — never by the
leaf name, which would hide a production `test_connection`). When nothing clears the bar the correct
output is the explicit fallback ("nothing hidden") — a manufactured surprise is worse than none. The
cross-impl suite pins the surface four-way: the same fixture yields the same top reach in every engine,
the salience floor holds, and test contexts stay excluded.

**A located report that yields no trustworthy functions MUST fail loudly** ⟨0.11⟩ (exit 2, the failure
disclosed), never read as an empty report: a report file that is *found* but cannot be parsed — or
parses to the wrong shape (a `null`/scalar document, a bare array of junk entries, a non-array
`functions`) — is corrupt input, not an effect-free package. Returning an empty answer over it is the
§4 false all-clear: `tour` would print "nothing hidden", and a policy gate over the empty `map` would
pass. A **well-formed** report that legitimately lists zero functions (`functions: []`) remains a valid
pure report and MUST NOT trip this rule. (The twin of §3.1's no-report-loud rule for `diff`, and of
§3.3.1's rule that a locator matching no files fails loudly — this one covers *found-but-corrupt*.)

`blindspots` ⟨0.6⟩ is the *source* view of `Unknown`: each entry is a unit whose OWN body has an
unresolvable call (so it carries `unknownWhy`, required on such a unit — §4), with `reaches` the size of
its `Unknown` blast radius (the transitive callers that inherit `Unknown` through it; blast radii may
overlap between sources) and `affected` that list (optional, like `impact`). Sorted by `reaches`
descending — the root causes that poison the most functions first. A unit whose `Unknown` is purely
inherited (no `unknownWhy` of its own) is NOT a source and is excluded; `totalUnknown` is the report's
total count of units carrying `Unknown` — the surface these sources explain. The point is to turn a
high-`Unknown` report from "the analysis failed" into a short, ranked worklist of real blind spots.

⟨0.24⟩ **`gate --report <locator> --policy <file>` — apply a policy to an EXISTING report, with no scan.**
Every other route into the gate recomputes the effect set from source (`scan --policy`), or reports only
what a hypothetical *introduces* (`whatif`: a report already carrying `Net` under `deny Net` returns
`ok: true`, by design). So the gate has never been reachable as a **function of a given signature**. Exit
codes and verdict shape are exactly `scan --policy`'s; the only difference is where `S` and `D` come from.

Two things this buys, and the second is why it is a MUST rather than a convenience.

*It is the supply-chain verb.* Gating a dependency's published report is the operation an adopter actually
wants and could not previously express without re-analysing code they do not have.

*It makes the code-implements-spec direction testable at all.* The gate was previously exercised only
end-to-end, through the classifier — so a defect in the **gate** and a defect in the **classifier** were
indistinguishable from any test, and no test could isolate either. That is not a hypothesis about how
defects hide here: the ⟨0.24⟩ §6.2 divergence was a *contract-versus-model* defect that every engine
implemented faithfully and no end-to-end test could have localised. With this verb, conformance can feed
each engine a signature the reference model has already judged and compare verdicts directly — extending
the model check from "the model is internally monotone" to "each ENGINE agrees with the model".

An engine MUST NOT re-derive, widen, or re-classify anything while serving this verb: it reads `S` and `D`
from the report as given and applies §6's matching. In particular a report entry that is **absent** is
absent — the ⟨0.21⟩ purity claim — and MUST NOT be back-filled from a callgraph sidecar or a chained dep.
The verb's whole value is that it is a pure function of the report and the policy, and an engine that
improves the input has destroyed that.

**SHAPE** (reference implementation, candor-java): `gate --report <locator> --policy <file> [--json]
[--gate-json <file>]`. It is a **query verb**, not a scan flag, so it inherits §3.3.1's grammar unchanged —
the same locator rules and discovery fallback, the same `CANDOR_POLICY` fallback, the same exit-2 on an
unreadable policy, and **no positionals**. Exit codes are `scan --policy`'s exactly: 0 / 1 / 2. **`--json`
is `--gate-json -`**, deliberately: on a scan `--json <file>` writes the *report*, and there is no report
to write here, so the verb's machine output is the verdict. A second meaning for `--json` would be the one
place a consumer could tell the two routes apart.

**EQUIVALENCE IS THE ACCEPTANCE TEST, AND IT IS BYTE-LEVEL.** For any report a scan produced,
`gate --report <it> --policy P` MUST produce a `--gate-json` document **byte-equal** to `scan --policy P`'s
⟨0.24⟩ **for every policy the verb evaluates IN FULL — and that condition was missing, so as written every
conformant engine violated this MUST.** A policy containing `forbid` or `allow` cannot satisfy it: the scan
route evaluates AS-EFF-009 from the source it is looking at, and this section REQUIRES the gate route to
refuse it for lack of a surface. Measured on candor-ts, `deny Fs` + `forbid src.app -> src.lib`: scan exits
1 with 4 violations, gate exits 1 with 2 plus `unevaluated`. Equality binds the EVALUATED PROJECTION —
identical bytes over the rules both routes actually decided. The sentence "reaching equivalence required
exactly three refusals" already presupposed this scoping without stating it
— `analyzed.count`, `reasonClass`, `netClass` and the coverage advisory included. Measured on the reference
engine over 25 rows and two corpora (a 970-function report against 13 policies, up to 113 violations, plus
a fixture making the scoped arms non-vacuous). Anything less than byte-equality lets the two routes drift
into two gates.

⟨0.24⟩ **ANSWERABILITY: a rule whose EVIDENCE THE WIRE DOES NOT CARRY MUST BE REFUSED (exit 2), never
evaluated.** Reaching equivalence required the refusals below, each found by measurement and each
FAIL-OPEN if approximated instead. ⟨0.29⟩ *This list read "exactly three" and was a CLOSED enumeration —
so when `only` was added it had nowhere to be admitted, and §6.2's `only` clause pointed back at a list
that did not contain it. A rule stated as a count of its members is a rule that silently stops being true
the next time the domain grows; the count is gone and the members are what carry it.*:

- **`forbid A -> B`** — a call-graph dependency rule. `calls` is *effect-relevant* only, so a crossing into
  a wholly pure unit is invisible in the report. Unanswerable.
- **`allow <E> …`** — the AS-EFF-008 literal allowlist. Its surface-completeness marker **is not
  guaranteed** to ride the wire, and the refusal is required of every engine **regardless of whether a
  given one happens to carry it**. ⟨0.24⟩ *This clause first said the marker "does not ride the wire", flatly.
  That is FALSE for at least one engine: candor-rust emits a per-entry `incomplete` field, which §2's
  chained-join clause names, so it could answer `allow` from a report. It refuses anyway, and correctly —
  **an engine that answers a question its three siblings refuse has SPLIT THE VERB**, and `gate --report`'s
  whole value is that one report and one policy give one verdict everywhere. Uniform refusal is the
  requirement; the wire's contents are not the reason, they were merely the first reason noticed.* The reference engine's first attempt *reconstructed* it for `Net` from `netClass ∋ unknown-host`;
  the equivalence test refuted that in one run, because the same token also names a merely **unrecognised**
  host, so it flagged two functions the scan passes.
- ⟨0.29⟩ **`only <A> -> <B> …`** — the permission form, and unanswerable for a STRICTER reason than
  `forbid`: `forbid` asks whether ONE named crossing is present, `only` asks whether EVERY reached scope
  is on a list, so a report that omits a crossing does not merely under-report — it turns a green into a
  claim of COMPLETENESS. A route that discloses it MUST also REMOVE it from the evaluation.
- **A CLASS-SCOPED `deny` whose scoping datum is an ABSENT OPTIONAL FIELD.** Measured, and this one is a
  live fail-open rather than a theoretical one: `deny Net[unknown-host]` over a `Net`-bearing entry with no
  `netClass` matched against an empty set and returned **exit 0**, where the bare `deny Net` returns 1 —
  *an absent optional field silently un-scoping a fail-closed security gate*. Same shape for
  `deny Unknown[dispatch]` over an entry whose `Unknown` is inherited and whose `calls` is absent: the
  transitive class fixpoint is uncomputable, so every scoped filter tolerates while only bare `Unknown`
  fires.

⟨0.24⟩ **REFUSE ONLY WHEN THE ABSENT DATUM COULD CHANGE THE ANSWER — the refusal is MINIMAL, not coarse,
and monotone denial is what makes that safe.** A class-scoped `deny` is not unanswerable merely because
`calls` is missing. The class set only ever GROWS as more evidence arrives (§6.2: a reason is
*contributed*, never retracted), and `Reject` is upward-closed in it (Lemma 2). So:

- if the classes determinable from the entry ALONE already intersect the filter, **the rule FIRES** —
  whatever the missing `calls` would have added could only have added more matches, so the absent datum
  cannot change the verdict. Answer it.
- only if it does NOT yet fire, and the missing datum could still make it fire, is the question genuinely
  unanswerable. **Refuse that.**

Measured on candor-swift: `gate --report` refused the ⟨0.24⟩ CONTRIBUTES counterexample — a function whose
DIRECT `Unknown` carries no reason, gated `deny E Unknown[unresolved]`. That refusal is **over-broad**: a
reasonless direct `Unknown` contributes `unresolved` from the entry alone, with no transitive step, so the
rule fires and the answer is certain. Exit 2 there is not wrong in the fail-closed sense — it is a *worse*
answer than the correct one, and a verb whose value is being a pure function of its input should not
decline questions it can answer.

This is the first place in this document where the monotone-denial property is used to *do* something
rather than to be preserved. A gate that knows its predicate is upward-closed can distinguish "I cannot
tell" from "more information could not change this", and only the first is a refusal.

The refusal's **granularity differs by cause, and that is deliberate**: whole-policy for `forbid`/`allow`
(enforcing the answerable half and exiting 0 would be gateless-green), and per-(rule, function) for the
scoped case, so a scoped rule whose own matches carry their evidence still evaluates. The message MUST name
the offending rule kind — and for the scoped case the exact `deny` line and function — and MUST carry the
remedy (gate at scan time). Refusing costs nothing on a self-produced report: `netClass` is emitted for
every `Net`-bearing entry and is floored at `unknown-host`, and an inherited `Unknown` always has its callee
in `calls` (that callee carries `Unknown`, so it is effectful).

⟨0.24⟩ **THE FOURTH CHANNEL: POLICY VOCABULARY ANCHORS AT THE POLICY FILE, ON BOTH ROUTES.** §3.1's
MUST NOT names three channels through which an effect must never enter a gate that its report does not
carry. A review found a fourth that no engine's test covers: **`.candor/config`'s `unknown-alias`.**
Measured four-way, an alias file placed beside the POLICY moves the verdict 0→1; the same alias in the cwd
alone does not. Three consequences, and only the third is a defect:

- `CANDOR_CONFIG` alone can flip the verdict, so the verb is **not literally a pure function of
  `(report, policy)`**. That is tolerable — an alias is policy *vocabulary*, and vocabulary is part of the
  policy — but the claim in this section must be stated as the closure, not the pair.
- Config discovery **walks parent directories**, so an alias file anywhere ABOVE the policy participates.
  Ambient, and invisible in the output.
- **The two routes anchor differently.** All four gate verbs anchor at the **policy file's** directory
  while all four scan routes anchor at the **target**. With the policy stored outside the scan target,
  `scan --policy P` and `gate --report R --policy P` can expand the same rule differently — **so
  §3.1's byte-equality MUST is breakable by a file that is neither the report nor the policy.** That is
  the defect, and it is uniform.

**RULING.** `unknown-alias` — and any future key that supplies POLICY VOCABULARY rather than scan
configuration — resolves **relative to the `--policy` file's directory on BOTH routes** when `--policy` is
given explicitly. Vocabulary travels with the policy that uses it; target-scoped keys (`deps`,
`net-partner`, scan settings) keep anchoring at the target, because they describe the thing being scanned.
This makes byte-equality hold **by construction** rather than by the two routes happening to be pointed at
the same directory, and it is the only anchor under which the equality MUST is not hostage to where the
operator filed the policy.

⟨0.24⟩ **AND THE AMBIENCE MUST BE DISCLOSED.** If a config file supplied vocabulary that participated in
the verdict, the `--gate-json` document MUST name that file. A verdict changed by a file the operator
cannot see named in the output is the ambient-input failure this whole format exists to refuse; the remedy
is the same one used everywhere else here — not to forbid the input, but to make it impossible for it to
act unnamed. **The three documented baits MUST gain this fourth**, on all four engines.

⟨0.24⟩ **A TYPO'D EFFECT NAME DELETES THE RULE, SILENTLY, FOUR-WAY GREEN — and the token rule stopped at
the bracket for no reason its own argument supports.** Measured on all four engines:

    deny Nett app             ->  rust 0  ts 0  java 0  swift 0     the rule is DELETED, the gate is green
    allow Nett host.example   ->  rust 0  ts 0  java 0  swift 0     the certification silently vanishes

The operator reads an armed `deny Net`; there is no gate at all. This document already calls a dropped rule
*"the limit case of silently rewritten into a different policy… a bigger rewrite than a narrowed filter,
not a smaller one"* — and yet the bigger rewrite was warning-only while the smaller one is exit 2. **That is
the fourth time a clause has been scoped to the position its defect was found in rather than the condition
its reasoning names.**

The grammar defence for leaving this open is real but NARROWER than I took it to be. `deny Net Exex app`
genuinely cannot be told from a legitimate scope by the parser. But:

- **`allow`'s effect position is a fixed, closed FIVE-token set** — `Net`, `Exec`, `Fs`, `Db`, `Llm`.
  ⟨0.24⟩ **I wrote FOUR here, and that error had the opposite sign to the six before it: it would have made
  the engines REFUSE A VALID POLICY.** `allow Llm api.openai.com` is the privacy-manifest use case, all
  three measurable engines accept it today, and this clause would have turned it into exit 2. candor-java
  measured it while implementing and reported rather than complying — which is the only reason a fail-open
  fix did not ship a fail-CLOSED regression on a real policy. **A closed set is a load-bearing claim in
  BOTH directions: too wide lets a typo through, too narrow rejects working policy** — and I had only been
  checking one of those. `allow Nett …` is still unambiguously a typo,
  with no scope reading available. It MUST be a policy error.
- **A `deny` whose effect list ends up EMPTY after scope-splitting is malformed under either reading** —
  there is no legitimate policy it could be — so refusing it loses nothing.

Both are exit 2. What stays open is only the genuinely ambiguous middle: a `deny` with at least one valid
effect and an unrecognised trailing token that MIGHT be a scope. `parsepolicy` reports it either way
(§3.1), so the operator can always see it.

⟨0.24⟩ **CORRUPTION IS JUDGED PER KEY *ROLE*, NOT PER RULE — and the decisive argument is that
trustworthiness cannot depend on the question you asked.** A review measured the engines split on a corrupt
`netClass: 1` sitting beside a well-formed `deny Fs` that fires: **rust 2, ts 2, swift 2, java 1.** Both
readings were conformant under `01d5c6b`, which fixed the DIRECTION of the boundary and left its GRANULARITY
underivable. The two candidates are *consulted-keys* (refuse only if a rule read the corrupt key — java) and
*producer impeachment* (a corrupt key impeaches the document — the other three).

**Consulted-keys is wrong, and not by preference: it makes the same report trustworthy under one policy and
untrustworthy under another.** Whether a document's bytes mean what they say is a property of the document,
not of the query. Under that reading an operator could make a corrupt report gate green by narrowing their
policy — the gate would get *quieter* as the input got *worse*.

But producer impeachment is not "any bad byte refuses" either, and this document already ruled otherwise
without noticing it was ruling: candor-rust relaxed its corrupt-key refusal for a `coverage` ledger whose
`calls` field it could not read, because **no verdict reads it** — and that was correct. The line is the
key's ROLE:

- **SIGNATURE keys** — `functions`, `inferred`, `direct`, `unknownWhy`, `netClass`, `analyzed`,
  `unanalyzed` — carry the claim. One unreadable among them means the document's claim cannot be trusted,
  whatever this particular policy happens to ask. **Refuse.**
- **DECORATIONS** — a coverage ledger's detail, `loc`, and `hash` ON A SINGLE-REPORT ROUTE — carry no claim
  a verdict reads. Withhold the decoration, disclose it, and answer. Refusing there drops a hedge to be
  strict about ornament.
  **⟨0.32⟩ `hash` IS NOT A DECORATION WHEN SEVERAL REPORTS ARE MERGED.** §2.2 requires a consumer to join
  across reports by `hash` and never by bare `fn`, so on a multi-report route the join — and therefore
  every accumulator the verdict is computed from — depends on it. There it is a SIGNATURE key: a report
  set in which any entry lacks `hash` cannot be merged soundly, and the run MUST refuse rather than fall
  back to names. This split is deliberate and narrow: one report needs no join, so `hash` really is
  ornament there, and the ⟨0.24⟩ rule above is unchanged for that case.

So the three engines are right on `netClass` and rust was right on `coverage`, for one reason rather than
two.

⟨0.24⟩ **THE FIRING CONDITION IS OVER THE REACHABLE CLOSURE, NOT "THE FUNCTION'S OWN ENTRY".** `5a8cf48`
and `05158db` say a rule fires where the match is evidenced by *that function's own entry*; `4805fca`, forty
lines below, says the answerability test runs over what the function REACHES. Measured, a function whose own
entry is reasonless but whose callee carries `reflect:forName`, gated `deny Unknown[reflect]`: **all four
exit 1** — firing on the callee's evidence, which this document's own control endorses as correct. An engine
implementing the "own entry" wording literally would withhold and refuse there. The condition is *evidenced
by entries the report carries in the function's reachable closure*; "own entry" was the instance the
measurement that prompted the clause happened to exercise.

⟨0.24⟩ **`whatif` OVER AN INCOMPLETE REPORT OMITS `ok` — it does not answer `true`, and it does not answer
`false` either.** Measured independently by candor-rust AND candor-java, both of which reported it rather
than deciding it: `whatif` returns `ok: true` over a report declaring `unanalyzed` units. Its `affected` set
is computed over a universe it cannot see all of — a caller in an unparsed file is invisible — so `true` is
a claim the input does not license. It is not a gate, but **its `ok` reads as one**, and this document's
standing rule is that the naive read of a field must be the safe one.

Neither boolean is honest here, which is why the answer is neither:

- `ok: true` asserts "nothing this hypothetical touches is denied", over a set that is known to be partial.
- `ok: false` would assert a VIOLATION the analysis never found — the fabrication mirror, and worse than
  the thing it replaces.

So the field is **omitted**, and `incomplete: true` plus the `unanalyzed` manifest take its place. A
consumer writing `if (r.ok)` gets a falsy value and fails safe; one that looks further learns exactly what
was unread. **This is deliberately NOT the refusal document's shape** (`ok: false` + `refused: true`,
§3.1): there, `ok: false` is *true* — the gate did not pass — whereas here neither value is. **A shape is
copied for its reasoning, not for its familiarity**, and the difference between the two cases is precisely
whether a `false` would be a statement or an invention.

The `affected` and `violations` arrays still ship: a partial answer that says it is partial is worth more
than a refusal, and `whatif` is consulted BEFORE an edit, where the alternative is the operator guessing.

⟨0.24⟩ **THE GENERAL LAW: AN ADVISORY VERB MAY BE LESS CERTAIN THAN THE GATE, NEVER MORE.** Three separate
measurements have now hit the same wall from three sides, and each was patched locally because the law was
never stated:

1. the manifest reader that skipped a malformed `unanalyzed` element, making the verb read a SHORTER
   incompleteness list than the gate read from the same file (below);
2. `unverified` / `fix-gate` computing from the effect set while the gate applied a class filter — the verb
   answering a WIDER question than the gate asked;
3. and this one: over a report carrying `hosts` but no `netClass`, **`gate --report` REFUSES (§3.1
   answerability) while the advisory verbs answer anyway** — going silent on a function the gate could not
   judge.

⟨0.24⟩ *Instance 3 was first written here as "answer from a FALLBACK DERIVATION", which is candor-ts's
mechanism and NOT candor-rust's — rust reads `netClass` verbatim and never derives it; there, the hole
predicate simply required `Unknown`, so a `Net`-only entry was never a candidate for the disclosure at all.
**Two engines, the same violation of the law, through mechanisms with nothing in common.** That is the
argument for stating this as a comparison rather than a behaviour, arriving as evidence within a day of the
clause being written: a rule phrased against the derivation would have missed rust entirely.*

All three are one defect: **the advisory verb was more confident than the gate over identical bytes.** The
current code documents (3) as intentional — *"no refusal channel, so a hedge beats a hole"* — and the first
half of that is true. **A hedge does beat a hole. But a DERIVATION is not a hedge; it is a second opinion,
and it is the one opinion an advisory verb is not entitled to.**

So, where the gate would refuse for want of evidence:

- **`unverified` MUST NAME the function.** A function the gate COULD NOT JUDGE is an unverified hole in the
  strongest sense the verb has — it is precisely *"your green gate is not provably green"*, and skipping it
  because a fallback derivation cleared it is the verb contradicting its own purpose. The reason recorded is
  **the missing evidence**, never the derived class.
- **`fix-gate` AND `fix` MUST NOT offer a remedy premised on evidence the gate refused to read.** A hoist
  plan for a boundary the gate could not adjudicate is a confident instruction resting on a guess.
  ⟨0.24⟩ *This clause named only `fix-gate`, and candor-rust measured that **`fix` was the worse of the
  two**: `fix-gate` already routed through the gate's own firing decision and merely mis-set `ok`, while
  `fix` went through a filter-blind layer predicate and printed the complete confident refactoring
  instruction this clause describes. Naming one verb and not its sibling is the same scoping error this
  document has now made nine times; the law binds every verb that answers from a signature, and the list is
  illustrative rather than exhaustive.*
- **Both carry `unevaluated: [ { "rule", "why" } ]`** — the gate's own shape (§3.1), because it is the same
  disclosure and inventing a second spelling is the mistake this document has made four times.
- **`--strict` exits 2**, matching the gate.

**Why this is a LAW and not a fourth patch:** the three instances differ in mechanism — a lenient reader, a
missing conjunct, a fallback derivation — and share only the direction of the error. A rule stated over any
one of them would not have caught the next two, which is exactly what happened. **The invariant is a
COMPARISON, not a behaviour: for any report and policy, the advisory verb's confidence must be bounded above
by the gate's.** An implementation can check that directly, and a conformance row can too.

⟨0.24⟩ **"THE SAME BYTES" MEANS THE SAME REPORT SET, AND THAT WAS NOT TRUE.** candor-java measured the
relation above and found the two sides were never reading the same input: **`gate --report <prefix>` reads
the report SET the locator names, while every other verb read the ONE file the prefix expansion picked.**
Two sibling reports under one prefix with the manifest in the second — gate exits 2, `unverified --strict`
comes back clean. The verb was not less pessimistic than the gate; it was answering a different question and
the comparison silently did not apply. **A relation between two readers is only a constraint while both
read the same thing** — so the advisory verbs take the LOCATOR and union the envelope over the located set,
exactly as the gate does.

⟨0.24⟩ **AND `ok` IS OMITTED FOR THE WITHHELD-RULE TRIGGER TOO, not set to `false`.** `4fd140c` argued the
`false` deliberately and that was wrong, by its own reasoning one paragraph earlier: on an advisory verb
`ok: false` asserts *"a hole exists, here it is"* — and where a rule was WITHHELD, no hole was found; the
question was declined. That is the fabrication mirror, which is precisely why `ec1a441` omits the field for
incompleteness. **The two triggers are the same shape and take the same answer.** Measured, the family split
two-against-two on it (rust and java `false`, ts and swift omitted) — the identical split this rung has just
spent a round closing on the sibling trigger, and it exists because I ruled the two cases in two clauses a
day apart instead of noticing they were one case.

⟨0.24⟩ **AN ADVISORY VERB MUST NEVER BE LESS SENSITIVE TO INCOMPLETENESS THAN THE GATE OVER THE SAME
BYTES.** candor-swift and candor-ts implemented the manifest reader with different ELEMENT rules — swift
skips a member with no string `path`, ts counts any object — and ts is right, for a reason that generalises
past this field. **Skipping a malformed element makes the advisory verb read a SHORTER `unanalyzed` list
than the gate reads from the identical file**, so a report the gate calls incomplete gets a clean advisory
answer. That is this section's own defect one layer down: a verb quietly disagreeing with the gate about
what the evidence says.

So the rule is a RELATION, not a shape: whatever leniency a reader applies, the advisory verb's
incompleteness verdict must be **at least as pessimistic** as the gate's over the same bytes. An element
that cannot be read is still an element that says something was not analysed — its unreadability is the
disclosure, not a reason to drop it.

⟨0.24⟩ **THE SAME RULE BINDS EVERY ADVISORY VERB THAT ANSWERS `ok` — `unverified`, `fix-gate`, and any
later sibling.** `0075987` ruled it for `whatif` and I scoped it to `whatif`, which is the eighth time this
document has been scoped to the verb its defect was found in. candor-swift and candor-rust then measured the
siblings INDEPENDENTLY and found the same shape:

    over a report declaring `unanalyzed`:
      gate --report        exit 2, incomplete, manifest        ← correct
      unverified --strict  exit 0, ok:true, no disclosure      ← and `--strict` is how CI consumes it
      fix-gate  --strict   exit 0, ok:true, no disclosure

`unverified` is the sharpest case in the family: **it is the verb that exists to say "your green gate is not
provably green", certifying a set it knows it cannot see all of.** A function in an unparsed file is absent
from `functions`, so it cannot be enumerated as an unverified pass — and its absence is exactly what the
verb would have to report.

So: an advisory verb over an incomplete report emits `incomplete: true` plus the `unanalyzed` manifest and
**OMITS `ok`**, and `--strict` (the CI form) exits 2. **`ok: false` is wrong here for the same reason it is
wrong in `whatif`**: on an advisory verb `false` asserts *"a hole exists, here it is"* beside an empty array
— the fabrication mirror, and worse than the silence it replaces. candor-swift shipped this shape after
reasoning to it unprompted; candor-rust measured the same defect and correctly DECLINED to invent a shape,
citing this section's own rule that an unspecified field becomes four guesses. Both were right, and the
second is why this clause exists.

⟨0.24⟩ **AND THE DISCLOSURE MUST REACH EVERY CHANNEL THE VERB ANSWERS ON, WHICH ITS TESTS PROBABLY CANNOT
SEE.** candor-rust built a mutant that kept the whole JSON fix and deleted only the printed human line —
**it survived the entire suite**, because absence-asserts on `ok` cannot see the other channel. candor-java
found the identical hole independently: `✓ within policy` is the prose `ok: true`, and removing the JSON
field while leaving that sentence standing MOVES the false all-clear rather than removing it. A verb with
two output channels needs the claim withdrawn from both, and a test that reads one channel is evidence
about one channel.

⟨0.24⟩ **A NARROWED RULE ASKED AS A HYPOTHETICAL IS ANSWERED CONDITIONALLY, AND THE CONDITION IS NAMED:
`"conditional": [ { "rule": "<the raw policy line>", "condition": "<the narrowing left unevaluated>" } ]`,
omitted when empty.** `whatif` asks about an effect the code does not yet have. A narrowing filter
quantifies over a CLASS of that effect — `deny Net[unknown-host]` asks about a destination the hypothetical
call has not got, because the call does not exist. There is nothing to match, so the filter cannot be
evaluated and the answer is fail-closed **but conditional**.

Neither of the two obvious answers is right. Printing the rule stripped of its filter (`deny Net` for
`deny Net[unknown-host]`) misattributes the verdict to a rule the operator did not write. Printing the raw
line with an unconditional verdict is **worse than that bug**, because it reads as a filter candor evaluated
and did not. §3.1's own rule settles it: an unanswerable condition is DISCLOSED, never scored — so the raw
line is printed and the unevaluated narrowing is named beside it.

⟨0.24⟩ *I MIS-TRANSCRIBED THIS PIN, WHICH IS ITS OWN LESSON.* The shape above was written from the
description of candor-rust's behaviour rather than from its output. Measured, rust emits `conditional` as a
**per-violation STRING** — `violations[].conditional: "the \`Net\` you introduce reaches destination class
unknown-host"` — not a top-level array of `{rule, condition}`. **Rust's shape is the better one and stands:**
the condition qualifies a specific hypothetical finding, so it belongs on that finding, not in a parallel
list a consumer has to re-join. The normative shape is `violations[].conditional: "<the narrowing left
unevaluated>"`, omitted on rules that do not narrow. It is also pinned here, inside the `gate --report`
section, while being a **`whatif` output** — a reader of §3.2 will not find it. Both are my errors, and both
are the same one: *pinning a field from a description instead of from the artifact.* A pin written without
running the thing is a fifth guess, not a constraint.

⟨0.24⟩ **`errors[].accepted` IS AN ARRAY OF TOKENS, and `kind` is drawn from a CLOSED set** —
`reason-class/alias`, `Net destination-class`, `effect-name`, `rule-kind`, `rule-form`.

⟨0.24⟩ *`rule-form` was missing and the set was wrong the day it was pinned — the SIXTH time I have scoped
a clause to the cases in front of me.* candor-java already emitted `forbid form` and `allow values`: a rule
whose KIND is recognised (`forbid`, `allow`) but whose FORM is malformed, which none of my four values
describes. candor-rust, following the spec over the reference engine, mapped those onto `rule-kind` — a
true statement about a closed set that was itself incomplete. **A closed set is only a constraint if it is
closed over the domain rather than over the author's sample**; five values with a stated meaning each beats
four plus an engine quietly widening one. Engines emitting `forbid form` / `allow values` / `rule kind`
normalise to these spellings; the hyphen is not decoration, it is what makes the value machine-comparable. Measured divergence already
shipped: java emits `accepted` as an array, **candor-ts emits it as a PROSE STRING** ("reflect, dispatch, …
aliases: dynamic, *, or a config `unknown-alias`") and additionally names the pinned `kind` field
`vocabulary` and `rule` field `where`. A prose string is unparseable by the consumer the field exists for,
and the trailing "…" I left on `kind`'s vocabulary was four future guesses in one ellipsis.

⟨0.24⟩ **THE STALE-DOCUMENT RULE BINDS EVERY MACHINE-OUTPUT PATH, NOT JUST `--gate-json`.** The argument —
*a CI wrapper reading the path unconditionally re-reads the PREVIOUS run's document as current* — is exactly
as true of `scan --json <report>`, of SARIF output, and of `fix-gate --json`. It is WORSE for `scan --json`:
an exit-2 scan leaves yesterday's REPORT on disk, and a downstream `gate --report` then gates stale data
green — which is this rung's own supply-chain route, poisoned at the source. `1503368` generalised the rule
over its *causes* and I did not think to generalise it over its *paths*. **On any exit-2, every machine
output path the invocation requested is written fail-closed, or is not left holding a previous run's
answer.**

⟨0.28⟩ **AND HERE IS THE MUST FOR THE REPORT SINK, WITH A SHAPE.** The ⟨0.24⟩ clause above generalised the
*what* over paths; it did not settle the *when* or the *document*, and no engine implemented either.
Measured 2026-08-10 across all four code engines with the simplest exit-2 trigger, an unknown flag beside
`--json <file>`: candor-scan wrote 502 bytes of report on the clean run and the same 502 bytes remained on
exit 2; candor-java wrote 648 and the same 648 remained; candor-ts (423) and candor-swift (517) behaved the
same, byte-identical, MD5 unchanged. A downstream `gate --report <that>` then reads a green report the
failed run never produced. ⟨0.27⟩ closed exactly this defect on `--gate-json` and left the report sink one
hop upstream.

**(1) THE ARMING RULE, RESTATED FOR THE REPORT SINK.** As soon as `--json <path>` has been parsed and
accepted, the implementation MUST write the fail-closed report (shape below) to `<path>`. Every subsequent
exit then leaves that document in place unless a real report replaces it. Arming later — after config load,
after target discovery — is the stale green with a window ⟨0.27⟩ closed for `--gate-json`, reopening through
a different sink.

**(2) THE FAIL-CLOSED REPORT IS A MANIFEST-CARRYING EMPTY UNDER ⟨0.21⟩ ROW 1** — the shape a ⟨0.24⟩ consumer
already reads as *nothing was judged, no purity licence*:

    { "candor":     { "version": "…", "toolchain": "…", "spec": "0.31" },
      "functions":  [],
      "analyzed":   { "count": 0 },
      "unanalyzed": [ { "path": "<what the run could not analyze>", "reason": "<why>" } ] }

Row 1 of the ⟨0.24⟩ table pins the reading: `analyzed.count: 0` + `functions: []` is *nothing was judged*,
not *nothing to judge*. A ⟨0.21⟩ chain grants no purity licence, `gate --report` records the file
`invisible` in the coverage ledger, and a downstream verdict discloses it — the machine-consumer channel
the stale defect was silently deleting is restored. This IS a PARTIAL artifact, and the ⟨0.26⟩ lesson
(partial answered worse than absent) is answered specifically by keying on `count: 0` — the one integer
⟨0.24⟩ Row 1 READS as "no claim".

⟨0.28⟩ **THE `unanalyzed[].reason` VOCABULARY, MINTED HERE RATHER THAN CITED.** This clause said the string
"uses the same vocabulary as the §3.3 incomplete verdict" and named four tokens. There is no such
vocabulary: §3.3 pins `unanalyzed: [ { path, reason } ]` and leaves `reason` unconstrained, and grepping
this document finds those four tokens nowhere else. They are being CREATED here, and a reader of §3.3 will
never find them — the same mislocation this section already confesses for `conditional`. So, stated as what
it is: an armed report's `reason` SHOULD name the cause from `unknown-flag`, `unreadable-config`,
`refused-policy`, `target-missing`, `armed` — and the set is **open**, because a closed set is only a
constraint if it is closed over the domain and the causes of a failed run are not enumerable in advance.
`armed` is in the list for the reason the next paragraph gives.

**AND THE ARMED DOCUMENT IS WRITTEN BEFORE THE CAUSE EXISTS.** Arming happens at parse time; the failure
that leaves the document in place has not happened yet, and rule (1)'s own words — "every subsequent exit
then leaves that document in place" — literally license never touching it again. An implementation MAY
therefore arm with `reason: "armed"` and refine it at the exit that knows better; what it MUST NOT do is
let the vocabulary sentence above read as a promise the machine channel does not keep. A consumer must key
on the SHAPE (Row 1: `count: 0` + `functions: []`), never on the reason string.

**(3) THE INPUT EXEMPTION FROM ⟨0.27⟩ (2) COVERS THE PATH, NOT THE RUN.** A `--json` path naming an INPUT
of this run (the target's own source tree, the discovered `.candor/config`, the policy file, a chained dep
report) is refused with exit 2 having written NOTHING to that path — arming would destroy the input.
Sameness is a question about ARTIFACTS not strings — the ⟨0.28⟩ device+inode rule for the verdict sink
below applies here as well.

⟨0.28⟩ **AND AN INPUT LOCATOR NAMES A SET — COMPARE THE EXPANSION, NEVER THE TOKEN.** "Artifacts not
strings" was read as *resolve the path* and implemented as *compare one resolved path to one resolved
path*, which is still a comparison of the token the operator typed. Almost every input in this format is
named by a locator that the LOADER expands and the GUARD did not: a `--report` prefix resolves to the
sibling report set, a baseline prefix to `<prefix>.<unit>.scan.json` plus its callgraph, a dep DIRECTORY
to every report inside it, a discovered `.candor/` to the whole set. The guard compared `r`; the loader
read `r.B.…json`; the sink destroyed `r.B.…json`.

**Found independently in three engines, and it is one defect with three spellings.** Measured: `gate
--report r --gate-json r.B.Swift.json` destroyed the operator's report at exit 2 (candor-swift, also
through the no-`--report` discovery spelling); `CANDOR_BASELINE=base … --out base` destroyed the ratchet's
baseline (candor-scan); and candor-java's `gate` sink guard compares the raw `--report` token to this day.
The `CANDOR_DEPS` directory case was already fixed family-wide one rung earlier, one channel at a time,
which is precisely the evidence that the rule was never stated over the CONDITION — each engine fixed the
directory and left every other locator that expands.

So: **before comparing, expand each input locator exactly as the code that READS it will expand it**, and
compare the resulting set. Two consequences the implementations paid for:

- **DERIVE THE EXPANSION FROM THE LOADER, do not re-spell it.** A hand-written second expansion is a
  second parser and it drifts: measured, one engine's duplicate-sink guard was a re-derivation of its own
  input set that had silently lost `CANDOR_BASELINE`, `CANDOR_DEPS` and the config keys, so the refusal
  document — written to every sink by design — destroyed a chained dep report. Two spellings of one rule
  means the rule holds on whichever route was in front of the author.
- **THE SIDECARS EXPAND TOO.** A report locator that resolves to `<stem>.json` also reaches
  `<stem>.callgraph.json` and the rest of §2.2's reserved family. A guard that protects the report and
  not its sidecars leaves the pair destroyable one half at a time.

⟨0.28⟩ **AND HERE IS WHAT EACH LOCATOR FORM RESOLVES TO — because "expand as the loader will" says how to
compare, and never says what the loader should expand to.** Three engines were measured disagreeing, and
the disagreement was invisible because each was internally consistent:

- **A locator naming a FILE resolves to that file, and to its §2.2 sidecars.** It does NOT union the
  prefix siblings beside it. The operator named one artifact; silently reading three is the mirror of the
  guard bug above, and it would make `--report r.json` mean something different depending on what else
  happens to sit in the directory. candor-java and candor-ts already do this and are RIGHT.
- **A locator naming a PREFIX resolves to the whole matching set, unioned.** ⟨0.24⟩ already ruled this for
  the advisory verbs and the gate. **Measured, and it did not reach the descriptive verbs:** candor-java's
  prefix form prints `matches 2 reports; using <one>` and answers `map`/`where`/`show` from the
  lexicographically FIRST file. A locator that means "the set" for one verb and "whichever sorts first"
  for another is two contracts wearing one flag, and the quiet one under-reports by construction.
- **A locator naming a DIRECTORY resolves to the reports discovered inside it**, which is the `.candor/`
  discovery spelling and is already pinned by the guard clause above.

⟨0.28⟩ **AND THE SCAN TARGET EXPANDS TO THE FILES THE RUN WILL PARSE — the residual the exact-artifact
ruling deliberately left.** That ruling refuses a sink that IS the target and permits everything else,
which is correct as far as it goes and leaves this: measured on candor-ts, `--gate-json src/main.ts` while
scanning `tsconfig.json` still destroys that source, because only the target token is registered and not
the files it resolves to. The same residual exists in all four.

The obvious fix is not available. The parse-time arming that ⟨0.27⟩ requires happens BEFORE the file walk,
so the set of files the run will read is not yet known — and deferring the arm to after enumeration would
uncover the argv-error exits the arming rule exists for.

So the check is narrow and stated over what IS knowable at parse time: **a sink that lies under the target
AND bears an extension the engine parses is refused.** Not containment in general — `<dir>/.candor/report.json`
is under the target and is not a source file, so the recommended layout stays permitted, which is the
control that fix must not break. An engine knows its own source extensions before it knows its file list;
that is the whole of what makes this checkable at the moment arming happens.

⟨0.28⟩ **AND THE SCAN TARGET IS THE MEMBER OF THAT LIST NO ENGINE IMPLEMENTED.** The sentence above names
"the target's own source tree" first, and every engine registered the policy, the config, the baseline and
the dep reports — and not the target. **Measured, two engines, live:**

    $ printf 'export function hello(){ return 1 }\n' > app.ts
    $ candor-ts app.ts --gate-json app.ts
      candor-ts: wrote 0 effectful functions (1 analyzed, 1 files) …                      exit 0
    $ cat app.ts
      { "spec": "0.28", "ok": false, … }                     ← the operator's SOURCE FILE, replaced (measured at spec 0.28, informative)

    $ candor-java app.jar --json app.jar
      candor: cannot read scan target app.jar: zip END header not found                   exit 2
                                    ↑ it cannot read the jar because arming just overwrote it

The first is the worse artifact: unrecoverable loss of the operator's own code, reported as SUCCESS. The
second is self-describing — the diagnostic is the engine discovering the file it destroyed.

So it is stated as a MUST in its own right: **the scan target is an input, and a report or verdict sink
naming it is refused.** Two notes on the shape of the check, both of which an implementation gets wrong by
default:

- **EXACT ARTIFACT, NEVER CONTAINMENT.** A report written into `.candor/` *inside* the tree being scanned
  is ordinary usage and the recommended layout; a rule that refuses any sink under the target refuses the
  default. One engine tried containment and it "took 33 tests with it". Exact identity already separates
  the two cases: `<dir>/.candor/report.json` is not the artifact `<dir>`.
- **THE TARGET IS OFTEN A DIRECTORY, AND THAT IS NOT A GUARD.** Two engines were protected only because
  their targets are directories, so the arm write happened to fail. An accident that holds for today's
  target kinds is not an implementation of this rule — a single-file target route (a jar, a `.ts` file, a
  module) is exactly where it stops holding, which is where both reproductions above came from.

**(4) `--json` ON STDOUT IS THE STREAM FORM.** Arming does not apply (no previous document to go stale);
the document-on-every-exit rule applies IN FULL. On any exit-2 the fail-closed report is written to stdout,
exactly once, as the stream's only content. Measured across all four engines on the same unknown-flag
trigger, **stdout was 0 bytes on exit 2** in every one — the same defect ⟨0.27⟩ closed on the verdict
stream, arriving through the report sink because that rule was written for the verdict sink and no engine
extended it. A JSON consumer keying on stdout throws a parse error and is thrown back to scraping stderr,
which is the distinction that made the incomplete-analysis defect a defect (§3.3).

**(5) EVERY ROUTE AND EVERY ENGINE THAT WRITES A REPORT.** The rule is about the SINK, not one CLI. Surface
as of this rung: `candor-scan --json`, `candor-java --json`, `candor-ts --json`, `candor-swift --json`, and
the agent-fleet's **`observe --json` alongside its `scan`**. `observe` publishes the same §2 shape and its
stale reports poison chains identically; a route is not covered by its sibling.

**(6) `--out <prefix>` — THE REPORT SET, AND THE SET IS THE ONE THE PREVIOUS RUN LEFT.** This was deferred
pending measurement between a `<prefix>.__failed.json` marker and per-package placeholders; measured, and
**neither framing survived**. Only ONE engine fans out (candor-scan, one report per crate); java, ts and
swift write a single report under `--out`, so the file-SET problem exists in one engine rather than four.
And the objection to per-package placeholders — that the run cannot know the package set at parse time — is
about the wrong set: the set at risk of going stale is the one the PREVIOUS run wrote, which is knowable by
globbing the prefix. So the implementation MUST rewrite each of those to the shape in (2) at parse time, and
each package that scans successfully overwrites its own a moment later.

**Three rules the implementations paid for, stated here so nobody re-derives them:**

- **ONLY A SINK THE OPERATOR NAMED.** Arming binds an explicit `--out`, never the DEFAULT prefix. Measured:
  arming `<dir>/.candor/report` on a run that died in argv parsing overwrote a COMMITTED report — in this
  family's own reference tree, which commits reports for six crates, and committed reports and baselines
  are the pattern this document recommends. ⟨0.27⟩ never had to say this because `--gate-json` has no
  default: every verdict sink is named. Destroying a version-controlled artifact is a worse outcome than
  the staleness the rung closes.
- **IDENTIFY WHAT YOU OVERWRITE; DO NOT DENYLIST WHAT YOU SKIP.** An armer MUST write only files it
  positively recognises as its own §2 report. A suffix denylist over §2.2's reserved family is the wrong
  mechanism, not merely an incomplete list: measured, a three-suffix carve-out overwrote `calibrated`,
  `layerreach`, `encountered-*` and **`<prefix>.gate.json`, a gate verdict** — the report sink silently
  destroying the verdict sink's document beside it. The denylist-over-allowlist rule elsewhere in this
  family is about CLASSIFYING, where over-approximating is safe; **for a WRITER it inverts.**
- **THE INPUT EXEMPTION IS ASKED FIRST, BEFORE IDENTIFICATION.** A policy holding ordinary rule lines is
  not JSON, so identification-first skips it silently and the operator never learns their policy sat in the
  arming path; and the exemption must outrank identification for the case where the colliding input IS a
  valid report — a chained dep report under the same prefix. *Do not touch what this run reads* is the
  stronger claim whatever the file turns out to be.

**AND THE RUN HANDS BACK WHAT IT TURNED OUT NOT TO OWN.** A file still holding the placeholder once the run
has finished writing is one the run never claimed — a leftover from a package no longer in the scan. That is
not an incomplete analysis, and leaving the placeholder asserts one: measured, it turned a COMPLETE scan of
the remaining members into a permanent exit-2 refusal that only manual deletion cleared, because a
placeholder's non-empty `unanalyzed` is the ⟨0.21⟩ incompleteness trigger. The implementation MUST restore
the previous bytes there. The orphaned report is a real and separate defect — it still describes deleted
code and still reaches a gate over the prefix — and it keeps its own wire question rather than being
resolved as a side effect of a staleness fix.

⟨0.28⟩ **AND "FINISHED WRITING" MEANS THE SCAN COMPLETED — NOT THAT CONTROL CAME BACK.** The paragraph above
was stated over the instance it was measured in, a COMPLETE scan with a member removed, and read literally
it reinstates the exact stale green this rung exists to destroy. On a run that dies part-way, the packages
it never reached are still holding placeholders, and they are not "never claimed" — they are
claimed-and-unreached. Handing their previous bytes back republishes the previous run's answer as current.
**Measured**: candor-scan's `--deps` path *returns* 2 instead of exiting, so the hand-back ran on a run that
had written nothing, and the previous green reports came back byte-identically at exit 2.

So the hand-back is conditional on the run having ENUMERATED and SCANNED its package set. On any exit that
precedes that, the placeholders stand — a run that died before enumeration cannot distinguish "no longer in
the scan" from "not yet reached", and the fail-closed reading is the only one it is entitled to. An
implementation keying the hand-back on *control returned to the top level* rather than on *this run wrote
its set* has the defect whether or not a path reaches it today; the next early return will re-open it
silently.

**AND AN ORPHAN'S SIDECARS COME BACK WITH IT.** The hand-back as first written restores report bytes only,
while the sidecar rule below deleted that report's sidecars at arming — so a compliant run produced a
live-looking report with its sidecars missing, which is a third state neither the pre-run tree nor the armed
tree ever had, and precisely the torn pair the pairing rule two clauses down treats as a hazard route. A
pair is restored together or not at all.

⟨0.28⟩ **AND THE §2.2 SIDECARS GO WITH THE REPORT — DELETED, NOT EMPTIED.** A report armed to the shape in
(2) beside a live sidecar is a PAIR THAT CONTRADICTS ITSELF, and §2.2 gives the sidecar no provenance of its
own to arbitrate with. It is not a theoretical pairing problem: `callers`/`whatif`/`rewire` are answered
FROM THE SIDECAR, because a currently-pure function is absent from the report by §2 rule 3 and only the
sidecar records it. Measured — baseline `f` pure with one caller `g`; the new version gives `f` a real
effect and adds a second caller `h`; the run exits 2 with the report armed and the sidecar left as it was:

    callers f   →   exit 0, "`f` is reached by 1 function(s) (the blast radius if it gained an effect): g"

The answer is confident, exit-0, labelled as the blast radius, and **wrong** — `h` calls `f` too. An agent
reads it as safe-to-edit. That is the cardinal sin reached through the half of the pair the rung had not
touched.

So: on arming, the implementation MUST remove each armed report's §2.2 sidecars, under the same
artifact-resolution and input-exemption rules as the report itself.

**Deletion rather than `{}`, and the reasoning is NOT the report's.** §3.3.1 forbids deleting a REPORT
because a consumer that treats a missing file as "nothing to report" fails open. No sidecar consumer has
that failure mode: §2.2 makes the sidecar OPTIONAL, so every consumer was forced to define an absence arm
from the start and every specified arm is safe — over-listing (§3.1), `unknown` disclosed (the `gains`
origin rule), refusal on a corrupt one. Writing `{}` instead buys nothing: ⟨0.24⟩ has already RULED that an
empty, an absent and an unparseable hierarchy sidecar are THE SAME INPUT. Measured four-way on the one cell
that rule does not cover — an empty-but-valid baseline CALLGRAPH — all four engines answer `origin:
"unknown"`, so `{}` and absent are indistinguishable in the field as well as in the text. Absence is the
state the consumers were built for; `{}` is a file this document has declared meaningless.

⟨0.28⟩ **THE PAIRING RULE — a CONSUMER obligation, and the belt to arming's braces.** A §2.2 sidecar whose
paired report is a ⟨0.21⟩ Row-1 manifest-carrying empty is **unanswerable input regardless of its own
content**. This is the normative form of §2.2's own "read together with its report", and it covers the
staleness routes arming cannot reach: a crash between the report write and the sidecar write, a hand-copied
half, an artifact pair restored from different backups. Producer-side deletion is the floor because *the
naive read is the one that ships*; this rule is what makes a pair that arrives contradictory anyway fail
closed.

**AND UNANSWERABLE MUST REACH THE MACHINE CHANNEL — "take the absence arm" IS NOT ENOUGH, which is what
this clause said until it was measured.** The absence arm of a call-graph verb is silence: over an armed
pair, `callers <f>` emits `{}` (candor-scan) or `{"of":[],"direct":[],"transitive":[]}` (candor-ts), **both
exit 0**, while the human channel says "no call graph in the report". A consumer reading `direct` — or
defaulting it, which ⟨0.24⟩ already names as the fail-open idiom on every key in this format — is told
NOBODY CALLS `f`. That is a blast-radius answer of "safe to edit" over a pair whose honest answer is
"this run judged nothing", and it is the same human-channel-fine / machine-channel-silent split that made
the incomplete-analysis defect a defect.

So a verb that has ruled its input unanswerable MUST say so **in the machine output**: a pinned
`"unanswerable": "<why>"` key, or a non-zero exit, or both. An empty `direct` means *nothing calls this*;
the verb does not know that, and must not say it.

⟨0.28⟩ **AND THE OBLIGATION KEYS ON THE REPORT, NOT ON THE SIDECAR'S EXISTENCE — which is what this clause
said until the deletion rule above was read back against it.** As written it bound "a verb answering from
a sidecar it has ruled unanswerable", i.e. a sidecar that is THERE. Two clauses earlier, this same rung
requires the armed report's sidecars to be **deleted**. After compliant deletion there is no sidecar, the
verb takes the ordinary absence arm, and the ordinary absence arm is the `{}`-at-exit-0 this clause was
written to forbid — measured, and quoted three paragraphs up. The producer MUST steered the common case
into the one state the consumer MUST did not cover, and the clause's own words say why that matters: the
rung "made a rare state — no sidecar — into the standard post-failure state".

So the trigger is **the report**: a verb answering over a ⟨0.21⟩ Row-1 manifest-carrying empty is
unanswerable for the call-graph questions whether the sidecar is present-and-contradictory, absent, or
deleted by arming. One semantic state — *this run judged nothing* — gets one machine surface, instead of
two that differ by whether a file happened to survive.

⟨0.28⟩ **AND `unanswerable` REPLACES THE RESULT SET; IT DOES NOT ACCOMPANY ONE.** The permitted remedy
above read "a pinned `unanswerable` key **alongside whatever else it emits**", which licenses
`{"of":[…],"direct":[],"transitive":[],"unanswerable":"…"}` — and the naive reader this clause names, the
one keying on `direct`, is still told NOBODY CALLS `f`. The remedy still carried the defect. ⟨0.27⟩ already
settled the identical question the other way one section down: the refusal document **MUST NOT carry a
`violations` key**, because "an empty array there is precisely the claim it cannot make", and a consumer
keying only on `ok` must land on FAIL. A hedge beside an empty result set is that same defect wearing the
hedge as clothing.

So a verb emitting `unanswerable` MUST **withhold the result keys** it cannot fill — no `direct`, no
`transitive`, no `path`, no `affected` — rather than emitting them empty. Keys that merely echo the
question (`of`, `fn`, `effect`) may stay: they carry no claim about the code.

*Recorded because the corrections are the point, and there were two of them on one clause. The first
version specified the remedy as "take its absence arm", and the absence arm IS the defect — raised by
candor-ts's arm of this rung, which flagged the `--json` silence rather than treating it as out of scope.
The second version fixed the channel and left the shape, so a compliant engine could still ship the
determined negative with a hedge stapled to it. A MUST whose literal compliance is the forbidden behaviour
is worse than no MUST, because it reads as covered — and this clause managed it twice.*

⟨0.24⟩ **AND THE GENERAL RULE, BECAUSE THIS IS THE FOURTH TIME IN ONE DAY.** `coverage.packages`,
`policyVocabulary`, `parsepolicy`'s `errors`, and now `conditional` were each a field I required — or an
engine needed — without specifying its shape, and three of the four had produced a live cross-engine
divergence before anyone looked. Measured interval on the third: **under an hour** from "an engine minted
an unpinned name" to "R9 reports three names for one field".

So: **a field that enters a machine-consumed document MUST have its name and shape stated here in the same
rung that introduces it.** A MUST that says "disclose X" without saying what X is called is not a
requirement, it is four independent guesses with a conformance failure scheduled. The cost of pinning is
one sentence written at the time; the cost of not pinning is an engine round per implementation plus a
conformance row to catch it — which is what today cost. **`conditional` is rust-only as this is written,
and it is pinned before the other three implement it rather than after**, which is the first time this
rung has got ahead of that.

⟨0.24⟩ **`aliases` MAPS EACH ALIAS TO THE CLASSES IT EXPANDS TO — `{"corp": ["reflect"]}`, AN OBJECT.**
This clause already pinned braces and three engines shipped `["corp"]` anyway, so the pin was not explicit
about the VALUE. candor-ts kept the object and argued for it from this section's own sentence, which is why
it stands rather than the majority: `configSources: [path]` is rejected below because *a disclosure that
names the source but not the content leaves the reader knowing they were affected and not how* — and
`aliases: ["corp"]` fails that same test one level down. **`corp = reflect` and `corp = reflect,native`
gate DIFFERENTLY under one unchanged policy line**, so a reader given only the name cannot tell which gate
ran. The object is a strict superset; `Object.keys` recovers the array. rust, java and swift move.

⟨0.24⟩ **THE DISCLOSURE'S SHAPE IS `"policyVocabulary": { "config": "<path>", "aliases": { … } }`.** I left
this unspecified when I required the disclosure, and three engines invented three answers within the hour —
`vocabulary` (rust), `policyVocabulary` (java), and `configSources: [path]` (swift). **That is the
`coverage.modules` failure recurring on the very next field, which is what it looks like when the lesson
was recorded and the practice was not changed**: I wrote "MUST name that file" and specified no shape, and
a MUST with no shape is an invitation to diverge.

`policyVocabulary` over `vocabulary` because the document already carries other vocabularies (effects,
reason classes) and the bare word does not say whose. **And the OBJECT form is required, not the array**:
swift's `configSources: [path]` names the file but drops the alias names, and the file is the lesser half —
an operator reading a verdict changed by an ambient definition needs to see *what the definition was*, not
merely that one existed. A disclosure that names the source but not the content leaves the reader knowing
they were affected and not how.

⟨0.31⟩ **THE SAME OBLIGATION REACHES `net-partner`, AND ITS SHAPE IS `"netPartners": { "config":
"<path>", "hosts": [ … ] }` IN THE REPORT, A LIST OF THOSE RECORDS IN THE VERDICT.** The reasoning above
already covers this key and its MUST did not reach it. MEASURED, identically in candor-ts and
candor-rust: under `deny Net[unknown-host]` a call to `partner.example` exits **1**; adding `net-partner
partner.example` to an ambient `.candor/config` exits **0** with `ok: true`, and no key names the file,
its path, or the host. *An operator reading a verdict changed by an ambient definition needs to see what
the definition was* — the argument is quoted from the clause above, and it is the same failure one key
along.

**`hosts` is what PARTICIPATED, not what was declared.** A config listing twenty partners of which one
matched discloses the one: a declaration that changed nothing is not provenance, and a list of everything
declared would bury the line that moved the verdict. Both negatives follow — a project declaring no
partners, and one whose declarations never matched, carry the key nowhere and are byte-identical to a
pre-rung report.

**IT IS RECORDED IN THE REPORT, AND THAT IS WHAT MAKES IT EMITTABLE AT ALL.** `net-partner` anchors at
the TARGET; `gate --report` has no target, and re-classifying the report's hosts through the CONSUMER's
own config would be the re-derivation ⟨0.24⟩ forbids — it would make a verdict depend on the reader's
working directory. So a verdict-only disclosure is computable on the scan route and not on the report
route, which breaks §3.1's byte-equality: this was implemented that way once and reverted, with the
producing engine's own suite reporting *"pure: NOT byte-equal"*. The producer records what participated;
both routes copy that one record. They agree by construction, which is the shape ⟨0.30⟩'s `outOfScope`
already uses for the same structural reason.

**A SEPARATE KEY, NOT A FIELD ON `policyVocabulary`.** The two anchor differently — `unknown-alias`
resolves against the POLICY file's directory, because vocabulary travels with the policy, while
`net-partner` resolves against the TARGET. In one run they are two different files, so a single `config`
naming one source for both would be false about one of them.

**AND THE MATCH MUST BE THE CLASSIFIER'S OWN.** The engine decides `known-partner` by some host
normalisation; the disclosure MUST report the partner that decision matched, by asking the same code
rather than repeating it. The first attempt normalised differently — a declared `partner.example` never
equalled an observed `partner.example:443` — so the disclosure came back empty on every real run while
the verdicts it was reporting on had flipped. A disclosure normalised differently from the decision it
reports can only be wrong, and the way to make that unwritable is one matcher with two callers.

⟨0.24⟩ **THE VERDICT'S `coverage` BLOCK IS `{ "uncovered": <n>, "packages": [ … ] }`, AND UNTIL NOW THIS
DOCUMENT NEVER SAID SO.** §2 defines the *report's* ledger — `coverage.uncovered` as an ARRAY of
`{name, calls}` — and that is a different shape from the *verdict's*, which carries a COUNT plus a name
list. The verdict shape was never pinned anywhere, so the engines diverged unobserved: rust and ts emit
`packages`, **candor-swift emits `modules`**, and the single prose mention of it in this section said
`modules` too — almost certainly because it was written with swift's output open.

`packages` is correct, and **not because it is three-to-one.** The §2 envelope names the very same objects
`package` / `packages`; a verdict that renames them mid-document is drift, and `module` already means a
different thing in two of the four implementation languages (a compilation unit, which is not what is
being counted). The prose mention was wrong and is corrected above.

Recording the shape of the miss: **a field can be uniform across three engines, mentioned in this document,
covered by a conformance suite, and still be UNSPECIFIED** — because the mention was descriptive prose
rather than a normative shape, and no PART compared the key. That is the same failure mode as an untested
guard, and the tell is available whenever a "spec says X" claim traces to a sentence that was *describing*
an implementation rather than *constraining* one.

⟨0.24⟩ **PRECEDENCE: A CERTAIN VIOLATION DOMINATES A REFUSAL, AND ALL FOUR ENGINES HAVE THIS BACKWARDS.**
Three outcomes can be live at once. The order is **violation (1) > refusal (2) > incomplete (2)**, and the
first rung is forced by Lemma 2 rather than chosen. If one rule FIRES on evidence the report carries, the
policy is rejected — and because `Reject` is upward-closed, *however the unanswerable rule would have
resolved cannot un-reject it*. Exit 1 is therefore not merely fail-closed here, it is **certain**, and it
is strictly more informative than exit 2: it names the violation. Refusing instead is the same defect §3.1
already criticises as "a worse answer than the correct one".

The consequence is not cosmetic. A refusal writes no `--gate-json` document (below), so refusing over a
firing rule **deletes a certain violation from the machine-consumer channel** — byte-identical in harm to
candor-rust's incomplete-analysis path, which this same rung is making it fix. Measured, a policy carrying
a firing `deny Fs` plus one unanswerable scoped rule exits 2 on **rust, java, ts and swift alike**, with no
document. Four-way agreement, and four-way wrong.

⟨0.24⟩ *This clause first read "refusal (2) > violation (1)", ratifying the measured four-way behaviour. I
wrote it, and it was wrong within the hour: the monotone-denial property this section already invokes two
paragraphs above settles the question in the other direction, and I had just finished using that same
property to argue engines should answer more questions rather than fewer. **Uniform agreement is the
weakest evidence in this project, and it is at its weakest when it agrees with the draft you were about to
write.*** ⟨0.24⟩ **THAT DISCLOSURE IS `"unevaluated": [ { "rule": "<the RAW policy line, verbatim>",
"why": "<why it could not be decided>" } ]` IN THE `--gate-json` DOCUMENT, one entry PER RULE, omitted when
empty — and requiring it without naming it is the sharpest failure of my own pinning rule, because it
happened on the clause sitting beside the one that states the rule.** Measured on `deny Fs` + `forbid …`,
exit 1, all four engines:

    rust    NOTHING in the document — stderr only
    swift   NOTHING in the document — stderr only
    java    "unevaluated": [{"rule": "forbid (× 1)"}]   ← a KIND AGGREGATE; two forbid lines collapse to
                                                          "forbid (× 2)" and WHICH rules is lost
    ts      "unevaluated": [{"rule": "<raw line>", "why"}]   ← correct

**A machine consumer of rust's or swift's exit-1 verdict cannot see that any rule went unevaluated at all.**
That is a finding that never reaches the consumer — the harm class this entire rung exists to close —
arriving through the disclosure the rung added. stderr is not the machine channel; that is the same
distinction that made the incomplete-analysis defect a defect. And java's aggregate answers "how many" when
the operator's question is "which", so it satisfies a naive reading of "disclose which rules" while
answering the other one.

⟨0.24⟩ The refusal document's `reason` is likewise now pinned: a STRING naming the cause. All four converge
on it today **by luck, not by pin** — it was specified only as "with the refusal reason". Exit 1 reports the
violation it is sure of, it does not conceal the part it could not read.

The stale-document hazard is separate, and survives the correction above — it bites whenever a refusal is
the *sole* outcome. A refusal writes no `--gate-json` document at all, so a CI wrapper that reads the path
unconditionally re-reads **the PREVIOUS run's document as current**. A green file from yesterday's clean
run, still on disk, is how a refusal becomes an all-clear. Deleting the path is not the fix either: a
consumer that treats a missing file as "nothing to report" fails open by a different route.

So: ⟨0.24⟩ **if `--gate-json` was requested and the gate REFUSES, the implementation MUST write a document
at that path, and that document MUST be fail-closed to a NAIVE reader.** Concretely it carries `"ok":
false` and `"refused": true` with the refusal reason, and it **MUST NOT carry a `violations` key** — the
gate is making no claim about violations, and an empty array there is precisely the claim it cannot make.
The `ok: false` is not ceremony: a consumer keying only on `ok` must land on FAIL, and a consumer keying on
`refused` learns why. This is the same reasoning as the empty-report rung — the naive read of a document
this format emits must be the safe one, because the naive read is the one that ships.

⟨0.27⟩ **WHEN, EXACTLY, THE SINK IS ARMED — and the one thing that must never be written to it.** The rule
above says *what* to write; it did not say *when*, and every engine got the timing wrong in a different
way. Two MUSTs settle it:

**(1) Arm at the instant the sink is known, and before anything else can exit.** The implementation MUST
write the fail-closed refusal to the path as soon as `--gate-json <path>` has been parsed and accepted —
before loading config, before resolving the pin, before validating any other flag, before touching the
target. Every subsequent exit then leaves a refusal behind unless it is replaced by a real verdict. Arming
*later* than this is a stale green with a window: measured, engines armed after config load (where an
unreadable config exits 2), after pin resolution, and — in the reference engine — mid-flag-loop, which
made the behaviour depend on **argv order**: `--gate-json G --frobnicate` wrote a refusal into `G` and
`--frobnicate --gate-json G` left yesterday's verdict untouched. Nothing about the operator's intent
changed between those two spellings.

**(2) A `--gate-json` path that names an INPUT of this run is refused, and NOTHING is written.** The sink
is opened for writing before the run knows its own answer, so if it is the same artifact as the policy
file, the discovered `.candor/config`, a report being read (`gate --report`), or a chained dependency
report, arming **destroys the input**. Measured across four engines: `--policy P --gate-json P` armed over
`P`, the now-JSON policy parsed as zero rules, and a gate that exits 1 on the same code exited **0 with
`"ok": true`** — a machine-readable all-clear produced by deleting the question. The implementation MUST
detect this and exit 2 with a diagnostic naming both flags, having written nothing. This is the *only*
exempt cause in (1), and it is exempt for a reason that is not a carve-out: the path was never a sink, so
there is no verdict at it to go stale, and the alternative is destroying the operator's policy.

⟨0.28⟩ **AND THE WRITE MUST LAND ON THE SAME ARTIFACT THE COMPARISON RESOLVED.** The rule above is stated
about identity, and every engine implemented it in the COMPARISON while leaving the WRITE to whatever its
serializer did. Measured with a SINGLE `--gate-json` pointed at a symlink — an ordinary CI layout, one
`artifacts/verdict.json` linked into a shared directory:

- two engines published by temp-file-and-rename, which REPLACES the link instead of following it, so the
  real artifact kept a previous run's `{"ok": true}` while the gate FIRED and exit was 1;
- a third wrote the right document but still severed the link, so the next run's reader was pointed
  somewhere else;
- only one followed the link.

A stale green through a single flag, with no operator mistake at all. An implementation MUST resolve the
sink to its final artifact before writing and write THERE, leaving the link in place. Arming, the refusal
document and the verdict are all the same write and all bound by this.

⟨0.28⟩ **DEVICE+INODE IS NOT OPTIONAL WHERE THE PLATFORM OFFERS IT.** The parenthetical below was read as
advisory: measured, `--gate-json h1 --gate-json h2` over two HARDLINKS to one inode was refused as two
sinks by three engines and correctly gated as one by the fourth, and a duplicate naming a DANGLING symlink
beside its target split the other way. Both are one artifact and one verdict, so refusing is a FALSE
refusal of a legal command — the mirror of the stale green, and the reason the rule is about artifacts.
Implementations MUST compare device+inode when the platform exposes it, and MUST resolve a symlink to its
target even when the target does not exist yet.

Sameness here is a question about **artifacts, not strings**. `--policy /w/P --gate-json ./P` from `/w` is
the same file, and a comparison of path spellings says it is not — an engine that had this check still
failed to the spelling. Implementations MUST resolve both sides (symlinks included; device+inode where the
platform offers it) before comparing, and for a sink that does not exist yet, resolve its parent directory.
The rule that catches the release verifier catches this: *resolve the artifact, not just the string.*

⟨0.27⟩ **THE STREAM SINK: `-` IS NOT ARMED, AND IT IS NOT EXEMPT.** `--gate-json -` (and §3.1's `--json`,
which IS `--gate-json -` on the gate verbs) names a stream, and both halves of the arming rule change
shape there. Arming does not apply: a stream has no previous document to go stale, and a placeholder would
put TWO documents in a consumer's pipe. But the document-on-every-exit rule applies IN FULL: **if the sink
is `-` and the run exits 2 for ANY cause, the fail-closed document — the refusal or the ⟨0.21⟩ incomplete
verdict — is written to stdout, exactly once, as the stream's only content.** Measured, the engines had
quietly re-created the write-nothing carve-out on this sink, selected by CAUSE: an unhonourable policy
wrote the refusal to stdout in all four, while an unknown flag wrote it in ONE of four (swift) and left
stdout EMPTY in the rest — the same operator mistake, answered or not according to which early exit
happened to fire. A consumer of the stream is exactly the wrapper the file rule protects, minus the
staleness: it cannot re-read yesterday's document, but an empty stream throws it back to scraping stderr,
which is the distinction that made the incomplete-analysis defect a defect. The one honest gap is a run
that dies before it can write anything (a crash, a kill): the stream is then EMPTY, which a JSON consumer
reads as a parse failure — fail-closed by construction, and the reason arming is unnecessary here rather
than merely impossible. An engine MUST NOT print anything else to a stdout that carries a verdict (§3.3's
pure-JSON rule), which is also why the refusal replaces the placeholder strategy instead of joining it.

⟨0.28⟩ **TWO ARTIFACTS CANNOT SHARE ONE STREAM: `--json` BESIDE `--gate-json -` ON THE SCAN ROUTE IS
REFUSED.** On the gate verbs `--json` IS `--gate-json -` — one artifact named twice, and evaluated as such.
On the SCAN route `--json` means something else: write the REPORT to stdout. Asking for both puts a report
AND a verdict on one stream, and measured before this clause, four engines simply concatenated them: a
consumer calling `json.load()` on stdout over violating code got `Extra data` and therefore **no verdict at
all**, while the fifth refused. Four engines had settled on a reading the text above does not license.

The implementation MUST exit 2 with a diagnostic naming both flags, and the fail-closed document is the
stream's only content — so the refusal is decided BEFORE the report is written, not after. This is the same
answer as the repeated-sink rule directly below and for the same reason: when an instruction names one
destination for two different documents, the contract says so rather than picking an order and hoping the
reader stream-decodes. `--json <file>` beside `--gate-json -` is NOT this case — those are two artifacts
in two places, which is exactly what the operator asked for.

⟨0.28⟩ **ONE RUN NAMES ONE SINK. A REPEATED `--gate-json` IS REFUSED, AND EVERY PATH NAMED GETS THE
REFUSAL.** `--gate-json A --gate-json B` in a single invocation is a broken gate configuration, which §3.3
already treats as an exit-2 cause: the operator has stated where the verdict goes, twice, and the two
statements cannot both be honoured. The implementation MUST exit 2 with a diagnostic naming every path
given, and MUST write the refusal document to **each** of them (the stream, if `-` is among them, under
the stream rule above).

Writing to *each* is the load-bearing half, and it is not symmetry for its own sake. Measured across all
four code engines before this rung: **every one of them took the LAST path, wrote the verdict there, and
left the first exactly as it found it**. Pre-seed `A` with a previous run's `{"ok": true}`, run a gate
that fires, and `A` still says the code is clean.

(An earlier draft of this paragraph said one engine refused. It did not: that reading came from a
contaminated measurement — the engine in question was handed a second POSITIONAL, and what was recorded
as a duplicate-sink refusal was its extra-argument refusal. Corrected here because the pre-state is the
evidence this rung's choice rests on, and re-measured against a build from before the rung landed.) That is the stale green of
(1) reached by a spelling nobody had considered, and it is worse than the refusal case that motivated (1):
the run did not fail, the gate *did* fire, and the operator's own command named the path that lies. A CI
wrapper that appends `--gate-json artifacts/verdict.json` to a command a user has already configured with
one produces this on every run.

**EVERY ROUTE THAT ACCEPTS `--gate-json`.** The rule is about a RUN, not about one CLI. An engine that
exposes the gate through both a scan command and a `gate --report` verb MUST apply it on both — measured,
the rung was first implemented on the scan route in four engines while the verb route kept last-wins, so
`gate --report R --policy <fires> --gate-json A --gate-json B` exited 1 and published a previous run's
green at `A`. A route is not covered by its sibling.

⟨0.28⟩ **AND A REPEATED `--out` IS THE SAME RULE — filed as an open question by the rung that wrote the
sentence above, which is the tell.** This clause was recorded as "deferred" for the report sink while
being settled for the verdict sink, on no stated ground except that the verdict sink was the one being
worked on. The argument transfers without a word changed: `--out A --out B` names where the reports go,
twice, the two statements cannot both be honoured, and every engine takes the LAST — leaving `A` holding
a previous run's reports, readable as current, with nothing saying otherwise.

If anything the report sink is the WORSE case, because `--out` fans out on one engine: the stale set left
at `A` is a whole prefix of per-crate reports, and a `gate --report A` over it answers from a scan that
never ran. So: **refused at exit 2, with the fail-closed report written to every prefix named** — the
report-sink analogue of "every path named gets the refusal", under §3.3.1's arming rules.

*Two spellings of one rule is the habit this document has now paid for in six separate places in a single
rung. The general form, stated once: when a rule is settled for one sink, the question is not whether it
applies to the other — it is what makes the other different, answered in writing, or it applies.*

⟨0.32⟩ **AND THE DEFAULT PREFIX IS ANSWERED BY A MARKER, NOT BY ARMING IT.**

Everything above is about a prefix the operator NAMED. A run given no `--out` still writes reports — to
its default prefix — and a refusal leaves whatever the last successful run put there, readable as
current. MEASURED in all four engines: scan a tree green, change it so it now violates, then refuse for
any reason; `gate --report <tree>` answers `policy ✓` at exit 0 off the previous run's bytes. The harm is
the one this whole section exists to prevent, and the only thing separating it from the covered case is
whether a flag was typed.

**Arming the default prefix is NOT the answer, and this is recorded because it was tried.** An engine
that overwrites reports it was never told it owned destroys data: measured, a run that died in argv
parsing replaced a COMMITTED report in its own repository. Naming a prefix is a declaration; a default is
a convention, and a convention does not license destroying a file the operator may be keeping.

So a refusing run **MUST** write a **refusal marker** at `<prefix>.refused.json` for the prefix it would
have written, carrying at minimum the `prefix` it belongs to, the `target` scanned, and a `reason`
naming the cause. It overwrites no report. A run that COMPLETES its write phase **MUST** remove the
marker for that prefix, so the marker's presence means exactly "the most recent attempt over this prefix
refused".

A consumer resolving a `--report` locator **MUST** consult the marker and refuse (exit 2) when one is
present for the reports it is about to read:
  · a **directory** locator → the marker beside `<dir>/.candor/report`;
  · a **prefix** locator → `<prefix>.refused.json`;
  · a **direct-file** locator → any `*.refused.json` in that file's directory **whose recorded `prefix`
    covers the file**. The marker carries its prefix precisely so this case is answerable: a direct-file
    locator accepts any `.json` name whatever its dot-segments, so the prefix cannot be recovered from
    the filename and must be read from the marker.

**Why a marker rather than a check.** A consumer cannot compute this for itself. The hazard is an EVENT —
a refusal that happened AFTER these bytes were written — witnessed only by the run that refused. No
function of the report and the tree recovers it: `analyzed.digest` is over the sorted analyzed-qual set,
so a changed body under an unchanged name is byte-identical, and the §2.1 producing-build machinery is
about producer identity, which §3.3.1 already scopes away from a verb that only READS a report. The
defence has to be written down by the run that knows.

**The failure direction is deliberate.** A marker that is lost or deleted fails open — exactly as today —
so this is strictly better than the status quo and never worse. A marker left behind by a refusal that is
never retried fails CLOSED, and that is the correct way round: the reports under it really are from a
scan whose successor refused.

**THE INPUT EXEMPTION COVERS THE PATH, NOT THE RUN.** Rule (2) says a sink naming an input of this run is
refused having written NOTHING, and it outranks this refusal — for *that path*. Every OTHER path named in
the same argv still gets the refusal document, and a `-` among them always does: a stream has no input to
destroy, so (2)'s justification cannot reach it. Measured in all five engines before this clause:
`--gate-json <the policy> --gate-json B` exited 2 with the policy correctly intact and `B` still holding a
pre-seeded `{"ok": true}`, and with `-` in place of `B` stdout was left EMPTY. The operator named `B` as
where the verdict goes, the run declined to produce one, and `B` went on saying the code was clean.

The choice of refusal over last-wins follows from the same place as (2): when an instruction is ambiguous,
this contract's answer is to say so, not to pick. Last-wins is defensible for a flag that names a
preference; it is not defensible for a flag that names where the answer is published, because the reader
of the losing path has no way to learn that it lost. Two identical spellings of one path are ONE sink, not
two — the artifact rule from (2) applies here as well, so `--gate-json P --gate-json ./P` from `P`'s own
directory is a single sink and is not refused.

⟨0.24⟩ **PRECEDENCE GOVERNS ANSWERABILITY REFUSALS. A CORRUPTION REFUSAL DOMINATES EVERYTHING, INCLUDING
A CERTAIN VIOLATION — and that is a BOUNDARY, not a carve-out.** The distinction is load-bearing and the
two look identical from the exit code:

- An **answerability** refusal says *the report is trustworthy and this particular rule cannot be decided
  from it.* The evidence for the OTHER rules is carried, so a rule that fires is certain, Lemma 2 applies,
  and exit 1 dominates.
- A **corruption** refusal says *this report cannot be read as a report.* That undermines the premise the
  precedence argument runs on. A violation "computed from" a document with an unparseable §2 key is not a
  certain finding — it is a finding computed from bytes of unknown meaning, and reporting exit 1 would
  assert a confidence the input does not support.

So `netClass: 1` moving exit 1 → 2 is **correct**, and it is not the precedence ruling being walked back.
Applying "a violation dominates" there would be the mirror error to the one `5a8cf48` just fixed: charging
something the evidence does not carry.

The general test, and the reason this is a boundary rather than a carve-out: **ask whether the refusal's
cause undermines the premise that the fired rule's evidence was carried.** If it does not, the violation
dominates. If it does, nothing downstream of that input is certain. A carve-out is an exception with no
account of itself; this one is derived from the same Lemma the precedence rule is.

⟨0.24⟩ **THE OPERATIONAL FORM OF MINIMAL REFUSAL: WITHHOLD PER (RULE, FUNCTION) — and applying the
precedence ruling WITHOUT this introduces a FABRICATION.** This is not a refinement; it is the half of
`7271c69` that makes it safe, and it was found by implementing the ruling rather than by reading it.

Once a firing rule stops short-circuiting the refusal, the evaluator reaches code it never reached before.
Measured on the reference engine: a scoped `deny Unknown[unresolved]` over an entry whose `Unknown` is
**INHERITED and reasonless** began emitting an actual **violation record**, because the class-set helper
floors an empty set at `unresolved`. **That floor is the correct fail-closed default for a MATCHER — "could
this rule apply?" — and the wrong basis for a FIRING — "did it?"** The two questions had shared one helper
safely only because the refusal short-circuited before the difference could show.

So the rule is: **a rule FIRES on a function only where the match is evidenced by that function's own
entry, and is WITHHELD exactly where it is not.** Withholding is per `(rule, function, EFFECT)` — never
whole-policy, and ⟨0.24⟩ **never per `(rule, function)` either, which is what this clause first said and
which reintroduces the exact harm the precedence ruling exists to remove.** Measured on candor-ts with
`deny Fs Net[unknown-host] app` over ONE function carrying a certain `Fs` beside a `netClass`-less `Net`:

    per (rule, function)          -> exit 2, refused, `violations` key ABSENT   ← the certain Fs is DELETED
    per (rule, function, effect)  -> exit 1, violations: [{app.mixed, [Fs]}]

A single rule can name several effects, and the evidence for them is independent. Withholding at the pair
level lets one unevidenced effect suppress a *certain* finding standing beside it in the same rule and the
same function — which is `7271c69`'s defect, arrived at through the fix for `7271c69`'s defect. The same
rule may therefore fire on one function and be withheld on another, AND fire for one of its effects while
being withheld for another on that same function; the verdict carries both — exit 1 for what fired, a
disclosure for what could not be evaluated. That is already what the
minimal-refusal rule says; what was missing was saying it about the *firing* side rather than only the
*refusing* side.

**Two things generalise here, and both are expensive to learn twice.**

*A fail-closed default is not portable between a predicate that GUARDS and a predicate that CHARGES.*
Flooring an unknown class set at `unresolved` makes a matcher conservative — it considers the rule
applicable and lets the refusal machinery decide. The identical floor, read as grounds to emit a violation,
asserts a reason nobody recorded. Same constant, same helper, opposite direction of harm.

*And a soundness fix is a fabrication risk in its own right.* This project already records that killing a
fabrication is where silent under-reports get introduced ([[feedback-fabrication-fixes-cause-misses]]);
this is the mirror, and it arrived within an hour of the ruling. **The new-reachability question is the one
to ask of any short-circuit removal: what code now runs that never ran, and what did it assume about who
would call it?** Three engines had already landed the precedence fix before this surfaced.

⟨0.24⟩ **PRECEDENCE BINDS THE VERDICT, NOT THE POLICY GATE — a certain BASELINE regression is deleted by an
unrelated refusal, in all four engines.** This is the ruling's fifth mirror and the broadest: I wrote
"a certain violation dominates a refusal" while thinking only of the policy gate, and every engine
implemented it against the policy gate's own violation list. **The AS-EFF-005 baseline guard is a different
violation producer**, it runs deliberately EARLIER, and it records into the same verdict. Measured — a pure
function gains an `Fs` call, scanned against a frozen baseline:

                        control (no policy)      + a policy with a bad token
    rust / java / ts / swift    exit 1, ["AS-EFF-005"]     exit 2, NO `violations` key — all four

So **a typo in a policy token downgrades "your change added an effect" to "could not evaluate"**, and the
regression disappears from the machine channel. It survives on stderr, so the human sees it and CI does not
— the same split this rung exists to close. It is fail-LOUD (`ok:false`), so it is not a stale green; it is
a lost finding.

Three individually-correct decisions composed into it, which is why no engine caught it: the baseline guard
runs before the policy gate *by design*; the precedence repair was scoped to the gate's violation list; and
the rule that a refusal document carries no `violations` key was justified by every exit-2 site running
before anything could be recorded — **true until a producer's evidence sat upstream of the refusal.** That
last one is worth stating plainly: **it was a claim about ORDERING that reads as a claim about SHAPE**, and
it stopped being true when the ordering changed underneath it.

**So the rule is over the verdict.** Any violation the run has already established on carried evidence —
whatever subsystem produced it: the policy gate, the baseline ratchet, or anything later — dominates a
refusal and MUST appear in the document. An implementation MUST NOT key its refusal arm on a predicate that
conflates *"this run ended refused"* with *"this run evaluated nothing"*, which is exactly the conflation
measured here.

⟨0.24⟩ **NEITHER RULE HAS A CARVE-OUT, AND BOTH OF MINE DID.** candor-rust implemented the two clauses
above, then reported the two places they stop short. Both stops were mine, both were inherited from where
the defect happened to be found, and the reasoning in each clause reaches further than the clause does.

**(a) Precedence binds `forbid` and `allow` too.** Measured: `deny Fs app.fsUnit` (fires) beside
`forbid app -> dep` (refused whole-policy) still exits 2, with the certain violation absent from the
document. **Lemma 2 does not care which KIND of refusal stands beside the firing rule** — `Reject` is
upward-closed, so a rule that already fires on carried evidence stays fired however the refused rule would
have resolved. The whole-policy granularity of a `forbid`/`allow` refusal (§3.1) governs *which rules go
unevaluated*; it was never a licence to suppress a violation that was evaluated and certain. The engine
declined to change this unilaterally because §3.1's prose makes those refusals whole-policy and it wanted a
ruling rather than a divergence. Correct instinct — and the ruling is that the precedence is general.

**(b) The refusal document has no exempt cause.** §3.3 enumerates exit-2 causes including a broken gate
CONFIG or an unreadable policy, and mandates writing no document there; two tests in candor-rust pin that.
But the argument I used to require a document — *a CI wrapper reading the path unconditionally re-reads the
PREVIOUS run's verdict as current* — is **exactly as true for an unreadable policy as for an answerability
refusal.** A stale green does not care why this run declined to overwrite it. So: **if `--gate-json` was
requested and the run exits 2 for ANY reason, a fail-closed document is written at that path.** An
unreadable policy has no rules to reason about, which is precisely why the document carries no `violations`
key — the shape already says "no claim about violations", and that is the honest thing to say when the
policy could not be read at all.

**The pattern in both is one thing: a rule stated over the instance it was found in rather than over the
condition that makes it true.** A carve-out in a fail-closed rule is a fail-open path with a reason attached
— and in each of these two the reason was only ever "the measurement that prompted the clause did not
happen to cover this case".

⟨0.27⟩ **THE COMPOSED DOCUMENT: `refused` AND `violations` ARE MUTUALLY EXCLUSIVE, AND THE COMPOSED SHAPE
IS A VERDICT.** The precedence rulings above say a certain violation dominates a refusal (exit 1) and MUST
appear in the document, and the refusal-document clause says what a refusal writes — but neither said what
the ONE document looks like when both outcomes are live, and measured on the same input (a baseline
regression beside a policy token that cannot be honoured, `--gate-json G`) the four engines wrote FOUR
spellings of it:

    java    refused:true + reason + violations + unevaluated
    rust    refused:true + reason + violations               — no unevaluated
    ts      violations + unevaluated                         — the correct shape
    swift   violations only                                  — the refusal vanishes from the machine channel

The rule: **a document that carries `violations` is a VERDICT, never a refusal document, and it MUST NOT
carry `refused`.** `refused: true` is the refusal document's discriminator, and its meaning to a consumer
is pinned three clauses up: *the gate is making no claim about violations* — which is precisely the claim
a violations-bearing document IS making. A document carrying both keys gives one key two contradictory
readings, and a consumer keying on `refused` (which the refusal-document clause invites) files a certain
violation under "no claim about violations". The two shapes MUST stay disjoint on `refused`; that
disjointness is what makes keying on it safe.

**The refusal is disclosed in `unevaluated`, and on a whole-policy refusal that list carries EVERY rule of
the refused policy** — one entry per rule, the RAW line verbatim: the unhonourable line(s) with their
specific cause, and each remaining rule with a `why` naming the whole-policy refusal. Not only the
offending line: a consumer that finds `deny Fs` absent from `unevaluated` on an exit-1 document reads it as
*enforced and passed*, which is a per-rule false all-clear arriving through the disclosure — measured in
candor-ts, which listed only the bad token's line. Where the policy has no lines to name (the file itself
unreadable), the list carries ONE entry naming the whole policy — candor-ts's spelling, `(entire policy
<locator> — unreadable, no rules parsed)`, is the model; the wording is engine-natural, the non-emptiness
is not, because an exit-1 document with `violations` and no `unevaluated` claims the policy ran and passed.
Nothing here weakens the SOLE-refusal case: with no established
violation the run still exits 2 with the refusal document, on both routes — a bad token establishes nothing
from the policy itself, so `gate --report` with a firing `deny Fs` beside a bad token correctly refuses
whole-policy (the answerability refusals, which leave the parsed rules trustworthy, are the exit-1 +
`unevaluated` case).

⟨0.27⟩ **A rule whose SCOPE binds nothing rides the verdict document as `zeroMatch` — see §3.1's
zero-match clause for the shape; it is named here only because it is the third disclosure list a composed
verdict can carry** (`violations`, `unevaluated`, `zeroMatch`), and the three answer different questions:
what fired, what could not be decided, and what was decided over nothing.

⟨0.24⟩ **A SCOPE DOES NOT SHRINK THE QUESTION — the answerability test runs over what the in-scope
function REACHES, not over the in-scope entry's own class set. Adding a scope currently RE-OPENS the
fail-open the third refusal exists to close, in ALL FOUR ENGINES.** Measured:

    app.web.go   Unknown, own unknownWhy [dispatch:virtual], calls [lib.B.g]
    lib.B.g      Unknown inherited, NO reason, NO calls      ← the uncomputable state

    deny Unknown[reflect] app.web   →  rust 0  ts 0  java 0  swift 0     ← GREEN
    deny Unknown[reflect]           →  rust 2  ts 2  java 2  swift 2     ← correctly refused

The unscoped form of the very same question is refused by every engine; adding `app.web` makes all four
answer it. And the CONTROL is decisive: supply `lib.B.g`'s reason as `reflect` and all four go to **exit
1**. The absent datum flips the verdict 0→1, so by the minimal-refusal rule directly above, this is the
second bullet — it does not yet fire, and the missing datum could still make it fire — and it MUST be
refused.

The cause is uniform: each engine tests whether the *in-scope entry's own* class set is empty, and never
asks whether an entry REACHABLE from it had its reason channel dropped. The scope selects which functions
the rule applies to; it does not license reading a smaller graph. So: **propagate an unknowable-contribution
marker through the same transitive fixpoint that builds the class set, and refuse on an INCOMPLETE set, not
only on an EMPTY one.**

This one is worth stating as a general shape, because it is the second time in this rung the same mistake
has appeared: *a guard written against the value at hand rather than against the closure the value stands
for.* The class set is a transitive object; every predicate over it must be too. An implementation that
answers correctly on the bare form and green on the scoped form has not scoped the rule — it has scoped
the evidence.

⟨0.24⟩ **THE MANIFEST DOES NOT TRAVEL, AND THIS VERB IS WHERE THAT BITES.** The verb leans on *absent is
absent*. PAPER3 Def 24 already says a `{count, digest}` manifest cannot discharge that — it cannot separate
*dropped* from *pure* — and measurement on the reference engine found the situation is worse than the
definition states, in three ways. `count − |functions|` is simply the pure count (970 − 390 = 580 on a real
report), so a dropped unit is *arithmetically identical* to a pure one. The `digest` is over the sorted
**analyzed qual set**, of which a consumer holds only the effectful subset — so it **cannot recompute it**;
it is a same-producer re-scan check, not a cross-boundary one. And `count < |functions|` is not a usable
corruption signal either, because ⟨0.23⟩ `interfaceUnion` entries are appended to `functions` keyed by a
bodyless declaration that is not a node, making the inequality legitimately reachable.

What would close it is the **per-unit analyzed NAME SET**. That set exists today — it is exactly the §2.2
callgraph node set — but it lives in a **sidecar**, which this verb refuses by construction. So the rung is
either an envelope-level list of analyzed units or making the sidecar part of the addressed artifact. Until
one of those lands, **the ⟨0.21⟩ purity claim is trustworthy within one producer and unverifiable across a
trust boundary** — which is precisely where the supply-chain verb is used. An engine SHOULD say so rather
than let a consumer infer otherwise from a green verdict.

⟨0.24⟩ **THE MODEL-VERSUS-CONTRACT RESIDUAL IS RESOLVED — and it MOVED before it closed, which is the part
to remember.** The first engine to run this differential found **100 disagreements, all one family**: a
signature containing `Db` under `deny Net`, model REJECT and engine pass, because Def 2 carried
`Db ⊑ₑ Net`. That was the *theory's* fault — an embedded store has no egress — and correcting the preorder
took it to zero.

**The second engine then found 100 disagreements again, in a NEW family**: `Llm ∈ S` with `Net ∉ S`, the
surviving refinement pair. Same shape, same direction, same count. **And this paragraph still named `Db`** —
stale in the one place an auditor would check, hours after the fix that made it so. That is the third
instance in one day of a corrected assertion outliving its correction in a second location, and the first
where the stale copy was written the same day as the fix.

The `Llm` family is **not a defect in either layer: it is UNREACHABLE.** Every engine co-emits `Llm` and
`Net` at a model-provider call site — which is the very fact that makes the refinement hold — so
`Llm ∈ S ∧ Net ∉ S` describes **32 768 of the lattice's 131 072 points and none of them can be produced.**
Restricted to reachable signatures the differential is **0 of 1280**, and the reference model now checks it
directly: *refinement ≡ plain membership over all 98 304 reachable signatures.*

**The standing rule for anyone running this differential: a model quantifying over all of `L` will fire
CORRECTLY on points that do not exist.** Reachability is a precondition of the comparison, not a detail of
it. `reference/policy_model.py` exposes `is_reachable()` and `reachable_lattice()`; use them. Worth naming
what that condition is — it is the shape PAPER1's **(W)** was reaching for and mis-stated. (W) was written
`Unknown ∈ S ⇒ D ≠ ∅`, whose antecedent is unsatisfiable, so it constrained nothing; the same shape over the
refinement preorder is satisfiable and constrains a quarter of the lattice. That is the whole difference
between a well-formedness condition and a sentence.

The residual that IS real is narrower and is a classifier question rather than a gate one: a **networked**
DB call is egress a `deny Net` gate does not see. `Db` and `Net` overlap without either refining the other.

⟨0.24⟩ **Three surfaces this document NAMED and never DEFINED.** Each is cited elsewhere as though it were
specified — one of them as "the canonical oracle" for a question this section answers — and an implementer
could not have built any of them from what was written. This is the condition that produced the `--class`
divergence (named, load-bearing, undefined, four implementations), so they are defined here rather than
left to convention.

- **`blindspots --stats`** ⟨0.20⟩ — the §4 **reason-class distribution** over the same `sources` set
  `blindspots` reports: a count per class, using §6.2's projection, plus `totalUnknown`. It answers "what
  KIND of blind spot dominates" before an author drills in with `--class`. Its output contract lived only
  in the conformance suite.
- **`reports <prefix>`** — enumerates the report files a prefix locator resolves to, and nothing else. It
  is the **canonical answer to "what counts as a report"**, which is why §2.2's sidecar-reservation rule
  cites it, and why its listing sidecars was recorded there as a defect rather than a cosmetic one. It MUST
  apply exactly the §2.2 exclusion — an engine whose `reports` output disagrees with what its own queries
  load has two answers to one question.
- **The `encountered-*` sidecar family** — engine-local artefacts recording what a scan saw, reserved in
  §2.2 alongside `callgraph`/`hierarchy`/`calibrated`/`layerreach`/`locs`/`gate`. They carry no interchange
  contract: no consumer may depend on their shape or presence. They are named here **only** so the reserved
  set is complete, because that set's whole job is to be exhaustive — an unlisted suffix falls back into
  the report candidate set.

`callers --include-unknown` ⟨0.7⟩ adds **`possibleViaUnknownDispatch`** to the `callers` output: the
*unresolved-dispatch frontier*. The plain `callers` set (`transitive`) is a **confirmed** lower bound: a
function that reaches `<fn>` only through a call the engine charged `Unknown` with an unresolved
`dispatch:OWNER.M` reason (a bounded-CHA fan-out, a dynamic receiver of a known type) is *correctly* absent
from `transitive`, because the engine refuses to fabricate the edge. `possibleViaUnknownDispatch` discloses exactly
those: each entry `{ "fn", "viaDispatchOn" }` names a function `fn` that (1) carries a `dispatch:OWNER.M`
`unknownWhy`, (2) is not already a confirmed transitive caller, and (3) for which some confirmed reacher
(in `transitive ∪ {<fn>}`) is an **override of `OWNER.M`** (its method's simple name is `M` and its
declaring type is a subtype of `OWNER` per the §2.2 hierarchy sidecar). `viaDispatchOn` is the dispatched
member `OWNER.M` it travels through. The subtype check (vs a bare simple-name match) is what removes false
positives: an unrelated same-named dispatch is not listed unless its owner actually sits above a reaching
override. This is a **disclosed lower-bound expansion, never an assertion**: it says "this *may* reach
`<fn>` through a dispatch I could not resolve," and reports only the frontier dispatch-source functions (the
smaller, more informative set), not their transitive cones.

⟨0.27⟩ **A rule whose SCOPE matches no function is UNANSWERABLE, and MUST be disclosed rather
than scored as satisfied.** A `deny`/`forbid` rule naming a layer that binds nothing was evaluated and
bound nothing, so it cannot have caught anything — yet every engine scores it as passing, which makes a
one-character typo in a layer name a permanently green gate. Measured 2026-08-05 in candor-rust,
candor-swift and candor-ts: `deny Net orders` exits 1 on a real violation and `deny Net ordrs` exits 0
with `policy ✓`, and `unverified` then reports the layer as *"PROVABLY clean"*.

The asymmetry is the tell: a typo'd **effect** token already exits 2 naming the accepted vocabulary,
while a typo'd **layer** token binds nothing and passes. Same file, same rule, opposite treatment.

The remedy is DISCLOSURE, not refusal. Exit 2 would be wrong: a zero-match rule is legitimate when one
policy is shared across repositories or modules and a layer exists in only some of them. So a producer
MUST report each such rule — verbatim, so the reader can see the typo — and MUST NOT change the verdict
on account of it.

⟨0.27⟩ **…and the `--gate-json` VERDICT CARRIES THE SAME LIST, under the pinned key `zeroMatch`.** This
sentence read "SHOULD carry the same list" and named no key — the same unpinned state that produced the
`--class` divergence — and measured on all FIVE engines the list was stderr-only: a machine consumer
could not see that a rule bound nothing, which is the very blindness this clause exists to close (a CI
wrapper reads the document, and a typo'd scope was invisible in it — the silently green gate, one channel
over). The shape:

    "zeroMatch": [ "<the RAW rule line, verbatim>", … ]

sorted by Unicode code point and deduplicated (the `viaDispatchOn` collation, for the same reason: a
field no consumer re-parses must not be able to differ between engines), OMITTED when empty so every
fully-binding verdict gains NO key from this clause. (Not literally byte-identical to a pre-⟨0.27⟩
document — the envelope's `spec` moves with the floor either way — but a consumer diffing verdicts across
the upgrade sees no new field on any input where every rule bound something.) It rides **VERDICT
documents only** — the
exit-0/1 shape, on BOTH routes (`scan --policy` and `gate --report`, which §3.1's byte-equality MUST
forces to agree here) — and never the refusal document: a refused run evaluated nothing, so it is not
entitled to the claim "this rule was evaluated and bound nothing". It MUST NOT change `ok` or the exit
code — it is the third disclosure list a verdict can carry, beside `violations` (what fired) and
`unevaluated` (what could not be decided): this one is what was decided over nothing.

**Status: the console disclosure is implemented four-way** (candor-swift led it; candor-java, candor-rust
and candor-ts followed), pinned by conformance **PART 32** — which pins the disclosure, that the verdict
and exit code are UNCHANGED by it, and that a SCOPELESS `deny` is exempt (it binds every function by
construction, so it can never be this kind of typo). ⟨0.27⟩ The `zeroMatch` verdict key is pinned by
conformance **PART 36** on all five engines, both routes.

⟨0.24⟩ **A `dispatch:` detail with NO DOT names no owner, so condition (3) is UNANSWERABLE — and an
unanswerable condition MUST NOT be scored as a failed one.** §4 reserves the dot-free detail for an
unresolved dispatch where the engine could not form an owner type at all. Condition (3) asks whether a
confirmed reacher overrides `OWNER.M`; with no `OWNER` and no `M` there is nothing to test. Such an entry
MUST therefore be **disclosed** with `viaDispatchOn` set to the raw detail verbatim, and MUST NOT be
dropped. Dropping it is absence under a key that could have carried an answer: a consumer reads an omission
from `possibleViaUnknownDispatch` as "no function may reach the target through an unresolved dispatch," and
that is exactly the claim the engine is not entitled to make.

This is the same direction the **no-hierarchy fallback already takes** one rung up: with no §2.2 sidecar,
condition (3)'s subtype test is unanswerable, and the specified behaviour is to over-list by simple name
rather than to drop. A dot-free detail is that situation one rung further down — no owner *and* no member —
and takes the same answer. The frontier over-lists by construction and asserts nothing, so the cost of a
spurious entry is precision; the cost of a dropped one is a false all-clear on the query.

Measured on the reference implementation before this clause: a report carrying
`dispatch:untyped cross-package receiver` produced a frontier containing only the dotted entry, in **both**
the hierarchy and fallback arms. The dot-free source appeared nowhere in the output and no diagnostic named
it. Note also that the parenthetical this clause replaces was **stale**: the Rust scanner *does* emit
`dispatch:`, and did so for every dispatch reason in a 1062-report census — so "returns `[]` consistently,
N/A by language model" was reading a silent drop as a language property.

⟨0.24⟩ **An EMPTY §2.2 hierarchy sidecar and an ABSENT one are the SAME INPUT to this query, and both
take the over-listing fallback.** An engine MUST NOT read a sidecar that parses to `{}` as the positive
claim "no type has a supertype" and score condition (3) as *failed* on that basis — that would collapse the
frontier to empty across every dotted dispatch source at once, and a consumer reads an empty frontier as
"no function may reach the target through an unresolved dispatch". An empty sidecar is far more often "the
hierarchy pass found nothing, was not run, or wrote a stub" than a claim about the type graph, and the
distinction is not recoverable from the file. Absent, empty, and unparseable therefore all mean *the
subtype test is unanswerable*, which by the rule above means over-list, not drop.

**A dot-free detail MUST be recognised STRUCTURALLY** (the detail contains no `.`) and short-circuited
*before* the owner/member split is attempted — not by matching a known wording. Two hazards make this a
requirement rather than a style note, both measured on the reference implementation:

- The split helpers fall back to the WHOLE STRING when there is no dot, and they are applied to the reason
  detail *and* to the confirmed reachers' qualified names. The override test therefore degenerates into
  **string equality between a reason detail and a function name**. Measured: a dot-free detail that happens
  to equal a reacher's qual was *disclosed*, and in the hierarchy arm the subtype check passed **only by
  reflexivity** (`ty == owner`) over a string that is not a type name — the sidecar was never consulted.
  The entry belonged in the output under this clause anyway, so the pre-fix behaviour was **right for the
  wrong reason**, which is the shape that hides a gap rather than showing one.
- Without the short-circuit the same detail can be **disclosed in one arm and dropped in the other**,
  decided by nothing but whether a §2.2 sidecar happens to exist. Measured: a dot-free detail equal to a
  dotted reacher's simple method name matched in the no-hierarchy arm and was dropped in the hierarchy arm.

A wording-based check is an ALLOWLIST, and everything it omits is a silent drop — the defect itself. It
also fails on arrival: an engine whose dot-free detail is a plain identifier rather than a phrase would be
matched against reacher names by exactly the equality above.

⟨0.24⟩ **The MIXED source.** One function may carry several `dispatch:` reasons — dotted ones that pass
condition (3) and dot-free ones that cannot be evaluated. It gets **one** entry, whose `viaDispatchOn` is
the **sorted, deduplicated, comma-joined** union of the dispatched members (`M`, for each dotted reason
that passed) and the raw details (for each dot-free one). Sorted and deduplicated so two engines cannot
disagree on a field neither of them re-parses.

**"Sorted" means by UNICODE CODE POINT**, equivalently by UTF-8 byte order — the two orders coincide, and
naming both is deliberate because the natural implementation differs per language. Rust's `BTreeSet<&str>`
gives it for free. Java's `String.compareTo` and JavaScript's default `Array.sort` both order by **UTF-16
code unit**, which agrees with code-point order on ASCII and *disagrees above the BMP*: a supplementary
character sorts before `U+E000..U+FFFF` under UTF-16 because it is stored as a surrogate pair. Every detail
any engine emits today is ASCII, so nothing diverges yet — but all four analysed languages permit non-ASCII
identifiers, and `<owner>.<member>` is built from user identifiers, so this is reachable rather than
theoretical. An engine whose natural comparator is UTF-16 MUST compare by code point explicitly.

**"UTF-8 byte order" names the ORDER, not the METHOD — do not implement it by encoding to UTF-8.** In a
language whose strings are UTF-16 (Java, JavaScript), an *unpaired surrogate* is representable in memory
but has no UTF-8 encoding, so every lone surrogate encodes to the same replacement byte. A comparator built
on that encoding is **order-correct and cardinality-lossy at once**: two distinct details differing only in
a lone surrogate compare EQUAL, and a set-backed accumulator reads equal as duplicate and **silently drops
one from the join** — reintroducing, inside the conformance fix, the exact drop class this rung exists to
close. Measured: the encoding-based comparator passes the ordering test and fails a lone-surrogate
cardinality test. Compare code points directly.

Note also what is *not* checkable across engines here: a lone surrogate has no UTF-8 encoding and therefore
cannot cross the JSON wire in any engine, so cross-impl fixtures MUST NOT assert a lone-surrogate literal.
**Cardinality survives that channel and identity does not** — pin the count, not the string.

This is a small thing pinned at length on purpose: an unspecified collation on a field no consumer parses
is invisible until a conformance row is written years later and fails for a reason nobody can reconstruct; `viaDispatchOn` is a disclosure string, and candor never
parses an owner back out of it. A detail containing a comma would be ambiguous to a consumer that splits on
one, and that is accepted deliberately rather than escaped: no engine emits one, and the alternatives are a
new sub-grammar in a pinned field, or truncating the detail — which re-opens the drop this clause exists to
close.

⟨0.24⟩ The cross-impl suite **WILL pin** the frontier output including the dot-free arm — it does not yet;
`frontier_differential.py` has no dot-free arm today and its own header still carries the stale "rust has no
`dispatch:`" rationale. Stated in the future tense on review, because the sentence previously claimed a pin
that does not exist while this rung's own changelog entry says it is "NOT yet conformance-pinned". A spec
that overstates its own coverage is the same failure as an engine that overstates its own: the reader stops
looking. When it lands it will cover the engines that
IMPLEMENT this query — the Rust, JVM and TypeScript query surfaces. The Swift engine deliberately ships no
`callers` verb (it is a producer that writes the §2.2 sidecar *for* those consumers); ⟨0.24⟩ binds it only
through §4 and the §6.2 class projection, which is pinned separately.

### 3.2 Pre-edit and structural tools (SHOULD)

Two tools answer what an agent asks *around* an edit — deterministically, where a model would otherwise
guess (and, the evidence shows, under-count):

- **whatif `<fn>` `<Effect>`**: the **pre-edit verdict**. Crosses the blast radius (every transitive caller
  of `<fn>` would gain `<Effect>`) with the active policy and reports which functions would **violate** a
  `deny`/`pure` boundary *before* the edit, instead of edit → run the gate → revert. It is the pre-edit
  form of **AS-EFF-006**.
- **rewire `<baseline>`**: the **de-wiring / structural-regression** check. Diffs the current call graph
  against a baseline and flags edges a function **dropped** (a call it made before and no longer makes). An
  effect gate checks effect *boundaries*, not correctness, so it can be satisfied by *disconnecting*
  functionality: a function stops calling the chain that performs a forbidden effect, the gate passes, the
  feature breaks. That removal is invisible to the effect diff (a pure function dropping a call changes no
  effect) but present in the call graph. rewire is the **structural dual of the baseline guard
  (AS-EFF-005)**: 005 flags an effect *gained* versus the baseline, rewire flags a call *dropped*. It is
  **advisory**; run it ALONGSIDE the policy gate: a green gate **plus** a clean rewire means the boundary
  was respected *without* gutting the feature. A gate alone is necessary, never sufficient.

Their JSON shapes (the verdict + blast radius the conformance suite pins across both engines):

```text
whatif   { "of":[fn…], "effect", "affected":[fn…], "violations":[ { "fn", "rule" } ], "ok":bool }
         ⟨0.24⟩ over an INCOMPLETE report: "incomplete":true, "unanalyzed":[…], and **`ok` OMITTED**
rewire   { "dropped":[ { "caller", "no_longer_calls":[fn…] } ] }
```

### 3.3 The command-line surface (REQUIRED)

The mode names above are conceptual; this fixes the *invocation* so a person or an agent drives any
engine identically. Every implementation's scanner MUST accept:

| flag | meaning |
|---|---|
| `<target>` (positional) | what to scan — a directory, a built artifact, or a source file, as the language dictates. |
| `--policy <file>` | enforce a §6.2 policy file: exit **1** on a violation, **2** if the file is unreadable (never silently gate-pass). MUST also honour a `CANDOR_POLICY` environment variable when the flag is absent; the flag takes precedence. |
| `--json` | emit the §2 report as JSON to **stdout** (the report envelope; the §2.2 sidecar need not go to stdout). stdout MUST then be *pure JSON* — any human/progress output goes to stderr, so the report pipes cleanly. An engine MAY additionally accept `--json <file>` to write the report to a file. |
| `--gate-json <file>` ⟨0.8⟩ | write the **structured gate verdict** (below) as JSON — the machine analog of the `AS-EFF` console lines, from the SAME check that sets the exit code. Written whenever the FLAG is given: with a gate active it re-emits that gate's verdict; with no gate configured it writes the clean verdict `{ ok: true, violations: [] }`. On **exit 2** it writes a **fail-closed document for EVERY cause** ⟨0.24⟩ — the `ok:false` + `refused:true` refusal for a broken gate config (unreadable policy, invalid baseline, **unknown flag**), or the ⟨0.21⟩ machine-legible incomplete verdict (§3.3.1) for an incomplete analysis. *This entry read "never for a broken gate config" until ⟨0.27⟩ — the reading §3.1 superseded, surviving in a second location. A carve-out here is a fail-open path: a refusal that writes nothing leaves the previous run's green document on disk.* The one case that writes nothing is a `--gate-json` path that **cannot be honoured as a sink** — no value given, or the same artifact as an INPUT this run must read (§3.3.1). Does not change the exit code. |
| `--version` / `-V` | print the engine build **and the candor-spec version it implements** (the §2.1 envelope `spec`), on the same or an adjacent line. |
| `--help` / `-h` | print a usage summary that lists these flags. |
| `--agents` | print the engine's **embedded** agent contract (item 11) — its `AGENTS.md`, prefixed by the canonical version header `<!-- candor-<engine> <version> · … -->` so a consumer can tell which build's contract it is reading. The embedded copy MUST equal the repo's `AGENTS.md` (§7 item 11's drift gate). |

⟨0.31⟩ **(d) AN UNEVALUABLE TARGET — the walk admitted no file this engine can read.** A target that
exists but holds nothing of this engine's kind is a REFUSAL (exit 2), not a clean scan: *"I found nothing
to open"* and *"I opened everything and judged it"* are different claims, and exit 0 makes the second. A
typo'd path in CI, a module that moved, an unbuilt project — each of these is a permanent green otherwise.
Three engines already refused this shape before it was enumerated; this clause writes down the cause they
were minting, and brings the fourth into line.

**THIS SUPERSEDES THE ⟨0.24⟩ JUDGED-NOTHING RULING FOR THE SCAN ROUTE'S OWN TARGET, AND ONLY THERE.** A
judged-nothing REPORT — presented to `gate --report`, or chained as a dependency — is untouched: it stays
verdict-preserving, exit unchanged, the caveat travelling, exactly as ⟨0.24⟩ requires. The distinction is
**the walk versus the report**, and it is load-bearing rather than tidy: a produced `analyzed.count: 0`
report travels into the gate route, so a refusal keyed on it splits the verb (measured — an attempt keyed
that way answered `scan --policy` 2 against `gate --report` 0 on its first run). A refusal keyed on the
walk never reaches the gate route at all, because §3.1's byte-equality is quantified over *any report a
scan produced* and this refusal produces none.

Three boundaries, each of which a naive form gets wrong:

- **A project of this engine's kind that yields ZERO UNITS is an ANSWER**, exit 0 with `analyzed.count: 0`
  — the premise ⟨0.24⟩'s gate rule is derived from. The predicate is *zero readable files*, never *not a
  valid project*: a `package.json` tree holding only unread JavaScript must still refuse, and a facade
  package whose sources parse to nothing must still answer.
- **PER-INVOCATION, never per-member.** The cause fires only when the walk admitted nothing anywhere under
  the target. A workspace with one live member and one scaffolded one stays green, and the empty member
  still publishes its ⟨0.24⟩ count-0 report. Per-member would redden benign layouts the languages
  themselves define — swift `binary`/`system` targets carry zero sources by design, a maven aggregator has
  no classes, a solution-style TypeScript root unions its members.
- **The ⟨0.30⟩ peek runs FIRST.** If the excluded files hold an effect the policy denies, that finding is
  the answer: it is reported, with `outOfScope` in a report, and the exit is 2 through the scope cause.
  The refusal is the last resort, not a short-circuit — otherwise the rung that exists to name the effect
  in the unread file is silenced by the target being unreadable, which is precisely when it matters most.

The refusal MUST carry a remedy naming what a target of this engine's kind looks like: a red gate that
tells the operator to run `mvn -q compile` is actionable, and one that only says no is the kind that gets
switched off.

**Fully offline.** candor runs fully offline: an engine MUST NOT phone home — no telemetry, no update
checks, no network traffic of its own, under any flag or mode. The §7 item 12 self-gate is the
machine-checked form of this promise (the engines' own declared boundary is Fs/Env only).

The short aliases `-V` and `-h` are REQUIRED; every other flag uses its long `--name` form. An engine
MAY expose `--out <prefix>` for file output plus any engine-specific flags. Flag names and help wording
are kept consistent across engines (the same `--policy`/`--json`/`--version`/`--help`/`--agents` mean the
same thing everywhere — the CLI counterpart of the item-10 cross-language query consistency).

A read-only **query** surface (§3.1) — whether shipped as a separate binary (e.g. `candor-query`) or as
subcommands of the scanner — MUST expose the same `--version`/`-V` and `--help`/`-h` conventions, with
its `--help` listing the available queries. The query *names and JSON shapes* are already pinned
cross-engine by item 10; this fixes the surrounding CLI so the tool is driven identically too.

#### 3.3.1 The query command-line grammar (REQUIRED for any exposed query verb) ⟨0.10⟩

§3.1 pins the query **names and JSON shapes**; this pins the **invocation** around them, so a query is
driven identically in every language — `candor where Net` is one command, not four. For each §3.1 verb an
engine exposes, it MUST accept:

```text
<cmd> <verb> <verb-args…> [--report <locator>] [--policy <file>] [--json] [--strict] [--include-unknown]
```

- **Report resolution.** With no `--report`, the engine discovers the report by walking UP from the CWD
  for a `.candor/` directory and using its `report` prefix (the §3.4 discovery mechanism; a `CANDOR_REPORT`
  env var overrides). `--report <locator>` overrides discovery. A `<locator>` — whether from `--report` or
  `CANDOR_REPORT`, resolved **identically** — is one rule: a **directory** → `<dir>/.candor/report`; a path
  ending `.json` → that **single report file loaded directly** (any `.json` file, whatever its internal
  dot-segments, so one engine can query another's report by path); otherwise a **prefix**
  (`<prefix>.<crate>.<backend>.json`). The comparative verbs `diff` and `gains` instead take two positional
  locators, `<current> <baseline>`, in that order (§3.1) — they compare two explicit reports, so discovery
  does not apply.
- **No report is a loud failure.** If the report cannot be resolved to an existing file — discovery finds no
  `.candor/`, or a `--report`/`CANDOR_REPORT` locator names nothing — the engine MUST print a clear error
  identifying what it looked for and **exit 2**. It MUST NOT emit an empty or degenerate answer at exit 0: a
  query that cannot find its report must never read as a clean "nothing here" (the §4 cardinal sin). A
  `--report` given with no value is likewise an exit-2 error, never a silent fall-back to discovery.

  ⟨0.28⟩ **AND "GIVEN NO VALUE" MEANS THE NEXT TOKEN IS FLAG-SHAPED — otherwise the clause cannot be
  implemented at all.** A value-taking flag whose following token begins with `--` has NOT been given a
  value; the operator has made a typing mistake. An engine that consumes the token as a filename cannot
  ever recognise the "no value" cause this document requires it to report, because there is no argv that
  produces it: `--policy --gate-json -` becomes *policy = the file named `--gate-json`*, an unreadable
  path, and the verdict sink the operator named is silently not a sink. Measured after the ⟨0.28⟩
  pre-pass alignment: candor-scan and candor-java exited 2 with **nothing on the stream**, where the
  `--gate-json -` refusal document belongs.

  This is the §6.2 unknown-flag rule one position over. That clause refuses to read `--poilcy` as a
  positional path because *silent reinterpretation is the one thing a security gate must not do*; reading
  `--gate-json` as a policy FILENAME is the same reinterpretation, and it additionally swallows a sink.
  So: a value-taking flag followed by a `--`-prefixed token is a usage error at exit 2, and the sinks
  named elsewhere in that argv are still sinks — the run has a broken command line, not a redefined one.

  A bare `-` stays a legitimate VALUE (`--gate-json -` is the stream form), and an operator who genuinely
  has a file whose name begins with `--` can spell it `./--weird`. Both are cheaper than the class of
  mistake this closes.

  *Recorded because the four engines were split by a FIX: aligning the arming pre-pass to the parse loop
  (⟨0.28⟩, so nothing arms a sink the loop never accepted) exposed that on two engines the loop itself was
  fail-open. candor-ts and candor-swift kept registering the sink and still pass; candor-scan and
  candor-java aligned onto the permissive reading and lost the refusal document. The row that caught it —
  §3.1 (b13) — had been passing on the DISAGREEMENT between pre-pass and loop, which is why neither half
  looked wrong on its own.*
- **Verb args** are positional, in the §3.1 order: `where <Effect>`; `show`/`callers`/`impact` `<fn>`;
  `path`/`whatif`/`fix` `<fn> <Effect>`; `map`/`reachable`/`blindspots`/`fix-gate`/`unverified` none;
  `containment [<baseline>]`. The report is a **flag**, never a leading positional, so the first token after
  the verb is the verb's own argument. In particular a **single** bare positional to `containment` is the
  **baseline** (the gating ratchet), report discovered — never re-read as the report (which would silently
  drop to non-gating report mode); the bare report-only form migrates to `--report`.
- **Deprecated positional forms are arity-gated.** An engine that still accepts the pre-0.10 positional forms
  MUST only treat a leading positional as the deprecated report, or strip a trailing `0|1` sentinel, or claim
  a trailing positional as the deprecated policy, when the positional count **exceeds** the verb's canonical
  arity (there is a surplus). It MUST NOT consume, probe, or reinterpret a positional that the canonical form
  needs — so `where Net` is always the effect `Net`, never a report lookup, and `show 1` keeps `1` as the
  query. Ambiguity here resolves toward the canonical (discovering) reading, never toward a silent gate-off.
- **`--json`** selects JSON (stdout MUST then be pure JSON, per §3.3). **`--policy <file>`** supplies a
  policy, honouring `CANDOR_POLICY` then `.candor/config` when the flag is absent (§3.3/§3.4) — never a
  positional. **`--include-unknown`** (on `callers`) keeps its §3.1 meaning.
- **`--strict` — the advisory-verb CI gate** ⟨0.18⟩. `unverified`, `fix-gate`, and `gains` are ADVISORY: they
  disclose (an unverified-purity hole, a boundary crossing, a supply-chain gain) and exit **0** by default, so
  an agent edit-loop reads the finding and acts without the run reading as failed. `--strict` turns each into
  a CI gate — **exit 1 while a finding remains** (`unverified`: an Unknown hole; `fix-gate`: an outstanding
  crossing; `gains`: ANY gained effect), unchanged otherwise. An engine exposing any of these three verbs MUST
  honour `--strict` this way; a typo'd or a not-applicable flag stays an exit-2 error (§3.3.1), never a silent
  swallow. In particular `gains` has **no `--policy`** — the effect-specific supply-chain gate is a `deny <E>
  gained` policy at scan time (`AS-EFF-005`, §6) — so a `--policy` passed to `gains` is an exit-2 error naming
  that gate, never a silently-dropped flag that lets the run exit 0.

The grammar is **conditional on exposure**: §3.1 queries are SHOULD, so an engine need not expose every verb
(candor-swift exposes a subset — e.g. `fix`/`fix-gate`/`unverified`/`tour`/`gains` — not the full read-only
set), but every verb it *does* expose MUST accept this grammar. An engine MAY continue to accept prior positional forms — a leading report, a `0|1` JSON sentinel,
a positional policy — as **deprecated** aliases that emit a stderr deprecation note; they are removed no
earlier than the next breaking bump, so this rung stays byte-compatible with 0.9. Each engine exposes its
query surface under its own **qualified** name (`candor-query`, `candor-ts-query`, `candor-java`,
`candor-swift`). Because the grammar is uniform, the bare **`candor`** name SHOULD be owned by a single
language-aware **dispatcher** that routes a query by the discovered report's backend and a scan by the
project manifest to the matching engine — not shipped four times by four engines, which would collide on
`PATH`. The dispatcher MUST route unambiguously or fail loudly (a polyglot report/project or a missing engine
is an error, never a silent wrong-engine run).

**The gate verdict** ⟨0.8⟩ (`--gate-json`). The shape:

```text
gate  { "spec": "<version>", "ok": bool, "violations": [ { "rule", "fn", "effects":[Effect…], "detail"? } ] }
```

`ok` is the CI verdict (true ⇔ the run gate-passes; advisory-only findings such as `AS-EFF-007` MAY appear
in `violations` but MUST NOT set `ok` false). Each entry names the `rule` (an `AS-EFF-00x` code, §6), the
`fn` it fired on, and `effects`, the specific effect set the violation concerns **per the rule's
semantics**: the denied intersection for `AS-EFF-006` (a fn performing `{Clock, Fs}` under `deny Fs`
reports `["Fs"]`, never its full set); the allow rule's effect for `AS-EFF-008`; the gained set (005); the
ambient set (004); the undeclared set (001); the unused **declared** set for 002 (capabilities held but
never used: the one code whose `effects` are declared, not performed); the taint-reached set (007); and
`[]` where no effect set applies (`AS-EFF-009` layer-flow, `AS-EFF-003` unresolved). `detail` is an OPTIONAL human message.
**Conformance pins `ok` and the `{rule, fn, effects}` set** (the same policy + code yields the same verdict
in every engine); `detail` is engine-natural prose (like the function-name *value* elsewhere, §3.1) and is
NOT pinned. The verdict is a re-emission of the gate the engine already ran, so it MUST agree with the process
exit code (a non-empty gate-failing `violations` ⟺ exit 1), so a consumer can never see a verdict that
disagrees with the gate. Source locations are not duplicated: a consumer joins each `fn` to its `loc` from
the §2 report (this is what the PR-native SARIF reporter does; `effects` gives it the precise effect to trace
a codeFlow for, which the report's per-fn `direct` set, a superset, cannot). An engine MAY also expose the
verdict some other idiomatic way, but `--gate-json` is the pinned form.

Two further MUSTs guard the verdict's integrity:

- **On exit 2 (could-not-evaluate) no *ok:true/false GUESS* is written** — refined ⟨0.21⟩. There are four
  exit-2 causes ⟨0.31⟩ and they differ: **(a) a broken gate CONFIG** (an unreadable policy, an invalid baseline, an
  unknown flag) — the gate could not be evaluated at all. ⟨0.24⟩ **SUPERSEDED: this said NO verdict is
  written, and §3.1's refusal-document clause (`107755b`, generalised by `1503368`) now requires one on
  EVERY exit-2 cause including this one.** All four engines follow the newer rule; this sentence is stale
  prose that would lead an implementer to reintroduce the hazard it was written before — a refusal that
  writes nothing leaves the PREVIOUS run's green document on disk, and a CI wrapper reading that path
  unconditionally reads it as current. The document written here carries `ok: false` + `refused: true` and
  **no `violations` key**, so it is fail-closed to a naive reader without asserting a finding. *A corrected
  assertion outliving its correction in a second location is a defect class this document has now produced
  three times; the release review that caught this one was reading for exactly that.* **(b) an INCOMPLETE analysis** (a source file failed to read/parse — the target's own code was
  not fully seen) — here the engine SHOULD write a machine-legible **incomplete verdict**
  `{ spec, ok: false, incomplete: true, unanalyzed: [ { path, reason } ], analyzed: { count } }` and exit 2.
  This is not a fabrication: `ok: false` is honest (the gate did not certify) and `incomplete: true` +
  `unanalyzed` say *why*, so a CI/agent reading the JSON learns the gate couldn't certify over unseen code
  rather than having to scrape stderr — closing the machine-consumer false-all-clear the manifest fixes (a
  green report over unanalyzed source). A configured gate over incompletely-analyzed code MUST fail closed
  (exit ≠ 0); a real violation (exit 1) still dominates. A bare scan with no gate does not exit 2 — it
  discloses `unanalyzed` in the report (exit 0). The `analyzed: { count }` count rides EVERY verdict (Gap 1).
  ⟨0.30⟩ **(c) AN INCOMPLETE SCOPE** — the peek found a function performing an effect the policy DENIES in
  a file the scan deliberately did NOT open (§2's `outOfScope`). This is neither (a) nor (b): the policy
  loaded and the files READ cleanly; what is missing is not readable bytes but the DECISION to open them.
  The verdict is the same shape as (b) — `{ spec, ok: false, incomplete: true, outOfScope: [ … ],
  analyzed: { count } }`, exit 2 — and for the same reason: the gate could not see enough of the tree to
  certify it. The findings are NEVER `violations` (the gate did not judge those units) and the document
  MUST carry `outOfScope`, because exit 2 with a silent document is the stderr-only disclosure ⟨0.21⟩
  exists to close. It carries **no `violations` entry for these functions** — the same explicit statement
  (a) makes about its own shape — and a run that ALSO holds a real violation exits 1 carrying both keys. A real violation (exit 1) still dominates, as in (b).

  *Recorded because a reader relied on the count: this list read "there are two exit-2 causes and they
  differ" for four rungs, and §3.1 leans on that enumeration when it rules that an engine refusing
  elsewhere "has minted a third cause and split the verb". ⟨0.30⟩ mints one deliberately, and a superlative
  left standing next to its own exception is how the last one of these was found.* ⟨0.31⟩ *mints the
  fourth — (d) an UNEVALUABLE TARGET — and this note is the reason the count in the sentence above was
  moved with it rather than left to be discovered. A stale count here has been shipped three times.*
- **A multi-package scan MUST accumulate violations across members into ONE final verdict.** A
  per-member write lets a clean last member overwrite an earlier violator's verdict — shipped as
  exactly that bug in candor-scan 0.8.1, where a workspace's `gate.json` said `ok: true` while the
  process exited 1. A consumer of the file and a consumer of the exit code must never disagree.

### 3.4 The configuration file — `.candor/config` (SHOULD)

A single checked-in file replaces the `CANDOR_*` environment wiring, so CI becomes "point at the repo"
and the configuration travels with the code. One `key value…` per line; `#` begins a comment (inline
too); blank lines are ignored — the §6.2 lexical rules. The **key vocabulary** is shared across engines:

| key | env var | value |
|---|---|---|
| `policy` | `CANDOR_POLICY` | path to a §6.2 policy file |
| `baseline` | `CANDOR_BASELINE` | path to a baseline report (the AS-EFF-005 ratchet) |
| `strict` | `CANDOR_STRICT` | a scope (conformance, AS-EFF-001–003) |
| `no-ambient` | `CANDOR_NO_AMBIENT` | a scope (AS-EFF-004) |
| `closed-world` | `CANDOR_CLOSED_WORLD` | boolean (`true`/`1`/`yes`, or a bare key) |
| `taint` | `CANDOR_TAINT` | boolean — enables the §3 **risk** mode (AS-EFF-007; two names, one mode) |
| `deps` | `CANDOR_DEPS` | whitespace-separated report paths (§2 chaining) |
| `unknown-ratchet` | `CANDOR_UNKNOWN_RATCHET` | boolean — with a `baseline`, a **newly-introduced** `Unknown` fails AS-EFF-005 (default: Unknown-only gains are advisory) |
| `engine` | — | ⟨0.27⟩ `[<impl>] <version>` — the engine build this repo's committed artifacts were produced with; a different build FAILS (exit 2). No env var: a pin an environment can override is not a pin |

⟨0.27⟩ **`engine [<impl>] <version>` — the engine↔baseline coupling, enforced rather than
hoped for.** The committed `baseline` is a snapshot of what one engine build reported, and an engine
swap is baseline-invalidating. Engines already refuse a baseline whose §2.1 provenance **build id**
differs from the running one — but that id is a build hash, which a consumer cannot *declare*: the
version lived in CI configuration, decoupled from the baseline it is married to, and a mismatch was
discovered only after running the wrong engine. A pin is declarative, so it also tells tooling which
engine to FETCH, and it applies to runs with **no baseline configured at all**, where the existing
refusal — which lives inside the baseline comparison — cannot reach.

**Scope.** This applies where a producer analyses code and emits a report or a verdict from that
analysis. It does NOT apply to a verb that only reads an EXISTING report (`gate --report`, the §3.1
queries): there the running engine is an evaluator, not the producer, and its version says nothing
about the artifact being read. The comparison that matters there is between the artifacts' own
recorded provenance, which §2.1 already governs.

A producer implementing this MUST compare the pin against its own release version and, on a difference,
FAIL with **exit 2** — the run is *unevaluable*, not violating, and a machine consumer must not read
"I could not trust this result" as "your code broke a rule". **Two of the five answers MUST NOT change
the exit code**, and they are the load-bearing part:

- **No pin, or a pin naming another implementation** — unchanged behaviour. The key is opt-in by
  construction: a config with no `engine` line behaves exactly as it did before.
- **The pin is well-formed and the producer cannot determine its OWN version** (a source build rather
  than a published artifact). The condition is UNANSWERABLE, and §3.1's rule applies unchanged: an
  unanswerable condition MUST be disclosed, never scored — *including* as satisfied. Failing here would
  break every developer on a source build; passing silently would delete the pin exactly where nobody is
  watching for it. So the producer says so, once, and leaves the verdict alone.

A pin that is present but **unreadable** (`engine latest`, a bare `engine`, anything that is not a
version) MUST fail with exit 2 rather than being skipped as a malformed line. This is the one place the
§6.2 warn-and-skip posture inverts: skipping a key that ADDS something costs that key's contribution,
while skipping a PIN hands the operator a guard they believe is on.

**The qualified form exists because the family versions as a LADDER, not in lockstep** (§2 versioning
policy): one engine may lead a rung, so a bare version in a polyglot repo would fail whichever engine had
not yet caught up. `engine java v0.27.0` pins one implementation; an unqualified `engine v0.27.0` applies
to whichever engine reads it; a qualified pin takes precedence over an unqualified one. An implementation
MUST ignore a pin qualified for a different implementation — one config serves the whole family.
**That skip is WHOLE-LINE and takes precedence over the unreadable-pin rule above.** The two clauses
collide on a line like `engine swift 0.99.0 junk`, and a cross-engine differential found the family split
three ways on it: one engine ignored it, three refused their OWN run over a line naming an engine they are
not, and the engine it actually names refused (correctly). A malformed line qualified for another
implementation is THAT implementation's problem, and it will refuse on it; killing every other engine's
run as well turns one typo into a family-wide outage. So read the qualifier FIRST: if it names a known
implementation that is not yours, the line is not yours, whatever follows it. A line that is unqualified,
qualified for YOU, or whose qualifier is not a known implementation at all (`engine kotlin v1`) is yours
to read, and MUST be MALFORMED if it is unreadable.

**A version token carries AT MOST ONE leading `v`.** `vv0.27.0` is not a version; two engines accepted it
as one by stripping every leading `v`, so the same bytes were a valid pin to two implementations and
MALFORMED to three. Config parsing MUST also tolerate CRLF: a trailing `\r` is whitespace, not part of
the version — one engine refused a MATCHING pin on a repository checked out on Windows.

There is deliberately **no `CANDOR_ENGINE` environment variable**, breaking the 1:1 key↔env mapping the
rest of this table keeps. Every other key configures what the run *does*; this one asserts what the run
*is*, and an assertion an ambient environment can silently switch off is not one. For the same reason
there is no `--ignore-engine-pin` escape: the deliberate act is editing the pin, in the same change that
regenerates the baseline, which is exactly the discipline being enforced.

**Status: implemented and enforced identically by candor-java, candor-rust, candor-ts, candor-swift and
candor-agents**, pinned by conformance **PART 33** (a holding pin is silent and changes no exit code; a
mismatched or unreadable pin is exit 2; a pin qualified for another implementation is ignored) and by
**PART 13b**, which pins that the key is recognized rather than reported unknown.

**`unknown-ratchet`** (opt-in, default off) makes `deny E Unknown` adoptable on legacy DI/reflection-heavy
code. Ordinarily an `Unknown`-only gain vs the `baseline` is *advisory* (resolution noise dominates on version
bumps). With the ratchet on, the **current** `Unknown` surface is grandfathered — a function already `Unknown`
in the baseline shows no gain, so it never fails — and only a **new** `Unknown` (a blind spot the baseline did
not have) raises AS-EFF-005. A team freezes today's report as the baseline and the strict gate ratchets the
`Unknown` surface *down* rather than failing everywhere on day one; a new `Unknown` is grandfathered by
regenerating the baseline. Shipped four-way (java/rust/ts/swift); the flag is additive and, when unset, leaves
the AS-EFF-005 contract byte-identical, so — like the other opt-in flags (`closed-world`, `taint`) — it is
per-engine tested rather than conformance-differential-pinned.

An engine reads the keys whose modes it implements; a known-but-unimplemented key is **inert for
enforcement, but SHOULD be disclosed**: one stderr line naming the keys this engine recognizes and
does not implement. Inertness is by design (a repo scanned by several engines carries one config;
`strict` drives the JVM engine and gates nothing elsewhere), but a key that names a **gate**
(`policy`, `baseline`, `strict`, `no-ambient`, `taint`) must never read as silently active: a team
that checks in `baseline .candor/baseline` believing the guard is on deserves the one-line correction.
A key **outside** the vocabulary is **ignored with a warning** (the §6.2 malformed-line posture: a
misspelt `policy` must never silently drop a gate). A **bare** value key (a lone `strict` line) means
"enabled with the empty value", exactly the set-but-empty env var (whole-unit scope for a scope key;
a bare `policy` fails loud on the empty path), never a silent drop.

**Discovery is anchored to the scan target, not the CWD**: the file is found by walking UP from the
target (`target/classes` → the repo root's `.candor/config`), so the config that travels with the
scanned code is the one that applies regardless of where the process was launched; a `CANDOR_CONFIG`
environment variable overrides discovery entirely. **Precedence, highest first: a CLI flag → the
matching `CANDOR_*` env var (the one-off override) → this file → the built-in default.** For the same
reason, a **relative path value** (`policy`, `baseline`, `deps` entries) resolves against the
**config's home directory**, never the process CWD: the directory containing the `.candor/` directory
(the repo root the config travels with; for an out-of-tree `CANDOR_CONFIG` override file, simply the
file's own directory). A checked-in `policy .candor/gate.pol` in `<root>/.candor/config`
therefore names `<root>/.candor/gate.pol` from any launch directory. (A relative path supplied via a
CLI flag or `CANDOR_*` env var stays CWD-relative as usual: the one-off override is launch-context
local; only the checked-in file's values travel with the code.)

**Fail-closed:** a config that is configured but unusable never silently degrades to "no config". A
set `CANDOR_CONFIG` naming a missing/unreadable path, or a discovered file that exists but cannot be
read, FAILS the run (exit 2, the §6.2 unreadable-policy posture; the file may carry the policy, so a
silently-dropped config is a silently-dropped gate). Only genuine absence is an empty config.

`CANDOR_CONFIG` is **reserved** for this override path; an engine must not overload the name for any
other input (the Rust lint's classifier-extension rules file, which historically used it, is now
`CANDOR_RULES`): one env var carrying two file grammars would make the fail-closed posture ambiguous.

This is configuration, not the report/effect wire contract (no field an interoperating consumer reads
changes), so it advances no version (an additive amendment within 0.8; all four engines implement it and
the conformance config differential pins discovery, precedence and the fail-closed posture).

## 4. The trust contract — the core of candor

The defining rule: **an implementation must never report a function as effect-free when it could not
actually determine that.** A call it cannot resolve to a concrete target — dynamic dispatch over an
unknown type, a function value / callback, reflection — MUST contribute `Unknown` to that function's
effect set and set `unresolved: true`. It must not be silently assumed pure.

Its companion — **under-report, don't fabricate** — is stated once here; every other section points at
it. When the choice is between asserting something the engine did not read from the code (a guessed
chain join, a minted literal, an argument classified as a subprocess head) and asserting less, it
asserts less: a gap is *disclosed* (`Unknown`, an omitted optional field), while a fabricated positive
is silently trusted downstream — the unrecoverable direction. §2's chain joins, literal surfaces and
SQL `tables` extraction, and this section's Exec-head refinement are all applications of this rule.

**The limit, stated plainly.** Whether a function performs an effect is undecidable in general (Rice's
theorem), so this rule is a *best-effort discipline, not a completeness guarantee*: a conforming
implementation is one that disclosed `Unknown` everywhere it could not resolve a target — never one
that has provably found every effect. New ways for an effect to hide behind a construct an engine does
not yet model are found and closed over time; the residual is tracked openly (the code engines
maintain a soundness register and adversarial gates) rather than asserted away. So the contract a
consumer can rely on is **disclosure** (what the engine couldn't see is marked, not silently dropped),
not omniscience. A clean report means *the implementation found no effect and disclosed every gap it
hit* — read it as "more thorough than review, and honest about its blind spots," not as a proof of
purity.

### 4.0 The disclosure model, formally — a signature is a pair `(S, D)`

The prose above has a precise carrier. A function's signature is a **pair `(S, D)`**:

- `S ⊆ E` — the **determined** effects: those the engine positively classified (the report's `direct`/
  `inferred`, minus the `Unknown` marker).
- `D` — a set of **disclosure reasons**: the reason-tagged sources of `Unknown` (the `unknownWhy` classes,
  §4's reason vocabulary). `D = ∅` ⇔ **sound-complete** (no blind spot); `D ≠ ∅` ⇔ `Unknown` present, and
  `Unknown ∈ inferred` is exactly the serialized marker that `D ≠ ∅`.

Order the pairs **componentwise**: `(S₁, D₁) ⊑ (S₂, D₂)  iff  S₁ ⊆ S₂ ∧ D₁ ⊆ D₂`. This is a genuine product
lattice (join = componentwise `∪`), so `⊑` is a real **partial order** — in particular antisymmetric. The
naïve "one flat set with `Unknown` in it, ordered by `⊆`-or-`Unknown∈T`" is only a *preorder* (it cannot tell
`{Net, Unknown}` from `{Unknown}`, which reason-scoping relies on); the pair carrier fixes this. Two
consequences the model must get right:

- `(E, ∅)` ("performs every effect, fully determined") and `(∅, {r})` ("determined-pure so far, but with an
  undischarged blind spot `r`") are **incomparable** — so `{Unknown}` is **not** `⊤`. Top is `(E, AllReasons)`;
  the undetermined signature `(∅, D)` sits off to the side, not above the concrete ones.
- The transitive effect set (§2.2) is the **least fixpoint** of the monotone componentwise join over this
  finite lattice (Knaster–Tarski) — a callee's `(S, D)` joins into its caller's, so both `S` and the reason
  set `D` propagate along the call graph (which is why a reason class travels transitively, §6.2 ⟨0.19⟩).

The policy verbs (§6.2) are **monotone predicates** over `(S, D)`:

| verb | fires iff |
|---|---|
| `pure <scope>` | `S = ∅ ∧ D = ∅` is required; violated when `S ≠ ∅` (an effect) — `D ≠ ∅` alone is AS-EFF-003 disclosure, not AS-EFF-006 |
| `deny e` | `e ∈ S` |
| `deny e Unknown` | `e ∈ S ∨ D ≠ ∅` |
| `deny e Unknown[c…]` | `e ∈ S ∨ (D ∩ {c…}) ≠ ∅` — the reason-scoped gate reads the `D` component directly |

So **reason-scoped `Unknown` (⟨0.19⟩) is the `D` component made policy-addressable**, and the completeness
manifest's `analyzed`/`unanalyzed` (§2) is what lets a consumer tell `(∅, ∅)` (provably pure) from a function
never placed in the lattice at all (dropped — outside `analyzed`). This subsection formalizes the operational
rules that follow; it adds no new obligation.

**Dispatch over a local abstraction — the bounded-CHA discipline** (all four code engines): a
call dispatched through a locally-declared abstraction (a Rust `dyn`/`impl`/generic-bound trait, a
TS interface, a JVM interface/supertype, a Swift protocol/class) SHOULD resolve to the **visible local implementors'**
methods when the dispatch is *narrow* (at most **12** implementors, the shared bound, so the
verdicts agree across engines), and MUST otherwise read `Unknown`: a local abstraction with no
visible implementor, too many, or an ambiguous name is disclosed indeterminacy, never silent purity.
Resolving to local implementors is an over-approximation in the CHA sense (any of them *could* be
the target) and an under-approximation across the open world (a downstream implementor is
invisible); both are the accepted trade everywhere else in this contract. Dispatch through an
EXTERNAL abstraction an engine does not model (a stdlib iterator protocol, a serialization trait)
MAY remain unflagged, but then MUST be documented as a named miss (item 7, §7).

**Refining the subprocess boundary** ⟨0.5⟩. `Exec` marks that a subprocess was spawned; what the
child does is beyond the caller's static scope (the *capability cliff*, the subprocess analog of an
unresolved dispatch). An engine MAY refine it when the sub-command's **head is a literal,
statically-known** value (the `cmds` literal surface, §2): it MAY classify that head and attribute
the head's effects to the caller: a spawned `curl` contributes `Net`, a spawned `psql` contributes
`Db`, and a spawned **candor engine** contributes `Fs`/`Env`, which §7 item 12 *guarantees* (the
analyzer self-boundary), making this one case spec-supplied rather than curated. The same disclosure
posture as bounded-CHA governs: refinement only **adds** resolved effects or **bounds** the cliff's
reach. It MUST NOT drop the `Exec` itself (a subprocess was still spawned), and MUST NOT narrow a
**dynamically-constructed or unrecognised head to pure** (that head keeps the unrefined cliff). The
**head** is the program-naming position (argv[0], the command actually executed), *not* merely any
literal among the call's arguments: when the program itself is runtime-computed, a literal appearing
only as a later **argument** (a flag, a path, an env value) is data, NOT the head, and MUST NOT
refine: `spawn(tool, "curl")` with a dynamic `tool` keeps the bare cliff, because `curl` is an
argument here, not the program. Classifying an argument as the head would **fabricate** that
argument's effect onto a program that may never perform it — the under-report-don't-fabricate rule
(above) forbids it. A
head resolved to a known non-project tool also bounds *transitive* attribution: a caller that only
ever spawns such tools does not thereby reach the effects of the project's own binaries. For example, a
step that runs candor *over* the code performs `Fs` (candor reads the source), not the analysed
code's `Net`/`Db`. The head table is curated engine data under the same under-report-don't-fabricate
rule, never normative; only this posture is.

For a consumer, this means:

- `inferred` is **authoritative** for what the implementation resolved.
- When `unresolved` is true (or `Unknown` is present), the set **may be incomplete** — read the
  source for that function before relying on its effects.

An implementation MAY treat dispatch over a curated set of conventionally-pure standard-library
traits/interfaces (formatting, equality, hashing, cloning) as resolved-pure, to avoid flooding
reports with false `Unknown`s; but it MUST document which, and MUST NOT extend the set to anything where an
effect could plausibly hide (iterators, callbacks, I/O traits, finalizers).

A method *inherited* by a type (a trait default/provided method, or a concrete method on a base
class the type does not override) is a **resolved** call, not an `Unknown`: it lands on that inherited
body, whose effects MUST be attributed. Reporting it `Unknown` is unsound in the noisy direction (it
masks the inherited body's real effects, since an unresolved dispatch also stops propagation). An
`Unknown` from dispatch is justified only when the target is *genuinely* indeterminate: a value
implementing a trait/interface the implementation declares but whose concrete implementor it cannot
see (a DI-wired strategy, a `dyn`/virtual call with no visible impl). The `unknownWhy` field
records this distinction per function so a consumer (and the implementer) can tell irreducible opacity
(`reflect:`, `native:`) from the improvable kind (`dispatch:`/`callback:`, often resolved by widening
the analysed inputs to include the missing implementor or the higher-order call's target). ⟨0.6⟩ It is
**REQUIRED on a unit that introduces `Unknown` DIRECTLY** (a *source*: its own body has the
unresolvable call), and absent on a unit whose `Unknown` is purely inherited from a callee. That source
vs. inherited split is what makes the `blindspots` query (§3.1) name the handful of real root causes
behind a widely-propagated `Unknown`; a 0.5 consumer that ignores the field is unaffected.

⟨0.7⟩ **Canonical `unknownWhy` vocabulary.** Each entry is `kind:detail`, where `kind` is exactly one of
**five** ⟨0.24⟩, chosen to be language-neutral over *why a call's body could not be resolved*:

| `kind` | meaning | `detail` |
|---|---|---|
| `reflect:` | invocation chosen at runtime by name/metadata — reflection, `Method.invoke`, `eval`, dynamic property install/accessor | best-effort |
| `native:` | a boundary to code the engine cannot analyse — native methods, FFI/`extern`, intrinsics | best-effort |
| `dispatch:` | an unresolved **virtual / interface / protocol** dispatch with a **resolvable owner type + member** — static target known, concrete body not (no impl, bounded-CHA over many impls, dynamic receiver of known type) | **`<owner-type>.<member>`** (dotted) — NORMATIVE |
| `callback:` | an unresolved **higher-order / owner-less** invocation — a function/closure *value* (param, field, bound, computed, opaque-iterable) whose target and owner type are not both known | best-effort |
| `ambiguous:` ⟨0.24⟩ | the analyser's own **name resolution** was ambiguous — two same-named local definitions, so no owner could be formed at all. Not a `dispatch:` with a missing body and not a `callback:` (no function value); a vocabulary without it forces an engine to lie or fall silent | best-effort |

⟨0.24⟩ **The dotted detail is normative WHEN an owner was formed; a DOT-FREE detail is the reserved form
for "no owner could be formed at all".** It is free text naming the cause (`untyped cross-package receiver`)
and is NOT conformance-compared — but it remains a `dispatch:`, and consumers MUST handle it (§3.1). The
alternative rulings were both measured and rejected. Reclassifying to `callback:` is what §4's own dividing
line reads like — no resolvable owner — but it is false (no function value is involved) and it moves the
reason's §6.2 class from `dispatch` to `indirect`, silently **narrowing** every `deny E Unknown[dispatch]`
gate in the field. Refusing to emit anything is the cardinal sin outright. The kind is the part gates read,
so the kind is the part that must stay true; the detail is where the engine says how much it knows, and
"nothing" is a thing it must be able to say.

The dividing line between `dispatch:` and `callback:` is whether a **resolvable owner type** exists:
`dispatch:` is reserved for unresolved member dispatch where the engine knows the owner type and member
(so a consumer can resolve overrides — this is what the `callers --include-unknown` frontier keys off);
every other unresolved invocation (an opaque function value, an untyped receiver, opaque iteration) is
`callback:`. Only the `dispatch:` detail is conformance-compared (as `owner.member`); the other three
kinds' details are best-effort prose. An engine emits whichever kinds its language model produces — a
language whose model genuinely produces no virtual/interface dispatch emits no `dispatch:`, and its frontier
is correspondingly empty. ⟨0.24⟩ *This sentence named the Rust scanner as such a language. It is not one —
it emits `dispatch:` for **every** dispatch reason in a 1062-report census, and `ambiguous:` on 8710 of
19607 `Unknown`-bearing entries. The claim was a **description of a defect's symptom promoted to a language
property**, sitting in the section an auditor of the vocabulary would read to confirm it was not a defect.
It was corrected in §3.1 first, and this copy survived that correction — which is the transferable part: a
falsified assertion has as many homes as it has restatements, and fixing the one you found is not fixing
it.*

⟨0.7⟩ **What is conformance-binding, and what is per-language.** Precisely: the **`kind` SET**
(`reflect`/`native`/`dispatch`/`callback`/`ambiguous` ⟨0.24⟩) is the closed vocabulary every code engine's
reasons draw from,
and the **`dispatch:` detail** (`owner.member`) is the one normative detail. Everything else is
per-language and **OPTIONAL**: an engine emits `native:` / `reflect:` **only where its language model
actually produces that origin** — they are not universal. By design the engines diverge here, legitimately:
TypeScript folds a native boundary
into `reflect:` (`eval`/`defineProperty`/dynamic accessor) and emits no bare `native:`; Swift's syntactic
model produces neither `reflect:` nor `native:`. A consumer therefore MUST NOT assume all four kinds appear
in every report — only that any kind it *does* see is one of the **five** (and that a `dispatch:` which
formed an owner carries `owner.member`; see the dot-free reserved form above). Finally, an engine **MAY** emit an additional, off-vocabulary kind **during a migration**
(candor-java has historically emitted `task-handoff:` and `indy:`; reconciling them onto the four is a
tracked, byte-changing task — MODEL.md): such a kind round-trips and a consumer tolerates it under §2
forward-compatibility. ⟨0.24⟩ **AN ENGINE HOLDS THIS VOCABULARY TWICE, AND THE HALVES DRIFT.** Every implementation surveyed has
**two** representations of a `kind`: a **prefix/string classifier** feeding §6.2's class table, and a
**typed/structural** one (an enum, a union, a constructor set, a match). They are authored from different
places — the class table from a cross-engine audit of what engines actually emit, the typed vocabulary from
this section's list — so when this section goes stale, **the string half stays right and the typed half does
not.**

That asymmetry is not a curiosity, it is a *concealment mechanism*: the string half being correct is exactly
what stops anyone noticing. Measured on the reference JVM engine, whose string classifier had mapped
`ambiguous` → `dispatch` since a 2026-07-16 audit while its typed `Kind` enum did not contain the kind at
all — so the token parsed to a null kind and classified as `unresolved` on the typed path, `dispatch` on the
string path, in one engine, silently. Two code comments had recorded the divergence as intended behaviour
rather than fixing it.

An implementer amending this section MUST update both halves and **MUST** add a test that a **fabricated**
off-vocabulary kind (`banana:whatever`) still behaves as §2 forward-compatibility requires — round-tripped
verbatim, classified through the conservative catch-all. Without that control, "added a kind" and "stopped
checking the kind set" are the same diff.

**MUST, not SHOULD — because a mutation exists that ONLY that control catches.** Measured: an engine whose
prefix test is rewritten from *is the kind in the SET* to *does the token have the `kind:detail` SHAPE*
(`contains(":")`) passes **every** assertion about every real kind — they all have the shape — and is caught
solely by the fabricated one. Of four mutations run against one engine, the fabricated kind was load-bearing
in three, and the sole detector in that one. A control that is only exercised by inputs the implementation
already handles is not a control.

**A consumer may need a kind it never emits.** An engine that chains dependency reports relays their
`unknownWhy` tags into its own report keyed by the calling function, so a kind produced only by another
engine's language model can appear in this engine's output. The JVM engine emits no `ambiguous:` — a JVM
invoke carries owner, name and descriptor, so bytecode name resolution is never ambiguous — and must still
represent it.

**A dispatch FRONTIER must key off the kind, not the class.** §3.1's frontier resolves overrides against an
owner type. `ambiguous:` projects to class `dispatch` (§6.2) but has **no owner**, so an engine whose
frontier selects sources by *class* will admit entries there is nothing to resolve against, while one that
selects by *kind* excludes them for free.

⟨0.24⟩ **OPEN — two off-vocabulary kinds an engine emits today, and one of them answers a DIFFERENT
QUESTION from the five.** Recorded rather than reconciled, because reconciling either changes report bytes.
`dynamicMemberLookup:` is the mild case — off-vocabulary as a §4 *kind*, but §6.2's projection table does
register it, which is the same producer/consumer asymmetry `ambiguous:` sat in until this rung.
**`contentsOf:indeterminate-url-scheme` is the sharp one: registered NOWHERE** — not among the five, not in
§6.2's table, not as a migration kind. It reaches `unresolved` through the conservative catch-all, which is
defensible, but its meaning is *"the call resolved; its effect CATEGORY is unprovable"* — which is not what
any of the five say. All five answer *"the body could not be resolved."* A vocabulary whose members answer
one question should not silently acquire a member answering another; either it earns a kind with its own
projection, or its meaning belongs in a different field.

⟨0.24⟩ **`dep:<hash>` and `dep-stale:<pkg>` are REGISTERED, not migration kinds** —
§6.2 holds them up as the correct shape (a reason attached where the `Unknown` is created, per dependency
ENTRY), so they must not sit in a clause about kinds being reconciled away. They project to `unresolved`.
The conformance check pins the canonical kinds and the `dispatch:` shape, and
**tolerates a known migration kind as a warning rather than a hard divergence**, so a not-yet-reconciled
engine is visible without being falsely red.

⟨0.7⟩ **Domain engines.** The four kinds describe why a *code* call's body could not be resolved, and so
bind every engine that analyses source or bytecode. A **domain engine**, one whose units are not
functions and whose call graph is not code (e.g. the agent-fleet engine, where units are agents and edges
are delegation), has no virtual dispatch, reflection, or FFI in this sense; its `Unknown` sources are
domain-specific (an uncurated MCP server, an unknown tool, ambient tool authority, an unprovable agent
spawn). Such an engine MUST still attach an `unknownWhy` to every direct `Unknown` source (the disclosure
requirement of §4 is universal), drawn from its own documented origin vocabulary (e.g. `mcp-uncurated:`,
`tool-unknown:`, `ambient:`, `agent-spawn:`), and emits none of the four code kinds (so its frontier is
likewise empty). Disclosure is required of *every* conformant engine; the code vocabulary above is
required only of code engines.

## 5. Capabilities (conformance)

Conformance needs a way for a function to *declare* the effects it may perform. The canonical
mechanism is a **capability passed as a typed parameter**: holding a value of a capability type
declares the corresponding effect. Examples: candor-Rust's own `&Fs` token; a real
[cap-std](https://github.com/bytecodealliance/cap-std) `&Dir`; a dependency-injected collaborator in
Java/C#. An implementation maps capability types → declared effects.

This is deliberately aligned with capability-secure and dependency-injection styles — the goal is
that a function's *signature* tells you its effect surface.

### 5.1 The effect manifest — declared effects for an opaque dependency ⟨0.5⟩

A cap type lets a *function* declare its effects. The same trust tier extends to a whole **opaque
dependency** (a package whose source the engine does not analyse, an MCP server, a tool behind the
`Exec` boundary) via an **effect manifest**: a `candorEffects` declaration (an array of effect
names from §1) the dependency publishes, naming the surface it may perform. An engine MAY read it
and classify the dependency's calls accordingly, killing the `Unknown` it would otherwise carry.
The trust is **declared-not-verified**: the report is only as trustworthy as the declaration, exactly
like a cap type (and unlike the engine's own analysis, which is checked). An effect name outside §1
MUST void the declaration loudly (a typo must not silently *narrow* a surface), and a declaration
that under-claims is caught the moment the source *is* analysed; the coverage ledger (§7) names every
dependency still opaque, so a missing manifest is visible, never silent. The edge cases are fixed
normatively so the engines can't drift on them (a cross-engine manifest differential is tracked
conformance work; these MUSTs bind regardless): an **empty** array (`candorEffects: []`) is a positive
"declared pure", covered, NOT a blind spot (distinct from an *absent* manifest, which stays opaque, the same load-bearing
empty-vs-absent split as `deny`-with-no-effect vs `pure`); a present-but-**non-array** value is malformed
and MUST void loudly (the same class as an out-of-§1 name, never a silent narrowing); names are a **set**
(deduped); `Unknown` is not a §1 effect name, so `candorEffects:["Unknown"]` voids; and a manifest MUST
come from the **effect-owning package itself**, never a type-only stub (a `@types/<pkg>`-style sidecar a
third party can publish must not silence the real package's surface). This is one mechanism with
several existing shapes: a project-side declaration on an MCP server entry, a user-supplied
crate→effect rule, a chained sibling report. The spec names the convention so it is portable across
them; where to put the field (a package manifest, a registry's metadata) is the ecosystem's to
settle, and adoption is the path to shrinking `Unknown` across a whole dependency graph rather than
one curated table at a time.

The manifest pays off twice. First, **precision**: a declared dependency stops flooding consumers
with `Unknown`. Second, and higher-signal, **supply-chain review**: an effect surface is a
versioned fact, so a `diff`/`gains` (§3.1, §6 `AS-EFF-005`) between two *releases* of a dependency
surfaces a **gained capability**: "this update gained `Net`/`Exec`". A dependency that quietly
grows a network or subprocess reach between a patch release is exactly the supply-chain event nothing
else flags cheaply; candor flags it as a deterministic effect-set delta, declaration or analysis
alike. An engine SHOULD make the package-level gained set machine-readable so a gate can alarm on it;
the **`gains`** query (§3.1) is that shape.

## 6. Diagnostics (`AS-EFF-00x`)

Shared codes (the `AS-EFF` prefix is historical — "AgentScript effect", the project's origin):

| Code | Meaning | Mode |
|---|---|---|
| `AS-EFF-001` | performs an effect it does not declare | conformance |
| `AS-EFF-002` | declares a capability it never uses | conformance |
| `AS-EFF-003` | makes unresolved calls; effect set not provably complete — cannot be certified | conformance |
| `AS-EFF-004` | uses ambient authority directly | no-ambient |
| `AS-EFF-005` | gained an effect versus the baseline | baseline guard |
| `AS-EFF-006` | (transitively) performs an effect a declared policy forbids | policy |
| `AS-EFF-007` | performs an injection-class effect on caller-derived input (**heuristic, advisory**) | risk |
| `AS-EFF-008` | an allowlisted effect's literal surface (host / command / path / table) is visibly violating **or uncertifiable** — a value outside the allowlist, or a value the engine cannot see (fail-closed) | policy |
| `AS-EFF-009` | (transitively) calls into a layer a declared dependency rule forbids | policy |
| `AS-EFF-010` | a boundary effect leaked into a layer it was not in, versus a baseline (containment regression) | containment |
| ⟨0.29⟩ `AS-EFF-011` | reaches a scope an `only` PERMISSION rule does not list | policy |

The program entry point (e.g. `main`) is exempt from `AS-EFF-001` — it legitimately mints/holds the
whole capability bundle.

A **literal-allowlist** policy rule, `allow <Effect> [in <scope>] <value>...`, constrains *which* values a
scope's effect may reach (AS-EFF-008). Four effects carry a literal surface: `Net` hosts, `Exec`
commands, `Fs` paths, and `Db` tables, checked against the transitive `hosts`/`cmds`/`paths`/`tables`
detail, so it catches a value that lives in a deep or cross-crate callee, matched per-effect (host by
name, command by basename, path by prefix, table by case-insensitive qualified name with `schema.*`
covering a schema; an allowed unqualified name does NOT cover a qualified one). The rule is a
**certification, and it fails closed** (see SEMANTICS §6): a function in scope passes only when every
value its effect reaches is *visible and allowed*. A value the engine cannot read (computed at
runtime, concatenated, derived from a parameter) leaves the surface **uncertifiable**, and that is an
AS-EFF-008 failure too, never a pass: a denied endpoint assembled at runtime slipping through an
allowlist that *saw nothing* is the masked-literal evasion, the cardinal gate-evasion the fail-closed
direction exists to prevent (the conformance masking differential pins it engine-by-engine). The
consequence to design for: `allow` is a certification tool for scopes narrow enough to certify. On
code whose values are inherently dynamic the right verdict is "uncertifiable", not a pass; narrow the
scope or make the values literal. One residual stays outside AS-EFF-008: a fully *unresolved* call
(`Unknown ∈ I(f)`, AS-EFF-003) could perform the effect invisibly without ever touching its literal
surface; pair the allowlist with a `deny Unknown <scope>` rule where even that residual must be
excluded.

A **layering** policy rule, `forbid <A> -> <B>`, constrains *who* a layer may depend on: no function in
scope `A` may transitively call into scope `B` (AS-EFF-009) — the dependency-direction boundary, checked
over the call graph (see SEMANTICS §6). Together the three policy rule kinds — `deny`/`pure` (what a
layer does), `allow Net` (which endpoints), and `forbid ->` (who it depends on) — make `CANDOR_POLICY`
an architecture-as-code layer.

### 6.1 Containment — the architecture-quality signal (deliberately not a "score")

candor defines **no single quality score**. Raw effect *counts* are domain-dependent — a database app
performs `Db` in most functions, which is not a defect — so any rolled-up grade would be meaningless
across domains and gameable. The domain-independent signal is **dispersion**: how well an effect that
*should* live in a dedicated layer actually stays there. A `Db`-heavy app with all `Db` in `dao` is
well-architected; one with `Db` in `model`, `controllers`, **and** `dao` is leaky, regardless of how
much `Db` it does. The total is domain-dependent; the dispersion is an architecture fact.

Two classes of effect:

- **boundary**: `Db`, `Net`, `Llm`, `Exec`, `Fs`, `Ipc`, `Clipboard`. These *should* be contained in a
  dedicated layer; their dispersion is the signal. (`Clipboard` is external-resource I/O, a boundary
  capability, so it is contained/scored, not cross-cutting.)
- **cross-cutting**: `Log`, `Clock`, `Rand`, `Env`. Pervasive by nature (logging/timestamps everywhere is
  normal), so they are reported but **not** scored. `Unknown` is excluded entirely (it is a visibility
  property, not an effect).

> **Note — "cross-cutting" here is unrelated to the "ambient authority" partition.** This containment
> split (`{Log,Clock,Rand,Env}` = cross-cutting vs the boundary effects) is about *where an effect should
> be contained*, and is independent of the no-ambient check's partition, which calls **`𝔼 \ {Log}`**
> "ambient authority" (every effect except `Log` is ambient authority a function should *receive* rather
> than reach for directly; SEMANTICS §6, AS-EFF-004). The two sets answer different questions and
> deliberately do not coincide; "ambient" is reserved for the capability sense, and this containment
> bucket is named "cross-cutting" to keep them apart.

A **layer** is inferred from the function name with no configuration: strip the longest module/package
prefix shared by *every* function (the codebase root), and the next segment is the layer (`pgman::app::…`
→ `app`; `com.example.dao.…` → `dao`; a multi-crate report → the crate). A function with no module
beyond the root (a free function, a root-package class) buckets into `(root)` rather than becoming its
own pseudo-layer.

For each boundary effect, **containment** is the share of its *direct* occurrences that fall in its
dominant layer (100% = fully contained). This is reported **per effect**, as a diagnostic, never summed
into one number.

⟨0.28⟩ **AND THE JSON SHAPE, PINNED BECAUSE IT WAS NOT.** `containment --json` and the `fix`/`fix-gate`
remedy documents carry SEVEN field names this document has never named — measured by conformance PART 42,
which harvests what the engines actually emit and compares it against SPEC.md. That is the identical
condition `judgedNothing` was in the morning it shipped as an array in three engines and a boolean in the
fourth, so these are pinned before a second engine guesses rather than after:

    containment    "contained": [ { "effect": "<E>", "containmentPct": <0..100 integer>,
                                    "layers": <n>, "owner": "<layer>",
                                    "placement": { "<layer>": <count>, … } }, … ]
                   "ambient":   { "<E>": <count>, … }   // the §6.1 ambient effects, keyed by EFFECT
                                                        // (engine vocabulary, not a user namespace)

    fix-gate       "remedies": [ { "fn": …, "effect": "<E>", "site": [ … ],
                                   "deniedSpan": [ "<fn>", … ],   // the functions the denied effect crosses
                                   "hoistTo": [ "<fn>", … ],      // where the boundary can move to; [] = nowhere
                                   "hoistHigher": [ "<fn>", … ],  // …and further up, if the caller allows it
                                   "cleanHoist": <bool>,          // the hoist introduces no new crossing
                                   "layer": "<layer>",            // the remedy's layer; "" = the root
                                   "policyAlternative": "<a policy line>"  // e.g. "allow Exec"
                                 }, … ]

    unverified     "unverified": [ { "fn": …, "rule": "<the policy line that could not be discharged>",
                                     "unknownWhy": [ … ],
                                     "upgrade": "<a policy line>" // e.g. "deny Unknown app" — the rule
                                   }, … ]                         // that WOULD make this decidable

    fix            "crossing": <bool>   // present iff the verb answered; see the ruling below

⟨0.28⟩ **`crossing` — PINNED, and pinning it fixes a purity defect on the other side.** This was the one
key left grandfathered when the other eleven were pinned, because it needed a ruling rather than a
transcription: candor-ts and candor-swift emit it from `fix` as a THREE-STATE discriminator — `true`
beside a plan, `false` with a `reason` on the no-crossing arm, and ABSENT when the verb refused — and the
MCP `candor_fix` tool contract instructs agents to check `refused` before `crossing`, so it is a shipped
consumer contract. candor-rust and candor-java emit no such key.

The tempting reading is that two engines minted a field and should drop it. **The measurement says
otherwise**: rust and java answer that same arm as **PROSE ON STDOUT, under `--json`** — which §3.3.1
independently forbids ("stdout MUST then be pure JSON"). So the choice is not *pin a key or not*; it is
*pin the key, or leave two engines emitting a determined negative as unparseable text on the machine
channel*. Removing it would also break a published tool contract to preserve a defect.

So `crossing` is a **boolean, present exactly when the verb answered**, absent when it refused — the same
present-iff-answered discipline ⟨0.28⟩ applies to `unanswerable`, and the reason the MCP contract's
check-`refused`-first ordering is correct rather than incidental. The `false` arm carries `reason`.
rust and java gain the key and stop printing prose onto a JSON stdout; ts and swift are already conformant.

*Recorded because the shape of the decision generalises: a key TWO engines emit and two do not is not
automatically a mint to be removed. Ask what the engines WITHOUT it are doing instead — here, the answer
was a second defect, and the divergence was the only thing making it visible.*

`containmentPct` is an INTEGER percentage, not a float and not a ratio — three engines agree and the
agreement is now a rule rather than a coincidence. `placement` is an object keyed by LAYER NAME, so it is
a user namespace: a reserved key may not be added beside its entries (§2.2's `@`-prefix problem, one level
in). `deniedSpan`, `hoistTo` and `site` are arrays of function names and MUST be emitted even when empty —
an absent `hoistTo` and an empty one mean different things (*not computed* vs *nowhere to hoist*), and this
document has ruled twice that a consumer must not have to tell those apart by guessing.

⟨0.28⟩ **`layerPrefix` IS THE ONE THAT MUST CHANGE, AND IT IS AN INSTRUCTIVE SHAPE.** candor-java emits a
top-level `"layerPrefix": "<the common prefix this run collapsed>"` from `containment`, and emits it
UNCONDITIONALLY — including `""` when nothing was collapsed. The other engines do not emit it at all. Both
halves are wrong in the way this document keeps correcting:

- a key one engine emits and another does not is a divergence a consumer sees, and
- a field that is **always present and usually empty** is the `fs: Vec::new()` defect recorded in
  `conformance/field_audit.py`'s header — *"a present-but-always-empty field asserts 'kind undetermined' on
  every function forever while wearing a schema that implies support"*. Requiring the other three to emit
  `""` forever would spread that rather than fix it.

The field is load-bearing when it is non-empty: `owner` and `placement` are layer names, and a collapsed
prefix changes what those names denote. So: **`layerPrefix` is emitted when, and only when, a prefix was
actually collapsed.** Its ABSENCE means no prefix was collapsed — a real answer under §2's
omit-rather-than-guess convention, not a gap. candor-java emitted it unconditionally when this clause was
written and now guards it; PART 45 pins both arms, including the NEGATIVE one — a run that collapses
nothing must emit no key at all, which is the arm a presence-only check cannot see. The other engines gain
the field if and when they collapse a prefix.

**The ratchet (`AS-EFF-010`).** Given a baseline report, an implementation compares the *set of layers*
each boundary effect appears in. If an effect appears in a layer it was **not** in before, that is a
containment regression (`AS-EFF-010`), and the check fails: the gate. The reverse, an effect that
*left* a layer, SHOULD be reported as an improvement (informative, not a failure). Because this compares
a codebase to *itself* over time, it is domain-independent and not gameable by renaming, and is the form
suitable for CI. The unsupervised per-layer diagnostic is a heuristic that assumes layer-organized code;
the ratchet is the robust form. An implementation that supports containment MUST treat it as a diagnostic
+ trend gate and MUST NOT present a single aggregate score.

### 6.2 The policy DSL (normative)

The policy modes (AS-EFF-006/008/009) and the `whatif` tool (§3.2) all read one **policy file** (the Rust
and JVM engines take its path from `CANDOR_POLICY`). For the gate to mean the same thing in every language
the grammar must be fixed, not merely "some rules text" — so this section is **normative**: a conformant
policy reader parses exactly this, and the cross-impl suite checks it (§7).

**Lexical.** One rule per line. A `#` begins a comment to end-of-line; blank lines and comment-only lines
are ignored. A line is split into tokens on runs of **ASCII whitespace** (space U+0020, tab U+0009,
and CR/LF/VT/FF U+000A–U+000D) and *only* these. A non-ASCII space (NBSP U+00A0, ideographic space
U+3000, NEL U+0085, …) is **not** a separator: it stays an ordinary character of its token, so the token
is malformed and the rule is ignored-with-a-warning, uniformly across engines. (Pinning the separator
class to ASCII is load-bearing: a language's "default whitespace" varies, Unicode `White_Space` vs JS
`\s` vs ASCII, so an unpinned class let one engine split a NBSP-bearing line and another silently DROP
the rule — a gateless-green divergence a shared gate must not have.) The first token is the **rule kind**. A
line whose kind is unrecognized, or that is malformed for its kind, is **ignored with a warning**, never
silently treated as a stricter or looser rule (silent reinterpretation is the one thing a security gate
must not do).

**An unreadable policy FILE is a failure, not an absent gate.** The malformed-line rule above is for
content; the file is different: when a policy is *configured* (a `--policy` flag, the `CANDOR_POLICY`
env) and cannot be read, the run MUST fail loudly with a non-zero exit (the code engines' CLIs use a
distinct `2`, vs `1` for a policy violation; an engine embedded in a compiler fails the build,
whose wrapper reports its own code) — it MUST NOT proceed gateless. A typo'd policy path
that runs green is a gate that silently passes everything, the exact failure a gate exists to
prevent. (Found live in a code engine: loud on stderr, but exit 0 — a CI gate that never bit.)

⟨0.28⟩ **AND A CONFIGURED POLICY THAT YIELDS ZERO RULES IS THE SAME FAILURE, REACHED THROUGH A READABLE
FILE.** The clause above keys on *cannot be read*; measured four-way 2026-08-10, the harm it names arrives
just as easily through a file that reads perfectly. Point `--policy` at a README — the wrong path in a CI
script, the commonest spelling of this mistake — and every engine writes

    { "ok": true, "violations": [] }

and exits 0. That is **byte-identical to the verdict of a gate that ran and found nothing**, and also
byte-identical to the no-gate-configured verdict (§3.3), so the one consumer this format exists for cannot
tell *your code is clean* from *your gate had no rules*. The human channel is fine, which is why it went
unnoticed: all four warn per ignored line. The verdict document is silent. Measured on the `gate --report`
verb too — a route is not covered by its sibling.

So: **when a policy is CONFIGURED and parsing yields NO RULES AT ALL, the run MUST refuse — exit 2 with
the fail-closed refusal document (§3.1)**, exactly as for an unreadable file. The `unevaluated` list
carries one entry naming the whole policy, the shape §3.1 already pins for a policy with no lines to name.

**Three things make this forced rather than chosen.** First, it is the clause above stated over the
CONDITION that makes it true rather than over the instance it was found in — the same correction ⟨0.24⟩
made twice in §3.1, and the harm ("a gate that silently passes everything") is quoted from the clause
above, not invented here. Second, **there is already a way to say "I am not gating": do not configure a
policy.** A configured policy yielding zero rules is therefore never a legitimate expression of intent —
it is always either a wrong path or a file the engine could not understand, and an engine that cannot
tell those apart from a real gate must not answer as though it ran one. Third, it is ⟨0.24⟩ §4's
zero-match ruling one level up: a RULE whose scope binds nothing is disclosed rather than scored as
satisfied, and a POLICY that contains no rules is the same shape and the stronger case.

**The line-level leniency above is UNCHANGED and still correct.** An unrecognized or malformed line stays
ignored-with-a-warning — silent reinterpretation remains the one thing a security gate must not do, and an
engine meeting a rule kind from a newer spec rung must not refuse the whole file over it. This rung is
about what that leniency COMPOSES TO: every line ignored is a gate, and it asked nothing.

⟨0.28⟩ **AND THE CONDITION IS A DROPPED LINE, NOT AN EMPTY POLICY — the clause above is stated over its own
instance, which is the fifth time in this document** (§3.1's ⟨0.24⟩ dropped-rule clause was the fourth, and
it disposes of the sharpest case: a typo'd effect token like `deny Nett app` is a policy ERROR at exit 2,
not an ignored line, so what follows is about the residue the forward-compat leniency deliberately keeps).
The zero-rule clause's justification is per-line: *"every line ignored is a gate, and it asked nothing"*,
and its measurement note — all four engines warn per ignored line while the verdict document stays silent —
is exactly as true of a policy where NINE of ten lines were dropped. The refusal fires only at zero
survivors, so the discontinuity is stark and the wrong way round:

    0 of 10 rules parse   →   exit 2, fail-closed refusal document
    1 of 10 rules parse   →   { "ok": true, "violations": [] }, exit 0, and the document says nothing
                              about the nine gates that were never asked

A 90%-gateless green is the harm this rung exists to close, arriving at every fraction below 100%.

Refusal is the wrong remedy there — it would break the forward-compatibility leniency this clause has just
finished defending. **Disclosure is the remedy**, and it is the same move ⟨0.15⟩ made for `coverage`: the
verdict document MUST carry the lines the parse dropped, so a machine consumer can see that the gate it is
reading is smaller than the gate that was written.

    "ignored": [ { "line": <n>, "text": "<the source line, verbatim>", "reason": "<why>" }, … ]

Omitted entirely when nothing was dropped, so a clean policy's verdict stays byte-identical. This is
distinct from `unevaluated`, and the distinction is load-bearing: `unevaluated` carries rules that PARSED
and could not be answered, `ignored` carries text that never became a rule at all. A consumer that sees
neither is entitled to believe the policy on disk is the policy that ran — which is the claim every engine
is currently making without support.

**The refusal covers the empty file and the all-comments file too**, and that is deliberate rather than
incidental: the operator who commits a placeholder policy and the operator who typo'd a path have written
the same thing, and `ok: true` is a claim about the CODE that neither run is entitled to make. An engine
adopting this rung on a codebase that has such a placeholder will start refusing — correctly, and the
remedy is one line (`# no rules yet` is still zero rules; remove the `policy` key instead).

**An unrecognized command-line FLAG is the same failure class.** A CLI MUST reject an unknown
leading-dash argument with a non-zero exit (the code engines use `2`), never silently ignore
it nor read it as a positional path. The same gateless-green hazard applies: a typo'd `--policy`/
`--poilcy` that is silently dropped runs the scan with no gate; an agent following a newer doc
against an older binary that swallows the unknown flag gets a misleading scan instead of an
"upgrade me" signal. The cross-impl suite probes this (an unknown flag → exit 2) across the engines.

**The four rule kinds:**

```
deny    <Effect>… [<scope>]          # AS-EFF-006 — what a layer may NOT do
pure    [<scope>]                    # AS-EFF-006 — shorthand for "deny every effect"
allow   <Effect> [in <scope>] <v>…   # AS-EFF-008 — which literals an effect may reach
forbid  <A> -> <B>                   # AS-EFF-009 — A may not depend on B
```

- **`deny`**: the tokens after `deny` are read left to right: each token that names an effect (the §1
  vocabulary, **or** the literal `Unknown`) joins the forbidden set; the **first** token that is not a
  known effect is the **scope**, and **ends the rule** (any further tokens are ignored). A `deny` that
  names no known effect is **dropped** (it is not a `pure` rule — that distinction is load-bearing).
  `Unknown` is denyable precisely so `deny Unknown <scope>` forbids the *unverifiable* case (§6,
  AS-EFF-008's companion).
- **`pure`**: an empty forbidden set, meaning **every** effect; the optional next token is the scope.
  `pure parse` ≡ "functions in `parse` must be effect-free."
- **`allow`**: the effect MUST be one of the **five** that carry a literal surface (`Net`, `Exec`, `Fs`,
  `Db`, ⟨0.13⟩ `Llm`, which rides `Net`'s host literal); an `allow` for any other effect is dropped with a
  warning. ⟨0.24⟩ *This said FOUR and omitted `Llm` from the moment `Llm` was added in ⟨0.13⟩; all three
  measurable engines have accepted `allow Llm <host>` the whole time.* An optional `in <scope>` follows; the
  remaining tokens are the allowed values (≥1 required, else the rule is dropped).
- **`forbid`**: two scopes separated by a literal `->` token (`forbid domain -> infra`). A line missing
  the arrow or either scope is dropped.
- ⟨0.29⟩ **`only`**: a scope, a literal `->` token, then **one or more** scopes
  (`only app.model -> app.dto app.util`). A line missing the arrow, the leading scope, or **every**
  trailing scope is dropped — an empty tail is NOT read as "may reach nothing", which is a different rule
  and one far likelier typed by accident than meant. **`only <A> -> <B> …` says A may reach A and the
  listed scopes and NOTHING ELSE**, and it charges its OWN code, **`AS-EFF-011`**.

  ⟨0.29⟩ *It charged `AS-EFF-009` for one commit, on the reasoning that the code already means "calls into
  a layer a declared dependency rule forbids" and an `only` is one. That is true about the ENGINE and wrong
  about the CONSUMER. A code is the handle a suppression, a dashboard link and an alert filter key on, and
  `forbid` and `only` are opposite constructs — must-not-reach versus must-be-on-the-list — with opposite
  remedies. The decisive argument is timing: before this rung an `AS-EFF-009` suppression meant exactly "I
  have accepted a `forbid` crossing", so shipping `only` under it would make every existing suppression
  silently begin muting a class of violation its author never accepted — a fail-open change to an
  operator's configuration, made by us, invisible to them. That is the argument `only` itself is built on,
  turned on the tool. Free to fix before release and breaking after it.*

  **`forbid` FAILS OPEN and `only` FAILS SAFE, which is the whole reason the second form exists.** A
  dependency you forgot to prohibit is silently permitted, so *"this package is a leaf"* can only be
  spelled with `forbid` as an enumeration of what it must not reach — a list that does not cover a package
  added tomorrow, and nothing says so. That is the allowlist hazard this document refuses throughout the
  ANALYSIS, sitting in the POLICY LANGUAGE. Under `only` the dependency you forgot to permit is a loud
  violation on the day it appears, which makes `only` the form to RECOMMEND for protecting a leaf.

  Three rules an implementation MUST follow, each of which could plausibly have gone the other way:

  1. **`A -> A` is IMPLICIT.** A scope may always reach itself. Without this the form is unusable for the
     case it exists for: a scope matches a contiguous run of segments, so `app.model` sits *under*
     `app`, and the natural rule for a leaf self-fires on every internal call.
  2. **The walk STOPS at a permitted scope, and DESCENDS THROUGH `from`.** A permitted callee's own
     dependencies are governed by the rules about IT; descending past it would make `only` demand the
     transitive closure of everything you permit, which is the same enumeration-that-rots one level down.
     A function in `A` calling another function in `A` that reaches `infra` is still `A` reaching `infra`.
  3. **Zero-match (§4) is measured on `from` ALONE**, unlike `forbid`, which counts a match on either
     endpoint. A `forbid`'s subject is the pair; an `only`'s subject is the scope it makes a promise
     ABOUT. A rule whose destinations all resolve while its `from` names nothing has bound nothing — and
     that is precisely the typo that leaves an operator believing a leaf is protected.

  **`only` is UNANSWERABLE from a report**, on the same §3.1 rule as `forbid` and for a stricter reason:
  `forbid` asks whether one named crossing is present, while `only` asks whether EVERY reached scope is on
  a list, so a report that omits a crossing does not merely under-report — it turns a green into a claim of
  COMPLETENESS. A route that discloses the rule MUST also REMOVE it from the evaluation; disclosing it and
  then evaluating it anyway is the shape this clause exists to prevent, and it is what a partial
  implementation produces. `only` is a RULE for §6.2's zero-rule check: a policy holding only `only` lines
  is armed, and refusing it as empty would turn that fail-closed guard into a false refusal.

  **`forbid` is UNANSWERABLE from a report** — §3.1's answerability rule already binds it, and this is a
  pointer to that rule, not a second statement of it. See §3.1 ⟨0.24⟩ ANSWERABILITY: *a rule whose evidence
  the wire does not carry MUST be refused (exit 2), never evaluated*, which names `forbid A -> B` in its
  own list. Evaluating `forbid` at SCAN time is the supported route.

  *⟨0.29⟩ This paragraph was, for one commit, a full restatement of the rule with its own grounding, and
  every part of that was a mistake worth recording rather than quietly deleting.*
  *(1) It claimed the behaviour was "specified nowhere". §3.1 had specified it since ⟨0.24⟩ — the MUST and
  the `forbid` bullet both — so the register briefly held TWO entries for one rule, one pinned and one not,
  which is a drift channel rather than a pin.*
  *(2) Its stated ground was FALSE and had already been retracted one section up. It said a report's
  `calls` graph is effect-relevant so a crossing into a pure unit is invisible; but §2.2 requires the
  SIDECAR to record every project function's edges INCLUDING pure ones, and PART 1b pins that. §3.1's
  `allow` bullet had already had to correct exactly this reasoning — "This clause first said the marker
  does not ride the wire, flatly. That is FALSE for at least one engine … Uniform refusal is the
  requirement; the wire's contents are not the reason." The real basis is that a report MUST NOT be
  back-filled from its sidecar, plus uniform refusal.*
  *(3) It stated the refusal UNCONDITIONALLY, which contradicts §3.1's precedence ruling: where a certain
  violation stands beside the refused rule, the gate exits 1 with the rule disclosed as `unevaluated`, not
  2. Measured — all four engines exit 1 on `deny Fs` + `forbid` over a report, so a fifth engine
  implementing this paragraph literally would have been the odd one out. A rule stated over the INSTANCE
  that was measured (a sole-`forbid` policy) rather than over the CONDITION, for the fourth time in this
  document, in the section whose own commentary names that hazard.*

**Reason-scoped `Unknown` (`deny E Unknown[class…]`)** ⟨0.19⟩**.** In a `deny`, the `Unknown` token MAY
carry a bracketed **reason-class filter**: `Unknown[reflect,dispatch]` denies the `Unknown` part only for a
function whose `Unknown` arises from one of the listed classes; a concrete effect in the same rule (`deny Net
Unknown[reflect] api`) is unaffected. The classes are the **closed, normative projection** of the §4
`unknownWhy` reasons onto a fixed cross-engine vocabulary — a reader of the policy knows the class set
without reading any engine's raw reason strings:

| class | raw `unknownWhy` prefixes it projects |
|---|---|
| `reflect` | reflection / metaprogramming (`reflect:*`, `dynamicMemberLookup`) |
| `dispatch` | unresolved virtual/dynamic dispatch, invokedynamic, same-name ambiguity (`dispatch:*`, `indy*`, `ambiguous:*`) |
| `indirect` | callback / closure / function-value / async-continuation indirection (`callback:*`, `closure*`, `task-handoff*`) |
| `native` | FFI / native boundary (`native:*`) |
| `unresolved` | generic unresolvable call/import **and the catch-all for any unrecognized raw reason** |
| `setup` | the analysis is not wired up — fixable, not a real hole (`missing-config`, `no-tsconfig`, no-`node_modules`) |

The projection is **conservative**: a raw reason matching no listed prefix maps to `unresolved`, and a
function whose `Unknown` carries no recorded reason **CONTRIBUTES** `unresolved` to its class set — so a
narrowed filter never *silently* tolerates a hole it failed to classify.

⟨0.24⟩ **The `--class` FILTER — normative, because it had no semantics here and three engines wrote three.**
`blindspots --class` and `unverified --class` (§3.1 ⟨0.20⟩) select the entries whose reason classes
intersect the filter. Until now this document named the flag and never said what it selects, which is how a
consumer-side rule with a measurable failure mode reached four implementations unexamined. Three
requirements:

0. **REQUIREMENT (1) BELOW — transitive resolution — applies to `unverified` and NOT to `blindspots`.**
   Both verbs keep the flag; what differs is what the class set is resolved over.
   `blindspots` is the **source** view (§3.1) and *excludes* a unit whose `Unknown` is purely inherited, so
   every entry it filters carries a direct reason by construction and the direct-only read is CORRECT
   there. Resolving transitively would pull in exactly the units that verb is defined to exclude, turning a
   ranked worklist of root causes into a list of everything downstream of them. `unverified` is the
   opposite: an inherited hole is still a hole the gate did not prove. **A shared code path is not a shared
   defect**, and this pair is the counterexample — one verb's definition is the other verb's bug.

1. **It MUST resolve the class set TRANSITIVELY, over the same reach the gate uses.** `unknownWhy` is
   **direct-only by design** (§4: a reason names a site in the function's *own* body), so a function whose
   `Unknown` is purely *inherited* carries no reason of its own. A filter matching against the direct field
   is reading a field that answers a different question. Measured: **44%** of `Unknown`-bearing entries on
   one corpus and **67%** on another carry no direct reason at all.
2. **It MUST fail CLOSED.** An entry the filter cannot classify is KEPT, never dropped. The failure it
   replaces read "no matching reason ⇒ exclude", so an unclassifiable hole was excluded by *every* filter,
   including one naming its own class.
3. **The contribution in (2) MUST be gated on the function having a DIRECT `Unknown` it did not name** —
   not on its reason set being absent. Absence is also what an *inherited* `Unknown` looks like, and
   contributing `unresolved` to one whose `Unknown` is correctly classified at the callee is the mirror
   fabrication. A fix that trades one for the other is not a fix.

⟨0.24⟩ **THE POLICY SIDE MUST REFUSE TOO — my "a dropped token leaves a WIDER rule" reasoning was FALSE,
and the false half is fail-open.** This clause used to justify the query/policy asymmetry by asserting that
dropping an unrecognised class token on the policy side can only widen. Measured four-way, it does both:

- `deny Unknown[corp]` — the *only* token is unrecognised, the filter empties, and the rule **WIDENS** to a
  bare `deny Unknown`. Merely surprising. **But the engine prints "ignoring policy rule" and then KEEPS and
  re-scopes it — a FALSE DISCLOSURE**, the `net-partner` class PART 13b already exists for.
- `deny Unknown[dispatch,nativ]` — a **typo among valid tokens**. It is silently dropped, the rule
  **NARROWS** to `[dispatch]`, and it **no longer gates native-caused holes at all** while the operator
  reads a gate that looks armed. That is fail-open, and it is the common case: a typo lands beside correct
  tokens far more often than alone.

So the policy side takes the same rule as the query side: **an unrecognised token in ANY policy value list
is a policy error — exit 2, the unreadable-policy posture (§6.2), naming the token and the accepted set.** A
policy that cannot be honoured as written is not silently rewritten into a different policy.

⟨0.24⟩ **"REASON-CLASS" WAS TOO NARROW, AND THE NARROWING WAS AN ARTIFACT OF WHERE I FOUND IT.** This
clause first said *reason-class token*, because a reason-class token is what the review measured. candor-rust
then measured the siblings and both are live:

- `deny Net[known-telemetry,unknown-hosst]` → **exit 0**, where the correctly-spelled rule exits 1. A
  NET-class typo, byte-identical in shape to the reason-class one.
- `unknown-alias corp = dispatch,nativ` → the DEFINITION silently becomes `{dispatch}`, and the gate goes
  **green on a native hole** where `= dispatch,native` exits 1. The typo is in the vocabulary the policy is
  written against rather than in the policy, and it fails open just the same.

The rule was never about reason-classes; it is about **a policy value list the implementation cannot honour
as written**. So it binds every such list — reason-class filters, net-class filters, and alias definitions
alike. Generalising here is not speculative: the argument in this clause never mentions which vocabulary the
token belongs to, and each place I let it stay narrow is a place the same fail-open survives under a
different key. The asymmetry I claimed
does not exist; only the *direction* of the surprise differed, and one of the two directions is a hole.

⟨0.24⟩ **THE FLAG'S VALUE GRAMMAR**, which was never stated and is therefore where the next divergence
would have gone. `--class <c>[,<c>…]` takes ONE comma-separated list; it is **not repeatable** (a second
occurrence is a usage error, not a union). Accepted tokens are the six classes, plus the two aliases `*`
and `dynamic` — the latter being what the diagnostic below uses, so it must be accepted. An
**UNRECOGNISED** token is a **usage error: exit 2**, naming the token and listing the accepted set. It is
NOT the policy-side drop-with-warning behaviour, and the difference is the point: here a dropped token
leaves a *narrower* filter — so `--class
dyanmic` would silently answer a question the user did not ask, with a smaller number, which is the
fail-open this whole clause exists to close. A query flag that cannot be honoured is refused.

The diagnostic is cheap and every implementation should carry it as a test, **but it must be stated
precisely, because the obvious phrasing is false.** `--class dynamic` is an alias for every *genuine* class
— which by its own definition **excludes `setup`**, and `setup`-classed entries are reachable
(`missing-config`, `no-tsconfig`). So the invariant is *filtered = unfiltered MINUS entries whose only class
is `setup`*, or equivalently, run the diagnostic on a setup-free fixture. ⟨0.24⟩ *This clause first said
"`dynamic` must exclude nothing", flatly. That is a normative test that fails spuriously on any corpus
carrying a `setup` reason, and it would have pressured implementers to fold `setup` into `dynamic` and
contradict its definition. Corrected on review.* With that stated — a filtered count below the unfiltered one is
the defect, and the gap is its size. Measured on the engine where this was found, before repair: 387 → 230
(−41%) on a corpus target and 51 → 16 (−69%) on the engine's own sources; after, both converge exactly
across all eight target × policy rows. The *discrimination* control matters equally and is the one a blanket
"keep everything" would fail: after repair, `--class unresolved` selects **6 of 387** and `--class native`
selects **0**.

Why this is a soundness clause and not a precision one: `unverified` exists to name the holes a `pure` /
`deny E` layer PASSES without proving anything — the tool whose whole job is "this gate is green but not
provably so". A filter that fails open makes it under-report the holes it was built to surface, and
under-report *more* the more the user narrows.

**THE GATE AND THE DISCLOSURE MUST APPLY THE SAME RULE, AND SHOULD SHARE THE SAME CODE.** In the engine
where this was traced to a root cause, the gate had *never* been party to the defect — it already resolved
transitively and already treated an absent class set as `unresolved`. The divergence was entirely
consumer-side, in the one query that reads a **report** rather than the scan's in-memory graph, and which
carried an **open-coded second copy** of the classification. Two implementations of one rule inside one
engine, one of them correct, drifting silently because nothing compared them. A disclosure that contradicts
the gate beside it is worse than either being wrong alone: it tells the user their gate is green *and*
under-reports why they should not believe it. The repair there was structural — hoist the fixpoint and the
match rule into shared code so the two cannot drift — and that is the shape to prefer over patching the
consumer.

⟨0.24⟩ **IMPLEMENT IT AT THE SOURCE, NOT AT THE JOIN — one engine already did, and that is the shape to
copy.** The rule above is written as a property of the class set, but the right place to satisfy it is where
the `Unknown` is *created*: an engine that cannot account for an `Unknown` records a reason for it there and
then, so the class set is never assembled from nothing. candor-swift does exactly this — it synthesizes a
`dep:<hash>` reason per dependency ENTRY, precisely when the dependency classified nothing, and a
`dep-stale:<pkg>` for a distrusted producer; both project here to `unresolved`. Because that happens per
entry rather than per function, a caller of both a reasonless dep and a reasoned one accumulates
`{unresolved, dispatch}` naturally, with no join-time special case at all.

Measured consequence: candor-swift's empty-set default is **unreachable** — instrumented over two real
targets, **0 fires across 487 `Unknown`-bearing functions**, confirmed by an offline recomputation of the
class fixpoint. Implementing the join-side rule there would have been a no-op.

**THE STRONGEST FORM IS TO MAKE THE STATE UNWRITABLE, NOT MERELY UNREACHED — and one engine already does.**
candor-ts is at the source twice over: its emitter writes `unknownWhy: ["unresolved"]` on any direct
`Unknown` it could not name, *and* a trust-marker self-check **REFUSES TO WRITE THE REPORT AT ALL** (exit 2,
"direct carries `Unknown` but `unknownWhy` is empty") if one ever escaped. Measured the same way: **0 fires
across 1872 `Unknown`-bearing functions** over five arms including trusted and stale chained dependencies.
Established by mutation rather than inspection — deleting the fallback turns the stale-dependency arm into
exit 2 with no report, which is the self-check firing.

That is the ideal an implementation should aim at. A join-side default is a *coping* mechanism; a
source-side contribution makes the state *unreached*; a producer-side self-check makes it **unwritable**,
so the ill-formed signature cannot leave the engine even if a future edit reopens the path. Recall why this
matters: the state is not merely undesirable, it is **not representable in the formal model at all** (the
reason set is the carrier of the `Unknown`), so an engine that can emit it is emitting something the theory
has no image for.

This is the same conclusion the formal model reaches from the other end (`reference/policy_model.py`): a
reasonless `Unknown` is **not representable** in the `(S, D)` lattice at all, because Def 6 makes `D` the
carrier of the `Unknown` — so the state must be made *unreachable* rather than *handled*. An engine that
patches the join is treating a symptom; an engine that attaches a reason at the source has made the
ill-formed signature impossible to construct. Note that swift arrived here independently, before the model
was written, which is the strongest evidence available that it is the right shape rather than a convenient
one.

The failure mode to avoid is the naive form: contributing `unresolved` whenever an `Unknown` is present,
without asking whether it is already accounted for. Measured on the same corpus that yields 0 legitimate
fires, that would mark **435 functions** — the flood, and it would make the `[class]` filter useless.

⟨0.24⟩ **`ambiguous:` is a §4 kind, and was projected here before it was one.** This table has always
mapped `ambiguous:*` to `dispatch`, so a CONSUMER meeting the token classified it correctly — while §4's
kind list omitted it, making the PRODUCER that emits it non-conforming. One section blessed what the other
excluded, and the asymmetry survived because a consumer never complains about a token it can classify.

It is now a fifth kind in §4. The alternative — stop emitting it — was measured and rejected: on candor-rust
it is **8710 of 19607** `Unknown`-bearing entries, and reclassifying it to `indirect` takes
`deny E Unknown[dispatch]` from **58 of 200 crates to 0 of 200**. That is not a narrowing, it is a deletion
of the verb on that engine. `ambiguous:` also names something the other four kinds genuinely do not: not an
unresolved DISPATCH (no owner type was ever formed) and not a `callback:` (no function value is involved) —
the analyser's own name resolution was ambiguous. A vocabulary that cannot say that forces an engine to
either lie or fall silent.

⟨0.24⟩ **`CONTRIBUTES`, not "is treated as" — and the difference is a proved property.** This clause used to
read *"a function whose `Unknown` carries no recorded reason is **treated as** `unresolved`"*, i.e. the class
defaulted to `unresolved` when the class set was **empty**. That is keyed on ABSENCE, and absence is not
upward-closed: acquiring a reason *removed* the default. The result was a measured counterexample to the
monotone-denial lemma's corollary — a function calling one reasonless dependency was REJECTED by
`deny Unknown[unresolved]`, a function calling one reasoned dependency was correctly not, and a function
calling **both** was **not rejected**. Adding a call turned a red verdict green, which is precisely the
"silent relaxation" the lemma exists to forbid.

The engines were conforming when this happened; the defect was here. Under the contribution reading both
properties hold at once: an unclassifiable hole still matches `Unknown[unresolved]` (fail-closed, which is
what the clause was for), and a class set can only ever GROW as more is learned (monotone, which is what the
lemma needs). A conforming implementation must therefore ADD `unresolved` to the class set of any function
carrying an `Unknown` with no reason, rather than consulting emptiness. The reason class **propagates transitively** along the
call graph exactly as the `Unknown` effect does: a function that inherits `Unknown` from a callee is scoped
by that callee's reason class (the `unknownWhy` a report emits stays per-function/direct; the *gate*
resolves the transitive class). Filter forms:

- bare **`Unknown`** and **`Unknown[*]`** mean **all classes** — a pre-0.18 `deny E Unknown` is byte-identical
  (soundness-by-default; narrowing is opt-in).
- **`Unknown[dynamic]`** is a built-in alias for every *genuine* class (`reflect,dispatch,indirect,native,unresolved`
  — excludes `setup`): the recommended usable strict gate.
- ⟨0.24⟩ **SUPERSEDED — an unrecognised class token is now a POLICY ERROR (exit 2), see §6.2's
  unrecognised-token rule.** This bullet is kept only to name what it used to say, because a review found it
  still reading as normative 130 lines below the rule that replaced it, which makes it a **licence to
  regress**: an engine could cite it and reintroduce the `deny Unknown[dispatch,nativ]` → `[dispatch]`
  narrowing that stops gating native holes. A corrected assertion outliving its correction in a second
  location is a defect class this document has now produced twice. FORMER TEXT: an unrecognized class token
  in the brackets was dropped with a warning (the rule keeps its recognized
  classes); a narrowed filter that omits `unresolved` SHOULD emit an **advisory under-gating lint** (it may
  tolerate holes the engine could not classify).
- **`pure`** is unaffected — **its verdict never depended on `Unknown` at all**; reason-scoping is a
  `deny`-side feature only. ⟨0.24⟩ *This bullet previously read "it fails on any `Unknown` (all classes)",
  contradicting §4.0's verb table, conformance **PART 16** (which pins the same fixture under a bare `pure`
  as PASS, four-way) and every engine. `D ≠ ∅` alone is AS-EFF-003 disclosure, not an AS-EFF-006 violation
  — which is exactly why `unverified` exists. PAPER3's Definition 32 carried the same error; the reference
  model has been amended to match the contract, not the reverse.*

A conformant `--gate-json` verdict (§3.3) records, on an `AS-EFF-006` violation whose `effects` include
`Unknown`, a **`reasonClass`** array listing **all** reason classes present on the function (not just the
matched one), so a consumer sees every reason the strict gate bit. Config MAY define a **named class alias**
via a `.candor/config` `unknown-alias <name> = <class,…>` entry that a rule references **explicitly**
(`Unknown[<name>]`); a config alias is a spelling convenience only — it MUST NOT change what bare `deny E
Unknown` means (that is always `Unknown[*]`, everywhere), so a policy's denied set is always legible from the
policy alone.

**`Net` destination-class (`deny Net[dest…]`)** ⟨0.21⟩**.** In a `deny`, the `Net` token MAY carry a bracketed
**destination-class filter**: `deny Net[unknown-host]` denies the `Net` part only for a function whose `Net`
reaches a host of one of the listed classes; a concrete effect in the same rule is unaffected. This makes the
industry security use case gate-able — *"the domain layer may egress to declared partners and telemetry, but
not to an unknown host"* — which bare `deny Net` (all destinations) cannot express. The closed, normative
vocabulary refines a `Net` host literal (the §2 `hosts` surface) into a **destination class**:

| class | source of truth | meaning |
|---|---|---|
| `known-telemetry` | a curated, four-way-**verbatim** `TELEMETRY_HOSTS` set (the `MODEL_HOSTS` precedent) — analytics / monitoring / error-tracking | a benign observability endpoint |
| `known-partner` | a config-declared `.candor/config` `net-partner <host>` (per-project) **OR** a model host (the §1 `Llm` refinement — a declared-ish external API) | a host the project recognizes as a business partner |
| `unknown-host` | the honest default — every visible host on neither list, **AND** every function whose `Net` host is unresolved / runtime-computed / structurally masked | candor makes no claim; could be benign or exfiltration |

The classifier is **fail-closed** — the DUAL of the reason-class conservatism: an asserted-safe class
(`known-telemetry`/`known-partner`) is assigned **only** from an exact host-literal match against the curated
set / declared partners (the literal IS the match key). Everything else is `unknown-host`: an unresolved or
runtime-computed host, a **structurally-masked** surface (an AS-EFF-008 incomplete `Net` — so a benign visible
telemetry host can never certify a function that *also* reaches an invisible endpoint), and any host on neither
list. So `deny Net[unknown-host]` fails closed on anything candor cannot positively identify — over-reporting
the exfiltration risk, never under-reporting it. The destination class **propagates transitively** along the
call graph exactly as the `Net` effect does. Filter forms mirror `Unknown[…]`:

- bare **`Net`** and **`Net[*]`** mean **all destinations** — a pre-0.21 `deny Net` is byte-identical
  (backward-compatible; narrowing is opt-in).
- ⟨0.24⟩ **SUPERSEDED — an unrecognised class token is now a POLICY ERROR (exit 2), see §6.2's
  unrecognised-token rule.** This bullet is kept only to name what it used to say, because a review found it
  still reading as normative 130 lines below the rule that replaced it, which makes it a **licence to
  regress**: an engine could cite it and reintroduce the `deny Unknown[dispatch,nativ]` → `[dispatch]`
  narrowing that stops gating native holes. A corrected assertion outliving its correction in a second
  location is a defect class this document has now produced twice. FORMER TEXT: an unrecognized class token
  in the brackets was dropped with a warning (the rule keeps its recognized
  classes).
- **`pure`** is unaffected — it fails on *any* `Net`; destination-scoping is a `deny`-side feature only.

Per-function, a conformant report MAY carry a **`netClass`** array (§2) — the destination classes present in a
function's transitive `Net` surface — and an `AS-EFF-006` `--gate-json` verdict whose `effects` include `Net`
records the same array (all classes on the function, not just the matched one), so a consumer sees which class
the security gate bit. `net-partner` is per-project and so MUST be config-declared, never a universal list; and
like `unknown-alias` it is a spelling of *"I accept `Net` to this host"* — it can never make a bare `deny Net`
narrower, so a policy's denied set stays legible from the policy alone. (Design: `NET-DESTINATION-CLASS-DESIGN.md`.)

**Scope matching** (`<scope>` against a function's fully-qualified name) is **by path segment, not
substring**. Split both on the language's path separator (`::` in Rust, `.` on the JVM) — **and on the
language's nested-scope boundaries**, the same boundaries the §3.1 query name ladder recognizes: the
JVM's `$` nested-type separator (`q.L$app.entry` has segment `app`) and a TS namespace segment count as
segments too, so a layer rule bites a layer whether it is a package, a module, a directory, a nested
type or a namespace (a 2026-07-09 clarification: the engines diverged on nested scopes — a `forbid
app -> repo` that bit a Rust module missed a JVM nested class). The scope matches
iff its segments appear as a **contiguous run** in the name where every segment **except the last** matches
exactly and the **last** segment is a **prefix** of its name-segment. So scope `domain` matches
`app::domain::handle`, `domain::handle`, and the function `domain_logic` (last-segment prefix), but **not**
`subdomain` or `not_my_domain` (substring, not a segment boundary); scope `net::client` matches
`crate::net::client_pool::get` but not `crate::network::client` (intermediate segments are exact, not
prefixes). An **absent/empty scope means the whole compilation unit** (matches every function).

**Literal matching** (`allow`) is **per effect**: a `Net` host matches by hostname with the port ignored
(`api.stripe.com` allows `api.stripe.com:443`); an `Exec` command matches by basename
(`git` allows `/usr/bin/git`); an `Fs` path matches by **path-boundary-respecting prefix** (an allowed
directory covers itself and everything beneath it, but `/etc/app` does **not** cover `/etc/apppwned`, and a
reached path that climbs out via `..` is never covered); a `Db` table matches by **case-insensitive exact
qualified name**, with `schema.*` covering every table in that schema (boundary-respecting: `ledger.*`
does not cover `ledgerx.entries`) and a bare allowed name never silently widening to a qualified one
(`entries` does not cover `ledger.entries`). Matching is over the **transitive**
`hosts`/`cmds`/`paths`/`tables` surface (§2), so a value buried in a deep or cross-crate callee is still
checked. Each matching `allow` rule is checked **independently** (the SEMANTICS predicate quantifies per
rule): two rules that each cover half of a function's reached literals do not pass by union.

**From gate to guard — runtime enforcement** ⟨0.5⟩. A policy is an *advisory* gate by default: the
engine DETECTS a violation (a build fails), but nothing stops the effect at runtime. Where the analysed
artifact runs on a host with a native capability boundary, an implementation MAY **compile a `deny
<Effect>` rule into a runtime guard** that enforces the same boundary — a seccomp/landlock profile for a
process, or, for an agent fleet, the harness's own `permissions.deny` over the tools that produce the
effect. This is the dual of analysis: the analyzer READS the enforcement surface (§4 — an agent engine
subtracts a hard-denied tool); the guard WRITES it. The guard MUST **disclose the cliff it
cannot close**: denying the tools that *directly* perform an effect does not bind a subprocess (`Exec`)
that can reach it anyway, so a guard MUST report that residual path rather than imply total
enforcement. Per-target scopes a host boundary cannot express (a project-wide `permissions.deny` is not
per-agent) MUST be reported as unenforceable at that layer, not silently widened to everything.

## 7. Conformance checklist for an implementation

Two **profiles** exist, and a claim of conformance names one. A **sound engine** meets every MUST below;
this is the default meaning of "conformant". A **disclosed syntactic floor** (the Rust repo's stable
`candor-scan` backend is the canonical example) deliberately does not claim items 1/4: it documents that
it can under-report *silently* (item 7 applied to its own design), meets the
interchange items (2–3, 5–6, 8, 14) and answers the cross-impl conformance fixtures it can. Both declare
the envelope `spec` of the contract whose **interchange surfaces** they implement; what differs (and MUST
be documented, never implied away) is the §4 claim. (Item 13 states the same split for the soundness
harness; this paragraph names it as a profile so "every conformant engine agrees" is a precise claim, not
one that quietly includes an engine the checklist would otherwise disqualify.)

A **sound engine** conforms to candor-spec if it:

1. resolves call targets using type information (not purely syntactically);
2. computes a per-function **transitive** effect set;
3. emits the §2 report schema;
4. honours the §4 trust contract: unresolved ⇒ `Unknown`, never silent-pure;
5. supports at least **audit**, **JSON**, and **baseline-guard** modes, driven through the **required
   command-line surface** of §3.3: `--policy` (honouring `CANDOR_POLICY`), `--json` to stdout,
   `--version`/`-V` carrying the spec version, `--help`/`-h`, `--agents` (the embedded agent
   contract, item 11), for an engine declaring `spec ≥ 0.8`, `--gate-json` (the structured
   gate verdict), and, for an engine declaring `spec ≥ 0.9`, the **remedial tool surface** —
   `fix`/`fix-gate` and `unverified` (§3.1/§3.3) plus the gate's provable-purity auto-disclosure (a
   verdict-preserving advisory note on a `--policy` scan), and, for an engine declaring `spec ≥ 0.10`,
   every exposed §3.1 query verb driven through the **canonical query grammar** of §3.3.1 — report
   discovery with a `--report` override, `--json` selection, `--policy` as a flag — with flag names and
   help wording consistent across engines;
6. uses the §1 vocabulary and §6 codes where they apply, and, if it enforces any policy mode, parses
   the §6.2 policy DSL exactly (so a policy file means the same thing in every language);
7. documents, plainly and in its own docs, what it cannot see;
8. declares the **spec version** it implements (the envelope's `spec`, §2.1) and keeps it in step with
   this document.

It SHOULD additionally (items 9–13):

9. emit the **call-graph sidecar** (§2.2): required if it answers any caller-direction query
   (`callers`/`whatif`/`rewire`), since the report alone omits pure functions;
10. expose the read-only queries (§3.1) and the pre-edit/structural tools (§3.2) under
    **cross-language-consistent** names and shapes, so an agent uses any implementation's output
    identically. The cross-impl conformance suite checks this for effect sets, the `whatif` verdict +
    blast radius, the `fix`/`fix-gate` remedy (PART 12b), the `unverified` provable-purity disclosure and
    its gate auto-disclosure (PARTs 12c/12d), the `rewire` verdict, the `§6.2` policy-DSL parse, the §2
    tables extraction, the item-14 coverage ledger disclosure, and the read-only queries' JSON shapes +
    name-match ladder;
11. ship the **standard companion documents**: an `AGENTS.md` (how an AI coding agent produces and
    consumes this implementation's reports; the per-language counterpart of this repo's
    language-agnostic AGENTS.md), and a `PROVE-IT.md` (a runnable self-experiment an adopter's own
    agent executes on their codebase: manual blast-radius trace committed *before* the tool runs,
    every claimed miss verified at a file:line, and a negative outcome reported as found, so value is
    demonstrated on *their* code, not the implementer's fixtures). The §4 exemption/disclosure
    documentation is already a MUST (items 6–7). The engine is additionally
    **self-describing**: its installed artifact embeds the `AGENTS.md` and prints it under the
    **`--agents` flag, REQUIRED in the §3.3 command-line surface** (all four engines ship it, and
    the conformance suite Part 7 gates it pass/fail), prefixed by a header naming the installed
    engine version, so the contract an agent reads always matches the binary it runs. A vendored or
    remotely fetched copy can describe a *different* version (or be tampered with in transit); the
    embedded copy is the §2.1 version-trust rule applied to documentation. The embedded copy MUST
    equal the repo's `AGENTS.md` (a drift gate in the engine's test suite), and the doc SHOULD tell
    agents to prefer `--agents` over any other copy, re-reading it when the engine version changes.
    (The *flag* and the embedded-copy equality are MUSTs; shipping the companion `PROVE-IT.md`
    remains a SHOULD.);
12. **use candor on itself.** Analyze its own codebase cleanly (no crash, a plausible report:
    self-analysis is the free real-world test), and run a **self-gate** in CI: a declared
    `CANDOR_POLICY` (§6.2) over its own code that fails the build when violated (e.g. the code
    engines are analyzers whose own boundary is "Fs/Env only — never Net/Db/Exec/Ipc"). The
    self-gate is the falsifiable form of dogfooding: an effect-gate implementation whose own gate
    is red (or absent) is asking adopters to hold a standard it does not hold itself. (This item
    previously said "MUST analyze" inside this SHOULD list, a wording contradiction; the SHOULD
    umbrella governs.)
13. **enforce the §4 trust contract with an adversarial soundness harness.** Item 4 states the
    contract; this is what makes it a tested property instead of a hope. The harness GENERATES
    programs that thread a *known* effect from a sink through the language's call forms, every form
    that could hide an edge: direct calls and the language's lambda/closure idioms, method dispatch,
    cross-module calls, callback values, and the language's desugars (operators, `?`, `await`,
    destructors, iterator protocols, whatever the language has) and asserts every reachable unit
    is reported with the effect **or** `Unknown`. A reachable unit reported pure, or omitted, fails
    the harness: that is the silent under-report §4 forbids. Requirements on the harness itself:
    - **Teeth-verified:** disabling a resolution mechanism MUST make the harness fail: a harness
      that cannot fail proves nothing. Verify teeth per *mechanism*, not per line: engines grow
      redundant defenses (two independent paths both catching a callback call), and neutering one
      line of a doubly-covered mechanism passes vacuously; neuter the mechanism.
    - **Forms are the coverage unit.** The harness proves only the forms it encodes; every
      code engine has had a "no known unencoded form remains" claim refuted by a new form
      found in the wild. Treat the form list as open, and add a form with every soundness fix.
    - A **precision twin** is recommended: a pure bystander unit that must stay OUT of the report,
      so the harness also catches an engine that goes sound by flooding.
    - The harness SHOULD run in CI alongside the engine's tests; an unrun harness proves nothing.
    All four code engines ship one (Rust `soundness/`, JVM `soundness/`, candor-ts `fuzz.mjs`,
    candor-swift `fuzz.py`),
    and the design ports beyond programming languages (the candor-agents engine runs the same
    harness shape over agent-fleet effect graphs). Like every SHOULD in this list, the harness is a
    claim an engine either ships or doesn't make: an engine without one has an *untested* §4, and
    its docs must not suggest otherwise. The harness applies per **engine**, not per repo, and only
    to engines that claim §4 at all: a deliberately syntactic floor (the Rust repo's stable
    `candor-scan` backend) documents that it under-reports *silently*, so it does not claim item 4 (or
    item 1's type-informed resolution), so there is no §4 claim for a harness to test; its
    obligations are item 7's disclosure duty and the cross-impl conformance fixtures it does answer. In the
    Rust repo the harness accordingly drives the nightly lint (the engine that claims §4), not
    `candor-scan`.
And, as of spec 0.4, it MUST also (the number is kept from its SHOULD-era introduction, so references
to "item 14" stay valid):

14. **disclose the curated classifier's blind spots per scan — the coverage ledger.** Every
    candor engine classifies external calls against a curated table, and an UNLISTED package
    contributes nothing: invisible, not `Unknown`. That is the documented weaker edge of item 4's promise,
    and historically its sharpest (an unlisted password-hashing library read silently pure on
    exactly the call a security review cared about). A conforming engine MUST therefore emit,
    with each scan, the external packages the scanned code **demonstrably calls** that the
    classifier neither classifies nor has reviewed-pure, named with call counts: per-scan
    evidence in the receipt, not a documentation footnote. The disclosure line contains the
    canonical marker **`classifier doesn't cover`** so consumers (and the conformance suite, which
    asserts it) can find it without per-engine wording knowledge. Exempt from the disclosure: the
    platform/builtin frontier (the classifier's actual job), packages the classifier covers
    verb-precisely (zero classifications can mean the code touches only their pure surface),
    and packages a chained sibling report covers (§2, including an EMPTY report, whose silence
    is a purity claim). A domain engine (§4) satisfies this item over its own curated frontier:
    candor-agents' ledger names the uncurated MCP servers, unknown tools, and unlisted literal
    command heads the scan relied on (`mcp:`/`tool:`/`head:` with unit counts), plus the curated
    reviewed-pure grants the verdict rests on: the domain analog of "packages the code
    demonstrably calls". The ledger plus chaining (§2) is the curation treadmill's exit: the
    disclosure names what is invisible, one dependency scan closes it, and the curated table's
    long-term obligation shrinks to the builtin/FFI frontier. The cross-impl conformance suite
    pins the disclosure's behavior in all four engines.

## 8. Changelog

The spec version is the contract version (§2.1) — bumped on additive changes (a minor: a new optional
field or `AS-EFF` code) or breaking ones (a major: the envelope reshape, a removed field). Implementations
declare it via the envelope's `spec`.

- **0.30 (conformance-pinned four-way, PART 48 amended + PART 54)** — the **first NON-ADDITIVE rung**: the
  first whose verdict change lands on TRUSTED, UNCHANGED inputs with no precondition. (0.24 below is the
  first rung that could turn a green gate red at all, and says so; it needed a stale or unreadable input to
  do it. This one needs nothing — a report that passed yesterday can exit 2 today on the same bytes.) No field is added or removed: `outOfScope`
  (§2, ⟨0.29⟩) is unchanged in shape and in emission rule. What changes is what a gate DOES with it —
  **a non-empty `outOfScope` now makes the verdict `ok: false`, `incomplete: true`, exit 2**, reversing
  ⟨0.29⟩'s "an out-of-scope finding MUST NOT move the verdict".

  **Reversed on a measurement.** The ⟨0.29⟩ rule assumed the peek surfaces UNCERTAINTY, which a gate may
  reasonably decline to act on. Measured on published 0.29.1 under `deny Net`, it does not: it resolves a
  CONCRETE denied effect and names the function — `axios` 37 functions `performs Net`, `node-fetch` 15,
  `ky` 9, `execa` 9, `zx` 3, `ofetch` 1, every one exiting 0 with `policy ✓`. `axios` ships 5 real `.ts`
  files, all of them type tests, against 160 `.js` implementation files. An engine that concludes a
  function performs the denied effect, prints that conclusion, and then certifies the tree is committing
  the cardinal sin holding its own evidence.

  **Exit 2, not exit 1**: these are still never members of `violations`, because the gate did not judge
  them and a violation claim would be false in the other direction. It reuses ⟨0.21⟩'s
  `{ok:false, incomplete:true}` and follows ⟨0.27⟩'s precedent that an unreadable configured input is
  UNEVALUABLE rather than reduced coverage.

  **Bounded, so the over-charge control is structural.** ⟨0.29⟩ already restricts `outOfScope` to effects
  the policy DENIES, so the trigger is never "you excluded something" but "you excluded something that
  does the thing you forbade". Across 27 real packages it flips the 6 above and leaves 14 green untouched.
  Present-and-empty stays asked-and-clear and stays exit 0; an ABSENT key is ⟨0.26⟩ *cannot answer* and
  does NOT trigger the clause, so pre-⟨0.30⟩ reports and no-policy reports are unaffected.

- **0.29 (all code engines declare `0.29`; conformance-pinned four-way, PARTs 48–53)** — a **tier-1
  additive** rung: **THE FILE SET — what a report says about code it never opened.** ⟨0.21⟩ gave the
  report a completeness manifest, but `unanalyzed` names files an engine OPENED and could not read; it
  said nothing about files never opened at all, and a consumer could not tell the two apart because
  `analyzed.count` is a NUMERATOR whose denominator — the engine's file selector — was invisible.

  MEASURED FOUR-WAY: a same-language source performing `Exec`, sitting outside the engine's selector,
  under `deny Exec`. All four answered `policy ✓`, exit 0, with no note on stderr, no key in the report
  and no exit code — a false all-clear under an explicit deny, in every engine, agreeing with each
  other, which by this project's own standing rule is the weakest evidence of correctness available.

  The envelope gains **`excluded: [{class, count, peeked, reason}]`** — THE SCOPE, the files the scan
  chose not to OPEN, emitted whenever the engine can enumerate its own selection, `[]` INCLUDED (an
  empty list is the positive statement *I looked and excluded nothing*, and under ⟨0.26⟩ an absent key
  means *this producer cannot answer*) — and **`outOfScope: [{fn, path, effects, class, reason}]`**, THE
  PEEK: an effect found in a file the gate did not judge, emitted only when a policy is CONFIGURED and
  HONOURED and only for effects that policy DENIES. **`peeked: true` MUST mean every file of that class
  was READ on this run**, so a file the peek opened and could not read withdraws the claim for its
  class. Per-function **`incomplete: ["<Effect>"…]`** names the effects whose LOCATOR a unit could not
  determine. Additive: the peek's findings did not move the verdict — a rule ⟨0.30⟩ later reverses.

- **0.28 (all code engines declare `0.28`; conformance-pinned four-way, PARTs 37–39)** — a **tier-1**
  rung: **THE REPORT SINK IS ARMED THE SAME WAY THE VERDICT SINK IS.** ⟨0.27⟩ armed `--gate-json` so a
  run that died wrote a fail-closed document rather than leaving the previous run's green one on disk.
  The REPORT had no such arming, so the identical hazard remained one file over: a scan that failed,
  crashed or was killed left `report.json` from the last good run, and every consumer — the gate, the
  query verbs, a CI wrapper — read it as current. The report sink is now armed on exit-2 causes too,
  with a manifest-carrying empty that says why.

  Also: §6.2 **`ignored: [{line, text, reason}]`** — the policy lines the parse DROPPED, in the machine
  channel, so a consumer can see that the gate it is reading is SMALLER than the gate that was written
  (measured four-way: all four warned per dropped line on stderr while the verdict document stayed
  silent, so 1-of-10 rules parsing wrote `{"ok": true, "violations": []}` at exit 0 with nothing said
  about the nine gates never asked). And SPEC §2's **row 3 split**: a report carrying NO `analyzed` key
  is a pre-⟨0.21⟩ producer that DECLARES nothing, which is a different claim from one declaring
  `analyzed.count: 0`, and reporting the first as the second is a FALSE disclosure — a class this
  family rates worse than a missing one.

- **0.27 (all code engines declare `0.27`; conformance-pinned four-way, PART 31)** — a **tier-1 additive**
  rung: the envelope's **`resolves`** array (§2.1) declares which optional per-function refinement surfaces
  a producer actually computes.

  **Motivated by a measurement, not a design taste.** `fs` (read/write, §2) had been in this document for a
  long time; on 2026-08-04 it was found emitted by ONE engine of four. One had no such field, one emitted
  none, and one carried it in its wire model with a hardcoded empty value — never populated, which is worse
  than absent because a present-but-always-empty field asserts "kind undetermined" on every function forever
  while wearing a schema that implies support. Nobody had noticed for as long as the field existed, because
  §2's omit-rather-than-guess rule made every individual omission defensible. **A field whose absence is
  always excusable is a field nobody checks.**

  Note what a MUST on the field would NOT have fixed: a hardcoded empty value satisfies a mandatory field
  and declares nothing. Only a positive declaration separates "I compute this and could not determine it"
  from "I do not compute this" — the same construction as `extensions`, and the same one ⟨0.26⟩ used for the
  sidecar key set.

  ⟨0.27⟩ also closes three unpinned cells in the **verdict document**, found by one cross-engine review
  and pinned by conformance **PART 36**: the **composed document** (`refused` and `violations` are
  mutually exclusive; the refusal beside a dominating violation travels as `unevaluated`, one entry per
  rule of the refused policy — §3.1, measured as FOUR spellings across four engines); the **stream sink**
  (`--gate-json -` writes the fail-closed document to stdout on EVERY exit-2 cause — §3.1, measured
  answered-or-empty by CAUSE); and the **`zeroMatch` verdict key** (§3.1's zero-match list reaches the
  machine channel, both routes, five engines — it was stderr-only in all five).

- **0.26 (all code engines declare `0.26`; conformance-pinned four-way)** — a **tier-1 additive** rung:
  **§2.2, the hierarchy sidecar's KEY SET is its MANIFEST.** A producer MUST emit a key for every type it
  indexed (`[]` included); a consumer MUST treat a type ABSENT from a present sidecar as UNANSWERABLE and
  disclose rather than drop. Adds the optional `@unanalyzed` diagnostic key.

  Absence carried two meanings and the format could not tell them apart — a supertypeless type and a type
  the pass never looked at were spelled identically — so `isSubtypeOf` over an unindexed type answered
  `false`, a positive claim about a type nobody analysed. MEASURED with only the sidecar doctored on a real
  scan: removing ONE entry dropped a reacher from `callers --include-unknown`, while removing the sidecar
  ENTIRELY left it correct. **A partial sidecar answered worse than an absent one**, identically in java and
  ts — which is evidence about the FORMAT, since neither engine had a third answer available.

  Engine work in all four. Pinned by conformance **PART 30** (P6, sidecar manifest fidelity: degrading a
  sidecar may only WIDEN a disclosure, and every type an engine walked carries a key), which also closes the
  self-differential family's structural gap — P2 and P3 degrade the chained dep REPORT, and nothing
  degraded a SIDECAR.

- **0.25 (conformance-pinned four-way)** — a **correction** rung, no engine work required at the contract
  level: **§2 chaining rule 1 is REVERSED.** Two dep-report entries colliding on one join key are UNIONED,
  never withdrawn and never picked between; trust levels do not rank. Dropping the key turned a disclosed
  ambiguity into silence, which is the cardinal sin wearing a tidy-looking rule.

- **0.24 (all code engines declare `0.24`; conformance-pinned four-way)** — a **tier-1** rung, and the
  first one whose primary change can **turn a currently-green gate RED**. Read the verdict note below
  before adopting.

  Pinned by conformance **PART 27** (the rung's behaviour — CONTRIBUTES, the `viaDispatchOn` literal, the
  dot-free frontier arm, the sidecar triple, `--class`, `gate --report`, locale), **PART 10** (the
  five-kind vocabulary, with a fabricated-kind negative control), and **PART 23** (the model). PART 27's
  fixtures are hand-written reports, so the classifier is out of the loop and a divergence there is a
  CONSUMER defect — which is where every defect this rung fixed actually lived.

  ⟨0.24⟩ **`gate --report` was pinned 2-of-4 for part of this rung's life, and this entry said "four-way"
  without saying so.** Recorded rather than erased, because the correction was the point: PART 27 prints
  `NOSURF` for an engine lacking a surface, and NOSURF does not FAIL — so the suite was green while a clause
  §3.1 calls a MUST held in two engines. It is now genuinely four-way (rust `93ed0a1`, ts `c2b8ce4`), R6
  green on all twelve cells.
  **And building it in the remaining two immediately justified the verb.** candor-rust's equivalence run
  found a defect **in its own gate** that no end-to-end test could have isolated: a `#[cfg(unix)]` function
  beside its `#[cfg(not(unix))]` twin put one qualified name in the gate's function list **twice**, so the
  gate emitted two byte-identical violation records and an inflated count — **15 of the first 90 rows.** The
  report route cannot reproduce it, because a report is keyed by name; that asymmetry is what surfaced it.
  This is exactly what the clause promised — a defect in the GATE and a defect in the CLASSIFIER were
  previously indistinguishable — and it was found the first time the two routes were compared.

  Three self-differential properties landed alongside it and are not part of the contract but are how it
  was checked: **PART 24** split-invariance, **PART 25** chain idempotence, **PART 26** trust monotonicity.
  Each compares an engine with ITSELF across two configurations, so common-mode failure — four engines
  implementing one wrong idea — is excluded by construction rather than by argument.

  **Primary: §6.2's reason-class projection CONTRIBUTES `unresolved` rather than defaulting to it.** The old
  rule keyed on ABSENCE — "a function whose `Unknown` carries no recorded reason *is treated as*
  `unresolved`" — which fires only when the class set is *empty*, so acquiring a *second*, classifiable
  reason **removed** the default. That is a counterexample to the monotone-denial corollary the formal model
  proves (`reference/policy_model.py`, Lemma 2: `Reject` is upward-closed, so no signature can be *relaxed*
  by learning more about it). Measured: a function calling one reasonless dep was rejected under
  `deny E Unknown[unresolved]`, one calling a correctly-reasoned dep was not, and **one calling BOTH was
  not**. `CONTRIBUTES` keeps the fail-closed intent — an unclassifiable hole still matches a narrowed
  filter — and restores monotonicity.

  **VERDICT IMPACT — MEASURED, and it is sharply conditional.** The new rule matches a strict superset, so a
  `deny E Unknown[<class>]` gate can go **exit 0 → exit 1** on unchanged code. That is the *correct* verdict
  (the old pass was the silent relaxation Lemma 2 forbids) but it is a real break, and re-baselining a report
  does not fix it. The numbers, old vs new over one identical scan on the JVM engine, two real targets:

  | dependency reports | class sets changed | `[unresolved]` verdict flips |
  |---|---|---|
  | **trusted** | 0 / 141 and 0 / 211 | **0** |
  | **stale** (§2.1 distrusted) | 130 / 145 and 311 / 311 | **52** and **2** |

  **52 of 145 is 36% of one target — a large break — and it is reachable ONLY through the dependency
  boundary.** With trusted reports nothing moves at all. That is not a coincidence: an engine records a
  reason beside every `Unknown` it raises itself, so the only route to a reasonless one is a report it did
  not produce — a §2.1 distrusted one whose effects were downgraded wholesale, or an entry whose `Unknown`
  neither its own tags nor its published `calls` chain accounts for. An adopter on trusted reports sees no
  change; an adopter consuming reports this build cannot verify sees the gate start telling the truth about
  them. Engines SHOULD name the new matches in the disclosure rather than let a build fail unexplained.

  **The control this rung is easiest to fake.** The naive form — contribute `unresolved` whenever an
  `Unknown` is present, without asking whether it is already accounted for — is indistinguishable from the
  correct rule *on a stale-report fixture*, because under a stale report nothing is accounted for. It must
  therefore be separated by a **fresh** dependency whose `Unknown` IS explained, once via its own tag and
  once via a `calls` edge. Measured on the same two targets, the naive form flips **96/141 and 211/211**
  with fresh reports where the correct rule flips **none** — and on the Swift engine, whose default is
  unreachable, it marks **435** functions where the legitimate count is **0**.

  **Secondary, additive: `ambiguous:` is a fifth §4 kind.** §6.2 has always projected `ambiguous:*` to
  `dispatch`, so a CONSUMER classified it correctly while a PRODUCER emitting it was non-conforming — an
  asymmetry that survives because a consumer never complains about a token it can classify. Removing it was
  measured and rejected (8710 of 19607 `Unknown`-bearing entries on candor-rust;
  `deny E Unknown[dispatch]` would go from 58 of 200 crates to **0 of 200** — a deletion of the verb, not a
  narrowing). It also names what no other kind can: no owner type was ever formed, and no function value is
  involved.

  **Also, §3.1 — an UNANSWERABLE frontier condition is disclosed, never scored as a failed one.** Three
  inputs now collapse to the same answer, over-list rather than drop: a **dot-free** `dispatch:` detail (no
  owner could be formed), and an **empty or unparseable** §2.2 hierarchy sidecar. All three were silently
  dropping entries from `possibleViaUnknownDispatch`, which a consumer reads as "nothing may reach the
  target through an unresolved dispatch" — about calls the engine had explicitly charged `Unknown`. The
  clause additionally pins the **mixed source** (one entry, `viaDispatchOn` = the sorted, deduplicated,
  comma-joined union) and names the **collation** (Unicode code point ≡ UTF-8 byte order; UTF-16-natural
  comparators must compare explicitly). This half is a **three**-surface query — the Swift engine ships no
  `callers` verb, being the producer that writes the sidecar *for* the other engines.

  **Also: §3.1 `gate --report <locator> --policy <file>`** — apply a policy to an EXISTING report with no
  scan. Closes the reason this rung's own defect was hard to localise: the gate had never been reachable as
  a function of a GIVEN signature, so a defect in the gate and a defect in the classifier were
  indistinguishable from any test. It is also the supply-chain verb. It carries a MUST NOT (no re-deriving,
  no back-filling an absent entry from a sidecar or chained dep), a byte-level equivalence obligation
  against `scan --policy`, and an **answerability** rule: `forbid`, `allow`, and a class-scoped `deny`
  whose scoping datum is an absent optional field MUST be refused with exit 2, never evaluated — all three
  measured as fail-open otherwise, the third as a live `deny Net[unknown-host]` → exit 0.

  Two corrections to this document ride the rung, both recorded because of how they survived. §3.1 asserted
  *"the Rust scanner emits no `dispatch:`"* and therefore returns an empty frontier "by language model, not
  a gap" — the scanner emits it for every dispatch reason in a 1062-report census, so **the specification
  had promoted the bug's symptom to an invariant**, in the one place an auditor would look to confirm it was
  not a bug. And the absence-keyed §6.2 rule was **in this file**, not invented by the implementations:
  every engine was conforming, and the divergence was between the *model* and the *contract* — a class of
  defect no amount of four-way implementation agreement can surface.

- **0.23 (all code engines declare `0.23`; conformance-pinned four-way)** — a **tier-1 additive** rung: the
  **cross-package interface-dispatch** rung (§2, `WORKSPACE-CHAINING-DESIGN.md`). Adds the optional
  **`interfaceUnion`** report entry — a synthetic `pkg#Iface.method` union over a package's local implementers
  (interfaces/protocols/traits) — emitted **gated** behind `CANDOR_WORKSPACE_CHAIN`, so a CHAINED consumer's
  cross-package interface/protocol/trait dispatch resolves to the implementation's effect instead of reading
  silent-pure; plus the **`--workspace`/`--deps`** auto-discovery convention (scan a monorepo's local deps into
  `.candor/deps/` and chain them, transitively to a fixpoint). Conformance **PART 18** pins it **four-way**
  (candor-java + candor-scan + candor-ts + candor-swift). Because emission is gated, a **default report is
  byte-identical** — a 0.22 consumer reads a 0.23 report unaffected. The empirical finding: the silent-pure
  cross-package dispatch hole existed in every source engine, each via a different resolution path.
  candor-java was recorded N/A here at first, on the grounds that "whole-classpath bytecode resolves
  cross-module dispatch natively" — true of an UNCHAINED whole-classpath scan and false of a chained one,
  where the implementer sits in the other tree. Its CONSUMER needed no change at all (it keys entries by
  `owner.name+desc`, exactly the key an INVOKEINTERFACE site forms, so a union entry lands where the join
  already looks); only the producer was missing, and it joined 2026-07-26.

  The rung also carries the optional **`typeSurface`** object (§2, `DEP-RECEIVER-TYPING-DESIGN.md`) —
  `returns: {"<pkg>#<fn qual>": "<pkg>#<type qual>"}`, both ends fully qualified — so a receiver bound from
  a dependency FACTORY can be typed at all. A pure factory is absent from its own report, so its return
  type is unrecoverable from the entries; without it the receiver stays untyped and every later method call
  drops. Led by **candor-scan**, optional elsewhere; an empty surface omits the field, so a default report
  is byte-identical and a 0.22 consumer is unaffected. The companion `implements` member was designed and
  then dropped — `interfaceUnion` already publishes the implementer set it would have carried.

- **0.22 (all code engines declare `0.22`; conformance-pinned)** — a **tier-2** rung: the **`verify` oracle**,
  candor's dynamic honesty check. `candor verify` runs the analyzed program and asserts, per executed function,
  that observed runtime effects are contained in the report's declared set up to `Unknown` — `observed(f) ⊆
  inferred(f) ∪ {Unknown}` — falsifying a silent under-report (the cardinal sin) at runtime. It ships with
  mechanism-independent capture arms (a language-level preload, a JVM `-javaagent`, a syscall parser) and fails
  **closed** (exit 2) when runtime attribution is incomplete rather than certifying a clean pass. The oracle is
  **per-engine** (not conformance-differential — like the other tool surfaces). The rung also folds in two
  corpus-found soundness fixes (a JVM bridge-method attribution false-positive; a Node effect-polymorphism
  boundary — `process.env` aliased through a parameter) and the opt-in **unknown-ratchet** gate flag. The report
  and verdict **schema are unchanged from 0.21** — a 0.21 consumer reads a 0.22 report/verdict unaffected.

- **0.21 (all code engines declare `0.21`; conformance-pinned)** — a **tier-1 additive** rung: the
  **completeness manifest** (COMPLETENESS-MANIFEST-DESIGN.md). The report envelope gains **`analyzed: {count,
  digest}`** — the analyzed universe (effectful + pure = the §2.2 node set), so a bare-envelope consumer
  computes `analyzed.count − |functions|` = the pure count and reads a unit as *effectful* / *provably-pure*
  (a §2.2 node absent from `functions`) / *never-seen* (in neither); the digest is an opaque within-engine-
  stable fingerprint (FNV-1a-64, one algorithm four-way; compare same-engine only). The envelope + gate
  verdict gain **`unanalyzed: [{path, reason}]`** — the target's own source candor could not read/parse,
  disclosed on stderr before but INVISIBLE to a machine reading the JSON. **The sharp fix (§3.3.1):** a
  configured gate over incompletely-analyzed source now FAILS CLOSED — exit 2 with a machine-legible
  `{ok:false, incomplete:true, unanalyzed:[…], analyzed:{count}}` verdict, instead of a green report (or an
  exit-2 with no verdict) a CI/agent read as an all-clear over code candor never saw. A real violation still
  exits 1; a bare scan discloses `unanalyzed` and stays exit 0. Additive (a pre-0.21 report/verdict is
  byte-compatible bar the fields); Gap 3 (a truly-isolated pure unit is a §2.2 node) is a conformance pin.
  Pinned four-way in `gen_completeness.py`. See COMPLETENESS-MANIFEST-DESIGN.md.
- **0.20 (all code engines declare `0.20`; conformance-pinned)** — an **additive** rung. Primary: the
  **`Net` destination-class**. A per-function **`netClass`** report field (§2) refines the `Net` `hosts` surface
  into `known-telemetry` (a curated four-way-verbatim `TELEMETRY_HOSTS` set) / `known-partner` (a config
  `net-partner <host>` OR a model host) / `unknown-host` (the fail-closed default — a masked/runtime host, or a
  host on neither list). A `deny` may narrow its `Net` part to those classes — **`deny Net[unknown-host]`** — so
  the security use case *"egress only to known destinations"* is gate-able where bare `deny Net` (all
  destinations, unchanged) is all-or-nothing. The class propagates transitively like the effect; the verdict
  carries `netClass` on a `Net` denial. Fail-closed by construction: an asserted-safe class comes only from an
  exact host-literal match, so an exfiltration `Net` can never slip a `deny Net[unknown-host]`. Pinned four-way
  in conformance PART 4 (`netClasses` parse) + the Net destination-class differential (`gen_netclass.py` — the
  fail-closed gate posture); see `NET-DESTINATION-CLASS-DESIGN.md`. Also TIER-2: a reason-class **query
  surface** — `blindspots --stats` (the §4 reason-class distribution) + `blindspots --class`/`unverified
  --class` (filter by class), sizing and drilling into the blind-spot cost the 0.19 gate acts on. A pre-0.20
  report/policy/consumer is unaffected (the field, the bracket syntax, and the new flags are additive).
- **0.19 (all code engines declare `0.19`; conformance-pinned)** — a **tool-surface** rung (no report-schema
  change; a 0.18 report is byte-identical under 0.19). TIER-2 required: **reason-scoped `Unknown` policies**
  (§6.2). A `deny` may narrow its `Unknown` part to a fixed cross-engine reason-class vocabulary —
  `deny E Unknown[reflect,dispatch,indirect,native,unresolved,setup]` — projecting the §4 `unknownWhy` reasons;
  with the built-in `dynamic` alias (every genuine class, excl. `setup`), `*`, and config-defined
  `unknown-alias <name> = <class…>` names. Bare `deny E Unknown` is **unchanged** (`Unknown[*]`, fires on any —
  soundness-by-default), an unrecognized/unclassified reason maps to `unresolved` (conservative), and the
  reason class propagates transitively along the call graph exactly as the `Unknown` effect does. An
  AS-EFF-006 `--gate-json` verdict whose `effects` include `Unknown` carries a new **`reasonClass`** array (all
  classes on the fn). A pre-0.19 policy and verdict-consumer are unaffected (the bracket syntax + field are
  additive). Pinned four-way in conformance PART 4 (parse + `unknownClasses` + config alias) and PART 12 (the
  `reasonClass` structural invariant). See `REASON-SCOPED-UNKNOWN-DESIGN.md`.
- **0.18 (code engines declared `0.18`; conformance-pinned)** — a **pinned-tool-surface** rung (no
  report-schema or verdict change; a 0.17 report and gate verdict are byte-identical under 0.18). Two TIER-2
  required additions, both enforcing the §4 "never a false all-clear" rule at the tool surface: **(1) the
  `--strict` advisory-verb CI gate** (§3.3.1) — `fix-gate`, `gains`, and `unverified` are advisory (exit 0),
  and `--strict` makes each a CI gate (exit 1 while a finding remains: an outstanding crossing, ANY gained
  effect, an unverified-purity hole); a typo'd or not-applicable flag is an exit-2 error (never a silent
  swallow that disarms a gate), and `gains` has no `--policy` — passing one is an exit-2 error naming the
  scan-time `deny <E> gained` gate (`AS-EFF-005`). **(2) the surface/`tour` mostly-Unknown disclosure** — over
  a graph where ≥⅓ of effectful functions are `Unknown` (unresolved calls whose transitive effects are
  unanalyzed), the scan opener and `tour` MUST NOT print the bare "nothing hidden"; they qualify (naming the
  Unknown count + `blindspots`), and `tour --json` carries an additive `unknown: {count, total}` field rather
  than a bare `{"reaches": []}` a machine reads as clean. Pinned four-way by conformance PARTs 4l, 5b, 12b, 12c.
- **0.17 (all code engines declared `0.17`; conformance-pinned)** — **query target validation** (§3.1, a
  TIER-2 required addition enforcing the §4 "never a false all-clear" rule at the query surface): `where
  <Effect>` and `callers <fn>` now **fail loud (exit 2)** on an unknown/typo'd effect or a nonexistent
  function, instead of returning an empty result at exit 0 (which read as an authoritative "nothing performs
  it" / "nothing calls it" for a question that was never validly posed). A KNOWN effect that is merely absent
  stays a legitimate 0-result; an unknown effect NAME present in the report (a spec extension) is still
  accepted — so the error fires only when the name is neither known nor present. `callers` stays exit-0 when
  only the effect-relevant fallback graph is available (no callgraph sidecar), where a miss is inconclusive
  rather than proof of absence. Conformance PART 17 pins the loud-failure four-way. Engine-side this release
  also carries recall + output-uniformity + remediation-text fixes (candor-ts HTTP-client import recall,
  prose-at-a-TTY query output, the empty-scope remedy label) — none of which change the report or gate
  contract, so they ride the same floor.
- **0.16 (all code engines declare `0.16`; conformance-pinned)** — the **callgraph-aware baseline guard**
  (§7 item 5): AS-EFF-005 existence keyed on the baseline callgraph sidecar when present, so a formerly-
  pure function turning effectful is a GAIN violation rather than exempt "new code" (the `gains` `origin`
  existence rule applied to the scan-time ratchet); sidecar absent → report-only degradation, sidecar
  corrupt → fail closed. The ratchet fires only on gaining a REAL boundary effect; an `Unknown`-only gain
  (the §4 trust marker, not an effect) is disclosed as advisory, exit unchanged — on real dependency
  bumps an Unknown-only gain is dominated by resolution noise, so failing on it would break CI on
  innocuous updates. Conformance PART 15b (pure→effectful) + PART 15c (Unknown-only advisory) pin it
  four-way.
- **0.15 (all code engines declare `0.15`; conformance-pinned)** — additive, wire-compatible with 0.14: the
  **`coverage` envelope field** (§2) — the κ-coverage ledger as data (`{"uncovered":[{"name","calls"}]}`,
  omitted when empty), so "what the scan couldn't see" travels with the report; the per-function
  **`invisible`** field formalized (§2 — the ledger attributed per fn; engines already emitted it);
  and **verb conditionality** (§3.1/§3.3) — a report-consuming verb whose verdict could change under
  uncovered reach re-discloses coverage in its output, verdict-preserving (`privacy-manifest` gains a
  conditional marker, `--gate-json` an advisory note, `gains` the current ledger + delta). Motivated by
  the wikipedia-ios privacy-manifest false-confidence find (SOUNDNESS-LOG 2026-07-15); design in
  [COVERAGE-DESIGN.md](COVERAGE-DESIGN.md). Conformance **PART 4s** pins it four-way.
- **0.14 (all code engines declare `0.14`; conformance-pinned)** — additive, wire-compatible with 0.13.
  The **top-level / initializer unit**: a module whose top-level executable code performs an effect is
  attributed to an INITIALIZER unit (`unitKind:"initializer"`), never a false-"pure" empty report. A
  module-load-time model call (top-level `await fetch("…api.openai.com…")`, an IIFE, a bare
  `readFileSync`, a JVM static initializer) was SILENTLY DROPPED by candor-ts and candor-swift (a
  `deny Llm`/`deny Net`/`deny Fs` gate passed it — the cardinal sin); candor-java's `<clinit>` was
  already sound (the reference), rust is N/A (no top-level executable code). Each engine's unit NAME
  differs (java `<clinit>`, ts `<module>`, swift `<main>`); the effect model is identical. Conformance
  **PART 4p** pins it. Report bytes change where a previously-empty top-level module now carries a unit.
- **0.13 (all code engines declare `0.13`; conformance-pinned)** — additive, wire- and invocation-compatible
  with 0.12: the **`Llm` effect** (§1) — a machine-learning model-provider call, refining `Net` the way
  `Db` does (a model-SDK surface + a known-model-host literal refinement; an unknown host/SDK stays bare
  `Net`). A boundary effect (§6.1), high salience in the §3.1 surprising-reach surface, and the sharpest
  form of the `gains`/`origin` alarm ("a dependency bump added an `Llm` call"). Tier-1 additive: a
  pre-⟨0.13⟩ consumer tolerates the new effect name and a pre-⟨0.13⟩ policy never names it. The reference
  engine declares `0.13` ahead of the floor; the floor rises to 0.13 when the last code engine implements
  it, pinned by the conformance host-literal + SDK-surface differential.
- **0.12 (all code engines declare `0.12`; conformance-pinned)** — additive, wire- and invocation-compatible with 0.11:
  the **`gains` `origin` field** (§3.1) — each `byFunction` entry names whether the gaining fn existed
  at the baseline (`existing`, the supply-chain attack signal: shipped pure, now performs the effect),
  is new (`new`, a feature), or is undecidable (`unknown`, disclosed — the baseline callgraph is absent or PARTIAL: a corrupt sidecar must not downgrade the attack signal to "new").
  Existence keys on the baseline callgraph sidecar because reports omit pure functions. Promoted from
  the candor-gains prototype's driver into the open query; human/TSV output unchanged.
- **0.11 (all code engines declare `0.11`; conformance-pinned)** — additive, wire- and invocation-compatible with 0.10:
  another **tier-2 (pinned-tool-surface) rung**, no report-schema or verdict change. It promotes the
  **§3.1 surprising-reach surface** into the pinned tools: the scan-time opener, the **`tour [<N>]`**
  verb (+ its JSON shape), `path`'s human-readable default, the shared deterministic ranking heuristic
  (salience floor: `Clock`/`Log`/`Rand` never surface; test contexts excluded by module segment, never
  by leaf name), and the "nothing hidden" fallback over a manufactured surprise. Also ⟨0.11⟩: **a
  located report yielding no trustworthy functions fails loudly** (found-but-corrupt is never an empty
  all-clear — syntactic and semantic corruption alike, while a well-formed `functions: []` stays a
  valid pure report), and the coverage-ledger marker de-jargoned (`classifier doesn't cover`).
  Conformance pins it four-way: PARTs 4f (opener), 4g (tour + the plural-`packages` header label),
  4h (tour 0 → exit 2; sidecar-loss fallback), 4i (test exclusion), 4j (salience floor),
  4k (corrupt-report loudness).
- **0.10 (all code engines declare `0.10`; conformance-pinned)** — additive, wire- and
  invocation-compatible with 0.9: another **tier-2 (pinned-tool-surface) rung**. No report-schema or verdict
  change. It promotes the
  **§3.3.1 canonical query grammar** into the pinned surface: for every §3.1 query verb an engine exposes,
  one invocation shape across all languages — the report **discovered** from `.candor/` (walk-up, §3.4) with
  a `--report <locator>` override, `--json` selecting JSON, `--policy <file>` a flag (never a positional).
  The pre-0.10 positional forms (a leading report, the `0|1` JSON sentinel, a positional policy) stay
  accepted as **deprecated aliases** with a stderr note, removed no earlier than the next major — so a 0.9
  invocation still runs. Conformance **PART 17** pins the grammar four-way (discovery ≡ explicit `--report`,
  cross-engine agreement, `--json` selection, `--policy`-as-flag). Rationale and per-engine impact in
  `CLI-GRAMMAR-DESIGN.md`.
- **0.9 (all code engines declare `0.9`; conformance-pinned)** —
  additive, wire-compatible with 0.8: a **tier-2 (pinned-tool-surface) rung** (see *[Conformance
  tiers](#conformance-tiers)*). No report-schema, effect-vocabulary, or verdict change — a 0.8 report and a
  0.8 `--gate-json` verdict are byte-identical under 0.9. What the rung promotes into the pinned §3.1/§3.3
  surface is the **remedial tool loop**, the inverse of the pre-edit `whatif`:
  - §3.1/§3.3 **`fix` / `fix-gate`** — given a boundary crossing, compute the *fix*: the direct effect
    site, the pure span that threads the value through the forbidden layer, and the **hoist frontier** (the
    nearest allowed-layer caller the effect can move to), plus `hoistHigher` (allowed ancestors that also
    route it) and a `cleanHoist=false` **sandwiched** flag when a forbidden function calls back into the
    frontier. `fix-gate` is the gate-shaped form. Reference impl: candor-query, then candor-java and
    candor-ts (candor-swift computes the plan; its editor code-action rides the pending whatif action).
    Conformance PART 12b pins the four-way remedy (leaf-normalized).
  - §3.1/§3.3 **`unverified`** — the provable-purity disclosure: a `pure`/`deny E` layer PASSES a function
    that is `Unknown`, but that pass is *unverified* (the Unknown could hide the very effect the rule
    forbids — the classic fn/closure-injected port). `unverified` names each such hole and the
    `deny <E> Unknown <scope>` upgrade that makes the layer provably clean. Advisory (exit 0); `--strict` →
    exit 1 so CI can require provable purity. All four engines; conformance PART 12c.
  - §3.3 the **gate's provable-purity auto-disclosure** — a `--policy` scan emits the `unverified` holes
    automatically as an advisory stderr note after the verdict, so an author learns their `pure` layer
    isn't *provably* pure without knowing the subcommand exists. **Verdict-preserving**: a note, never a
    violation — the exit code, the gate verdict, and `--gate-json` are untouched (this is why the rung is
    tier-2, not tier-1). All four engines share ONE hole predicate with `unverified`, so the scan-path and
    query-path disclosures cannot drift; conformance PART 12d pins their agreement.
  - **Conformance tiering recorded** — each conformance PART is now tagged tier-1 (interop floor) or
    tier-2 (tool-surface parity), making the next version trigger unambiguous (see *Conformance tiers*).
  - The candor-agents domain engine (§4) rides the rung behind the code engines, declaring `0.9`.
- **0.8 (all four engines declare `0.8`; conformance-pinned)** —
  additive, wire-compatible with 0.7. The first version to ride the **ladder** (see *Versioning policy*): a
  minor rung led by the reference engine (candor-java), then implemented by candor-scan, candor-ts and
  candor-swift in turn — the floor has now risen to `0.8`, its cross-engine agreement pinned by the
  conformance gate-verdict differential (PART 12).
  - §3.3 the **structured gate verdict** — `--gate-json <file>` emits `{ spec, ok, violations:[{rule, fn,
    effects, detail?}] }`, the machine analog of the `AS-EFF` console lines, from the same check that sets the exit
    code (so a consumer can never see a verdict that disagrees with the gate). Conformance pins `ok` + the
    `{rule, fn, effects}` set; `detail` is engine-natural. Powers the PR-native SARIF surface
    (`candor/integrations/github`): each `fn` joins to its `loc`/effects in the §2 report.
  - Reference impl: candor-java (`--gate-json`, captured at the single diagnostic sink); then candor-scan,
    candor-ts and candor-swift in turn. All four declare `0.8`; the conformance gate-verdict differential
    (PART 12) pins their agreement on the shared fixtures. The candor-agents domain engine (§4) rides the
    ladder behind them: its 0.8.0 adds `.candor/config`, `--gate-json` and the item-14 coverage ledger, declaring
    `0.8`.
  - **(amended)** §2.1 the **stale-baseline posture**: a baseline GUARD given a baseline from a
    different (or absent) producing version MUST fail closed without evaluating (the unreadable-policy
    class); comparison QUERIES disclose (warning + provenance fields) and still answer. Documentation of
    the aligned behavior all reference engines now implement; no wire change, spec string unchanged.
  - **(amended)** §3.4 the **`.candor/config` configuration file** — the checked-in alternative to the
    `CANDOR_*` env wiring (shared key vocabulary; target-anchored discovery; precedence flag → env →
    config → default; fail-closed when configured-but-unusable; unknown keys warn). Configuration, not
    the wire contract: additive within 0.8, the spec string is unchanged (the 0.3/0.4-amendment
    precedent); all four engines implement it, pinned by the conformance config differential (PART 13).
  - **(amended, 2026-07-09)** §3.4 two clarifications from the whole-family review: a **relative path
    value resolves against the config's home directory** (the directory containing `.candor/` — never
    the CWD; the config travels with the code), and a recognized-but-unimplemented key **SHOULD be
    disclosed** (one stderr line), so a checked-in gate key never reads as silently active in an
    engine that doesn't drive that mode.
  - **(amended, 2026-07-09)** §6 + SEMANTICS §6: the **AS-EFF-008 text reconciled to the
    machine-checked contract** — the rule fails closed on an uncertifiable (masked/opaque) literal
    surface, as every engine has implemented and the conformance masking + gate-verdict differentials
    have pinned since the 0.5.15-era gate-evasion hardening; the prior prose wrongly scoped the code to
    visible violations only. Also recorded: the `gains` query shape in §3.1 (shipped and
    conformance-pinned since the ⟨0.5⟩ query parts; §2.1/§5.1 references now resolve), SEMANTICS'
    AS-EFF-010 predicate row, and the §2.1 version-trust precondition on the baseline-reading
    predicates. Documentation catch-up throughout: no wire change, no behavior change anywhere.
- **0.7 (released — engines declare `0.7`; untagged — the tag-the-floor rule postdates this rung, so
  its floor rise is recorded here and by the engine releases)** —
  additive, wire-compatible with 0.6; all four engines implement it and two conformance differentials pin
  it (see `proposals/unknownwhy-vocabulary.md`, `proposals/0.7-unknown-dispatch-frontier.md`):
  - §4 the **canonical `unknownWhy` vocabulary** — four kinds `reflect:`/`native:`/`dispatch:`/`callback:`,
    superseding the ~12 divergent per-engine prefixes; `dispatch:` detail normative as `owner.member` (the
    dividing line: `dispatch:` is an unresolved dispatch with a resolvable owner type+member; every
    owner-less unresolved invocation is `callback:`). Conformance `[10]` pins the prefix set + dispatch shape.
  - §2.2 a compact **type-hierarchy sidecar** (`<stem>.hierarchy.json`, type → direct supertypes/interfaces)
    — lets a query resolve overrides without storing the candidate edges bounded-CHA drops.
  - §3.1 the **`callers --include-unknown`** modifier — discloses the *unresolved-dispatch frontier*
    (`possibleViaUnknownDispatch`): functions that reach the target only through an unresolved `dispatch:`,
    resolved precisely against the hierarchy (a confirmed reacher that overrides the dispatched member). A
    disclosed lower-bound, never asserted; the dispatch-frontier conformance differential pins cross-engine
    agreement. A language with no class/protocol dispatch (the Rust scanner) emits no `dispatch:`, so its
    frontier is empty by construction.
  - §3.3 the **required command-line surface** — every engine's scanner takes `--policy` (honouring
    `CANDOR_POLICY`), `--json` to stdout, `--version`/`-V` carrying the spec version, and `--help`/`-h`,
    with flag names + help wording kept consistent across engines. Codifies what the four engines now
    expose; no wire change (the §2 envelope is untouched), so engines keep declaring `0.7`.
- **0.6 (released — engines declare `0.6`; untagged, as 0.7)** —
  additive, wire-compatible with 0.5; all four engines implement it and a conformance differential pins it:
  - §3.1 the **`blindspots`** read-only query — the Unknown SOURCES (the calls genuinely unresolvable),
    ranked by how many functions transitively inherit `Unknown` through each: the actionable inverse of a
    widely-propagated `Unknown`. A new query shape = a minor bump (this changelog's own rule).
  - §4 **`unknownWhy` is now REQUIRED on a direct `Unknown` source** (still absent on purely-inherited
    `Unknown`), so `blindspots` separates the few root causes from the smear identically across engines. A
    presence tightening on an existing field; a 0.5 consumer that ignores `unknownWhy` is unaffected.
  - Rolled out across all four engines (candor-java reference first, then candor-query/rust, candor-ts,
    and candor-swift reports queried via candor-query), with a conformance differential pinning the shape —
    then the header + engine declarations moved to `0.6` together (the same discipline the ⟨0.5⟩ parts followed).
- **0.5 (released — tag `v0.5`; engines declare `0.5`)** — the ⟨0.5⟩ parts (units/`unitKind` §2, Exec
  subprocess-boundary refinement §4, the effect manifest §5.1, gate→guard §6.2, and the §3.1 read-only
  query shapes), plus two cross-engine consistency rules a divergence review pinned: the §6.2 policy
  lexer splits on **ASCII whitespace only** (a Unicode space is part of its token, so a malformed rule is
  dropped uniformly — never enforced by one engine and silently dropped by another), and `unknownWhy`
  adds the `callback:` origin (a higher-order call's unresolved target, the improvable class with
  `dispatch:`). All wire-compatible with 0.4 (additive fields, narrowing refinements, a lexer
  clarification). Detail of the ⟨0.5⟩ parts:
  - the **units** generalization: a report entry describes a *unit* (the smallest body effects are
    attributed to), of which a function is the common case; the new OPTIONAL `unitKind` field (§2)
    names the non-function kinds (initializer / accessor / export / agent / command / skill / cron /
    session / hooks — an open set, informative only). A new optional field is the changelog's own
    definition of a minor bump, hence 0.5 rather than a 0.4 amendment. Wire-compatible: absent =
    "function", and a 0.4 consumer tolerates the field under §2 forward compatibility.
  - the **subprocess-boundary refinement of `Exec`** (§4): an engine MAY classify a literal,
    statically-known sub-command head to add the head's effects and bound the capability cliff's
    transitive reach (a spawned candor engine → `Fs`/`Env`, supplied by §7 item 12). Posture-only —
    the head table is curated engine data, never normative; an unknown/dynamic head keeps the
    cliff; `Exec` is never dropped. The *head* is argv[0] (the program), never a trailing literal
    **argument** of a dynamically-named program — classifying an argument would fabricate its effect.
    It only narrows an upper bound, so a 0.4 consumer is unaffected.
  - the **effect manifest** (§5.1): an opaque dependency MAY declare its effect surface
    (`candorEffects`), read as the declared-not-verified tier (the cap-type trust extended to a whole
    package), killing its `Unknown`; a `diff`/`gains` between two releases of a declaration surfaces a
    gained capability — the supply-chain alarm. Also pins the §3.1 `reachable`/`path`/`impact` query
    shapes (with `impact`'s `affected` blast-radius list) so the agent-facing shapes agree across engines.
  - **gate → guard** (§6.2): a `deny` rule MAY compile to a *runtime guard* enforcing the same
    boundary (a sandbox profile for a process; the harness's `permissions.deny` for an agent fleet) —
    the dual of analysis, which reads the same enforcement surface. SHOULD-level; honest about the
    cliff it cannot close, and about per-target scopes a host boundary cannot express.
  - **§4 epistemic caveat (clarification, not a contract change)**: §4 now states explicitly that the
    trust rule is a *best-effort discipline against an undecidable property* (Rice), not a completeness
    guarantee — the contract a consumer relies on is **disclosure** of what couldn't be resolved, not
    omniscience, with the residual tracked openly. No obligation on implementations changed; the `spec`
    string stays `0.5`.

- **0.4 (amended 2026-06-12, same day; tagged `v0.4.1`)** — additive within 0.4, wire-compatible both ways (no new
  required report field; every pre-amendment 0.4 report and policy parses unchanged), so the spec
  string stays **0.4** (the 0.3-amendment precedent):
  - §2 **one report covers one package** + the **report set** (one report per package under a
    shared prefix; consumers join across reports by `hash`, never bare `fn`). Motivated by a live
    find: a repo-root scan folding 194 fixture packages into one report cross-wired the call graph;
  - §2 the **`package` / `packages` envelope field** (SHOULD): name what the report covers, so an
    all-pure EMPTY report's coverage is readable without entry hashes;
  - §2 **forward compatibility**: consumers MUST tolerate unrecognized fields;
  - §6.2 a configured-but-**unreadable policy file MUST fail the run loudly** (distinct exit; never
    proceed gateless). Found live: a reference engine was loud on stderr but exited 0;
  - §3.1 **parsepolicy** documented (the conformance suite's grammar witness; SHOULD for enforcers);
  - §7 item 11 **the self-describing engine**: embed `AGENTS.md` in the installed artifact and
    print it under `--agents` with a version header (SHOULD); the embedded copy MUST equal the
    repo doc (a drift-gate test). Conformance Part 7 checks every present engine;
  - §7 item 12 wording: the stray "MUST analyze" inside the SHOULD list now reads under the SHOULD
    umbrella, as intended.
- **0.4 (2026-06-12)** — **wire-compatible, conformance-breaking**: no report-schema change (a 0.3
  reader parses a 0.4 report byte-for-byte; only the envelope's `spec` string moves), but four
  obligations are upgraded SHOULD → MUST, so an implementation that conformed to 0.3 may not
  conform to 0.4 until it adds them:
  - **§2.1 version-trust at the chain join** is MUST (and a MISSING producer version is as
    unverifiable as a mismatched one — downgrade to `Unknown`). The trust contract (§4) extended
    across report boundaries; the engines had measurably drifted under SHOULD.
  - **§7 item 14, the coverage ledger,** is MUST (conformance Part 4c already enforced it): the
    per-scan disclosure is the executable form of item 7's honesty obligation.
  - **`hash` emission** is MUST for every producer (any report can become a chained sibling; a
    hashless report is silently unchainable — the under-report direction).
  - **Literal surfaces** are MUST for an implementation that enforces `allow` rules (an allow gate
    over an unemitted surface fails every rule as uncertifiable — worse than no gate).
  The §7.13 soundness harness deliberately REMAINS a SHOULD: §4 is already a MUST, and the harness
  is its evidence — required of the reference engines by their own CI, recommended for all.
- **0.3 (second amendment, 2026-06-11)** — additive within 0.3, no wire change (no new report
  fields; `hash` was already §2):
  - §2 **report chaining** made normative: the CANDOR_DEPS convention, the never-guess join rule,
    stale-report distrust (restating §2.1), and the chained-coverage rule (an empty report is a
    purity claim);
  - §4 the **bounded-CHA discipline** for dispatch over local abstractions (resolve ≤12 local
    implementors, the shared bound; otherwise honest `Unknown`; external-abstraction misses must be
    documented);
  - §7 item 14: the **coverage ledger** (disclose unlisted-but-called packages per scan), pinned
    by conformance Part 4c.
- **0.3 (amended 2026-06-11)** — additive within 0.3, wire-compatible both ways (a pre-amendment 0.3
  reader parses a post-amendment report — `tables` is one more OPTIONAL literal-surface field on the
  exact pattern of `hosts`/`cmds`/`paths` — and the §6.2 grammar accepts every pre-amendment policy
  unchanged), so the spec string stays **0.3**:
  - the `tables` field (§2): the `Db` literal surface — SQL table-position identifiers (extraction
    pinned token-for-token in §2, executable in `conformance/tables/vectors.json`) plus
    declaratively-routed ORM tables;
  - `allow Db [in <scope>] <table>…` joins §6.2 (AS-EFF-008's fourth surface; case-insensitive exact
    match, `schema.*` covering);
  - §7 item 13: the adversarial soundness harness requirement (documentation of the practice every
    engine already ships — teeth verified per mechanism, the form list open, a precision twin).
- **0.3** — additive over 0.2 (wire-compatible; a 0.2 reader still parses a 0.3 report):
  - `AS-EFF-006` (policy `deny`/`pure`), `AS-EFF-007` (heuristic `risk`), `AS-EFF-008` (literal allowlists
    `allow Net`/`Exec`/`Fs`), `AS-EFF-009` (layering `forbid ->`), `AS-EFF-010` (containment ratchet);
  - report fields `calls`, `fs`, `hosts`, `cmds`, `paths`, `unknownWhy` (the per-fn Unknown-origin tag),
    `entryPoint` (the runtime-invoked reachability-root flag);
  - the `containment` mode + §6.1 (the not-a-score architecture signal);
  - the envelope's `spec` field itself (§2.1);
  - **documentation-only, no wire change** (a 0.3 report is byte-identical): §2.2 specifies the call-graph
    sidecar an implementation already emits; §3.1–3.2 specify the read-only queries and the
    pre-edit/structural tools (`whatif`, `rewire`) as cross-language-consistent SHOULDs; checklist items
    9–10 (§7) make both SHOULD-level; §6.2 fixes the **policy DSL** (the `deny`/`pure`/`allow`/`forbid`
    grammar, segment-based scope matching, per-effect literal matching) as a normative grammar so the
    gate means the same thing in every language. The report schema is unchanged, so the spec version
    stays **0.3**.
- **0.2** — the self-describing `{ candor, functions }` envelope with a provenance header (`version`,
  `toolchain`); cross-crate inheritance by `hash`; version-aware trust.
- **0.1** — the bare top-level array of function entries (still accepted by readers during migration).

## Appendix — Implementing 0.8: the checklist

The ordered build for a new engine — each step is usable on its own, each is judged by a named part of
the cross-impl conformance suite (`conformance/run.sh`), and the order matches how the existing engines
grew. Wire the engine into the suite early (see `conformance/README.md` for the env vars and the SKIP
discipline) so every step lands machine-checked.

1. **§2 — the report envelope, `hash`, and the sidecars.** The `{ candor, functions }` envelope with a
   full provenance header, one report per package, `hash` on every entry, the call-graph sidecar (and
   the type-hierarchy sidecar if the language has class/protocol dispatch). Judged by **PART 1**
   (effect sets + callgraph completeness), **PART 1c** (the §4 honesty invariant over the emitted
   report), **PART 9** (`unitKind`), and — once chaining lands — **PART 14** (`CANDOR_DEPS`
   join-inherit / stale-downgrade / empty-report coverage).
2. **§4 — the trust contract and the `unknownWhy` vocabulary.** Unresolved ⇒ `Unknown`, never
   silent-pure; the four canonical kinds with `dispatch:owner.member` normative. Judged by **PART 1c**
   and **PART 10** (vocabulary + dispatch shape), plus the dispatch-frontier differential once §3.1's
   `callers --include-unknown` exists.
3. **§3.3 — the command-line surface and the gate verdict.** `--policy` (+ `CANDOR_POLICY`), `--json`
   to stdout, `--version`/`-V` with the spec version, `--help`/`-h`, `--agents`, unknown-flag ⇒ exit 2,
   `--gate-json`. Judged by **PART 7** (`--agents`), **PART 8** (unreadable policy / unknown flag ⇒
   exit 2), **PART 12** (gate-verdict differential), and **PART 15** (the stale-baseline fail-closed
   posture, once the AS-EFF-005 baseline guard exists — the reference engine implements it and the
   family roll across ts/swift/scan is landing, after which PART 15 pins four-way).
4. **§3.4 — the `.candor/config` file.** Target-anchored discovery, flag → env → config → default
   precedence, fail-closed when configured-but-unusable, unknown keys warned. Judged by **PART 13**.
5. **§6.2 — the policy grammar and scope/literal matching.** The four rule kinds parsed exactly
   (expose `parsepolicy`), segment-based scope matching (including nested-scope boundaries), per-effect
   literal matching, fail-closed AS-EFF-008. Judged by **PART 4** (grammar), **PARTS 4b/4d/4e**
   (tables / Exec-head / Net host:port extraction), the four-way policy-matching and gate-masking
   differentials, **PART 2** (the `whatif` verdict + blast radius), **PART 3** (`rewire`), and
   **PART 16** (applied `deny Unknown`, `pure`-vs-`Unknown`, `forbid` layering).
6. **§3.1 — the read-only queries.** `show`/`where`/`callers`/`map`/`diff`/`gains`/`reachable`/`path`/
   `impact`/`blindspots`, the name-match ladder, `callers --include-unknown`. Judged by **PART 5**
   (query JSON shapes), **PART 11** (containment + the AS-EFF-010 ratchet, where implemented), and the
   dispatch-frontier differential.
7. **§7 — the coverage ledger, `--agents`, and the checklist items.** The per-scan `classifier doesn't cover`
   disclosure (item 14), the embedded agent contract (item 11), the self-gate (item 12), the soundness
   harness (item 13). Judged by **PART 4c** (the ledger differential) and **PART 7**; items 12–13 live
   in the engine's own CI.
