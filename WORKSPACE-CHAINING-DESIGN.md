# Workspace report chaining — cross-package interface dispatch (design)

*Status: PROTOTYPE in candor-ts (spec 0.22 line, `--workspace`, gated). This document specs the
`interfaceUnion` report field, the `--workspace` discovery flag, and the cross-package-interface-dispatch
rule, and records the four-way rollout plan. Not yet a floor rung — it becomes one when ≥2 engines ship it
and conformance pins it (the ladder discipline, [[candor-versioning-ladder]]).*

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

**The key finding: the *silent-pure* version of this gap was UNIQUE to candor-ts.** The other source engines
already **disclose** for unresolved cross-package dispatch rather than reading pure — so for them the
`interfaceUnion` is a *precision* upgrade (a disclosed `Unknown` → the precise chained effect), not a
soundness fix.

| engine | chaining infra | `invisible` through chain | cross-pkg interface/protocol dispatch — posture | discovery flag |
|---|---|---|---|---|
| **candor-ts** | ✓ (§2) | ✓ (added here) | WAS **silent-pure** (a cardinal sin) → **FIXED** via `interfaceUnion` (gated) | ✓ `--workspace` |
| **candor-swift** | ✓ (Deps.swift) | ✓ (already) | **SOUND** — an unmodeled external protocol's member is disclosed `Unknown` (`Driver.swift:454-475`, `why: dispatch:Sup.member`), never silent-pure; a MODELED external protocol (Fluent `Model` CRUD → Db) is classified. `interfaceUnion` would only sharpen `Unknown`→precise. | manual `CANDOR_DEPS` today |
| **candor-rust** | ✓ `--deps` | confirm | trait-object dispatch is heavily handled (R32–R44, bounded CHA); an unresolved cross-crate trait call discloses Unknown per the same never-silent posture — assess for the precise-effect upgrade | ✓ `--deps` (Cargo) |
| **candor-java** | ✓ (§2) | confirm | **N/A** — the bytecode engine is typically given the whole classpath, so cross-module interface dispatch resolves natively (it sees every `invokeinterface` target's class) | classpath, not a flag |

Why ts was the outlier: it leans on the TS type checker to type the receiver, then keys the chain lookup on
the *interface method signature* (no body → no entry → the join missed → **pure**). swift/rust reach an
unresolved external dispatch through their own name/CHA resolution and fall to the **never-silent** `Unknown`
default instead. So the rung's soundness value was ts-specific and is **shipped**; the four-way roll is the
optional precision arm (turn a disclosed `Unknown` into the exact chained effect where a dep report exists).

Rollout: pin the `interfaceUnion` field + `--workspace`/`--deps` convention here (done); the precision roll to
swift/rust is promoted to a floor rung only if/when it earns its keep on a real corpus (an `Unknown`-heavy
monorepo where the precise effect materially changes a gate) and conformance pins it. The empirical test for
any engine: a 2-package fixture (interface in a dep, impl reaching an effect, consumer calling the interface
method) — a SOUND engine discloses (`Unknown`/`invisible`/effect), never pure; `interfaceUnion` upgrades a
disclosed `Unknown` to the precise effect.

## Measured value

ukri-tfs (a real TypeScript microservice monorepo), `--workspace` across 11 services: **+545 functions
disclosed** that previously read pure (1396 → 1941), every service gaining. Verified sound — dominated by
precise concrete-class chain resolutions (`getUserByTfsId → client.get('/users/…') → Net`), not the union
over-approximation. The lesson: **per-package scanning of a monorepo is a systematic under-report multiplier**
— chaining is load-bearing, not a nicety.
