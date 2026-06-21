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

**CI action item:** the spec CI should run with `CONFORMANCE_REQUIRE_ALL=1` **once it provisions all four
toolchains** (rust+java+node+swift) — otherwise strict mode will fail on the missing ones. Until then, strict is
opt-in (local + a future all-toolchain CI job). Do NOT flip CI to strict before the toolchains are installed.

## 8. How to read confidence today (2026-06-18)

- **Floor is solid:** the honesty *invariant* (never silent-pure where an effect is reached) was verified clean
  on **13 real dep-rich projects** across all engines in the coverage round — zero silent gaps found.
- **Six seam classes closed** (key-collision, lazy-init, deferred-iterator, fire-and-forget, gate-evasion,
  implicit-conversion) + FFI + macro, each with a per-engine regression test.
- **But:** most are 🟡, not 🟢 — closed once, not yet cross-engine-standing; the strongest evidence (oracle) is
  still narrow; and there are 7 low/med SILENT residuals. So: *high and rising, not "done."* The roadmap is how
  it keeps rising.

## 8.1 Java adversarial round (2026-06-20, candor-java 0.7.8 `@d6927ff`)

A fresh Java-only soundness pass, run AFTER this session's structural changes (LB-1b thread-local
re-entrancy, `--parallel`, the GraalVM native-image + JDK-supertype index, and the `ctx()` hoists) — to
confirm none of them opened a silent gap. Two halves, both clean:

- **Synthetic adversarial sweep — no cardinal sins.** ~55 fixtures across 5 mechanism families, each an
  effect delivered via a mechanism that might slip past bytecode/CHA/κ. Every one was correctly attributed,
  honestly `Unknown` (with a precise `unknownWhy`), or honestly `invisible` — never silent-pure. Families +
  hard cases that resolved correctly: (a) dynamic invocation — MethodHandle/VarHandle/Proxy/asType/bindTo →
  honest `Unknown`; reflective-LITERAL name → `Net` (resolved); (b) modern concurrency — virtual threads,
  `newVirtualThreadPerTaskExecutor`, `CompletableFuture.supplyAsync`, parallel streams, ForkJoinPool,
  `StructuredTaskScope` (lambda effects attributed at the CREATION site); field-Runnable→`new Thread(r)`
  honestly degrades to `Unknown:task-handoff`; (c) foreign/native/process — a `native`-declared callee →
  `Unknown:native`, Panama FFM downcall → `Unknown`, all `Runtime.exec`/`ProcessBuilder`/`System.load`
  variants → `Exec`, `FileChannel.map` → `Fs`; (d) control-flow-hidden + structural — catch-only,
  finally-only (incl. nested in a switch), transitive `<clinit>`, enum-constant dispatch, sealed-record
  dispatch, default-interface-method, record compact-ctor, try-with-resources implicit `close`, CHA on an
  interface with no in-project instantiation, assert-guarded (present in bytecode); (e) newer I/O & SPI —
  JDK11 `HttpClient` send/sendAsync → `Net`, async `FileChannel`/`SocketChannel`, `Files.lines/walk` → `Fs`,
  `ServiceLoader` impl effect surfaced via the `calls` edge, `ScriptEngine.eval` → honest `Unknown`,
  `DriverManager.getConnection` → `Db`, `URL.openStream` → `Net`.
- **Real-jar dogfood — sound + honest** on three libraries never tested before: commons-net 3.11.1
  (725 fns, Net-dominant — correct for a network lib), jedis 5.2.0 (4646 fns, Net + honest Unknown smear),
  postgresql 42.7.4 (2188 fns, Fs/Net/Db/Env — correct for a JDBC driver). Effects land where expected;
  every gap is DISCLOSED (`invisible` κ-floor or `Unknown`), none silent. κ-coverage leads surfaced as
  honest `invisible` (NOT sins, the floor working): `resilience4j.*`, `commons-pool2.impl`, `org.ietf.jgss`,
  `waffle.windows.auth`, `org.osgi.framework`, `org.xml.sax` — all optional third-party / config namespaces.
- **`org.xml.sax` lead investigated → no missed I/O.** `DocumentBuilder`/`SAXParser`/`XMLReader.parse` and
  `Transformer.transform` are ALREADY classified `Unknown` (Classifier.java ~68-71 — the sound disclosure of
  an XML-parse-from-systemId, also the XXE/SSRF sink). The residual `org.xml.sax` `invisible` is only the
  pure factory/config members (`XMLReaderFactory.createXMLReader`, `InputSource`, `setFeature`); postgresql's
  use is in-memory/caller-visible. No κ rule added — that would be coverage-chasing pure calls against the
  "model specific effectful members for precision, not chase coverage" principle.

