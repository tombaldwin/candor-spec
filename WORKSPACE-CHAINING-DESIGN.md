# Workspace report chaining — cross-package interface dispatch (design)

*Status: SHIPS on candor-ts + candor-swift (spec 0.22 line, gated behind `CANDOR_WORKSPACE_CHAIN`), and
conformance **PART 18** pins the field + the cross-package resolution across both — the ≥2-engine + pinned
threshold for a rung (the ladder discipline, [[candor-versioning-ladder]]). This document specs the
`interfaceUnion` report field, the `--workspace` discovery flag, and the cross-package-interface-dispatch
rule. Remaining: the candor-rust roll (trait-union entries); candor-java is N/A (whole-classpath bytecode).*

## The problem

candor scans **one package at a time**. A call into a *dependency* is resolved through report **chaining**
(`CANDOR_DEPS`, SPEC §2): a consumer joins a loaded sibling report by `hash` (`pkg#LocalName`) and inherits
that function's effects. This works for a call that resolves to a **concrete** external declaration
(`new SNS().publish()` → the class method's entry).

It does **not** work for **interface / protocol / trait dispatch across a package boundary**. When a consumer
calls a method on a value whose *declared* type is an interface imported from a sibling package —

```ts
// @ukri-tfs/message-handling exports:  interface OutboundChannel { publish(m): Promise<void> }
//                                       class AwsOutboundChannel implements OutboundChannel { publish(){ …SNS… } }
function publishEvent(ch: OutboundChannel) { return ch.publish(evt); }   // consumer package
```

— the type checker resolves `.publish` to the **interface method signature**, which has **no body**, so it
is **no report entry**, so the chain join misses and the call reads **pure**. Yet every implementation
reaches an effect. On a real monorepo backend this is not a corner case: measured on the ukri-tfs services,
**545 functions across 11 services** read pure per-package that actually reach an effect one workspace hop
away (HTTP service-clients → Net, repositories → Db, config → Env).

The engine already does interface→impl CHA *within* a package; the gap is that the union is not **exposed**
to consumers in the report.

## The mechanism (three parts)

**1. `interfaceUnion` report entries (producer side).** When emitting a package's report, for each local
interface `I` with ≥1 implementing class and each method `m` of `I`, emit a synthetic entry:

```json
{ "fn": "OutboundChannel.publish", "hash": "@scope/pkg#OutboundChannel.publish",
  "inferred": [], "invisible": ["@aws-sdk/client-sns"], "interfaceUnion": true }
```

whose effects are the **union** over every implementing class `C` of `C.m`'s effects (`inferred`) and blind
boundaries (`invisible`) — reusing the same interface-CHA universe in-package dispatch uses. It is a **sound
over-approximation** (union of impls); **omitted when the union is pure** (silence = purity, SPEC §2 rule 3).
The `interfaceUnion: true` flag marks the entry synthetic so a consumer can tell it from an analyzed unit
(it is NOT counted in `analyzed.count`, which is the analyzed-unit universe).

Because a consumer resolving `ch.publish()` on an `I`-typed receiver already keys the chain lookup on
`pkg#I.m`, **no consumer-side change is needed** — the union entry is what the existing lookup was missing.

**2. `invisible` travels through the chain (consumer side).** A chained dep function's own blind boundary
(an uncovered package IT calls into) must reach the consumer as **its** `invisible` — else a sibling's
`SnsTopic.publish → invisible:[@aws-sdk/client-sns]` reads pure across the edge. (candor-swift already does
this; candor-ts gained it with this work; candor-rust/java to confirm.)

**3. `--workspace` auto-discovery (ergonomics).** `candor <target> --workspace` (alias `--deps`) discovers the
target's **symlinked** monorepo dependencies (a workspace link points OUT of `node_modules`/the module dir to
the package's real source; a published dep is a real dir), scans each into `.candor/deps/` with `interfaceUnion`
emission enabled, and chains them — the source-engine analog of rust `--deps` (which scans the Cargo.lock
tree). **Transitive**: deps are re-scanned WITH the accumulating deps dir chained, to a monotone fixpoint, so
a dep's calls into *its own* workspace deps resolve too.

## Gating

`interfaceUnion` emission is **opt-in** (candor-ts: env `CANDOR_WORKSPACE_CHAIN`, set by `--workspace` on the
child scans) so a **default** scan stays byte-identical and four-way conformance is unaffected until the rung
is pinned. A load-bearing sub-fix rode along, ungated because it is pure correctness: a **workspace-symlinked**
dep's real path has no `node_modules/` segment, so module-name resolution must walk up to the nearest
`package.json` `name` — otherwise a monorepo dep's effects are mis-keyed (an unmatchable chain key AND an
ugly `invisible:[/abs/path]`).

## Four-way status & rollout

`interfaceUnion` now SHIPS on **two** engines (candor-ts + candor-swift), the threshold for a floor rung
(conformance PART 18 pins the field + the cross-package resolution).

| engine | chaining infra | `invisible` through chain | cross-pkg interface/protocol dispatch | discovery flag |
|---|---|---|---|---|
| **candor-ts** | ✓ (§2) | ✓ (added here) | WAS **silent-pure** → **FIXED** via `interfaceUnion` (gated) | ✓ `--workspace` |
| **candor-swift** | ✓ (Deps.swift) | ✓ (already) | WAS **silent-pure** for an external-protocol-typed receiver (an interface method on a value whose protocol is imported from a chained package read PURE) → **FIXED** via protocol-CHA `interfaceUnion` (gated). NB a *project* type conforming to an *external* protocol is already handled soundly (`Driver.swift:454-475`: unmodeled → `Unknown`, Fluent `Model` → Db) — a different shape. | manual `CANDOR_DEPS` today |
| **candor-rust** | ✓ `--deps` | confirm | trait-object dispatch heavily handled (R32–R44, bounded CHA); assess the cross-crate-trait shape against the 2-package test — likely the same precise-effect roll | ✓ `--deps` (Cargo) |
| **candor-java** | ✓ (§2) | confirm | **N/A** — the bytecode engine is typically given the whole classpath, so cross-module interface dispatch resolves natively (it sees every `invokeinterface` target's class) | classpath, not a flag |

The empirical result on a 2-package fixture (protocol in a dep, effectful conformer, consumer calling the
protocol method): **both** ts and swift read the consumer call **PURE** when the dep is unchained, and both
now disclose the **precise chained effect** with `interfaceUnion` + the dep report chained. So this was a
genuine silent-pure hole in the source engines (each reached it through a different resolution path — ts keys
the chain lookup on the bodyless interface method signature; swift on an unresolved external-protocol
receiver), not merely a precision gap. The bytecode engine (java) sidesteps it by seeing all classes.

Rollout: `interfaceUnion` field + `--workspace`/`--deps` convention pinned here and in conformance PART 18
(done for ts+swift); rust is the remaining source-engine roll (trait-union entries), java is N/A. The
empirical test for any engine: a 2-package fixture — a consumer calling an interface/protocol method whose
declaration comes from a chained dep must resolve to the union entry's effect (not read pure).

## Measured value

ukri-tfs (a real TypeScript microservice monorepo), `--workspace` across 11 services: **+545 functions
disclosed** that previously read pure (1396 → 1941), every service gaining. Verified sound — dominated by
precise concrete-class chain resolutions (`getUserByTfsId → client.get('/users/…') → Net`), not the union
over-approximation. The lesson: **per-package scanning of a monorepo is a systematic under-report multiplier**
— chaining is load-bearing, not a nicety.
