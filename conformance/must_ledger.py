#!/usr/bin/env python3
"""
EVERY NORMATIVE STATEMENT IN SPEC.md IS CLASSIFIED: EXERCISED BY A NAMED PART, OR UNENFORCED WITH A REASON.

WHY THIS EXISTS — the failure it is built for, stated as it happened
--------------------------------------------------------------------
clause_check.py binds property → clause: a generator must quote the contract it enforces, and the quote
must resolve. Nothing ran in the other direction. A clause could be written, reviewed, echoed in four
engines' comments, and never executed by anything — and two did, measured on the same day (2026-08-12):

  · §3.3.1 (3) named *"the target's own source tree"* FIRST in the list of inputs a sink must never be
    armed over, from the day the clause was written. No engine implemented it; no conformance row asked.
    Reproduced live: candor-ts replaced the operator's SOURCE FILE with the verdict document at EXIT 0,
    reporting success; candor-java destroyed app.jar and then reported "cannot read scan target app.jar" —
    the diagnostic is the engine discovering the file it destroyed. Cost of finding it that way: a day.
  · §2's re-disclosure MUST shipped without pinning its field name, and four engines guessed four ways —
    `judgedNothing` an array in three, a boolean in the fourth (SPEC §2, the measured table).

Both clauses were correct, prominent, and inert. What was missing is not review but a REGISTER: the moment
a normative statement enters the contract, someone must answer "which row exercises this?" — and "none,
because <reason>" must be a recorded answer, not a silence. An unenforced MUST nobody looks at is how
§3.3.1 (3) happened.

WHAT A STATEMENT IS — measured before this gate was built around it
-------------------------------------------------------------------
The register this project keeps (BACKLOG.md, the coverage-gap checker that was deliberately NOT built:
1 true positive, 8 permanent false positives — "an ignored checker is worse than none") demands the
extractor's precision be measured first. Naive designs were measured and REJECTED on SPEC.md as of 0.28:

  · sentence-level "contains MUST": 87% precision on a 15-sentence stratum — but it CANNOT SEE the
    motivating clause. §3.3.1 (3) as first written (c6748f1) contains no MUST token at all: the kernel is
    bold, the doomed input list is a plain sentence. This spec states rules declaratively.
  · sentence-level bold spans: 49% precision on a 41-sentence stratum — half the catch is emphatic
    narration. Rejected for the same reason the coverage-gap checker was.

What shipped is BLOCK granularity: the unit is a paragraph / list item / table row / fence line, extracted
when it carries a normative trigger — the token MUST or REQUIRED, or a **bold span of >= 4 words** (this
document's own convention for a rule kernel). Measured precision, hand-classified:

  · whole document, every-9th-block sample (45 blocks): 38 genuine ≈ 84%.
  · the entire ⟨0.28⟩ rung arc, all 59 added-or-changed blocks: 55 genuine ≈ 93%, ~5 blocks per commit.
    The false positives are measurement/rationale paragraphs; each costs one `unenforced` line, once.

Block granularity is also load-bearing for the motivating clause: an edit ANYWHERE in a normative
paragraph — such as an input list gaining "the target's own source tree" — changes the block's anchor and
forces reclassification, even though the edited sentence itself carries no trigger.

Three structural skips, each an observed convention of SPEC.md: the §8 Changelog (narrates the past by
definition, re-bolded every rung); paragraphs wholly wrapped in single-star *italics* (the house form for
a historical aside — a rule must not live there); a paragraph that is a single bold span ending in ':'
(a lead-in whose content is the following items, which are extracted on their own). Keyword filters
("measured", "found") were tried and REJECTED: by house style a rule paragraph EMBEDS its measurement
(§6.2's zero-rules clause both states the rule and says "measured four-way"), so the filter deletes
genuine rules.

THE LEDGER — must-ledger.json, and the ratchet
----------------------------------------------
SPEC.md stays prose-first: no inline tags. The mapping lives beside this file, one entry per statement,
anchored on sha256 of the whitespace-normalised block text. Each entry is exactly one of:

  {"sha": …, "part": "PART 37 (f)"}       — a conformance part exercises it (the part must resolve in
                                            this directory's files; "PART NN" is tried as a fallback)
  {"sha": …, "unenforced": "<why>"}       — deliberately not exercised, reason recorded; COUNTED and
                                            printed every run, so the pile stays visible
  {"sha": …, "status": "pre-ledger"}      — the baseline freeze: it existed before this gate did. The
                                            same ratchet shape candor-java uses for `deny E Unknown`.
                                            Adding NEW entries as pre-ledger is forbidden and is exactly
                                            what a reviewer of this file's diff is looking for.

A statement in SPEC.md with no entry FAILS the gate (new or reworded — classify it; the diagnostic prints
a paste-ready entry). An entry whose sha no longer matches any statement FAILS the gate (the clause was
edited or removed — an edited MUST is one whose row may no longer match it, so it must be RE-confirmed,
not silently carried).

DELIBERATELY NOT CHECKED: that the named part actually exercises the statement's semantics — no script can
read that. What the gate forces is the moment of classification: a human holding the new clause and the
suite's table of contents at the same time, which is the step §3.3.1 (3) never got. Also invisible: a rule
stated in a plain sentence with no MUST, no REQUIRED and no bold kernel — measured rare (the sampled
misses were all narration, not rules), and the fix if one is found is to bold its kernel, which this
document does anyway.

    python3 must_ledger.py            # gate: exit 1 on any unclassified / orphaned statement
    python3 must_ledger.py --init     # one-time baseline freeze; refuses if the ledger exists
    --spec P / --ledger P             # test-only overrides (used by the falsification transcript)
"""
import hashlib
import json
import os
import re
import sys
from difflib import get_close_matches

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SPEC = os.path.join(HERE, "..", "SPEC.md")
DEFAULT_LEDGER = os.path.join(HERE, "must-ledger.json")