- **Strongest tier — runtime ground truth (DONE, not a TODO).** Java already has a dynamic oracle (better
  than the Rust strace harness: it has per-method STACK TRACES and runs on macOS, being JVM-level not an OS
  tracer): `soundness/dynamic/` = a JFR oracle (`jfr_diff.py`, Fs/Net via `jdk.{File,Socket}{Read,Write}`
  events) + a bytecode leaf-instrumenting agent (`agent/`, Exec/Db/Env/Clock/Rand/Log) + `corpus.sh` that
  runs both over a corpus and fails on any runtime-observed effect candor's static report neither predicts
  nor discloses. RAN it this round: extended the corpus with `async-netfs` (real loopback Net in a VIRTUAL
  THREAD + real Fs in a CompletableFuture + a parallel stream) and `async-exec` (real `/bin/echo` Exec via a
  Thread and a CompletableFuture). Result: **7 entries CLEAN, 0 NEW model gaps** — the kernel/JVM actually
  saw the Net/Fs/Exec and candor predicted every one, so the lambda/task effect attribution the synthetic
  sweep checked statically is now confirmed against RUNTIME ground truth. The lone gap is the documented,
  allowlisted abstract-`java.io.Reader` boundary (a `parse(Reader)` whose concrete `FileReader` is only
  known at the caller) — accepted, not a regression.

Net: the cardinal-sin floor held on Java across synthetic, real-world, AND runtime-ground-truth inputs,
including over all of this session's new code paths (byte-identity + the native-vs-jar parity gate prove
those produce identical reports). The standard MECHANISM families are covered (the synthetic/runtime axes
find-rate 0), and what candor can't resolve it discloses. NB the earlier "κ veins mined out" phrasing was
about mechanism coverage on the tested corpus — LIBRARY/framework κ-coverage is NOT exhausted: dogfooding a
new framework still surfaces unmodeled effectful members (disclosed `invisible`, never silent), e.g. §8.3's
Hibernate-6/Jakarta-Data vein found on a Quarkus app. Evidence ladder, all three tiers now
exercised: synthetic = controlled (known effect → checked report); dogfood = real-world breadth; JFR+agent
corpus = runtime ground truth (the strongest, which catches even a shared blind spot). Remaining oracle
growth = more corpus programs / effects, not a missing capability.

## 8.2 Cross-language adversarial round (2026-06-21, candor-java)

Every prior sweep used JAVA fixtures; candor analyzes BYTECODE from any JVM language, so the
under-explored axis is whether language-specific effect-delivery (which compiles to bytecode shapes a
Java-centric analyzer never saw in a Java fixture) slips the floor. Swept all three claimed languages —
**no cardinal sin in any**:

- **Kotlin (kotlinc 2.4.0) — precise.** The existing lane (`soundness/run_kotlin.sh`, 16 forms) passed;
  then an ADVERSARIAL sweep of 22 more mechanisms all attributed the threaded `Net` leaf: stdlib —
  `lazy{}`, `sequence{}` (a lazy-iterator coroutine), the scope functions (let/run/apply/also/with),
  inline + non-inline HOFs, `object :` expressions, `companion object { init }`, custom delegated
  properties (`by`), the `invoke` operator, extension functions, receiver-HOFs; and **coroutines**
  (kotlinx-coroutines 1.9.0) — `runBlocking`, `launch`, `async`, `withContext(Dispatchers.IO)`, a
  `suspend` chain `s1→s2→leaf` (each suspend fn individually got `Net`, traced THROUGH the CPS
  state-machine bytecode), and `Flow { … }.collect`. Kotlin's hardest shapes (CPS continuations,
  synthetic SuspendLambda classes, lazy iterators) all trace soundly.
- **Groovy (groovyc) — honest Unknown.** Dynamic dispatch (the default) compiles every call — even
  `new Socket(...)` — to a runtime callsite, so candor cannot statically see the type → it discloses
  `Unknown` for `leaf`/`viaDynamic`/`viaClosure`/`viaEach`/`viaCompileStatic`. Never silent-pure: the
  sound floor for a genuinely-dynamic language is exactly Unknown (a precision limit inherent to Groovy,
  not a soundness gap).

