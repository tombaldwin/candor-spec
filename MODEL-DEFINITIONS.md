# The disclosure model — numbered definitions (extract)

**This is an extract of an unpublished manuscript, not the manuscript.** PAPER3 (*The Disclosure Model: A
Formal Reference*) is kept outside every repo. Tom ruled on 2026-10-10 that its **definitions** may live
here — *"Just the defs in the spec pls"* — so that the model's citations of them in `lean/`, `reference/`
and `LEAN-CHECKER-PLAN.md` point at text a reviewer can open and `git diff`. **Only numbered Definitions
are here.** No lemma, theorem, proposition, corollary, remark or escape; no proofs, motivation, evaluation
or commentary — the one exception is the amendment note to Definitions 33–35 listed below. A citation of a
Lemma, Theorem, Proposition, Corollary, Remark or Escape still points at the manuscript.

**Source snapshot.** `PAPER3.md`, 1044 lines, sha256
`037239dc1e57d1b0163c79a9a4b96be7b8b0d2a544222f279ac41a3f3b15d959`. Every item below is preceded by an
HTML comment giving its PAPER3 line range in that snapshot, and the text between the comment and the next
comment is **verbatim** — no item is edited, elided or annotated. Re-extract from a new snapshot by those
ranges; do not edit an item here in place, because a hand-edited item is a citation target that no longer
matches its source.

**Which definitions, and why these.** All the Definitions of PAPER3 **§6–§7** (the policy layer — the
question Tom answered), plus every earlier Definition that a citation in `lean/`, `reference/` or
`LEAN-CHECKER-PLAN.md` names, plus Definition 25 ((A1)), which the definitions and the cited results lean
on. `scripts/model-citations.py` (a doc-gate) fails if one of those files cites a Definition this extract
does not carry; it does not check citations of other kinds of item.

| PAPER3 | definitions included (lines) |
|---|---|
| §1 | Definitions 1–7 (35–36, 38–42, 69–81, 83–85, 87–88, 90–94, 96–97) |
| §2 | Definition 12 (184–185) |
| §3 | Definitions 16 (210–212), 16a (227–230), 16b (232–254), 16c (256–258), 17 (265–269), 18 (271–280), 19 (282–291), 19a (293–300), 20 (302–305), 21 (447–465), 22 (467–471) |
| §4 | Definitions 24 (504–513), 25 (515–516), 26 (518–527), 27 (529–542), 28 (544–546) |
| §6 | Definitions 29 (685–689), 30 (691–693), 31 (701–703), 32 (705–706), 33 (726–729), 34 (731–734), 35 (736–739), and **the amendment note to Definitions 33–35** (741–748) |
| §7 | Definition 36 (765–766) |

32 definitions. **Amended definitions are given as amended:** Definitions 2, 32, 33, 34 and 35 were amended in
PAPER3 and the text below is the amended text. The amendment note for 33–35 is kept because
`LEAN-CHECKER-PLAN.md` cites it (P3:726-750) and it carries the executed counterexample to the old
Definition 35; the amendment notes for Definitions 2 and 32 are not.

**Referenced by an included definition but NOT extracted:** Definitions 15 and 20b (named in Definitions
22 and 21). The symbols `F`, `call`, `unres`, `direct`, `Φ`, `inferred`, `S(f)`, `D(f)` and `μ` are fixed
by PAPER3 Definitions 8, 8a, 8b and 9–11 (§2), not extracted. Definition 6's pointer "see §6.1b" names no
section of PAPER3. The included definitions also mention Lemma 2, Theorem 1, Corollary 1, Propositions 1,
3, 4, 4a, 4b, 5, 6 and Remarks 1, 4a, 5, 6 — none of which is here.

---

## §1  The disclosure lattice

<!-- PAPER3 lines 35–36: Definition 1 -->
> **Definition 1 (Capability effects).** `E` is a finite set of **capability effects** — coarse, named
> world-interactions: `E = {Net, Fs, Exec, Db, Env, Clock, Llm, …}`. `E` is not a heap read/write partition.

