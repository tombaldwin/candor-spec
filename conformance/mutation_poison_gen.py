#!/usr/bin/env python3
"""
mutation_poison_gen.py — CLASSIFY a checker's own comparisons, MECHANICALLY emit the matching
near-miss poison family, and prove the checker rejects every one of them (and still accepts a
genuinely valid document).

WHY THIS EXISTS, in one sentence (see mutation-gate.sh's header and BACKLOG.md "THE BIGGEST
STRUCTURAL FINDING" for the full history): every near-miss fixture in this suite so far — eleven
bypasses (A1-A5, S1-S6) in mutation-gate.sh, thirteen more in a survey of standalone
`conformance/*.py` checkers — was found by a HUMAN re-deriving the same four comparison shapes
(identity degraded to truthiness, exact equality degraded to membership/subset, a dropped
`isinstance` guard, absent-key blindness) one adversarial round at a time, and every round left the
next-shaped gap standing. A generative alternative — walk the checker's OWN source, classify each
comparison, mechanically emit the canonical near-miss for its shape — was named as owed once a
fourth round found the same class on a new surface (mutation-gate.sh's own header set that
threshold). This is that generator.

WHAT IT DOES NOT DO. It does not invent a "valid" document from nothing — knowing what a real
engine report looks like is domain knowledge no source-reader can derive, so a genuinely-valid
baseline document, per checker (and per argv "mode" where a checker has several), is supplied by a
human once, in mutation_poison_configs.py. Given that baseline, EVERY POISON is derived
mechanically: the generator reads the checker's actual comparisons via `ast`, resolves each one to
a concrete field of the baseline document it reads, and emits the near-miss family
(truthy-not-True, falsy-but-present, genuinely-absent-key, wrong-type, superset, subset,
substring) by perturbing ONLY that field, holding everything else at the baseline's passing value —
the same per-condition-isolation discipline BACKLOG's "B1" lesson forced into every hand-authored
fixture in mutation-gate.sh.

WHAT IT REFUSES TO DO SILENTLY. A comparison the classifier cannot resolve to a concrete document
field is exactly the class of thing this whole exercise exists to stop hiding — see
AGENT-CORPUS-BRIEF.md rule 9 ("an audit's boundary must not be drawn around its own trigger") and
`[[candor-denylist-over-allowlist]]`. Every such comparison is printed as UNRESOLVED, with its file,
line and source text, and counts toward a nonzero exit — never dropped, never merged into a
generic "N comparisons found" count that a reader cannot audit.

TWO CHECKER SHAPES, reached by two extraction paths — the thing the existing hand-built gate could
not do for the second one (BACKLOG.md: "13 of 13 external conformance checkers could not fail"):
  - EMBEDDED: a bash variable holding inline Python (`VD_PY='...'`), or a bash function wrapping a
    `python3 -c '...'` body (`ck83_defect`) — both pulled live out of conformance/run.sh via the
    SAME independently-validated extractor conformance/scripts/check_nested_quotes.py already uses
    for extraction (`--extract-var`), or a small same-convention brace-matcher for the bashfunc
    case. Never a frozen copy.
  - STANDALONE: a `conformance/*.py` file invoked by path — read directly, so an edit to it is
    picked up on the very next run with no copy to go stale.
Both are reduced to a flat Python AST and classified by the identical engine; the CLI driving them
differs only in how the resulting source text is obtained and how the process is invoked.

FAIL-CLOSED: any exception raised by this module's own machinery (extraction, AST parse, JSON
encoding, subprocess) is a HARD FAILURE of the whole run, not a skipped checker and not a PASS —
see main()'s top-level try/except. A generator that quietly swallows its own errors and reports
partial success would be exactly the bug this project keeps finding one layer down from the last
fix.

USAGE
    python3 mutation_poison_gen.py                    # run every checker registered in configs
    python3 mutation_poison_gen.py --only NAME[,NAME]  # run a subset
    python3 mutation_poison_gen.py --retro             # run the retro-test (see retro_test.py)
    python3 mutation_poison_gen.py --list-findings NAME  # print classified comparisons, no run
"""
import argparse
import ast
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_SH = os.path.join(HERE, "run.sh")
NESTED_QUOTES_PY = os.path.join(HERE, "..", "scripts", "check_nested_quotes.py")

MISSING = object()   # sentinel: "this key must be entirely absent from the document"


class ExtractionError(Exception):
    """Extraction failed. Callers must treat this as a HARD stop (see mutation-gate.sh's own
    require_extracted: an extraction failure recorded as an ordinary BROKEN row is indistinguishable
    from the thing under test actually failing — A3 hardening, 2026-08-29)."""


class GeneratorError(Exception):
    """This tool's own machinery broke. Fail closed — never a silent pass."""


# ════════════════════════════════════════════════════════════════════════════════════════════════
# EXTRACTION — pull the checker's CURRENT source out of wherever it actually lives.
# ════════════════════════════════════════════════════════════════════════════════════════════════

