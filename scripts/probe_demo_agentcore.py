"""Three free native-contract probes against the dedicated AgentCore mock."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from mcpkart.demo_contract import MODELS, PROVIDERS
from mcpkart.demo_transport import AgentCoreTransport
from mcpkart.duel import TRIO_RACERS, DuelSimulation
from mcpkart.duel_decisions import DuelDecisionClient, duel_facts


async def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")

    async def probe(rid, model):
        api = DuelDecisionClient(facts=duel_facts(sim.observation(rid), sim.config(), rid),
                                 handling=sim.config()["handling"], budget=None,
                                 http_client=object(), api_key="free-placeholder")
        transport = AgentCoreTransport(args.arn, args.region, rid, args.session_prefix,
                                       evidence_path=output / rid)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.post("https://openrouter.ai/api/alpha/decisions", json={
                "model": model, "state": {}, "questions": api.questions,
                "provider": {"only": [PROVIDERS[model]], "allow_fallbacks": False},
            })
        response.raise_for_status()
        native = response.json()
        assert native["model"] == model + "-mock"
        assert native["usage"] == {"input_tokens": 0, "output_tokens": 0, "cost": 0}
        for head in ("wheel", "pedal"):
            assert native["answers"][head]["choice"] in api.component_criteria[head]
        return {"racer_id": rid, "session_id": transport.session,
                "model": native["model"], "provider": native["provider"], "passed": True}

    result = await asyncio.gather(*(probe(r, m) for r, m in zip(TRIO_RACERS, MODELS, strict=True)))
    (output / "receipt.json").write_text(json.dumps({"model_requests": 0, "probes": result}, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arn", required=True)
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--session-prefix", default="mcpkart-agentcore-probe-v1")
    parser.add_argument("--output", required=True)
    asyncio.run(run(parser.parse_args()))
