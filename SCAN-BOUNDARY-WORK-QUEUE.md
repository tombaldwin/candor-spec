# Work queue: closing the scan-boundary vein

The ordered backlog for [SOUNDNESS-VEIN-crossing-the-scan-boundary.md](SOUNDNESS-VEIN-crossing-the-scan-boundary.md).
Written to be picked up cold — by a fresh session, or by an agent — without needing anyone's context.

**Why this is the top of the queue.** It is the only known defect that makes a `deny` gate pass code it
should fail, it reproduces in all four engines, and it is gate-level rather than report-level. PAPER1 §6.1b
now scopes the headline claim because of it.

## THE STANDING BAR — applies to every item, no exceptions

1. **The cardinal sin is a SILENT UNDER-REPORT.** Never trade it for its mirror. A fix that FABRICATES an
   effect on a genuinely pure function is worse than the miss it closes. If an A/B shows gains you cannot
   trace to a real reach, **revert**. Three swift fixes were reverted this way before a fourth landed clean;
   that is the expected rhythm, not a failure.
2. **A/B on real code, every change.** Scan several real codebases before and after and diff per-function
   effect sets. Report gains AND losses. Zero losses required. Every gain traced to source, not assumed.
   Watch the report ENTRY COUNT too — a spurious extra entry means an unbounded edge (this caught a bad
   drop-glue marker).
3. **Two-tree fixture per fix**, with the single-tree control, and the `deny` gate going from exit 0 back to
   exit 1. The control is what proves it is a *boundary* defect and not a general limitation.
4. **Regression test per fix**, engine's own suite green, four-way conformance green.
5. **Verify before claiming.** Several sweep findings did not reproduce (see the corrections in the vein
   doc). Reduce every mechanism story to a fixture before acting on it.
6. **Honest beats silent.** If a mechanism cannot be resolved soundly, making it disclose `Unknown` is a
   valid and valuable fix.
