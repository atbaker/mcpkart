# First experiment: realtime driving through MCP

Status: approved by the user on October 18, 2026. Local implementation and initial screens are complete. [Track telemetry iteration](0002-track-telemetry.md) is underway before further qualification trials.

Amended during implementation on October 18: the user requested an automatic off-track rescue to test whether staying on the road is easier than recovering from distant off-road positions. The initial no-rescue measurements remain separate. The new default is rescue after three continuous seconds off-road, configurable per experiment; assisted completions and zero-rescue completions are reported separately.

Further amended on October 18: focus initial PoC testing on Jev 1.14. Preserve existing three-route measurements and the interrupted Clef screen. Resume other routes after Jev demonstrates passing driving; this does not change the target, physics, or shared spending cap.

Test whether OpenAI Decisions, Jev, and Clef can directly drive a solo kart around three laps of a winding track in real time. Use the same local Python simulation, observation content, control menu, MCP transport, and track for each model. Access all models through OpenRouter's Decisions endpoint.

## Agreed scope

- Continuous wall-clock racing with direct steering, throttle, and brake inputs. The game does not wait for a model, and the driver receives no automatic lane keeping or racing-line control.
- Structured telemetry and upcoming track geometry, with a live 2D SVG spectator view.
- One request in flight per driver. Apply its result and obtain the next observation immediately; faster models can act more frequently.
- Off-road slowdown and ordered checkpoints. After three continuous seconds off-road, rescue the kart near its departure point, aligned with the road, stopped and coasting. Continue the clock and count the rescue.
- Python simulation and driver first. Measure before considering a Rust simulation.
- Initial model set: `openai/gpt-6-luna-decisions`, `typesafe/jev-1.14`, and `cloudflare/clef`.
- The assisted experiment targets at least eight of ten completed three-lap runs, with median completed-run race time within twice the scripted reference. Report zero-rescue completion and rescue counts separately; assisted success does not establish the original unassisted target.
- A $10 total spending cap across the first paid batch, including smoke tests, warm-ups, latency tests, and driving trials.

## Initial experiment defaults

### Simulation and track

Run fixed-step physics at 60 Hz, paced against a monotonic wall clock. Rendering and model requests have separate schedules. Record simulation lateness and elapsed-time drift; a run that silently slows the world cannot establish realtime viability.

Use a small 2D vehicle model with position, heading, velocity, acceleration, braking, steering response, and limited grip. Start with a winding closed track containing straights, broad bends, and at least one bend requiring reduced speed. Calibrate handling and track dimensions with the scripted driver before model trials, then freeze them. This first experiment omits kart-to-kart collisions, items, handbrake controls, and damage; the simulation boundary should permit adding them later.

Grass reduces acceleration and speed but leaves steering under the driver's control. Track consecutive off-road time; returning to the road clears that timer. At the rescue timeout, place the kart on the centreline one metre before its last on-road departure point, facing the road direction, with zero velocity and neutral controls. Do not rewind time, grant checkpoint credit for the teleport, or erase accumulated off-road time. Count a lap only after all required finite gates are crossed forward on the road. Ordinary corner clipping between gates remains possible.

### Observations and controls

Send a compact structured observation containing observation identity and racing time, kart position and heading, velocity, current controls, lap/checkpoint progress, nearby road boundaries, and a preview of upcoming track geometry. Use documented units and a consistent coordinate frame. Relative track position and geometry are observations; recommended steering, braking points, or a computed racing line are not provided.

Include fixed handling limits, the action definitions, and the same basic racing objective for every model. Begin with no growing conversation history or model-specific prompt tuning. Keep state comfortably below the selected provider's effective input limit and verify that geometry is not truncated.

Start with 15 allowed actions: five normalized steering positions (`-1`, `-0.5`, `0`, `0.5`, `1`) combined with acceleration, coasting, or braking. Acceleration sets throttle to one and brake to zero; coasting sets both to zero; braking sets throttle to zero and brake to one. Steering positions map to fixed physical steering values. The selected action persists until replaced; the adapter adds no driving policy.

Use one named `choice` question with all 15 joint actions as its criteria. Verify the exact request and response schema with OpenRouter. Provider scores or probability mixtures are not blended into an additional control policy in this experiment.

### MCP and action timing

Use a local MCP server with structured observations and control submission. The decisive driving runs use a real MCP client/transport rather than direct calls to simulation functions. A control response may include the next observation to avoid a redundant round trip, provided that behavior is identical across models.

