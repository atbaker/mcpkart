// Race state types for the spectator frontend
// Aligned with backend models

export type RaceStatus = 'lobby' | 'matchmaking' | 'planning' | 'racing' | 'finished';
export type RacerStatus = 'racing' | 'crashed' | 'finished';
export type TileType = 'straight' | 'turn_left';
export type PowerUp = 'mushroom' | 'banana' | 'shell';

export interface Racer {
	id: string;
	name: string;
	mcp_client: string;
	tile_index: number;
	tile_subunit: number;
	speed: number;
	current_lap: number;
	power_up: PowerUp | null;
	boost_ticks_remaining: number;
	status: RacerStatus;
	penalty_ticks_remaining: number;
	finish_position: number | null;
	finish_time: string | null;
	total_crashes: number;
	on_turn_tile: boolean;
	in_drift_zone: boolean;
	drift_enabled: boolean;
}

export interface Tile {
	index: number;
	tile_type: TileType;
	has_item_box: boolean;
}

export interface Track {
	tiles: Tile[];
}

export interface Standing {
	position: number;
	racer_id: string;
	name: string;
	mcp_client: string;
	lap: number;
	tile_index: number;
	status: RacerStatus;
	finish_time: string | null;
}

export interface SpectatorState {
	race_id: string;
	current_tick: number;
	max_ticks: number;
	laps_required: number;
	status: RaceStatus;
	is_public: boolean;
	race_clock: string;
	max_race_clock: string;
	matchmaking_ends_at: string | null;
	planning_ends_at: string | null;
	ready_players: string[];
	track: Track;
	racers: Racer[];
	standings: Standing[];
	events: string[];
}

// Replay types for viewing historical races

export interface TickRacerSnapshot {
	tile: number;
	subunit: number;
	speed: number;
	lap: number;
	status: RacerStatus;
}

export interface TickSnapshot {
	tick: number;
	racers: Record<string, TickRacerSnapshot>;
}

export interface RacerInfo {
	player_id: string;
	mcp_client: string;
	finish_position: number | null;
	finish_time: string | null;
	total_crashes: number;
}

export interface RacerHistory {
	tick_count: number;
	ticks: TickSnapshot[];
}

export interface ReplayData {
	race_id: string;
	total_ticks: number;
	max_ticks: number;
	laps_required: number;
	is_public: boolean;
	started_at: string | null;
	finished_at: string | null;
	standings: string[];
	events: string[];
	racers_info: Record<string, RacerInfo>;
	racer_history: RacerHistory;
	track: Track;
}
