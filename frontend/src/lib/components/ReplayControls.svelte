<script lang="ts">
	let {
		currentTick = 0,
		totalTicks,
		isPlaying = false,
		playbackSpeed = 1,
		onTickChange,
		onPlayPause,
		onSpeedChange
	}: {
		currentTick: number;
		totalTicks: number;
		isPlaying: boolean;
		playbackSpeed: number;
		onTickChange: (tick: number) => void;
		onPlayPause: () => void;
		onSpeedChange: (speed: number) => void;
	} = $props();

	// Format tick as MM:SS
	function formatTime(tick: number): string {
		const minutes = Math.floor(tick / 60);
		const seconds = tick % 60;
		return `${minutes}:${seconds.toString().padStart(2, '0')}`;
	}

	// Handle slider change
	function handleSliderChange(event: Event) {
		const target = event.target as HTMLInputElement;
		onTickChange(parseInt(target.value, 10));
	}

	// Jump to start
	function jumpToStart() {
		onTickChange(0);
	}

	// Jump to end
	function jumpToEnd() {
		onTickChange(totalTicks);
	}
</script>

<div class="bg-gray-800 rounded-lg p-4">
	<h2 class="text-lg font-bold text-white mb-3">Replay</h2>

	<!-- Progress bar / slider -->
	<div class="mb-4">
		<input
			type="range"
			min="0"
			max={totalTicks}
			value={currentTick}
			oninput={handleSliderChange}
			class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
		/>
		<div class="flex justify-between text-xs text-gray-400 mt-1">
			<span>{formatTime(currentTick)}</span>
			<span>{formatTime(totalTicks)}</span>
		</div>
	</div>

	<!-- Controls -->
	<div class="flex items-center justify-center gap-4">
		<!-- Jump to start -->
		<button
			onclick={jumpToStart}
			class="p-2 text-gray-400 hover:text-white transition-colors"
			title="Jump to start"
		>
			<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
				<path d="M15 3a1 1 0 00-1.707-.707l-6 6a1 1 0 000 1.414l6 6A1 1 0 0015 15V3zM6 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1z" />
			</svg>
		</button>

		<!-- Play/Pause -->
		<button
			onclick={onPlayPause}
			class="p-3 bg-purple-600 hover:bg-purple-700 rounded-full text-white transition-colors"
			title={isPlaying ? 'Pause' : 'Play'}
		>
			{#if isPlaying}
				<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
			{:else}
				<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
				</svg>
			{/if}
		</button>

		<!-- Jump to end -->
		<button
			onclick={jumpToEnd}
			class="p-2 text-gray-400 hover:text-white transition-colors"
			title="Jump to end"
		>
			<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
				<path d="M5 17a1 1 0 001.707.707l6-6a1 1 0 000-1.414l-6-6A1 1 0 005 5v12zM14 17a1 1 0 001-1V4a1 1 0 10-2 0v12a1 1 0 001 1z" />
			</svg>
		</button>
	</div>

	<!-- Speed controls -->
	<div class="flex items-center justify-center gap-2 mt-4">
		<span class="text-gray-400 text-sm">Speed:</span>
		<button
			onclick={() => onSpeedChange(1)}
			class="px-3 py-1 rounded text-sm {playbackSpeed === 1 ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}"
		>
			1x
		</button>
		<button
			onclick={() => onSpeedChange(2)}
			class="px-3 py-1 rounded text-sm {playbackSpeed === 2 ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'}"
		>
			2x
		</button>
	</div>
</div>
