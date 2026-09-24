#!/usr/bin/env python3
"""soundness-status.py — how many defects are OPEN, and which.

    python3 scripts/soundness-status.py            # counts + the open list
    python3 scripts/soundness-status.py --ids      # open IDs only, one per line

WHY THIS EXISTS. Asked "how many known defects are we shipping", I could not answer it from the register.
SOUNDNESS.md records closure in PROSE — "**CLOSED candor-rust `abc1234`**" — and only 37 of 472 rows use
the strikethrough convention, so every row closed this week still read as OPEN by that convention. The
answer took forensic grepping and came out "approximately 25, derived". A register whose central question
needs forensics is a register that will be wrong when it matters.

This does not invent a new schema or ask anyone to backfill 472 rows. It reads the prose markers that are
ALREADY there, and — the important part — it reports what it CANNOT decide rather than guessing:

    CLOSED     a closure marker is present  (CLOSED / FIXED / REFUTED / RETIRED / ~~Rn~~ / WITHDRAWN)
    OPEN       no marker anywhere in the row
    UNCERTAIN  a marker appears, but so does an OPEN/LIVE marker — the row is arguing with itself,
               or it is citing another row's closure. These are listed individually and are NOT
               silently counted as either.

The UNCERTAIN bucket is the point. A status tool that resolves ambiguity by picking a side is how a
register starts lying; this one makes the ambiguity the output. If that bucket grows, the fix is to
sharpen the rows it names, not to sharpen the regex.
"""
import re, sys, pathlib

# `fail closed` / `fail-closed` / `closed-world` are ORDINARY VOCABULARY here — this contract is about
# failing closed — so a bare \bCLOSED\b marks half the register resolved. Measured: R520 was filed as an
# open defect and read as CLOSED purely because its evidence says "nothing to fail closed OVER". Strip
# those spellings before looking for the marker; a status tool that mistakes the subject matter for a
# verdict is worse than no tool.
_NOT_A_VERDICT = re.compile(r'fails?[- ]closed|failing[- ]closed|closed[- ]world|fail[- ]closed', re.I)
# …AND EXPLICIT NEGATION OF THE CLOSURE WORD, which is a different failure from the fail-closed idiom
# above. Measured 2026-09-21 on R524: the row says a defect was "surfaced by the R519 work and NOT closed
# by it" and cites R519's fix SHA to say WHICH work did not close it — so CLOSURE matched `closed`,
# FIXSHA matched the sha, and the row was filed under closed-with-fix. It never appeared in the OPEN list
# the tool exists to produce, and the row was one I had written an hour earlier and was about to escalate.
# A status tool that reads a row saying NOT CLOSED as CLOSED is the register's own cardinal-sin shape.
_NEGATED_CLOSURE = re.compile(r"\b(?:not|never|isn'?t|was\s?n'?t|are\s?n'?t)\s+(?:yet\s+)?"
                              r"(?:been\s+)?(?:closed|fixed|resolved|retired|withdrawn)\b", re.I)
CLOSURE = re.compile(r'\bCLOSED\b|\bFIXED\b|\bREFUTED\b|\bRETIRED\b|\bWITHDRAWN\b|\bDECLINED\b|~~R\d+~~', re.I)
FIXSHA  = re.compile(r'`?\b[0-9a-f]{7,40}\b`?')   # backticked OR bare: measured across all 476 rows,
                                                 # accepting bare hex added exactly 2 matches and no
                                                 # false positives, so the looser form is the correct one

# THE DISCRIMINATOR, and why it is this one. The first version of this script asked only "does a closure
# WORD appear anywhere in the row", and put 191 of 476 rows in an UNCERTAIN bucket — useless, because a
# closed row routinely discusses an open question and an open row routinely cites another row's closure.
# The signal that actually separates them is whether the row CITES A FIX: a defect closed by a code change
# names the commit. That takes the ambiguous bucket from 191 to 92, and the 92 are a REAL category rather
# than a parsing failure — resolved with no code change (declined, refuted, accepted as a limit).
#
# Sharpening this further would be the wrong move. The remaining ambiguity is in the ROWS, and the honest
# output is four buckets that say which question each row leaves open.

