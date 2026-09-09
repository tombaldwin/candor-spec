use super::client::Client;
pub struct RequestBuilder;
impl RequestBuilder { pub fn send(&self) -> bool { let c = Client; c.execute() } }
