"""Temporal workflow for MCP Kart races."""

import asyncio
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import pydantic_core.core_schema  # noqa: F401 - Pre-import for Temporal sandbox

    from mcpkart_backend.models import (
        GameState,
        PlayerInput,
        PowerUp,
        RacePhase,
        RacerState,
        RacerStatus,
        TileType,
        Track,
    )
    from mcpkart_backend.temporal.search_attributes import (
        IS_PUBLIC,
        PHASE,
        RACER_COUNT,
    )

# Lobby and planning phase durations
LOBBY_TIMEOUT = timedelta(hours=1)
MATCHMAKING_TIMEOUT = timedelta(minutes=5)
PLANNING_DURATION = timedelta(seconds=60)

# Turn tiles and their drift zones (3 tiles before each turn)
TURN_TILES = {7, 15, 29, 37}
DRIFT_ZONES = {4, 5, 6, 12, 13, 14, 26, 27, 28, 34, 35, 36}


@workflow.defn
class RaceWorkflow:
    """Temporal workflow representing a single race."""

    def __init__(self) -> None:
        self.game_state: GameState | None = None
        self.started_at = None
        self.enable_search_attrs = True

    def _log_event(self, message: str) -> None:
        """Add an event to the game log."""
        if self.game_state is not None:
            tick = self.game_state.current_tick
            self.game_state.events.append(f"[tick {tick}] {message}")

    def _update_drift_state(self, racer: RacerState) -> None:
        """Update drift zone and drift enabled state based on position."""
        current_tile = racer.tile_index

        # Check if in drift zone
        if current_tile in DRIFT_ZONES:
            if not racer.in_drift_zone:
                racer.in_drift_zone = True
                self._log_event(
                    f"{racer.player_id} entered drift zone at tile {current_tile}"
                )

            # Enable drift if control is set while in drift zone
            if racer.controls.drift and not racer.drift_enabled:
                racer.drift_enabled = True
                racer.controls.drift = False  # Consume the input
                self._log_event(f"{racer.player_id} enabled DRIFT in drift zone")
        else:
            # Exiting drift zone (but not into a turn)
            if racer.in_drift_zone and current_tile not in TURN_TILES:
                racer.in_drift_zone = False
                # drift_enabled stays true if heading into turn

    def _check_turn_entry(
        self, racer: RacerState, from_tile: int, to_tile: int
    ) -> bool:
        """Check if racer can safely enter/traverse turn. Returns False if crash."""
        if to_tile not in TURN_TILES:
            return True  # Not a turn, always safe

        # Entering or on turn tile
        if not racer.on_turn_tile:
            racer.on_turn_tile = True
            racer.in_drift_zone = False  # Clear drift zone flag when entering turn
            self._log_event(f"{racer.player_id} entering turn at tile {to_tile}")

        # Speed 1 is always safe
        if racer.speed <= 1:
            return True

        # Speed 2 with drift is safe
        if racer.speed == 2 and racer.drift_enabled:
            return True

        # Speed > 2, or speed 2 without drift = CRASH
        if racer.drift_enabled:
            reason = "too fast even with drift (max drift speed is 2)"
        else:
            reason = "too fast without drift enabled"
        self._crash_racer(racer, from_tile, to_tile, reason)
        return False

    def _check_turn_exit(self, racer: RacerState, from_tile: int, to_tile: int) -> None:
        """Handle exiting a turn tile."""
        if from_tile in TURN_TILES and to_tile not in TURN_TILES:
            # Successfully exited turn
            self._log_event(f"{racer.player_id} exited turn at tile {from_tile}")

            # Clear turn/drift state
            racer.on_turn_tile = False
            racer.in_drift_zone = False
            racer.drift_enabled = False

    def _crash_racer(
        self, racer: RacerState, from_tile: int, crash_tile: int, reason: str
    ) -> None:
        """Handle racer crash with penalty."""
        racer.tile_index = crash_tile
        racer.tile_subunit = 0
        racer.speed = 0
        racer.controls.target_speed = 0
        racer.penalty_ticks_remaining = 5
        racer.status = RacerStatus.CRASHED
        racer.boost_ticks_remaining = 0
        racer.total_crashes += 1

        # Clear turn/drift tracking
        racer.on_turn_tile = False
        racer.in_drift_zone = False
        racer.drift_enabled = False
        racer.controls.drift = False

        self._log_event(f"{racer.player_id} CRASHED at tile {crash_tile} - {reason}")

    def _upsert_search_attributes(self) -> None:
        """Update Temporal search attributes to reflect current state.

        Skipped when enable_search_attrs is False (for time-skipping tests).
        """
        if self.game_state is None or not self.enable_search_attrs:
            return

        workflow.upsert_search_attributes([
            IS_PUBLIC.value_set(self.game_state.is_public),
            PHASE.value_set(self.game_state.phase.value.upper()),
            RACER_COUNT.value_set(len(self.game_state.racers)),
        ])

    def _should_start_matchmaking_race(self) -> bool:
        """Check if matchmaking race should transition to PLANNING.

        Returns True if any of:
        - All players are ready
        - Lobby is full (8 players)
        - Matchmaking timeout expired
        """
        if self.game_state is None:
            return False

        # All players ready (and at least 1 player)
        all_ready = (
            len(self.game_state.ready_players) == len(self.game_state.racers)
            and len(self.game_state.racers) >= 1
        )
        if all_ready:
            return True

        # Lobby is full
        if self.game_state.is_lobby_full:
            return True

        # Timeout expired (handled by wait_condition timeout, but check anyway)
        if self.game_state.matchmaking_ends_at:
            if workflow.now() >= self.game_state.matchmaking_ends_at:
                return True

        return False

    @workflow.run
    async def run(
        self,
        race_id: str,
        creator_id: str,
        is_public: bool = False,
        enable_search_attrs: bool = True,
    ) -> GameState:
        """Main race lifecycle.

        Private races: LOBBY -> PLANNING -> RACING -> FINISHED
        Public races:  MATCHMAKING -> PLANNING -> RACING -> FINISHED

        Args:
            race_id: Unique race identifier
            creator_id: Player ID of the first player (host for private, just first joiner for public)
            is_public: True for public matchmaking, False for private lobbies
            enable_search_attrs: Whether to update Temporal search attributes (disable for time-skipping tests)
        """
        self.enable_search_attrs = enable_search_attrs
        now = workflow.now()

        # Initialize based on public/private
        initial_phase = RacePhase.MATCHMAKING if is_public else RacePhase.LOBBY

        self.game_state = GameState(
            race_id=race_id,
            phase=initial_phase,
            creator_id=creator_id if not is_public else None,  # No "host" for public races
            is_public=is_public,
            track=Track.create_oval(),
            created_at=now,
            lobby_expires_at=now + LOBBY_TIMEOUT if not is_public else None,
            matchmaking_ends_at=now + MATCHMAKING_TIMEOUT if is_public else None,
        )

        # Add creator as first racer
        self.game_state.racers[creator_id] = RacerState(player_id=creator_id)

        if is_public:
            self._log_event(f"Public matchmaking started by {creator_id}")
        else:
            self._log_event(f"Lobby created by {creator_id}")

        # Set initial search attributes
        self._upsert_search_attributes()

        if is_public:
            # MATCHMAKING PHASE: Wait for all ready, lobby full, or timeout
            try:
                await workflow.wait_condition(
                    self._should_start_matchmaking_race,
                    timeout=MATCHMAKING_TIMEOUT,
                )
            except asyncio.TimeoutError:
                # Timeout - start with whoever is here
                self._log_event("Matchmaking timeout - starting race")

            # Transition to PLANNING
            self.game_state.phase = RacePhase.PLANNING
            self.game_state.planning_ends_at = workflow.now() + PLANNING_DURATION
            self._upsert_search_attributes()

            if self.game_state.is_lobby_full:
                self._log_event("Lobby full - starting race")
            elif len(self.game_state.ready_players) == len(self.game_state.racers):
                self._log_event("All players ready - starting race")

        else:
            # LOBBY PHASE: Wait for start_race update or timeout
            try:
                await workflow.wait_condition(
                    lambda: self.game_state.phase != RacePhase.LOBBY,
                    timeout=LOBBY_TIMEOUT,
                )
            except asyncio.TimeoutError:
                # Lobby expired without starting
                self._log_event("Lobby expired after 1 hour")
                self.game_state.phase = RacePhase.FINISHED
                self._upsert_search_attributes()
                return self.game_state

        # PLANNING PHASE: 60-second countdown
        if self.game_state.phase == RacePhase.PLANNING:
            self._log_event("Planning phase started - 60 second countdown")
            await asyncio.sleep(PLANNING_DURATION.total_seconds())

            # Transition to RACING
            self.game_state.phase = RacePhase.RACING
            self.game_state.race_started_at = workflow.now()
            self.started_at = workflow.now()
            self._log_event("Race started!")

        # RACING PHASE: Main game loop
        while not self.game_state.is_finished:
            # Process tick
            self._process_tick()

            # Wait for next tick (1 second)
            await asyncio.sleep(1)

        # FINISHED
        self.game_state.phase = RacePhase.FINISHED
        self._upsert_search_attributes()
        finished_at = workflow.now()

        # Store results via activity
        await workflow.execute_activity(
            "store_race_results",
            args=[
                race_id,
                self.started_at.isoformat() if self.started_at else finished_at.isoformat(),
                finished_at.isoformat(),
                self.game_state.current_tick,
                self.game_state.max_ticks,
                self.game_state.laps_required,
                self.game_state.is_public,
                self.game_state.standings,
                self._get_racer_states(),
                self.game_state.events,
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
    async def join_lobby(self, player_id: str) -> GameState:
        """Add a player to the lobby or matchmaking.

        Args:
            player_id: Unique identifier provided by MCP client

        Returns:
            Updated game state
        """
        # Add the racer
        self.game_state.racers[player_id] = RacerState(player_id=player_id)

        if self.game_state.phase == RacePhase.MATCHMAKING:
            self._log_event(f"{player_id} joined matchmaking")
        else:
            self._log_event(f"{player_id} joined the lobby")

        # Update search attributes with new racer count
        self._upsert_search_attributes()

        return self.game_state

    @join_lobby.validator
    def _validate_join_lobby(self, player_id: str) -> None:
        """Validate join_lobby update before processing."""
        if self.game_state is None:
            raise ValueError("Game state not initialized")
        # Allow joining during LOBBY (private) or MATCHMAKING (public) phases
        if self.game_state.phase not in (RacePhase.LOBBY, RacePhase.MATCHMAKING):
            raise ValueError(
                f"Cannot join: race is in {self.game_state.phase.value} phase"
            )
        if player_id in self.game_state.racers:
            raise ValueError(f"Player {player_id} already in lobby")
        if self.game_state.is_lobby_full:
            raise ValueError(
                f"Lobby is full (max {self.game_state.max_racers} racers)"
            )

    @workflow.update
    async def start_race(self, player_id: str) -> GameState:
        """Start the race (transition from LOBBY to PLANNING).

        Only the lobby creator can start the race (private lobbies only).

        Args:
            player_id: Must match creator_id

        Returns:
            Updated game state with PLANNING phase
        """
        # Transition to PLANNING
        self.game_state.phase = RacePhase.PLANNING
        self.game_state.planning_ends_at = workflow.now() + PLANNING_DURATION
        self._log_event(f"{player_id} started the race - 60 second countdown")

        # Update search attributes
        self._upsert_search_attributes()

        return self.game_state

    @start_race.validator
    def _validate_start_race(self, player_id: str) -> None:
        """Validate start_race update before processing."""
        if self.game_state is None:
            raise ValueError("Game state not initialized")
        if self.game_state.phase != RacePhase.LOBBY:
            raise ValueError(
                f"Cannot start: race is in {self.game_state.phase.value} phase"
            )
        if player_id != self.game_state.creator_id:
            raise ValueError(
                f"Only the lobby creator ({self.game_state.creator_id}) can start the race"
            )
        if len(self.game_state.racers) < 1:
            raise ValueError("Cannot start race with no racers")

    @workflow.update
    async def apply_input(self, input_data: PlayerInput) -> GameState:
        """Update handler: apply player input immediately.

        Args:
            input_data: The input to apply
        """

        if input_data.player_id not in self.game_state.racers:
            raise ValueError(f"Unknown player: {input_data.player_id}")

        racer = self.game_state.racers[input_data.player_id]
        changes = []

        # Handle ready input (only during MATCHMAKING phase)
        if input_data.ready and self.game_state.phase == RacePhase.MATCHMAKING:
            if input_data.player_id not in self.game_state.ready_players:
                self.game_state.ready_players.add(input_data.player_id)
                changes.append("READY")

        # Handle race controls (only during PLANNING or RACING)
        if self.game_state.phase in (RacePhase.PLANNING, RacePhase.RACING):
            # Validate target_speed if present
            if input_data.target_speed is not None:
                if not (0 <= input_data.target_speed <= 5):  # Allow up to 5 for boost
                    raise ValueError(
                        f"Invalid target_speed {input_data.target_speed} (must be 0-5)"
                    )
                # Also validate against effective_max_speed
                if input_data.target_speed > racer.effective_max_speed:
                    raise ValueError(
                        f"Invalid target_speed (must be 0-{racer.effective_max_speed})"
                    )

            # Apply input immediately
            controls = racer.controls

            if input_data.target_speed is not None:
                controls.target_speed = input_data.target_speed
                changes.append(f"target_speed={input_data.target_speed}")

            # Handle drift input - valid in drift zone or on turn tile
            if input_data.drift:
                if racer.in_drift_zone or racer.on_turn_tile:
                    # Valid location - enable drift
                    controls.drift = True
                    if racer.on_turn_tile:
                        changes.append("drift enabled (late, on turn)")
                    else:
                        changes.append("drift requested")
                else:
                    # Invalid location - crash for early drift
                    self._crash_racer(
                        racer,
                        racer.tile_index,
                        racer.tile_index,
                        "early drift (not in drift zone or turn)"
                    )
                    changes.append("CRASHED - early drift")

            if input_data.use_item:
                controls.use_item = True
                changes.append("use item")

        if changes:
            self._log_event(f"{input_data.player_id}: {', '.join(changes)}")

        return self.game_state

    @apply_input.validator
    def _validate_apply_input(self, input_data: PlayerInput) -> None:
        """Validate apply_input update before processing."""
        if self.game_state is None:
            raise ValueError("Game state not initialized")
        # Allow input during MATCHMAKING (for ready), PLANNING, or RACING
        if self.game_state.phase not in (
            RacePhase.MATCHMAKING,
            RacePhase.PLANNING,
            RacePhase.RACING,
        ):
            raise ValueError(
                f"Cannot control: race is in {self.game_state.phase.value} phase"
            )

    def _process_tick(self) -> None:
        """Process one game tick: update all racers."""
        if self.game_state is None:
            return

        self.game_state.current_tick += 1

        # Process each racer
        for racer in self.game_state.racers.values():
            # Update drift state based on current position (before movement)
            self._update_drift_state(racer)

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

                # Update drift state for new tile
                self._update_drift_state(racer)

                # Check turn entry/traversal (may cause crash)
                if not self._check_turn_entry(racer, old_tile_index, racer.tile_index):
                    return  # Crashed

                # Check turn exit
                self._check_turn_exit(racer, old_tile_index, racer.tile_index)

                # Check for item box
                new_tile = self.game_state.track.tiles[racer.tile_index]
                if new_tile.has_item_box and racer.power_up is None:
                    racer.power_up = PowerUp.SPEED_BOOST  # Only one power-up for now
                    self._log_event(
                        f"{racer.player_id} picked up SPEED_BOOST (tile {racer.tile_index})"
                    )
                elif new_tile.has_item_box and racer.power_up is not None:
                    self._log_event(
                        f"{racer.player_id} passed item box but already has {racer.power_up.value} (tile {racer.tile_index})"
                    )

    def _get_racer_states(self) -> list[dict]:
        """Get full state for all racers for storing in database."""
        if self.game_state is None:
            return []

        states = []
        for player_id, racer in self.game_state.racers.items():
            states.append({
                "player_id": player_id,
                "tile_index": racer.tile_index,
                "tile_subunit": racer.tile_subunit,
                "speed": racer.speed,
                "current_lap": racer.current_lap,
                "finish_position": racer.finish_position,
                "finish_tick": racer.finish_tick,
                "finish_time": racer.finish_time,
                "total_crashes": racer.total_crashes,
                "items_used": racer.items_used,
            })
        return states
