#!/usr/bin/env python3
"""
check_nested_quotes.py — lint for the nested-single-quote corruption class.

MEASURED BUG (candor-spec, 2026-08-28, PART 80 and PART 83 first drafts, both fixed
same session): bash single quotes have NO escape mechanism — a single-quoted string
ends at the very next literal `'`, full stop. When a `python3 -c '...'` (or any other
inline-interpreter invocation, or a `NAME='...'` variable assignment later fed to one
as `-c "$NAME"`) has its multi-line body written as a plain bash single-quoted string,
any apostrophe genuinely required inside that body (a Python dict-key literal like
`d.get('ok')`, an f-string, etc.) silently truncates the intended script. Bash then
reassembles the remaining text as extra shell words with the quote characters
themselves stripped, so the interpreter receives corrupted-but-often-still-valid code
(`d.get('ok')` arrives as the bare name `d.get(ok)` — a NameError, but only on the
branch that evaluates it). THE DAMAGE IS INVISIBLE ON THE PASSING PATH: a checker's
message-building/failure branch is exactly the code most likely to contain the
apostrophe-bearing string literals, and that branch only runs on a real divergence —
so the corrupted checker prints a clean OK forever and cannot ever report FAIL.

This script does NOT re-derive bash's grammar approximately (see AGENT-CORPUS-BRIEF.md:
"re-deriving ci-watch.sh's logic instead of reading it reintroduced the exact bug its
own comment warns about" — same trap, at the grammar level). It implements bash's
ACTUAL single/double-quote and heredoc rules precisely enough to answer one narrow,
load-bearing question correctly: does an inline-interpreter script argument, or a
variable later used as one, resolve to MORE THAN ONE shell word-segment where at least
one segment is single-quoted? That structural shape is the unique fingerprint of the
bug (bash split what the author intended as one literal blob into several concatenated
pieces) — and it is ALSO, when every non-single-quoted piece is a bare `"$VAR"` /
`"${VAR}"` expansion, the fingerprint of the one LEGITIMATE reason to do this on
purpose: interpolating a shell variable into an otherwise-literal single-quoted
string (`'...'"$VAR"'...'`). Two such deliberate, correct uses already exist in
conformance/run.sh (SPEC-effects-vocabulary check, lines ~4458/4483, splicing $HERE
into a `sys.path.insert` call) — this script tells the two apart instead of flagging
both, because a lint that cries wolf on known-good code trains people to ignore it.

Cross-checked against `shfmt -tojson` (a real, independently-implemented bash parser)
on the full conformance/run.sh at the commit this script was added: shfmt's AST
agrees exactly — 2 multi-segment single-quoted words, both the deliberate $HERE
interpolation, zero of the corruption shape. This script is the pure-stdlib
equivalent kept in the repo (no new dependency) so the check can run everywhere
python3 already runs.

The established safe idiom in this repo, when a script body needs an apostrophe, is a
heredoc (`<<'PY' ... PY`) — heredoc bodies are never subject to shell quote-removal, so
an apostrophe inside one is always literal. This lint does not flag heredocs; it
exists to catch the OTHER form regressing.

Exit code: 0 if clean, 1 if any finding (or if this script's own self-test — see
--selftest — fails, which would mean the lint itself can no longer be trusted; a lint
for "a checker that cannot fail" that cannot itself be shown able to fail is the same
bug one layer up).
"""
import re
import sys

INTERP_NAMES = {"python3", "python", "python2", "node", "nodejs", "perl", "ruby",
                 "php", "tclsh", "osascript"}
VAR_RE = re.compile(r'^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$')


