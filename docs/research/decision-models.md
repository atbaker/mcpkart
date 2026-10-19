# Decision models for the local driving experiment

Checked October 18, 2026. OpenRouter exposes the three requested model families through a shared Decisions endpoint, so an OpenRouter key can support the comparison. These API research notes preceded the local implementation; measurement recordings are stored separately under `artifacts/`.

## Verified access

Use `POST https://openrouter.ai/api/alpha/decisions` with Bearer authentication from `OPENROUTER_API_KEY`. This uses OpenRouter's request schema: required `model`, `state`, and a `questions` object keyed by question name. A choice question contains `instructions` and a `criteria` object mapping allowed values to descriptions. Responses put a selected control under `answers.control.choice`. [Endpoint reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)

| Model | OpenRouter identifier | Initial role |
| --- | --- | --- |
| [TypeSafe Jev 1.14](https://openrouter.ai/typesafe/jev-1.14) | `typesafe/jev-1.14` | Requested comparison |
| [Cloudflare Clef](https://openrouter.ai/cloudflare/clef) | `cloudflare/clef` | Requested comparison |
| [OpenAI GPT-6 Luna Decisions](https://openrouter.ai/openai/gpt-6-luna-decisions) | `openai/gpt-6-luna-decisions` | Requested comparison; originally the first target |
| [Cloudflare Clef Flash](https://openrouter.ai/cloudflare/clef-flash) | `cloudflare/clef-flash` | Optional additional speed comparison |

OpenRouter's OpenAI model page explicitly identifies this route as GPT-6 Luna served through OpenAI's Decisions API. It is separate from Chat Completions. OpenAI's [native Decisions guide](https://developers.openai.com/api/docs/guides/decisions) describes a different request shape at `POST /v1/decisions`; changing only an OpenAI SDK base URL would not implement the OpenRouter request contract.

These APIs return typed decisions, not tool calls. The local driver owns observation collection, calls the model, maps a chosen label to fixed steering/throttle/brake values, and sends the MCP command. All models receive the same observation content and control menu.

## Reproducible routing and measurements

The [OpenRouter OpenAPI specification](https://openrouter.ai/openapi.json) gives the alpha Decisions request a `provider` field supporting provider preferences, including `only`, `order`, and `allow_fallbacks`. Read exact provider slugs from the live endpoint catalog, pin the selected provider, and set `allow_fallbacks: false` for controlled comparisons. Record the actual response model and provider. [Routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection)

The Decisions response schema includes token usage and may include cost and request identity, but does not establish an observation-to-control timing measurement. Measure full response latency and action application locally. Disable automatic retries in timing runs and record refused, invalid, timed-out, and rate-limited attempts separately.

Provider routes and workload size affect latency. OpenRouter's displayed latency aggregates and vendors' own benchmarks are useful hypotheses, not measurements of this game's controls. Report model, provider, endpoint, observation size, date, local conditions, sample count, and cache warm-up conditions with results. The first comparison measures performance through OpenRouter, including its routing overhead.

Keep telemetry compact. The Cloudflare-hosted Clef routes' model pages warn about state-text truncation at roughly 2,000 tokens. Confirm the selected route's input handling and ensure no geometry or control instructions are silently omitted. Do not assume that a catalog context window describes every provider's effective handling. [Clef](https://openrouter.ai/cloudflare/clef), [Clef Flash](https://openrouter.ai/cloudflare/clef-flash)

## Controls and cost

Proposed: one joint choice from a small fixed menu combining steering positions with acceleration, coasting, or braking. The driver applies the chosen primitives directly; it does not execute a maneuver or follow a racing line. Control resolution is an experimental variable, so keep it identical across compared models.

Fetch current pricing for each pinned provider when preparing a run and record returned usage and cost where available. A model's cheapest advertised price may differ from the route used for a trial. Enforce a request/token bound as well as a spending estimate; a post-response usage report alone cannot prevent the final in-flight request from exceeding a threshold.

An API key can be placed in the repo's ignored `.env` file. Never store it in these notes, tracked configuration, prompts, or benchmark logs. No OpenAI API key is required for the OpenRouter route.
