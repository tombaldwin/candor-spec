# Coverage granularity: what "one resolved call clears the blind marker" actually is

Characterisation of the cross-cutting item in
[SCAN-BOUNDARY-WORK-QUEUE.md](SCAN-BOUNDARY-WORK-QUEUE.md), recorded there as:

> **Coverage granularity.** Package/crate-granular coverage means one *resolved* call clears the blind
> marker for every call shape into that dependency, so chaining removes a hedge that would otherwise have
> flagged these. Present in all four engines. Does not cause the misses; makes them confident.

**Verdict: the item is one true claim wearing three others' clothes.** Coverage *is* package-granular in
all four engines, but it is decided by three different mechanisms with three different confidence bases,
and only one of them is a defect. Split apart and measured:

| arm | what makes a package "covered" | engines | is it a defect? | blast radius if fixed |
|---|---|---|---|---|
| **A — dynamic** | the scan classified ≥1 call into it | **rust, java** | **YES** — an unvouched proxy for coverage, and it silently voids a stance the source comments state explicitly | java **2.3%** of methods on the worst corpus; rust **0** (structurally ≈inert) |
| **B — curated** | the package name is on a reviewed list | all four | no — SPEC §7 item 14 exempts it by name, backed by review | rust **8–14%**, java **15–25%** of all analyzed functions — **not adoptable** |
| **C — chained** | a sibling report was loaded for it | all four | no — SPEC §2 chaining rule 3 mandates it | ts 2 fns; the real residual is a *join* defect, not a granularity one |

**Recommendation: fix arm A only, in rust and java. Leave B and C alone.** Detail in §5.

Everything below was reproduced this session against `candor-scan 0.23.1` (rebuilt from `50218e3`),
`candor-java 0.23.1-all` (`b891d5f`, single jar, version checked), `candor-ts` at `8eba3af` run from
`~/git/candor-ts`, and `candor-swift` rebuilt from `eae2de2`. Every arm's output directory was deleted
before the control was measured (standing bar item 7).

---

## 1. Where the marker lives, per engine

### rust — `crates/candor-scan/src/scan.rs`

```rust
// scan.rs:1249  the κ ledger, and the global blind set the per-fn `invisible` is filtered against
let mut coverage_ledger: Vec<(String, usize)> = dep_seen.iter().filter(|(cr, _)| {
        !dep_classified.contains(*cr)                                    // ← arm A
     && !deps_idx.crates.contains(…)                                     // ← arm C
     && !candor_classify::CALIBRATED_CRATES.contains(&cr.as_str())       // ← arm B
     && !candor_classify::PATH_CALIBRATED_CRATES.contains(&cr.as_str())
     && !candor_classify::CALIBRATED_PREFIXES.iter().any(|p| cr.starts_with(p))
})…
```

- arm A is set at `scan.rs:836` — `if classified.is_some() { dep_classified.insert(cr.to_string()); }`
  — and again at `scan.rs:1061` on a dep-report join hit. **Crate-wide, from one call site.**
- per-fn attribution: `scan.rs:1324` — `invisible` = the fn's transitive blind reach ∩ `global_blind`.
- floored calls are recorded per fn at `scan.rs:839` (`blind_direct`) — so the per-call-site datum
  **already exists**; it is the *global* filter that throws it away.

### java — `src/main/java/io/poly/candor/`

```java
// Candor.java:1717
if (!pkg.isEmpty() && !kappaCovers(pkg)) {              // ← arm B (Rules.java:646 prefix list)
    ctx.kappaSeen.merge(pkg, 1, Integer::sum);
    if (effect != null) ctx.kappaClassified.add(pkg);   // ← arm A: package-wide, from one call
    else ctx.blindDirect.computeIfAbsent(id, …).add(pkg);
}
// Candor.java:712  the ledger
.filter(e -> !ctx().kappaClassified.contains(e.getKey()) && !ctx().depCoveredPkgs.contains(e.getKey()))
// ReportWriter.java:100  per-method
List<String> invisible = blindAcc.getOrDefault(fn, …).stream().filter(globalBlind::contains)…
```

Same structure as rust, same discard of an already-computed per-call-site datum (`blindDirect`).

### ts — `scan.mjs` / `scan-core.mjs`

```js
// scan.mjs:1767 (chargeExternalDecl) and :2823 (the call arm) and :3224
if (!kappaKnows(pkg) && !depCoveredPkgs.has(pkg) && crossesPackageBoundary(file)) {
  unlistedSeen.set(pkg, (unlistedSeen.get(pkg) ?? 0) + 1);
  rec.blind.add(pkg);
}
// scan-core.mjs:234
export function kappaKnows(m) { return KAPPA_PURE.has(m) || KAPPA_RULES.some(([re]) => re.test(m)); }
```