class Word:
    __slots__ = ("segments", "line")

    def __init__(self, line):
        self.segments = []  # list of (kind, text) ; kind in {"lit","sq","dq","ansic","other"}
        self.line = line

    def add(self, kind, text):
        """Append a segment, merging into the previous one when it is the SAME
        kind (e.g. two adjacent unquoted characters). Without this, an unquoted
        run like `AR_STALE=` would be recorded as 9 separate single-character
        'lit' segments instead of one, making is_multi_segment_with_single_quote
        fire on EVERY `NAME='...'` assignment regardless of whether the body
        actually contains a nested quote — a lint that flags its own safe idiom
        (every clean fixture assignment in this file) is worse than no lint: it
        trains people to ignore it. MEASURED while building this check: the
        first version of this method (plain list.append per character) produced
        42 findings on conformance/run.sh where the ground truth (cross-checked
        against `shfmt -tojson`, a real independent bash parser) is 2, both the
        deliberate $HERE-interpolation idiom, zero corruption."""
        if self.segments and self.segments[-1][0] == kind:
            prev_kind, prev_text = self.segments[-1]
            self.segments[-1] = (prev_kind, prev_text + text)
        else:
            self.segments.append((kind, text))

    def text(self):
        return "".join(t for _, t in self.segments)

    @staticmethod
    def _is_multi_segment_with_single_quote(segments):
        if len(segments) <= 1:
            return False
        return any(k == "sq" for k, _ in segments)

    @staticmethod
    def _is_safe_variable_interpolation(segments):
        """True iff every non-single-quoted segment is EITHER a bare $VAR /
        ${VAR} expansion OR an ANSI-C $'...' segment (the two deliberate,
        correct reasons to split a single-quoted script this way) and there
        is at least one 'sq' segment.

        The $'...' carve-out (added 2026-08-29, A4 hardening): '...'$'\\n''...'
        — splicing a literal control character (almost always \\n) between two
        ordinary single-quoted pieces — is the established idiom for building
        multi-line embedded-script text without a literal newline sitting in
        the shell source. Before this carve-out, that idiom was INDISTINGUISHABLE
        from real corruption to this lint (both produce multiple segments with
        an 'sq' among them), so a checker author using it correctly would see a
        FAIL for code that was never at risk — exactly the "lint that cries
        wolf" failure mode this module's own docstring warns trains people to
        ignore it. This carve-out does NOT weaken detection of the real bug
        class: the real bug's extra segment is always a BARE WORD (a Python
        dict-key literal like `zeroMatch` with no `$` prefix at all — see
        scan_nested_quotes.py's own canary fixture), which is 'lit' kind, not
        'ansic' or a $VAR 'dq' — so it still falls through to `return False`
        below untouched. See --selftest's "ansic-splice" and
        "ansic-splice-plus-real-bug" cases for the proof: the splice alone is
        silent, and a genuine corruption in the SAME file is still caught."""
        has_sq = False
        for k, t in segments:
            if k == "sq":
                has_sq = True
                continue
            if k == "ansic":
                continue
            if k == "dq" and VAR_RE.match(t.strip()):
                continue
            return False
        return has_sq


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def scan_double_quoted(text, i, sink):
    """i points just past the opening '\"'. Returns (content, end_idx) where
    end_idx is just past the closing '\"'. Handles backslash escapes of
    \" $ ` \\ , and RECURSES into any nested $(...) via
    skip_command_substitution — both so an apostrophe/quote inside the
    substitution can't be mistaken for closing this double quote, AND so an
    inline-interpreter call inside `"$(python3 -c '...')"` (the exact shape
    of the two deliberate $HERE-interpolation lines in conformance/run.sh,
    e.g. `P23_EXPECT="$(python3 -c '...')"`)  is still discovered and
    checked rather than silently swallowed as opaque text. Words found inside
    the substitution are appended to `sink`, the same list the top-level scan
    returns, so they get the identical safe/unsafe classification a top-level
    invocation would."""
    n = len(text)
    buf = []
    while i < n:
        c = text[i]
        if c == '"':
            return "".join(buf), i + 1
        if c == "\\" and i + 1 < n and text[i + 1] in '"$`\\':
            buf.append(text[i + 1])
            i += 2
            continue
        if text[i:i + 2] == "$(":
            j = skip_command_substitution(text, i, sink)
            buf.append(text[i:j])
            i = j
            continue
        buf.append(c)
        i += 1
    return "".join(buf), n


