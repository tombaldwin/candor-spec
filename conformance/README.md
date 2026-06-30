# Cross-implementation conformance suite

An **executable** differential for the candor spec. Each case is a function written in each engine's
language — Rust (`rust/src/lib.rs`), Java (`java/Cases.java`), TypeScript (`candor-ts/Cases.ts`) and Swift
(`candor-swift/conformance/Cases.swift`) — with equivalent semantics; the runner analyses each with its
native engine ([candor-scan](../../candor-rust) syntactic Rust, [candor-java](../../candor-java) JVM
bytecode, [candor-ts](../../candor-ts) TS compiler API, [candor-swift](../../candor-swift) SwiftParser) and
asserts they all infer the **same** effect set, which is also the one the spec mandates (`expected.json`).
The Rust + JVM engines are always required; the TS + Swift engines join when present (and a present-but-broken
engine FAILS the run, never reads as skipped).

Because the expected set *is* the spec answer, one run does double duty:

- **conformance** — each engine vs the spec (`SPEC.md §1` vocabulary, `SEMANTICS.md` propagation), and
- **differential** — the independent engines vs each other (a divergence is a bug in one).

The runner checks many parts (the `[n]` labels in its output) — covering every cross-language command.
The load-bearing ones:

1. **Effect sets** (`rust/` + `java/` + `expected.json`) — every engine infers the same effects for
   equivalent functions; plus a callgraph-completeness check and a §4 honesty invariant on each report.
2. **Policy verdict** (`policy/`) — given the *same* `deny`/`pure` policy text and the *same* layered
   fixture, the engines reach the same `whatif` verdict: the same violating functions, the same `ok`,
   **and** the same blast radius (the affected set).
3. **Rewire verdict** (`rewire/`) — given the *same* de-wiring (a function drops a call), the engines'
   `rewire` flags the same dropped edge.
4. **Policy-DSL grammar** (`policydsl/`) — the engines that expose `parsepolicy` parse the *same*
   `CANDOR_POLICY` battery (every `deny`/`pure`/`allow`/`forbid` form plus the edge cases — `deny Unknown`,
   a scope after the first non-effect token, an unsupported `allow` effect) into the *same* rule set. This
   is the executable form of **SPEC §6.2**: the gate's grammar means the same thing in each language.
   Companion **literal- and scope-matching** parts then assert the engines AGREE on the *applied* match —
   the four-way `--policy` verdict differential (host:port allow, `::`-vs-`.` scope segmentation, basename
   Exec / path-boundary Fs / `schema.*` Db matching), the `tables` extraction battery, the Exec-head and
   Net host:port surfaces.
5. **Query shape** (`show`/`where`/`callers`/`map`/…) — the engines emit the *same JSON shape* (the keys
   an agent parses) for the read-only graph queries. The function-name *values* are language-natural
   (`a::b` vs `a.b`), so this pins structure, not content — catching a field rename or a restructured
   query (**SPEC §3.1**). The core graph queries are candor's value surface; their shape must not drift.
6. **Containment** (`containment/`) — given the *same* layered fixture, the engines agree on the
   `containment` diagnostic (each boundary effect's containment %, layer count, owner layer, and
   placement) **and** on the **AS-EFF-010 ratchet** verdict: the same leak (`Fs → svc`) and the same
   exit 1 when an effect drifts into a new layer. This is the executable form of **SPEC §6.1** — the
   architecture-drift gate means the same thing in each language. (candor-java implements `containment`
   file-based; candor-query/Rust prefix-based, also serving candor-swift's reports; candor-ts has none.)
7. **κ-coverage ledger** (SPEC §7 item 14), the **`--agents`** self-describing contract (§7.11), an
   **unreadable-policy / unknown-flag** exit-2 check (§6.2), the **unknownWhy vocabulary** + **dispatch
   frontier** (§4/§3.1 ⟨0.7⟩), and two generated batteries — an effect × indirection matrix and a
   gate-masking differential — round out the suite.

Parts 2–7 are what a per-language ruleset (CodeQL/Semgrep/ArchUnit) structurally can't match: not just
"rules exist for both languages", but a **machine-checked guarantee that the same architecture gate, the
same blast radius, and the same de-wiring check mean the same thing in each.** That cross-language
consistency is candor's moat — and it's a test, not a claim.

## Run

```sh
bash conformance/run.sh
```

Repos are assumed siblings of `candor-spec`. Override with `CANDOR=…` / `CANDOR_JAVA=…`, or skip the build
by pointing at pre-built binaries:

```sh
CANDOR_SCAN_BIN=/path/to/candor-scan CANDOR_JAVA_JAR=/path/to/candor-java-all.jar bash conformance/run.sh
```

Exit 0 iff every case matches in **both** engines. Output is a table; a `DIVERGE` row means the engines
disagree, a `BOTH-OFF` row means they agree with each other but not the spec.

CI runs this on every change to candor-spec (`.github/workflows/conformance.yml`): it checks out both
engine repos from their `main` branches, builds each, and runs the differential — so a classifier change
that breaks cross-impl parity turns the spec's own CI red. After landing a classifier change in an engine,
dispatch the workflow manually (or open a PR) to re-check.

## Adding a case

1. Add a function `foo` to **both** `rust/src/lib.rs` and `java/Cases.java` with the same intended effect.
   Match the function name exactly — the runner pairs cases by the bare function name.
2. Add `"foo": ["Effect", …]` (its full **transitive** inferred set; `[]` for pure) to `expected.json`.

## Scope: the std-only core

The cases use only each language's standard library, so they need no dependency management and exercise the
vocabulary both engines must agree on without external calibration: **Fs, Net, Exec, Env, Clock**, the
**Unknown** trust contract (an unanalysable call — a fn-pointer field in Rust, reflection in Java), purity,
multi-effect union, and transitive propagation across a call.

Deliberately **out of scope here** (each is covered by the engines' own unit/calibration tests):

- **Db / Rand / Log** — Java reaches these in the JDK (`java.sql`, `java.util.Random`, `java.util.logging`)
  but Rust needs a crate (`rusqlite`, `rand`, `log`/`tracing`), so a *std-only* pairing isn't possible.
- **Clipboard** — Java has it in AWT; Rust needs `arboard`.
- **Ipc** — structurally asymmetric: Rust distinguishes a Unix-domain socket by *type* (`std::os::unix::net`),
  but on the JVM the family is a runtime *argument* to `SocketChannel.open`, invisible to type-based
  classification (so a JVM Unix socket reads as `Net` — a documented, justified asymmetry).
