"""Temporal workflow for MCP Kart races."""

import asyncio
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from mcpkart_backend.models import (
        GameState,
        PlayerInput,
        PowerUp,
        RacerState,
        RacerStatus,
        Steering,
        TileType,
        Track,
    )


@workflow.defn
class RaceWorkflow:
    """Temporal workflow representing a single race."""

    def __init__(self) -> None:
        self.game_state: GameState | None = None
        self.started_at = None

    def _log_event(self, message: str) -> None:
        """Add an event to the game log."""
        if self.game_state is not None:
            tick = self.game_state.current_tick
            self.game_state.events.append(f"[tick {tick}] {message}")

    @workflow.run
    async def run(self, race_id: str, player_ids: list[str]) -> GameState:
        """Main race loop."""
        self.started_at = workflow.now()

        # Initialize game state
        self.game_state = GameState(race_id=race_id, track=Track.create_oval())
        for player_id in player_ids:
            self.game_state.racers[player_id] = RacerState(player_id=player_id)

        # Main game loop
        while not self.game_state.is_finished:
            # Process tick
            self._process_tick()

            # Wait for next tick (1 second)
            await asyncio.sleep(1)

        finished_at = workflow.now()

        # Store results via activity
        await workflow.execute_activity(
            "store_race_results",
            args=[
                race_id,
                self.started_at.isoformat(),
                finished_at.isoformat(),
                self.game_state.current_tick,
                self.game_state.standings,
                self._get_racer_stats(),
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return self.game_state

    @workflow.query
    def get_state(self) -> GameState:
        """Query handler: return current game state."""
        if self.game_state is None:
            raise ValueError("Game state not initialized")
        return self.game_state

    @workflow.update
    async def apply_input(self, input_data: PlayerInput) -> GameState:
        """Update handler: apply player input and return current state."""
        if self.game_state is None:
            raise ValueError("Game state not initialized")

        if input_data.player_id not in self.game_state.racers:
            raise ValueError(f"Unknown player: {input_data.player_id}")

        racer = self.game_state.racers[input_data.player_id]
        controls = racer.controls

        # Apply input (None means "don't change") and log changes
        changes = []
        if input_data.accelerating is not None and controls.accelerating != input_data.accelerating:
            controls.accelerating = input_data.accelerating
            changes.append("accelerate" if input_data.accelerating else "stop accelerating")
        if input_data.braking is not None and controls.braking != input_data.braking:
            controls.braking = input_data.braking
            changes.append("brake" if input_data.braking else "stop braking")
        if input_data.steering is not None and controls.steering != input_data.steering:
            controls.steering = input_data.steering
            changes.append(f"steer {input_data.steering.value}")
        if input_data.use_item:
            controls.use_item = True
            changes.append("use item")

        if changes:
            self._log_event(f"{input_data.player_id}: {', '.join(changes)}")

        return self.game_state

    def _process_tick(self) -> None:
        """Process one game tick: update all racers."""
        if self.game_state is None:
            return

        self.game_state.current_tick += 1

        for racer in self.game_state.racers.values():
            if racer.status == RacerStatus.FINISHED:
                continue

            # Handle penalty cooldown
            if racer.penalty_ticks_remaining > 0:
                racer.penalty_ticks_remaining -= 1
                racer.status = (
                    RacerStatus.CRASHED
                    if racer.penalty_ticks_remaining > 0
                    else RacerStatus.RACING
                )
                continue

            # Handle boost countdown
            if racer.boost_ticks_remaining > 0:
                racer.boost_ticks_remaining -= 1

            # Process item use
            if racer.controls.use_item and racer.power_up == PowerUp.SPEED_BOOST:
                racer.boost_ticks_remaining = 3
                racer.power_up = None
                racer.controls.use_item = False
                racer.items_used += 1
                self._log_event(f"{racer.player_id} used SPEED_BOOST")

            # Clear use_item flag if no item to use
            if racer.controls.use_item and racer.power_up is None:
                racer.controls.use_item = False

            # Update speed based on controls
            self._update_speed(racer)

            # Move racer
            self._move_racer(racer)

    def _update_speed(self, racer: RacerState) -> None:
        """Update racer speed based on controls."""
        if racer.controls.accelerating and not racer.controls.braking:
            racer.speed = min(racer.speed + 1, racer.effective_max_speed)
        elif racer.controls.braking and not racer.controls.accelerating:
            racer.speed = max(racer.speed - 1, 0)
        # If both or neither: speed unchanged

    def _move_racer(self, racer: RacerState) -> None:
        """Move racer based on current speed, handle turns and items."""
        if self.game_state is None:
            return

        subunits_to_move = racer.speed
        if racer.boost_ticks_remaining > 0:
            subunits_to_move = 5  # Boost overrides normal speed

        while subunits_to_move > 0:
            # Move one subunit
            racer.tile_subunit += 1
            subunits_to_move -= 1

            # Check if crossed into new tile
            if racer.tile_subunit >= 3:
                racer.tile_subunit = 0
                old_tile_index = racer.tile_index
                racer.tile_index = (
                    racer.tile_index + 1
                ) % self.game_state.track.total_tiles

                # Check for lap completion (crossing from last tile to first)
                if (
                    racer.tile_index == 0
                    and old_tile_index == self.game_state.track.total_tiles - 1
                ):
                    racer.current_lap += 1
                    if racer.current_lap >= self.game_state.laps_required:
                        racer.status = RacerStatus.FINISHED
                        racer.finish_position = self.game_state.next_finish_position
                        racer.finish_tick = self.game_state.current_tick
                        self.game_state.standings.append(racer.player_id)
                        self._log_event(f"{racer.player_id} FINISHED in position {racer.finish_position}!")
                        return
                    else:
                        self._log_event(f"{racer.player_id} completed lap {racer.current_lap}/{self.game_state.laps_required}")

                # Get new tile
                new_tile = self.game_state.track.tiles[racer.tile_index]

                # Check for turn handling
                if new_tile.tile_type == TileType.TURN_LEFT:
                    # Must be at speed 1 and steering left
                    was_too_fast = racer.speed > 1
                    was_not_steering = racer.controls.steering != Steering.LEFT
                    if was_too_fast or was_not_steering:
                        # Crash! Reset to previous tile
                        crash_tile = racer.tile_index
                        racer.tile_index = old_tile_index
                        racer.tile_subunit = 0
                        racer.speed = 0
                        racer.penalty_ticks_remaining = 2
                        racer.status = RacerStatus.CRASHED
                        racer.boost_ticks_remaining = 0  # Lose boost on crash
                        racer.controls.accelerating = False  # Stop accelerating after crash
                        racer.total_crashes += 1
                        reason = "too fast" if was_too_fast else "not steering left"
                        self._log_event(f"{racer.player_id} CRASHED at turn (tile {crash_tile}) - {reason}")
                        return

                # Check for item box
                if new_tile.has_item_box and racer.power_up is None:
                    racer.power_up = PowerUp.SPEED_BOOST  # Only one power-up for now
                    self._log_event(f"{racer.player_id} picked up SPEED_BOOST (tile {racer.tile_index})")

    def _get_racer_stats(self) -> dict[str, dict]:
        """Get stats for all racers for storing in database."""
        if self.game_state is None:
            return {}

        stats = {}
        for player_id, racer in self.game_state.racers.items():
            stats[player_id] = {
                "finish_position": racer.finish_position,
                "finish_tick": racer.finish_tick,
                "total_crashes": racer.total_crashes,
                "items_used": racer.items_used,
            }
        return stats
