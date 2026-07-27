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
| **java** | `if (!de.effects.isEmpty()) put(h, de)` — last **non-empty** wins | keeps an answer; order-dependent |
| **ts** | merge into a Set — **union** | sound over-approximation, order-independent |
| **swift** | trust level decides first, then withdraw within a level | `ca5feb0`; hedged, not silent |

**java's rule is not what the review reported.** "Last-wins" is right only between two *effectful* claims;
the `!isEmpty()` guard means **a pure claim can never erase an effectful one**, which is the direction that
matters. So java is unsound only in *choosing* between two non-empty claims — a precision loss, never a
purity claim. That guard looks accidental and is load-bearing; it should be commented as such.

**But java's choice is arbitrary in a way worth seeing.** Measured: the same two reports give the consumer
`['Net']` as `a-Exec.json` + `z-Net.json`, and `['Exec']` as `z-Exec.json` + `a-Net.json`. **The effect
depends on the filename.** Rename a file, change the answer.

**rust is the only unsound one**, and it is unsound in the worst direction: the consumer disappears from
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
