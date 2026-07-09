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

    # 3 — AGENTS.md must not reintroduce the stale claims the 2026-07 review caught.
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
