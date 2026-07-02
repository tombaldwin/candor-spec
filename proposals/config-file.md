# `.candor/config` — a checked-in configuration file

Status: **DONE — all four engines implement it; normative as SPEC.md §3.4** (an additive amendment within
0.8 — configuration, not the wire contract, so the spec string is unchanged). Conformance PART 13 pins
discovery, precedence and the fail-closed posture per engine (config-gate=1 / env-override=0 /
typo-config=2). Additions beyond this proposal, made during the roll: target-anchored discovery (walk up
from the scan target; CANDOR_CONFIG overrides), fail-closed on configured-but-unusable, bare value keys =
enabled-with-empty, unknown keys warned (typo protection), inert-if-unimplemented known keys.

## Motivation

Today candor is driven by `CANDOR_*` environment variables (`CANDOR_POLICY`, `CANDOR_BASELINE`,
`CANDOR_STRICT`, `CANDOR_NO_AMBIENT`, `CANDOR_CLOSED_WORLD`, `CANDOR_DEPS`, `CANDOR_TAINT`) plus the
`.candor/` directory convention (`baseline.json`, the report). The only declarative, checked-in file is the
policy. So CI needs env wiring, and the configuration doesn't travel with the code. A single checked-in
`.candor/config` fixes both: CI becomes "point at the repo," and the config is versioned with the source.

## Format

One `key value…` per line; `#` starts a comment (stripped to end-of-line, inline too); blank lines ignored —
the same lexical rules as the §6.2 policy grammar. Keys are lower-case and map **1:1** to the env vars:

| key | env var | value |
|---|---|---|
| `policy` | `CANDOR_POLICY` | path to a §6.2 policy file |
| `baseline` | `CANDOR_BASELINE` | path to a baseline report (the AS-EFF-005 ratchet) |
| `strict` | `CANDOR_STRICT` | a scope (conformance / AS-EFF-001–003) |
| `no-ambient` | `CANDOR_NO_AMBIENT` | a scope (AS-EFF-004) |
| `closed-world` | `CANDOR_CLOSED_WORLD` | boolean |
| `taint` | `CANDOR_TAINT` | boolean |
| `deps` | `CANDOR_DEPS` | whitespace-separated report paths (a path LIST) |

Booleans are truthy on `true`/`1`/`yes` or a **bare key** (no value); absent or `false` is off. The file
lives at `.candor/config`, or the path in `CANDOR_CONFIG`.

```
# .candor/config
policy        arch.policy
baseline      .candor/baseline.json
strict        com.acme.domain
closed-world  true
deps          ../lib-a/.candor/report.json  ../lib-b/.candor/report.json
```

## Precedence (highest first)

**CLI flag → `CANDOR_*` env var → `.candor/config` → built-in default.**

So a checked-in config is the *default* for the repo, and an env var or flag still overrides it for a
one-off run (e.g. `CANDOR_POLICY=/tmp/other.policy candor …` on a machine, without editing the file). This is
the natural layering: the flag is the most explicit, the env var is the one-off, the file is the durable
default.

## Not the effect contract

`.candor/config` is *configuration*, not part of the report/effect wire contract — it changes no field an
interoperating consumer reads. So it does not advance the spec version; it is a cross-engine convention every
engine implements (like the §3.3 command surface), pinnable by a small conformance parse-agreement check
(feed the same `.candor/config` to every engine, assert they resolve the same values — the `parsepolicy`
pattern).

## Rollout

1. candor-java — `Config` layer (`.candor/config` / `$CANDOR_CONFIG`), precedence flag→env→config→default,
   wired into every gate-mode resolution. **Done** (ConfigTest + a CLI end-to-end test).
2. candor-scan / candor-ts / candor-swift — the same parse + precedence.
3. Conformance parse-agreement check; then document as a normative §config.
