# Vein: the module-import edge is not modelled (candor-ts)

**Status: CLOSED for what is determinable — candor-ts `70553c3` (intra-project) + `3643cd9` (chained deps); swift `acfed07`. Only an UNCHAINED dependency is left undisclosed, deliberately.** Found 2026-07-25 on real code by the corrected Node oracle
(see [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md) same date, and `candor-ts/soundness/confirmatory/RERUN.md`).

> **CORRECTION (same day, before any fix).** This document first framed the vein as *"the edge into an
> **unanalyzed** dependency"* and asserted that chaining the dependency's report via the existing `deps` key
> would resolve it. **Both claims were wrong, and testing them is what showed it.** Chaining `graceful-fs`'s
> report into `proper-lockfile` changes nothing — because there is no edge to resolve. And the vein is not
> about dependencies at all: candor-ts does not model the import edge **even when both modules are inside
> the scanned project and both are analyzed**. The correction is kept rather than edited away; I had written
> a mechanism story into the record without running it, which is the failure this project keeps re-learning.

## The shape

A module's own top level performs no effect. It imports a module **whose top level does**. Importing runs
that top level, so the importing initializer transitively performs the effect — and candor-ts reports it
`(∅, ∅)`, sound-complete pure. Under H that is a false all-clear.

**The sharp form is intra-project**, where nothing is unanalyzed and no disclosure is needed — the answer is
simply determinable and candor-ts does not compute it:

    dep.js   const dbg = process.env.NODE_DEBUG || '';   ->  dep.<module>  ['Env']     correct
    app.js   const d = require('./dep.js');              ->  app.<module>  ABSENT      the vein

Both module systems: CJS `require('./dep.js')` and ESM `import { dbg } from './dep.mjs'`. candor-java has
the equivalent edge and gets it right (below), so this is a candor-ts gap, not a model gap.

Found first on two held-out npm packages, traced to source rather than counted:

- `proper-lockfile`'s `index.<module>` ran `{Env, Fs}` declared complete-pure. It requires `lib/lockfile`,
  which requires `graceful-fs`, whose module top level reads `process.env.NODE_DEBUG`
  (`graceful-fs.js:35`).
- `write-file-atomic`'s `lib.index.<module>` ran `{Rand}`, same shape, via `imurmurhash`/`signal-exit`.

Both were invisible until the oracle's ten-frame truncation was fixed the same day, because the frames that
carry them are the outermost ones — the first thing truncation drops.

## The concept is RIGHT in the reference engine; the edge is missing on one side

This is the [implicit-stringification](SOUNDNESS-VEIN-implicit-stringify.md) pattern again: not a missing
idea, a missing edge. With the dependency **inside** the scanned set, candor-java models it exactly:

    app.App.<clinit>    { Env* }        # 1 hop away via dep.Dep.<clinit>
    dep.Dep.<clinit>    { Env }

`GETSTATIC` on an unanalyzed type forces that type's `<clinit>`, and the reference engine follows it. Move
`Dep` **out** of the scanned set and `app.App.<clinit>` reads pure — the edge is dropped in silence rather
than disclosed. candor-ts behaves identically on the `require` form. Fixtures: `fixtures/initializer-edge/`.

### The four-way sweep — and my "N/A" for Swift was wrong

I first recorded Swift and Rust as N/A from language semantics alone. Sweeping with fixtures instead:

| engine | the analogue | result |
|---|---|---|
| **java** | a `GETSTATIC`/method touch forces the owner's `<clinit>` | **SOUND** — `App.<clinit> { Env* }` *and* `App2.use { Env* }` |
| **rust** | reading a `LazyLock`/`lazy_static` static forces its initializer | **SOUND** — `main { Env }`, one hop via `<lazy>::DBG` |
| **ts** | `import`/`require` runs the module top level | **was MISSING → FIXED** (below) |
| **swift** | globals are lazy, so *reading* one forces its initializer | **FIXED** `acfed07` |