# AN EXPLICIT DECLARATION BEATS INFERENCE. A row whose outcome cell OPENS with `OPEN` is its author
# saying so in as many words, and no amount of SHA-spotting should overrule that. R524 says
# "**OPEN — needs a family-level ruling, not a patch**" and cites R519's fix SHA to name the work that
# did NOT close it; the tool read the sha and filed it under "cites a sha, read it" — better than the
# closed-with-fix it started in, but still not the list its author put it on. Anchored to the START of
# the cell so the WORD "open" in ordinary prose ("an open question", "left open by") cannot trigger it.
# SOUNDNESS R588 — AND THE DECLARATION IS NOT ALWAYS IN THE OUTCOME CELL. The register overloads the
# THIRD column ("engine") as the row's CURRENT STATUS for every row filed before ~R430 — `**CLOSED —
# candor-rust `ff6efad`**` sits there while the outcome cell still carries the original "Not yet fixed.
# The fix is to route…" note written at filing. That convention is fine; reading only ONE of the two
# cells is not. 24 rows whose status cell OPENS with `OPEN` or `REOPENED` were bucketed
# `closed-with-fix`/`resolved-no-fix` — R198, R209, R227, R305 and R372 among them, every one saying
# "Not fixed" in the outcome cell, R372 a declared CARDINAL SIN. This is the FOURTH defect of this shape
# in this file and the second in two days; the first three are enumerated in `bucket()` below. The
# instrument that exists to find silent under-reports was under-reporting its own shipping-defect list
# by roughly a quarter.
#
# `REOPENED` and `STILL OPEN` are here because both are used as status heads (R140, R429) and neither
# is the word the R524 fix anchored on. Still CASE-SENSITIVE and still anchored to the head of the cell:
# the shouty form is the convention, and a lowercase "open question" in prose must not move a closed row.
_DECLARED_OPEN = re.compile(r'^\s*(?:\*\*|__)?\s*(?:\u26a0\s*)?(?:STILL\s+OPEN|REOPENED|OPEN)\b')
# …AND A STALE STATUS HEAD MUST NOT OUTRANK A LATER CLOSURE. R230's status cell still opens `**OPEN —
# mechanism now MEASURED…` while its OUTCOME cell opens `**RESOLVED 2026-09-06 by building the shape
# this row said would decide it**`. The outcome cell is the later word, so an explicit closure at ITS
# head suppresses the status-cell shortcut above. Without this the fix trades 24 false closures for a
# handful of false OPENs, which is the same error pointing the other way.
_DECLARED_RESOLVED = re.compile(r'^\s*(?:\*\*|__)?\s*(?:\u26a0\s*)?'
                                r'(?:RESOLVED|CLOSED|FIXED|WITHDRAWN|RETRACTED|SUPERSEDED)\b')
# A CLOSURE WITH A DECLARED OPEN REMAINDER IS NOT A CLOSURE, AND IT IS NOT FULLY OPEN EITHER. Eleven
# rows head their status cell `PARTLY CLOSED` / `HALF CLOSED` / `FIRST HALF FIXED` and then name what is
# still owed (R101, R190, R208, R214, R243, R249, R347, R414 …). Bucketing them `closed-with-fix` hides
# the remainder; bucketing them `open` overstates it. They get their own line so a reader is SENT to
# them rather than told an answer — the same reason `cites-a-sha-only` exists.
# The shape of a closure recorded INSIDE a row's prose: a closure word followed closely by a commit.
# Requiring the sha is what keeps it off the many rows that merely DISCUSS closing something — "the fix
# would close it", "R99 closed the sibling" — because a row that cites a commit for its own closure is
# making a claim about ITSELF. Not anchored, unlike the status-head patterns: this is deliberately
# looking for a statement buried mid-cell, which is the whole failure.
# SOUNDNESS R591 — AND IT MUST NOT FIRE INSIDE A *PARTIAL* CLOSURE. The first version matched
# `\bCLOSED\b`, which sits inside "PARTIALLY CLOSED", "HALF CLOSED", "SWIFT HALF CLOSED" and "(b)
# CLOSED" — so the advisory named R198, R209 and R576 as rows that "say both" when all three say
# PARTLY, correctly, and are correctly open. The check was right to fire and wrong about what it had
# found, which is the worse failure of the two: a reader who checks three and finds them all fine
# stops reading the fourth.
_PARTIAL_BEFORE = re.compile(r'(?:PARTIALLY|PARTLY|HALF|\(\w\)|\bONE\s+HALF)\s*$', re.I)
_BODY_CLOSURE = re.compile(
    r'\b(?:NOW\s+)?(?:FULLY\s+|BOTH\s+HALVES\s+(?:OF\s+THIS\s+ROW\s+)?(?:ARE\s+)?)?'
    r'CLOSED\b[^.`]{0,70}`[0-9a-f]{7,40}`')


