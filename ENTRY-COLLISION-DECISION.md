# Two chained reports, one key, different answers — what should an engine do?

**Status: DECIDED 2026-07-27 — adopt the union. The gating measurement (item 1 below, "what a union does
to rust's corpus") is done and is at the foot of this note. It changed the reasoning as well as confirming
the recommendation: the objection this note treated as the real cost does not describe anything in the
corpus, and the cost of withdrawing is larger than "effects". No engine has changed yet; the four-way
implementation is queued behind this decision so it is made once rather than four times by accident.**

## Why it is live

Two reports covering one package in one dep directory is ordinary, not pathological — measured at 7/167 dep
reports in candor-rust, 9/259 in pgman, 30/378 in ebman. It arises from a dep dir that accumulates, from
`--workspace` prepending its own directory to `CANDOR_DEPS`, and from a package scanned twice at different
versions. SPEC §2.1 covers the *staleness* downgrade and says nothing about two reports disagreeing.

## What the four engines actually do — measured, not read off the code

| engine | rule | verdict |
|---|---|---|
| **rust** | WITHDRAW the key (never-guess) | consumer goes **ABSENT** ⇒ a ⟨0.21⟩ purity claim. **Unsound.** |
| **java** | `if (!de.effects.isEmpty()) put(h, de)` — last **non-empty** wins | keeps an answer; order-dependent — **and a stale `{Unknown}` erases a trusted effect (measured, both orders): `deny Fs` exit 1 → 0** |
| **ts** | merge into a Set — **union** | sound over-approximation, order-independent |
| **swift** | trust level decides first, then withdraw within a level | `ca5feb0`; hedged, not silent |

**java's rule is not what the review reported** — and my first reading of it, below, was ALSO wrong. The
`!isEmpty()` guard means a *pure* claim (`[]`) can never erase an effectful one, and I concluded from that
that java "is unsound only in choosing between two non-empty claims — a precision loss, never a purity
claim". **That conclusion is false, and a later review caught it. `{Unknown}` IS NON-EMPTY.**

The §2.1 staleness downgrade turns a stale report's entries into exactly `{Unknown}`, which sails through
the guard and overwrites a trusted report's concrete effects. **Measured, both file orders:** a trusted
report carrying `Fs` plus a stale report for the same package gives the consumer `['Unknown']` — the `Fs`
is gone. `deny Fs` goes **exit 1 → exit 0**.

It is not a purity claim (the `Unknown` is disclosed, so `deny Unknown` still bites), which is why it is not
the cardinal sin. But it is a gate-level defect on the commonest policy shape, and **a report the engine
has explicitly refused to trust gets to erase a fact from a report it does trust.** The guard is real and
it is load-bearing against a `[]` claim; it is not the safety property I said it was.

**But java's choice is arbitrary in a way worth seeing.** Measured: the same two reports give the consumer
`['Net']` as `a-Exec.json` + `z-Net.json`, and `['Exec']` as `z-Exec.json` + `a-Net.json`. **The effect
depends on the filename.** Rename a file, change the answer.

**rust is the only one producing a purity claim** (java's defect above is a gate flip, not silence), and it is unsound in the worst direction: the consumer disappears from
`functions` entirely, which under the completeness manifest is a positive claim of purity. Filed separately
with its own measurements.

## The recommendation: ts's union

Union the effects. It is the only rule that is *sound* (the runtime may execute either body, so their union
is the honest over-approximation), *order-independent* (no filename decides an effect), and *never a purity
claim* (a union with anything non-empty is non-empty).

The objection is real and should be stated: two entries under one key may be two **different functions** that
merely collide, and unioning then charges one's effects to the other — a fabrication. That is exactly why
rust withdraws. But:

- withdrawing trades the fabrication for the **cardinal sin**, which the standing bar forbids in that
  direction specifically;
- java and ts have both shipped non-withdrawing rules and neither has produced a reported fabrication from
  this path;
- the collision that motivates withdrawal is a *leaf* collision, and the full-qualification key
  (rust `5feba18`, swift `9a51e7f`) exists precisely to make those rarer.

**It also dissolves rust's open row.** Rust's alternative fix — disclose `Unknown` on a withdrawn key — was
built and measured at **15–20% of functions newly carrying `Unknown`** (30/200 pgman, 108/544 ebman). A
union needs no disclosure at all, because nothing is withdrawn. The same defect, closed at a fraction of the
cost.

## What is NOT settled, and must be measured before anyone acts

1. **What a union does to rust's corpus.** Unmeasured. Do it before landing.
2. **Whether the union should extend to the literal surfaces.** Probably yes (a surface union is already the
   sound reading), and rust `6f2210c` established that most collisions agree on effects and differ only in
   surfaces — 1536/2041 on pgman, 2255/3276 on ebman.
3. **The `Unknown`-vs-effect asymmetry.** One entry `['Unknown']` and another `['Fs']` unions to
   `['Fs','Unknown']`, which is right but noisier than either. Check the rate.
4. **Whether swift's trust-level-first rule composes with a union** or replaces it.

## If adopted

A conformance PART pinning it four-way, with the fixture that already exists in three engines: two reports,
one key, different effects, and the consumer must carry both — verified to catch per engine, and a row that
FAILS for an engine that withdraws or picks.


## Correction, 2026-07-27 — and it strengthens the recommendation

The paragraph above marked as my error is worth keeping visible rather than editing away, because it is the
second time in this note's short life that a claim about java's collision rule has been wrong: the review
before it reported plain "last-wins", I corrected that to "last non-empty wins" and over-read the guard as a
safety property, and a third review found the `{Unknown}` path through it. **The rule has now been described
three times and been wrong twice.** That is itself an argument for the union: a rule nobody can state
correctly on three attempts is not a rule a policy gate should depend on.

It also removes java from the "safe, merely imprecise" column. Every non-union engine now has a measured
gate-level failure — rust's is a purity claim, java's is a `deny Fs` flip — and the union has neither,
because it never discards a claim it was given.


## The gating measurement, 2026-07-27 — read-only over three real dep corpora

Item 1 said "what a union does to rust's corpus is unmeasured — do it before landing". Done, offline over
the actual `.candor/deps` trees of candor-rust (173 reports), pgman (268) and ebman (409), with no engine
built or run. Two false starts are recorded at the end because both produced flattering zeros.

| | candor-rust | pgman | ebman |
|---|---|---|---|
| distinct keys | 16 355 | 21 787 | 42 402 |
| colliding keys | 705 (4.3%) | 1 960 (9.0%) | 4 782 (11.3%) |
| …disagreeing on `inferred` | **2** | **8** | **113** |
| rust WITHDRAWS ⇒ absent ⇒ purity claim | 2 | 8 | 113 |
| java order-dependent (rename a file, change the effect) | 0 | 0 | 32 |
| java stale-`{Unknown}` erases a trusted effect | 0 | 0 | 24 |
| **items a UNION adds beyond the best single entry** | **0** | **0** | **7** |

**The union's total cost across all three corpora is 7 effect-items.** It closes 123 purity claims and 24
`deny`-flips to buy them.

### The finding that changes the reasoning: every disagreement is a VERSION PAIR

This note's stated objection to the union was that "two entries under one key may be two **different
functions** that merely collide, and unioning then charges one's effects to the other — a fabrication."
**Not one measured disagreement is that.** Every single one is the same function in two versions of the
same crate, both legitimately in the tree because cargo permits semver-major duplicates:

```
thiserror_impl#valid::Enum::validate       ['Unknown'] @1.0.69   vs  [] @2.0.18
rustix#backend::libc::time::…::timerfd_create   [] @0.38.44  vs  ['Unknown'] @1.1.4
http#uri::authority::Authority::from_static ['Unknown'] @0.2.12  vs  [] @1.4.0
hyper#client::conn::http1::Builder::handshake   ['Log'] @0.14.32 vs  [] @1.9.0
hyper#client::conn::http2::Builder::handshake   ['Log','Unknown'] @0.14.32 vs ['Clock'] @1.9.0
```

That last-but-one line is a live cardinal sin on one of the most-depended-upon crates in the ecosystem:
hyper 0.14's `Builder::handshake` logs, hyper 1.9's does not, both are in the tree, and rust's withdrawal
makes the consumer read the key as **absent — a positive claim of purity under ⟨0.21⟩**.

For a version pair the union is not a hedge, it is the *correct* answer. Both bodies are in the build; which
one a given caller resolves to is a fact the package-scoped key cannot express; so the runtime may execute
either and their union is simply what the key means. The fabrication objection survives only for a genuine
leaf collision between unrelated functions — and this corpus contains none of those to trade against.

### The second finding: withdrawing costs more than the effect

This note framed the choice as being about effects. It is about the whole entry. Disagreements by field:

| field | candor-rust | pgman | ebman | union adds (all three) |
|---|---|---|---|---|
| `inferred` | 2 | 8 | 113 | 7 items |
| `invisible` (the κ ledger) | 30 | 37 | 273 | 185 items |
| `calls` (graph edges) | 57 | 120 | 326 | 350 items |
| `direct` | 3 | 21 | 86 | **0** |
| `unknownWhy` | 5 | 27 | 36 | **0** |

Rust withdraws the KEY, so it withdraws all of these at once: the coverage disclosure the κ ledger exists to
carry, and the call edges the graph queries walk. `direct` and `unknownWhy` union at **zero** cost in every
corpus — one side is always a subset of the other, so the union is just "the one that said something".

### What is still NOT settled — item 2 is UNDER-POWERED, not answered

Item 2 asked whether the union should extend to the literal surfaces. This corpus **cannot answer it**, and
saying so matters more than the tidy zero I first wrote down. Non-empty surfaces among *colliding* keys:
`paths` 0/1/2, `hosts` 0/0/2, `cmds` 2/0/0, `netClass` 0/0/9. Where they exist they agree, but a sample of
0–9 is not evidence. The same reasoning that settles effects applies (both versions are in the build, so
union), but it is an argument here, not a measurement — and this note's own history says which of those to
trust.

Items 3 and 4 stand. Item 3 is answered in passing: 31 of ebman's 113 unions mix `Unknown` with a concrete
effect, and the largest union anywhere is 3 effects, so the noise is bounded and small.

### Two false starts, kept because both produced flattering zeros

1. The first loader read `<deps>/*.json`. Reports actually live one directory per crate (`<deps>/<crate>@<ver>/report.<pkg>.scan.json`), so it loaded **0 reports** and reported 0 collisions across all three
   corpora — a clean bill of health from an empty measurement.
2. The first surface pass keyed on `hosts`/`paths`/`cmds`/`tables` and found **0 disagreements everywhere**.
   Three of those fields are usually absent from these reports and `tables` never appears at all, so it was
   comparing absent keys to absent keys. This is standing-bar item 7d ("an empty dep report gives a
   meaningless ABSENT") recurring in a new place, and it is why the vacuity check above exists.


## The rule generalises, and it arose a second time the same day — in a different index

This note decided one collision: two dependency reports carrying one key with different answers. Hours
later the same shape appeared in the **return-type index**, and the resolution is the same sentence.

Chasing why a chained dependency's methods were failing to resolve, the Rust engine found that **37 of the
57 genuinely-unresolvable markers on one corpus were a single function** — `chrono`'s `Utc::now`. Its report
carries the effect (`offset::utc::Utc::now ['Clock']`); only its *return type* was withheld. The cause is a
collision that is not one: `chrono` declares `pub fn now() -> DateTime<Utc>` **twice**, under mutually
exclusive `#[cfg]`s (native and wasm32). The scan walks both arms by design, the return index sees two
same-named definitions, and the never-guess rule drops the entry — **even though both candidates name the
same return type.**

> **When the colliding candidates AGREE, the collision is not a reason to withhold.**

The never-guess rule exists to prevent *picking* between two different answers. It was never meant to
suppress a case where there is nothing to pick between. Applied here it costs nothing and recovers over half
of that corpus's unresolvable chained markers — **by determination rather than suppression**, which is the
⟨0.24⟩ ordering, and on every call spelling at once, so it cannot reintroduce the spelling asymmetry that
was closed the same day.

Two things this says beyond the immediate fix:

**The rule belongs to the never-guess principle, not to either index.** It has now appeared in the entry
index (this note) and the return index (above). Any index in the family that drops an ambiguous key should
be asked the same question: *does it check whether the candidates disagree, or only whether there is more
than one?* The second is the cheaper check and it is what both sites implemented.

**A withheld answer is a silent one.** Neither site logged anything. The entry-index case surfaced as a
consumer vanishing from `functions` — a purity claim. The return-index case surfaced as a corpus-wide
disclosure that looked like imprecision and was really one crate's `#[cfg]` pair. In both, the engine knew
the answer and declined to say it, and nothing in the output distinguished *"I could not determine this"*
from *"I determined it twice identically and threw it away."*