Swift is not N/A: `import` forces nothing, but a **read** does, and that edge is dropped:

    Config.swift  let dbg = ProcessInfo…environment["NODE_DEBUG"] ?? ""   ->  dbg ['Env']   correct
    main.swift    print(dbg.count)                                        ->  <main> ABSENT  the vein
    Use.swift     func useMember() -> Int { return dbg.count }            ->  PURE           the vein
    Use.swift     func useBare() -> String { return dbg }                 ->  ['Env']        already sound

candor-swift **has** the mechanism (`globalReads`, "reading it edges to the global unit") and it fires for a
bare read. It is skipped when the reference is the **base of a member access, call or subscript**
(`CallCollector.swift`), which is by far the commoner shape — you almost always read a member *of* the
global, not the global itself.

### The obvious swift fix over-fires, and was reverted

Recording the base of a member access as a global read is a two-line change. It recovers all three fixtures
— and on candor-swift's own tree it produced **113 gains over 226 functions**, `Ipc` alone reaching 114
units including `<main>`. Every one is a **name collision**: `globalUnitNames` is module-flat, so a local
named `pipe`/`run`/`capture`/`env` matched a same-named top-level `let` in a *different* file (a test
fixture), and `local.member` edged to that global's initializer. That is the cardinal sin's mirror, so the
change was **A/B-reverted rather than shipped** — the same call as the flate2 leaf-name-collision revert.

### Decomposing it: the blocker is structural, and it has an order

Two further attempts, both reverted, located the real obstacle. Each is recorded because the *ordering* is
the finding — the vein fix cannot land until the layer beneath it does.

**Attempt 2 — module-scoped resolution.** Swift globals are module-scoped and a SwiftPM package holds
several modules (`Sources/<T>` and `Tests/<T>` are different ones), so resolve a read in the reader's module
and drop any name declared in more than one. Fabrications fell **113 → 94**. The remainder collide *within*
one module, so scoping alone is not enough.

**Attempt 3 — the file-scope guard, a real defect found on the way, and now SHIPPED on its own
(candor-swift `080fb3e`).** Swift allows executable statements at
file scope, so a `let` inside a top-level `if`/`for` block is lexically outside any type while being an
ordinary **local of that block**. candor-swift registered those as module globals: its own `main.swift` has
`let pipe = Pipe()` three blocks deep inside `if wantWorkspace { for … { … } }`, and that is where `Ipc`
came from. Requiring a real file-scope parent chain is correct — `<main>`'s effect set is **unchanged**, so
nothing is lost at the program level — but it did not remove the fabrications. It **re-shuffled which
colliding declaration wins**: `DeclCollector.pushType`, whose entire body appends to three arrays, went from
pure to `{Env, Fs, Unknown}`.

**The root cause is that global units are keyed by BARE NAME.** Several declarations share a name, nothing
distinguishes them, and every scoping refinement only changes which one a read resolves to. Until global
units carry a **unique qualified identity** (module + declaring file, with ambiguous names dropped rather
than guessed), any widening of what counts as a read — which is what closing the vein requires — converts
directly into fabrication.

So the order is: **(a) unique keying for global units, (b) the file-scope guard, (c) then the member-access
base read.**

**(b) is DONE** — separated out and A/B'd in isolation so the result is attributable: **0 gains** on both
candor-swift (226 → 192 units, 9 effectful phantoms dropped: `pipe`/`proc`/`env`/`pol`/`prev`/`fetched`/
`ef`/`disclosePolicy`/`unknownAliases`) and swift-syntax (7,227 fns, 6 dropped). No reader lost an effect —
nothing referenced these names, which is what makes them phantoms — and `<main>` is unchanged on both, so
the block's effects are still charged where they always belonged. Type members untouched. Gates: swift test,
fabrication probe, fuzz, four-way conformance 26/0.

