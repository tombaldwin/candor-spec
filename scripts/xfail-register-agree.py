#!/usr/bin/env python3
"""The xfail ledger and SOUNDNESS.md are two records of one fact — check they agree.

SOUNDNESS R647, and R646 is the instance that produced it.

Every conformance generator carries an `XFAIL` dict keyed by `(arm, engine)` whose value names the
SOUNDNESS row the expectation rests on. R475 established that every entry names a row, and
`part_declarations.py` checks the row EXISTS. **Nothing checked that the row and the xfail AGREE about
WHICH ENGINES are affected.** So retiring one engine's arm leaves the row asserting a stale engine set,
and the register is the document a reader trusts for exactly that.

DIRECTION, stated because it decides how hard this gate bites: a reader is told a defect is live in an
engine that has fixed it. That is the MIRROR of the cardinal sin — it costs re-derivation, not a missed
defect — so the checks below are ordered by how objective they are, and the prose-dependent one is an
ADVISORY rather than a failure.

  [1] HARD  — every XFAIL note cites at least one row id.
  [2] HARD  — every cited row EXISTS in the register.
  [3] HARD  — no cited row reads as CLOSED while an xfail still claims an engine fails. Uses
              `soundness_status.bucket()` rather than a second opinion about what "closed" means (§G:
              ask the authority, never reimplement it), so this gate cannot drift from the status tool.
  [4] HARD  — for every engine an xfail names, the row MENTIONS that engine somewhere. If the register
              does not even name the engine whose arm is xfailed, it cannot be read for that fact.
THE DIRECTION R647 NAMES MOST LOUDLY IS THE ONE THIS GATE DOES NOT CHECK, and that is a measurement
rather than an omission. R647's harm is "a reader is told a defect is live in an engine that fixed it" —
i.e. the row claims MORE engines than the xfail table does. I built that as advisory check [5]: engines
the row NAMES that the xfail set does not. It fired on 4 of 4 live rows, every time saying "the row names
java/rust/swift/ts", because a register row of this era DISCUSSES all four engines as a matter of course —
R533 says "silently pure in three engines of four", R613 says "java, rust and swift all read pure". The
status cell is no better: R533's names rust (as FIXED) alongside java and swift (as open).

So the naive form cannot distinguish "claims this engine is affected" from "mentions this engine", and a
warning that fires on every row is noise — which is how a real one gets skipped. Check [5] was REMOVED
rather than shipped at 4-of-4. What is left is three checks that are objective, and the stale-engine-set
direction stays unchecked, named here, with the reason: it needs prose understanding, which is why R647
records that nothing reads these two documents together.

WHY THE LIVE SURFACE BEING SMALL DOES NOT MAKE THIS DECORATIVE. At the time of writing, one generator
has entries: 5 in `gen_chained_dispatch.py`, citing R533, R548, R607 and R613 — and the register AGREES
with all of them. A gate that is green on arrival and has never failed is the shape this register keeps
finding in its own instruments, so `--selftest` seeds poison for every hard check and requires each one
to fire.
"""
import ast
import glob
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

ENGINES = ("rust", "java", "ts", "swift")
ROW_RE = re.compile(r'\bR\d{2,4}[a-z]?\b')


def xfail_entries(paths=None):
    """[(generator, arm, engine, note, [row ids])] across every generator's XFAIL literal.

    Parsed with `ast`, not a regex: the tables carry multi-line notes and nested quotes, and a regex
    over them is the shape that counted 96 of 175 elsewhere in this repo.
    """
    out = []
    for f in sorted(paths or glob.glob(str(ROOT / "conformance" / "gen_*.py"))):
        src = pathlib.Path(f).read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(getattr(t, "id", "") == "XFAIL" for t in node.targets):
                continue
            try:
                table = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for key, note in (table or {}).items():
                arm, engine = (key if isinstance(key, tuple) and len(key) == 2 else (str(key), "?"))
                out.append((os.path.basename(f), arm, engine, note, sorted(set(ROW_RE.findall(str(note))))))
    return out


def register_rows(path=None):
    """row id -> (whole line, status cell). The register is read ONCE, by the shared recogniser's shape."""
    p = path or (ROOT / "SOUNDNESS.md")
    rows = {}
    for line in p.read_text().split("\n"):
        m = re.match(r'^\| (R\d+[a-z]?) ', line)
        if not m:
            continue
        cells = re.split(r'(?<!\\)\|', line)
        rows[m.group(1)] = (line, cells[3] if len(cells) > 3 else "")
    return rows


