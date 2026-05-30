# candor — formal semantics of the effect analysis

This document specifies *what candor computes* and *under what guarantees*. [SPEC.md](SPEC.md) fixes
the **interface** (effect vocabulary, report schema, diagnostic codes, modes); this fixes the
**analysis**: the effect lattice, how a call site resolves, the transitive fixpoint, cross-crate
composition, the conformance predicates, and the soundness/precision claims — stated honestly,
including the two places soundness is *assumed* rather than proven.

The model is language-agnostic; §9 maps it onto an implementation (the Rust reference impl).

---

## 1. Effect domain

Fix a finite **effect vocabulary**

> 𝔼 = { Net, Fs, Db, Exec, Env, Clock, Ipc, Log, Rand, Clipboard }.

Adjoin a distinguished element **Unknown ∉ 𝔼** meaning *"this effect set may be incomplete — some
dispatch could not be resolved."* `Unknown` is **not** an effect (you can never hold a capability for
it); it is an honesty marker (see §7, §8).

The analysis works over the **powerset lattice**

> 𝓛 = ( 𝒫(𝔼 ∪ {Unknown}), ⊆ ),  join ⊔ = ∪,  meet ⊓ = ∩,  ⊥ = ∅,  ⊤ = 𝔼 ∪ {Unknown}.

𝓛 is finite, of height |𝔼| + 1 = 11. "More effects / more uncertainty" is *higher* in the order; a
**sound** result *over-approximates* (sits above) the truth.

## 2. Programs

A program under analysis is a set of **functions** `F` (the compilation's named, body-bearing items:
functions, methods, and const/static initializers). Each `f ∈ F` has:

- a **body** `body(f)` — a finite set of **call sites**;
- a **signature** `sig(f)` — used only by the conformance layer (§6).

Functions split into **local** (defined in the crate currently being analyzed) and **external**
(defined elsewhere — dependencies, the standard library, or *sibling crates of the same project*,
§5b). Effects performed in a closure are attributed to the nearest enclosing function in `F` (closures
are not in `F`); equivalently, a closure's call sites belong to `body(f)` of that enclosing `f`.

## 3. The classifier

The **classifier** is a partial function

> κ : Callee ⇀ 𝔼

mapping a *resolved* callee (identified by its crate and fully-qualified path) to **at most one**
effect. `κ(t) = e` asserts "calling `t` performs `e`"; `κ(t)` **undefined** means *candor has no rule
for `t`* and treats it as performing no direct effect.

κ obeys the **I/O-boundary principle**: it tags the *dispatch/execution* operation, never the pure
builders that construct a request — e.g. `reqwest::…::send ↦ Net` while the request-builder methods
are undefined; `Collection::find_one ↦ Db` while `Collection::name` is undefined. κ is a *curated*
function: completeness over real-world effectful APIs is a goal, not a theorem (see §8, caveat C1).

## 4. Call-site resolution

For a call site `c ∈ body(f)`, resolution yields two things:

- **contrib(c) ∈ 𝒫(𝔼 ∪ {Unknown})** — effects charged *directly* to `f` at this site;
- **edges(c) ⊆ F** — local callees whose effects propagate to `f` transitively (§5).

The judgment is the **first** matching rule below (read `t` = the syntactic callee, `X` = the
cross-crate oracle of §5b, `impls(T,m)` = the local impls of trait method `m` of trait `T`):

```
(CLASSIFY)   t external,  κ(t) = e
             ────────────────────────────────         contrib = {e},  edges = ∅

(CROSS)      t external,  κ(t) undefined,  ĥ(t) ∈ dom(X)
             ──────────────────────────────────────    contrib = X(ĥ(t)),  edges = ∅

(DEVIRT)     c is a method call on a CONCRETE receiver,
             statically resolvable to one impl t′ that is local
             ──────────────────────────────────────    contrib = ∅,  edges = { t′ }

(LOCAL)      t is a local function (direct call)
             ──────────────────────────────────         contrib = ∅,  edges = { t }

(CHA)        c dispatches over a LOCAL trait T (dyn or generic),
             not devirtualizable
             ──────────────────────────────────         contrib = ∅,  edges = impls(T, m)

(EXEMPT)     c dispatches over a conventionally-pure std trait
             (Display, Debug, Error, ToString, Clone, Eq/Ord, …)
             ──────────────────────────────────         contrib = ∅,  edges = ∅

(UNKNOWN)    c is a fn-pointer / closure call, OR dispatch over a
             NON-local, non-exempt trait that cannot be resolved
             ──────────────────────────────────         contrib = { Unknown },  edges = ∅

(OPAQUE)     t external,  κ(t) undefined,  ĥ(t) ∉ dom(X)
             ──────────────────────────────────         contrib = ∅,  edges = ∅
```

