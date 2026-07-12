# The query command-line grammar — one shape, four engines

_Design doc. Status: **drafted** (2026-07-12), from the "why do engines differ in grammar?" review. Proposes
pinning the read-only query CLI grammar (§3.1/§3.3) so `candor where Net` means the same invocation in every
language — the CLI counterpart of the item-10 cross-language query-shape pin. **A spec 0.10 candidate** (a
tier-2 promotion, byte-compatible with 0.9); the version bump + ship is Tom's call._

## Why

The spec pins the query **shapes** (§3.1 — the JSON `show`/`where`/`path`/… output is identical cross-engine)
and the scanner **flags** (§3.3 — `--policy`/`--json`/`--version`/`--agents` mean the same everywhere). But it
never pinned the query **invocation grammar** — the arg order, how the report is located, how JSON is
selected. Predictably, an unpinned surface drifted. Four independent divergences today:

| divergence | Rust (`candor-query`) | TS (`candor-ts-query`) | Java (`candor`) | Swift (`candor-swift`) |
|---|---|---|---|---|
| **report** | discovered from `.candor/` (wrapper) | explicit **prefix** | explicit **`.json` path** | explicit **prefix** |
| **JSON** | trailing `0\|1` sentinel | trailing `[0\|1]` sentinel | `--json` flag | `--json` flag |
| **policy** | optional positional | optional positional | optional positional | **required** positional (`fix`) |
| **front-end** | `candor` (discovers) | raw binary only | raw binary only | raw binary only |

So the documented opener — `candor where Net`, `candor path <fn> Net` (the one-pager, the cold-repo demo, the
tab-completion) — is only true on Rust. A TS or Java user who types the documented command gets an error. That
is the exact worst case for the skeptical, IDE-less senior dev the whole top-of-funnel is aimed at: the tool
fumbles the first command. It also means the cross-engine tab completion has to carry per-engine grammar
branches — needing a workaround in the tooling is the tell that the surface itself should be uniform.

The flag *names* are already consistent (`--json`, `--policy`, `--strict`, `--include-unknown` agree
everywhere). This is a **shape** pin, not a rename.

## The canonical grammar

One form, for any query verb an engine exposes:

```
<query-cmd> <verb> <verb-args…> [--report <locator>] [--policy <file>] [--json] [--strict] [--include-unknown]
```

Three rules make it uniform:

