# `Net` destination-class — telemetry vs. exfiltration, made gate-able ⟨proposed⟩

Refine the `Net` effect with a **destination CLASS** per host — `known-telemetry`, `known-partner`,
`unknown-host` — so a gate can say *"the domain layer may reach our declared partners and telemetry, but
not an unknown host"* instead of the all-or-nothing `deny Net`. Answers the industry referee's hardest
coarse-effects dealbreaker (candor-paper `REFEREE-REPORTS.md`): **`Net` today can't tell a benign analytics
POST from an exfiltration POST — both are `Net`**, so a security-minded team can't gate on it and falls back
to a network egress allowlist candor doesn't feed.

## The finding

`deny Net domain` blocks *all* network from the domain layer — but real domain code legitimately reaches
telemetry (Sentry, Datadog) and declared partner APIs (Stripe, the payments provider). So the gate is either
off (no protection) or breaks the build on benign telemetry. The *exfiltration* shape — a `Net` to a host
that is neither known-telemetry nor a declared partner — is exactly what a security reviewer wants to catch,
and it is **structurally identical** to `Net` to a partner in today's report. The coarseness, not the
detection, is the defect — the same shape as the `Unknown` deny-all problem the reason-scoped rung fixed.

## What already exists — the exact machinery to generalize

candor already **extracts `Net` host literals and classifies one host family** — the `Llm` refinement:
- **`MODEL_HOSTS`** (ts `scan-core.mjs` / java `Literals.MODEL_HOSTS` / rust / swift): a curated, shared-
  **verbatim** set of model-provider hosts, matched by host (subdomain-aware, case-insensitive, `:port`
  stripped). A `Net` call to a `MODEL_HOSTS` host is refined to `Llm` (SPEC §1 ⟨0.13⟩).
- The report's **`hosts`** field already carries the literal endpoints (`host[:port]`) when `Net` is present
  (const-anchored + literal-head resolution, spec 0.14/0.15) — and the **AS-EFF-008 masking guard**
  fail-closes when a host is structurally invisible.

So the destination-class is `MODEL_HOSTS` generalized: **host → class**, plus the honest `unknown-host`
default and the AS-EFF-008 fail-closed posture already in place.

## The design

### 1. The three classes (a closed vocabulary + one config-driven member)

| class | source of truth | meaning |
|---|---|---|
| `known-telemetry` | a curated, four-way-**verbatim** `TELEMETRY_HOSTS` set (like `MODEL_HOSTS`) — analytics / monitoring / error-tracking (segment, datadog, sentry, google-analytics, mixpanel, amplitude, newrelic, bugsnag, honeycomb, …) | a benign observability endpoint |
| `known-partner` | **config-declared** — `.candor/config` `net-partner <host>` (per-project; a partner is not universal) | a host the project has explicitly declared a business partner |
| `unknown-host` | **the honest default** — every visible host on neither list, AND every fn whose `Net` host is unresolved / runtime / masked | candor makes NO claim; could be benign or exfiltration |

`known-telemetry` and `known-partner` are the *asserted-safe* classes; `unknown-host` is the residual the
security gate bites. (An `Llm` model host is already its own refinement; a model host is treated as
`known-partner`-adjacent OR carries no `Net` class — resolved in Open questions.)

### 2. Soundness — `unknown-host` is the fail-closed default (never fabricated)

The cardinal-sin risk here is the DUAL of the `setup` tag: **mis-classifying an exfil host as
`known-telemetry`/`known-partner` would let a genuine exfiltration `Net` slip a `deny Net[unknown-host]`
gate** (under-gating). So the asserted-safe classes are **only** ever assigned from an exact host-literal
match against the curated set / declared partners — precise because the host literal IS the match key (the
`MODEL_HOSTS` precision). Everything else is `unknown-host`:
- an **unresolved / runtime-computed host** (`fetch(base + path)` where `base` is a var) → `unknown-host`
  (the existing bare-`Net` posture; never guessed);
- a **structurally-masked surface** (AS-EFF-008 incomplete) → `unknown-host`, fail-closed (a benign visible
  telemetry host must not certify a fn that ALSO reaches an invisible endpoint — the existing masking rule);
