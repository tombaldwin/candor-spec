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
| R11 | agents | only key-collision seam-hunted; other seams unchecked | UNCHECKED | med | run the seam battery against the agents model |
| R12 | rust-deep | CI self-guard ICE (nightly-2026-04-16) blocks continuous self-gating | infra | med | nightly bump / rustc_private migration (parked) |

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
   gates. NEXT: more uncalibrated recall probes (Env/Clock crates candor doesn't model); deepen each effect's
   real-crate diversity.*
3. **Open SILENT residuals** (§5) = count by severity. *Baseline: 7 SILENT (R1–R8, mostly low). 2026-06-18:
   R1 (the only `med`) RESOLVED — empirically already covered + now standing-gated → **6 SILENT (R2–R8), all
   low/v.low**. Target: 0 med+; lows documented-accepted.*
4. **Find-rate** = cardinal sins found per fresh adversarial round. *2026-06-18: 6 seam-class rounds each found
   ≥1; the 7th (coverage) and 8th (R1 deep implicit-conversion 6-sub-case probe) each found 0 silent; the 9th
   (rust-deep fire-forget/lazy-init/deferred-iterator probe, candor-rust `8bf9c6b`) found 1 — the lazy-init
   forcing site read pure (effectful `LazyLock` init charged to the static, never to the forcing fn). FIXED +
   gated (ui/deferred_effects.rs); the other two seams were already caught. Convergence = sustained 0 across
   diverse new seams (not yet reached — the deep engine still yields finds when probed at new seams).*

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
