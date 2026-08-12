#!/usr/bin/env python3
"""
P7 — THE SINK SURFACE, generated: (binary x verb x value-taking flag x sink spelling).

    A value-taking flag whose next token is `--`-prefixed has been GIVEN NO VALUE (SPEC §3.2 ⟨0.28⟩);
    the argv is a usage error at exit 2 — and the sinks named ELSEWHERE in that argv are still sinks,
    so the fail-closed refusal document must still reach them, in BOTH spellings (file and `-` stream).

WHY THIS PROPERTY EXISTS — the failure it was built for, as it happened (2026-08-12)
-------------------------------------------------------------------------------------
A value-taking flag whose next token began with `--` was consumed as its VALUE. So
`--policy --gate-json -` made `--gate-json` the policy FILENAME: the verdict sink the operator named
was silently not a sink, and the fail-closed refusal document went nowhere. Measured on candor-scan
and candor-java: exit 2 with NOTHING on the stream, where the `--gate-json -` refusal belongs. It also
made SPEC's own "given no value" cause unreachable in principle — no argv could produce it.

How it was found is the point. ONE conformance row (§3.1 b13) caught it on two engines' scan CLIs.
Fixing those exposed it in candor-query — the sibling binary in the same repo — an hour later; checking
ts and swift then found it in THEIR query/gate verbs too, each a separate hand-driven discovery, after
the scan CLIs' pass had been wrongly read as family health. The worst was a FAIL-OPEN GREEN:
`candor-query gate-verdict --report <swallowed>` exited 0 with a green verdict, because the swallowed
locator failed silently inside the coverage loader. Five scan CLIs got a rule and zero gate verbs — the
sibling-route habit. A hand enumeration finds the surface in front of the author; this file GENERATES
it: every binary, every verb, every value-taking flag DERIVED FROM --help (never hand-listed), every
sink spelling.

An exit-code-only assertion is worthless here: every one of that day's defects already exited 2 while
doing the wrong thing, and the fail-open gate-verdict case exited 0. So a sink cell asserts the
DOCUMENT (`ok:false` + `refused:true` at the named sink), and a cause cell asserts the diagnostic NAMES
THE BROKEN FLAG — measured that day, every wrong-cause diagnostic named the swallowed token
("no report files at prefix `--json`") and never the flag, so naming the flag separates the two.

WHAT THE MATRIX FOUND THAT THE HAND SWEEP MISSED (first full run, 2026-08-12) — the reason a
generator beats an enumeration, again:
  · candor-query `diff`/`rewire` swallow a broken flag pair SILENTLY AT EXIT 0 (`diff A B --report
    --json` exits 0 with a clean answer) where candor-java and candor-ts refuse at exit 2 naming the
    flag — §3.3.1: "a typo'd or a not-applicable flag stays an exit-2 error, never a silent swallow".
  · candor-java ACCEPTS `--class` as a value-taking flag on every query verb while its --help never
    documents it; and the `verify` verb (value-taking `--run`/`--report`/`--scope`) is absent from the
    top-level --help entirely — disclosure defects in a project whose subject is disclosure (§3.3:
    --help MUST "print a usage summary that lists these flags").
Both ride the baseline as clause-cited waivers so the accusation is recorded and expires when fixed.

THE TWO VACUITY GUARDS (this suite was bitten twice that same day — a row querying a function present
in no fixture; an oracle with a mangled locator making 58 of 60 cells vacuous):
  1. The derived flag inventory is PRINTED per binary, and a binary that yields NO value-taking flag
     FAILS the run — every one of them has some, so an empty derivation is the parser broken, never
     health.
  2. A flag discovered by probe that --help does not document is a FINDING, not a gap. The probe set
     is the UNION of every sibling's derived flags: what one engine documents, another must at least
     refuse loudly.

BOUNDARIES PINNED so the matrix cannot over-refuse: a healthy `--policy <file> --gate-json -` still
streams the green verdict at exit 0 (the bare `-` stays a legitimate value), and the file spelling
still lands it on disk.

USAGE
    python3 gen_sink_surface.py                                    # raw truth, exit non-zero on any FAIL
    python3 gen_sink_surface.py --keep                             # leave the scratch tree for inspection
    python3 gen_sink_surface.py --baseline sink-surface-baseline.json   # the ratchet
"""
# THE CONTRACT THIS PROPERTY ENFORCES, quoted so clause_check.py can prove SPEC.md still says it.
SPEC_CLAUSES = [
    ("§3.2 ⟨0.28⟩", 'AND "GIVEN NO VALUE" MEANS THE NEXT TOKEN IS FLAG-SHAPED — otherwise the clause '
                    'cannot be implemented at all.'),
    ("§3.2 ⟨0.28⟩", "a value-taking flag followed by a `--`-prefixed token is a usage error at exit 2, "
                    "and the sinks named elsewhere in that argv are still sinks — the run has a broken "
                    "command line, not a redefined one."),
    ("§3.2 ⟨0.28⟩", "A bare `-` stays a legitimate VALUE (`--gate-json -` is the stream form"),
    ("§3.3 ⟨0.8⟩",  "On **exit 2** it writes a **fail-closed document for EVERY cause**"),
    ("§3.3.1 ⟨0.18⟩", "a typo'd or a not-applicable flag stays an exit-2 error (§3.3.1), never a silent swallow."),
    ("§3.3",        "print a usage summary that lists these flags."),
    ("§3.3.1 ⟨0.28⟩ (5)", "EVERY ROUTE AND EVERY ENGINE THAT WRITES A REPORT."),
    ("§3.3.1 ⟨0.28⟩ (5)", "a route is not covered by its sibling."),
]

