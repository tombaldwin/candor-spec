#!/usr/bin/env bash
# Cross-impl conformance differential. Runs BOTH candor implementations on equivalent fixtures and asserts
# they agree — first on the EFFECT SETS they infer, then on the POLICY VERDICT they reach. The two
# independent engines (Rust syntactic scan + JVM bytecode) sharing one spec is candor's defining moat over
# a per-language ruleset (CodeQL/Semgrep/ArchUnit): not just "we have rules for both languages", but a
# MACHINE-CHECKED guarantee that the same effect contract AND the same `deny`/`pure` gate mean the same
# thing in each. A DIVERGE row is a bug in one engine.
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
  JAR="$(ls "$CANDOR_JAVA"/build/libs/*-all.jar 2>/dev/null | head -1)"
fi
[ -x "$SCAN" ]  || { echo "FAIL: no candor-scan at $SCAN"; exit 2; }
[ -x "$QUERY" ] || { echo "FAIL: no candor-query at $QUERY"; exit 2; }
[ -f "$JAR" ]   || { echo "FAIL: no candor-java jar at $JAR"; exit 2; }

# The optional THIRD engine (candor-ts). When present, it joins the grammar (4), query-shape (5) and
# effect-set (6) differentials; when absent those parts run two-way / Part 6 skips loudly.
TS_DIR="${CANDOR_TS:-$HERE/../../candor-ts}"
TS_OK=""
if command -v node >/dev/null 2>&1 && [ -f "$TS_DIR/scan.mjs" ]; then
  ( cd "$TS_DIR" && [ -d node_modules ] || npm install --no-fund --no-audit >/dev/null 2>&1 )
  ( cd "$TS_DIR" && node scan.mjs Cases.ts "$W/ts" 2>/dev/null )
  [ -f "$W/ts.json" ] && TS_OK=1
fi

rc=0

# ====================================================================================================
# PART 1 — effect-set differential (each engine vs the spec, and vs each other)
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

# ====================================================================================================
# PART 2 — policy-verdict differential: the same `deny Net api` policy, the same `whatif`, same verdict?
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
# PART 3 — rewire-verdict differential: a function drops a call (de-wiring). Do both engines flag the
# SAME dropped edge? Completes cross-impl parity for the newest commands (effects + whatif + rewire).
# ====================================================================================================
cp -r "$HERE/rewire" "$W/rewire"
"$SCAN" "$W/rewire/rust/baseline" >/dev/null 2>&1 || { echo "FAIL: scan errored on rewire/rust/baseline"; exit 2; }
"$SCAN" "$W/rewire/rust/gamed" >/dev/null 2>&1 || { echo "FAIL: scan errored on rewire/rust/gamed"; exit 2; }
"$QUERY" rewire "$W/rewire/rust/gamed/.candor/report" "$W/rewire/rust/baseline/.candor/report" 1 > "$W/rust_rw.json" 2>/dev/null
javac -d "$W/rwb" $(find "$W/rewire/java/baseline" -name '*.java') 2>/dev/null || { echo "FAIL: javac on rewire/java/baseline"; exit 2; }
javac -d "$W/rwg" $(find "$W/rewire/java/gamed" -name '*.java') 2>/dev/null || { echo "FAIL: javac on rewire/java/gamed"; exit 2; }
java -jar "$JAR" "$W/rwb" --json "$W/rwb.json" >/dev/null 2>&1
java -jar "$JAR" "$W/rwg" --json "$W/rwg.json" >/dev/null 2>&1
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
# PART 4 — policy-DSL grammar differential: parse the SAME CANDOR_POLICY battery with both engines and
# assert identical parsed rule sets. The executable form of SPEC §6.2 — the gate's grammar
# (deny/pure/allow/forbid, the Unknown-deny, scope/literal matching) meaning the same thing in each.
# A per-language ruleset has no shared grammar to diff; candor's single policy file MUST parse alike.
# ====================================================================================================
POL_BATTERY="$HERE/policydsl/policy.txt"
"$QUERY" parsepolicy "$POL_BATTERY" > "$W/rust_pol.json" 2>/dev/null
java -jar "$JAR" parsepolicy "$POL_BATTERY" > "$W/java_pol.json" 2>/dev/null
if [ -n "$TS_OK" ] && [ -f "$TS_DIR/query.mjs" ]; then
  node "$TS_DIR/query.mjs" parsepolicy "$POL_BATTERY" > "$W/ts_pol.json" 2>/dev/null
fi

python3 - "$W/rust_pol.json" "$W/java_pol.json" "$W/ts_pol.json" <<'PY' || rc=1
import json, os, sys
def norm(p):
    d = json.load(open(p))
    deny   = sorted((tuple(sorted(r["effects"])), r["scope"]) for r in d["deny"])
    allow  = sorted((r["effect"], r["scope"], tuple(sorted(r["values"]))) for r in d["allow"])
    forbid = sorted((r["from"], r["to"]) for r in d["forbid"])
    return deny, allow, forbid