def extract_pyvar(name, run_sh=RUN_SH):
    """A bash variable holding inline Python (VD_PY, RS_PY_FAILCLOSED, CHAN_PY, ZR_PY_*, ...),
    pulled out via the SAME parser mutation-gate.sh already trusts for this (cross-checked against
    `shfmt -tojson` — see that script's own docstring), never a hand-copied duplicate."""
    r = subprocess.run([sys.executable, NESTED_QUOTES_PY, "--extract-var", name, run_sh],
                        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout:
        raise ExtractionError(f"--extract-var {name} {run_sh}: rc={r.returncode} stderr={r.stderr.strip()!r}")
    return r.stdout


def extract_bashfunc_pyc(funcname, run_sh=RUN_SH):
    """A bash function shaped like ck83_defect/ck83_control: `funcname() {\\n  python3 -c '\\n<PY>\\n' ...`.
    Finds the function by the same `^name() {` convention mutation-gate.sh's extract_func uses, then
    slices out the single-quoted Python body between `python3 -c '` and the next line-leading `'`."""
    if not os.path.exists(run_sh):
        raise ExtractionError(f"no such file: {run_sh}")
    text = open(run_sh).read()
    m = re.search(r'(?m)^' + re.escape(funcname) + r'\(\)\s*\{', text)
    if not m:
        raise ExtractionError(f"no bash function `{funcname}() {{` found in {run_sh}")
    tail = text[m.end():]
    end_m = re.search(r'(?m)^\}', tail)
    if not end_m:
        raise ExtractionError(f"no closing `}}` (at column 0) found for function `{funcname}`")
    body = tail[:end_m.start()]
    pyc = re.search(r"python3 -c '\n(.*?)\n'", body, re.S)
    if not pyc:
        raise ExtractionError(f"no `python3 -c '...'` body found inside `{funcname}()`")
    return pyc.group(1)


def read_extfile(path):
    if not os.path.exists(path):
        raise ExtractionError(f"no such file: {path}")
    return open(path).read()


# ════════════════════════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION — walk the AST, find every comparison of the four families, resolve each to a
# concrete (slot, key-path) address in a JSON document wherever the source itself makes that
# derivable.
# ════════════════════════════════════════════════════════════════════════════════════════════════

SHAPE_IS_BOOL = "is_bool"          # `x is True` / `is not True` / `is False` / `is not False`
SHAPE_EQ_BOOL = "eq_bool"          # `x == True/False` / `!=` — same family, `==` spelling
SHAPE_EQ_LITERAL = "eq_literal"    # `x == "str"` / `x == 0` / `!=` — non-bool literal
SHAPE_LIST_SET_EQ = "list_set_eq"  # `x == [...]`, `sorted(a)==sorted(b)`, `set(a)==set(b)`
SHAPE_ISINSTANCE = "isinstance"    # `isinstance(x, T)` used as a guard
SHAPE_PRESENCE = "presence"        # `"key" in d` / `"key" not in d` with NO further value read

FAMILY_NAMES = {
    "truthy_not_true": "truthy-but-not-the-literal-True",
    "falsy_not_false": "falsy-but-not-the-literal-False",
    "absent": "the key genuinely absent",
    "wrong_type": "present, truthy, but the WRONG TYPE",
    "superset": "the correct collection PLUS one extra element",
    "subset": "a strict SUBSET of the correct collection",
    "substring": "a value that CONTAINS the wanted string but is not equal to it",
    "wrong_value": "present, correct type, a plainly wrong value",
}


@dataclass
class KeyPath:
    """Where a resolved comparison operand lives inside a JSON document.
    slot: an opaque id for WHICH document (e.g. "argv1", "argv2", "stdin") — cross-checked against
          the CheckerConfig's declared slots.
    steps: a list of ("key", name) or ("select", listkey, matchsrc, matchfn, matchval) — the latter
          for "the entry of list field `listkey` whose derived key equals `matchval`", where
          `matchfn` is COMPILED FROM THE CHECKER'S OWN comprehension filter (see resolve_call), not
          reinvented, so the leaf-matching convention ("match on the trailing segment of a
          `::`/`.`-qualified name") is derived, not hard-coded.
    """
    slot: str
    steps: list = field(default_factory=list)

    def describe(self):
        parts = [self.slot]
        for st in self.steps:
            if st[0] == "key":
                parts.append(f".{st[1]}")
            else:
                parts.append(f"[{st[1]} where {st[2]}=={st[4]!r}]")
        return "".join(parts)


@dataclass
class Finding:
    lineno: int
    shape: str
    negated: bool               # True for `is not` / `!=` / `not isinstance` / `not in`
    literal: Any                # the constant compared against (bool/str/int/list/set), or a type name for isinstance
    path: Optional[KeyPath]
    mode: Optional[str]         # the `want=="MODE"` guard this comparison lives under, if any
    snippet: str
    unresolved_reason: Optional[str] = None
    exact_reject_code: Optional[int] = None   # if the enclosing statement is `sys.exit(N)`, capture N


def _lit(node):
    """A plain literal value, or NOT_A_LITERAL if the node isn't one."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        vals = [_lit(e) for e in node.elts]
        if any(v is _NOT_LITERAL for v in vals):
            return _NOT_LITERAL
        return list(vals) if isinstance(node, (ast.List, ast.Tuple)) else set(vals)
    return _NOT_LITERAL


_NOT_LITERAL = object()


def _snippet(node):
    try:
        return ast.unparse(node)
    except Exception:
        return "<unparseable>"


def _subscript_const(node):
    """The constant key/index of an ast.Subscript, across the 3.8 ast.Index wrapper and the 3.9+
    direct-expression form (ast.Index still parses under 3.9 for back-compat but is never PRODUCED
    by ast.parse there, so both branches are checked rather than assumed)."""
    sl = node.slice
    if hasattr(ast, "Index") and isinstance(sl, ast.Index):
        sl = sl.value
    v = _lit(sl)
    return v if v is not _NOT_LITERAL else None


def _enclosing_exit_code(node, parents):
    """Walk UP the parents chain from `node` to find the nearest `if <cond-containing node>: sys.exit(N)`
    with a literal N and no other statements in that branch's body besides the exit (a single-purpose
    guard) — the shape ZR_PY_NO_OK/CHAN_PY use throughout. Returns None if the guard isn't this simple;
    a None here just means "assert reject via any nonzero exit + no traceback" (weaker, stated as
    such) rather than a hard failure."""
    for anc in reversed(parents):
        if isinstance(anc, ast.If):
            for stmt in anc.body:
                if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                        and _snippet(stmt.value).startswith("sys.exit(")):
                    pass
                if isinstance(stmt, (ast.Expr,)):
                    continue
            for stmt in anc.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    call = stmt.value
                    if _snippet(call.func) == "sys.exit" and len(call.args) == 1:
                        v = _lit(call.args[0])
                        if isinstance(v, int):
                            return v
    return None


class Classifier:
    """One classifier instance per checker source. Call .run() to get (findings, module_helpers)."""

    def __init__(self, source, filename="<checker>"):
        self.source = source
        self.filename = filename
        try:
            self.tree = ast.parse(source, filename=filename)
        except SyntaxError as e:
            raise GeneratorError(f"{filename}: could not parse as Python: {e}")
        self.helpers = {n.name: n for n in ast.walk(self.tree) if isinstance(n, ast.FunctionDef)}
        self.findings = []

    # ---- entry body: `def main():`/`def main(argv):` body if present, else module level ----------
    def entry_body(self):
        for n in self.tree.body:
            if isinstance(n, ast.FunctionDef) and n.name == "main":
                return n.body
        return self.tree.body

    def run(self):
        scope = {"assigns": {}, "argv_index": {}, "doc_slot": {}}
        self._walk_stmts(self.entry_body(), scope, mode=None, parents=[])
        return self.findings

    # ---- statement walk, threading a mutable local-binding scope + active `want==` mode ----------
    def _walk_stmts(self, stmts, scope, mode, parents):
        for stmt in stmts:
            self._walk_stmt(stmt, scope, mode, parents)

    def _walk_stmt(self, stmt, scope, mode, parents):
        parents = parents + [stmt]
        # ---- a NESTED helper `def` (ck83_defect's `load`, fs_position_check.py's `unit`/`paths`/
        # `inc`) is never scanned top-down for its OWN classifiable comparisons: its parameter names
        # are meaningless against the ENCLOSING scope (a bare `leaf`/`f`/`p` there is not a document
        # reference the outer scope can resolve), so a generic walk only ever produces a SPURIOUS
        # unresolved duplicate of a comparison _resolve_call's ACCESSOR/SELECTOR machinery already
        # interprets correctly on demand, at the actual call site, with the real argument bound.
        # Reproduced live: fs_position_check.py's `unit()` selector condition was correctly consumed
        # by every one of L86/90/96/104/110's findings AND separately reported as UNRESOLVED by this
        # same top-down sweep, from the identical source line, before this guard was added.
        if isinstance(stmt, ast.FunctionDef):
            return
        # ---- bindings: NAME = <expr>, and simple tuple unpacks -------------------------------
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            tgt = stmt.targets[0]
            if isinstance(tgt, ast.Name):
                scope["assigns"][tgt.id] = stmt.value
                self._maybe_bind_argv(tgt.id, stmt.value, scope)
                self._maybe_bind_doc(tgt.id, stmt.value, scope)
            elif isinstance(tgt, ast.Tuple) and isinstance(stmt.value, ast.Tuple) \
                    and len(tgt.elts) == len(stmt.value.elts):
                for te, ve in zip(tgt.elts, stmt.value.elts):
                    if isinstance(te, ast.Name):
                        scope["assigns"][te.id] = ve
                        self._maybe_bind_argv(te.id, ve, scope)
        if isinstance(stmt, ast.With):
            # `with open(path) as f: NAME = json.load(f)` — bind `f` to `open(path)` exactly like a
            # plain assignment would, so `_maybe_bind_doc`'s resolution of `json.load(f)` inside the
            # body can trace `f` back to the argv slot `path` came from (incomplete_check.py's exact
            # shape: `with open(dep_path) as f: dep = json.load(f)`).
            for item in stmt.items:
                if isinstance(item.optional_vars, ast.Name):
                    scope["assigns"][item.optional_vars.id] = item.context_expr

        # ---- `if want == "MODE"` / `if want.startswith("MODE:")` / `if want=="MODE" and <check>:`
        # pushes a mode context for everything gated by it — INCLUDING the rest of a compound `and`
        # test, which is how VD_PY actually writes every one of its nine rows (`if want=="ok0" and
        # d.get("ok") is not False: bad.append(...)` — a single flat `if`, not a nested one). The
        # guard conjunct itself (`want=="ok0"`) is excluded from classification via `skip` — it tests
        # an argv literal, not a document field, and is not itself poisonable.
        if isinstance(stmt, ast.If):
            new_mode, guard_node = self._mode_of_test(stmt.test, scope)
            skip = parents_skip = {id(guard_node)} if guard_node is not None else set()
            self._scan_expr(stmt.test, scope, new_mode or mode, parents, skip=skip)
            self._walk_stmts(stmt.body, dict_copy(scope), new_mode or mode, parents)
            self._walk_stmts(stmt.orelse, dict_copy(scope), mode, parents)
            return
        if isinstance(stmt, (ast.For, ast.While)):
            self._walk_stmts(getattr(stmt, "body", []), scope, mode, parents)
            self._walk_stmts(getattr(stmt, "orelse", []), scope, mode, parents)
            return
        if isinstance(stmt, ast.Try):
            self._walk_stmts(stmt.body, scope, mode, parents)
            for h in stmt.handlers:
                self._walk_stmts(h.body, scope, mode, parents)
            self._walk_stmts(stmt.orelse, scope, mode, parents)
            self._walk_stmts(stmt.finalbody, scope, mode, parents)
            return
        if isinstance(stmt, ast.With):
            self._walk_stmts(stmt.body, scope, mode, parents)
            return

        # ---- everything else: scan every expression this statement contains --------------------
        self._scan_expr(stmt, scope, mode, parents, skip=set(), top_is_stmt=True)

    def _scan_expr(self, node, scope, mode, parents, skip=None, top_is_stmt=False):
        if skip is None:
            skip = set()
        else:
            skip = set(skip)   # never mutate a caller's set/frozenset in place
        for sub in ast.walk(node):
            if top_is_stmt and sub is node:
                continue
            if id(sub) in skip:
                continue
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in ("any", "all") \
                    and len(sub.args) == 1 and isinstance(sub.args[0], ast.GeneratorExp):
                if self._classify_any_all(sub, scope, mode, parents, skip):
                    continue  # handled as its own finding; do not ALSO classify the inner Compare generically
            if isinstance(sub, ast.Compare):
                self._classify_compare(sub, scope, mode, parents)
            elif isinstance(sub, ast.Call) and _snippet(sub.func) == "isinstance":
                self._classify_isinstance(sub, scope, mode, parents)

    def _classify_any_all(self, call, scope, mode, parents, skip):
        """`any(X.<chain> == LIT for X in ITER)` / `all(...)` — an EXISTENTIAL equality over a list
        field (VD_PY's `v005` row: `any(v.get("rule")=="AS-EFF-005" for v in d.get("violations",[]))`).
        This is the SAME exact-equality-vs-substring/membership shape as a plain `==`, one level
        inside a comprehension; degrading it to `in`/`.startswith()` is the historical S6 bypass.
        Resolved as a `select` KeyPath: the entry of ITER whose <chain> equals LIT, then the leaf key
        <chain> reads off that entry. Returns True if handled (caller must not ALSO generically walk
        into the inner Compare, which would report it as an unresolved bare comparison)."""
        gen = call.args[0]
        if len(gen.generators) != 1 or not isinstance(gen.elt, ast.Compare) or len(gen.elt.ops) != 1:
            return False
        g = gen.generators[0]
        if not isinstance(g.target, ast.Name) or g.ifs:
            return False
        loopvar = g.target.id
        cmp = gen.elt
        if not isinstance(cmp.ops[0], (ast.Eq, ast.NotEq)):
            return False
        left, right = cmp.left, cmp.comparators[0]
        if _mentions(left, loopvar) and not _mentions(right, loopvar):
            chain, lit = left, _lit(right)
        elif _mentions(right, loopvar) and not _mentions(left, loopvar):
            chain, lit = right, _lit(left)
        else:
            return False
        if lit is _NOT_LITERAL:
            return False
        base, listkey = self._peel_one_key(g.iter, scope, 0) or (None, None)
        if base is None or listkey is None:
            return False
        matchfn = _compile_unary_lambda(loopvar, chain)
        if matchfn is None:
            return False
        select_step = ("select", listkey, _snippet(chain), matchfn, lit)
        # the leaf field the near-miss must mutate is whatever `chain` itself reads off the loop var
        leaf_base, leaf_key = self._peel_one_key(chain, {"assigns": {}, "argv_index": {}, "doc_slot": {loopvar: "__v__"}}, 0)
        if leaf_base is None or leaf_key is None or leaf_base.slot != "__v__":
            return False
        path = KeyPath(base.slot, base.steps + [select_step, ("key", leaf_key)])
        self.findings.append(Finding(cmp.lineno, SHAPE_EQ_LITERAL, isinstance(cmp.ops[0], ast.NotEq),
                                      lit, path, mode, _snippet(call)))
        skip.add(id(cmp))
        return True

    def _mode_of_test(self, test, scope):
        """Returns (mode_or_None, guard_node_or_None) — guard_node is the SPECIFIC comparison/call
        that names the mode, so callers can exclude just that node (never the whole test) from
        classification: VD_PY writes `if want=="ok0" and <real check>:` as ONE flat `if`, so the
        real check lives in the SAME test as the guard, not in a nested `if`."""
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And) and test.values:
            m, g = self._mode_of_test(test.values[0], scope)
            if m is not None:
                return m, g
        # `want == "X"` — a single mode literal
        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
            lit = _lit(test.comparators[0])
            if isinstance(lit, str) and isinstance(test.left, ast.Name):
                return lit, test
        # `want.startswith("X:")`
        if isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute) \
                and test.func.attr == "startswith" and test.args:
            lit = _lit(test.args[0])
            if isinstance(lit, str):
                return lit.rstrip(":"), test
        return None, None

    # ---- binding helpers -----------------------------------------------------------------------
    def _maybe_bind_argv(self, name, expr, scope):
        """NAME = sys.argv[N] (optionally .strip()'d) -> argv_index[NAME] = N."""
        e = expr
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr == "strip":
            e = e.func.value
        if isinstance(e, ast.Subscript) and _snippet(e.value) == "sys.argv":
            idx = _subscript_const(e)
            if isinstance(idx, int):
                scope["argv_index"][name] = idx

    def _maybe_bind_doc(self, name, expr, scope):
        """NAME = json.load(open(PATH)) / json.loads(f.read()) / json.loads(sys.stdin...read()) -> a
        root doc, OR NAME = <local wrapper>(PATH) where the wrapper's own body is exactly one of
        those shapes (ck83_defect's `load(p)`, wrapping `json.load(open(p))` in a try/except so a
        bad fixture path fails loudly rather than with a raw traceback) — traced ONE level through a
        same-module helper, never assumed, so a wrapper with any OTHER shape is correctly left
        unresolved rather than guessed at."""
        e = expr
        if isinstance(e, ast.Call) and _snippet(e.func) in ("json.load", "json.loads") and e.args:
            slot = self._slot_of_stream_expr(e.args[0], scope)
            if slot:
                scope["doc_slot"][name] = slot
            return
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id in self.helpers and e.args:
            fn = self.helpers[e.func.id]
            if len(fn.args.args) == 1 and self._is_doc_loader_helper(fn, fn.args.args[0].arg):
                slot = self._slot_of_stream_expr(e.args[0], scope)
                if slot:
                    scope["doc_slot"][name] = slot

    @staticmethod
    def _is_doc_loader_helper(fn, param):
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Call) \
                    and _snippet(node.value.func) in ("json.load", "json.loads") and node.value.args:
                arg = node.value.args[0]
                if isinstance(arg, ast.Call) and _snippet(arg.func) == "open" and arg.args \
                        and isinstance(arg.args[0], ast.Name) and arg.args[0].id == param:
                    return True
                if isinstance(arg, ast.Name) and arg.id == param:
                    return True
        return False

    def _slot_of_stream_expr(self, expr, scope, depth=0):
        """Resolve `expr` (a document/bytes source: `sys.argv[N]`, `open(sys.argv[N])`,
        `open(sys.argv[N]).read()`, `sys.stdin.buffer.read()`, or a local alias of any of those) to
        an opaque slot id: "argvN", "stdin", or None if it traces to something this tool cannot
        parameterise (e.g. a hard-coded path like SPEC.md — reported upstream as unresolved, never
        guessed)."""
        if depth > 6:
            return None
        if "sys.stdin" in _snippet(expr):
            return "stdin"
        node = expr
        while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            node = node.func.value   # peel .read() / .buffer.read() / .strip() chains
        if isinstance(node, ast.Call) and _snippet(node.func) == "open" and node.args:
            return self._slot_of_path_expr(node.args[0], scope)
        if isinstance(node, ast.Subscript) and _snippet(node.value) == "sys.argv":
            idx = _subscript_const(node)
            return f"argv{idx}" if isinstance(idx, int) else None
        if isinstance(node, ast.Name):
            idx = scope["argv_index"].get(node.id)
            if idx is not None:
                return f"argv{idx}"
            src = scope["assigns"].get(node.id)
            if src is not None:
                return self._slot_of_stream_expr(src, scope, depth + 1)
        return None

    @staticmethod
    def _slot_of_path_expr(pathexpr, scope):
        if isinstance(pathexpr, ast.Subscript) and _snippet(pathexpr.value) == "sys.argv":
            idx = _subscript_const(pathexpr)
            return f"argv{idx}" if isinstance(idx, int) else None
        if isinstance(pathexpr, ast.Name):
            idx = scope["argv_index"].get(pathexpr.id)
            if idx is not None:
                return f"argv{idx}"
            return f"nonargv:{pathexpr.id}"
        return None

    # ---- expression resolution: NAME/expr -> KeyPath -------------------------------------------
    def resolve_expr(self, node, scope, depth=0):
        """Best-effort: resolve `node` to a KeyPath into a root document, or None."""
        if depth > 6:
            return None
        # direct doc reference
        if isinstance(node, ast.Name) and node.id in scope["doc_slot"]:
            return KeyPath(scope["doc_slot"][node.id], [])
        # a PLAIN scalar argv slot referenced bare (e.g. `rc != "1"` where `rc = sys.argv[3]`) — a
        # ROOT path with zero steps, exactly like a whole-document isinstance check: the poison
        # replaces the entire slot's value, there is no further key to address. Checked AFTER
        # doc_slot (a name can be bound as both if the checker re-purposes it, doc_slot must win)
        # and BEFORE the assigns/helper fallbacks below, so a name that is directly an argv value
        # is not misread as needing one more hop.
        if isinstance(node, ast.Name) and node.id in scope["argv_index"] and node.id not in scope["doc_slot"]:
            return KeyPath(f"argv{scope['argv_index'][node.id]}", [])
        # `X.get("key")` / `X.get("key", default)` / `X["key"]`
        base_path, key = self._peel_one_key(node, scope, depth)
        if base_path is not None and key is not None:
            return KeyPath(base_path.slot, base_path.steps + [("key", key)])
        # `(X.get("key") or {}).get("sub")` — BoolOp inside a Call chain: handled because
        # _peel_one_key recurses through BoolOr on the object side.
        # local variable alias: NAME = <expr>
        if isinstance(node, ast.Name) and node.id in scope["assigns"]:
            return self.resolve_expr(scope["assigns"][node.id], scope, depth + 1)
        # `helper(arg)` where helper is a module-level function of one parameter returning
        # `<param>.get("key")`-shaped expression, or a SELECTOR (list filter) — see _resolve_call.
        if isinstance(node, ast.Call):
            return self._resolve_call(node, scope, depth)
        # dict-literal subscript bound via a dict-comprehension assignment, e.g.
        # `fns = {leaf: unit(leaf) for leaf in (...)}` then `fns["exfil"]`
        if isinstance(node, ast.Subscript):
            return self._resolve_dictcomp_subscript(node, scope, depth)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and node.values:
            return self.resolve_expr(node.values[0], scope, depth + 1)
        return None

    def _peel_one_key(self, node, scope, depth):
        """Return (base_KeyPath, key) if node is `<base>.get("key"[, default])` or `<base>["key"]`
        or `bool(<base>.get(...))`/`set(<base>.get(...) or [])`-style wrappers (peeled first)."""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("bool", "set", "list", "sorted", "str") and len(node.args) == 1:
            return self._peel_one_key(node.args[0], scope, depth)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or) and node.values:
            return self._peel_one_key(node.values[0], scope, depth)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
            key = _lit(node.args[0])
            if isinstance(key, str):
                base = self.resolve_expr(node.func.value, scope, depth + 1)
                return base, key
        if isinstance(node, ast.Subscript):
            key = _subscript_const(node)
            if isinstance(key, str):
                base = self.resolve_expr(node.value, scope, depth + 1)
                return base, key
        return None, None

    def _resolve_call(self, node, scope, depth):
        if not isinstance(node.func, ast.Name):
            return None
        fn = self.helpers.get(node.func.id)
        if fn is None or len(fn.args.args) != 1 or not node.args:
            return None
        param = fn.args.args[0].arg
        callarg = node.args[0]
        # SELECTOR shape: `hits = [X for X in <doc>.get("<listkey>") if <transform>(X) == <param>]; return hits[0]...`
        sel = self._detect_selector(fn, param)
        if sel is not None:
            transform_src, loopvar = sel
            base_key = self._selector_base(fn, scope, depth)
            if base_key is None:
                return None
            base_path, listkey = base_key
            match_value = _lit(callarg)
            if match_value is _NOT_LITERAL and isinstance(callarg, ast.Name):
                # the call-site argument is a VARIABLE, not a literal directly — resolve it through
                # the current scope's bindings first (this is how a dict-comprehension's substituted
                # loop variable actually reaches here: `_resolve_dictcomp_subscript` binds the
                # comprehension's OWN loop var to a fake `ast.Constant` in a throwaway scope before
                # recursing into `unit(leaf)`, so `leaf` itself is never a literal AST node — only
                # what it is bound to is).
                bound = scope["assigns"].get(callarg.id)
                if bound is not None:
                    match_value = _lit(bound)
            if match_value is _NOT_LITERAL:
                # still not resolvable to a literal (e.g. a genuine runtime-computed argument) — out
                # of scope for this resolver; report unresolved upstream.
                return None
            matchfn = _compile_unary_lambda(loopvar, transform_src)
            if matchfn is None:
                return None
            return KeyPath(base_path.slot,
                            base_path.steps + [("select", listkey, _snippet(transform_src), matchfn, match_value)])
        # ACCESSOR shape: `def helper(param): return <param>.get("key") ...`
        for stmt in fn.body:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                inner_scope = {"assigns": {param: None}, "argv_index": {}, "doc_slot": {param: "__param__"}}
                path = self.resolve_expr(stmt.value, inner_scope, depth + 1)
                if path is not None and path.slot == "__param__":
                    argpath = self.resolve_expr(callarg, scope, depth + 1)
                    if argpath is not None:
                        return KeyPath(argpath.slot, argpath.steps + path.steps)
        return None

    def _selector_base(self, fn, scope, depth):
        """The (KeyPath-to-container, listkey) a helper's list comprehension iterates over, e.g.
        `rep.get("functions")` resolved against the OUTER scope — a helper's own body has no local
        doc bindings of its own, it reads whatever free variable the checker's entry scope already
        bound (e.g. `rep`), so resolution happens with the CALLER's scope, not the helper's."""
        for node in ast.walk(fn):
            if isinstance(node, ast.ListComp) and len(node.generators) == 1:
                iter_node = node.generators[0].iter
                base, key = self._peel_one_key(iter_node, scope, depth)
                if base is not None and key is not None:
                    return base, key
        return None

    def _detect_selector(self, fn, param):
        """Find `[X for X in <iterable> if <cond involving X and param>]` in fn's body and, if the
        condition is `<transform(X)> == param` (optionally via str()/.replace()/.split()[-1] — the
        family's OWN documented "match on the leaf" convention), return (transform_ast_for_X,
        loopvar_name). The transform is returned as an AST node so the caller can COMPILE it — the
        leaf-matching rule is derived from the checker's own source, never hard-coded here."""
        for node in ast.walk(fn):
            if isinstance(node, ast.ListComp) and len(node.generators) == 1:
                gen = node.generators[0]
                if not isinstance(gen.target, ast.Name):
                    continue
                loopvar = gen.target.id
                for cond in gen.ifs:
                    if isinstance(cond, ast.Compare) and len(cond.ops) == 1 and isinstance(cond.ops[0], ast.Eq):
                        left, right = cond.left, cond.comparators[0]
                        if isinstance(right, ast.Name) and right.id == param and _mentions(left, loopvar):
                            return left, loopvar
                        if isinstance(left, ast.Name) and left.id == param and _mentions(right, loopvar):
                            return right, loopvar
        return None

    def _resolve_dictcomp_subscript(self, node, scope, depth):
        if not isinstance(node.value, ast.Name):
            return None
        comp_expr = scope["assigns"].get(node.value.id)
        if not isinstance(comp_expr, ast.DictComp) or len(comp_expr.generators) != 1:
            return None
        gen = comp_expr.generators[0]
        if not isinstance(gen.target, ast.Name):
            return None
        key = _subscript_const(node)
        if key is None:
            return None
        # substitute the loop var with this literal key and resolve the comp's value expr
        fake_scope = dict(scope)
        fake_scope["assigns"] = dict(scope["assigns"])
        fake_scope["assigns"][gen.target.id] = ast.Constant(value=key)
        return self.resolve_expr(comp_expr.value, fake_scope, depth + 1)

    # ---- classification of a found Compare / isinstance node ------------------------------------
    def _classify_compare(self, node, scope, mode, parents):
        if len(node.ops) != 1:
            return  # chained comparisons (a < b < c) are out of scope for this vocabulary
        op = node.ops[0]
        left, right = node.left, node.comparators[0]
        exact_rc = _enclosing_exit_code(node, parents)

        if isinstance(op, (ast.Is, ast.IsNot)):
            lit = _lit(right)
            if isinstance(lit, bool):
                self._emit(node, scope, mode, SHAPE_IS_BOOL, isinstance(op, ast.IsNot), lit, left, exact_rc)
                return
        if isinstance(op, (ast.Eq, ast.NotEq)):
            litL, litR = _lit(left), _lit(right)
            value_side, lit = (right, litL) if litR is _NOT_LITERAL else (left, litR)
            other_lit = litL if litR is _NOT_LITERAL else litR
            if other_lit is _NOT_LITERAL:
                # neither side is a plain literal — could be sorted(a)==sorted(b) / set(a)==set(b)
                self._maybe_list_set_eq(node, scope, mode, isinstance(op, ast.NotEq), exact_rc)
                return
            if isinstance(lit, bool):
                self._emit(node, scope, mode, SHAPE_EQ_BOOL, isinstance(op, ast.NotEq), lit, value_side, exact_rc)
            elif isinstance(lit, (list, set)):
                self._emit(node, scope, mode, SHAPE_LIST_SET_EQ, isinstance(op, ast.NotEq), lit, value_side, exact_rc)
            else:
                self._emit(node, scope, mode, SHAPE_EQ_LITERAL, isinstance(op, ast.NotEq), lit, value_side, exact_rc)
            return
        if isinstance(op, (ast.In, ast.NotIn)):
            key = _lit(left)
            if isinstance(key, str):
                path = self.resolve_expr(right, scope)
                if path is not None:
                    self.findings.append(Finding(
                        node.lineno, SHAPE_PRESENCE, isinstance(op, ast.NotIn), key,
                        KeyPath(path.slot, path.steps + [("key", key)]), mode, _snippet(node), exact_reject_code=exact_rc))
                else:
                    self._unresolved(node, mode, f"membership test on an unresolved container: {_snippet(right)}")

    def _maybe_list_set_eq(self, node, scope, mode, negated, exact_rc):
        left, right = node.left, node.comparators[0]

        def unwrap(n):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("sorted", "set", "list"):
                return n.args[0] if n.args else n
            return n

        lu, ru = unwrap(left), unwrap(right)
        lp = self.resolve_expr(lu, scope)
        if lp is not None:
            self._record(node, mode, SHAPE_LIST_SET_EQ, negated, None, lp, exact_rc)
            return
        rp = self.resolve_expr(ru, scope)
        if rp is not None:
            self._record(node, mode, SHAPE_LIST_SET_EQ, negated, None, rp, exact_rc)
            return
        self._unresolved(node, mode, f"list/set equality between two unresolved expressions: {_snippet(node)}")

    def _classify_isinstance(self, node, scope, mode, parents):
        if len(node.args) != 2:
            return
        target, typ = node.args
        typename = _snippet(typ)
        path = self.resolve_expr(target, scope)
        # `not isinstance(...)` is the guard shape that matters (a dropped guard passes silently);
        # walk parents to see if this call sits inside a `not (...)` / is the sole test of an `if`
        # that we can treat as "isinstance must hold".
        exact_rc = _enclosing_exit_code(node, parents)
        if path is not None:
            self.findings.append(Finding(node.lineno, SHAPE_ISINSTANCE, False, typename, path, mode,
                                          _snippet(node), exact_reject_code=exact_rc))
        else:
            self._unresolved(node, mode, f"isinstance guard on an unresolved target: {_snippet(node)}")

    def _emit(self, node, scope, mode, shape, negated, lit, value_node, exact_rc):
        path = self.resolve_expr(value_node, scope)
        self._record(node, mode, shape, negated, lit, path, exact_rc)

    def _record(self, node, mode, shape, negated, lit, path, exact_rc):
        if path is None:
            self._unresolved(node, mode, f"{shape} comparison, value side unresolved: {_snippet(node)}")
            return
        self.findings.append(Finding(node.lineno, shape, negated, lit, path, mode, _snippet(node),
                                      exact_reject_code=exact_rc))

    def _unresolved(self, node, mode, reason):
        self.findings.append(Finding(node.lineno, "UNRESOLVED", False, None, None, mode, _snippet(node),
                                      unresolved_reason=reason))


