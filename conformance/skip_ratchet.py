#!/usr/bin/env python3
"""
A SKIP COUNT MAY FALL. IT MAY NOT RISE.

THE FAILURE THIS WAS BUILT FOR, as it happened (2026-08-13). Falsifying a new PART 40 row, I disabled
candor-rust's `must_hedge` — a total removal of the ⟨0.28⟩ Rung A disclosure — and re-ran the suite:

    candor-scan   pass=65 skip=1  fail=0      (before)
    candor-scan   pass=43 skip=23 fail=0      (Rung A entirely gone)

Twenty-two cells flipped and **the part did not redden**. The suite caught that run through PART 27; the
part that drives those exact cells said nothing was wrong. A whole rung can un-ship in silence.

WHY, AND WHY IT IS NOT A BUG IN THAT PART. Reference-led rows score an unshipped rung as SKIP so the
suite stays green while engines catch up — deliberate, and the right default for a family that ships a
rung one engine at a time. The cost is that "never shipped" and "shipped, then regressed" are THE SAME
OBSERVATION. Every reference-led row here has it: PART 37 (a)/(d)/(e), PART 38's rows, PART 39 (ii),
PART 38 (cross), PART 40's matrix.

THE RATCHET. Skip counts are frozen in `skip-baseline.json`; a count that RISES fails, a count that
FALLS is the desired direction and silently updates nothing. That asymmetry is the whole design:

FALSIFIED, by re-running that exact scenario against the finished gate. With `must_hedge` disabled the
ratchet fails and names THREE keys, not one:

    candor-scan   pass=43 skip=23 fail=0                                  <- PART 40, still green
    FAIL skip-ratchet: `tally:candor-scan`   skipped 23, baseline 1       <- PART 40's matrix
    FAIL skip-ratchet: `cell:candor-scan:ii` skipped  1, baseline 0       <- PART 39, caveat re-disclosure
    FAIL skip-ratchet: `cell:candor-scan:ok` skipped  1, baseline 0       <- PART 38, `ok` withdrawal
    -> skip-ratchet: 3 key(s) rose

Restoring `must_hedge` returns the suite to `conformance: OK`. Note what the third and fourth lines say:
the un-shipped rung degraded rows in THREE parts and NONE of them reddened. This was written believing it
was a PART 40 problem; it is a property of every reference-led row in the suite, which is why the gate is
scoped suite-wide and not to the part that motivated it.

  · it CANNOT redden on success. An earlier vacuity floor in PART 40 keyed on `skips == 0` and had to be
    removed for exactly that — once every verb complied, skips legitimately reached zero and the floor
    would have failed the suite FOR SUCCEEDING. Keying on the DELTA rather than the value is the mirror
    of that mistake and does not reintroduce it;
  · it is the shape this project already trusts — the `key-shapes-baseline.json` grandfather list and
    `sink-surface-baseline.json`'s waivers are both ratchets that may only tighten, and both have caught
    real drift within a day of existing.

INSTALLED WHEN THE SURFACE WAS NEAR-EMPTY, deliberately. The opening baseline is FIVE skips over four
keys, all of them PART 40 tallies — the per-cell SKIPs cleared earlier the same day when java and swift
shipped the `fix` withholding. A baseline captured here is close to "everything is shipped", so almost
any rise is a regression rather than noise. Waiting until the next rung opens twenty skips would bake
those in as normal.

THE COST, STATED. Legitimately ADDING coverage raises skips — a new verb an engine does not implement, a
new state it does not handle. The baseline then needs a deliberate update, which is a reviewable act
rather than an accident. That is the feature: "I added coverage and the skip count went up" should have
to be said out loud, because the alternative is a number that drifts upward one unremarkable commit at a
time until it means nothing.

WHAT IT COUNTS, and the limit of that. Two shapes appear in the log and both are parsed:

  · the per-engine tallies PART 40 prints (`candor-scan   pass=65 skip=1 fail=0`), keyed by engine;
  · every other line containing a SKIP token, keyed by the (part, engine, cell) it names where the line
    is structured enough to say, else by a normalised form of the line itself.

A line whose wording changes therefore reads as one key disappearing and another appearing — the
disappearance passes (a fall) and the appearance fails (a rise). That is noisy-but-safe: it fails toward
telling you, and the fix is to re-baseline with the new wording, which is one reviewable line.

USAGE
    python3 skip_ratchet.py <run.log>                     # the gate
    python3 skip_ratchet.py <run.log> --write-baseline    # after a DELIBERATE coverage change
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "skip-baseline.json")

# `candor-scan   pass=65 skip=1 fail=0` — the per-engine tally form.
TALLY = re.compile(r"^\s*(candor-[a-z]+)\s+pass=(\d+)\s+skip=(\d+)\s+fail=(\d+)")
# A SKIP line that names its engine and cell: `  candor-java  (cross) SKIP — …`
CELL = re.compile(r"^\s*(candor-[a-z]+)\s*\(([^)]+)\)\s+SKIP")
# Anything else carrying a SKIP token AS A RESULT — `… SKIP — reason` or `… SKIP: reason`.
#
# MEASURED on the first baseline: a bare `\bSKIP\b` counted three VERDICT lines that merely MENTION the
# convention ("-> MATCH — … the rest print SKIP (reference-led until 0.28 ships)"). Those are prose, not
# skipped cells, so the total was not a skip count — and worse, rewording a verdict line would have read
# as one key vanishing and another appearing, i.e. a spurious RISE. A result line always separates the
# token from its reason with an em dash or a colon; a sentence about skipping does not.
#
# THE PUNCTUATION IS ALSO WHAT KEEPS A RUNNER-ABSENCE SKIP OUT OF THE COUNT, and that is a rule, not a
# happy accident of the regex. Two different facts wear the word SKIP:
#
#   · REFERENCE-LED — "this engine has not shipped the rung." A rung, watchable, and the whole reason
#     this gate exists. Written `… SKIP — reason`, and COUNTED.
#   · RUNNER-ABSENCE — "this leg does not have this engine." A property of the LEG, not the engine.
#     Written `… -> SKIP     (reason)`, and NOT counted. PART 47's rows are the canonical spelling;
#     PARTs 63, 67 and 68 follow it.
#
# WHY ABSENCE MUST NOT BE COUNTED. There is one baseline file and two legs: ubuntu carries three engines
# (no swift toolchain on those runners) and macos four. A count of swift's absence is true on one leg and
# false on the other, so baselining it puts a runner condition in a file that is supposed to hold rungs —
# and it has to be raised again for every future part that gains a swift row, which is exactly the number
# that "drifts upward one unremarkable commit at a time" this header warns about.
# MEASURED 2026-08-25: PARTs 63 and 68 landed with the em-dash spelling and reddened the ubuntu leg at
# `line:swift SKIP — engine absent` skipped 2, baseline 0 — while the macOS leg scored all four cells of
# both parts OK. The coverage had not dropped; the wording had.
#
# AND ABSENCE IS ALREADY RATCHETED, harder than a skip count could be, which is why declining to count it
# loses nothing: [6]/[6c] FAIL outright when an engine is PRESENT but produced no report (the
# TS_PRESENT-vs-TS_OK split), and CONFORMANCE_REQUIRE_ALL=1 on the macOS leg FAILs when an engine is
# absent at all. A row's `if [ -n "$SW_OK" ]` can therefore only fall through when the engine is
# structurally absent on this leg, or the suite is ALREADY red.
LOOSE = re.compile(r"\bSKIP\b\s*[—:]")
VERDICT = re.compile(r"^\s*->")
# An engine the RUNNER does not have. The suite already announces this itself, loudly and on purpose —
# "candor-swift: not present on this runner", plus a `CONFORMANCE_REQUIRE_ALL=1` escape to make absence
# fatal where a leg demands all four. Absence is a first-class state of a run, and this gate reads the
# suite's own declaration of it rather than re-deriving engine availability from the toolchain, which
# would be a SECOND spelling of a fact the suite already states and free to drift from it.
ABSENT = re.compile(r"(candor-[a-z]+).*not present on this runner")
# Volatile substrings that must not enter a key: temp dirs, counts, hashes.
SCRUB = [(re.compile(r"/(?:var|tmp|private)/\S+"), "<path>"),
         (re.compile(r"\b\d+\b"), "<n>"),
         (re.compile(r"\s+"), " ")]


def key_of(line):
    m = CELL.match(line)
    if m:
        return "cell:%s:%s" % (m.group(1).strip(), m.group(2).strip())
    s = line.strip()
    for pat, rep in SCRUB:
        s = pat.sub(rep, s)
    return "line:" + s[:120]


def counts(path):
    """(key -> skip count, engines the suite declared absent) over the whole run log."""
    out = collections.Counter()
    absent = set()
    with open(path, errors="replace") as fh:
        for line in fh:
            a = ABSENT.search(line)
            if a:
                absent.add(a.group(1).strip())
            m = TALLY.match(line)
            if m:
                out["tally:" + m.group(1).strip()] += int(m.group(3))
                continue
            if LOOSE.search(line) and not VERDICT.match(line):
                out[key_of(line)] += 1
    return out, absent


def main():
    args = [a for a in sys.argv[1:]]
    write = "--write-baseline" in args
    args = [a for a in args if not a.startswith("--")]
    if not args:
        print("skip_ratchet: usage: skip_ratchet.py <run.log> [--write-baseline]")
        return 2
    log = args[0]
    if not os.path.exists(log):
        # An ABSENT log is a failure, not a pass. The gate runs last in the suite; if the log is missing
        # the suite did not produce one, and "no log, no skips, nothing rose" is the exact vacuity this
        # family keeps finding in its own instruments.
        print("     FAIL skip-ratchet: no run log at %s — the ratchet cannot see what it is ratcheting, "
              "and an unreadable instrument must never read as a clean one" % log)
        return 1

    now, absent = counts(log)
    if write:
        payload = {
            "_": ["SKIP RATCHET BASELINE — see skip_ratchet.py's header.",
                  "A count here may FALL freely (an engine shipped a rung). A count that RISES fails.",
                  "Regenerate ONLY for a deliberate coverage change, and say so in the commit: a skip",
                  "count that drifts upward one unremarkable commit at a time stops meaning anything."],
            "skips": dict(sorted(now.items())),
        }
        with open(BASELINE, "w") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print("skip-ratchet: baseline written — %d keys, %d skips total"
              % (len(now), sum(now.values())))
        return 0

    if not os.path.exists(BASELINE):
        print("     FAIL skip-ratchet: no baseline at %s — an absent ratchet must not read as a passing "
              "one (regenerate with --write-baseline)" % BASELINE)
        return 1
    base = json.load(open(BASELINE)).get("skips", {})

    # A SHORT READ MUST NOT READ AS A CLEAN ONE. The suite tees its output and this gate reads that log
    # while tee is still draining, so a truncated tail would drop SKIP lines — and fewer skips is a PASS.
    # Measured on the first wired run: the in-suite count and a re-read of the finished file agree (5 over
    # 4 keys), so no truncation was observed. One observation is not a guarantee, hence this: PART 40
    # prints exactly one tally per engine, unconditionally, so a baseline tally key that is ABSENT means
    # the log stopped early or the matrix did not run. Cell keys are exempt — a cell that stops skipping
    # legitimately prints PASS instead, and its key is SUPPOSED to disappear.
    # AN ENGINE THIS RUNNER DOES NOT HAVE IS NOT A MISSING TALLY. The conformance CI runs two legs: a
    # ubuntu leg with rust/java/ts (no swift toolchain on those runners) and a macos leg with all four.
    # This guard was written on a four-engine machine and stated over that INSTANCE — "PART 40 prints one
    # tally per engine, unconditionally" — which is only true of engines the run actually HAS. It reddened
    # the ubuntu leg on its first push. Same shape as the SPEC clause in #97, one layer down: a rule
    # written over the situation in front of me rather than the condition that makes it true.
    #
    # The exemption reads the suite's OWN declaration ("not present on this runner"), so absence still has
    # to be stated in the log to be honoured — a tally that vanishes with no such line is still the
    # truncation case and still FAILS. The absent set is printed, so an engine quietly dropping out of a
    # leg is visible rather than inferred from a number that got smaller.
    missing = sorted(k for k in base
                     if k.startswith("tally:") and k not in now and k[len("tally:"):] not in absent)
    if missing:
        for k in missing:
            print("     FAIL skip-ratchet: `%s` is in the baseline but absent from the log, and the suite "
                  "never said that engine was \"not present on this runner\" — so it WAS available and its "
                  "tally still did not print, meaning the log was truncated or the matrix never ran. Fewer "
                  "skips scores as a PASS, so this must fail loudly." % k)
        print("  -> skip-ratchet: %d baseline tally key(s) missing" % len(missing))
        return 1

    risen = [(k, base.get(k, 0), v) for k, v in sorted(now.items()) if v > base.get(k, 0)]
    fell = sum(max(0, base.get(k, 0) - now.get(k, 0)) for k in base)
    if risen:
        for k, was, is_ in risen:
            print("     FAIL skip-ratchet: `%s` skipped %d, baseline %d — a SKIP means \"this engine has "
                  "not shipped the rung\", so a RISE is a rung that un-shipped. Reference-led rows cannot "
                  "tell that from never-shipped, which is why this exists. If the coverage genuinely grew, "
                  "re-baseline and say so." % (k, is_, was))
        print("  -> skip-ratchet: %d key(s) rose" % len(risen))
        return 1
    print("  skip-ratchet: OK — %d skips over %d keys, none risen%s%s"
          % (sum(now.values()), len(now), (", %d fell" % fell) if fell else "",
             (" [not on this runner: %s]" % " ".join(sorted(absent))) if absent else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
