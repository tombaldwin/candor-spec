# Work queue: closing the scan-boundary vein

The ordered backlog for [SOUNDNESS-VEIN-crossing-the-scan-boundary.md](SOUNDNESS-VEIN-crossing-the-scan-boundary.md).
Written to be picked up cold — by a fresh session, or by an agent — without needing anyone's context.

**Why this is the top of the queue.** It is the only known defect that makes a `deny` gate pass code it
should fail, it reproduces in all four engines, and it is gate-level rather than report-level. PAPER1 §6.1b
now scopes the headline claim because of it.

## THE STANDING BAR — applies to every item, no exceptions

0. **A FABRICATION FIX IS WHERE UNDER-REPORTS GET INTRODUCED. Measured: four defects in five fixes.**
   After a code review found ten defects in one day's boundary work, every one of the five fixes written in
   response was re-checked in the OTHER direction. Four were wrong, two of them cardinal sins:

   | fix | what the other-direction check found |
   |---|---|
   | rust `trait_quals` tombstone | dropped a genuine cross-crate reach — **cardinal sin** |
   | java hand-off filter | an ALLOWLIST of SAM names, four already missing |
   | ts callback-position guard | dropped `then`'s second callback — **cardinal sin** |
   | swift erasure split | clean |
   | rust provenance scoping | clean; exposed a pre-existing gap underneath |

   The shape is always the same: you narrow an over-approximation to kill a fabrication, and narrow past the
   real reaches. **The fixture that proves you closed the fabrication is structurally incapable of noticing
   the reach you closed with it** — it contains only the pure receiver, only the uninvoked argument, only the
   one call. Write the second fixture before you believe the first.
   - Narrow with a **denylist** of proven-safe cases, never an allowlist of permitted ones (the java fix
     reached for an allowlist while fixing an over-charge, and had already forgotten four entries).
   - Prefer **disambiguating** to **dropping**. Tombstoning a colliding key is safe against fabrication and
     silently costs every genuine use of it; the information to tell the cases apart usually exists one
     level down (there, per-receiver instead of per-leaf).
0b. **A guess that is right for the wrong reason hides the gap underneath it.** rust's leaf map was
   last-wins, which — by accident — stored the crate a shadowing local needed, so a whole missing feature
   (locals never recorded their own qualification) looked like working code. Removing the guess did not
   create that gap, it revealed it. Expect a "regression" when you stop guessing, and check whether it is
   one before treating it as one.
1. **The cardinal sin is a SILENT UNDER-REPORT.** Never trade it for its mirror. A fix that FABRICATES an
   effect on a genuinely pure function is worse than the miss it closes. If an A/B shows gains you cannot
   trace to a real reach, **revert**. Three swift fixes were reverted this way before a fourth landed clean;
   that is the expected rhythm, not a failure.
2. **A/B on real code, every change.** Scan several real codebases before and after and diff per-function
   effect sets. Report gains AND losses. Zero losses required. Every gain traced to source, not assumed.
   Watch the report ENTRY COUNT too — a spurious extra entry means an unbounded edge (this caught a bad
   drop-glue marker).
3. **Two-tree fixture per fix**, with the single-tree control, and the `deny` gate going from exit 0 back to
   exit 1. The control is what proves it is a *boundary* defect and not a general limitation.
4. **Regression test per fix**, engine's own suite green, four-way conformance green.
5. **Verify before claiming.** Several sweep findings did not reproduce (see the corrections in the vein
   doc). Reduce every mechanism story to a fixture before acting on it.
6. **Honest beats silent.** If a mechanism cannot be resolved soundly, making it disclose `Unknown` is a
   valid and valuable fix.
7. **Delete the output before you measure a control.** A crashed or stale run leaves the previous report on
   disk, and reading it back silently reports the wrong arm's result. This has now bitten three times in this
   vein — twice via a stale `*-all.jar` picked by `ls … | head -1`, once via a pre-fix ts worktree with no
   `node_modules`. Every time, the fabricated datapoint pointed the *flattering* way.
8. **An A/B diff cannot show that a mechanism never fires, or fires on the wrong thing.** It shows what
   CHANGED. Two defects this vein produced had perfectly clean A/Bs: `typeSurface` was near-inert because
   the producer read module names as types, and swift's half-1 provenance conjunct was matching `max()`,
   `min()` and the engine's own local functions. Both were invisible in the output and obvious in the
   COUNTS. **Instrument the preconditions** — how often does the trigger hold, and on what? — and read the
   ratio, not just the diff. A trigger that fires 239 times on shapes you did not intend is not "bounded
   as designed", and a bound that admits nothing on a real modular crate is usually a keying bug.
9. **A comment that states a justification is an assertion, not a proof — and it will be believed.** Three
   of the ten defects a code review found in this vein were cases where the correct principle was written
   in a comment and the code beneath it did the opposite: a leaf-key join four paragraphs under "the trap
   this must not walk into"; "the parameter is gated to Runnable/Callable, so its reported surface is what
   the runtime invokes" (the gate constrains the TYPE, never which MEMBER runs); "cleared on any rebind by
   the clearBinding path below" where that path cleared four other maps and not this one. Each was
   confident, specific and wrong, and each survived self-review *because* the comment answered the question
   the code should have been asked. **Reduce the comment's claim to a fixture, or write it as an open
   question.**
9b. **"Additive" is a claim about the OTHER entries, and it does not cover the entry colliding with itself.**
   Adding a third key shape to the rust dep index (`{krate}#{full qual}`) is additive against every *other*
   entry — a ≥3-segment qual cannot collide with anyone's 1-segment leaf or 2-segment tail2. But for a 1- or
   2-segment qual the "new" key IS the string already pushed, and the index's never-guess rule drops a key
   two entries share. Without a dedup the entry collides with ITSELF and the key that worked before is
   REMOVED: a silent under-report manufactured by a change whose whole argument was that it removed nothing.
   Landing it alone, with a mutant test in both directions, is what caught it (`5feba18`). **An additive
   change still needs the second-direction check of item 0 — ask what the new thing collides with, including
   the old copy of itself.**