<!-- PAPER3 lines 38–42: Definition 2 -->
> **Definition 2 (Refinement preorder).** `⊑ₑ` is a preorder on `E` in which an effect refines a base channel
> **only when every occurrence of it is an occurrence of that channel**: `Llm ⊑ₑ Net`. All other effects are
> incomparable — in particular `Db ⋢ₑ Net`. The preorder is flat among the base channels, so for `Fs`,
> `Exec`, `Env`, `Clock`, `Db` — which have no refinements — every predicate below coincides with plain
> membership.

<!-- PAPER3 lines 69–81: Definition 3 -->
> **Definition 3 (Covering; observation side).** An observed effect `e` is **covered by** `S ⊆ E` iff
> `e ⊑ₑ e'` for some `e' ∈ S`. So an observed `Llm` is covered by a declared `Net`. An observed `Db` is
> **not** covered by a declared `Net` (Definition 2, amended); whether an uncovered observation is a
> *violation* is Definition 22's question, which additionally requires `D(f) = ∅`.
> **Scope of this reading.** Containments between an *observed* effect set and a *declared* one — those in
> `obs(f) ⊆ S(f)`, `charged(f) ⊆ S(f)`, H (Definition 21), Definition 22 and Theorem 1 — are read modulo
> `⊑ₑ` in this sense, written `⊆` and `⊄`. **Every other containment in this document is plain subset**,
> including the components of the product order (Definition 7) and every step in Propositions 1, 3 and
> Lemma 2. The distinction is not stylistic: modulo `⊑ₑ` the order on `𝒫(E)` is not antisymmetric
> (`{Net}` and `{Net, Llm}` become equivalent), so Proposition 1's lattice structure and Lemma 2's
> upward-closure both **fail** under a blanket reading — Proposition 6 is precisely a proof of that failure.
> Plain-`⊆` steps compose with modulo-`⊑ₑ` steps in the sound direction, since `⊑ₑ` is a preorder and plain
> containment implies the modulo form.

<!-- PAPER3 lines 83–85: Definition 4 -->
> **Definition 4 (Firing; gate side).** A denial of `e` **fires** on `S` iff `S` contains a refinement of `e`:
> `∃ e' ∈ S. e' ⊑ₑ e`. So `deny Net` fires on a determined `{Llm}`. It does **not** fire on `{Db}`
> (Definition 2, amended): a database effect is not a network effect.

<!-- PAPER3 lines 87–88: Definition 5 -->
> **Definition 5 (Disclosure reasons).** `R` is a finite set of **disclosure reasons** — the causes an
> analyzer can fail to resolve: `reflect`, `dispatch`, `indirect`, `native`, `unresolved`, `setup`, ….

<!-- PAPER3 lines 90–94: Definition 6 -->
> **Definition 6 (Effect signature).** An **effect signature** is a pair `(S, D)` with `S ⊆ E` the
> **determined** effects and `D ⊆ R` the **disclosure set** — the reasons the determination is incomplete.
> `D = ∅` means the signature is *sound-complete*; `D ≠ ∅` means it carries `Unknown`, tagged with exactly the
> reasons `D`. The bare `Unknown` marker is the pair `(∅, {r})` **for some `r ∈ R`** — the reason set is what
> carries the marker, so no signature represents an `Unknown` with no reason (see §6.1b).

<!-- PAPER3 lines 96–97: Definition 7 -->
> **Definition 7 (Product order).** `(S₁, D₁) ⊑ (S₂, D₂)` iff `S₁ ⊆ S₂` and `D₁ ⊆ D₂` (plain subset in both
> components). Write `L = 𝒫(E) × 𝒫(R)` for the carrier.

---

## §2  Signatures and the transitive rule

<!-- PAPER3 lines 184–185: Definition 12 -->
> **Definition 12 (Omission convention).** Functions with `inferred(f) = (∅, ∅)` are **omitted** from the
> report; report completeness is keyed on the convention **absent ⇒ (∅, ∅)**.

---

## §3  Postures, charging, and the honesty invariant

<!-- PAPER3 lines 210–212: Definition 16 -->
> **Definition 16 (Fabrication).** A **fabrication** is growth of `S` beyond what any run performs, or of `D` beyond the unresolved sites that actually exist. It is
> a precision property; the model gives it no invariant. It lies outside H (Definition 21), is uncovered by
> Theorem 1, and is absent from Corollary 1's case split.

