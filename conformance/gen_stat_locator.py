#!/usr/bin/env python3
"""
THE STAT-LOCATOR DIFFERENTIAL — ⟨0.37⟩'s four arms, cross-engine.

A call's LOCATOR may arrive as an ARGUMENT or as the RECEIVER, and both are the call's own. A path-stat
invoked on its path — `p.exists()`, `f.exists()`, `url.checkResourceIsReachable()` — names its destination
exactly as `fs::metadata(p)` does. An engine silent on the receiver form lets a benign sibling literal
certify a caller-controlled path: `allow Fs /tmp/benign` exits 0 and the run prints "nothing hidden".

WHY FOUR ARMS AND NOT ONE. A defect arm alone is the shape SOUNDNESS R411 was filed against — conformance
PART 12 and gen_masking.py are BOTH green on a class that is live-broken, because each pins only the
spelling the engines already handle. So this part carries its over-charge controls as first-class arms:

  a1arg    ARGUMENT-form stat beside a benign allowed literal      -> must FAIL   (AS-EFF-008)
  a2recv   RECEIVER-form stat beside the same                      -> must FAIL   (ts: INEXPRESSIBLE)
  a3handle a HANDLE use-verb beside the same                       -> must PASS   (no locator of its own)
  a4local  a LOCAL-BOUND literal path                              -> must PASS   (determined is determined)

a3 stops a fix reintroducing rust's measured 544-row Net inversion. a4 stops "Captured" being read as a
SYNTACTIC window: a locator whose value is statically determined is determined however it reaches the call.

MEASURED BEFORE THIS FILE EXISTED, on the shipped 0.36.2 engines (SOUNDNESS R414, R416):
    arm    rust        java        ts              swift
    a1arg  marks       SILENT      marks           marks
    a2recv SILENT      SILENT      inexpressible   SILENT
    a3handle ok        ok          ok              ok
    a4local OVER-MASK  ok          OVER-MASK       ok
So this part is EXPECTED RED until R409/R414/R416 land. It is written and held with the ⟨0.37⟩ clause
draft (conformance/gate/R414-STAT-RULING-DRAFT.md) rather than wired into run.sh, because a suite with no
xfail mechanism would red `main` on a defect nobody has fixed yet.

REUSES gen_masking.ENGINES rather than copying the four Engine classes. Five generators already carry
their own copies (gen_completeness, gen_fs_kind, gen_masking, gen_netclass, gen_policy_match) with zero
imports between them — R288's fifteen-`ab.py` shape, inside the conformance suite. This file does not
become the sixth.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_masking as gm  # noqa: E402  -- import-safe: its work is behind a __main__ guard

ALLOWED = "/tmp/benign"
EFF = {"id": "stat"}

# arm -> (expected gate rc, what it proves, engines that cannot express it)
ARMS = [
    ("a1arg",    1, "an ARGUMENT-form stat's path is its locator",              ()),
    ("a2recv",   1, "a RECEIVER-form stat's path is its locator too",           ("ts",)),
    ("a3handle", 0, "CONTROL: a handle use-verb has no locator of its own",     ()),
    ("a4local",  0, "CONTROL: a determined locator stays determined",           ()),
]

BODIES = {
    "rust": {
        "a1arg":    'use std::fs;\nuse std::path::Path;\npub fn f(p:&Path)->std::io::Result<()>{{ fs::write("%s",b"x")?; let _=fs::metadata(p)?; Ok(()) }}' % ALLOWED,
        "a2recv":   'use std::fs;\nuse std::path::Path;\npub fn f(p:&Path)->std::io::Result<()>{{ fs::write("%s",b"x")?; let _=p.exists(); Ok(()) }}' % ALLOWED,
        "a3handle": 'use std::fs;\nuse std::io::Read;\npub fn f(h:&mut std::fs::File)->std::io::Result<()>{{ fs::write("%s",b"x")?; let mut s=String::new(); h.read_to_string(&mut s)?; Ok(()) }}' % ALLOWED,
        "a4local":  'use std::fs;\nuse std::path::Path;\npub fn f()->std::io::Result<()>{{ let p=Path::new("%s"); fs::write(p,b"x") }}' % ALLOWED,
    },
    # BODY ONLY — `_java_tree` wraps this in `package q; public class E { … }`, so no imports and no
    # class declaration; everything is fully qualified.
    "java": {
        "a1arg":    '  public static void f(java.nio.file.Path p) throws Exception {{ java.nio.file.Files.write(java.nio.file.Paths.get("%s"), new byte[0]); java.nio.file.Files.exists(p); }}' % ALLOWED,
        "a2recv":   '  public static void f(java.io.File h) throws Exception {{ java.nio.file.Files.write(java.nio.file.Paths.get("%s"), new byte[0]); h.exists(); }}' % ALLOWED,
        "a3handle": '  public static void f(java.io.InputStream in) throws Exception {{ java.nio.file.Files.write(java.nio.file.Paths.get("%s"), new byte[0]); in.read(); }}' % ALLOWED,
        "a4local":  '  public static void f() throws Exception {{ java.nio.file.Path p = java.nio.file.Paths.get("%s"); java.nio.file.Files.write(p, new byte[0]); }}' % ALLOWED,
    },
    # BODY ONLY — `_ts_tree` prepends `import * as fsm from "node:fs"` (and net/cp/sqlite), so use `fsm`.
    "ts": {
        "a1arg":    'export function f(p:string):void{{ fsm.writeFileSync("%s",""); fsm.existsSync(p); }}' % ALLOWED,
        "a3handle": 'export function f(fd:number):void{{ fsm.writeFileSync("%s",""); fsm.readSync(fd,Buffer.alloc(1),0,1,null); }}' % ALLOWED,
        "a4local":  'export function f():void{{ const p="%s"; fsm.writeFileSync(p,""); }}' % ALLOWED,
    },
    "swift": {
        "a1arg":    'import Foundation\npublic func f(_ p:String) throws {{ try "x".write(toFile:"%s",atomically:true,encoding:.utf8); _ = FileManager.default.fileExists(atPath:p) }}' % ALLOWED,
        "a2recv":   'import Foundation\npublic func f(_ u:URL) throws {{ try "x".write(toFile:"%s",atomically:true,encoding:.utf8); _ = try? u.checkResourceIsReachable() }}' % ALLOWED,
        "a3handle": 'import Foundation\npublic func f(_ h:FileHandle) throws {{ try "x".write(toFile:"%s",atomically:true,encoding:.utf8); _ = h.availableData }}' % ALLOWED,
        "a4local":  'import Foundation\npublic func f() throws {{ let p="%s"; try "x".write(toFile:p,atomically:true,encoding:.utf8) }}' % ALLOWED,
    },
}


def _swift_tree(d, body):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "cases.swift"), "w") as f:
        # .format() for the same reason gen_masking's writers use it: the bodies double their braces
        f.write("// GENERATED by gen_stat_locator.py -- do not edit.\n" + body.format() + "\n")


def render(ws):
    """One tree per (engine, arm). Arms an engine cannot express are simply not written."""
    for arm, _rc, _why, skip in ARMS:
        cell = f"{EFF['id']}_{arm}"
        if "rust" not in skip:
            gm._rust_tree(os.path.join(ws, "rust", cell), BODIES["rust"][arm])
        if "java" not in skip:
            gm._java_tree(os.path.join(ws, "java", cell), BODIES["java"][arm])
        if "ts" not in skip and arm in BODIES["ts"]:
            gm._ts_tree(os.path.join(ws, "ts", cell), BODIES["ts"][arm])
        if "swift" not in skip:
            _swift_tree(os.path.join(ws, "swift", cell), BODIES["swift"][arm])


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-statlocator-")
    pol = os.path.join(ws, "allow.policy")
    with open(pol, "w") as f:
        f.write(f"allow Fs {ALLOWED}\n")

    print("=" * 100)
    print("STAT-LOCATOR differential ⟨0.37⟩ — a locator may arrive as an ARGUMENT or as the RECEIVER")
    print(f"  policy  : allow Fs {ALLOWED}")
    print("  property: a1arg/a2recv must FAIL (the locator is the call's own and was not captured);")
    print("            a3handle/a4local must PASS (no locator of its own / determined is determined)")
    print("=" * 100)

    render(ws)
    available = []
    for eng in gm.ENGINES:
        eng.prepare(ws)
        if eng.ok:
            available.append(eng)
        else:
            print(f"  {eng.name:6s} not available — skipped LOUDLY: {eng.err}")
    if not available:
        print("STAT-LOCATOR: no engine available"); return 2

    fails, inexpressible = [], []
    print(f"\n{'arm':10s} " + " ".join(f"{e.name:14s}" for e in available))
    print("-" * 78)
    for arm, want, why, skip in ARMS:
        row = f"{arm:10s} "
        for eng in available:
            if eng.name in skip:
                row += f"{'—  (n/a)':14s} "
                inexpressible.append((arm, eng.name))
                continue
            rc = eng.gate(ws, EFF, arm, pol)
            ok = (rc != 0) if want else (rc == 0)
            row += f"{('rc=' + str(rc) + (' ok' if ok else ' ✘')):14s} "
            if not ok:
                fails.append((arm, eng.name, rc, why))
        print(row)

    print()
    for arm, eng, rc, why in fails:
        want = dict((a, w) for a, w, _, _ in ARMS)[arm]
        verb = "CERTIFIED a locator it never captured" if want else "REFUSED a call it should certify"
        print(f"  ✘ {eng}/{arm}: {verb} (rc={rc}) — {why}")
    for arm, eng in inexpressible:
        print(f"  •   {eng}/{arm}: INEXPRESSIBLE in this language, declared — not a gap")
    if fails:
        print(f"\nSTAT-LOCATOR: {len(fails)} cell(s) wrong — see SOUNDNESS R409/R414/R416")
        return 1
    print("\nSTAT-LOCATOR: OK — every engine reads the locator from wherever it arrives, and neither "
          "over-masks a determined one nor marks a handle use-verb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
