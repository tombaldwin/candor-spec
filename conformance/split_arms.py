#!/usr/bin/env python3
"""
SHARED PLUMBING for the self-differential properties that vary the CHAINED INPUT rather than the program.

P1 (`gen_split_invariance.py`) varies the PROGRAM's partitioning and holds the chain fixed. P2 and P3 do
the opposite: they hold ONE two-package rendering fixed and vary what is handed to the consumer on
`CANDOR_DEPS`. That is the same three-step dance in both — render the split, scan the dep half once, then
scan the app half N times against N different dep-directory contents — so it lives here once instead of
being written out twice per engine.

WHAT THIS MODULE DELIBERATELY DOES NOT CONTAIN: any statement about what an effect SHOULD be. Every
property built on it compares one arm against another arm of the same engine. The moment a table of
expected values appears in a file that imports this one, that file has stopped being a self-differential.
(See the header of gen_split_invariance.py at length.)

THE CELL VOCABULARY IS P1'S, ON PURPOSE. `SPLITS` (10 shapes) and `gen_differential.EFFECTS` (8 effects)
are imported, not copied, so the matrix stays defined in ONE place — the same reason P1 imports EFFECTS
from gen_differential rather than restating it. A shape added for P1 is automatically tested by P2 and P3.

ISOLATION RULES, both of them learned the hard way and both enforced structurally rather than by care:
  * every arm scans its OWN copy of the app tree, made with `.candor` EXCLUDED, so no arm can read another
    arm's report or the dep half's (standing bar item 7: delete the output before you measure a control);
  * the dep half is scanned in a THIRD copy, so the pristine base never acquires a `.candor` directory
    that a later copy could inherit.

RC IS RECORDED, NOT JUST THE REPORT. An arm that produces no report because the engine REFUSED the input
(exit != 0, e.g. candor-java on an unparseable dep report) is a legitimate, fail-closed outcome and must
be reported as REFUSED. An arm that produces no report while exiting ZERO is the harness being broken, and
must be reported as such — otherwise a mis-invocation reads as good engine behaviour, which is the exact
shape of defect P1's own harness had (a mistyped `--only` printing a substantive-sounding finding).
"""
import json
import os
import shutil

import gen_differential as gd
import gen_split_invariance as p1

UNKNOWN = "Unknown"


# =====================================================================================================
# CELLS. Same 8 effects x 10 split shapes as P1, with a per-property entry-fn prefix so a report from one
# property is never mistaken for another's.
# =====================================================================================================
def build_cells(prefix, only=None):
    cells = []
    for sp in p1.SPLITS:
        if only and sp["id"] not in only:
            continue
        for eff in gd.EFFECTS:
            name = f"{prefix}_{eff['id']}_{sp['id']}"
            cells.append(dict(name=name, effect=eff["effect"], effect_id=eff["id"],
                              split=sp["id"], code=sp["render"](eff, name, eff["id"])))
    return cells


def split_ids(only=None):
    return [sp["id"] for sp in p1.SPLITS if not only or sp["id"] in only]


# =====================================================================================================
# READING A REPORT. Richer than gen_differential.leaf_set, because both properties need the DISCLOSURE
# channels and not just `inferred`:
#
#   eff       -- the concrete effects (inferred minus Unknown)
#   unknown   -- whether `Unknown` is present            } the two channels in which an engine can say
#   invisible -- the per-entry kappa coverage ledger     } "there is something here I could not see"
#
# BOTH CHANNELS COUNT AS DISCLOSURE, and that is a measured decision, not a stylistic one. candor-rust and
# candor-ts, handed an unparseable dep report, drop the inherited effects AND record the package in
# `invisible` + the report-level `coverage.uncovered` -- byte-identical to the answer they give with no
# dep report at all, which is the CORRECT trust semantics (an unusable report contributes nothing). A
# property that counted only `Unknown` as disclosure would file that as a cardinal loss on two engines.
# The channels are still tracked SEPARATELY because they are not equally strong: `deny E Unknown` bites on
# one and not the other, so a move from Unknown to kappa is a gate-visible weakening worth counting.
# =====================================================================================================
def leaf_info(path, seps):
    """{leaf-fn-name -> {eff, unknown, invisible, why}} plus a report-level ('' key) coverage summary.

    ⟨0.28⟩ Returns (None, None) on a ⟨0.21⟩ Row-1 fail-closed manifest-carrying empty at `path` — the
    shape ⟨0.28⟩ arming leaves at a `--json <file>` sink when the scan exits before producing a real
    report. Before that rung, a failed scan left NO file and the caller keyed on `os.path.exists`; with
    arming, the file always exists and the caller has to key on the content. Row 1 pins the reading:
    `analyzed.count == 0` + `functions == []` is *nothing was judged*, not *nothing to judge*, and a
    consumer that reads it as a real report is exactly the fabrication mirror this rung exists to close.
    """
    with open(path) as f:
        d = json.load(f)
    fns = d["functions"] if isinstance(d, dict) else d
    if isinstance(d, dict):
        analyzed = d.get("analyzed") or {}
        count = analyzed.get("count")
        if isinstance(count, int) and count == 0 and not fns and (d.get("unanalyzed") or []):
            return None, None
    out = {}
    for e in fns:
        n = e["fn"]
        for s in seps:
            n = n.split(s)[-1]
        inf = set(e.get("inferred", []))
        out[n] = dict(eff=frozenset(inf - {UNKNOWN}),
                      unknown=UNKNOWN in inf,
                      invisible=frozenset(e.get("invisible", []) or []),
                      why=frozenset(e.get("unknownWhy", []) or []))
    cov = d.get("coverage", {}) if isinstance(d, dict) else {}
    uncovered = frozenset(u.get("name", "?") for u in (cov.get("uncovered") or []))
    return out, uncovered


