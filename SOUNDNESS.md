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
| **top-level module code (load-time effect → initializer unit)** ⟨0.14⟩ | — | — | 🟢 | 🟢 | 🟢 | — |
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
| ~~R28~~ | swift | conditional conformance on a stdlib collection (`extension Array: Saveable where Element: Saveable` via `xs.persist()`) read silent-pure — two coupled gaps. **FIXED 2026-07-11** (0.8.10): (a) an array receiver edges to the local `Array.<member>` extension unit via a soft resolveQual edge (std methods drop silently, no spurious Unknown); (b) a bare `forEach { $0.method() }` over self types `$0` as the extension's `where Element: P` bound (FnInfo.selfElementType + a selfElementStack). Pure conditional conformance stays pure. | ~~SILENT low~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-11 R28 entry; gate `testConditionalConformanceOnArrayCollectionDispatches` |
| ~~R29~~ | swift | `@resultBuilder` transform read silent-pure — a func `@SomeBuilder` runs `SomeBuilder.buildBlock(…)` etc (implicit, no call site), so an effectful builder was dropped. **FIXED 2026-07-10** (0.8.9): edge the annotated func to the builder type's `build*` units; a pure builder adds nothing. | ~~SILENT v.low~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 non-accessor-seam sweep |
| ~~R30~~ | rust-scan | trait DEFAULT method via an empty impl read silent-pure (`impl Logger for S {}` + `s.log()` inheriting `Logger::log`). The caller-fallback already existed but was GATED OUT: a type whose only impl is an empty trait impl has no fn unit, so it was absent from `local_types` → its typed call was un-resolvable. **FIXED 2026-07-11** (candor-scan 0.8.8, 2 lines): register every trait-impl type as local. Override wins (no fabrication); pure default stays pure. | ~~SILENT low-med~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-11 R30 entry; gate `trait_default_method_via_empty_impl_charges_the_default_body` |
| ~~R31~~ | rust-scan | a **bounded-generic struct field** read silent-pure — `struct Pipe<T: Saver> { item: T }` reaching `self.item.save()`: field types resolved with an empty generic-bounds map, so `T` never resolved to `Saver`. **FIXED 2026-07-10** (candor-scan 0.8.7): seed the struct's own `<T: P>`/`where T: P` bounds into field trait-leaf resolution; unconstrained field read stays pure. The swift R27 analog. | ~~SILENT low-med~~ CLOSED | — | SOUNDNESS-LOG.md, 2026-07-10 cross-engine sweep; gate `generic_struct_field_resolves_to_its_trait_bound_dispatch` |
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
| ~~R32–R44~~ | ALL FOUR (cross-engine dispatch era, 2026-07-18) | **~20 trait-object / dynamic-dispatch cardinal sins** found + FIXED across every engine: provided-method→override (R32, four-way), swift deinit-glue / generic-operator / @dynamicCallable / generic-array / super-protocol (R33–R35, R39, R43-swift), rust trait-default / dyn-collection-param/generic/field / method-returns-dyn(-collection) / supertrait (R36, R37/R37b/R40, R42/R44, R43), java unbound-interface-method-ref (R38), container/Option dispatch four-way (R41). Each regression-gated + corpus-A/B'd (genuine jsoup Clock + pgman Log recoveries) + four-way-conformance-clean, on 0.22. Two halves done in PARALLEL via subagents (R41, R43). | ~~SILENT (systematic, shared)~~ CLOSED | — | full prose: SOUNDNESS-LOG.md, 2026-07-18 entries (R32→R44) |
| R45 | rust-scan | **blanket impl** `impl<T: Bound> Ext for T` + `x.ext()` — a blanket impl isn't in the concrete-keyed CHA universe, so an effectful blanket body reads silent-pure. Auto-resolving risks fabrication (a blanket method leaf edged onto any unresolved same-name call) + needs a threaded blanket index. | SILENT (open) | low/niche | effectful blanket bodies uncommon; poor fix risk/reward — documented-accepted for now |
| R46 | rust-scan | dispatch long-tail: nested `Vec<Option<Box<dyn>>>` (Option not peeled in the element), tuple-destructured dyn factory return, `Default::default()` turbofish (inferred type's effectful default). | SILENT (open) | v.low/niche | each a narrow nesting/inference shape; queued |
| R47 | ts | a sub-interface SUPER-method (`s.base()` on `s: Sub`, `interface Sub extends Sup`) reads Unknown, not the precise Fs java/rust give. | DISCLOSED (precision) | n/a | sound (Unknown disclosed) — a precision opportunity, not a cardinal sin; honesty-first posture keeps it |
| R53 | rust-scan | **trait-qualified UFCS call reads pure**: `Runner::go(&t)` and `<Task as Runner>::go(&t)` (t: Task, `impl Runner for Task` effectful) drop silent — the INHERENT form `Task::go(&t)` resolves, but the TRAIT-qualified form doesn't (no fn named `Runner::go`; the impl is `Task::go`). FABRICATION SUBTLETY: unlike `dyn Runner` dispatch (runtime type unknown → CHA-over-all-impls is the sound over-approximation), a UFCS call's receiver type is STATICALLY known (the first arg / the `<T as ..>` type), so CHA-over-all-impls would OVER-CHARGE a multi-impl trait (edging B::go/C::go onto a call that only hits Task::go). Safe pre-designed fix: resolve via the first-arg type (`&t`→Task→`Task::go`), OR edge only when the trait has EXACTLY ONE local impl (unambiguous, the R36-default discipline). Deferred: low incidence (4–8 `<T as Trait>::` sites per large crate, nearly all std-trait disambiguation — `Future`/`From`/`Default` — which candor leaves as external; a LOCAL effectful-trait UFCS target is rare). | SILENT (open) | low/niche | real but rare; the fix must stay precise (arg-typed or single-impl) — never CHA-all a statically-known-receiver call, that fabricates |
| ~~R52~~ | rust-scan | **var-clone rebind lost the pointee type**: `let a = Arc::new(Svc); let b = a.clone(); b.run()` read pure — `a.clone()` is (correctly) the pure `Arc::clone`, NOT charged, but `b` got no type (`ctor_type` doesn't consult `vars` for the clone receiver), so `b.run()` dropped. **FIXED 2026-07-18** (`2f487dd`): at the `let` binding, an untyped `<expr>.clone()` init carries `resolve_recv_type(<expr>)` to the binding (clone is type-preserving `-> Self` → sound; the clone call stays uncharged, so the anti-fabrication guard `..._but_not_clone` is untouched). Turned out HIGHER-value than estimated — the `let self_ = self.clone(); self_.call_async()` / `let mut cmd = self.cmd.clone(); cmd.build()` idiom is pervasive in tower/hyper `Service::call` + command builders. A/B RECOVERED real silent-pure, all honest (0 concrete fabrication, 0 removed): hyper-util `HttpConnector::call`→[Log,Unknown] (confirmed self.clone→call_async→trace!+connect), clap +30 (Command dispatch through `Box<dyn TypedValueParser>`). | ~~SILENT~~ CLOSED | — | regression `smart_pointer_ctor_..._dispatch` (via_clone Fs, clone_pure control) |
| R49 | rust-scan | **a local effectful-`Drop` guard held as a struct FIELD** — constructing an owner `struct Session { _g: Guard }` (or `Vec<Guard>`, or a nested owner) runs `Guard::drop` at the owner's scope exit, but reads silent-pure. The DIRECT case (a local OF the drop-type) IS charged; only the field/transitive case is missed (rust analog of swift's R33 deinit-glue, field edition). **A prototype fix (a transitive drop-owner closure over `drop_types` × `fields`/`field_elem`, no new cache plumbing) was BUILT + regression-tested green, then REVERTED on the A/B gate**: it fabricated **14 false `Unknown`s on flate2** (`Compress::new`/`Decompress::new`/… — constructors that CONSTRUCT AND RETURN the owner, whose owned `Stream`'s FFI Drop runs in the CALLER's scope, not the constructor's). Field-owners are overwhelmingly constructed-to-be-RETURNED (resource wrappers), so the returned-value escape case DOMINATES this vein — unlike direct guards (constructed-to-be-used-locally), where the same over-approximation is rare/accepted. A correct fix needs a returned-value ESCAPE GATE (swift-R33 style), which needs return-type info not cheaply available (FnInfo carries none; the `returns` index is leaf-keyed so `::new` collides and drops as ambiguous) — i.e. a new FnInfo return-type field or collector-side escape analysis. **Zero corpus incidence for direct effects** (dozens of crates; the only real local-Drop crate, flate2, flushes to a generic writer, not a classified effect). | SILENT (open) | v.low/theoretical | naive fix does NET HARM (fabricates on the pervasive constructor pattern, helps ~zero real cases); a sound fix needs escape-analysis plumbing for near-zero benefit — the A/B gate correctly rejected it |
| R48 | rust-scan | a **local `macro_rules!` whose template does DIRECT I/O** (`macro_rules! do_io { () => { fs::write(..) } }`) reads pure — `visit_macro` scans the invocation's ARG tokens (catching effects in a caller-passed `$expr`) and expands `cfg_if!`, but never the macro DEFINITION's template. Metavar templates (`$m`) that interpolate a caller expr ARE already caught (the effectful call comes from the arg). Rust-specific (java/swift/ts lack C-style macros). **Zero real-world incidence**: across dozens of local-corpus crates (flate2, commons-io, dotenv, …) 8 `macro_rules!` total and NONE with a direct-I/O template — the only hits are the synthetic probe. Pre-designed fix (deferred until it appears in real code): collect `macro_rules!` templates into a cache-threaded `local_macros` map → at a bare local-macro invocation `$`-strip the arm template + parse-or-skip as a Block + inline-`visit_block` (parse-or-skip only ever ADDS visibility, never fabricates; repetition `$(..)*` arms skip). | SILENT (open) | v.low/theoretical | real effectful macros interpolate a caller expr (already caught) or call a normal fn (caught at the fn); a template that hardcodes `fs::write` is something you'd write as a function — 15-site plumbing not justified at zero corpus incidence |

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
3. **Open SILENT residuals** (§5) = count by severity. *As of 2026-07-11 this read "**zero FIXABLE
   silent residuals remain**" — and the **2026-07-18 cross-engine dispatch era FALSIFIED that** (the §1
   point, live): a fresh systematic hunt of the trait-object/dispatch vein found **~20 fixable cardinal
   sins across all four engines** (R32–R44 in the LOG), every one now FIXED + regression-gated + corpus-
   A/B'd + four-way-conformance-clean. So "zero fixable remain" is never a provable state, only "none
   found by the hunts run so far." After that wave: the open residuals are again the FUNDAMENTAL syntactic
   limits (R2–R8, low/v.low) PLUS a NEW niche dispatch long-tail — blanket impls `impl<T: B> Ext for T`
   (fabrication-risk to auto-resolve; low value), nested `Vec<Option<Box<dyn>>>`, tuple-destructured dyn
   returns, `Default::default()` turbofish, and a ts super-interface PRECISION gap (reads sound Unknown,
   not a cardinal sin) — all characterized in the LOG (2026-07-18 long-tail entry), niche, none med+.
   Target: 0 med+; lows/niche documented-accepted; keep hunting fresh veins (the count is a floor, not a proof).*
4. **Find-rate** = cardinal sins found per fresh adversarial round. *Lede (as of 2026-07-18): SIX find
   eras — the 6th is the **cross-engine dispatch era** (2026-07-18, autonomous, part in PARALLEL via
   subagents): a systematic sweep of the trait-object / dynamic-dispatch vein across ALL FOUR engines found
   ~20 cardinal sins — R32 (a PROVIDED method driving a required OVERRIDE, four-way + a real jsoup Clock
   recovery), R33–R35 (swift deinit-glue / generic-operator / @dynamicCallable), R36 (rust trait-default →
   requirement, java/ts already sound), R37/R37b/R40 (rust dyn-collection: param / generic bound / field),
   R38 (java unbound interface-method-ref), R39 (swift generic-array), R41 (container/Option dispatch —
   HashMap values, Arc<Mutex> guard chains, Option/Result unwrap in every form; rust + swift IN PARALLEL,
   real pgman Log recovery), R42/R44 (rust method returning a bare/collection trait object), R43 (supertrait
   / super-protocol dispatch, rust + swift in parallel). Every one fixed + regression-gated + corpus-A/B'd +
   four-way-conformance-clean, all on 0.22. This era MASSIVELY re-opened the find-rate — the 5th (swift-
   resolution) era's "dropping toward zero" was premature for the SHARED dispatch vein, which had a deep
   systematic hole in every engine (the exact cross-engine-agreement blind spot §1 warns of: engines agreeing
   on the wrong PURE answer). After it, fresh NON-dispatch probes (closures / threads / channels / iterator
   adapters / std-I/O classification / stdio) came back SOUND — the dispatch vein is now saturated; the era's
   find-rate is dropping. Earlier five eras — seam-class, κ-coverage, porcelain, coverage, swift-resolution —
   every find fixed and standing-gated; convergence NOT reached, and each era shift re-opens the find-rate.
   That is the epistemic frame (§1) working as designed: two parallel subagent branches even had their OWN
   corpus-A/B gates catch over-fires mid-flight (R43-swift's 139-fn Unknown blast, self-corrected). The
   instrument's job is to make each new era's finds cheap and standing-gated, not to declare victory.*
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
| Corrupt-report false all-clear (read side) | 2026-07-13 | rust `fdb5e63` + java `60d812b` + ts `d0d0b1f` | **READ-side cardinal sin** — a found-but-untrustworthy report → `tour` "nothing hidden" / `map` empty at exit 0. Syntactic (truncated) hit rust+ts; semantic (bare junk array) hit rust+java. Swept ALL 4. | fixed loud exit 2 (syntactic + semantic); clean-empty still exit 0 (parity); PART 4k-pinned four-way + unit/fuzz gates |
| Loudness left unfinished: verbs × surfaces (max review) | 2026-07-13 | all engines + suite | **the same §4 class one surface over** — rust comparatives, ts MCP (15 sites), swift gains semantic hole, partial-graph origin downgrade ×4, fail-open 4i/4j oracles | all fixed same-day + gated (PART 5b partial, fail-closed oracles, per-engine pins); lesson: sweep engine × verb × surface |
| Alarm mutes via storage/identity, not parsing (max review r2) | 2026-07-14 | gains corpus + java union + swift/rust gains | **the ⚠⚠ oracle itself** — fabricated `{}` cache, report-only hash key, engine-blind sidecar union, --json-only disclosure | all fixed + pinned; lesson: audit the whole decision chain, undecidable oracle must fail TOWARD the alarm |
| New-effect attribution over-matches (Llm/privacy max review r3) | 2026-07-14 | all engines + candor-scan | **FABRICATION** — :11434 any-host + bedrock-substring over-match, ts raw-literal, swift AVAudioEngine playback; + the reqwest-builder under-report mirror | all fixed four-way + PART 4m given negative-case teeth; lesson: pin BOTH directions, fix a shared predicate everywhere it was copied |
| Provided Write/Read method → local required-method impl (R32, direct-method sibling of R14/R16) — **ALL FOUR ENGINES** | 2026-07-18 | rust scan+lint `445a1e0`; java `453cbe9`; swift `ef1d1c7`; ts `77cd4ae` | **SILENT-PURE** — a std/library-provided method drives the receiver's required override, invisibly: rust `s.write_all()`/`r.read_to_end()`; java `w.write(String)`/`r.read(char[])`; swift a protocol-extension `provided()` calling `req()`; ts a node `Writable.write()`→`_write`. Only the format-macro/facade edge (R14/R16) was recovered before | fixed in EVERY engine; 0 over-fire A/B (~900 rust + ~12k java + ~1.5k swift + ~770 ts real fns) + a genuine jsoup Clock recovery; four-way conformance OK; regressions + ui pins in each |
| deinit-glue — an effectful `deinit` charges the constructing scope (R33) | 2026-07-18 | swift `3f5b0f4` | **SILENT-PURE** — `let r = Resource()` where `Resource.deinit` does I/O runs at scope exit (ARC, non-escaping local) but read pure; swift-only (rust Drop-glue already sound; java/ts have no deterministic destructor) | fixed via a `propertyEdges` soft edge (drops on struct/pure-class — no external-protocol-fallback fabrication) + a returned-identifier escape gate (no `makeNSView` factory over-charge); 240 suite + regression; 0 over-fire A/B ~1.5k fns; conformance OK |
| swift generic-operator (R34) + @dynamicCallable (R35) dispatch | 2026-07-18 | swift `7f6ba58`, `2667fdc` | **SILENT-PURE** — a generic `a+b` on a `T: P` local-operator-protocol bound, and `c(1,2)` on a `@dynamicCallable` type, both read pure (the desugar was invisible) | R34 emits protoDispatch(P,op) for a protocol-typed operand; R35 a `<t>.dynamicallyCall` soft edge; each a named regression, 0 over-fire A/B ~1.5k fns, conformance OK |
| trait/interface DEFAULT calling a requirement (R36) — closed four-way | 2026-07-18 | rust `7f80e41` (java/ts/swift already) | **SILENT-PURE** (rust only) — a trait default's `self.persist()` reached an effectful impl witness but read pure; java (bytecode CHA) / ts (class-CHA) / swift (R32) already sound | rust CHA over `trait_impls` gated on `trait_decls` declaring the leaf, bounded ≤12; full suite + regression; 0 effect changes A/B ~950 fns; conformance OK |
| post-dispatch probing — gate surface verified; R48/R49 characterized | 2026-07-18 | rust-scan (no ship) | gate SOUND (Unknown non-silent + mistyped-class fail-closed + incomplete exit-2); two THEORETICAL rust veins (local-macro-template R48; drop-guard-as-field R49) | R48 zero-incidence → documented-with-fix; R49 prototype BUILT+regression-green then **A/B-REVERTED** (14 false Unknowns on flate2 — constructor-returns-owner escape); both residual, honesty-first over net-harm |
| inline struct-literal receiver typed (R50) | 2026-07-18 | rust-scan `71fad60` | **SILENT-PURE** (rust only) — a value CONSTRUCTED INLINE and immediately consumed (`for _ in (RowIter{conn})`, `(RowIter{conn}).count()`) typed to nothing, so the iterator-forcing edge + method resolution dropped it pure; `resolve_recv_type` handled `Call` (ctor_type) but not `Struct` | added the `Struct` arm; A/B **ZERO over-fire across ~2600 real fns** (syn 1442/serde_json 348/tokio 148/…); regression extended; four-way conformance OK; ts/swift swept SOUND (rust struct-literal-syntax-specific — they construct via calls) |
| smart-pointer ctor typed as its pointee (R51) | 2026-07-18 | rust-scan `f93bd6a` | **SILENT-PURE** (rust only) — `let db = Arc::new(Db::new()); db.migrate()` read pure: `ctor_type` typed the ctor as the impl-less wrapper "Arc" and dropped the `<Db>` arg (`type_path` already peels an `Arc<Db>` FIELD/param — this closes the local-binding form + inline `Arc::new(..).m()`) | `ctor_type` types `Box`/`Rc`/`Arc::new(x)` as the pointee (arg's ctor_type); Mutex/RefCell NOT peeled (methods on the wrapper). A/B **ZERO over-fire across ~2400 real fns**; the clone anti-fabrication guard verified intact (a local `Arc::new` receiver's `.clone()` still not charged); regression + four-way conformance OK; rust-specific (no Box/Rc/Arc in java/ts/swift). Clone-rebind sibling → R52 |
