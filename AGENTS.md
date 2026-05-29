# Using a candor report (instructions for an AI coding agent)

candor reports, for every function, which side effects it performs (transitively). This file is the
**language-agnostic** contract for *consuming* a report. To **produce** one, use the candor
implementation for the language you're in — each has its own `AGENTS.md` with exact setup:

- Rust → https://github.com/tombaldwin/candor/blob/main/AGENTS.md
- other languages → see the implementation index in this repo's [README](README.md)

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

- **Blast radius of editing a function** → read its `inferred`.
- **Find functions with a given effect** → filter on `inferred`.
- **Safe to treat as pure** (e.g. test without mocks) → `inferred == []` *and* `unresolved == false`.
- **Scope a cross-cutting change** (e.g. "wrap every network call") → filter `inferred`/`direct`
  instead of reading the whole codebase.

## The trust rule — do not skip this

`inferred` is **authoritative for what candor resolved**. When `unresolved` is `true` (or `"Unknown"`
is in the set), the effect list **may be incomplete** — read the source for that function before
relying on it. Never conclude a function is pure if it is marked `unresolved`. candor is deliberately
honest about what it cannot see; respect that boundary rather than over-trusting the report.
