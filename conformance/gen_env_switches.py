#!/usr/bin/env python3
"""PART 109 — RESULT-MOVING SWITCHES, SPEC §2 `switches` / §3.4 / §3.3 cause (e), ⟨0.42⟩.

SOUNDNESS R1634. Every engine's released binary honours undocumented environment variables that restore closed
defects or turn on opt-in modes. MEASURED on candor-scan 0.41.3: `CANDOR_R1608_OFF=1` removes `c_let_chain` from
`functions[]`, every top-level key stays byte-equal, `"spec"` stays `0.41`, and `deny Fs c_let_chain` goes from exit 1
to exit 0. The clause: the report names every switch that was SET and CONSULTED (`switches`), `spec` is unchanged, a
gate under a set switch (its own environment, or the report it judges) is a §3.1 refusal at exit 2, and a CHAINED
report carrying `switches` gets an advisory with the exit untouched.

ONE REAL SWITCH PER ENGINE, on a fixture where it demonstrably moves a result (each engine's own measured example):

  rust   CANDOR_R1608_OFF   a let-bound chain `H::new().find().filter(1)` then `.all()`: with the switch, c_let_chain
                            (which reaches an Fs write through `F::all`) is ABSENT from functions[]
  java   CANDOR_R1304       the PRODUCER's `dispatchesOn` key on a formatting member (`ArrayConverter.toString` calls
                            `elem.toString()` on a package-owned interface): with the switch the producer row is gone
                            and a chained consumer's `deny Fs app.App.c_call` goes from exit 1 to exit 0
  ts     CANDOR_CT2_OFF     destructuring a property of an interface-typed parameter: `destrIface` loses its Fs
  swift  CANDOR_R1032_OFF   `[1,2,3].shuffled()` draws entropy: `mixAll` loses its Rand

CELLS (per engine unless stated; `w` = the switch arm, `u` = the unset arm):

  live          HARNESS CHECK, never an xfail: the unit present in `u` is ABSENT in `w`. A switch that moved nothing
                would make every cell below read a pre-rung engine as conforming or as failing for the wrong reason.
  two_sw        rust only: CANDOR_R1494_OFF (read at six sites) beside CANDOR_R1608_OFF: `switches` is the two names, code-point
                sorted, each once. If a port reads R1494 lazily and this fixture never reaches the read, the lane moves
                the fixture, not the clause.
  c_report      (c) a refused policy run with a report sink STILL WRITES its report, carrying `switches`.
  h_env         `gate --report` with a scan-time switch in ITS environment over a clean report judges it (exit 1, no
                refusal): an evaluator that ran no analysis consulted nothing, and an engine must not read eagerly.
  h_verb        the advisory verb `unverified --report` over the switched report exits 2 (plain: not 2).
  d_key         (d) the consumer's verdict carries `switchedDependencies` naming the package and the switch.
  ctl_plain     `u`: no `switches` key, the firing policy exits 1, no refusal document. Passes today.
  a_named       (a) `w`'s report carries `switches` == [<NAME>] exactly.
  b_spec        (b) `w`'s `candor.spec` equals `u`'s. A guard against a fix that "marks" the report by changing `spec`.
  c_scan        (c)(i) the policy run with the switch in its OWN environment exits 2 with the §3.1 refusal document
                (`ok:false`, `refused:true`, NO `violations`) carrying `switches` == [<NAME>].
  unconsulted   `CANDOR_R0_OFF=1`, a prefixed name no engine consults: no `switches` key, the policy still exits 1. The
                row that makes "dump every CANDOR_ variable" a failure rather than a pass.
  default_val   java only: `CANDOR_R1304=1` equals unset for that engine, so it is not SET (§3.4 (a)): no key.
  h_ctl / h_ref (c)(ii) FOUR-WAY, one hand-written report through each engine's `gate --report`: the plain report
                exits 1 (control); the same report carrying `switches` exits 2 with the refusal document naming it.
  d_exit / d_adv (d) rust and java, CHAINED: a producer report carrying `switches` injected by hand, chained into a
                consumer whose policy fires. `d_exit`: the exit and the `--gate-json` document equal the plain chain's
                (untouched; passes today). `d_adv`: stderr names the switch (the advisory). ts and swift have no
                chained arm here (GAP, named in the run.sh header): ts needs an npm package layout and swift a SwiftPM
                dependency pair, and neither recipe exists in this suite outside PART 107's swift S arm.
  seed_a        calibration of `a_named`'s own checker, per engine: the unset report with `switches: [NAME]` INJECTED
                must pass it and the same report with the key DELETED must fail it, or the part is VACUOUS.
  seed_c        the same for the refusal checker behind `c_scan` and `h_ref`: a well-formed refusal passes, and a scored
                verdict, a `violations` key, no switch named, another switch named, or exit 1 each fail.

THE JAVA PROPERTY ARM (R1645, `jp_*`, java only): a JVM system property that moves a result (`candor.r1078=off`; the fixture's
`rfu.Cov$Base.getOptions` is absent unset and present under it) is a switch exactly as a variable is, so it is delivered
by `java -D…`, `JAVA_TOOL_OPTIONS` and `JDK_JAVA_OPTIONS`, and named as `candor.r1078` (no `-D`). `jp_live` is a harness
check (never an xfail); `jp_ctl`, `jp_spec`, `jp_unconsulted`, `jp_default_val`, `jp_two_ctl`, `jp_seed`, `jp_strip` pass
today; `jp_named_cmd/jto/jdk`, `jp_refuse_cmd/jto` and `jp_two` (`CANDOR_R1461=off` beside `-Dcandor.r1461=off`: both names,
sorted, once) are XFAIL citing R1645 until candor-java registers its properties. `strip_env` now drops the four JVM option
variables from every engine's environment, and the property arm sets them on the ENGINE process only (javac is a JVM too).

EVERY ENGINE FAILS a_named, c_scan, h_ref (and d_adv for rust and java) TODAY. They are XFAIL, keyed (cell, engine);
a PASSING xfail is a FAILURE, so the engine that lands its port reddens this part and retires its own lines in the same
commit. `live`, `ctl_plain`, `b_spec`, `unconsulted`, `default_val`, `h_ctl`, `d_exit`, `seed_a` and `seed_c` pass today and
must keep passing.

CALIBRATED: CANDOR_PROBE_FAULT=1 runs the switch arm WITHOUT the switch, so `live` reddens on every engine (it is a
harness check, never an xfail). Registered in probe_check.py (java arm).
"""
import glob
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
    ("§2 ⟨0.42⟩", "**the result-moving switches (§3.4) that were SET in the producing run's environment and CONSULTED by it**"),
    ("§2 ⟨0.42⟩", "**Omitted when empty**, so a scan under no switch is byte-identical to a pre-rung report."),
    ("§3.4 ⟨0.42⟩", "An ambient input whose value, as the engine reads it, can change any byte of a report or of a verdict: an environment variable, or any other channel the"),
    ("§3.4 ⟨0.42⟩", "**THE CLASS BINDS THE EFFECT, NOT THE CHANNEL.**"),
    ("§3.4 ⟨0.42⟩", "BY WHICHEVER ROUTE IT ARRIVED"),
    ("§2 ⟨0.42⟩", "the name the engine reads it by, with no launcher syntax (the JVM engine's `-Dcandor.r1078=off` is named `candor.r1078`)"),
    ("§3.4 ⟨0.42⟩", "A `CANDOR_`-prefixed variable the engine does not consult is therefore NOT listed"),
    ("§3.4 ⟨0.42⟩", "**(b) A REPORT THAT CARRIES IT IS NOT A CONFORMING REPORT OF ITS `spec`, AND `spec` IS NOT CHANGED.**"),
    ("§3.4 ⟨0.42⟩", "**(c) A GATE EVALUATED UNDER A SET SWITCH IS UNANSWERABLE: exit 2, the §3.1 refusal document, the fifth §3.3"),
    ("§3.4 ⟨0.42⟩", "`gate --report` over a report a switched scan produced refuses as `scan --policy` did"),
    ("§3.4 ⟨0.42⟩", "**(d) A GATE THAT CONSUMES A CHAINED REPORT CARRYING `switches` GETS THE ADVISORY SHAPE, AND ITS EXIT IS UNTOUCHED.**"),
    ("§3.3 ⟨0.42⟩", "⟨0.42⟩ **(e) A SET RESULT-MOVING SWITCH** (§3.4)"),
]

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
ENGINES = ["rust", "java", "ts", "swift"]