def check(gen_paths=None, register=None):
    """(hard failures, advisories) — both as printable strings."""
    hard, adv = [], []
    entries = xfail_entries(gen_paths)
    rows = register_rows(register)

    # §G — ask the status tool what "closed" means rather than holding a second opinion. It must be
    # loaded BY PATH: the file is `soundness-status.py` with a HYPHEN, so `import soundness_status`
    # raises, and the first cut of this function swallowed that in a bare `except` and set `bucket =
    # None` — which made check [3] SILENTLY DISAPPEAR. Its selftest case caught it, which is the only
    # reason this comment exists: a vacuous guard inside the gate written to catch vacuous guards.
    # An unloadable status tool is now a REFUSAL, not a skip.
    bucket = None
    try:
        import importlib.util
        _p = ROOT / "scripts" / "soundness-status.py"
        _spec = importlib.util.spec_from_file_location("_ss", _p)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        bucket = _mod.bucket
    except Exception as exc:
        hard.append("could not load scripts/soundness-status.py to ask what CLOSED means (%s). Check "
                    "[3] cannot run, and an unrunnable check must not read as agreement." % exc)

    per_row = {}
    for gen, arm, engine, note, ids in entries:
        if not ids:
            hard.append("%s (%s, %s): the XFAIL note names NO SOUNDNESS row — %r" % (gen, arm, engine, str(note)[:60]))
            continue
        for rid in ids:
            if rid not in rows:
                hard.append("%s (%s, %s): cites %s, which is not a row in the register" % (gen, arm, engine, rid))
                continue
            per_row.setdefault(rid, set()).add(engine)

    for rid, engs in sorted(per_row.items()):
        line, _status = rows[rid]
        if bucket is not None:
            b = bucket(line)
            if b in ("closed-with-fix", "resolved-no-fix"):
                hard.append("%s buckets %r while an xfail still claims %s FAILS. A PASSING xfail is "
                            "reported by the suite itself; this is the other direction — the ROW says "
                            "done and the expectation says not." % (rid, b, "/".join(sorted(engs))))
        low = line.lower()
        for e in sorted(engs):
            if e in ENGINES and e not in low:
                hard.append("%s is xfailed for %s and the row never mentions %s — the register cannot "
                            "be read for the one fact the expectation rests on." % (rid, e, e))
    # (no [5] — see the module docstring: measured at 4-of-4 and removed as noise)
    return hard, adv


def selftest():
    """Seed poison for every HARD check and require each to fire. A gate green on arrival needs this."""
    import tempfile
    bad = 0

    def drive(name, gen_src, reg_src, want_hard):
        nonlocal bad
        with tempfile.TemporaryDirectory() as td:
            g = pathlib.Path(td) / "gen_probe.py"
            g.write_text(gen_src)
            r = pathlib.Path(td) / "REG.md"
            r.write_text(reg_src)
            hard, _adv = check([str(g)], r)
            got = len(hard)
            ok = (got > 0) if want_hard else (got == 0)
            print("  %s %-52s hard=%d" % ("ok  " if ok else "FAIL", name, got))
            if not ok:
                bad += 1
                for h in hard:
                    print("        " + h)

    HDR = "| id | date | engine | evidence | notes |\n|---|---|---|---|---|\n"
    agree = HDR + "| R900 swift: a thing | 2026-09-27 | swift — OPEN | e | n |\n"

    drive("agreeing table passes",
          'XFAIL = {("a1", "swift"): "R900"}\n', agree, False)
    drive("[1] a note citing NO row fires",
          'XFAIL = {("a1", "swift"): "because reasons"}\n', agree, True)
    drive("[2] a note citing a row that does not exist fires",
          'XFAIL = {("a1", "swift"): "R901"}\n', agree, True)
    drive("[4] xfailed for an engine the row never mentions fires",
          'XFAIL = {("a1", "java"): "R900"}\n', agree, True)
    drive("[3] a row that reads CLOSED while still xfailed fires",
          'XFAIL = {("a1", "swift"): "R900"}\n',
          HDR + "| R900 swift: a thing | 2026-09-27 | swift — **CLOSED — candor-swift `abc1234`** | e | n |\n",
          True)
    drive("an empty XFAIL table is not a failure",
          'XFAIL = {}\n', agree, False)
    drive("a generator with no XFAIL at all is not a failure",
          'OTHER = {"x": 1}\n', agree, False)

    # There is no advisory case: check [5] was measured at 4-of-4 on the live register and removed.
    # Keeping a selftest for a check that does not exist would be worse than having neither.
    print("xfail-register-agree selftest: " + ("OK" if not bad else "FAILED (%d)" % bad))
    return 1 if bad else 0


def main(argv):
    if len(argv) > 1 and argv[1] == "--selftest":
        return selftest()
    entries = xfail_entries()
    hard, adv = check()
    tables = len({e[0] for e in entries})
    print("xfail-register-agree: %d live XFAIL entr(ies) across %d generator table(s), %d row(s) cited"
          % (len(entries), tables, len({r for e in entries for r in e[4]})))
    for a in adv:
        print("  ADVISORY: " + a)
    if hard:
        for h in hard:
            print("  ✘ " + h)
        print("xfail-register-agree: FAILED — the xfail ledger and the register disagree. One of them is")
        print("  wrong about which engines are affected, and the register is the document a reader trusts.")
        return 1
    if not entries:
        # An empty ledger is legitimate (every expectation retired) but it must not read as agreement:
        # this gate would then be passing over nothing at all, which is the vacuity shape.
        print("  NOTE: no live XFAIL entries anywhere. Nothing to disagree about — this run checked NOTHING.")
    print("xfail-register-agree: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
