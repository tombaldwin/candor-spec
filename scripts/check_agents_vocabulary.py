#!/usr/bin/env python3
"""AGENT-FACING VOCABULARY drift gate — does every §1 effect name reach the docs an agent reads?

R155 (SOUNDNESS.md): SPEC.md defines `Llm` (⟨0.13⟩, shipped four-way) and every engine's classifier
polices it, but every agent-facing vocabulary copy — the umbrella `AGENTS.md`, each engine's own
`AGENTS.md`/`README.md`, and the EMBEDDED `--agents` contract a binary prints for itself — omitted it.
The mechanism: candor-rust's CI drift gate pins the repo doc to the embedded copy (doc == binary), so
the two drift TOGETHER and the gate stays green; nothing pins either of them to SPEC §1. `check_agents_drift.py`
(same job) checks the spec VERSION a doc teaches against SPEC.md's floor. This checks something that
drift gate cannot see: the effect VOCABULARY a doc teaches against SPEC.md's own table — the two are
independent axes and a doc can be version-correct while silently missing an effect name.

THE VOCABULARY IS DERIVED, NEVER HAND-LISTED. It is parsed out of SPEC.md's own §1 table (between the
`## 1. Effects` heading and the next `##` heading), because a hand-typed copy in this script is exactly
the kind of second copy that rots the way the docs under test already have. `Unknown` is excluded —
SPEC.md says so explicitly: "where this document says 'a §1 effect name' ... it means every effect in
the table above, excluding `Unknown`" (it is a visibility marker, not a declarable effect; nothing in
an agent's vocabulary — a `deny` set, a manifest — ever names it as an effect to reach).

WHAT IS CHECKED, per copy: every derived effect name appears at least once as a whole word (`\\bName\\b`,
case-sensitive — `Llm` is a token, not a substring of prose). This is deliberately a coverage check, not
a "the doc lists them all in one place" check: several docs (candor-ts, candor-java, candor-agents,
candor-swift's AGENTS.md) never enumerate the full vocabulary in one line, and the reference contract
(candor-spec/AGENTS.md) explicitly defers to being "language-agnostic" rather than exhaustive — so the
only mechanically honest question is "does this name ever reach an agent reading this file", not "is it
in a specific list."

EMBEDDED CONTRACTS. Where a built engine binary exists, this ALSO runs its `--agents` (read-only —
never `scan`/`verify`/anything that writes) and applies the same check to what it prints, because a
repo doc and an embedded copy can drift from each other even when a doc-only gate (`check_agents_drift.py`)
is green — proven precedent: candor-swift's `privacy/1` vs `privacy/2` (see `check_agents_vs_engine.py`).
A missing binary reports UNRUN for that engine and is NEVER treated as passing — an engine this gate
could not ask a question of has not answered it.

Run:  python3 scripts/check_agents_vocabulary.py
CI:   the agents-doc-drift job in .github/workflows/conformance.yml (cheap — no engine checkouts there,
      so the embedded-contract checks report UNRUN in CI and only run locally where binaries are built).

Exit 0 = every checked copy names every SPEC §1 effect · 1 = at least one (copy, effect) pair is missing
· 2 = SPEC.md's own table could not be parsed (nothing to check against).
"""
import glob
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SPEC_REPO = HERE.parent
SIBS = SPEC_REPO.parent


def sibling(env_var, default_dirname):
    return pathlib.Path(os.environ.get(env_var, str(SIBS / default_dirname)))


# ---------------------------------------------------------------------------------------------------
# 1. Derive the vocabulary from SPEC.md §1 — never hand-listed.
# ---------------------------------------------------------------------------------------------------
def spec_vocabulary(spec_text: str):
    m = re.search(r"^## 1\. Effects\n(.*?)^## ", spec_text, re.S | re.M)
    if not m:
        return None, "SPEC.md has no '## 1. Effects' section (or no following '## ' heading to end it)"
    section = m.group(1)
    rows = re.findall(r"^\|\s*`([A-Za-z]+)`\s*\|", section, re.M)
    if not rows:
        return None, "SPEC.md §1 has no `| `Name` | ... |` table rows"
    # `Unknown` is a visibility marker, not a declarable effect — SPEC.md says so explicitly (see the
    # docstring above); every consumer of "a §1 effect name" is defined to exclude it.
    vocab = [name for name in rows if name != "Unknown"]
    if not vocab:
        return None, "SPEC.md §1 table parsed but yielded no effect names besides `Unknown`"
    return vocab, None


# ---------------------------------------------------------------------------------------------------
# 2. Doc copies to check. Every one is a place an agent is told to read the vocabulary from.
# ---------------------------------------------------------------------------------------------------
def doc_targets():
    return [
        ("umbrella AGENTS.md", SIBS / "candor" / "AGENTS.md"),
        ("candor-spec AGENTS.md", SPEC_REPO / "AGENTS.md"),
        ("candor-rust AGENTS.md", SIBS / "candor-rust" / "AGENTS.md"),
        ("candor-java AGENTS.md", SIBS / "candor-java" / "AGENTS.md"),
        ("candor-ts AGENTS.md", SIBS / "candor-ts" / "AGENTS.md"),
        ("candor-agents AGENTS.md", SIBS / "candor-agents" / "AGENTS.md"),
        ("candor-swift AGENTS.md", SIBS / "candor-swift" / "AGENTS.md"),
        ("candor-swift README.md", SIBS / "candor-swift" / "README.md"),
    ]