<!-- PAPER3 lines 227–230: Definition 16a -->
> **Definition 16a (Program state).** Fix a finite set `T` of thread identifiers. A **state** is a map
> `σ : T ⇀ Frame*` assigning to each live thread a finite stack of frames, innermost first. A **frame** is a
> pair `⟨f, ι⟩` of a function `f ∈ F ∪ Ext` (`Ext` the functions outside the report's claimed scope) and a
> unique **activation identifier** `ι`, so two activations of the same `f` are distinct frames.

<!-- PAPER3 lines 232–254: Definition 16b -->
> **Definition 16b (Run).** A **run** is a finite sequence of states (Definition 16a) `σ₀ → σ₁ → ⋯ → σₙ`
> where each step is
> labelled by exactly one of:
> - `call(t, ⟨g, ι⟩)` — push `⟨g, ι⟩` onto thread `t`'s stack, with `ι` fresh;
> - `ret(t)` — pop thread `t`'s stack;
> - `spawn(t, t′, ⟨g, ι⟩)` — create thread `t′` with initial stack `[⟨g, ι⟩]`;
> - `issue(t, e)` — thread `t` performs a world-interaction of effect class `e ∈ E`;
> - `exit(t)` — thread `t` terminates, its stack being empty.
>
> `T` is fixed in advance and `spawn` marks a thread live rather than creating it; `ret` and `issue` are
> defined only for a thread with a non-empty stack. `spawn(t, t′, ⟨g, ι⟩)` records the spawning **thread**;
> where the spawning *frame* matters it is the innermost frame of `σ(t)` at that step.
>
> **Scope limit (deliberate).** This system models *direct* thread creation only. **Submission of a task to a
> pre-existing worker** — a thread pool — has no label here: the submitting frame performs an ordinary `call`
> into library code, and the task body later runs on a worker whose stack never contained the submitter. That
> is not an omission to be repaired by adding a label; it is the *reason* the cross-thread boundary of
> Definition 19 exists (Remark 6, Table 1 row 2). Any extension that made the handoff an edge of this system
> would also have to say what `charged` means across it, which is precisely the open design question.
>
> An **executed** function is one appearing in some frame of some state. An **executed call** `f → g` is a
> `call(t, ⟨g, ι⟩)` step whose target is pushed directly onto a frame of `f`. `f`'s activation `⟨f, ι⟩` is
> **live** in every state between its `call` and its matching `ret`.

<!-- PAPER3 lines 256–258: Definition 16c -->
> **Definition 16c (Issue site and enclosing chain).** For an `issue(t, e)` step at state `σᵢ`, its
> **enclosing chain** is the stack `σᵢ(t)` read innermost-first. The chain is finite and linearly ordered, and
> every frame in it is live at `σᵢ`.

<!-- PAPER3 lines 265–269: Definition 17 -->
> **Definition 17 (Coverage classes).** Fix a run. Each executed frame is exactly one of: **analyzed** — in
> the report's claimed scope, carrying a signature; **modelled** — covered-but-unanalyzed, a library primitive
> the effect model resolves; or **uncovered** — never modelled, its reach carried by the **coverage envelope**
> (a per-function `uncovered`-function receipt, a third disclosure channel that is deliberately *not* a member
> of `R`). Write **covered = analyzed ∪ modelled**.

<!-- PAPER3 lines 271–280: Definition 18 -->
> **Definition 18 (Charging convention; `obs`).** An effect is **directly charged** to the **nearest
> *analyzed* frame** on
> the stack when it fires. Concretely, `obs(f) ⊆ E` is every effect issued by `f`'s own body, **plus** every
> effect issued by *modelled* code reached from `f` with **no intervening analyzed frame and through no
> intervening uncovered frame**: charging passes *through* modelled frames to the nearest analyzed ancestor,
> and an **uncovered** frame **terminates** the chain, its reach charged to no analyzed frame.
> The accounting is three-way, not two: a **modelled** target folds into `direct(f).S` — the load (A2) carries;
> an **unresolvable site** contributes a reason to `D(f)` — (A1); an **uncovered** callee is carried by the
> coverage envelope, entering neither `S` nor `D`. An effect issued by an *analyzed* callee `g` is `obs` of
> `g`, not of `f`; it re-enters `f`'s account only transitively, through Definition 20.

<!-- PAPER3 lines 282–291: Definition 19 -->
> **Definition 19 (Per-thread dynamic extent).** `f`'s **dynamic extent** is the union, over `f`'s activations
> (Definition 16a), of the intervals of the run during which that activation is live on its *own thread's*
> stack. An effect issued on a *different* thread that `f` spawned or handed a task to is **outside** `f`'s
> extent.
>
> Note the two relations are distinct and must not be conflated: an effect is **directly charged** to exactly
> one frame (Definition 18, Proposition 4), whereas the **transitively-charged** set `charged(f)`
> (Definition 20) collects the `obs` of every analyzed frame reached from `f` — so an effect deep in `f`'s
> covered-reached tree is directly charged to its own nearest encloser and appears in `charged(f)` for every
> analyzed ancestor `f`.

<!-- PAPER3 lines 293–300: Definition 19a -->
> **Definition 19a (Covered-reached).** An effect issue event is **covered-reached from `f`** iff its enclosing
> chain contains `f` and no *uncovered* frame lies between the issuing frame and `f`. An analyzed frame `h` is
> **covered-reached from `f`** iff `h` lies in `f`'s chain with **no *uncovered* frame** between them — i.e.
> every intervening frame is *covered* (analyzed or modelled), which is the relation Theorem 1(i) and
> Definition 20 quantify over. (The stricter *modelled-only* relation is a different object: it is the
> single-hop collapse of Definition 27, used to state (A3), and must not be substituted here — doing so
> would reduce Theorem 1(ii) to depth one and make 'transitive soundness' non-transitive.) Both clauses
> are reflexive in `f`.

<!-- PAPER3 lines 302–305: Definition 20 -->
> **Definition 20 (Transitively-charged set).** "Reached from `f`" is **reflexive** — `f` is reached from
> itself — so `obs(f) ⊆ charged(f)`, which is what makes the `h = f` instance of Theorem 1(ii) yield H.
> `charged(f) := ⋃ { obs(h) : h analyzed, reached from f through
> covered frames, executed within f's dynamic extent }`.

<!-- PAPER3 lines 447–465: Definition 21 -->
> **Definition 21 (Honesty invariant H).** For every executed **analyzed** `f` (Definition 17) with
> `inferred(f) = (S, D)`, *scoped to the
> effects `f` reaches through the covered set*: **if `D = ∅` then `obs(f) ⊆ S`.** An effect `f` reaches *only*
> through an **uncovered** callee is excluded from H's scope; **given frontier disclosure (Definition 20b)** —
> which Proposition 4b derives through analyzed code — Proposition 4a makes that exclusion a partition *of issue events* rather than a stipulation — every excluded
> event is envelope-carried and named in the report. The partition is of **events, never of `E`**: at the level
> of effect classes `charged(f)` and `envCarried(f)` overlap (Remark 4a(i)), so H does bind a class that `f`
> also reaches through an uncovered package. Without frontier disclosure the excluded event may be disclosed
> nowhere at all (Remark 4a(ii)).
>
> The restriction to **analyzed** frames is not cosmetic. A *modelled* frame carries no signature and is
> therefore absent from the report, so Definition 12's convention would give it `(∅, ∅)`; unrestricted, H
> would then assert `obs(f) ⊆ ∅` of a library primitive that genuinely issues an effect, and would be false
> for every program. Modelled frames are accounted for by charging *through* them (Definition 18), never by
> H binding them directly.
> Write **H⁺** for the **transitive strengthening** of H, which is the form the oracle checks — **`D(f) ≠ ∅` or `charged(f) ⊆ S(f)`**, which
> is Theorem 1(ii) per frame and of which the `obs` form is the `h = f` special case. It is written as a
> disjunction rather than by unioning a pseudo-effect `{Unknown}` into a subset of `E`, so as to keep
> `Unknown` off the effect lattice (Remark 1). When `D ≠ ∅`, H is **vacuous**.

<!-- PAPER3 lines 467–471: Definition 22 -->
> **Definition 22 (Violation).** A **violation** is an executed **analyzed** `f` with `D(f) = ∅` and
> `obs(f) ⊄ S(f)`, read
> modulo `⊑ₑ` (Definition 3): an observed `Llm` against a declared `Net` is *not* a violation; an observed `Net`
> against a declared `{Db}` is, and so — since the Definition 2 amendment — is an observed `Db` against a
> declared `Net`. A violation is a false all-clear (Definition 15); H says there are none.

---

## §4  Antecedents and the conditional soundness theorem

<!-- PAPER3 lines 504–513: Definition 24 -->
> **Definition 24 ((A0) enumeration completeness).** Every function whose body executes in the run is
> **covered** (analyzed or modelled) or carried by the coverage envelope, *and* every function of the report's
> **claimed scope** — the code the analysis purports to have analyzed, as opposed to a modelled library or an
> envelope-disclosed dependency — is in the analyzed set. (A0) constrains the claimed-scope enumeration, not
> the modelled or uncovered frames. By Definition 12 a function silently dropped from the claimed scope is
> indistinguishable from a provably-pure one, so discharging (A0) requires a completeness manifest at
> **function granularity**; a `{count, digest}` manifest is not that granularity. (A0) is the one antecedent a
> runtime observer cannot *localize*, and cannot falsify from the report alone: the dropped frame leaves no
> analyzed frame at which to witness a violation. Given a function-granularity manifest an observer that sees
> a body-executing function absent from it has falsified (A0) — it simply cannot say which frame to blame.

<!-- PAPER3 lines 515–516: Definition 25 -->
> **Definition 25 ((A1) disclosure of sites).** Every unresolved primitive or dispatch site in `f`'s own body
> contributes a reason to `Dᵈ(f)`.

<!-- PAPER3 lines 518–527: Definition 26 -->
> **Definition 26 ((A2) direct soundness).** For every executed `f` **with `Dᵈ(f) = ∅`**,
> `obs(f) ⊆ direct(f).S`.
> The restriction to own-body-complete frames is the correct quantification, not a hedge: stated over *every*
> executed `f`, (A2) would be falsified by a perfectly honest engine, since a correctly-disclosed unresolved
> site in `f`'s body whose runtime dispatch reaches a modelled effect puts that effect in `obs(f)` while
> `direct(f).S` rightly excludes it — the disclosure, not the effect set, carries that reach. The restricted
> form is exactly what Theorem 1 consumes.
> A second load: because `obs(f)` charges effects reached through chains of *modelled* frames (Definition 18),
> the library-effect model must be **transitively closed** over such chains — a modelled `m₁ → m₂ → Net` must
> put `Net` in `direct(f).S`, not merely detect a single per-call model.

<!-- PAPER3 lines 529–542: Definition 27 -->
> **Definition 27 ((A3) call-graph soundness modulo disclosure).** For every executed call `f → g` between
> analyzed functions — "executed call" as given by Definition 16b, lifted to the collapse below — either
> `(f,g) ∈ call` or a reason is contributed to `D(f)`.
> The lift is the **nearest-analyzed-ancestor collapse**: for an executed call step `call(t, ⟨g, ι⟩)` with `g`
> analyzed, `f` is the innermost analyzed frame strictly below `⟨g, ι⟩` in `σ(t)` (Definition 16c), provided
> every frame between them is **modelled**. The collapse therefore passes through modelled frames *only*. An **uncovered**
> intermediate frame **terminates** the collapse — the reach beyond it is the coverage envelope's, not
> required of `f`.
> The collapse is load-bearing. On the *raw* stack, (A3) would be vacuously satisfiable for an analyzed,
> effectful callback `g` invoked *through* a modelled higher-order library (`f` calls `lib.each(g)`, with
> `lib.each` modelled as invoking its argument): the runtime edges `f → lib` and `lib → g` are not literally
> between analyzed functions, so (A3) would not require `f` to account for `g` — yet `g`'s effect is charged
> within `f`'s extent and Theorem 1(ii) demands it appear in `f`'s signature. Under the collapse, `f → g` is a
> required edge.

<!-- PAPER3 lines 544–546: Definition 28 -->
> **Definition 28 ((A4) report fidelity).** The emitted report presents the computed least fixpoint —
> `inferred = lfp(Φ)` over the engine's *own* computed `(call, direct, unres)`. Theorem 1's containments are
> over the computed fixpoint; (A4) is the bridge to the report a consumer, and Corollary 1, actually read.

---

## §6  Policy semantics

<!-- PAPER3 lines 685–689: Definition 29 -->
> **Definition 29 (Layer; policy).** A `<layer>` names a set of functions. A **policy** `P` is a set of rules,
> each a verb applied to a layer. `Reject_{P,f}(S,D)` holds iff some verb of `P` whose layer contains `f`
> rejects `(S,D)`; i.e. `Reject_{P,f} = ⋃_{v applicable to f} Rejectᵥ`. The index on `f` is necessary:
> applicability is a property of the function, not of `(S,D)`, and `allow` acts by removing `f` from a rule's
> scope (Proposition 5). Upward-closure (Lemma 2) is asserted per fixed `f`.

<!-- PAPER3 lines 691–693: Definition 30 -->
> **Definition 30 (`deny e <layer>`).** `Reject_{deny e}(S,D) ⇔ ∃ e' ∈ S. e' ⊑ₑ e` (Definition 4). A non-empty
> `D` does **not** fire it — the analysis cannot assert `e` — but is surfaced as an advisory: the gate stays
> green *with a disclosure*, never a silent pass.

<!-- PAPER3 lines 701–703: Definition 31 -->
> **Definition 31 (`deny e Unknown[c₁,…,cₖ] <layer>`).** The reason-scoped strict gate:
> `Reject(S,D) ⇔ (∃ e' ∈ S. e' ⊑ₑ e) ∨ D ∩ C ≠ ∅`, where `C = {c₁,…,cₖ}`. Bare `deny e Unknown` is `C = R`.
> Its guarantee is scoped by Remark 5.

<!-- PAPER3 lines 705–706: Definition 32 -->
> **Definition 32 (`pure <layer>`).** `Reject_{pure}(S,D) ⇔ S ≠ ∅`: a determined effect fails it; a
> **disclosure alone does not**.

<!-- PAPER3 lines 726–729: Definition 33 -->
> **Definition 33 (`forbid A -> B`).** **Not a predicate over `(S,D)` at all.** It is a *call-graph
> dependency* rule: it fires when a function in layer `A` calls one in layer `B`, irrespective of effects —
> a wholly pure call fires it, and its diagnostic carries an empty effect set. Its carrier is the edge set
> `→`, not the signature lattice `L`.

<!-- PAPER3 lines 731–734: Definition 34 -->
> **Definition 34 (`allow <E> <literal>…`).** **A fail-closed certification predicate, not a scope
> exception.** It certifies that a function's *literal surface* for effect `E` (its hosts, paths, commands,
> tables) lies within an allowlist, and it **rejects** when the surface is absent or uncertifiable — an
> opaque or computed literal fails it. Its carrier includes the literal surfaces, which are **outside `L`**.