def _body_closure(body):
    """A closure recorded mid-cell, EXCLUDING one that is explicitly partial."""
    for m in _BODY_CLOSURE.finditer(body):
        head = body[max(0, m.start() - 24):m.start()]
        if _PARTIAL_BEFORE.search(head.rstrip()):
            continue
        return m
    return None

_DECLARED_PARTLY = re.compile(r'^\s*(?:\*\*|__)?\s*(?:\u26a0\s*)?'
                              r'(?:PARTLY|PARTIALLY|HALF|\w+\s+HALF)\b[^|]{0,28}?(?:CLOSED|FIXED)', re.I)
# SOUNDNESS R553 — A DECLARATION OF NON-CLOSURE AT THE HEAD OF THE CELL, which is a status claim, as
# opposed to a negation buried in prose and SCOPED TO SOME OTHER WORK ("surfaced by the R519 work and NOT
# closed by it"), which is not. Anchored for exactly the reason `_DECLARED_OPEN` is: the first thing the
# cell says is the row's own verdict; anything later is commentary about something else. The selftest
# case for that scoped shape is what stopped this being written unanchored — it must stay `cites-a-sha-only`.
_DECLARED_NOT_FIXED = re.compile(r"^\s*(?:\*\*|__)?\s*(?:not|never)\s+(?:yet\s+)?(?:fixed|closed|resolved)\b", re.I)


def _idkey(rid):
    """Sort R529 before R529b before R530. `int(rid[1:])` raised on a lettered sub-row and the OPEN
    listing died after printing its counts — 52 open, none named. Added 2026-09-22 with the suffix fix."""
    m = re.match(r'R(\d+)([a-z]*)$', rid)
    return (int(m.group(1)), m.group(2)) if m else (0, rid)