# =====================================================================================================
# THE BINARY INVENTORY IS ITSELF A HAND LIST — so it is CHECKED against §3.3.1 (5), both ways.
#
# The flag list is derived from --help precisely because a hand enumeration finds only the surface in
# front of the author — and then the BINARIES this matrix drives were exactly such a hand list, one
# level up. That is how `cargo-candor policy/guard --gate-json` (a bespoke gate-sink route) and the
# agent-fleet's `scan`/`observe --json` sat outside every guard written on 2026-08-12: no cell could
# fail over a binary the matrix never runs.
#
# So the inventory is DECLARED here and checked BOTH WAYS against the route list SPEC §3.3.1 (5)
# actually names (the "Surface as of this rung:" sentence, parsed from SPEC.md at run time — the same
# construction as part_declarations.py, chosen over inference after inference measured 1 true : 8 false
# positives):
#   · a route named in the clause and absent from this declaration FAILS — the spec grew a route and
#     the matrix silently didn't;
#   · a route declared here that the clause no longer names FAILS — the declaration outlived a rewrite.
# A route may be declared as a GAP with a reason: a gap stays a gap, but a visible one, printed every
# run — never an absence. ("driven", <engine-key>) must match a key locate_engines() returns, so a
# "driven" claim over a binary the matrix cannot locate is a FAIL, not a silent vacuity.
# =====================================================================================================
ROUTE_INVENTORY = {
    "candor-scan --json":  ("driven", "rust"),
    "candor-java --json":  ("driven", "java"),
    "candor-ts --json":    ("driven", "ts"),
    "candor-swift --json": ("driven", "swift"),
    "observe --json": ("gap", "candor-agents (the agent-fleet engine, a pipx-installed Python tool) is "
                              "not driven by this matrix — NO cell asserts its report sink or its argv "
                              "handling; its own suite (candor-agents test.py) is the only coverage"),
    "scan":           ("gap", "candor-agents `scan` — same engine, same gap; the clause's own words: "
                              "a route is not covered by its sibling"),
}

# Sink routes that exist in the family but are NOT report sinks named by §3.3.1 (5) — declared here so
# the reader of this inventory sees the whole surface, not the checked subset. Informative, printed.
ROUTE_NOTES = [
    ("cargo-candor policy/guard --gate-json", "a bespoke VERDICT-sink route (not a report sink); "
     "covered in candor-rust ci/wrapper-smoke.sh (input exemption + refusal document rows, 2026-08-12)"),
    ("candor-java verify", "driven by this matrix as a flag family inside the one jar"),
    ("candor-query gate-verdict --gate-json", "driven by this matrix (the rust query surface)"),
    ("MCP servers / LSP / umbrella bin/candor dispatcher", "read-only or pass-through — no report or "
     "verdict sink of their own; the dispatcher's engines are the ones driven above"),
]


def check_route_inventory(eng):
    """The both-ways check: SPEC §3.3.1 (5)'s named routes vs ROUTE_INVENTORY. Returns FAIL strings."""
    fails = []
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SPEC.md")
    try:
        text = open(spec_path).read()
    except OSError as e:
        return ["route-inventory: cannot read SPEC.md (%s) — this check would pass over nothing" % e]
    # The clause's route list is one sentence: "Surface as of this rung: `a`, `b`, … `z`**."
    # Whitespace-tolerant anchors — SPEC.md is hard-wrapped, so a phrase can carry a line break.
    m5 = re.search(r"\(5\)\s+EVERY\s+ROUTE\s+AND\s+EVERY\s+ENGINE\s+THAT\s+WRITES\s+A\s+REPORT\."
                   r"(.*?)(?:\n\n|\*\*\(6\))", text, re.S)
    if not m5:
        return ["route-inventory: SPEC §3.3.1 (5) not found — the clause this inventory is checked "
                "against has moved or been reworded; re-anchor the parse AND re-audit the inventory"]
    sent = re.search(r"Surface\s+as\s+of\s+this\s+rung:(.*?\.)", m5.group(1), re.S)
    if not sent:
        return ["route-inventory: the (5) clause no longer says 'Surface as of this rung:' — re-anchor "
                "the parse AND re-audit the inventory"]
    spec_routes = re.findall(r"`([^`]+)`", sent.group(1))
    if not spec_routes:
        return ["route-inventory: parsed the (5) sentence but found NO backticked routes — the "
                "derivation is broken, and an empty route list must never read as 'all covered'"]
    print("  route inventory (SPEC §3.3.1 (5), both ways):")
    for r in spec_routes:
        decl = ROUTE_INVENTORY.get(r)
        if decl is None:
            fails.append("route-inventory: SPEC §3.3.1 (5) names `%s` and this matrix neither drives "
                         "nor declares it — the spec grew a route and the inventory silently didn't" % r)
            continue
        status, detail = decl
        if status == "driven":
            if detail not in eng:
                fails.append("route-inventory: `%s` is declared driven via engine %r, which "
                             "locate_engines() does not return — a vacuous 'driven'" % (r, detail))
            else:
                print("    driven  %-22s (engine %s%s)" % (r, detail,
                      "" if eng[detail].get("present") else " — ABSENT this run, disclosed above"))
        else:
            print("    GAP     %-22s — %s" % (r, detail))
    for r in sorted(set(ROUTE_INVENTORY) - set(spec_routes)):
        fails.append("route-inventory: `%s` is declared here but SPEC §3.3.1 (5) no longer names it — "
                     "the declaration outlived a rewrite; re-audit both sides" % r)
    for name, note in ROUTE_NOTES:
        print("    note    %-22s — %s" % (name, note))
    return fails

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import gen_differential as gd

