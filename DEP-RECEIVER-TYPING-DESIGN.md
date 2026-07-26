# Design: the untyped cross-package receiver

The last structural item in [the scan-boundary vein](SOUNDNESS-VEIN-crossing-the-scan-boundary.md). It blocks
three queue entries at once — rust **R5**, swift's **factory-bound receiver**, java's **dep-interface-typed
dispatch** — and all three have been correctly diagnosed as "needs a report-format extension". This document
argues that the format extension is the *second* half of the fix, that the first half needs no format change
at all, and that doing them in that order is what keeps the cardinal sin off the table while the slower half
is negotiated four-way.

## The shape, reduced to a fixture

```rust
// deplib                                     // app, with deplib's report chained
pub struct Client;
impl Client {
    pub fn fetch(&self) -> String {           pub fn go() -> String {
        std::fs::read_to_string("/etc/x")…        let c = deplib::build();
    }                                             c.fetch()
}                                             }
pub fn build() -> Client { Client }
```

Measured, `candor-scan 0.23.1`:

```
dep report:   deplib#Client::fetch  ['Fs']      <- the answer is right there, under the right key
consumer:     go  ABSENT FROM THE REPORT        <- reads PURE
              coverage: null    analyzed: 1
```

Two details make this the sharpest remaining instance rather than one more miss.

**`coverage: null`.** The crate is *covered* — it has a chained sibling report — so no hedge attaches, and
correctly so under §2 rule 3. This is not softened by the coverage-granularity fix
([COVERAGE-GRANULARITY-FINDING.md](COVERAGE-GRANULARITY-FINDING.md)); that repair addresses a different arm.
The report makes a **confident purity claim** about a function that performs `Fs`.

**`analyzed: 1`.** Under the ⟨0.21⟩ completeness manifest the function is counted as analyzed while being
absent from `functions`, so its absence is a positive claim rather than a gap.

## The distinction the engines do not currently draw

There are two ways a chained lookup comes back empty, and they carry opposite evidential weight:

| | what happened | what it licenses |
|---|---|---|
| **keyed-and-missed** | the engine formed the key `deplib#Client::fetch` and the dep's report has no entry | a genuine purity claim — the dep's report omits pure functions, so absence IS its honest answer (§2 rule 3) |
| **could-not-form-a-key** | the engine never typed `c`, so no lookup happened at all | **nothing.** No question was asked; silence is not an answer |

Every engine currently treats both as the first. That is the defect, and it is a *disclosure* defect before it
is a resolution one. The distinction is available today, in every engine, with no format change: an engine
always knows whether it formed a key.

### CORRECTION — the binary above is wrong, and three engines found the same third case

The table has two rows; there are three. Implementing half 1 in rust, java and ts produced three *different*
triggers, and the reason is that "could-not-form-a-key" was the wrong generalisation:

| | what happened | licenses a purity claim? |
|---|---|---|
| **keyed-and-missed** | the key was formed and names something that *could* have had a body | **yes** — the dep's report omits pure functions, so absence is its honest answer (§2 rule 3) |
| **could-not-form-a-key** | the receiver was never typed, so no lookup happened | no — no question was asked |
| **keyed-but-unanswerable** | the key WAS formed, but it names a **declaration that can have no body** — an interface method, an `abstract` member, a type-literal or property signature | no — absence under that key is *structurally guaranteed*, so it carries no information at all |

The third row is the one that matters in practice, and it is where **java** and **ts** both landed while rust
landed on the second:

- **rust** has genuinely untyped receivers (`let c = deplib::build()` — a pure factory is absent from the
  report, so no return type travels). Row 2.
- **java** has no untyped receiver at all: bytecode always carries a static owner. Its conjunct is the
  **opcode** — `INVOKEINTERFACE` *proves* the site names a declaration the JVM will never run, while
  `INVOKEVIRTUAL` on a dep class usually names the body itself, so a miss there is a real purity claim. Row 3.
- **ts** *refuted the canonical fixture*: return types travel in the `.d.ts`, so `build()` types `c`, the key
  is formed and the join succeeds — `go` gets `Fs` precisely. Every genuinely-untyped variant (`any`, no
  typings, untyped `require()`) *already* disclosed. What was silent was one level up: a receiver typed to an
  **abstraction**. Row 3, reached from the opposite direction.

**The unifying rule, and the one to implement:** *absence under a key licenses a purity claim only if the key
names something that could have had a body.* Both other rows are the same failure — treating the absence of
an answer as an answer.

