<script lang="ts">
	import { page } from '$app/state';
	import TrackViewSVG from '$lib/components/TrackViewSVG.svelte';
	import Standings from '$lib/components/Standings.svelte';
	import EventLog from '$lib/components/EventLog.svelte';
	import ReplayControls from '$lib/components/ReplayControls.svelte';
	import type { SpectatorState, ReplayData, Racer, Standing, RacerStatus } from '$lib/types';

	let raceState = $state<SpectatorState | null>(null);
	let replayData = $state<ReplayData | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);
	let now = $state(Date.now());

	// Replay state
	let replayTick = $state(0);
	let isPlaying = $state(false);
	let playbackSpeed = $state(1);
	let playbackInterval = $state<ReturnType<typeof setInterval> | null>(null);

	const raceId = $derived(page.params.id);

	// Check if we have replay data available
	const hasReplay = $derived(replayData !== null && replayData.racer_history?.ticks?.length > 0);

	// Check if race is finished
	const isFinished = $derived(raceState?.status === 'finished');

	// Compute planning countdown
	const planningCountdown = $derived(() => {
		if (!raceState?.planning_ends_at) return null;
		const endsAt = new Date(raceState.planning_ends_at).getTime();
		const remaining = Math.max(0, Math.ceil((endsAt - now) / 1000));
		return remaining;
	});

	// Compute matchmaking countdown
	const matchmakingCountdown = $derived(() => {
		if (!raceState?.matchmaking_ends_at) return null;
		const endsAt = new Date(raceState.matchmaking_ends_at).getTime();
		const remaining = Math.max(0, Math.ceil((endsAt - now) / 1000));
		return remaining;
	});

	// Compute ready count for matchmaking
	const readyCount = $derived(() => {
		if (!raceState) return { ready: 0, total: 0 };
		return {
			ready: raceState.ready_players?.length || 0,
			total: raceState.racers?.length || 0
		};
	});

	// Build racers array from replay data at current tick
	function buildRacersFromReplay(tick: number): Racer[] {
		if (!replayData) return [];

		// Find the snapshot for this tick
		const snapshot = replayData.racer_history.ticks.find((t) => t.tick === tick);
		if (!snapshot) {
			// If no exact match, use the last available tick
			const lastSnapshot = replayData.racer_history.ticks[replayData.racer_history.ticks.length - 1];
			if (!lastSnapshot) return [];
			return buildRacersFromSnapshot(lastSnapshot.racers);
		}

		return buildRacersFromSnapshot(snapshot.racers);
	}

	function buildRacersFromSnapshot(racersSnapshot: Record<string, { tile: number; subunit: number; speed: number; lap: number; status: RacerStatus }>): Racer[] {
		if (!replayData) return [];

		return Object.entries(racersSnapshot).map(([playerId, snapshot]) => {
			const info = replayData!.racers_info[playerId];
			return {
				id: playerId,
				name: playerId,
				mcp_client: info?.mcp_client || 'unknown',
				tile_index: snapshot.tile,
				tile_subunit: snapshot.subunit,
				speed: snapshot.speed,
				current_lap: snapshot.lap,
				power_up: null,
				boost_ticks_remaining: 0,
				status: snapshot.status,
				penalty_ticks_remaining: 0,
				finish_position: info?.finish_position || null,
				finish_time: info?.finish_time || null,
				total_crashes: info?.total_crashes || 0,
				on_turn_tile: false,
				in_drift_zone: false,
				drift_enabled: false
			};
		});
	}

	// Build standings from replay data at current tick
	function buildStandingsFromReplay(tick: number): Standing[] {
		const racers = buildRacersFromReplay(tick);
		if (!replayData) return [];

		// Sort racers by: finished (by position), then by lap desc, then by tile desc
		const sorted = [...racers].sort((a, b) => {
			// Finished racers first, sorted by position
			if (a.status === 'finished' && b.status === 'finished') {
				return (a.finish_position || 999) - (b.finish_position || 999);
			}
			if (a.status === 'finished') return -1;
			if (b.status === 'finished') return 1;

			// Then by lap (desc)
			if (a.current_lap !== b.current_lap) {
				return b.current_lap - a.current_lap;
			}

			// Then by tile position (desc)
			return b.tile_index - a.tile_index;
		});

		return sorted.map((racer, index) => ({
			position: index + 1,
			racer_id: racer.id,
			name: racer.name,
			mcp_client: racer.mcp_client,
			lap: racer.current_lap,
			tile_index: racer.tile_index,
			status: racer.status,
			finish_time: racer.finish_time
		}));
	}

	// Filter events up to current replay tick
	function filterEventsForTick(tick: number): string[] {
		if (!replayData) return [];

		// Events are formatted as "[tick N] message"
		return replayData.events.filter((event) => {
			const match = event.match(/^\[tick (\d+)\]/);
			if (!match) return true; // Include events without tick prefix
			const eventTick = parseInt(match[1], 10);
			return eventTick <= tick;
		});
	}

	// Computed values for replay mode
	const displayRacers = $derived(
		hasReplay && isFinished ? buildRacersFromReplay(replayTick) : raceState?.racers || []
	);

	const displayStandings = $derived(
		hasReplay && isFinished ? buildStandingsFromReplay(replayTick) : raceState?.standings || []
	);

	const displayEvents = $derived(
		hasReplay && isFinished ? filterEventsForTick(replayTick) : raceState?.events || []
	);

	const displayTick = $derived(hasReplay && isFinished ? replayTick : raceState?.current_tick || 0);

	// Format tick as race clock
	function formatRaceClock(tick: number): string {
		const minutes = Math.floor(tick / 60);
		const seconds = tick % 60;
		return `${minutes}:${seconds.toString().padStart(2, '0')}`;
	}

	// Replay control handlers
	function handleTickChange(tick: number) {
		replayTick = tick;
		// Stop playback when manually seeking
		if (isPlaying) {
			handlePlayPause();
		}
	}

	function handlePlayPause() {
		isPlaying = !isPlaying;

		if (isPlaying) {
			// Start playback
			const intervalMs = 1000 / playbackSpeed;
			playbackInterval = setInterval(() => {
				if (replayData && replayTick < replayData.total_ticks) {
					replayTick += 1;
				} else {
					// Reached end, stop playback
					isPlaying = false;
					if (playbackInterval) {
						clearInterval(playbackInterval);
						playbackInterval = null;
					}
				}
			}, intervalMs);
		} else {
			// Stop playback
			if (playbackInterval) {
				clearInterval(playbackInterval);
				playbackInterval = null;
			}
		}
	}

	function handleSpeedChange(speed: number) {
		playbackSpeed = speed;
		// If playing, restart interval with new speed
		if (isPlaying && playbackInterval) {
			clearInterval(playbackInterval);
			const intervalMs = 1000 / speed;
			playbackInterval = setInterval(() => {
				if (replayData && replayTick < replayData.total_ticks) {
					replayTick += 1;
				} else {
					isPlaying = false;
					if (playbackInterval) {
						clearInterval(playbackInterval);
						playbackInterval = null;
					}
				}
			}, intervalMs);
		}
	}

	// Update `now` every second for countdown
	$effect(() => {
		const interval = setInterval(() => {
			now = Date.now();
		}, 1000);
		return () => clearInterval(interval);
	});

	// Poll for race state every second (stops when race is finished)
	$effect(() => {
		let active = true;
		let interval: ReturnType<typeof setInterval> | null = null;

		async function poll() {
			try {
				const res = await fetch(`/api/races/${raceId}/spectator-state`);
				if (!res.ok) {
					const text = await res.text();
					throw new Error(`HTTP ${res.status}: ${text}`);
				}
				if (active) {
					const state: SpectatorState = await res.json();
					raceState = state;
					error = null;
					loading = false;

					// Stop polling once race is finished
					if (state.status === 'finished' && interval) {
						clearInterval(interval);
						interval = null;
					}
				}
			} catch (e) {
				if (active) {
					error = e instanceof Error ? e.message : 'Unknown error';
					loading = false;
				}
			}
		}

		// Initial fetch
		poll();

		// Poll every second
		interval = setInterval(poll, 1000);

		return () => {
			active = false;
			if (interval) clearInterval(interval);
		};
	});

	// Fetch replay data when race is finished
	$effect(() => {
		if (!isFinished || replayData) return;

		async function fetchReplay() {
			try {
				const res = await fetch(`/api/races/${raceId}/replay`);
				if (res.ok) {
					const data: ReplayData = await res.json();
					replayData = data;
					// Start at the beginning
					replayTick = 0;
				}
				// If replay fetch fails, that's okay - we just won't show replay controls
			} catch {
				// Ignore errors - replay is optional
			}
		}

		fetchReplay();
	});

	// Cleanup playback interval on unmount
	$effect(() => {
		return () => {
			if (playbackInterval) {
				clearInterval(playbackInterval);
			}
		};
	});

	// Get status badge color
	function getStatusColor(status: string): string {
		switch (status) {
			case 'lobby':
				return 'bg-blue-500';
			case 'matchmaking':
				return 'bg-yellow-500';
			case 'planning':
				return 'bg-orange-500';
			case 'racing':
				return 'bg-green-500';
			case 'finished':
				return 'bg-purple-500';
			default:
				return 'bg-gray-500';
		}
	}
