#!/usr/bin/env python3
"""Every documents-only script CI runs from candor-spec must be in scripts/doc-gates.sh, or be exempt BY NAME.

Measured 2026-11-13, the 0.42.0 cut. `scripts/check_agents_drift.py` runs in the `agents-doc-drift` CI job and
was not in doc-gates.sh, so `doc-gates: OK` was green locally while the job went red after the push (SPEC.md
carried an unannotated `"spec": "0.41"` envelope line). Adding that one gate fixes the instance; this checks the
CLASS: a script wired into a workflow with no row here is the same hole, and the only thing that can notice a
new one is something that reads the workflow.

  python3 scripts/ci-doc-gate-coverage.py            # 0 covered, 1 uncovered / stale exemption, 2 cannot check
  python3 scripts/ci-doc-gate-coverage.py --selftest # seeds an uncovered script and a stale exemption; both must fire

An exemption carries its REASON, and a stale one (the script is no longer in any workflow, or is now in
doc-gates) fails too, so the list cannot rot into a place to park things.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# script -> why doc-gates.sh does not run it. Every entry is a measured reason, not a convenience.
EXEMPT = {
    "scripts/check_agents_vocabulary.py":
        "reads the SIBLING repos' AGENTS.md/README.md and reports OK over whichever are absent (NOT CHECKED), "
        "so as a doc-gates row it would be green over an unrun comparison; it needs the CI sibling checkouts",
    "scripts/check_agents_vs_engine.py":
        "invokes the BUILT engines (what they emit vs what their contract claims); not documents-only",
    "check.sh":
        "lean.yml: the Lean checker, needs a Lean toolchain",
}

STEP = re.compile(r'(?:python3|bash)\s+"?(?:\$GITHUB_WORKSPACE/candor-spec/)?((?:scripts/|conformance/)?[\w./-]+\.(?:py|sh))')


def ci_scripts(workflow_texts):
    found = set()
    for text in workflow_texts:
        for line in text.splitlines():
            m = STEP.search(line)
            if m and ("run:" in line or line.lstrip().startswith(("python3", "bash"))):
                found.add(m.group(1))
    return found


def doc_gate_scripts(text):
    return set(m.group(1) for m in re.finditer(r'^\s*run\s+"[^"]*"\s+(?:python3|bash)\s+([\w./-]+\.(?:py|sh))', text, re.M))


def judge(ci, gated, exempt):
    errs = []
    for s in sorted(ci):
        if s in ("scripts/doc-gates.sh",) or s.startswith("conformance/run"):
            continue  # doc-gates itself; the four-way suite is an engine job by definition
        if s not in gated and s not in exempt:
            errs.append(f"{s} runs in CI but is neither a doc-gates.sh row nor exempt (with a reason) in {pathlib.Path(__file__).name}")
    for s in sorted(exempt):
        if s not in ci:
            errs.append(f"exemption {s} is STALE: no workflow runs it any more")
        elif s in gated:
            errs.append(f"exemption {s} is STALE: doc-gates.sh runs it now")
    return errs


def main():
    try:
        wfs = [p.read_text(encoding="utf-8") for p in sorted((ROOT / ".github/workflows").glob("*.yml"))]
        gates = (ROOT / "scripts/doc-gates.sh").read_text(encoding="utf-8")
    except OSError as e:
        print(f"ci-doc-gate-coverage: cannot read inputs: {e}", file=sys.stderr)
        return 2
    ci = ci_scripts(wfs)
    gated = doc_gate_scripts(gates)
    if not ci or not gated:
        print(f"ci-doc-gate-coverage: VACUOUS — parsed {len(ci)} CI script(s) and {len(gated)} doc-gates row(s); "
              f"one side is empty, so a clean result would mean nothing", file=sys.stderr)
        return 2
    errs = judge(ci, gated, EXEMPT)
    if errs:
        print("ci-doc-gate-coverage: FAIL")
        for e in errs:
            print("  " + e)
        return 1
    print(f"ci-doc-gate-coverage: OK ({len(ci)} CI script(s); {len(gated)} gated in doc-gates, {len(EXEMPT)} exempt)")
    return 0


def selftest():
    wf = "    steps:\n      - run: python3 scripts/seeded_new_gate.py\n      - run: python3 scripts/check_agents_drift.py\n"
    gates = 'run "x"  python3 scripts/check_agents_drift.py\n'
    bad = []
    if judge(ci_scripts([wf]), doc_gate_scripts(gates), {}) != [
            "scripts/seeded_new_gate.py runs in CI but is neither a doc-gates.sh row nor exempt (with a reason) in ci-doc-gate-coverage.py"]:
        bad.append("an uncovered CI script was not reported (or a covered one was)")
    if not judge(ci_scripts([wf]), doc_gate_scripts(gates), {"scripts/seeded_new_gate.py": "r", "scripts/gone.py": "r"}):
        bad.append("a stale exemption was not reported")
    if judge(ci_scripts([wf]), doc_gate_scripts(gates), {"scripts/seeded_new_gate.py": "r"}):
        bad.append("an exempted script was reported as uncovered")
    if bad:
        print("ci-doc-gate-coverage selftest: FAIL")
        for b in bad:
            print("  " + b)
        return 1
    print("ci-doc-gate-coverage selftest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else main())