def scan_ansic_quoted(text, i):
    """text[i:i+2] == "$'" — an ANSI-C-quoted word ($'...'). Returns (content,
    end_idx) where end_idx is just past the closing "'". Bash processes
    backslash escapes (\\n, \\t, \\', \\\\, ...) INSIDE these quotes, so an
    escaped quote \\' does not end the string — skipped here the same way
    scan_double_quoted skips \\" — otherwise a legitimate $'it\\'s'  would be
    misread as ending after `it\\`, splitting the rest into a spurious extra
    segment and producing exactly the false-positive shape this function
    exists to avoid (A4 hardening, 2026-08-29: '...'$'\\n''...' — splicing a
    literal newline between two ordinary single-quoted pieces, the established
    idiom for building multi-line embedded-script text without a literal
    newline in the shell source — was flagged as UNSAFE before this function
    existed, because the lint had no notion of $'...' at all and fell through
    to treating the '$' as a bare literal character and the following '...'
    as an ordinary single-quoted segment)."""
    n = len(text)
    j = i + 2  # past both '$' and the opening "'"
    buf = []
    while j < n:
        c = text[j]
        if c == "\\" and j + 1 < n:
            buf.append(text[j:j + 2])
            j += 2
            continue
        if c == "'":
            return "".join(buf), j + 1
        buf.append(c)
        j += 1
    return "".join(buf), n


def skip_command_substitution(text, i, sink):
    """text[i:i+2] == '$('. Returns index just past the matching ')',
    correctly skipping nested quotes and nested $(...) inside. Also RECURSES:
    the interior of a command substitution is a fresh command context (its
    own words, independent of whatever quoting surrounds the `$(...)` itself),
    so it is scanned with scan_words and any words found are appended to
    `sink` — this is what lets the lint see a `python3 -c '...'` invocation
    written as `VAR="$(python3 -c '...')"` instead of missing it entirely."""
    n = len(text)
    depth = 0
    inner_start = i + 2  # past BOTH '$' and '(' — content starts here
    i += 2
    # MEASURED BUG, caught building this lint: `i += 1` (skipping only the '$')
    # left `i` pointing AT the '(' itself, so the very first loop iteration saw
    # that same opening paren again and counted it as a NESTED one (depth 0->1).
    # Every real, unnested `$(...)` then needed a SECOND, unrelated ')' before
    # anything satisfied `depth == 0`, so the scanner ran past the true close
    # looking for one — usually finding one deep in later code by accident,
    # silently mis-scoping the substitution. Once this function started
    # recursing into scan_words() (to see interpreter calls written as
    # `VAR="$(python3 -c '...')"`), the same off-by-one turned into a hang:
    # each wrongly-oversized "interior" still contained further $(...) calls,
    # each of which repeated the same overshoot, so nearly the whole rest of
    # the file was re-scanned again at every level — a lint that never returns
    # is exactly as untrustworthy as one that returns a false OK.
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
            i += 1
        elif c == ")":
            if depth == 0:
                sink.extend(scan_words(text, inner_start, i, sink=[]))
                return i + 1
            depth -= 1
            i += 1
        elif c == "'":
            j = text.find("'", i + 1)
            i = (j + 1) if j != -1 else n
        elif c == '"':
            _, i = scan_double_quoted(text, i + 1, sink)
        else:
            i += 1
    sink.extend(scan_words(text, inner_start, n, sink=[]))
    return n


HEREDOC_START = re.compile(r"<<-?\s*")
HEREDOC_DELIM = re.compile(r"""(?:'([^']*)'|"([^"]*)"|([A-Za-z_][A-Za-z0-9_]*))""")


def try_skip_heredoc(text, i):
    """If text[i:] begins a heredoc redirect (<< or <<-), return the index
    just past the ENTIRE heredoc body (including its terminator line).
    Otherwise return None. Heredoc bodies are exempt from this lint by
    construction (no shell quote-removal happens inside one)."""
    m = HEREDOC_START.match(text, i)
    if not m:
        return None
    dm = HEREDOC_DELIM.match(text, m.end())
    if not dm:
        return None
    delim = dm.group(1) or dm.group(2) or dm.group(3)
    after_delim = dm.end()
    nl = text.find("\n", after_delim)
    if nl == -1:
        return len(text)
    body_start = nl + 1
    dashed = text[i:i + 3].startswith("<<-")
    pat = re.compile(r"^[ \t]*" if dashed else r"^", re.M)
    term = re.compile((r"^[ \t]*" if dashed else r"^") + re.escape(delim) + r"[ \t]*$", re.M)
    tm = term.search(text, body_start)
    return tm.end() + 1 if tm else len(text)