**1. The report is DISCOVERED by default; `--report` overrides.**
With no `--report`, the engine walks UP from the CWD for a `.candor/` directory and uses its `report` prefix —
the same mechanism §3.4 already defines for `.candor/config` discovery (a `CANDOR_REPORT` env var overrides,
mirroring `CANDOR_CONFIG`). `--report <locator>` overrides discovery, and `<locator>` resolves by ONE shared
rule that subsumes all three of today's forms:
  - a **directory** → `<dir>/.candor/report` (the prefix inside it);
  - a path ending in a report suffix (`.json`) → that **full report path** (Java's current form);
  - otherwise → a **prefix** (`<prefix>.<crate>.<backend>.json`, TS/Swift's current form).

So `candor where Net` (discovered), `candor where Net --report .` (dir), `candor where Net --report
.candor/report` (prefix), and `candor where Net --report out/report.lib.jvm.json` (path) are all valid and
equivalent. Making the report a **flag** — not a leading positional — is what removes the ambiguity that a
leading-positional report would create (is the first token after `where` the report or the effect?). The verb
args are always positional and never shadowed.

**2. Verb args are positional, in a pinned order** (unchanged from §3.1's shapes — this fixes the *surface*
around them):

| verb | args |
|---|---|
| `where` | `<Effect>` |
| `show` `callers` `impact` | `<fn>` |
| `path` `whatif` `fix` | `<fn> <Effect>` |
| `map` `reachable` `blindspots` `fix-gate` `unverified` | _(none)_ |
| `containment` | `[<baseline-locator>]` |
| `diff` `gains` | `<current> <baseline>` — two locators, in that order (§3.1) |

`diff`/`gains` are the deliberate exception to rule 1: they are inherently comparative, so they take **two
positional locators** rather than one discovered report. Everything else discovers.

**3. `--json` selects JSON; `--policy <file>` supplies a policy.**
The positional `0|1` JSON sentinel is retired (kept as a deprecated, undocumented alias during the migration —
see below). Policy is always the `--policy <file>` flag (falling back to `CANDOR_POLICY` then `.candor/config`,
exactly as the scanner surface §3.3 already does), never a positional — which also fixes Swift's odd *required*
positional policy on `fix`.

### Scope: conditional on exposing the verb

§3.1 queries are **SHOULD**, not MUST — an engine need not expose every verb (Swift ships only
`fix`/`fix-gate`/`unverified`). The grammar pin is **conditional**: *for each query verb an engine DOES expose,
it MUST accept the canonical grammar.* Swift keeps its three verbs but drives them the canonical way (discovery
+ `--report`, `--policy` as a flag). The fleet engine (`candor-agents`) is a different surface (scan/observe/
drift/guard over transcripts, not report queries) and is out of scope here — though it already follows the
shared flag conventions (`--json`/`--policy`/`--strict`).

## The front-end name (SHOULD) — one dispatcher, not four collisions

The grammar above is what conformance pins, whether it's served by a raw binary or a wrapper. But the bare
**`candor`** *name* needs a single owner: if candor-ts (npm), candor-rust, candor-java, and candor-swift each
shipped a `candor` binary, they'd collide on `PATH` — last install wins — and each is a *language-specific*
engine, so a mixed setup would silently run the wrong one. That is the exact "wastes your time / does the
wrong thing" failure the product is built against.

So each engine keeps its **qualified** name (`candor-query`/`candor-scan`, `candor-ts-query`/`candor-ts`,
`candor-java`, `candor-swift`), and the bare `candor` is a single language-aware **dispatcher** (in the
umbrella repo, `bin/candor`). Because the grammar is uniform, routing is deterministic: a **query** goes to
the engine whose backend the discovered report declares (`.scan`/`.lint` → Rust, `.JS` → TS, `.jvm` → Java,
`.Swift` → Swift); a **scan** goes to the engine whose manifest the target holds (`Cargo.toml` → Rust,
`package.json`/`tsconfig.json` → TS, Gradle/Maven/`*.java` → Java, `Package.swift` → Swift). Ambiguity (a
polyglot report or project) and a missing engine are **loud errors**, never a silent wrong-engine run. In the
common single-engine environment there's no collision and the dispatcher just finds the one engine present.
This is ergonomics (a SHOULD), separable from the REQUIRED grammar.

## Back-compat & phasing

The pin is **additive** — no engine breaks:
- Every engine already accepts `--json`; adding discovery + `--report` to the raw binaries is new *accepted*
  behavior, not a removal.
- The old forms stay accepted as **deprecated aliases** through the 0.10 line: a leading-positional report (if
  the first token resolves to a report), the `0|1` sentinel (Rust/TS), a positional policy. Each emits a
  one-line deprecation note to stderr. They are removed at the next **breaking** (major) bump, not before.

So a 0.9 report and verdict are byte-identical under 0.10 (tier 1 untouched), and every 0.9 invocation still
runs — you just also get the uniform grammar. This is the same move as 0.9 itself: promote an
already-shipped-but-unpinned tier-2 surface into the contract without touching the interop floor.

**Version:** a **minor** bump — a previously-unspecified tier-2 surface promoted to required → **spec 0.10**,
floor ratchets, every engine implements it. (Per the §"Conformance tiers" rule: "a tier-2 addition promoted to
required bumps the minor.") Not a ship until Tom says ship.

## Paste-ready SPEC text — new §3.3.1

> ### 3.3.1 The query command-line grammar (REQUIRED for any exposed query verb) ⟨0.10⟩
>
> §3.1 pins the query **names and JSON shapes**; this pins the **invocation** around them, so a query is driven
> identically in every language. For each §3.1 verb an engine exposes, it MUST accept:
>
> ```
> <cmd> <verb> <verb-args…> [--report <locator>] [--policy <file>] [--json] [--strict] [--include-unknown]
> ```
>
> - **Report resolution.** With no `--report`, the engine discovers the report by walking UP from the CWD for a
>   `.candor/` directory and using its `report` prefix (the §3.4 discovery mechanism; `CANDOR_REPORT`
>   overrides). `--report <locator>` overrides discovery. A `<locator>` resolves by one rule: a **directory** →
>   `<dir>/.candor/report`; a path ending `.json` → that **full report path**; otherwise a **prefix**. The
>   comparative verbs `diff` and `gains` instead take two positional locators, `<current> <baseline>`, in that
>   order (§3.1).
> - **Verb args** are positional in the §3.1 order: `where <Effect>`; `show`/`callers`/`impact` `<fn>`;
>   `path`/`whatif`/`fix` `<fn> <Effect>`; `map`/`reachable`/`blindspots`/`fix-gate`/`unverified` none;
>   `containment [<baseline>]`.
> - **`--json`** selects JSON output (stdout MUST then be pure JSON, per §3.3). **`--policy <file>`** supplies a
>   policy, honouring `CANDOR_POLICY` then `.candor/config` when absent (§3.3/§3.4) — never a positional.
>   **`--strict`** (on `unverified`) and **`--include-unknown`** (on `callers`) keep their §3.1 meaning.
>
> Flag names and help wording are consistent across engines (§3.3). An engine MAY continue to accept prior
> positional forms (a leading report, a `0|1` JSON sentinel, a positional policy) as **deprecated** aliases with
> a stderr deprecation note; they are removed no earlier than the next breaking bump. An engine SHOULD ship an
> ergonomic entry point named `candor` that discovers the report and unifies scan and query.

And §7 item 5 gains a clause (for `spec ≥ 0.10`): *"…and, for an engine declaring `spec ≥ 0.10`, every exposed
§3.1 query verb driven through the **canonical query grammar** of §3.3.1 — report discovery with `--report`
override, `--json` selection, `--policy` as a flag — verified by conformance PART 17."*

## Conformance — new PART 17 (TIER 2)

Pins that the grammar is uniform, four-way, and that discovery and explicit `--report` agree. For each present
engine that exposes `where` (the representative single-report verb):

1. **Discovery ≡ explicit.** From a CWD holding `.candor/report*`, run `<cmd> where Net --json` (discovered).
   Then run the same with `--report <dir>`, `--report <prefix>`, and `--report <path>`. Assert all four
   invocations of that engine produce **byte-identical** JSON.
2. **Cross-engine agreement.** Assert the discovered `where Net --json` JSON agrees across all four engines
   (leaf-normalized, as PART 5 does) — i.e. the *grammar* change did not perturb the *shape*.
3. **`--json` is the selector.** Assert `where Net` without `--json` is human/non-JSON and `where Net --json`
   is pure JSON on stdout (mirrors §3.3).
4. **Policy is a flag.** For `fix-gate` (present on all four): assert `fix-gate --report <r> --policy <p>
   --json` produces the PART-12b remedy, and that the deprecated positional policy still resolves with a
   deprecation note (during the migration window).
5. **Deprecated aliases still resolve.** Assert the old leading-positional-report form and the `0|1` sentinel
   (Rust/TS) still produce the same JSON as the canonical form + emit a stderr note. (Dropped from the suite
   when the aliases are removed at the next major.)

Style mirrors PART 12/12b: build each engine, invoke, compare JSON via an inline `python3` leaf-normalizer,
print a labeled MATCH/DIVERGE table, exit 1 on mismatch. Tagged **[TIER 2]** — the report and verdict are
untouched; this pins a tool surface.

## Per-engine impact

| engine | change |
|---|---|
| **Rust** | Raw `candor-query` accepts `--report` + discovery (today only the wrapper discovers); `--json` replaces the `0\|1` sentinel it passes (sentinel kept as deprecated alias); `--policy` flag on `whatif`/`fix`. Front-end `candor`: **done**. |
| **TS** | `candor-ts-query` discovers by default + accepts `--report`; `--json` canonical (already accepts), `0\|1` sentinel deprecated; `--policy` flag. Add a `candor` npm bin. |
| **Java** | `candor` query mode discovers by default + accepts `--report` (today the `.json` path is a required leading positional → becomes `--report <path>`); already uses `--json`; `--policy` flag on `whatif`/`fix`. Add a `candor` launcher (has the name via jar; wire discovery). |
| **Swift** | `fix`/`fix-gate`/`unverified` discover + accept `--report`; `--policy` becomes a flag (today a *required* positional on `fix`). Keeps its three-verb scope (the other verbs stay unexposed — allowed). |
| **Agents** | Out of scope (fleet surface, not report queries); already flag-consistent. |
| **conformance** | Existing PARTs' invocations migrate to the canonical grammar (or exercise the deprecated-alias path explicitly); add PART 17. |
| **spec** | Add §3.3.1, the §7-item-5 clause, envelope → 0.10, CHANGELOG. |
| **completion** | Collapses the per-engine grammar branches to one grammar (the reason to hold the completion polish until this lands). |

## Phasing

- **P1** — land §3.3.1 + PART 17 + the four engines' additive grammar (discovery + `--report` + `--json` +
  `--policy` flag), old forms deprecated-but-accepted. Bump to 0.10 on Tom's ship.
- **P2** — the `candor` front-end name parity (ts/java/swift), a SHOULD.
- **P3** — a future major removes the deprecated aliases (`0|1` sentinel, positional report/policy) and drops
  the PART-17 alias checks.

The product point this closes: `candor where Net` becomes a true statement in every language — the CLI finally
matches the "one contract, four engines" promise the reports and verdicts already keep, and the docs, the
muscle memory, and the tab completion all become uniform instead of Rust-only.