This is why the ts refutation was worth more than a ts fix would have been on its own. Being told the
canonical shape does not reproduce is what forced the generalisation; had ts simply implemented row 2, all
three engines would have shipped and the actual rule would still be unstated.

## Half 1 — disclose the unformed key (no format change, no four-way negotiation)

**Rule.** When a call's receiver could not be typed, AND the receiver's value is bound (directly or
transitively) from a call into a **chained package**, the calling function MUST disclose rather than drop.

`Unknown` with a reason class is the natural spelling where the engine has one; `invisible: [pkg]` is
acceptable where the miss is better described as an unseen surface. Either satisfies H; silence does not.

**Why it does not flood.** The trigger is not "untyped receiver" — that is pervasive and hedging on it would
be the false-uncertainty failure that [the coverage finding](COVERAGE-GRANULARITY-FINDING.md) measured at
8–25% of all functions. The trigger is the conjunction: untyped receiver **and** provenance in a chained
dependency. In the fixture, the engine knows `c` came from `deplib::build()` — it recorded the call — it
simply does not know what type came back. That is a narrow, evidence-backed trigger, and the engine already
has both facts in hand.

**Why this is worth doing first even though half 2 supersedes it.** Half 2 needs a spec rung and agreement
across four engines. Half 1 converts a cardinal sin into a disclosed gap in each engine independently, on its
own schedule. Standing-bar item 6: *honest beats silent* — a disclosed `Unknown` is a valid and valuable fix,
not a placeholder. And when half 2 lands, half 1 does not become dead code: it remains the **fail-closed
floor** for every receiver half 2 still cannot type (a trait object built by a third crate, a type whose
factory the dep did not export).

**Measurement gate.** Per engine, before shipping: A/B on real code, count the functions that gain a hedge,
and trace a sample to a genuine unformed key. If the count is large, the trigger has been implemented as
"untyped receiver" rather than as the conjunction — that is the predicted failure mode, so check it
specifically rather than accepting the number.

### A THIRD conjunct, found by measuring — the dep must be CHAINED

Implemented first in rust (`5fde0d6`), and the two-conjunct version above is **not** what shipped. It fired
on `let finds = candor_classify::best_finds(); finds.first()` — a std `Vec` method on a dep-returned value.
Genuinely an unformed key, and genuinely not worth a disclosure, because for an **unchained** crate the κ
ledger *already* discloses `invisible: [cr]`. The reader is warned; a second disclosure is pure false
uncertainty.

It is exactly when the crate **is** chained that the ledger correctly falls silent — the crate is covered
under §2 rule 3 — and the silence becomes the confident purity claim this rung exists to prevent. That is
also why the fixture reads `coverage: null`: the absence of a hedge is not an oversight, it is the covered
claim, and it is right about every call except the one no key was formed for.

So the trigger is: **untyped receiver AND dep provenance AND the dep is chained.** Measured cost in rust
after the third conjunct — 0 changes on three unchained corpora, and on a chained scan 1 new source plus 4
transitive callers of it. Other engines should expect to find the same third conjunct rather than rediscover
it: check where your own coverage ledger already speaks before adding a second voice. Confirmed in ts
(0 changes on 10 unchained real targets) and in java (twelve unchained jars byte-identical).

### What it means where the receiver is always typed (ts, `420e715`) — the fixture above REFUTES

The fixture at the top of this document does not reproduce in candor-ts, and that is the finding rather
than an obstacle to one. Return types travel in the `.d.ts`, so `build()` types `c` to `Client`, the key
`depkit#Client.fetch` is formed, and the join succeeds. The receiver ts genuinely *cannot* type is `any`,
which already read `callback:` Unknown. Both halves of the rust shape are absent.

The rung still bites, one level up: a receiver typed to an **abstraction** — an interface method or
property signature, an anonymous type-literal member, an `abstract` member. No *body* is hashed under that
name in the dependency, whatever its implementations do, so `build(): Fetcher` against a report whose only
body is `pkg#Client.fetch` produces a key that is formed and can never be answered — by that report or any
other. Measured, unchained 0/10 targets changed; chained, 5 gains over ~1000 analyzed functions on five
monorepo services (8/202 and 3/453 with producer-side `interfaceUnion` entries stripped), every one traced
to a real implementor or to a member installed at runtime by `fastify.decorate(…)`.