MUST_RE = re.compile(r"\bMUST\b")
REQUIRED_RE = re.compile(r"\bREQUIRED\b")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
MIN_BOLD_WORDS = 4
EXCERPT = 110


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def strip_rung(t):
    """Peel leading ⟨0.NN⟩ rung markers off a block before testing its shape."""
    return re.sub(r"^\s*(?:⟨[0-9.]+⟩\s*)+", "", t.strip())


def italic_aside(text):
    """A block wholly wrapped in single-star italics: the house convention for a
    historical/correction aside. A rule must not live there, so it is not a statement."""
    t = strip_rung(text)
    return t.startswith("*") and not t.startswith("**") and t.endswith("*") and not t.endswith("**")


def bold_leadin(text):
    """A block that is one bold span ending in ':' — a header for the items after it,
    which are extracted on their own."""
    return bool(re.fullmatch(r"\*\*(.+?):\*\*", strip_rung(text), re.S))


def blocks(path):
    """Yield (first_line_no, kind, text): prose paragraphs (blank-line separated; each
    table row and each list item its own unit), individual code-fence lines, headings."""
    lines = open(path).read().split("\n")
    fence = False
    cur, cur_start = [], None

    def flush():
        nonlocal cur, cur_start
        if cur:
            yield cur_start, "prose", " ".join(cur)
        cur, cur_start = [], None

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            yield from flush()
            fence = not fence
            continue
        if fence:
            yield i, "code", line
            continue
        stripped = line.strip()
        if not stripped:
            yield from flush()
            continue
        if stripped.startswith("#"):
            yield from flush()
            yield i, "heading", stripped
            continue
        if stripped.startswith("|") or re.match(r"[-*+] |\d+\. ", stripped):
            yield from flush()
            cur, cur_start = [stripped], i
            continue
        if cur:
            cur.append(stripped)
        else:
            cur, cur_start = [stripped], i
    yield from flush()


def triggers(text, kind):
    t = []
    if MUST_RE.search(text):
        t.append("MUST")
    if REQUIRED_RE.search(text):
        t.append("REQUIRED")
    if kind != "code":  # ** is not markup inside a fence
        for b in BOLD_RE.findall(text):
            if len(b.split()) >= MIN_BOLD_WORDS:
                t.append("BOLD")
                break
    return t


def extract(path):
    """The normative statements of a spec: {sha: (lineno, section, text)}, document order."""
    out = {}
    section = "(preamble)"
    skip_section = False
    for lineno, kind, text in blocks(path):
        if kind == "heading":
            if re.match(r"#{1,4} ", text):
                section = norm(text.lstrip("# "))
                skip_section = bool(re.match(r"##\s+8\.\s+Changelog", text))
            continue
        if skip_section:
            continue
        if kind == "prose" and (italic_aside(text) or bold_leadin(text)):
            continue
        s = norm(text)
        if not triggers(s, kind):
            continue
        sha = hashlib.sha256(s.encode()).hexdigest()[:16]
        out.setdefault(sha, (lineno, section, s))
    return out


