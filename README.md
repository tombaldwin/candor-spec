# candor

**Make what code *does* legible — to humans, and especially to AI agents.** candor is a family of
per-language tools that report, for every function, which side effects it performs — network,
filesystem, database, subprocess, env, clock, IPC, logging, randomness, clipboard — *transitively*,
and are honest about what they can't resolve.

This repo is the **language-agnostic specification**: the shared effect vocabulary, report schema,
diagnostic codes, modes, and agent contract that every implementation conforms to. The *design*
ports across languages; each implementation's *engine* is bespoke to its toolchain.

## Implementations

| Language | Repo | Engine | Status |
|---|---|---|---|
| Rust | [candor](https://github.com/tombaldwin/candor) | dylint (HIR + CHA) | **shipped** — reference implementation |
| Java / JVM | [candor-java](https://github.com/tombaldwin/candor-java) | ASM bytecode + CHA | **prototype** — full mode set; Spring-aware |
| C# / .NET | _planned_ | Roslyn analyzer | planned |
| Go | _planned_ | `go/analysis` + SSA | planned |

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

## Why per-language tools sharing one spec

"What does this code do?" is answered by language-specific machinery — type resolution, call-graph
construction — so the *engine* can't be shared. But the *output* should be identical: the effect
vocabulary, the report, the trust contract, the adoption ladder. That way an AI agent (or a human, or
a CI gate) uses a Rust report and a Java report exactly the same way. This repo is that shared
definition; the implementations plug into it.

## License

Dual-licensed under [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
