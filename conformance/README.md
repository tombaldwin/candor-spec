# Cross-implementation conformance suite

An **executable** differential for the candor spec, across the **four code engines**: each case is a
function written in each engine's language with equivalent semantics, and the runner analyses each
with its native engine and asserts they agree — with each other, and with the answer the spec mandates
(`expected.json`). A `DIVERGE` row is a bug in one engine; a `BOTH-OFF` row means the engines agree
with each other but not the spec.

The four fixture files (the runner pairs cases across them by bare function name):

| engine | fixture | lives in |
|---|---|---|
| candor-scan (Rust, syntactic) | `rust/src/lib.rs` | this repo, `conformance/rust/` |
| candor-java (JVM, ASM bytecode) | `java/Cases.java` | this repo, `conformance/java/` |
| candor-ts (TS compiler API) | `Cases.ts` | the candor-ts repo root |
| candor-swift (SwiftParser) | `conformance/Cases.swift` | the candor-swift repo |

Because the expected set *is* the spec answer, one run does double duty: **conformance** (each engine
vs SPEC §1/SEMANTICS propagation) and **differential** (the independent engines vs each other). That
machine-checked "the same gate means the same thing in each language" is what a per-language ruleset
(CodeQL/Semgrep/ArchUnit) structurally can't match — and it's a test, not a claim.

## The sixteen parts

The `[n]` labels in the runner's output, in run order:

1. **Effect sets** (`rust/` + `java/` + `expected.json`) — every engine infers the same effects for
   equivalent functions, plus a callgraph-completeness check; **1c** asserts the SPEC §4 honesty
   invariant on each emitted report (uncertainty propagates caller-ward, never silently dropped).
2. **Policy verdict** (`policy/`) — same `deny` policy + layered fixture ⇒ the same `whatif` verdict:
   the same violating functions, the same `ok`, the same blast radius.
3. **Rewire verdict** (`rewire/`) — the same de-wiring (a function drops a call) ⇒ every engine's
   `rewire` flags the same dropped edge.
4. **Policy-DSL grammar** (`policydsl/`) — the engines that expose `parsepolicy` parse the same
   `CANDOR_POLICY` battery into the same rule set (the executable SPEC §6.2). Its lettered siblings
   pin the *applied* surfaces: **4b** the SPEC §2 SQL `tables` extraction vector battery, **4c** the
   κ-coverage ledger (SPEC §7 item 14 — every engine names an unlisted-but-called package), **4d** the
   Exec-head rule (a literal that is only an *argument* must not refine), **4e** the Net `host[:port]`
   literal surface.
5. **Query shapes** — `show`/`where`/`callers`/`map` emit the same JSON keys in every engine
   (SPEC §3.1); function-name *values* stay language-natural, so this pins structure, not content.
6. **The third engine, live** (candor-ts) and **6c the fourth** (candor-swift) — the derivability
   proof: each later engine runs the same PART 1 oracle on its own fixture file.
7. **Self-describing engines** — `--agents` prints the embedded, version-headed agent contract
   (SPEC §7 item 11).
8. **Unreadable policy / unknown flag ⇒ exit 2** — a configured-but-unreadable gate fails the run
   loudly (SPEC §6.2), never a silent gateless green.
9. **`unitKind`** — the optional §2 field: non-function units named, plain functions omit it.
10. **`unknownWhy` vocabulary** — every emitted reason uses the four canonical kinds and every
    `dispatch:` carries the normative `owner.member` detail (SPEC §4 ⟨0.7⟩).
11. **Containment** (`containment/`) — the §6.1 dispersion diagnostic and the AS-EFF-010 ratchet
    verdict agree (candor-java file-based; candor-query prefix-based, also serving candor-swift's
    reports; candor-ts exposes no containment command).
12. **Gate verdict** — `--gate-json` re-emits the policy verdict as machine JSON that agrees with the
    exit code; `ok` and the `{rule, fn, effects}` set are pinned (SPEC §3.3 ⟨0.8⟩). **12b the FIX-GATE
    remedy** (`fix/`, integrations/FIX-SPEC.md) — the remedial companion: the same orderflow under `deny
    Net domain` yields the same boundary fix in every engine (candor-query/java/ts), leaf-normalized —
    the same direct site, pure span, hoist target, layer and `cleanHoist`. Where PART 12 pins *that* a
    boundary was crossed, 12b pins *where the effect belongs*.
13. **`.candor/config`** — discovery, precedence and the fail-closed posture agree (SPEC §3.4):
    config-gate ⇒ 1, env-override ⇒ 0, typo'd config ⇒ 2.
14. **Chaining** (`CANDOR_DEPS`, SPEC §2) — join-inherit across a report boundary, stale-report
    downgrade to `Unknown`, and the empty-report-is-a-purity-claim coverage rule.
15. **Baseline guard, four-way** (SPEC §7 item 5 + the §2.1 stale posture) — every engine's
    AS-EFF-005 guard pinned on five cells: gain → `[AS-EFF-005]` + exit 1; clean → 0; absent file →
    note + 0 (guard inactive); doctored producing version → exit 2 WITHOUT evaluating; a
    configured-but-empty value → exit 2 (a declared ratchet naming no file is a broken gate, not an
    inactive one). Comparison *queries* disclose the mismatch and still answer. (The ts/swift/scan
    guard surfaces landed 2026-07-10; the item-5 MUST is satisfied, not narrowed.)
16. **Applied `deny Unknown` / `pure`-vs-`Unknown` / `forbid` layering** — the remaining §6/§6.2
    verdicts agree, including nested-scope segment matching.
