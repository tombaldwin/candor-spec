// orderflow: api::get -> domain::bulk -> domain::price -> infra::fetch (the Net source).
// `deny Net domain` makes the two domain fns a crossing; the fix hoists Net to api::get.
pub mod infra {
    pub fn fetch() { let _ = std::net::TcpStream::connect("h:1"); }
}
pub mod domain {
    pub fn price() { crate::infra::fetch(); }
    pub fn bulk() { price(); }
}
pub mod api {
    pub fn get() { crate::domain::bulk(); }
}
