# The masking DEFECT arm — written, measured four-way, and HELD until SOUNDNESS R409 is fixed

`conformance/gate` currently pins only the **control** arm of the AS-EFF-008 masking class. Every
language's fixture is one method whose path is a parameter and which contains **no other literal**, so
every engine correctly answers "uncertifiable" and PART 12 passes. The arm that actually distinguishes a
sound engine from an unsound one — the same runtime write with a benign **allowed literal beside it** —
was never written, which is why this differential could not see R409 (java) or R410 (ts) and never could.
That is SOUNDNESS **R411**.

## Why this is not committed yet

The suite is strictly pass/fail; there is no xfail or declared-divergence mechanism. Landing the arm
makes `conformance` RED on `main` until **R409** (java: the Fs surface-incomplete marking is
allowlist-shaped, so a benign sibling certifies a caller-controlled path) is fixed. So the arm is written
and MEASURED here, and lands in the same change as that fix.

## Measured four-way, 2026-09-12, against the shipped 0.36.1 engines

Policy unchanged (`deny Fs` + `allow Fs /var/data`). Adding `masked` to each fixture gives:

| engine | `AS-EFF-006 masked` | `AS-EFF-008 masked` | verdict |
|---|---|---|---|
| candor-scan (rust) | yes | **yes** | sound |
| candor-ts          | yes | **yes** | sound (after R410) |
| candor-swift       | yes | **yes** | sound (after R395/R393) |
| **candor-java**    | yes | **NO**  | **the bypass — R409** |

Three engines flag the masked destination and java does not. That asymmetry is the whole value of the
arm: it discriminates, where the existing fixture is a second control.

## The arm, in all four languages

```java
// java/app/Store.java
public void masked(Path p, byte[] b) throws Exception {
    Files.write(Paths.get("/var/data"), b);   // the ALLOWED literal
    Files.write(p, b);                        // caller-controlled — invisible to the gate
}
```
```rust
// rust/src/lib.rs
pub fn masked(p: &Path, b: &[u8]) { let _ = std::fs::write("/var/data", b); let _ = std::fs::write(p, b); }
```
```typescript
// ts/store.ts
export function masked(p: string): void { writeFileSync("/var/data", ""); writeFileSync(p, ""); }
```
```swift
// swift/Store.swift
func masked(_ p: String) throws {
    try Data().write(to: URL(fileURLWithPath: "/var/data"))
    try Data().write(to: URL(fileURLWithPath: p))
}
```

Note the java arm takes a `Path` PARAMETER rather than a `String`: `Paths.get(p)` enters java's
path-construction branch and is correctly marked incomplete, which is precisely why the existing `save`
fixture passes. The defect needs a path that never passes through that branch at all.

## The `EXPECT` delta in run.sh PART 12

```python
EXPECT = (False, [("AS-EFF-006", "masked", ("Fs",)),
                  ("AS-EFF-006", "save",   ("Fs",)),
                  ("AS-EFF-008", "masked", ("Fs",)),   # ← the arm this file adds
                  ("AS-EFF-008", "save",   ("Fs",))])
```

The list is sorted by `(rule, leaf, effects)` in `norm()`, so `masked` precedes `save` within each rule.

---

## THE SECOND BLIND INSTRUMENT — `gen_masking.py`, found 2026-09-12 by running the suite

PART 12 is not the only gate for this class. `conformance/run.sh` also drives a **CROSS-ENGINE
GATE-MASKING differential — masked-literal allowlist evasion (AS-EFF-008 opaque)** over 16
(effect × engine) cells, built for exactly this evasion. Its **Fs × java** cell reports `m→1 c→0 [ok]`,
green, while java Fs is live-broken (R409).

Both are true because `gen_masking.py` renders the java masked program as:

```java
Files.write(java.nio.file.Path.of("/var/app/ok"), …);   // benign, allowed
Files.write(java.nio.file.Path.of(p), …);               // "masked"
```

`Path.of(p)` **enters java's construction branch** (`Candor.java:5209-5221`) and is correctly marked
incomplete, so the cell passes. R409's spelling — `Files.write(p, b)` where `p` is already a `Path` —
never reaches that branch at all. **PART 12's fixture makes the identical choice** (`Paths.get(p)`).

So two instruments, written independently for the same evasion, both CONSTRUCT THE PATH INLINE — the one
shape the engine handles — and neither can ever see a path that arrived as a parameter.

### What `gen_masking.py` needs, alongside the PART 12 arm above

A second java variant whose path is a **parameter**, not an inline construction:

```java
static void masked(java.nio.file.Path p, byte[] b) throws Exception {
    Files.write(java.nio.file.Path.of("/var/app/ok"), b);   // benign, allowed
    Files.write(p, b);                                       // caller-controlled, invisible
}
```

The other three engines already fail closed on their equivalent (measured), so this widens the
differential from 16 cells to 20 and turns exactly one of them red until R409 lands.

**Both arms are owed by the same fix, and should land in the same change.**

