#!/usr/bin/env python3
"""
mutation_poison_configs.py — the MINIMAL, unavoidable human-supplied seam mutation_poison_gen.py
needs per checker: how it is invoked, and ONE genuinely-valid (accept-known-good) baseline document
per argv "mode". This is NOT a bypass list — it encodes no wrongness at all, only what a real,
correct engine report/ledger/consumer-output looks like, which is domain knowledge no source-reader
can derive (see mutation_poison_gen.py's own header). Every POISON is generated mechanically from
this baseline plus the checker's own source; nothing here says what a mutant looks like.

Baselines are reused, not reinvented, wherever conformance/mutation-gate.sh already has an
independently-authored accept-known-good fixture for the same condition — a second, disagreeing copy
would itself be a drift risk.

WAIVERS name a specific line + reason, the same convention this project already uses everywhere else
(clause_check.py's citations, must_ledger.py's `unenforced`) — never a silent skip.
"""
import os
from mutation_poison_gen import CheckerConfig, Call, extract_pyvar, extract_bashfunc_pyc, read_extfile

HERE = os.path.dirname(os.path.abspath(__file__))
D83_SCOPE = "deny Fs poison"


def _argv(*fixed):
    """argv builder: fixed positional pieces, where the string "{argv1}"/"{argv2}" get substituted
    with the real temp-file path for that slot at call time."""
    def build(paths):
        out = []
        for piece in fixed:
            if isinstance(piece, str) and piece.startswith("{") and piece.endswith("}"):
                out.append(paths[piece[1:-1]])
            else:
                out.append(piece)
        return out
    return build


# ════════════════════════════════════════════════════════════════════════════════════════════════
# EMBEDDED (pulled live out of conformance/run.sh) — used for the RETRO-TEST calibration control.
# ════════════════════════════════════════════════════════════════════════════════════════════════

VD_PY = CheckerConfig(
    name="VD_PY", source_fn=lambda: extract_pyvar("VD_PY"), interpreter="inline",
    calls=[
        Call("ok0", {"argv1": {"ok": False}}, _argv("{argv1}", "ok0")),
        Call("okt", {"argv1": {"ok": True}}, _argv("{argv1}", "okt")),
        Call("refused", {"argv1": {"refused": True}}, _argv("{argv1}", "refused")),
        Call("norefused", {"argv1": {"violations": []}}, _argv("{argv1}", "norefused")),
        Call("v005", {"argv1": {"violations": [{"rule": "AS-EFF-005"}]}}, _argv("{argv1}", "v005")),
        Call("zm", {"argv1": {"zeroMatch": [D83_SCOPE]}}, _argv("{argv1}", f"zm:{D83_SCOPE}")),
        Call("nozm", {"argv1": {}}, _argv("{argv1}", "nozm")),
    ],
)

RS_PY_FAILCLOSED = CheckerConfig(
    name="RS_PY_FAILCLOSED", source_fn=lambda: extract_pyvar("RS_PY_FAILCLOSED"), interpreter="inline",
    calls=[Call(None, {"argv1": {"functions": [], "analyzed": {"count": 0}, "unanalyzed": ["x"]}},
                 _argv("{argv1}"))],
)

RS_PY_STREAM_FAILCLOSED = CheckerConfig(
    name="RS_PY_STREAM_FAILCLOSED", source_fn=lambda: extract_pyvar("RS_PY_STREAM_FAILCLOSED"), interpreter="inline",
    calls=[Call(None, {"stdin": {"functions": [], "analyzed": {"count": 0}, "unanalyzed": ["x"]}},
                 _argv(), stdin_slot="stdin")],
)

ZR_PY_NO_OK = CheckerConfig(
    name="ZR_PY_NO_OK", source_fn=lambda: extract_pyvar("ZR_PY_NO_OK"), interpreter="inline",
    calls=[Call(None, {"argv1": {"judgedNothing": ["x"]}}, _argv("{argv1}"))],
)

ZR_PY_HAS_OK = CheckerConfig(
    name="ZR_PY_HAS_OK", source_fn=lambda: extract_pyvar("ZR_PY_HAS_OK"), interpreter="inline",
    calls=[Call(None, {"argv1": {"ok": True}}, _argv("{argv1}"))],
)

