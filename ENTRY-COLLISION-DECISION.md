# Two chained reports, one key, different answers — what should an engine do?

**Status: a decision the spec does not make, measured across all four engines 2026-07-27. Nothing changed
in any engine on the strength of this note; it exists so the change is made once, deliberately, rather than
four times by accident.**

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