def _mentions(node, name):
    return any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(node))


def _compile_unary_lambda(param_name, body_node):
    """Turn an AST expression (a selector's own transform, e.g.
    `str(f.get("fn", "")).replace("::", ".").split(".")[-1]`) into a REAL callable of one argument
    named `param_name` — compiled from the checker's own AST subtree (via a fresh, unparsed source
    string), not reinvented. Returns None if it won't compile standalone (e.g. it references a name
    other than the loop variable and Python builtins)."""
    try:
        src = f"lambda {param_name}: {ast.unparse(body_node)}"
        return eval(compile(src, "<selector-transform>", "eval"), {"__builtins__": __builtins__})
    except Exception:
        return None


def dict_copy(scope):
    return {"assigns": dict(scope["assigns"]), "argv_index": dict(scope["argv_index"]),
            "doc_slot": dict(scope["doc_slot"])}


# ════════════════════════════════════════════════════════════════════════════════════════════════
# NEAR-MISS EMISSION — given a Finding, produce the mechanical poison family.
# ════════════════════════════════════════════════════════════════════════════════════════════════

def near_miss_family(finding, baseline_value=None, baseline_has_key=True, root_path=False):
    """Yield (family_name, poison_value) pairs — the value this ONE key must take so a checker
    degraded from the classified shape to the named near-miss would wrongly accept it, while the
    real (correct) checker must still reject it. `MISSING` means "delete the key entirely".

    `baseline_value` is the CORRECT (accept-known-good) value already sitting at this key in the
    supplied baseline document — used only when the expected value could not be read off the
    checker's source as a literal (e.g. `sorted(a) == sorted(b)`, where the comparison names no
    constant list at all). This is not domain knowledge invented by the generator: it is the same
    baseline the human already supplied, read back rather than duplicated.

    `baseline_has_key` says whether the SUPPLIED baseline carries this key at all — load-bearing for
    SHAPE_PRESENCE: a bare `"key" in d` / `"key" not in d` has no "wrong value" to degrade to, only
    two states (present/absent), and the direction that constitutes a near-miss is whichever one the
    baseline does NOT already occupy (deleting an already-absent key is a no-op, not a poison — this
    was a real bug caught by this tool's own over-charge control, not a hypothetical).

    `root_path` says the resolved path has ZERO key steps — the comparison is about the WHOLE
    document (e.g. `isinstance(d, dict)`), which has no parent container an "absent" poison could
    remove a key from; that family member is skipped rather than raising later."""
    shape, lit, neg = finding.shape, finding.literal, finding.negated
    if shape in (SHAPE_IS_BOOL, SHAPE_EQ_BOOL):
        # correct check demands the literal `lit` (is True/False); the two near-misses are the
        # OTHER boolean-ish values that agree with `lit` under plain truthiness but not identity.
        yield "truthy_not_true", 1
        yield "falsy_not_false", 0
        if not root_path:
            yield "absent", MISSING
    elif shape == SHAPE_EQ_LITERAL:
        if isinstance(lit, str) and lit:
            yield "substring", lit + "0"          # contains `lit` as a substring, is not equal to it
            yield "wrong_value", lit + "-DIFFERENT"
        elif isinstance(lit, (int, float)) and not isinstance(lit, bool):
            yield "falsy_not_exact", 0 if lit != 0 else 1
        else:
            yield "wrong_value", None
        if not root_path:
            yield "absent", MISSING
    elif shape == SHAPE_LIST_SET_EQ:
        base = list(lit) if lit else (list(baseline_value) if baseline_value else [])
        yield "superset", base + ["__extra__"]
        if base:   # a proper SUBSET of an already-empty expected collection does not exist —
            yield "subset", base[:-1]   # yielding `[]` again would be a no-op mutation, not a poison
        else:
            # `!= []` degraded to plain truthiness (`if x:`) accepts EVERY truthy poison for the same
            # accidental reason a correct `!= []` also rejects them (both non-empty is truthy) — the
            # one value only the degraded form wrongly waves through is FALSY but not exactly `[]`.
            # An empty STRING is falsy, JSON-serialisable, and not a list — mutation-gate.sh's own S4
            # fix (`violations: ""`) is this exact family member.
            yield "falsy_not_exact", ""
        if not root_path:
            yield "absent", MISSING
    elif shape == SHAPE_ISINSTANCE:
        wrong = {"list": "not-a-list", "dict": ["not", "a", "dict"], "str": 12345}.get(lit, "wrong-type")
        yield "wrong_type", wrong
        if not root_path:
            yield "absent", MISSING
    elif shape == SHAPE_PRESENCE:
        # the ONLY two states are present/absent — poison whichever one the baseline is NOT already
        # in, or the mutation is a no-op (this exact bug was caught live: an "absent" poison against
        # a baseline that already lacks the key silently changed nothing and was wrongly recorded as
        # the CHECKER failing to discriminate).
        if baseline_has_key:
            yield "absent", MISSING
        else:
            yield "present", "__poison_present__"
    # UNRESOLVED shapes yield nothing — handled separately as a loud report, never silently poisoned.