Verdict: candor's bytecode analysis is language-shape-robust — PRECISE where the bytecode is statically
resolvable (Java, Kotlin incl. coroutines), HONEST `Unknown` where it's genuinely dynamic (Groovy). The
cardinal-sin floor holds across the JVM-language surface, not just Java. Find-rate on this NEW axis = 0.

## 8.3 Real-app dogfood → κ batch 24 (Hibernate-6 / Jakarta Data, 2026-06-21, candor-java 0.7.9 `ed231ed`)

The Bet-1 case-study work ran candor on five real third-party JVM projects (two Spring apps, a Kotlin app,
a Quarkus app, the gson library). Four resolved cleanly. The Quarkus **Hibernate ORM / Jakarta Data
quickstart** (deliberately non-Spring) exposed a κ-COVERAGE gap — correctly DISCLOSED, not a cardinal sin:
its `FruitResource` endpoints read `inferred=[]` + `invisible=[org.hibernate, org.hibernate.query, …]` with
the κ receipt naming the packages + call counts. candor modeled the classic `org.hibernate.Session`/`Query`
API and `jakarta.persistence.*`, but NOT the Hibernate-6 / Jakarta-Data generation the quickstart's
generated repositories drive (`StatelessSession`, the split `SelectionQuery`/`MutationQuery`, the
`jakarta.data.repository.*` pattern). So `Db` never landed — the persistence was honestly `invisible`
(κ-floor working), but the architecture gate couldn't see it.

**Mined (precise, verb-gated; terminals → Db, builders stay pure):** `StatelessSession` CRUD terminals
(insert/update/upsert/delete +*Multiple, get/getMultiple/getIdentifier/refresh/fetch); `SelectionQuery`
result terminals + `MutationQuery.executeUpdate`; and `isJakartaDataRepoBase` promoting project interfaces
extending `jakarta.data.repository.*Repository` into `repoTypes` (mirrors `isSpringDataRepoBase`).
DELIBERATELY did NOT κ-cover `org.hibernate.query.criteria`/`.specification` — those pure AST builders stay
honestly `invisible` (the κ discipline: model the effectful member, never blanket a namespace silent-pure),
so the post-fix Quarkus report still discloses them. Gates: byte-identity IDENTICAL on pc/jsoup/gson;
`./gradlew test` green; `soundness/run.sh` 40/0 + all probes OK; `kappa_libs_probe` +4 Db terminal anchors
+1 builder-purity anti-fab anchor (442 leaves / 164 pure neighbours). Quarkus: `Db` lands on all five
endpoints, 100% contained.

Lesson for this tracker: the synthetic/runtime find-rate-0 measures MECHANISM soundness (does an effect
delivered via shape X get attributed); it does NOT measure LIBRARY κ-completeness (is every effectful member
of every framework enumerated). The latter is open-ended and best driven by dogfooding real apps — each new
framework can surface a vein, always disclosed `invisible` first (never silent), then optionally mined for
precision. Hibernate was the dominant-ORM instance; the same loop applies to the next unmodeled framework.

**κ batch 25 — Quarkus Panache → Db (2026-06-21, candor-java post-0.7.9 `cf359ce`). A genuine SILENT-PURE
cardinal sin, NOT just an `invisible` gap.** Continuing the dogfood thread to Quarkus's *other* (and dominant)
persistence — Panache active-record (`Fruit.listAll()`, `f.persist()`) + `PanacheRepository` — found it read
SILENT-PURE (the methods were ABSENT from the report, no `invisible`, no `Unknown`), so the architecture gate
was blind to ALL DB access in a Panache app. Why silent (vs Jakarta Data's honest `invisible`): the call-site
owner is the PROJECT entity/repo (`Fruit.listAll()` emits owner `app/Fruit`), not an external package — so the
κ-floor invisible disclosure (which fires on EXTERNAL owners) never triggered, and CHA found no project body →
dropped to pure. This is the dangerous shape: an inherited-from-unmodeled-external method called via a project
subtype receiver. MINED: repository promotion (isPanacheRepoBase → repoTypes), active-record call-site rule
(PANACHE_ENTITY_VERBS + `extendsPanacheEntity` via transSupers, with the no-fabrication override guard), and
PanacheQuery terminals (classify). Verb+hierarchy-gated → a lookalike non-Panache class stays pure (fab probe
OK). Gated: byte-identity pc/jsoup/gson, full suite, soundness 40/0, conformance. LESSON: the "always disclosed
`invisible` first" claim above has an EXCEPTION — when the unmodeled-framework method is INHERITED into a
project type (so the call owner is a project class), it reads silent-pure, not invisible. That shape is the one
to watch when dogfooding the next framework (active-record / base-class-mixin APIs, not just repository/builder
APIs whose calls keep an external owner).

**κ batch 26 — the inherited-into-project vein class swept (2026-06-21, candor-java post-0.7.9 `32229da`).**
Rather than wait for the next framework, probed the persistence ecosystem for batch 25's shape directly (an
external stub base + a project subtype + the inherited call, scan only the project). Spring Data was the
passing CONTROL (Db); MyBatis mapper interfaces correctly disclose `Unknown` (not a vein). FOUR more confirmed
SILENT-PURE and mined: **Micronaut Data** (repository — `isMicronautDataRepoBase` → repoTypes promotion),
**Ebean** (`io.ebean.Model`), **ActiveJDBC** (`org.javalite.activejdbc.Model`), **jOOQ** (`org.jooq.impl.DAOImpl`)
— the latter three via a new `AR_DB_BASES` registry (base internal name → its DB verb set) + `inheritsArDbVerb`
(checks owner + supertypes; per-base verb gating; the no-fab override guard). Verb+hierarchy-gated, fab probe
OK (lookalike non-framework save()/findAll() stays pure). So the inherited-into-project shape is now covered
for the major JVM persistence frameworks (Spring/Jakarta Data/Panache/Micronaut Data repositories +
Hibernate/JPA + Panache/Ebean/ActiveJDBC active-record + jOOQ DAO). The general METHOD (external-stub probe of
any base-class API) is the reusable instrument for the next framework.

