#!/usr/bin/env python3
"""DOES EACH ENGINE'S AGENTS.md AGREE WITH WHAT THE ENGINE EMITS?

There is already an AGENTS.md drift gate (`check_agents_drift.py`). It pins the spec version the doc
teaches against SPEC.md, and that the envelope example parses as the §2 shape. Both compare A DOCUMENT
TO A DOCUMENT. Neither ever asks a binary anything, so a claim that is stale in the file is stale in the
embedded copy too, and the two agree with each other perfectly while both being wrong.

That gap is real, and it was found by hand on 2026-08-05: candor-swift's AGENTS.md described the
`privacy/1` extension in two places, while the engine has emitted `extensions: ["privacy/2"]` since the
sensor vocabulary went from six to eighteen.

WHAT THIS CHECKS. Each engine is run on a tiny fixture and its own report is read. Every fact below is
one the engine STATES about itself, so there is no interpretation in the middle:

    spec version   the envelope's `candor.spec`  vs the version AGENTS.md teaches
    extensions     the envelope's `extensions`   vs the `name/version` strings AGENTS.md names
    resolves       the envelope's `resolves`     vs whether AGENTS.md mentions the surface at all

A mismatch on the first two FAILS (exit 1): the contract is telling its only consumer something the
engine contradicts. The third is REPORTED: a resolved surface the contract never mentions under-serves
an agent rather than misleading one.

──────────────────────────────────────────────────────────────────────────────────────────────────────
A REJECTED DESIGN, KEPT BECAUSE THE FAILURE IS THE USEFUL PART.

This script first compared the FLAGS AGENTS.md names against the flags each engine accepts. It reported
20 phantom flags across five engines. Every refinement cut the count, and none of it was signal:

  20 → 14   comparing against the top-level `--help` is a PROXY, not the claim. Most were correct flags
            on query SUBCOMMANDS, which a top-level help text has no reason to list.
  14 →  2   AGENTS.md contains OTHER TOOLS' command lines. `git clone --depth 1 …/candor-swift` and
            `git fetch --tags` both contain the engine's name — in a URL and in a path — so `--depth`
            and `--tags` were reported as contract defects. They are git's.
   2 →  0   the last two were java's `--strict` and `--include-unknown`, both ACCEPTED: the engine was
            failing on a missing report file, and the learned unknown-flag marker matched that too.

Zero true positives, on a tree where two real doc defects existed and had just been found by reading.
The probe was wrong: AGENTS.md legitimately spells CLIs several ways, mixes in other tools, and
documents subcommand flags whose rejection is indistinguishable from any other error. A check that
confidently names GIT'S flags as candor's contract defects is worse than no check — the reader who
dismisses those two also dismisses the real one sitting beside them.

The emitted-fact probe above is the same idea aimed at a target that cannot be misread: a value the
engine puts in its own report.
──────────────────────────────────────────────────────────────────────────────────────────────────────

    python3 scripts/check_agents_vs_engine.py

Exit 0 = in step · 1 = the contract contradicts an engine · 2 = no engine could be run (never a pass).
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SIBS = pathlib.Path(__file__).resolve().parent.parent.parent

FIXTURES = {
    "candor-rust": ("src/lib.rs",
                    'use std::fs;\npub fn w() { let _ = fs::write("/tmp/a", "b"); }\n'),
    "candor-ts": ("src/a.ts",
                  'import * as fs from "node:fs";\n'
                  'export function w(): void { fs.writeFileSync("/tmp/a", "b"); }\n'),
    # The swift fixture ALSO touches a privacy sensor, deliberately. Without it the probe emitted no
    # `extensions` at all, so the extensions row said nothing — and the defect this whole script exists
    # to catch (`privacy/1` in the contract, `privacy/2` from the engine) would have sailed through a
    # green run. A check that cannot fail on its own motivating example is not a check.
    "candor-swift": ("Sources/App/main.swift",
                     'import Foundation\n'
                     'import Contacts\n'
                     'try? "x".write(toFile: "/tmp/a", atomically: true, encoding: .utf8)\n'
                     'let store = CNContactStore()\n'
                     '_ = try? store.unifiedContacts(matching: '
                     'CNContact.predicateForContacts(matchingName: "a"), keysToFetch: [])\n'),
}


def run(cmd, cwd=None):
    """stdout ONLY. Merging stderr broke the parse: every engine writes progress and coverage notes
    there, and `text.find("{")` then started at a brace inside a warning line instead of at the
    envelope — which showed up as two engines silently 'not built here'."""
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              text=True, timeout=180, cwd=cwd).stdout or ""
    except Exception:
        return ""


def envdir(var, default):
    return pathlib.Path(os.environ.get(var, str(SIBS / default)))


def _json(text):
    i = text.find("{")
    if i < 0:
        return None
    try:
        return json.loads(text[i:])
    except Exception:
        return None


def scan_envelope(engine, ws):
    """Run one engine on a throwaway fixture and return its report envelope, or None."""
    if engine not in FIXTURES:
        return None
    rel, body = FIXTURES[engine]
    root = ws / engine
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(body)
    if engine == "candor-rust":
        (root / "Cargo.toml").write_text('[package]\nname = "probe"\nversion = "0.0.0"\nedition = "2021"\n')
        for r in ("target/debug/candor-scan", "target/release/candor-scan"):
            b = envdir("CANDOR", "candor-rust") / r
            if b.exists():
                return _json(run([str(b), str(root), "--json"]))
    elif engine == "candor-ts":
        (root / "package.json").write_text('{"name":"probe","version":"0.0.0"}\n')
        (root / "tsconfig.json").write_text('{"include":["src"]}\n')
        s = envdir("CANDOR_TS", "candor-ts") / "scan.mjs"
        if s.exists():
            return _json(run(["node", str(s), str(root), "--json"]))
    elif engine == "candor-swift":
        (root / "Package.swift").write_text(
            '// swift-tools-version:5.9\nimport PackageDescription\n'
            'let package = Package(name: "App", targets: [.executableTarget(name: "App")])\n')
        for r in (".build/debug/candor-swift", ".build/release/candor-swift"):
            b = envdir("CANDOR_SWIFT", "candor-swift") / r
            if b.exists():
                return _json(run([str(b), str(root), "--json"]))
    return None


def main():
    ws = pathlib.Path(tempfile.mkdtemp(prefix="agents-vs-engine-"))
    errors, ran, skipped, notes = [], [], [], []
    try:
        print("AGENTS.md vs WHAT THE ENGINE EMITS\n")
        for engine in ("candor-rust", "candor-ts", "candor-swift"):
            doc_path = SIBS / engine / "AGENTS.md"
            env = scan_envelope(engine, ws)
            if not env or not doc_path.exists():
                skipped.append(engine)
                continue
            doc = doc_path.read_text(errors="replace")
            ran.append(engine)
            print(f"  {engine}")

            spec = (env.get("candor") or env.get("meta") or {}).get("spec")
            if spec:
                # IN A SPEC CONTEXT, not anywhere. A bare `\b0.27\b` search was VACUOUS: every AGENTS.md
                # carries a build version like `candor-swift-0.27.0`, whose `0.27` satisfies the word
                # boundary, so the row could never fail no matter how stale the spec claim was. The three
                # forms below are how the contracts actually write it: `"spec": "0.27"`, `spec 0.27`, `⟨0.27⟩`.
                v = re.escape(str(spec))
                if re.search(rf'"spec"\s*:\s*"{v}"|spec\s+{v}\b|⟨{v}⟩', doc):
                    print(f"    ✔ spec {spec} — the contract teaches this version")
                else:
                    errors.append(f"{engine}: emits spec {spec}, and AGENTS.md never mentions it")
                    print(f"    ✘ emits spec {spec}, which AGENTS.md never mentions")

            exts = env.get("extensions") or []
            for e in exts:
                if e in doc:
                    print(f"    ✔ extensions {e!r} — named by the contract")
                else:
                    base = e.split("/")[0]
                    stale = sorted(set(re.findall(re.escape(base) + r"/\d+", doc)))
                    detail = f" (it names {', '.join(stale)})" if stale else ""
                    errors.append(f"{engine}: emits extensions {e!r}, AGENTS.md does not name it{detail}")
                    print(f"    ✘ emits {e!r}, and the contract does not name it{detail}")
            if not exts:
                print("    · no extensions active on the probe fixture — this row says nothing")

            res = env.get("resolves") or []
            missing = [r for r in res if r not in doc]
            if missing:
                notes.append(f"{engine}: resolves {missing}, unmentioned in AGENTS.md")
                print(f"    · resolves {res}; the contract never mentions {missing} "
                      "(under-serves, does not mislead)")
            elif res:
                print(f"    ✔ resolves {res} — all mentioned")
            print()
    finally:
        shutil.rmtree(ws, ignore_errors=True)

    if not ran:
        print("check_agents_vs_engine: NO engine could be run — build them first. An empty comparison "
              "must never read as agreement.", file=sys.stderr)
        return 2
    if skipped:
        print(f"  NOT CHECKED (reported, never implied): {', '.join(skipped)} — not built here.")
    print("  candor-java and candor-agents are not probed: neither writes a §2 envelope from the tiny\n"
          "  fixture shape above without a compile step. Stated rather than left as an empty row.")
    if errors:
        print("\n\033[31mcheck_agents_vs_engine: the contract contradicts an engine\033[0m")
        for e in errors:
            print(f"  ✘ {e}")
        return 1
    print(f"\n\033[32mcheck_agents_vs_engine: OK — {len(ran)} engine(s) agree with their contract\033[0m")
    for n in notes:
        print(f"  · {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