17. **Query CLI grammar** (§3.3.1) [TIER 2] — every engine drives a query the same way: the report
    **discovered** from a `.candor/` ancestor ≡ passed as `--report <locator>` (dir / prefix / `.json`
    path) ≡ the deprecated leading-positional form, `--json` selecting JSON, `--policy` a flag not a
    positional. Rust+Java always; TS/Swift when present (Swift shares only `fix-gate`, so it joins the
    policy-flag leg + a discovery check). Pins that the pre-0.10 positional forms still resolve (a stderr
    deprecation note, identical JSON), so the rung stays byte-compatible with 0.9. Staged 0.10.

Between parts 9 and 10 run four **generated batteries** (unnumbered): an effect × indirection matrix
(`gen_differential.py`), the gate-masking differential (`gen_masking.py` — the fail-closed AS-EFF-008
evasion battery), the four-way policy literal/scope-matching differential (`gen_policy_match.py`), and
the ⟨0.7⟩ dispatch-frontier differential (`frontier_differential.py`).

## Run

```sh
bash conformance/run.sh
```

Engine repos are assumed **siblings** of `candor-spec`. Override locations with `CANDOR=…`,
`CANDOR_JAVA=…`, `CANDOR_TS=…`, `CANDOR_SWIFT=…`; skip builds by pointing at pre-built artifacts:

```sh
CANDOR_SCAN_BIN=/path/to/candor-scan CANDOR_QUERY_BIN=/path/to/candor-query \
CANDOR_JAVA_JAR=/path/to/candor-java-all.jar bash conformance/run.sh
```

Exit 0 iff every part matches across every present engine.

**The SKIP discipline.** The Rust + JVM engines are always required. For candor-ts/candor-swift the
runner distinguishes *present* (the checkout exists) from *ok* (its scan produced a report): an
**absent** engine SKIPs loudly, but a **present-and-broken** engine FAILS the run — it must never read
as "not present". `CONFORMANCE_REQUIRE_ALL=1` turns every loud SKIP into a failure (the strict CI
leg), so the four-engine floor can't silently degrade to fewer engines.

## CI — three legs (`.github/workflows/conformance.yml`)

1. **cross-impl-differential** — ubuntu, engine **main tips**, three engines (Rust, JVM, TS; ubuntu
   runners have no swift toolchain, so swift skips loudly). The fast leg, on every push/PR.
2. **four-engine-differential** — macos, main tips, **all four** engines with
   `CONFORMANCE_REQUIRE_ALL=1`: the leg that actually enforces the four-engine floor the spec claims.
3. **released-floor** — weekly + on dispatch, ubuntu, the **released artifacts** (the latest
   candor-java GitHub-release jar + the crates.io candor-scan/candor-query): proves the floor where
   consumers live, not just tip-vs-tip.

After landing a classifier change in an engine, dispatch the workflow (or open a PR) to re-check —
a change that breaks cross-impl parity turns this repo's CI red. (A fourth, non-differential job,
`agents-doc-drift`, pins AGENTS.md to SPEC.md's floor.)

## Adding a case

1. Add a function `foo` with the same intended effect to **all four** fixture files —
   `rust/src/lib.rs`, `java/Cases.java`, the candor-ts repo's `Cases.ts`, and the candor-swift repo's
   `conformance/Cases.swift`. Match the bare function name exactly — the runner pairs cases by it.
2. Add `"foo": ["Effect", …]` (the full **transitive** inferred set; `[]` for pure) to
   `expected.json`.
3. The TS/Swift halves live in the engine repos, so a new case is a two-repo change: land the fixture
   additions there, then the `expected.json` row here (order matters only for CI green-ness; the
   strict leg checks out every repo's main).

## Wiring in a fifth engine

The pattern each later engine followed (candor-ts, then candor-swift):

1. A `CANDOR_<LANG>` env var with a sibling-directory default (`../candor-<lang>`), plus optionally a
   pre-built `*_BIN` override, resolved at the top of `run.sh`.
2. A `Cases.<ext>` fixture in the engine's repo carrying every case, same bare function names.
3. A `<LANG>_PRESENT` / `<LANG>_OK` pair honouring the SKIP discipline above: absent ⇒ loud SKIP
   (a FAIL under `CONFORMANCE_REQUIRE_ALL=1`), present-but-broken ⇒ FAIL.
4. Join each differential in turn — the PART 1 effect-set oracle first (a new `[6x]`-style live leg),
   then grammar/queries/gate as the engine grows the surfaces; the generated batteries pick the engine
   up from its env var.
5. A CI checkout step in each leg (and a toolchain step if the runner lacks one — the swift/macos
   precedent).

## Scope: the std-only core

The cases use only each language's standard library, so they need no dependency management and
exercise the vocabulary every engine must agree on without external calibration: **Fs, Net, Exec,
Env, Clock**, the **Unknown** trust contract (an unanalysable call — a fn-pointer field in Rust,
reflection in Java), purity, multi-effect union, and transitive propagation across a call.

Deliberately **out of scope here** (covered by the engines' own unit/calibration tests):

- **Db / Rand / Log** — Java reaches these in the JDK (`java.sql`, `java.util.Random`,
  `java.util.logging`) but Rust needs a crate (`rusqlite`, `rand`, `log`/`tracing`), so a *std-only*
  pairing isn't possible.
- **Clipboard** — Java has it in AWT; Rust needs `arboard`.
- **Ipc** — structurally asymmetric: Rust distinguishes a Unix-domain socket by *type*
  (`std::os::unix::net`), but on the JVM the family is a runtime *argument* to `SocketChannel.open`,
  invisible to type-based classification (so a JVM Unix socket reads as `Net` — a documented,
  justified asymmetry).
