#!/usr/bin/env bash
# Cross-impl conformance differential. Runs the candor implementations (Rust + JVM, and the TS engine
# when present) on equivalent fixtures and asserts they agree — first on the EFFECT SETS they infer,
# then on the POLICY VERDICT they reach. Independent engines (Rust syntactic scan + JVM bytecode +
# TS AST) sharing one spec is candor's defining moat over
# a per-language ruleset (CodeQL/Semgrep/ArchUnit): not just "we have rules for both languages", but a
# MACHINE-CHECKED guarantee that the same effect contract AND the same `deny`/`pure` gate mean the same
# thing in each. A DIVERGE row is a bug in one engine.
#
# TIER TAGS. Each PART header carries [TIER 1] or [TIER 2] (SPEC §"Conformance tiers"). TIER 1 pins the
# INTEROP FLOOR — the report schema, effect vocabulary, the Unknown trust marker, the policy VERDICT and
# grammar, the literal surfaces, the coverage ledger, config fail-closed sourcing, chaining, and the baseline
# guard: a divergence here yields output another engine or a consumer CANNOT TRUST. TIER 2 pins the
# TOOL SURFACES — the read-only query shapes, `rewire`, `fix`/`fix-gate`, `unverified`, and the gate's
# advisory disclosures: a divergence breaks a TOOL's cross-engine uniformity, but reports and verdicts stay
# trustworthy. The version trigger follows the tiers (SPEC §Versioning): a tier-1 breaking change bumps the
# major lockstep; a tier-1 additive change or a tier-2 addition promoted to required bumps the minor (0.9
# was exactly a tier-2 promotion — `fix`/`unverified`/the disclosure became required, tier 1 untouched).
#
# Usage:   bash conformance/run.sh
# Repos are assumed siblings of candor-spec; override with CANDOR=… CANDOR_JAVA=… . Pre-built binaries via
# CANDOR_SCAN_BIN=… CANDOR_QUERY_BIN=… CANDOR_JAVA_JAR=… skip the build. Exit 0 iff everything matches.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANDOR="${CANDOR:-$HERE/../../candor-rust}"
CANDOR_JAVA="${CANDOR_JAVA:-$HERE/../../candor-java}"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT

# A CHECKER CRASH MUST NOT MASQUERADE AS AN ENGINE DISAGREEMENT.
#
# Every differential case here runs `python3 - … <<'PY' || rc=1`. That sets rc on a real divergence AND on
# a checker that merely died — a report truncated because a release rebuild was in flight, a missing file,
# a typo in the checker itself. Both exit 1; only the first prints a DIVERGE line. So the run ended
# "conformance: FAILED" with no named divergence anywhere in it, which reads as "the engines disagree and
# the suite will not say how". That happened once during the R4 work and cost a real investigation before
# three clean re-runs made it look like flakiness.
#
# It is the suite's own version of the defect it exists to catch: a verdict whose evidence is absent.
# Tee stderr so the summary can tell the two apart and say which it was.
exec 2> >(tee "$W/harness-stderr.log" >&2)

# --- locate / build the engines ----------------------------------------------------------------------
SCAN="${CANDOR_SCAN_BIN:-}"
QUERY="${CANDOR_QUERY_BIN:-}"
if [ -z "$SCAN" ] || [ -z "$QUERY" ]; then
  echo "building candor-scan + candor-query…"
  cargo build -q --manifest-path "$CANDOR/Cargo.toml" -p candor-scan -p candor-query 2>/dev/null \
    || { echo "FAIL: could not build candor-scan/candor-query (set CANDOR or the *_BIN vars)"; exit 2; }
  SCAN="${SCAN:-$CANDOR/target/debug/candor-scan}"
  QUERY="${QUERY:-$CANDOR/target/debug/candor-query}"
fi
JAR="${CANDOR_JAVA_JAR:-}"
if [ -z "$JAR" ]; then
  echo "building candor-java…"
  ( cd "$CANDOR_JAVA" && ./gradlew -q shadowJar ) 2>/dev/null \
    || { echo "FAIL: could not build candor-java (set CANDOR_JAVA or CANDOR_JAVA_JAR)"; exit 2; }
  JAR="$(ls -t "$CANDOR_JAVA"/build/libs/*-all.jar 2>/dev/null | head -1)"  # -t: newest, not lexicographic — a stale 0.3.2 jar must not shadow 0.3.3
fi
[ -x "$SCAN" ]  || { echo "FAIL: no candor-scan at $SCAN"; exit 2; }
[ -x "$QUERY" ] || { echo "FAIL: no candor-query at $QUERY"; exit 2; }
[ -f "$JAR" ]   || { echo "FAIL: no candor-java jar at $JAR"; exit 2; }

# The optional THIRD engine (candor-ts). When present, it joins the grammar (4), query-shape (5) and
# effect-set (6) differentials; when absent those parts run two-way / Part 6 skips loudly.
# TS_PRESENT (the checkout exists) is deliberately distinct from TS_OK (the scan produced a report):
# a present-but-broken engine must FAIL the suite, never read as "not present — SKIPPED".
TS_DIR="${CANDOR_TS:-$HERE/../../candor-ts}"
TS_PRESENT=""
TS_OK=""
if command -v node >/dev/null 2>&1 && [ -f "$TS_DIR/scan.mjs" ]; then
  TS_PRESENT=1
  ( cd "$TS_DIR" && { [ -d node_modules ] || npm install --no-fund --no-audit >/dev/null 2>&1; } )
  ( cd "$TS_DIR" && node scan.mjs Cases.ts "$W/ts" 2>/dev/null )
  [ -s "$W/ts.json" ] && TS_OK=1
fi

# The optional FOURTH engine (candor-swift). Joins the tables (4b), ledger (4c) and effect-set (6c)
# differentials. SW_PRESENT vs SW_OK: present-but-broken must FAIL, never read as skipped (the
# TS_PRESENT lesson). CI note: ubuntu runners have no swift toolchain, so CI runs three-way and the
# fourth engine is a loud local/macOS differential until the workflow gains a swift setup step.
SW_DIR="${CANDOR_SWIFT:-$HERE/../../candor-swift}"
SW_PRESENT=""
SW_OK=""
SW_BIN=""
if command -v swift >/dev/null 2>&1 && [ -f "$SW_DIR/Package.swift" ]; then
  SW_PRESENT=1
  ( cd "$SW_DIR" && swift build >/dev/null 2>&1 )
  SW_BIN="$SW_DIR/.build/debug/candor-swift"
  if [ -x "$SW_BIN" ]; then
    "$SW_BIN" "$SW_DIR/conformance/Cases.swift" --out "$W/sw" >/dev/null 2>&1
  fi
  SW_REPORT=$(ls "$W"/sw.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
  [ -n "$SW_REPORT" ] && [ -s "$SW_REPORT" ] && SW_OK=1
fi

rc=0

# ====================================================================================================
# PART 1 — effect-set differential (each engine vs the spec, and vs each other)   [TIER 1]
# ====================================================================================================
cp -r "$HERE/rust" "$W/rust"
"$SCAN" "$W/rust" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on the rust fixture"; exit 2; }
RUST_REPORT="$(ls "$W"/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
javac -d "$W/jout" "$HERE/java/Cases.java" 2>/dev/null || { echo "FAIL: javac on Cases.java"; exit 2; }
java -jar "$JAR" "$W/jout" --json "$W/java.json" >/dev/null 2>&1 \
  || { echo "FAIL: candor-java errored on the java fixture"; exit 2; }

python3 - "$HERE/expected.json" "$RUST_REPORT" "$W/java.json" <<'PY' || rc=1
import json, sys
expected = {k: set(v) for k, v in json.load(open(sys.argv[1])).items() if not k.startswith("_")}
def by_leaf(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
rust = by_leaf(sys.argv[2], "::"); java = by_leaf(sys.argv[3], ".")
print(f"\n[1] EFFECT-SET differential")
print(f"{'case':20s} {'expected':16s} {'candor-scan':16s} {'candor-java':16s} verdict")
print("-" * 86)
fails = 0
for case, exp in expected.items():
    r, j = rust.get(case, set()), java.get(case, set())
    verdict = "ok" if (r == exp and j == exp) else ("DIVERGE" if r != j else "BOTH-OFF")
    if verdict != "ok": fails += 1
    f = lambda s: ",".join(sorted(s)) or "(pure)"
    print(f"{case:20s} {f(exp):16s} {f(r):16s} {f(j):16s} {verdict}")
print("-" * 86)
print(f"{len(expected)} cases, {fails} mismatch(es)")
sys.exit(1 if fails else 0)
PY

# Callgraph COMPLETENESS (SPEC §2.2): every analyzed function — including an uncalled pure LEAF like
# `pure_fn` — must be a key in the sidecar (empty list when it has no project callees). Omitting leaves
# made them invisible to whatif/callers and conflated "no callers" with "no such function".
RUST_CG="${RUST_REPORT%.json}.callgraph.json"
JAVA_CG="${W}/java.callgraph.json"
python3 - "$HERE/expected.json" "$RUST_CG" "$JAVA_CG" <<'PY' || rc=1
import json, sys
cases = {k for k in json.load(open(sys.argv[1])) if not k.startswith("_")}
def keys_by_leaf(p, sep):
    return {k.split(sep)[-1] for k in json.load(open(p))}
r, j = keys_by_leaf(sys.argv[2], "::"), keys_by_leaf(sys.argv[3], ".")
miss_r, miss_j = sorted(cases - r), sorted(cases - j)
print(f"\n[1b] CALLGRAPH completeness (SPEC §2.2 — every fn a key, incl. uncalled pure leaves)")
print(f"  candor-scan: {'all ' + str(len(cases)) + ' cases present' if not miss_r else 'MISSING ' + str(miss_r)}")
print(f"  candor-java: {'all ' + str(len(cases)) + ' cases present' if not miss_j else 'MISSING ' + str(miss_j)}")
ok = not miss_r and not miss_j
print("  -> " + ("MATCH — both sidecars are complete" if ok else "INCOMPLETE"))
sys.exit(0 if ok else 1)
PY

# PART 1c — HONESTY invariant (SPEC §4 trust contract). candor's one dangerous lie is the silent UNDER-   [TIER 1]
# report (pure-when-it-isn't), and its mitigation is that UNCERTAINTY PROPAGATES caller-ward: a function
# may look certain (no Unknown / no disclosure) only if everything it transitively reaches is certain too.
# check_honesty.py asserts that over each engine's OWN report (callgraph-driven, so pure fns are covered).
# This is engine-vs-spec (each engine must be internally honest), NOT a differential — and it catches the
# class where uncertainty was HAD but swallowed (it can't catch an effect the engine never registered;
# that needs the dynamic syscall oracle). A violation fails the run.
echo ""
echo "[1c] HONESTY invariant (SPEC §4 — uncertainty must propagate caller-ward)"
honesty() { local out r; out=$(python3 "$HERE/check_honesty.py" "$1" 2>&1); r=$?; printf '%s\n' "$out" | sed 's/^/  /'; return $r; }
honesty "$RUST_REPORT" || rc=1
honesty "$W/java.json" || rc=1
[ -n "$TS_OK" ] && { honesty "$W/ts.json" || rc=1; }
[ -n "$SW_OK" ] && { honesty "$SW_REPORT" || rc=1; }

# ====================================================================================================
# PART 2 — policy-verdict differential: the same `deny Net api` policy, the same `whatif`, same verdict?   [TIER 1]
# This is the moat a per-language ruleset can't offer: the ENFORCEMENT means the same thing in each engine.
# ====================================================================================================
cp -r "$HERE/policy" "$W/policy"
POL="$W/policy/policy"
"$SCAN" "$W/policy/rust" >/dev/null 2>&1 || { echo "FAIL: scan errored on the policy/rust fixture"; exit 2; }
"$QUERY" whatif "$W/policy/rust/.candor/report" quote Net "$POL" 1 > "$W/rust_wi.json" 2>/dev/null
javac -d "$W/pjout" $(find "$W/policy/java" -name '*.java') 2>/dev/null || { echo "FAIL: javac on policy/java"; exit 2; }
java -jar "$JAR" "$W/pjout" --json "$W/pjava.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on policy/java"; exit 2; }
java -jar "$JAR" whatif "$W/pjava.json" quote Net "$POL" --json > "$W/java_wi.json" 2>/dev/null

python3 - "$W/rust_wi.json" "$W/java_wi.json" <<'PY' || rc=1
import json, sys
r = json.load(open(sys.argv[1])); j = json.load(open(sys.argv[2]))
def verdict(d, sep):
    leaf = lambda s: s.split(sep)[-1]
    return (bool(d["ok"]),
            sorted(leaf(v["fn"]) for v in d["violations"]),    # the gate verdict
            sorted(leaf(f) for f in d["affected"]))            # AND the blast radius (the graph)
rv, jv = verdict(r, "::"), verdict(j, ".")
print(f"\n[2] POLICY-VERDICT differential  (whatif quote Net  ·  policy `deny Net api`)")
print(f"  candor-scan: ok={rv[0]}  violations={rv[1]}  affected={rv[2]}")
print(f"  candor-java: ok={jv[0]}  violations={jv[1]}  affected={jv[2]}")
match = rv == jv
print("  -> " + ("MATCH — the gate verdict AND the blast radius are identical in both engines"
                 if match else "DIVERGE — the engines disagree on the verdict or the blast radius"))
sys.exit(0 if match else 1)
PY

# ====================================================================================================
# PART 3 — rewire-verdict differential: a function drops a call (de-wiring). Do both engines flag the   [TIER 2]
# SAME dropped edge? Completes cross-impl parity for the newest commands (effects + whatif + rewire).
# ====================================================================================================
cp -r "$HERE/rewire" "$W/rewire"
"$SCAN" "$W/rewire/rust/baseline" >/dev/null 2>&1 || { echo "FAIL: scan errored on rewire/rust/baseline"; exit 2; }
"$SCAN" "$W/rewire/rust/gamed" >/dev/null 2>&1 || { echo "FAIL: scan errored on rewire/rust/gamed"; exit 2; }
"$QUERY" rewire "$W/rewire/rust/gamed/.candor/report" "$W/rewire/rust/baseline/.candor/report" 1 > "$W/rust_rw.json" 2>/dev/null
javac -d "$W/rwb" $(find "$W/rewire/java/baseline" -name '*.java') 2>/dev/null || { echo "FAIL: javac on rewire/java/baseline"; exit 2; }
javac -d "$W/rwg" $(find "$W/rewire/java/gamed" -name '*.java') 2>/dev/null || { echo "FAIL: javac on rewire/java/gamed"; exit 2; }
java -jar "$JAR" "$W/rwb" --json "$W/rwb.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on rewire/java/baseline"; exit 2; }
java -jar "$JAR" "$W/rwg" --json "$W/rwg.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on rewire/java/gamed"; exit 2; }
java -jar "$JAR" rewire "$W/rwg.json" "$W/rwb.json" --json > "$W/java_rw.json" 2>/dev/null

python3 - "$W/rust_rw.json" "$W/java_rw.json" <<'PY' || rc=1
import json, sys
def dewired(p, sep):
    d = json.load(open(p))
    return sorted((e["caller"].split(sep)[-1], sorted(c.split(sep)[-1] for c in e["no_longer_calls"]))
                  for e in d["dropped"])
r, j = dewired(sys.argv[1], "::"), dewired(sys.argv[2], ".")
print(f"\n[3] REWIRE-VERDICT differential  (a function drops a call — de-wiring detection)")
print(f"  candor-scan: dropped={r}")
print(f"  candor-java: dropped={j}")
match = r == j
print("  -> " + ("MATCH — both engines detect the same de-wiring"
                 if match else "DIVERGE — the engines disagree on the dropped edges"))
sys.exit(0 if match else 1)
PY

# ====================================================================================================
# PART 4 — policy-DSL grammar differential: parse the SAME CANDOR_POLICY battery with both engines and   [TIER 1]
# assert identical parsed rule sets. The executable form of SPEC §6.2 — the gate's grammar
# (deny/pure/allow/forbid, the Unknown-deny, scope/literal matching) meaning the same thing in each.
# A per-language ruleset has no shared grammar to diff; candor's single policy file MUST parse alike.
# ====================================================================================================
POL_BATTERY="$HERE/policydsl/policy.txt"
"$QUERY" parsepolicy "$POL_BATTERY" > "$W/rust_pol.json" 2>/dev/null \
  || { echo "FAIL: candor-query parsepolicy errored on the battery"; exit 2; }
java -jar "$JAR" parsepolicy "$POL_BATTERY" > "$W/java_pol.json" 2>/dev/null \
  || { echo "FAIL: candor-java parsepolicy errored on the battery"; exit 2; }
if [ -n "$TS_PRESENT" ] && [ -f "$TS_DIR/query.mjs" ]; then
  node "$TS_DIR/query.mjs" parsepolicy "$POL_BATTERY" > "$W/ts_pol.json" 2>/dev/null \
    || { echo "FAIL: candor-ts parsepolicy errored on the battery"; exit 2; }
fi
# candor-swift's `parsepolicy` shipped 2026-07-10 (0df872f, java-parity verified incl. the set-dedup
# fix it forced) — the grammar diff is now a HARD four-way requirement whenever the engine works: a
# working swift binary that cannot dump a parse is present-but-broken and FAILS, never a skip.
SW_POL_OK=""
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  "$SW_BIN" parsepolicy "$POL_BATTERY" > "$W/sw_pol.json" 2>/dev/null \
    && python3 -c 'import json,sys; json.load(open(sys.argv[1]))["deny"]' "$W/sw_pol.json" >/dev/null 2>&1 \
    || { echo "FAIL: candor-swift is working but parsepolicy produced no parse — the §6.2 grammar witness vanished"; exit 2; }
  SW_POL_OK=1
fi

python3 - "$W/rust_pol.json" "$W/java_pol.json" "$W/ts_pol.json" "${SW_POL_OK:+$W/sw_pol.json}" <<'PY' || rc=1
import json, os, sys
def norm(p):
    d = json.load(open(p))
    # `unknownClasses` (reason-scoped Unknown) + `netClasses` (Net destination-class) are compared four-way:
    # absent and [] both normalize to (), so a bare deny stays comparable while a `deny E Unknown[class…]` /
    # `deny Net[dest…]` pins the reason-class + destination-class parsing across all engines.
    deny   = sorted((tuple(sorted(r["effects"])), r["scope"],
                     tuple(sorted(r.get("unknownClasses", []))),
                     tuple(sorted(r.get("netClasses", [])))) for r in d["deny"])
    allow  = sorted((r["effect"], r["scope"], tuple(sorted(r["values"]))) for r in d["allow"])
    forbid = sorted((r["from"], r["to"]) for r in d["forbid"])
    return deny, allow, forbid
r, j = norm(sys.argv[1]), norm(sys.argv[2])
t = norm(sys.argv[3]) if os.path.exists(sys.argv[3]) else None
sw = norm(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] and os.path.exists(sys.argv[4]) else None
print("\n[4] POLICY-DSL grammar differential  (SPEC §6.2 — parse the same battery in every engine)")
print(f"  candor(rust): {len(r[0])} deny, {len(r[1])} allow, {len(r[2])} forbid")
print(f"  candor-java : {len(j[0])} deny, {len(j[1])} allow, {len(j[2])} forbid")
if t is not None:
    print(f"  candor-ts   : {len(t[0])} deny, {len(t[1])} allow, {len(t[2])} forbid")
if sw is not None:
    print(f"  candor-swift: {len(sw[0])} deny, {len(sw[1])} allow, {len(sw[2])} forbid")
else:
    print("  candor-swift: not present on this runner — grammar diff runs three-way (loudly)")
others = [x for x in (t, sw) if x is not None]
match = all(r == o for o in others) and r == j
n = {0: "two", 1: "three", 2: "all four"}[len(others)]
print("  -> " + (f"MATCH — {n} engines parse the deny/pure/allow/forbid grammar identically"
                 if match else "DIVERGE — the engines parse the policy DSL differently"))
if not match:
    for name, idx in (("deny", 0), ("allow", 1), ("forbid", 2)):
        sets = {"rust": r[idx], "java": j[idx]}
        if t is not None: sets["ts"] = t[idx]
        if sw is not None: sets["swift"] = sw[idx]
        if len({repr(v) for v in sets.values()}) > 1:
            for eng, v in sets.items():
                print(f"     {name} {eng}={v}")
sys.exit(0 if match else 1)
PY

# ====================================================================================================
# PART 4b — tables-extraction differential: SPEC §2 pins the SQL `tables` extraction token-for-token;   [TIER 1]
# tables/vectors.json is its executable form. Each vector is embedded as a string literal in a
# per-language Db-effect fixture and the three reports' `tables` fields must match the expectation —
# two engines extracting different tables from the same SQL would split the AS-EFF-008 verdict.
# (The TS fixture ships a stub `pg` package so the import resolves hermetically — no npm install.)
# ====================================================================================================
TABVEC="$HERE/tables/vectors.json"
python3 - "$TABVEC" "$W" <<'PY'
import json, os, sys
V = json.load(open(sys.argv[1]))["vectors"]
W = sys.argv[2]
lit = lambda x: json.dumps(x, ensure_ascii=False)  # raw UTF-8: \uXXXX escapes are valid Java/TS but NOT Rust (\u{…}); a JSON string literal is otherwise valid in all three
os.makedirs(f"{W}/tab/rust/src", exist_ok=True)
open(f"{W}/tab/rust/Cargo.toml", "w").write('[package]\nname = "tabvec"\nversion = "0.0.0"\nedition = "2021"\n')
open(f"{W}/tab/rust/src/lib.rs", "w").write("".join(
    f'pub fn {v["name"]}() {{ let _ = rusqlite::Connection::execute({lit(v["sql"])}); }}\n' for v in V))
os.makedirs(f"{W}/tab/java/q", exist_ok=True)
open(f"{W}/tab/java/q/V.java", "w").write("package q;\npublic class V {\n" + "".join(
    f'    static void {v["name"]}(java.sql.Connection c) throws Exception {{ c.prepareStatement({lit(v["sql"])}).executeQuery(); }}\n'
    for v in V) + "}\n")
os.makedirs(f"{W}/tab/ts/node_modules/pg", exist_ok=True)
open(f"{W}/tab/ts/node_modules/pg/package.json", "w").write('{"name":"pg","version":"0.0.0","main":"index.js","types":"index.d.ts"}\n')
open(f"{W}/tab/ts/node_modules/pg/index.d.ts", "w").write("export declare class Pool { query(sql: string): Promise<any>; }\n")
open(f"{W}/tab/ts/node_modules/pg/index.js", "w").write("module.exports = { Pool: class Pool { query() {} } };\n")
open(f"{W}/tab/ts/cases.ts", "w").write('import { Pool } from "pg";\nconst pool = new Pool();\n' + "".join(
    f'export function {v["name"]}() {{ return pool.query({lit(v["sql"])}); }}\n' for v in V))
os.makedirs(f"{W}/tab/swift", exist_ok=True)
open(f"{W}/tab/swift/cases.swift", "w").write("import Foundation\nimport SQLite3\n\n" + "".join(
    f'func {v["name"]}() {{ _ = sqlite3_exec(nil, {lit(v["sql"])}, nil, nil, nil) }}\n' for v in V))
PY
"$SCAN" "$W/tab/rust" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on the tables-vector fixture"; exit 2; }
TAB_RUST="$(ls "$W"/tab/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
javac -d "$W/tab/jout" "$W/tab/java/q/V.java" 2>/dev/null || { echo "FAIL: javac on the tables-vector fixture"; exit 2; }
java -jar "$JAR" "$W/tab/jout" --json "$W/tab/java.json" >/dev/null 2>&1 \
  || { echo "FAIL: candor-java errored on the tables-vector fixture"; exit 2; }
if [ -n "$TS_PRESENT" ]; then
  node "$TS_DIR/scan.mjs" "$W/tab/ts/cases.ts" "$W/tab/ts_out" >/dev/null 2>&1
  [ -s "$W/tab/ts_out.json" ] || { echo "FAIL: candor-ts errored on the tables-vector fixture"; exit 2; }
fi
SW_TAB=""
if [ -n "$SW_PRESENT" ]; then
  "$SW_BIN" "$W/tab/swift/cases.swift" --out "$W/tab/sw_out" >/dev/null 2>&1
  SW_TAB=$(ls "$W"/tab/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
  [ -n "$SW_TAB" ] && [ -s "$SW_TAB" ] || { echo "FAIL: candor-swift errored on the tables-vector fixture"; exit 2; }
fi
python3 - "$TABVEC" "$TAB_RUST" "$W/tab/java.json" "$W/tab/ts_out.json" "${SW_TAB:-/nonexistent}" <<'PY' || rc=1
import json, os, sys
V = json.load(open(sys.argv[1]))["vectors"]
def by_leaf(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: sorted(e.get("tables", [])) for e in d["functions"]}
rust, java = by_leaf(sys.argv[2], "::"), by_leaf(sys.argv[3], ".")
ts = by_leaf(sys.argv[4], ".") if os.path.exists(sys.argv[4]) else None
sw = by_leaf(sys.argv[5], ".") if len(sys.argv) > 5 and os.path.exists(sys.argv[5]) else None
print("\n[4b] TABLES-EXTRACTION differential  (SPEC §2 — the same SQL must yield the same `tables` in every engine)")
fails = 0
for v in V:
    exp = sorted(v["tables"])
    got = {"rust": rust.get(v["name"], []), "java": java.get(v["name"], [])}
    if ts is not None: got["ts"] = ts.get(v["name"], [])
    if sw is not None: got["swift"] = sw.get(v["name"], [])
    bad = {k: g for k, g in got.items() if g != exp}
    if bad:
        fails += 1
        print(f"  DIVERGE {v['name']}: expected {exp}, " + ", ".join(f"{k}={g}" for k, g in bad.items()))
engines = 2 + (ts is not None) + (sw is not None)
print(f"  -> " + (f"MATCH — {len(V)} vectors, all {engines} engines extract identical tables" if not fails
                  else f"{fails} vector(s) diverge"))
sys.exit(1 if fails else 0)
PY

# ====================================================================================================
# PART 4d — Exec-head differential (SPEC §4 ⟨0.5⟩): a literal that appears only as a subprocess ARGUMENT   [TIER 1]
# is DATA, not the command head. `spawn(dynamicTool, "curl")` must NOT populate `cmds` with "curl" in ANY
# engine — else an `allow Exec curl` gate spuriously certifies a dynamic-head spawn (the verdict-flip the
# adversarial review found in candor-java). Pins every engine: a dynamic head yields NO `cmds` literal.
# ====================================================================================================
mkdir -p "$W/eh/rust/src" "$W/eh/java/q"
cat > "$W/eh/rust/Cargo.toml" <<'EOF'
[package]
name = "eh"
version = "0.0.0"
edition = "2021"
EOF
printf 'pub fn dyn_head(tool: &str) { let _ = std::process::Command::new(tool).arg("curl").spawn(); }\n' > "$W/eh/rust/src/lib.rs"
printf 'package q;\npublic class E { static void dyn_head(String tool) throws Exception { new ProcessBuilder(tool, "curl").start(); } }\n' > "$W/eh/java/q/E.java"
"$SCAN" "$W/eh/rust" >/dev/null 2>&1
EH_RUST="$(ls "$W"/eh/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
javac -d "$W/eh/jout" "$W/eh/java/q/E.java" 2>/dev/null
java -jar "$JAR" "$W/eh/jout" --json "$W/eh/java.json" >/dev/null 2>&1
EH_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  printf 'import { spawn } from "child_process";\nexport function dyn_head(tool: string) { return spawn(tool, ["curl"]); }\n' > "$W/eh/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/eh/cases.ts" "$W/eh/ts_out" >/dev/null 2>&1
  EH_TS="$W/eh/ts_out.json"
fi
python3 - "$EH_RUST" "$W/eh/java.json" "$EH_TS" <<'PY' || rc=1
import json, os, sys
def cmds_of(path, sep):
    d = json.load(open(path))
    for e in d["functions"]:
        if e["fn"].split(sep)[-1] == "dyn_head":
            return e.get("cmds", [])
    return []
print("\n[4d] EXEC-HEAD differential  (SPEC §4 — a dynamic head's argument literal must NOT become `cmds`)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
fails = 0
for name, path, sep in engines:
    cmds = cmds_of(path, sep)
    if "curl" in cmds:   # the argument leaked into the cmds head (the verdict-flip bug)
        fails += 1
        print(f"  DIVERGE {name}: cmds={cmds} — a dynamic head must yield NO cmds literal")
print("  -> " + ("MATCH — no engine extracts a cmds literal from a dynamic subprocess head"
                 if not fails else f"{fails} engine(s) leak the argument into cmds"))
sys.exit(1 if fails else 0)
PY

# ====================================================================================================
# PART 4e — Net host[:port] differential (SPEC §2): every engine must include the statically-known PORT   [TIER 1]
# in the `hosts` surface, not just the host. candor-java once dropped the literal port of a two-arg
# Socket(host, 443) while keeping it for a URL — self-inconsistent and divergent from candor-scan/ts
# (adversarial coverage-gap review, GAP2); candor-swift had its own host:port divergence on NWConnection.
# Each engine (now incl. swift) scans its idiomatic host:port call; all must emit `api.example.com:8080`.
# ====================================================================================================
mkdir -p "$W/nh/rust/src" "$W/nh/java/q"
cat > "$W/nh/rust/Cargo.toml" <<'EOF'
[package]
name = "nh"
version = "0.0.0"
edition = "2021"
EOF
printf 'pub fn h() { let _ = std::net::TcpStream::connect("api.example.com:8080"); }\n' > "$W/nh/rust/src/lib.rs"
printf 'package q;\npublic class N { static void h() throws Exception { new java.net.URL("http://api.example.com:8080/v1").openConnection(); } }\n' > "$W/nh/java/q/N.java"
"$SCAN" "$W/nh/rust" >/dev/null 2>&1
NH_RUST="$(ls "$W"/nh/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
javac -d "$W/nh/jout" "$W/nh/java/q/N.java" 2>/dev/null
java -jar "$JAR" "$W/nh/jout" --json "$W/nh/java.json" >/dev/null 2>&1
NH_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  printf 'import https from "https";\nexport function h() { return https.get("https://api.example.com:8080/v1"); }\n' > "$W/nh/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/nh/cases.ts" "$W/nh/ts_out" >/dev/null 2>&1
  NH_TS="$W/nh/ts_out.json"
fi
NH_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/nh/swift"
  # ⟨0.24⟩ TWO IDIOMS, and the second is why this cell existed without covering anything. PART 4e's four
  # cells are rust `TcpStream::connect`, java `URL(...).openConnection()`, ts `https.get(url)` — three
  # URL-BASED forms — and swift's `NWConnection(host:port:)`, which takes the literal DIRECTLY. swift was
  # the one engine whose cell exercised the shape that already worked, so its ENTIRE URLSession surface
  # could be missing with this row green. Measured 2026-07-29: every `URLSession` form yielded NO hosts,
  # so `deny Net[known-telemetry]` read GREEN over a real telemetry call on Apple-platform code, and
  # `api.openai.com` never classified `Llm`. A single-idiom fixture standing in for a language's whole
  # network surface is not coverage; it is a cell that cannot fail.
  printf 'import Foundation\nimport Network\nfunc h() { _ = NWConnection(host: "api.example.com", port: 8080, using: .tcp) }\nfunc u() { _ = URLSession.shared.dataTask(with: URL(string: "http://api.example.com:8080/v1")!) }\n' > "$W/nh/swift/cases.swift"
  "$SW_BIN" "$W/nh/swift/cases.swift" --out "$W/nh/sw_out" >/dev/null 2>&1
  NH_SW=$(ls "$W"/nh/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
  [ -n "$NH_SW" ] || NH_SW="/nonexistent"
fi
python3 - "$NH_RUST" "$W/nh/java.json" "$NH_TS" "$NH_SW" <<'PY' || rc=1
import json, os, sys
def hosts_of(path, sep):
    d = json.load(open(path))
    for e in d["functions"]:
        if e["fn"].split(sep)[-1] == "h":
            return e.get("hosts", [])
    return []
print("\n[4e] NET HOST[:PORT] differential  (SPEC §2 — the statically-known port is part of the host surface)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4], "."))
fails = 0
for name, path, sep in engines:
    hosts = hosts_of(path, sep)
    if "api.example.com:8080" not in hosts:
        fails += 1
        print(f"  DIVERGE {name}: hosts={hosts} — must include the port (api.example.com:8080)")
print("  -> " + ("MATCH — every engine emits the host:port surface with the literal port"
                 if not fails else f"{fails} engine(s) drop the literal port"))
sys.exit(1 if fails else 0)
PY

# ====================================================================================================
# PART 4m — Llm host-literal differential (SPEC §1 ⟨0.13⟩): a statically-known request to a KNOWN MODEL   [TIER 1]
# HOST classifies `Llm` IN ADDITION to `Net` (Net is never dropped — a model call IS network I/O); an
# UNKNOWN host stays bare `Net`. Each engine scans its idiomatic call to api.anthropic.com + a non-model
# host, from the shared model-host table (candor-spec LLM-EFFECT-DESIGN.md). Reference-led: an engine that
# does NOT yet emit Llm here is SKIPPED, not failed — the rung is pinned across the engines that implement
# it and the floor rises when the last lands (SPEC §Versioning, incremental-proof).
# ====================================================================================================
mkdir -p "$W/llm/rust/src" "$W/llm/java/q"
cat > "$W/llm/rust/Cargo.toml" <<'EOF'
[package]
name = "llm"
version = "0.0.0"
edition = "2021"
EOF
printf 'pub fn chat() { let _ = std::net::TcpStream::connect("api.anthropic.com:443"); }\npub fn other() { let _ = std::net::TcpStream::connect("api.example.com:443"); }\npub fn bedrock() { let _ = std::net::TcpStream::connect("bedrock-runtime.us-east-1.amazonaws.com:443"); }\npub fn s3bucket() { let _ = std::net::TcpStream::connect("bedrock-backups.s3.amazonaws.com:443"); }\npub fn rport() { let _ = std::net::TcpStream::connect("svc.internal.example.com:11434"); }\n' > "$W/llm/rust/src/lib.rs"
printf 'package q;\npublic class L {\n  static void chat() throws Exception { new java.net.URL("https://api.anthropic.com/v1/messages").openConnection().getInputStream(); }\n  static void other() throws Exception { new java.net.URL("https://api.example.com/x").openConnection().getInputStream(); }\n  static void bedrock() throws Exception { new java.net.URL("https://bedrock-runtime.us-east-1.amazonaws.com/x").openConnection().getInputStream(); }\n  static void s3bucket() throws Exception { new java.net.URL("https://bedrock-backups.s3.amazonaws.com/x").openConnection().getInputStream(); }\n  static void rport() throws Exception { new java.net.URL("https://svc.internal.example.com:11434/x").openConnection().getInputStream(); }\n}\n' > "$W/llm/java/q/L.java"
"$SCAN" "$W/llm/rust" >/dev/null 2>&1
LLM_RUST="$(ls "$W"/llm/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
javac -d "$W/llm/jout" "$W/llm/java/q/L.java" 2>/dev/null
java -jar "$JAR" "$W/llm/jout" --json "$W/llm/java.json" >/dev/null 2>&1
LLM_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  printf 'export function chat() { return fetch("https://api.anthropic.com/v1/messages"); }\nexport function other() { return fetch("https://api.example.com/x"); }\nexport function bedrock() { return fetch("https://bedrock-runtime.us-east-1.amazonaws.com/x"); }\nexport function s3bucket() { return fetch("https://bedrock-backups.s3.amazonaws.com/x"); }\nexport function rport() { return fetch("https://svc.internal.example.com:11434/x"); }\n' > "$W/llm/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/llm/cases.ts" "$W/llm/ts_out" >/dev/null 2>&1
  LLM_TS="$W/llm/ts_out.json"
fi
LLM_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/llm/swift"
  printf 'import Foundation\nfunc chat() { _ = URLSession.shared.dataTask(with: "https://api.anthropic.com/v1/messages") { _,_,_ in } }\nfunc other() { _ = URLSession.shared.dataTask(with: "https://api.example.com/x") { _,_,_ in } }\nfunc bedrock() { _ = URLSession.shared.dataTask(with: "https://bedrock-runtime.us-east-1.amazonaws.com/x") { _,_,_ in } }\nfunc s3bucket() { _ = URLSession.shared.dataTask(with: "https://bedrock-backups.s3.amazonaws.com/x") { _,_,_ in } }\nfunc rport() { _ = URLSession.shared.dataTask(with: "https://svc.internal.example.com:11434/x") { _,_,_ in } }\n' > "$W/llm/swift/cases.swift"
  "$SW_BIN" "$W/llm/swift/cases.swift" --out "$W/llm/sw_out" >/dev/null 2>&1
  LLM_SW=$(ls "$W"/llm/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
fi
python3 - "$LLM_RUST" "$W/llm/java.json" "$LLM_TS" "$LLM_SW" <<'PYLLM' || rc=1
import json, sys, os
def eff(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
print("\n[4m] Llm HOST-LITERAL differential  (SPEC §1 ⟨0.13⟩ — model hosts Llm+Net; unknown/s3-bedrock/remote-11434 stay bare Net)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4], "."))
fails = 0; pinned = 0
for name, path, sep in engines:
    e = eff(path, sep)
    chat = e.get("chat", set())
    other = e.get("other", set())
    if "Llm" not in chat and "Llm" not in e.get("bedrock", set()):
        print(f"  {name:6s} -> SKIP (does not yet declare Llm — reference-led rung)")
        continue
    pinned += 1
    bedrock, s3b, rport = e.get("bedrock", set()), e.get("s3bucket", set()), e.get("rport", set())
    checks = {
        "chat":     ("Llm" in chat and "Net" in chat),        # a known model host → Llm+Net
        "bedrock":  ("Llm" in bedrock and "Net" in bedrock),  # the Bedrock RUNTIME endpoint → Llm+Net
        "other":    ("Llm" not in other and "Net" in other),  # an unknown host → bare Net (no fabrication)
        "s3bucket": ("Llm" not in s3b and "Net" in s3b),      # an S3 bucket NAMED bedrock → NOT Llm (fabrication guard)
        "rport":    ("Llm" not in rport and "Net" in rport),  # a remote host on :11434 → NOT Llm (fabrication guard)
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        fails += 1
        print(f"  {name:6s} -> DIVERGE on {bad}  (chat={sorted(chat)} bedrock={sorted(bedrock)} other={sorted(other)} s3bucket={sorted(s3b)} rport={sorted(rport)})")
    else:
        print(f"  {name:6s} -> MATCH  (model hosts Llm+Net; unknown/s3-bedrock/remote-:11434 stay bare Net — no fabrication)")
if pinned == 0:
    print("  -> (no engine declares Llm yet)")
else:
    print("  -> " + ("MATCH — every engine that declares Llm classifies the model host Llm+Net, the unknown host Net"
                     if not fails else f"DIVERGE — {fails} engine(s) disagree"))
sys.exit(1 if fails else 0)
PYLLM

# ====================================================================================================
# PART 4n — SPEC-EXTENSION tolerance (SPEC §2 extensions, §2 forward-compatibility): a report that carries   [TIER 1]
# an EXTENSION effect (candor-swift privacy/1: Location/Camera/…) + the `extensions` envelope field must be
# TOLERATED by every OTHER engine's query loader — the extension effect is an unknown name to them, and a
# consumer MUST ignore unknown fields/effects, never choke. A swift-led ecosystem extension only lands its
# effects in swift; the cross-engine guarantee it needs is that the rest of the family keeps reading its
# reports. Synthetic report (no engine has to implement privacy/1 to prove tolerance).
# ====================================================================================================
mkdir -p "$W/ext"
cat > "$W/ext/report.demo.scan.json" <<'EOF'
{ "meta": { "version": "t", "toolchain": "stable", "spec": "0.23" },
  "extensions": ["privacy/1"],
  "package": "app",
  "functions": [
    { "fn": "app::loc::here", "inferred": ["Location", "Net"], "direct": ["Location"] },
    { "fn": "app::caller", "inferred": ["Location", "Net"], "calls": ["app::loc::here"] } ] }
EOF
cat > "$W/ext/report.JS.json" <<'EOF'
{ "candor": { "version": "t", "toolchain": "node", "spec": "0.23" },
  "extensions": ["privacy/1"], "package": "app",
  "functions": [
    { "fn": "app.loc.here", "inferred": ["Location", "Net"], "direct": ["Location"] },
    { "fn": "app.caller", "inferred": ["Location", "Net"], "calls": ["app.loc.here"] } ] }
EOF
cat > "$W/ext/report.jvm.json" <<'EOF'
{ "candor": { "version": "t", "toolchain": "jdk-21", "spec": "0.23" },
  "extensions": ["privacy/1"], "package": "app",
  "functions": [
    { "fn": "app.Loc.here", "inferred": ["Location", "Net"], "direct": ["Location"] },
    { "fn": "app.caller", "inferred": ["Location", "Net"], "calls": ["app.Loc.here"] } ] }
EOF
echo ""
echo "[4n] SPEC-EXTENSION tolerance  (a privacy/1 report + extensions field is read by every OTHER engine)"
P4N_OK=0
p4n() { echo "     FAIL $1"; P4N_OK=1; }
# The §2 forward-compat guarantee is TOLERATION: an engine that does not know the extension effect must
# still LOAD the report and OPERATE (map/show a known effect) without crashing or rejecting it — never a
# "cannot read report". It is NOT required to SURFACE the unknown effect (rust/ts preserve it as an opaque
# string and can query it; java's typed loader drops it — both compliant; cross-engine SURFACING of
# extension effects is a future enhancement, noted in SPEC-EXTENSION-privacy.md). So the pin is: the
# report is read, `map` answers, and the KNOWN co-effect (Net, present on the same fns) still surfaces.
tolerant() { # $1 label ; $2 report locator ; $3.. query cmd
  "${@:3}" map --report "$2" >/dev/null 2>"$W/ext/err"; local mc=$?
  if [ "$mc" != 0 ]; then p4n "$1: map over an extension report exited $mc (should tolerate + answer)"; return; fi
  case "$(cat "$W/ext/err" 2>/dev/null)" in *"cannot read"*|*"failed to"*|*"could not"*) p4n "$1: rejected the extension report as unreadable";; esac
  # the KNOWN co-effect Net must still surface (proves the report's effect data was read, not dropped whole)
  "${@:3}" where Net --report "$2" --json 2>/dev/null | grep -q "here" || p4n "$1: the known co-effect Net did not surface from an extension report"
}
tolerant "rust" "$W/ext/report.demo.scan.json" "$QUERY"
tolerant "java" "$W/ext/report.jvm.json" java -jar "$JAR"
[ -n "$TS_PRESENT" ] && tolerant "ts" "$W/ext/report" node "$TS_DIR/query.mjs"
if [ "$P4N_OK" = 0 ]; then
  echo "  -> MATCH — every engine tolerates an extension report (loads, answers, the known co-effect surfaces)"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 4o — Llm model-SDK-surface differential (SPEC §1 ⟨0.13⟩): a call into a curated MODEL-PROVIDER   [TIER 1]
# CLIENT classifies `Llm` IN ADDITION to `Net`, the SECOND classification source (distinct from PART 4m's
# host literal) and the one real code most uses. Each engine curates its OWN per-ecosystem SDK surface
# (rust MODEL_SDK_CRATES, java Rules.MODEL_SDK_PACKAGES, ts MODEL_SDK_RE, swift MODEL_SDK_TYPES) — the
# highest DRIFT risk in the rung, so it needs a differential. A plain non-model Net call in the same
# module must stay bare `Net` (the surface is scoped to the curated clients, never bleeds). Reference-led:
# an engine not yet emitting Llm here is SKIPPED, not failed. Fixtures are hermetic (no network, no real
# dependency install) — each engine resolves its own way (rust crate path, java owner package, ts a
# minimal node_modules type stub, swift the imported type name).
# ====================================================================================================
mkdir -p "$W/llmsdk/rust/src" "$W/llmsdk/java/q" "$W/llmsdk/java/dev/langchain4j/model/chat"
cat > "$W/llmsdk/rust/Cargo.toml" <<'EOF'
[package]
name = "llmsdk"
version = "0.0.0"
edition = "2021"
EOF
# rust: a path-qualified call whose crate root is a curated model SDK (async-openai) → Llm+Net; a plain
# reqwest call to a non-model host → Net only (candor-scan resolves both syntactically, no crate built).
printf 'pub fn sdk() { let _ = async_openai::Client::new(); }\npub async fn plain() { let _ = reqwest::get("https://api.example.com/x").await; }\n' > "$W/llmsdk/rust/src/lib.rs"
"$SCAN" "$W/llmsdk/rust" >/dev/null 2>&1
SDK_RUST="$(ls "$W"/llmsdk/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
# java: a call whose bytecode owner is a curated model-SDK package (dev.langchain4j.model.*) → Llm+Net; a
# plain JDK URL fetch to a non-model host → Net only. The langchain4j owner is a compiled stub class.
printf 'package dev.langchain4j.model.chat;\npublic class ChatModel { public String generate(String p) { return p; } }\n' > "$W/llmsdk/java/dev/langchain4j/model/chat/ChatModel.java"
printf 'package q;\nimport dev.langchain4j.model.chat.ChatModel;\npublic class L {\n  static String sdk() { return new ChatModel().generate("hi"); }\n  static void plain() throws Exception { new java.net.URL("https://api.example.com/x").openConnection().getInputStream(); }\n}\n' > "$W/llmsdk/java/q/L.java"
javac -d "$W/llmsdk/jout" "$W/llmsdk/java/dev/langchain4j/model/chat/ChatModel.java" "$W/llmsdk/java/q/L.java" 2>/dev/null
java -jar "$JAR" "$W/llmsdk/jout" --json "$W/llmsdk/java.json" >/dev/null 2>&1
SDK_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  # ts: a call into the curated `openai` package → Llm+Net; a plain fetch to a non-model host → Net only.
  # The package is a minimal hermetic type stub in node_modules (the checker resolves the method chain
  # back to module "openai" without any real install).
  mkdir -p "$W/llmsdk/ts/node_modules/openai"
  printf '{ "name": "openai", "version": "4.0.0", "types": "index.d.ts", "main": "index.js" }\n' > "$W/llmsdk/ts/node_modules/openai/package.json"
  printf 'export default class OpenAI {\n  chat: { completions: { create(body: any): Promise<any> } };\n  constructor(opts?: any);\n}\n' > "$W/llmsdk/ts/node_modules/openai/index.d.ts"
  : > "$W/llmsdk/ts/node_modules/openai/index.js"
  printf 'import OpenAI from "openai";\nconst c = new OpenAI();\nexport async function sdk() { return c.chat.completions.create({ model: "m", messages: [] }); }\nexport function plain() { return fetch("https://api.example.com/x"); }\n' > "$W/llmsdk/ts/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/llmsdk/ts/cases.ts" "$W/llmsdk/ts_out" >/dev/null 2>&1
  SDK_TS="$W/llmsdk/ts_out.json"
fi
SDK_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  # swift: a call constructing/using the curated `OpenAI` type (MacPaw) → Llm+Net; a plain URLSession call
  # to a non-model host → Net only. SwiftSyntax matches the imported type name (guarded against fabrication
  # by the declared/local-types rule — a non-model local type never classifies).
  mkdir -p "$W/llmsdk/swift"
  printf 'import OpenAI\nimport Foundation\nfunc sdk() { let c = OpenAI(apiToken: "x"); _ = c.chats(query: .init(messages: [], model: "m")) }\nfunc plain() { _ = URLSession.shared.dataTask(with: "https://api.example.com/x") { _,_,_ in } }\n' > "$W/llmsdk/swift/cases.swift"
  "$SW_BIN" "$W/llmsdk/swift/cases.swift" --out "$W/llmsdk/sw_out" >/dev/null 2>&1
  SDK_SW=$(ls "$W"/llmsdk/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
fi
python3 - "$SDK_RUST" "$W/llmsdk/java.json" "$SDK_TS" "$SDK_SW" <<'PYSDK' || rc=1
import json, sys, os
def eff(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
print("\n[4o] Llm model-SDK-surface differential  (SPEC §1 ⟨0.13⟩ — a curated model-SDK call is Llm+Net; a plain non-model Net call stays bare Net)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4], "."))
fails = 0; pinned = 0
for name, path, sep in engines:
    e = eff(path, sep)
    sdk = e.get("sdk", set())
    plain = e.get("plain", set())
    if "Llm" not in sdk:
        print(f"  {name:6s} -> SKIP (does not yet declare the Llm model-SDK surface — reference-led rung)")
        continue
    pinned += 1
    checks = {
        "sdk":   ("Llm" in sdk and "Net" in sdk),          # a curated model-SDK client call → Llm+Net
        "plain": ("Llm" not in plain and "Net" in plain),  # a plain non-model Net call → bare Net (no SDK-surface bleed)
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        fails += 1
        print(f"  {name:6s} -> DIVERGE on {bad}  (sdk={sorted(sdk)} plain={sorted(plain)})")
    else:
        print(f"  {name:6s} -> MATCH  (model-SDK call Llm+Net; plain Net call stays bare Net — surface scoped, no bleed)")
if pinned == 0:
    print("  -> (no engine declares the Llm model-SDK surface yet)")
else:
    print("  -> " + ("MATCH — every engine that declares Llm classifies a curated model-SDK call Llm+Net, a plain call Net"
                     if not fails else f"DIVERGE — {fails} engine(s) disagree"))
sys.exit(1 if fails else 0)
PYSDK

# ====================================================================================================
# PART 4p — TOP-LEVEL / INITIALIZER-unit differential (SPEC §2 unitKind ⟨0.14⟩): a MODULE whose top-level   [TIER 1]
# executable code performs an effect must attribute it to an INITIALIZER unit (unitKind "initializer") —
# NEVER an empty/"pure" report. A module-load-time model call (`fetch("https://api.openai.com/…")` at file
# top level, a JVM static initializer) is the cardinal-sin test: it was silently dropped by candor-ts and
# candor-swift (a false all-clear a `deny Llm` gate passed) until the ⟨0.14⟩ fix. Each engine's own unit
# NAME differs (java `<clinit>`, ts `<module>`, swift `<main>`) — the differential keys on the unitKind +
# the effect set, not the name. RUST is N/A: it has no top-level executable code (a `const`/`static` must
# be const-evaluable — no I/O at load), so there is nothing to attribute; it is reported N/A, not skipped.
# ====================================================================================================
mkdir -p "$W/tl/java/q"
# java: a static initializer performing a model call → the <clinit> unit, unitKind "initializer".
printf 'package q;\npublic class T {\n  static { try { new java.net.URL("https://api.openai.com/x").openConnection().getInputStream(); } catch (Exception e) {} }\n}\n' > "$W/tl/java/q/T.java"
javac -d "$W/tl/jout" "$W/tl/java/q/T.java" 2>/dev/null
java -jar "$JAR" "$W/tl/jout" --json "$W/tl/java.json" >/dev/null 2>&1
TL_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  # ts: a bare top-level statement (no wrapping function) doing a model call → the <module> unit.
  printf 'fetch("https://api.openai.com/x");\n' > "$W/tl/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/tl/cases.ts" "$W/tl/ts_out" >/dev/null 2>&1
  TL_TS="$W/tl/ts_out.json"
fi
TL_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  # swift: a bare top-level statement in main.swift doing a model call → the <main> unit.
  mkdir -p "$W/tl/swift"
  printf 'import Foundation\nlet _ = URLSession.shared.dataTask(with: "https://api.openai.com/x") { _,_,_ in }\n' > "$W/tl/swift/main.swift"
  "$SW_BIN" "$W/tl/swift/main.swift" --out "$W/tl/sw_out" >/dev/null 2>&1
  TL_SW=$(ls "$W"/tl/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
fi
python3 - "$W/tl/java.json" "$TL_TS" "$TL_SW" <<'PYTL' || rc=1
import json, sys, os
def initunit(path):
    # return the effect set of the report's INITIALIZER unit (unitKind == "initializer"), or None if the
    # report is empty / has no such unit — the silent-under-report signature.
    d = json.load(open(path))
    fns = d.get("functions", [])
    for e in fns:
        if e.get("unitKind") == "initializer":
            return set(e.get("inferred", []))
    return None
print("\n[4p] TOP-LEVEL / INITIALIZER-unit differential  (SPEC §2 unitKind ⟨0.14⟩ — a module's top-level model call is an initializer unit, never a false-pure empty report)")
print("  rust   -> N/A (no top-level executable code; a const/static is const-evaluated — nothing runs at load)")
engines = [("java", sys.argv[1])]
if os.path.exists(sys.argv[2]): engines.append(("ts", sys.argv[2]))
if len(sys.argv) > 3 and os.path.exists(sys.argv[3]): engines.append(("swift", sys.argv[3]))
fails = 0; pinned = 0
for name, path in engines:
    ic = initunit(path)
    if ic is None:
        # no initializer unit at all: either the engine does not yet model top-level units (reference-led
        # SKIP) OR the cardinal-sin regression (a top-level effect dropped). Distinguish by whether the
        # report is otherwise empty — an empty report here IS the silent under-report we pin against.
        d = json.load(open(path))
        if not d.get("functions"):
            fails += 1
            print(f"  {name:6s} -> DIVERGE  (EMPTY report — a top-level model call was SILENTLY DROPPED, the cardinal sin)")
        else:
            print(f"  {name:6s} -> SKIP (models top-level differently; no initializer unit — reference-led)")
        continue
    pinned += 1
    ok = ("Llm" in ic and "Net" in ic)
    if not ok:
        fails += 1
        print(f"  {name:6s} -> DIVERGE  initializer unit = {sorted(ic)} (want superset of Llm,Net)")
    else:
        print(f"  {name:6s} -> MATCH  (top-level model call → initializer unit Llm+Net)")
if pinned == 0 and not fails:
    print("  -> (no engine models a top-level initializer unit yet)")
else:
    print("  -> " + ("MATCH — every engine attributes a top-level model call to an initializer unit (Llm+Net); none reports false-pure"
                     if not fails else f"DIVERGE — {fails} engine(s) drop or mis-classify the top-level effect"))
sys.exit(1 if fails else 0)
PYTL

# ====================================================================================================
# PART 4q — CONST-INDIRECTED HOST differential (SPEC §1 — a STATICALLY-KNOWN request via a string    [TIER 1]
# CONSTANT resolves the same as an inline literal): real clients put the model host in a `const`/`static`
# and build the URL by interpolation/format (`const API_BASE="https://…"; fetch(`${API_BASE}/x`)`). The
# host IS statically known, so §1 requires the same Llm (and Db / Net-allowlist) refinement as an inline
# literal. candor-java was already sound here (javac inlines `static final String`); the SOURCE-LEVEL
# engines (rust/ts/swift) resolve a literal-valued const at the host arg. A NON-model const host (a CDN)
# must stay bare Net — the fabrication guard: propagation must not paint Llm onto a static non-model host,
# and a runtime/config host stays masked. Reference-led: an engine not yet resolving consts is SKIPPED.
# ====================================================================================================
mkdir -p "$W/ch/rust/src" "$W/ch/java/q"
cat > "$W/ch/rust/Cargo.toml" <<'EOF'
[package]
name = "ch"
version = "0.0.0"
edition = "2021"
EOF
# rust: a model host and a CDN host, each in a const, each used via format!("{}/…", CONST).
printf 'const API_BASE: &str = "https://api.anthropic.com/v1";\nconst CDN: &str = "https://cdn.example.com";\npub async fn chat() { let _ = reqwest::Client::new().post(format!("{}/messages", API_BASE)).send().await; }\npub async fn cdn() { let _ = reqwest::Client::new().post(format!("{}/asset", CDN)).send().await; }\n' > "$W/ch/rust/src/lib.rs"
"$SCAN" "$W/ch/rust" >/dev/null 2>&1
CH_RUST="$(ls "$W"/ch/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
# java: static final String constants (javac inlines them) + concat at the URL.
printf 'package q;\npublic class L {\n  static final String API_BASE = "https://api.anthropic.com/v1";\n  static final String CDN = "https://cdn.example.com";\n  static void chat() throws Exception { new java.net.URL(API_BASE + "/messages").openConnection().getInputStream(); }\n  static void cdn() throws Exception { new java.net.URL(CDN + "/asset").openConnection().getInputStream(); }\n}\n' > "$W/ch/java/q/L.java"
javac -d "$W/ch/jout" "$W/ch/java/q/L.java" 2>/dev/null
java -jar "$JAR" "$W/ch/jout" --json "$W/ch/java.json" >/dev/null 2>&1
CH_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  # ts: a const model host and a const CDN, each used via a `${CONST}/…` template.
  printf 'const API_BASE = "https://api.anthropic.com/v1";\nconst CDN = "https://cdn.example.com";\nexport async function chat() { return fetch(`${API_BASE}/messages`); }\nexport async function cdn() { return fetch(`${CDN}/asset`); }\n' > "$W/ch/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/ch/cases.ts" "$W/ch/ts_out" >/dev/null 2>&1
  CH_TS="$W/ch/ts_out.json"
fi
CH_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  # swift: a global `let` model host and CDN, each used via string interpolation.
  mkdir -p "$W/ch/swift"
  printf 'import Foundation\nlet apiBase = "https://api.anthropic.com/v1"\nlet cdn = "https://cdn.example.com"\nfunc chat() { _ = URLSession.shared.dataTask(with: "\\(apiBase)/messages") { _,_,_ in } }\nfunc cdnCall() { _ = URLSession.shared.dataTask(with: "\\(cdn)/asset") { _,_,_ in } }\n' > "$W/ch/swift/cases.swift"
  "$SW_BIN" "$W/ch/swift/cases.swift" --out "$W/ch/sw_out" >/dev/null 2>&1
  CH_SW=$(ls "$W"/ch/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
fi
python3 - "$CH_RUST" "$W/ch/java.json" "$CH_TS" "$CH_SW" <<'PYCH' || rc=1
import json, sys, os
def eff(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
print("\n[4q] CONST-INDIRECTED HOST differential  (SPEC §1 — a const-anchored model host is Llm+Net like an inline literal; a const CDN host stays bare Net)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4], "."))
fails = 0; pinned = 0
for name, path, sep in engines:
    e = eff(path, sep)
    chat = e.get("chat", set())
    cdn = e.get("cdn", set()) or e.get("cdnCall", set())
    if "Llm" not in chat:
        print(f"  {name:6s} -> SKIP (does not yet resolve a const-indirected host — reference-led)")
        continue
    pinned += 1
    checks = {
        "chat": ("Llm" in chat and "Net" in chat),       # a const-anchored MODEL host → Llm+Net (like inline)
        "cdn":  ("Llm" not in cdn and "Net" in cdn),      # a const-anchored NON-model host → bare Net (no fabrication)
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        fails += 1
        print(f"  {name:6s} -> DIVERGE on {bad}  (chat={sorted(chat)} cdn={sorted(cdn)})")
    else:
        print(f"  {name:6s} -> MATCH  (const model host Llm+Net; const CDN host bare Net — no fabrication)")
if pinned == 0 and not fails:
    print("  -> (no engine resolves const-indirected hosts yet)")
else:
    print("  -> " + ("MATCH — every engine resolves a const-anchored host like an inline literal (model→Llm+Net, CDN→Net)"
                     if not fails else f"DIVERGE — {fails} engine(s) disagree"))
sys.exit(1 if fails else 0)
PYCH

# ====================================================================================================
# PART 4r — LITERAL-HEAD HOST differential (SPEC §1 — a host that is COMPLETE in the literal head of a   [TIER 1]
# composed URL, with interpolation only in the PATH): `fetch(`https://api.anthropic.com/v1/${p}`)` /
# `format!("https://…/{}", p)` / `"https://…/" + p` — the most common real-world URL shape. The host is
# statically known (the authority is terminated by a `/` WITHIN the literal head, before any placeholder),
# so §1 requires the same Llm/Db/Net refinement as an inline literal. The SOUNDNESS BOUNDARY is pinned:
# a SPLIT authority (`https://api.${x}.com/…` — placeholder inside the authority) stays bare Net, and a
# literal-head NON-model host (a CDN) stays bare Net — no fabrication. Reference-led: an engine not yet
# extracting the literal head is SKIPPED. All four extract it (java from the runtime-concat bytecode).
# ====================================================================================================
mkdir -p "$W/lh/rust/src" "$W/lh/java/q"
cat > "$W/lh/rust/Cargo.toml" <<'EOF'
[package]
name = "lh"
version = "0.0.0"
edition = "2021"
EOF
# rust: format! whose format-string literal completes the authority before `{}`; a split authority; a CDN.
printf 'pub async fn chat(p: &str) { let _ = reqwest::Client::new().post(format!("https://api.anthropic.com/v1/{}", p)).send().await; }\npub async fn split(x: &str) { let _ = reqwest::Client::new().post(format!("https://api.{}.com/v1/y", x)).send().await; }\npub async fn cdn(p: &str) { let _ = reqwest::Client::new().post(format!("https://cdn.example.com/v1/{}", p)).send().await; }\n' > "$W/lh/rust/src/lib.rs"
"$SCAN" "$W/lh/rust" >/dev/null 2>&1
LH_RUST="$(ls "$W"/lh/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
# java: runtime string concat whose literal LEFT completes the authority (both javac concat shapes).
printf 'package q;\npublic class L {\n  static void chat(String p) throws Exception { new java.net.URL("https://api.anthropic.com/v1/" + p).openConnection().getInputStream(); }\n  static void split(String x) throws Exception { new java.net.URL("https://api." + x + ".com/v1/y").openConnection().getInputStream(); }\n  static void cdn(String p) throws Exception { new java.net.URL("https://cdn.example.com/v1/" + p).openConnection().getInputStream(); }\n}\n' > "$W/lh/java/q/L.java"
javac -d "$W/lh/jout" "$W/lh/java/q/L.java" 2>/dev/null
java -jar "$JAR" "$W/lh/jout" --json "$W/lh/java.json" >/dev/null 2>&1
LH_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  # ts: a template whose literal head completes the authority; a split authority; a CDN.
  printf 'export async function chat(p: string) { return fetch(`https://api.anthropic.com/v1/${p}`); }\nexport async function split(x: string) { return fetch(`https://api.${x}.com/v1/y`); }\nexport async function cdn(p: string) { return fetch(`https://cdn.example.com/v1/${p}`); }\n' > "$W/lh/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/lh/cases.ts" "$W/lh/ts_out" >/dev/null 2>&1
  LH_TS="$W/lh/ts_out.json"
fi
LH_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  # swift: a string interpolation whose first literal segment completes the authority; split; CDN.
  mkdir -p "$W/lh/swift"
  printf 'import Foundation\nfunc chat(_ p: String) { _ = URLSession.shared.dataTask(with: "https://api.anthropic.com/v1/\\(p)") { _,_,_ in } }\nfunc split(_ x: String) { _ = URLSession.shared.dataTask(with: "https://api.\\(x).com/v1/y") { _,_,_ in } }\nfunc cdn(_ p: String) { _ = URLSession.shared.dataTask(with: "https://cdn.example.com/v1/\\(p)") { _,_,_ in } }\n' > "$W/lh/swift/cases.swift"
  "$SW_BIN" "$W/lh/swift/cases.swift" --out "$W/lh/sw_out" >/dev/null 2>&1
  LH_SW=$(ls "$W"/lh/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
fi
python3 - "$LH_RUST" "$W/lh/java.json" "$LH_TS" "$LH_SW" <<'PYLH' || rc=1
import json, sys, os
def eff(path, sep):
    d = json.load(open(path))
    return {e["fn"].split(sep)[-1]: set(e.get("inferred", [])) for e in d["functions"]}
print("\n[4r] LITERAL-HEAD HOST differential  (SPEC §1 — a host complete in the literal head is Llm+Net like an inline literal; a split authority / CDN head stays bare Net)")
engines = [("rust", sys.argv[1], "::"), ("java", sys.argv[2], ".")]
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3], "."))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4], "."))
fails = 0; pinned = 0
for name, path, sep in engines:
    e = eff(path, sep)
    chat = e.get("chat", set())
    split = e.get("split", set())
    cdn = e.get("cdn", set())
    if "Llm" not in chat:
        print(f"  {name:6s} -> SKIP (does not yet extract a literal-head host — reference-led)")
        continue
    pinned += 1
    checks = {
        "chat":  ("Llm" in chat and "Net" in chat),      # a literal-head MODEL host → Llm+Net (like inline)
        "split": ("Llm" not in split and "Net" in split),# a placeholder INSIDE the authority → bare Net (boundary)
        "cdn":   ("Llm" not in cdn and "Net" in cdn),    # a literal-head NON-model host → bare Net (fabrication guard)
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        fails += 1
        print(f"  {name:6s} -> DIVERGE on {bad}  (chat={sorted(chat)} split={sorted(split)} cdn={sorted(cdn)})")
    else:
        print(f"  {name:6s} -> MATCH  (literal-head model host Llm+Net; split authority + CDN head bare Net — no fabrication)")
if pinned == 0 and not fails:
    print("  -> (no engine extracts a literal-head host yet)")
else:
    print("  -> " + ("MATCH — every engine extracts a host complete in the literal head (model→Llm+Net), never a split authority or CDN"
                     if not fails else f"DIVERGE — {fails} engine(s) disagree"))
sys.exit(1 if fails else 0)
PYLH

# ====================================================================================================
# PART 4s — COVERAGE ENVELOPE differential (SPEC §2 ⟨0.15⟩): the κ-coverage ledger travels WITH   [TIER 1]
# the report — a scan with an UNCOVERED external dep emits `"coverage": {"uncovered": [{"name","calls"}]}`
# naming it, a FULLY-COVERED scan OMITS the field entirely (byte-compatible), the affected function carries
# a per-fn disclosure (`invisible` non-empty OR reads `Unknown` — §2 blesses either), and the --gate-json
# verdict RE-DISCLOSES coverage as a VERDICT-PRESERVING advisory (ok/violations/exit unchanged — the ⟨0.9⟩
# auto-disclosure precedent). Motivation: a report that reads as total lets a downstream verb answer with
# false confidence (the wikipedia-ios privacy-manifest find, SOUNDNESS-LOG 2026-07-15; COVERAGE-DESIGN.md).
# Reference-led: an engine not yet emitting the envelope field is SKIPPED.
# ====================================================================================================
mkdir -p "$W/cov/rust/src" "$W/cov/java/ext" "$W/cov/java/q" "$W/cov/ts/node_modules/somedep" "$W/cov/swift"
# rust: a declared-but-uncovered dep + a covered effectful fn (for the gate leg)
cat > "$W/cov/rust/Cargo.toml" <<'EOF'
[package]
name = "cov"
version = "0.0.0"
edition = "2021"
[dependencies]
somedep = "1"
EOF
printf 'pub fn f() { somedep::do_thing(); }\npub mod api { pub fn hit() { let _ = std::net::TcpStream::connect("h:80"); } }\n' > "$W/cov/rust/src/lib.rs"
"$SCAN" "$W/cov/rust" >/dev/null 2>&1
COV_RUST="$(ls "$W"/cov/rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
printf 'deny Net api\n' > "$W/cov/policy.txt"
CANDOR_POLICY="$W/cov/policy.txt" "$SCAN" "$W/cov/rust" --gate-json "$W/cov/rust_verdict.json" >/dev/null 2>&1
# java: an external package off the scan path + a covered Net fn
printf 'package ext;\npublic class Lib { public static void doThing(){} }\n' > "$W/cov/java/ext/Lib.java"
printf 'package q;\npublic class L {\n  static void f(){ ext.Lib.doThing(); }\n  static void hit() throws Exception { new java.net.URL("https://h.example.com/x").openConnection().getInputStream(); }\n}\n' > "$W/cov/java/q/L.java"
javac -d "$W/cov/jall" "$W/cov/java/ext/Lib.java" "$W/cov/java/q/L.java" 2>/dev/null
mkdir -p "$W/cov/jout/q" && cp "$W/cov/jall/q/L.class" "$W/cov/jout/q/"
java -jar "$JAR" "$W/cov/jout" --json "$W/cov/java.json" >/dev/null 2>&1
printf 'deny Net q\n' > "$W/cov/jpolicy.txt"
java -jar "$JAR" "$W/cov/jout" --policy "$W/cov/jpolicy.txt" --gate-json "$W/cov/java_verdict.json" >/dev/null 2>&1
COV_TS="/nonexistent"; COV_TS_V="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  # ts: a declared+installed-but-uncovered package (typed stub) + a covered Net fn
  printf '{"name":"covts","version":"1.0.0","dependencies":{"somedep":"^1.0.0"}}\n' > "$W/cov/ts/package.json"
  printf '{"name":"somedep","version":"1.0.0","main":"index.js","types":"index.d.ts"}\n' > "$W/cov/ts/node_modules/somedep/package.json"
  printf 'export function doThing(): void;\n' > "$W/cov/ts/node_modules/somedep/index.d.ts"
  : > "$W/cov/ts/node_modules/somedep/index.js"
  printf 'import { doThing } from "somedep";\nexport function f(){ return doThing(); }\n' > "$W/cov/ts/dep.ts"
  printf 'export function hit(){ return fetch("https://h.example.com/x"); }\n' > "$W/cov/ts/api.ts"
  node "$TS_DIR/scan.mjs" "$W/cov/ts" "$W/cov/ts_out" >/dev/null 2>&1
  COV_TS="$W/cov/ts_out.json"
  printf 'deny Net api\n' > "$W/cov/tspolicy.txt"
  node "$TS_DIR/scan.mjs" "$W/cov/ts" --policy "$W/cov/tspolicy.txt" --gate-json "$W/cov/ts_verdict.json" >/dev/null 2>&1
  COV_TS_V="$W/cov/ts_verdict.json"
fi
COV_SW="/nonexistent"; COV_SW_V="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  # swift: an uncovered imported module + a covered Net fn
  printf 'import SomeSDK\nimport Foundation\nfunc f() { SomeSDK.doThing() }\nenum Api { static func hit() { _ = URLSession.shared.dataTask(with: "https://h.example.com/x") { _,_,_ in } } }\n' > "$W/cov/swift/cases.swift"
  "$SW_BIN" "$W/cov/swift/cases.swift" --out "$W/cov/sw_out" >/dev/null 2>&1
  COV_SW=$(ls "$W"/cov/sw_out.*.Swift.json 2>/dev/null | grep -v callgraph | head -1)
  printf 'deny Net Api\n' > "$W/cov/swpolicy.txt"
  "$SW_BIN" "$W/cov/swift/cases.swift" --policy "$W/cov/swpolicy.txt" --gate-json "$W/cov/sw_verdict.json" >/dev/null 2>&1
  COV_SW_V="$W/cov/sw_verdict.json"
fi
python3 - "$COV_RUST" "$W/cov/rust_verdict.json" "$W/cov/java.json" "$W/cov/java_verdict.json" "$COV_TS" "$COV_TS_V" "$COV_SW" "$COV_SW_V" <<'PYCOV' || rc=1
import json, sys, os
def load(p):
    try: return json.load(open(p))
    except Exception: return None
print("\n[4s] COVERAGE ENVELOPE differential  (SPEC §2 ⟨0.15⟩ — the κ ledger travels with the report; the gate re-discloses it verdict-preserving)")
engines = [("rust", sys.argv[1], sys.argv[2]), ("java", sys.argv[3], sys.argv[4])]
if os.path.exists(sys.argv[5]): engines.append(("ts", sys.argv[5], sys.argv[6]))
if os.path.exists(sys.argv[7]): engines.append(("swift", sys.argv[7], sys.argv[8]))
fails = 0; pinned = 0
for name, rp, vp in engines:
    r = load(rp)
    if r is None:
        fails += 1; print(f"  {name:6s} -> DIVERGE (report unreadable)"); continue
    cov = r.get("coverage")
    if cov is None:
        print(f"  {name:6s} -> SKIP (does not yet emit the coverage envelope — reference-led)")
        continue
    pinned += 1
    names = {e.get("name") for e in cov.get("uncovered", [])}
    ok_env = any(("somedep" in n) or ("ext" in n) or ("SomeSDK" in n) for n in names) and \
             all(isinstance(e.get("calls"), int) and e["calls"] >= 1 for e in cov.get("uncovered", []))
    # per-fn disclosure: the dep-calling fn carries invisible OR reads Unknown
    fn_ok = False
    for f in r.get("functions", []):
        inv = f.get("invisible") or []
        if any(("somedep" in i) or ("ext" in i) or ("SomeSDK" in i) for i in inv): fn_ok = True; break
        if "Unknown" in f.get("inferred", []): fn_ok = True
    v = load(vp)
    gate_ok = bool(v) and v.get("ok") is False and len(v.get("violations", [])) >= 1 and \
              isinstance(v.get("coverage"), dict) and v["coverage"].get("uncovered", 0) >= 1
    bad = [k for k, okk in [("envelope", ok_env), ("per-fn", fn_ok), ("gate-advisory", gate_ok)] if not okk]
    if bad:
        fails += 1
        print(f"  {name:6s} -> DIVERGE on {bad}  (cov={json.dumps(cov)[:90]} verdict={json.dumps(v)[:110] if v else None})")
    else:
        print(f"  {name:6s} -> MATCH  (envelope names the uncovered dep; per-fn disclosed; gate verdict ok:false+violations with the coverage advisory)")
if pinned == 0 and not fails:
    print("  -> (no engine emits the coverage envelope yet)")
else:
    print("  -> " + ("MATCH — the κ ledger travels with the report and the gate re-discloses it, verdict-preserving"
                     if not fails else f"DIVERGE — {fails} engine(s) disagree"))
sys.exit(1 if fails else 0)
PYCOV
# 4s-b: the OMISSION leg — a fully-covered scan must NOT carry a coverage key (byte-compat pin)
mkdir -p "$W/cov/pure_rust/src"
printf '[package]\nname = "purecov"\nversion = "0.0.0"\nedition = "2021"\n' > "$W/cov/pure_rust/Cargo.toml"
printf 'pub fn g() { let _ = std::fs::read("/x"); }\n' > "$W/cov/pure_rust/src/lib.rs"
"$SCAN" "$W/cov/pure_rust" >/dev/null 2>&1
PURE_RUST="$(ls "$W"/cov/pure_rust/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
python3 - "$PURE_RUST" <<'PYCOVB' || rc=1
import json, sys
r = json.load(open(sys.argv[1]))
if "coverage" in r:
    print("  [4s-b] rust  -> DIVERGE — a fully-covered scan must OMIT the coverage key"); sys.exit(1)
print("  [4s-b] fully-covered scan omits the coverage key (byte-compat) — MATCH")
PYCOVB

# ====================================================================================================
# PART 4c — coverage ledger differential (SPEC §7 item 14): every engine must NAME an unlisted   [TIER 1]
# external package the scanned code demonstrably calls ("classifier doesn't cover …"), and must NOT name the
# platform/builtin frontier. Package naming is language-natural (crate / java package / npm name);
# what's pinned is the disclosure behavior, not the string values.
# ====================================================================================================
mkdir -p "$W/led/rust/src" "$W/led/java/dep/com/mystery" "$W/led/java/src/org/app" "$W/led/ts/node_modules/mystery-pkg"
cat > "$W/led/rust/Cargo.toml" <<'EOF'
[package]
name = "ledfix"
version = "0.0.0"
edition = "2021"

[dependencies]
mystery_pkg = "1.0"
EOF
cat > "$W/led/rust/src/lib.rs" <<'EOF'
pub fn go() { let _ = std::fs::read("/tmp/x"); let _ = mystery_pkg::do_thing("x"); }
EOF
LED_RUST=$("$SCAN" "$W/led/rust" 2>&1)
cat > "$W/led/java/dep/com/mystery/Util.java" <<'EOF'
package com.mystery;
public class Util { public static String go(String s) { return s; } }
EOF
cat > "$W/led/java/src/org/app/Main.java" <<'EOF'
package org.app;
public class Main {
    public static void run() throws Exception {
        java.nio.file.Files.readString(java.nio.file.Path.of("/tmp/x"));
        com.mystery.Util.go("x");
    }
}
EOF
javac -d "$W/led/java/depcls" "$W/led/java/dep/com/mystery/Util.java" 2>/dev/null
javac -cp "$W/led/java/depcls" -d "$W/led/java/app" "$W/led/java/src/org/app/Main.java" 2>/dev/null
LED_JAVA=$(java -jar "$JAR" "$W/led/java/app" 2>&1)
LED_SW=""
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/led/swift"
  # the fixture must DEMONSTRABLY CALL into MysteryKit (item 14's wording), not merely import it —
  # a module-qualified free-function call keeps the syntactic engine's import-based ledger valid
  # under the spec's stronger call-based reading.
  printf 'import Foundation\nimport MysteryKit\n\nfunc go() { _ = FileManager.default.contents(atPath: "/tmp/x"); _ = MysteryKit.frob("x") }\n' > "$W/led/swift/m.swift"
  LED_SW=$("$SW_BIN" "$W/led/swift" --out "$W/led/swr" 2>&1)
fi
LED_TS=""
if [ -n "$TS_PRESENT" ]; then
  printf '{"name":"mystery-pkg","version":"0.0.0","main":"index.js","types":"index.d.ts"}\n' > "$W/led/ts/node_modules/mystery-pkg/package.json"
  printf 'export declare function doThing(s: string): string;\n' > "$W/led/ts/node_modules/mystery-pkg/index.d.ts"
  printf 'module.exports.doThing = (s) => s;\n' > "$W/led/ts/node_modules/mystery-pkg/index.js"
  cat > "$W/led/ts/cases.ts" <<'EOF'
import { doThing } from "mystery-pkg";
import * as fsm from "node:fs";
export function go(): string { fsm.readFileSync("/tmp/x"); return doThing("x"); }
EOF
  LED_TS=$(node "$TS_DIR/scan.mjs" "$W/led/ts/cases.ts" "$W/led/ledts" 2>&1)
fi
python3 - "$LED_RUST" "$LED_JAVA" "$LED_TS" "$TS_PRESENT" "$LED_SW" "$SW_PRESENT" <<'PY' || rc=1
import sys
rust, java, ts, ts_present = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sw, sw_present = (sys.argv[5], sys.argv[6]) if len(sys.argv) > 6 else ("", "")
print("\n[4c] COVERAGE LEDGER differential  (SPEC §7 item 14 — unlisted-but-called packages are NAMED)")
ok = True
def check(name, out, pkg, frontier):
    global ok
    named = "classifier doesn't cover" in out and pkg in out
    quiet = frontier not in out
    print(f"  {name:12s} -> {'MATCH' if named and quiet else 'DIVERGE'}"
          + ("" if named else f" (did not name {pkg})") + ("" if quiet else f" (named the frontier {frontier})"))
    ok = ok and named and quiet
check("candor-scan", rust, "mystery_pkg", "std")
check("candor-java", java, "com.mystery", "java.nio")
if ts_present:
    check("candor-ts", ts, "mystery-pkg", "node:fs")
if sw_present:
    check("candor-swift", sw, "MysteryKit", "Foundation")
print("  -> " + ("MATCH — every engine disclosed the blind spot and stayed quiet about the frontier"
                 if ok else "DIVERGE — a ledger is missing or over-disclosing"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 4f — SURFACE-BEST-FIND differential (the cold-repo "most surprising reach" opener): every engine   [TIER 2]
# ends a scan by surfacing the SAME single most-surprising transitive reach on a shared fixture — a
# benign-named function (`Settings::load`) inheriting Fs three hops away via a `read` source in another
# module. The heuristic is pure call-graph + name analysis, so a parallel fixture MUST yield the same
# winner in every language: the disclosure line `candor: most surprising reach — … load … Fs`. Pins that
# the opener is consistent per engine (SURFACE-BEST-FIND-DESIGN.md P3), not that it's clever.
# ====================================================================================================
mkdir -p "$W/surf/rust/src" "$W/surf/ts" "$W/surf/java/src/app"
cat > "$W/surf/rust/Cargo.toml" <<'EOF'
[package]
name = "surffix"
version = "0.0.0"
edition = "2021"
EOF
cat > "$W/surf/rust/src/lib.rs" <<'EOF'
pub struct Settings;
impl Settings { pub fn load() -> bool { refresh() } }
fn refresh() -> bool { compute() }
fn compute() -> bool { io_read_thing() }
pub fn io_read_thing() -> bool { std::fs::read("/tmp/x").is_ok() }
EOF
SURF_RUST=$("$SCAN" "$W/surf/rust" 2>&1)
cat > "$W/surf/java/src/app/Settings.java" <<'EOF'
package app;
public class Settings { public static boolean load() { return Chain.refresh(); } }
EOF
cat > "$W/surf/java/src/app/Chain.java" <<'EOF'
package app;
public class Chain { public static boolean refresh() { return compute(); } static boolean compute() { return Io.readThing(); } }
EOF
cat > "$W/surf/java/src/app/Io.java" <<'EOF'
package app;
public class Io { public static boolean readThing() { try { java.nio.file.Files.readString(java.nio.file.Path.of("/tmp/x")); } catch (Exception e) {} return true; } }
EOF
javac -d "$W/surf/java/app" $(find "$W/surf/java/src" -name '*.java') 2>/dev/null
SURF_JAVA=$(java -jar "$JAR" "$W/surf/java/app" 2>&1)
SURF_TS=""
if [ -n "$TS_PRESENT" ]; then
  cat > "$W/surf/ts/cases.ts" <<'EOF'
import * as fsm from "node:fs";
class Settings { static load(): boolean { return refresh(); } }
function refresh(): boolean { return compute(); }
function compute(): boolean { return ioReadThing(); }
export function ioReadThing(): boolean { fsm.readFileSync("/tmp/x"); return true; }
export { Settings };
EOF
  SURF_TS=$(node "$TS_DIR/scan.mjs" "$W/surf/ts/cases.ts" "$W/surf/tsout" 2>&1)
fi
SURF_SW=""
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/surf/swift"
  printf 'import Foundation\nstruct Settings { static func load() -> Bool { return refresh() } }\nfunc refresh() -> Bool { return compute() }\nfunc compute() -> Bool { return ioReadThing() }\nfunc ioReadThing() -> Bool { _ = FileManager.default.contents(atPath: "/tmp/x"); return true }\n' > "$W/surf/swift/m.swift"
  SURF_SW=$("$SW_BIN" "$W/surf/swift" --out "$W/surf/swout" 2>&1)
fi
python3 - "$SURF_RUST" "$SURF_JAVA" "$SURF_TS" "$TS_PRESENT" "$SURF_SW" "$SW_PRESENT" <<'PY' || rc=1
import sys
rust, java, ts, ts_present = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sw, sw_present = sys.argv[5], sys.argv[6]
print("\n[4f] SURFACE-BEST-FIND differential  (the cold-repo opener names the SAME surprising reach)")
ok = True
def check(name, out):
    global ok
    # the marker + the benign winner (`load`) + the effect (Fs). Language-natural qual all contain "load".
    hit = "most surprising reach" in out and "load" in out and "Fs" in out
    print(f"  {name:12s} -> {'MATCH' if hit else 'DIVERGE'}"
          + ("" if hit else "  (did not surface `load` reaching Fs as the opener)"))
    ok = ok and hit
check("candor-scan", rust)
check("candor-java", java)
if ts_present:
    check("candor-ts", ts)
if sw_present:
    check("candor-swift", sw)
print("  -> " + ("MATCH — every engine's opener names the same benign→Fs reach"
                 if ok else "DIVERGE — an engine surfaced a different opener (or none)"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 4g — SURFACE TOUR differential (`candor tour`): the on-demand top-N query names the SAME opener as   [TIER 2]
# the scan-time note. Reuses the PART 4f fixtures (benign `Settings::load` inheriting Fs three hops via a
# `read` source in another module): scan each into a report, run `tour --json`, and assert every engine's
# top reach is `…load…` performing Fs — so the guided-poke verb is consistent per engine too.
# ====================================================================================================
"$SCAN" "$W/surf/rust" >/dev/null 2>&1
TOUR_RUST=$("$QUERY" tour --report "$W/surf/rust/.candor/report" --json 2>/dev/null)
java -jar "$JAR" "$W/surf/java/app" --json "$W/surf/jrep.json" >/dev/null 2>&1
TOUR_JAVA=$(java -jar "$JAR" tour --report "$W/surf/jrep.json" --json 2>/dev/null)
TOUR_TS=""
if [ -n "$TS_PRESENT" ]; then
  node "$TS_DIR/scan.mjs" "$W/surf/ts/cases.ts" "$W/surf/tsrep" >/dev/null 2>&1
  TOUR_TS=$(node "$TS_DIR/query.mjs" tour --report "$W/surf/tsrep" --json 2>/dev/null)
fi
TOUR_SW=""
if [ -n "$SW_PRESENT" ]; then
  env -u CANDOR_CONFIG "$SW_BIN" "$W/surf/swift" --out "$W/surf/swrep" >/dev/null 2>&1
  TOUR_SW=$(env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/surf/swrep" --json 2>/dev/null)
fi
python3 - "$TOUR_RUST" "$TOUR_JAVA" "$TOUR_TS" "$TS_PRESENT" "$TOUR_SW" "$SW_PRESENT" <<'PY' || rc=1
import json, sys
rust, java, ts, ts_present = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sw, sw_present = sys.argv[5], sys.argv[6]
print("\n[4g] SURFACE TOUR differential  (`candor tour` names the same top reach as the scan opener)")
ok = True
def check(name, out):
    global ok
    try:
        reaches = json.loads(out).get("reaches", [])
        top = reaches[0] if reaches else {}
        hit = "load" in top.get("fn", "") and top.get("effect") == "Fs"
    except Exception:
        hit = False
    print(f"  {name:12s} -> {'MATCH' if hit else 'DIVERGE'}"
          + ("" if hit else "  (tour's top reach is not `load` performing Fs)"))
    ok = ok and hit
check("candor-scan", rust)
check("candor-java", java)
if ts_present:
    check("candor-ts", ts)
if sw_present:
    check("candor-swift", sw)
print("  -> " + ("MATCH — `candor tour` surfaces the same top reach in every engine"
                 if ok else "DIVERGE — an engine's tour ranks a different top reach (or has no tour)"))
sys.exit(0 if ok else 1)
PY

# 4g addendum — the PLURAL `packages` envelope (SPEC §2's JVM shape, which candor-java's own scan emits)
# must feed the tour header in EVERY engine: several packages name their longest common dotted prefix.
# Dogfood find: java's tour on its own multi-package report printed the raw FILENAME because every
# engine's reportPackage read only the singular `package`. Fixture: packages ["com.a.x","com.a.y"] →
# the header must say "in com.a:" (each engine gets its own qual-shaped functions so the reach surfaces).
mkdir -p "$W/plural"
plural_hdr() { # $1 label ; $2 locator ; $3.. cmd — asserts the human header names the common prefix
  hdr="$( "${@:3}" tour --report "$2" 2>/dev/null | head -1 )"
  case "$hdr" in *"in com.a:"*) ;; *) echo "     FAIL $1: tour header did not name the packages' common prefix (got: ${hdr:0:80})"; return 1;; esac
}
P4G2_OK=0
printf '%s' '{ "meta": {"version":"t","toolchain":"stable","spec": "0.23"}, "packages": ["com.a.x","com.a.y"], "functions": [ {"fn":"settings::Settings::load","inferred":["Fs"],"calls":["io::write_file"]}, {"fn":"io::write_file","loc":"src/io.rs:3","inferred":["Fs"],"direct":["Fs"]} ] }' > "$W/plural/r.demo.scan.json"
plural_hdr rust "$W/plural/r" "$QUERY" || P4G2_OK=1
printf '%s' '{ "candor": {"version":"t","spec": "0.23"}, "packages": ["com.a.x","com.a.y"], "functions": [ {"fn":"com.a.x.Settings.load","inferred":["Fs"],"calls":["com.a.y.Disk.writeFile"]}, {"fn":"com.a.y.Disk.writeFile","loc":"Disk.java:3","inferred":["Fs"],"direct":["Fs"]} ] }' > "$W/plural/j.jvm.json"
plural_hdr java "$W/plural/j.jvm.json" java -jar "$JAR" || P4G2_OK=1
if [ -n "$TS_PRESENT" ]; then
  printf '%s' '{ "candor": {"version":"t","spec": "0.23"}, "packages": ["com.a.x","com.a.y"], "functions": [ {"fn":"com_a.Settings.load","inferred":["Fs"],"calls":["com_a.io.writeFile"]}, {"fn":"com_a.io.writeFile","loc":"src/io.ts:3","inferred":["Fs"],"direct":["Fs"]} ] }' > "$W/plural/t.JS.json"
  plural_hdr ts "$W/plural/t" node "$TS_DIR/query.mjs" || P4G2_OK=1
fi
if [ -n "$SW_PRESENT" ]; then
  printf '%s' '{ "candor": {"version":"t","spec": "0.23"}, "packages": ["com.a.x","com.a.y"], "functions": [ {"fn":"Settings.load","inferred":["Fs"],"calls":["Disk.writeFile"]}, {"fn":"Disk.writeFile","loc":"Sources/Disk.swift:3","inferred":["Fs"],"direct":["Fs"]} ] }' > "$W/plural/s.Swift.json"
  plural_hdr swift "$W/plural/s" env -u CANDOR_CONFIG "$SW_BIN" || P4G2_OK=1
fi
if [ "$P4G2_OK" = 0 ]; then
  echo "  -> MATCH — every engine's tour header honours the plural packages envelope (common prefix)"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 4h — SURFACE TOUR robustness (the review's cardinal-sin fixes): `tour 0` must FAIL LOUD (exit 2),    [TIER 2]
# not print a false "nothing hidden"; and with the callgraph sidecar DELETED, tour must STILL surface the
# reach by falling back to the report's inline `calls` — never silently drop to zero reaches. Reuses the
# PART 4g reports (each engine already scanned its surf fixture above).
# ====================================================================================================
echo ""
echo "[4h] SURFACE TOUR robustness  (tour 0 → exit 2; a deleted callgraph sidecar still surfaces via inline calls)"
P4H_OK=0
p4h() { echo "     FAIL $1"; P4H_OK=1; }
n0() { ( "$@" ) >/dev/null 2>&1; [ "$?" = 2 ]; }
n0 "$QUERY" tour 0 --report "$W/surf/rust/.candor/report"       || p4h "rust: tour 0 must exit 2 (false all-clear otherwise)"
n0 java -jar "$JAR" tour 0 --report "$W/surf/jrep.json"         || p4h "java: tour 0 must exit 2"
[ -n "$TS_PRESENT" ] && { n0 node "$TS_DIR/query.mjs" tour 0 --report "$W/surf/tsrep"      || p4h "ts: tour 0 must exit 2"; }
[ -n "$SW_PRESENT" ] && { n0 env -u CANDOR_CONFIG "$SW_BIN" tour 0 --report "$W/surf/swrep" || p4h "swift: tour 0 must exit 2"; }
# Delete every callgraph sidecar next to the surf reports, then re-run tour: it must fall back to inline calls.
rm -f "$W"/surf/rust/.candor/report.*.callgraph.json "$W"/surf/jrep*.callgraph.json \
      "$W"/surf/tsrep*.callgraph.json "$W"/surf/swrep*.callgraph.json 2>/dev/null
nosidecar() { # $1 label ; $2 tour --json output (sidecar deleted)
  python3 -c 'import json,sys
r=json.loads(sys.argv[1] or "{}").get("reaches",[])
sys.exit(0 if r and "load" in r[0].get("fn","") and r[0].get("effect")=="Fs" else 1)' "$2" 2>/dev/null \
    || p4h "$1: tour dropped all reaches with the callgraph sidecar deleted (silent under-report)"
}
nosidecar rust  "$("$QUERY" tour --report "$W/surf/rust/.candor/report" --json 2>/dev/null)"
nosidecar java  "$(java -jar "$JAR" tour --report "$W/surf/jrep.json" --json 2>/dev/null)"
[ -n "$TS_PRESENT" ] && nosidecar ts    "$(node "$TS_DIR/query.mjs" tour --report "$W/surf/tsrep" --json 2>/dev/null)"
[ -n "$SW_PRESENT" ] && nosidecar swift "$(env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/surf/swrep" --json 2>/dev/null)"
if [ "$P4H_OK" = 0 ]; then
  echo "  -> MATCH — every engine rejects N=0 and survives a missing sidecar without a false all-clear"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 4l — SURFACE mostly-Unknown qualification (re-audit cardinal sin): when ≥⅓ of effectful functions    [TIER 2]
# are Unknown (unresolved calls — a missing tsconfig / unresolvable imports silently degrade the graph to
# no-transitive-analysis) AND nothing surprising clears the bar, tour must NOT print the reassuring
# "nothing hidden" — that is a FALSE all-clear over a graph whose Unknowns ARE the hidden part. Every engine
# instead qualifies (names the Unknown count + `candor blindspots`). Four-way. A mostly-Unknown report has 2
# Unknown + 1 Fs leaf (nothing surprising), so the fallback fires — but the Unknown fraction (⅔) trips the guard.
# ====================================================================================================
echo ""
echo "[4l] SURFACE mostly-Unknown qualification  (never a false 'nothing hidden' over a ≥⅓-Unknown graph)"
P4L_OK=0
p4l() { echo "     FAIL $1"; P4L_OK=1; }
MU='{"candor":{"version":"t","toolchain":"stable","spec":"0.23"},"package":"mu","functions":[{"fn":"a.loadA","inferred":["Unknown"],"unknownWhy":["dispatch:x"]},{"fn":"a.loadB","inferred":["Unknown"],"unknownWhy":["dispatch:y"]},{"fn":"db.query","inferred":["Fs"],"direct":["Fs"]}]}'
mkdir -p "$W/mu"
qual() { # $1 label ; $2… command — output must qualify with the RIGHT counts, not the false "nothing hidden"
  local out; out="$("${@:2}" 2>&1)"
  case "$out" in
    *"nothing hidden"*) p4l "$1: printed the FALSE 'nothing hidden' over a ⅔-Unknown graph";;
    # Pin the COUNTS (2 Unknown of 3 effectful), not just the shape — an engine miscounting the Unknown
    # fraction would still qualify-with-wrong-numbers and pass a shape-only check (Fable-review finding F5).
    *"2 of 3"*"are Unknown"*blindspots*) ;;              # OK — qualified with the right counts
    *"are Unknown"*blindspots*) p4l "$1: qualified but with the WRONG counts (want '2 of 3'), got: ${out:0:80}";;
    *) p4l "$1: did not qualify (want '2 of 3 … are Unknown … blindspots'), got: ${out:0:70}";;
  esac
}
printf '%s' "$MU" > "$W/mu/r.mu.scan.json"; qual "rust tour"  "$QUERY" tour --report "$W/mu/r.mu.scan.json"
printf '%s' "$MU" > "$W/mu/j.jvm.json";     qual "java tour"  java -jar "$JAR" tour --report "$W/mu/j.jvm.json"
[ -n "$TS_PRESENT" ] && { printf '%s' "$MU" > "$W/mu/t.json";       qual "ts tour"    node "$TS_DIR/query.mjs" tour --report "$W/mu/t.json"; }
[ -n "$SW_PRESENT" ] && { printf '%s' "$MU" > "$W/mu/s.Swift.json"; qual "swift tour" env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/mu/s.Swift.json"; }
# The MACHINE half (Fable-review finding E): `tour --json` over the same ⅔-Unknown report must NOT be a bare
# `{"reaches":[]}` a consumer reads as clean — it carries the additive `"unknown":{"count":2,"total":3}`
# disclosure, byte-identical four-way (2 Unknown of 3 effectful).
qualj() { # $1 label ; $2… command — the --json output must carry the unknown disclosure with the right counts
  local out; out="$("${@:2}" 2>/dev/null)"
  case "$out" in
    *'"unknown":{"count":2,"total":3}'*) ;;             # OK — additive disclosure, right counts, sorted keys
    *) p4l "$1 --json: missing/!=  \"unknown\":{\"count\":2,\"total\":3} (a JSON consumer reads {reaches:[]} as clean), got: ${out:0:90}";;
  esac
}
qualj "rust tour"  "$QUERY" tour --report "$W/mu/r.mu.scan.json" --json
qualj "java tour"  java -jar "$JAR" tour --report "$W/mu/j.jvm.json" --json
[ -n "$TS_PRESENT" ] && qualj "ts tour"    node "$TS_DIR/query.mjs" tour --report "$W/mu/t.json" --json
[ -n "$SW_PRESENT" ] && qualj "swift tour" env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/mu/s.Swift.json" --json
if [ "$P4L_OK" = 0 ]; then
  echo "  -> MATCH — no engine reassures 'nothing hidden' over a mostly-Unknown graph"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 4k — SURFACE TOUR corrupt-report loudness (dogfood find, candor-rust/java/ts): a report that is     [TIER 2]
# FOUND but yields NO trustworthy functions must make `tour` exit NON-ZERO with the corruption DISCLOSED —
# never print "nothing hidden" (a §4 cardinal-sin false all-clear over corrupt input). Two corruption
# shapes, because they exposed DIFFERENT engines: (a) SYNTACTIC — a truncated/unparseable envelope (rust
# +ts returned []→"nothing hidden"; java/swift already loud); (b) SEMANTIC — a valid-JSON but wrong-shape
# report, a bare `[1,2,3]` array whose entries are all junk (rust+java parsed it as a legacy array, dropped
# every entry, and read the empty result as all-clear; ts/swift already loud). The COMPLEMENT pins the
# other side: a WELL-FORMED empty `functions: []` report is NOT corrupt and must exit 0 (never over-fire).
# Teeth: (a) corrupts a COPY of each engine's real surf report (PART 4g proved a valid one surfaces a
# reach); (b)/(complement) write standalone report files each engine's --report discovers.
# ====================================================================================================
echo ""
echo "[4k] SURFACE TOUR corrupt-report loudness  (a found-but-untrustworthy report → exit ≠0, disclosed, never 'nothing hidden')"
P4K_OK=0
p4k() { echo "     FAIL $1"; P4K_OK=1; }
TRUNC='{ "candor": {}, "functions": [ { "fn": "x.'   # (a) a truncated envelope — valid prefix, unparseable
JUNK_ARR='[1, 2, 3]'                                  # (b) a bare array whose entries are all junk (no `fn`)
# $1 label ; $2 report locator ; $3.. cmd  — asserts exit≠0 AND stdout has no "nothing hidden" all-clear
# AND stderr discloses the corruption (proving the report was found + rejected, not merely missing).
loud_corrupt() {
  out="$( "${@:3}" tour --report "$2" 2>"$W/4k.err" )"; code=$?
  err="$(cat "$W/4k.err" 2>/dev/null)"
  if [ "$code" = 0 ]; then p4k "$1: tour exited 0 over a corrupt report (false all-clear)"; return; fi
  case "$out" in *"nothing hidden"*) p4k "$1: tour printed 'nothing hidden' over a corrupt report"; return;; esac
  case "$err" in *parse*|*OMITTED*|*malformed*|*MalformedJson*|*"could not"*|*"no usable"*|*"failed to load"*) ;; *) p4k "$1: corruption not disclosed on stderr (err=${err:0:80})";; esac
}
# $1 label ; $2 report locator ; $3.. cmd — the COMPLEMENT: a well-formed EMPTY report must exit 0.
clean_empty_ok() {
  "${@:3}" tour --report "$2" >/dev/null 2>&1
  [ "$?" = 0 ] || p4k "$1: a well-formed empty report did NOT exit 0 (loud rule over-fires on a valid empty report)"
}
mkdir -p "$W/corrupt/rust/.candor"
# (a) SYNTACTIC — corrupt a copy of each engine's surf report so discovery finds it and the PARSE fails.
for f in "$W"/surf/rust/.candor/report.*.scan.json; do [ -e "$f" ] && printf '%s' "$TRUNC" > "$W/corrupt/rust/.candor/$(basename "$f")"; done
loud_corrupt "rust  (syntactic)" "$W/corrupt/rust/.candor/report" "$QUERY"
printf '%s' "$TRUNC" > "$W/corrupt/jrep.jvm.json";  loud_corrupt "java  (syntactic)" "$W/corrupt/jrep.jvm.json" java -jar "$JAR"
[ -n "$TS_PRESENT" ] && { printf '%s' "$TRUNC" > "$W/corrupt/tsrep.JS.json";     loud_corrupt "ts    (syntactic)" "$W/corrupt/tsrep" node "$TS_DIR/query.mjs"; }
[ -n "$SW_PRESENT" ] && { printf '%s' "$TRUNC" > "$W/corrupt/swrep.Swift.json";  loud_corrupt "swift (syntactic)" "$W/corrupt/swrep" env -u CANDOR_CONFIG "$SW_BIN"; }
# (b) SEMANTIC — a valid-JSON bare junk array. Standalone report files (report-glob names per engine).
printf '%s' "$JUNK_ARR" > "$W/corrupt/rj.demo.scan.json"; loud_corrupt "rust  (semantic)" "$W/corrupt/rj" "$QUERY"
printf '%s' "$JUNK_ARR" > "$W/corrupt/jj.jvm.json";       loud_corrupt "java  (semantic)" "$W/corrupt/jj.jvm.json" java -jar "$JAR"
[ -n "$TS_PRESENT" ] && { printf '%s' "$JUNK_ARR" > "$W/corrupt/tj.JS.json";    loud_corrupt "ts    (semantic)" "$W/corrupt/tj" node "$TS_DIR/query.mjs"; }
[ -n "$SW_PRESENT" ] && { printf '%s' "$JUNK_ARR" > "$W/corrupt/sj.Swift.json"; loud_corrupt "swift (semantic)" "$W/corrupt/sj" env -u CANDOR_CONFIG "$SW_BIN"; }
# COMPLEMENT — a well-formed empty report must NOT trip the loud rule (exit 0, parity across engines).
EMPTY='{ "candor": { "version": "conf" }, "functions": [] }'
printf '%s' "$EMPTY" > "$W/corrupt/re.demo.scan.json"; clean_empty_ok "rust  (clean-empty)" "$W/corrupt/re" "$QUERY"
printf '%s' "$EMPTY" > "$W/corrupt/je.jvm.json";       clean_empty_ok "java  (clean-empty)" "$W/corrupt/je.jvm.json" java -jar "$JAR"
[ -n "$TS_PRESENT" ] && { printf '%s' "$EMPTY" > "$W/corrupt/te.JS.json";    clean_empty_ok "ts    (clean-empty)" "$W/corrupt/te" node "$TS_DIR/query.mjs"; }
[ -n "$SW_PRESENT" ] && { printf '%s' "$EMPTY" > "$W/corrupt/se.Swift.json"; clean_empty_ok "swift (clean-empty)" "$W/corrupt/se" env -u CANDOR_CONFIG "$SW_BIN"; }
if [ "$P4K_OK" = 0 ]; then
  echo "  -> MATCH — every engine fails loud on a corrupt report (syntactic + semantic), none over-fires on a valid empty one"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 4i — SURFACE test-code exclusion: a benign-named function IN A TEST CONTEXT (each engine's idiom —   [TIER 2]
# a Rust `mod tests`, a Java `.tests.` package, a TS `*.test.ts` file, a Swift `*Tests` type) that inherits
# Fs must NEVER be surfaced as a reach — the scan-note/tour point at real code, not test scaffolding.
# ====================================================================================================
mkdir -p "$W/surft/rust/src" "$W/surft/java/src/app/tests"
printf '[package]\nname = "surftfix"\nversion = "0.0.0"\nedition = "2021"\n' > "$W/surft/rust/Cargo.toml"
cat > "$W/surft/rust/src/lib.rs" <<'EOF'
pub fn reader() -> bool { std::fs::read("/tmp/x").is_ok() }
pub mod tests { pub fn load() -> bool { crate::reader() } }
EOF
"$SCAN" "$W/surft/rust" >/dev/null 2>&1
TX_RUST=$("$QUERY" tour --report "$W/surft/rust/.candor/report" --json 2>/dev/null)
cat > "$W/surft/java/src/app/Reader.java" <<'EOF'
package app;
public class Reader { public static boolean read() { try { java.nio.file.Files.readString(java.nio.file.Path.of("/tmp/x")); } catch (Exception e) {} return true; } }
EOF
cat > "$W/surft/java/src/app/tests/Data.java" <<'EOF'
package app.tests;
public class Data { public static boolean load() { return app.Reader.read(); } }
EOF
javac -d "$W/surft/java/app" $(find "$W/surft/java/src" -name '*.java') 2>/dev/null
java -jar "$JAR" "$W/surft/java/app" --json "$W/surft/jrep.json" >/dev/null 2>&1
TX_JAVA=$(java -jar "$JAR" tour --report "$W/surft/jrep.json" --json 2>/dev/null)
TX_TS=""
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/surft/ts"
  printf 'import * as fsm from "node:fs";\nexport function reader(): boolean { fsm.readFileSync("/tmp/x"); return true; }\n' > "$W/surft/ts/reader.ts"
  printf 'import { reader } from "./reader";\nexport function load(): boolean { return reader(); }\n' > "$W/surft/ts/cases.test.ts"
  node "$TS_DIR/scan.mjs" "$W/surft/ts" "$W/surft/tsrep" >/dev/null 2>&1
  TX_TS=$(node "$TS_DIR/query.mjs" tour --report "$W/surft/tsrep" --json 2>/dev/null)
fi
TX_SW=""
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/surft/swift"
  printf 'import Foundation\nfunc reader() -> Bool { _ = FileManager.default.contents(atPath: "/tmp/x"); return true }\nstruct DataTests { static func load() -> Bool { return reader() } }\n' > "$W/surft/swift/m.swift"
  env -u CANDOR_CONFIG "$SW_BIN" "$W/surft/swift" --out "$W/surft/swrep" >/dev/null 2>&1
  TX_SW=$(env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/surft/swrep" --json 2>/dev/null)
fi
python3 - "$TX_RUST" "$TX_JAVA" "$TX_TS" "$TS_PRESENT" "$TX_SW" "$SW_PRESENT" <<'PY' || rc=1
import json, sys
rust, java, ts, ts_present = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sw, sw_present = sys.argv[5], sys.argv[6]
print("\n[4i] SURFACE test-code exclusion  (a benign test-context reach is NEVER surfaced)")
ok = True
def check(name, out):
    global ok
    # An EMPTY capture (engine crashed, exited loud, or the scan step failed) must be a DIVERGE —
    # json.loads("{}") would otherwise read as an empty reach list and pass the very check the part
    # exists to run (a fail-open oracle; max-review find).
    if not (out or "").strip():
        print(f"  {name:12s} -> DIVERGE  (no tour output — the engine crashed or the fixture scan failed)")
        ok = False
        return
    try:
        reaches = json.loads(out).get("reaches", [])
        excluded = not any("load" in r.get("fn", "") for r in reaches)
    except Exception:
        excluded = False
    print(f"  {name:12s} -> {'MATCH' if excluded else 'DIVERGE'}"
          + ("" if excluded else "  (surfaced the test-context `load` — test-code not excluded)"))
    ok = ok and excluded
check("candor-scan", rust)
check("candor-java", java)
if ts_present:
    check("candor-ts", ts)
if sw_present:
    check("candor-swift", sw)
print("  -> " + ("MATCH — every engine excludes the test-context reach"
                 if ok else "DIVERGE — an engine surfaced test scaffolding as a reach"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 4j — SURFACE salience floor (corpus-dogfood refinement): a benign function whose ONLY reach is a     [TIER 2]
# mundane effect (Clock/Log/Rand — salience 0) must NOT be surfaced as "the most surprising reach"; the
# engine reports "nothing hidden" honestly instead of over-promising. Only Net/Exec/Db/Ipc/Fs/Env surface.
# ====================================================================================================
mkdir -p "$W/surfc/rust/src" "$W/surfc/java/src/app"
printf '[package]\nname = "surfcfix"\nversion = "0.0.0"\nedition = "2021"\n' > "$W/surfc/rust/Cargo.toml"
cat > "$W/surfc/rust/src/lib.rs" <<'EOF'
pub struct Settings;
impl Settings { pub fn load() -> u128 { stamp() } }
fn stamp() -> u128 { std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis() }
EOF
"$SCAN" "$W/surfc/rust" >/dev/null 2>&1
TC_RUST=$("$QUERY" tour --report "$W/surfc/rust/.candor/report" --json 2>/dev/null)
cat > "$W/surfc/java/src/app/Settings.java" <<'EOF'
package app;
public class Settings { public static long load() { return Clock.stamp(); } }
EOF
cat > "$W/surfc/java/src/app/Clock.java" <<'EOF'
package app;
public class Clock { public static long stamp() { return System.currentTimeMillis(); } }
EOF
javac -d "$W/surfc/java/app" $(find "$W/surfc/java/src" -name '*.java') 2>/dev/null
java -jar "$JAR" "$W/surfc/java/app" --json "$W/surfc/jrep.json" >/dev/null 2>&1
TC_JAVA=$(java -jar "$JAR" tour --report "$W/surfc/jrep.json" --json 2>/dev/null)
TC_TS=""
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/surfc/ts"
  printf 'class Settings { static load(): number { return stamp(); } }\nfunction stamp(): number { return Date.now(); }\nexport { Settings };\n' > "$W/surfc/ts/cases.ts"
  node "$TS_DIR/scan.mjs" "$W/surfc/ts/cases.ts" "$W/surfc/tsrep" >/dev/null 2>&1
  TC_TS=$(node "$TS_DIR/query.mjs" tour --report "$W/surfc/tsrep" --json 2>/dev/null)
fi
TC_SW=""
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/surfc/swift"
  printf 'import Foundation\nstruct Settings { static func load() -> Double { return stamp() } }\nfunc stamp() -> Double { return Date().timeIntervalSince1970 }\n' > "$W/surfc/swift/m.swift"
  env -u CANDOR_CONFIG "$SW_BIN" "$W/surfc/swift" --out "$W/surfc/swrep" >/dev/null 2>&1
  TC_SW=$(env -u CANDOR_CONFIG "$SW_BIN" tour --report "$W/surfc/swrep" --json 2>/dev/null)
fi
python3 - "$TC_RUST" "$TC_JAVA" "$TC_TS" "$TS_PRESENT" "$TC_SW" "$SW_PRESENT" <<'PY' || rc=1
import json, sys
rust, java, ts, ts_present = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sw, sw_present = sys.argv[5], sys.argv[6]
print("\n[4j] SURFACE salience floor  (a mundane Clock-only reach is NEVER surfaced)")
ok = True
def check(name, out):
    global ok
    # An EMPTY capture must be a DIVERGE, never a pass — an engine that CRASHES on the salience
    # fixture would otherwise parse as {} -> zero reaches -> "quiet" -> MATCH (fail-open; max-review
    # find). The honest quiet answer is a JSON body with an empty reaches list, not silence.
    if not (out or "").strip():
        print(f"  {name:12s} -> DIVERGE  (no tour output — the engine crashed or the fixture scan failed)")
        ok = False
        return
    try:
        reaches = json.loads(out).get("reaches", [])
        quiet = len(reaches) == 0
    except Exception:
        quiet = False
    print(f"  {name:12s} -> {'MATCH' if quiet else 'DIVERGE'}"
          + ("" if quiet else "  (surfaced a mundane Clock reach as `most surprising`)"))
    ok = ok and quiet
check("candor-scan", rust)
check("candor-java", java)
if ts_present:
    check("candor-ts", ts)
if sw_present:
    check("candor-swift", sw)
print("  -> " + ("MATCH — every engine stays quiet on a Clock-only crate (nothing hidden)"
                 if ok else "DIVERGE — an engine over-promised on a mundane reach"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 5 — read-only query SHAPE differential: run show/where/callers/map on both engines and assert the   [TIER 2]
# JSON *shape* (the keys an agent parses) is identical. The function-name VALUES are language-natural
# (`a::b` vs `a.b`), so this pins structure, not content — catching a field rename or a restructured
# query (SPEC §3.1). The core graph queries are candor's value surface; their shape must not drift.
# ====================================================================================================
RUST_PREFIX="$(dirname "$RUST_REPORT")/report"
"$QUERY" show    "$RUST_PREFIX" net_connect 1     > "$W/r_show.json"    2>/dev/null
"$QUERY" where   "$RUST_PREFIX" Fs 1              > "$W/r_where.json"   2>/dev/null
"$QUERY" callers "$RUST_PREFIX" transitive_leaf 1 > "$W/r_callers.json" 2>/dev/null
"$QUERY" map     "$RUST_PREFIX" 1                 > "$W/r_map.json"     2>/dev/null
"$QUERY" diff    "$RUST_PREFIX" "$RUST_PREFIX" 1 v v > "$W/r_diff.json" 2>/dev/null
"$QUERY" impact  "$RUST_PREFIX" transitive_leaf --json > "$W/r_impact.json" 2>/dev/null
"$QUERY" gains   "$RUST_PREFIX" "$RUST_PREFIX" --json   > "$W/r_gains.json" 2>/dev/null
"$QUERY" path    "$RUST_PREFIX" transitive_caller Fs --json > "$W/r_path.json" 2>/dev/null
"$QUERY" blindspots "$RUST_PREFIX" --json                   > "$W/r_blindspots.json" 2>/dev/null
"$QUERY" reachable "$RUST_PREFIX" --json                    > "$W/r_reachable.json" 2>/dev/null
java -jar "$JAR" show    "$W/java.json" net_connect --json     > "$W/j_show.json"    2>/dev/null
java -jar "$JAR" where   "$W/java.json" Fs --json              > "$W/j_where.json"   2>/dev/null
java -jar "$JAR" callers "$W/java.json" transitive_leaf --json > "$W/j_callers.json" 2>/dev/null
java -jar "$JAR" map     "$W/java.json" --json                 > "$W/j_map.json"     2>/dev/null
java -jar "$JAR" diff    "$W/java.json" "$W/java.json" --json  > "$W/j_diff.json"    2>/dev/null
java -jar "$JAR" impact  "$W/java.json" transitive_leaf --json > "$W/j_impact.json"  2>/dev/null
java -jar "$JAR" gains   "$W/java.json" "$W/java.json" --json   > "$W/j_gains.json"   2>/dev/null
java -jar "$JAR" path    "$W/java.json" transitive_caller Fs --json > "$W/j_path.json" 2>/dev/null
java -jar "$JAR" blindspots "$W/java.json" --json              > "$W/j_blindspots.json" 2>/dev/null
java -jar "$JAR" reachable "$W/java.json" --json               > "$W/j_reachable.json" 2>/dev/null
"$QUERY" show "$RUST_PREFIX" act 1  > "$W/r_ladder_act.json"  2>/dev/null
"$QUERY" show "$RUST_PREFIX" nion 1 > "$W/r_ladder_nion.json" 2>/dev/null
java -jar "$JAR" show "$W/java.json" act --json  > "$W/j_ladder_act.json"  2>/dev/null
java -jar "$JAR" show "$W/java.json" nion --json > "$W/j_ladder_nion.json" 2>/dev/null
# segment-suffix at a NESTED-TYPE boundary: `Svc::act`/`Svc.act` must resolve to exactly the one
# inner-type method (Rust `::Svc::act`, JVM `Cases$Svc.act` — the `$` boundary), never a substring cousin.
"$QUERY" show "$RUST_PREFIX" Svc::act 1 > "$W/r_ladder_svc.json" 2>/dev/null
java -jar "$JAR" show "$W/java.json" Svc.act --json > "$W/j_ladder_svc.json" 2>/dev/null
if [ -n "$TS_OK" ] && [ ! -f "$TS_DIR/query.mjs" ]; then
  # a working scanner with a missing query surface is present-but-broken (the suite's own rule):
  # a deleted/renamed query.mjs must FAIL the differential, never silently degrade it to two-way.
  echo "FAIL: candor-ts scanner works but $TS_DIR/query.mjs is missing — the §3.1 query surface vanished"
  exit 2
fi
if [ -n "$TS_OK" ]; then
  TSQ() { node "$TS_DIR/query.mjs" "$@"; }
  TSQ show    "$W/ts" net_connect 1     > "$W/t_show.json"    2>/dev/null
  TSQ where   "$W/ts" Fs 1              > "$W/t_where.json"   2>/dev/null
  TSQ callers "$W/ts" transitive_leaf 1 > "$W/t_callers.json" 2>/dev/null
  TSQ map     "$W/ts" 1                 > "$W/t_map.json"     2>/dev/null
  TSQ show    "$W/ts" act 1             > "$W/t_ladder_act.json"  2>/dev/null
  TSQ show    "$W/ts" nion 1            > "$W/t_ladder_nion.json" 2>/dev/null
  TSQ show    "$W/ts" Svc.act 1         > "$W/t_ladder_svc.json"  2>/dev/null
  TSQ diff    "$W/ts" "$W/ts" 1         > "$W/t_diff.json"       2>/dev/null
  TSQ impact  "$W/ts" transitive_leaf 1 > "$W/t_impact.json"     2>/dev/null
  TSQ gains   "$W/ts" "$W/ts"            > "$W/t_gains.json"      2>/dev/null
  TSQ path    "$W/ts" transitive_caller Fs --json > "$W/t_path.json"     2>/dev/null
  TSQ blindspots "$W/ts"                   > "$W/t_blindspots.json" 2>/dev/null
  TSQ reachable "$W/ts"                    > "$W/t_reachable.json" 2>/dev/null
fi

# PART 5c — blindspots --stats (SPEC §3.1 ⟨0.20⟩): the reason-class distribution. Three-way (R+J+T — swift
# has no `blindspots` verb). The exact class COUNTS diverge representationally (an engine classifies its own
# Unknowns), so this pins the CONTRACT structurally: `byClass` carries exactly the six classes as integers,
# `sources`/`totalUnknown` are integers, every count ≤ sources, and the class memberships sum to ≥ sources
# (every source classifies to ≥1 class — never a silent drop). Identical shape in all three declaring engines.
"$QUERY" blindspots "$RUST_PREFIX" --stats --json  > "$W/r_bstats.json" 2>/dev/null
java -jar "$JAR" blindspots "$W/java.json" --stats --json > "$W/j_bstats.json" 2>/dev/null
[ -n "$TS_OK" ] && TSQ blindspots "$W/ts" --stats --json > "$W/t_bstats.json" 2>/dev/null
python3 - "$W" "${TS_OK:+ts}" <<'PY' || rc=1
import json, os, sys
W = sys.argv[1]; ts = len(sys.argv) > 2 and sys.argv[2] == "ts"
CLASSES = ["reflect", "dispatch", "indirect", "native", "unresolved", "setup"]
engines = [("candor(rust)", "r_bstats"), ("candor-java", "j_bstats")] + ([("candor-ts", "t_bstats")] if ts else [])
print("\n[5c] BLINDSPOTS --stats  (SPEC §3.1 ⟨0.20⟩ — reason-class distribution; structural, three-way)")
fails = []
for name, stem in engines:
    p = f"{W}/{stem}.json"
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        fails.append(f"{name}: --stats produced no output"); continue
    d = json.load(open(p))
    bc = d.get("byClass", {})
    if sorted(bc.keys()) != sorted(CLASSES):
        fails.append(f"{name}: byClass keys {sorted(bc.keys())} != the six classes")
    src, tot = d.get("sources"), d.get("totalUnknown")
    if not isinstance(src, int) or not isinstance(tot, int):
        fails.append(f"{name}: sources/totalUnknown must be integers, got {src}/{tot}"); continue
    if any(not isinstance(v, int) or v < 0 or v > src for v in bc.values()):
        fails.append(f"{name}: a byClass count is not a 0..sources integer: {bc} (sources={src})")
    if sum(bc.values()) < src:
        fails.append(f"{name}: class memberships {sum(bc.values())} < sources {src} — a source went unclassified")
    print(f"  {name:13s} sources={src} totalUnknown={tot} byClass={bc}")
for f in fails: print(f"     FAIL {f}")
print("  -> " + ("MATCH — every declaring engine emits the same `byClass`/sources/totalUnknown shape, counts internally consistent"
                 if not fails else "DIVERGE — see FAIL lines"))
sys.exit(0 if not fails else 1)
PY

# A crashed query leaves a 0-byte redirect file the comparison would then choke on with a bare
# JSONDecodeError — name the engine and query instead, before the python ever runs.
P5_FILES="r_show r_where r_callers r_map r_diff r_impact r_gains r_path r_blindspots r_reachable r_ladder_act r_ladder_nion r_ladder_svc \
          j_show j_where j_callers j_map j_diff j_impact j_gains j_path j_blindspots j_reachable j_ladder_act j_ladder_nion j_ladder_svc"
if [ -n "$TS_OK" ]; then  # query.mjs presence is enforced above — a working scanner without it already FAILED
  P5_FILES="$P5_FILES t_show t_where t_callers t_map t_diff t_impact t_gains t_path t_blindspots t_reachable t_ladder_act t_ladder_nion t_ladder_svc"
fi
for f in $P5_FILES; do
  [ -s "$W/$f.json" ] || { echo "FAIL: $f.json is empty — the ${f%%_*} engine's '${f#*_}' query errored"; exit 2; }
done

python3 - "$W" <<'PY' || rc=1
import json, os, sys
W = sys.argv[1]
load = lambda q, e: json.load(open(f"{W}/{e}_{q}.json"))
ts = os.path.exists(f"{W}/t_show.json")
print("\n[5] QUERY-SHAPE differential  (show/where/callers/map JSON shape agrees across engines"
      + (", incl. candor-ts" if ts else "") + ")")
ok = True
def check(name, cond, detail=""):
    global ok
    print(f"  {name:8s} -> {'MATCH' if cond else 'DIVERGE'}{detail}")
    ok = ok and cond
# show: the four required fields present in both (optional fs/hosts are engine-capability dependent)
req = {"fn", "inferred", "direct", "unresolved"}
rs, js = load("show", "r"), load("show", "j")
tshow = load("show", "t") if ts else None
check("show", bool(rs) and bool(js) and req <= set(rs[0]) and req <= set(js[0])
              and (not ts or (bool(tshow) and req <= set(tshow[0]))))
# where / callers: exact top-level key set in every engine
for q, keys in (("where", {"effect", "directly", "inherited"}), ("callers", {"of", "direct", "transitive"})):
    r, j = load(q, "r"), load(q, "j")
    tq = load(q, "t") if ts else None
    check(q, set(r) == keys and set(j) == keys and (not ts or set(tq) == keys))
# map: every module bucket carries exactly {effects, functions}
mk = {"effects", "functions"}
rm, jm = load("map", "r"), load("map", "j")
tm = load("map", "t") if ts else None
check("map", bool(rm) and bool(jm) and all(set(v) == mk for v in rm.values())
                                    and all(set(v) == mk for v in jm.values())
                                    and (not ts or (bool(tm) and all(set(v) == mk for v in tm.values()))))
# diff: an envelope object with `changes` (a list) in both — diff-vs-self must be empty. The Java
# engine used to emit a bare array (no envelope), so a consumer's d["changes"] worked on one engine
# and threw on the other.
rd, jd = load("diff", "r"), load("diff", "j")
td = load("diff", "t") if ts else None
check("diff", isinstance(rd, dict) and isinstance(jd, dict)
              and rd.get("changes") == [] and jd.get("changes") == []
              and (not ts or (isinstance(td, dict) and td.get("changes") == [])))
# impact (SPEC §3.1): the blast-radius LIST, not just a count — {fn, affectedCount, affected,
# entryPoints}. affectedCount must equal len(affected), and the affected SET (by leaf-name, since the
# fn VALUES are language-natural) must agree across engines. This pins the enrichment that lets an
# agent read the blast radius instead of re-deriving it.
ik = {"fn", "affectedCount", "affected", "entryPoints"}
ri, ji = load("impact", "r"), load("impact", "j")
ti = load("impact", "t") if ts else None
leaf = lambda n: n.split("::")[-1].split(".")[-1]
aff = lambda d: {leaf(n) for n in d["affected"]}
check("impact", ik <= set(ri) and ik <= set(ji)
                and ri["affectedCount"] == len(ri["affected"]) and ji["affectedCount"] == len(ji["affected"])
                and aff(ri) == aff(ji) and aff(ri) == {"transitive_caller"}
                and (not ts or (ik <= set(ti) and ti["affectedCount"] == len(ti["affected"]) and aff(ti) == aff(ri))))
# gains (SPEC §5.1): the supply-chain alarm shape {gained:[Effect], byFunction:[{fn,effect}]}. Diffed
# against ITSELF here, so the alarm is silent (gained == []) — pins the cross-engine shape + the
# "a stable surface raises no alarm" invariant.
gk = {"gained", "byFunction"}
rg, jg = load("gains", "r"), load("gains", "j")
tg = load("gains", "t") if ts else None
check("gains", gk <= set(rg) and gk <= set(jg) and rg["gained"] == [] and jg["gained"] == []
               and (not ts or (gk <= set(tg) and tg["gained"] == [])))
# blindspots (SPEC §3.1 ⟨0.6⟩): the Unknown-SOURCES view {sources:[{fn,why,reaches,affected}],
# totalUnknown}. Pins the shape across engines — each source carries its why + blast radius. Content is
# engine-natural (and the fixture may have zero sources), so this checks structure, not counts.
bk = {"sources", "totalUnknown"}; sk = {"fn", "why", "reaches", "affected"}
rb, jb = load("blindspots", "r"), load("blindspots", "j")
tb = load("blindspots", "t") if ts else None
bs_ok = lambda d: set(d) == bk and all(sk <= set(s) for s in d["sources"])
check("blindspots", bs_ok(rb) and bs_ok(jb) and (not ts or bs_ok(tb)))
# reachable (SPEC §3.1): the runtime effect surface {entryPoints:int, effects:{Effect:{count,via}}}.
# Shape-only (entry-point detection is engine-natural on this fixture) — it was the one specced §3.1
# query with NO conformance coverage while the unspecced gains WAS pinned; both directions now hold.
kk = {"entryPoints", "effects"}
rr, jr = load("reachable", "r"), load("reachable", "j")
tr = load("reachable", "t") if ts else None
re_ok = lambda d: kk <= set(d) and isinstance(d["entryPoints"], int) \
                  and all({"count", "via"} <= set(v) for v in d["effects"].values())
check("reachable", re_ok(rr) and re_ok(jr) and (not ts or re_ok(tr)))
# path (SPEC §3.1): the provenance chain {effect, fn, path:[{fn,loc,source}]} from fn to the nearest
# unit performing the effect DIRECTLY (source:true). The leaf-name chain + the source must agree across
# engines — this pins the freshly-written candor-ts BFS against candor-query's, which nothing else did.
pk = {"effect", "fn", "path"}
rp, jp = load("path", "r"), load("path", "j")
tp = load("path", "t") if ts else None
chain = lambda d: [s["fn"].split("::")[-1].split(".")[-1] for s in d["path"]]
srcs = lambda d: [s["fn"].split("::")[-1].split(".")[-1] for s in d["path"] if s.get("source")]
check("path", pk <= set(rp) and pk <= set(jp)
              and chain(rp) == ["transitive_caller", "transitive_leaf"] and chain(jp) == chain(rp)
              and srcs(rp) == ["transitive_leaf"] and srcs(jp) == ["transitive_leaf"]
              and (not ts or (pk <= set(tp) and chain(tp) == chain(rp) and srcs(tp) == ["transitive_leaf"])))
# match LADDER (SPEC §3.1): a segment-suffix query resolves to exactly the suffix match in both
# engines (`act` -> only Svc.act), while a substring-only query still browses (`nion` -> union_a/b/c).
rs1, js1 = load("ladder_act", "r"), load("ladder_act", "j")
ts1 = load("ladder_act", "t") if ts else None
check("ladder:suffix", len(rs1) == 1 and len(js1) == 1
                       and rs1[0]["fn"].split("::")[-1] == "act" and js1[0]["fn"].split(".")[-1] == "act"
                       and (not ts or (len(ts1) == 1 and ts1[0]["fn"].split(".")[-1] == "act")))
rs2, js2 = load("ladder_nion", "r"), load("ladder_nion", "j")
names_r = {e["fn"].split("::")[-1] for e in rs2}; names_j = {e["fn"].split(".")[-1] for e in js2}
names_t = {e["fn"].split(".")[-1] for e in load("ladder_nion", "t")} if ts else names_r
check("ladder:substr", names_r == {"union_a", "union_b", "union_c"} and names_j == names_r
                       and names_t == names_r)
# nested-type boundary (`::` on Rust, `$` on the JVM, `.` in TS): exactly the one Svc method.
rs3, js3 = load("ladder_svc", "r"), load("ladder_svc", "j")
ts3 = load("ladder_svc", "t") if ts else None
check("ladder:nested", len(rs3) == 1 and len(js3) == 1
                       and rs3[0]["fn"].split("::")[-1] == "act" and js3[0]["fn"].split(".")[-1] == "act"
                       and (not ts or (len(ts3) == 1 and ts3[0]["fn"].split(".")[-1] == "act")))
print("  -> " + ("MATCH — the agent-facing query shapes are identical in both engines"
                 if ok else "DIVERGE — a query's JSON shape differs between engines"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 5b — GAINS ORIGIN differential (SPEC §3.1 ⟨0.12⟩): each `gains --json` byFunction entry    [TIER 2]
# carries `origin`, separating the supply-chain ATTACK signal (a fn that EXISTED at the baseline —
# shipped pure, now performs the effect) from a NEW fn (a feature). Reports omit pure functions, so
# baseline existence keys on the BASELINE CALLGRAPH sidecar; with no baseline callgraph the origin is
# "unknown" — disclosed, never guessed. Fixture per engine (own qual + filename shapes, verified against
# each loader): baseline report lists only g (Fs); the baseline callgraph knows pure f; current has
# f→Net (existing!), g unchanged, h→Net (new). Then the sidecar is DELETED → both must read "unknown".
# ====================================================================================================
echo ""
echo "[5b] GAINS ORIGIN differential  (existing-fn gain vs new-fn vs unknown, keyed on the baseline callgraph)"
P5B_OK=0
p5b() { echo "     FAIL $1"; P5B_OK=1; }
mkdir -p "$W/gorigin"
# $1 label; $2 f-qual; $3 g-qual; $4 h-qual; $5 base report; $6 base callgraph sidecar; $7 cur report
gow() { # write one engine's fixture pair
  printf '{ "candor": {"version":"t","spec": "0.23"}, "functions": [ {"fn":"%s","inferred":["Fs"],"direct":["Fs"]} ] }' "$3" > "$5"
  printf '{ "%s": ["%s"], "%s": [] }' "$2" "$3" "$3" > "$6"
  printf '{ "candor": {"version":"t","spec": "0.23"}, "functions": [ {"fn":"%s","inferred":["Net"],"direct":["Net"]}, {"fn":"%s","inferred":["Fs"],"direct":["Fs"]}, {"fn":"%s","inferred":["Net"],"direct":["Net"]} ] }' "$2" "$3" "$4" > "$7"
}
# $1 label; $2 f-qual; $3 h-qual; $4 gains JSON output; $5 expected-f-origin; $6 expected-h-origin
gocheck() {
  python3 - "$1" "$2" "$3" "$4" "$5" "$6" <<'PY' || P5B_OK=1
import json, sys
label, fq, hq, out, want_f, want_h = sys.argv[1:7]
try:
    ent = {e["fn"]: e.get("origin") for e in json.loads(out).get("byFunction", [])}
except Exception as ex:
    print(f"     FAIL {label}: gains --json did not parse ({ex})"); sys.exit(1)
ok = True
for q, want in ((fq, want_f), (hq, want_h)):
    got = ent.get(q)
    if got != want:
        print(f"     FAIL {label}: {q} origin = {got!r}, want {want!r}"); ok = False
sys.exit(0 if ok else 1)
PY
}
# rust — <prefix>.demo.scan.json family
gow rust "m::f" "m::g" "m::h" "$W/gorigin/rbase.demo.scan.json" "$W/gorigin/rbase.demo.scan.callgraph.json" "$W/gorigin/rcur.demo.scan.json"
gocheck rust "m::f" "m::h" "$("$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase" --json 2>/dev/null)" existing new
rm -f "$W/gorigin/rbase.demo.scan.callgraph.json"
gocheck "rust (no baseline callgraph)" "m::f" "m::h" "$("$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase" --json 2>/dev/null)" unknown unknown
# java — <prefix>.jvm.json + <prefix>.jvm.callgraph.json
gow java "m.f" "m.g" "m.h" "$W/gorigin/jbase.jvm.json" "$W/gorigin/jbase.jvm.callgraph.json" "$W/gorigin/jcur.jvm.json"
gocheck java "m.f" "m.h" "$(java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json" --json 2>/dev/null)" existing new
rm -f "$W/gorigin/jbase.jvm.callgraph.json"
gocheck "java (no baseline callgraph)" "m.f" "m.h" "$(java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json" --json 2>/dev/null)" unknown unknown
# ts — <prefix>.json + <prefix>.callgraph.json (no backend infix in this engine's own shape)
if [ -n "$TS_PRESENT" ]; then
  gow ts "m.f" "m.g" "m.h" "$W/gorigin/tbase.json" "$W/gorigin/tbase.callgraph.json" "$W/gorigin/tcur.json"
  gocheck ts "m.f" "m.h" "$(node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase" 2>/dev/null)" existing new
  rm -f "$W/gorigin/tbase.callgraph.json"
  gocheck "ts (no baseline callgraph)" "m.f" "m.h" "$(node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase" 2>/dev/null)" unknown unknown
fi
# swift — <prefix>.<pkg>.Swift.json + <prefix>.<pkg>.Swift.callgraph.json
if [ -n "$SW_PRESENT" ]; then
  gow swift "M.f" "M.g" "M.h" "$W/gorigin/sbase.M.Swift.json" "$W/gorigin/sbase.M.Swift.callgraph.json" "$W/gorigin/scur.M.Swift.json"
  gocheck swift "M.f" "M.h" "$(env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase" --json 2>/dev/null)" existing new
  rm -f "$W/gorigin/sbase.M.Swift.callgraph.json"
  gocheck "swift (no baseline callgraph)" "M.f" "M.h" "$(env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase" --json 2>/dev/null)" unknown unknown
fi
# PARTIAL baseline graph (max-review find): a corrupt sidecar must never downgrade the attack signal
# to a feature-looking "new" — a fn absent from the surviving edges is "unknown", not "new". rust/ts/
# swift merge multi-sidecar families (a VALID sidecar knowing only g + a CORRUPT second one → non-empty
# partial graph); java reads one sidecar per report path (corrupt single sidecar → same invariant).
printf '{ "%s": [] }' "m::g" > "$W/gorigin/rbase.demo.scan.callgraph.json"
printf '{ corrupt' > "$W/gorigin/rbase.demo2.scan.callgraph.json"
gocheck "rust (partial baseline callgraph)" "m::f" "m::h" "$("$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase" --json 2>/dev/null)" unknown unknown
printf '{ corrupt' > "$W/gorigin/jbase.jvm.callgraph.json"
gocheck "java (corrupt baseline callgraph)" "m.f" "m.h" "$(java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json" --json 2>/dev/null)" unknown unknown
if [ -n "$TS_PRESENT" ]; then
  printf '{ "%s": [] }' "m.g" > "$W/gorigin/tbase.a.callgraph.json"
  printf '{ corrupt' > "$W/gorigin/tbase.b.callgraph.json"
  gocheck "ts (partial baseline callgraph)" "m.f" "m.h" "$(node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase" 2>/dev/null)" unknown unknown
fi
if [ -n "$SW_PRESENT" ]; then
  printf '{ "%s": [] }' "M.g" > "$W/gorigin/sbase.M.Swift.callgraph.json"
  printf '{ corrupt' > "$W/gorigin/sbase.N.Swift.callgraph.json"
  gocheck "swift (partial baseline callgraph)" "M.f" "M.h" "$(env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase" --json 2>/dev/null)" unknown unknown
fi
if [ "$P5B_OK" = 0 ]; then
  echo "  -> MATCH — every engine separates existing-fn gains from new-fn gains, and discloses unknown on an absent OR partial baseline callgraph"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# PART 5b, EXIT-CODE contract (#3 corpus re-audit): gains is a diff view — ADVISORY (exit 0) by default. Two
# guards pinned four-way: (a) `--strict` fails on ANY gained effect (exit 1) so a supply-chain CI job can
# require a dependency bump introduce no new capability; (b) an unknown flag — notably a `--policy` a user
# reaches for expecting a gate — is REJECTED loud (exit 2), NEVER swallowed into an exit-0 false-clean. The
# gorigin fixtures carry a real gain (m::f gained an effect), so --strict must bite. (The effect-SPECIFIC
# gate stays the scan-time `deny <E> gained` policy — AS-EFF-005, pinned in PART 15.)
echo "[5b] GAINS exit-code contract  (advisory 0 · --strict 1 on a gain · --strict 0 on none · --policy rejected 2)"
# gains_exit: run a command, assert its exit code. gains_reject: additionally assert the stderr NAMES the
# real gate (AS-EFF-005), so an engine that spec-violatingly ACCEPTS --policy and merely fails to read a
# missing file (also exit 2) can't pass for the wrong reason — the policy file we pass EXISTS.
GPOL="$W/gorigin/readable.policy"; printf 'deny Net someLayer\n' > "$GPOL"
gains_exit() { local label="$1" want="$2"; shift 2; ( "$@" ) >/dev/null 2>&1; local got=$?
  [ "$got" = "$want" ] || { echo "  -> DIVERGE — $label: gains exit $got, expected $want"; rc=1; }; }
gains_reject() { local label="$1"; shift; local err; err="$( "$@" 2>&1 >/dev/null )"; local got=$?
  [ "$got" = 2 ] || { echo "  -> DIVERGE — $label: gains --policy exit $got, expected 2"; rc=1; }
  case "$err" in *AS-EFF-005*) ;; *) echo "  -> DIVERGE — $label: --policy rejection must NAME the AS-EFF-005 scan gate (got: ${err:0:60})"; rc=1;; esac; }
# rust — advisory 0, --strict 1 on a gain, --strict 0 over NO gain (same report both sides), --policy rejected+named.
gains_exit   "rust advisory"      0 "$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase"
gains_exit   "rust --strict"      1 "$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase" --strict
gains_exit   "rust --strict clean" 0 "$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rcur" --strict
gains_reject "rust --policy"         "$QUERY" gains "$W/gorigin/rcur" "$W/gorigin/rbase" --policy "$GPOL"
gains_exit   "java advisory"      0 java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json"
gains_exit   "java --strict"      1 java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json" --strict
gains_exit   "java --strict clean" 0 java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jcur.jvm.json" --strict
gains_reject "java --policy"         java -jar "$JAR" gains "$W/gorigin/jcur.jvm.json" "$W/gorigin/jbase.jvm.json" --policy "$GPOL"
if [ -n "$TS_OK" ]; then
  gains_exit   "ts advisory"      0 node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase"
  gains_exit   "ts --strict"      1 node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase" --strict
  gains_exit   "ts --strict clean" 0 node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tcur" --strict
  gains_reject "ts --policy"         node "$TS_DIR/query.mjs" gains "$W/gorigin/tcur" "$W/gorigin/tbase" --policy "$GPOL"
else echo "  (ts gains exit-code checks SKIPPED — engine unavailable)"; fi
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  gains_exit   "swift advisory"      0 env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase"
  gains_exit   "swift --strict"      1 env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase" --strict
  gains_exit   "swift --strict clean" 0 env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/scur" --strict
  gains_reject "swift --policy"         env -u CANDOR_CONFIG "$SW_BIN" gains "$W/gorigin/scur" "$W/gorigin/sbase" --policy "$GPOL"
else echo "  (swift gains exit-code checks SKIPPED — engine unavailable)"; fi
echo "  -> checked advisory=0 / --strict=1 / --strict-clean=0 / --policy=reject-2-named on every working engine"

# ====================================================================================================
# PART 6 — the THIRD engine (candor-ts): the derivability proof, run live. The TS slice was written   [TIER 1]
# from the spec documents alone; here it answers the SAME Part-1 oracle as the Rust and JVM engines.
# Optional: skips (loudly) when the engine or node isn't available, so the suite never blocks on it.
# Locally, a sibling ../candor-ts checkout is used; in CI the workflow checks it out.
# ====================================================================================================
if [ -n "$TS_PRESENT" ]; then
  if [ -n "$TS_OK" ]; then
    python3 - "$HERE/expected.json" "$W/ts.json" <<'PY' || rc=1
import json, sys
expected = {k: set(v) for k, v in json.load(open(sys.argv[1])).items() if not k.startswith("_")}
d = json.load(open(sys.argv[2]))
fns = d["functions"] if isinstance(d, dict) else d
got = {e["fn"].split(".")[-1]: set(e.get("inferred", [])) for e in fns}
fails = sum(1 for c, exp in expected.items() if got.get(c, set()) != exp)
print(f"\n[6] THIRD ENGINE (candor-ts, derived from the spec alone): {len(expected)-fails}/{len(expected)} cases match")
for c, exp in expected.items():
    g = got.get(c, set())
    if g != exp:
        print(f"  DIVERGE {c}: expected {sorted(exp)} got {sorted(g)}")
sys.exit(1 if fails else 0)
PY
  else
    echo; echo "[6] THIRD ENGINE (candor-ts): PRESENT at $TS_DIR but its scan produced no report — FAIL"; rc=1
  fi
elif [ -n "${CONFORMANCE_REQUIRE_ALL:-}" ]; then
  echo; echo "[6] THIRD ENGINE (candor-ts): not present AND CONFORMANCE_REQUIRE_ALL is set — FAIL (strict: the gate must not silently degrade to fewer engines)"; rc=1
else
  echo; echo "[6] THIRD ENGINE (candor-ts): not present (set CANDOR_TS or clone ../candor-ts) — SKIPPED (set CONFORMANCE_REQUIRE_ALL=1 to make this a failure in CI)"
fi

# ====================================================================================================
# PART 6c — the FOURTH engine (candor-swift): the derivability proof, run live (same Part-1 oracle).   [TIER 1]
# ====================================================================================================
if [ -n "$SW_PRESENT" ]; then
  if [ -n "$SW_OK" ]; then
    python3 - "$HERE/expected.json" "$SW_REPORT" <<'PY' || rc=1
import json, sys
expected = {k: set(v) for k, v in json.load(open(sys.argv[1])).items() if not k.startswith("_")}
d = json.load(open(sys.argv[2]))
fns = d["functions"] if isinstance(d, dict) else d
got = {e["fn"].split(".")[-1]: set(e.get("inferred", [])) for e in fns}
fails = sum(1 for c, exp in expected.items() if got.get(c, set()) != exp)
print(f"\n[6c] FOURTH ENGINE (candor-swift, derived from the spec alone): {len(expected)-fails}/{len(expected)} cases match")
for c, exp in expected.items():
    g = got.get(c, set())
    if g != exp:
        print(f"  DIVERGE {c}: expected {sorted(exp)} got {sorted(g)}")
sys.exit(1 if fails else 0)
PY
  else
    echo; echo "[6c] FOURTH ENGINE (candor-swift): PRESENT at $SW_DIR but its scan produced no report — FAIL"; rc=1
  fi
elif [ -n "${CONFORMANCE_REQUIRE_ALL:-}" ]; then
  echo; echo "[6c] FOURTH ENGINE (candor-swift): not present AND CONFORMANCE_REQUIRE_ALL is set — FAIL (strict)"; rc=1
else
  echo; echo "[6c] FOURTH ENGINE (candor-swift): not present (set CANDOR_SWIFT or clone ../candor-swift, swift toolchain required) — SKIPPED (set CONFORMANCE_REQUIRE_ALL=1 to make this a failure in CI)"
fi

# --- Part 9: unitKind (SPEC §2, released since 0.5) --------------------------------------------------
# Engines that have non-function units name them; ordinary functions OMIT the field. `unitKind` is an
# OPTIONAL §2 field (released in 0.5; an engine MAY omit it entirely, §2 forward-compat), so this part
# stays ADVISORY — a miss WARNS but does not fail the suite, since omission is conformant. (Each branch
# traps its own errors so a broken scan prints a labelled WARN, never an unattributed Python traceback.)
echo
echo "[9] unitKind (OPTIONAL §2 field, released 0.5 — ADVISORY: non-function units named, plain fns omit the field):"
mkdir -p "$W/uk/java"
cat > "$W/uk/java/Uk.java" <<'J'
import java.nio.file.*;
public class Uk {
  static { try { Files.readString(Path.of("/etc/x")); } catch (Exception e) {} }
  static void plain() { try { Files.readString(Path.of("/etc/y")); } catch (Exception e) {} }
}
J
javac -d "$W/uk/jcls" "$W/uk/java/Uk.java" 2>/dev/null
java -jar "$JAR" "$W/uk/jcls" --json "$W/uk/java.json" >/dev/null 2>&1
python3 - "$W/uk/java.json" <<'PY' || true
import json, sys
try:
    by = {e["fn"]: e for e in json.load(open(sys.argv[1]))["functions"]}
    clinit = next((e for f, e in by.items() if f.endswith(".<clinit>")), None)
    ok = clinit and clinit.get("unitKind") == "initializer" and "unitKind" not in by.get("Uk.plain", {})
    print("  java       <clinit> -> initializer; plain fn omits" if ok else "  java       WARN (unitKind absent — draft)")
except Exception as e:
    print(f"  java       WARN ({e})")
PY
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/uk/ts"
  printf '{"name":"ukpkg"}' > "$W/uk/ts/package.json"
  printf 'const fs = require("node:fs");\nmodule.exports = function () { return fs.readFileSync("/k"); };\n' > "$W/uk/ts/sign.js"
  ( cd "$TS_DIR" && node scan.mjs "$W/uk/ts" --allow-js --out "$W/uk/tsr" >/dev/null 2>&1 )
  python3 - "$W/uk/tsr.json" <<'PY' || true
import json, sys
try:
    fns = json.load(open(sys.argv[1]))["functions"]
    ok = any(e.get("unitKind") == "export" for e in fns)
    print("  ts         CJS export unit -> export" if ok else "  ts         WARN (unitKind absent — draft)")
except Exception as e:
    print(f"  ts         WARN ({e})")
PY
fi
if [ -n "$SW_BIN" ] && [ -x "$SW_BIN" ]; then
  mkdir -p "$W/uk/sw"
  printf 'import Foundation\nstruct C { var v: Int { _ = FileManager.default.contents(atPath: "/x"); return 1 } }\nfunc plainSw() { _ = FileManager.default.contents(atPath: "/y") }\n' > "$W/uk/sw/m.swift"
  "$SW_BIN" "$W/uk/sw" --out "$W/uk/swr" >/dev/null 2>&1
  python3 - <<PY || true
import json, glob
try:
    ps = [x for x in glob.glob("$W/uk/swr.*.json") if "callgraph" not in x and "hierarchy" not in x]
    if not ps:
        print("  swift      WARN (no report produced)")
    else:
        by = {e["fn"]: e for e in json.load(open(ps[0]))["functions"]}
        ok = by.get("C.v", {}).get("unitKind") == "accessor" and "unitKind" not in by.get("plainSw", {})
        print("  swift      accessor unit -> accessor; plain fn omits" if ok else "  swift      WARN (unitKind absent — draft)")
except Exception as e:
    print(f"  swift      WARN ({e})")
PY
fi

# --- Part 8: an unreadable policy FILE fails the run (SPEC §6.2 MUST) --------------------------------
# A configured-but-unreadable policy must exit 2 (distinct from 1 = violation), never run gateless:
# a typo'd path that runs green is a gate that silently passes everything. (Found live: one engine
# was loud on stderr but exited 0.)
echo
echo "[8] UNREADABLE POLICY FAILS THE RUN (SPEC §6.2):"
NOPOL="$W/no-such-dir/no-such.policy"
check_polfail() { # $1 label, $2… command (run from cwd)
  local label="$1"; shift
  "$@" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq 2 ]; then
    echo "  $label -> exit 2"
  else
    echo "  $label FAILED: exit $got (want 2 — gateless green is the §6.2 forbidden state)"; rc=1
  fi
}
mkdir -p "$W/polfail/src"
printf '[package]\nname="p"\n' > "$W/polfail/Cargo.toml"
printf 'pub fn f(){ let _ = std::fs::read("/x"); }\n' > "$W/polfail/src/lib.rs"
check_polfail "rust:scan " "$SCAN" "$W/polfail" --policy "$NOPOL" --out "$W/polfail/r"
# Unknown FLAGS fail the same way (exit 2) — silently ignoring a typo'd flag, or reading it as a
# path, drops gates and confuses agents following a newer doc against an older binary.
check_polfail "rust:scan  (unknown flag)" "$SCAN" --frobnicate
check_polfail "java       (unknown flag)" java -jar "$JAR" --frobnicate
[ -n "$TS_PRESENT" ] && check_polfail "ts         (unknown flag)" node "$TS_DIR/scan.mjs" --frobnicate
[ -n "$SW_BIN" ] && [ -x "$SW_BIN" ] && check_polfail "swift      (unknown flag)" "$SW_BIN" --frobnicate
check_polfail "java      " env CANDOR_POLICY="$NOPOL" java -jar "$JAR" "$W/jout"
[ -n "$TS_PRESENT" ] && check_polfail "ts        " node "$TS_DIR/scan.mjs" "$TS_DIR/Cases.ts" --policy "$NOPOL" --out "$W/polfail/ts"
[ -n "$SW_BIN" ] && [ -x "$SW_BIN" ] && check_polfail "swift     " "$SW_BIN" "$SW_DIR/conformance/Cases.swift" --policy "$NOPOL" --out "$W/polfail/sw"

# --- Part 7: the self-describing engine (SPEC §7.11) -------------------------------------------------
# Every engine present prints its embedded agent contract under --agents: a version header comment
# followed by the AGENTS.md. The flag must exit 0, and the header must follow the CANONICAL shape
# `<!-- candor-<engine> <version> · …` (engine and version space-separated) so tooling can parse it
# uniformly — pinning it here is the one shared place that holds the format across the engines.
echo
echo "[7] SELF-DESCRIBING ENGINES (--agents, SPEC §7.11):"
check_agents() { # $1 label, $2… command
  local label="$1"; shift
  local out first
  # NOTE: first line via pure-bash parameter expansion + grep via here-strings — NOT `printf "$out" |
  # head -1 | grep`. Under `set -o pipefail`, head closing the pipe after line 1 gives printf a SIGPIPE
  # (write error: Broken pipe), failing the whole pipeline even when the header matched — a timing-
  # dependent CI flake (it spuriously failed run 27887693481, passed unchanged on the next commit).
  if out="$("$@" 2>/dev/null)"; then
    first="${out%%$'\n'*}"
    if grep -Eq '^<!-- candor-[a-z]+ [^ ]+ · ' <<<"$first" && grep -q 'AI coding agent' <<<"$out"; then
      echo "  $label --agents -> canonical header + contract"
      return
    fi
  fi
  echo "  $label --agents FAILED (header not 'candor-<engine> <version> ·', or contract missing): ${out%%$'\n'*}"; rc=1
}
check_agents "rust:scan " "$SCAN" --agents
check_agents "rust:query" "$QUERY" --agents
check_agents "java      " java -jar "$JAR" --agents
[ -n "$TS_PRESENT" ] && check_agents "ts        " node "$TS_DIR/scan.mjs" --agents
[ -n "$SW_BIN" ] && [ -x "$SW_BIN" ] && check_agents "swift     " "$SW_BIN" --agents

# ====================================================================================================
# GENERATIVE differential — the fixed fixtures above are hand-written; this GENERATES an effect ×
# indirection matrix (each effect reached through direct/local-call/typed-method/for-loop-element/field/
# callback) in all 4 languages and asserts the engines agree on every cell. It found a real bug on its
# first run (candor-scan silently dropped a fn-typed-param callback while the others propagated/Unknowned
# it — fixed in candor-scan ec94e73). Reuses the binaries this run already built/resolved.
# ====================================================================================================
# a missing/renamed gen script must FAIL, never silently delete the suite's strongest part
[ -f "$HERE/gen_differential.py" ] || { echo "FAIL: gen_differential.py is missing"; exit 2; }
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_differential.py"
) || { echo "generative differential: FAILED"; rc=1; }

# ====================================================================================================
# GATE-MASKING differential — the sibling of the generative differential, on the POLICY VERDICT axis.
# For each literal-surface effect {Net→host, Exec→cmd, Fs→path, Db→table} it renders, per language, a
# MASKED program (a benign ALLOWED literal beside a runtime-MASKED denied literal of the same effect) and
# a COMPLIANT one (only the benign literal), then runs each engine's `allow <Effect> <benign>` gate and
# asserts masked→FAIL-CLOSED, compliant→PASS. A masked program any engine PASSES is the cardinal gate-
# evasion (AS-EFF-008 opaque). Turns this session's per-engine fail-closed-on-masked fixes (scan/deep
# Fs+Db, swift two-path/establishing, java URL-split) into a cross-engine STANDING gate. Reuses the
# binaries this run already built/resolved.
[ -f "$HERE/gen_masking.py" ] || { echo "FAIL: gen_masking.py is missing"; exit 2; }
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_masking.py"
) || { echo "gate-masking differential: FAILED"; rc=1; }

# ====================================================================================================
# POLICY-MATCHING differential (FOUR-WAY, SPEC §6.2) — the APPLIED literal- & scope-matching sibling of the
# PART 4 grammar diff. Runs the SAME policy + an equivalent fixture through every engine's `--policy` gate
# and asserts the verdict equals the rule's expected verdict — for a `host:port` allow (the port rule),
# `::`-vs-`.` scope segmentation, fs path-boundary prefix, exec basename, and `schema.*` db matching. This
# is the four-way coverage the live candor-swift Net-port / `::`-scope divergences slipped past (they were
# rust+java+ts-only). Reuses gen_masking.py's engine harness. Reuses the binaries this run resolved.
[ -f "$HERE/gen_policy_match.py" ] || { echo "FAIL: gen_policy_match.py is missing"; exit 2; }
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_policy_match.py"
) || { echo "policy-matching differential: FAILED"; rc=1; }

# ====================================================================================================
# NET DESTINATION-CLASS differential (FOUR-WAY, SPEC §1/§6.2 ⟨0.20⟩) — the applied sibling of the PART 4
# `Net[dest…]` grammar diff. Runs `deny Net[unknown-host]` over an equivalent fixture in every engine and
# asserts the FAIL-CLOSED security posture: a known-telemetry host (curated TELEMETRY_HOSTS), a known-
# partner (model host), and a config `net-partner` are TOLERATED (PASS); an unknown-host + a runtime-masked
# host are DENIED (FAIL). A PASS on the exfil/runtime case is the cardinal sin — an exfiltration Net slipping
# the gate. Reuses gen_masking.py's engine harness + the binaries this run resolved (NET-DESTINATION-CLASS-DESIGN.md).
[ -f "$HERE/gen_netclass.py" ] || { echo "FAIL: gen_netclass.py is missing"; exit 2; }
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_netclass.py"
) || { echo "net destination-class differential: FAILED"; rc=1; }

# ====================================================================================================
# COMPLETENESS-MANIFEST differential (FOUR-WAY, SPEC §2 + §3.3.1 ⟨0.22⟩) — analyzed / unanalyzed. Over an
# equivalent fixture (effectful + plain-pure + ISOLATED-pure + an unparsed file) in every engine, asserts:
# the report's `analyzed.count` includes pure leaves (pure = count − |functions| ≥ 2); the unparsed unit is
# machine-legible in BOTH the report's `unanalyzed` and the --gate-json verdict; and a configured gate over
# it FAILS CLOSED (exit 2, verdict {ok:false,incomplete:true,unanalyzed:[…]}) — never green over unseen code
# (the machine-consumer cardinal sin). Reuses gen_netclass.py's engine harness (COMPLETENESS-MANIFEST-DESIGN.md).
[ -f "$HERE/gen_completeness.py" ] || { echo "FAIL: gen_completeness.py is missing"; exit 2; }
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_completeness.py"
) || { echo "completeness-manifest differential: FAILED"; rc=1; }

# ====================================================================================================
# DISPATCH-FRONTIER differential (SPEC §3.1/§4 ⟨0.7⟩) — `callers --include-unknown`. One shared scenario
# (Base.op with >fan-out impls, one reaching Sink.touch; a Dispatcher dispatching Base.op) across the
# class/protocol engines (java, ts, swift; rust has no dispatch: → empty frontier, excluded). Asserts all
# present engines AGREE: the dispatcher is disclosed in possibleViaUnknownDispatch via dispatch on `op`
# (resolved against the hierarchy sidecar), with Impl7.op confirmed. Makes the frontier a verified
# contract, not just a per-engine feature (the [10] check pins only the vocabulary + dispatch shape).
#
# NOW A PRODUCER x CONSUMER MATRIX (2026-08-03), because it was three arms with only TWO independent
# consumers: candor-swift ships no `callers` verb, so its arm read swift's report with candor-rust's
# `candor-query` — unlabelled. A common-mode defect in the rust consumer would have shown up in the swift
# arm alone and read as a PRODUCER disagreement. Every producer's report now goes through every consumer:
# a red ROW is a consumer defect, a red COLUMN is a producer defect, a single red cell is a genuine
# pairwise disagreement. Verified to discriminate by injecting one of each. 9 pairs, 3 consumers.
[ -f "$HERE/frontier_differential.py" ] || { echo "FAIL: frontier_differential.py is missing"; exit 2; }
echo
(
  export CANDOR_JAVA_JAR="$JAR" CANDOR_QUERY_BIN="$QUERY"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/frontier_differential.py"
) || { echo "dispatch-frontier differential: FAILED"; rc=1; }

# PART 10 — unknownWhy VOCABULARY (SPEC §4 ⟨0.7⟩). Every `unknownWhy` entry any engine emits on the   [TIER 1]
# shared fixtures MUST use one of the four canonical kinds (reflect/native/dispatch/callback), and every
# `dispatch:` entry MUST carry the normative `owner.member` detail (a dot in the detail) — that uniform
# shape is what lets the 0.7 dispatch-frontier resolve identically across engines. A non-canonical prefix
# (the old `dispatch-broad:`/`call:`/`accessor:`/`ffi:`/… divergence) is a DIVERGE. Each engine emits only
# the kinds its language model produces (Rust: no `dispatch:`), so per-engine kind sets may differ — only
# the vocabulary + the dispatch shape are pinned, not which kinds appear.
echo
# THE SHARED FIXTURE CANNOT PRODUCE EVERY KIND AN ENGINE EMITS, AND THIS ROW WAS VACUOUS FOR ONE OF THEM.
# candor-scan's dominant `unknownWhy` kind on real code is `ambiguous:` (8710 of 19607 entries over a
# 1062-report census — more than `callback:`), and PART 10 never saw a single one, because the differential
# fixture has no bare call naming two same-name local defs. A vocabulary check that only reads the shared
# fixture pins the vocabulary of the shared fixture. So PART 10 also scans a tiny per-engine crate BUILT TO
# PRODUCE the kind, and asserts it actually appeared — a row that could not fail is not a check (item 8c).
mkdir -p "$W/vocab/src"
cat > "$W/vocab/Cargo.toml" <<'TOML'
[package]
name = "vocab"
version = "0.1.0"
TOML
# The real-world shape, reduced: cfg-gated alternative definitions of one free function. Rust's own name
# resolution picks by cfg; a syntactic scan cannot evaluate cfg, so the callee is genuinely ambiguous and
# the engine discloses rather than picking (which would fabricate one arm's effects onto the other).
cat > "$W/vocab/src/lib.rs" <<'RS'
#[cfg(unix)]
pub fn helper() { std::fs::read("/etc/a").ok(); }
#[cfg(windows)]
pub fn helper() { println!("pure"); }
pub fn go() { helper(); }
RS
"$SCAN" "$W/vocab" --json > "$W/vocab.json" 2>/dev/null || true
echo "[10] unknownWhy VOCABULARY (canonical kinds + dispatch:owner.member, SPEC §4 ⟨0.7⟩):"
python3 - "$RUST_REPORT" "$W/java.json" "${TS_OK:+$W/ts.json}" "${SW_REPORT:-}" "$W/vocab.json" <<'PY' || rc=1
import json, os, sys
# ⟨0.24⟩ FIVE canonical kinds. `ambiguous` was promoted from TOLERATED: §6.2 had always classed it
# `dispatch`, so consumers were right while producers emitting it were non-conforming, and reclassifying it
# to `indirect` was measured to take `deny E Unknown[dispatch]` from 58 of 200 crates to 0 of 200.
CANON = {"reflect", "native", "dispatch", "callback", "ambiguous"}
# Known migration kinds (SPEC §4 ⟨0.7⟩): an engine MAY still emit these while it reconciles its reasons
# onto the canonical four (MODEL.md tracks candor-java's task-handoff/indy). They WARN — visible, not
# silently allowed — but do NOT fail the suite, so a not-yet-reconciled engine is surfaced without being
# falsely red. Any OTHER off-vocabulary kind is a hard DIVERGE (the old `dispatch-broad:`/`call:`/… drift).
#
# `ambiguous:` IS IN THE SAME TOLERATED BUCKET, BUT FOR THE OPPOSITE REASON, AND THE DIFFERENCE IS WORTH
# WRITING DOWN. java's two are remnants awaiting reconciliation onto the canonical four. rust's names a
# state NONE of the four can express: a BARE FREE call whose leaf has two-or-more local definitions (the
# cfg-gated-alternatives shape above). It is not `dispatch:` — there is no owner type, so the NORMATIVE
# `owner.member` detail cannot be formed, and nothing virtual happens (exactly one function runs; it is the
# ANALYSER's name resolution that failed, not the program's). It is not `callback:` either — that kind is an
# unresolved HIGHER-ORDER invocation over a function VALUE, and it is not the residual bucket (the residual
# is reached by the ABSENCE of a reason). SPEC §6.2's reason-class table already anticipated this and names
# `ambiguous*` explicitly, ruling its class `dispatch`; §4's closed kind set has not caught up. Reconciling
# it is a SPEC rung, not an engine edit, and it is not free: measured, `deny E Unknown[dispatch]` fires on
# 58 of 200 crates.io crates today and on 0 of 200 if `ambiguous:` is reclassified `indirect`, because
# every other `dispatch:` rust emits requires a chained dependency. Tolerated + WARNED until that rung.
MIGRATION = {"task-handoff", "indy"}
# ⟨0.24⟩ REGISTERED, not tolerated and not migration: §6.2 holds these up as the CORRECT shape (a reason
# attached where the `Unknown` is created, per dependency ENTRY), so they must not sit in a bucket whose
# meaning is "being reconciled away". They project to `unresolved`.
REGISTERED = {"dep", "dep-stale"}
TOLERATED = set()   # ⟨0.24⟩ emptied — `ambiguous` is canonical, `dep*` registered. Kept so a future
                    # genuinely-transitional kind has a home that is neither canon nor a hard divergence.
labels = ["rust", "java", "ts", "swift", "rust(vocab)"]

# ⟨0.24⟩ THE CLASSIFICATION IS A FUNCTION SO THE NEGATIVE CONTROL CAN GO THROUGH IT.
# It used to be inlined in the loop below, and the control below tested the SET MEMBERSHIPS instead —
# `banana` not in CANON/REGISTERED/MIGRATION/TOLERATED. A review pointed out what that cannot see:
# neutralise the loop's `kind not in CANON -> DIVERGE` branch and the sets are UNCHANGED, so the control
# still prints green while every real off-vocabulary kind is accepted silently. The control was checking
# the data the decision reads, not the decision. One function, two callers, and the control now exercises
# the exact code path the engines' output does.
def classify(w, fn):
    """-> (verdict, message). verdict in {'ok','warn','diverge'}. THE decision path for §4 vocabulary."""
    kind = w.split(":", 1)[0]
    if kind in REGISTERED:
        return "ok", ""          # accepted silently: named by §4, classed by §6.2
    if kind in MIGRATION:
        return "warn", f"migration unknownWhy kind (not yet reconciled, SPEC §4): {w!r}  (fn {fn})"
    if kind in TOLERATED:
        return "warn", f"off-§4-vocabulary kind named+classed by SPEC §6.2: {w!r}  (fn {fn})"
    if kind not in CANON:
        return "diverge", f"non-canonical unknownWhy kind: {w!r}  (fn {fn})"
    if kind == "dispatch":
        # ⟨0.24⟩ A DOT-FREE DETAIL IS THE RESERVED "no owner could be formed" FORM — free text,
        # explicitly NOT conformance-compared. This check used to DIVERGE on it, which would hard-fail
        # the reference Rust engine on its DOMINANT dispatch reason
        # (`dispatch:untyped cross-package receiver`) the moment §4 ⟨0.24⟩ was implemented. The
        # dotted form is still normative WHERE AN OWNER WAS FORMED, so the shape is only checked
        # when a dot is present.
        detail = w.split(":", 1)[1] if ":" in w else ""
        if "." in detail and (detail.startswith(".") or detail.endswith(".")):
            return "diverge", f"dotted dispatch: detail must be owner.member: {w!r}  (fn {fn})"
    return "ok", ""

fails = 0; warns = 0; seen = {}; total = 0
for label, path in zip(labels, sys.argv[1:6]):
    if not path or not os.path.exists(path):
        continue
    try:
        d = json.load(open(path))
    except Exception:
        continue
    fns = d.get("functions", []) if isinstance(d, dict) else d
    for f in fns:
        for w in (f.get("unknownWhy") or f.get("unknown_why") or []):
            total += 1
            seen.setdefault(label, set()).add(w.split(":", 1)[0])
            verdict, msg = classify(w, f.get("fn"))
            if verdict == "warn":
                print(f"  WARN    [{label}] {msg}"); warns += 1
            elif verdict == "diverge":
                print(f"  DIVERGE [{label}] {msg}"); fails += 1
for label in labels:
    if label in seen:
        print(f"  {label}: kinds = {sorted(seen[label])}")
# THE PURPOSE-BUILT INPUT MUST HAVE PRODUCED THE KIND IT EXISTS FOR. Without this the row degrades
# silently the moment the fixture stops triggering (a resolution improvement, a parser change), and a
# vocabulary check nobody notices went quiet is exactly how `ambiguous:` stayed invisible for a release.
#
# ⟨0.24⟩ THE NEGATIVE CONTROL, and it is what makes the five rows above mean anything. Without it this PART
# cannot distinguish "pins five kinds" from "stopped checking the kind set" — the same diff. A fabricated
# off-vocabulary kind must still DIVERGE.
# Two probes, both through `classify` — the same function the loop above calls on every engine entry.
# One must DIVERGE (an off-vocabulary kind), one must NOT (a canonical kind), because a decision path
# that has been neutralised to accept everything and one that has been broken to reject everything are
# both dead, and a single probe can only see one of them.
_bad = classify("banana:whatever", "probe.f")[0]
_good = classify("reflect:Method.invoke", "probe.g")[0]
if _bad != "diverge":
    print(f"  DIVERGE [self-check] the fabricated kind `banana:` classified as {_bad!r}, not 'diverge' — "
          "the §4 vocabulary decision path has stopped discriminating"); fails += 1
elif _good != "ok":
    print(f"  DIVERGE [self-check] the canonical kind `reflect:` classified as {_good!r}, not 'ok' — the "
          "decision path rejects everything, so its DIVERGEs carry no information"); fails += 1
else:
    print("  self-check: `banana:` DIVERGEs and `reflect:` does not, through the same classifier the "
          "engine entries run through — the vocabulary check discriminates")
if "ambiguous" not in seen.get("rust(vocab)", set()):
    print("  DIVERGE [rust(vocab)] the purpose-built ambiguity fixture produced NO `ambiguous:` reason — "
          "this row's coverage of the off-vocabulary kind is vacuous, not passing"); fails += 1
suffix = "OK" if fails == 0 else f"{fails} violation(s)"
if warns: suffix += f", {warns} tolerated off-vocabulary warning(s)"
print(f"  {total} unknownWhy entr{'y' if total==1 else 'ies'} checked — " + suffix)
sys.exit(1 if fails else 0)
PY

# ====================================================================================================
# PART 11 — CONTAINMENT differential (SPEC §6.1 boundary-effect dispersion + AS-EFF-010 ratchet). The   [TIER 1]
# `containment` query is the architecture-drift gate's signature: which layer a boundary effect lives in,
# how contained it is, and a ratchet that FAILS when an effect leaks into a new layer. Two engines
# implement it INDEPENDENTLY — candor-java (file-based) and candor-query/Rust (prefix-based, also the path
# candor-swift's analyze-only reports are queried through); candor-ts has no `containment` command. This
# part proves they agree on BOTH the diagnostic and the ratchet verdict (the moat: the gate means the same
# thing cross-engine). Fixture: repo=Fs(×2), svc=Net; `current` adds an Fs leak in svc, `base` does not.
# ====================================================================================================
cp -r "$HERE/containment" "$W/containment"
# build + scan the Java current/base states
javac -d "$W/cont_jcur"  $(find "$W/containment/java/current" -name '*.java') 2>/dev/null || { echo "FAIL: javac on containment/java/current"; exit 2; }
javac -d "$W/cont_jbase" $(find "$W/containment/java/base"    -name '*.java') 2>/dev/null || { echo "FAIL: javac on containment/java/base"; exit 2; }
java -jar "$JAR" "$W/cont_jcur"  --json "$W/cont_jcur.json"  >/dev/null 2>&1 || { echo "FAIL: candor-java errored on containment/java/current"; exit 2; }
java -jar "$JAR" "$W/cont_jbase" --json "$W/cont_jbase.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on containment/java/base"; exit 2; }
# scan the Rust current/base states (candor-scan analyzes source in place)
"$SCAN" "$W/containment/rust/current" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on containment/rust/current"; exit 2; }
"$SCAN" "$W/containment/rust/base"    >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on containment/rust/base"; exit 2; }
# REPORT mode (the diagnostic). §3.3.1: containment's SINGLE positional is the BASELINE, so the report-mode
# diagnostic (no baseline) supplies the report via --report — a bare `containment <report>` now discovers +
# ratchets, never re-reads the lone positional as the report (the cardinal-sin gate-off this rung fixes).
java -jar "$JAR" containment --report "$W/cont_jcur.json" --json > "$W/cont_jrep.json" 2>/dev/null
"$QUERY" containment --report "$W/containment/rust/current/.candor/report" --json > "$W/cont_rrep.json" 2>/dev/null
# RATCHET mode (current vs base — AS-EFF-010); capture exit codes (1 = leak)
java -jar "$JAR" containment "$W/cont_jcur.json" "$W/cont_jbase.json" --json > "$W/cont_jrat.json" 2>/dev/null; jrat=$?
"$QUERY" containment "$W/containment/rust/current/.candor/report" "$W/containment/rust/base/.candor/report" --json > "$W/cont_rrat.json" 2>/dev/null; rrat=$?
python3 - "$W/cont_jrep.json" "$W/cont_rrep.json" "$W/cont_jrat.json" "$W/cont_rrat.json" "$jrat" "$rrat" <<'PY' || rc=1
import json, sys
jrep, rrep, jrat, rrat = (json.load(open(sys.argv[i])) for i in (1, 2, 3, 4))
jrx, rrx = int(sys.argv[5]), int(sys.argv[6])
def norm(rep):  # the comparable containment surface (drop java-only layerPrefix; key by effect)
    contained = {c["effect"]: {"containmentPct": c["containmentPct"], "layers": c["layers"],
                               "owner": c["owner"], "placement": c["placement"]} for c in rep.get("contained", [])}
    return contained, rep.get("ambient", {})
jc, ja = norm(jrep); rc_, ra = norm(rrep)
report_ok = (jc == rc_ and ja == ra)
ratchet_ok = (jrat.get("leaks") == rrat.get("leaks") and jrat.get("cleanups") == rrat.get("cleanups")
              and jrx == rrx == 1)
# FLOOR: not just "java == rust" — assert the engines actually produced the EXPECTED diagnostic for this
# fixture, so a TWO-SIDED regression (both emit empty `contained` / drop the leak) can't pass green.
EXP_FS = {"containmentPct": 66, "layers": 2, "owner": "repo", "placement": {"repo": 2, "svc": 1}}
EXP_NET = {"containmentPct": 100, "layers": 1, "owner": "svc", "placement": {"svc": 1}}
floor_ok = (jc.get("Fs") == EXP_FS and jc.get("Net") == EXP_NET and jrat.get("leaks") == ["Fs → svc"])
print("\n[11] CONTAINMENT differential  (SPEC §6.1 dispersion + AS-EFF-010 ratchet)")
print(f"  report : java {jc} ambient={ja}")
print(f"           rust {rc_} ambient={ra}")
print(f"           -> " + ("MATCH" if report_ok else "DIVERGE — engines disagree on the containment diagnostic"))
print(f"  ratchet: java leaks={jrat.get('leaks')} exit={jrx}   rust leaks={rrat.get('leaks')} exit={rrx}")
print(f"           -> " + ("MATCH — both flag the same leak and fail (exit 1)" if ratchet_ok
                           else "DIVERGE — engines disagree on the AS-EFF-010 ratchet verdict"))
if not floor_ok:
    print(f"           -> FLOOR FAILED — the engines agree but did NOT produce the expected diagnostic "
          f"(Fs={jc.get('Fs')} Net={jc.get('Net')} leaks={jrat.get('leaks')}); a two-sided regression?")
ok = report_ok and ratchet_ok and floor_ok
print("  -> " + ("MATCH — containment means the same thing in both engines" if ok else "DIVERGE"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 12 — GATE-VERDICT (SPEC §3.3 ⟨0.8⟩): `--gate-json` re-emits the policy verdict as machine JSON,   [TIER 1]
# from the SAME check that sets the exit code. LADDER-AWARE (SPEC §"Versioning policy"): exercised on
# every engine that DECLARES spec ≥ 0.8; an engine still on the 0.7 FLOOR is disclosed, not failed — it
# joins when it implements --gate-json and reaches 0.8, at which point this becomes a full differential.
# ====================================================================================================
echo
GDIR="$HERE/gate"; GPOL="$GDIR/policy"
# The SAME static two-rule fixture in every language; each engine's --gate-json verdict must AGREE, AND
# each engine's process EXIT CODE is captured and pinned against its verdict — §3.3's central clause
# (non-empty gate-failing violations ⟺ exit 1) was previously untested here (the runs ended in
# >/dev/null with no $? capture). Membership is REQUIRED, not file-existence: java+scan always, ts/swift
# whenever the engine is present-and-working (TS_OK/SW_OK) — a 0.8 engine whose --gate-json regresses to
# writing nothing must FAIL the differential, never silently drop out of it.
javac -d "$W/g_java" $(find "$GDIR/java" -name '*.java') 2>/dev/null || { echo "FAIL: javac on gate/java"; exit 2; }
java -jar "$JAR" "$W/g_java" --policy "$GPOL" --gate-json "$W/gv_java.json" >/dev/null 2>&1; GX_JAVA=$?
"$SCAN" "$GDIR/rust" --out "$W/g_rust" --policy "$GPOL" --gate-json "$W/gv_scan.json" >/dev/null 2>&1; GX_SCAN=$?
GX_TS=-1; [ -n "$TS_OK" ] && { node "$TS_DIR/scan.mjs" "$GDIR/ts" --out "$W/g_ts" --policy "$GPOL" --gate-json "$W/gv_ts.json" >/dev/null 2>&1; GX_TS=$?; }
GX_SW=-1; [ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && { "$SW_BIN" "$GDIR/swift" --out "$W/g_sw" --policy "$GPOL" --gate-json "$W/gv_swift.json" >/dev/null 2>&1; GX_SW=$?; }
python3 - "$W" "$GX_JAVA" "$GX_SCAN" "$GX_TS" "$GX_SW" <<'PY' || rc=1
import json, os, sys
W = sys.argv[1]
exits = dict(zip(["candor-java", "candor-scan", "candor-ts", "candor-swift"], map(int, sys.argv[2:6])))
engines = [("candor-java", "gv_java", True), ("candor-scan", "gv_scan", True),
           ("candor-ts", "gv_ts", exits["candor-ts"] >= 0), ("candor-swift", "gv_swift", exits["candor-swift"] >= 0)]
leaf = lambda s: s.replace("::", ".").split(".")[-1]
VALID_RC = {"reflect", "dispatch", "indirect", "native", "unresolved", "setup"}
rc_violations = []  # §6.2 ⟨0.19⟩ structural invariant, checked on every engine's verdicts
def norm(path):
    d = json.load(open(path))
    # §6.2 ⟨0.19⟩ reasonClass invariant (representation-agnostic — the VALUES may legitimately differ across
    # engines, but the CONTRACT is fixed): an AS-EFF-006 violation whose effects include `Unknown` MUST carry
    # a non-empty `reasonClass` of valid tokens; any other violation MUST NOT carry one. Guards every engine's
    # verdict without pinning class values (which are representationally divergent).
    for x in d["violations"]:
        rc = x.get("reasonClass", [])
        has_unknown = x["rule"] == "AS-EFF-006" and "Unknown" in x.get("effects", [])
        if has_unknown and (not rc or any(t not in VALID_RC for t in rc)):
            rc_violations.append(f"{path}: {x['rule']} on `{x['fn']}` denies Unknown but reasonClass={rc} (must be non-empty valid tokens)")
        if not has_unknown and rc:
            rc_violations.append(f"{path}: {x['rule']} on `{x['fn']}` carries reasonClass={rc} without denying Unknown")
    v = sorted((x["rule"], leaf(x["fn"]), tuple(sorted(x.get("effects", []))))
               for x in d["violations"] if x["rule"] != "AS-EFF-007")
    return d.get("spec"), bool(d["ok"]), v
print("[12] GATE-VERDICT differential  (SPEC §3.3 ⟨0.8⟩ — verdict AND exit code agree across every declaring engine)")
EXPECT = (False, [("AS-EFF-006", "save", ("Fs",)),    # deny Fs — the denied intersection
                  ("AS-EFF-008", "save", ("Fs",))])   # allow Fs, param path → uncertifiable (fail-closed); pure `add` absent
fails = []
for n, stem, required in engines:
    if not required:
        print(f"  {n:13s} not present on this runner — skipped (loudly)")
        continue
    path = f"{W}/{stem}.json"
    if not os.path.exists(path):
        fails.append(f"{n}: REQUIRED but wrote no verdict file")   # a regressed --gate-json must FAIL, not vanish
        continue
    spec, ok, v = norm(path)
    ex = exits[n]
    print(f"  {n:13s} spec={spec} exit={ex} ok={ok} violations={[(r, f, list(e)) for r, f, e in v]}")
    if (ok, v) != EXPECT:
        fails.append(f"{n}: verdict diverges from the pinned expectation")
    if ex != 1:
        fails.append(f"{n}: exit {ex} on a violating gate (must be 1)")
    if ok is not (ex == 0):
        fails.append(f"{n}: verdict ok={ok} DISAGREES with exit {ex} — the §3.3 MUST")
fails += rc_violations  # §6.2 ⟨0.19⟩ reasonClass structural invariant (representation-agnostic)
for f in fails:
    print(f"     FAIL {f}")
if not rc_violations:
    print("  reasonClass invariant: OK (no Unknown-denial verdict malformed a reasonClass — SPEC §6.2 ⟨0.19⟩)")
print("  -> " + ("MATCH — every declaring engine emits the same faithful verdict AND exit (ok:false · 006+008 on `save` · {Fs} · exit 1)"
                 if not fails else "DIVERGE — see FAIL lines"))
sys.exit(0 if not fails else 1)
PY

# ====================================================================================================
# PART 12b — FIX-GATE differential (integrations/FIX-SPEC.md): the remedy for a boundary crossing means the   [TIER 2]
# same thing in every engine. `whatif`/`--gate-json` say a boundary was crossed; `fix-gate` says WHERE the
# effect belongs + the hoist refactor. The same orderflow (api→domain→infra, all Net, the leaf direct) under
# `deny Net domain` MUST yield the same cut in each engine: same direct site, same pure span, same hoist
# target, same layer, same cleanHoist — modulo function-name spelling (the leaf-normalized shape). The
# remedial companion to PART 12's gate verdict; three-engine (R+J+T — swift has no `fix` port yet).
# ====================================================================================================
cp -r "$HERE/fix" "$W/fix"
FIXPOL="$W/fix/policy"
"$SCAN" "$W/fix/rust" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on the fix/rust fixture"; exit 2; }
"$QUERY" fix-gate "$W/fix/rust/.candor/report" "$FIXPOL" 1 > "$W/rust_fix.json" 2>/dev/null
javac -d "$W/fjout" $(find "$W/fix/java" -name '*.java') 2>/dev/null || { echo "FAIL: javac on fix/java"; exit 2; }
java -jar "$JAR" "$W/fjout" --json "$W/fjava.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on fix/java"; exit 2; }
java -jar "$JAR" fix-gate "$W/fjava.json" "$FIXPOL" --json > "$W/java_fix.json" 2>/dev/null
TS_FIX=""
if [ -n "$TS_OK" ] && [ -f "$TS_DIR/query.mjs" ]; then
  node "$TS_DIR/scan.mjs" "$W/fix/ts" "$W/fts" >/dev/null 2>&1 \
    && node "$TS_DIR/query.mjs" fix-gate "$W/fts" "$FIXPOL" > "$W/ts_fix.json" 2>/dev/null \
    && TS_FIX=1 \
    || { echo "FAIL: candor-ts is working but fix-gate produced no remedy — the FIX-SPEC parity witness vanished"; exit 2; }
fi
# candor-swift's `fix`/`fix-gate` port shipped 2026-07-11 — a read-only query over the report/callgraph a
# scan wrote. Four-way whenever the engine works: a working swift that can't emit a remedy is present-but-
# broken and FAILS, never a skip (same posture as PART 4's grammar witness).
SW_FIX=""
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  env -u CANDOR_CONFIG "$SW_BIN" "$W/fix/swift" --out "$W/fsw" >/dev/null 2>&1 \
    && env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/fsw" "$FIXPOL" > "$W/sw_fix.json" 2>/dev/null \
    && python3 -c 'import json,sys; json.load(open(sys.argv[1]))["remedies"]' "$W/sw_fix.json" >/dev/null 2>&1 \
    && SW_FIX=1 \
    || { echo "FAIL: candor-swift is working but fix-gate produced no remedy — the FIX-SPEC parity witness vanished"; exit 2; }
fi

python3 - "$W/rust_fix.json" "$W/java_fix.json" "${TS_FIX:+$W/ts_fix.json}" "${SW_FIX:+$W/sw_fix.json}" <<'PY' || rc=1
import json, sys
def norm(path, sep):
    d = json.load(open(path))
    leaf = lambda xs: sorted(x.split(sep)[-1] for x in xs)
    # the remedy, leaf-normalized: (site, pure span, hoist target, HIGHER hoist options, layer, cleanHoist, effect)
    return (bool(d["ok"]),
            sorted((tuple(leaf(r["site"])), tuple(leaf(r["deniedSpan"])), tuple(leaf(r["hoistTo"])),
                    tuple(leaf(r.get("hoistHigher", []))), r["layer"], bool(r["cleanHoist"]), r["effect"]) for r in d["remedies"]))
argv = sys.argv[1:]
rv, jv = norm(argv[0], "::"), norm(argv[1], ".")
tv = norm(argv[2], ".") if len(argv) > 2 and argv[2] else None
sv = norm(argv[3], ".") if len(argv) > 3 and argv[3] else None
print("\n[12b] FIX-GATE differential  (fix-gate  ·  policy `deny Net domain`  ·  orderflow api→domain→infra)")
print(f"  candor-scan: ok={rv[0]}  remedies={rv[1]}")
print(f"  candor-java: ok={jv[0]}  remedies={jv[1]}")
if tv is not None: print(f"  candor-ts:   ok={tv[0]}  remedies={tv[1]}")
if sv is not None: print(f"  candor-swift:ok={sv[0]}  remedies={sv[1]}")
match = all(v == rv for v in (jv, tv, sv) if v is not None)
print("  -> " + ("MATCH — the boundary remedy (site · pure span · hoist target · layer) is identical across the engines"
                 if match else "DIVERGE — the engines disagree on where the effect belongs or what stays pure"))
sys.exit(0 if match else 1)
PY

# 12b, EXIT-CODE contract (#3 corpus re-audit): fix-gate is ADVISORY (exit 0) by default — the agent fix-loop
# reads the remedy and edits — but `--strict` makes an OUTSTANDING crossing a CI failure (exit 1), matching
# `unverified --strict`. Same crossing (the orderflow under `deny Net domain`), two exit codes by flag, pinned
# four-way. Checked HERE while the callgraph sidecars still exist (the sidecar-absent block below strips them,
# which disables candor-ts fix-gate). Mirrors the proven positional invocations above, adding `--strict`.
echo "[12b] FIX-GATE exit-code contract  (advisory 0 · --strict 1 while a crossing remains · --strict 0 when clean)"
fixgate_exit() { local label="$1" want="$2"; shift 2; ( "$@" ) >/dev/null 2>&1; local got=$?
  [ "$got" = "$want" ] || { echo "  -> DIVERGE — $label: fix-gate exit $got, expected $want"; rc=1; }; }
# A policy that matches NO layer → no crossing → even --strict exits 0 (the "unchanged otherwise" control: it
# catches an engine that wired --strict to an unconditional exit 1, which the crossing-present checks miss).
CLEANPOL="$W/fix/clean.policy"; printf 'deny Net nonexistentlayer\n' > "$CLEANPOL"
fixgate_exit "rust advisory"      0 "$QUERY" fix-gate "$W/fix/rust/.candor/report" "$FIXPOL"
fixgate_exit "rust --strict"      1 "$QUERY" fix-gate "$W/fix/rust/.candor/report" "$FIXPOL" --strict
fixgate_exit "rust --strict clean" 0 "$QUERY" fix-gate "$W/fix/rust/.candor/report" "$CLEANPOL" --strict
fixgate_exit "java advisory"      0 java -jar "$JAR" fix-gate "$W/fjava.json" "$FIXPOL"
fixgate_exit "java --strict"      1 java -jar "$JAR" fix-gate "$W/fjava.json" "$FIXPOL" --strict
fixgate_exit "java --strict clean" 0 java -jar "$JAR" fix-gate "$W/fjava.json" "$CLEANPOL" --strict
if [ -n "$TS_FIX" ]; then
  fixgate_exit "ts advisory"      0 node "$TS_DIR/query.mjs" fix-gate "$W/fts" "$FIXPOL"
  fixgate_exit "ts --strict"      1 node "$TS_DIR/query.mjs" fix-gate "$W/fts" "$FIXPOL" --strict
  fixgate_exit "ts --strict clean" 0 node "$TS_DIR/query.mjs" fix-gate "$W/fts" "$CLEANPOL" --strict
else echo "  (ts fix-gate exit-code checks SKIPPED — engine unavailable)"; fi
if [ -n "$SW_FIX" ]; then
  fixgate_exit "swift advisory"      0 env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/fsw" "$FIXPOL"
  fixgate_exit "swift --strict"      1 env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/fsw" "$FIXPOL" --strict
  fixgate_exit "swift --strict clean" 0 env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/fsw" "$CLEANPOL" --strict
else echo "  (swift fix-gate exit-code checks SKIPPED — engine unavailable)"; fi
echo "  -> checked advisory=0 / --strict=1 / --strict-clean=0 on every working engine (a crossing is present)"

# 12b, sidecar-ABSENT: the report engines whose §2 report EMBEDS inline `calls` (candor-query, candor-java,
# candor-swift) must emit the SAME remedy when the `.callgraph.json` sidecar is gone — they fall back to the
# inline calls. (candor-query never reads the sidecar; java/swift fall back to `calls`.) A regression here is
# the degenerate empty-graph "no clean hoist" the /code-review caught in java. candor-ts is EXCLUDED on
# purpose: its report carries no inline `calls` (the sidecar is its only graph), so its fix/fix-gate FAIL LOUD
# (exit 2) without a sidecar rather than emit a degenerate remedy — asserted separately below.
rm -f "$W"/fix/rust/.candor/report.*.callgraph.json "$W"/fjava.callgraph.json "$W"/fts.callgraph.json "$W"/fsw.*.callgraph.json 2>/dev/null
"$QUERY" fix-gate "$W/fix/rust/.candor/report" "$FIXPOL" 1 > "$W/rust_fix2.json" 2>/dev/null
java -jar "$JAR" fix-gate "$W/fjava.json" "$FIXPOL" --json > "$W/java_fix2.json" 2>/dev/null
[ -n "$SW_FIX" ] && env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/fsw" "$FIXPOL" > "$W/sw_fix2.json" 2>/dev/null
python3 - "$W/rust_fix2.json" "$W/java_fix2.json" "${SW_FIX:+$W/sw_fix2.json}" <<'PY' || rc=1
import json, sys
def norm(path, sep):
    d = json.load(open(path))
    leaf = lambda xs: sorted(x.split(sep)[-1] for x in xs)
    return (bool(d["ok"]),
            sorted((tuple(leaf(r["site"])), tuple(leaf(r["deniedSpan"])), tuple(leaf(r["hoistTo"])),
                    tuple(leaf(r.get("hoistHigher", []))), r["layer"], bool(r["cleanHoist"]), r["effect"]) for r in d["remedies"]))
argv = sys.argv[1:]
rv, jv = norm(argv[0], "::"), norm(argv[1], ".")
sv = norm(argv[2], ".") if len(argv) > 2 and argv[2] else None
print("[12b] FIX-GATE differential, SIDECAR-ABSENT  (inline-`calls` fallback must match the sidecar cut)")
ok = rv[1] and all(v == rv for v in (jv, sv) if v is not None)  # rv[1] non-empty: a remedy still comes out
print("  -> " + ("MATCH — the inline-`calls` engines (query/java/swift) emit the identical remedy sidecar-less"
                 if ok else "DIVERGE — a sidecar-less report gives a different (likely degenerate) remedy in some engine"))
sys.exit(0 if ok else 1)
PY
# candor-ts (sidecar-only graph): fix-gate MUST fail loud (exit 2), never a degenerate "no crossings".
if [ -n "$TS_FIX" ]; then
  node "$TS_DIR/query.mjs" fix-gate "$W/fts" "$FIXPOL" >/dev/null 2>&1
  [ "$?" -eq 2 ] || { echo "  -> DIVERGE — candor-ts fix-gate without a sidecar must exit 2 (fail loud), not compute"; rc=1; }
fi

# 12b, SANDWICHED layer: an allowed layer CALLED BY a denied one (top → mid → inner → fetch, `deny Net
# domain`). The nearest allowed frontier (`mid`) is not a clean hoist — a denied caller (`top`) would still
# inherit the effect. Every engine MUST report cleanHoist=false, identically. (/code-review — was a misleading
# "hoist to mid" that wouldn't clear `top`.)
cp -r "$HERE/fix-sandwich" "$W/sw"
SWPOL="$W/sw/policy"
"$SCAN" "$W/sw/rust" >/dev/null 2>&1 && "$QUERY" fix-gate "$W/sw/rust/.candor/report" "$SWPOL" 1 > "$W/rust_sw.json" 2>/dev/null
javac -d "$W/swjout" $(find "$W/sw/java" -name '*.java') 2>/dev/null && java -jar "$JAR" "$W/swjout" --json "$W/swjava.json" >/dev/null 2>&1 && java -jar "$JAR" fix-gate "$W/swjava.json" "$SWPOL" --json > "$W/java_sw.json" 2>/dev/null
SWTS=""; [ -n "$TS_OK" ] && node "$TS_DIR/scan.mjs" "$W/sw/ts" "$W/swts" >/dev/null 2>&1 && node "$TS_DIR/query.mjs" fix-gate "$W/swts" "$SWPOL" > "$W/ts_sw.json" 2>/dev/null && SWTS=1
SWSW=""; [ -n "$SW_OK" ] && env -u CANDOR_CONFIG "$SW_BIN" "$W/sw/swift" --out "$W/swsw" >/dev/null 2>&1 && env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$W/swsw" "$SWPOL" > "$W/sw_sw.json" 2>/dev/null && SWSW=1
python3 - "$W/rust_sw.json" "$W/java_sw.json" "${SWTS:+$W/ts_sw.json}" "${SWSW:+$W/sw_sw.json}" <<'PY' || rc=1
import json, sys
def clean_flags(path):
    d = json.load(open(path))
    return [bool(r["cleanHoist"]) for r in d["remedies"]], len(d["remedies"])
print("[12b] FIX-GATE differential, SANDWICHED layer  (allowed layer called by a denied one → NOT a clean hoist)")
names = ["candor-scan", "candor-java", "candor-ts", "candor-swift"]
ok = True
for p, n in zip(sys.argv[1:], names):
    if not p: continue
    flags, cnt = clean_flags(p)
    good = cnt >= 1 and all(f is False for f in flags)  # a remedy exists and NONE claims a clean hoist
    ok = ok and good
    print(f"  {n:12s} remedies={cnt} cleanHoist={flags} {'ok' if good else 'DIVERGE'}")
print("  -> " + ("MATCH — every engine reports the sandwiched frontier as NOT a clean hoist"
                 if ok else "DIVERGE — an engine still claims a clean hoist into a sandwiched layer"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 12c — UNVERIFIED differential (integrations/FIX-SPEC.md, eval/fixloop/DISPATCH-NOTE.md): the provable-   [TIER 2]
# purity disclosure means the same thing in every engine. `domain::price` calls through a FUNCTION VALUE →
# Unknown; `pure domain` PASSES it, but its purity is UNVERIFIED. Every engine's `unverified` MUST flag the
# same function with the same `deny Unknown domain` upgrade (leaf-normalized). Four-way.
# ====================================================================================================
cp -r "$HERE/unverified" "$W/unv"
UNVPOL="$W/unv/policy"
"$SCAN" "$W/unv/rust" >/dev/null 2>&1 && "$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVPOL" 1 > "$W/rust_unv.json" 2>/dev/null
javac -d "$W/unvjout" $(find "$W/unv/java" -name '*.java') 2>/dev/null && java -jar "$JAR" "$W/unvjout" --json "$W/unvjava.json" >/dev/null 2>&1 && java -jar "$JAR" unverified "$W/unvjava.json" "$UNVPOL" --json > "$W/java_unv.json" 2>/dev/null
UNVTS=""; [ -n "$TS_OK" ] && node "$TS_DIR/scan.mjs" "$W/unv/ts" "$W/unvts" >/dev/null 2>&1 && node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVPOL" > "$W/ts_unv.json" 2>/dev/null && UNVTS=1
UNVSW=""; [ -n "$SW_OK" ] && env -u CANDOR_CONFIG "$SW_BIN" "$W/unv/swift" --out "$W/unvsw" >/dev/null 2>&1 && env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVPOL" > "$W/sw_unv.json" 2>/dev/null && UNVSW=1
python3 - "$W/rust_unv.json" "$W/java_unv.json" "${UNVTS:+$W/ts_unv.json}" "${UNVSW:+$W/sw_unv.json}" <<'PY' || rc=1
import json, sys
def norm(path, sep):
    d = json.load(open(path))
    # leaf-normalize each hole: (fn leaf, upgrade). The upgrade is engine-independent (deny Unknown domain).
    return (bool(d["ok"]), sorted((h["fn"].split(sep)[-1], h["upgrade"]) for h in d["unverified"]))
argv = sys.argv[1:]
rv, jv = norm(argv[0], "::"), norm(argv[1], ".")
tv = norm(argv[2], ".") if len(argv) > 2 and argv[2] else None
sv = norm(argv[3], ".") if len(argv) > 3 and argv[3] else None
print("[12c] UNVERIFIED differential  (fn-value port under `pure domain` → a provable-purity hole)")
for n, v in [("candor-scan", rv), ("candor-java", jv), ("candor-ts", tv), ("candor-swift", sv)]:
    if v is not None: print(f"  {n:12s} ok={v[0]}  holes={v[1]}")
match = rv[1] and all(v == rv for v in (jv, tv, sv) if v is not None)  # a hole is found and all agree
print("  -> " + ("MATCH — every engine discloses the same unverified-purity hole + the same upgrade"
                 if match else "DIVERGE — the engines disagree on the provable-purity disclosure"))
sys.exit(0 if match else 1)
PY

# 12c, EXIT-CODE contract (#3 / Fable-review finding F2): `unverified` is the THIRD advisory verb of the
# ⟨0.18⟩ trio (SPEC §3.3.1), but only fix-gate/gains had their exit codes pinned. Pin it here too: advisory
# (exit 0) discloses the hole; `--strict` → exit 1 while a hole remains; `--strict` over a policy with NO hole
# stays 0 (the "unchanged otherwise" control). Reuses the reports produced above; UNVPOL has a hole.
echo "[12c] UNVERIFIED exit-code contract  (advisory 0 · --strict 1 while a hole remains · --strict 0 when clean)"
unv_exit() { local label="$1" want="$2"; shift 2; ( "$@" ) >/dev/null 2>&1; local got=$?
  [ "$got" = "$want" ] || { echo "  -> DIVERGE — $label: unverified exit $got, expected $want"; rc=1; }; }
UNVCLEAN="$W/unv/clean.policy"; printf 'pure nonexistentlayer\n' > "$UNVCLEAN"
unv_exit "rust advisory"      0 "$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVPOL"
unv_exit "rust --strict"      1 "$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVPOL" --strict
unv_exit "rust --strict clean" 0 "$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVCLEAN" --strict
unv_exit "java advisory"      0 java -jar "$JAR" unverified "$W/unvjava.json" "$UNVPOL"
unv_exit "java --strict"      1 java -jar "$JAR" unverified "$W/unvjava.json" "$UNVPOL" --strict
unv_exit "java --strict clean" 0 java -jar "$JAR" unverified "$W/unvjava.json" "$UNVCLEAN" --strict
if [ -n "$UNVTS" ]; then
  unv_exit "ts advisory"      0 node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVPOL"
  unv_exit "ts --strict"      1 node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVPOL" --strict
  unv_exit "ts --strict clean" 0 node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVCLEAN" --strict
else echo "  (ts unverified exit-code checks SKIPPED — engine unavailable)"; fi
if [ -n "$UNVSW" ]; then
  unv_exit "swift advisory"      0 env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVPOL"
  unv_exit "swift --strict"      1 env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVPOL" --strict
  unv_exit "swift --strict clean" 0 env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVCLEAN" --strict
else echo "  (swift unverified exit-code checks SKIPPED — engine unavailable)"; fi
echo "  -> checked advisory=0 / --strict=1 / --strict-clean=0 on every working engine (a hole is present)"

# 12c-deny — the SAME hole under a `deny Net Db domain` rule exercises the OTHER upgrade branch: the
# multi-effect `deny <E…> Unknown <scope>` form. `pure domain` (above) only pins the empty-effects branch;
# this pins the effect-list formatting AND its ORDER (every engine sorts → `deny Db Net Unknown domain`),
# where a drift would otherwise pass unnoticed. Reuses the reports/classes already produced above.
UNVPOLD="$W/unv/policy-deny"
"$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVPOLD" 1 > "$W/rust_unvd.json" 2>/dev/null
java -jar "$JAR" unverified "$W/unvjava.json" "$UNVPOLD" --json > "$W/java_unvd.json" 2>/dev/null
[ -n "$UNVTS" ] && node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVPOLD" > "$W/ts_unvd.json" 2>/dev/null
[ -n "$UNVSW" ] && env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVPOLD" > "$W/sw_unvd.json" 2>/dev/null
python3 - "$W/rust_unvd.json" "$W/java_unvd.json" "${UNVTS:+$W/ts_unvd.json}" "${UNVSW:+$W/sw_unvd.json}" <<'PY' || rc=1
import json, sys
def norm(path, sep):
    d = json.load(open(path))
    return (bool(d["ok"]), sorted((h["fn"].split(sep)[-1], h["upgrade"]) for h in d["unverified"]))
argv = sys.argv[1:]
rv, jv = norm(argv[0], "::"), norm(argv[1], ".")
tv = norm(argv[2], ".") if len(argv) > 2 and argv[2] else None
sv = norm(argv[3], ".") if len(argv) > 3 and argv[3] else None
print("[12c-deny] UNVERIFIED multi-effect branch  (same hole under `deny Net Db domain` → the `deny <E…> Unknown` upgrade)")
for n, v in [("candor-scan", rv), ("candor-java", jv), ("candor-ts", tv), ("candor-swift", sv)]:
    if v is not None: print(f"  {n:12s} ok={v[0]}  holes={v[1]}")
# the expected upgrade is the SORTED effect list — `deny Db Net Unknown domain` — in EVERY engine
want = ("price", "deny Db Net Unknown domain")
match = rv[1] and all(want in v[1] for v in (rv, jv, tv, sv) if v is not None) and all(v == rv for v in (jv, tv, sv) if v is not None)
print("  -> " + ("MATCH — every engine emits the same sorted multi-effect upgrade `deny Db Net Unknown domain`"
                 if match else "DIVERGE — the engines disagree on the multi-effect upgrade (effect set or ORDER)"))
sys.exit(0 if match else 1)
PY

# 12c-multi — the TIE-BREAK: when TWO in-scope rules both govern the same passing-but-Unknown fn, which one
# does the disclosure name? Policy `pure domain` THEN `deny Net domain` — the fn passes BOTH (no real effect;
# no Net) and is Unknown. Every engine must name the FIRST governing rule (parse order) → `deny Unknown domain`,
# NOT the second (`deny Net Unknown domain`). Pins first-match + iteration order across the fold, so a future
# one-engine refactor (e.g. splitting pure/deny into separate lists, or break-on-first-in-scope) can't silently
# disclose a different rule than the other three (max-review finding, 2026-07-11).
UNVPOLM="$W/unv/policy-multi"
"$QUERY" unverified "$W/unv/rust/.candor/report" "$UNVPOLM" 1 > "$W/rust_unvm.json" 2>/dev/null
java -jar "$JAR" unverified "$W/unvjava.json" "$UNVPOLM" --json > "$W/java_unvm.json" 2>/dev/null
[ -n "$UNVTS" ] && node "$TS_DIR/query.mjs" unverified "$W/unvts" "$UNVPOLM" > "$W/ts_unvm.json" 2>/dev/null
[ -n "$UNVSW" ] && env -u CANDOR_CONFIG "$SW_BIN" unverified "$W/unvsw" "$UNVPOLM" > "$W/sw_unvm.json" 2>/dev/null
python3 - "$W/rust_unvm.json" "$W/java_unvm.json" "${UNVTS:+$W/ts_unvm.json}" "${UNVSW:+$W/sw_unvm.json}" <<'PY' || rc=1
import json, sys
def norm(path, sep):
    d = json.load(open(path))
    return sorted((h["fn"].split(sep)[-1], h["upgrade"]) for h in d["unverified"])
argv = sys.argv[1:]
rv, jv = norm(argv[0], "::"), norm(argv[1], ".")
tv = norm(argv[2], ".") if len(argv) > 2 and argv[2] else None
sv = norm(argv[3], ".") if len(argv) > 3 and argv[3] else None
print("[12c-multi] UNVERIFIED tie-break  (two governing rules `pure domain`+`deny Net domain` → the FIRST wins)")
for n, v in [("candor-scan", rv), ("candor-java", jv), ("candor-ts", tv), ("candor-swift", sv)]:
    if v is not None: print(f"  {n:12s} holes={v}")
# the first governing rule is `pure domain` → upgrade `deny Unknown domain` (NOT the later `deny Net …`)
want = ("price", "deny Unknown domain")
match = rv and all(want in v for v in (rv, jv, tv, sv) if v is not None) and all(v == rv for v in (jv, tv, sv) if v is not None)
print("  -> " + ("MATCH — every engine names the FIRST governing rule (`deny Unknown domain`), same tie-break"
                 if match else "DIVERGE — the engines disagree on which of two governing rules the disclosure names"))
sys.exit(0 if match else 1)
PY

# ====================================================================================================
# PART 12d — GATE AUTO-DISCLOSURE differential (spec 0.23 — candor-scan/java/ts/swift 0.13.0):   [TIER 2]
# a plain `--policy` gate scan must emit the SAME provable-purity holes that `unverified` (12c) reports —
# automatically, as an advisory stderr note, WITHOUT the operator knowing to run the subcommand. This pins
# the discovery path: every engine, scanning the fn-value-port fixture under `pure domain`, PASSES the gate
# AND prints `<fn> → add deny Unknown domain` for the unverified layer. Four-way, leaf-normalized. Guards
# against one engine's gate going silent on the gap while another discloses it.
# ====================================================================================================
"$SCAN" "$W/unv/rust" --out "$W/gd_rust" --policy "$UNVPOL" > /dev/null 2> "$W/gd_rust.err"
java -jar "$JAR" "$W/unvjout" --policy "$UNVPOL" > /dev/null 2> "$W/gd_java.err"
GDTS=""; [ -n "$TS_OK" ] && { node "$TS_DIR/scan.mjs" "$W/unv/ts" --out "$W/gd_ts" --policy "$UNVPOL" > /dev/null 2> "$W/gd_ts.err"; GDTS=1; }
GDSW=""; [ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && { env -u CANDOR_CONFIG "$SW_BIN" "$W/unv/swift" --out "$W/gd_sw" --policy "$UNVPOL" > /dev/null 2> "$W/gd_sw.err"; GDSW=1; }
python3 - "$W/gd_rust.err" "$W/gd_java.err" "${GDTS:+$W/gd_ts.err}" "${GDSW:+$W/gd_sw.err}" <<'PY' || rc=1
import re, sys
# Each engine's disclosure note carries lines of the form:  `<fn>`  → add  `<upgrade>`
PAT = re.compile(r"`([^`]+)`\s*→\s*add\s*`([^`]+)`")
def holes(path):
    if not path: return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    # leaf-normalize the fn (split on both separators); the upgrade is engine-independent
    out = []
    for fn, up in PAT.findall(txt):
        leaf = fn.replace("::", ".").split(".")[-1]
        out.append((leaf, up.strip()))
    return sorted(out)
argv = sys.argv[1:]
rv, jv = holes(argv[0]), holes(argv[1])
tv = holes(argv[2]) if len(argv) > 2 else None
sv = holes(argv[3]) if len(argv) > 3 else None
print("[12d] GATE AUTO-DISCLOSURE differential  (a plain `--policy` scan discloses the same holes as `unverified`)")
for n, v in [("candor-scan", rv), ("candor-java", jv), ("candor-ts", tv), ("candor-swift", sv)]:
    if v is not None: print(f"  {n:12s} note-holes={v}")
found = bool(rv) and all(v == rv for v in (jv, tv, sv) if v is not None)  # a hole is disclosed and all agree
print("  -> " + ("MATCH — every engine's gate auto-discloses the same unverified-purity hole + upgrade"
                 if found else "DIVERGE — an engine's gate went silent on the provable-purity gap"))
sys.exit(0 if found else 1)
PY

# 12d-deny — the gate auto-disclosure over the multi-effect branch: a `--policy deny Net Db domain` scan must
# print the SAME `deny Db Net Unknown domain` upgrade the `unverified` subcommand does (12c-deny), four-way.
"$SCAN" "$W/unv/rust" --out "$W/gdd_rust" --policy "$UNVPOLD" > /dev/null 2> "$W/gdd_rust.err"
java -jar "$JAR" "$W/unvjout" --policy "$UNVPOLD" > /dev/null 2> "$W/gdd_java.err"
[ -n "$GDTS" ] && node "$TS_DIR/scan.mjs" "$W/unv/ts" --out "$W/gdd_ts" --policy "$UNVPOLD" > /dev/null 2> "$W/gdd_ts.err"
[ -n "$GDSW" ] && env -u CANDOR_CONFIG "$SW_BIN" "$W/unv/swift" --out "$W/gdd_sw" --policy "$UNVPOLD" > /dev/null 2> "$W/gdd_sw.err"
python3 - "$W/gdd_rust.err" "$W/gdd_java.err" "${GDTS:+$W/gdd_ts.err}" "${GDSW:+$W/gdd_sw.err}" <<'PY' || rc=1
import re, sys
PAT = re.compile(r"`([^`]+)`\s*→\s*add\s*`([^`]+)`")
def holes(path):
    if not path: return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    return sorted((fn.replace("::", ".").split(".")[-1], up.strip()) for fn, up in PAT.findall(txt))
argv = sys.argv[1:]
rv, jv = holes(argv[0]), holes(argv[1])
tv = holes(argv[2]) if len(argv) > 2 else None
sv = holes(argv[3]) if len(argv) > 3 else None
print("[12d-deny] GATE AUTO-DISCLOSURE multi-effect branch  (`--policy deny Net Db domain` note → sorted upgrade)")
for n, v in [("candor-scan", rv), ("candor-java", jv), ("candor-ts", tv), ("candor-swift", sv)]:
    if v is not None: print(f"  {n:12s} note-holes={v}")
want = ("price", "deny Db Net Unknown domain")
found = bool(rv) and all(want in v for v in (rv, jv, tv, sv) if v is not None) and all(v == rv for v in (jv, tv, sv) if v is not None)
print("  -> " + ("MATCH — every engine's gate note emits the same sorted multi-effect upgrade"
                 if found else "DIVERGE — an engine's gate note disagrees on the multi-effect upgrade"))
sys.exit(0 if found else 1)
PY

# ====================================================================================================
# PART 13 — .CANDOR/CONFIG differential (SPEC §config): the checked-in gate source means the same thing   [TIER 1]
# in every engine. Three pinned behaviors, per engine: (a) a .candor/config discovered from the SCAN
# TARGET's ancestors supplies the policy → the gate fires (exit 1) with no flag and no env; (b) the
# CANDOR_POLICY env OVERRIDES the config (a passing policy wins → exit 0); (c) a set-but-unusable
# CANDOR_CONFIG fails closed (exit 2) — configured gate sources never vanish silently.
# ====================================================================================================
echo
echo "[13] .CANDOR/CONFIG differential  (SPEC §config — discovery, precedence, fail-closed agree)"
CFGW="$W/cfg"; mkdir -p "$CFGW"
cp -r "$GDIR/rust" "$CFGW/rust"; cp -r "$GDIR/ts" "$CFGW/ts"; cp -r "$GDIR/swift" "$CFGW/swift"
mkdir -p "$CFGW/java"; javac -d "$CFGW/java" $(find "$GDIR/java" -name '*.java') 2>/dev/null
printf 'deny Net\n' > "$CFGW/pass.policy"   # the fixtures do Fs only → deny Net passes
for eng in java rust ts swift; do
  mkdir -p "$CFGW/$eng/.candor"
  printf 'policy %s\npolcy typo\n' "$GPOL" > "$CFGW/$eng/.candor/config"
done
cfg_probe() { # $1 engine label, then the scan command (target LAST for readability of callers)
  local label=$1; shift
  local rc_a rc_b rc_c err_a warn=no
  err_a=$(env -u CANDOR_POLICY -u CANDOR_CONFIG "$@" 2>&1 >/dev/null); rc_a=$?
  # the config carries a `polcy typo` line: §3.4's unknown-key posture requires a warning NAMING the
  # key — a misspelt gate key silently ignored is a silently-dropped gate (previously unasserted).
  case "$err_a" in *polcy*) warn=yes;; esac
  env -u CANDOR_CONFIG CANDOR_POLICY="$CFGW/pass.policy" "$@" >/dev/null 2>&1; rc_b=$?
  env -u CANDOR_POLICY CANDOR_CONFIG="$CFGW/no-such-config" "$@" >/dev/null 2>&1; rc_c=$?
  echo "  $label config-gate=$rc_a env-override=$rc_b typo-config=$rc_c unknown-key-warned=$warn"
  [ "$rc_a" = 1 ] && [ "$rc_b" = 0 ] && [ "$rc_c" = 2 ] && [ "$warn" = yes ] && return 0
  echo "     FAIL $label: expected 1/0/2 + a warning naming the unknown key 'polcy'"; return 1
}
CFG_OK=0
cfg_probe "candor-java " java -jar "$JAR" "$CFGW/java" || CFG_OK=1
cfg_probe "candor-scan " "$SCAN" "$CFGW/rust" --out "$CFGW/r_rep" || CFG_OK=1
[ -n "$TS_OK" ] && { cfg_probe "candor-ts   " node "$TS_DIR/scan.mjs" "$CFGW/ts" --out "$CFGW/t_rep" || CFG_OK=1; }
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && { cfg_probe "candor-swift" "$SW_BIN" "$CFGW/swift" --out "$CFGW/s_rep" || CFG_OK=1; }
if [ "$CFG_OK" = 0 ]; then
  echo "  -> MATCH — .candor/config discovery, env precedence and fail-closed agree across the engines"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 13b — CONFIG VOCABULARY + INERT-KEY DISCLOSURE, four-way (SPEC §config, the ⟨0.9⟩ inert-key    [TIER 1]
# amendment). PART 13 pins that a MISSPELT key warns. This pins the two ways an engine can be wrong
# about a key it DOES recognize — both of which were live in three engines until 2026-07-24, and both
# of which four-way agreement was structurally blind to, because every engine was wrong the same way:
#
#   (a) FALSE "unknown key". `net-partner` and `unknown-alias` are multi-value keys read straight from
#       the config TEXT (they cannot ride the single-value map), and they are HONOURED — setting
#       `net-partner h` flips a host's netClass from `unknown-host` to `known-partner`. Yet rust/ts/
#       swift omitted them from the recognized vocabulary, so a config that set one printed "ignoring
#       unknown config key" WHILE APPLYING THE VALUE. A tool whose contract is that its statements
#       about itself are true cannot ship an actively false disclosure; it is worse than a silent one.
#       PINNED: no engine may report ANY family key as unknown.
#
#   (b) SILENTLY INERT key. An engine that recognizes a gate key it does not implement must SAY SO —
#       a checked-in enforcement key that quietly does nothing reads to its author as a gate that is
#       ON (a declared-gate-silently-off). rust disclosed it; ts and swift said nothing. PINNED: a key
#       an engine does not implement draws a disclosure NAMING it.
#
# The suite asserts the union invariant, which is uniform across engines even though the implemented
# SETS differ (java wires all ten; rust/ts/swift wire policy/baseline/deps/unknown-ratchet plus the two
# text-parsed multi-value keys): FOR EVERY FAMILY KEY, an engine either honours it or discloses that it
# does not — never silently ignores it, and never calls it unknown.
# ====================================================================================================
echo
echo "[13b] CONFIG VOCABULARY + INERT-KEY disclosure  (SPEC §config — recognized keys are never 'unknown', never silent)"
VOCW="$W/cfgvocab"; mkdir -p "$VOCW"
cp -r "$GDIR/rust" "$VOCW/rust"; cp -r "$GDIR/ts" "$VOCW/ts"; cp -r "$GDIR/swift" "$VOCW/swift"
mkdir -p "$VOCW/java"; javac -d "$VOCW/java" $(find "$GDIR/java" -name '*.java') 2>/dev/null
# The shared family vocabulary (candor-spec §config). A key here is RECOGNIZED by every engine.
#
# `engine` (⟨0.28 PROPOSED⟩ §3.4) is here from the release that introduces it, and that timing is the
# point. It shipped ASYMMETRIC for a few hours — java enforcing, the rest disclosing it as inert — which
# is exactly the shape that produced the `net-partner` false disclosure: a key reported as ignored while
# a sibling engine honoured it. ALL FIVE now enforce it (PART 33 pins that), so this row's job is the
# narrower one it was always for: the key is RECOGNIZED, never reported unknown. The probe value stays
# qualified for an implementation none of the probed engines are, so it exercises the parse without
# becoming an enforcement test — that belongs to PART 33.
VOCAB="policy baseline strict no-ambient closed-world taint deps unknown-alias net-partner unknown-ratchet engine"
# Keys that carry a VALUE the parser needs; the rest are booleans/flags. Values are inert for this part
# (nothing is enforced — we read stderr only), they just have to parse.
#
# `engine`'s value is QUALIFIED FOR AN IMPLEMENTATION NONE OF THE PROBED ENGINES ARE. candor-java is the
# one engine that acts on this key, and a pin naming a version it is not would exit 2 — turning a
# vocabulary probe into an enforcement test and failing the part for the wrong reason. `agents` is a
# real §3.4 implementation name, so the line PARSES as a pin (this still exercises the parse path) while
# resolving to "not mine" for all four probed engines. Version-independent by construction: no build
# number can drift into or out of agreement with it.
vocab_val() { case "$1" in policy|baseline) echo "$GPOL";; deps) echo "$VOCW";; unknown-alias) echo "blind=dispatch";;
                           net-partner) echo "partner.example";; engine) echo "agents v0.0.1";;
                           *) echo "true";; esac; }
# WHICH ENGINE IMPLEMENTS WHICH KEY — the fact check (c) below cannot observe from stderr. `label:key`
# pairs, using the same padded labels the probes are called with. Every engine implements `policy`,
# `baseline`, `deps`, `unknown-ratchet` and (since ⟨0.27⟩) `engine`; `unknown-alias` and `net-partner` are
# multi-value keys read straight off the config TEXT, so they never reach the single-value loop and are
# listed here for the same reason. The remainder (`strict`, `no-ambient`, `closed-world`, `taint`) are
# java-only gates and MUST be disclosed as inert everywhere else.
IMPLEMENTED_BY=""
for _e in "candor-java " "candor-scan " "candor-ts   " "candor-swift"; do
  for _k in policy baseline deps unknown-ratchet engine unknown-alias net-partner; do
    IMPLEMENTED_BY="$IMPLEMENTED_BY $_e:$_k"
  done
done
for _k in strict no-ambient closed-world taint; do IMPLEMENTED_BY="$IMPLEMENTED_BY candor-java :$_k"; done

vocab_probe() { # $1 engine label, then the scan command (target LAST)
  local label=$1; shift
  local bad=0 k out cfgdir
  # THIS PART RAN NO ENGINE FOR ITS ENTIRE EXISTENCE. Finding the target used to be
  #     cfgdir=$1; while [ $# -gt 1 ]; do shift; cfgdir=$1; done
  # which locates the last argument by SHIFTING THE OTHERS AWAY — so by the time the probe reached
  # `env … "$@"`, `$@` held only the target directory and the engine command was gone. Every run
  # therefore executed the DIRECTORY, got `env: /path: Permission denied`, and matched that string
  # against `*"unknown config key '<k>'"*` and `*"<k>"*`. Neither can ever match, so both checks passed
  # unconditionally and every engine was reported `vocabulary=clean inert-disclosure=well-formed`.
  #
  # This is the part written after the `net-partner` false disclosure — a key reported as ignored while
  # it was being honoured — and its whole job is to pin that a recognized key is never called unknown
  # and never silently dropped. It could not have caught that defect, or any other.
  #
  # Found by adding `engine` to VOCAB and then trying to make the new row FAIL: removing `engine` from
  # candor-ts's vocabulary (verified applied) changed nothing. A row that cannot fail is worth nothing,
  # which is exactly why the negative control is run before the addition is believed.
  local cmd=( "$@" )
  cfgdir="${cmd[$(( ${#cmd[@]} - 1 ))]}"     # last element, WITHOUT destroying the command
  mkdir -p "$cfgdir/.candor"
  for k in $VOCAB; do
    printf '%s %s\n' "$k" "$(vocab_val "$k")" > "$cfgdir/.candor/config"
    out=$(env -u CANDOR_POLICY -u CANDOR_CONFIG "${cmd[@]}" 2>&1 >/dev/null)
    # (a) a RECOGNIZED key must never be called unknown — the false-disclosure class.
    case "$out" in
      *"unknown config key '$k'"*)
        echo "     FAIL $label: '$k' is family vocabulary but reported UNKNOWN"; bad=1; continue;;
    esac
    # (b) a CONFIG DIAGNOSTIC about this key must be the sanctioned inert disclosure.
    #
    # MATCHED ON THE QUOTED FORM, `config key '<k>'`, not on the bare key name. The bare form was the
    # rule until this part was repaired and actually ran the engines — at which point it reported seven
    # failures, all false: an engine that HONOURS `policy` says `policy ✓`, and one that honours
    # `baseline` names it in the guard's own message. Those are the key WORKING, and flagging them as
    # malformed disclosures would have made the repaired part unusable on its first green run.
    # The quoted form is what every engine's config layer uses for a diagnostic ABOUT a key
    # (`config key 'strict' is recognized … not implemented by candor-scan`), so it separates "the
    # engine is talking about this config key" from "the engine is doing what the key asked".
    case "$out" in
      *"config key '$k'"*)
        case "$out" in
          *"not implemented by"*) : ;;                       # the sanctioned inert disclosure
          *) echo "     FAIL $label: '$k' drew a config diagnostic that is not the sanctioned disclosure"; bad=1;;
        esac;;
      *)
        # (c) SILENCE IS NOT A PASS. This was the hole left when the part was repaired: an engine that
        # neither honours a key nor discloses it said nothing, and saying nothing matched no case, so
        # it passed as "wired". That reading is only safe for a key the engine really does implement —
        # which is a fact the suite cannot see from stderr, so it is supplied here per engine.
        #
        # Kept as a DENYLIST of the keys each engine implements, so a NEW family key defaults to
        # "must disclose": forgetting to add a key is then loud, which is the direction this project
        # takes everywhere else. An engine that starts implementing a key and forgets to move it here
        # fails too, and that is right — its inert disclosure would then be a false one.
        case " $IMPLEMENTED_BY " in
          *" $label:$k "*) : ;;                              # implemented here → silence is correct
          *) echo "     FAIL $label: '$k' is family vocabulary, is not implemented here, and drew NO"
             echo "          disclosure at all — silence reads as 'wired' and is how an inert gate stays believed"
             bad=1;;
        esac;;
    esac
  done
  rm -f "$cfgdir/.candor/config"
  [ "$bad" = 0 ] && { echo "  $label vocabulary=clean inert-disclosure=well-formed"; return 0; }
  return 1
}
VOC_OK=0
vocab_probe "candor-java " java -jar "$JAR" "$VOCW/java" || VOC_OK=1
vocab_probe "candor-scan " "$SCAN" "$VOCW/rust" || VOC_OK=1
[ -n "$TS_OK" ] && { vocab_probe "candor-ts   " node "$TS_DIR/scan.mjs" "$VOCW/ts" || VOC_OK=1; }
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && { vocab_probe "candor-swift" "$SW_BIN" "$VOCW/swift" || VOC_OK=1; }
if [ "$VOC_OK" = 0 ]; then
  echo "  -> MATCH — every engine recognizes the whole family vocabulary, and discloses what it does not implement"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 14 — CHAINING differential (SPEC §2 `CANDOR_DEPS` — 0.4 MUSTs, previously unpinned): the same   [TIER 1]
# dep+app pair per language, scanned app-only with the dep's report chained. Three pinned behaviors:
# (a) JOIN-INHERIT — the app fn inherits the dep fn's effects AND its literal surface (Net + host);
# (b) STALE-DOWNGRADE — a dep report whose producing version was doctored is not trusted: the call
#     downgrades to `Unknown`, never a stale Net claim (§2.1 at the join);
# (c) EMPTY-REPORT COVERAGE — an all-pure dep's EMPTY report is a purity CLAIM: the call reads pure
#     and the coverage ledger must NOT name the covered package (§2 rule 3).
# candor-swift joined the consumers 2026-07-09 (Deps.swift: pkg#leaf/pkg#tail2 index, import-gated,
# ambiguous-drops; stale → `dep-stale:<pkg>` Unknown) — its row is REQUIRED whenever the engine works.
# ====================================================================================================
echo
echo "[14] CHAINING differential  (SPEC §2 CANDOR_DEPS — join-inherit / stale-downgrade / empty-report coverage)"
CHW="$W/chain"
mkdir -p "$CHW/java/dep/com/dep" "$CHW/java/app/org/app" "$CHW/rust/dep/src" "$CHW/rust/app/src"
cat > "$CHW/java/dep/com/dep/D.java" <<'EOF'
package com.dep;
public class D {
    public static void hit() throws Exception { new java.net.URL("http://rates.internal:7070/x").openConnection(); }
}
EOF
cat > "$CHW/java/app/org/app/A.java" <<'EOF'
package org.app;
public class A {
    public static void go() throws Exception { com.dep.D.hit(); }
}
EOF
javac -d "$CHW/java/depcls" "$CHW/java/dep/com/dep/D.java" 2>/dev/null || { echo "FAIL: javac on chain/dep"; exit 2; }
javac -cp "$CHW/java/depcls" -d "$CHW/java/appcls" "$CHW/java/app/org/app/A.java" 2>/dev/null || { echo "FAIL: javac on chain/app"; exit 2; }
java -jar "$JAR" "$CHW/java/depcls" --json "$CHW/jdep.json" >/dev/null 2>&1 || { echo "FAIL: candor-java errored on the chain dep"; exit 2; }
printf '[package]\nname = "depc"\nversion = "0.0.0"\nedition = "2021"\n' > "$CHW/rust/dep/Cargo.toml"
printf 'pub fn hit() { let _ = std::net::TcpStream::connect("rates.internal:7070"); }\n' > "$CHW/rust/dep/src/lib.rs"
printf '[package]\nname = "appc"\nversion = "0.0.0"\nedition = "2021"\n\n[dependencies]\ndepc = "1.0"\n' > "$CHW/rust/app/Cargo.toml"
printf 'pub fn go() { depc::hit(); }\n' > "$CHW/rust/app/src/lib.rs"
"$SCAN" "$CHW/rust/dep" >/dev/null 2>&1 || { echo "FAIL: candor-scan errored on the chain dep"; exit 2; }
RCH_DEP="$(ls "$CHW"/rust/dep/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)"
if [ -n "$TS_OK" ]; then
  mkdir -p "$CHW/ts/dep" "$CHW/ts/app/node_modules/dep-pkg"
  printf '{"name":"dep-pkg","version":"0.0.0","main":"index.js","types":"index.d.ts"}\n' > "$CHW/ts/dep/package.json"
  printf 'import * as https from "node:https";\nexport function hit() { return https.get("http://rates.internal:7070/x"); }\n' > "$CHW/ts/dep/index.ts"
  node "$TS_DIR/scan.mjs" "$CHW/ts/dep" --out "$CHW/tdep" >/dev/null 2>&1
  [ -s "$CHW/tdep.json" ] || { echo "FAIL: candor-ts errored on the chain dep"; exit 2; }
  printf '{"name":"dep-pkg","version":"0.0.0","main":"index.js","types":"index.d.ts"}\n' > "$CHW/ts/app/node_modules/dep-pkg/package.json"
  printf 'export declare function hit(): any;\n' > "$CHW/ts/app/node_modules/dep-pkg/index.d.ts"
  printf 'module.exports.hit = () => {};\n' > "$CHW/ts/app/node_modules/dep-pkg/index.js"
  printf 'import { hit } from "dep-pkg";\nexport function go() { return hit(); }\n' > "$CHW/ts/app/cases.ts"
fi
SCH_DEP=""
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  mkdir -p "$CHW/swift/DepKit" "$CHW/swift/app"
  printf 'import Foundation\nimport Network\n\npublic func hit() { _ = NWConnection(host: "rates.internal", port: 7070, using: .tcp) }\n' > "$CHW/swift/DepKit/dep.swift"
  "$SW_BIN" "$CHW/swift/DepKit" --out "$CHW/sdep" >/dev/null 2>&1
  SCH_DEP="$CHW/sdep.DepKit.Swift.json"
  [ -s "$SCH_DEP" ] || { echo "FAIL: candor-swift errored on the chain dep"; exit 2; }
  printf 'import DepKit\n\nfunc go() { DepKit.hit() }\n' > "$CHW/swift/app/a.swift"
fi
# doctor each dep report: a STALE copy (foreign producing version) and an EMPTY copy (purity claim)
python3 - "$CHW/jdep.json" "$RCH_DEP" "${TS_OK:+$CHW/tdep.json}" "$SCH_DEP" <<'PY' || { echo "FAIL: could not doctor the chain dep reports"; exit 2; }
import json, sys
for src in [a for a in sys.argv[1:] if a]:
    d = json.load(open(src))
    s = json.loads(json.dumps(d)); s["candor"]["version"] = "candor-doctored-0.0.0"
    json.dump(s, open(src.replace(".json", "") + "_stale.json", "w"))
    e = json.loads(json.dumps(d)); e["functions"] = []
    json.dump(e, open(src.replace(".json", "") + "_empty.json", "w"))
PY
chain_scan() { # $1 java-dep  $2 out-stem  $3 rust-dep  $4 ts-dep  $5 swift-dep
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_DEPS="$1" java -jar "$JAR" "$CHW/java/appcls" --json "$W/ch_j_$2.json" > "$W/ch_j_$2.err" 2>&1 \
    || { echo "FAIL: candor-java errored on the chained app ($2)"; exit 2; }
  rm -rf "$CHW/rust/app/.candor"
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_DEPS="$3" "$SCAN" "$CHW/rust/app" > "$W/ch_r_$2.err" 2>&1 \
    || { echo "FAIL: candor-scan errored on the chained app ($2)"; exit 2; }
  cp "$(ls "$CHW"/rust/app/.candor/report.*.scan.json | grep -v callgraph | head -1)" "$W/ch_r_$2.json"
  if [ -n "$TS_OK" ]; then
    env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_DEPS="$4" node "$TS_DIR/scan.mjs" "$CHW/ts/app/cases.ts" "$W/ch_t_$2" > "$W/ch_t_$2.err" 2>&1 \
      || { echo "FAIL: candor-ts errored on the chained app ($2)"; exit 2; }
  fi
  if [ -n "$SCH_DEP" ]; then
    env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_DEPS="$5" "$SW_BIN" "$CHW/swift/app" --out "$W/ch_s_raw_$2" > "$W/ch_s_$2.err" 2>&1 \
      || { echo "FAIL: candor-swift errored on the chained app ($2)"; exit 2; }
    cp "$(ls "$W"/ch_s_raw_$2.*.Swift.json | grep -v callgraph | grep -v hierarchy | head -1)" "$W/ch_s_$2.json"
  fi
}
JD="$CHW/jdep"; RD="${RCH_DEP%.json}"; TD="$CHW/tdep"; SD="${SCH_DEP%.json}"
chain_scan "$JD.json"        fresh "$RD.json"        "$TD.json"        "$SD.json"
chain_scan "${JD}_stale.json" stale "${RD}_stale.json" "${TD}_stale.json" "${SD}_stale.json"
chain_scan "${JD}_empty.json" empty "${RD}_empty.json" "${TD}_empty.json" "${SD}_empty.json"
python3 - "$W" "$TS_OK" "$SCH_DEP" <<'PY' || rc=1
import json, sys
W, ts, sw = sys.argv[1], sys.argv[2], len(sys.argv) > 3 and sys.argv[3]
engines = [("candor-java", "j", "com.dep"), ("candor-scan", "r", "depc")] \
          + ([("candor-ts", "t", "dep-pkg")] if ts else []) \
          + ([("candor-swift", "s", "DepKit")] if sw else [])
ok = True
def fns(e, stem):
    d = json.load(open(f"{W}/ch_{e}_{stem}.json"))
    return {f["fn"].split(".")[-1].split("::")[-1]: f for f in d["functions"]}
for name, e, pkg in engines:
    fresh, stale, empty = fns(e, "fresh"), fns(e, "stale"), fns(e, "empty")
    err_empty = open(f"{W}/ch_{e}_empty.err").read()
    join = "go" in fresh and set(fresh["go"].get("inferred", [])) == {"Net"} \
           and "rates.internal:7070" in fresh["go"].get("hosts", [])
    down = "go" in stale and "Unknown" in stale["go"].get("inferred", []) \
           and "Net" not in stale["go"].get("inferred", [])
    pure = all("Net" not in f.get("inferred", []) and "Unknown" not in f.get("inferred", []) for f in empty.values())
    covered = not ("classifier doesn't cover" in err_empty and pkg in err_empty)
    good = join and down and pure and covered
    detail = "".join([
        "" if join else " (join: app fn must inherit exactly {Net} + the host literal)",
        "" if down else " (stale: a doctored producing version must downgrade to Unknown, not keep Net)",
        "" if pure else " (empty: an all-pure dep report is a purity claim — the call must read pure)",
        "" if covered else f" (empty: the coverage ledger must NOT name {pkg} — a loaded report COVERS its package, §2 rule 3)"])
    print(f"  {name:12s} -> {'MATCH' if good else 'DIVERGE'}{detail}")
    ok = ok and good
print("  -> " + ("MATCH — chaining joins, distrusts stale producers, and honors empty-report coverage in every consuming engine"
                 if ok else "DIVERGE — see rows"))
sys.exit(0 if ok else 1)
PY

# ====================================================================================================
# PART 15 — the AS-EFF-005 BASELINE GUARD, four-way (SPEC §7 item 5 + the §2.1 stale-baseline posture).   [TIER 1]
# All four engines carry the scan-time guard as of 2026-07-10 (java since 0.8.x; scan/ts/swift landed
# in the doc-review wave — the item-5 MUST is now satisfied, not narrowed). Pinned per engine:
#   gain      — an existing fn gaining an effect vs a same-build baseline → [AS-EFF-005] + exit 1
#   clean     — no gain vs the same baseline → exit 0
#   absent    — a baseline path that names no file → note, guard inactive, exit 0
#   doctored  — a foreign producing version → exit 2 WITHOUT evaluating (no [AS-EFF-005] lines)
#   empty     — a configured-but-EMPTY value → exit 2 (a declared ratchet naming no file is a broken
#               gate, not an inactive one — the family ruling; java/scan/ts/swift all aligned)
# Plus (b): comparison QUERIES disclose the mismatch (provenance fields + warning) and still answer.
# ====================================================================================================
echo
echo "[15] BASELINE GUARD four-way + stale posture  (SPEC §7 item 5, §2.1 — gain/clean/absent/doctored/empty)"
SBW="$W/sb"; mkdir -p "$SBW/jb/q" "$SBW/ja/q" "$SBW/rb/src" "$SBW/ra/src" "$SBW/tb" "$SBW/ta" "$SBW/swb/gd" "$SBW/swa/gd"
printf 'package q;\npublic class G { static void entry() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); } }\n' > "$SBW/jb/q/G.java"
printf 'package q;\npublic class G { static void entry() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); new java.net.Socket("h", 80); } }\n' > "$SBW/ja/q/G.java"
javac -d "$SBW/jbc" "$SBW/jb/q/G.java" 2>/dev/null && javac -d "$SBW/jac" "$SBW/ja/q/G.java" 2>/dev/null || { echo "FAIL: javac on the guard fixtures"; exit 2; }
printf '[package]\nname = "gd"\nversion = "0.0.0"\nedition = "2021"\n' | tee "$SBW/rb/Cargo.toml" > "$SBW/ra/Cargo.toml"
printf 'pub fn entry() { let _ = std::fs::read("/x"); }\n' > "$SBW/rb/src/lib.rs"
printf 'pub fn entry() { let _ = std::fs::read("/x"); let _ = std::net::TcpStream::connect("h:80"); }\n' > "$SBW/ra/src/lib.rs"
printf 'import * as fsm from "node:fs";\nexport function entry(): string { return fsm.readFileSync("/x", "utf8"); }\n' > "$SBW/tb/gd.ts"
printf 'import * as fsm from "node:fs";\nimport * as netm from "node:net";\nexport function entry(): string { netm.connect(80, "h"); return fsm.readFileSync("/x", "utf8"); }\n' > "$SBW/ta/gd.ts"
printf 'import Foundation\nfunc entry() { _ = FileManager.default.contents(atPath: "/x") }\n' > "$SBW/swb/gd/a.swift"
printf 'import Foundation\nimport Network\nfunc entry() { _ = FileManager.default.contents(atPath: "/x"); _ = NWConnection(host: "h", port: 80, using: .tcp) }\n' > "$SBW/swa/gd/a.swift"
# baselines from the BEFORE fixtures, generated in-run by the same binaries (same-build by construction)
java -jar "$JAR" "$SBW/jbc" --json "$SBW/jbase.json" >/dev/null 2>&1 || { echo "FAIL: java guard-baseline scan"; exit 2; }
"$SCAN" "$SBW/rb" >/dev/null 2>&1 || { echo "FAIL: scan guard-baseline scan"; exit 2; }
# copy the baseline OUT of the fixture's .candor — the clean-row re-scan would rewrite it in place
cp "$(ls "$SBW"/rb/.candor/report.*.scan.json | grep -v callgraph | head -1)" "$SBW/rbase.json"
RBASE="$SBW/rbase.json"
[ -n "$TS_OK" ] && { node "$TS_DIR/scan.mjs" "$SBW/tb/gd.ts" "$SBW/tbase" >/dev/null 2>&1; [ -s "$SBW/tbase.json" ] || { echo "FAIL: ts guard-baseline scan"; exit 2; }; }
SWBASE=""
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  "$SW_BIN" "$SBW/swb/gd" --out "$SBW/sbase" >/dev/null 2>&1
  SWBASE="$SBW/sbase.gd.Swift.json"; [ -s "$SWBASE" ] || { echo "FAIL: swift guard-baseline scan"; exit 2; }
fi
python3 - "$SBW/jbase.json" "$RBASE" "${TS_OK:+$SBW/tbase.json}" "$SWBASE" <<'PY' || { echo "FAIL: could not doctor the guard baselines"; exit 2; }
import json, sys
for src in [a for a in sys.argv[1:] if a]:
    d = json.load(open(src))
    d["candor"]["version"] = "candor-doctored-0.0.0"
    json.dump(d, open(src.replace(".json", "") + "_doct.json", "w"))
PY
SB_OK=0
sbrow() { # $1 label  $2 base  $3 doctored  — then '--' AFTER-cmd... '--' BEFORE-cmd...
  local label=$1 base=$2 doct=$3; shift 3
  local after=() before=() cur=after
  shift  # leading --
  while [ $# -gt 0 ]; do
    if [ "$1" = "--" ]; then cur=before; shift; continue; fi
    if [ "$cur" = after ]; then after+=("$1"); else before+=("$1"); fi
    shift
  done
  local g c a d e out
  out=$(env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${after[@]}" 2>&1); g=$?
  local gain_seen=no; printf '%s' "$out" | grep -q "\[AS-EFF-005\]" && gain_seen=yes
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${before[@]}" >/dev/null 2>&1; c=$?
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$SBW/nope.json" "${after[@]}" >/dev/null 2>&1; a=$?
  out=$(env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$doct" "${after[@]}" 2>&1); d=$?
  local doct_eval=no; printf '%s' "$out" | grep -q "\[AS-EFF-005\]" && doct_eval=yes
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE= "${after[@]}" >/dev/null 2>&1; e=$?
  echo "  $label gain=$g(seen=$gain_seen) clean=$c absent=$a doctored=$d(eval=$doct_eval) empty=$e"
  [ "$g" = 1 ] && [ "$gain_seen" = yes ] && [ "$c" = 0 ] && [ "$a" = 0 ] \
    && [ "$d" = 2 ] && [ "$doct_eval" = no ] && [ "$e" = 2 ] && return 0
  echo "     FAIL $label: expected gain=1+[AS-EFF-005] clean=0 absent=0 doctored=2-no-eval empty=2"; return 1
}
sbrow "candor-java " "$SBW/jbase.json" "${SBW}/jbase_doct.json" \
  -- java -jar "$JAR" "$SBW/jac" -- java -jar "$JAR" "$SBW/jbc" || SB_OK=1
sbrow "candor-scan " "$RBASE" "${RBASE%.json}_doct.json" \
  -- "$SCAN" "$SBW/ra" -- "$SCAN" "$SBW/rb" || SB_OK=1
[ -n "$TS_OK" ] && { sbrow "candor-ts   " "$SBW/tbase.json" "$SBW/tbase_doct.json" \
  -- node "$TS_DIR/scan.mjs" "$SBW/ta/gd.ts" "$SBW/t_o1" -- node "$TS_DIR/scan.mjs" "$SBW/tb/gd.ts" "$SBW/t_o2" || SB_OK=1; }
[ -n "$SWBASE" ] && { sbrow "candor-swift" "$SWBASE" "${SWBASE%.json}_doct.json" \
  -- "$SW_BIN" "$SBW/swa/gd" --out "$SBW/s_o1" -- "$SW_BIN" "$SBW/swb/gd" --out "$SBW/s_o2" || SB_OK=1; }
# doctor a chain-fixture copy for the QUERY half below (diff must disclose, not refuse)
python3 - "$W/ch_j_fresh.json" "$W/sb_java_stale.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["candor"]["version"] = "candor-doctored-0.0.0"
json.dump(d, open(sys.argv[2], "w"))
PY
java -jar "$JAR" diff "$W/ch_j_fresh.json" "$W/sb_java_stale.json" --json > "$W/sb_j_diff.json" 2>"$W/sb_j_diff.err"
mkdir -p "$W/sb_r_base"
cp "$CHW"/rust/app/.candor/report.*.json "$W/sb_r_base/" 2>/dev/null
python3 - "$W/sb_r_base" <<'PY'
import glob, json, sys
for p in glob.glob(sys.argv[1] + "/report.*.scan.json"):
    d = json.load(open(p)); d["candor"]["version"] = "candor-doctored-0.0.0"; json.dump(d, open(p, "w"))
PY
"$QUERY" diff "$CHW/rust/app/.candor/report" "$W/sb_r_base/report" 1 candor-doctored-0.0.0 live > "$W/sb_r_diff.json" 2>/dev/null
if [ -n "$TS_OK" ]; then
  # the baseline must carry a FOREIGN producing version (ch_t_stale was scanned by the live engine,
  # so its own header matches — doctor a copy instead, the same shape the guard half uses)
  python3 - "$W/ch_t_fresh.json" "$W/sb_t_base.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["candor"]["version"] = "candor-doctored-0.0.0"
json.dump(d, open(sys.argv[2], "w"))
PY
  node "$TS_DIR/query.mjs" diff "$W/ch_t_fresh" "$W/sb_t_base" > "$W/sb_t_diff.json" 2>"$W/sb_t_diff.err"
fi
python3 - "$W" "$TS_OK" <<'PY' || SB_OK=1
import json, sys
W, ts = sys.argv[1], sys.argv[2]
ok = True
def probe(name, path, errpath=None, want_warn=False):
    global ok
    try:
        d = json.load(open(path))
    except Exception:
        print(f"  {name:12s} diff -> DIVERGE (no parseable answer — a version mismatch must disclose, not refuse)")
        ok = False; return
    fields = {"baseline_version", "engine_version"} <= set(d) and "changes" in d
    warn = (not want_warn) or ("baseline" in open(errpath).read())
    print(f"  {name:12s} diff -> {'MATCH' if fields and warn else 'DIVERGE'}"
          + ("" if fields else " (missing baseline_version/engine_version provenance fields)")
          + ("" if warn else " (missing the stderr mismatch warning)"))
    ok = ok and fields and warn
probe("candor-java", f"{W}/sb_j_diff.json", f"{W}/sb_j_diff.err", want_warn=True)
probe("candor-query", f"{W}/sb_r_diff.json")
if ts:
    probe("candor-ts", f"{W}/sb_t_diff.json", f"{W}/sb_t_diff.err", want_warn=True)
sys.exit(0 if ok else 1)
PY
if [ "$SB_OK" = 0 ]; then
  echo "  -> MATCH — the guard refuses a stale baseline without evaluating; comparison queries disclose and answer"
else
  echo "  -> DIVERGE — see FAIL rows"; rc=1
fi

# ====================================================================================================
# PART 15b — ⟨0.16⟩ the CALLGRAPH-AWARE baseline guard (SPEC §7 item 5, the ⟨0.16⟩ paragraph).  [TIER 1]
# PART 15 pins the guard on an ALREADY-effectful fn WIDENING. This pins the sharpest supply-chain shape:
# a formerly-PURE fn turning effectful. Reports omit pure fns (§2.2), so pre-0.16 such a fn read as
# exempt "new code" and ESCAPED. The fix keys existence on the baseline CALLGRAPH sidecar (which lists
# pure leaves), exactly as `gains` `origin` (§3.1 ⟨0.12⟩) does. Per engine, three sub-cases:
#   present  — sidecar beside the baseline, a baseline-pure fn now effectful → [AS-EFF-005] + exit 1
#   absent   — sidecar removed → degrade to report-only existence (the pure fn reads as new) → exit 0
#   corrupt  — sidecar present but unparseable → fail closed (exit 2), like a corrupt baseline; a broken
#              sidecar must not silently narrow the guard back to report-only
# Fixtures: a pure `calc` (omitted from the report, a callgraph node) + an effectful `keep` that calls
# it; the AFTER fixture makes `calc` do I/O. Baselines are scanned in-run (same-build by construction),
# in the sidecar-writing form (java --json / scan --out / ts prefix / swift --out all emit the sibling).
# ====================================================================================================
echo
echo "[15b] CALLGRAPH-AWARE guard four-way  (SPEC §7 item 5 ⟨0.16⟩ — pure→effectful: present/absent/corrupt)"
PEW="$W/pe"; mkdir -p "$PEW/jb/q" "$PEW/ja/q" "$PEW/rb/src" "$PEW/ra/src" "$PEW/tb" "$PEW/ta" "$PEW/swb/pe" "$PEW/swa/pe"
# java: pure calc + effectful keep; AFTER makes calc read a file
printf 'package q;\npublic class P {\n static int calc(String s){ return s.length(); }\n static void keep() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); calc("z"); }\n}\n' > "$PEW/jb/q/P.java"
printf 'package q;\npublic class P {\n static int calc(String s) throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/y")); return s.length(); }\n static void keep() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); calc("z"); }\n}\n' > "$PEW/ja/q/P.java"
javac -d "$PEW/jbc" "$PEW/jb/q/P.java" 2>/dev/null && javac -d "$PEW/jac" "$PEW/ja/q/P.java" 2>/dev/null || { echo "FAIL: javac on the ⟨0.16⟩ guard fixtures"; exit 2; }
# rust: same shape, one crate name so fn keys match across before/after
printf '[package]\nname = "pe"\nversion = "0.0.0"\nedition = "2021"\n' | tee "$PEW/rb/Cargo.toml" > "$PEW/ra/Cargo.toml"
printf 'pub fn calc(s: &str) -> usize { s.len() }\npub fn keep() { let _ = std::fs::read("/x"); let _ = calc("z"); }\n' > "$PEW/rb/src/lib.rs"
printf 'pub fn calc(s: &str) -> usize { let _ = std::fs::read("/y"); s.len() }\npub fn keep() { let _ = std::fs::read("/x"); let _ = calc("z"); }\n' > "$PEW/ra/src/lib.rs"
# ts: same basename in sibling dirs so module-qualified fn names match
printf 'import * as fsm from "node:fs";\nexport function calc(s: string): number { return s.length; }\nexport function keep(): void { fsm.readFileSync("/x"); calc("z"); }\n' > "$PEW/tb/pe.ts"
printf 'import * as fsm from "node:fs";\nexport function calc(s: string): number { fsm.readFileSync("/y"); return s.length; }\nexport function keep(): void { fsm.readFileSync("/x"); calc("z"); }\n' > "$PEW/ta/pe.ts"
# swift: same leaf dir name "pe" so the package segment matches across before/after
printf 'import Foundation\nfunc calc(_ s: String) -> Int { s.count }\nfunc keep() { _ = FileManager.default.contents(atPath: "/x"); _ = calc("z") }\n' > "$PEW/swb/pe/a.swift"
printf 'import Foundation\nfunc calc(_ s: String) -> Int { _ = FileManager.default.contents(atPath: "/y"); return s.count }\nfunc keep() { _ = FileManager.default.contents(atPath: "/x"); _ = calc("z") }\n' > "$PEW/swa/pe/a.swift"
# scan the baselines (sidecar-writing form). same binaries → same-build by construction.
java -jar "$JAR" "$PEW/jbc" --json "$PEW/jbase.json" >/dev/null 2>&1 || { echo "FAIL: java ⟨0.16⟩ baseline scan"; exit 2; }
"$SCAN" "$PEW/rb" --out "$PEW/rbase" >/dev/null 2>&1 || { echo "FAIL: scan ⟨0.16⟩ baseline scan"; exit 2; }
[ -f "$PEW/rbase.pe.scan.callgraph.json" ] || { echo "FAIL: scan ⟨0.16⟩ baseline wrote no callgraph sidecar"; exit 2; }
[ -n "$TS_OK" ] && { node "$TS_DIR/scan.mjs" "$PEW/tb/pe.ts" "$PEW/tbase" >/dev/null 2>&1; [ -s "$PEW/tbase.callgraph.json" ] || { echo "FAIL: ts ⟨0.16⟩ baseline sidecar"; exit 2; }; }
PE_SWBASE=""
if [ -n "$SWBASE" ]; then
  "$SW_BIN" "$PEW/swb/pe" --out "$PEW/sbase" >/dev/null 2>&1
  PE_SWBASE="$PEW/sbase.pe.Swift.json"; [ -s "${PE_SWBASE%.json}.callgraph.json" ] || { echo "FAIL: swift ⟨0.16⟩ baseline sidecar"; exit 2; }
fi
PE_OK=0
perow() { # $1 label  $2 basereport  --  after-scan-cmd...
  local label=$1 base=$2; shift 2; shift  # drop the leading --
  local after=("$@")
  local sidecar="${base%.json}.callgraph.json"
  [ -f "$sidecar" ] || { echo "     FAIL $label: no baseline sidecar at $sidecar"; return 1; }
  local out p a c seen=no
  # present — the pure→effectful transition must be a GAIN
  out=$(env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${after[@]}" 2>&1); p=$?
  printf '%s' "$out" | grep -q "\[AS-EFF-005\]" && seen=yes
  # absent — degrade to report-only (the pure fn reads as new), exit 0
  mv "$sidecar" "$sidecar.bak"
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${after[@]}" >/dev/null 2>&1; a=$?
  mv "$sidecar.bak" "$sidecar"
  # corrupt — fail closed (exit 2)
  cp "$sidecar" "$sidecar.keep"; printf '{' > "$sidecar"
  env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${after[@]}" >/dev/null 2>&1; c=$?
  mv "$sidecar.keep" "$sidecar"
  echo "  $label present=$p(seen=$seen) absent=$a corrupt=$c"
  [ "$p" = 1 ] && [ "$seen" = yes ] && [ "$a" = 0 ] && [ "$c" = 2 ] && return 0
  echo "     FAIL $label: expected present=1+[AS-EFF-005] absent=0 corrupt=2"; return 1
}
perow "candor-java " "$PEW/jbase.json" -- java -jar "$JAR" "$PEW/jac" || PE_OK=1
perow "candor-scan " "$PEW/rbase.pe.scan.json" -- "$SCAN" "$PEW/ra" || PE_OK=1
[ -n "$TS_OK" ] && { perow "candor-ts   " "$PEW/tbase.json" -- node "$TS_DIR/scan.mjs" "$PEW/ta/pe.ts" "$PEW/t_pe_out" || PE_OK=1; }
[ -n "$PE_SWBASE" ] && { perow "candor-swift" "$PE_SWBASE" -- "$SW_BIN" "$PEW/swa/pe" --out "$PEW/s_pe_out" || PE_OK=1; }
if [ "$PE_OK" = 0 ]; then
  echo "  -> MATCH — every engine keys existence on the baseline callgraph: pure→effectful is caught, absent degrades, corrupt fails closed"
else
  echo "  -> DIVERGE — see FAIL rows"; rc=1
fi

# ⟨0.16⟩ the ratchet fires only on a REAL boundary effect; a pure fn that gains ONLY `Unknown` (an
# unresolved call — the §4 trust marker, not an effect) is DISCLOSED as advisory, exit 0. On real version
# bumps an Unknown-only gain is dominated by resolution noise (SOUNDNESS-LOG 2026-07-16), so failing on it
# would break CI on innocuous updates. Per engine: baseline-pure `fmt` (a callgraph node) gains an
# engine-idiomatic UNRESOLVED call (fn-pointer / reflection / dynamic value / opaque closure) — SAME fn
# identity — and must exit 0, print the advisory note, and NOT [AS-EFF-005].
echo "[15c] Unknown-only gain is ADVISORY four-way  (SPEC §7 item 5 ⟨0.16⟩ — pure→Unknown: exit 0 + note, no fail)"
PUW="$W/peu"; mkdir -p "$PUW/jbu/q" "$PUW/jau/q" "$PUW/rbu/src" "$PUW/rau/src" "$PUW/tbu" "$PUW/tau" "$PUW/swbu/pe" "$PUW/swau/pe"
# java: fmt pure → fmt does reflection (Unknown), same descriptor fmt(String)
printf 'package q;\npublic class P {\n static int fmt(String s){ return s.length(); }\n static void keep(){ fmt("z"); }\n}\n' > "$PUW/jbu/q/P.java"
printf 'package q;\npublic class P {\n static int fmt(String s) throws Exception { return (int) String.class.getMethod("length").invoke(s); }\n static void keep(){ try { fmt("z"); } catch (Exception e) {} }\n}\n' > "$PUW/jau/q/P.java"
javac -d "$PUW/jbc" "$PUW/jbu/q/P.java" 2>/dev/null && javac -d "$PUW/jac" "$PUW/jau/q/P.java" 2>/dev/null || { echo "FAIL: javac ⟨0.16⟩ Unknown fixtures"; exit 2; }
# rust: fmt pure → fmt calls a fn pointer (Unknown), same name fmt
printf '[package]\nname = "pe"\nversion = "0.0.0"\nedition = "2021"\n' | tee "$PUW/rbu/Cargo.toml" > "$PUW/rau/Cargo.toml"
printf 'pub fn helper()->usize{ 0 }\npub fn fmt(s:&str)->usize{ s.len() }\n' > "$PUW/rbu/src/lib.rs"
printf 'pub fn helper()->usize{ 0 }\npub fn fmt(s:&str)->usize{ let g: fn()->usize = helper; g() }\n' > "$PUW/rau/src/lib.rs"
# ts: fmt pure → fmt invokes a Function-typed value (Unknown), same name fmt
printf 'export function fmt(s: string): number { return s.length; }\nexport function keep(): number { return fmt("z"); }\n' > "$PUW/tbu/pe.ts"
printf 'export function fmt(s: string): number { const f: Function = (globalThis as any).x; return f(); }\nexport function keep(): number { return fmt("z"); }\n' > "$PUW/tau/pe.ts"
# swift: fmt pure → fmt gains a CLOSURE-PARAM call (Unknown). candor-swift keys on the base name `fmt`,
# so fmt(_:) and fmt(_:_:) are the same node; the invoked closure param is an unresolved call.
printf 'import Foundation\nfunc fmt(_ s: String) -> Int { s.count }\nfunc anchor() { _ = FileManager.default.contents(atPath: "/x") }\nanchor()\n' > "$PUW/swbu/pe/a.swift"
printf 'import Foundation\nfunc fmt(_ s: String, _ opaque: () -> Void) -> Int { opaque(); return s.count }\nfunc anchor() { _ = FileManager.default.contents(atPath: "/x") }\nanchor()\n' > "$PUW/swau/pe/a.swift"
# baselines (sidecar-writing form)
java -jar "$JAR" "$PUW/jbc" --json "$PUW/jbase.json" >/dev/null 2>&1 || { echo "FAIL: java ⟨0.16⟩ Unknown baseline"; exit 2; }
"$SCAN" "$PUW/rbu" --out "$PUW/rbase" >/dev/null 2>&1 || { echo "FAIL: scan ⟨0.16⟩ Unknown baseline"; exit 2; }
# ⟨0.24⟩ THESE TWO USED TO RUN UNCHECKED AND THE ROW BELOW SKIPPED ON A MISSING SIDECAR, so a ts or swift
# leg that never ran printed MATCH. Sibling PART 15b hard-fails this exact hazard (see its `[ -s … ] || …
# exit 2`); 15c dropped the guard. A leg that cannot run is a HARNESS fault and must be loud — silently
# reporting agreement among the engines that happened to work is how this suite lies about its coverage.
[ -n "$TS_OK" ] && { node "$TS_DIR/scan.mjs" "$PUW/tbu/pe.ts" "$PUW/tbase" >/dev/null 2>&1 \
  || { echo "FAIL: candor-ts ⟨0.16⟩ Unknown baseline scan errored — 15c's ts leg cannot run"; exit 2; }; }
PU_SWBASE=""
[ -n "$SWBASE" ] && { "$SW_BIN" "$PUW/swbu/pe" --out "$PUW/sbase" >/dev/null 2>&1 \
  || { echo "FAIL: candor-swift ⟨0.16⟩ Unknown baseline scan errored — 15c's swift leg cannot run"; exit 2; }; PU_SWBASE="$PUW/sbase.pe.Swift.json"; }
PU_OK=0
peurow() { # $1 label  $2 basereport  --  after-scan-cmd...
  local label=$1 base=$2; shift 2; shift
  local after=("$@"); local sidecar="${base%.json}.callgraph.json"
  [ -f "$sidecar" ] || { echo "     FAIL $label: no baseline sidecar"; return 1; }
  local out rc noteseen=no fireseen=no
  out=$(env -u CANDOR_POLICY -u CANDOR_CONFIG CANDOR_BASELINE="$base" "${after[@]}" 2>&1); rc=$?
  printf '%s' "$out" | grep -q "\[AS-EFF-005\]" && fireseen=yes
  printf '%s' "$out" | grep -qi "Unknown" && printf '%s' "$out" | grep -qi "advisory" && noteseen=yes
  echo "  $label exit=$rc fired=$fireseen advisory-note=$noteseen"
  [ "$rc" = 0 ] && [ "$fireseen" = no ] && [ "$noteseen" = yes ] && return 0
  echo "     FAIL $label: expected exit 0, NO [AS-EFF-005], an Unknown advisory note"; return 1
}
peurow "candor-java " "$PUW/jbase.json" -- java -jar "$JAR" "$PUW/jac" || PU_OK=1
peurow "candor-scan " "$PUW/rbase.pe.scan.json" -- "$SCAN" "$PUW/rau" || PU_OK=1
# An ABSENT sidecar is now a FAILURE, not a skip: the engine is present (guarded above), so the sidecar
# missing means the baseline scan did not produce what this row reads — a fault, not a capability gap.
[ -n "$TS_OK" ] && { [ -f "$PUW/tbase.callgraph.json" ] \
  || { echo "  FAIL: candor-ts is present but its ⟨0.16⟩ baseline callgraph sidecar is missing — this leg would have SKIPPED and the row would still have printed MATCH"; PU_OK=1; }; }
[ -n "$TS_OK" ] && [ -f "$PUW/tbase.callgraph.json" ] && { peurow "candor-ts   " "$PUW/tbase.json" -- node "$TS_DIR/scan.mjs" "$PUW/tau/pe.ts" "$PUW/tu_out" || PU_OK=1; }
[ -n "$PU_SWBASE" ] && { [ -f "${PU_SWBASE%.json}.callgraph.json" ] \
  || { echo "  FAIL: candor-swift is present but its ⟨0.16⟩ baseline callgraph sidecar is missing — this leg would have SKIPPED and the row would still have printed MATCH"; PU_OK=1; }; }
[ -n "$PU_SWBASE" ] && [ -f "${PU_SWBASE%.json}.callgraph.json" ] && { peurow "candor-swift" "$PU_SWBASE" -- "$SW_BIN" "$PUW/swau/pe" --out "$PUW/su_out" || PU_OK=1; }
if [ "$PU_OK" = 0 ]; then
  echo "  -> MATCH — an Unknown-only gain is advisory (exit 0 + note), never a CI-breaking regression, in every engine"
else
  echo "  -> DIVERGE — see FAIL rows"; rc=1
fi

# ====================================================================================================
# PART 16 — applied `deny Unknown` + `pure`-vs-Unknown + applied `forbid A->B` (AS-EFF-009 at LAYER   [TIER 1]
# granularity, incl. NESTED scopes). Previously only the §6.2 GRAMMAR of these rules was differentialed
# (PART 4 parses them); the applied verdict was pinned for deny/allow only. Per engine:
#   * an idiomatic unresolved call under `deny Unknown` must FAIL (exit 1);
#   * the SAME fixture under a bare `pure` must PASS (exit 0) — Unknown is the §4 trust marker, not an
#     effect (three engines wrongly counted it until 2026-07-09; the deny-alignment round caught it);
#   * a layer-crossing call under `forbid app -> repo` must FAIL and `forbid app -> other` must PASS —
#     at package/module/dir granularity AND at the nested-scope boundary (a JVM nested class `L$app`,
#     a TS namespace), per the §6.2 scope-segment ruling (the boundaries the §3.1 name ladder splits on).
# ====================================================================================================
echo
echo "[16] APPLIED deny-Unknown / pure-vs-Unknown / forbid-layering  (SPEC §6/§6.2 — remaining verdicts agree)"
PW="$W/p16"; mkdir -p "$PW"
printf 'deny Unknown\n' > "$PW/unknown.policy"
printf 'pure\n' > "$PW/pure.policy"
printf 'forbid app -> repo\n' > "$PW/layer.policy"
printf 'forbid app -> other\n' > "$PW/cousin.policy"
# --- unresolved-call fixtures (each language's idiomatic Unknown: fn-value / reflection / closure) ---
mkdir -p "$PW/ur/src" "$PW/uj/q" "$PW/ut" "$PW/us"
printf '[package]\nname = "u"\nversion = "0.0.0"\nedition = "2021"\n' > "$PW/ur/Cargo.toml"
printf 'pub fn entry(f: fn()) { f(); }\n' > "$PW/ur/src/lib.rs"
printf 'package q;\npublic class U { public static void entry() throws Exception { Class.forName(System.getProperty("x")).getMethod("run").invoke(null); } }\n' > "$PW/uj/q/U.java"
printf 'export function entry(f: () => void): void { f(); }\n' > "$PW/ut/a.ts"
printf 'import Foundation\nfunc entry(_ f: () -> Void) { f() }\n' > "$PW/us/a.swift"
# --- layered fixtures (app calls repo; layers = module / package / directory / enum-namespace) ---
mkdir -p "$PW/lr/src" "$PW/lj/q/app" "$PW/lj/q/repo" "$PW/lt/app" "$PW/lt/repo" "$PW/ls"
printf '[package]\nname = "l"\nversion = "0.0.0"\nedition = "2021"\n' > "$PW/lr/Cargo.toml"
cat > "$PW/lr/src/lib.rs" <<'EOF'
pub mod repo { pub fn load() { let _ = std::fs::read("/x"); } }
pub mod app { pub fn entry() { crate::repo::load(); } }
EOF
printf 'package q.repo;\npublic class R { public static void load() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); } }\n' > "$PW/lj/q/repo/R.java"
printf 'package q.app;\npublic class A { public static void entry() throws Exception { q.repo.R.load(); } }\n' > "$PW/lj/q/app/A.java"
printf 'import * as fsm from "node:fs";\nexport function load(): void { fsm.readFileSync("/x"); }\n' > "$PW/lt/repo/index.ts"
printf 'import { load } from "../repo/index.js";\nexport function entry(): void { load(); }\n' > "$PW/lt/app/index.ts"
cat > "$PW/ls/a.swift" <<'EOF'
import Foundation
enum repo { static func load() { _ = FileManager.default.contents(atPath: "/x") } }
enum app { static func entry() { repo.load() } }
EOF
# nested-scope variants (the §6.2 ruling: nested-type/namespace boundaries are scope segments) —
# the exact shapes that diverged before the 2026-07-09 java `$`-boundary and ts namespace-naming fixes.
mkdir -p "$PW/nj/q" "$PW/nt"
cat > "$PW/nj/q/LN.java" <<'EOF'
package q;
public class LN {
    public static class repo { static void load() throws Exception { java.nio.file.Files.readString(java.nio.file.Path.of("/x")); } }
    public static class app { static void entry() throws Exception { repo.load(); } }
}
EOF
cat > "$PW/nt/ns.ts" <<'EOF'
import * as fsm from "node:fs";
export namespace repo { export function load(): string { return fsm.readFileSync("/x", "utf8"); } }
export namespace app { export function entry(): string { return repo.load(); } }
EOF
javac -d "$PW/ujc" "$PW/uj/q/U.java" 2>/dev/null || { echo "FAIL: javac on p16 unknown fixture"; exit 2; }
javac -d "$PW/ljc" "$PW/lj/q/repo/R.java" "$PW/lj/q/app/A.java" 2>/dev/null || { echo "FAIL: javac on p16 layer fixture"; exit 2; }
javac -d "$PW/njc" "$PW/nj/q/LN.java" 2>/dev/null || { echo "FAIL: javac on p16 nested fixture"; exit 2; }
P16_OK=0
vp() { # $1 label $2 expected $3 actual
  if [ "$3" != "$2" ]; then echo "     FAIL $1: exit $3, expected $2"; P16_OK=1; fi
}
# candor-java
env -u CANDOR_CONFIG java -jar "$JAR" "$PW/ujc" --policy "$PW/unknown.policy" >/dev/null 2>&1; JU=$?
env -u CANDOR_CONFIG java -jar "$JAR" "$PW/ujc" --policy "$PW/pure.policy"    >/dev/null 2>&1; JP=$?
env -u CANDOR_CONFIG java -jar "$JAR" "$PW/ljc" --policy "$PW/layer.policy"   >/dev/null 2>&1; JL=$?
env -u CANDOR_CONFIG java -jar "$JAR" "$PW/ljc" --policy "$PW/cousin.policy"  >/dev/null 2>&1; JC=$?
env -u CANDOR_CONFIG java -jar "$JAR" "$PW/njc" --policy "$PW/layer.policy"   >/dev/null 2>&1; JN=$?
echo "  candor-java  deny-Unknown=$JU pure=$JP forbid=$JL forbid-cousin=$JC nested-forbid=$JN"
vp "java deny-Unknown" 1 "$JU"; vp "java pure-on-Unknown" 0 "$JP"; vp "java forbid" 1 "$JL"; vp "java forbid-cousin" 0 "$JC"; vp "java nested-forbid" 1 "$JN"
# candor-scan
env -u CANDOR_CONFIG "$SCAN" "$PW/ur" --policy "$PW/unknown.policy" >/dev/null 2>&1; RU=$?
env -u CANDOR_CONFIG "$SCAN" "$PW/ur" --policy "$PW/pure.policy"    >/dev/null 2>&1; RP=$?
env -u CANDOR_CONFIG "$SCAN" "$PW/lr" --policy "$PW/layer.policy"   >/dev/null 2>&1; RL=$?
env -u CANDOR_CONFIG "$SCAN" "$PW/lr" --policy "$PW/cousin.policy"  >/dev/null 2>&1; RC2=$?
echo "  candor-scan  deny-Unknown=$RU pure=$RP forbid=$RL forbid-cousin=$RC2 (nested = module case)"
vp "scan deny-Unknown" 1 "$RU"; vp "scan pure-on-Unknown" 0 "$RP"; vp "scan forbid" 1 "$RL"; vp "scan forbid-cousin" 0 "$RC2"
if [ -n "$TS_OK" ]; then
  env -u CANDOR_CONFIG node "$TS_DIR/scan.mjs" "$PW/ut/a.ts" "$PW/ut_out" --policy "$PW/unknown.policy" >/dev/null 2>&1; TU=$?
  env -u CANDOR_CONFIG node "$TS_DIR/scan.mjs" "$PW/ut/a.ts" "$PW/ut_out_p" --policy "$PW/pure.policy"  >/dev/null 2>&1; TP=$?
  env -u CANDOR_CONFIG node "$TS_DIR/scan.mjs" "$PW/lt" --out "$PW/lt_out" --policy "$PW/layer.policy"  >/dev/null 2>&1; TL=$?
  env -u CANDOR_CONFIG node "$TS_DIR/scan.mjs" "$PW/lt" --out "$PW/lt_out2" --policy "$PW/cousin.policy" >/dev/null 2>&1; TC=$?
  env -u CANDOR_CONFIG node "$TS_DIR/scan.mjs" "$PW/nt/ns.ts" "$PW/nt_out" --policy "$PW/layer.policy"  >/dev/null 2>&1; TN=$?
  echo "  candor-ts    deny-Unknown=$TU pure=$TP forbid=$TL forbid-cousin=$TC nested-forbid=$TN"
  vp "ts deny-Unknown" 1 "$TU"; vp "ts pure-on-Unknown" 0 "$TP"; vp "ts forbid" 1 "$TL"; vp "ts forbid-cousin" 0 "$TC"; vp "ts nested-forbid" 1 "$TN"
fi
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  env -u CANDOR_CONFIG "$SW_BIN" "$PW/us" --out "$PW/us_out" --policy "$PW/unknown.policy" >/dev/null 2>&1; SU=$?
  env -u CANDOR_CONFIG "$SW_BIN" "$PW/us" --out "$PW/us_out_p" --policy "$PW/pure.policy"  >/dev/null 2>&1; SP=$?
  env -u CANDOR_CONFIG "$SW_BIN" "$PW/ls" --out "$PW/ls_out" --policy "$PW/layer.policy"   >/dev/null 2>&1; SL=$?
  env -u CANDOR_CONFIG "$SW_BIN" "$PW/ls" --out "$PW/ls_out2" --policy "$PW/cousin.policy" >/dev/null 2>&1; SC=$?
  echo "  candor-swift deny-Unknown=$SU pure=$SP forbid=$SL forbid-cousin=$SC (nested = enum-namespace case)"
  vp "swift deny-Unknown" 1 "$SU"; vp "swift pure-on-Unknown" 0 "$SP"; vp "swift forbid" 1 "$SL"; vp "swift forbid-cousin" 0 "$SC"
fi
if [ "$P16_OK" = 0 ]; then
  echo "  -> MATCH — deny-Unknown bites, pure passes the Unknown marker, and forbid bites every layer shape identically"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 17 — query CLI GRAMMAR differential (SPEC §3.3.1): every engine drives a query the SAME way.        [TIER 2]
# §3.1/PART 5 pin the query SHAPES; this pins the INVOCATION around them — the report DISCOVERED from a
# `.candor/` ancestor (or `--report <locator>`: a dir, a prefix, or a `.json` path), `--json` selecting
# JSON, `--policy` a FLAG not a positional — so `candor where Fs` is one command in every language. Also
# proves the pre-0.10 positional forms still resolve as a DEPRECATED alias (a stderr note, identical JSON),
# so the rung stays byte-compatible with 0.9. Comparison is canonical-JSON (content, key-order-insensitive:
# candor-java's Map.of ordering is per-run). Rust+Java always; TS/Swift when present. Swift shares only
# `fix-gate` (no `where`), so it joins the policy-flag leg (+ a discovery check there).
# ====================================================================================================
P17="$W/p17"; mkdir -p "$P17/j/.candor" "$P17/t/.candor"
P17_OK=0
p17fail() { echo "     FAIL $1"; P17_OK=1; }
canoneq() { # $1 label ; $2 fileA ; $3 fileB — content-equal as canonical JSON?
  python3 -c 'import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
sys.exit(0 if json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True) else 1)' "$2" "$3" 2>/dev/null \
    || p17fail "$1"
}

# --- discovery fixtures: a `.candor/report` each engine's discovery can walk UP to from its dir ----------
#   rust already holds $W/rust/.candor/ from PART 1; java/ts scan the SAME Cases fixtures into a fresh one.
java -jar "$JAR" "$W/jout" --json "$P17/j/.candor/report.app.jvm.json" >/dev/null 2>&1 \
  || p17fail "java: could not write the discovery report"
[ -n "$TS_OK" ] && ( cd "$TS_DIR" && node scan.mjs Cases.ts "$P17/t/.candor/report" ) >/dev/null 2>&1

# --- `where Fs` four ways, per single-report engine: discovered ≡ --report(dir) ≡ --report(prefix|path) ≡
#     OLD positional. The canonical forms' stderr MUST be clean; the OLD form MUST emit a deprecation note.
( cd "$W/rust" && "$QUERY" where Fs --json ) > "$P17/r_disc.json" 2>"$P17/r_disc.err"
"$QUERY" where Fs --report "$W/rust"                --json > "$P17/r_dir.json" 2>/dev/null
"$QUERY" where Fs --report "$W/rust/.candor/report" --json > "$P17/r_pfx.json" 2>/dev/null
"$QUERY" where "$W/rust/.candor/report" Fs 1                > "$P17/r_old.json" 2>"$P17/r_old.err"
[ -s "$P17/r_disc.err" ] && p17fail "rust where: a canonical form wrote to stderr"
[ -s "$P17/r_old.err" ]  || p17fail "rust where: the OLD positional form emitted no deprecation note"

( cd "$P17/j" && java -jar "$JAR" where Fs --json ) > "$P17/j_disc.json" 2>"$P17/j_disc.err"
java -jar "$JAR" where Fs --report "$P17/j"                             --json > "$P17/j_dir.json" 2>/dev/null
java -jar "$JAR" where Fs --report "$P17/j/.candor/report.app.jvm.json" --json > "$P17/j_pfx.json" 2>/dev/null
java -jar "$JAR" where "$P17/j/.candor/report.app.jvm.json" Fs          --json > "$P17/j_old.json" 2>"$P17/j_old.err"
[ -s "$P17/j_disc.err" ] && p17fail "java where: a canonical form wrote to stderr"
[ -s "$P17/j_old.err" ]  || p17fail "java where: the OLD positional form emitted no deprecation note"

if [ -n "$TS_OK" ]; then
  ( cd "$P17/t" && node "$TS_DIR/query.mjs" where Fs --json ) > "$P17/t_disc.json" 2>"$P17/t_disc.err"
  node "$TS_DIR/query.mjs" where Fs --report "$P17/t"                --json > "$P17/t_dir.json" 2>/dev/null
  node "$TS_DIR/query.mjs" where Fs --report "$P17/t/.candor/report" --json > "$P17/t_pfx.json" 2>/dev/null
  node "$TS_DIR/query.mjs" where "$P17/t/.candor/report" Fs                 > "$P17/t_old.json" 2>"$P17/t_old.err"
  [ -s "$P17/t_disc.err" ] && p17fail "ts where: a canonical form wrote to stderr"
  [ -s "$P17/t_old.err" ]  || p17fail "ts where: the OLD positional form emitted no deprecation note"
fi

python3 - "$P17" "$TS_OK" <<'PY' || P17_OK=1
import json, os, re, sys
P17, ts = sys.argv[1], bool(sys.argv[2])
canon = lambda p: json.dumps(json.load(open(p)), sort_keys=True)
leaf  = lambda x: re.split(r'[.:$]+', x)[-1]
print("\n[17] QUERY-GRAMMAR differential  (discovery ≡ --report ≡ OLD positional; --json selects; --policy a flag)")
ok = True
for name, pre in [("rust","r"), ("java","j")] + ([("ts","t")] if ts else []):
    try:
        vals = {f: canon(f"{P17}/{pre}_{f}.json") for f in ("disc","dir","pfx","old")}
        d = json.load(open(f"{P17}/{pre}_disc.json"))
        shape = d.get("effect") == "Fs" and isinstance(d.get("directly"), list) and isinstance(d.get("inherited"), list)
    except Exception as e:
        print(f"  {name:5s} where -> DIVERGE (a form produced no/invalid JSON: {e})"); ok = False; continue
    same = len(set(vals.values())) == 1
    print(f"  {name:5s} where -> {'MATCH' if same and shape else 'DIVERGE'}"
          + ("" if same else "  (the four invocations disagree)")
          + ("" if shape else "  (discovered `where Fs` is not the pinned shape — discovery broken)"))
    ok = ok and same and shape
sys.exit(0 if ok else 1)
PY

# --- policy is a FLAG (fix-gate): NEW `--policy <p>` ≡ OLD positional policy; four-way. Scans its OWN fresh
#     fix fixtures — PART 12b strips the callgraph sidecars from its copies (its sidecar-absent test), and a
#     fix-gate needs the sidecar, so we test grammar here on healthy reports. Swift also gets a discovery
#     check (it has no `where`).
fgpair() { # $1 label ; $2 new-json ; $3 old-json ; $4 old-err
  canoneq "$1 fix-gate: --policy(flag) != positional policy" "$2" "$3"
  [ -s "$4" ] || p17fail "$1 fix-gate: the OLD positional form emitted no deprecation note"
}
cp -r "$HERE/fix" "$P17/fx"; FPOL="$P17/fx/policy"
"$SCAN" "$P17/fx/rust" >/dev/null 2>&1 || p17fail "rust: fix fixture scan failed"
javac -d "$P17/fxjc" $(find "$P17/fx/java" -name '*.java') 2>/dev/null \
  && java -jar "$JAR" "$P17/fxjc" --json "$P17/fxjava.json" >/dev/null 2>&1 || p17fail "java: fix fixture scan failed"
"$QUERY" fix-gate --report "$P17/fx/rust/.candor/report" --policy "$FPOL" --json > "$P17/r_fg_n.json" 2>/dev/null
"$QUERY" fix-gate "$P17/fx/rust/.candor/report" "$FPOL" 1                        > "$P17/r_fg_o.json" 2>"$P17/r_fg_o.err"
fgpair rust "$P17/r_fg_n.json" "$P17/r_fg_o.json" "$P17/r_fg_o.err"
java -jar "$JAR" fix-gate --report "$P17/fxjava.json" --policy "$FPOL" --json > "$P17/j_fg_n.json" 2>/dev/null
java -jar "$JAR" fix-gate "$P17/fxjava.json" "$FPOL" --json                    > "$P17/j_fg_o.json" 2>"$P17/j_fg_o.err"
fgpair java "$P17/j_fg_n.json" "$P17/j_fg_o.json" "$P17/j_fg_o.err"
if [ -n "$TS_OK" ]; then
  node "$TS_DIR/scan.mjs" "$P17/fx/ts" "$P17/fxts" >/dev/null 2>&1
  node "$TS_DIR/query.mjs" fix-gate --report "$P17/fxts" --policy "$FPOL" > "$P17/t_fg_n.json" 2>/dev/null
  node "$TS_DIR/query.mjs" fix-gate "$P17/fxts" "$FPOL"                   > "$P17/t_fg_o.json" 2>"$P17/t_fg_o.err"
  fgpair ts "$P17/t_fg_n.json" "$P17/t_fg_o.json" "$P17/t_fg_o.err"
fi
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  env -u CANDOR_CONFIG "$SW_BIN" "$P17/fx/swift" --out "$P17/fxsw" >/dev/null 2>&1
  env -u CANDOR_CONFIG "$SW_BIN" fix-gate --report "$P17/fxsw" --policy "$FPOL" --json > "$P17/s_fg_n.json" 2>/dev/null
  env -u CANDOR_CONFIG "$SW_BIN" fix-gate "$P17/fxsw" "$FPOL"                          > "$P17/s_fg_o.json" 2>"$P17/s_fg_o.err"
  fgpair swift "$P17/s_fg_n.json" "$P17/s_fg_o.json" "$P17/s_fg_o.err"
  mkdir -p "$P17/s/.candor"
  env -u CANDOR_CONFIG "$SW_BIN" "$P17/fx/swift" --out "$P17/s/.candor/report" >/dev/null 2>&1
  ( cd "$P17/s" && env -u CANDOR_CONFIG "$SW_BIN" fix-gate --policy "$FPOL" --json ) > "$P17/s_fg_disc.json" 2>/dev/null
  canoneq "swift fix-gate: discovered != --report" "$P17/s_fg_disc.json" "$P17/s_fg_n.json"
fi

# --- ROBUSTNESS: the §3.3.1 loud-failure + gating rules, pinned four-way (the cardinal-sin fixes) ---------
# (1) No report → LOUD exit 2. A query that cannot resolve its report MUST NOT answer empty at exit 0 (§4).
mkdir -p "$P17/empty"
noreport() { # $1 label ; $2… command — run from an empty dir with discovery env cleared
  ( cd "$P17/empty" && env -u CANDOR_REPORT -u CANDOR_CONFIG "${@:2}" ) >/dev/null 2>&1
  [ "$?" = 2 ] || p17fail "$1: a missing report must exit 2 (loud), not answer empty at exit 0"
}
noreport "rust no-report" "$QUERY" where Fs --json
noreport "java no-report" java -jar "$JAR" where Fs --json
[ -n "$TS_OK" ] && noreport "ts no-report" node "$TS_DIR/query.mjs" where Fs --json
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && noreport "swift no-report" "$SW_BIN" fix-gate --policy "$FPOL" --json

# (1b) BAD TARGET → LOUD exit 2 (corpus-audit #3): a typo'd EFFECT name (`where Network`) or a nonexistent
#      FUNCTION (`callers zzz`) must NOT answer empty at exit 0 — that reads as an authoritative all-clear for
#      a question never posed (§4). Pinned for where/callers (path/impact already gate) across the engines that
#      implement them (swift has neither verb). Uses the discovery reports scanned above; --report avoids the cd.
badtarget() { # $1 label ; $2… command — expect exit 2
  ( "${@:2}" ) >/dev/null 2>&1
  [ "$?" = 2 ] || p17fail "$1: a typo'd effect / nonexistent fn must exit 2 (loud), not answer empty at exit 0"
}
badtarget "rust where <typo effect>"  "$QUERY" where Netwerk --report "$W/rust/.candor/report"
badtarget "rust callers <bad fn>"     "$QUERY" callers zzz_no_such_fn --report "$W/rust/.candor/report"
badtarget "java where <typo effect>"  java -jar "$JAR" where Netwerk --report "$P17/j/.candor/report.app.jvm.json"
badtarget "java callers <bad fn>"     java -jar "$JAR" callers zzz_no_such_fn --report "$P17/j/.candor/report.app.jvm.json"
if [ -n "$TS_OK" ]; then
  badtarget "ts where <typo effect>"  node "$TS_DIR/query.mjs" where Netwerk --report "$P17/t"
  badtarget "ts callers <bad fn>"     node "$TS_DIR/query.mjs" callers zzz_no_such_fn --report "$P17/t"
fi

# (1c) TYPO'd FLAG → LOUD exit 2 (corpus re-audit #2): a `-`-prefixed token that is not a known candor flag is
# NEVER swallowed as a positional — a silent `--polciy` runs the query with NO policy and exits green (a CI
# author who typos --policy ships a gate that never fires; the same silent-guess cardinal sin). AND every
# engine TOLERATES another engine's valid flag: `--text`/`--human` are candor-ts output-mode flags, so a
# prose-default engine (rust/java/swift) must accept them (cross-engine `candor <verb> --text` never errors).
badtarget "rust typo'd flag"  "$QUERY" where Fs --polciy /x --report "$W/rust/.candor/report"
badtarget "java typo'd flag"  java -jar "$JAR" where Fs --polciy /x --report "$P17/j/.candor/report.app.jvm.json"
[ -n "$TS_OK" ] && badtarget "ts typo'd flag" node "$TS_DIR/query.mjs" where Fs --polciy /x --report "$P17/t"
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && badtarget "swift typo'd flag" env -u CANDOR_CONFIG "$SW_BIN" tour --polciy /x --report "$P17/s"
tolerated() { # $1 label ; $2… command — a valid cross-engine flag must be TOLERATED. The command uses a
  # valid report, so tolerance means it runs to a clean exit 0 — NOT merely "exit != 2": a crash (rust panic
  # 101, a JVM exit 1) is also != 2 yet means the flag broke the engine, which "!= 2" would wave through.
  ( "${@:2}" ) >/dev/null 2>&1
  [ "$?" = 0 ] || p17fail "$1: a valid cross-engine output flag (--text) must run clean (exit 0), not error"
}
tolerated "rust --text"  "$QUERY" where Fs --text --report "$W/rust/.candor/report"
tolerated "java --text"  java -jar "$JAR" where Fs --text --report "$P17/j/.candor/report.app.jvm.json"
[ -n "$TS_OK" ] && tolerated "ts --text" node "$TS_DIR/query.mjs" where Fs --text --report "$P17/t"
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && tolerated "swift --text" env -u CANDOR_CONFIG "$SW_BIN" tour --text --report "$P17/s"

# (2) CANDOR_REPORT=<dir> resolves like --report (dir → <dir>/.candor/report), identically, from any CWD.
( cd / && env CANDOR_REPORT="$W/rust" "$QUERY" where Fs --json ) > "$P17/r_env.json" 2>/dev/null
canoneq "rust CANDOR_REPORT=<dir> != discovered" "$P17/r_env.json" "$P17/r_disc.json"
( cd / && env CANDOR_REPORT="$P17/j" java -jar "$JAR" where Fs --json ) > "$P17/j_env.json" 2>/dev/null
canoneq "java CANDOR_REPORT=<dir> != discovered" "$P17/j_env.json" "$P17/j_disc.json"
if [ -n "$TS_OK" ]; then
  ( cd / && env CANDOR_REPORT="$P17/t" node "$TS_DIR/query.mjs" where Fs --json ) > "$P17/t_env.json" 2>/dev/null
  canoneq "ts CANDOR_REPORT=<dir> != discovered" "$P17/t_env.json" "$P17/t_disc.json"
fi

# (3) containment's SINGLE positional is the BASELINE — the discovery ratchet GATES (exit 1 on a leak),
#     never silently drops to non-gating report mode. Reuses PART 11's leak fixtures (current LEAKS vs base).
( cd "$W/containment/rust/current" && "$QUERY" containment "$W/containment/rust/base/.candor/report" --json ) >/dev/null 2>&1
[ "$?" = 1 ] || p17fail "rust containment: discovery form \`containment <baseline>\` must GATE (exit 1 on the Fs→svc leak), not drop to report mode"
mkdir -p "$P17/cont_j/.candor"
java -jar "$JAR" "$W/cont_jcur" --json "$P17/cont_j/.candor/report.cur.jvm.json" >/dev/null 2>&1
( cd "$P17/cont_j" && java -jar "$JAR" containment "$W/cont_jbase.json" --json ) >/dev/null 2>&1
[ "$?" = 1 ] || p17fail "java containment: discovery form \`containment <baseline>\` must GATE (exit 1 on the Fs→svc leak), not drop to report mode"

# (4) A report loaded by a direct <file>.json path loads its SIDECAR call graph too: transitive `callers`
#     via --report <.json> MUST equal the prefix form (and be non-empty) — else the sidecar is silently
#     dropped and a blast-radius query under-reports at exit 0 (the §4 cardinal sin; regressed once here).
sidecar_eq() { # $1 label ; $2 prefix-form json ; $3 json-form json
  python3 -c 'import json,sys
leaf=lambda x: x.split("::")[-1].split(".")[-1]
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
ta=sorted(map(leaf,a.get("transitive",[]))); tb=sorted(map(leaf,b.get("transitive",[])))
sys.exit(0 if ta==tb and len(ta)>0 else 1)' "$2" "$3" 2>/dev/null \
    || p17fail "$1: transitive callers via --report <.json> must equal the prefix form AND be non-empty (sidecar dropped?)"
}
RJSON="$(ls "$W"/rust/.candor/report*.scan.json 2>/dev/null | grep -v -e callgraph -e hierarchy | head -1)"
"$QUERY" callers transitive_leaf --report "$W/rust/.candor/report" --json > "$P17/r_cg_pfx.json"  2>/dev/null
"$QUERY" callers transitive_leaf --report "$RJSON" --json                 > "$P17/r_cg_json.json" 2>/dev/null
sidecar_eq "rust callers <.json>" "$P17/r_cg_pfx.json" "$P17/r_cg_json.json"
java -jar "$JAR" callers transitive_leaf --report "$P17/j" --json                             > "$P17/j_cg_pfx.json"  2>/dev/null
java -jar "$JAR" callers transitive_leaf --report "$P17/j/.candor/report.app.jvm.json" --json > "$P17/j_cg_json.json" 2>/dev/null
sidecar_eq "java callers <.json>" "$P17/j_cg_pfx.json" "$P17/j_cg_json.json"
if [ -n "$TS_OK" ]; then
  TJSON="$(ls "$P17"/t/.candor/report*.json 2>/dev/null | grep -v -e callgraph -e hierarchy | head -1)"
  node "$TS_DIR/query.mjs" callers transitive_leaf --report "$P17/t/.candor/report" --json > "$P17/t_cg_pfx.json"  2>/dev/null
  node "$TS_DIR/query.mjs" callers transitive_leaf --report "$TJSON" --json                > "$P17/t_cg_json.json" 2>/dev/null
  sidecar_eq "ts callers <.json>" "$P17/t_cg_pfx.json" "$P17/t_cg_json.json"
fi

if [ "$P17_OK" = 0 ]; then
  echo "  -> MATCH — every engine drives a query the same way (discovery ≡ --report ≡ OLD positional, --json, --policy flag); a missing report fails loud (exit 2); CANDOR_REPORT=<dir> resolves; containment discovery gates"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# PART 18 — CROSS-PACKAGE INTERFACE DISPATCH (interfaceUnion, WORKSPACE-CHAINING-DESIGN.md).            [TIER 2]
# A consumer calling an interface/protocol method on a value whose type is imported from a CHAINED dep MUST
# resolve to the implementation's effect (via the producer's synthetic `interfaceUnion` union entry), never
# read pure. FOUR-WAY since 2026-07-26. Producer scans the dep with CANDOR_WORKSPACE_CHAIN=1; the consumer
# chains that report. Runs per shipping engine when present.
#
# java was N/A here until 2026-07-26, on the grounds that "whole-classpath bytecode resolves cross-module
# dispatch natively". That is true of an UNCHAINED whole-classpath scan and FALSE of a chained one, where the
# implementer is in the other tree — the same "ask separately what an engine does at the BOUNDARY" lesson the
# initializer-edge vein (PART 19) taught. Its consumer needed no change at all: candor-java keys entries by
# `owner.name+desc`, exactly the key it forms for an INVOKEINTERFACE site, so a union entry lands where the
# join already looks. Only the PRODUCER was missing (candor-spec DEP-RECEIVER-TYPING-DESIGN.md).
# ====================================================================================================
P18="$W/p18"; mkdir -p "$P18"; P18_OK=0
p18fail() { echo "     FAIL $1"; P18_OK=1; }

# --- candor-scan (rust): dep exports a trait + impl doing Fs; app calls ch.publish() on &dyn Trait -------
mkdir -p "$P18/rs/dep/src" "$P18/rs/app/src" "$P18/rs/deps"
printf '[package]\nname = "dep"\nversion = "0.0.0"\nedition = "2021"\n' > "$P18/rs/dep/Cargo.toml"
printf 'pub trait OutboundChannel { fn publish(&self); }\npub struct AwsChannel;\nimpl OutboundChannel for AwsChannel { fn publish(&self) { let _ = std::fs::remove_file("/tmp/x"); } }\n' > "$P18/rs/dep/src/lib.rs"
printf '[package]\nname = "app"\nversion = "0.0.0"\nedition = "2021"\n[dependencies]\ndep = { path = "../dep" }\n' > "$P18/rs/app/Cargo.toml"
printf 'use dep::OutboundChannel;\npub fn use_ch(ch: &dyn OutboundChannel) { ch.publish(); }\n' > "$P18/rs/app/src/lib.rs"
CANDOR_WORKSPACE_CHAIN=1 "$SCAN" "$P18/rs/dep" --json > "$P18/rs/deps/dep.json" 2>/dev/null
CANDOR_DEPS="$P18/rs/deps" "$SCAN" "$P18/rs/app" --json > "$P18/rs_app.json" 2>/dev/null
python3 -c 'import json,sys
r=json.load(open(sys.argv[1])); u=[f for f in r["functions"] if f["fn"].endswith("use_ch")]
sys.exit(0 if u and "Fs" in (u[0].get("inferred") or []) else 1)' "$P18/rs_app.json" \
    || p18fail "candor-scan: use_ch did not inherit Fs across the chained trait (read pure)"
python3 -c 'import json,sys
r=json.load(open(sys.argv[1]))
sys.exit(0 if any(f.get("interfaceUnion") and f["hash"].endswith("#OutboundChannel::publish") for f in r["functions"]) else 1)' "$P18/rs/deps/dep.json" \
    || p18fail "candor-scan: dep emitted no interfaceUnion entry for OutboundChannel::publish"

# --- candor-java: dep exports an interface + impl doing Fs; app calls s.save() on a Store-typed param ----
# The two trees are compiled together (the app must see `lib.Store` to compile) and then SPLIT, so the app
# scan sees only its own class — the boundary the rung is about.
mkdir -p "$P18/java/src/lib" "$P18/java/src/app"
printf 'package lib;\npublic interface Store { void save(String s); }\n' > "$P18/java/src/lib/Store.java"
printf 'package lib;\nimport java.io.*;\npublic class FileStore implements Store {\n  public void save(String s) { try { new FileWriter("/tmp/x").write(s); } catch (IOException e) {} }\n}\n' > "$P18/java/src/lib/FileStore.java"
printf 'package app;\nimport lib.Store;\npublic class Go { public void run(Store s) { s.save("hello"); } }\n' > "$P18/java/src/app/Go.java"
javac -d "$P18/java/all" "$P18/java/src/lib/Store.java" "$P18/java/src/lib/FileStore.java" "$P18/java/src/app/Go.java" 2>/dev/null
mkdir -p "$P18/java/jdep" "$P18/java/japp/app" && cp -r "$P18/java/all/lib" "$P18/java/jdep/" 2>/dev/null
cp "$P18/java/all/app/Go.class" "$P18/java/japp/app/" 2>/dev/null
rm -f "$P18/j_dep.json" "$P18/j_app.json"      # standing-bar item 7: never read back a stale arm
CANDOR_WORKSPACE_CHAIN=1 java -jar "$JAR" "$P18/java/jdep" --json "$P18/j_dep.json" >/dev/null 2>&1
CANDOR_DEPS="$P18/j_dep.json" java -jar "$JAR" "$P18/java/japp" --json "$P18/j_app.json" >/dev/null 2>&1
python3 -c 'import json,sys
r=json.load(open(sys.argv[1])); u=[f for f in r["functions"] if f["fn"].endswith("Go.run")]
sys.exit(0 if u and "Fs" in (u[0].get("inferred") or []) else 1)' "$P18/j_app.json" \
    || p18fail "candor-java: Go.run did not inherit Fs across the chained interface (Unknown or pure)"
python3 -c 'import json,sys
r=json.load(open(sys.argv[1]))
sys.exit(0 if any(f.get("interfaceUnion") and f["hash"] == "lib/Store.save(Ljava/lang/String;)V" for f in r["functions"]) else 1)' "$P18/j_dep.json" \
    || p18fail "candor-java: dep emitted no interfaceUnion entry for lib/Store.save"

if [ -n "$TS_OK" ]; then
  mkdir -p "$P18/ts/dep" "$P18/ts/app/node_modules"
  printf '{"name":"dep","version":"0.0.0","types":"index.ts","main":"index.js"}' > "$P18/ts/dep/package.json"
  printf 'export interface I { doIt(): Promise<void>; }\nexport class Impl implements I { async doIt(): Promise<void> { await fetch("http://example.com"); } }\n' > "$P18/ts/dep/index.ts"
  printf '{"name":"app","version":"0.0.0"}' > "$P18/ts/app/package.json"
  printf 'import { I } from "dep";\nexport function use(x: I): Promise<void> { return x.doIt(); }\n' > "$P18/ts/app/index.ts"
  cp -r "$P18/ts/dep" "$P18/ts/app/node_modules/dep"
  ( cd "$TS_DIR" && CANDOR_WORKSPACE_CHAIN=1 node scan.mjs "$P18/ts/dep" --json ) > "$P18/ts_dep.json" 2>/dev/null
  ( cd "$TS_DIR" && CANDOR_DEPS="$P18/ts_dep.json" node scan.mjs "$P18/ts/app" --json ) > "$P18/ts_app.json" 2>/dev/null
  python3 -c 'import json,sys
r=json.load(open(sys.argv[1])); u=[f for f in r["functions"] if f["fn"].endswith("use")]
sys.exit(0 if u and "Net" in (u[0].get("inferred") or []) else 1)' "$P18/ts_app.json" \
    || p18fail "candor-ts: use() did not inherit Net across the chained interface (read pure)"
  python3 -c 'import json,sys
r=json.load(open(sys.argv[1]))
sys.exit(0 if any(f.get("interfaceUnion") and f["hash"].endswith("#I.doIt") for f in r["functions"]) else 1)' "$P18/ts_dep.json" \
    || p18fail "candor-ts: dep emitted no interfaceUnion entry for I.doIt"
fi

if [ -n "$SW_OK" ]; then
  mkdir -p "$P18/sw/dep/Sources/Dep" "$P18/sw/app/Sources/App"
  printf '// swift-tools-version:5.5\nimport PackageDescription\nlet package = Package(name: "Dep", targets: [.target(name: "Dep")])\n' > "$P18/sw/dep/Package.swift"
  printf 'import Foundation\npublic protocol OutboundChannel { func publish(_ m: String) }\npublic final class AwsChannel: OutboundChannel { public init() {} public func publish(_ m: String) { try? FileManager.default.removeItem(atPath: "/tmp/x") } }\n' > "$P18/sw/dep/Sources/Dep/channel.swift"
  printf '// swift-tools-version:5.5\nimport PackageDescription\nlet package = Package(name: "App", targets: [.target(name: "App")])\n' > "$P18/sw/app/Package.swift"
  printf 'import Foundation\nimport Dep\npublic func use(_ ch: OutboundChannel) { ch.publish("x") }\n' > "$P18/sw/app/Sources/App/use.swift"
  CANDOR_WORKSPACE_CHAIN=1 "$SW_BIN" "$P18/sw/dep" --json > "$P18/sw_dep.json" 2>/dev/null
  CANDOR_DEPS="$P18/sw_dep.json" "$SW_BIN" "$P18/sw/app" --json > "$P18/sw_app.json" 2>/dev/null
  python3 -c 'import json,sys
r=json.load(open(sys.argv[1])); u=[f for f in r["functions"] if f["fn"].endswith("use")]
sys.exit(0 if u and "Fs" in (u[0].get("inferred") or []) else 1)' "$P18/sw_app.json" \
    || p18fail "candor-swift: use() did not inherit Fs across the chained protocol (read pure)"
  python3 -c 'import json,sys
r=json.load(open(sys.argv[1]))
sys.exit(0 if any(f.get("interfaceUnion") and f["hash"].endswith("#OutboundChannel.publish") for f in r["functions"]) else 1)' "$P18/sw_dep.json" \
    || p18fail "candor-swift: dep emitted no interfaceUnion entry for OutboundChannel.publish"
fi

echo "PART 18 — cross-package interface dispatch (interfaceUnion, WORKSPACE-CHAINING-DESIGN.md)"
if [ "$P18_OK" = 0 ]; then
  echo "  -> MATCH — candor-java + candor-scan + candor-ts + candor-swift all resolve a chained interface/protocol/trait method to the impl's effect (never pure); the union entry is emitted producer-side"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 19 — the INITIALIZER EDGE ACROSS THE SCAN BOUNDARY, four-way                                 [TIER 1]
# ====================================================================================================
# Touching a dependency runs ITS initializer — a module top level, a `<clinit>`, a lazy static. Each engine
# models that correctly for a unit INSIDE the scan; each one dropped it when the owner sat on the other side
# of the scan boundary, so a consumer of an effectful dependency initializer read SOUND-COMPLETE PURE even
# with the dependency's report chained. Found 2026-07-25 on two held-out npm packages and swept to all four
# engines (candor-spec SOUNDNESS-VEIN-initializer-edge.md). Two of them looked clean precisely because the
# inside-scan case works — which is why this differential keys on the CHAINED case specifically.
# The shapes differ (import / GETSTATIC / lazy-static read) but the contract is one: with the dependency's
# report chained, the consumer must NOT be pure. Unchained, each engine is unchanged — that is not a
# regression, it is the honest state when nobody has scanned the dependency.
P19_OK=0
# ---- java: a dep class whose <clinit> reads the environment; the app touches it via GETSTATIC.
mkdir -p "$W/ie/java/dep" "$W/ie/java/app"
printf 'package dep;\npublic class D { public static final String C = System.getenv("IE_CFG"); }\n' > "$W/ie/java/dep/D.java"
printf 'package app;\npublic class A { static final String X = dep.D.C; }\n' > "$W/ie/java/app/A.java"
javac -d "$W/ie/jall" "$W/ie/java/dep/D.java" "$W/ie/java/app/A.java" 2>/dev/null
mkdir -p "$W/ie/jdep" "$W/ie/japp/app" && cp -r "$W/ie/jall/dep" "$W/ie/jdep/" 2>/dev/null
cp "$W/ie/jall/app/A.class" "$W/ie/japp/app/" 2>/dev/null
java -jar "$JAR" "$W/ie/jdep" --json "$W/ie/jdep.json" >/dev/null 2>&1
CANDOR_DEPS="$W/ie/jdep.json" java -jar "$JAR" "$W/ie/japp" --json "$W/ie/japp.json" >/dev/null 2>&1
# ---- rust: a dep crate with an effectful lazy static; the app reads it qualified.
IE_RS="/nonexistent"
if [ -x "$SCAN" ]; then
  mkdir -p "$W/ie/rs/deplib/src" "$W/ie/rs/app/src"
  printf '[package]\nname="deplib"\nversion="0.0.0"\nedition="2021"\n' > "$W/ie/rs/deplib/Cargo.toml"
  printf 'use std::sync::LazyLock;\npub static C: LazyLock<String> = LazyLock::new(|| std::env::var("IE_CFG").unwrap_or_default());\n' > "$W/ie/rs/deplib/src/lib.rs"
  printf '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\ndeplib={path="../deplib"}\n' > "$W/ie/rs/app/Cargo.toml"
  printf 'fn main() { println!("{}", deplib::C.len()); }\n' > "$W/ie/rs/app/src/main.rs"
  ( cd "$W/ie/rs/deplib" && "$SCAN" . >/dev/null 2>&1 )
  cp "$W"/ie/rs/deplib/.candor/report.*.scan.json "$W/ie/rsdep.json" 2>/dev/null
  ( cd "$W/ie/rs/app" && CANDOR_DEPS="$W/ie/rsdep.json" "$SCAN" . >/dev/null 2>&1 )
  IE_RS=$(ls "$W"/ie/rs/app/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)
fi
# ---- ts: a dep package whose module top level reads the environment; the app imports it.
IE_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/ie/ts/dep" "$W/ie/ts/app/src"
  printf '{"name":"iedep","version":"0.0.0","main":"index.js"}\n' > "$W/ie/ts/dep/package.json"
  printf 'const c = process.env.IE_CFG || "";\nmodule.exports = { c };\n' > "$W/ie/ts/dep/index.js"
  node "$TS_DIR/scan.mjs" "$W/ie/ts/dep" --allow-js --out "$W/ie/tsdep" >/dev/null 2>&1
  printf '{"name":"ieapp","version":"0.0.0"}\n' > "$W/ie/ts/app/package.json"
  printf 'import { c } from "iedep";\nexport const v = c;\n' > "$W/ie/ts/app/src/a.ts"
  CANDOR_DEPS="$W/ie/tsdep.json" node "$TS_DIR/scan.mjs" "$W/ie/ts/app" --allow-js --out "$W/ie/tsapp" >/dev/null 2>&1
  IE_TS="$W/ie/tsapp.json"
fi
# ---- swift: a dep package with an effectful global; the app reads it across the module boundary.
IE_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/ie/sw/deplib/Sources/DepLib" "$W/ie/sw/app/Sources/App"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "DepLib", products: [.library(name: "DepLib", targets: ["DepLib"])], targets: [.target(name: "DepLib")])\n' > "$W/ie/sw/deplib/Package.swift"
  printf 'import Foundation\npublic let depCfg = ProcessInfo.processInfo.environment["IE_CFG"] ?? ""\n' > "$W/ie/sw/deplib/Sources/DepLib/Cfg.swift"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "App", dependencies: [.package(path: "../deplib")], targets: [.executableTarget(name: "App", dependencies: [.product(name: "DepLib", package: "deplib")])])\n' > "$W/ie/sw/app/Package.swift"
  printf 'import DepLib\nprint(depCfg.count)\n' > "$W/ie/sw/app/Sources/App/main.swift"
  ( cd "$W/ie/sw/deplib" && "$SW_BIN" . >/dev/null 2>&1 )
  cp "$W"/ie/sw/deplib/.candor/report.*.Swift.json "$W/ie/swdep.json" 2>/dev/null
  ( cd "$W/ie/sw/app" && CANDOR_DEPS="$W/ie/swdep.json" "$SW_BIN" . >/dev/null 2>&1 )
  IE_SW=$(ls "$W"/ie/sw/app/.candor/report.*.Swift.json 2>/dev/null | grep -vE 'callgraph|hierarchy' | head -1)
fi
python3 - "$W/ie/japp.json" "$IE_RS" "$IE_TS" "$IE_SW" <<'PYIE' || P19_OK=1
import json, sys, os
def effectful(path):
    """True when SOME unit in the report carries a non-Unknown effect — the consumer is not reading pure."""
    try: d = json.load(open(path))
    except Exception: return None
    for e in d.get("functions", []):
        if set(e.get("inferred", [])) - {"Unknown"}: return True
    return False
print("\n[19] INITIALIZER EDGE ACROSS THE SCAN BOUNDARY  (a chained dependency's initializer must reach its consumer)")
engines = [("java", sys.argv[1])]
if os.path.exists(sys.argv[2]): engines.append(("rust", sys.argv[2]))
if os.path.exists(sys.argv[3]): engines.append(("ts", sys.argv[3]))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("swift", sys.argv[4]))
fails = 0
for name, path in engines:
    got = effectful(path)
    if got is True:
        print(f"  {name:6s} -> MATCH    (the chained dependency's initializer reaches the consumer)")
    else:
        fails += 1
        why = "unreadable report" if got is None else "consumer reads PURE — the dependency initializer was dropped"
        print(f"  {name:6s} -> DIVERGE  ({why})")
sys.exit(1 if fails else 0)
PYIE

echo "PART 19 — initializer edge across the scan boundary (SOUNDNESS-VEIN-initializer-edge.md)"
if [ "$P19_OK" = 0 ]; then
  echo "  -> MATCH — a chained dependency's initializer reaches its consumer in all four engines; unchained, each is unchanged"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 20 — IMPLICIT STRINGIFICATION ACROSS THE SCAN BOUNDARY, four-way                             [TIER 1]
# ====================================================================================================
# The sharpest instance of the scan-boundary vein (SOUNDNESS-VEIN-crossing-the-scan-boundary.md), and the
# one with the most history: implicit stringification was closed INSIDE the scan in all four engines on
# 2026-07-25, and was still fully live ACROSS it the same day. Reaching an effect through a dependency
# type's `toString`/`Display::fmt`/`description` must not read sound-complete pure once that dependency's
# report is chained — the dep report carries the witness under its own key, and the consumer must consult it.
#
# This is the DEPENDENCY half; PART 19 pins the initializer half of the same boundary. Each engine's syntax
# differs (`"x" + e`, `format!("{}", e)`, `` `${e}` ``, `"\(e)"`) but the contract is one: with the dependency
# chained, a consumer that stringifies an effectful dep value is NOT pure. Unchained, each engine is
# unchanged — that is the honest state when nobody has scanned the dependency, not a regression.
P20_OK=0
# ---- java: a dep class whose toString() reads the environment; the app concatenates it.
mkdir -p "$W/sb/java/dep" "$W/sb/java/app"
printf 'package dep;\npublic class E { @Override public String toString() { return System.getenv("SB_CFG"); } }\n' > "$W/sb/java/dep/E.java"
printf 'package app;\npublic class S { public static String show(dep.E e) { return "x" + e; } }\n' > "$W/sb/java/app/S.java"
javac -d "$W/sb/jall" "$W/sb/java/dep/E.java" "$W/sb/java/app/S.java" 2>/dev/null
mkdir -p "$W/sb/jdep" "$W/sb/japp/app" && cp -r "$W/sb/jall/dep" "$W/sb/jdep/" 2>/dev/null
cp "$W/sb/jall/app/S.class" "$W/sb/japp/app/" 2>/dev/null
java -jar "$JAR" "$W/sb/jdep" --json "$W/sb/jdep.json" >/dev/null 2>&1
CANDOR_DEPS="$W/sb/jdep.json" java -jar "$JAR" "$W/sb/japp" --json "$W/sb/japp.json" >/dev/null 2>&1
# ---- rust: a dep type whose Display::fmt reads the clock; the app formats it.
SB_RS="/nonexistent"
if [ -x "$SCAN" ]; then
  mkdir -p "$W/sb/rs/deplib/src" "$W/sb/rs/app/src"
  printf '[package]\nname="deplib"\nversion="0.0.0"\nedition="2021"\n' > "$W/sb/rs/deplib/Cargo.toml"
  printf 'use std::fmt;\npub struct E;\nimpl fmt::Display for E {\n  fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result { let _ = std::time::SystemTime::now(); write!(f, "e") }\n}\n' > "$W/sb/rs/deplib/src/lib.rs"
  printf '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\ndeplib={path="../deplib"}\n' > "$W/sb/rs/app/Cargo.toml"
  printf 'fn show(e: &deplib::E) -> String { format!("{}", e) }\nfn main() { println!("{}", show(&deplib::E)); }\n' > "$W/sb/rs/app/src/main.rs"
  ( cd "$W/sb/rs/deplib" && "$SCAN" . >/dev/null 2>&1 )
  cp "$W"/sb/rs/deplib/.candor/report.*.scan.json "$W/sb/rsdep.json" 2>/dev/null
  ( cd "$W/sb/rs/app" && CANDOR_DEPS="$W/sb/rsdep.json" "$SCAN" . >/dev/null 2>&1 )
  SB_RS=$(ls "$W"/sb/rs/app/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)
fi
# ---- swift: a dep type whose description reads the environment; the app interpolates it.
SB_SW="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/sb/sw/deplib/Sources/DepLib" "$W/sb/sw/app/Sources/App"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "DepLib", products: [.library(name: "DepLib", targets: ["DepLib"])], targets: [.target(name: "DepLib")])\n' > "$W/sb/sw/deplib/Package.swift"
  printf 'import Foundation\npublic struct E: CustomStringConvertible {\n  public init() {}\n  public var description: String { ProcessInfo.processInfo.environment["SB_CFG"] ?? "" }\n}\n' > "$W/sb/sw/deplib/Sources/DepLib/E.swift"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "App", dependencies: [.package(path: "../deplib")], targets: [.executableTarget(name: "App", dependencies: [.product(name: "DepLib", package: "deplib")])])\n' > "$W/sb/sw/app/Package.swift"
  printf 'import DepLib\nfunc show(_ e: E) -> String { return "x \\(e)" }\nprint(show(E()))\n' > "$W/sb/sw/app/Sources/App/main.swift"
  ( cd "$W/sb/sw/deplib" && "$SW_BIN" . >/dev/null 2>&1 )
  cp "$W"/sb/sw/deplib/.candor/report.*.Swift.json "$W/sb/swdep.json" 2>/dev/null
  ( cd "$W/sb/sw/app" && CANDOR_DEPS="$W/sb/swdep.json" "$SW_BIN" . >/dev/null 2>&1 )
  SB_SW=$(ls "$W"/sb/sw/app/.candor/report.*.Swift.json 2>/dev/null | grep -vE 'callgraph|hierarchy' | head -1)
fi
# ---- ts: a dep class whose toString() reads the environment; the app template-interpolates it.
SB_TS="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/sb/ts/deplib/src" "$W/sb/ts/app/src" "$W/sb/ts/app/node_modules"
  printf '{"name":"deplib","version":"0.0.0","main":"src/index.ts"}\n' > "$W/sb/ts/deplib/package.json"
  printf 'export class E {\n  toString(): string { return process.env.SB_CFG ?? ""; }\n}\n' > "$W/sb/ts/deplib/src/index.ts"
  printf '{"name":"app","version":"0.0.0","dependencies":{"deplib":"file:../deplib"}}\n' > "$W/sb/ts/app/package.json"
  printf 'import { E } from "deplib";\nexport function show(e: E): string { return `x ${e}`; }\n' > "$W/sb/ts/app/src/index.ts"
  ln -sfn "$W/sb/ts/deplib" "$W/sb/ts/app/node_modules/deplib"
  ( cd "$TS_DIR" && node scan.mjs "$W/sb/ts/deplib" >/dev/null 2>&1 )
  cp "$W/sb/ts/deplib/.candor/report.json" "$W/sb/tsdep.json" 2>/dev/null
  ( cd "$TS_DIR" && CANDOR_DEPS="$W/sb/tsdep.json" node scan.mjs "$W/sb/ts/app" >/dev/null 2>&1 )
  SB_TS="$W/sb/ts/app/.candor/report.json"
fi
python3 - "$W/sb/japp.json" "$SB_RS" "$SB_SW" "$SB_TS" <<'PYSB' || P20_OK=1
import json, sys, os
def effectful(path):
    try: d = json.load(open(path))
    except Exception: return None
    for e in d.get("functions", []):
        if set(e.get("inferred", [])) - {"Unknown"}: return True
    return False
print("\n[20] IMPLICIT STRINGIFICATION ACROSS THE SCAN BOUNDARY  (a chained dependency's toString/Display/description witness must reach its consumer)")
engines = [("java", sys.argv[1])]
if os.path.exists(sys.argv[2]): engines.append(("rust", sys.argv[2]))
if len(sys.argv) > 3 and os.path.exists(sys.argv[3]): engines.append(("swift", sys.argv[3]))
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]): engines.append(("ts", sys.argv[4]))
fails = 0
for name, path in engines:
    got = effectful(path)
    if got is True:
        print(f"  {name:6s} -> MATCH    (the chained dependency's stringification witness reaches the consumer)")
    else:
        fails += 1
        why = "unreadable report" if got is None else "consumer reads PURE — the witness was dropped"
        print(f"  {name:6s} -> DIVERGE  ({why})")
sys.exit(1 if fails else 0)
PYSB

echo "PART 20 — implicit stringification across the scan boundary (SOUNDNESS-VEIN-crossing-the-scan-boundary.md)"
if [ "$P20_OK" = 0 ]; then
  echo "  -> MATCH — a chained dependency's stringification witness reaches its consumer in all four engines"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 21 — COULD-NOT-FORM-A-KEY MUST DISCLOSE, NOT READ PURE                             [TIER 1]
#
# DEP-RECEIVER-TYPING-DESIGN.md, half 1. A chained lookup coming back empty means two different things:
#   keyed-and-missed     the key WAS formed, the dep's report has no entry -> a genuine purity claim,
#                        because dep reports omit pure functions (SPEC §2 rule 3). Silence is correct.
#   could-not-form-a-key the receiver was never typed, so NO lookup happened -> licenses nothing.
# Every engine used to treat both as the first, which makes the caller a CONFIDENT purity claim about a
# function that performs I/O — and under the ⟨0.21⟩ manifest the fn is still counted in `analyzed`, so its
# absence reads as a positive claim rather than a gap.
#
# This pins the DISCLOSURE, not the effect: the consumer must carry `Unknown` (any `unknownWhy` reason).
# Recovering the effect itself needs the format rung (half 2) and is deliberately NOT asserted here.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
P21_OK=0
# ---- rust: a receiver bound from a dep FACTORY. The factory is pure, so it is absent from the dep's
#      report entirely — there is no return type to travel, and `c` is never typed.
P21_RS="/nonexistent"
if [ -x "$SCAN" ]; then
  mkdir -p "$W/ukr/rs/deplib/src" "$W/ukr/rs/app/src"
  printf '[package]\nname="deplib"\nversion="0.0.0"\nedition="2021"\n' > "$W/ukr/rs/deplib/Cargo.toml"
  printf 'pub struct Client;\nimpl Client {\n  pub fn fetch(&self) -> String { std::fs::read_to_string("/etc/x").unwrap_or_default() }\n}\npub fn build() -> Client { Client }\n' > "$W/ukr/rs/deplib/src/lib.rs"
  printf '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\ndeplib={path="../deplib"}\n' > "$W/ukr/rs/app/Cargo.toml"
  printf 'pub fn go() -> String { let c = deplib::build(); c.fetch() }\n' > "$W/ukr/rs/app/src/lib.rs"
  ( cd "$W/ukr/rs/deplib" && "$SCAN" . >/dev/null 2>&1 )
  cp "$W"/ukr/rs/deplib/.candor/report.*.scan.json "$W/ukr/rsdep.json" 2>/dev/null
  ( cd "$W/ukr/rs/app" && CANDOR_DEPS="$W/ukr/rsdep.json" "$SCAN" . >/dev/null 2>&1 )
  P21_RS=$(ls "$W"/ukr/rs/app/.candor/report.*.scan.json 2>/dev/null | grep -v callgraph | head -1)
fi
# ---- java: dispatch on a DEP-DECLARED INTERFACE whose impl lives in the dep. The site names the
#      interface (a declaration the JVM never runs); the body is keyed under the impl's owner.
mkdir -p "$W/ukr/java/lib" "$W/ukr/java/app"
printf 'package lib;\npublic interface Store { void save(String s); }\n' > "$W/ukr/java/lib/Store.java"
printf 'package lib;\nimport java.io.*;\npublic class FileStore implements Store {\n  public void save(String s) { try (FileWriter w = new FileWriter("/tmp/x")) { w.write(s); } catch (Exception e) {} }\n}\n' > "$W/ukr/java/lib/FileStore.java"
printf 'package lib;\npublic class Factory { public static Store build() { return new FileStore(); } }\n' > "$W/ukr/java/lib/Factory.java"
printf 'package app;\npublic class Go { public void run() { lib.Store s = lib.Factory.build(); s.save("hello"); } }\n' > "$W/ukr/java/app/Go.java"
javac -d "$W/ukr/jall" "$W/ukr/java/lib"/*.java "$W/ukr/java/app/Go.java" 2>/dev/null
mkdir -p "$W/ukr/jlib" "$W/ukr/japp/app" && cp -r "$W/ukr/jall/lib" "$W/ukr/jlib/" 2>/dev/null
cp "$W/ukr/jall/app/Go.class" "$W/ukr/japp/app/" 2>/dev/null
java -jar "$JAR" "$W/ukr/jlib" --json "$W/ukr/jlib.json" >/dev/null 2>&1
CANDOR_DEPS="$W/ukr/jlib.json" java -jar "$JAR" "$W/ukr/japp" --json "$W/ukr/japp.json" >/dev/null 2>&1
# ---- ts: the PUBLISHED shape — dist JS + `.d.ts`. TypeScript reaches this case by a different road than
#      rust: a receiver it genuinely cannot type is `any`, which already reads `callback:` Unknown, because
#      return types travel in the typings. Its unformed key is the receiver typed to an ABSTRACTION the
#      dependency's report has no vocabulary for — the factory returns the INTERFACE, and the only body is
#      hashed under the implementing class the consumer never sees.
TS_UK="/nonexistent"
if [ -d "$TS_DIR" ] && [ -f "$TS_DIR/scan.mjs" ]; then
  mkdir -p "$W/ukr/ts/deplib/src" "$W/ukr/ts/app/src" "$W/ukr/ts/app/node_modules/deplib/dist"
  printf '{"name":"deplib","version":"0.0.0"}\n' > "$W/ukr/ts/deplib/package.json"
  printf 'import * as fs from "node:fs";\nexport interface Store { save(s: string): void; }\nexport class FileStore implements Store {\n  save(s: string): void { fs.writeFileSync("/tmp/x", s); }\n}\nexport function build(): Store { return new FileStore(); }\n' > "$W/ukr/ts/deplib/src/index.ts"
  printf '{"name":"app","version":"0.0.0"}\n' > "$W/ukr/ts/app/package.json"
  printf 'import { build } from "deplib";\nexport function go(): void { const s = build(); s.save("hello"); }\n' > "$W/ukr/ts/app/src/index.ts"
  printf '{"name":"deplib","version":"0.0.0","types":"dist/index.d.ts","main":"dist/index.js"}\n' > "$W/ukr/ts/app/node_modules/deplib/package.json"
  printf 'export interface Store { save(s: string): void; }\nexport declare function build(): Store;\n' > "$W/ukr/ts/app/node_modules/deplib/dist/index.d.ts"
  printf 'exports.build = function () { return {}; };\n' > "$W/ukr/ts/app/node_modules/deplib/dist/index.js"
  ( cd "$TS_DIR" && node scan.mjs "$W/ukr/ts/deplib" >/dev/null 2>&1 )
  cp "$W/ukr/ts/deplib/.candor/report.json" "$W/ukr/tsdep.json" 2>/dev/null
  ( cd "$TS_DIR" && CANDOR_DEPS="$W/ukr/tsdep.json" node scan.mjs "$W/ukr/ts/app" >/dev/null 2>&1 )
  TS_UK="$W/ukr/ts/app/.candor/report.json"
fi
# ---- swift: a receiver bound from a dep FACTORY. The factory is pure, so it is absent from the dep's
#      report and no return type travels — the binding is never typed and no key is ever formed.
SW_UK="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/ukr/sw/deplib/Sources/DepLib" "$W/ukr/sw/app/Sources/App"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "DepLib", products: [.library(name: "DepLib", targets: ["DepLib"])], targets: [.target(name: "DepLib")])\n' > "$W/ukr/sw/deplib/Package.swift"
  printf 'import Foundation\npublic protocol Store { func save(_ s: String) }\npublic final class FileStore: Store {\n  public init() {}\n  public func save(_ s: String) { try? s.write(toFile: "/tmp/x", atomically: true, encoding: .utf8) }\n}\npublic func build() -> Store { return FileStore() }\n' > "$W/ukr/sw/deplib/Sources/DepLib/Store.swift"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "App", dependencies: [.package(path: "../deplib")], targets: [.executableTarget(name: "App", dependencies: [.product(name: "DepLib", package: "deplib")])])\n' > "$W/ukr/sw/app/Package.swift"
  printf 'import DepLib\nfunc goFactory() { let s = build(); s.save("hello") }\ngoFactory()\n' > "$W/ukr/sw/app/Sources/App/main.swift"
  ( cd "$W/ukr/sw/deplib" && "$SW_BIN" . >/dev/null 2>&1 )
  cp "$W"/ukr/sw/deplib/.candor/report.*.Swift.json "$W/ukr/swdep.json" 2>/dev/null
  ( cd "$W/ukr/sw/app" && CANDOR_DEPS="$W/ukr/swdep.json" "$SW_BIN" . >/dev/null 2>&1 )
  SW_UK=$(ls "$W"/ukr/sw/app/.candor/report.*.Swift.json 2>/dev/null | grep -vE 'callgraph|hierarchy' | head -1)
fi
python3 - "$W/ukr/japp.json" "$P21_RS" "$TS_UK" "$([ -x "$SCAN" ] && echo 1 || echo 0)" "$([ -n "$TS_PRESENT" ] && echo 1 || echo 0)" "$SW_UK" "$([ -n "$SW_PRESENT" ] && echo 1 || echo 0)" <<'PYUK' || P21_OK=1
import json, sys, os
def verdict(path, fn):
    """(disclosed, detail). A fn ABSENT from `functions` is the defect: under ⟨0.21⟩ it is still
    counted in `analyzed`, so absence is a purity CLAIM, not a gap."""
    try: d = json.load(open(path))
    except Exception: return None, "unreadable report"
    for e in d.get("functions", []):
        if e.get("fn") == fn or (e.get("hash") or "").endswith(f"#{fn}"):
            inf = e.get("inferred", [])
            # The invariant is "MUST NOT CLAIM PURITY", not "must say Unknown". An engine that RESOLVES
            # the effect satisfies it more strongly than one that hedges — and an engine which has landed
            # the typeSurface rung does exactly that, so demanding Unknown here would fail a strict
            # improvement. Either disclosure or determination passes; only silence fails.
            if "Unknown" in inf: return True, f"DISCLOSED — Unknown {e.get('unknownWhy') or ''}"
            if inf: return True, f"RESOLVED — {inf} (typeSurface: stronger than a hedge)"
            return False, f"present but reads pure {e.get('invisible') or ''}"
    return False, "ABSENT from the report — a confident purity claim"
print("\n[21] COULD-NOT-FORM-A-KEY MUST NOT READ PURE  (disclose it, or resolve it — never claim purity)")
engines = [("java", sys.argv[1], "app.Go.run")]
fails = 0
# An engine whose binary is absent is legitimately skipped; an engine whose binary is PRESENT but whose
# report never appeared is a FAILURE, not a skip. Distinguishing the two is the whole point — a run that
# quietly checks three engines instead of four reads exactly like a run that checked four and agreed.
# (This bit immediately: renaming the fixture root left one path stale, rust's report went missing, and
# the row printed java/ts/swift with no mention that rust had dropped out.)
for name, argi, fn, present in (("rust", 2, "go", sys.argv[4] == "1"),
                                ("ts", 3, "src.index.go", sys.argv[5] == "1"),
                                ("swift", 6, "goFactory", sys.argv[7] == "1")):
    path = sys.argv[argi]
    if os.path.exists(path):
        engines.append((name, path, fn))
    elif present:
        fails += 1
        print(f"  {name:6s} -> FAIL     (engine PRESENT but its PART 21 report was never produced at "
              f"{path or '<unset>'} — a missing arm is not a passing arm)")
for name, path, fn in engines:
    ok, why = verdict(path, fn)
    if ok:
        print(f"  {name:6s} -> MATCH    ({why})")
    else:
        fails += 1
        print(f"  {name:6s} -> DIVERGE  ({why})")
sys.exit(1 if fails else 0)
PYUK

echo "PART 21 — could-not-form-a-key discloses (DEP-RECEIVER-TYPING-DESIGN.md half 1)"
if [ "$P21_OK" = 0 ]; then
  echo "  -> MATCH — an untyped cross-package receiver discloses instead of reading pure in all four engines"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 22 — A CHAINED DEP JOIN CARRIES THE WHOLE SURFACE, NOT JUST THE EFFECT          [TIER 1]
#
# Four engines, four independent instances of ONE defect, all found within a day of each other:
#   candor-rust   THREE apply sites; drop-glue carried effects+paths only, dep-lazy carried no
#                 `invisible`/`incomplete`                                              (7cb5748)
#   candor-java   TWO copies; `crossDepJoin` reproduced `inheritDepFn` line for line and drifted until
#                 the ⟨0.19⟩ reason class reached the hand-off path and NOT the ordinary call path,
#                 leaving a shipped, conformance-pinned gate silently inert            (6ab26e4)
#   candor-swift  THREE copies; the chained-global site dropped tables/invisible/incomplete (84a71ea)
#   candor-ts     TWO drifted copies; a chained dep's Unknown lost its REASON CLASS      (4dad22d)
# Each engine folded its copies into one apply site. Nothing pins that they stay folded, and the
# failure mode is silent in every direction that matters: the EFFECT still travels, so a corpus A/B
# shows nothing, while the literal surface that a policy matches on, or the disclosure that qualifies
# the verdict, quietly does not. A join that carries `Fs` and drops `paths` lets `allow Fs /tmp/**`
# pass on a dependency that reads /etc/shadow.
#
# THE ASSERTION IS RELATIVE, and deliberately so: for each surface, whatever the DEPENDENCY's own
# report carries, the consumer's entry must contain. It is NOT "every engine extracts the same
# literals" — swift does not lift a `Process.launchPath` string into `cmds`, and that is a producer
# precision question, not this contract. Keying the assertion off each engine's own dep report makes
# the part test the JOIN in every engine while asserting nothing about extraction, so a producer gap
# cannot make this row fail and cannot make it vacuous either: the row reports what it compared.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
P22_OK=0
mkdir -p "$W/dsurf"
# ---- rust
P22_RS_DEP="/nonexistent"; P22_RS_APP="/nonexistent"
if [ -x "$SCAN" ]; then
  mkdir -p "$W/dsurf/rs/deplib/src" "$W/dsurf/rs/app/src"
  printf '[package]\nname="deplib"\nversion="0.0.0"\nedition="2021"\n' > "$W/dsurf/rs/deplib/Cargo.toml"
  printf 'pub trait Sink { fn emit(&self); }\npub fn work(s: &dyn Sink) {\n  let _ = std::fs::read_to_string("/surface/path");\n  let _ = std::process::Command::new("surfacecmd").status();\n  s.emit();\n}\n' > "$W/dsurf/rs/deplib/src/lib.rs"
  printf '[package]\nname="app"\nversion="0.0.0"\nedition="2021"\n\n[dependencies]\ndeplib="1"\n' > "$W/dsurf/rs/app/Cargo.toml"
  printf 'pub fn go(s: &dyn deplib::Sink) { deplib::work(s); }\n' > "$W/dsurf/rs/app/src/lib.rs"
  ( cd "$W/dsurf/rs/deplib" && "$SCAN" . --json > "$W/dsurf/rsdep.json" 2>/dev/null )
  ( cd "$W/dsurf/rs/app" && CANDOR_DEPS="$W/dsurf/rsdep.json" "$SCAN" . --json > "$W/dsurf/rsapp.json" 2>/dev/null )
  P22_RS_DEP="$W/dsurf/rsdep.json"; P22_RS_APP="$W/dsurf/rsapp.json"
fi
# ---- java
P22_J_DEP="/nonexistent"; P22_J_APP="/nonexistent"
if [ -n "$JAR" ] && [ -f "$JAR" ]; then
  mkdir -p "$W/dsurf/j"
  printf 'package lib;\nimport java.io.*;\npublic interface Sink { void emit(); }\n' > "$W/dsurf/j/Sink.java"
  printf 'package lib;\nimport java.io.*;\npublic class Work { public static void work(Sink s) throws Exception {\n  new FileReader("/surface/path").close();\n  Runtime.getRuntime().exec("surfacecmd");\n  s.emit();\n} }\n' > "$W/dsurf/j/Work.java"
  javac -d "$W/dsurf/j/libc" "$W/dsurf/j/Sink.java" "$W/dsurf/j/Work.java" 2>/dev/null
  java -jar "$JAR" "$W/dsurf/j/libc" --json "$W/dsurf/jdep.json" >/dev/null 2>&1
  printf 'package app;\npublic class Go { public void run(lib.Sink s) throws Exception { lib.Work.work(s); } }\n' > "$W/dsurf/j/Go.java"
  javac -cp "$W/dsurf/j/libc" -d "$W/dsurf/j/appc" "$W/dsurf/j/Go.java" 2>/dev/null
  CANDOR_DEPS="$W/dsurf/jdep.json" java -jar "$JAR" "$W/dsurf/j/appc" --json "$W/dsurf/japp.json" >/dev/null 2>&1
  P22_J_DEP="$W/dsurf/jdep.json"; P22_J_APP="$W/dsurf/japp.json"
fi
# ---- ts
P22_T_DEP="/nonexistent"; P22_T_APP="/nonexistent"
if [ -n "$TS_PRESENT" ]; then
  mkdir -p "$W/dsurf/ts/deplib/src" "$W/dsurf/ts/app/src" "$W/dsurf/ts/app/node_modules/deplib"
  printf '{"name":"deplib","version":"1.0.0","main":"src/index.ts"}\n' > "$W/dsurf/ts/deplib/package.json"
  printf 'import * as fs from "node:fs";\nimport { execSync } from "node:child_process";\nexport interface Sink { emit(): void }\nexport function work(s: Sink): void {\n  fs.readFileSync("/surface/path");\n  execSync("surfacecmd");\n  s.emit();\n}\n' > "$W/dsurf/ts/deplib/src/index.ts"
  ( cd "$TS_DIR" && node scan.mjs "$W/dsurf/ts/deplib" --json > "$W/dsurf/tsdep.json" 2>/dev/null )
  cp -r "$W/dsurf/ts/deplib/." "$W/dsurf/ts/app/node_modules/deplib/" 2>/dev/null
  printf '{"name":"app","version":"0.0.0","dependencies":{"deplib":"1.0.0"}}\n' > "$W/dsurf/ts/app/package.json"
  printf 'import { work, Sink } from "deplib";\nexport function go(s: Sink): void { work(s); }\n' > "$W/dsurf/ts/app/src/index.ts"
  ( cd "$TS_DIR" && CANDOR_DEPS="$W/dsurf/tsdep.json" node scan.mjs "$W/dsurf/ts/app" --json > "$W/dsurf/tsapp.json" 2>/dev/null )
  P22_T_DEP="$W/dsurf/tsdep.json"; P22_T_APP="$W/dsurf/tsapp.json"
fi
# ---- swift
P22_S_DEP="/nonexistent"; P22_S_APP="/nonexistent"
if [ -n "$SW_PRESENT" ]; then
  mkdir -p "$W/dsurf/sw/dep/Sources/DepLib" "$W/dsurf/sw/app/Sources/App"
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "DepLib", products: [.library(name: "DepLib", targets: ["DepLib"])], targets: [.target(name: "DepLib")])\n' > "$W/dsurf/sw/dep/Package.swift"
  printf 'import Foundation\npublic protocol Sink { func emit() }\npublic func work(_ s: any Sink) {\n  _ = try? String(contentsOfFile: "/surface/path", encoding: .utf8)\n  let p = Process(); p.launchPath = "/bin/surfacecmd"; try? p.run()\n  s.emit()\n}\n' > "$W/dsurf/sw/dep/Sources/DepLib/Work.swift"
  ( cd "$W/dsurf/sw/dep" && "$SW_BIN" . --json > "$W/dsurf/swdep.json" 2>/dev/null )
  printf '// swift-tools-version:5.9\nimport PackageDescription\nlet package = Package(name: "App", dependencies: [.package(path: "../dep")], targets: [.executableTarget(name: "App", dependencies: [.product(name: "DepLib", package: "dep")])])\n' > "$W/dsurf/sw/app/Package.swift"
  printf 'import DepLib\nfunc go(_ s: any Sink) { work(s) }\n' > "$W/dsurf/sw/app/Sources/App/main.swift"
  ( cd "$W/dsurf/sw/app" && CANDOR_DEPS="$W/dsurf/swdep.json" "$SW_BIN" . --json > "$W/dsurf/swapp.json" 2>/dev/null )
  P22_S_DEP="$W/dsurf/swdep.json"; P22_S_APP="$W/dsurf/swapp.json"
fi
python3 - "$P22_RS_DEP" "$P22_RS_APP" "$([ -x "$SCAN" ] && echo 1 || echo 0)" \
           "$P22_J_DEP" "$P22_J_APP" "$([ -n "$JAR" ] && [ -f "$JAR" ] && echo 1 || echo 0)" \
           "$P22_T_DEP" "$P22_T_APP" "$([ -n "$TS_PRESENT" ] && echo 1 || echo 0)" \
           "$P22_S_DEP" "$P22_S_APP" "$([ -n "$SW_PRESENT" ] && echo 1 || echo 0)" <<'PYDS' || P22_OK=1
import json, sys, os
# `unknownWhy` is IN this list, and its absence was a defect in this part's first version: the header above
# cites FOUR motivating commits and TWO of them (java 6ab26e4, ts 4dad22d) are a chained dep's `Unknown`
# losing its ⟨0.19⟩ REASON CLASS — which a part comparing only the literal surfaces cannot regress. A
# conformance row that cannot catch the defect it names as its motivation is the "comment asserts what the
# code does not do" pattern with a test around it. The dep fixture below now also carries an unresolvable
# dispatch so the reason class actually exists to compare.
SURFACES = ("hosts", "cmds", "paths", "tables", "unknownWhy")
def entry(path, pred):
    try: d = json.load(open(path))
    except Exception: return None
    for e in d.get("functions", []):
        if pred(e): return e
    return None
def check(name, dep_path, app_path, dep_fn, app_fn):
    """Consumer's surfaces must CONTAIN the dep's. Asserted per surface the dep actually carries, so a
       producer that does not extract a literal makes this vacuous for that surface, never failing."""
    de = entry(dep_path, dep_fn)
    if de is None: return False, "the dependency's own entry is missing — fixture did not produce it"
    ae = entry(app_path, app_fn)
    if ae is None: return False, "consumer ABSENT from the report — a purity claim over a chained call"
    deff = set(de.get("inferred", [])) - {"Unknown"}
    aeff = set(ae.get("inferred", []))
    lost = deff - aeff
    if lost: return False, f"effects dropped by the join: {sorted(lost)}"
    compared, dropped = [], []
    for k in SURFACES:
        dv = set(de.get(k) or [])
        if not dv: continue                      # the dep carries none — nothing to assert
        compared.append(k)
        missing = dv - set(ae.get(k) or [])
        if missing: dropped.append(f"{k}{sorted(missing)}")
    if dropped: return False, "surface dropped by the join: " + ", ".join(dropped)
    if not compared: return True, f"effects {sorted(deff)} travel (no literal surface in the dep to compare)"
    return True, f"effects {sorted(deff)} + {'/'.join(compared)} all travel"
print("\n[22] A CHAINED DEP JOIN CARRIES THE WHOLE SURFACE  (the effect AND the literals it was found with)")
rows = [("rust", 1, 2, 3, lambda e: e.get("fn") == "work",       lambda e: e.get("fn") == "go"),
        ("java", 4, 5, 6, lambda e: "Work.work" in (e.get("fn") or ""), lambda e: "Go.run" in (e.get("fn") or "")),
        ("ts",   7, 8, 9, lambda e: (e.get("fn") or "").endswith("work"), lambda e: (e.get("fn") or "").endswith("go")),
        ("swift",10,11,12, lambda e: e.get("fn") == "work",      lambda e: e.get("fn") == "go")]
fails = 0
for name, di, ai, pi, dfn, afn in rows:
    dep, app, present = sys.argv[di], sys.argv[ai], sys.argv[pi] == "1"
    if not (os.path.exists(dep) and os.path.exists(app)):
        # A missing arm is NOT a passing arm (the lesson PART 21 records): an absent binary is a skip,
        # a PRESENT binary whose report never appeared is a failure.
        if present:
            fails += 1
            print(f"  {name:6s} -> FAIL     (engine PRESENT but its PART 22 reports were never produced)")
        continue
    ok, why = check(name, dep, app, dfn, afn)
    print(f"  {name:6s} -> {'MATCH   ' if ok else 'DIVERGE '} ({why})")
    if not ok: fails += 1
sys.exit(1 if fails else 0)
PYDS

echo "PART 22 — a chained dep join carries the whole surface (SOUNDNESS-VEIN-crossing-the-scan-boundary.md)"
if [ "$P22_OK" = 0 ]; then
  echo "  -> MATCH — the literals a dependency was charged with travel with its effects in all four engines"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 23 — THE MODEL'S OWN LEMMA STILL HOLDS                                              [TIER 1]
#
# Every other PART here is a differential BETWEEN ENGINES. That answers "do the engines agree" and it
# has twice reported OK while all four were wrong the same way. This one is not a differential at all:
# it checks the SPEC's policy semantics against the THEORY they are supposed to implement — PAPER3
# Definitions 30-32/35 and Lemma 2 — using `reference/policy_model.py`, the model as executable code.
#
# WHY IT IS HERE. On 2026-07-27 a shipped engine took `deny Unknown[unresolved]` from a REJECT to a PASS
# when a call was ADDED to the function under test, contradicting Lemma 2's corollary ("a newly-determined
# effect or a newly-disclosed blind spot can only turn a green verdict red"). The lemma was not wrong: the
# engine had reached a signature the model does not admit and coped with a rule that is nowhere in the
# model — default the reason class to `unresolved` when D is empty — which is keyed on ABSENCE and is
# therefore not upward-closed. Nothing in this suite could have caught that, because the model lived only
# in prose and the suite only ever compared engines to each other.
#
# WHAT IT DOES AND DOES NOT COVER. It verifies the model, completely: upward-closure is checked against
# COVERS rather than all ordered pairs, so a single-element step suffices by induction and the check is a
# proof for the whole finite lattice (2^|E| x 2^|R|, derived below rather than hardcoded) rather than a
# sample. It does NOT verify any engine — no engine exposed a way to gate a GIVEN signature (the gate was
# reachable only via `scan --policy`, which computes S from source, and via `whatif`, which reports only
# violations the hypothetical INTRODUCES), so the code-implements-spec direction stayed with the
# differential PARTs above.
#
# ⟨0.24⟩ THAT GAP IS BEING CLOSED: SPEC §3.1 now specifies `gate --report <locator> --policy <file>`,
# which applies a policy to a GIVEN report with no scan. When engines ship it, this PART extends from "the
# model is internally monotone" to "each ENGINE agrees with the model" — feed each one a signature the
# model has already judged and compare verdicts. Do NOT extend it naively: a review found that PAPER3's
# `pure` (Def 32) rejected a disclosed signature where the contract and all four engines pass it, so the
# first differential row would have flagged four CONFORMING engines. The model was amended. The same
# review found Defs 33/34/35 (`forbid`, `allow`, `unknown-ratchet`) also describe verbs that do not exist
# as modelled — those rows must NOT be added until the definitions are reconciled, or this PART will
# manufacture divergences out of the theory.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
P23_OK=0
REF="$HERE/../reference/policy_model.py"
if [ -f "$REF" ]; then
  P23_OUT="$(python3 "$REF" 2>&1)" || P23_OK=1
  echo "$P23_OUT" | sed 's/^/  /'
  # A vacuity floor: the file must actually have checked the whole lattice, not a stub that prints OK.
  # DERIVED, not hardcoded. This grepped for the literal "32768 signatures" until 2026-07-27, when adding
  # the two §1 effects the model was missing (`Ipc`, `Clipboard`) made it 131072 and turned a correct fix
  # into a red suite. The floor was right to fire — the lattice DID change — but a literal cannot tell
  # "the vocabulary grew" from "the check was stubbed out", which is the only thing it exists to detect.
  # So compute the expected size from the model's own E and R and require the printed count to match it.
  P23_EXPECT="$(python3 -c 'import sys; sys.path.insert(0, "'"$HERE"'/../reference"); import policy_model as m; print(2**len(m.E) * 2**len(m.R))' 2>/dev/null)"
  if [ -z "$P23_EXPECT" ]; then
    echo "  FAIL: could not derive the lattice size from the model's own vocabulary"; P23_OK=1
  else
    echo "$P23_OUT" | grep -q "$P23_EXPECT signatures" || {
      echo "  FAIL: the model check did not cover the full lattice (expected $P23_EXPECT signatures from |E|x|R|)"; P23_OK=1; }
  fi
  # And the vocabulary itself must not drift from SPEC §1. ⟨0.24⟩ A REVIEW FOUND THIS BLOCK VACUOUS FOUR
  # WAYS, and the floor above CIRCULAR because of the first of them.
  #
  #   (1) It was a NOTE that never set P23_OK, so drift printed and PASSED. The one check anchored to a
  #       source outside the model was the one that could not fail.
  #   (2) That made the derived floor above CIRCULAR along the vocabulary dimension: P23_EXPECT is
  #       computed by importing the very module whose printed count it checks, so deleting `Ipc` and
  #       `Clipboard` — THE EXACT HISTORICAL DEFECT — moves both numbers together and passes. The floor
  #       detects a stub; it cannot detect a shrink. Only a comparison against SPEC.md can, and that
  #       comparison was the toothless one.
  #   (3) `grep -c ... || echo 0` and the `-gt 0` guard mean that if the table is ever reformatted so the
  #       pattern stops matching, the check SILENTLY SKIPS. A grep returning zero here means the SURFACE
  #       is absent, never that the obligation is — the standing bar this project keeps relearning.
  #   (4) It compared COUNTS. Renaming `Ipc` to `Ipx`, or swapping one effect for another, leaves the
  #       count identical and the vocabularies disjoint at that row.
  #
  # So: compare the NAME SETS, and fail on drift, on an unreadable table, and on an empty parse.
  SPEC_EFFECTS="$(grep -o '^| `[A-Z][A-Za-z]*` |' "$HERE/../SPEC.md" 2>/dev/null | tr -d '|` ' | grep -v '^Unknown$' | sort | tr '\n' ' ')"
  MODEL_EFFECTS="$(python3 -c 'import sys; sys.path.insert(0, "'"$HERE"'/../reference"); import policy_model as m; print(" ".join(sorted(m.E)) + " ")' 2>/dev/null)"
  if [ -z "$SPEC_EFFECTS" ]; then
    echo "  FAIL: parsed ZERO effect rows out of SPEC §1's table — the pattern no longer matches the"
    echo "        document, so the model's vocabulary is unanchored. This is not a skip."
    P23_OK=1
  elif [ -z "$MODEL_EFFECTS" ]; then
    echo "  FAIL: could not read the model's effect vocabulary"; P23_OK=1
  elif [ "$SPEC_EFFECTS" != "$MODEL_EFFECTS" ]; then
    echo "  FAIL: the model's effect vocabulary has DRIFTED from SPEC §1"
    echo "        SPEC  §1: $SPEC_EFFECTS"
    echo "        model E : $MODEL_EFFECTS"
    echo "        (this is also what keeps the lattice floor above non-circular — it is the only"
    echo "         assertion in PART 23 anchored to a source the model does not supply)"
    P23_OK=1
  fi
  echo "$P23_OUT" | grep -q "NOT upward-closed" || { echo "  FAIL: the known-bad rule is no longer demonstrated — the check has stopped discriminating"; P23_OK=1; }
else
  echo "  FAIL: reference/policy_model.py is missing — the theory-vs-spec check cannot run"
  P23_OK=1
fi

echo "PART 23 — the model's own lemma still holds (PAPER3 Lemma 2, over the full lattice)"
if [ "$P23_OK" = 0 ]; then
  echo "  -> MATCH — every shipped verb's rejection set is upward-closed, and the absence-keyed rule still is not"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# CLAUSE CHECK — before any property runs, prove each one still quotes a contract that exists  [TIER 1]
#
# A property enforces a MUST. This asserts that the MUST is IN SPEC.md, verbatim, and that every waiver
# naming an engine as known-broken cites the sentence it violates.
#
# WHY IT IS A PRECONDITION RATHER THAN A PART. PART 29 was once extended with two triggers asserting MUSTs
# the spec explicitly REFUSES — that a judged-nothing report must not exit 0 from `gate --report` (§2 binds
# that rule "AS A DISCLOSURE, NOT AS AN EXIT CODE": *"the exit code and the verdict document are
# UNCHANGED"*), and that a violation read out of an IMPEACHED document must still dominate (§2: *"One
# unreadable among them means the document's claim cannot be trusted … Refuse."*). It failed all four
# engines on those and they were WAIVED as engine defects. Every one was conforming.
#
# The act of finding the quote is the check: writing the citation for that trigger requires opening the
# clause that contradicts it. And a wrong WAIVER is worse than a wrong queue entry — it records a
# conforming engine as broken, in the file whose job is to be trusted later, and makes the suite go GREEN
# over the accusation. Running it first means a property cannot report on engines before it has shown its
# premise is real.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/clause_check.py" ] || { echo "FAIL: clause_check.py is missing — properties would run without their premises checked"; exit 2; }
echo
python3 "$HERE/clause_check.py" || { echo "  -> a property is enforcing something SPEC.md does not say, or a waiver accuses an engine without citing a clause"; rc=1; }

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 24 — P1, SPLIT-INVARIANCE: EACH ENGINE AGAINST ITSELF                                [TIER 1]
#
# PARTs 18-22 are five hand-written instances of ONE property:
#     scan(A u B)  ==  scan(B) chained with report(A),   modulo disclosure
# and they are five of the 44+ instances this vein produced. A human wrote each one and chose each shape
# — and five fixtures written during the wave could not reach the code they named, because the shape was
# wrong. PART 24 replaces the choosing: `gen_split_invariance.py` renders an EFFECT x SPLIT-SHAPE matrix
# (8 effects x 10 shapes = 80 cells) in all four languages, scans each cell BOTH as one tree and as two
# chained packages, and asserts that each engine agrees with ITSELF across the split.
#
# WHY A SELF-DIFFERENTIAL AND NOT ANOTHER CROSS-ENGINE ONE. Every other PART here asks "do the engines
# agree", which is the weakest signal available: four engines share one spec and one author's mental
# model, so a wrong model reads as agreement (the coverage door and the malformed manifest were both
# four-way). An engine cannot share a wrong model with ITSELF across two renderings of one program, so
# this row needs no reference implementation, no second opinion and no expected-value table — the
# engine's own single-tree answer is the oracle for its chained answer.
#
# THE ASSERTION IS DIRECTIONAL, and PART 21's ruling is why. An effect that becomes `Unknown` across the
# split is a DISCLOSED precision loss and is counted, not failed; an effect that disappears with NO
# disclosure — or a function that goes ABSENT, which under <0.21> is a purity CLAIM — fails. Equality
# would fail the cases the family has already decided are correct.
#
# VERIFIED TO CATCH, on two engines, by reverting a shipped boundary fix in an ISOLATED git worktree with
# its own build dir (never the shared binaries — standing bar 7f):
#   candor-ts   625e8fd reverted -> the 8 `implicit_conv` cells go ABSENT, ts only, its other 72 unchanged
#   candor-rust 1623a07 reverted -> the 8 `implicit_conv` cells go ABSENT, rust only, ts/swift unchanged
#
# TWO FLOORS, because a property that quietly tests nothing looks exactly like one that passes:
#   * VACUITY — the row FAILS if any engine's live (non-vacuous) cell count is zero. Currently 80/80 live
#     on all four; the counts print every run.
#   * THE RATCHET — `split-invariance-baseline.json` waives the (engine, split) pairs that are known-
#     broken TODAY, each with a hand fixture that reproduces it without the generator. A failing cell
#     outside the baseline fails the suite, AND a baselined pair whose cells all pass ALSO fails, so a
#     waiver cannot outlive its defect. Run the script without --baseline to see the raw truth.
# Both floors and all three ratchet failure modes were verified to FIRE, not assumed: a bogus waiver on a
# passing pair -> exit 2 STALE WAIVER; an emptied baseline -> exit 1 NEW DEBT naming the pairs; an
# unreadable or missing baseline -> exit 2 (it must never read as "nothing is waived"); zero cells ->
# exit 2 vacuity floor. A misspelled --only is a usage error rather than a silently-empty run, because an
# empty run trips the vacuity floor with a message that is true of zero cells and misleading about the
# engines.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_split_invariance.py" ] || { echo "FAIL: gen_split_invariance.py is missing"; exit 2; }
[ -f "$HERE/split-invariance-baseline.json" ] || { echo "FAIL: split-invariance-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P24_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_split_invariance.py" --baseline "$HERE/split-invariance-baseline.json"
) || P24_OK=1

echo "PART 24 — split-invariance: each engine against ITSELF (SCAN-BOUNDARY-WORK-QUEUE.md §3, P1)"
if [ "$P24_OK" = 0 ]; then
  echo "  -> MATCH — one tree and split+chained agree, per engine, on every live cell outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 25 — P2, CHAIN IDEMPOTENCE: CHAINING A REPORT TWICE == CHAINING IT ONCE               [TIER 1]
#
# P1 varies how the PROGRAM is partitioned and holds the chain fixed. P2 holds one two-package rendering
# fixed and varies what the consumer is HANDED: the same dependency report once, then twice. Same
# self-differential construction and same reason — four engines sharing one spec and one author's mental
# model agree just as readily when the model is wrong, so the arm that chains once is the oracle for the
# arm that chains twice, and there is no expected-value table anywhere in it.
#
# NOT A HYPOTHETICAL. Two reports covering one package in one dep directory is measured at 7/167 dep
# reports in candor-rust, 9/259 in pgman, 30/378 in ebman (ENTRY-COLLISION-DECISION.md) — a dep dir that
# accumulates, `--workspace` prepending its own directory, a package scanned twice. And it has bitten:
# candor-rust 6f2210c, where two byte-identical reports made a consumer VANISH from `functions`, which
# under <0.21> is a positive purity CLAIM and not a gap.
#
# THE RELATION IS EQUALITY, and that is the difference from PART 24. P1 must stay directional because a
# chained arm may legitimately disclose MORE than a single-tree one. Here both arms are the same program,
# the same boundary, the same engine and the same report, so there is nothing either arm can legitimately
# see less of — equality covers the DISCLOSURE too (a duplicate arm that newly calls the package
# `uncovered` is claiming a blind spot it does not have). Justified by measurement rather than taste:
# java, ts and swift are exactly equal on all three duplication spellings, 216/216 live cells.
#
# THREE SPELLINGS, and the third is the one that matters: the same path twice; two byte-identical files;
# and two files whose BYTES differ (sorted keys, different indent) but whose content is identical. An
# engine that dedupes by hashing the file passes the first two and is not idempotent at all — the real
# duplicate in a dep directory is the same package scanned twice, not a `cp`. That is P1's own lesson
# (every hand-written fixture had picked ONE spelling) applied before it could bite.
#
# WHAT IT FOUND ON HEAD: candor-rust drops the inherited effect on ALL THREE spellings — 64/72 live cells
# LOST plus 8 DISC — and re-declares the package uncovered, taking `deny Fs` from exit 1 to exit 0. The
# other three engines are clean. Baselined with a hand-written two-package repro, so no waiver rests on
# the generator being right.
#
# TWO FLOORS, because a property that quietly tests nothing looks exactly like one that passes:
#   * VACUITY — the row FAILS if any (engine, arm) has zero live cells without the engine having REFUSED
#     the input. Live counts print every run (rust 72, java 72, ts 56, swift 72 of 80).
#   * THE RATCHET — `chain-idempotence-baseline.json` waives the known-broken pairs. A failing cell
#     outside it fails the suite, AND a baselined pair whose cells all pass ALSO fails, so a waiver cannot
#     outlive its defect. Run the script without --baseline to see the raw truth.
# An arm that produces no report while exiting ZERO is reported as the harness being broken, never as a
# fail-closed refusal — a mis-invocation must not read as good engine behaviour.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_chain_idempotence.py" ] || { echo "FAIL: gen_chain_idempotence.py is missing"; exit 2; }
[ -f "$HERE/chain-idempotence-baseline.json" ] || { echo "FAIL: chain-idempotence-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P25_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_chain_idempotence.py" --baseline "$HERE/chain-idempotence-baseline.json"
) || P25_OK=1

echo "PART 25 — chain idempotence: one copy of a dep report == two (SCAN-BOUNDARY-WORK-QUEUE.md §3, P2)"
if [ "$P25_OK" = 0 ]; then
  echo "  -> MATCH — chaining a report twice answers exactly as chaining it once, outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 26 — P3, TRUST MONOTONICITY: A REPORT YOU DO NOT TRUST MAY ONLY ADD HEDGES             [TIER 1]
#
# The third self-differential, and the one with two reference arms. Each degraded dep report must sit
# between them:
#     unchained (CANDOR_DEPS unset) <= degraded <= trusted (the report as produced)
# Its KNOWLEDGE may not exceed the trusted arm — a report you distrust cannot teach you something the real
# one did not — and its DISCLOSURE may not fall below the unchained arm — a report you refuse to use
# cannot silence a blind spot you would otherwise have declared. That second bound is the COVERAGE DOOR,
# which was in all four engines: reject a dep report for a version mismatch, register the package as
# covered anyway, and every function it does not mention becomes a confident purity claim.
#
# THE DIRECTION IS PER ARM, and one arm runs the opposite way. For a REPLACE arm (version mismatch,
# missing version, a non-empty <0.21> `unanalyzed`, an unparseable file) the degraded report stands
# INSTEAD of the good one, so losing effects is correct as long as the loss is disclosed. For the BESIDE
# arm (a distrusted copy sitting ALONGSIDE the trusted report — the ordinary accumulating dep directory)
# the trusted report is still there, so a hedge does NOT license dropping what it says. Judging BESIDE by
# the REPLACE rule would report nothing about candor-java's measured `deny Fs` exit 1 -> exit 0; judging
# REPLACE by the BESIDE rule would fail all four engines for the correct §2.1 downgrade.
#
# BOTH DISCLOSURE CHANNELS COUNT — measured, not assumed. Handed an unparseable report, candor-rust and
# candor-ts drop the effects and record the package in `invisible` + `coverage.uncovered`, byte-identical
# to their answer with no dep report at all, which is the CORRECT trust semantics. A property counting
# only `Unknown` as disclosure would have filed that as a cardinal loss on two engines. candor-java and
# candor-swift instead REFUSE the run (exit 2), which is also fine and is reported as REFUSED.
#
# WHAT IT FOUND ON HEAD, and the FOUR-WAY one is new:
#   * ALL FOUR ENGINES read a chained report that lists no functions and declares `analyzed.count: 0`
#     ("I judged nothing") as full coverage: the caller drops out of `functions` — a <0.21> purity claim —
#     with no advisory anywhere, which is strictly MORE confident than the same scan with no report at
#     all. `deny Fs` goes exit 1 -> exit 0. The live shape is futures@0.3.32, whose chained report
#     contains zero functions. The wire CAN express the difference (candor-scan emits count 0 for a
#     `pub use`-only facade crate and count 2 for an all-pure two-function crate) and no engine reads it —
#     which the harness proves rather than asserts, with a NEGATIVE CONTROL arm that differs from the
#     failing one by that single integer and legitimately never fails (§2 chaining rule 3: an all-pure
#     dependency's empty report is a claim, not a blind spot). CONTROL SEPARATION prints
#     INDISTINGUISHABLE for all four; when someone fixes the door the two arms MUST diverge.
#   * candor-rust and candor-java let a DISTRUSTED copy beside the trusted report erase what the trusted
#     report says (rust withdraws the key and re-declares the package uncovered; java's §2.1 downgrade
#     writes `{Unknown}` straight over the `Fs`). ts unions and swift prefers the trusted level: both clean.
# Every one re-derived from a hand-written two-package fixture with HAND-WRITTEN dep reports.
#
# FLOORS, as PART 25: a per-(engine, arm) vacuity floor where REFUSED is the one benign way to have no
# live cells; a reference arm that produces nothing fails the engine outright (the oracle is missing); an
# arm producing no report while exiting 0 is the harness broken and says so; and the same both-ways
# ratchet in `trust-monotonicity-baseline.json`.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_trust_monotonicity.py" ] || { echo "FAIL: gen_trust_monotonicity.py is missing"; exit 2; }
[ -f "$HERE/trust-monotonicity-baseline.json" ] || { echo "FAIL: trust-monotonicity-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P26_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_trust_monotonicity.py" --baseline "$HERE/trust-monotonicity-baseline.json"
) || P26_OK=1

echo "PART 26 — trust monotonicity: a distrusted dep report may only ADD hedges (SCAN-BOUNDARY-WORK-QUEUE.md §3, P3)"
if [ "$P26_OK" = 0 ]; then
  echo "  -> MATCH — every degraded dep report stayed between the unchained and trusted arms, outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 28 — P4, SIGNATURE MONOTONICITY: ADDING A CALL MAY ONLY ADD                            [TIER 1]
#
# The fourth and last self-differential, and the only one that varies the PROGRAM rather than the input
# reports (P2, P3) or the packaging (P1). Each unit is rendered twice — once bare, once with one more
# call in its body — and the augmented arm must be a superset of the base in every channel:
#
#     effects(base) <= effects(base + a call)     reasons(base) <= reasons(base + a call)
#     base present in `functions`  =>  the augmented unit is present too
#
# THE RELATION IS DIRECTIONAL AND RUNS THE OPPOSITE WAY FROM P3. Equality would be wrong and would fail
# every honest engine: the added call is SUPPOSED to contribute. What is forbidden is LOSS. The presence
# conjunct is the sharpest — under <0.21> an absent entry is a POSITIVE purity claim, so a unit that
# drops out of `functions` when a call is added has started making a STRONGER claim on less evidence.
#
# THE DEFECT IT IS BUILT FOR is an engine that, meeting a call it cannot resolve, REPLACES a unit's
# answer instead of widening it: `f(){fs_sink();}` -> ['Fs'] but `f(){fs_sink(); opaque();}` -> ['Unknown'],
# the Fs silently gone. That is a cardinal sin reached by ADDING code, which is the direction real
# programs move in, and the same shape hides behind every CHA fan-out bound in the family — whether
# publishing `['Unknown']` past `CHA_FANOUT_LIMIT` (12 in ts and java) adds to the union or replaces it is
# exactly what the `plus_fanout` arm asks.
#
# ARM ACTIVITY IS PRINTED EVERY RUN, and it is the guard that matters here. A cell counts as "live" when
# its BASE claims something, which says NOTHING about whether the added call did — so an augmentation that
# never changes any engine's answer cannot fail and passes for free. The three MUST_CHANGE arms
# (plus_other, plus_opaque, plus_fanout) FAIL the run if they are inert; the three must-not arms
# (plus_pure, plus_same, plus_recurse) reading 0 everywhere is the CORRECT outcome, and they are what
# catches an engine that loses an effect on meeting a harmless call.
#
# WHAT IT FOUND ON HEAD: nothing in the engines — 48/48 live cells clean on all four. It found TWO
# defects in ITSELF, both of the same kind and both caught by ARM ACTIVITY: a `plus_recurse` guard written
# with Clock sinks (`System.nanoTime`, `Date.now`), so the arm measured its own guard and "changed" 5/5
# cells on exactly the two engines whose spelling it used; and a `plus_fanout` arm rendered with exactly
# CHA_FANOUT_LIMIT implementers, sitting on the boundary of the bound it existed to cross and changing
# nothing anywhere. The first honest run reported OK on all four engines with both arms inert.
#
# VERIFIED TO CATCH: a seeded mutant in candor-scan making an unresolved call REPLACE a unit's concrete
# effects produced exactly 16 LOST_EFF findings on rust (8 effects x the 2 Unknown-introducing arms) with
# the other three engines clean, each naming the shape (`base=Fs arm=+Unknown`).
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_signature_monotonicity.py" ] || { echo "FAIL: gen_signature_monotonicity.py is missing"; exit 2; }
[ -f "$HERE/signature-monotonicity-baseline.json" ] || { echo "FAIL: signature-monotonicity-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P28_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_signature_monotonicity.py" --baseline "$HERE/signature-monotonicity-baseline.json"
) || P28_OK=1

echo "PART 28 — signature monotonicity: adding a call may only ADD (SCAN-BOUNDARY-WORK-QUEUE.md §3, P4)"
if [ "$P28_OK" = 0 ]; then
  echo "  -> MATCH — every added call only widened, on every live cell, outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 29 — P5, INCOMPLETE-VS-VIOLATION DOMINANCE: OVER EVERY GATE                            [TIER 1]
#
# SPEC 3.3.1 has two clauses and only the first one had a test:
#
#     A configured gate over incompletely-analyzed code MUST fail closed (exit != 0);
#     a real violation (exit 1) still dominates.
#
# The second is the one with a body count. candor-rust's AS-EFF-005 baseline guard shipped with it
# inverted -- the incomplete refusal ran BEFORE the baseline compare, so a crate with a real regression
# AND one unparseable file exited 2 and wrote `{ok:false, incomplete:true, violations: []}`. The finding
# was not mis-coded, it was ABSENT FROM THE ARTIFACT a CI consumer reads. Its sibling, the POLICY gate,
# had the identical defect and had been fixed a week earlier; the fix wrote its reasoning into the policy
# gate's comment and never looked thirty lines up the same function. ONE CLAUSE, TWO GATES, ONE TESTED.
#
# So this enumerates the gates rather than testing the one the author had in mind. Three arms per
# (engine, gate), and the relation is a SELF-DIFFERENTIAL -- no expected-value table:
#
#     violation_only    a real violation, everything parses          the CONTROL and the ORACLE
#     incomplete_only   no violation, one unit that will not parse   must FAIL CLOSED
#     both              the same violation plus that same unit       must answer like violation_only,
#                                                                    AND disclose the incompleteness
#
# `violation_only` is the expectation for `both`: whatever an engine reports when it can see everything,
# it must still report when one extra unit is unreadable. The CONTROL IS CHECKED FIRST and its failure is
# reported as CONTROL-DEAD rather than OK -- a dead control makes the row below pass while measuring
# nothing, which this suite has had to add a verdict for twice already.
#
# WHY THE DIRTY DIRECTION IS SOUND, which is what licenses demanding a verdict at all: a parse failure
# makes the scan see LESS; `deny` fires on effects PRESENT and AS-EFF-005 on effects GAINED. Less evidence
# can only MASK a violation, never manufacture one. So a violation found beside unreadable source is real,
# while a CLEAN gate over unreadable source is the false-pure clause 1 forbids. Both are asserted, because
# a "fix" that merely dropped the refusal satisfies one and breaks the other.
#
# WHAT IT FOUND ON HEAD: a gate-level CARDINAL SIN in candor-swift, on both gates. `Parser.parse` is
# error-tolerant and never throws, so a file with a syntax error counted as fully analyzed; error recovery
# folds the declarations after the bad token into the broken function's body, so the effect is
# MISATTRIBUTED and its real owner vanishes from `functions` -- a <0.21> purity claim over a function that
# performs Net. `deny Net Hidden` went exit 1 -> exit 0 with `ok: true` and nothing disclosed, from one
# stray character. Fixed by consulting ParseDiagnosticsGenerator and recording `unanalyzed` while STILL
# walking the recovered tree, so no effect is lost.
#
# TWO HARNESS DEFECTS WERE FIXED BEFORE ANY OF THAT WAS BELIEVED, both of which manufactured findings
# about candor that were findings about the harness: the swift arm scanned `cases.swift` instead of the
# directory (so the "incomplete" arms were not incomplete), and `find_report` excluded two of SPEC 2.2's
# six reserved sidecar segments, so a `.locs.json` sidecar was handed to an engine as a BASELINE.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_incomplete_dominance.py" ] || { echo "FAIL: gen_incomplete_dominance.py is missing"; exit 2; }
[ -f "$HERE/incomplete-dominance-baseline.json" ] || { echo "FAIL: incomplete-dominance-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P29_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_incomplete_dominance.py" --baseline "$HERE/incomplete-dominance-baseline.json"
) || P29_OK=1

echo "PART 29 — incomplete-vs-violation dominance: a real violation survives an incomplete scan (SPEC §3.3.1, P5)"
if [ "$P29_OK" = 0 ]; then
  echo "  -> MATCH — every gate failed closed over unreadable code AND still reported the violation it found, outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 27 — THE ⟨0.24⟩ RUNG'S BEHAVIOUR                                                      [TIER 1]
#
# WHY IT EXISTS. A whole rung of normative requirements shipped with NOTHING behind it: `grep -c` over
# this file returned ZERO for `CONTRIBUTES`, `viaDispatchOn`, `dot-free`, `--class dynamic` and locale.
# SPEC §3.1 says the suite "WILL pin the frontier output including the dot-free arm — it does not yet",
# in the future tense, precisely because the sentence before it had claimed a pin that did not exist. A
# floor bump to 0.24 is gated on this PART existing AND on it having been seen to fail.
#
# SEVEN ROWS, and the engine coverage differs per row because the ⟨0.24⟩ SURFACES differ per engine:
#   R1 §6.2 CONTRIBUTES         4-way on `unverified --class` + 4-way on `gate --report`
#   R2 §3.1 viaDispatchOn       3-way (rust/java/ts) — swift ships no `callers` verb, by design
#   R3 §3.1 the dot-free arm    3-way
#   R4 §3.1 the sidecar triple  3-way
#   R5 §6.2 --class            4-way — `dynamic`, the discrimination control, and the value grammar
#   R6 §3.1 gate --report       4-way — rust and ts landed the verb 2026-07-27
#   R7 §2   locale-independence 4-way
# A surface an engine does not implement prints NOSURF with the reason, never a silent skip: the whole
# failure mode this PART addresses is a document overstating its own coverage.
#
# THE ORACLE IS THE SPEC, not another engine — the difference from PARTs 24–26. Those are
# self-differentials because their property relates two runs of one engine. Here every clause names a
# required ANSWER, and the ⟨0.24⟩ review's own finding was a defect "every engine implemented
# faithfully", which four-way agreement cannot see. R7 is the exception and IS a self-differential: its
# oracle is the same engine's output under a different `LC_ALL`.
#
# WHAT IT FOUND ON HEAD. candor-java's `unverified --class` has not landed the §6.2 repair the other
# three carry: it matches the DIRECT `unknownWhy`, so `--class unresolved` selects NOTHING where rust,
# ts and swift select three functions, and `--class dynamic` selects 2 of 7. Waived in
# `rung024-baseline.json` with a hand repro. java's GATE half is clean, which is §6.2's own diagnosis:
# the divergence is consumer-side, in an open-coded second copy of a rule the gate already had right.
# SEPARATELY, and FOUR-WAY: nobody implements ⟨0.24⟩'s `--class` VALUE GRAMMAR. An unrecognised token
# (`--class dyanmic`) and a repeated `--class` are both specified as usage errors — exit 2 — because a
# filter that cannot be honoured leaves a NARROWER answer, not a wider one, so a typo silently answers a
# question the user did not ask with a smaller number. All four engines exit 0. That is not a divergence
# but a shared gap, so it carries the suite's only `engine: "*"` waiver.
#
# VERIFIED TO CATCH, per row, against a real reverted fix or a deliberate mutation in an ISOLATED
# WORKTREE — never in an engine tree, since a mutation on a shared binary is a destructive write to
# another agent's measurement. R1/R5: candor-ts `cbbb05c` reverted -> ts fails exactly as java does.
# R2: the sort deleted from ts's join -> `untyped cross-package receiver,write,run`. R3: ts's dot-free
# short-circuit deleted -> all three shapes vanish from both arms. R4: java's `hasHier` emptiness test
# deleted -> the `{}` arm loses entries the absent arm keeps, the measured pre-fix collapse. R6: four
# java mutations, one per cell. R7: candor-ts `6502b56` reverted -> the κ-ledger tiebreak reorders under
# `et_EE` and the frontier's entry order flips. Every catch was engine-local: the others stayed green.
#
# FLOORS. A row with no live cell FAILS; a run with no live cell FAILS; a fixture whose PRECONDITION
# collapsed is VACUOUS, which is failing. A CLI that produced no stdout is ERROR and says
# "HARNESS/ENGINE INVOCATION — not a statement about candor" — without that guard a zero-byte jar
# printed "the frontier came back empty", which reads as a finding about candor. An engine installed but
# not responding fails the run rather than reading as absent.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_rung024.py" ] || { echo "FAIL: gen_rung024.py is missing"; exit 2; }
[ -f "$HERE/rung024-baseline.json" ] || { echo "FAIL: rung024-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P27_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_QUERY_BIN="$QUERY" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_rung024.py" --baseline "$HERE/rung024-baseline.json"
) || P27_OK=1

echo "PART 27 — the ⟨0.24⟩ rung's behaviour (SPEC §2 locale, §3.1 frontier + gate --report, §6.2 CONTRIBUTES + --class)"
if [ "$P27_OK" = 0 ]; then
  echo "  -> MATCH — every ⟨0.24⟩ clause the engines implement answers as the spec states it, outside the ratchet"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 30 — P6, SIDECAR MANIFEST FIDELITY: DEGRADING A SIDECAR MAY ONLY WIDEN                 [TIER 1]
#
# The self-differential family's structural gap, closed. P2 and P3 degrade the chained DEP REPORT; nothing
# degraded a SIDECAR, and a sidecar is not a dep report — it is a second, differently-shaped input that no
# property varied. The ⟨0.26⟩ defect lived in that gap for as long as the sidecar has existed.
#
# TWO CONJUNCTS, and between them every engine carries at least one:
#   A. CONSUMER MONOTONICITY (java, ts, rust — the engines with a `callers --include-unknown` verb)
#          frontier(full) <= frontier(full minus one key) <= frontier(no sidecar)
#      Both bounds matter and they run opposite ways. The LEFT: degrading an input may not buy CONFIDENCE.
#      The RIGHT: a PARTIAL sidecar may not out-claim an ABSENT one — the bound the defect broke, and the
#      reason the repair had to be a FORMAT change. With no sidecar the frontier falls back to a documented
#      over-listing simple-name match; with ONE key missing it went confidently silent. Removing MORE
#      information gave a SAFER answer. No consumer can patch around that alone: without a manifest it
#      cannot tell a producer's silence from its answer.
#   B. PRODUCER MANIFEST CLOSURE (java, ts, swift — the engines that WRITE a sidecar)
#          { declaring type of u : u a unit in the engine's OWN callgraph } <= sidecar key set
#      Both sides are the same engine's own output for one scan, so there is no expected-value table and
#      none may ever be added. A callgraph KEY is a unit whose body the engine walked, so its declaring
#      type was indexed — and an indexed type must carry a key. Callee VALUES are excluded (a callee may be
#      an external type never indexed), as are BRACKETED synthetic members: `Cases.<module>` is ts's ⟨0.14⟩
#      top-level initializer unit whose prefix is a FILE, and demanding a key for it would be the
#      modules-counted-as-types error. That exclusion was found by reading a callgraph after this conjunct
#      flagged a CONFORMING engine — not by anticipating it.
#
# The NOT-APPLICABLE cells are structural facts, not waivers, and are printed as such: candor-swift ships
# no `callers` verb (no conjunct A); candor-scan writes no hierarchy sidecar (no conjunct B) — which is
# exactly why rust's consumer arm matters, since every hierarchy it walks was produced by another engine.
#
# VERIFIED TO CATCH, per engine, by reverting each engine's own ⟨0.26⟩ commit and re-running: ts fails both
# conjuncts, java fails both, rust fails A, swift fails B. The rust and java runs first came back GREEN
# while reverted — both were STALE ARTIFACTS (a root `cargo build` does not rebuild candor-query; the jar
# was not deleted before `shadowJar`). Deleting the binary first is the only reliable form of that control.
#
# Note which arms fire: `minus:mod.Sub` and `minus:mod.Mid` do, `minus:mod.Base` does not — removing the
# OWNER's own key changes nothing, because the walk matches it directly before any lookup. That is the same
# fact that makes a FLAT fixture blind to this defect, showing up per-arm.
#
# FLOORS: vacuity is computed from the engine's own output (an empty `full` frontier demands nothing); a
# conjunct with no live cell on ANY engine fails the run; a reference arm producing nothing is reported as
# the harness broken rather than as engine behaviour; and the same both-ways ratchet in
# `sidecar-manifest-baseline.json`.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
# ── PRECONDITION: EVERY REGISTERED PROPERTY MUST STILL BE ABLE TO FAIL ─────────────────────────────
# "Verified to catch" was a habit applied ONCE at authoring time and never re-run, so a property that
# quietly stopped discriminating would print MATCH forever. `probe_check.py` runs each registered
# generator with `CANDOR_PROBE_FAULT` — corrupting its first live cell in the direction its own property
# forbids — and fails if the property survives. Coverage is partial and the uncovered generators are
# PRINTED with reasons rather than implied. Runs before the parts, because a suite whose instruments
# cannot fail has nothing to say about the engines.
[ -f "$HERE/probe_check.py" ] || { echo "FAIL: probe_check.py is missing"; exit 2; }
echo
( export CANDOR_SCAN_BIN="$SCAN" CANDOR_QUERY_BIN="$QUERY" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/probe_check.py" ) || { echo "conformance: a property cannot fail — see PROBE CHECK above"; rc=1; }

[ -f "$HERE/gen_sidecar_manifest.py" ] || { echo "FAIL: gen_sidecar_manifest.py is missing"; exit 2; }
[ -f "$HERE/sidecar-manifest-baseline.json" ] || { echo "FAIL: sidecar-manifest-baseline.json is missing — the ratchet cannot run, and an absent baseline must never read as 'nothing is waived'"; exit 2; }
P30_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_QUERY_BIN="$QUERY" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_sidecar_manifest.py" --baseline "$HERE/sidecar-manifest-baseline.json"
) || P30_OK=1

echo "PART 30 — sidecar manifest fidelity: degrading a sidecar may only WIDEN a disclosure (SPEC §2.2 ⟨0.26⟩, P6)"
if [ "$P30_OK" = 0 ]; then
  echo "  -> MATCH — every degraded sidecar sat between the full and absent arms, and every walked type carries a key"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# PART 31 — SPEC §2 `fs`: THE READ/WRITE REFINEMENT ANSWERS THE SAME WAY EVERYWHERE          [TIER 1]
#
# `fs` has been in §2 for a long time and was pinned by NOTHING. What that bought, measured 2026-08-04:
# candor-swift had no such field; candor-ts emitted none; candor-rust had `pub fs: Vec<String>` in the wire
# model with `fs: Vec::new()` hardcoded at the construction site — never populated, which is WORSE than
# absent, because a present-but-always-empty field says "kind undetermined" on every function forever while
# wearing a schema that implies support. Only candor-java emitted it. §2's own omit-rather-than-guess rule
# is exactly what hid all three: every empty answer looked legitimate.
#
# FIVE ROWS, and the last two ARE the property:
#   reads_only / writes_only / copies   the vocabulary agrees
#   reaches_writer -> ["write"]         kinds TRAVEL — a caller that transitively only writes IS a writer
#   mixed          -> ABSENT            one contributor with no determined kind suppresses the WHOLE field
#
# An engine can fail two opposite ways: propagate nothing (row 4 empty, under-informative) or propagate
# without the undetermined guard (row 5 non-empty — the partial claim §2 forbids in as many words).
#
# ON ITS FIRST RUN IT FOUND ALL FOUR ENGINES WRONG, in both directions. rust/ts/swift propagated nothing.
# candor-java propagated correctly but injected its FS_UNKNOWN poison only for CROSS-JAR Fs — a LOCAL call
# whose verb is mode-dependent (`new RandomAccessFile(p,"rw")`) recorded nothing, so a caller of one writer
# and one undetermined-kind callee reported fs=["write"]: "writes but never reads" about a function that
# may do both. That is the reference engine making the exact claim the spec forbids.
#
# VACUITY FLOOR: every row must carry `Fs` in `inferred` on every engine, else the cell is reported as a
# broken fixture rather than a pass. WHAT IT DOES NOT PIN: whether a producer implements `fs` AT ALL —
# absence is overloaded between "undetermined" and "unimplemented", which is a FORMAT gap needing a
# positive capability declaration in the envelope, not a conformance row.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
[ -f "$HERE/gen_fs_kind.py" ] || { echo "FAIL: gen_fs_kind.py is missing"; exit 2; }
P31_OK=0
echo
(
  export CANDOR_SCAN_BIN="$SCAN" CANDOR_QUERY_BIN="$QUERY" CANDOR_JAVA_JAR="$JAR"
  [ -n "$TS_PRESENT" ] && export CANDOR_TS="$TS_DIR"
  [ -n "$SW_PRESENT" ] && export CANDOR_SWIFT="$SW_DIR"
  python3 "$HERE/gen_fs_kind.py"
) || P31_OK=1

echo "PART 31 — SPEC §2 \`fs\`: the read/write refinement answers the same way in every engine"
if [ "$P31_OK" = 0 ]; then
  echo "  -> MATCH — kinds travel the call graph, and an undetermined contributor suppresses the field"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 32 — SPEC §4: A RULE THAT BINDS NOTHING IS DISCLOSED, NEVER SCORED AS SATISFIED      [TIER 1]
#
# THE DEFECT, measured 2026-08-05 in candor-java, candor-rust and candor-ts (candor-swift had already
# been fixed): a package `app.orders` performing `Fs`, and
#
#     deny Fs orders   -> exit 1   the violation
#     deny Fs ordrs    -> exit 0   IN SILENCE
#
# A one-character typo in a layer name is a permanently green gate, and `unverified` then reports the
# layer as "PROVABLY clean". The asymmetry is the tell: a typo'd EFFECT token already exits 2 naming the
# accepted vocabulary, while a typo'd LAYER token binds nothing and passes. Same file, same rule,
# opposite treatment — and the passing half is the one that fails open.
#
# THE REMEDY IS DISCLOSURE, NOT REFUSAL, so this part pins BOTH halves. Exit 2 would be wrong: a
# zero-match rule is legitimate when one policy is shared across repositories and a layer exists in only
# some of them, so a refusing engine would make a shared policy unusable.
#
# THREE ROWS, and the second is the one that stops this becoming a new way to fail a build:
#   (a) a scope that matches nothing        -> DISCLOSED on stderr
#   (b) …and the exit code is UNCHANGED     -> compared against the same run with the rule removed
#   (c) a SCOPELESS `deny` is never reported -> it binds every function by construction, so it can never
#                                              be this kind of typo; reporting it would be a false alarm
#                                              on the commonest rule in the vocabulary
#
# FIXTURE-INDEPENDENT BY CONSTRUCTION: `zzz_no_such_layer` cannot match in any language, so no row
# depends on how an engine qualifies names. Row (c) doubles as the VACUITY FLOOR — it asserts the
# scopeless rule still GATES (exit 1), so a fixture that stopped violating would fail the part rather
# than passing it silently.
# ─────────────────────────────────────────────────────────────────────────────────────────────────
echo
echo "[32] ZERO-MATCH RULE DISCLOSURE  (SPEC §4 — a rule that bound nothing cannot have caught anything)"
ZM_OK=0
ZMW="$W/zeromatch"; mkdir -p "$ZMW"
printf 'deny Fs zzz_no_such_layer\n' > "$ZMW/miss.policy"   # (a)+(b): binds nothing, in every language
printf 'deny Fs\n'                   > "$ZMW/hit.policy"    # (c): scopeless — binds everything
zm_probe() { # $1 label ; then the scan command WITHOUT a --policy flag
  local label=$1; shift
  local cmd=( "$@" ) miss_out miss_rc hit_out hit_rc base_rc bad=0
  miss_out=$( "${cmd[@]}" --policy "$ZMW/miss.policy" 2>&1 >/dev/null ); miss_rc=$?
  hit_out=$(  "${cmd[@]}" --policy "$ZMW/hit.policy"  2>&1 >/dev/null ); hit_rc=$?
  "${cmd[@]}" >/dev/null 2>&1; base_rc=$?          # the same run with NO policy at all
  case "$miss_out" in
    *"matched NO function"*) : ;;
    *) echo "     FAIL $label: a rule binding NO function was not disclosed — a typo'd layer name is a green gate"; bad=1;;
  esac
  [ "$miss_rc" = "$base_rc" ] || { echo "     FAIL $label: the zero-match disclosure CHANGED the verdict (exit $miss_rc vs $base_rc with no policy)"; bad=1; }
  case "$hit_out" in
    *"matched NO function"*) echo "     FAIL $label: a SCOPELESS deny was reported as zero-match — it binds every function"; bad=1;;
  esac
  [ "$hit_rc" = 1 ] || { echo "     FAIL $label: the fixture no longer violates a scopeless \`deny Fs\` (exit $hit_rc) — this part would be vacuous"; bad=1; }
  [ "$bad" = 0 ] && { echo "  $label disclosed=yes verdict-unchanged=yes scopeless-exempt=yes"; return 0; }
  return 1
}
zm_probe "candor-java " java -jar "$JAR" "$W/g_java" || ZM_OK=1
zm_probe "candor-scan " "$SCAN" "$GDIR/rust" --out "$ZMW/r" || ZM_OK=1
[ -n "$TS_OK" ] && { zm_probe "candor-ts   " node "$TS_DIR/scan.mjs" "$GDIR/ts" --out "$ZMW/t" || ZM_OK=1; }
[ -n "$SW_OK" ] && [ -x "$SW_BIN" ] && { zm_probe "candor-swift" "$SW_BIN" "$GDIR/swift" --out "$ZMW/s" || ZM_OK=1; }
# THE `gate --report` ROUTE TOO. §4's MUST carries no route qualifier, and a differential found java and
# swift disclosing there while rust and ts stayed silent — so on the SUPPLY-CHAIN gate, the surface a
# consumer points at a report someone else produced, a typo'd layer was still scored as satisfied by half
# the family. PART 32 pinned the scan route only, which is why the split survived it.
zm_gate_probe() { # $1 label ; $2 report path ; then the gate command (…gate --report <r> --policy <p>)
  local label=$1 rep=$2; shift 2
  [ -f "$rep" ] || { echo "     FAIL $label: no report at $rep — the gate row would be vacuous"; return 1; }
  local out; out=$( "$@" --report "$rep" --policy "$ZMW/miss.policy" 2>&1 >/dev/null )
  case "$out" in
    *"matched NO function"*) echo "  $label gate --report: disclosed"; return 0 ;;
    *) echo "     FAIL $label: gate --report scored a zero-match rule as satisfied, in silence"; return 1 ;;
  esac
}
ZMR="$ZMW/reports"; mkdir -p "$ZMR"
java -jar "$JAR" "$W/g_java" --json "$ZMR/java.json" >/dev/null 2>&1
zm_gate_probe "candor-java " "$ZMR/java.json" java -jar "$JAR" gate || ZM_OK=1
"$SCAN" "$GDIR/rust" --out "$ZMR/rust" >/dev/null 2>&1
zm_gate_probe "candor-scan " "$(ls "$ZMR"/rust*.json 2>/dev/null | grep -vE 'callgraph|hierarchy|locs' | head -1)" "$QUERY" gate || ZM_OK=1
if [ -n "$TS_OK" ]; then
  node "$TS_DIR/scan.mjs" "$GDIR/ts" --out "$ZMR/ts" >/dev/null 2>&1
  zm_gate_probe "candor-ts   " "$(ls "$ZMR"/ts*.json 2>/dev/null | grep -vE 'callgraph|hierarchy|locs' | head -1)" node "$TS_DIR/query.mjs" gate || ZM_OK=1
fi
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  "$SW_BIN" "$GDIR/swift" --out "$ZMR/sw" >/dev/null 2>&1
  zm_gate_probe "candor-swift" "$(ls "$ZMR"/sw*.json 2>/dev/null | grep -vE 'callgraph|hierarchy|locs' | head -1)" "$SW_BIN" gate || ZM_OK=1
fi
echo "PART 32 — SPEC §4: a rule whose scope binds no function is disclosed, and the verdict is untouched"
if [ "$ZM_OK" = 0 ]; then
  echo "  -> MATCH — every engine discloses a zero-match rule, exempts a scopeless deny, and leaves the exit code alone"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

# ====================================================================================================
# PART 33 — SPEC §3.4 `engine`: THE PIN IS ENFORCED THE SAME WAY IN EVERY ENGINE            [TIER 1]
#
# PART 13b pins that `engine` is RECOGNIZED (never reported unknown, never silently dropped). That is a
# vocabulary property and it passes on an engine that does nothing with the key. This pins the BEHAVIOUR.
#
# WHY IT MATTERS THAT ALL FIVE AGREE: one `.candor/config` serves a polyglot repo, so a pin the operator
# writes once must mean the same thing to every engine that reads it. An engine enforcing while another
# silently ignores is the shape that makes an operator trust a guard that is only half on.
#
# FOUR ROWS, and the two that must NOT fail are the design:
#   matching pin        -> exit UNCHANGED and SILENT   (a pin that holds costs nothing)
#   mismatched pin      -> exit 2                       (UNEVALUABLE — never 1, which means "violation")
#   unreadable pin      -> exit 2                       (`engine latest`: skipping it would hand the
#                                                        enforcement site "absent", and absent PASSES)
#   pin for ANOTHER impl-> exit UNCHANGED               (the family versions as a LADDER; one engine may
#                                                        lead a rung, so a qualified pin is not ours)
#
# The mismatched/unreadable rows must be exit 2 SPECIFICALLY: a machine consumer that separates 1 from 2
# must not read "I could not trust this result" as "your code broke a rule".
# ─────────────────────────────────────────────────────────────────────────────────────────────────
echo
echo "[33] ENGINE PIN ENFORCEMENT  (SPEC §3.4 — one config, one meaning, in every engine)"
EP_OK=0
EPW="$W/enginepin"; mkdir -p "$EPW"
ep_probe() { # $1 label ; $2 impl token ; $3 the engine's own release version ; then the scan command (target LAST)
  local label=$1 impl=$2 running=$3; shift 3
  local cmd=( "$@" ) cfgdir bad=0 rc base
  cfgdir="${cmd[$(( ${#cmd[@]} - 1 ))]}"
  mkdir -p "$cfgdir/.candor"
  : > "$cfgdir/.candor/config";           "${cmd[@]}" >/dev/null 2>&1; base=$?
  printf 'engine v%s\n' "$running" > "$cfgdir/.candor/config"
  local out; out=$( "${cmd[@]}" 2>&1 >/dev/null ); rc=$?
  [ "$rc" = "$base" ] || { echo "     FAIL $label: a MATCHING pin changed the exit code ($rc vs $base with no pin)"; bad=1; }
  case "$out" in *"pins engine"*) echo "     FAIL $label: a matching pin said something — a pin that holds must cost nothing"; bad=1;; esac
  printf 'engine v0.0.1\n' > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = 2 ] || { echo "     FAIL $label: a MISMATCHED pin exited $rc, not 2 (unevaluable, never 1)"; bad=1; }
  printf 'engine latest\n' > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = 2 ] || { echo "     FAIL $label: an UNREADABLE pin exited $rc, not 2 — skipping it hands the check 'absent', and absent PASSES"; bad=1; }
  # A qualified pin for an implementation this engine is NOT. `agents` is used for the four code
  # engines and `java` for candor-agents, so no row is ever self-referential.
  local other=java; [ "$impl" = java ] && other=agents
  printf 'engine %s v0.0.1\n' "$other" > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = "$base" ] || { echo "     FAIL $label: a pin qualified for \`$other\` changed this engine's exit ($rc vs $base)"; bad=1; }
  # …AND A MALFORMED LINE QUALIFIED FOR ANOTHER IMPLEMENTATION IS STILL NOT OURS. A differential split the
  # family three ways on `engine swift 0.99.0 junk`: one engine ignored it, three killed their OWN run over
  # a line naming an engine they are not, and the engine it names refused (correctly). SPEC §3.4 rules the
  # skip WHOLE-LINE — otherwise one typo is a family-wide outage.
  printf 'engine %s 0.99.0 junk\n' "$other" > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = "$base" ] || { echo "     FAIL $label: a JUNKED line qualified for \`$other\` killed this engine's run ($rc vs $base)"; bad=1; }
  # A MALFORMED UNQUALIFIED LINE IS STILL YOURS TO READ, even beside a qualified pin that applies. The
  # reference engine was the sole non-conformer here — `engine 0.26.0 oops` plus `engine <impl> <good>`
  # exited 0 in java and 2 in the other four, because its precedence returned the qualified pin without
  # ever looking at the unreadable line. Precedence decides which VERSION applies, not whether a line you
  # were supposed to read parses.
  # BOTH SPELLINGS. The row shipped with only the two-token form, which every engine caught by ARITY —
  # so it was green five-way while the ONE-TOKEN form (`engine garbage`) split the family four against
  # java, silently. A row that pins one spelling of a rule pins one spelling of a rule; this is the
  # split-invariance lesson (44 fixtures, one spelling each) arriving in a hand-written part.
  for junk in "0.26.0 oops" "garbage"; do
    printf 'engine %s\nengine %s v%s\n' "$junk" "$impl" "$running" > "$cfgdir/.candor/config"
    "${cmd[@]}" >/dev/null 2>&1; rc=$?
    [ "$rc" = 2 ] || { echo "     FAIL $label: unreadable UNQUALIFIED line \`engine $junk\` hidden by a qualified pin (exit $rc, want 2)"; bad=1; }
  done
  # AT MOST ONE LEADING `v`. Two engines stripped every one, so `vv0.27.0` was a valid pin to them and
  # MALFORMED to the other three — the family disagreeing on what counts as a version.
  printf 'engine vv%s\n' "$running" > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = 2 ] || { echo "     FAIL $label: \`vv$running\` was accepted as a version (exit $rc, want 2)"; bad=1; }
  # CRLF. `\r` is whitespace, not part of the version — one engine refused a MATCHING pin on a repository
  # checked out on Windows, which is "same file, two meanings" verbatim.
  printf 'engine v%s\r\n' "$running" > "$cfgdir/.candor/config"
  "${cmd[@]}" >/dev/null 2>&1; rc=$?
  [ "$rc" = "$base" ] || { echo "     FAIL $label: a CRLF config broke a MATCHING pin (exit $rc vs $base)"; bad=1; }
  # THE VACUITY FLOOR. Every row above compares against \$base, so an engine that ALWAYS exits 2 would
  # pass the whole part. PART 32 got a floor; this one did not until a review pointed it out.
  [ "$base" != 2 ] || { echo "     FAIL $label: the no-pin baseline is itself exit 2 — every row here would be vacuous"; bad=1; }
  rm -f "$cfgdir/.candor/config"
  [ "$bad" = 0 ] && { echo "  $label match=silent mismatch=2 unreadable=2 other-impl=ignored"; return 0; }
  return 1
}
EP_JV=$(java -jar "$JAR" --version 2>/dev/null | head -1 | awk '{print $2}')
EP_RV=$("$SCAN" --version 2>/dev/null | head -1 | awk '{print $2}')
mkdir -p "$EPW/java" "$EPW/rust"
cp -r "$GDIR/rust/." "$EPW/rust/" 2>/dev/null
javac -d "$EPW/java" $(find "$GDIR/java" -name '*.java') 2>/dev/null
ep_probe "candor-java " java "$EP_JV" java -jar "$JAR" "$EPW/java" || EP_OK=1
ep_probe "candor-scan " rust "$EP_RV" "$SCAN" "$EPW/rust" || EP_OK=1
if [ -n "$TS_OK" ]; then
  EP_TV=$(node "$TS_DIR/scan.mjs" --version 2>/dev/null | head -1 | awk '{print $2}')
  mkdir -p "$EPW/ts"; cp -r "$GDIR/ts/." "$EPW/ts/" 2>/dev/null
  ep_probe "candor-ts   " ts "$EP_TV" node "$TS_DIR/scan.mjs" "$EPW/ts" || EP_OK=1
fi
if [ -n "$SW_OK" ] && [ -x "$SW_BIN" ]; then
  EP_SV=$("$SW_BIN" --version 2>/dev/null | head -1 | awk '{print $2}')
  mkdir -p "$EPW/swift"; cp -r "$GDIR/swift/." "$EPW/swift/" 2>/dev/null
  ep_probe "candor-swift" swift "$EP_SV" "$SW_BIN" "$EPW/swift" || EP_OK=1
fi
# candor-agents IS PROBED TOO, and it was not: the part's headline says "every engine" and the spec
# CHANGELOG says "ALL FIVE now enforce it (PART 33 pins that)" — a claim the suite did not test. agents
# was also one of the two engines whose version normaliser accepted `vv0.27.0`, so the row written about
# that defect never ran for one of the engines that had it. It is a domain engine over a `.claude/` fleet
# rather than code, so it gets a fleet fixture; the probe is otherwise identical.
# A MISSING candor-agents is REPORTED, never a silent skip. The row was guarded by a bare `if` that
# vanished when the repo was absent — which is exactly what happened in candor-spec CI, where the
# checkout did not exist, so PART 33 printed "every engine" over four. Absence is now named.
if [ ! -d "$HERE/../../candor-agents" ]; then
  echo "  · candor-agents NOT CHECKED (repo absent) — this row did not run; PART 33 covers 4 engines here"
  [ -z "${CONFORMANCE_REQUIRE_ALL:-}" ] || { echo "     FAIL candor-agents: required by CONFORMANCE_REQUIRE_ALL"; EP_OK=1; }
elif command -v python3 >/dev/null 2>&1; then
  EPA="$W/enginepin/agents"; mkdir -p "$EPA/.claude"
  EP_AV=$(python3 -c "import sys; sys.path.insert(0,'$HERE/../../candor-agents'); from candor_agents.scan import RELEASE; print(RELEASE)" 2>/dev/null)
  if [ -n "$EP_AV" ]; then
    ep_probe "candor-agents" agents "$EP_AV" python3 -c "
import sys; sys.path.insert(0,'$HERE/../../candor-agents')
from candor_agents.scan import load_candor_config
try: load_candor_config(sys.argv[1])
except SystemExit as e: sys.exit(e.code)
" "$EPA" || EP_OK=1
  else
    echo "     FAIL candor-agents: could not read its RELEASE — the row would be vacuous"; EP_OK=1
  fi
fi
echo "PART 33 — SPEC §3.4: the engine pin is enforced identically in every engine"
if [ "$EP_OK" = 0 ]; then
  echo "  -> MATCH — a holding pin is silent, a broken one is exit 2 (never 1), another impl's pin is not ours"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

echo
[ "$rc" -eq 0 ] \
  && echo "conformance: OK (effect sets + policy verdict + rewire + policy-DSL grammar + policy-matching + net destination-class + completeness-manifest + tables extraction + coverage ledger + surface-best-find + surface tour + tour robustness + corrupt-report loudness + test-exclusion + salience floor + query shapes + gains origin + Llm host-literal + Llm model-SDK surface + top-level initializer units + const-indirected hosts + literal-head hosts + coverage envelope + --agents + generative differential + gate-masking differential + unknownWhy vocabulary + dispatch frontier + containment + gate-verdict + fix-gate remedy + .candor/config + chaining + stale-baseline + callgraph-aware guard (pure→effectful + Unknown-advisory) + deny-Unknown/forbid applied + query grammar + cross-package interface dispatch + initializer edge across the scan boundary + implicit stringification across the scan boundary + could-not-form-a-key discloses + chained dep-join surface completeness agree across the engines + the model's own Lemma 2 holds over the full lattice + each engine agrees with ITSELF across the scan-boundary split + chaining a dep report twice answers as chaining it once + a dep report an engine will not trust only ADDS hedges + adding a call to a function only ever ADDS to what its report says + a real violation survives an incomplete scan on EVERY gate + the ⟨0.24⟩ rung's behaviour: CONTRIBUTES, the viaDispatchOn literal, the dot-free frontier arm, the sidecar triple, --class dynamic, gate --report and locale-independence + degrading a sidecar may only WIDEN a disclosure, and every type an engine WALKED carries a key + the fs read/write refinement answers the same way in every engine + a rule that binds nothing is disclosed rather than scored as satisfied + the engine pin is enforced identically everywhere)" \
  || echo "conformance: FAILED"

# If we failed, say WHICH KIND of failure it was. A checker that crashed leaves a Python traceback on
# stderr; a genuine divergence does not. Without this the two are indistinguishable in the summary, and an
# infrastructure error gets investigated as an engine disagreement (or, worse, re-run until it passes).
if [ "$rc" -ne 0 ]; then
  sync 2>/dev/null || true
  if grep -q "^Traceback (most recent call last)" "$W/harness-stderr.log" 2>/dev/null; then
    echo
    echo "conformance: THE HARNESS ITSELF ERRORED — this is NOT an engine disagreement."
    echo "  A checker raised rather than reporting a divergence, so the FAILED above is not evidence"
    echo "  about the engines. Do NOT re-run until it passes; fix the cause. Most likely: a report file"
    echo "  was read while a rebuild was rewriting it, or a checker references a file that was not"
    echo "  produced. The exception:"
    # The exception line is the LAST line of a traceback block and is the only part that says what
    # actually went wrong — the intermediate frames are usually inside json/ or the stdlib.
    grep -E "^[A-Za-z_][A-Za-z_.]*(Error|Exception|Interrupt)\b" "$W/harness-stderr.log" 2>/dev/null \
      | head -1 | sed 's/^/    /'
  fi
fi
exit "$rc"
