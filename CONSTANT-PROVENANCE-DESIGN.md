# Constant provenance — the second axis, and the route to complete privacy-key coverage

**Status:** design, unbuilt. Written 2026-08-05 after measuring candor-swift against Apple's own key list.
**Companion to:** [VALUE-PROVENANCE-DESIGN.md](VALUE-PROVENANCE-DESIGN.md), which covers the *other* axis.

---

## 1. The finding that forces this

candor-swift models 42 of the 57 usage-description keys Apple documents. The 15 that remain do not
remain because nobody has written the table rows. They remain because **the resource is not named by the
API** — the same call needs a different key, or none, depending on a *value*:

```swift
FileManager.default.contents(atPath: p)      // p = "~/Desktop/x"  → NSDesktopFolderUsageDescription
                                             // p = "~/Documents/x"→ NSDocumentsFolderUsageDescription
                                             // p = "/Volumes/USB" → NSRemovableVolumesUsageDescription
                                             // p = <app sandbox>  → NO KEY AT ALL
```

Five of the fifteen are exactly this shape. And it is not an Apple curiosity: the Android permission
work measured the identical problem in a different ecosystem —
`ContentResolver.query(CalendarContract.Events.CONTENT_URI, …)` needs `READ_CALENDAR`, the same method
with a different URI constant needs `READ_CONTACTS`, and **zero `@RequiresPermission` annotations exist
on the entire ContentResolver surface** because no method annotation can express it.

Two ecosystems, one missing primitive.

## 2. Why the existing design does not cover it

`VALUE-PROVENANCE-DESIGN.md` recovers a value's **concrete type** — which `newType` reaches a call, so a
factory return or a field read resolves to the class that actually flows there. That is the right
primitive for *dispatch*: it answers "whose method is this".

The keys above need a different question answered: **"what constant is this"**. A `String` is a `String`
whichever folder it names; the type axis is uninformative by construction.

So:

| axis | question | recovers | designed in |
|---|---|---|---|
| **type** | whose method runs? | `newType` of a receiver/argument | VALUE-PROVENANCE-DESIGN.md |
| **constant** | which resource? | a string literal / enum case reaching an argument | **this document** |

They share machinery (both are backward dataflow to an origin, both are bounded, both must fail to
`Unknown`) and should share an implementation. They are not the same lattice.

## 3. What already exists (audited 2026-08-05, by running it)

More than expected, and it changes the cost estimate:

- **Literal arguments already reach the report.** `FileManager.default.contents(atPath: "/Users/me/Desktop/x.txt")`
  emits `paths: ["/Users/me/Desktop/x.txt"]` today. The §2 `paths`/`hosts`/`cmds`/`tables` fields are
  already a constant-capture mechanism — for the *direct literal* case only.
- **Argument-gated classification is an established pattern**, implemented twice: `privacyCaptureEffects`
  (the `AVCaptureDevice` media type) and `privacyAudioSessionEffects` (the `AVAudioSession` category).
  Both read a leading-dot enum member syntactically and both **over-disclose when the argument is not
  readable**.
- **`incompleteSurfaces`** already marks an effect whose *literal was not determinable*, which is the
  disclosure hook this design needs and does not have to invent.

What is missing is the step between: a literal bound to a variable, passed as a parameter, stored in a
field, or built by concatenation.

## 4. The design

### 4.1 Classes, not strings

Do **not** try to reconstruct the path. Reconstructing `"~/" + user + "/Desktop"` is a string-solver
problem and unbounded. What the answer needs is far weaker: **which protected class does this value fall
in**. So the lattice is over *classes*, and the platform supplies the class set:

```
PathClass  ::= Desktop | Documents | Downloads | Removable | NetworkVolume | Sandbox | Other
UriClass   ::= <android authority>            (contacts, calendar, call_log, media, …)
```

A constant resolves to a **set** of classes, and the set is the honest carrier:

- `{Desktop}` — proved: a literal, or an enum case (`.desktopDirectory`), or a concatenation whose
  *prefix* is proved.
- `{Desktop, Documents}` — a branch merge; both are possible, so both keys are required. Over-disclosure,
  which is the safe direction here.
- `⊤` (**undetermined**) — the value's origin is not in scope, is user input, or is past the bound.

### 4.2 The rule for ⊤, which is the whole ethical content of this design

**⊤ must not charge every key, and must not be silent.**

Charging all five folder keys on every undetermined path fabricates a requirement on every app that
writes a file — the overwhelming majority of which touch only their own sandbox and need no key at all.
That is the fabrication mirror, and it would make the feature unusable.

Staying silent is the cardinal sin: absence from the required set reads as "no key needed".

So ⊤ is neither. It is a **third state, disclosed** — precisely the treatment §2 already gives an
uncovered module and an unresolved call:

```
⚠ 12 file operations whose path could not be determined (in 4 functions). If any of them reach the
  Desktop, Documents or Downloads folder, or a removable or network volume, those keys are required
  and this verify cannot tell you. → candor path <fn> Fs
```

The count is the product. A verify that says *"clean, and there are zero undetermined paths"* is a much
stronger statement than today's, and one that says *"clean, but 12 undetermined"* is honest about
exactly what it did not see. Neither is available now.

### 4.3 The resolution ladder, cheapest first

Each rung is independently shippable and each strictly increases what is *determined* — never what is
claimed. Stopping at any rung is sound; it just leaves more ⊤.

1. **Direct literal** — done today (`paths`).
2. **Platform enum argument** — `.desktopDirectory`, `.documentDirectory`, `.downloadsDirectory` on
   `FileManager.urls(for:in:)`. Syntactically visible; the `mediaTypeArg` pattern exactly. Covers the
   *canonical* spelling for these folders, which matters more than the literal case.
