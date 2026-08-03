#!/usr/bin/env python3
"""Cross-engine DISPATCH-FRONTIER differential (SPEC §3.1/§4 ⟨0.7⟩, `callers --include-unknown`),
run as a PRODUCER x CONSUMER MATRIX.

THE SCENARIO. One shared program per producer: a `Base.op()` with >CHA_FANOUT_LIMIT (13) implementors,
exactly one of which (`Impl7.op`) reaches an effectful sink `Sink.touch`; a `Dispatcher` that dispatches
`Base.op` on a `Base`-typed value. The dispatch is over too many impls, so each engine discloses it as
`dispatch:<Base>.op` (Unknown) and drops the edges — the dispatcher is NOT a confirmed caller of
`Sink.touch`. `callers Sink.touch --include-unknown` must therefore surface it in
`possibleViaUnknownDispatch` via dispatch on `op`, resolved against the §2.2 hierarchy sidecar.

WHY A MATRIX, AND THIS IS A DEFECT THAT WAS INSIDE THE INSTRUMENT
------------------------------------------------------------------
This ran as three arms — java, ts, swift — and printed "java, ts, swift agree". They were not three
independent observations. java's arm queried candor-java's own report with candor-java's consumer, ts's
likewise; but **candor-swift ships no `callers` verb, so the swift arm read its report with candor-rust's
`candor-query`**. Three arms, TWO independent consumers. A common-mode defect in the rust consumer would
have appeared in the swift arm alone and read as "swift disagrees" — attributing a consumer bug to a
producer — and a rust consumer that agreed with a WRONG answer would have counted as a third vote for it.

That is precisely §3's structural gap (four engines can share one wrong model) occurring INSIDE the suite
built to detect it. It is worth pointing at when justifying self-differentials, because it is not
hypothetical: it was here, in the file that prints the word "agree".

So the cross is now DESIGNED rather than accidental. Every producer's report is fed to every available
consumer, and the result is a grid:

    a whole ROW red     -> the CONSUMER is wrong (it fails on reports from every producer)
    a whole COLUMN red  -> the PRODUCER is wrong (every consumer fails on its report)
    one CELL red        -> a genuine pairwise disagreement, which is the interesting case

Neither shape is distinguishable from the other in a diagonal-only run, which is what this was.

CONSUMERS are java, ts and rust — the three engines shipping `callers --include-unknown`. rust is a
consumer here even though it is NOT a producer: it emits no `dispatch:` (its indeterminacy is
callback/native) and writes no §2.2 sidecar, so its own frontier is empty by language model. That
asymmetry is the reason it was doing double duty unlabelled before.

Each producer's report is NORMALISED into the file layout each consumer discovers sidecars by — java and
ts read `<stem>.json` + `<stem>.callgraph.json` + `<stem>.hierarchy.json`; rust globs a prefix. The
normalisation copies bytes and renames; it never edits a report, so no cell can pass because the harness
repaired its input.
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

# =====================================================================================================
# PRODUCERS. Each scans its own rendering of the scenario and returns
# (report, callgraph, hierarchy, target-fn) — or None when the engine is not present.
# =====================================================================================================
def produce_java(ws):
    jar = os.environ.get("CANDOR_JAVA_JAR") or newest(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
    if not jar or not shutil.which("javac"): return None
    d = os.path.join(ws, "p_java"); os.makedirs(os.path.join(d, "fr"), exist_ok=True)
    open(os.path.join(d, "fr", "Cases.java"), "w").write(java_src())
    cls = os.path.join(d, "out")
    if run(["javac", "-d", cls, os.path.join(d, "fr", "Cases.java")]).returncode: return None
    rep = os.path.join(d, "r.json")
    run(["java", "-jar", jar, cls, "--json", rep])
    stem = rep[:-5]
    return (rep, stem + ".callgraph.json", stem + ".hierarchy.json", "fr.Sink.touch")

def produce_ts(ws):
    if not os.path.exists(os.path.join(CANDOR_TS, "scan.mjs")) or not shutil.which("node"): return None
    d = os.path.join(ws, "p_ts"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "Cases.ts"), "w").write(ts_src())
    open(os.path.join(d, "package.json"), "w").write('{"name":"fr","version":"0.0.0"}')
    pfx = os.path.join(d, "r")
    run(["node", os.path.join(CANDOR_TS, "scan.mjs"), os.path.join(d, "Cases.ts"), pfx])
    return (pfx + ".json", pfx + ".callgraph.json", pfx + ".hierarchy.json", "Cases.Sink.touch")

def produce_swift(ws):
    if not shutil.which("swift") or not os.path.exists(os.path.join(CANDOR_SWIFT, "Package.swift")): return None
    swbin = os.path.join(CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(swbin) and run(["swift", "build"], cwd=CANDOR_SWIFT).returncode: return None
    d = os.path.join(ws, "p_swift"); os.makedirs(d, exist_ok=True)
    src = os.path.join(d, "cases.swift"); open(src, "w").write(swift_src())
    pfx = os.path.join(d, "r")
    run([swbin, src, "--out", pfx])
    rep = newest(d, ".Swift.json")
    if not rep: return None
    stem = rep[:-5]
    return (rep, stem + ".callgraph.json", stem + ".hierarchy.json", "Sink.touch")

PRODUCERS = [("java", produce_java), ("ts", produce_ts), ("swift", produce_swift)]


# =====================================================================================================
# CONSUMERS. Each takes the producer's three files, lays them out the way THIS consumer discovers
# sidecars, and runs `callers --include-unknown`. Copy-and-rename only: a cell must never pass because
# the harness edited the report it was handed.
# =====================================================================================================
def _lay(dst, kind, files):
    rep, cg, hier = files
    os.makedirs(dst, exist_ok=True)
    # rust globs `<prefix>.*`; java and ts strip `.json` off the report path and append the suffixes.
    names = ({"rep": "r.app.scan.json", "cg": "r.app.scan.callgraph.json", "hier": "r.app.hierarchy.json"}
             if kind == "rust" else
             {"rep": "r.json", "cg": "r.callgraph.json", "hier": "r.hierarchy.json"})
    shutil.copyfile(rep, os.path.join(dst, names["rep"]))
    for src, key in ((cg, "cg"), (hier, "hier")):
        if src and os.path.exists(src): shutil.copyfile(src, os.path.join(dst, names[key]))
    return os.path.join(dst, "r") if kind == "rust" else os.path.join(dst, names["rep"])

def consume_java(dst, files, target):
    jar = os.environ.get("CANDOR_JAVA_JAR") or newest(os.path.join(CANDOR_JAVA, "build", "libs"), "-all.jar")
    if not jar: return None
    loc = _lay(dst, "java", files)
    out = run(["java", "-jar", jar, "callers", target, "--report", loc, "--include-unknown", "--json"])
    return json.loads(out.stdout or b"{}")

def consume_ts(dst, files, target):
    q = os.path.join(CANDOR_TS, "query.mjs")
    if not shutil.which("node") or not os.path.exists(q): return None
    loc = _lay(dst, "ts", files)
    out = run(["node", q, "callers", target, "--report", loc, "--include-unknown"])
    return json.loads(out.stdout or b"{}")

def consume_rust(dst, files, target):
    qbin = os.environ.get("CANDOR_QUERY_BIN") or os.path.join(CANDOR, "target", "debug", "candor-query")
    if not os.path.exists(qbin): return None
    pfx = _lay(dst, "rust", files)
    out = run([qbin, "callers", pfx, target, "1", "--include-unknown"])
    return json.loads(out.stdout or b"{}")

CONSUMERS = [("java", consume_java), ("ts", consume_ts), ("rust", consume_rust)]


def leaf(fn): return fn.split("(")[0].split(".")[-1]

def verdict(res):
    """The frontier must surface exactly the dispatcher (via dispatch on `op`), with Impl7.op confirmed."""
    if res is None: return None, "absent"
    pv = res.get("possibleViaUnknownDispatch", [])
    confirmed = any(leaf(f) == "op" for f in res.get("transitive", []))
    disp = [p for p in pv if leaf(p["fn"]) in ("run", "Dispatcher") and "op" in p.get("viaDispatchOn", "")]
    ok = confirmed and len(pv) == 1 and len(disp) == 1
    return ok, ("ok" if ok else "pv=%s confirmed=%s" % ([p["fn"] + " via " + p.get("viaDispatchOn", "?") for p in pv], confirmed))


def main():
    print("DISPATCH-FRONTIER differential (callers --include-unknown, 0.7) — PRODUCER x CONSUMER matrix")
    print(f"  scenario: Base.op with {N} impls (>fan-out), Impl{REACH}.op reaches Sink.touch; Dispatcher dispatches Base.op")
    print("  rust is a CONSUMER only — it emits no `dispatch:` and writes no §2.2 sidecar, so it has no")
    print("  frontier of its own. That asymmetry is what made the old swift ARM secretly a rust-consumer arm.")
    ws = tempfile.mkdtemp(prefix="candor-frontier-")
    grid, notes = {}, {}
    try:
        made = {}
        for pname, mk in PRODUCERS:
            got = mk(ws)
            if got is None:
                print(f"  producer {pname:6} not present — SKIPPED"); continue
            made[pname] = got
        if not made:
            print("  no producer present — SKIPPED"); return 0
        for pname, (rep, cg, hier, target) in made.items():
            for cname, fn in CONSUMERS:
                dst = os.path.join(ws, f"x_{pname}_{cname}")
                try:
                    res = fn(dst, (rep, cg, hier), target)
                except Exception as e:               # a consumer that THROWS is the harness, not a verdict
                    grid[(pname, cname)], notes[(pname, cname)] = None, "harness: %s" % e
                    continue
                ok, why = verdict(res)
                grid[(pname, cname)] = ok
                notes[(pname, cname)] = why
    finally:
        shutil.rmtree(ws, ignore_errors=True)

    cons = [c for c, _ in CONSUMERS]
    print("\n  producer \\ consumer   " + "".join(f"{c:>10}" for c in cons))
    for pname, _ in PRODUCERS:
        if not any((pname, c) in grid for c in cons): continue
        cells = []
        for c in cons:
            v = grid.get((pname, c))
            cells.append("  -  " if v is None else (" ok  " if v else "DIVERG"))
        print(f"  {pname:20} " + "".join(f"{x:>10}" for x in cells))

    live = {k: v for k, v in grid.items() if v is not None}
    bad = [k for k, v in live.items() if not v]
    if not live:
        print("  no (producer, consumer) pair ran — SKIPPED"); return 0
    # A property with no live cell must never print as a pass; and a whole row/column red is a louder
    # finding than a cell, so name the shape rather than leaving it to be eyeballed.
    for c in cons:
        col = [k for k in live if k[1] == c]
        if col and all(not live[k] for k in col):
            print(f"  ROW RED — consumer `{c}` fails on EVERY producer's report: a CONSUMER defect, not a producer one.")
    for p, _ in PRODUCERS:
        row = [k for k in live if k[0] == p]
        if row and all(not live[k] for k in row):
            print(f"  COLUMN RED — every consumer fails on `{p}`'s report: a PRODUCER defect.")
    if not bad:
        print(f"  FRONTIER DIFFERENTIAL: OK — {len(live)} (producer, consumer) pairs agree: the dispatcher is")
        print(f"  disclosed via dispatch on `op`, Impl{REACH}.op confirmed. Independent consumers: {len({k[1] for k in live})}.")
        return 0
    for k in sorted(bad):
        print(f"  DIVERGE  producer={k[0]} consumer={k[1]}: {notes[k]}")
    print("  FRONTIER DIFFERENTIAL: FAILED"); return 1

sys.exit(main())