SWITCH = {"rust": "CANDOR_R1608_OFF", "java": "CANDOR_R1304", "ts": "CANDOR_CT2_OFF", "swift": "CANDOR_R1032_OFF"}
# How each engine reads its own switch (the value that SELECTS the non-default branch), measured on the 0.41.3 binaries.
SET_VALUE = {"rust": "1", "java": "0", "ts": "1", "swift": "1"}
UNIT = {"rust": "c_let_chain", "java": "convlib.ArrayConverter.toString", "ts": "src.a.destrIface", "swift": "mixAll"}
UNCONSULTED = "CANDOR_R0_OFF"
# rust only: a second switch read at six sites across three files (R1494), for the sorted / no-duplicates cell
SECOND_RUST = "CANDOR_R1474_OFF"  # a switch the RS_SRC fixture reaches (switches are read lazily; R1494 is never consulted here)

# An expectation keyed by (cell, engine). A PASSING XFAIL IS A FAILURE: the engine that lands its port reddens this
# part and retires its own lines in the same commit.
_A = "R1634 — the report names no switch: `switches` is absent although %s was set and consulted (the unit is gone)"
_C = "R1634 — a gate under a set switch scores the run (exit 1/0) instead of refusing with exit 2"
_H = "R1634 — `gate --report` over a report carrying `switches` judges it instead of refusing with exit 2"
_D = "R1634 — a chained report carrying `switches` is gated silently: no advisory names the switch on stderr"
XFAIL = {}
# Engines whose R1634 port has landed: their cells are pinned, not xfailed.
PORTED = {"ts", "java", "swift", "rust"}
for _e in [e for e in ENGINES if e not in PORTED]:
    XFAIL[("a_named", _e)] = _A % SWITCH[_e]
    XFAIL[("c_scan", _e)] = _C
    XFAIL[("h_ref", _e)] = _H
for _e in [e for e in ("rust", "java") if e not in PORTED]:
    XFAIL[("d_adv", _e)] = _D
    XFAIL[("d_key", _e)] = "R1634 — the consumer's verdict carries no `switchedDependencies`, so a machine consumer cannot see the chained input was switched"
for _e in [e for e in ENGINES if e not in PORTED]:
    XFAIL[("c_report", _e)] = "R1634 — the refused policy run's report does not carry `switches` (the report is where a harness attributes, and what gate --report is bound to answer over)"
    XFAIL[("h_verb", _e)] = "R1634 — `unverified --report` over a report carrying `switches` certifies it instead of refusing as the gate does (⟨0.33⟩ siblings)"


# The channels that carry a JVM `-D` system property to the engine without a visible flag (SPEC §3.4 ⟨0.42⟩, R1645). A
# coordinator's shell may hold any of them; an inherited `-Dcandor.…` would turn every unset arm into a switched one.
JVM_OPTION_VARS = ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "JAVA_OPTS")

# R1645 — the java property arm (`jp_*` cells). candor-java reads five `-Dcandor.*` JVM system properties that move
# results through no registering read, so none of them is named. XFAIL until the java port registers them.
_JP = "R1645 — a result-moving JVM system property is set and consulted but the report names no switch: `switches` is absent"
_JPC = "R1645 — a gate under a set JVM system property scores the run (exit 1/0) instead of refusing with exit 2"
XFAIL.update({("jp_named_cmd", "java"): _JP, ("jp_named_jto", "java"): _JP, ("jp_named_jdk", "java"): _JP,
              ("jp_refuse_cmd", "java"): _JPC, ("jp_refuse_jto", "java"): _JPC,
              ("jp_two", "java"): "R1645 — `-Dcandor.r1461=off` beside `CANDOR_R1461=off`: only the variable is named, the property twin of the same switch is not"})