3. **Intra-procedural binding** — `let p = "~/Desktop/x"; …contents(atPath: p)`. A local bound once to a
   determined value carries it. Bounded, no fixpoint.
4. **Prefix-preserving concatenation** — `home + "/Desktop/" + name` resolves to `{Desktop}` because the
   *class* is decided by a proved prefix; the unknown tail cannot move it. This is where classes beat
   strings: an unknowable suffix is irrelevant to the answer.
5. **Interprocedural parameter binding** — one level, reusing the construction-carried binding already
   designed for the type axis (§3 of the companion doc).
6. **Field origin** — same summary structure as the type axis, carrying constants instead of types.

Rungs 1–2 need no dataflow at all. Rungs 3–4 are intra-procedural. Only 5–6 need the interprocedural
machinery, and they share it with the type axis rather than adding a second engine.

### 4.4 The soundness contract

Identical in shape to the companion doc's, and it must be stated because this analysis *adds*
requirements rather than removing them:

> Constant provenance may only ever move a value **down** from ⊤ to a determined class set, or leave it
> at ⊤. It must never *narrow* a determined set on the basis of an unproved origin. An imprecise result
> is therefore always either a larger key set (over-disclosure) or a disclosed ⊤ — never a missing key.

Concretely: a merge of `{Desktop}` with ⊤ is ⊤ *and stays disclosed*, not `{Desktop}`.

## 5. The second input: entitlements

Four of the fifteen (`NSAppBundles`, `NSAppData`, `NSCriticalMessaging`, `NSEnterpriseMCAM`) are managed
/enterprise surfaces. Some may have **no public API at all** — the capability is gated by an entitlement,
not by a call, and no amount of code analysis will see it.

For those the input is the `.entitlements` file: a plist, read exactly as `Info.plist` already is, with a
rule of the form *entitlement present ⇒ key required*. This is **not code analysis and must not be
presented as such** — it is a manifest-to-manifest consistency check, and the verify should say which of
its findings came from which kind of evidence.

**Open, needs a doc read per key before designing further:** whether each of the four has any public API
surface at all. Do not build the entitlement path until that is answered; it may be that two of them are
ordinary type mappings and only two need this.

## 6. What full coverage must not cost

Today the verify says *"I check 42 keys, here are the 15 I do not"*, and that sentence is what stops a
green result reading as "green for Apple".

**If every key becomes nominally modelled, that sentence disappears — while the coverage *within* several
keys is still partial.** A folder key resolved at rung 2 catches the canonical and literal spellings and
leaves computed paths at ⊤. Reporting that as "modelled" with no qualifier would be a *reduction* in
honesty bought with an increase in the count, which is the exact trade this project exists not to make.

So full coverage requires the disclosure to change axis, from **which keys** to **how completely**. Each
key carries a **determination basis**:

| basis | meaning | example |
|---|---|---|
| `type` | a distinctly-named API names the resource | Camera, Contacts |
| `argument` | an enum/descriptor argument names it; unreadable ⇒ over-disclose | audio category |
| `constant` | a path/URI class; unresolved ⇒ **⊤, counted and disclosed** | Desktop, Documents |
| `entitlement` | read from `.entitlements`, not from code | enterprise keys |
| `none` | no code signal exists at all | — |

and the verify reports per basis, with the ⊤ count for `constant` keys. That keeps the safety net at
57/57 instead of trading it away for the number.

## 7. Scope: what is floor and what is extension

- **Constant provenance is a FLOOR capability.** It is the same primitive Android permissions need, and
  `paths`/`hosts`/`cmds`/`tables` are already floor fields whose determinability it improves. It belongs
  in SPEC §2 beside them, with the ⊤ count as a disclosed field — probably a sibling of the
  `incompleteSurfaces` mechanism rather than a new concept.
- **The class→key tables stay in the extensions.** `PathClass → NS…UsageDescription` is Apple's;
  `UriAuthority → android.permission.*` is Google's. Neither belongs in the contract.

That split is what makes this worth building twice over: one primitive, two ecosystems, and the
ecosystem-specific parts stay where they can be wrong without breaking the floor.

## 8. Route to all 57, with what each step actually costs

| # | keys | route | new machinery |
|---|---|---|---|
| 1 | NearbyInteractionAllowOnce | a second acceptable key on an existing effect | none — `privacyKeyMap` is already a *list* and the verify accepts any member |
| 2 | AccessoryTracking, AudioCapture | type mapping, as privacy/4 | none |
| 3 | 5 folder keys, LocalNetwork | ladder rungs 1–2 (literal + platform enum) | the `mediaTypeArg` pattern, third instance |
| 4 | the same 6, computed spellings | ladder rungs 3–4 | intra-procedural constant binding |
| 5 | 4 enterprise keys | entitlements input, *if* they have no API | plist read + rule table |
| 6 | FileProviderPresence | member gate, probably | none |
| — | all of them | honest reporting at 57/57 | **determination basis + ⊤ counts (§6)** |

Steps 1, 2, 3 and 6 are the existing patterns and reach roughly 51/57 with no new design. Step 4 is the
first genuinely new machinery and is also the Android unblock. Step 5 needs a doc read before it can be
scoped. **§6 is not optional** — it is what makes the other steps safe to ship.

## 9. What this is NOT

- **Not a string solver.** Classes, not values; a proved prefix decides the class and the tail is
  irrelevant. No constraint solving, no regex reasoning about paths.
- **Not general constant propagation.** Only values that reach an argument slot the classifier asks
  about — the same demand-driven shape the type axis uses.
- **Not a replacement for disclosure.** Every rung leaves ⊤ cases, and the design's central rule is that
  ⊤ is counted and reported rather than resolved by guessing in either direction.