HERE = os.path.dirname(os.path.abspath(__file__))

# =====================================================================================================
# FIXTURE SOURCES — one effectful function per language, named `touch`, so every verb has a real
# argument and a healthy run is genuinely healthy (the boundary cells depend on that).
# =====================================================================================================
RUST_SRC = 'pub fn touch() { let _ = std::fs::read("/etc/hosts"); }\n'
TS_SRC = "import * as fs from 'fs';\nexport function touch() { fs.readFileSync('/etc/hosts'); }\n"
JAVA_SRC = ('package app;\nimport java.io.*;\npublic class App { void touch() { '
            'try { new FileInputStream("/etc/hosts").close(); } catch (Exception e) {} } }\n')
SWIFT_SRC = 'import Foundation\nfunc touch() { _ = try? String(contentsOfFile: "/etc/hosts") }\n'
PASS_POLICY = "deny Db\n"   # the fixtures only touch Fs, so a healthy gate is GREEN — the boundary rows
                            # prove the ok:false assertions are live (the document CAN say ok:true).

# =====================================================================================================
# FLAG DERIVATION FROM --help. This is the point of the file: the flag list is never hand-enumerated.
# A value-taking flag reads `--name <placeholder>` (also `--name "<cmd>"` — candor-java's verify
# spells `--run "<cmd>"`, which the first cut of this regex MISSED, silently shrinking java-verify's
# row to one flag); `--name [<placeholder>]` declares the VALUE optional (candor-java's
# `--json [<file>]`), and an optional-value flag followed by a `--` token has legitimately been given
# no value — it is EXCLUDED from swallow cells and PRINTED. A bare enum alternation (`--scope
# direct|all`) is a value too; requiring the space keeps `[--exists|--backend]` (a boolean choice,
# no value) out.
# =====================================================================================================
_FLAG_RE = re.compile(r'(--[a-z][a-z-]*)(\s*"?\s*)(\[?)<')
_ENUM_RE = re.compile(r'(--[a-z][a-z-]*)\s+[a-z]+\|[a-z]+')

# Measured exceptions to the syntax: help spells a mandatory-looking `<value>` but the engine PEEKS and
# treats the value as optional. Excluded from swallow cells for the same reason as `--json [<file>]`,
# and printed — an exclusion this table hides would be a silent hole in the matrix.
OPTIONAL_VALUE_MEASURED = {
    ("swift", "--verify"): "peeks — candor-swift 3fa358d: '--verify takes an OPTIONAL value'; "
                           "`privacy-manifest --verify` with no plist discovers one",
}


def derive_flags(engine, help_text):
    """{flag: 'mandatory'|'optional'} from one binary's --help text."""
    out = {}
    for m in _FLAG_RE.finditer(help_text):
        flag, optional = m.group(1), m.group(3) == "["
        # a flag seen both ways is optional-value (the safer reading for a swallow cell)
        out[flag] = "optional" if (optional or out.get(flag) == "optional") else "mandatory"
    for m in _ENUM_RE.finditer(help_text):
        out.setdefault(m.group(1), "mandatory")
    for (eng, flag), why in OPTIONAL_VALUE_MEASURED.items():
        if eng == engine and flag in out:
            out[flag] = "optional"
    return out


def derive_verbs(help_text):
    """Verb names from the ALL ACTIONS block. Two layouts exist: a table (one verb per line, args and
    prose after it — rust) and a bare word list (ts/java/swift). A line whose every token is
    verb-shaped is a word list; otherwise only the leading token counts."""
    verbs, in_block = [], False
    for line in help_text.splitlines():
        if "ALL ACTIONS" in line:
            in_block = True
            continue
        if in_block:
            s = line.strip()
            if not s or s.upper() == s and s.isupper():
                break
            toks = s.split()
            if toks[0].startswith("--"):
                continue
            if all(re.fullmatch(r"[a-z][a-z-]*", t) for t in toks):
                verbs.extend(toks)
            elif re.fullmatch(r"[a-z][a-z-]*", toks[0]):
                verbs.append(toks[0])
    return verbs


