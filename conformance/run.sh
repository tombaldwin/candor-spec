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
# grammar, the literal surfaces, the κ ledger, config fail-closed sourcing, chaining, and the baseline
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
    deny   = sorted((tuple(sorted(r["effects"])), r["scope"]) for r in d["deny"])
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
  printf 'import Network\nfunc h() { _ = NWConnection(host: "api.example.com", port: 8080, using: .tcp) }\n' > "$W/nh/swift/cases.swift"
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
# PART 4c — κ-coverage ledger differential (SPEC §7 item 14): every engine must NAME an unlisted   [TIER 1]
# external package the scanned code demonstrably calls ("κ doesn't know …"), and must NOT name the
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
print("\n[4c] κ-COVERAGE LEDGER differential  (SPEC §7 item 14 — unlisted-but-called packages are NAMED)")
ok = True
def check(name, out, pkg, frontier):
    global ok
    named = "κ doesn't know" in out and pkg in out
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
  TSQ path    "$W/ts" transitive_caller Fs > "$W/t_path.json"     2>/dev/null
  TSQ blindspots "$W/ts"                   > "$W/t_blindspots.json" 2>/dev/null
  TSQ reachable "$W/ts"                    > "$W/t_reachable.json" 2>/dev/null
fi

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
# DISPATCH-FRONTIER differential (SPEC §3.1/§4 ⟨0.7⟩) — `callers --include-unknown`. One shared scenario
# (Base.op with >fan-out impls, one reaching Sink.touch; a Dispatcher dispatching Base.op) across the
# class/protocol engines (java, ts, swift; rust has no dispatch: → empty frontier, excluded). Asserts all
# present engines AGREE: the dispatcher is disclosed in possibleViaUnknownDispatch via dispatch on `op`
# (resolved against the hierarchy sidecar), with Impl7.op confirmed. Makes the frontier a verified
# contract, not just a per-engine feature (the [10] check pins only the vocabulary + dispatch shape).
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
echo "[10] unknownWhy VOCABULARY (canonical kinds + dispatch:owner.member, SPEC §4 ⟨0.7⟩):"
python3 - "$RUST_REPORT" "$W/java.json" "${TS_OK:+$W/ts.json}" "${SW_REPORT:-}" <<'PY' || rc=1
import json, os, sys
CANON = {"reflect", "native", "dispatch", "callback"}
# Known migration kinds (SPEC §4 ⟨0.7⟩): an engine MAY still emit these while it reconciles its reasons
# onto the canonical four (MODEL.md tracks candor-java's task-handoff/indy). They WARN — visible, not
# silently allowed — but do NOT fail the suite, so a not-yet-reconciled engine is surfaced without being
# falsely red. Any OTHER off-vocabulary kind is a hard DIVERGE (the old `dispatch-broad:`/`call:`/… drift).
MIGRATION = {"task-handoff", "indy"}
labels = ["rust", "java", "ts", "swift"]
fails = 0; warns = 0; seen = {}; total = 0
for label, path in zip(labels, sys.argv[1:5]):
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
            kind = w.split(":", 1)[0]
            seen.setdefault(label, set()).add(kind)
            if kind in MIGRATION:
                print(f"  WARN    [{label}] migration unknownWhy kind (not yet reconciled, SPEC §4): {w!r}  (fn {f.get('fn')})"); warns += 1
            elif kind not in CANON:
                print(f"  DIVERGE [{label}] non-canonical unknownWhy kind: {w!r}  (fn {f.get('fn')})"); fails += 1
            elif kind == "dispatch":
                detail = w.split(":", 1)[1] if ":" in w else ""
                if "." not in detail:
                    print(f"  DIVERGE [{label}] dispatch: must be owner.member: {w!r}  (fn {f.get('fn')})"); fails += 1
for label in labels:
    if label in seen:
        print(f"  {label}: kinds = {sorted(seen[label])}")
suffix = "OK" if fails == 0 else f"{fails} violation(s)"
if warns: suffix += f", {warns} migration warning(s)"
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
# REPORT mode (the diagnostic)
java -jar "$JAR" containment "$W/cont_jcur.json" --json > "$W/cont_jrep.json" 2>/dev/null
"$QUERY" containment "$W/containment/rust/current/.candor/report" --json > "$W/cont_rrep.json" 2>/dev/null
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
def norm(path):
    d = json.load(open(path))
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
for f in fails:
    print(f"     FAIL {f}")
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
# PART 12d — GATE AUTO-DISCLOSURE differential (spec 0.9 — candor-scan/java/ts/swift 0.9.0):   [TIER 2]
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
# PART 14 — CHAINING differential (SPEC §2 `CANDOR_DEPS` — 0.4 MUSTs, previously unpinned): the same   [TIER 1]
# dep+app pair per language, scanned app-only with the dep's report chained. Three pinned behaviors:
# (a) JOIN-INHERIT — the app fn inherits the dep fn's effects AND its literal surface (Net + host);
# (b) STALE-DOWNGRADE — a dep report whose producing version was doctored is not trusted: the call
#     downgrades to `Unknown`, never a stale Net claim (§2.1 at the join);
# (c) EMPTY-REPORT COVERAGE — an all-pure dep's EMPTY report is a purity CLAIM: the call reads pure
#     and the κ ledger must NOT name the covered package (§2 rule 3).
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
    covered = not ("κ doesn't know" in err_empty and pkg in err_empty)
    good = join and down and pure and covered
    detail = "".join([
        "" if join else " (join: app fn must inherit exactly {Net} + the host literal)",
        "" if down else " (stale: a doctored producing version must downgrade to Unknown, not keep Net)",
        "" if pure else " (empty: an all-pure dep report is a purity claim — the call must read pure)",
        "" if covered else f" (empty: the κ ledger must NOT name {pkg} — a loaded report COVERS its package, §2 rule 3)"])
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

if [ "$P17_OK" = 0 ]; then
  echo "  -> MATCH — every engine drives a query the same way: discovery ≡ --report ≡ OLD positional, --json selects, --policy is a flag"
else
  echo "  -> DIVERGE — see FAIL lines"; rc=1
fi

echo
[ "$rc" -eq 0 ] \
  && echo "conformance: OK (effect sets + policy verdict + rewire + policy-DSL grammar + policy-matching + tables extraction + κ ledger + query shapes + --agents + generative differential + gate-masking differential + unknownWhy vocabulary + dispatch frontier + containment + gate-verdict + fix-gate remedy + .candor/config + chaining + stale-baseline + deny-Unknown/forbid applied + query grammar agree across the engines)" \
  || echo "conformance: FAILED"
exit "$rc"