def hedged(info):
    """Does this entry disclose a hole AT ALL, in either channel? The predicate is deliberately a
    BOOLEAN and not a set-inclusion test: a report that moves a hole from the `Unknown` channel to the
    kappa channel has changed HOW it discloses, not WHETHER, and a set test would file that as a lost
    disclosure. The channel change is counted separately (see the callers)."""
    return bool(info["unknown"] or info["invisible"])


# =====================================================================================================
# THE ARMS. `arms` is an ordered list of (name, mk_deps) where mk_deps(dep_report_path, scratch_dir)
# returns the CANDOR_DEPS value for that arm (SPEC 3.4: whitespace-separated report paths). The FIRST arm
# is the reference: every property here compares the others against it.
# =====================================================================================================
def arm_env(mk, dep, scratch):
    """mk returning None means UNSET CANDOR_DEPS — the honest way to render 'chained with nothing at
    all', which is a reference arm for P3 and must not be faked with an empty string (an engine is
    entitled to treat `CANDOR_DEPS=""` as a malformed setting, and then the arm would be measuring the
    engine's tolerance for blank env vars rather than its unchained behaviour)."""
    v = mk(dep, scratch)
    env = dict(os.environ)
    if v is None:
        env.pop("CANDOR_DEPS", None)
    else:
        env["CANDOR_DEPS"] = v
    return env


class ArmResult:
    __slots__ = ("leaves", "uncovered", "rc", "note")

    def __init__(self, leaves, uncovered, rc, note=""):
        self.leaves, self.uncovered, self.rc, self.note = leaves, uncovered, rc, note

    @property
    def refused(self):
        return self.leaves is None and self.rc != 0

    @property
    def broken(self):
        return self.leaves is None and self.rc == 0


def _copy_tree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True,
                    ignore=shutil.ignore_patterns(".candor"))


def _pick(d, **kw):
    return p1._report(d, **kw)


# ---- rust ------------------------------------------------------------------------------------------
def _rust(root, cells, arms):
    binp = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
    if not os.path.exists(binp):
        return None, "no candor-scan at %s" % binp
    base = os.path.join(root, "base")
    p1.write_rust(base, cells)
    depsrc = os.path.join(base, "split")
    scratch = os.path.join(root, "scratch")
    os.makedirs(scratch, exist_ok=True)
    ds = os.path.join(root, "depscan")
    _copy_tree(depsrc, ds)
    gd.run([binp, "."], cwd=os.path.join(ds, "deplib"))
    dp = _pick(os.path.join(ds, "deplib", ".candor"), suffix=".scan.json")
    if not dp:
        return None, "rust dep scan produced no report"
    out = {}
    for name, mk in arms:
        d = os.path.join(root, "arm_" + name)
        _copy_tree(depsrc, d)
        r = gd.run([binp, "."], cwd=os.path.join(d, "app"), env=arm_env(mk, dp, scratch))
        rp = _pick(os.path.join(d, "app", ".candor"), suffix=".scan.json")
        out[name] = ArmResult(*(leaf_info(rp, ("::",)) if rp else (None, None)), rc=r.returncode,
                              note=r.stderr.decode()[:200].replace("\n", " | "))
    return (out, dp), None