**No arm A.** `kappaKnows` is a pure function of the package NAME; `depCoveredPkgs` is populated at report
LOAD time (`scan.mjs:527,531`), not by a resolution. Nothing a call site does can move a package from
uncovered to covered.

### swift — `Sources/candor-swift/`

```swift
// main.swift:526  the ledger
let unlisted = importCounts.filter { !PLATFORM_MODULES.contains($0.key) && !KAPPA_MODULES.contains($0.key)
    && !internalModules.contains($0.key) && !depsIndex.coveredPkgs.contains($0.key) }
// Driver.swift:383  the per-fn blind set, hoisted once, from the same predicate
```

**No arm A either**, and swift is *coarser* than the others in a different direction: its blind set is keyed
on the file's `import` list, not on calls.

---

## 2. Fixtures — arm A, the defect

### rust: CONFIRMED

`pnet_datalink` is the one real crate whose name `classify()` matches but which is absent from
`CALIBRATED_CRATES` / `PATH_CALIBRATED_CRATES` / `CALIBRATED_PREFIXES` — `pnet_datalink::channel` → `Net`,
everything else floors (`candor-classify/src/lib.rs:601`). Two arms, `list_ifaces` byte-identical in both:

```rust
// ARM A                                    // ARM B = ARM A plus:
pub fn list_ifaces() -> usize {             pub fn open_channel(i: &pnet_datalink::NetworkInterface) {
    let ifs = pnet_datalink::interfaces();      let _ = pnet_datalink::channel(i, Default::default());
    ifs.len()                               }
}
```

```
ARM A   coverage: {'uncovered': [{'name': 'pnet_datalink', 'calls': 1}]}
        fn fxr#list_ifaces  []  invisible=['pnet_datalink']      analyzed: 1
        stderr: "candor's classifier doesn't cover 1 dependency … pnet_datalink (1 call)"
        --gate-json (deny Db): ok=True  coverage={'uncovered':1,'packages':['pnet_datalink']}

ARM B   coverage: None                                            analyzed: 2
        fn fxr#open_channel ['Net'] invisible=None
        (list_ifaces is ABSENT from the report — no advisory, no coverage field)
        --gate-json (deny Db): ok=True  coverage=None
```

`list_ifaces` did not change. It goes from *"pure as far as candor could see, but it calls into a package
the classifier doesn't cover"* to **absent-from-report-with-`analyzed:2`** — which under ⟨0.21⟩ is not
silence, it is an affirmative **provably-pure** claim. The completeness manifest makes this arm *worse*,
not better: the hedge was the only thing stopping the omission from reading as a positive claim.

### java: CONFIRMED — and it contradicts a stance the source states in words

`org.apache.commons.io` is classified verb-precisely (`Classifier.java:516`, `:1097`) and is deliberately
**not** in `KAPPA_COVERED_PREFIXES`. `Rules.java:666-669` says why:

> NB `com.amazonaws` and `org.apache.commons.io` are CLASSIFIED … but deliberately NOT ledger-covered …
> An unmodeled member of either discloses `invisible` — the honest floor.

Arm A defeats that. Same two-arm fixture (`FilenameUtils.getName` floors; `FileUtils.readFileToString` → Fs):

```
ARM A   coverage: {'uncovered': [{'name': 'org.apache.commons.io', 'calls': 1}]}
        fn app/A.base(Ljava/lang/String;)Ljava/lang/String;  []  invisible=['org.apache.commons.io']
        analyzed: {'count': 2}   + the stderr advisory

ARM B   coverage: None                                        analyzed: {'count': 4}
        fn app/B.load(Ljava/io/File;)Ljava/lang/String; ['Fs'] invisible=None
        (app/A.base is ABSENT — the honest floor is gone, from an unrelated class in the same scan)
```

### ts: REFUTED

Same experiment, `blindlib` (uncurated) + `stripe` (curated, verb-precise):

```
ARM A   coverage: [{'name':'blindlib','calls':1}]    fn app#guess [] invisible=['blindlib']
ARM B   coverage: [{'name':'blindlib','calls':1}]    fn app#guess [] invisible=['blindlib']
                                                     fn app#charge ['Net'] invisible=None
```

Adding a resolving call changed nothing. (Note `app#verify`, which calls the *unclassified*
`stripe.webhooks.constructEvent`, is unhedged in **both** arms — that is arm B, not arm A.)

### swift: REFUTED

