# Vein: an effect reached through IMPLICIT STRINGIFICATION — silent in ALL FOUR engines

**Status: CLOSED four-way** (2026-07-25) — java `5189da7`, swift `ca299f0`, ts `e1a84fc`, rust `382e7e0`.
Found under the `candor-java/eval/corpus-crossorg` pre-registration, which forbade fixing *during* the
confirmatory run; these are the "separate, later effort with its own separate result" that PREREG.md
anticipates. **Class: silent under-report (cardinal sin). Common-mode: 4 of 4 engines.**

## Closure summary

| engine | mechanism reused | A/B fabrication gate | suite |
|---|---|---|---|
| java `5189da7` | implicit-contract-reentry sink table (existed for `String.format`/`append`/`println`) — logging facades were simply absent from it | uflexi, 18.7k fns: **8939 -> 8939 effectful, 0 changed** | 436 |
| swift `ca299f0` | `edgeStringWitness` (concrete operands already worked) — added CHA over protocol conformers for existential/generic/caught-error operands | 10 packages, 4360 fns: 3 gains, **0 fabricated concrete effects** (all transitive `Unknown`) | 268 + smoke 104 |
| ts `e1a84fc` | `coercionTargets` (desugared the coercion protocol but never consulted the CHA machinery beside it) | 8 repos, ~17k fns: **0 effect-set changes**, 1 explained new edge | 600 |
| rust `382e7e0` | `charge_coercion` (concrete operands) + the existing bounded-CHA arm — joined; also closed inline-captured holes, a silent miss even for concrete types | **962 crates, 470,971 fns**: 4 concrete gains (one genuine recovery, verified to source), 0 losses, 93 `Unknown` (0.020%) | 338 + integration 150 |

**The dynamic oracle re-run closes the loop on the original catch:** HikariCP, same corpus and suite,
`cardinalSinViolations` **2 -> 0**, `honestyInvariantHolds` **false -> true**, and the two frames moved into
`soundCompleteOk` (25 -> 27) rather than `disclosedPartial` (unchanged at 47) — the effect was *resolved*,
not papered over with a fresh `Unknown`.

**In every engine the fix was a missing EDGE, not a missing concept.** Each already modelled implicit
stringification for the easy case and declined the dispatched one; three of the four had the needed CHA
machinery sitting adjacent and unused. That is a reassuring result for the model and an uncomfortable one
for the assumption that shared architecture implies shared correctness.

**Where the denylist-over-allowlist rule inverts, and why.** In swift an open "any type with local
conformers" rule *fabricates* — `enum Suit: String` records `String` as a conformed supertype, so every
`"\(someString)"` would edge to the enum's `description`. The conformance list is therefore closed by
name. In ts the *site* table is likewise an allowlist (every external call as a sink would flood), with
the denylist applied to the *targets*, where a forgotten case over-discloses rather than hides.

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

## Closure sketch (as written BEFORE the fix — retained; each engine followed it)

Model the formatting/logging boundary as a synchronous invoking HOF over its arguments: at a call to a
known formatting sink (slf4j/log4j parameterized methods, `String.format`, `console.*`, `format!`/`write!`,
Swift interpolation), edge to each argument's `toString`/`Display::fmt`/`description` — resolved where the
receiver type is known, disclosed as `Unknown[dispatch]` where it is not. The denylist-over-allowlist rule
applies: carve out proven-pure formatting targets rather than enumerating effectful ones.