def scan_words(text, start=0, end=None, sink=None):
    """Walk text[start:end] and return Word objects for every shell word,
    skipping comments and heredoc bodies, and descending into $(...) (via
    skip_command_substitution) so a nested inline-interpreter call is found
    no matter how deep the substitution nesting goes. `sink`, if given, is
    the list nested recursive calls append extra discovered words into; the
    return value is this level's OWN words, in source order, with any
    recursively-discovered words already merged in via `sink`."""
    n = len(text) if end is None else end
    i = start
    words = []
    cur = None
    if sink is None:
        sink = []

    def flush():
        nonlocal cur
        if cur is not None and cur.segments:
            words.append(cur)
        cur = None

    while i < n:
        c = text[i]
        if c in " \t\n":
            flush()
            i += 1
            continue
        if c == "#" and cur is None:
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if text[i:i + 3] == "<<<":
            # here-string operator (`cmd <<<"$var"`) — NOT a heredoc opener. Must be
            # checked BEFORE try_skip_heredoc: consuming the first '<' as a lone
            # operator char (see the ;|&()<> branch below) would leave the remaining
            # "<<" immediately followed by a quoted word (e.g. <<<"$first") looking
            # EXACTLY like a heredoc `<<"$first"` with delimiter "$first" — which then
            # hunts for a terminator line that never exists and swallows the rest of
            # the file as a fake heredoc body. MEASURED: this exact collision silently
            # truncated this lint's own scan of conformance/run.sh at line ~2193
            # (the first `<<<` in the file, in check_agents()'s here-string), before
            # any real finding past that point was ever inspected — a lint whose scan
            # silently stops is the same failure shape this whole task exists to catch.
            flush()
            i += 3
            continue
        hd_end = try_skip_heredoc(text, i)
        if hd_end is not None:
            flush()
            i = hd_end
            continue
        if c in ";|&()<>":
            flush()
            i += 1
            continue
        if c == "'":
            j = text.find("'", i + 1)
            seg = text[i + 1:j] if j != -1 else text[i + 1:]
            if cur is None:
                cur = Word(line_of(text, i))
            cur.add("sq", seg)
            i = (j + 1) if j != -1 else n
            continue
        if c == '"':
            content, j = scan_double_quoted(text, i + 1, sink)
            if cur is None:
                cur = Word(line_of(text, i))
            cur.add("dq", content)
            i = j
            continue
        if text[i:i + 2] == "$(":
            j = skip_command_substitution(text, i, sink)
            if cur is None:
                cur = Word(line_of(text, i))
            cur.add("other", text[i:j])
            i = j
            continue
        if text[i:i + 2] == "$'":
            content, j = scan_ansic_quoted(text, i)
            if cur is None:
                cur = Word(line_of(text, i))
            cur.add("ansic", content)
            i = j
            continue
        if c == "\\":
            if cur is None:
                cur = Word(line_of(text, i))
            if i + 1 < n and text[i + 1] == "\n":
                i += 2  # line continuation: not part of the word text
                continue
            nc = text[i + 1] if i + 1 < n else ""
            cur.add("lit", nc)
            i += 2
            continue
        if cur is None:
            cur = Word(line_of(text, i))
        cur.add("lit", c)
        i += 1
    flush()
    words.extend(sink)
    words.sort(key=lambda w: w.line)
    return words


