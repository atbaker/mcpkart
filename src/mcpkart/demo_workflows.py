"""Deterministic Temporal orchestration; physics and paid effects live outside it."""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

NO_RETRY = RetryPolicy(maximum_attempts=1)
DRIVER_LABELS = {"red": "Jev", "blue": "OpenAI Decisions", "green": "Clef"}


@workflow.defn
class KartDriverWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        rid = config["racer_id"]
        for seq in range(config["max_decisions"] + 1):
            summary = f"{DRIVER_LABELS[rid]}: choose steering and pedals - decision {seq + 1}"
            workflow.set_current_details(summary)
            execute = workflow.execute_local_activity if config["local"] else workflow.execute_activity
            receipt = await execute(
                "kart_step", {"racer_id": rid, "seq": seq},
                schedule_to_close_timeout=timedelta(seconds=15), retry_policy=NO_RETRY,
                activity_id=f"{rid}-decision-{seq + 1:04d}", summary=summary,
            )
            workflow.set_current_details(receipt.get("summary", f"{DRIVER_LABELS[rid]}: step completed"))
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
            activity_id="start-race", summary="Start three ghost karts on the oval track",
        )
        children = []
        try:
            for rid in ("red", "blue", "green"):
                children.append(await workflow.start_child_workflow(
                    KartDriverWorkflow.run,
                    {"racer_id": rid, "max_decisions": config["max_decisions"], "local": config["local"]},
                    id=workflow.info().workflow_id + "-" + rid,
                    static_summary=f"{DRIVER_LABELS[rid]} drives the {rid} kart",
                ))
            await asyncio.gather(*children)
        except Exception as error:  # noqa: BLE001 - native errors are recorded by the broker
            workflow.logger.warning("Driver stopped; draining broker: %s", type(error).__name__)
        finally:
            # Stop admission and drain native replies before cancelling wrappers.
            receipt = await asyncio.shield(workflow.execute_activity(
                "kart_finish", start_to_close_timeout=timedelta(seconds=60), retry_policy=NO_RETRY,
                activity_id="finish-race", summary="Finish the race and audit every model control",
            ))
            for child in children:
                if not child.done():
                    child.cancel()
            await asyncio.gather(*children, return_exceptions=True)
        return receipt
