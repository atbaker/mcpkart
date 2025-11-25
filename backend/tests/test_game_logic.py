"""Unit tests for game logic and models."""

import pytest

from mcpkart_backend.models import (
    GameState,
    PowerUp,
    RacerControls,
    RacerState,
    RacerStatus,
    Steering,
    Tile,
    TileType,
    Track,
)


class TestTrack:
    """Tests for Track model."""

    def test_create_oval(self):
        """Test oval track creation."""
        track = Track.create_oval()

        assert track.total_tiles == 20
        assert len(track.tiles) == 20

        # Check turns are at correct positions
        turn_tiles = [t for t in track.tiles if t.tile_type == TileType.TURN_LEFT]
        assert len(turn_tiles) == 4
        turn_indices = [t.index for t in turn_tiles]
        assert turn_indices == [4, 9, 14, 19]

        # Check item boxes are at correct positions
        item_tiles = [t for t in track.tiles if t.has_item_box]
        assert len(item_tiles) == 4
        item_indices = [t.index for t in item_tiles]
        assert item_indices == [0, 5, 10, 15]

    def test_tile_properties(self):
        """Test tile creation and properties."""
        tile = Tile(index=5, tile_type=TileType.STRAIGHT, has_item_box=True)

        assert tile.index == 5
        assert tile.tile_type == TileType.STRAIGHT
        assert tile.has_item_box is True


class TestRacerState:
    """Tests for RacerState model."""

    def test_default_values(self):
        """Test default racer state values."""
        racer = RacerState(player_id="test")

        assert racer.player_id == "test"
        assert racer.tile_index == 0
        assert racer.tile_subunit == 0
        assert racer.speed == 0
        assert racer.current_lap == 0
        assert racer.power_up is None
        assert racer.status == RacerStatus.RACING
        assert racer.finish_position is None

    def test_total_subunits(self):
        """Test total subunits calculation."""
        racer = RacerState(player_id="test")

        # At start
        assert racer.total_subunits == 0

        # After moving
        racer.tile_index = 5
        racer.tile_subunit = 2
        racer.current_lap = 1
        # Lap 1 = 60 subunits, tile 5 = 15 subunits, + 2 = 77
        assert racer.total_subunits == 60 + 15 + 2

    def test_effective_max_speed(self):
        """Test effective max speed with and without boost."""
        racer = RacerState(player_id="test")

        # Without boost
        assert racer.effective_max_speed == 3

        # With boost
        racer.boost_ticks_remaining = 3
        assert racer.effective_max_speed == 5

    def test_controls_default(self):
        """Test default control values."""
        racer = RacerState(player_id="test")

        assert racer.controls.accelerating is True
        assert racer.controls.braking is False
        assert racer.controls.steering == Steering.STRAIGHT

    def test_racer_with_power_up(self):
        """Test racer with power up."""
        racer = RacerState(player_id="test", power_up=PowerUp.SPEED_BOOST)

        assert racer.power_up == PowerUp.SPEED_BOOST


class TestRacerControls:
    """Tests for RacerControls model."""

    def test_default_values(self):
        """Test default control values."""
        controls = RacerControls()

        assert controls.accelerating is True
        assert controls.braking is False
        assert controls.steering == Steering.STRAIGHT
        assert controls.use_item is False


class TestGameState:
    """Tests for GameState model."""

    def test_default_values(self):
        """Test default game state values."""
        state = GameState(race_id="test-race")

        assert state.race_id == "test-race"
        assert state.current_tick == 0
        assert state.max_ticks == 180
        assert state.laps_required == 3
        assert state.track.total_tiles == 20
        assert len(state.racers) == 0
        assert len(state.standings) == 0

    def test_is_finished_no_racers(self):
        """Test is_finished with no racers."""
        state = GameState(race_id="test")

        # No racers = not finished
        assert state.is_finished is False

    def test_is_finished_all_racers_finished(self):
        """Test is_finished when all racers have finished."""
        state = GameState(race_id="test")
        state.racers["player1"] = RacerState(
            player_id="player1", status=RacerStatus.FINISHED
        )

        assert state.is_finished is True

    def test_is_finished_max_ticks(self):
        """Test is_finished when max ticks reached."""
        state = GameState(race_id="test")
        state.racers["player1"] = RacerState(player_id="player1")
        state.current_tick = 180

        assert state.is_finished is True

    def test_is_finished_race_in_progress(self):
        """Test is_finished when race is still in progress."""
        state = GameState(race_id="test")
        state.racers["player1"] = RacerState(player_id="player1")
        state.current_tick = 50

        assert state.is_finished is False

    def test_next_finish_position(self):
        """Test next finish position calculation."""
        state = GameState(race_id="test")

        assert state.next_finish_position == 1

        state.standings.append("player1")
        assert state.next_finish_position == 2

        state.standings.append("player2")
        assert state.next_finish_position == 3


class TestSteering:
    """Tests for Steering enum."""

    def test_steering_values(self):
        """Test steering enum values."""
        assert Steering.LEFT.value == "left"
        assert Steering.STRAIGHT.value == "straight"
        assert Steering.RIGHT.value == "right"


class TestPowerUp:
    """Tests for PowerUp enum."""

    def test_power_up_values(self):
        """Test power up enum values."""
        assert PowerUp.SPEED_BOOST.value == "speed_boost"


class TestRacerStatus:
    """Tests for RacerStatus enum."""

    def test_status_values(self):
        """Test racer status enum values."""
        assert RacerStatus.RACING.value == "racing"
        assert RacerStatus.CRASHED.value == "crashed"
        assert RacerStatus.FINISHED.value == "finished"
