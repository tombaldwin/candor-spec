# The privacy-sensor effect cluster — design (swift-led, pre-implementation)

**Status: DECIDED (Tom, 2026-07-14) — proceed as a swift-led SPEC EXTENSION + a `privacy-manifest`
product verb. Next: draft candor-swift/SPEC-EXTENSION-privacy.md, then implement.**

## Why

Apple's **privacy manifests** (NSPrivacyAccessedAPITypes, purpose strings, App Store review) demand a
declaration of exactly what candor computes from code: *which capabilities does this code actually
touch, including transitively through dependencies*. Today a `CLLocationManager` call reads as nothing
(uncovered — DISCLOSED in the ledger, invisible to the report). Yesterday's pollen dogfood ledger
already names the demand: `UserNotifications (3 imports), MapKit (8 imports)` sit in the uncovered
list of a real app.

The product shape this unlocks is bigger than a classifier batch: **generate or VERIFY a privacy
manifest from code-level truth** — "your manifest declares Location; your code (via dependency X)
also reaches Contacts" is an App-Store-rejection-shaped finding.

## The cluster

| effect | swift sources (first wave) |
|---|---|
| `Location` | CoreLocation (CLLocationManager…), MapKit user-location surfaces |
| `Camera` / `Mic` | AVFoundation capture (AVCaptureDevice, AVAudioRecorder…) |
| `Contacts` | Contacts / ContactsUI |
| `Photos` | PhotosKit (PHPhotoLibrary…) |
| `Notify` | UserNotifications (UNUserNotificationCenter…) |

Boundary-rule check: every one is an outside-world surface (a sensor, a personal-data store, or the
user's attention) — same footing as `Clipboard` (§6.1). Abstract non-boundaries (Crypto, Memory) stay
out. All five join the CONTAINED (boundary) class for §6.1 containment + the surprising-reach
salience set — "a `formatDate` helper that reaches `Location` three hops down" is precisely the tour
find that sells this.

## Cross-engine posture

Server-side engines (rust/java-server/ts-node) have no native analog for most of the cluster —
**N/A by language model**, the `dispatch:`-frontier precedent: conformance treats a structurally
absent effect as N/A, not a gap. Real analogs exist later (Android's location/camera APIs for a
JVM-Android target; browser geolocation/getUserMedia for ts-web) — staged, not first-wave.

## The ladder decision — RESOLVED (Tom, 2026-07-14)

**Ecosystem-specific rungs are led by the motivated engine as a SPEC EXTENSION** (SPEC.md §Versioning
policy, the engine-extensions clause): candor-swift writes `SPEC-EXTENSION-privacy.md` in its own repo
— the full contract (vocabulary, classification sources, disclosure posture, fabrication fences) —
implements against it, and discloses it in the envelope (`"extensions": ["privacy/1"]`). The extension
can later be promoted into the main spec as a shared rung, or adopted verbatim by another engine
(the Android/JVM and browser/ts analogs are the obvious future adopters).

## Costs + sequencing

Same per-effect soundness pricing as any vocabulary addition (seam-matrix columns, fabrication
probes — a fabricated `Camera` on a QR-decode library is the precision failure to fence, conformance
vectors where engines have the effect, else N/A). Sequence: (1) the vocabulary + swift classification
batch (the pollen ledger's uncovered list doubles as the first fixture set); (2) the
`privacy-manifest` verb (generate + verify against an existing manifest); (3) the marketing exhibit —
run it on a real open-source iOS app and show a manifest divergence.
