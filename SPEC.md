# The candor specification

A candor *implementation* analyzes a codebase in one language and reports, per function, the set of
side effects it performs. This document defines what every implementation must produce, so that a
report is interchangeable across languages — for an AI agent, a human, or a CI gate.

## Contents

- [The family, named precisely](#the-family-named-precisely) · [Versioning policy](#versioning-policy)
- [1. Effects](#1-effects)
- [2. The report](#2-the-report) — [2.1 Provenance](#21-provenance-the-candor-header) · [2.2 The sidecars](#22-the-call-graph-sidecar)
- [3. Modes](#3-modes) — [3.1 Read-only queries](#31-read-only-queries-should) · [3.2 Pre-edit and structural tools](#32-pre-edit-and-structural-tools-should) · [3.3 The command-line surface](#33-the-command-line-surface-required) · [3.4 The configuration file](#34-the-configuration-file--candorconfig-should)
- [4. The trust contract](#4-the-trust-contract--the-core-of-candor)
- [5. Capabilities](#5-capabilities-conformance) — [5.1 The effect manifest](#51-the-effect-manifest--declared-effects-for-an-opaque-dependency-05)
- [6. Diagnostics](#6-diagnostics-as-eff-00x) — [6.1 Containment](#61-containment--the-architecture-quality-signal-deliberately-not-a-score) · [6.2 The policy DSL](#62-the-policy-dsl-normative)
- [7. Conformance checklist](#7-conformance-checklist-for-an-implementation)
- [8. Changelog](#8-changelog)
- [Appendix — Implementing 0.8: the checklist](#appendix--implementing-08-the-checklist)

**Version 0.8** — all four code engines declare `0.8`; the floor is conformance-pinned. How versions
move (the ladder, the floor, who may lead a rung) is stated once, in **[Versioning policy](#versioning-policy)**
below. The ⟨0.8⟩/⟨0.7⟩/⟨0.6⟩ markers through this document tag each surface with the rung that introduced
it; the [changelog](#8-changelog) lists every rung's contents. Each rung is additive over the last, so an
older-version consumer that ignores the newer optional fields is unaffected.

The **spec/contract version** — the report schema, the effect vocabulary, the `AS-EFF` codes, and the
**pinned tool surfaces** (the §3.1 query shapes, the §3.3 command-line surface, the §6.2 policy grammar) —
that a conformant implementation declares it implements (the envelope's `spec`). It is
distinct from an engine's *build id* (a git hash, §2.1) and from its *release semver*. An engine's
release **major.minor tracks the spec it implements** — `candor-java 0.8.x` declares spec `0.8`, a sibling
still on the floor declares `0.7` — with
the patch floating per-engine; internal library crates (e.g. `candor-report`) keep their own semver.

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
says "a §1 effect name" (the §5.1 manifest, §6.1 containment, a policy `deny` set), it means the ten
effects above, never `Unknown` (which `deny Unknown` addresses explicitly, §6.2).

Plain **console writes** (`println!`, `System.out.println`, bare stdout/stderr) are deliberately **not**
classified — not as `Log`, not as `Fs`. Classifying them would flood every CLI tool's report (printing
*is* a CLI's purpose, the way `Db` is a database app's — the §6.1 argument), drowning the signal. `Log`
is for calls into a logging/tracing *framework*, whose presence is an architectural fact. The four code
engines agree on this; an implementation that does classify console output MUST use a
language-specific effect name, not `Log`.

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
  "candor":    { "version": "<engine build id>", "toolchain": "<channel>", "spec": "0.8" },
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
parsing entry hashes. When the field is absent, coverage is derivable from the entries' `hash`
prefixes (`pkg#…`), which an all-pure empty report does not have; emit the field.

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
                                         // field whose target isn't statically known). Lets a consumer
                                         // tell irreducible opacity (reflection, native) from the
                                         // IMPROVABLE kind (`dispatch:`/`callback:` — a missing impl or
                                         // an unresolved higher-order target, often resolved by widening
                                         // the analysed inputs). Omitted when this fn introduces no
                                         // direct Unknown.
  "unitKind":     "accessor",            // OPTIONAL ⟨0.5⟩: what KIND of unit this entry is, when it
                                         // is not an ordinary function/method. Absent = "function".
                                         // Recommended values: "initializer" (static/class init —
                                         // a JVM <clinit>, a lazy/static initializer), "accessor"
                                         // (computed property get/set/observer bodies), "export"
                                         // (a module-boundary export surface, the CJS shape),
                                         // "agent"/"command"/"skill"/"cron"/"session"/"hooks"
                                         // (an agent-fleet report).
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
  "tables":       ["ledger.entries"]     // OPTIONAL: when `Db` is present, the LITERAL database
                                         // tables statically visible (table-position identifiers
                                         // in a SQL string literal). Same rules as `hosts`.
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
- `spec`: the **candor-spec contract version** this engine implements (`"0.8"`). This is the version
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

## 3. Modes

An implementation SHOULD support:

- **audit** (default): report each function's `inferred` set; no judgement.
- **JSON**: write the §2 report to a file for machine/agent consumption.
- **conformance**: given functions that *declare* capabilities (§5), flag mismatches (§6). MAY be
  scoped to a module/path prefix for incremental adoption.
- **no-ambient**: flag any *direct* use of ambient authority (an effect performed without holding a
  matching capability), pushing toward a capability-passing / capability-secure style.
- **baseline guard**: diff against a saved report and flag functions that *gained* an effect.
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
  since the ⟨0.5⟩ query parts — the §2.1 and §5.1 references resolve here.)*
- **reachable / path / impact**: the runtime effect surface (union over entry points), an effect's
  provenance (the call chain to its source), and the blast radius from entry points.
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
gains    { "gained":[Effect…], "byFunction":[ { "fn", "effect" } ], …optional provenance fields }
reachable { "entryPoints":int, "effects": { "<Effect>": { "count":int, "via":[fn…] } } }
path      { "effect", "fn", "path":[ { "fn", "loc", "source":bool } ] }
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

`blindspots` ⟨0.6⟩ is the *source* view of `Unknown`: each entry is a unit whose OWN body has an
unresolvable call (so it carries `unknownWhy`, required on such a unit — §4), with `reaches` the size of
its `Unknown` blast radius (the transitive callers that inherit `Unknown` through it; blast radii may
overlap between sources) and `affected` that list (optional, like `impact`). Sorted by `reaches`
descending — the root causes that poison the most functions first. A unit whose `Unknown` is purely
inherited (no `unknownWhy` of its own) is NOT a source and is excluded; `totalUnknown` is the report's
total count of units carrying `Unknown` — the surface these sources explain. The point is to turn a
high-`Unknown` report from "the analysis failed" into a short, ranked worklist of real blind spots.

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
smaller, more informative set), not their transitive cones. An engine whose language has no class/protocol
dispatch (the Rust scanner emits no `dispatch:`) returns `possibleViaUnknownDispatch: []` consistently (N/A
by language model, not a gap). The cross-impl suite pins the frontier output across the dispatching engines.

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
| `--gate-json <file>` ⟨0.8⟩ | write the **structured gate verdict** (below) as JSON — the machine analog of the `AS-EFF` console lines, from the SAME check that sets the exit code. Written whenever the FLAG is given, **except on exit 2**: with a gate active it re-emits that gate's verdict; with no gate configured it writes the clean verdict `{ ok: true, violations: [] }`. Does not change the exit code. |
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

- **On exit 2 (could-not-evaluate) NO verdict is written.** An unreadable policy, an invalid baseline,
  an unknown flag — the run could not evaluate the gate, so there is no faithful verdict to emit;
  writing `ok: true` (or `ok: false`) would fabricate one. The "written whenever the flag is given"
  rule above carries this single exception.
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
four, chosen to be language-neutral over *why a call's body could not be resolved*:

| `kind` | meaning | `detail` |
|---|---|---|
| `reflect:` | invocation chosen at runtime by name/metadata — reflection, `Method.invoke`, `eval`, dynamic property install/accessor | best-effort |
| `native:` | a boundary to code the engine cannot analyse — native methods, FFI/`extern`, intrinsics | best-effort |
| `dispatch:` | an unresolved **virtual / interface / protocol** dispatch with a **resolvable owner type + member** — static target known, concrete body not (no impl, bounded-CHA over many impls, dynamic receiver of known type) | **`<owner-type>.<member>`** (dotted) — NORMATIVE |
| `callback:` | an unresolved **higher-order / owner-less** invocation — a function/closure *value* (param, field, bound, computed, opaque-iterable) whose target and owner type are not both known | best-effort |

The dividing line between `dispatch:` and `callback:` is whether a **resolvable owner type** exists:
`dispatch:` is reserved for unresolved member dispatch where the engine knows the owner type and member
(so a consumer can resolve overrides — this is what the `callers --include-unknown` frontier keys off);
every other unresolved invocation (an opaque function value, an untyped receiver, opaque iteration) is
`callback:`. Only the `dispatch:` detail is conformance-compared (as `owner.member`); the other three
kinds' details are best-effort prose. An engine emits whichever kinds its language model produces — a
language with no virtual/interface dispatch (e.g. the Rust scanner: only `callback:`/`native:`) simply
emits no `dispatch:`, and its frontier is correspondingly empty.

⟨0.7⟩ **What is conformance-binding, and what is per-language.** Precisely: the **`kind` SET**
(`reflect`/`native`/`dispatch`/`callback`) is the closed vocabulary every code engine's reasons draw from,
and the **`dispatch:` detail** (`owner.member`) is the one normative detail. Everything else is
per-language and **OPTIONAL**: an engine emits `native:` / `reflect:` **only where its language model
actually produces that origin** — they are not universal. By design the engines diverge here, legitimately:
the Rust scanner emits only `callback:`/`native:` (no class dispatch); TypeScript folds a native boundary
into `reflect:` (`eval`/`defineProperty`/dynamic accessor) and emits no bare `native:`; Swift's syntactic
model produces neither `reflect:` nor `native:`. A consumer therefore MUST NOT assume all four kinds appear
in every report — only that any kind it *does* see is one of the four (and that a `dispatch:` carries
`owner.member`). Finally, an engine **MAY** emit an additional, off-vocabulary kind **during a migration**
(candor-java has historically emitted `task-handoff:` and `indy:`; reconciling them onto the four is a
tracked, byte-changing task — MODEL.md): such a kind round-trips and a consumer tolerates it under §2
forward-compatibility. The conformance check pins the four canonical kinds and the `dispatch:` shape, and
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
that under-claims is caught the moment the source *is* analysed; the κ ledger (§7) names every
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

- **boundary**: `Db`, `Net`, `Exec`, `Fs`, `Ipc`, `Clipboard`. These *should* be contained in a
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
   contract, item 11), and, for an engine declaring `spec ≥ 0.8`, `--gate-json` (the structured
   gate verdict), with flag names and help wording consistent across engines;
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
    blast radius, the `rewire` verdict, the `§6.2` policy-DSL parse, the §2 tables extraction, the
    item-14 κ-ledger disclosure, and the read-only queries' JSON shapes + name-match ladder;
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

14. **disclose the curated classifier's blind spots per scan — the κ-coverage ledger.** Every
    candor engine classifies external calls against a curated table, and an UNLISTED package
    contributes nothing: invisible, not `Unknown`. That is the documented weaker edge of item 4's promise,
    and historically its sharpest (an unlisted password-hashing library read silently pure on
    exactly the call a security review cared about). A conforming engine MUST therefore emit,
    with each scan, the external packages the scanned code **demonstrably calls** that the
    classifier neither classifies nor has reviewed-pure, named with call counts: per-scan
    evidence in the receipt, not a documentation footnote. The disclosure line begins with the
    canonical marker **`κ doesn't know`** so consumers (and the conformance suite, which asserts
    it) can find it without per-engine wording knowledge. Exempt from the disclosure: the
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
    ladder behind them: its 0.8.0 adds `.candor/config`, `--gate-json` and the item-14 κ ledger, declaring
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
  - **§7 item 14, the κ-coverage ledger,** is MUST (conformance Part 4c already enforced it): the
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
  - §7 item 14: the **κ-coverage ledger** (disclose unlisted-but-called packages per scan), pinned
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
7. **§7 — the κ-coverage ledger, `--agents`, and the checklist items.** The per-scan `κ doesn't know`
   disclosure (item 14), the embedded agent contract (item 11), the self-gate (item 12), the soundness
   harness (item 13). Judged by **PART 4c** (the ledger differential) and **PART 7**; items 12–13 live
   in the engine's own CI.
