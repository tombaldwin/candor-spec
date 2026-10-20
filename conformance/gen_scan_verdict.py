#!/usr/bin/env python3
"""
PART 97b — THE SCAN-ROUTE VERDICT AGREES WITH THE REFERENCE MODEL'S COMPOSITION OF ITS PRODUCERS.

WHAT IT CHECKS
--------------
PART 97 judges `gate --report`, a pure function of (report, policy). It cannot see the baseline guard, which
has no report-only route (SPEC §3; `reference/policy_model.py` header), and it cannot see how `scan --policy`
COMPOSES its producers — the policy gate, the AS-EFF-005 baseline guard — with the causes that make a run
refuse or go incomplete. The S5 review of 2026-10-20 found that composition is where the scan-route defects
live: SOUNDNESS R1231 and R1236 were both an exit-2 arm that forgot "a certain violation dominates".

The oracle is `policy_model.scan_verdict` (with its own selftest, which carries a refusal-first seed of
exactly that defect class), fed the GROUND-TRUTH signatures of one small program per engine:

    save   Fs            (direct)
    go     Fs            (inherited: calls save)
    env    Env           (direct; PURE in the `gain` baseline, so the guard sees env GAIN Env)
    calm   pure          (absent from every report)

and the axes, 24 cells per engine:

    policy    none | clean (`deny Net`) | fire (`deny Fs`)
    baseline  none | clean (recorded over the same program) | gain (recorded with `env` pure)
    cause     none | parse (one unparseable unit beside the program) | badtoken (`deny Unknown[dispach]`
              appended to the policy — §3.1: a policy that cannot be honoured AS WRITTEN; policy != none only)

Compared per cell: the exit code; the SET of (rule, unit leaf) violation rows; `refused`; that a run over
unparsed code under a configured gate says so (`incomplete` / `unanalyzed`); and on a bad token, the SET of
`unevaluated` rules (EVERY rule — §3.1 ⟨0.24⟩ on the composed document, §3.1 ⟨0.40⟩ on the sole refusal).

PRECONDITION, per engine, before any cell is judged: the engine's OWN plain-scan report of each program
variant must carry the ground truth (save and go carry Fs, env carries Env or nothing as the variant says,
calm absent). A failure is ANALYSIS-MISMATCH — reported, counted as a failure, and the engine's cells are
not judged: a verdict over a report that does not say what the model was told proves nothing about the
composition.

WHAT IT CANNOT SEE: an absent or fabricated effect (the precondition is the only analysis check, on four
units); scope matching; an unreadable BASELINE beside a firing policy, which SPEC does not decide (R1237 —
PART 29 measures it as UNPINNED).

SEEDS, every run:
  oracle    the refusal-first composer (`policy_model._scan_verdict_refusal_first`, R1231/R1236's shape) is
            compared against each engine's ACTUAL output and must diverge on at least one cell.
  document  one violation deleted from an engine's real `--gate-json`: MUST be caught.
  expected  one cell's EXPECTED exit flipped: EXACTLY that cell must diverge.

XFAIL is keyed (cell, engine), names an OPEN register row, and a PASSING XFAIL IS A FAILURE.

USAGE
    python3 gen_scan_verdict.py [--keep] [--engine rust|java|ts|swift]
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference"))
import policy_model as M                    # noqa: E402  the oracle
import gen_incomplete_dominance as P5       # noqa: E402  engine invokers, report discovery, verdict reading

SPEC_CLAUSES = [
    ("§3.1 ⟨0.24⟩", "Any violation the run has already established on carried evidence"),
    ("§3.1 ⟨0.24⟩", "on a whole-policy refusal that list carries EVERY rule of\nthe refused policy"),
    ("§3.1 ⟨0.40⟩", "**A REFUSAL CAUSED BY THE POLICY DISCLOSES THE POLICY**"),
    ("§3.3.1", "A configured gate over incompletely-analyzed code MUST fail closed"),
    ("§3 ⟨0.40⟩", "**A FUNCTION ABSENT FROM THE BASELINE IS COMPARED AGAINST NOTHING — IT IS NOT EXEMPT.**"),
]

ENGINES = ("rust", "java", "ts", "swift")
UNITS = {"save": M.Sig({"Fs"}), "go": M.Sig({"Fs"}), "env": M.Sig({"Env"})}
BASE = {"clean": dict(UNITS), "gain": {"save": M.Sig({"Fs"}), "go": M.Sig({"Fs"}), "env": M.Sig()}}
POLICY = {"clean": ("deny Net", M.deny("Net")), "fire": ("deny Fs", M.deny("Fs"))}
BADTOKEN = "deny Unknown[dispach]"

SRC = {
    "rust": lambda env_body: (
        'pub fn save() { let _ = std::fs::read("/tmp/candor-p97b"); }\n'
        'pub fn go() { save(); }\n'
        f'pub fn env() {{ {env_body} }}\n'
        'pub fn calm() -> u32 { 1 }\n'),
    "java": lambda env_body: (
        "public class Svc {\n"
        '  public static void save() { try { java.nio.file.Files.readAllBytes(java.nio.file.Path.of("/tmp/candor-p97b")); } catch (Exception e) {} }\n'
        "  public static void go() { save(); }\n"
        f"  public static void env() {{ {env_body} }}\n"
        "  public static int calm() { return 1; }\n}\n"),
    "ts": lambda env_body: (
        'import * as fs from "fs";\n'
        'export function save(): void { fs.readFileSync("/tmp/candor-p97b"); }\n'
        'export function go(): void { save(); }\n'
        f'export function env(): void {{ {env_body} }}\n'
        'export function calm(): number { return 1; }\n'),
    "swift": lambda env_body: (
        "import Foundation\n"
        "enum Svc {\n"
        '  static func save() { _ = FileManager.default.contents(atPath: "/tmp/candor-p97b") }\n'
        "  static func go() { save() }\n"
        f"  static func env() {{ {env_body} }}\n"
        "  static func calm() -> Int { 1 }\n}\n"),
}
ENV_READ = {"rust": 'let _ = std::env::var("CANDOR_P97B");', "java": 'System.getenv("CANDOR_P97B");',
            "ts": "void process.env.CANDOR_P97B;",
            "swift": '_ = ProcessInfo.processInfo.environment["CANDOR_P97B"]'}
BROKEN = {"rust": ("src/broken.rs", "pub fn nope( {{{ this is not rust\n"),
          "ts": ("broken.ts", "export function nope( {{{ <<< not typescript\n"),
          "swift": ("broken.swift", "func nope( {{{ <<< not swift\n")}

# (cell id, engine) -> OPEN register row. A PASSING XFAIL IS A FAILURE.
# EMPTY on the released 0.40.13 engines once R1236 (candor-scan, fixed at `f81d38a`) is in. Note what is NOT
# here: R1233's missing `unevaluated` is a `gate --report` defect only — on THIS route candor-scan and
# candor-swift both write every rule (measured 2026-10-20), so the two routes' documents differ there (PART 99
# carries the report-route xfails).
XFAIL = {}


_FAULT = [1] if os.environ.get("CANDOR_PROBE_FAULT") else []


def leaf(fn):
    for sep in ("::", "#", "."):
        fn = fn.split(sep)[-1]
    return fn


def build(eng, ws, env_body, broken):
    """Write one program variant IN PLACE and return the scan target (None: harness failure).

    ONE DIRECTORY PER ENGINE, REWRITTEN BETWEEN SCANS — never a directory per variant. candor-swift names
    the package after the directory it scans, so a baseline recorded over `pure/` and a run over `cur/` share
    no key: every unit read as ABSENT from the baseline and the ⟨0.40⟩ guard fired on all three (measured on
    the first run of this file, 2026-10-20 — a harness artifact shaped exactly like a swift defect)."""
    d = os.path.join(ws, eng, "prog")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    if eng == "rust":
        os.makedirs(os.path.join(d, "src"))
        with open(os.path.join(d, "Cargo.toml"), "w") as f:
            f.write('[package]\nname = "p97b"\nversion = "0.0.0"\nedition = "2021"\n')
        with open(os.path.join(d, "src", "lib.rs"), "w") as f:
            f.write(SRC[eng](env_body))
    elif eng == "java":
        src = os.path.join(d, "src")
        os.makedirs(src)
        with open(os.path.join(src, "Svc.java"), "w") as f:
            f.write(SRC[eng](env_body))
        out = os.path.join(d, "classes")
        rc, _o, _e = P5.run(["javac", "-d", out, os.path.join(src, "Svc.java")])
        if rc != 0:
            return None
        if broken:
            with open(os.path.join(out, "Broken.class"), "wb") as f:
                f.write(b"\xca\xfe\xba\xbe" + b"\x00" * 8 + b"garbage-not-a-constant-pool")
        return out
    elif eng == "ts":
        with open(os.path.join(d, "package.json"), "w") as f:
            f.write('{"name":"p97b","version":"1.0.0"}\n')
        with open(os.path.join(d, "svc.ts"), "w") as f:
            f.write(SRC[eng](env_body))
    else:
        with open(os.path.join(d, "svc.swift"), "w") as f:
            f.write(SRC[eng](env_body))
    if broken and eng in BROKEN:
        rel, txt = BROKEN[eng]
        with open(os.path.join(d, rel), "w") as f:
            f.write(txt)
    return d


def plain_report(go, target, prefix):
    for f in P5.gd._glob(os.path.dirname(prefix), ".json"):
        if os.path.basename(f).startswith(os.path.basename(prefix)):
            os.remove(f)
    rc, _o, _e = go(target, None, None, None, out_prefix=prefix)
    snap = P5.find_report(os.path.dirname(prefix), prefix)
    if rc != 0 or not snap:
        return None, None
    return snap, json.load(open(snap))


def precondition(rep, env_has):
    """The engine's own report must say what the model is told. Returns problems."""
    got = {}
    for e in rep.get("functions", []):
        if e.get("interfaceUnion"):
            continue
        got.setdefault(leaf(e.get("fn", "")), set()).update(set(e.get("inferred") or []))
    bad = []
    for u in ("save", "go"):
        if "Fs" not in got.get(u, set()):
            bad.append(f"{u} does not carry Fs ({sorted(got.get(u, []))})")
    if env_has and "Env" not in got.get("env", set()):
        bad.append(f"env does not carry Env ({sorted(got.get('env', []))})")
    if not env_has and got.get("env"):
        bad.append(f"env (pure variant) carries {sorted(got['env'])}")
    if got.get("calm"):
        bad.append(f"calm carries {sorted(got['calm'])}")
    extra = {u for u in got if u not in ("save", "go", "env", "calm") and got[u] - {"Unknown"}}
    if extra:
        bad.append(f"unexpected effectful units {sorted(extra)}")
    return bad


