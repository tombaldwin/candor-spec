# Changelog

The **spec (contract) version** is bumped on additive changes (a minor: a new optional field, `AS-EFF`
code, or pinned tool surface) or breaking ones (a major: an envelope reshape or a removed field).
Implementations declare the version they implement via the report envelope's `spec` string. The version
moves as a **ladder**: the reference engine (candor-java) leads a new rung, it is written into
[SPEC.md](SPEC.md), then the other code engines implement it in turn and the cross-impl conformance suite
pins the floor. Each rung is **additive** over the last — an older-version consumer that ignores the newer
optional fields is unaffected.

This file is a one-line-per-rung index. The authoritative, surface-by-surface record is **[SPEC.md §8](SPEC.md#8-changelog)**
(each surface is also tagged inline with the ⟨0.8⟩/⟨0.7⟩/⟨0.6⟩ rung that introduced it); the adversarial
evidence behind the soundness posture is **[SOUNDNESS-LOG.md](SOUNDNESS-LOG.md)**.

## 0.18 — current floor (the trust-trio)

A pinned-tool-surface rung (no report-schema or verdict change; a 0.17 report and gate verdict are
byte-identical under 0.18). Two TIER-2 required additions, both enforcing §4 "never a false all-clear" at the
tool surface: **(1)** the `--strict` advisory-verb CI gate (§3.3.1) — `fix-gate`/`gains`/`unverified` advisory
at exit 0, `--strict` → exit 1 while a finding remains; a typo'd/not-applicable flag is an exit-2 error (never
a silent swallow), and `gains` has no `--policy` (a passed one names the `deny <E> gained` scan gate); **(2)**
the surface/`tour` mostly-Unknown disclosure — never "nothing hidden" (nor a `tour --json` `{"reaches":[]}`)
over a ≥⅓-Unknown graph. Pinned four-way by conformance PARTs 4l, 5b, 12b, 12c. (Rungs 0.16/0.17 are recorded
in [SPEC.md §8](SPEC.md#8-changelog).)

## 0.15

All code engines declare `0.15`; the floor is conformance-pinned (PARTs 4q/4r/4s). A **tier-1 additive**
rung, wire-compatible with 0.14. Three groups, all found/driven by real-world corpus testing:

- The **`coverage` envelope field** (§2) — the κ-coverage ledger travels WITH the report
  (`{"uncovered": [{"name", "calls"}]}`, omitted when empty — a fully-covered report is byte-identical),
  the per-function **`invisible`** field formalized, and **verb conditionality**: every engine's
  `--gate-json` re-discloses coverage as a verdict-preserving advisory, `gains --json` carries the ledger
  + `coverageDelta {nowUncovered, noLongerUncovered}`, and candor-swift's `privacy-manifest` marks its
  verdict `conditional: true` with a human ⚠ when uncovered modules could hide sensor usage (the
  wikipedia-ios false-confidence fix). Design: [COVERAGE-DESIGN.md](COVERAGE-DESIGN.md). **PART 4s** pins
  it four-way (+ the omitted-when-covered byte-compat leg).
- **Host-resolution recall** (§1, "a statically-known request") — a model/Db/Net host that is statically
  knowable but not a bare literal now resolves like an inline literal, both halves: a CONST-anchored head
  (`const API_BASE = "…"; fetch(`${API_BASE}/x`)`; java was already sound via static-final inlining) and
  a LITERAL-COMPLETE head with an interpolated path (`https://api.openai.com/v1/${p}`, `format!`, runtime
  concat from bytecode — all four engines). Sound boundaries pinned: a split authority, an interpolated
  port, and a non-model (CDN) host stay bare `Net`. **PARTs 4q + 4r**.
- **Soundness fixes** (candor-scan: cross-crate glob-reexport/use-rebind silent drop — sqlx-postgres's
  TCP-to-Postgres read pure; cfg_if! macro arms now expanded; block-nested `use` resolved. candor-ts:
  `process.env` via bracket/alias/destructure/`in` now classifies Env). Zero fabrication across the
  1337-crate realworld-oracle.

## 0.14

All code engines declare `0.14`; the floor is conformance-pinned (PART 4p). A **tier-1 additive**
rung, wire-compatible with 0.13 — a **soundness fix** for the cardinal sin (silent under-report).

- The **top-level / initializer unit** (§2 `unitKind`) — a module whose **top-level executable code**
  performs an effect is now attributed to an INITIALIZER unit (`unitKind:"initializer"`), never a
  false-`"pure"` empty report. A module-load-time model call — top-level `await fetch("…api.openai.com…")`,
  an IIFE, a bare `readFileSync`, a JVM static initializer — was **silently dropped** by candor-ts and
  candor-swift (a `deny Llm`/`deny Net`/`deny Fs` gate passed it). Found by dogfooding a real OSS LLM app.
  candor-java's `<clinit>` was already sound (the reference); rust is **N/A** (no top-level executable
  code — a `const`/`static` is const-evaluated). Each engine's unit NAME differs (java `<clinit>`, ts
  `<module>`, swift `<main>`); the effect model is identical. Conformance **PART 4p** pins it. Report bytes
  change where a previously-empty top-level module now carries a unit.

