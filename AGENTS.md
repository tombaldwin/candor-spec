# Using a candor report (instructions for an AI coding agent)

candor reports, for every function, which side effects it performs (transitively). This file is the
**language-agnostic** contract for *consuming* a report. To **produce** one, use the candor
implementation for the language you're in — each has its own `AGENTS.md` with exact setup:

- Rust → https://github.com/tombaldwin/candor-rust/blob/main/AGENTS.md
- JVM (Java/Kotlin/Scala/Groovy) → https://github.com/tombaldwin/candor-java/blob/main/AGENTS.md
- other languages → see the implementation index in this repo's [README](README.md)

To let a HUMAN adopter verify candor's value on their own codebase, each implementation ships a
`PROVE-IT.md` — a self-experiment prompt their agent runs (SPEC §7.11).

## The report

A JSON array, one object per function:

```json
{ "fn": "...", "loc": "file:line:col",
  "inferred": ["Net", "Fs", "Unknown"],  // full TRANSITIVE effect set
  "direct":   ["Fs"],                     // effects in this function's own body
  "unresolved": true }                    // true => some calls could not be resolved
```

Effects: `Net`, `Fs`, `Db`, `Exec` (subprocess), `Env`, `Clock`, `Ipc`, `Log`, `Rand`, `Clipboard`.

## How to use it

- **What a function performs** → read its `inferred` (the full transitive effect set).
- **Blast radius of editing a function** — *"who is affected if I add or change an effect in X?"* → the
  transitive **`callers`** of X, **not** `inferred` (which is what X itself does). Use the `callers <fn>`
  query (it reads the call-graph sidecar); it works for **any** function, including a still-**pure** one
  you are *about* to make effectful — so it answers the question *before* the edit. Enumerating 3–5 layers
  of transitive callers by hand is exactly what's easy to under-count; let candor list them.
- **Find functions with a given effect** → filter on `inferred` (or query `where <Effect>`).
- **Safe to treat as pure** (e.g. test without mocks) → `inferred == []` *and* `unresolved == false`.
- **Scope a cross-cutting change** (e.g. "wrap every network call") → filter `inferred`/`direct`
  instead of reading the whole codebase.
- **Enforce a boundary in CI** → a policy gate (`deny`/`allow`/`forbid`) fails the build when an edit
  crosses an effect or layer line — a *deterministic* guarantee an LLM review can't give.
- **Decide BEFORE you edit** — *"if I add a network call in X, what propagates and does it break the
  architecture?"* → `whatif <fn> <Effect>`. It crosses the blast radius (every transitive caller gains the
  effect) with the policy and returns the verdict — the functions that *would* violate a `deny`/`pure`
  boundary — without writing any code. The pre-edit form of the gate: ask it instead of edit → run the
  gate → revert. (Implementations may expose this as a query; where they don't, compute it from `callers`
  + the policy yourself.)

## The trust rule — do not skip this

`inferred` is **authoritative for what candor resolved**. When `unresolved` is `true` (or `"Unknown"`
is in the set), the effect list **may be incomplete** — read the source for that function before
relying on it. Never conclude a function is pure if it is marked `unresolved`. candor is deliberately
honest about what it cannot see; respect that boundary rather than over-trusting the report.
