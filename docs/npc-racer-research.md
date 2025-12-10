# NPC Racer Research

Research into options for adding AI-controlled NPC racers to MCP Kart races with fewer than 8 human players.

## Token Usage Estimates

Based on MCP tool response templates:

| Template | Approx Tokens |
|----------|---------------|
| `state.jinja2` (racing phase) | 600-800 |
| System instructions | ~400 |
| Tool definitions (5 tools) | ~500 |
| Model output (tool call) | ~80 |

**Per-race estimates** (assuming 4-minute race, 1 call/5 seconds = ~48 calls per NPC):
- **Input per NPC**: ~57,600 tokens (48 calls × 1,200 avg)
- **Output per NPC**: ~3,840 tokens (48 calls × 80)
- **7 NPCs per race**: ~403K input, ~27K output

---

## Option 1: Commercial CLI Agents (Subprocesses)

Spawn CLI agents (Claude Code, Gemini CLI, etc.) as subprocesses from the backend.

| Provider/Model | Input ($/1M) | Output ($/1M) | Cost/NPC/Race | Cost/Race (7 NPCs) |
|---------------|--------------|---------------|---------------|-------------------|
| **Claude Haiku 3** | $0.25 | $1.25 | $0.019 | **$0.13** |
| **Claude Haiku 3.5** | $0.80 | $4.00 | $0.061 | $0.43 |
| **Gemini 2.0 Flash** | $0.10 | $0.40 | $0.017 | **$0.12** |
| **Gemini 2.5 Flash** | $0.30 | $2.50 | $0.085 | $0.59 |
| **GPT-4o mini** | $0.15 | $0.60 | $0.011 | **$0.08** |
| **o3-mini** | $1.10 | $4.40 | $0.182 | $1.27 |
| **Claude Sonnet 4** | $3.00 | $15.00 | $0.578 | $4.05 |

**Pros**:
- Easiest to implement - just spawn CLI subprocesses
- Well-tested MCP support

**Cons**:
- Latency from API calls may slow NPC responses
- Depends on external services
- Rate limits could be an issue with many concurrent NPCs

**Best commercial options**: GPT-4o mini (~$0.08/race), Gemini 2.0 Flash (~$0.12/race), Claude Haiku 3 (~$0.13/race)

---

## Option 2: Third-Party Inference Providers (Groq, Together.ai)

Use inference providers with open-source models and custom MCP client integration.

| Provider | Model | Input ($/1M) | Output ($/1M) | Cost/Race (7 NPCs) |
|----------|-------|--------------|---------------|-------------------|
| **Groq** | Llama 3.3 70B | $0.59 | $0.79 | $0.26 |
| **Groq** | Qwen3 32B | ~$0.20 | ~$0.30 | ~$0.09 |
| **Together.ai** | Llama 3 8B | $0.10 | $0.10 | **$0.04** |
| **Together.ai** | Qwen 2.5 7B | $0.10 | $0.10 | **$0.04** |

**Pros**:
- Groq has extremely fast inference (~275 tokens/sec) - could actually outpace human players
- Together.ai has very cheap small models
- Supports open models with good tool-calling

**Cons**:
- Still external dependency
- May need custom integration with Goose or custom MCP client

---

## Option 3: Open Source CLI Agent - Goose