Same experiment, `BlindLib` (uncurated) + `AsyncHTTPClient` (a `KAPPA_MODULES` entry):

```
ARM A   coverage: [{'name':'BlindLib','calls':1}]    fn App#guessIt [] invisible=['BlindLib']
ARM B   coverage: [{'name':'BlindLib','calls':1}]    fn App#guessIt [] invisible=['BlindLib']
                                                     fn App#fetch ['Net'] invisible=None
```

`App#poolStats`, which calls the unmodeled `HTTPClient.connectionPoolSize()`, is unhedged in both arms —
again arm B.

**So the sweep's "present in all four engines" is half right:** the *package granularity* is four-way; the
*resolution-driven clearing* the sentence describes is rust + java only.

---

## 3. Fixture — arm C, the chained case (and why it is not a granularity bug)

rust R5 (factory-bound receiver), the queue's largest open item, with its single-tree control:

```
CONTROL (one crate)     together#deplib::C::fetch ['Env']   together#go ['Env']        ← correct
dep scan                deplib#C::fetch ['Env']                                        ← the answer is here
APP UNCHAINED           app#go []  invisible=['deplib']     coverage: [deplib × 1]     ← hedged non-claim
APP CHAINED             (app#go ABSENT)                     coverage: None             ← confident + wrong
```

This is the item's "makes them confident", exactly. But the fix is **not** per-call-site coverage.
SPEC §2 chaining rule 3 is deliberate and correct — *"a call that joins no entry in a loaded sibling report
is that report's affirmative purity claim"* — and hedging every joinless call would delete the entire value
of chaining (a dep report omits pure functions **by design**, so most joins legitimately miss).

The real distinction the engines do not currently draw is:

- **keyed and missed** — the consumer formed the join key, looked it up, found nothing. This *is* the
  producer's purity claim. Leave it silent.
- **could not form a key at all** — `c.fetch()` on a receiver the consumer cannot type. The consumer has
  no claim to rest on. This should hedge.

In `scan.rs:1033` the join arm is guarded by `c.path.contains("::") && deps_idx.crates.contains(cr_real)`,
so an unkeyable call **never enters the arm** and is therefore indistinguishable, at the ledger, from a
keyed miss. That is a *resolution/disclosure* gap on the R5/R6/factory-receiver axis, already tracked, and
it does not become easier by changing coverage granularity.

---

## 4. Blast radius — measured, on real code

Method: throwaway instrumented copies (a scratch `git worktree` per engine, and a scratch copy of
`scan.mjs`; **no engine repo was modified**). Each counts, per function, unclassified external call sites
that produce no hedge today, then closes the count transitively over the callgraph and subtracts the
functions that already carry a hedge (`invisible` non-empty or `Unknown`). "fresh" = functions that today
make an unhedged claim and would stop doing so.

### Arm A (the defect) — bounded, and rust's is structurally zero

| engine | corpus | analyzed fns | fresh, direct | fresh, transitive | share |
|---|---|---|---|---|---|
| rust | pgman | 684 | 0 | 0 | **0%** |
| rust | ebman | 1047 | 0 | 0 | **0%** |
| rust | candor-rust (3 members) | 214 / 89 / 172 | 0 | 0 | **0%** |
| java | spring-petclinic | 118 | 0 | 0 | **0%** |
| java | warroot (legacy enterprise) | 18 692 | 261 | **422** | **2.3%** |

rust's zero is not luck. Diffing every crate name `classify()` matches against the three calibrated
exemption lists leaves exactly `{pnet_datalink, pnet_transport}` (plus `cap_*`, covered by
`CALIBRATED_PREFIXES`); the model-SDK crates classify *every* qualified call, so they can never leave a
floored one behind. **The rust arm-A mechanism can only fire on the pnet family** — it fired on my fixture
and on nothing else.

java's 2.3% comes from three packages: `org.hibernate` (287 sites), `org.hibernate.query` (22),
`com.google.maps` (3). `org.hibernate` is precisely the package `Rules.java:652` says *"broadly stays
LEDGERED — its unclassified surface is not vouched for"*.

### Arm B (curated) — the flood; do not touch

| engine | corpus | analyzed fns | fresh, transitive | share | top contributors (call sites) |
|---|---|---|---|---|---|
| rust | pgman | 684 | 55 | **8.0%** | tokio 60, tokio_postgres 43, rustls 12 |
| rust | ebman | 1047 | 149 | **14.2%** | tokio 245, aws_sdk_* 373, chrono 81, reqwest 19 |
| java | spring-petclinic | 118 | 29 | **24.6%** | org.springframework.{aot.hint 17, validation 17, data.domain 11, ui 8} |
| java | warroot | 18 692 | 2 852 | **15.3%** | org.apache.struts.action 4472, commons.lang3.builder 2014 |
| ts | 8 real targets | 20–426 each | 0 on 6 of 8; 3 and 3 on the other two | **0.8% / 4.2%** | uuid 1, lodash 1 |