def strip_env(extra=None):
    """The engine's environment: the harness's own, minus EVERY CANDOR_ variable (a switch inherited from the
    coordinator's shell would turn the unset arm into a switched one and read as a pre-rung engine)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CANDOR_") and k not in JVM_OPTION_VARS}
    env.update(extra or {})
    return env


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def run(cmd, env, cwd=None):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=cwd)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                       # noqa: BLE001
        return None


# =====================================================================================================
# FIXTURES — one per engine
# =====================================================================================================
RS_CARGO = '[package]\nname = "%s"\nversion = "0.1.0"\nedition = "2021"\n'
RS_SRC = """fn hit() { let _ = std::fs::write("/tmp/candor-part109-never-run", "x"); }
pub struct H;
pub struct F(u8);
impl H {
    pub fn new() -> Self { H }
    pub fn find(&self) -> F { F(0) }
}
impl F {
    pub fn filter(self, x: u8) -> Self { F(self.0 + x) }
    pub fn all(self) { hit() }
}
pub fn c_let_chain() { let f = H::new().find().filter(1); f.all() }
pub fn c_pure() -> u8 { 1 }
"""
RS_DEP = "pub fn run() { let _ = std::fs::write(\"/tmp/candor-part109-never-run\", \"x\"); }\n"
RS_APP = "pub fn go() { swdep::run() }\n"

TS_SRC = """import * as fs from "fs";
export interface G2 { readonly g: number; }
export class GC2 implements G2 { get g(): number { fs.writeFileSync("/tmp/candor-part109-never-run", "y"); return 1; } }
export function destrIface(x: G2) { const { g } = x; return g; }
"""

SW_SRC = "import Foundation\nfunc mixAll() -> [Int] { [1, 2, 3].shuffled() }\n"

J_CONV = "package convlib;\npublic interface Converter { String convert(String s); }\n"
J_ARR = ("package convlib;\npublic class ArrayConverter {\n  private final Converter elem;\n"
         "  public ArrayConverter(Converter e) { elem = e; }\n"
         "  @Override public String toString() { return \"AC[\" + elem.toString() + \"]\"; }\n}\n")
J_MY = ("package app;\npublic class MyConv implements convlib.Converter {\n  public String convert(String s) { return s; }\n"
        "  @Override public String toString() { new java.io.File(\"/tmp\").exists(); return \"MyConv\"; }\n}\n")
J_APP = ("package app;\nimport convlib.*;\npublic class App {\n"
         "  public static String c_call(ArrayConverter ac) { return ac.toString(); }\n}\n")

POLICY = {"rust": "deny Fs c_let_chain\n", "java": "deny Fs app.App.c_call\n", "ts": "deny Fs src.a.destrIface\n",
          "swift": "deny Rand mixAll\n"}


class Arm:
    """One engine's fixture and the two ways of running it. `report(env, tag)` scans for the REPORT only;
    `gate(env, tag, deps=None)` runs the policy route. Both return a dict with rc/err/doc/gdoc."""

    def __init__(self, eng, ws):
        self.eng, self.ws = eng, ws
        self.d = os.path.join(ws, eng)
        self.pol = os.path.join(self.d, "p.candor")
        w(self.pol, POLICY[eng])
        self.build()

    # ---- build ----
    def build(self):
        e, d = self.eng, self.d
        if e == "rust":
            w(os.path.join(d, "rs", "Cargo.toml"), RS_CARGO % "swfx")
            w(os.path.join(d, "rs", "src", "lib.rs"), RS_SRC)
            w(os.path.join(d, "dep", "Cargo.toml"), RS_CARGO % "swdep")
            w(os.path.join(d, "dep", "src", "lib.rs"), RS_DEP)
            w(os.path.join(d, "app", "Cargo.toml"), (RS_CARGO % "swapp") + '[dependencies]\nswdep = { path = "../dep" }\n')
            w(os.path.join(d, "app", "src", "lib.rs"), RS_APP)
            w(os.path.join(d, "chain.candor"), "deny Fs go\n")
        elif e == "ts":
            w(os.path.join(d, "ts", "package.json"), '{"name":"candorpart109","version":"1.0.0"}')
            w(os.path.join(d, "ts", "src", "a.ts"), TS_SRC)
        elif e == "swift":
            w(os.path.join(d, "sw", "cases.swift"), SW_SRC)
        else:
            for rel, txt in (("lib/convlib/Converter.java", J_CONV), ("lib/convlib/ArrayConverter.java", J_ARR),
                             ("app/app/MyConv.java", J_MY), ("app/app/App.java", J_APP)):
                w(os.path.join(d, "src", rel), txt)
            for sub in ("libcls", "appcls"):
                os.makedirs(os.path.join(d, sub), exist_ok=True)
            env = strip_env()
            rc, _o, err = run(["javac", "-nowarn", "-d", os.path.join(d, "libcls")] +
                              sorted(glob.glob(os.path.join(d, "src/lib/convlib/*.java"))), env)
            if rc:
                raise RuntimeError("javac (lib) failed: " + err[:300])
            rc, _o, err = run(["javac", "-nowarn", "-cp", os.path.join(d, "libcls"), "-d", os.path.join(d, "appcls")] +
                              sorted(glob.glob(os.path.join(d, "src/app/app/*.java"))), env)
            if rc:
                raise RuntimeError("javac (app) failed: " + err[:300])

    # ---- the report a scan wrote ----
    def _find(self, out_dir):
        e = self.eng
        c = sorted(glob.glob(os.path.join(out_dir, "*.json")))
        c = [p for p in c if not any(p.endswith(s) for s in (".callgraph.json", ".hierarchy.json", ".locs.json")) and os.path.basename(p) != "gate.json"]
        if e == "swift":
            c = [p for p in c if p.endswith(".Swift.json")]
        return c[0] if len(c) == 1 else None

    def _fresh(self, tag):
        od = os.path.join(self.d, "out", tag)
        shutil.rmtree(od, ignore_errors=True)
        os.makedirs(od)
        return od

    def _argv(self, od, policy, gj, deps_target=None, scan_dir=None):
        e = self.eng
        pfx = os.path.join(od, "r")
        tail = ["--policy", self.pol if policy is True else policy, "--gate-json", gj] if policy else []
        if e == "rust":
            return [G.rust_scan(), scan_dir or os.path.join(self.d, "rs"), "--out", pfx] + tail
        if e == "ts":
            return ["node", os.path.join(G.ts_root(), "scan.mjs"), os.path.join(self.d, "ts"), "--out", pfx] + tail
        if e == "swift":
            return [G.swift_bin(), os.path.join(self.d, "sw", "cases.swift"), "--out", pfx] + tail
        return ["java", "-jar", G.java_jar(), scan_dir, "--json", pfx + ".json"] + tail

    def switch_env(self, name=None, value=None):
        return {name or SWITCH[self.eng]: value if value is not None else SET_VALUE[self.eng]}

    def report(self, extra_env, tag):
        """Scan for the report alone. java: the PRODUCER (libcls), where the switch lives."""
        od = self._fresh(tag)
        e = self.eng
        scan_dir = os.path.join(self.d, "libcls") if e == "java" else None
        rc, _o, err = run(self._argv(od, None, None, scan_dir=scan_dir), strip_env(extra_env))
        rep = os.path.join(od, "r.json") if e == "java" else self._find(od)
        return {"rc": rc, "err": err, "path": rep, "doc": load(rep) if rep else None, "dir": od}

    def gate(self, extra_env, tag, producer_path=None):
        """The policy route. java gates the CONSUMER (appcls) chained over a producer report; the others scan
        their one tree. Returns rc/err/gdoc (the --gate-json document)."""
        od = self._fresh(tag)
        gj = os.path.join(od, "gate.json")
        e = self.eng
        env = dict(extra_env)
        if e == "java":
            env["CANDOR_DEPS"] = producer_path
            argv = self._argv(od, True, gj, scan_dir=os.path.join(self.d, "appcls"))
        else:
            argv = self._argv(od, True, gj)
        rc, _o, err = run(argv, strip_env(env))
        rep = os.path.join(od, "r.json") if e == "java" else self._find(od)
        return {"rc": rc, "err": err, "gdoc": load(gj) if os.path.exists(gj) else None,
                "rdoc": load(rep) if rep and os.path.exists(rep) else None}

    def chain(self, extra_env, tag, deps_path):
        """rust: the consumer crate gated over a dependency report handed on CANDOR_DEPS."""
        od = self._fresh(tag)
        gj = os.path.join(od, "gate.json")
        env = dict(extra_env, CANDOR_DEPS=deps_path)
        if self.eng == "rust":
            argv = self._argv(od, os.path.join(self.d, "chain.candor"), gj, scan_dir=os.path.join(self.d, "app"))
        else:
            argv = self._argv(od, True, gj, scan_dir=os.path.join(self.d, "appcls"))
        rc, _o, err = run(argv, strip_env(env))
        return {"rc": rc, "err": err, "gdoc": load(gj) if os.path.exists(gj) else None}


def rgate(eng, loc, policy_text, ws, tag, extra_env=None, verb="gate"):
    """`gate --report` (or `unverified --report`) with the environment STRIPPED of every CANDOR_ variable, like every
    other cell here (PS.gate inherits os.environ). Returns (rc, gate-json doc, stderr)."""
    pf = os.path.join(ws, "pol.%s" % tag)
    w(pf, policy_text)
    gj = os.path.join(ws, "%s.%s.gate.json" % (eng, tag))
    if os.path.exists(gj):
        os.remove(gj)
    if verb == "gate":
        base = {"rust": lambda: [G.rust_query(), "gate"], "java": lambda: ["java", "-jar", G.java_jar(), "gate"],
                "ts": lambda: ["node", os.path.join(G.ts_root(), "query.mjs"), "gate"],
                "swift": lambda: [G.swift_bin(), "gate"]}[eng]()
        cmd = base + ["--report", loc, "--policy", pf, "--gate-json", gj]
    else:
        cmd = G._unverified_cmd(eng, loc, pf)
    rc, _o, err = run(cmd, strip_env(extra_env))
    return rc, load(gj) if os.path.exists(gj) else None, err


def has_unit(doc, name):
    return any(f.get("fn") == name for f in (doc or {}).get("functions") or [])


# =====================================================================================================
# CHECKERS — each is applied to a REAL arm and to a seeded one
# =====================================================================================================
def check_a(doc, name):
    """(a): the report carries `switches` and it is exactly [name]."""
    return isinstance(doc, dict) and doc.get("switches") == [name]


def check_refusal(gdoc, rc, names):
    """(c): exit 2 and the §3.1 refusal document: `switches` == the sorted names, and a `reason` STRING naming each."""
    names = [names] if isinstance(names, str) else list(names)
    reason = gdoc.get("reason") if isinstance(gdoc, dict) else None
    return (rc == 2 and isinstance(gdoc, dict) and gdoc.get("ok") is False and gdoc.get("refused") is True
            and "violations" not in gdoc and gdoc.get("switches") == names
            and isinstance(reason, str) and all(n in reason for n in names))


def seed_report(doc, name, inject):
    d = json.loads(json.dumps(doc))
    if inject:
        d["switches"] = [name]
    else:
        d.pop("switches", None)
    return d


# =====================================================================================================
# THE CELLS
# =====================================================================================================
def producer_for_java(arm, tag, env):
    r = arm.report(env, tag)
    return r


def run_engine(eng, ws):
    rows = []
    name = SWITCH[eng]
    arm = Arm(eng, ws)

    def cell(cid, ok, detail, why):
        rows.append((cid, eng, ok, detail, why))

    sw_env = {} if FAULT else arm.switch_env()
    u = arm.report({}, "u")
    wr = arm.report(sw_env, "w")
    if u["doc"] is None or wr["doc"] is None:
        cell("live", False, "a scan wrote no report (u rc=%s, w rc=%s): %s" % (u["rc"], wr["rc"], (u["err"] or wr["err"])[:200]),
             "harness: the fixture did not scan")
        return rows
    # live: the switch must MOVE the unit, or nothing below measures anything.
    live = has_unit(u["doc"], UNIT[eng]) and not has_unit(wr["doc"], UNIT[eng])
    cell("live", live,
         "`%s` is %s unset and %s under %s=%s" % (UNIT[eng], "present" if has_unit(u["doc"], UNIT[eng]) else "ABSENT",
                                                  "present" if has_unit(wr["doc"], UNIT[eng]) else "absent", name, SET_VALUE[eng]),
         "harness: the switch must move a result on this fixture, or no cell below measures anything")
    if not live:
        return rows

    # the policy route. java: a consumer chained over the producer report.
    if eng == "java":
        gu = arm.gate({}, "gu", producer_path=u["path"])
        gw_move = arm.gate({}, "gwm", producer_path=wr["path"])     # the producer was switched, the consumer was not
        gc = arm.gate(arm.switch_env(), "gc", producer_path=u["path"])
        cell("live_gate", gu["rc"] == 1 and gw_move["rc"] == 0,
             "chained consumer: exit %s over the unswitched producer, exit %s over the switched one (expected 1 then 0)"
             % (gu["rc"], gw_move["rc"]),
             "harness: the switch moves a GATE, not only a row")
    else:
        gu = arm.gate({}, "gu")
        gc = arm.gate(arm.switch_env(), "gc")
    cell("ctl_plain", ("switches" not in u["doc"]) and gu["rc"] == 1 and not (gu["gdoc"] or {}).get("refused"),
         "unset arm: no `switches` key (%s), policy exit %s, refused=%s" % ("switches" not in u["doc"], gu["rc"],
                                                                         (gu["gdoc"] or {}).get("refused")),
         "control: today's output with no switch set")
    cell("a_named", check_a(wr["doc"], name), "switches = %r" % (wr["doc"].get("switches"),),
         "§3.4 (a): the report names a set and consulted switch")
    if eng == "rust":
        two = arm.report({SWITCH["rust"]: "1", SECOND_RUST: "1"}, "two")
        cell("two_sw", two["doc"] is not None and two["doc"].get("switches") == sorted([SWITCH["rust"], SECOND_RUST]),
             "two switches set: switches = %r (expected %r, sorted, each once although %s is read at several sites)"
             % ((two["doc"] or {}).get("switches"), sorted([SWITCH["rust"], SECOND_RUST]), SECOND_RUST),
             "§3.4 (a): sorted by code point, no duplicates")
    cell("b_spec", wr["doc"].get("candor", {}).get("spec") == u["doc"].get("candor", {}).get("spec"),
         "spec %r under the switch, %r unset" % (wr["doc"].get("candor", {}).get("spec"), u["doc"].get("candor", {}).get("spec")),
         "§3.4 (b): `spec` is not changed")
    cell("c_scan", check_refusal(gc["gdoc"], gc["rc"], name),
         "policy run under %s: exit %s, refused=%s, switches=%r" % (name, gc["rc"], (gc["gdoc"] or {}).get("refused"),
                                                                    (gc["gdoc"] or {}).get("switches")),
         "§3.4 (c)(i): a gate under a set switch is unanswerable")
    cell("c_report", check_a(gc.get("rdoc"), name),
         "refused policy run wrote a report: %s, switches=%r" % (gc.get("rdoc") is not None, (gc.get("rdoc") or {}).get("switches")),
         "§3.4 (c): a refused scan with a report sink still writes its report, carrying `switches`")
    un = arm.report({UNCONSULTED: "1"}, "un")
    ug = arm.gate({UNCONSULTED: "1"}, "ung", producer_path=u["path"]) if eng == "java" else arm.gate({UNCONSULTED: "1"}, "ung")
    cell("unconsulted", un["doc"] is not None and "switches" not in un["doc"] and ug["rc"] == 1,
         "%s=1: switches %s, policy exit %s" % (UNCONSULTED, "absent" if un["doc"] and "switches" not in un["doc"] else "PRESENT", ug["rc"]),
         "§3.4 (a): a prefixed name the engine never consults is not listed")
    if eng == "java":
        dv = arm.report({name: "1"}, "dv")
        cell("default_val", dv["doc"] is not None and "switches" not in dv["doc"],
             "%s=1 equals unset: switches %s" % (name, "absent" if dv["doc"] and "switches" not in dv["doc"] else "PRESENT"),
             "§3.4 (a): SET means the value selects a non-default branch")

    # seed_a — calibrate a_named's own checker, per engine
    inj, dele = seed_report(u["doc"], name, True), seed_report(wr["doc"], name, False)
    cell("seed_a", check_a(inj, name) and not check_a(dele, name),
         "injected passes=%s, key deleted fails=%s" % (check_a(inj, name), not check_a(dele, name)),
         "calibration: `a_named` can pass and can fail")

    # seed_c — calibrate the refusal checker the same way: a well-formed refusal passes, and each way a refusal can be
    # wrong (a scored verdict, a `violations` key, no switch named, a different switch) fails.
    good = {"spec": "0.42", "ok": False, "refused": True, "switches": [name],
            "reason": "a result-moving switch is set (%s): unset it and re-run" % name}
    bads = [(1, dict(good, ok=True, refused=False)), (2, dict(good, violations=[])), (2, {k: v for k, v in good.items() if k != "switches"}),
            (2, dict(good, switches=["CANDOR_OTHER"])), (2, {k: v for k, v in good.items() if k != "reason"}),
            (2, dict(good, reason="refused"))]
    seeded = check_refusal(good, 2, name) and not any(check_refusal(b, rc_, name) for rc_, b in bads) \
        and not check_refusal(good, 1, name)
    cell("seed_c", seeded, "well-formed refusal (with a reason) passes, %d malformed ones (incl. no reason) and exit 1 fail" % len(bads),
         "calibration: `c_scan` and `h_ref` can pass and can fail")

    # h arm — (c)(ii) over a hand-written report, four-way
    h = {"candor": {"version": "handwritten", "spec": "0.42"}, "package": "app", "analyzed": {"count": 1, "digest": "0"},
         "functions": [{"fn": "app.f", "hash": "app#app.f", "inferred": ["Fs"], "direct": ["Fs"]}]}
    hs = dict(h, switches=[name])
    loc = G.write_report(os.path.join(ws, "h-%s-plain" % eng), eng, h)
    rc0, doc0, _e0 = rgate(eng, loc, "deny Fs\n", ws, "h-%s-plain" % eng)
    locs = G.write_report(os.path.join(ws, "h-%s-sw" % eng), eng, hs)
    rc1, doc1, _e1 = rgate(eng, locs, "deny Fs\n", ws, "h-%s-sw" % eng)
    # the evaluator's own environment: a scan-time switch in `gate --report`'s environment, over a CLEAN report
    rce, doce, _ee = rgate(eng, loc, "deny Fs\n", ws, "h-%s-env" % eng, extra_env=arm.switch_env())
    cell("h_env", rce == 1 and not (doce or {}).get("refused"),
         "gate --report under %s over a clean report: exit %s, refused=%s" % (name, rce, (doce or {}).get("refused")),
         "§3.4 (a): an evaluator that never ran the analysis did not consult a scan-time switch (no eager reads)")
    # the advisory verbs follow the cause (⟨0.33⟩)
    rv0, _d0, _x0 = rgate(eng, loc, "deny Fs\n", ws, "v-%s-plain" % eng, verb="unverified")
    rv1, _d1, _x1 = rgate(eng, locs, "deny Fs\n", ws, "v-%s-sw" % eng, verb="unverified")
    cell("h_verb", rv0 != 2 and rv1 == 2, "unverified --report: plain exit %s, over the switched report exit %s" % (rv0, rv1),
         "§3.4 (c): the advisory verbs that answer `ok` refuse as the gate does")
    cell("h_ctl", rc0 == 1 and not (doc0 or {}).get("refused"), "plain hand-written report: exit %s" % rc0,
         "control: the same report without the key is judged and fails")
    cell("h_ref", check_refusal(doc1, rc1, name), "report carrying switches=[%s]: exit %s, refused=%s" % (name, rc1, (doc1 or {}).get("refused")),
         "§3.4 (c)(ii): the route that reads a report refuses it as the scan route did")

    # d arm — chained, rust and java
    if eng in ("rust", "java"):
        if eng == "rust":
            od = arm._fresh("dprod")
            rc, _o, err = run([G.rust_scan(), os.path.join(arm.d, "dep"), "--out", os.path.join(od, "swdep")], strip_env())
            reps = [p for p in glob.glob(os.path.join(od, "*.scan.json"))]
            base = reps[0] if reps else None
        else:
            base = u["path"]
        if not base or not os.path.exists(base):
            cell("d_exit", False, "no producer report to chain", "harness: the chained producer did not scan")
            return rows
        plain_dir, inj_dir = os.path.join(ws, "d-%s-plain" % eng), os.path.join(ws, "d-%s-inj" % eng)
        for dd in (plain_dir, inj_dir):
            shutil.rmtree(dd, ignore_errors=True)
            os.makedirs(dd)
        bn = os.path.basename(base)
        pdoc = load(base)
        for dd, inject in ((plain_dir, False), (inj_dir, True)):
            with open(os.path.join(dd, bn), "w") as fh:
                json.dump(seed_report(pdoc, name, inject), fh)
            for suf in (".callgraph.json", ".hierarchy.json"):
                sc = base[:-len(".json")] + suf
                if os.path.exists(sc):
                    shutil.copy(sc, os.path.join(dd, bn[:-len(".json")] + suf))
        cp = arm.chain({}, "dplain", os.path.join(plain_dir, bn))
        ci = arm.chain({}, "dinj", os.path.join(inj_dir, bn))
        live_join = cp["rc"] == 1
        strip = lambda g: {k: v for k, v in (g or {}).items() if k != "switchedDependencies"}   # noqa: E731
        cell("d_exit", live_join and ci["rc"] == cp["rc"] and strip(ci["gdoc"]) == strip(cp["gdoc"]),
             "plain chain exit %s, chain over a report carrying switches exit %s; documents equal but for `switchedDependencies`: %s"
             % (cp["rc"], ci["rc"], strip(ci["gdoc"]) == strip(cp["gdoc"])),
             "§3.4 (d): the exit and the rest of the verdict are untouched (and the join is live: the plain chain fires)")
        once = ci["err"].count(name) == 1
        plain_silent = name not in cp["err"]
        cell("d_adv", once and plain_silent,
             "stderr names %s %d time(s) (expected once); plain chain names it: %s" % (name, ci["err"].count(name), not plain_silent),
             "§3.4 (d): the advisory names the switch, once")
        sd = (ci["gdoc"] or {}).get("switchedDependencies")
        okd = isinstance(sd, list) and len(sd) == 1 and sd[0].get("switches") == [name] and isinstance(sd[0].get("package"), str) \
            and "switchedDependencies" not in (cp["gdoc"] or {})
        cell("d_key", okd, "verdict switchedDependencies = %r (absent on the plain chain: %s)" % (sd, "switchedDependencies" not in (cp["gdoc"] or {})),
             "§3.4 (d): a machine consumer of the verdict can see that a chained input was switched")
    return rows


# =====================================================================================================
# THE JAVA PROPERTY ARM (R1645) — a result-moving JVM system property is a switch exactly as a variable is
# =====================================================================================================
JP_PROP = "candor.r1078"
JP_UNIT = "rfu.Cov$Base.getOptions"
JP_SRC = """package rfu;
public class Cov {
  public interface Opts {}
  public static class ChatOpts implements Opts {}
  public interface Req { Opts getOptions(); }
  public static class Base implements Req { public ChatOpts getOptions() { return new ChatOpts(); } }
  public static class Sub extends Base { @Override public ChatOpts getOptions() {
    try { java.nio.file.Files.writeString(java.nio.file.Path.of("/tmp/candor-part109-never-run"), "x"); } catch (Exception e) { }
    return new ChatOpts(); } }
  public static boolean viaIface(Req r) { return r.getOptions() != null; }
  // a call on a generic collection owner whose project implementor has another type argument: the only thing that makes
  // the engine consult the R1461 generic-hedge switch
  public static class Ints extends java.util.AbstractList<Integer> {
    @Override public Integer get(int i) { return i; }
    @Override public int size() { return 0; } }
  public static int size(java.util.List<String> l) { return l.size(); }
}
"""


def run_java_props(ws):
    """A property the engine reads (`candor.r1078=off`: a covariant bridge's self-call is folded into its real member, so
    `Base.getOptions` inherits `Sub`'s Fs when it is OFF) delivered four ways: `java -D… -jar`, `JAVA_TOOL_OPTIONS`,
    `JDK_JAVA_OPTIONS`, and beside the env twin of a second switch. Every route is the SAME read in the engine, which is
    why SPEC §3.4 binds them alike. The property arm's environment reaches the ENGINE process only: javac is a JVM too."""
    rows = []

    def cell(cid, ok, detail, why):
        rows.append((cid, "java", ok, detail, why))

    d = os.path.join(ws, "jprop")
    w(os.path.join(d, "src", "rfu", "Cov.java"), JP_SRC)
    cls = os.path.join(d, "cls")
    os.makedirs(cls, exist_ok=True)
    rc, _o, err = run(["javac", "-nowarn", "-d", cls, os.path.join(d, "src", "rfu", "Cov.java")], strip_env())
    if rc:
        raise RuntimeError("javac (property fixture) failed: " + err[:300])
    pol = os.path.join(d, "p.candor")
    w(pol, "deny Fs %s\n" % JP_UNIT)

    def scan(tag, jvm=(), env=None, policy=False):
        od = os.path.join(d, "out", tag)
        shutil.rmtree(od, ignore_errors=True)
        os.makedirs(od)
        gj = os.path.join(od, "gate.json")
        argv = ["java"] + list(jvm) + ["-jar", G.java_jar(), cls, "--json", os.path.join(od, "r.json")]
        if policy:
            argv += ["--policy", pol, "--gate-json", gj]
        rc_, _o_, err_ = run(argv, strip_env(env))
        return {"rc": rc_, "err": err_, "doc": load(os.path.join(od, "r.json")), "gdoc": load(gj)}

    prop = [] if FAULT else ["-D%s=off" % JP_PROP]
    jto = {} if FAULT else {"JAVA_TOOL_OPTIONS": "-D%s=off" % JP_PROP}
    jdk = {} if FAULT else {"JDK_JAVA_OPTIONS": "-D%s=off" % JP_PROP}

    u = scan("u", policy=True)
    wc = scan("wc", jvm=prop, policy=False)
    wj = scan("wj", env=jto, policy=False)
    wk = scan("wk", env=jdk, policy=False)
    if None in (u["doc"], wc["doc"], wj["doc"], wk["doc"]):
        cell("jp_live", False, "a scan wrote no report: %s" % (u["err"] or wc["err"] or wj["err"] or wk["err"])[:200],
             "harness: the fixture did not scan")
        return rows
    present = lambda r: has_unit(r["doc"], JP_UNIT)   # noqa: E731
    live = (not present(u)) and present(wc) and present(wj) and present(wk)
    cell("jp_live", live, "`%s` is %s unset, %s under -D, %s under JAVA_TOOL_OPTIONS, %s under JDK_JAVA_OPTIONS" % (
        JP_UNIT, "present" if present(u) else "ABSENT", "present" if present(wc) else "absent",
        "present" if present(wj) else "absent", "present" if present(wk) else "absent"),
        "harness: the property must move a result by every route, or no jp_ cell measures anything")
    if not live:
        return rows
    cell("jp_ctl", "switches" not in u["doc"] and u["rc"] == 0 and not (u["gdoc"] or {}).get("refused"),
         "unset arm: no `switches` key (%s), policy exit %s, refused=%s" % ("switches" not in u["doc"], u["rc"], (u["gdoc"] or {}).get("refused")),
         "control: today's output with no property set")
    cell("jp_named_cmd", check_a(wc["doc"], JP_PROP), "java -D%s=off: switches = %r" % (JP_PROP, wc["doc"].get("switches")),
         "§3.4 (a): a property set on the command line is named, by the name the engine reads it by (no `-D`)")
    cell("jp_named_jto", check_a(wj["doc"], JP_PROP), "JAVA_TOOL_OPTIONS=-D%s=off: switches = %r" % (JP_PROP, wj["doc"].get("switches")),
         "§3.4 (a): the same property by JAVA_TOOL_OPTIONS is named alike: the engine cannot tell the routes apart")
    cell("jp_named_jdk", check_a(wk["doc"], JP_PROP), "JDK_JAVA_OPTIONS=-D%s=off: switches = %r" % (JP_PROP, wk["doc"].get("switches")),
         "§3.4 (a): and by JDK_JAVA_OPTIONS")
    cell("jp_spec", wc["doc"].get("candor", {}).get("spec") == u["doc"].get("candor", {}).get("spec"),
         "spec %r under the property, %r unset" % (wc["doc"].get("candor", {}).get("spec"), u["doc"].get("candor", {}).get("spec")),
         "§3.4 (b): `spec` is not changed")
    gc = scan("gc", jvm=prop, policy=True)
    gj = scan("gj", env=jto, policy=True)
    cell("jp_refuse_cmd", check_refusal(gc["gdoc"], gc["rc"], JP_PROP),
         "policy run under -D%s=off: exit %s, refused=%s, switches=%r" % (JP_PROP, gc["rc"], (gc["gdoc"] or {}).get("refused"), (gc["gdoc"] or {}).get("switches")),
         "§3.4 (c)(i): a gate under a set property is unanswerable")
    cell("jp_refuse_jto", check_refusal(gj["gdoc"], gj["rc"], JP_PROP),
         "policy run under JAVA_TOOL_OPTIONS: exit %s, refused=%s, switches=%r" % (gj["rc"], (gj["gdoc"] or {}).get("refused"), (gj["gdoc"] or {}).get("switches")),
         "§3.4 (c)(i): the same by the ambient route")
    # a property the engine does not read is not listed, and a property set to its default is not SET
    nn = scan("nn", jvm=["-Dcandor.nonesuch=off"], policy=True)
    cell("jp_unconsulted", nn["doc"] is not None and "switches" not in nn["doc"] and nn["rc"] == 0,
         "-Dcandor.nonesuch=off: switches %s, policy exit %s" % ("absent" if nn["doc"] and "switches" not in nn["doc"] else "PRESENT", nn["rc"]),
         "§3.4 (a): a property the engine never reads is not listed (a dump of the properties would bury the one that mattered)")
    dv = scan("dv", jvm=["-D%s=on" % JP_PROP], policy=True)
    cell("jp_default_val", dv["doc"] is not None and "switches" not in dv["doc"] and dv["rc"] == 0,
         "-D%s=on equals unset: switches %s, policy exit %s" % (JP_PROP, "absent" if dv["doc"] and "switches" not in dv["doc"] else "PRESENT", dv["rc"]),
         "§3.4 (a): SET means the value selects a branch other than the unset one")
    # two channels of ONE flag: the variable is read first, the property beside it. Both are SET and CONSULTED, so both are named.
    e1 = scan("e1", env={"CANDOR_R1461": "off"}, policy=False)
    e2 = scan("e2", jvm=["-Dcandor.r1461=off"], env={"CANDOR_R1461": "off"}, policy=False)
    want1, want2 = ["CANDOR_R1461"], ["CANDOR_R1461", "candor.r1461"]
    cell("jp_two_ctl", (e1["doc"] or {}).get("switches") == want1,
         "CANDOR_R1461=off alone: switches = %r (expected %r — proves the flag is consulted on this fixture)" % ((e1["doc"] or {}).get("switches"), want1),
         "control: the variable twin is already named, so jp_two is not vacuous")
    cell("jp_two", (e2["doc"] or {}).get("switches") == want2,
         "CANDOR_R1461=off beside -Dcandor.r1461=off: switches = %r (expected %r, code-point sorted, each once)" % ((e2["doc"] or {}).get("switches"), want2),
         "§3.4 (a): two names of one flag arrive by two channels; sorted by code point, no duplicates")
    # seeds — the same calibration as seed_a: the checker passes the right name, fails a deleted key and a launcher-syntax spelling
    inj, dele = seed_report(u["doc"], JP_PROP, True), seed_report(wc["doc"], JP_PROP, False)
    dash = seed_report(u["doc"], "-D" + JP_PROP, True)
    cell("jp_seed", check_a(inj, JP_PROP) and not check_a(dele, JP_PROP) and not check_a(dash, JP_PROP),
         "injected passes=%s, key deleted fails=%s, `-D`-prefixed name fails=%s" % (check_a(inj, JP_PROP), not check_a(dele, JP_PROP), not check_a(dash, JP_PROP)),
         "calibration: jp_named_* can pass, can fail, and refuse the launcher spelling")
    sv = {k: os.environ.get(k) for k in JVM_OPTION_VARS}
    try:
        for k in JVM_OPTION_VARS:
            os.environ[k] = "-Dcandor.seeded=1"
        leaked = [k for k in JVM_OPTION_VARS if k in strip_env()]
    finally:
        for k, v in sv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    cell("jp_strip", not leaked, "strip_env drops every JVM option channel (leaked: %r)" % (leaked,),
         "harness: an inherited JAVA_TOOL_OPTIONS must not turn an unset arm into a switched one")
    return rows


def main():
    argv = sys.argv[1:]
    only = argv[argv.index("--engine") + 1] if "--engine" in argv else None
    print("=" * 100)
    print("RESULT-MOVING SWITCHES ⟨0.42⟩ — a set and consulted switch is named in the report, `spec` is unchanged,")
    print("a gate under one refuses (exit 2), and a chained report carrying one gets an advisory")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the switch arm runs WITHOUT the switch, so `live` must go red.")
    ws = tempfile.mkdtemp(prefix="candor-part109-")
    bad = stale = 0
    rows = []
    engines = [e for e in ENGINES if G.present(e) and (only is None or e == only)]
    try:
        for e in ENGINES:
            if G.installed(e) and not G.alive(e) and (only is None or e == only):
                print("  %-6s -> BROKEN: installed but not responding" % e)
                bad += 1
        if not engines:
            print("ENV-SWITCHES: no engine available — NOT a pass")
            return 2
        for e in engines:
            try:
                rows += run_engine(e, ws)
            except Exception as ex:                     # noqa: BLE001
                print("  %-6s -> BROKEN: %s" % (e, ex))
                bad += 1
        if "java" in engines:
            try:
                rows += run_java_props(ws)
            except Exception as ex:                     # noqa: BLE001
                print("  %-6s -> BROKEN (property arm): %s" % ("java", ex))
                bad += 1
        nx = 0
        for cid, eng, ok, detail, why in rows:
            key = (cid, eng)
            if ok and key in XFAIL:
                print("  XFAIL CELL PASSED %-11s %-6s — expectation is STALE, retire it: %s" % (cid, eng, XFAIL[key]))
                stale += 1
            elif ok:
                print("  OK    %-11s %-6s %s" % (cid, eng, detail))
            elif key in XFAIL:
                print("  xfail %-11s %-6s %s  [%s]" % (cid, eng, detail, XFAIL[key]))
                nx += 1
            else:
                print("  FAIL  %-11s %-6s %s  [%s]" % (cid, eng, detail, why))
                bad += 1
    finally:
        shutil.rmtree(ws, ignore_errors=True)
    if bad or stale:
        print("ENV-SWITCHES: %d cell(s) wrong, %d xfail cell(s) PASSED — SPEC §3.4 ⟨0.42⟩ result-moving switches" % (bad, stale))
        return 1
    print("ENV-SWITCHES: OK — %d cell(s), %d engine(s), %d xfail (each names R1634)" % (len(rows), len(engines), nx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
