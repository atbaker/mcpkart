# MCP Kart revival plan

Updated October 18, 2026. The current decision is to retain **process-isolated Python with asyncio pacing**: the [Python-on-GCP comparison](experiments/0009-python-on-gcp.md) passed three scripted races and a 170.1 s clock check, with 3.28 ms worst lateness. This qualifies the current solo workload for further Jev navigation experiments on GCP. Local Mac timing remains unqualified; no three-lap model completion has been established.

The user selected Python and requested a clean `main` handoff for Codex Cloud.
The [Cloud development guide](cloud-development.md), pinned setup script and
portable free controls support a fresh checkout. Qualify timing in that new
environment before paid Jev runs; preserve the latest shared spending ledger.
The optional Rust comparison remains available outside the default build.

The first experiment and three telemetry iterations are implemented. The [compact navigation iteration](experiments/0003-jev-navigation.md) tested observations, control wording and strategy instructions. The subsequent [gate/history experiment](experiments/0004-gates-and-observation-history.md) added explicit checkpoint geometry and past-only motion history; its new model screens were timing-invalid, and free controls reproduced local clock delays. The requested [process isolation](experiments/0005-isolated-physics-clock.md) passed three initial scripted controls, including an HTTP-process pause. A Jev screen had valid timing but reached only 63/120 gates. Later independent-clock diagnostics and a native sleeper control failed timing, holding local paid testing. The native pacer remains an explicit diagnostic option; road-physics remains the default observation candidate.

The first question is whether decision models can drive a kart in real time through MCP. The user narrowed the initial PoC to TypeSafe Jev 1.14 through OpenRouter on October 18. OpenAI Decisions and Cloudflare Clef remain later validation targets; existing measurements are preserved. The eventual product is a fun way for developers to experience the trade-off between model speed and intelligence by watching autonomous kart races.

The [Linux Docker comparison](experiments/0006-linux-docker-clock.md) also failed
its first timing control (104.26 ms maximum), despite completing all three laps.
It recorded a 102 ms state-publication span with substantial process CPU, a
different diagnostic from the low-CPU Mac bursts. Docker/container support is
implemented, but this local environment did not qualify for further Jev tests.

The [Rust worker experiment](experiments/0007-rust-race-engine.md) is implemented
behind the same Python/FastMCP interface. Deterministic parity and 276 tests pass
on macOS and Linux. The first scripted control passed, but the second reached
117.09 ms maximum lateness, so the batch stopped before Jev. Physics steps were
short; changing language and thread architecture did not establish reliability.
The subsequent [GCP comparison](experiments/0008-remote-linux-clock.md) passed
all three free races and the 170.1 s clock check on a four-vCPU C2D VM. Worst
free-control lateness was 0.86 ms. A timing-valid Jev navigation screen reached
50/120 gates with 24 rescues; its clock maximum was 1.20 ms. This establishes a
useful remote test environment, while driving viability remains unproven.
The VM and boot disk were deleted after evidence and budget updates were
downloaded.

The subsequent [Python-on-GCP comparison](experiments/0009-python-on-gcp.md)
used the same VM type, pinned environment, source, reference and limits. All
three races completed with zero rescues; worst race lateness was 2.22 ms.
The 170.1 s check peaked at 3.28 ms, with 1.30 ms exact p95 and 0.37 ms drift.
Independent replay and worker identity checks passed. The VM and boot disk
were deleted; no model calls were made. This supports keeping Python for the
solo PoC without requiring Rust's lower jitter. Multiplayer and Temporal
overhead remain unmeasured.

## Confirmed first milestone

- A solo kart completes three laps of a winding track at a useful racing speed.
- The initial target was eight completed runs out of ten without resets, and median completed race time within twice the scripted reference. During implementation the user added off-track rescue; the assisted experiment retains the completion/pace target but reports rescue counts and zero-rescue completions separately. Freeze track and vehicle handling within each comparison.
- The driver chooses steering, throttle, and braking directly. There is no automatic lane keeping or racing-line follower.
- Physics advances continuously in wall-clock time while model requests are in flight. The kart holds its last control input between decisions.
- Faster models get more opportunities to act: keep one request in flight per kart, apply its reply, then collect the next observation without imposing a common decision cadence.
- A thin Python driver converts Decisions choices into MCP control calls. Access models through OpenRouter's Decisions endpoint. Codex, Claude Code, and other general-purpose agent clients are evaluated later.
- The model receives structured telemetry and upcoming track geometry, including position, heading, velocity, and road boundaries, without suggested steering inputs. Image-based driving is a later experiment.
- A scripted driver establishes that the same track and physics are driveable and provides a comparison for the model.
- Start the simulation in Python as well. Consider Rust only if measured simulation or scheduling costs interfere with realtime operation.
- Development uses Python with a 2D SVG spectator view, locally or in a qualified Cloud environment. Traffic, collisions, and power-ups follow the solo milestone.
- Going off-road slows the kart down. After three continuous seconds off-road, a configurable rescue returns it near its departure point, aligned with the road, stopped and coasting. The clock and checkpoint progress continue; the teleport grants no progress. Older model replies are discarded after rescue. Ordered checkpoints prevent skipped gates, but permit ordinary corner clipping between gates.
- The first paid experiment batch has a total spending cap of $10 across all models.
- Current testing focuses on Jev. Establish passing solo driving before resuming other models; a Jev pass does not establish their performance.

