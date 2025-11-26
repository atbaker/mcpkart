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

    def _auto_reset_steering(self) -> None:
        """Auto-reset steering to STRAIGHT after LEFT/RIGHT inputs."""
        if self.game_state is None:
            return

        for racer in self.game_state.racers.values():
            if racer.controls.steering in (Steering.LEFT, Steering.RIGHT):
                old_steering = racer.controls.steering
                racer.controls.steering = Steering.STRAIGHT
                self._log_event(
                    f"{racer.player_id} steering auto-reset: "
                    f"{old_steering.value} -> straight"
                )

    def _apply_scheduled_inputs(self) -> None:
        """Apply scheduled inputs for current tick."""
        if self.game_state is None:
            return

        current_tick = self.game_state.current_tick

        for player_id in list(self.game_state.scheduled_inputs.keys()):
            player_schedule = self.game_state.scheduled_inputs[player_id]

            # Check if there's an input for this tick
            if current_tick not in player_schedule:
                continue

            input_data = player_schedule.pop(current_tick)

            # Clean up empty player schedules
            if not player_schedule:
                del self.game_state.scheduled_inputs[player_id]

            # Apply the input
            racer = self.game_state.racers.get(player_id)
            if not racer:
                continue

            changes = []
            if input_data.target_speed is not None:
                racer.controls.target_speed = input_data.target_speed
                changes.append(f"target_speed={input_data.target_speed}")
            if input_data.steering is not None:
                racer.controls.steering = input_data.steering
                changes.append(f"steer {input_data.steering.value}")
            if input_data.use_item:
                racer.controls.use_item = True
                changes.append("use item")

            if changes:
                self._log_event(
                    f"{player_id} [SCHEDULED tick {current_tick}]: {', '.join(changes)}"
                )

    def _crash_racer(
        self, racer: RacerState, from_tile: int, crash_tile: int, reason: str
    ) -> None:
        """Handle racer crash with penalty."""
        racer.tile_index = from_tile
        racer.tile_subunit = 0
        racer.speed = 0
        racer.controls.target_speed = 0
        racer.penalty_ticks_remaining = 2
        racer.status = RacerStatus.CRASHED
        racer.boost_ticks_remaining = 0
        racer.total_crashes += 1

        # Clear turn tracking
        racer.on_turn_tile = False
        racer.steered_left_during_turn = False
        racer.turn_entry_tick = None

        self._log_event(f"{racer.player_id} CRASHED at tile {crash_tile} - {reason}")

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
    async def apply_input(
        self, input_data: PlayerInput, execute_at_tick: int | None = None
    ) -> GameState:
        """Update handler: apply player input immediately or schedule for future tick.

        Args:
            input_data: The input to apply
            execute_at_tick: If set, schedule input for this tick. If None, apply immediately.
        """
        if self.game_state is None:
            raise ValueError("Game state not initialized")

        if input_data.player_id not in self.game_state.racers:
            raise ValueError(f"Unknown player: {input_data.player_id}")

        racer = self.game_state.racers[input_data.player_id]
        current_tick = self.game_state.current_tick

        # Validate target_speed if present
        if input_data.target_speed is not None:
            if not (0 <= input_data.target_speed <= 5):  # Allow up to 5 for boost
                raise ValueError(
                    f"Invalid target_speed {input_data.target_speed} (must be 0-5)"
                )

        # If execute_at_tick is set, schedule the input
        if execute_at_tick is not None:
            # Validate tick timing
            if execute_at_tick <= current_tick:
                raise ValueError(
                    f"Cannot schedule for past/current tick {execute_at_tick} "
                    f"(current: {current_tick})"
                )
            if execute_at_tick > current_tick + 20:
                raise ValueError(
                    f"Cannot schedule more than 20 ticks ahead "
                    f"(target: {execute_at_tick}, current: {current_tick})"
                )

            # Store scheduled input
            if input_data.player_id not in self.game_state.scheduled_inputs:
                self.game_state.scheduled_inputs[input_data.player_id] = {}

            self.game_state.scheduled_inputs[input_data.player_id][
                execute_at_tick
            ] = input_data

            self._log_event(
                f"{input_data.player_id} scheduled input for tick {execute_at_tick}"
            )
            return self.game_state

        # Otherwise apply immediately
        controls = racer.controls
        changes = []

        if input_data.target_speed is not None:
            # Also validate against effective_max_speed for immediate application
            if input_data.target_speed > racer.effective_max_speed:
                raise ValueError(
                    f"Invalid target_speed (must be 0-{racer.effective_max_speed})"
                )
            controls.target_speed = input_data.target_speed
            changes.append(f"target_speed={input_data.target_speed}")

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

        # Process in order: reset old steering, apply new scheduled inputs
        self._auto_reset_steering()
        self._apply_scheduled_inputs()

        # Track steering on turn tiles BEFORE movement
        for racer in self.game_state.racers.values():
            if racer.on_turn_tile and racer.controls.steering == Steering.LEFT:
                if not racer.steered_left_during_turn:
                    racer.steered_left_during_turn = True
                    self._log_event(
                        f"{racer.player_id} steering LEFT on turn tile {racer.tile_index}"
                    )

        # Process each racer
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
        """Update racer speed toward target_speed with asymmetric acceleration/braking."""
        target = min(racer.controls.target_speed, racer.effective_max_speed)

        if racer.speed < target:
            # Accelerate: +1 per tick
            racer.speed = min(racer.speed + 1, target)
        elif racer.speed > target:
            # Brake: up to -2 per tick (faster braking for better turn handling)
            brake_amount = min(2, racer.speed - target)
            racer.speed = racer.speed - brake_amount

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
                        self._log_event(
                            f"{racer.player_id} FINISHED in position "
                            f"{racer.finish_position}!"
                        )
                        return
                    else:
                        self._log_event(
                            f"{racer.player_id} completed lap "
                            f"{racer.current_lap}/{self.game_state.laps_required}"
                        )

                # Get new tile
                new_tile = self.game_state.track.tiles[racer.tile_index]

                # Track turn tile entry
                if new_tile.tile_type == TileType.TURN_LEFT and not racer.on_turn_tile:
                    racer.on_turn_tile = True
                    racer.steered_left_during_turn = False
                    racer.turn_entry_tick = self.game_state.current_tick
                    self._log_event(
                        f"{racer.player_id} entered turn at tile {racer.tile_index}"
                    )

                # Validate speed continuously on turn tiles (crash if speed > 1)
                if racer.on_turn_tile and racer.speed > 1:
                    self._crash_racer(
                        racer, old_tile_index, racer.tile_index, "too fast (speed > 1)"
                    )
                    return

                # Check turn exit - validate steering
                if racer.on_turn_tile and new_tile.tile_type != TileType.TURN_LEFT:
                    # Exiting turn - check if steered left at any point
                    if not racer.steered_left_during_turn:
                        self._crash_racer(
                            racer,
                            old_tile_index,
                            old_tile_index,  # Crash at the turn tile we're leaving
                            "didn't steer left during turn",
                        )
                        return
                    # Success - clear turn tracking
                    racer.on_turn_tile = False
                    racer.steered_left_during_turn = False
                    racer.turn_entry_tick = None

                # Check for item box
                if new_tile.has_item_box and racer.power_up is None:
                    racer.power_up = PowerUp.SPEED_BOOST  # Only one power-up for now
                    self._log_event(
                        f"{racer.player_id} picked up SPEED_BOOST (tile {racer.tile_index})"
                    )

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