# ════════════════════════════════════════════════════════════════════════════════════════════════
# DOCUMENT MUTATION — apply a resolved KeyPath + near-miss value to a baseline document.
# ════════════════════════════════════════════════════════════════════════════════════════════════

class UnresolvableMutation(Exception):
    pass


def apply_mutation(baseline, path, value):
    """Return a DEEP COPY of `baseline` with the field at `path.steps` set to `value`
    (or removed, if value is MISSING). A ROOT path (zero steps — the comparison is about the WHOLE
    document, e.g. `isinstance(d, dict)`) has no parent container to set a key on: the poison IS the
    whole replacement document. `near_miss_family(..., root_path=True)` never yields MISSING for such
    a path, so the ValueError below is a defensive check, not a reachable one in normal use."""
    if not path.steps:
        if value is MISSING:
            raise UnresolvableMutation("root-level (whole-document) path has no parent key to remove")
        return copy.deepcopy(value)
    doc = copy.deepcopy(baseline)
    _apply_steps(doc, path.steps, value)
    return doc


def _apply_steps(container, steps, value):
    if not steps:
        raise UnresolvableMutation("empty key path — nothing to mutate")
    step = steps[0]
    if step[0] == "key":
        key = step[1]
        if len(steps) == 1:
            if value is MISSING:
                container.pop(key, None)
            else:
                container[key] = value
            return
        if key not in container or not isinstance(container[key], (dict, list)):
            container[key] = {} if steps[1][0] == "key" else []
        _apply_steps(container[key], steps[1:], value)
    elif step[0] == "select":
        _, listkey, _, matchfn, matchval = step
        lst = container.get(listkey) or []
        target = None
        if matchfn is not None:
            for entry in lst:
                try:
                    if isinstance(entry, dict) and matchfn(entry) == matchval:
                        target = entry
                        break
                except Exception:
                    continue
        if target is None:
            raise UnresolvableMutation(f"no entry in `{listkey}` matches selector == {matchval!r} "
                                        f"(baseline document may not carry this checker's expected shape)")
        _apply_steps(target, steps[1:], value)
    else:
        raise UnresolvableMutation(f"unknown key-path step {step!r}")