These decisions were confirmed through the interview and the switch to OpenRouter. [The realtime timing decision](adr/0001-racing-time-is-independent-of-model-responses.md) preserves the intended comparison between intelligence and latency. The [first experiment specification](experiments/0001-realtime-driving.md) turns this scope into a reviewable implementation plan.

## What the first milestone establishes

A successful result establishes solo driving with this model, driver, observation format, track, and local network conditions. Competitive racing, general-purpose agent clients, multiplayer capacity, and production latency each require additional experiments.

## Experiment sequence

The following sequence implements the approved first experiment.

1. **Endpoint smoke test.** Confirm access to OpenRouter's `POST /api/alpha/decisions` with the three requested models. Record the request shape, model, provider, and failure modes without logging credentials.
2. **Physics reference.** Establish continuous simulation, a winding track, and a scripted driver. Measure simulation scheduling separately from inference. Freeze track difficulty and handling before measuring the model.
3. **Delay tolerance.** Inject controlled observation and action delays into the scripted driver. Determine which delays and jitter prevent it from maintaining control. This diagnoses sensitivity; it does not establish that a model will drive equally well.
4. **Decision latency.** Measure realistic changing observations and a small fixed control menu using a reused connection. Pin exact models and providers, disable automatic fallbacks and hidden retries, and record the actual returned route. Report sample counts, warm and cold behavior, latency distributions, errors, rate limits, and input usage.
5. **Closed-loop driving.** Run the Decisions driver through MCP while physics keeps advancing. Capture the observation, chosen action, when that action took effect, and a spectator replay. Compare completion and driving performance with the reference.
6. **Failure diagnosis.** Compare the same driver with and without MCP overhead, different action grids, and different observation sizes. Keep direct transport runs separate from the MCP milestone. Distinguish latency failures from poor decisions, incomplete observations, or inadequate controls.

The critical timing measure is **observation age when the action takes effect**, not time to first token. Capture observation time, request start, complete response, and action application using one monotonic clock wherever possible. Also measure simulation lateness so an overloaded Python loop cannot silently slow the game.

Track completion, progress, off-track time, lap times, action age, rejected or late actions, errors, and cost. Include sample counts with percentiles; a small smoke test cannot characterize the latency tail.

## Decisions API findings

OpenRouter documents a shared [Decisions endpoint](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) for the requested models. It accepts structured state and named questions, and returns choices or scores rather than requesting tool calls. The initial comparison uses `typesafe/jev-1.14`, `cloudflare/clef`, and `openai/gpt-6-luna-decisions`; Clef Flash is a possible additional comparison.

The driver asks for one choice among 15 explicit low-level control combinations and maps the answer to an MCP call. A joint choice keeps steering and acceleration decisions coupled. A score is a probability-weighted rubric result, not a generated steering angle.

The user supplied an OpenRouter API key locally as `OPENROUTER_API_KEY`, and initial measurements are underway; ChatGPT/Codex login is not part of the experiment's authentication. [The API research notes](research/decision-models.md) record the verified endpoints, schemas, model identities, and routing considerations.

## Temporal and language boundary

Keep the physics and inference timing loop independent of Temporal, then add Temporal orchestration and measure its effect. The GCP comparison qualifies the existing isolated Python worker for the current solo PoC; retain Python/FastMCP and asyncio pacing. Reconsider Rust if future measured workloads require it, including multiplayer or integration overhead.

For the platform, a Race Workflow could own admission, start, cancellation, completion, and results while a separate runtime executes continuous physics. A long-running Activity and an external race service are both candidates; recovery and interruption semantics need an explicit design.

[Temporal's Local Activity guidance](https://docs.temporal.io/local-activity) and [design notes](https://docs.temporal.io/design-patterns/local-activities) describe execution inside Workflow Tasks, result markers, and responsiveness constraints. Local Activities do not by themselves establish that a Workflow can host a responsive realtime race. This is an architectural hypothesis to test after model driving viability, not a settled production design.

## Implementation readiness

The user confirmed shared understanding of the experiment specification on October 18, 2026, including 60 Hz physics, 15 control choices, and a trial timeout of three times the scripted reference duration. Planning for the first PoC is complete. The next step is the offline physics and scripted-driver reference, followed by model trials when API access is available.

The local implementation and initial screens are complete. API access has been supplied and measurements are recorded under `artifacts/`. The no-rescue screen was stopped when the user requested the rescue experiment; its completed and interrupted recordings are preserved separately. The rescue timeout is an explicit game rule, not an unrecorded driving controller. The rescued raw-telemetry screen did not yield a three-lap completion; the user requested [clearer track telemetry](experiments/0002-track-telemetry.md) before further trials.

OpenRouter credentials are stored locally in the ignored `.env`. Exact provider slugs, route availability, and prices were recorded before paid runs. Clef Flash remains an optional follow-up to the three requested models.

## Later product scope

The broader concept remains autonomous three-lap racing with kart collisions, several power-ups, live spectators, public matchmaking, and service-operated bots. GitHub OAuth supplies racer identities; organization-based teams may follow. Race size remains undecided between six and eight racers.

Leaderboards should distinguish racer identity, model, and agent client or harness. Public self-reported entries and controlled model comparisons will need different evidence standards before they can support claims about the best model.

Browser spectator links, MCP Apps, and client-specific integrations need a separate compatibility investigation. A low-poly 3D presentation is a possible later evolution.

Production is intended for GCP and Temporal Serverless Workers. Hosting, service boundaries, multiplayer recovery, authentication, and capacity planning follow the local viability evidence.