def analyze(path):
    text = open(path, encoding="utf-8").read()
    words = scan_words(text)
    findings = []
    safe_interpolations = []

    def flag_target(target_word, value_segments=None):
        """value_segments lets a caller exclude a leading unquoted prefix that
        is structurally always present and never itself the risk — e.g. the
        `NAME=` of an assignment word, which fuses with its quoted value into
        ONE bash word by ordinary, correct syntax (segments = [lit, sq] for
        ANY clean `NAME='...'` assignment, buggy or not). Checking the RAW
        word there would flag every single-quoted assignment in the file,
        buggy or not, since 2 segments is simply what correct syntax looks
        like. Checking only the value (segments after the prefix) restores
        the real signal: a clean value is ONE segment; corruption or the safe
        interpolation idiom both produce more than one."""
        segs = target_word.segments if value_segments is None else value_segments
        if not Word._is_multi_segment_with_single_quote(segs):
            return
        if Word._is_safe_variable_interpolation(segs):
            safe_interpolations.append(target_word)
            return
        findings.append(target_word)

    for idx, w in enumerate(words):
        wt = w.text()
        # 1) direct  <interp> -c '...'  /  <interp> -e '...'
        if wt in INTERP_NAMES:
            k = idx + 1
            saw_flag = False
            while k < len(words) and k < idx + 6:
                ft = words[k].text()
                if ft in ("-c", "-e"):
                    saw_flag = True
                    k += 1
                    break
                if ft.startswith("-"):
                    k += 1
                    continue
                break
            if saw_flag and k < len(words):
                flag_target(words[k])
        # 2) NAME='...'  assignment (single fused word: a leading unquoted
        #    segment matching `NAME=` with no space before the quote, e.g. the
        #    *_PY checker-source variables and the JSON/policy fixture
        #    constants throughout this file). Since same-kind segments are
        #    merged (Word.add), the leading run of unquoted characters is
        #    exactly ONE 'lit' segment here, not one per character.
        if w.segments and w.segments[0][0] == "lit" and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=$", w.segments[0][1]):
            flag_target(w, value_segments=w.segments[1:])

    return findings, safe_interpolations, words


def extract_assignment_value(path, name):
    """Return the bash-real VALUE of a top-level `NAME='...'` (or `NAME="..."`)
    assignment in `path`, exactly as bash would deliver it after quote removal
    — or None if no such assignment exists. Used by conformance/mutation-gate.sh
    to pull a checker's CURRENT source (e.g. `RS_PY_FAILCLOSED`) straight out of
    conformance/run.sh rather than keeping a second, hand-copied version that
    could silently drift from the real one. Reuses this module's own
    scan_words() rather than a second hand-rolled parser — the whole point of
    this file is that a hand-rolled bash-quote parser is easy to get wrong
    (three separate bugs were caught building THIS one; see git history), so a
    second one written just for extraction would carry the same risk for no
    reason when this one is already proven against `shfmt -tojson`."""
    text = open(path, encoding="utf-8").read()
    words = scan_words(text)
    prefix = f"{name}="
    for w in words:
        if w.segments and w.segments[0][0] == "lit" and w.segments[0][1] == prefix:
            return "".join(t for _, t in w.segments[1:])
    return None


def extract_heredoc_body(path, delim):
    """Return the FIRST `<<'DELIM' ... DELIM` heredoc body in `path`, verbatim. Used by
    conformance/mutation-gate.sh to pull an embedded run.sh differential's CURRENT source (e.g. the
    PART 46 `python3 - ... <<'PYBL'` script) live, the same "never a frozen copy" discipline
    extract_assignment_value already gives VAR='...' checkers. A heredoc body needs no quote-aware
    parser — unlike a `'...'` argument, a heredoc has no escaping ambiguity: it lexically ends at the
    first line that IS the delimiter, full stop — so a plain anchored regex is the correct tool here,
    not a second use of scan_words()."""
    text = open(path, encoding="utf-8").read()
    # trailing content after the opening quote (` || VAR=1`) is common and not part of the body.
    m = re.search(r"<<'" + re.escape(delim) + r"'[^\n]*\n(.*?)\n" + re.escape(delim) + r"\n",
                  text, re.S)
    return m.group(1) if m else None


