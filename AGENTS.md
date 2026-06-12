# Using a candor report (instructions for an AI coding agent)

candor reports, for every function, which side effects it performs (transitively). This file is the
**language-agnostic** contract for *consuming* a report. To **produce** one, use the candor
implementation for the language you're in — each has its own `AGENTS.md` with exact setup:

- Rust → https://github.com/tombaldwin/candor-rust/blob/main/AGENTS.md
- JVM (Java/Kotlin/Scala/Groovy) → https://github.com/tombaldwin/candor-java/blob/main/AGENTS.md
- other languages → see the implementation index in this repo's [README](README.md)

**Prefer the installed copy over these links**: every engine prints its own `AGENTS.md` under
`--agents` (e.g. `candor-scan --agents`, `npx -y candor-ts --agents`), version-matched to the
binary you are actually running (SPEC §7.11). A repo link can describe a newer or older candor
than the one installed. If the engine version changes mid-project, re-read `--agents`.

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
- **Safe to treat as pure** (e.g. test without mocks) → the function appears in the **call-graph
  sidecar** (every *analyzed* function does, SPEC §2.2) but is **absent from the report** — reports
  list only effectful or unresolved functions, so a pure function has no report entry to inspect.
  (An entry with `inferred == []` and `unresolved == false` would mean the same, but engines normally
  elide it.) Two preconditions before trusting this: the sidecar is **OPTIONAL** (SPEC §2.2) — with
  no sidecar present, absence-from-the-report alone distinguishes nothing and certifies nothing — and
  the producer must claim the §4 trust contract (a documented syntactic *floor* engine misses calls
  silently, so its absences are not purity evidence; check the producing engine's own docs). A
  function in *neither* file was never seen — conclude nothing about it.
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
