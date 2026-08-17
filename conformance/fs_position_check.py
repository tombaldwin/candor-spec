#!/usr/bin/env python3
"""
PART 51 — AN `Fs` PATH LITERAL IS READ FROM THE PATH POSITION, NEVER FROM ANYWHERE IN THE CALL (SPEC §4).

The rule already exists in this family, twice, for the other two locator-bearing effects. candor-ts spells
it out at the `Exec` head: *"The head MUST be argv[0], NOT any literal arg: `spawn(toolVar, "curl")` names
no static program, so its trailing literal must not fabricate Net"* — and the comment one block down says
that discipline was "generalized from Exec to Net". It stopped there. `Fs` went on taking the first string
literal ANYWHERE in the call and publishing it as the path.

MEASURED, on the ⟨0.29⟩ pre-release panel:

    fs.writeFileSync(userPath, "/tmp/lit")        // the literal is the BYTES, not the destination
    policy: allow Fs /tmp/lit

    candor-rust / candor-ts   → paths: ["/tmp/lit"], `policy ✓`, exit 0     ← the destination is unknown
    candor-java / candor-swift → AS-EFF-008, exit 1                          ← identical code

That is the cardinal sin in its exact shape: a green gate certifying a write to a runtime-controlled
destination, with the operator's own allow-rule as the thing that lets it through. Worse than a missing
rule, because the report names a path that was never written to.

THIS ROW HAS FOUR FUNCTIONS AND ALL FOUR ARE LOAD-BEARING:

  exfil(p)    write(runtime, "/tmp/lit")           the defect: a literal in a NON-path position
  okLit()     write("/tmp/lit", …)                 THE OVER-CHARGE CONTROL
  twoPath(d)  copy("/tmp/lit", runtime)            a literal in ONE path position of TWO
  twoLit()    copy("/tmp/lit", "/tmp/dst")         BOTH positions literal — publish BOTH

`twoLit` is the second defect this row caught, and it was found by GENERATING a case per `fs` export
rather than by re-reading the fix: candor-rust and candor-ts published position 0, saw both positions were
literal, and therefore called the surface COMPLETE — so `allow Fs /tmp/lit` answered `policy ✓` at exit 0
over a copy INTO `/tmp/dst`. A false all-clear built out of two correct-looking halves: the right
completeness verdict attached to half a surface. candor-java and candor-swift published both all along.

`okLit` is why the row cannot be satisfied by an engine that simply stopped reading literals: charge
everything and `exfil`/`twoPath` pass while the tool becomes useless, which is the failure mode every
fabrication-fix in this project has had to be measured against. `twoPath` is why "is there a literal at
position 0" is not the property — `copyFile("/safe", userPath)` has one and still writes somewhere nobody
can see, so the question is whether EVERY path position is a literal.

THE VERDICT IS THE TEETH; the per-function fields are the diagnosis. A row that only read `paths` would
pass on an engine that publishes the right field and gates on the wrong one.
"""
import json
import sys


def main():
    if len(sys.argv) != 5:
        print("usage: fs_position_check.py <engine> <report> <gate-rc> <gate-output>")
        return 2
    engine, report_path, rc, out = sys.argv[1].strip(), sys.argv[2], sys.argv[3], sys.argv[4]

    def fail(msg):
        print(f"  {engine:6} -> DIVERGE  ({msg})")
        return 1

    try:
        with open(report_path) as f:
            rep = json.load(f)
    except Exception as e:                                    # noqa: BLE001 — the diagnosis IS the message
        return fail(f"the report is unreadable ({report_path}: {e}) — the fixture did not scan, and every "
                    "assertion below would be about a file that is not there")

    # Names are spelled per engine (`x.A.exfil`, `src.a.exfil`, `a::exfil`, `exfil`), so match on the leaf.
    def unit(leaf):
        hits = [f for f in rep.get("functions", [])
                if str(f.get("fn", "")).replace("::", ".").split(".")[-1] == leaf]
        return hits[0] if len(hits) == 1 else None

    fns = {leaf: unit(leaf) for leaf in ("exfil", "okLit", "twoPath", "twoLit")}
    missing = [k for k, v in fns.items() if v is None]
    if missing:
        return fail(f"the report does not name exactly one unit for {missing} — the fixture did not "
                    "analyze, so a green result below would mean nothing was measured")

    def paths(f):
        return set(f.get("paths") or [])

    def inc(f):
        return set(f.get("incomplete") or [])

    # (1) THE DEFECT. The literal sits in the CONTENT position; publishing it as a path is a fabricated
    # destination, and the engine must instead say it could not see one.
    if "/tmp/lit" in paths(fns["exfil"]):
        return fail("`exfil` publishes `/tmp/lit` as a path, but that literal is the BYTES BEING WRITTEN "
                    "— the destination is a parameter; `allow Fs /tmp/lit` now certifies a write nobody "
                    "can see")
    if "Fs" not in inc(fns["exfil"]):
        return fail("`exfil` writes to a runtime path and does not mark `incomplete: [Fs]` — an absent "
                    "`paths` reads as 'reaches no path', which is the overload ⟨0.29⟩ removed")

    # (2) THE OVER-CHARGE CONTROL. Without this the row is satisfied by an engine that stopped reading
    # `Fs` literals at all, which passes every assertion above and answers nothing for a user.
    if "/tmp/lit" not in paths(fns["okLit"]):
        return fail("`okLit` writes to a LITERAL path and the engine did not publish it — the fix has "
                    "been made by giving up the surface rather than by reading the right position")
    if inc(fns["okLit"]):
        return fail(f"`okLit` has a fully-literal path and is marked incomplete {sorted(inc(fns['okLit']))} "
                    "— every certifiable write in a real tree would now be charged")

    # (3) ONE literal path position out of TWO is not a complete surface.
    if "Fs" not in inc(fns["twoPath"]):
        return fail("`twoPath` copies FROM a literal TO a runtime path and is not marked incomplete — a "
                    "position-0 literal certified a destination that was never visible")

    # (4) BOTH literal ⇒ BOTH published. Completeness and the surface must be computed over the same set
    # of positions; a `complete` verdict covering positions the report never lists is the false all-clear.
    if paths(fns["twoLit"]) != {"/tmp/lit", "/tmp/dst"}:
        return fail(f"`twoLit` copies between TWO literal paths and publishes {sorted(paths(fns['twoLit']))} "
                    "— the unpublished position is certified by any rule that allows the published one")
    if inc(fns["twoLit"]):
        return fail("`twoLit` has literals in BOTH path positions and is still marked incomplete — the "
                    "surface is entirely visible, so this charges a call nothing is hidden in")

    # (5) THE VERDICT. Fields an engine publishes but does not gate on are a report nobody is protected by.
    if rc != "1":
        return fail(f"the gate answered exit {rc} over `allow Fs /tmp/lit`, but three of these four units "
                    "reach an Fs destination outside the allowlist — a green here IS the false all-clear")
    for leaf in ("exfil", "twoPath", "twoLit"):
        if leaf not in out:
            return fail(f"the violation output never names `{leaf}` — the exit code is right for some "
                        "other reason, and this row would survive the defect it exists to catch")
    if "okLit" in out:
        return fail("the violation output names `okLit`, whose path is a literal the policy ALLOWS — the "
                    "exit 1 above is an over-charge, not this defect")

    print(f"  {engine:6} -> OK        (the path POSITION decides: a content literal fabricates nothing, a "
          "half-literal two-path op is incomplete, BOTH literal positions are published, and a "
          "fully-literal write still certifies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
