<script lang="ts">
	import type { Track, Racer, Tile } from '$lib/types';

	let { track, racers }: { track: Track; racers: Racer[] } = $props();

	// Track geometry constants (rectangular with 90-degree corners)
	const SVG_WIDTH = 500;
	const SVG_HEIGHT = 300;
	const LEFT_X = 60;
	const RIGHT_X = 440;
	const TOP_Y = 40;
	const BOTTOM_Y = 260;

	// Pre-compute all 44 tile positions along the rectangular track
	// Track layout (counterclockwise):
	// - Bottom straight: tiles 38-43, 0-6 (13 tiles, left→right)
	// - Tile 7: bottom-right corner (turn)
	// - Right side: tiles 8-14 (7 tiles, bottom→top)
	// - Tile 15: top-right corner (turn)
	// - Top straight: tiles 16-28 (13 tiles, right→left)
	// - Tile 29: top-left corner (turn)
	// - Left side: tiles 30-36 (7 tiles, top→bottom)
	// - Tile 37: bottom-left corner (turn)
	const TILE_POSITIONS: Array<{ x: number; y: number }> = (() => {
		const positions: Array<{ x: number; y: number }> = new Array(44);

		// Bottom straight: tiles 38-43, 0-6 (left to right, 13 tiles)
		const bottomTiles = [38, 39, 40, 41, 42, 43, 0, 1, 2, 3, 4, 5, 6];
		const bottomSpacing = (RIGHT_X - LEFT_X) / (bottomTiles.length + 1);
		bottomTiles.forEach((tileIdx, i) => {
			positions[tileIdx] = { x: LEFT_X + (i + 1) * bottomSpacing, y: BOTTOM_Y };
		});

		// Tile 7: bottom-right corner
		positions[7] = { x: RIGHT_X, y: BOTTOM_Y };

		// Right side: tiles 8-14 (bottom to top, 7 tiles)
		const rightTiles = [8, 9, 10, 11, 12, 13, 14];
		const rightSpacing = (BOTTOM_Y - TOP_Y) / (rightTiles.length + 1);
		rightTiles.forEach((tileIdx, i) => {
			positions[tileIdx] = { x: RIGHT_X, y: BOTTOM_Y - (i + 1) * rightSpacing };
		});

		// Tile 15: top-right corner
		positions[15] = { x: RIGHT_X, y: TOP_Y };

		// Top straight: tiles 16-28 (right to left, 13 tiles)
		const topTiles = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28];
		const topSpacing = (RIGHT_X - LEFT_X) / (topTiles.length + 1);
		topTiles.forEach((tileIdx, i) => {
			positions[tileIdx] = { x: RIGHT_X - (i + 1) * topSpacing, y: TOP_Y };
		});

		// Tile 29: top-left corner
		positions[29] = { x: LEFT_X, y: TOP_Y };

		// Left side: tiles 30-36 (top to bottom, 7 tiles)
		const leftTiles = [30, 31, 32, 33, 34, 35, 36];
		const leftSpacing = (BOTTOM_Y - TOP_Y) / (leftTiles.length + 1);
		leftTiles.forEach((tileIdx, i) => {
			positions[tileIdx] = { x: LEFT_X, y: TOP_Y + (i + 1) * leftSpacing };
		});

		// Tile 37: bottom-left corner
		positions[37] = { x: LEFT_X, y: BOTTOM_Y };

		return positions;
	})();

	// Get position for a tile, with optional subunit interpolation
	function getTilePosition(tileIndex: number, subunit: number = 0): { x: number; y: number } {
		const pos = TILE_POSITIONS[tileIndex];
		if (subunit === 0) return pos;

		// Interpolate toward next tile for subunit positioning
		const nextPos = TILE_POSITIONS[(tileIndex + 1) % 44];
		const t = subunit / 3;
		return {
			x: pos.x + (nextPos.x - pos.x) * t,
			y: pos.y + (nextPos.y - pos.y) * t
		};
	}

	// Get color for a tile marker
	function getTileColor(tile: Tile): string {
		if (tile.tile_type === 'turn_left') return '#fb923c'; // orange-400
		if (tile.has_item_box) return '#fde047'; // yellow-300
		if (DRIFT_ZONE_TILES.has(tile.index)) return '#22d3ee'; // cyan-400
		return '#4b5563'; // gray-600
	}

	// Get color for a racer based on status
	function getRacerColor(racer: Racer): string {
		if (racer.status === 'crashed') return '#ef4444'; // red-500
		if (racer.status === 'finished') return '#c084fc'; // purple-400
		if (racer.boost_ticks_remaining > 0) return '#facc15'; // yellow-400
		if (racer.drift_enabled) return '#22d3d2'; // cyan-400
		return '#4ade80'; // green-400
	}

	// Turn tiles for reference
	const TURN_TILES = new Set([7, 15, 29, 37]);

	// Drift zone tiles (3 tiles before each turn)
	const DRIFT_ZONE_TILES = new Set([4, 5, 6, 12, 13, 14, 26, 27, 28, 34, 35, 36]);

	// Racer slice layout constants
	const SLICE_DEPTH = 9; // Each subunit slice is 9 SVG units deep (along track)
	const SLICE_WIDTH = 27; // Full tile width perpendicular to track (~27 units)
	const BASE_RACER_RADIUS = 4; // Default radius when ≤3 racers in slice
	const BASE_FONT_SIZE = 5; // Default font size when ≤3 racers in slice

	// Get normalized direction vector from a tile toward the next tile
	// For turn tiles, use 45-degree angle (bisector of incoming/outgoing directions)
	function getTileDirection(tileIndex: number): { dx: number; dy: number } {
		const pos = TILE_POSITIONS[tileIndex];
		const nextPos = TILE_POSITIONS[(tileIndex + 1) % 44];

		// For turn tiles, blend incoming and outgoing directions (45-degree angle)
		if (TURN_TILES.has(tileIndex)) {
			const prevPos = TILE_POSITIONS[(tileIndex - 1 + 44) % 44];
			// Incoming direction (from prev tile)
			const inDx = pos.x - prevPos.x;
			const inDy = pos.y - prevPos.y;
			// Outgoing direction (to next tile)
			const outDx = nextPos.x - pos.x;
			const outDy = nextPos.y - pos.y;
			// Average them (creates 45-degree bisector)
			const dx = inDx + outDx;
			const dy = inDy + outDy;
			const len = Math.sqrt(dx * dx + dy * dy);
			return { dx: dx / len, dy: dy / len };
		}

		// Normal tiles: direction toward next tile
		const dx = nextPos.x - pos.x;
		const dy = nextPos.y - pos.y;
		const len = Math.sqrt(dx * dx + dy * dy);
		return { dx: dx / len, dy: dy / len };
	}

	// Position racer within its subunit slice, spreading perpendicular to track
	function getRacerSlicePosition(
		tileIndex: number,
		subunit: number,
		indexInSlice: number, // 0-based index among racers in same tile+subunit
		totalInSlice: number // total racers in this tile+subunit
	): { x: number; y: number; radius: number; fontSize: number } {
		const tilePos = TILE_POSITIONS[tileIndex];
		const dir = getTileDirection(tileIndex);

		// Perpendicular direction (for spreading racers within slice)
		const perpX = -dir.dy;
		const perpY = dir.dx;

		// Position along track: subunit 0 at tile center, 1 and 2 toward next tile
		const trackOffset = (subunit - 1) * SLICE_DEPTH;

		// Position perpendicular: spread racers evenly across slice width
		const spreadWidth = SLICE_WIDTH * 0.8; // Use 80% of width for some margin
		let perpOffset = 0;
		if (totalInSlice > 1) {
			const spacing = spreadWidth / (totalInSlice - 1);
			perpOffset = (indexInSlice - (totalInSlice - 1) / 2) * spacing;
		}

		// Shrink if more than 3 racers in slice
		const scaleFactor = totalInSlice <= 3 ? 1 : 3 / totalInSlice;

		return {
			x: tilePos.x + dir.dx * trackOffset + perpX * perpOffset,
			y: tilePos.y + dir.dy * trackOffset + perpY * perpOffset,
			radius: BASE_RACER_RADIUS * scaleFactor,
			fontSize: BASE_FONT_SIZE * scaleFactor
		};
	}

