#!/usr/bin/env python3
"""AGENTS.md drift gate.

AGENTS.md is the language-agnostic consumer contract, and it rotted once: it taught the legacy
v0.1 bare-array report years after the envelope shipped, because nothing checked it. This gate
pins the two facts that rot silently:

  1. the spec version AGENTS.md teaches (its envelope example's `candor.spec`) equals SPEC.md's
     floor declaration (the `**Version X.Y**` header line), and
  2. the envelope example actually parses as the SPEC §2 shape — a `candor` provenance header
     (version/toolchain/spec) plus a `functions` array whose entries carry the required fields.

Run:  python3 scripts/check_agents_drift.py   (exit 0 = in step, 1 = drift, 2 = can't check)
CI:   the agents-doc-drift job in .github/workflows/conformance.yml
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    try:
        spec_text = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    except OSError as e:
        print(f"DRIFT GATE: cannot read inputs: {e}", file=sys.stderr)
        return 2

    # 1 — SPEC.md's floor declaration.
    m = re.search(r"^\*\*Version (\d+\.\d+)\*\*", spec_text, re.M)
    if not m:
        print("DRIFT GATE: SPEC.md has no '**Version X.Y**' floor declaration", file=sys.stderr)
        return 2
    floor = m.group(1)

    # 2 — AGENTS.md's first ```json block is the envelope example; it must parse.
    blocks = re.findall(r"```json\s*\n(.*?)```", agents_text, re.S)
    if not blocks:
        err("AGENTS.md has no ```json envelope example at all")
    else:
        try:
            env = json.loads(blocks[0])
        except json.JSONDecodeError as e:
            env = None
            err(f"AGENTS.md envelope example is not valid JSON: {e}")
        if env is not None:
            if not isinstance(env, dict) or "candor" not in env or "functions" not in env:
                err("AGENTS.md envelope example is not the SPEC §2 `{ candor, functions }` shape "
                    "(the legacy v0.1 bare array must not come back)")
            else:
                header = env["candor"]
                for key in ("version", "toolchain", "spec"):
                    if not isinstance(header, dict) or key not in header:
                        err(f"envelope example's `candor` header is missing `{key}` (SPEC §2.1)")
                if isinstance(header, dict) and header.get("spec") != floor:
                    err(f"AGENTS.md teaches spec {header.get('spec')!r} but SPEC.md declares the "
                        f"floor as {floor!r} — update the envelope example (and re-read the doc "
                        f"for other stale rungs)")
                fns = env["functions"]
                if not isinstance(fns, list) or not fns:
                    err("envelope example's `functions` must be a non-empty array")
                else:
                    entry = fns[0]
                    for key in ("fn", "loc", "inferred", "direct", "unresolved", "hash"):
                        if not isinstance(entry, dict) or key not in entry:
                            err(f"envelope example entry is missing `{key}` (SPEC §2; `hash` is a "
                                f"0.4 MUST for producers)")
                    if isinstance(entry, dict):
                        for key in ("inferred", "direct"):
                            if key in entry and not isinstance(entry[key], list):
                                err(f"envelope example entry's `{key}` must be an array")

    # 3 — SPEC.md's OWN envelope examples must declare the floor SPEC.md itself declares.
    #
    # THE HOLE THIS CLOSES, measured twice. Every check above reads AGENTS.md and holds it against
    # SPEC.md's `**Version X.Y**` line — so SPEC.md is the AUTHORITY here and nothing ever reads it back.
    # A floor bump rewrites the prose spelling and leaves the JSON spelling in the code fences: at 0.30
    # candor-java's release preflight caught `"spec":    "0.30"` by hand (the alignment padding had also
    # defeated a hand sweep for the exact string `"spec": "0.30"`), and at ⟨0.32⟩ THREE fences in this
    # file still said `"spec": "<prior floor>"` while line 20 said `**Version 0.32**`. Those fences are what an
    # implementer copies, so a stale one teaches the wrong contract from the document that defines it.
    #
    # DELIBERATELY JSON-ONLY, unlike the sweep the engines now run over their READMEs. This file is dense
    # with PROSE rung references — `⟨0.27⟩`, "measured at spec 0.28", clause histories — that are true
    # statements about the past and must not move. A prose sweep here would be a false-positive machine.
    # The `"spec": "X.Y"` form inside a fence is always an ENVELOPE EXAMPLE, i.e. always a claim about the
    # CURRENT contract, so restricting to it is not a weakening: it is the whole class.
    #
    # The exemption is per-LINE, because that is where this document already puts the marker (§3.3.1's
    # replaced-source-file example ends `(measured at spec 0.28, informative)` and the `"spec": "0.28"` it
    # annotates sits earlier on the same line). Keying on the family's `, informative)` marker rather than
    # on a list of tolerated old versions means a legitimate annotation never needs this gate edited.
    json_spec = re.compile(r'"spec"\s*:\s*"(\d+\.\d+)"')
    for lineno, line in enumerate(spec_text.splitlines(), 1):
        if ", informative)" in line:
            continue
        for sm in json_spec.finditer(line):
            if sm.group(1) != floor:
                err(f"SPEC.md:{lineno} carries an envelope example declaring spec {sm.group(1)!r} while "
                    f"SPEC.md declares the floor as {floor!r} — `{line.strip()[:110]}`. If it is a "
                    f"historical illustration, annotate the line `(measured at spec {sm.group(1)}, "
                    f"informative)`; otherwise bump it.")

    # 3b — AND THE CHECK ABOVE MUST BE ABLE TO FAIL. It reads clean when the document is clean, when the
    # pattern has stopped matching, and when the exemption swallows everything — three states, one
    # output. So both halves are exercised on a fixture before the document's silence is read as evidence.
    probe_hit = [m.group(1)
                 for ln in ('  "candor": { "toolchain": "x", "spec":    "0.9" },',
                            '{ "spec": "0.7", "ok": false }')
                 for m in json_spec.finditer(ln)]
    probe_exempt = [m.group(1)
                    for ln in ('{ "spec": "0.28", … }   <- (measured at spec 0.28, informative)',)
                    if ", informative)" not in ln
                    for m in json_spec.finditer(ln)]
    if probe_hit != ["0.9", "0.7"] or probe_exempt != []:
        err(f"CONTROL FAILED — the SPEC.md envelope sweep no longer discriminates (matched {probe_hit}, "
            f"want ['0.9', '0.7']; matches on an exempted line {probe_exempt}, want []). Until that is "
            f"fixed the check above is VACUOUS and its silence is not evidence.")

    # 3c — README.md's FAMILY TABLE, and every other prose spec claim in the two docs.
    #
    # THE HOLE THIS CLOSES. Checks 2 and 3 read one JSON envelope in AGENTS.md and every JSON fence in
    # SPEC.md. Nothing in this repo ever read README.md, whose family table states the contract FIVE
    # times — once per engine, as `**shipped (spec X.Y)**` — and which is the first document a reader of
    # the spec meets. Each of the four code engines gained a sweep of its own README at ⟨0.32⟩; the
    # repo that DEFINES the version was the one left without one.
    #
    # PROSE IS SAFE HERE, unlike in SPEC.md. Check 3's header explains why SPEC.md is deliberately
    # JSON-only: that file is dense with true statements about past rungs. README.md and AGENTS.md are
    # not — they describe the CURRENT contract — so the wider sweep the engines run is the right one,
    # with the family's `(spec X.Y, informative)` marker as the escape hatch for a deliberate historical
    # note.
    #
    # THE GRAMMAR is the family's shared one: `spec` + one to EIGHT of [-: "*)\]] + <digits>.<digits>.
    # Eight, not four, because SPEC.md's own aligned `"spec":    "0.32"` needs six (spec 0.32, informative).
    # `)` and `]`, because candor-swift's README says `[candor-spec](…) 0.32`. Both were live in
    # shipped documents that every gate in the family read clean over.
    claim = re.compile(r'spec[-: "*)\]]{1,8}(\d+\.\d+)')

    def claims(text: str) -> list[tuple[str, str]]:
        return [(m.group(1), text[m.start():m.end() + 16]) for m in claim.finditer(text)
                if not text[m.end():m.end() + 16].startswith(", informative)")]

    # THE CONTROL FIRST, same fixture as the four engines carry, so a grammar that quietly narrows in
    # one repo reddens rather than going silent. A sweep that matches nothing reads exactly like a
    # sweep over a clean document.
    ctl = [v for v, _ in claims(
        'carrying `unitKind` (spec 0.8, informative); ordinary\n'
        'This project is on candor-java 9.9.9 (spec 0.9).\n'
        'a section reference, spec §6.1, is not a version\n'
        'the gate prints { "spec": "0.7", "ok": true }\n'
        'and the hyphenated attributive spec-0.6 form\n'
        'an aligned envelope column, { "spec":    "0.5" }\n'
        'a markdown link [candor-spec](https://example.org/candor-spec) 0.4\n')]
    if ctl != ["0.9", "0.7", "0.6", "0.5", "0.4"]:
        err(f"CONTROL FAILED — the prose spec-claim sweep no longer discriminates (flagged {ctl}, want "
            f"['0.9', '0.7', '0.6', '0.5', '0.4']). Until that is fixed the README/AGENTS sweep below "
            f"is VACUOUS and its silence is not evidence.")
    else:
        for name, text in (("README.md", None), ("AGENTS.md", agents_text)):
            if text is None:
                try:
                    text = (ROOT / name).read_text(encoding="utf-8")
                except OSError as e:
                    err(f"cannot read {name}: {e}")
                    continue
            for version, ctx in claims(text):
                if version != floor:
                    err(f"{name} claims spec {version} but SPEC.md declares the floor as {floor} — at "
                        f'"{ctx}". If that is a historical marker naming the rung a feature arrived '
                        f'at, write it "(spec {version}, informative)"; otherwise bump it.')

    # 4 — AGENTS.md must not reintroduce the stale claims the 2026-07 review caught.
    for stale in ("JSON array, one object per function", "(0.5 draft)"):
        if stale in agents_text:
            err(f"AGENTS.md contains the stale phrase {stale!r} (the pre-envelope wording)")

    if errors:
        print("AGENTS.md drift gate FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"AGENTS.md drift gate OK (floor {floor}; envelope example parses as the §2 shape)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