## 0.13

All code engines declare `0.13`; the floor is conformance-pinned (PARTs 4m/4n). A **tier-1 additive**
rung (a new §1 effect + a new envelope field), wire- and invocation-compatible with 0.12 (a consumer
already tolerates unknown effect names, so a pre-0.13 report/policy is unaffected). Two additions:

- The **`Llm` effect** (§1) — a machine-learning model-provider call (chat/completion/embedding/
  moderation), a **boundary effect refining `Net`** the way `Db` does. Classified from a known
  **model-host literal** (`api.openai.com`, `api.anthropic.com`, Bedrock runtime, a loopback Ollama
  `:11434`, …) OR a curated **model-SDK surface** per ecosystem; an unknown host/SDK stays bare `Net`,
  never guessed. Gate-able (`deny Llm ai/`), the sharpest `gains`/`origin` supply-chain alarm ("a
  dependency bump added an `Llm` call"), high surprising-reach salience. Conformance **PART 4m** pins it
  four-way including negative fabrication cases (an S3 bucket named "bedrock", a remote `:11434`).
- The **`extensions` envelope field** (§2) — an engine classifying effects from a **spec extension**
  discloses `"extensions": ["<name>/<version>"]`; omitted when inactive. The first extension is
  candor-swift's **`privacy/1`** — six Apple privacy-sensor effects (Location/Camera/Mic/Contacts/Photos/
  Notify) + the **`privacy-manifest`** verb (verify an app's Info.plist against its code-level sensor
  reach). Its contract lives in candor-swift/SPEC-EXTENSION-privacy.md; **PART 4n** pins that every other
  engine TOLERATES an extension report.

## 0.12

All code engines declare `0.12`; conformance-pinned (PART 5b). A **tier-2
(pinned-tool-surface)** rung, additive over 0.11 and invocation-compatible with it. The **§3.1 `gains`
`origin` field**: each `byFunction` entry separates the supply-chain *attack* signal (`existing` — a fn
that shipped pure at the baseline now performs the effect) from a feature (`new`) and from the
undecidable case (`unknown` — the baseline callgraph is absent OR partial: a corrupt sidecar must never
downgrade the alarm). Existence keys on the baseline callgraph because reports omit pure functions;
`gains --json` also carries `baseline_version`/`engine_version` + the §2.1 producing-build mismatch
disclosure in every engine. Alongside the rung: the corrupt-report loudness rule completed across the
comparative verbs and the MCP surface (the 0.11 rule applied engine × verb × surface), and candor-swift
gained the `gains` verb (its first). Conformance **PART 5b** pins the differential four-way, including
the partial-sidecar and no-baseline cases.

## 0.11

All code engines declare `0.11`; conformance-pinned (PARTs 4f–4k). Another **tier-2
(pinned-tool-surface)** rung, additive over 0.10 and invocation-compatible with it. The **§3.1
surprising-reach surface**: the scan-time opener (the single most surprising transitive reach — a
mundane-named function inheriting a boundary effect from hops away — with a ready-to-run `path`
command), the **`tour [<N>]`** verb (the same ranking on demand, top-N, + a pinned JSON shape), and
`path`'s human-readable default. One deterministic shared heuristic (salience × benignity × hops ×
crossing) with a **salience floor** (`Clock`/`Log`/`Rand` never surface), **module-segment test
exclusion** (never the leaf name), and the explicit "nothing hidden" fallback over a manufactured
surprise. Also ⟨0.11⟩: **found-but-corrupt loudness** — a located report yielding no trustworthy
functions fails loudly, syntactic and semantic corruption alike (a well-formed `functions: []` stays a
valid pure report); the coverage-ledger marker de-jargoned (**`classifier doesn't cover`**, was `κ
doesn't know` — a consumer grepping the old marker must update); and the plural-`packages` tour-header
label. Design: candor-rust SURFACE-BEST-FIND-DESIGN.md.