def conformance_corpus():
    """Concatenated text a `part` value must resolve in: the suite's own files."""
    names = sorted(os.listdir(HERE))
    parts = []
    for n in names:
        if n.endswith(".py") or n.endswith(".sh") or n == "README.md":
            p = os.path.join(HERE, n)
            if os.path.isfile(p):
                try:
                    parts.append(open(p, errors="replace").read())
                except OSError:
                    pass
    return "\n".join(parts)


def entry_line(sha, section, text, classification='"status": "pre-ledger"'):
    ex = text[:EXCERPT].replace("\\", "\\\\").replace('"', '\\"')
    sec = section[:48].replace("\\", "\\\\").replace('"', '\\"')
    return f'    {{"sha": "{sha}", "at": "{sec}", "excerpt": "{ex}", {classification}}}'


def write_ledger(path, spec_stmts):
    rows = [entry_line(sha, sec, s) for sha, (ln, sec, s) in
            sorted(spec_stmts.items(), key=lambda kv: kv[1][0])]
    head = json.dumps({"_": [
        "MUST LEDGER — every normative statement of SPEC.md, classified. See must_ledger.py's header",
        "for why this exists and what a statement is (block-granularity: MUST/REQUIRED/bold-kernel).",
        "Each entry carries exactly ONE of:",
        "  \"part\": \"PART NN …\"      — the conformance part that exercises it (must resolve in this dir)",
        "  \"unenforced\": \"<why>\"    — deliberately not exercised; the reason is the record",
        "  \"status\": \"pre-ledger\"   — existed before the ledger did (the baseline freeze).",
        "Adding a NEW entry as pre-ledger defeats the gate; a reviewer of this diff should refuse it.",
        "`sha` anchors the whitespace-normalised block text: editing the clause orphans the entry,",
        "which is the point — an edited MUST must be RE-confirmed. `at`/`excerpt` are informative.",
    ]}, indent=2).rstrip("\n}")
    with open(path, "w") as f:
        f.write(head + ',\n  "entries": [\n' + ",\n".join(rows) + "\n  ]\n}\n")


