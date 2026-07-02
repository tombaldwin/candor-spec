# `.candor/config` — a checked-in configuration file

Status: **reference implementation in candor-java** (engine feature at the current spec — reading a config
file changes no report schema / effect vocabulary / AS-EFF code, so it does **not** bump the spec version).
Roll to candor-scan/ts/swift next, then document as a normative §config so every engine agrees.

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
