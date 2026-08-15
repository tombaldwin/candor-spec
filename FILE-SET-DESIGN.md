# The file set — what a report says about code it never opened ⟨0.29 candidate, DESIGN⟩

> **Status (2026-08-16):** DESIGN, not shipped. The defect is MEASURED four-way (§1). The proposal in §4
> has one decision left for Tom (§5, the verdict consequence). This is B1 of the agreed ⟨0.29⟩ rung.

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

Collapsing N1 into N2/N3 is what makes the current silence defensible-sounding and wrong: the engines are
not choosing to exclude `build.rs`, they simply never had a concept of it.

## 4. Proposal

A `unconsidered` block in the report envelope, beside `analyzed`/`unanalyzed`:

```json
"analyzed":     { "count": 2, "digest": "…" },
"unanalyzed":   [ { "path": "src/broken.ts", "reason": "source failed to parse" } ],
"unconsidered": {
  "files":  [ { "path": "build.rs",      "reason": "outside the file selector" },
              { "path": "examples/ex.rs", "reason": "outside the file selector" } ],
  "elided": [ { "path": "target/",        "count": 18422, "reason": "excluded by convention" },
              { "path": "scripts/deploy.sh", "count": 1,   "reason": "not a language this engine reads" } ]
}
```

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

## 5. The one open decision — what it does to the VERDICT

⟨0.21⟩ established that a disclosure alone does not close a machine-consumer channel; the fail-closed exit-2
verdict is what did. The same question here, and it is genuinely a trade:

- **V1 — advisory.** Report key plus stderr, exit unchanged. Cheapest, adoptable everywhere, and weakest:
  it leaves `deny Exec` → exit 0 over a repo containing `execSync("curl | sh")`, which is the exact sentence
  this rung exists to delete.
- **V2 — fail closed on N1 when a policy is configured.** `unconsidered.files` non-empty ⇒ the gate cannot
  be certified ⇒ exit 2, same shape as ⟨0.21⟩'s parse-failure verdict. Strongest, and consistent with
  *always fix a fixable silent under-report*. Cost: every Rust crate with a `build.rs` goes red on upgrade.
- **V3 — the ⟨0.24⟩ shape.** Withdraw `ok` from the verdict document (the machine channel) and disclose,
  while exit stays 0 unless `--strict`. Splits the difference along a seam the family already has.

**Recommendation: V2, narrowed to N1, with the ⟨0.21⟩ UNKNOWN-RATCHET precedent for adoption** — a recorded
baseline of accepted `unconsidered.files` in `.candor/config`, so a legacy project pins what it already has
and only *new* unopened source turns the gate red. That keeps the fail-closed property where it earns its
keep (a file appearing outside the selector is a change nobody reviewed) without the flag-day cost of V2
plain. It is a ratchet, not a threshold, which is the form this project has repeatedly found survives.

## 6. Conformance obligation (sketch)

A new PART, four-way, with rows that a pre-fix engine **cannot** pass:

- the §1 fixture per engine — same-language `Exec` outside the selector — asserting the verdict changes AND
  that `unconsidered.files[].reason` reads the expected string (a value, not a presence).
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