10. Commit each fix separately, substantive message, trailers:
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` and the session `Claude-Session:` line.
   **Do not push without an explicit instruction.**

## The template that works

Emit the call shape the cross-package join **already understands**, rather than adding a resolution path.
The dependency's report almost always already holds the right answer under the right key — in 12 of 13 JVM
cases it did, and nothing looked for it. Two caveats learned the hard way:

- The emitted shape must be **distinguishable from a real call**, or it pollutes the κ ledger and the
  coverage envelope (`cr::<drop>::Type`, not `cr::Type::drop`).
- **Bound it at consumption**: join it and `continue`, so it can never reach local resolution or the
  classifier.

## A cross-engine precedent tells you an approach CAN work. It does not specify the guard.

R4 is the case study, and the mistake was mine. R4 sat blocked as *"a decision, not a patch"*; I unblocked it
by citing swift's `eae2de2`, which had shipped the same idea safely behind one carve-out, and I decided for
**resolution 1 (provenance)** on that basis. Measured, resolution 1 *as I specified it* produced **32 fresh
Unknowns on serde_json** — worse than the 30 that had caused the original revert. `serde::Serialize` genuinely
IS a dependency trait, so provenance waves it through.

The discriminator that actually works is **erasure**, which was in neither the queue nor the precedent: a
`dyn` receiver is type-erased, so the crate's local impls really are its candidate witnesses; a `T: Trait`
bound or an `impl Trait` param is monomorphized *by the caller*, so they are not. Two further carve-outs
(`self`/`crate`/`super` roots, nested-item scoping) were each found the same way — by a flood on real code,
not by reasoning.

So: the precedent was good evidence that the shape was reachable, and no evidence at all about which guard
made it safe. **Cite a precedent to justify attempting something; measure to find out what it costs.** And
the reverse now needs checking too — swift's carve-out does not appear to distinguish erased from
monomorphized receivers, so the engine that supplied the precedent may itself be fabricating. That is being
probed; a precedent inherits the other engine's unexamined assumptions along with its result.

## Queue

### rust — 4 of 5 done; R5's DISCLOSURE half also landed (`5fde0d6`), determination half open
- [x] implicit stringification via a dep's `Display::fmt` — `1623a07`
- [x] drop glue via a dep's `Drop` — `a2fbe74`
- [x] `interfaceUnion` emitted in `--deps` child scans — `50218e3`
- [x] **R4 — imported-trait dispatch — `1950a27`.** DECIDED as resolution 1 (provenance) and shipped, with
      the test that said "external-trait local impl must not resolve (fabrication)" **unchanged and still
      passing**: it uses a bare `Iterator`, which needs no `use`, so `expand` leaves it unqualified and the
      provenance gate keeps it out. The hazard it protects is untouched.

      **Resolution 1 as written is NOT enough, and only measuring showed that.** It needs THREE carve-outs,
      each one a flood found on real code, each pinned by a verified-to-catch control:
      1. **provenance** — a genuine dependency crate root. std/core/alloc out (the `Iterator` case), AND
         `self`/`crate`/`super` out: a `use` binding keeps the text it was written with, so value-bag's
         `pub use self::error::Error` made std's `Error` look dependency-qualified — **17 fresh Unknowns**.
      2. **erasure** — the receiver must be spelled `dyn`. `serde::Serialize`/`Serializer` ARE dependency
         traits, so provenance passes them; CHA-ing serde_json's five `impl Serializer` types onto its
         GENERIC entry points put **32 fresh Unknowns** on serde_json (`to_string`, `to_vec`, `to_writer`).
         A `dyn` receiver is erased and the local impls are its candidate witnesses; a `T: Trait` bound or
         `impl Trait` param is monomorphized BY THE CALLER, so they are not. With this, serde_json is 0.
      3. **nested-item scope** (a leak this rung exposed, not previously recorded) — a `fn`/`impl` inside a
         body has its own signature but its calls are attributed to the enclosing unit, so its params
         SHADOW the outer ones. value-bag's `internal_visit(v: &dyn Serialize)` declares a nested
         `impl Serializer` whose `serialize_some<T: Serialize>(self, v: &T)` inherited the outer `v`'s
         `dyn`-ness.

      ADDITIVE and PRECISE-OR-NOTHING (the swift template): edges only, bounded at 12 impls, and
      `unresolved` is NOT set on the wide/absent arms — the local impl set is a LOWER bound on the true one,
      so a wide one stays the documented miss rather than flooding Unknown.

      A/B: 12 real crates zero gains/losses/entry-delta/Unknown-delta. Then the **whole local crates.io
      registry (976 crates) swept with the rung instrumented**, to find where it is LIVE rather than assume:
      6 crates, 35 firings, every one traced (rustls-webpki `&dyn pki_types::SignatureVerificationAlgorithm`
      → Ring/AwsLcRs is the R4 shape exactly); A/B on all 6 clean. **Worth carrying: on that corpus the only
      `dyn`-spelled external traits are `Write`, `Iterator` and `Error` — i.e. every firing the carve-outs
      block is a real fabrication, and the carve-outs are the whole safety margin, not belt-and-braces.**
      Known over-fire, bounded: there is no external analogue of the local arm's `trait_declares_method`
      guard, so a blanket-trait method on a `dyn` receiver (hyper 0.14's `.into()` on a `&dyn Stream`) forms
      an edge that dangles. Zero measured effect.
- [x] **R5 — CLOSED, both halves. Half 2 landed on the SECOND attempt — `a1e53e7`.** The canonical fixture
      goes exit 0 → **exit 1**, matching a single-tree control that is exit 1 in both arms, so it is a
      boundary defect and not a limit. Every one of attempt 1's four reverted defects is now a requirement
      with a mutation that was run and confirmed to fail: fully-qualified type identity on both ends;
      wrapper returns refused outright (`-> Result<Conn,E>` must not publish `Conn` — the binding holds the
      Result); a miss on `returns` OR on the entry lookup after a `returns` hit falls back to half 1's
      disclosure; every surface applied through the ONE `apply_dep_fn` from `7cb5748`.
      - **Item 0 fired for real, mid-implementation.** The first producer used suffix matching, and the
        MODULAR second fixture reproduced defect 1 through a new door: a bare `-> Client` inside `mod mock`
        is module-relative, `expand` leaves it bare, so it published `deplib#mock::client → deplib#sync::Client`.
        The flat fixture was structurally incapable of noticing. `bound_return_type` now resolves a bare
        name against its DECLARING module, matching is exact, and `super::` is refused (`expand` strips the
        root without walking up, which would root the path in the wrong module).
      - **Counts, not output** (item 8): 430 of 850 registry dep reports carry a surface, 9108 returns
        published; all 850 byte-equal to the pre-change engine once the block is removed. Consumer arm of
        408 crates / 41686 entries changed **nothing** and was entered 408 times (2 hits, 406 misses) — the
        rung is exercised there and simply has nothing to say. The one real recovery is on application code:
        `aws_config::defaults(v) -> ConfigLoader` then `.load()`, 2 functions gain `Log` and 45 gain
        `invisible: [aws_credential_types, aws_runtime]`, a blind-crate disclosure ebman could not make for
        itself.
      - Spec side: the field is now documented in SPEC §2 + the 0.23 changelog (`8394af0`). PART 21's rust
        row reads `RESOLVED — ['Fs']`, an arm the checker already accepted, so conformance needed no edit.

      Original framing, kept because it is what half 2 addressed:

      **R5 — the untyped cross-package receiver. DESIGN:
      [DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md).** The key finding is that it SPLITS,
      and the first half needs no format change: an engine always knows whether it FORMED A KEY, and
      `keyed-and-missed` (a genuine purity claim under §2 rule 3) vs `could-not-form-a-key` (no question was
      asked; silence licenses nothing) is a distinction available today. Half 1 = disclose the unformed key,
      triggered on the CONJUNCTION *untyped receiver AND provenance in a chained package* — not on untyped
      receivers generally, which would be the 8-25% false-uncertainty flood the coverage finding measured.
      Do half 1 per engine on its own schedule; it stops the report lying while the rung is negotiated, and
      it survives half 2 as the fail-closed floor for receivers half 2 still cannot type.
      Original framing kept below, since it is what half 2 addresses:
      **return types in the report.** A receiver bound from a dep factory (`let c = deplib::build();
      c.fetch()`) is untyped, so every later method call drops. Needs a `returns` field in the report
      format — spec-visible, so it wants a rung and four-way agreement. Largest item here, and now the last.

      **Both PREREQUISITES for attempt 2 are landed, each on its own, each measured (2026-07-26):**
      prerequisite 0, the full-qual third index key — `5feba18`, and it falsified this doc's claim that a
      full qual is unique within a crate (pgman: 1865 of 17861 collide, on duplicate cfg-gated entries), so
      requirement 3's fall-back-to-disclosure is load-bearing rather than belt-and-braces; and requirement
      4's duplication audit — `7cb5748`, which found rust carrying THREE drifted copies of the dep-apply
      path, exactly candor-java's `6ab26e4` shape. The rung itself is what remains.