def extract_oneline_pyc_func(path, name):
    """Return the python body of a bash function shaped `name() { python3 -c '<PY>' ARGS; }`, where
    the closing `'` and the function's closing `}` share ONE line — e.g. PART 72's `eq72`/`ck72`/
    `mut72` in conformance/run.sh. This is a DIFFERENT shape from mutation-gate.sh's own `extract_func`
    (used for ck83_defect/ck83_control), which assumes the closing `}` sits alone at column 0; that
    assumption is false here; a same-line close is uncounted by it (it would run to the file's next
    column-0 `}`, likely swallowing unrelated code), so this is a dedicated extractor, not a reuse."""
    text = open(path, encoding="utf-8").read()
    m = re.search(r"(?m)^" + re.escape(name) + r"\(\) \{ python3 -c '\n(.*?)\n'", text, re.S)
    return m.group(1) if m else None


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--extract-var" in argv:
        i = argv.index("--extract-var")
        try:
            name, path = argv[i + 1], argv[i + 2]
        except IndexError:
            print("usage: check_nested_quotes.py --extract-var NAME file.sh", file=sys.stderr)
            return 2
        value = extract_assignment_value(path, name)
        if value is None:
            print(f"check_nested_quotes: no top-level assignment `{name}=` found in {path}",
                  file=sys.stderr)
            return 1
        sys.stdout.write(value)
        return 0
    if "--extract-heredoc" in argv:
        i = argv.index("--extract-heredoc")
        try:
            delim, path = argv[i + 1], argv[i + 2]
        except IndexError:
            print("usage: check_nested_quotes.py --extract-heredoc DELIM file.sh", file=sys.stderr)
            return 2
        value = extract_heredoc_body(path, delim)
        if value is None:
            print(f"check_nested_quotes: no <<'{delim}' heredoc found in {path}", file=sys.stderr)
            return 1
        sys.stdout.write(value)
        return 0
    if "--extract-oneline-func" in argv:
        i = argv.index("--extract-oneline-func")
        try:
            name, path = argv[i + 1], argv[i + 2]
        except IndexError:
            print("usage: check_nested_quotes.py --extract-oneline-func NAME file.sh", file=sys.stderr)
            return 2
        value = extract_oneline_pyc_func(path, name)
        if value is None:
            print(f"check_nested_quotes: no `{name}() {{ python3 -c '...'` found in {path}",
                  file=sys.stderr)
            return 1
        sys.stdout.write(value)
        return 0
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print("usage: check_nested_quotes.py <file.sh> [file.sh ...]", file=sys.stderr)
        return 2
    total = 0
    for path in paths:
        findings, safe, _ = analyze(path)
        print(f"=== {path} ===")
        print(f"  {len(safe)} safe single-quote/variable-interpolation word(s) "
              f"(e.g. '...'\"$VAR\"'...') — not flagged")
        for w in safe:
            print(f"    line {w.line}: OK (interpolation) — {w.text()[:90]!r}")
        print(f"  {len(findings)} UNSAFE nested-single-quote finding(s)")
        for w in findings:
            print(f"    line {w.line}: FAIL — body splits into {len(w.segments)} segments; "
                  f"bash silently reassembles this, stripping quote characters")
            print(f"      as-intended-looking text : {w.text()[:160]!r}")
        total += len(findings)
    if total:
        print(f"\ncheck_nested_quotes: {total} unsafe nested-single-quote invocation(s) found — "
              f"convert to a heredoc (<<'PY' ... PY), the established safe idiom in this repo.")
        return 1
    print("\ncheck_nested_quotes: OK — no nested-single-quote corruption found")
    return 0