The rust/java numbers are the flood the question was asked to find: 8–25% of every function in a real
application would newly carry a hedge, and essentially all of it would be false uncertainty —
`tokio::sync` handles, `aws_sdk` builder setters, `chrono` value arithmetic, Struts bean plumbing,
`StringUtils`. That is what the curated list is *for*, and SPEC §7 item 14 exempts it in as many words:

> Exempt from the disclosure: … packages the classifier covers verb-precisely (zero classifications can
> mean the code touches only their pure surface)

ts's near-zero is not a different design — it is the same design with a much smaller and more effect-dense
κ table, plus node builtins excluded at `crossesPackageBoundary` (`scan.mjs:655`).

swift was not instrumented, because **swift already ran this experiment and reverted it.**
`Driver.swift:732-736`:

> ONLY unqualified calls count: a bare MEMBER call (`str.uppercased()`, `p.canReadObject()`) … counting it
> tagged every function touching a stdlib method in a blind-importing file (**rampant false uncertainty**,
> sweep [33]/[36]).

That is arm B measured on a third engine, with the same answer.

### Arm C (chained) — small here, and legitimate

ts, `@ukri-tfs/common` chained against `@ukri-tfs/strings` (an all-pure package, 0 functions): the ledger
drops from 7 packages to 6 and **2 functions** lose a hedge. Both are the spec's intended behaviour — an
empty report *is* a purity claim. rust's corpora scan unchained, so 0.

---

## 5. Recommendation

### 5.1 Fix arm A. Two deletions, one in each engine.

The principle: **coverage is a REVIEW claim, not a resolution outcome.** "The classifier has a rule that
matched one call here" is not evidence that the classifier covers the package; the curated prefix/crate
list is that evidence, and both engines already have one. `dep_classified` / `kappaClassified` is an
unvouched proxy standing in front of it.

- **java** — drop `ctx.kappaClassified` from the `kappaUncovered()` filter (`Candor.java:714`), leaving
  `kappaCovers()` (the reviewed prefix list) and `depCoveredPkgs` (§2 chaining) as the only two coverage
  claims. `blindDirect` is already populated per call site (`Candor.java:1723`) and already propagates, so
  the per-function hedge needs no new machinery. Expected: +422 hedged methods on warroot (2.3%), 0 on
  petclinic. Every one of them is a method reaching an unmodeled `org.hibernate` member.
- **rust** — drop `dep_classified` from the ledger filter (`scan.rs:1252`) and both its insertion sites
  (`scan.rs:836`, `scan.rs:1061`). Measured cost on three real corpora: **zero**. It closes the
  `pnet_datalink` hole and removes a mechanism whose only effect is to make coverage depend on which call
  shapes a scan happens to contain.
- **ts, swift** — nothing to do; neither has the mechanism.

Both changes are strictly in the *disclose more* direction, so they cannot fabricate an effect (standing
bar item 1 is not at risk). Each wants: an A/B on the corpora above with the gain list traced (every new
`invisible` must name a package the scan really calls and the curated list really does not vouch for), a
regression test on the two fixtures in §2, and a conformance row — the natural home is a **PART 4c
sibling** asserting that adding a *classified* call into package P must not remove `invisible: [P]` from an
unrelated function. That row would be verified-to-catch on rust and java today and pass trivially on ts
and swift, which is the correct shape for a rule three engines already satisfy.

The `--gate-json` consequence is worth stating: on warroot the verdict's advisory `coverage` note would
gain `org.hibernate`, and 422 methods would stop being certifiable under `deny E Unknown` /
allow-list rules that currently pass on an unhedged claim. That is the point.

### 5.2 Do not make arm B per-call-site. Model the member instead.

8–25% of functions is not adoptable, and java already has the right pattern for the sharp cases inside a
covered namespace — the **structural Spring floor** (`Candor.java:1724-1739`): an unmodeled member of an
I/O-*convention* type (`*Template`/`*Operations`/`*Repository`/`*Gateway`) inside the κ-covered
`org.springframework` prefix discloses `Unknown` instead of flooring. That is per-call-site granularity
applied to the ~1% of a covered package where it earns its noise, and it generalises: the rule is not
"hedge every unclassified call into a covered package", it is "hedge an unclassified call into a covered
package **on a type whose name or role says it does I/O**". If arm B is ever revisited, that is the shape,
one library family at a time, each with its own A/B — not a granularity switch.