def _navigate_container(doc, steps):
    """Walk BOTH step kinds ("key" and "select") from `doc` and return the value at the end — the
    shared traversal `apply_list_membership_mutation` needs (a "select" step can legitimately precede
    the final list-holding key, e.g. fs_position_check.py's `paths(fns['exfil'])`: select the
    function entry named `exfil`, THEN read its `paths` field)."""
    node = doc
    for step in steps:
        if node is None:
            raise UnresolvableMutation("path traverses through a missing/None container")
        if step[0] == "key":
            if not isinstance(node, dict):
                raise UnresolvableMutation(f"expected a dict to read key {step[1]!r}, found {type(node).__name__}")
            node = node.get(step[1])
        elif step[0] == "select":
            _, listkey, _, matchfn, matchval = step
            lst = node.get(listkey) if isinstance(node, dict) else None
            found = None
            if matchfn is not None:
                for entry in (lst or []):
                    try:
                        if isinstance(entry, dict) and matchfn(entry) == matchval:
                            found = entry
                            break
                    except Exception:
                        continue
            if found is None:
                raise UnresolvableMutation(f"no entry in `{listkey}` matches selector == {matchval!r}")
            node = found
        else:
            raise UnresolvableMutation(f"unknown key-path step {step!r}")
    return node


def apply_list_membership_mutation(baseline, container_path, literal, add):
    """Return a DEEP COPY of `baseline` with `literal` added to (or removed from) the LIST value
    sitting at `container_path` — the runtime-disambiguated counterpart to apply_mutation's dict-key
    presence handling (see evaluate_checker's SHAPE_PRESENCE branch for why this is decided from the
    baseline's actual type rather than from source alone)."""
    doc = copy.deepcopy(baseline)
    lst = _navigate_container(doc, container_path.steps)
    if not isinstance(lst, list):
        raise UnresolvableMutation(f"expected a list at {container_path.describe()}, found {type(lst).__name__}")
    if add:
        if literal not in lst:
            lst.append(literal)
    else:
        if literal in lst:
            lst.remove(literal)
    return doc


