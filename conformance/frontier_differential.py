#!/usr/bin/env python3
"""Cross-engine DISPATCH-FRONTIER differential (SPEC §3.1/§4 ⟨0.7⟩, `callers --include-unknown`).

The frontier is a class/protocol-dispatch concept, so this covers the three class/protocol engines
(java, ts, swift); rust has no `dispatch:` (its indeterminacy is callback/native) — its frontier is
empty by language model and it is excluded here.

One shared scenario per engine: a `Base.op()` with >CHA_FANOUT_LIMIT (13) implementors, exactly one of
which (`Impl7.op`) reaches an effectful sink `Sink.touch`; a `Dispatcher` that dispatches `Base.op` on a
`Base`-typed value. Because the dispatch is over too many impls, each engine discloses it as
`dispatch:<Base>.op` (Unknown) and drops the edges — so the dispatcher is NOT a confirmed caller of
`Sink.touch`. `callers Sink.touch --include-unknown` must therefore surface the dispatcher in
`possibleViaUnknownDispatch` (via dispatch on `op`), resolved against the hierarchy sidecar — and all
three engines must AGREE on that (the dispatcher, via `op`, the one frontier entry). Confirmed callers
include `Impl7.op`. This is what makes the frontier a verified contract, not just a per-engine feature.
"""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
def envdir(v, d): return os.environ.get(v, os.path.normpath(os.path.join(HERE, d)))
CANDOR       = envdir("CANDOR",       "../../candor-rust")
CANDOR_JAVA  = envdir("CANDOR_JAVA",  "../../candor-java")
CANDOR_TS    = envdir("CANDOR_TS",    "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")
def run(cmd, **kw): return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
def newest(d, suf):
    try: c = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(suf)]
    except FileNotFoundError: return None
    return max(c, key=os.path.getmtime) if c else None

N = 13  # > CHA_FANOUT_LIMIT (12), so Base.op dispatch is bounded -> dispatch:Base.op Unknown
REACH = 7  # the one implementor whose op() reaches the sink

def java_src():
    impls = "\n".join(
        f"class Impl{i} implements Base {{ public void op() {{ {'try{ new Sink().touch(); }catch(Exception e){}' if i==REACH else ''} }} }}"
        for i in range(1, N + 1))
    return ("package fr;\n"
            "class Sink { void touch() throws Exception { new java.io.FileInputStream(\"/etc/hosts\").close(); } }\n"
            "interface Base { void op(); }\n" + impls + "\n"
            "class Dispatcher { void run(Base b) { b.op(); } }\n")

def ts_src():
    impls = "\n".join(
        f"class Impl{i} implements Base {{ op() {{ {'new Sink().touch();' if i==REACH else ''} }} }}"
        for i in range(1, N + 1))
    return ("import * as fs from 'fs';\n"
            "class Sink { touch() { fs.readFileSync('/etc/hosts'); } }\n"
            "interface Base { op(): void; }\n" + impls + "\n"
            "class Dispatcher { run(b: Base) { b.op(); } }\n")

def swift_src():
    impls = "\n".join(
        f"final class Impl{i}: Base {{ func op() {{ {'Sink().touch()' if i==REACH else ''} }} }}"
        for i in range(1, N + 1))
    return ("import Foundation\n"
            "final class Sink { func touch() { try? Data().write(to: URL(fileURLWithPath: \"/etc/hosts\")) } }\n"
            "protocol Base { func op() }\n" + impls + "\n"
            "final class Dispatcher { func run(_ b: Base) { b.op() } }\n")