The genuinely uncomfortable residual in arm B is `CALIBRATED_CRATES` entries that are only *partly*
modelled — `clap`, `console`, `dialoguer`, `walkdir` — where the crate-name grant vouches for a surface
nobody enumerated. That is a curation-discipline question (does every calibrated crate have an inventory,
as κ batches 28–31 did for java?), not a coverage-granularity one, and it belongs in SOUNDNESS.md rather
than this queue.

### 5.3 Arm C: the useful change is a distinction, not a granularity.

Keep §2 chaining rule 3. Add, where an engine can tell them apart, a hedge for **calls it could not key**
into a chained package — the R5/R6/factory-receiver shapes. In rust that means the `scan.rs:1033` guard
gains an else-branch for a call whose receiver has a dependency provenance the engine can see but cannot
qualify; today such a call exits the loop with no trace at all. This is the same work as R5, approached
from the disclosure side rather than the resolution side, and it is the one place where "honest beats
silent" (standing bar item 6) buys something the resolution fix has not yet delivered.

---

## 6. Corrections to the item as written

For the queue's own record, three things in the one-sentence item are wrong or misleading:

1. **"Present in all four engines"** — the *package granularity* is; the *one-resolved-call clearing* is
   rust + java only. ts and swift decide coverage from a name list and a loaded-report set, and no call
   site can change either. Fixtures in §2.
2. **"one *resolved* call"** — in rust and java the trigger is a **classified** call (a classifier hit),
   which is not the same thing; in arm C the trigger is not a call at all, it is the *presence of the
   report*. Three different triggers were collapsed into one word.
3. **"chaining removes a hedge that would otherwise have flagged these"** — true, and already correctly
   caveated in the vein doc's own correction section ("the disclosure was never covering the miss; it
   merely happened to be present"). Worth keeping that caveat attached: arm C's hedge is incidental, so
   "would otherwise have flagged" overstates it. The hedge names the *package*, never the *mechanism*.

## UPDATE 2026-07-26 — arm A FIXED in java, and the blast-radius number was wrong

Landed as candor-java `5a76adf`, exactly as recommended (the `kappaClassified` deletion), plus a second
correction the recommendation did not name: `kappaSeen` counted CLASSIFIED calls too, so the tally beside a
package overstated what was invisible (the arm-B fixture read *"2 calls"* when one of them was on the
record). It now counts floored calls only, and a package whose every call is classified never enters the
ledger at all — the number has to mean the same thing as the name beside it.

**The decisive argument turned out to be in the project's own words**, not in the blast radius.
`Rules.java:652`: *"org.hibernate broadly stays LEDGERED — its unclassified surface is not vouched for."*
Bare `org.hibernate` is deliberately absent from `KAPPA_COVERED_PREFIXES` — but because candor classifies the
Session/Criteria terminals, the filter cancelled precisely the ledger entry the curated list withholds on
purpose. The comment and the behaviour disagreed, and the behaviour was wrong. That settles adoptability
without needing to argue about the percentage: it is the disclosure the engine already says it intends.

**The blast-radius number was 8.1%, not 2.3%.** Measured on the real change (pre/post jars built in separate
worktrees, each verified to reproduce its own arm before use) rather than an instrumented copy:

| corpus | new hedges | of analyzed |
|---|---|---|
| spring-petclinic | 0 | 0.0% (118) |
| uflexi / warroot | 1516 | **8.1%** (18692) |

`org.hibernate` 1455, `com.google.maps` 251, `org.hibernate.query` 122. Effect-set changes **0**, entry
losses **0**. Strictly disclose-more, as predicted. *(warroot and uflexi produced byte-identical reports —
they are the same corpus, so this is two corpora, not three.)*

The gap between 2.3% and 8.1% is worth keeping: an instrumented throwaway copy is a good way to decide
whether to try something and a bad way to report what it costs. The estimate was close enough to be useful
and far enough off to have been wrong in a commit message.

Pinned by `CoverageEnvelopeTest.aClassifiedCallMustNotClearTheHedgeOnAnUnrelatedCallIntoTheSamePackage`,
**verified to catch**: against pre-fix source it fails on arm B with *"app.A.nm must be IN the report"* while
arm A passes.

**Still open:** the rust half (`dep_classified`, same two deletion sites) — deferred only because a
concurrent agent was editing that repo. Arms B and C stand as recommended: not per-call-site, and a
keyed-and-missed vs could-not-form-a-key distinction respectively.