CHAN_PY = CheckerConfig(
    name="CHAN_PY", source_fn=lambda: extract_pyvar("CHAN_PY"), interpreter="inline",
    calls=[Call("caveat", {"argv1": {"judgedNothing": ["x"], "incomplete": True}}, _argv("{argv1}", "caveat"))],
)

CK83_DEFECT = CheckerConfig(
    name="ck83_defect", source_fn=lambda: extract_bashfunc_pyc("ck83_defect"), interpreter="inline",
    calls=[Call(None,
                {"argv1": {"ok": True, "violations": []},
                 "argv2": {"ok": True, "violations": [], "zeroMatch": [D83_SCOPE]}},
                _argv("{argv1}", "{argv2}", D83_SCOPE))],
)

CK83_CONTROL = CheckerConfig(
    name="ck83_control", source_fn=lambda: extract_bashfunc_pyc("ck83_control"), interpreter="inline",
    calls=[Call(None,
                {"argv1": {"ok": False, "violations": [{"rule": "AS-EFF-006"}]},
                 "argv2": {"ok": False, "violations": [{"rule": "AS-EFF-006"}]}},
                _argv("{argv1}", "{argv2}"),
                # ck83_control ALSO asserts argv1/argv2 are byte-identical (`sb != rb`), independent
                # of every per-field check below it — poisoning argv1 alone would trip THAT assertion
                # as a side effect and mask whichever field condition is under test. Mirroring the
                # poison onto argv2 keeps the documents byte-equal so each field condition is isolated
                # on its own, matching mutation-gate.sh's own fixtures for this checker (which `cp` the
                # mutated scan.json onto report.json rather than leaving report.json at baseline).
                mirror={"argv1": "argv2"})],
)


# ════════════════════════════════════════════════════════════════════════════════════════════════
# STANDALONE conformance/*.py — the six named checkers this task assigns; two of them (incomplete_
# check, fs_position_check) fit the document-via-argv shape directly.
# ════════════════════════════════════════════════════════════════════════════════════════════════

INCOMPLETE_CHECK = CheckerConfig(
    name="incomplete_check.py",
    source_fn=lambda: read_extfile(os.path.join(HERE, "incomplete_check.py")),
    interpreter=f"file:{os.path.join(HERE, 'incomplete_check.py')}",
    calls=[
        Call(None,
             {"argv2": {"resolves": ["incomplete"],
                        "functions": [{"fn": "depWrite", "incomplete": ["Fs"], "paths": []}]},
              "argv3": "1", "argv4": "consumer diverges: AS-EFF-008 charged on depWrite"},
             lambda paths: ["rust", paths["argv2"], paths["argv3"], paths["argv4"]])
    ],
)

FS_POSITION_CHECK = CheckerConfig(
    name="fs_position_check.py",
    source_fn=lambda: read_extfile(os.path.join(HERE, "fs_position_check.py")),
    interpreter=f"file:{os.path.join(HERE, 'fs_position_check.py')}",
    calls=[
        Call(None,
             {"argv2": {"functions": [
                 {"fn": "a.exfil", "paths": [], "incomplete": ["Fs"]},
                 {"fn": "a.okLit", "paths": ["/tmp/lit"], "incomplete": []},
                 {"fn": "a.twoPath", "paths": [], "incomplete": ["Fs"]},
                 {"fn": "a.twoLit", "paths": ["/tmp/lit", "/tmp/dst"], "incomplete": []},
             ]},
              "argv3": "1",
              "argv4": "violations: exfil twoPath twoLit"},   # deliberately NOT containing the
                                                                # substring "okLit" — see fs_position_
                                                                # check.py L125 ('okLit' in out): the
                                                                # first draft of this baseline string
                                                                # happened to spell "...twoLit ... okLit
                                                                # not", which CONTAINS "okLit" and
                                                                # tripped that check by accident —
                                                                # caught by this generator's own
                                                                # accept-known-good control.
             lambda paths: ["rust", paths["argv2"], paths["argv3"], paths["argv4"]])
    ],
)

