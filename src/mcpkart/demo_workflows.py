"""Deterministic Temporal orchestration; physics and paid effects live outside it."""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

NO_RETRY = RetryPolicy(maximum_attempts=1)


@workflow.defn
class KartDriverWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        for seq in range(config["max_decisions"] + 1):
            execute = workflow.execute_local_activity if config["local"] else workflow.execute_activity
            receipt = await execute(
                "kart_step", {"racer_id": config["racer_id"], "seq": seq},
                schedule_to_close_timeout=timedelta(seconds=15), retry_policy=NO_RETRY,
            )
            if receipt["done"]:
                return {"racer_id": config["racer_id"], "decisions": seq,
                        "retired": receipt.get("retired", False)}
            # Flush bounded batches of local markers and allow signals/cancellation.
            if config["local"] and seq % 8 == 7:
                await workflow.sleep(.001)
        raise RuntimeError("Broker must reject dispatch beyond its finite ceiling")


@workflow.defn
class KartRaceWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        await workflow.execute_activity(
            "kart_start", start_to_close_timeout=timedelta(seconds=45), retry_policy=NO_RETRY,
        )
        children = []
        try:
            for rid in ("red", "blue", "green"):
                children.append(await workflow.start_child_workflow(
                    KartDriverWorkflow.run,
                    {"racer_id": rid, "max_decisions": config["max_decisions"], "local": config["local"]},
                    id=workflow.info().workflow_id + "-" + rid,
                ))
            await asyncio.gather(*children)
        except Exception as error:  # noqa: BLE001 - native errors are recorded by the broker
            workflow.logger.warning("Driver stopped; draining broker: %s", type(error).__name__)
        finally:
            # Stop admission and drain native replies before cancelling wrappers.
            receipt = await asyncio.shield(workflow.execute_activity(
                "kart_finish", start_to_close_timeout=timedelta(seconds=60), retry_policy=NO_RETRY,
            ))
            for child in children:
                if not child.done():
                    child.cancel()
            await asyncio.gather(*children, return_exceptions=True)
        return receipt