- [x] **R6 — fully-qualified `&dyn deplib::Handler` — `7a5fc1d`.** The cause was one line of lossy indexing:
      `bound_leaves` keeps only `segments.last()` (every downstream index is leaf-keyed), and with no `use`
      to expand through the crate identity was simply GONE — `expand` returned a bare `Handler`, the
      `contains("::")` test failed, and the site emitted nothing at all: no dep key, no CHA, no disclosure.
      `sig_trait_quals` keeps the path the signature wrote; `crate`/`self`/`super` spellings are excluded
      because `expand` STRIPS those roots and would hand back a dependency-looking path (carve-out 1 by a
      second door). Gate exit 0 → 1.

      A/B, the whole 976-crate registry: **one** effect change and zero losses — tracing 0.1.44
      `__macro_support::__tracing_log` PURE → `['Log']`, traced to
      `__tracing_log(logger: &'static dyn log::Log, …) { logger.log(…) }`. The key now formed is
      `log::Log::log`, a rule the classifier already had and had never been handed. **855 new report entries
      across 60 crates, all with EMPTY effect sets** — functions that were ABSENT (which in this format IS a
      purity claim) and now carry `invisible: [<dep>]`. Unknown delta across all 976: zero. The same rung
      makes candor's own `span_lint(cx: &impl rustc_lint::LintContext)` read Log.

      Residual, asserted in the test so it cannot drift: the erasure carve-out means the generic-bound and
      `impl Trait` spellings of an imported trait still do not CHA local impls.

### java — 5 mechanism families DONE (fixture 15 silent-pure → 0; five gates exit 0 → 1 on the effect itself — the dep-interface row went `deny E Unknown[dispatch]` at half 1 and now flips on `deny Fs` too)
- [x] implicit stringification + equals/hashCode reentry — `bdf272c`. `reentryEdge` ended in a project-only
      `chaTargets`, and **an empty CHA emitted no Unknown, only a dropped edge**. New `nearestDepFn` — the
      cross-boundary analogue of `nearestConcreteSuper` — plus a shared `inheritDepFn` fold.
      *Independently verified here:* `app.S.show -> ['Env']`, gate exit 1.
- [x] inherited / default methods from a dep supertype — `a5b0a41`. `this.load()` compiles to invokevirtual
      with the PROJECT class as owner, so the join was never reached; the subclass's own ClassNode names its
      dep parent, so the chain is walkable from this side.
- [x] callback / HOF hand-off — `b891d5f`. Method refs join on the handle's exact owner+name+desc; a
      constructed functional takes the type's reported surface, gated on the PARAMETER being a functional
      interface.
