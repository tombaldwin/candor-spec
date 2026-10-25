# Proposal — call-target SITE disclosure, "resolved means minted", and the wire's member kinds

**Status: PROPOSED, NOT NORMATIVE.** Drafted 2026-10-25 by the spec lane of call-target round 1. Nothing here
carries a rung marker and no engine may cite it as SPEC. It is the text FABLE-SYNTHESIS §2.2 items 1–3 asks for
(`~/candor-handoff/calltarget-analysis/FABLE-SYNTHESIS.md`), written so Tom can choose between the two
strictness options for item 1 and so each engine lane knows what to measure first. Item 4 (the std-owned
requirement key, [SOUNDNESS R974]'s deferred rung) is NOT drafted; §4 below says only what its census must
count before it is un-deferred.

Evidence: the four call-target matrices (`~/candor-handoff/calltarget-analysis/<engine>/REPORT.md`), the rows filed
from them (SOUNDNESS R1405–R1428), and conformance PART 104 (`conformance/gen_call_target.py`), whose RECORDED cells
are the ones these clauses would turn into scored cells.

---

## 1. The site/disclosure clause (new paragraph, §4 — after the bounded-CHA paragraph)

### 1.1 Why a clause is needed

Every engine already treats an unresolved EXPLICIT call as a disclosure: no target, so `Unknown` with a reason. An
unresolved IMPLICIT call — a site where the platform runs user code (formatting, comparison, hashing, cloning,
iteration, conversion, deferred force, drop/close, a callback) — ends in NOTHING: no edge and no `Unknown`. The four
lanes measured the asymmetry in the same place in every engine (rust `charge_coercion*` "no edge and no Unknown" by
design; swift's untyped member call dropped at `CallCollector.swift:8735`; java generating no site for a JDK body
that calls back; ts's accessor, iteration and coercion readers having no "not proven, so disclose" branch), and it is
where most of each engine's silences sit (SOUNDNESS R1405–R1408). No SPEC sentence says what an engine must do at a
site it RECOGNISES but cannot resolve. Today two sentences bear on it and both are permissive:

- §4's conventionally-pure MAY (*"formatting, equality, hashing, cloning … MUST NOT extend the set to anything where
  an effect could plausibly hide (iterators, callbacks, I/O traits, finalizers)"*), narrowed by ⟨0.40⟩ to a receiver
  whose declared type IS the standard-library or root type;
- the bounded-CHA paragraph's *"Dispatch through an EXTERNAL abstraction an engine does not model (a stdlib iterator
  protocol, a serialization trait) MAY remain unflagged, but then MUST be documented as a named miss (item 7, §7)"*.

So an iterator silence is conformant today if the engine's README names it. The clause below removes that licence
for recognised sites, in one of two widths.

### 1.2 Draft text (common part)

> **An implicit site that runs user code MUST end in a charge or a disclosure, as an unresolved explicit call does.**
> An implicit site is an expression at which the platform, not the program text, invokes a member the program may
> supply: formatting, comparison, hashing, cloning, iteration, conversion, a deferred or lazy force, a drop, close or
> finaliser, and a platform routine that runs a function value it was given. An implementation that RECOGNISES such
> a site resolves it to the analysed units that can run there, under the bounded-CHA discipline, or — where it
> cannot — discloses `Unknown` with a reason naming the site's member (`dispatch:<owner>.<member>`, or `callback:`
> for a function value), never silence. The set of sites an implementation recognises MUST be derived from the
> platform's own declarations where the platform publishes them (rust-src bounds, JDK class files, a
> `.swiftinterface`, ECMA-262 and `lib.d.ts`), and the sites it does NOT recognise MUST be listed as a named miss
> under §7 item 7, so the residue is a documented list rather than an absence.

What the common part does NOT say: it does not require an engine to recognise every site, only to stop treating a
recognised-but-unresolved one as resolved-pure, and to derive what it recognises rather than enumerate it by hand.
"Derive" is a property of the table, checkable like κ (`--check` against the pinned platform); the lanes'
inventories show the hand-written lists are where the silences cluster (the lanes' own counts, not re-derived here
— FABLE-SYNTHESIS §1.3 found rust's overall list percentage irreproducible: rust implicit-hook 33 of 92 items,
deferred-iterator 21 of 35; swift 66 pure lists; ts ~20 lists across the implicit readers).

### 1.3 The two strictness options (Tom chooses)

**Option A — every recognised unresolved implicit site discloses.** Append:

