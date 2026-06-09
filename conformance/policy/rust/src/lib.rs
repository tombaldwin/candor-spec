//! Layered fixture for the ENFORCEMENT differential: `pricing::quote` is the leaf; `api` is the layer the
//! shared policy forbids from the network. `whatif quote Net` must flag the `api` layer in BOTH engines.
pub mod pricing { pub fn quote(c: u64) -> u64 { c * 100 } }
pub mod cart    { use crate::pricing; pub fn total(c: u64) -> u64 { pricing::quote(c) } }
pub mod api     { use crate::cart; pub fn handle(c: u64) -> u64 { cart::total(c) } }   // deny Net api
pub mod report  { use crate::cart; pub fn summary(c: u64) -> u64 { cart::total(c) } }  // NOT denied
