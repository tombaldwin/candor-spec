# R213 — `use super::` is stored with the prefix intact

**This fixture exists because the original repro went missing.** R213 cited `r212/repro` and
`repro2` in a session scratchpad; by the time the row was worked, those held only stale `.candor/`
reports and `r212/fixture/src/lib.rs` was 0 bytes. A row whose repro lives only in `/tmp` is a row
nobody can re-open.

## What it shows

    cargo build --release -p candor-scan     # in candor-rust
    candor-scan candor-spec/fixtures/r213-super-import --json

    net::client::Client::execute   ['Exec']
    reported: 1 of analyzed 3          <-- net::request::RequestBuilder::send is ABSENT

`send` calls `Client::execute`, which runs `Command::new("/bin/true").status()`. It is a positive
purity claim under SPEC §2 rule 3, and nothing discloses it: no `unanalyzed`, no `coverage`, no
`excluded`.

    echo 'pure net::request::RequestBuilder::send' > p
    candor-scan candor-spec/fixtures/r213-super-import --policy p   # exit 0

## THE PART THE ROW DID NOT SAY: `src/other/client.rs` is load-bearing

Two earlier reconstructions of this repro did NOT reproduce — `send` reported `['Exec']` correctly.
The defect only appears when a SAME-LEAF sibling (`other::client::Client::execute`) exists elsewhere
in the crate. `use super::client::Client` is stored as `super::client::Client`, which names no local
def, so resolution falls back to the bare leaf `execute`; with one candidate the fallback finds the
right one, and with two the uniqueness hedge drops the edge silently.

So the sibling is not scenery. Delete `src/other/` and the fixture stops demonstrating anything.

## Scope of the sin

`deny Exec` over the whole crate still exits 1, because the DEFINITION
(`net::client::Client::execute`) is reported. The silence is function-scoped: it is `send`, and any
gate naming `send`, that is certified pure.
