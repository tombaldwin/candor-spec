# Using a candor report (instructions for an AI coding agent)

candor reports, for every function, which side effects it performs (transitively). This file is the
**language-agnostic** contract for *consuming* a report — any engine, any language. To **produce** one,
use the candor implementation for the language you're in; each has its own `AGENTS.md` with exact setup:

- Rust → https://github.com/tombaldwin/candor-rust/blob/main/AGENTS.md
- JVM (Java/Kotlin/Scala/Groovy) → https://github.com/tombaldwin/candor-java/blob/main/AGENTS.md
- other languages → the implementation index in this repo's [README](README.md)

**Prefer the installed copy over these links**: every engine prints its own `AGENTS.md` under
`--agents` (e.g. `candor-scan --agents`, `npx -y candor-ts --agents`), version-matched to the binary
you are actually running (SPEC §7 item 11). A repo link can describe a newer or older candor than the
one installed. If the engine version changes mid-project, re-read `--agents`.

## The report envelope

A report is a self-describing JSON **envelope**: a provenance header plus one entry per analyzed unit
(SPEC §2). One report covers ONE package; a multi-package project emits a report set under a shared
prefix.

```json
{
  "candor": { "version": "a1b2c3d", "toolchain": "jdk-21", "spec": "0.10" },
  "package": "app",
  "functions": [
    {
      "fn": "app.OrderService.place",
      "loc": "src/OrderService.java:41:5",
      "inferred": ["Db", "Net", "Unknown"],
      "direct": ["Db"],
      "declared": [],
      "undeclared": [],
      "overdeclared": [],
      "unresolved": true,
      "unknownWhy": ["dispatch:Notifier.send"],
      "hash": "app#OrderService.place",
      "calls": ["app.Notifier.send"]
    }
  ]
}
```

- `inferred` — the FULL TRANSITIVE effect set (this fn plus everything it calls).
- `direct` — effects in this function's own body only.
- `unresolved` / `Unknown` — some call could not be resolved; the set may be incomplete (see the
  trust rule below). `unknownWhy` says why, per source.