- [x] **dep-interface-typed dispatch to a dep impl — HALF 1 DONE, `828ca18`** (java is the second engine to
      take [DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md) half 1, after rust `5fde0d6`).
      Resolution still needs the dependency's HIERARCHY — that stays half 2 — but the DISCLOSURE needed no
      format change: `Store s = Factory.build(); s.save()` was ABSENT from `functions` while counted in
      ⟨0.21⟩ `analyzed`, i.e. a positive purity claim, and now reads `['Unknown']` /
      `unknownWhy: ['dispatch:lib.Store.save']`. Gate `deny Fs Unknown[dispatch]` exit 0 → 1.

      **The java shape of "could-not-form-a-key" is INVOKEINTERFACE**, and that is the conjunct rust does
      not have an analogue for. Java always has a static owner, so there is no untyped receiver as such —
      but the OPCODE proves whether the key names the body: INVOKEINTERFACE proves the owner is an
      interface, so the hash we formed names a declaration the JVM will not run. INVOKEVIRTUAL is
      excluded (a plain dep class usually IS the body, so a miss there is a real purity claim), which is
      why an abstract dep CLASS — jackson's `ObjectIdGenerator`, the case originally recorded here — is
      **still open** and is the sharpest thing half 2's `typeSurface` would buy java.

      Five conjuncts, each one MEASURED not reasoned. "Unresolved receiver into a chained dep" alone fires
      on **5.4% of all analyzed functions** over nine chained JVM corpora (8.4% on logback-classic) —
      the COVERAGE-GRANULARITY flood, reproduced on the JVM. Adding INVOKEINTERFACE → 2.1%; adding "the
      chained report holds an EFFECTFUL body with this exact name+desc under another owner" → **0.49%**.
      The last is a signature join used ONLY as evidence to disclose, never to resolve — the behaviour the
      design doc prescribes when the type surface is absent.

      A/B nine chained library pairs, 32175 analyzed functions: **0 effect losses, 0 non-Unknown gains**,
      122 functions gain Unknown, entry count +25. All 68 distinct disclosed targets traced; ~95% of the
      355 sites justified by a genuine implementor (okio `BufferedSink`/`BufferedSource` → `RealBufferedSink`
      /`RealBufferedSource` — okhttp's `HeadersReader.readLine`, `RequestBody.writeTo` and
      `ResponseBody.byteStream` were absent from the report entirely). The other ~5% fired on a signature
      COLLISION (`HttpRequest.getPath` matched `URIBuilder.getPath`); those sites ARE genuinely
      unresolvable, so the disclosure is true about candor's state — only the evidence that prioritised it
      was coincidental. **Unchained control: twelve jars BYTE-IDENTICAL before and after** (conjunct 3).
