# Cross-implementation conformance suite

An **executable** differential for the candor spec. Each case is a function written in **both** Rust
(`rust/src/lib.rs`) and Java (`java/Cases.java`) with equivalent semantics; the runner analyses each with
its native engine — [candor-scan](../../candor) (Rust, syntactic) and [candor-java](../../candor-java)
(JVM bytecode) — and asserts both infer the **same** effect set, which is also the one the spec mandates
(`expected.json`).

Because the expected set *is* the spec answer, one run does double duty:

- **conformance** — each engine vs the spec (`SPEC.md §1` vocabulary, `SEMANTICS.md` propagation), and
- **differential** — the two independent engines vs each other (a divergence is a bug in one).

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
