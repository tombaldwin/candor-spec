# ⟨0.37⟩ — the STAT RULING: a locator may arrive as an ARGUMENT or as the RECEIVER

**Status: DRAFTED AND MEASURED, HELD until its conformance PART and MUST-ledger entries land with it.**
The clause below was written into SPEC.md, all three candor-spec gates passed, and then `must_ledger.py`
correctly refused it: *"a normative statement was added ... without its classification moving with it"* —
5 findings. Each new normative statement must name the PART that exercises it, and that PART does not
exist yet. So the edit was reverted rather than half-landed: a contract change and its enforcement are
one indivisible piece, which is this family's own "write the row before the port".

## Measured FIRST, on the shipped 0.36.2 engines, before a word was written

One variable in every cell — a benign allowed literal beside a runtime destination.

| arm | rust | java | ts | swift |
|---|---|---|---|---|
| 1 · argument-form stat (`fs::metadata(p)`, `Files.exists(p)`) | marks | **SILENT** | marks | marks |
| 2 · receiver-form stat (`p.exists()`, `f.exists()`) | **SILENT** | **SILENT** | *inexpressible* | **SILENT** |
| 3 · handle use-verb — must NOT mark | ok | ok | ok | ok |
| 4 · local-bound literal — must certify | **over-masks** | ok | **over-masks** | ok |

Arm 2 is the finding: **every engine that can express a receiver-form stat is silent on it**, so R414 is
family-wide, not rust-only. Arm 4 went red on its first run and is R416 — rust loses a literal through
`Path::new(...)`, ts loses even a plain string local, and that matters for sequencing because a fix keyed
on "the locator was not captured" would compound the over-mask in exactly those two engines.

## The PART is WRITTEN and RUNS — `conformance/gen_stat_locator.py`

Not wired into `run.sh`, for R411's reason: the suite has no xfail, so wiring a part that is expected red
would red `main` on defects nobody has fixed. Run it by hand:

```bash
CANDOR_SCAN_BIN=… CANDOR_JAVA_JAR=… CANDOR_TS=… CANDOR_SWIFT=… python3 conformance/gen_stat_locator.py
```

It reproduces the hand measurement above exactly, which is its calibration — the numbers were taken
independently before the file existed:

```
arm        rust        java        ts          swift
a1arg      ok          ✘           ok          ok        ← java = R409
a2recv     ✘           ✘           n/a         ✘         ← R414, family-wide
a3handle   ok          ok          ok          ok        ← the control holds everywhere
a4local    ✘           ok          ✘           ok        ← rust, ts = R416
STAT-LOCATOR: 6 cell(s) wrong
```

It **reuses `gen_masking.ENGINES`** rather than copying the four `Engine` classes — five generators already
carry their own copies with zero imports between them (R288's shape inside the conformance suite), and
this file does not become the sixth. Wiring it into `run.sh` is the last step, after the six cells go
green, and at that point it replaces nothing: PART 12 and `gen_masking` stay, because they pin the
argument-form spelling this one does not.

## What still has to land WITH the clause
1. A conformance PART with all four arms above — arm 2 declared inexpressible for ts under
   `part_declarations.py`, arms 3 and 4 as over-charge controls, not afterthoughts.
2. MUST-ledger classification for each new normative statement, naming that PART.
3. `spec-bump.sh` — this is a RUNG, and a non-additive one: a tree passing `allow Fs …` under ⟨0.36⟩
   can exit 1 under ⟨0.37⟩ with no code change, because the stat that was invisible becomes a surface
   the allowlist must cover.

## The clause, as drafted
```markdown
⟨0.37⟩ **A call's LOCATOR may arrive as an ARGUMENT or as the RECEIVER, and both are the call's own.**
⟨0.29⟩ above says the surface is read from the position that names the locator; it does not say where that
position may be, and every engine read it as "an argument". **A path-stat invoked on its path —
`p.exists()`, `p.metadata()`, `f.exists()`, `url.checkResourceIsReachable()` — names its destination just
as `fs::metadata(p)` does, and a stat IS an `Fs` reach**: three of the four engines already classify it so
(rust's `is_fs_path_arg` carries `metadata`/`canonicalize`, java's `fsKind` calls `exists` a READ), which
is why this clause states the family's practice rather than inventing a rule.

**Measured before it was written, on the shipped 0.36.2 engines, one variable — a benign allowed literal
beside a runtime destination.** Every engine that can express the receiver form was SILENT on it (rust,
java, swift; TypeScript has no path object and is a declared exclusion), while the argument form was
marked by all but java. A silent receiver-form stat is the masked-literal evasion by another spelling:
`allow Fs /tmp/lit` exits 0 over a caller-controlled path and the run prints *"nothing hidden"*.

**THIS RUNG IS NON-ADDITIVE, like ⟨0.30⟩.** A tree that passed `allow Fs …` under ⟨0.36⟩ can exit 1 under
⟨0.37⟩ with no code change on either side of the gate, because the stat that was invisible is now a
surface the allowlist must cover. Upgrading is a decision, not a drop-in.

**AND ITS COUNTERPART, which an implementer must read as part of the same rung — a call on an ALREADY-OPENED
HANDLE has NO locator of its own and MUST NOT be marked.** `f.read_to_string(…)`, `in.read()`,
`h.availableData` inherit a destination fixed at `open`, which this analysis has already seen. Marking them
would fail every program that opens a file by a literal name. All four engines are already correct here;
the clause exists so a fix to the sentence above cannot quietly break it.

**"DETERMINED" IS A PROPERTY OF THE VALUE, NOT OF THE SYNTAX.** A locator whose value is statically
determined is determined however it reaches the call — inline, through a local binding, through a
constructor (`Path::new("/lit")`, `Paths.get("/lit")`), or through a constant. An engine MAY
under-approximate and mark a determined locator incomplete: that fails CLOSED and stays conformant. But it
is a PRECISION defect and it had a measured cost in this family — rust lost a literal through
`Path::new(…)` while crediting a plain local and a `const`, and TypeScript lost even the plain local, so in
exactly those two engines an ordinary determined write was uncertifiable. **An implementation tightening the
sentences above MUST NOT widen that gap**, and a conformance PART for this rung carries the
determined-locator arm as an over-charge control, not as an afterthought.

> **STATUS OF THAT GAP — past tense as of 2026-09-12, and stated in the past tense deliberately.** Both
> halves were closed after this draft was written: rust by SOUNDNESS R416 (`resolve_str_expr` now peels
> `Path::new`/`PathBuf::from`, and only those two — `join`/`with_extension`/`canonicalize` transform the
> value and must keep returning nothing), candor-rust `1b981d3`; TypeScript's half in the same wave. The
> PART's `a4local` arm reads `ok` for rust and ts as a result. **The paragraph above was TRUE WHEN WRITTEN
> and would have shipped as a false claim about the engines a few hours later** — which is the whole
> failure mode of a limitation recorded as prose: it reads as considered, so nobody re-measures it. The
> normative sentence is unchanged and still binding; only the evidence sentence moved. Re-check this note
> against the PART's actual output at landing time rather than trusting it.

```