One layering note that generalises: ts's `interfaceUnion` emitter *declines* to emit when an interface name
is declared twice in a package (never guess which one). That refusal is right, and before half 1 it left
silence. **Half 1 is the fail-closed floor under every guard the resolution path is correct to refuse** —
which is the same reason it does not become dead code when half 2 lands.

### What "could not form a key" means in an engine with no untyped receivers (java, `828ca18`)

JVM bytecode always carries a static owner, so java has no untyped receiver to test for. The conjunct that
replaces it is the **opcode**: `INVOKEINTERFACE` *proves* the owner is an interface, so the hash formed at
the site names a declaration the JVM will not run — the key is unformed in exactly the sense that matters.
`INVOKEVIRTUAL` is excluded, because a plain dependency class usually IS the body and a miss there is a
genuine purity claim; the cost is that an abstract dependency CLASS receiver stays open, which is the
sharpest thing half 2 would buy java. The other departure is a **fifth** conjunct: the chained report must
demonstrably hold an effectful body with the same `name+desc` under another owner. Without it the hedge
lands overwhelmingly on interfaces whose every implementation in the dependency is a pure accessor.

The numbers are the argument for measuring rather than reasoning, and they reproduce this document's
prediction on a second engine: unresolved-receiver-into-a-chained-dep alone is **5.4%** of all analyzed
functions across nine chained JVM corpora (8.4% on logback-classic); + the opcode conjunct, 2.1%; + the
signature evidence, **0.49%**. Note that the fifth conjunct is a signature join, which "the trap this must
not walk into" below rejects — for RESOLUTION. Used purely as evidence to DISCLOSE, with nothing charged
and no edge formed, it is the behaviour that section prescribes; a collision costs one conservative Unknown
on a site that is genuinely unresolvable either way, and can never fabricate an effect.

## Half 2 — carry enough type surface to form the key

Only now does the format matter. Three observations bound what it needs to carry.

**A pure factory is absent from the report entirely.** Measured above: `build` returns `Client` and is pure,
so it is omitted, and no field added to *function entries* can help — there is no entry to put it on. This
kills the obvious `"returns"` field on a function entry as a complete answer, and it is the reason this item
has stalled. Any workable design must carry type surface **independently of the effect entries**.

**The information is small and public-API-shaped.** The consumer needs, for the dependency's *exported*
surface only: which type a function returns, and which interfaces/protocols/traits a type conforms to. Not
bodies, not fields, not private types.

**It only matters when it can change an answer.** If the returned type has no effectful and no
`Unknown`-carrying member anywhere in the dep's report, then typing `c` changes nothing — the lookup would
succeed and return pure, which is what silence already yields. So emission can be **bounded to types with at
least one non-pure member**, which is the same *precise-or-nothing, additive* discipline the engines already
apply to `interfaceUnion`.

### Sketch

A new OPTIONAL top-level envelope block, sibling to `coverage`, not attached to function entries:

```jsonc
"typeSurface": {
  "returns":    { "deplib#build": "deplib#Client" },      // fn hash -> returned type id
  "implements": { "deplib#Client": ["deplib#Fetcher"] }   // type id -> conformed interface ids
}
```

- **Omitted entirely** when nothing qualifies, so a default report stays byte-identical — the
  wire-compatibility rule that let ⟨0.23⟩'s `interfaceUnion` ride gated.
- **Bounded** to types having ≥1 non-pure member.
- `returns` closes rust R5 and swift's factory-bound receiver; `implements` closes java's dep-interface
  dispatch, which needs the dependency's hierarchy and nothing else.
- Consumers that ignore it behave exactly as today, which is what makes it tier-1 additive.

### ATTEMPTED AND REVERTED (2026-07-26) — read this before trying again

A full producer+consumer prototype was built in rust (`58ddff0`, `b98957f`) and **reverted**. It worked on
its fixture — the effect crossed the boundary and `deny Fs` went exit 0 → exit 1 — and a code review then
confirmed **four** defects in it, two of them soundness. The fixture passing is not the bar.

1. **It became the leaf-key join this document rejects.** Both ends collapsed the type to its bare leaf
   (`{crate}#{leaf}`), so `sync::Client` and `mock::Client` in one dependency are indistinguishable. A pure
   `mock_client()` factory published `deplib#Client`, and the consumer charged `sync::Client::send`'s `Net`
   to a caller that cannot reach it. I wrote the warning below and then implemented the thing it warns
   against, because "the type id" felt like a naming detail rather than the whole mechanism.