Attach observation and command sequence identities to controls. Apply accepted inputs at a defined physics-step boundary, record when they actually took effect, and reject duplicate or out-of-order commands. Acknowledging a queued command does not mean it has already affected physics.

Model requests do not block physics. On a request error, refusal, invalid action, or missing reply, retain the last applied controls and record the event. The game's rescue rule may independently return the kart to the road and neutralize controls. Reject a reply based on an observation from before the latest rescue and return fresh state. Do not silently retry a timed decision, pause the world, or invoke a fallback driver. Cancellation closes the trial so a late reply cannot affect a subsequent race.

The trial deadline is three times that trial's scripted reference duration. An unfinished trial is recorded as a failure at the deadline. A network failure is part of the observed model/route result; a simulation scheduling failure is reported separately and cannot count as a passing trial.

### Providers and spending

Discover current provider endpoints and prices, choose and record a route for each model, and pin it for comparison with automatic fallbacks disabled. Select routes before collecting the comparison results; do not choose a different route in response to a losing race. Record the actual returned model and provider. These are model-plus-route comparisons through OpenRouter, rather than measurements of isolated inference compute.

Load `OPENROUTER_API_KEY` from the local environment or ignored `.env`. Keep credentials out of logs and replays. Stop before the next request would exceed the $10 allowance, using a conservative allowance for in-flight work and a maximum request/token count as well as reported spending. If the cap stops a batch before ten trials per model, report the smaller sample as incomplete rather than changing the pass rule.

## Experiment sequence

1. **Offline reference:** verify direct control, lap/checkpoint correctness, off-road recovery, deterministic replay from recorded inputs, and reliable realtime simulation. The scripted driver uses the same action menu. It is a reference driver, never a rescue controller for the model.
2. **Delay tolerance:** delay the reference driver's observations/actions by controlled amounts and add jitter. This measures the track's control sensitivity and helps interpret later failures.
3. **Endpoint and latency tests:** verify each pinned route with a small smoke test, then measure changing realistic observations over reused connections. Separate cold and warmed requests and retain all errors. Use sample counts appropriate to the latency claims; do not infer a reliable p99 from a small pilot. Classify explicit upstream refusals separately even when a provider returns them as HTTP 502.
4. **Driving screen:** run each model on the same track through MCP. Confirm that observation formatting, action mapping, and timing instrumentation work before committing the remaining budget to a batch.
5. **Ten paired trials per model:** reuse ten predefined starting-condition seeds for every model and interleave model order to reduce time-of-day bias. Run trials sequentially initially so local concurrency does not confound the comparison. Freeze track, handling, prompts, and control menu for the batch.
6. **Diagnose failures:** if needed, compare transport overhead, observation size, or control resolution as separately labeled experiments. Keep the original comparison results; changes require a new experiment configuration.

The runner optionally supports stopping a model after three failed trials, since eight completions out of ten would then be impossible. Such a report retains the observed sample count and marks the full batch incomplete; it does not pretend that the unrun trials were measured. A failed initial driving screen should be diagnosed before starting a larger comparison.

## Evidence and interpretation

For each request, record observation capture, request start, complete response, and action application times. Compute observation age at application, plus API round-trip time and MCP/control-queue time. Record physics lateness independently.

For each trial, save configuration, seed, track/handling version, model/provider identity, observations and actions, completion, lap times, checkpoint progress, off-road time, rescue count/events, discarded pre-rescue commands, errors, token usage, cost, and a replay. The SVG viewer shows the track, kart, progress, current controls, rescue state, and whether the driver is waiting for a reply.

Report completion out of all ten trials, completion without rescue, rescue counts, median completed-run duration relative to the paired reference, off-road time, action-age distributions, errors, and cost. Preserve failures in the completion denominator. Show sample counts and mark any interrupted batch as incomplete. Assisted results establish only assisted solo driving in this configuration. They do not establish unassisted control, collision handling, multiplayer capacity, embedded client compatibility, or universal model superiority.

## Following milestones

If solo driving works, add a competing kart and collisions, then power-ups and six/eight-driver load tests. Separately add Temporal race lifecycle orchestration and measure its overhead and recovery behavior. General-purpose agent clients, OAuth, matchmaking, leaderboards, embedded spectator UI, production hosting, and 3D presentation follow that evidence.

## References

- [Project plan](../plan.md)
- [Verified API and model research](../research/decision-models.md)
- [Racing time decision](../adr/0001-racing-time-is-independent-of-model-responses.md)
