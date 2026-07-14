# The `Llm` effect — design (family-level, pre-implementation)

**Status: IN IMPLEMENTATION (2026-07-14) — spec §1 written (SPEC.md ⟨0.13⟩), java reference in progress
(reference-led rung). All three open questions decided as recommended (name `Llm`; embeddings/moderation
count; local inference counts).**

## The shared model-host table (the four engines implement this verbatim — the conformance oracle)

Case-insensitive host match; a SUBDOMAIN of a listed host counts. Anything else stays bare `Net`.

    api.openai.com                          api.mistral.ai
    api.anthropic.com                       api.cohere.ai / api.cohere.com
    generativelanguage.googleapis.com       api.groq.com
    *.bedrock*.amazonaws.com  (bedrock-runtime.<region>.amazonaws.com)   api.together.xyz
    openrouter.ai                           api.perplexity.ai
    <any host>:11434  (a local Ollama endpoint — the local-inference-counts decision)

A statically-known request to one of these → `Llm` IN ADDITION to `Net` (Net is never dropped — a model
call IS network I/O, mirroring how an Exec-refined subprocess keeps `Exec`). An unknown host or an
uncovered SDK stays bare `Net`/`Unknown`; the §7 ledger discloses the uncovered provider. The table
lives beside each engine's command-head table (candor-java Literals.commandHeadEffects,
candor-rust classify_command_head, …) as a shared verbatim block, so it can't drift.


## Why

"Which functions call a model provider" is a per-function supply-chain question nobody answers from
static analysis: an LLM call is a data-exfiltration surface (whatever reaches its arguments leaves the
box), a prompt-injection ingress, and a cost/latency boundary. Today it reads as bare `Net` — drowned
among every other outbound call. As its own effect it becomes:

- **gate-able** — `deny Llm outside ai/` (the §6.2 grammar already parses any effect token);
- **watchable** — `gains` + `origin`: *"your dependency bump added an LLM call to a function that
  shipped without one"* is the sharpest form of the candor-gains alarm;
- **tour-able** — a benign-named fn reaching `Llm` four hops down is exactly the surprising-reach
  shape (salience: high, alongside Net/Exec/Db/Ipc).

## Shape

- **Standalone effect, not a Net annotation** — the `Db`/`Ipc` precedent: the boundary taxonomy is
  disjoint at the source; a policy denying `Net` does not (and should not) implicitly deny `Db`, so
  likewise for `Llm`. A call site classifies as `Llm` when the SINK is a model API; plain transport it
  rides on is not separately charged (same as Db-over-jdbc).
- **Classification sources**, two rules mirroring existing machinery:
  1. **SDK surface** — the provider clients per ecosystem (anthropic/openai/google-genai/bedrock/
     mistral/ollama/langchain-core invoke surfaces; JVM: the AWS Bedrock + langchain4j + openai-java
     clients; rust: async-openai, anthropic-sdk crates; swift: the OpenAI/Anthropic swift SDKs; ts:
     openai, @anthropic-ai/sdk, ai (Vercel), @google/generative-ai).
  2. **Host-literal refinement** — the literal-host extraction (§2 `hosts`) already captures
     `api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com`,
     `bedrock*.amazonaws.com`, `localhost:11434` (ollama) — a raw fetch/reqwest to a known model host
     classifies `Llm` exactly as a jdbc URL classifies `Db`. Unknown hosts stay bare `Net` (never
     guess).
- **Salience**: high (joins Net/Exec/Db/Ipc in the surprising-reach heuristic).

## Contract mechanics

- **Tier-1 ADDITIVE** (a new vocabulary entry) → a minor rung, ladder-conformant, java leads.
  Forward-compat: consumers MUST already tolerate unknown effect names in `inferred`/`direct`
  (§2 forward-compatibility); a pre-rung policy simply never names `Llm` (no behavior change).
- **Costs, priced in before building** (the soundness tracker's discipline): a new EFFECT column in
  the seam × engine matrix — conformance PART 1 vectors ×4, fabrication-probe entries ×4 (an `Llm`
  fabricated onto a non-model host is the precision failure to fence), and the per-engine SDK lists
  become curated surface (the κ ledger continues to disclose uncovered providers).

## Decisions (Tom, 2026-07-14)

1. Name: **`Llm`**.
2. Embeddings/moderation calls **count** — one effect, no sub-taxonomy (same exfil surface).
3. Local inference (ollama/llama.cpp) **counts** — the host literal discloses localhost; the gate
   question is "does this code consult a model", not "does it pay a provider".