def read_value(doc, path):
    """The value currently sitting at `path.steps` in `doc` — used to derive a superset/subset
    near-miss when the checker's own source names no literal collection (e.g. `sorted(a)==sorted(b)`)."""
    node = doc
    for step in path.steps:
        if node is None:
            return None
        if step[0] == "key":
            node = node.get(step[1]) if isinstance(node, dict) else None
        elif step[0] == "select":
            _, listkey, _, matchfn, matchval = step
            lst = node.get(listkey) if isinstance(node, dict) else None
            found = None
            if matchfn is not None:
                for entry in (lst or []):
                    try:
                        if isinstance(entry, dict) and matchfn(entry) == matchval:
                            found = entry
                            break
                    except Exception:
                        continue
            node = found
    return node


def key_present(doc, path):
    """Does `doc` already carry the leaf key `path.steps[-1]`? (True for a root/select-only path —
    there is no separate leaf key to be missing.) Load-bearing for SHAPE_PRESENCE: see
    near_miss_family's docstring for the bug this exists to prevent."""
    if not path.steps or path.steps[-1][0] != "key":
        return True
    node = doc
    for step in path.steps[:-1]:
        if node is None:
            return False
        if step[0] == "key":
            node = node.get(step[1]) if isinstance(node, dict) else None
        elif step[0] == "select":
            _, listkey, _, matchfn, matchval = step
            lst = node.get(listkey) if isinstance(node, dict) else None
            found = None
            if matchfn is not None:
                for entry in (lst or []):
                    try:
                        if isinstance(entry, dict) and matchfn(entry) == matchval:
                            found = entry
                            break
                    except Exception:
                        continue
            node = found
    return isinstance(node, dict) and path.steps[-1][1] in node


# ════════════════════════════════════════════════════════════════════════════════════════════════
# INVOCATION — run a checker (embedded or standalone) against a document set, fail closed on
# anything this tool itself cannot make sense of.
# ════════════════════════════════════════════════════════════════════════════════════════════════