- Effects: `Net`, `Fs`, `Db`, `Exec` (subprocess), `Env`, `Clock`, `Ipc`, `Log`, `Rand`, `Clipboard`.
- Optional per-entry refinements you may see: `fs` (read/write kinds), `hosts`/`cmds`/`paths`/`tables`
  (the literal surfaces an `allow` gate certifies), `entryPoint` (a runtime reachability root),
  `unitKind` (a non-function unit: `initializer`/`accessor`/`export`, or `agent`/`session`/`hooks` in
  an agent-fleet report — informative only; tolerate values you don't recognize).
- A bare top-level array (no envelope) is the legacy v0.1 form; readers accept it during migration,
  but treat it as predating everything below.

**Which spec am I reading?** Read the envelope's `candor.spec` field — that names the exact contract
version (this repo's SPEC.md rung) the report conforms to; do not assume it from the engine's release
number or from this file. A report without `spec` predates 0.3.

**Why the provenance header matters**: a richer classifier changes the effect set for the *same*
source, so reports are comparable only within one producing `version`. A baseline produced by a
different (or missing) version is invalid gate input — engines fail such a guard run with exit 2
rather than silently comparing (SPEC §2.1). Trust a report relative to its header, not in the
abstract.

## The consumer MUSTs (SPEC §2)

1. **Join across reports by `hash`, never by bare `fn`** — function names legitimately repeat across
   packages (every binary has a `main`); `hash` is the stable cross-package identity.
2. **Tolerate unknown fields** — envelope or entry fields you don't recognize are extensions, not
   errors. The defined fields are the interchange contract, not a closed schema.

## How to use it

Prefer the engine's read-only queries (SPEC §3.1) over parsing the JSON yourself — one cheap call
instead of grepping, same names and output shapes in every language:

- **What a function performs** → its `inferred` set (`show <fn>`).
- **Find functions with a given effect** → `where <Effect>`.
- **Blast radius of editing a function** — *"who is affected if I change X?"* → `impact <fn>` (the
  `affected` list plus the `entryPoints` a change surfaces through) or the lower-level
  `callers <fn>`. Both work for a still-**pure** function you are *about* to make effectful, so they
  answer *before* the edit. Layers of transitive callers are exactly what's easy to under-count by
  hand; let candor list them.
- **Is this caller list complete?** → `callers <fn> --include-unknown` additionally discloses the
  *unresolved-dispatch frontier* (`possibleViaUnknownDispatch`): functions that may reach `<fn>` only
  through a dispatch the engine refused to fabricate an edge for. A disclosed lower-bound expansion,
  never an assertion.
- **Decide whether an `Unknown` is irreducible** → `blindspots`. It lists the Unknown SOURCES (each
  with `unknownWhy`), ranked by how many functions inherit `Unknown` through them. Read the kinds:
  `reflect:`/`native:` are irreducible opacity — accept or gate them; `dispatch:`/`callback:` are the
  improvable kind — often resolved by widening the analysed inputs (the missing implementor, the
  higher-order target) or by a dependency declaring its surface. A 60%-`Unknown` report usually has a
  dozen root causes; fix those, not the smear.
- **Kill an `Unknown` from an uncurated dependency** → the dependency can declare
  `"candorEffects": ["Net"]` in its manifest (SPEC §5.1) — read as declared-not-verified; a name
  outside the vocabulary voids the declaration loudly. Or scan the dependency and chain its report
  (`CANDOR_DEPS`, SPEC §2).
- **Catch a supply-chain capability gain** → `gains <current> <baseline>` — two inputs, current
  first — reports the effects a package *gained* between two reports (a dependency that grew a
  `Net`/`Exec` reach between releases). `diff <current> <baseline>` is the per-function view.
- **Safe to treat as pure** (e.g. test without mocks) → the function appears in the **call-graph
  sidecar** (every analyzed function does, SPEC §2.2) but is **absent from the report** — reports list
  only effectful or unresolved functions. Two preconditions: the sidecar must be present (it is
  OPTIONAL; without it absence proves nothing), and the producer must claim the §4 trust contract (a
  documented syntactic-floor engine misses calls silently, so its absences are not purity evidence).
  A function in *neither* file was never seen — conclude nothing.
- **Decide BEFORE you edit** → `whatif <fn> <Effect>` crosses the blast radius with the active policy
  and returns which functions *would* violate a `deny`/`pure` boundary — ask, instead of
  edit → gate → revert.
- **Enforce a boundary in CI** → a policy gate (`deny`/`allow`/`forbid`, SPEC §6.2) fails the build
  when an edit crosses an effect or layer line — a deterministic guarantee an LLM review can't give.
  The configuration travels with the repo in **`.candor/config`** (SPEC §3.4: `policy`, `baseline`,
  `deps`, … keys; discovered from the scan target, so "point CI at the repo" is the whole setup).
- **Consume the gate verdict as data** → run the scan with `--gate-json <file>` (SPEC §3.3): the same
  check that sets the exit code re-emits `{ spec, ok, violations: [{rule, fn, effects}] }` — join each
  `fn` to its `loc` in the report instead of parsing console `AS-EFF` lines. On exit 2 no verdict is
  written; never treat a stale file as the current verdict.

## The trust rule — do not skip this

`inferred` is **authoritative for what candor resolved**. When `unresolved` is `true` (or `Unknown`
is in the set), the effect list **may be incomplete** — read the source for that function before
relying on it. Never conclude a function is pure if it is marked `unresolved`.

Also read the scan's **κ-coverage ledger** line, which starts with the marker `κ doesn't know`
(SPEC §7 item 14): it names the external packages the scanned code demonstrably calls that the
engine's classifier has neither classified nor reviewed pure. Those packages are *invisible* in the
report — not even `Unknown` — so the ledger is the report's blind-spot receipt: an empty ledger means
covered; a named package means its effects are simply absent until it is declared (§5.1) or its
report is chained (§2). candor is deliberately explicit about what it cannot see; respect that
boundary rather than over-trusting the report.
