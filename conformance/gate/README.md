# gate-verdict fixture (SPEC §3.3 ⟨0.8⟩)

A minimal, STATIC policy violation for the `--gate-json` verdict differential (run.sh PART 12), in
every language: `save` performs `Fs`, which `policy` (`deny Fs`) forbids → one AS-EFF-006, effects
`{Fs}`, exit 1. The pure `add` must not appear.

All four engines implement `--gate-json` and declare spec 0.8, so PART 12 is a full cross-engine
differential: `java/` (bytecode, compiled first), `rust/` (a crate), `ts/`, `swift/` — every engine's
verdict must agree on `ok:false · AS-EFF-006 · save · {Fs}` (fn compared by leaf name, which is
language-natural per §3.1).
