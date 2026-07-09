# Building a candor classifier for a new language

The classifier maps a *resolved* call target to an effect (or none). It is the heart of an
implementation — and where every hard lesson lives. These are distilled from building the family's
first implementation (Rust); they generalize.

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
- raw sockets → the I/O types, not the address/data types alongside them. But detection here
  is **crate-keyed**: recognising `std::net`/`tokio::net` is not enough — a project on another
  socket runtime (legacy `tokio_tcp`/`tokio_udp`, or `async-std`/`smol`/`mio`) opens sockets through
  *different* types, and a tool that only knows the mainstream pair will confidently report 0 network
  on it. (Found running on websocat, still on tokio 0.1: its `tokio_tcp::TcpStream::connect` was
  classified network-free.) Cover the runtimes your corpus actually uses; treat each as its own
  calibration with a real repro.

The same *verb* can sit on different sides of that boundary in different libraries, so calibrate
per-library, not per-verb: in `sqlx`, bare `query()` only **builds** (the effect is `.fetch_*`/
`.execute()`), but in `tokio-postgres`/`postgres`/`rusqlite` `query()`/`batch_execute()`/`prepare()`
**are** the round-trip. A rule tuned to exclude sqlx's builder silently hid 16 of pgman's 20 DB call
sites until an A/B on the real app exposed it (§5). Give each library its own verb set.

Over-reporting erodes trust as much as under-reporting hides danger. Both are dishonesty about what
the code does. Add a precision test — a positive *and* a negative case — for each rule.

## 3. Make the classifier extensible

You cannot enumerate every effectful library. Ship a curated core (the stdlib + common libraries) and
a config mechanism so projects add their own rules without forking.

## 4. Resolve dispatch where you can; be honest where you can't

- Statically-resolvable calls, and (via CHA/RTA) dispatch over types you can see, → resolve precisely.
  The Rust impl uses Class Hierarchy Analysis to follow `dyn`/generic dispatch over
  locally-defined traits to their impls.
- Dispatch you cannot resolve (unknown dynamic target, reflection, a callback value) → `Unknown`,
  never silent-pure (SPEC §4).
- **Exception:** dispatch over conventionally-pure stdlib interfaces (formatting, equality, hashing,
  cloning, conversion) may be treated as pure — otherwise ubiquitous patterns (e.g. error formatting
  via `dyn Error`) flood the report with false `Unknown`s. Curate this set tightly and exclude
  anything where an effect could hide (iterators, finalizers/`Drop`, `Fn`-like callbacks, I/O traits).

## 5. Let reality correct you

Synthetic tests miss real patterns. Run the classifier on real codebases *early*. Every gap the Rust
impl's classifier had — a missing HTTP client (reqwest), an over-broad clock rule, error-formatting
false positives, a tokio-postgres DB gap hiding 16 of 20 call sites — was found by running on real
code, not by reading it. A green build proves nothing. The strongest version of this is an **A/B**:
have one agent answer a question from the candor report and another from source alone, then diff —
that's exactly how the pgman DB gap surfaced.

## 6. Provide the trust signal

Whatever you can't classify with confidence, surface as `unresolved` / `Unknown` so consumers know
where to stop trusting the report. This is non-negotiable (SPEC §4) — it is what makes the report
safe for an agent to rely on.

## Language notes (starting points)

- **Java / Kotlin** — bytecode call graph via WALA or SootUp (CHA/RTA/points-to come for free); or a
  source-level Error Prone / Checker Framework plugin. (Note: the shipped engine, candor-java, chose
  **plain ASM plus its own bounded CHA** over these frameworks — a smaller dependency surface and full
  control of classification; WALA/SootUp remain viable starting points for a new engine.)
  Classify `java.io` / `java.nio.file`,
  `java.net` + `HttpClient`, `java.sql` execution, `ProcessBuilder` / `Runtime.exec`, `System.getenv`,
  clocks, slf4j/log4j, `Random` / `SecureRandom`. Capability declarations map naturally onto
  dependency injection; no-ambient maps onto "don't bypass DI". Ceiling: reflection / AOP / proxies
  (Spring) defeat the call graph — be honest (`Unknown`) there. Bonus: checked exceptions are a
  native effect annotation you can read straight from signatures.
- **C# / .NET** — a Roslyn analyzer (first-class semantic API, ships as NuGet, runs in IDE + build).
  Likely the easiest engine to build. `async` / `await` already primes the effect mindset.
- **Go** — `golang.org/x/tools` SSA + the `go/analysis` framework. Small, explicit stdlib (`os`,
  `net`, `database/sql`, `os/exec`, `time`, `log`); no exceptions. Interface dispatch needs RTA.
- **TypeScript / JavaScript** — resolve with the **TypeScript compiler API** (`ts.TypeChecker`:
  `getResolvedSignature` / `getSymbolAtLocation` / `getTypeAtLocation` give devirt-equivalent targets) or
  the ergonomic `ts-morph` wrapper; `@typescript-eslint`'s typed AST also works. Heed §1 hard — a bare
  `x.write()` / `db.query()` means nothing until the receiver's type resolves. The κ surface:
  **Fs** `node:fs` + `fs/promises` (`readFile`/`writeFile`/`createReadStream`), `Bun.file`, `Deno.readFile`;
  **Net** the global `fetch`/`undici`, `node:http(s)`, raw `node:net` sockets, `node:dgram`, `axios`/`got`/
  `node-fetch`, `WebSocket`;
  **Db** the *execution* verb (the I/O boundary, exactly the sqlx lesson in §2): `pg`/`mysql2` `query`,
  `better-sqlite3` `run`/`get`/`all`, `mongodb` `find`/`insertOne`, `ioredis` — and for the ORMs
  (Prisma/Drizzle/TypeORM/Knex) the awaited *execution*, not the chained query builders;
  **Exec** `node:child_process` (`exec`/`execFile`/`spawn`/`fork`), `Bun.spawn`, `Deno.Command`;
  **Env** `process.env` access + `Deno.env.get`; **Clock** `Date.now`/`new Date()`/`performance.now`/
  `process.hrtime`; **Rand** `Math.random`, `node:crypto` (`randomBytes`/`randomUUID`), Web `crypto.getRandomValues`;
  **Log** `console.*`, `pino`/`winston`/`debug`; **Clipboard** the browser `navigator.clipboard`.
  Capability declarations (§5) have no native token, but a *branded type* or a dependency-injected
  collaborator (a NestJS provider, an injected `fs`-like handle) declares the surface — no-ambient maps
  onto "receive your I/O, don't `import` it". **Ceiling — the gradual-typing escape hatch is the defining
  honesty pressure here:** an `any`-typed receiver, an **untyped JS dependency** (no `.d.ts`), `eval` /
  dynamic `import()` / `require(variableName)`, and monkey-patched or computed dispatch (`obj[name]()`) are
  all unresolvable and MUST be `Unknown`, never assumed pure (SPEC §4). This is actually a clean fit —
  TS's `any` and an untyped import *are* the "could not resolve" case the trust contract already names.
  Like the JVM, a Unix-domain socket is `net.connect({ path })` with the family as a runtime argument, so
  it reads as `Net` (the same documented `Ipc`/`Net` asymmetry).
