#!/usr/bin/env python3
"""How many CARDINAL SINS are open? Answer it in one command. SOUNDNESS R771.

    python3 scripts/sin-direction.py            # counts, by direction and engine
    python3 scripts/sin-direction.py --list     # …plus the row ids
    python3 scripts/sin-direction.py --selftest

WHY THIS EXISTS, and it is the most-asked question about this register. On 2026-09-28 the
question "how many sins are open?" cost two failed automated attempts and a full manual read of
126 rows. The two lexical attempts returned **19** and **11**; the truth, read row by row, was
**48**. Both were wrong because the register records direction in PROSE — a row states its own
severity in a sentence, often CORRECTS it later in the same row ("Was: …"), and also discusses
other rows, so any keyword search matches the neighbours as well as the subject.

That is worse than an inconvenience. The register's own history records the open-sin count being
miscounted repeatedly, once because a row's wording ("the proposed fix shape is REFUTED") made a
LIVE sin invisible to the status tool. A number that cannot be recomputed on demand is a number
that silently goes stale.

THE FIX IS A DECLARED TOKEN, NOT A CLEVERER PARSER. Every OPEN row carries exactly one of these
at the end of its STATUS cell:

    DIR=SILENT      the engine is SILENT where an effect exists — the cardinal sin. The practical
                    test: a gate like `deny Fs f` exits 0 over code that really performs it.
    DIR=NOTSILENT   anything else: over-disclosure, fabrication/over-charge, a precision gap that
                    hedges with `Unknown`, or an instrument/process/spec row. NOT a sin.
    DIR=UNSETTLED   not established either way — typically a row asserting a missed join without
                    an EXECUTED gate result. Counted separately and never folded into either side.

WHY THE TOKEN GOES AT THE END OF THE STATUS CELL. `soundness-status.py` requires `OPEN` to sit
IMMEDIATELY after the engine dash, so a token prefixed to that cell would break bucketing. Appended,
it is inert: backfilling all 126 open rows left closed-with-fix/partly/resolved/cites-a-sha at
469/11/57/4, unchanged. The token values also avoid every closure word — note `DISCLOSED` was
REJECTED as a value because it contains `CLOSED`, and this file's own history includes a bare
`\\bCLOSED\\b` reading half the register as resolved.

SCOPE, STATED SO THE GREEN DOES NOT OVERCLAIM: only OPEN rows are required to carry a token,
because only they can be a live sin. Closed rows may acquire one as they are touched. So this
tool answers "how many sins are OPEN", never "how many have we ever had".
"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALID = ("SILENT", "NOTSILENT", "UNSETTLED")
TOKEN = re.compile(r'\bDIR=([A-Z]+)')


def open_ids(path=None):
    """The OPEN row ids, taken from `soundness-status.py --ids` — the authority's own answer.

    §G, and this tool needed the lesson twice. First it called `bucket(line)` without the outcome
    cell and reported 116 where the authority said 127. Then, having fixed that, it still scanned
    every `|`-row in the FILE — and SOUNDNESS.md contains tables that are not the register, so it
    demanded a direction token from R2..R9, R67, R72 and R230, none of which the authority calls
    open at all. Replicating "which table am I in" would have been a third recogniser in a repo
    whose R641 exists because the SECOND one lost rows.

    So: do not re-derive it. Ask. A failure here REFUSES — an unrunnable authority must not read
    as an empty open set, which would make this gate pass by knowing nothing.
    """
    import subprocess
    cmd = [sys.executable, str(ROOT / "scripts" / "soundness-status.py"), "--ids"]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       cwd=str(path.parent) if path else str(ROOT))
    if r.returncode != 0:
        raise RuntimeError("soundness-status.py --ids exited %d: %s" % (r.returncode, r.stderr[:200]))
    ids = [l.strip() for l in r.stdout.split("\n") if re.match(r'^R\d+[a-z]?$', l.strip())]
    if not ids:
        raise RuntimeError("soundness-status.py --ids produced NO ids; refusing to report a "
                           "direction audit over an empty open set.")
    return set(ids)


def _authority():
    """Ask soundness-status.py what OPEN means — §G, never hold a second opinion.

    Loaded BY PATH because the filename has a HYPHEN, so `import soundness_status` raises. An
    unloadable status tool is a REFUSAL, not a skip: a check that cannot run must not read as
    agreement (the lesson `xfail-register-agree.py` learned the hard way, where a bare `except`
    made a hard check silently disappear).
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import soundness_row
    spec = importlib.util.spec_from_file_location("_ss", ROOT / "scripts" / "soundness-status.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.bucket, soundness_row


def rows(path=None, sr=None):
    """[(id, engine, whole line)] for every register row, in file order.

    USES THE SHARED RECOGNISER `soundness_row.row_id`, not a local regex. R641 is why: a second
    recogniser in this repo missed a doubled-leading-pipe row, so it vanished from the counts and
    the shipping-defect list while another tool went red on it. One recogniser, one selftest table.
    """
    out = []
    for line in (path or ROOT / "SOUNDNESS.md").read_text().split("\n"):
        rid = sr.row_id(line)
        if not rid:
            continue
        # The subject prefix is `<engine>:` — but it may be MULTI-WORD ("all engines:", "rust-deep:")
        # and a few early rows carry NO prefix at all, going straight into the claim. Matching only
        # `[a-z-]+:` attributed R533 ("all engines") to nobody. An unattributable row is reported as
        # such rather than silently bucketed under "?", because a breakdown that quietly loses rows is
        # the same shape as every other under-report in this register.
        eng = re.match(r'^\|+ R\d+[a-z]? ([a-z][a-z -]{0,20}?):(?!:)', line)
        out.append((rid, eng.group(1).strip() if eng else None, line))
    return out


def audit(path=None, bucket=None, sr=None, open_set=None):
    """(counts, per_engine, problems). `problems` is what makes this a gate rather than a report."""
    if bucket is None or sr is None:
        bucket, sr = _authority()
    opens = open_set if open_set is not None else open_ids(path)
    counts, per_engine, problems = {v: 0 for v in VALID}, {}, []
    listed = {v: [] for v in VALID}
    seen = set()
    for rid, eng, line in rows(path, sr):
        if rid not in opens:
            # A closed row carrying a token is fine and is not checked; see SCOPE above.
            continue
        seen.add(rid)
        found = TOKEN.findall(line)
        if not found:
            problems.append("%s is OPEN and declares no DIR= token. Every open row must say whether "
                            "it is a silence; an undeclared row is invisible to the sin count." % rid)
            continue
        if len(found) > 1:
            problems.append("%s declares %d DIR= tokens (%s) — exactly one, or the count is a guess."
                            % (rid, len(found), ", ".join(found)))
            continue
        tok = found[0]
        if tok not in VALID:
            problems.append("%s declares DIR=%s, which is not one of %s." % (rid, tok, "/".join(VALID)))
            continue
        counts[tok] += 1
        listed[tok].append(rid)
        if tok == "SILENT":
            per_engine[eng if eng else "(no subject prefix)"] = \
                per_engine.get(eng if eng else "(no subject prefix)", 0) + 1
    for rid in sorted(opens - seen):
        problems.append("%s is OPEN per soundness-status.py but no row for it was found in the "
                        "register table — the two tools disagree about what exists." % rid)
    return counts, per_engine, problems, listed


def main(argv):
    if "--selftest" in argv:
        return selftest()
    counts, per_engine, problems, listed = audit()
    total = sum(counts.values())
    print("SOUNDNESS direction — %d open row(s)" % total)
    print("  OPEN CARDINAL SINS      %d" % counts["SILENT"])
    print("  not a silence           %d" % counts["NOTSILENT"])
    print("  unsettled either way    %d" % counts["UNSETTLED"])
    if per_engine:
        print("\n  sins by engine: " + ", ".join("%s %d" % (k, v)
              for k, v in sorted(per_engine.items(), key=lambda kv: -kv[1])))
    if "--list" in argv:
        for v in VALID:
            if listed[v]:
                print("\n  DIR=%s (%d):\n    %s" % (v, len(listed[v]), " ".join(listed[v])))
    if counts["UNSETTLED"]:
        print("\n  NOTE: %d row(s) are UNSETTLED and are in NEITHER count. They are usually a row "
              "asserting" % counts["UNSETTLED"])
        print("  a missed join with no EXECUTED gate result. Reading them all as sins would give "
              "%d." % (counts["SILENT"] + counts["UNSETTLED"]))
    if problems:
        print()
        for p in problems:
            print("  ✘ " + p)
        print("sin-direction: FAILED — %d open row(s) do not declare a direction, so the sin count "
              "above is a LOWER BOUND" % len(problems))
        print("  rather than an answer. Add DIR=SILENT / DIR=NOTSILENT / DIR=UNSETTLED to the status cell.")
        return 1
    print("\nsin-direction: OK — every open row declares a direction.")
    return 0


def selftest():
    """Seed each failure mode and require it to fire. A gate green on arrival needs this."""
    import tempfile
    bad = 0
    HDR = "| id | date | engine | evidence | notes |\n|---|---|---|---|---|\n"

    def drive(name, body, want_problems, want_silent=None, opens=None):
        nonlocal bad
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "REG.md"
            f.write_text(HDR + body)
            # The open set is supplied per case: the real tool asks the authority, and the
            # authority is not available over a temp fixture. R904's case passes an EMPTY set
            # deliberately — that IS what 'closed' means here, and it is the scope assertion.
            counts, _eng, problems, _l = audit(f, open_set=opens)
            ok = (len(problems) > 0) == want_problems
            if ok and want_silent is not None:
                ok = counts["SILENT"] == want_silent
            print("  %s %-54s problems=%d silent=%d"
                  % ("ok  " if ok else "FAIL", name, len(problems), counts["SILENT"]))
            if not ok:
                bad += 1
                for p in problems:
                    print("        " + p)

    drive("a tokened open row counts",
          "| R900 rust: a thing | 2026-09-28 | rust — OPEN DIR=SILENT | e | n |\n", False, 1, opens={"R900"})
    drive("an open row with NO token FAILS",
          "| R901 rust: a thing | 2026-09-28 | rust — OPEN | e | n |\n", True, opens={"R901"})
    drive("TWO tokens on one row FAILS",
          "| R902 rust: a thing | 2026-09-28 | rust — OPEN DIR=SILENT DIR=NOTSILENT | e | n |\n", True, opens={"R902"})
    drive("an UNKNOWN token value FAILS",
          "| R903 rust: a thing | 2026-09-28 | rust — OPEN DIR=MAYBE | e | n |\n", True, opens={"R903"})
    drive("a CLOSED row needs no token (scope)",
          "| R904 rust: a thing | 2026-09-28 | rust — **CLOSED — candor-rust `abc1234`** | e | n |\n", False, 0, opens=set())
    # THE ONE THAT MATTERS: a row whose PROSE screams "silent under-report" but whose DECLARED
    # direction is NOTSILENT must count as NOTSILENT. The whole point is that the declaration
    # outranks inference — that is how a live sin got hidden by its own wording before.
    drive("the DECLARATION outranks the prose",
          "| R905 rust: **A SILENT UNDER-REPORT, CARDINAL SIN** | 2026-09-28 | "
          "rust — OPEN DIR=NOTSILENT | e | n |\n", False, 0, opens={"R905"})
    drive("UNSETTLED is in neither count",
          "| R906 rust: a thing | 2026-09-28 | rust — OPEN DIR=UNSETTLED | e | n |\n", False, 0, opens={"R906"})
    print("sin-direction selftest: " + ("OK" if not bad else "FAILED (%d)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