def frontier_java(ws):
    jar = os.environ.get("CANDOR_JAVA_JAR") or newest(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
    if not jar or not shutil.which("javac"): return None
    d = os.path.join(ws, "java"); os.makedirs(os.path.join(d, "fr"), exist_ok=True)
    open(os.path.join(d, "fr", "Cases.java"), "w").write(java_src())
    cls = os.path.join(d, "out")
    if run(["javac", "-d", cls, os.path.join(d, "fr", "Cases.java")]).returncode: return None
    rep = os.path.join(d, "r.json")
    run(["java", "-jar", jar, cls, "--json", rep])
    out = run(["java", "-jar", jar, "callers", rep, "fr.Sink.touch", "--json", "--include-unknown"])
    return json.loads(out.stdout or b"{}")

def frontier_ts(ws):
    if not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")) or not shutil.which("node"): return None
    d = os.path.join(ws, "ts"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "Cases.ts"), "w").write(ts_src())
    open(os.path.join(d, "package.json"), "w").write('{"name":"fr","version":"0.0.0"}')
    pfx = os.path.join(d, "r")
    run(["node", os.path.join(CANDOR_TS, "scan.mjs"), os.path.join(d, "Cases.ts"), pfx])
    out = run(["node", os.path.join(CANDOR_TS, "query.mjs"), "callers", pfx, "Sink.touch", "1", "--include-unknown"])
    return json.loads(out.stdout or b"{}")

def frontier_swift(ws):
    if not shutil.which("swift") or not os.path.exists(os.path.join(CANDOR_SWIFT, "Package.swift")): return None
    swbin = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(swbin) and run(["swift", "build"], cwd=CANDOR_SWIFT).returncode: return None
    qbin = os.environ.get("CANDOR_QUERY_BIN") or os.path.join(CANDOR, "target", "debug", "candor-query")
    if not os.path.exists(qbin) and run(["cargo", "build", "-q", "-p", "candor-query",
                                         "--manifest-path", os.path.join(CANDOR, "Cargo.toml")]).returncode: return None
    d = os.path.join(ws, "swift"); os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "cases.swift"); open(src, "w").write(swift_src())
    pfx = os.path.join(d, "r")
    run([swbin, src, "--out", pfx])
    out = run([qbin, "callers", pfx, "Sink.touch", "1", "--include-unknown"])
    return json.loads(out.stdout or b"{}")

def leaf(fn): return fn.split("(")[0].split(".")[-1]

def check(engine, res):
    """The frontier must surface exactly the dispatcher (via dispatch on `op`); Impl7.op confirmed."""
    if res is None:
        print(f"  {engine:6} not present — SKIPPED"); return None
    pv = res.get("possibleViaUnknownDispatch", [])
    confirmed_ok = any(leaf(f) == "op" for f in res.get("transitive", []))  # Impl7.op reaches the sink
    disp = [p for p in pv if leaf(p["fn"]) in ("run", "Dispatcher") and "op" in p["viaDispatchOn"]]
    ok = confirmed_ok and len(pv) == 1 and len(disp) == 1
    mark = "ok" if ok else "DIVERGE"
    print(f"  {engine:6} possibleViaUnknownDispatch={[p['fn'] + ' via ' + p['viaDispatchOn'] for p in pv]} "
          f"confirmed(Impl7.op)={confirmed_ok} -> {mark}")
    return ok

def main():
    print("DISPATCH-FRONTIER differential (callers --include-unknown, 0.7) — class/protocol engines")
    print(f"  scenario: Base.op with {N} impls (>fan-out), Impl{REACH}.op reaches Sink.touch; Dispatcher dispatches Base.op")
    ws = tempfile.mkdtemp(prefix="candor-frontier-")
    try:
        results = {"java": check("java", frontier_java(ws)),
                   "ts": check("ts", frontier_ts(ws)),
                   "swift": check("swift", frontier_swift(ws))}
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    present = {k: v for k, v in results.items() if v is not None}
    if not present:
        print("  no class/protocol engine present — SKIPPED"); return 0
    if all(present.values()):
        print(f"  FRONTIER DIFFERENTIAL: OK — {', '.join(present)} agree: the dispatcher is disclosed via dispatch on `op`, Impl{REACH}.op confirmed.")
        return 0
    print("  FRONTIER DIFFERENTIAL: FAILED"); return 1

sys.exit(main())