def selftest():
    """Prove the lint can fail: run it against a synthetic buggy snippet and a
    synthetic clean snippet, in memory, and require the right verdict from each."""
    import tempfile, os
    buggy = """
f() {
  python3 -c '
import json, sys
s = json.load(open(sys.argv[1]))
v = s.get('ok')
print(v)
' "$1"
}
"""
    clean = """
f() {
  python3 -c '
import json, sys
s = json.load(open(sys.argv[1]))
v = s.get("ok")
print(v)
' "$1"
}
"""
    interp = """
g() {
  H="$1"
  python3 -c 'import sys; sys.path.insert(0, "'"$H"'/../reference"); print("ok")'
}
"""
    clean_assign = """
FOO_PY='import json,sys
d=json.load(open(sys.argv[1]))
sys.exit(0 if d.get("ok") is True else 1)'
check() { python3 -c "$FOO_PY" "$1"; }
"""
    # Regression fixture for the real HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")"
    # && pwd)" shape (conformance/run.sh line 2) and the real PART 23 shape
    # (P23_EXPECT="$(python3 -c '...')", run.sh ~4458): a command substitution
    # nested inside a double-quoted assignment, itself containing a further
    # nested double-quoted $(...). Building this lint's own $(...) recursion
    # (needed so an inline-interpreter call written this way isn't invisible
    # to the scan) had an off-by-one in the paren-depth counter that made this
    # EXACT shape hang the lint outright rather than misreport — the worse
    # failure mode, since a hang is at least loud, but only after wasting
    # whoever ran it. This case is a fast, standing regression guard for it.
    nested_cmdsub = """
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
buggy_nested() {
  H="$1"
  P23_EXPECT="$(python3 -c 'import sys; sys.path.insert(0, "'"$H"'/x"); print(2**len(m.E))' 2>/dev/null)"
}
echo "reached the end without hanging"
"""
    buggy_assign = """
FOO_PY='import json,sys
d=json.load(open(sys.argv[1]))
sys.exit(0 if d.get('ok') is True else 1)'
check() { python3 -c "$FOO_PY" "$1"; }
"""
    # A4 hardening (2026-08-29): the ANSI-C $'\\n' splice — '...'$'\\n''...' —
    # is the established idiom for embedding a literal newline between two
    # ordinary single-quoted script pieces without a literal newline sitting
    # in the shell source. Before scan_ansic_quoted()/_is_safe_variable_interpolation's
    # "ansic" carve-out, this produced the SAME multi-segment-with-single-quote
    # shape as real corruption and was flagged UNSAFE — a lint crying wolf on
    # correct code, which this module's own docstring says trains people to
    # ignore it. This fixture must come back CLEAN.
    ansic_splice = """
h() {
  python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
print("line one")'$'\\n''print("line two")
sys.exit(0)
' "$1"
}
"""
    # The other half of the A4 control: the $'\\n' splice must stop being
    # flagged WITHOUT blinding the lint to a real corruption sitting in the
    # very same file. `bad()` here carries the classic unescaped-apostrophe
    # bug (s.get('ok') nested in the outer '...') right alongside the clean
    # splice in `h()` — the splice must stay silent AND `bad()` must still be
    # caught, or the fix has merely traded a false positive for a false
    # negative instead of actually distinguishing the two shapes.
    ansic_splice_plus_bug = """
h() {
  python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
print("line one")'$'\\n''print("line two")
sys.exit(0)
' "$1"
}
bad() {
  python3 -c '
import json, sys
s = json.load(open(sys.argv[1]))
v = s.get('ok')
print(v)
' "$1"
}
"""
    import signal

    class Hung(Exception):
        pass

    def alarm_handler(signum, frame):
        raise Hung()

    ok = True
    for label, src, want_findings, want_safe in (
        ("buggy", buggy, 1, 0),
        ("clean", clean, 0, 0),
        ("interpolation", interp, 0, 1),
        ("clean-assignment", clean_assign, 0, 0),
        ("nested-cmdsub-no-hang", nested_cmdsub, 0, 1),
        ("buggy-assignment", buggy_assign, 1, 0),
        ("ansic-splice", ansic_splice, 0, 1),
        ("ansic-splice-plus-real-bug", ansic_splice_plus_bug, 1, 1),
    ):
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
            f.write(src)
            path = f.name
        try:
            # A 5-second budget on a <20-line fixture: any hang (e.g. the
            # $(...) depth-tracking off-by-one this suite once had) fails
            # LOUDLY here instead of leaving whoever runs the lint staring at
            # a stuck terminal wondering if it's still working.
            old_handler = signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(5)
            try:
                findings, safe, _ = analyze(path)
                got_f, got_s = len(findings), len(safe)
                status = "OK" if (got_f == want_findings and got_s == want_safe) else "FAIL"
            except Hung:
                got_f = got_s = None
                status = "FAIL (HUNG past 5s budget)"
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            if status != "OK":
                ok = False
            print(f"[selftest:{label}] want findings={want_findings} safe={want_safe}, "
                  f"got findings={got_f} safe={got_s} -> {status}")
        finally:
            os.unlink(path)
    if ok:
        print("selftest: OK — the lint is proven able to both fire on the real bug shape "
              "and stay silent on clean/deliberate code")
        return 0
    print("selftest: FAIL — the lint's own self-test did not get the expected verdicts; "
          "do not trust its output until this is fixed")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
