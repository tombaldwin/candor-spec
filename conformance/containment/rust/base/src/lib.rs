//! Baseline: svc does Net only — Fs is fully contained in repo.
pub mod repo {
    pub fn read_a() { let _ = std::fs::read("a"); }
    pub fn read_b() { let _ = std::fs::read("b"); }
}
pub mod svc {
    pub fn net() { let _ = std::net::TcpStream::connect("h:80"); }
}