- a host on **neither list** → `unknown-host`.

So `deny Net[unknown-host]` fails closed on anything candor cannot positively identify as telemetry/partner —
the sound direction (over-report the exfil risk, never under-report it).

### 3. Report schema (additive)

A per-fn **`netClass`** array — the destination classes present in the fn's (transitive) `Net` surface,
e.g. `["known-telemetry", "unknown-host"]` — omitted when the fn has no `Net`. Additive + optional (a
pre-rung consumer ignores it); the `hosts` field is unchanged. The class travels transitively along the call
graph exactly like the effect (a caller reaching an unknown-host through a callee is `unknown-host`), the
same propagation the reason-scoped `reasonClass` uses.

### 4. Policy grammar — the security gate

`deny Net[unknown-host] <scope>` — deny `Net` to an unknown host in scope, tolerating telemetry + declared
partners. Bracket syntax + fail-closed semantics reuse the reason-scoped `Unknown[class]` machinery
verbatim (bare `deny Net` unchanged = all destinations; `Net[*]` = all; an unrecognized class warns). The
verdict carries the fn's `netClass` (like `reasonClass`). This is the **security use case candor can't
currently cash**: "the domain layer may egress only to known destinations."

### 5. Config — declaring partners

`.candor/config` `net-partner api.stripe.com` (repeatable, multi-value — same shape as `unknown-alias`),
matched host-wise like `MODEL_HOSTS`. A partner is per-project, so it MUST be config-declared, never a
universal list; and it is a spelling of *"I accept Net to this host"*, so it can never make a bare `deny
Net` narrower (the `unknown-alias` legibility rule).

## Conformance + versioning

A new PART pins `netClass` four-way (the curated `TELEMETRY_HOSTS` set is shared verbatim, like `MODEL_HOSTS`
— PART 4l precedent) + the `Net[class]` grammar (PART 4) + the fail-closed `unknown-host` posture on a
masked/unresolved host. A tier-1 additive schema field + a tier-2 policy/config surface — a real vocabulary
rung (est. **0.21**), additive (a pre-0.21 report/policy is unaffected).

## What this is NOT

- **Not a claim a host is SAFE** — `known-telemetry`/`known-partner` mean "candor recognizes this endpoint,"
  not "this traffic is harmless"; the gate is a *coarseness fix*, not a threat model. `unknown-host` is the
  honest "candor cannot vouch for this."
- **Not deep-packet / payload analysis** — it is host-literal classification only, the decidable subset (the
  same honest limit as `hosts`).
- **Not fabrication** — an unresolved host is `unknown-host`, never guessed onto a safe class.

## Open questions (for Tom, before the four-way build)

1. **The curated `TELEMETRY_HOSTS` scope** — how broad? A tight, defensible starter set (like the `MODEL_HOSTS`
   starter) vs. a large catalog. Recommendation: start tight + high-precision (mis-including an exfil-capable
   host would under-gate), grow via corpus.
2. **`known-partner` = config-only?** (recommended — partners aren't universal), or also a small curated set
   of ubiquitous partner APIs (Stripe/Twilio/…)? Config-only is the sound, per-project-honest choice.
3. **`Llm` model hosts** — does a model host get a `Net` destination-class too (e.g. `known-partner`), or is
   the `Llm` refinement its class? Recommendation: a model host is `known-partner`-class for the `Net`
   destination gate (it IS a declared-ish external API), independent of the `Llm` effect refinement.
4. **Naming** — `netClass` / `unknown-host` / `known-telemetry`, or shorter (`net-dest`, `unknown`)? The
   `unknown-host` token must not collide with the `Unknown` effect or the `unresolved` reason class.
5. **Effort/sequencing** — this is the biggest of the disclosure-refinement rungs (schema + host-classifier
   + policy + config, four-way). Worth it iff the security-gate use case is a real sales/adoption driver
   (the referee says it is). Sequence after any pending 0.20 (blindspots `--stats`/`--class`) ship.
