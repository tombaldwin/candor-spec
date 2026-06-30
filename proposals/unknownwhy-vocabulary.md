# Proposal — canonical `unknownWhy` vocabulary (candor-rust BACKLOG 1d; ⟨0.7⟩ prerequisite)

**Status: RELEASED in 0.7** — the canonical vocabulary is now normative in SPEC §4 (four kinds
`reflect:/native:/dispatch:/callback:`, with `dispatch:OWNER.member` the one conformance-compared detail),
and conformance Part 10 pins it across the engines. This document is kept for its **historical rationale**:
the inventory of what each engine emitted before harmonisation, the per-engine mapping, and the resolved
`verify` rows. Where it describes the pre-0.7 divergence (e.g. the loose §4 list, or Java's `dispatch-broad:`),
that is the *historical* state; the released contract is SPEC §4.

## Inventory — what each engine emits today (2026-06-19)

| engine | reason prefixes emitted |
|---|---|
| candor-java | `reflect:` `native:` `dispatch:` `dispatch-broad:` `dispatch-broad-ext:` `dispatch-fn:` |
| candor-ts | `dispatch:` `call:` `accessor:` `bind:` `override:` `callback:` |
| candor-swift | `dispatch:` `call:` `callback:` `opaque-sequence:` |
| candor-rust | `callback:` `ffi:` |

Format also diverges *within* `dispatch:`: candor-ts emits `dispatch:Sink` (owner type only); candor-swift
and candor-java emit `dispatch:Type.member`. The frontier needs the member.

## Canonical vocabulary ⟨0.7⟩

Each entry is `kind:detail`. **Four canonical kinds**, chosen to be language-neutral over *why the engine
could not resolve a call's body*:

| kind | meaning | `detail` format (REQUIRED) |
|---|---|---|
| `reflect:` | invocation chosen at runtime by name/metadata (reflection, `Method.invoke`, dynamic import) | the reflective API or target, best-effort |
| `native:` | a boundary to code the engine cannot analyse: native methods, FFI/`extern`, intrinsics | the symbol/signature, best-effort |
| `dispatch:` | an unresolved **virtual / interface / protocol / dynamic dispatch** — static target known, concrete body not (no impl, bounded-CHA over many impls, or dynamic receiver) | **`<owner-type>.<member>`** (dotted owner + member) — load-bearing for the frontier |
| `callback:` | an unresolved **higher-order** invocation — calling a function/closure *value* (param, field, returned) whose target isn't known | the callback identity (`param#N`, name), best-effort |

`detail` after `reflect:`/`native:`/`callback:` is best-effort prose (not conformance-compared). `detail`
after `dispatch:` is **normative**: `<owner-type>.<member>`, dotted, so the frontier resolves overrides.

## Per-engine mapping (current → canonical)

| current | → canonical | notes |
|---|---|---|
| java `dispatch-broad:` `dispatch-broad-ext:` `dispatch:` | `dispatch:OWNER.member` | fold the bounded-CHA "broad"/owner-external nuance into `dispatch:` — it is still an unresolved dispatch; the frontier resolves it identically. The internal broad/single distinction, if still wanted, is not part of the public reason. |
| java `dispatch-fn:` | `callback:…` (verify) | if it is a function-object/lambda dispatch (a higher-order call), it is `callback:`; if a virtual call, `dispatch:`. **Owner to verify.** |
| ts `dispatch:Sink` | `dispatch:Sink.<member>` | ts must add the member to the detail. |
| ts `accessor:` `override:` | `dispatch:OWNER.member` (verify) | property-accessor / overridable-member dispatch → `dispatch:` if it is virtual member dispatch. **Owner to verify.** |
| ts `call:` `bind:` | `callback:…` (verify) | unresolved function-value call / `.bind` → higher-order → `callback:`. **Owner to verify.** |
| swift `call:` | `callback:…` (verify) | as ts `call:`. |
| swift `opaque-sequence:` | `callback:…` or `dispatch:…` (verify) | opaque `Sequence` iteration → the unresolved `next()`/iterator dispatch. **Owner to verify.** |
| rust `ffi:extern fn` | `native:extern fn` | FFI is a native boundary; fold into `native:`. |
| rust `callback:unresolved call` | `callback:unresolved call` | already canonical. |

Mappings marked **verify** need the engine author to confirm the underlying mechanism before renaming —
a mislabel would make `blindspots`/frontier reason about the wrong kind.

## Conformance ⟨0.7⟩

Add an **`unknownWhy` vocabulary check** to `conformance/run.sh`: assert every `unknownWhy` entry in every
engine's report on the shared fixtures uses one of the four canonical prefixes, and that `dispatch:`
entries match `dispatch:<dotted-owner>.<member>`. (Detail beyond the prefix is compared only for
`dispatch:`.) This is what lets the 0.7 frontier be conformance-equal: all class/protocol engines emit
`dispatch:OWNER.member`, so the frontier query resolves identically; Rust emits no `dispatch:` (its
indeterminacy is `callback:`/`native:`), so its frontier is consistently empty.

## Rollout

1. **Spec** — land the canonical table in `SPEC.md` §4 (⟨0.7⟩), superseding the loose list. **DONE.**
2. **Align engines** — rename each engine's reasons per the mapping. **DONE** (all four):
   - candor-java 0.5.45 — `dispatch-broad*`→`dispatch:`, `dispatch-fn:`→`callback:`.
   - candor-ts 0.5.26 — `dispatch:` now `Owner.member`, `override:`→`dispatch:`, `call:`/`bind:`/`iterate:`/
     untyped-receiver→`callback:`, `eval`/`defineProperty`/`accessor`→`reflect:`.
   - candor-swift 0.5.24 — `opaque-sequence:`/`call:computed`→`callback:` (dispatch:/callback: already canonical).
   - candor-scan 0.5.20 — `ffi:`→`native:`; no `dispatch:` (Rust has no class dispatch → frontier empty).
3. **Conformance** — the vocabulary check above (shipped as conformance/run.sh PART 10); EXIT 0. **DONE.**
4. **Unblocks** — the 0.7 dispatch-frontier port to ts + swift on the now-canonical `dispatch:OWNER.member`
   (conformance/frontier_differential.py). **DONE.**

The **verify** rows resolved to: ts `accessor:`→`reflect:` (defineProperty runtime accessor),
`override:`→`dispatch:` (class override family), `call:`/`bind:`/opaque-iteration→`callback:`; swift
`opaque-sequence:`/`call:computed`→`callback:`; java `dispatch-fn:`→`callback:` (JDK functional-SAM on an
unpinned receiver = a function value). Principle locked: `dispatch:` ⟺ resolvable owner type + member.

This is the standalone prerequisite; the frontier proposal depends on step 2 landing the canonical
`dispatch:OWNER.member` in candor-java (reconciling its current `dispatch-broad:`) and in ts/swift.
