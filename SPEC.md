# The candor specification

A candor *implementation* analyzes a codebase in one language and reports, per function, the set of
side effects it performs. This document defines what every implementation must produce, so that a
report is interchangeable across languages — for an AI agent, a human, or a CI gate.

**Version 0.2** — tracks the Rust reference implementation, [candor](https://github.com/tombaldwin/candor).
v0.2 wraps the report in a self-describing `{ candor, functions }` envelope (§2); the v0.1 bare array
is still accepted by conformant readers during migration.

> This document fixes the **interface** an implementation must produce. For the **analysis** behind
> it — the effect lattice, call-site resolution rules, the transitive fixpoint, cross-crate
> composition, and the soundness/precision properties — see [SEMANTICS.md](SEMANTICS.md).

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

An implementation emits, per compilation unit, a self-describing **envelope** — a provenance header
plus one entry per analyzed function (or other *reportable item*, e.g. a static initializer). Write
one file per unit, named so multiple units don't collide (the Rust impl uses
`<prefix>.<crate>.<type>.json`):

```json
{
  "candor":    { "version": "<engine build id>", "toolchain": "<channel>" },
  "functions": [ /* the entries below */ ]
}
```

The `candor` header records which engine produced the report (§2.1). A bare top-level array (no
envelope) remains accepted as the legacy **v0.1** form — readers MUST accept both during migration.

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
  "unresolved":   true,                  // true if `inferred` may be incomplete (contains Unknown)
  "hash":         "<stable cross-crate id>", // OPTIONAL: a stable identity (e.g. DefPathHash) so a
                                         // dependent crate's analysis can inherit this fn's effects
                                         // across the crate boundary. Per-crate analyzers SHOULD
                                         // emit it; consumers may ignore it.
  "calls":        ["..."],               // OPTIONAL: effectful local functions this one calls — the
                                         // effect-relevant call graph, so a consumer can answer
                                         // "who calls X?" from the report without re-analysis.
  "fs":           ["read", "write"],     // OPTIONAL: when `Fs` is present, which kinds — `read`
                                         // and/or `write`. Omitted when the kind can't be
                                         // determined (see below); never a partial claim.
  "hosts":        ["api.example.com"],   // OPTIONAL: when `Net` is present, the LITERAL endpoints
                                         // statically visible (`host[:port]`). Omitted when the
                                         // address is runtime-computed (see below); never complete.
  "cmds":         ["git"],               // OPTIONAL: when `Exec` is present, the LITERAL subprocess
                                         // commands statically visible. Same rules as `hosts`.
  "paths":        ["/etc/app"]           // OPTIONAL: when `Fs` is present, the LITERAL filesystem
                                         // paths statically visible. Same rules as `hosts`.
}
```

`inferred` MUST be transitive: if A calls B and B performs `Net`, A's `inferred` includes `Net` —
**including when B lives in another crate of the same project**. `direct` is the non-transitive
subset. Effect-free items MAY be omitted from the report.

`hash` is optional *only* for single-crate analysis. As soon as A and B are in different crates,
`hash` is the join key a dependent uses to inherit B's effects, so a multi-crate implementation MUST
emit it to satisfy the transitivity rule above — otherwise every cross-crate call is silently dropped
and the boundary function *under*-reports (the dangerous direction). A consumer may still ignore
`hash`; a producer of multi-crate reports may not omit it.

`fs` refines the `Fs` effect into `read` / `write` kinds — the detail a consumer needs to tell a
read-only function from one that mutates the disk. It applies only when `inferred` contains `Fs`. An
implementation that resolves the kind SHOULD emit it; one that can't (or doesn't track it) MAY omit
it. Crucially, when `Fs` is reached but its kind is *unknown* — e.g. inherited from a sibling/dep
report (§2.1) that carried no `fs`, so no read/write is locally observable — the field MUST be
**omitted rather than guessed**. An empty or partial `fs` would be read as a positive claim ("reads
but never writes"), which is the §4 trust contract's forbidden direction (under-claiming an effect).
Omission says "`Fs`, kind undetermined"; a present `fs` is an affirmative read/write classification.

`hosts` refines the `Net` effect with the endpoint(s) a call talks to, but **only the statically
decidable subset**: a string-*literal* address or URL (`connect("rates.internal:7070")`,
`get("https://api.example.com/v1")`) yields a host (`host[:port]`, scheme and path stripped); a
runtime-computed address yields none. It applies only when `inferred` contains `Net`. Unlike `fs`,
`hosts` is **never a completeness claim**: host-by-runtime-value is undecidable, so an absent or
partial `hosts` means "these are the endpoints I could see," NOT "the function talks to no others."
A consumer MUST treat it as informative, never as a closed allow-list — and an implementation MUST
NOT emit a host it merely inferred (only ones it read from a literal), so a present entry is always
sound. This keeps it within the §4 trust contract: `Net` already carries the "performs network I/O"
claim; `hosts` only ever *narrows* it with what's provably visible.

`cmds` (for `Exec`) and `paths` (for `Fs`) follow the **same rules as `hosts`**: the statically-decidable
literal subset only (a `Command::new("git")` / `fs::read("/etc/x")` literal, never a runtime value),
informative-not-complete, never emitted unless read from a literal. The three together are the literal
surfaces an `allow <Effect>` policy rule (AS-EFF-008) enforces; a producer SHOULD emit them so a
dependent crate's allowlist can see a value that lives across the crate boundary.

### 2.1 Provenance (the `candor` header)

A report is only meaningful relative to the engine that produced it: a richer classifier or a new
resolution rule changes the effect set for the *same* source, so a baseline is comparable only to its
own producing version, and a dependent crate must not silently trust a sibling report from a different
engine (the trust contract, §4, applied to candor's own output). The envelope's `candor` header
carries this — `version` (engine build id) and `toolchain` — so the report is self-describing.

Two requirements on it:

- `version` MUST reflect the engine **binary that actually ran**, not the source tree it was built
  from — those diverge when the source is updated without a rebuild, and a source-derived version
  would call a stale engine "current" and mask a stale baseline.
- A consumer performing cross-crate inheritance (§2, `hash`) SHOULD compare versions and, on a
  mismatch, treat the inherited effects as unverified (downgrade to `Unknown`) rather than trust them.

The Rust reference impl additionally embeds `version` in the dylib itself (so a tool can read the
*true* build version without running the engine) and mirrors `version`/`toolchain` into its
`<prefix>.calibrated.json` sidecar; for a **legacy v0.1 bare-array** report that has no header, an
implementation MAY fall back to that sidecar for provenance.

## 3. Modes

An implementation SHOULD support:

- **audit** (default) — report each function's `inferred` set; no judgement.
- **JSON** — write the §2 report to a file for machine/agent consumption.
- **conformance** — given functions that *declare* capabilities (§5), flag mismatches (§6). MAY be
  scoped to a module/path prefix for incremental adoption.
- **no-ambient** — flag any *direct* use of ambient authority (an effect performed without holding a
  matching capability), pushing toward a capability-passing / capability-secure style.
- **baseline guard** — diff against a saved report and flag functions that *gained* an effect.
- **policy** — enforce declared effect boundaries (e.g. "the `domain` layer must perform no `Net`/`Db`",
  "module `parse` must be pure"); flag any function that *transitively* violates one. The architectural
  invariant an agent can't see from a local edit.
- **risk** (optional, **heuristic**) — flag an effect whose argument derives from a function parameter
  (e.g. `fs::read(path_from_param)`) — the injection class (path traversal, command injection, SSRF).
  Unlike the others this is *advisory and imprecise*: a syntactic, intra-procedural nudge that over- and
  under-flags; it MUST NOT gate. An implementation MAY support it; if so it MUST document its limits.

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
| `AS-EFF-006` | (transitively) performs an effect a declared policy forbids | policy |
| `AS-EFF-007` | performs an injection-class effect on caller-derived input (**heuristic, advisory**) | risk |
| `AS-EFF-008` | (transitively) reaches a literal (host / command / path) outside a declared allowlist, or one it cannot see | policy |
| `AS-EFF-009` | (transitively) calls into a layer a declared dependency rule forbids | policy |

The program entry point (e.g. `main`) is exempt from `AS-EFF-001` — it legitimately mints/holds the
whole capability bundle.

A **literal-allowlist** policy rule, `allow <Effect> [in <scope>] <value>...`, constrains *which* values a
scope's effect may reach (AS-EFF-008). Three effects carry a literal surface: `Net` hosts, `Exec`
commands, and `Fs` paths — checked against the transitive `hosts`/`cmds`/`paths` detail, so it catches a
value that lives in a deep or cross-crate callee, matched per-effect (host by name, command by basename,
path by prefix). It certifies the *visible* surface only (see SEMANTICS §6); pair it with a
`deny Unknown <scope>` rule to also forbid the unverifiable case in a scope.

A **layering** policy rule, `forbid <A> -> <B>`, constrains *who* a layer may depend on: no function in
scope `A` may transitively call into scope `B` (AS-EFF-009) — the dependency-direction boundary, checked
over the call graph (see SEMANTICS §6). Together the three policy rule kinds — `deny`/`pure` (what a
layer does), `allow Net` (which endpoints), and `forbid ->` (who it depends on) — make `CANDOR_POLICY`
an architecture-as-code layer.

## 7. Conformance checklist for an implementation

An implementation conforms to candor-spec if it:

1. resolves call targets using type information (not purely syntactically);
2. computes a per-function **transitive** effect set;
3. emits the §2 report schema;
4. honours the §4 trust contract — unresolved ⇒ `Unknown`, never silent-pure;
5. supports at least **audit**, **JSON**, and **baseline-guard** modes;
6. uses the §1 vocabulary and §6 codes where they apply;
7. is honest in its own docs about what it cannot see.