> This binds every implicit site, including formatting, equality, hashing and cloning: §4's conventionally-pure MAY
> licenses treating a resolved dispatch over those members as pure only where every implementor reachable at the
> site is analysed and pure; it does not license silence at a site whose operand the implementation could not type.

Effect: the asymmetry disappears. `format!("{:?}", vec![x])`, `"\([x])"`, `String.valueOf(list)` and
`` `${[x]}` `` over a user element must charge the element's member or disclose. PART 104's `hk_fmt_container` cell
becomes scored (today SILENT on rust, R1247, and swift, R1249; charged on java and ts). Cost: every untyped operand at
a formatting/equality/hashing/cloning site becomes an `Unknown` until the engine can type it — this is the half rust
priced once and withdrew (R1157, 558 rows).

**Option B — only the class §4 already says may not be left silent.** Append instead:

> This binds iteration, a callback, an I/O read or write, a conversion, a deferred or lazy force, and a drop, close
> or finaliser. Formatting, equality, hashing and cloning remain under §4's conventionally-pure MAY as narrowed by
> ⟨0.40⟩ (a receiver whose declared type IS the standard-library or root type); a receiver typed by a package's own
> abstraction or by a concrete package type is bound by this paragraph through ⟨0.40⟩, not by the MAY.

Effect: SPEC-consistent with the ⟨0.40⟩ MAY as written; the iterator/callback/I/O silences (rust `io::copy`,
`BufWriter`, `Iterator::zip`, `for` over a user `IntoIterator`, `thread::spawn` with a fn item — R1405; java `Thread`
subclass `start()`, `writeObject`, the collection skeletons — R1242/R1406; swift `for in`, `Set.insert` —
R1407/R1415; ts for-of/spread — R1408) lose the named-miss licence, while `{:?}` over `vec![x]` stays licensed.
PART 104's `hk_iter_local` and `hk_callback` become scored under either option (both charge on all four engines today
in their sample shapes); `hk_fmt_container` stays recorded under B.

### 1.4 What each lane must measure to price A and B (before Tom decides)

The bands in `candor/CLAUDE.md` ("When a disclosure-only change ships without asking") price the HEDGE half only.
The RESOLUTION half (derive the site table, resolve the site) adds concrete charges and is priced by auditing every
new charge. So each lane reports the two halves separately, both against PUBLISHED 0.40.16, absolute counts beside
percentages, and says which option each count belongs to:

| measure | rust | java | swift | ts |
|---|---|---|---|---|
| denominator | analysed units, 1,175 chained + 5,376 standalone (`bin/corpus-ab.py`, `--jobs 2`) | functions, 452 jars + 304 chained | functions, 38-package chained set | units, 28-entry roster + chained |
| (1) recognised sites, by class (format/eq/hash/clone vs iterate/callback/IO/convert/deferred/drop) | std entry points the generated rust-src bound table names, reached in the corpus | JDK call sites the site generator's summary says invoke an overridable member of an argument or receiver | sites the `.swiftinterface` table names | sites the ECMA-262/`lib.d.ts` table (executed Proxy oracle) names |
| (2) RESOLVED by the table (adds concrete) | ADDED concrete rows, every one traced to a body | same | same | same |
| (3) UNRESOLVED → new `Unknown` (the hedge) | rows newly carrying `Unknown` because a recognised site's operand is untyped (the `charge_coercion` untyped-operand branch) — split A-only vs B | rows newly carrying `Unknown` at a recognised JDK site with an unresolved argument type | today's dropped untyped member calls (`:8735`) that would disclose | the implicit readers' new "no target" branch (J3) |
| (4) gate flips at callers | `deny E` / `deny Unknown` 0→1 per class, the user-visible cost | same | same | same |
| (5) the R1157 check | does (3) under A reproduce R1157's 558 withdrawn rows? | — | — | — |

The decision then reads off (3) and (4) per option: B's hedge reach is (3) restricted to the iterate/callback/IO/
convert/deferred/drop class; A's is all of (3). A count in (3) that the lane can move into (2) first — a resolution
— is not a cost of the clause at all (CLAUDE.md: "a resolution beats a hedge").

## 2. The resolved-means-minted rule (one sentence, §4 — after "A method *inherited* by a type … is a resolved call")

> **A body an implementation names as a target is RESOLVED only if it is an analysed unit; a target that is not a
> unit — a declaration with no body the scan analysed, a member assigned at run time, a body in a file the scan did
> not read — MUST be disclosed, never counted as resolved-pure, and MUST NOT suppress a hedge the site would
> otherwise carry.**

