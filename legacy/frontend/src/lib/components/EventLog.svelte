<script lang="ts">
	let { events }: { events: string[] } = $props();

	// Get event type and appropriate styling
	function getEventStyle(event: string): string {
		if (event.includes('FINISH') || event.includes('finished')) return 'text-purple-400';
		if (event.includes('CRASH') || event.includes('crash')) return 'text-red-400';
		if (event.includes('LAP') || event.includes('lap')) return 'text-green-400';
		if (event.includes('ITEM') || event.includes('item') || event.includes('power-up')) return 'text-yellow-400';
		if (event.includes('BOOST') || event.includes('boost')) return 'text-orange-400';
		return 'text-gray-300';
	}
</script>

<div class="bg-gray-800 rounded-lg p-4">
	<h2 class="text-lg font-bold text-white mb-3">Event Log</h2>

	<div class="h-48 overflow-y-auto space-y-1 font-mono text-xs">
		{#each [...events].reverse() as event}
			<div class={getEventStyle(event)}>
				{event}
			</div>
		{:else}
			<p class="text-gray-500 text-center py-4">No events yet...</p>
		{/each}
	</div>
</div>
