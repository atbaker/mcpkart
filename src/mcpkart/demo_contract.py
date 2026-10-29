"""Small fixed model contract shared with the isolated AgentCore deployment."""

MODELS = ("typesafe/jev-1.14", "openai/gpt-6-luna-decisions", "cloudflare/clef")
PROVIDERS = dict(zip(MODELS, ("typesafe", "openai", "primeintellect"), strict=True))
