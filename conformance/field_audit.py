#!/usr/bin/env python3
"""
WHICH SPEC §2 FIELDS DOES EACH ENGINE ACTUALLY EMIT?

A field can be in this document, in an engine's wire model, and emitted by nobody. `fs` was: spec'd for a
long time, emitted by candor-java alone, absent from candor-swift and candor-ts entirely, and present in
candor-rust's `Report` struct with `fs: Vec::new()` hardcoded at the construction site — never populated,
which is worse than absent because a present-but-always-empty field asserts "kind undetermined" on every
function forever while wearing a schema that implies support.

Nobody noticed for as long as the field existed, because §2's omit-rather-than-guess rule made every
individual omission defensible. **A field whose absence is always excusable is a field nobody checks.**

So this checks. One fixture per language exercising the same effects, then a table of which §2 fields each
engine emitted. It is a REPORT, not a gate: an engine legitimately omits a field its fixture never
provoked, and turning that into a failure would be the absence-is-a-claim error one level up. Read the
table and ask why a column is empty.

WHAT IT FOUND ON ITS FIRST RUN (2026-08-04): nothing new. Worth recording, because it means the `fs` gap
was NOT part of a pattern of unimplemented fields — it was specifically a field nobody had pinned in
conformance. That is a different problem with a different fix, and knowing which one you have matters.

The fixture includes a PEER CALL (`calls_a_peer` → `reads`) deliberately: without one, `calls` is
legitimately absent everywhere and the row is untrustworthy rather than informative. A row that cannot
distinguish "not emitted" from "not provoked" is exactly the ambiguity this whole audit is about.

KNOWN LIMIT, stated rather than implied: the fixture exercises Fs/Exec/Unknown, a dispatch and a peer call.
It does NOT provoke `hosts` (needs a literal network endpoint) or `tables` (needs SQL), so those rows say
nothing at all.
A clean run here is a partial bill of health, never a full one.

    python3 field_audit.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def envdir(var, default_rel):
    return os.environ.get(var, os.path.normpath(os.path.join(HERE, default_rel)))


CANDOR       = envdir("CANDOR",       "../../candor-rust")
CANDOR_JAVA  = envdir("CANDOR_JAVA",  "../../candor-java")
CANDOR_TS    = envdir("CANDOR_TS",    "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")

# SPEC §2 optional per-function fields, and the envelope-level ones.
FN_FIELDS  = ["calls", "cmds", "fs", "hosts", "paths", "tables", "unknownWhy", "netClass", "invisible"]
ENV_FIELDS = ["coverage", "analyzed", "unanalyzed", "typeSurface", "extensions", "resolves"]

RUST = '''use std::fs;
use std::process::Command;
pub fn reads() { let _ = fs::read_to_string("/tmp/a"); }
pub fn writes() { let _ = fs::write("/tmp/b", "x"); }
pub fn spawns() { let _ = Command::new("curl").arg("-s").status(); }
pub fn dispatches(cb: &dyn Fn()) { cb(); }
pub fn calls_a_peer() { reads(); }
'''
JAVA = '''  public static void reads() throws Exception { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/a")); }
  public static void writes() throws Exception { java.nio.file.Files.writeString(java.nio.file.Path.of("/tmp/b"), "x"); }
  public static void spawns() throws Exception { new ProcessBuilder("curl", "-s").start(); }
  public static void dispatches(Runnable r) { r.run(); }
  public static void calls_a_peer() throws Exception { reads(); }
'''
TS = '''import * as fsm from "node:fs";
import { execFileSync } from "node:child_process";
export function reads(): Buffer { return fsm.readFileSync("/tmp/a"); }
export function writes(): void { fsm.writeFileSync("/tmp/b", "x"); }
export function spawns(): void { execFileSync("curl", ["-s"]); }
export function dispatches(cb: Function): void { cb(); }
export function calls_a_peer(): void { reads(); }
'''
SWIFT = '''import Foundation
func reads() { _ = FileManager.default.contents(atPath: "/tmp/a") }
func writes() { FileManager.default.createFile(atPath: "/tmp/b", contents: nil) }
func spawns() { let p = Process(); p.launchPath = "/usr/bin/curl"; try? p.run() }
func dispatches(_ cb: () -> Void) { cb() }
func calls_a_peer() { reads() }
'''


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def _glob(d):
    return [os.path.join(d, f) for f in os.listdir(d)] if os.path.isdir(d) else []


def read_report(d):
    """(envelope-keys, union of fn keys) from whatever report an engine wrote under `d`."""
    skip = ("callgraph", "hierarchy", "locs", "calibrated", "encountered")
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith(".json") or any(s in f for s in skip):
            continue
        try:
            dd = json.load(open(os.path.join(d, f)))
        except Exception:
            continue
        if not isinstance(dd, dict) or "functions" not in dd:
            continue
        fns = dd["functions"]
        it = fns.values() if isinstance(fns, dict) else fns
        fk = set()
        for e in it:
            if isinstance(e, dict):
                fk |= set(e.keys())
        return set(dd.keys()), fk
    return None, None


def main():
    ws = tempfile.mkdtemp(prefix="field-audit-")
    results = {}
    try:
        # rust
        d = os.path.join(ws, "rust"); os.makedirs(os.path.join(d, "src"), exist_ok=True)
        open(os.path.join(d, "Cargo.toml"), "w").write('[package]\nname = "aud"\nversion = "0.0.0"\nedition = "2021"\n')
        open(os.path.join(d, "src", "lib.rs"), "w").write(RUST)
        b = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
        if os.path.exists(b):
            run([b, d, "--out", os.path.join(d, "out")]); results["rust"] = read_report(d)

        # java
        d = os.path.join(ws, "java"); os.makedirs(os.path.join(d, "q"), exist_ok=True)
        open(os.path.join(d, "q", "E.java"), "w").write("package q;\npublic class E {\n" + JAVA + "}\n")
        cls = os.path.join(d, "classes"); os.makedirs(cls, exist_ok=True)
        jar = os.environ.get("CANDOR_JAVA_JAR") or next(
            (p for p in _glob(os.path.join(CANDOR_JAVA, "build", "libs")) if p.endswith("-all.jar")), None)
        if jar and shutil.which("javac") and run(["javac", "-d", cls, os.path.join(d, "q", "E.java")]).returncode == 0:
            run(["java", "-jar", jar, cls, "--json", os.path.join(d, "r.json")]); results["java"] = read_report(d)

        # ts
        d = os.path.join(ws, "ts"); os.makedirs(os.path.join(d, "src"), exist_ok=True)
        open(os.path.join(d, "package.json"), "w").write('{"name":"aud","version":"0.0.0"}\n')
        open(os.path.join(d, "tsconfig.json"), "w").write('{"include":["src"]}\n')
        open(os.path.join(d, "src", "a.ts"), "w").write(TS)
        if shutil.which("node") and os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")):
            run(["node", os.path.join(CANDOR_TS, "scan.mjs"), d, "--out", os.path.join(d, "out")])
            results["ts"] = read_report(d)

        # swift
        d = os.path.join(ws, "swift"); os.makedirs(os.path.join(d, "Sources", "App"), exist_ok=True)
        open(os.path.join(d, "Package.swift"), "w").write(
            '// swift-tools-version:5.9\nimport PackageDescription\n'
            'let package = Package(name: "App", targets: [.target(name: "App", path: "Sources/App")])\n')
        open(os.path.join(d, "Sources", "App", "a.swift"), "w").write(SWIFT)
        sb = os.path.join(CANDOR_SWIFT, ".build", "release", "candor-swift")
        if not os.path.exists(sb):
            sb = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
        if os.path.exists(sb):
            run([sb, d, "--out", os.path.join(d, "out")]); results["swift"] = read_report(d)
    finally:
        shutil.rmtree(ws, ignore_errors=True)

    live = [e for e in ("rust", "java", "ts", "swift") if results.get(e) and results[e][0]]
    if not live:
        print("FIELD AUDIT: no engine could run — an empty table must never read as agreement", file=sys.stderr)
        return 2

    def table(title, fields, idx):
        print(f"\n  {title}")
        print("    " + "field".ljust(14) + "".join(e.ljust(8) for e in live))
        for f in fields:
            row = "".join(("  ✔     " if f in results[e][idx] else "  ·     ") for e in live)
            print("    " + f.ljust(14) + row)

    print("SPEC §2 FIELD AUDIT — which engine emitted what, on an equivalent fixture")
    table("per-function fields", FN_FIELDS, 1)
    table("envelope fields", ENV_FIELDS, 0)
    print("\n  `·` is NOT a failure: a field the fixture never provoked is legitimately absent. This table is")
    print("  a prompt to ask why a column is empty — the `fs` gap looked exactly like a legitimate `·` for")
    print("  as long as it existed. The fixture does NOT provoke `hosts` or `tables`, so those rows say")
    print("  nothing at all.")
    skipped = [x for x in ("rust", "java", "ts", "swift") if x not in live]
    if skipped:
        print(f"\n  NOT RUN (reported, never implied): {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