def cells():
    out = []
    for p in ("none", "clean", "fire"):
        for b in ("none", "clean", "gain"):
            for c in ("none", "parse", "badtoken"):
                if p == "none" and c == "badtoken":
                    continue
                out.append((p, b, c))
    return out


def expected(p, b, c):
    rules = ()
    pol = None
    if p != "none":
        rules = (POLICY[p][0],) + ((BADTOKEN,) if c == "badtoken" else ())
        pol = POLICY[p][1]
    return M.scan_verdict(UNITS, policy=pol, baseline=BASE.get(b, M.ABSENT), has_baseline=(b != "none"),
                          parse_failure=(c == "parse"), policy_error=(c == "badtoken"), policy_rules=rules)


def observe(rc, doc):
    o = {"exit": rc, "doc": isinstance(doc, dict)}
    if not isinstance(doc, dict):
        return o
    o["refused"] = bool(doc.get("refused"))
    o["rows"] = {(v.get("rule"), leaf(v.get("fn", ""))) for v in P5.violations_of(doc)}
    o["incomplete"] = P5.says_incomplete(doc)
    ue = doc.get("unevaluated")
    o["unevaluated"] = {u.get("rule") for u in ue if isinstance(u, dict)} if isinstance(ue, list) else set()
    return o


def judge(o, want, gate):
    bad = []
    if o["exit"] != want["exit"]:
        bad.append(f"exit {o['exit']}, model {want['exit']}")
    if not o["doc"]:
        return bad + ["no readable --gate-json document"]
    if o["refused"] != want["refused"]:
        bad.append(f"refused={o['refused']}, model {want['refused']}")
    if o["rows"] != want["rows"]:
        extra, missing = sorted(o["rows"] - want["rows"]), sorted(want["rows"] - o["rows"])
        if extra:
            bad.append(f"rows the model does not produce: {extra}")
        if missing:
            bad.append(f"rows MISSING: {missing}")
    if want["incomplete"] and not o["incomplete"]:
        bad.append("the run did not disclose the unparsed unit (`incomplete`/`unanalyzed`)")
    if want["unevaluated"] and o["unevaluated"] != want["unevaluated"]:
        bad.append(f"`unevaluated` {sorted(o['unevaluated'])}, model {sorted(want['unevaluated'])}")
    return bad