> **UPDATE 2 — (c) is DONE (candor-swift `acfed07`).** Traced the leftover 26 instead of assuming they were
> fabrications: they are the **recovery**. `let allFns = analysis.allFns` reads the global `analysis`, whose
> initializer calls the effectful `analyze(…)`; `depsSpec` reads two globals reaching `Fs`; swift-syntax's
> `SYNTAX_NODE_MAP` reads `SYNTAX_NODES`. Every sampled gain is a real global-to-global read that was
> previously silent. **26 gains / 0 losses** on candor-swift, **7 / 0** on swift-syntax. The one genuine
> fabrication was `DeclCollector.pushType` — a self-property read — and the exclusion for that is what made
> the rest legible. **The swift half of this vein is closed.**
>
> Three reverts got here and each was right at the time: 113 fabrications under bare-name keying → 34 once
> identity was unique → 26 after the self-property exclusion → all 26 verified genuine.
>
> **UPDATE — (a) is DONE.** Global/lazy unit identity is now unique per module in all four engines
> ([SOUNDNESS-VEIN-global-unit-identity.md](SOUNDNESS-VEIN-global-unit-identity.md); rust `5447eba`, swift
> `b616caf`, plus swift's function-call halves `7cec437`/`7f18c38`). Re-attempting **(c)** on that foundation
> took the fabrication count on candor-swift's own tree from **113 → 34**, and adding a guard for
> implicit-self property reads (`self.typeStack.append(x)` is not a global read — `DeclCollector.pushType`,
> whose whole body appends to three of its own properties, was picking up `{Env, Fs, Unknown}`) took it to
> **26**. Still not shippable, so (c) stays reverted.
>
> **The remaining blocker is now precisely identified, and it is not identity.** The leftover 26 are bare
> names that are LOCAL bindings in scopes the collector does not track — `accessorQuals`, `allFns`,
> `conformers` and friends, which exist as bare-named units at indented locations. The guard chain (`vars`,
> `fnTyped`, `boundLocals`, and now enclosing-type `fields`) does not cover every binding form, so a base
> that is really a local still reaches `globalReads`. **Completing local-binding coverage is what (c) needs**
> — a narrower and much better-understood problem than the one this vein started with.

**(a) — historical note.** Pinning down what (a) actually was uncovered a **separate live fabrication** in
the shipped engine, reproduced with a two-module fixture:

    Sources/Core/Core.swift   let cfg = (try? String(contentsOfFile:"/etc/core")) ?? ""   // Fs
    Sources/Util/Util.swift   let cfg = ProcessInfo…environment["U"] ?? ""                // Env
                              func utilUses() -> String { return cfg }

    reported:  cfg       -> ['Env','Fs']   @ Sources/Util/Util.swift
               utilUses  -> ['Env','Fs']

The two globals **merge into one unit** carrying the union of their effects, and `utilUses` — which reads
only Util's `cfg` — inherits **`Fs` from a different module's unrelated global.** Global unit quals are bare
names, so nothing distinguishes them. This is live today and independent of the vein.

Filtering the edge is **not** an acceptable fix. Dropping the read when a name is declared in more than one
module does remove the fabrication, and it also removes `utilUses`'s genuine `Env` — trading a fabrication
for a silent under-report, which is the wrong direction. (Measured: with the filter, `utilUses` disappears
from the report entirely.) The filter is also a **no-op** on candor-swift's own tree once (b) landed — the
cross-module collisions there were all phantom-driven — so it would be unmeasured machinery as well.

**(a) is therefore: give global units a module-qualified IDENTITY so they do not merge.** With distinct
units, resolution is exact, no disclosure is needed, and no genuine reach is lost. It changes report unit
names, so it is a spec-visible change rather than an internal one. **(c)** stays blocked on it — and (c)
additionally needs the implicit-self and unresolved-local bases kept out of `globalReads`, which the
`pushType` case shows are leaking (`typeStack.append(name)` recorded `typeStack` as a global read).

Attempts 1, 2 and 4 stay reverted; only (b) shipped.

*The methodological point: attempt 3 looked dirty only because it was measured on top of (c). Isolated, it
was clean and shippable. Stacked changes hide which one is at fault — separate them before judging.*

## Why the obvious fix is wrong: measured

"A top-level import of an unanalyzed dependency discloses `Unknown`" would fire on essentially everything:

| package | modules top-level-importing an external dep |
|---|---|
| `get-port` | 4/4 (100%) |
| `graceful-fs` | 20/24 (83%) |
| `candor-ts` itself | 24/29 (83%) |
| `write-file-atomic` | 4/6 (67%) |
| `node-tar` | 38/62 (61%) |
| `proper-lockfile` | 9/15 (60%) |

Between 60% and 100% of module units would carry `Unknown`, which does not make the initializer unit honest
— it makes it uninformative, the same trade that makes TS method-decorator effect-injection unfixable by
blanket disclosure. A disclosure everyone learns to ignore protects nobody.

## The resolution is determination, not disclosure

The dependency is not *invisible*; it is merely **outside the scanned set**. `node_modules` and the
classpath are on disk. So the honest answer is to make the edge **determinable** rather than to widen the
`Unknown` surface:

**Chaining the dependency's report does NOT do it** — tested: scanning `graceful-fs` standalone gives
`graceful-fs.<module> ['Clock','Unknown']`, and chaining that report into `proper-lockfile` leaves
`index.<module>` absent. Nothing changes because there is no edge for the chained report to resolve. The
edge has to exist first.

1. **Model the import edge** — from the importing file's `<module>` unit to the imported module's
   `<module>` unit, for every specifier that resolves **inside the scanned set**. Both ends are analyzed, so
   this is precise, needs no `Unknown`, and carries **no flood at all**: an edge into a pure initializer
   yields a pure unit, which the report omits. This is the fix; the external half is what remains.
2. **DONE (candor-ts `3643cd9`).** With the edge in place, a chained dep report resolves it — and the data
   was already present: a dep's module units hash under `<pkg>#<module>`, a package's initializers share
   that one key, so `crossDeps` already held the exact effect set. The edge simply never consulted it.
   Effects attach directly (the dep's unit lives in another report), as chained CALL effects already do.
   With `graceful-fs` chained, `proper-lockfile`'s `lib.lockfile.<module>` picks up its `Clock` and that
   propagates to `index.<module>` — which is what I originally, wrongly, claimed chaining alone would do.
   An unchained dependency is untouched: the guard makes a scan without chained reports byte-identical.
   Scanning **dependency initializers only** to produce those reports automatically — module top level is a tiny fraction of a package's code, so the cost is small
   and the answer exact. It also sharpens `gains`: *"a dependency bump added a top-level `Net` call"* is the
   supply-chain signal candor exists to raise, and it lives precisely here.
3. **Disclose only when neither is available** — an unreadable or absent dependency. That set is small
   enough for the disclosure to still mean something.

## Open

**(1) is DONE** — candor-ts `70553c3` models the edge for every specifier resolving inside the scanned set.
A/B on six real repositories: **zero losses, zero gains outside an initializer unit**, recoveries verified
against source (`node-tar`'s `lib.read-entry.<module>` reaches `Env` because `read-entry.js:3` requires
`./normalize-windows-path.js`, whose line 6 reads `process.env` at top level; candor-ts was also
under-reporting on **itself**). On the held-out slice `proper-lockfile` goes **1 violation → 0**:
`index.<module>` moves from claimed-complete to disclosed. `write-file-atomic`'s finding reaches through
`node_modules` and stays open — the two separated exactly along the line this analysis predicted. Deciding between (2) as default-on versus opt-in, and whether the
disclosure in (3) is `Unknown` or a distinct reason class, is unresolved — the flood table is why. The two
held-out findings reach through `node_modules`, so they stay in the record as candidate silent under-reports
until the external half is settled.
