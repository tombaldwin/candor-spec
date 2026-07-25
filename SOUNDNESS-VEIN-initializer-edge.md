# Vein: the initializer edge into an unanalyzed dependency

**Status: OPEN — characterized, not fixed.** Found 2026-07-25 on real code by the corrected Node oracle
(see [SOUNDNESS-LOG.md](SOUNDNESS-LOG.md) same date, and `candor-ts/soundness/confirmatory/RERUN.md`).

## The shape

A module's own top level performs no effect. It imports a dependency **whose top level does**. Importing
runs that top level, so the importing initializer transitively performs the effect — and candor reports it
`(∅, ∅)`, sound-complete pure. Under H that is a false all-clear.

Found on two held-out npm packages, traced to source rather than counted:

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

Swift's globals are lazy, so `import` alone forces nothing; Rust has no top-level executable code (the same
N/A the 0.14 rung records). So this is a **JVM + Node** vein, not four-way.

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

1. **Chain the dependency's report** — the existing `deps` config key (§2 chaining) already does this, and
   with it the edge resolves precisely, as the JVM fixture shows.
2. **Scan dependency initializers only.** Module top level is a tiny fraction of a dependency's code, so
   the cost is small and the answer is exact. This also sharpens `gains`: *"a dependency bump added a
   top-level `Net` call"* is the supply-chain signal candor exists to raise, and it lives precisely here.
3. **Disclose only when neither is available** — an unreadable or absent dependency. That set is small
   enough for the disclosure to still mean something.

Under (1) or (2) the flood above collapses to the genuinely-effectful initializers, which on this corpus is
a handful.

## Open

Deciding between (2) as default-on versus opt-in, and whether the disclosure in (3) is `Unknown` or a
distinct reason class, is unresolved. Until then the vein is **recorded, not repaired**, and the two
held-out findings stand in the record as candidate silent under-reports of this one class.
