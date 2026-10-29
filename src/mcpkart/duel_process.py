"""Duel RPC adapter reusing the isolated, bounded publication transport."""

from .duel import RACERS, DuelSimulation
from .process_runtime import ProcessRaceRuntime


class ProcessDuelRuntime(ProcessRaceRuntime):
    worker_module = "mcpkart.duel_worker"

    def __init__(self, *, watchdog=False):
        super().__init__(watchdog=watchdog)
        preview = DuelSimulation()
        self._idle = {
            "status": "idle",
            "track": preview.track.as_dict(),
            "config": preview.config(),
            "observation": preview.state(),
        }

    def runtime_info(self):
        return {**super().runtime_info(), "protocol_version": 2, "mode": "duel"}

    async def observe(self, race_id=None, racer_id=None):
        self._check_race(race_id)
        if racer_id is not None and racer_id not in RACERS:
            raise ValueError("Unknown racer")
        if self._session is None:
            if self._result is None:
                raise ValueError("No duel has started")
            full = self._terminal_observation
            if racer_id is None:
                return {**full, "worker_closed": True}
            return {
                **full["racers"][racer_id],
                "race_id": full["race_id"],
                "racer_id": racer_id,
                "status": full["status"],
                "observed_ns": full["observed_ns"],
                "worker_closed": True,
            }
        return await self._rpc("observe", {"race_id": race_id, "racer_id": racer_id})

    async def drive(self, race_id, racer_id, driver_token, action_id, observation_tick, command_seq):
        self._check_race(race_id)
        if self._result is not None:
            return {
                "race_id": race_id,
                "racer_id": racer_id,
                "action_id": action_id,
                "command_seq": command_seq,
                "applied": False,
                "reason": "race_already_ended",
                "observation": await self.observe(race_id, racer_id),
            }
        return await self._rpc(
            "drive",
            {
                "race_id": race_id,
                "racer_id": racer_id,
                "driver_token": driver_token,
                "action_id": action_id,
                "observation_tick": observation_tick,
                "command_seq": command_seq,
            },
        )

    async def finish(self, race_id=None, reason="cancelled", owner_token=None):
        self._check_race(race_id)
        if self._result is not None:
            return self._result
        session = self._session
        try:
            value = await self._rpc(
                "finish", {"race_id": race_id, "reason": reason, "owner_token": owner_token}, session=session
            )
            result = self._decorate(value, session)
            if self._session is session:
                self._result = result
            return result
        except BaseException as error:
            # Invalid owner capabilities leave the active race alone. Other
            # failures must close the old worker before another admission.
            if not isinstance(error, ValueError):
                await self.close()
                self._worker_error = f"Duel finish failed ({type(error).__name__})"
            raise
        finally:
            if self._result is not None:
                await self._shutdown(session=session)