Why: the ts lane's prototype first suppressed the opaque-iterable hedge on finding an object-literal
`[Symbol.iterator]` declaration that was never minted as a unit, and supplied no edge — 24 DISCLOSED→SILENT cells,
fixed only by counting minted bodies (`~/candor-handoff/calltarget-analysis/ts/REPORT.md` §4). It is the resolver-level
form of ⟨0.26⟩'s "disclose the ambiguity, never resolve it by guessing", and of R1424 (JS prototype-assigned members
never minted). It adds no field.

## 3. The wire's member-kind generality (clarification of ⟨0.39⟩ obligation 1 — no rung, no field)

> **"The dispatched member" in obligation 1 is a member of ANY kind** — a method, an accessor or property, a
> subscript, an operator, an initialiser requirement, a hook member reached by an implicit site (§1 above), and a
> member whose only implementors the producer sees are pure. **A consumer's SUBCLASS of a dependency's concrete,
> non-final (Swift: `open`) class is an implementor of that class's members**, as the ⟨0.39⟩ subclass sentence
> already says for the dependency's own subclasses; a producer whose call site dispatches on such a member MUST name
> it (`dispatchesOn`) unless the class or member is closed (final, sealed, private, package-private across runtime
> packages, non-`open`). **Publishing a key or a union entry MUST NOT delete a disclosure the consumer would
> otherwise make:** a chained hit on a union entry for an abstraction whose OWNING package is not chained leaves the
> owner's `invisible` (or `Unknown`) in place — the ⟨0.39⟩ sentence *"A mechanism that makes reports better must
> not make silence cheaper"* applied to the producer's new keys.

What it closes once each producer complies (all are rows today, all are ⟨0.39⟩ text already binding): swift cause C
`open class` members (R1416) and non-method hooks at L4b (R1415); ts concrete classes (R1417), accessors/JSON/
`valueOf`/for-of over a dependency interface (R1419), `${x}` over a dependency abstraction (R1418); java concrete
non-final classes (R1317) and third-package Object-protocol members (R1316). What guards the removal direction: PART
104's `r764` cell, which doctors a producer's report with a pure-only union entry for an unchained owner and requires
the owner's disclosure to survive — it PASSES on rust, java and swift (with its `fx` control proving the doctored
entry reaches them) and is XFAILED on ts (R764). It must stay green on every engine before any producer publishes
pure-only or class-member keys (FABLE-SYNTHESIS §3.2).

## 4. NOT drafted: the std-owned requirement key (R974's deferred rung)

Tom deferred the rung on 2026-10-13 after a benefit census found the population ≈ 0 (swift: 2,095 witnesses, 6
effectful, 1 reaching a dependency generic, and that one disclosed; rust: 949 crates, 13,921 witness units, 2
effectful). The call-target matrices since show the SHAPE is pervasive (rust `dep_gen`/`depH_gen` silent for most of
66 hook kinds — R1409; swift cause D, 132 measurements — R1407), but a shape count is not a benefit census, and the
rust shape counts carry the `ctlib::S` path-value confound (R1426, FABLE-SYNTHESIS §1.2).

Before the rung is un-deferred, a census must count **the conjunction the fix needs, on the real corpus**:

1. a DEPENDENCY function or type, generic over a parameter bounded by a STANDARD-LIBRARY-owned trait or protocol
   (`Display`, `Debug`, `Iterator`, `Hash`, `Eq`/`Ord`, `Clone`, `Read`/`Write`, `CustomStringConvertible`,
   `Hashable`, `Sequence`, `Codable`, …), whose body invokes a member of that bound on the parameter (directly or
   through a std entry point the site table names) — count these sites;
2. × a CONSUMER instantiation of that generic with a type whose implementation of the invoked member is EFFECTFUL
   (in the consumer or a third package) — count the (site, instantiation) pairs, and separately the pairs whose
   implementation is pure (benefit 0);
3. for each effectful pair, the caller's verdict today: CHARGED (some other route), DISCLOSED, `invisible`-only, or
   SILENT — only the SILENT and `invisible`-only pairs are the rung's benefit;
4. the gate flips at those callers if the rung's join were in place (`deny E` 0→1).

Report the counts per engine with the spelling control in place (rust: a `use`/`let`-bound control over every
dependency placement). The rung is probably two-engine (rust, swift): java erases generics in bytecode and ts has no
std-owned bound traits, but that is to be confirmed by the java and ts lanes, and if confirmed the rung names them as
declared exclusions with their reasons, as ⟨0.38⟩ did.
