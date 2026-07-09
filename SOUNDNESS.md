# Soundness Confidence — the cardinal-sin tracker

The **cardinal sin** is the **silent under-report**: candor reporting a function pure / effect-free when an
effect is actually reachable from it, with **no disclosure** (no `Unknown`, no `invisible`/blind/`incomplete`).
Over-reporting (a spurious effect) and *disclosed* uncertainty are safe; a silent under-report is the one
failure that breaks trust. This document is the **living instrument** for answering: *how confident are we that
candor never commits it, and how do we make that confidence go up over time?*

## 1. Epistemic frame (what "eradicate" can and can't mean)

Purity over a Turing-complete language is **undecidable** (Rice's theorem) — every static analyzer has blind
spots. We therefore cannot *prove* zero cardinal sins. The achievable, trackable goal is the **conjunction**:

1. **Every known seam** (way an effect can be reached unseen) has a **standing CI gate** — so a closed sin
   can't silently regress.
2. **Dynamic ground truth** (the syscall oracle — the only evidence that catches *shared* blindness across all
   engines) covers a **growing fraction** of real-world effect-reaching code.
3. The **residual register** of known blind spots is **explicit and shrinking** — and every residual is either
   SILENT (a real cardinal-sin risk, must be driven to zero) or DISCLOSED (honest imprecision, acceptable).
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
| 2 | **Independent-method differential** | coverage gaps (disclosed-but-unmodeled) | finds honest gaps, not silent ones, unless paired with #1 | ad-hoc (the 2026-06-18 coverage round) |
| 3 | **Adversarial seam probes** | a specific structural seam class | only the seams you think to probe | the per-engine regression tests + one-shot hunts |
| 4 | **Cross-engine generative matrix** | per-engine divergence on effect×indirection | WEAK for *shared* blind spots (engines can share a gap) | `candor-spec/conformance/` (`gen_differential.py`, 30 cells) |
| 5 | **Recall corpus** | recall holes (known-semantics APIs) | only listed APIs | `candor-rust/soundness/realworld/recall/` |
| 6 | **§4 honesty-invariant checker** | swallowed uncertainty (propagation bugs) | NOT blindness (a never-registered call is invisible to it) | `candor-spec/conformance/check_honesty.py` |
| 7 | **Seam fuzzer** | random structural shapes | shallow | `candor-rust/soundness/gen.py` |

**Key insight:** #4 (cross-engine agreement) is the weakest for the *dangerous* case — all engines sharing a
blind spot (the log-macro bug survived 4 engines + the differential for months). Real confidence needs #1
(external ground truth), not internal consensus. Grow #1.

## 4. Status scorecard — SEAM × ENGINE

Legend: 🟢 standing CI gate · 🟡 checked once / per-engine regression test only (no *cross-engine standing*
gate) · 🔴 unchecked · ⚫ known residual (see §5) · — N/A (immune by construction)

| seam class | rust-scan | rust-deep | java | ts | swift | agents |
|---|---|---|---|---|---|---|
| direct / local-call / method-recv / loop-elem / field / callback (6 basic indirections) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 |
| key-collision (same-named unit clobber → wrong attribution) | 🟡 | — | — | 🟡 | 🟡 | 🟡 |
| **lazy-init (deferred initializer forced elsewhere)** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 |
| deferred-iterator (lazy seq built≠consumed) ³ | 🟡 | 🟢 | 🟡 | 🟡 | 🟡 | — |
| **fire-and-forget / spawned task** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 |
| **gate-evasion / literal-masking (policy fail-closed)** | 🟢 | 🟡 | 🟢 | 🟢 | 🟢 | 🟡² |
| **implicit-conversion (effect via format/concat/interpolation)** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | — |
| FFI / extern / opaque foreign call | 🟡 | 🟢¹ | 🟡 | 🟡 | — | — |
| macro / codegen reach | 🟡 | 🟢¹ | — | — | — | — |

¹ "🟢" here = clean/correct *by construction* (verified) — but still needs a *cross-engine standing* cell to be
truly green; today these are per-engine. ² agents = the declared-vs-observed drift gate (a different shape).
³ deferred-iterator does NOT fit the shared-compilation-unit matrix (java's whole-program CHA over
`Iterator.next()` fans out across all the cells' Iterator impls and unions every effect) — stays per-engine.
**This scorecard is the gap:** almost everything is 🟡 — closed once, with a per-engine regression test, but NOT
in the cross-engine standing matrix. The roadmap (§6) is mostly "turn 🟡 → 🟢".

## 5. Residual register (known blind spots)

Each is **SILENT** (true cardinal-sin risk → drive to zero) or **DISCLOSED** (engine emits Unknown/invisible →
honest, lower priority). Eradication = SILENT count → 0.

| id | engine | residual | kind | severity | plan |
|---|---|---|---|---|---|
| ~~R1~~ | rust-deep | implicit-conversion class — **RESOLVED 2026-06-18**: empirically already covered, not a residual | ~~SILENT~~ CLOSED | — | probe `candor-rust/ui/implicit_conversion.rs` (13-warning regression fixture) confirms all 6 sub-cases (format/Display·`?`→From·`.into()`·auto-deref·operator·Drop-glue) charge the effect + 4 pure controls stay pure. The type-aware HIR walker resolves these natively (fmt via the explicit "HOLE 2"); the scan 0.5.16 fix was the *syntactic* engine's counterpart, never needed in deep. |
| R2 | rust-scan | auto-deref *method* calls (`w.method()` via Deref::Target) | SILENT | low | needs target-type method resolution (syntactic limit) |
| R3 | rust-scan | untyped-operand implicit-conversion (format/operator over an unresolved type) | SILENT | low | syntactic limit; honest residual (no flood vs precision tradeoff) |
| R4 | rust-scan | bare-unit-struct iterate/drop (`for _ in Unit {}`, `let _g = Unit;`) | SILENT | v.low | rare idiom |
| R5 | rust-scan | general unresolvable-bare-call → Unknown REJECTED (floods 80/tokio) | SILENT | low | needs provenance (extern/glob) to disclose without flooding |
| R6 | rust-scan/deep | multi-impl ambiguity, compound-assign operators | SILENT | v.low | — |
| R7 | swift | untyped-operand implicit-conversion | SILENT | low | syntactic limit |
| R8 | java | container-erased sort `compareTo` reentry (element type erased in generic) | SILENT | low | needs element-type recovery |
| R9 | java | okio buffered read/write on an ambiguous BufferedSink | DISCLOSED | n/a | by design (Buffer-vs-socket ambiguous; construction boundary modeled) |
| R10 | ts | `@types/uuid` v8 intersection-typed `v4`; googleapis deep service verbs | DISCLOSED | n/a | honest (reads Unknown); modern uuid fixed |
| R11 | agents | seam battery run (2026-06-18): named-delegation-narrowing was UNSOUND (narrowed on a prompt mention, not a proof) — FIXED candor-agents 0.4.13 (`755216a`): declared `Agent(x,y)` allowlist narrows soundly; bare `Agent`+mention discloses an Unknown spawn residual; bare `Agent`+no-mention is CHA. Delegation forms / MCP-Unknown / hooks+cron entry points already covered (fuzz.py + test.py). | was UNCHECKED → mostly covered | low | remaining: allowlist naming a non-existent agent (unresolvable spawn → Unknown?); deeper hook-matcher adversarial cases |
| R12 | rust-deep | CI self-guard ICE (nightly-2026-04-16) blocks continuous self-gating | infra | med | nightly bump / rustc_private migration (parked) |
| ~~R13~~ | rust-deep | `thread_local!` force via `KEY.with(...)` read PURE (effect in the macro-gen init fn, orphaned behind non-local `LocalKey::with`). **FIXED 2026-06-18** (`6010832`) | ~~SILENT med~~ CLOSED | — | a method call on a `LocalKey` receiver edges the forcing fn to the local init fn(s) referenced in that thread_local item's body (intravisit FnDef-ref collector). Sound (pure init → nothing); gated by ui/thread_local_effects.rs |
| ~~R14~~ | rust-deep **+ rust-scan + swift** (SYSTEMIC shared blind spot) | the WRITER side of formatting read PURE — an effectful custom sink (`fmt::Write`/`io::Write` via `write!`; Swift `TextOutputStream` via `print(to:)`/`write(to:)`) driven by a non-local format helper was dropped (distinct from the arg-Display side, which all engines handled). Found in rust-deep, then a cross-engine SWEEP found the SAME gap silent in **candor-scan** (the user-facing floor) AND **candor-swift** — the dangerous shared case cross-engine agreement hides. **ALL FIXED 2026-06-18** (deep `0e4bf50` HOLE 2c; scan `dabafd0` 0.5.18; swift `9368311` 0.5.22 modelOutputStreamCall). | ~~SILENT~~ CLOSED (3 engines) | — | gated by ui/write_trait.rs (deep), write_macro test (scan), smoke N4b (swift). candor-java analog PROBED — also silent (see R16, tracked); candor-ts has no clean writer-sink idiom (N/A). `thread_local!` swept too — scan handles it (not shared). |
| ~~R16~~ | java | writer side of formatting — a custom effectful `Appendable`/`Writer` wrapped in a JDK `Formatter`/`PrintWriter` and driven by `format`/`printf` read PURE. The 4th engine with the R14 class. **FIXED 2026-06-18** (candor-java 0.5.40 `5f86d3e`). | ~~SILENT~~ CLOSED | — | a CONSTRUCTOR-site reentry: at `new Formatter(Appendable)` / `new PrintWriter(Writer\|OutputStream)` / `new PrintStream(OutputStream)`, edge the enclosing method to the sink arg's `append`/`write` (new C_APPEND/C_WRITE contracts, by-name reentryEdge over the arg's declType, same machinery as compareTo). Resolve-or-skip → a std StringBuilder/FileOutputStream sink contributes nothing. Gated by ImplicitReentryTest.writerSideCustomSinkCarriesEffect; PetClinic + jsoup/gson/HikariCP dogfoods byte-for-byte unchanged (no fabrication). **So the write-fmt writer-side class is now closed in ALL 4 engines (rust deep/scan, swift, java).** |
| ~~R17~~ | java (also the jsoup streaming-parser pattern) | I/O via an ABSTRACT `java.io` stream (`Reader`/`InputStream`/`Writer`/`OutputStream`) whose concrete impl candor can't pin read PURE, not Unknown — e.g. an entry point `void onData(InputStream s){ s.readAllBytes(); }` where the framework injects `s`. **FIXED 2026-06-21** (provenance-gated, entry-point-scoped). | ~~SILENT~~ CLOSED | — | **Fix:** in `analyze`, when a call classifies pure AND is an I/O verb on an abstract `java.io` stream base (`isAbstractStreamIo`) AND the receiver is the method's OWN param by ProvValue identity (`isOwnParam`) AND the method is a rooted ENTRY POINT (`ctx.entryPoints`), disclose `Unknown` with `unknownWhy=dispatch:<owner>.<verb>`. Entry-point gating is what avoids the flood: an internal helper reading a PASSED stream stays pure (its in-project caller holds the concrete → effect already attributed at the creation site; the common case stays globally sound, e.g. the `AbstractReaderParse` corpus fixture's Fs at `main` and jsoup's Net/Fs at `connect`/`parse(File)` are unchanged). Gated by `R17AbstractStreamTest` (entry-point param read → Unknown; non-entry helper → pure, no flood; concrete creator → Fs unchanged). PetClinic/jsoup/gson byte-for-byte unchanged; native==jar; soundness 40 + kappa_libs 438 + conformance green. RESIDUAL (low, MEASURED 2026-06-21): the TRANSITIVE case — an entry point that PASSES its abstract-stream param to a helper which reads it — is not covered (would need interprocedural param-flow). A code-review worried this might be the COMMON framework shape; MEASURED across 6 real jars incl **spring-web** (4196 fns / 129 entry points): **0 rooted entry points take an abstract-`java.io`-stream param at all, and R17 fires 0 times** — so both the direct and transitive cases are genuinely rare. The real framework shape is `request.getInputStream().read()` (stream from a getter INSIDE the method), NOT an `InputStream` param — a SEPARATE getter-return-abstract-stream question R17 doesn't address (receiver is a call-return, not a param). PROBED 2026-06-21 → SOUND, no cardinal sin: (i) JDK I/O types — `Socket`/`URLConnection`/`Process`/`HttpExchange` getters classify to the precise effect (Net/Exec) even when the object is a PARAM (the getter itself is modelled, not just the creation); (ii) framework interface types — `HttpServletRequest.getInputStream`/`getReader`, Spring `HttpInputMessage.getBody` disclose `Unknown` via candor's GENERAL unresolved-interface dispatch (no in-scope impl → the getter call itself is `dispatch:<iface>.<method>` Unknown, before any read); (iii) in-memory concrete (`ByteArrayInputStream`) stays pure — no flood. So the getter-return shape needs no fix; R17's narrow surface is the only place this class isn't already covered by precise-effect or unresolved-dispatch disclosure. So the deeper param-taint fix is NOT warranted for this empty surface. (#3 reviewed too: the `dispatch:` kind is spec-CANONICAL here — SPEC.md §4 defines `dispatch:<type>.<method>` as "an abstraction with no visible impl", exactly R17's abstract-stream-with-unknown-concrete; a new kind would break the 4-kind vocabulary for a 0-occurrence case, so unchanged.) |
| R15 | — | *(number never assigned — retired to keep later ids stable)* | — | — | — |
| ~~R18~~ | java | the **inherited-into-project silent-pure vein** (κ batches 25–27): a framework method inherited into a PROJECT type (Panache active-record; repo/base-class mixins — Micronaut Data, Ebean, ActiveJDBC, jOOQ; then ANY classify-modeled base) read silent-pure — the call owner is a project class, so neither the κ-floor invisible disclosure (external owners only) nor CHA (no project body) fired. **FIXED 2026-06-21** (`cf359ce`/`32229da`/`7421301`) — the vein CLASS closed for modeled + unmodeled bases; cross-engine check: java-specific, not shared. | ~~SILENT~~ CLOSED | — | full prose: SOUNDNESS-LOG.md, batches 25–27 |
| ~~R19~~ | java | **six classifier regressions shipped in 0.8.3** (the κ batch 28–31 breadth invited them: name/prefix owner gates + bare verb prefixes fabricating on mixed namespaces; a repo-promotion silent-pure; descriptor rules matching the RETURN position) — found by the 2026-07-08 review, NOT by CI. **FIXED 0.8.4** (`4bdb996`); the kappa_libs/mutation probes move into scheduled CI so breadth regressions stop relying on review. | ~~mixed~~ CLOSED | — | SOUNDNESS-LOG.md, "0.8.4 review patch" |
| ~~R20~~ | swift | **UserDefaults / Keychain `SecItem*` / Bundle resource lookups read silent-pure under the covered-module floor** (`Foundation`/`Security` in PLATFORM_MODULES vouch for everything, so a member gap is absolute — the Panache shape, Swift edition; ubiquitous iOS persistence invisible to the gate). **FIXED 2026-07-09** (`dd134e2`; all → Fs, verb-precise, twin-gated). | ~~SILENT~~ CLOSED | — | SOUNDNESS-LOG.md, swift κ batch |
| ~~R21~~ | family porcelain | the **2026-07-09 whole-project review's fail-open class**: gate surfaces converting "the gate could not run" into green — cargo-candor `policy` build-failure `\|\| true` and `guard` with no baseline ever snapshotted; java `--gate-json` unwritable → exit 0, `CANDOR_DEPS` typo silently ignored; ts MCP `candor_whatif` bad policy path + configured-but-empty policy falsy-skipped; agents `gate_reports` fail-open dead code + undisclosed observed-paths truncation. The engine-level fail-closed doctrine had never swept the OUTPUT/auxiliary channels or the shell porcelain. **FIXED 2026-07-09** (same-day wave, per repo; conformance PARTs 14–15 + wrapper CI lanes added as standing gates). | ~~fail-open~~ CLOSED | — | the 2026-07-09 review wave |

## 6. The metric (track these four; each "step forward" moves one)

1. **Cardinal-surface coverage** = % of (seam × engine) cells at 🟢 in §4. *2026-06-18: the basic-indirection
   row (6 indirections × **8** effects = 48 cross-engine-standing cells, up from 5 effects/30) is 🟢 and the gate
   is now un-foolable in strict mode (G1/G2). Most seam-class rows are 🟡 (per-engine tests, not yet in
   the cross-engine matrix), EXCEPT the rust-deep column, now fully 🟢 via standing per-engine fixtures in
   candor-rust CI: implicit-conversion (ui/implicit_conversion.rs), lazy-init + fire-and-forget +
   deferred-iterator (ui/deferred_effects.rs). Target: every closed seam → 🟢 via the matrix's SEAM axis.*
2. **Oracle coverage** = # real crates × effects under dynamic ground truth (§3 #1). *2026-06-18: grew 7→11
   crates — Net ×3 (std/minreq/ureq), Exec ×3 (duct/xshell/std), Fs ×4 (fs-err/std/walkdir/tempfile) — now
   ≥3 per syscall-distinguishable effect (Fs/Net/Exec); incl. the walkdir calibration confirmed vs the kernel
   + tempfile as an honesty probe. + 13 crates with an UNCALIBRATED honesty probe per
   effect (minreq/subprocess/fs_extra — a crate candor doesn't model, exercised for real; the strongest test).
   Rand/Clock are syscall-distinguishable but markerless/noisy (getrandom has no string arg; HashMap seeds
   getrandom) — covered by the non-syscall recall complement instead. **NOW CONTINUOUS: `realworld-oracle.yml`
   runs on every push to main + every PR (was workflow_dispatch) → kernel ground truth is a STANDING gate, a
   new silent under-report on a real crate fails CI.** And the NON-SYSCALL RECALL complement now covers the
   last 2 effects (Env, Clock — recall corpus 14→20 cases, all honest), so with the syscall oracle (Fs/Net/
   Exec) candor's effect classification is under ground-truth/known-semantics coverage for ALL 10 EFFECTS.
   Recall is also wired into realworld-oracle.yml → BOTH ground-truth methods are now continuous standing
   gates. 2026-06-18: moved the session's adversarial-sweep finds UP the evidence ladder to ground truth —
   syscall oracle 13→**14 drivers** (added `fs_writefmt`: a custom `fmt::Write` writing a marker file via
   `write!`; CI-verified `ran=1 effect=Fs candor=[Fs] certain` — the write-fmt class now KERNEL-gated, the
   strongest evidence, independent of engine logic); recall 20→**23** (seam_lazy_force/seam_thread_local/
   seam_write_fmt, all →Clock). realworld-oracle.yml run GREEN: 14 honest / 0 under-reports / 0 fabrications,
   recall 23 honest. So the systemic write-fmt shared blind spot is now caught by EXTERNAL ground truth, not
   just engine-internal fixtures. NEXT: more uncalibrated recall probes; deepen each effect's real-crate
   diversity.*
3. **Open SILENT residuals** (§5) = count by severity. *Baseline: 7 SILENT (R1–R8, mostly low). 2026-06-18:
   R1 (the only `med`) RESOLVED — empirically already covered + now standing-gated → 6 SILENT (R2–R8), all
   low/v.low. The thread_local probe briefly added R13 (med) — now FIXED same-session (`6010832`) → back to
   **6 SILENT (R2–R8), all low/v.low; no med+ open**. Target: 0 med+; lows documented-accepted.*
4. **Find-rate** = cardinal sins found per fresh adversarial round. *2026-06-18: 6 seam-class rounds each found
   ≥1; the 7th (coverage) and 8th (R1 deep implicit-conversion 6-sub-case probe) each found 0 silent; the 9th
   (rust-deep fire-forget/lazy-init/deferred-iterator probe, candor-rust `8bf9c6b`) found 1 — the lazy-init
   forcing site read pure (effectful `LazyLock` init charged to the static, never to the forcing fn). FIXED +
   gated (ui/deferred_effects.rs); the other two seams were already caught. The 10th (agents seam battery,
   candor-agents `755216a`) found 1 — named-delegation narrowing trusted a prompt mention as proof of the
   spawn set, silently dropping unmentioned-but-spawnable agents. FIXED (allowlist→sound, bare-Agent→disclosed
   Unknown) + gated (test.py). The 11th (rust-deep `thread_local!` probe) found 1 — R13, a `.with()`-forced
   thread_local read pure (effect orphaned in the macro-gen init fn); FIXED same-session (`6010832`) + gated.
   Rounds 12–13 (rust-deep derived-Clone/Once/OnceLock-named-init, then compound-assign R6) found 0 — both
   sound, gated (R6 stale for deep, may hold for scan). The 14th (rust-deep `write!` writer side) found 1 —
   R14, `fmt::Write` writer silent-pure; FIXED (`0e4bf50`) + gated. The 15th was a CROSS-ENGINE
   sweep of R14 + thread_local against candor-scan: write-fmt was ALSO silent in scan (shared blind spot,
   FIXED scan 0.5.18 `dabafd0`); thread_local already handled. The 16th extended the sweep to candor-swift:
   write-fmt's writer side was ALSO silent there (effectful `TextOutputStream` via `print(to:)`/`write(to:)`),
   FIXED swift 0.5.22 `9368311`. Convergence = sustained 0 across diverse new seams (NOT reached — 16 rounds,
   ~13 finds, all fixed). KEY LESSON reinforced: a find in one engine is a SWEEP trigger for ALL — write-fmt's
   writer side was a SYSTEMIC shared blind spot (deep+scan+swift), the exact case cross-engine agreement hides.
   The 17th finished the sweep on
   candor-java: the writer side is silent there too (4th engine — R16), but the precise fix needs receiver→
   ctor-arg escape provenance (the infra exists; CHA-blanket rejected by candor-java's precision design) and
   the idiom is rare, so it's tracked as a low SILENT residual rather than rushed. ts is N/A (no writer-sink
   idiom). SWEEP COMPLETE: write-fmt writer side assessed across ALL engines — silent in 4 (deep/scan/swift/
   java), FIXED in 3, java tracked (R16). R16 since FIXED (candor-java 0.5.40 `5f86d3e`, constructor-site
   reentry) — so the write-fmt writer-side class is now closed in ALL 4 engines. Convergence: 17 rounds,
   ~14 finds, ALL 14 fixed. Also validated on real code: PetClinic dogfood (the JVM gate works end-to-end,
   0 Unknown, caught a real cross-layer smell) + the gson InetAddress catch.*
   *2026-06-21 → 2026-07-09, the κ-coverage and porcelain eras (full prose per entry in SOUNDNESS-LOG.md;
   register entries R18–R21): real-app dogfooding found the inherited-into-project silent-pure vein and
   closed the CLASS (batches 25–27, R18); the uflexi legacy round mined batches 28–31 to a zero ledger and
   found one live silent-Net member gap (Jackson, batch 30b); the breadth invited six shipped classifier
   regressions (0.8.4 review patch, R19 — caught by review, now moving under scheduled CI); the same
   covered-module shape then surfaced in swift (UserDefaults/Keychain/Bundle, R20); and the 2026-07-09
   whole-project review opened a THIRD find category — porcelain/output-channel fail-opens (R21), plus one
   normative contradiction (AS-EFF-008's opaque case: spec text vs the conformance-pinned fail-closed
   behavior — the written contract had lagged the machine-checked one since the 0.5.15 hardening). All
   fixed; chaining + stale-baseline became conformance PARTs 14–15 the same day, and PART 14's first run
   caught candor-scan's missing empty-report ledger exemption. Convergence: STILL NOT reached — every era
   shift re-opens the find-rate, which is the epistemic frame (§1) working as designed: the instrument's
   job is to make each new era's finds cheap and standing-gated, not to declare victory.*

## 7. Roadmap (meaningful, measurable steps)

1. **Standing gates (highest leverage):** extend `conformance/gen_differential.py` from 6 indirections to the
   full seam set (each seam × effect × engine = a CI cell). Converts the 🟡 one-shot hunts to 🟢; a regression
   becomes un-shippable. *Each seam class added = a measurable step (cells turn green).*
2. **Grow the dynamic oracle (strongest evidence):** add real crates per effect to `soundness/realworld/`,
   wire `realworld-oracle.yml` to run in CI on every push. *Each crate/effect = a step on metric #2.*
3. **Eradicate SILENT residuals (§5):** R1 done (already covered); drive the remaining R2–R8 (all low/v.low) to
   zero or convert to disclosed-Unknown. *Each = a step on metric #3.*
4. **rust-deep parity + unblock its self-guard (R12):** the reference engine must carry every scan fix and
   be continuously gated.
5. **agents seam battery (R11):** run the six seam classes against the agents drift model.
6. **Convergence log:** record each adversarial round's find-rate here; a sustained zero across *diverse* new
   seams is the strongest convergence signal we can have.

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

## 8. How to read confidence today (2026-07-09)

- **Floor is solid and continuously gated:** the honesty invariant (never silent-pure where an effect is
  reached) is a standing conformance part over every engine's own report; the kernel syscall oracle +
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
  engine-level fail-closed doctrine never swept.
- **So: high and rising on the analysis core; the active frontier is κ-coverage member gaps and
  gate-surface fail-opens, both now with standing gates.** Treat any new framework's
  inherited-into-project shape and any new output/auxiliary channel as guilty until gated.

### 8.1 Round & batch index (prose in [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md))

| entry | date | engine | class | outcome |
|---|---|---|---|---|
| Java adversarial round (§8.1) | 2026-06-20 | java | ~55 synthetic fixtures, 5 mechanism families | 0 silent |
| Cross-language round (§8.2) | 2026-06-21 | java (Kotlin/Groovy) | compiler-generated dispatch | finds fixed, gated |
| κ batch 24 — Hibernate-6/Jakarta Data | 2026-06-21 | java `ed231ed` | DISCLOSED invisible → modeled Db | precision |
| κ batch 25 — Quarkus Panache | 2026-06-21 | java `cf359ce` | **SILENT-PURE sin** (inherited-into-project) | fixed + gated |
| κ batch 26 — Micronaut/Ebean/ActiveJDBC/jOOQ | 2026-06-21 | java `32229da` | **SILENT-PURE** ×4 (same vein, probed) | fixed + gated |
| κ batch 27 — modeled-base subclass, general | 2026-06-21 | java `7421301` | **SILENT-PURE** class closed | fixed + gated |
| Cross-engine vein check | 2026-06-21 | scan/ts/swift | inherited-into-project | java-specific, not shared |
| κ batch 28 — legacy-enterprise tier (JCL/…) | 2026-07-06 | java `aefca4f` | DISCLOSED → modeled | precision |
| κ batch 29 — next tier, same discipline | 2026-07-06 | java `2575683` | DISCLOSED → modeled | precision |
| κ batch 30/30b — Jackson (+ live silent-Net find) | 2026-07-06 | java `cd617cb` | **SILENT-NET** member gap | fixed + gated |
| κ batch 31 — long-tail sweep, ledger → zero | 2026-07-07 | java `17eb81d` | DISCLOSED → modeled | ledger empty |
| 0.8.4 review patch | 2026-07-08 | java `4bdb996` | **6 regressions** batches 28–31 shipped | fixed + gated |
| κ batch — UserDefaults/Keychain/Bundle | 2026-07-09 | swift `dd134e2` | **SILENT-PURE** (covered-module) | fixed + gated |
| Whole-project review (porcelain fail-opens et al.) | 2026-07-09 | all repos | fail-open gate surfaces, doc drift | fix wave, conformance PARTs 14–15 added |
