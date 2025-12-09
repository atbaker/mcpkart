<script lang="ts">
	import { goto } from '$app/navigation';

	let raceId = $state('');

	function handleSubmit(event: Event) {
		event.preventDefault();
		if (raceId.trim()) {
			goto(`/races/${raceId.trim().toUpperCase()}`);
		}
	}
</script>

<svelte:head>
	<title>MCP Kart - Spectator</title>
</svelte:head>

<div class="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
	<div class="max-w-md w-full">
		<div class="text-center mb-8">
			<h1 class="text-4xl font-bold mb-2">MCP Kart</h1>
			<p class="text-gray-400">Watch AI racers compete in real-time</p>
		</div>

		<form onsubmit={handleSubmit} class="bg-gray-800 rounded-lg p-6">
			<label for="raceId" class="block text-sm font-medium text-gray-300 mb-2">
				Enter Race ID
			</label>
			<div class="flex gap-2">
				<input
					id="raceId"
					type="text"
					bind:value={raceId}
					placeholder="e.g. ABC123"
					class="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 uppercase"
					maxlength="6"
				/>
				<button
					type="submit"
					class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-medium transition-colors"
				>
					Watch
				</button>
			</div>
		</form>

		<p class="text-center text-gray-500 text-sm mt-6">
			Get a Race ID from someone running MCP Kart
		</p>
	</div>
</div>
