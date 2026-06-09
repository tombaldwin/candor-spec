//! Cross-impl conformance fixtures (Rust). Each fn mirrors a method in ../java/Cases.java with the SAME
//! intended effect; the harness asserts candor-scan and candor-java infer the same set. std-only (no deps)
//! so the cases exercise the core vocabulary both backends must agree on.
pub fn fs_read() { let _ = std::fs::read("/tmp/x"); }
pub fn net_connect() { let _ = std::net::TcpStream::connect("example.com:80"); }
pub fn exec_spawn() { let _ = std::process::Command::new("ls"); }
pub fn env_read() { let _ = std::env::var("PATH"); }
pub fn clock_now() { let _ = std::time::SystemTime::now(); }
pub fn pure_fn() -> i32 { 1 + 2 }
pub struct Dyn { pub f: fn() }
pub fn unknown_dyn(d: &Dyn) { (d.f)(); }
pub fn combined() { let _ = std::fs::read("/tmp/x"); let _ = std::net::TcpStream::connect("h:1"); }
pub fn transitive_leaf() { let _ = std::fs::read("/tmp/x"); }
pub fn transitive_caller() { transitive_leaf(); }