[Goose](https://github.com/block/goose) is Block's open-source AI agent with:
- Works with **any LLM** (local or API)
- Has **native MCP support** - a founding project of the Agentic AI Foundation alongside MCP itself
- Supports multi-model configuration
- Available as CLI or desktop app

**Architecture option**: Run Goose with different backends:
- Commercial APIs (Claude, GPT, Gemini)
- Third-party inference (Groq, Together.ai)
- Self-hosted models (Ollama, vLLM)

This gives a single codebase that can switch backends based on cost/performance needs.

---

## Option 4: Self-Hosted on GKE (GPU)

Deploy open-source models on GKE with GPU acceleration using vLLM.

| GPU | Memory | Spot Price/hr | Good For | Est. Cost/Race |
|-----|--------|---------------|----------|----------------|
| **L4** | 24GB | ~$0.21 | 7B-13B models | **$0.01-0.02** |
| **T4** | 16GB | ~$0.14 | 7B quantized | **$0.01** |
| **A100 40GB** | 40GB | ~$1.10 | 70B models | $0.07 |

**Recommended models for tool calling**:
- **Qwen 2.5 7B-Instruct**: Excellent structured output, good function calling
- **Llama 3.1 8B-Instruct**: Best overall for tool calling per Berkeley benchmarks
- **Qwen3 8B**: Newest, strong agentic capabilities

**Performance**: vLLM on L4 can achieve 50-100+ tokens/sec for 7B models, much faster than API round-trips

**Scale-to-zero**: With KEDA, you only pay when races are active

**Total cost**: At 10 races/day, ~$0.10-0.20/day (spot L4)

---

## Option 5: Self-Hosted on GKE (CPU - Quantized Models)

Run llama.cpp with quantized models on CPU instances.

| Instance | vCPUs | RAM | Price/hr | Tokens/sec (Q4 7B) |
|----------|-------|-----|----------|-------------------|
| n2-standard-8 | 8 | 32GB | $0.39 | ~5-8 |
| n2-standard-16 | 16 | 64GB | $0.78 | ~8-12 |
| c3-standard-8 | 8 | 32GB | $0.42 | ~8-12 |

**Using llama.cpp with Q4 quantized models**:
- 7B Q4_0: ~6-10 tokens/sec on modern x86 CPUs
- Memory bandwidth is the bottleneck

**⚠️ Concern**: At 5-10 tokens/sec, generating 80 output tokens takes 8-16 seconds. This is **too slow** for 1 call per 5 seconds. NPCs would fall behind significantly.

**Verdict**: CPU inference is likely **not viable** for real-time racing unless NPCs being slow/handicapped is acceptable (could actually be a feature to level the playing field).

---

## Cost Comparison Summary

Assuming 7 NPCs, 10 races/day, 30 days:

| Option | Cost/Race | Monthly Cost | Latency | Complexity |
|--------|-----------|--------------|---------|------------|
| GPT-4o mini | $0.08 | **$24** | Medium | Low |
| Gemini 2.0 Flash | $0.12 | $36 | Medium | Low |
| Claude Haiku 3 | $0.13 | $39 | Medium | Low |
| Together.ai (8B) | $0.04 | **$12** | Medium | Medium |
| Groq (32B) | $0.09 | $27 | **Very Low** | Medium |
| GKE L4 (spot) | $0.02 | **$6** | Low | High |
| GKE CPU | ~$0.03 | $9 | **High** | High |

---

## Recommendations

### For fastest implementation (days)
Use **Gemini CLI** or spawn **Claude Code** with Haiku - ~$30-40/month for moderate usage. The latency actually helps level the playing field with human-controlled racers running outside the infrastructure.

### For lowest cost with good performance (1-2 weeks)
Use **Goose + Together.ai/Groq** backend. ~$15-30/month, very fast inference from Groq.

### For lowest long-term cost and full control (2-4 weeks)
Self-host **Qwen 2.5 7B** or **Llama 3.1 8B** on GKE with **L4 spot instances** using vLLM. ~$6/month at 10 races/day, scales to zero when idle.

### Hybrid approach (recommended)
1. Start with commercial CLI agents (Gemini/Claude) for MVP
2. Build Goose integration as abstraction layer
3. Migrate to self-hosted as usage grows

---

## Additional Considerations

### Leveling the Playing Field
Adding network latency to NPC inference (as noted) could help balance races. Options:
- Artificial delays before submitting NPC tool calls
- Rate-limit NPC calls to match expected human cadence
- Use slower models intentionally for difficulty levels

### Personality/Difficulty
Different NPC "personalities" could use:
- Different models (faster/slower, smarter/dumber)
- Different system prompts (aggressive vs cautious racing)
- Different polling intervals

### MCP Client Implementation
If not using existing CLI agents, you'll need an MCP client. Options:
- Use Goose (recommended - native MCP support)
- Build minimal client with `mcp` Python package
- Adapt existing agent framework

---

## Sources

- [Claude API Pricing](https://costgoat.com/pricing/claude-api)
- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Groq Pricing](https://groq.com/pricing)
- [Together AI Pricing](https://www.together.ai/pricing)
- [Goose GitHub](https://github.com/block/goose)
- [GKE GPU Pricing](https://cloud.google.com/compute/vm-instance-pricing)
- [vLLM Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling/)
- [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)
- [Qwen Function Calling](https://qwen.readthedocs.io/en/latest/framework/function_call.html)