## 0.10

All code engines declare `0.10`; conformance-pinned (PART 17). Another **tier-2
(pinned-tool-surface)** rung, additive over 0.9 and invocation-compatible with it. The
**§3.3.1 canonical query grammar**: for every §3.1 query verb an engine exposes, one invocation shape in
every language — the report **discovered** from `.candor/` (walk-up, §3.4) with a `--report <locator>`
override, `--json` selecting JSON, `--policy <file>` a flag never a positional. Pre-0.10 positional forms (a
leading report, the `0|1` JSON sentinel, a positional policy) stay accepted as **deprecated aliases** with a
stderr note, removed no earlier than the next major. Conformance **PART 17** pins it four-way. Design +
per-engine impact: [CLI-GRAMMAR-DESIGN.md](CLI-GRAMMAR-DESIGN.md).

## 0.9

All code engines declare `0.9`; conformance-pinned (PART 12b/12c/12d). A **tier-2
(pinned-tool-surface)** rung, additive and wire-compatible with 0.8 (a 0.8 report and `--gate-json` verdict
are byte-identical under 0.9). It promotes the **remedial tool loop** into the pinned §3.1/§3.3 surface:
`fix`/`fix-gate` (compute the boundary hoist-refactor), `unverified` (the provable-purity disclosure), and
the gate's provable-purity **auto-disclosure** (a verdict-preserving advisory note on a `--policy` scan).
Full surface-by-surface record in [SPEC.md §8](SPEC.md#8-changelog).

## 0.8

All four code engines declare `0.8`; conformance-pinned (PART 12, the gate-verdict
differential). Additive and wire-compatible with 0.7.

- **The structured gate verdict** (§3.3) — `--gate-json` emits `{ spec, ok, violations:[{rule, fn, effects,
  detail?}] }` from the same check that sets the exit code, so a consumer can never see a verdict that
  disagrees with the gate. Powers the PR-native SARIF surface.
- **The `.candor/config` file** (§3.4, amendment) — a checked-in alternative to the `CANDOR_*` env wiring:
  shared key vocabulary, target-anchored discovery, fail-closed when configured-but-unusable, unknown keys
  warn. Relative values anchor to the config's home directory; recognized-but-unimplemented keys are
  disclosed.
- **The stale-baseline posture** (§2.1, amendment) — a baseline *guard* given a baseline from a different
  (or absent) producing build MUST fail closed without evaluating; a comparison *query* discloses and still
  answers.
- **AS-EFF-008 reconciled** to the machine-checked contract (§6) — the rule fails closed on an
  uncertifiable masked/opaque literal surface, as every engine implements and the masking + gate-verdict
  differentials pin.

## 0.7

Additive, wire-compatible with 0.6; all four engines implement it, two conformance differentials pin it.

- The canonical **`unknownWhy` vocabulary** (§4) — four kinds `reflect:`/`native:`/`dispatch:`/`callback:`,
  superseding the divergent per-engine prefixes.
- A compact **type-hierarchy sidecar** (§2.2) and the **`callers --include-unknown`** modifier (§3.1) — the
  disclosed unresolved-dispatch frontier, resolved precisely against the hierarchy.
- The **required command-line surface** (§3.3) pinned across engines.

## 0.6 and earlier

The report envelope, the effect vocabulary, the `AS-EFF-00x` diagnostics, the §6.2 policy DSL, the §3.1
query shapes (including `gains`), and the §5.1 effect manifest landed across the 0.4–0.6 rungs. See
**[SPEC.md §8](SPEC.md#8-changelog)** for the full per-rung surface list and the ⟨rung⟩ inline tags, and the
repo's git tags (`v0.4`, `v0.4.1`, `v0.5`, `v0.8`) for the contract snapshots.
