# Vein: effect mechanisms that die at the scan boundary (rust + JVM)

**Status: OPEN — reproduced and gate-confirmed, not fixed.** Found 2026-07-25 by a fan-out sweep after the
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
| implicit stringification (`Display::fmt` at a `format!` hole) | **silent-pure** |
| `Drop` glue — a dependency type whose `Drop` writes a file | **silent-pure** |
| `&dyn Trait` / `Vec<Box<dyn Trait>>` where the trait is the dependency's | silent-pure by default; recovered **only** if `CANDOR_WORKSPACE_CHAIN` was set when the *dependency* was scanned, which `--deps` does not do |
| a value bound from a dependency's factory (`let c = deplib::build(); c.fetch()`) | silent-pure — **no return-type information travels in the report**, so the receiver is untyped and every later method call drops |
| dispatch over an **imported** trait whose impls are all local | silent-pure — `trait_decls` is built only from local `ItemTrait` nodes, so CHA never fires |

## Root causes, ranked by leverage

1. **The join only fires on crate-qualified call paths.** Desugared edges — `Display::fmt` at a format hole,
   `Drop::drop` at scope exit — produce no such path, so the dep report's correct entry is never consulted.
2. **No return types in the report**, so a receiver bound from a dependency factory is untyped.
3. **`interfaceUnion` is shipped-but-off in the default `--deps` path** (child scans do not set
   `CANDOR_WORKSPACE_CHAIN`).
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

## Not yet swept

candor-ts and candor-swift. Two of four engines are confirmed; the initializer-edge instance was four-way
and the stringification vein was four-way; the presumption should be that these are too until measured.
