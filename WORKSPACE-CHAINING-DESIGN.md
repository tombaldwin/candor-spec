# Workspace report chaining — cross-package interface dispatch (design)

*Status: SHIPS on ALL FOUR engines — candor-scan (rust) + candor-ts + candor-swift, and since 2026-07-26
candor-java (spec 0.23 line, gated behind `CANDOR_WORKSPACE_CHAIN`); conformance **PART 18** pins the field +
the cross-package resolution four-way (the ladder discipline, [[candor-versioning-ladder]]). This document
specs the `interfaceUnion` report field, the `--workspace` discovery flag, and the
cross-package-interface-dispatch rule.*

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

In candor-ts/swift a consumer resolving `ch.publish()` on an `I`-typed receiver already keys the chain lookup
on `pkg#I.m`, so **no consumer-side change is needed** — the union entry is what the existing lookup was
missing. candor-scan (rust) additionally needed a small consumer fix: an external `&dyn Trait` dispatch was
formerly DROPPED (its impls are in another crate, so in-crate CHA found nothing), so the consumer now emits a
`use`-resolved crate-qualified `Call` (`dep::Trait::method`) that the chain then joins on `dep#Trait::method`.

**2. `invisible` travels through the chain (consumer side).** A chained dep function's own blind boundary
(an uncovered package IT calls into) must reach the consumer as **its** `invisible` — else a sibling's
`SnsTopic.publish → invisible:[@aws-sdk/client-sns]` reads pure across the edge. (candor-swift already does
this; candor-ts gained it with this work; candor-rust's `DepFn.invisible` + the external-`&dyn` consumer
resolution disclose it as `invisible:[crate]` even unchained.)

**3. `--workspace` auto-discovery (ergonomics).** `candor <target> --workspace` (alias `--deps`) discovers the
target's **symlinked** monorepo dependencies (a workspace link points OUT of `node_modules`/the module dir to
the package's real source; a published dep is a real dir), scans each into `.candor/deps/` with `interfaceUnion`
emission enabled, and chains them — the source-engine analog of rust `--deps` (which scans the Cargo.lock
tree). **Transitive**: deps are re-scanned WITH the accumulating deps dir chained, to a monotone fixpoint, so
a dep's calls into *its own* workspace deps resolve too.

## Gating

`interfaceUnion` emission is **opt-in** across all three source engines (env `CANDOR_WORKSPACE_CHAIN`, set by
`--workspace` on the child scans) so a **default** scan stays byte-identical — four-way conformance is
unaffected, and PART 18 exercises the emission only under the flag. A load-bearing sub-fix rode along, ungated because it is pure correctness: a **workspace-symlinked**
dep's real path has no `node_modules/` segment, so module-name resolution must walk up to the nearest
`package.json` `name` — otherwise a monorepo dep's effects are mis-keyed (an unmatchable chain key AND an
ugly `invisible:[/abs/path]`).

## Four-way status & rollout

`interfaceUnion` now SHIPS on **all four** engines (candor-java + candor-scan + candor-ts + candor-swift),
pinned by conformance PART 18; recorded as spec rung **0.23**. candor-java was recorded N/A here — "whole-
classpath bytecode resolves cross-module dispatch natively" — which is true of an UNCHAINED whole-classpath
scan and false of a CHAINED one, where the implementer is in the other tree. Its consumer needed no change:
it keys entries by `owner.name+desc`, exactly the key an INVOKEINTERFACE site forms, so a union entry lands
where the join already looks; only the PRODUCER was missing.

| engine | chaining infra | `invisible` through chain | cross-pkg interface/protocol dispatch | discovery flag |
|---|---|---|---|---|
| **candor-ts** | ✓ (§2) | ✓ (added here) | WAS **silent-pure** → **FIXED** via `interfaceUnion` (gated) | ✓ `--workspace` |
| **candor-swift** | ✓ (Deps.swift) | ✓ (already) | WAS **silent-pure** for an external-protocol-typed receiver (an interface method on a value whose protocol is imported from a chained package read PURE) → **FIXED** via protocol-CHA `interfaceUnion` (gated). NB a *project* type conforming to an *external* protocol is already handled soundly (`Driver.swift:454-475`: unmodeled → `Unknown`, Fluent `Model` → Db) — a different shape. | manual `CANDOR_DEPS` today |
| **candor-rust** | ✓ `--deps` | ✓ | WAS **silent-pure** for a `&dyn ExternalTrait` call (its impls live in another crate, so in-crate CHA found nothing and dropped it) → **FIXED**: trait-CHA `interfaceUnion` producer entries + a consumer that emits a crate-qualified `Call` for an external-`use`-resolved trait so the chain resolves (unchained it now discloses `invisible:[crate]`, was pure). A/B on syn/serde_json/h2: +80 recoveries, 0 fabrication. | ✓ `--deps` (Cargo) |
| **candor-java** | ✓ (§2) | ✓ | WAS recorded **N/A** ("the whole classpath resolves it natively") — true UNCHAINED, false at the boundary: split the trees and chain the dep report and `s.save()` on a dep-declared `Store` reads `Unknown[dispatch:…]` (half 1) rather than the effect, because the body is keyed `lib/FileStore.save` and the site keys `lib/Store.save`. → **FIXED** producer-side: interface-CHA `interfaceUnion` entries (gated). The CONSUMER needed no change — entries are keyed `owner.name+desc`, exactly the INVOKEINTERFACE key. A/B on twelve real jars: report byte-identical with the flag off; six chained library pairs, 65 effect gains, 0 effect losses. | classpath, or `--deps` |

The empirical result on a 2-package fixture (interface/protocol/trait in a dep, effectful impl, consumer
calling the method): **all three source engines** read the consumer call **PURE** when the dep is unchained,
and all three now disclose the **precise chained effect** with `interfaceUnion` + the dep report chained.
candor-java's chained arm reached `Unknown[dispatch:…]` rather than pure (half 1 already covered it) and now
reaches the precise effect too. So
this was a genuine silent-pure hole in every source engine — each reached it through a different resolution
path (ts keys the chain lookup on the bodyless interface method signature; swift on an unresolved
external-protocol receiver; rust drops an external-`&dyn` dispatch because its impls are in another crate) —
not merely a precision gap. The bytecode engine (java) sidesteps it by seeing all classes. HARD LESSON:
repo-reading one engine's resolution path (e.g. swift's project-conforms-to-external handler) mis-scoped the
gap as precision-only; the 2-package empirical fixture is the honest oracle — and all three source engines
read it pure.

Rollout: DONE for all four engines — `interfaceUnion` field + `--workspace`/`--deps` convention pinned
here and in conformance PART 18 (candor-scan trait-union + cross-crate `&dyn` consumer resolution, candor-ts
interface-union, candor-swift protocol-union, candor-java interface-CHA union), recorded as spec 0.23. The empirical test for any
engine: a 2-package fixture — a consumer calling an interface/protocol/trait method whose declaration comes
from a chained dep must resolve to the union entry's effect (not read pure). Remaining follow-ons: a
`--workspace` ergonomics flag for candor-swift now exists (parses `.package(path:)`); candor-java has
`--deps` rather than `--workspace`. Open: publish the 0.23 line.

## Measured value

ukri-tfs (a real TypeScript microservice monorepo), `--workspace` across 11 services: **+545 functions
disclosed** that previously read pure (1396 → 1941), every service gaining. Verified sound — dominated by
precise concrete-class chain resolutions (`getUserByTfsId → client.get('/users/…') → Net`), not the union
over-approximation. The lesson: **per-package scanning of a monorepo is a systematic under-report multiplier**
— chaining is load-bearing, not a nicety.