- [x] **dep-interface-typed dispatch to a dep impl — HALF 2 DONE, and it needed NO format rung.** The
      `implements` field this row was blocked on is REDUNDANT: java keys report entries by
      `owner.name+desc`, which is exactly the key its consumer forms for an INVOKEINTERFACE site, so the
      already-specified `interfaceUnion` entries land where the join already looks. **The consumer was never
      the problem — only the PRODUCER was missing**, and candor-java's PART 18 N/A ("whole-classpath bytecode
      resolves cross-module dispatch natively") was true of an UNCHAINED scan and false at the boundary — the
      "ask separately what an engine does at the BOUNDARY" lesson again. candor-java now emits interface-CHA
      union entries under `CANDOR_WORKSPACE_CHAIN`, and **PART 18 is four-way** (verified to catch: against
      the pre-fix jar both java rows FAIL). `void run(lib.Store s) { s.save(…) }` goes
      `Unknown[dispatch:lib.Store.save]` → `['Fs']`.

      Measured. Flag OFF: twelve real jars **byte-identical** to the pre-change engine. Flag ON: entries
      +0.9%–14.8%, every added entry an `interfaceUnion`, ordinary entries untouched. The empty-union skip is
      the dominant filter, not a rubber stamp — jackson-databind: 198 candidate interface methods, 161 pure
      across every implementer, 36 emitted. Six chained library pairs, 21 922 analyzed functions: **65 effect
      gains, 0 effect losses**, 7 half-1 Unknowns resolved to a precise effect, 10 functions newly disclosing
      Unknown (httpcore's `Cancellable.cancel` implementers are themselves unresolved, so the union says so
      rather than letting httpclient's `abort()` claim a complete set). Gains traced: okio `BufferedSink`/
      `BufferedSource` → `RealBufferedSink`/`RealBufferedSource` (okhttp's `ResponseBody.byteStream`, every
      `WebSocketWriter.write*`), httpcore `HttpClientConnection.flush` → `DefaultBHttpClientConnection`
      (`Net`) reaching httpclient's three connection adapters.

      **A guard written, measured and REMOVED before shipping — item 0 in its exact shape.** "Emit only for
      an interface with at least one local subtype" read like a bound on `chaTargets`' owner-inherits-a-
      default fallback. It changed **not one entry** across twelve jars, and the one shape where it did fire
      — an interface re-abstracting a method whose only body is a super-interface `default` — is a genuinely
      runnable body that an EXTERNAL implementer inherits and cannot see for itself (a dep supertype is not
      on candor's classpath). It was an under-report wearing a bound's clothes; `chaTargets` finding nothing
      is what actually delivers "nothing implements it, so nothing is published". Two guards that DID survive
      were only shown load-bearing after their first fixture failed to exercise them — the static/private
      filter needs a PURE `static` interface method beside an implementer declaring the same `name+desc` as
      an INSTANCE method, or the static call site is charged a body it never runs. Every guard was then
      verified by mutating it out and confirming a named test fails; a test that has never failed is not
      evidence.

      **AMENDED after a code review (2026-07-26).** The emitter as first written carried three defects, all
      now fixed, and two of them were exactly the failure modes this queue's standing bar predicts:
      - an effectful `default` method's REAL entry SUPPRESSED the union (`if (!claimed.add(hash)) continue`),
        so every overriding implementer's effects were dropped from the only hash a chained consumer can key
        on — a silent under-report. Now MERGED into the claiming entry, which correctly stays UNMARKED (it is
        a real analysed unit counted in `analyzed`; marking it would make a consumer subtract it twice).
        Measured: `deny Net` two-tree exit 0 → 1, single-tree control exit 1 in both arms. On real code
        okhttp's `Interceptor.intercept` went `[]` → `[Clock,Fs,Log,Net,Unknown]`. — `48a5f18`
      - it unioned every implementer with NO fan-out bound, so an open hierarchy re-exported the smear the
        in-scan `CHA_FANOUT_LIMIT` exists to prevent (kafka `Message`, 217 subtypes). Now bounded, and a
        broad interface publishes `["Unknown"]` rather than silence — twelve pure implementers do not make
        the thirteenth pure, and §2 rule 3 makes an absent entry a purity claim. — `429c7b2`
      - the union's `netClass` merged hosts across implementers, letting one literal telemetry host certify
        another implementer's runtime-computed endpoint. Now classified PER IMPLEMENTER. Real but latent:
        across 52 jars, 1089 union entries carry a netClass and **not one** was certified. — `90af98f`

      So the earlier claim in this row that the union used "the CHA universe in-scan dispatch uses" was NOT
      true as written — the bound was missing. It is true now.
- [x] **by-NAME reentry contracts (`compareTo`/`append`/`write`/`read`) — `dd81bfa`** (+ `47caf53`). No
      single hash to join on, so the join enumerates the type's whole reported surface under the contract
      NAME — what the in-scan `reentryTargets` already does over project subtypes. Six shapes reproduced
      silent-pure split+chained; four now match their single-tree control, gate `deny Env` exit 0 → 1.
      Three guards keep it off the leaf-name join, each verified by mutating it out: owner pinned to the
      argument's DECLARED type; descriptor must match the contract's shape (a denylist — `default: true`);
      shadowing per OVERLOAD, with one fixture asserting **both** failure directions (the dropped inherited
      `append(CharSequence)` and the charged shadowed `append(char)`). 14 real jars unchained
      byte-identical; 21 chained/split libraries, 41k analysed fns, 0 gains 0 losses. Per item 8 the clean
      diff is not the evidence — the trigger was instrumented (1205×/523×, every declared type JDK or
      project), so the corpus is the fabrication CONTROL and the fixtures are the evidence.
      - **The `interfaceUnion` does not answer this one** (checked first): `Comparable`/`Appendable` are JDK
        types, never in a scanned set, and the consumer's key is the concrete dep type anyway.
      - **The sink bound shipped as an ALLOWLIST and was inverted — `47caf53`.** `comparesArgZero` listed
        the element-taking sinks, so a newly-added one would default to SUPPRESSING the dep join: omissions
        that are cardinal sins, the SAM-name allowlist shape one repo over. Today's partition is identical
        either way, so no fixture and no corpus can tell them apart — the direction is pinned by a unit
        test on the predicate itself, verified to catch (allowlist restored → that test and only that test
        fails, all 33 others green).
      - **RESIDUAL, refuted with evidence rather than deferred:** the receiver-driven form (`w.write("x")`)
        fails only on `isJavaIoStreamType`, which needs the DEPENDENCY's supertypes. Relaxing it was
        measured on 11 split-and-chained libraries: 161 sites over 31 dep types, only 3 of the 31 are
        java.io streams — the rest (`PacketLineOut.writeString`, `RebaseState.readFile`,
        `ObjectWriter.writeValueAsString`) are already resolved by the exact-hash join. ~90% wrong-receiver
        fabrication, so the gate stays shut. Pinned as a test that says: *if this passes, the hierarchy
        arrived — delete the residual, don't relax the gate.*
- [ ] **CONSUME `<report>.hierarchy.json` — the dep hierarchy java ALREADY WRITES to disk.** Found while
      closing the row above. `ReportWriter.writeHierarchy` emits every project class's direct supers +
      interfaces beside every scan; `Loader.loadCrossDeps` reads only the report JSON, so **nothing on the
      consumer side ever opens the sidecar**. That is precisely the `typeSurface.implements` information the
      abstract-dep-CLASS row, swift row 3 and the write/read residual are all blocked on — and for java it
      needs no format rung at all, only a consumer. It changes dispatch resolution globally, so it wants its
      own A/B and its own commit.
- [ ] **`reentryTargets` fans only DOWN the subtype index** (pre-existing, unrelated to the boundary): in a
      single tree, `new Formatter(half)` where `Half extends Sink` inherits `append(CharSequence)` misses
      the inherited body. The chained arm is now strictly MORE complete than the in-scan control for that
      shape, which is the wrong way round.

**A fabrication caught mid-flight, worth carrying:** the first version imported dep entries whose whole
content is `Unknown`, which turned **12 fully-resolved jackson-databind functions Unknown** from one method
`ObjectIdGenerator`/`ResolvedType.isReferenceType()`. Guard: skip a bare-`Unknown` dep entry when the
project CHA resolves the same signature. Measured with the guard removed — suppresses exactly 14 functions
across six pairs, all Unknown-only, **never a real effect**.

**Two operational traps:** dep reports are VERSION-GATED (generate with the same jar you test with or it is
silently treated as stale); and `build/libs` can hold MORE THAN ONE `-all.jar`, so a glob picks the stale one
— that cost two false negatives here before it was spotted. The stale 0.23.0 artifact has been removed.

### ts — all 5 confirmed mechanisms DONE
- [x] the monorepo symlink shape — a symlinked workspace dep produced **no disclosure at all** because the
      blind branch was guarded on `/node_modules/` — `6fb2560`
- [x] implicit coercion into a dep's `toString`/`valueOf`/`toJSON` — `625e8fd`
- [x] `new DepClass()` never consulting the chained dep report — `965ac82`
- [x] a dep function passed BY REFERENCE to an invoking HOF — `75ec3f6`
- [x] **the UNANSWERABLE KEY** ([DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md) half 1).
      Conformance PART 21 now runs ts beside java and rust.

      **The design note's canonical fixture REFUTES for ts** — worth recording rather than papering over.
      Return types travel in the `.d.ts`, so `const c = build(); c.fetch()` types `c` to `Client`, forms
      `depkit#Client.fetch`, and joins precisely. A receiver ts genuinely cannot type is `any`, which
      already read `callback:` Unknown. Neither half of the rust shape survives here.

      What IS silent is a receiver typed to an **abstraction** — an interface method or property
      signature, an anonymous type-literal member, an `abstract` member. `build(): Fetcher` over a `.d.ts`
      whose only body is hashed `pkg#Client.fetch`: the key is formed and can never be answered, by any
      report, whatever the implementations do. The same evidential position as rust's unformed key,
      reached from the other side — ts knows a type the dependency has no vocabulary for, where rust knows
      a provenance and no type. Silent on the desugared path too (`[1].forEach(job.run)`).

      Third conjunct confirmed independently on ts: unchained, the κ ledger already emits
      `invisible: [pkg]` for every one of these; chained it correctly falls silent, and that silence is
      the confident purity claim. A/B unchained over 10 real targets: **0 gains, 0 losses, entry counts
      identical**. Chained `--workspace` over 5 ukri-tfs services: **5 gains, 0 losses** over ~1000
      analyzed functions; with producer-side union entries stripped (the plain `CANDOR_DEPS` shape) 8/202
      and 3/453. Every gain traced to a real implementor — `OutboundChannel.publishRaw` (publishes to
      SNS), `CoreLogger.info` (`Clock`), `ServiceHostNames.getUrl` (`Env`) — or to a member installed at
      runtime by `fastify.decorate('getServices', …)`, which nothing could resolve.

      **The union and this arm are layered, not redundant.** `OutboundChannel` is declared TWICE in
      `@ukri-tfs/message-handling`, so the `interfaceUnion` emitter's never-guess ambiguity guard declines
      to emit — correctly — and before this arm that declining left silence. Half 1 is the fail-closed
      floor under every guard the resolution path is right to refuse.

The first four follow the rust template: no new resolution path — each routes its declaration through the decision
procedure the CallExpression path already runs (chained report → §5.1 manifest → κ ledger), factored into one
`chargeExternalDecl`. Gate on the two-package fixture, `deny Fs`, identical source: one project **exit 1** →
split+chained **exit 0** → now **exit 1**, matching the one-project control on all three mechanisms.

A/B, 13 real targets unchained: 0 effect gains, 0 losses, 166 invisible gains, 0 invisible losses. Chained
over 4 ukri-tfs services: 7 effect gains, 0 losses — every one tracing to
`@ukri-tfs/common#ServiceHostNamesFromAwsServiceDiscovery.constructor -> ['Clock','Env']` reaching
`createServiceHostNamesForDsApi`, which went from absent-from-the-report (a purity claim) to `['Clock','Env']`.

The coercion arm's anti-flood property was measured under load rather than assumed: the arm is entered a few
hundred times on the corpus and contributes nothing every time, because every resolution lands on the ES lib
or `@types/node` (`Buffer.toString`), both excluded by design.

**Verified independently before PART 20's ts row was added**, on a fixture outside the harness: pre-fix
candor-ts writes `0 effectful functions` for the consumer, post-fix `src.index.show -> ['Env']`. *The first
attempt at that control was worthless* — the pre-fix worktree had no `node_modules`, so the scan crashed and
left the POST-fix report on disk to be read back as if it were the pre-fix result. **Delete the output before
you measure a control** (now item 8 of the standing bar).

Residual, still open:
  union of every file's top level (`proper-lockfile` picked up `Net` from `retry`'s `example/dns.js`).

  **Analysed 2026-07-26 — and "narrow to the resolved entry" is the WRONG fix as stated.** The union is baked
  into the KEY, not the scan scope: the child scan emits every module unit under the single hash
  `<pkg>#<module>`, and the consumer looks up exactly that (`crossDeps.get(\`${pkg}#<module>\`)`).

  Two tempting narrowings, both wrong:
  - *Scan only the entry file.* Under-reports: the entry's transitively-required modules genuinely DO run on
    import, and their top-level effects are real. This is the miss direction.
  - *Exclude `example/`, `test/`, `benchmark/`.* A denylist of directory names is a guess about reachability,
    not a proof of it — and those files are in `node_modules` precisely because they were published.

  The correct fix is **per-file module unit keys** in the child report (`<pkg>#<relpath>.<module>`), with the
  consumer looking up the package's ENTRY module (`main`/`exports`). That is sound without any reachability
  guess, because the entry unit's `inferred` ALREADY includes its transitive imports — the in-scan
  module-import edge computes exactly that closure. An unreachable `example/dns.js` then simply has its own
  key that nobody looks up.

  Cost: it is a wire-visible change to how module units are named, so it wants the same care as a rung.
- **Interface-union needs source — DIAGNOSED 2026-07-26, and the obvious fix is the wrong one.** A published
  package ships `dist` JS + `.d.ts`. Measured: scanning it with `CANDOR_WORKSPACE_CHAIN=1 --allow-js` emits
  `depkit#FileStore.save ['Fs']` and NO union entry.

  **The blocker is not that the interface declaration is filtered out.** I assumed it was — `.d.ts` files are
  deliberately excluded from the scanned set (they have no bodies, so scanning them would mint empty units),
  so `localInterfaceDecls`' `projectFiles` check rejects an interface declared only in typings. I widened
  that check to accept `.d.ts` interfaces belonging to the scanned package, measured, and it changed
  **nothing**. Reverted.

  The real blocker is one level up: the emitter walks the CLASS's `heritageClauses`, and the scanned source
  is `dist/index.js`, where `class FileStore { save(s) {…} }` has no `implements` clause at all — grep says
  0 in the `.js`, 1 in the `.d.ts`. There is no heritage clause to walk, so no interface is ever consulted.

  **The symbol path is CLOSED and the module path is OPEN — both measured with the TypeScript API directly.**
  The checker does NOT merge a CommonJS `exports.FileStore = FileStore` with the sibling `declare class`:
  the `.js` class symbol has exactly ONE declaration, its own, with zero heritage clauses. So no
  symbol-walk reaches the `implements`.

  But the typings MODULE's exports do:

      checker.getExportsOfModule(<dist/index.d.ts symbol>)
        export build      kind=FunctionDeclaration
        export Store      kind=InterfaceDeclaration
        export FileStore  kind=ClassDeclaration   heritage= implements:Store

  So the mechanism is: resolve the package's own typings module, walk its exports, and for each exported
  class carrying an `implements` clause register it under that interface — pairing the typings declaration
  to the scanned `dist` class **by exported name within the same package**. That pairing is authoritative
  rather than a guess: `exports.FileStore` and `declare class FileStore` are the same public symbol by
  construction of the package. Cross-package name matching would NOT be, and must not be attempted.

  **Do not re-attempt the `localInterfaceDecls` widening; it is measured inert** — the blocker was never
  which interface declarations are admitted.
- **A LOCAL class implementing a DEPENDENCY's interface is outside the CHA universe.** `interfaceImpls`
  registers local interface declarations only, so `use(f: DepIface) { f.go() }` never reaches the local
  `class Mine implements DepIface` — the ts sibling of swift's `eae2de2` (dispatch over an IMPORTED protocol
  with LOCAL conformers). Found while measuring half 1, and half 1 now DISCLOSES it (`Unknown`) rather than
  reading pure, so it is no longer a silent under-report; resolving it precisely is the open item. Note
  swift's carve-out before copying it — a widened match here is the leaf-name trap the design note rejects.

