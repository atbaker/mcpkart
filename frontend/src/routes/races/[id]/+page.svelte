<script lang="ts">
	import { page } from '$app/state';
	import TrackViewSVG from '$lib/components/TrackViewSVG.svelte';
	import Standings from '$lib/components/Standings.svelte';
	import EventLog from '$lib/components/EventLog.svelte';
	import type { SpectatorState } from '$lib/types';

	let raceState = $state<SpectatorState | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);
	let now = $state(Date.now());

	const raceId = $derived(page.params.id);

	// Compute planning countdown
	const planningCountdown = $derived(() => {
		if (!raceState?.planning_ends_at) return null;
		const endsAt = new Date(raceState.planning_ends_at).getTime();
		const remaining = Math.max(0, Math.ceil((endsAt - now) / 1000));
		return remaining;
	});

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

	// Get status badge color
	function getStatusColor(status: string): string {
		switch (status) {
			case 'lobby':
				return 'bg-blue-500';
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
					{raceState.status}
				</span>
				{#if raceState.status === 'planning' && planningCountdown() !== null}
					<span class="text-orange-400 font-mono">
						Race starts in {planningCountdown()}s
					</span>
				{:else if raceState.status === 'racing' || raceState.status === 'finished'}
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
				<TrackViewSVG track={raceState.track} racers={raceState.racers} />
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				<Standings
					standings={raceState.standings}
					racers={raceState.racers}
					lapsRequired={raceState.laps_required}
				/>
				<EventLog events={raceState.events} />
			</div>
		</div>

		<!-- Race info footer -->
		<footer class="mt-6 text-sm text-gray-500">
			<p>Tick: {raceState.current_tick} / {raceState.max_ticks}</p>
		</footer>
	{/if}
</div>
