# The disclosure-completeness gate — "sound modulo disclosure", made checkable ⟨proposed⟩

Prove, per engine, that **every way a call edge or effect site can arise is either resolved into the graph
or disclosed as `Unknown`** — so a silently-dropped edge (a latent false all-clear) cannot exist for any
enumerated kind. The static, by-construction complement to the dynamic honesty oracle.

## The finding (from formalizing the honesty invariant — HONEST-STATIC-ANALYSIS paper §3.4)

The honesty invariant `H` (a sound-complete signature `(S, ∅)` contains everything a function does at
runtime) holds under three antecedents, two of which the write-up calls *"checkable per engine"* but candor
does **not** mechanize:

- **(a)** every unresolved site/edge contributes its reason to the disclosure set `D` (i.e. emits an
  `unknownWhy`), and
- **(c)** the call graph is sound **modulo `D`** — every real call edge is in `call` **or** is a disclosed
  unresolved edge.

Antecedent **(c) is where a false all-clear lives**: a real call edge that is *neither* modelled *nor*
disclosed silently drops the callee's effects, so a genuinely-effectful function reads as pure `(∅, ∅)`.
A new dynamic-language feature, a new bytecode shape, or a new framework idiom that the graph builder skips
*and* forgets to disclose is a latent cardinal sin that no current test would catch.

**The java battery (2026-07-17) already earned its keep** — one fixture per edge kind, each with a `Net`
effect reachable *only* through that construct, asserting the entry method is never silently pure:

- Every kind (direct, reflection, callback/method-ref, native, virtual dispatch) **resolves-or-discloses** —
  no silent `(∅, ∅)`. Reflection discloses `Unknown` with `reflect:*` reasons (`Class.forName`, `Method.invoke`),
  so the older audit note that *"java emits no `reflect` reason"* is **stale** for spec 0.18 — java tags it.
