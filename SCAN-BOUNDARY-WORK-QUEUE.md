# Work queue: closing the scan-boundary vein

The ordered backlog for [SOUNDNESS-VEIN-crossing-the-scan-boundary.md](SOUNDNESS-VEIN-crossing-the-scan-boundary.md).
Written to be picked up cold — by a fresh session, or by an agent — without needing anyone's context.

**Why this is the top of the queue.** It is the only known defect that makes a `deny` gate pass code it
should fail, it reproduces in all four engines, and it is gate-level rather than report-level. PAPER1 §6.1b
now scopes the headline claim because of it.

## OPEN — the 2026-07-27 review of the sweep wave (10 confirmed, 9 resolved, 1 live — rust incompleteness)

A second workflow review, scoped to the ~40 commits the five-shape sweep produced. **Ten confirmed
defects. Every one is again a guard written during that wave** — the same base rate as the previous
review's nine-for-nine, and the reason that review was commissioned at all. Two were mine and are closed;
a third (java's `entryPackage`) and the java half of the incompleteness door closed 2026-07-27, as did all
three rust rows — two fixed, one REFUSED with the counterfactual measured (a refusal with numbers is a
result). None is recorded anywhere else — they arrived in a task notification, which is
the "a residual recorded only in a narrative is a residual nobody will find" failure repeating one level
up, so they are written here first and worked second.

### Silent under-reports — do these first
- [x] **ts `scan.mjs:2631` — the `.bind` arm's new `hofInvokesArg` position gate returns early**, so a
      static/free-form HOF whose callee signature cannot be resolved now DROPS a `.bind`-wrapped dependency
      callback it previously charged. Measured as a `deny Fs` flip from exit 1 to **exit 0**. A guard added
      this wave, narrowing past a real reach — standing-bar item 0, for the third wave running.
      **FIXED candor-ts `b66b69a`.** Reproduced at gate level first (`deny Fs src.api`: two trees exit
      1 → 0, single-tree control exit 0 in BOTH arms, which is what makes it a boundary defect).
      `hofInvokesArg` is a POSITIVE test whose return value cannot distinguish "invoked" from "no
      evidence"; the arm now asks for the OPPOSITE evidence — drop only when the name map excludes the
      position AND the signature positively declares a non-callback. The hard part is that `any` cannot
      be that evidence: `forEach(cb, thisArg?: any)` and a loose library's `fn: any` are the same type
      with opposite meanings, so `calleeParamIsCallable` went THREE-VALUED (`null` = no information) and
      the receiver slot is recognised by parameter NAME (`thisArg`) — a denylist whose failure mode is
      an over-charge on a contrived shape, never a reach. `hofInvokesArg` tests `=== true`, so the
      by-reference arm is untouched by construction.
      - **The wave's own no-fabrication test COULD NOT FAIL, and that is why the regression shipped.**
        It asserted `!includes("Fs")` on a DEP ref in the thisArg slot — but that arm's only possible
        output is an Unknown disclosure, so the shape it was written for (`['Unknown']` before the guard,
        pure after) was invisible to it. Mutating the guard out left the suite **766/0**. Now five
        mutants produce five named failures; a bound LOCAL writer sits in the slot so a fabrication
        shows up as the concrete Fs. Standing-bar item 8c, in the sharpest form yet: the guard was
        *undetectable*, and nobody checked.
      - **A/B: 22 real targets, ~13,000 analyzed functions, ZERO of everything** (gains, losses,
        Unknown delta, entry delta) — and per item 8 that is a claim about the corpus first, so the
        precondition was instrumented: exactly **3** `.bind` arguments reach the non-local HOF arm in
        the whole corpus (apollo-client ×3), all at position 0, all agreeing old-gate vs new. The
        differing branch fires **zero** times. The change is a strict widening by case analysis on the
        four return values, so losses are impossible by construction — the corpus can show it costs
        nothing and cannot show it gains anything. The `.bind`-into-HOF idiom has been all but replaced
        by arrow functions in modern TS; it survives in class-style code, which is where the reviewer's
        shape and the fixture live.
- [ ] **rust `deps.rs:220` + ~~java~~ + ~~swift~~ — only candor-ts withholds coverage from a dep report that
      declares ITSELF incomplete** (non-empty ⟨0.21⟩ `unanalyzed`). The other three gate coverage on
      STALENESS alone, so an incomplete dep report's silence still reads as a purity claim. This is
      shape 1's second door — the one ts found in its own sweep (`21277eb`) — unswept in three engines.
      **The sweep found the door and did not carry it across, which is the exact thing the sweep exists
      to do.** **JAVA DONE — candor-java `d1d3045`. SWIFT DONE — candor-swift `74cd8f1`. Rust remains.**
      - Entries KEPT (they came from source the dep really did read), coverage withheld, stderr says why.
        Absent or explicitly EMPTY `unanalyzed` = complete; anything else, malformed included, fails
        closed. ts's item-0 trade — the ledger hedge REPLACING half 1's `Unknown[dispatch]`, its
        `deny Fs Unknown[dispatch]` going exit 1 → 0 — **cannot happen in java**, because `7e41327` had
        already given chained-ness its own ungated set. That is an argument, so it is a third arm of the
        κ-curated fixture rather than a comment.
      - **Two things to carry into rust and swift.** (1) In java, coverage AND chained-ness are each
        anchored TWICE — a file-level envelope registration and an entry-hash fallback — so gating one is
        a **no-op wearing a fix's clothes**: the mutant that gates only the file-level path fails
        NOTHING. Count the anchors before believing a gate. (2) Reading an ABSENT `unanalyzed` as
        incompleteness is the tempting fail-closed reading and it is wrong — that mutant fails seven
        tests across four classes, because it deletes chained coverage outright. The writer omits the key
        when the manifest is empty, so absent = complete; malformed = incomplete.
      - Measured: 7 chained real jar pairs from `~/.m2`, **0 of 11 real dep reports declare an
        `unanalyzed` unit** — the corpus is the fabrication control and the fixtures are the evidence.
        Armed (every dep report made to declare itself incomplete, envelope only, `functions`
        byte-identical): 4147 functions gain `invisible`, 662 entries appear, **0 effect gains, 0 losses,
        Unknown delta 0 on every pair** — the additive shape, with half 1 still speaking.
      - **SWIFT (`74cd8f1`).** Same treatment, and java's two warnings both applied. (1) The anchors:
        swift registers coverage in THREE places — the envelope `package`, the plural `packages`, and
        each entry's hash prefix — so the registration went through one `register(pkg)` closure rather
        than being gated at one of them. (2) Absent `unanalyzed` = complete, for the same reason (the
        writer omits the key when the manifest is empty). ts's item-0 trade CANNOT happen here either,
        but for a different reason than java's: swift's half-1 gate reads `isChained`, so adding
        `incompletePkgs` to that predicate is what preserves it — and the mutant that omits it fails
        exactly the half-1 row, so it is an assertion rather than an argument. Six guards, six mutants,
        each failing its named test and only it. Corpus: 0 of 34 real Swift packages produce a report
        declaring an `unanalyzed` unit; A/B byte-identical.
      - **A SECOND DEFECT FELL OUT OF THE FIXTURE, in the index rather than the coverage set:** two
        reports carrying an IDENTICAL entry for the same key were WITHDRAWING it as ambiguous. The
        canonical-path dedup catches the same FILE twice and not the same report under two names, which
        is the ordinary shape once `--workspace` prepends its scanned dir to a configured `CANDOR_DEPS`.
        §2 rule 1 forbids PICKING between candidates; there is nothing to pick when they are equal.
        Worth checking in rust and java: the fixture that finds it is "chain the same package twice".

### Fabrication / data loss
- [x] **swift `CallCollector.swift:813` — `fnValueAlias` is a name-keyed RESOLUTION table no clear path
      touches.** The catch-all binder clears vars/protoTyped/arrayElem/opaqueElem/dictElem/tupleElem/
      monoNames/depBoundLocals/localConstStrings — but not this one — and `leaveShadowScope` does not
      save/restore it, so a free-fn alias for a name answers for every later or inner binding of that name.
      **The SEVENTH map in this mechanism**, after six defects across three days. Also at `:2036`, `:954`.
      **FIXED candor-swift `c2c85e3`**, and the DERIVATION landed with it (`97c6b12`, below).
      - Reproduced with the rename control: `func f(_ jobs: [() -> Void]) { let g = eff; for g in jobs
        { g() } }` reads `['Fs']` and the identical body binding `h` is ABSENT. The inner-shadow form
        (`if c { let g = { }; g() }`) is the same defect through a door `clearBinding` does not reach at
        all — a `let` that DOES type never goes near it — which is why the clear lives in `shadowName`.
      - **The widest of the five**: the other four are TYPE indexes, so leaking one charges whatever some
        type's member happens to do; this one names a FUNCTION and charges its whole transitive set.
      - **Why the previous audit cleared it is the durable part.** It wrote "an aliased fn value called
        after a shadowing loop still resolves" — the LOSS direction. The FABRICATION direction was never
        run. **A rename control run in one direction is half a control.**
      - Three guards, three mutants. The third is the ordering carve-out `protoTyped` needs one map over:
        `let g = g` resolves THROUGH the binding it replaces, and the re-aliasing branch cannot restore
        it because its RHS is a shadowed local rather than a `localFreeFns` name.
      - A/B 34 real Swift packages: 0/0/0. Per item 8 that is the control, not the evidence —
        instrumented, the rung is established **once** in the whole corpus (console-kit
        `let rpp = linux_readpassphrase`) and the fix's trigger fires **zero** times. The probe was an
        ARM and was removed before the commit (item 8b: an env read in the collector writes Env into
        candor's own self-scan).
- [x] **swift `main.swift:425` — `--workspace`'s new `sweepStale()` deletes every `*.json` in
      `<root>/.candor/deps` that this run's own path-dep scans did not produce**, including reports the
      USER placed there for non-path dependencies. Unrecoverable, and not an analysis defect at all. Also
      at `:439`. **FIXED candor-swift `b4f6cbc`.**
      - The sweep STAYS (it exists for `43a0eaa`'s measured reason); what changed is that a file this run
        did not write is never a deletion candidate. **Ownership is DERIVED from `Package.swift`, not
        marked** — a manifest sidecar would answer only for caches written after the change, leaving the
        first post-change run over an existing cache in exactly the state `43a0eaa` fixed. The candidates
        are the discovered path deps; a FAILED dep's file is found by the package name an earlier round
        recorded, else its own manifest `name:`, else the directory basename — the writer's own three
        sources in the writer's own order. Everything else is named on stderr and left alone.
      - Residual, disclosed: a report for a package that USED to be a path dep and no longer is lingers.
        Information kept rather than destroyed.
      - The manifest-name row uses a dep whose DIRECTORY is `libdep-src` while its package is `Dep0`,
        because with the two equal the basename fallback answers correctly too and the branch under test
        could be deleted with the row still green — item 8c's shape, avoided by construction.
      - **The release build caught what the debug build and 328 tests could not**: a nested func closing
        over a top-level `var` a sibling closure writes is a Swift-6 `sending` diagnostic under
        whole-module optimization ONLY. The first "verified" arm was a binary the failed build had left
        on disk — item 7c, in a new spelling: `swift build -c release` failing does not remove
        `.build/release/`.

### NEW, from the same swift pass — the EIGHTH and NINTH maps, REFUSED with numbers
- [ ] **swift `boundLocals` (and `catchBindings` with it) — the same mechanism, in the map neither audit
      classified, because it is not a FACT.** Every other row in this family is a name-keyed fact (a type,
      an opacity, a provenance, a literal, an alias) outliving its binding. `boundLocals` is the other
      half: an EXISTENCE claim — "this name names a local" — and both audits were looking for facts.
      **Three forms REPRODUCED with rename controls, all fabrications:**

      | form | reads | rename control |
      |---|---|---|
      | `if case let token? = o { print(token) }` inside a type with an effectful computed `token` | `['Env']` | ABSENT |
      | `catch let token { print(token) }`, same type | `['Env']` | ABSENT |
      | `if case let boot? = o { print(boot) }` beside an effectful top-level `let boot` | `['Env']` | ABSENT |

      It is written by **2 of the ~7 binder forms** (a `let`/`var` identifier and a tuple destructure),
      so a loop, closure, `case let` or `catch` binder registers no shadow at all; a `for` binder happens
      to be safe only by ACCIDENT of usually landing a type in `vars`, which the bare-read arm tests
      instead. `catchBindings` is entangled with it: that map is function-wide too, and its shadow guard
      is a `!boundLocals.contains` PROXY that stops working the instant every binder writes `boundLocals`
      (a catch binder would shadow itself).

      **THE OBVIOUS FIX WAS WRITTEN, MEASURED AND REVERTED.** Write it in `shadowName` (the one path every
      binder takes), save it in `ShadowSave` (function-wide it would silence the enclosing type's real
      property read for the rest of the body — the two directions genuinely oppose here), defer it past a
      self-referential initializer (`let boot = boot` reads the GLOBAL), and add `boundLocals` to the
      bare-read arm's shadow test. All five fixture rows go the right way and both second-direction rows
      are RECOVERIES. Then the corpus:

      | arm | vs. baseline |
      |---|---|
      | everything | **1 gain, 405 losses, −93 entries** |
      | minus the bare-read arm's shadow test | 1 gain, 292 losses, −77 entries |
      | the bare-read arm's shadow test ALONE | 0 gains, **173 losses**, −8 entries |
      | `shadowName` write + scope + deferral, no bare-read change | 1 gain, **305 losses**, −77 entries |

      Two sub-cases traced, and they point OPPOSITE ways, which is the whole reason this is filed rather
      than shipped. (a) The bare-read arm's 173 are largely FABRICATIONS being removed: swift keys global
      units by BARE NAME, so pollen's `PollenForecastCache.fetchOrLoad` — which holds a local
      `let task = Task<…>{…}` — was charged `Exec` from a top-level `let task = Process()` in a different
      target's `CapturePollen.swift`, and the same for `outPath`. That is the open
      [global-unit-identity vein](SOUNDNESS-VEIN-global-unit-identity.md), reached through the shadow
      discipline. (b) The other 305 include units DISAPPEARING and disclosed `Unknown`s and `invisible`s
      vanishing, reduced to a 12-line repro (vapor's `AbortError.swift`: `DecodingError.reason` and
      `.description` both vanish) that was NOT explained inside the session's budget.

      **Refused under item 1: 305 report changes I cannot trace is not shippable, in either direction.**
      A loss you cannot explain is not a fabrication you have removed. Both maps are filed in
      `NameKeyedStateTests.disposition` as `.knownDefect` with these numbers attached, so the next audit
      inherits them instead of the surprise — and the classification test makes walking past them again
      a deliberate act rather than an oversight.

      **Whoever picks this up: start from the 12-line vapor repro, not from the corpus.** The two
      sub-cases must be separated before either is shipped; they are different defects that happen to
      share a map.

### The remedy for the whole family — DONE
- [x] **swift — the set of maps a rebind must invalidate is now DERIVED, not listed** (candor-swift
      `97c6b12`). `42093b6` removed the enumeration of binder FORMS and left the enumeration of MAPS
      standing, which is where defects six and seven came from. `NameKeyedStateTests` parses
      `CallCollector.swift` with SwiftParser, enumerates the class's stored properties from the parse
      tree, and requires each to be classified — cleared (and whether scoped), a deliberately-kept HEDGE,
      a program-wide index, or not per-binding. Adding a map without the decision fails a test;
      classifying one as cleared without writing the clear fails another; classifying one as scoped
      without BOTH saving and restoring fails a third (`opaqueElem` shipped with exactly that half).
      Three mutants, three named failures, and the stale-entry direction caught a real one unprompted on
      its first run.
      - **The honest limit, stated in the file**: the SET is derived, the JUDGEMENT is authored. Whether a
        `[String: X]` is keyed by a binding name or a type name is a fact about meaning, not syntax, and
        the hedging sets must NOT be cleared — so the value is in forcing the decision to be written once
        per property, with its argument, not in making it automatic.
      - Reflection was unavailable (`CallCollector` is in the executable target, which a test target
        cannot import), so it is a source-level test — with its own controls, since an extraction that
        silently finds nothing would pass every row vacuously.
      - **The "rewrite the binding model" option was RE-PRICED with the seventh instance in hand and the
        verdict STANDS.** Fusing the flags into `vars` still requires `vars` to become lexically scoped,
        which it deliberately is not (function-wide with clear-on-rebind: a stale TYPE is dangerous
        inward and merely lossy outward), and doing it without that scoping makes every flag leak outward
        the way types do. What changed is the GROUNDS: the reason to keep deferring it was "the residual
        is a new map added later without being added here, which is a review question" — and this pass
        proved a review question is not enough, twice. It is now a TEST question, which is the thing the
        rewrite was wanted for. Re-open the rewrite only if a defect appears that the classification
        cannot express.

### Cross-engine divergence — `Unknown[class]` gates now fire differently per engine
- [x] **java `Loader.java:203` — `entryPackage`'s slash fallback takes the last `/` in the whole hash**,
      which for java's own hash form lands inside the method DESCRIPTOR, so entry-level coverage registers
      a garbage package name. **DONE — candor-java `47e2721`**, and the review's "harmless-looking"
      caveat was the right question to ask: the two directions came out opposite.
      - It could never FABRICATE coverage. A parse that runs into the descriptor necessarily keeps the
        `(` that opens it, and no JVM package name can contain one, so the bogus string matched nothing
        in `depCoveredPkgs` — inert, and now asserted inert.
      - The cost is the registration that did NOT happen. `depChainedPkgs` is conjunct 3 of the half-1
        unanswerable-key rung, so a chained report with no envelope package field left an INVOKEINTERFACE
        into an unnameable dep implementation reading as a confident purity claim:
        `deny Fs Unknown[dispatch]` **0 → 1 violation**, against a single-tree control that is 1 in both
        arms. A silent under-report, not a cosmetic parse bug.
      - **Every dep-report fixture in candor-java's suite predating the fix used `()V` or `(I)V`** — no
        reference type, no descriptor slash — which is exactly why they all passed. Worth checking in the
        other engines' fixtures for the same shape of blind spot.
      - A/B 7 chained real jar pairs: 0 delta, because every candor-java report carries `packages` and the
        fallback is redundant there. **A zero-delta arm is a claim about the experiment first** (item 8),
        so the same pairs were re-run with the envelope package field STRIPPED — the legacy/foreign shape
        the fallback exists for — and the mechanism fires: httpclient sheds 966 false `invisible` markers
        and 320 entries, each package traced to real entries in httpcore's own report. Still 0 effect
        gains and 0 losses.
- [x] **rust `deps.rs:307` — a stale report's `Unknown` now arrives tagged `callback:…`**, classifying as
      `indirect`, where the other three leave it `unresolved`. Rust is the four-way outlier, and the class
      the stale Unknown used to carry has been replaced by a fabricated one. This is the fail-closed
      fallback rust's own sweep agent wrote. Also java `ReasonClass.java:77`.
      **DONE — candor-rust `f2309a5`**, both sites (the staleness downgrade AND the reasonless-Unknown
      fallback in `apply_dep_fn`). The generalisation is worth keeping: **`callback:` is not a residual
      bucket.** §4 ⟨0.7⟩ defines it as an unresolved higher-order / owner-less INVOCATION — a claim about
      code — and §6.2 already names the residual, `unresolved`, reached by ABSENCE. Reaching for a
      canonical kind to "fail closed" is how a fabricated class gets written.
      - Measured chained on pgman/ebman/candor-rust: **0 effect gains, 0 losses, entry count +0, Unknown
        count +0**; 18 of 367 Unknown-bearing fns move class — 15 `indirect`→`unresolved`, 3
        `{dispatch,indirect}`→`{dispatch}` (swift's documented "a class the chained arm has and the
        single-tree control does not", live on real code).
      - **rust's own writer invariant is what forced the fabrication.** `scan_one`'s `debug_assert`
        ("`direct` carries Unknown ⇒ `unknownWhy` non-empty") makes the boundary case name one of the four
        §4 kinds, and NONE of them projects to `unresolved`. §4's own definition of a source — a unit
        "whose own body has the unresolvable call" — exempts a chained consumer, so the assertion was too
        broad, not the fix. **Any engine with an equivalent assertion has the same trap.**
      - rust deliberately did NOT copy ts's `stale-dep:` / swift's `dep-stale:`: PART 10 makes an
        off-vocabulary kind a HARD divergence. **Those two engines are one fixture away from failing their
        own conformance part** — worth checking, not checked here.
      - Found on the way: rust had NO staleness disclosure on ANY channel (ts and swift both print one);
        added on stderr.
- [ ] **OPENED BY THAT FIX — rust is the only engine with no transitive-why resolution.** java
      (`depTransitiveWhy`) and ts (`resolveInheritedWhy`) both walk the dependency's own `calls` edges to
      recover the class of an Unknown the dep unit only INHERITED (⟨0.6⟩ makes `unknownWhy` direct-only, so
      a dep's exported function publishes `inferred:['Unknown']` with no reason whenever the hole is one
      hop further in). rust leaves those at the honest `unresolved`. Its report already carries `calls`, so
      this needs **no format rung** — it is determination replacing disclosure, and it is the reach the
      fabricated tag was groping for. 15 fns on the three-project corpus are waiting for it.
- [x] **rust `deps.rs:377` — a package chained BOTH fresh and stale resolves as untrusted**; java, ts and
      swift all resolve the same input the other way (fresh wins). Four engines, two answers, same input.
      **REFUSED, with the counterfactual measured — candor-rust `63bbe87`.** Aligning rust costs a silent
      under-report. Coverage is the claim that an absent entry is a purity claim (§2 rule 3); rust's index
      DROPS a key two dep functions share rather than picking, so a fresh+stale collision withdraws the
      answer entirely. With `untrusted` cleared (the ts/swift shape, one line) the fixture's consumer fn
      does not merely lose a hedge — **it disappears from the report**, and an `Exec` the fresh report
      names reads as a confident purity claim. java and ts can afford fresh-wins because their entry-level
      conflict keeps an answer (java `crossDeps.put` last-wins, ts merges into a Set); rust's cannot. SPEC
      §2.1 is silent on the conflict and no PART pins it, so this wants a **four-way ruling**, not a
      unilateral edit. Pinned by a two-direction fixture carrying flip instructions.
      - Not theoretical: two reports naming one package is the ordinary Cargo shape (semver-major
        duplication) — **7 of 167 dep reports in candor-rust, 9 of 259 in pgman, 30 of 378 in ebman**.
- [ ] **FOR candor-swift, from that refusal: swift drops the colliding key exactly as rust does
      (`Deps.swift` `insert`) AND resolves coverage fresh-wins** — the two halves that together produce the
      false all-clear measured above. Not checked in swift (another repo, another measurement); the
      fixture to reproduce is in candor-rust `tests.rs`
      `a_package_chained_both_fresh_and_stale_keeps_its_blind_spot_disclosure`.

### The one I would look at hardest
- [x] **rust `scan.rs:622` — the cached parser-abort replay is gated on content hash + decl-index hash,
      but the abort is NOT a function of those two.** `4f7b704` established that the abort depends on how
      much each rayon worker happened to parse, so a ONE-OFF abort is latched into the cache and replayed
      forever. This is the fix for MY cache-poisoning defect, and it may have replaced one latch with
      another — the direction is different (a spurious `unanalyzed` + a gate that will not go green, rather
      than a false all-clear) but the shape is identical. Also `:618`.
      **CONFIRMED AND DONE — candor-rust `35466f0`.** A cached abort is now a marker that the FnInfos were
      never derived, not an answer to replay: the entry is dropped at the one place `cached_fninfos` is
      populated, so the reuse gate misses it, the round-2 re-parse picks it up as ordinary stale FnInfos,
      and the file either aborts again (disclosing by the same cold path, byte for byte) or produces the
      answer it always owed. The write-back takes the marker only from THIS run, so an abort cannot outlive
      the run that observed it.
      - **The latch also broke the documented `--incremental` contract** ("produces a BYTE-IDENTICAL report
        to a full scan"), silently, in a mode nobody re-runs from cold.
      - Measured by injecting the fault into a REAL crate's real file (reqwest 0.12.28 `src/cookie.rs`),
        injection removed for runs 2–3: pre latches forever at 361 entries + 1 `unanalyzed`; post recovers
        **22 entries, 0 losses, 0 changed effect sets, Unknown delta 0**, `analyzed` 946→969, and is
        byte-identical to the full scan. Inert on pgman/ebman/candor-rust and **196 crates.io crates**
        (full + cold + warm, both arms, 0 differ).
      - The old test's `warm2` arm — injection removed, disclosure expected anyway — was the assertion that
        PINNED the latch (standing-bar item 7g, again). It survives inverted in
        `a_cached_abort_is_re_attempted_rather_than_latched`; the still-aborting arm keeps the original
        defect's requirement and is now named for it.
      - The generalisation: **`--incremental` reuse is licensed by "the input is unchanged", and an abort is
        not a function of the input.** Any per-file cache that persists an OUTCOME rather than a DERIVATION
        has this shape; ask what the outcome actually depends on before choosing the cache key.

### Closed already — both mine
- [x] **conformance PART 22 could not regress two of the four defects its own header cites** — `unknownWhy`
      was neither compared nor producible by the fixture. Fixed `81e919e`; verified to catch via a java
      mutant (`java -> DIVERGE (surface dropped by the join: unknownWhy[...])`). Rust could not demonstrate
      it because its own fail-closed writer assertion aborts the run first — a stronger guarantee than the row.
- [x] **`release-preflight` check [4] silently covered four of five components** — no `grabver` row for
      candor-java. Legitimate (java's build id is GENERATED from the git hash, so it cannot lag) but unsaid.
      Fixed `f6cc184`: the row now prints, naming itself out of scope.

## CARRIED FORWARD — the vein's own rows are all closed; these are what it uncovered

**The vein has ZERO open rows.** Every mechanism family that made a `deny` gate pass code it should fail is
closed four-way and pinned by conformance PARTs 18–22. What follows is not the vein: it is the set of things
found *while* closing it that were deliberately deferred with a reason. They were buried in prose in the
sections below, which is the failure this document exists to prevent — **a residual recorded only in a
narrative is a residual nobody will find.** Hoisted here 2026-07-27.

Each was refused or deferred with a measurement, not left undone. None is a known silent under-report.

### Needs its own measurement before anyone touches it
- [ ] **java — a CONCRETE dep method overridden effectfully** answers only for its own body across the
      boundary. Unlike the abstract case the key IS answerable and the answer IS true, so this is a
      narrower question than a purity claim — but the blast radius is every non-final method of every
      non-final class, so it wants its own A/B before a line is written.
- [ ] **swift — the erasure gate does not reach the LOCAL-protocol dispatch arm.** REFUSED with both
      treatments priced (`020add4`): suppress costs 5 losses and 7 entries REMOVED; disclose costs 9
      concrete effects → hedge. The deciding argument is recorded in the code — for an IMPORTED protocol
      the in-scan conformers are an arbitrary subset of the candidates, for a LOCAL one they BOUND them.
      Re-open only with an A/B, since this arm is what R28/R39 and the whole element-dispatch family run on.
- [ ] **java — the dep-sidecar hierarchy half.** `writeHierarchy` writes a sorted `TreeSet` with no
      superclass marker, so a chain lying ENTIRELY inside a dependency stays depth-ordered. Closing it is a
      sidecar-FORMAT rung with its own compatibility surface; the compatible encoding is worked out in
      `Cha#resolutionOrder` and was deliberately not ridden on `9f8e71c`.

### Unblocked, deliberately unlanded — each narrows a gate
- [x] **LANDED, candor-ts `5ba301c`** — 1,234 malformed emissions over 15 repos, all from the interface-CHA arm; effect sets and entry counts identical, 695 functions leave `dispatch` / 573 enter `indirect`, monotone. **The narrowing is named, not buried: `deny Unknown[dispatch]` flips exit 1 → 0 on 4 of 14 targets — and in each of those EVERY dispatch reason in the report was malformed (6/6, 56/56, 18/18, 10/10).** ORIGINAL: the malformed `dispatch:type.member` reclassification. The blocker is RESOLVED: all four
      engines were RUN on owner-less function values (rust `callback:unresolved call`, java
      `callback:…Function.apply`, swift `callback:fn` — all class `indirect`), SPEC §4's dividing line is
      explicit, and PART 10 already asserts every `dispatch:` carries `owner.member`. **candor-ts is the
      outlier and the change moves it toward both the family and the spec, needing no spec change.** Not
      landed because it narrows a gate (16 functions move `dispatch`→`indirect`) and wants its own A/B plus
      a second-direction fixture. Note `826571c` makes the malformed string travel across the boundary, so
      the blast radius is wider than the 68 measured.
      **LANDED candor-ts `5ba301c`, with both the A/B and the second-direction fixture — and the blast
      radius really was wider: 1,234 malformed emissions over a 15-repo corpus, 695 functions leaving
      class `dispatch`.**
      - **What the malformed strings were, instrumented rather than guessed**: every one of the 1,234
        came from the interface-CHA arm and none from the other three emission sites. Two shapes, both
        function VALUES — a named type whose content is a CALL SIGNATURE (`interface UnaryFunction { (x:
        T): R }`, `type PatchFn = …`: owner, no member; the corpus names read as function types because
        they are — `ErrorCallback`, `SendCallback`, `MessageHandler`, `PatchFn`), and a member of an
        ANONYMOUS type literal (member, no owner; 251 had neither). The `callback:` detail is
        best-effort, so the nameable half is KEPT — `callback:src.a.UnaryFunction`, `callback:run` —
        rather than thrown away along with the classification.
      - **A/B, 14 scannable targets, both arms hashed.** Effect sets identical on every function of
        every target, entry counts identical: this changes a string, not an analysis. Class movement is
        MONOTONE — 695 leave `dispatch`, 573 enter `indirect`, 0 gain `dispatch`, 0 lose `indirect`.
        `deny Unknown` unmoved everywhere; `deny Unknown[indirect]` was already firing everywhere it now
        additionally covers. Nothing goes silent.
      - **The narrowing, with its number:** `deny Unknown[dispatch]` flips exit 1 → 0 on four of the
        fourteen (conf, got, ky, p-queue). In each, EVERY `dispatch:` reason in the report was malformed
        — 6/6, 56/56, 18/18, 10/10 — so the rule was firing entirely on the classification this change
        says is wrong. On the other ten it is unmoved.
      - **Both directions fixtured**, and mutating the rule out is what proves it: always-dispatch fails
        4 named tests, always-callback fails 15 — including every pre-existing `dispatch:` assertion in
        the suite, which is the real second-direction evidence.
      - **For the rust row below this is a precedent, not a guard** (cf. "a cross-engine precedent tells
        you an approach CAN work"). What made it safe here is that the reclassified strings named
        NOTHING, so no `deny Unknown[dispatch]` could have been relying on a real owner.
        `ambiguous:same-name local defs` DOES name something, so that row still needs its own answer.
- [ ] **rust — `ambiguous:same-name local defs` is outside the closed §4 vocabulary**, emitted **757 times
      across 253 crates**. PART 10 misses it because the harness's fixtures never produce that kind.
      Renaming is not free: `callback:` moves the class Dispatch→Indirect and WEAKENS
      `deny Unknown[dispatch]`. Wants its own measurement and probably the spec's MIGRATION mechanism.

### Precision gaps, disclosed and not silent
- [ ] **ts — the BY-REFERENCE HOF arm has the `.bind` arm's hole, but DISCLOSED.** Found while fixing
      `b66b69a` and deliberately not fixed with it. That arm keeps the positive `!hofInvokesArg(…)`
      early return, so a DEP function passed BY REFERENCE at a position a loosely typed dep HOF does not
      declare loses its concrete effect. Reduced to a fixture rather than asserted — `forEach(xs: any[],
      fn: any)` against a well-typed `some(xs, fn: (x) => boolean)`, same argument, same position:
      `depRefLoosePos1 -> ['Unknown'] (callback:fn, callback:param#1)` vs
      `depRefTypedPos1 -> ['Fs','Unknown']`.
      **A precision loss, not the cardinal sin** — the Unknown and its reason are still published, so
      `deny Unknown` and `deny Fs Unknown` still bite where a bare `deny Fs` no longer would. That is
      why it did not ride the `.bind` fix: `.bind(…)` IS a function by construction, so widening that
      arm was free, while this one takes a BARE IDENTIFIER and the callability guard does not save it (a
      seed object typed `any` passes `argIsCallable` — the `path.reduce(fn, obj)` shape guard (1) exists
      for). Widening it is a fabrication risk with no measurement behind it; it wants its own A/B.
- [ ] **swift — dep reports name SwiftPM PACKAGES while imports name MODULES** (`swift-case-paths` vs
      `CasePaths`), so on those targets nothing is covered in EITHER arm. Found by instrumenting why a fix
      showed no delta rather than assuming it was inert. Pre-existing and separate from the vein.
- [ ] **swift — a nested-type factory does not resolve IN-SCAN either**, so that row has no single-tree
      control and the chained arm is now strictly BETTER than the unsplit one — candor-java `9ae68f7`'s
      smell, one repo over. Documented on the test rather than asserted, because pinning it would encode
      the gap as a requirement.
- [ ] **swift — `returnsIdx` is bare-name keyed package-wide**, a pre-existing residual doing one conjunct
      earlier what `7a4f977` fixed. Pinned as a test asserting TODAY's behaviour with instructions to flip it.
- [ ] **ts — `.candor/dep-inits/` and `.candor/deps/` are never cleared**, so a package whose rescan throws
      is served from the PREVIOUS run's file while the code comment claims it "is skipped".
      ABSENT-BY-ACCIDENT: the incompleteness fix (`21277eb`) removed the sharpest edge, but nothing prevents
      the shape returning.
- [ ] **rust — the QUIET half of the span-crossing-a-thread defect is unmeasured.** `4f7b704` closed the
      loud tail (the panic; 60 unseen crates now clean). The quiet form resolves a span against the WRONG
      file instead of aborting, and the precondition was measured at **72.4% of 88,927 macro re-parses**.
      No known wrong output — and no measurement either.

### Release-shape, needs Tom
- [ ] **candor-ts is at build 0.23.2, the family at 0.23.1.** Legitimate — its module-unit wire key moved
      and §2.1's staleness gate keys on the per-engine build id. `release-preflight` check [4] was relaxed
      to report rather than fail (`candor` `b5e2cb0`), and its `WANT_VER` arm still catches a genuine lag
      exactly. The release set is a decision, not a defect.

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
   - **THIRD INSTANCE, 2026-07-27, and the sharpening is worse than the rule.** The `.bind` gate
     (candor-ts `4958a6d` → fixed `b66b69a`) shipped with a FIRST fixture that could not fail either. It
     asserted `!includes("Fs")` on a *dependency* ref in the receiver slot — an arm whose only possible
     output is an `Unknown` disclosure — so the over-charge it was written for (`['Unknown']` before the
     guard, pure after) was invisible to its own assertion, and mutating the guard out left the suite
     766/0. So the rule is not only "the first fixture cannot see the reach you closed": **check that the
     first fixture can see the fabrication.** Mutate the guard out and name the failing test *before*
     writing the second fixture — if nothing fails, you have not yet tested anything at all.
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
7b. **KEEP BOTH ARMS' BINARIES, not just their outputs — a measurement you cannot re-run is not a
   measurement.** The dep-hierarchy A/B reported httpclient BYTE-IDENTICAL on its first pass. Three later
   runs — two of them of a *different* variant of the same change — all report it DIFFERS, deterministically,
   with seven traceable Net gains. The first result was wrong and the cause is now unrecoverable, because
   the post-arm jar had been rebuilt over by the time the contradiction surfaced. Deleting the OUTPUT before
   a control (item 7) is not enough: name each arm's binary by its content hash, keep it for the life of the
   measurement, and when two runs disagree re-run BOTH from their preserved binaries before believing
   either. Note which way the bad datapoint pointed — again the flattering way (a real recovery, hidden).
7c. **TWO WAYS I RAN THE WRONG BINARY IN ONE HOUR, both silent, both mine.** (a) `cargo build … | head -3`
   SIGPIPEs the build: cargo dies, the *old* binary stays on disk, and every "verification" after it tested
   code that was never compiled. Four consecutive results came from a binary 70 minutes stale. Never pipe a
   BUILD through `head`; check the artifact's mtime, not the command's exit. (b) `git checkout <file>` to
   undo a one-line MUTANT reverted the whole file — including forty lines of uncommitted work in it. Copy
   the file aside and restore from the copy; `git checkout` cannot tell your mutant from your work.
7d. **BEFORE YOU REPORT A DEFECT, ASK WHETHER YOUR TEST METHOD PRODUCED IT.** Twice in one day I built a
   measurement that showed a fix was broken, and twice the measurement was the broken thing. (a) I pointed
   `--deps` at a hand-built old-format report while `--dep-inits` was on — which RE-SCANS the packages on
   disk and chains its own fresh reports, so the report I wrote never participated; I read the fix working
   as a compatibility regression. (b) I removed a fault injected by an ENV VAR and expected a cached abort
   to clear — but the env var is deliberately outside the cache key, so replay was the designed behaviour;
   the real clearing guard fires on a CONTENT change, and does. **A false defect costs the same review time
   as a real one and burns credibility with whoever fixed it.** The check is cheap: name the thing your
   arms actually differ in, and confirm it is the thing you think you are varying.
7e. **CHECK THAT THE THING READING YOUR OUTPUT CAN NAME WHAT IT READ.** A mutation round reported the
   WRONG tests failing, in a pattern that looked exactly like a real inversion, and two rounds went into
   theorising about the engine before the CLI contradicted the harness. Cause: the results parser matched
   `<testcase name="X" …>(.*?)</testcase>` against JUnit XML — and a PASSING testcase is SELF-CLOSING, so
   the regex ran from one test's name to a LATER failing test's close tag and attributed the failure to the
   wrong test. Item 7 says delete the output before you measure a control; its sibling is that **a parser
   which silently mis-attributes is worse than one that errors, because its output is plausible.** Prefer
   the tool's own reporting to a regex over its artifacts, and when a mutation result surprises you,
   confirm it from a second channel before theorising about the engine.
8b. **INSTRUMENTING AN ANALYSER CHANGES WHAT IT ANALYSES — including itself.** A probe added to swift's
   hot receiver-resolution path read an env var, and candor's own self-scan then charged Env+Fs to 26 of
   its OWN functions. The probe was correct and its finding was correct; shipping it would have written
   the measurement into the product's report. Instrument freely, but treat the probe as an ARM to be
   removed, and never leave one in a path the engine walks over itself. (Cf. item 7: this is the same
   family as reading a stale artifact — the tool and the thing measured are the same object.)
7f. **CONCURRENT AGENTS SHARE THE BINARIES, THE HARNESS AND THE SCRATCHPAD — A MUTATION TEST IS A
   DESTRUCTIVE WRITE TO SOMEBODY ELSE'S MEASUREMENT.** Four per-engine agents ran at once, every one of
   them instructed (correctly) to verify guards by mutating them out and re-running the shared four-way
   conformance suite. I did the same thing myself to prove PART 22 catches a dropped surface: deleted the
   `paths` fold from rust's `apply_dep_fn`, rebuilt the shared release binary, ran conformance, restored.
   The rust agent's conformance run landed inside that window and reported a divergence — `cmds` travelled,
   `paths` did not — **which it could not reproduce in 129 subsequent runs and honestly flagged as
   unexplained.** It was mine. Two further collisions the same hour: one agent clobbered another's
   scratchpad directory, and a candor-java jar rebuilt mid-run aborted a conformance pass.
   - **A divergence on an engine that is not yours is not your finding** until it reproduces.
   - Keep mutation windows short; restore before touching the shared suite.
   - The orchestrator owns this: fanning out per-repo work is safe, but per-repo agents that all run ONE
     shared differential harness are not isolated, and saying "one agent per repo, no file conflicts" is
     true of the source and false of the build outputs.
7g. **A TEST CAN PIN THE BUG. Ask what CHANNEL each suite can see.** java's `test/smoke.sh` asserted a
   coverage row containing a *permanently stale* version string — it had encoded shape 1 (a distrusted
   report still granting coverage) as a REQUIREMENT, so fixing the defect broke the suite that was
   supposed to protect it. Worse: `gradle test check` and the four-way conformance suite were green
   through all five preceding commits and **neither could see it**, because the assertion lives in
   stderr and those two legs read the report and the exit code. A green suite is evidence about the
   channels that suite reads. Enumerate them — report content, exit code, stderr, sidecars — and know
   which leg covers which, because a defect will sit in the channel nobody's assertions look at.
8c. **"UNTESTABLE" AND "NOT LOAD-BEARING" ARE DIFFERENT CLAIMS, AND A GUARD CAN BE ONE WITHOUT THE
   OTHER.** This queue filed swift's `typeSurface` exact-match guard as UNPROVEN, on the grounds that
   relaxing it to a suffix match failed no test. The engineer who landed the missing index key then
   measured the counterfactual instead of assuming it: with the third key mutated back OUT and the suffix
   mutant left IN, the CONSUMER rows go green again — a wrong answer simply misses, harmlessly — and only
   a producer-side assertion nobody had written still fails. So the guard was always OBSERVABLE in
   principle; what the key changed is that a wrong answer now **LANDS** instead of missing. Two distinct
   properties: *can this guard's absence be detected* and *does this guard's absence cost anything*. The
   row conflated them, and the fix is not to argue about which was meant but to state both — a guard that
   cannot be detected needs a test, a guard that costs nothing needs deleting, and they are not the same
   remedy.
9d. **A SOUNDNESS ASSERTION CAN FORCE A SOUNDNESS DEFECT.** rust's §4 writer carries a `debug_assert`
   demanding that any `Unknown` name one of the four §4 kinds. **No kind projects to `unresolved`** — so
   when a chained dep declared `Unknown` with NO reason, the assertion left no legal way to say "no
   reason", and the fix was to INVENT one (`callback:…`), which classifies `indirect` and made rust the
   four-way outlier on every `Unknown[class]` gate. The assertion was too broad: §4's own definition of a
   source ("its own body has the unresolvable call") exempts a chained CONSUMER, which is not a source.
   **An invariant that cannot express a legitimate state will be satisfied by fabricating an illegitimate
   one — and that reads as compliance.** Any engine with an equivalent assertion has the same trap.
   Corollary found with it: **`callback:` is NOT the residual bucket** several comments in this codebase
   call it. §4 defines it as an unresolved HIGHER-ORDER invocation; the residual class is reached by the
   ABSENCE of a reason, not by a token standing in for one.
8. **An A/B diff cannot show that a mechanism never fires, or fires on the wrong thing.** It shows what
   CHANGED. Two defects this vein produced had perfectly clean A/Bs: `typeSurface` was near-inert because
   the producer read module names as types, and swift's half-1 provenance conjunct was matching `max()`,
   `min()` and the engine's own local functions. Both were invisible in the output and obvious in the
   COUNTS. **Instrument the preconditions** — how often does the trigger hold, and on what? — and read the
   ratio, not just the diff. A trigger that fires 239 times on shapes you did not intend is not "bounded
   as designed", and a bound that admits nothing on a real modular crate is usually a keying bug.
   **Third instance, 2026-07-26, and this one was an ORDERING fact nobody would have guessed:** the arm
   testing "what if the dependency hierarchy widened the subtype index" came back byte-identical with zero
   cost — flattering, and wrong. `buildSubtypeIndex` runs BEFORE `loadCrossDeps` populates the dep
   hierarchy, so the one-line widening cannot fire at all as a one-liner. With the load hoisted so the arm
   is real, the same change costs **8 losses against 113 gains** — seven functions lose a disclosed
   `Unknown` and one loses a concrete `Net`. **A zero-delta arm is a claim about the EXPERIMENT before it
   is a claim about the change**: prove the mechanism fired before you report that it changed nothing.
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
9c. **AN AUTOMATED FIXER WILL DELETE YOUR REASONING, AND THE DIFF LOOKS LIKE A CLEANUP.** `clippy --fix`
   rewrote a `match` into `.map` and removed with it a comment recording a SOUNDNESS argument — why an
   unpinnable local `fmt` is treated as pure rather than `Unknown`. The code was equivalent; the record of
   why it is allowed to be that way was not, and nothing in the diff said so. Item 9 says a comment is an
   assertion and will be believed; its converse is that a comment carrying the only written form of an
   argument is load-bearing, and a mechanical rewrite has no way to know. Read a `--fix` diff for deletions
   before you read it for changes.
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
made it safe. **Cite a precedent to justify attempting something; measure to find out what it costs.**

**The reverse check came back POSITIVE, twice.** swift's carve-out did not distinguish erased from
monomorphized receivers, and the engine that supplied the precedent WAS fabricating — `d62dd69` closed the
`some P` parameter, and `02fb0ad` closed four more spellings that the parameter-typed check could not see
(`[T]` under a `<T: P>` bound, `[some P]`, their `forEach` form, a `T`-typed field of a generic type, and
`extension Array where Element: P`). A precedent inherits the other engine's unexamined assumptions along
with its result — and the traffic goes BOTH ways: rust's measurement is what sent anyone to look at swift.

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

### java — 6 mechanism families DONE, and the JVM half of the vein has NO open row (fixture 15 silent-pure → 0; six gates exit 0 → 1 on the effect itself — the dep-interface row went `deny E Unknown[dispatch]` at half 1 and now flips on `deny Fs` too, and the abstract dep CLASS flips on `deny Fs` outright)
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
      why an abstract dep CLASS — jackson's `ObjectIdGenerator`, the case originally recorded here — was
      left open here. **It is now CLOSED (`333cf10`, its own row below), and NOT by `typeSurface`:** the
      producer knows something no consumer can read off a call site, namely `ACC_ABSTRACT` on the member,
      and that flag answers the same question the opcode answers, one step earlier and with better
      evidence. The claim that this was "the sharpest thing half 2's `typeSurface` would buy java" was
      wrong — half 2 buys java nothing here.

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
      - **RESIDUAL — CLOSED by `800f471`, the way its own test instructed.** The receiver-driven form (`w.write("x")`)
        fails only on `isJavaIoStreamType`, which needs the DEPENDENCY's supertypes. Relaxing it was
        measured on 11 split-and-chained libraries: 161 sites over 31 dep types, only 3 of the 31 are
        java.io streams — the rest (`PacketLineOut.writeString`, `RebaseState.readFile`,
        `ObjectWriter.writeValueAsString`) are already resolved by the exact-hash join. ~90% wrong-receiver
        fabrication, so the gate stays shut. Pinned as a test that says: *if this passes, the hierarchy
        arrived — delete the residual, don't relax the gate.*
- [x] **CONSUME `<report>.hierarchy.json` — DONE, `800f471`, and it closed the write/read residual with
      it.** Traced on real code: httpclient's `LoggingManagedHttpClientConnection.getSocketInputStream`
      went `[] → ['Net']` because `nearestDepFn` stopped at the first DEPENDENCY class — it could not see
      that class's own super, so the declaring body one hop further up (httpcore's
      `BHttpConnectionBase.getSocketInputStream`, `Net` in the chained report) was never reached. Seven
      functions recover Net; four had it DECLARED already, so `overdeclared` shrinks to match.
      - **The one-line version is unsound and that is the whole lesson.** Reading the sidecar inside
        `Cha.externalSupers` gets everything downstream for free — and `externalSupers` feeds
        `buildSubtypeIndex`, so a project `P extends DepBase` where `DepBase implements Runnable` newly
        lands in `subtypeIndex[Runnable]`, an `r.run()` site finds a non-empty CHA, and the JDK-SAM gate
        that raises the honest `callback:` Unknown fires ONLY on an empty target set. Disclosed Unknown →
        confident purity claim, manufactured by a change whose argument was that it only adds knowledge.
        Scoped to the two dep-facing walks instead, with a test asserting the SCOPE (`externalSupers` on a
        sidecar type must still return empty) rather than a comment claiming it.
      - Measured: 5 chained pairs, 7 gains, 0 losses, entry counts identical, **Unknown counts unchanged on
        every pair** — the scoping is what that last column proves. `CANDOR_DEPHIER_DEBUG` instruments both
        halves (18–276 types loaded per pair; 44 and 54 consultations, every hit a correct fact).
      - Not version-gated, deliberately: the sidecar carries no effect claim, only a route, and the entry it
        routes to is still version-gated — so a stale hierarchy reaches a stale entry and yields Unknown.
      As originally filed: `ReportWriter.writeHierarchy` emits every project class's direct supers +
      interfaces beside every scan; `Loader.loadCrossDeps` read only the report JSON, so nothing on the
      consumer side ever opened the sidecar. That is the `typeSurface.implements` information the
      abstract-dep-CLASS row, swift row 3 and the write/read residual were all blocked on — and for java it
      needed no format rung at all, only a consumer.
      **THE FOLLOW-ON IS SETTLED — and BOTH halves of "the abstract-dep-CLASS row wants the hierarchy in
      the SUBTYPE INDEX" turned out to be wrong.** That sentence stood here as the one use `800f471`
      refused, needing "its own argument about what happens to the Unknowns that resolution would
      suppress". The argument was measured before a line of fix was written (item 8: a shadow subtype
      index built from the sidecar, compared against the real one at every polymorphic dispatch site, over
      seven chained real jar pairs / 68 539 sites):
      - **It cannot close the row.** `buildSubtypeIndex` files PROJECT `ClassNode`s and `chaTargets` needs
        one to test `declaresConcrete`, so a DEPENDENCY's implementer never enters the index however wide
        the hierarchy gets. The two-tree fixture is exit 0 in that arm too. The row's impl is in the dep;
        the index only ever holds the consumer's classes.
      - **And it costs.** 737 sites go empty-CHA → non-empty; at report level 113 gains and **8 LOSSES** —
        7 functions lose a disclosed `Unknown`, one loses a concrete `Net`. httpclient's
        `IdleConnectionHandler.closeExpiredConnections` and three siblings become confident purity claims
        on methods that close network connections, because the target set substituted for the disclosure
        is not the true one (httpcore's own implementers are outside the scan). **The gate `800f471`'s
        comment named is not the one that fired**: instrumented per site, the JDK-functional-SAM
        `callback:` branch suppressed ZERO, as did the missing-project-impl branch — what suppressed was
        half 1, whose conjunct 4 is the same "the project CHA is empty" test. The argument generalises and
        the illustration did not; the property to protect is EVERY Unknown branch conditioned on an empty
        target set, not the one that was easiest to picture.
      - **The first arm said byte-identical, zero cost — the flattering way again (item 7), and the cause
        is worth carrying.** As a literal one-liner inside `externalSupers` the widening is **INERT**:
        `runScan` builds the subtype index BEFORE `loadCrossDeps` populates `depSupers`. So the hazard
        `800f471` argued against could not fire as written, and a future reordering of `runScan` would arm
        it silently. The numbers above are from the arm with the load hoisted. **A control that produces
        no diff may be measuring nothing — check the mechanism is reachable before believing its zero.**
      The refusal + the numbers now live in `Cha#depDirectSupers` (candor-java `cb8c1aa`), so nobody has
      to re-derive them, and the surviving guard is named there: `CrossScanBoundaryTest`'s "`externalSupers`
      on a sidecar type must still return empty" holds under either ordering.
- [x] **dispatch through a dependency's ABSTRACT CLASS — DONE, candor-java `333cf10`, producer-side, and
      the consumer changed not at all.** The last open JVM row. `Store s = Factory.build(); s.save()` where
      `Store` is a dep's abstract class read SILENT-PURE (absent from `functions`, counted in ⟨0.21⟩
      `analyzed`) — INVOKEVIRTUAL, so half 1 deliberately does not disclose, and the project CHA is empty
      because the implementer is in the dependency. Gate `deny Fs` exit 0 → **1**, single-tree control exit
      1 in BOTH arms.

      **The discriminator is the ACCESS FLAG, and it is the producing side of the three-row rule.** Absence
      under a key licenses a purity claim only if the key names something that COULD have had a body.
      `ACC_ABSTRACT` on the member proves the JVM will never run the declaration `lib/Store.save` names, so
      no report — of any version, from any engine — can ever answer that key. Half 1 reads the OPCODE at the
      consumer; this reads the access flag at the producer, which is strictly better evidence. So the
      `interfaceUnion` emitter admits abstract CLASSES and publishes their ABSTRACT members, the entry lands
      under the key `crossDepJoin` already forms, and there is **no consumer change: no CHA, no subtype
      index, no Unknown gate, no new resolution path.** The template ("emit the call shape the join already
      understands") for the third time.

      SCOPE, asserted by tests not by comments: a class publishes only its ABSTRACT members. A concrete
      member's key names a body that exists and was analysed, so the report's answer under it — the entry,
      or silence meaning pure — is already TRUE, and a union over its overrides could only widen a true
      answer. Verified by mutation: removing the `ACC_ABSTRACT` member skip fails
      `aConcreteMemberOfTheSameAbstractClassPublishesNoUnion` and only that; reverting the class admission
      to interfaces-only fails the four abstract-arm tests. Existing bounds all apply unchanged (all-pure →
      publish NOTHING; >`CHA_FANOUT_LIMIT` open hierarchy → `["Unknown"]`, never the smear and never
      silence). **The pre-existing test that asserted the old scope was REWRITTEN, not deleted** — half its
      premise ("an abstract dependency CLASS receiver is the documented residual") was this row, and the
      half that was always a scope survives as `aCONCRETEClassMethodIsUntouched`.

      **A comment claim the measurement falsified mid-flight, item 9 in its exact shape.** It read "an
      abstract member has no body, so no real entry can claim its hash — the merge path is unreachable for
      it." False: `writeJson`'s filter keeps a BODILESS entry when the method is framework-rooted or its
      class declares a capability — **17 such entries across twelve real dep reports**, logback's
      `AppenderBase.append` among them, an entry point carrying `inferred: []`. The merge is *right* there,
      for the reason `48a5f18` gives: `[]` under a hash a consumer keys on IS a purity claim about the
      dispatch and it was false. Verified widening-only across all 17.

      Measured, seven chained pairs, both arms' jars kept by content hash and the final jar re-run to
      reproduce its arm byte-for-byte (item 7b): flag OFF every dep AND consumer report **byte-identical**;
      flag ON producer +59 entries over 7 383 (0.8%), all marked, 17 widened / 0 narrowed / 0 removed;
      flag ON consumer **14 gains, 0 losses, Unknown 8 330 → 8 336 (UP, never down** — a dropping Unknown
      count is exactly what the refused route does). Gains traced to bytecode, and the headline is the case
      this queue recorded by name: jackson-databind's `WritableObjectId.generateId` does `INVOKEVIRTUAL
      ObjectIdGenerator.generateId` on a field typed by jackson-annotations' abstract class, whose
      `ObjectIdGenerators$UUIDGenerator.generateId` is `UUID.randomUUID()` — `Rand`, reaching
      `BeanSerializer.serialize` and 7 more. The other 6 are logback appender/converter dispatch going
      `[]` → `['Unknown']`, the disclosure direction.

      **Residual, deliberately not taken here:** a CONCRETE dep method that is overridden effectfully still
      answers only for its own body across the boundary, where in-scan the same site is charged the CHA
      union. That is the `48a5f18` "the engine contradicts itself across the scan boundary" argument one
      rung down — but unlike the abstract case the key IS answerable and the answer IS true, so it is a
      narrower question than a purity claim, and its blast radius (every non-final method of every
      non-final class) wants its own measurement.
- [x] **`reentryTargets` fanned only DOWN the subtype index — FIXED, candor-java `9ae68f7`.** A SINGLE-TREE
      silent under-report, found by a smell rather than a report: making the chained arm walk a dependency's
      supers left the in-scan control strictly LESS complete than the cross-boundary case, which is the
      wrong way round and meant the in-scan gap had been there all along. `new Formatter(half)` where `Half`
      overrides `append(char)` and inherits the effectful `append(CharSequence)` reported `[]`. Now walks
      each subtype's own chain with per-OVERLOAD shadowing — the same rule the cross-boundary
      `nearestDepFnsNamed` uses; per NAME would drop the inherited overload, no shadowing would charge a
      replaced body, and the fixture asserts both directions. One real gain on the corpus, traced to
      bytecode: jgit's `PackWriter.writeChecksum` went from a purity claim to the effect set the same
      report already gave `CancellableDigestOutputStream.write(byte[],int,int)` — which is exactly what
      `out.write(packcsum)` runs, since `PackOutputStream` declares no `write` of its own.

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

  **DONE — candor-ts `db64b1e`, and the wire-compatibility half is the part that needed the care.** Keys are
  now `<pkg>#<relpath>.<module>` and the consumer looks up the module its SPECIFIER names. A new consumer
  meeting an OLD report (bare `<pkg>#<module>`) honours the old key and returns the old union answer —
  silence there would have turned a precision fix into the very under-report this vein exists to close, and
  the bare tail is a structural discriminator rather than a version guess. Measured: 8 targets, unchained
  byte-identical; chained 0 gains, 0 losses, 84 narrowed, **0 `Unknown` removed** and nothing went from
  disclosing something to disclosing nothing. The 13 concrete effects removed were each traced to a file no
  import runs (`react/umd/react.development.js`, next's polyfills, angular's schematics codemods).

  **VERIFIED INDEPENDENTLY** (four fixtures of my own, not the agent's): per-file keys are emitted; the
  load-bearing premise holds — the entry unit's `inferred` really does carry a transitively-imported file's
  `Fs`; the consumer charges that `Fs` and NOT the unimported sibling's `Net`; and an old-shape report with
  two colliding units returns `['Fs','Net']`, the union, unchanged.

  **A measurement trap found while verifying, worth carrying:** `--dep-inits` RE-SCANS the packages on disk
  and chains its own fresh reports, so pointing `--deps` at a hand-built report while `--dep-inits` is on
  measures the fresh scan, not the report you wrote. It made a correct fix look like a compatibility
  regression for two rounds. To exercise the compatibility path, remove the package from disk so the
  rescan has nothing to contribute.
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

  **SHIPPED as candor-ts `5057026`, then INDEPENDENTLY VERIFIED — and the verification found two defects in
  it plus two more the rung exposed, all four now closed.** The A/B was not re-run and agreed with; the
  attack was the other direction, per item 0. Every fix carries a two-tree fixture, a single-tree control,
  and each guard mutated out with the named failing test recorded.
  - **FABRICATION, and a regression the rung introduced — candor-ts `0185649`.** The ambiguity counter read
    only the `.` typings, but the union hash is `pkg#Iface.member`, a package plus a BARE name, so every
    interface of that name in the package maps to it however it is exported. A `subkit` with an effectful
    `Store` on `.` and an unrelated PURE `Store` on `./sub` published the first as the answer for both, and
    a consumer of `subkit/sub` FAILED `deny Fs`; the pre-`5057026` engine disclosed
    `Unknown[dispatch:subkit.Store.save]` and exited 0. The census now covers `types`/`typings`, every
    `.d.ts` in the `exports` tree and `typesVersions` (which names files without their extension — 8 of 343
    corpus packages declare one, 7 with a star, so the star is expanded from disk). **ONE program over all
    the roots**, because a barrel `export * from './sub'` must give back the same declaration NODE from both
    entry points or every package shipping a barrel is refused. A truncated expansion refuses the typings
    arm outright: half a census re-opens the fabrication.
  - **A CONFIDENT WRONG ANSWER, older than the rung — candor-ts `d7060ca`.** "The in-scan arm wins a name
    collision" dropped the typings arm on the NAME, throwing away the only evidence the engine had that the
    name means two things. An internal `interface Store` (implementer does Net) beside the public one the
    typings pair to an effectful `FileStore` published `mixkit#Store.save -> ['Net'] unresolved:false`: a
    fabricated Net, a dropped Fs, no disclosure. The rule is now REDUNDANCY — drop the typings arm only when
    every class it names is already in the in-scan set — so the shadow case survives and a collision that
    brings new information makes the name ambiguous and refuses both. Instrumented: 27 typings arms across
    the corpus, **21 collide and all 21 are redundant**, so @ukri-tfs/common's seven entries survive by the
    rule rather than by exemption.
  - **NO FAN-OUT BOUND — candor-ts `fc8d297`, the ts sibling of java `429c7b2`.** The emitter unioned every
    implementer while the in-scan dispatch site bounds at 12, so the producer published what its own
    dispatch refuses to resolve: rxjs `Operator` has 70 implementers, 16 reaching Net, and rxjs's own
    `Observable.subscribe` reads `Unknown[dispatch:…Operator.call]` while the report offered a consumer
    `rxjs#Operator.call -> ['Net','Unknown']`. Now ONE named `CHA_FANOUT_LIMIT` read by both sites (java left
    two literals and that is how they drifted), publishing `['Unknown']` + reason past the bound — never
    silence. Measured across 353 targets the tail is thin but real: 43 of 44 arms have ≤5 implementers and
    the 44th has 70, so **the argument is the self-contradiction, not the distribution**. No
    `isClosedHierarchy` analogue exists in TS (no `sealed`).
  - **PROPERTY-SPELLED INTERFACE MEMBERS — candor-ts `d9b8c34`**, the residual `5057026` recorded, closed in
    BOTH arms. `run: (x) => void` is a PropertySignature over a FunctionTypeNode and the checker resolves a
    call to the TYPE NODE, which has no name and no owner — so three sites that key on a declaration's name
    formed no key at all. @ukri-tfs/email's whole `SendStrategy` is spelled this way (four implementers, zero
    method signatures). One `memberSigOf` hop, called from all four sites; only a FunctionTypeNode qualifies.
    Chained pair measured end to end: `@ukri-tfs/email#EmailService.send` `['Unknown']` → `['Net']
    invisible:['@aws-sdk/client-ses']`, reaching `invite-service#EmailServiceProxy.send`, 0 losses. It also
    repairs 139 disclosure strings that named the PROPERTY as the owner type (`dispatch:<mod>.<prop>.member`).
  - **Two carried findings. (1) is DONE, candor-ts `4dad22d`; (2) is DIAGNOSED and the question it was filed
    under is the wrong question.**
    1. ~~The ts dep-join copies `inferred` and `invisible` only, so a chained dep's Unknown loses its REASON
       CLASS at the consumer and falls back to `unresolved`~~ — **CLOSED**, and the root cause was the same
       one candor-java `6ab26e4` found: DUPLICATION. The CallExpression arm and the desugared-declaration
       arm each spelled the apply-a-dep-entry copy out, they had already drifted, and the reason class was
       added to neither; there is one `applyDepHit` now. A report failing the §2.1 check keeps the BARE
       Unknown — its reasons are assertions from a build we do not trust — and that is asserted, not
       assumed. Measured, 4 chained @ukri-tfs services: 0 effect gains, 0 losses, entry counts identical,
       **606 functions gain a real reason class** where they read `unresolved`; producer reports
       byte-identical. Gate both ways: `deny Net Unknown[reflect]` exit 0 → 1, `Unknown[native]` stays 0.
    2. **The malformed `….member` reasons are NOT "all the function-type-under-a-TYPE-ALIAS shape", and
       "what should the owner be" has no answer because there is no owner.** Measured on a fixture, three
       producing shapes, and in two of them the owner is not a type at all:
       - `type Handler = (x) => void` → `dispatch:<mod>.Handler.member` (the filed shape — owner is a type,
         member is the literal string `member`);
       - `makeFn()("a")` where the RETURN is an inline function type → `dispatch:<mod>.makeFn.member`,
         naming a **function** as the owner type;
       - `const slot: (x) => void` → `dispatch:<mod>.slot.member`, naming a **variable**.

       And on the ukri-tfs corpus the dominant form is neither: **31 of 68 are `dispatch:type.member`**,
       both halves fallen back. So the string violates SPEC §4's NORMATIVE `dispatch:<owner-type>.<member>`
       in the OWNER as often as in the member, and the dispatch-frontier consumer
       (`possibleViaUnknownDispatch`), which parses that payload against the hierarchy, can never match it.

       The settled diagnosis: in every one of these the callee is a function VALUE with no owner type and
       no member, which SPEC §4 assigns to **`callback:`** ("an unresolved higher-order / owner-less
       invocation… whose target and owner type are not both known", best-effort spelling) and explicitly
       withholds from `dispatch:`. The engine already gets this right where there is no name to grab —
       `f: (x) => void` emits `callback:param#0` and nothing else — and the alias shape emits **both**, the
       correct `callback:` and the malformed `dispatch:`, for the same site. So this is a
       RECLASSIFICATION, not a better owner string.

       **Deliberately NOT landed with the rest of this pass, for two reasons.** It NARROWS a gate: 68
       reasons over 64 functions, and for **16 of those functions it is the only reason**, so their class
       moves `dispatch` → `indirect` and a `deny E Unknown[dispatch]` rule stops firing where it fires
       today. And `unknownWhy` vocabulary is TIER 1 and four-way, so ts should not move a shape's class
       unilaterally — ask rust/java/swift what they emit for an owner-less function value first. A
       strictly-widening interim (ADD the `callback:` reason, keep the malformed `dispatch:` one) is
       available and loses no gate, but leaves the malformed string in the report and was not taken.
  - **Worth carrying methodologically:** the ambiguity guard's SILENCE is honest in ts specifically, because
    half 1 discloses an absent interface key at the consumer — mutating the fan-out bound's Unknown to a
    `continue` still leaves the consumer disclosing. That is a property of the layer beneath, not of the
    emitter, and it is why the producer-side tests are the ones that catch it. Also: scratch copies of the
    engine left in the scanned repo showed up as four "new entries" in the self-scan A/B — a measurement
    apparatus inside the target.
- **A SECOND adversarial review of the ts boundary work found three more, all now closed (2026-07-26/27),
  and the pattern is that each one was a REFUSAL AIMED AT THE WRONG SIDE.**
  - **`db64b1e`'s wire-key change was invisible to §2.1 — candor-ts `651c9f9`.** Module unit hashes moved
    from `<pkg>#<module>` to `<pkg>#<relpath>.<module>` without a `package.json` bump, so both builds called
    themselves `candor-ts-0.23.1`. The comment claimed "an OLD consumer over a NEW report treats the whole
    report as stale and downgrades it to Unknown"; measured with the pre-change build as the consumer, that
    is **false**, and the bump alone does not fix it: **staleness rewrites the CONTENT of the keys a report
    carries and can never conjure a key it lacks**, so a lookup that misses, misses whatever the version
    says. The importer read ABSENT (a ⟨0.21⟩ purity claim) with `deny Fs` at exit 0, single-tree control
    exit 1 in both arms. Nothing a NEW report can CARRY helps either — the old consumer is frozen and reads
    one discriminator — so the durable rule is the forward one: **an untrusted report grants no COVERAGE**,
    since §2 rule 3 turns its silence into a purity claim on the authority of a report we just refused to
    trust. Now a key it fails to answer falls back to the κ ledger's `invisible` hedge and an import backed
    only by it discloses Unknown. Real code: one dep report marked as another build gives invite-service 76
    new hedges and 10 functions that were absent entirely, 0 effect losses. **Standing rule now in
    candor-ts AGENTS.md: a report-KEY change bumps the build id in the same commit — necessary, and not
    sufficient.**
  - **A truncated typings census refused the EVIDENCE — candor-ts `90655d9`.** `typingsRoots` gives up past
    128 `.d.ts` and dropped the typings arm when it did. The evidence is the only thing that can say a name
    means two things, so `ifaceNameCounts` read 1 instead of 2, the never-guess guard did not fire, and the
    package published its INTERNAL `Store` (Net) as the answer for the PUBLIC one (Fs) — `d7060ca`'s
    fabrication restored for exactly the packages big enough to hit the cap, and `d7060ca`'s own test could
    not see it (its fixture has no in-scan arm, so "publishes nothing" could not distinguish a dropped arm
    from a refused publication). The refusal moved to the PUBLISHING side, routed through the never-guess
    guard already there: **two declarations of a name, and a census that cannot prove there is only one,
    are the same evidential position.** Bite measured across 8 real `node_modules` trees: 3 packages in
    3213 (rxjs, @angular/common), costing 7 union entries, every one a bare `['Unknown']`.
  - **A real entry claiming a union's hash suppressed the union — candor-ts `67d092d`, the ts sibling of
    java `48a5f18`.** TS reaches the collision by a BARE NAME (`pkg#Store.save`), so any `class Store`
    claims the key an interface-typed consumer forms — by declaration merging or by two unrelated
    declarations across files. In-scan `['Fs','Net']` and `deny Net` exit 1; split and chained the consumer
    read an unrelated class's `['Env']`, exit 0, plus a fabricated `deny Env` catch. **It is NOT
    `mergeUnionInto`, and measuring the literal port is what said so:** java merges into the interface's own
    `default` METHOD, whose in-scan site already carries the CHA union; TS interfaces have no bodies, so the
    claimant is always a CLASS body, and java's merge ported literally charges an env-reading class with
    `['Env','Fs','Net']` and fires the producer's own `deny Net` on it — the hazard java's comment names one
    field along, at `overdeclared`. The union goes in its own marked entry under the shared hash and SPEC
    §2's documented duplicate-hash UNION rule joins it: same answer, no analysed unit rewritten. **A
    precedent tells you the OUTCOME to reach, not the mechanism to reach it with** — the sibling of the R4
    lesson, one rung along.
  - **Found while measuring, closed with them — candor-ts `e66f29e`:** a union entry that INHERITED Unknown
    from an implementer published `inferred: ['Unknown']` with `unresolved` absent, i.e. false. `unresolved`
    was set on the `broad` arm only. A TIER-1 trust marker failing OPEN, live on all seven of rxjs's unions.
  - **Two zero-delta A/Bs in this pass were claims about the EXPERIMENT** (item 8), and each needed a
    different answer. The §2.1 arms are byte-identical because no run there HAS a version mismatch — so the
    mechanism was armed on real code instead (one report re-marked). The union-hash arms are byte-identical
    because the trigger never fires: instrumented over **270 producer-scanned packages, a union hash is
    claimed zero times**, which makes the corpus the fabrication CONTROL and the fixtures the evidence — the
    posture java's `dd81bfa` landed under. **A third arm measured nothing at all and looked clean:** five
    `--workspace` targets that chained "0 workspace dep report(s)", byte-identical for a reason with nothing
    to do with the change. Check the chain actually chained before reading its diff.
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
- [x] dispatch over an IMPORTED protocol with LOCAL conformers — `eae2de2`, plus **TWO erasure fixes it
      needed and shipped without**: `d62dd69` and `02fb0ad`. Needs no dep report: Swift spells a conformance
      to an imported protocol in the same inheritance clause, so `subtypesOf` already had it.

      **It took THREE carve-outs, and only one of them shipped with the rung.**
      1. `RAW_VALUE_BASE_TYPES` (in `eae2de2`) — `enum Rank: String` puts `String` in the inheritance clause,
         so an unguarded CHA sends every call on a String-typed value into raw-value enums' methods.
      2. **ERASURE, the `some P` parameter (`d62dd69`)** — found by rust's R4 measurement pointing back here.
         `typeName` collapses `some P` and `any P` to `P`, so the opaque spelling inherited the existential's
         CHA. Note the mid-flight correction in `81a9dc3`: the first version enforced it by WITHHOLDING the
         receiver's type, which took the §2 dep join with it and made an Fs-performing function read PURE —
         one sin traded for the other. The gate belongs on the CHA arm alone.
      3. **ERASURE, everything that is not a parameter's own type (`02fb0ad`)** — `isOpaqueParam(p.type)`
         answers the question for `func f(_ s: some P)` and for nothing else. `[T]` under a `<T: P>` bound,
         `[some P]`, the `forEach` closure form of either, a field typed as the enclosing type's generic
         parameter, and `extension Array where Element: P` all resolve a receiver to the bound `P` too, and
         all are monomorphized by the caller. Each was measured charging the effectful conformer's Env to a
         function whose only call site passes the pure one. The bare `<T: P>(_ x: T)` parameter escaped by
         ACCIDENT (`params` records the spelling `T`, which resolves to nothing) — which is exactly why the
         container and field paths, which deliberately resolve to the bound for R28/R39, did not.
         `mono` now travels with `rootOf`'s resolution instead of being re-derived at the call site, because
         the same receiver spelling resolves through `vars`, a field, a field-walk or a subscript element and
         only the answering branch knows which.

      *This is the swift analogue of the same trap rust hit at R4: an imported-supertype CHA is only safe
      with explicit carve-outs, and you find out how many by measuring, not by enumerating.*

      **RAW_VALUE_BASE_TYPES is NOT subsumed by erasure** — checked by removing it with the erasure gate in
      place, and `plainString(_ s: String)` reads Env via `Rank.lowercased`. They answer different questions:
      erasure is about the receiver's SPELLING, the raw-value carve-out is about Swift's inheritance clause
      being overloaded for a CONCRETE receiver that nobody monomorphizes.

      A/B for `02fb0ad`, 11 real Swift targets / 10 609 entries (pollen, candor-swift, swift-syntax,
      Alamofire, vapor, TCA, SQLite.swift, swift-argument-parser, console-kit, Files, swift-log): zero entry,
      effect, Unknown and unknownWhy deltas, and ONE traced change — TCA's `TransactionPublisher.receive`,
      whose `var upstream: Upstream` (`<Upstream: Publisher>`) was CHA'd over TCA's five local Publisher
      conformers though its one construction site passes a Combine `AnyPublisher`. Instrumented, the gate
      fires exactly once across all eleven: the trigger is real and this corpus barely exercises it.
- [x] **factory-bound receiver — the HONESTY half is CLOSED (`47bb69a`).** `let c = build(); c.fetch()` no
      longer reads pure: it discloses `Unknown[dispatch:untyped cross-package receiver]`. The claim above
      that "there is no evidence `c` came from the dep at all" was **wrong** — the callee name is right
      there, and `returns` failing to hold it is itself the evidence that it came from outside the target.
      Note what this does and does not move: `deny E Unknown[dispatch]` now flips, `deny Fs` does NOT. Half 1
      converts the cardinal sin into a disclosed gap; it does not recover the effect.
- [x] **factory-bound receiver — the DETERMINATION half — DONE, candor-swift `f537ac3`.** The rung is
      no longer blocked: SPEC §2 fixes `typeSurface.returns` and rust shipped it at `a1e53e7`. swift is
      the second engine to take it. Canonical fixture goes exit 0 → **exit 1** on `deny Fs`, single-tree
      control exit 1 in both arms. Every one of rust's four reverted defects is a requirement here with a
      mutation that was RUN and confirmed to fail a named test.

      **Swift's door into defect 1 is the NESTED TYPE, not the module.** `Conn` and `Mock.Conn` live in
      one module; a leaf-keyed surface makes them one string and the PURE `openMock()` charges the real
      client's Fs. A bare `-> Conn` written inside `enum Mock` means `Mock.Conn`, so the spelling resolves
      OUTWARD from its declaring type path and must match a declared path EXACTLY. `localTypes` keeps only
      the simple name, so a new `localTypePaths` was needed — the leaf-vs-qual distinction did not exist
      in the engine before this.
      - **The wrapper refusal needed the fixture to earn it.** `plainNominalTypeName` is stricter than
        `typeName`, which peels `Conn?` → `Conn`. The first fixture could not tell them apart; making
        `Conn` declare an effectful `map` and having each wrapper consumer call the WRAPPER's own `map`
        is what turned the rule into a test. `-> Box<Conn>` is the sharp row: `Box` IS a declared local
        type, so it is refused for being GENERIC, not for failing to resolve.
      - **PROTOCOL returns are published, and that is the swift-specific half.** `func make() -> Proto`
        is the commonest Swift factory; the key it forms names a requirement with no body and is answered
        only by an `interfaceUnion` entry. Asserted BOTH ways: dep scanned plain → the row must DISCLOSE
        (resolving it anyway would mean a guess answered the key); dep scanned with
        `CANDOR_WORKSPACE_CHAIN` → the row RESOLVES. Surface and union are layered, never redundant —
        the same layering the ts row records.
      - **Counts, not output** (item 8): producer 3 564 entries across 11 real targets (swift-syntax
        2 732, vapor 205, SQLite.swift 197, pollen 122, Alamofire 111); unchained A/B 0 gains/0 losses/0
        entry deltas with the new `typeSurface` key as the ONLY envelope change. Consumer: 5 chained
        consumers / 2 805 entries, 0 gains 0 losses, arm ENTERED 20 times, every one a `returns` miss —
        the same shape rust measured (408 crates, 2 hits, 406 misses).
      - **RESIDUAL — CLOSED, candor-swift `9a51e7f` + `74bed40` (2026-07-27). The guard is PROVEN.**
        As filed: a nested type's method was unreachable for the consumer, because the key is three
        segments and this engine's dep index carried only `pkg#leaf` and `pkg#tail2`. Swift now carries
        rust's prerequisite too — a third key shape `pkg#<full qual>`, NORMALIZED rather than raw (the
        one place swift is not rust: `tail2` already normalizes `.`/`::`, so pushing the raw qual would
        add a key no Swift call site can spell). Index 14 535 → 15 398 keys over seven real repos split
        one package per target; keys present before and absent after: 0; new ≥3-segment collisions 0,
        unlike rust's pgman 1 865 — swift's scanner emits no cfg-gated duplicates, so the fall-back-to-
        disclosure is unexercised here but stays required. The dedup is the whole safety argument and
        was mutated out: `viaFactory` loses its Fs and a bare free call goes ABSENT from the report (a
        ⟨0.21⟩ purity claim) — item 9b in its exact shape.
      - **The exact type-path match is now load-bearing, and the counterfactual was MEASURED rather than
        argued.** The fixture was written WITH the key, as instructed: `openForeign() -> Progress` names
        a type the package does not declare, a suffix match answers the nested `Mock.Progress` that
        merely shares its leaf, and the third key makes that guess LAND — the caller is charged an Env
        it cannot reach AND loses half 1's disclosure with it. The mutation fails that test and no other.
        **Then the interesting half:** with the key mutated back OUT and the suffix mutant left IN, the
        CONSUMER rows go green again and only a producer-side "publishes nothing" assertion fails. So
        what the key changed is not that a wrong answer can be OBSERVED — a producer assertion could
        always have seen that, and nobody had written one — it is that a wrong answer now LANDS. *An
        untestable guard is a hope; but "untestable" can mean "nobody wrote the cheap assertion" as well
        as "the mechanism cannot bite", and only the second is a real blocker. Say which one you have.*
        `-> any P` / `-> some P` returns are still refused; `any P` is erased and would be safe to admit
        later, `some P` is not.
      - **FOUND WHILE FIXTURING, reported not fixed:** `let c = openMock(); c.probe()` on a NESTED type
        does not resolve IN-SCAN either, so the new row has no single-tree control and the chained arm is
        now strictly BETTER than the unsplit one — candor-java `9ae68f7`'s smell, one repo over. The
        local returns/binder path does not carry a nested type path. Documented on the test rather than
        asserted, since pinning it would encode the gap as a requirement (item 7g).
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

## Found while VERIFYING `02fb0ad` and landing swift's typeSurface rung (2026-07-26)

Verification of `02fb0ad` was run in the OTHER direction, per item 0, rather than by re-running its A/B.
**It found two silent under-reports, both introduced or inherited by the erasure gate, and both invisible
to any corpus A/B** — each needs a name collision no measured target contains. The commit's own headline
result stands: its A/B, its five monomorphized rows and its three erased controls all reproduce.

- [x] **The ELEMENT-opacity flag outlived its block — candor-swift `71de627`.** `02fb0ad` made
      `enterShadowScope` save UNCONDITIONALLY, reasoning correctly that a `for x in xs` binder can now ADD
      to `monoNames`. It introduced a SECOND set, `opaqueElem`, and never added it to the save. Its stated
      invariant — lockstep with `arrayElem`, so a rebind cannot leave a stale opacity behind a fresh
      element type — is the CLEAR half of the discipline and is silent about the RESTORE half.

          func f(_ xs: [some Speaker], _ ys: [any Speaker], _ c: Bool) {
              if c { let ys = xs.filter { _ in true }; _ = ys }   // ys marked monomorphized
              for y in ys { y.speak() }                            // ys is the ERASED PARAMETER again
          }

      The block closes and the CHA stays suppressed for the rest of the body: `f` is ABSENT from the
      report, a positive purity claim about a function that performs Env. Control: rename the inner binder
      `zs` and it is `['Env']`. Fixed as a scope, not a clear — the other direction is asserted too, since
      dropping the flag re-opens the fabrication `02fb0ad` closed.
- [x] **A nested `func`'s PARAMETERS were not a scope — candor-swift `83cd607`.** Inherited from
      `d62dd69` rather than introduced by `02fb0ad`, but the same mechanism.
      `func outer(_ s: some Speaker) { func inner(_ s: any Speaker) { s.speak() } }` read silent-pure:
      `inner`'s receiver is an existential, the local conformers really are its witnesses, and the CHA was
      suppressed because the ENCLOSING parameter — three lines up, a different variable — is spelled
      `some`. Spell the outer one `any` and the identical body is `['Env']`. **This is the swift form of
      the leak candor-rust's R4 needed its THIRD carve-out for**, running the other way: value-bag's
      nested `impl Serializer` INHERITED the outer `&dyn`-ness and gained a fabrication; here the nested
      item inherits the outer opacity and loses a real reach. The nested signature's own opacity is
      re-applied so the mirror does not open.
- [~] **The erasure gate does not reach the LOCAL-protocol dispatch arm — REFUSED WITH NUMBERS, candor-swift
      `020add4`.** Both treatments priced: SUPPRESS costs 5 losses and 7 entries REMOVED (TCA's `_$willModify`
      goes from a disclosed `Unknown` to ABSENT) — disqualified, because the imported arm is safe only by being
      additive and here it deletes a disclosure. DISCLOSE costs 9 concrete effects → hedge. **The argument that
      settles it:** for an IMPORTED protocol the in-scan conformers are an arbitrary subset of the candidates;
      for a LOCAL one they BOUND them (TCA's `ScopedCore<Base: Core>` — all 8 in-scan conformers are legal
      instantiations and they compose), so the union IS the candidate set. That argument now lives in the code,
      replacing the citation of a note nobody wrote. ORIGINAL:
      `d62dd69`/`02fb0ad` gate the arm at `Driver.swift`'s imported-supertype CHA, which requires
      `!localTypes.contains(owner)`. A LOCALLY-declared protocol dispatches through a different path
      (`protoTyped`/`localProtocols` → `subtypesOf`), which never consults `opaqueRecv`. Measured on a
      one-package fixture: `localMonoParam(_ s: some Speaker)`, `<T: Speaker>(_ s: T)`, `[some Speaker]`
      elements and a `Relay<T: Speaker>` field ALL read `['Env']` from the effectful conformer, with the
      only call sites passing the pure one — i.e. the fabrication those two commits closed is still open
      through the far more common door (your own protocol, your own conformers).

      A `DeclCollector.swift` comment already says so ("the LOCAL-protocol arm above is untouched … see
      the note in SOUNDNESS-VEIN-crossing-the-scan-boundary.md") — **and that note does not exist**, which
      is item 9 exactly. It is recorded here now. Closing it is NOT a wider `if`: the local-protocol arm
      is what R28/R39 and the whole element-dispatch family run on, so suppressing it needs its own A/B
      and its own second-direction fixture.
- [x] **FIXED, candor-swift `7a4f977` — 289 bindings to 123, candor-swift's own 23 to 2.** Half 1's provenance conjunct fired on LOCAL methods and computed properties — measured while
      instrumenting the typeSurface consumer, which is the only reason it was visible. `localFreeFns`
      removes the local leak for FREE functions only; a bare call to a METHOD or a computed property of
      the enclosing type still looks like a dependency factory. All 20 half-1 triggers across five chained
      real consumers are of this kind — `closureParamNames`, `fnsFor`, `sortedPlaces`, `dayHourlyValues`,
      `withAnimation` — and not one is a dependency factory. Each gets a false
      `Unknown[dispatch:untyped cross-package receiver]`. False uncertainty, not a cardinal sin, so it is
      filed rather than patched; the fix is to widen the local-name exclusion beyond free functions.
- [x] **swift carried THREE copies of the chained-dep apply path and one had drifted — `84a71ea`.** Asked
      BEFORE adding the typeSurface consumer, exactly as this queue's rust (`7cb5748`) and java
      (`6ab26e4`) rows instruct. The chained-GLOBAL read applied effects/`hosts`/`cmds`/`paths` and
      dropped `tables`, `invisible` and `incomplete`: a consumer reading a dependency's effectful lazy
      global inherited the EFFECT and none of the dependency's honesty markers, turning "Fs plus a blind
      spot inside the dependency" into a fully-analysed `Fs`. Fixture-proven both ways; no corpus output
      changes, because no measured target has a chained dependency global carrying a disclosure. **Three
      engines asked, three engines guilty — the audit is worth running in candor-ts too.**

## Found in passing while landing the typeSurface rung (2026-07-26) — not boundary defects

- [x] **`candor-scan` PANICS deterministically on `getrandom@0.3.4` / `0.4.2` — CLOSED, candor-rust
      `4f7b704`, and the cause was a SPAN CROSSING A THREAD.** proc-macro2's fallback `Span` is a pair
      of byte offsets into a THREAD-LOCAL source map; candor parses on rayon workers and walks on the
      collector thread (`SendFile`). The contract was written as if candor were the only span reader —
      **syn's parser reads spans too**, and `visit_macro` hands it the moved token stream, where
      `parse_negative_lit` JOINs the `-` punct's span with the literal's. A `-1` in any macro body is the
      whole trigger. Fixed by `respan_call_site` at all four sites that re-parse moved tokens; the
      `a593197` containment stays. **`0.4.3` was crashing too** — nobody had looked.
      - The claim that it could not be reduced was about the setup, not the bug: parse on one thread,
        walk on a second FRESH one, and the panic is deterministic. Three fixtures, four mutants, four
        named failing tests.
      - The prior diagnosis was INVERTED, which is why removing `macro_template_blocks` changed nothing:
        `Span::call_site()` is `(0,0)`, the dummy file every thread's map is seeded with — always valid,
        and now the fix. (`macro_template_blocks` was already safe for a second reason: it re-parses from
        a STRING, which registers a file on the current thread.)
      - **The quiet half is the point.** Past the end of the walking thread's map the lookup panics;
        inside it, it silently resolves against an unrelated file. Instrumented over 121 crates: 88 927
        macro re-parses, **72.4% handed a stream this thread cannot resolve.** The A/B moved 3 crates of
        976 — the counts are the evidence, not the diff (item 8).
      - 976 crates, both arms hashed: panics 3 → 0, 21 gains, 0 losses, `unanalyzed` −3, 973 identical.
      ORIGINAL ENTRY:
- [~] **`candor-scan` PANICS deterministically on `getrandom@0.3.4` / `0.4.2`.** `proc-macro2`'s
      `Span::join`: *"Invalid span with no related FileInfo"*. Two things to fix, and the queue was right
      that the second matters more.
      - **BLAST RADIUS — FIXED, candor-rust `a593197`.** Contained per FILE and DISCLOSED through the
        ⟨0.21⟩ `unanalyzed` array, which also sets `had_parse_failure`, so a configured gate refuses to go
        green over the hole (`deny Fs` → exit 2, "policy NOT enforced"). getrandom now yields a real report
        naming `src/backends/use_file.rs` as unanalyzed, instead of no report at all. The fault is INJECTED
        for the test (`CANDOR_PANIC_ON_FILE`) because the real trigger needs a whole crate's parse state —
        the file scanned ALONE does not panic — and a containment nobody can fire is a containment nobody
        has checked. Both directions asserted: the surviving file keeps its effects, and the lost file is
        NAMED (absence from `functions` is a purity claim, so a dropped file with no disclosure is the
        cardinal sin wearing a crash).
      - **THE PARSE DEFECT ITSELF — CLOSED, candor-rust `4f7b704`, and my diagnosis was not merely wrong,
        it was INVERTED.** I wrote here that "synthesized `Group::new` spans are call-site spans with no
        FileInfo". `Span::call_site()` is `(0,0)` — the DUMMY FILE every thread's source map is seeded
        with, i.e. the one span that is always resolvable, and it is now the FIX (`respan_call_site`, at
        all four sites that re-parse moved tokens). The `macro_rules!` template path was already safe for a
        second reason — it re-parses from a STRING, which registers a file on the current thread — which is
        exactly why removing it changed nothing and should have told me the theory was wrong.

        The real cause is a SPAN CROSSING A THREAD. proc-macro2's fallback span is a pair of byte offsets
        into a THREAD-LOCAL source map; candor parses files on rayon workers and walks them on the collector
        thread. The code half-knew this — `fn_locs` runs inside the parse closure precisely because line/col
        only resolves there — but the `SendFile` contract was written as though candor were the only span
        reader. **syn's own parser reads spans too:** `parse_negative_lit` JOINS the `-` punct's span with
        the literal's, so a `-1` anywhere in a macro body is the whole trigger. getrandom spells it
        `debug_assert!({ match ret { 0 => true, -1 => …, _ => false } })`.

        It DOES reduce to a fixture, contrary to what I concluded: parse on one thread, walk on a second
        FRESH thread whose map holds only the dummy file. My "it needs whole-crate parse state" was a
        description of the rayon pool, not of the defect. Measured over 976 registry crates: panics 3 → 0
        (0.4.3 was crashing too), 21 gains, 0 losses. And the count that matters more than the crash —
        instrumented over 121 crates, **72.4% of 88,927 macro re-parses were handed a stream the walking
        thread cannot resolve**. The panic is the loud tail; the quiet form silently resolves a span against
        an unrelated file.
- [x] **`build.rs` fails clippy `collapsible_if` — CLOSED, candor-rust `0d63ead`, and the qualifier is
      gone.** The cause of the qualifier was never a preference: stable clippy cannot compile the
      `rustc_private` dylint lib at all, so the `-p` list was the only thing that could work, and
      `build.rs` (root package) fell outside it too. Nothing linted either, so 45 warnings had
      accumulated. Fixed by adding a SECOND leg rather than widening the list — `clippy` joins the pinned
      nightly's components in `rust-toolchain`, so the bare `cargo clippy --all-targets` resolves and CI
      runs it beside the stable one. Verified-to-catch: restoring the nested `if` reddens the new leg.
      - Worth carrying: the two clippy versions **do** catch different things — the stable leg then
        flagged a `doc_lazy_continuation` the nightly leg had passed. Keeping both is not belt-and-braces.
      - And a `clippy --fix` hazard: rewriting a `match` into `.map(…)` DELETED the comment on the `None`
        arm, which recorded why an unpinnable local `fmt` is treated as PURE rather than `Unknown`. That
        is a soundness argument, not decoration. Check every `--fix` diff for eaten comments.

## Residuals surfaced by the 2026-07-26 agent round (recorded so they do not live only in a transcript)

- [x] **ts's `interfaceUnion` CHA fan-out bound — DONE, candor-ts `fc8d297`.** Measured first: the fat tail
      is NOT the argument (44 arms over 353 targets; one with 70). The decisive finding was that rxjs's OWN
      `Observable.subscribe` reads `Unknown[dispatch:…Operator.call]` — the in-scan site declining the 70-way
      fan-out — while the report it wrote handed a chained consumer the smear. **candor published what candor
      refuses to resolve.** Past the bound: `['Unknown']` + `unresolved` + reason, never silence. ORIGINAL: candor-java added one (`429c7b2`) after a
      217-subtype smear: past a threshold a union stops being information, and java's answer was to drop to
      a DISCLOSED Unknown rather than emit the smear. The same hazard is live in ts. Measure the
      distribution before implementing — and note the bound must not silently drop the union and leave
      nothing, which would be the cardinal sin wearing a precision fix. *(in flight)*
- [x] **ts's union reads method SIGNATURES only — DONE, candor-ts `d9b8c34`.** A `run: (x) => void` member is
      a FunctionTypeNode with no name and no owner, so three sites keying on a declaration's name formed no
      key at all. Chained end to end: `@ukri-tfs/email#EmailService.send` `['Unknown']` →
      `['Net'] invisible:['@aws-sdk/client-ses']`. Also repaired 139 disclosure strings that named the
      PROPERTY as the owner type. ORIGINAL: so an interface member declared as a property with a
      function type (`@cucumber/cucumber`'s `IDefinition.getInvocationParameters`) is never unioned.
      Pre-existing, and shared with the in-scan arm. *(in flight)*
- [x] **rust dictionary values / `fieldArrayElem` — ANSWERED, candor-rust `a80bb15`, and the premise was
      wrong.** Probed with a `dyn` control per row: the container and field positions ALREADY thread the bound
      map and all resolve. The real gap was the local `let` ANNOTATION, and a parameter-position defect was
      hiding underneath it (a tuple destructure wrote both type maps and `vars` won). ORIGINAL: so they are
      inert — **correct by accident** (item 0b). If anyone adds bound resolution there for the reason R28/R39
      needed it, the erasure gate is needed at the same time. Swift recorded the same shape in its own code
      comments. *(in flight)*
- [x] **`@aws-sdk/client-sns` CJS-vs-ESM — REFUTED AS FILED, item closed.** The original finding was an
      artifact of its own method: `dist/cjs` and `dist/es` were scanned as SEPARATE roots with no
      `node_modules`, comparing DIFFERENT functions. Redone as one scan of the package root with
      resolution: 309 same-named units in both builds, `invisible` present in ESM only on 76 and in CJS
      only on **0** — and the cause is not candor. The ESM build IMPORTS `__awaiter`/`__generator` from
      `tslib` (56 files) and the CJS build INLINES them (5), so `invisible:['tslib']` is TRUE of the ESM
      body and its absence is TRUE of the CJS body. The 87-vs-1 `unknownWhy` gap has the same cause: the
      downlevel state machine adds `_a.sent`/`.apply` shapes the inlined form does not have. **Two
      different bodies, two correct answers.** ORIGINAL FILING:
  ~~**`@aws-sdk/client-sns` reads WEAKER in its CJS build than its ESM one**~~ — the ESM units name the
      packages they reach through `invisible`, the CJS units report the same reach as `Unknown`. The
      disclosure survives, so this is precision, not honesty; but a consumer's answer should not depend on
      which build of the same package it happens to load.

## Found while answering the swift generic-bound note (2026-07-26)

- [x] **rust HAS swift's "correct by accident" shape, and it is not where the note guessed — candor-rust
      `a80bb15`.** The note asked whether rust has a container/field position where a generic bound WOULD
      resolve but the code never asks. Answered with a probe crate carrying every dispatch position and a
      `dyn` CONTROL beside each row, because a silent row that is silent for a DIFFERENT reason looks
      identical.

      The container and field positions are **not** it: `Vec<T>`, `&[T]`, `HashMap<K,T>` and every field
      form already thread the bound map (R37b/R39/R40) and all resolve. The gap is the LOCAL `let`
      ANNOTATION — the one position Pass A cannot reach, and the collector had no bound map, so
      `trait_leaves` took a literal `HashMap::new()`. `let d: T = pick(); d.go()` under `fn f<T: Doer>`
      read silent-pure while the identical PARAMETER resolved, and while `let d: Box<dyn Doer> = x` —
      the same line, one spelling along — resolved too. The site was also missing `elem_trait_leaves`,
      `tuple_trait_leaves` and the `is_callable_type` map outright.

      **A PARAMETER-position defect was hiding underneath it** (bar item 0b): the tuple destructure wrote
      BOTH maps for a position — `tuple_types` yields the spelling (`"T"`), `tuple_trait_leaves` yields
      the bound — and `vars` wins at the call site, so the binding resolved to a type named `T`, which is
      nothing. The `dyn` spelling escaped only because `tuple_types` yields `None` for it.

      976 crates: 4 gains, 0 losses, entry +2, Unknown +3/−0. **Every gain is a disclosure, and every one
      is the existing 12-impl CHA bound reaching a receiver it could not see** — pinned by a fixture where
      the PARAMETER form of a 13-impl trait reads `Unknown` in BOTH arms, so the rung moved the position
      and not the rule. Six guards, six mutants, six named failing tests.

      Residuals pinned as a test rather than a comment, WITH the finding that makes them residuals: tuple
      INDEX access (`t.0.go()`), an unannotated rebind (`let v = xs`), and a factory return bound into a
      local are all still silent — and so is each one's `dyn` control, so they are POSITION-level gaps
      rather than this rung's "never asks for the bound". The test fails if one starts resolving.

## Closed by the swift round (2026-07-26 night) — three confirmed defects, and the design question behind them

An adversarial code review found three more. Two were the SAME failure the gate had already produced
four times, which is why the third patch was refused and the mechanism was fixed instead. All three
landed with two-direction fixtures, every guard mutated out and the failing test named, an A/B over 14
real Swift targets / 12 004 entries (0 gains, 0 losses, Unknown unchanged) and four-way conformance.

- [x] **A ternary's opacity was composed with `||` — candor-swift `663752a`, CARDINAL SIN.** `rootOf`
      types `cond ? a : b` from the arms' shared root; `mono` is what licenses SUPPRESSING the
      local-conformer CHA, so one monomorphized arm certified an ERASED sibling.
      `f(_ m: some Speaker, _ e: any Speaker, _ c: Bool) { (c ? m : e).speak() }` was ABSENT from
      `functions` — a ⟨0.21⟩ purity claim about a body that performs Env whenever `c` is false. Opacity
      licenses suppression, so it composes by CONJUNCTION. Three rows, because each alone is satisfiable
      by a wrong fix (mixed must dispatch; erased/erased must dispatch; mono/mono must stay suppressed).
      **Instrumented, the join fires 12 times across the whole corpus and every firing is
      ERASED/ERASED** — so `&&` and `||` are indistinguishable there and the corpus is the fabrication
      CONTROL, the fixtures are the evidence. The probe was NOT shipped: an env read inside `rootOf`
      charged Env+Fs to 26 of candor's own functions in its self-scan.
- [x] **`patternNames` listed three of the seven pattern kinds — candor-swift `42093b6`, CARDINAL SIN
      plus its mirror, and this is where the SET-OF-NAME-FLAGS DESIGN QUESTION got answered.**
      `for case let x?`, `for case .some(let x)`, `for case let x as T` and `for var x` never reached
      `shadowName`, so the enclosing signature's `monoNames`/`depBoundLocals` stayed on the loop's own
      unrelated binding: silent-pure in one direction, and a false
      `Unknown[dispatch:untyped cross-package receiver]` for a purely LOCAL value in the other (which
      flips `deny E Unknown[dispatch]` to exit 1 on clean code). Both reproduced before anything changed.

      **Is the name-flag side table itself the defect? Partly, and the useful answer is more specific
      than the question.** Of the six defects this gate has produced, exactly one (`71de627`) was a
      SAVE-LIST omission; two (`83cd607`, this one) are missing ENUMERATIONS — of scope forms and of
      binder forms; the rest are not scoping at all. Attaching opacity to the BINDING resolved at the
      point of use does not remove the enumerations, and it requires `vars` to become lexically scoped —
      which it deliberately is not (function-wide with clear-on-rebind, because a stale type is
      dangerous inward and merely lossy outward). Fusing the flags into `vars` WITHOUT that would make
      the flags leak outward the way types do, i.e. `71de627` permanently. So the full structural fix is
      a rewrite of the collector's binding model with its own A/B, not a safety refactor — **filed, with
      that cost, rather than attempted here.**

      What WAS done instead is the part that is structural at acceptable risk: the binder enumeration is
      replaced by a property of the PARSE TREE — a walk for every `IdentifierPatternSyntax` in the
      pattern subtree — verified exact in BOTH directions against SwiftParser rather than assumed (every
      bound name reaches one, including `let x?` through
      `valueBinding > expressionPattern > optionalChainingExpr > patternExpr`; and no non-binding
      pattern produces one — `for case konst in`, `case E.one(3)`, `case 1...2` parse to
      `declReferenceExpr`/literals, `_` is a `wildcardPattern`). Plus a catch-all
      `visit(IdentifierPatternSyntax)` that CLEARS any binder no specific visitor claimed, which
      **inverts the failure mode**: an unenumerated form now defaults to dropping a stale binding
      instead of keeping one. The MARKING carries the risk, not the clearing — removing the
      `OptionalBindingCondition` mark fails two OTHER suites, because the catch-all would wipe a genuine
      `if let` binding.

      **Scoping alone would have been a fix that changed nothing**, and only measuring showed it: these
      binders were never TYPED either, so a cleared flag left the same silent-pure answer by another
      route (both `…NoShadow` controls fail before the change). The two forms whose type needs no
      inference are now typed — `let x as T` and `let x?`; `.some(let x)` is REFUSED through that door,
      because a local enum with a case named `some` parses identically and the element type would be
      the enum rather than the payload.
      **And typing it made `vars`' documented outward leak bite** (standing bar item 0, mid-flight):
      `let c = depBuild(); for case let c? in xs {…}; c.speak()` typed the loop's `c` from the sequence,
      that type survived the loop, and the factory-bound receiver below stopped reaching half 1's
      marker — a disclosed gap turned into a silent purity claim by a fix aimed at the opposite defect.
      A loop binder's type is now restored at the loop's end, which closes the same leak for the plain
      `for x in xs` binder that always had it. **Measured live: 258 restores across 13 targets actually
      change a binding, with zero output delta.**
      Two more binder forms found by INSTRUMENTING rather than by reading the grammar: `for var x in xs`
      (a `valueBindingPattern` wrapping the identifier — the loop variable was never typed at all, 5
      corpus sites with an element type in hand), and `catch let e as MyError`, which matched a
      `DeclReferenceExpr` where the parser puts a `patternExpr > identifierPattern` and so never fired.
- [x] **`typeSurface.returns` gated the ENTRY lookup and never the ANSWER — candor-swift `6aa4635`,
      FABRICATION.** `depCallee` is a bare name (an idiomatic Swift call into a dependency carries no
      module), so every covered import of the file is asked the same fn key. Alpha publishing
      `build -> Alpha#Client` (whose `fetch` is Fs with `/etc/secrets` in `paths`) and Beta publishing
      `build -> Beta#Stub` (whose `fetch` is pure, so absent) made `surfaced` hold two types while `hits`
      held one — and the caller was charged Alpha's effect AND its path literal, with `unresolved` left
      false so nothing disclosed it. **rust's reverted defect 1 — a leaf-keyed collapse of two distinct
      types — reappearing ACROSS packages instead of within one.** §2 rule 1 is enforced within a report
      by `returnsAmbiguous` and nothing enforced it across the file's imports, where no single report can
      see the collision. Refusing falls back to half 1's disclosure.
      The SECOND fixture is what rules out the guard everyone reaches for: with BOTH packages imported
      and covered and only ONE answering `openAlpha`, the row must still resolve — a guard keyed on "the
      file imports more than one covered package" passes the colliding row and silently kills every real
      recovery in a multi-dependency file.
      Measured: unchained A/B byte-equal (the arm needs `CANDOR_DEPS` to be entered at all), so **three
      REAL chained consumers were built by resolving their SwiftPM dependencies and scanning each
      checkout** (candor-swift ← swift-syntax; console-kit ← 6; TCA ← 17): 964 consumer entries, 0 gains,
      0 losses, arm entered 4 times, every one a `returns` miss and 0 AMBIGUOUS. The trigger is real and
      no measured target exercises it.

## Opened by the swift round (2026-07-26 evening) — three real, one of them a live fabrication

*(the first is now CLOSED — see the section above.)*

- [x] **The erasure gate never reaches the LOCAL-PROTOCOL dispatch arm — MEASURED, and the answer is
      REFUSE TO GATE IT. The phantom citation is replaced by the argument (candor-swift `DeclCollector`).**
      The gate requires `!localTypes.contains(owner)`, so `some P`, `<T: P>`, `[some P]` and generic-field
      receivers over a *locally declared* protocol all charge every local conformer. Reproduced on a
      one-package fixture: five monomorphized forms all read `['Env']` from the effectful conformer while
      the only call sites pass the pure one, and the caller inherits it.

      **But the two cases are not the same question, and that is why the gate must not simply widen.**
      For an IMPORTED protocol the conformers in scope are an ARBITRARY SUBSET of the candidate set — the
      caller is in another module and may supply a type this scan has never seen, so unioning our few
      conformers is neither the true set nor a bound on it. For a LOCAL protocol they BOUND the
      instantiations, and where they do not (open hierarchy, unresolvable witness) `protoDispatches`
      already falls to a disclosed `Unknown` rather than to a partial union. The union is the sound
      over-approximation of a generic function, not a fabrication.

      Both candidate treatments measured, 14 real Swift targets / 12 004 entries; the trigger is 17
      monomorphized local-protocol dispatch sites (swift-syntax 4, Alamofire 4, TCA 7, SQLite.swift 1,
      console-kit 1) — small, real, and every one traced.
      - **Suppress the arm** (what the imported side does): **5 effect losses and 7 entries REMOVED**,
        and among them TCA's `_$willModify` goes from a disclosed `Unknown[dispatch:…]` to ABSENT. A
        purity claim manufactured by a fabrication fix — standing-bar item 0, disqualified outright. The
        reason the same treatment is safe on the imported side is that the arm there is ADDITIVE (it
        emits edges and never an Unknown), so suppressing returns to the pre-rung baseline; here it
        deletes a disclosure.
      - **Disclose `Unknown` instead:** nothing goes silent (Unknown 10 539 → 10 540, entry count
        unchanged) but **9 concrete effects degrade to a hedge**. The row that decides it is TCA's
        `final class ScopedCore<Base: Core>: Core { func send() { base.send() } }` — `Base` is bounded by
        `Core`, all 8 in-scan conformers are legal instantiations and they compose, so the union IS the
        candidate set and replacing it with `Unknown` trades a correct answer for a hedge.

      Residual, stated rather than hidden: candor does not specialize at call sites, so a generic function
      whose only instantiation in THIS program is pure still carries the union. That is general to
      caller-agnostic per-function analysis, not specific to protocols, and it is a true statement about
      what a public generic function can be asked to do.

      **The comment cited a justification in the vein doc that was never written** — standing-bar item 9
      with no code beneath it at all, which is worse than a wrong comment: the reader has no way to tell
      an argument from a citation of one. It now carries the argument and the numbers inline.
- [x] **FIXED `7a4f977` (same defect as the row above — the two filings were one item).** All 20 of swift's half-1 disclosure triggers on a real corpus were FALSE. Instrumenting the
      `typeSurface` consumer showed every one firing on `closureParamNames`, `sortedPlaces`,
      `withAnimation` — local methods and computed properties — because `localFreeFns` covers free
      functions only. This is over-disclosure, not the cardinal sin, so it is noise rather than a lie; but
      a hedge that is wrong 20 times out of 20 teaches a consumer to ignore the channel, and rust measured
      the same conjunct firing on `max()`/`min()` before narrowing it.
- [x] **FIXED — candor-swift `9a51e7f` (the key) + `74bed40` (the guard it makes provable), 2026-07-27.**
      Swift's index now carries `pkg#<full qual>` beside `pkg#leaf` and `pkg#tail2`, NORMALIZED rather
      than raw — the one place it is not a copy of rust's `5feba18`, since `tail2` already folds `.`/`::`
      and the raw qual would key a string no Swift call site spells. Additive with the dedup, both
      directions mutation-verified; 14 535 → 15 398 keys over seven real repos split one package per
      target, 0 keys lost, and 43 chained consumer reports byte-identical.

      **And the exactness guard IS provable now** — a suffix match publishes a nested type that merely
      shares its leaf, the third key makes that guess LAND, and the caller is charged an effect it cannot
      reach. But the useful result is the counterfactual, which was measured: with the key removed and the
      suffix mutant left in, the CONSUMER rows go green and only a producer-side assertion fails. **"The
      guard is untestable" was half true.** Nobody had written the cheap producer assertion, which needed
      no key at all; what genuinely needed the key was showing the guard is LOAD-BEARING rather than
      cosmetic. Two different claims, and this row conflated them. *When you file a guard as unprovable,
      say whether the mechanism cannot bite or whether the assertion was merely never written.*
      Full detail on the `typeSurface` row above.

## The 2026-07-26 adversarial review: 9 confirmed defects, ALL of them narrowings that went one step too far

A workflow review (4 finder angles, an independent verifier per location, 42 agents) over the whole day's
four-repo output. **Ten findings survived verification; nine distinct.** Every single one is the shape
standing-bar item 0 names — a change that narrowed a sound over-approximation to kill a fabrication, and
narrowed past a real reach. Two were mine, and both are in the fail-closed direction I had just claimed to
protect. *(All in flight 2026-07-26 evening.)*

**Cardinal sins (silent under-reports):**
- [x] **FIXED `39bbc8b`** — rust `scan.rs:663` — the contained parser abort (`a593197`, MINE) writes `fninfos: []` into the
      `--incremental` cache under the file's REAL content hash, so a warm run reuses it, skips the
      `catch_unwind`, emits no `unanalyzed` and no `had_parse_failure`, and a gate goes GREEN over a file
      whose effects were never derived. **I converted a fail-closed crash into a cached, reproducible false
      all-clear.** The asymmetry that proves it: a round-1 parse failure `continue`s BEFORE the cache write
      and re-discloses every run.
- [x] **FIXED, candor-java `9f8e71c` — and the review named two sites; there were FOUR, one of them every
      polymorphic dispatch candor resolves.** java `Candor.java:3673` (`9ae68f7`, MINE) + `:2810`
      (`dd81bfa`) — single-queue BFS over `directSupers` interleaves the superclass chain with interfaces by
      DEPTH, so a nearer `interface` default settles a descriptor and suppresses the superclass body the JVM
      actually runs (JLS 15.12.2.5 / 8.4.8: **the class wins**, at any depth). I added per-overload shadowing
      to stop dropping inherited bodies and dropped a different one. Both halves failed at once: the real
      `Fs` dropped AND the interface's empty effects charged in its place.

      **The instruction to reuse `Cha.nearestConcreteSuper` rather than write a third walk was right about
      the shape and wrong about the helper.** That helper — which `chaTargets` and `monomorphicTarget` both
      end in — walked `transSupers`, a **HashSet**, and returned the first `declaresConcrete` hit in HASH
      order. It was not ordered wrongly; it was not ordered. `nearestDepFn` was the fourth. All four now
      share ONE traversal (`Cha.resolutionOrder`), so this vein's fourth drifted copy of a walk was not
      written. *A cross-site precedent tells you where a walk belongs, not that the walk is correct.*

      **Most of the damage was CLASS-vs-CLASS, not class-vs-interface** — the narrow reading would have
      fixed the ordering and left the unordered helper in place. Over 45 real jars the answer changed
      **11 277** times: **11 193** where the new owner is a proper SUBTYPE of the old (a near override was
      losing to a far base), and **84** the reported interface-default shape. Traced to bytecode both ways:
      spring-core `ResourceDecoder.decode` `[]` → `['Log','Unknown']` (it resolved to `AbstractDecoder`'s
      `throw new UnsupportedOperationException()` instead of the `AbstractDataBufferDecoder` body that
      runs); guava `AbstractStreamingHasher.putLong` `['Clock','Log','Unknown']` → pure (charged through an
      `AbstractHasher` chain a `final` override replaces — the fabrication mirror).

      Nine chained pairs: consumer side 0 gains / 0 losses / identical Unknown counts — and per item 8 that
      is a claim about the experiment until instrumented: `nearestConcreteSuper` differs 5–531 times per
      pair while the dep-facing walks are entered 8–30k times and differ **zero**. The boundary defect is
      real (fixtures) and rare on real library pairs. Full record: SOUNDNESS-LOG 2026-07-26.

      **RESIDUAL, and it is the next rung here:** `ReportWriter.writeHierarchy` records a dep type's
      supertypes as a sorted `TreeSet` with no superclass marker, so a chain lying ENTIRELY inside a
      dependency stays depth-ordered. The consumer's own classes state their superclass and interfaces
      separately, which is why the shape the defect was found in resolves exactly. Closing the rest = a
      sidecar key whose value is an OBJECT (`Loader#loadDepHierarchy` already skips non-array values, so an
      older consumer ignores it, and a sidecar without it keeps today's answer). A format rung with its own
      compatibility surface — it wants its own measurement, so it did not ride.
- [x] **FIXED, candor-java `c583da7`** — java `ReportWriter.java:499` — `mergeUnionInto`'s `unchanged` test
      compared each widened `TreeSet`'s SIZE against the original LIST's size; those agree only while no
      list holds a duplicate, so a genuine widening could land on the same count, read as "no change", and
      drop the union — the entry then claiming a narrower effect set than the dispatch reaches, under the
      exact hash a chained consumer keys on. The review could not confirm it and was right not to:
      **established NOT reachable** (every list field of an ordinary entry is materialised from a sorted
      `TreeSet` in `writeJson`, and `real` is always an ordinary entry). Fixed anyway — the size test was
      right for a reason it did not state, leaning on an invariant three hundred lines away that a later
      change would break silently and in the miss direction. Since no corpus can reach it, the UNIT test is
      the evidence: it feeds the duplicate directly, asserts both directions, and restoring the size
      comparison fails it and, across all 512, only it.
- [x] **FIXED `663752a`** — swift `CallCollector.swift:384` — a ternary receiver composes opacity with `a.mono || b.mono`, so a
      `some P` / `any P` ternary claims full monomorphization and skips the CHA for the ERASED arm. Needs `&&`.
- [x] **FIXED `42093b6`** — swift `CallCollector.swift:805` — **the third scope leak**, arriving through the PATTERN not the scope:
      `patternNames` returns `[]` for optional/expression/enum-case patterns, so `for case let x? in` never
      shadows and an enclosing `some P` parameter's flag stays attached to an unrelated erased binder.
- [x] **FIXED `9196c89`** — rust `collector.rs:907` — `mem::take` blanks `generic_bounds` inside a nested `fn` and never installs
      the nested signature's own bounds, so `fn inner<T: Doer>(d: T) { d.go() }` resolves to nothing. The
      commit's fixture asserted only the FABRICATION direction; the second fixture was never written.
- [x] **FIXED `651c9f9` (and the brief was wrong — see below)** — ts `scan.mjs:1631` — the module unit's wire key changed shape with **no engine-version bump**, and
      §2.1 staleness keys on `candor.version`. A SAME-version consumer over a new report finds no key, is not
      told it is stale, and reads the import as pure. The comment above `depInitCell` asserts this cannot
      happen; the code does not implement that (item 9).

**Fabrications:**
- [x] **FIXED `90655d9`** — ts `scan.mjs:3884` — `typingsRoots()` returns null past a 128-file cap and the caller degrades it to
      `[]`, so a large package loses the whole typings arm INCLUDING its role as the ambiguity evidence —
      restoring `d7060ca`'s fabricated-Net / dropped-Fs / `deny Fs`-green defect for exactly the packages big
      enough to hit the cap. **A truncated census must make the affected names REFUSE, never make them
      confident.**
- [x] **FIXED `6aa4635`** — swift `Driver.swift:828` — the `typeSurface` consumer keys a BARE callee across every covered import
      and checks only that the ENTRY lookup is unambiguous, never that the `returns` answer was. Two packages
      exporting `build` → one silently wins, and the caller is charged the other's `Fs` and its path literal.
      **The reverted rust attempt's defect 1, reappearing ACROSS packages instead of within one.**
- [x] **FIXED `67d092d` (NOT by porting java — see below)** — ts `scan.mjs:4062` — the union is DROPPED where java MERGES (`48a5f18`), so a narrow real entry
      replaces the dispatch union including its `['Unknown']` fan-out disclosure.

**REFUTED and worth knowing:** the "fourth unpatched `respan_call_site` site" — the `macro_rules!` template
path re-parses from a STRING, which registers a file on the current thread, so it was already safe. That is
the second time that path has been wrongly accused today.

### What the review says about the METHOD, which is worth more than the nine fixes

1. **Nine for nine.** Not one confirmed finding was a fresh mechanism; every one was a guard added THAT DAY
   that fired on the wrong thing or failed to fire. The fabrication/under-report boundary is not a place
   where defects are *likely* — on this evidence it is where they *are*.
2. **Authorship is no protection.** Two are mine, written while holding item 0 in mind, and both are in the
   direction I had just argued I was protecting. The rust one is worse than the bug it fixed: a crash is
   fail-closed, a cached empty result is not.
3. **The same defect keeps recurring through a NEW DOOR.** The reverted rust leaf-key join came back as a
   module-relative return type, and now again as a cross-package bare callee. Three doors, one defect.
4. **A cap or a refusal must land on the PUBLISHING side, never on the EVIDENCE side.** ts's typings cap and
   the union's drop-on-collision are the same error: refusing to gather evidence lets a confident wrong
   answer through, where refusing to publish would have been safe.

### rust's two review defects — CLOSED, and the fix corrected the finding's own shape

`39bbc8b` persists the abort IN the cache entry (`FileCache::aborted`, schema rev8) and replays it, rather
than refusing to cache. The argument that decided it: **replaying assumes exactly what reusing the FnInfos
already assumes** — same content hash AND same decl index ⇒ same walk ⇒ same outcome — so it is gated on
both, and a decl-index move sends the file back through the walk. Verified by me in both directions: with
content and decl index unchanged the abort REPLAYS (gate stays exit 2); the moment the walk re-runs clean
the abort CLEARS (`unanalyzed: []`, entries 1→2, gate back to a real exit 1). The clearing guard is the
MIRROR SIN and needed its own fixture — *a cached abort that outlives a clean re-walk is a gate that can
never go green.*

`9196c89` — **the review's finding was right about the cause and wrong about the shape, and probing before
patching is what showed it.** A nested `fn inner<T: Doer>(d: T) { d.go() }` is NOT fixed by the bound map:
its `dyn` control (`fn inner(d: &dyn Doer)`) is equally silent, because a nested item's PARAMETERS are
never typed at all — a position-level gap, now pinned as a residual with both controls. What the blanked
map actually bites is the `let` ANNOTATION inside the nested item. Three rows fixed (nested fn, nested impl
block, nested impl method); re-installing `dyn_sig_traits`/`trait_quals` was REFUSED, because the only
position they could bind to is the untyped-parameter one that does not resolve anyway.

**And the agent caught item 9 in its own work:** its "REPLACE, not merge" comment was an assertion nothing
checked — the merge mutant passed the entire suite. Pinning it needed a deliberately NON-COMPILING fixture,
because rustc's E0401 makes the two indistinguishable on anything that compiles, and candor-scan analyses
crates without building them. That is a genuinely new corner of item 9: *a guard can be untestable on valid
input and still matter, because this analyser does not require its input to be valid.*

## PRE-RELEASE BLOCKER opened 2026-07-26 — the build-id lockstep vs §2.1

candor-ts is at build **0.23.2**; the rest of the family is at **0.23.1**. `candor/bin/release-preflight.sh`
check [4] demands all self-declared build versions agree and now FAILS:

    ✘ build versions DISAGREE (a hand-maintained constant lagged the release): 0.23.1 0.23.2

**Both sides are right, which is why this needs a decision rather than a patch.** §2.1's staleness gate keys
on the per-engine BUILD id, so an engine that changes a wire key MUST bump it or every protection that gate
arms stays disarmed — that is why candor-ts `651c9f9` bumped. Check [4] exists to catch the opposite failure,
a hand-maintained constant that LAGGED a release, and its message assumes that is the only way the versions
can differ. Under [[candor-three-axis-versioning]] the build id is explicitly per-engine, so lockstep is a
release convention, not a contract.

Two resolutions, and the choice is Tom's because it is a release-shape decision:
- **release the family together**, bumping all four to 0.23.2 — preserves the convention, costs nothing
  technically, and is what the ladder has done to date;
- **relax check [4]** to compare each build id against the REQUESTED release version rather than demanding
  mutual equality — which is what the check's `WANT_VER` arm already does one line below.

Nothing is published, so this blocks a release and nothing else. **Do not resolve it by reverting the ts
bump:** that would re-disarm §2.1 on the very engine whose wire key moved.

### All nine review defects are closed — and four of the nine briefs were wrong about the fix

Worth recording, because the pattern is now consistent enough to plan around: **the review located every
defect correctly and mis-stated the remedy in four of nine.** In each case probing before patching is what
separated them.

| defect | what the brief said | what measurement said |
|---|---|---|
| java BFS | two sites | **four** — and the unnamed one, `Cha.nearestConcreteSuper`, walked a `HashSet`: not ordered wrongly, **not ordered**. 11,193 of 11,277 changed answers were class-vs-class, not the reported interface shape |
| rust nested bounds | a nested `fn`'s parameter | the parameter is never typed at all (its `dyn` control is equally silent) — the map bites the `let` ANNOTATION |
| ts wire key | bump the version | **no version can close it** — §2.1 rewrites the CONTENT of keys a report carries and can never conjure a key it lacks. The fixable half was elsewhere: an untrusted report still granted COVERAGE, so every key it lacked read pure |
| ts union drop | port java's `mergeUnionInto` | java merges into an interface's own `default` BODY; TS interfaces have no bodies, so the literal port charges a class its own union and fires the producer's `deny Net` on it |

The two that were right as stated (swift's ternary `||`, swift's pattern binders) are the two smallest.
**A verified finding is a verified SYMPTOM.** The verifier's job is to prove the failure is reachable; it is
not to design the repair, and a brief that hands over the reviewer's proposed remedy as if it were settled
will get it built.

### rust's five-shape sweep — 3 of 5 PRESENT, and the worst one was where it was predicted

The sweep hypothesis (a shape found in one engine belongs swept in all four) paid immediately.

- **1. An untrusted report still grants coverage — PRESENT, `069b4c0`.** The predicted one, and the worst.
  §2.1 downgraded a stale report's effects to `Unknown` while the same load registered its package in
  `DepIndex::crates` — the set that EXEMPTS a crate from the κ ledger. So every function the distrusted
  report did not mention became a purity claim with `invisible`, `coverage.uncovered` and the stderr line
  all gone. Split into `crates` (the join gate) and `untrusted` (the claim that silence is informative).
  Measured on real trees restamped to a previous build: ebman 483→584 entries with 389 `invisible` gains
  and **13 crates re-entering the ledger** (`ratatui` at 2977 calls, silently claimed covered); pgman
  195→244. **Verified independently:** a consumer calling a PURE dep fn under a stale report now discloses
  `invisible: ['deplib']` + `coverage.uncovered: [deplib]`, where it previously read as a clean purity claim.
- **2. An unordered walk — ABSENT, now pinned `b16dd38`.** `resolve_target` filters on `v.len() == 1` — it
  REFUSES rather than picks — and the dep index removes colliding keys. **The never-guess rule that
  prevents fabrication is what makes it order-independent**, which is a nice structural result. Gate added
  (123 targets × 5 runs byte-identical, with a probe confirming `RandomState` really reseeds). Note the
  agent's first fixture COULD NOT WITNESS the property — its hits came from a walk-ordered `Vec`; it needed
  a type implementing two traits with differing defaults to reach a genuinely hash-ordered container.
- **3. A disclosure lost to a cache — ABSENT-BY-ACCIDENT, closed `34e425e`.** The abort/ordering paths are
  sound, but `MergedDecls` has 17 fields and the digest hashed 16 (`deref_target` missing). It costs
  nothing ONLY because the deref chase reads it live rather than baking it into an FnInfo — every other
  receiver-typing rung of the last month landed in `CallCollector`. **The reflective guard that promised
  "add a field → the build fails" could not deliver it** (two hand-maintained lists, so binding the field
  `_` restored the build). One macro now generates both.
- **4. A trust marker failing open — PRESENT, `e429a0e`.** ts's exact shape is impossible (`unresolved` is
  derived), but the ⟨0.19⟩ reason class was lost instead: `deny Unknown[indirect]` exited 0 on a function
  whose dep report NAMED `indirect`. Partial, which is why it survived — bare `deny Unknown` and
  `[dynamic]` both fired; only the class-targeted middle, which is how the ratchet is adopted, read green.
- **5. A flag outliving its scope — PRESENT, `05d0ee9`.** `fn f(s: &dyn Store) { for s in 0..3 { s.go(); } }`
  charged `f` with `Fs` on a `u8`. **`scoped_var` DID clear `vars`, and `vars` is read before `trait_vars`
  — so every TYPABLE shadow is masked by precedence and looks perfect**; only a shadow that types to
  nothing exposes it, and the agent's five typed-shadow fixtures all passed. Instrumented: 72,872 binder
  calls, 116 shadowing a live entry, **76 hitting the exact precondition** on named real crates (cap-std,
  clap_builder, h2, ignore) — latent, one effectful impl away from being charged.

**Deliberately not fixed, and correctly:** rust emits `ambiguous:same-name local defs` — outside the closed
§4 vocabulary — **757 times across 253 crates**, and PART 10 misses it because the harness's own fixtures
never produce that kind. Renaming is not free: `callback:` moves the class Dispatch→Indirect and WEAKENS
`deny Unknown[dispatch]`. Wants its own measurement and probably the spec's migration mechanism.

### java's five-shape sweep — 2 PRESENT, 2 absent-by-accident closed, 1 structurally absent

- **1. An untrusted report still grants coverage — PRESENT, `7e41327`.** The same defect rust had, in the
  same place: `loadCrossDeps` registered `depCoveredPkgs` from a report whose effects it had just
  downgraded. The three-arm fixture is the sharp bit — **the STALE arm was byte-for-byte the FRESH arm, and
  `app.S.go` vanished from `functions` entirely**, with the arms differing only in the build id. Measured
  over 7 chained `~/.m2` pairs: httpclient +629 entries, +633 `invisible`, 13 packages back in the
  envelope, 0 effect losses. **Item 0 fired for real:** the one-set fix cost 2 disclosed Unknowns on
  logback-classic with no `invisible` to replace them, because `ch.qos.logback` is a κ-curated prefix — so
  `depCoveredPkgs` (trust-gated) and `depChainedPkgs` (ungated) are now separate sets, both directions
  mutation-verified.
- **2. An unordered walk — NO soundness instance; one WITNESS instance fixed `54350bf`.** Every
  effect-owner selection is a monotone set-union or an existential boolean, hence order-invariant. The one
  that could differ is `Policy.reachesScope`, which picked the AS-EFF-009 `via` witness by DFS over a
  HashSet-seeded stack — and `--gate-json` PUBLISHES that witness. Now nearest-first: verdicts identical on
  5 real jars, and for all 452 jgit violations the new witness is **107 strictly nearer, 0 farther**. The
  agent explicitly declined to call this a soundness defect, which is right.
- **3. A disclosure lost to a memo — no live hazard; one ABSENT-BY-ACCIDENT closed `2b606ee`.** All 14
  memos traced. `depDeclaresSigElsewhere` latched `built` unconditionally — safe only via a property of its
  CALLER, while both its siblings guard directly.
- **4. A trust marker failing open — PRESENT, `2f7479a`, AND IT IS A HOP FURTHER OUT THAN THE BRIEF SAID.**
  `unresolved` does not fail open; the REASON CLASS does, one hop past `6ab26e4`: a dep unit whose Unknown
  was itself INHERITED publishes no `unknownWhy`, so in A→B→C the reason never reaches A.
  `deny Net Unknown[reflect]` went exit 1 single-tree → **exit 0 chained**, while bare `deny Net Unknown`
  fired throughout — only the class-targeted middle read green, and that middle is how the ratchet is
  adopted. No format rung needed; `calls` already held the chain.
  **RELAYED and MEASURED against rust: rust is CLEAN on the second hop** — a three-package fixture
  (C originates `callback:unresolved call`, B chains C, A chains only B) carries the reason all the way to
  A. So java's "rust/ts/swift very likely have the same gap" is FALSE for rust. ts and swift are testing it.
- **5. A flag outliving its scope — ABSENT, structurally.** `MethodScan` never escapes its loop iteration;
  every context mutation is an owner-qualified insert into a whole-scan accumulator. 12 real jar pairs,
  12/12 byte-identical under a reentrancy selftest.

**Two found off-brief, both real:** `--parallel` ignored every target's `.candor/config` while its own
documentation promised byte-identity (`4ddbd3c`), and `test/smoke.sh` had pinned shape 1 as a REQUIREMENT
(`640630b`) — see standing-bar item 7g.

### swift's five-shape sweep — 4 of 5 PRESENT, the richest of the four

- **1. An untrusted report still grants coverage — PRESENT, `308ad15`. THE VEIN IS NOW 4/4.** ts found it,
  and rust, java and swift all had it. Swift's reproduction is the clearest statement of the defect:
  a call into a dep API the report lacks reads `invisible: ['RatesDep']` unchained, and goes **absent from
  `functions`** the moment a STALE report is chained — the κ ledger and the verdict's `coverage` field fall
  silent with it. The fix is a SPLIT, not a drop (chained-but-not-covered); gating the join on coverage
  instead — the obvious one-liner — fails FOUR named tests, three of them the stale-downgrade rows.
  Live: console-kit's 6 dep reports restamped → +29 `invisible`, **18 functions back from absent**, 0 losses.
  Instrumented rather than assumed where it showed nothing: TCA/candor-swift dep reports name SwiftPM
  PACKAGES (`swift-case-paths`) while imports name MODULES (`CasePaths`), so nothing is covered in either
  arm — **a separate pre-existing gap, reported not fixed.**
- **2. An unordered walk — PRESENT in a different guise, `196e125`.** Java's "picks in hash order" form is
  absent (sorted since `23eafc2`). What is present is `23eafc2`'s SIBLING in the code written after it:
  five runs of ONE binary over Alamofire under `CANDOR_WORKSPACE_CHAIN` produced **five report hashes**
  carrying the same 879 union entries in five orders — on the cross-package PUBLISHING path.
- **3. A disclosure lost to a cache — PRESENT, `43a0eaa`.** No incremental cache, but `--workspace`'s
  `.candor/deps` IS a disk cache: a child scan that FAILED was silently skipped and the previous run's
  report stood in. Warm vs cold on identical source: `useDep` absent from `functions` vs
  `invisible: ['DepLib']`. Sweeping alone was insufficient — children share the cache, so the fixpoint
  re-runs once after sweeping.
- **4. A trust marker failing open — ABSENT for `unresolved` (0 failures over 12,004 entries, 10,539 with
  `Unknown`); PRESENT one layer over, `eb0250e`** — and at HOP 1, not hop 2 as java predicted. Building the
  three-package chain to check the relay exposed a SECOND defect underneath: **`reasonClass` tested
  `dynamicMemberLookup` for EQUALITY while the engine emits `kind:detail`, so `Unknown[reflect]` was
  unsatisfiable even single-tree.** A dead parallel `unresolvedSet` (written 7×, read 0×) was
  absent-by-accident and removed (`c5929e3`).
  - **CROSS-ENGINE CONSEQUENCE, verified and fixed by me in java (`d9b07b0`).** The same equality test is
    in candor-java `ReasonClass.java:70` and candor-ts `policy.mjs:20`. Swift emits
    `dynamicMemberLookup:<root>.<prop>` and never the bare token, so neither could ever match a real one.
    REFLECT and UNRESOLVED are both in the `dynamic` set, so a bare `deny Unknown` fires either way — what
    silently dies is `deny Unknown[reflect]`, the form the ratchet is adopted in. **candor-ts is still
    OPEN** (its repo had an agent working in it); the fix is `startsWith`, monotone, with both the
    `kind:detail` and bare rows pinned.
- **5. A flag outliving its scope — the catch-all inversion VERIFIED with a working negative control; two
  uncovered maps still leaking, fixed `c77038f`.** `protoTyped` and `localConstStrings` were covered by
  neither `clearBinding` nor `shadowName`, both FABRICATING, each isolated by a rename control. The obvious
  placement cost Alamofire's `URLRequest.init` its disclosure. The filed binding-model rewrite was
  re-priced: **verdict stands** — the catch-all removed the binder-form enumeration; this is a different one.

**Job 2:** half-1 false triggers fixed (`7a4f977`) — 289 bindings → **123**, candor-swift's own 23 → 2, with
a PRE-EXISTING residual found doing the same thing one conjunct earlier (`returnsIdx` is bare-name keyed
package-wide), pinned as a test asserting today's behaviour with instructions to flip it. The
full-qualification dep-index key (rust's prerequisite 0) was **not attempted** and remains open.

**Two method traps, both the agent's own and both worth carrying:** a test suite **passed three mutants**
because its rows used `-> Int` methods a pre-existing conjunct already excluded, so the new guards were
never reached — *a test that cannot reach the code it names is not a test*. And standing-bar item 7c(b)
claimed its second victim: `git checkout <file>` to undo a one-line mutant reverted uncommitted work, and
three measurements ran against a half-applied change.

### ts's five-shape sweep — 2 PRESENT (both SIBLINGS of its own already-fixed defects), 3 absent

ts is the engine that FOUND shapes 1 and 4, so its job was the harder question: is the fix complete, and
does the shape have other doors here? Both answers were no, and finding that is the case for sweeping an
engine against its own defect rather than ticking it.

- **1. PRESENT — a NEW door, `21277eb`.** A report that declares ITSELF incomplete (non-empty ⟨0.21⟩
  `unanalyzed`) still registered full coverage. A dep with one unparseable file scans to **exit 0** with a
  report that still names its package; the consumer's call to a declaration that file held went from
  `invisible:['deplib']` unchained to **absent from the report** — and the single-tree control is **exit 2**.
  **Chaining an incomplete report was strictly WORSE than not chaining it.** Treatment deliberately differs
  from staleness: entries are kept (they were derived from source it DID read), only the silence hedges.
  Item 0 fired: withholding coverage silently replaced half 1's unanswerable-key `Unknown` with the κ
  hedge, taking `deny Fs Unknown[dispatch]` from exit 1 to 0 — both voices now speak.
- **2. ABSENT, with a real structural argument.** Java's defect was a `HashSet` with no order at all; JS
  Maps/Sets are insertion-ordered, so the live question is whether insertion order is MEANINGFUL — and at
  every decision point it either is (TypeScript's source-ordered `members`/`declarations`), or is sorted
  before `[0]`, or is unioned, or the never-guess counter drops BOTH candidates.
- **3. ABSENT for the memos.** `depEntryCache`/`pkgNameCache` are pure functions of key + a filesystem that
  does not change mid-run; the program/checker is built once, after all cross-dep state is final.
  **ABSENT-BY-ACCIDENT, filed:** `.candor/dep-inits/` and `.candor/deps/` are never cleared, so a package
  whose rescan throws is served from the PREVIOUS run's file while the code comment claims it "is skipped".
- **4. PRESENT — a NEW sibling, `acbd79b`.** `netClass`. `hosts` is a lower bound and `unknown-host` is the
  producer's published judgment that it IS one — and the join copied the literals but not the judgment. A
  dep entry reading `['known-telemetry','unknown-host']` arrived as `['known-telemetry']`, and
  **`deny Net[unknown-host]` went exit 1 → exit 0** against a control that is exit 1 in both arms. The
  invariant is now ASSERTED fail-closed in the writer (`95dc3bc`): `Unknown ⇒ unresolved`,
  `direct Unknown ⇒ non-empty unknownWhy`. It fires nowhere on 42 reports / 22,978 entries, and is
  verified to catch (a mutated producer exits 2 and writes nothing).
- **5. ABSENT, structurally.** Every module-level mutable map keys on node/symbol identity or on a
  MODULE-QUALIFIED name, so two same-named functions in two files cannot collide — confirmed with a
  two-file fixture rather than asserted.

**The relay landed: ts HAD java's second-hop gap (`826571c`).** `deny Unknown[reflect]` exit 1 single-tree
→ exit 0 chained, at one hop AND two. Two process notes from it worth keeping: **the agent's first gate
measurement was wrong and its own negative control caught it** (`deny Net Unknown[reflect]` reads as "Net
OR Unknown[reflect]" and fired in every arm), and item 0 fired again — restricting the recovery to entries
with no reason of their own under-carried, and the original fixture could not notice.

**The malformed-reason blocker is RESOLVED, and the way it was resolved is the point.** The queue said ts
must not move a shape's class unilaterally and should ask the other three. The agent asked *by running all
four engines* on owner-less function values: rust `callback:unresolved call`, java
`callback:…Function.apply`, swift `callback:fn` — all class `indirect`. SPEC §4's dividing line is
normative and explicit, and PART 10 already asserts every `dispatch:` carries `owner.member`. **candor-ts
is the outlier; the reclassification moves it toward the family AND the spec, and needs no spec change.**
Correctly not landed — it narrows a gate and wants its own A/B. New datum: `826571c` makes the malformed
string travel across the boundary, so its blast radius is wider than the 68 measured.

### Phase-4 corpus round on UNSEEN code (2026-07-27) — the invariant holds at scale

Run after the sweep, on code none of these engines had been pointed at during the vein's work, to test the
two things the sweep just changed: that the getrandom-class parse containment holds across breadth, and
that the trust-marker invariant the sweep asserted is actually true on real output rather than on fixtures.

| engine | targets | entries | carrying `Unknown` | marker violations |
|---|---|---|---|---|
| rust  | 60 registry crates (excluding every crate named in this vein) | 18,485 | 420 | **0** |
| java  | 40 `~/.m2` jars (excluding every pair used in this session) | 22,270 | 13,644 | **0** |
| ts    | 4 real dependency-bearing projects | 207 | 121 | **0** |
| | | **40,962** | **14,185** | **0** |

The invariant tested is the one candor-ts asserted fail-closed in its writer (`95dc3bc`) and rust
asserted at its apply site: **an entry carrying `Unknown` must carry the marker that says so** — a
non-empty `unresolved`/`unknownWhy`. 14,185 opportunities to fail, zero failures, on code the assertion was
never written against.

Also: **60 rust crates, zero parse aborts.** The `respan_call_site` fix (`4f7b704`) had been verified on
the three getrandom versions that crashed; this is the breadth check it did not have. Note what this does
NOT show — the quiet form of that defect (a span resolving against the WRONG file rather than panicking)
is invisible here, and the 72.4% precondition rate measured at the time says it is common. The loud tail is
closed; the quiet body is disclosed and unmeasured.

Three ts targets returned **exit 2 with "no TypeScript sources"** — correct fail-closed behaviour on a
project whose sources are elsewhere, not a defect, and worth stating because a run that silently produced
an empty report there would be the exact false all-clear this vein exists to prevent.

### Verified independently (not taken on report)

- **rust's fresh-vs-stale REFUSAL is correct.** I built the two-report fixture myself: with a FRESH and a
  STALE report for one package chained, rust's consumer reads `go []` **with `invisible: ['deplib']` and
  `coverage.uncovered: [deplib]`** — unresolved but HEDGED, which is the honest answer. Aligning to the
  other three engines' fresh-wins would grant coverage while the never-guess rule still drops the colliding
  key, converting that hedge into a confident purity claim over an `Exec` the FRESH report names. java and
  ts can afford fresh-wins because their entry-level conflict KEEPS an answer (java last-wins, ts merges
  into a Set); rust's drops. **The divergence is real and rust is the correct arm** — so this closes as a
  refusal, and the two-direction fixture asserts the PREMISE (that the key really is withdrawn) so the
  argument re-opens if that ever changes rather than silently outliving itself.
- **Two findings the agents produced that outrank their own fixes**, both about tests rather than code:
  java's every-dep-fixture-used-`()V` (no reference type, hence no descriptor slash — the suite agreed on
  an accident), and rust's old `warm2` arm, which was **the assertion pinning the latch** it was meant to
  guard. That is standing-bar item 7g's third occurrence: a test can hold a defect in place.

## OPEN — found by verifying the review round (2026-07-27, me, not an agent)

Chasing candor-swift's handover ("two reports carrying an IDENTICAL entry withdrew the key as ambiguous —
rust and java should check it") turned up a confirmed cardinal sin in rust, a clean negative in java, and
one deeper defect underneath both that is NOT fixed.

**CLOSED, candor-rust `6f2210c`** — two IDENTICAL entries under one key were withdrawn. Measured both ways
on one fixture: one report chained gives `go = ['Exec']`; the SAME report chained twice gives **ABSENT, no
`invisible`, no coverage hedge**. java is CLEAN (last-wins keeps an answer) — verified directly, not
assumed. A/B free: pgman 0/0/0, ebman +2 entries recovered from absence.

- [ ] **A WITHDRAWN KEY READS AS SILENCE AT THE ORDINARY CALL JOIN — and `a1e53e7` says it must not.**
      Two TRUSTED reports that DISAGREE about one function leave the consumer ABSENT from `functions` with
      no `invisible` and no coverage hedge: a confident purity claim assembled out of the index's refusal to
      answer. This is the three-row rule (PART 21) one level down — at the INDEX rather than at the receiver
      — and `a1e53e7`'s own commit message states the requirement verbatim: *"a miss on an exact key still
      cannot distinguish 'no such method' from 'the index withdrew an entry', so it must fall back to
      disclosure, never to silence."* The `typeSurface` consumer implements it; the ordinary call join does
      not, because the withdrawn-key set is local to `load_dep_reports` and never reaches a consumer.
      **Standing-bar item 9 — a comment stating a justification the code does not implement — in a commit
      message rather than a comment.**
      I BUILT the fix (expose `withdrawn` on `DepIndex`, disclose `Unknown[dispatch:withdrawn ambiguous
      dependency key]` on a miss against it) and verified all five directions. **Not landed**, because it
      costs 30 of pgman's 200 functions and 108 of ebman's 544 newly carrying `Unknown` — 15-20%, the same
      order as the false-uncertainty flood the coverage-granularity finding measured. That is a design
      decision, and I am not making it unreviewed at the end of a long session in exactly the class of
      change two consecutive reviews have found defects in.
      **The disagreements are REAL and one of them is alarming**: `backtrace#fmt` has one entry claiming
      `["Env","Unknown"]` and another claiming PURE. Silence there matches the wrong one. Measured
      distribution of collisions: pgman 2041 withdrawals, 1536 effect-agreeing / 505 effect-disagreeing;
      ebman 3276, 2255 / 1021.
- [ ] **The effect-agreeing majority could be merged instead of withdrawn.** 1536/2041 and 2255/3276
      collisions are entries whose effect sets are IDENTICAL and whose literal surfaces merely differ;
      unioning the surfaces is the sound over-approximation. Measured cost: 24/200 and 108/544 functions
      newly carry `Unknown` — because the entries recovered are ones the DEPENDENCY could not resolve, so
      this is disclosure the consumer was previously denied rather than noise. Filed with the numbers.
- [ ] **THE FOUR ENGINES DO THREE DIFFERENT THINGS ON AN ENTRY COLLISION** and nothing pins it:
      rust WITHDRAWS, java takes LAST-WINS (it picks — which the never-guess rule forbids elsewhere), ts
      MERGES INTO A SET (unions effects). Whatever the right answer is, three answers cannot all be it, and
      a `deny` gate gives different verdicts per engine on the same two reports. Wants a conformance part
      once the decision above is made.