MUST_LEDGER = CheckerConfig(
    name="must_ledger.py",
    source_fn=lambda: read_extfile(os.path.join(HERE, "must_ledger.py")),
    interpreter=f"file:{os.path.join(HERE, 'must_ledger.py')}",
    calls=[],   # see WAIVERS / the report: must_ledger's document is a (SPEC.md-fragment, ledger-json)
                # PAIR whose sha256 must match by CONTENT hash — a poison must recompute a real sha,
                # which this generator's key-path/near-miss vocabulary does not model. Attempted and
                # explicitly reported as out of reach below, not silently absent from CHECKERS.
)


CHECKERS = {
    "VD_PY": VD_PY,
    "RS_PY_FAILCLOSED": RS_PY_FAILCLOSED,
    "RS_PY_STREAM_FAILCLOSED": RS_PY_STREAM_FAILCLOSED,
    "ZR_PY_NO_OK": ZR_PY_NO_OK,
    "ZR_PY_HAS_OK": ZR_PY_HAS_OK,
    "CHAN_PY": CHAN_PY,
    "ck83_defect": CK83_DEFECT,
    "ck83_control": CK83_CONTROL,
    "incomplete_check.py": INCOMPLETE_CHECK,
    "fs_position_check.py": FS_POSITION_CHECK,
}

# lineno -> reason, PER CHECKER. Every entry here is a comparison the classifier found and could NOT
# resolve to a poisonable document field — printed loudly by mutation_poison_gen.py regardless
# (never silently dropped), and waived here (with a stated reason) rather than failing the whole run
# on a generalisation gap that is not a security-relevant blind spot.
WAIVERS = {
    "fs_position_check.py": [
        (50, "`len(sys.argv) != 5` is the script's own usage/argc guard, not a document comparison "
             "— there is no document field for a wrong argument COUNT to poison. Every OTHER "
             "comparison in this checker resolved and is mechanically covered above."),
    ],
    "incomplete_check.py": [
        (36, "`len(sys.argv) != 5` is the script's own usage/argc guard, not a document comparison — "
             "there is no document field for a wrong argument COUNT to poison."),
        (67, "`'Fs' in (f.get('incomplete') or [])` reads the COMPREHENSION LOOP VARIABLE `f` inside "
             "`marked = [f for f in fns if ...]` — the same per-item list-filter shape as "
             "fs_position_check.py's `unit()` helper, but written inline rather than as a named "
             "function this generator can trace a call-site argument into. Not silently assumed safe: "
             "the SAME list (`fns`, i.e. `dep.functions`) is independently exercised by "
             "fs_position_check.py's OWN per-entry `paths`/`incomplete` near-miss coverage above."),
    ],
    "VD_PY": [
        (15, "`unev` projects `[u.get('rule') for u in d.get('unevaluated',[])]` through a list "
             "comprehension before comparing — this generator resolves a bare `X.get(key)` and the "
             "`any(...)==LIT` existential form, but not an arbitrary per-item PROJECTION feeding a "
             "list/set-equality one level up. Reconstructing the object shape a superset/subset poison "
             "would need (a list of {'rule': ...} dicts, not bare strings) requires inverting the "
             "projection, which this tool does not attempt rather than guess at. NOT silently assumed "
             "safe: this exact condition (VD_PY's `unev` mode) already carries hand-authored superset/"
             "subset near-miss fixtures in mutation-gate.sh (A5), so it is independently covered there."),
    ],
    "ck83_control": [
        (4, "`sb != rb` compares the RAW BYTES of two whole files (argv1 vs argv2) for equality — "
            "there is no single document/key-path here at all, the compared 'value' IS an entire "
            "slot's content. This generator's vocabulary is per-FIELD comparisons within a document; "
            "whole-document byte-equality is a structurally different shape (same one ck83_control's "
            "OWN historical fix required a same-length/different-bytes pair for, by hand). Already "
            "covered by mutation-gate.sh's own PART83/ck83_control(byte-equal) row; not reproduced here."),
        (13, "`'AS-EFF-006' not in rules` where `rules = sorted(v.get('rule') for v in ...)` is a "
             "membership test over a PROJECTED, SORTED generator expression, the same projection gap "
             "as VD_PY's `unev` above. Not one of the historically-documented A1-S6 bypasses (that "
             "condition was correct from the first draft), so its absence here does not weaken the "
             "retro-test control."),
    ],
}
