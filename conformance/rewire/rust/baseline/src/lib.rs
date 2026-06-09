pub mod a { use crate::b; pub fn caller() { b::work(); } }   // a::caller -> b::work
pub mod b { pub fn work() { let _ = std::fs::read("/tmp/x"); } }
