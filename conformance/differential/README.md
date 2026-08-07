# Generative grammar differentials

Two instruments, one method, and a reason they exist.

## Why

Every config-layer defect found on 2026-08-06 — a NO-BREAK SPACE hiding the `engine` key while its pin
went unenforced, Unicode digits normalising as a version so an unreadable line was hidden by a qualified
pin, a `deps` path split on the wrong whitespace, a trailing separator surviving a trim — was found **by
hand, one spelling at a time, over hours**. They are all instances of a single property:

> the five engines must read the same config the same way.

`run.sh`'s PART 33 pins that property with a handful of rows, and its own comment records the lesson
those rows taught: *a row that pins one spelling of a rule pins one spelling of a rule* — the two-token
`engine 0.26.0 oops` was green five-way while the one-token `engine garbage` split the family four
against one, silently, for as long as the row existed. Hand-written rows will always be a sample.

These enumerate the space instead.

## The method

**No expected-value table.** The assertion is that the engines AGREE on the exit code, so a divergence is
a finding without anyone having to be right in advance — the same construction as the P1 self-differential
parts (24–29). What "correct" is gets decided after the differential points at a row.

## The two instruments

| file | grammar | shapes |
|---|---|---|
| `config_grammar_gen.py` | `.candor/config` — separators, versions, qualifiers, trailers, every key | 2546 |
| `policy_grammar_gen.py` | the §6.2 policy DSL — verbs, effects, filters, scopes, malformed shapes | 61 |

Each generator emits `(label, text)`; the runner writes the text, runs all engines, compares exit codes.

## Calibration — read this before trusting a green run

A differential that has never failed is not evidence. Both were calibrated against a **real regression**,
not a hypothetical one:

- **config**: candor-agents at the commit *before* the ASCII-digit fix (interpreted, so no build needed).
  27 rows diverge, every one a `paired/…` shape — a junk line beside a qualified pin, which is the only
  shape that reveals it. 133 control rows still agree.
- **policy**: a copy of candor-ts with its unrecognised-token error swallowed — the ⟨0.24⟩ fail-open.
  14 rows light up, all the malformed-token shapes; the rest still agree.

## Two traps this harness fell into, both worth keeping

1. **A shared target directory measures the harness.** Every engine writes into `<target>/.candor/`, and
   candor-agents drops `report.*.json` in the cwd. Two runner instances — or one whose children outlived
   a `pkill` of its parent — write one another's config files, and you get a page of divergences that
   reproduce nowhere. The tell was a `.sb-…` atomic-write temp file under a directory nothing should have
   been writing to. **Build a fresh target per invocation.**
2. **A differential is only about the thing you vary.** The first policy run reported 39 of 61 shapes
   diverging: candor-agents had no agent files to gate at all, and `app` was a scope in java's fixture and
   nowhere else. Run it over `conformance/gate/`, whose fixtures are built to perform the same effects in
   the same scope in every language. Four scoped rows still differ for exactly that reason and are
   expected — java's fixture is the only one with an `app` package.
