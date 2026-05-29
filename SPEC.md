# The candor specification

A candor *implementation* analyzes a codebase in one language and reports, per function, the set of
side effects it performs. This document defines what every implementation must produce, so that a
report is interchangeable across languages — for an AI agent, a human, or a CI gate.

**Version 0.1** — tracks the Rust reference implementation, [candor](https://github.com/tombaldwin/candor).

## 1. Effects

An **effect** is an observable interaction with the world outside pure computation. The shared
vocabulary:

| Effect | Meaning |
|---|---|
| `Net` | network I/O — sockets, HTTP clients, cloud-SDK request dispatch |
| `Fs` | filesystem read/write |
| `Db` | database query execution |
| `Exec` | spawning / controlling a subprocess |
| `Env` | reading environment variables / the process environment |
| `Clock` | reading wall-clock or monotonic time |
| `Ipc` | local inter-process communication (e.g. Unix-domain sockets) |
| `Log` | logging / tracing |
| `Rand` | randomness / entropy |
| `Clipboard` | system clipboard access |
| `Unknown` | a call the implementation **could not resolve** — see §4 |

An implementation MAY add language-specific effects, but SHOULD use these names where they apply.
`Unknown` is mandatory and special.

## 2. The report

An implementation emits a JSON array, one object per analyzed function (or other *reportable item*,
e.g. a static initializer). Write one file per compilation unit, named so multiple units don't
collide (the Rust impl uses `<prefix>.<crate>.<type>.json`).

Each entry:

```json
{
  "fn":           "<fully-qualified function name>",
  "loc":          "<file:line:col>",
  "inferred":     ["Net", "Fs", "..."],  // FULL TRANSITIVE effect set (this fn + everything it calls)
  "direct":       ["Fs"],                // effects performed in this fn's own body only
  "declared":     [],                    // effects the signature declares it may perform (§5)
  "undeclared":   [],                    // inferred − declared (violations); empty in audit
  "overdeclared": [],                    // declared − inferred (unused declarations)
  "unresolved":   true                   // true if `inferred` may be incomplete (contains Unknown)
}
```

`inferred` MUST be transitive: if A calls B and B performs `Net`, A's `inferred` includes `Net`.
`direct` is the non-transitive subset. Effect-free items MAY be omitted from the report.

## 3. Modes

An implementation SHOULD support:

- **audit** (default) — report each function's `inferred` set; no judgement.
- **JSON** — write the §2 report to a file for machine/agent consumption.
- **conformance** — given functions that *declare* capabilities (§5), flag mismatches (§6). MAY be
  scoped to a module/path prefix for incremental adoption.
- **no-ambient** — flag any *direct* use of ambient authority (an effect performed without holding a
  matching capability), pushing toward a capability-passing / capability-secure style.
- **baseline guard** — diff against a saved report and flag functions that *gained* an effect.

## 4. The trust contract — the core of candor

The defining rule: **an implementation must never report a function as effect-free when it could not
actually determine that.** A call it cannot resolve to a concrete target — dynamic dispatch over an
unknown type, a function value / callback, reflection — MUST contribute `Unknown` to that function's
effect set and set `unresolved: true`. It must not be silently assumed pure.

For a consumer, this means:

- `inferred` is **authoritative** for what the implementation resolved.
- When `unresolved` is true (or `Unknown` is present), the set **may be incomplete** — read the
  source for that function before relying on its effects.

An implementation MAY treat dispatch over a curated set of conventionally-pure standard-library
traits/interfaces (formatting, equality, hashing, cloning) as resolved-pure, to avoid flooding
reports with false `Unknown`s — but MUST document which, and MUST NOT extend it to anything where an
effect could plausibly hide (iterators, callbacks, I/O traits, finalizers).

## 5. Capabilities (conformance)

Conformance needs a way for a function to *declare* the effects it may perform. The canonical
mechanism is a **capability passed as a typed parameter**: holding a value of a capability type
declares the corresponding effect. Examples: candor-Rust's own `&Fs` token; a real
[cap-std](https://github.com/bytecodealliance/cap-std) `&Dir`; a dependency-injected collaborator in
Java/C#. An implementation maps capability types → declared effects.

This is deliberately aligned with capability-secure and dependency-injection styles — the goal is
that a function's *signature* tells you its effect surface.

## 6. Diagnostics (`AS-EFF-00x`)

Shared codes (the `AS-EFF` prefix is historical — "AgentScript effect", the project's origin):

| Code | Meaning | Mode |
|---|---|---|
| `AS-EFF-001` | performs an effect it does not declare | conformance |
| `AS-EFF-002` | declares a capability it never uses | conformance |
| `AS-EFF-003` | makes unresolved calls; effect set not provably complete — cannot be certified | conformance |
| `AS-EFF-004` | uses ambient authority directly | no-ambient |
| `AS-EFF-005` | gained an effect versus the baseline | baseline guard |

The program entry point (e.g. `main`) is exempt from `AS-EFF-001` — it legitimately mints/holds the
whole capability bundle.

## 7. Conformance checklist for an implementation

An implementation conforms to candor-spec if it:

1. resolves call targets using type information (not purely syntactically);
2. computes a per-function **transitive** effect set;
3. emits the §2 report schema;
4. honours the §4 trust contract — unresolved ⇒ `Unknown`, never silent-pure;
5. supports at least **audit**, **JSON**, and **baseline-guard** modes;
6. uses the §1 vocabulary and §6 codes where they apply;
7. is honest in its own docs about what it cannot see.