</script>

<svelte:head>
	<title>Race {raceId} - MCP Kart</title>
</svelte:head>

<div class="min-h-screen bg-gray-900 text-white p-4">
	<!-- Header -->
	<header class="mb-6">
		<div class="flex items-center gap-4">
			<a href="/" class="text-gray-400 hover:text-white">← Back</a>
			<h1 class="text-2xl font-bold">Race {raceId}</h1>
			{#if raceState}
				<span class="px-3 py-1 rounded text-sm font-bold uppercase {getStatusColor(raceState.status)}">
					{hasReplay && isFinished ? 'replay' : raceState.status}
				</span>
				{#if raceState.status === 'matchmaking' && matchmakingCountdown() !== null}
					<span class="text-yellow-400 font-mono">
						{readyCount().ready}/{readyCount().total} ready · Auto-start in {matchmakingCountdown()}s
					</span>
				{:else if raceState.status === 'planning' && planningCountdown() !== null}
					<span class="text-orange-400 font-mono">
						Race starts in {planningCountdown()}s
					</span>
				{:else if raceState.status === 'racing'}
					<span class="text-gray-400">
						{raceState.race_clock} / {raceState.max_race_clock}
					</span>
				{:else if isFinished && hasReplay}
					<span class="text-gray-400">
						{formatRaceClock(replayTick)} / {formatRaceClock(replayData?.total_ticks || 0)}
					</span>
				{:else if isFinished}
					<span class="text-gray-400">
						{raceState.race_clock} / {raceState.max_race_clock}
					</span>
				{/if}
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="flex items-center justify-center h-64">
			<p class="text-gray-400">Loading race...</p>
		</div>
	{:else if error}
		<div class="bg-red-900/50 border border-red-500 rounded-lg p-4">
			<p class="text-red-400">Error: {error}</p>
			<p class="text-gray-400 text-sm mt-2">Make sure the backend is running on port 8000.</p>
		</div>
	{:else if raceState}
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main track view (spans 2 columns on large screens) -->
			<div class="lg:col-span-2">
				<TrackViewSVG track={raceState.track} racers={displayRacers} />
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				{#if hasReplay && isFinished}
					<ReplayControls
						currentTick={replayTick}
						totalTicks={replayData?.total_ticks || 0}
						{isPlaying}
						{playbackSpeed}
						onTickChange={handleTickChange}
						onPlayPause={handlePlayPause}
						onSpeedChange={handleSpeedChange}
					/>
				{/if}
				<Standings
					standings={displayStandings}
					racers={displayRacers}
					lapsRequired={raceState.laps_required}
					raceStatus={raceState.status}
					readyPlayers={raceState.ready_players}
				/>
				<EventLog events={displayEvents} />
			</div>
		</div>

		<!-- Race info footer -->
		<footer class="mt-6 text-sm text-gray-500">
			<p>Tick: {displayTick} / {raceState.max_ticks}</p>
		</footer>
	{/if}
</div>
