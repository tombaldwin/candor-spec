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
- [ ] **R4 — imported-trait dispatch (no chaining needed).** `use deplib::Handler; fn run(h: &dyn Handler)`
      reads pure while the effectful `MyH::go` impl is IN THE SAME REPORT. `trait_decls` is built only from
      local `ItemTrait` nodes, so an imported trait has no method list and CHA never fires. Fixture at
      `/tmp/rrev`. **This one is pure local information — highest value-to-risk in the queue.**
      Ambiguity rule: keep the existing `lt.count > 1` bail.
- [ ] **R5 — return types in the report.** A receiver bound from a dep factory (`let c = deplib::build();
      c.fetch()`) is untyped, so every later method call drops. Needs a `returns` field in the report
      format — spec-visible, so it wants a rung and four-way agreement. Largest item here.
- [ ] **R6 — fully-qualified `&dyn deplib::Handler`** still reads pure (the imported form is fixed): the
      consumer never forms the crate-qualified key.

### java — 13 of 13 shapes were silent; agent in flight
Priority order: implicit stringification → inherited/default methods from a dep supertype → equals/hashCode
reentry → callback/HOF and method refs. Root causes: CHA is project-only **and an empty CHA emits no
Unknown**; `this.load()` on a dep supertype compiles with the PROJECT class as owner so the join is never
reached; the opaque-handoff Unknown is gated off for exactly the cases HOF surfaces miss.
**Note:** dep reports are VERSION-GATED — generate with the same jar you test with or it is silently stale.

### ts — agent in flight
Priority: coercion (local-only AND outside the disclosure channel) → the monorepo symlink shape (a symlinked
workspace dep produces **no disclosure at all** because the blind branch is guarded on `/node_modules/`) →
by-reference HOF handoff → `new DepBoot()` never consulting `crossDeps`.
Also open: the `--dep-inits` precision cost — all of a package's module units share one hash, so importing
charges the union of every file's top level (`proper-lockfile` picked up `Net` from `retry`'s
`example/dns.js`). Narrow to the resolved entry.

### swift — 7 of 13 silent; agent in flight
Priority: stringification witnesses (local-only) → `deinit` glue (gated on `localTypes`) → protocol indexes
(local-only, and the guard DROPS rather than emitting Unknown) → factory-bound receiver.

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