2. **`returns` is the UNWRAPPED success type.** `record_return` applies `unwrap_result_option`, so
   `fn connect() -> Result<Conn, E>` publishes `Conn`. The consumer's binding is a `Result`; method calls on
   it were keyed against `Conn`. `c.map(…)` charges `Conn::map`'s effects (fabrication) and the far more
   common `c.unwrap()` misses and — see 3 — reads pure.
3. **It removed half 1's fail-closed floor.** On a `returns` hit followed by a `by_key` miss the branch
   `continue`d, treating it as keyed-and-missed. But `by_key` deliberately DROPS ambiguous keys ("never
   guess"), so the case where the dependency index *refuses to answer* was read as *the dependency claims
   purity*. That is precisely where this document says half 1 must remain the floor, and the code did the
   opposite.
4. **It dropped `incomplete` and `dep_invisible`** that the main join propagates, so a literal `tables`
   surface inherited across it read as complete.

**Requirements for a second attempt**, all of them from the above rather than invented:
- Type identity must be **fully qualified** — the module path is load-bearing, not cosmetic. If the id
  cannot be made unambiguous, the rung is not ready.
- The published return type must record **wrapper provenance** (`Result`/`Option`/etc.) or the consumer must
  refuse to key through it.
- A `by_key` miss after a `returns` hit must **fall back to half 1's disclosure**, never to silence, unless
  the index can distinguish "no such entry" from "I dropped an ambiguous entry".
- It must carry every surface the main join carries.
- The producer's own emission must be measured on a MODULAR crate. An earlier bug here published module
  names as types and was invisible on a flat fixture; the counts (`returns` size vs published size) are the
  diagnostic, not the output.

### Which engine needs WHICH field — settle this before implementing again

The sketch above bundles `returns` and `implements` into one block, which reads as one rung. Checked against
what each engine actually cannot do locally, they are **two independent rungs with different constituencies**,
and one of them has a constituency of zero for its motivating case:

The table below is the ORIGINAL reading, kept because the corrections underneath it are the finding. Read the
`implements` column as **struck through**: it is redundant in every row, and both cells that carried it were
wrong for the same reason — the engine was measured with the `interfaceUnion` producer switched OFF.

| engine | needs `returns`? | ~~needs `implements`?~~ | why |
|---|---|---|---|
| rust | **yes** | no | a pure factory is absent from the report, so no return type travels (R5) |
| swift | **yes** | ~~yes~~ → **no** | the factory case (row 2) is real and is `returns`. Row 3 was recorded as needing the hierarchy — measured 2026-07-26 with the dep scanned under `CANDOR_WORKSPACE_CHAIN`, `go(_ s: any Store)` resolves to `['Fs']` through the union entry, unprompted. The row-3 fixture had scanned the dependency without the flag. |
| java | no | ~~yes~~ → **no** | bytecode always carries a static owner, so return types are never the problem; and the dep-interface case needs the implementer SET, not the hierarchy — the union publishes exactly that, under the key an INVOKEINTERFACE site already forms |
| ts | **no** | no (a `dist`-shipped package is a producer-side residual, not a field) | return types already travel in `.d.ts` — ts REFUTED the factory probe outright |

Two consequences worth acting on:

1. **Ship them separately** — which is what made the second consequence findable at all. `returns` served
   rust+swift and `implements` served java+swift, and bundling would have meant the rung could not land until
   both were agreed four ways. Splitting them put `implements` on its own, where one experiment could kill it.
2. **`implements` IS REDUNDANT — measured 2026-07-26, and the rung comes off the queue.** The experiment
   was one hand-edited dep report. candor-java's consumer, with NO code change:

       natural dep report (lib/FileStore.save only)
         app.Go.run  ->  Unknown[dispatch:lib.Store.save]      (half 1's disclosure)
       + one `interfaceUnion`-shaped entry, hash lib/Store.save(Ljava/lang/String;)V
         app.Go.run  ->  ['Fs']                                 RESOLVED

   Java keys its report entries by `owner.name+desc`, which is *exactly* the key its consumer forms for an
   `INVOKEINTERFACE` site — so a union entry lands where the join already looks. No hierarchy encoding, no
   new field, no consumer work.

   **What was actually missing is a PRODUCER — now SHIPPED (2026-07-26).** candor-java was marked N/A for
   conformance PART 18 on the grounds that "whole-classpath bytecode resolves cross-module dispatch
   natively". That is true of an unchained whole-classpath scan and false of a chained one, where the
   dependency is not on the classpath — the same "ask separately what an engine does at the BOUNDARY" lesson
   the initializer-edge vein taught. candor-java now emits the union entries under `CANDOR_WORKSPACE_CHAIN`
   and PART 18 runs **four-way**; nothing new was designed and the consumer was untouched.

   Measured, and the numbers are the argument for the rung rather than for the field:
   - flag OFF, twelve real jars: reports **byte-identical** to the pre-change engine, byte for byte.
   - flag ON, the same twelve: **+0.9% to +14.8% entries**, all `interfaceUnion`, ordinary entries untouched.
     The dominant filter is the empty-union skip (jackson-databind: 198 candidate interface methods, 161
     pure across every implementer, 36 emitted) — the rung publishes the effectful minority, not a mirror
     of the type surface.
   - six chained library pairs, 21 922 analyzed functions: **65 effect gains, 0 effect losses**, 7 half-1
     `Unknown`s resolved to a precise effect, 10 functions newly disclosing `Unknown` (traced: httpcore's
     `Cancellable.cancel` implementers are themselves unresolved, so the union publishes that honestly and
     httpclient's `abort()` stops claiming a complete set).
   - traced gains: okio `BufferedSink.flush`/`BufferedSource.inputStream` → `RealBufferedSink`/
     `RealBufferedSource` (okhttp's `ResponseBody.byteStream` and every `WebSocketWriter.write*`);
     httpcore `HttpClientConnection.flush` → `DefaultBHttpClientConnection` (`Net`) reaching httpclient's
     three connection adapters.

   One guard was written and then REMOVED after measuring, which is the part worth carrying: "emit only for
   an interface with at least one local subtype" changed **not one entry** across the twelve jars, and the
   single shape where it did fire — an interface re-abstracting a method whose only body is a
   super-interface `default` — is a genuinely runnable body an external implementer inherits. The guard was
   an under-report wearing a bound's clothes. `chaTargets` returning nothing is what actually delivers
   "nothing implements it, so nothing is published".

   This also resolves **swift row 3** and the java dep-interface item without `implements`: both need the
   dependency's implementer set, and that is what the union publishes. **Swift needs no work at all** —
   measured, it already EMITS the union entry under `CANDOR_WORKSPACE_CHAIN=1` and its consumer resolves
   row 3 to the real effect. The earlier "row 3 is not fixable locally" finding was measured on a dependency
   scanned without that flag: an engine that had not been asked, mistaken for one that could not answer. `returns` is unaffected and remains
   the one genuinely new field, wanted by rust and swift only.

### BLOCKING PREREQUISITE, found by designing rather than coding (2026-07-26)

Requirement 1 says type identity must be **fully qualified**. Checked against the consumer's actual index,
that is not currently expressible:

    crates/candor-scan/src/deps.rs — by_key holds exactly two key shapes per entry
        "{krate}#{leaf}"      e.g.  deplib#fetch
        "{krate}#{tail2}"     e.g.  deplib#Client::fetch

There is **no full-qualified key**. So a consumer cannot look up `deplib#sync::Client::fetch` even if the
producer published that exact string — the index has never held it. This is *why* the first attempt
collapsed to a leaf: not carelessness, but the only key shape the lookup could answer. Publishing a
qualified id against a tail2 index would simply miss every time, which is the silent direction.

**So the rung has a prerequisite, and it is additive and independent:**

0. **The dep index must carry the FULL qual as a third key** — `"{krate}#{qual}"`. Purely additive: existing
   leaf/tail2 lookups are untouched. This is worth landing and testing ON ITS OWN, before any
   `typeSurface` work, because it is useful independently (any join that knows a precise target can then ask
   for it exactly instead of settling for tail2) and because bundling it would hide its own regressions
   inside a bigger change.

   **LANDED — candor-rust `5feba18`, and it corrected two of this note's own claims.**

   - *"Purely additive"* is only true **with a dedup**, and that is the whole safety argument. For a 1- or
     2-segment qual the full qual **IS** the leaf or tail2 string, so an undeduped third push self-collides
     and the never-guess rule REMOVES a key that worked before — a silent under-report manufactured by an
     additive change. The additive claim was verified in both directions (against a mutant with the dedup
     deleted, `deplib#Root::only` disappears) and by measurement: keys present before and absent after = 0
     across 90k dep entries in three chained trees. A ≥3-segment full qual can never collide with another
     entry's leaf (1 segment) or tail2 (2 segments), so no pre-existing key is at risk.
   - *"A full qual is unique within a crate by construction"* is **false, measured.** pgman: 1865 of 17861
     new keys go ambiguous, full-qual against full-qual. Traced to byte-identical DUPLICATE entries for one
     function (anyhow `error::Error::as_ref`, same loc, same effects) that the scanner emits once per
     cfg-gated impl. Pre-existing — the leaf/tail2 keys for those functions were already dropped by the same
     duplicates. So requirement 3 below is not belt-and-braces: an exact-key miss genuinely cannot
     distinguish "no such method" from "the index withdrew an entry", and must fall back to disclosure.

Only then does the rest become implementable:

1. producer publishes `returns: { "cr#<full fn qual>": "cr#<full type path>" }`;
2. consumer forms `cr#<full type path>::<method>` and looks up the **exact** key;
3. a miss falls back to half 1's disclosure — never to silence, because a miss on an exact key still cannot
   distinguish "no such method" from "the index withdrew an ambiguous entry";
4. the join applies **every** surface, via the one shared application path rather than a second copy of it.
   candor-java shipped this rung's sibling with `crossDepJoin` duplicating `inheritDepFn` line for line, and
   the copies drifted until a reason-scoped gate was inert on the ordinary call path (`6ab26e4`). Rust
   should be checked for the same duplication BEFORE adding a third consumer of a DepFn.

   **AUDIT DONE — candor-rust `7cb5748`, and rust had THREE copies which had drifted the same way.** In the
   DISCLOSURE surfaces this time: the cross-crate drop-glue join carried effects + paths only; the dep-lazy
   join carried no `invisible` and no `incomplete`. A join that carries the effect and drops the
   `incomplete` beside it lets a benign literal in the CONSUMER certify a surface the dependency already
   declared uncertifiable — the masking evasion, reintroduced one join site over. All three now call
   `apply_dep_fn`. **The A/B was 0 deltas on all three corpora** — none of them exercises the drop or lazy
   site, so no corpus diff could ever have shown this (standing-bar item 8); the fixture, one distinct value
   per surface per site, is the evidence.

**The order matters more than the content.** Every defect in attempt 1 was design content discovered while
coding. Prerequisite 0 is the same class of discovery, found this time by reading the index before writing
the emitter — which cost one grep instead of a revert.

### The trap this must not walk into

A leaf-name join (`M#fetch` — match on the method name alone, ignore the receiver type) was already
considered and **rejected** for exactly this problem: leaves as generic as `write`, `run` or `send` would
fabricate on unrelated receivers. `typeSurface` exists precisely so the key can be formed *correctly* rather
than guessed. If an implementation finds itself matching on a leaf because the type surface was absent, the
correct behaviour is half 1 — disclose — not a widened match. **Never trade the cardinal sin for its mirror.**

### Open questions, not yet decided

- **Type identity across engines.** `hash` is already "a stable identity (e.g. DefPathHash, `pkg#LocalName`)"
  and deliberately engine-chosen. Type ids need the same latitude, and PART 18's experience suggests the
  four-way agreement is the expensive part, not the emission.
- **Generic returns.** `fn build<T>() -> Wrapper<T>` — is the id `deplib#Wrapper`, and is that precise enough
  to be useful, or precise enough to be wrong? Unresolved; a first implementation should emit nothing here
  and let half 1 cover it.
- ~~**Whether `implements` duplicates `interfaceUnion`.**~~ **SETTLED 2026-07-26 — it does, and `implements`
  is dropped.** `interfaceUnion` publishes the *effect union*; `implements` publishes the *hierarchy*. java's
  dep-interface case was the test, and once candor-java emitted the union entries it resolves precisely with
  no hierarchy encoding and no consumer change. `returns` remains the one genuinely new field, wanted by rust
  and swift only.

## Order of work

1. **Half 1, per engine, independently.** Each engine's own schedule; no rung, no negotiation. Measure the
   hedge count and check the trigger is the conjunction, not the disjunct. Done: rust `5fde0d6`, java
   `828ca18` (candor-java), ts `420e715` (candor-ts). Open: swift.
2. **Conformance part** pinning that an untyped cross-package receiver DISCLOSES rather than reads pure —
   verified-to-catch by reverting one engine, as PARTs 19 and 20 were. **Done, PART 21**, three arms live
   (java, rust, ts), each verified to catch against its own pre-fix engine.
3. **Half 2** as a spec rung, once half 1 has removed the urgency and the type-identity question has been
   settled against a real four-way implementation rather than in the abstract.

The ordering is the point. Half 2 is the better fix and half 1 is the one that stops the report lying while
half 2 is negotiated.