def run_engine(eng, ws):
    """Returns (results {cid: (obs, want, problems)}, harness problems)."""
    go, err = P5.engine_bin(eng)
    if go is None:
        return None, [f"absent: {err}"]
    variant = {"cur": (ENV_READ[eng], False), "pure": ("", False), "curbroken": (ENV_READ[eng], True)}
    snaps, harness = {}, []
    for b, tag, env_has in (("clean", "cur", True), ("gain", "pure", False)):
        t = build(eng, ws, *variant[tag])
        if t is None:
            return None, [f"HARNESS: could not build the {tag} variant"]
        snap, rep = plain_report(go, t, os.path.join(ws, eng, f"base-{b}"))
        if snap is None:
            return None, [f"HARNESS: the plain scan of the {tag} variant wrote no report"]
        pre = precondition(rep, env_has)
        if pre:
            harness.append(f"ANALYSIS-MISMATCH ({tag} variant): " + "; ".join(pre))
        snaps[b] = snap
    if harness:
        return None, harness
    res = {}
    for p, b, c in cells():
        cid = f"p={p}/b={b}/c={c}"
        pol = None
        if p != "none":
            pol = os.path.join(ws, eng, f"pol-{p}-{c}.txt")
            with open(pol, "w") as f:
                f.write(POLICY[p][0] + "\n" + (BADTOKEN + "\n" if c == "badtoken" else ""))
        verdict = os.path.join(ws, eng, f"v-{p}-{b}-{c}.json")
        if os.path.exists(verdict):
            os.remove(verdict)
        target = build(eng, ws, *variant["curbroken" if c == "parse" else "cur"])
        if target is None:
            return None, [f"HARNESS: could not build the program for {cid}"]
        rc, _o, e = go(target, pol, verdict, snaps.get(b))
        doc = P5.verdict_of(verdict)
        if _FAULT and cid == "p=fire/b=none/c=none" and P5.violations_of(doc):
            # probe_check.py's fault (PART 30): one violation silently missing from a real document.
            print(f"  PROBE: CANDOR_PROBE_FAULT — deleting one violation from {eng}'s {cid} document")
            doc = dict(doc); doc["violations"] = P5.violations_of(doc)[1:]
            _FAULT.clear()
        o = observe(rc, doc)
        o["_doc"], o["_err"] = doc, e
        want = expected(p, b, c)
        res[cid] = (o, want, judge(o, want, gate=(p != "none" or b != "none")))
    return res, []


