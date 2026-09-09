use std::fs::File;
use std::io::Read;
pub fn a_method(mut f: File) -> String { let mut s = String::new(); f.read_to_string(&mut s).unwrap(); s }
pub fn b_ufcs(mut f: File) -> String { let mut s = String::new(); Read::read_to_string(&mut f, &mut s).unwrap(); s }
pub fn c_iocopy(mut f: File) { std::io::copy(&mut f, &mut std::io::sink()).unwrap(); }
pub fn d_from_reader(f: File) -> serde_json::Value { serde_json::from_reader(f).unwrap() }
pub fn e_bufreader(f: File) -> Vec<String> { use std::io::BufRead; std::io::BufReader::new(f).lines().map(|l| l.unwrap()).collect() }
pub fn n_ufcs(mut s: std::net::TcpStream) { use std::io::Write; Write::write_all(&mut s, b"x").unwrap(); }
pub fn n_method(mut s: std::net::TcpStream) { use std::io::Write; s.write_all(b"x").unwrap(); }
pub fn x_cmd_method(mut c: std::process::Command) { c.spawn().unwrap(); }
pub fn z_child_wait(mut c: std::process::Child) { c.wait().unwrap(); }
pub fn z_child_ufcs(c: std::process::Child) { let _ = std::process::Child::wait_with_output(c); }
