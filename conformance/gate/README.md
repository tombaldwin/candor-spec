# gate-verdict fixture (SPEC §3.3 ⟨0.8⟩)

A minimal, STATIC policy violation for the `--gate-json` verdict differential (run.sh PART 12):
`app.Store.save` performs `Fs`, which `policy` (`deny Fs app`) forbids → one AS-EFF-006, exit 1.
The pure `add` must not appear in the verdict.

Only `java/` is populated today — candor-java is the reference engine on spec 0.8. Sibling
`rust/`, `ts/`, `swift/` fixtures land as each engine implements `--gate-json` and reaches 0.8,
at which point PART 12 becomes a full cross-engine differential (the ladder; SPEC §"Versioning policy").
