# The file set — what a report says about code it never opened ⟨0.29 candidate, DESIGN⟩

> **Status (2026-08-19): BUILT, and §5's verdict rule was REVERSED by ⟨0.30⟩.** This document describes
> the rung as designed, when an out-of-scope finding was disclosure only — every "no verdict change" and
> "nothing goes red" below is the ⟨0.29⟩ decision and is now HISTORY. ⟨0.30⟩ makes a non-empty
> `outOfScope` an INCOMPLETE verdict (`ok:false`, `incomplete:true`, exit 2), on the measurement that the
> peek resolves a CONCRETE denied effect rather than uncertainty. SPEC.md §2 ⟨0.30⟩ and §3.3(c) are
> authoritative; read this for the design reasoning, not for what an engine does today.

> **Status (2026-08-16):** DESIGN, DECIDED, not yet built. The defect is MEASURED four-way (§1). §5 was
> rewritten after reading why each engine skips what it skips — the first draft had the wrong axis, and
> §5.0 records that. **Tom's call: rung 2 of the ladder, "disclose + peek".**

⟨0.21⟩ gave the report a completeness manifest: `analyzed:{count,digest}` and `unanalyzed:[{path,reason}]`,
plus a fail-closed exit-2 verdict when a file was opened and could not be parsed. That closed the
enumeration drop *inside* the analysis.

This is the same question one level out. **`unanalyzed` names files the engine OPENED and failed on. It
says nothing about files it never opened at all** — and a consumer cannot tell the two apart, because the
denominator is the engine's file selector and the file selector is invisible.

## 1. The measurement (2026-08-15/16, all four engines, one fixture shape each)

Each engine was pointed at a project root with a policy of `deny Exec`, over a tree containing a
same-language source file that performs `Exec` and sits outside that engine's selector.

| engine | verdict | manifest | the file it never opened |
|---|---|---|---|
| **rust** | `policy ✓`, exit 0 | `analyzed {count: 1}`, no `unanalyzed` | `build.rs` — `Command::new("curl")` — **and it runs on every `cargo build`**; plus `examples/ex.rs` |
| **java** | `no violations`, exit 0 | `analyzed {count: 3}`, no `unanalyzed` | `src/com/x/Deploy.java` — `Runtime.exec("curl … \| sh")` — present, never compiled, so no class exists |
| **ts** | `policy ✓`, exit 0 | `analyzed {count: 2}`, no `unanalyzed` | `excluded/deploy.ts` — `execSync("curl … \| sh")` — outside the tsconfig `include` |
| **swift** | `policy ✓`, exit 0 | `analyzed {count: 1}`, no `unanalyzed` | `Tests/Helper.swift` — `Process().run()`; `Package.swift` also unread |

Every one of these is a **false all-clear under an explicit deny**, and every one is silent: not a note on
stderr, not a key in the report, not an exit code. The four engines agree, which by this project's own
standing rule ([[candor-honesty-confidence]]) is the *weakest* evidence of correctness available — it is
common-mode, and here it is common-mode wrong.

**The control is clean, and that is the important half.** Column (iv) of the same matrix — a file the engine
OPENED and could not parse — behaves correctly: candor-ts disclosed `unanalyzed: [{path: "src/broken.ts",
reason: "source failed to parse"}]`, refused to certify the gate, and exited 2. ⟨0.21⟩ works. This rung is
not a repair of ⟨0.21⟩; it is the half ⟨0.21⟩ never claimed.

## 2. Why the manifest reads as more than it says

`analyzed: {count: 2}` is true. The consumer's inference — "candor judged this project and found no `Exec`"
— is not, and nothing in the document marks the gap. This is the shape the family already has a rule for:

> **The three-row rule** ⟨0.21⟩/⟨0.24⟩: *absence under a key licenses a purity claim only if the key names
> something that could have had a body.*

Applied one level out: **absence of a file from the report licenses a purity claim about that file only if
the report says the file was CONSIDERED.** Today no report says that about anything, so the licence is
being taken without ever having been granted.

It is also the ⟨0.28⟩ lesson restated — *arming shifts what "the file exists" MEANS*. Here, pointing candor
at a repository root shifts what "no violations" means, and the report does not move with it.

