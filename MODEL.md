# The candor domain model — a shared vocabulary

This document names candor's domain concepts as **types**, so every engine can express the same model
in its own idiom. It is a *vocabulary*, not a schema: there is no shared library or generated code to
import. The contract remains [SPEC.md](SPEC.md) (the wire format + behavior) and [SEMANTICS.md](SEMANTICS.md)
(the analysis); `conformance/` proves the engines agree. Each engine **derives this model independently
from the spec** — that independence is what the cross-engine differential is evidence for, and is why
the model is described here rather than shipped as code.

The motivation: the spec's nouns (an effect, the per-unit entry, a report, the policy rules, the
diagnostic codes) tend to live as strings, maps, and conventions in an implementation. Naming them as
types makes the compiler enforce the vocabulary, unifies an engine's producer and consumer sides, and
gives the family a shared way to talk about the same things.

## The concepts

| Concept | What it is | Spec | Wire |
|---|---|---|---|
| **Effect** | An observable interaction with the world outside pure computation. The closed vocabulary `Net, Fs, Db, Exec, Env, Clock, Ipc, Log, Rand, Clipboard`, plus `Unknown` — which is **not** an effect but the §4 trust marker. | §1 | a string (`"Net"`) |
| **EffectSet** | A set of effects — an element of the lattice `𝓛 = (𝒫(𝔼 ∪ {Unknown}), ⊆)`, join = ∪. The value attributed to a unit's `inferred` / `direct`. | SEMANTICS §1 | a (spec-name-sorted) array |
| **Effector** | The smallest body the engine attributes effects to — a function/method, a static initializer, a computed accessor, an export surface, an agent-fleet session/hook. (The spec's historical term was "unit"; the wire field stays `fn`.) The per-unit report entry. | §2 | the entry object |
| **EffectorKind** | What kind of effector an entry is when not an ordinary function: `initializer`/`accessor`/`export`/`agent`/`command`/`skill`/`cron`/`session`/`hooks`. Absent = function. | §2 | `unitKind` |
| **UnknownReason** | Why a body introduced `Unknown` directly — a `kind:detail` tag. Canonical kinds: `reflect`/`native`/`dispatch`/`callback`. | §4 | a `unknownWhy` string |
| **Provenance** | Which engine produced a report and which contract it conforms to: `version` (build id), `toolchain`, `spec`. | §2.1 | the `candor` header |
| **Report** | The envelope: provenance + the package(s) covered + the effectors. | §2 | `{ candor, packages, functions }` |
| **PolicyRule** | An architecture-as-code rule (sealed: `Deny` / `Allow` / `Forbid`), the parsed form of the §6.2 DSL. | §6.2 | (read from a policy file) |
| **Diagnostic / DiagnosticCode** | A gate finding + its standardized code (`AS-EFF-001..010`). | §6 | (gate output) |
| **Mode** | An analysis mode — audit, conformance, no-ambient, baseline, policy, taint, containment. | §3 | (selected by flag/env) |

The **load-bearing serialization invariant**: an effect set's wire form is its names sorted by spec
name. With every effect→wire path going through that one ordering, an engine can use any internal
representation (an enum set, a string set) and stay byte-identical.

## Per-engine realization

The model is expressed in each engine's natural style. None of these are shared across repos.

| Concept | Rust (`candor-rust`) | Java (`candor-java`) | TypeScript / Swift |
|---|---|---|---|
| Effect | `EFFECTS: [&str; 11]` (const) | `enum Effect` | string constant set |
| EffectSet | `Vec<String>` / `BTreeSet` | `final class EffectSet` (EnumSet-backed) | `Set<string>` / `[String]` |
| Effector | `struct ReportEntry` (`candor-report`) | `record Effector` (`io.poly.candor.model`) | object literal / `[String:Any]` |
| Provenance | `struct ReportMeta` | `record Provenance` | object literal |
| Report | `struct Report` | `record Report` | object literal |
| PolicyRule | `PolicyRule`/`AllowRule`/`LayerRule` (`candor-classify`) | sealed `PolicyRule.{Deny,Allow,Forbid}` | object literals |
| (de)serialization | serde | one `ReportJson` serializer + parser | hand-built + defensive read |

candor-java is the JVM **reference realization**: a public `io.poly.candor.model` package holding
the types above, used on both the producing side (the analyzer builds `Effector`s, serialized through
a single `ReportJson`) and the consuming side (the query tool reads reports into the same `Effector`).
Rust's `candor-report` is the established, most-typed reference for the wire structs. TS and Swift
assemble entries ad hoc and validate on read; they can converge on named types where it is idiomatic,
but are under no obligation to — the spec + conformance are the contract.

## Notes / open items

- **Wire field names are historical, not the model names.** `fn` (not `effector`) and `unitKind` (not
  `effectorKind`) stay for compatibility, exactly as the spec already pins `fn`. Renaming a wire field
  would be a separate, versioned, all-engines migration.
- **`UnknownReason` kinds beyond the canonical four.** The spec's code vocabulary is four kinds;
  candor-java currently also emits `task-handoff` and `indy`. Its `UnknownReason` models all of them
  (and preserves any unrecognized prefix verbatim) so reports round-trip; reconciling those two onto
  the canonical four is a tracked, deliberate (byte-changing) conformance task.
- **AS-EFF-010 (containment regression)** is defined by the spec but not implemented by every engine
  (e.g. candor-java models codes 001–009).
- **`Clipboard` is unclassified in the §6.1 containment partition.** §6.1 splits effects into boundary
  (`Db,Net,Exec,Fs,Ipc`) and ambient/cross-cutting (`Log,Clock,Rand,Env`); `Clipboard` was added to the
  vocabulary later and is in neither, so containment scoring silently ignores it. A spec decision is
  needed (it is plausibly a boundary effect — external-resource I/O). candor-java pins the current
  partition with a test so the gap can't change unnoticed.
