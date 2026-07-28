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

**Version 0.24** — all code engines declare `0.24`; the floor is conformance-pinned. How versions
move (the ladder, the floor, who may lead a rung) is stated once, in **[Versioning policy](#versioning-policy)**
below. The ⟨0.23⟩/⟨0.22⟩/⟨0.21⟩/⟨0.20⟩/⟨0.19⟩/⟨0.12⟩/⟨0.11⟩/⟨0.10⟩/⟨0.9⟩/⟨0.8⟩ markers through this document tag each surface with the rung that
introduced it; the [changelog](#8-changelog) lists every rung's contents. Each rung is additive over the last,
so an older-version consumer that ignores the newer optional fields is unaffected. **0.23 is a tier-1 additive
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
  "candor":    { "version": "<engine build id>", "toolchain": "<channel>", "spec":    "0.24" },
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
and `--gate-json`'s `coverage.modules`, which is the machine-consumer channel. The gate flip appears only
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
enumerates exactly two exit-2 causes (a broken gate CONFIG; an INCOMPLETE analysis of the target's own
code) and a judged-nothing DEPENDENCY is neither, so an engine that refuses here has minted a third cause
and **split the verb**.

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
- `"unanalyzed": [ { "path": "<file>", "reason": "<why>" } ]` — the TARGET's own source candor could NOT
  analyze (a file that failed to read/parse; a skipped unparseable class). Its units are absent NOT because
  pure but because never seen — disclosed on stderr today but INVISIBLE to a machine reading the JSON, so a
  bare report *looked* complete. **Omitted entirely when empty** (a complete scan is byte-identical to a
  pre-⟨0.21⟩ report). Distinct from `coverage` (an unmodeled *dependency*): `unanalyzed` is the target's own
  unseen source. A truly-isolated pure unit (uncalled, calling nothing) MUST still be a §2.2 call-graph node
  (empty adjacency), so its membership reads *analyzed-pure*, never *never-seen*.

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
  "declared":     [],                    // effects the signature declares it may perform (§5)
  "undeclared":   [],                    // inferred − declared (violations); empty in audit
  "overdeclared": [],                    // declared − inferred (unused declarations)
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

1. **Joins never guess.** The `hash` key must identify the target the way the *consumer's* view of
   the call names it (a `package#LocalName`, a `crate#qual` tail, a full method reference:
   per-language, but derivable from both sides). An ambiguous key (two dep functions sharing it) is
   dropped, not picked from — §4's under-report-don't-fabricate rule, applied at the join.
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
and the `encountered-*` family. It is stated here because **the engines were already drifting on it** and
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
— `analyzed.count`, `reasonClass`, `netClass` and the coverage advisory included. Measured on the reference
engine over 25 rows and two corpora (a 970-function report against 13 policies, up to 113 violations, plus
a fixture making the scoped arms non-vacuous). Anything less than byte-equality lets the two routes drift
into two gates.

⟨0.24⟩ **ANSWERABILITY: a rule whose EVIDENCE THE WIRE DOES NOT CARRY MUST BE REFUSED (exit 2), never
evaluated.** Reaching equivalence required exactly three refusals, each found by measurement and each
FAIL-OPEN if approximated instead:

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
| `--gate-json <file>` ⟨0.8⟩ | write the **structured gate verdict** (below) as JSON — the machine analog of the `AS-EFF` console lines, from the SAME check that sets the exit code. Written whenever the FLAG is given: with a gate active it re-emits that gate's verdict; with no gate configured it writes the clean verdict `{ ok: true, violations: [] }`. On **exit 2** it writes a verdict only for an INCOMPLETE analysis (the ⟨0.21⟩ machine-legible incomplete verdict, §3.3.1) — never for a broken gate config. Does not change the exit code. |
| `--version` / `-V` | print the engine build **and the candor-spec version it implements** (the §2.1 envelope `spec`), on the same or an adjacent line. |
| `--help` / `-h` | print a usage summary that lists these flags. |
| `--agents` | print the engine's **embedded** agent contract (item 11) — its `AGENTS.md`, prefixed by the canonical version header `<!-- candor-<engine> <version> · … -->` so a consumer can tell which build's contract it is reading. The embedded copy MUST equal the repo's `AGENTS.md` (§7 item 11's drift gate). |

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

- **On exit 2 (could-not-evaluate) no *ok:true/false GUESS* is written** — refined ⟨0.21⟩. There are two
  exit-2 causes and they differ: **(a) a broken gate CONFIG** (an unreadable policy, an invalid baseline, an
  unknown flag) — the gate could not be evaluated at all, so NO verdict is written (a fabricated verdict would
  be a guess); **(b) an INCOMPLETE analysis** (a source file failed to read/parse — the target's own code was
  not fully seen) — here the engine SHOULD write a machine-legible **incomplete verdict**
  `{ spec, ok: false, incomplete: true, unanalyzed: [ { path, reason } ], analyzed: { count } }` and exit 2.
  This is not a fabrication: `ok: false` is honest (the gate did not certify) and `incomplete: true` +
  `unanalyzed` say *why*, so a CI/agent reading the JSON learns the gate couldn't certify over unseen code
  rather than having to scrape stderr — closing the machine-consumer false-all-clear the manifest fixes (a
  green report over unanalyzed source). A configured gate over incompletely-analyzed code MUST fail closed
  (exit ≠ 0); a real violation (exit 1) still dominates. A bare scan with no gate does not exit 2 — it
  discloses `unanalyzed` in the report (exit 0). The `analyzed: { count }` count rides EVERY verdict (Gap 1).
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
- **`allow`**: the effect MUST be one of the four that carry a literal surface (`Net`, `Exec`, `Fs`,
  `Db`); an `allow` for any other effect is dropped with a warning. An optional `in <scope>` follows; the
  remaining tokens are the allowed values (≥1 required, else the rule is dropped).
- **`forbid`**: two scopes separated by a literal `->` token (`forbid domain -> infra`). A line missing
  the arrow or either scope is dropped.

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

So the policy side takes the same rule as the query side: **an unrecognised reason-class token is a policy
error — exit 2, the unreadable-policy posture (§6.2), naming the token and the accepted set.** A policy that
cannot be honoured as written is not silently rewritten into a different policy. The asymmetry I claimed
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
- an **unrecognized class token** in the brackets is **dropped with a warning** (the rule keeps its recognized
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
- an **unrecognized class token** in the brackets is **dropped with a warning** (the rule keeps its recognized
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
