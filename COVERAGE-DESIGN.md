# The coverage envelope — carrying "what the scan couldn't see" with the report ⟨0.15⟩

**Status: staged for spec 0.15 (design accepted 2026-07-15; all-engine wave held with the 0.14.2 batch).**

## The finding (SOUNDNESS-LOG 2026-07-15, wikipedia-ios)

A report today carries what the scan **saw** (`functions`). What it **couldn't see** — the κ-coverage
ledger of uncovered packages/modules — is printed to stderr at scan time and evaporates. So every
report-consuming verb answers over a report that silently *reads as total*:

- `privacy-manifest --verify` on wikipedia-ios's app target said `ok: true, underDeclared: []` while the
  app's Location/Photos usage lived in 19 uncovered framework modules. Over-declaration was flagged (the
  safe direction), but the mirror case — an under-declaration hiding in an uncovered module — would read
  as a clean all-clear. A **security-relevant verdict with false confidence**.
- The same shape affects `gains` (a gained effect in an uncovered dep is invisible → "no gains" reads
  clean), `containment`, and any `--gate-json` verdict over partially-covered code.

This violates the family's core contract — *no false all-clear* — not at the scan layer (the stderr
ledger is honest) but at the **artifact** layer: the trust caveat doesn't travel with the report.

## What already exists (audited 2026-07-15, all four engines probed)

| surface | rust | java | swift | ts |
|---|---|---|---|---|
| per-function disclosure | `invisible: [crate]` on the wire | `invisible: [pkg]` on the wire | `invisible: [module]` on the wire | `Unknown` + `unknownWhy` (a *stronger* posture: the fn is marked untrusted, not just annotated) |
| scan-level ledger | stderr only | stderr only | stderr only | stderr only |

So per-function attribution substantially **exists but is unspecced** (three engines emit `invisible`;
ts satisfies the same "never silently pure" obligation through `Unknown`). The missing pieces are the
**envelope-level ledger** and **verb conditionality**.

## The design

### 1. The `coverage` envelope field (§2, NEW, tier-1 additive)

```jsonc
"coverage": {                       // OPTIONAL ⟨0.15⟩ — omitted when nothing is uncovered
  "uncovered": [                    // the κ ledger, exactly the stderr line's content as data
    { "name": "WMF", "calls": 134 },// language-natural name (crate / java package / npm name /
    { "name": "MapKit", "calls": 10 } // swift module), call/import count as the engine counts it
  ]
}
```

- The JSON form of the §7-item-14 ledger the engines already compute — same names, same counts, same
  fail-honest semantics ("their effects are INVISIBLE to the scan — absent, NOT a claim they're pure").
- **Omitted when empty** (the `extensions`-field precedent): a fully-covered scan's report is
  byte-identical to a ⟨0.14⟩ report, so the rung is wire-compatible.
- A pre-0.15 consumer ignores the unknown field (§2 forward-compatibility).

### 2. The per-function `invisible` field (§2, FORMALIZED ⟨0.15⟩)

Pinned as the per-function attribution of the ledger: the uncovered packages **this function
demonstrably calls**. Informative, direct-only (transitive reach is the consumer's join — see 3).
An engine MAY instead mark such a function `Unknown` (the candor-ts posture — strictly stronger,
since `Unknown` participates in gating); an engine MUST do at least one. Engines that emit
`invisible` keep their current names/shape — this formalizes existing behavior, no wire change.

### 3. Verb conditionality (§3.1/§3.3, NEW ⟨0.15⟩)

A report-consuming verb whose verdict could be changed by uncovered reach MUST disclose coverage:

- **`privacy-manifest --verify`**: the JSON verdict gains `"coverage": {"uncovered": N, "modules":
  [...]}` (mirroring the envelope) and — the precise form — `"conditional": true` when any function
  on a *transitive path* the verb examined carries `invisible` (or is `Unknown`), OR the envelope
  ledger is non-empty. Human output appends: `⚠ verdict is conditional on N uncovered modules —
  sensor usage there is invisible to this verify`. **Exit code unchanged** (disclosure, not a gate).
- **`--gate-json`**: the verdict gains an advisory `"coverage"` note (same shape), **verdict-
  preserving** — the ⟨0.9⟩ provable-purity auto-disclosure precedent exactly. A gate does NOT
  fail on uncovered deps (nearly every real scan has some; failing would kill every real gate) —
  the policy author sees the note and decides. `deny Unknown` remains the opt-in strict posture
  (and in ts, uncovered reach already trips it).
- **`gains`**: the JSON gains the same `"coverage"` block from the CURRENT report's envelope; when
  the baseline's ledger differs (a dep became uncovered between scans — itself a signal), disclose
  `"coverageDelta"`. Human TSV unchanged (pinned consumer surface).

Architecture note: engines emit **direct** facts (per-fn `invisible`, envelope `coverage`); verbs
compute **transitive** conditionality from the callgraph they already load. No new propagation
machinery in the scanners.

### 4. What this rung is NOT

- NOT a gate-failure change: coverage discloses; only `deny Unknown` (existing) hard-fails on it.
- NOT a new effect or a report reshape: additive envelope field + formalization of an existing one.
- NOT chaining: `--deps`/CANDOR_DEPS remains the way to *close* a gap; `coverage` is how an
  unclosed gap *travels*.

## Conformance

**PART 4s (tier 1)** pins four-way: (a) a scan with an uncovered dep emits the `coverage` envelope
field naming it (count ≥ 1) and the fully-covered scan omits the field; (b) the per-function
disclosure exists (`invisible` non-empty OR the fn reads `Unknown`); (c) `privacy-manifest` (swift)
and `--gate-json` (all four) carry the coverage note when the ledger is non-empty, and the gate
VERDICT/exit is unchanged by it (verdict-preserving pinned).

## Versioning

Tier-1 additive (a new optional §2 field + formalizing an existing informative one) → the 0.15 rung.
Rides the held train: engines implement now (unversioned, publish held with the 0.14.2 batch); at
ship time either 0.14.2 (engines) + 0.15 (spec floor) split into two releases, or one combined 0.15
cut — Tom's call at ship time.
