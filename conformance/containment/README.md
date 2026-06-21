# containment differential fixture (SPEC §6.1 + AS-EFF-010)

A shared layered fixture proving the `containment` query means the same thing in every engine that
implements it. Two layers, two boundary effects:

- `repo` performs **Fs** (file read) in two functions — the proper home of that effect.
- `svc` performs **Net** (socket connect) in `current` and `base`.
- `current` ALSO has `svc` perform **Fs** (the architecture drift); `base` does not.

Both effects appear in both states so the common-layer prefix is stable at `c` / crate-root.

Expected, identical across engines:

- **report mode** (`containment current`): `Fs` 66% / 2 layers / owner `repo` / `{repo:2, svc:1}`;
  `Net` 100% / 1 layer / owner `svc` / `{svc:1}`; no ambient.
- **ratchet mode** (`containment current base`): `leaks = ["Fs → svc"]`, `cleanups = []`, exit 1
  (AS-EFF-010 — a boundary effect entered a layer it wasn't in).

Engines: candor-java (file-based `containment`) vs candor-query/Rust (prefix-based, also the path
candor-swift's analyze-only reports are queried through). candor-ts has no `containment` command.