# ---- java ------------------------------------------------------------------------------------------
def _java(root, cells, arms):
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None
    if not jar or not os.path.exists(jar):
        return None, "no candor-java jar"
    if not shutil.which("javac"):
        return None, "no javac on PATH"
    p1.write_java(root, cells)
    allcls = os.path.join(root, "classes")
    os.makedirs(allcls, exist_ok=True)
    c = gd.run(["javac", "-nowarn", "-d", allcls,
                os.path.join(root, "src", "dep", "Dep.java"), os.path.join(root, "src", "app", "App.java")])
    if c.returncode != 0:
        return None, "javac failed: %s" % c.stderr.decode()[:400]
    depd, appd = os.path.join(root, "jdep"), os.path.join(root, "japp")
    os.makedirs(depd, exist_ok=True)
    os.makedirs(appd, exist_ok=True)
    shutil.copytree(os.path.join(allcls, "dep"), os.path.join(depd, "dep"), dirs_exist_ok=True)
    shutil.copytree(os.path.join(allcls, "app"), os.path.join(appd, "app"), dirs_exist_ok=True)
    scratch = os.path.join(root, "scratch")
    os.makedirs(scratch, exist_ok=True)
    dj = os.path.join(root, "dep.json")
    gd.run(["java", "-jar", jar, depd, "--json", dj])
    if not os.path.exists(dj):
        return None, "candor-java dep scan produced no report"
    out = {}
    for name, mk in arms:
        aj = os.path.join(root, "app_%s.json" % name)
        if os.path.exists(aj):
            os.remove(aj)          # never let a previous arm's file be read as this arm's answer
        r = gd.run(["java", "-jar", jar, appd, "--json", aj], env=arm_env(mk, dj, scratch))
        ok = os.path.exists(aj)
        out[name] = ArmResult(*(leaf_info(aj, (".",)) if ok else (None, None)), rc=r.returncode,
                              note=r.stderr.decode()[:200].replace("\n", " | "))
    return (out, dj), None


# ---- ts --------------------------------------------------------------------------------------------
def _ts(root, cells, arms):
    ts_dir = gd.CANDOR_TS
    if not shutil.which("node") or not os.path.exists(os.path.join(ts_dir, "scan.mjs")):
        return None, "no node / scan.mjs"
    if not os.path.isdir(os.path.join(ts_dir, "node_modules")):
        gd.run(["npm", "install", "--no-fund", "--no-audit"], cwd=ts_dir)
    base = os.path.join(root, "base")
    p1.write_ts(base, cells)
    depsrc = os.path.join(base, "split")
    scratch = os.path.join(root, "scratch")
    os.makedirs(scratch, exist_ok=True)
    ds = os.path.join(root, "depscan")
    _copy_tree(depsrc, ds)
    gd.run(["node", "scan.mjs", os.path.join(ds, "deplib")], cwd=ts_dir)
    dp = os.path.join(ds, "deplib", ".candor", "report.json")
    if not os.path.exists(dp):
        return None, "ts dep scan produced no report"
    out = {}
    for name, mk in arms:
        d = os.path.join(root, "arm_" + name)
        _copy_tree(depsrc, d)
        r = gd.run(["node", "scan.mjs", os.path.join(d, "app")], cwd=ts_dir,
                   env=arm_env(mk, dp, scratch))
        rp = os.path.join(d, "app", ".candor", "report.json")
        ok = os.path.exists(rp)
        out[name] = ArmResult(*(leaf_info(rp, (".",)) if ok else (None, None)), rc=r.returncode,
                              note=r.stderr.decode()[:200].replace("\n", " | "))
    return (out, dp), None


# ---- swift -----------------------------------------------------------------------------------------
def _swift(root, cells, arms):
    if not shutil.which("swift") or not os.path.exists(os.path.join(gd.CANDOR_SWIFT, "Package.swift")):
        return None, "no swift toolchain"
    binp = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if not os.path.exists(binp):
        b = gd.run(["swift", "build"], cwd=gd.CANDOR_SWIFT)
        if b.returncode != 0 or not os.path.exists(binp):
            return None, "swift build failed"
    base = os.path.join(root, "base")
    p1.write_swift(base, cells)
    depsrc = os.path.join(base, "split")
    scratch = os.path.join(root, "scratch")
    os.makedirs(scratch, exist_ok=True)
    ds = os.path.join(root, "depscan")
    _copy_tree(depsrc, ds)
    gd.run([binp, "."], cwd=os.path.join(ds, "deplib"))
    dp = _pick(os.path.join(ds, "deplib", ".candor"), exclude=("callgraph", "hierarchy"), suffix=".Swift.json")
    if not dp:
        return None, "swift dep scan produced no report"
    out = {}
    for name, mk in arms:
        d = os.path.join(root, "arm_" + name)
        _copy_tree(depsrc, d)
        r = gd.run([binp, "."], cwd=os.path.join(d, "app"), env=arm_env(mk, dp, scratch))
        rp = _pick(os.path.join(d, "app", ".candor"), exclude=("callgraph", "hierarchy"), suffix=".Swift.json")
        out[name] = ArmResult(*(leaf_info(rp, (".",)) if rp else (None, None)), rc=r.returncode,
                              note=r.stderr.decode()[:200].replace("\n", " | "))
    return (out, dp), None


