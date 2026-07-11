pub mod infra { pub fn fetch() { let _ = std::net::TcpStream::connect("h:1"); } }
pub mod domain {
    pub fn inner() { crate::infra::fetch(); }
    pub fn top() { crate::api::mid(); }
}
pub mod api { pub fn mid() { crate::domain::inner(); } }
