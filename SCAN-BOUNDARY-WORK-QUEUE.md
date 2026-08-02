# Work queue: closing the scan-boundary vein

The ordered backlog for [SOUNDNESS-VEIN-crossing-the-scan-boundary.md](SOUNDNESS-VEIN-crossing-the-scan-boundary.md).
Written to be picked up cold — by a fresh session, or by an agent — without needing anyone's context.

**Why this is the top of the queue.** It is the only known defect that makes a `deny` gate pass code it
should fail, it reproduces in all four engines, and it is gate-level rather than report-level. PAPER1 §6.1b
now scopes the headline claim because of it.

**HOW TO READ THIS FILE (2026-07-27).** It has two halves and they have different jobs.
**`## THE QUEUE`, immediately below, is the authoritative open list**, ordered by dependency. Everything
after it is the RECORD — the standing bar, the durable lessons, and the original filings with their
measurements — kept chronological because it is a history and its value is in why each thing was decided.
Markers in the record mean: `- [x]` closed · `- [→]` folded into or indexed at a QUEUE section, not
separate work · `- [D]` decided and refused with numbers, re-open only with new evidence · `- [ ]` in the
record but not yet promoted, which should be rare and is a bug in this file if it is not.

## THE QUEUE — the authoritative open list, ordered by DEPENDENCY (2026-07-27)

Everything below this section is the RECORD: the standing bar, the lessons, and the original filings with
their measurements. It is chronological because it is a history. **This section is the queue.** A `- [ ]`
further down is the original filing of something indexed here, not a separate job.

### QUEUE REVIEW, 2026-07-28 — what is actually left

The section numbering below is CHRONOLOGICAL (§1, §2, §2b, §2c, §2d, §3, §3b, §3c, §3d, §4…) because
sections were opened as findings arrived. **It is no longer dependency order and should not be read as
priority.** This block is the priority; the sections are where the detail lives.

**SHIPPED since this queue was last reordered** — the ⟨0.24⟩ rung entire, floor bumped four-way (seven
components), and **FIVE four-way defects closed**: the scan-boundary `--class` fail-open, the §4 vocabulary
rung, `gate --report`, the empty-report cardinal sin, and the frontier rung. Conformance gained **PARTs
24–27** (three self-differential properties + the rung's behaviour). The theory↔spec↔code loop is closed
and immediately found the theory wrong twice.

**ONE ITEM DOMINATES, and it is a decision already made:**

1. **The ENTRY-COLLISION UNION (§2).** Decided 2026-07-27 with measurements (`b47c9ab`), still
   unimplemented. It is now the **only** thing behind BOTH remaining `stale_beside` waivers, and each of
   those records a measured cardinal sin — java's stale `{Unknown}` erasing a trusted `Fs` (`deny Fs`
   exit 1 → 0), and rust withdrawing a key when a distrusted copy sits beside the trusted original. It also
   **dissolves rust's deliberate conflict-case divergence**, which exists ONLY to compensate for the
   withdraw behaviour the union replaces. *Two waivers retired, two cardinal sins closed, one divergence
   dissolved, zero new decisions required.* Nothing else open has that ratio.

**THEN, in order:**

2. **P4 — signature monotonicity** (§3). The last self-differential property. P1/P2/P3 found 8 defects
   between them on first run; there is no reason to expect P4 differs.
3. **rust's incomplete-vs-violation exit-code divergence** (§3b). rust exits 2 where java and swift exit 1;
   a four-way ruling I owe, now pinned on BOTH routes since `gate --report` mirrors its own scan.
4. **java's `blindspots` never lists a setup-only source** (§4). `UnknownReason.parse` returns null on a
   colon-free tag, so the UNFILTERED list is already wrong. Check the other three for the same
   colon-required parse.

**FILED WITH MEASUREMENTS, NOT STARTED** — each has a number attached and none is blocking: the manifest
that cannot cross a trust boundary (§2b); the return-index collision lead (§3c — recovers >half of one
corpus's unresolved markers, and is `6f2210c`'s rule one index over); the networked-DB classifier question
(§2b); the frontier differential's three-arms-two-consumers (§2); the per-type sidecar unanswerability
(§2); two off-vocabulary swift kinds (§4); candor-agents' `Net[…]` widening (§2c).

**OPERATIONAL, and both are the same shape — a tool that costs more than it repays:**
- The full suite now exceeds **50 MINUTES** (PARTs 24–27 all landed today). Split the property PARTs into
  their own leg; the generators already take `--baseline` individually.
- **`ci/self-gate.sh` DELETES TRACKED FILES** — a script contributors are told to run.

**NEEDS TOM, NOT WORK:** ~153 unpushed commits across seven repos; candor-ts at build 0.23.2 against the
family's 0.23.1 (legitimate — its module-unit wire key moved).

**A NOTE ON THE OLD ORDERING**, kept because it was true when written: this document began as a worklist of
silent under-reports. That is no longer what it is — the open items are decisions, priced refusals and
disclosed precision. The one exception is item 1, which is a decision whose *implementation* closes two
silent under-reports, and that is exactly why it is first.

### 1 — THE §4 VOCABULARY RUNG · serial, first, cannot be parallelised
**One decision with four symptoms**, filed separately across three review rounds and only visible as one
thing when read together. It is the critical path: it blocks the `ambiguous:` rename, any engine renaming,
and probably the dot-free detail fix.

- [x] **SYMPTOMS 1 AND 2 SETTLED (spec ⟨0.24⟩) — and the diagnosis was wrong in a way that matters.**
      **The absence-keyed rule was IN THE SPEC**, not invented by the engines: §6.2 said *"a function whose
      `Unknown` carries no recorded reason is treated as `unresolved`"*. Every engine was conforming. The
      divergence was MODEL vs CONTRACT, not contract vs implementation — a materially different failure,
      and one four agreeing implementations could never surface. PAPER1's (W) passage is corrected.
      - **Symptom 2 — fixed by one word: `CONTRIBUTES`.** A reasonless `Unknown` now ADDS `unresolved` to
        the class set instead of defaulting when the set is empty. Both properties then hold at once:
        fail-closed on an unclassifiable hole (what the clause was for) and monotone (what Lemma 2 needs).
        That the fix is one word is not evidence the defect was small — it is evidence a spec can sit one
        word from contradicting a theorem it implements, with nothing in a four-way differential able to
        notice.
      - **Symptom 1 — `ambiguous:` is now a §4 kind.** §6.2 had projected `ambiguous:*` to `dispatch` all
        along, so CONSUMERS classified it correctly while the PRODUCER emitting it was non-conforming; the
        asymmetry survived because a consumer never complains about a token it can classify. Removing it
        was measured and rejected — 8710 of 19607 rust entries, and `deny E Unknown[dispatch]` would go
        58/200 crates → 0/200. It also names something the other kinds cannot: no owner was ever formed,
        and no function value is involved.
      - [x] **SYMPTOM 3 CLOSED — and the vocabulary question was the SMALL half.** Measuring before
        editing (as this entry demanded) found the real defect one layer down, in the CONSUMER. A report
        carrying `dispatch:untyped cross-package receiver` is **silently dropped** from
        `possibleViaUnknownDispatch` — in BOTH the hierarchy and no-hierarchy arms, with no diagnostic —
        because the dot-free detail makes `simple_method`/`declaring_type` return the whole string and
        `by_method.get(m)` cannot hit. A consumer reads that omission as "no function may reach the target
        through an unresolved dispatch", about a call the engine explicitly charged `Unknown`.
        - **The rule generalises past the symptom** (SPEC §3.1 ⟨0.24⟩, `ec75631`): when frontier condition
          (3) cannot be EVALUATED, the entry is disclosed with the raw detail, never dropped. The spec
          already took this direction one rung up — no §2.2 sidecar → over-list by simple name. Dot-free is
          that case one rung down (no owner AND no member) and takes the same answer.
        - Both candidate fixes REJECTED on the measurement, as predicted: `callback:` is false (no function
          value) and silently NARROWS every field `deny E Unknown[dispatch]` gate by moving the §6.2 class
          to `indirect`; emitting nothing is the cardinal sin. §4 blesses the dot-free form instead — the
          KIND is what gates read so the kind stays true; the DETAIL is where the engine says how much it
          knows, and "nothing" must be sayable. **Zero engine emit changes required.**
        - Also caught a STALE spec claim in the same paragraph: §3.1 said "the Rust scanner emits no
          `dispatch:`" and returns `[]` by language model, not as a gap. It emits `dispatch:` for every
          dispatch reason in a 1062-report census. **The spec was reading a silent drop as a language
          property** — which is how the drop survived.
        - [x] **rust FIXED `a11adf1`** — and the brief UNDERSTATED it: **three** defective shapes, not
          one. The agent measured all three on the pre-fix binary rather than taking my one.
          | dot-free detail | no-hier | with-hier |
          |---|---|---|
          | a phrase (`untyped cross-package receiver`) | dropped | dropped |
          | equal to a reacher's WHOLE qual | **MATCHED** | **MATCHED** |
          | equal to a dotted reacher's SIMPLE METHOD name | **MATCHED** | dropped |
          Row 2 is a genuine false positive: the split helpers fall back to the whole string AND are applied
          to both sides, so the override test degenerates into **string equality between a reason detail and
          a function name** — and the hierarchy arm passed it **only by reflexivity** over a string that is
          not a type name, never consulting the sidecar. Row 3 is arm-dependence: the same detail disclosed
          or dropped on nothing but whether a sidecar exists. Fix short-circuits **before** the split.
          Negative control run on the tests themselves (branch disabled → 5 tests fail).
          **Row 2's nuance is the durable part**: that entry belonged in the output under ⟨0.24⟩ anyway, so
          the pre-fix behaviour was **right for the wrong reason** — the configuration that hides a gap
          instead of showing one ([[feedback-fabrication-fixes-cause-misses]]).
        - [x] **swift `5f9e75e` — MY BRIEF'S PREMISE WAS WRONG, and the agent measured instead of
          complying.** candor-swift implements **no `callers` verb at all** (`--include-unknown` → exit 2);
          it is a PRODUCER that writes the §2.2 sidecar *for* the other engines' consumers. The frontier is
          a **three**-surface query (rust/java/ts). SPEC corrected `7fb5356`. In-scope work done instead:
          the producer half pinned — `reasonClass("dispatch:untyped cross-package receiver") == "dispatch"`,
          previously unpinned (only the DOTTED form was asserted), verified by mutation, and the gate arms
          measured (`deny Unknown[dispatch]` exit 1 / `deny Unknown[indirect]` exit 0 — the control showing
          the rejected `callback:` ruling would have flipped it).
        - [x] **java FIXED (2 commits)** — had BOTH defects, in both arms, and the measurement beat the
          prediction on the second. Pre-fix, three arms:
          | hierarchy sidecar | frontier BEFORE |
          |---|---|
          | ABSENT | dot-free MISSING |
          | POPULATED | dot-free AND the row-3 collider MISSING |
          | `{}` | **`[]` — EVERYTHING missing, including the dotted entries** |
          The `{}` arm is **worse than the dot-free drop it was filed behind**: honouring an empty sidecar
          took out the entries that were working. Fixed to `hier != null && !hier.isEmpty()`, matching rust
          and ts. The agent agreed over-listing is right rather than implementing it under instruction —
          the brief invited it to argue back.
          Also: **my guess in the brief was wrong** ("JVM quals are dotted so this may be a non-issue").
          Row 3 fires on dotted quals precisely because the detail collides with the SIMPLE METHOD name,
          not the qual; row 2 fires whenever a report carries a dot-free unit name (`main`). Both measured.
          Mutation-checked both directions; 550 tests green.
        - [→] ts still in flight.

      ORIGINAL FILING of symptom 3 — the dot-free detail: rust and swift emit
        `dispatch:untyped cross-package receiver`: canonical kind, malformed normative detail (§4 makes
        `<owner>.<member>` the one conformance-compared part). Two candidate fixes and they differ in
        class: emit `callback:` (which §4's own dividing line implies for an untyped receiver, but moves
        the class `dispatch`→`indirect` and NARROWS gates), or bless a detail-free form for the case where
        no owner exists. **Wants the measurement before the edit** — how many functions change class under
        each. Do not take this one by argument.

      ORIGINAL FILING — settle §4's reason vocabulary: its MEMBERSHIP, its normative DETAIL, and its
      relation to §6.2's class table. The four symptoms:
      1. **§6.2's class table (line 1433) lists `ambiguous*` under `dispatch`; §4's kind vocabulary omits
         it.** The spec blesses an emission in one section and excludes it in another.
      2. **No kind can express "Unknown, and one of them has no reason."** §4 has none, §6.2's rule is
         per-function and keyed on ABSENCE so it does not compose, and a second-hop consumer re-derives
         `dispatch` alone. All four engines. **This is the one that reaches the theory paper** — PAPER1
         now carries it as the well-formedness condition (W), with a measured monotonicity violation.
      3. **Every `dispatch:` rust and swift emit at the half-1 site is dot-free** — canonical kind,
         malformed normative detail. PART 10 would DIVERGE on it and does not only because its fixture
         never chains a dependency. §4's own dividing line says an untyped receiver is `callback:` anyway,
         so the KIND may be wrong too.
      4. Consequence, already priced: rust's `ambiguous:` rename is refused because it would take
         `deny E Unknown[dispatch]` from 58 of 200 crates to **0 of 200** — a deletion, not a narrowing.
      **Do not let an engine rename anything until this is settled.**

### 2 — TWO MORE SPEC SILENCES · concurrent with (1), different subject matter
Neither depends on the other or on (1). Both are the same failure: the spec is silent and the engines
diverged, so a `deny` gate gives different verdicts per engine on identical input.

- [ ] **Entry collision: three engines, three behaviours.** rust WITHDRAWS, java takes last-NON-EMPTY-wins
      (and a stale `{Unknown}` therefore erases a trusted effect — measured, `deny Fs` exit 1 → 0), ts
      UNIONS. Measured across all four and written up in `ENTRY-COLLISION-DECISION.md`.
      **DECIDED 2026-07-27 (`b47c9ab`) — adopt ts's union.** The gating measurement (item 1, "what a union
      does to rust's corpus") is done, read-only over the real `.candor/deps` trees of candor-rust/pgman/
      ebman. It cost SEVEN effect-items across all three corpora and buys back 123 purity claims + 24
      `deny Fs` flips. It also **moved the argument**, which is what waiting for it was worth:
      - The doc's own objection — "two entries under one key may be two DIFFERENT functions that merely
        collide, so unioning fabricates" — **describes nothing in the corpus.** Every measured disagreement
        is one function at two VERSIONS of one crate (thiserror-impl 1.x/2.x, rustix 0.38/1.1, http 0.2/1.4,
        hyper 0.14/1.9), both legitimately in the tree. For a version pair the union is not a hedge, it is
        the correct answer: both bodies are in the build and the package-scoped key cannot say which one a
        caller resolves to.
      - Named live cardinal sin: `hyper#client::conn::http1::Builder::handshake` = `['Log']` @0.14.32 vs
        `[]` @1.9.0 → rust withdraws → consumer reads it ABSENT = pure, on one of the most-depended-upon
        crates there is.
      - **Withdrawing costs more than the effect** — a finding the doc had not considered. The key carries
        the κ ledger and the call edges too, and both disagree far MORE often than `inferred` (`invisible`
        30/37/273, `calls` 57/120/326). Rust discards all of it at once.
      - Item 2 (surfaces) recorded as **UNDER-POWERED, not answered** — my first pass produced a flattering
        zero by comparing absent keys to absent keys. Real sample is 0-9 keys.
      - [ ] **IMPLEMENT four-way**, behind the decision: rust stops withdrawing, java stops last-non-empty,
            swift's trust-level-first rule reconciled with the union (doc item 4, still open), ts unchanged
            as the reference. Plus a conformance PART verified-to-catch per engine, with a row that FAILS
            for an engine that withdraws or picks. Do NOT start while the four frontier agents hold the
            repos.
      Note the doc's own history: this rule has been described three times and been wrong twice — which is
      itself part of the argument for a rule that discards nothing.
- [x] **RULED (SPEC §3.1 ⟨0.24⟩, `ec75631`) — empty, absent and unparseable are ONE input: over-list.**
      `hasHier` gates on EMPTINESS (rust `!hier.is_empty()`, ts `Object.keys(...).length > 0`) vs ABSENCE
      (java `hier == null`). Three engines, two answers — and java's is the unsafe one: a sidecar that
      parses to `{}` is non-null, so java HONOURS it, `isSubtypeOf` fails for every type, condition (3)
      fails for every dotted dispatch source at once, and the frontier collapses to EMPTY. A consumer reads
      an empty frontier as "nothing may reach the target through an unresolved dispatch".
      The ruling: `{}` is not the claim "no type has a supertype" — far more often it is "the pass found
      nothing, was not run, or wrote a stub", and the difference is **not recoverable from the file**. So
      all three mean *the subtype test is unanswerable*, which is the same trigger as symptom 3's dot-free
      detail: disclose, do not drop. This item and §1 symptom 3 turned out to be one rule, which is why
      they landed in one commit.
      **Sent to the java engine to MEASURE** — I read java statically and have not run it, and the brief
      says so, plus invites it to argue back if an empty sidecar is a meaningful claim after all.

- [ ] **NEW, opened by the ⟨0.24⟩ ruling — unanswerability in the §2.2 sidecar is PER-TYPE, and the
      ruling only handles it PER-FILE.** Absent/empty/unparseable sidecars now correctly over-list. But
      once a sidecar IS present and non-empty, condition (3) runs `isSubtypeOf(t, owner)` per reaching type
      `t`, and a type with **no entry in the map** is treated as having no supertypes — a positive claim.
      Absence there is genuinely ambiguous: a type with no supertypes legitimately has no entry, and so
      does a type the hierarchy pass never indexed (an out-of-scan reacher is the obvious case). The
      sidecar has no way to say *"I did not analyse this type"*, so the consumer cannot tell the two apart
      and silently resolves the ambiguity in the direction that DROPS.
      ts's `7bbf73c` is the near-miss that makes this concrete: it fixed `{"@superclass":{}}` collapsing
      the frontier by DROPPING uninterpretable keys — which is right for a wholly-uninterpretable file
      (`{}` → over-list), but a **partially** interpretable one stays non-empty and takes the precise path
      over a hierarchy that cannot answer for the dropped types.
      **This is the three-row rule applied to the sidecar, and unlike symptom 3 it probably DOES need a
      format rung** — the sidecar would need the `analyzed`/`unanalyzed` treatment that reports got at spec
      0.21 ([[candor-completeness-manifest]]). Do not patch around it with a leaf-key guess.
      MEASURE FIRST, and not while the four frontier agents are live — running a shared rust binary during
      someone else's edits is standing-bar item 7f, which produced a phantom finding once already.

- [x] **CLOSED `94de3b0` + SPEC §2.2 ⟨0.24⟩ `5652ce6` — and it was not cosmetic, and it needed no sweep.**
      Filed as a spurious warning; measured as **three real losses**, each against a sidecar-removed control:
      - **an effect-free crate was REFUSED OUTRIGHT** — the bogus parse failure set the `hard_fail` bit that
        distinguishes "no effects" from "every report was corrupt", so a well-formed `functions: []` report
        beside a sidecar exited **2** and answered nothing;
      - **provenance emptied** — the build-version reader takes the first report by sorted path and the
        sidecar sorts first, so `baseline_version`/`engine_version` came back `""`, which **silences the
        §2.1 producing-build mismatch disclosure**. A false disclosure suppressing a true one.
      - `reports <prefix>` — the canonical "what counts as a report" oracle — listed the sidecars as reports.
      **MY SWEEP ASSUMPTION WAS WRONG, and the measurement inverted it.** I briefed this as spec-level and
      expected four engines to share it. Three already exclude these by NAME; only rust discriminated by
      SEGMENT COUNT, which is why only rust had the hole. No sweep.
      **But the spec gap is sharper than the bug**: nothing said prefix discovery must exclude the §2.2
      sidecars. Three engines did it by convention, the fourth did not, and nothing said it was wrong — and
      the three by-name lists **disagree** (ts carves out six suffixes, java two). Cross-engine reading is
      real (the frontier differential has one engine produce and another consume), so the short-list
      consumer claims the other's sidecar as a report. Reserved set now enumerated in §2.2, denylist
      required, direct-file locator explicitly exempt.
      - [x] **java `c406119` — and java HAS the "refused outright" consequence, in its own form.** Measured:
        one report plus two foreign sidecars → a FALSE ambiguity disclosure (`matches 3 reports`), then it
        **picks the sidecar** (`gate` sorts before `jvm`; the resolver takes the lexicographically first
        hit) and refuses every query about a file the user never named. After: exit 0, silent, answered from
        the real report. The other two consequences were checked and do NOT apply — java reads provenance
        from the *resolved* report rather than the first by sorted path, and has no `reports` verb.
        One denylist in `Loader.isSidecarName`, all seven spec segments, read by **both** globs *and* the
        `CANDOR_DEPS` walk — routed through one reader rather than a second list that happens to agree.
        Controls both ways: old two-suffix list → 3 of 4 tests red; over-wide "reserved word anywhere" → the
        `hierarchy`-named-package control red.
        **Also found the comment-as-assertion defect again**: a doc comment claimed the discriminator was
        **segment count**, which the code never implemented. Corrected.
      ORIGINAL FILING — a FALSE DISCLOSURE on every `callers` call that has a hierarchy sidecar (found by
      the rust agent in passing, and independently by me while measuring the frontier). The report-locator
      glob picks up `<prefix>.<pkg>.hierarchy.json` as a candidate REPORT and prints
      `candor: report ….hierarchy.json failed to parse — its functions are OMITTED from this query (corrupt
      or mid-write); re-run the scan`. The sidecar is not corrupt and nothing is omitted — the message is
      simply false, and it tells the user to re-run a scan that is fine.
      This is the class [[candor-scan-guards]] already names once (`net-partner` reported as an ignored
      unknown config key **while being honoured**): **a false disclosure is worse than a missing one**,
      because it spends the user's trust in the disclosure channel on noise. It fires on every `callers`
      call with a sidecar present, including inside the existing frontier tests. Sweep the locator glob in
      all engines — the sidecar suffixes (`.callgraph.json`, `.hierarchy.json`) should be excluded at the
      glob, not diagnosed at the parse.

- [ ] **NEW — the FRONTIER DIFFERENTIAL has three named arms and only TWO independent consumers, and it
      excludes the engine it silently depends on.** Found while correcting SPEC §3.1's "all four engines".
      `conformance/frontier_differential.py` runs `java`, `ts`, `swift` and asserts "three engines must
      AGREE". But `frontier_swift()` uses candor-swift only as the **producer** and then runs **rust's
      `candor-query`** as the consumer (line 87: `CANDOR_QUERY_BIN` / `candor-rust/target/debug/candor-query`)
      — because candor-swift ships no `callers` verb at all. So the arms are really java(prod+cons),
      ts(prod+cons), swift(prod) + **rust(cons)**.
      Two consequences, and the second is the sharp one:
      - Its header excludes rust because *"rust has no `dispatch:` — its indeterminacy is callback/native"*.
        **That is the same stale claim SPEC §3.1 carried** (`7fb5356`): rust emits `dispatch:` for every
        dispatch reason in a 1062-report census. So rust's producer side is untested here **while rust's
        consumer silently carries the swift arm**.
      - A common-mode defect in the rust consumer appears IDENTICALLY in the swift arm and cannot be
        distinguished — which is precisely §3's structural gap, occurring **inside the suite built to
        detect it**, and dressed as a third independent vote. This is the concrete artefact to point at
        when justifying §3: not a hypothetical, a live one, in our own instrument.
      Fix has two halves: separate PRODUCER from CONSUMER in the arm labels so a shared consumer cannot read
      as independent agreement, and add rust's producer arm. Belongs with §3 (P1 holds `conformance/`).

### 2b — WHAT THREE FABLE REVIEWS OF THE THEORY + SPEC FOUND (2026-07-27) · mostly fixed, three open

Three independent reviewers (theory-internal, theory↔spec correspondence, spec-internal). **Two of them
independently found the same top finding**, and eleven of one reviewer's fifteen touched text written that
same day. FIXED already: `pure` (§6.2 + the model), §4's four-kinds + two stale rust claims, §2.2's
"NOT YET RULED", `netClass`'s rung tag, "the ten effects", the falsified `--class dynamic` diagnostic, the
overstated frontier pin, `dep:`/`dep-stale:` registration, and the model's missing `Ipc`/`Clipboard`.

- [x] **FIXED (`2b4c9a1`) — and the fix was one SENTENCE, three places.** §1 said "`Llm` refines `Net`
      **the way `Db` does**". The test for what "refines" may mean: **every occurrence of the refining
      effect must be an occurrence of the base channel.** An `Llm` call is an outbound request in every
      instance (engines **co-emit** `Llm`+`Net`); an embedded/file-backed/in-process store has **no egress
      at all** (engines emit `Db` **alone**). The encodings were already opposite; only the sentence
      claimed otherwise.
      **The sentence had PROPAGATED into the theory** — PAPER3 Def 2 took it at its word and carried
      `Db ⊑ₑ Net`, Def 4 fires `deny e` on any refinement, the model transcribed both faithfully, and the
      JVM differential produced **100 disagreements over 1792 rows, every one that family**. Corrected in
      all three: SPEC §1, PAPER3 Defs 2 and 4, and `policy_model.py` (whose worked example ASSERTED the
      wrong direction — `assert deny("Net")(Sig({"Db"}))` — and now asserts both, with `Db` as an explicit
      negative). **100 → 0 without touching a single engine.**
      **The reviewer's proposed fix was the wrong one and this is why**: widening `deny` to be
      refinement-closed is the FABRICATION MIRROR — it charges every embedded-database user with network
      egress they do not have. Correcting the preorder costs nothing and the engines were right all along.
      - [ ] **RESIDUAL, filed as a CLASSIFIER question not a gate one:** a **networked** DB call is genuine
            egress `deny Net` does not see. `Db` and `Net` **overlap without either refining the other**,
            which a relation over effect NAMES cannot express. Closing it means extending the destination
            classification the gate already carries for `Net` (`netClass`) to `Db`, so a networked store is
            distinguishable from an embedded one at the call site. Measure first: how often is the
            driver/DSN resolvable at the call site, four-way.
      ORIGINAL FILING — `deny Net` does not fire on a `{Db}` function, and §1 claims it should.**
      Model Def 4/30 is refinement-closed (`Reject ⇔ ∃e′∈S. e′ ⊑ₑ e`, so `deny Net` fires on `{Db}` — the
      model's own pinned worked example). SPEC §4.0 says plain membership (`e ∈ S`). Engines implement
      membership. **VERIFIED MYSELF**: §1 line 224 says *"`Llm` refines `Net` **the way `Db` does**"*;
      candor-classify emits `Llm`+`Net` together (*"a model dispatch IS network I/O"*, `lib.rs:1549`) and
      emits `Db` **alone** (five `Some("Db")` sites, no `Net`). The two refinements §1 calls identical are
      encoded oppositely.
      **BUT THE REVIEWER'S FIX IS WRONG, AND THE ASYMMETRY IS PROBABLY CORRECT.** It proposed making `deny`
      refinement-closed so `deny Net` catches `Db`. That over-fires: **`Db` is not always network.** SQLite,
      embedded H2, an in-memory store — all `Db`, no egress. `Llm` genuinely *is* always a network call to a
      provider, which is why co-emitting `Net` there is right. So `Llm ⊑ Net` holds and `Db ⊑ Net` **does
      not**; they are different relations and **§1's sentence is the defect**, not the gate.
      What remains real underneath: a **networked** DB call (JDBC/sqlx over TCP) is genuine egress that a
      `deny Net` gate will miss. That is a CLASSIFIER precision question — can an engine distinguish
      postgres-over-TCP from SQLite at a call site? — not a gate-semantics one, and answering it by widening
      `deny` would charge every SQLite user with network egress. **MEASURE BEFORE EDITING**: how often can
      the driver/DSN be resolved at the call site, four-way. Then either co-emit `Net` where it IS network
      (byte-changing rung) or state the residual in §1 honestly. Do NOT take this one by argument — that
      instruction paid for itself twice today.
- [ ] **OPEN: the ⟨0.21⟩ manifest is exactly the `{count, digest}` form PAPER3 Def 24 says CANNOT discharge
      (A0).** Def 24/Remark 2: discharging it needs **function granularity**; `{count, digest}` "cannot
      disambiguate dropped from pure". §4.0 nonetheless claims the manifest "is what lets a consumer tell
      `(∅,∅)` from a function never placed in the lattice at all" — which for a *bare envelope* is the claim
      Remark 2 denies (the per-unit route is the §2.2 sidecar, which is OPTIONAL). **This lands directly on
      `gate --report`**, which leans on "absent is absent" with no manifest obligation stated: a dependency
      report that silently dropped a function gates GREEN, in the supply-chain verb. Either require the
      function-granularity set wherever absent⇒pure is consumed across a TRUST BOUNDARY, or weaken §4.0's
      sentence to the count-level claim it actually supports.
- [x] **DONE — the PAPER side of the reviews is now acted on** (papers are local, never committed):
      - **PAPER1's (W) rewritten.** It was written as `Unknown ∈ S ⇒ D ≠ ∅`, whose antecedent is
        unsatisfiable (`Unknown ∉ E`), so it was **vacuous** — and it produced a visible contradiction two
        paragraphs apart ("the lemma NEEDS (W)" vs "the lemma is UNDAMAGED"). The condition is real but
        lives on the **representation map**, not on signatures: the offending state is not expressible in
        the lattice at all. The wrong version is kept visible rather than replaced.
      - **PAPER1's "no new proof" softened** to what is true: no new proof about `Reject`, one one-line
        obligation about the PRODUCER (the composite *code-change → signature → verdict* has two arrows;
        Lemma 2 covers the second).
      - **PAPER3 Def 32 (`pure`) amended** to `Reject ⇔ S ≠ ∅`, with the divergence recorded: 15
        disagreements over 256 signatures before, **0 after**.
      - **PAPER3 Defs 33/34/35 rewritten** to the shipped verbs — `forbid` is a call-graph dependency rule
        (no effect predicate, fires on a PURE call), `allow` is a **fail-closed literal-surface
        certification** and is rejection-capable, and the ratchet **grandfathers** (executed counterexample:
        `D_b={dispatch}`, `D={dispatch,reflect}` → Def 35 rejects, every engine passes).
      - **Prop 5 RETRACTED and rescoped.** It claimed coverage of "the full shipped policy language" and
        discharged three verbs in three lines — proving things about verbs that do not exist. Now scoped to
        the `L`-carried verbs, with the four uncovered ones and what is genuinely unproved about each
        listed.
      - **ESCAPE 4 ADDED** (§8 said "three escapes"; there are four): **within-`D` reason-class
        reclassification** is `⊑`-incomparable, H-invisible, and relaxes a scoped gate. Not hypothetical —
        the contract itself records refiling `dispatch:`→`callback:` taking a deployed gate from 58/200
        packages to **0/200**. The projection layer from raw reasons to classes **has no counterpart object
        in the model at all**, which is why an algebraic reading missed it and a measurement did not.
        Propagated through both papers.
      - **Def 6's `r` quantified**; **Def 30's refinement divergence recorded** (the `Db`-under-`deny Net`
        family) with the ruling that `Llm ⊑ₑ Net` holds and `Db ⊑ₑ Net` does not, so Def 2 treats one
        relation as two.
      - **The model now states what it does NOT transcribe** and warns that adding rows for `forbid`,
        `allow`, `deny E[dest…]` or the ratchet would **manufacture divergences out of the theory** — which
        is what the `pure` row would have done before the amendment.
      ORIGINAL FILING — PAPER3's Defs 33/34/35 do not describe the shipped verbs, so Prop 5's "full shipped
      policy language" is not discharged.** Found by BOTH theory reviewers. `forbid` is modelled as an effect
      predicate `φₑ`; the shipped `forbid A -> B` (AS-EFF-009) is a **call-graph dependency rule** that
      fires on a *pure* call and carries an empty effect set. `allow` is modelled as a scope exception "not
      a rejection predicate"; the shipped `allow` (AS-EFF-008) is a **fail-closed literal allowlist** that
      IS rejection-capable and reads `hosts`/`paths`/`cmds`/`tables` — **outside the carrier `L` entirely**.
      `unknown-ratchet` is modelled as `D ⊄ D_b`; the shipped one **grandfathers** a function already
      `Unknown` at baseline even when it acquires new classes (executed counterexample: `D_b={dispatch}`,
      `D={dispatch,reflect}` → model REJECT, engine passes). Also unmodelled: `deny Net[dest…]`, the
      marketed security gate. **Consequence: the planned engine-vs-model differential will falsely flag
      engines on the ratchet row and cannot exercise `forbid`/`allow`/`Net[dest]` at all.** Paper work.
- [x] **CLEARED (`eab46fc`) the spec-only leftovers** — the three NAMED-BUT-UNDEFINED surfaces
      (`blindspots --stats`, the `reports` verb — cited in §2.2 as *"the canonical what-counts-as-a-report
      oracle"* and specified NOWHERE, and the `encountered-*` family), plus the locale clause's two readings
      (locale-independence binds EVERY ordering; code-point binds only where a field's collation is pinned,
      so ts's ~70 UTF-16 sites are conformant and the clause now says so), plus `--class`'s value grammar
      (one comma list, not repeatable, unrecognised token = **exit 2**, deliberately NOT the policy side's
      drop-with-warning: a dropped POLICY token leaves a WIDER rule standing, a dropped QUERY token leaves a
      NARROWER filter and would silently answer a question the user did not ask), plus requirement 0's
      antecedent, which as written abolished `blindspots --class` rather than exempting it.
- [ ] Still open, lower priority: a **fourth escape** §8 does not catalogue (within-`D` reason-class
      reclassification is `⊑`-incomparable, H-invisible, flips a scoped gate red→green — and §6.2 names the
      hazard itself); `deny <NewEffect>` on an older engine is **silently dropped** = gateless-green,
      fail-OPEN, the shape the unreadable-policy clause refuses with exit 2; `gate --report`'s four
      under-definitions (no changelog entry, `--report` required-or-discovered, behaviour over an
      `unanalyzed` report, provenance posture); the locale clause's two readings (code-point everywhere vs
      environment-independence only); `--class`'s value grammar and unrecognised-token behaviour;
      `blindspots --stats` / the `reports` verb / `encountered-*` are **named and never defined**.

### 3 — CLOSE THE STRUCTURAL GAP WITH SELF-DIFFERENTIAL PROPERTIES · the highest-yield row here

**The gap.** Conformance asks *"do the engines agree?"* All four share one spec, one set of design docs
and one author's mental model, so when that model is wrong all four implement the same wrong thing and
the suite reports OK. It has done exactly that twice — the coverage door and the malformed manifest were
both four-way. PAPER2 already names this (Knight & Leveson; *"engine agreement is the weakest signal"*);
what has been missing is a second oracle for the CONTRACT layer.

**Two findings that make this cheap.**

1. **The whole scan-boundary vein is ONE property, hand-instantiated 44+ times.** Every "two-tree fixture
   with its single-tree control" — 44 mentions of `single-tree control` across 13 files, 56
   chained-vs-unchained assertions — is an instance of *`scan(A ∪ B)` ≡ `scan(B)` chained with
   `report(A)`, modulo disclosure*. A human wrote each one and chose each shape, and **five fixtures this
   week could not reach the code they named** because the shape was wrong.
2. **`conformance/gen_differential.py` already exists** — an EFFECT × INDIRECTION matrix rendered
   semantically-equivalently in all four languages, built to "extend in ONE place". It has precisely the
   two limitations that ARE the gap: it generates SINGLE-TREE programs, and it asserts CROSS-ENGINE
   agreement.

**The move: change the axis, not the machinery.** Add a SPLIT dimension to that matrix (render each case
both as one tree and as two chained packages), and change the assertion from *"the engines agree"* to
**"each engine agrees with ITSELF across the split."**

That second half is the point. **A self-differential is immune to common-mode by construction.** Four
engines can share a wrong model of the spec; an engine cannot share a wrong model with ITSELF across two
renderings of the same program. The engine's own single-tree answer is the oracle for its chained answer —
no reference implementation, no second opinion, no spec interpretation in the loop.

- [x] **P1 — SPLIT-INVARIANCE. BUILT AND WIRED IN — `conformance/gen_split_invariance.py`, conformance
      PART 24 (`75b7044` + `41216aa`).** 8 effects × 10 split shapes = 80 cells, each rendered in all four
      languages and scanned BOTH as one tree and as two chained packages; the assertion is that each
      engine agrees with ITSELF. Reuses `gen_differential.py`'s EFFECTS table so the effect vocabulary
      stays in one place. **Counts: 80 cells, 80 LIVE, 0 vacuous, on every engine.** (`direct` is the one
      shape with no dep half — its sink is inline in the entry — so it is named and not rendered: 8 more
      cells, structurally vacuous.) ~45s for the full four-way matrix.

      **VERIFIED TO CATCH**, on two engines, by reverting a shipped boundary fix in an isolated worktree
      with its own build dir — never the shared binaries (item 7f): candor-ts `625e8fd` → the 8
      `implicit_conv` cells go ABSENT, **ts only, its other 72 unchanged**; candor-rust `1623a07` → the
      same 8 cells, **rust only, ts and swift unchanged**. Each fires on exactly the shape whose fix was
      removed and on exactly the engine that was mutated.

      **AND IT FOUND FOUR LIVE DEFECTS ON HEAD, ON ITS FIRST RUN**, every one of them the same shape of
      thing: *the dependency's report already carries the witness under exactly the key the consumer
      needs, and the consumer's join has a branch that does not fire.* All four are baselined in
      `conformance/split-invariance-baseline.json`, each with a hand-written two-package repro, so no
      waiver rests on the generator being right. **They are engine work, not conformance work — §3c.**

      Two durable notes, both learned here. (a) **A rendering choice can weaken the ORACLE, and nothing
      but the vacuity count will say so.** The first draft spelled the rust app half `deplib::X` (a
      `pub mod deplib` wrapper in the single-tree arm) and that alone made **16 of rust's 80 cells
      vacuous** — candor-scan resolves neither a module-qualified unit-struct value literal (`m::T.run()`)
      nor a module-qualified lazy-static read (`*m::L`), so the single-tree arm went silent and those rows
      stopped demanding anything. Verdict unchanged, signal gone. That is item 8 in a new costume.
      (b) **The assertion must stay DIRECTIONAL.** An effect that becomes `Unknown` across the split is a
      HEDGE — counted, never failed — because PART 21's ruling is precisely that a consumer which cannot
      form a key MUST disclose where the single-tree arm resolves. Simplifying it to equality would fail
      every case the family has already decided is correct. Both are written into the file at length,
      because someone will later try to "simplify" it.

      Bonus, not this row's job: rust charges a lazy-static read to its reader inside the same module but
      **not through a module path** — `m::INNER` from outside `mod m` reads pure while `INNER` from inside
      it reads `['Fs']`, single tree, no boundary involved. Filed at §3c as a separate finding because it
      is a plain single-tree under-report, and P1 correctly does NOT fail on it (the property is
      directional and this weakens the oracle rather than the chained arm).
- [x] **P2 — BUILT, conformance PART 25.** 80 cells × **3 duplication arms** (byte-identical, renamed,
      re-serialised — an engine deduping on file bytes would pass two of them). Relation = **EQUALITY
      including disclosure**, justified with numbers: java/ts/swift are exactly equal on **216/216** live
      cells, so unlike P1 there is no legitimate asymmetry to permit.
      **FINDING: candor-rust is not chain-idempotent, on all three spellings.** Chaining a byte-identical
      report twice WITHDRAWS the key — effect gone, package re-declared `uncovered`, `deny Fs` **exit 1 →
      exit 0**. That is the ENTRY-COLLISION union decision's own defect, now gated.
      ORIGINAL — P2, chain idempotence. Would have caught the
      identical-entry withdrawal (`6f2210c`) — two byte-identical reports made a consumer vanish from
      `functions`.
- [x] **P3 — BUILT, conformance PART 26.** 80 cells × **7 degraded arms** against two reference arms.
      Relation = a **SANDWICH**, `unchained ≤ degraded ≤ trusted`, with direction stated per arm — and the
      BESIDE arm **inverts**, which had to be discovered: judging BESIDE by the REPLACE rule reports nothing
      about java's erasure, judging REPLACE by the BESIDE rule fails all four for the *correct* §2.1
      downgrade. Both κ and `Unknown` count as disclosure (measured — counting only `Unknown` would have
      filed a false cardinal loss on rust and ts).
      **rust + java let a distrusted copy BESIDE the trusted report erase it** (rust withdraws, java's §2.1
      downgrade writes `{Unknown}` over the `Fs`); ts unions and swift ranks trust first, both clean.
      ORIGINAL — P3, trust monotonicity. An untrusted or incomplete report can only REDUCE what a consumer
      claims, never increase it. Would have caught the coverage door in all four engines, and java's
      stale-`{Unknown}`-erasing-a-trusted-effect (`deny Fs` exit 1 → 0).
- [ ] **P4 — SIGNATURE MONOTONICITY.** Adding a call cannot remove an effect or a reason class. Would have
      caught the Lemma 2 violation. **Blocked on the gate-a-report verb below** for the class half.

**What this will NOT catch, and it is the right thing to leave out:** the classifier. If candor does not
know `Foo.bar()` performs `Net`, single-tree and chained agree on the same wrong answer and no property
here fires. That is the runtime oracle's job, the instrument exists, and it is calibrated.

- [x] **CLOSED — LOCALE-SENSITIVE ORDERING (candor-ts `6502b56`, SPEC §2 ⟨0.24⟩ `e3e61d6` + `aa82937`).**
      Raised by the ts engine as out of scope for its own task, which was the right call twice over.
      **7 call sites** (not 8 — one grep hit is a comment), one of them ordering the κ-coverage ledger
      **inside the emitted report**. Wider sweep found nothing beyond the list: no `Intl.Collator`, no
      `Intl` at all, no `toLocale*Case`.
      **OBSERVED, not latent** — same build, same tree, environment only:
      `LC_ALL=C` → `uncovered = [tpad, zpad]`, md5 `8ad6e50a…`; `LC_ALL=et_EE.UTF-8` → `[zpad, tpad]`,
      md5 `d5b2cac1…`. Estonian collates `z` between `s` and `t`. Post-fix: C / et_EE / da_DK / tr_TR give
      four identical md5s.
      **THE CONTROL I PROPOSED WOULD HAVE MISSED IT.** I briefed C-vs-`tr_TR` on the dotless-i reasoning.
      Turkish inserts its extra letters BETWEEN the ASCII ones, so pure-ASCII relative order is unchanged —
      the experiment returns "no difference" and licenses "latent, not observed", which is false. The agent
      chose `et_EE`. **I spent the day telling agents a fixture that cannot show the gap is not a control,
      then wrote one.**
      **And the deeper correction: ASCII DOES NOT PROTECT YOU.** The whole day's collation reasoning ran
      "our identifiers are ASCII, so UTF-16 and code-point order agree" — true, and it is why THAT risk is
      latent. **Locale collation reorders pure ASCII**: the ledger keys are lowercase npm package names,
      exactly the case that argument declares safe. Danish breaks a second ASCII pair (`aa` = `å`, so
      `aardvark` follows `z`).
      **The ~10 bare `.sort()` sites that write REPORT BYTES are CHECKED AND NOT A DEFECT** — recorded so
      nobody re-opens them. `calls`/`hosts`/`tables`/`cmds`/`paths`/`unknownWhy`/`invisible` and
      `analyzedQuals` (which feeds `analyzed.digest`) are UTF-16-ordered, hence **deterministic and
      environment-independent** → §2-clean. They are not code-point-ordered, which would only matter for
      CROSS-engine byte comparison — and §2 defines `digest` as *"an opaque, **within-engine**-comparable"*
      value, so no such claim exists to break. The §3.1 collation rule binds the one joined field it names.

- [→] **P2 (chain idempotence) + P3 (trust monotonicity) DISPATCHED** into `conformance/`. Both picked next
      because both are **regression-shaped**: P2 would have caught rust `6f2210c` (two byte-identical
      reports made a consumer **VANISH from `functions`**), P3 would have caught the coverage door **in all
      four engines** plus java's stale-`{Unknown}` erasing a trusted effect (`deny Fs` exit 1 → 0).
      Briefed with every P1 judgment call restated as a CONSTRAINT rather than a suggestion, since those are
      what kept P1 from being a worthless artefact: no expected-value table; vacuity earned with a refusal
      on zero live cells; ratchet-not-red with a both-ways baseline; **the RELATION justified with numbers**
      (P2 is probably genuine equality, P3 is explicitly DIRECTIONAL — subset-or-equal, never-more-
      confident); verified-to-catch in **isolated worktrees** (rust and ts have live agents, standing bar
      7f); and **every guard made to fire**, which is how P1 found the defect in its own harness.
      **P4 is now UNBLOCKED** by `gate --report`.
      **MY FIFTH CONCURRENCY SLIP, caught before it bit**: I told this agent it was the only writer in
      `conformance/`. It is not — the rust agent is deleting its own waivers from
      `split-invariance-baseline.json`, which lives there. Corrected mid-flight: that file is shared, P2/P3
      get their own baselines, and a `STALE WAIVER` failure right now is most likely the other agent's fix
      landing rather than a defect.

### 3c — WHAT P1 FOUND ON HEAD · per-engine, parallel, each already reduced to a fixture
Four defects, found by P1 on its first run (2026-07-27) and each then re-derived from a hand-written
two-package fixture so none of them rests on the generator being right. All four are baselined in
`conformance/split-invariance-baseline.json`, which carries the repros; deleting the entry is part of
the fix, because the ratchet FAILS on a waiver whose defect is gone.

**One sentence covers all four: the dependency's report already carries the witness under exactly the key
the consumer needs, and the consumer's join has a branch that does not fire.** That is "the template that
works" from further down this file, and it means none of these should need a report-format change.

**And the reason PARTs 18–22 could not see any of them is the same in every case: each hand-written
fixture picked ONE spelling.** This is finding (1) at the top of §3 — a human chose each shape — landing
with four concrete instances rather than an argument.

- [x] **ALL THREE FIXED — candor-rust `ca27ecc`, waivers retired `e995c51`, `known` now EMPTY four-way.**
      No report-format change on any of them — *"emit the call shape the join already understands"*, third
      time running.
      **THE `5447eba` VERDICT IS *YES*, AND FAR WIDER THAN THE FILING.** Measured three ways on one fixture
      (`use crate::ROOT_CFG;` from a submodule — the ORDINARY shape, not the filing's inline `mod m`):
      | | same module | 4 cross-module spellings |
      |---|---|---|
      | before `5447eba` | `Fs` | **`Fs`** |
      | at HEAD | `Fs` | **PURE** |
      | after | `Fs` | `Fs` |
      `5447eba` made the WRITER module-qualified while the READER still built `<lazy>::<its own module>::
      NAME`. **A fabrication fix that introduced a cardinal sin** — and at HEAD *any* crate-root lazy static
      read from *any* submodule read pure. The identity property it bought is preserved.
      [[feedback-fabrication-fixes-cause-misses]] landing again, established by measurement rather than
      asserted.
      **THE AGENT CAUGHT A LIVE FABRICATION IT INTRODUCED ITSELF**: its first cut charged `deplib::C`'s
      `Env` to `let C = "aa"; C.len()`, because the five typed side-tables answering "is this shadowed?"
      only hold bindings **whose type resolved** — harmless while only a qualified path could force, live
      the instant the bare spelling was added. Its own mirror control found it.
      **MY CONTROL WAS WRONG, for the second time today.** I specified *"an unbound call to a factory the
      dep report shows as PURE must stay pure"*. That contradicts the ⟨0.24⟩ ruling — a `by_key` miss cannot
      distinguish "no such method" from "I withdrew an ambiguous entry", so the BOUND form discloses there
      too, and making the unbound form stay pure would have made it **diverge** from the bound form,
      recreating the defect. Rewritten as **equality with the bound form**, which is what the property
      itself asserts.
      **A/B: 0 concrete effects gained, 0 losses, four targets.** But **95 of 550 ebman functions newly
      carry `Unknown`** (direct `dispatch:untyped cross-package receiver` 18→52, ≈2.9× the bound arm) —
      squarely in the 8–25% false-uncertainty band `COVERAGE-GRANULARITY-FINDING.md` measured. Shipped at
      **PARITY** rather than narrowing, correctly: a denylist on one spelling only recreates the exact
      defect class this row exists to close.
      - [x] **ANSWERED, and 95/550 IS REAL — the disclosures are honest.** The third conjunct IS applied:
            it lives on the SHARED consumption path, and the fix was emission-side only, so both spellings
            emit the same marker shape and pass the identical gate. **Instrumented at the marker, before the
            gate**, rather than inferred:
            | | markers | CHAINED | UNCHAINED (suppressed) |
            |---|---|---|---|
            | ebman alone | 53 → **141** | 32 → 73 | 21 → **68** |
            | whole dep-tree walk | 53 → **22,131** | 32 → 73 | 21 → **22,058** |
            **The conjunct suppresses 99.7% of the new arm's markers**, and exactly its remit: `std` (52),
            `String` (7), local modules — not one a real dependency. Of the 95 gains: **0** have no chained
            marker, **0** are backed only by an unchained one. `chrono` and `serde_yml` are chained with
            substantial reports (191 and 337 fns). **None is the false-uncertainty shape.**
      - [ ] **NEW LEAD, and it is better than a denylist — `6f2210c`'s rule, one index over.** Chasing WHY
            the chained markers miss: of ebman's 73, 10 resolve, 6 miss on a module-qualification mismatch,
            and **57 are genuinely absent from the published surface — of which 37 are chrono's `Utc::now`
            alone, and its absence is a SPURIOUS COLLISION.** chrono declares `pub fn now() -> DateTime<Utc>`
            **twice**, under mutually exclusive `#[cfg]`s (native / wasm32). The scan walks both arms by
            design, the return index sees two same-named defs, and its never-guess rule drops the entry —
            **even though both candidates name the SAME return type. There is nothing to guess between.**
            The report already carries `offset::utc::Utc::now ['Clock']`; only the return type was withheld.
            **This is the ENTRY-COLLISION union decision (`b47c9ab`) applied to the RETURN index instead of
            the entry index** — same principle: *when the colliding candidates AGREE, the collision is not a
            reason to withhold.* Worth naming as a general rule, because it has now arisen twice in two
            different indexes on the same day.
            Recovers **>half** of ebman's chained untyped markers, **additively**, by **DETERMINATION rather
            than SUPPRESSION** (the ⟨0.24⟩ ordering), and **on both spellings at once** — so it cannot
            disturb the parity just accepted. Producer-side; needs its own A/B.
      - [ ] **Caveat worth a look, and it is P3's shape:** `futures@0.3.32`'s chained report is **EMPTY
            (0 fns)** and accounts for 2 of the newly-direct fns. **An empty chained report reads as
            "covered, no effects"**, so the κ ledger stays silent and the disclosure is the only voice.
            That is trust-monotonicity territory — an empty report licensing purity claims for everything
            in the package. Flagged to P3. PART 21's guard is *untyped receiver AND
            dep provenance AND **the dep is CHAINED***. The third exists precisely for the shape topping the
            list (`chrono::Utc::now().signed_duration_since(..)` ×16 — a std combinator on a dep-returned
            value), because for an UNCHAINED dep the κ ledger ALREADY says `invisible: [pkg]` and a second
            hedge is pure false uncertainty. The naive two-conjunct form measured **5.4%** on the JVM; with
            the third, **0** unchained / 0.4–0.5% chained. **Asked the engine to split the 95 by
            chained-vs-unchained.** If a meaningful share are unchained the conjunct must extend to the new
            arm — **on both spellings**, preserving the parity argument.
      ORIGINAL FILING — rust, a chained dep's lazy static is charged only through a PATH-QUALIFIED read.**
      `deplib::C.len()` → `['Env']`; `use deplib::C; C.len()` → **absent**. Deref vs method call makes no
      difference; the `use` does. PART 19's rust fixture uses the qualified spelling.
- [x] **ALL THREE rust §3c FIXED `ca27ecc`** (see the block above for the `5447eba` verdict).
      ORIGINAL — rust, a chained dep FACTORY call with NO intermediate binding reads silent-pure.**
      `let c = deplib::build(); c.fetch()` → `['Fs']` (resolved); `deplib::build().fetch()` → **absent**.
      `let t = deplib::get_dyn(); t.run()` → `['Unknown'] dispatch:untyped cross-package receiver`;
      `deplib::get_dyn().run()` → **absent**. A hole in a SHIPPED guard, not an un-attempted precision
      gap — and it violates PART 21's own ruling that an unformable key must not read pure. PART 21's
      rust fixture binds the factory result.
- [x] **FIXED candor-swift `e02bff7` — and the A/B was DECISIVE, not confirmatory.** Both reproduced
      exactly as filed, plus **a THIRD spelling the filing did not name**: `static var` (`SC.s`), alongside
      `lazy var` and plain computed `var`. Fixed with no report-format change — the brief's "the witness is
      already under the key" sentence held for both.
      **The A/B caught an over-fire the fixture could not**, which is the standing result restated: A/B on
      real code is BOTH the fabrication gate AND the value estimator. `xs.map(String.init)` is a member
      access with member `init`, and swift-syntax publishes `SwiftSyntax#String.init` for its own extension
      — so the join charged that to callers of the **stdlib** initializer. Excluded `.init`/`.self`/
      `.Type`/`.Protocol` as a class. The agent also added `CANDOR_DEPMEMBER_DEBUG=1` because *the diff
      showed which functions moved and never which KEY moved them* — which is exactly why the over-fire was
      invisible. That instrument is the durable part.
      A/B: unchained 8 real targets, **3082 entries, 0 changed** (inert without a dep report, by
      construction). Chained candor-swift ← swift-syntax: **+35 functions, all `Unknown`-only, 0 new real
      effects, 0 losses**; all 99 join hits are SwiftSyntax node accessors whose own dep entries are
      `Unknown`, **0 hits on any Foundation/stdlib type**.
      **`unboundPure` gains `Unknown` and that is CORRECT** — measured against the BOUND spelling first: a
      dep factory whose product is pure has no report entry, the key MISSes, and it falls to PART 21's
      disclosure. `boundPure` already did this on HEAD. Matching it is the invariant; anything else
      re-creates the divergence.
      Baseline entries deleted (`bda00a5`); cells flipped `A`→`.` (lazy_init, exact) and `A`→`h`
      (fn_returned_dyn — **now identical to java and ts, so the four-way divergence is CLOSED**). Ratchet
      verified in the other direction: with the entries restored it reports FAIL (STALE WAIVER), exit 2.
      ORIGINAL FILING — swift, a chained dep type's PROPERTY ACCESSOR read is silent-pure.** The dep report carries
      `L.v ['Fs'] accessor` and `C.w ['Env'] accessor`; the consumer's `l.v` / `c.w` are absent. **Not
      lazy-specific — a plain computed `var` behaves identically**, which makes this much wider than the
      cell that found it. PART 19's swift fixture reads a module-level GLOBAL, which IS modelled, so the
      accessor form had never been asked.
- [x] **FIXED with the above (`e02bff7`)** — the two spellings now share one guard by construction
      (`CallCollector.depFactoryCallee(_:)`), rather than the inline binding-only check.
      ORIGINAL FILING — swift, the same unbound-factory shape as rust**, with the same asymmetry: `let t = getDyn();
      t.run()` discloses and `let c = build(); c.fetch()` resolves, while `getDyn().run()` and
      `build().fetch()` are both absent.
- [x] **FIXED with the above.**
      ORIGINAL — rust, single-tree, a lazy-static read through a MODULE PATH is not charged.**
      `mod m { pub static INNER: LazyLock<u8> = …Fs…; pub fn inside() { let _ = *INNER; } }` charges
      `m::inside` correctly; `fn outside() { let _ = *m::INNER; }` reads **pure**. The unit is emitted as
      `<lazy>::m::INNER ['Fs']`, so the writer knows; the reader-side edge does not make the hop. Worth
      checking against `5447eba` (which moved the module path INSIDE the `<lazy>::` prefix to stop
      same-named globals merging) — if the reader still keys on the bare name, that fix bought identity
      at the cost of this edge, which is [[feedback-fabrication-fixes-cause-misses]] exactly.

**Two of these put rust and swift SILENT where java and ts both disclose `Unknown` on byte-identical
input** (the `fn_returned_dyn` pair). That is a four-way divergence on a decided contract, which is the
class of thing PARTs 18–22 exist to catch — and each of them fixes one spelling, so none could.

- [ ] **OPERATIONAL, new today: the full suite now exceeds 50 MINUTES.** A `timeout 3000` run reached
      **PART 25 of 27** and was killed — PARTs 24–27 all landed today and are the heaviest (P3 alone is 80
      cells × 7 degraded arms × 4 engines, each arm a real scan). PARTs 1–25 were green in that run;
      26/27 had to be run directly via their generators.
      Two consequences to decide, not urgent but real: **CI wall-clock** (a suite people cannot run is a
      suite that stops being run — which is the same failure mode as a permanently-red row, and the reason
      the property PARTs are ratcheted rather than red), and whether the property PARTs should be **a
      separate tier or leg** from the differential PARTs so a fast pre-commit path still exists. Note the
      generators are individually runnable with `--baseline`, so the mechanism for splitting already
      exists.

### 2c — WHAT THE TARGETED REVIEWS FOUND (2026-07-27/28) · one real defect, in the least-covered component

Three lenses, each chosen for a NAMED reason to be under-checked rather than for generic diligence:
candor-agents (four clauses in one pass, verdict-changing, **no conformance PART covers it at all**), the
four independent `--class` fixes (fabrication-mirror risk), and my own floor bump (the only work of the day
not written by an agent and checked by a second party).

- [x] **FINDING 1 FIXED (candor-agents `f83b3c8`) — reproduced exactly, and the agent CORRECTED MY BRIEF.**
      `link_code_report` now resolves each linked report's **own transitive** reason classes (the
      `.callgraph.json` sidecar **unioned with the rows' `calls`**, so it works sidecar-less) and seeds them
      into the direct map before propagation. Post-fix: `[dispatch]` → exit 1 with
      `reasonClass: ["dispatch"]`; `[unresolved]` → exit 0; bare/`[*]`/`[dynamic]` unchanged.
      **THE MUTATION TABLE IS THE EVIDENCE, and its middle row is the good one:**
      | mutation | result |
      |---|---|
      | seed dropped (= pre-fix) | **12 of 13 fail** — survivor is the non-fabrication pin, correct in both states |
      | **seed from the entry's DIRECT `unknownWhy`** (the tempting wrong fix) | **exactly the 4 inherited-case checks fail** |
      | source-side fail-close removed | the masking check flips to exit 0 — the under-report restored one layer up |
      That middle row is the whole point: `unknownWhy` is direct-only by §4 design, so seeding from it looks
      right and silently misses every case where the code report's `Unknown` is reached a frame deeper.
      **MY BRIEF WAS WRONG and the agent said so.** I asked that `[unresolved]` behaviour be "unchanged —
      all four still fire today", but direction 2 REQUIRES `[unresolved]` to **stop** firing on the
      linked-dispatch unit; that is the fabrication half. It scoped "unchanged" to the unlinked fleet
      (where every pre-existing check passes untouched) and pinned the correct behaviour instead of the
      one I asked for.
      Also: a linked `Unknown` with no resolvable reason now contributes `unresolved` **at the pseudo-node**
      rather than via the join's empty-`classes` arm — without which a unit inheriting BOTH a classed and a
      classless linked `Unknown` has a non-empty set, never reaches the net, and is dropped by every
      narrowed filter. And `classify_reason`'s code-prefix table is **no longer dead**; its docstring now
      names the single production path instead of claiming one it did not have.
      463 checks / 0 failed on Python 3.9 and 3.12.
      ORIGINAL — FINDING 1: §6.2's transitive class resolution STOPS AT THE `--link` BOUNDARY — and BOTH failure modes the spec names fire at once.** The gate's `Unknown` reach
      includes linked code entrypoints; the CLASS resolution does not (`link_code_report` keeps only
      `inferred`; `build_functions` drops the pseudo-node; the code report's `unknownWhy` never reaches
      `transitive_reason_classes`).
      - `deny Unknown[dispatch] runner` → **exit 0** on a unit whose transitive `Unknown` is *exactly*
        dispatch-classified — requirement 2's failure text verbatim, *"excluded by every filter, including
        one naming its own class."* **An under-report.**
      - `deny Unknown[unresolved] runner` → **exit 1**, charging `unresolved` to an `Unknown` correctly
        classified `dispatch` at its source — **the mirror fabrication requirement 3 forbids**, firing
        through the absence-keyed arm CONTRIBUTES exists to replace.
      - The verdict **omits `reasonClass` entirely**, which the spec makes a MUST.
      **THE TESTS COULD NOT SEE IT, for the reason I made a MUST hours earlier**: the existing `--link`
      control uses `unknownWhy: ["banana:whatever"]`, which classifies `unresolved` ANYWAY — so it passes
      whether or not linked reasons are consumed at all. *"A control only exercised by inputs the
      implementation already handles is not a control"* — written into §4 this afternoon, and violated in a
      test written this evening.
- [ ] **FINDING 2 (judgment, well-argued, NOT dispatched): the `Net[…]` widening.** The fail-open IS closed
      (old dropped the rule and exited 0; new exits 1, both reproduced). But `deny Net[known-telemetry]` now
      fires on **all** `Net` — fail-closed and loud, yet a legitimate narrow rule becomes a permanent red on
      any `Net`-holding fleet. **The reviewer's counter is the strong part**: the commit argued "no
      `netClass` is emitted, so honouring it would fail open", which elides that §6.2's classifier is
      defined fail-closed over HOST LITERALS — and this engine *does* have `cmds`/`hosts` surfaces, so
      everything not positively identified is `unknown-host`. That is implementable, and for
      `deny Net[unknown-host]` it would coincide with what shipped. Exit-2 refusal (the §3.1 answerability
      precedent) was the other spec-consonant option. Also: the widening is disclosed on **stderr only** —
      `--gate-json` carries no record that the rule's semantics changed, so a SARIF/CI consumer sees
      violations under a rule text whose meaning was silently altered.
- [ ] Minor, from the same review: the widening message is Net-specific wording for any bracketed effect
      (`deny Fs[x]` gets "scopes by destination class"); and the candor-query parity harness never feeds a
      bracketed form, so **cross-impl agreement on the new grammar is unpinned** — while
      `deny Net[unknown-host]` verdicts now deliberately diverge from candor-rust's, with the divergence
      nowhere recorded as deliberate.
- [x] **Verified sound, each checked against the claim rather than taken from the commit message**: `pure`
      (A/B both directions, non-tautological control), `Llm` (single-sourced, co-emits `Net`, `Db` alone),
      the `Unknown[class]` grammar (bare ≡ `[*]` ≡ `[unresolved]` ≡ `[dynamic]`, and the
      all-unrecognised→ALL fallback is the correct SIDE because the exit-2 rule is explicitly the
      query-side flag and this engine ships no §3.1 verb), CONTRIBUTES gating within fleet reach, the
      sidecar denylist (all seven, trailing-segment-only), and the locale control (non-vacuous in fixture
      AND platform, with a disclosed SKIP rather than a vacuous pass).

### 2d — THE ts `--class` OVER-FIRE · a GATE-LEVEL FABRICATION, and the reviewer called it unreachable

- [x] **FIXED candor-ts `72a9b51`. Both triggers reproduced at the shipped CLI — and a THIRD, which the
      reviewer had judged unreachable BY INSPECTION and which a RUN proved live.**
      `reasonClassesMatch` returned `true` on an empty class set, so an unclassifiable hole matched **all
      six classes**. Four-way before: rust `[]`, java `[]`, swift `[]`, **ts `['app.orphan']`**.
      **THE THIRD TRIGGER IS THE SERIOUS ONE — A GATE-LEVEL FABRICATION, LIVE.** Driven over the real MCP
      stdio transport (`candor_gate`, a shipped surface that runs `evaluatePolicy` over a **loaded —
      possibly FOREIGN — report**), `deny Unknown[reflect] app` **FIRED** on `app.orphan`, with **no
      `reasonClass` on the violation record** because the set it matched on was empty. The LSP shares the
      same call.
      **The reviewer's "unreachable" was a code-inspection judgement and it was wrong.** Its argument — ts's
      emitter writes `["unresolved"]` on any unnamed direct `Unknown`, plus the exit-2 self-check — holds
      for ts's OWN reports and says nothing about **MCP/LSP, which read whatever report they are pointed
      at.** The fixer answered it with a run instead, which is the standing rule at the highest possible
      stakes: *a judgement about reachability is a hypothesis until something executes it.*
      Fix, both halves: project empty → `{unresolved}`, and build the edge set from the report's own §2
      `calls` **unioned** with the sidecar (union, not either-or — the sidecar can carry edges an older
      report's entries lack, and more edges only ADD classes, the fail-closed direction). The residual
      genuinely-degraded case (no sidecar AND no `calls`) is now **disclosed on stderr**, the channel a
      *corrupt* sidecar already used while an *absent* one said nothing.
      **Four-way agreement: 4 fixtures × 8 filters = 32 comparisons, 0 diverging** (8 diverged before), and
      byte-identical with and without the sidecar.
      **IT CORRECTED MY BRIEF AGAIN**: "must NOT match `--class unresolved`" applies to the **no-sidecar**
      case only. A genuine orphan callee DOES match `unresolved` in rust, java and swift — that is exactly
      §6.2's projection. Only the no-sidecar-but-classified case must escape it. Both are now asserted.
      - [ ] **One piece of coverage deliberately NOT added**: the CLI-level arm in `test.mjs` beside the
            existing `unverified --class` e2e block, because the doc-sweep agent was editing that file
            concurrently and writing it risked clobbering in-flight work. Verified by hand instead (byte
            identity over 8 filters ± sidecar, plus the disclosure). **Add it once ts is quiet.**

### 2e — THE 2026-07-28 REVIEW ROUND · 14 defects, ordered · **THIS IS THE TOP OF THE QUEUE**

Three lenses (empty-report four-way, `gate --report` four-way, my own harness/preflight). Two clean
results worth naming first: **the MUST NOT holds four-way** with every bait live SIMULTANEOUSLY plus a
fourth channel the reviewer opened, and **byte-equality is genuine and non-vacuous** in both new engines,
reproduced live on scan-produced reports. `_rust_scan`/`_ts_scan` verified real by mutation battery.

**A — REFUTES A MUST. Do first.**
- [ ] **rust: count-0 breaks byte-equality against RUST'S OWN SCAN.** Same policy, the report the scan just
      wrote: `scan` exit 0 with a verdict, `gate --report` **exit 2 and no document written**. ~7–10% of
      real dep reports. `ci/gate-equivalence.sh`'s 90 rows cannot reach it — every corpus crate has
      functions. **Fix per the corrected §3.1** (`0744d29`): caveat on stderr, exit and document unmoved.
- [ ] **rust: incomplete analysis SWALLOWS the violation and the verdict DROPS it.** `gate.rs:558-565`
      writes `&mut []` before violations are recorded → exit 2, `violations: []`, **a real finding absent
      from the artifact**. §3.3 settles it: *"a real violation (exit 1) still dominates."* java/swift/ts
      right, rust wrong on BOTH routes.
- [ ] **java + swift: `gate --report` prints the literal string the clause forbids** — "no violations",
      exit 0, **stderr 0 bytes**. Neither commit touched the gate verb; both already collect
      `analyzed.count` and never test it.

**B — FAIL-OPEN, four-way, in the NEW machinery.**
- [ ] **A scoped `deny Unknown[C]` under-refuses when the unknowable hole is REACHED FROM in-scope code.**
      All four exit 0 where the unscoped form exits 2; **the control is decisive** — supply the reason and
      all four exit 1, so the absent datum DOES change the verdict and §3.1's minimal-refusal rule requires
      a refusal. Every engine tests answerability on the in-scope function's own post-fixpoint set, so a
      hole one edge away is tolerated. **Fix: propagate "contributed nothing determinable" through the
      fixpoint; refuse on an INCOMPLETE set, not only an empty one.**
- [ ] **swift: `analyzed: {count: true}` reads as JUDGED** — Foundation bridges `NSNumber(bool:)` through
      `as? Int`. Byte-identical to `count: 2`; the caller drops out of `functions`. **Specced `18fb770`.**
- [ ] **rust: a malformed `unanalyzed` manifest is silently dropped** (`.ok()…unwrap_or_default()`) →
      exit 0 where the other three exit 2. `unanalyzed` non-emptiness IS the fail-closed trigger.
- [ ] **ts + java: a partially-corrupt multi-report prefix gates GREEN** — the dropped member is exactly
      where the violations could live, and the omission is machine-invisible (`incomplete:false`,
      `ok:true`, `analyzed.count` silently excludes it). rust and swift refuse.

**C — SPEC RULINGS I OWE.**
- [ ] **Pin the `unknown-alias` config ANCHOR.** The gate anchors at the POLICY dir, the scan at the
      TARGET — so with a config inside the scanned tree and the policy outside it, the two routes disagree
      **and byte-equality is broken by an ambient file.** `CANDOR_CONFIG` alone flips 1→0, so the verdict
      is not a pure function of (report, policy). Uniform four-way, so no divergence — but unstated, and
      all four MUST-NOT tests miss the bait.
- [ ] State **refusal-vs-violation precedence** and the **no-verdict-on-refusal** rule (a CI wrapper can
      re-read a STALE verdict file as current).
- [ ] `analyzed:{count:0}` in the verdict for a **pre-⟨0.21⟩ manifest-less** report now collides with the
      token that means "judged nothing".

**D — MY HARNESS/PREFLIGHT. CLOSED 2026-07-28** (`fff7bdf`, `5b535c9`, `96fedca`, `36a38c0`, `7caea30`,
`c35e29d`). Every item below is fixed and each fix carries its own negative control, run. Two things worth
keeping from the round. First, **three of the five were the same defect wearing different clothes: a check
whose subject and whose oracle came from the same source.** PART 23 derived the expected lattice size by
importing the module it was checking; PART 10's control asserted properties of the sets the decision reads
instead of running the decision; R1's cell accepted the code that a *failed invocation* also returns. In
each case the check passed for a reason unrelated to the thing it was written to detect. Second, **the R1
fix landed on a SPEC correction, not on harness cleverness** — once §3.1 said the entry contributes
`unresolved` so the rule fires, `exit 1` became the only correct code, and requiring exactly 1 is
incidentally immune to the usage-error collision the review found. A tightened spec made the test sharper
for free.
- [x] **R1's gate cell passes on an engine with NO `gate --report` at all** — adding rust/ts branches killed
      the `None → NOSURF` path, and `OK if rc_g in (1,2)` accepts **2, the generic usage-error code**. R6
      catches it three ways because it carries a firing control; R1 does not. **Give R1 a firing control.**
- [x] **PART 23's derived floor is CIRCULAR along the vocabulary dimension** — it imports the module it
      checks, so removing `Ipc`/`Clipboard` (the exact historical defect) self-adjusts and passes. The
      SPEC-vs-model comparison is an `echo` that **never sets `P23_OK=1`**. Enumeration dimension is sound.
- [x] **PART 10's negative control tests the SETS, not the decision path** — neutralise the loop's DIVERGE
      branch and `banana:whatever` is accepted while the self-check prints green.
- [x] Stale coverage prose in `gen_rung024.py` + `run.sh` (still says R6 is 2-way); `bad()` sets `fail=1`
      rather than incrementing, so the summary always reads "1 check(s) FAILED".

**E — pre-existing, lower.** java's multi-report locator gates only ONE report; java's `interfaceUnion`
entries gated as ordinary functions (byte-equality refuted on self-produced output); corrupt entries read
as purity claims (swift keyless, three engines on non-string `inferred`); swift's verdict uses `modules`
where three use `packages`; java's conflict rule is EMERGENT with no test and its advisory is a **false
disclosure** in that case.

### 3d — WHAT P2/P3 FOUND ON HEAD · the four-way one is a CARDINAL SIN with a proven fix path

- [→] **SPECCED (§2 ⟨0.24⟩ `34f8443`, harm restated `400e8e1`) and IN FLIGHT four-way.**
      **swift LANDED `b41b1df`.** Placement — `Deps.swift`'s `loadDepReports`, beside the ⟨0.21⟩
      `incomplete` computation, **consumer-side coverage bookkeeping, NOT the gate**. Its reasoning is the
      part to keep: *"coverage is the single mechanism that turns a report's silence into a purity claim,
      and this is the THIRD answer to 'may this silence speak?' after staleness (§2.1) and incompleteness
      (⟨0.21⟩)."* Gate placement would have fixed `deny` and left the report, the κ ledger and every other
      consumer of the same silence untouched. No new plumbing — withhold coverage and `blindModules`,
      per-fn `invisible`, `coverage.uncovered` and the verdict caveat all fall out.
      **The two reconciliations run in OPPOSITE directions, following what the second report SAYS**:
      `incomplete` makes a NEGATIVE claim about its source, so it beats a complete sibling; `count: 0` makes
      NO claim, so a package chained once judged and once not **keeps** coverage.
      **MUTATION 2 IS WHY THE SECOND ROW HAD TO BE A CONTROL**: hedging both rows reddens the control **plus
      8 pre-existing coverage tests** including `testEmptyDepReportIsAPurityClaim` — the deleted-feature
      signature — **while the FLOOR test stays GREEN.** The floor arm alone cannot be trusted.
      **BLAST RADIUS: 1 in 37.** Across swift-syntax's 21 modules, candor-swift's 2 and 14 fixtures, exactly
      one report emits `count: 0` — swift-syntax's `SwiftSyntax-all`, whose only source file is a comment
      reading *"This is a fake target that depends on all targets in the package."* **A rare facade, not
      half a dep tree** — precisely the shape the rule is for.
      **PART 26 CONTROL SEPARATION**: java **56/80**, swift **24/80**, rust + ts **INDISTINGUISHABLE**.
      - [x] **rust `faf4430` — and it hit TRAP 1 exactly as warned, in a shape java's warning did not
            cover.** rust has **FOUR** coverage anchors (envelope `package`, `packages[]`, **filename
            fallback**, entry `hash` prefix), and *"a count-0 report reaches the entry loop with no entries,
            so the `hash` anchor never fires for it"* — the envelope and **filename** anchors are the two
            that carry this shape. A structural test now enumerates 4 writes / 3 consumers out of the
            source, so the anchor set cannot grow silently.
            **rust's ratio is ~1:1, not java's 79:104 — an honest narrowing of my own framing.** 17/173
            candor-rust (9.8%), 27/409 ebman, 20/270 pgman emit `count: 0` — all macro-only, platform link
            stubs, data blobs or re-export facades (`cfg_if`, `windows_*_msvc`, `icu_*_data`, `pin_utils`,
            `static_assertions`) — against 16/49/39 legitimately all-pure. The emptiness-keyed fix is still
            the wrong trade, **by a narrower margin than the JVM number suggests.** Live effect on
            candor-rust's own scan: reports IDENTICAL, one new stderr advisory naming all 17.
            **Its `gate --report` REFUSES (exit 2) with NO verdict**, and the reasoning is careful: §3.3
            exit-2 cause (a). It declined to borrow cause (b)'s `incomplete: true` verdict shape because
            that is keyed to `unanalyzed`, **a NAMED list** — a count-0 report names nothing, so borrowing
            it would put an unsupported claim on the wire.
      - [x] **ts `4637a16` — CLOSED FOUR-WAY. 56 ABSENT cells → 0.** Placement was the default (third
            conjunct on the COVERED set in `scan.mjs`'s dep loader). Its mutation table reproduces the
            signature both prior engines reported: **m2, keying on `functions.length`, leaves the FLOOR row
            GREEN** while failing the CONTROL rows **plus four pre-existing coverage tests** including
            *"an all-pure dep's EMPTY report covers its package"* — the deleted-feature signature.
            **ts's BLAST RADIUS is 0 in 91, for a STRUCTURAL reason worth knowing**: candor-ts mints a
            `<module>` unit per file, so `count ≥ 1` for any scannable tree, **and it refuses to write a
            report at all** (exit 2, "no TypeScript sources") for a directory with none. **So in this engine
            a count-0 report is never SELF-produced — it can only arrive from another engine**, which makes
            the un-version-checked routes the ones that matter.
            And that is where the ts-specific warning paid: a foreign-version count-0 report chained via
            `CANDOR_DEPS` **already takes the §2.1 stale path** (staleness is checked first, deliberately —
            it carries the more specific remedy). **The routes that actually receive a foreign count-0
            report are `gate --report`, MCP `candor_gate` and the LSP live gate**, and all three are now
            covered — the LSP one because *"an empty editor over a count-0 report otherwise reads as
            green."* Exit codes and the verdict document are deliberately unmoved on the gate route: §3.1
            byte-equality, and asserting an effect would be fabrication.
      - [x] **ALL FOUR SEPARATED** — rust 64/80, java 56/80, ts 64/80, swift 24/80. **rust's and ts's
            `empty_zero` waivers DELETED, not narrowed**: the ratchet itself reported
            `FAIL (STALE WAIVER): baselined as known-broken but every cell now passes`, zero residual cells.
      - [x] **A 15TH BUMP SITE, found by this agent as a "pre-existing" failure — it was mine.**
            `tests/integration.sh:368` asserted the deep backend's verdict declares spec **0.23**. The
            backend derives from `SPEC_VERSION` and emits 0.24 correctly; only the assertion was stale.
            **The preflight could not have caught it**: check [2]'s pattern DOES match `spec: 0.23`, but the
            line lives under `tests/`, which my loud/advisory split classifies as advisory on the reasoning
            that an older spec string there is a deliberate fixture. **That is right for fixtures and wrong
            for OUTPUT ASSERTIONS, which also live in test files** — and every one of the nine I found
            during the bump was exactly that shape, found by running suites rather than reading the gate.
            **The split makes the preflight readable; it cannot replace running the tests.** Not widened,
            because widening puts 220 fixture lines back.
      - [ ] **swift's 40 residual cells are NOT this door** — a **separate pre-existing per-function
            `invisible` attribution gap** (field, implicit_conv, lazy_init, loop_elem, method_recv): every
            one reads `unchained=(ABSENT)`, so the unchained baseline is equally silent, and PART 26 credits
            only shapes where swift also attributes a per-fn `invisible`. **java shares two of them.** Worth
            its own pass.
      - [x] **java LANDED `110bec5`, and it produced THE number of the whole exercise.** Same placement
            shape as swift, reached independently: a **third conjunct on the COVERED set**, beside §2.1
            `stale` and ⟨0.21⟩ `incomplete`. **Keyed on the INTEGER, never on the emptiness of
            `functions`** — and here is why, over **1997 deduplicated JVM dependency jars**:
            | | count |
            |---|---|
            | emit `analyzed.count: 0` | 79 (4.0%) — of which only **6** actually granted coverage |
            | are the LEGITIMATE all-pure kind | **104 (5.2%)** |
            **A fix keyed on emptiness would have withdrawn 104 REAL CLAIMS to catch 6.** The
            plausible-but-wrong fix is *more destructive than the defect*. Cross-checked on a rust chained
            tree (69 reports): 5 count-0, all genuine facade/platform stubs.
            **Two structural traps recorded for the copiers**: coverage is anchored **TWICE** (envelope
            `packages` AND each entry's `hash` prefix) so *"gating one is a no-op wearing a fix's clothes"*;
            and the CHAINED set must stay **ungated** since it only adds disclosure.
            Its mutation table mirrors swift's: hedging on emptiness fails the control, the divergence row
            and the shape table **while the count-0 row stays GREEN** — *"what a plausible-but-wrong fix
            looks like"*.
            **BOTH ENGINES CORRECTED MY BRIEF THE SAME WAY**: `deny Fs` does NOT return to exit 1 and
            should not — *"restoring the verdict would mean asserting an effect the consumer has no
            evidence for."* Spec text fixed (`400e8e1`).
      - [x] **Both waivers NARROWED, not retired** — java 72→16 cells, swift 64→40. The residuals are a
            **separate pre-existing gap**: every one reads `unchained=(ABSENT)`, so the reference arm is
            itself silent and the property has nothing to compare against. java's two shapes are a subset
            of swift's five.
      - [ ] **NEW, from java: `⟨0.24⟩` row 3 RETIRES a pre-⟨0.21⟩ affordance** — a manifest-less empty
            report used to buy coverage, and java had a test pinning exactly that. Now recorded in §2 as
            deliberate, with the guidance to re-point such a pin at a manifest-bearing fixture rather than
            delete it.
      - [ ] **NEW, from java: the same rule must bind `gate --report`** — a `count: 0` report handed
            DIRECTLY to the verb still prints "no violations", exit 0. Specced (`4ef7166`); unimplemented
            in java and swift, and rust/ts are building the verb now.
      - [ ] **Minor, live shell bug java found and fixed**: a smoke row's label had unescaped backticks
            inside a double-quoted string, so it had been **running `package` as a command** and printing
            the substituted result.
      ORIGINAL — Both `empty_zero` waivers are now STALE and OVERSTATE (swift's still says "64/72 ABSENT …
            INDISTINGUISHABLE"; the live numbers are 40 cells / 24-80 separated). The ratchet does not fail
            on improvement, so nothing is red — which is exactly why they will rot. **Mine to retire, once
            java's in-flight work lands** (swift measured java against an uncommitted tree).
      ORIGINAL — FOUR-WAY, NEW: AN EMPTY CHAINED REPORT BUYS MORE CONFIDENCE THAN NO REPORT AT ALL.** A report with
      `functions: []` and `analyzed.count: 0` — *"I judged nothing"* — is read as **full coverage**. The
      caller drops out of `functions`, which under ⟨0.21⟩ is a **positive purity claim**, with **no
      advisory anywhere**. `deny Fs` **exit 1 → exit 0**. rust 64 / java 72 / ts 56 / swift 64 live cells
      ABSENT. Strictly MORE confident than the unchained arm, which correctly discloses `invisible` +
      `coverage.uncovered`.
      **THE FIX PATH IS PROVEN, NOT ARGUED — and that is the valuable half.** The wire ALREADY expresses the
      difference: candor-scan emits `count: 0` for a `pub use`-only facade crate and `count: 2` for an
      all-pure two-function crate. **No engine reads it.** Demonstrated by a negative-control arm differing
      by that single integer — a legitimate all-pure claim §2 rule 3 says a consumer SHOULD believe, so it
      must never fail — and `CONTROL SEPARATION` prints INDISTINGUISHABLE for all four today. **A fix must
      make those two arms diverge.**
      Provenance worth keeping: rust noticed `futures@0.3.32`'s empty report while measuring something
      else → relayed as a candidate P3 arm → P3 turned it into a four-way finding with a remedy.
      - [ ] **Producer-side caveat, unmeasured:** `analyzed.count` was verified correct (0 for a facade,
            N for all-pure) **on candor-rust only**. Whether java/ts/swift EMIT 0 correctly for their own
            facade packages is a separate question.
- [→] **rust's chain-idempotence and the BESIDE-erasure are both the ENTRY-COLLISION union decision**
      (§2, decided `b47c9ab`, unimplemented). They now have a conformance gate waiting for them — PARTs 25
      and 26 will go green on the engines the moment the union lands, and fail if it regresses.
- [x] **The harness caught a defect in ITSELF, the same shape P1's did.** P2's first draft reused a
      `GAINED` verdict and printed *"the duplicate arm invented an effect … once=(ABSENT) twice=(ABSENT)"* —
      a mis-invocation dressed as a finding about candor. It now has its own `BROKEN` verdict. **Two
      property harnesses, two instances, both found by deliberately firing every guard.**

### 3b — THE GATE-A-REPORT VERB · **BUILT in java as reference**; rust/ts/swift to copy the shape
**candor-java SHIPPED it, and it produced more normative content than the clause I wrote — three
requirements found by MEASUREMENT, not design** (SPEC §3.1 ⟨0.24⟩ `a96da88`).
`candor gate --report <locator> --policy <file> [--json] [--gate-json <file>]` — a QUERY verb, inheriting
§3.3.1's grammar unchanged, no positionals, exit codes exactly `scan --policy`'s. **`--json` ≡
`--gate-json -`**, which CONTRADICTS my brief ("support `--json` exactly as the scanning path does") and the
agent was right: on a scan `--json <file>` writes the REPORT, and there is no report here — a second
meaning would be the one place a consumer could tell the routes apart.
- **The MUST NOT is PROVEN, not asserted**: the absent entry sat beside THREE baits — a callgraph sidecar
  edging it to a `Net` unit, a chained dep report giving it `Net`, and a `.candor/config` `deps` key in the
  one directory the verb does open a config from. Verdict clean; positive control exit 1; **verified by
  mutation** (back-filling makes both halves fail). All 21 tests mutation-checked.
- **EQUIVALENCE IS BYTE-LEVEL**: 25 rows, two corpora, every `--gate-json` document byte-equal between
  routes — `analyzed.count`, `reasonClass`, `netClass`, coverage advisory included.
- **ANSWERABILITY — three refusals, each FAIL-OPEN if approximated.** `forbid` (a `calls` field that is
  effect-relevant-only cannot see a crossing into a pure unit) and `allow` (the AS-EFF-008 marker does not
  ride the wire) — **the engine's first cut RECONSTRUCTED `allow` for `Net` from `netClass ∋ unknown-host`
  and the equivalence test refuted it in one run**, because that token also names a merely *unrecognised*
  host. Plus a LIVE fail-open found by the correspondence review and measured here:
  `deny Net[unknown-host]` over a `Net` entry with no `netClass` → **exit 0** where bare `deny Net` → 1.
  Refusal granularity differs by cause: whole-policy for `forbid`/`allow` (enforcing the answerable half is
  gateless-green), per-(rule, function) for the scoped case.
- **THE MANIFEST DOES NOT TRAVEL — worse than PAPER3 Def 24 says.** `count − |functions|` is just the pure
  count (970 − 390 = 580), so a dropped unit is **arithmetically identical to a pure one**; the `digest` is
  over the analyzed QUAL SET of which a consumer holds only the effectful subset, so it **cannot be
  recomputed across a boundary at all**; and `count < |functions|` is legitimately reachable because
  ⟨0.23⟩ `interfaceUnion` entries are appended. Closing it needs the per-unit analyzed NAME SET — which
  exists, as the §2.2 callgraph node set, but lives in a **sidecar this verb refuses by construction**.
- **100 model disagreements over 1792 rows, ALL one family** — `Db` under `deny Net`. The engine reached
  **the same ruling I had recorded independently**: model-vs-contract, not an engine defect, pinned both
  ways rather than patched. `pure` went from 15 disagreements to **0/256** once the model was corrected.
- [x] **DONE FOUR-WAY — rust `93ed0a1`, ts `c2b8ce4`, and PART 27's R6 is OK on ALL TWELVE CELLS.**
      The harness needed three fixes of MINE before it could say so: `GATE_ENGINES` hard-coded to
      java+swift, no rust/ts branch in `q_gate`, and — the real bug — **the equivalence cell dispatched
      everything non-java to `_swift_scan`**, so rust's and ts's gate was compared against SWIFT's scan.
      Both agents reported *"no change in my repo can flip this row"* and verified against scratch patches
      rather than editing a harness they were told not to touch.
      **AND BUILDING IT IMMEDIATELY JUSTIFIED THE VERB — a defect IN RUST'S OWN GATE that no end-to-end
      test could have isolated.** A `#[cfg(unix)]` fn beside its `#[cfg(not(unix))]` twin put one qualified
      name in the gate's function list **TWICE**, so the gate emitted two byte-identical violation records
      and an inflated count — **15 of the first 90 rows.** The report route cannot reproduce it (a report is
      keyed by NAME), and that asymmetry is what surfaced it. Exactly what the clause promised: a defect in
      the GATE and one in the CLASSIFIER were previously indistinguishable. Equivalence after: **90/90
      byte-equal**, 30 policies × 3 corpora. Model cross-check **2,949,120 rows, 0 disagreements**, negative
      control firing on the known unreachable family.
      **ts found a second real defect, on the FOREIGN-report routes**: `netClass` was being **RE-DERIVED
      from `hosts`** on MCP/LSP, because the producer's `net-partner` list and masked-surface flag are not
      on the wire. Both directions wrong — a `known-partner` host re-read as `unknown-host` (**fabricated**
      `deny Net[unknown-host]` hit) and a masked surface re-read from its one benign literal (**fail-open
      mirror**). Now read verbatim. ts also confirmed **the minimal-refusal rule was implementable as
      stated**: it exits 1 on PART 27's R1 fixture where swift exits 2, because it already CONTRIBUTES
      `unresolved` at the entry.
      **`allow`'s justification was FALSIFIED by rust and is corrected** (`98ac23b`): the clause said the
      completeness marker "does not ride the wire" — rust emits a per-entry `incomplete` field §2 names, so
      it COULD answer. It refuses anyway, and its reason is better than mine: **an engine that answers a
      question its three siblings refuse has SPLIT THE VERB.**
- [ ] **rust DEFECT against an EXISTING MUST — I filed this as "needs a four-way ruling" and it is not one.**
      §3.3.1 already says it, verbatim: *"A configured gate over incompletely-analyzed code MUST fail closed
      (exit ≠ 0); **a real violation (exit 1) still dominates.**"* java and swift are right; **rust is
      wrong** — `had_parse_failure` returns 2 *before* recording violations, so a real violation found
      alongside an unparseable file is reported as "I could not analyse" instead of "your code violates".
      **THE MACHINE-CONSUMER CONSEQUENCE IS THE SHARP PART, and it is worse than an exit code.** §3.3.1
      pairs the code with the document: on **exit 2** an engine writes *only* the ⟨0.21⟩ incomplete verdict
      `{ok:false, incomplete:true, unanalyzed:[…]}` — **never the violations.** So on an input carrying both,
      rust's `--gate-json` **DROPS a real finding** and tells a CI consumer the analysis was incomplete. The
      violation is not merely mis-coded, it is *absent from the artifact*. That is a machine-consumer
      under-report, which is the class this whole document is about.
      Now pinned on BOTH routes: `gate --report` mirrors rust's own scan for byte-equality, so fixing the
      scan fixes both, and fixing only the verb would break the equivalence PART 27 asserts.
      **Lesson for me, not for rust**: I read a cross-engine disagreement as an open question without
      checking whether the contract already settled it. Two engines agreeing with the spec and one
      disagreeing is not a tie.
- [x] **CLOSED 2026-07-28 (rust `89f2c0f`). NEW, from rust: `ci/self-gate.sh` DELETES TRACKED FILES.** Its `rm -rf "$d/.candor"` removed the
      checked-in `report.*.scan.json` artifacts in all four crates. The agent restored them byte-for-byte
      via `git show HEAD:<path> >` rather than `git checkout` (the standing rule). Harmless in CI,
      destructive locally — and it is a script a contributor is told to run.
      ORIGINAL — rust + ts: copy the shape. NOW THE LARGEST SINGLE CORRECTNESS GAP IN THE RUNG: §3.1 calls it a MUST, PART 27 prints NOSURF for rust/ts, NOSURF
      does not fail the run, and the 0.24 changelog entry had to be **corrected to "pinned 2-of-4"** rather
      than four-way. Swift's finding sizes the job: the report READER had to be written, because *"a
      `gate --report` reader must read strictly LESS than the enrichment loader, which is not a subset you
      can reach by passing a flag."* Then extend PART 23 from "the model is monotone" to "each ENGINE
      agrees with the model" — but NOT naively: Defs 33/34/35 still describe verbs that do not exist, so
      those rows would manufacture divergences out of the theory (§2b).

ORIGINAL FILING — the gate-a-report verb, parallel per engine, unblocks P4
**SPECCED ⟨0.24⟩ `3dd2e39` as `gate --report <locator> --policy <file>`; java DISPATCHED as reference.**
Shape: exit codes and verdict identical to `scan --policy`, only the source of `S`/`D` differs. The
load-bearing half is a **MUST NOT** — no re-deriving, widening or re-classifying; an ABSENT entry stays
absent and is not back-filled from a sidecar or a chained dep. The verb's whole value is being a pure
function of (report, policy), and this codebase's loader is built to ENRICH reports, so the brief requires
proving the path does not.
**Today's evidence supports this entry's own hypothesis**: the ⟨0.24⟩ §6.2 defect was a contract-vs-model
divergence every engine implemented faithfully, and no end-to-end test could have localised it.
- [x] **CLOSED 2026-07-27 — `gate --report` now ships FOUR-WAY.** (Kept for the diagnosis, which was
      right and is the reason the rung exists at all.) **No engine exposes a way to gate a GIVEN
      signature.** The gate is reachable only via
      `scan --policy` (which computes `S` from source, putting the classifier back in the loop) and
      `whatif` (which reports only violations the hypothetical INTRODUCES — verified: a report with
      `inferred: ["Net"]` under `deny Net` returns `ok: true`). **This is plausibly WHY the model and the
      engines drifted**: the gate is only ever exercised end-to-end, so no test could isolate it.
      Closing it makes conformance PART 23 extend from "the model is monotone" to "each ENGINE agrees with
      the model", which is the code-implements-spec direction and is currently unverifiable.
      Was recorded ONLY in `reference/README.md` until now — the recorded-in-a-narrative failure, again.

### 4 — IMPLEMENT (1) FOUR-WAY · UNBLOCKED (§1 settled); fully parallel, one agent per repo

§1 produced THREE separable implementation items, not one. They have different blast radii and the first is
the only verdict-changing one — do not bundle them.

- [x] **4a DONE FOUR-WAY — and java was the ONLY engine where it was reachable.** swift 0 fires / 487 fns,
      ts **0 / 1872** (and *unwritable* — a self-check refuses to emit such a report at all), rust 0 fires.
      java was reachable via the **dependency boundary**, the one route the other three had already closed;
      36% verdict flips on stale deps, 0 on trusted.
      **rust's measurement found the MIRROR instead, live on TRUSTED reports**: its source-side contribution
      was gated only on the dep entry's own direct tag, and §4 makes `unknownWhy` direct-only — so an
      *inherited* dep `Unknown` looked identical to an unaccounted one. **26 functions on candor-scan's own
      tree fired `deny Unknown[unresolved]` wrongly**, all tracing to 8 callers of three `syn` entries whose
      `Unknown` syn's own `calls` chain explains 2–5 hops down. Fixed by resolving across the dep's
      published edges: 26 → **0**, and `[dispatch]` **19 → 28** (the discrimination control — merely
      dropping the contribution leaves it at 19).
      ORIGINAL — 4a. §6.2 CONTRIBUTES — the only one that can turn a GREEN GATE RED.** A reasonless `Unknown` ADDS
      `unresolved` to the class set instead of defaulting when the set is empty. Matches a strict superset,
      so `deny E Unknown[<class>]` can go exit 0 → exit 1 on unchanged code, and re-baselining does not fix
      it. **Each engine must reproduce the three-row counterexample BEFORE changing anything** (reasonless
      dep → rejected; reasoned dep → passes; **BOTH → passes**, the strictly-worse-known case passing where
      the weaker one is rejected). And each must carry the control that separates this from "contribute
      `unresolved` unconditionally": a function whose reasons are ALL classifiable and none `unresolved`
      must still NOT match `deny E Unknown[unresolved]`. Without it the fix is indistinguishable from one
      that floods every narrowed gate and makes `[class]` useless.
      **Blast radius must be MEASURED per engine on real code and reported as a number.**
      - [x] **swift: NO-OP, measured — and the measurement found the RIGHT IMPLEMENTATION SHAPE.** The
            counterexample does not reproduce. Swift attaches a reason **at the point the Unknown is
            created**, not at the join: `dep:<hash>` synthesized per dependency ENTRY exactly when that dep
            classified nothing, plus `dep-stale:<pkg>` for a distrusted producer. Per-ENTRY, so a caller of
            both a reasonless and a reasoned dep accumulates `{unresolved, dispatch}` with no join-time
            special case. Its empty-set default is **UNREACHABLE — 0 fires across 487 Unknown-bearing
            functions** over two real targets, corroborated by an offline fixpoint recomputation. My
            specified join-side change would have been a no-op that looked like a fix.
            **Now normative** (SPEC §6.2 `f6337fa`): attach at the source. Same conclusion the formal model
            reaches from the other end — a reasonless `Unknown` is not representable in `(S,D)` at all, so
            the state must be made unreachable, not handled. **Swift got there independently, before the
            model was written.**
            Calibration number for the other engines: the naive form (contribute whenever `Unknown` is
            present) marks **435** on the corpus where the legitimate count is **0**.
      - [x] **java FIXED `82bf4d4` — REPRODUCED, unlike swift, and the difference is instructive.** Java
            records an `unknownWhy` beside every `Unknown` it raises itself (**all 13 `dir.add(UNKNOWN)`
            sites checked**), so the only route to a reasonless one is the **dependency boundary** — a §2.1
            distrusted report whose effects were downgraded wholesale, or an entry neither its own tags nor
            its published `calls` chain accounts for. That is the route swift had already closed with
            `dep-stale:` and java had not. Fixed **at the source, per dependency ENTRY** (swift's shape):
            `dep:<hash>` / `dep-stale:<pkg>` recorded at load, both projecting to `unresolved`, and it
            **rides in the report** so the class travels to whoever chains it. Join-side default kept only
            as a fail-closed backstop, commented as one.
            | dep reports | class sets changed | `[unresolved]` flips |
            |---|---|---|
            | **trusted** | 0/141, 0/211 | **0** |
            | **stale** | 130/145, 311/311 | **52**, **2** |
            **36% of one target — a large break, and it is entirely conditional on reports the build cannot
            verify.** Trusted reports: nothing moves.
            **THE CONTROL FAILURE IS THE DURABLE PART, and the agent caught it in its own work.** Its first
            fixture *could not distinguish the fix from the flood* — under a stale report NOTHING is
            accounted for, so the naive form passed every assertion. The real control is a **FRESH** dep
            whose `Unknown` IS explained (once via its own tag, once via a `calls` edge). Measured: the
            naive form flips **96/141 and 211/211** with fresh reports where the correct rule flips **0**.
            Java's analogue of swift's 435-vs-0. **A fixture that cannot show that gap is not a control.**
      - [x] **ts: NO-OP, and its guarantee is the STRONGEST of the four (`d64c032`, test-only).**
            Reachability **0 over 1872** `Unknown`-bearing functions, five arms including trusted AND stale
            chained deps. **candor-ts is at the source TWICE**: the emitter writes
            `unknownWhy: ["unresolved"]` on any unnamed direct `Unknown`, AND a trust-marker self-check
            **REFUSES TO WRITE THE REPORT AT ALL** (exit 2) if one escaped. *"The state is not merely
            unwritten, it is unwritable."* Established by MUTATION — deleting the fallback turns the
            stale-dep arm into exit 2 with no report. Now the stated ideal in SPEC §6.2 (`7aa0ebc`): a
            join-side default COPES, a source-side contribution makes it UNREACHED, a producer-side
            self-check makes it UNWRITABLE.
            **So 4a is: java the ONLY engine where it was reachable** — via the dependency boundary, the one
            route swift and ts had already closed. Three of four were already right at the source.
      - [→] rust pending.
- [x] **CLOSED FOUR-WAY.** swift `2c96569`, rust `5df4af1`, ts `cbbb05c` (+ `72a9b51` for the over-fire the
      review found), java `03b833b`. Worst was ts at **got 64→21 (−67%)**. All four now share one fixpoint
      and one match rule with their own gate. Plus the ⟨0.24⟩ **value grammar** four-way (rust `7d916f4`,
      swift `0646085`, java `735204c`, ts `53e4585`) — a shared gap no engine had implemented.
      ORIGINAL — `unverified --class` FAILS OPEN under absence (swift `Fix.swift:242`), found while measuring
      4a.** The tool whose entire job is to name the holes a green gate does not prove — and its filter
      **under-reports the more the user narrows**. Two causes, both needed:
      (1) an entry with empty `unknownWhy` matches NO filter, including `unresolved` — the exact fail-open
      ⟨0.24⟩ closes; (2) it reads the report's **direct-only** `unknownWhy` with no transitive resolution,
      where the gate does resolve via `reasonClassAcc`. §4 makes `unknownWhy` direct-only BY DESIGN, so this
      is misreading the format rather than hitting a format gap.
      **Measured on pollen, `deny Exec`: 387 holes unfiltered vs 230 under `--class dynamic`** — and
      `dynamic` names every genuine class, so **157 (41%) vanish under a filter that should be a no-op**.
      Cause is (2): 192 of 435 pollen entries (44%) and 35 of 52 of candor-swift's own (67%) carry no direct
      `unknownWhy` because their Unknown is purely inherited.
      **Both halves must land together**: fixing only (1) contributes `unresolved` to an inherited-Unknown
      entry whose Unknown is perfectly well classified at the callee — trading a fail-open for a
      fabrication, which the standing bar forbids.
      - [x] **swift FIXED `2c96569` — converged EXACTLY, on all 8 target × policy rows.**
        | target | unfiltered | `--class dynamic` BEFORE | AFTER |
        |---|---|---|---|
        | pollen | 387 | 230 (−41%) | **387** |
        | candor-swift | 51 | 16 (−69%) | **51** |
        candor-swift's own arm was WORSE than the corpus target — 69% of its holes vanished under a filter
        that excludes nothing. Half 1 gated on `direct ∋ Unknown` with no `unknownWhy` (the function
        introduced the hole and named nothing), **not** on absence-of-reason, which is the mirror
        fabrication. Half 2 reuses the gate's own least-fixpoint. A third rule handles neither case: an
        `Unknown` nothing in its reach explains (truncated report, callee in an unloaded report) gets
        `unresolved` — §6.2's conservative projection.
        Controls held at corpus scale, which is the part that proves it is not a blanket: `--class
        unresolved` = **6 of 387**, `--class native` = **0**. And `--class unresolved` went 1 → 6, not
        1 → 387. `direct`/`calls` are now non-defaulted on the entry type so a construction site cannot
        silently rebuild the direct-only reading. **No format rung needed** — both fields were already on
        every entry, just unread.
      - [x] **rust FIXED `5df4af1` — reproduced in `unverified`, and WORSE than swift.** All 8 target ×
        policy rows converge exactly after; unfiltered → `--class dynamic` before: **54→26 (−52%)**,
        **7→1 (−86%)**, **94→23 (−76%)**, **43→21 (−51%)**. Fault 1 (direct-only read) was the bulk —
        101/124 ebman `Unknown` entries, 37/60 pgman, 6/7 candor-scan holes carry no direct reason.
      - [x] **`blindspots` CLEAN — my two-verb brief was WRONG and the correction reached the agent in
        time.** Measure-only, 5 targets: 0→0, 1→1, 23→23, 23→23, 26→26. And `sources` provably cannot hold
        a reasonless entry in rust — the code skips `unknown_why.is_empty()` before the filter runs, AND
        **zero of 17,306 entries across 173 dep reports** carry a direct `Unknown` with no reason. Applying
        swift's fix here would have been a regression: it would pull in exactly the inherited units the
        verb is DEFINED to exclude. *One verb's definition is the other verb's bug.*
      - **THE ROOT CAUSE, and it is the durable part** (now SPEC §6.2 `15041de`): **rust's GATE was never
        party to this defect.** It already resolved transitively and already treated an absent class set as
        `unresolved`. The divergence was purely consumer-side, in the one query that reads a **report**
        rather than the scan's in-memory graph — carrying an **open-coded second copy** of the
        classification. *Two implementations of one rule inside one engine, one correct, drifting silently
        because nothing compared them.* Fix was structural: `propagate_str` + `reason_class_matches` hoisted
        into `candor-classify`, so gate and disclosure share one fixpoint and one match rule.
      - **An honest zero, flagged by the agent so nobody misreads it:** rust's post-fix `--class unresolved`
        selects **0**, not swift's 6-of-387 — because no rust report contains a reasonless direct `Unknown`
        at all (17,306 entries, zero). Fault 1's contribution is a genuine fail-closed net whose only
        demonstrated firing is the fixture. **A 0 that means "the net never had to catch anything", not
        "the fix did not land".**
      - [x] **ts FIXED `cbbb05c` — the WORST of the family.** Six rows, three real targets × two policies,
        all converging exactly: candor-ts's own **207→173 (−16%)**, execa **268→158 (−41%)**, got
        **64→21 (−67%)**. Underlying gap: **24%** of `Unknown`-bearing entries on ts's own sources and
        **57–58%** on execa/got carry no direct reason.
        Structural repair as specified — the gate already resolved transitively, the second copy was
        consumer-side; `resolveReasonClasses`/`reasonClassesMatch` now live in `policy.mjs` and BOTH call
        them, with `dynamic` resolved from the same exported vocabulary the policy parser uses. **One
        fixpoint, one match rule, one vocabulary.**
        **`blindspots` measured and LEFT ALONE** — 237/190/55 sources, `--class dynamic` already excluded
        nothing on all three. **Third independent confirmation that my two-verb brief was wrong** and the
        correction was right.
        **The agent caught its own mirror fabrication**, third to do so today: its first attempt treated an
        absent `direct` key as direct and over-fired on an inherited-but-classified caller — *"exactly the
        mirror fabrication req 3 warns about; measuring caught it."*
      - [→] java pending.
- [ ] **Residual, deliberately left (swift, and check it four-way when the sweep lands):** `UnverifiedHole`
      still prints the report's DIRECT `unknownWhy`, so a hole surfaced by `--class dispatch` *through
      inheritance* is listed with an empty `unknownWhy` — the filter matched on a class the output does not
      show. Not a defect against §4 (direct-only is by design) and not a dead end (`upgrade` carries the
      remedy, `path` traces the origin), but incoherent to read. Putting the RESOLVED class set on the wire
      is a **format rung**, and it was left alone deliberately given the standing result that none of this
      vein's fixes has needed one.
- [x] **4b JAVA DONE (`91930f2`) — and the audit produced the SHAPE, which is worth more than the fix.**
      **Every engine holds the kind vocabulary TWICE**: a prefix/STRING classifier feeding §6.2's class
      table, and a TYPED/structural one (enum/union/match). They are authored from different sources — the
      class table from a cross-engine audit of what engines EMIT, the typed vocabulary from §4's list — so
      when §4 goes stale **the string half stays right and the typed half does not.** *"The bug lives in the
      disagreement between the two, and the string half being right is exactly what hides it."*
      In java: `ReasonClass.classify(String)` mapped `ambiguous`→`DISPATCH` **since a 2026-07-16 audit**,
      while `UnknownReason.Kind` lacked the kind entirely — so the token was a FOREIGN prefix, `kind()` was
      null, and the typed path classified it `unresolved` where §6.2 says `dispatch`. **One token, two
      answers, one engine, silent.** Two code comments had recorded the divergence as *intended* rather than
      fixing it — the comment-as-assertion class, again.
      **java emits NO `ambiguous:`** (a JVM invoke carries owner+name+descriptor, so bytecode resolution is
      never ambiguous) **but it RELAYS them**: `depTransitiveWhy` parses a chained dep's tags into java's own
      report, so a rust `ambiguous:` appears in java's output. **A consumer needs kinds it never emits** —
      now stated in §4 (`57eaf6f`).
      **The frontier point is a checkable prediction**: java's frontier keys off the TYPED `DISPATCH`, so it
      excludes `ambiguous:` for free; an engine keying off the CLASS would admit entries with no owner to
      resolve against. Sent to rust with 8710 entries at stake.
      Control: `banana:whatever` unchanged, asserted at model level AND end-to-end. **Four mutations, each
      caught** — including catch-all→`DISPATCH` (the blanket), which failed BOTH controls. No verdict change.
      - [x] **rust: ONE representation, structurally immune** (`0a3e6c9`). Raw `kind:detail` strings out,
            one prefix table in, already right since ⟨0.19⟩. **Both predictions answered NO**: it is not
            emitting a kind it cannot parse back (no typed vocabulary to lack it), and its frontier is
            **KIND-keyed** (`strip_prefix("dispatch:")`) so `ambiguous:` is excluded for free — **0 wrongly
            admitted**, now pinned by a fixture running the kind-keyed frontier and the class-keyed
            `blindspots --class dispatch` over ONE report: the class selector returns the entry, the
            frontier does not.
      - [x] **swift: ONE representation too — NO production change, zero source diff** (`0855fff`). Its
            `reasonClass` `dispatch` arm has read `ambiguous` since `8b0a660` (the ⟨0.19⟩ port), traced not
            assumed. No `Kind` enum, union, validator or accepted-prefix set anywhere; every consumer routes
            through `reasonClass`. **Emits none but RELAYS them** — `Deps.swift:387` copies a dep's tokens
            verbatim, so a chained rust `ambiguous:` lands in swift's own report and is gated on there.
            No class-where-kind instance (it ships no `callers`/`blindspots`, and nothing parses a
            `dispatch:` detail into `owner.member`).
            **ITS MUTATION TABLE UPGRADED A SPEC SHOULD TO A MUST** (`fc501bb`): rewriting the prefix test
            from *is the kind in the SET* to *does the token have the `kind:detail` SHAPE* passes EVERY
            assertion about EVERY real kind — they all have the shape — and is caught **solely by the
            fabricated kind**. Load-bearing in 3 of 4 mutations, sole detector in one. *A control only
            exercised by inputs the implementation already handles is not a control.*
      - [x] **ts: ONE representation, rust-shaped, NO production change** (`cb53c9d`). Enumerated every
            construction site and every read — no enum, union, kind `Set`, kind-keyed `switch` or validator
            anywhere. Frontier is **KIND-keyed** (`startsWith("dispatch:")`); mutating it to be class-keyed
            admits `m.Ambig.go` with `viaDispatchOn: "two same-named local definitions"` in BOTH arms — an
            entry with nothing to resolve overrides against.
            **AGENTS.md WAS a second copy after all — of the VOCABULARY, not the class table** — and it had
            drifted: it named `call:jwt.sign` as a live `unknownWhy` origin, a kind ts has not emitted since
            the `callback:param#i` form landed. **A phantom kind in the doc an agent reads.** Rewritten to
            the closed five, and the doc drift gate — which pinned only spec-generation strings — was
            **extended to the kind vocabulary**, both halves verified red.
            **Caveat worth knowing for cross-engine work:** ts's chain trusts a dep report only when
            `d.candor.version === "candor-ts-<pkgver>"`, so a literally-foreign candor-rust report takes the
            **stale** path and downgrades to bare `Unknown` — sound, not fabrication, but it means **the
            chain is NOT the route a rust `ambiguous:` takes into ts.** The route that matters is the QUERY
            VERBS, which read any report `--report` is pointed at. Both now covered.
      **4b IS COMPLETE FOUR-WAY. java was the ONLY engine with the defect** — the only one holding the
      vocabulary twice. Same pattern as 4a, where java was also the only engine where the defect was
      reachable. Three of four were already right, twice over, and the sweep's value was establishing that
      rather than changing it.
      - [ ] **NEW, opened by swift: two OFF-VOCABULARY kinds in the field.** `dynamicMemberLookup:` is mild
            (absent from §4, registered in §6.2's table — the same asymmetry `ambiguous:` sat in).
            **`contentsOf:indeterminate-url-scheme` is registered NOWHERE** and **answers a different
            question from the five**: all five mean *"the body could not be resolved"*, this means *"the
            call resolved; its effect CATEGORY is unprovable"*. Recorded in §4, not reconciled — either fix
            changes report bytes.
      - [x] **conformance PART 10 FIXED (`2efe0bf`) — it CONTRADICTED the spec and would have hard-DIVERGEd
            any engine implementing ⟨0.24⟩ in the field, two ways.** `CANON` still held four kinds with
            `ambiguous` in a warn bucket and `dep:`/`dep-stale:` in none. Worse, the dispatch-detail check
            DIVERGEd on **any dot-free detail** — the exact form ⟨0.24⟩ reserves, and the reference Rust
            engine's **dominant** dispatch reason. Now five canonical kinds + a `REGISTERED` bucket
            (deliberately not `MIGRATION`, whose meaning is "being reconciled away"), the dot shape checked
            only when a dot is present, and **the negative control** without which "pins five kinds" and
            "stopped checking" are the same diff. Verified on nine rows across all five outcomes.
            ORIGINAL — PART 10 must move from *tolerating* `ambiguous` as a
            warning to pinning it canonical: accepted with no warning; detail **best-effort, NOT**
            conformance-compared; `dep:`/`dep-stale:` registered; migration tolerance narrowed to
            `task-handoff:`/`indy:` only; **and the negative control that makes the other four mean
            anything** — a fabricated kind must still warn, else PART 10 cannot distinguish "pins five
            kinds" from "stopped checking".
      ORIGINAL FILING — 4b. `ambiguous:` as a fifth §4 kind. Vocabulary-only; no verdict change (§6.2 already projected
      `ambiguous:*` → `dispatch`, which is why the producer was non-conforming while consumers were fine).
      Mostly a conformance/vocabulary-check update per engine — check each engine's `unknownWhy` kind
      validator, not just its emitter.
- [x] **4c. The §3.1 frontier rung** — dot-free disclosed, empty sidecar ≡ absent, mixed source pinned,
      collation named. **rust `a11adf1`, java (3 commits), swift `5f9e75e` (producer half — no `callers`
      verb), ts in flight.** Three-surface, not four.
- [x] **4d DONE — conformance PART 27 (`dc892a7`), 45 live cells, every row VERIFIED-TO-CATCH in isolated
      worktrees.** `gen_rung024.py` + a both-ways ratchet. Seven rows: CONTRIBUTES, the `viaDispatchOn`
      exact literal, the dot-free frontier (3 shapes × 2 arms), the sidecar triple, `--class`, `gate
      --report`, and locale. **All fixtures are hand-written reports, so the classifier is out of the loop
      entirely** — a divergence is a CONSUMER defect, which is where ⟨0.24⟩ found every one of its defects.
      Rows scoped honestly: R2–R4 three-surface (swift ships no `callers`), R6 two-engine (rust/ts lack the
      verb), both printing **NOSURF with the reason** rather than skipping.
      **TWO REAL DEFECTS FOUND ON HEAD, both waived with hand repros:**
      - **java's `unverified --class` never landed the §6.2 repair** the other three carry: `--class
        unresolved` selects **nothing** where they select three, `--class dynamic` **2 of 7**. Its GATE half
        is clean — §6.2's own diagnosis, an open-coded second copy consumer-side.
      - [x] **rust `7d916f4` + swift `0646085` — grammar landed.** rust covers BOTH verbs that take the
        flag, with the token rule in one place (`parse_class_filter`, now `Result`-returning) so the two
        cannot drift and the repeat rule in `grammar.rs` covering every verb; swift covers `unverified`,
        which is its whole surface. Messages carry the REASONING, not just the refusal — *"a `--class`
        value that cannot be honoured is refused, not dropped: dropping it would narrow the filter and
        answer a question you did not ask, with a smaller number"*.
        **Two things fell out of writing it that the brief did not ask for, and both are right:** `*` is
        now evaluated only after the WHOLE list is walked, so `--class *,dyanmic` still reports the typo
        instead of short-circuiting past it (it did short-circuit before); and a refusal emits **no answer
        document at all** — *"a narrower result one exit code away from a refusal is the same fail-open in
        a different hat."*
        Failability shown per rule: warn-and-continue → only the typo test; last-wins → only the repeat
        test; filter-keeps-everything → both regression controls and **neither** refusal test. The repeat
        test asserts two phrases PRESENT and two ABSENT, which is what stops it passing for the wrong
        reason — the exact trap a swift test fell into earlier today.
      - [x] **java `735204c` (grammar) + `03b833b` (`unverified --class`) — LAST engine, and it changed
        the GATE, which the diagnosis had said it would not.** The structural repair landed as briefed:
        `Policy.reasonClassesOf` + `reasonClassMatches` are now the single definition, called by BOTH the
        gate's `Unknown[c…]` scoping and `unverified --class`. Measured on PART 27's own 7-entry fixture:
        `--class dynamic` **2 → 7**, `unresolved` **0 → 3**, `dispatch` **1 → 3**. `blindspots`
        **byte-identical** before and after on both fixtures — a fourth independent confirmation.
        **BUT: §6.2 requirement (3) CANNOT be satisfied at the join** — *"a set already unioned over callees
        can't say which member was unaccounted-for"* — so the contribution had to land **per-entry**, in the
        shared seam, which moved the gate too. Consequence on a foreign report whose entry has
        `direct: ["Unknown"]` and no `unknownWhy`: `deny Unknown[unresolved]` **2 → 1** (fires) and
        `deny Unknown[native]` **2 → 0** (tolerates), **both now matching what `scan --policy` already did
        over the same signature.** So *"the old refusal had become a scan-vs-report DIVERGENCE rather than a
        protection"* — java reached the over-broad-refusal conclusion independently, and it is the same one
        specced at `05158db` from swift's evidence. Control retained for the genuinely underivable case.
        **Two of its own gate fixtures were the comment-that-lies defect** (fifth today): they read
        `// INHERITED, no calls` while the helper wrote `direct: ["Unknown"]`, so they were asserting the
        CONTRIBUTES case, not the inherited one.
- [ ] **NEW, pre-existing, and a SILENT UNDER-REPORT IN THE SOURCE VIEW — found by java while routing
      AROUND it.** `UnknownReason.parse` returns null for a **colon-free** tag, so `ReportJson.parseEntries`
      **silently drops** `missing-config` from `Effector.unknownWhy()`. Consequence: **`blindspots` never
      lists a setup-only source at all** — 2 sources where there are 3 on the setup fixture, and
      `blindspots --class setup` returns nothing. **The UNFILTERED list is already wrong**, so this is
      independent of `--class` and older than this rung. `unverified --class` is immune only because java
      routed it through the RAW strings via `readEnvelope` — a choice made for a different reason that
      happened to dodge it.
      Note the shape: a parser that models `kind:detail` **drops a token that has no detail**, and the
      §6.2 projection table registers exactly such tokens (`missing-config`, `no-tsconfig` → class `setup`).
      **Check the other three for a colon-required parse.**
      - **AN AGENT DETECTED A COLLISION INSTEAD OF FILING A FINDING, unprompted** — standing bar 7f
        working as intended. PART 27's java cell **passed against an uncommitted jar**: candor-java HEAD is
        still the commit the waiver records as FAILING, but its tree is dirty and the jar was rebuilt at
        23:12 by the live java agent. The agent checked *"precisely because the measurement changed for a
        reason I couldn't explain"*, left java **unwaived** ("the ratchet reports what's on the box"), and
        wrote the caveat into the entry so a revert fails java *unwaived* rather than looking like a
        regression in the baseline file.
      - The baseline narrowing (`engine: "*"` → `engine: "ts"`) is deliberately **uncommitted**, to avoid
        conflicting with two live agents in the same repo; patch saved in the scratchpad. PART 27 currently
        exits 1 on three now-stale JAVA waivers, which are the java agent's to delete with its commit.
      ORIGINAL — FOUR-WAY: nobody implements the `--class` VALUE GRAMMAR.** `--class dyanmic` and a repeated
        `--class` are specified exit 2; all four exit **0**. Not a divergence — a **shared gap**, the
        suite's only `engine: "*"` waiver, and a clause I wrote today that no engine implements.
      **The harness caught two of its own faults, both by measuring rather than reviewing.** A zero-byte jar
      made three cells print *"the frontier came back empty"* and *"unfiltered selected 0/7"* — sentences
      about candor from a CLI that never started; fixed with an empty-stdout ERROR plus a `--help` liveness
      probe. And scanning each locale into its own DIRECTORY reported swift as locale-dependent, because
      swift derives the package name from the containing directory — **the harness's own path was leaking
      into the bytes it was diffing.**
      **R4's equivalence assertion alone did NOT catch** java's `hasHier` deletion, because ts's absent path
      normalises to `{}`; adding the over-listing assertion caught it on both. *Equality between two arms is
      weaker than equality plus a positive claim about what must survive.*
      - [x] **The open question ANSWERED and specced (`05158db`)**: swift's `gate --report` REFUSED the
            CONTRIBUTES counterexample instead of firing, and that is **over-broad**. The refusal is now
            MINIMAL: refuse only when the absent datum could CHANGE the answer. The class set only grows and
            `Reject` is upward-closed, so if the entry-alone classes already intersect the filter the rule
            FIRES — missing data could only add matches. **First place the document uses monotone denial to
            DO something rather than to be preserved.**
      ORIGINAL — 4d DISPATCHED as PART 27 — and the audit that preceded it IS the finding.** `grep -c` over
      `run.sh` returns **0** for `CONTRIBUTES`, `viaDispatchOn`, `dot-free`, `--class dynamic` and locale:
      **a whole rung of normative requirements shipped today with no differential behind any of its
      behaviour.** Seven rows briefed, each verified-to-catch, scoped to the engines that actually have the
      surface (`gate --report` is java+swift only; the frontier is a THREE-surface query).
      ORIGINAL — 4d. A conformance PART for the whole rung, once 4a/4b land. Must be verified-to-catch per engine:
      the three-row counterexample as a row that FAILS for an engine still keyed on absence, and the
      cross-engine `viaDispatchOn` LITERAL (`"run,untyped cross-package receiver,write"` and `"run"`) —
      the existing frontier differential only substring-checks that field and cannot catch an ordering or
      dedup divergence.
- [x] **4e DONE — floor is 0.24 across all SEVEN components, `release-preflight` exits 0.** It was not
      mechanical: I located FIVE strings and there were **FOURTEEN**, across five repos. Nine were found by
      watching a test fail, one at a time; a follow-up review found **six more**, including candor-java's
      **jar-embedded AGENTS.md** (the engine told an agent it spoke 0.23 while stamping 0.24 into every
      envelope) and **published npm/jbang metadata**.
      **THREE GATES WERE GREEN WHILE BLIND, each differently**: java's asserted the stale LITERAL so it
      *enforced* drift; ts's missed on **FORM** (`spec: "0.23"` evades `/spec 0\.2[0-3]\b/`) and had never
      swept `package.json`; the preflight's signal was buried under 220 fixture lines. All three now
      DERIVE the floor rather than assert it.
      ORIGINAL — 4e. Bump the floor to 0.24, sites located. Do NOT bump
      before then: the rung is tier-1 and VERDICT-CHANGING, so it needs the full pre-publish checklist and
      not a quiet edit.
      **The five strings** (one per engine plus the floor declaration the drift gate reads):
      | what | where |
      |---|---|
      | floor | `candor-spec/SPEC.md:20` — `**Version 0.23** — all code engines declare 0.23` |
      | rust | `crates/candor-report/src/lib.rs:226` — `pub const SPEC_VERSION: &str = "0.23";` |
      | java | `src/main/java/io/poly/candor/Candor.java:68` — `static final String SPEC_VERSION = "0.23";` |
      | ts | `scan.mjs:45` — `const SPEC_VERSION = "0.23";` |
      | swift | `Sources/candor-swift/main.swift:36` — `let specVersion = "0.23"` |
      **Then, in order** ([[candor-pre-publish-checklist]]): `candor/bin/release-preflight.sh` — its check
      **[2] is literally "no leftover prior-floor spec strings — the bump-miss signature"**, which is
      exactly the failure mode a five-site bump has; then four-way conformance; then per-engine CI
      (clippy/smoke/integration — the checks a local `test` skips); then a corpus test on a real repo; then
      re-review.
      **Also rewrite the ⟨0.24⟩ rung entry** in SPEC's version list — it says "IN PROGRESS — engines
      landing; NOT yet conformance-pinned, and no engine declares it yet", and all three stop being true at
      the bump.
      **The adoption note rides with it**: first rung whose primary change can turn a green gate red —
      measured **0** verdict flips on TRUSTED dep reports, **52 of 145 (36%)** on STALE ones, reachable only
      through reports the build cannot verify.
      ORIGINAL — 4e. Bump the floor to 0.24 once 4a-4d are green four-way. The rung is OPEN in SPEC but marked IN
      PROGRESS and no engine declares it. Per [[candor-versioning-ladder]] the tier decides the trigger;
      this is **tier-1** and verdict-changing, so it needs the full pre-publish checklist, not a quiet bump.

### 5 — DECIDED, NOT OPEN · re-open only with new evidence
These were refused WITH MEASUREMENTS and the arguments live in the code. They are listed so nobody
re-litigates them, not as work.
- **swift's local-protocol erasure arm** — suppress costs 5 losses and 7 entries REMOVED; disclose costs 9
  concrete effects → hedge.
- **rust's `ambiguous:` rename** — 58/200 crates → 0/200. A deletion.
- **java's concrete-dep override** — 12 of 22 changed functions are `super` calls that can never dispatch
  to an override. It is the wrong KEY, not a missing bound.
- **rust's withdrawn-key disclosure** — built and verified in five directions, costs 15–20% of functions
  newly carrying `Unknown`. **DISSOLVED 2026-07-27 by the collision decision in (2)** (`b47c9ab`): the union
  withdraws nothing, so there is no withdrawn key left to disclose. The same defect closed at a fraction of
  the cost — 7 effect-items across three corpora against 15–20% of all functions. Recorded because the
  cheap fix only became visible once the expensive one had been built and measured.

### 6 — PRECISION GAPS · parallel, and I recommend NOT doing them yet
Seven rows, **none a silent under-report**: swift package-vs-module chaining inertness, swift
`boundLocals`/`catchBindings` (filed with a 12-line repro after a 405-loss revert), swift `returnsIdx`,
swift nested-type factory, rust's quiet span half (72.4% precondition, no known wrong output), rust's
`ambiguous:` candidate set (156/930 with ≤1 candidate), ts's remaining malformed reasons.

**The argument for waiting is a measured one.** Three review rounds today produced **29 confirmed defects,
every single one a guard written during the wave under review**, all with clean A/Bs and green suites.
These rows are exactly that kind of change — narrowing guards at the fabrication boundary — and none of
them closes a lie. On today's base rate, four agents here would ship roughly ten new defects to find in
exchange for precision nobody is currently missing. Revisit when the defect rate on new work falls.

### 7 — RELEASE · needs Tom, not work
- [→] **candor-ts's build id vs the family's — DUPLICATE, see the single entry under THE STANDING BAR.**
      Two entries for one open question, written six days apart, is how a queue starts under-counting
      itself: the second reader closes one and the other survives as a live item nobody owns.

## DONE — the THIRD review, swift only (4 confirmed + 1 alignment, all closed 2026-07-27)

A third adversarial pass, scoped to candor-swift's half of the wave. **Four confirmed defects, and the
base rate held for the third time running: every one was a guard written during the wave under review.**
All five rows below are closed, each with both fixtures (the second written first), each guard mutated
out and the failing test named, A/B over 13 real Swift packages with both arms' release binaries kept by
content hash, four-way conformance green after each commit.

- [x] **swift `CallCollector.swift:1465` — the TYPED enum-payload binder called `shadowName` only**, so
      `protoTyped`/`arrayElem`/`opaqueElem`/`dictElem`/`tupleElem` survived a rebind that wrote `vars`
      over the top. A payload binding shadowing a same-named PROTOCOL-TYPED parameter dispatched over
      that protocol's conformers. **FIXED candor-swift `ba91a27` — and the review's real question was
      about the TEST**, so: `NameKeyedStateTests` was green through it and correctly so. That file
      derives the SET of name-keyed maps and checks each MAP's classification; what was violated is
      per-NAME and per-CONTROL-PATH, which a parse tree cannot see. **Both derivable strengthenings were
      priced and both would have PASSED on the defective code** — "every method that writes a
      per-binding map must mention a clear helper" (the method mentioned both) and "every write SITE
      must be on an authored list" (the site predates the wave that broke it, and it re-introduces the
      authored list that file exists to delete). The remedy is at the site — the branches are fused so
      no path can write a type without the clear — and **the limit is now written into the file**, since
      the next reader would otherwise assume coverage.
- [x] **AND THE RENAME CONTROL THEN FOUND FOUR MORE (candor-swift `7646c3d`).** One mechanism, five
      doors: `if let`, an ANNOTATED closure parameter, a tuple destructure, and a nested `func`
      parameter, each shadowing a protocol-typed parameter and each reading `['Fs']` against an ABSENT
      control. **Two of the second-direction rows came back as RECOVERIES**, which is the part worth
      carrying: the stale entry was not only fabricating, it was MASKING the shadowing binding's own
      type, so `if let j = o { j.go() }` resolves `Ctx.go` for the first time. The ordering carve-out
      (`let u = u.asURL()` resolves THROUGH the entry being cleared) is a denylist and is pinned by a
      row whose mutant fails only it. Two sites take a narrower treatment for stated reasons — the
      nested-func parameter clears only the SCOPED maps (`vars` is not in `ShadowSave`, so clearing it
      would leak outward), and the closure parameter is cleared inside `visit(ClosureExprSyntax)`
      because only there is the save live.
- [x] **swift `main.swift:468` — `sweepStale` deleted a report a HEALTHY sibling had just written.** It
      skipped deps that SUCCEEDED, which is not the set of files THIS RUN PRODUCED. Two path deps
      deriving one report name (a vendored fork beside the upstream checkout) put the failed copy in
      charge of the healthy copy's file — and the non-empty sweep triggers the retry, which rewrites it,
      and the second sweep deletes it AGAIN. Consumer `['Fs']` + literal surface → `invisible:
      ['Shared']`. **FIXED candor-swift `497e117`**: never delete a file this run wrote (`confirmed` was
      already that set and was otherwise write-only). The per-dep failure line no longer claims a
      removal that did not happen — a false disclosure in the collision case, twice over.
- [x] **swift `main.swift:447` — the sweep's manifest parse was not the writer's, under a comment saying
      it was.** Anchored after `Package(` vs the writer's unanchored first `name:`; a hoisted target or
      dependency array splits them. **BOTH directions land on one fixture**: the stale report SURVIVES
      (`use0` ABSENT — a ⟨0.21⟩ purity claim over a dep that writes to disk) and a user-placed file
      under the invented name is DELETED. **FIXED candor-swift `fce24ec`** — one parse and one name
      transform, both the writer's, both called by the writer. Two of the row's assertions were
      DECORATIVE at first and the mutant is what showed it: both file names appear in the mutant's
      stderr with the two lines' contents SWAPPED, so a `contains` over the whole stream could not tell
      the arms apart. They assert per LINE now.
- [x] **swift `Deps.swift:424` — `incompletePkgs.subtract(coveredPkgs)` restored full coverage to a
      package as soon as ANY report claiming it was complete.** **FIXED candor-swift `756a8f0`,
      incompleteness now wins.** Coverage turns SILENCE into a purity claim, so a set of reports' silence
      is only as strong as the weakest completeness claim in it — **two reports covering one package do
      not cover the same SOURCE**. Measured: B alone hedges `invisible: ['RatesDep']`, A+B went ABSENT.
      The sharper form is `63bbe87`'s argument arriving on the COMPLETENESS axis — two fresh reports
      disagreeing on a key withdraw it (rule 1, correctly) and complete-wins turned the withdrawal into
      a purity claim over a function both reports call effectful (`A alone go->['Net']`, `C alone
      go->['Exec']`, `A+C go->ABSENT`). The staleness line one below is NOT the same shape and is
      untouched: a stale report makes no claim about its own source, and swift's `insert` keeps the
      trusted answer on a fresh/stale collision (`ca5feb0`) rather than withdrawing the key — **which
      also closes the open "FOR candor-swift" row further down this file: swift does NOT drop the
      colliding key the way rust does.** `testPackageChainedCompleteAndIncompleteKeepsItsCoverage`
      PINNED the defect (item 7g) and is inverted with flip instructions rather than deleted.
- [x] **swift `Deps.swift:212` — the identical-entry exemption was a PARTIAL port** of rust `6f2210c`:
      trusted arm only. Two byte-identical entries from two STALE reports still withdrew the key,
      costing the §2.1 `Unknown` downgrade the stale arm exists to produce (`['Unknown']` +
      `dep-stale:RatesDep` → a bare ledger hedge, so `deny E Unknown[…]` stopped firing). **FIXED
      candor-swift `cbed5df`**, aligned with rust. **The population is not marginal: 476 of 8367 join
      keys already collide WITHIN a single real report, in 12 of 13 corpus packages** (Alamofire 119,
      pollen 104, vapor 95). Found while writing it and stated in the code rather than left to be
      discovered: the stale-vs-stale WITHDRAWAL is now unreachable, because a stale entry is built from
      nothing but its package and the key begins with that package — kept, not deleted, because it goes
      live the moment a stale entry carries anything per-FUNCTION.

## OPEN — the 2026-07-27 review of the sweep wave (10 confirmed, 9 resolved, 1 live — rust incompleteness)

A second workflow review, scoped to the ~40 commits the five-shape sweep produced. **Ten confirmed
defects. Every one is again a guard written during that wave** — the same base rate as the previous
review's nine-for-nine, and the reason that review was commissioned at all. Two were mine and are closed;
a third (java's `entryPackage`) and the java half of the incompleteness door closed 2026-07-27, as did all
three rust rows — two fixed, one REFUSED with the counterfactual measured (a refusal with numbers is a
result). None is recorded anywhere else — they arrived in a task notification, which is
the "a residual recorded only in a narrative is a residual nobody will find" failure repeating one level
up, so they are written here first and worked second.

### Silent under-reports — do these first
- [x] **ts `scan.mjs:2631` — the `.bind` arm's new `hofInvokesArg` position gate returns early**, so a
      static/free-form HOF whose callee signature cannot be resolved now DROPS a `.bind`-wrapped dependency
      callback it previously charged. Measured as a `deny Fs` flip from exit 1 to **exit 0**. A guard added
      this wave, narrowing past a real reach — standing-bar item 0, for the third wave running.
      **FIXED candor-ts `b66b69a`.** Reproduced at gate level first (`deny Fs src.api`: two trees exit
      1 → 0, single-tree control exit 0 in BOTH arms, which is what makes it a boundary defect).
      `hofInvokesArg` is a POSITIVE test whose return value cannot distinguish "invoked" from "no
      evidence"; the arm now asks for the OPPOSITE evidence — drop only when the name map excludes the
      position AND the signature positively declares a non-callback. The hard part is that `any` cannot
      be that evidence: `forEach(cb, thisArg?: any)` and a loose library's `fn: any` are the same type
      with opposite meanings, so `calleeParamIsCallable` went THREE-VALUED (`null` = no information) and
      the receiver slot is recognised by parameter NAME (`thisArg`) — a denylist whose failure mode is
      an over-charge on a contrived shape, never a reach. `hofInvokesArg` tests `=== true`, so the
      by-reference arm is untouched by construction.
      - **The wave's own no-fabrication test COULD NOT FAIL, and that is why the regression shipped.**
        It asserted `!includes("Fs")` on a DEP ref in the thisArg slot — but that arm's only possible
        output is an Unknown disclosure, so the shape it was written for (`['Unknown']` before the guard,
        pure after) was invisible to it. Mutating the guard out left the suite **766/0**. Now five
        mutants produce five named failures; a bound LOCAL writer sits in the slot so a fabrication
        shows up as the concrete Fs. Standing-bar item 8c, in the sharpest form yet: the guard was
        *undetectable*, and nobody checked.
      - **A/B: 22 real targets, ~13,000 analyzed functions, ZERO of everything** (gains, losses,
        Unknown delta, entry delta) — and per item 8 that is a claim about the corpus first, so the
        precondition was instrumented: exactly **3** `.bind` arguments reach the non-local HOF arm in
        the whole corpus (apollo-client ×3), all at position 0, all agreeing old-gate vs new. The
        differing branch fires **zero** times. The change is a strict widening by case analysis on the
        four return values, so losses are impossible by construction — the corpus can show it costs
        nothing and cannot show it gains anything. The `.bind`-into-HOF idiom has been all but replaced
        by arrow functions in modern TS; it survives in class-style code, which is where the reviewer's
        shape and the fixture live.
- [x] **~~rust~~ + ~~java~~ + ~~swift~~ — only candor-ts withholds coverage from a dep report that
      declares ITSELF incomplete** (non-empty ⟨0.21⟩ `unanalyzed`). The other three gate coverage on
      STALENESS alone, so an incomplete dep report's silence still reads as a purity claim. This is
      shape 1's second door — the one ts found in its own sweep (`21277eb`) — unswept in three engines.
      **The sweep found the door and did not carry it across, which is the exact thing the sweep exists
      to do.** **JAVA `d1d3045`. SWIFT `74cd8f1`. RUST `dbab8be` — THE VEIN IS NOW CLOSED FOUR-WAY.**
      - Entries KEPT (they came from source the dep really did read), coverage withheld, stderr says why.
        Absent or explicitly EMPTY `unanalyzed` = complete; anything else, malformed included, fails
        closed. ts's item-0 trade — the ledger hedge REPLACING half 1's `Unknown[dispatch]`, its
        `deny Fs Unknown[dispatch]` going exit 1 → 0 — **cannot happen in java**, because `7e41327` had
        already given chained-ness its own ungated set. That is an argument, so it is a third arm of the
        κ-curated fixture rather than a comment.
      - **Two things to carry into rust and swift.** (1) In java, coverage AND chained-ness are each
        anchored TWICE — a file-level envelope registration and an entry-hash fallback — so gating one is
        a **no-op wearing a fix's clothes**: the mutant that gates only the file-level path fails
        NOTHING. Count the anchors before believing a gate. (2) Reading an ABSENT `unanalyzed` as
        incompleteness is the tempting fail-closed reading and it is wrong — that mutant fails seven
        tests across four classes, because it deletes chained coverage outright. The writer omits the key
        when the manifest is empty, so absent = complete; malformed = incomplete.
      - Measured: 7 chained real jar pairs from `~/.m2`, **0 of 11 real dep reports declare an
        `unanalyzed` unit** — the corpus is the fabrication control and the fixtures are the evidence.
        Armed (every dep report made to declare itself incomplete, envelope only, `functions`
        byte-identical): 4147 functions gain `invisible`, 662 entries appear, **0 effect gains, 0 losses,
        Unknown delta 0 on every pair** — the additive shape, with half 1 still speaking.
      - **SWIFT (`74cd8f1`).** Same treatment, and java's two warnings both applied. (1) The anchors:
        swift registers coverage in THREE places — the envelope `package`, the plural `packages`, and
        each entry's hash prefix — so the registration went through one `register(pkg)` closure rather
        than being gated at one of them. (2) Absent `unanalyzed` = complete, for the same reason (the
        writer omits the key when the manifest is empty). ts's item-0 trade CANNOT happen here either,
        but for a different reason than java's: swift's half-1 gate reads `isChained`, so adding
        `incompletePkgs` to that predicate is what preserves it — and the mutant that omits it fails
        exactly the half-1 row, so it is an assertion rather than an argument. Six guards, six mutants,
        each failing its named test and only it. Corpus: 0 of 34 real Swift packages produce a report
        declaring an `unanalyzed` unit; A/B byte-identical.
      - **A SECOND DEFECT FELL OUT OF THE FIXTURE, in the index rather than the coverage set:** two
        reports carrying an IDENTICAL entry for the same key were WITHDRAWING it as ambiguous. The
        canonical-path dedup catches the same FILE twice and not the same report under two names, which
        is the ordinary shape once `--workspace` prepends its scanned dir to a configured `CANDOR_DEPS`.
        §2 rule 1 forbids PICKING between candidates; there is nothing to pick when they are equal.
        Worth checking in rust and java: the fixture that finds it is "chain the same package twice".
        (rust had it too and closed it independently, `6f2210c`; java is clean — last-wins keeps an answer.)
      - **RUST (`dbab8be`), and this is the one engine where the corpus is EVIDENCE rather than a
        fabrication control.** java measured 0 of 11 real dep reports declaring `unanalyzed` and swift 0
        of 34 packages; rust measures **4 of 855** (0.47%, two distinct crates) and **1 of 200** crates.io
        crates scanned cold. The live case is as sharp as the shape gets: **`signal-hook-registry` 1.4.8's
        entire `src/lib.rs` fails to parse**, so its report carries two functions and an `unanalyzed`
        manifest naming the library itself — and chained, `signal-hook`'s `PendingSignals::add_signal`,
        whose body is `unsafe { signal_hook_registry::register_sigaction(signal, action) }` (installing a
        signal handler), read as a confident purity claim about that crate. Post: `invisible:
        ['signal_hook_registry']` + a coverage-ledger row. **Whoever repeats a "0 real reports" control in
        another engine: rust's 0.47% says the shape exists in the wild, so a 0 there is a claim about
        that ecosystem's parsers, not about the door.**
      - **The anchor count is a PER-ENGINE fact and rust's is 1.** Four registration sites (envelope
        `package`, plural `packages[]`, filename fallback, entry `hash` prefix) all funnel through one
        `cover` closure, and coverage is CONSUMED at exactly one place — so one conjunct is the whole
        gate, unlike java's two. ts's item-0 trade cannot happen here for swift's reason: rust's half-1
        gate reads the CHAINED set (`deps_idx.crates`), which an incomplete report is still in — asserted
        as a fourth arm on the half-1 fixture, and the mutant that gates it on coverage fails that row.
      - **rust does NOT adopt swift's `incompletePkgs.subtract(coveredPkgs)`**, for the same rust-specific
        reason `63bbe87` refused to align fresh-vs-stale: rust's index DROPS a key two dep entries
        disagree under, so complete-wins makes the withdrawn key read confidently PURE. Pinned with flip
        instructions; the mutant that implements complete-wins fails exactly that fixture.
      - **Eight guards, eight mutants**, and one of them deleted a guard rather than proving it: the
        `!stale &&` conjunct on the incompleteness flag failed NOTHING, because `cover`'s `else if`
        already decides the precedence. Item 8c — a guard that costs nothing needs deleting.
      - A/B, three chained projects, both binaries by content hash: **0 gains, 0 losses, 0 entry delta, 0
        Unknown delta**, dep trees byte-identical — and per item 8 the precondition was instrumented
        rather than assumed: the mechanism DOES fire (2 crates lose coverage on pgman and ebman) but the
        κ ledger only asks about a crate the TARGET calls into with a first-segment-qualified path, and
        none of the three does. ARMED (all 855 dep reports made incomplete, envelope only): +123 entries
        and +278 functions gaining `invisible` across the three, with 0 effect gains, 0 losses, Unknown
        delta 0. 200 crates.io crates scanned UNCHAINED in both arms are byte-identical.

### Fabrication / data loss
- [x] **swift `CallCollector.swift:813` — `fnValueAlias` is a name-keyed RESOLUTION table no clear path
      touches.** The catch-all binder clears vars/protoTyped/arrayElem/opaqueElem/dictElem/tupleElem/
      monoNames/depBoundLocals/localConstStrings — but not this one — and `leaveShadowScope` does not
      save/restore it, so a free-fn alias for a name answers for every later or inner binding of that name.
      **The SEVENTH map in this mechanism**, after six defects across three days. Also at `:2036`, `:954`.
      **FIXED candor-swift `c2c85e3`**, and the DERIVATION landed with it (`97c6b12`, below).
      - Reproduced with the rename control: `func f(_ jobs: [() -> Void]) { let g = eff; for g in jobs
        { g() } }` reads `['Fs']` and the identical body binding `h` is ABSENT. The inner-shadow form
        (`if c { let g = { }; g() }`) is the same defect through a door `clearBinding` does not reach at
        all — a `let` that DOES type never goes near it — which is why the clear lives in `shadowName`.
      - **The widest of the five**: the other four are TYPE indexes, so leaking one charges whatever some
        type's member happens to do; this one names a FUNCTION and charges its whole transitive set.
      - **Why the previous audit cleared it is the durable part.** It wrote "an aliased fn value called
        after a shadowing loop still resolves" — the LOSS direction. The FABRICATION direction was never
        run. **A rename control run in one direction is half a control.**
      - Three guards, three mutants. The third is the ordering carve-out `protoTyped` needs one map over:
        `let g = g` resolves THROUGH the binding it replaces, and the re-aliasing branch cannot restore
        it because its RHS is a shadowed local rather than a `localFreeFns` name.
      - A/B 34 real Swift packages: 0/0/0. Per item 8 that is the control, not the evidence —
        instrumented, the rung is established **once** in the whole corpus (console-kit
        `let rpp = linux_readpassphrase`) and the fix's trigger fires **zero** times. The probe was an
        ARM and was removed before the commit (item 8b: an env read in the collector writes Env into
        candor's own self-scan).
- [x] **swift `main.swift:425` — `--workspace`'s new `sweepStale()` deletes every `*.json` in
      `<root>/.candor/deps` that this run's own path-dep scans did not produce**, including reports the
      USER placed there for non-path dependencies. Unrecoverable, and not an analysis defect at all. Also
      at `:439`. **FIXED candor-swift `b4f6cbc`.**
      - The sweep STAYS (it exists for `43a0eaa`'s measured reason); what changed is that a file this run
        did not write is never a deletion candidate. **Ownership is DERIVED from `Package.swift`, not
        marked** — a manifest sidecar would answer only for caches written after the change, leaving the
        first post-change run over an existing cache in exactly the state `43a0eaa` fixed. The candidates
        are the discovered path deps; a FAILED dep's file is found by the package name an earlier round
        recorded, else its own manifest `name:`, else the directory basename — the writer's own three
        sources in the writer's own order. Everything else is named on stderr and left alone.
      - Residual, disclosed: a report for a package that USED to be a path dep and no longer is lingers.
        Information kept rather than destroyed.
      - The manifest-name row uses a dep whose DIRECTORY is `libdep-src` while its package is `Dep0`,
        because with the two equal the basename fallback answers correctly too and the branch under test
        could be deleted with the row still green — item 8c's shape, avoided by construction.
      - **The release build caught what the debug build and 328 tests could not**: a nested func closing
        over a top-level `var` a sibling closure writes is a Swift-6 `sending` diagnostic under
        whole-module optimization ONLY. The first "verified" arm was a binary the failed build had left
        on disk — item 7c, in a new spelling: `swift build -c release` failing does not remove
        `.build/release/`.
- [x] **ts `scan.mjs:504` — `--workspace` DELETED the stale cached dep report AFTER the fixpoint rounds
      and never re-derived them.** `95d0b8b` correctly established that a cached report this run did not
      write is not this run's answer, and swept one — but the sweep runs after the rounds, and every
      child in those rounds is spawned with `CANDOR_DEPS` pointing at the SAME cache. So a sibling that
      scanned cleanly had already chained the report being deleted, its own cached report kept that
      answer, and the parent chained the sibling. **The file went; the conclusion drawn from it survived
      one hop away.** swift's `43a0eaa` re-runs its fixpoint for exactly this reason and ts did not.
      **FIXED candor-ts `7ba3776`.**
      - Reproduced on a two-hop workspace (`libb` imports `liba`; `liba` loses its analyzable source
        while its `.d.ts` keeps it RESOLVABLE), with the COLD arm as the control: WARM `callB` **ABSENT
        from `functions`** — a ⟨0.21⟩ positive purity claim — against COLD `invisible: ['liba']` plus a
        `coverage.uncovered` row. **And it moves a GATE through the interface-CHA join**: `liba`'s run-1
        report carries an `interfaceUnion` entry, so the concrete `Fs` survived inside `libb`'s cached
        report and `deny Fs` was **exit 1 warm / exit 0 cold** — RED over a body not on disk.
      - **NO `deny` goes exit 0 → exit 1, and that is structural rather than an accident of the
        fixture.** candor-ts gates read `inferred` (`policy.mjs:235`), an unchained-but-resolvable dep
        call yields `invisible` and never `Unknown`, and withdrawing a chained report's coverage can only
        move a call from the half-1 `Unknown[dispatch]` arm to the ledger's `invisible`. So sweeping can
        only ever REDUCE `inferred`. Worth knowing before anyone hunts for a `deny Fs` flip in the
        cardinal-sin direction here: the sin is at the ⟨0.21⟩ report level, which is also where swift
        `43a0eaa` and ts `95d0b8b` measured their own.
      - **Scoped honestly: the wrong answer lasts exactly ONE run** — measured, runs 3 and 4 are correct,
        because by then the swept file is gone before the siblings are scanned. That run is the one a CI
        gate sees the first time somebody breaks a workspace package, over a persisted `.candor/deps`.
      - **NO second sweep**, unlike swift: a report file only ever appears from a success, so a second
        `dropUnanswered` can only return `[]` — item 8c, a guard that costs nothing needs deleting rather
        than writing. The re-pass is gated on something having been swept and DISCLOSES itself on stderr,
        because without that line the gate is invisible in every channel the suite reads (an ungated
        re-pass is byte-identical and merely slower).
      - **The A/B needed its corpus proved first, and the first one was inert** — item 8, and exactly the
        trap this queue warns about. A bare vue-core checkout resolves NO cross-package declaration, so
        `--workspace` chained 12 reports and changed NOTHING (chained == unchained, 0 gains, 0
        `invisible`). With each package's `types` pointing at its own source entry the join is real
        (runtime-core's own ledger names `@vue/shared` at 273 calls, `@vue/reactivity` at 119). Then:
        clean arm **byte-identical** across the change (app report and both dep reports); armed
        (`@vue/shared` given an unreadable `.candor/config`, source untouched) **0 effect gains, 0
        losses, Unknown delta 0**, and **+53 `invisible` and +18 entries recovered in the carrier's
        report**, 3 reaching the consumer. **The invariant: POST-armed is byte-identical to POST-cold and
        PRE-armed is not** — a cache must not change the answer.
- [x] **ts — and the ownership derivation `95d0b8b` introduced had TWO defects, found by asking its own
      two questions rather than by suspicion. FIXED candor-ts `29cd992`.**
      - **A file a USER placed CAN be deleted, and it needs no malice.** The rule is "a file candor would
        have OVERWRITTEN on success is the file it removes on failure", which holds only while the
        writer's name and the sweeper's candidate name are the same string — and they were two spellings:
        the writer took `report.package` on trust, `failedDepName` required a non-empty STRING. A
        manifest saying `"name": 123` made `name.replace` throw, the `catch` read a scan that **exited
        0** as a failure, and the sweep deleted `<directory-basename>.json`, a name that writer would
        never have produced. stderr said "could not scan utils" about a successful scan and the count
        line claimed to have chained `123` with no file on disk. **Count the spellings of a derivation,
        not just the anchors of a gate.**
      - **A write that THREW was recorded as an answer.** `answered`/`ownFiles` sat three lines above the
        write, so a read-only cache dir or a full disk marked the dep answered, the sweep skipped it, and
        the previous run's report stood in for one this run never put on disk — `95d0b8b`'s own class
        through the write door instead of the scan door.
      - **Two clean negatives, recorded because deletion is unrecoverable.** An INTERRUPTED run
        self-heals (measured: the cache converges on the next run). TWO PROCESSES on one `.candor/deps`
        FAIL CLOSED — fed a report truncated at 40 bytes the consumer prints "CANDOR_DEPS report
        unparsable, skipped" and reads `invisible`, so non-atomic writes cost precision, not soundness.
      - Inert on real input and instrumented rather than assumed: **0 of 28,407 real `package.json`
        manifests across 61 `node_modules` trees** have a non-string `name`.

### NEW, from the same swift pass — the EIGHTH and NINTH maps, REFUSED with numbers
- [~] **swift `boundLocals` (and `catchBindings` with it) — the same mechanism, in the map neither audit
      classified, because it is not a FACT.** Every other row in this family is a name-keyed fact (a type,
      an opacity, a provenance, a literal, an alias) outliving its binding. `boundLocals` is the other
      half: an EXISTENCE claim — "this name names a local" — and both audits were looking for facts.
      **Three forms REPRODUCED with rename controls, all fabrications:**

      | form | reads | rename control |
      |---|---|---|
      | `if case let token? = o { print(token) }` inside a type with an effectful computed `token` | `['Env']` | ABSENT |
      | `catch let token { print(token) }`, same type | `['Env']` | ABSENT |
      | `if case let boot? = o { print(boot) }` beside an effectful top-level `let boot` | `['Env']` | ABSENT |

      It is written by **2 of the ~7 binder forms** (a `let`/`var` identifier and a tuple destructure),
      so a loop, closure, `case let` or `catch` binder registers no shadow at all; a `for` binder happens
      to be safe only by ACCIDENT of usually landing a type in `vars`, which the bare-read arm tests
      instead. `catchBindings` is entangled with it: that map is function-wide too, and its shadow guard
      is a `!boundLocals.contains` PROXY that stops working the instant every binder writes `boundLocals`
      (a catch binder would shadow itself).

      **THE OBVIOUS FIX WAS WRITTEN, MEASURED AND REVERTED.** Write it in `shadowName` (the one path every
      binder takes), save it in `ShadowSave` (function-wide it would silence the enclosing type's real
      property read for the rest of the body — the two directions genuinely oppose here), defer it past a
      self-referential initializer (`let boot = boot` reads the GLOBAL), and add `boundLocals` to the
      bare-read arm's shadow test. All five fixture rows go the right way and both second-direction rows
      are RECOVERIES. Then the corpus:

      | arm | vs. baseline |
      |---|---|
      | everything | **1 gain, 405 losses, −93 entries** |
      | minus the bare-read arm's shadow test | 1 gain, 292 losses, −77 entries |
      | the bare-read arm's shadow test ALONE | 0 gains, **173 losses**, −8 entries |
      | `shadowName` write + scope + deferral, no bare-read change | 1 gain, **305 losses**, −77 entries |

      Two sub-cases traced, and they point OPPOSITE ways, which is the whole reason this is filed rather
      than shipped. (a) The bare-read arm's 173 are largely FABRICATIONS being removed: swift keys global
      units by BARE NAME, so pollen's `PollenForecastCache.fetchOrLoad` — which holds a local
      `let task = Task<…>{…}` — was charged `Exec` from a top-level `let task = Process()` in a different
      target's `CapturePollen.swift`, and the same for `outPath`. That is the open
      [global-unit-identity vein](SOUNDNESS-VEIN-global-unit-identity.md), reached through the shadow
      discipline. (b) The other 305 include units DISAPPEARING and disclosed `Unknown`s and `invisible`s
      vanishing, reduced to a 12-line repro (vapor's `AbortError.swift`: `DecodingError.reason` and
      `.description` both vanish) that was NOT explained inside the session's budget.

      **Refused under item 1: 305 report changes I cannot trace is not shippable, in either direction.**
      A loss you cannot explain is not a fabrication you have removed. Both maps are filed in
      `NameKeyedStateTests.disposition` as `.knownDefect` with these numbers attached, so the next audit
      inherits them instead of the surprise — and the classification test makes walking past them again
      a deliberate act rather than an oversight.

      **Whoever picks this up: start from the 12-line vapor repro, not from the corpus.** The two
      sub-cases must be separated before either is shipped; they are different defects that happen to
      share a map.

      ### THE 12-LINE REPRO, EXPLAINED — and the answer is that a UNIT DISAPPEARING WAS THE FABRICATION
      **candor-swift `083f370` lands the enum-payload half. 0 gains, 15 report changes over 13 packages,
      every one traced.** The unexplained losses were not losses.

      Reproduced in 13 lines, and the mechanism runs end to end:

      ```swift
      import BlindMod                    // any module the classifier doesn't cover
      struct Ctx {}
      enum E { case one(Ctx) }
      extension E {
          var reason: String { switch self { case let .one(ctx): return help(ctx) } }
          var description: String { "d: \(self.reason)" }
          func help(_ c: Ctx) -> String { "x" }
      }
      ```

      1. `case let .one(ctx)` binds through a `patternExpr > identifierPattern` — **no
         `ValueBindingPattern`**, so `typeEnumCaseBinding` skipped it (its own comment said so) and only
         `visit(IdentifierPatternSyntax)`'s `clearBinding` ran. `ctx` ends up in NEITHER `vars` NOR
         `boundLocals`. The multi-payload form reaches the same state through the ARITY guard, and an
         ambiguous case name through the ambiguity guard — three doors, one state.
      2. `help(ctx)` then hits the **fn-ref-as-argument rule** (`xs.map(transform)`, CallCollector ~1520):
         a bare identifier argument that is not a known local is taken to name a FREE FUNCTION and emitted
         as an unqualified untyped call.
      3. That call resolves to no local unit, so the Driver sets `resolved = false` — **which is the
         Driver's entire test for "this unit reaches code the scan cannot see"** — and the per-fn
         `invisible` disclosure names every blind module in the file's import scope.
      4. **A unit is in the report iff it has effects OR a disclosure.** `DecodingError.reason` has no
         effects. Its only reason to exist as an entry was that `invisible`.
      5. `DecodingError.description` reads `self.reason` → a property edge → it inherits `reason`'s
         `invisible` transitively. When `reason`'s goes, so does its own, and both entries leave.

      **So the disappearing units were a fabricated disclosure being withdrawn, and the disclosure's
      parent was a phantom free-function reference built out of a local binding's name.** The previous
      round was right to revert and right about the shape (two defects, one map); what it could not see
      was that ONE of its loss classes was the same fabrication-removal as the other, arriving through
      the disclosure channel instead of the effect channel. `UploadRequest.task` is the same story with
      the volume turned up: `case let .data(data)` resolved to the unrelated `DataRequest.data` accessor
      and inherited an `Unknown` from it.

      **What landed** (`083f370`): the payload names go into a SEPARATE, LEXICALLY SCOPED
      `casePayloadLocals` that the collector's in-walk guards consult alongside `boundLocals`. Both
      spellings are claimed for the EXISTENCE claim; only the `.active(let c)` spelling is TYPED, as
      before. Keying on `patternExpr` is exact in both directions — a matched CONSTANT parses to
      `declReferenceExpr`, a literal to `integerLiteralExpr`, so a compared value can never be read as a
      bound name (verified against SwiftParser, not assumed).

      **What was refused, with numbers.** Three arms measured over the same 13 packages, binaries kept:
      | arm | vs. baseline | verdict |
      |---|---|---|
      | payload names into the FUNCTION-WIDE `boundLocals` | 0 gains, 15 changes — **but drops a genuine edge**: swift-syntax `IfConfigDiagnostic.asDiagnostic` binds `syntax` in three `if case` blocks and then reads the real `self.syntax` | REFUSED — a silent under-report manufactured by a fabrication fix |
      | scope `boundLocals` ITSELF (`ShadowSave`) | +1 entry, and **`if c { let loadIt = { }; loadIt() }` starts charging the caller the free `loadIt`'s effects** | REFUSED — `Driver` reads `boundLocals` ONCE, AFTER the walk, where a restored set is empty; a post-hoc guard has no lexical position |
      | also TYPE the `case let .active(c)` spelling from `singleAssoc` | 4 new `Unknown`s (`dispatch:URLConvertible.??`, `LocalizedError.map`, `URLQueryFragmentConvertible.*`), 1 withdrawn, 1 `invisible` withdrawn | NOT LANDED — the typing is right; it feeds the external-supertype rung, which counts a LOCAL PROTOCOL as an external supertype and discloses on `??`/`*`. Separate row below. |

      **Two residuals this un-masked, both filed rather than patched:**
      - `Driver`'s guard is "was this name bound ANYWHERE in the unit", so `let location = location(converter:)`
        (swift-syntax `Note.debugDescription`) loses a real edge to `Note.location` — the self-referential
        initializer carve-out `fnValueAlias` already needed, one consumer over. Over-suppression, so it is
        the direction a call-graph guard is allowed to be wrong in — but it is a real miss.
      - a bare read of a **PARAMETER** charges the enclosing type's same-named property
        (`TokenKind.fromRaw`'s `text`), and today that only stays hidden because some inner binder happens
        to have poisoned the function-wide set. The `boundLocals` `.knownDefect` entry now names the three
        binder forms still missing — catch, closure parameter, function parameter — instead of "~5 of 7".
      - TCA `TypeSyntax.genericSubstitution`'s `genericBase?.identifier` never resolved in EITHER arm
        (proved by deleting the case-binding block: both arms lose the edge). A dictionary-of-optionals
        receiver is untyped; not this vein.

### The remedy for the whole family — DONE
- [x] **swift — the set of maps a rebind must invalidate is now DERIVED, not listed** (candor-swift
      `97c6b12`). `42093b6` removed the enumeration of binder FORMS and left the enumeration of MAPS
      standing, which is where defects six and seven came from. `NameKeyedStateTests` parses
      `CallCollector.swift` with SwiftParser, enumerates the class's stored properties from the parse
      tree, and requires each to be classified — cleared (and whether scoped), a deliberately-kept HEDGE,
      a program-wide index, or not per-binding. Adding a map without the decision fails a test;
      classifying one as cleared without writing the clear fails another; classifying one as scoped
      without BOTH saving and restoring fails a third (`opaqueElem` shipped with exactly that half).
      Three mutants, three named failures, and the stale-entry direction caught a real one unprompted on
      its first run.
      - **The honest limit, stated in the file**: the SET is derived, the JUDGEMENT is authored. Whether a
        `[String: X]` is keyed by a binding name or a type name is a fact about meaning, not syntax, and
        the hedging sets must NOT be cleared — so the value is in forcing the decision to be written once
        per property, with its argument, not in making it automatic.
      - Reflection was unavailable (`CallCollector` is in the executable target, which a test target
        cannot import), so it is a source-level test — with its own controls, since an extraction that
        silently finds nothing would pass every row vacuously.
      - **The "rewrite the binding model" option was RE-PRICED with the seventh instance in hand and the
        verdict STANDS.** Fusing the flags into `vars` still requires `vars` to become lexically scoped,
        which it deliberately is not (function-wide with clear-on-rebind: a stale TYPE is dangerous
        inward and merely lossy outward), and doing it without that scoping makes every flag leak outward
        the way types do. What changed is the GROUNDS: the reason to keep deferring it was "the residual
        is a new map added later without being added here, which is a review question" — and this pass
        proved a review question is not enough, twice. It is now a TEST question, which is the thing the
        rewrite was wanted for. Re-open the rewrite only if a defect appears that the classification
        cannot express.

### Cross-engine divergence — `Unknown[class]` gates now fire differently per engine
- [x] **ts `query-core.mjs:333` — a hierarchy-sidecar key the reader cannot interpret was coerced to `[]`
      and KEPT, which is a PHANTOM TYPE.** Routed from java's `bb8459a`/`403f24b` `"@superclass"` rung.
      Not inert: `callersFrontier` gates on `Object.keys(hierarchy).length > 0`, so ONE metadata key takes
      the frontier off its documented over-listing simple-name fallback and onto the precise subtype test
      over a hierarchy that can answer nothing. Measured: sidecar `{}` → `possibleViaUnknownDispatch:
      [app.Frontier.go]`; sidecar `{"@superclass":{}}` → `[]`. **FIXED candor-ts `7bbf73c`** — the `@`
      extension namespace and any non-array value are DROPPED, asymmetrically on purpose (a phantom can
      only NARROW this frontier; a dropped key only widens it back to the fallback a "cannot confirm"
      disclosure is allowed to sit at). **The array-valued spelling is java's CURRENT one, so a type check
      alone would have left the phantom in and read as a fix** — the second mutant is what showed that.
      The old row PINNED the bug (it required the coerced key to be kept) and is inverted, not deleted.
- [→] **INDEXED at THE QUEUE §2.** FOUR-WAY RULING WANTED: `hasHier` gates on EMPTINESS, java gates on ABSENCE.** ts
      `query-core.mjs` and rust `callers.rs:121` both read `Object.keys(h).length > 0` / the equivalent,
      so a present-but-EMPTY sidecar takes the over-listing fallback; candor-java's `Query.java:672`
      gates on absence and takes the PRECISE path over an empty map, which NARROWS the frontier. Three
      engines, two answers, same input, and no PART pins it. Deliberately NOT aligned unilaterally
      (`63bbe87`'s precedent). ts's new rows pin only "metadata-only == empty", which stays correct under
      either ruling; nothing there asserts "empty == absent".
- [x] **java `Loader.java:203` — `entryPackage`'s slash fallback takes the last `/` in the whole hash**,
      which for java's own hash form lands inside the method DESCRIPTOR, so entry-level coverage registers
      a garbage package name. **DONE — candor-java `47e2721`**, and the review's "harmless-looking"
      caveat was the right question to ask: the two directions came out opposite.
      - It could never FABRICATE coverage. A parse that runs into the descriptor necessarily keeps the
        `(` that opens it, and no JVM package name can contain one, so the bogus string matched nothing
        in `depCoveredPkgs` — inert, and now asserted inert.
      - The cost is the registration that did NOT happen. `depChainedPkgs` is conjunct 3 of the half-1
        unanswerable-key rung, so a chained report with no envelope package field left an INVOKEINTERFACE
        into an unnameable dep implementation reading as a confident purity claim:
        `deny Fs Unknown[dispatch]` **0 → 1 violation**, against a single-tree control that is 1 in both
        arms. A silent under-report, not a cosmetic parse bug.
      - **Every dep-report fixture in candor-java's suite predating the fix used `()V` or `(I)V`** — no
        reference type, no descriptor slash — which is exactly why they all passed. Worth checking in the
        other engines' fixtures for the same shape of blind spot.
      - A/B 7 chained real jar pairs: 0 delta, because every candor-java report carries `packages` and the
        fallback is redundant there. **A zero-delta arm is a claim about the experiment first** (item 8),
        so the same pairs were re-run with the envelope package field STRIPPED — the legacy/foreign shape
        the fallback exists for — and the mechanism fires: httpclient sheds 966 false `invisible` markers
        and 320 entries, each package traced to real entries in httpcore's own report. Still 0 effect
        gains and 0 losses.
- [x] **rust `deps.rs:307` — a stale report's `Unknown` now arrives tagged `callback:…`**, classifying as
      `indirect`, where the other three leave it `unresolved`. Rust is the four-way outlier, and the class
      the stale Unknown used to carry has been replaced by a fabricated one. This is the fail-closed
      fallback rust's own sweep agent wrote. Also java `ReasonClass.java:77`.
      **DONE — candor-rust `f2309a5`**, both sites (the staleness downgrade AND the reasonless-Unknown
      fallback in `apply_dep_fn`). The generalisation is worth keeping: **`callback:` is not a residual
      bucket.** §4 ⟨0.7⟩ defines it as an unresolved higher-order / owner-less INVOCATION — a claim about
      code — and §6.2 already names the residual, `unresolved`, reached by ABSENCE. Reaching for a
      canonical kind to "fail closed" is how a fabricated class gets written.
      - Measured chained on pgman/ebman/candor-rust: **0 effect gains, 0 losses, entry count +0, Unknown
        count +0**; 18 of 367 Unknown-bearing fns move class — 15 `indirect`→`unresolved`, 3
        `{dispatch,indirect}`→`{dispatch}` (swift's documented "a class the chained arm has and the
        single-tree control does not", live on real code).
      - **rust's own writer invariant is what forced the fabrication.** `scan_one`'s `debug_assert`
        ("`direct` carries Unknown ⇒ `unknownWhy` non-empty") makes the boundary case name one of the four
        §4 kinds, and NONE of them projects to `unresolved`. §4's own definition of a source — a unit
        "whose own body has the unresolvable call" — exempts a chained consumer, so the assertion was too
        broad, not the fix. **Any engine with an equivalent assertion has the same trap.**
      - rust deliberately did NOT copy ts's `stale-dep:` / swift's `dep-stale:`: PART 10 makes an
        off-vocabulary kind a HARD divergence. **Those two engines are one fixture away from failing their
        own conformance part** — worth checking, not checked here.
      - Found on the way: rust had NO staleness disclosure on ANY channel (ts and swift both print one);
        added on stderr.
- [ ] **OPENED BY THAT FIX — rust is the only engine with no transitive-why resolution.** java
      (`depTransitiveWhy`) and ts (`resolveInheritedWhy`) both walk the dependency's own `calls` edges to
      recover the class of an Unknown the dep unit only INHERITED (⟨0.6⟩ makes `unknownWhy` direct-only, so
      a dep's exported function publishes `inferred:['Unknown']` with no reason whenever the hole is one
      hop further in). rust leaves those at the honest `unresolved`. Its report already carries `calls`, so
      this needs **no format rung** — it is determination replacing disclosure, and it is the reach the
      fabricated tag was groping for. 15 fns on the three-project corpus are waiting for it.
- [x] **rust `deps.rs:377` — a package chained BOTH fresh and stale resolves as untrusted**; java, ts and
      swift all resolve the same input the other way (fresh wins). Four engines, two answers, same input.
      **REFUSED, with the counterfactual measured — candor-rust `63bbe87`.** Aligning rust costs a silent
      under-report. Coverage is the claim that an absent entry is a purity claim (§2 rule 3); rust's index
      DROPS a key two dep functions share rather than picking, so a fresh+stale collision withdraws the
      answer entirely. With `untrusted` cleared (the ts/swift shape, one line) the fixture's consumer fn
      does not merely lose a hedge — **it disappears from the report**, and an `Exec` the fresh report
      names reads as a confident purity claim. java and ts can afford fresh-wins because their entry-level
      conflict keeps an answer (java `crossDeps.put` last-wins, ts merges into a Set); rust's cannot. SPEC
      §2.1 is silent on the conflict and no PART pins it, so this wants a **four-way ruling**, not a
      unilateral edit. Pinned by a two-direction fixture carrying flip instructions.
      - Not theoretical: two reports naming one package is the ordinary Cargo shape (semver-major
        duplication) — **7 of 167 dep reports in candor-rust, 9 of 259 in pgman, 30 of 378 in ebman**.
- [x] **CHECKED IN SWIFT, 2026-07-27, and the answer is NO on the first half — so the false all-clear
      does not arise on the staleness axis.** `Deps.swift`'s `insert` is TRUST-AWARE (`ca5feb0`): a
      fresh/stale collision keeps the TRUSTED entry rather than withdrawing the key, which is exactly
      what java's last-wins and ts's Set-merge buy, and it is why rust's refusal is rust-specific. Two
      residuals fell out of the check and are FIXED: the identical-entry exemption had been ported to the
      trusted arm only (candor-swift `cbed5df`), and the same complete-wins reading rust refused WAS
      landed on the COMPLETENESS axis, where swift's index does withdraw (both fresh, both trusted) —
      measured at a positive purity claim and reversed in `756a8f0`. See the third-review section at the
      top. ORIGINAL: **swift drops the colliding key exactly as rust does
      (`Deps.swift` `insert`) AND resolves coverage fresh-wins** — the two halves that together produce the
      false all-clear measured above. Not checked in swift (another repo, another measurement); the
      fixture to reproduce is in candor-rust `tests.rs`
      `a_package_chained_both_fresh_and_stale_keeps_its_blind_spot_disclosure`.

### The one I would look at hardest
- [x] **rust `scan.rs:622` — the cached parser-abort replay is gated on content hash + decl-index hash,
      but the abort is NOT a function of those two.** `4f7b704` established that the abort depends on how
      much each rayon worker happened to parse, so a ONE-OFF abort is latched into the cache and replayed
      forever. This is the fix for MY cache-poisoning defect, and it may have replaced one latch with
      another — the direction is different (a spurious `unanalyzed` + a gate that will not go green, rather
      than a false all-clear) but the shape is identical. Also `:618`.
      **CONFIRMED AND DONE — candor-rust `35466f0`.** A cached abort is now a marker that the FnInfos were
      never derived, not an answer to replay: the entry is dropped at the one place `cached_fninfos` is
      populated, so the reuse gate misses it, the round-2 re-parse picks it up as ordinary stale FnInfos,
      and the file either aborts again (disclosing by the same cold path, byte for byte) or produces the
      answer it always owed. The write-back takes the marker only from THIS run, so an abort cannot outlive
      the run that observed it.
      - **The latch also broke the documented `--incremental` contract** ("produces a BYTE-IDENTICAL report
        to a full scan"), silently, in a mode nobody re-runs from cold.
      - Measured by injecting the fault into a REAL crate's real file (reqwest 0.12.28 `src/cookie.rs`),
        injection removed for runs 2–3: pre latches forever at 361 entries + 1 `unanalyzed`; post recovers
        **22 entries, 0 losses, 0 changed effect sets, Unknown delta 0**, `analyzed` 946→969, and is
        byte-identical to the full scan. Inert on pgman/ebman/candor-rust and **196 crates.io crates**
        (full + cold + warm, both arms, 0 differ).
      - The old test's `warm2` arm — injection removed, disclosure expected anyway — was the assertion that
        PINNED the latch (standing-bar item 7g, again). It survives inverted in
        `a_cached_abort_is_re_attempted_rather_than_latched`; the still-aborting arm keeps the original
        defect's requirement and is now named for it.
      - The generalisation: **`--incremental` reuse is licensed by "the input is unchanged", and an abort is
        not a function of the input.** Any per-file cache that persists an OUTCOME rather than a DERIVATION
        has this shape; ask what the outcome actually depends on before choosing the cache key.

### Closed already — both mine
- [x] **conformance PART 22 could not regress two of the four defects its own header cites** — `unknownWhy`
      was neither compared nor producible by the fixture. Fixed `81e919e`; verified to catch via a java
      mutant (`java -> DIVERGE (surface dropped by the join: unknownWhy[...])`). Rust could not demonstrate
      it because its own fail-closed writer assertion aborts the run first — a stronger guarantee than the row.
- [x] **`release-preflight` check [4] silently covered four of five components** — no `grabver` row for
      candor-java. Legitimate (java's build id is GENERATED from the git hash, so it cannot lag) but unsaid.
      Fixed `f6cc184`: the row now prints, naming itself out of scope.

## OPEN — the THIRD review (2026-07-27 evening): 10 confirmed, 1 fixed, 9 in flight

Third review of this work in one day. **9, then 10, then 10 — and in all three, EVERY confirmed defect was
a guard written during the wave under review.** Not one has been a fresh mechanism. That is now a measured
property of this work rather than an impression, and it is the argument for reviewing each wave rather than
trusting a green suite: all thirty had clean A/Bs and passing suites.

### CLOSED — mine, and it invalidated a recommendation I had just written
- [x] **`ENTRY-COLLISION-DECISION.md` — my claim about java's `!isEmpty()` guard was FALSE.** I wrote that
      it makes java "unsound only in choosing between two effectful claims — a precision loss, never a
      purity claim". **`{Unknown}` is non-empty.** The §2.1 staleness downgrade produces exactly that, so a
      STALE report's Unknown overwrites a TRUSTED report's concrete effects. Verified in BOTH file orders:
      trusted `Fs` + stale report → consumer reads `['Unknown']`, and **`deny Fs` goes exit 1 → exit 0**.
      Corrected in `a7a6147`, with the wrong paragraph left visible: **this rule has now been described
      three times and been wrong twice** (plain last-wins → last-non-empty-wins → last-non-empty-wins-except-
      Unknown-counts). A rule nobody can state correctly on three attempts is not one a policy gate should
      depend on, which strengthens the union recommendation rather than weakening it.

### Cardinal sins and gate flips — in flight
- [x] **FIXED candor-ts `7ba3776`** — ts `scan.mjs:504` — `--workspace` deleted a stale cached dep report AFTER the fixpoint rounds and
      never re-runs them, so a sibling that scanned successfully has ALREADY chained the report being
      deleted and its own cache keeps that answer. The stale content survives inside a downstream report
      after the file it came from is gone. swift's equivalent fix does a second `runRounds()` for exactly
      this reason (`43a0eaa`).
- [x] **FIXED candor-swift `497e117`** — swift `main.swift:468` — `sweepStale` deleted a HEALTHY sibling's freshly-written report: it skips
      deps that succeeded, not files THIS RUN produced. Two path deps deriving one report name, one fails,
      the other's output is deleted — and deleted AGAIN after the retry rewrites it. Second round of this
      class after `b4f6cbc` deleted user-placed reports.
- [x] **FIXED candor-swift `756a8f0`, INVERTED so incompleteness wins** — swift `Deps.swift:424` — `incompletePkgs.subtract(coveredPkgs)` restored FULL coverage as soon as
      any report claims the package complete, cancelling a second report's hedge over a region it could not
      read. Complete-wins is the reading rust REFUSED twice (`63bbe87`, `dbab8be`): **two reports covering
      one package do not cover the same SOURCE.**
- [x] **rust `deps.rs:135`** — the reasonless-Unknown class reaches only a `debug_assert`, never
      `reason_class_direct`. §6.2's `unresolved` fallback is per-FUNCTION and fires only on an absent or
      empty class set, so **any other reason on the same function swallows it** — precisely where a gate
      needs it. **CONFIRMED AND FIXED — candor-rust `558342f`.**
      - Reproduced at gate level first, bracketed by both single-call controls, and the sharpest statement
        of it is a MONOTONICITY failure: `one(){dep::mute();}` exits 1 under `deny Unknown[unresolved]`,
        `one(){dep::murky();}` exits 0 (correctly, it is classified), and
        `one(){dep::murky(); dep::mute();}` exits **0**. **Adding a call REMOVED a class.** The
        pre-existing fixture could not see it — its consumer calls ONE dep function, so the class set was
        empty and the fallback answered; it still PASSES under the mutant.
      - The fix CONTRIBUTES `unresolved` into `reason_class_direct` for every `unknown_via_dep` caller,
        which then propagates like any other class. **No token is invented**: it writes a §6.2 CLASS, not
        a §4 kind, into a gate-side map — `unknownWhy` and the report are untouched, and byte-identical
        reports on every A/B arm prove it.
      - **The gate moves and the analysis does not.** Reports byte-identical on candor-rust, pgman and
        ebman under four policies; 0 effect gains, 0 losses, 0 entry delta, 0 Unknown delta.
        `deny Unknown[unresolved]` violations: candor-rust **8 → 26**, ebman **7 → 29**, pgman 0 → 0,
        with 0 lost anywhere and `deny Unknown` / `[dispatch]` / `[indirect]` counts unchanged — every
        class change ADDS `unresolved` to an existing set.
      - Per item 8 the precondition was instrumented, and pgman's zero is a fact about pgman: the join
        fires on 8 functions in candor-scan, 13 in ebman, **0 in pgman**. Traced to source —
        `lang::format_const_prefix_arg` calls `m.parse_body_with(…)` and syn 2.0.117's
        `mac::Macro::parse_body_with` publishes `inferred:['Unknown']` with no `unknownWhy`, because ⟨0.6⟩
        makes the field direct-only. **2643 of candor-rust's 6773 Unknown-bearing dep entries are
        reasonless (39%)** — the ordinary shape, not a corner.
      - §6.2's by-absence fallback is KEPT and re-documented as a NET rather than a route: the writer's §4
        invariant is a `debug_assert`, so in release a future reasonless path still fails closed there.
        Its mutant fails a named test, so it is not the item-8c "costs nothing" case.
- [ ] **THE RESIDUAL THAT FIX LEAVES IS THE FORMAT'S, AND IT IS FOUR-WAY.** A report cannot say
      "`Unknown`, and one of them has no reason" *alongside* a reason the function does have: §4's kind
      vocabulary has no member for it (that is why `f2309a5` had to remove an invented one) and §6.2's
      "no recorded reason ⇒ `unresolved`" is stated per FUNCTION and keyed on ABSENCE, so it does not
      compose. Consequence: a SECOND-hop consumer chaining the fixed report re-derives `dispatch` alone
      and the same gate goes quiet one boundary further out. rust fixed its own in-process gate and
      **cannot fix the wire half without a token PART 10 makes a hard divergence** — which would be the
      fabrication `f2309a5` removed. java, ts and swift have the same hole (swift's `dep:` pointer is the
      nearest thing to an answer and is off-vocabulary). **This wants a §4/§6.2 rung**, e.g. an explicit
      per-function reason-CLASS surface, or a §6.2 rule that a reason set is a LOWER bound. Not a
      unilateral edit.

### The wire-format break, both halves from one java commit
- [x] **FIXED candor-rust `e3e99aa` (mine)** — THE THIRD READER — `candor-query::load_hierarchy` deserializes the sidecar as a strict
      `BTreeMap<String, Vec<String>>`, so java `bb8459a`'s new `"@superclass"` OBJECT makes the WHOLE file
      fail to parse and be silently discarded. **That is the identical failure the same commit fixed in the
      SECOND reader** (`Query.loadHierarchy` threw, swallowed it, and dropped the whole hierarchy with 540
      tests green). Introduced by the fix for it, in another language.
- [x] **FIXED candor-java `7acd64a`; the key is now a flat ARRAY (`403f24b`)** — `@superclass` was written UNCONDITIONALLY, so an empty sidecar becomes `{"@superclass":{}}` and
      candor-ts's `callersFrontier` — which gates on `Object.keys(hierarchy).length > 0` — flips from its
      safe over-listing fallback to the precise path over an EMPTY hierarchy. A metadata key silently
      narrows another engine's frontier.
      **Worth deciding with it:** SPEC §2.2 states the non-array skip as a requirement on READERS, which
      obliges every deployed reader to have been updated — which is exactly what did not happen, twice. A
      WRITER-side constraint would have made both defects impossible.

### Partial ports and a comment that lies
- [x] **FIXED candor-swift `cbed5df`** — swift `Deps.swift:212` — the identical-entry exemption (rust `6f2210c`) was added only to the
      TRUSTED arm; two IDENTICAL entries from two STALE reports still withdraw the key, losing the §2.1
      `Unknown` downgrade the stale arm exists to produce.
- [x] **FIXED candor-swift `fce24ec`, one parse and one transform, both the writer's** — swift `main.swift:447` — `ownedReportFile` parsed the manifest name anchored AFTER `Package(`;
      the WRITER at `:304` is UNANCHORED and takes the FIRST `name:` in the file. The comment claims "the
      same three sources the writer uses, in the same order". It is not, and the sweep can therefore
      compute a different name than the writer did.
- [x] **FIXED candor-swift `ba91a27`; the rename control then found FOUR MORE doors (`7646c3d`)** — swift `CallCollector.swift:1465` — the TYPED enum-payload binder calls `shadowName` only, missing
      `protoTyped`/`arrayElem`/`opaqueElem`/`dictElem`/`tupleElem`, so a payload shadowing a protocol-typed
      parameter still dispatches over the protocol's conformers. **`NameKeyedStateTests` cannot see it** —
      it derives the map SET and checks classifications, not whether each BINDER SITE honours them. Its
      author named that limit; this is the limit biting.

### Found by re-checking two rust guards from this wave that the review probed and did not confirm
Both were sent as "establish whether this is reachable, or record precisely why it cannot happen". One was
reachable and is fixed; the other's claim held with one word wrong. Neither would have been found by a
suite or an A/B — the first needs a producer the corpus does not contain, the second is a claim about the
source rather than about any run.
- [x] **rust `deps.rs` — the identical-entry exemption (`6f2210c`) compared SERIALISATIONS, not claims.
      REACHABLE, and FIXED in the type — candor-rust `811bbf3`.** Derived `PartialEq` on a `Vec` is
      element-wise and order-sensitive, so two entries stating one claim in a different order (or one of
      them restating a host) read as a DISAGREEMENT, the key was withdrawn, and under ⟨0.21⟩ the
      consumer's silence is a purity claim — **the same cardinal sin `6f2210c` closed, surviving for any
      producer that orders a vector differently.** All eight `DepFn` fields are `BTreeSet`s now: the
      argument is that `apply_dep_fn` folds every one into a set, so the join is invariant under order and
      multiplicity and set-equality is not a RELAXATION of never-guess but its exact statement. A type
      cannot be forgotten by the next field; a hand-written per-field comparison can.
      - **The corpus is a fabrication control here, not evidence, and that was measured before the edit:**
        over 850 real dep reports, 72 490 key collisions — 65 685 restatements, 6 805 genuine
        disagreements, and **ZERO set-equal-but-not-vec-equal**; zero entries carry an unsorted or a
        duplicate-bearing field. §2.1 only admits a report claiming this binary's version and this writer
        emits every field from a `BTreeSet` — but `scan-{CARGO_PKG_VERSION}` is a CRATE VERSION, not a
        build id, so a different build of the same version, a hand-written report (the suite writes them)
        or a future non-set field all pass.
      - **So the arm was ARMED**, each dep tree re-chained with a second copy of every report whose
        multi-element arrays are REVERSED. Pre-fix: **pgman loses 7 entries and changes 13** —
        `app::persist_draft_to` and `app::persist_history_to` lose `['Clock','Fs']` and DISAPPEAR;
        **ebman changes 47** (live `invisible` disclosures withdrawn); candor-rust loses 1. Post-fix all
        three are identical to the unarmed baseline, and unarmed the two binaries are byte-identical.
      - The opposite direction is safe by construction: `DepFn` IS what a consumer inherits, `apply_dep_fn`
        is its only reader, and equality compares all eight fields.
- [x] **rust — `dbab8be`'s own "four anchors, one `cover`, one consumer" claim: TRUE in substance, wrong in
      one word, and now a TEST — candor-rust `8a9618e`.** Enumerated rather than re-read: the three set
      writes appear exactly once each in the whole workspace and all sit inside `cover`; `untrusted` and
      `incomplete_pkgs` are CONSUMED at exactly one place (the κ-ledger `covered` predicate), with every
      downstream surface reading the one `coverage_ledger`/`global_blind` derived from it. **The comment
      said "read nowhere else in the engine", which is false** — `load_dep_reports` reads both again for
      its two stderr disclosures. `coverage_has_exactly_one_anchor_and_exactly_one_consumer` now derives
      the writes and the consumers out of the source at test time (the `NameKeyedStateTests` shape), with
      four mutants and four named failures including a vacuity floor. **Whoever ports the incompleteness
      door to another engine: the anchor count is per-engine — java's was 2, swift's 3, rust's 1 — and
      "all N funnel through one closure" is a claim a fifth site added later silently breaks.**

## CARRIED FORWARD — the vein's own rows are all closed; these are what it uncovered

**The vein has ZERO open rows.** Every mechanism family that made a `deny` gate pass code it should fail is
closed four-way and pinned by conformance PARTs 18–22. What follows is not the vein: it is the set of things
found *while* closing it that were deliberately deferred with a reason. They were buried in prose in the
sections below, which is the failure this document exists to prevent — **a residual recorded only in a
narrative is a residual nobody will find.** Hoisted here 2026-07-27.

Each was refused or deferred with a measurement, not left undone. None is a known silent under-report.

### Needs its own measurement before anyone touches it
- [x] **java — a CONCRETE dep method overridden effectfully — MEASURED, and the obvious fix REFUSED with
      the numbers (candor-java `61cfcc4`).** It answers only for its own body across the boundary, where
      in-scan the same site is charged the CHA union. The row is real: over 11 real dep jars, 12 242
      concrete overridable members, 861 (7.0%) with any override inside the dependency, **76** whose
      override carries an effect the base does not — 35 of them under a key with NO entry, i.e. a live
      purity claim (`AbstractResource.getFile()` `[]` vs `[Fs,Log,Unknown]` over 7 implementers,
      `AppenderBase.start()` `[]` vs `[Clock,Fs,Net,Unknown]` over 8).
      - **The problem is the KEY, not a missing bound, and that is the transferable part.** Publishing the
        union under the base's own key answers for every site that forms it — and `super.m()` forms exactly
        the same key, while INVOKESPECIAL by JVM semantics runs the base body and can never dispatch to an
        override. Consumer A/B, 7 chained real jar pairs / 10 914 analysed functions: 22 functions change,
        0 losses, and **12 are charged through a direct `invokespecial`** (`ResponseEntityProxy.getContent`
        → `HttpEntityWrapper.getContent`, `WithLayoutListAppender.start` → `AppenderBase.start`, four
        logback converters through a project superclass), with 6 more transitive callers of those.
      - **Why the ABSTRACT arm was free of this is structural, not quantitative**: an abstract member's key
        is unanswerable AND unreachable by `super` — you cannot `super`-call an abstract method — so no
        INVOKESPECIAL can land on it. Both properties fail for a concrete member. **Any engine tempted to
        widen its own abstract-arm equivalent should ask what its `super` spelling does to the same key.**
      - **The correct shape was PRICED rather than asserted**: the same union under a key only a virtual
        site can form (`owner.<dispatch>name+desc`, joined on INVOKEVIRTUAL/INVOKEINTERFACE) changes **4**
        functions on the same pairs, 0 losses — spring's `DefaultListableBeanFactory.getPriority` `[]` →
        `[Fs,Log,Unknown]` through `OrderComparator.getPriority`, which `AnnotationAwareOrderComparator`
        really does override (the row's one traced real reach), its caller, and a `BasicFuture.get` pair
        that is the same over-approximation the in-scan CHA already makes. That needs a NEW resolution path
        in the consumer (`333cf10` needed none) plus a synthetic entry shape no other engine produces or
        consumes — a **four-way question**, for 4 functions in 10 914. Left open on those terms.
      - Pinned by two SEPARATE tests: the row with flip instructions against a single-tree control that IS
        charged the union, and `aSuperCallToAConcreteDepMethodIsNeverChargedItsOverrides`, which must never
        be made to pass by closing the row. Separate because inside the first it would sit behind the
        flipping assertion and could never be observed (item 8c). Both fail under the naive mutant.
- [D] **DECIDED — see THE QUEUE §5. Not open work.** swift — the erasure gate does not reach the LOCAL-protocol dispatch arm. REFUSED with both
      treatments priced (`020add4`): suppress costs 5 losses and 7 entries REMOVED; disclose costs 9
      concrete effects → hedge. The deciding argument is recorded in the code — for an IMPORTED protocol
      the in-scan conformers are an arbitrary subset of the candidates, for a LOCAL one they BOUND them.
      Re-open only with an A/B, since this arm is what R28/R39 and the whole element-dispatch family run on.
- [x] **java — the dep-sidecar hierarchy half — DONE, candor-java `bb8459a`, and it found a defect in its
      own compatibility argument.** `writeHierarchy` wrote a sorted `TreeSet` with no superclass marker, so
      a chain lying ENTIRELY inside a dependency stayed depth-ordered and `9f8e71c`'s JLS rule could not be
      applied to it. It now also writes `"@superclass"`, a sibling key whose value is an OBJECT; its
      PRESENCE licenses the split, ABSENCE keeps exactly the depth-ordered answer that shipped, and neither
      side needs a version gate. Fixture: the whole chain in `lib` (`Half9 extends Mid9 implements Trace9`,
      `Mid9 extends Root9`) goes `['Env']` → `['Fs']` chained, against a single-tree control that is `Fs`
      in both arms. `9f8e71c`'s own fixtures put the branching class in the APP, where a project ClassNode
      states the split — **ask separately what an engine does when every link is in the dependency.**
      - **THE SECOND FIXTURE COULD NOT FAIL AT FIRST, and mutating it is what showed that.** The competing
        interface used `System.out.println`, which produces no report entry at all, so the "unmarked list
        read as ALL INTERFACES" mutant changed nothing. With an `Exec` body instead it fails, named.
        Item 8c, caught before the commit rather than by the next review.
      - **The compatibility argument was true of ONE reader and untrue of the other.** `Query.loadHierarchy`
        called `getAsJsonArray()` unconditionally — it THROWS on an object, its own `catch { return null; }`
        swallowed it, and the WHOLE hierarchy was discarded, dropping the `callers --include-unknown`
        frontier to a bare simple-name match. 539 tests were green through it. **SPEC §2.2 now states the
        skip as a requirement on READERS**, because the failure it prevents is silent. candor-ts's
        `loadHierarchy` already normalises non-arrays; rust/swift do not read a java sidecar. Worth a
        30-second check in any engine that reads a sidecar it did not write.
      - Measured, 7 chained real jar pairs: **125 of 2 702 dependency-hierarchy resolution orders change**
        (4.6%; logback 65, httpclient 23, httpclient5 21, spring-beans 16), 2 214 dep types load a known
        split, and the report delta is **0 gains / 0 losses / identical entry and Unknown counts**, all 10
        dep reports byte-identical apart from their build id. The fixture is the evidence; per item 8 the
        clean corpus is the fabrication control, and the precondition was instrumented to say so.

### Unblocked, deliberately unlanded — each narrows a gate
- [x] **LANDED, candor-ts `5ba301c`** — 1,234 malformed emissions over 15 repos, all from the interface-CHA arm; effect sets and entry counts identical, 695 functions leave `dispatch` / 573 enter `indirect`, monotone. **The narrowing is named, not buried: `deny Unknown[dispatch]` flips exit 1 → 0 on 4 of 14 targets — and in each of those EVERY dispatch reason in the report was malformed (6/6, 56/56, 18/18, 10/10).** ORIGINAL: the malformed `dispatch:type.member` reclassification. The blocker is RESOLVED: all four
      engines were RUN on owner-less function values (rust `callback:unresolved call`, java
      `callback:…Function.apply`, swift `callback:fn` — all class `indirect`), SPEC §4's dividing line is
      explicit, and PART 10 already asserts every `dispatch:` carries `owner.member`. **candor-ts is the
      outlier and the change moves it toward both the family and the spec, needing no spec change.** Not
      landed because it narrows a gate (16 functions move `dispatch`→`indirect`) and wants its own A/B plus
      a second-direction fixture. Note `826571c` makes the malformed string travel across the boundary, so
      the blast radius is wider than the 68 measured.
      **LANDED candor-ts `5ba301c`, with both the A/B and the second-direction fixture — and the blast
      radius really was wider: 1,234 malformed emissions over a 15-repo corpus, 695 functions leaving
      class `dispatch`.**
      - **What the malformed strings were, instrumented rather than guessed**: every one of the 1,234
        came from the interface-CHA arm and none from the other three emission sites. Two shapes, both
        function VALUES — a named type whose content is a CALL SIGNATURE (`interface UnaryFunction { (x:
        T): R }`, `type PatchFn = …`: owner, no member; the corpus names read as function types because
        they are — `ErrorCallback`, `SendCallback`, `MessageHandler`, `PatchFn`), and a member of an
        ANONYMOUS type literal (member, no owner; 251 had neither). The `callback:` detail is
        best-effort, so the nameable half is KEPT — `callback:src.a.UnaryFunction`, `callback:run` —
        rather than thrown away along with the classification.
      - **A/B, 14 scannable targets, both arms hashed.** Effect sets identical on every function of
        every target, entry counts identical: this changes a string, not an analysis. Class movement is
        MONOTONE — 695 leave `dispatch`, 573 enter `indirect`, 0 gain `dispatch`, 0 lose `indirect`.
        `deny Unknown` unmoved everywhere; `deny Unknown[indirect]` was already firing everywhere it now
        additionally covers. Nothing goes silent.
      - **The narrowing, with its number:** `deny Unknown[dispatch]` flips exit 1 → 0 on four of the
        fourteen (conf, got, ky, p-queue). In each, EVERY `dispatch:` reason in the report was malformed
        — 6/6, 56/56, 18/18, 10/10 — so the rule was firing entirely on the classification this change
        says is wrong. On the other ten it is unmoved.
      - **Both directions fixtured**, and mutating the rule out is what proves it: always-dispatch fails
        4 named tests, always-callback fails 15 — including every pre-existing `dispatch:` assertion in
        the suite, which is the real second-direction evidence.
      - **For the rust row below this is a precedent, not a guard** (cf. "a cross-engine precedent tells
        you an approach CAN work"). What made it safe here is that the reclassified strings named
        NOTHING, so no `deny Unknown[dispatch]` could have been relying on a real owner.
        `ambiguous:same-name local defs` DOES name something, so that row still needs its own answer.
- [x] **rust — `ambiguous:same-name local defs` is outside the closed §4 vocabulary**, emitted **757 times
      across 253 crates**. PART 10 misses it because the harness's fixtures never produce that kind.
      Renaming is not free: `callback:` moves the class Dispatch→Indirect and WEAKENS
      `deny Unknown[dispatch]`. Wants its own measurement and probably the spec's MIGRATION mechanism.
      **REFUSED, with the counterfactual measured — candor-rust `4817b71`; PART 10 repaired,
      candor-spec `90ad1f6`.**
      - **What it IS in §4 terms: none of the four kinds can express it.** NOT `dispatch:` — that kind
        needs a resolvable owner type and its detail is NORMATIVE `<owner>.<member>`; a BARE FREE call has
        no owner, so the detail cannot be formed and PART 10 rejects a dot-free `dispatch:`. It is also
        not dispatch at all: exactly one function runs and rustc resolves it statically, so what failed is
        the ANALYSER's name resolution, not the program's. NOT `callback:` — an unresolved HIGHER-ORDER
        invocation over a function VALUE, and not the residual bucket (item 9d). Not `native:`/`reflect:`.
        **SPEC §6.2's reason-class table already NAMES `ambiguous*` and rules its class `dispatch`**, so
        the spec blesses the prefix in one section and omits it from the closed set in another.
        Reconciling that is a SPEC rung, not an engine edit.
      - **The number that refuses the rename.** One line in `ReasonClass::classify` moves `ambiguous*` to
        `indirect`; both binaries kept by content hash. `deny E Unknown[dispatch]` then goes from firing
        on **58 of 200 crates.io crates to 0 of 200**, and exit 1 → exit 0 on pgman, ebman and
        candor-rust. **That is a deletion, not a narrowing** — every OTHER `dispatch:` this engine emits
        is `dispatch:untyped cross-package receiver`, 20 in a 1062-report census, all needing a chained
        dependency to exist at all. ts's `5ba301c` was safe because its reclassified strings named
        NOTHING; the precedent says the shape CAN work, not that this one is safe.
      - **The weight, so nobody re-opens it as a corner case:** censused over 1062 reports (200 crates.io
        crates + 855 dep reports + 3 projects), `ambiguous:` is **8710 of 19607** `unknownWhy` entries
        across 220 packages — `callback:` 9421, `native:` 1456, `dispatch:` 20. The filed 757/253 was a
        large undercount. The shape is cfg-gated alternative definitions (rustix 1989, syn 1851), which a
        syntactic scan cannot resolve because it does not evaluate `cfg`.
      - **PART 10's blindness was the real defect and is now closed.** The row read only the SHARED
        fixture, so it pinned the vocabulary OF THE SHARED FIXTURE. It now also scans a purpose-built
        crate that produces the kind, tolerates-and-WARNS it beside java's `task-handoff`/`indy` (with
        the header spelling out that java's are remnants and rust's is an inexpressible state), and
        carries its own vacuity floor: if the fixture stops producing the kind the row DIVERGES rather
        than passing quietly. Two mutants, two named failures.

### NEW, found while measuring that refusal — both filed with numbers, neither fixed
- [→] **FOLDED into THE QUEUE §1, symptom 3.** rust AND swift — every `dispatch:` they emit at the half-1 site is `dispatch:untyped
      cross-package receiver`: the CANONICAL kind with a MALFORMED normative detail.** §4 makes
      `<owner>.<member>` the one conformance-compared detail and PART 10 DIVERGES on a dot-free one; it
      does not fire only because PART 10's fixture never chains a dependency (PART 21, which does, prints
      the string in both engines' rows). Worse, §4's own dividing line says an **untyped receiver is
      `callback:`** — so the kind is wrong too. 20 emissions in a 1062-report rust census.
      **Not fixed here for two reasons**: swift emits the identical string, so this wants a four-way
      ruling like `63bbe87`, not a unilateral edit; and landing it alone would turn the shared suite red
      the moment PART 10 gets a chaining fixture. Note the cost is not obviously zero — moving it to
      `callback:` takes the class Dispatch→Indirect, and in rust `deny Unknown[dispatch]` would then rest
      entirely on `ambiguous:`.
- [ ] **rust — the `ambiguous:` arm's candidate set includes METHODS, which a bare free call can never
      resolve to.** Instrumented over the 200-crate breadth: **156 of 930 emissions have ≤1 free-fn
      candidate and 48 have NONE**. The clearest is `drop`: a bare `drop(x)` is the PRELUDE fn, charged
      `Unknown` 36 times because the crate happens to have ≥2 `Drop::drop` impls. Over-DISCLOSURE, not
      the cardinal sin — but it is ~17% of this engine's co-dominant kind, and it is what makes
      `deny Unknown[dispatch]` fire on 29% of crates.io. Narrowing the candidate set to free-fn defs is
      exactly the shape item 0 warns about, so it wants its own A/B in both directions.

### Precision gaps, disclosed and not silent
- [x] **FIXED candor-ts `1960979`** — ts — the BY-REFERENCE HOF arm had the `.bind` arm's hole, but DISCLOSED.** Found while fixing
      `b66b69a` and deliberately not fixed with it. That arm keeps the positive `!hofInvokesArg(…)`
      early return, so a DEP function passed BY REFERENCE at a position a loosely typed dep HOF does not
      declare loses its concrete effect. Reduced to a fixture rather than asserted — `forEach(xs: any[],
      fn: any)` against a well-typed `some(xs, fn: (x) => boolean)`, same argument, same position:
      `depRefLoosePos1 -> ['Unknown'] (callback:fn, callback:param#1)` vs
      `depRefTypedPos1 -> ['Fs','Unknown']`.
      **A precision loss, not the cardinal sin** — the Unknown and its reason are still published, so
      `deny Unknown` and `deny Fs Unknown` still bite where a bare `deny Fs` no longer would. That is
      why it did not ride the `.bind` fix: `.bind(…)` IS a function by construction, so widening that
      arm was free, while this one takes a BARE IDENTIFIER and the callability guard does not save it (a
      seed object typed `any` passes `argIsCallable` — the `path.reduce(fn, obj)` shape guard (1) exists
      for). Widening it is a fabrication risk with no measurement behind it; it wants its own A/B.
- [ ] **swift — dep reports name SwiftPM PACKAGES while imports name MODULES** (`swift-case-paths` vs
      `CasePaths`), so on those targets nothing is covered in EITHER arm. Found by instrumenting why a fix
      showed no delta rather than assuming it was inert. Pre-existing and separate from the vein.
      - **REPRODUCED WITH ITS CONTROL, 2026-07-27, and it is total rather than partial.** Two packages: a
        dep whose manifest is `name: "swift-dep-kit"` with one target `DepKit` exporting an `Fs` method,
        and an app that does `import DepKit` and calls it. **Chained and unchained are BYTE-IDENTICAL** —
        `useDep` reads `invisible: ['DepKit']`, coverage reports `uncovered: [DepKit]`, and the dep's `Fs`
        never arrives. Rename the manifest to `name: "DepKit"`, change nothing else, and the same chained
        run gives `useDep -> ['Fs']` with the coverage gap closed. So on any package whose SwiftPM name
        differs from its module name — the majority of the ecosystem's `swift-*` repos — `CANDOR_DEPS`
        and `--workspace` are **inert**, not merely lossy.
      - **THE CAUSE IS ONE NAME IN TWO ROLES.** `main.swift:302` sets `pkgName` from the manifest's first
        `name:` (the PACKAGE), and that name is both the envelope `package` and the prefix of every
        entry's `hash` (`<pkg>#<qual>`), which is what `Deps.load` keys the index on. Every consumer-side
        lookup is `deps.lookup("\(m)#…")` for `m` in `fileImports[file]` — an **import**, i.e. a MODULE.
        The two halves have never been the same string unless the package happens to be single-module.
      - **THE OBVIOUS HALF-FIX IS A CARDINAL SIN, and it is worth writing down because it is one line.**
        `Deps.load` already reads a plural `packages: [...]` (the JVM envelope shape) and registers every
        entry of it as COVERED. Emitting `packages: [pkgName] + internalModules` would make
        `isChained("DepKit")` true — and the entry keys would still be `swift-dep-kit#…`, so every lookup
        would still miss. The consumer would then have **coverage without entries**: the `invisible`
        disclosure withdrawn and nothing put in its place, i.e. silence read as purity. The coverage half
        cannot land without the key half.
      - **SO THE FIX IS THE KEY HALF: the first component of the join key must be the name a consumer
        WRITES IN `import`.** For Swift that is the module, not the SwiftPM package — the same way java's
        is the JVM package and ts's is the npm package name you import. `Driver.analyze` already derives
        the module set exactly (`internalModules`: `Sources/<Target>/` subdirectories plus the manifest's
        `.target/.executableTarget/.macro` names, deliberately NOT `.product` — a distinction the κ ledger
        already paid for), and each entry's own `loc` names the file it came from, so the per-entry module
        is derivable without a new index. **Not attempted here**: it moves the report's primary join key,
        so it is baseline-invalidating, needs the four-way conformance chaining parts re-run (their
        fixtures use package == module and would not notice), and wants its own A/B — the honest scope is
        its own session, not a tail-end of this one.
- [ ] **swift — a nested-type factory does not resolve IN-SCAN either**, so that row has no single-tree
      control and the chained arm is now strictly BETTER than the unsplit one — candor-java `9ae68f7`'s
      smell, one repo over. Documented on the test rather than asserted, because pinning it would encode
      the gap as a requirement.
- [ ] **swift — `returnsIdx` is bare-name keyed package-wide**, a pre-existing residual doing one conjunct
      earlier what `7a4f977` fixed. Pinned as a test asserting TODAY's behaviour with instructions to flip it.
- [x] **FIXED candor-ts `95d0b8b` + `29cd992`, which found TWO further defects in the fix itself** — ts — `.candor/dep-inits/` and `.candor/deps/` were never cleared**, so a package whose rescan throws
      is served from the PREVIOUS run's file while the code comment claims it "is skipped".
      ABSENT-BY-ACCIDENT: the incompleteness fix (`21277eb`) removed the sharpest edge, but nothing prevents
      the shape returning.
- [x] **rust — the QUIET half of the span-crossing-a-thread defect is unmeasured.** `4f7b704` closed the
      loud tail (the panic; 60 unseen crates now clean). The quiet form resolves a span against the WRONG
      file instead of aborting, and the precondition was measured at **72.4% of 88,927 macro re-parses**.
      No known wrong output — and no measurement either.
      **CONFINED — candor-rust `fc71bc9`. Row closed with evidence rather than a fix.**
      - **Structural, by enumeration of every span read and what its result feeds:** `fn_locs` is the ONLY
        one whose result is PUBLISHED (`loc`), and it runs INSIDE the parse closure on the worker that owns
        the map; the four moved-token re-parses are re-stamped to `call_site()` = `(0,0)`, the dummy file
        every thread's map is seeded with; `macro_template_blocks` re-parses from a STRING (registers a
        file on the current thread); the six `parse_nested_meta` sites read spans only for errors, all
        discarded with `let _ =`, and a cfg verdict is a function of paths and literals, not spans.
      - **The oracle**: open the file each `loc` names and require it to exist, be long enough, and declare
        that function. **24 008 of 24 008** non-synthetic locs over 200 crates.io crates pass. CALIBRATED
        before believed — permuting each loc onto a different file of its own crate makes it flag **20 001
        of 23 657 (84.5%)**, 5 507 as short-file. Its first run reported 2 523 wrong lines that were all
        DOC COMMENTS (the item span starts there); that was the instrument, not the engine.
      - 200 crates × four rayon thread counts (**800 scans**) byte-identical: no published field varies
        with how much each worker parsed, which is the quiet form's whole precondition.
      - **The seeded control settles the shape of the risk**: `fn_locs` moved out of the parse closure
        PANICS on 57 of 60 crates (the 3 survivors are single-file). An output-bearing span read on the
        wrong thread is loud by nature — there is no silent-wrong-loc regime behind the panics.
      - **A near-miss worth keeping**: the first differential compared the SEEDED binary at t=1 vs t=16 and
        reported "0 differing" — because both arms had panicked to EMPTY files. A diff over two equally
        absent outputs is not a measurement, and it pointed the flattering way (item 7d).
      - Pinned by `every_published_loc_names_the_source_that_declares_it`, a hermetic 24-module fixture
        running the same oracle; the seeded mutant fails it. Honest limit stated on the test: on a
        single-core machine rayon may run every parse on the calling thread, and the property then holds
        trivially — the test loses its power there, not its correctness.

### Release-shape, needs Tom
- [ ] **candor-ts is at build 0.23.2, the family at 0.23.1.** Legitimate — its module-unit wire key moved
      and §2.1's staleness gate keys on the per-engine build id. `release-preflight` check [4] was relaxed
      to report rather than fail (`candor` `b5e2cb0`), and its `WANT_VER` arm still catches a genuine lag
      exactly. The release set is a decision, not a defect.

## Standing bar 7o — A CLEAN TREE IS NOT A COMPLETION SIGNAL. I broke 7f myself (2026-07-28)

The ts round-1 agent committed both briefed items and left `git status` clean. I read that as finished and
dispatched a second agent into the same repo. It was **a lull between its briefed work and a follow-on it
had correctly decided to do** (extending the present-but-unparseable rule to the chained-dep route — work I
would have asked for). Two writers interleaved in `scan.mjs` for about twenty minutes.

**The completion signal is the agent's REPORT, not the tree.** A clean tree means "no edit is half-written
right now", which is true between every pair of commits. 7f says one writer per repo; this is how the rule
gets broken by someone who knows it — by substituting a cheap observable for the real one, under time
pressure, having just been asked to move fast.

No loss: the second agent detected the collision itself, committed nothing, and preserved separated patches
(`scratchpad/collision/`) before standing down. I told the first agent to stage explicitly by path and never
`git add -A`, since either side could otherwise sweep the other's half-finished work into its commit. **But
the recovery being clean is not evidence the risk was small** — it is evidence the agent handled it well.

**The mitigation is to make the signal cheap and correct, not to be more careful**: if a repo must be
handed over fast, tell the outgoing agent to report before starting anything unbriefed, or dispatch the
follow-on to the SAME agent via SendMessage, which cannot collide with itself.

### It also produced the round's sharpest cross-engine find, which R9 could not see

Before standing down that agent measured the ⟨0.24⟩ policy-vocabulary disclosure: **rust `vocabulary`, java
`policyVocabulary`, swift `configSources: [path]`** — three names, and swift's array drops the alias names
entirely. `coverage.modules` recurring on the very next field.

**And R9 was blind to it by construction.** I chose one uniformly-minimal fixture so no optional block was
present, which stops the row flagging legitimate per-situation differences — and thereby made it blind to
every optional block, which is exactly where divergence lives. Fixed (`f06c762`): the row is a LIST OF
SITUATIONS, and the rule is **every optional block needs an arm that makes it PRESENT**. Shape ruled in
`b4e9155` — `policyVocabulary: {config, aliases}`, object not array, because naming the source without the
content leaves the reader knowing they were affected and not how.

Same shape of error twice in one session, mine both times: **a check whose fixture cannot reach the
condition it is checking for.**

## Standing bar 7p — A CORPUS IS A SHAPE, AND THE SHAPE DECIDES WHICH DEFECTS IT CAN SHOW YOU

candor-java's `unknownClasses` defect was found on the `Unknown[…]` axis and missed on the `Net[…]` axis for
one reason: **candor-java's own report has ZERO Net-bearing functions.** The engines are routinely measured
against their own source, and a self-scan is not a neutral corpus — it is a corpus with a shape, and an axis
the shape cannot exercise reads clean whatever the code does.

**This is the per-shape vacuity floor again, one level out.** That floor exists because a conformance row
whose fixture stopped triggering looks exactly like a passing one; a corpus that cannot exercise an axis
looks exactly like an engine that handles it. Same failure, different instrument.

**So: before measuring an axis, assert the corpus can EXERCISE it.** Count the entries that carry the thing
under test — Net-bearing functions for a `Net[…]` filter, `Unknown`-bearing for a reason class — and say the
number out loud in the report. `0` is not a passing measurement, it is the absence of one. java did exactly
this once it noticed, moving to httpclient5-5.6.1 (2395 fns, 393 Net-bearing) rather than trusting a
self-scan that could not answer.

**Corollary for A/B evidence generally:** a zero-loss column over a corpus that never reaches the changed
code is not evidence of safety. State what the corpus exercises, not just what it did not lose.

## Standing bar 7s — DISQUALIFY THE INSTRUMENT BEFORE REPORTING ITS NUMBER (2026-08-02)

Sent to un-skip candor-swift's Linux tests, the investigation found the mechanism (`Bundle(for:) ===
Bundle.main` is false on macOS and TRUE on Linux, so `.deletingLastPathComponent()` lands one directory too
high) and then a genuine shipped defect: **`Process.waitUntilExit()` blocks forever on
swift-corelibs-foundation once the child has already exited** — pipes at EOF, child reaped, `isRunning`
still true. 10/10 hangs on aarch64 AND on emulated x86_64; `terminationHandler` + semaphore 0/10, 30/30
correct. The shipped engine carried the same pattern, so **`candor-swift --workspace` hung forever on
Linux** in 0.24.0 (`RC=124`, killed at 60s, nothing written; macOS exited 0 with a 630-byte report).
Correctly classified as an AVAILABILITY defect, NOT the cardinal sin — it hangs rather than emitting a
false all-clear, so no silent under-report was ever produced. Do not inflate an availability bug into a
soundness one; the distinction is the whole vocabulary.

**But the durable lesson is the number that was NOT reported.** Asked for the new Linux skip count, the
answer was *"not measurable in this environment"*, backed by a control: `PolicyTests|SurfaceTests|FixTests`
— 50 tests containing **zero `Process()` references** — hung 2 of 3 runs in Docker-on-macOS, while those
same tests have been green on real Linux CI for months. That control disqualifies the instrument, so every
hang-rate datapoint taken with it was retracted too, including ones that had already been reported.

**The rule: when a control shows your instrument produces the failure you are measuring, you have no
measurement — and the honest output is the disqualification, not a hedged number.** A figure from a
disqualified instrument is worse than no figure, because it will be quoted later without its caveat. Same
family as 7q and the oracle work: calibrate the instrument, never a copy of it.

**Two supporting habits worth keeping:** a falsified theory was KEPT for its real but smaller merit (closing
149 leaked pipe descriptors) with the commit stating plainly that it did **not** fix the hang it was written
for — a fix that does not do what you hoped is still a fix, provided the message says so. And the engine
change was isolated to a single `Sources/`-only commit so it reverts independently of the three test-side
ones.

**Correction to the record, and it is a clean instance of 7q:** commit `26d5a7f` cites *"Linux, `swift test
--filter NetLocatorProvenanceProcessTests`: 41 tests, 0 failures, 0 unexpected"* as evidence the Linux leg
was healthy. The harness could not locate the binary on Linux, so **all 41 were `XCTSkip`s** — zero failures
out of zero executed rows. I wrote that green number into a commit message as proof of the very thing it
could not measure, in the same session as the bar warning against exactly this.

## Standing bar 7r — A CLAIM RECORDED IN ONE PLACE, NEVER CHECKED AGAINST THE ARTIFACT IT NAMES (2026-08-01)

The 0.24 release produced this same defect FOUR times in one hour, in four different components, and it is
the exact error class the analyzers exist to catch:

- **`release-preflight [3]` passed green over a 404.** It verified that `jbang-catalog.json` *said*
  `v0.24.0`. The release that URL points at did not exist, so `candor update` and every jbang user got a
  404 for the JVM engine. **A pin naming a URL is not the URL existing.**
- **The `candor-agents` pin.** I changed a CORRECT `v0.23.1` to an older `v0.23.0` on my claim the tag was
  never created, and announced it in the commit message as a repair. `gh release list` showed the tag and
  its Release, both. I had run `git ls-remote --tags | grep` with a pattern that mangled its own input —
  **a bad grep reports absence identically to real absence**, which is absence of evidence rendered as
  evidence of absence.
- **`candor-rust`'s GitHub release existed while crates.io sat at 0.23.1.** The repo looked shipped. Rust
  users install from crates.io. **A release on the wrong surface reads as done.**
- **Two CHANGELOGs had no entry for the version being cut**, the umbrella's stale by three rungs while
  `ENGINE_PIN` moved beneath it. Checks 2 and 3 EXCLUDE changelogs from the stale-string sweep — correctly,
  since a changelog is a history — but excluding it from the negative check left no positive one. Now
  gated by preflight **[5]**, which was verified able to FAIL before being trusted.

**The rule: resolve the artifact, never just the string.** `curl -o /dev/null -w '%{http_code}'` the
download URLs; `gh release view --json assets`; `npm view`; `crates.io/api/v1`. A green check over a string
that names a missing thing is worse than no check, because it converts an absence into a confident claim —
which is the cardinal sin, wearing release-tooling clothes.

**Corollary: the tooling existed and I bypassed it.** `bin/release.sh` builds the jar and cuts every
release from each repo's CHANGELOG in one pass; `bin/release-verify.sh` checks the published surfaces
afterwards. Hand-driving the steps lost three of them — including tagging candor-spec, the repo the rung is
authored IN and therefore the one you never think to tag. `release-verify` found every miss, but only
because it was eventually run. **A release is done when the verifier passes, not when the tags are pushed.**

**Also worth keeping: three of my own verification probes cried wolf today** — `npm run build` on a package
with no build script, `ERR_MODULE_NOT_FOUND` from an unpacked tarball with no deps installed, and reading
`j.spec` at the wrong nesting depth. None were real defects. That trade is correct — a probe that cries
wolf costs a minute, a probe that stays quiet over a real defect is the cardinal sin — but it means an
ad-hoc probe is currently LESS reliable than the artifact it is inspecting, and should not be trusted over
it without a second reading.

## CLOSED 2026-08-02 — candor-swift's Linux CI leg skipped 474 of its 559 tests (found 2026-08-01)

**RESULT: 474 skips → 4, all four NAMED, 0 failures, on CI's own ubuntu-24.04 x86_64 leg.** 470 tests ran on
Linux for the first time and every one passed. The remaining four are three macOS-only `XCTExpectFailure`
ratchets and one arm that is untestable as root (root reads through `0000` permissions). Linux completes in
27.3s against the new 15-minute hang bound.

**The most informative result is the absence:** a Linux/macOS divergence in effect reporting would have been
the cardinal sin, invisible for as long as these rows never ran. It did not materialise — and that is now
MEASURED rather than assumed, which it had never been. Getting there required fixing a real shipped defect
first: `Process.waitUntilExit()` blocks forever on swift-corelibs-foundation after the child exits, which
made `candor-swift --workspace` hang forever on Linux in 0.24.0 (availability, not soundness — see 7s).

Original entry follows.

### (original entry) — candor-swift's Linux CI leg skips 411 of its 496 tests (found 2026-08-01, NOT release-gating)

From the last green Linux run, verbatim:

    Executed 496 tests, with 411 tests skipped, 0 failures, in 4.761 seconds

`ProcessHarness.binaryURL` derives the binary from `Bundle(for:).bundleURL.deletingLastPathComponent()`,
which on Linux resolves to `.build/<triple>/` rather than `.build/<triple>/debug/`. The harness does not
find the binary, so **every process-based suite `XCTSkip`s**. What remains is a compile gate plus ~85 unit
tests. The leg reports a four-digit-looking test count while exercising about a fifth of the behaviour, and
it does it in 4.7 seconds — a duration that should itself have been the tell.

**This is why bar 7q's first defect could only surface as a BUILD failure**: the Linux leg has almost no
behavioural surface left to fail on, so a compile error is very nearly the only signal it can still emit.
The two findings are the same fact seen from opposite ends.

Deliberately NOT fixed in the same commit as the CI unblock, and that scoping was right: un-skipping 411
tests at once can surface real Linux-only failures, and a release-blocking CI fix is the worst possible
place to discover them. Do it as its own change, after 0.24 ships, and expect it to find things.

**The general form, worth more than the instance:** a skip that is CONDITIONAL ON THE ENVIRONMENT reports as
a pass at the summary line. `0 failures` and `411 skipped` are the same green tick to anyone reading the
dashboard. Every arm of this project that reports a count should be asked how many of that count actually
RAN — this is the coverage-envelope discipline (κ travels with the report) applied to our own CI, which has
never had it.

## Standing bar 7q — TWO CI BREAKS IN ONE DAY, BOTH MINE, BOTH INVISIBLE WHERE I VERIFIED (2026-08-01)

Both were conventions I introduced *and* verified — on the only platform and population I happened to be
standing in.

**`XCTExpectFailure` is Darwin-XCTest only.** I chose it over `XCTSkip` for the three pinned module-const
tests precisely because it is a BOTH-WAYS ratchet: it fails if the defect is ever fixed without removing the
marker. Sound reasoning, and swift-corelibs-xctest on Linux does not ship the API — so candor-swift's Linux
CI leg died at *compile*: `cannot find 'XCTExpectFailure' in scope` ×3, then `error: fatalError`. **My local
`swift test` was green with 559 passing and could not have seen it**, and my first diagnosis (the
type-checker timeouts in `Policy.swift` the editor had been reporting all session) was a red herring the
agent correctly ignored in favour of reading the actual log. Fixed with `#if canImport(Darwin)` — the
ratchet stays live where it can run and the Linux leg SAYS WHY it skips.

**R10's majority is population-dependent.** Its known divergences are waived PER ENGINE (java and rust, the
two that must move), which is only correct at full population. CI has two legs by design — ubuntu with three
engines, macos-15 with four. On the three-engine leg no majority forms and **ts is flagged for being on the
shape we consider CORRECT.** candor-spec CI had been red since the day R10 landed — three runs — and I never
looked, because I ran the suite locally where swift is present. Now VACUOUS below full population; and
fixing that exposed a second defect one layer down, where the vacuous cells reported their waivers STALE, so
the leg that COULD NOT EVALUATE the row would have deleted the waivers the leg that can still needs. **A
waiver is retired by a PASS, never by an absence of measurement.**

**The shared shape:** *local green is a claim about local.* Both defects were in the verification apparatus
rather than the analysers, both passed everything I ran, and both were caught only by a machine with a
different toolchain or a different engine set. This is the same lesson as bar 7p (a corpus is a shape) one
level out: **a test environment is a shape too, and the shape decides which failures it can show you.**

**Corollary, and it cost three red runs:** after adding or changing a conformance row, READ THE CI RUN it
lands in. The suite passing on the machine that wrote the row is the weakest evidence available about it.

## Standing bar 7o(b) — the INVERSE of 7o: do not edit a repo an agent is already in

7o records dispatching a second agent into a repo whose first agent had not finished. The mirror happened
today: I bumped `candor-swift`'s `engineVersion` **after** dispatching an agent into that repo, leaving my
uncommitted edit in its working tree. Benign here — one line, a different file, and the agent was told to
stage by path — but a `git add -A` would have merged a release version bump into a CI-fix commit, so a
revert of the fix would have silently reverted the bump. **The rule is symmetric: one writer per repo means
the coordinator too.**

## THE STANDING BAR — applies to every item, no exceptions

0. **A FABRICATION FIX IS WHERE UNDER-REPORTS GET INTRODUCED. Measured: four defects in five fixes.**
   After a code review found ten defects in one day's boundary work, every one of the five fixes written in
   response was re-checked in the OTHER direction. Four were wrong, two of them cardinal sins:

   | fix | what the other-direction check found |
   |---|---|
   | rust `trait_quals` tombstone | dropped a genuine cross-crate reach — **cardinal sin** |
   | java hand-off filter | an ALLOWLIST of SAM names, four already missing |
   | ts callback-position guard | dropped `then`'s second callback — **cardinal sin** |
   | swift erasure split | clean |
   | rust provenance scoping | clean; exposed a pre-existing gap underneath |

   The shape is always the same: you narrow an over-approximation to kill a fabrication, and narrow past the
   real reaches. **The fixture that proves you closed the fabrication is structurally incapable of noticing
   the reach you closed with it** — it contains only the pure receiver, only the uninvoked argument, only the
   one call. Write the second fixture before you believe the first.
   - Narrow with a **denylist** of proven-safe cases, never an allowlist of permitted ones (the java fix
     reached for an allowlist while fixing an over-charge, and had already forgotten four entries).
   - Prefer **disambiguating** to **dropping**. Tombstoning a colliding key is safe against fabrication and
     silently costs every genuine use of it; the information to tell the cases apart usually exists one
     level down (there, per-receiver instead of per-leaf).
   - **THIRD INSTANCE, 2026-07-27, and the sharpening is worse than the rule.** The `.bind` gate
     (candor-ts `4958a6d` → fixed `b66b69a`) shipped with a FIRST fixture that could not fail either. It
     asserted `!includes("Fs")` on a *dependency* ref in the receiver slot — an arm whose only possible
     output is an `Unknown` disclosure — so the over-charge it was written for (`['Unknown']` before the
     guard, pure after) was invisible to its own assertion, and mutating the guard out left the suite
     766/0. So the rule is not only "the first fixture cannot see the reach you closed": **check that the
     first fixture can see the fabrication.** Mutate the guard out and name the failing test *before*
     writing the second fixture — if nothing fails, you have not yet tested anything at all.
0b. **A guess that is right for the wrong reason hides the gap underneath it.** rust's leaf map was
   last-wins, which — by accident — stored the crate a shadowing local needed, so a whole missing feature
   (locals never recorded their own qualification) looked like working code. Removing the guess did not
   create that gap, it revealed it. Expect a "regression" when you stop guessing, and check whether it is
   one before treating it as one.
1. **The cardinal sin is a SILENT UNDER-REPORT.** Never trade it for its mirror. A fix that FABRICATES an
   effect on a genuinely pure function is worse than the miss it closes. If an A/B shows gains you cannot
   trace to a real reach, **revert**. Three swift fixes were reverted this way before a fourth landed clean;
   that is the expected rhythm, not a failure.
2. **A/B on real code, every change.** Scan several real codebases before and after and diff per-function
   effect sets. Report gains AND losses. Zero losses required. Every gain traced to source, not assumed.
   Watch the report ENTRY COUNT too — a spurious extra entry means an unbounded edge (this caught a bad
   drop-glue marker).
3. **Two-tree fixture per fix**, with the single-tree control, and the `deny` gate going from exit 0 back to
   exit 1. The control is what proves it is a *boundary* defect and not a general limitation.
4. **Regression test per fix**, engine's own suite green, four-way conformance green.
5. **Verify before claiming.** Several sweep findings did not reproduce (see the corrections in the vein
   doc). Reduce every mechanism story to a fixture before acting on it.
6. **Honest beats silent.** If a mechanism cannot be resolved soundly, making it disclose `Unknown` is a
   valid and valuable fix.
7. **Delete the output before you measure a control.** A crashed or stale run leaves the previous report on
   disk, and reading it back silently reports the wrong arm's result. This has now bitten three times in this
   vein — twice via a stale `*-all.jar` picked by `ls … | head -1`, once via a pre-fix ts worktree with no
   `node_modules`. Every time, the fabricated datapoint pointed the *flattering* way.
7b. **KEEP BOTH ARMS' BINARIES, not just their outputs — a measurement you cannot re-run is not a
   measurement.** The dep-hierarchy A/B reported httpclient BYTE-IDENTICAL on its first pass. Three later
   runs — two of them of a *different* variant of the same change — all report it DIFFERS, deterministically,
   with seven traceable Net gains. The first result was wrong and the cause is now unrecoverable, because
   the post-arm jar had been rebuilt over by the time the contradiction surfaced. Deleting the OUTPUT before
   a control (item 7) is not enough: name each arm's binary by its content hash, keep it for the life of the
   measurement, and when two runs disagree re-run BOTH from their preserved binaries before believing
   either. Note which way the bad datapoint pointed — again the flattering way (a real recovery, hidden).
7c. **TWO WAYS I RAN THE WRONG BINARY IN ONE HOUR, both silent, both mine.** (a) `cargo build … | head -3`
   SIGPIPEs the build: cargo dies, the *old* binary stays on disk, and every "verification" after it tested
   code that was never compiled. Four consecutive results came from a binary 70 minutes stale. Never pipe a
   BUILD through `head`; check the artifact's mtime, not the command's exit. (b) `git checkout <file>` to
   undo a one-line MUTANT reverted the whole file — including forty lines of uncommitted work in it. Copy
   the file aside and restore from the copy; `git checkout` cannot tell your mutant from your work.
7d. **BEFORE YOU REPORT A DEFECT, ASK WHETHER YOUR TEST METHOD PRODUCED IT.** Twice in one day I built a
   measurement that showed a fix was broken, and twice the measurement was the broken thing. (a) I pointed
   `--deps` at a hand-built old-format report while `--dep-inits` was on — which RE-SCANS the packages on
   disk and chains its own fresh reports, so the report I wrote never participated; I read the fix working
   as a compatibility regression. (b) I removed a fault injected by an ENV VAR and expected a cached abort
   to clear — but the env var is deliberately outside the cache key, so replay was the designed behaviour;
   the real clearing guard fires on a CONTENT change, and does. **A false defect costs the same review time
   as a real one and burns credibility with whoever fixed it.** The check is cheap: name the thing your
   arms actually differ in, and confirm it is the thing you think you are varying.
7e. **CHECK THAT THE THING READING YOUR OUTPUT CAN NAME WHAT IT READ.** A mutation round reported the
   WRONG tests failing, in a pattern that looked exactly like a real inversion, and two rounds went into
   theorising about the engine before the CLI contradicted the harness. Cause: the results parser matched
   `<testcase name="X" …>(.*?)</testcase>` against JUnit XML — and a PASSING testcase is SELF-CLOSING, so
   the regex ran from one test's name to a LATER failing test's close tag and attributed the failure to the
   wrong test. Item 7 says delete the output before you measure a control; its sibling is that **a parser
   which silently mis-attributes is worse than one that errors, because its output is plausible.** Prefer
   the tool's own reporting to a regex over its artifacts, and when a mutation result surprises you,
   confirm it from a second channel before theorising about the engine.
8b. **INSTRUMENTING AN ANALYSER CHANGES WHAT IT ANALYSES — including itself.** A probe added to swift's
   hot receiver-resolution path read an env var, and candor's own self-scan then charged Env+Fs to 26 of
   its OWN functions. The probe was correct and its finding was correct; shipping it would have written
   the measurement into the product's report. Instrument freely, but treat the probe as an ARM to be
   removed, and never leave one in a path the engine walks over itself. (Cf. item 7: this is the same
   family as reading a stale artifact — the tool and the thing measured are the same object.)
7f. **CONCURRENT AGENTS SHARE THE BINARIES, THE HARNESS AND THE SCRATCHPAD — A MUTATION TEST IS A
   DESTRUCTIVE WRITE TO SOMEBODY ELSE'S MEASUREMENT.** Four per-engine agents ran at once, every one of
   them instructed (correctly) to verify guards by mutating them out and re-running the shared four-way
   conformance suite. I did the same thing myself to prove PART 22 catches a dropped surface: deleted the
   `paths` fold from rust's `apply_dep_fn`, rebuilt the shared release binary, ran conformance, restored.
   The rust agent's conformance run landed inside that window and reported a divergence — `cmds` travelled,
   `paths` did not — **which it could not reproduce in 129 subsequent runs and honestly flagged as
   unexplained.** It was mine. Two further collisions the same hour: one agent clobbered another's
   scratchpad directory, and a candor-java jar rebuilt mid-run aborted a conformance pass.
   - **A divergence on an engine that is not yours is not your finding** until it reproduces.
   - Keep mutation windows short; restore before touching the shared suite.
   - The orchestrator owns this: fanning out per-repo work is safe, but per-repo agents that all run ONE
     shared differential harness are not isolated, and saying "one agent per repo, no file conflicts" is
     true of the source and false of the build outputs.
   - **RECURRENCE 2026-07-27, and this time the rule I broke was "one agent per repo" itself.** I
     dispatched a follow-up into candor-rust for the frontier literal pins while a *second* agent was
     already live in candor-rust on the sidecar false-disclosure. Both edited `crates/candor-query/tests/
     cli.rs`. The frontier agent noticed only because the **test count jumped 53 → 55 between two of its
     own mutation runs**, and it then saw 3 bin unit tests red that had been 23/23 green at its baseline —
     the other agent's in-flight state, not a regression it had caused.
     It handled the collision better than I set it up: reversed its own mutant **immediately** on
     discovery (a concurrent `cargo test` would otherwise have shown failures from a deliberately-broken
     join and sent the other agent chasing a ghost), then reconstructed a my-changes-only `cli.rs`,
     verified by diff that it equalled the working file minus exactly the other block, and staged it via
     `git hash-object -w` + `git update-index --cacheinfo` so its commit carried only its own version
     while the working tree kept the other's. **A plain `git add -A` from either side would have swallowed
     the other's work** — which is the same failure as [[feedback-evidence-dirs-are-sacred]], one repo over.
     Outcome was clean (`276838c` + `97c1a2b`, working tree clean, `cargo test --workspace` 14 legs exit 0),
     but that was the agent's recovery, not my orchestration.
     - **THE RULE, tightened: one WRITER per repo at a time, not one agent per task.** Two tasks that are
       independent in subject matter are not independent if they touch the same repo. Sequence them, or
       give the second a worktree.
   - **7l. I RETIRED A WAIVER ON A MEASUREMENT OF AN UNCOMMITTED TREE — the seventh instance, and mine,
     one hour after writing the rule down for the fifth time.** The rust agent reported candor-ts's
     `empty_zero` waiver stale, having seen PART 26 print `ts SEPARATED`. I deleted it. But candor-ts's HEAD
     was still its `gate --report` commit and its empty-report fix was **eleven dirty files** — the agent
     had measured ts's WORKING TREE mid-flight and **said so plainly** (*"ts appears to have landed in
     parallel"*), and I read a hedged observation as a landed fact. My own re-run showed ts
     INDISTINGUISHABLE. Restored.
     - **A waiver is retired when THE RATCHET reports it stale against a COMMITTED tree.** Nothing else is
       evidence — not another engine's run, not a working-tree measurement, and not a report that says
       "appears to".
     - The hedge word is the tell. Every one of today's seven collisions was reported honestly by the agent
       that hit it; **the losses came from the reader, not the reporter.** An agent writing "appears to",
       "seems", or "in parallel" is telling you it did not verify — and that qualifier is exactly what gets
       dropped when the finding is acted on second-hand.

   - **7k. `cargo test … --lib <filter>` ON A GATE THAT LIVES IN THE `--bin` TARGET SELECTS ZERO TESTS AND
     PRINTS `ok`.** During the floor bump I verified rust's doc drift gate with
     `cargo test -p candor-scan --lib repo_docs`, read *"test result: ok. 0 passed"*, and banked it as
     green. **It selected nothing.** The gate lives on the BIN target; the correct invocation is
     `--bin candor-scan repo_docs`, which runs 1 test. I ran a verification that verified nothing and did
     not notice, because a zero-test run and a passing run print the same word.
     **`0 passed` IS NOT A PASS. Read the COUNT, not the verdict** — and when filtering by name, confirm the
     filter matched something before believing the result. This is the same shape as 7j one level up: there
     I treated a grep's zero as evidence of absence; here I treated a test runner's zero as evidence of
     correctness. Both are the instrument reporting that it did nothing, in the vocabulary of success.
     Related, from the same sweep: rust's doc gate greps the PROSE form `spec 0.24` and **structurally
     cannot see the JSON form** (`"spec": "0.23"`), so it never had a chance at the README line it exists
     to guard — a gate can be correctly invoked, pass honestly, and still be blind to the shape it is
     pointed at.

   - **7j. A GREP THAT RETURNS ZERO MEANS "THE SURFACE IS ABSENT", NOT "THE OBLIGATION DOES NOT APPLY" —
     AND THE ZERO CAN BE THE DEFECT ITSELF.** Before sweeping the fifth component (candor-agents) for the
     ⟨0.24⟩ rung I grepped it and reported: `Unknown[` **0**, `reasonClass` **0**, `--class` **0**, and
     concluded *"my expectation is that TWO clauses bind here and the rest are genuinely N/A."* **Three of
     those zeros were live fail-open gates.**
     - `Unknown[` = 0 was not absence of the feature. The bracket **parsed as the rule's SCOPE**, so
       `deny Unknown[*]` named no known effect, the rule was **dropped**, and it exited **0** on a report
       where bare `deny Unknown` exits **1** — which the spec says are byte-identical. Same shape one rung
       down for `deny Net[unknown-host]`.
     - `reasonClass` = 0 and `--class` = 0 were *"both true and both misleading — absence of the surface,
       not absence of the obligation."*
     - Independently: **`Llm` was missing from all three hand-typed copies of §1's effect table**, so
       `deny Llm` named no known effect → rule dropped → **exit 0**; and `"candorEffects": ["Llm"]` was
       **voided as out-of-vocabulary — a FALSE disclosure calling a legitimate declaration a typo.**
     - And **`pure` fired on `Unknown`** here too — the PART 16 defect, in the one component no PART covers.
     **The rule: ask what the clause REQUIRES, then look for the requirement's absence — do not look for
     the feature's presence and infer exemption from its absence.** A component that never implemented a
     gate cannot fail it in a way grep can see. I came within one instruction of exempting a component from
     four clauses on the strength of four zeros, and the brief only survived because it said "establish
     which, with evidence" and "if a clause I called N/A actually applies, that is the most valuable thing
     you can report."

   - **7i. AN AGENT REPORTING "I CREATED X, DELETE IT" MAY BE WRONG ABOUT HAVING CREATED IT — CHECK THE
     TIMESTAMPS BEFORE ACTING ON A CLEANUP REQUEST.** An agent closed with *"`--deps` created
     `/Users/tom/git/pgman/.candor/deps/` (270 generated reports, untracked) … `rm -rf` when convenient"*.
     **268 of those 270 were from the PREVIOUS DAY.** The agent added two files to a directory that
     pre-dated it; the suggested `rm -rf` would have destroyed 268 pre-existing dependency reports — the
     same corpus THIS session measured the entry-collision decision against a few hours earlier.
     `git status` shows the whole directory as one untracked `??` entry, which is exactly what makes the
     mistake easy: an agent that generated *into* a directory cannot tell from `git status` that it did not
     generate *the* directory. Same class as [[feedback-evidence-dirs-are-sacred]], arriving as a helpful
     offer rather than as a careless command.
     - **Do not act on a cleanup suggestion without `stat`-ing the contents.** One `find -exec stat` split
       270 files into 268/2 and settled it in a second.
     - Nothing was deleted; the directory stands.

   - **7h. `cargo build --release` AT THE WORKSPACE ROOT BUILDS ONLY THE ROOT PACKAGE.** `candor-scan` is a
     separate workspace member, so a root-level build leaves its binary STALE and the first "verification"
     of a scan-side fix showed no change. `-p candor-scan` is required. Same class as the `| head` SIGPIPE
     trap (7c): a build command that silently does less than you asked, producing a measurement of the old
     code that looks like a measurement of the new.

   - **7g. A TEST CAN BE INERT BECAUSE OF STATIC INITIALISATION ORDER, and it will look green.** The java
     engine found a bug in its own new code — in `--json` mode a trailer line went to stdout and corrupted
     the verdict — **and its unit test passed against it.** `Candor.diagOut` is a `static` initialised to
     `System.out` at CLASS LOAD, so swapping `System.out` in the test left the stray write going to the
     real console, where the assertion could not see it. Caught only by piping the REAL CLI into a JSON
     parser. The engine's own note: *"the 'verify every new test can fail' rule is what surfaced that the
     test was inert."* Two rules follow — for any output-capture test, check whether the stream under test
     was captured into a static before your fixture swapped it; and for a verb whose contract is machine
     output, the acceptance test runs the shipped binary and PARSES the output, never a unit-level capture.

     - A test-count change you did not cause is the cheapest available collision detector. Nothing else
       reported this — the tree looked fine, both agents' work was correct, and the only signal was 53→55.
   - **RECURRENCE 3, same day, DIFFERENT resource: the shared SCRATCHPAD.** The java agent reported that
     *"another agent was writing into the shared session scratchpad and overwrote my first measurement's
     inputs mid-run"*. It moved to a private subdirectory and re-ran everything from scratch, so no
     reported number came from the clobbered run — but it caught that itself, and nothing in my briefs
     told it to. **Separately, the same hour, candor-java's `build/libs` was wiped for ~35 minutes by a
     concurrent `./gradlew clean`, mid-way through P1's four-way run.** P1 correctly refused to rebuild in
     someone else's tree (this very item) and re-ran once the jar returned.
     **THREE COLLISIONS IN ONE SESSION, on three different shared resources — the repo, the scratchpad, and
     another repo's build outputs — none of which the "one agent per repo" framing covers.** The honest
     statement of the rule:
     - **Every agent gets a PRIVATE scratchpad subdirectory**, named for its task. The session scratchpad
       is shared by default and that default is wrong for concurrent fan-out.
     - **`clean` targets are cross-repo hazards.** A build that wipes artefacts another agent's harness
       consumes is a destructive write outside its own repo, even though every file it touched was its own.
     - The detector in all three cases was an agent noticing an anomaly in its OWN numbers — a test count,
       a missing input, a stale jar. **Brief agents to treat an unexplained change in their own measurement
       as a collision hypothesis first**, not as a finding about candor. Every one of them did; that was
       their judgment, not my instruction, and it is now the instruction.
   - **AND OF candor-spec ITSELF, which is worse: `git add -A` there COMMITS ANOTHER AGENT'S IN-FLIGHT
     EDIT under your message.** 2026-07-27: the SPEC §2.2 + CHANGELOG halves of the java hierarchy-sidecar
     rung (`bb8459a`) were written into the working tree and swept, minutes later, into `272e423` — a
     commit about swift's `boundLocals` that says nothing about them. Nothing was lost and nothing
     conflicted, so no tool complained; the record is simply wrong, and the next person looking for why
     the sidecar grew an extension point will not find it in `git log`. In a repo more than one agent is
     editing, `git add <paths>` — never `-A` — and check `git status` for files you did not touch before
     committing. The queue and SPEC are the two files every agent writes to.
7g. **A TEST CAN PIN THE BUG. Ask what CHANNEL each suite can see.** java's `test/smoke.sh` asserted a
   coverage row containing a *permanently stale* version string — it had encoded shape 1 (a distrusted
   report still granting coverage) as a REQUIREMENT, so fixing the defect broke the suite that was
   supposed to protect it. Worse: `gradle test check` and the four-way conformance suite were green
   through all five preceding commits and **neither could see it**, because the assertion lives in
   stderr and those two legs read the report and the exit code. A green suite is evidence about the
   channels that suite reads. Enumerate them — report content, exit code, stderr, sidecars — and know
   which leg covers which, because a defect will sit in the channel nobody's assertions look at.
8c. **"UNTESTABLE" AND "NOT LOAD-BEARING" ARE DIFFERENT CLAIMS, AND A GUARD CAN BE ONE WITHOUT THE
   OTHER.** This queue filed swift's `typeSurface` exact-match guard as UNPROVEN, on the grounds that
   relaxing it to a suffix match failed no test. The engineer who landed the missing index key then
   measured the counterfactual instead of assuming it: with the third key mutated back OUT and the suffix
   mutant left IN, the CONSUMER rows go green again — a wrong answer simply misses, harmlessly — and only
   a producer-side assertion nobody had written still fails. So the guard was always OBSERVABLE in
   principle; what the key changed is that a wrong answer now **LANDS** instead of missing. Two distinct
   properties: *can this guard's absence be detected* and *does this guard's absence cost anything*. The
   row conflated them, and the fix is not to argue about which was meant but to state both — a guard that
   cannot be detected needs a test, a guard that costs nothing needs deleting, and they are not the same
   remedy.
9d. **A SOUNDNESS ASSERTION CAN FORCE A SOUNDNESS DEFECT.** rust's §4 writer carries a `debug_assert`
   demanding that any `Unknown` name one of the four §4 kinds. **No kind projects to `unresolved`** — so
   when a chained dep declared `Unknown` with NO reason, the assertion left no legal way to say "no
   reason", and the fix was to INVENT one (`callback:…`), which classifies `indirect` and made rust the
   four-way outlier on every `Unknown[class]` gate. The assertion was too broad: §4's own definition of a
   source ("its own body has the unresolvable call") exempts a chained CONSUMER, which is not a source.
   **An invariant that cannot express a legitimate state will be satisfied by fabricating an illegitimate
   one — and that reads as compliance.** Any engine with an equivalent assertion has the same trap.
   Corollary found with it: **`callback:` is NOT the residual bucket** several comments in this codebase
   call it. §4 defines it as an unresolved HIGHER-ORDER invocation; the residual class is reached by the
   ABSENCE of a reason, not by a token standing in for one.
1b. **A DISAPPEARING UNIT IS NOT AUTOMATICALLY A LOST REACH — CHECK WHY IT WAS AN ENTRY.** Item 1 says
   revert when an A/B shows losses you cannot trace, and that is right. But swift's `boundLocals` attempt
   was reverted on 405 "losses" that a later pass proved were mostly the fix WORKING. A unit is in the
   report iff it has EFFECTS **or** a DISCLOSURE. When the fabrication you are removing was the thing
   manufacturing the disclosure, the unit correctly stops being an entry — and it looks identical, in a
   diff, to a unit whose real reach you just dropped. **A withdrawn `invisible` is not a withdrawn reach.**
   The 13-line repro: an enum-payload binding landed in neither `vars` nor `boundLocals`, so a bare
   `help(ctx)` hit the fn-ref-as-argument rule, was emitted as an unqualified free call, resolved to
   nothing, set `resolved = false` — which is the Driver's ENTIRE test for "this unit reaches code the
   scan cannot see" — and fired a per-fn `invisible`. The unit's only reason to exist was that fabricated
   disclosure. So: before reverting on lost entries, check each one's effect set. An entry that leaves
   carrying no effects and only a disclosure is a candidate for a correct removal, not a loss.
8. **An A/B diff cannot show that a mechanism never fires, or fires on the wrong thing.** It shows what
   CHANGED. Two defects this vein produced had perfectly clean A/Bs: `typeSurface` was near-inert because
   the producer read module names as types, and swift's half-1 provenance conjunct was matching `max()`,
   `min()` and the engine's own local functions. Both were invisible in the output and obvious in the
   COUNTS. **Instrument the preconditions** — how often does the trigger hold, and on what? — and read the
   ratio, not just the diff. A trigger that fires 239 times on shapes you did not intend is not "bounded
   as designed", and a bound that admits nothing on a real modular crate is usually a keying bug.
   **Third instance, 2026-07-26, and this one was an ORDERING fact nobody would have guessed:** the arm
   testing "what if the dependency hierarchy widened the subtype index" came back byte-identical with zero
   cost — flattering, and wrong. `buildSubtypeIndex` runs BEFORE `loadCrossDeps` populates the dep
   hierarchy, so the one-line widening cannot fire at all as a one-liner. With the load hoisted so the arm
   is real, the same change costs **8 losses against 113 gains** — seven functions lose a disclosed
   `Unknown` and one loses a concrete `Net`. **A zero-delta arm is a claim about the EXPERIMENT before it
   is a claim about the change**: prove the mechanism fired before you report that it changed nothing.
9. **A comment that states a justification is an assertion, not a proof — and it will be believed.** Three
   of the ten defects a code review found in this vein were cases where the correct principle was written
   in a comment and the code beneath it did the opposite: a leaf-key join four paragraphs under "the trap
   this must not walk into"; "the parameter is gated to Runnable/Callable, so its reported surface is what
   the runtime invokes" (the gate constrains the TYPE, never which MEMBER runs); "cleared on any rebind by
   the clearBinding path below" where that path cleared four other maps and not this one. Each was
   confident, specific and wrong, and each survived self-review *because* the comment answered the question
   the code should have been asked. **Reduce the comment's claim to a fixture, or write it as an open
   question.**
9b. **"Additive" is a claim about the OTHER entries, and it does not cover the entry colliding with itself.**
   Adding a third key shape to the rust dep index (`{krate}#{full qual}`) is additive against every *other*
   entry — a ≥3-segment qual cannot collide with anyone's 1-segment leaf or 2-segment tail2. But for a 1- or
   2-segment qual the "new" key IS the string already pushed, and the index's never-guess rule drops a key
   two entries share. Without a dedup the entry collides with ITSELF and the key that worked before is
   REMOVED: a silent under-report manufactured by a change whose whole argument was that it removed nothing.
   Landing it alone, with a mutant test in both directions, is what caught it (`5feba18`). **An additive
   change still needs the second-direction check of item 0 — ask what the new thing collides with, including
   the old copy of itself.**
9c. **AN AUTOMATED FIXER WILL DELETE YOUR REASONING, AND THE DIFF LOOKS LIKE A CLEANUP.** `clippy --fix`
   rewrote a `match` into `.map` and removed with it a comment recording a SOUNDNESS argument — why an
   unpinnable local `fmt` is treated as pure rather than `Unknown`. The code was equivalent; the record of
   why it is allowed to be that way was not, and nothing in the diff said so. Item 9 says a comment is an
   assertion and will be believed; its converse is that a comment carrying the only written form of an
   argument is load-bearing, and a mechanical rewrite has no way to know. Read a `--fix` diff for deletions
   before you read it for changes.
10. Commit each fix separately, substantive message, trailers:
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` and the session `Claude-Session:` line.
   **Do not push without an explicit instruction.**

## The template that works

Emit the call shape the cross-package join **already understands**, rather than adding a resolution path.
The dependency's report almost always already holds the right answer under the right key — in 12 of 13 JVM
cases it did, and nothing looked for it. Two caveats learned the hard way:

- The emitted shape must be **distinguishable from a real call**, or it pollutes the κ ledger and the
  coverage envelope (`cr::<drop>::Type`, not `cr::Type::drop`).
- **Bound it at consumption**: join it and `continue`, so it can never reach local resolution or the
  classifier.

## A cross-engine precedent tells you an approach CAN work. It does not specify the guard.

R4 is the case study, and the mistake was mine. R4 sat blocked as *"a decision, not a patch"*; I unblocked it
by citing swift's `eae2de2`, which had shipped the same idea safely behind one carve-out, and I decided for
**resolution 1 (provenance)** on that basis. Measured, resolution 1 *as I specified it* produced **32 fresh
Unknowns on serde_json** — worse than the 30 that had caused the original revert. `serde::Serialize` genuinely
IS a dependency trait, so provenance waves it through.

The discriminator that actually works is **erasure**, which was in neither the queue nor the precedent: a
`dyn` receiver is type-erased, so the crate's local impls really are its candidate witnesses; a `T: Trait`
bound or an `impl Trait` param is monomorphized *by the caller*, so they are not. Two further carve-outs
(`self`/`crate`/`super` roots, nested-item scoping) were each found the same way — by a flood on real code,
not by reasoning.

So: the precedent was good evidence that the shape was reachable, and no evidence at all about which guard
made it safe. **Cite a precedent to justify attempting something; measure to find out what it costs.**

**The reverse check came back POSITIVE, twice.** swift's carve-out did not distinguish erased from
monomorphized receivers, and the engine that supplied the precedent WAS fabricating — `d62dd69` closed the
`some P` parameter, and `02fb0ad` closed four more spellings that the parameter-typed check could not see
(`[T]` under a `<T: P>` bound, `[some P]`, their `forEach` form, a `T`-typed field of a generic type, and
`extension Array where Element: P`). A precedent inherits the other engine's unexamined assumptions along
with its result — and the traffic goes BOTH ways: rust's measurement is what sent anyone to look at swift.

## Queue

### rust — 4 of 5 done; R5's DISCLOSURE half also landed (`5fde0d6`), determination half open
- [x] implicit stringification via a dep's `Display::fmt` — `1623a07`
- [x] drop glue via a dep's `Drop` — `a2fbe74`
- [x] `interfaceUnion` emitted in `--deps` child scans — `50218e3`
- [x] **R4 — imported-trait dispatch — `1950a27`.** DECIDED as resolution 1 (provenance) and shipped, with
      the test that said "external-trait local impl must not resolve (fabrication)" **unchanged and still
      passing**: it uses a bare `Iterator`, which needs no `use`, so `expand` leaves it unqualified and the
      provenance gate keeps it out. The hazard it protects is untouched.

      **Resolution 1 as written is NOT enough, and only measuring showed that.** It needs THREE carve-outs,
      each one a flood found on real code, each pinned by a verified-to-catch control:
      1. **provenance** — a genuine dependency crate root. std/core/alloc out (the `Iterator` case), AND
         `self`/`crate`/`super` out: a `use` binding keeps the text it was written with, so value-bag's
         `pub use self::error::Error` made std's `Error` look dependency-qualified — **17 fresh Unknowns**.
      2. **erasure** — the receiver must be spelled `dyn`. `serde::Serialize`/`Serializer` ARE dependency
         traits, so provenance passes them; CHA-ing serde_json's five `impl Serializer` types onto its
         GENERIC entry points put **32 fresh Unknowns** on serde_json (`to_string`, `to_vec`, `to_writer`).
         A `dyn` receiver is erased and the local impls are its candidate witnesses; a `T: Trait` bound or
         `impl Trait` param is monomorphized BY THE CALLER, so they are not. With this, serde_json is 0.
      3. **nested-item scope** (a leak this rung exposed, not previously recorded) — a `fn`/`impl` inside a
         body has its own signature but its calls are attributed to the enclosing unit, so its params
         SHADOW the outer ones. value-bag's `internal_visit(v: &dyn Serialize)` declares a nested
         `impl Serializer` whose `serialize_some<T: Serialize>(self, v: &T)` inherited the outer `v`'s
         `dyn`-ness.

      ADDITIVE and PRECISE-OR-NOTHING (the swift template): edges only, bounded at 12 impls, and
      `unresolved` is NOT set on the wide/absent arms — the local impl set is a LOWER bound on the true one,
      so a wide one stays the documented miss rather than flooding Unknown.

      A/B: 12 real crates zero gains/losses/entry-delta/Unknown-delta. Then the **whole local crates.io
      registry (976 crates) swept with the rung instrumented**, to find where it is LIVE rather than assume:
      6 crates, 35 firings, every one traced (rustls-webpki `&dyn pki_types::SignatureVerificationAlgorithm`
      → Ring/AwsLcRs is the R4 shape exactly); A/B on all 6 clean. **Worth carrying: on that corpus the only
      `dyn`-spelled external traits are `Write`, `Iterator` and `Error` — i.e. every firing the carve-outs
      block is a real fabrication, and the carve-outs are the whole safety margin, not belt-and-braces.**
      Known over-fire, bounded: there is no external analogue of the local arm's `trait_declares_method`
      guard, so a blanket-trait method on a `dyn` receiver (hyper 0.14's `.into()` on a `&dyn Stream`) forms
      an edge that dangles. Zero measured effect.
- [x] **R5 — CLOSED, both halves. Half 2 landed on the SECOND attempt — `a1e53e7`.** The canonical fixture
      goes exit 0 → **exit 1**, matching a single-tree control that is exit 1 in both arms, so it is a
      boundary defect and not a limit. Every one of attempt 1's four reverted defects is now a requirement
      with a mutation that was run and confirmed to fail: fully-qualified type identity on both ends;
      wrapper returns refused outright (`-> Result<Conn,E>` must not publish `Conn` — the binding holds the
      Result); a miss on `returns` OR on the entry lookup after a `returns` hit falls back to half 1's
      disclosure; every surface applied through the ONE `apply_dep_fn` from `7cb5748`.
      - **Item 0 fired for real, mid-implementation.** The first producer used suffix matching, and the
        MODULAR second fixture reproduced defect 1 through a new door: a bare `-> Client` inside `mod mock`
        is module-relative, `expand` leaves it bare, so it published `deplib#mock::client → deplib#sync::Client`.
        The flat fixture was structurally incapable of noticing. `bound_return_type` now resolves a bare
        name against its DECLARING module, matching is exact, and `super::` is refused (`expand` strips the
        root without walking up, which would root the path in the wrong module).
      - **Counts, not output** (item 8): 430 of 850 registry dep reports carry a surface, 9108 returns
        published; all 850 byte-equal to the pre-change engine once the block is removed. Consumer arm of
        408 crates / 41686 entries changed **nothing** and was entered 408 times (2 hits, 406 misses) — the
        rung is exercised there and simply has nothing to say. The one real recovery is on application code:
        `aws_config::defaults(v) -> ConfigLoader` then `.load()`, 2 functions gain `Log` and 45 gain
        `invisible: [aws_credential_types, aws_runtime]`, a blind-crate disclosure ebman could not make for
        itself.
      - Spec side: the field is now documented in SPEC §2 + the 0.23 changelog (`8394af0`). PART 21's rust
        row reads `RESOLVED — ['Fs']`, an arm the checker already accepted, so conformance needed no edit.

      Original framing, kept because it is what half 2 addressed:

      **R5 — the untyped cross-package receiver. DESIGN:
      [DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md).** The key finding is that it SPLITS,
      and the first half needs no format change: an engine always knows whether it FORMED A KEY, and
      `keyed-and-missed` (a genuine purity claim under §2 rule 3) vs `could-not-form-a-key` (no question was
      asked; silence licenses nothing) is a distinction available today. Half 1 = disclose the unformed key,
      triggered on the CONJUNCTION *untyped receiver AND provenance in a chained package* — not on untyped
      receivers generally, which would be the 8-25% false-uncertainty flood the coverage finding measured.
      Do half 1 per engine on its own schedule; it stops the report lying while the rung is negotiated, and
      it survives half 2 as the fail-closed floor for receivers half 2 still cannot type.
      Original framing kept below, since it is what half 2 addresses:
      **return types in the report.** A receiver bound from a dep factory (`let c = deplib::build();
      c.fetch()`) is untyped, so every later method call drops. Needs a `returns` field in the report
      format — spec-visible, so it wants a rung and four-way agreement. Largest item here, and now the last.

      **Both PREREQUISITES for attempt 2 are landed, each on its own, each measured (2026-07-26):**
      prerequisite 0, the full-qual third index key — `5feba18`, and it falsified this doc's claim that a
      full qual is unique within a crate (pgman: 1865 of 17861 collide, on duplicate cfg-gated entries), so
      requirement 3's fall-back-to-disclosure is load-bearing rather than belt-and-braces; and requirement
      4's duplication audit — `7cb5748`, which found rust carrying THREE drifted copies of the dep-apply
      path, exactly candor-java's `6ab26e4` shape. The rung itself is what remains.
- [x] **R6 — fully-qualified `&dyn deplib::Handler` — `7a5fc1d`.** The cause was one line of lossy indexing:
      `bound_leaves` keeps only `segments.last()` (every downstream index is leaf-keyed), and with no `use`
      to expand through the crate identity was simply GONE — `expand` returned a bare `Handler`, the
      `contains("::")` test failed, and the site emitted nothing at all: no dep key, no CHA, no disclosure.
      `sig_trait_quals` keeps the path the signature wrote; `crate`/`self`/`super` spellings are excluded
      because `expand` STRIPS those roots and would hand back a dependency-looking path (carve-out 1 by a
      second door). Gate exit 0 → 1.

      A/B, the whole 976-crate registry: **one** effect change and zero losses — tracing 0.1.44
      `__macro_support::__tracing_log` PURE → `['Log']`, traced to
      `__tracing_log(logger: &'static dyn log::Log, …) { logger.log(…) }`. The key now formed is
      `log::Log::log`, a rule the classifier already had and had never been handed. **855 new report entries
      across 60 crates, all with EMPTY effect sets** — functions that were ABSENT (which in this format IS a
      purity claim) and now carry `invisible: [<dep>]`. Unknown delta across all 976: zero. The same rung
      makes candor's own `span_lint(cx: &impl rustc_lint::LintContext)` read Log.

      Residual, asserted in the test so it cannot drift: the erasure carve-out means the generic-bound and
      `impl Trait` spellings of an imported trait still do not CHA local impls.

### java — 6 mechanism families DONE, and the JVM half of the vein has NO open row (fixture 15 silent-pure → 0; six gates exit 0 → 1 on the effect itself — the dep-interface row went `deny E Unknown[dispatch]` at half 1 and now flips on `deny Fs` too, and the abstract dep CLASS flips on `deny Fs` outright)
- [x] implicit stringification + equals/hashCode reentry — `bdf272c`. `reentryEdge` ended in a project-only
      `chaTargets`, and **an empty CHA emitted no Unknown, only a dropped edge**. New `nearestDepFn` — the
      cross-boundary analogue of `nearestConcreteSuper` — plus a shared `inheritDepFn` fold.
      *Independently verified here:* `app.S.show -> ['Env']`, gate exit 1.
- [x] inherited / default methods from a dep supertype — `a5b0a41`. `this.load()` compiles to invokevirtual
      with the PROJECT class as owner, so the join was never reached; the subclass's own ClassNode names its
      dep parent, so the chain is walkable from this side.
- [x] callback / HOF hand-off — `b891d5f`. Method refs join on the handle's exact owner+name+desc; a
      constructed functional takes the type's reported surface, gated on the PARAMETER being a functional
      interface.
- [x] **dep-interface-typed dispatch to a dep impl — HALF 1 DONE, `828ca18`** (java is the second engine to
      take [DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md) half 1, after rust `5fde0d6`).
      Resolution still needs the dependency's HIERARCHY — that stays half 2 — but the DISCLOSURE needed no
      format change: `Store s = Factory.build(); s.save()` was ABSENT from `functions` while counted in
      ⟨0.21⟩ `analyzed`, i.e. a positive purity claim, and now reads `['Unknown']` /
      `unknownWhy: ['dispatch:lib.Store.save']`. Gate `deny Fs Unknown[dispatch]` exit 0 → 1.

      **The java shape of "could-not-form-a-key" is INVOKEINTERFACE**, and that is the conjunct rust does
      not have an analogue for. Java always has a static owner, so there is no untyped receiver as such —
      but the OPCODE proves whether the key names the body: INVOKEINTERFACE proves the owner is an
      interface, so the hash we formed names a declaration the JVM will not run. INVOKEVIRTUAL is
      excluded (a plain dep class usually IS the body, so a miss there is a real purity claim), which is
      why an abstract dep CLASS — jackson's `ObjectIdGenerator`, the case originally recorded here — was
      left open here. **It is now CLOSED (`333cf10`, its own row below), and NOT by `typeSurface`:** the
      producer knows something no consumer can read off a call site, namely `ACC_ABSTRACT` on the member,
      and that flag answers the same question the opcode answers, one step earlier and with better
      evidence. The claim that this was "the sharpest thing half 2's `typeSurface` would buy java" was
      wrong — half 2 buys java nothing here.

      Five conjuncts, each one MEASURED not reasoned. "Unresolved receiver into a chained dep" alone fires
      on **5.4% of all analyzed functions** over nine chained JVM corpora (8.4% on logback-classic) —
      the COVERAGE-GRANULARITY flood, reproduced on the JVM. Adding INVOKEINTERFACE → 2.1%; adding "the
      chained report holds an EFFECTFUL body with this exact name+desc under another owner" → **0.49%**.
      The last is a signature join used ONLY as evidence to disclose, never to resolve — the behaviour the
      design doc prescribes when the type surface is absent.

      A/B nine chained library pairs, 32175 analyzed functions: **0 effect losses, 0 non-Unknown gains**,
      122 functions gain Unknown, entry count +25. All 68 distinct disclosed targets traced; ~95% of the
      355 sites justified by a genuine implementor (okio `BufferedSink`/`BufferedSource` → `RealBufferedSink`
      /`RealBufferedSource` — okhttp's `HeadersReader.readLine`, `RequestBody.writeTo` and
      `ResponseBody.byteStream` were absent from the report entirely). The other ~5% fired on a signature
      COLLISION (`HttpRequest.getPath` matched `URIBuilder.getPath`); those sites ARE genuinely
      unresolvable, so the disclosure is true about candor's state — only the evidence that prioritised it
      was coincidental. **Unchained control: twelve jars BYTE-IDENTICAL before and after** (conjunct 3).
- [x] **dep-interface-typed dispatch to a dep impl — HALF 2 DONE, and it needed NO format rung.** The
      `implements` field this row was blocked on is REDUNDANT: java keys report entries by
      `owner.name+desc`, which is exactly the key its consumer forms for an INVOKEINTERFACE site, so the
      already-specified `interfaceUnion` entries land where the join already looks. **The consumer was never
      the problem — only the PRODUCER was missing**, and candor-java's PART 18 N/A ("whole-classpath bytecode
      resolves cross-module dispatch natively") was true of an UNCHAINED scan and false at the boundary — the
      "ask separately what an engine does at the BOUNDARY" lesson again. candor-java now emits interface-CHA
      union entries under `CANDOR_WORKSPACE_CHAIN`, and **PART 18 is four-way** (verified to catch: against
      the pre-fix jar both java rows FAIL). `void run(lib.Store s) { s.save(…) }` goes
      `Unknown[dispatch:lib.Store.save]` → `['Fs']`.

      Measured. Flag OFF: twelve real jars **byte-identical** to the pre-change engine. Flag ON: entries
      +0.9%–14.8%, every added entry an `interfaceUnion`, ordinary entries untouched. The empty-union skip is
      the dominant filter, not a rubber stamp — jackson-databind: 198 candidate interface methods, 161 pure
      across every implementer, 36 emitted. Six chained library pairs, 21 922 analyzed functions: **65 effect
      gains, 0 effect losses**, 7 half-1 Unknowns resolved to a precise effect, 10 functions newly disclosing
      Unknown (httpcore's `Cancellable.cancel` implementers are themselves unresolved, so the union says so
      rather than letting httpclient's `abort()` claim a complete set). Gains traced: okio `BufferedSink`/
      `BufferedSource` → `RealBufferedSink`/`RealBufferedSource` (okhttp's `ResponseBody.byteStream`, every
      `WebSocketWriter.write*`), httpcore `HttpClientConnection.flush` → `DefaultBHttpClientConnection`
      (`Net`) reaching httpclient's three connection adapters.

      **A guard written, measured and REMOVED before shipping — item 0 in its exact shape.** "Emit only for
      an interface with at least one local subtype" read like a bound on `chaTargets`' owner-inherits-a-
      default fallback. It changed **not one entry** across twelve jars, and the one shape where it did fire
      — an interface re-abstracting a method whose only body is a super-interface `default` — is a genuinely
      runnable body that an EXTERNAL implementer inherits and cannot see for itself (a dep supertype is not
      on candor's classpath). It was an under-report wearing a bound's clothes; `chaTargets` finding nothing
      is what actually delivers "nothing implements it, so nothing is published". Two guards that DID survive
      were only shown load-bearing after their first fixture failed to exercise them — the static/private
      filter needs a PURE `static` interface method beside an implementer declaring the same `name+desc` as
      an INSTANCE method, or the static call site is charged a body it never runs. Every guard was then
      verified by mutating it out and confirming a named test fails; a test that has never failed is not
      evidence.

      **AMENDED after a code review (2026-07-26).** The emitter as first written carried three defects, all
      now fixed, and two of them were exactly the failure modes this queue's standing bar predicts:
      - an effectful `default` method's REAL entry SUPPRESSED the union (`if (!claimed.add(hash)) continue`),
        so every overriding implementer's effects were dropped from the only hash a chained consumer can key
        on — a silent under-report. Now MERGED into the claiming entry, which correctly stays UNMARKED (it is
        a real analysed unit counted in `analyzed`; marking it would make a consumer subtract it twice).
        Measured: `deny Net` two-tree exit 0 → 1, single-tree control exit 1 in both arms. On real code
        okhttp's `Interceptor.intercept` went `[]` → `[Clock,Fs,Log,Net,Unknown]`. — `48a5f18`
      - it unioned every implementer with NO fan-out bound, so an open hierarchy re-exported the smear the
        in-scan `CHA_FANOUT_LIMIT` exists to prevent (kafka `Message`, 217 subtypes). Now bounded, and a
        broad interface publishes `["Unknown"]` rather than silence — twelve pure implementers do not make
        the thirteenth pure, and §2 rule 3 makes an absent entry a purity claim. — `429c7b2`
      - the union's `netClass` merged hosts across implementers, letting one literal telemetry host certify
        another implementer's runtime-computed endpoint. Now classified PER IMPLEMENTER. Real but latent:
        across 52 jars, 1089 union entries carry a netClass and **not one** was certified. — `90af98f`

      So the earlier claim in this row that the union used "the CHA universe in-scan dispatch uses" was NOT
      true as written — the bound was missing. It is true now.
- [x] **by-NAME reentry contracts (`compareTo`/`append`/`write`/`read`) — `dd81bfa`** (+ `47caf53`). No
      single hash to join on, so the join enumerates the type's whole reported surface under the contract
      NAME — what the in-scan `reentryTargets` already does over project subtypes. Six shapes reproduced
      silent-pure split+chained; four now match their single-tree control, gate `deny Env` exit 0 → 1.
      Three guards keep it off the leaf-name join, each verified by mutating it out: owner pinned to the
      argument's DECLARED type; descriptor must match the contract's shape (a denylist — `default: true`);
      shadowing per OVERLOAD, with one fixture asserting **both** failure directions (the dropped inherited
      `append(CharSequence)` and the charged shadowed `append(char)`). 14 real jars unchained
      byte-identical; 21 chained/split libraries, 41k analysed fns, 0 gains 0 losses. Per item 8 the clean
      diff is not the evidence — the trigger was instrumented (1205×/523×, every declared type JDK or
      project), so the corpus is the fabrication CONTROL and the fixtures are the evidence.
      - **The `interfaceUnion` does not answer this one** (checked first): `Comparable`/`Appendable` are JDK
        types, never in a scanned set, and the consumer's key is the concrete dep type anyway.
      - **The sink bound shipped as an ALLOWLIST and was inverted — `47caf53`.** `comparesArgZero` listed
        the element-taking sinks, so a newly-added one would default to SUPPRESSING the dep join: omissions
        that are cardinal sins, the SAM-name allowlist shape one repo over. Today's partition is identical
        either way, so no fixture and no corpus can tell them apart — the direction is pinned by a unit
        test on the predicate itself, verified to catch (allowlist restored → that test and only that test
        fails, all 33 others green).
      - **RESIDUAL — CLOSED by `800f471`, the way its own test instructed.** The receiver-driven form (`w.write("x")`)
        fails only on `isJavaIoStreamType`, which needs the DEPENDENCY's supertypes. Relaxing it was
        measured on 11 split-and-chained libraries: 161 sites over 31 dep types, only 3 of the 31 are
        java.io streams — the rest (`PacketLineOut.writeString`, `RebaseState.readFile`,
        `ObjectWriter.writeValueAsString`) are already resolved by the exact-hash join. ~90% wrong-receiver
        fabrication, so the gate stays shut. Pinned as a test that says: *if this passes, the hierarchy
        arrived — delete the residual, don't relax the gate.*
- [x] **CONSUME `<report>.hierarchy.json` — DONE, `800f471`, and it closed the write/read residual with
      it.** Traced on real code: httpclient's `LoggingManagedHttpClientConnection.getSocketInputStream`
      went `[] → ['Net']` because `nearestDepFn` stopped at the first DEPENDENCY class — it could not see
      that class's own super, so the declaring body one hop further up (httpcore's
      `BHttpConnectionBase.getSocketInputStream`, `Net` in the chained report) was never reached. Seven
      functions recover Net; four had it DECLARED already, so `overdeclared` shrinks to match.
      - **The one-line version is unsound and that is the whole lesson.** Reading the sidecar inside
        `Cha.externalSupers` gets everything downstream for free — and `externalSupers` feeds
        `buildSubtypeIndex`, so a project `P extends DepBase` where `DepBase implements Runnable` newly
        lands in `subtypeIndex[Runnable]`, an `r.run()` site finds a non-empty CHA, and the JDK-SAM gate
        that raises the honest `callback:` Unknown fires ONLY on an empty target set. Disclosed Unknown →
        confident purity claim, manufactured by a change whose argument was that it only adds knowledge.
        Scoped to the two dep-facing walks instead, with a test asserting the SCOPE (`externalSupers` on a
        sidecar type must still return empty) rather than a comment claiming it.
      - Measured: 5 chained pairs, 7 gains, 0 losses, entry counts identical, **Unknown counts unchanged on
        every pair** — the scoping is what that last column proves. `CANDOR_DEPHIER_DEBUG` instruments both
        halves (18–276 types loaded per pair; 44 and 54 consultations, every hit a correct fact).
      - Not version-gated, deliberately: the sidecar carries no effect claim, only a route, and the entry it
        routes to is still version-gated — so a stale hierarchy reaches a stale entry and yields Unknown.
      As originally filed: `ReportWriter.writeHierarchy` emits every project class's direct supers +
      interfaces beside every scan; `Loader.loadCrossDeps` read only the report JSON, so nothing on the
      consumer side ever opened the sidecar. That is the `typeSurface.implements` information the
      abstract-dep-CLASS row, swift row 3 and the write/read residual were all blocked on — and for java it
      needed no format rung at all, only a consumer.
      **THE FOLLOW-ON IS SETTLED — and BOTH halves of "the abstract-dep-CLASS row wants the hierarchy in
      the SUBTYPE INDEX" turned out to be wrong.** That sentence stood here as the one use `800f471`
      refused, needing "its own argument about what happens to the Unknowns that resolution would
      suppress". The argument was measured before a line of fix was written (item 8: a shadow subtype
      index built from the sidecar, compared against the real one at every polymorphic dispatch site, over
      seven chained real jar pairs / 68 539 sites):
      - **It cannot close the row.** `buildSubtypeIndex` files PROJECT `ClassNode`s and `chaTargets` needs
        one to test `declaresConcrete`, so a DEPENDENCY's implementer never enters the index however wide
        the hierarchy gets. The two-tree fixture is exit 0 in that arm too. The row's impl is in the dep;
        the index only ever holds the consumer's classes.
      - **And it costs.** 737 sites go empty-CHA → non-empty; at report level 113 gains and **8 LOSSES** —
        7 functions lose a disclosed `Unknown`, one loses a concrete `Net`. httpclient's
        `IdleConnectionHandler.closeExpiredConnections` and three siblings become confident purity claims
        on methods that close network connections, because the target set substituted for the disclosure
        is not the true one (httpcore's own implementers are outside the scan). **The gate `800f471`'s
        comment named is not the one that fired**: instrumented per site, the JDK-functional-SAM
        `callback:` branch suppressed ZERO, as did the missing-project-impl branch — what suppressed was
        half 1, whose conjunct 4 is the same "the project CHA is empty" test. The argument generalises and
        the illustration did not; the property to protect is EVERY Unknown branch conditioned on an empty
        target set, not the one that was easiest to picture.
      - **The first arm said byte-identical, zero cost — the flattering way again (item 7), and the cause
        is worth carrying.** As a literal one-liner inside `externalSupers` the widening is **INERT**:
        `runScan` builds the subtype index BEFORE `loadCrossDeps` populates `depSupers`. So the hazard
        `800f471` argued against could not fire as written, and a future reordering of `runScan` would arm
        it silently. The numbers above are from the arm with the load hoisted. **A control that produces
        no diff may be measuring nothing — check the mechanism is reachable before believing its zero.**
      The refusal + the numbers now live in `Cha#depDirectSupers` (candor-java `cb8c1aa`), so nobody has
      to re-derive them, and the surviving guard is named there: `CrossScanBoundaryTest`'s "`externalSupers`
      on a sidecar type must still return empty" holds under either ordering.
- [x] **dispatch through a dependency's ABSTRACT CLASS — DONE, candor-java `333cf10`, producer-side, and
      the consumer changed not at all.** The last open JVM row. `Store s = Factory.build(); s.save()` where
      `Store` is a dep's abstract class read SILENT-PURE (absent from `functions`, counted in ⟨0.21⟩
      `analyzed`) — INVOKEVIRTUAL, so half 1 deliberately does not disclose, and the project CHA is empty
      because the implementer is in the dependency. Gate `deny Fs` exit 0 → **1**, single-tree control exit
      1 in BOTH arms.

      **The discriminator is the ACCESS FLAG, and it is the producing side of the three-row rule.** Absence
      under a key licenses a purity claim only if the key names something that COULD have had a body.
      `ACC_ABSTRACT` on the member proves the JVM will never run the declaration `lib/Store.save` names, so
      no report — of any version, from any engine — can ever answer that key. Half 1 reads the OPCODE at the
      consumer; this reads the access flag at the producer, which is strictly better evidence. So the
      `interfaceUnion` emitter admits abstract CLASSES and publishes their ABSTRACT members, the entry lands
      under the key `crossDepJoin` already forms, and there is **no consumer change: no CHA, no subtype
      index, no Unknown gate, no new resolution path.** The template ("emit the call shape the join already
      understands") for the third time.

      SCOPE, asserted by tests not by comments: a class publishes only its ABSTRACT members. A concrete
      member's key names a body that exists and was analysed, so the report's answer under it — the entry,
      or silence meaning pure — is already TRUE, and a union over its overrides could only widen a true
      answer. Verified by mutation: removing the `ACC_ABSTRACT` member skip fails
      `aConcreteMemberOfTheSameAbstractClassPublishesNoUnion` and only that; reverting the class admission
      to interfaces-only fails the four abstract-arm tests. Existing bounds all apply unchanged (all-pure →
      publish NOTHING; >`CHA_FANOUT_LIMIT` open hierarchy → `["Unknown"]`, never the smear and never
      silence). **The pre-existing test that asserted the old scope was REWRITTEN, not deleted** — half its
      premise ("an abstract dependency CLASS receiver is the documented residual") was this row, and the
      half that was always a scope survives as `aCONCRETEClassMethodIsUntouched`.

      **A comment claim the measurement falsified mid-flight, item 9 in its exact shape.** It read "an
      abstract member has no body, so no real entry can claim its hash — the merge path is unreachable for
      it." False: `writeJson`'s filter keeps a BODILESS entry when the method is framework-rooted or its
      class declares a capability — **17 such entries across twelve real dep reports**, logback's
      `AppenderBase.append` among them, an entry point carrying `inferred: []`. The merge is *right* there,
      for the reason `48a5f18` gives: `[]` under a hash a consumer keys on IS a purity claim about the
      dispatch and it was false. Verified widening-only across all 17.

      Measured, seven chained pairs, both arms' jars kept by content hash and the final jar re-run to
      reproduce its arm byte-for-byte (item 7b): flag OFF every dep AND consumer report **byte-identical**;
      flag ON producer +59 entries over 7 383 (0.8%), all marked, 17 widened / 0 narrowed / 0 removed;
      flag ON consumer **14 gains, 0 losses, Unknown 8 330 → 8 336 (UP, never down** — a dropping Unknown
      count is exactly what the refused route does). Gains traced to bytecode, and the headline is the case
      this queue recorded by name: jackson-databind's `WritableObjectId.generateId` does `INVOKEVIRTUAL
      ObjectIdGenerator.generateId` on a field typed by jackson-annotations' abstract class, whose
      `ObjectIdGenerators$UUIDGenerator.generateId` is `UUID.randomUUID()` — `Rand`, reaching
      `BeanSerializer.serialize` and 7 more. The other 6 are logback appender/converter dispatch going
      `[]` → `['Unknown']`, the disclosure direction.

      **Residual, deliberately not taken here:** a CONCRETE dep method that is overridden effectfully still
      answers only for its own body across the boundary, where in-scan the same site is charged the CHA
      union. That is the `48a5f18` "the engine contradicts itself across the scan boundary" argument one
      rung down — but unlike the abstract case the key IS answerable and the answer IS true, so it is a
      narrower question than a purity claim, and its blast radius (every non-final method of every
      non-final class) wants its own measurement.
- [x] **`reentryTargets` fanned only DOWN the subtype index — FIXED, candor-java `9ae68f7`.** A SINGLE-TREE
      silent under-report, found by a smell rather than a report: making the chained arm walk a dependency's
      supers left the in-scan control strictly LESS complete than the cross-boundary case, which is the
      wrong way round and meant the in-scan gap had been there all along. `new Formatter(half)` where `Half`
      overrides `append(char)` and inherits the effectful `append(CharSequence)` reported `[]`. Now walks
      each subtype's own chain with per-OVERLOAD shadowing — the same rule the cross-boundary
      `nearestDepFnsNamed` uses; per NAME would drop the inherited overload, no shadowing would charge a
      replaced body, and the fixture asserts both directions. One real gain on the corpus, traced to
      bytecode: jgit's `PackWriter.writeChecksum` went from a purity claim to the effect set the same
      report already gave `CancellableDigestOutputStream.write(byte[],int,int)` — which is exactly what
      `out.write(packcsum)` runs, since `PackOutputStream` declares no `write` of its own.

**A fabrication caught mid-flight, worth carrying:** the first version imported dep entries whose whole
content is `Unknown`, which turned **12 fully-resolved jackson-databind functions Unknown** from one method
`ObjectIdGenerator`/`ResolvedType.isReferenceType()`. Guard: skip a bare-`Unknown` dep entry when the
project CHA resolves the same signature. Measured with the guard removed — suppresses exactly 14 functions
across six pairs, all Unknown-only, **never a real effect**.

**Two operational traps:** dep reports are VERSION-GATED (generate with the same jar you test with or it is
silently treated as stale); and `build/libs` can hold MORE THAN ONE `-all.jar`, so a glob picks the stale one
— that cost two false negatives here before it was spotted. The stale 0.23.0 artifact has been removed.

### ts — all 5 confirmed mechanisms DONE
- [x] the monorepo symlink shape — a symlinked workspace dep produced **no disclosure at all** because the
      blind branch was guarded on `/node_modules/` — `6fb2560`
- [x] implicit coercion into a dep's `toString`/`valueOf`/`toJSON` — `625e8fd`
- [x] `new DepClass()` never consulting the chained dep report — `965ac82`
- [x] a dep function passed BY REFERENCE to an invoking HOF — `75ec3f6`
- [x] **the UNANSWERABLE KEY** ([DEP-RECEIVER-TYPING-DESIGN.md](DEP-RECEIVER-TYPING-DESIGN.md) half 1).
      Conformance PART 21 now runs ts beside java and rust.

      **The design note's canonical fixture REFUTES for ts** — worth recording rather than papering over.
      Return types travel in the `.d.ts`, so `const c = build(); c.fetch()` types `c` to `Client`, forms
      `depkit#Client.fetch`, and joins precisely. A receiver ts genuinely cannot type is `any`, which
      already read `callback:` Unknown. Neither half of the rust shape survives here.

      What IS silent is a receiver typed to an **abstraction** — an interface method or property
      signature, an anonymous type-literal member, an `abstract` member. `build(): Fetcher` over a `.d.ts`
      whose only body is hashed `pkg#Client.fetch`: the key is formed and can never be answered, by any
      report, whatever the implementations do. The same evidential position as rust's unformed key,
      reached from the other side — ts knows a type the dependency has no vocabulary for, where rust knows
      a provenance and no type. Silent on the desugared path too (`[1].forEach(job.run)`).

      Third conjunct confirmed independently on ts: unchained, the κ ledger already emits
      `invisible: [pkg]` for every one of these; chained it correctly falls silent, and that silence is
      the confident purity claim. A/B unchained over 10 real targets: **0 gains, 0 losses, entry counts
      identical**. Chained `--workspace` over 5 ukri-tfs services: **5 gains, 0 losses** over ~1000
      analyzed functions; with producer-side union entries stripped (the plain `CANDOR_DEPS` shape) 8/202
      and 3/453. Every gain traced to a real implementor — `OutboundChannel.publishRaw` (publishes to
      SNS), `CoreLogger.info` (`Clock`), `ServiceHostNames.getUrl` (`Env`) — or to a member installed at
      runtime by `fastify.decorate('getServices', …)`, which nothing could resolve.

      **The union and this arm are layered, not redundant.** `OutboundChannel` is declared TWICE in
      `@ukri-tfs/message-handling`, so the `interfaceUnion` emitter's never-guess ambiguity guard declines
      to emit — correctly — and before this arm that declining left silence. Half 1 is the fail-closed
      floor under every guard the resolution path is right to refuse.

The first four follow the rust template: no new resolution path — each routes its declaration through the decision
procedure the CallExpression path already runs (chained report → §5.1 manifest → κ ledger), factored into one
`chargeExternalDecl`. Gate on the two-package fixture, `deny Fs`, identical source: one project **exit 1** →
split+chained **exit 0** → now **exit 1**, matching the one-project control on all three mechanisms.

A/B, 13 real targets unchained: 0 effect gains, 0 losses, 166 invisible gains, 0 invisible losses. Chained
over 4 ukri-tfs services: 7 effect gains, 0 losses — every one tracing to
`@ukri-tfs/common#ServiceHostNamesFromAwsServiceDiscovery.constructor -> ['Clock','Env']` reaching
`createServiceHostNamesForDsApi`, which went from absent-from-the-report (a purity claim) to `['Clock','Env']`.

The coercion arm's anti-flood property was measured under load rather than assumed: the arm is entered a few
hundred times on the corpus and contributes nothing every time, because every resolution lands on the ES lib
or `@types/node` (`Buffer.toString`), both excluded by design.

**Verified independently before PART 20's ts row was added**, on a fixture outside the harness: pre-fix
candor-ts writes `0 effectful functions` for the consumer, post-fix `src.index.show -> ['Env']`. *The first
attempt at that control was worthless* — the pre-fix worktree had no `node_modules`, so the scan crashed and
left the POST-fix report on disk to be read back as if it were the pre-fix result. **Delete the output before
you measure a control** (now item 8 of the standing bar).

Residual, still open:
  union of every file's top level (`proper-lockfile` picked up `Net` from `retry`'s `example/dns.js`).

  **Analysed 2026-07-26 — and "narrow to the resolved entry" is the WRONG fix as stated.** The union is baked
  into the KEY, not the scan scope: the child scan emits every module unit under the single hash
  `<pkg>#<module>`, and the consumer looks up exactly that (`crossDeps.get(\`${pkg}#<module>\`)`).

  Two tempting narrowings, both wrong:
  - *Scan only the entry file.* Under-reports: the entry's transitively-required modules genuinely DO run on
    import, and their top-level effects are real. This is the miss direction.
  - *Exclude `example/`, `test/`, `benchmark/`.* A denylist of directory names is a guess about reachability,
    not a proof of it — and those files are in `node_modules` precisely because they were published.

  The correct fix is **per-file module unit keys** in the child report (`<pkg>#<relpath>.<module>`), with the
  consumer looking up the package's ENTRY module (`main`/`exports`). That is sound without any reachability
  guess, because the entry unit's `inferred` ALREADY includes its transitive imports — the in-scan
  module-import edge computes exactly that closure. An unreachable `example/dns.js` then simply has its own
  key that nobody looks up.

  Cost: it is a wire-visible change to how module units are named, so it wants the same care as a rung.

  **DONE — candor-ts `db64b1e`, and the wire-compatibility half is the part that needed the care.** Keys are
  now `<pkg>#<relpath>.<module>` and the consumer looks up the module its SPECIFIER names. A new consumer
  meeting an OLD report (bare `<pkg>#<module>`) honours the old key and returns the old union answer —
  silence there would have turned a precision fix into the very under-report this vein exists to close, and
  the bare tail is a structural discriminator rather than a version guess. Measured: 8 targets, unchained
  byte-identical; chained 0 gains, 0 losses, 84 narrowed, **0 `Unknown` removed** and nothing went from
  disclosing something to disclosing nothing. The 13 concrete effects removed were each traced to a file no
  import runs (`react/umd/react.development.js`, next's polyfills, angular's schematics codemods).

  **VERIFIED INDEPENDENTLY** (four fixtures of my own, not the agent's): per-file keys are emitted; the
  load-bearing premise holds — the entry unit's `inferred` really does carry a transitively-imported file's
  `Fs`; the consumer charges that `Fs` and NOT the unimported sibling's `Net`; and an old-shape report with
  two colliding units returns `['Fs','Net']`, the union, unchanged.

  **A measurement trap found while verifying, worth carrying:** `--dep-inits` RE-SCANS the packages on disk
  and chains its own fresh reports, so pointing `--deps` at a hand-built report while `--dep-inits` is on
  measures the fresh scan, not the report you wrote. It made a correct fix look like a compatibility
  regression for two rounds. To exercise the compatibility path, remove the package from disk so the
  rescan has nothing to contribute.
- **Interface-union needs source — DIAGNOSED 2026-07-26, and the obvious fix is the wrong one.** A published
  package ships `dist` JS + `.d.ts`. Measured: scanning it with `CANDOR_WORKSPACE_CHAIN=1 --allow-js` emits
  `depkit#FileStore.save ['Fs']` and NO union entry.

  **The blocker is not that the interface declaration is filtered out.** I assumed it was — `.d.ts` files are
  deliberately excluded from the scanned set (they have no bodies, so scanning them would mint empty units),
  so `localInterfaceDecls`' `projectFiles` check rejects an interface declared only in typings. I widened
  that check to accept `.d.ts` interfaces belonging to the scanned package, measured, and it changed
  **nothing**. Reverted.

  The real blocker is one level up: the emitter walks the CLASS's `heritageClauses`, and the scanned source
  is `dist/index.js`, where `class FileStore { save(s) {…} }` has no `implements` clause at all — grep says
  0 in the `.js`, 1 in the `.d.ts`. There is no heritage clause to walk, so no interface is ever consulted.

  **The symbol path is CLOSED and the module path is OPEN — both measured with the TypeScript API directly.**
  The checker does NOT merge a CommonJS `exports.FileStore = FileStore` with the sibling `declare class`:
  the `.js` class symbol has exactly ONE declaration, its own, with zero heritage clauses. So no
  symbol-walk reaches the `implements`.

  But the typings MODULE's exports do:

      checker.getExportsOfModule(<dist/index.d.ts symbol>)
        export build      kind=FunctionDeclaration
        export Store      kind=InterfaceDeclaration
        export FileStore  kind=ClassDeclaration   heritage= implements:Store

  So the mechanism is: resolve the package's own typings module, walk its exports, and for each exported
  class carrying an `implements` clause register it under that interface — pairing the typings declaration
  to the scanned `dist` class **by exported name within the same package**. That pairing is authoritative
  rather than a guess: `exports.FileStore` and `declare class FileStore` are the same public symbol by
  construction of the package. Cross-package name matching would NOT be, and must not be attempted.

  **Do not re-attempt the `localInterfaceDecls` widening; it is measured inert** — the blocker was never
  which interface declarations are admitted.

  **SHIPPED as candor-ts `5057026`, then INDEPENDENTLY VERIFIED — and the verification found two defects in
  it plus two more the rung exposed, all four now closed.** The A/B was not re-run and agreed with; the
  attack was the other direction, per item 0. Every fix carries a two-tree fixture, a single-tree control,
  and each guard mutated out with the named failing test recorded.
  - **FABRICATION, and a regression the rung introduced — candor-ts `0185649`.** The ambiguity counter read
    only the `.` typings, but the union hash is `pkg#Iface.member`, a package plus a BARE name, so every
    interface of that name in the package maps to it however it is exported. A `subkit` with an effectful
    `Store` on `.` and an unrelated PURE `Store` on `./sub` published the first as the answer for both, and
    a consumer of `subkit/sub` FAILED `deny Fs`; the pre-`5057026` engine disclosed
    `Unknown[dispatch:subkit.Store.save]` and exited 0. The census now covers `types`/`typings`, every
    `.d.ts` in the `exports` tree and `typesVersions` (which names files without their extension — 8 of 343
    corpus packages declare one, 7 with a star, so the star is expanded from disk). **ONE program over all
    the roots**, because a barrel `export * from './sub'` must give back the same declaration NODE from both
    entry points or every package shipping a barrel is refused. A truncated expansion refuses the typings
    arm outright: half a census re-opens the fabrication.
  - **A CONFIDENT WRONG ANSWER, older than the rung — candor-ts `d7060ca`.** "The in-scan arm wins a name
    collision" dropped the typings arm on the NAME, throwing away the only evidence the engine had that the
    name means two things. An internal `interface Store` (implementer does Net) beside the public one the
    typings pair to an effectful `FileStore` published `mixkit#Store.save -> ['Net'] unresolved:false`: a
    fabricated Net, a dropped Fs, no disclosure. The rule is now REDUNDANCY — drop the typings arm only when
    every class it names is already in the in-scan set — so the shadow case survives and a collision that
    brings new information makes the name ambiguous and refuses both. Instrumented: 27 typings arms across
    the corpus, **21 collide and all 21 are redundant**, so @ukri-tfs/common's seven entries survive by the
    rule rather than by exemption.
  - **NO FAN-OUT BOUND — candor-ts `fc8d297`, the ts sibling of java `429c7b2`.** The emitter unioned every
    implementer while the in-scan dispatch site bounds at 12, so the producer published what its own
    dispatch refuses to resolve: rxjs `Operator` has 70 implementers, 16 reaching Net, and rxjs's own
    `Observable.subscribe` reads `Unknown[dispatch:…Operator.call]` while the report offered a consumer
    `rxjs#Operator.call -> ['Net','Unknown']`. Now ONE named `CHA_FANOUT_LIMIT` read by both sites (java left
    two literals and that is how they drifted), publishing `['Unknown']` + reason past the bound — never
    silence. Measured across 353 targets the tail is thin but real: 43 of 44 arms have ≤5 implementers and
    the 44th has 70, so **the argument is the self-contradiction, not the distribution**. No
    `isClosedHierarchy` analogue exists in TS (no `sealed`).
  - **PROPERTY-SPELLED INTERFACE MEMBERS — candor-ts `d9b8c34`**, the residual `5057026` recorded, closed in
    BOTH arms. `run: (x) => void` is a PropertySignature over a FunctionTypeNode and the checker resolves a
    call to the TYPE NODE, which has no name and no owner — so three sites that key on a declaration's name
    formed no key at all. @ukri-tfs/email's whole `SendStrategy` is spelled this way (four implementers, zero
    method signatures). One `memberSigOf` hop, called from all four sites; only a FunctionTypeNode qualifies.
    Chained pair measured end to end: `@ukri-tfs/email#EmailService.send` `['Unknown']` → `['Net']
    invisible:['@aws-sdk/client-ses']`, reaching `invite-service#EmailServiceProxy.send`, 0 losses. It also
    repairs 139 disclosure strings that named the PROPERTY as the owner type (`dispatch:<mod>.<prop>.member`).
  - **Two carried findings. (1) is DONE, candor-ts `4dad22d`; (2) is DIAGNOSED and the question it was filed
    under is the wrong question.**
    1. ~~The ts dep-join copies `inferred` and `invisible` only, so a chained dep's Unknown loses its REASON
       CLASS at the consumer and falls back to `unresolved`~~ — **CLOSED**, and the root cause was the same
       one candor-java `6ab26e4` found: DUPLICATION. The CallExpression arm and the desugared-declaration
       arm each spelled the apply-a-dep-entry copy out, they had already drifted, and the reason class was
       added to neither; there is one `applyDepHit` now. A report failing the §2.1 check keeps the BARE
       Unknown — its reasons are assertions from a build we do not trust — and that is asserted, not
       assumed. Measured, 4 chained @ukri-tfs services: 0 effect gains, 0 losses, entry counts identical,
       **606 functions gain a real reason class** where they read `unresolved`; producer reports
       byte-identical. Gate both ways: `deny Net Unknown[reflect]` exit 0 → 1, `Unknown[native]` stays 0.
    2. **The malformed `….member` reasons are NOT "all the function-type-under-a-TYPE-ALIAS shape", and
       "what should the owner be" has no answer because there is no owner.** Measured on a fixture, three
       producing shapes, and in two of them the owner is not a type at all:
       - `type Handler = (x) => void` → `dispatch:<mod>.Handler.member` (the filed shape — owner is a type,
         member is the literal string `member`);
       - `makeFn()("a")` where the RETURN is an inline function type → `dispatch:<mod>.makeFn.member`,
         naming a **function** as the owner type;
       - `const slot: (x) => void` → `dispatch:<mod>.slot.member`, naming a **variable**.

       And on the ukri-tfs corpus the dominant form is neither: **31 of 68 are `dispatch:type.member`**,
       both halves fallen back. So the string violates SPEC §4's NORMATIVE `dispatch:<owner-type>.<member>`
       in the OWNER as often as in the member, and the dispatch-frontier consumer
       (`possibleViaUnknownDispatch`), which parses that payload against the hierarchy, can never match it.

       The settled diagnosis: in every one of these the callee is a function VALUE with no owner type and
       no member, which SPEC §4 assigns to **`callback:`** ("an unresolved higher-order / owner-less
       invocation… whose target and owner type are not both known", best-effort spelling) and explicitly
       withholds from `dispatch:`. The engine already gets this right where there is no name to grab —
       `f: (x) => void` emits `callback:param#0` and nothing else — and the alias shape emits **both**, the
       correct `callback:` and the malformed `dispatch:`, for the same site. So this is a
       RECLASSIFICATION, not a better owner string.

       **Deliberately NOT landed with the rest of this pass, for two reasons.** It NARROWS a gate: 68
       reasons over 64 functions, and for **16 of those functions it is the only reason**, so their class
       moves `dispatch` → `indirect` and a `deny E Unknown[dispatch]` rule stops firing where it fires
       today. And `unknownWhy` vocabulary is TIER 1 and four-way, so ts should not move a shape's class
       unilaterally — ask rust/java/swift what they emit for an owner-less function value first. A
       strictly-widening interim (ADD the `callback:` reason, keep the malformed `dispatch:` one) is
       available and loses no gate, but leaves the malformed string in the report and was not taken.
  - **Worth carrying methodologically:** the ambiguity guard's SILENCE is honest in ts specifically, because
    half 1 discloses an absent interface key at the consumer — mutating the fan-out bound's Unknown to a
    `continue` still leaves the consumer disclosing. That is a property of the layer beneath, not of the
    emitter, and it is why the producer-side tests are the ones that catch it. Also: scratch copies of the
    engine left in the scanned repo showed up as four "new entries" in the self-scan A/B — a measurement
    apparatus inside the target.
- **A SECOND adversarial review of the ts boundary work found three more, all now closed (2026-07-26/27),
  and the pattern is that each one was a REFUSAL AIMED AT THE WRONG SIDE.**
  - **`db64b1e`'s wire-key change was invisible to §2.1 — candor-ts `651c9f9`.** Module unit hashes moved
    from `<pkg>#<module>` to `<pkg>#<relpath>.<module>` without a `package.json` bump, so both builds called
    themselves `candor-ts-0.23.1`. The comment claimed "an OLD consumer over a NEW report treats the whole
    report as stale and downgrades it to Unknown"; measured with the pre-change build as the consumer, that
    is **false**, and the bump alone does not fix it: **staleness rewrites the CONTENT of the keys a report
    carries and can never conjure a key it lacks**, so a lookup that misses, misses whatever the version
    says. The importer read ABSENT (a ⟨0.21⟩ purity claim) with `deny Fs` at exit 0, single-tree control
    exit 1 in both arms. Nothing a NEW report can CARRY helps either — the old consumer is frozen and reads
    one discriminator — so the durable rule is the forward one: **an untrusted report grants no COVERAGE**,
    since §2 rule 3 turns its silence into a purity claim on the authority of a report we just refused to
    trust. Now a key it fails to answer falls back to the κ ledger's `invisible` hedge and an import backed
    only by it discloses Unknown. Real code: one dep report marked as another build gives invite-service 76
    new hedges and 10 functions that were absent entirely, 0 effect losses. **Standing rule now in
    candor-ts AGENTS.md: a report-KEY change bumps the build id in the same commit — necessary, and not
    sufficient.**
  - **A truncated typings census refused the EVIDENCE — candor-ts `90655d9`.** `typingsRoots` gives up past
    128 `.d.ts` and dropped the typings arm when it did. The evidence is the only thing that can say a name
    means two things, so `ifaceNameCounts` read 1 instead of 2, the never-guess guard did not fire, and the
    package published its INTERNAL `Store` (Net) as the answer for the PUBLIC one (Fs) — `d7060ca`'s
    fabrication restored for exactly the packages big enough to hit the cap, and `d7060ca`'s own test could
    not see it (its fixture has no in-scan arm, so "publishes nothing" could not distinguish a dropped arm
    from a refused publication). The refusal moved to the PUBLISHING side, routed through the never-guess
    guard already there: **two declarations of a name, and a census that cannot prove there is only one,
    are the same evidential position.** Bite measured across 8 real `node_modules` trees: 3 packages in
    3213 (rxjs, @angular/common), costing 7 union entries, every one a bare `['Unknown']`.
  - **A real entry claiming a union's hash suppressed the union — candor-ts `67d092d`, the ts sibling of
    java `48a5f18`.** TS reaches the collision by a BARE NAME (`pkg#Store.save`), so any `class Store`
    claims the key an interface-typed consumer forms — by declaration merging or by two unrelated
    declarations across files. In-scan `['Fs','Net']` and `deny Net` exit 1; split and chained the consumer
    read an unrelated class's `['Env']`, exit 0, plus a fabricated `deny Env` catch. **It is NOT
    `mergeUnionInto`, and measuring the literal port is what said so:** java merges into the interface's own
    `default` METHOD, whose in-scan site already carries the CHA union; TS interfaces have no bodies, so the
    claimant is always a CLASS body, and java's merge ported literally charges an env-reading class with
    `['Env','Fs','Net']` and fires the producer's own `deny Net` on it — the hazard java's comment names one
    field along, at `overdeclared`. The union goes in its own marked entry under the shared hash and SPEC
    §2's documented duplicate-hash UNION rule joins it: same answer, no analysed unit rewritten. **A
    precedent tells you the OUTCOME to reach, not the mechanism to reach it with** — the sibling of the R4
    lesson, one rung along.
  - **Found while measuring, closed with them — candor-ts `e66f29e`:** a union entry that INHERITED Unknown
    from an implementer published `inferred: ['Unknown']` with `unresolved` absent, i.e. false. `unresolved`
    was set on the `broad` arm only. A TIER-1 trust marker failing OPEN, live on all seven of rxjs's unions.
  - **Two zero-delta A/Bs in this pass were claims about the EXPERIMENT** (item 8), and each needed a
    different answer. The §2.1 arms are byte-identical because no run there HAS a version mismatch — so the
    mechanism was armed on real code instead (one report re-marked). The union-hash arms are byte-identical
    because the trigger never fires: instrumented over **270 producer-scanned packages, a union hash is
    claimed zero times**, which makes the corpus the fabrication CONTROL and the fixtures the evidence — the
    posture java's `dd81bfa` landed under. **A third arm measured nothing at all and looked clean:** five
    `--workspace` targets that chained "0 workspace dep report(s)", byte-identical for a reason with nothing
    to do with the change. Check the chain actually chained before reading its diff.
- **A LOCAL class implementing a DEPENDENCY's interface is outside the CHA universe.** `interfaceImpls`
  registers local interface declarations only, so `use(f: DepIface) { f.go() }` never reaches the local
  `class Mine implements DepIface` — the ts sibling of swift's `eae2de2` (dispatch over an IMPORTED protocol
  with LOCAL conformers). Found while measuring half 1, and half 1 now DISCLOSES it (`Unknown`) rather than
  reading pure, so it is no longer a silent under-report; resolving it precisely is the open item. Note
  swift's carve-out before copying it — a widened match here is the leaf-name trap the design note rejects.

### swift — half 1 NOT YET DONE; both rows reproduced with a fixture (2026-07-26)

The last engine missing from conformance PART 21. **Reproduced, not assumed** — dep declares the protocol
and the only conformer, app has none:

    dep report:  FileStore.save ['Fs']          <- the answer is present
    app:         go(_ s: any Store) { s.save() }        ABSENT — reads PURE   (row 3)
                 goFactory() { let s = build(); s.save() }  ABSENT — reads PURE   (row 2)
    coverage: null   (the package is chained, so correctly no hedge)

- **Row 2 (`goFactory`) is implementable now.** `rootOf` types a factory call via `returns[n]`, which holds
  LOCAL function returns only; `build` is a dep function so the root is `nil`, no `extOwner` is formed, and
  the member call falls through silently. Same shape as rust `5fde0d6`: mark the binding dep-provenance-
  untyped, emit a marker, disclose `Unknown` when the file imports a COVERED package (the third conjunct).
- **Row 3 (`go`) needs half 2.** The join forms `DepLib#Store.save` and misses, because `Store.save` is a
  protocol REQUIREMENT — no body is ever hashed under that key, so no report can answer it. Distinguishing
  that from a legitimate keyed-and-missed needs the dependency's HIERARCHY, i.e. `typeSurface.implements`.
  This is the same blocker as java's dep-interface case, and java only got round it because bytecode carries
  the opcode: `INVOKEINTERFACE` proves unanswerability without needing the hierarchy. Swift's syntax does
  not carry an equivalent — a protocol-typed and a class-typed parameter look identical at the call site.

### swift — 6 of 7 gate-flipping mechanisms DONE
- [x] implicit stringification of a dep type, all three operand forms — `83ca73c` (verified independently:
      `describeTyped -> ['Env']` across the boundary, gate back to exit 1)
- [x] dependency `deinit` glue — `41dc8de`
- [x] dispatch over an IMPORTED protocol with LOCAL conformers — `eae2de2`, plus **TWO erasure fixes it
      needed and shipped without**: `d62dd69` and `02fb0ad`. Needs no dep report: Swift spells a conformance
      to an imported protocol in the same inheritance clause, so `subtypesOf` already had it.

      **It took THREE carve-outs, and only one of them shipped with the rung.**
      1. `RAW_VALUE_BASE_TYPES` (in `eae2de2`) — `enum Rank: String` puts `String` in the inheritance clause,
         so an unguarded CHA sends every call on a String-typed value into raw-value enums' methods.
      2. **ERASURE, the `some P` parameter (`d62dd69`)** — found by rust's R4 measurement pointing back here.
         `typeName` collapses `some P` and `any P` to `P`, so the opaque spelling inherited the existential's
         CHA. Note the mid-flight correction in `81a9dc3`: the first version enforced it by WITHHOLDING the
         receiver's type, which took the §2 dep join with it and made an Fs-performing function read PURE —
         one sin traded for the other. The gate belongs on the CHA arm alone.
      3. **ERASURE, everything that is not a parameter's own type (`02fb0ad`)** — `isOpaqueParam(p.type)`
         answers the question for `func f(_ s: some P)` and for nothing else. `[T]` under a `<T: P>` bound,
         `[some P]`, the `forEach` closure form of either, a field typed as the enclosing type's generic
         parameter, and `extension Array where Element: P` all resolve a receiver to the bound `P` too, and
         all are monomorphized by the caller. Each was measured charging the effectful conformer's Env to a
         function whose only call site passes the pure one. The bare `<T: P>(_ x: T)` parameter escaped by
         ACCIDENT (`params` records the spelling `T`, which resolves to nothing) — which is exactly why the
         container and field paths, which deliberately resolve to the bound for R28/R39, did not.
         `mono` now travels with `rootOf`'s resolution instead of being re-derived at the call site, because
         the same receiver spelling resolves through `vars`, a field, a field-walk or a subscript element and
         only the answering branch knows which.

      *This is the swift analogue of the same trap rust hit at R4: an imported-supertype CHA is only safe
      with explicit carve-outs, and you find out how many by measuring, not by enumerating.*

      **RAW_VALUE_BASE_TYPES is NOT subsumed by erasure** — checked by removing it with the erasure gate in
      place, and `plainString(_ s: String)` reads Env via `Rank.lowercased`. They answer different questions:
      erasure is about the receiver's SPELLING, the raw-value carve-out is about Swift's inheritance clause
      being overloaded for a CONCRETE receiver that nobody monomorphizes.

      A/B for `02fb0ad`, 11 real Swift targets / 10 609 entries (pollen, candor-swift, swift-syntax,
      Alamofire, vapor, TCA, SQLite.swift, swift-argument-parser, console-kit, Files, swift-log): zero entry,
      effect, Unknown and unknownWhy deltas, and ONE traced change — TCA's `TransactionPublisher.receive`,
      whose `var upstream: Upstream` (`<Upstream: Publisher>`) was CHA'd over TCA's five local Publisher
      conformers though its one construction site passes a Combine `AnyPublisher`. Instrumented, the gate
      fires exactly once across all eleven: the trigger is real and this corpus barely exercises it.
- [x] **factory-bound receiver — the HONESTY half is CLOSED (`47bb69a`).** `let c = build(); c.fetch()` no
      longer reads pure: it discloses `Unknown[dispatch:untyped cross-package receiver]`. The claim above
      that "there is no evidence `c` came from the dep at all" was **wrong** — the callee name is right
      there, and `returns` failing to hold it is itself the evidence that it came from outside the target.
      Note what this does and does not move: `deny E Unknown[dispatch]` now flips, `deny Fs` does NOT. Half 1
      converts the cardinal sin into a disclosed gap; it does not recover the effect.
- [x] **factory-bound receiver — the DETERMINATION half — DONE, candor-swift `f537ac3`.** The rung is
      no longer blocked: SPEC §2 fixes `typeSurface.returns` and rust shipped it at `a1e53e7`. swift is
      the second engine to take it. Canonical fixture goes exit 0 → **exit 1** on `deny Fs`, single-tree
      control exit 1 in both arms. Every one of rust's four reverted defects is a requirement here with a
      mutation that was RUN and confirmed to fail a named test.

      **Swift's door into defect 1 is the NESTED TYPE, not the module.** `Conn` and `Mock.Conn` live in
      one module; a leaf-keyed surface makes them one string and the PURE `openMock()` charges the real
      client's Fs. A bare `-> Conn` written inside `enum Mock` means `Mock.Conn`, so the spelling resolves
      OUTWARD from its declaring type path and must match a declared path EXACTLY. `localTypes` keeps only
      the simple name, so a new `localTypePaths` was needed — the leaf-vs-qual distinction did not exist
      in the engine before this.
      - **The wrapper refusal needed the fixture to earn it.** `plainNominalTypeName` is stricter than
        `typeName`, which peels `Conn?` → `Conn`. The first fixture could not tell them apart; making
        `Conn` declare an effectful `map` and having each wrapper consumer call the WRAPPER's own `map`
        is what turned the rule into a test. `-> Box<Conn>` is the sharp row: `Box` IS a declared local
        type, so it is refused for being GENERIC, not for failing to resolve.
      - **PROTOCOL returns are published, and that is the swift-specific half.** `func make() -> Proto`
        is the commonest Swift factory; the key it forms names a requirement with no body and is answered
        only by an `interfaceUnion` entry. Asserted BOTH ways: dep scanned plain → the row must DISCLOSE
        (resolving it anyway would mean a guess answered the key); dep scanned with
        `CANDOR_WORKSPACE_CHAIN` → the row RESOLVES. Surface and union are layered, never redundant —
        the same layering the ts row records.
      - **Counts, not output** (item 8): producer 3 564 entries across 11 real targets (swift-syntax
        2 732, vapor 205, SQLite.swift 197, pollen 122, Alamofire 111); unchained A/B 0 gains/0 losses/0
        entry deltas with the new `typeSurface` key as the ONLY envelope change. Consumer: 5 chained
        consumers / 2 805 entries, 0 gains 0 losses, arm ENTERED 20 times, every one a `returns` miss —
        the same shape rust measured (408 crates, 2 hits, 406 misses).
      - **RESIDUAL — CLOSED, candor-swift `9a51e7f` + `74bed40` (2026-07-27). The guard is PROVEN.**
        As filed: a nested type's method was unreachable for the consumer, because the key is three
        segments and this engine's dep index carried only `pkg#leaf` and `pkg#tail2`. Swift now carries
        rust's prerequisite too — a third key shape `pkg#<full qual>`, NORMALIZED rather than raw (the
        one place swift is not rust: `tail2` already normalizes `.`/`::`, so pushing the raw qual would
        add a key no Swift call site can spell). Index 14 535 → 15 398 keys over seven real repos split
        one package per target; keys present before and absent after: 0; new ≥3-segment collisions 0,
        unlike rust's pgman 1 865 — swift's scanner emits no cfg-gated duplicates, so the fall-back-to-
        disclosure is unexercised here but stays required. The dedup is the whole safety argument and
        was mutated out: `viaFactory` loses its Fs and a bare free call goes ABSENT from the report (a
        ⟨0.21⟩ purity claim) — item 9b in its exact shape.
      - **The exact type-path match is now load-bearing, and the counterfactual was MEASURED rather than
        argued.** The fixture was written WITH the key, as instructed: `openForeign() -> Progress` names
        a type the package does not declare, a suffix match answers the nested `Mock.Progress` that
        merely shares its leaf, and the third key makes that guess LAND — the caller is charged an Env
        it cannot reach AND loses half 1's disclosure with it. The mutation fails that test and no other.
        **Then the interesting half:** with the key mutated back OUT and the suffix mutant left IN, the
        CONSUMER rows go green again and only a producer-side "publishes nothing" assertion fails. So
        what the key changed is not that a wrong answer can be OBSERVED — a producer assertion could
        always have seen that, and nobody had written one — it is that a wrong answer now LANDS. *An
        untestable guard is a hope; but "untestable" can mean "nobody wrote the cheap assertion" as well
        as "the mechanism cannot bite", and only the second is a real blocker. Say which one you have.*
        `-> any P` / `-> some P` returns are still refused; `any P` is erased and would be safe to admit
        later, `some P` is not.
      - **FOUND WHILE FIXTURING, reported not fixed:** `let c = openMock(); c.probe()` on a NESTED type
        does not resolve IN-SCAN either, so the new row has no single-tree control and the chained arm is
        now strictly BETTER than the unsplit one — candor-java `9ae68f7`'s smell, one repo over. The
        local returns/binder path does not carry a nested type path. Documented on the test rather than
        asserted, since pinning it would encode the gap as a requirement (item 7g).
- [x] **swift row 3 — ALREADY SOLVED by `interfaceUnion`; my characterisation was wrong (2026-07-26).**
      Recorded here as "NOT fixable locally" and "the strongest argument for `typeSurface.implements` in the
      whole queue". Both false. Measured:

          dep scanned WITH CANDOR_WORKSPACE_CHAIN=1 emits, unprompted:
              DepLib#Store.save ['Fs']  interfaceUnion: true
          consumer:
              go(_ s: any Store) { s.save() }   ->  ['Fs']        row 3, RESOLVED
              goFactory() { let s = build(); … } ->  Unknown[…]   row 2, the genuine `returns` case

      My earlier fixture scanned the dependency WITHOUT the flag, so I measured an engine that had not been
      ASKED and concluded it could not answer. The same experiment on java gave the same result (its
      consumer resolves a union entry with no code change), which is what removed `implements` from the
      queue. *When an engine "cannot" do something, check whether the feature that would do it was switched
      on.*
- [~] **Coverage granularity — CHARACTERISED, split into three arms, one worth fixing.**
      Full write-up + fixtures + measured blast radius:
      [COVERAGE-GRANULARITY-FINDING.md](COVERAGE-GRANULARITY-FINDING.md). The one-line item above
      conflated three mechanisms:
      - **A, dynamic** (`dep_classified` rust `scan.rs:836/1061/1252`; `kappaClassified` java
        `Candor.java:714/1719`): ONE *classified* call marks the whole package covered, deleting the
        `invisible` hedge from every other floored call into it — including packages the source
        deliberately left ledgered (`Rules.java:666`: "an unmodeled member … discloses `invisible` — the
        honest floor"). **A real defect, rust + java only.** Fixtures: rust `pnet_datalink`
        (`interfaces()` floors, `channel()` → Net), java `org.apache.commons.io`
        (`FilenameUtils.getName` floors, `FileUtils.readFileToString` → Fs). In both, the untouched
        function goes from `invisible:[pkg]` to **absent-from-report with `analyzed` counting it** — i.e.
        ⟨0.21⟩ *provably pure*, a positive claim. **FIX:** delete `dep_classified` / `kappaClassified` from
        the ledger filter; the reviewed prefix/crate list and §2 chaining remain the only coverage claims.
        Cost measured: java **422 methods / 18 692 (2.3%)** on warroot, **0** on petclinic; rust **0** on
        pgman/ebman/candor-rust (the mechanism can only fire on `pnet_datalink`/`pnet_transport` — every
        other crate name `classify()` matches is already in `CALIBRATED_*`). Wants a PART 4c sibling:
        adding a classified call into P must not remove `invisible:[P]` from an unrelated function.
      - **B, curated** (the reviewed name lists): four-way, and **SPEC §7 item 14 exempts it by name.**
        Making it per-call-site adds a hedge to **8.0% (pgman) / 14.2% (ebman) / 15.3% (warroot) /
        24.6% (petclinic)** of all analyzed functions — tokio handles, aws_sdk builders, chrono
        arithmetic, Struts beans. **Not adoptable.** swift already tried and reverted exactly this
        (`Driver.swift:732`, "rampant false uncertainty", sweep [33]/[36]). The right pattern for the
        sharp cases is java's structural Spring floor (`Candor.java:1724`), one library family at a time.
      - **C, chained** (`deps_idx.crates` / `depCoveredPkgs` / `coveredPkgs`): four-way and **SPEC §2
        chaining rule 3 mandates it.** The R5 fixture reproduces the confidence loss (control
        `go -> ['Env']`; unchained `go -> [] invisible:['deplib']`; chained `go` absent, no coverage
        field) but the fix is not granularity — it is distinguishing **keyed-and-missed** (a real purity
        claim; stay silent) from **could-not-form-a-key** (`c.fetch()` on an untyped receiver; should
        hedge). Today the `scan.rs:1033` guard means an unkeyable call never enters the join arm at all,
        so the two are indistinguishable at the ledger. Folds into R5/R6/factory-receiver.
      - ts and swift **refute** arm A outright: `kappaKnows` (`scan-core.mjs:234`) and
        `PLATFORM_MODULES`/`KAPPA_MODULES` (`main.swift:526`) are pure functions of the package NAME, and
        `depCoveredPkgs`/`coveredPkgs` are populated at report-LOAD time. No call site can move a package
        from uncovered to covered. Fixtures in the write-up show both arms identical.
- [x] **Conformance PART 20** pinning the boundary contract four-way — `3bd69ec` (java/rust/swift) then
      `08b796a` (ts joins). Verified-to-catch on each engine's row by unchaining that engine's consumer:
      the row goes DIVERGE and the suite FAILED while the others still match.
- [x] **PAPER1 §6.1b / PAPER2 §4.6b** updated through the four-way half-1 close. §6.1b now carries the
      three-row rule and swift's row 3 as the argument for the format rung; §4.6b carries the methodology
      claim that *disagreement* between implementations is where the generalisation lives. The headline
      claim stays SCOPED to a single analysed artifact — deliberately; see the reasoning in §6.1b.

## Done-ness

The vein is closed when, for each engine, the two-tree fixture matches its single-tree control on every
mechanism in the table, PART 20 is green and verified-to-catch, and PAPER1 §6.1b can be rewritten from
"currently false" to a bounded residual.

## Found while fixing round 2 — three items nobody asked for

Each surfaced by an agent working a different task, and each is recorded here rather than in a log because
each is actionable.

- [x] **THE REPORT IS NOT DETERMINISTIC — FIXED (candor-swift `23eafc2`).** `supertypesOf` is a
      `[String: Set<String>]` and Swift seeds Set hashing per process, so `.first(where:)` picked a different
      supertype per run. After: five runs on pollen give ONE report hash, byte-identical. Swept — every other
      `.first` in the driver is guarded by `count == 1` (deterministic by construction), and rust/ts/java were
      each checked directly and are already stable. The test asserts the PROPERTY (alphabetically-first wins),
      because two scans in one test process share a hash seed and a double-scan could pass while the defect
      was live; against the pre-fix build that property test fails 5 runs in 6.
      ORIGINAL REPORT: Four identical runs of the
      *unmodified* candor-swift binary on pollen disagree on `unknownWhy` for **14 functions** —
      `dispatch:CodingKey.self` vs `dispatch:String.self`, `dispatch:NSObject.results` vs
      `dispatch:MKLocalSearchCompleterDelegate.results`: an unordered pick among a class's several
      supertypes. Effect sets are stable; only the disclosure REASON churns.

      Why this outranks a single defect: **A/B on real code is the project's primary evidence**, and a report
      that differs from itself run-to-run injects noise into every diff. It cost one agent a false datapoint
      before it thought to run the control against itself. It also makes `gains` — the supply-chain
      effect-diff product — noisy between identical inputs, which is a product-facing bug, not just an
      internal one.

      Fix shape: sort the supertype candidates before picking, or emit all of them. Cheap. The reason it has
      survived is that nobody diffs a report against ITSELF, only against another version.

- [x] **REASON CLASS ACROSS THE BOUNDARY — FIXED (candor-java `6ab26e4`).** `DepFn` now carries
      `unknownWhy`, and the real cause was DUPLICATION: `crossDepJoin` reproduced `inheritDepFn` line for
      line instead of calling it, so the ⟨0.19⟩ class reached the task/HOF hand-off sites and not the
      ORDINARY call. Deleting the copy was the fix. Measured: `deny Net Unknown[reflect]` exit 0 → 1 on a
      consumer, while `deny Net Unknown[native]` stays 0 so the scoping still discriminates.
      ORIGINAL REPORT: A chained dep's Unknown loses its REASON CLASS, so `deny Unknown[reflect]` cannot bite across a scan
      boundary.** `DepFn` carries no `unknownWhy`, so an inherited Unknown classifies as `unresolved` with no
      class. The reason-scoped gate — a shipped ⟨0.19⟩ rung — is therefore silently inert at the boundary,
      which is exactly where a consumer most needs it. Additive fix: teach `DepFn` to carry `unknownWhy`.

- [x] **netClass fails open in the ORDINARY path — FIXED (candor-java `e24edd9`).** The marker is now
      derived from what a Net call YIELDED rather than from a list of owners, so it fails closed for idioms
      nobody enumerated; restricted to calls taking arguments, because a zero-arg call (`socket.close()`)
      carries no destination and is evidence of neither completeness nor incompleteness — an existing masking
      test caught that over-fire. Both directions pinned. Honest measurement: no jar among 60 sampled has a
      CERTIFIED netClass entry at all, so the corpus cannot price this; the fixture is the evidence.
      ORIGINAL REPORT: A function combining
      `new URL("https://sentry.io/x").openStream()` with `HttpClient.send(request, …)` reports
      `netClass: ["known-telemetry"]`. Each hostless idiom alone yields `unknown-host` via the empty-hosts
      branch, but that branch is per-function, so a literal sibling masks it. Same shape as the union defect
      `90af98f` fixed, one layer beneath it — and the union fix does not reach it.

## Found while VERIFYING `02fb0ad` and landing swift's typeSurface rung (2026-07-26)

Verification of `02fb0ad` was run in the OTHER direction, per item 0, rather than by re-running its A/B.
**It found two silent under-reports, both introduced or inherited by the erasure gate, and both invisible
to any corpus A/B** — each needs a name collision no measured target contains. The commit's own headline
result stands: its A/B, its five monomorphized rows and its three erased controls all reproduce.

- [x] **The ELEMENT-opacity flag outlived its block — candor-swift `71de627`.** `02fb0ad` made
      `enterShadowScope` save UNCONDITIONALLY, reasoning correctly that a `for x in xs` binder can now ADD
      to `monoNames`. It introduced a SECOND set, `opaqueElem`, and never added it to the save. Its stated
      invariant — lockstep with `arrayElem`, so a rebind cannot leave a stale opacity behind a fresh
      element type — is the CLEAR half of the discipline and is silent about the RESTORE half.

          func f(_ xs: [some Speaker], _ ys: [any Speaker], _ c: Bool) {
              if c { let ys = xs.filter { _ in true }; _ = ys }   // ys marked monomorphized
              for y in ys { y.speak() }                            // ys is the ERASED PARAMETER again
          }

      The block closes and the CHA stays suppressed for the rest of the body: `f` is ABSENT from the
      report, a positive purity claim about a function that performs Env. Control: rename the inner binder
      `zs` and it is `['Env']`. Fixed as a scope, not a clear — the other direction is asserted too, since
      dropping the flag re-opens the fabrication `02fb0ad` closed.
- [x] **A nested `func`'s PARAMETERS were not a scope — candor-swift `83cd607`.** Inherited from
      `d62dd69` rather than introduced by `02fb0ad`, but the same mechanism.
      `func outer(_ s: some Speaker) { func inner(_ s: any Speaker) { s.speak() } }` read silent-pure:
      `inner`'s receiver is an existential, the local conformers really are its witnesses, and the CHA was
      suppressed because the ENCLOSING parameter — three lines up, a different variable — is spelled
      `some`. Spell the outer one `any` and the identical body is `['Env']`. **This is the swift form of
      the leak candor-rust's R4 needed its THIRD carve-out for**, running the other way: value-bag's
      nested `impl Serializer` INHERITED the outer `&dyn`-ness and gained a fabrication; here the nested
      item inherits the outer opacity and loses a real reach. The nested signature's own opacity is
      re-applied so the mirror does not open.
- [~] **The erasure gate does not reach the LOCAL-protocol dispatch arm — REFUSED WITH NUMBERS, candor-swift
      `020add4`.** Both treatments priced: SUPPRESS costs 5 losses and 7 entries REMOVED (TCA's `_$willModify`
      goes from a disclosed `Unknown` to ABSENT) — disqualified, because the imported arm is safe only by being
      additive and here it deletes a disclosure. DISCLOSE costs 9 concrete effects → hedge. **The argument that
      settles it:** for an IMPORTED protocol the in-scan conformers are an arbitrary subset of the candidates;
      for a LOCAL one they BOUND them (TCA's `ScopedCore<Base: Core>` — all 8 in-scan conformers are legal
      instantiations and they compose), so the union IS the candidate set. That argument now lives in the code,
      replacing the citation of a note nobody wrote. ORIGINAL:
      `d62dd69`/`02fb0ad` gate the arm at `Driver.swift`'s imported-supertype CHA, which requires
      `!localTypes.contains(owner)`. A LOCALLY-declared protocol dispatches through a different path
      (`protoTyped`/`localProtocols` → `subtypesOf`), which never consults `opaqueRecv`. Measured on a
      one-package fixture: `localMonoParam(_ s: some Speaker)`, `<T: Speaker>(_ s: T)`, `[some Speaker]`
      elements and a `Relay<T: Speaker>` field ALL read `['Env']` from the effectful conformer, with the
      only call sites passing the pure one — i.e. the fabrication those two commits closed is still open
      through the far more common door (your own protocol, your own conformers).

      A `DeclCollector.swift` comment already says so ("the LOCAL-protocol arm above is untouched … see
      the note in SOUNDNESS-VEIN-crossing-the-scan-boundary.md") — **and that note does not exist**, which
      is item 9 exactly. It is recorded here now. Closing it is NOT a wider `if`: the local-protocol arm
      is what R28/R39 and the whole element-dispatch family run on, so suppressing it needs its own A/B
      and its own second-direction fixture.
- [x] **FIXED, candor-swift `7a4f977` — 289 bindings to 123, candor-swift's own 23 to 2.** Half 1's provenance conjunct fired on LOCAL methods and computed properties — measured while
      instrumenting the typeSurface consumer, which is the only reason it was visible. `localFreeFns`
      removes the local leak for FREE functions only; a bare call to a METHOD or a computed property of
      the enclosing type still looks like a dependency factory. All 20 half-1 triggers across five chained
      real consumers are of this kind — `closureParamNames`, `fnsFor`, `sortedPlaces`, `dayHourlyValues`,
      `withAnimation` — and not one is a dependency factory. Each gets a false
      `Unknown[dispatch:untyped cross-package receiver]`. False uncertainty, not a cardinal sin, so it is
      filed rather than patched; the fix is to widen the local-name exclusion beyond free functions.
- [x] **swift carried THREE copies of the chained-dep apply path and one had drifted — `84a71ea`.** Asked
      BEFORE adding the typeSurface consumer, exactly as this queue's rust (`7cb5748`) and java
      (`6ab26e4`) rows instruct. The chained-GLOBAL read applied effects/`hosts`/`cmds`/`paths` and
      dropped `tables`, `invisible` and `incomplete`: a consumer reading a dependency's effectful lazy
      global inherited the EFFECT and none of the dependency's honesty markers, turning "Fs plus a blind
      spot inside the dependency" into a fully-analysed `Fs`. Fixture-proven both ways; no corpus output
      changes, because no measured target has a chained dependency global carrying a disclosure. **Three
      engines asked, three engines guilty — the audit is worth running in candor-ts too.**

## Found in passing while landing the typeSurface rung (2026-07-26) — not boundary defects

- [x] **`candor-scan` PANICS deterministically on `getrandom@0.3.4` / `0.4.2` — CLOSED, candor-rust
      `4f7b704`, and the cause was a SPAN CROSSING A THREAD.** proc-macro2's fallback `Span` is a pair
      of byte offsets into a THREAD-LOCAL source map; candor parses on rayon workers and walks on the
      collector thread (`SendFile`). The contract was written as if candor were the only span reader —
      **syn's parser reads spans too**, and `visit_macro` hands it the moved token stream, where
      `parse_negative_lit` JOINs the `-` punct's span with the literal's. A `-1` in any macro body is the
      whole trigger. Fixed by `respan_call_site` at all four sites that re-parse moved tokens; the
      `a593197` containment stays. **`0.4.3` was crashing too** — nobody had looked.
      - The claim that it could not be reduced was about the setup, not the bug: parse on one thread,
        walk on a second FRESH one, and the panic is deterministic. Three fixtures, four mutants, four
        named failing tests.
      - The prior diagnosis was INVERTED, which is why removing `macro_template_blocks` changed nothing:
        `Span::call_site()` is `(0,0)`, the dummy file every thread's map is seeded with — always valid,
        and now the fix. (`macro_template_blocks` was already safe for a second reason: it re-parses from
        a STRING, which registers a file on the current thread.)
      - **The quiet half is the point.** Past the end of the walking thread's map the lookup panics;
        inside it, it silently resolves against an unrelated file. Instrumented over 121 crates: 88 927
        macro re-parses, **72.4% handed a stream this thread cannot resolve.** The A/B moved 3 crates of
        976 — the counts are the evidence, not the diff (item 8).
      - 976 crates, both arms hashed: panics 3 → 0, 21 gains, 0 losses, `unanalyzed` −3, 973 identical.
      ORIGINAL ENTRY:
- [~] **`candor-scan` PANICS deterministically on `getrandom@0.3.4` / `0.4.2`.** `proc-macro2`'s
      `Span::join`: *"Invalid span with no related FileInfo"*. Two things to fix, and the queue was right
      that the second matters more.
      - **BLAST RADIUS — FIXED, candor-rust `a593197`.** Contained per FILE and DISCLOSED through the
        ⟨0.21⟩ `unanalyzed` array, which also sets `had_parse_failure`, so a configured gate refuses to go
        green over the hole (`deny Fs` → exit 2, "policy NOT enforced"). getrandom now yields a real report
        naming `src/backends/use_file.rs` as unanalyzed, instead of no report at all. The fault is INJECTED
        for the test (`CANDOR_PANIC_ON_FILE`) because the real trigger needs a whole crate's parse state —
        the file scanned ALONE does not panic — and a containment nobody can fire is a containment nobody
        has checked. Both directions asserted: the surviving file keeps its effects, and the lost file is
        NAMED (absence from `functions` is a purity claim, so a dropped file with no disclosure is the
        cardinal sin wearing a crash).
      - **THE PARSE DEFECT ITSELF — CLOSED, candor-rust `4f7b704`, and my diagnosis was not merely wrong,
        it was INVERTED.** I wrote here that "synthesized `Group::new` spans are call-site spans with no
        FileInfo". `Span::call_site()` is `(0,0)` — the DUMMY FILE every thread's source map is seeded
        with, i.e. the one span that is always resolvable, and it is now the FIX (`respan_call_site`, at
        all four sites that re-parse moved tokens). The `macro_rules!` template path was already safe for a
        second reason — it re-parses from a STRING, which registers a file on the current thread — which is
        exactly why removing it changed nothing and should have told me the theory was wrong.

        The real cause is a SPAN CROSSING A THREAD. proc-macro2's fallback span is a pair of byte offsets
        into a THREAD-LOCAL source map; candor parses files on rayon workers and walks them on the collector
        thread. The code half-knew this — `fn_locs` runs inside the parse closure precisely because line/col
        only resolves there — but the `SendFile` contract was written as though candor were the only span
        reader. **syn's own parser reads spans too:** `parse_negative_lit` JOINS the `-` punct's span with
        the literal's, so a `-1` anywhere in a macro body is the whole trigger. getrandom spells it
        `debug_assert!({ match ret { 0 => true, -1 => …, _ => false } })`.

        It DOES reduce to a fixture, contrary to what I concluded: parse on one thread, walk on a second
        FRESH thread whose map holds only the dummy file. My "it needs whole-crate parse state" was a
        description of the rayon pool, not of the defect. Measured over 976 registry crates: panics 3 → 0
        (0.4.3 was crashing too), 21 gains, 0 losses. And the count that matters more than the crash —
        instrumented over 121 crates, **72.4% of 88,927 macro re-parses were handed a stream the walking
        thread cannot resolve**. The panic is the loud tail; the quiet form silently resolves a span against
        an unrelated file.
- [x] **`build.rs` fails clippy `collapsible_if` — CLOSED, candor-rust `0d63ead`, and the qualifier is
      gone.** The cause of the qualifier was never a preference: stable clippy cannot compile the
      `rustc_private` dylint lib at all, so the `-p` list was the only thing that could work, and
      `build.rs` (root package) fell outside it too. Nothing linted either, so 45 warnings had
      accumulated. Fixed by adding a SECOND leg rather than widening the list — `clippy` joins the pinned
      nightly's components in `rust-toolchain`, so the bare `cargo clippy --all-targets` resolves and CI
      runs it beside the stable one. Verified-to-catch: restoring the nested `if` reddens the new leg.
      - Worth carrying: the two clippy versions **do** catch different things — the stable leg then
        flagged a `doc_lazy_continuation` the nightly leg had passed. Keeping both is not belt-and-braces.
      - And a `clippy --fix` hazard: rewriting a `match` into `.map(…)` DELETED the comment on the `None`
        arm, which recorded why an unpinnable local `fmt` is treated as PURE rather than `Unknown`. That
        is a soundness argument, not decoration. Check every `--fix` diff for eaten comments.

## Residuals surfaced by the 2026-07-26 agent round (recorded so they do not live only in a transcript)

- [x] **ts's `interfaceUnion` CHA fan-out bound — DONE, candor-ts `fc8d297`.** Measured first: the fat tail
      is NOT the argument (44 arms over 353 targets; one with 70). The decisive finding was that rxjs's OWN
      `Observable.subscribe` reads `Unknown[dispatch:…Operator.call]` — the in-scan site declining the 70-way
      fan-out — while the report it wrote handed a chained consumer the smear. **candor published what candor
      refuses to resolve.** Past the bound: `['Unknown']` + `unresolved` + reason, never silence. ORIGINAL: candor-java added one (`429c7b2`) after a
      217-subtype smear: past a threshold a union stops being information, and java's answer was to drop to
      a DISCLOSED Unknown rather than emit the smear. The same hazard is live in ts. Measure the
      distribution before implementing — and note the bound must not silently drop the union and leave
      nothing, which would be the cardinal sin wearing a precision fix. *(in flight)*
- [x] **ts's union reads method SIGNATURES only — DONE, candor-ts `d9b8c34`.** A `run: (x) => void` member is
      a FunctionTypeNode with no name and no owner, so three sites keying on a declaration's name formed no
      key at all. Chained end to end: `@ukri-tfs/email#EmailService.send` `['Unknown']` →
      `['Net'] invisible:['@aws-sdk/client-ses']`. Also repaired 139 disclosure strings that named the
      PROPERTY as the owner type. ORIGINAL: so an interface member declared as a property with a
      function type (`@cucumber/cucumber`'s `IDefinition.getInvocationParameters`) is never unioned.
      Pre-existing, and shared with the in-scan arm. *(in flight)*
- [x] **rust dictionary values / `fieldArrayElem` — ANSWERED, candor-rust `a80bb15`, and the premise was
      wrong.** Probed with a `dyn` control per row: the container and field positions ALREADY thread the bound
      map and all resolve. The real gap was the local `let` ANNOTATION, and a parameter-position defect was
      hiding underneath it (a tuple destructure wrote both type maps and `vars` won). ORIGINAL: so they are
      inert — **correct by accident** (item 0b). If anyone adds bound resolution there for the reason R28/R39
      needed it, the erasure gate is needed at the same time. Swift recorded the same shape in its own code
      comments. *(in flight)*
- [x] **`@aws-sdk/client-sns` CJS-vs-ESM — REFUTED AS FILED, item closed.** The original finding was an
      artifact of its own method: `dist/cjs` and `dist/es` were scanned as SEPARATE roots with no
      `node_modules`, comparing DIFFERENT functions. Redone as one scan of the package root with
      resolution: 309 same-named units in both builds, `invisible` present in ESM only on 76 and in CJS
      only on **0** — and the cause is not candor. The ESM build IMPORTS `__awaiter`/`__generator` from
      `tslib` (56 files) and the CJS build INLINES them (5), so `invisible:['tslib']` is TRUE of the ESM
      body and its absence is TRUE of the CJS body. The 87-vs-1 `unknownWhy` gap has the same cause: the
      downlevel state machine adds `_a.sent`/`.apply` shapes the inlined form does not have. **Two
      different bodies, two correct answers.** ORIGINAL FILING:
  ~~**`@aws-sdk/client-sns` reads WEAKER in its CJS build than its ESM one**~~ — the ESM units name the
      packages they reach through `invisible`, the CJS units report the same reach as `Unknown`. The
      disclosure survives, so this is precision, not honesty; but a consumer's answer should not depend on
      which build of the same package it happens to load.

## Found while answering the swift generic-bound note (2026-07-26)

- [x] **rust HAS swift's "correct by accident" shape, and it is not where the note guessed — candor-rust
      `a80bb15`.** The note asked whether rust has a container/field position where a generic bound WOULD
      resolve but the code never asks. Answered with a probe crate carrying every dispatch position and a
      `dyn` CONTROL beside each row, because a silent row that is silent for a DIFFERENT reason looks
      identical.

      The container and field positions are **not** it: `Vec<T>`, `&[T]`, `HashMap<K,T>` and every field
      form already thread the bound map (R37b/R39/R40) and all resolve. The gap is the LOCAL `let`
      ANNOTATION — the one position Pass A cannot reach, and the collector had no bound map, so
      `trait_leaves` took a literal `HashMap::new()`. `let d: T = pick(); d.go()` under `fn f<T: Doer>`
      read silent-pure while the identical PARAMETER resolved, and while `let d: Box<dyn Doer> = x` —
      the same line, one spelling along — resolved too. The site was also missing `elem_trait_leaves`,
      `tuple_trait_leaves` and the `is_callable_type` map outright.

      **A PARAMETER-position defect was hiding underneath it** (bar item 0b): the tuple destructure wrote
      BOTH maps for a position — `tuple_types` yields the spelling (`"T"`), `tuple_trait_leaves` yields
      the bound — and `vars` wins at the call site, so the binding resolved to a type named `T`, which is
      nothing. The `dyn` spelling escaped only because `tuple_types` yields `None` for it.

      976 crates: 4 gains, 0 losses, entry +2, Unknown +3/−0. **Every gain is a disclosure, and every one
      is the existing 12-impl CHA bound reaching a receiver it could not see** — pinned by a fixture where
      the PARAMETER form of a 13-impl trait reads `Unknown` in BOTH arms, so the rung moved the position
      and not the rule. Six guards, six mutants, six named failing tests.

      Residuals pinned as a test rather than a comment, WITH the finding that makes them residuals: tuple
      INDEX access (`t.0.go()`), an unannotated rebind (`let v = xs`), and a factory return bound into a
      local are all still silent — and so is each one's `dyn` control, so they are POSITION-level gaps
      rather than this rung's "never asks for the bound". The test fails if one starts resolving.

## Closed by the swift round (2026-07-26 night) — three confirmed defects, and the design question behind them

An adversarial code review found three more. Two were the SAME failure the gate had already produced
four times, which is why the third patch was refused and the mechanism was fixed instead. All three
landed with two-direction fixtures, every guard mutated out and the failing test named, an A/B over 14
real Swift targets / 12 004 entries (0 gains, 0 losses, Unknown unchanged) and four-way conformance.

- [x] **A ternary's opacity was composed with `||` — candor-swift `663752a`, CARDINAL SIN.** `rootOf`
      types `cond ? a : b` from the arms' shared root; `mono` is what licenses SUPPRESSING the
      local-conformer CHA, so one monomorphized arm certified an ERASED sibling.
      `f(_ m: some Speaker, _ e: any Speaker, _ c: Bool) { (c ? m : e).speak() }` was ABSENT from
      `functions` — a ⟨0.21⟩ purity claim about a body that performs Env whenever `c` is false. Opacity
      licenses suppression, so it composes by CONJUNCTION. Three rows, because each alone is satisfiable
      by a wrong fix (mixed must dispatch; erased/erased must dispatch; mono/mono must stay suppressed).
      **Instrumented, the join fires 12 times across the whole corpus and every firing is
      ERASED/ERASED** — so `&&` and `||` are indistinguishable there and the corpus is the fabrication
      CONTROL, the fixtures are the evidence. The probe was NOT shipped: an env read inside `rootOf`
      charged Env+Fs to 26 of candor's own functions in its self-scan.
- [x] **`patternNames` listed three of the seven pattern kinds — candor-swift `42093b6`, CARDINAL SIN
      plus its mirror, and this is where the SET-OF-NAME-FLAGS DESIGN QUESTION got answered.**
      `for case let x?`, `for case .some(let x)`, `for case let x as T` and `for var x` never reached
      `shadowName`, so the enclosing signature's `monoNames`/`depBoundLocals` stayed on the loop's own
      unrelated binding: silent-pure in one direction, and a false
      `Unknown[dispatch:untyped cross-package receiver]` for a purely LOCAL value in the other (which
      flips `deny E Unknown[dispatch]` to exit 1 on clean code). Both reproduced before anything changed.

      **Is the name-flag side table itself the defect? Partly, and the useful answer is more specific
      than the question.** Of the six defects this gate has produced, exactly one (`71de627`) was a
      SAVE-LIST omission; two (`83cd607`, this one) are missing ENUMERATIONS — of scope forms and of
      binder forms; the rest are not scoping at all. Attaching opacity to the BINDING resolved at the
      point of use does not remove the enumerations, and it requires `vars` to become lexically scoped —
      which it deliberately is not (function-wide with clear-on-rebind, because a stale type is
      dangerous inward and merely lossy outward). Fusing the flags into `vars` WITHOUT that would make
      the flags leak outward the way types do, i.e. `71de627` permanently. So the full structural fix is
      a rewrite of the collector's binding model with its own A/B, not a safety refactor — **filed, with
      that cost, rather than attempted here.**

      What WAS done instead is the part that is structural at acceptable risk: the binder enumeration is
      replaced by a property of the PARSE TREE — a walk for every `IdentifierPatternSyntax` in the
      pattern subtree — verified exact in BOTH directions against SwiftParser rather than assumed (every
      bound name reaches one, including `let x?` through
      `valueBinding > expressionPattern > optionalChainingExpr > patternExpr`; and no non-binding
      pattern produces one — `for case konst in`, `case E.one(3)`, `case 1...2` parse to
      `declReferenceExpr`/literals, `_` is a `wildcardPattern`). Plus a catch-all
      `visit(IdentifierPatternSyntax)` that CLEARS any binder no specific visitor claimed, which
      **inverts the failure mode**: an unenumerated form now defaults to dropping a stale binding
      instead of keeping one. The MARKING carries the risk, not the clearing — removing the
      `OptionalBindingCondition` mark fails two OTHER suites, because the catch-all would wipe a genuine
      `if let` binding.

      **Scoping alone would have been a fix that changed nothing**, and only measuring showed it: these
      binders were never TYPED either, so a cleared flag left the same silent-pure answer by another
      route (both `…NoShadow` controls fail before the change). The two forms whose type needs no
      inference are now typed — `let x as T` and `let x?`; `.some(let x)` is REFUSED through that door,
      because a local enum with a case named `some` parses identically and the element type would be
      the enum rather than the payload.
      **And typing it made `vars`' documented outward leak bite** (standing bar item 0, mid-flight):
      `let c = depBuild(); for case let c? in xs {…}; c.speak()` typed the loop's `c` from the sequence,
      that type survived the loop, and the factory-bound receiver below stopped reaching half 1's
      marker — a disclosed gap turned into a silent purity claim by a fix aimed at the opposite defect.
      A loop binder's type is now restored at the loop's end, which closes the same leak for the plain
      `for x in xs` binder that always had it. **Measured live: 258 restores across 13 targets actually
      change a binding, with zero output delta.**
      Two more binder forms found by INSTRUMENTING rather than by reading the grammar: `for var x in xs`
      (a `valueBindingPattern` wrapping the identifier — the loop variable was never typed at all, 5
      corpus sites with an element type in hand), and `catch let e as MyError`, which matched a
      `DeclReferenceExpr` where the parser puts a `patternExpr > identifierPattern` and so never fired.
- [x] **`typeSurface.returns` gated the ENTRY lookup and never the ANSWER — candor-swift `6aa4635`,
      FABRICATION.** `depCallee` is a bare name (an idiomatic Swift call into a dependency carries no
      module), so every covered import of the file is asked the same fn key. Alpha publishing
      `build -> Alpha#Client` (whose `fetch` is Fs with `/etc/secrets` in `paths`) and Beta publishing
      `build -> Beta#Stub` (whose `fetch` is pure, so absent) made `surfaced` hold two types while `hits`
      held one — and the caller was charged Alpha's effect AND its path literal, with `unresolved` left
      false so nothing disclosed it. **rust's reverted defect 1 — a leaf-keyed collapse of two distinct
      types — reappearing ACROSS packages instead of within one.** §2 rule 1 is enforced within a report
      by `returnsAmbiguous` and nothing enforced it across the file's imports, where no single report can
      see the collision. Refusing falls back to half 1's disclosure.
      The SECOND fixture is what rules out the guard everyone reaches for: with BOTH packages imported
      and covered and only ONE answering `openAlpha`, the row must still resolve — a guard keyed on "the
      file imports more than one covered package" passes the colliding row and silently kills every real
      recovery in a multi-dependency file.
      Measured: unchained A/B byte-equal (the arm needs `CANDOR_DEPS` to be entered at all), so **three
      REAL chained consumers were built by resolving their SwiftPM dependencies and scanning each
      checkout** (candor-swift ← swift-syntax; console-kit ← 6; TCA ← 17): 964 consumer entries, 0 gains,
      0 losses, arm entered 4 times, every one a `returns` miss and 0 AMBIGUOUS. The trigger is real and
      no measured target exercises it.

## Opened by the swift round (2026-07-26 evening) — three real, one of them a live fabrication

*(the first is now CLOSED — see the section above.)*

- [x] **The erasure gate never reaches the LOCAL-PROTOCOL dispatch arm — MEASURED, and the answer is
      REFUSE TO GATE IT. The phantom citation is replaced by the argument (candor-swift `DeclCollector`).**
      The gate requires `!localTypes.contains(owner)`, so `some P`, `<T: P>`, `[some P]` and generic-field
      receivers over a *locally declared* protocol all charge every local conformer. Reproduced on a
      one-package fixture: five monomorphized forms all read `['Env']` from the effectful conformer while
      the only call sites pass the pure one, and the caller inherits it.

      **But the two cases are not the same question, and that is why the gate must not simply widen.**
      For an IMPORTED protocol the conformers in scope are an ARBITRARY SUBSET of the candidate set — the
      caller is in another module and may supply a type this scan has never seen, so unioning our few
      conformers is neither the true set nor a bound on it. For a LOCAL protocol they BOUND the
      instantiations, and where they do not (open hierarchy, unresolvable witness) `protoDispatches`
      already falls to a disclosed `Unknown` rather than to a partial union. The union is the sound
      over-approximation of a generic function, not a fabrication.

      Both candidate treatments measured, 14 real Swift targets / 12 004 entries; the trigger is 17
      monomorphized local-protocol dispatch sites (swift-syntax 4, Alamofire 4, TCA 7, SQLite.swift 1,
      console-kit 1) — small, real, and every one traced.
      - **Suppress the arm** (what the imported side does): **5 effect losses and 7 entries REMOVED**,
        and among them TCA's `_$willModify` goes from a disclosed `Unknown[dispatch:…]` to ABSENT. A
        purity claim manufactured by a fabrication fix — standing-bar item 0, disqualified outright. The
        reason the same treatment is safe on the imported side is that the arm there is ADDITIVE (it
        emits edges and never an Unknown), so suppressing returns to the pre-rung baseline; here it
        deletes a disclosure.
      - **Disclose `Unknown` instead:** nothing goes silent (Unknown 10 539 → 10 540, entry count
        unchanged) but **9 concrete effects degrade to a hedge**. The row that decides it is TCA's
        `final class ScopedCore<Base: Core>: Core { func send() { base.send() } }` — `Base` is bounded by
        `Core`, all 8 in-scan conformers are legal instantiations and they compose, so the union IS the
        candidate set and replacing it with `Unknown` trades a correct answer for a hedge.

      Residual, stated rather than hidden: candor does not specialize at call sites, so a generic function
      whose only instantiation in THIS program is pure still carries the union. That is general to
      caller-agnostic per-function analysis, not specific to protocols, and it is a true statement about
      what a public generic function can be asked to do.

      **The comment cited a justification in the vein doc that was never written** — standing-bar item 9
      with no code beneath it at all, which is worse than a wrong comment: the reader has no way to tell
      an argument from a citation of one. It now carries the argument and the numbers inline.
- [x] **FIXED `7a4f977` (same defect as the row above — the two filings were one item).** All 20 of swift's half-1 disclosure triggers on a real corpus were FALSE. Instrumenting the
      `typeSurface` consumer showed every one firing on `closureParamNames`, `sortedPlaces`,
      `withAnimation` — local methods and computed properties — because `localFreeFns` covers free
      functions only. This is over-disclosure, not the cardinal sin, so it is noise rather than a lie; but
      a hedge that is wrong 20 times out of 20 teaches a consumer to ignore the channel, and rust measured
      the same conjunct firing on `max()`/`min()` before narrowing it.
- [x] **FIXED — candor-swift `9a51e7f` (the key) + `74bed40` (the guard it makes provable), 2026-07-27.**
      Swift's index now carries `pkg#<full qual>` beside `pkg#leaf` and `pkg#tail2`, NORMALIZED rather
      than raw — the one place it is not a copy of rust's `5feba18`, since `tail2` already folds `.`/`::`
      and the raw qual would key a string no Swift call site spells. Additive with the dedup, both
      directions mutation-verified; 14 535 → 15 398 keys over seven real repos split one package per
      target, 0 keys lost, and 43 chained consumer reports byte-identical.

      **And the exactness guard IS provable now** — a suffix match publishes a nested type that merely
      shares its leaf, the third key makes that guess LAND, and the caller is charged an effect it cannot
      reach. But the useful result is the counterfactual, which was measured: with the key removed and the
      suffix mutant left in, the CONSUMER rows go green and only a producer-side assertion fails. **"The
      guard is untestable" was half true.** Nobody had written the cheap producer assertion, which needed
      no key at all; what genuinely needed the key was showing the guard is LOAD-BEARING rather than
      cosmetic. Two different claims, and this row conflated them. *When you file a guard as unprovable,
      say whether the mechanism cannot bite or whether the assertion was merely never written.*
      Full detail on the `typeSurface` row above.

## The 2026-07-26 adversarial review: 9 confirmed defects, ALL of them narrowings that went one step too far

A workflow review (4 finder angles, an independent verifier per location, 42 agents) over the whole day's
four-repo output. **Ten findings survived verification; nine distinct.** Every single one is the shape
standing-bar item 0 names — a change that narrowed a sound over-approximation to kill a fabrication, and
narrowed past a real reach. Two were mine, and both are in the fail-closed direction I had just claimed to
protect. *(All in flight 2026-07-26 evening.)*

**Cardinal sins (silent under-reports):**
- [x] **FIXED `39bbc8b`** — rust `scan.rs:663` — the contained parser abort (`a593197`, MINE) writes `fninfos: []` into the
      `--incremental` cache under the file's REAL content hash, so a warm run reuses it, skips the
      `catch_unwind`, emits no `unanalyzed` and no `had_parse_failure`, and a gate goes GREEN over a file
      whose effects were never derived. **I converted a fail-closed crash into a cached, reproducible false
      all-clear.** The asymmetry that proves it: a round-1 parse failure `continue`s BEFORE the cache write
      and re-discloses every run.
- [x] **FIXED, candor-java `9f8e71c` — and the review named two sites; there were FOUR, one of them every
      polymorphic dispatch candor resolves.** java `Candor.java:3673` (`9ae68f7`, MINE) + `:2810`
      (`dd81bfa`) — single-queue BFS over `directSupers` interleaves the superclass chain with interfaces by
      DEPTH, so a nearer `interface` default settles a descriptor and suppresses the superclass body the JVM
      actually runs (JLS 15.12.2.5 / 8.4.8: **the class wins**, at any depth). I added per-overload shadowing
      to stop dropping inherited bodies and dropped a different one. Both halves failed at once: the real
      `Fs` dropped AND the interface's empty effects charged in its place.

      **The instruction to reuse `Cha.nearestConcreteSuper` rather than write a third walk was right about
      the shape and wrong about the helper.** That helper — which `chaTargets` and `monomorphicTarget` both
      end in — walked `transSupers`, a **HashSet**, and returned the first `declaresConcrete` hit in HASH
      order. It was not ordered wrongly; it was not ordered. `nearestDepFn` was the fourth. All four now
      share ONE traversal (`Cha.resolutionOrder`), so this vein's fourth drifted copy of a walk was not
      written. *A cross-site precedent tells you where a walk belongs, not that the walk is correct.*

      **Most of the damage was CLASS-vs-CLASS, not class-vs-interface** — the narrow reading would have
      fixed the ordering and left the unordered helper in place. Over 45 real jars the answer changed
      **11 277** times: **11 193** where the new owner is a proper SUBTYPE of the old (a near override was
      losing to a far base), and **84** the reported interface-default shape. Traced to bytecode both ways:
      spring-core `ResourceDecoder.decode` `[]` → `['Log','Unknown']` (it resolved to `AbstractDecoder`'s
      `throw new UnsupportedOperationException()` instead of the `AbstractDataBufferDecoder` body that
      runs); guava `AbstractStreamingHasher.putLong` `['Clock','Log','Unknown']` → pure (charged through an
      `AbstractHasher` chain a `final` override replaces — the fabrication mirror).

      Nine chained pairs: consumer side 0 gains / 0 losses / identical Unknown counts — and per item 8 that
      is a claim about the experiment until instrumented: `nearestConcreteSuper` differs 5–531 times per
      pair while the dep-facing walks are entered 8–30k times and differ **zero**. The boundary defect is
      real (fixtures) and rare on real library pairs. Full record: SOUNDNESS-LOG 2026-07-26.

      **RESIDUAL, and it is the next rung here:** `ReportWriter.writeHierarchy` records a dep type's
      supertypes as a sorted `TreeSet` with no superclass marker, so a chain lying ENTIRELY inside a
      dependency stays depth-ordered. The consumer's own classes state their superclass and interfaces
      separately, which is why the shape the defect was found in resolves exactly. Closing the rest = a
      sidecar key whose value is an OBJECT (`Loader#loadDepHierarchy` already skips non-array values, so an
      older consumer ignores it, and a sidecar without it keeps today's answer). A format rung with its own
      compatibility surface — it wants its own measurement, so it did not ride.
- [x] **FIXED, candor-java `c583da7`** — java `ReportWriter.java:499` — `mergeUnionInto`'s `unchanged` test
      compared each widened `TreeSet`'s SIZE against the original LIST's size; those agree only while no
      list holds a duplicate, so a genuine widening could land on the same count, read as "no change", and
      drop the union — the entry then claiming a narrower effect set than the dispatch reaches, under the
      exact hash a chained consumer keys on. The review could not confirm it and was right not to:
      **established NOT reachable** (every list field of an ordinary entry is materialised from a sorted
      `TreeSet` in `writeJson`, and `real` is always an ordinary entry). Fixed anyway — the size test was
      right for a reason it did not state, leaning on an invariant three hundred lines away that a later
      change would break silently and in the miss direction. Since no corpus can reach it, the UNIT test is
      the evidence: it feeds the duplicate directly, asserts both directions, and restoring the size
      comparison fails it and, across all 512, only it.
- [x] **FIXED `663752a`** — swift `CallCollector.swift:384` — a ternary receiver composes opacity with `a.mono || b.mono`, so a
      `some P` / `any P` ternary claims full monomorphization and skips the CHA for the ERASED arm. Needs `&&`.
- [x] **FIXED `42093b6`** — swift `CallCollector.swift:805` — **the third scope leak**, arriving through the PATTERN not the scope:
      `patternNames` returns `[]` for optional/expression/enum-case patterns, so `for case let x? in` never
      shadows and an enclosing `some P` parameter's flag stays attached to an unrelated erased binder.
- [x] **FIXED `9196c89`** — rust `collector.rs:907` — `mem::take` blanks `generic_bounds` inside a nested `fn` and never installs
      the nested signature's own bounds, so `fn inner<T: Doer>(d: T) { d.go() }` resolves to nothing. The
      commit's fixture asserted only the FABRICATION direction; the second fixture was never written.
- [x] **FIXED `651c9f9` (and the brief was wrong — see below)** — ts `scan.mjs:1631` — the module unit's wire key changed shape with **no engine-version bump**, and
      §2.1 staleness keys on `candor.version`. A SAME-version consumer over a new report finds no key, is not
      told it is stale, and reads the import as pure. The comment above `depInitCell` asserts this cannot
      happen; the code does not implement that (item 9).

**Fabrications:**
- [x] **FIXED `90655d9`** — ts `scan.mjs:3884` — `typingsRoots()` returns null past a 128-file cap and the caller degrades it to
      `[]`, so a large package loses the whole typings arm INCLUDING its role as the ambiguity evidence —
      restoring `d7060ca`'s fabricated-Net / dropped-Fs / `deny Fs`-green defect for exactly the packages big
      enough to hit the cap. **A truncated census must make the affected names REFUSE, never make them
      confident.**
- [x] **FIXED `6aa4635`** — swift `Driver.swift:828` — the `typeSurface` consumer keys a BARE callee across every covered import
      and checks only that the ENTRY lookup is unambiguous, never that the `returns` answer was. Two packages
      exporting `build` → one silently wins, and the caller is charged the other's `Fs` and its path literal.
      **The reverted rust attempt's defect 1, reappearing ACROSS packages instead of within one.**
- [x] **FIXED `67d092d` (NOT by porting java — see below)** — ts `scan.mjs:4062` — the union is DROPPED where java MERGES (`48a5f18`), so a narrow real entry
      replaces the dispatch union including its `['Unknown']` fan-out disclosure.

**REFUTED and worth knowing:** the "fourth unpatched `respan_call_site` site" — the `macro_rules!` template
path re-parses from a STRING, which registers a file on the current thread, so it was already safe. That is
the second time that path has been wrongly accused today.

### What the review says about the METHOD, which is worth more than the nine fixes

1. **Nine for nine.** Not one confirmed finding was a fresh mechanism; every one was a guard added THAT DAY
   that fired on the wrong thing or failed to fire. The fabrication/under-report boundary is not a place
   where defects are *likely* — on this evidence it is where they *are*.
2. **Authorship is no protection.** Two are mine, written while holding item 0 in mind, and both are in the
   direction I had just argued I was protecting. The rust one is worse than the bug it fixed: a crash is
   fail-closed, a cached empty result is not.
3. **The same defect keeps recurring through a NEW DOOR.** The reverted rust leaf-key join came back as a
   module-relative return type, and now again as a cross-package bare callee. Three doors, one defect.
4. **A cap or a refusal must land on the PUBLISHING side, never on the EVIDENCE side.** ts's typings cap and
   the union's drop-on-collision are the same error: refusing to gather evidence lets a confident wrong
   answer through, where refusing to publish would have been safe.

### rust's two review defects — CLOSED, and the fix corrected the finding's own shape

`39bbc8b` persists the abort IN the cache entry (`FileCache::aborted`, schema rev8) and replays it, rather
than refusing to cache. The argument that decided it: **replaying assumes exactly what reusing the FnInfos
already assumes** — same content hash AND same decl index ⇒ same walk ⇒ same outcome — so it is gated on
both, and a decl-index move sends the file back through the walk. Verified by me in both directions: with
content and decl index unchanged the abort REPLAYS (gate stays exit 2); the moment the walk re-runs clean
the abort CLEARS (`unanalyzed: []`, entries 1→2, gate back to a real exit 1). The clearing guard is the
MIRROR SIN and needed its own fixture — *a cached abort that outlives a clean re-walk is a gate that can
never go green.*

`9196c89` — **the review's finding was right about the cause and wrong about the shape, and probing before
patching is what showed it.** A nested `fn inner<T: Doer>(d: T) { d.go() }` is NOT fixed by the bound map:
its `dyn` control (`fn inner(d: &dyn Doer)`) is equally silent, because a nested item's PARAMETERS are
never typed at all — a position-level gap, now pinned as a residual with both controls. What the blanked
map actually bites is the `let` ANNOTATION inside the nested item. Three rows fixed (nested fn, nested impl
block, nested impl method); re-installing `dyn_sig_traits`/`trait_quals` was REFUSED, because the only
position they could bind to is the untyped-parameter one that does not resolve anyway.

**And the agent caught item 9 in its own work:** its "REPLACE, not merge" comment was an assertion nothing
checked — the merge mutant passed the entire suite. Pinning it needed a deliberately NON-COMPILING fixture,
because rustc's E0401 makes the two indistinguishable on anything that compiles, and candor-scan analyses
crates without building them. That is a genuinely new corner of item 9: *a guard can be untestable on valid
input and still matter, because this analyser does not require its input to be valid.*

## PRE-RELEASE BLOCKER opened 2026-07-26 — the build-id lockstep vs §2.1

candor-ts is at build **0.23.2**; the rest of the family is at **0.23.1**. `candor/bin/release-preflight.sh`
check [4] demands all self-declared build versions agree and now FAILS:

    ✘ build versions DISAGREE (a hand-maintained constant lagged the release): 0.23.1 0.23.2

**Both sides are right, which is why this needs a decision rather than a patch.** §2.1's staleness gate keys
on the per-engine BUILD id, so an engine that changes a wire key MUST bump it or every protection that gate
arms stays disarmed — that is why candor-ts `651c9f9` bumped. Check [4] exists to catch the opposite failure,
a hand-maintained constant that LAGGED a release, and its message assumes that is the only way the versions
can differ. Under [[candor-three-axis-versioning]] the build id is explicitly per-engine, so lockstep is a
release convention, not a contract.

Two resolutions, and the choice is Tom's because it is a release-shape decision:
- **release the family together**, bumping all four to 0.23.2 — preserves the convention, costs nothing
  technically, and is what the ladder has done to date;
- **relax check [4]** to compare each build id against the REQUESTED release version rather than demanding
  mutual equality — which is what the check's `WANT_VER` arm already does one line below.

Nothing is published, so this blocks a release and nothing else. **Do not resolve it by reverting the ts
bump:** that would re-disarm §2.1 on the very engine whose wire key moved.

### All nine review defects are closed — and four of the nine briefs were wrong about the fix

Worth recording, because the pattern is now consistent enough to plan around: **the review located every
defect correctly and mis-stated the remedy in four of nine.** In each case probing before patching is what
separated them.

| defect | what the brief said | what measurement said |
|---|---|---|
| java BFS | two sites | **four** — and the unnamed one, `Cha.nearestConcreteSuper`, walked a `HashSet`: not ordered wrongly, **not ordered**. 11,193 of 11,277 changed answers were class-vs-class, not the reported interface shape |
| rust nested bounds | a nested `fn`'s parameter | the parameter is never typed at all (its `dyn` control is equally silent) — the map bites the `let` ANNOTATION |
| ts wire key | bump the version | **no version can close it** — §2.1 rewrites the CONTENT of keys a report carries and can never conjure a key it lacks. The fixable half was elsewhere: an untrusted report still granted COVERAGE, so every key it lacked read pure |
| ts union drop | port java's `mergeUnionInto` | java merges into an interface's own `default` BODY; TS interfaces have no bodies, so the literal port charges a class its own union and fires the producer's `deny Net` on it |

The two that were right as stated (swift's ternary `||`, swift's pattern binders) are the two smallest.
**A verified finding is a verified SYMPTOM.** The verifier's job is to prove the failure is reachable; it is
not to design the repair, and a brief that hands over the reviewer's proposed remedy as if it were settled
will get it built.

### rust's five-shape sweep — 3 of 5 PRESENT, and the worst one was where it was predicted

The sweep hypothesis (a shape found in one engine belongs swept in all four) paid immediately.

- **1. An untrusted report still grants coverage — PRESENT, `069b4c0`.** The predicted one, and the worst.
  §2.1 downgraded a stale report's effects to `Unknown` while the same load registered its package in
  `DepIndex::crates` — the set that EXEMPTS a crate from the κ ledger. So every function the distrusted
  report did not mention became a purity claim with `invisible`, `coverage.uncovered` and the stderr line
  all gone. Split into `crates` (the join gate) and `untrusted` (the claim that silence is informative).
  Measured on real trees restamped to a previous build: ebman 483→584 entries with 389 `invisible` gains
  and **13 crates re-entering the ledger** (`ratatui` at 2977 calls, silently claimed covered); pgman
  195→244. **Verified independently:** a consumer calling a PURE dep fn under a stale report now discloses
  `invisible: ['deplib']` + `coverage.uncovered: [deplib]`, where it previously read as a clean purity claim.
- **2. An unordered walk — ABSENT, now pinned `b16dd38`.** `resolve_target` filters on `v.len() == 1` — it
  REFUSES rather than picks — and the dep index removes colliding keys. **The never-guess rule that
  prevents fabrication is what makes it order-independent**, which is a nice structural result. Gate added
  (123 targets × 5 runs byte-identical, with a probe confirming `RandomState` really reseeds). Note the
  agent's first fixture COULD NOT WITNESS the property — its hits came from a walk-ordered `Vec`; it needed
  a type implementing two traits with differing defaults to reach a genuinely hash-ordered container.
- **3. A disclosure lost to a cache — ABSENT-BY-ACCIDENT, closed `34e425e`.** The abort/ordering paths are
  sound, but `MergedDecls` has 17 fields and the digest hashed 16 (`deref_target` missing). It costs
  nothing ONLY because the deref chase reads it live rather than baking it into an FnInfo — every other
  receiver-typing rung of the last month landed in `CallCollector`. **The reflective guard that promised
  "add a field → the build fails" could not deliver it** (two hand-maintained lists, so binding the field
  `_` restored the build). One macro now generates both.
- **4. A trust marker failing open — PRESENT, `e429a0e`.** ts's exact shape is impossible (`unresolved` is
  derived), but the ⟨0.19⟩ reason class was lost instead: `deny Unknown[indirect]` exited 0 on a function
  whose dep report NAMED `indirect`. Partial, which is why it survived — bare `deny Unknown` and
  `[dynamic]` both fired; only the class-targeted middle, which is how the ratchet is adopted, read green.
- **5. A flag outliving its scope — PRESENT, `05d0ee9`.** `fn f(s: &dyn Store) { for s in 0..3 { s.go(); } }`
  charged `f` with `Fs` on a `u8`. **`scoped_var` DID clear `vars`, and `vars` is read before `trait_vars`
  — so every TYPABLE shadow is masked by precedence and looks perfect**; only a shadow that types to
  nothing exposes it, and the agent's five typed-shadow fixtures all passed. Instrumented: 72,872 binder
  calls, 116 shadowing a live entry, **76 hitting the exact precondition** on named real crates (cap-std,
  clap_builder, h2, ignore) — latent, one effectful impl away from being charged.

**Deliberately not fixed, and correctly:** rust emits `ambiguous:same-name local defs` — outside the closed
§4 vocabulary — **757 times across 253 crates**, and PART 10 misses it because the harness's own fixtures
never produce that kind. Renaming is not free: `callback:` moves the class Dispatch→Indirect and WEAKENS
`deny Unknown[dispatch]`. Wants its own measurement and probably the spec's migration mechanism.

### java's five-shape sweep — 2 PRESENT, 2 absent-by-accident closed, 1 structurally absent

- **1. An untrusted report still grants coverage — PRESENT, `7e41327`.** The same defect rust had, in the
  same place: `loadCrossDeps` registered `depCoveredPkgs` from a report whose effects it had just
  downgraded. The three-arm fixture is the sharp bit — **the STALE arm was byte-for-byte the FRESH arm, and
  `app.S.go` vanished from `functions` entirely**, with the arms differing only in the build id. Measured
  over 7 chained `~/.m2` pairs: httpclient +629 entries, +633 `invisible`, 13 packages back in the
  envelope, 0 effect losses. **Item 0 fired for real:** the one-set fix cost 2 disclosed Unknowns on
  logback-classic with no `invisible` to replace them, because `ch.qos.logback` is a κ-curated prefix — so
  `depCoveredPkgs` (trust-gated) and `depChainedPkgs` (ungated) are now separate sets, both directions
  mutation-verified.
- **2. An unordered walk — NO soundness instance; one WITNESS instance fixed `54350bf`.** Every
  effect-owner selection is a monotone set-union or an existential boolean, hence order-invariant. The one
  that could differ is `Policy.reachesScope`, which picked the AS-EFF-009 `via` witness by DFS over a
  HashSet-seeded stack — and `--gate-json` PUBLISHES that witness. Now nearest-first: verdicts identical on
  5 real jars, and for all 452 jgit violations the new witness is **107 strictly nearer, 0 farther**. The
  agent explicitly declined to call this a soundness defect, which is right.
- **3. A disclosure lost to a memo — no live hazard; one ABSENT-BY-ACCIDENT closed `2b606ee`.** All 14
  memos traced. `depDeclaresSigElsewhere` latched `built` unconditionally — safe only via a property of its
  CALLER, while both its siblings guard directly.
- **4. A trust marker failing open — PRESENT, `2f7479a`, AND IT IS A HOP FURTHER OUT THAN THE BRIEF SAID.**
  `unresolved` does not fail open; the REASON CLASS does, one hop past `6ab26e4`: a dep unit whose Unknown
  was itself INHERITED publishes no `unknownWhy`, so in A→B→C the reason never reaches A.
  `deny Net Unknown[reflect]` went exit 1 single-tree → **exit 0 chained**, while bare `deny Net Unknown`
  fired throughout — only the class-targeted middle read green, and that middle is how the ratchet is
  adopted. No format rung needed; `calls` already held the chain.
  **RELAYED and MEASURED against rust: rust is CLEAN on the second hop** — a three-package fixture
  (C originates `callback:unresolved call`, B chains C, A chains only B) carries the reason all the way to
  A. So java's "rust/ts/swift very likely have the same gap" is FALSE for rust. ts and swift are testing it.
- **5. A flag outliving its scope — ABSENT, structurally.** `MethodScan` never escapes its loop iteration;
  every context mutation is an owner-qualified insert into a whole-scan accumulator. 12 real jar pairs,
  12/12 byte-identical under a reentrancy selftest.

**Two found off-brief, both real:** `--parallel` ignored every target's `.candor/config` while its own
documentation promised byte-identity (`4ddbd3c`), and `test/smoke.sh` had pinned shape 1 as a REQUIREMENT
(`640630b`) — see standing-bar item 7g.

### swift's five-shape sweep — 4 of 5 PRESENT, the richest of the four

- **1. An untrusted report still grants coverage — PRESENT, `308ad15`. THE VEIN IS NOW 4/4.** ts found it,
  and rust, java and swift all had it. Swift's reproduction is the clearest statement of the defect:
  a call into a dep API the report lacks reads `invisible: ['RatesDep']` unchained, and goes **absent from
  `functions`** the moment a STALE report is chained — the κ ledger and the verdict's `coverage` field fall
  silent with it. The fix is a SPLIT, not a drop (chained-but-not-covered); gating the join on coverage
  instead — the obvious one-liner — fails FOUR named tests, three of them the stale-downgrade rows.
  Live: console-kit's 6 dep reports restamped → +29 `invisible`, **18 functions back from absent**, 0 losses.
  Instrumented rather than assumed where it showed nothing: TCA/candor-swift dep reports name SwiftPM
  PACKAGES (`swift-case-paths`) while imports name MODULES (`CasePaths`), so nothing is covered in either
  arm — **a separate pre-existing gap, reported not fixed.**
- **2. An unordered walk — PRESENT in a different guise, `196e125`.** Java's "picks in hash order" form is
  absent (sorted since `23eafc2`). What is present is `23eafc2`'s SIBLING in the code written after it:
  five runs of ONE binary over Alamofire under `CANDOR_WORKSPACE_CHAIN` produced **five report hashes**
  carrying the same 879 union entries in five orders — on the cross-package PUBLISHING path.
- **3. A disclosure lost to a cache — PRESENT, `43a0eaa`.** No incremental cache, but `--workspace`'s
  `.candor/deps` IS a disk cache: a child scan that FAILED was silently skipped and the previous run's
  report stood in. Warm vs cold on identical source: `useDep` absent from `functions` vs
  `invisible: ['DepLib']`. Sweeping alone was insufficient — children share the cache, so the fixpoint
  re-runs once after sweeping.
- **4. A trust marker failing open — ABSENT for `unresolved` (0 failures over 12,004 entries, 10,539 with
  `Unknown`); PRESENT one layer over, `eb0250e`** — and at HOP 1, not hop 2 as java predicted. Building the
  three-package chain to check the relay exposed a SECOND defect underneath: **`reasonClass` tested
  `dynamicMemberLookup` for EQUALITY while the engine emits `kind:detail`, so `Unknown[reflect]` was
  unsatisfiable even single-tree.** A dead parallel `unresolvedSet` (written 7×, read 0×) was
  absent-by-accident and removed (`c5929e3`).
  - **CROSS-ENGINE CONSEQUENCE, verified and fixed by me in java (`d9b07b0`).** The same equality test is
    in candor-java `ReasonClass.java:70` and candor-ts `policy.mjs:20`. Swift emits
    `dynamicMemberLookup:<root>.<prop>` and never the bare token, so neither could ever match a real one.
    REFLECT and UNRESOLVED are both in the `dynamic` set, so a bare `deny Unknown` fires either way — what
    silently dies is `deny Unknown[reflect]`, the form the ratchet is adopted in. **candor-ts is still
    OPEN** (its repo had an agent working in it); the fix is `startsWith`, monotone, with both the
    `kind:detail` and bare rows pinned.
- **5. A flag outliving its scope — the catch-all inversion VERIFIED with a working negative control; two
  uncovered maps still leaking, fixed `c77038f`.** `protoTyped` and `localConstStrings` were covered by
  neither `clearBinding` nor `shadowName`, both FABRICATING, each isolated by a rename control. The obvious
  placement cost Alamofire's `URLRequest.init` its disclosure. The filed binding-model rewrite was
  re-priced: **verdict stands** — the catch-all removed the binder-form enumeration; this is a different one.

**Job 2:** half-1 false triggers fixed (`7a4f977`) — 289 bindings → **123**, candor-swift's own 23 → 2, with
a PRE-EXISTING residual found doing the same thing one conjunct earlier (`returnsIdx` is bare-name keyed
package-wide), pinned as a test asserting today's behaviour with instructions to flip it. The
full-qualification dep-index key (rust's prerequisite 0) was **not attempted** and remains open.

**Two method traps, both the agent's own and both worth carrying:** a test suite **passed three mutants**
because its rows used `-> Int` methods a pre-existing conjunct already excluded, so the new guards were
never reached — *a test that cannot reach the code it names is not a test*. And standing-bar item 7c(b)
claimed its second victim: `git checkout <file>` to undo a one-line mutant reverted uncommitted work, and
three measurements ran against a half-applied change.

### ts's five-shape sweep — 2 PRESENT (both SIBLINGS of its own already-fixed defects), 3 absent

ts is the engine that FOUND shapes 1 and 4, so its job was the harder question: is the fix complete, and
does the shape have other doors here? Both answers were no, and finding that is the case for sweeping an
engine against its own defect rather than ticking it.

- **1. PRESENT — a NEW door, `21277eb`.** A report that declares ITSELF incomplete (non-empty ⟨0.21⟩
  `unanalyzed`) still registered full coverage. A dep with one unparseable file scans to **exit 0** with a
  report that still names its package; the consumer's call to a declaration that file held went from
  `invisible:['deplib']` unchained to **absent from the report** — and the single-tree control is **exit 2**.
  **Chaining an incomplete report was strictly WORSE than not chaining it.** Treatment deliberately differs
  from staleness: entries are kept (they were derived from source it DID read), only the silence hedges.
  Item 0 fired: withholding coverage silently replaced half 1's unanswerable-key `Unknown` with the κ
  hedge, taking `deny Fs Unknown[dispatch]` from exit 1 to 0 — both voices now speak.
- **2. ABSENT, with a real structural argument.** Java's defect was a `HashSet` with no order at all; JS
  Maps/Sets are insertion-ordered, so the live question is whether insertion order is MEANINGFUL — and at
  every decision point it either is (TypeScript's source-ordered `members`/`declarations`), or is sorted
  before `[0]`, or is unioned, or the never-guess counter drops BOTH candidates.
- **3. ABSENT for the memos.** `depEntryCache`/`pkgNameCache` are pure functions of key + a filesystem that
  does not change mid-run; the program/checker is built once, after all cross-dep state is final.
  **ABSENT-BY-ACCIDENT, filed:** `.candor/dep-inits/` and `.candor/deps/` are never cleared, so a package
  whose rescan throws is served from the PREVIOUS run's file while the code comment claims it "is skipped".
- **4. PRESENT — a NEW sibling, `acbd79b`.** `netClass`. `hosts` is a lower bound and `unknown-host` is the
  producer's published judgment that it IS one — and the join copied the literals but not the judgment. A
  dep entry reading `['known-telemetry','unknown-host']` arrived as `['known-telemetry']`, and
  **`deny Net[unknown-host]` went exit 1 → exit 0** against a control that is exit 1 in both arms. The
  invariant is now ASSERTED fail-closed in the writer (`95dc3bc`): `Unknown ⇒ unresolved`,
  `direct Unknown ⇒ non-empty unknownWhy`. It fires nowhere on 42 reports / 22,978 entries, and is
  verified to catch (a mutated producer exits 2 and writes nothing).
- **5. ABSENT, structurally.** Every module-level mutable map keys on node/symbol identity or on a
  MODULE-QUALIFIED name, so two same-named functions in two files cannot collide — confirmed with a
  two-file fixture rather than asserted.

**The relay landed: ts HAD java's second-hop gap (`826571c`).** `deny Unknown[reflect]` exit 1 single-tree
→ exit 0 chained, at one hop AND two. Two process notes from it worth keeping: **the agent's first gate
measurement was wrong and its own negative control caught it** (`deny Net Unknown[reflect]` reads as "Net
OR Unknown[reflect]" and fired in every arm), and item 0 fired again — restricting the recovery to entries
with no reason of their own under-carried, and the original fixture could not notice.

**The malformed-reason blocker is RESOLVED, and the way it was resolved is the point.** The queue said ts
must not move a shape's class unilaterally and should ask the other three. The agent asked *by running all
four engines* on owner-less function values: rust `callback:unresolved call`, java
`callback:…Function.apply`, swift `callback:fn` — all class `indirect`. SPEC §4's dividing line is
normative and explicit, and PART 10 already asserts every `dispatch:` carries `owner.member`. **candor-ts
is the outlier; the reclassification moves it toward the family AND the spec, and needs no spec change.**
Correctly not landed — it narrows a gate and wants its own A/B. New datum: `826571c` makes the malformed
string travel across the boundary, so its blast radius is wider than the 68 measured.

### Phase-4 corpus round on UNSEEN code (2026-07-27) — the invariant holds at scale

Run after the sweep, on code none of these engines had been pointed at during the vein's work, to test the
two things the sweep just changed: that the getrandom-class parse containment holds across breadth, and
that the trust-marker invariant the sweep asserted is actually true on real output rather than on fixtures.

| engine | targets | entries | carrying `Unknown` | marker violations |
|---|---|---|---|---|
| rust  | 60 registry crates (excluding every crate named in this vein) | 18,485 | 420 | **0** |
| java  | 40 `~/.m2` jars (excluding every pair used in this session) | 22,270 | 13,644 | **0** |
| ts    | 4 real dependency-bearing projects | 207 | 121 | **0** |
| | | **40,962** | **14,185** | **0** |

The invariant tested is the one candor-ts asserted fail-closed in its writer (`95dc3bc`) and rust
asserted at its apply site: **an entry carrying `Unknown` must carry the marker that says so** — a
non-empty `unresolved`/`unknownWhy`. 14,185 opportunities to fail, zero failures, on code the assertion was
never written against.

Also: **60 rust crates, zero parse aborts.** The `respan_call_site` fix (`4f7b704`) had been verified on
the three getrandom versions that crashed; this is the breadth check it did not have. Note what this does
NOT show — the quiet form of that defect (a span resolving against the WRONG file rather than panicking)
is invisible here, and the 72.4% precondition rate measured at the time says it is common. The loud tail is
closed; the quiet body is disclosed and unmeasured.

Three ts targets returned **exit 2 with "no TypeScript sources"** — correct fail-closed behaviour on a
project whose sources are elsewhere, not a defect, and worth stating because a run that silently produced
an empty report there would be the exact false all-clear this vein exists to prevent.

### Verified independently (not taken on report)

- **rust's fresh-vs-stale REFUSAL is correct.** I built the two-report fixture myself: with a FRESH and a
  STALE report for one package chained, rust's consumer reads `go []` **with `invisible: ['deplib']` and
  `coverage.uncovered: [deplib]`** — unresolved but HEDGED, which is the honest answer. Aligning to the
  other three engines' fresh-wins would grant coverage while the never-guess rule still drops the colliding
  key, converting that hedge into a confident purity claim over an `Exec` the FRESH report names. java and
  ts can afford fresh-wins because their entry-level conflict KEEPS an answer (java last-wins, ts merges
  into a Set); rust's drops. **The divergence is real and rust is the correct arm** — so this closes as a
  refusal, and the two-direction fixture asserts the PREMISE (that the key really is withdrawn) so the
  argument re-opens if that ever changes rather than silently outliving itself.
- **Two findings the agents produced that outrank their own fixes**, both about tests rather than code:
  java's every-dep-fixture-used-`()V` (no reference type, hence no descriptor slash — the suite agreed on
  an accident), and rust's old `warm2` arm, which was **the assertion pinning the latch** it was meant to
  guard. That is standing-bar item 7g's third occurrence: a test can hold a defect in place.

## OPEN — found by verifying the review round (2026-07-27, me, not an agent)

Chasing candor-swift's handover ("two reports carrying an IDENTICAL entry withdrew the key as ambiguous —
rust and java should check it") turned up a confirmed cardinal sin in rust, a clean negative in java, and
one deeper defect underneath both that is NOT fixed.

**CLOSED, candor-rust `6f2210c`** — two IDENTICAL entries under one key were withdrawn. Measured both ways
on one fixture: one report chained gives `go = ['Exec']`; the SAME report chained twice gives **ABSENT, no
`invisible`, no coverage hedge**. java is CLEAN (last-wins keeps an answer) — verified directly, not
assumed. A/B free: pgman 0/0/0, ebman +2 entries recovered from absence.

- [D] **DECIDED — see THE QUEUE §5; may be dissolved entirely by the collision ruling.** A WITHDRAWN KEY READS AS SILENCE AT THE ORDINARY CALL JOIN — and `a1e53e7` says it must not.**
      Two TRUSTED reports that DISAGREE about one function leave the consumer ABSENT from `functions` with
      no `invisible` and no coverage hedge: a confident purity claim assembled out of the index's refusal to
      answer. This is the three-row rule (PART 21) one level down — at the INDEX rather than at the receiver
      — and `a1e53e7`'s own commit message states the requirement verbatim: *"a miss on an exact key still
      cannot distinguish 'no such method' from 'the index withdrew an entry', so it must fall back to
      disclosure, never to silence."* The `typeSurface` consumer implements it; the ordinary call join does
      not, because the withdrawn-key set is local to `load_dep_reports` and never reaches a consumer.
      **Standing-bar item 9 — a comment stating a justification the code does not implement — in a commit
      message rather than a comment.**
      I BUILT the fix (expose `withdrawn` on `DepIndex`, disclose `Unknown[dispatch:withdrawn ambiguous
      dependency key]` on a miss against it) and verified all five directions. **Not landed**, because it
      costs 30 of pgman's 200 functions and 108 of ebman's 544 newly carrying `Unknown` — 15-20%, the same
      order as the false-uncertainty flood the coverage-granularity finding measured. That is a design
      decision, and I am not making it unreviewed at the end of a long session in exactly the class of
      change two consecutive reviews have found defects in.
      **The disagreements are REAL and one of them is alarming**: `backtrace#fmt` has one entry claiming
      `["Env","Unknown"]` and another claiming PURE. Silence there matches the wrong one. Measured
      distribution of collisions: pgman 2041 withdrawals, 1536 effect-agreeing / 505 effect-disagreeing;
      ebman 3276, 2255 / 1021.
- [ ] **The effect-agreeing majority could be merged instead of withdrawn.** 1536/2041 and 2255/3276
      collisions are entries whose effect sets are IDENTICAL and whose literal surfaces merely differ;
      unioning the surfaces is the sound over-approximation. Measured cost: 24/200 and 108/544 functions
      newly carry `Unknown` — because the entries recovered are ones the DEPENDENCY could not resolve, so
      this is disclosure the consumer was previously denied rather than noise. Filed with the numbers.
- [→] **INDEXED at THE QUEUE §2.** THE FOUR ENGINES DO THREE DIFFERENT THINGS ON AN ENTRY COLLISION** and nothing pins it:
      rust WITHDRAWS, java takes LAST-WINS (it picks — which the never-guess rule forbids elsewhere), ts
      MERGES INTO A SET (unions effects). Whatever the right answer is, three answers cannot all be it, and
      a `deny` gate gives different verdicts per engine on the same two reports. Wants a conformance part
      once the decision above is made.

### swift's `boundLocals` row — the repro EXPLAINED, and it inverts the previous reading

The deliverable was the explanation, and it arrived: **the vanishing units were the fabrication, not a lost
reach** (13-line repro, traced end to end — see new standing-bar item 1b). The previous round's two
sub-cases that "pointed opposite ways" are ONE defect arriving through two channels: the 173 were
fabrications removed in the EFFECT channel, and a chunk of the 305 were the same fabrications removed in
the DISCLOSURE channel. Reverting was right; the missing step was knowing that a withdrawn `invisible` is
not a withdrawn reach.

**Landed (`083f370`, `5c42ad2`):** enum-case payload bindings register in a separate, lexically scoped
`casePayloadLocals`. A/B over 13 packages / 11,924 entries: 0 gains, **8 fabricated call edges removed, 13
manufactured `invisible` disclosures withdrawn, 1 fabricated `Unknown` withdrawn** — every one traced
(Alamofire's `AuthenticationInterceptor.adapt` → its own `credential`; `UploadRequest.task` → the unrelated
`DataRequest.data`; TCA's `TypeSyntax.identifier` reported as its own caller).

**Three refusals, each pinned as a fixture**, and the first is the one to keep: putting payload names into
the FUNCTION-WIDE `boundLocals` is 0 gains / 15 changes but **drops a genuine edge** (swift-syntax's
`IfConfigDiagnostic.asDiagnostic` binds `syntax` in three `if case` blocks and then reads the real
`self.syntax`) — a silent under-report manufactured by a fabrication fix, item 0 caught in the act.
Scoping `boundLocals` itself was refused because the Driver reads it ONCE, after the walk, where a restored
set is empty — **a post-hoc guard has no lexical position.**

One mutant `started life unable to fail` (its edge came from `globalReads`, which no guard it touched
consults) and was rewritten until it could — the third instance this week of a test that cannot reach the
code it names.

- [ ] **swift chaining is INERT when a package's name is not its module's** — reproduced `399433c`, filed
      not fixed, and the filing explains why the one-liner is a CARDINAL SIN. Two-package fixture: dep
      manifest `name: "swift-dep-kit"`, target `DepKit` → chained and unchained reports are BYTE-IDENTICAL.
      Rename the manifest to `DepKit` and the same code resolves `['Fs']`. Cause: `pkgName` is both the
      envelope `package` and every entry `hash` prefix, while every consumer lookup is keyed by an IMPORT.
      **The tempting fix — emit module names in the already-consumed plural `packages` — grants COVERAGE
      without moving the entry keys, so the consumer withdraws its `invisible` and finds nothing to replace
      it: silence read as purity.** The key half moves the report's primary join key, is
      baseline-invalidating, and the conformance chaining fixtures use package == module so they would not
      notice. Wants its own session.
- [ ] **two residuals un-masked by the fix, filed not patched:** the Driver's guard is "bound ANYWHERE in
      the unit", so `let location = location(converter:)` loses a real edge (`Note.debugDescription`); and a
      bare read of a PARAMETER charges the enclosing type's same-named property (`TokenKind.fromRaw`),
      hidden today only by an accident of the monotone set.

### rust's three rows — the door closes FOUR-WAY, and two refusals with decisive numbers

**TASK 1, the incomplete-report door — CLOSED (`dbab8be`), and rust is the only engine where the corpus is
EVIDENCE rather than a fabrication control.** java saw 0 of 11 real dep reports declaring `unanalyzed`,
swift 0 of 34; rust sees **4 of 855** (0.47%, two crates) and 1 of 200 crates.io crates cold. The live case
is as sharp as this shape gets: **`signal-hook-registry` 1.4.8's entire `src/lib.rs` fails to parse**,
leaving a two-function report that nonetheless vouched for `signal_hook::PendingSignals::add_signal` —
whose body is `unsafe { signal_hook_registry::register_sigaction(…) }`, i.e. installing a signal handler.
Now `invisible: ['signal_hook_registry']` plus a ledger row. ARMED across all 855 reports: +123 entries,
**+278 functions gain `invisible`**, 0 gains, 0 losses.
- Per java's warning about anchors: rust registers coverage from four sites but all funnel through ONE
  `cover` closure and coverage is consumed at exactly one place — **counted, not assumed**.
- One mutant DELETED a guard: the `!stale &&` conjunct failed nothing, because `cover`'s `else if` already
  decides it (item 8c, a guard that cannot be observed).
- **Refused swift's `subtract(coveredPkgs)`**: rust drops a key two entries disagree under, so complete-wins
  makes it read confidently pure — `63bbe87`'s argument, same shape.

- [x] **CLOSED FOUR-WAY — ts `26a89fc`, swift `6de5169` (mine).** ts and swift failed OPEN on a MALFORMED `unanalyzed` manifest (present but not an array). java fails
      closed and rust adopted java's reading. A report carrying `"unanalyzed": "oops"` is therefore read as
      COMPLETE and its silence buys full coverage — the door `21277eb` closed for the well-formed case,
      reopened by a malformed one. Relayed to the live ts agent; **swift remains.**

**TASK 2, `ambiguous:` — REFUSED, and the number is a deletion rather than a narrowing (`4817b71`).**
With `ambiguous*` → `indirect`, `deny E Unknown[dispatch]` goes from **58 of 200 crates.io crates to 0 of
200**, and exit 1 → 0 on all three projects — because rust's only OTHER `dispatch:` needs a chained dep. The
filed "757 across 253 crates" was a large undercount: censused over 1062 reports it is **8710 of 19607
entries**. Landed instead: PART 10 now scans a purpose-built fixture that PRODUCES the kind, tolerates it
with a WARNING, and carries a vacuity floor.
- [→] **FOLDED into THE QUEUE §1, symptom 1.** THE SPEC CONTRADICTS ITSELF HERE, and that is the real rung. SPEC §6.2's class table (line 1433)
      explicitly lists `ambiguous*` under `dispatch` — so the emission is BLESSED there — while §4's kind
      vocabulary omits it from the closed list of four. One section names it, the other excludes it.
      Reconciling them is a spec change, not an engine change, and it should be made before any engine
      renames anything.
- [ ] **Filed by the same pass:** every `dispatch:` rust AND swift emit at the half-1 site is dot-free — a
      canonical kind with a malformed normative detail, and §4 says an untyped receiver is `callback:`
      anyway. Wants a four-way ruling. Also: that arm's candidate set includes methods a bare free call
      cannot reach — 156 of 930 emissions have ≤1 free candidate, 48 have none (bare `drop(x)` is the
      prelude fn, charged 36 times).

**TASK 3, the quiet span half — CONFINED, measured (`fc71bc9`).** **24,008 of 24,008** non-synthetic `loc`
strings across 200 crates pass an oracle that opens the named file and checks it declares the function —
and **the oracle was calibrated rather than trusted**: permuted locs flag at 84.5%. 800 scans across four
rayon thread counts are byte-identical, and a seeded control (moving `fn_locs` out of the parse closure)
PANICS on 57 of 60, so the failure mode is loud by nature. **Two instrument errors caught and recorded
rather than shipped, both pointing the flattering way**: a first oracle whose 2,523 "wrong lines" were all
doc comments, and a first differential whose "0 differing" compared two arms that had both panicked to
empty files.

### ts's three rows — and the last fail-open closed four-way

**The by-reference HOF arm (`1960979`) was a BOUNDARY defect, not the precision gap it was filed as.** The
single-tree control came back `['Fs','Unknown']` with `deny Fs` exit 1 in BOTH arms: the LOCAL half of the
same argument list was charged all along (the local edge arm sits ABOVE the guard, the dep charge below),
so **one call, one position, one argument got two answers depending only on which tree the referent lived
in.** Filing it as precision was generous to it.
- **It answered the question I asked, with a measurement rather than an opinion:** the three-valued
  treatment ALONE does not separate a genuine callback from a fold's seed — `reduce(xs, cb, depWrite)`
  declares `seed: any`, exactly as silent as a real `fn: any`, and that mutant fails 5 named tests. The
  separator is a SECOND question the same signature answers: the name map describes the METHOD form, so
  when parameter 0 is positively a collection the receiver has moved into argument 0 and the map is wrong
  by exactly one place.
- **Two guards were written, measured, and REMOVED** — one failed nothing AND was actively wrong on
  `groupBy(xs: any[], key: string)`; the other was provably unreachable. Removing a guard you cannot
  justify is as much the job as adding one.
- Numbers worth keeping: the predicate's first version **fired 68 times on ukri-tfs and was wrong all 68**
  (TypeORM's `EntityTarget<T>` is a union with a `string` arm, and `string` carries `[Symbol.iterator]` —
  hence `every`, not `some`). And `checker.isArrayLikeType(any)` is TRUE, which without an exclusion pulls
  the receiver slot into the map and silences the `thisArg` denylist landed one commit earlier.

**The uncleared caches (`95d0b8b`) reproduced in the CARDINAL-SIN direction**, with a lever that is an
ordinary published shape: the walk excludes `*.d.ts` AND `*.min.js`, so a typings+minified package exits 2
while still resolving for its consumer — **5 real packages in the corpus exit 2 for this reason**. Run 2
served `useHot = ABSENT` for a body calling `fs.appendFileSync`, `coverage.uncovered` null, stderr silent.
An earlier arm carried `unknownWhy: ['callback:x.trim']` — **a reason class naming a deleted body.** Fixed
via DERIVED ownership (a file candor would have overwritten on success is the file it removes on failure),
so hand-placed reports survive and still chain. **The stderr assertion caught a defect in the fix itself**
— the sweep removed the right file and named the wrong directory, with report and exit code green.

**The aws-sdk row keeps its REFUTED status with the cause corrected:** the CJS build does not INLINE the
tslib helpers — `__awaiter`/`__generator` appear in 9 ES files and **0** CJS files, and the CJS twin uses
native `async`/`await`. It is a downlevel-TARGET difference, not an inlining one, and 41 of the 56 imports
are `__extends` rather than the named helpers. A refutation whose stated cause is wrong is half a
refutation.

### Verified independently, rust's round (2026-07-27 evening)

**The gate defect is a MONOTONICITY failure**, which is a sharper statement than the review's. Reproduced
by me post-fix, bracketed by both single-call controls — that bracketing is what makes it monotonicity
rather than a missing case:

| consumer body | `deny Unknown[unresolved]` |
|---|---|
| the REASONLESS dep fn only | exit 1 — the §6.2 absence fallback answers |
| the REASONED dep fn only | exit 0 — correctly `dispatch`, not `unresolved` |
| **BOTH** | **was exit 0, now exit 1** |

**Adding a call removed a class.** The pre-existing fixture could not see it — its consumer calls ONE dep
function, so the class set was empty and the fallback answered — **and it still passes under the mutant.**

**MY CHECK 1 WAS RIGHT, and it was a SECOND CARDINAL SIN in my own `6f2210c`.** Derived `PartialEq`
compares `Vec`s element-wise and order-sensitively, so the exemption decided "the same claim restated" by
**SERIALISATION** rather than by the claim: two reports making an identical claim with a differently-ordered
`hosts` vector were still withdrawn → absent entry → purity claim. Fixed in the TYPE (all eight `DepFn`
fields are `BTreeSet`s), on the argument that `apply_dep_fn` folds every field into a set anyway — so
set-equality is not a relaxation of never-guess but its exact statement.
- The corpus is a **fabrication control, not evidence**: 0 set-equal-but-not-vec-equal across 72,490
  collisions, because §2.1 admits only same-version reports and this writer emits from `BTreeSet`s — *and
  that is a crate version, not a build id.*
- **ARMED** (every report re-chained with array order reversed): pre-fix pgman **loses 7 entries**,
  `persist_draft_to` and `persist_history_to` vanishing with `['Clock','Fs']`; ebman 47 changed. Post-fix
  identical to unarmed.

**MY CHECK 2 — true in substance, one word wrong.** The three set writes do appear exactly once each inside
`cover` and are consumed at one place, but *"read nowhere else in the engine"* is FALSE: `load_dep_reports`
reads both again for its two stderr disclosures. The argument is now a test that DERIVES writes and
consumers from the source instead of asserting them.

- [→] **FOLDED into THE QUEUE §1, symptom 2 — and it is the one that reaches the theory paper.** All four engines: a report cannot say "Unknown, and one of them has no reason" beside a
      reason it does have.** §4 has no kind for it (which is why the invented one was removed), and §6.2's
      rule is per-function and keyed on ABSENCE, so it does not compose. A second-hop consumer re-derives
      `dispatch` alone. This is a §4/§6.2 rung, not an engine fix.

## §2f — the SECOND gate review (2026-07-28): it confirmed the first and found three the first missed

Two independent reviews of the same verb. The overlap is the useful part: where both landed on the same
defect, the finding is not an artifact of one reviewer's angle. Where the second found something new, it is
because it probed a channel the first did not.

**CONFIRMED by both, already dispatched:** rust's count-0 byte-equality break; rust's incomplete-analysis
swallowing the violation *and deleting it from the document*; java's and swift's `gate --report` printing
the forbidden literal with zero bytes on stderr; the four-way scoped-`Unknown[C]` fail-open.

**NEW in the second review, and the sharpest is MINE:**

1. **The policy parser says "ignoring policy rule" while KEEPING and silently re-scoping it.** Two
   directions, one false disclosure. `deny Unknown[corp]` — sole unrecognised token — empties the filter and
   **widens** to a bare `deny Unknown`, having just announced it was ignoring it. `deny
   Unknown[dispatch,nativ]` — a typo BESIDE valid tokens — is silently dropped and **narrows** to
   `[dispatch]`, so it no longer gates native-caused holes while the operator reads a gate that looks armed.
   **I specced this asymmetry deliberately and my reasoning was false:** I argued a dropped policy token can
   only widen, so the failure is loud. It does both, and the narrowing half is the common case — a typo
   lands beside correct tokens far more often than alone. **RULED `382a7e0`:** both sides refuse.
   *Still to implement four-way.*

2. **The FOURTH CHANNEL — `.candor/config` `unknown-alias` moves the verdict, and no engine's MUST-NOT test
   covers it.** The three documented baits are all covered; this one was not even a candidate. Worse than
   the coverage gap: **the two routes anchor differently** — every gate verb at the policy file's dir, every
   scan route at the target — so byte-equality is breakable by a file that is neither report nor policy.
   **RULED `99eb4e9`:** vocabulary anchors at the policy on both routes, and a config that participated MUST
   be named in the document. *Still to implement four-way, plus a fourth bait in all four MUST-NOT tests.*

3. **A refusal writes NO document, so a CI wrapper re-reads the PREVIOUS run's verdict as current.** Uniform
   four-way and defensible in isolation, which is why neither engine's authors saw it — the hazard is not in
   the exit code, it is in what the file on disk says afterwards. **RULED `107755b`:** a refusal writes a
   document that is fail-closed to a naive reader (`ok:false` + `refused:true`, and NO `violations` key,
   because an empty array is exactly the claim a refusal cannot make). *Still to implement four-way.*

Also new, lower: java's prefix locator gates only ONE of several matched reports (engine-wide, pre-existing,
but the workspace prefix is this verb's use case — dispatched); a present-but-unparseable `unanalyzed`
dropped by rust, and by ALL FOUR in the bare-string-list shape (ruled `38ba3e2`, dispatched); a
pre-⟨0.21⟩ report emitting `analyzed:{count:0}` — the exact token that now means "judged nothing" — to a
machine consumer; swift's verdict using `modules` where the other three use `packages`.

### What the second review is worth, beyond the three findings

It **cleared two things the first could not**, and the clearances are load-bearing:

- The MUST NOT holds four-way **under a stronger test than any engine ships** — `CANDOR_DEPS` set, a
  `.candor/config` `deps` key in FOUR directories at once, a `.callgraph.json` naming the absent function
  and edging it to an `Fs` unit, and a `.hierarchy.json` — `deny Fs app.ghost` exits 0 on all four, and the
  negative control (same baits, effect written INTO the report) exits 1 on all four. Absent stays absent.
- **Byte-equality is real and non-vacuous in both new engines**, reproduced live on scan-produced reports
  rather than inferred from the test suites.

And it found the weakest link is **java's** in-repo byte-equality test, which compares only violation count
and exit code, while conformance PART 27's byte-diff is three policies over a three-function `Fs` fixture —
so the four fields §3.1 names in the byte-equality MUST are pinned by the NEW engines' own suites rather
than by the shared gate. **The reference engine has the weakest test of the property it is the reference
for.** That is a conformance gap, not an engine bug, and it belongs to me.

### Standing bar, 7m

**When two engines disagree, the reference engine is not automatically the right one.** On both contested
`gate --report` questions this week the answer was **candor-ts**, and java was changed to match it. The
reference engine is the one whose behaviour the spec was WRITTEN FROM, which makes it the most likely place
for an unexamined assumption to have been promoted to a rule. Adjudicate from the clause, not the pedigree.

## OPEN, four-way, opened by CORRECTING MY OWN RULING (2026-07-28) — violation dominates refusal

`7271c69`. I pinned `refusal (2) > violation (1)` in `107755b`, ratifying what all four engines measurably
do, and it was wrong inside the hour. If a rule FIRES on evidence the report carries, `Reject` is
upward-closed (Lemma 2), so however the unanswerable rule would have resolved **cannot un-reject it** —
exit 1 is *certain*, not merely fail-closed, and it names the violation where exit 2 does not.

The harm is concrete rather than taxonomic: a refusal writes no `--gate-json` document, so refusing over a
firing rule **deletes a certain violation from the machine-consumer channel** — the same harm as
candor-rust's incomplete-analysis path, which this very rung is making it fix. Measured: `deny Fs` (firing)
plus one unanswerable scoped rule → **exit 2 with no document on rust, java, ts and swift alike.**

- [ ] Implement violation-dominates-refusal four-way, with the refusal message still disclosing which
      rules could not be evaluated.
- [ ] Implement the refusal document (`ok:false` + `refused:true`, **no `violations` key**) four-way.
- [ ] Implement the policy-side class-token refusal (`382a7e0`) four-way.
- [ ] Implement the config anchor + its disclosure (`99eb4e9`) four-way, and add the **fourth bait** to all
      four MUST-NOT tests.
- [ ] A conformance row for the precedence itself. It cannot be `deny Fs` alone — the row must carry a
      firing rule AND an unanswerable one *in the same policy*, or it tests neither.
- [ ] **java's byte-equality test is the weakest of the four** and java is the reference engine: it compares
      violation COUNT and exit code only, while PART 27's byte-diff is three policies over a three-function
      fixture. The four fields §3.1 names are pinned by the NEW engines' suites, not by the shared gate.

### Standing bar, 7n — how I got the precedence wrong, because the shape will recur

**I took uniform four-way agreement as the contract and wrote the clause to match.** In the same session I
had used monotone denial to argue engines should answer MORE questions rather than fewer, and then failed to
apply it one screen further down. Agreement between implementations is already recorded here as the weakest
signal available; what this adds is that **it is weakest of all when it agrees with the draft you were
about to write** — at that moment it stops being evidence and becomes confirmation. The tell was available
and I walked past it: the behaviour I was about to bless deletes a finding from the machine channel, which
is the exact harm I had spent the morning making rust fix.

## java's round — CLOSED (`92a7891`, `6c64835`, `2cdc443`), and it corrected the brief

All four dispatched items landed; 596 tests / 0 failures, counted from the XML rather than from "BUILD
SUCCESSFUL", and each new test verified to fail at its parent by stashing only the main-source file.

**The prefix locator gated ONE of several matched reports** — `m3/rep` exited 0 with `analyzed.count 3` and
zero violations where rust and ts both exit 1 with count 4. **The scope decision is the interesting part,
and it went the other way from the obvious one:** fixed on the GATE ROUTE ONLY, not in the engine-wide
resolver. Every other verb derives per-report *sidecars* from the resolved path (`callers`/`tour`/`whatif`/
`fix` all call `loadCallgraph`), so unioning entries while the callgraph stayed anchored to one report would
answer "no callers" for every sibling's function — **a silent under-report introduced by the repair.** The
gate reads the report file and nothing else, so a union there is a pure function of the located set with
nothing to desynchronise. It is also the only verb whose output is a machine verdict, which is where the
narrowing is invisible; the prose verbs keep their `matches N reports; using X` disclosure, and the gate
route *replaces* that line rather than keeping it, since it would now be a false disclosure. Join is the
safe direction throughout: counts SUM, `unanalyzed`/κ concatenate, a repeated `fn` UNIONs.

**The partially-corrupt set closed as a consequence** and the agent added no second guard — re-measured
after the locator fix, `multi/rep` exits 2 naming the torn file and the parse position. Asked to check
before writing, it checked, and reported the redundancy instead of shipping a guard that would have looked
like a fix.

**THE BRIEF WAS WRONG ON `interfaceUnion`.** I passed on the first review's claim that `scan --policy`
exits 0 while `gate --report` exits 1. Measured: **both exit 1.** The divergence is an extra violation ROW
in the document — scan 2, gate 3 — so byte-equality is refuted either way on the engine's own output, **but
a CI gate keying on the exit code would never have caught it.** That distinction is the finding, and it is
sharper than the one I sent: this rung's whole premise is that the DOCUMENT is the machine channel and the
exit code is not.

### The residual java did NOT patch around, and was right not to

The MERGED arm. Where a real entry already claims the hash the union is merged into it and the entry stays
unmarked *by design* — it is a real analysed unit counted in `analyzed`, and marking it would make consumers
subtract it twice. Measured on an effectful `default` method plus an overriding implementer: scan 1
violation, gate 2. There is no marker to key off, and the report cannot distinguish a widened entry's body
effects from its dispatch union, so **skipping by "the hash names an interface member" would drop a real
`default`-body violation — trading a fabrication for the cardinal sin**, which is the exact move
[[feedback-fabrication-fixes-cause-misses]] exists to forbid. It needs a four-engine format rung. It fails
safe as it stands: an extra row, never a missing one. Recorded in java's BACKLOG.md.

## rust's round — CLOSED (`ff34070`, `a88a562`, `464c682`, `6175f3d`), and it caught its own overreach

428 tests (426 before), clippy clean, 51 byte-equal gate-equivalence rows, every new test verified to FAIL
against stashed pre-fix sources.

**The incomplete-analysis fix was two bugs of one shape, on two routes.** candor-query ran the manifest
branch first with `write_verdict(&mut [], …)`; candor-scan returned from `had_parse_failure` *before*
`record_gate_violations`, and `write_gate_json`'s exit-2 arm hard-coded `&mut none`. Both printed the
AS-EFF-006 lines to stderr and then deleted the findings from the document — **only the machine consumer
was lied to**, which is the channel that gates the PR.

**Why the existing CI could not see it, and it is the same lesson R8 was built on:**
`ci/gate-equivalence.sh`'s incomplete arm carried **only a NON-VIOLATING policy**. With nothing to delete,
a route that deletes violations is indistinguishable from one that does not. Now split into two arms.
Independent corroboration of R8's design rule: *a precedence row needs a firing rule and an unanswerable
one in the SAME policy, or it tests neither.*

**The count-0 fix did not just delete the refusal — the pinning test was REWRITTEN and its assertion moved
to the disclosure.** Deleting a refusal without asserting the note that replaces it is this very defect
wearing the fix's clothes. A new row keeps a count-0 report that nevertheless lists an effectful entry at
exit 1, so the hedge can never swallow a finding.

**And it caught its own overreach.** Its `unanalyzed` fix was too strict on `coverage`: sweeping the
reviewer's 22×10 bait matrix afterwards, `cov.json` refused on all ten policies because its ledger spells
the count differently while naming the package perfectly well. Refusing there **drops a hedge in order to
be strict about a decoration** — `calls` is never read on the gate route. `6175f3d` gets a better answer
than either the pre-fix silent drop or the refusal: exit 1 with `coverage: {uncovered:1, packages:
[ratesdep]}`. Ledgers that cannot be read at all still refuse. This is [[feedback-fabrication-fixes-cause-misses]]
running in the OTHER direction — a strictness fix costing a disclosure — and it was found by SWEEPING the
matrix after the fix, not by reasoning about it.

Grep result as asked: exactly ONE `unwrap_or_default` on a §2 key, the one named. Three near misses checked
and correctly left alone. Side finding fixed: `analyzed: {"count": 5}` with no digest contributed **0** to
the verdict's count while a second reader of the same file said "judged 5" — two readers, one file,
disagreeing.

### Two environment traps, and the second one validates the R1 harness fix

- **`ci/self-gate.sh:21,34` does `rm -rf "$d/.candor"` on every crate dir**, deleting eight TRACKED
  `crates/*/.candor/report.*.json` files and never restoring them. It caught the agent inside a `git add
  -A`; restored from `abbb67c`, verified byte-identical. This is [[feedback-evidence-dirs-are-sacred]]
  again and it has now bitten twice. **Queued to fix — it is a live trap for anyone running that leg.**
- **`cargo build --release` at the workspace root builds only the root package** (standing bar 7h, third
  sighting). It left a stale `candor-query` **with no `gate` verb at all**. Caught before it produced a
  datapoint — but note what would have happened downstream: **that is exactly the state PART 27's R1 cell
  used to score OK on**, since it accepted exit 2 and 2 is also the usage-error code. The harness fix
  landed hours before the condition it was written for occurred naturally.

## swift's round — CLOSED (`3ba8b3a`, `beea0e2`, `a0131d5`, `1611608`, `daf62c4`) · 411 tests, 0 failures

Four dispatched, **five landed** — and R8 got verified as a side effect.

**The boolean `count` was live exactly as specced.** `__NSCFBoolean as? Int` succeeds with `1`, so a
boolean manifest granted coverage byte-identically to `count: 2` and the caller dropped out of `functions`
— a ⟨0.21⟩ purity claim licensed by a manifest that made no readable claim. Rejected **before** the integer
cast on `objCType == "c"`, which is the boolean tag on Darwin *and* corelibs, so the Linux CI leg runs the
same test. **A value test cannot work here**: `count: 1` and `count: true` are the same number. The shape
table gained seven rows including `float_integral` (`2.0` is still believed) as the anti-flood control.

**A second defect fell out of testing the first: an unreadable `count` was being SUMMED INTO the verdict
document.** `count: true` emitted `"analyzed":{"count":1}`, `count: -1` emitted `-1` — a fabricated number
in the machine channel, arriving through the same type bridge. Both now 0.

**FIX 5 was not in the brief.** Probing for siblings found the same coercion on the SCAN path: a corrupt
chained-dep entry was `continue`d, so a covered package's silence turned it into a purity claim — measured
**strictly more confident than not chaining the dep at all**, which is the shape to remember. Its first
measurement of this was **vacuous** (no `import` in the consumer, so the intact arm also read pure) and it
caught that itself; the intact arm is now asserted in the test for exactly that reason.

**A pre-existing fixture was REFUTED by the fix.** `testScopedUnknownDenyWithNoReachableReasonIsRefused`
posed `direct: ["Unknown"]` — the helper defaults `direct` to `inferred` — while its prose said "no
`unknownWhy` nor a `calls` edge". Two different states, and **it had picked ONE SPELLING of two**, which is
[[candor-selfdifferential-property]]'s finding arriving in a hand-written fixture. Re-pointed at the
inherited state it meant, and `fnEntry` now takes an explicit `direct:`.

Brief correction: swift did not write *zero* bytes to stderr on `empty/` — it wrote `candor-swift: policy
✓` there. The substance (no disclosure that the report judged nothing) was right.

### R8 IS VERIFIED NON-VACUOUS, and I did not have to run the suite to learn it

The agent's own conformance run went OK → FAILED mid-session and **it correctly attributed the change to my
`fae26a0`, not to its work** — checking that its diff touched no `gateDie`, `writeGateVerdict` or `exit(`
line, and that the pre-session matrix already recorded `mixed_prec` at exit 2 four-way. That is the
discipline this project keeps asking for: when the suite turns red, establish *which* change moved it
before defending your own.

**R8 fails on all four engines** — rust/java on `refusal-doc`, ts/swift on `refusal-doc` AND `precedence`.
That is the predicted first result and it means the row discriminates rather than passing by construction.
Every other part is MATCH, including R1's new `deny Unknown[unresolved] → exit 1` cell, **now green
four-way** because swift's fix 3 landed the CONTRIBUTES half. The tightened R1 cell and the fix that
satisfies it arrived within an hour of each other from opposite directions.

## MY RULING CREATED A FABRICATION — found by java, reproduced by me in rust, worse there (2026-07-28)

`7271c69` said a certain violation dominates a refusal. Correct, and incomplete. **candor-java implemented
it and the implementation produced a fabrication that the ruling made reachable**, then reported it rather
than shipping it.

**The mechanism.** Once a firing rule stops short-circuiting the refusal, the evaluator reaches code it
never reached before. A scoped `deny Unknown[unresolved]` over an entry whose class set is UNCOMPUTABLE
began emitting a violation record, because the class-set helper floors an empty set at `unresolved`. **That
floor is the correct fail-closed default for a MATCHER — "could this rule apply?" — and the wrong basis for
a FIRING — "did it?"** One helper served both questions safely only while the short-circuit hid the
difference. Ruled in `5a8cf48`: withhold per (rule, function), never whole-policy.

**I then measured rust, and rust is worse — it is a fabrication AND a false disclosure.** Fresh
`--workspace` build at `89f2c0f`, fixture: `app.opaque` with `inferred:["Unknown"]`, no `direct`, no
`unknownWhy`, no `calls`:

```
A  deny Unknown[unresolved] app.opaque   -> prints a NOTE ending "Refusing (exit 2)."
                                            then CHARGES that exact rule+function, exit 1,
                                            violation in the --gate-json document
B  deny Unknown app.opaque      (bare)   -> exit 1   CONTROL: the fixture is live
C  deny Fs app.writes + the A rule       -> both charged; app.opaque still fabricated
```

The NOTE in case **A** also asserts *"a rule FIRED on evidence this report carries"* — **and none did.** The
only rule in that policy is the unanswerable one. The sentence is attached unconditionally to the refusal
note instead of being conditioned on a violation having been recorded, which makes it a **false
disclosure**, the `net-partner`/PART 13b class. Dispatched.

### What this round is actually teaching, and it is not "test more"

**A soundness fix is a fabrication risk in its own right.** The recorded lesson so far runs one way —
[[feedback-fabrication-fixes-cause-misses]], killing an over-charge is where silent under-reports get
introduced. This is the MIRROR, and it arrived within the hour: removing a short-circuit to stop losing a
finding made the engine charge one it could not evidence.

**The operational question for any short-circuit removal is: what code now runs that never ran, and what
did it assume about who would call it?** The floor was written for a caller that could not reach it in this
state. Three engines had landed the precedence fix before this surfaced.

**And my first reproduction attempt was WRONG in the flattering direction.** I built an entry inheriting
from a reasonless source and found rust firing — nearly filed it. But that class set is `{unresolved}`
*legitimately*, computed over the gate's reach, and R1 already pins it. The control is what caught me:
the real case is an EMPTY class set, not a reasonless one, and the difference is exactly the difference
between "resolved to nothing" and "could not be resolved". **Every fix here now needs its mirror checked —
withholding is precisely where the under-report gets reintroduced.**

## ts's round 1 — CLOSED (`be739fa`, `de2b2a1`, `df85cfd`), and my severity call was wrong

Two items dispatched, **three defects fixed**, and the one I graded LOW-MEDIUM was the largest in the round.

**I called `inferred: [1]` "LOW-MEDIUM, narrow".** Measured: **12 of 14 corrupt shapes gated GREEN**; all 14
refuse now. `inferred: [1]` was the smallest instance of an idiom that was live on `unanalyzed`,
`analyzed.count`, AND the chained-dep join — where it was **both a silent under-report and a live
fabrication reaching a consumer's own report.** I graded the instance I was shown rather than the idiom it
was an instance of, which is the same error as scoping a clause to where its defect was found.

**FIX 3, found by the sweep and not in the brief, is the worst of the three.** On the chained-dep route,
`functions: "oops"` / `{}` / `inferred: null` put the caller **ABSENT from `functions`** with no
`invisible`, no `coverage.uncovered`, no verdict block — **strictly more confident than not chaining the
dep at all.** That is the count-0 defect arriving through a different key. The fabrication mirror sat on the
same line: `inferred: "Fs"` iterated into `['F','s']`, writing two invented effects into the consumer's
report. **Its first attempt at this fix was wrong and measuring caught it** — withholding coverage alone
left a `crossDeps` cell that short-circuits `chargeExternalDecl` before the coverage check, so the fix
*moved* the under-report rather than closing it.

**The MCP `candor_gate` tool had the multi-report hole identically**, returning `{ok:true,violations:[]}`
to an AGENT with the disclosure on the *server's* stderr — a channel no agent reads. Read-only tools
deliberately left alone.

**The empty-coercion sweep came back with a ruling on every idiom**, which is the output shape I want from
these: 7 fixed as the same defect; 8 kept as legitimate absent-defaults with the reason each (Map/graph
misses over already-normalised entries, an advisory κ ledger the gate reads separately, a callgraph already
tagged `partial`); 7 keys deliberately out of scope because no verdict reads them and refusing there is a
spurious-refusal machine — **pinned by a control row**, so the scope decision is itself tested.

**Verified on real code, not just fixtures:** byte-equality over two corpora scanned at HEAD — hal-explorer
(45 entries) and ukri-tfs (4121) — byte-equal across `deny Net`/`deny Fs`/`pure`, **zero spurious refusals
over 4166 real entries**, and ukri-tfs exits 1 so the check is non-vacuous. That is the control that makes
"refuse on corrupt input" safe to ship: the fear with a new refusal is that it fires on healthy code.

- [ ] **NEW — MCP `candor_gate` implements NO ⟨0.21⟩ incompleteness rule at all.** It returns `{ok:true}`
      over a report declaring `unanalyzed` units where the CLI exits 2. Reported not fixed: it needs a
      tool-result shape decision (`incomplete`/`unanalyzed` keys). **The agent-facing surface is the one
      where a false all-clear is acted on without a human reading it.** Check the LSP surface too, and the
      other three engines' MCP servers.

## swift round 2 — CLOSED, FIRST ENGINE GREEN ON R8, and it found a suite-halting blocker

8 commits, 428 tests / 0 failures. **All 69 live PART 27 cells pass for swift**, including R8 `precedence`
and R8 `refusal-doc`. The only red PART 27 cell left is `rust key-parity(opt)` — rust's key name.

**Swift HAD the fabrication** the urgent mid-flight warning was about: `deny Unknown[unresolved]` over an
inherited reasonless `Unknown` fired with a violation record **in the same run whose stderr said that rule
could not be evaluated for that function.** Fixed by moving the `unresolved` floor out of the matcher and
into the gate-input builders, where `netClassesOf` has always floored. The test row is one rule over two
functions and violations went `["app.named","app.orphanU"] → ["app.named"]` — a mirror-checked fix, since
the sound half must survive.

**And `configSources` proved my own point inside the hour.** The agent minted a key name for the config
disclosure, flagged it as needing a four-way pin — and R9 immediately measured three names for one field.
It then converged swift to `policyVocabulary`. **The interval between "I am inventing an unpinned name" and
"this is a measured three-way divergence" was under an hour**, which is the strongest argument yet that an
unspecified field is not a small debt.

### THE BLOCKER: my `be0b9a9` took the whole differential offline

`parsepolicy` began exiting 2 on the conformance battery — which contains unrecognised tokens
DELIBERATELY, as the four-way pin on how such a token parses. **The suite HALTS at PART 4.** java and ts
applied the token ruling in the PARSER; rust and swift kept the parse and refuse only at the gate.

**Ruled `6929dce`: `parsepolicy` MUST NOT refuse.** The refusal belongs to the gate, which must not enforce
a policy it cannot honour. It does not belong to the *witness*, whose job is to answer *what did this engine
make of my policy?* — a question most valuable exactly when the answer is "not what you meant". A
diagnostic that declines to explain the thing being diagnosed has inverted its purpose. It emits its parse
plus an `errors` list and exits 0, and the token must APPEAR there rather than being dropped: pre-⟨0.24⟩
behaviour was drop-with-a-warning, and **a diff that cannot distinguish "dropped" from "rejected" cannot
pin this rung at all.** java dispatched, ts told.

**The lesson is about blast radius, not about the ruling.** `be0b9a9` was correct and I did not ask which
OTHER verbs share the code path it changed. Two of four engines put the error where it disabled the
instrument that would have caught the disagreement — so the failure was silent until an engine tried to run
the suite. **When a ruling changes a shared component, name the verbs that share it before dispatching.**

### R9's remaining blind spots, named by swift and worth queueing

- [ ] **R9 arm 1 only sees keys present in an AS-EFF-006 verdict**; arm 2 covers exactly ONE optional block.
      Still uncompared four-way: `incomplete`/`unanalyzed`, `coverage` itself, the refusal document's
      `reason`, and each violation record's optional `reasonClass`/`netClass`. Each needs its own arm, per
      the rule arm 2 established: *every optional block needs an arm that makes it PRESENT.*
- [ ] **`privacy-manifest --verify --json` emits `coverage.modules`** — the SECOND instance of the exact
      hole `coverage.packages` fell through, on an extension surface. No clause and no PART pins it, and no
      other engine ships the verb, **so nothing can compare it** — a single-implementation surface is
      structurally immune to a differential. swift named it rather than renaming unilaterally, which is
      right.
- [ ] **Reserved-NAME alias rejection (`unknown-alias reflect = native`) is a different rule** from the
      unrecognised-TOKEN rule and stays warn-and-skip: the name IS recognised, and skipping leaves the
      built-in meaning standing, so there is no fail-open. Pinned four-way by PART 4. Confirmed, not open.

## The parsepolicy blocker is CLEARED (java `a71cf3a`) — suite runs all 27 PARTs again

PART 4 MATCH four-way, 18/7/3 in every engine; zero java FAIL rows in the whole run. `errors` is omitted
when empty so a clean dump stays byte-identical and PART 4's comparison is untouched. An unreadable policy
FILE still exits 2 — there is no parse to report — and that stays distinguishable in the API
(`policyUnreadable` vs `policyErrors`) rather than being inferred from an empty list.

**My brief was wrong about who broke it.** I wrote "candor-ts did the same"; measured, **ts exits 0 and never
had the defect — the halt was candor-java alone.** I relayed swift's report without checking, which is the
second time this session I have propagated an unverified cross-engine claim (the first was `interfaceUnion`).
Both times the agent measured and corrected me. **A cross-engine claim in a brief is a measurement someone
else made, and it inherits none of my confidence unless I re-run it.**

- [ ] **The ruling's second half is unimplemented in ALL THREE siblings.** rust, ts and swift exit 0 but
      **silently drop** the token — their `parsepolicy` keys are exactly `deny/allow/forbid`. That is the
      pre-⟨0.24⟩ drop-with-a-warning the ruling says cannot pin the rung, so **the diff still cannot
      distinguish "dropped" from "rejected"** and the blocker being cleared has NOT restored the pin. java
      is the only engine emitting `errors`, and **the spec does not pin its shape** — java chose
      `{kind, token, accepted, rule, message}`. Pin it, then converge three engines.

### A NUL byte hid 1,105 lines of the policy parser from grep — and my first measurement of it was WRONG

`Policy.java:363` holds a raw `\0` in a string literal (`r.src().trim() + "\0" + fn`). It compiles and is
semantically fine, but **grep treats the whole file as binary and exits 1 printing nothing**: a probe that
has 13 real matches reports none. That file is 1,105 lines of the POLICY PARSER — the exact component this
entire session has been changing.

**And my first attempt to size it was flattering nonsense.** I ran `grep -rl $'\0'`, got 14 files, and was
about to record "93% of candor-java's core source is invisible to grep". In zsh `$'\0'` is an EMPTY STRING,
so that command matched every file it was given. The real number is **one file**. Checked whether it had
corrupted any conclusion I drew today: it had not — the `packages`/`modules` ruling was confirmed from
`VerifyCli.java`, which my earlier glob missed for an unrelated reason (a subdirectory).

Two things worth keeping. **This is standing bar 7j with a new cause**: not "the surface is absent" but
"the tool cannot read the file and does not say so" — and unlike a zero-match grep, this one is invisible
even when you are looking for it, because exit 1 with no output is what a genuine miss looks like.
**And I produced the exact failure I spend this queue documenting** — a dramatic number, arrived at in one
step, not controlled. The tell was available: 14 files each containing a NUL is implausible for hand-written
Java, and I had a second tool (python) that took ten seconds to disagree.

- [ ] Replace the literal NUL in `Policy.java:363` with the `\0` ESCAPE — byte-identical semantics,
      searchable file. Also: `unverified` over an unhonourable policy prints "— no fix computed" (shares
      `loadPolicyOrDie` with `fix`/`fix-gate`): right posture, wrong noun.

## rust round 3 — CLOSED (7 commits), and removing a short-circuit bit TWICE in one session

438 tests, clippy 0, bait matrix 29/29, gate-equivalence 54 rows, self-gate OK.

**A/B/C reproduced exactly.** `deny Unknown[unresolved] app.opaque` alone: NOTE ending *"Refusing (exit
2)."* then exit 1 with a violation record → now exit 2, refusal document, no violation. The bare-rule
control unchanged; the mixed policy now charges only `app.writes` and discloses the withheld rule.

**The tell I missed and rust found: the fabricated record carried NO `reasonClass` KEY AT ALL**, while the
evidenced records beside it carry `["unresolved"]`. The floor lived in the predicate and never in the data,
so **the record refuted itself** — the document contained the evidence that it was fabricated. Worth
remembering as a detection shape: a violation whose justifying field is absent is not a formatting quirk.

Root cause differed from java's: rust had TWO pieces of code and its answerability detector was already
right — only the firing side was wrong. Fixed by asking the firing question three ways (fire / tolerate /
**withhold**), with withheld pairs riding out in a `GateOutcome` so no caller can drop them. **The Net
filter got the same split — it never fabricated, it silently DROPPED, which is the other half of one
defect.** Both directions of one bug, found because the fix forced the question.

**THE SAME HAZARD BIT TWICE.** Deferring the `forbid`/`allow` refusal (my `1503368`) silently started
*evaluating* them: `deny Net` + `allow Net other.example.com` put an **AS-EFF-008 record in the document**,
derived from a `surface_incomplete` map the report route leaves empty ON PURPOSE — precisely the unsound
verdict that refusal exists to prevent, shipped as if certain. Its own new test caught it on the first run.
**Removing a short-circuit exposes code to inputs its author never had to consider, and I have now caused
this twice in one session from two different rulings.**

**`unverified` LOST A DISCLOSURE, in a verb java never named.** A hole is a function that *passes* its rule
while Unknown — so widening `Unknown[corp]` to a bare `deny Unknown` reclassified a real hole as a
violation-that-isn't, and the verb printed **"PROVABLY clean ✓"**. The token ruling's blast radius reached
a *disclosure* verb, not just gates.

- [ ] **Two residuals rust reported rather than fixing unilaterally** (both touch conformance-pinned
      predicates): (a) `whatif`/`fix-gate`/`unverified` ignore the `Unknown[…]`/`Net[…]` FILTER when
      matching — `unverified_hole_rule` computes `violates` from `r.effects` alone, so the same lost
      disclosure is reachable one layer down **with no alias at all**, shared with candor-scan's gate note
      (PART 12d); (b) `whatif` reconstructs the printed rule from `effects`+`scope` instead of `raw`.
      **Fixing (b) alone would be WORSE while (a) stands** — it would attribute an unfiltered verdict to the
      operator's actual narrowed rule.
- [ ] **A wider vein under `be0b9a9`, for a four-way call:** a policy line whose rule KIND or EFFECT NAME is
      unrecognised is still dropped with a warning. Now half-addressed: `195d45a` requires `parsepolicy` to
      REPORT every dropped line, which is additive and needs no grammar decision. Whether the GATE should
      refuse stays open — `deny Net Exex app` cannot be told from a legitimate scope by the parser.

### Two measurement errors rust caught in itself, both flattering

Its first corpus run **discarded the violation lines** (they go to stdout), and its first mutant harness
**didn't rebuild after restoring**, so a non-compiling mutant inherited the previous mutant's binary and
looked "caught". **A mutant that doesn't compile is not a mutant** — and the tell was arithmetic: 6 bait
failures with 0 test failures is impossible. Also fixed: a `gate-equivalence` arm asserting *neither* route
writes a document on a policy error — an equality claim about an ABSENCE, which `1503368`(b) inverted.

## R8 IS GREEN FOUR-WAY — and the last fix CREATED the mirror rather than leaving it standing

ts round 2 (`4faac08`, `4762b2f`, +2) and java (`74f348c`, `93ac572`, `868dbc9`) close the rung.
**All four engines pass both R8 cells and both R9 cells.** One red cell remains in the whole suite —
rust's `key-parity(opt)` — dispatched.

**My withholding clause was wrong and an engine measured it.** I specced per `(rule, function)`. On one
function carrying a certain `Fs` beside a `netClass`-less `Net`, that form gives **exit 2 with the
`violations` key ABSENT** — the certain finding deleted, which is `7271c69`'s defect arrived at through the
fix for `7271c69`'s defect. Amended to per `(rule, function, EFFECT)` in `b3748ed`. **I then assumed java
and swift both had it and measured instead: only java did.** swift exits 1 with the violation present.
Second time today that measuring corrected an assumption before it reached a brief.

### The finding worth carrying: a latent bug made LIVE by a correctness fix

java's mirror check was not "did the old fabrication survive" — **the granularity fix CREATED a new one.**
`unanswerableScopedFilters` tested its two withhold causes with `else if`. That is harmless while either
cause withholds the whole pair, and becomes a live fabrication the instant the key stops covering the pair:
measured on the real binary, one function carrying both a `netClass`-less `Net` and a reasonless inherited
`Unknown` under one rule was **charged `Unknown` — a class its report never asserted.**

    else if  ->  exit 1, violations: [{app.both, ["Unknown"]}]      FABRICATED
    if       ->  exit 2, both withheld effects disclosed

**Three times on this rung a fix has produced its own inverse, and this is the first where the inverse did
not pre-exist.** The general shape: *a guard that was sound only because a coarser key upstream made its
weaker branch unreachable.* Widening precision anywhere downstream of such a guard arms it. The operational
question is the same one short-circuit removal asks — **what did this code assume about who would call it,
and is that still true?**

java also produced the state no engine had before: a document carrying **both** `violations` (the certain
`Fs`) **and** `unevaluated` (the withheld `Net`) — the verdict finally says *what fired* and *what could not
be read* in the same breath, which is the whole point of the precedence ruling.

Follow-ons landed: `parsepolicy`'s `errors` now carries **10** entries where it carried 2 (the 8 dropped
lines included an NBSP-separated `deny Net Db` read as an unknown rule kind — worth knowing that
whitespace, not vocabulary, was the cause of one); the gate's behaviour on dropped rules deliberately
untouched, and the stderr sentence filtered too, since printing "the GATE REFUSES this policy" over a
merely-dropped line would itself be a false disclosure. The `Policy.java` NUL is escaped —
`grep -n unanswerableKey Policy.java` went from **nothing to three hits** — and the guard is a scan over
the whole main tree, not the one line, because candor-ts hit the same idiom independently.

## rust closes the last red cell (`15917d2`, `481269b`, `736957b`) — FULL FOUR-WAY CONFORMANCE EXIT 0

442 tests, clippy 0, all 18 rust PART 27 cells OK with no other cell moved, PART 12b/12c/12d unmoved,
PART 2's whatif differential matching java. Mutant audit re-run: the empty-`violations` serializer is now
killed by **43** gate-equivalence rows and **11** cargo tests (it survived 50 of 51 arms two rounds ago).

**Two test-design points worth keeping.** The rename tests assert **the OLD key is ABSENT**, not merely
that the new one is present — an engine emitting both would satisfy every "policyVocabulary present"
assertion while leaving the divergence standing. And the first run's default **fail-fast hid the second
route's failure**; `--no-fail-fast` is required in that repo to see both.

### THE HAZARD FIRED A FOURTH TIME, AGAIN CREATED BY THE FIX

Making `unverified`'s predicate filter-aware is precisely what first lets a NARROWED rule *be* the rule a
hole is disclosed under — and `rule_and_upgrade`'s reconstruction dropped the bracket, so it would have
printed `deny Unknown` for `deny Unknown[reflect]` and advised the nonsense `deny Unknown Unknown`. Dormant
until the fix reached it. That is now **four times on this rung**, and the shape has been identical every
time: *code that was correct only because something upstream never handed it the case it mishandles.*

Two further copies of the same defect, found by measuring rather than by the brief: **candor-scan's gate
note re-parsed the policy WITHOUT the `.candor/config` vocabulary** — `ea0df4f`'s defect standing in the
other copy — and **`fix-gate` ran the mirror**, computing a hoist remedy for a crossing the gate does not
report. `fix`'s upward climb correctly keeps the hypothetical predicate, because it asks about a *layer*.

### The brief's premise on `whatif` was wrong, and the obvious fix was worse than the bug

I said (a) would carry over to `whatif`. It does not: `unverified`/`fix-gate` read a signature that EXISTS,
while `whatif` asks a hypothetical — a narrowing filter quantifies over the class of an effect **not written
yet**, so there is nothing to match. And printing `raw` alone, which is what I asked for, would have been
**worse than the bug it fixed**: attaching an unconditional verdict to the operator's narrowed line reads as
a filter candor evaluated and didn't. The answer is §3.1's own rule — disclose the condition, never score
it. Pinned as `conditional` in `6f30540`, **before the other three implement it**, which is the first time
this rung has got ahead of the unpinned-field hole instead of behind it.

## swift's release round — CLOSED (`db3e9e6`…`954bc04`), 457 tests, zero swift cells failing

All six items reproduced before fixing. Both R8 cells, both R9 cells and **R10 report-parity OK**.

**Two method notes worth more than the fixes.** *One of its OWN new rows was vacuous against the defect* —
the `errors` shape check looped over an absent array, so it passed before the fix; caught by asserting a
count first. And *one existing test changed its answer, and the old answer was the defect*:
`allow Location somewhere` used to warn-and-ignore at exit 0, **leaving a sensor ungated behind a rule that
looked like a gate.** `Location` is not a typo — it is a real effect with no literal surface — so the new
refusal text names both readings rather than asserting "typo", which is the right call: a disclosure that
guesses the operator's intent is a disclosure that will eventually guess wrong.

Its mirrors are the strongest of the round: a *consumed* alias typo still refuses; a **sole** refusal still
exits 2 with no `violations` key; and — the one that matters — **the refused policy is still NOT EVALUATED**
(a `deny Fs` beside the bad token must not fire), because otherwise *"could not read this policy"* silently
becomes *"enforced it anyway"*.

- [x] **CLOSED — shipped as candor-swift v0.23.3 (2026-08-01), and ported to `main` except the
      module-const half (pinned known-broken there). SOUNDNESS — swift extracted a Net host ONLY from a direct string argument of
      `NWConnection(host:port:)`, the one idiom PART 4e pins.** Measured, and worse than the review
      reported: **every `URLSession` form yields NO `hosts`** (the `URL(string:)` constructor interposes)
      and **every `Process` form yields NO `cmds`** (`launchPath`/`executableURL` are property WRITES;
      `Process.run` takes a `URL`). rust and ts extract on their equivalents from both an inline literal
      and a local binding. Three consequences, all live on Apple-platform code:
      - **`deny Net[known-telemetry]` reads GREEN over a `URLSession` call to `api.segment.io`** — a
        narrowed deny that silently misses, which is the fail-open the destination-class rung exists to
        close.
      - a `URLSession` call to `api.openai.com` is **not classified `Llm`**, so the §1 ⟨0.13⟩ refinement
        AND the privacy manifest both miss it.
      - `allow Net` / `allow Exec` fail closed over essentially all Apple-platform code.
      **Correctly NOT fixed in this round.** It is three mechanisms (constructor unwrap, local-binder
      provenance, property-assignment provenance) and **every one moves the gate in the RELAXING
      direction** — extracting a host turns a fail-closed `unknown-host` into a classified destination and
      an uncertifiable `allow` into a certified one. That needs its own A/B on real corpora with the
      second fixture written first, not a tail-end change after five gate-semantics commits.
      PART 4e pins only `NWConnection` for swift, so **the suite cannot see any of this** — a
      single-idiom fixture standing in for a language's whole network surface.

## java's release round — CLOSED (`d6a1312`…`54e11ca`), 621 tests, all 18 PART 27 java cells OK

Six items reproduced then fixed, plus a **seventh found while checking a mirror**. Its `report-parity` FAIL
is `packages:list` vs `package:str` — **byte-identical on the pre-change jar**, so R10 is reporting a
pre-existing divergence, which is the row working.

**The seventh is the stale-document defect on the SCAN route** — specced in `901f14d`, implemented by
nobody: a clean run leaves `ok:true` in the gate-json, then an invalidated baseline OR an unreadable scan
target exits 2 and **leaves the green in place**. Its fix is better than the obvious one: rather than thread
a sink through ~20 exit sites — *the position-scoped fix this rung has criticised four times, and one that
still misses crashes and kills* — it arms the path **fail-closed when the flag is PARSED**, and normal
paths overwrite it. `-` (stdout) excluded and pinned by its own test.

**Same harm class on the MCP surface:** `ensure_report()` discarded the scan result, so with a good jar
scanned and the path then replaced by a corrupt one, `candor_effects` **kept returning the OLD jar's
`Net`/`hosts`/`netClass`**. Fixed on the INVARIANT (report newer than the newest class), not on the exit
code — because exit 1 is a gate violation and does write a good report.

Its item-1 fix keys the refusal arm on `violations == 0` — *"evaluated nothing"* — never on "ended
refused", which is the conflation the review named. And it emits `unevaluated` for **every** rule of a
refused policy, since naming only the typo'd line would read as the rest having passed.

### The correction that matters most came from java, and it had the opposite sign to every other one today

`allow` takes **FIVE** effects, not four — `Llm` rides `Net`'s host literal (⟨0.13⟩) and all three
measurable engines have accepted `allow Llm <host>` the whole time. The grammar clause has said "four"
since before `Llm` existed, and I repeated it in `1e1748a` while declaring the position CLOSED — which
would have made **`allow Llm api.openai.com`, the privacy-manifest use case, exit 2.** Fixed `a07b9d3`.

**Six scoping errors today were too narrow in what they REFUSED, leaving a fail-open. This one was too
narrow in what it ADMITTED, and would have shipped a fail-CLOSED regression on working policy.** A closed
set is load-bearing in both directions and I had only been checking one. java measured it while
implementing and reported rather than complying, which is the only reason it did not ship.

## OPEN at the budget stop — what a release still needs

- [ ] **java: normalise `errors[].kind` onto the pinned set** (`forbid form`/`allow values` → `rule-form`,
      added in `f735b16` after java's round began; it argued for exactly this member and was right).
- [ ] **R10's baseline**: the row is live and correct but has no waiver file yet, so today's real
      divergences (java `packages`, rust's `incomplete` marker, omit-vs-empty) fail it. Measure once, record
      each with a reason, and it ratchets from there.
- [ ] **Per-shape vacuity ratchet in PARTs 24/25/26** — the floor trips only at `live == 0` in TOTAL, so a
      review neutered one split shape (8 cells/engine) and the run stayed green. Up to 9 of 10 shapes could
      rot with exit 0. **The `live` column and the `0/0` witness count are PRINTED, never ASSERTED.**
- [ ] **R9 needs an `unevaluated`-present arm** — the field is now pinned and four-way implemented, and no
      cell compares it.
- [ ] **`whatif` returns `ok:true` over a report declaring `unanalyzed`** — measured by rust AND java, both
      declined to fix unilaterally. §3.2 pins whatif's shape with no `incomplete` field, so it is a
      four-way rung, not a bug. Its `ok` reads as a verdict and its `affected` set is computed over an
      incomplete universe.
- [x] **CLOSED — v0.23.3.** swift host/cmd extraction, which was the largest open soundness item.

## swift host/cmd extraction — CLOSED (`b27c3c9`, `f5be3e6`, `77b6bff`, `c611671`), the one defect live in the RELEASED line

496 tests, conformance four-way OK, every swift cell MATCH. A/B over **4 corpora, 8,568 functions**:
13 fns gained hosts, 12 gained cmds, 31 effect sets grew, +8 report entries — and the column that makes
those credible: **0 lost, 0 shrank, 0 dropped.** Two real-world negative controls held (a parameterised
`executableURL`, a file-scope handle). 19 fail-closed mirrors written BEFORE each mechanism, and the
singleton-field mirror verified non-vacuous by removing its guard.

**The A/B caught a fabrication in the agent's OWN mechanism that all 25 fixtures had passed.** A
`SequenceExpr` is flat, so `p.launchPath = "/usr/bin/" + tool` parses as `[lhs, =, "/usr/bin/", +, tool]`
— it read `"/usr/bin/"` and reported THAT as the program, which **`allow Exec /usr/bin/` would have
certified for an entirely runtime command.** It surfaced only on a negative control written into the
corpus, not on any fixture. That is [[feedback-fabrication-fixes-cause-misses]] in the relaxing direction,
and it is the clearest case yet for the standing rule that **a fixture suite and a corpus A/B fail
differently**: 25 fixtures agreeing is not evidence when the defect needs a concatenation nobody thought
to write.

**A FOURTH defect, out of scope, found by the A/B and isolated in its own commit:**
`private let session = URLSession.shared` left the field **untyped**, so the call missed κ entirely and the
function was **ABSENT FROM THE REPORT** — a ⟨0.21⟩ purity claim, a cardinal sin, and one no locator or
gate work could ever reach. The same inference already existed for local bindings; only the field case was
missing. 29 enlarged effect sets on one corpus alone, including a SwiftUI card → `MedicationStore.shared
.log()` → `saveEntries()` → `defaults.set()`: **a real disk write reported as pure.**

**Guard direction is inverted here BY DESIGN and the agent got it right:** mechanism 1 uses an **allowlist**
of companion arguments, not a denylist, because the direction is RELAXING —
`URL(string: "/v1/track", relativeTo: base)` would otherwise fabricate the host `/v1/track`. The family's
denylist-over-allowlist rule is about widening a sound over-approximation; it inverts when the change
narrows toward a confident claim.

### PART 4e was a cell that could not fail, and that is why this survived (FIXED)

Its four cells are rust `TcpStream::connect`, java `URL(...).openConnection()`, ts `https.get(url)` —
**three URL-based forms** — and swift `NWConnection(host:port:)`, which takes the literal DIRECTLY. **swift
was the one engine whose cell exercised the shape that already worked**, so an entire language's network
surface could be absent with the row green. Now carries the `URLSession.shared.dataTask(with: URL(string:
…))` idiom too, which would have failed before this work and passes after.

**The general shape, which is worth more than the fix:** a differential row is only as good as the
*idiom* each engine's cell instantiates. Four engines agreeing on four DIFFERENT shapes is not four-way
coverage of one property — it is four one-way checks that happen to share a heading.

### Review of the swift extraction round (2026-07-29, me, measured not read) — no fabrication in 11 probes

Hunted the shape the author's own A/B caught (a literal captured and reported as the value at the call when
it is not). **All five hard cases fail CLOSED, correctly**: string interpolation, concatenation, a ternary
over two literals, a `var` rebound before the call, and `URL(string:relativeTo:)` each extract **nothing**
and keep `netClass: ["unknown-host"]`. Sound controls extract (`good.example`, `/bin/ls`).

**The mirror holds where it matters most:** an unrecoverable `Exec` — interpolated program, or an
`executableURL` from a parameter — still carries `inferred: ["Exec"]` with an EMPTY `cmds`. The effect is
kept and only the literal is withheld, which is the distinction that makes `allow Exec` fail closed rather
than the function reading pure.

**`c611671` (field typing) is broader and cleaner than its commit message claims** — all four forms type
and extract correctly: `let` singleton, `var` singleton, a field assigned in `init` with an explicit type,
and a field whose initialiser is a FUNCTION CALL (`URLSession(configuration:)`) rather than a singleton.

- [ ] **ONE INCONSISTENCY, low severity, fail-closed direction.** A double assignment
      `p.executableURL = …/bin/sh; p.executableURL = …/bin/zsh; p.run()` reports **both**
      `cmds: ["/bin/sh", "/bin/zsh"]` — but only `/bin/zsh` can run. **The URL path withholds on exactly
      this shape** (`rebound` above extracts nothing), so the two mechanisms disagree about straight-line
      rebinding: one unions, one withholds. Harm direction: over-reporting a command is fail-CLOSED for
      `allow Exec` (a spurious gate failure, never a missed one) and inert for `deny Exec` — so this is a
      false-positive risk, not a cardinal sin, and NOT a release blocker. Worth settling because the
      inconsistency will read as a bug to whoever hits it, and because "last write wins" is decidable here
      where a loop-carried rebind is not.

## The 0.23 BACKPORT — and the differential that caught a fabrication the port introduced (2026-07-30)

`release/0.23` off `v0.23.0` carries the locator-provenance work as a genuine 0.23 patch (`specVersion` stays
`"0.23"`, no ⟨0.24⟩ vocabulary — verified by grepping the whole `+` side). 272 insertions, hand-ported onto
files that had moved ~1,700 lines.

**A THREE-ARM differential — branch vs `main` vs the plain `v0.23.0` tag — is what made the finding
attributable rather than arguable.** Two arms would have shown a disagreement; the third proved which side
introduced it.

**The port FABRICATED hosts on five shapes that main withholds.** An inner `let` SHADOWING an outer name
wrote the name-keyed locator state, nothing restored it at scope exit, and a later use of the OUTER binding
claimed the shadow's literal — `hosts: ['phantom40.example.com']` for a host never contacted, and in one
shape the *real* outer host replaced by the phantom. Relaxing direction, so `deny Net[known-telemetry]` could
PASS on a phantom. The tag arm reported `hosts=[]` on all five, so this did not pre-exist: the map was always
leaky, and the port's constructor look-through made it reachable for host claims.

**It landed exactly where the port's one untested invariant was.** `NameKeyedStateTests` did not port (it
needs shadow-scope machinery postdating the tag), and the comment written in its place protects the KEEP half
— `movedNames` must not be cleared — and is silent on the SCOPE half `localConstStrings` needs. **A shadow
binder is not a rebind**, so `movedNames` never records it and the refusal never fires. An invariant asserted
in prose is an invariant nobody checks.

**Fixed without back-porting the shadow wave** (`eb1c76b`): `locatorNameIsStable` already runs a whole-body
pre-pass, so it now refuses any name with more than one binder site in the unit, **parameters counted as
binders** — the same conservatism `movedNames` applies to rebinds. Two refusal sites, and the second is the
one that matters: refusing only the local entry hands the read to `moduleConstStrings`, so a function
shadowing a module-level `let` answers with the MODULE's literal.

**A second fabrication was in the ORIGINAL work on both lines** (`47f460f` on main, `2c90c8d` ported): an
exec-side shadow binder claiming `/bin/phantom47` from a factory-produced handle. Main's own disposition note
justified keeping it because "a rebind is already recorded in `movedNames`" — **true of a rebind, false of a
shadow binder.** The note was wrong and is corrected alongside the code. On main the check is deliberately
exec-only, because applying it to the host path there would delete measured reach the scope machinery already
protects.

Evidence: **pollen A/B zero losses, and the port's gain intact to the row** — 37 enlarged rows + 5 recovered
units vs the tag, before AND after the fix. Same zero-loss on four corpora, 8.6k functions. main 501 tests +
**four-way conformance OK (swift 75 cells, 0 FAIL)**; branch 304 tests. Three synthetic shapes do lose reach
(sibling-branch bindings sharing a name, a closure parameter reusing the locator's name, the outer-literal
shadow) — all pinned as tests so a later scope-aware refinement reads as a deliberate change.

- [x] **MEASURED 2026-07-30 — IT IS *NOT* PRE-EXISTING. THE PATCH INTRODUCES IT, AND THAT IS RELEASE-
      BLOCKING.** The agent reported this shape as pre-existing on both lines. The `v0.23.0` arm — the one
      it did not run, and the reason I insisted on it — says otherwise:

          shape                          v0.23.0 (RELEASED)   release/0.23 + both fixes
          moduleConstShadowedByDynamic   hosts=[]             hosts=['moduleconst.example.com']  ← NEW
          moduleConstShadowedTwice       hosts=[]             hosts=[]                            (caught)
          moduleConstUsed  (control)     hosts=[]             hosts=['moduleconst.example.com']   legit gain

      **The released artifact extracts nothing here — including on the POSITIVE CONTROL** — because it
      cannot see a module const through the URL constructor at all. So the module-const channel is opened
      BY the port, exactly as the shadow-binder channel was: the constructor look-through makes a
      previously-unreachable leaky map reachable for host claims. Same cause, third instance.
      **Shipping the patch as it stands would introduce a fabrication that does not exist in 0.23 today.**
      The multi-binder refusal already catches the two-binder form; the single-binder dynamic shadow needs
      a poison marker at the binder so the read cannot fall through to `moduleConstStrings`.

      **The durable lesson is about attribution, not about the bug.** "Pre-existing on both lines" was
      inferred from two arms that happened to agree; both were post-port. A defect present in every tree
      you have built is not thereby pre-existing — **the only arm that can tell you is the one you are
      shipping against**, and it is the arm easiest to skip because building it proves nothing when the
      answer comes back clean.

- [x] **(superseded framing, resolved: it was port-introduced, fixed in 0.23.3) A third fabrication —** A module-level `let apiBase = "https://…"` shadowed by a DYNAMIC local of the same name:
      the binder scopes the local entry, `constValue` falls through to the module index, and the shadow
      inherits the global's literal. **One binder, so neither the new refusal nor main's `ShadowSave`
      touches it.** Fixture: `scratchpad/fixtures2/…/ModuleConst.swift` (`moduleConstShadowedByDynamic`,
      positive control `moduleConstUsed`). **The v0.23.0 arm was NOT shown for this shape** — establish
      whether it is reachable in the RELEASED artifact before deciding the release, because that is the
      difference between "a known bug we are shipping a fix beside" and "a fabrication the patch leaves
      live."

## 0.23 RELEASE ATTEMPT (2026-08-01, 03:04 cron) — NOT SHIPPED, and two of the reasons were not in the brief

**The brief's premise was wrong in a way that would have shipped a regression.** `release/0.23` was cut from
`v0.23.0`, but **`v0.23.1` is the latest release** — the local clone simply had not fetched its tag, so
`git describe` said 0.23.0 and everyone (me included) believed it. Shipping 0.23.2 from that base would have
**silently reverted 0.23.1's perf hoist**. Rebased onto `v0.23.1`, clean, hoist verified present.
*A branch point is a claim about what is released, and `git describe` on a stale clone is not evidence for it.*

**The blocker itself is FIXED and the family is closed.** The single-binder shadow — a module-level const
shadowed by a local bound once to something dynamic — answered with the MODULE's literal, because
`multiplyBoundNames` only refuses names bound TWICE and `constValue` then fell through to
`moduleConstStrings`. Mirror written first and confirmed failing; 305 tests pass; the positive control keeps
its host. Verified against a build of the released tag, which reports nothing here — so this was introduced
by the constructor look-through, third defect from that one cause. Swept for siblings: `globalReads` is a
name set rather than a literal map, and there is no other local-to-global literal fallback, so `constValue`
was the only channel.

### It did not ship, and the A/B is why — but two of the three "losses" were the fix WORKING

    lost surface                          verdict
    runSweepMode    paths=preview.html    FABRICATION REMOVED — it binds its own `sweep-<stamp>.md`
    runConvergenceMode  paths=…           FABRICATION REMOVED — its own `convergence-<stamp>.md`
    <main>          paths=preview.html    REAL REGRESSION, and mine

**The released engine was reporting a module const from an unrelated file as the path two functions write.**
That is a fabrication nobody had looked for, found by reading the loss column instead of trusting it — the
A/B's "losses" are not automatically losses, and treating them as such would have hidden a defect while
blocking a good fix.

The third is real: a multi-file package unions its per-file top-level code under one `<main>` unit, and in
that merged form the gate fires where it must not, dropping a genuine `Fs` path. **An isolated two-file
repro shows the intended behaviour** (`<main>` keeps its path, the shadowing function loses the fabricated
one), so the defect is specific to the merged unit. Diagnosis solid, fix unverified.

**Gate held: nothing pushed, no tag, no release.** Dropping a real filesystem path from a released engine is
the cardinal sin, and 03:00 surgery on a released line to chase it is how the second one gets shipped.

- [x] **NOT A DEFECT — the merged `<main>` "loss" was the fabrication being removed** (`<main>` inherited
      the fabricated path by calling the two functions that had it). No fix was needed. Former text: fix the merged `<main>` case. Per-file `<main>` FnInfos are built with `isTopLevel = true`
      (`DeclCollector.swift:193`) and "union under the one `<main>` module-entry unit" — the union is where
      the flag stops reaching the gate. Then re-run: pollen A/B loss column must be **zero after subtracting
      the two proven fabrications**, the three-arm table, 305+ tests, and the release steps.
- [→] **PINNED on `main` as three XCTExpectFailure tests (`f575f3f`) — the 0.23 fix does NOT port, see
      below. `main` FABRICATES on BOTH module-const shapes** (`moduleConstShadowedByDynamic` AND
      `moduleConstShadowedTwice`) — measured this session, three-arm. The branch is now ahead of `main` on
      soundness. `main` needs this same fix, and it was out of scope for a release brief.

## candor-swift 0.23.3 SHIPPED (2026-08-01) — and 0.23.2 shipped a fabrication first

**v0.23.3 is published** (`github-actions[bot]`, run 30693627952). Gates on the tagged commit: 306 tests /
0 failures, smoke 104/0, fuzz 25/0, fabrication-probe clean, every fabrication shape at `hosts=[]` with
every positive control intact. It supersedes **v0.23.2, which is also published and fabricates.**

### PUSHING A TAG IS PUBLISHING IN candor-swift, and I did not know it

`.github/workflows/release.yml` is `on: push: tags: ['v*']` — it cut Tom's own `v0.23.1` in July the same
way. I pushed `v0.23.2` believing a tag was inert until `gh release create`, reported "no release exists"
on a `gh release view` that ran before the workflow finished, and told Tom it was safely reversible. It was
not. **One `ls .github/workflows/` before pushing would have said so**, and I had read that directory
earlier in the week.

**Correcting a memory that is now wrong:** [[feedback-always-cut-gh-releases]] says every tag must also get
a `gh release create`. For candor-swift that is now FALSE and actively misleading — the workflow does it,
and a manual `gh release create` after a tag push is a second attempt at an already-published release.

### THE GUARDRAIL WAS ON THE WRONG DOOR

The permission classifier **blocked** my `gh release create` as a public-surface action — while the
**authorised** `git push origin v0.23.2` did the actual publishing. The operation that looked dangerous was
stopped; the one that was dangerous went through. A control keyed on the VERB rather than the EFFECT stops
the wrong thing whenever a repo automates the last step.

### release.yml's OWN GATES PASSED ON A FABRICATING BUILD

The workflow reruns `swift test` + smoke precisely to stop a bad release, and both were **green** — because
no test covered the nested-shadow shape until it was written an hour later. **The gate worked exactly as
designed; the test suite was the hole.** Same failure as the port's missing `NameKeyedStateTests`, arriving
one layer up. A release gate inherits the blind spots of the suite it runs, and adds none of its own.

### The defect itself, and why it is the most instructive of the three

`v0.23.2`'s guard was skipped for the **whole `<main>` unit**, on the reasoning that a file's top-level `let`
IS the module const rather than a shadow of it. True of a binder at the outermost level, false of one in a
nested scope — so the fabrication reappeared **one scope down**, inside the fix for it.

And the exemption **was never needed**: it was added to protect three pollen `paths` that turned out to be
the fabrication being correctly removed. **A guard built against a loss that was not a loss, which was
itself a hole.** With it gone the positive control still keeps its host, so nothing legitimate depended on
it. Scoping a rule to the UNIT when the condition is about the BINDING — the seventh instance this week of
scoping to the instance rather than the condition.

- [ ] **`main` is now BEHIND `release/0.23` on soundness** — it still fabricates on both module-const shapes
      AND has the top-level nested-shadow hole. Port `a05c44d` + the single-binder gate back to `main`,
      where the shadow-scope machinery (`ShadowSave`) changes the shape of the fix, so re-measure rather
      than transcribe.

## THE PLAN ON `main` (2026-08-01) — what stands between here and a 0.24 release

`main` is green (505 tests, 0 failures) with three defects pinned as both-ways ratchets. 65 open items, but
they are not equally weighted; this is the order and the reason.

### 1. THE INSTRUMENT, BEFORE ANY MORE ENGINE WORK

Everything else is measured with it, and it currently has two known holes:

- **Per-shape vacuity ratchet in PARTs 24/25/26.** The floor trips only at `live == 0` in TOTAL, so a review
  neutered one split shape (8 cells/engine) and the run stayed green. **Up to 9 of 10 shapes could rot with
  exit 0.** The `live` column and the `0/0` witness count are PRINTED, never ASSERTED. This is the single
  highest-leverage fix on the list: it is the difference between a suite that measures and a suite that
  reports.
- **R10's baseline.** The row is live and correct and has no waiver file, so three real divergences fail it
  today. Record each with its reason and it ratchets from there. **One of the three has a semantic
  disagreement underneath it** (java `undeclared:[…]` vs ts/swift `undeclared:[]` for the same situation) —
  fixing the key set alone would produce agreement on shape over a disagreement on meaning, so settle the
  semantics first.
- **R9 needs an `unevaluated`-present arm.** The field is pinned and four-way implemented and no cell
  compares it.

### 2. THE FOUR-WAY CONVERGENCE THE ⟨0.24⟩ RUNG STILL OWES

- java: normalise `errors[].kind` onto the pinned five (`forbid form`/`allow values` → `rule-form`).
- rust/ts/swift: emit the `aliases` OBJECT (ruled `7f5b5ba`; ts already does).
- `whatif` returns `ok:true` over a report declaring `unanalyzed` — measured by rust AND java, both correctly
  declined to decide it unilaterally. §3.2 pins whatif's shape with no `incomplete` field, so this is a
  four-way rung, not a bug.
- MCP incompleteness, measured four-way. ts fixed its own; the other three are unverified. **This is the
  agent-facing surface, where a false all-clear is acted on with no human reading it.**

### 3. `main`'s MODULE-CONST FABRICATION — design work, not a port

Pinned as three `XCTExpectFailure` tests. The 0.23 fix is a whole-body `locallyBoundNames` gate; `main` has
`ShadowSave`, which correctly restores an outer const past a shadow scope, so the blunt set over-refuses and
costs two measured regressions. **`main` needs a SCOPE-AWARE set maintained by the same save/restore**, and
`NameKeyedStateTests.disposition` is the file that must record what a rebind does to it — before the code,
not after.

### 4. ONLY THEN, THE 0.24 RELEASE

Floor bump, four-way conformance green with the ratchets honest, per-engine CI, corpus test, preflight. **Do
not cut it before (1)**: a release gated on a suite that can go green over dead fixtures is the shape this
whole rung exists to refuse — and `release.yml`'s gates passing on a fabricating v0.23.2 is the live proof.

### What NOT to do next

Not more engine fixes. The last three rounds each found more defects in the *instruments* than in the
engines, and the 0.23.2 release shipped a fabrication through a green gate. **The suite is the bottleneck,
not the analysers.**

## Step 2 of the plan — java (`cd4bda9`…`1dafd51`) and swift (`bda49af`…`4fa329c`) landed

R9 `key-parity(opt)` is **OK four-way** and its waiver is deleted (`d400cc2`) — **the ratchet reported it
STALE before anyone thought to check**, which is the both-ways design earning its keep. java was the last
engine on the array; rust and swift had already moved.

**java corrected me twice.** My `errors[].kind` measurement was STALE — I reported seven values, four of
which had been normalised at `74fd040`; the real remainder was two. And its test pins the closed set as a
**membership list written out longhand rather than read from the engine**, because *a test deriving its
admissible set from the code it checks cannot catch that code widening it* — the subject-and-oracle defect
avoided by design rather than found by review.

**Three java findings that were not in the brief:**
- **`whatif` read only the callgraph SIDECAR and never opened the report**, so a corrupt report produced a
  confident pre-edit all-clear from a file nothing had checked. Found only because reading the manifest was
  the first time that verb ever needed the report.
- **The prose channel made the same claim as the JSON.** Omitting `ok` while leaving `✓ within policy`
  standing would have MOVED the false all-clear, not removed it.
- **MCP `candor_where(effect="Net")` returned `{"directly":[],"inherited":[]}`** over a report whose
  manifest named the Net-performing class as unread. *"Nobody performs Net"*, confidently. My brief said
  "they shell out to the CLI, so there may be nothing to fix"; java's verdict on that reasoning is the
  keeper: **"the shelling-out is what hid the second site"** — exit codes and JSON come through, the scan's
  stderr does not.

**swift: `unverified --strict` and `fix-gate --strict` returned `ok:true`, exit 0, over an incomplete
report** — and `--strict` is how CI consumes both. Fixed with `whatif`'s shape rather than the gate's,
correctly: these are ADVISORY, so `ok:false` beside an empty array would assert "a hole exists, here it is"
— the fabrication mirror. `ok` omitted, manifest in its place, `--strict` exits 2.

### swift found a four-way question and refused to half-fix it — the right call

`DenyRule.unknownClasses` is parsed and populated, and **neither `deniedLayer` nor `unverifiedHoleRule`
consults it.** Same policy `deny Unknown[reflect,unresolved] app`, same report whose only hole is
`native:dlopen`:

    gate               exit 0   correct — the class is excluded
    fix-gate --strict  exit 1 + a remedy naming `app.nativeHole`   ← a red CI check for a boundary the
                                                                     policy does not deny
    unverified --strict  exit 0, ok:true                           ← THE MIRROR, and the worse half

The second is the one that matters: the layer passes while carrying an `Unknown`, so it **is** a
PASS-but-Unknown hole — and the verb whose entire job is *"not PROVABLY clean"* certifies it. Fixing only
the `fix-gate` over-charge (which is what I briefed) would close the fabrication and leave its silent mirror
open, which is [[feedback-fabrication-fixes-cause-misses]] exactly. Left whole for its own round with an A/B.

- [ ] **FOUR-WAY: does `unverified`/`fix-gate` consult the rule's `Unknown[…]` class filter?** Measured
      broken in swift; rust reported the same shape one layer down earlier this week (`unverified_hole_rule`
      computing `violates` from `r.effects` alone). **Measure java and ts before fixing** — and fix both
      halves together, since the over-charge and the under-report are one defect seen from two sides.

## STEP 2 COMPLETE — suite green, 77 live cells, 0 unwaived FAILs, 0 stale waivers

rust (`270d30b`, `ff565ea`, `531c415`) closes the round. 449 tests, clippy clean, 54 byte-equal
equivalence rows, PART 27 exit 0.

**rust's mutant M8 is the finding of the round, and java found it independently.** It built a mutant that
kept the ENTIRE JSON fix and deleted only the printed human line — **it survived the whole suite.**
Absence-asserts on `ok` cannot see the other channel, and the ruling says "no disclosure on ANY channel".
java hit the same thing from the other side: `✓ within policy` IS the prose `ok: true`, so removing the JSON
field while leaving the sentence standing MOVES the false all-clear rather than removing it. **Two engines,
two routes, one hole — and the suite was blind to it in both.** Ruled in `ec1a441`.

**And I scoped `0075987` to `whatif` — the eighth instance.** swift and rust independently measured
`unverified --strict` and `fix-gate --strict` returning `ok:true` over an incomplete report, with `--strict`
being how CI consumes both. `unverified` is the sharpest case the family has: **the verb that exists to say
"your green gate is not provably green" certifying a set it knows it cannot see all of.** Now bound for
every advisory verb.

The two engines' responses were opposite and BOTH right: **swift shipped the shape after reasoning to it
unprompted; rust measured the same defect and DECLINED to invent one**, citing this document's own rule that
an unspecified field becomes four guesses. The second is why the clause now exists rather than four
spellings of it.

### Process notes worth keeping, both from rust, both self-caught

- A mutant harness whose `/tmp` backup **failed silently** contaminated four mutants with a fifth's
  mutation. Redone with a git-based restore.
- `git checkout -- .` inside that restore **destroyed an uncommitted test** before it was committed.
  **A restore step in a measurement script is a destructive step** — [[feedback-evidence-dirs-are-sacred]]
  in a new costume.

- [ ] **`rewire` emits an `ok` key that §3.2's shape table does not list.** Found by rust in passing. Either
      the table is incomplete or the key is unspecified drift; it is the same unpinned-field class, so pin
      it before a second engine invents a meaning for it.

## THE `unknownClasses` ROUND — present in 3 of 4, and the same adjacent defect fired in all four

Suite green: exit 0, 77 live cells, 0 unwaived FAILs, 0 stale waivers, 0 per-shape vacuity.
java `acc6ee7` · swift `9aa7552` · ts `caac688`+`612b7d8` · **rust: measured null result, already correct.**

**The defect.** `deniedLayer` and `unverifiedHoleRule` computed from the effect SET alone and never consulted
the rule's `Unknown[…]` / `Net[…]` class filter, which lived inlined inside the gate and nowhere else. Two
halves of one bug: `fix-gate --strict` raised a red CI check and a hoist plan for a boundary the policy does
not deny, while **`unverified --strict` — the verb that exists to say "your green gate is not provably
green" — certified the same hole clean.**

**Two measurements make the scale concrete, and both are on real code:**

- java's PARTITION property. The gate and `unverified` must partition the `Unknown`-bearing set. On its own
  407-function report, 72 such functions: `deny Unknown[dispatch,unresolved]` gave **gate 0 + unverified 0**
  — *a wholly green gate over 72 unproven `Unknown`s with nothing said about any of them.* Gate verdicts
  came out **byte-identical** across the fix, so it moves what is DISCLOSED and never what is DECIDED.
- swift's count: up to **459 functions on pollen and 54 in its own sources were NEITHER a violation NOR a
  disclosed hole** — silently certified. After: **0**, every policy. And zero real disclosure loss: the ~292
  remedies that vanished were all for functions the gate charges ZERO violations on, so `--strict` had been
  reddening CI on every one.

### THE SAME ADJACENT DEFECT FIRED IN ALL FOUR ENGINES

Making the predicate filter-aware is what first lets a NARROWED rule *be* the rule a hole is disclosed
under — and every engine's upgrade path then dropped the bracket, printing the operator's
`deny Unknown[reflect,unresolved] app` back as the wide rule and advising the nonsense
**`deny Unknown Unknown app`**. On the Net sibling ts's advised `deny Net Unknown app`, **silently
un-narrowing a rule scoped to one destination class.** Dormant in every engine until the fix reached it.

**This is the fifth firing of the hazard on this rung, and the first where the lesson propagated instead of
recurring**: rust had settled the shape in `736957b`, the queue recorded it, and **ts read that record and
matched rust byte-for-byte rather than rediscovering it.** That is the first time this session a recorded
lesson prevented a defect rather than explaining one after the fact.

### rust's null result is the model for how to deliver one

Already correct — `481269b` pointed BOTH consumers at one `rule_hits` decision in a single commit. But it
did not stop at "I looked and it is fine": it **built the pre-`481269b` binary in a worktree and ran the
identical 10-row matrix against it**, reproducing the defect on all 6 filtered rows and none of the 4
unfiltered controls. *A null result is worthless without proof the measurement can fail*, and that is the
proof.

### Judgement calls worth keeping

- swift: **an empty class set means NOT-forbidden**, and that one choice is the disclosing one for BOTH
  callers. Which is why the matcher takes the **unfloored** map while `--class` keeps the **floored** one —
  floor the empty set to `unresolved` and `deny Unknown[unresolved]` starts firing on functions nobody
  classified, **re-fabricating in `fix-gate` and re-swallowing in `unverified` at once.** One principle,
  two maps.
- ts kept its OWN manifest element rule rather than copying swift's stricter one, because swift's would make
  the advisory verb **less sensitive to incompleteness than the gate over the same bytes** — this rung's own
  defect one layer down. A shape is copied for its reasoning, not its familiarity.
- java declined to normalise effect-name ORDER while fixing the filter: that misquote names the same rule
  and is what PART 12c compares four-way. **A filter is the case where reconstruction changes meaning; an
  ordering is not.**

- [ ] **`netClasses` has the identical shape and is NOT fixed** (swift measured it, correctly did not
      attempt it): under `deny Net[external] app` a fn reaching only internal hosts passes the gate, and
      `unverifiedHoleRule` still treats it as a real violation and returns nil — so an `Unknown`-carrying
      passer goes unnamed. Unlike reason classes it **cannot be derived from the fields `FixFn`/
      `UnverifiedFn` carry** (it needs the host surface plus the partner set), so it is a data-threading
      job, not a conjunct. Four-way.
- [ ] **`conditional` is one-engine.** Pinned in `6f30540`, implemented only by rust; java measured its own
      absence. The pin got ahead of the implementations, which was the point — but three engines still owe it.
- [ ] **swift and ts now disagree on manifest ELEMENT leniency** (swift skips a member with no string
      `path`, ts counts any object). ts's reasoning is recorded above and is sound; rule it or converge it
      before a third engine invents a third answer.

## java's netClasses/conditional round — a null result, a bigger defect than briefed, and a live measurement trap

**ITEM 1 was a measured null result** (`e948ce0`). java's `classNarrowingFires` takes a **`GateInput`**, which
carries `netClasses()`, rather than an effect set — so threading it into `unverifiedHoleRule`/`deniedLayer`
last round covered the Net axis for free. My data-threading argument was right in general and **had already
been paid** in java's shape.

It proved the null the right way: A/B against a jar built from `acc6ee7^`, so the instrument was shown able
to fail first, then the partition property at scale on **httpclient5-5.6.1** (2395 fns, 393 Net-bearing):

    deny Net[known-telemetry]   PRE gate 0 + unv 114 ✗    HEAD gate 0 + unv 389 ✓
    deny Net[unknown-host]      PRE gate 393 + unv 114 ✓  HEAD gate 393 + unv 114 ✓

**And it explained why this axis went unmeasured while its sibling did not: candor-java's OWN report has ZERO
Net-bearing functions**, so the Net axis is vacuous on the corpus the Unknown axis was measured on. *A
self-scan is a corpus with a shape, and the shape decides which defects it can show you.*

**ITEM 2's defect was bigger than "absent field"** (`8b98e09`). `whatif` **REBUILT** the rule from `scope`
plus the effect asked about: `deny Unknown[reflect] app` → `deny Unknown app`, and `deny Net Db app` →
`deny Net app` — **losing the operator's other denied effect entirely.** Both halves had to land together,
which is what the SPEC text argues for itself. `narrowingCondition` is deliberately a SIBLING of
`classNarrowingFires`, not a reuse: `unverified`/`fix-gate` read a signature that EXISTS, `whatif` does not.

### THE MEASUREMENT TRAP, and it nearly confirmed the wrong answer

I told java to read rust's actual JSON rather than my prose — correct, and load-bearing twice, because
**`candor-query` ON THE PATH IS A STALE 2026-07-20 BUILD** that still shows the pre-fix behaviour.
Confirmed: `~/.cargo/bin/candor-query` dated 2026-07-20 against `target/release` dated 2026-08-01. Reading
the reference implementation through the PATH binary would have confirmed the OLD shape as normative.

- [ ] **`~/.cargo/bin/candor-query` (and whatever `candor` dispatches to) is ~12 days behind the repo.**
      Every "read the reference engine" instruction is only as good as which binary answers. Refresh the
      local install, and consider whether `candor doctor` should compare the installed engine's build id
      against the repo HEAD rather than only checking spec agreement between engines — **two stale engines
      agree with each other perfectly.**

Nothing in this session's own measurements was contaminated: the conformance suite rebuilds its engines, and
every ad-hoc probe here used an explicit `~/git/…/target/release/` path. Verified, not assumed.

## The netClasses/conditional round — CLOSED, suite green (77 live cells, 0 unwaived FAILs)

**Two measured null results and two real fixes**, which is the right ratio for a round briefed from one
engine's finding:

- **rust** — already correct on both axes (verified last round with a pre-fix binary A/B).
- **java** (`e948ce0`, `8b98e09`) — `netClasses` a NULL: `classNarrowingFires` takes a `GateInput` carrying
  `netClasses()`, so last round's hoist paid for both axes at once. `conditional` implemented, and its
  defect was bigger than absent-field: `whatif` **rebuilt** the rule from `scope` + the effect asked about,
  so `deny Net Db app` printed as `deny Net app` — losing the operator's other denied effect.
- **swift** (`1e20e34`, `40ae8b0`) — `netClasses` PRESENT and fixed. Zero-loss A/B: **+49 holes newly named
  on pollen, 0 lost, 0 gate verdicts moved** (12/12 byte-identical). `conditional` measured N/A with an
  argument rather than an absence — no swift verb asks a hypothetical, and after the fix a narrowed rule
  over a real `Net` is *evaluated*, not deferred.
- **ts** (2 commits) — `netClasses` a NULL (`classFilterExcludes` takes the effect as an argument and always
  handled both axes), but it PINNED the scan route's Net half, which was the one place needing data
  *threaded* rather than a conjunct. `conditional` implemented and now **14/14 differential rows byte-match
  candor-rust's `violations` array.**

**The upgrade defect fired a FIFTH time, and swift's Net-axis harm is the worst version yet:** under
`deny Net[unknown-host] app` the tool offered `deny Net Unknown app` — **an edit that silently widens the
denial from one destination class to ALL of them while presenting itself as one added token.** 408–410 rows
per pollen run carried it.

### Two false alarms, both from the same cause, both costing investigation time

ts reported a `rust equivalence` FAIL; a clean run has it OK. It ran PART 27 while rust's binary was
mid-rebuild. **java flagged the identical thing last week** ("cross-engine PARTs are unreliable right now
because the sibling repos are moving under them"). Twice is a pattern:

- [ ] **Cross-engine PARTs run against sibling repos that other agents are actively rebuilding.** The
      failure looks exactly like a real divergence and is not. Either the generators should record each
      engine's build id alongside its cells (so a reader can see the arms were not contemporaneous), or
      parallel rounds should not run PART 27 per-agent at all and leave it to the coordinator's single run.

### Two engines independently caught a control that lied

ts's first pre-fix scan measurement showed "no note" — **because the worktree had no `node_modules` and the
scan CRASHED.** Right headline, wrong reason. rust caught the same class last round (a stale scratch file
injecting a phantom function). *An absence measured through a broken instrument is indistinguishable from
an absence.*

- [ ] **RULING OWED — the answerability gap on advisory verbs, now raised THREE times.** Over a report
      carrying `hosts` but no `netClass`, `gate --report` REFUSES (exit 2, §3.1 answerability), while
      `fix-gate`/`unverified` answer from a fallback derivation — so `unverified` is **silent on an
      `Unknown`-carrying function the gate could not judge.** Same cardinal-sin shape as the narrowing
      defect, but arising from ANSWERABILITY rather than narrowing. Currently documented as intentional
      ("no refusal channel, so a hedge beats a hole"), and closing it needs a ruling on **what `unevaluated`
      looks like on an advisory verb** — which `612b7d8` already noted has no ruled shape. ts reported
      rather than deciding, correctly. **This is the third time the missing refusal channel has surfaced;
      it should be ruled rather than re-noted.**

## R11 CLOSED FOUR-WAY — suite green, 81 live cells, 2 waivers left (both R10 report-parity)

rust `e406e09` · java `ed4dcda` · swift `71732ff` · ts `1c664a1`. All four R11 waivers deleted hours after
being written; each named its own exit condition and every engine met it.

### FOUR ENGINES, FOUR DIFFERENT MECHANISMS — the case for a comparison, proved

    rust    the hole predicate REQUIRED `Unknown`, so a Net-only entry was never a candidate at all
    java    two OPPOSITE conditions collapsing to one `false` — "the filter says a different class" and
            "the field the filter reads is absent". *That collapse was the defect.*
    swift   `unverified` only ever considered `Unknown`-carrying functions; the entry had NO CHANNEL
    ts      a fallback derivation — **the only mechanism my clause actually described**

**A rule phrased against any one of them would have missed the other three.** The clause named ts's
mechanism because ts's is the one that had been measured, and rust corrected it within the day. This is the
first law in the rung stated as an invariant rather than a behaviour, and it is the first to survive contact
with three mechanisms nobody had seen.

### It also corrected its own scope twice

`fix` was not named in the ruling. **rust measured it as WORSE than `fix-gate`** (which already routed
through the gate's firing decision and merely mis-set `ok`), and ts found it is *"the one the LSP code
action and MCP tool run"* — the surface an agent acts on. Ninth instance of naming one verb and not its
sibling; amended in `ad3ff08`.

### The best implementations made the law true by CONSTRUCTION rather than by matching

rust **deleted `reason_class_acc`**, the verb's private copy of the gate's fixpoint, so both advisory verbs
now read the gate's own signature. swift routed `gate --report` itself through the new predicate, on the
reasoning that *a law which is a comparison cannot be checked from two implementations of the thing
compared.* Neither can drift back.

### Standing bar 7p changed what the evidence WAS, on two engines

- **rust**: its four usual corpora carry **0** entries of the shape (`net_classes_of` floors every one), so
  their 440-run A/B "proves zero loss and nothing else". It measured value on **three real legacy reports
  found on disk** (spec 0.8 and 0.5) — 726 functions newly named.
- **swift**: pollen and its own `Sources` carry **0** reachable entries, because *this producer floors
  `netClass` and records a reason beside every `Unknown`* — **a report this engine wrote cannot reach the
  defect.** The reachable case is a report ANOTHER producer wrote, which is precisely what `gate --report`
  exists for. The defect is structurally supply-chain-only for a self-producing engine.
- **ts** swept 968 reports / 153,492 entries: **106 carry the exact shape**, all spec 0.4–0.15 — from before
  the field existed.

### Self-caught mirrors, both worth keeping

swift's first cut withheld `fix`'s plan by answering `crossing: false` — **over a CERTAIN crossing whose only
unadjudicable function is a hoist target, that turns a violation the gate charges into a non-finding.**
`crossing` now states only what is known. And ts's mutant audit found deleting the withhold from
`deniedLayer` was *invisible on the Net axis* but **live on the Unknown axis**, because `reasonClassesMatch`
floors an empty set at `unresolved`; three rows added.

- [ ] **⚠ UPGRADE NOTE for the 0.24 release.** The exit code is verdict-adjacent: a `--strict` CI step on
      `unverified`/`fix-gate` that read GREEN over a report the gate refuses now exits 2. **That green was
      the defect** — but it will present as a new failure to anyone upgrading, and the release notes must
      say so plainly rather than let it look like a regression.
- [ ] **ts found a PRODUCER defect while sweeping**: candor-ts's `interfaceUnion` synthetic entries never
      get a `netClass`, so the engine **publishes entries its own gate cannot judge** — one current-spec
      (0.23) instance in 153k. Back-filling a class for an entry whose hosts were never collected is its own
      ruling.
- [ ] **swift residual, stated not papered over**: when `fix-gate` withholds a plan it drops the *crossing*
      with it — `remedies[]` has no shape for a crossing without a plan, where single-function `fix` does.