### swift — half 1 NOT YET DONE; both rows reproduced with a fixture (2026-07-26)

The last engine missing from conformance PART 21. **Reproduced, not assumed** — dep declares the protocol
and the only conformer, app has none:

    dep report:  FileStore.save ['Fs']          <- the answer is present
    app:         go(_ s: any Store) { s.save() }        ABSENT — reads PURE   (row 3)
                 goFactory() { let s = build(); s.save() }  ABSENT — reads PURE   (row 2)
    coverage: null   (the package is chained, so correctly no hedge)

- **Row 2 (`goFactory`) is implementable now.** `rootOf` types a factory call via `returns[n]`, which holds
  LOCAL function returns only; `build` is a dep function so the root is `nil`, no `extOwner` is formed, and
  the member call falls through silently. Same shape as rust `5fde0d6`: mark the binding dep-provenance-
  untyped, emit a marker, disclose `Unknown` when the file imports a COVERED package (the third conjunct).
- **Row 3 (`go`) needs half 2.** The join forms `DepLib#Store.save` and misses, because `Store.save` is a
  protocol REQUIREMENT — no body is ever hashed under that key, so no report can answer it. Distinguishing
  that from a legitimate keyed-and-missed needs the dependency's HIERARCHY, i.e. `typeSurface.implements`.
  This is the same blocker as java's dep-interface case, and java only got round it because bytecode carries
  the opcode: `INVOKEINTERFACE` proves unanswerability without needing the hierarchy. Swift's syntax does
  not carry an equivalent — a protocol-typed and a class-typed parameter look identical at the call site.