</script>

<div class="bg-gray-900 p-4 rounded-lg">
	<svg viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" class="w-full max-w-2xl mx-auto">
		<!-- Pattern definitions -->
		<defs>
			<pattern id="checkerboard" width="8" height="8" patternUnits="userSpaceOnUse">
				<rect width="4" height="4" fill="white" />
				<rect x="4" width="4" height="4" fill="black" />
				<rect y="4" width="4" height="4" fill="black" />
				<rect x="4" y="4" width="4" height="4" fill="white" />
			</pattern>
		</defs>

		<!-- Track outline (rectangular with slightly rounded corners) -->
		<path
			d="M {LEFT_X} {BOTTOM_Y}
			   L {RIGHT_X} {BOTTOM_Y}
			   L {RIGHT_X} {TOP_Y}
			   L {LEFT_X} {TOP_Y}
			   Z"
			fill="none"
			stroke="#374151"
			stroke-width="36"
			stroke-linejoin="round"
		/>

		<!-- Racing line segments (between tile positions, with gaps at dots) -->
		{#each TILE_POSITIONS as pos, i}
			{@const nextPos = TILE_POSITIONS[(i + 1) % 44]}
			{@const dx = nextPos.x - pos.x}
			{@const dy = nextPos.y - pos.y}
			<line
				x1={pos.x + dx * 0.35}
				y1={pos.y + dy * 0.35}
				x2={pos.x + dx * 0.65}
				y2={pos.y + dy * 0.65}
				stroke="#1f2937"
				stroke-width="2"
			/>
		{/each}

		<!-- MCP KART text in center -->
		<text
			x={SVG_WIDTH / 2}
			y={SVG_HEIGHT / 2}
			text-anchor="middle"
			dominant-baseline="central"
			fill="#374151"
			font-size="24"
			font-weight="bold"
		>
			MCP KART
		</text>

		<!-- Tile markers -->
		{#each track.tiles as tile (tile.index)}
			{@const pos = getTilePosition(tile.index)}
			{#if TURN_TILES.has(tile.index)}
				<!-- Turn tiles: orange dot -->
				<circle cx={pos.x} cy={pos.y} r="3" fill={getTileColor(tile)} />
			{:else if tile.has_item_box}
				<!-- Item box tiles: question mark -->
				<text
					x={pos.x}
					y={pos.y}
					text-anchor="middle"
					dominant-baseline="central"
					fill={getTileColor(tile)}
					font-size="14"
					font-weight="bold"
				>
					?
				</text>
			{:else}
				<!-- Normal tiles: small dot -->
				<circle cx={pos.x} cy={pos.y} r="3" fill={getTileColor(tile)} />
			{/if}
		{/each}

		<!-- Start/Finish line (checkered pattern at tile 0) - rendered after tiles for z-order -->
		<rect
			x={TILE_POSITIONS[0].x - 6}
			y={BOTTOM_Y - 18}
			width="12"
			height="36"
			fill="url(#checkerboard)"
		/>

		<!-- Racers (positioned within subunit slices) -->
		{#each racers as racer (racer.id)}
			{@const racersInSlice = racers
				.filter((r) => r.tile_index === racer.tile_index && r.tile_subunit === racer.tile_subunit)
				.sort((a, b) => a.name.localeCompare(b.name))}
			{@const indexInSlice = racersInSlice.findIndex((r) => r.id === racer.id)}
			{@const pos = getRacerSlicePosition(
				racer.tile_index,
				racer.tile_subunit,
				indexInSlice,
				racersInSlice.length
			)}
			<g>
				<!-- Racer circle -->
				<circle
					cx={pos.x}
					cy={pos.y}
					r={pos.radius}
					fill={getRacerColor(racer)}
					stroke="white"
					stroke-width="1"
				/>
				<!-- Racer initial -->
				<text
					x={pos.x}
					y={pos.y}
					text-anchor="middle"
					dominant-baseline="central"
					fill="white"
					font-size={pos.fontSize}
					font-weight="bold"
				>
					{racer.name.charAt(0).toUpperCase()}
				</text>
			</g>
		{/each}
	</svg>

	<!-- Legend -->
	<div class="mt-4 text-xs text-gray-500 flex gap-4 justify-center flex-wrap">
		<span><span style="color: #fde047">?</span> Item Box</span>
		<span><span style="color: #fb923c">●</span> Turn</span>
		<span><span style="color: #22d3ee">●</span> Drift Zone</span>
		<span class="text-gray-600">|</span>
		<span><span style="color: #4ade80">●</span> Racing</span>
		<span><span style="color: #facc15">●</span> Boosting</span>
		<span><span style="color: #22d3ee">●</span> Drifting</span>
		<span><span style="color: #ef4444">●</span> Crashed</span>
		<span><span style="color: #c084fc">●</span> Finished</span>
	</div>
</div>