- It surfaced a real **transitive-reason under-gating bug** (found+fixed same day): the `Unknown` *effect*
  propagates along call edges but the `unknownWhy` *reason* was direct-only, so a caller inheriting `Unknown`
  from a reflect-caused callee carried no reason-class. A `deny E Unknown[reflect]` at the caller then
  defaulted to `unresolved`, did **not** fire, and let a reflection-caused `Unknown` slip the gate — the
  cardinal sin at the *policy* layer. Fixed by propagating the reason CLASS transitively at gate-eval time
  (mirroring `literalFixpoint`; the report's direct `unknownWhy` is unchanged), matching the paper's `(S,D)`
  join where `D` is componentwise-unioned over callees. Regression-pinned in `ReasonScopedPolicyTest`.

## What already exists (audited 2026-07-16)

- The graph builders resolve most edges and emit an `unknownWhy` at the edges they decline (§4 `unknownWhy`
  vocabulary; `dispatch:` / `reflect:*` / `callback:*` / `native:*` / `unresolved` / …). The **SPEC §2.2
  callgraph** records every analyzed function (pure leaves included).
- The honesty **oracle** (RQ1, prototype) checks (a)/(c) *dynamically* — it catches an escape if a corpus
  program exercises the dropped edge.
- **What's missing:** a *static, by-construction* check that (a)+(c) hold for **every edge/site KIND** — not
  just the ones a corpus happened to run. The oracle is existential (it finds an escape if executed); this
  gate is universal-over-kinds (it proves the class cannot arise). They are complements.

## The design

### 1. Enumerate the edge/site kinds (the closed battery)

The soundness of `(∅, ∅)` rests on: for every construct that can introduce a call edge or an effect site,
the engine either **resolves** it (adds the edge to `call` / the effect to `S`) or **discloses** it (emits an
`unknownWhy` → `D`). The kinds, per representation (the union is the spec-normative battery; each engine
maps its idioms onto it):

| kind | resolve-or-disclose examples |
|---|---|
| direct / static call | resolved |
| virtual / interface dispatch | resolved to impls, or → `dispatch` |
| reflection / metaprogramming | resolved (const target) or → `reflect` (`Class.forName`+invoke, `eval`, selectors, macros) |
| function-value indirection | resolved (visible target) or → `indirect` (callback/closure/fn-pointer stored & later called) |
| native / FFI boundary | → `native` (JNI, `extern`, node addon, C-interop) |
| dynamic import / require | resolved or → `reflect`/`unresolved` (`import(expr)`, `require(var)`) |
| framework / DI wiring | resolved (single impl / explicit binding) or → `dispatch` (profile/conditional/plugin) |
| invokedynamic / lambda metafactory | resolved (lambda body) or → `dispatch` |
| async / task handoff | resolved (spawned target) or → `indirect` |
| dynamic host / non-literal target | resolved (const-anchored / literal-head) or → the `Net`/… site stays bare with a `host?` disclosure |
| implicit / operator-driven effect | resolved or → `unresolved` |

### 2. The gate: a completeness battery, one fixture per kind, per engine

For each kind, a fixture that provably *has* an effect reachable only through that construct. Assert, per
engine, the **disjunction**: the reachable effect is either **in the report** (resolved — the edge made it
into `call`/`S`) **or** the site carries an **`unknownWhy`** of the expected class (disclosed — it entered
`D`). The **failure condition is the silent third case**: the effect is absent from the report *and* no
`unknownWhy` was emitted — a dropped edge, a false `(∅, ∅)`. This is the disclosure-completeness gate;
running it green *is* mechanized evidence for antecedents (a)+(c) over the enumerated kinds.

This differs from the existing seam/corpus probes (which look for *specific* silent-pure veins after the
fact): it is a **systematic, kind-indexed** check that no *category* of edge is silently dropped — the
universal quantifier the oracle's existential probing can't supply.

### 3. Complementarity with the honesty oracle (the paper's static+dynamic story)

- The **oracle** (RQ1) is *sound-for-finding* but *coverage-bounded*: it catches a dropped edge only if a
  corpus run exercises it. Existential.
- The **disclosure-completeness gate** is *coverage-free* but *kind-bounded*: it proves no *enumerated* kind
  drops silently, on hand-built fixtures, regardless of any corpus. Universal-over-kinds.
- Together they bound the false-all-clear surface from both sides: a violation must be an **unenumerated
  edge kind** (missed by the gate) that **is executed** (caught by the oracle) — the gate shrinks the space
  the oracle must cover, and a new gap in one is a prompt to extend the other. This is candor's defense-in-
  depth (§4.4 of the paper) with a static leg added; the gate is the mechanized form of the "(a) checkable
  per engine" claim §3.4 makes.

### 4. What this is NOT

- **Not a proof of soundness** — it proves resolve-or-disclose for the *enumerated* kinds only; an
  unforeseen kind is still possible (and is exactly what the oracle + adversarial probing hunt). It converts
  "we believe every edge is resolved-or-disclosed" into "we *check* it for every kind we know of."
- **Not a new effect or report field** — it exercises the existing graph + `unknownWhy` emission.
- **Not the seam/corpus probes** — those are ad-hoc vein hunts; this is a systematic kind battery.

## Conformance

A new PART pins the battery four-way: for each edge/site kind, every available engine must
resolve-or-disclose (never silently drop). A kind an engine cannot even *exhibit* (a Swift-only construct in
rust) is an accepted representational band; a kind an engine exhibits but silently drops is a **DIVERGE**,
not a band. This PART is where the audit's found gaps become red-until-fixed (e.g. reflection must map to a
`reflect`-class disclosure, closing finding 2).

## Versioning

Tier-2 / internal-soundness: it adds no wire surface — it pins that the *existing* graph + `unknownWhy`
emission is complete over the kind battery. Best shipped as a standing gate (like the candor-java
`mutation_probe` meta-soundness check) + a conformance PART, not a floor rung. It also **strengthens the
paper**: a green disclosure-completeness gate is static evidence for §3.4 antecedents (a)/(c), reported
alongside RQ1's dynamic oracle.