Notes.
- **(DEVIRT) before (CHA).** When the receiver type is known, the call dispatches to exactly one
  impl; using that single impl instead of *every* impl is the precision difference between (DEVIRT)
  and (CHA). (CHA) is the sound fallback for genuinely dynamic/generic dispatch.
- **(CHA) is an over-approximation:** it unions *all* impls' effects, some of which the call could
  never select. This is sound (never misses) but imprecise; (DEVIRT) recovers the precision when it
  can.
- **(EXEMPT)** prevents the trust marker from flooding: dispatch over std traits that are
  conventionally effect-free (formatting, equality, cloning) does *not* raise `Unknown`. The exempt
  set is curated tightly and excludes traits where I/O can hide (`Iterator`, `Fn*`, `Drop`,
  `io::Write`). This is caveat **C2** of §8.
- **(OPAQUE)** is the curated-classifier assumption: an external callee candor has no rule for and
  no cross-crate report for contributes *nothing*. This is caveat **C1** of §8 — the principal
  source of unsoundness.

Define, for `f ∈ F`:

> **D(f)** = ⊔_{c ∈ body(f)} contrib(c)        (direct effects — performed in f's own body)
> **calls(f)** = ⋃_{c ∈ body(f)} edges(c)       (local call-graph successors)

## 5. Transitive effects (the report's `inferred`)

### 5a. The fixpoint

The **inferred** effect set `I : F → 𝒫(𝔼 ∪ {Unknown})` is the **least solution** of

> **I(f) = D(f) ⊔ ⊔_{g ∈ calls(f)} I(g)**     for all f ∈ F.

The right-hand side is a monotone operator `Φ : (F → 𝓛) → (F → 𝓛)` on the finite product lattice
`F → 𝓛`. By Knaster–Tarski its least fixpoint exists and equals `⊔_n Φⁿ(λf.∅)` (Kleene iteration),
reached in finitely many steps (§7).

`I(f)` is what a report entry publishes as `inferred`; `D(f)` is published as `direct`. The
`unresolved` flag of an entry is `Unknown ∈ I(f)`.

### 5b. Cross-crate composition

candor analyzes one crate at a time, but a program spans crates (a `bin` over its `lib`, a workspace
member over a sibling). Effects must cross that boundary, so each analyzed crate K **emits** its
result and a dependent reads it.

Let `ĥ : F → H` assign every function a **stable cross-crate identity** `ĥ(f)` — a value identical
whether `f` is viewed from its home crate or from a dependent (a content hash of its definition path;
*not* its surface path, which dependents may see reexport-shortened). When candor analyzes crate K,
it builds the **oracle**

> X  =  ⋃ { ĥ(g) ↦ I_{K′}(g)  :  K′ a dependency of K,  g ∈ F_{K′} }

from the reports K′ already emitted. Rule **(CROSS)** then makes a call from K into K′ inherit the
callee's *already-transitive* `I_{K′}(g)`. Because reports are emitted **bottom-up** (a dependency is
analyzed, and writes its report, before its dependents), `X` is available when needed. For a
trait-method call across the boundary, `ĥ` is taken of the **devirtualized** impl (the home crate
keyed its report by the impl, not the trait method).

This composition is itself an instance of (CROSS): the analysis is *modular* — `I_K` is computed using
only `D` of K's own functions plus the *published* `I` of its dependencies.

## 6. Conformance (the modes)

The conformance layer compares what a function *performs* against what its signature *grants*. Let
`declared(f) ⊆ 𝔼` be the effects `sig(f)` confers — via **capability tokens** (a parameter whose type
names an effect, e.g. `&Fs`, or an unforgeable cap-std handle), or, in a dependency-injection idiom,
the effects the injected collaborators of `f`'s enclosing unit provide. Let `Ambient ⊆ 𝔼` be the
ambient-authority effects (`𝔼 \ {Log}`), and `B(f)` a previously-saved baseline value of `I(f)`.

The diagnostics are exactly these predicates:

| code | fires when | meaning |
|---|---|---|
| **AS-EFF-001** | `I(f) \ declared(f) \ {Unknown} ≠ ∅` (and `f` is not the entry point) | performs an effect it doesn't declare |
| **AS-EFF-002** | `declared(f) \ I(f) ≠ ∅` | declares a capability it never uses |
| **AS-EFF-003** | `Unknown ∈ I(f)` | effect set not provably complete; cannot certify |
| **AS-EFF-004** | `D(f) ∩ Ambient ≠ ∅` | reaches for ambient authority *directly* (vs. receiving it) |
| **AS-EFF-005** | `I(f) \ B(f) ≠ ∅` | an existing function gained an effect vs. the baseline |

