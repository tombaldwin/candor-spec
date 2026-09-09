pub struct Client;
impl Client { pub fn execute(&self) -> bool { std::process::Command::new("/bin/true").status().is_ok() } }
