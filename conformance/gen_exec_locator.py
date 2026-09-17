#!/usr/bin/env python3
"""
PART 91 — THE EXEC-LOCATOR differential (FOUR-WAY, SPEC §2 ⟨0.37⟩).

PART 88 pins this property for `Fs`: a call's LOCATOR is read from the position that NAMES it, whether
that position is an ARGUMENT or the RECEIVER, and a benign sibling literal must not certify a call whose
own locator was never captured. **Nothing pinned the same property for `Exec`, and that is why two engines
shipped the identical hole independently.**

  SOUNDNESS R464 (java, 2026-09-17)  a benign `new ProcessBuilder("git")` literal certified
                                     `System.load(argv[0])` — `allow Exec git` exit 0. SIX spellings.
  SOUNDNESS R460 (rust, 2026-09-17)  a spawn whose `Command` arrives as a RECEIVER has no `Command::new`
                                     in the function for the guard to fire on — `allow Exec git` exit 0
                                     over `fn go(cmd: &mut Command) { Command::new("git").status();
                                     cmd.spawn(); }`.

Both were found in the same overnight wave, by different agents, neither aware of the other. That is the
argument for this part existing: a cross-engine row is what turns "we fixed it in two engines" into
"the third and fourth cannot ship it". java's report named the gap explicitly — *"PART 88's arms and the
⟨0.29⟩ clause do not currently express an Exec-locator arm at all, so nothing cross-engine pins R464"*.

WHY THE BENIGN SIBLING IS LOAD-BEARING IN EVERY ARM. A spawn with no readable literal is ALREADY
uncertifiable — AS-EFF-008 refuses an `allow` over a function with no visible locator, so a naked
`cmd.spawn()` fails on its own and proves nothing. The hole only opens when ONE unrelated readable
literal populates `cmds` and makes the whole surface read complete. That is the same shape as R395
(`id_rsa` certified by a benign sibling) and as swift's R387, and it is why each defect arm below pairs a
benign literal with a caller-chosen spawn rather than testing the spawn alone.

THE CONTROL ARMS ARE NOT OPTIONAL. Widening a masking guard is where this family turns a silence into a
fabrication — measured repeatedly, and R460's own A/B priced the over-mask rather than carving it out
(101 of 217 triggers were `Result`/`Option` combinators mis-typed as `Command`). So:

  e3determined  a spawn whose program IS a determined literal must STILL certify. If this reddens, the
                fix has made ordinary code uncertifiable — R416's shape, which PART 88's a4local caught on
                its first execution.
  e4nonexec     a benign Exec literal beside a call that spawns NOTHING must not be marked. This is the
                arm that fails if an engine starts marking on "the function mentions Exec" rather than on
                "this call's own locator was not captured".

ENGINE EXPRESSIBILITY IS DECLARED PER ARM, NOT ASSUMED. `e2recv` needs a language where the spawn handle
is a value that can arrive as a parameter — rust `&mut Command`, java `ProcessBuilder`, swift `Process`.
ts's `child_process.spawn(cmd, args)` takes the program as an ARGUMENT and has no receiver form, so ts is
declared inexpressible on that arm rather than silently skipped.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_masking as gm  # noqa: E402  -- import-safe: its work is behind a __main__ guard

ALLOWED = "git"
EFF = {"id": "execloc"}
FAULT = os.environ.get("CANDOR_PROBE_FAULT")

# arm -> (expected gate rc under `allow Exec git`, what it proves, engines that cannot express it)
ARMS = [
    ("e1arg",        1, "an ARGUMENT-form spawn's program is its locator (R464)",        ()),
    ("e2recv",       1, "a RECEIVER-form spawn's program is its locator too (R460)",     ("ts",)),
    ("e3determined", 0, "CONTROL: a determined program still certifies",                 ()),
    ("e4nonexec",    0, "CONTROL: a benign literal beside no spawn is not marked",       ()),
]

# An expectation keyed by (arm, engine) — NEVER by arm alone, because the whole finding is that one
# engine closed the ARGUMENT form and not the RECEIVER form. A PASSING xfail is a FAILURE here: it is the
# only thing in the suite that notices an expectation which has quietly become true.
# EMPTY, and it was not empty when this part landed. `("e2recv","java")` was declared here for
# SOUNDNESS R477 — R464 closed the ARGUMENT form and left the RECEIVER form open — and PART 91 found
# that on its FIRST EXECUTION. Retired 2026-09-17 in the same commit as candor-java `5440749`, which
# is the discipline: a PASSING xfail is a FAILURE here, so an expectation that has become true is
# reported rather than quietly carried. Keep the mechanism now the dict is empty — the next
# engine-specific gap in this family will land exactly the same way.
XFAIL = {}

BODIES = {
    "rust": {
        # e1arg: the program is a caller-supplied ARGUMENT; the benign literal is a sibling.
        "e1arg":        'use std::process::Command;\npub fn f(p:&str){{ let _=Command::new("%s").status(); let _=Command::new(p).status(); }}' % ALLOWED,
        # e2recv: R460 exactly — the Command arrives as a RECEIVER, so no Command::new names it here.
        "e2recv":       'use std::process::Command;\npub fn f(c:&mut Command){{ let _=Command::new("%s").status(); let _=c.spawn(); }}' % ALLOWED,
        "e3determined": 'use std::process::Command;\npub fn f(){{ let _=Command::new("%s").status(); }}' % ALLOWED,
        "e4nonexec":    'use std::process::Command;\npub fn f(n:usize)->usize{{ let _=Command::new("%s").status(); n+1 }}' % ALLOWED,
    },
    # BODY ONLY — `_java_tree` wraps this in `package q; public class E { … }`.
    "java": {
        "e1arg":        '  public static void f(String p) throws Exception {{ new ProcessBuilder("%s").start(); new ProcessBuilder(p).start(); }}' % ALLOWED,
        "e2recv":       '  public static void f(ProcessBuilder b) throws Exception {{ new ProcessBuilder("%s").start(); b.start(); }}' % ALLOWED,
        "e3determined": '  public static void f() throws Exception {{ new ProcessBuilder("%s").start(); }}' % ALLOWED,
        "e4nonexec":    '  public static int f(int n) throws Exception {{ new ProcessBuilder("%s").start(); return n + 1; }}' % ALLOWED,
    },
    # BODY ONLY — `_ts_tree` prepends the std imports, so use `cp` for child_process.
    "ts": {
        "e1arg":        'export function f(p:string):void{{ cp.spawnSync("%s",[]); cp.spawnSync(p,[]); }}' % ALLOWED,
        "e3determined": 'export function f():void{{ cp.spawnSync("%s",[]); }}' % ALLOWED,
        "e4nonexec":    'export function f(n:number):number{{ cp.spawnSync("%s",[]); return n+1; }}' % ALLOWED,
    },
    "swift": {
        "e1arg":        'import Foundation\npublic func f(_ p:String) throws {{ let a=Process(); a.launchPath="/usr/bin/%s"; try? a.run(); let b=Process(); b.launchPath=p; try? b.run() }}' % ALLOWED,
        "e2recv":       'import Foundation\npublic func f(_ q:Process) throws {{ let a=Process(); a.launchPath="/usr/bin/%s"; try? a.run(); try? q.run() }}' % ALLOWED,
        "e3determined": 'import Foundation\npublic func f() throws {{ let a=Process(); a.launchPath="/usr/bin/%s"; try? a.run() }}' % ALLOWED,
        "e4nonexec":    'import Foundation\npublic func f(_ n:Int) throws -> Int {{ let a=Process(); a.launchPath="/usr/bin/%s"; try? a.run(); return n+1 }}' % ALLOWED,
    },
}


def _swift_tree(d, body):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "cases.swift"), "w") as f:
        f.write("// GENERATED by gen_exec_locator.py -- do not edit.\n" + body.format() + "\n")


def render(ws):
    """One tree per (engine, arm). Arms an engine cannot express are simply not written."""
    for arm, _rc, _why, skip in ARMS:
        cell = f"{EFF['id']}_{arm}"
        # THE FAULT is at the FIXTURE, not the comparison — it writes e3determined's body (a fully
        # determined spawn every engine correctly certifies) into e2recv's cell, so the arm that MUST
        # fail now cannot. Inverting an expected value would only prove the comparison can subtract;
        # this proves the row's INPUT reached the engine.
        src = "e3determined" if (FAULT and arm == "e2recv") else arm
        if "rust" not in skip:
            gm._rust_tree(os.path.join(ws, "rust", cell), BODIES["rust"][src])
        if "java" not in skip:
            gm._java_tree(os.path.join(ws, "java", cell), BODIES["java"][src])
        if "ts" not in skip and src in BODIES["ts"]:
            gm._ts_tree(os.path.join(ws, "ts", cell), BODIES["ts"][src])
        if "swift" not in skip:
            _swift_tree(os.path.join(ws, "swift", cell), BODIES["swift"][src])


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-execlocator-")
    pol = os.path.join(ws, "allow.policy")
    with open(pol, "w") as f:
        f.write(f"allow Exec {ALLOWED}\n")

    print("=" * 100)
    print("EXEC-LOCATOR differential ⟨0.37⟩ — a spawn's program is its locator, however it arrives")
    print(f"  policy  : allow Exec {ALLOWED}")
    print("  property: e1arg/e2recv must FAIL (the program is the call's own locator and was not")
    print("            captured — a benign sibling literal must not certify it);")
    print("            e3determined/e4nonexec must PASS (determined still certifies; no spawn, no mark)")
    print("=" * 100)

    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the e2recv cell is being written with the e3determined "
              "body (a fully determined spawn). The arm that MUST fail now cannot, and this run's verdict "
              "MUST go red. A clean run must never print this line.")
    render(ws)

    available = []
    for eng in gm.ENGINES:
        eng.prepare(ws)
        if eng.ok:
            available.append(eng)
        else:
            print(f"  {eng.name:6s} not available — skipped LOUDLY: {eng.err}")
    if not available:
        print("EXEC-LOCATOR: no engine available — NOT a pass")
        return 2

    fails, inexpressible, xfail_passed = [], [], []
    for arm, want, why, skip in ARMS:
        for eng in available:
            if eng.name in skip or (eng.name == "ts" and arm not in BODIES["ts"]):
                inexpressible.append((arm, eng.name)); continue
            got = eng.gate(ws, EFF, arm, pol)
            exp = XFAIL.get((arm, eng.name))
            if got == want:
                if exp:
                    print(f"  XFAIL ARM PASSED  {arm:13s} {eng.name:6s} — expectation is STALE: {exp[:60]}…")
                    xfail_passed.append((arm, eng.name))
                else:
                    print(f"  OK    {arm:13s} {eng.name:6s} rc={got}  {why}")
            elif exp:
                print(f"  xfail {arm:13s} {eng.name:6s} rc={got} (want {want}) — {exp[:70]}…")
            else:
                print(f"  FAIL  {arm:13s} {eng.name:6s} rc={got}, want {want}  {why}")
                fails.append((arm, eng.name, got, want))

    for arm, name in inexpressible:
        print(f"  n/a   {arm:13s} {name:6s} — declared inexpressible, not silently skipped")

    if xfail_passed:
        print(f"\nEXEC-LOCATOR: {len(xfail_passed)} xfail arm(s) PASSED — an expectation that has become "
              "true is a FAILURE here; retire it from XFAIL in the same commit as the engine fix.")
        return 1
    if fails:
        print(f"\nEXEC-LOCATOR: {len(fails)} cell(s) wrong — see SOUNDNESS R460 (rust) / R464 (java)")
        return 1
    print("\nEXEC-LOCATOR: OK — every engine reads a spawn's program from wherever it arrives, and neither "
          "refuses a determined one nor marks a function that spawns nothing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