def bucket(line, outcome=None):
    # The STATUS cell is the register's third column — see `_DECLARED_OPEN`. Split the same
    # escaped-pipe-aware way `main()` does, or a row with `\|` in a code sample shifts every index.
    _cells = re.split(r'(?<!\\)\|', line)
    status = _cells[3] if len(_cells) > 3 else ""
    oc = outcome if outcome is not None else ""
    # An explicit closure at the head of the OUTCOME cell is the row's LATER word and wins over a status
    # head left stale (R230). Everything else: a declared OPEN in EITHER status cell outranks inference.
    # SOUNDNESS R591 — AND THE RULE MUST BE SYMMETRIC, which R588 left it not. R588 taught
    # `_DECLARED_OPEN` to read the STATUS cell as well as the outcome cell, because the register
    # overloads column 3 as current status. It did not teach `_DECLARED_RESOLVED` the same thing, so a
    # row whose STATUS head says `RETRACTED` and whose OUTCOME head still carries its filing-time
    # "Not yet fixed" note bucketed OPEN — the asymmetry recovered 23 rows in one direction and then
    # held R126 in the other. Rows here are updated by APPENDING, so the outcome cell's HEAD is the
    # oldest thing in it; the status cell is what gets rewritten. Reading a closure in either is the
    # only rule consistent with how the file is actually edited.
    # …BUT A CELL THAT SAYS BOTH IS NOT RESOLVED. R162 heads its status cell "RESOLVED as a PROCESS
    # GAP, not a live generator defect; two real generator bugs found beside it, OPEN" — resolved word
    # first, so the head test matched and the row left the shipping-defect list while its own outcome
    # cell still ends "What a correct instrument does, NOT IMPLEMENTED" over four items. That is a
    # FALSE CLOSURE, the direction this tool must never fail in, and the symmetry fix above introduced
    # it. So a closure head only counts when the SAME cell does not also declare something open; a row
    # that says both stays open and gets read. Costs a few rows that are genuinely finished sitting on
    # the list until someone rewrites the sentence — the cheap direction.
    _SAYS_OPEN_TOO = re.compile(r'\b(?:OPEN|REOPENED|NOT\s+IMPLEMENTED|STILL\s+OWED)\b')

    def _closure_head(cell):
        return bool(_DECLARED_RESOLVED.match(cell)) and not _SAYS_OPEN_TOO.search(cell)

    resolved_head = _closure_head(oc) or _closure_head(status)
    # AND THE HEAD SAYS WHICH KIND OF CLOSURE IT IS. `closed-with-fix` asserts "a defect, and here is
    # the commit"; `resolved-no-fix` says "a DECISION, not a fix". Deciding between them by whether a
    # sha appears ANYWHERE in the row is the R553 defect one bucket over — an INCIDENTALLY cited
    # commit picking the label. R225 is the case: it resolves as an accepted-and-watched environmental
    # limit, nothing was fixed, and it landed in `closed-with-fix` on shas it merely cites as evidence
    # (`845cb32`, the commit it was MEASURED at). So when the row declares its own closure, read the
    # KIND off that declaration: a fix word with its commit beside it is a fix; a decision word with no
    # commit beside it is a decision.
    _head = next((c for c in (status, oc) if _closure_head(c)), "")
    _decided = bool(re.match(r'^\s*(?:\*\*|__)?\s*(?:\u26a0\s*)?'
                             r'(?:RESOLVED|RETRACTED|WITHDRAWN|REFUTED|SUPERSEDED)\b', _head)) \
        and not FIXSHA.search(_head[:110])
    if not resolved_head:
        if _DECLARED_OPEN.match(status) or _DECLARED_OPEN.match(oc):
            return "open"
        if _DECLARED_PARTLY.match(status):
            return "partly-closed"
    declared_not_fixed = outcome is not None and bool(_DECLARED_NOT_FIXED.match(outcome))
    line = _NOT_A_VERDICT.sub(" ", line)
    # SOUNDNESS R553 — AN EXPLICIT "NOT FIXED" OUTRANKS AN INCIDENTALLY-CITED SHA, and until 2026-09-23
    # it did not. The negation was SUBSTITUTED AWAY before the test ran, so a row reading
    # `Not fixed. … measured at abc1234` lost its only status word, matched FIXSHA on the incidental
    # commit, and landed in `cites-a-sha-only` — a bucket the report prints as "read these, they are
    # neither clearly". EIGHT of the twelve rows in that bucket said "Not fixed" in plain English.
    #
    # The consequence is the one that matters: `open` is THE SHIPPING-DEFECT LIST, and eight defects
    # that declared themselves open were being kept off it by a commit hash. The count this tool prints
    # was an UNDER-REPORT — the same class it exists to find, in the instrument that finds it. That is
    # the third defect of this shape in this file (reading `Not fixed.` as FIXED hid 32 rows; sweeping
    # the accepted-floor table added 38 phantom ones).
    #
    # A POSITIVE closure word still wins, deliberately: a row that says both is a row where something
    # WAS closed, and `closed-with-fix` sends a human to read it.
    line = _NEGATED_CLOSURE.sub(" ", line)
    w, s = bool(CLOSURE.search(line)), bool(FIXSHA.search(line))
    # SOUNDNESS R588 — `RESOLVED` at the head of the outcome cell IS a closure declaration, and CLOSURE
    # deliberately does not contain the word: `resolved`/`unresolved`/`could not be resolved` are
    # candor's vocabulary for DISPATCH, so matching them anywhere in a row would empty the resolved
    # bucket (that near-miss is a selftest case). At the HEAD of the outcome cell it is unambiguous —
    # it is the row saying what happened to IT. Without this the R230 shape (stale `OPEN` status head,
    # real closure in the outcome cell) falls through to `cites-a-sha-only`, which sends a reader to a
    # row that already answered itself.
    if resolved_head:
        w = True
    if resolved_head and _decided:
        return "resolved-no-fix"               # the row's own head calls it a decision, with no commit
    if w and s:  return "closed-with-fix"      # a defect, and here is the commit
    if w:        return "resolved-no-fix"      # declined / refuted / accepted limit — a DECISION, not a fix
    if declared_not_fixed: return "open"       # the cell OPENS by saying it is not fixed; a cited commit does not overrule that
    if s:        return "cites-a-sha-only"     # odd; read it
    return "open"                              # nothing claims this is resolved