@dataclass
class Call:
    """One concrete invocation shape for a checker: the baseline (accept-known-good) value for every
    slot it reads, how to build argv from a dict of {slot: filepath-or-literal}, and how to tell
    reject from accept. `mode` matches Finding.mode (the `want=="X"` guard a comparison lives under),
    so a poison is only generated for conditions this call's own baseline would actually exercise."""
    mode: Optional[str]
    baseline: dict                       # slot_id -> JSON-serialisable value (dict/list) or plain str
    argv: Callable[[dict], list]         # (slot_id -> path-or-value) -> argv list (script name excluded)
    stdin_slot: Optional[str] = None
    accept_rc: int = 0
    mirror: dict = field(default_factory=dict)
    # slot -> slot: some checkers ALSO assert two slots are byte/content-IDENTICAL (ck83_control's
    # `sb != rb`), checked independently of any single-slot field condition. Poisoning only ONE slot
    # while holding its mirror at the unchanged baseline breaks that identity as a SIDE EFFECT, so the
    # cross-document check fires regardless of whether the field-level mutation under test would have
    # been caught on its own — masking the very condition being isolated (reproduced live: ck83_
    # control's `d_ok` near-miss legs were rejected by every mutant, real AND buggy alike, until this
    # was added — not because the poison was wrong, but because `sb != rb` fired first for an
    # unrelated reason). Declaring `{"argv1": "argv2"}` here mirrors any poison applied to argv1 onto
    # argv2 as well, matching how mutation-gate.sh's OWN hand-built fixtures for this exact checker
    # `cp`the mutated scan.json onto report.json rather than leaving report.json at baseline.


@dataclass
class CheckerConfig:
    name: str
    source_fn: Callable[[], str]         # lazy: extract_pyvar(...) / extract_bashfunc_pyc(...) / read_extfile(...)
    interpreter: str                     # "python3 -c <source>" (embedded) or "python3 <path>" (extfile)
    calls: list                          # list[Call]
    notes: str = ""


