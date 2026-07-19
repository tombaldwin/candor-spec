# Interprocedural value provenance — carrying a value's concrete origin across construction and fields

The design for the one remaining class of report imprecision the reconcile-against-reality engine keeps
surfacing on well-exercised libraries: an effect that is **created in one place and used in another**, where
candor loses the link between the two. The motivating case is the source/sink stance boundary; the fix
generalizes to the whole wrapped-stream / factory-returned / field-carried family.

## The finding (SOUNDNESS-LOG 2026-07-19, commons-compress + commons-vfs2)

The transitive runtime oracle flagged `ZipArchiveInputStream.readFully(byte[],int)` → Fs on code candor read
pure. Root cause is **not** a κ-rule miss — it is that candor's source/sink stance charges an effect at a
stream's *creation* and treats reads as pure-relative, and here the creation is out of the analysed unit:

```
user code:   InputStream in = new FileInputStream(f);        // Fs charged HERE, in the caller
             ZipArchiveInputStream z = new ZipArchiveInputStream(in);
compress:    void readFully(byte[] b, int off) {
               IOUtils.read(this.in, b, off, len);            // reads `this.in` — but its concrete type is GONE
             }
```

By the time `readFully` reads `this.in`, candor sees an abstract `InputStream` of unknown origin. It can
charge `Fs` at creation (**precise whole-program**, but the library-view read looks pure — a silent
under-report on a library scan) *or* disclose `Unknown` at the read (**complete library-view**, but every
whole-program caller that opened a plain file now carries a spurious `Unknown` and fails a `deny Net` gate).
Neither is right, and the choice is forced **only because candor dropped the fact that links them**: that
`this.in` *is* the `FileInputStream` created in the caller. Recover that fact and the trade-off disappears —
the read resolves to `Fs` when creation is in scope, and to `Unknown` only at a genuine external boundary.

The same information loss drives the wider family: a factory-returned object whose concrete type is known at
the `new` but erased at the return; a field assigned an effectful implementation in `<init>` but read behind
an interface; a delegate stream wrapped N deep. All are "created over there, used here."

## What already exists (audited 2026-07-19)

- **`Interp.ProvValue`** — candor's *intraprocedural* provenance lattice on the ASM analysis frames. Per
  value it carries `newType` (the internal name of a provable `new T` receiver — a hard narrowing),
  `declType` (the declared static type, a sound over-approximation source for CHA), `fromIndy` /
  `lambdaTarget` (lambda origin + the project body a functional param resolves to). This is the substrate;
  it is **reset at every method boundary** — it does not follow a value into a field or out through a return.
- **The source/sink stance** — effects charged at stream *creation*; `IOUtils`/filter-stream read overloads
  classify pure-relative (`ClassifierLongTailTest.commonsIoFollowsTheSourceSinkStance`). Sound for
  whole-program, under-reports library-view.
- **R17 `entryAbstractStream`** — already does "external abstract-stream read → `Unknown`", but **gated to
  entry points** precisely to avoid the whole-program redundant-`Unknown` flood. It is the special case of
  this design where the external boundary is an entry point's own parameter; value provenance generalises its
  gate from "is an entry-point param" to "has no in-scope concrete creation".
- **The `invisible` / `coverage` envelope** (⟨0.15⟩) — the *orthogonal* boundary (an effect inside an
  unmodelled package). Value provenance does not subsume it; see "What this is NOT".

## The design

Extend provenance from intra- to **inter**-procedural along three edges, keeping the existing `ProvValue`
lattice as the per-frame carrier and adding a small per-class/per-method summary the analysis already has the
structure to compute (candor is a whole-program bytecode analysis with a class map).

### 1. Field origin summary (per class, one pass)

For each instance field of a reference type, summarise the set of concrete types (`newType`s) and external
origins (constructor parameters, other fields, method returns) ever **assigned** to it, across all `<init>`s
and methods of the declaring class (and subclasses that assign it). A field is:

- **in-scope-concrete** — every assignment is a `new T` (or a value whose provenance is itself
  in-scope-concrete). Its reads carry the union of those concrete types → the read resolves precisely
  (e.g. `this.in` is only ever `new GZIPInputStream(...)` → `Fs` on read).
- **external** — at least one assignment is a constructor parameter / another external / an unresolved
  return. Its reads are parametric on a value candor did not create → they disclose `Unknown` (the honest
  library-view answer), *unless* a whole-program caller supplies the concrete type (edge 3).

The summary is a bounded fixpoint over the class map (monotone: types only accumulate; a merge of an external
origin makes the field external). No heap model, no aliasing beyond field identity.

### 2. Return-type origin (per method)

A method whose returned value has a precise `newType` on every return path exports that as its **origin
type**, so a caller's `x = factory()` gives `x` the concrete provenance the callee proved (recovers the
factory-returned-object veins). An indeterminate return exports nothing (the caller falls back to `declType`
CHA, as today).

### 3. Construction-carried argument provenance (the whole-program precision recovery)

