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
it: check where your own coverage ledger already speaks before adding a second voice.

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
- **Whether `implements` duplicates `interfaceUnion`.** They overlap. `interfaceUnion` publishes the *effect
  union*; `implements` publishes the *hierarchy*. If the union is always sufficient for the consumer's
  question, `implements` is redundant and should be dropped — java's dep-interface case is the one to test
  that against, since java is N/A for PART 18 and so has never exercised the union path.

## Order of work

1. **Half 1, per engine, independently.** Each engine's own schedule; no rung, no negotiation. Measure the
   hedge count and check the trigger is the conjunction, not the disjunct.
2. **Conformance part** pinning that an untyped cross-package receiver DISCLOSES rather than reads pure —
   verified-to-catch by reverting one engine, as PARTs 19 and 20 were.
3. **Half 2** as a spec rung, once half 1 has removed the urgency and the type-identity question has been
   settled against a real four-way implementation rather than in the abstract.

The ordering is the point. Half 2 is the better fix and half 1 is the one that stops the report lying while
half 2 is negotiated.
