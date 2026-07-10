# Soundness Confidence — the cardinal-sin tracker

The **cardinal sin** is the **silent under-report**: candor reporting a function pure / effect-free when an
effect is actually reachable from it, with **no disclosure** (no `Unknown`, no `invisible`/blind/`incomplete`).
Disclosed uncertainty is safe, and over-reporting (a fabricated effect) is the opposite failure direction — a
precision failure, guarded by the per-engine fabrication probes, never to be confused with the cardinal sin;
the silent under-report is the one failure that breaks trust. This document is the **living instrument** for
answering: *how confident are we that candor never commits it, and how do we make that confidence go up over
time?*

## 1. Epistemic frame (what "eradicate" can and can't mean)

Purity over a Turing-complete language is **undecidable** (Rice's theorem) — every static analyzer has blind
spots. We therefore cannot *prove* zero cardinal sins. The achievable, trackable goal is the **conjunction**:

1. **Every known seam** (way an effect can be reached unseen) has a **standing CI gate** — so a closed sin
   can't silently regress.
2. **Dynamic ground truth** (the syscall oracle — the only evidence that catches *shared* blindness across all
   engines) covers a **growing fraction** of real-world effect-reaching code.
3. The **residual register** of known blind spots is **explicit and shrinking** — and every residual is either
   SILENT (a real cardinal-sin risk, must be driven to zero) or DISCLOSED (marked imprecision, acceptable).
4. The **find-rate** of fresh adversarial hunts trends to **zero** across diverse new seams (convergence
   evidence — never proof).

Confidence = all four, watched over time. Not a single number — a dashboard.

## 2. The cardinal-sin surface

A silent under-report lives at one intersection of **EFFECT × SEAM × ENGINE**:

- **Effects (10):** Net · Fs · Db · Exec · Env · Clock · Rand · Ipc · Clipboard · Log
- **Engines (6):** rust-scan · rust-deep · java · ts · swift · agents
- **Seams:** the *ways* an effect reaches a function without the engine attributing it. Confidence = coverage of
  this surface by standing evidence, weighted by evidence strength.

## 3. Evidence ladder (strongest → weakest)

| # | method | catches | limits | where |
|---|--------|---------|--------|-------|
| 1 | **Dynamic syscall oracle** | shared blindness (the unknown-unknown) — observed-but-not-predicted is undeniable | Fs/Net/Exec only (syscall-distinguishable); exercised paths only; Linux | `candor-rust/soundness/realworld/` (`oracle.sh`, `realworld/run.sh`) |
| 2 | **Independent-method differential** | coverage gaps (disclosed-but-unmodeled) | finds disclosed gaps, not silent ones, unless paired with #1 | ad-hoc (the 2026-06-18 coverage round) |
| 3 | **Adversarial seam probes** | a specific structural seam class | only the seams you think to probe | the per-engine regression tests + one-shot hunts |
| 4 | **Cross-engine generative matrix** | per-engine divergence on effect×indirection | WEAK for *shared* blind spots (engines can share a gap) | `candor-spec/conformance/` (`gen_differential.py`, 72 cells as of 2026-07-09) |
| 5 | **Recall corpus** | recall holes (known-semantics APIs) | only listed APIs | `candor-rust/soundness/realworld/recall/` |
| 6 | **§4 disclosure-invariant checker** | swallowed uncertainty (propagation bugs) | NOT blindness (a never-registered call is invisible to it) | `candor-spec/conformance/check_honesty.py` |
| 7 | **Seam fuzzer** | random structural shapes | shallow | `candor-rust/soundness/gen.py` |

**Key insight:** #4 (cross-engine agreement) is the weakest for the *dangerous* case — all engines sharing a
blind spot (the log-macro bug survived 4 engines + the differential for months). Real confidence needs #1
(external ground truth), not internal consensus. Grow #1.

## 4. Status scorecard — SEAM × ENGINE

Legend: 🟢 standing CI gate · 🟡 checked once / per-engine regression test only (no *cross-engine standing*
gate) · 🔴 unchecked · ⚫ known residual (see §5) · — N/A (immune by construction)

| seam class | rust-scan | rust-deep | java | ts | swift | agents |
|---|---|---|---|---|---|---|
| direct / local-call / method-recv / loop-elem / field / callback (6 basic indirections) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢⁴ |
| key-collision (same-named unit clobber → wrong attribution) | 🟡 | — | — | 🟡 | 🟡 | 🟡 |
| **lazy-init (deferred initializer forced elsewhere)** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | — |
| deferred-iterator (lazy seq built≠consumed) ³ | 🟡 | 🟢 | 🟡 | 🟡 | 🟡 | — |
| **fire-and-forget / spawned task** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢⁴ |
| **gate-evasion / literal-masking (policy fail-closed)** | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | 🟡² |
| **implicit-conversion (effect via format/concat/interpolation)** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | — |
| FFI / extern / opaque foreign call | 🟡 | 🟢¹ | 🟡 | 🟡 | — | — |
| macro / codegen reach | 🟡 | 🟢¹ | — | — | — | — |

¹ "🟢" here = clean/correct *by construction* (verified) — but still needs a *cross-engine standing* cell to be
truly green; today these are per-engine. ² agents = the declared-vs-observed drift gate (a different shape).
³ deferred-iterator does NOT fit the shared-compilation-unit matrix (java's whole-program CHA over
`Iterator.next()` fans out across all the cells' Iterator impls and unions every effect) — stays per-engine.
⁴ agents cannot join the shared-compilation-unit matrix (its input is a fleet definition, not code); its
analogs are CI-standing per-engine: the delegation-form chains (named / CHA / ambient + curated/uncurated
MCP sinks) are fuzzed on every push (`fuzz.py`, incl. a precision-distractor twin) and regression-pinned
(`test.py` — spawn residual, hooks matcher tiers, cron entry points) — an agent spawn IS the fleet's
fire-and-forget, and the basic-indirection analog is the delegation-form set. Lazy-init has no fleet analog
(nothing defers an initializer): N/A.
**Where the scorecard stands (2026-07-09):** 🟢 is the plurality — the basic-indirection, lazy-init,
fire-and-forget, gate-evasion and implicit-conversion rows are cross-engine-standing (§7b). The remaining 🟡
rows — key-collision, deferred-iterator, FFI, macro — are per-engine by their nature (§7b: deferred-iterator
can't share a compilation unit across engines; FFI has no clean ts idiom; key-collision and macro are
engine-structural seams), each held by standing per-engine regression tests, plus rust-deep's gate-evasion
cell (the policy differential gates the user-facing engines; deep's policy surface stays per-engine). The
roadmap (§7) tracks what's left.

## 5. Residual register (known blind spots)

Each is **SILENT** (true cardinal-sin risk → drive to zero) or **DISCLOSED** (engine emits Unknown/invisible —
lower priority). Eradication = SILENT count → 0. Closed rows keep a one-line summary here; the full prose for
the essay-sized ones lives in [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md).

| id | engine | residual | kind | severity | plan |
|---|---|---|---|---|---|
| ~~R1~~ | rust-deep | implicit-conversion class — **RESOLVED 2026-06-18**: empirically already covered, not a residual | ~~SILENT~~ CLOSED | — | probe `candor-rust/ui/implicit_conversion.rs` (13-warning regression fixture) confirms all 6 sub-cases (format/Display·`?`→From·`.into()`·auto-deref·operator·Drop-glue) charge the effect + 4 pure controls stay pure. The type-aware HIR walker resolves these natively (fmt via the explicit "HOLE 2"); the scan 0.5.16 fix was the *syntactic* engine's counterpart, never needed in deep. |
| R28 | swift | **conditional conformance on a stdlib type read silent-pure**: `extension Array: Saveable where Element: Saveable { func persist() {…} }` reached via `xs.persist()` (xs: [Item]) — two gaps: `xs.persist()` doesn't edge to `Array.persist`, and `Array.persist`'s `$0.persist()` (self-element, bound Saveable) doesn't dispatch. Compound + niche. Found 2026-07-10. | SILENT | low | resolve a method on an array-typed receiver to an extension-on-Array unit; carry the extension `where Element: P` bound to type `$0` in the self-element closure |
| ~~R29~~ | swift | `@resultBuilder` transform read silent-pure — a func `@SomeBuilder` runs `SomeBuilder.buildBlock(…)` etc (implicit, no call site), so an effectful builder was dropped. **FIXED 2026-07-10** (0.8.9): edge the annotated func to the builder type's `build*` units; a pure builder adds nothing. | ~~SILENT v.low~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 non-accessor-seam sweep |
| R2 | rust-scan | auto-deref *method* calls (`w.method()` via Deref::Target) | SILENT | low | needs target-type method resolution (syntactic limit) |
| R3 | rust-scan | untyped-operand implicit-conversion (format/operator over an unresolved type) | SILENT | low | syntactic limit; accepted residual (no flood vs precision tradeoff) |
| R4 | rust-scan | bare-unit-struct iterate/drop (`for _ in Unit {}`, `let _g = Unit;`) | SILENT | v.low | rare idiom |
| R5 | rust-scan | general unresolvable-bare-call → Unknown REJECTED (floods 80/tokio) | SILENT | low | needs provenance (extern/glob) to disclose without flooding |
| R6 | rust-scan | multi-impl ambiguity, compound-assign operators | SILENT | v.low | deep was probed (round 13, 2026-06-18) — sound, gated; the residual may hold for scan only |
| R7 | swift | untyped-operand implicit-conversion | SILENT | low | syntactic limit |
| ~~R26~~ | swift | generic-constrained dispatch via a **`where T: P` clause** read silent-pure — only the inline `<T: P>` bound was collected into genericBounds, so `func f<T>(_ x: T) where T: P { x.method() }` didn't dispatch. **FIXED 2026-07-10** (0.8.9): collect where-clause conformance requirements too; gated. | ~~SILENT low-med~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 generic-dispatch entry |
| ~~R27~~ | swift | a **type-level generic bound** on a stored field read silent-pure — `struct Box<T: P> { let x: T }` reaching `x.method()`: the field typed `T` wasn't resolved to its bound `P`, so the (already-working) protocol-typed-field dispatch never fired. **FIXED 2026-07-10** (0.8.9): record type-level generic bounds (struct/class/enum/actor) + resolve a field typed as a bounded param to its bound; gated. | ~~SILENT low-med~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 generic-dispatch entry |
| ~~R24~~ | swift | property-wrapper `projectedValue` via `$` access (`m.$name`) read silent-pure — the `$`-prefixed access didn't edge to `<Wrapper>.projectedValue`. **FIXED 2026-07-10** (0.8.9): mirror the `wrappedValue` edging for `$name` (CallCollector property-read visitor); gated. | ~~SILENT low~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 accessor-vein sweep |
| ~~R25~~ | swift | keypath read of an effectful computed property (`h[keyPath: \.data]`) read silent-pure — the implicit-root keypath resolver handled only the element-iterator form (`xs.map(\.p)`), skipping the `[keyPath:]` subscript application (root = receiver's OWN type). **FIXED 2026-07-10** (0.8.9): resolve the subscript-applied keypath to the member's accessor unit; gated. | ~~SILENT low~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 accessor-vein sweep |
| R8 | java | container-erased sort `compareTo` reentry (element type erased in generic) | SILENT | low | needs element-type recovery |
| R9 | java | okio buffered read/write on an ambiguous BufferedSink | DISCLOSED | n/a | by design (Buffer-vs-socket ambiguous; construction boundary modeled) |
| R10 | ts | `@types/uuid` v8 intersection-typed `v4`; googleapis deep service verbs | DISCLOSED | n/a | reads Unknown (disclosed); modern uuid fixed |
| R11 | agents | seam battery run (2026-06-18): named-delegation-narrowing was UNSOUND (narrowed on a prompt mention, not a proof) — FIXED candor-agents 0.4.13 (`755216a`): declared `Agent(x,y)` allowlist narrows soundly; bare `Agent`+mention discloses an Unknown spawn residual; bare `Agent`+no-mention is CHA. Delegation forms / MCP-Unknown / hooks+cron entry points already covered (fuzz.py + test.py). | was UNCHECKED → mostly covered | low | remaining: allowlist naming a non-existent agent (unresolvable spawn → Unknown?); deeper hook-matcher adversarial cases |
| ~~R12~~ | rust-deep | CI self-guard ICE (nightly-2026-04-16) blocked continuous self-gating. **CLOSED 2026-07-09** (verified against the repo): the pin moved to nightly-2026-06-14, ci.yml's Self-guard step runs the deep engine on every push, `ci/self-gate.sh` gates on the STABLE scanner (never nightly-blocked), `realworld-oracle-deep.yml` runs the deep engine against the kernel oracle on every push/PR, and `nightly-bump.yml` automates the weekly nightly migration. | ~~infra~~ CLOSED | — | continuous self-gating is a standing CI property |
| ~~R13~~ | rust-deep | `thread_local!` force via `KEY.with(...)` read PURE (effect orphaned in the macro-gen init fn). **FIXED 2026-06-18** (`6010832`); gated by ui/thread_local_effects.rs. | ~~SILENT med~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-06-18 thread_local entry |
| ~~R14~~ | rust-deep + rust-scan + swift (SYSTEMIC shared blind spot) | the WRITER side of formatting read PURE — an effectful custom sink driven by a non-local format helper was dropped; silent in three engines at once, the exact case cross-engine agreement hides. **ALL FIXED 2026-06-18** (deep `0e4bf50`; scan `dabafd0` 0.5.18; swift `9368311` 0.5.22); java analog = R16; ts N/A. | ~~SILENT~~ CLOSED (3 engines) | — | prose: SOUNDNESS-LOG.md, 2026-06-18 write-fmt entry |
| R15 | — | *(number never assigned — retired to keep later ids stable)* | — | — | — |
| ~~R16~~ | java | writer side of formatting — a custom effectful `Appendable`/`Writer` driven via a JDK `Formatter`/`PrintWriter` read PURE (the R14 class, 4th engine). **FIXED 2026-06-18** (0.5.40 `5f86d3e`, constructor-site reentry); the write-fmt writer-side class is closed in all 4 engines. | ~~SILENT~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-06-18 write-fmt entry |
| ~~R17~~ | java | I/O via an ABSTRACT `java.io` stream param at a rooted entry point read PURE, not Unknown (the jsoup streaming-parser pattern). **FIXED 2026-06-21** (provenance-gated, entry-point-scoped; `R17AbstractStreamTest`); the transitive and getter-return shapes were measured/probed sound — surface genuinely near-empty. | ~~SILENT~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-06-21 R17 entry |
| ~~R18~~ | java | the **inherited-into-project silent-pure vein** (κ batches 25–27): a framework method inherited into a PROJECT type (Panache active-record; repo/base-class mixins — Micronaut Data, Ebean, ActiveJDBC, jOOQ; then ANY classify-modeled base) read silent-pure — the call owner is a project class, so neither the κ-floor invisible disclosure (external owners only) nor CHA (no project body) fired. **FIXED 2026-06-21** (`cf359ce`/`32229da`/`7421301`) — the vein CLASS closed for modeled + unmodeled bases; cross-engine check: java-specific, not shared. | ~~SILENT~~ CLOSED | — | full prose: SOUNDNESS-LOG.md, batches 25–27 |
| ~~R19~~ | java | **six classifier regressions shipped in 0.8.3** (the κ batch 28–31 breadth invited them: name/prefix owner gates + bare verb prefixes fabricating on mixed namespaces; a repo-promotion silent-pure; descriptor rules matching the RETURN position) — found by the 2026-07-08 review, NOT by CI. **FIXED 0.8.4** (`4bdb996`); the kappa_libs/mutation probes move into scheduled CI so breadth regressions stop relying on review. | ~~mixed~~ CLOSED | — | SOUNDNESS-LOG.md, "0.8.4 review patch" |
| ~~R20~~ | swift | **UserDefaults / Keychain `SecItem*` / Bundle resource lookups read silent-pure under the covered-module floor** (`Foundation`/`Security` in PLATFORM_MODULES vouch for everything, so a member gap is absolute — the Panache shape, Swift edition; ubiquitous iOS persistence invisible to the gate). **FIXED 2026-07-09** (`dd134e2`; all → Fs, verb-precise, twin-gated). | ~~SILENT~~ CLOSED | — | SOUNDNESS-LOG.md, swift κ batch |
| ~~R23~~ | swift | **setter `newValue` read silent-pure**: an effect reached THROUGH a setter's implicit value param (`set { newValue.write(toFile:) }` on a computed property/subscript, or a `willSet`) was dropped — `newValue` was never typed, so a member call on it didn't resolve. Hit computed-property + subscript setters, `willSet`, and renamed params `set(v)`. **FIXED 2026-07-10** (0.8.8): the accessor unit's `newValue`/named param is seeded with the property/subscript element type. `newValue`-as-arg to a resolved call already worked (the receiver case is the hole); pure setter stays pure. `==`/`+`/subscript-getter probed sound; ts/kotlin/rust use explicit typed setter params — swift-specific. | ~~SILENT low-med~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-07-10 setter-newValue entry; gate `DriverResolutionProcessTests.testSetterNewValueIsTypedSoEffectsThroughItResolve` |
| ~~R22~~ | swift | **inherited property accessors read silent-pure**: an effectful computed property / `didSet`-`willSet` observer / subscript whose BODY lives on a superclass was dropped when accessed through a subclass (`d.payload`, `s.name=x`, two-level) — property-edge resolution matched only the OWN type's `Type.member` unit while the method-call path already climbed `supertypesOf` (the R18 vein, property edition). **FIXED 2026-07-10** (0.8.7): property edges now climb `supertypesOf` (transitive; override-wins so no fabrication; pure inherited stays pure). candor-ts + java checked SOUND (not shared). | ~~SILENT med~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-07-10 inherited-property-accessor entry; gate `DriverResolutionProcessTests.testInheritedPropertyAccessorEffectsClimbTheHierarchy` |
| ~~R21~~ | family porcelain | the **2026-07-09 whole-project review's fail-open class**: gate surfaces converting "the gate could not run" into green — cargo-candor `policy` build-failure `\|\| true` and `guard` with no baseline ever snapshotted; java `--gate-json` unwritable → exit 0, `CANDOR_DEPS` typo silently ignored; ts MCP `candor_whatif` bad policy path + configured-but-empty policy falsy-skipped; agents `gate_reports` fail-open dead code + undisclosed observed-paths truncation. The engine-level fail-closed doctrine had never swept the OUTPUT/auxiliary channels or the shell porcelain. **FIXED 2026-07-09** (same-day wave, per repo; conformance PARTs 14–15 + wrapper CI lanes added as standing gates). | ~~fail-open~~ CLOSED | — | prose: SOUNDNESS-LOG.md, 2026-07-09 whole-project review entry |

## 6. The metric (track these four; each "step forward" moves one)

1. **Cardinal-surface coverage** = % of (seam × engine) cells at 🟢 in §4. *As of 2026-07-09: the
   cross-engine matrix holds **72** vs-ground-truth cells (9 indirections/seams × 8 effects — the growth
   history 30 → 48 → 64 → 72 is §7b's narrative), 4 of 6 seam classes are cross-engine-standing (§7b), and
   strict mode (G1/G2) makes the gate un-foolable. The rust-deep column is 🟢 except its gate-evasion cell
   (the masked-literal differential gates the user-facing scan/java/ts/swift gates; deep's policy surface
   stays per-engine); the remaining 🟡 rows are per-engine by nature (§4 note). Target: every closed seam →
   🟢 via the matrix's SEAM axis where it fits, standing per-engine gates where it doesn't.*
2. **Oracle coverage** = # real crates × effects under dynamic ground truth (§3 #1). *2026-06-18: grew 7→11
   crates — Net ×3 (std/minreq/ureq), Exec ×3 (duct/xshell/std), Fs ×4 (fs-err/std/walkdir/tempfile) — now
   ≥3 per syscall-distinguishable effect (Fs/Net/Exec); incl. the walkdir calibration confirmed vs the kernel
   + tempfile as a disclosure probe. + 13 crates with an UNCALIBRATED disclosure probe per
   effect (minreq/subprocess/fs_extra — a crate candor doesn't model, exercised for real; the strongest test).
   Rand/Clock are syscall-distinguishable but markerless/noisy (getrandom has no string arg; HashMap seeds
   getrandom) — covered by the non-syscall recall complement instead. **NOW CONTINUOUS: `realworld-oracle.yml`
   runs on every push to main + every PR (was workflow_dispatch) → kernel ground truth is a STANDING gate, a
   new silent under-report on a real crate fails CI.** And the NON-SYSCALL RECALL complement now covers the
   last 2 effects (Env, Clock — recall corpus 14→20 cases, all sound), so with the syscall oracle (Fs/Net/
   Exec) candor's effect classification is under ground-truth/known-semantics coverage for ALL 10 EFFECTS.
   Recall is also wired into realworld-oracle.yml → BOTH ground-truth methods are now continuous standing
   gates. 2026-06-18: moved the session's adversarial-sweep finds UP the evidence ladder to ground truth —
   syscall oracle 13→**14 drivers** (added `fs_writefmt`: a custom `fmt::Write` writing a marker file via
   `write!`; CI-verified `ran=1 effect=Fs candor=[Fs] certain` — the write-fmt class now KERNEL-gated, the
   strongest evidence, independent of engine logic); recall 20→**23** (seam_lazy_force/seam_thread_local/
   seam_write_fmt, all →Clock). realworld-oracle.yml run GREEN: 14 sound / 0 under-reports / 0 fabrications,
   recall 23 sound. So the systemic write-fmt shared blind spot is now caught by EXTERNAL ground truth, not
   just engine-internal fixtures. NEXT: more uncalibrated recall probes; deepen each effect's real-crate
   diversity.*
3. **Open SILENT residuals** (§5) = count by severity. *As of 2026-07-10: **8 open (R2–R8, R28), all
   low/v.low; 0 med+** (R24–R27, R29 opened + FIXED same day; R28 conditional-conformance-on-stdlib open, niche). Everything opened since the baseline (R13, R14/R16, R17–R21) was driven to CLOSED — see the
   register and the LOG. Target: 0 med+; lows documented-accepted.*
4. **Find-rate** = cardinal sins found per fresh adversarial round. *Lede (as of 2026-07-10): FIVE find
   eras so far — the 5th is the **swift-resolution era** (2026-07-10, autonomous): the syntactic swift engine's
   access-path/dispatch resolution had a vein of silent holes — R22–R27 + R29 (inherited accessors, setter
   newValue, projected/keypath, generic where-clause/type-level bound, resultBuilder), all fixed + gated +
   (0.8.7/0.8.8 shipped, 0.8.9 staged); R28 open (niche). 8 further non-accessor seams probed sound. The
   era's find-rate is now dropping toward zero. Earlier four eras — seam-class, κ-coverage, porcelain, coverage — every find fixed and standing-gated;
   convergence NOT reached, and each era shift re-opens the find-rate. That is the epistemic frame (§1)
   working as designed: the instrument's job is to make each new era's finds cheap and standing-gated, not
   to declare victory.*
   - *Inheritance-of-accessors probe (2026-07-10): 1 find — swift inherited property accessors (computed
     getter / `didSet` / subscript) read silent-pure through a subclass while inherited METHODS climbed
     (R22, fixed 0.8.7, gated). A "covered seam, uncovered edition" find: the accessor climb existed for
     the own type and the method climb existed for inheritance, but their intersection did not. candor-ts +
     java were probed with the same shape and are sound — swift-specific, not shared. Prose: LOG.*
   - *Operator-overload / setter probe (2026-07-10): 1 find — swift setter `newValue` read silent-pure
     (an effect through the implicit value param, `set { newValue.write(…) }`; computed-property + subscript
     setters + `willSet`), because `newValue` was never typed (R23, fixed 0.8.8, gated). The operator paths
     themselves — `==`, `+`, subscript-getter — were sound; ts/kotlin/rust use explicit typed setter params
     (no implicit `newValue`), so swift-specific. Another "covered seam, uncovered edition": accessor bodies
     were collected, but the setter's implicit param wasn't given the type that lets its member calls
     resolve. Prose: LOG.*
   - *Error-path / cleanup-block probe (2026-07-10): 0 finds — an effect that runs ONLY in a `finally` /
     `catch` / Swift `defer`/`guard-else` / Rust error combinator / implicit try-with-resources `close()`
     is charged by all four engines (they walk the full statement tree; the cleanup path is an ordinary
     call edge). Java's try-with-resources — an effect via a compiler-synthesized `close()` — is the
     sharpest case and is sound (the close is real bytecode). Convergence evidence, not promoted to a
     standing gate. Prose: LOG.*
   - *Seam-class era (2026-06-18 → 06-21, rounds 1–17): ~14 finds, all fixed + gated. Highlights: the
     lazy-init forcing site (rust-deep `8bf9c6b`), the agents named-delegation narrowing (a prompt mention
     is not a spawn-set proof, `755216a`), thread_local (R13), and the write-fmt writer side (R14/R16) — a
     SYSTEMIC blind spot silent in four engines at once, the exact case cross-engine agreement hides; since
     then a find in one engine triggers a sweep of all. Rounds 7, 8, 12 and 13 found 0. Validated on real
     code the same era (the PetClinic end-to-end gate, the gson InetAddress catch). Full round-by-round
     narrative: SOUNDNESS-LOG.md, the seam-class-era entry.*
   - *κ-coverage and porcelain eras (2026-06-21 → 2026-07-09; full prose per entry in SOUNDNESS-LOG.md;
     register entries R18–R21): real-app dogfooding found the inherited-into-project silent-pure vein and
     closed the CLASS (batches 25–27, R18); the uflexi legacy round mined batches 28–31 to a zero ledger and
     found one live silent-Net member gap (Jackson, batch 30b); the breadth invited six shipped classifier
     regressions (0.8.4 review patch, R19 — caught by review, now moving under scheduled CI); the same
     covered-module shape then surfaced in swift (UserDefaults/Keychain/Bundle, R20); and the 2026-07-09
     whole-project review opened a THIRD find category — porcelain/output-channel fail-opens (R21), plus one
     normative contradiction (AS-EFF-008's opaque case: spec text vs the conformance-pinned fail-closed
     behavior — the written contract had lagged the machine-checked one since the 0.5.15 hardening). All
     fixed; chaining + stale-baseline became conformance PARTs 14–15 the same day, and PART 14's first run
     caught candor-scan's missing empty-report ledger exemption.*
   - *Coverage era (2026-07-10): the first-ever coverage measurement made "documented surface with zero
     executions" a find category of its own — four real bugs, including a broken user-facing gate
     (candor-java's CANDOR_STRICT checkConformance had never been executed by any harness). See the LOG's
     coverage-wave entry and §8.*

## 7. Roadmap (meaningful, measurable steps)

1. **Standing gates (highest leverage):** extend `conformance/gen_differential.py` from 6 indirections to the
   full seam set (each seam × effect × engine = a CI cell). Converts the 🟡 one-shot hunts to 🟢; a regression
   becomes un-shippable. *DONE for the classes the matrix can hold (2026-06-18, §7b): 4 of 6 seam classes are
   cross-engine-standing; deferred-iterator + FFI stay per-engine by nature.*
2. **Grow the dynamic oracle (strongest evidence):** add real crates per effect to `soundness/realworld/`,
   wire `realworld-oracle.yml` to run in CI on every push. *DONE 2026-06-18 (metric #2): 14 oracle drivers +
   23 recall cases run on every candor-rust push. Growth (more crates/effects) remains open-ended.*
3. **Eradicate SILENT residuals (§5):** R1 done (already covered); drive the remaining R2–R8 (all low/v.low) to
   zero or convert to disclosed-Unknown. *Each = a step on metric #3.*
4. **rust-deep parity + unblock its self-guard (R12):** the deep engine must carry every scan fix and
   be continuously gated. *Self-guard part DONE (R12 closed 2026-07-09): the nightly pin moved past the ICE,
   the Self-guard step + `realworld-oracle-deep.yml` run in CI on every push, and `nightly-bump.yml` automates
   future bumps.*
5. **agents seam battery (R11):** run the six seam classes against the agents drift model. *DONE 2026-06-18
   (round 10, R11): one find (named-delegation narrowing), fixed + CI-gated; the §4 agents column now reflects
   it (footnote ⁴).*
6. **Convergence log:** record each adversarial round's find-rate in [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md), one
   entry per round (§6 metric 4 keeps the compressed view); a sustained zero across *diverse* new seams is the
   strongest convergence signal we can have.

## 7b. Gate integrity — the gate itself was code-reviewed + hardened (2026-06-18)

Before extending the gate we reviewed *the gate*. The core is sound: the generative matrix compares each
engine against a **hardcoded EXPECTED effect** (vs-ground-truth, not mere inter-engine agreement — so it
catches even a *shared* blind spot), absent-fn → PURE → DROP → fails, and the callback accepted-band tolerates
`Unknown` but never silent-pure. Three findings, all addressed:

- **G1 (fixed) — silent engine-skip → false multi-engine green.** A skipped (absent) ts/swift engine left the
  verdict "OK" with fewer engines; a misconfigured CI could read a 2-engine pass as a 4-engine guarantee.
  FIX: `CONFORMANCE_REQUIRE_ALL=1` strict mode — a skipped engine now FAILS (run.sh Parts 6/6c + gen_differential).
  Verified: strict + engine absent → exit ≠ 0; strict + all present → exit 0.
- **G2 (fixed) — `check_honesty.py` silently degraded** when the callgraph sidecar was missing (fell back to
  inline `calls`, which misses pure-fn callers — the dangerous case). FIX: strict mode FAILS on a missing
  callgraph. Verified.
- **G3 (in progress) — coverage was the real limit.** The matrix is vs-ground-truth, so every (effect×seam)
  cell it covers is strongly gated and every one it doesn't is ungated. Extended the EFFECT axis 5→8
  (added **Rand/Db/Log**, the proven-cross-engine vocab; matrix 30→48 cells, all engines agree). **Ipc/Clipboard
  stay out by design** (no JDK std IPC primitive; no node clipboard model — structurally per-engine). Remaining
  G3 work = the SEAM axis (add renderers for lazy-init / deferred-iterator / fire-and-forget / implicit-conversion
  / gate-masking / FFI to the matrix) — the next roadmap increment. **STARTED: implicit-conversion +
  fire-and-forget are now matrix INDIRECTIONS (matrix 48→64 cells, all 4 engines agree, exact {effect}) —
  those two seam rows are now 🟢 cross-engine-standing. THEN lazy-init too (matrix 64→72, all 4 agree) → 3 of 6
  seam classes are now 🟢.** The other 3 don't fit the EFFECT matrix: deferred-iterator (java whole-program CHA
  over a shared `Iterator` interface unions every cell's effect — footnote ³); gate-masking (a POLICY-verdict
  seam — extend the policy differential instead); FFI (expected is {Unknown}/disclosure, no clean ts idiom).
  So the matrix seam-axis is effectively COMPLETE for the classes it can hold; the residual 3 stay per-engine
  (🟡) by their nature, documented here. THEN gate-masking too, via a SEPARATE policy-verdict differential
  (`gen_masking.py`, also wired into run.sh): for each literal-surface effect {Net→host, Exec→cmd, Fs→path,
  Db→table}, a MASKED denied literal beside a benign one must FAIL the `allow <Effect> <benign>` gate
  (fail-closed) in every engine, and the compliant program must PASS — 16 (effect×engine) cells, all green.
  Building it SURFACED a real swift gate-evasion: `shellOut(to: runtimeVar)` (ShellOut, classified Exec) was
  missing from the Exec establishing set, so a masked command evaded `allow Exec` — FIXED (candor-swift 0.5.21,
  `1a60bce`). So **4 of 6 seam classes are now cross-engine-standing** (implicit-conv/fire-forget/lazy-init via
  the effect matrix; gate-masking via the policy differential); only deferred-iterator (java CHA artifact) and
  FFI (expected {Unknown}, no clean ts idiom) remain per-engine by nature.

**CI action item — DONE (2026-07-09):** conformance.yml now carries a macos four-engine job running with
`CONFORMANCE_REQUIRE_ALL=1` (all four toolchains provisioned), alongside the fast ubuntu three-way leg and a
weekly released-artifacts leg. Strict mode is a standing CI property, no longer local-only.

## 8. How to read confidence today (2026-07-10)

- **Floor is solid and continuously gated:** the §4 disclosure invariant (never silent-pure where an effect
  is reached) is a standing conformance part over every engine's own report; the kernel syscall oracle +
  recall corpus run on every candor-rust push; the cross-engine matrix holds 72 vs-ground-truth cells;
  the masked-literal policy verdict, gate-verdict/exit agreement, `.candor/config`, chaining and the
  stale-baseline posture are all standing four-way differentials (conformance PARTs 12–15).
- **The find-rate has NOT converged** — and the finds have changed shape. The seam-class era (rounds
  1–17, ~14 finds, all fixed) gave way to the κ-coverage era: real-app dogfooding keeps surfacing
  covered-namespace member gaps (Panache, the inherited-into-project class, the legacy-enterprise tier,
  Jackson's live silent-Net, swift's UserDefaults/Keychain) — and breadth-work invites its own
  regressions (the 0.8.4 review patch: six classifier regressions shipped in 0.8.3, caught by review,
  not CI). The 2026-07-09 whole-project review added a third era: the *porcelain* — fail-opens in the
  layers users invoke (cargo-candor policy/guard, gate-json write paths, deps resolution) that the
  engine-level fail-closed doctrine never swept. And the 2026-07-10 coverage wave added a fourth:
  *documented surfaces with zero executions* — the first-ever coverage measurement showed several
  documented, load-bearing gate surfaces had never been executed by any harness, and pinning them found
  four real bugs, including a broken user-facing gate (candor-java's CANDOR_STRICT `checkConformance`).
- **So: high and rising on the analysis core; the active frontier is κ-coverage member gaps,
  gate-surface fail-opens, and never-executed surfaces — each now with standing gates.** Treat any new
  framework's inherited-into-project shape, any new output/auxiliary channel, and any documented surface
  with zero executions as guilty until gated.

### 8.1 Round & batch index (prose in [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md))

| entry | date | engine | class | outcome |
|---|---|---|---|---|
| Seam-class era, rounds 1–17 (find-rate narrative) | 2026-06-18 | all engines | 6 seam classes + sweeps | ~14 finds, all fixed + gated |
| thread_local force (R13) | 2026-06-18 | rust-deep `6010832` | **SILENT** (macro-gen init orphaned) | fixed + gated |
| write-fmt writer side (R14 + R16) | 2026-06-18 | deep/scan/swift/java | **SILENT** shared blind spot (writer sink) | fixed in all 4 engines |
| Java adversarial round | 2026-06-20 | java | ~55 synthetic fixtures, 5 mechanism families | 0 silent |
| Cross-language round | 2026-06-21 | java (Kotlin/Groovy) | compiler-generated dispatch | 0 silent, find-rate 0 |
| κ batch 24 — Hibernate-6/Jakarta Data | 2026-06-21 | java `ed231ed` | DISCLOSED invisible → modeled Db | precision |
| κ batch 25 — Quarkus Panache | 2026-06-21 | java `cf359ce` | **SILENT-PURE sin** (inherited-into-project) | fixed + gated |
| κ batch 26 — Micronaut/Ebean/ActiveJDBC/jOOQ | 2026-06-21 | java `32229da` | **SILENT-PURE** ×4 (same vein, probed) | fixed + gated |
| κ batch 27 — modeled-base subclass, general | 2026-06-21 | java `7421301` | **SILENT-PURE** class closed | fixed + gated |
| Cross-engine vein check | 2026-06-21 | scan/ts/swift | inherited-into-project | java-specific, not shared |
| Abstract-stream entry-point params (R17) | 2026-06-21 | java | **SILENT**, narrow surface (measured near-empty) | fixed + gated |
| κ batch 28 — legacy-enterprise tier (JCL/…) | 2026-07-06 | java `aefca4f` | DISCLOSED → modeled | precision |
| κ batch 29 — next tier, same discipline | 2026-07-06 | java `2575683` | DISCLOSED → modeled | precision |
| κ batch 30/30b — Jackson (+ live silent-Net find) | 2026-07-06 | java `cd617cb` | **SILENT-NET** member gap | fixed + gated |
| κ batch 31 — long-tail sweep, ledger → zero | 2026-07-07 | java `17eb81d` | DISCLOSED → modeled | ledger empty |
| 0.8.4 review patch | 2026-07-08 | java `4bdb996` | **6 regressions** batches 28–31 shipped | fixed + gated |
| κ batch — UserDefaults/Keychain/Bundle | 2026-07-09 | swift `dd134e2` | **SILENT-PURE** (covered-module) | fixed + gated |
| Whole-project review (porcelain fail-opens et al.) | 2026-07-09 | all repos | fail-open gate surfaces, doc drift | fix wave, conformance PARTs 14–15 added |
| candor-scan κ-ledger §2 rule-3 gap | 2026-07-09 | scan `2d32086` | over-disclosure on chained empty reports | fixed, PART 14-pinned |
| candor-java mutation_probe rot | 2026-07-09 | java `a6c60c0` | meta-soundness decay (3/14 patch-error) | re-anchored 14/14, weekly CI |
| Coverage wave — never-executed gate surfaces | 2026-07-10 | all engines | **4 bugs in 0-coverage surfaces** (strict-gate 001 over-fire, guard fail-open, positional swallow, watch no-quit) + swift payload-host parity | all fixed red-then-green; TESTING.md standards |