**κ batch 27 — the inherited-into-project vein, GENERAL fix for classify-MODELED bases (2026-06-21, candor-java
post-0.7.9 `7421301`).** Batches 24–26 covered bases candor does NOT model at the leaf (via repoTypes/AR_DB_BASES
registries). The complementary case: a project class subclasses a base candor DOES model at the leaf, and calls
an inherited method — still silent-pure, because the call owner is the project subclass (no rule) and classify
was never re-tried against the external supertype. Found via Testcontainers (`class MyContainer extends
GenericContainer` then `c.start()` read pure though `GenericContainer.start` is modeled Exec); also hits
non-test cases (`extends java.io.FileInputStream` → inherited `read()`). FIX (Candor.analyze, classify site):
when classify(owner) is null AND owner is a project class with no concrete body of its own (not overridden) and
no project super provides one, re-run classify against each EXTERNAL supertype — the exact method the JVM
dispatches to. No new fabrication (classify already vouches for the external leaf; an override wins). Byte-identity
HELD on pc/jsoup/gson (the broad fix fires only on the narrow subclass-a-modeled-type shape). NON-SIN finding
recorded for completeness: declared-on-interface HTTP clients (Retrofit `@GET`, Micronaut `@Client`) read
`Unknown` (DISCLOSED, not silent) — a precision opportunity (model → Net like Feign), NOT a cardinal sin.
**Status: the inherited-into-project silent-pure vein CLASS is now closed** across modeled + unmodeled bases.

**CROSS-ENGINE verification — the vein was JAVA-SPECIFIC, NOT a shared blind spot (2026-06-21).** The
tracker's #1 risk is a blind spot SHARED across engines (cross-engine agreement hides it), so after closing
the inherited-into-project vein in candor-java I probed the others for the same shape. RESULT — not shared:
- **candor-ts** (the clearest analog — TS active-record ORMs): `class User extends BaseEntity` (TypeORM) →
  `user.save()`/`User.find()`, and Sequelize `Model.create()` → all read **`Unknown`** (`callback:u.save` etc.),
  DISCLOSED, never silent-pure (control `fs.readFileSync` → Fs confirms the harness). Its AST model treats an
  unresolved method call as `callback:Unknown` — it never CHA-resolves-to-nothing-then-pure.
- **candor-scan (Rust)**: an unresolved external/trait-default method call → **`Unknown`** (`callback:unresolved
  call`). Same safe floor.
- **candor-swift**: structurally N/A — Core Data / SwiftData persist via the *context* (`context.save()`), not
  an effectful method inherited into the entity subclass.
So candor-java was the OUTLIER: its CHA could resolve an inherited-from-unmodeled-external call to no project
body and drop to pure, where the AST/syntactic engines disclose `Unknown`. The dangerous SHARED case does not
exist here. (PRECISION note, not a sin: candor-ts/scan report these as `Unknown` — modeling the ORMs → Db/Net,
the analog of the Java persistence work, would sharpen them, but they are footnote engines and it is not a
cardinal-sin fix.)
