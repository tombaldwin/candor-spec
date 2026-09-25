#!/usr/bin/env python3
"""
PART 92 — THE CHAINED-DISPATCH UNION differential (FOUR-WAY, SPEC §4 ⟨0.39⟩).

THE DEFECT IS A TOGGLE, AND IT RUNS THE WRONG WAY.

  a library whose public abstraction has ZERO local implementors  -> a chained consumer gets a
                                                                     disclosed `Unknown`   (correct)
  add ONE PURE implementor to that same library                   -> the consumer is SILENTLY
                                                                     CERTIFIED PURE       (the sin)

So **adding a pure implementation to a library REMOVES a disclosure from every consumer of it.** That is
the ⟨0.21⟩ cardinal sin reached by a route no single scan can see: nothing is wrong with either package
on its own, and the loss only exists in the join.

  SOUNDNESS R475 (rust + java, identical, 2026-09-17)  LIVE ON REAL CODE. `ratatui-core`'s
      `Terminal::size` dispatches `Backend::size` over its sole local implementor `TestBackend` (pure);
      `ratatui-crossterm`'s `CrosstermBackend::size` performs `Ipc`. An application chained onto BOTH
      reports that function ABSENT, and `deny Ipc` and `pure` over it BOTH exit 0.

WHY THE FIXTURE MUST BE THREE PACKAGES — AND, FOR ONE ARM, FOUR. The effectful implementor lives in a
THIRD package — neither the dispatching dependency nor the consumer. No two-package arm can express the
finding, and §4 ⟨0.39⟩ says so in the clause itself: *"no two of them are separable — the effectful implementor in the measured case
lives in a THIRD package"*. `split_arms.py` was built for P1's two-package split; the `Scanner` layer it
now carries is the extension that made an N-package chain expressible without a second copy of the
engine plumbing (R288: fifteen copies of one instrument have no owner).

WHAT MAKES THE CROSS SOUND — stated because the coordinator got exactly this wrong on the day R475 was
filed, reporting a cross-engine contrast that was FIXTURE-INDUCED because the two arms differed in their
inputs rather than their engines.

  **The consumer's function under test is the SAME SOURCE TEXT in c1, c2, c3 and c5.** Byte-identical,
  asserted by the generator itself (`_assert_identical_consumers`), not by care. Between c2 and c3 the
  ONLY thing that differs in the entire experiment is the implementor set inside the dependency; between
  c3 and c1 the only thing that differs is the EXISTENCE of a third package and its report on
  CANDOR_DEPS. Nothing about the consumer moves, so nothing about the consumer can explain the answer
  moving.

THE CONTROL ARMS ARE NOT OPTIONAL. Widening a union is exactly where this family has repeatedly turned a
silence into a fabrication, and the ⟨0.39⟩ cost model is explicit that nothing may move from disclosed
to silent and no implementation may start hedging:

  c2_zero_impl  the zero-implementor case MUST REMAIN a disclosed `Unknown`. If a fix reddens this arm's
                sibling and greys this one, it has traded one silence for another — and this arm is also
                the left-hand side of the toggle, so a fix that quietly loses it has deleted the very
                contrast the part exists to pin.
  c3_pure_only  a consumer over a library whose only implementor ANYWHERE is pure is LEGITIMATELY pure
                and MUST STAY pure. This is the fabrication guard: an engine that unions indiscriminately
                — charging every consumer of a dispatching library for effects nobody implements —
                reddens here and nowhere else.
  c4_sealed     a sealed/private abstraction whose implementors are all local and visible keeps an EXACT
                union and gains NO hedge. §4 is explicit that this case stays exact; an engine that
                starts hedging on "this call dispatched" rather than on "an implementor is invisible"
                fails here.
  c6_middle_package  a FOURTH package, and the arm c1 cannot reach: the package that DISPATCHES owns
                neither the abstraction nor any implementor of it. See the note beside `ARMS` for why
                three packages cannot express this and why c6 is not in `CROSS_ARMS`. SOUNDNESS R504.
  c5_unchained  the same fixture as c1 with CANDOR_DEPS UNSET. Not a defect arm — a REFERENCE, and the
                one that makes the clause's central observation concrete: unchained, the consumer says
                `[]` + `invisible: [iface, effimpl]`; chained, it says nothing at all. **Chaining does
                not flip a gate here, it DELETES the disclosure** that ⟨0.30⟩'s non-gating ruling for
                `invisible` depends on being present. A mechanism that makes reports better must not make
                silence cheaper.

WHY THE ASSERTION IS AT THE CONSUMER AND NOT ON `dispatchesOn` / `interfaceUnion`. ⟨0.39⟩ imposes three
obligations and says no two are separable. Only their JOINT effect is observable without naming an
implementation strategy, so the part asserts the joint effect — what the consumer's row says — and PRINTS
the two producer-side legs as diagnostics (measured: `dispatchesOn` absent and `interfaceUnion` null in
all four engines' producer reports today, which is why c1 fails everywhere). Asserting the wire shape
would pin an engine to one route to the property; asserting the consumer's row pins the property.

EVERY FIXTURE COMPILES, AND THAT IS ENFORCED RATHER THAN CLAIMED. A control that asserts an ABSENCE over
a program that cannot be built is not weak evidence, it is NO evidence — absence is also what a broken
engine produces. `cargo build` / `javac` / `tsc --noEmit` / `swift build` run over every rendered arm,
and a build failure FAILS the part. Set CANDOR_PART92_NOBUILD=1 only to iterate; the run says loudly
when the proof was skipped.

AN ABSENT CONSUMER ROW IS A FAILURE HERE, NOT A SKIP — SOUNDNESS R636/R677. Every engine omits pure
functions from `functions[]`, so a broken engine and a correct one produce the same bytes when the answer
is silence: `facts()` renders a missing entry as `eff=∅, unknown=False, invisible=∅`, which satisfies
every `hasnt`, every `unknown=False` and every `invisible=False` in the table below. Driven against that
value, 11 of these 13 arms went red on their other assertions and TWO PASSED — `c3_pure_only` and
`c12_consumer_pure_only_union`, the second of which exists precisely because the first did not pin. So
`judge()` now rejects an absent row unless the arm carries a NAMED `absent_ok` licence, `--selftest`
drives that with no engine, and `assert_hasnt_is_reachable()` refuses a `hasnt` naming an effect no sink
in the arm's own fixture performs — four arms had one (`c2`, `c3`, `c9`, `c12`), which is the same
vacuity one level down. SPEC.md:4680 states the rule verbatim for this exact reason.

THE XFAIL TABLE. `c1_foreign_effectful` fails on ALL FOUR engines today — measured against the released
artifacts, spec 0.38 (candor-scan 0.38.4, candor-java 0.38.3, candor-ts 0.38.3, candor-swift 0.38.3).
Every one is declared as an `(arm, engine)` expectation rather than hidden, and **A PASSING XFAIL IS A
FAILURE HERE**: the moment an engine ports ⟨0.39⟩ this part goes red and that engine retires its own
line, in the same commit as the fix. That mechanism is what made PART 91 catch R477 on its first
execution; it is the only thing in the suite that notices an expectation which has quietly become true.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd      # noqa: E402  -- import-safe: work is behind a __main__ guard
import split_arms as sa            # noqa: E402

SPEC_CLAUSES = [
    ("§4 ⟨0.39⟩", "A CHAINED CONSUMER'S INHERITED SIGNATURE MUST CARRY THE EFFECTS OF EVERY IMPLEMENTOR "
                  "VISIBLE TO THE CONSUMER — its own and any chained report's — so supplying an "
                  "effectful implementor to a dependency is never silent."),
    ("§4 ⟨0.39⟩", "adding a pure implementation to a library REMOVES a disclosure from every consumer "
                  "of it"),
    ("§4 ⟨0.39⟩", "The consumer's join MUST union, per key, its own visible implementors with every "
                  "chained entry carrying that key."),
    ("§4 bounded-CHA", "a local abstraction with no visible implementor, too many, or an ambiguous name "
                       "is disclosed indeterminacy, never silent purity"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
NOBUILD = os.environ.get("CANDOR_PART92_NOBUILD")

# =====================================================================================================
# THE ARMS.
#
#   iface     which variant of the dispatching dependency: "impl" (one PURE local implementor),
#             "zero" (none at all), "sealed" (a private abstraction with one local EFFECTFUL impl)
#   third     is the third package (a FOREIGN implementor, effectful) rendered and chained?
#   chained   is CANDOR_DEPS set at all? (c5 is the unchained reference)
#   entry     which consumer function the row is read from
#   want      the assertion, per disclosure channel:
#               has       effects that MUST appear in `inferred`
#               hasnt     effects that MUST NOT
#               unknown   True/False = the `Unknown` marker must/must not be present (None = unasserted)
#               invisible True/False = the kappa ledger must/must not be non-empty
#
# `has`/`hasnt` rather than an exact set on the defect arm ON PURPOSE: the soundness claim is that the
# effect REACHES the consumer, and an engine that also hedges while carrying it has not violated ⟨0.39⟩.
# The exactness demand belongs on c4, where the clause really does say the union stays exact.
# =====================================================================================================
EFFECT = "Net"

# THE CARRIER EFFECT — SOUNDNESS R677/R678. A SECOND, DISTINCT effect, read from `gen_differential`'s
# vocabulary rather than re-spelled here (attack G: ask the authority, never reimplement it). Two arms
# needed an effect that is NOT `Net`: `c12` needs one its consumer legitimately CARRIES, so that "reads
# the dep's one pure implementor" and "produced no row at all" stop being the same bytes; `c2`, `c3` and
# `c9` need one that EXISTS in their fixture, so their `hasnt` can fail at all. Using `Net` for either
# would have collided with the very assertion under test in `c1`/`c5`/`c10`.
_FS = next(e for e in gd.EFFECTS if e["id"] == "fs")
CARRIER = _FS["sink"]           # {lang: statement}
CARRIER_EFFECT = _FS["effect"]  # "Fs"
ARMS = [
    dict(id="c1_foreign_effectful", iface="impl", third=True, chained=True, entry="dispatch",
         want=dict(has={EFFECT}),
         why="DEFECT: a FOREIGN effectful implementor in a third package must reach the consumer"),
    # `hasnt` carries the CARRIER effect for the reason spelled out on c3: `hasnt={Net}` alone is
    # VACUOUS BY CONSTRUCTION here (no third package, no sink in the `zero` dependency). This arm was
    # never at risk from it — `unknown=True` is its real assertion and absence fails that — but an
    # assertion that cannot fail should not be left in a table whose whole subject is unfalsifiable
    # greens.
    dict(id="c2_zero_impl", iface="zero", third=False, chained=True, entry="dispatch",
         want=dict(hasnt={EFFECT, CARRIER_EFFECT}, unknown=True),
         why="CONTROL: zero implementors anywhere MUST stay a disclosed Unknown (the toggle's left side)"),
    # SOUNDNESS R677/R678 — TWO CHANGES, BOTH ABOUT WHAT A GREEN CELL HERE MEANS.
    #
    # (a) `absent_ok`, NAMED rather than implicit. This arm is the one place in the table where an
    #     omitted row is the CORRECT answer: the consumer is genuinely pure and does not itself dispatch
    #     (it delegates to `iface::term_size`, whose own bounded CHA resolves the dep's one pure
    #     implementor), and SPEC §2 rule 3 licenses omitting a pure function. Demanding a row would score
    #     an engine on this arm's preference rather than on the contract. What the arm is FOR is catching
    #     a CHARGE, and a charge cannot be absent — so the licence costs the assertion nothing.
    # (b) `hasnt` gains the CARRIER effect, because `hasnt={Net}` ALONE COULD NOT FAIL: measured
    #     2026-09-25 by rendering every arm and grepping for its own sink, `c2`, `c3`, `c9` and `c12`
    #     contain NO `Net` anywhere — no third package, and neither the `impl` nor the `zero` dependency
    #     has a sink. R636 recorded that vacuity for `c12` only; it is four arms. The dependency now
    #     declares an effectful function the consumer never calls, so "an engine that unions
    #     indiscriminately — charging every consumer of a dispatching library for effects nobody
    #     implements" finally has something to charge, and this fabrication guard can go red.
    dict(id="c3_pure_only", iface="impl", third=False, chained=True, entry="dispatch",
         want=dict(hasnt={EFFECT, CARRIER_EFFECT}, unknown=False, invisible=False,
                   absent_ok="a pure, non-dispatching consumer — SPEC §2 rule 3 licenses the omission, "
                             "and this arm exists to catch a CHARGE, which cannot be absent"),
         why="CONTROL: only-pure-implementor-anywhere is LEGITIMATELY pure — the fabrication guard"),
    dict(id="c4_sealed", iface="sealed", third=False, chained=True, entry="sealed",
         want=dict(has={EFFECT}, unknown=False, invisible=False),
         why="CONTROL: a sealed abstraction's union stays EXACT — the real effect, and no new hedge"),
    # ⟨0.39⟩/R518 — THE SPELLING ARM, and the axis six arms never varied. c1-c6 all differ in WHICH
    # PACKAGE holds what; every one of them writes the abstraction at the package ROOT. R513 (rust) and
    # R512 (ts) were both defects in the SPELLING, and PART 92 was green with an empty xfail table
    # throughout — it could not have failed on either. This arm holds the topology of c1 EXACTLY and moves
    # only the declaration site, so "passes c1, fails c7" reads as "the engine keys on the written path".
    #
    # DECLARED INEXPRESSIBLE for java and swift rather than silently skipped, and for different reasons:
    # java has no re-export, so nesting the interface forces `iface.Api.Backend` through the consumer and
    # the implementor too — three variables instead of one, which is not this arm's question; swift has no
    # submodules within a target, and its analogue (a protocol nested in an enum, SE-0404) renames the
    # type to `Term.Backend`, with the same consequence. Both are worth their own arm; neither is this one.
    dict(id="c7_nested_abstraction", iface="nested", third=False, chained=True, entry="nesteddispatch",
         want=dict(has={EFFECT}), skip=("java", "swift"),
         why="DEFECT-SHAPE: an EFFECTFUL implementor declared in a MODULE inside the dependency (R513) — "
             "the LOCAL union leg, which is the one that had no fallback"),
    # ⟨0.39⟩/R533 — THE CONSUMER'S OWN FOREIGN SITE WITH AN EMPTY UNION, which `c2_zero_impl` does NOT
    # reach. In c2 the zero-implementor dispatch lives in the DEP (`iface::term_size`), where the dep's own
    # bounded CHA fires and the consumer inherits the hedge through the ordinary chain join. Here the
    # CONSUMER dispatches directly on the foreign abstraction — the `nesteddispatch` body, which is why
    # that branch is load-bearing (see app_body) — and NOTHING implements it anywhere.
    #
    # MEASURED 2026-09-22 on a hand fixture, same consumer body per language, one dep report, zero
    # implementors in both packages, only the ENGINE varying: **THREE OF FOUR READ SILENTLY PURE**, the
    # REFERENCE ENGINE INCLUDED. java `app.App.go` is `inferred: []`, `unresolved: false`,
    # `unknownWhy: null`, carrying `dispatchesOn` — so the engine KNOWS it is a dispatch — and `pure`
    # EXITS 0 over a call whose target it knows nothing about. rust the same plus a non-gating
    # `invisible`; swift the same. ts is the only engine that discloses `Unknown`.
    #
    # FILED AS A MEASURED DIVERGENCE, NOT YET AS A MUST. The tightening it implies — an EMPTY union at a
    # consumer's dispatch site reads `Unknown` — is a real ⟨0.40⟩ MINOR, and ⟨0.39⟩'s own cost paragraph
    # DECLINED the neighbouring hedge at 2.60% of functions across 435 libraries. This one bills every
    # middle library scanned alone. So the arm exists to PIN the divergence and make it retire loudly; the
    # clause waits on a corpus A/B per engine. ts passing is the existence proof that it is affordable
    # somewhere.
    # ⟨0.39⟩/R529+R530b+R532 — THE CONSUMER SUPPLIES THE IMPLEMENTOR, AND WRITES IT IN A PLACE ITS OWN
    # INDEX DOES NOT HOLD. The dep declares ONE PURE implementor, so the toggle's right side is present
    # and bounded CHA resolves happily to it; the consumer's own effectful implementor is written inside
    # a function body (rust `impl` in a block, swift a conformance in a func, java a LAMBDA — the one
    # shape with no class file, ts a structural literal, which is R512's closed shape and so a REGRESSION
    # PIN here rather than a new question).
    #
    # `disclosed` rather than `has`: ⟨0.35⟩ licenses COMPLETING the dispatch or DISCLOSING it, and after
    # R529 rust legitimately takes the hedge. Demanding the effect would score rust's licensed choice as a
    # failure and measure this arm's preference instead of the contract.
    dict(id="c8_body_local_implementor", iface="impl", third=False, chained=True, entry="escapedispatch",
         want=dict(disclosed={EFFECT}),
         why="R529/R530b/R532: an implementor the consumer's own body walk READ but its index does not "
             "HOLD must not be papered over by the dep's pure one"),
    # ⟨0.40⟩ — THE MIDDLE CASE `c3_pure_only` DOES NOT PIN, and the gap is one knob wide. c3 puts the
    # dispatch in the DEPENDENCY (`entry="dispatch"` -> the consumer calls `iface::termSize(b)`), where
    # the dep's OWN CHA resolves its one pure implementor and the consumer inherits a resolved answer.
    # This arm holds everything else and moves the dispatch to the CONSUMER's own body, which is the
    # site ⟨0.40⟩ actually governs: the dep has exactly one implementor, it is PURE, and the consumer
    # has none of its own.
    #
    # WHY IT IS THE ARM THAT SEPARATES THE TWO HALVES OF THE RUNG. Under the CONSUMER half alone the
    # consumer hedges on WIRE ABSENCE — all three silent producers drop a pure-only union entry
    # (`silence = purity`), so "no implementor" and "all implementors pure" are indistinguishable on
    # the wire and this arm reads `Unknown`, which is an OVER-disclosure. Under BOTH halves the
    # producer publishes the pure-only entry, the consumer can tell the two apart, and this arm reads
    # PURE — which is the target state asserted here.
    #
    # It was DECLARED xfail four-way on that reasoning and THREE ENGINES PASSED ON THE FIRST RUN — see
    # the XFAIL note for what each pass rests on, which is not the same thing in java/swift as in rust
    # (SOUNDNESS R646). Only ts's line remains. The failure direction is the opposite of
    # `c9_consumer_zero_union`'s, and having both means a port cannot satisfy one by breaking the other.
    # SOUNDNESS R677 — THIS ARM COULD NOT FAIL, AND IT WAS WRITTEN TO CLOSE c3's SAME HOLE.
    # As first written its `want` was `hasnt={Net}, unknown=False`, and BOTH halves are satisfied by a
    # report that never mentions `appSize`: `hasnt` was vacuous by construction (no `Net` anywhere in
    # this fixture) and `unknown=False` is what absence gives for free. So its green for java, rust and
    # swift did not distinguish *resolves the dep's one pure implementor* from *produced no row*.
    #
    # THE FIX IS A CARRIER, NOT A STRICTER `want`. `judge()` now rejects an absent row outright, which
    # would be enough IF ⟨0.39⟩ obligation 1's "a dispatching row is no longer absent" were relied on —
    # but that would make the arm red for a ⟨0.39⟩ reason and stop it measuring its ⟨0.40⟩ question. So
    # the consumer additionally CALLS a pure-to-it dependency function that performs the CARRIER effect.
    # The row must then exist and carry `Fs` for reasons that have nothing to do with the dispatch, and
    # `unknown=False` — the ⟨0.40⟩ question, *can the engine tell "no implementors" from "all
    # implementors pure"* — is asked of a row rather than of silence.
    #
    # THE COST, STATED: `c12` now differs from `c3` in TWO things rather than one — the dispatch site
    # (the knob) and the carrier call. The carrier is not an input to the dispatch question, and c4
    # already establishes four-way that a dep function's effect reaches a consumer through the ordinary
    # chain join, so a green `Fs` here is also evidence CANDOR_DEPS reached this arm's scan. `hasnt` is
    # dropped rather than kept vacuous: there is no `Net` in this fixture to fabricate.
    dict(id="c12_consumer_pure_only_union", iface="impl", third=False, chained=True,
         entry="pureonlydispatch",
         want=dict(has={CARRIER_EFFECT}, unknown=False),
         why="⟨0.40⟩ PRODUCER HALF: a consumer dispatching on a dependency whose ONLY implementor "
             "anywhere is PURE must read pure, not Unknown — which requires the producer to publish "
             "the pure-only union entry it currently drops"),
    # SOUNDNESS R595 — A CONSUMER-SUPPLIED IMPLEMENTOR REACHED THROUGH A MUTABLE GLOBAL, not through a
    # type. Measured in java first: the library declares a hook field with a PURE default and invokes it;
    # the consumer reassigns it with an EFFECTFUL callable. **Adding that pure default DELETES a
    # disclosure and a real effect from every consumer** — with the default absent the consumer reads
    # `["Fs","Unknown"]` and `deny` exits 1; with it present the consumer reads `inferred: []` and exits 0.
    #
    # THE CONSTANT: the consumer body is byte-identical to the control in every language; only the
    # library's hook default moves. That is how R595 itself was measured, and it is why this is an arm
    # rather than three agent reports — ⟨0.39⟩ says the open-world trade "stops being acceptable" across
    # a CHAIN because "the consumer supplies it, and the engine can see it", and that sentence is
    # engine-independent. Each language spells the mutable global differently (java a `public static`
    # field, swift a `public static var`, ts a property on an exported object since ES bindings are
    # read-only to importers, rust a `OnceLock` since it has no safe mutable static) — the SHAPE is what
    # is held constant, not the syntax.
    dict(id="c13_reassigned_field_hook", iface="hook", third=False, chained=True, entry="reassignhook",
         want=dict(has={EFFECT}),
         why="R595: a consumer-supplied implementor reached through a MUTABLE GLOBAL the dependency "
             "invokes — a pure default in the library must not delete the consumer's own effect"),
    # `hasnt` carries the CARRIER effect for the same reason as c2 — see c3's note.
    dict(id="c9_consumer_zero_union", iface="zero", third=False, chained=True, entry="nesteddispatch",
         want=dict(hasnt={EFFECT, CARRIER_EFFECT}, unknown=True),
         why="R533: the CONSUMER dispatches on a foreign abstraction nobody implements — an empty union "
             "must not read as purity"),
    # SOUNDNESS R548 — c5's REFERENCE claim is about ONE consumer shape, and the other one behaves
    # differently in one engine. c5's consumer calls a FREE FUNCTION that takes the abstraction
    # (`iface.termSize(b)`); this arm dispatches DIRECTLY on the value (`b.size()`), which is the
    # `nesteddispatch` body c9 uses — so this is c9 with the chaining removed, and it is the control c9
    # never had. Without it "unchained discloses via `invisible`" was pinned for one body shape and
    # ASSUMED for the other, in a part whose whole subject is that the two shapes resolve differently.
    dict(id="c10_unchained_direct", iface="zero", third=True, chained=False, entry="nesteddispatch",
         want=dict(hasnt={EFFECT}, unknown=False, invisible=True),
         why="R548/CONTROL for c9: unchained + DIRECT dispatch must disclose via `invisible` exactly as "
             "c5 does through a free function — the body shape must not change whether anything is said"),
    # SOUNDNESS R524 (re-scoped) + R556 — SHAPE (i): the consumer's OWN effectful implementor of a
    # FOREIGN abstraction, reached through a LOCAL BINDING rather than a signature parameter. ⟨0.35⟩
    # (SPEC.md:4655) already binds here — "where a synthesised or structural implementor is VISIBLE to the
    # engine's own resolution", with no local-abstraction restriction — so this is a PORT GAP, not a rung.
    # `disclosed` rather than `has`, because ⟨0.35⟩ licenses COMPLETING the dispatch or DISCLOSING it.
    #
    # THIS ARM EXISTS BECAUSE THE INSTRUMENT THAT COVERED IT COULD NOT FAIL: PART 4s's `fn_ok`
    # (run.sh:1394-1398) is true if ANY function carries `invisible` naming the dep OR ANY function
    # anywhere carries `Unknown` — so both spellings passed by construction.
    dict(id="c11_local_impl_via_binding", iface="impl", third=False, chained=False, entry="localbinding",
         want=dict(disclosed={EFFECT}),
         why="R524/R556: an implementor the consumer OWNS, reached through a let/local binding instead "
             "of a signature parameter, must not read pure — `dispatch` is the same shape one variable over"),
    dict(id="c5_unchained", iface="impl", third=True, chained=False, entry="dispatch",
         want=dict(hasnt={EFFECT}, unknown=False, invisible=True),
         why="REFERENCE: unchained, the same consumer discloses via `invisible` — chaining DELETES it"),
    dict(id="c6_middle_package", iface="impl", third=True, chained=True, entry="dispatch", middle=True,
         want=dict(has={EFFECT}),
         why="DEFECT: the DISPATCHER owns nothing — a MIDDLE package must name its dependency's member"),
]

# THE FOURTH PACKAGE, and why three cannot express what it does (SOUNDNESS R504).
#
# In c1–c5 the package that DISPATCHES is also the package that OWNS the abstraction, so an engine that
# scopes obligation 1 to abstractions it DECLARES answers correctly and the hole never opens. `middle`
# owns neither the trait nor any implementor of it: it depends on `iface` and dispatches over `iface`'s
# abstraction, which is the ordinary shape of a library layered on another library. If it names nothing,
# the consumer never learns the member to union on and the chain breaks ONE HOP SHORT — the app's row is
# ABSENT, which under ⟨0.21⟩ is a positive claim of purity.
#
# Found by candor-java's port reading candor-rust's source (`dispatch_sites` recorded local-trait dispatch
# only), measured silent on a four-package chain, and closed in java first — which is why this arm's XFAIL
# table is NOT uniform and why the `(arm, engine)` keying is load-bearing rather than defensive.
#
# c6 IS DELIBERATELY NOT IN `CROSS_ARMS`. Its consumer calls `middle` where c1's calls `iface`, so its
# source text CANNOT be byte-identical to the others' — the dispatcher has to live somewhere. The cross it
# supports is a different one, stated so it is not mistaken for the c1/c2/c3/c5 cross: c6 differs from c1
# in exactly ONE structural fact, which package holds the dispatching function. Every other input — the
# abstraction, its pure local implementor, the foreign effectful implementor, the chained report set — is
# rendered from the same sources. So an engine that passes c1 and fails c6 has told you precisely that its
# obligation-1 pass is scoped to abstractions it owns.

# An expectation keyed by (arm, engine) — NEVER by arm alone. Today it happens to be uniform, and it will
# not stay uniform: the moment one engine ports ⟨0.39⟩ its line comes out and the others' stay, which is
# precisely the state an arm-keyed table cannot represent. A PASSING xfail is a FAILURE (see main()).
XFAIL = {
    # ⟨0.40⟩ CANDIDATE, DECLARED 2026-09-22 — SOUNDNESS R533. Three engines read a consumer's own
    # zero-implementor foreign dispatch as SILENTLY PURE; ts discloses. These are NOT a port lag like the
    # lines below them: no engine has ever been asked for this, because no clause requires it yet. They
    # are here so the divergence is PINNED and retires loudly the moment an engine closes it, and so that
    # a ⟨0.40⟩ decision is made against a measured four-way row rather than against my summary of one.
    # c8 — the two engines that have NOT closed the body-local implementor, declared 2026-09-22 with the
    # arm. Unlike c9's lines these ARE port lags against text that already binds: ⟨0.35⟩ names "a lambda
    # or closure coerced to an interface" an implementor, and ⟨0.39⟩ obligation 2 requires a package
    # implementing a FOREIGN abstraction to publish an entry. Both rows are open and priced.
    #   java  — R530b, a returned LAMBDA: no class file, so `unionCandidates` ARM 2 never sees it.
    #   swift — R532, a conformance inside a func/init body: DeclCollector's four `.skipChildren` sites.
    # rust passes by DISCLOSING (R529's hedge) and ts by COMPLETING (R512) — which is why `want` is the
    # ⟨0.35⟩ disjunction and not `has`.
    # RETIRED 2026-09-22 — candor-java `d17dc66` (R530b) and candor-swift `5c53e96` (R532), both on the
    # same day the arm was written. Each was announced by its own line PASSING, which is the mechanism
    # working: java now COMPLETES (a lambda is an implementor via `samLambdaImpls`, kept out of
    # `chaTargets` because every emptiness test there reads empty as "disclose"), and swift COMPLETES too
    # (`finishBodyLocalTypes` mints the body-local conformer). So all four engines now answer c8: rust by
    # DISCLOSING, the other three by COMPLETING — which is exactly the shape `disclosed` was added to
    # express, and the reason the arm did not have to prefer one.

    # SOUNDNESS R548 — swift ALONE, and the tell is that it PASSES c5_unchained on the same dep with the
    # same abstraction. The only thing that changes between them is the CONSUMER BODY: c5 calls a free
    # function taking the abstraction, c10 dispatches directly on the value. java, rust and ts disclose
    # `invisible:['iface']` on both; swift discloses on c5 and its consumer row goes ABSENT on c10 — an
    # affirmative purity claim under SPEC §2 rule 3 over a call it cannot resolve. Not gate-affecting
    # (`invisible` arms no policy form — R133, CLOSED as a documentation gap on Tom's 2026-09-03 ruling),
    # which is exactly why it needs pinning rather than trusting: nothing else in the suite would notice.
    # SOUNDNESS R556 — rust ALONE, with java, swift AND ts all carrying the effect on the identical
    # fixture. `dyn_sig_trait_leaves` (lang.rs:83) iterates `sig.inputs` and nothing else — its own doc
    # says "a signature's PARAMETERS" — so the imported-trait local-impl arm (collector.rs:3676) never
    # fires for a `let`-position `dyn`. The control is `c5_unchained`/`dispatch`, where the SAME
    # implementor reached through a signature parameter resolves. Gate-visible: `deny Fs <fn>` and
    # `pure <fn>` both 1→0 on this shape, while the same run publishes the union entry carrying the effect.
    # RETIRED 2026-09-23, candor-rust `e82e00f` — R556 CLOSED, and the arm is what announced it. The fix
    # is a new ADDITIVE index (`dyn_local_traits`) written at one site and read by one predicate, not a
    # widening of `dyn_sig_traits`, which every other resolver sees. The diagnosis was confirmed by
    # BREAKING it rather than by reading the source: adding an entirely UNUSED `_x: &dyn Handlers`
    # parameter to the failing function flipped it `inferred:[]` → `['Fs']` with the body unchanged,
    # which names `dyn_sig_traits` and nothing else. Keep the arm: it is now a four-way regression pin,
    # and its `dispatch` control is what makes the one variable legible.

    ("c10_unchained_direct", "swift"): "R548",

    # SOUNDNESS R607 — c13's four-way answer, and rust is the only engine that does not COMPLETE.
    # java carries `['Net']` (which is R595's fix, confirmed four-way by this arm rather than by three
    # agent reports); swift and ts carry it AND hedge. rust reads `eff=∅ unknown=True`.
    #
    # NOTE WHAT THAT IS AND IS NOT. `unknown=True` means rust DISCLOSES — under ⟨0.35⟩'s disjunction
    # (complete the dispatch OR disclose it; only silence is forbidden) rust is CONFORMANT here, and
    # this is NOT the cardinal sin. What it fails is ⟨0.39⟩'s COMPLETENESS obligation: a chained
    # consumer's inherited signature must carry the effects of every implementor visible to it, and the
    # consumer supplied this one itself. A weaker finding than java's was, recorded at its real weight.
    ("c13_reassigned_field_hook", "rust"): "R607",

    # ⟨0.40⟩'s consumer-site pure-only union. I DECLARED THIS XFAIL FOUR-WAY AND WAS WRONG ON THREE
    # ENGINES — the arm's first run reported `XFAIL ARM PASSED` for java, rust and swift, which is the
    # ledger working exactly as R475 intended: an expectation that has become true is a FAILURE here.
    #
    # java and swift already read this correctly with `interfaceUnion=absent`, resolving the dep's one
    # pure implementor through the dependency's own row rather than through a union entry. rust passes
    # for a different reason and it is worth recording: its dep line reads `interfaceUnion=present`,
    # which is R609's producer half — shipped the same night — doing precisely what it was built for.
    #
    # ts is the one that over-discloses (`unknown=True` where the answer is knowable), so it keeps its
    # line under its own row rather than under the rung's.
    ("c12_consumer_pure_only_union", "ts"):    "R613",

    # RETIRED 2026-09-25, candor-rust `e4808bf` — the FIRST engine to close it. rust now reads
    # `['Unknown'], unresolved: true, unknownWhy: ['dispatch:Backend.size']` on this arm. Keep the
    # table rather than deleting it: java and swift are still open, and a PASSING xfail is what
    # announced this one, exactly as it announced each of ⟨0.39⟩'s four.
    # ("c9_consumer_zero_union", "rust"):  "R533",
    ("c9_consumer_zero_union", "java"):  "R533",
    ("c9_consumer_zero_union", "swift"): "R533",

    # RETIRED 2026-09-20, candor-ts `ee844f0` — the FOURTH and last engine. **⟨0.39⟩ IS NOW PORTED IN ALL
    # FOUR AND THIS TABLE IS EMPTY**, which is the state it was built to reach: every line was retired by
    # the engine that earned it, and a PASSING xfail failing is what announced each one. Keep the mechanism
    # rather than deleting it — the next cross-engine rung lands exactly the same way, and an arm-keyed
    # table could not have expressed any of the four intermediate states this one passed through.

    # RETIRED 2026-09-20, candor-swift `9ae9ea5`/`68f89a0` — the THIRD engine, and both of its lines came
    # out together because it ported the rung and R504's middle-package leg in one go. Its port recorded a
    # real DIFFERENCE rather than smoothing one over: swift cannot see that a call IS a dispatch. rust
    # reads `&dyn iface::Backend`, java reads INVOKEINTERFACE, ts reads the named import — Swift source
    # says only `b.size()` on a parameter typed `Backend`, and whether `Backend` is a protocol, a class or
    # a struct lives in a module the scan never opened. So obligation 1 over a foreign abstraction is
    # recorded at the engine's EXISTING imported-supertype CHA site under its existing conjuncts, not as a
    # second judgement about what a dispatch is.

    # RETIRED 2026-09-17, candor-rust `df4cf3f` — the FIRST engine to port ⟨0.39⟩, which is what this
    # table was built to notice. rust's three legs are live: the producer emits `dispatchesOn` on a row
    # that is otherwise PURE, a crate implementing a FOREIGN abstraction publishes its `interfaceUnion`
    # entry keyed under the OWNING crate, and the consumer unions per key. The other three engines' lines
    # stay exactly as they were — an arm-keyed table could not have expressed this state, which is the
    # reason this one is keyed by (arm, engine).
    #
    # RETIRED 2026-09-18, candor-java — the SECOND engine, and the family's reference one, so this port is
    # the shape ts and swift copy. Its legs are the same three and its arithmetic is simpler: a JVM entry
    # hash is already fully qualified in the owning package's namespace, so obligation 2's key needs no
    # prefixing rule at all (`iface/backend/Backend.size()I`) and the consumer resolves `dispatchesOn`
    # through the ordinary `crossDeps` index. Un-gating ⟨0.23⟩ was part of the port here too: this engine's
    # union entries rode behind CANDOR_WORKSPACE_CHAIN, and that gate is why the toggle survived default
    # scans. swift's and ts's lines are untouched.
    # c6 — THE MIDDLE PACKAGE (SOUNDNESS R504). java PASSES this arm: its port closed the hole in the same
    # commit that opened it, on the same four-package chain, keyed on INVOKEINTERFACE with a non-κ owner.
    # The other three lines are here for three different reasons, and the difference is the point of an
    # (arm, engine) table: ts and swift have not ported ⟨0.39⟩ at all, so c6 fails for the same reason c1
    # does; rust HAS ported it and still fails c6 alone, because its obligation-1 pass was scoped to
    # abstractions the producer DECLARES. A passing xfail is a FAILURE here — when rust closes it, this
    # line comes out in the same commit as the fix.
}

# The consumer's dispatching function, per engine. rust keeps its own casing convention; the assertion is
# on the LEAF name after `leaf_info` strips module separators.
# `nesteddispatch` names the SAME consumer function as `dispatch` — only its BODY differs (it dispatches
# on the abstraction itself rather than delegating to a dep function). Kept as a separate entry key so
# the arm table reads honestly; kept TOTAL across engines so a renderer cannot KeyError on an arm its
# engine declares inexpressible.
ENTRY = {
    "rust":  dict(pureonlydispatch="app_size", localbinding="app_size", dispatch="app_size", nesteddispatch="app_size", sealed="app_sealed", escapedispatch="app_size", reassignhook="app_run"),
    "java":  dict(pureonlydispatch="appSize", localbinding="appSize", dispatch="appSize", nesteddispatch="appSize", sealed="appSealed", escapedispatch="appSize", reassignhook="appRun"),
    "ts":    dict(pureonlydispatch="appSize", localbinding="appSize", dispatch="appSize", nesteddispatch="appSize", sealed="appSealed", escapedispatch="appSize", reassignhook="appRun"),
    "swift": dict(pureonlydispatch="appSize", localbinding="appSize", dispatch="appSize", nesteddispatch="appSize", sealed="appSealed", escapedispatch="appSize", reassignhook="appRun"),
}

# =====================================================================================================
# THE FIXTURE, four ways. Three packages:
#
#   iface     `trait/interface/protocol Backend { size() }` + `termSize(b)` which DISPATCHES over it.
#             variant "impl"   also declares ONE PURE implementor (ratatui-core's `TestBackend`)
#             variant "zero"   declares none
#             variant "sealed" a PRIVATE abstraction, one local EFFECTFUL implementor, dispatched from a
#                              public entry point — the exactness control, a different program on purpose
#   effimpl   implements iface's FOREIGN abstraction, effectfully (ratatui-crossterm's CrosstermBackend)
#   app       `appSize(b) { return iface.termSize(b) }` — the function under test, IDENTICAL in every arm
#             that uses it; `appRun()` supplies the foreign implementor, which is what makes the union
#             legitimate rather than a minted edge (⟨0.39⟩ REFUSES an escaping-value rule)
# =====================================================================================================
SINK = {  # one `Net` sink per language, the same vocabulary gen_differential.EFFECTS uses
    "rust":  'let _ = std::net::TcpStream::connect("h:1");',
    "java":  'try { new java.net.Socket("h", 1); } catch (Exception e) {}',
    "ts":    'try { netm.connect(1, "h") } catch {}',
    "swift": '_ = URLSession.shared.dataTask(with: URL(string: "http://h")!)',
}

RUST_IFACE = {
    # SOUNDNESS R595 / c13 — rust has no safe mutable static, so the analogous shape is a consumer-
    # SUPPLIED callable behind a global the library invokes. `OnceLock` is set-once rather than
    # reassignable — the closest safe spelling — with `noop` as the PURE DEFAULT. The question is
    # identical: the consumer supplies the implementor and the engine can see it.
    "hook": ('use std::sync::OnceLock;\n'
             'fn noop() {}\n'
             'pub static AFTER_STAGE: OnceLock<fn()> = OnceLock::new();\n'
             'pub fn run_stage() -> usize { (AFTER_STAGE.get().copied().unwrap_or(noop as fn()))(); 0 }\n'),
    "impl": ('pub trait Backend { fn size(&self) -> usize; }\n'
             'pub struct TestBackend;\n'
             'impl Backend for TestBackend { fn size(&self) -> usize { 7 } }\n'
             'pub fn term_size(b: &dyn Backend) -> usize { b.size() }\n'
             'pub fn conf_load() -> usize { %s 0 }\n' % CARRIER["rust"]),
    "zero": ('pub trait Backend { fn size(&self) -> usize; }\n'
             'pub fn term_size(b: &dyn Backend) -> usize { b.size() }\n'
             'pub fn conf_load() -> usize { %s 0 }\n' % CARRIER["rust"]),
    # ⟨0.39⟩/R518 — THE SPELLING ARM. Same abstraction, declared INSIDE A MODULE and re-exported at the
    # root, so `effimpl` and `app` are byte-identical to the `impl` variant and the ONLY variable is where
    # the abstraction is WRITTEN. That is R513's exact shape: candor-scan keyed its local union row on the
    # self type AS WRITTEN, so a module-qualified impl's real key never matched and NO union row was
    # published — a chained consumer read `[]` with no `invisible` and `deny Net` exited 0.
    "nested": ('pub mod backend {\n'
               '    pub trait Backend { fn size(&self) -> usize; }\n'
               '    pub struct NestedSink;\n'
               '    impl Backend for NestedSink { fn size(&self) -> usize { %s 0 } }\n'
               '}\n'
               'pub use backend::{Backend, NestedSink};\n'
               'pub fn term_size(b: &dyn Backend) -> usize { b.size() }\n' % SINK["rust"]),
    "sealed": ('trait Sealed { fn go(&self) -> usize; }\n'
               'struct LocalImpl;\n'
               'impl Sealed for LocalImpl { fn go(&self) -> usize { %s 0 } }\n'
               'pub fn sealed_dispatch() -> usize { let s: &dyn Sealed = &LocalImpl; s.go() }\n' % SINK["rust"]),
}
RUST_APP = {
    "reassignhook": ('fn sink() { %s }\n'
                     'pub fn app_run() -> usize { let _ = iface::AFTER_STAGE.set(sink); iface::run_stage() }\n'
                     % SINK["rust"]),
    # c11/R524+R556 — the CONTROL for this arm is `dispatch` above: the same implementor, the same
    # abstraction, reached through a SIGNATURE PARAMETER instead of a `let`. One variable.
    "localbinding": ('pub struct LocalB;\n'
                     'impl iface::Backend for LocalB { fn size(&self) -> usize { %s 0 } }\n'
                     'pub fn app_size() -> usize { let b: &dyn iface::Backend = &LocalB; b.size() }\n'
                     % SINK["rust"]),
    "dispatch": 'pub fn app_size(b: &dyn iface::Backend) -> usize { iface::term_size(b) }\n',
    # c12/R677 — `nesteddispatch` PLUS one call to the dep's carrier function. See the arm's note: the
    # call is what makes the row EXIST, so "reads the dep's one pure implementor" and "produced no row"
    # stop being the same bytes. It is a dep call rather than a contained sink on purpose — `c4_sealed`
    # already proves the ordinary chain join delivers a dep's effect four-way, so a green `Fs` here is
    # also evidence that this arm's CANDOR_DEPS reached the scan.
    "pureonlydispatch": ('pub fn app_size(b: &dyn iface::Backend) -> usize '
                         '{ let _ = iface::conf_load(); b.size() }\n'),
    "third":    'pub fn app_run() -> usize { app_size(&effimpl::Crossterm) }\n',
    "sealed":   'pub fn app_sealed() -> usize { iface::sealed_dispatch() }\n',
    # c6 — the ONLY line that differs from `dispatch`: the dispatching callee lives one package over.
    "middle":   'pub fn app_size(b: &dyn iface::Backend) -> usize { middle::mid_size(b) }\n',
    # c7/R518 — the consumer dispatches on the abstraction ITSELF rather than delegating to a dep
    # function. That distinction is load-bearing and cost me a vacuous arm: with `iface::term_size(b)`
    # the dep resolves its own dispatch by bounded CHA and the effect reaches the consumer through the
    # ORDINARY chain join, so the arm passed against a pre-R513 binary. Dispatching here makes the
    # union entry the only carrier, which is what R513 was about.
    "nesteddispatch": 'pub fn app_size(b: &dyn iface::Backend) -> usize { b.size() }\n',
    # c8/R529+R532 — the consumer SUPPLIES a body-local implementor. Two functions on purpose: the
    # supplier declares `L` inside its own body (so containment charges the SUPPLIER, correctly) and
    # hands it to the entry, which delegates to the dep exactly as `dispatch` does. No call edge runs
    # from the entry to the effect, so the ONLY route by which `app_size` can learn of `L` is the union —
    # which is the thing under test. Put the impl inside `app_size` itself and containment answers, and
    # the arm measures nothing.
    "escapedispatch": ('pub fn app_size(b: &dyn iface::Backend) -> usize { iface::term_size(b) }\n'
                       'pub fn app_supply() -> usize {\n'
                       '    struct L;\n'
                       '    impl iface::Backend for L { fn size(&self) -> usize { %s 0 } }\n'
                       '    app_size(&L)\n'
                       '}\n' % SINK["rust"]),
}
# THE MIDDLE PACKAGE, four ways. It depends on `iface` and dispatches over `iface`'s abstraction; it
# declares no abstraction and implements none.
RUST_MIDDLE = 'pub fn mid_size(b: &dyn iface::Backend) -> usize { b.size() }\n'

JAVA_IFACE = {
    # SOUNDNESS R595 / c13 — the exact shape the row was measured on: a PUBLIC STATIC NON-FINAL field
    # with a PURE default, invoked by a library entry.
    "hook": {
        "Hook.java": 'package iface; public interface Hook { void run(); }\n',
        "Hooks.java": ('package iface; public class Hooks {\n'
                       '  public static Hook afterStage = () -> { };\n'
                       '  public static int runStage() { afterStage.run(); return 0; }\n}\n'),
    },
    "impl": {
        "Backend.java": 'package iface; public interface Backend { int size(); }\n',
        "TestBackend.java": 'package iface; public class TestBackend implements Backend { public int size() { return 7; } }\n',
        "Terminal.java": 'package iface; public class Terminal { public static int termSize(Backend b) { return b.size(); } }\n',
        "Conf.java": 'package iface; public class Conf { public static int confLoad() { %s return 0; } }\n' % CARRIER["java"],
    },
    "zero": {
        "Backend.java": 'package iface; public interface Backend { int size(); }\n',
        "Terminal.java": 'package iface; public class Terminal { public static int termSize(Backend b) { return b.size(); } }\n',
        "Conf.java": 'package iface; public class Conf { public static int confLoad() { %s return 0; } }\n' % CARRIER["java"],
    },
    "sealed": {
        "Sealed.java": 'package iface; interface Sealed { int go(); }\n',
        "LocalImpl.java": 'package iface; class LocalImpl implements Sealed { public int go() { %s return 0; } }\n' % SINK["java"],
        "SealedDispatch.java": 'package iface; public class SealedDispatch { public static int sealedDispatch() { Sealed s = new LocalImpl(); return s.go(); } }\n',
    },
}
JAVA_APP = {
    "reassignhook": ('  public static int appRun() { iface.Hooks.afterStage = () -> { %s }; '
                     'return iface.Hooks.runStage(); }\n' % SINK["java"]),
    # c11 — java measured CLEAN on this shape, so this arm is a regression pin for it.
    "localbinding": ('  public static int appSize() { iface.Backend b = () -> { %s return 0; }; return b.size(); }\n'
                     % SINK["java"]),
    "dispatch": '  public static int appSize(iface.Backend b) { return iface.Terminal.termSize(b); }\n',
    # c12/R677 — see RUST_APP["pureonlydispatch"].
    "pureonlydispatch": ('  public static int appSize(iface.Backend b) '
                         '{ iface.Conf.confLoad(); return b.size(); }\n'),
    "third":    '  public static int appRun() { return appSize(new effimpl.Crossterm()); }\n',
    "sealed":   '  public static int appSealed() { return iface.SealedDispatch.sealedDispatch(); }\n',
    "middle":   '  public static int appSize(iface.Backend b) { return middle.Mid.midSize(b); }\n',
    # present only so the table is TOTAL — java declares c7 inexpressible (no re-export), so this is
    # never rendered. A missing key here is a KeyError in a renderer, not a skip.
    "nesteddispatch": '  public static int appSize(iface.Backend b) { return b.size(); }\n',
    # c8 — java's spelling of the same thing is a LAMBDA, which is the one implementor shape with no
    # class file and therefore no CHA entry (SOUNDNESS R530b). `Backend` is a SAM, so this compiles.
    "escapedispatch": ('  public static int appSize(iface.Backend b) { return iface.Terminal.termSize(b); }\n'
                       '  public static int appSupply() { iface.Backend b = () -> { %s return 0; }; return appSize(b); }\n'
                       % SINK["java"]),
}
JAVA_MIDDLE = {
    "Mid.java": 'package middle; public class Mid { public static int midSize(iface.Backend b) { return b.size(); } }\n',
}

TS_IFACE = {
    # SOUNDNESS R595 / c13 — an ES module BINDING is read-only to importers, so the idiomatic spelling
    # of "a mutable hook a consumer reassigns" is a property on an exported object. Same question.
    "hook": ('export type Hook = () => void\n'
             'export const hooks: { afterStage: Hook } = { afterStage: () => {} }\n'
             'export function runStage(): number { hooks.afterStage(); return 0 }\n'),
    "impl": ('import * as fsm from "node:fs";\n'
             'export interface Backend { size(): number }\n'
             'export class TestBackend implements Backend { size(): number { return 7 } }\n'
             'export function termSize(b: Backend): number { return b.size() }\n'
             'export function confLoad(): number { %s return 0 }\n' % CARRIER["ts"]),
    "zero": ('import * as fsm from "node:fs";\n'
             'export interface Backend { size(): number }\n'
             'export function termSize(b: Backend): number { return b.size() }\n'
             'export function confLoad(): number { %s return 0 }\n' % CARRIER["ts"]),
    # ⟨0.39⟩/R518 — the ts spelling arm: declared in a nested module, re-exported at the root, so the
    # consumer's import is unchanged and only the declaration site moves.
    "nested": ('export * from "./backend";\n'
               'import { Backend } from "./backend";\n'
               'export function termSize(b: Backend): number { return b.size() }\n'),
    "sealed": ('import * as netm from "node:net";\n'
               'interface Sealed { go(): number }\n'
               'class LocalImpl implements Sealed { go(): number { %s ; return 0 } }\n'
               'export function sealedDispatch(): number { const s: Sealed = new LocalImpl(); return s.go() }\n'
               % SINK["ts"]),
}
TS_APP = {
    "reassignhook": ('import * as netm from "node:net";\n'
                     'import { hooks, runStage } from "iface";\n'
                     'export function appRun(): number { hooks.afterStage = () => { %s }; return runStage() }\n'
                     % SINK["ts"]),
    # c11 — ts is clean on THIS spelling. Its own R524 defect needs an INDEX-SIGNATURE dep, a different
    # dep shape, so it is deliberately NOT approximated here.
    "localbinding": ('import * as netm from "node:net";\n'
                     'import { Backend } from "iface";\n'
                     'export function appSize(): number { const b: Backend = { size() { %s return 0 } }; return b.size() }\n'
                     % SINK["ts"]),
    "dispatch": ('import { Backend, termSize } from "iface";\n'
                 'export function appSize(b: Backend): number { return termSize(b) }\n'),
    # c12/R677 — see RUST_APP["pureonlydispatch"].
    "pureonlydispatch": ('import { Backend, confLoad } from "iface";\n'
                         'export function appSize(b: Backend): number { confLoad(); return b.size() }\n'),
    "third":    ('import { Crossterm } from "effimpl";\n'
                 'export function appRun(): number { return appSize(new Crossterm()) }\n'),
    "sealed":   ('import { sealedDispatch } from "iface";\n'
                 'export function appSealed(): number { return sealedDispatch() }\n'),
    "middle":   ('import { Backend } from "iface";\n'
                 'import { midSize } from "middle";\n'
                 'export function appSize(b: Backend): number { return midSize(b) }\n'),
    "nesteddispatch": ('import { Backend } from "iface";\n'
                       'export function appSize(b: Backend): number { return b.size() }\n'),
    # c8 — ts's spelling is a STRUCTURAL literal, which is R512's shape. This arm is a REGRESSION PIN
    # for that fix rather than a new question, and it is expected GREEN.
    "escapedispatch": ('import * as netm from "node:net";\n'
                       'import { Backend, termSize } from "iface";\n'
                       'export function appSize(b: Backend): number { return termSize(b) }\n'
                       'export function appSupply(): number {\n'
                       '  const l: Backend = { size() { %s return 0 } };\n'
                       '  return appSize(l)\n'
                       '}\n' % SINK["ts"]),
}
TS_MIDDLE = ('import { Backend } from "iface";\n'
             'export function midSize(b: Backend): number { return b.size() }\n')

SW_IFACE = {
    # SOUNDNESS R595 / c13 — swift spells it `public static var` on a public enum.
    "hook": ('public enum Hooks {\n'
             '  public static var afterStage: () -> Void = { }\n'
             '  public static func runStage() -> Int { afterStage(); return 0 }\n}\n'),
    "impl": ('import Foundation\n'
             'public protocol Backend { func size() -> Int }\n'
             'public struct TestBackend: Backend { public init() {}; public func size() -> Int { return 7 } }\n'
             'public func termSize(_ b: Backend) -> Int { return b.size() }\n'
             'public func confLoad() -> Int { %s; return 0 }\n' % CARRIER["swift"]),
    "zero": ('import Foundation\n'
             'public protocol Backend { func size() -> Int }\n'
             'public func termSize(_ b: Backend) -> Int { return b.size() }\n'
             'public func confLoad() -> Int { %s; return 0 }\n' % CARRIER["swift"]),
    "sealed": ('import Foundation\n'
               'protocol Sealed { func go() -> Int }\n'
               'struct LocalImpl: Sealed { func go() -> Int { %s; return 0 } }\n'
               'public func sealedDispatch() -> Int { let s: Sealed = LocalImpl(); return s.go() }\n'
               % SINK["swift"]),
}
SW_APP = {
    "reassignhook": ('import Iface\nimport Foundation\n'
                     'public func appRun() -> Int { Hooks.afterStage = { %s }; return Hooks.runStage() }\n'
                     % SINK["swift"]),
    # c11 — swift measured clean on this shape; a regression pin.
    "localbinding": ('import Iface\nimport Foundation\n'
                     'public struct LocalB: Backend { public init() {}\n'
                     '    public func size() -> Int { %s; return 0 } }\n'
                     'public func appSize() -> Int { let b: Backend = LocalB(); return b.size() }\n'
                     % SINK["swift"]),
    "dispatch": 'import Iface\npublic func appSize(_ b: Backend) -> Int { return termSize(b) }\n',
    # c12/R677 — see RUST_APP["pureonlydispatch"].
    "pureonlydispatch": ('import Iface\n'
                         'public func appSize(_ b: Backend) -> Int { _ = confLoad(); return b.size() }\n'),
    "third":    'import EffImpl\npublic func appRun() -> Int { return appSize(Crossterm()) }\n',
    "sealed":   'import Iface\npublic func appSealed() -> Int { return sealedDispatch() }\n',
    "middle":   'import Iface\nimport Middle\npublic func appSize(_ b: Backend) -> Int { return midSize(b) }\n',
    # as above: swift declares c7 inexpressible (no submodules), so this is never rendered.
    "nesteddispatch": 'import Iface\npublic func appSize(_ b: Backend) -> Int { return b.size() }\n',
    # c8 — swift's spelling is a conformance declared INSIDE a function body, which DeclCollector's
    # `.skipChildren` sites never reach (SOUNDNESS R532). Same two-function shape as the other three.
    "escapedispatch": ('import Iface\nimport Foundation\n'
                       'public func appSize(_ b: Backend) -> Int { return termSize(b) }\n'
                       'public func appSupply() -> Int {\n'
                       '    struct L: Backend { func size() -> Int { %s; return 0 } }\n'
                       '    return appSize(L())\n'
                       '}\n' % SINK["swift"]),
}
SW_MIDDLE = ('import Iface\n'
             'public func midSize(_ b: Backend) -> Int { return b.size() }\n')


def _w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def iface_variant(arm):
    """THE FAULT IS AT THE FIXTURE, NOT THE COMPARISON. With CANDOR_PROBE_FAULT set, c2_zero_impl's
    dependency is rendered with the "impl" variant — the one PURE implementor — so the arm that MUST
    remain a disclosed `Unknown` cannot be, and the run MUST go red.

    Chosen over inverting an expected value for the reason probe_check.py records at length: inverting
    proves only that the comparison can subtract, while corrupting the INPUT proves the cell is reading
    the fixture it names — and here it proves specifically that the CHAINED DEPENDENCY's content reached
    the consumer's scan, which is the one thing this part measures that no single-package part does.
    Chosen over swapping two must-fail arms because there are none to swap: c1 is xfailed on every
    engine, so a substitution into c1 would move no verdict (the vacuity recorded for gen_binding_union).
    """
    if FAULT and arm["id"] == "c2_zero_impl":
        return "impl"
    return arm["iface"]


# =====================================================================================================
# RENDERING. One workspace per (engine, arm): ws/<engine>/<arm>/{iface,effimpl,app}. Every arm gets its
# OWN copy of every package, so no arm can read another's `.candor` and no dependency scan can be
# attributed to the wrong arm — the same structural isolation split_arms.py enforces for P1/P2/P3.
# Returns the ordered list of (package_dir, is_dep) for the arm.
# =====================================================================================================
def app_body(arm):
    """Which consumer body this arm's app carries. `middle` is the c6 variant — the SAME function, the
    same signature, one call target over."""
    if arm["entry"] == "sealed":
        return "sealed"
    if arm["entry"] == "nesteddispatch":
        # R518: c7's consumer dispatches on the abstraction ITSELF. This branch is load-bearing — without
        # it this function returned "dispatch" for c7, the consumer delegated to `iface::term_size`, the
        # dep resolved its own dispatch by bounded CHA, and the effect reached the consumer through the
        # ORDINARY chain join. The arm then passed against a PRE-R513 binary, i.e. it was vacuous.
        return "nesteddispatch"
    if arm["entry"] == "localbinding":
        # c11/R524+R556. The consumer declares its OWN effectful implementor of the FOREIGN abstraction
        # and dispatches through a LOCAL BINDING typed as that abstraction, NOT through a signature
        # parameter. That distinction is the whole arm: rust's `dyn_sig_trait_leaves` reads `sig.inputs`
        # and nothing else, so the imported-trait local-impl route never fires for this spelling — while
        # the signature spelling, which `dispatch` already covers, resolves correctly. Same trap as c7 and
        # c8: without this branch `app_body` falls through to "dispatch" and the arm measures the control.
        return "localbinding"
    if arm["entry"] == "reassignhook":
        # c13 / SOUNDNESS R595. Same trap as c7, c8 and c11 above and the file says so three times: a
        # missing branch here silently renders the "dispatch" body instead, and the arm then measures
        # the control on every engine while looking like a four-way finding.
        return "reassignhook"
    if arm["entry"] == "pureonlydispatch":
        # c12/R677. THE SAME TRAP AS c7, c8, c11 AND c13 ABOVE, and the file now says so five times: a
        # missing branch here renders the "dispatch" body instead, the consumer never dispatches on the
        # abstraction at all, and the arm measures c3 while looking like a ⟨0.40⟩ finding.
        return "pureonlydispatch"
    if arm["entry"] == "escapedispatch":
        # c8. THE SAME TRAP AS c7 ABOVE, AND I WALKED INTO IT ADDING THIS ARM. Without this branch the
        # function returns "dispatch", the renderer writes ONLY `app_size`, the consumer never supplies a
        # body-local implementor at all — and the arm failed on all FOUR engines, which looked like a
        # four-way finding and was a missing two lines. `app_body` is TOTAL over `entry` by construction
        # or it is silently wrong; a fall-through default is what makes that possible.
        return "escapedispatch"
    return "middle" if arm.get("middle") else "dispatch"


def dep_order(root, arm):
    """The dependency package directories, in scan order. `middle` sits between the abstraction's owner
    and its foreign implementor because that is where it sits in the dependency graph."""
    order = [os.path.join(root, "iface")]
    if arm.get("middle"):
        order.append(os.path.join(root, "middle"))
    if arm["third"]:
        order.append(os.path.join(root, "effimpl"))
    return order


def render_rust(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "Cargo.toml"), '[package]\nname="iface"\nversion="0.0.0"\nedition="2021"\n')
    _w(os.path.join(root, "iface", "src", "lib.rs"), RUST_IFACE[var])
    deps = ['iface={path="../iface"}']
    if mid:
        _w(os.path.join(root, "middle", "Cargo.toml"),
           '[package]\nname="middle"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\niface={path="../iface"}\n')
        _w(os.path.join(root, "middle", "src", "lib.rs"), RUST_MIDDLE)
        deps.append('middle={path="../middle"}')
    if third:
        _w(os.path.join(root, "effimpl", "Cargo.toml"),
           '[package]\nname="effimpl"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\niface={path="../iface"}\n')
        _w(os.path.join(root, "effimpl", "src", "lib.rs"),
           'pub struct Crossterm;\nimpl iface::Backend for Crossterm { fn size(&self) -> usize { %s 0 } }\n'
           % SINK["rust"])
        deps.append('effimpl={path="../effimpl"}')
    body = RUST_APP[app_body(arm)]
    if third:
        body += RUST_APP["third"]
    _w(os.path.join(root, "app", "Cargo.toml"),
       '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\n' + "\n".join(deps) + "\n")
    _w(os.path.join(root, "app", "src", "lib.rs"), body)
    return dep_order(root, arm), os.path.join(root, "app")


def render_java(root, arm):
    """java scans BYTECODE, so the packages are class directories and javac is mandatory rather than a
    compile proof bolted on — the fixture cannot even be presented to the engine unbuilt."""
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    src = os.path.join(root, "src")
    for name, text in JAVA_IFACE[var].items():
        _w(os.path.join(src, "iface", name), text)
    if mid:
        for name, text in JAVA_MIDDLE.items():
            _w(os.path.join(src, "middle", name), text)
    if third:
        _w(os.path.join(src, "effimpl", "Crossterm.java"),
           'package effimpl; public class Crossterm implements iface.Backend { public int size() { %s return 0; } }\n'
           % SINK["java"])
    body = JAVA_APP[app_body(arm)]
    if third:
        body += JAVA_APP["third"]
    _w(os.path.join(src, "app", "App.java"), "package app;\npublic class App {\n" + body + "}\n")
    return src, [p for p, on in (("iface", True), ("middle", mid), ("effimpl", third)) if on]


def render_ts(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "package.json"), '{"name":"iface","version":"0.0.0","main":"src/index.ts"}\n')
    _w(os.path.join(root, "iface", "src", "index.ts"), TS_IFACE[var])
    if var == "nested":
        # R518: the abstraction's own file, one level down. The root index re-exports it, so the
        # consumer's `import { Backend } from "iface"` is unchanged and the spelling is the only variable.
        _w(os.path.join(root, "iface", "src", "backend.ts"),
           'import * as netm from "node:net";\n'
           'export interface Backend { size(): number }\n'
           'export class NestedSink implements Backend { size(): number { %s ; return 0 } }\n'
           % SINK["ts"])
    if mid:
        _w(os.path.join(root, "middle", "package.json"),
           '{"name":"middle","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "middle", "src", "index.ts"), TS_MIDDLE)
        _link(os.path.join(root, "middle", "node_modules", "iface"), os.path.join(root, "iface"))
    if third:
        _w(os.path.join(root, "effimpl", "package.json"),
           '{"name":"effimpl","version":"0.0.0","main":"src/index.ts"}\n')
        _w(os.path.join(root, "effimpl", "src", "index.ts"),
           'import * as netm from "node:net";\nimport { Backend } from "iface";\n'
           'export class Crossterm implements Backend { size(): number { %s ; return 0 } }\n' % SINK["ts"])
        _link(os.path.join(root, "effimpl", "node_modules", "iface"), os.path.join(root, "iface"))
    body = TS_APP[app_body(arm)]
    if third:
        body += TS_APP["third"]
    dep_decl = ('{"iface":"file:../iface"'
                + (',"middle":"file:../middle"' if mid else "")
                + (',"effimpl":"file:../effimpl"' if third else "") + "}")
    _w(os.path.join(root, "app", "package.json"),
       '{"name":"app","version":"0.0.0","dependencies":%s}\n' % dep_decl)
    _w(os.path.join(root, "app", "src", "index.ts"), body)
    _link(os.path.join(root, "app", "node_modules", "iface"), os.path.join(root, "iface"))
    if mid:
        _link(os.path.join(root, "app", "node_modules", "middle"), os.path.join(root, "middle"))
    if third:
        _link(os.path.join(root, "app", "node_modules", "effimpl"), os.path.join(root, "effimpl"))
    # `@types/node` is borrowed from the engine's own tree into EVERY package, not just the consumer:
    # tsc resolves the `node:net` sink's types relative to the file that imports it, so a link only on
    # `app` leaves the dependency unchecked and the typecheck fails there instead.
    types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
    if os.path.isdir(types):
        for pkg in ["iface", "app"] + (["middle"] if mid else []) + (["effimpl"] if third else []):
            _link(os.path.join(root, pkg, "node_modules", "@types"), types)
    return dep_order(root, arm), os.path.join(root, "app")


def _link(link, target):
    os.makedirs(os.path.dirname(link), exist_ok=True)
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)


SW_MANIFEST = ('// swift-tools-version:5.9\nimport PackageDescription\n'
               'let package = Package(name: "%(mod)s", products: [.library(name: "%(mod)s", targets: ["%(mod)s"])], '
               'dependencies: [%(deps)s], targets: [.target(name: "%(mod)s", dependencies: [%(prods)s])])\n')


def render_swift(root, arm):
    var, third, mid = iface_variant(arm), arm["third"], arm.get("middle")
    _w(os.path.join(root, "iface", "Package.swift"), SW_MANIFEST % dict(mod="Iface", deps="", prods=""))
    _w(os.path.join(root, "iface", "Sources", "Iface", "iface.swift"), SW_IFACE[var])
    deps, prods = ['.package(path: "../iface")'], ['.product(name: "Iface", package: "iface")']
    if mid:
        _w(os.path.join(root, "middle", "Package.swift"),
           SW_MANIFEST % dict(mod="Middle", deps='.package(path: "../iface")',
                              prods='.product(name: "Iface", package: "iface")'))
        _w(os.path.join(root, "middle", "Sources", "Middle", "mid.swift"), SW_MIDDLE)
        deps.append('.package(path: "../middle")')
        prods.append('.product(name: "Middle", package: "middle")')
    if third:
        _w(os.path.join(root, "effimpl", "Package.swift"),
           SW_MANIFEST % dict(mod="EffImpl", deps='.package(path: "../iface")',
                              prods='.product(name: "Iface", package: "iface")'))
        _w(os.path.join(root, "effimpl", "Sources", "EffImpl", "eff.swift"),
           'import Foundation\nimport Iface\n'
           'public struct Crossterm: Backend { public init() {}; public func size() -> Int { %s; return 0 } }\n'
           % SINK["swift"])
        deps.append('.package(path: "../effimpl")')
        prods.append('.product(name: "EffImpl", package: "effimpl")')
    body = SW_APP[app_body(arm)]
    if third:
        body += SW_APP["third"]
    _w(os.path.join(root, "app", "Package.swift"),
       SW_MANIFEST % dict(mod="App", deps=", ".join(deps), prods=", ".join(prods)))
    _w(os.path.join(root, "app", "Sources", "App", "app.swift"), body)
    return dep_order(root, arm), os.path.join(root, "app")


# =====================================================================================================
# THE CROSS, ASSERTED RATHER THAN CLAIMED. If the consumer's source text ever stops being identical
# across the toggle's arms, every comparison below becomes fixture-induced and means nothing. This is the
# failure mode that produced three corrections to R475's original filing, so it is a hard check and not a
# comment.
# =====================================================================================================
CROSS_ARMS = ("c1_foreign_effectful", "c2_zero_impl", "c3_pure_only", "c5_unchained")


def _assert_identical_consumers(texts):
    """texts: {arm_id: consumer source text}. The c1/c5 consumers carry an EXTRA function (`appRun`,
    which supplies the foreign implementor); the function under test must be a verbatim prefix-line
    match, so compare the `dispatch` block alone."""
    ref = None
    for aid in CROSS_ARMS:
        t = texts.get(aid)
        if t is None:
            continue
        if ref is None:
            ref = (aid, t)
        elif t != ref[1]:
            return ("the consumer's dispatching source differs between %s and %s — the cross is "
                    "FIXTURE-INDUCED and no comparison below is evidence" % (ref[0], aid))
    return None


def build_proof(kind, path, extra=None):
    """Compile the rendered fixture. An absence-asserting control over an unbuildable program is NOT
    weak evidence, it is none: no correct engine could pass it differently and no broken one would be
    caught. Returns an error string, or None."""
    if NOBUILD:
        return None
    if kind == "rust":
        r = gd.run(["cargo", "build", "--offline", "-q"], cwd=path)
    elif kind == "swift":
        r = gd.run(["swift", "build"], cwd=path)
    elif kind == "ts":
        tsc = os.path.join(gd.CANDOR_TS, "node_modules", "typescript", "bin", "tsc")
        types = os.path.join(gd.CANDOR_TS, "node_modules", "@types")
        if not os.path.exists(tsc) or not os.path.isdir(types):
            return "SKIPPED: no tsc / @types under CANDOR_TS/node_modules — the ts fixture is UNTYPECHECKED"
        # `--types node` explicitly: with nodenext the automatic @types sweep does not reach the linked
        # directory from an IMPORTED package's file, so the dependency's `node:net` sink fails to
        # typecheck while the consumer's passes — a compile proof that covers only half the fixture.
        r = gd.run(["node", tsc, "--noEmit", "--module", "nodenext", "--moduleResolution", "nodenext",
                    "--target", "es2022", "--types", "node",
                    os.path.join("src", "index.ts")] + (extra or []), cwd=path)
    else:
        return None
    if r.returncode != 0:
        return "%s build FAILED: %s" % (kind, (r.stderr or r.stdout).decode()[:300].replace("\n", " | "))
    return None


def producer_note(path):
    """Diagnostics for ⟨0.39⟩ obligations 1 and 2 — printed, never asserted (see the header)."""
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception:
        return "unreadable"
    fns = d["functions"] if isinstance(d, dict) else d
    disp = sum(1 for e in fns if e.get("dispatchesOn"))
    # SPEC §2 (:441, :3565) defines `interfaceUnion` as a PER-ENTRY field — the union is a synthetic
    # entry APPENDED TO `functions`, not a top-level key. Reading it at the top level made this
    # diagnostic print `absent` even for a conforming producer, which is how it read for rust right up
    # until the rung shipped. Diagnostic-only, but a wrong diagnostic misleads the NEXT engine, which
    # is the whole audience of this part.
    iu = any(f.get("interfaceUnion") for f in fns) if isinstance(d, dict) else None
    return "rows=%d dispatchesOn=%d interfaceUnion=%s" % (len(fns), disp, "present" if iu else "absent")


def facts(leaves, entry):
    """The consumer's row as a triple, with ABSENCE made explicit. `leaf_info` omits pure functions
    because the engines do — so a missing key is a POSITIVE purity claim, not a missing measurement, and
    conflating the two is the shape of the sin itself.

    THAT DOCSTRING WAS TRUE AND `judge()` DID NOT READ THE FLAG (SOUNDNESS R636/R677). The `absent` key
    was set correctly from the day it was written and consumed only by `show()`; the comparison it exists
    for was never made. A field that records the right thing with no assertion that reads it is the same
    vacuity as no field at all."""
    if leaves is None:
        return None
    e = leaves.get(entry)
    if e is None:
        return dict(eff=frozenset(), unknown=False, invisible=frozenset(), absent=True)
    return dict(eff=e["eff"], unknown=e["unknown"], invisible=e["invisible"], absent=False)


def judge(want, f):
    bad = []
    # SOUNDNESS R677 — AN ABSENT ROW USED TO PASS, AND `facts()`' OWN DOCSTRING SAYS WHY IT MUST NOT.
    # A missing consumer entry is rendered `eff=∅, unknown=False, invisible=∅`, so EVERY `hasnt`,
    # `unknown=False` and `invisible=False` in the table above is satisfied by a report that never
    # mentioned the function at all. Driven against that value, 11 of the 13 arms went red on their
    # other assertions and `c3_pure_only` and `c12_consumer_pure_only_union` PASSED — attack B, an
    # unconditional pass, in the arm written to close the gap c3 left open.
    #
    # SPEC §4 ⟨0.35⟩ states the rule this enforces verbatim (SPEC.md:4680): *any row asserting this
    # clause MUST treat a missing entry as a FAILURE, never as a skip … a checker that looks the caller
    # up and skips-if-absent is green on a broken engine forever.*
    #
    # THE LICENCE IS NAMED, NEVER IMPLICIT, and `_assert_arm_table()` refuses one that contradicts its
    # own arm. Exactly one arm carries it today — `c3_pure_only`, where an omitted pure row is what a
    # conforming engine produces — and the reason is PRINTED in that cell, so a reader can see which
    # greens silence can buy instead of deriving it from `want`.
    if f["absent"]:
        if not want.get("absent_ok"):
            return ["ABSENT — no row for this function at all. Under SPEC §2 rule 3 that is a POSITIVE "
                    "purity claim, not a missing measurement, and it is the sin's own signature"]
        return []
    # `disclosed=E` is ⟨0.35⟩'s DISJUNCTION, not a third way of spelling `has`. The contract says an
    # engine must either COMPLETE the dispatch (the effect arrives) or DISCLOSE it (a hedged Unknown) —
    # never silently pure — and it explicitly licenses both. An arm that demanded `has={E}` would fail an
    # engine taking the licensed hedge (rust after R529) and so would measure the ARM's preference rather
    # than the contract; one that demanded `unknown=True` would fail an engine that did the better thing.
    # Added 2026-09-22 with c8, where two engines complete, one hedges, and one is silent.
    for x in sorted(want.get("disclosed", ())):
        if x not in f["eff"] and not f["unknown"]:
            bad.append("SILENT on %s — neither the effect nor a disclosed Unknown" % x)
    for x in sorted(want.get("has", ())):
        if x not in f["eff"]:
            bad.append("missing %s" % x)
    for x in sorted(want.get("hasnt", ())):
        if x in f["eff"]:
            bad.append("FABRICATED %s" % x)
    if want.get("unknown") is not None and f["unknown"] != want["unknown"]:
        bad.append("unknown=%s want %s" % (f["unknown"], want["unknown"]))
    if want.get("invisible") is not None and bool(f["invisible"]) != want["invisible"]:
        bad.append("invisible=%s want %s" % (sorted(f["invisible"]) or "∅", want["invisible"]))
    return bad


def show(f, want=None):
    if f["absent"]:
        lic = (want or {}).get("absent_ok")
        # A cell that says nothing reads like a pass — the same reason a declared SKIP is printed.
        return "ABSENT (a purity claim)" + (" — LICENSED: %s" % lic if lic else "")
    return "eff=%s unknown=%s invisible=%s" % (sorted(f["eff"]) or "∅", f["unknown"],
                                               sorted(f["invisible"]) or "∅")




# =====================================================================================================
# THE TWO TABLE GUARDS, and why they are executable rather than review notes. SOUNDNESS R636/R677/R678:
# this part shipped two arms whose `want` could be satisfied by an engine that said NOTHING, and one of
# them was added BECAUSE the other did not pin. Neither was caught by reading; both are caught by
# driving `judge()` against the values `facts()` can actually produce. `--selftest` runs them with no
# engine, no build and no network, and `scripts/doc-gates.sh` runs `--selftest`.
# =====================================================================================================
SINKS_BY_EFFECT = {EFFECT: SINK, CARRIER_EFFECT: CARRIER}


def assert_arm_table(arms=None):
    """`absent_ok` may not contradict its own arm. An arm that demands an effect, a disclosure or a
    non-empty kappa ledger CANNOT be satisfied by an omitted row, so declaring the licence there is
    either a copy-paste or a misunderstanding — and it would silently convert a real assertion into a
    pass. Returns a list of complaints."""
    bad = []
    for arm in (arms if arms is not None else ARMS):
        w = arm["want"]
        if not w.get("absent_ok"):
            continue
        for key in ("has", "disclosed"):
            if w.get(key):
                bad.append("%s: absent_ok with `%s` — an omitted row can never carry %s"
                           % (arm["id"], key, sorted(w[key])))
        if w.get("unknown") is True:
            bad.append("%s: absent_ok with `unknown=True` — an omitted row discloses nothing" % arm["id"])
        if w.get("invisible") is True:
            bad.append("%s: absent_ok with `invisible=True` — an omitted row has no kappa ledger"
                       % arm["id"])
    return bad


def assert_hasnt_is_reachable(arms=None):
    """A `hasnt` names an effect the consumer MUST NOT carry. If no sink for any of those effects exists
    anywhere in the arm's rendered fixture, no engine can fail it and the assertion is decoration.

    MEASURED 2026-09-25 by rendering all 13 arms four ways and counting each language's own sink:
    `c2`, `c3`, `c9` and `c12` contained ZERO `Net` — no third package, and neither the `impl` nor the
    `zero` dependency had a sink. R636 recorded that vacuity for `c12`; it was four arms, which is why
    this is a gate and not a fix to one line. Renders only — nothing is built and no engine is invoked.
    """
    import tempfile
    bad = []
    ws = tempfile.mkdtemp(prefix="candor-part92-armcheck-")
    renderers = dict(rust=render_rust, java=render_java, ts=render_ts, swift=render_swift)
    for arm in (arms if arms is not None else ARMS):
        hasnt = sorted(arm["want"].get("hasnt", ()))
        if not hasnt:
            continue
        for eng, render in sorted(renderers.items()):
            if eng in (arm.get("skip") or ()):
                continue
            root = os.path.join(ws, eng, arm["id"])
            os.makedirs(root, exist_ok=True)
            render(root, arm)
            seen = set()
            for d, _dd, fs in os.walk(root):
                if "node_modules" in d:
                    continue
                for fn in fs:
                    p = os.path.join(d, fn)
                    if os.path.islink(p):
                        continue
                    try:
                        text = open(p).read()
                    except Exception:
                        continue
                    for eff in hasnt:
                        if SINKS_BY_EFFECT.get(eff, {}).get(eng, "\0") in text:
                            seen.add(eff)
            if not seen:
                bad.append("%s/%s: hasnt=%s is VACUOUS — no sink for any of those effects is rendered "
                           "anywhere in the fixture, so the assertion cannot fail" % (arm["id"], eng, hasnt))
    shutil.rmtree(ws, ignore_errors=True)
    return bad


ABSENT_ROW = dict(eff=frozenset(), unknown=False, invisible=frozenset(), absent=True)


def absent_passers(arms):
    """Which arms would a report that never mentions the consumer satisfy? SOUNDNESS R636 drove this by
    hand and found two; the answer must stay the declared set."""
    return {a["id"] for a in arms if not judge(a["want"], ABSENT_ROW)}


def selftest():
    """CALIBRATED, not asserted: every check below is first shown FAILING on an injected defect, then
    passing on the real table. A gate that has never gone red has not been shown to be a gate."""
    fails = []

    ran = []

    def check(label, got, want):
        ran.append(label)
        status = "OK  " if got == want else "FAIL"
        if got != want:
            fails.append("%s: got %r want %r" % (label, got, want))
        print("  %s %s" % (status, label))

    # 1. THE DEFECT ITSELF, pinned independently of the arm table so a future edit cannot retire it by
    #    accident: the exact `want` shape R636 found — hasnt + unknown=False + invisible=False — is what
    #    an absent row satisfies, and it must now be rejected.
    r636_shape = dict(hasnt={EFFECT}, unknown=False, invisible=False)
    check("R636 shape is REJECTED when absent", bool(judge(r636_shape, ABSENT_ROW)), True)
    check("R636 shape PASSES when the row exists and is pure",
          judge(r636_shape, dict(eff=frozenset(), unknown=False, invisible=frozenset(), absent=False)), [])
    check("a NAMED licence still passes",
          judge(dict(r636_shape, absent_ok="a reason"), ABSENT_ROW), [])

    # 2. EVERY ARM, against the value `facts()` produces for a missing entry. The licensed set is
    #    declared here as a literal rather than derived from ARMS: a count compared against itself is
    #    the two-sided drift that makes a ratchet vacuous (the COVERED_FLOOR convention in probe_check).
    #    NOTE WHAT THIS CHECK CAN AND CANNOT SEE. It is a RATCHET on the licensed set, not a second
    #    detector for R677 — once no arm's `want` is the R636 shape any more, removing the absence
    #    branch from `judge()` leaves this set unchanged (verified by injection). Check 1 is the one
    #    that fails on that; this one fails when an arm quietly GAINS a licence, which is calibrated
    #    below on a poisoned table rather than assumed.
    licensed = {"c3_pure_only"}
    check("exactly the declared arms pass on an absent row", absent_passers(ARMS), licensed)
    check("and every other arm goes red", len(ARMS) - len(absent_passers(ARMS)), 12)
    poison = ARMS + [dict(id="poison", want=dict(hasnt={EFFECT}, absent_ok="smuggled in"))]
    check("the licensed-set ratchet CATCHES an arm that gains a licence",
          absent_passers(poison) - licensed, {"poison"})

    # 3. `absent_ok` may not contradict its own arm — calibrated on an injected one.
    poison = [dict(id="poison", want=dict(has={EFFECT}, absent_ok="wrong"))]
    check("arm-table guard CATCHES a contradictory licence", len(assert_arm_table(poison)), 1)
    check("arm-table guard is clean on the real table", assert_arm_table(), [])

    # 4. `hasnt` reachability — calibrated on an arm naming an effect no fixture contains.
    poison = [dict(ARMS[2], id="poison", want=dict(hasnt={"Exec"}))]
    check("hasnt guard CATCHES an unreachable effect", len(assert_hasnt_is_reachable(poison)) > 0, True)
    check("hasnt guard is clean on the real table", assert_hasnt_is_reachable(), [])

    # 5. `app_body` must be TOTAL over `entry` — the trap this file records five times. A `pureonlydispatch`
    #    arm that fell through to "dispatch" would silently re-measure c3.
    bodies = {a["id"]: app_body(a) for a in ARMS}
    check("c12 renders its OWN body", bodies["c12_consumer_pure_only_union"], "pureonlydispatch")
    check("every entry has a renderer four ways",
          sorted({b for b in bodies.values()} - set(RUST_APP) - {"middle"}), [])
    check("every arm's entry is in every engine's ENTRY map",
          sorted({a["entry"] for a in ARMS} - set.intersection(*[set(v) for v in ENTRY.values()])), [])

    if fails:
        print("\nPART 92 SELFTEST: %d FAILED" % len(fails))
        for f in fails:
            print("  " + f)
        return 1
    print("\nPART 92 SELFTEST: OK — %d checks, no engine invoked" % len(ran))
    return 0


def run_engine(name, ws):
    """Returns ({arm_id: facts-or-None}, notes, err)."""
    scanner = sa.SCANNERS[name]()
    if not scanner.available:
        return None, None, scanner.err
    out, notes, texts = {}, [], {}
    for arm in ARMS:
        # R518: an arm may declare itself INEXPRESSIBLE for an engine, with the reason in its comment.
        # Declared, never silently skipped — PART 91 set this precedent when ts had no receiver form for
        # a spawn, and the difference matters: a skipped cell that prints nothing reads like a pass.
        if name in (arm.get("skip") or ()):
            out[arm["id"]] = "SKIP"
            continue
        root = os.path.join(ws, name, arm["id"])
        os.makedirs(root, exist_ok=True)
        if name == "java":
            src, pkgs = render_java(root, arm)
            texts[arm["id"]] = open(os.path.join(src, "app", "App.java")).read().replace(JAVA_APP["third"], "")
            cls = os.path.join(root, "cls")
            os.makedirs(cls, exist_ok=True)
            srcs = []
            for d, _dd, fs in os.walk(src):
                srcs += [os.path.join(d, f) for f in fs if f.endswith(".java")]
            c = gd.run(["javac", "-nowarn", "-d", cls] + sorted(srcs))
            if c.returncode != 0:
                return None, None, "javac failed on %s: %s" % (arm["id"], c.stderr.decode()[:300])
            # ONE class directory per package, in the dependency order `pkgs` names — a package scanned
            # with its siblings' classes on the same path is not a separate package at all, which is the
            # isolation every arm here depends on.
            deps = [os.path.join(root, "d_" + pkg) for pkg in pkgs]
            for pkg, d in zip(pkgs, deps):
                os.makedirs(d, exist_ok=True)
                shutil.copytree(os.path.join(cls, pkg), os.path.join(d, pkg), dirs_exist_ok=True)
            app = os.path.join(root, "d_app")
            os.makedirs(app, exist_ok=True)
            shutil.copytree(os.path.join(cls, "app"), os.path.join(app, "app"), dirs_exist_ok=True)
        else:
            render = dict(rust=render_rust, ts=render_ts, swift=render_swift)[name]
            deps, app = render(root, arm)
            src_file = dict(rust=("app", "src", "lib.rs"), ts=("app", "src", "index.ts"),
                            swift=("app", "Sources", "App", "app.swift"))[name]
            whole = open(os.path.join(root, *src_file)).read()
            third_block = dict(rust=RUST_APP, ts=TS_APP, swift=SW_APP)[name]["third"]
            texts[arm["id"]] = whole.replace(third_block, "")
            # BUILD THE CONSUMER ONLY: it pulls every dependency package in transitively, so a build of
            # `app` is a build of the whole arm. Building each package separately would cost three
            # toolchain invocations to prove the same thing.
            err = build_proof(name, app)
            if err and err.startswith("SKIPPED"):
                notes.append("  NOTE  %s %-22s %s" % (name, arm["id"], err))
            elif err:
                return None, None, "%s (%s)" % (err, arm["id"])

        dep_reports = []
        for d in deps:
            r = scanner.scan(d)
            if not r.produced:
                return None, None, "%s: dependency scan produced no report for %s (rc=%d) %s" % (
                    arm["id"], d, r.rc, r.note)
            dep_reports.append(r.report)
            notes.append("  dep   %s %-22s %-8s %s" % (name, arm["id"], os.path.basename(d),
                                                       producer_note(r.report)))
        r = scanner.scan(app, deps=dep_reports if arm["chained"] else ())
        if not r.produced:
            return None, None, "%s: consumer scan produced no report (rc=%d) %s" % (arm["id"], r.rc, r.note)
        leaves, _unc = sa.leaf_info(r.report, ("::", "."))
        f = facts(leaves, ENTRY[name][arm["entry"]])
        if f is None:
            # ⟨0.21⟩ Row-1 fail-closed empty: the engine judged NOTHING. That is not "the consumer is
            # pure", and reading it as such is the fabrication mirror of the sin under test.
            return None, None, "%s: consumer report is a judged-nothing manifest (rc=%d)" % (arm["id"], r.rc)
        out[arm["id"]] = f
    cross = _assert_identical_consumers(texts)
    if cross:
        return None, None, cross
    return out, notes, None


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-part92-")
    print("=" * 100)
    print("CHAINED-DISPATCH UNION differential ⟨0.39⟩ — a consumer carries every implementor it can see")
    print("  fixture : THREE packages — iface (dispatches) · effimpl (a FOREIGN effectful impl) · app;")
    print("            c6 adds a FOURTH — `middle`, which dispatches over iface's abstraction and owns")
    print("            neither it nor any implementor of it (SOUNDNESS R504)")
    print("  property: c1 the foreign implementor's %s MUST reach the consumer;" % EFFECT)
    print("            c2 zero implementors MUST stay a disclosed Unknown (the toggle's other side);")
    print("            c3 an only-pure library MUST stay pure; c4 a sealed union stays EXACT;")
    print("            c5 unchained, the same consumer discloses via `invisible`;")
    print("            c6 a MIDDLE package that owns nothing must still name the member it dispatches on")
    print("  cross   : the consumer's dispatching source is BYTE-IDENTICAL across c1/c2/c3/c5, asserted")
    print("=" * 100)
    if NOBUILD:
        print("NOTE: CANDOR_PART92_NOBUILD is set — fixtures were NOT compiled. An absence-asserting")
        print("      control over an unbuilt program is not evidence; this run is for iteration only.")
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — c2_zero_impl's DEPENDENCY is being rendered with the")
        print("       'impl' variant (one pure implementor), so the arm that MUST stay a disclosed")
        print("       Unknown cannot be. This run's verdict MUST go red. A clean run never prints this.")

    table = assert_arm_table()
    if table:
        for t in table:
            print("  ARM TABLE: " + t)
        print("\nCHAINED-DISPATCH: the arm table contradicts itself — NOT a pass")
        return 2

    results, all_notes = {}, []
    for name in ("rust", "java", "ts", "swift"):
        res, notes, err = run_engine(name, ws)
        if err:
            if sa.engine_absent(err) or "no candor" in err or "no node" in err or "no swift" in err:
                print("  %-6s not available — skipped LOUDLY: %s" % (name, err))
            else:
                print("  %-6s BROKEN: %s" % (name, err))
                results[name] = "broken"
            continue
        results[name] = res
        all_notes += notes
    live = {k: v for k, v in results.items() if isinstance(v, dict)}
    if not live:
        print("\nCHAINED-DISPATCH: no engine available — NOT a pass")
        return 2
    if any(v == "broken" for v in results.values()):
        print("\nCHAINED-DISPATCH: an engine was present but broken — NOT a pass")
        return 2

    print("\nPRODUCER-SIDE DIAGNOSTICS (⟨0.39⟩ obligations 1 and 2 — printed, not asserted):")
    for n in all_notes:
        print(n)

    print()
    fails, xfail_passed = [], []
    for arm in ARMS:
        for name, res in sorted(live.items()):
            f = res[arm["id"]]
            if f == "SKIP":
                # DECLARED, and printed. A cell that says nothing reads like a pass; this one names the
                # engine and the arm so a reader can see the coverage hole rather than infer its absence.
                print("  SKIP  %-22s %-6s — declared inexpressible for this engine (see the arm's note)"
                      % (arm["id"], name))
                continue
            bad = judge(arm["want"], f)
            exp = XFAIL.get((arm["id"], name))
            if not bad:
                if exp:
                    print("  XFAIL ARM PASSED  %-22s %-6s — expectation is STALE: %s" % (arm["id"], name, exp))
                    xfail_passed.append((arm["id"], name))
                else:
                    print("  OK    %-22s %-6s %s" % (arm["id"], name, show(f, arm["want"])))
            elif exp:
                print("  xfail %-22s %-6s %s — %s" % (arm["id"], name, show(f, arm["want"]),
                                                          "; ".join(bad)))
            else:
                print("  FAIL  %-22s %-6s %s — %s  [%s]" % (arm["id"], name, show(f, arm["want"]),
                                                            "; ".join(bad), arm["why"]))
                fails.append((arm["id"], name))

    print()
    if xfail_passed:
        print("CHAINED-DISPATCH: %d xfail arm(s) PASSED — an expectation that has become true is a "
              "FAILURE here. Retire it from XFAIL in the same commit as the engine fix (SOUNDNESS R475)."
              % len(xfail_passed))
        return 1
    if fails:
        print("CHAINED-DISPATCH: %d cell(s) wrong — see SOUNDNESS R475 and SPEC §4 ⟨0.39⟩" % len(fails))
        return 1
    print("CHAINED-DISPATCH: OK — every engine's consumer carries the effects of every implementor "
          "visible to it, keeps the zero-implementor disclosure, and fabricates nothing over a "
          "legitimately-pure or sealed abstraction")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print("PART 92 selftest — the arm table and judge(), with NO engine and NO build")
        sys.exit(selftest())
    sys.exit(main())
