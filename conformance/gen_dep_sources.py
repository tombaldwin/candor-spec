#!/usr/bin/env python3
"""PART 108 — TYPING A VALUE FROM A DEPENDENCY'S OWN SOURCE, `dependencySources`, SPEC §2 ⟨0.42⟩.

SOUNDNESS R1578 (an UNCHAINED dependency's factory value untyped, so its method reaches no rule and the caller reads
silent or `invisible` only; candor-rust `lane/rust-vein` types it from the dependency's source). The owner's ruling
(2026-11-09) and the clause: ONLY the version the project's Cargo.lock pins, ONLY when its source is present, the reading
may only ADD, and every source read is recorded in the top-level `dependencySources` array.

TWO ARMS.

  S — rust only, a HERMETIC fixture: a CARGO_HOME holding one registry checkout (`async-nats` 0.49.0, signatures only;
      the dependency carries a classified crate's NAME so candor's own rules decide what a typed call is charged —
      the cells are about which TYPE the receiver gets), a path dependency (0.50.0), and six consumers that differ in
      their manifest / lockfile alone. Every consumer's `f` is the same text:
          let js = async_nats::jetstream::new(c); js.query_account().await
        pin_reg     lock pins 0.49.0, present            -> f charged Net (`deny Net f` exits 1), field names it
        pin_path    lock pins the path dependency        -> f charged Net, field names it with origin `path`
        absent_ver  lock pins 0.49.1, only 0.49.0 there  -> f NOT charged Net, field ABSENT (no semver guess)
        no_lock     no Cargo.lock                        -> f NOT charged Net, field ABSENT
        twin        consumer declares its own `struct Context` with an Fs `query_account`
                                                         -> f_twin charged Net, NOT Fs, no call-graph edge to the local
                                                            `Context::query_account`
        none        lock pins a present source, nothing is typed through it
                                                         -> the report has NO `dependencySources` key (the carrier
                                                            `h` reads Env, so the scan demonstrably ran)
        mono        pin_reg's tree scanned with the source ABSENT (an empty CARGO_HOME) and PRESENT: every unit's
                    inferred / invisible / incomplete with the source absent is a subset of the same with it present
                    (the adding-only rule). SEED `mono_seed`: the same checker run in the REVERSE direction must
                    find a difference, or `mono` is VACUOUS
        det         pin_reg's tree scanned under two different CARGO_HOMEs holding the same source (different paths,
                    different registry index directory names): the two reports are BYTE-IDENTICAL, and neither
                    carries either CARGO_HOME path
        chain_tol   the path dependency scanned alone, its report chained into pin_path's consumer as is and with a
                    `dependencySources` key injected: the consumer's two reports are byte-identical (a rust reader
                    tolerates the key on the chained route)
      java, ts and swift have no S arm: java reads bytecode and ts asks the type checker, so neither types a dependency
      value from the dependency's source; candor-swift does not do so today.

  H — four-way READER TOLERANCE (§2 forward compatibility, :1845): one hand-written report with a Net unit and a
      `dependencySources` array (each element also carrying `typed` and an unknown future member), and the same report
      without the key. Every engine's `gate --report` with `deny Net` must exit 1 on both, with the same violations.

CALIBRATED: CANDOR_PROBE_FAULT=1 deletes the registry checkout (so pin_reg, twin and det go red) and removes the Net
unit's effect from the H arm's report carrying the field (so h_tol goes red on every engine). Registered in
probe_check.py (java arm, H only).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_rung024 as G                # noqa: E402
import gen_policy_semantics as PS      # noqa: E402

SPEC_CLAUSES = [
    ("§2 ⟨0.42⟩", "ONLY THE SOURCE THE PROJECT'S LOCKFILE PINS, AND ONLY WHEN THAT SOURCE IS PRESENT."),
    ("§2 ⟨0.42⟩", "It MUST NOT withdraw any effect, `Unknown`, `invisible` or `incomplete` that the same engine reports"),
    ("§2 ⟨0.42⟩", "It MUST NOT route the call to a definition the consumer declares that merely shares the type's leaf name"),
    ("§2 ⟨0.42⟩", "EVERY SOURCE READ TO TYPE A VALUE IS RECORDED"),
    ("§2 ⟨0.42⟩", "The field is OMITTED when empty, so a report that read nothing is byte-identical to a pre-rung one."),
    ("§2 ⟨0.42⟩", "produce byte-identical reports wherever those sources are installed"),
    ("§2", "a consumer MUST tolerate (ignore) envelope or entry fields it does not recognize."),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
REG = "registry+https://github.com/rust-lang/crates.io-index"
STRIP = ("CANDOR_CONFIG", "CANDOR_DEPS", "CANDOR_POLICY", "CANDOR_BASELINE", "CANDOR_R1580", "CANDOR_R1580_OFF",
         "CANDOR_R1578_OFF", "CANDOR_R1580_CUT_OFF")


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(s)


def dep_src(d, version):
    write(os.path.join(d, "Cargo.toml"),
          '[package]\nname = "async-nats"\nversion = "%s"\nedition = "2021"\n' % version)
    write(os.path.join(d, "src/lib.rs"), "pub mod jetstream;\n")
    write(os.path.join(d, "src/jetstream/mod.rs"),
          "pub mod context;\npub use context::Context;\npub fn new(c: u8) -> Context { Context::make(c) }\n")
    write(os.path.join(d, "src/jetstream/context.rs"),
          "pub struct Context(u8);\nimpl Context {\n pub(crate) fn make(c: u8) -> Self { Context(c) }\n"
          " pub async fn query_account(&self) -> u8 { self.0 }\n}\n")


F_SRC = "pub async fn f(c: u8) -> u8 { let js = async_nats::jetstream::new(c); js.query_account().await }\n"
TWIN_SRC = ("pub struct Context;\nimpl Context { pub async fn query_account(&self) -> u8 "
            "{ let _ = std::fs::write(\"/tmp/never\", \"\"); 0 } }\n"
            "pub async fn f_twin(c: u8) -> u8 { let js = async_nats::jetstream::new(c); js.query_account().await }\n")
NONE_SRC = ("pub fn g() -> u8 { 1 }\n"
            "pub fn h() -> String { std::env::var(\"X\").unwrap_or_default() }\n")


def app(root, name, req, lock, src):
    d = os.path.join(root, name)
    write(os.path.join(d, "Cargo.toml"),
          '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\nasync-nats = %s\n' % (name, req))
    if lock is not None:
        ver, source = lock
        srcline = 'source = "%s"\n' % source if source else ""
        write(os.path.join(d, "Cargo.lock"),
              'version = 4\n\n[[package]]\nname = "async-nats"\nversion = "%s"\n%s\n[[package]]\nname = "%s"\n'
              'version = "0.1.0"\n' % (ver, srcline, name))
    write(os.path.join(d, "src/lib.rs"), src)
    return d


def build(ws):
    fx = os.path.join(ws, "fx")
    homes = {"home": os.path.join(fx, "home"), "home2": os.path.join(fx, "other", "cargo"),
             "empty": os.path.join(fx, "empty-home")}
    dep_src(os.path.join(homes["home"], "registry/src/index.crates.io-0000000000000000/async-nats-0.49.0"), "0.49.0")
    dep_src(os.path.join(homes["home2"], "registry/src/index.crates.io-1111111111111111/async-nats-0.49.0"), "0.49.0")
    os.makedirs(os.path.join(homes["empty"], "registry/src"), exist_ok=True)
    dep_src(os.path.join(fx, "pathdep", "async-nats"), "0.50.0")
    if FAULT:
        shutil.rmtree(os.path.join(homes["home"], "registry/src/index.crates.io-0000000000000000"))
        shutil.rmtree(os.path.join(homes["home2"], "registry/src/index.crates.io-1111111111111111"))
    apps = {
        "pin_reg": app(fx, "pinreg", '"0.49"', ("0.49.0", REG), F_SRC),
        "pin_path": app(fx, "pinpath", '{ path = "../pathdep/async-nats" }', ("0.50.0", None), F_SRC),
        "absent_ver": app(fx, "absentver", '"0.49"', ("0.49.1", REG), F_SRC),
        "no_lock": app(fx, "nolock", '"0.49"', None, F_SRC),
        "twin": app(fx, "twin", '"0.49"', ("0.49.0", REG), TWIN_SRC),
        "none": app(fx, "none", '"0.49"', ("0.49.0", REG), NONE_SRC),
    }
    return fx, homes, apps


def scan(target, home, out, deps=None):
    """Scan with `--out` (report + call-graph sidecar). Returns (report dict | None, report bytes, sidecar | None, err)."""
    env = {k: v for k, v in os.environ.items() if k not in STRIP}
    env["CARGO_HOME"] = home
    if deps:
        env["CANDOR_DEPS"] = deps
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    p = subprocess.run([G.rust_scan(), target, "--out", os.path.join(out, "r")], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    reps = sorted(f for f in os.listdir(out) if f.endswith(".scan.json"))
    if len(reps) != 1:
        return None, b"", None, "scan exit %s, report(s) %s: %s" % (p.returncode, reps, p.stderr.decode()[-300:])
    raw = open(os.path.join(out, reps[0]), "rb").read()
    cg = os.path.join(out, reps[0][:-len(".json")] + ".callgraph.json")
    side = json.load(open(cg)) if os.path.exists(cg) else None
    return json.loads(raw), raw, side, None


def units(rep):
    return {e.get("fn"): e for e in (rep or {}).get("functions", []) if not e.get("interfaceUnion")}


def has(rep, fn, eff):
    e = units(rep).get(fn)
    return bool(e) and eff in (e.get("inferred") or [])


def gate_exit(rep_path, policy, ws, tag):
    rc, _doc, _err = PS.gate("rust", rep_path, policy, ws, tag)
    return rc


def ds_check(rep, want):
    """Problems with `dependencySources` against the expected [(package, version, origin)] ([] = key must be ABSENT)."""
    if not want:
        return [] if "dependencySources" not in rep else ["`dependencySources` present: %s"
                                                          % json.dumps(rep["dependencySources"])]
    ds = rep.get("dependencySources")
    if not isinstance(ds, list):
        return ["`dependencySources` absent or not an array: %r" % (ds,)]
    bad = []
    got = []
    for el in ds:
        if not isinstance(el, dict):
            bad.append("element is not an object: %r" % (el,))
            continue
        extra = set(el) - {"package", "version", "origin", "typed"}
        if extra:
            bad.append("element carries member(s) the clause does not define: %s" % sorted(extra))
        if "typed" in el and not (isinstance(el["typed"], int) and el["typed"] >= 1):
            bad.append("`typed` is not an integer >= 1: %r" % (el["typed"],))
        got.append((el.get("package"), el.get("version"), el.get("origin")))
    if got != sorted(got, key=lambda t: str(t[0])):
        bad.append("elements not ordered by package")
    if got != want:
        bad.append("records %s, EXPECTED %s" % (got, want))
    return bad


SURF = ("inferred", "invisible", "incomplete")


def subset_problems(small, big):
    """Every unit of `small`, surface by surface, is a subset of the same unit in `big`."""
    out = []
    bu = units(big)
    for fn, e in units(small).items():
        o = bu.get(fn)
        for s in SURF:
            a = set(e.get(s) or [])
            if not a:
                continue
            b = set((o or {}).get(s) or [])
            if not a <= b:
                out.append("%s.%s loses %s" % (fn, s, sorted(a - b)))
    return out


# =====================================================================================================
# S ARM — rust
# =====================================================================================================
def run_s(ws):
    rows = []
    fx, homes, apps = build(ws)
    o = lambda tag: os.path.join(ws, "out", tag)        # noqa: E731
    r = {}
    for k, d in apps.items():
        rep, raw, side, err = scan(d, homes["home"], o(k))
        if err:
            return None, "%s: %s" % (k, err)
        r[k] = (rep, raw, side, os.path.join(o(k), [f for f in os.listdir(o(k)) if f.endswith(".scan.json")
                                                    and not f.endswith(".callgraph.json")][0]))

    def cell(cid, problems, why):
        rows.append((cid, "rust", not problems, "; ".join(problems) if problems else "as the clause says", why))

    for cid, want_ds in (("pin_reg", [("async-nats", "0.49.0", "registry")]),
                         ("pin_path", [("async-nats", "0.50.0", "path")])):
        rep, _raw, _s, path = r[cid]
        p = [] if has(rep, "f", "Net") else ["f not charged Net: %s" % units(rep).get("f")]
        g = gate_exit(path, "deny Net f\n", ws, cid)
        if g != 1:
            p.append("`deny Net f` exit %s, EXPECTED 1" % g)
        p += ds_check(rep, want_ds)
        cell(cid, p, "the lock-pinned, present source types the value; the read is recorded")
    for cid in ("absent_ver", "no_lock"):
        rep, _raw, _s, path = r[cid]
        p = ["f charged Net from a source the lock does not pin: %s" % units(rep).get("f")] if has(rep, "f", "Net") else []
        g = gate_exit(path, "deny Net f\n", ws, cid)
        if g == 1:
            p.append("`deny Net f` exit 1, EXPECTED not 1")
        p += ds_check(rep, [])
        cell(cid, p, "no semver guess and no lockless reading: nothing typed, nothing recorded")
    rep, _raw, side, path = r["twin"]
    p = [] if has(rep, "f_twin", "Net") else ["f_twin not charged Net: %s" % units(rep).get("f_twin")]
    if has(rep, "f_twin", "Fs"):
        p.append("f_twin charged the local twin's Fs")
    edges = (side or {}).get("f_twin")
    if side is None:
        p.append("no call-graph sidecar to read the edge from")
    elif edges and any(x == "Context::query_account" for x in edges):
        p.append("f_twin edged to the consumer's own `Context::query_account`: %s" % edges)
    p += ds_check(rep, [("async-nats", "0.49.0", "registry")])
    cell("twin", p, "a same-leaf local type never answers for the dependency's type")
    rep, _raw, _s, _path = r["none"]
    p = [] if has(rep, "h", "Env") else ["carrier `h` not charged Env — the scan did not read this tree"]
    p += ds_check(rep, [])
    cell("none", p, "nothing typed through a source: no key at all")

    # mono + its seed
    absent, _a, _s2, err = scan(apps["pin_reg"], homes["empty"], o("mono_absent"))
    if err:
        return None, "mono: " + err
    present = r["pin_reg"][0]
    cell("mono", subset_problems(absent, present),
         "the source-absent report is a subset of the source-present one, unit by unit (adding only)")
    rev = subset_problems(present, absent)
    rows.append(("mono_seed", "rust", bool(rev),
                 "reverse direction finds %d difference(s)%s" % (len(rev), (": " + rev[0]) if rev else ""),
                 "SEED: the subset checker must detect a difference where one exists, or `mono` is VACUOUS"))

    # det
    rep2, raw2, _s3, err = scan(apps["pin_reg"], homes["home2"], o("det2"))
    if err:
        return None, "det: " + err
    raw1 = r["pin_reg"][1]
    p = [] if raw1 == raw2 else ["reports differ between two CARGO_HOMEs holding the same source"]
    for h in (homes["home"], homes["home2"]):
        if h.encode() in raw1 or h.encode() in raw2:
            p.append("a CARGO_HOME path (%s) appears in the report" % h)
    if not has(rep2, "f", "Net"):
        p.append("the second home typed nothing (f not Net) — the comparison is between two pre-rung reports")
    cell("det", p, "the report is a function of the tree and the pinned sources present, not of where they live")

    # chain_tol
    prod, _p, _s4, err = scan(os.path.join(fx, "pathdep", "async-nats"), homes["empty"], o("prod"))
    if err:
        return None, "producer: " + err
    pdir = os.path.join(ws, "deps-plain")
    idir = os.path.join(ws, "deps-inj")
    for d, doc in ((pdir, prod), (idir, dict(prod, dependencySources=[
            {"package": "zz-other", "version": "9.9.9", "origin": "registry", "typed": 3, "checksum": "future"}]))):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "async_nats.scan.json"), "w") as fh:
            json.dump(doc, fh)
    _c1, raw_a, _s5, err1 = scan(apps["pin_path"], homes["home"], o("chain_plain"),
                                 deps=os.path.join(pdir, "async_nats.scan.json"))
    _c2, raw_b, _s6, err2 = scan(apps["pin_path"], homes["home"], o("chain_inj"),
                                 deps=os.path.join(idir, "async_nats.scan.json"))
    if err1 or err2:
        cell("chain_tol", ["chained scan failed: %s %s" % (err1, err2)], "a rust reader tolerates the key")
    else:
        p = [] if raw_a == raw_b else ["the consumer's report changed when the producer carried the key"]
        # LIVENESS: the chained report must differ from the unchained one, or the producer was never read and the
        # equality above compares two reports that ignored CANDOR_DEPS altogether.
        if raw_a == r["pin_path"][1]:
            p.append("DEAD JOIN — the chained report equals the unchained one, so CANDOR_DEPS was not read")
        cell("chain_tol", p, "a chained rust reader ignores `dependencySources` on the producer report")
    return rows, None


# =====================================================================================================
# H ARM — four `gate --report`s
# =====================================================================================================
NET = {"fn": "jet::f", "hash": "app#jet::f", "inferred": ["Net"], "direct": ["Net"]}
BASE = {"candor": {"version": "handwritten", "spec": "0.42"}, "package": "app",
        "analyzed": {"count": 1, "digest": "0"}, "functions": [NET]}
DS = [{"package": "async-nats", "version": "0.49.0", "origin": "registry", "typed": 2, "checksum": "future-member"},
      {"package": "zz-path", "version": "0.1.0", "origin": "path"}]


def run_h(engines, ws):
    out = []
    with_ds = json.loads(json.dumps(BASE))
    with_ds["dependencySources"] = DS
    if FAULT:
        with_ds["functions"][0]["inferred"] = []
        with_ds["functions"][0]["direct"] = []
    for eng in engines:
        res = {}
        for tag, rep in (("plain", BASE), ("ds", with_ds)):
            loc = G.write_report(os.path.join(ws, "h-%s-%s" % (eng, tag)), eng, rep)
            rc, doc, _err = PS.gate(eng, loc, "deny Net\n", ws, "h-%s-%s" % (eng, tag))
            v = sorted((x.get("hash"), x.get("fn")) for x in (doc or {}).get("violations") or [])
            res[tag] = (rc, v)
        p = []
        for tag in ("plain", "ds"):
            if res[tag][0] != 1:
                p.append("%s: exit %s, EXPECTED 1" % (tag, res[tag][0]))
        if res["plain"][1] != res["ds"][1]:
            p.append("violations differ: %s vs %s" % (res["plain"][1], res["ds"][1]))
        out.append(("h_tol", eng, not p, "; ".join(p) if p else "exit 1 on both, same violations",
                    "§2 forward compatibility: a reader ignores `dependencySources`"))
    return out


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    print("=" * 100)
    print("DEPENDENCY SOURCES ⟨0.42⟩ — an unchained dependency's value typed from its own source: lock-pinned and")
    print("present only, adding only, every read recorded in `dependencySources`")
    print("  S arm : rust, a hermetic CARGO_HOME registry and a path dependency (java/ts/swift: N/A)")
    print("  H arm : one hand-written report with the key, four `gate --report`s (reader tolerance)")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the registry checkout is deleted and the H report's Net is removed,")
        print("       so pin_reg/twin/det and h_tol must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part108-")
    bad = 0
    rows = []
    try:
        engines = [e for e in G.ENGINES if G.present(e) and (only is None or e == only)]
        for e in G.ENGINES:
            if G.installed(e) and not G.alive(e) and (only is None or e == only):
                print("  %-6s -> BROKEN: installed but not responding" % e)
                bad += 1
        if not engines:
            print("DEP-SOURCES: no engine available — NOT a pass")
            return 2
        rows += run_h(engines, ws)
        if "rust" in engines:
            res, err = run_s(ws)
            if err:
                print("  rust   -> BROKEN S arm: %s" % err)
                bad += 1
            else:
                rows += res
        for cid, eng, ok, detail, why in rows:
            if ok:
                print("  OK    %-12s %-6s %s" % (cid, eng, detail))
            else:
                print("  FAIL  %-12s %-6s %s  [%s]" % (cid, eng, detail, why))
                bad += 1
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    if bad:
        print("DEP-SOURCES: %d cell(s) wrong — SPEC §2 ⟨0.42⟩ dependencySources" % bad)
        return 1
    print("DEP-SOURCES: OK — %d cell(s), %d engine(s)" % (len(rows), len(engines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
