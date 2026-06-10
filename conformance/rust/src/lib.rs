//! Cross-impl conformance fixtures (Rust). Each fn mirrors a method in ../java/Cases.java with the SAME
//! intended effect; the harness asserts candor-scan and candor-java infer the same set. std-only (no deps)
//! so the cases exercise the core vocabulary both backends must agree on.

// --- direct vocabulary ------------------------------------------------------------------------------
pub fn fs_read() { let _ = std::fs::read("/tmp/x"); }
pub fn net_connect() { let _ = std::net::TcpStream::connect("example.com:80"); }
pub fn exec_spawn() { let _ = std::process::Command::new("ls"); }
pub fn env_read() { let _ = std::env::var("PATH"); }
pub fn clock_now() { let _ = std::time::SystemTime::now(); }
pub fn pure_fn() -> i32 { 1 + 2 }

// --- the trust contract: an unanalysable call is Unknown --------------------------------------------
pub struct Dyn { pub f: fn() }
pub fn unknown_dyn(d: &Dyn) { (d.f)(); }

// --- composition: union + transitive propagation ----------------------------------------------------
pub fn combined() { let _ = std::fs::read("/tmp/x"); let _ = std::net::TcpStream::connect("h:1"); }
pub fn transitive_leaf() { let _ = std::fs::read("/tmp/x"); }
pub fn transitive_caller() { transitive_leaf(); }

// --- effect inside a locally-invoked closure flows to the enclosing fn -------------------------------
pub fn closure_effect() {
    let f = || { let _ = std::fs::read("/tmp/x"); };
    f();
}

// --- Unknown propagates across a call like any other effect -----------------------------------------
pub fn unknown_propagates(d: &Dyn) { unknown_dyn(d); }

// --- a function with BOTH an opaque call and a concrete effect --------------------------------------
pub fn mixed_unknown(d: &Dyn) { (d.f)(); let _ = std::fs::read("/tmp/x"); }

// --- a 3-hop chain a -> b -> c(Net) -----------------------------------------------------------------
pub fn hop_c() { let _ = std::net::TcpStream::connect("h:1"); }
pub fn hop_b() { hop_c(); }
pub fn hop_a() { hop_b(); }

// --- a caller unions the effects of two distinct callees --------------------------------------------
pub fn union_b() { let _ = std::fs::read("/tmp/x"); }
pub fn union_c() { let _ = std::net::TcpStream::connect("h:1"); }
pub fn union_a() { union_b(); union_c(); }

// --- recursion: the fixpoint must terminate AND keep the effect -------------------------------------
pub fn recurse(n: i32) { if n > 0 { let _ = std::env::var("X"); recurse(n - 1); } }

// --- an effect in one branch only is still inferred (over-approximation) ----------------------------
pub fn conditional(b: bool) { if b { let _ = std::process::Command::new("x"); } }

// --- transitive purity: a -> b -> c, all pure, stays pure (negative) --------------------------------
pub fn pure_c() -> i32 { 3 }
pub fn pure_b() -> i32 { pure_c() }
pub fn pure_a() -> i32 { pure_b() }

// --- a method call on a concrete LOCAL-type receiver propagates the method's effect ------------------
pub struct Svc;
impl Svc { pub fn act(&self) { let _ = std::fs::read("/tmp/x"); } }
pub fn method_call(s: &Svc) { s.act(); }

// --- scheduler attribution: an effect inside a spawned closure attributes to the SPAWNING fn ---------
// (SEMANTICS §2 closure-attribution; the JVM twin — an anonymous Runnable handed to Thread — was a real
// under-report in candor-java, fixed 2026-06-10. This case locks the guarantee cross-impl.)
pub fn sched() {
    let h = std::thread::spawn(|| { let _ = std::fs::read("/tmp/x"); });
    let _ = h.join();
}
