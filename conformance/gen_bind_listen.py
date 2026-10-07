#!/usr/bin/env python3
"""
PART 96 — A BIND/LISTEN ADDRESS IS NOT A DESTINATION; AN ACCEPT IS AN UNSEEN ONE (FOUR-WAY, SPEC §2 ⟨0.40⟩).

SOUNDNESS R817. Until ⟨0.40⟩ the family cited "⟨0.29⟩'s rule that a listen address must never enter
`hosts`" — in candor-swift's source and in R809 — and SPEC had no such sentence (`grep -i listen SPEC.md`
returned 0). With no clause and no part, the engines drifted in BOTH directions, and this part measured
the drift on its first execution:

  * a FABRICATION: an engine that captures the literal of a bind/listen as though it were a destination
    publishes the process's OWN address in `hosts`, and `allow Net <that address>` is then an allow over
    a destination the program never reaches (R809, closed in rust-deep; java publishes it today);
  * a SILENCE: a unit that ACCEPTS talks to peers no literal can name, so a benign sibling literal must
    not certify it. Where an engine reads an accept as an ordinary use-verb, `allow Net <benign>` exits 0
    over a server writing to whoever connects (rust; ts's node `listen`, R781's listen half);
  * an OVER-CHARGE: an engine that hedges EVERY bind marks an ephemeral client socket incomplete, so a
    UDP client sending to one literal destination can never be certified (java).

THE ARMS, one package per (engine, arm), one function `f` in each:

  a_litbind    a bind to a LITERAL local address, alone.  `allow Net 10.0.0.5` MUST exit 1, AND no `hosts`
               entry of `f` may name 10.0.0.5. Both halves are asserted separately: an engine that
               publishes the bind address AND marks the surface incomplete fails closed on the gate and
               still FABRICATES a destination on the wire, which a chained consumer or `diff` would read.
  b_rtbind     a bind over an already-RESOLVED runtime address (rust `SocketAddr`, java `SocketAddress`, swift
               NIO `bind(to: SocketAddress)`, ts port-only `bind(0)`) that never accepts, beside a benign
               literal connect. `allow Net ok.example` MUST exit 0 — the address is where the process
               listens and nothing is resolved. (CONTROL for the over-charge; one variable from e_rtname.)
  c_accept     an ACCEPT (rust `accept`, java `ServerSocket.accept`, node `server.listen`, swift
               `NWListener`) beside the same benign literal connect. `allow Net ok.example` MUST exit 1:
               the peers are a destination no literal can name, the SEMANTICS §6 `masked_Net` case.
  d_ephemeral  an ephemeral bind (port 0, no address) plus a send to a LITERAL destination.
               `allow Net 10.9.9.9` MUST exit 0 — the outbound locator is carried by the send itself, so
               the bind marks nothing. (CONTROL for the over-charge.)

  e_rtname     the same bind handed a runtime STRING (`UdpSocket::bind(h)`, `new InetSocketAddress(h, 0)`,
               `dgram.bind(0, h)`, NIO `bind(host: h)`). The engine's bind RESOLVES `h` — a DNS reach of a
               computed name, the explicit resolver's exfil channel by another spelling — so `allow Net
               ok.example` MUST exit 1 (SOUNDNESS R949).
  f_rtresolve  an explicit resolver over a runtime name (`to_socket_addrs`, `getByName`, `dns.lookup`,
               `getaddrinfo`) beside the benign literal: exit 1. The rust body is the UFCS/`&str` spelling;
               the tuple receiver `(h, 80).to_socket_addrs()` is a separate rust silence (R950).
  g_litdiscard a LITERAL name resolved and the result discarded, beside the benign literal: the name is a
               reach and enters `hosts`, so `allow Net ok.example` exits 1 and `hosts` names it.

FIXTURE REACH IS CHECKED BEFORE ANY ARM IS SCORED, and a reach failure is a HARNESS FAULT, never an xfail:
every cell must (1) produce a report, (2) carry `f` with `Net` in `inferred`, and (3) where the arm has a
benign literal, carry that literal in `f`'s `hosts` — otherwise an exit 1 on c_accept could be the empty
surface failing, not the accept, and an exit 0 on b/d could not have happened at all. `deny Net` must also
exit 1 on every cell, so the gate is shown able to fail on the bytes it is scoring.

XFAILs are keyed (arm, engine) and cite R817. A PASSING xfail is a FAILURE here — the engine that ports
the clause reddens this part and retires its own line in the same commit.

CALIBRATED: CANDOR_PROBE_FAULT=1 writes the c_accept AND f_rtresolve cells with the benign connect ALONE
(`z_benign` — no accept, no resolution), so the arms that MUST fail now cannot: java and swift go red on
c_accept (rust and ts are xfailed there and cannot mask it), and all four go red on f_rtresolve, which every
engine passes today — so the fault reaches every engine, not only the two right about accept. The first fault tried — b_rtbind's body — did NOT
go red, because the two engines conformant on c_accept are exactly the two that over-charge a runtime bind:
a fault built from a sibling arm's body is only a fault for an engine that gets that sibling right.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_differential as gd  # noqa: E402  -- the shared tree writers and engine paths (one owner)

FAULT = os.environ.get("CANDOR_PROBE_FAULT")
DUMP = os.environ.get("CANDOR_PART96_DUMP")   # print each cell's `f` row — for porting, not scoring

# Each fragment must resolve verbatim in SPEC.md (clause_check.py).
SPEC_CLAUSES = [
    ("§2 ⟨0.40⟩", "A BIND OR LISTEN ADDRESS IS WHERE THE PROCESS LISTENS, NEVER A DESTINATION IT REACHES."),
    ("§2 ⟨0.40⟩", "It MUST NOT enter `hosts`"),
    ("§2 ⟨0.40⟩", "A bind marks nothing."),
    ("§2 ⟨0.40⟩", "A UNIT THAT ACCEPTS A CONNECTION TALKS TO PEERS NO LITERAL CAN NAME"),
    ("§2 ⟨0.40⟩", "MUST put `Net` into the unit's `incomplete`, and `allow Net <host>` over that unit MUST fail closed"),
    ("§2 ⟨0.40⟩", "A RESOLUTION OF A COMPUTED NAME IS A `Net` REACH WHOSE LOCATOR IS THE NAME"),
    ("§2 ⟨0.40⟩", "or a bind handed a runtime name MUST put `Net` into the unit's `incomplete`"),
    ("§2 ⟨0.40⟩", "A LITERAL name resolved enters `hosts`"),
    ("§2 ⟨0.40⟩", "resolves nothing and **marks nothing**"),
]

BIND_LIT = "10.0.0.5"
BENIGN = "ok.example"
DEST = "10.9.9.9"
EVIL = "evil.example"

# arm -> (allow-policy literal, wanted exit, benign literal that must be in `hosts` or None, why)
ARMS = [
    ("a_litbind",    BIND_LIT, 1, None,   "a literal bind is not a destination: no `hosts` entry, and the empty surface fails closed"),
    ("b_rtbind",     BENIGN,   0, BENIGN, "CONTROL: a bind over an already-resolved address resolves nothing and marks nothing"),
    ("c_accept",     BENIGN,   1, BENIGN, "an accept talks to peers no literal names: `incomplete`, fail closed"),
    ("d_ephemeral",  DEST,     0, DEST,   "CONTROL: an ephemeral bind marks nothing; the send carries the locator"),
    ("e_rtname",     BENIGN,   1, BENIGN, "a bind handed a runtime NAME resolves it: a Net reach whose locator is unseen, `incomplete`"),
    ("f_rtresolve",  BENIGN,   1, BENIGN, "an explicit resolution of a runtime name is a Net reach whose locator is unseen, `incomplete`"),
    ("g_litdiscard", BENIGN,   1, BENIGN, "a literal name resolved and discarded is a reach: it enters `hosts`, so `allow` over the benign literal alone fails"),
]

# (arm, engine) -> why. Measured 2026-10-07 on candor-rust 708ce46, candor-java 6c000a4, candor-ts
# 503f449, candor-swift 519f62d (the engine trees' HEADs when this part was written).
XFAIL = {
    ("c_accept", "rust"):    "R817 — `accept`/`incoming` read as use-verbs; the benign literal certifies a server",
    ("c_accept", "ts"):      "R817 (R781's listen half) — node `listen` is not establishing; the benign literal certifies a server",
    ("a_litbind", "java"):   "R817 — the bind address is published into `hosts` (it does fail closed, via `incomplete`)",
    ("b_rtbind", "java"):    "R817 — every bind is hedged `incomplete`, so a bind over a resolved address is uncertifiable",
    ("d_ephemeral", "java"): "R817 — every bind is hedged `incomplete`, AND `send(DatagramPacket)` takes no locator from a literal packet address",
    # swift was reported conformant before this part ran; it is, on the Network.framework spellings
    # (`NWListener` fails closed, `requiredLocalEndpoint` is withheld). The NIO bootstraps are not.
    ("a_litbind", "swift"):  "R817 — NIO `bind(host:port:)` is read as a destination: hosts=['10.0.0.5:9'] COMPLETE, `allow Net 10.0.0.5` exits 0",
    # R949 — a bind or resolver handed a COMPUTED NAME resolves it, and that resolution is unseen.
    ("e_rtname", "rust"):    "R949 — `UdpSocket::bind(h: &str)` resolves `h` and marks nothing; the benign literal certifies it",
    ("e_rtname", "ts"):      "R949 — `dgram.bind(0, h)` resolves `h` and marks nothing; the benign literal certifies it",
    # Withdrawal of this line was briefed on the strength of a java measurement; swift's NIO `bind(to:)`
    # over a `SocketAddress` parameter was measured separately and is STILL marked (Bootstrap `bind` is
    # an establishing member whatever its argument), so it stays — the over-charge, fail-closed.
    ("b_rtbind", "swift"):   "R817 — NIO `bind(to: SocketAddress)` is establishing, so a bind over a resolved address is uncertifiable",
    # g_litdiscard: both FAIL CLOSED (rc 1) — the literal resolution is marked `incomplete` rather than
    # published, a precision gap (⟨0.37⟩ "DETERMINED" IS A PROPERTY OF THE VALUE), not a silence.
    ("g_litdiscard", "rust"): "R949 — a literal `to_socket_addrs` is marked `incomplete` instead of publishing the name (fails closed)",
    ("g_litdiscard", "java"): "R949 — a literal `getByName` resolved and discarded is marked `incomplete` instead of publishing the name (fails closed)",
}

TS_IMPORTS = ('import * as netm from "node:net";\nimport * as dgram from "node:dgram";\n'
              'import * as dns from "node:dns";\n')

BODIES = {
    "rust": {
        "z_benign":    'pub fn f() { let _ = std::net::TcpStream::connect("%s:80"); }' % BENIGN,
        "a_litbind":   'pub fn f() { let _ = std::net::UdpSocket::bind("%s:9"); }' % BIND_LIT,
        # A `SocketAddr` — already resolved, so nothing about this bind can reach a name server.
        "b_rtbind":    'pub fn f(a: std::net::SocketAddr) { let _ = std::net::TcpStream::connect("%s:80"); '
                       'let _ = std::net::UdpSocket::bind(a); }' % BENIGN,
        "c_accept":    'pub fn f(l: &std::net::TcpListener) { let _ = std::net::TcpStream::connect("%s:80"); '
                       'if let Ok((mut s, _)) = l.accept() { use std::io::Write; let _ = s.write_all(b"hi"); } }' % BENIGN,
        # `.unwrap()`, NOT `if let Ok(s) = …`: under that binder candor-scan loses the socket's type and the
        # `send_to` is never seen at all (SOUNDNESS R946 — a separate defect, found by this arm's reach
        # check on its first run), which would make this a test of the binder rather than of the bind.
        "d_ephemeral": 'pub fn f() { let s = std::net::UdpSocket::bind("0.0.0.0:0").unwrap(); '
                       'let _ = s.send_to(b"x", "%s:53"); }' % DEST,
        "e_rtname":    'pub fn f(h: &str) { let _ = std::net::TcpStream::connect("%s:80"); '
                       'let _ = std::net::UdpSocket::bind(h); }' % BENIGN,
        # UFCS over the `&str` parameter: the TUPLE receiver `(h, 80).to_socket_addrs()` is a separate rust
        # silence (SOUNDNESS R950), and this arm tests the resolution rule, not that spelling.
        "f_rtresolve": 'pub fn f(h: &str) { let _ = std::net::TcpStream::connect("%s:80"); '
                       'let _ = std::net::ToSocketAddrs::to_socket_addrs(&h); }' % BENIGN,
        "g_litdiscard": 'pub fn f() { let _ = std::net::TcpStream::connect("%s:80"); '
                        'let _ = std::net::ToSocketAddrs::to_socket_addrs(&"%s:80"); }' % (BENIGN, EVIL),
    },
    # BODY ONLY — gd.write_java_tree wraps it in `package q; public class E { … }`.
    "java": {
        "z_benign":    '  public static void f() throws Exception { new java.net.Socket("%s", 80).close(); }' % BENIGN,
        "a_litbind":   '  public static Object f() throws Exception { return new java.net.DatagramSocket('
                       'new java.net.InetSocketAddress("%s", 9)); }' % BIND_LIT,
        # A SocketAddress PARAMETER, not `new InetSocketAddress(h, 0)`: that constructor RESOLVES the runtime
        # name `h` — which is e_rtname's question, not this arm's. One variable per arm.
        "b_rtbind":    '  public static Object f(java.net.SocketAddress a) throws Exception { new java.net.Socket("%s", 80).close(); '
                       'return new java.net.DatagramSocket(a); }' % BENIGN,
        "c_accept":    '  public static void f(java.net.ServerSocket ss) throws Exception { '
                       'new java.net.Socket("%s", 80).close(); ss.accept().getOutputStream().write(1); }' % BENIGN,
        "d_ephemeral": '  public static void f() throws Exception { java.net.DatagramSocket s = new java.net.DatagramSocket(0); '
                       'byte[] b = new byte[1]; s.send(new java.net.DatagramPacket(b, 1, '
                       'java.net.InetAddress.getByName("%s"), 53)); }' % DEST,
        "e_rtname":    '  public static Object f(String h) throws Exception { new java.net.Socket("%s", 80).close(); '
                       'return new java.net.DatagramSocket(new java.net.InetSocketAddress(h, 0)); }' % BENIGN,
        "f_rtresolve": '  public static Object f(String h) throws Exception { new java.net.Socket("%s", 80).close(); '
                       'return java.net.InetAddress.getByName(h); }' % BENIGN,
        "g_litdiscard": '  public static void f() throws Exception { new java.net.Socket("%s", 80).close(); '
                        'java.net.InetAddress.getByName("%s"); }' % (BENIGN, EVIL),
    },
    "ts": {
        "z_benign":    'export function f(): void { netm.connect(80, "%s"); }' % BENIGN,
        "a_litbind":   'export function f(): void { dgram.createSocket("udp4").bind(9, "%s"); }' % BIND_LIT,
        # Port only: node binds the wildcard address and resolves nothing.
        "b_rtbind":    'export function f(): void { netm.connect(80, "%s"); '
                       'dgram.createSocket("udp4").bind(0); }' % BENIGN,
        "c_accept":    'export function f(): void { netm.connect(80, "%s"); '
                       'netm.createServer((s) => { s.write("hi"); }).listen(8080); }' % BENIGN,
        "d_ephemeral": 'export function f(): void { const s = dgram.createSocket("udp4"); s.bind(0); '
                       's.send(Buffer.from("x"), 53, "%s"); }' % DEST,
        "e_rtname":    'export function f(h: string): void { netm.connect(80, "%s"); '
                       'dgram.createSocket("udp4").bind(0, h); }' % BENIGN,
        "f_rtresolve": 'export function f(h: string): void { netm.connect(80, "%s"); '
                       'dns.lookup(h, () => {}); }' % BENIGN,
        "g_litdiscard": 'export function f(): void { netm.connect(80, "%s"); '
                        'dns.lookup("%s", () => {}); }' % (BENIGN, EVIL),
    },
    "swift": {
        "z_benign":    'import Network\npublic func f() { _ = NWConnection(host: "%s", port: 80, using: .tcp) }' % BENIGN,
        "a_litbind":   'import NIOCore\nimport NIOPosix\n'
                       'public func f(_ g: EventLoopGroup) { _ = DatagramBootstrap(group: g).bind(host: "%s", port: 9) }' % BIND_LIT,
        # NIO's `bind(to: SocketAddress)` — an already-resolved address.
        "b_rtbind":    'import Network\nimport NIOCore\nimport NIOPosix\n'
                       'public func f(_ g: EventLoopGroup, _ a: SocketAddress) { '
                       '_ = NWConnection(host: "%s", port: 80, using: .tcp); '
                       '_ = DatagramBootstrap(group: g).bind(to: a) }' % BENIGN,
        "c_accept":    'import Network\n'
                       'public func f() { _ = NWConnection(host: "%s", port: 80, using: .tcp); '
                       '_ = try? NWListener(using: .tcp, on: 8080) }' % BENIGN,
        "d_ephemeral": 'import Network\n'
                       'public func f() { let p = NWParameters.udp; '
                       'p.requiredLocalEndpoint = NWEndpoint.hostPort(host: "0.0.0.0", port: 0); '
                       'let c = NWConnection(host: "%s", port: 53, using: p); c.start(queue: .main) }' % DEST,
        "e_rtname":    'import Network\nimport NIOCore\nimport NIOPosix\n'
                       'public func f(_ g: EventLoopGroup, _ h: String) { '
                       '_ = NWConnection(host: "%s", port: 80, using: .tcp); '
                       '_ = DatagramBootstrap(group: g).bind(host: h, port: 0) }' % BENIGN,
        "f_rtresolve": 'import Foundation\nimport Network\n'
                       'public func f(_ h: String) { _ = NWConnection(host: "%s", port: 80, using: .tcp); '
                       'var r: UnsafeMutablePointer<addrinfo>? = nil; _ = getaddrinfo(h, "443", nil, &r) }' % BENIGN,
        "g_litdiscard": 'import Foundation\nimport Network\n'
                        'public func f() { _ = NWConnection(host: "%s", port: 80, using: .tcp); '
                        'var r: UnsafeMutablePointer<addrinfo>? = nil; _ = getaddrinfo("%s", "443", nil, &r) }' % (BENIGN, EVIL),
    },
}

SIDE = ("callgraph", "hierarchy", "calibrated", "layerreach", "locs", "gate", "refused")


def _leaf(name):
    return (name or "").replace("::", ".").split(".")[-1]


def _report(d, prefix):
    base = os.path.basename(prefix)
    for fn in sorted(os.listdir(d)):
        if fn.startswith(base) and fn.endswith(".json") and not any(("." + s + ".") in fn or fn.endswith("." + s + ".json") for s in SIDE):
            return os.path.join(d, fn)
    return None


class Eng:
    def __init__(self, name):
        self.name, self.ok, self.err = name, False, None
        if name == "rust":
            self.bin = os.environ.get("CANDOR_SCAN_BIN") or os.path.join(gd.CANDOR, "target", "debug", "candor-scan")
            self.ok = os.path.exists(self.bin)
            self.err = None if self.ok else "no candor-scan at %s" % self.bin
        elif name == "java":
            jar = os.environ.get("CANDOR_JAVA_JAR")
            if not jar:
                c = gd._glob(os.path.join(gd.CANDOR_JAVA, "build", "libs"), "-all.jar")
                jar = max(c, key=os.path.getmtime) if c else None
            self.jar = jar
            self.ok = bool(jar and os.path.exists(jar) and shutil.which("javac"))
            self.err = None if self.ok else "no candor-java jar / javac"
        elif name == "ts":
            self.mjs = os.path.join(gd.CANDOR_TS, "scan.mjs")
            self.ok = bool(shutil.which("node") and os.path.exists(self.mjs))
            self.err = None if self.ok else "no node / scan.mjs"
        else:
            self.bin = os.environ.get("CANDOR_SWIFT_BIN") or os.path.join(gd.CANDOR_SWIFT, ".build", "debug", "candor-swift")
            self.ok = os.path.exists(self.bin)
            self.err = None if self.ok else "no candor-swift at %s" % self.bin

    def render(self, d, body):
        if self.name == "rust":
            gd.write_rust_tree(d, "bindlisten", "gen_bind_listen.py", body)
            return d
        if self.name == "java":
            gd.write_java_tree(d, "gen_bind_listen.py", body)
            cls = os.path.join(d, "cls")
            os.makedirs(cls, exist_ok=True)
            c = gd.run(["javac", "-nowarn", "-d", cls, os.path.join(d, "q", "E.java")])
            if c.returncode != 0:
                raise RuntimeError("javac failed: " + c.stderr.decode()[:300])
            return cls
        if self.name == "ts":
            gd.write_ts_tree(d, "bindlisten", "gen_bind_listen.py", body, imports=TS_IMPORTS)
            return d
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "cases.swift")
        with open(p, "w") as f:
            f.write("// GENERATED by gen_bind_listen.py -- do not edit.\n" + body + "\n")
        return p

    def run(self, target, d, pol=None):
        """(rc, report_path_or_None). A gate run also writes its report, so one run answers both."""
        env = dict(os.environ)
        env.pop("CANDOR_DEPS", None)
        if pol:
            env["CANDOR_POLICY"] = pol
        else:
            env.pop("CANDOR_POLICY", None)
        out = os.path.join(d, "rep")
        for fn in os.listdir(d):
            if fn.startswith("rep") and fn.endswith(".json"):
                os.remove(os.path.join(d, fn))
        if self.name == "rust":
            argv = [self.bin, target, "--out", out]
        elif self.name == "java":
            argv = ["java", "-jar", self.jar, target, "--json", out + ".json"]
        elif self.name == "ts":
            argv = ["node", self.mjs, target, "--out", out]
        else:
            argv = [self.bin, target, "--out", out]
        r = gd.run(argv, env=env)
        return r.returncode, _report(d, "rep")


def main():
    print("=" * 100)
    print("BIND/LISTEN ⟨0.40⟩ — a bind/listen address is never a destination; an accept is an unseen one")
    print("  a_litbind   literal bind alone          `allow Net %s` -> 1, and no `hosts` entry names it" % BIND_LIT)
    print("  b_rtbind    runtime bind, no accept     `allow Net %s` -> 0 (CONTROL)" % BENIGN)
    print("  c_accept    accept beside benign lit    `allow Net %s` -> 1" % BENIGN)
    print("  d_ephemeral ephemeral bind + lit send   `allow Net %s` -> 0 (CONTROL)" % DEST)
    print("  reach       every cell: report produced, `f` carries Net, benign literal in `hosts`, `deny Net` -> 1")
    print("=" * 100)
    if FAULT:
        print("PROBE: CANDOR_PROBE_FAULT is set — the c_accept and f_rtresolve cells are written with the benign "
              "connect alone (no accept, no resolution). The arms that MUST fail now cannot; this run MUST go red.")
    ws = tempfile.mkdtemp(prefix="candor-part96-")
    fails, stale, harness, live = [], [], [], 0
    for name in ("rust", "java", "ts", "swift"):
        eng = Eng(name)
        if not eng.ok:
            print("  %-6s SKIPPED LOUDLY — %s" % (name, eng.err))
            continue
        live += 1
        for arm, lit, want, benign, why in ARMS:
            src = "z_benign" if (FAULT and arm in ("c_accept", "f_rtresolve")) else arm
            d = os.path.join(ws, name, arm)
            try:
                target = eng.render(d, BODIES[name][src])
            except RuntimeError as e:
                harness.append((arm, name, str(e)))
                print("  HARNESS %-11s %-6s %s" % (arm, name, e))
                continue
            pd = os.path.join(d, "pol")
            os.makedirs(pd, exist_ok=True)
            pdeny, pallow = os.path.join(pd, "deny.policy"), os.path.join(pd, "allow.policy")
            with open(pdeny, "w") as f:
                f.write("deny Net\n")
            with open(pallow, "w") as f:
                f.write("allow Net %s\n" % lit)
            # ---- REACH: the fixture reached the engine, or nothing below is evidence -------------------
            _rc0, rp = eng.run(target, d)
            row = None
            if rp:
                rows = {_leaf(r.get("fn")): r for r in (json.load(open(rp)).get("functions") or [])}
                row = rows.get("f")
            if DUMP:
                print("    dump %-11s %-6s %s" % (arm, name, json.dumps({k: (row or {}).get(k) for k in
                      ("inferred", "hosts", "incomplete", "netClass")})))
            reach = None
            if not rp:
                reach = "no report produced (rc=%d)" % _rc0
            elif row is None or "Net" not in (row.get("inferred") or []):
                reach = "`f` absent or carries no Net — the fixture never reached the bind/accept"
            elif benign and not any(h.split(":")[0] == benign for h in (row.get("hosts") or [])):
                reach = "benign literal %s not in `f`'s hosts %s — the arm's comparison cannot be read" % (
                    benign, row.get("hosts"))
            else:
                drc, _ = eng.run(target, d, pdeny)
                if drc != 1:
                    reach = "`deny Net` exit %d, want 1 — the gate is not shown able to fail here" % drc
            if reach:
                harness.append((arm, name, reach))
                print("  HARNESS %-11s %-6s %s" % (arm, name, reach))
                continue
            # ---- SCORE ---------------------------------------------------------------------------------
            got, _ = eng.run(target, d, pallow)
            bad = []
            if got != want:
                bad.append("`allow Net %s` exit %d, want %d" % (lit, got, want))
            if arm == "g_litdiscard" and not any(h.split(":")[0] == EVIL for h in (row.get("hosts") or [])):
                bad.append("the resolved literal %s is missing from hosts=%s" % (EVIL, row.get("hosts")))
            if arm == "a_litbind":
                leaked = [h for h in (row.get("hosts") or []) if h.split(":")[0] == BIND_LIT]
                if leaked:
                    bad.append("bind address published as a destination: hosts=%s" % leaked)
            exp = XFAIL.get((arm, name))
            detail = "hosts=%s incomplete=%s rc=%d" % (row.get("hosts"), row.get("incomplete"), got)
            if not bad and exp:
                print("  XFAIL ARM PASSED  %-11s %-6s — expectation is STALE: %s" % (arm, name, exp))
                stale.append((arm, name))
            elif not bad:
                print("  OK    %-11s %-6s %s  (%s)" % (arm, name, detail, why))
            elif exp:
                print("  xfail %-11s %-6s %s — %s  [%s]" % (arm, name, detail, "; ".join(bad), exp))
            else:
                print("  FAIL  %-11s %-6s %s — %s  (%s)" % (arm, name, detail, "; ".join(bad), why))
                fails.append((arm, name))
    if os.environ.get("CANDOR_PART96_KEEP"):
        print("  workspace kept: %s" % ws)
    else:
        shutil.rmtree(ws, ignore_errors=True)
    if not live:
        print("BIND/LISTEN: no engine available — NOT a pass")
        return 2
    if harness:
        print("\nBIND/LISTEN: %d cell(s) are a HARNESS FAULT — the fixture did not reach the engine, so no "
              "verdict on them is evidence (never an xfail)" % len(harness))
    if stale:
        print("\nBIND/LISTEN: %d xfail arm(s) PASSED — an expectation that has become true is a FAILURE here; "
              "retire it in the same commit as the engine fix (SOUNDNESS R817)" % len(stale))
    if fails:
        print("\nBIND/LISTEN: %d cell(s) wrong — see SPEC §2 ⟨0.40⟩ and SOUNDNESS R817" % len(fails))
    if harness or stale or fails:
        return 1
    print("\nBIND/LISTEN: OK — every conformant cell holds the bind/listen clause, every fixture reached its "
          "engine, and every open cell is declared on R817 or R949")
    return 0


if __name__ == "__main__":
    sys.exit(main())