7. Commit each fix separately, substantive message, trailers:
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` and the session `Claude-Session:` line.
   **Do not push without an explicit instruction.**

## The template that works

Emit the call shape the cross-package join **already understands**, rather than adding a resolution path.
The dependency's report almost always already holds the right answer under the right key — in 12 of 13 JVM
cases it did, and nothing looked for it. Two caveats learned the hard way:

- The emitted shape must be **distinguishable from a real call**, or it pollutes the κ ledger and the
  coverage envelope (`cr::<drop>::Type`, not `cr::Type::drop`).
- **Bound it at consumption**: join it and `continue`, so it can never reach local resolution or the
  classifier.

## Queue

### rust — 3 of 5 done
- [x] implicit stringification via a dep's `Display::fmt` — `1623a07`
- [x] drop glue via a dep's `Drop` — `a2fbe74`
- [x] `interfaceUnion` emitted in `--deps` child scans — `50218e3`
- [!] **R4 — imported-trait dispatch. ATTEMPTED, REVERTED, and it needs a DECISION not a patch.**
      `use deplib::Handler; fn run(h: &dyn Handler)` reads pure while the effectful `MyH::go` impl is IN THE
      SAME REPORT. Implementing local CHA over an imported trait's impls does fix it — the fixture at
      `/tmp/rrev` then matches its control exactly — **but it contradicts a deliberate prior decision**, and
      an existing test says so in as many words:

          tests.rs:1698  "external-trait local impl must not resolve (fabrication)"

      That decision is defensible and I did not flip the test to make my change pass. For a STD trait it is
      plainly right: CHA-ing `Iterator` over a local `RowIter::next` charges every `.next()` in the crate
      with that impl's effects. Measured on the widened version: **30 fresh `Unknown`s on serde_json** from
      the >12-impl arm alone, before the resolving arm is even considered.

      So R4 is a real tension between two rules the project holds simultaneously:
      *never leave a provable reach silent* vs *never fabricate over an unbounded impl universe.*
      The plausible resolutions, none free:
      1. Split the trait's PROVENANCE — CHA local impls of a trait imported from a **project dependency**
         (`deplib::Handler`) but never one from std/core/alloc. Narrower than the current blanket rule, and
         still an over-approximation if a third crate implements the trait.
      2. Require a provable receiver — only resolve when the `&dyn` value's construction site is local and
         monomorphic (the same shape rust already uses for the monomorphic-receiver retry).
      3. Accept it as a documented residual and disclose `Unknown` only where the impl set is small and
         wholly local.
      **Do not implement any of these without deciding which rule wins first.** Attempted in this session,
      reverted clean, suite green.
- [ ] **R5 — return types in the report.** A receiver bound from a dep factory (`let c = deplib::build();
      c.fetch()`) is untyped, so every later method call drops. Needs a `returns` field in the report
      format — spec-visible, so it wants a rung and four-way agreement. Largest item here.
- [ ] **R6 — fully-qualified `&dyn deplib::Handler`** still reads pure (the imported form is fixed): the
      consumer never forms the crate-qualified key.

### java — 4 mechanism families DONE (fixture 15 silent-pure → 0, four gates exit 0 → 1)
- [x] implicit stringification + equals/hashCode reentry — `bdf272c`. `reentryEdge` ended in a project-only
      `chaTargets`, and **an empty CHA emitted no Unknown, only a dropped edge**. New `nearestDepFn` — the
      cross-boundary analogue of `nearestConcreteSuper` — plus a shared `inheritDepFn` fold.
      *Independently verified here:* `app.S.show -> ['Env']`, gate exit 1.
- [x] inherited / default methods from a dep supertype — `a5b0a41`. `this.load()` compiles to invokevirtual
      with the PROJECT class as owner, so the join was never reached; the subclass's own ClassNode names its
      dep parent, so the chain is walkable from this side.
- [x] callback / HOF hand-off — `b891d5f`. Method refs join on the handle's exact owner+name+desc; a
      constructed functional takes the type's reported surface, gated on the PARAMETER being a functional
      interface.
- [ ] **dep-interface-typed dispatch to a dep impl** — needs the dependency's own HIERARCHY, which the report
      format does not carry. Live residual, measured (jackson `WritableObjectId.generateId` loses `Rand`
      through `ObjectIdGenerator`). Same family as rust R5 / swift factory-receiver: a format extension.
- [ ] by-NAME reentry contracts (`compareTo`/`append`/`write`/`read`) — resolve over any descriptor, so
      there is no single hash to join on.

**A fabrication caught mid-flight, worth carrying:** the first version imported dep entries whose whole
content is `Unknown`, which turned **12 fully-resolved jackson-databind functions Unknown** from one method
`ObjectIdGenerator`/`ResolvedType.isReferenceType()`. Guard: skip a bare-`Unknown` dep entry when the
project CHA resolves the same signature. Measured with the guard removed — suppresses exactly 14 functions
across six pairs, all Unknown-only, **never a real effect**.

**Two operational traps:** dep reports are VERSION-GATED (generate with the same jar you test with or it is
silently treated as stale); and `build/libs` can hold MORE THAN ONE `-all.jar`, so a glob picks the stale one
— that cost two false negatives here before it was spotted. The stale 0.23.0 artifact has been removed.

### ts — agent in flight
Priority: coercion (local-only AND outside the disclosure channel) → the monorepo symlink shape (a symlinked
workspace dep produces **no disclosure at all** because the blind branch is guarded on `/node_modules/`) →
by-reference HOF handoff → `new DepBoot()` never consulting `crossDeps`.
Also open: the `--dep-inits` precision cost — all of a package's module units share one hash, so importing
charges the union of every file's top level (`proper-lockfile` picked up `Net` from `retry`'s
`example/dns.js`). Narrow to the resolved entry.

### swift — 6 of 7 gate-flipping mechanisms DONE
- [x] implicit stringification of a dep type, all three operand forms — `83ca73c` (verified independently:
      `describeTyped -> ['Env']` across the boundary, gate back to exit 1)
- [x] dependency `deinit` glue — `41dc8de`
- [x] dispatch over an IMPORTED protocol with LOCAL conformers — `eae2de2`. Needs no dep report: Swift
      spells a conformance to an imported protocol in the same inheritance clause, so `subtypesOf` already
      had it. **Note the carve-out that made it safe** — `enum Rank: String` puts `String` in the inheritance
      clause, so an unguarded CHA sends every call on a String-typed value into raw-value enums' methods;
      `RAW_VALUE_BASE_TYPES` closes it and a test pins it. *This is the swift analogue of the same trap rust
      hit at R4: an imported-supertype CHA is only safe with an explicit carve-out.*
- [ ] **factory-bound receiver** — the one gate still flipping 1 → 0. `let c = build(); c.fetch()`: `c` is
      untyped because no return types travel, AND the dep's `build` is pure so it is not even in the report —
      there is no evidence `c` came from the dep at all. Blocked on the same report-format extension as
      rust's R5. A leaf-key join (`M#fetch`) was considered and rejected: leaves like `write`/`run`/`send`
      would fabricate on unrelated receivers.
- Residual: the dep-CONFORMER direction of the protocol case is recovered only under `--workspace` (child
  scans emit the union entries); a plain `--deps` report carries no hierarchy. Pinned as a residual in the
  test rather than invented.

### cross-cutting
- [ ] **Coverage granularity.** Package/crate-granular coverage means one *resolved* call clears the blind
      marker for every call shape into that dependency, so chaining removes a hedge that would otherwise
      have flagged these. Present in all four engines. Does not cause the misses; makes them confident.
- [ ] **Conformance PART 20** pinning the boundary contract four-way, once ≥2 engines have their
      stringification case fixed. Model it on PART 19 and **verify it CATCHES** by mutating one engine.
- [ ] **PAPER1 §6.1b / PAPER2 §4.6b** are written against the current state — update the counts as
      mechanisms close, and re-scope if the claim can be restored.

## Done-ness

The vein is closed when, for each engine, the two-tree fixture matches its single-tree control on every
mechanism in the table, PART 20 is green and verified-to-catch, and PAPER1 §6.1b can be rewritten from
"currently false" to a bounded residual.
