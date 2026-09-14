#!/usr/bin/env python3
"""
PART 89 — THE CONDITIONAL-BINDING UNION DIFFERENTIAL — ⟨0.38⟩, rust + swift.

A `use … as X` / `typealias X = …` declared twice under mutually-exclusive configuration arms resolves
to the UNION of the arms' effects, exactly as a conditional DEFINITION does (⟨0.36⟩). Three things can go
wrong and this part separates them, because two of them were live when it was written:

  PICK    resolve by source order   — the ⟨0.21⟩ cardinal sin. The losing arm's effects are GONE.
  HEDGE   withdraw to {Unknown}     — not ⊤ under §4.0, so it WITHDRAWS a determined effect and
                                      `deny <E>` stops firing on a call that reaches <E>.
  UNION   charge both, no surface   — the ruled answer (Tom, 2026-09-12).

WHY `deny Env` IS THE DISCRIMINATOR AND `deny Fs` IS NOT. Every arm of these fixtures reaches Fs by one
route or another, so an Fs-shaped question cannot tell the three apart. `Env` is carried by ONE arm only:
a PICK that lost that arm is silent, a HEDGE that renamed it `Unknown` is silent, and only the UNION
fires. b2order is the same question with the arms written the other way round — a pick answers those two
differently, which is the one property R105 was filed for and the one that holds whatever the right
answer turns out to be.

THE CONTROLS ARE NOT AFTERTHOUGHTS. A union is an OVER-report by construction, so the cost side needs
pinning as hard as the defect:

  b3nohedge  deny Unknown  -> 0  the answer is a complete one, not a withdrawal
  b5agree    deny Env      -> 0  arms that classify ALIKE must not manufacture the other arm's effect.
                                 This is the shape measured at 6.6% prevalence in a real registry slice
                                 (R105): every real conditional binding out there is a portability shim
                                 whose arms agree, so a union that added noise here would add it to
                                 almost every real hit and to nothing else.
  b6single   allow Fs <lit>-> 0  an ORDINARY binding still resolves AND still certifies off its literal.
                                 If a widening makes this red, the fix has made determined code
                                 uncertifiable — R416's shape, which is how the ⟨0.37⟩ rung's own
                                 over-charge control earned its keep on first run.

b4surface is the half a union gets wrong: the arms are DIFFERENT targets, so publishing either one's
literal is the pick-by-position this clause forbids arriving by another route. It must fail closed.

MEASURED BEFORE THIS FILE EXISTED, on the shipped 0.37.0 engines:
    arm        rust                         swift
    b1union    HEDGE ({Unknown}, silent)    PICK (source order, arm dropped)
    b2order    HEDGE                        PICK — and answers the two orders DIFFERENTLY
NEITHER IS FULLY FIXED, and this docstring claimed they were. Both fixes closed the case where every
arm names a PROJECT-DECLARED target; a MIXED arm set (one project type beside a framework or `std` one)
still picks. **THIS PART CANNOT SEE THAT, and the reason is worth reading before trusting its green:**
all six swift arms below are project-declared enums, so the part sits entirely inside the narrowing that
hides the defect. A green here is evidence about the narrowed case only. The mixed-arm arms are owed
(b7mixed / b8mixedallow) and are expected RED on both engines when they land.

java/ts have no mutually-exclusive configuration construct. Declared exclusions with that reason — not
gaps, and not silently absent rows.

REUSES gen_masking.ENGINES rather than copying the Engine classes (R288's fifteen-`ab.py` shape, inside
the suite). This file does not become the sixth copy.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_masking as gm  # noqa: E402  -- import-safe: its work is behind a __main__ guard

ALLOWED = "/tmp/benign"
EFF = {"id": "bindunion"}

# arm -> (policy key, expected gate rc, what it proves, engines that cannot express it)
SKIP = ("java", "ts")
ARMS = [
    ("b1union",   "denyenv",  1, "the OTHER arm's effect is charged — a pick or a hedge is silent here", SKIP),
    ("b2order",   "denyenv",  1, "…and the same answer with the arms written the other way round",       SKIP),
    ("b3nohedge", "denyunk",  0, "CONTROL: the answer is the UNION, never a withdrawal to {Unknown}",     SKIP),
    ("b4surface", "allowfs",  1, "no arm's literal may certify — the surface is withheld",                SKIP),
    ("b5agree",   "denyenv",  0, "CONTROL: arms that classify ALIKE manufacture nothing",                 SKIP),
    ("b6single",  "allowfs",  0, "CONTROL: an ordinary binding still resolves and still certifies",       SKIP),
    # THE MIXED ARM SET — one PROJECT-DECLARED target beside a framework/std one. Both engines closed
    # only the all-project-declared case, and both parts of that narrowing are invisible to the six arms
    # above because every one of them declares all its arms locally. This is the ordinary portability
    # shim (`Color = NSColor | UIColor`; `#[cfg(unix)] std::fs::write` beside a crate-local fallback),
    # measured at 1,173 of 3,052 registry files carrying two cfg-gated `use` items.
    # EXPECTED RED until R429 (swift) and R438 (rust) land — written first, deliberately, because a part
    # that arrives after the fix cannot falsify it.
    ("b7mixed",     "denyenv",  1, "a MIXED arm set charges BOTH arms — not just the one the engine can type", SKIP),
    ("b8mixedrev",  "denyenv",  1, "…and the same answer with the mixed arms written the other way round",     SKIP),
    ("b9mixedallow","allowfs",  1, "a MIXED set must not CERTIFY off the arm it happened to resolve",          SKIP),
]

_RUST_CALL = "use crate::sys::put;\npub fn probe() { let _ = put(\"%s\", \"x\"); }\n" % ALLOWED
def _dbl(s):
    """`gm._rust_tree` runs `.format()` over the body, so every literal brace must be doubled — the same
    reason gen_stat_locator's bodies carry `{{`. Done here rather than in the string literals because
    these bodies are BUILT, and a hand-doubled template is one edit away from being wrong."""
    return s.replace("{", "{{").replace("}", "}}")


def _rust(first, second):
    return _dbl("pub mod sys {\n  #[cfg(unix)] pub use %s as put;\n  #[cfg(not(unix))] pub use %s as put;\n}\n%s"
                % (first, second, _RUST_CALL))

FS, ENV = "std::fs::write", "std::env::set_var"

# The MIXED shape: one arm names a target the classifier can type (`std::fs::write`), the other a
# PROJECT-LOCAL one. rust classifies a local target to `None` and drops it, so the set resolves to the
# std arm alone AND publishes its literal.
_RUST_MIXED = (
    "pub mod loc { pub fn put(_p: &str, _v: &str) { std::env::set_var(\"K\", \"1\"); } }\n"
    "pub mod sys {\n  #[cfg(unix)] pub use %s as put;\n  #[cfg(not(unix))] pub use %s as put;\n}\n"
    "use crate::sys::put;\npub fn probe() { let _ = put(\"" + ALLOWED + "\", \"x\"); }\n"
)

# b4surface needs arms that name DIFFERENT destinations, and that is the whole point of the arm. The
# other arms bind to two std functions called at ONE call site, so both arms share the site's literal and
# there is nothing for a union to hide — swift CERTIFIES that shape and is right to: in every
# configuration the Fs reach is exactly that literal. Measured on the first run of this part, against a
# clause that said the surface MUST be incomplete; the clause was too strong and was corrected, which is
# what an over-charge control is for. The hazard is arms whose literals DIFFER — certify off one and the
# other is hidden — so these arms are PROJECT functions carrying a literal each.
_RUST_TWO_LIT = (
    "pub mod a { pub fn put(_x: &str) { let _ = std::fs::write(\"%s\", b\"x\"); } }\n"
    "pub mod b { pub fn put(_x: &str) { let _ = std::fs::write(\"/tmp/other\", b\"x\"); } }\n"
    "pub mod sys {\n  #[cfg(unix)] pub use crate::a::put;\n  #[cfg(not(unix))] pub use crate::b::put;\n}\n"
    "use crate::sys::put;\npub fn probe() { put(\"z\"); }\n" % ALLOWED
)
BODIES = {
    "rust": {
        "b1union":   _rust(FS, ENV),
        "b2order":   _rust(ENV, FS),
        "b3nohedge": _rust(FS, ENV),
        "b4surface": _dbl(_RUST_TWO_LIT),
        "b5agree":   _rust(FS, FS),
        "b6single":  _dbl("pub mod sys {\n  pub use %s as put;\n}\n%s" % (FS, _RUST_CALL)),
        # A LOCAL arm beside a std one. `crate::loc::put` sets an env var; the std arm writes a file.
        "b7mixed":     _dbl(_RUST_MIXED % (FS, "crate::loc::put")),
        "b8mixedrev":  _dbl(_RUST_MIXED % ("crate::loc::put", FS)),
        "b9mixedallow":_dbl(_RUST_MIXED % (FS, "crate::loc::put")),
    },
}

_SW_HELPERS = (
    'import Foundation\n'
    'enum FsImpl { static func act() { try? "x".write(toFile: "%s", atomically: true, encoding: .utf8) } }\n'
    'enum EnvImpl { static func act() { setenv("CANDOR_PART89", "1", 1) } }\n' % ALLOWED
)
def _swift_mixed(first, second):
    """One arm a FRAMEWORK type, the other a project-declared enum — the shape both engines' narrowings
    exclude, and the shape real code writes (`Color = NSColor | UIColor`)."""
    return (_SW_HELPERS
            + "#if os(macOS)\ntypealias Impl = %s\n#else\ntypealias Impl = %s\n#endif\n" % (first, second)
            + "public func probe() { Impl.act() }\n")


def _swift(first, second=None):
    if second is None:
        alias = "typealias Impl = %s\n" % first
    else:
        alias = "#if os(macOS)\ntypealias Impl = %s\n#else\ntypealias Impl = %s\n#endif\n" % (first, second)
    return _SW_HELPERS + alias + "public func probe() { Impl.act() }\n"

BODIES["swift"] = {
    "b1union":   _swift("FsImpl", "EnvImpl"),
    "b2order":   _swift("EnvImpl", "FsImpl"),
    "b3nohedge": _swift("FsImpl", "EnvImpl"),
    "b4surface": (
        'import Foundation\n'
        'enum FsA { static func act() { try? "x".write(toFile: "%s", atomically: true, encoding: .utf8) } }\n'
        'enum FsB { static func act() { try? "x".write(toFile: "/tmp/other", atomically: true, encoding: .utf8) } }\n'
        '#if os(macOS)\ntypealias Impl = FsA\n#else\ntypealias Impl = FsB\n#endif\n'
        'public func probe() { Impl.act() }\n' % ALLOWED
    ),
    "b5agree":   _swift("FsImpl", "FsImpl"),
    "b6single":  _swift("FsImpl"),
    # A PROJECT-DECLARED enum beside a FRAMEWORK type. swift's `declaredTypes` filter makes only the
    # project arm eligible, so the set falls back to last-writer-wins and the framework arm decides.
    "b7mixed":      _swift_mixed("FileManager", "EnvImpl"),
    "b8mixedrev":   _swift_mixed("EnvImpl", "FileManager"),
    "b9mixedallow": _swift_mixed("FileManager", "FsImpl"),
}

POLICIES = {
    # SCOPED to `probe` on purpose. The swift fixture's own helper enums carry Fs and Env as units of
    # their own, so a whole-scan `deny Env` is 1 for every arm and discriminates nothing. `probe` is the
    # only name with that prefix in either tree — asserted below, because a scoped rule's function match
    # is a PREFIX match and a silent prefix collision manufactures a pass-looking gate.
    "denyenv": "deny Env probe\n",
    "denyunk": "deny Unknown probe\n",
    # SCOPED to `probe`. Unscoped, `b4surface`'s OWN second arm (`pub mod b { … write("/tmp/other") }`)
    # is a unit in the scan and violates on its own, so the cell scored "ok" on a tree containing NO
    # conditional binding at all — measured by replacing the binding with an unconditional `use` and
    # watching it still pass. The arm could not fail for the reason it names; `run.sh`'s own DIVERGE text
    # ("a ✘ on b4surface is one arm's literal certifying for both") described an unreachable outcome.
    "allowfs": "allow Fs in probe %s\n" % ALLOWED,
}


def _swift_tree(d, body):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "cases.swift"), "w") as f:
        f.write("// GENERATED by gen_binding_union.py -- do not edit.\n" + body + "\n")


# ── THE FAULT, for conformance/probe_check.py ───────────────────────────────────────────────────────
# Corrupts the b1union FIXTURE — writes b5agree's body (arms that classify ALIKE, so no Env anywhere)
# into b1union's cell. b1union must FAIL under `deny Env probe`; with the agreeing body in its tree it
# CANNOT, so the verdict must go red. A run that still reports b1union green is reading something other
# than the fixture it names.
#
# **THE FIRST FAULT HERE WAS VACUOUS AND IS RECORDED RATHER THAN QUIETLY REPLACED.** It wrote b1union's
# body into b2order's cell — and b1union and b2order are the SAME program with the arms swapped, both
# expected rc=1, so the substitution changed no verdict and the fault run came back OK. A fault that
# cannot redden the thing it corrupts proves nothing, which is the exact failure this hook exists to
# catch, one level up. Caught by running it, not by reading it.
FAULT = bool(os.environ.get("CANDOR_PROBE_FAULT"))

# ── THE MIXED ARMS ARE EXPECTED RED, AND NAMED TO THEIR ROWS ────────────────────────────────────────
# They are committed BEFORE the engine fixes on purpose: a part that arrives after a fix cannot falsify
# it, and these three are the falsification arm for R429 and R438. But a suite that simply goes red
# blocks every other repo, and `main` red for days teaches people to ignore it — PART 88 was held out of
# `run.sh` for exactly that reason.
#
# So they run, they print, and they do not fail the suite WHILE their row is open. The asymmetry that
# keeps this from rotting into permanent tolerance: **an xfail arm that starts PASSING is a FAILURE.**
# The row is then fixed and the xfail is a stale claim about the engine — which is the same defect class
# as a stale comment, and the suite says so rather than quietly going green.
# KEYED BY (arm, ENGINE), not by arm. The first cut keyed on the arm alone and the mechanism caught it
# on its first run: swift PASSES `b7mixed` — it resolves that arm order correctly — so a per-arm
# expectation was a false claim about swift while being true of rust. An xfail is an assertion about a
# specific engine's specific defect; anything coarser tolerates a passing engine.
XFAIL = {
    ("b7mixed",      "rust"):  "R438 — rust picks the external arm and publishes its literal",
    ("b8mixedrev",   "rust"):  "R438 — rust picks in BOTH orders",
    ("b8mixedrev",   "swift"): "R429 — swift is ORDER-DEPENDENT on a mixed arm set",
    ("b9mixedallow", "rust"):  "R438 — the picked arm's literal CERTIFIES",
    ("b9mixedallow", "swift"): "R429 — the picked arm's literal CERTIFIES",
}


def render(ws):
    for arm, _pol, _rc, _why, skip in ARMS:
        cell = f"{EFF['id']}_{arm}"
        src = "b5agree" if (FAULT and arm == "b1union") else arm
        if "rust" not in skip:
            gm._rust_tree(os.path.join(ws, "rust", cell), BODIES["rust"][src])
        if "swift" not in skip:
            _swift_tree(os.path.join(ws, "swift", cell), BODIES["swift"][src])


def main():
    import tempfile
    ws = tempfile.mkdtemp(prefix="candor-bindunion-")
    pols = {}
    for k, text in POLICIES.items():
        p = os.path.join(ws, f"{k}.policy")
        with open(p, "w") as f:
            f.write(text)
        pols[k] = p

    print("=" * 100)
    print("CONDITIONAL-BINDING UNION differential ⟨0.38⟩ — a binding's arms union, exactly as a "
          "definition's do")
    print("  property: b1union/b2order must FAIL under `deny Env probe` (a PICK or a HEDGE is silent);")
    print("            b3nohedge/b5agree/b6single must PASS (no withdrawal, no manufacture, no over-mask);")
    print("            b4surface must FAIL under `allow Fs` (no arm's literal may certify)")
    print("=" * 100)

    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — b1union's cell is being written with b5agree's body "
              "(arms that classify alike, so no Env anywhere). The arm that MUST fail under `deny Env` "
              "now cannot, and this run's verdict MUST go red. A clean run must never print this line.")
    render(ws)

    available = []
    for eng in gm.ENGINES:
        if eng.name in SKIP:
            continue
        eng.prepare(ws)
        if eng.ok:
            available.append(eng)
        else:
            print(f"  {eng.name:6s} not available — skipped LOUDLY: {eng.err}")
    if not available:
        print("BINDING-UNION: no engine available")
        return 2

    fails, xfails, fixed = [], [], []
    print(f"\n{'arm':11s}{'policy':11s} " + " ".join(f"{e.name:14s}" for e in available))
    print("-" * 78)
    for arm, polkey, want, why, _skip in ARMS:
        row = f"{arm:11s}{polkey:11s} "
        for eng in available:
            rc = eng.gate(ws, EFF, arm, pols[polkey])
            ok = (rc != 0) if want else (rc == 0)
            xf = XFAIL.get((arm, eng.name))
            if xf and not ok:
                row += f"{'rc=' + str(rc) + ' xfail':14s} "
                xfails.append((arm, eng.name, xf))
            elif xf and ok:
                row += f"{'rc=' + str(rc) + ' FIXED!':14s} "
                fixed.append((arm, eng.name, xf))
            else:
                row += f"{('rc=' + str(rc) + (' ok' if ok else ' ✘')):14s} "
                if not ok:
                    fails.append((arm, eng.name, rc, why))
        print(row)

    print()
    for arm, eng, rc, why in fails:
        want = dict((a, w) for a, _p, w, _y, _s in ARMS)[arm]
        verb = "did NOT answer with the union" if want else "over-reported on a shape that must stay quiet"
        print(f"  ✘ {eng}/{arm}: {verb} (rc={rc}) — {why}")
    for eng in SKIP:
        print(f"  •   {eng}: no mutually-exclusive configuration construct — DECLARED exclusion, not a gap")
    for arm, eng, xf in xfails:
        print(f"  ·   {eng}/{arm}: EXPECTED RED — {xf}")
    for arm, eng, xf in fixed:
        print(f"  ✘ {eng}/{arm}: XFAIL ARM PASSED. The row is fixed and this expectation is now a STALE "
              f"CLAIM ABOUT THE ENGINE — retire it here and close {xf}")
    if fixed:
        print(f"\nBINDING-UNION: {len(fixed)} expected-red cell(s) now PASS — retire the xfail")
        return 1
    if fails:
        print(f"\nBINDING-UNION: {len(fails)} cell(s) wrong — see SOUNDNESS R287/R429 and the "
              f"2026-09-12 ruling")
        return 1
    if xfails:
        # NOT "OK — every engine answers with the union". Five cells are red by expectation, and a
        # summary that claims the property while its own table shows otherwise is the false-green this
        # suite exists to prevent — one level up, in the sentence rather than the cell.
        print(f"\nBINDING-UNION: OK for the ALL-PROJECT-DECLARED case, with {len(xfails)} cell(s) "
              f"EXPECTED RED on the MIXED arm set (R429 swift, R438 rust — named above). The union "
              f"property is NOT established for a mixed set on either engine.")
    else:
        print("\nBINDING-UNION: OK — every engine answers a conditional binding with the union of its "
              "arms, in either written order, without withdrawing to Unknown and without certifying off "
              "one arm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
