# The completeness manifest — distinguishing "provably pure" from "never seen" ⟨SHIPPED spec 0.21⟩

> **Status (2026-07-17):** SHIPPED four-way as spec 0.21. `analyzed:{count,digest}` + `unanalyzed:[{path,
> reason}]` in the report envelope; the machine-legible incomplete gate verdict (`{ok:false, incomplete:true,
> unanalyzed}` + exit 2) closing the machine-consumer false-all-clear (Gap 2, the sharp one); Gap 3 (isolated
> pure leaf is a §2.2 node) confirmed compliant four-way (no fix needed). FNV-1a-64 digest, one algorithm
> across engines (values differ — quals differ). SPEC §2 + §3.3.1; pinned four-way in `gen_completeness.py`.
> The `candor verify` dynamic oracle (§3 below) that would CONSUME `analyzed`/`unanalyzed` remains the open
> follow-on (closes sub-case (ii), the misjudgment; the manifest closes (i), the enumeration drop).

Carry the set of functions the scan **analyzed**, so a function's absence from the report can be read as
*provably pure* (analyzed, no effects) rather than ambiguously *pure-or-silently-dropped*.

## The finding (referee pass 2026-07-16, PL-theory angle — `~/candor-paper/REFEREE-REPORTS.md`)

The §2 report **omits pure functions** (a size optimization: a report lists only effectful/`Unknown`
functions). The consuming convention is "**absent ⇒ pure**." But that is a *universal* claim over all
functions the report cannot actually back: a function silently dropped by the analysis (never enumerated —
the cardinal-sin bug class) is **indistinguishable** from a function analyzed and found pure. Worse, the
honesty oracle (RQ1) checks `observed ⊆ inferred ∪ {Unknown}` only over *executed* functions, so a
silently-dropped effectful function that the corpus never runs is (a) claimed pure by omission and (b)
unfalsifiable — an undetectable false-all-clear region *by construction*. The gap between "absent ⇒ pure"
(universal) and "H checked on executed only" (existential refutation) is exactly where a false all-clear
can live undetected.

## What already exists (audited 2026-07-16 across all four engines — MORE than the first draft assumed)

The grounding audit changed this design substantially. The analyzed universe is **not new** — candor already
records it, normatively, four-way, and it is already load-bearing:

- **SPEC §2.2 already mandates it.** "The sidecar records EVERY project function's edges, **including pure
  ones** … what lets a consumer answer 'who transitively calls X?' for a function that is currently pure."
  Every engine implements it and says so in-source: rust (`for q in &all … EVERY analyzed function …
  including a LEAF … as an empty list`), java (`ReportWriter`: `SPEC §2.2: EVERY analyzed method is a key — a
  LEAF … gets an empty list`), ts (`§2.2 … lists every project fn INCLUDING pure`), swift (`SPEC §2.2 lists
  EVERY analyzed fn, pure leaves included`). Each fixed exactly the "uncalled pure leaf went invisible" bug
  already (rust's nix `unistd::pipe` case).
- **It is already load-bearing.** The AS-EFF-005 baseline guard ⟨0.16⟩ keys pure→effectful existence on
  "callgraph node with ∅ baseline effects" (`gate.rs`), and `whatif`/`callers`/`rewire` rely on it for blast
  radius. So `callgraph nodes = the analyzed set` is a battle-tested contract, not an aspiration.
- **Incompleteness is already disclosed and already fails the gate** (rust confirmed): unparsed source files
  are named on stderr ("effects in them are NOT in this report") and, when a policy is configured, a parse
  failure makes the gate FAIL non-zero (`had_parse_failure` — "a gateless-green over unanalyzed code is a
  false-pure hole").

So the referee's "absent ⇒ pure is unbacked" critique is only true for a consumer reading the **bare report**
(the §2 envelope) *without* loading the §2.2 sidecar. With the sidecar, absent-from-report-but-a-callgraph-
node = **analyzed-pure**, and absent-from-both = **never-seen** — the distinction already exists. The real
gaps are three narrower things (below), not the analyzed universe itself.

## The design

**Definition.** `analyzed(f)` ≙ *candor formed an effect judgment for `f`* — it computed `inferred(f)`, a
signature that may be `∅` (pure), an effect set, or `Unknown(reason)`. A function candor never enumerated
(never formed a judgment for) is **not** analyzed. The manifest is the set `{ f : analyzed(f) }`. This is the
predicate the membership table (§2) is defined against; without it "never seen" is fuzzy.

**Scope of the fix (state it precisely — the manifest is necessary, not sufficient, alone).** A false
all-clear has two sub-cases: **(i) an enumeration drop** — candor never judged `f`, yet `f`'s absence reads
as pure; and **(ii) a misjudgment** — candor judged `f` and got `∅` while `f` is actually effectful. The
manifest closes **(i)**: an unenumerated `f` is now *absent-and-unanalyzed* ("never seen"), not silently
pure. It does **not** by itself close **(ii)** — an `analyzed`-and-wrongly-pure `f` still reads pure. What
the manifest does for (ii) is make the "analyzed-pure" claim *checkable*: the honesty oracle (§3) can then
falsify it against runtime behaviour. Manifest (closes (i)) + oracle (closes (ii)) together close the hole;
the manifest alone earns the "absent ⇒ pure" convention for the enumerated set only.

The analyzed universe already rides the **§2.2 callgraph sidecar** (its node set = every analyzed function,
pure leaves included). Do **not** re-emit it. The three genuine gaps are:

### Gap 1 — the report ENVELOPE doesn't summarize the analyzed universe (self-description)

The datum lives in the *sidecar*; a consumer reading the **bare §2 report** or the **`--gate-json` verdict**
(the machine surfaces an agent or CI actually consumes) cannot tell analyzed-pure from never-seen without
also loading and cross-referencing the callgraph. Add a small self-describing summary to the §2 envelope
(and mirror the count in the gate verdict):

```jsonc
"analyzed": { "count": 1420, "digest": "sha256:…" }
```

- `count` = functions analyzed (effectful + pure) → the consumer computes the **pure count** =
  `count − |functions|` and sees that pure functions exist and were *seen*, from the report alone.
- `digest` = a hash over the sorted analyzed-qual set; a compact fingerprint so a report and a **same-engine
  re-scan** agree on the same universe without shipping the list. **Within-engine only** (qualifiers differ
  `::` vs `.`); cross-engine agreement is a conformance concern, not a digest-equality one.
- Omitted only when the engine genuinely cannot enumerate its analyzed set — disclosed, never silently absent.

The full membership set is already the callgraph node set (no new sidecar). The reading, now answerable from
`report envelope + §2.2 sidecar`:

| fn is in… | reading |
|---|---|
| `functions` | determined-effectful or `Unknown` — as today |
| a §2.2 callgraph node, **not** in `functions` | **provably pure** — analyzed, no effects (omission earned) |
| **neither** | **never analyzed** — out of scope; candor makes **no** purity claim |

### Gap 2 — incompleteness is stderr-only, not machine-readable (the sharp, cardinal-sin-facing gap)

Today a parse/read failure is disclosed on **stderr** and fails the gate exit code (rust `had_parse_failure`)
— but it is **not in the report or the `--gate-json` verdict**. So a MACHINE consumer (an agent piping JSON,
a CI reading the verdict) can see `ok: true` while N source files went unanalyzed — the human sees the
stderr warning, the machine does not. This is the exact machine-consumer false-all-clear the motivating
thesis is about, hiding in the *incompleteness* channel rather than the effect channel.

Add a structured **`unanalyzed`** disclosure to the §2 envelope — the units candor could not analyze
(unparsed/unreadable files, deliberately-skipped scopes), with a reason: `unanalyzed: [{ path, reason }]`.

**Grounded status (2026-07-16).** The GATED path is *already correct*: on a parse failure with a policy
configured, rust exits **2** with a stderr reason and writes **no** `--gate-json` verdict — SPEC §3.3.1's
deliberate "on exit 2, NO verdict is written (writing `ok:true/false` would fabricate one)." So the machine
gets a could-not-evaluate exit, which is honest. The genuinely-broken surface is the **bare `--json`
report** (a scan without a gate): it carried the functions but disclosed the dropped files only on stderr,
so a JSON consumer saw a report that *looked* complete. **DONE in rust (reference):** the report envelope now
carries `unanalyzed: [{path, reason}]` (omitted when empty → wire-compatible); `candor-report` round-trip
test + verified end-to-end. Remaining: port to java/ts/swift, the SPEC §2 field, and a conformance PART.

**Open decision (Tom's call — a spec-rule refinement, not blind-implementable).** Should the exit-2
incomplete-analysis path emit a *minimal structured reason* rather than nothing? Today §3.3.1 writes no
verdict on exit 2. An `unanalyzed`-only disclosure (`{ spec, ok:false, incomplete:true, unanalyzed:[…] }`)
would not *fabricate* a verdict — `ok:false` is honest (the gate did not pass) and `unanalyzed` says why —
so a machine could learn *why* the gate couldn't evaluate without parsing stderr. This refines the
"no-verdict-on-exit-2" rule and wants a decision before implementing across the four engines.

### Gap 3 — the §2.2 "every analyzed fn" contract has a residual isolated-leaf hole in some engines

rust and java build the node set as `for q in &all` (every analyzed fn is a key, isolated leaves included).
ts computes the node set as `every caller key ∪ every callee` (scan.mjs) — so a **truly isolated** pure
function (uncalled *and* calling nothing) may be **absent** from the ts callgraph, i.e. it reads as
never-seen when it was in fact analyzed-and-pure. This is the finding-2 analog from the reason-scoped audit:
an engine diverging from §2.2 in practice. **Verify and pin four-way** that an isolated pure function is a
callgraph node (empty adjacency) in every engine; fix the ts/swift node-set construction if it's edge-derived
rather than analyzed-fn-derived. This closes the "never-seen" row's soundness across engines.

### Honesty-invariant sharpening (RQ1 tie-in)

With the analyzed universe legible from the report, the oracle's verdict is precise about scope:
- a runtime effect from a function **in** the analyzed set that the report claimed pure/complete → a **true
  H-violation** (cardinal sin).
- a runtime effect from a function **not** in the analyzed set → **out of scope**, not a violation — and
  itself surfaced as an *executed-but-unanalyzed* coverage gap (the corpus exercised code the scan never
  saw). This is exactly the distinction §3.4/§8 of the write-up needs to state.

### `blindspots` / query integration

`blindspots` (and a small `analyzed` query verb) report the analyzed count, the pure fraction, the
`unanalyzed` list, and — given a function name — its membership row (effectful / provably-pure / not-seen),
by joining the report envelope with the §2.2 callgraph. This makes "did candor actually look at `X`?" a
first-class question a consumer or agent can ask, rather than inferring purity from silence.

### What this rung is NOT

- **Not a change to effect classification** — the same functions get the same effects; this adds *which
  functions were seen* and *what couldn't be*.
- **Not a new analyzed-set sidecar** — the analyzed universe is already the §2.2 callgraph node set; the
  additions are an envelope *summary* (`analyzed`), a machine-legible *incompleteness* field (`unanalyzed`),
  and a four-way guarantee that isolated pure leaves really are callgraph nodes.
- **Not the coverage envelope** — coverage names *dependency/module* blind spots (what the scan couldn't
  reach); this names the *analyzed universe of the target* + *what within-target couldn't be analyzed*.
  Complementary; `unanalyzed` (a parse failure of the target's own source) is distinct from `coverage`
  (an unmodeled dependency).

## Conformance

A new PART pins the three gaps four-way, over a target with a known count of functions — some effectful,
some pure, one **truly isolated** pure fn (uncalled, calling nothing), and one file that fails to parse:
- `analyzed.count` equals the true analyzed count; `count − |functions|` equals the pure count (Gap 1).
- the parse-failing file appears in the **`unanalyzed`** field of both the report and the `--gate-json`
  verdict (not stderr only), and — with a policy configured — the gate exit is non-zero (Gap 2).
- the isolated pure fn is a **callgraph node** (empty adjacency) in every engine, so its membership reads
  *analyzed-pure*, not *never-seen* (Gap 3 — the residual §2.2 hole).
- the digest is stable across a same-engine re-scan of unchanged input and changes when the analyzed set does.

## Versioning

**Tier-1 additive** (a new §2 envelope field `analyzed` + a verdict/envelope `unanalyzed` field; a pre-rung
consumer that ignores them is unaffected, and a pre-rung report is byte-compatible except for the additive
fields). Gap 3 is a **conformance fix to the existing §2.2 contract** (engines that already comply need no
change). Soundness-motivated — Gap 2 closes a machine-consumer cardinal-sin channel (a JSON `ok:true` over
unanalyzed source) — so it ships on the ladder, paired with the honesty-oracle work (`candor verify`) that
consumes `analyzed`/`unanalyzed`.