ENGINES = [("rust", _rust), ("java", _java), ("ts", _ts), ("swift", _swift)]

ABSENT_MARKERS = ("no candor-scan", "no candor-java jar", "no javac", "no node / scan.mjs",
                  "no swift toolchain")


def engine_absent(err):
    return any(m in err for m in ABSENT_MARKERS)


# =====================================================================================================
# DEP-REPORT MUTATORS, shared by P2 and P3. Each takes the produced dep report and writes a DERIVED file
# into the scratch dir; none of them touches the original, so the reference arm is never contaminated.
# =====================================================================================================
def _load(p):
    with open(p) as f:
        return json.load(f)


def copy_as(src, scratch, name):
    dst = os.path.join(scratch, name)
    shutil.copyfile(src, dst)
    return dst


def reserialise(src, scratch, name):
    """Byte-DIFFERENT, semantically identical: sorted keys, different indent. This is the spelling that
    separates an engine which dedupes on file bytes from one which is genuinely idempotent — the real
    duplicate in a dep directory is the same package scanned twice, not a `cp`."""
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        json.dump(_load(src), f, sort_keys=True, indent=1)
    return dst


def with_version(src, scratch, name, version):
    d = _load(src)
    d.setdefault("candor", {})["version"] = version
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        json.dump(d, f)
    return dst


def without_version(src, scratch, name):
    d = _load(src)
    d.setdefault("candor", {}).pop("version", None)
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        json.dump(d, f)
    return dst


def with_unanalyzed(src, scratch, name):
    d = _load(src)
    d["unanalyzed"] = [{"path": "src/never_read.src",
                        "reason": "conformance: forced <0.21> incompleteness"}]
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        json.dump(d, f)
    return dst


def emptied(src, scratch, name, zero_count):
    """A report that lists NO functions. The two spellings are the whole point, and the difference is
    ⟨0.21⟩'s `analyzed.count`:

      zero_count=True   `functions: []`, `analyzed.count: 0`  -- "I judged nothing here." Every call into
                        the package lands on a unit that was never analyzed, so absence carries NO purity
                        claim. This is the real shape: a facade crate of pure re-exports scans to exactly
                        this (MEASURED — candor-scan on a `pub use`-only crate emits count 0, and on an
                        all-pure two-function crate emits count 2, so the wire CAN express the difference).
      zero_count=False  `functions: []`, `analyzed.count` left as produced -- "I judged N units and none of
                        them has an effect." That is a legitimate positive purity claim and §2's chaining
                        rule 3 says a consumer SHOULD believe it ("an all-pure dependency's empty report is
                        a claim, not a blind spot").

    They are byte-identical apart from that one integer, which is why the second is carried as a NEGATIVE
    CONTROL rather than an assertion: if a property failed both, it would be failing "the report is empty"
    and not "the report claims nothing", and the fix it demanded would break the chaining rule."""
    d = _load(src)
    if isinstance(d, dict):
        d["functions"] = []
        if zero_count:
            d.setdefault("analyzed", {})["count"] = 0
    else:
        d = []
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        json.dump(d, f)
    return dst


def truncated(src, scratch, name):
    with open(src) as f:
        text = f.read()
    dst = os.path.join(scratch, name)
    with open(dst, "w") as f:
        f.write(text[: max(1, len(text) // 2)])
    return dst


# =====================================================================================================
# RUNNING ONE ENGINE'S WHOLE MATRIX. Returns (per_split_arms, dep_paths, err) where per_split_arms is
# {split_id: {arm_name: ArmResult}}.
# =====================================================================================================
def run_engine(eng, runner, ws, by_split, arms):
    per_split, deps = {}, {}
    for sid, cs in sorted(by_split.items()):
        root = os.path.join(ws, eng, sid)
        os.makedirs(root, exist_ok=True)
        res, err = runner(root, cs, arms)
        if err:
            return None, None, "%s: %s" % (sid, err)
        per_split[sid], deps[sid] = res[0], res[1]
    return per_split, deps, None


def dep_stats(path):
    """(entries, effectful entries) straight off the RAW dep report — the answer to 'is the witness even
    IN the dependency's report?'. A leaf-keyed map would collapse every cell's `W.run` onto one key and
    silently under-count (P1 hit exactly that)."""
    try:
        d = _load(path)
    except Exception:
        return (0, 0)
    fns = d["functions"] if isinstance(d, dict) else d
    return (len(fns), sum(1 for e in fns if set(e.get("inferred", [])) - {UNKNOWN}))