def main(argv):
    spec, ledger, init = DEFAULT_SPEC, DEFAULT_LEDGER, False
    args = argv[1:]
    while args:
        a = args.pop(0)
        if a == "--init":
            init = True
        elif a == "--spec" and args:
            spec = args.pop(0)
        elif a == "--ledger" and args:
            ledger = args.pop(0)
        else:
            print(f"must_ledger.py: unknown argument {a!r} (usage: [--init] [--spec P] [--ledger P])")
            return 2
    if not os.path.exists(spec):
        print(f"FAIL: cannot find SPEC.md at {spec} — this gate would pass over nothing")
        return 2

    stmts = extract(spec)

    if init:
        if os.path.exists(ledger):
            print(f"must_ledger.py --init: {ledger} already exists — the baseline freeze happens once.\n"
                  f"New statements are classified by ADDING entries, not by re-freezing.")
            return 2
        write_ledger(ledger, stmts)
        print(f"must-ledger initialised: {len(stmts)} statement(s) frozen as pre-ledger in {ledger}")
        return 0

    if not os.path.exists(ledger):
        print(f"FAIL: no ledger at {ledger} — run `python3 must_ledger.py --init` once to freeze the baseline")
        return 2
    try:
        entries = json.load(open(ledger)).get("entries", [])
    except Exception as e:
        print(f"FAIL: {ledger} unreadable — {e}")
        return 2

    fails = 0
    print("MUST LEDGER — every normative statement is classified: exercised, unenforced-with-reason, or pre-ledger")

    # ---- entry validation --------------------------------------------------------------
    corpus = None
    by_sha = {}
    n_part = n_unenforced = n_pre = 0
    unenforced_reasons = []
    for e in entries:
        sha = e.get("sha", "")
        keys = [k for k in ("part", "unenforced", "status") if k in e]
        if len(sha) != 16 or len(keys) != 1:
            print(f"  ✘ ledger entry {json.dumps(e)[:100]} — malformed: needs a 16-hex `sha` and exactly one "
                  f"of `part` / `unenforced` / `status: pre-ledger`")
            fails += 1
            continue
        if sha in by_sha:
            print(f"  ✘ ledger entry {sha} — duplicated; one statement, one classification")
            fails += 1
            continue
        by_sha[sha] = e
        k = keys[0]
        if k == "part":
            part = e["part"]
            if not isinstance(part, str) or not part.strip():
                print(f"  ✘ {sha} — `part` is empty; name the part that exercises it")
                fails += 1
                continue
            if corpus is None:
                corpus = conformance_corpus()
            m = re.search(r"PART \d+[a-z]?", part)
            if part not in corpus and not (m and m.group(0) in corpus):
                print(f"  ✘ {sha} — `part` {part!r} resolves nowhere in conformance/ — a row that does not "
                      f"exist enforces nothing; name a real one or reclassify as unenforced")
                fails += 1
                continue
            n_part += 1
        elif k == "unenforced":
            why = e["unenforced"]
            if not isinstance(why, str) or not why.strip():
                print(f"  ✘ {sha} — `unenforced` with NO reason. The reason is the record; an unenforced "
                      f"MUST nobody can re-examine is how §3.3.1 (3) happened. Say why.")
                fails += 1
                continue
            n_unenforced += 1
            unenforced_reasons.append((sha, e.get("excerpt", ""), why))
        else:
            if e["status"] != "pre-ledger":
                print(f"  ✘ {sha} — unknown status {e['status']!r} (only \"pre-ledger\" exists)")
                fails += 1
                continue
            n_pre += 1

    # ---- spec → ledger: every statement classified --------------------------------------
    unclassified = {sha: v for sha, v in stmts.items() if sha not in by_sha}
    orphans = [e for sha, e in by_sha.items() if sha not in stmts]
    stmt_texts = {v[2]: sha for sha, v in stmts.items()}

    for sha, (ln, sec, s) in sorted(unclassified.items(), key=lambda kv: kv[1][0]):
        fails += 1
        print(f"  ✘ SPEC.md:{ln} ({sec}) — NEW OR CHANGED normative statement, unclassified:")
        print(f"        “{s[:EXCERPT]}…”" if len(s) > EXCERPT else f"        “{s}”")
        near = get_close_matches(s[:EXCERPT], [e.get("excerpt", "") for e in orphans], n=1, cutoff=0.6)
        if near:
            print(f"        This resembles orphaned entry “{near[0][:80]}…” — if it is that clause REWORDED,")
            print(f"        the row that exercised the old wording may no longer match this one: re-read the")
            print(f"        clause against its part, then replace the old entry with the line below.")
        print(f"        Classify it — name the part that exercises it, or record why none does:")
        print(entry_line(sha, sec, s, '"part": "PART …"  OR  "unenforced": "<why>"'))

    # ---- ledger → spec: no entry outlives its clause ------------------------------------
    for e in sorted(orphans, key=lambda e: e.get("sha", "")):
        fails += 1
        ex = e.get("excerpt", "")
        print(f"  ✘ ledger entry {e['sha']} — its statement is no longer in SPEC.md:")
        print(f"        was: “{ex}…”")
        trunc = {t[:EXCERPT]: sha for t, sha in stmt_texts.items()}
        near = get_close_matches(ex, list(trunc), n=1, cutoff=0.6)
        if near:
            print(f"        Closest current statement: “{near[0][:80]}…” (sha {trunc[near[0]]})")
            print(f"        If the clause was reworded, RE-CONFIRM the classification against the new text —")
            print(f"        an edited MUST is one whose row may no longer match it — then update the entry.")
        else:
            print(f"        If the clause was removed, remove the entry; if reworded beyond recognition,")
            print(f"        classify the new statement above and delete this one.")

    # ---- the standing disclosure --------------------------------------------------------
    print(f"\n  statements in SPEC.md: {len(stmts)}   classified: {len(stmts) - len(unclassified)} "
          f"(pre-ledger {n_pre}, part-named {n_part}, unenforced {n_unenforced})")
    if unenforced_reasons:
        print(f"  UNENFORCED — {n_unenforced} statement(s) no row exercises, each with its reason on file:")
        for sha, ex, why in unenforced_reasons:
            print(f"    · {sha} “{ex[:60]}…” — {why}")
    print()
    if fails:
        print(f"MUST LEDGER: FAILED — {fails} finding(s). A normative statement was added, changed, or "
              f"removed without its classification moving with it.")
    else:
        print(f"MUST LEDGER: OK — {len(stmts)} statement(s) all classified; {n_unenforced} unenforced, "
              f"each with a reason on file.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
