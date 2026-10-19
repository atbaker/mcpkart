# Frontend Architecture Plan

This document outlines the architecture for the MCP Kart spectator frontend, which allows users to watch races in real-time.

## Requirements

- Display live race state updates to spectators
- Support individual race pages with ~8 viewers
- Support a homepage featuring an active race (potential traffic spikes)
- Integrate with Temporal workflow state via query()
- Deploy on GKE (GCP)

## Constraints

| Constraint | Value | Implication |
|------------|-------|-------------|
| Tick rate | 1 second | Max 1 meaningful update/sec |
| Max race duration | 10 minutes | ≤600 updates per race |
| State source | Temporal query() | Pull-based by nature |
| Typical viewers | ~8 per race | Low baseline load |
| Homepage spikes | 100-1000+ | Need to handle gracefully |

## Decision: Polling with Backend Caching

After evaluating several approaches (polling, SSE, WebSockets, long polling), we chose **simple polling with a short-TTL backend cache**.

### Why Polling?

1. **Matches the tick model**: Race state only changes once per second, so polling every second captures all updates
2. **Stateless**: Scales horizontally on GKE with zero special configuration
3. **Simple**: Easy to implement, debug, and monitor
4. **Resilient**: Each request is independent; no connection state to manage

### Why Not SSE/WebSockets?

- Adds connection state management complexity
- Requires sticky sessions on GKE
- The "push" benefit is negligible with 1-second ticks
- More failure modes (connection drops, reconnection logic)

## Architecture

```
                                    ┌─────────────────┐
                                    │   Cloud CDN     │ (future, for viral spikes)
                                    │   (1s TTL)      │
                                    └────────┬────────┘
                                             │
┌──────────────┐                    ┌────────▼────────┐
│   Svelte     │ ───── poll ──────▶│    FastAPI      │
│   Frontend   │    (every 1s)     │  + TTL Cache    │
│              │◀──────────────────│   (0.8s TTL)    │
└──────────────┘                    └────────┬────────┘
                                             │
                                             │ 1-3 queries/sec
                                             │ (per replica, regardless of viewers)
                                             ▼
                                    ┌─────────────────┐
                                    │    Temporal     │
                                    │    Workflow     │
                                    └─────────────────┘
```

## Backend Implementation

### Caching Strategy

The FastAPI backend implements a short-TTL in-memory cache to decouple viewer count from Temporal query load:

```python
from fastapi import FastAPI
import time

app = FastAPI()

# Simple in-memory cache (per-process)
_race_state_cache: dict[str, tuple[RaceState, float]] = {}
CACHE_TTL = 0.8  # seconds - slightly less than tick rate

async def get_race_state_cached(race_id: str) -> RaceState:
    cached = _race_state_cache.get(race_id)
    now = time.time()

    if cached and (now - cached[1]) < CACHE_TTL:
        return cached[0]  # Cache hit

    # Cache miss - query Temporal
    handle = client.get_workflow_handle(f"race-{race_id}")
    state = await handle.query(RaceWorkflow.get_state)
    _race_state_cache[race_id] = (state, now)
    return state

@app.get("/races/{race_id}/state")
async def get_race_state(race_id: str):
    return await get_race_state_cached(race_id)
```

### Cache Behavior

| Scenario | Viewers | Polls/sec | Temporal Queries/sec |
|----------|---------|-----------|----------------------|
| Normal race | 8 | 8 | ~1-2 per replica |
| Featured (moderate) | 100 | 100 | ~1-2 per replica |
| Featured (spike) | 1000 | 1000 | ~1-2 per replica |

The cache absorbs traffic spikes while keeping Temporal load constant.

### API Endpoints for Frontend

```
GET /races/{race_id}/state     - Get current race state (cached)
GET /races/featured            - Get the currently featured race ID
GET /races/{race_id}/results   - Get final results (post-race)
```

## Frontend Implementation

### Technology Stack

- **Framework**: SvelteKit 2 with Svelte 5
- **Styling**: TBD (Tailwind CSS or similar)
- **Deployment**: Static adapter for CDN deployment, or Node adapter for SSR

### Why Svelte?

- Small bundle size for fast initial load
- Built-in reactivity works well with polling data
- SvelteKit provides routing and SSR out of the box
- Svelte 5 runes (`$state`, `$effect`) make async state management clean

### Polling Implementation

```svelte
<script>
  let { raceId } = $props();
  let raceState = $state(null);
  let error = $state(null);

  $effect(() => {
    let active = true;

    async function poll() {
      try {
        const res = await fetch(`/api/races/${raceId}/state`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (active) {
          raceState = await res.json();
          error = null;
        }
      } catch (e) {
        if (active) error = e.message;
      }
    }

    // Initial fetch
    poll();

    // Poll every second
    const interval = setInterval(poll, 1000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  });
</script>

{#if error}
  <p class="error">Connection error: {error}</p>
{:else if raceState}
  <RaceViewer state={raceState} />
{:else}
  <p>Loading race...</p>
{/if}
```

### Page Structure

```
/                       - Homepage with featured race
/races                  - List of active/recent races
/races/[id]             - Individual race viewer
/races/[id]/results     - Post-race results and replay
```

## Scaling Path

### Phase 1: Launch (Current Plan)

- In-process TTL cache in FastAPI
- Simple polling from Svelte frontend
- Standard GKE deployment

### Phase 2: If Traffic Grows

- Add `Cache-Control: public, max-age=1` header to state endpoint
- Enable Cloud CDN on GCP load balancer
- CDN edge caching handles global traffic spikes

### Phase 3: If Needed (Unlikely)

- Shared Redis cache for cross-replica deduplication
- Or SSE with Cloud Pub/Sub for true push model

## Race State Schema

The frontend expects this structure from the polling endpoint:

```typescript
interface RaceState {
  race_id: string;
  current_tick: number;
  max_ticks: number;
  status: "waiting" | "countdown" | "racing" | "finished";

  racers: Racer[];
  track: Track;
  events: RaceEvent[];  // Events from current tick

  standings: Standing[];  // Current race positions
  finished: FinishedRacer[];  // Racers who completed the race
}

interface Racer {
  id: string;
  name: string;
  position: { tile: number; subtile: number };
  speed: number;
  steering: "left" | "right" | "straight" | null;
  current_item: PowerUp | null;
  lap: number;
  is_on_track: boolean;
  is_finished: boolean;
}

interface Track {
  tiles: Tile[];
  total_laps: number;
}

interface Tile {
  index: number;
  type: "straight" | "turn_left" | "turn_right";
  has_item_box: boolean;
}

interface RaceEvent {
  tick: number;
  type: "lap_complete" | "item_pickup" | "item_used" | "off_track" | "finished";
  racer_id: string;
  data: Record<string, unknown>;
}
```

## Open Questions

1. **Homepage race selection**: How do we choose which race to feature? Most viewers? Most recent start? Manual selection?
2. **Race discovery**: How do users find active races to watch?
3. **Historical races**: Do we want replay functionality for completed races?
4. **Authentication**: Do spectators need to log in, or is viewing public?

## References

- [Temporal Workflow Queries](https://docs.temporal.io/encyclopedia/workflow-message-passing)
- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [FastAPI Caching Patterns](https://fastapi.tiangolo.com/advanced/custom-response/)
- [GCP Cloud CDN](https://cloud.google.com/cdn/docs)
