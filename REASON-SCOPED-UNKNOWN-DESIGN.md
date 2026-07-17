# Reason-scoped `Unknown` policies — `deny E Unknown[class]` ⟨SHIPPED four-way 2026-07-17⟩

> **Status:** implemented in all four engines (java reference, rust, ts, swift) with a shared closed
> `ReasonClass` set {reflect, dispatch, indirect, native, unresolved, setup}, the `dynamic`/`*` aliases,
> and the A2 under-gating lint. The reason CLASS propagates transitively along the call graph at gate-eval
> time (the report's `unknownWhy` stays direct-only), so `deny E Unknown[reflect]` fires on a caller that
> inherits a reflect-caused `Unknown` from a callee — a transitive-reason under-gating gap found + fixed
> during the port. Pinned four-way in conformance PART 4 (parsepolicy `unknownClasses`).

Make the *reason* a policy first-class citizen: a gate can deny an effect that is either determined **or**
undetermined-for-a-reason-class-you-care-about, instead of the all-or-nothing `deny E Unknown`.

## The finding (referee pass 2026-07-16, industry angle — `~/candor-paper/REFEREE-REPORTS.md`)

`deny E Unknown <scope>` fires on `E` OR on *any* `Unknown` in scope. On DI-heavy Spring/Guice code,
reflection-laden enterprise Java, or dynamically-dispatched TypeScript, `Unknown` is common and largely
benign — so the strict gate becomes effectively **deny-all** and teams **permanently disable it**. §8.4 of
the write-up already concedes the mechanism ("if an adversary can make everything `Unknown`, `deny E
Unknown` becomes unusable — you don't even need an adversary, a normal Spring codebase does it"). The
result: the one gate that enforces "refuse effects I cannot even rule out" is the first thing switched off,
on exactly the code that most needs it. The blind spot is real; the *policy's inability to distinguish
kinds of blind spot* is the defect.

## What already exists (audited 2026-07-16, all four engines)

- candor **already reason-tags every `Unknown`**: the `unknownWhy` (rust `unknown_why`) field carries raw
  reasons — `dispatch:<sym>`, `reflect:eval`, `reflect:vm`, `reflect:require`, `reflect-metadata`,
  `native:<sym>`, `callback:<sym>`, `closure param leaked`, `unresolved`, and setup markers
  (`missing-config`, `no-tsconfig`, no-`node_modules`). Emitted four-way; pinned by the conformance
  `unknownWhy vocabulary` PART.
- The policy engine already has the **`Unknown`-aware gate**: `deny E Unknown <scope>` (AS-EFF, §6.2), the
  `unverified` verb that enumerates `Unknown`-carrying passers of a `pure`/`deny` layer, and `.candor/config`
  policy wiring.
- **Nothing quantifies over the reason.** `deny E Unknown` treats `reflect:eval` (a genuine dynamic hole) and
  `missing-config` (the tool isn't wired up) identically. The raw `unknownWhy` strings are consumer-visible
  but engine-specific and unstable — not a policy surface.

The data is on the wire; only the **policy grammar + a stable reason-class vocabulary** are missing.

## The design

### 1. A fixed reason-class vocabulary (§6, NEW — the policy-facing normalization of `unknownWhy`)

Raw `unknownWhy` strings are engine- and idiom-specific (`reflect:vm` is a JS construct; `native:` is FFI).
The policy surface needs a **small, fixed, cross-engine set of classes** (like the §1 effect vocabulary),
onto which each engine maps its raw reasons:

| class | meaning | raw `unknownWhy` that maps to it (audited 2026-07-16) |
|---|---|---|
| `reflect` | reflection / metaprogramming | ts `reflect:eval`/`reflect:vm`/`reflect:require`/`reflect:accessor:*`/`reflect_apply`/`reflect-metadata`; swift `reflecting`/`dynamicMemberLookup`; (java/rust: see finding 2) |
| `dispatch` | unresolved virtual/dynamic dispatch candor declined to resolve | rust/ts/java `dispatch:*`; rust `ambiguous:same-name local defs` |
| `indirect` | callback / closure / function-value indirection | all `callback:*` (incl. ts `callback:opaque-iterable:*`, `callback_recv`; swift `callback:computed`); ts `closure` |
| `native` | FFI / native boundary | rust `native:extern fn`; (JNI / C-interop / Node native addons as engines add them) |
| `unresolved` | a generic unresolvable call/import not in the above | ts/java/swift `unresolved`; any raw reason matching no pinned pattern |
| `setup` | **the analysis is not wired up** (fixable, not a real dynamic hole) | see finding 1 — this class must be actively PRODUCED; it is not emitted today |

`reflect`/`dispatch`/`indirect`/`native`/`unresolved` are **genuine** blind spots (the code really is
dynamic). `setup` is categorically different — it means candor couldn't *see* the code, and the fix is to
configure the scan, not to change the code. This distinction is the second half of the design (§3).

**Two findings from the four-engine `unknownWhy` audit (2026-07-16) — both are reference-implementation
prerequisites, not free:**

1. **`setup` is not emitted as an `unknownWhy` today** — it is a scan-time *warning channel*
   (missing-tsconfig / no-`node_modules` / classpath), so functions that go `Unknown` because the scan is
   mis-configured are currently tagged **`unresolved`**, not distinguishable from genuine unresolved holes.
   The setup/genuine split (§3) therefore requires a NEW per-function emission: when the scan detects it is
   mis-configured, the resulting `Unknown`s must carry a `setup`-class reason. Until an engine does this,
   its setup-holes fall into `unresolved` — which is **safe** (still gated by `dynamic`/`*`), just not yet
   *separable* for tolerance. So `setup` tolerance is opt-in AND opt-in-per-engine-as-it-lands.
2. **The reflection class is emitted unevenly** — ts is rich (`reflect:*`), swift has `reflecting`/
   `dynamicMemberLookup`, but **rust and java do not emit a `reflect` reason at all** (a `Class.forName`+
   `invoke` hole currently reads `dispatch`/`unresolved` in java). So `deny E Unknown[reflect]` would MISS
   reflection on rust/java until they emit a `reflect`-mappable reason. This is the A3 four-way risk made
   concrete: **the reference implementation must bring every engine's reflection constructs under the
   `reflect` class**, or the class is unsound cross-engine. Conformance must pin a reflection fixture in ALL
   four engines mapping to `reflect`.

The six classes are a **fixed, closed, spec-normative set** (like the §1 effect vocabulary). The mapping
`raw unknownWhy → class` is **also normative**: the spec pins, per class, the raw-reason patterns that map to
it (the "maps from" column, made exhaustive in §6.2), so the same construct classes identically in every
engine — otherwise `deny E Unknown[reflect]` would mean different things per engine and break the four-way
contract. A raw reason matching no pinned pattern maps to **`unresolved`** (conservative — it stays in scope
of any `dynamic`/`*` policy), never silently to a tolerated class. The raw `unknownWhy` string stays in the
report for human/debug use, unchanged; the class is its normative projection.

### 2. Reason-scoped policy grammar (§6.2, NEW — additive, back-compatible)

Extend the `deny … Unknown` rule with an optional class filter:

```
deny <E> Unknown[<class>,<class>,…] <scope>     # fire on E, OR on an Unknown whose class ∈ the set
deny <E> Unknown <scope>                        # unchanged: fire on E or ANY Unknown  ≡  Unknown[*]
```

- **`deny Net Unknown[reflect,dispatch,indirect,native,unresolved] domain`** — fail on a determined `Net`,
  or on an undetermined reach through any *genuine* blind spot, but **tolerate** a `setup`-class `Unknown`.
  This is the usable strict gate; the family of genuine classes has the alias `dynamic` (§4), so a policy
  writes `deny Net Unknown[dynamic] domain`.
- **`unresolved` MUST be included in any conservative scope** (and `dynamic` includes it). It is the
  catch-all for a raw reason the engine did not classify (§1) — omitting it would silently tolerate exactly
  the holes an engine couldn't name, an under-gating trap. A policy that lists specific classes *without*
  `unresolved` (e.g. `Unknown[reflect]`) is a deliberately narrow gate and SHOULD be flagged by a
  policy-lint as potentially under-gating, not silently accepted.
- **`deny Net Unknown domain`** stays exactly today's semantics (`Unknown[*]`, all classes incl. `setup`) —
  a pre-existing policy is byte-identical, so this rung breaks nothing.
- **`pure <scope>` stays strict this rung** — it fails on *any* `Unknown` (all classes, including `setup`),
  as today. A `pure` layer claims *provable* purity, so tolerating an unresolved hole there would contradict
  the verb's meaning; reason-scoping is a `deny`-side feature only for now.
- The gate verdict (`--gate-json`) reports, per violation, the `effects` and — when the trigger was an
  `Unknown` — **all** reason-classes present on the function (not just one), so a multi-reason function's
  verdict is unambiguous and a consumer can see every reason the strict gate bit.

### 3. The setup/genuine split (the fatigue fix — where `setup` is handled)

`setup`-class `Unknown` is the "tool isn't wired up" fatigue vector (the referee's week-two-uninstall). It
must be handled **without violating disclosure** (the blind spot is real — candor genuinely can't see the
code) and **without silently weakening the gate**. Three rules:

1. **`setup` is still emitted and still disclosed.** Nothing is dropped; the honesty contract is intact.
2. **`Unknown[*]` (bare `deny E Unknown`) keeps including `setup`** — the conservative default is unchanged,
   so soundness-by-default holds. Narrowing is opt-in (§2).
3. **A loud scan-time setup diagnostic.** When `setup`-class `Unknown` is present, the scan emits a
   first-class remediation line (stderr, and surfaced by `candor doctor`): *"N functions are Unknown only
   because the scan isn't fully configured — wire up `<tsconfig / classpath / npm install>`; your gate is
   failing on unconfigured analysis, not real blind spots."* This routes the fixable fraction to a **setup
   task**, not a policy decision — so a team narrows to `Unknown[reflect,native,…]` *and* fixes their config,
   instead of disabling the gate.

The net: a team can run a strict gate that bites on genuine dynamism, tolerates benign indirection, and is
*told exactly what to configure* to shrink the rest — the deny-all trap dissolved, disclosure preserved.

### 4. Reusable class aliases + `unverified`/`blindspots` integration

- **Scoping is always explicit in the rule — a config key MUST NOT silently narrow bare `deny E Unknown`.**
  A distant `.candor/config` that changed what `deny E Unknown` means would be a *silent gate-off* (the §4
  cardinal-sin posture: a policy reader could not tell what the rule denies without also reading config).
  Instead, config may define a **named class alias** that a rule references *explicitly*, so the narrowing is
  visible at the rule: `.candor/config` `unknown-alias dynamic = reflect,dispatch,indirect,native,unresolved`
  → the policy writes `deny Net Unknown[dynamic] domain`. The alias is a spelling convenience, not a hidden
  default; bare `deny E Unknown` is always `Unknown[*]`, everywhere, regardless of config.
- `unverified` and `blindspots` gain a `--class <class,…>` filter and group their output by reason class, so
  an author sees "12 `reflect` holes, 40 `setup` holes" and acts on each pile differently. Feeds the
  `Unknown`-rate metric (the sibling `[P1]` backlog item).

### 5. What this rung is NOT

- **Not a new effect or a report-schema change to what's disclosed** — the reasons are already emitted; this
  adds a *stable class projection* and a *policy filter* over them.
- **Not a weakening of `deny E Unknown`** — bare form is unchanged (`Unknown[*]`); narrowing is explicit and
  opt-in, so soundness-by-default is preserved.
- **Not fabrication** — an unrecognized raw reason maps to `unresolved` (kept in scope of `Unknown[*]`), never
  silently to a tolerated class.

## Conformance

A new PART pins reason-scoped verdicts four-way. Fixtures: a fn Unknown via a `dispatch:*`/`callback:*`
reach (both emitted uniformly today), a fn Unknown via **reflection** (`Class.forName`+invoke / `eval` /
`reflecting` — the construct differs, the class must not), and a determined `Net`. Assert, every engine:
- `deny Net Unknown[dispatch] <scope>` → fires on the dispatch-Unknown fn, **not** an `indirect`/`unresolved`
  one (exit 1; verdict names the reason-classes present).
- **`deny Net Unknown[reflect] <scope>` → fires on the reflection fn in ALL FOUR engines** — this is the pin
  that forces finding 2's emission work; a reflection construct that reads `dispatch`/`unresolved` in rust or
  java fails this and is a bug, not an accepted band.
- `deny Net Unknown <scope>` (bare) → fires on **every** Unknown fn (unchanged `Unknown[*]` semantics).
- the `raw unknownWhy → class` map agrees across engines (the normative table, §1).
- **setup fixture (added when the class lands, per finding 1):** a fn Unknown *only* because the scan is
  mis-configured is tagged `setup`; `deny E Unknown[dynamic]` tolerates it, bare `Unknown[*]` still bites it.

## Sequencing (the audit changed this from "add grammar" to "add grammar + fill emission gaps")

The four-engine `unknownWhy` audit (§1) shows the rung is **not** purely additive plumbing — the classes are
emitted unevenly. Honest phases:
1. **Grammar + normative map + the uniformly-emitted classes** (`dispatch`, `indirect`, `unresolved`) —
   shippable across all four engines immediately; delivers most of the deny-all-relief value.
2. **`reflect` parity** — bring rust and java reflection constructs under the `reflect` class (they read
   `dispatch`/`unresolved` today); the conformance reflection fixture is the gate.
3. **`native` parity** — as engines emit an FFI/native reason (rust has `native:`; java JNI / ts native
   addons / swift C-interop to follow).
4. **`setup` emission + separation** — the per-function `setup` tag + the scan-time diagnostic (§3).
Until a phase lands for an engine, that engine's holes fall into `unresolved` — **safe** (still gated by
`dynamic`/`*`), just not yet separable. So the floor can rise on phase 1; later phases are per-engine raises.

## Versioning

**Tier-2 additive** (§6.2 policy-DSL grammar + the fixed reason-class vocabulary + normative map; a pre-rung
policy and gate verdict are byte-identical because bare `Unknown` is unchanged) → a floor rung on the ladder.
Java-leadable (the reference engine). The floor rises when phase 1 lands four-way; the emission-parity phases
(2–4) are additive per-engine raises that widen which classes can be *separated*, never changing bare
semantics.