r, j = norm(sys.argv[1]), norm(sys.argv[2])
t = norm(sys.argv[3]) if os.path.exists(sys.argv[3]) else None
print("\n[4] POLICY-DSL grammar differential  (SPEC §6.2 — parse the same battery in every engine)")
print(f"  candor(rust): {len(r[0])} deny, {len(r[1])} allow, {len(r[2])} forbid")
print(f"  candor-java : {len(j[0])} deny, {len(j[1])} allow, {len(j[2])} forbid")
if t is not None:
    print(f"  candor-ts   : {len(t[0])} deny, {len(t[1])} allow, {len(t[2])} forbid")
match = r == j and (t is None or r == t)
n = "two" if t is None else "all three"
print("  -> " + (f"MATCH — {n} engines parse the deny/pure/allow/forbid grammar identically"
                 if match else "DIVERGE — the engines parse the policy DSL differently"))
if not match:
    for name, idx in (("deny", 0), ("allow", 1), ("forbid", 2)):
        sets = {"rust": r[idx], "java": j[idx]} | ({"ts": t[idx]} if t is not None else {})
        if len({repr(v) for v in sets.values()}) > 1:
            for eng, v in sets.items():
                print(f"     {name} {eng}={v}")
sys.exit(0 if match else 1)
PY

# ====================================================================================================
# PART 5 — read-only query SHAPE differential: run show/where/callers/map on both engines and assert the
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
java -jar "$JAR" show    "$W/java.json" net_connect --json     > "$W/j_show.json"    2>/dev/null
java -jar "$JAR" where   "$W/java.json" Fs --json              > "$W/j_where.json"   2>/dev/null
java -jar "$JAR" callers "$W/java.json" transitive_leaf --json > "$W/j_callers.json" 2>/dev/null
java -jar "$JAR" map     "$W/java.json" --json                 > "$W/j_map.json"     2>/dev/null
java -jar "$JAR" diff    "$W/java.json" "$W/java.json" --json  > "$W/j_diff.json"    2>/dev/null
"$QUERY" show "$RUST_PREFIX" act 1  > "$W/r_ladder_act.json"  2>/dev/null
"$QUERY" show "$RUST_PREFIX" nion 1 > "$W/r_ladder_nion.json" 2>/dev/null
java -jar "$JAR" show "$W/java.json" act --json  > "$W/j_ladder_act.json"  2>/dev/null
java -jar "$JAR" show "$W/java.json" nion --json > "$W/j_ladder_nion.json" 2>/dev/null
# segment-suffix at a NESTED-TYPE boundary: `Svc::act`/`Svc.act` must resolve to exactly the one
# inner-type method (Rust `::Svc::act`, JVM `Cases$Svc.act` — the `$` boundary), never a substring cousin.
"$QUERY" show "$RUST_PREFIX" Svc::act 1 > "$W/r_ladder_svc.json" 2>/dev/null
java -jar "$JAR" show "$W/java.json" Svc.act --json > "$W/j_ladder_svc.json" 2>/dev/null
if [ -n "$TS_OK" ] && [ -f "$TS_DIR/query.mjs" ]; then
  TSQ() { node "$TS_DIR/query.mjs" "$@"; }
  TSQ show    "$W/ts" net_connect 1     > "$W/t_show.json"    2>/dev/null
  TSQ where   "$W/ts" Fs 1              > "$W/t_where.json"   2>/dev/null
  TSQ callers "$W/ts" transitive_leaf 1 > "$W/t_callers.json" 2>/dev/null
  TSQ map     "$W/ts" 1                 > "$W/t_map.json"     2>/dev/null
  TSQ show    "$W/ts" act 1             > "$W/t_ladder_act.json"  2>/dev/null
  TSQ show    "$W/ts" nion 1            > "$W/t_ladder_nion.json" 2>/dev/null
  TSQ show    "$W/ts" Svc.act 1         > "$W/t_ladder_svc.json"  2>/dev/null
fi

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
check("diff", isinstance(rd, dict) and isinstance(jd, dict)
              and rd.get("changes") == [] and jd.get("changes") == [])
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
# PART 6 — the THIRD engine (candor-ts): the derivability proof, run live. The TS slice was written
# from the spec documents alone; here it answers the SAME Part-1 oracle as the Rust and JVM engines.
# Optional: skips (loudly) when the engine or node isn't available, so the suite never blocks on it.
# Locally, a sibling ../candor-ts checkout is used; in CI the workflow checks it out.
# ====================================================================================================
if [ -n "$TS_OK" ]; then
  if [ -f "$W/ts.json" ]; then
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
    echo; echo "[6] THIRD ENGINE (candor-ts): scan produced no report — FAIL"; rc=1
  fi
else
  echo; echo "[6] THIRD ENGINE (candor-ts): not present (set CANDOR_TS or clone ../candor-ts) — SKIPPED"
fi

echo
[ "$rc" -eq 0 ] \
  && echo "conformance: OK (effect sets + policy verdict + rewire + policy-DSL grammar + query shapes agree across the engines)" \
  || echo "conformance: FAILED"
exit "$rc"
