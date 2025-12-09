<script lang="ts">
	import type { Standing, Racer } from '$lib/types';

	let { standings, racers, lapsRequired }: { standings: Standing[]; racers: Racer[]; lapsRequired: number } = $props();

	// Get racer details by ID
	function getRacer(racerId: string): Racer | undefined {
		return racers.find((r) => r.id === racerId);
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
</script>

<div class="bg-gray-800 rounded-lg p-4">
	<h2 class="text-lg font-bold text-white mb-3">Standings</h2>

	<div class="space-y-2">
		{#each standings as standing}
			{@const racer = getRacer(standing.racer_id)}
			<div
				class="flex items-center gap-2 p-2 rounded {standing.status === 'crashed'
					? 'bg-red-900/30'
					: standing.status === 'finished'
						? 'bg-purple-900/30'
						: 'bg-gray-700/50'}"
			>
				<!-- Position (fixed width) -->
				<span class="w-10 text-sm font-mono {standing.position <= 3 ? 'text-yellow-400' : 'text-gray-400'}">
					{getPositionDisplay(standing.position)}
				</span>

				<!-- Racer name (flex to fill) -->
				<span class="flex-1 text-white font-medium truncate min-w-0">
					{standing.name}
				</span>

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
			</div>
		{/each}
	</div>

	{#if standings.length === 0}
		<p class="text-gray-500 text-center py-4">Waiting for racers...</p>
	{/if}
</div>
