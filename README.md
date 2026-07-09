# candor

<p align="center"><img src="https://raw.githubusercontent.com/tombaldwin/candor/main/assets/beaky.svg" alt="Beaky, the candor canary" width="180"></p>

**Make what code *does* legible — to humans, and especially to AI agents.** candor is a family of
per-language tools that report, for every function, which side effects it performs — network,
filesystem, database, subprocess, env, clock, IPC, logging, randomness, clipboard — *transitively*,
and are honest about what they can't resolve.

This repo is the **language-agnostic specification**: the shared effect vocabulary, report schema,
diagnostic codes, modes, and agent contract that every implementation conforms to. The *design*
ports across languages; each implementation's *engine* is bespoke to its toolchain.

**Site:** [candor.poly.io](https://candor.poly.io) — the measured case in five minutes: the
exhibits, the pre-registered evals, and the prove-it-on-your-own-repo path.

## Implementations

| Language | Repo | Engine | Status |
|---|---|---|---|
| Java / JVM | [candor-java](https://github.com/tombaldwin/candor-java) | ASM bytecode + CHA | **shipped (spec 0.8)** — the **reference engine**; full mode set incl. `--gate-json`; Spring-aware; Java/Kotlin/Scala/Groovy (`jbang candor@tombaldwin/candor-java`) |
| Rust | [candor-rust](https://github.com/tombaldwin/candor-rust) | dylint (HIR + CHA) + a stable `syn` scanner | **shipped (spec 0.8)** — `cargo install candor-scan` |
| TypeScript | [candor-ts](https://github.com/tombaldwin/candor-ts) | TS compiler API | **shipped (spec 0.8)** — project scanning, gate, queries, MCP + LSP servers; on npm (`npx -y candor-ts`) |
| Swift | [candor-swift](https://github.com/tombaldwin/candor-swift) | SwiftParser (syntactic) | **shipped (spec 0.8)** — receiver-typed local inference; the 4th conformance engine |
| C# / .NET | _planned_ | Roslyn analyzer | planned |
| Go | _planned_ | `go/analysis` + SSA | planned |

Domain engines (units are not functions; ride the version ladder on their own schedule — SPEC §4):

| Domain | Repo | Engine | Status |
|---|---|---|---|
| Agent fleets | [candor-agents](https://github.com/tombaldwin/candor-agents) | declared-vs-observed effect analysis over agent fleets (units = agents/sessions/hooks) | **shipped (spec 0.8)** — v0.8.1; `pipx install git+https://github.com/tombaldwin/candor-agents` |

## Documents

- **[SPEC.md](SPEC.md)** — the contract: effect vocabulary, JSON report schema, the `AS-EFF-00x`
  codes, the modes, and the trust contract. What it means to "be a candor implementation."
- **[SEMANTICS.md](SEMANTICS.md)** — the formal analysis: the effect lattice, call-site resolution
  rules, the transitive fixpoint, cross-crate composition, the conformance predicates, and the
  soundness/precision/termination properties (with the two honesty caveats stated explicitly).
- **[PRINCIPLES.md](PRINCIPLES.md)** — the ideas the family is built on (honesty under uncertainty).
- **[AGENTS.md](AGENTS.md)** — how an AI agent *consumes* a candor report (any language).
- **[CLASSIFIER.md](CLASSIFIER.md)** — how to build the effect classifier for a new language, and the
  precision lessons learned the hard way.
- **[conformance/](conformance/)** — an *executable* differential: the same fixtures across the four
  engines (JVM, Rust, TypeScript, Swift), asserting they all infer the spec-mandated effect set, agree
  on the policy verdict, the `--gate-json` verdict + exit code (⟨0.8⟩), the `.candor/config` discovery
  and fail-closed posture, the query shapes (incl. `blindspots`, the containment ratchet, the
  unresolved-dispatch frontier), the κ-coverage ledger, the masked-literal fail-closed gate, and the
  §6.2 grammar (`bash conformance/run.sh`). Conformance and cross-impl agreement in one run.

## Why per-language tools sharing one spec

"What does this code do?" is answered by language-specific machinery — type resolution, call-graph
construction — so the *engine* can't be shared. But the *output* should be identical: the effect
vocabulary, the report, the trust contract, the adoption ladder. That way an AI agent (or a human, or
a CI gate) uses a Rust report and a Java report exactly the same way. This repo is that shared
definition; the implementations plug into it.

This is the line a per-language tool (CodeQL, Semgrep, ArchUnit) can't cross. They can have *rules* for
each language, but never a guarantee those rules *mean the same thing*. candor can — and it's not a
claim: [`conformance/`](conformance/) is a CI-enforced differential that runs the engines on equivalent
fixtures and fails if they disagree on the **effect set**, the **policy verdict**, or the **§6.2
grammar** — *on those fixtures*: the differential covers what the battery encodes (and the battery
grows with every divergence found in the wild), not every conceivable program. So a `deny Net
in <layer>` boundary is enforced *identically* across a polyglot codebase, by construction. That cross-
language consistency — not raw analysis power — is the durable position: it's what neither a smarter model,
a single-language effect system, nor a per-language ruleset can offer.

## License

Dual-licensed under [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