# Verbs OUTSIDE the §3.3.1 query grammar, excluded with the reason printed. An exclusion is a claim;
# each one names its ground. (`reports` and `gate-verdict` are engine-specific too, but they were two
# of the day's defect sites, so they stay IN, scoped to the flags their own usage line documents.)
EXCLUDED_VERBS = {
    "agents":      "prints a fixed document; no report grammar, no value-taking flag",
    "parsepolicy": "conformance witness outside the §3.3.1 grammar — family-uniform (measured "
                   "2026-08-12: all four engines ignore trailing flags at exit 0)",
    "audit":       "engine-specific ledger utility outside the §3.3.1 grammar",
    "state":       "engine-specific source-hash utility outside the §3.3.1 grammar",
    "receipt":     "engine-specific receipt utility outside the §3.3.1 grammar",
    "locate":      "engine-specific artifact-probe utility outside the §3.3.1 grammar",
    "engine-version": "engine-specific artifact-probe utility outside the §3.3.1 grammar",
    "merge-hook":  "engine-specific settings utility outside the §3.3.1 grammar",
}

# §3.1-family verbs get EVERY derived flag (the §3.3.1 grammar is uniform across them; a flag a verb
# does not take must still refuse at exit 2 naming it — never a silent swallow). Utility verbs that
# stay in are scoped to the value-flags on their OWN usage line, parsed from help, not assumed.
FAMILY_VERBS = {"show", "where", "callers", "map", "diff", "containment", "reachable", "path",
                "impact", "blindspots", "tour", "whatif", "fix", "fix-gate", "gate", "unverified",
                "gains", "rewire", "privacy-manifest"}

# Canonical positional args per §3.3.1 ("Verb args are positional, in the §3.1 order"). Symbols are
# resolved per engine: REP = that engine's report locator, PREFIX = its --out prefix.
REP, PREFIX, PARTS, OUTPOS = "\0REP", "\0PREFIX", "\0PARTS", "\0OUTPOS"
VERB_ARGS = {
    "show": ["touch"], "where": ["Fs"], "callers": ["touch"], "map": [], "containment": [],
    "reachable": [], "impact": ["touch"], "blindspots": [], "tour": [], "path": ["touch", "Fs"],
    "whatif": ["touch", "Fs"], "fix": ["touch", "Fs"], "fix-gate": [], "unverified": [],
    "diff": [REP, REP], "gains": [REP, REP], "rewire": [PREFIX, PREFIX], "gate": [],
    "privacy-manifest": [], "reports": [PREFIX], "gate-verdict": [PARTS, OUTPOS],
}

# Verbs that DISCOVER a report (§3.3.1): a healthy `--report <rep>` is added when the flag under test
# is a different one, so a regressed swallow would run through to a green answer instead of tripping
# over a missing report — the cell then reads exit 0, not an accidental exit 2 with the wrong cause.
DISCOVERING = FAMILY_VERBS - {"diff", "gains", "rewire", "gate"}


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def _doc(text):
    """Parse a gate-verdict document; None when the text is not one."""
    try:
        return json.loads(text)
    except Exception:
        return None


