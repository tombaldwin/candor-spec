#!/usr/bin/env python3
"""Generate POLICY files across the §6.2 DSL's surface.

The config-grammar differential found its defects one spelling at a time until it was enumerated. The
POLICY DSL is the bigger hand-parsed grammar — five independent parsers, one contract — and it decides
gate verdicts directly, so a divergence there is a gate that fires in one engine and not another.

No expected-value table: the assertion is that the five engines AGREE on the exit code.
"""
import itertools

EFFECTS = ["Net", "Fs", "Exec", "Env", "Db", "Unknown", "Clock", "Rand", "Log", "Ipc", "Llm", "Clipboard"]

RULES = []
# well-formed shapes
for e in ["Net", "Fs", "Unknown"]:
    RULES += [
        (f"deny-{e}",            f"deny {e}"),
        (f"deny-{e}-scope",      f"deny {e} app"),
        (f"deny-{e}-nomatch",    f"deny {e} zzz_no_such_layer"),
    ]
RULES += [
    ("pure-scope",           "pure app"),
    ("pure-nomatch",         "pure zzz_no_such_layer"),
    ("deny-two",             "deny Net Fs"),
    ("deny-two-scope",       "deny Net Fs app"),
    ("allow-host",           "deny Net\nallow Net example.com"),
    ("forbid",               "forbid app -> dep"),
]
# malformed / edge shapes — every engine must answer the SAME way, whatever that answer is
RULES += [
    ("empty",                ""),
    ("blank",                "\n\n"),
    ("comment-only",         "# nothing\n"),
    ("unknown-verb",         "denny Net"),
    ("unknown-effect",       "deny Nett"),
    ("unknown-effect-2",     "deny Net Fss"),
    ("bare-deny",            "deny"),
    ("bare-pure",            "pure"),
    ("case-verb",            "DENY Net"),
    ("case-effect",          "deny NET"),
    ("case-effect-lower",    "deny net"),
    ("leading-ws",           "   deny Net"),
    ("tab-sep",              "deny\tNet"),
    ("nbsp-sep",             "deny Net"),
    ("emsp-sep",             "deny Net"),
    ("trailing-ws",          "deny Net   "),
    ("trailing-nbsp",        "deny Net "),
    ("crlf",                 "deny Net\r\n"),
    ("cr-only",              "deny Net\r"),
    ("no-final-nl",          "deny Net"),
    ("bom",                  "﻿deny Net"),
    ("inline-comment",       "deny Net  # why"),
    ("hash-no-space",        "deny Net#why"),
    ("dup-identical",        "deny Net\ndeny Net"),
    ("dup-widening",         "deny Net\ndeny Net Fs"),
    ("filter-ok",            "deny Unknown[dispatch]"),
    ("filter-typo",          "deny Unknown[dispatc]"),
    ("filter-mixed",         "deny Unknown[dispatch,nativ]"),
    ("filter-empty",         "deny Unknown[]"),
    ("filter-unclosed",      "deny Unknown[dispatch"),
    ("filter-spaces",        "deny Unknown[ dispatch ]"),
    ("net-class-ok",         "deny Net[unknown-host]"),
    ("net-class-typo",       "deny Net[unknown-hosts]"),
    ("two-filters",          "deny Net[unknown-host] Fs app"),
    ("scope-dots",           "deny Net a.b.c"),
    ("scope-glob",           "deny Net app.*"),
    ("scope-leading-dot",    "deny Net .app"),
    ("extra-tokens",         "deny Net app extra"),
    ("only-scope",           "deny app"),
    ("semicolon",            "deny Net;"),
    ("two-on-one-line",      "deny Net; deny Fs"),
    ("allow-no-deny",        "allow Net example.com"),
    ("allow-bare",           "allow Net"),
    ("forbid-no-arrow",      "forbid app dep"),
    ("forbid-bad-arrow",     "forbid app --> dep"),
    ("very-long-effect",     "deny " + "N"*200),
]

def policies():
    return RULES

if __name__ == "__main__":
    for n, t in policies():
        print(n, repr(t))
