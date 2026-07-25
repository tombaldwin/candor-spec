# Vein: global/lazy unit identity is not module-qualified (rust + swift)

**Status: rust FIXED (`5447eba`); swift OPEN.** Found 2026-07-25 while scoping blocker (a) of
[SOUNDNESS-VEIN-initializer-edge.md](SOUNDNESS-VEIN-initializer-edge.md). It is a defect in its own right,
independent of that vein, and it is **honesty-critical in BOTH directions**.

## The shape

Two modules each declare a module-scope global with the **same name**. The engine names the unit without the
module path, so the two collapse into one — carrying the union of their effects.

## Four-way sweep

| engine | global unit qual | result |
|---|---|---|
| **java** | `core.C.<clinit>` — fully qualified | **SOUND** |
| **ts** | `core.core.<module>` — path-qualified | **SOUND** |
| **rust** | `<lazy>::CFG` — the synthetic prefix **replaced** the module path | **FIXED** `5447eba` |
| **swift** | `cfg` — bare name | **DEFECT** |

The two sound engines already qualify by path, so the fix has in-family precedent: this is not a new spec
question, it is two engines not doing what the other two do. Note rust qualifies ordinary functions
correctly (`util_m::util_uses`) — it is specifically the `<lazy>::` synthetic that drops the path.

## Both engines fail, in OPPOSITE directions

**rust — a silent under-report (the cardinal sin).** With `LazyLock` statics named `CFG` in two `mod`s, the
report emits **two entries both named `<lazy>::CFG`, both `['Env','Fs']`, both pointing at the same `loc`**
(`src/main.rs:1:14` — the first declaration). And the readers vanish:

    distinct names   util_m::util_uses -> ['Env']    main -> ['Env']      correct
    colliding names  util_uses ABSENT (pure)         main ABSENT (pure)   the defect

A function that demonstrably reaches `Env` reads sound-complete pure, because the collision breaks the edge.

**swift — a fabrication.** Same fixture shape, opposite failure: the merged unit is reported at one file's
location with both effects, and a reader of one inherits the **other module's**:

    Sources/Core/Core.swift  let cfg = (try? String(contentsOfFile:"/etc/core")) ?? ""   // Fs
    Sources/Util/Util.swift  let cfg = ProcessInfo…environment["U"] ?? ""                // Env
                             func utilUses() -> String { return cfg }
    reported:  cfg -> ['Env','Fs'] @ Util.swift    utilUses -> ['Env','Fs']

`utilUses` reads only Util's `cfg` and is charged `Fs` from a global it never touches.

One defect, both halves of the honesty-critical union — which is what makes it worth fixing before anything
built on top of global reads.

## The fix

Qualify the global/lazy unit name with its **declaring module path**, as java and ts already do.

**rust is done** (`5447eba`): `<lazy>::CFG` → `<lazy>::util_m::CFG`. The module path goes **inside** the
prefix so `tail2` — which is how `resolve_target` resolves a `::` path, requiring a unique hit — stays
discriminating (`util_m::CFG`). Appending it after the name would leave tail2 identical and fix nothing;
that placement is the whole point. A shared `lazy_qual` builds the declaration and the forcing edge so they
cannot drift. A/B: **zero gains, zero losses on eight codebases** (regex, rayon, clap, aho-corasick,
serde_json + three of ours) — stated plainly, none has an effectful module-scope lazy static, so that is a
*no-regression* result and the recovery is pinned by the regression test instead.

**swift remains**: `cfg` → qualify by its module (`Sources/<Target>`). Distinct units then resolve exactly — no disclosure needed and no genuine reach
lost, which is why **filtering the edge is the wrong fix**: it removes the fabrication and the real effect
together (measured on swift — the reader loses its genuine `Env` and disappears from the report).

Report unit names change where a collision exists, so this is spec-visible. It is also blocker **(a)** of the
initializer-edge vein: widening what counts as a global read is unsafe until unit identity is unique.