# =====================================================================================================
# ENGINE SURFACES. Each binary yields a scan surface and/or a query surface; java adds `verify`
# (VerifyCli — a third flag-parsing family inside the one jar, reached via its own subcommand help).
# =====================================================================================================
def locate_engines(ws):
    """Build fixtures, locate binaries, produce one healthy report per engine.
    Returns {engine: dict(scan_argv, query_argv, rep, prefix, present, note)}."""
    eng = {}

    # ---- rust: candor-scan AND candor-query — the split-binary vein this matrix exists for.
    rdir = os.path.join(ws, "rust", "src")
    os.makedirs(rdir, exist_ok=True)
    open(os.path.join(ws, "rust", "Cargo.toml"), "w").write(
        '[package]\nname = "probe"\nversion = "0.0.0"\nedition = "2021"\n')
    open(os.path.join(rdir, "lib.rs"), "w").write(RUST_SRC)
    sbin = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
    # CANDOR_QUERY_BIN FIRST — run.sh resolves SCAN and QUERY independently (see gen_sidecar_manifest).
    qbin = os.environ.get("CANDOR_QUERY_BIN")
    if not qbin:
        qbin = os.path.join(os.path.dirname(sbin), "candor-query")
    pfx = os.path.join(ws, "rrep")
    if os.path.exists(sbin) and os.path.exists(qbin):
        r = run([sbin, os.path.join(ws, "rust"), "--out", pfx])
        rep = pfx + ".probe.scan.json"
        eng["rust"] = {"present": True, "scan_argv": [sbin, os.path.join(ws, "rust")],
                       "query_argv": [qbin], "rep": rep, "prefix": pfx,
                       "broken": r.returncode != 0 or not os.path.exists(rep)}
    else:
        eng["rust"] = {"present": False, "note": "no candor-scan/candor-query at %s" % os.path.dirname(sbin)}

    # ---- ts: scan.mjs AND query.mjs — the second split-binary family.
    tdir = os.path.join(ws, "ts")
    os.makedirs(tdir, exist_ok=True)
    open(os.path.join(tdir, "Cases.ts"), "w").write(TS_SRC)
    json.dump({"name": "probe", "version": "0.0.0"}, open(os.path.join(tdir, "package.json"), "w"))
    scan_mjs, query_mjs = os.path.join(gd.CANDOR_TS, "scan.mjs"), os.path.join(gd.CANDOR_TS, "query.mjs")
    if shutil.which("node") and os.path.exists(scan_mjs) and os.path.exists(query_mjs):
        pfx = os.path.join(ws, "tsrep")
        r = run(["node", scan_mjs, tdir, "--out", pfx])
        rep = pfx + ".json"
        eng["ts"] = {"present": True, "scan_argv": ["node", scan_mjs, tdir],
                     "query_argv": ["node", query_mjs], "rep": rep, "prefix": pfx,
                     "broken": r.returncode != 0 or not os.path.exists(rep)}
    else:
        eng["ts"] = {"present": False, "note": "no node / scan.mjs / query.mjs (set CANDOR_TS)"}

    # ---- java: ONE jar, several verb families inside it (Candor scan, Query verbs, VerifyCli).
    jar = os.environ.get("CANDOR_JAVA_JAR")
    if not jar:
        cands = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
        jar = max(cands, key=os.path.getmtime) if cands else None
    if jar and os.path.exists(jar) and shutil.which("javac"):
        jsrc = os.path.join(ws, "java")
        os.makedirs(jsrc, exist_ok=True)
        open(os.path.join(jsrc, "App.java"), "w").write(JAVA_SRC)
        cls = os.path.join(ws, "jclasses")
        c = run(["javac", "-nowarn", "-d", cls, os.path.join(jsrc, "App.java")])
        rep = os.path.join(ws, "jrep.json")
        r = run(["java", "-jar", jar, cls, "--json", rep])
        eng["java"] = {"present": True, "scan_argv": ["java", "-jar", jar, cls],
                       "query_argv": ["java", "-jar", jar], "rep": rep, "prefix": rep[:-5],
                       "verify_target": cls,
                       "broken": c.returncode != 0 or r.returncode != 0 or not os.path.exists(rep)}
    else:
        eng["java"] = {"present": False, "note": "no candor-java jar / javac (set CANDOR_JAVA_JAR)"}

    # ---- swift: one binary, multiple verb parsers.
    swbin = os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
    if os.path.exists(swbin):
        sdir = os.path.join(ws, "swift")
        os.makedirs(sdir, exist_ok=True)
        src = os.path.join(sdir, "cases.swift")
        open(src, "w").write(SWIFT_SRC)
        pfx = os.path.join(ws, "swrep")
        r = run([swbin, src, "--out", pfx])
        reps = [p for p in gd._glob(ws, ".json")
                if os.path.basename(p).startswith("swrep.") and "callgraph" not in p and "hierarchy" not in p]
        eng["swift"] = {"present": True, "scan_argv": [swbin, src], "query_argv": [swbin],
                        "rep": reps[0] if reps else None, "prefix": pfx,
                        "broken": r.returncode != 0 or not reps}
    else:
        eng["swift"] = {"present": False, "note": "no candor-swift at %s (swift build)" % swbin}

    return eng


def capture_help(argv):
    r = run(argv + ["--help"])
    return (r.stdout.decode(errors="replace") + "\n" + r.stderr.decode(errors="replace"))


# =====================================================================================================
# CELLS
# =====================================================================================================
_PROBE_FAULT = os.environ.get("CANDOR_PROBE_FAULT")
_probe_fired = []


class Matrix:
    def __init__(self, ws):
        self.ws = ws
        self.cells = []          # (cell_id, verdict, why)
        self.n = 0
        self.policy = os.path.join(ws, "pass.policy")
        open(self.policy, "w").write(PASS_POLICY)
        self.parts = os.path.join(ws, "parts.ndjson")
        open(self.parts, "w").write("")
        self._sink_n = 0

    def sinkpath(self):
        self._sink_n += 1
        return os.path.join(self.ws, "sink%03d.json" % self._sink_n)

    def record(self, cell_id, ok, why=""):
        self.n += 1
        self.cells.append((cell_id, "OK" if ok else "FAIL", why))

    # ---- the assertions -----------------------------------------------------------------------
    def cause_cell(self, cell_id, argv, flag):
        """`<flag> --json` — a usage error at exit 2 whose diagnostic NAMES THE FLAG. Exit 0/1 is the
        fail-open swallow; exit 2 without the flag's name is the wrong-cause reading (the diagnostics
        measured on the pre-fix engines named only the swallowed token, never the flag)."""
        r = run(argv)
        out = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        if r.returncode != 2:
            self.record(cell_id, False, "exit %d, expected the exit-2 usage error — a broken argv ran "
                                        "as if typed correctly (argv: %s)" % (r.returncode, " ".join(argv[-4:])))
        elif flag not in out:
            self.record(cell_id, False, "exit 2 but the diagnostic never names `%s` — the wrong-cause "
                                        "shape (got: %s)" % (flag, out.strip()[:140]))
        else:
            self.record(cell_id, True)

    def sink_cell(self, cell_id, argv, flag, sink):
        """`<flag> --gate-json <sink>` — exit 2 AND the fail-closed refusal document AT THE NAMED SINK.
        sink is a path or '-' (the stream form reads the document from stdout)."""
        if sink != "-" and os.path.exists(sink):
            os.unlink(sink)
        r = run(argv)
        text = r.stdout.decode(errors="replace") if sink == "-" else (
            open(sink).read() if os.path.exists(sink) else "")
        doc = _doc(text)
        if _PROBE_FAULT and not _probe_fired:
            _probe_fired.append(True)
            print("  PROBE: simulated the fail-open swallow on one sink cell (exit 0, green document) "
                  "— this run MUST fail")
            r = subprocess.CompletedProcess(argv, 0)
            doc = {"ok": True, "violations": []}
        where = "the stream" if sink == "-" else os.path.basename(sink)
        if r.returncode != 2:
            self.record(cell_id, False, "exit %d, expected 2 — `%s` swallowed `--gate-json` and the "
                                        "run carried on" % (r.returncode, flag))
        elif doc is None:
            self.record(cell_id, False, "exit 2 with NO document at %s — the sink named after the "
                                        "broken `%s` was silently not a sink (stdout/file: %r)"
                                        % (where, flag, text.strip()[:100]))
        elif doc.get("ok") is not False or doc.get("refused") is not True:
            self.record(cell_id, False, "the document at %s is not the ok:false+refused:true refusal "
                                        "— got %s" % (where, json.dumps(doc)[:120]))
        else:
            self.record(cell_id, True)

    def boundary_cell(self, cell_id, argv, sink):
        """The healthy run — `--policy <file>` honoured, `--gate-json <sink>` green at exit 0. Pins
        that the matrix cannot over-refuse: `-` stays a legitimate value, a normal --policy is
        unaffected — and proves the refusal assertions are live (the document CAN say ok:true)."""
        if sink != "-" and os.path.exists(sink):
            os.unlink(sink)
        r = run(argv)
        text = r.stdout.decode(errors="replace") if sink == "-" else (
            open(sink).read() if os.path.exists(sink) else "")
        doc = _doc(text)
        if r.returncode != 0:
            self.record(cell_id, False, "healthy run exited %d: %s" % (r.returncode,
                        r.stderr.decode(errors="replace").strip()[:140]))
        elif doc is None or doc.get("ok") is not True:
            self.record(cell_id, False, "healthy run wrote no green verdict at %s (got %r)"
                        % ("the stream" if sink == "-" else os.path.basename(sink), text.strip()[:100]))
        else:
            self.record(cell_id, True)


