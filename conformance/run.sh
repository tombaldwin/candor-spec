#!/usr/bin/env bash
# Cross-impl conformance differential. Runs BOTH candor implementations on equivalent fixtures and asserts
# each infers the spec-expected effect set — so the two independent engines (Rust syntactic scan + JVM
# bytecode) can't silently diverge on the shared contract. The expected sets ARE the spec answer, so this
# is simultaneously a conformance check (each impl vs the spec) and a differential (the impls vs each other).
#
# Usage:   bash conformance/run.sh
# Repos are assumed siblings of candor-spec; override with CANDOR=… CANDOR_JAVA=… . Pre-built binaries can
# be supplied via CANDOR_SCAN_BIN=… (a candor-scan executable) and CANDOR_JAVA_JAR=… (the shadow jar) to
# skip building. Exit 0 iff every case matches in BOTH impls.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANDOR="${CANDOR:-$HERE/../../candor}"
CANDOR_JAVA="${CANDOR_JAVA:-$HERE/../../candor-java}"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT

# --- locate / build the two engines ------------------------------------------------------------------
SCAN="${CANDOR_SCAN_BIN:-}"
if [ -z "$SCAN" ]; then
  echo "building candor-scan…"
  cargo build -q --manifest-path "$CANDOR/Cargo.toml" -p candor-scan 2>/dev/null \
    || { echo "FAIL: could not build candor-scan (set CANDOR or CANDOR_SCAN_BIN)"; exit 2; }
  SCAN="$CANDOR/target/debug/candor-scan"
fi
JAR="${CANDOR_JAVA_JAR:-}"
if [ -z "$JAR" ]; then
  echo "building candor-java…"
  ( cd "$CANDOR_JAVA" && ./gradlew -q shadowJar ) 2>/dev/null \
    || { echo "FAIL: could not build candor-java (set CANDOR_JAVA or CANDOR_JAVA_JAR)"; exit 2; }
  JAR="$(ls "$CANDOR_JAVA"/build/libs/*-all.jar 2>/dev/null | head -1)"
fi
[ -x "$SCAN" ] || { echo "FAIL: no candor-scan at $SCAN"; exit 2; }
[ -f "$JAR" ]  || { echo "FAIL: no candor-java jar at $JAR"; exit 2; }

# --- run both engines on their fixtures --------------------------------------------------------------
cp -r "$HERE/rust" "$W/rust"
"$SCAN" "$W/rust" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on the rust fixture"; exit 2; }
RUST_REPORT="$(ls "$W"/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"

javac -d "$W/jout" "$HERE/java/Cases.java" 2>/dev/null || { echo "FAIL: javac on Cases.java"; exit 2; }
"$JAR" >/dev/null 2>&1 # noop guard
java -jar "$JAR" "$W/jout" --json "$W/java.json" >/dev/null 2>&1 \
  || { echo "FAIL: candor-java errored on the java fixture"; exit 2; }

# --- compare to the expected sets (and thereby to each other) ----------------------------------------
python3 - "$HERE/expected.json" "$RUST_REPORT" "$W/java.json" <<'PY'
import json, sys
expected = {k: set(v) for k, v in json.load(open(sys.argv[1])).items() if not k.startswith("_")}
def by_leaf(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
rust = by_leaf(sys.argv[2], "::")
java = by_leaf(sys.argv[3], ".")

print(f"\n{'case':20s} {'expected':16s} {'candor-scan':16s} {'candor-java':16s} verdict")
print("-" * 86)
fails = 0
for case, exp in expected.items():
    r, j = rust.get(case, set()), java.get(case, set())
    if r == exp and j == exp:
        verdict = "ok"
    elif r != j:
        verdict = "DIVERGE"; fails += 1
    else:
        verdict = "BOTH-OFF"; fails += 1
    e = ",".join(sorted(exp)) or "(pure)"
    rs = ",".join(sorted(r)) or "(pure)"
    js = ",".join(sorted(j)) or "(pure)"
    print(f"{case:20s} {e:16s} {rs:16s} {js:16s} {verdict}")
print("-" * 86)
print(f"{len(expected)} cases, {fails} mismatch(es)\n")
sys.exit(1 if fails else 0)
PY