At a `new C(args)` site, bind each constructor argument's provenance (from the caller's frame — where a
`new FileInputStream(f)` is still concretely known) to the parameter slot C's field summary reads from. This
is the edge that makes `readFully` resolve to `Fs` **whole-program** (the caller's concrete stream flows into
`this.in`) while staying `Unknown` **library-view** (no caller in scope → the field is external → the read is
parametric). One level of construction binding, not a general call-string — bounded and deterministic.

### The soundness contract (unchanged invariant, tighter set)

Provenance may only ever **narrow an `Unknown` to a concrete effect** (when it proves an in-scope creation) or
**leave a pure-relative read as `Unknown`** (when the origin is external) — it must **never** turn a concrete
effect pure, and **never** fabricate a concrete effect from an external origin (external → `Unknown`, the
disclosure, not a guessed `Fs`). Formally it only ever moves a value *up* the honesty lattice
(pure-relative ⊑ `Unknown` ⊒ concrete), so the honesty invariant H is preserved by construction: an
imprecise (over-broad) origin can only over-disclose, never under-report.

## What this is NOT

- **Not a general points-to / alias analysis.** Field *identity* only (which field, what was assigned to it),
  one level of construction binding. No arbitrary heap, no interprocedural call-string beyond the constructor
  edge. It is the minimum flow that recovers "created here, used there", deterministically.
- **Not the coverage boundary.** An effect inside an *unmodelled package* (getResolver → `xml.resolver`)
  stays an `invisible`/`coverage` disclosure — a different axis (candor can't see the code at all, vs. can
  see the code but lost the value's type). The two compose; neither subsumes the other.
- **Not a stance reversal.** The source/sink stance stays — this makes it *check* its "a caller-opened
  stream" assumption (charge at creation **iff** creation is in scope) instead of blanket-assuming it.

## Conformance

A new PART: four equivalent fixtures where a class stores a constructor-parameter stream in a field and reads
it in a method (`external → Unknown`), plus a sibling that stores a `new FileInputStream(path)` and reads it
(`in-scope → Fs`), plus a whole-program fixture that constructs the former with a concrete stream
(`construction-carried → Fs`). Each engine must agree, and must never fabricate `Fs` on the external case.
The R17 entry-point case becomes a corollary row.

## Status (2026-07-20)

- **Phase 1 — SHIPPED (candor-java `8537909`).** The intraprocedural half: a stream-consuming utility whose
  InputStream/Reader argument was NOT opened in this method (`newType == null` — a param/field/return)
  discloses Unknown at the call site (`externalStreamUtility`), never in `classify()` (so the source/sink
  stance table stands). Closes `ZipArchiveInputStream.readFully` and 31 sibling readers on commons-compress;
  the compress runtime oracle goes 1→0. The in-scope-open case stays pure-relative (no redundant Unknown) —
  *more* precise than the blanket κ-rule, which fired on 18 in-scope cases too. Regression pins both.
- **The coverage-crediting companion — SHIPPED (candor-java `fbb8cda`).** The verify oracle's transitive
  attribution now stops at an uncovered-package boundary (VerifyCli passes `coverage.uncovered` → the agent;
  `Trace.emit` stops once its stack walk crosses an uncovered frame). Closes the `getResolver` false positive
  (configuration2 oracle 1→0); strictly sound, zero masking (a miss through all-covered frames still has no
  uncovered frame on its stack → still caught). Regression pins both halves.
- **Phase 2 — NOT YET BUILT (the co-scan precision refinement).** Phase 1's Unknown is the honest LIBRARY-view
  answer; whole-program, when the app AND the library are co-scanned and the concrete stream crosses the
  construction boundary (`new ZipArchiveInputStream(new FileInputStream(f))`), it propagates a *redundant*
  Unknown to the app's zip-processing functions ({Fs, Unknown} where {Fs} would do). Suppressing it needs the
  construction-carried binding (§3): a whole-program field-origin summary computed from the actual `new C(args)`
  sites — which requires a provenance PRE-PASS over the program (the field-origin must be known before a read
  is analysed). Real value in the co-scan gate scenario, but genuinely more machinery (a second frame pass or
  a re-propagating post-pass) than Phase 1; scoped as its own effort, not rushed onto the tail of the
  intraprocedural fix. The in-*function* open case (open and read in one method) is ALREADY precise via Phase 1.
- **Phase 3 — assessed as largely N/A for a four-engine sweep.** The specific `STREAM_CONSUMING_UTILITIES`
  table is java-ecosystem (commons-io/Guava); the sibling engines don't share it, so — like the filter-close
  and doPrivileged veins — this is JVM-specific by mechanism. The general *principle* (an external-origin
  stream read discloses Unknown) would apply per-engine to each ecosystem's own utilities, but there is no
  shared conformance case to pin. The return-origin factory half (§2) remains a general future precision item.

## Versioning

A report-shape-neutral **precision** rung (it only changes inferred sets in the sound direction — narrows
Unknowns, discloses external reads). Rides the ladder as an additive floor bump once all four engines carry
it; a sibling on the earlier floor stays conformant (it merely under-narrows / over-discloses, never
under-reports). Pairs with the oracle's path-based coverage crediting (the companion precision fix on the
verify side) so `candor verify` stops false-positiving on the external-origin and unmodelled-package cases
alike.
