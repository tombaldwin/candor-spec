#!/usr/bin/env python3
"""
PART 31 -- SPEC §2 `fs`: THE READ/WRITE REFINEMENT ANSWERS THE SAME WAY IN EVERY ENGINE.

WHY THIS EXISTS, stated as it happened.

`fs` refines a proved `Fs` into read/write kinds and has been in SPEC §2 for a long time. On 2026-08-04 it
was pinned by NOTHING -- the three `"fs"` hits elsewhere in this suite are a fixture ID, not an assertion.
What that bought:

  * candor-swift had no such field at all (its only `fs` was the effect-name enum case);
  * candor-ts emitted nothing;
  * candor-rust had `pub fs: Vec<String>` in the wire model and `fs: Vec::new()` at the construction site.
    Hardcoded. Never populated. Which is WORSE than absent: a missing field says "this producer does not
    track kinds", a present-but-always-empty one says "kind undetermined" on every function forever -- a
    claim the engine was in no position to make, wearing a schema that implies support.

Only candor-java ever emitted it, and nobody noticed for as long as the field has existed. §2's own
omit-rather-than-guess rule is exactly what hid it: every empty answer looked legitimate.

THE PROPERTY, and why it is language-independent. Each engine scans a fixture of four functions whose Fs
verbs are semantically equivalent across the four languages:

    reads_only      one read verb                    ->  fs == ["read"]
    writes_only     one write verb                   ->  fs == ["write"]
    copies          a copy verb                      ->  fs == ["read","write"]
    reaches_writer  calls writes_only only           ->  fs == ["write"]   (kinds TRAVEL)
    mixed           calls writes_only AND a callee   ->  fs ABSENT
                    whose Fs kind is undetermined

THE LAST TWO ROWS ARE THE PROPERTY. `fs` DOES travel the call graph -- a caller that transitively only
writes is a writer, and saying so is the point of the field. What must NOT travel is a PARTIAL answer: if
any contributing `Fs` on the reachable set has no determined kind, the whole field is suppressed, because
["write"] there would claim "writes but never reads" about a function that may well do both. §2: *"when
`Fs` is reached but its kind is unknown ... the field MUST be omitted rather than guessed. An empty or
partial `fs` would be read as a positive claim."*

So an engine can fail this two ways, and they are opposite mistakes: propagate nothing (row 4 empty --
under-informative) or propagate without the undetermined guard (row 5 non-empty -- the partial claim).

VACUITY FLOOR. Every row must carry `Fs` in `inferred` on every engine. A cell where the effect was never
proved says nothing about the refinement of a proved effect, so it is reported as a broken fixture rather
than as a pass -- an empty differential that prints MATCH is the failure mode this suite exists to remove.

WHAT THIS DOES NOT PIN, said plainly: whether a producer implements `fs` AT ALL. Every engine emits it
today so the four rows agree, but a fifth engine emitting nothing would fail here for a reason it cannot
distinguish from a wrong answer -- and a consumer reading such a report cannot distinguish those either.
That ambiguity is a FORMAT gap (absence is overloaded between "undetermined" and "unimplemented"), and it
needs a positive capability declaration in the envelope, not a conformance row. Tracked, not implied.

    python3 gen_fs_kind.py
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

# fn base name -> the kinds SPEC §2 dictates. `None` means the field MUST BE ABSENT (not empty, absent).
EXPECT = {
    "reads_only":     ["read"],
    "writes_only":    ["write"],
    "copies":         ["read", "write"],
    "reaches_writer": ["write"],   # kinds TRAVEL: a caller that transitively only writes is a writer
    "mixed":          None,        # one contributor has no determined kind -> the WHOLE field is suppressed
}

RUST = '''use std::fs;
pub fn reads_only() { let _ = fs::read_to_string("/tmp/a"); }
pub fn writes_only() { let _ = fs::write("/tmp/b", "x"); }
pub fn copies() { let _ = fs::copy("/tmp/a", "/tmp/b"); }
pub fn reaches_writer() { writes_only(); }
pub fn undetermined() { let _ = std::fs::OpenOptions::new(); }
pub fn mixed() { writes_only(); undetermined(); }
'''

JAVA = '''  public static void reads_only() throws Exception { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/a")); }
  public static void writes_only() throws Exception { java.nio.file.Files.writeString(java.nio.file.Path.of("/tmp/b"), "x"); }
  public static void copies() throws Exception { java.nio.file.Files.copy(java.nio.file.Path.of("/tmp/a"), java.nio.file.Path.of("/tmp/b")); }
  public static void reaches_writer() throws Exception { writes_only(); }
  public static void undetermined() throws Exception { new java.io.RandomAccessFile("/tmp/a", "rw"); }
  public static void mixed() throws Exception { writes_only(); undetermined(); }
'''

TS = '''import * as fsm from "node:fs";
export function reads_only(): Buffer { return fsm.readFileSync("/tmp/a"); }
export function writes_only(): void { fsm.writeFileSync("/tmp/b", "x"); }
export function copies(): void { fsm.copyFileSync("/tmp/a", "/tmp/b"); }
export function reaches_writer(): void { writes_only(); }
export function undetermined(): number { return fsm.openSync("/tmp/a", "r+"); }
export function mixed(): void { writes_only(); undetermined(); }
'''

SWIFT = '''import Foundation
func reads_only() { _ = FileManager.default.contents(atPath: "/tmp/a") }
func writes_only() { FileManager.default.createFile(atPath: "/tmp/b", contents: nil) }
func copies() { try? FileManager.default.copyItem(atPath: "/tmp/a", toPath: "/tmp/b") }
func reaches_writer() { writes_only() }
func undetermined() { _ = FileManager.default.temporaryDirectory }
func mixed() { writes_only(); undetermined() }
'''


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def _glob(d, suffix):
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suffix)]


def load_resolves(prefix_dir, skip=("callgraph", "hierarchy", "locs", "calibrated", "encountered")):
    """⟨0.27⟩ SPEC §2.1 `resolves` from whichever report file carries the envelope."""
    if not os.path.isdir(prefix_dir):
        return None
    for f in sorted(os.listdir(prefix_dir)):
        if not f.endswith(".json") or any(s in f for s in skip):
            continue
        try:
            d = json.load(open(os.path.join(prefix_dir, f)))
        except Exception:
            continue
        if isinstance(d, dict) and "functions" in d:
            return d.get("resolves")
    return None


def load_entries(prefix_dir, skip=("callgraph", "hierarchy", "locs", "calibrated", "encountered")):
    """Every `functions` entry from whatever report files an engine wrote under `prefix_dir`.

    Tolerant of both report shapes (a dict keyed by fn, and a list of entries) because the engines differ
    and this property is about a FIELD, not about the envelope.
    """
    out = {}
    if not os.path.isdir(prefix_dir):
        return out
    for f in sorted(os.listdir(prefix_dir)):
        if not f.endswith(".json") or any(s in f for s in skip):
            continue
        try:
            d = json.load(open(os.path.join(prefix_dir, f)))
        except Exception:
            continue
        fns = d.get("functions")
        if fns is None:
            continue
        items = fns.items() if isinstance(fns, dict) else [(e.get("fn"), e) for e in fns]
        for name, e in items:
            if isinstance(e, dict) and name:
                out[name] = e
    return out


def match_row(entries, base):
    """The entry whose fn name ends in `base` -- engines qualify differently (module/package/class)."""
    for name, e in entries.items():
        tail = name.replace("#", ".").split(".")[-1]
        if tail == base:
            return e
    return None


class Engine:
    name = "?"

    def __init__(self):
        self.present = False
        self.ok = False
        self.err = None

    def prepare(self):
        raise NotImplementedError

    def scan(self, ws):
        raise NotImplementedError


class RustEngine(Engine):
    name = "rust"

    def prepare(self):
        self.bin = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(CANDOR, "target", "debug", "candor-scan")
        if not os.path.exists(self.bin):
            b = run(["cargo", "build", "-q", "--manifest-path", os.path.join(CANDOR, "Cargo.toml"),
                     "-p", "candor-scan"])
            if b.returncode != 0 or not os.path.exists(self.bin):
                self.err = "no candor-scan (set CANDOR or CANDOR_SCAN_BIN)"
                return
        self.present = self.ok = True

    def scan(self, ws):
        d = os.path.join(ws, "rust")
        os.makedirs(os.path.join(d, "src"), exist_ok=True)
        open(os.path.join(d, "Cargo.toml"), "w").write(
            '[package]\nname = "fskind"\nversion = "0.0.0"\nedition = "2021"\n')
        open(os.path.join(d, "src", "lib.rs"), "w").write("// GENERATED by gen_fs_kind.py\n" + RUST)
        run([self.bin, d, "--out", os.path.join(d, "out")])
        return load_entries(d), load_resolves(d)


class JavaEngine(Engine):
    name = "java"

    def prepare(self):
        self.jar = os.environ.get("CANDOR_JAVA_JAR")
        if not self.jar:
            cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
            if not cands:
                run(["./gradlew", "-q", "shadowJar"], cwd=CANDOR_JAVA)
                cands = _glob(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
            self.jar = max(cands, key=os.path.getmtime) if cands else None
        if not self.jar or not os.path.exists(self.jar) or not shutil.which("javac"):
            self.err = "no candor-java jar / javac"
            return
        self.present = self.ok = True

    def scan(self, ws):
        d = os.path.join(ws, "java")
        os.makedirs(os.path.join(d, "q"), exist_ok=True)
        open(os.path.join(d, "q", "E.java"), "w").write(
            "// GENERATED by gen_fs_kind.py\npackage q;\npublic class E {\n" + JAVA + "}\n")
        cls = os.path.join(d, "classes")
        os.makedirs(cls, exist_ok=True)
        c = run(["javac", "-d", cls, os.path.join(d, "q", "E.java")])
        if c.returncode != 0:
            return {}
        # candor-java takes `--json <file>`, not `--out <prefix>` — the engines' scan CLIs differ here and
        # assuming otherwise made this arm silently produce nothing, which the harness reported as broken
        # rather than as a pass. That distinction is why it is reported at all.
        out = os.path.join(d, "report.json")
        run(["java", "-jar", self.jar, cls, "--json", out])
        return load_entries(d), load_resolves(d)


class TsEngine(Engine):
    name = "ts"

    def prepare(self):
        if not shutil.which("node") or not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")):
            self.err = "no node / scan.mjs (set CANDOR_TS)"
            return
        if not os.path.isdir(os.path.join(CANDOR_TS, "node_modules")):
            run(["npm", "install", "--no-fund", "--no-audit"], cwd=CANDOR_TS)
        self.present = self.ok = True

    def scan(self, ws):
        d = os.path.join(ws, "ts")
        os.makedirs(os.path.join(d, "src"), exist_ok=True)
        open(os.path.join(d, "package.json"), "w").write('{"name":"fskind","version":"0.0.0"}\n')
        open(os.path.join(d, "tsconfig.json"), "w").write('{"include":["src"]}\n')
        open(os.path.join(d, "src", "cases.ts"), "w").write("// GENERATED by gen_fs_kind.py\n" + TS)
        run(["node", os.path.join(CANDOR_TS, "scan.mjs"), d, "--out", os.path.join(d, "out")])
        return load_entries(d), load_resolves(d)


class SwiftEngine(Engine):
    name = "swift"

    def prepare(self):
        if not shutil.which("swift") or not os.path.exists(os.path.join(CANDOR_SWIFT, "Package.swift")):
            self.err = "no swift toolchain / Package.swift (set CANDOR_SWIFT)"
            return
        self.bin = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
        if not os.path.exists(self.bin):
            b = run(["swift", "build"], cwd=CANDOR_SWIFT)
            if b.returncode != 0 or not os.path.exists(self.bin):
                self.err = "swift build failed"
                return
        self.present = self.ok = True

    def scan(self, ws):
        d = os.path.join(ws, "swift")
        os.makedirs(os.path.join(d, "Sources", "App"), exist_ok=True)
        open(os.path.join(d, "Package.swift"), "w").write(
            '// swift-tools-version:5.9\nimport PackageDescription\n'
            'let package = Package(name: "App", targets: [.target(name: "App", path: "Sources/App")])\n')
        open(os.path.join(d, "Sources", "App", "cases.swift"), "w").write(
            "// GENERATED by gen_fs_kind.py\n" + SWIFT)
        run([self.bin, d, "--out", os.path.join(d, "out")])
        return load_entries(d), load_resolves(d)


def main():
    engines = [RustEngine(), JavaEngine(), TsEngine(), SwiftEngine()]
    for e in engines:
        e.prepare()
    live = [e for e in engines if e.ok]
    for e in engines:
        if not e.ok:
            print(f"  [{e.name:5}] SKIP -- {e.err}")
    if not live:
        print("FAIL: no engine could run -- an empty differential must never read as agreement")
        return 2

    # CANDOR_PROBE_FAULT: corrupt the first live cell in the direction the property forbids, so the suite
    # can check this generator still discriminates. The fault CLAIMS a direction the fixture never proved
    # -- which is precisely the partial claim §2 forbids.
    fault = bool(os.environ.get("CANDOR_PROBE_FAULT"))

    bad = 0
    checked = 0
    ws = tempfile.mkdtemp(prefix="fskind-")
    try:
        for e in live:
            entries, resolves = e.scan(ws)
            if not entries:
                print(f"  FAIL [{e.name}] produced no report entries -- the harness is broken, not the engine")
                bad += 1
                continue
            # ⟨0.27⟩ SPEC §2.1 -- an engine that emits `fs` VALUES must DECLARE that it resolves them.
            # Without the declaration a consumer cannot tell an omitted `fs` ("reached, kind undetermined")
            # from an engine that never computes kinds, and the omit-rather-than-guess rule loses its
            # meaning. This is the row a MUST on the FIELD could never have caught: `fs: Vec::new()`
            # satisfies a mandatory field and declares nothing.
            checked += 1
            if not resolves or "fs" not in resolves:
                print(f"  FAIL [{e.name}] emits `fs` values but its envelope does not declare "
                      f"resolves=[...\"fs\"...] (got {resolves!r}) -- every omission it writes is unreadable")
                bad += 1
            for base, want in EXPECT.items():
                row = match_row(entries, base)
                if row is None:
                    print(f"  FAIL [{e.name}] {base}: absent from the report entirely -- under ⟨0.21⟩ that is a "
                          f"purity claim, and this fixture proves the function is effectful")
                    bad += 1
                    continue
                inferred = row.get("inferred") or []
                if "Fs" not in inferred:
                    print(f"  FAIL [{e.name}] {base}: no `Fs` in inferred ({inferred}) -- the effect was never "
                          f"proved, so this cell says nothing about refining a proved effect (vacuous)")
                    bad += 1
                    continue
                got = row.get("fs")
                if fault and base == "mixed" and not got:
                    print(f"  PROBE: claiming a direction {e.name}/{base} never proved")
                    got = ["write"]
                checked += 1
                if want is None:
                    if got:
                        print(f"  FAIL [{e.name}] {base}: fs={got} but the fn performs NO Fs of its own -- "
                              f"§2 forbids a partial claim, and a propagated kind is exactly that "
                              f"('writes but never reads' about a caller that does neither)")
                        bad += 1
                elif sorted(got or []) != sorted(want):
                    print(f"  FAIL [{e.name}] {base}: fs={got}, expected {want}")
                    bad += 1

    finally:
        shutil.rmtree(ws, ignore_errors=True)

    names = ", ".join(e.name for e in live)
    if checked == 0:
        print("FAIL: no cell was actually compared -- a vacuous MATCH is the failure this suite removes")
        return 2
    if bad:
        print(f"  -> {bad} divergence(s) over {checked} cell(s) on [{names}]")
        return 1
    print(f"  fs read/write refinement agrees on {checked} cell(s) across [{names}]: kinds travel the call "
          f"graph, and an undetermined contributor suppresses the whole field on every engine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
