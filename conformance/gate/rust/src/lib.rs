pub fn save(p: &str) { let _ = std::fs::write(p, b"x"); }
// SOUNDNESS R411 — the DEFECT arm: a benign ALLOWED literal beside a caller-controlled write.
pub fn masked(p: &std::path::Path, b: &[u8]) {
    let _ = std::fs::write("/var/data", b);
    let _ = std::fs::write(p, b);
}
pub fn add(a: i32, b: i32) -> i32 { a + b }