<!-- PAPER3 lines 736–739: Definition 35 -->
> **Definition 35 (`unknown-ratchet`).** Against a *fixed* baseline `D_b`, over the functions **not already
> disclosed at baseline**: a function that carries no `Unknown` at baseline and acquires one is rejected. A
> function already disclosed at baseline is **grandfathered** and does not re-fire when its reason set
> grows. A baseline bump is a separate, deliberate act, not a signature change.

<!-- PAPER3 lines 741–748: Definitions 33–35, the amendment note -->
*Amended, all three.* These previously read: `forbid` as `φₑ`-shaped; `allow` as "an exception … not a
rejection predicate"; and the ratchet as `Reject ⇔ D ⊄ D_b`. None described the shipped verb. `forbid` is
AS-EFF-009, a dependency rule with no effect predicate. `allow` is AS-EFF-008 and is *rejection-capable* and
*fail-closed* — the direction that matters, since its purpose is refusing to certify what it cannot see.
And the shipped ratchet grandfathers: `D_b = {dispatch}`, `D = {dispatch, reflect}` is a **rejection under
Definition 35 as written and a pass in every implementation** — an executed counterexample, and the one
place among the three where the old definition was *stricter than* rather than merely *different from* the
deployment.

---

## §7  Monotone denial

<!-- PAPER3 lines 765–766: Definition 36 -->
> **Definition 36 (Atomic gate predicates).** `φₑ(S,D) := [ ∃ e' ∈ S. e' ⊑ₑ e ]` and
> `ψ_C(S,D) := [ D ∩ C ≠ ∅ ]`, for `e ∈ E` and `C ⊆ R`.
