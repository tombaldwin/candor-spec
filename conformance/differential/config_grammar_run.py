#!/usr/bin/env python3
"""Five-engine EXIT-CODE differential over the `.candor/config` grammar. See README.md.

    python3 config_grammar_run.py            # the full sweep (~2500 configs, ~90 min)
    python3 config_grammar_run.py --quick    # the shapes that have historically broken (~5 min)

Exits 1 if any generated config makes two engines answer differently. A green run means nothing until
the instrument has been calibrated against a real regression — README.md says how, and why.
"""
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_grammar_gen import configs   # noqa: E402

# Engine locations, overridable so this can run against a release build or a worktree.
GIT = os.environ.get("CANDOR_GIT", os.path.expanduser("~/git"))
JAR = os.environ.get("CANDOR_JAR", f"{GIT}/candor-java/build/libs/candor-java-0.27.0-all.jar")
SCAN = os.environ.get("CANDOR_SCAN", f"{GIT}/candor-rust/target/debug/candor-scan")
TS = os.environ.get("CANDOR_TS", f"{GIT}/candor-ts/scan.mjs")
SWIFT = os.environ.get("CANDOR_SWIFT", f"{GIT}/candor-swift/.build/debug/candor-swift")
AGENTS = os.environ.get("CANDOR_AGENTS", f"{GIT}/candor-agents")
NODE = os.environ.get("NODE", "node")

# PER-INVOCATION, and this is not cosmetic: every engine writes into `<target>/.candor/`, and
# candor-agents drops `report.*.json` in the cwd. Two runners sharing a target — or one whose engine
# children outlived a `pkill` of its parent — overwrite each other's config file, and the result is a
# page of divergences that reproduce nowhere. See README.md.
TGT = f"/tmp/candor-cfgdiff-{os.getpid()}"
CFG = f"{TGT}/.candor/config"

ENGINES = [
    ("java", ["java", "-jar", JAR, "classes"]),
    ("rust", [SCAN, "."]),
    ("ts", [NODE, TS, "."]),
    ("swift", [SWIFT, "."]),
    ("agents", [sys.executable, "-c",
                f"import sys; sys.path.insert(0,{AGENTS!r});"
                "sys.argv=['candor-agents','.'];"
                "from candor_agents.scan import main; main()"]),
]


def build_target():
    """A fresh scan target: one trivial unit per language, doing nothing.

    The fixture is deliberately EFFECT-FREE. This differential is about how a config is READ, so the
    scan itself must not be able to contribute a difference — every engine's baseline here is exit 0.
    """
    shutil.rmtree(TGT, ignore_errors=True)
    for d in [".candor", "src", "Sources/App", "jsrc"]:
        os.makedirs(f"{TGT}/{d}")
    open(f"{TGT}/jsrc/A.java", "w").write("public class A { public void f(){} }\n")
    subprocess.run(["javac", "-d", f"{TGT}/classes", f"{TGT}/jsrc/A.java"],
                   capture_output=True, check=True)
    open(f"{TGT}/Cargo.toml", "w").write('[package]\nname="c"\nversion="0.1.0"\nedition="2021"\n')
    open(f"{TGT}/src/lib.rs", "w").write("pub fn f(){}\n")
    open(f"{TGT}/a.ts", "w").write("export function f(){}\n")
    open(f"{TGT}/Package.swift", "w").write(
        '// swift-tools-version:5.9\nimport PackageDescription\n'
        'let package = Package(name:"App", targets:[.target(name:"App")])\n')
    open(f"{TGT}/Sources/App/A.swift", "w").write("func f(){}\n")


def pristine():
    """Everything except the config under test, removed before each run."""
    for p in glob.glob(f"{TGT}/.candor/*") + glob.glob(f"{TGT}/report.*.json"):
        if os.path.basename(p) == "config":
            continue
        try:
            shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
        except FileNotFoundError:
            pass


def run(cmd):
    pristine()
    try:
        return subprocess.run(cmd, cwd=TGT, capture_output=True, timeout=180).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def main():
    quick = "--quick" in sys.argv
    build_target()
    # Each engine gets its OWN text for the rows that name an implementation: a `self` row must pin the
    # engine's own qualified pin, and an `other` row must never name the engine under test.
    per_engine = {name: dict(configs(name)) for name, _ in ENGINES}
    labels = list(per_engine["swift"].keys())
    if quick:
        labels = [x for x in labels if x.startswith(("paired/", "policy/", "deps/"))
                  or x.count("/") < 2 or "/nbsp" in x or "/crlf" in x]
    seen, agreed = {}, 0
    for i, label in enumerate(labels):
        codes = {}
        for name, cmd in ENGINES:
            with open(CFG, "w", encoding="utf-8", newline="") as f:
                f.write(per_engine[name][label])
            codes[name] = run(cmd)
        if len(set(codes.values())) == 1:
            agreed += 1
            continue
        sig = tuple(sorted(codes.items()))
        seen.setdefault(sig, []).append(label)
        if len(seen[sig]) == 1:      # one line per distinct signature, not per row
            print(f"DIVERGE  {label}\n         {dict(codes)}\n"
                  f"         config = {per_engine['swift'][label]!r}", flush=True)
        if (i + 1) % 200 == 0:
            print(f"  … {i+1}/{len(labels)}  agreed={agreed}", flush=True)
    total = sum(len(v) for v in seen.values())
    print(f"\nconfig-grammar differential: {agreed} agreed · {total} diverged "
          f"· {len(seen)} distinct signatures")
    for sig, ls in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(ls):4d}x  {dict(sig)}   e.g. {ls[0]}")
    shutil.rmtree(TGT, ignore_errors=True)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
