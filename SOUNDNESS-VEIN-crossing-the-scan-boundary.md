# Vein: effect mechanisms that die at the scan boundary (ALL FOUR ENGINES)

**Status: OPEN — reproduced and gate-confirmed in all four engines. First mechanism fixed in one engine (rust implicit stringification, `1623a07`); the rest open.** Found 2026-07-25 by a fan-out sweep after the
[initializer edge](SOUNDNESS-VEIN-initializer-edge.md) turned out to be one instance of a general shape.

## The shape, and why it is worse than a missing feature

Take code candor analyses **soundly**. Split it across a crate boundary, scan the dependency separately,
chain its report — the arrangement candor's own docs recommend — and the effect **disappears**:

    // one crate                                    // two crates, dep report chained
    Entry::fmt  -> ['Clock']                        Entry::fmt  -> ['Clock']   (in the dep's own report)
    describe    -> ['Clock']                        describe    -> PURE
    main        -> ['Clock']                        main        -> PURE

`describe` is `format!("{}", e)` on a dependency type whose `Display::fmt` reads the clock. The dep's report
**contains the right entry under the right key** (`deplib#Entry::fmt`); nothing looks for it, because an
implicit coercion emits no crate-qualified call to join on.

**The gate diverges on identical source:**

    deny Clock,  single crate            -> exit 1   (violation, correct)
    deny Clock,  split + chained         -> exit 0   (PASSES — a false all-clear)

That is the cardinal sin in its most consequential form: not an under-report in a report someone might read
sceptically, but a **green gate on code that violates the policy**.

## Reproduction

`/tmp` fixtures, engine `candor-scan 0.23.1`. Dependency:

```rust
pub struct Entry;
impl fmt::Display for Entry {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let _ = std::time::SystemTime::now();      // Clock
        write!(f, "entry")
    }
}
```

Consumer: `fn describe(e: &deplib::Entry) -> String { format!("{}", e) }`.

## The other shapes, from the same sweep

Each was checked against a single-crate control that candor gets right, so each is a boundary effect and not
a general limitation:

| mechanism | chained result |
|---|---|
| implicit stringification (`Display::fmt` at a `format!` hole) | **FIXED** `1623a07` — was silent-pure |
| `Drop` glue — a dependency type whose `Drop` writes a file | **FIXED** `a2fbe74` — was silent-pure |
| `&dyn Trait` where the trait is **imported** (`use deplib::Handler`) | **FIXED** `50218e3` — `--deps` now sets `CANDOR_WORKSPACE_CHAIN` on its child scans |
| `&dyn deplib::Handler` (fully qualified) and field-typed `Vec<Box<dyn …>>` | **still silent** — the consumer never forms the crate-qualified key |
| a value bound from a dependency's factory (`let c = deplib::build(); c.fetch()`) | silent-pure — **no return-type information travels in the report**, so the receiver is untyped and every later method call drops |
| dispatch over an **imported** trait whose impls are all local | silent-pure — `trait_decls` is built only from local `ItemTrait` nodes, so CHA never fires |

## Root causes, ranked by leverage

1. **The join only fires on crate-qualified call paths.** Desugared edges — `Display::fmt` at a format hole,
   `Drop::drop` at scope exit — produce no such path, so the dep report's correct entry is never consulted.
   **The `Display` half is now fixed (`1623a07`)**, and the fix is the template for the rest: emit the call
   shape the join *already* understands (`cr::Type::method`, whose tail2 is exactly the dep report's key)
   rather than adding a resolution path. Gate back to exit 1; A/B zero gains and zero losses on five real
   crates. **`Drop::drop` at scope exit is now fixed too (`a2fbe74`)**, confirming the template generalises. One
caveat learned there and worth carrying: the emitted shape must be **distinguishable from a real call**. A
first attempt used a plain `cr::Type::drop`, which the κ ledger counted as a genuine dependency call and
which added report entries on two of our own crates — the coverage-envelope test caught it. The marker is
now `cr::<drop>::Type`, consumed only by the join, exactly as the lazy-static marker is.
2. **No return types in the report**, so a receiver bound from a dependency factory is untyped.
3. **`interfaceUnion` was shipped-but-off in the default `--deps` path** — **FIXED (`50218e3`)**. Measured:
   the same fixture reads `PURE` against a plainly-scanned dep report and `['Fs']` against a union-scanned
   one, so the flag was the whole difference. **A correction to the sweep that reported this:** it claimed
   the union recovers the field-typed `Vec<Box<dyn>>` and param-typed `&dyn` cases; neither reproduces. What
   it recovers is the **imported-trait** form, which is the idiomatic one. A fully-qualified
   `&dyn deplib::Handler` still reads pure because the consumer never forms the crate-qualified key — that
   residual is real and open.
4. **`trait_decls` is local-only.**
5. **Coverage is crate-granular**, so one *resolved* call into a crate clears its blind flag for **every**
   call shape into that crate. This does not cause the misses above, but it removes the `invisible` /
   `coverage.uncovered` caveat that would otherwise have been incidentally attached — so the report goes from
   *quietly wrong with a warning* to *quietly wrong and confident*.

## A correction to how this was first written up

The sweep first reported this as *"chaining deletes the disclosure"*. Checking it directly: in the
reproduction above the consumer's `invisible: ['deplib']` marker came from an **unrelated** call
(`deplib::helper()`), which chaining then resolved — correctly, since the dep's report omits pure functions
and that is its honest purity claim. The disclosure was never covering the `Display` miss; it merely
happened to be present. **The miss exists identically with and without chaining.** Chaining's contribution
is (5): removing the incidental caveat. Stating it the first way would have blamed the chaining feature for
a vein that predates it.

## The JVM is worse: 13 of 13 probed shapes are silent-pure

A parallel sweep of candor-java probed thirteen mechanisms across the same boundary. **Every one reads
`PURE` chained — none reads `Unknown`.** The sharpest is the one closed four-way *earlier the same day*:

    together:       app.S.show -> ['Env']        lib.Entry.toString -> ['Env']
    dep report:     lib/Entry.toString()Ljava/lang/String;  ->  ['Env']      <- the answer is right there
    app + chained:  (all pure)

**The implicit-stringification vein, closed inside the scan that morning, is still live across it** — and
the JVM gate diverges exactly as rust's does, on the same fixture:

    deny Env,  both trees scanned together     -> exit 1   (violation, correct)
    deny Env,  app alone + dep report chained  -> exit 0   (PASSES)

So the finding is gate-level in **both** confirmed engines, not report-level. Also
silent: `equals`/`hashCode` reentry on a dep key, `forEach(new DepConsumer())`, `Executor.submit` of a dep
`Runnable`, method references (`xs.forEach(DepUtil::write)`, `d::writeInst`), inherited and default methods
from a dep supertype, a dep provided-method driving an app requirement, and dep-interface-typed dispatch.
The only honest control in the set — `forEach(field)` on an opaque field — stays `Unknown[task-handoff]`
in all modes, which is what the rest should look like.

Three JVM root causes, distinct from rust's:

1. **CHA is project-only.** `chaTargets`/`nearestConcreteSuper` walk project-only indexes, so a dep
   `declType` yields an empty CHA — and an empty CHA emits **no Unknown**, only a dropped edge. Worse,
   `this.load()` on a dep superclass compiles to `invokevirtual` with the **project** class as owner, so the
   cross-dep join is never even reached (it requires a non-project owner).
2. **Callback/HOF surfaces are project-only, and the Unknown fallback is gated off for exactly the cases
   they miss.** `new DepConsumer()` has a `newType`, so the opaque-handoff Unknown does not fire; a method
   ref is an `invokedynamic` bootstrap arg, which the same guard suppresses.
3. **A dep's own disclosed `Unknown` is dropped too** — `lib/Task.go()V` is `["Unknown"]` in the dep report
   and its consumer certifies clean. The dependency explicitly said *"I don't know"* and the consumer
   published a clean bill.

**The information is already present in 12 of the 13.** The dep report carries the exact hashes
(`lib/Entry.toString…`, `lib/DepUtil.write…`, `lib/DepConsumer.accept…`, `lib/DepKey.equals…`); nothing looks
for them. Only dep-interface-typed dispatch needs something the report format does not carry (the dep's own
hierarchy).

The same κ hedge withdrawal appears here as cause (5) in rust: chaining a report clears `invisible` for the
whole package, so **8 of the 13 are strictly less honest chained than unchained** — `A1Log.logIt` goes from
`invisible: ["lib"]` to an unhedged pure claim, and the stderr advisory disappears.

## Swept: all four engines have it, and the gate flips in every one

| engine | silent-pure shapes | gate |
|---|---|---|
| **java** | **13 of 13** probed | `deny Env` 1 → 0 |
| **swift** | **7 of 13** | `deny Env Unknown` 1 → 0 on seven mechanisms |
| **ts** | 5 mechanism families | `deny Fs` 1 → 0 |
| **rust** | 5 families | `deny Clock` 1 → 0 |

**Implicit stringification is silent across the boundary in all four** — the vein closed four-way on the
morning of the same day. In every engine the dependency's report holds the right answer under the right key
and nothing looks for it.

### What each engine gets RIGHT — the differences are the design lesson

- **ts** recovers inheritance, factory-returned receivers (return types travel in the `.d.ts`, so rust's
  root cause 2 does not apply), a dep's own disclosed `Unknown`, and a dep's own `invisible`.
- **swift** carries a dep's disclosed `Unknown` *with its `whyReason`*, and its `--workspace`/`--deps` DOES
  set `CANDOR_WORKSPACE_CHAIN` on child scans — which is the sole reason its protocol-CHA case is recovered
  there and rust's is not. Class inheritance is honest (`Unknown[dispatch:Base.load]`), not silent.
- **java** recovers the direct-hash call path and the `<clinit>` edge fixed the same day.

So no engine is uniformly worse; each recovers what its own design happens to make reachable. **The union of
what the four already do is close to the full fix** — which is the strongest argument that this is
tractable rather than fundamental.

### Two engine-specific findings worth their own entries

- **ts, monorepo shape:** a symlinked workspace dependency produces **no disclosure at all** — no
  `invisible`, no ledger, no advisory — because the blind branch is guarded on `/node_modules\//` while the
  module name resolves through a different path. The published-package shape discloses correctly for the
  same code. So in a monorepo every cross-package mechanism is silent-pure until someone remembers
  `--workspace`.
- **ts, interface union needs source:** a published package ships `dist` JS + `.d.ts`, and the `implements`
  clause lives only in the typings, so the child scan emits no union entry. The mechanism is recovered for a
  monorepo sibling and silent for a real npm dependency.