def run_checker(cfg, argv_list, stdin_bytes=None):
    tmp_path = None
    if cfg.interpreter == "inline":
        cmd = [sys.executable, "-c", cfg.source_fn()] + argv_list
    elif cfg.interpreter.startswith("file:"):
        # Route through source_fn() — written to a scratch file — rather than execing
        # cfg.interpreter's path directly. In ORDINARY operation source_fn() for an extfile config
        # just re-reads the real file (mutation_poison_configs.py's read_extfile), so this is
        # behaviourally identical to running the file in place. What it ALSO enables: swapping in a
        # DIFFERENT source via `dataclasses.replace(cfg, source_fn=...)`, which retro_test.py and
        # generator_canary.py both depend on — bypassing source_fn here made every standalone-checker
        # mutation test silently execute the REAL, unmutated file instead (caught live: generator_
        # canary.py's extfile canary reported the real checker's own correct behaviour, not the
        # unconditional-accept/crash mutant it was asked to run, until this was fixed).
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=os.path.dirname(cfg.interpreter[5:]) or None) as tf:
            tf.write(cfg.source_fn())
            tmp_path = tf.name
        cmd = [sys.executable, tmp_path] + argv_list
    else:
        raise GeneratorError(f"unknown interpreter kind for {cfg.name}: {cfg.interpreter!r}")
    try:
        r = subprocess.run(cmd, input=stdin_bytes, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired as e:
        raise GeneratorError(f"{cfg.name}: checker invocation timed out: {e}")
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    out = (r.stdout or b"").decode(errors="replace") + (r.stderr or b"").decode(errors="replace")
    return r.returncode, out


def _write_doc(tmpdir, slot, value):
    p = os.path.join(tmpdir, f"{slot}.json")
    with open(p, "w") as f:
        if isinstance(value, str):
            f.write(value)
        else:
            json.dump(value, f)
    return p


@dataclass
class RowResult:
    status: str      # "PASS" | "BROKEN" | "ERROR"
    label: str
    detail: str = ""


def _has_traceback(out):
    return "Traceback (most recent call last)" in out


def run_call_reject(cfg, call, finding, poison_slot, poisoned_doc, tmpdir_root, label):
    """Write `poisoned_doc` at `poison_slot`, every OTHER slot at its call baseline unchanged, invoke
    the checker, and require REJECTION — a specific exit code if the source itself pinned one
    (`finding.exact_reject_code`), else any nonzero exit with no raw traceback (a crash is exactly as
    broken as silence — mutation-gate.sh's own rule, restated here)."""
    mirrored_slot = call.mirror.get(poison_slot)
    with tempfile.TemporaryDirectory(dir=tmpdir_root) as tmp:
        slot_paths = {}
        stdin_bytes = None
        for slot, val in call.baseline.items():
            v = poisoned_doc if slot in (poison_slot, mirrored_slot) else val
            if slot == call.stdin_slot:
                stdin_bytes = (v if isinstance(v, str) else json.dumps(v)).encode()
            elif isinstance(v, str):
                # a PLAIN argv string (engine name, expected rc, expected-output substring) — passed
                # through literally, never written to a file. Whether a slot is a JSON document or a
                # plain string is decided by its baseline's Python TYPE (dict/list vs str), set once
                # in mutation_poison_configs.py — never guessed from the slot's name.
                slot_paths[slot] = v
            else:
                slot_paths[slot] = _write_doc(tmp, slot, v)
        argv_list = call.argv(slot_paths)
        rc, out = run_checker(cfg, argv_list, stdin_bytes)
    if _has_traceback(out):
        return RowResult("BROKEN", label, f"checker CRASHED on poison instead of rejecting cleanly (rc={rc}):\n{out[:800]}")
    if finding.exact_reject_code is not None:
        ok = (rc == finding.exact_reject_code)
        want = f"exit {finding.exact_reject_code}"
    else:
        ok = (rc != call.accept_rc)
        want = f"any exit != {call.accept_rc}"
    if ok:
        return RowResult("PASS", label, f"rejected (rc={rc}, wanted {want})")
    return RowResult("BROKEN", label, f"poison was ACCEPTED (rc={rc}, wanted {want}) — the checker did not "
                                       f"discriminate this condition:\n{out[:400]}")


def run_call_accept(cfg, call, tmpdir_root, label):
    """The call's own baseline, unmodified, MUST be accepted — the A2 hardening control
    (mutation-gate.sh's header): a checker degenerated to unconditional rejection passes every
    poison leg while being dead, and only an accept-known-good check catches that."""
    with tempfile.TemporaryDirectory(dir=tmpdir_root) as tmp:
        slot_paths = {}
        stdin_bytes = None
        for slot, val in call.baseline.items():
            if slot == call.stdin_slot:
                stdin_bytes = (val if isinstance(val, str) else json.dumps(val)).encode()
            elif isinstance(val, str):
                slot_paths[slot] = val
            else:
                slot_paths[slot] = _write_doc(tmp, slot, val)
        argv_list = call.argv(slot_paths)
        rc, out = run_checker(cfg, argv_list, stdin_bytes)
    if _has_traceback(out):
        return RowResult("BROKEN", label, f"checker CRASHED on its OWN accept-known-good document (rc={rc}):\n{out[:800]}")
    if rc == call.accept_rc:
        return RowResult("PASS", label, f"accepted (rc={rc})")
    return RowResult("BROKEN", label, f"a VALID document was REJECTED (rc={rc}, wanted {call.accept_rc}) — "
                                       f"checker may have degenerated to unconditional-reject:\n{out[:400]}")


def evaluate_checker(cfg, findings, tmpdir_root):
    """Run every classified, resolved comparison's near-miss family against every Call whose `mode`
    matches, plus one accept-known-good check per Call. Returns (rows, unresolved_findings)."""
    rows = []
    unresolved = [f for f in findings if f.path is None]
    by_mode = {}
    for f in findings:
        if f.path is None:
            continue
        by_mode.setdefault(f.mode, []).append(f)

    for call in cfg.calls:
        rows.append(run_call_accept(cfg, call, tmpdir_root, f"{cfg.name}{'/' + call.mode if call.mode else ''} (accept-known-good)"))
        relevant = by_mode.get(call.mode, [])
        for f in relevant:
            if f.path.slot not in call.baseline:
                unresolved.append(Finding(f.lineno, f.shape, f.negated, f.literal, f.path, f.mode, f.snippet,
                                           unresolved_reason=f"resolved to slot {f.path.slot!r}, which this "
                                                              f"call's config does not declare a baseline for"))
                continue
            baseline_doc = call.baseline[f.path.slot]

            # SHAPE_PRESENCE is ambiguous from source ALONE between "is this KEY present in a dict"
            # (`"ok" in d`) and "is this ELEMENT a member of a list" (`"incomplete" not in resolves`,
            # incomplete_check.py's exact shape) — both parse as the identical ast.Compare(In/NotIn).
            # Disambiguated at RUNTIME from the baseline's own type at the CONTAINER position (one
            # step shallower than the resolved path, which always ends in the literal-as-a-key step —
            # see _classify_compare) rather than guessed at classify time.
            if f.shape == SHAPE_PRESENCE and f.path.steps:
                container_path = KeyPath(f.path.slot, f.path.steps[:-1])
                container_val = read_value(baseline_doc, container_path)
                literal = f.path.steps[-1][1]
                if isinstance(container_val, list):
                    is_member = literal in container_val
                    family, add = ("absent", False) if is_member else ("present", True)
                    label = f"{cfg.name}{'/' + call.mode if call.mode else ''} L{f.lineno} list_member[{family}] ({f.path.describe()})"
                    try:
                        poisoned = apply_list_membership_mutation(baseline_doc, container_path, literal, add)
                    except UnresolvableMutation as e:
                        unresolved.append(Finding(f.lineno, f.shape, f.negated, f.literal, f.path, f.mode,
                                                   f.snippet, unresolved_reason=f"could not apply list-"
                                                   f"membership mutation: {e}"))
                        continue
                    rows.append(run_call_reject(cfg, call, f, f.path.slot, poisoned, tmpdir_root, label))
                    continue
                if not isinstance(container_val, dict):
                    # a plain scalar (str/int/None) container: `"X" in out` over a free-text CLI
                    # argument is a deliberate substring/grep check, not a degradable key/element
                    # presence test — nothing to poison, and this is a POSITIVE classification (the
                    # generator recognised the shape and correctly declined it), not a gap. Recorded
                    # as an ordinary PASS row so it is still visible in the report, never silent.
                    rows.append(RowResult("PASS", f"{cfg.name} L{f.lineno} presence-over-scalar (not "
                                                   f"poisoned: {f.path.describe()} is free text, not a "
                                                   f"structured container)", "recognised, not degradable"))
                    continue
                # else: container IS a dict — fall through to the ordinary dict-key-presence path below.

            base_val = read_value(baseline_doc, f.path)
            has_key = key_present(baseline_doc, f.path)
            for family, poison in near_miss_family(f, baseline_value=base_val, baseline_has_key=has_key,
                                                    root_path=not f.path.steps):
                label = f"{cfg.name}{'/' + call.mode if call.mode else ''} L{f.lineno} {f.shape}[{family}] ({f.path.describe()})"
                try:
                    poisoned = apply_mutation(baseline_doc, f.path, poison)
                except UnresolvableMutation as e:
                    unresolved.append(Finding(f.lineno, f.shape, f.negated, f.literal, f.path, f.mode, f.snippet,
                                               unresolved_reason=f"could not apply mutation: {e}"))
                    continue
                rows.append(run_call_reject(cfg, call, f, f.path.slot, poisoned, tmpdir_root, label))
    return rows, unresolved


# ════════════════════════════════════════════════════════════════════════════════════════════════
# REPORTING + CLI
# ════════════════════════════════════════════════════════════════════════════════════════════════

def print_findings(name, findings):
    print(f"\n--- {name}: classified comparisons ---")
    resolved = [f for f in findings if f.path is not None]
    unresolved = [f for f in findings if f.path is None]
    for f in resolved:
        tag = f" [{f.mode}]" if f.mode else ""
        print(f"  L{f.lineno:<4} {f.shape:<12}{tag} {'NOT ' if f.negated else ''}{f.literal!r} "
              f"<- {f.path.describe()}   ({f.snippet})")
    if unresolved:
        print(f"  UNRESOLVED ({len(unresolved)}):")
        for f in unresolved:
            tag = f" [{f.mode}]" if f.mode else ""
            print(f"    L{f.lineno}{tag} {f.snippet} — {f.unresolved_reason}")
    print(f"  {len(resolved)} resolved, {len(unresolved)} unresolved")


def run_one(cfg, tmpdir_root, waivers=()):
    """Classify + evaluate one CheckerConfig. Returns (ok: bool, findings, rows, unresolved)."""
    source = cfg.source_fn()
    # MEASURED: extract_pyvar (--extract-var) parses the ENTIRE run.sh with a real bash-quote
    # grammar and takes ~6-7s per call. run_checker() calls `cfg.source_fn()` fresh on every single
    # subprocess invocation (one per near-miss leg + one accept check) — for a checker with a dozen
    # legs that is minutes of pure re-parsing of a file that has not changed since this function's
    # own first call. Cache it ONCE per run_one() call, never across checkers (a later checker's
    # source must still be read fresh, in case it was edited between runs).
    cfg.source_fn = (lambda s=source: s)
    findings = Classifier(source, filename=cfg.name).run()
    print_findings(cfg.name, findings)
    rows, unresolved = evaluate_checker(cfg, findings, tmpdir_root)
    waived_lines = {w[0] for w in waivers}
    hard_unresolved = [u for u in unresolved if u.lineno not in waived_lines]
    print(f"\n--- {cfg.name}: results ---")
    broken = [r for r in rows if r.status != "PASS"]
    for r in rows:
        mark = "PASS  " if r.status == "PASS" else "BROKEN"
        print(f"  {mark}  {r.label}")
        if r.status != "PASS":
            for line in r.detail.splitlines():
                print(f"          {line}")
    if hard_unresolved:
        print(f"  {len(hard_unresolved)} UNCLASSIFIABLE comparison(s) — reported, not silently skipped:")
        for u in hard_unresolved:
            print(f"    L{u.lineno}: {u.snippet} — {u.unresolved_reason}")
    if waivers:
        print(f"  {len(waivers)} waived (see config, each with a reason):")
        for lineno, why in waivers:
            print(f"    L{lineno}: {why}")
    ok = not broken and not hard_unresolved
    print(f"  {cfg.name}: {'OK' if ok else 'FAILED'} — {len(rows)} row(s), {len(broken)} broken, "
          f"{len(hard_unresolved)} unresolved")
    return ok, findings, rows, hard_unresolved


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated checker names")
    ap.add_argument("--list-findings", help="classify one checker and print findings only, no run")
    args = ap.parse_args(argv)

    try:
        import mutation_poison_configs as cfgmod
    except Exception as e:
        print(f"mutation_poison_gen: FAIL — could not import mutation_poison_configs.py: {e}")
        return 1

    if args.list_findings:
        cfg = cfgmod.CHECKERS[args.list_findings]
        findings = Classifier(cfg.source_fn(), filename=cfg.name).run()
        print_findings(cfg.name, findings)
        return 0

    names = args.only.split(",") if args.only else list(cfgmod.CHECKERS.keys())
    tmproot = tempfile.mkdtemp(prefix="mutation-poison-")
    try:
        overall_ok = True
        for name in names:
            cfg = cfgmod.CHECKERS[name]
            waivers = getattr(cfgmod, "WAIVERS", {}).get(name, ())
            try:
                ok, _, _, _ = run_one(cfg, tmproot, waivers)
            except (ExtractionError, GeneratorError) as e:
                print(f"\n--- {name}: HARD FAILURE (fail-closed, not a skip) ---\n  {e}")
                ok = False
            overall_ok = overall_ok and ok
        print(f"\nmutation_poison_gen: {'OK' if overall_ok else 'FAILED'}")
        return 0 if overall_ok else 1
    finally:
        import shutil
        shutil.rmtree(tmproot, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:   # fail closed: an error in THIS tool is a hard failure, never a silent pass
        import traceback
        traceback.print_exc()
        print(f"\nmutation_poison_gen: FAIL — the generator's own machinery raised {e!r}. "
              f"This is a hard failure, not a skipped checker.")
        sys.exit(1)
