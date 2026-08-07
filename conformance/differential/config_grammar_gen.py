#!/usr/bin/env python3
"""Generate `.candor/config` files across the grammar's whole surface.

Every config defect found by hand today — a NO-BREAK SPACE hiding a key, Unicode digits normalising as
a version, a deps path split on the wrong whitespace, a trailing separator surviving a trim, an
unreadable line hidden by a qualified pin — is an instance of ONE property: the five engines must read
the same config the same way. They were found one at a time, by a human, over hours. This enumerates
the space instead.

No expected-value table, deliberately (the P1 split-invariance methodology): the assertion is that the
five engines AGREE, so a divergence is a finding without anyone having to be right in advance.
"""
import itertools, os, sys

SEPS = [
    ("sp",      " "),
    ("tab",     "\t"),
    ("2sp",     "  "),
    ("nbsp",    " "),
    ("emsp",    " "),
    ("sp+nbsp", "  "),
    ("nbsp+sp", "  "),
    ("thin",    " "),
    ("ideo",    "　"),
]

VERSIONS = [
    ("match",       "0.27.0"),
    ("match-v",     "v0.27.0"),
    ("match-2part", "0.27"),
    ("mismatch",    "0.26.0"),
    ("junk",        "latest"),
    ("vv",          "vv0.27.0"),
    ("arabic",      "٣.٣"),
    ("superscript", "².0"),
    ("fraction",    "½.0"),
    ("fullwidth",   "０.２７.０"),
    ("leading-zero","01.02.03"),
    ("plus",        "+0.27.0"),
    ("hex",         "0x1.0"),
    ("empty-part",  "0..0"),
    ("four-part",   "0.27.0.1"),
    ("long",        "0.27.00000000000000000000"),
]

QUALIFIERS = ["bare", "self", "other"]   # resolved per engine in configs()

TRAILERS = [
    ("none",     ""),
    ("comment",  "  # pinned with the baseline"),
    ("trail-sp", "   "),
    ("trail-nbsp", " "),
    ("crlf",     "\r"),
]

def configs(self_impl):
    """(label, text) for every combination worth running."""
    out = []
    # "other" must never BE the engine under test, or the row tests the self case and every engine
    # legitimately answers differently — the same convention conformance PART 33 uses.
    other = "agents" if self_impl == "java" else "java"
    for (sl, sep), (vl, ver), ql, (tl, trail) in itertools.product(SEPS, VERSIONS, QUALIFIERS, TRAILERS):
        if ql == "bare":
            line = f"engine{sep}{ver}{trail}"
        elif ql == "self":
            line = f"engine{sep}{self_impl}{sep}{ver}{trail}"
        else:
            line = f"engine{sep}{other}{sep}{ver}{trail}"
        out.append((f"engine/{sl}/{vl}/{ql}/{tl}", line + "\n"))
    # …and the PAIRED shape, which is where today's Unicode-digit fail-open lived: only a junk line
    # BESIDE a qualified pin that applies reveals it.
    for (vl, ver) in VERSIONS:
        for (sl, sep) in SEPS:
            out.append((f"paired/{sl}/{vl}",
                        f"engine{sep}{ver}\nengine {self_impl} 0.27.0\n"))
    # other keys, same separator surface — a fix to one key's tokenisation must not move another's
    for key, val in [("policy", "/tmp/cfgfuzz/empty.policy"), ("baseline", "/tmp/cfgfuzz/nope.json"),
                     ("deps", "/tmp/cfgfuzz/nodep.json"), ("unknown-ratchet", "off"),
                     ("no-such-key", "x")]:
        for (sl, sep) in SEPS:
            for (tl, trail) in TRAILERS:
                out.append((f"{key}/{sl}/{tl}", f"{key}{sep}{val}{trail}\n"))
    # structural shapes
    out += [
        ("empty",            ""),
        ("blank-lines",      "\n\n\n"),
        ("comment-only",     "# nothing here\n"),
        ("bom",              "﻿engine 0.27.0\n"),
        ("dup-same",         "engine 0.27.0\nengine 0.27.0\n"),
        ("dup-differ",       "engine 0.27.0\nengine 0.26.0\n"),
        ("bare-key",         "engine\n"),
        ("bare-key-sp",      "engine   \n"),
        ("no-trailing-nl",   "engine 0.27.0"),
        ("crlf-file",        "engine 0.27.0\r\n"),
        ("cr-only",          "engine 0.27.0\r"),
        ("leading-ws",       "   engine 0.27.0\n"),
        ("leading-tab",      "\tengine 0.27.0\n"),
        ("inline-comment",   "engine 0.27.0 # ok\n"),
        ("hash-no-space",    "engine 0.27.0#ok\n"),
        ("upper-key",        "ENGINE 0.27.0\n"),
        ("mixed-key",        "EnGiNe 0.27.0\n"),
    ]
    return out

if __name__ == "__main__":
    impl = sys.argv[1]
    for label, text in configs(impl):
        print(repr(label), len(text))
