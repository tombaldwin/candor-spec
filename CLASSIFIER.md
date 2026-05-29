# Building a candor classifier for a new language

The classifier maps a *resolved* call target to an effect (or none). It is the heart of an
implementation — and where every hard lesson lives. These are distilled from building the Rust
reference implementation; they generalize.

## 1. Resolve, don't pattern-match syntax

The single most important rule. A bare `x.send()` is meaningless syntactically — it could be a
network dispatch, a channel send, or a builder method. You **must** resolve the call to its concrete
target (its fully-qualified definition) before classifying. Use the language's type-resolution or
call-graph tooling — Rust: dylint/HIR; Java: WALA / SootUp; C#: Roslyn; Go: `go/analysis` + SSA. A
syntactic tool cannot do this, and will be wrong in both directions.

## 2. Match the I/O boundary, not the library

Builder-pattern and SDK-heavy libraries are *mostly pure construction* — only the dispatch is the
effect. Tag the boundary call, not the whole crate/package:

- HTTP / cloud clients → the `.send()` / `.execute()`, not the request builders;
- DB clients → the query-*execution* verb, not query construction;
- raw sockets → the I/O types, not the address/data types alongside them.

Over-reporting erodes trust as much as under-reporting hides danger. Both are dishonesty about what
the code does. Add a precision test — a positive *and* a negative case — for each rule.

## 3. Make the classifier extensible

You cannot enumerate every effectful library. Ship a curated core (the stdlib + common libraries) and
a config mechanism so projects add their own rules without forking.

## 4. Resolve dispatch where you can; be honest where you can't

- Statically-resolvable calls, and (via CHA/RTA) dispatch over types you can see, → resolve precisely.
  The reference impl uses Class Hierarchy Analysis to follow `dyn`/generic dispatch over
  locally-defined traits to their impls.
- Dispatch you cannot resolve (unknown dynamic target, reflection, a callback value) → `Unknown`,
  never silent-pure (SPEC §4).
- **Exception:** dispatch over conventionally-pure stdlib interfaces (formatting, equality, hashing,
  cloning, conversion) may be treated as pure — otherwise ubiquitous patterns (e.g. error formatting
  via `dyn Error`) flood the report with false `Unknown`s. Curate this set tightly and exclude
  anything where an effect could hide (iterators, finalizers/`Drop`, `Fn`-like callbacks, I/O traits).

## 5. Let reality correct you

Synthetic tests miss real patterns. Run the classifier on real codebases *early*. Every gap the Rust
impl's classifier had — a missing HTTP client, an over-broad clock rule, error-formatting false
positives — was found by running on real code, not by reading it. A green build proves nothing.

## 6. Provide the trust signal

Whatever you can't classify with confidence, surface as `unresolved` / `Unknown` so consumers know
where to stop trusting the report. This is non-negotiable (SPEC §4) — it is what makes the report
safe for an agent to rely on.

## Language notes (starting points)

- **Java / Kotlin** — bytecode call graph via WALA or SootUp (CHA/RTA/points-to come for free); or a
  source-level Error Prone / Checker Framework plugin. Classify `java.io` / `java.nio.file`,
  `java.net` + `HttpClient`, `java.sql` execution, `ProcessBuilder` / `Runtime.exec`, `System.getenv`,
  clocks, slf4j/log4j, `Random` / `SecureRandom`. Capability declarations map naturally onto
  dependency injection; no-ambient maps onto "don't bypass DI". Ceiling: reflection / AOP / proxies
  (Spring) defeat the call graph — be honest (`Unknown`) there. Bonus: checked exceptions are a
  native effect annotation you can read straight from signatures.
- **C# / .NET** — a Roslyn analyzer (first-class semantic API, ships as NuGet, runs in IDE + build).
  Likely the easiest engine to build. `async` / `await` already primes the effect mindset.
- **Go** — `golang.org/x/tools` SSA + the `go/analysis` framework. Small, explicit stdlib (`os`,
  `net`, `database/sql`, `os/exec`, `time`, `log`); no exceptions. Interface dispatch needs RTA.
