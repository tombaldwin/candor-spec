# Vein: global/lazy unit identity is not module-qualified (rust + swift)

**Status: CLOSED — rust `5447eba`, swift `b616caf` (+ `7cec437`, `7f18c38`).** Found 2026-07-25 while scoping blocker (a) of
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
| **swift** | `cfg` — bare name | **FIXED** `b616caf` |

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

**swift remains**, and it is harder than rust was. Two findings while attempting it:

**Swift's sibling defect is in FUNCTIONS, not just globals.** Two modules each declaring `func shared()`
are grouped as **overloads of one another**, every signature matches, and each caller edges to **both**:

    Sources/Core/Core.swift   func shared() -> String { (try? String(contentsOfFile:"/etc/core")) ?? "" }
                              func coreEntry() -> String { shared() }
    Sources/Util/Util.swift   func shared() -> String { ProcessInfo…environment["U"] ?? "" }
                              func utilEntry() -> String { shared() }

    reported:  coreEntry -> ['Env','Fs']    utilEntry -> ['Env','Fs']

candor-swift *does* keep the two units distinct (`shared()` / `shared()#1`, each with its own correct
effect) — it is **resolution** that unions them. So a caller of its own module's `Fs`-only `shared` is
charged the other module's `Env`. Swift overloads live in one scope; functions in different modules are not
overloads of each other.

**"Prefer the caller's module" is UNSOUND for Swift — measured twice, both reverted.**

1. Applied to all candidates, it dropped **19 real `Unknown` disclosures** on swift-syntax. A type declared
   in one module and *extended* in another is idiomatic Swift, so for a member or initializer "a candidate
   in my module" does not mean "the candidate": `Bool.makeLiteralSyntax` (SwiftSyntaxBuilder) calls an
   initializer declared in SwiftSyntax.
2. Narrowed to **free functions only**, it still dropped one — and that one settles it.
   `SwiftSyntaxMacrosTestSupport/Assertions.swift:110` calls
   `SwiftSyntaxMacrosGenericTestSupport.assertMacroExpansion(…)`: **cross-module delegation between
   same-named free functions**, where the other module's function is precisely the intended target. A
   convenience wrapper delegating to a generic implementation of the same name is a normal library shape.

Choosing correctly needs the caller's **imports** and Swift's real overload resolution, which a syntactic
engine does not have — for the UNQUALIFIED half. The lead out of that second measurement turned out to be a
distinct, bigger find:

### The QUALIFIED half was a separate cardinal sin, and is FIXED (candor-swift `7cec437`)

`Core.shared()` — a module-qualified free call — is neither `typed` (its base names a module, not a type)
nor `unqualified`, so it matched **no branch** of the resolution chain and produced **no edge at all**:

    Sources/Util/Util.swift   func delegates() -> String { Core.shared() }   ->  PURE

A caller of a function that reads the filesystem, reported sound-complete pure. Instrumenting the call
records (after two wrong guesses about where the module name went) showed the qualifier is **not** lost: the
collector keeps the base on the call as `extOwner` and only strips `call.path` to the bare leaf. So the fix
is exact rather than heuristic — the base must be a real target that is not also a local type, and that
target must declare exactly one free function of the name, or nothing resolves.

**A/B: zero losses on candor-swift and swift-syntax, one gain** —
`assertMacroExpansion(…)#1` picks up `['Unknown']` because its module-qualified delegation now resolves.
The very case that motivated this vein, recovered on third-party code.

### And then the UNQUALIFIED half fell out — FIXED (candor-swift `7f18c38`)

With the qualified form resolving on its own path, the module preference that had been reverted twice was
re-measured and came back **clean: zero gains, zero losses** on candor-swift and swift-syntax. The
counterexample that had killed it — `SwiftSyntaxMacrosTestSupport` delegating to
`SwiftSyntaxMacrosGenericTestSupport.assertMacroExpansion` — is written **module-qualified**, so once
qualified calls stopped falling through, the preference no longer had to steal that edge.

**The earlier revert was right about the measurement and wrong about the cause.** The preference was being
judged on a broken foundation. It applies to **free functions only** — for a member or initializer, a type
declared in one module and extended in another is idiomatic, and applying it there dropped 19 real `Unknown`
disclosures.

Stated plainly: zero *gains* means neither corpus contains same-named free functions across modules with
differing effects, so the A/B is a **no-regression** result; the recovery is pinned by the regression test,
which asserts both halves — the qualified call charges only Core's `Fs`, the unqualified one only Util's
`Env`.

### The global half — FIXED (candor-swift `b616caf`)

File-scope globals are **accessor** units, and the overload pass that gives ordinary functions their
positional disambiguation excludes accessors — so nothing kept two modules' `let cfg` apart. They now get the
same `#n` treatment, and a bare read resolves in the reader's own module (the lexical rule the free-function
path already uses), with the plain-name fallback kept so a uniquely-named global elsewhere still resolves.

    before:  cfg  -> ['Env','Fs'] @ Util.swift    coreReads / utilReads  ->  both
    after:   cfg  -> ['Fs']  @ Core.swift         coreReads -> ['Fs']
             cfg#1 -> ['Env'] @ Util.swift        utilReads -> ['Env']

A/B: zero gains, zero losses on candor-swift and swift-syntax — plainly, neither declares the same global
name in two modules, so that is a *no-regression* result and the recovery is pinned by the regression test.

**This vein is now closed in all four engines**, and it clears **blocker (a)** of the initializer-edge vein:
widening what counts as a global read was unsafe while identity was ambiguous, and no longer is. Distinct units then resolve exactly — no disclosure needed and no genuine reach
lost, which is why **filtering the edge is the wrong fix**: it removes the fabrication and the real effect
together (measured on swift — the reader loses its genuine `Env` and disappears from the report).

Report unit names change where a collision exists, so this is spec-visible. It is also blocker **(a)** of the
initializer-edge vein: widening what counts as a global read is unsafe until unit identity is unique.