## 3. Three kinds of unopened file, and only one of them is the defect

A naive fix — enumerate everything under the scan root that is not in `analyzed` — produces a report whose
`unconsidered` list is `node_modules/`, `target/`, `.build/` and `.git/`. That is noise, and a gate that
routinely emits noise is a gate people learn to wave through. So the categories have to be separated:

- **N1 — same-language source under the scan root that the selector did not reach.** `build.rs`,
  `examples/`, `Tests/`, a `.java` with no compiled class, a `.ts` outside `include`. Small, nameable, and
  **exactly where the measurement in §1 lives.** This is the defect.
- **N2 — deliberately excluded trees.** Vendored dependencies, build output, VCS metadata. Enormous, and
  correctly excluded. Must be disclosed as a **count with a reason**, never enumerated — and the walk can
  stop at the directory and count that, rather than descending.
- **N3 — files in no language this engine reads.** `scripts/deploy.sh`. The engine has no competence over
  them and must not pretend otherwise; but a project whose `Exec` lives in shell is a project where "candor
  says no Exec" is a dangerous sentence. A count with a reason, same as N2.

Collapsing N1 into N2/N3 is what makes the current silence defensible-sounding and wrong.
**CORRECTED after §5.0: the engines ARE choosing.** The first draft of this paragraph said they "simply
never had a concept of it", and that is false — `build.rs` is skipped by name with a written rationale,
and the other three have their own. N1 is therefore not an oversight class but a SCOPE class, which is
why the fix is to publish the scope rather than to widen it. The three-way split still holds; only the
story about how N1 came to exist was wrong.

## 4. Proposal (shape; the chosen rung is §5.2)

Two additions to the report envelope, beside `analyzed`/`unanalyzed`. The first is the DENOMINATOR; the
second is what the peek found in it.

```json
"analyzed":     { "count": 2, "digest": "…" },
"unanalyzed":   [ { "path": "src/broken.ts", "reason": "source failed to parse" } ],
"unconsidered": {
  "files":  [ { "path": "build.rs",      "reason": "outside the file selector" },
              { "path": "examples/ex.rs", "reason": "outside the file selector" } ],
  "elided": [ { "path": "target/",        "count": 18422, "reason": "excluded by convention" },
              { "path": "scripts/deploy.sh", "count": 1,   "reason": "not a language this engine reads" } ]
},
"outOfScope": [ { "fn": "build_script::main", "path": "build.rs", "effects": ["Exec"],
                  "class": "build-script",
                  "reason": "runs at compile time, not crate runtime — this scan did not judge it" } ]
```

`outOfScope` is **its own kind, never a `violation`**: folding it in would move verdicts, which is exactly
what the chosen rung promises not to do, and would make an exit code depend on a file the gate declined to
judge. It is emitted ONLY when a policy is configured, and only for effects that policy DENIES — see §5.2
for why that bound is what keeps the whole thing quiet.

Four constraints this shape is built to satisfy:

1. **⟨0.26⟩ — the KEY SET is the manifest.** A *partial* sidecar answered WORSE than an ABSENT one. So
   `unconsidered` must be four-way and total, or it must not ship: an engine that emits the key while
   enumerating only some of N1 is a regression on today, because today's absence at least claims nothing.