### swift — 6 of 7 gate-flipping mechanisms DONE
- [x] implicit stringification of a dep type, all three operand forms — `83ca73c` (verified independently:
      `describeTyped -> ['Env']` across the boundary, gate back to exit 1)
- [x] dependency `deinit` glue — `41dc8de`
- [x] dispatch over an IMPORTED protocol with LOCAL conformers — `eae2de2`. Needs no dep report: Swift
      spells a conformance to an imported protocol in the same inheritance clause, so `subtypesOf` already
      had it. **Note the carve-out that made it safe** — `enum Rank: String` puts `String` in the inheritance
      clause, so an unguarded CHA sends every call on a String-typed value into raw-value enums' methods;
      `RAW_VALUE_BASE_TYPES` closes it and a test pins it. *This is the swift analogue of the same trap rust
      hit at R4: an imported-supertype CHA is only safe with an explicit carve-out.*
- [x] **factory-bound receiver — the HONESTY half is CLOSED (`47bb69a`).** `let c = build(); c.fetch()` no
      longer reads pure: it discloses `Unknown[dispatch:untyped cross-package receiver]`. The claim above
      that "there is no evidence `c` came from the dep at all" was **wrong** — the callee name is right
      there, and `returns` failing to hold it is itself the evidence that it came from outside the target.
      Note what this does and does not move: `deny E Unknown[dispatch]` now flips, `deny Fs` does NOT. Half 1
      converts the cardinal sin into a disclosed gap; it does not recover the effect.
- [ ] **factory-bound receiver — the DETERMINATION half.** Still blocked on the format rung, and still
      correctly so. A leaf-key join (`M#fetch`) remains rejected: leaves like `write`/`run`/`send` would
      fabricate on unrelated receivers.
- [x] **swift row 3 — ALREADY SOLVED by `interfaceUnion`; my characterisation was wrong (2026-07-26).**
      Recorded here as "NOT fixable locally" and "the strongest argument for `typeSurface.implements` in the
      whole queue". Both false. Measured:

          dep scanned WITH CANDOR_WORKSPACE_CHAIN=1 emits, unprompted:
              DepLib#Store.save ['Fs']  interfaceUnion: true
          consumer:
              go(_ s: any Store) { s.save() }   ->  ['Fs']        row 3, RESOLVED
              goFactory() { let s = build(); … } ->  Unknown[…]   row 2, the genuine `returns` case

      My earlier fixture scanned the dependency WITHOUT the flag, so I measured an engine that had not been
      ASKED and concluded it could not answer. The same experiment on java gave the same result (its
      consumer resolves a union entry with no code change), which is what removed `implements` from the
      queue. *When an engine "cannot" do something, check whether the feature that would do it was switched
      on.*