# ---------------------------------------------------------------------------------------------------
# 3. Embedded `--agents` contracts. Read-only invocation only — never a flag that writes/scans/gates.
# ---------------------------------------------------------------------------------------------------
def run_readonly(cmd, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True, timeout=timeout, cwd=cwd)
        return p.stdout or ""
    except Exception:
        return ""


def embedded_contracts():
    """Yields (label, text_or_None). None means UNRUN — the binary was not found, never a pass."""
    # rust
    rust_dir = sibling("CANDOR", "candor-rust")
    rust_bin = os.environ.get("CANDOR_SCAN_BIN")
    if not rust_bin:
        for rel in ("target/release/candor-scan", "target/debug/candor-scan"):
            cand = rust_dir / rel
            if cand.exists():
                rust_bin = str(cand)
                break
    if rust_bin and pathlib.Path(rust_bin).exists():
        yield "candor-rust --agents (embedded)", run_readonly([rust_bin, "--agents"])
    else:
        yield "candor-rust --agents (embedded)", None

    # java — newest *-all.jar, mirroring conformance/run.sh's `ls -t … | head -1`.
    java_dir = sibling("CANDOR_JAVA", "candor-java")
    java_jar = os.environ.get("CANDOR_JAVA_JAR")
    if not java_jar:
        jars = sorted(glob.glob(str(java_dir / "build" / "libs" / "*-all.jar")),
                       key=lambda p: pathlib.Path(p).stat().st_mtime if pathlib.Path(p).exists() else 0,
                       reverse=True)
        java_jar = jars[0] if jars else None
    if java_jar and pathlib.Path(java_jar).exists():
        yield "candor-java --agents (embedded)", run_readonly(["java", "-jar", java_jar, "--agents"])
    else:
        yield "candor-java --agents (embedded)", None

    # ts
    ts_dir = sibling("CANDOR_TS", "candor-ts")
    ts_script = ts_dir / "scan.mjs"
    if ts_script.exists():
        yield "candor-ts --agents (embedded)", run_readonly(["node", str(ts_script), "--agents"])
    else:
        yield "candor-ts --agents (embedded)", None

    # swift
    swift_dir = sibling("CANDOR_SWIFT", "candor-swift")
    swift_bin = os.environ.get("CANDOR_SWIFT_BIN")
    if not swift_bin:
        for rel in (".build/release/candor-swift", ".build/debug/candor-swift"):
            cand = swift_dir / rel
            if cand.exists():
                swift_bin = str(cand)
                break
    if swift_bin and pathlib.Path(swift_bin).exists():
        yield "candor-swift --agents (embedded)", run_readonly([swift_bin, "--agents"])
    else:
        yield "candor-swift --agents (embedded)", None


def missing_effects(text: str, vocab):
    return [e for e in vocab if not re.search(rf"\b{re.escape(e)}\b", text)]


def main() -> int:
    try:
        spec_text = (SPEC_REPO / "SPEC.md").read_text(encoding="utf-8")
    except OSError as e:
        print(f"VOCAB GATE: cannot read SPEC.md: {e}", file=sys.stderr)
        return 2
    vocab, err = spec_vocabulary(spec_text)
    if vocab is None:
        print(f"VOCAB GATE: {err}", file=sys.stderr)
        return 2

    print(f"SPEC.md §1 vocabulary (derived, {len(vocab)} declarable effects, `Unknown` excluded):")
    print("  " + ", ".join(f"`{e}`" for e in vocab))
    print()

    all_missing = []   # (copy, [effects])
    unrun = []

    print("Repo/README doc copies:")
    for label, path in doc_targets():
        if not path.exists():
            unrun.append(label)
            print(f"  · {label}: UNRUN — file not found at {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        miss = missing_effects(text, vocab)
        if miss:
            all_missing.append((label, miss))
            print(f"  ✘ {label}: missing {', '.join(f'`{e}`' for e in miss)}")
        else:
            print(f"  ✔ {label}: names every effect")
    print()

    print("Embedded `--agents` contracts (built binaries only — read-only invocation):")
    for label, text in embedded_contracts():
        if text is None:
            unrun.append(label)
            print(f"  · {label}: UNRUN — no built binary found (never counted as a pass)")
            continue
        if not text.strip():
            unrun.append(label)
            print(f"  · {label}: UNRUN — binary produced no output for --agents")
            continue
        miss = missing_effects(text, vocab)
        if miss:
            all_missing.append((label, miss))
            print(f"  ✘ {label}: missing {', '.join(f'`{e}`' for e in miss)}")
        else:
            print(f"  ✔ {label}: names every effect")
    print()

    if unrun:
        print(f"NOT CHECKED (reported, never implied as passing): {', '.join(unrun)}")
        print()

    if all_missing:
        print("\033[31mVOCAB GATE: missing (copy, effect) pairs:\033[0m")
        for label, miss in all_missing:
            for e in miss:
                print(f"  ✘ {label} — `{e}`")
        return 1

    print(f"\033[32mVOCAB GATE: OK — every checked copy names every one of the {len(vocab)} "
          f"SPEC §1 effects\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
