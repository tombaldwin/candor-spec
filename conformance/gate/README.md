# gate-verdict fixture (SPEC §3.3 ⟨0.8⟩)

A minimal, STATIC two-rule violation for the `--gate-json` verdict differential (run.sh PART 12), in
every language: `save` performs `Fs`, which `deny Fs` forbids → AS-EFF-006, effects `{Fs}`; and its
path is a PARAMETER, so `allow Fs /var/data` cannot be certified → AS-EFF-008 (fail-closed), effects
`{Fs}`. Exit 1; the pure `add` must not appear in either.

All four engines implement `--gate-json` and declare spec 0.8, so PART 12 is a full cross-engine
differential: `java/` (bytecode, compiled first), `rust/` (a crate), `ts/`, `swift/` — every engine's
verdict must agree on `ok:false · AS-EFF-006 · save · {Fs}` (fn compared by leaf name, which is
language-natural per §3.1).