- [~] **Coverage granularity — CHARACTERISED, split into three arms, one worth fixing.**
      Full write-up + fixtures + measured blast radius:
      [COVERAGE-GRANULARITY-FINDING.md](COVERAGE-GRANULARITY-FINDING.md). The one-line item above
      conflated three mechanisms:
      - **A, dynamic** (`dep_classified` rust `scan.rs:836/1061/1252`; `kappaClassified` java
        `Candor.java:714/1719`): ONE *classified* call marks the whole package covered, deleting the
        `invisible` hedge from every other floored call into it — including packages the source
        deliberately left ledgered (`Rules.java:666`: "an unmodeled member … discloses `invisible` — the
        honest floor"). **A real defect, rust + java only.** Fixtures: rust `pnet_datalink`
        (`interfaces()` floors, `channel()` → Net), java `org.apache.commons.io`
        (`FilenameUtils.getName` floors, `FileUtils.readFileToString` → Fs). In both, the untouched
        function goes from `invisible:[pkg]` to **absent-from-report with `analyzed` counting it** — i.e.
        ⟨0.21⟩ *provably pure*, a positive claim. **FIX:** delete `dep_classified` / `kappaClassified` from
        the ledger filter; the reviewed prefix/crate list and §2 chaining remain the only coverage claims.
        Cost measured: java **422 methods / 18 692 (2.3%)** on warroot, **0** on petclinic; rust **0** on
        pgman/ebman/candor-rust (the mechanism can only fire on `pnet_datalink`/`pnet_transport` — every
        other crate name `classify()` matches is already in `CALIBRATED_*`). Wants a PART 4c sibling:
        adding a classified call into P must not remove `invisible:[P]` from an unrelated function.
      - **B, curated** (the reviewed name lists): four-way, and **SPEC §7 item 14 exempts it by name.**
        Making it per-call-site adds a hedge to **8.0% (pgman) / 14.2% (ebman) / 15.3% (warroot) /
        24.6% (petclinic)** of all analyzed functions — tokio handles, aws_sdk builders, chrono
        arithmetic, Struts beans. **Not adoptable.** swift already tried and reverted exactly this
        (`Driver.swift:732`, "rampant false uncertainty", sweep [33]/[36]). The right pattern for the
        sharp cases is java's structural Spring floor (`Candor.java:1724`), one library family at a time.
      - **C, chained** (`deps_idx.crates` / `depCoveredPkgs` / `coveredPkgs`): four-way and **SPEC §2
        chaining rule 3 mandates it.** The R5 fixture reproduces the confidence loss (control
        `go -> ['Env']`; unchained `go -> [] invisible:['deplib']`; chained `go` absent, no coverage
        field) but the fix is not granularity — it is distinguishing **keyed-and-missed** (a real purity
        claim; stay silent) from **could-not-form-a-key** (`c.fetch()` on an untyped receiver; should
        hedge). Today the `scan.rs:1033` guard means an unkeyable call never enters the join arm at all,
        so the two are indistinguishable at the ledger. Folds into R5/R6/factory-receiver.
      - ts and swift **refute** arm A outright: `kappaKnows` (`scan-core.mjs:234`) and
        `PLATFORM_MODULES`/`KAPPA_MODULES` (`main.swift:526`) are pure functions of the package NAME, and
        `depCoveredPkgs`/`coveredPkgs` are populated at report-LOAD time. No call site can move a package
        from uncovered to covered. Fixtures in the write-up show both arms identical.
- [x] **Conformance PART 20** pinning the boundary contract four-way — `3bd69ec` (java/rust/swift) then
      `08b796a` (ts joins). Verified-to-catch on each engine's row by unchaining that engine's consumer:
      the row goes DIVERGE and the suite FAILED while the others still match.
- [x] **PAPER1 §6.1b / PAPER2 §4.6b** updated through the four-way half-1 close. §6.1b now carries the
      three-row rule and swift's row 3 as the argument for the format rung; §4.6b carries the methodology
      claim that *disagreement* between implementations is where the generalisation lives. The headline
      claim stays SCOPED to a single analysed artifact — deliberately; see the reasoning in §6.1b.

## Done-ness

The vein is closed when, for each engine, the two-tree fixture matches its single-tree control on every
mechanism in the table, PART 20 is green and verified-to-catch, and PAPER1 §6.1b can be rewritten from
"currently false" to a bounded residual.

## Found while fixing round 2 — three items nobody asked for

Each surfaced by an agent working a different task, and each is recorded here rather than in a log because
each is actionable.

- [x] **THE REPORT IS NOT DETERMINISTIC — FIXED (candor-swift `23eafc2`).** `supertypesOf` is a
      `[String: Set<String>]` and Swift seeds Set hashing per process, so `.first(where:)` picked a different
      supertype per run. After: five runs on pollen give ONE report hash, byte-identical. Swept — every other
      `.first` in the driver is guarded by `count == 1` (deterministic by construction), and rust/ts/java were
      each checked directly and are already stable. The test asserts the PROPERTY (alphabetically-first wins),
      because two scans in one test process share a hash seed and a double-scan could pass while the defect
      was live; against the pre-fix build that property test fails 5 runs in 6.
      ORIGINAL REPORT: Four identical runs of the
      *unmodified* candor-swift binary on pollen disagree on `unknownWhy` for **14 functions** —
      `dispatch:CodingKey.self` vs `dispatch:String.self`, `dispatch:NSObject.results` vs
      `dispatch:MKLocalSearchCompleterDelegate.results`: an unordered pick among a class's several
      supertypes. Effect sets are stable; only the disclosure REASON churns.

      Why this outranks a single defect: **A/B on real code is the project's primary evidence**, and a report
      that differs from itself run-to-run injects noise into every diff. It cost one agent a false datapoint
      before it thought to run the control against itself. It also makes `gains` — the supply-chain
      effect-diff product — noisy between identical inputs, which is a product-facing bug, not just an
      internal one.

      Fix shape: sort the supertype candidates before picking, or emit all of them. Cheap. The reason it has
      survived is that nobody diffs a report against ITSELF, only against another version.

- [x] **REASON CLASS ACROSS THE BOUNDARY — FIXED (candor-java `6ab26e4`).** `DepFn` now carries
      `unknownWhy`, and the real cause was DUPLICATION: `crossDepJoin` reproduced `inheritDepFn` line for
      line instead of calling it, so the ⟨0.19⟩ class reached the task/HOF hand-off sites and not the
      ORDINARY call. Deleting the copy was the fix. Measured: `deny Net Unknown[reflect]` exit 0 → 1 on a
      consumer, while `deny Net Unknown[native]` stays 0 so the scoping still discriminates.
      ORIGINAL REPORT: A chained dep's Unknown loses its REASON CLASS, so `deny Unknown[reflect]` cannot bite across a scan
      boundary.** `DepFn` carries no `unknownWhy`, so an inherited Unknown classifies as `unresolved` with no
      class. The reason-scoped gate — a shipped ⟨0.19⟩ rung — is therefore silently inert at the boundary,
      which is exactly where a consumer most needs it. Additive fix: teach `DepFn` to carry `unknownWhy`.

- [x] **netClass fails open in the ORDINARY path — FIXED (candor-java `e24edd9`).** The marker is now
      derived from what a Net call YIELDED rather than from a list of owners, so it fails closed for idioms
      nobody enumerated; restricted to calls taking arguments, because a zero-arg call (`socket.close()`)
      carries no destination and is evidence of neither completeness nor incompleteness — an existing masking
      test caught that over-fire. Both directions pinned. Honest measurement: no jar among 60 sampled has a
      CERTIFIED netClass entry at all, so the corpus cannot price this; the fixture is the evidence.
      ORIGINAL REPORT: A function combining
      `new URL("https://sentry.io/x").openStream()` with `HttpClient.send(request, …)` reports
      `netClass: ["known-telemetry"]`. Each hostless idiom alone yields `unknown-host` via the empty-hosts
      branch, but that branch is per-function, so a literal sibling masks it. Same shape as the union defect
      `90af98f` fixed, one layer beneath it — and the union fix does not reach it.

## Found in passing while landing the typeSurface rung (2026-07-26) — not boundary defects

- [ ] **`candor-scan` PANICS deterministically on `getrandom@0.3.4` / `0.4.2`**, and the panic aborts the
      whole `--deps` run rather than the one crate. `proc-macro2`'s `Span::join`: *"Invalid span with no
      related FileInfo"*. Pre-existing and unrelated to any boundary work — it cost the typeSurface pass a
      workaround. Two things to fix, and the second matters more than the first: the parse itself, and
      **the blast radius** — one unparsable dependency taking down the tree means a chained consumer
      silently proceeds with FEWER dep reports than it asked for, which is the κ ledger's business.
- [ ] **`build.rs` fails clippy `collapsible_if` on clippy 0.1.96**, present at HEAD, so
      `cargo clippy --all-targets` over the whole workspace cannot go green today. Every recent commit
      reports "clippy clean on the four library crates" because of it; that qualifier should stop being
      necessary.
