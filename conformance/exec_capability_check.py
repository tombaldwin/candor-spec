#!/usr/bin/env python3
"""
PART 66 — `Exec` REACHES THE SUBPROCESS CAPABILITY, NOT ONLY THE LAUNCH (SPEC §1 ⟨0.32⟩).

An invocation object — `std::process::Command`, `new ProcessBuilder(…)`, `Process()` — carries its own
payload (program, argv, environment) and travels fully armed. So the function that ASSEMBLES one holds
the capability just as surely as the one that calls `spawn`, and splitting build from launch across two
functions must not make the builder invisible.

MEASURED, on candor-java, which was the family's lone launch-verb ALLOWLIST (`start`/`startPipeline`/
`Runtime.exec`):

    public ProcessBuilder arm(String[] argv) { return new ProcessBuilder(argv); }
    public void configure(ProcessBuilder pb) { pb.directory(new File("/")); }
    policy: deny Exec

    -> exit 0, `no violations`, and `arm` reporting `inferred: []`

A method that assembles a fully-armed invocation out of caller-supplied argv and hands it back was
certified clean. That is the allowlist failure in its exact shape: not a wrong rule, an ABSENT one, and
absent silently — every verb nobody enumerated reads as pure.

THE CELLS, and why each is load-bearing:

  armed       build a Command/ProcessBuilder/Process and RETURN it       the defect, construction half
  configured  set argv/cwd/redirect on a RECEIVED builder                the defect, configuration half
  launched    spawn/start/run on a RECEIVED builder                      pins the pre-existing rule,
                                                                        cross-engine (candor-rust fe62b49)
  readBack    a read-back getter ONLY (`get_program`, `command()`, …)    THE OVER-CHARGE CONTROL
  lookalike   a PROJECT-LOCAL type that merely shares the name           THE OVER-CHARGE CONTROL

WHY THE CONTROLS DECIDE THIS PART. A rule that charges the whole invocation type is trivially satisfied
by charging more: an engine that answered `Exec` for every method on every type would pass all three
positive cells and be useless. `readBack` and `lookalike` are what that engine fails. They are also the
boundary of the ruling itself — it is specific to INVOCATION objects, and option-builders for other
effects (`OpenOptions`, an HTTP request builder) stay pure because their resource arrives at the terminal
verb, which is charged at its own call site.

VACUITY: A `noExec` CELL IS NOT "ABSENT FROM THE REPORT". Every engine here omits pure functions from
`functions`, so a misspelled control name would read as "not Exec" and PASS while asking nothing — the
PART 37 (e) failure, where a row scored a pass on a name that was in no fixture. So each control function
carries a CLOCK MARKER (`Instant::now` / `System.nanoTime` / `Date.now` / `Date()`), and this checker
REQUIRES a `noExec` cell to be PRESENT in the report with a non-empty effect set that excludes `Exec`.
Absent is a FAIL, and it says so: the fixture did not reach the engine.

    exec_capability_check.py <engine> <report> <fn>=Exec|noExec …
"""
import json
import sys


def resolve(fns, name):
    """The report entry for `name`, matched exactly or by the engines' qualified spellings
    (`x.A.armed`, `local::lookalike`, `src.a.readBack`, `S#armed`). Returns None if unmatched —
    which for a noExec cell is a FAILURE, never a silent pass."""
    hit = [f for f in fns
           if f.get("fn") == name
           or any(f.get("fn", "").endswith(sep + name) for sep in (".", "::", "#", "/"))]
    return hit[0] if len(hit) == 1 else (hit[0] if hit else None)


def main():
    if len(sys.argv) < 4:
        print("usage: exec_capability_check.py <engine> <report> <fn>=Exec|noExec …")
        return 2
    engine, report_path, cells = sys.argv[1].strip(), sys.argv[2], sys.argv[3:]

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    try:
        with open(report_path) as f:
            doc = json.load(f)
    except Exception as e:                                    # a missing/truncated report is a FAILURE,
        return fail(f"cannot read {report_path}: {e}")        # never a quiet skip

    fns = doc["functions"] if isinstance(doc, dict) else doc
    verdict = []
    for cell in cells:
        name, _, want = cell.partition("=")
        entry = resolve(fns, name)
        got = sorted(entry.get("inferred") or []) if entry else None
        if want == "Exec":
            if not entry or "Exec" not in got:
                return fail(f"{name} must be Exec — the invocation it holds is fully armed; got "
                            f"{got if entry else 'NOT IN THE REPORT'}")
            verdict.append(f"{name}=Exec")
        elif want == "noExec":
            if entry is None:
                return fail(f"{name} is ABSENT from the report — an over-charge control that was never "
                            f"analyzed asks nothing. Its Clock marker should have put it there; the "
                            f"fixture did not reach this engine")
            if not got:
                return fail(f"{name} carries NO effects at all — its Clock marker is missing, so the "
                            f"absence of Exec here is not evidence")
            if "Exec" in got:
                return fail(f"{name} is charged Exec — it only reads back stored state / uses a "
                            f"project-local type of the same name; got {got}")
            verdict.append(f"{name}={'+'.join(got)}")
        else:
            return fail(f"unknown want `{want}` in cell `{cell}`")
    print(f"  {engine:6} -> OK       " + "  ".join(verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
