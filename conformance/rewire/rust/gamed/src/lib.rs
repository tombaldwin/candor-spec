pub mod a { pub fn caller() {} }                              // a::caller DROPPED its call to b::work
pub mod b { pub fn work() { let _ = std::fs::read("/tmp/x"); } }
