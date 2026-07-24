# Vein: an effect reached through IMPLICIT STRINGIFICATION — silent in ALL FOUR engines

**Status: OPEN, recorded not repaired** (found under `candor-java/eval/corpus-crossorg` pre-registration,
which forbids fixing during the confirmatory run). **Class: silent under-report (cardinal sin).**
**Common-mode: 4 of 4 engines.**

## How it was found

The cross-organization confirmatory corpus (RQ1) ran `HikariCP-5.1.0` — an organization no candor
classifier fix was ever developed against — under the transitive oracle. Two functions reported a
**false all-clear**:

| function | inferred | observed | escaped |
|---|---|---|---|
| `com.zaxxer.hikari.util.ConcurrentBag.remove` | `[Log]` | `[Clock]` | `Clock` |
| `com.zaxxer.hikari.util.ConcurrentBag.unreserve` | `[Log]` | `[Clock]` | `Clock` |

## The mechanism (after one wrong diagnosis — recorded, because the wrong one is instructive)

**First diagnosis, WRONG:** "the compiler-inserted `toString()` at a string concatenation". A 12-line
fixture disproved it — candor-java resolves that correctly (`Vein.describe -> [Clock]`). Never trust a
mechanism story that has not been reduced to a fixture.

**Actual mechanism:** the call is *SLF4J parameterized logging*, not concatenation:

```java
public class ConcurrentBag<T extends IConcurrentBagEntry> { ...
   LOGGER.warn("Attempt to remove an object ... : {}", bagEntry);   // arg passed as Object
```

`toString()` is invoked **inside the logging library** (slf4j's `MessageFormatter`, at format time), not
at the call site. The concrete `PoolEntry.toString()` calls `currentTime()`. So at runtime the stack is
`remove → LOGGER.warn → MessageFormatter → PoolEntry.toString → currentTime`, and the effect is correctly
charged to `remove`; statically, candor resolved the explicit `LOGGER.warn` (hence the inferred `Log`) and
never followed the library's internal callback onto its argument.

This is the same FAMILY as the already-closed `forEach` / `doPrivileged` veins (`eval/transitive-reconcile`
RECONCILE.md): **a library method that synchronously invokes a callback on its argument.** What is new is
that the callback is `toString()` and the invocation is a *formatting convention* rather than a functional
interface, so `isInvokingHof`-style modelling never fired.

## Four-way reproduction (12-line fixtures, all confirm the miss)

| engine | fixture shape | result |
|---|---|---|
| candor-java | `LOGGER.warn("{}", e)` where `T extends Entry`, `Impl.toString()` → `currentTimeMillis()` | `describe -> [Log]`, **Clock missing** |
| candor-ts | `console.log("entry: %s", e)`, `Impl.toString()` → `Date.now()` | `describe` absent, **Clock missing** |
| candor-rust | `format!("entry: {}", e)` where `T: Display`, `Display::fmt` → `SystemTime::now()` | `describe` absent, **Clock missing** |
| candor-swift | `"entry: \(e)"`, `CustomStringConvertible.description` → `Date()` | `describe` absent, **Clock missing** |

In every case the *implementation* is analysed correctly (`Impl.toString` / `Display::fmt` /
`description` all carry `Clock`); what is missed is the **edge from the formatting site to it**.

## Why this matters beyond one more vein

This is a textbook **common-mode** defect, and it is the paper's RQ3 thesis reproducing itself:

- **Cross-engine conformance was green on it throughout.** Four independent implementations over four
  unrelated representations (bytecode / TS AST / Rust IR / SwiftSyntax) share the blind spot, because they
  share the *assumption* — that stringification is pure — not any code. Agreement cannot see it.
- **It took mechanism-independent evidence to surface it**: a runtime oracle, on third-party code, from an
  organization whose logging idiom differs from the corpus the classifier grew up on. The Apache Commons
  corpora never triggered it.
- The effect class involved (`Clock`) is benign; the *shape* is not. Any effect reachable from a
  `toString`/`Display`/`description` implementation — a lazily-resolved hostname, a file read, a metrics
  counter that touches the network — is silently absorbed at every logging call site in a program.

## Closure sketch (NOT implemented — the pre-registration forbids it during the run)

Model the formatting/logging boundary as a synchronous invoking HOF over its arguments: at a call to a
known formatting sink (slf4j/log4j parameterized methods, `String.format`, `console.*`, `format!`/`write!`,
Swift interpolation), edge to each argument's `toString`/`Display::fmt`/`description` — resolved where the
receiver type is known, disclosed as `Unknown[dispatch]` where it is not. The denylist-over-allowlist rule
applies: carve out proven-pure formatting targets rather than enumerating effectful ones.
