// domain::price calls through a FUNCTION VALUE — candor can't resolve it → Unknown. `pure domain` PASSES it
// (Unknown ≠ a real effect), but its purity is UNVERIFIED (the fn could do anything). `unverified` discloses it.
pub mod domain {
    pub fn price(fetch: &dyn Fn() -> u64) -> u64 { fetch() + 1 }
}