2. **⟨0.27⟩ — zero-match must disclose.** `"files": []` is a positive statement ("I looked and there were
   none") and must be emitted, not omitted. Absence of the key must mean *this engine cannot answer*, which
   is the ⟨0.26⟩ reading and the only one consistent with the rest of §2.2.
3. **N2/N3 are counts, never lists**, so the block cannot grow without bound and the walk cannot become the
   expensive part of a scan.
4. **The reason is a VALUE, not a presence.** PART 39 was wrong twice in one day by asking whether a key was
   there rather than what it said; the conformance rows for this must read the reason string.

## 5. The decision, and why the first version of this section was wrong

### 5.0 The correction — these are CONSIDERED exclusions, not gaps

The first draft treated this as *the engines miss files* and asked only how hard to fail. Reading the
engines settles it differently. **Every skip is deliberate and documented.** candor-rust, `lang.rs:1102`:

> *"True if a crate-root-RELATIVE path is the Cargo BUILD SCRIPT — i.e. exactly `build.rs` at the root.
> It runs at COMPILE time, never the crate's runtime behaviour, so it's skipped."*

candor-ts takes the tsconfig program (`parsed.fileNames`, and its own comment says the arm
over-approximates *deliberately*); candor-swift takes SwiftPM targets; candor-java reads bytecode. Every
one of those is defensible. **None of them is in the report.**

So the report carries a NUMERATOR and no DENOMINATOR. `analyzed: {count: N}` is true, and the scope
decision that produced N appears nowhere, so a consumer cannot tell whether the answer is to the question
they asked. The build-script exclusion is right for *"what does this library do when I call it"* and wrong
for *"what does building this crate do to my machine"*. The operator chose neither.

**Being considered is what made it survive.** This is [[feedback-documented-limitation-is-not-measured]]
exactly: a limitation written as a code comment reads as CONSIDERED, and that is what stops it being
measured. The `build.rs` comment is well-argued prose, which is precisely why nobody measured its cost —
and its cost is that `deny Exec` over a crate whose `build.rs` runs `curl | sh` is GREEN, on a file that
runs on every `cargo build` whether or not anyone calls the library.

### 5.1 Two things the first recommendation got wrong

- **Fail-closed on a UNIVERSAL condition disables the gate.** Every project has files outside the
  selector. This project already wrote that lesson down, in preflight [10]'s NONE branch: *a gate that
  fails routinely on a benign shape is a gate that gets waved through, which is worse than not having it.*
- **The ratchet FREEZES the defect rather than closing it.** Baselining the accepted set means day one
  accepts the `build.rs` that execs. It stops regressions — real value — but it does not close the hole
  that was measured, and the first draft presented it as though it did.

### 5.2 The ladder, and where we stop

1. **Disclose the scope** — excluded classes, counts, reasons.
2. **Disclose + PEEK** ⟵ **CHOSEN.** Additionally READ the excluded files and warn when they contain an
   effect **the policy actually denies**. No verdict change; nothing goes red.
3. **+ policy lever** — a `scope +build-scripts` form so CI can REQUIRE them clean. A four-engine rung.
4. **Change the default** — build scripts in scope unless excluded. A flag day.

**Rung 2 is chosen because it closes the measured defect for every existing user on upgrade, at zero
breakage.** Rung 1 tells you a build script exists, not that it execs — you still have to go and look,
which is the work the tool is for. Rungs 3 and 4 are both strictly better *for people who act*, and rung 4
is the only one that protects someone who never reads a changelog — but 4 turns adopters' CI red unasked
(uflexi's included) and 3 leaves everyone who does not opt in exactly where they are today.

**The peek is POLICY-SCOPED, and that is what keeps it quiet.** No configured policy ⇒ no peek ⇒ not one
new line of output. With a policy, it reports only effects that policy DENIES — so the noise floor is
"things you have already said you care about", not "everything in your test tree".

### 5.3 What rung 2 must not become

- **The same classifier, not a second path.** The peek differs from the gate in its FILE SET and in
  whether the result is binding — never in how an effect is judged. Two judgement paths would drift, and
  a drifted second opinion reported as a warning is worse than no warning.
- **Not a violation.** `outOfScope` findings are their own kind. Folding them into `violations` would
  change verdicts, which is exactly what rung 2 promises not to do, and would make the exit code depend
  on a file the gate did not judge.
- **Silent when there is nothing to say, LOUD in the report either way.** ⟨0.27⟩: an empty
  `outOfScope: []` is a positive statement and must be emitted. Absence of the key must mean *this engine
  cannot answer*, per ⟨0.26⟩.

## 6. Conformance obligation (sketch)

A new PART, four-way, with rows that a pre-fix engine **cannot** pass:

- the §1 fixture per engine — same-language `Exec` outside the selector — asserting the WARNING fires,
  that the verdict does NOT change (exit unchanged, `violations` untouched), and that the reason string
  reads what it should (a VALUE, not a key's presence — PART 39 was wrong twice in one day on that).
- **the peek is policy-scoped**: the same tree with NO policy emits no out-of-scope finding at all.
- **the peek is bounded by the policy**: `deny Net` over a tree whose only out-of-scope effect is `Exec`
  reports nothing — otherwise the floor is "everything in your test tree" and the gate becomes noise.
- **the control**, which is the row that matters most: a project with *no* unopened same-language source
  must emit `"files": []` and stay green. Without it the part passes against an engine that fails
  everything, which is the vacuous-control shape this project keeps measuring in its own work.
- an N2 row: a `node_modules/`-shaped tree must produce a COUNT, and must not enumerate.
- an N3 row: a shell script must be counted with the not-a-language-I-read reason, and must not be listed
  as N1 — the two reasons are the whole point of the distinction.
- the ⟨0.21⟩ mirror: a parse failure must still land in `unanalyzed`, not in `unconsidered`. Opened-and-
  failed and never-opened are different claims and the rung must not blur them.

## 7. What this does not cover

A file the selector DID reach and whose contents the engine understood only partly is `unanalyzed`'s
business, not this block's. And a *dependency* outside the scan root is the scan-boundary vein
([[candor-scan-boundary-vein]]), already closed and pinned by PART 20 — different question, and the reasons
must not be conflated in the report or the two disclosures become one indistinct hedge.

## 8. FILED, NOT IMPLEMENTED — the CROSS-POLICY hole (2026-08-24)

**A `peeked: true` is only true relative to the deny set the PRODUCER held, and the report does not say
what that was.** Found while ruling on ⟨0.32⟩'s carve-out; recorded rather than fixed, because the fix is
a report-format change and this rung was already in flight.

THE SHAPE, and it defeats every ⟨0.32⟩ arm because all of them are satisfied:

    candor-scan <tree> --out A --policy 'deny Net'     the peek runs, reads the excluded class IN FULL,
                                                      finds no Net there, and writes `peeked: true`
    candor-query gate --report A --policy 'deny Exec'  exit 0, `policy ✓`
    candor-scan <tree> --policy 'deny Exec'            exit 2 — there IS an Exec in that excluded file

The gate is not wrong about anything it can see. `peeked: true` says the peek OPENED those files, which it
did; ⟨0.32⟩'s unread-class rule correctly does not fire. What is missing is that the peek was BOUNDED — by
⟨0.29⟩'s own rule, `outOfScope` carries only effects the PRODUCER's policy denies, so the `Exec` finding in
the excluded file was seen and DISCARDED as out of the producer's question. The consumer then asks a
different question of a report that answered the first one, and nothing in the document marks the
difference. **Undetectable from the document**: the report records the peek's RESULT and never the policy
it was scanned under.

Note which way this fails. It is the fail-OPEN direction on the `gate --report` route — the supply-chain
route, where a consumer gates a report someone else produced — and it survives every control ⟨0.32⟩ has,
because the class really was read.

**PROPOSED FIX: record the scan policy's DENY SET, or a digest of it, in the report.** A gate then compares
its own deny set against the producer's and refuses (exit 2, INCOMPLETE) when the producer's does not cover
it, exactly as an unpeeked class refuses today. A digest is enough for equality and cheaper to keep stable
than the rule text; the full set is more useful in a message and is what a remedy would have to name. Which
of the two is a design decision, not a detail — a digest cannot tell an operator WHICH effect went unasked.

**The remedy message must say "the SAME policy", not "a policy".** ⟨0.32⟩'s existing remedy — *scan with
the policy* — is what produces this hole when read loosely: the operator did scan with a policy. SPEC §2's
⟨0.32⟩ producer clause already carries the corrected wording; the message an engine PRINTS has not been
checked against it, and this is the class of gap the ⟨0.29⟩ stale-message finding came from.

Cross-reference: the peek's ⟨0.29⟩ deny-set bound is what makes the whole rung affordable (SPEC §2 ⟨0.30⟩,
"the bound in the ⟨0.29⟩ clause above is what makes this affordable"), so this is a cost OF that bound
rather than a defect in it. Removing the bound is not the fix — an unbounded peek reports everything in
every excluded tree, which is the noise floor rung 2 was chosen to avoid (§5.2).