def main(argv):
    ids_only = "--ids" in argv
    p = pathlib.Path(__file__).resolve().parent.parent / "SOUNDNESS.md"
    # ONLY THE REGISTER TABLE. SOUNDNESS.md holds seven tables with different schemas, and matching
    # `^| R\d+` across the whole file swept in the ACCEPTED-FLOOR table (R2–R9 and friends), whose shape
    # is `| id | engine | description | SILENT | low | remedy |`. Its 5th cell is a SEVERITY ("low"),
    # not an outcome, so every one of those rows carried no closure word and printed as OPEN — 38 rows
    # of garbled text at the top of the list this tool exists to produce, which is also why its row count
    # (491) disagreed with `grep -c '^| R' SOUNDNESS.md` (453). An accepted, documented limit is not a
    # shipping defect, and padding the open list with them makes the real ones harder to see.
    #
    # The register table is identified by its HEADER, not by a line number or a row count: find
    # `| entry | date | engine | class | outcome |` and take the contiguous rows under its separator,
    # which is the same contiguity rule check_soundness_tables.py enforces.
    all_lines = p.read_text().splitlines()
    rows, in_register = [], False
    for ln in all_lines:
        low = ln.lower().replace(" ", "")
        if low.startswith("|entry|date|engine|class|outcome|"):
            in_register = True
            continue
        if in_register:
            if not ln.startswith("|"):
                in_register = False
                continue
            if re.match(r'^\| ~?~?R\d+', ln):
                rows.append(ln.rstrip("\n"))
    if not rows:
        print("soundness-status: REFUSING — no `| entry | date | engine | class | outcome |` table found.",
              file=sys.stderr)
        print("  A silent empty list is exactly the under-report this tool exists to prevent.", file=sys.stderr)
        return 2
    by = {}
    for l in rows:
        # THE LETTER SUFFIX IS PART OF THE ID. `(R\d+)` dropped it, so R529c printed as "R529", R531b as
        # "R531" and R532b as "R532" — and on 2026-09-22 all three of those BASE rows were CLOSED while
        # their lettered siblings were open. The shipping-defect list was therefore naming rows that are
        # fixed: a reader looking up "R529" finds a closed row and concludes the list is wrong, or worse
        # re-opens work that is done. Sub-rows are how this register splits one finding into its separate
        # measurable parts, so collapsing them loses exactly the distinction they were created to make.
        rid = re.match(r'^\| ~?~?(R\d+[a-z]?)', l).group(1)
        # The outcome is the LAST cell of the register table; pass it separately so a declared OPEN
        # is read as a declaration rather than hunted for in the whole row's prose.
        _c = re.split(r'(?<!\\)\|', l)
        _outcome = _c[5] if len(_c) > 5 else None
        by.setdefault(bucket(l, _outcome), []).append((rid, l))

    if ids_only:
        for rid, _ in sorted(by.get("open", []), key=lambda t: _idkey(t[0])):
            print(rid)
        return 0

    print(f"SOUNDNESS status — {len(rows)} rows")
    for k in ("closed-with-fix", "partly-closed", "resolved-no-fix", "cites-a-sha-only", "open"):
        print(f"  {k:18s} {len(by.get(k, []))}")
    print()
    print("OPEN — nothing in the row claims it is resolved. THIS is the shipping-defect list:")
    for rid, l in sorted(by.get("open", []), key=lambda t: _idkey(t[0])):
        cells = re.split(r'(?<!\\)\|', l)
        eng = cells[3].strip()[:20] if len(cells) > 3 else "?"
        claim = " ".join(cells[1].split())[len(rid) + 1:][:86]
        print(f"  {rid:6s} {eng:20s} {claim}")
    # SOUNDNESS R588 (the MIRROR) — A ROW THAT SAYS BOTH. R588 fixed `bucket()` reading a declared
    # `OPEN` only in the outcome cell; the defect pointing the other way is a STATUS HEAD left at
    # `OPEN` while the row's own body records the closure, and it hid SIX rows — R140, R349, R364,
    # R372, R387, R429 — every one of them closed, cited, and sitting on the shipping-defect list.
    # R222's row already documents the shape ("STATUS CELL WAS STALE ... corrected 2026-09-07"), which
    # is the argument for detecting it rather than trusting authors to update two places.
    #
    # ADVISORY, NOT FATAL, and deliberately: a row may legitimately head `OPEN` while its body closes
    # ONE HALF — R547 read exactly that way for a day and was correct to. So this cannot decide, and
    # does not try; it prints the candidates and lets a reader settle each. Guessing here would trade
    # six false opens for an unknown number of false closures, which is the worse direction.
    contra = []
    for rid, l in by.get("open", []):
        cells = re.split(r'(?<!\\)\|', l)
        body = " ".join(cells[4:6]) if len(cells) > 5 else ""
        if _body_closure(body):
            contra.append((rid, l))
    if contra:
        print()
        print(f"SAYS BOTH — {len(contra)} row(s) bucket OPEN while the body records a closure. Read each:")
        for rid, l in sorted(contra, key=lambda t: _idkey(t[0])):
            cells = re.split(r'(?<!\\)\|', l)
            body = " ".join(cells[4:6]) if len(cells) > 5 else ""
            m = _body_closure(body)
            print(f"  {rid:6s} body says: {' '.join(m.group(0).split())[:84]}")

    if by.get("partly-closed"):
        print()
        print("PARTLY CLOSED — a fix landed and the row NAMES what is still owed. Read the remainder:")
        for rid, l in sorted(by["partly-closed"], key=lambda t: _idkey(t[0])):
            cells = re.split(r'(?<!\\)\|', l)
            head = " ".join(cells[3].split())[:96] if len(cells) > 3 else ""
            print(f"  {rid:6s} {head}")
    if by.get("cites-a-sha-only"):
        print()
        print("CITES A SHA BUT NO CLOSURE WORD — read these, they are neither clearly:")
        for rid, _ in sorted(by["cites-a-sha-only"], key=lambda t: _idkey(t[0])):
            print(f"  {rid}")
    return 0

