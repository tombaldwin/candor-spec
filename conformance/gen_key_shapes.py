#!/usr/bin/env python3
"""
ONE KEY NAME, ONE JSON TYPE — the query-document wire vocabulary, harvested and gated.

THE FAILURE THIS WAS BUILT FOR, as it happened (2026-08-12). The ⟨0.28⟩ re-disclosure MUST shipped
without pinning the travelling caveat's field name, and four engines guessed. Measured inside one day:

    rust    judgedNothing: [ "<report path>", … ]      java   judgedNothing: [ "<report path>", … ]
    swift   judgedNothing: [ "<report path>", … ]      ts     judgedNothing: true

and on `gains`, which rests on two reports, THREE answers: rust and swift emitted `baselineIncomplete`
alone, java added `baselineJudgedNothing` as an array, ts as a boolean. A consumer written against the
majority (`doc.judgedNothing.length`) throws on ts; one written against ts (`=== true`) silently misses
the other three. BOTH java and ts had green unit tests asserting their own side. No engine's suite can
see a cross-engine split, and the conformance row that should have was a keyword grep — shape-blind:
`grep` finds the key and never asks what TYPE sits after the colon. `grep -c judgedNothing SPEC.md` was
0 at the time; the key set is pinned now (SPEC §2 ⟨0.28⟩, "AND HERE IS WHAT THE TRAVELLING CAVEAT IS
CALLED").

TWO CHECKS, in order of strength:

  (A) CROSS-ENGINE SHAPE AGREEMENT — needs no spec at all. Every disclosure verb is driven on every
      engine over THE SAME hand-written report in four artifact states, and every key path observed in
      the machine documents is recorded with its JSON type. The same (verb, path) carrying two types is
      a contract break BY CONSTRUCTION — no clause needs to name the key for `judgedNothing: [...]` vs
      `judgedNothing: true` to fail here, on the day it appears. This is the primary check.

  (B) THE VOCABULARY RATCHET — an engine MINTING a machine-document key that SPEC.md never names is
      the upstream cause of (A), so it is gated too, but against a committed baseline: a key that is
      neither named in SPEC.md nor grandfathered in key-shapes-baseline.json FAILS. MEASURED on the
      four engines the day this was written: 7 of 55 vocabulary keys are SPEC-unnamed
      (`containmentPct`, `deniedSpan`, `hoistTo`, `layerPrefix`, `placement`, `policyAlternative`,
      `remedies` — the fix/containment output families). A hard no-baseline gate would therefore open
      with 7 standing failures on engines that agree with each other, and the project has a recorded
      precedent for what that buys (umbrella BACKLOG.md, the coverage-gap checker measured at 1 true
      positive to 8 permanent false positives and deliberately not built: an ignored checker is worse
      than none). So the 7 are grandfathered BY NAME, the ratchet fails on any NEW unpinned mint, and
      the baseline ratchets BOTH WAYS — a grandfathered key that becomes SPEC-named, or stops being
      emitted at all, is a STALE entry and fails, so the debt list cannot outlive the debt.

WHY THIS IS A SIBLING OF field_audit.py AND NOT AN EXTENSION OF IT. field_audit.py is deliberately a
REPORT: it asks which SPEC §2 report fields each engine emitted, where an engine legitimately omits a
field its fixture never provoked, and failing on absence would repeat the absence-is-a-claim error one
level up. That reasoning is preserved untouched — including here: (A) fails only on a key that IS
emitted with two shapes, never on a key one engine does not emit; candor-swift withholding a key while
rust emits it passes (A) by design, because presence-per-verb is ⟨0.28⟩ engine work still landing
(PART 39/40 own that surface, reference-led). What field_audit.py does not cover is QUERY output,
which is where the split above happened; this file covers exactly that, and gates only the two
properties that are never legitimately violated.

THE USER-NAMESPACE LINE — the hazard that decides the whole design. Some document positions are keyed
by the USER'S OWN NAMES, not by engine vocabulary: `map` keys its root object by module name,
`containment` keys `placement` by layer name. Treating those as minted vocabulary produces unbounded
false positives (every new fixture module a "new unpinned key") and an ignored gate. The line drawn:

  · USER_POSITIONS declares, per verb, the object positions whose keys are user data; keys there are
    masked to `*` for both checks (their VALUE shapes are still compared — masking collapses names,
    never types). Declaration, not inference — the umbrella BACKLOG records that inference measured
    1:8 on a neighbouring problem, and a declaration is checked both ways here: a NOSURF verb that
    starts answering fails loudly (below), and a masked position that vanishes simply stops matching.
  · EXCEPT the six ⟨0.28⟩-pinned caveat keys (incomplete/unanalyzed/judgedNothing and their
    baseline-prefixed forms), which are reserved vocabulary EVERYWHERE — measured: the engines emit
    them INTO map's module namespace, the very collision SPEC §2 ⟨0.28⟩ leaves as a known-open cell,
    so the gate must see them there or it is blind at the exact position the caveat travels.

MEASURED FALSE-POSITIVE COUNT with this line, on the real four-engine corpus, day one: (A) 0, (B) 0
beyond the 7 grandfathered. Without the mixed-namespace exception, (A) reports 2 phantom rows from
map's root; without USER_POSITIONS at all, every fixture module name becomes a (B) mint.

VERB COVERAGE is per-engine DECLARED, never probed-and-guessed: candor-swift ships only
{path, tour, gains, fix, fix-gate, unverified} of the disclosure verbs, and — measured — feeding it
`map` makes its CLI treat the token as a SCAN TARGET and print an armed placeholder REPORT to stdout
(exit 2), which harvested-as-`map`-output would hand (A) a fleet of phantom keys. The declaration is
checked in the strict direction: a declared-NOSURF cell that answers exit 0 with parseable JSON FAILS
as a stale declaration, so an engine gaining a verb is a one-line, forced update here.

ARTIFACT STATES. A key that only appears when an engine hedges is exactly the key that diverges, so an
intact-only corpus would have missed the ⟨0.28⟩ split entirely: intact; the ⟨0.21⟩ Row-1 armed
placeholder (functions: [], analyzed.count: 0, non-empty unanalyzed); judged-nothing-without-unanalyzed;
and a corrupt sibling report under the same locator prefix. `gains` runs on five (current, baseline)
pairings of those states, because its caveat keys are `baseline`-prefixed per side.

VACUITY GUARD, earned not asserted: the six pinned caveat keys must each be OBSERVED in the harvest
from at least two engines, or the run FAILS AS VACUOUS — a fixture drift that stops provoking the very
keys this gate was built for must never read as agreement. Same for an engine that produces no
document at all (reported ABSENT, never implied), and fewer than two live engines is a FAIL: an empty
table must never read as agreement.

KNOWN LIMITS, stated rather than implied: `reachable`'s `effects` object and `containment`'s `ambient`
are never populated by this fixture (no entry points), so their inner keying is declared user-data on
the conservative assumption; exit-2 refusals that print no machine document contribute nothing (this
gate audits documents, not refusal text); and the corrupt-sibling state only bites engines whose
locator expansion reads siblings — measured: rust and swift flag it, java's file locator cannot see it,
ts ignores it. Presence divergences the harvest surfaces (e.g. java `unverified` answering
`{"ok": true}` over a judged-nothing report with no caveat) are DELIBERATELY not gated here — that is
per-verb ⟨0.28⟩ engine work, reference-led in PART 39.

USAGE
    python3 gen_key_shapes.py --baseline key-shapes-baseline.json     # the gate (PART wiring)
    python3 gen_key_shapes.py --write-baseline                        # regenerate the grandfather list
    python3 gen_key_shapes.py --keep                                  # keep the workspace for autopsy

Runtime: ~6s on all four engines (212 cells; the JVM cells dominate).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict

# Registered in clause_check.py's GENERATORS, which then required this list — correctly, and the
# omission is worth recording because it is this file's own subject one level up: a property that
# enforces a contract without naming it is the same defect as a field that enters a machine document
# without a name. Caught the moment the generator was wired in, by the gate that runs the other way.
SPEC_CLAUSES = [
    ("§3.3.1 ⟨0.24⟩", "a field that enters a machine-consumed document MUST have its name and shape "
                      "stated here in the same rung that introduces it."),
    ("§2 ⟨0.28⟩",     "**`judgedNothing` is an ARRAY, not a boolean**"),
    ("§2 ⟨0.28⟩",     "A verb resting on TWO reports discloses both sides separately, "
                      "`baseline`-prefixed"),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def envdir(var, default_rel):
    return os.environ.get(var, os.path.normpath(os.path.join(HERE, default_rel)))


CANDOR       = envdir("CANDOR",       "../../candor-rust")
CANDOR_JAVA  = envdir("CANDOR_JAVA",  "../../candor-java")
CANDOR_TS    = envdir("CANDOR_TS",    "../../candor-ts")
CANDOR_SWIFT = envdir("CANDOR_SWIFT", "../../candor-swift")

SPEC_MD = os.path.normpath(os.path.join(HERE, "..", "SPEC.md"))
DEFAULT_BASELINE = os.path.join(HERE, "key-shapes-baseline.json")


def rust_query():
    b = os.environ.get("CANDOR_QUERY_BIN") or os.path.join(CANDOR, "target", "debug", "candor-query")
    return b if os.path.exists(b) else None


def java_jar():
    j = os.environ.get("CANDOR_JAVA_JAR")
    if j and os.path.exists(j):
        return j
    d = os.path.join(CANDOR_JAVA, "build", "libs")
    c = [os.path.join(d, f) for f in os.listdir(d)] if os.path.isdir(d) else []
    c = [p for p in c if p.endswith("-all.jar")]
    return max(c, key=os.path.getmtime) if c else None


def ts_root():
    return CANDOR_TS if (shutil.which("node") and os.path.exists(os.path.join(CANDOR_TS, "query.mjs"))) else None


def swift_bin():
    for kind in ("debug", "release"):
        b = os.path.join(CANDOR_SWIFT, ".build", kind, "candor-swift")
        if os.path.exists(b):
            return b
    return None


ENGINES = ["rust", "java", "ts", "swift"]

# One report, four spellings — each engine discovers reports by its OWN naming convention (§3.3.1/§2.2).
STEM    = {"rust": "report.app.scan", "java": "r",      "ts": "r",         "swift": "r.app.Swift"}
LOCATOR = {"rust": "report",          "java": "r.json", "ts": "r",         "swift": "r"}
# The corrupt SIBLING under the same locator prefix. Measured: rust and swift read it (and disclose);
# java's file locator cannot see a sibling at all, ts's expansion ignores it. Written for all four
# anyway so an engine that STARTS reading siblings is exercised the day it does.
SIBLING = {"rust": "report.dep.scan", "java": "r.dep",  "ts": "r.dep",     "swift": "r.dep.Swift"}

# The shared fixture: enough effect variety that every disclosure verb has something to say —
# Fs/Exec/Net with hosts+netClass+cmds+paths, an Unknown with a reason class (blindspots, unverified),
# a two-hop call chain (path/tour/callers/impact), a `deny Exec` crossing (fix/fix-gate).
INTACT = {
    "candor": {"version": "handwritten", "toolchain": "stable", "spec": "0.27"},
    "package": "app",
    "analyzed": {"count": 5, "digest": "0"},
    "functions": [
        {"fn": "app.reads", "hash": "app#reads", "inferred": ["Fs"], "direct": ["Fs"],
         "fs": ["read"], "paths": ["/tmp/a"]},
        {"fn": "app.spawns", "hash": "app#spawns", "inferred": ["Exec", "Net"],
         "direct": ["Exec", "Net"], "cmds": ["curl"], "hosts": ["example.com:443"],
         "netClass": ["known-host"]},
        {"fn": "app.disp", "hash": "app#disp", "inferred": ["Unknown"], "direct": ["Unknown"],
         "unknownWhy": ["dispatch:app.Base.run"]},
        {"fn": "app.top", "hash": "app#top", "inferred": ["Exec", "Fs", "Net"],
         "calls": ["app.reads", "app.spawns"], "fs": ["read"], "cmds": ["curl"],
         "hosts": ["example.com:443"], "netClass": ["known-host"], "paths": ["/tmp/a"]},
        {"fn": "app.main", "hash": "app#main", "inferred": ["Exec", "Fs", "Net"],
         "calls": ["app.top"]},
    ],
}
CG = {e["fn"]: e.get("calls", []) for e in INTACT["functions"]}

# ⟨0.28⟩ `nomanifest` IS THE FOURTH HEDGING STATE, and its absence was a measured coverage gap rather
# than an oversight of taste. SPEC §2 ⟨0.24⟩'s table has THREE rows and this corpus carried two of them:
# `count: 0` (row 1) and a healthy report (row 2). A report with NO `analyzed` key — row 3, the
# pre-⟨0.21⟩ producer — never appeared, so when all four engines gained `noManifest` and derived
# `baselineNoManifest` from it mechanically, check (B) reported ZERO SPEC-unnamed keys while a key named
# nowhere in SPEC.md was being emitted four-way. The check was sound; it could not provoke the state.
# An instrument's FIXTURES are part of its coverage.
STATES = ["intact", "armed", "judgednothing", "nomanifest", "corruptsib"]
# `gains` reads TWO reports and prefixes the baseline side's caveats, so it gets its own pairings:
# a clean control, each hedge state on the baseline side, the hedge on the CURRENT side (unprefixed
# keys), and the corrupt sibling.
GAINS_PAIRS = [("intact", "intact"), ("intact", "armed"), ("intact", "judgednothing"),
               ("armed", "intact"), ("intact", "corruptsib"), ("intact", "nomanifest")]

# The disclosure verbs, with arguments that make each one answer over INTACT (an empty control answer
# is a cell that cannot diverge). @PURE@/@DENY@ are replaced with real policy-file paths at run time.
VERBS = [
    ("where",       ["where", "Fs"]),
    ("callers",     ["callers", "app.reads"]),
    ("impact",      ["impact", "app.reads"]),
    ("path",        ["path", "app.top", "Exec"]),
    ("map",         ["map"]),
    ("blindspots",  ["blindspots"]),
    ("reachable",   ["reachable"]),
    ("containment", ["containment"]),
    ("tour",        ["tour", "5"]),
    ("unverified",  ["unverified", "--policy", "@PURE@"]),
    ("fix",         ["fix", "app.top", "Exec", "--policy", "@DENY@"]),
    ("fix-gate",    ["fix-gate", "--policy", "@DENY@"]),
]

# DECLARED per-engine verb coverage — see header. candor-swift's CLI treats an unknown action word as a
# scan target (measured: `swift map --report …` prints an armed placeholder REPORT at exit 2), so
# probing instead of declaring would harvest scan-report keys as query vocabulary. The declaration is
# enforced in the strict direction below: a NOSURF cell that answers exit 0 + JSON fails as STALE.
ENGINE_VERBS = {
    "rust":  {v for v, _ in VERBS} | {"gains"},
    "java":  {v for v, _ in VERBS} | {"gains"},
    "ts":    {v for v, _ in VERBS} | {"gains"},
    "swift": {"path", "tour", "gains", "fix", "fix-gate", "unverified"},
}

# The ⟨0.28⟩-pinned caveat key set (SPEC §2, "AND HERE IS WHAT THE TRAVELLING CAVEAT IS CALLED"):
# reserved vocabulary at EVERY position, including inside user-keyed objects — measured, the engines
# emit them into map's module namespace, the collision SPEC leaves as a known-open cell.
# ⟨0.28⟩ `noManifest` AND ITS BASELINE TWIN JOIN THE SET, and the omission is why the row-3 fixture
# above turned (A) red the moment it existed: unregistered, the key was masked as USER DATA at `map`'s
# root and its array collided with the module objects beside it. The gate's own diagnostic named the
# cause ("a reserved-style key that is not in RESERVED_EVERYWHERE"). A caveat key must be reserved
# EVERYWHERE the caveat can travel, and `map`'s namespace is exactly where SPEC §2 ⟨0.28⟩ says it does.
RESERVED_EVERYWHERE = {"incomplete", "unanalyzed", "judgedNothing", "noManifest",
                       "baselineIncomplete", "baselineUnanalyzed", "baselineJudgedNothing",
                       "baselineNoManifest"}

# Object positions whose KEYS are the user's own names, not engine vocabulary (header: the
# user-namespace line). Paths use `.` segments with `[]` for array elements and `*` for masked keys.
USER_POSITIONS = {
    ("map",         "$"),                          # keyed by module name
    ("containment", "$.contained[].placement"),    # keyed by layer/owner name
    ("containment", "$.ambient"),                  # never populated by this fixture; conservative
    ("reachable",   "$.effects"),                  # never populated by this fixture; conservative
}


def run(cmd, cwd, env):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)


def state_report(state):
    r = json.loads(json.dumps(INTACT))
    if state in ("intact", "corruptsib"):
        return r
    r["functions"] = []
    if state == "nomanifest":                  # ⟨0.24⟩ ROW 3 — a pre-⟨0.21⟩ producer: no `analyzed` AT
        r.pop("analyzed", None)                # ALL, which is "no manifest, no claim" and NOT row 1's
        return r                               # "count: 0, nothing was judged"
    r["analyzed"]["count"] = 0
    if state == "armed":                       # the ⟨0.21⟩ Row-1 armed placeholder
        r["unanalyzed"] = [{"path": "src/broken.x", "reason": "parse error"}]
    return r                                   # judgednothing: count 0 and NO unanalyzed


def write_state(ws, engine, state):
    d = os.path.join(ws, engine, state)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, STEM[engine] + ".json"), "w") as f:
        json.dump(state_report(state), f, indent=1)
    with open(os.path.join(d, STEM[engine] + ".callgraph.json"), "w") as f:
        json.dump(CG if state in ("intact", "corruptsib") else {}, f, indent=1)
    if state == "corruptsib":
        with open(os.path.join(d, SIBLING[engine] + ".json"), "w") as f:
            f.write("{ this is not json")
    return os.path.join(d, LOCATOR[engine])


def cmdline(engine, verb_args, jar):
    if engine == "rust":
        return [rust_query()] + verb_args
    if engine == "java":
        return ["java", "-jar", jar] + verb_args
    if engine == "ts":
        return ["node", os.path.join(CANDOR_TS, "query.mjs")] + verb_args
    return [swift_bin()] + verb_args


def harvest(ws):
    """Every (engine, state, verb) cell. Returns (cells, absent, stale_nosurf) where cells maps
    (engine, state, verb) -> {"rc": int, "doc": parsed-or-None}."""
    present = {"rust": bool(rust_query()), "java": bool(java_jar()),
               "ts": bool(ts_root()), "swift": bool(swift_bin())}
    absent = [e for e in ENGINES if not present[e]]
    jar = java_jar()
    pure = os.path.join(ws, "pure.policy")
    deny = os.path.join(ws, "deny.policy")
    open(pure, "w").write("pure app\n")
    open(deny, "w").write("deny Exec\n")
    # a dedicated empty cwd: engines walk UP from the cwd when discovering reports, and candor-swift's
    # scan fallback resolves its "target" against it — nothing of ours must be reachable either way.
    cwd = os.path.join(ws, "cwd")
    os.makedirs(cwd, exist_ok=True)
    env = dict(os.environ)
    for var in ("CANDOR_CONFIG", "CANDOR_REPORT", "CANDOR_POLICY"):
        env.pop(var, None)

    cells, stale = {}, []
    for engine in ENGINES:
        if not present[engine]:
            continue
        locs = {s: write_state(ws, engine, s) for s in STATES}
        for state in STATES:
            for verb, vargs in VERBS:
                args = [a.replace("@PURE@", pure).replace("@DENY@", deny) for a in vargs]
                r = run(cmdline(engine, args + ["--report", locs[state], "--json"], jar), cwd, env)
                doc = None
                try:
                    doc = json.loads(r.stdout)
                except Exception:
                    pass
                if verb not in ENGINE_VERBS[engine]:
                    # the strict direction of the declaration: an engine that GAINED this verb answers
                    # exit 0 with a document, and must force the table to be updated. The scan
                    # fallback measured today refuses at exit 2, so it stays excluded.
                    if r.returncode == 0 and isinstance(doc, (dict, list)) \
                            and (engine, verb) not in stale:
                        stale.append((engine, verb))
                    continue
                cells[(engine, state, verb)] = {"rc": r.returncode, "doc": doc}
        for cs, bs in GAINS_PAIRS:
            r = run(cmdline(engine, ["gains", locs[cs], locs[bs], "--json"], jar), cwd, env)
            try:
                doc = json.loads(r.stdout)
            except Exception:
                doc = None
            cells[(engine, "gains:%s-vs-%s" % (cs, bs), "gains")] = {"rc": r.returncode, "doc": doc}
    return cells, absent, stale


def jtype(v):
    if isinstance(v, bool):                    # bool FIRST — bool is a subclass of int
        return "boolean"
    if isinstance(v, (int, float)):            # int/float merged: JSON has one number type
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return "null"


def collect(cells):
    """shapes[(verb, path)][jtype] -> {engines};  vocab[key] -> {(engine, verb)}."""
    shapes = defaultdict(lambda: defaultdict(set))
    vocab = defaultdict(set)

    def walk(verb, engine, node, path):
        shapes[(verb, path)][jtype(node)].add(engine)
        if isinstance(node, dict):
            user = (verb, path) in USER_POSITIONS
            for k, v in node.items():
                if user and k not in RESERVED_EVERYWHERE:
                    walk(verb, engine, v, path + ".*")
                else:
                    vocab[k].add((engine, verb))
                    walk(verb, engine, v, path + "." + k)
        elif isinstance(node, list):
            for v in node:
                walk(verb, engine, v, path + "[]")

    for (engine, _state, verb), cell in cells.items():
        if isinstance(cell["doc"], (dict, list)):
            walk(verb, engine, cell["doc"], "$")
    return shapes, vocab


def main():
    args = sys.argv[1:]
    baseline_path, write_baseline, keep = None, False, False
    i = 0
    while i < len(args):
        if args[i] == "--baseline":
            baseline_path = args[i + 1]; i += 2
        elif args[i] == "--write-baseline":
            write_baseline = True; i += 1
        elif args[i] == "--keep":
            keep = True; i += 1
        else:
            print("gen_key_shapes.py: unknown argument %r" % args[i], file=sys.stderr)
            return 2
    if not os.path.exists(SPEC_MD):
        print("FAIL: SPEC.md not found at %s — check (B) has no vocabulary to check against" % SPEC_MD)
        return 2
    spec_text = open(SPEC_MD, encoding="utf-8").read()

    ws = tempfile.mkdtemp(prefix="candor-keyshapes-")
    t0 = time.time()
    try:
        cells, absent, stale = harvest(ws)
    finally:
        if keep:
            print("  workspace kept: %s" % ws)
        else:
            shutil.rmtree(ws, ignore_errors=True)

    live = sorted({e for (e, s, v) in cells if isinstance(cells[(e, s, v)]["doc"], (dict, list))})
    ndocs = sum(1 for c in cells.values() if isinstance(c["doc"], (dict, list)))
    print("KEY-SHAPE GATE — %d machine documents from %s in %.1fs"
          % (ndocs, ", ".join(live) or "nobody", time.time() - t0))
    if absent:
        print("  NOT RUN (reported, never implied): %s" % ", ".join(absent))
    rc = 0
    if len(live) < 2:
        print("FAIL: fewer than two engines produced machine documents — an empty table must never "
              "read as agreement")
        return 2
    for engine, verb in stale:
        print("FAIL: ENGINE_VERBS says %s has no `%s`, but it answered exit 0 with a JSON document — "
              "the NOSURF declaration is stale; update ENGINE_VERBS in gen_key_shapes.py" % (engine, verb))
        rc = 1

    shapes, vocab = collect(cells)

    # VACUITY GUARD — the corpus must still provoke the keys this gate exists for.
    for k in sorted(RESERVED_EVERYWHERE):
        emitters = {e for e, _v in vocab.get(k, set())}
        if len(emitters) < 2:
            print("FAIL (VACUOUS): pinned caveat key `%s` was observed from %d engine(s) %s — the "
                  "fixture no longer provokes the key this gate was built for, and that must never "
                  "read as agreement" % (k, len(emitters), sorted(emitters)))
            rc = 1

    # (A) CROSS-ENGINE SHAPE AGREEMENT — the check that catches `judgedNothing: [...]` vs `: true`.
    a_fail = 0
    for (verb, path), types in sorted(shapes.items()):
        if len(types) > 1:
            a_fail += 1
            detail = "; ".join("%s from %s" % (t, ",".join(sorted(engs)))
                               for t, engs in sorted(types.items()))
            hint = (" (`*` is a declared user-namespace position — a scalar beside objects here "
                    "usually means an engine emitted a reserved-style key that is not in "
                    "RESERVED_EVERYWHERE, which needs a SPEC ruling before it can live there)"
                    if "*" in path else "")
            print("FAIL (A): `%s` emits `%s` with %d different JSON types — %s. One key name, one "
                  "type: a consumer cannot branch on this key safely against any engine%s"
                  % (verb, path, len(types), detail, hint))
    if a_fail:
        rc = 1
    else:
        print("  (A) PASS — %d (verb, path) rows, every key one JSON type across %s"
              % (len(shapes), ", ".join(live)))

    # (B) THE VOCABULARY RATCHET.
    #
    # ⟨0.28⟩ "NAMED" MEANS WRITTEN AS A KEY, NOT USED AS A WORD — and this check shipped with the
    # weaker test, which is the defect this whole file exists to catch, in the file that catches it.
    # `\bcrossing\b` matched SPEC.md SEVEN times as ordinary English — a salience factor in the
    # scoring formula, "a boundary crossing", "an unverified-purity hole, a boundary crossing" — and
    # ZERO times as a key. So `crossing`, an unpinned wire field ts and swift emit from `fix` and the
    # MCP tool contract instructs agents to branch on, scored PASS because the spec happened to
    # discuss boundaries in prose. Found by the engine agent that went looking for the ruling.
    #
    # A pinned key is written as code: `key` in backticks, or inside a fenced shape block. Prose
    # cannot pin a field name — that is the ⟨0.24⟩ general rule's whole point ("a MUST that says
    # 'disclose X' without saying what X is called is four independent guesses"). Matching prose lets
    # the ratchet certify exactly the debt it was built to name.
    def spec_names(k):
        # The identifier ALONE in backticks, or quoted-with-a-colon in a shape block. Nothing looser.
        #
        # Two weaker spellings were tried and both certified the debt they were built to name. A bare
        # `\bkey\b` matched ordinary English — `crossing` appears SEVEN times in this document as a word
        # ("a boundary crossing", a factor in the salience formula) and ZERO times as a key, so an
        # unpinned field that ts and swift emit from `fix`, and that the MCP tool contract instructs
        # agents to branch on, scored PASS. Allowing the key ANYWHERE INSIDE a backtick span then still
        # matched it, via the backticked FORMULA `score = salience × benignity × hops-factor × crossing`.
        # Prose cannot pin a field name; a backticked expression that merely mentions one cannot either.
        esc = re.escape(k)
        return bool(re.search(r'`"?%s"?`' % esc, spec_text)      # `key` / `"key"` — the identifier alone
                    or re.search(r'"%s"\s*:' % esc, spec_text))  # "key": — a pinned shape block
    unnamed = {k: v for k, v in vocab.items() if not spec_names(k)}
    if write_baseline:
        payload = {
            "_": ["GRANDFATHERED WIRE-VOCABULARY DEBT for gen_key_shapes.py check (B).",
                  "Every key here is EMITTED by shipped engines and NAMED NOWHERE in SPEC.md — the",
                  "same unpinned state judgedNothing was in when four engines guessed four shapes",
                  "(2026-08-12). Listing a key here says the debt is KNOWN, not licensed: the right",
                  "fix for any entry is a SPEC clause pinning it, and deleting the entry is part of",
                  "that fix. The ratchet runs BOTH WAYS — a key below that becomes SPEC-named, or",
                  "stops being emitted, FAILS as stale so this list cannot outlive the debt.",
                  "Regenerate with: python3 gen_key_shapes.py --write-baseline"],
            "grandfathered": {k: sorted("%s/%s" % (e, v) for e, v in sorted(vocab[k]))
                              for k in sorted(unnamed)},
        }
        out = baseline_path or DEFAULT_BASELINE
        with open(out, "w") as f:
            json.dump(payload, f, indent=1)
            f.write("\n")
        print("  (B) wrote %d grandfathered keys to %s" % (len(unnamed), out))
        return rc
    bp = baseline_path or DEFAULT_BASELINE
    if not os.path.exists(bp):
        print("FAIL: baseline %s is missing — the ratchet cannot run, and an absent baseline must "
              "never read as 'nothing is grandfathered'" % bp)
        return 2
    grandfathered = set(json.load(open(bp)).get("grandfathered", {}))
    b_fail = 0
    for k in sorted(unnamed):
        if k not in grandfathered:
            b_fail += 1
            wherefrom = ", ".join(sorted("%s/%s" % (e, v) for e, v in vocab[k]))
            print("FAIL (B): machine-document key `%s` (emitted by %s) is named NOWHERE in SPEC.md "
                  "and is not grandfathered — an unpinned name is four independent guesses with a "
                  "conformance failure scheduled. Pin it in the rung that introduces it (§3.3.1 "
                  "⟨0.24⟩), then it passes here; grandfathering new debt is not the fix" % (k, wherefrom))
    for k in sorted(grandfathered):
        if k not in unnamed:
            b_fail += 1
            why = ("SPEC.md now names it" if spec_names(k)
                   else "no engine emitted it in this harvest")
            print("FAIL (B): grandfathered key `%s` is STALE — %s. Deleting the entry is part of the "
                  "fix (the ratchet runs both ways so the debt list cannot outlive the debt)" % (k, why))
    if b_fail:
        rc = 1
    else:
        print("  (B) PASS — %d vocabulary keys: every SPEC-unnamed key (%d) is grandfathered debt, "
              "no stale entries" % (len(vocab), len(unnamed)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
