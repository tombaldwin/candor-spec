#!/usr/bin/env python3
"""Four-engine EXIT-CODE differential over the §6.2 POLICY DSL, on the conformance gate fixtures.

    python3 policy_grammar_run.py

Exits 1 on an UNEXPECTED divergence. Four scoped rows are expected to differ and are listed below —
they are fixture structure, not grammar, and the reason is worth keeping rather than silencing.

See README.md for the method and for the calibration that makes a green run mean something.
"""
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_grammar_gen import policies   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "gate"))
GIT = os.environ.get("CANDOR_GIT", os.path.expanduser("~/git"))
JAR = os.environ.get("CANDOR_JAR", f"{GIT}/candor-java/build/libs/candor-java-0.27.0-all.jar")
SCAN = os.environ.get("CANDOR_SCAN", f"{GIT}/candor-rust/target/debug/candor-scan")
TS = os.environ.get("CANDOR_TS", f"{GIT}/candor-ts/scan.mjs")
SWIFT = os.environ.get("CANDOR_SWIFT", f"{GIT}/candor-swift/.build/debug/candor-swift")
NODE = os.environ.get("NODE", "node")

W = f"/tmp/candor-poldiff-{os.getpid()}"

# `app` is a package in the java fixture and in none of the others (rust's unit is `save`, ts's is
# `store.save`, swift's is `save`), so a rule SCOPED to `app` binds in java alone. That is the fixtures
# being what they are, not the grammar diverging — recorded here rather than deleted, because a scoped
# rule is worth exercising and the day one of these stops differing is a day something changed.
EXPECTED_SCOPE_ROWS = {"deny-Fs-scope", "pure-scope", "deny-two-scope", "two-filters",
                       "deny-Net-scope", "deny-Unknown-scope"}


def prep():
    shutil.rmtree(W, ignore_errors=True)
    os.makedirs(W)
    for d in ["java", "rust", "ts", "swift"]:
        shutil.copytree(f"{SRC}/{d}", f"{W}/{d}")
        for p in glob.glob(f"{W}/{d}/.candor/*"):
            os.remove(p) if os.path.isfile(p) else shutil.rmtree(p, ignore_errors=True)
    subprocess.run(["javac", "-d", f"{W}/jclasses"] + glob.glob(f"{W}/java/app/*.java"),
                   capture_output=True, check=True)


def engines(pol):
    return [
        ("java", ["java", "-jar", JAR, f"{W}/jclasses", "--policy", pol], W),
        ("rust", [SCAN, ".", "--policy", pol], f"{W}/rust"),
        ("ts", [NODE, TS, ".", "--policy", pol], f"{W}/ts"),
        ("swift", [SWIFT, ".", "--policy", pol], f"{W}/swift"),
    ]


def run(cmd, cwd):
    for p in glob.glob(f"{cwd}/.candor/*"):
        try:
            os.remove(p) if os.path.isfile(p) else shutil.rmtree(p, ignore_errors=True)
        except FileNotFoundError:
            pass
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=180).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def main():
    prep()
    pol = f"{W}/pol.candor"
    seen, agreed, expected = {}, 0, 0
    for label, text in policies():
        with open(pol, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        codes = {n: run(c, d) for n, c, d in engines(pol)}
        if len(set(codes.values())) == 1:
            agreed += 1
        elif label in EXPECTED_SCOPE_ROWS:
            expected += 1
        else:
            seen.setdefault(tuple(sorted(codes.items())), []).append((label, text))
    total = sum(len(v) for v in seen.values())
    print(f"policy-grammar differential: {agreed} agreed · {expected} expected-scope "
          f"· {total} UNEXPECTED over {len(policies())} shapes")
    for sig, rows in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        print(f"\n  {len(rows)}x  {dict(sig)}")
        for label, text in rows:
            print(f"      {label:22s} {text!r}")
    shutil.rmtree(W, ignore_errors=True)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