def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    ws = tempfile.mkdtemp(prefix="candor-p97b-")
    fails = 0
    try:
        if M._selftest_scan_verdict.__name__ and M._selftest_scan_verdict() != 0:
            print("  FAIL: the oracle's own selftest failed — nothing below would be evidence")
            return 1
        all_res = {}
        for eng in ENGINES:
            if only and eng != only:
                continue
            res, harness = run_engine(eng, ws)
            if res is None:
                for h in harness:
                    print(f"  {eng:6s} {h}")
                fails += 0 if harness and harness[0].startswith("absent") else 1
                continue
            all_res[eng] = res
            n_ok = n_x = 0
            for cid, (o, want, bad) in res.items():
                xf = XFAIL.get((cid, eng))
                if bad and xf:
                    n_x += 1
                    print(f"    {eng:6s} {cid:28s} xfail [{xf.split(':')[0]}] — {'; '.join(bad)}")
                elif bad:
                    fails += 1
                    print(f"    {eng:6s} {cid:28s} DIVERGE from the model — {'; '.join(bad)}"
                          + (f"  [stderr: {o['_err'].strip()[:140]}]" if o["exit"] == 2 and want["exit"] != 2 else ""))
                elif xf:
                    fails += 1
                    print(f"    {eng:6s} {cid:28s} XFAIL ARM PASSED — expectation is STALE ({xf}); retire it")
                else:
                    n_ok += 1
            exits = {o["exit"] for o, _w, _b in res.values()}
            if not {0, 1, 2} <= exits:
                print(f"    {eng:6s} VACUOUS — exits seen {sorted(x for x in exits if x is not None)}")
                fails += 1
            print(f"  {eng:6s} {n_ok}/{len(res)} cells agree with the model" + (f", {n_x} xfail" if n_x else ""))
        if not all_res:
            print("  FAIL: no engine produced a measurement")
            return 1

        # ---- SEEDS ------------------------------------------------------------------------------------
        seed_bad = []
        eng0 = next(iter(all_res))
        res0 = all_res[eng0]
        moved = 0
        for cid, (o, _want, _bad) in res0.items():
            p, b, c = (x.split("=")[1] for x in cid.split("/"))
            rules = ((POLICY[p][0],) + ((BADTOKEN,) if c == "badtoken" else ())) if p != "none" else ()
            seedw = M._scan_verdict_refusal_first(
                UNITS, policy=POLICY[p][1] if p != "none" else None, baseline=BASE.get(b, M.ABSENT),
                has_baseline=(b != "none"), parse_failure=(c == "parse"), policy_error=(c == "badtoken"),
                policy_rules=rules)
            if judge(o, seedw, True):
                moved += 1
        if moved == 0:
            seed_bad.append("oracle seed: the refusal-first composer agrees with every cell — the cells do not reach the composition")
        cid1 = "p=fire/b=none/c=none"
        o, want, _bad = res0[cid1]
        d = o["_doc"]
        if d and P5.violations_of(d):
            d2 = dict(d); d2["violations"] = P5.violations_of(d)[1:]
            if not judge(observe(o["exit"], d2), want, True):
                seed_bad.append("document seed: a deleted violation was NOT caught")
        else:
            seed_bad.append(f"document seed could not run: {eng0}'s {cid1} document has no violations")
        flipped = 0
        for cid, (o, want, bad) in res0.items():
            w = dict(want)
            if cid == cid1:
                w["exit"] = 0
            if bool(judge(o, w, True)) != bool(bad):
                flipped += 1
        if flipped != 1:
            seed_bad.append(f"expected seed: flipping one EXPECTED exit moved {flipped} cells, want exactly 1")
        for s in seed_bad:
            print(f"  SEED FAIL: {s}")
        fails += len(seed_bad)
        if not seed_bad:
            print(f"  seeds ({eng0}): the refusal-first composer diverges on {moved} cell(s); a deleted violation is "
                  f"caught; one flipped EXPECTED moves exactly one cell")
        print("SCAN-ROUTE VERDICT: " + ("OK" if not fails else f"{fails} FAILURE(S)"))
        return 1 if fails else 0
    finally:
        if keep:
            print(f"  (workspace kept at {ws})")
        else:
            shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