def selftest():
    """Prove the bucketing can distinguish a claim of closure from a denial of one.

    WHY THIS EXISTS. For its whole life this tool read `Not fixed.` as FIXED. `CLOSURE` matched the word
    `fixed`, nothing looked left of it, and a row whose outcome cell opens "Not fixed." was filed as
    resolved — so on 2026-09-21, 43 rows were in the wrong bucket and 32 of them were REAL OPEN DEFECTS
    absent from the list this tool exists to print. The docstring called the OPEN bucket "the
    shipping-defect list" while the shipping-defect list was missing a third of itself.

    Each case below is a string this tool got wrong, or a near-miss that must NOT move. The domain cases
    are the ones that matter: `unresolved` and "could not be resolved" are candor's own vocabulary for
    DISPATCH, not for a row's status, and a strip that ate them would empty the resolved bucket instead.
    """
    cases = [
        # (text, expected bucket)
        ("Not fixed. One producer, or a normalisation at the writer.",          "open"),
        # SOUNDNESS R553 — THE SAME DECLARATION, PLUS AN INCIDENTAL COMMIT. Before 2026-09-23 the
        # negation was substituted away BEFORE the test ran, so the row lost its only status word,
        # matched FIXSHA on a commit it merely cites, and landed in `cites-a-sha-only`. NINE rows did
        # this — R126/R137/R138/R162/R202/R213/R225/R231/R369 — every one of them saying "Not fixed" in
        # plain English while absent from the list this tool calls the shipping-defect list.
        ("Not fixed. The remedy is known; measured at `abc1234`.",              "open"),
        ("Not yet fixed — see the A/B in `deadbee1`.",                          "open"),
        ("**Not fixed.** The gap is the finding. `0123456`",                    "open"),
        # …AND THE NEAR-MISS THAT MUST NOT MOVE, which is why the rule is ANCHORED to the head of the
        # cell. A negation buried in prose and scoped to SOME OTHER WORK is not this row's verdict. The
        # unanchored version of this fix broke the case below, and the selftest is what caught it.
        ("R519's work surfaced it and did not close it; not fixed there. `82da250`.", "cites-a-sha-only"),
        ("Not yet fixed — the remedy is known.",                                "open"),
        # R524's exact shape, and the bucket is `cites-a-sha-only` rather than `open` ON PURPOSE: it
        # cites a SHA (to name the work that did NOT close it) while making no closure claim, so the
        # honest answer is "neither clearly — read it", which is what that bucket means. This expectation
        # was written as `open` first and the selftest caught it. What matters is that it is no longer
        # filed under closed-with-fix, where it was invisible.
        ("surfaced by the R519 work and NOT closed by it. See `82da250`.",      "cites-a-sha-only"),
        ("**CLOSED — candor-ts `82da250`, shipped and verified.**",             "closed-with-fix"),
        ("**REFUTED** — measured, the premise was wrong.",                      "resolved-no-fix"),
        # NEAR-MISSES that must NOT be stripped: domain vocabulary, not a status claim.
        ("**CLOSED — `abc1234`.** The callee is not resolved through the alias.", "closed-with-fix"),
        ("**CLOSED — `abc1234`.** fails-closed on an unresolved import.",        "closed-with-fix"),
        ("the dispatch could not be resolved, so the row stands. `deadbee`",     "cites-a-sha-only"),
        # DECLARED OPEN beats a SHA. R524's real shape: it names the work that did NOT close it.
        ("**OPEN — needs a family-level ruling, not a patch.** See `82da250`.",  "open"),
        # …but only as a DECLARATION at the start of the cell. "open" in ordinary prose must not move a
        # closed row, or the bucket fills with rows that merely discuss open questions.
        ("**CLOSED — `abc1234`.** This left an open question for R99.",          "closed-with-fix"),
        # SOUNDNESS R588 — the other two status heads the register actually uses. R140 heads its cell
        # `**REOPENED 2026-09-10, HALF CLOSED…`, R429 `**REOPENED BY THE PRE-RELEASE REVIEW…`; both were
        # `closed-with-fix` because `_DECLARED_OPEN` only knew the word OPEN.
        ("**REOPENED 2026-09-10.** `aa280d1` unions the arms on the PATH route only.", "open"),
        ("**STILL OPEN: the CHAIN-DRIFT half.** Swept at `1234abc`.",            "open"),
        # …and a lowercase near-miss that must NOT move, for the same reason the rule is case-sensitive.
        ("**CLOSED — `abc1234`.** Reopened briefly, then fixed again.",          "closed-with-fix"),
    ]
    # THE STATUS CELL IS A DIFFERENT CODE PATH and the cases above cannot reach it — `bucket(text, text)`
    # has no columns, so `status` is "". These are whole rows, which is the shape that was mis-bucketed.
    row_cases = [
        ("| R198 rust: a thing | 2026-09-07 | **OPEN — PRE-EXISTING, all arms** |"
         " **CARDINAL SIN** `abc1234` | Not fixed. MATRIX-VERIFIED, closed nothing. |", "open"),
        # R230: status head left stale, outcome cell records the real closure — the outcome wins.
        ("| R230 rust: a thing | 2026-09-06 | **OPEN — mechanism now MEASURED** |"
         " class | **RESOLVED 2026-09-06 by building the shape that decides it.** |",
         "resolved-no-fix"),
        # …and the same shape WITH a fix commit is a closure with a fix, not a decision.
        ("| R231 rust: a thing | 2026-09-06 | **OPEN — mechanism MEASURED** |"
         " class | **RESOLVED — candor-rust `abc1234`, shipped.** |", "closed-with-fix"),
        # A normal closed row must not move: status head says CLOSED, outcome is the filing-time note.
        ("| R88 rust: a thing | 2026-08-30 | **CLOSED — candor-rust `ff6efad`** |"
         " class | Not yet fixed. The fix is to route the bare `let`. |", "closed-with-fix"),
        ("| R190 rust: a thing | 2026-09-05 | **PARTLY CLOSED — candor-rust `93cb988` closes (e)** |"
         " class | Not fixed. The union must be taken wherever. |", "partly-closed"),
        # SOUNDNESS R591 — THE SYMMETRY, both directions. A closure word at the head of the STATUS
        # cell counts even when the OUTCOME cell still opens with its filing-time "Not yet fixed"
        # note, because rows are updated by APPENDING and the outcome head is the oldest text in the
        # row (R126's shape: status `RETRACTED`, outcome `Not yet fixed.`).
        # `resolved-no-fix`, not `closed-with-fix`, and this expectation was written the OTHER way an
        # hour before the rule below existed: RETRACTED means "not a defect", which is a DECISION, and
        # the `abc1234` here is evidence the row cites, not a commit that fixed anything. The selftest
        # caught my own stale expectation, which is the only reason the distinction got made at all.
        ("| R126 swift: a thing | 2026-09-02 | **RETRACTED — NOT A DEFECT. Measured** |"
         " class `abc1234` | Not yet fixed. Fixture at `scratchpad/x`. |", "resolved-no-fix"),
        # …and the same shape WITH the commit beside the closure word is a fix, not a decision.
        ("| R127 swift: a thing | 2026-09-02 | **RESOLVED — candor-swift `abc1234`, shipped** |"
         " class | Not yet fixed. |", "closed-with-fix"),
        # …AND THE FALSE CLOSURE THAT FIX INTRODUCED, which is why this case exists. A cell that says
        # BOTH is not resolved: R162 heads "RESOLVED as a PROCESS GAP ... two real generator bugs
        # found beside it, OPEN" and must STAY on the shipping-defect list.
        ("| R162 rust: a thing | 2026-09-04 | **RESOLVED as a PROCESS GAP, not a live defect; two real"
         " generator bugs found beside it, OPEN** | class `abc1234` | Not fixed. |", "open"),
        # AND THE ESCAPED PIPE: a row whose code sample contains `\|` must not shift the status index.
        ("| R571 rust: `move \\| i: Input \\|` | 2026-09-23 | **OPEN — measured** |"
         " class | Not fixed. |", "open"),
    ]
    bad = 0
    # The ID parse is part of the contract too — see the comment at `rid`. A base row and its lettered
    # sibling are DIFFERENT rows and routinely have different verdicts.
    for line, want_id in (("| R529c rust: a body-local struct's field type…", "R529c"),
                          ("| R529 rust: an implementor written inside a block…", "R529"),
                          ("| ~~R116~~ retracted", "R116")):
        got = re.match(r'^\| ~?~?(R\d+[a-z]?)', line).group(1)
        flag = "ok  " if got == want_id else "FAIL"
        if got != want_id:
            bad += 1
        print(f"  {flag} id={got:7s} want {want_id:7s} {line[:46]!r}")
    for line, want in row_cases:
        _c = re.split(r'(?<!\\)\|', line)
        got = bucket(line, _c[5] if len(_c) > 5 else None)
        flag = "ok  " if got == want else "FAIL"
        if got != want:
            bad += 1
        print(f"  {flag} {got:17s} want {want:17s} {line[:64]!r}")
    for text, want in cases:
        got = bucket(text, text)   # in a real row the outcome IS the last cell
        flag = "ok  " if got == want else "FAIL"
        if got != want:
            bad += 1
        print(f"  {flag} {got:17s} want {want:17s} {text[:64]!r}")
    print("soundness-status selftest: " + ("OK" if not bad else f"FAILED ({bad})"))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    sys.exit(main(sys.argv))
