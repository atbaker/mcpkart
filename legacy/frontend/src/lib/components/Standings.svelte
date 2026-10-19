<script lang="ts">
	import type { Standing, Racer, RaceStatus } from '$lib/types';

	let {
		standings,
		racers,
		lapsRequired,
		raceStatus = 'racing',
		readyPlayers = []
	}: {
		standings: Standing[];
		racers: Racer[];
		lapsRequired: number;
		raceStatus?: RaceStatus;
		readyPlayers?: string[];
	} = $props();

	// Check if we're in matchmaking phase
	const isMatchmaking = $derived(raceStatus === 'matchmaking');

	// Get racer details by ID
	function getRacer(racerId: string): Racer | undefined {
		return racers.find((r) => r.id === racerId);
	}

	// Check if a player is ready
	function isPlayerReady(playerId: string): boolean {
		return readyPlayers.includes(playerId);
	}

	// Get status indicator
	function getStatusIndicator(standing: Standing): string {
		const racer = getRacer(standing.racer_id);
		if (!racer) return '';
		if (racer.status === 'finished') return '🏁';
		if (racer.status === 'crashed') return '💥';
		if (racer.boost_ticks_remaining > 0) return '🍄';
		if (racer.drift_enabled) return '↯';
		return '';
	}

	// Get position display (1st, 2nd, 3rd, etc.)
	function getPositionDisplay(pos: number): string {
		if (pos === 1) return '1st';
		if (pos === 2) return '2nd';
		if (pos === 3) return '3rd';
		return `${pos}th`;
	}

	// Get GitHub avatar URL
	function getAvatarUrl(username: string): string {
		return `https://avatars.githubusercontent.com/${username}`;
	}
</script>

<div class="bg-gray-800 rounded-lg p-4">
	<h2 class="text-lg font-bold text-white mb-3">
		{#if isMatchmaking}
			Players
		{:else}
			Standings
		{/if}
	</h2>

	<div class="space-y-2">
		{#each standings as standing}
			{@const racer = getRacer(standing.racer_id)}
			{@const playerReady = isPlayerReady(standing.racer_id)}
			<div
				class="flex items-center gap-2 p-2 rounded {isMatchmaking
					? playerReady
						? 'bg-green-900/30'
						: 'bg-gray-700/50'
					: standing.status === 'crashed'
						? 'bg-red-900/30'
						: standing.status === 'finished'
							? 'bg-purple-900/30'
							: 'bg-gray-700/50'}"
			>
				{#if isMatchmaking}
					<!-- Ready indicator for matchmaking -->
					<span class="w-10 text-sm font-mono {playerReady ? 'text-green-400' : 'text-gray-500'}">
						{playerReady ? 'READY' : '...'}
					</span>
				{:else}
					<!-- Position (fixed width) -->
					<span class="w-10 text-sm font-mono {standing.position <= 3 ? 'text-yellow-400' : 'text-gray-400'}">
						{getPositionDisplay(standing.position)}
					</span>
				{/if}

				<!-- Avatar and racer name -->
				<div class="flex-1 flex items-center gap-2 min-w-0">
					<img
						src={getAvatarUrl(standing.name)}
						alt="{standing.name}'s avatar"
						class="w-6 h-6 rounded-full object-cover flex-shrink-0"
						onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
					/>
					<span class="text-white font-medium truncate">
						{standing.name}
					</span>
				</div>

				{#if !isMatchmaking}
					<!-- Status indicator (fixed width) -->
					<span class="w-6 text-center flex-shrink-0">
						{getStatusIndicator(standing)}
					</span>

					<!-- Lap count (fixed width) -->
					<span class="w-16 text-sm text-gray-400 text-right flex-shrink-0">
						Lap {standing.lap}/{lapsRequired}
					</span>

					<!-- Speed/finish time column (fixed width, always present) -->
					<span class="w-16 text-sm text-right flex-shrink-0">
						{#if racer?.status === 'racing'}
							<span class="text-cyan-400">{racer.speed} spd</span>
						{:else if standing.finish_time}
							<span class="text-green-400">{standing.finish_time}</span>
						{:else}
							<span class="text-gray-600">-</span>
						{/if}
					</span>

					<!-- Power-up indicator (fixed width, always present) -->
					<span class="w-6 text-center flex-shrink-0">
						{#if racer?.power_up}
							{#if racer.power_up === 'mushroom'}
								🍄
							{:else if racer.power_up === 'banana'}
								🍌
							{:else if racer.power_up === 'shell'}
								🐚
							{/if}
						{/if}
					</span>
				{/if}
			</div>
		{/each}
	</div>

	{#if standings.length === 0}
		<p class="text-gray-500 text-center py-4">Waiting for racers...</p>
	{/if}
</div>
