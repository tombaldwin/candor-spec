# Vein: effect mechanisms that die at the scan boundary (rust)

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

## Not yet swept

Whether the equivalents hold in java, ts and swift. The JVM sweep is in flight; the initializer-edge
instance was four-way, so the presumption should be that these are too until measured.