`Unknown` is excluded from AS-EFF-001 deliberately — an unresolved call is not a *declarable* effect;
it is AS-EFF-003's concern. AS-EFF-005 fires only for functions present in `B` (regressions in
existing code), never for new functions.

## 7. Properties

**(P1) Termination.** Kleene iteration of `Φ` converges in at most `|F| · (|𝔼|+1)` round-trips: each
step that changes anything raises some `I(f)` strictly in the height-`(|𝔼|+1)` lattice 𝓛, and there
are `|F|` functions.

**(P2) Monotonicity / determinism.** `Φ` is monotone, so the least fixpoint is unique and independent
of iteration order. Adding a call edge or an effect can only *grow* `I` — never shrink it.

**(P3) Conditional soundness.** Let `R(f)` be the *true* set of effects `f` can perform at runtime.
Then

> **R(f) ⊆ I(f)**     *provided* the following two assumptions hold along everything `f` transitively reaches:

- every real effectful primitive is recognized — i.e. for each runtime effect there is a call whose
  callee is in `dom(κ)` (or is a recognized cross-crate function);
- every dispatch is either resolved to its possible targets ((LOCAL)/(DEVIRT)/(CHA)) or charged
  `Unknown` ((UNKNOWN)).

Under those assumptions candor never *silently* omits an effect: it either reports the effect or
reports `Unknown`. The assumptions are exactly the **two honesty caveats** of §8.

**(P4) Precision is best-effort.** `I(f)` may strictly over-approximate `R(f)`: (CHA) unions impls a
call can't select, and whole-*crate* classifier rules tag pure items in an otherwise-effectful crate.
Over-reporting is the *safe* direction for an auditor (it never hides danger) but is wrong for exact
per-function annotation; (DEVIRT) and verb-precise κ rules tighten it.

## 8. Where soundness is *assumed*, not proven

candor is honest about being conditionally sound. (P3) rests on two assumptions that are engineering
commitments, not theorems:

- **C1 — the classifier is curated.** κ is a hand-built allowlist. An effectful call whose callee is
  not in `dom(κ)` and has no cross-crate report falls under **(OPAQUE)** and contributes *nothing* —
  a **false negative** with no `Unknown` raised. Mitigations: keep κ broad (run on real code; let
  reality correct it — see CLASSIFIER.md §5), let projects extend κ, and surface the crates a build
  actually called that κ doesn't recognize (a *coverage* signal) so the gap is visible, not silent.
- **C2 — the pure-std-trait exemption.** **(EXEMPT)** assumes the listed std traits are effect-free.
  If a type implemented one of them with a hidden effect, candor would miss it. The set is curated
  tightly to traits where I/O cannot conventionally hide.

These are the price of running on real code without per-call proof obligations. The design choice
throughout is: when forced to choose, **over-report (P4) or mark `Unknown` (UNKNOWN) — never silently
under-report** — and make any residual blind spot *visible* (C1's coverage signal) rather than silent.

## 9. Realization (the Rust reference implementation)

| model element | implementation |
|---|---|
| `F`, `body(f)`, the call sites | HIR of the crate; a `dylint` `LateLintPass` visiting every expression |
| κ | `classify` (+ project rules via `CANDOR_CONFIG`) |
| (CLASSIFY/CROSS/DEVIRT/LOCAL/CHA/EXEMPT/UNKNOWN/OPAQUE) | `resolve_callee`, `trait_of_assoc`, `Instance::try_resolve` (DEVIRT), `cha_targets` (CHA), `is_pure_std_trait` (EXEMPT) |
| `D(f)`, `calls(f)` | the per-function `direct` and `calls` maps |
| the fixpoint `I` | the worklist in `check_crate_post` |
| `ĥ` | `DefPathHash` (stable across crates); emitted as each report entry's `hash` field |
| `X` (cross-crate oracle) | dependency crates' emitted JSON reports, loaded by hash |
| `declared(f)` | capability-token parameter types read from the signature (`&Fs`, cap-std handles) |
| AS-EFF-00x | the conformance/no-ambient/baseline modes |

A second implementation (JVM, ASM bytecode) realizes the *same* model with `declared` read from
dependency-injection wiring rather than token parameters — confirming the semantics is language-
agnostic and the engine is what's bespoke.

## 10. Summary

candor computes the least fixpoint of a monotone effect-propagation operator over a finite powerset
lattice: each function's **transitive** effect set, built from a curated classifier at the leaves,
resolved/over-approximated dispatch in the middle, and a stable-hash-keyed oracle across crate
boundaries — with an explicit `Unknown` wherever resolution fails, so the result is **conditionally
sound** (P3) under two stated, *visible* assumptions (C1, C2) and **safe by construction** (it
over-reports or says `Unknown`, never silently under-reports). The conformance modes are then simple
set predicates (§6) over `I`, `D`, `declared`, and a baseline.