def resolve_args(symbols, e, m):
    out = []
    for s in symbols:
        out.append({REP: e["rep"], PREFIX: e["prefix"], PARTS: m.parts,
                    OUTPOS: os.path.join(m.ws, "gv-out.json")}.get(s, s))
    return out


def verb_flags_from_line(help_text, verb, flags):
    """The value-taking flags a UTILITY verb's own usage line documents."""
    for line in help_text.splitlines():
        s = line.strip()
        if s.startswith(verb + " ") or s.startswith(verb + "  "):
            return [f for f in flags if f in line]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--baseline")
    args = ap.parse_args()
    t0 = time.time()

    ws = tempfile.mkdtemp(prefix="candor-p7-")
    try:
        return run_matrix(ws, args)
    finally:
        if args.keep:
            print("  scratch kept at %s" % ws)
        else:
            shutil.rmtree(ws, ignore_errors=True)
        print("  P7 runtime: %.1fs" % (time.time() - t0))


def run_matrix(ws, args):
    print("P7 — THE SINK SURFACE: (binary x verb x value-taking flag x sink spelling), derived from --help")
    eng = locate_engines(ws)
    # The binary inventory is a hand list — checked both ways against SPEC §3.3.1 (5) before any cell
    # runs, so a route the spec names and the matrix does not drive is a FAILURE or a printed GAP,
    # never an absence. NOT waivable through the ratchet: a waiver accuses an engine; this accuses the
    # suite's own coverage.
    inv_fails = check_route_inventory(eng)
    m = Matrix(ws)
    inventories = {}     # binary label -> sorted mandatory flags (the printed inventory)
    all_mandatory = {}   # binary label -> set, for the union probe

    # ------------------------------------------------------------------------------------------
    # PASS 1 — derive. Every binary's --help is captured and parsed; the inventory is printed and
    # an empty derivation FAILS (vacuity guard 1 — an empty matrix must never read as a green one).
    # ------------------------------------------------------------------------------------------
    surfaces = []   # (binary_label, engine, kind, base_argv, help_text, flags, verbs)
    for kind in ("rust", "ts", "java", "swift"):
        e = eng[kind]
        if not e["present"]:
            print("  SKIPPED %-5s — %s (a missing engine is loud, never a silent shrink)" % (kind, e["note"]))
            continue
        if e.get("broken"):
            m.record("%s/harness/scan" % kind, False, "engine present but its fixture scan produced no "
                                                      "report — the harness broken, never engine health")
            continue
        pairs = []
        if kind in ("rust", "ts"):   # split binaries — scan and query each own a help surface
            pairs = [("%s-scan" % kind, "scan", e["scan_argv"][:-1] if kind == "rust" else e["scan_argv"][:2]),
                     ("%s-query" % kind, "query", e["query_argv"])]
        else:                        # one binary, several verb families behind one help
            pairs = [("%s" % kind, "both", e["query_argv"])]
        for label, fam, help_argv in pairs:
            text = capture_help(help_argv)
            flags = derive_flags(kind, text)
            mand = sorted(f for f, k in flags.items() if k == "mandatory")
            opt = sorted(f for f, k in flags.items() if k == "optional")
            inventories[label] = mand
            all_mandatory[label] = set(mand)
            print("  %-11s value-taking flags: %s%s" % (label, " ".join(mand) or "(NONE)",
                  ("   [optional-value, excluded from swallow cells: %s]" % " ".join(opt)) if opt else ""))
            if not mand:
                m.record("%s/derive/flags" % label, False,
                         "--help yielded NO value-taking flag — every binary has some, so this is the "
                         "derivation broken or the help gutted, and the matrix over it would be vacuous")
                continue
            verbs = derive_verbs(text) if fam != "scan" else []
            surfaces.append((label, kind, fam, help_argv, text, flags, verbs))

    # ------------------------------------------------------------------------------------------
    # PASS 2 — the cells.
    # ------------------------------------------------------------------------------------------
    for label, kind, fam, base, text, flags, verbs in surfaces:
        e = eng[kind]
        mand = sorted(f for f, k in flags.items() if k == "mandatory")

        # ---- the SCAN surface: `<target> <F> --gate-json <sink>`, both spellings, + boundaries.
        if fam in ("scan", "both"):
            scan = e["scan_argv"]
            # A one-binary engine's help mixes scan and query flags; the query-only ones (--report,
            # --class) are unknown flags TO A SCAN, and run.sh's b1 pose already pins the unknown-flag
            # arming there — this matrix keeps its scan cells inside the ⟨0.28⟩ swallow clause. The
            # scoping is printed: a silent cap reads as coverage the matrix does not have.
            scan_flags = [f for f in mand if f not in ("--report", "--class")] if fam == "both" else mand
            dropped = sorted(set(mand) - set(scan_flags))
            if dropped:
                print("    %-11s scan cells scoped to %s — %s are query-family flags (unknown to a "
                      "scan; covered by the b1 unknown-flag pose, not this matrix)"
                      % (label, " ".join(scan_flags), " ".join(dropped)))
            for f in scan_flags:
                if f == "--gate-json":   # the sink flag broken ITSELF names no sink — cause cell
                    m.cause_cell("%s/scan/%s/cause" % (label, f), scan + [f, "--json"], f)
                    continue
                sp = m.sinkpath()
                m.sink_cell("%s/scan/%s/sink-file" % (label, f), scan + [f, "--gate-json", sp], f, sp)
                m.sink_cell("%s/scan/%s/sink-stream" % (label, f), scan + [f, "--gate-json", "-"], f, "-")
            sp = m.sinkpath()
            m.boundary_cell("%s/scan/healthy/boundary-file" % label,
                            scan + ["--policy", m.policy, "--gate-json", sp], sp)
            m.boundary_cell("%s/scan/healthy/boundary-stream" % label,
                            scan + ["--policy", m.policy, "--gate-json", "-"], "-")

        # ---- the QUERY surface: every derived verb x every derived flag.
        if fam in ("query", "both"):
            q = e["query_argv"]
            if not verbs:
                m.record("%s/derive/verbs" % label, False, "--help yielded NO verbs for a query surface")
            for v in verbs:
                if v in EXCLUDED_VERBS:
                    print("    %-11s verb `%s` excluded — %s" % (label, v, EXCLUDED_VERBS[v]))
                    continue
                if v not in VERB_ARGS:
                    m.record("%s/derive/verb-%s" % (label, v), False,
                             "--help lists verb `%s` this matrix has no argv shape for — teach "
                             "VERB_ARGS or exclude it WITH a reason; a silent skip is coverage the "
                             "matrix does not have" % v)
                    continue
                pos = resolve_args(VERB_ARGS[v], e, m)
                vflags = mand if v in FAMILY_VERBS else verb_flags_from_line(text, v, mand)
                if not vflags:
                    m.record("%s/derive/verb-%s" % (label, v), False,
                             "utility verb `%s` derived NO flags from its usage line — vacuous row" % v)
                    continue
                healthy = (["--report", e["rep"]] if v in DISCOVERING else [])
                if v == "gate":
                    # gate is the query family's SINK surface: the day's defect argv verbatim.
                    for f in ("--report", "--policy"):
                        other = (["--policy", m.policy] if f == "--report" else ["--report", e["rep"]])
                        sp = m.sinkpath()
                        m.sink_cell("%s/gate/%s/sink-file" % (label, f),
                                    q + ["gate"] + other + [f, "--gate-json", sp], f, sp)
                        m.sink_cell("%s/gate/%s/sink-stream" % (label, f),
                                    q + ["gate"] + other + [f, "--gate-json", "-"], f, "-")
                    for f in [x for x in vflags if x not in ("--report", "--policy")]:
                        m.cause_cell("%s/gate/%s/cause" % (label, f),
                                     q + ["gate", "--report", e["rep"], "--policy", m.policy, f, "--json"], f)
                    m.boundary_cell("%s/gate/healthy/boundary-stream" % label,
                                    q + ["gate", "--report", e["rep"], "--policy", m.policy,
                                         "--gate-json", "-"], "-")
                    sp = m.sinkpath()
                    m.boundary_cell("%s/gate/healthy/boundary-file" % label,
                                    q + ["gate", "--report", e["rep"], "--policy", m.policy,
                                         "--gate-json", sp], sp)
                    continue
                for f in vflags:
                    extra = [] if f == "--report" else healthy
                    m.cause_cell("%s/%s/%s/cause" % (label, v, f), q + [v] + pos + extra + [f, "--json"], f)

        # ---- VerifyCli — the third flag family inside the one jar, behind its own subcommand help.
        if kind == "java" and fam == "both":
            vh = capture_help(e["query_argv"] + ["verify"])
            if "usage" in vh.lower():
                vflags = sorted(f for f, k in derive_flags("java", vh).items() if k == "mandatory")
                inventories["java-verify"] = vflags
                print("  %-11s value-taking flags: %s   [from `verify --help`]" % ("java-verify", " ".join(vflags)))
                if not vflags:
                    m.record("java/verify/derive", False, "`verify --help` yielded no value-taking flags")
                for f in vflags:
                    base_v = e["query_argv"] + ["verify", e["verify_target"]]
                    argv = base_v + ([f, "--json"] if f == "--run" else ["--run", "true", f, "--json"])
                    m.cause_cell("java/verify/%s/cause" % f, argv, f)
                if "verify" not in text:
                    m.record("java/help/verify", False,
                             "the jar ANSWERS `verify --help` (value-taking --run/--report/--scope) "
                             "but the top-level --help never mentions the verb — §3.3 requires the "
                             "usage summary to list the flags the engine accepts")

    # ------------------------------------------------------------------------------------------
    # PASS 3 — the UNDOCUMENTED-FLAG probe (vacuity guard 2, inverted). Candidates are the UNION of
    # every surface's derived flags; a binary that ACCEPTS one its own --help never mentions has an
    # undisclosed value-taking flag — a finding, in a project whose subject is disclosure.
    # ------------------------------------------------------------------------------------------
    union = set().union(*all_mandatory.values()) if all_mandatory else set()
    for label, kind, fam, base, text, flags, verbs in surfaces:
        e = eng[kind]
        candidates = sorted(f for f in union if f not in text)
        for cand in candidates:
            if fam == "scan" or fam == "both":
                argv = e["scan_argv"] + [cand, "--json"]
            if fam == "query":
                argv = e["query_argv"] + ["tour", "--report", e["rep"], cand, "--json"]
            r = run(argv)
            out = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
            if r.returncode == 0:
                m.record("%s/help/%s" % (label, cand), False,
                         "probe flag `%s` is undocumented in --help and the run EXITED 0 — either an "
                         "undisclosed flag or a silent swallow; both are findings" % cand)
            elif re.search(r"(given no value|requires a)", out) and cand in out:
                m.record("%s/help/%s" % (label, cand), False,
                         "the binary ACCEPTS value-taking `%s` (refuses it a value like a real flag) "
                         "but its --help never documents it — §3.3: the usage summary lists the flags" % cand)
            else:
                m.record("%s/help/%s" % (label, cand), True)
        # `both` binaries parse two families; probe the query family too.
        if fam == "both":
            for cand in candidates:
                r = run(e["query_argv"] + ["tour", "--report", e["rep"], cand, "--json"])
                out = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
                if r.returncode == 0:
                    m.record("%s/help-query/%s" % (label, cand), False,
                             "probe flag `%s` undocumented in --help, and the query run EXITED 0" % cand)
                elif re.search(r"(given no value|requires a)", out) and cand in out:
                    m.record("%s/help-query/%s" % (label, cand), False,
                             "the query family ACCEPTS value-taking `%s` but --help never documents it "
                             "— §3.3: the usage summary lists the flags" % cand)
                else:
                    m.record("%s/help-query/%s" % (label, cand), True)

    # ------------------------------------------------------------------------------------------
    # VERDICT — with the both-ways ratchet: a waiver must cite the clause it accuses an engine of
    # violating, and a waiver whose cell now passes is STALE and fails (it outlived its defect).
    # ------------------------------------------------------------------------------------------
    fails = [(cid, why) for cid, v, why in m.cells if v == "FAIL"]
    oks = sum(1 for _, v, _ in m.cells if v == "OK")
    print("  %d cells: %d OK, %d FAIL" % (m.n, oks, len(fails)))

    waived = {}
    if args.baseline:
        if not os.path.exists(args.baseline):
            print("FAIL: baseline %s is missing — an absent baseline must never read as 'nothing is waived'"
                  % args.baseline)
            return 2
        for w in json.load(open(args.baseline)).get("waivers", []):
            waived[w["cell"]] = w["why"]

    used, unwaived = set(), []
    for cid, why in fails:
        if cid in waived:
            used.add(cid)
            print("  WAIVED %s — %s" % (cid, waived[cid][:110]))
        else:
            unwaived.append((cid, why))
    stale = sorted(set(waived) - used)
    for s in stale:
        print("FAIL: STALE WAIVER %s — the cell it covers now passes; delete it" % s)
    for cid, why in unwaived:
        print("FAIL: %s — %s" % (cid, why))

    for f in inv_fails:
        print("FAIL: %s" % f)

    if _PROBE_FAULT and not _probe_fired:
        print("FAIL: probe fault requested but no sink cell ran — the property is not exercising sinks")
        return 1
    if unwaived or stale or inv_fails:
        return 1
    print("  P7 OK — %d live cells across %d binaries (%s)"
          % (oks, len(inventories), ", ".join(sorted(inventories))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
