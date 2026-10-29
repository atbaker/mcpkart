# Experimental Jev question-context driver

This guide retains the historical solo interface. The current competitive
mode and $20 cumulative ledger are covered by the [two-kart guide](two-kart-driver.md).
The public solo CLI below enforces its former $10 ceiling and safely rejects
the expanded ledger; it does not implicitly select the newer goal-only duel
prompt. All earlier paid windows remain closed.

The question-local prompt places the current wheel facts inside the wheel
question and the current pedal facts inside the pedal question. Both questions
are answered in one Decisions API POST. The wheel has five choices and the
pedal has three; their original native inverse produces one of the same
fifteen controls. Jev selects both answers. The host supplies geometry and
motion facts, including a bearing computed from the supplied coordinates,
and does not evaluate a policy condition to select the kart's controls.

The unchanged research prompt completed eight fresh solo stadium starts
cleanly in [0053](experiments/0053-fresh-start-validation.md), following the
positive [paired pilot](experiments/0052-native-compatibility-driving.md).
It follows a supplied fixed bearing/edge policy. This is evidence for a
24 m solo stadium in two directions with small start-pose variations;
other tracks, opponents and recovery outside its domain remain untested.
The application default and joint `damped` baseline are unchanged.

The subsequent versioned-driver smoke and model comparison bring the Jev
record to 14/14 useful, 13/14 clean finishes. OpenAI completed both matched
comparison starts cleanly with this unchanged setup. See the
[current findings](experiments/2026-10-21-progress-checkpoint.md) and
[portable examples](experiments/current-driver-examples.json). All prior paid
windows are closed; Clef is set aside after the separate 0069 timeout.

## Goal-only driving

Study [0070](experiments/0070-question-local-policy-ablation.md) adds optional
`prompt_mode="goal"` to the Python client and recorded driver. It retains facts
inside each question and physical menus while removing the supplied action
policy and worked examples. Goal-only finished one of two starts cleanly;
the other stopped under the unchanged forward-preview guard while still
on-road after a 2.197-second reply.

Study [0071](experiments/0071-goal-only-recovery-domain.md) adds explicit
`extended_domain=True` for the goal-mode client and driver. It admits finite,
nonzero preview vectors with `ego_x_m <= 0` and known uncredited gates with
positive signed plane. It computes the same factual bearing and changes no
prompt strings, measurements or actions. Four goal-only races finished
cleanly in 79.52–81.63 seconds; none used the extended domain, so recovery
remains untested. [Exact examples](experiments/0071-goal-only-recovery-domain-prompts.json)
preserve the actual questions and native replies, including the 1.38-second
latency event.

Set both `prompt_mode="goal"` and `extended_domain=True` explicitly when
constructing `QuestionContextDriver` under a new registered experiment.
The extension rejects policy mode. The public CLI below retains the historical
policy mode and guarded domain; it does not select goal mode implicitly.
All paid windows are closed. No new application default is claimed.

Study [0072](experiments/0072-goal-only-challenge.md) adds an optional recorded
`start_pose={"offset_m": ..., "heading_error_rad": ...}` to `Simulation` and
`race_setup`, for stationary starts at track distance zero. Default starts
are unchanged. Both admitted challenge races finished with rescue; no clean
or unassisted recovery result was established. All 3,582 prior question sets
remained exact. [Actual challenge excerpts](experiments/0072-goal-only-challenge-prompts.json)
include the behind-preview choices. The public CLI has no custom-pose flag.
At the 0072 closure only 779 request slots remained, below its admission floor.

Study [0073](experiments/0073-goal-only-wheel-motion.md) adds optional
`include_wheel_motion=True` for projection, client and recorded driver, with
`prompt_mode="goal"`. It adds only `wheel_facts.motion`: current speed in m/s,
actual steering angle in rad, yaw rate in rad/s, held native input and units.
The actual steering measurement is distinct from the held input target.
Default questions, goal-rule text and the entire pedal question stay exact.
All four new free interface controls qualified; all four actual Jev races
finished and passed full audits. Motion was clean clockwise (83.12 s), while
minimal used three rescues (94.63 s); both recovery arms used one rescue before
their first gate. Natural API delays differed, so a causal improvement is not
established. See [actual requests/replies](experiments/0073-goal-only-wheel-motion-responses.json).
The comparison is closed. The public CLI retains its original guarded policy mode.

Study [0074](experiments/0074-goal-only-wheel-motion-repeats.md) ran eight
repeat races of the same comparison. All four clockwise runs were clean; all four recovery
runs needed one rescue. Motion reduced no paired rescues and was slower in all
four pairs. The pilot advantage did not reproduce; do not promote this option
as a proven improvement. Both minimal recovery repeats obtained a forward
preview before rescue but credited their first gate only afterward. No
production source changed. The [geometry proposal](experiments/0075-wheel-road-geometry-proposal.md)
was only a design at that checkpoint; the later execution is described below.

Study [0075](experiments/0075-goal-only-wheel-road-geometry.md) implements explicit
`include_wheel_road_frame=True` for projection, validation, question construction,
client and recorded driver. Goal mode is required; defaults are false and the
public CLI remains unchanged. It adds current raw road-minus-kart heading in
radians and existing pedal edge clearances inside `wheel_facts.road_frame`,
with descriptive units. Goal rules, pedal question, menus and native inputs
remain exact; motion was disabled in both comparison arms. All four recovery
races finished with rescue; zero earned a gate before rescue. No benefit was
demonstrated. 534 tests/3 optional Rust skips, full old-question parity, 34
native mocks, four new free controls and every actual race audit passed.
The study is closed; [actual examples](experiments/0075-goal-only-wheel-road-geometry-responses.json)
retain the real requests and native replies.

## Run one race

Start the process-isolated Python spectator/MCP server as usual. Configure
`OPENROUTER_API_KEY` through the environment's secret binding. Preserve the
shared `artifacts/budget.json`; the command requires an existing ledger and
preserves its saved request and token authorizations.

After a new authorized experiment window is established, the command in this
qualified cloud checkout is:

```bash
.venv/bin/python -m mcpkart.question_context_run \
  --seed 43 --course stadium \
  --clock-qualification artifacts/jev-goal-challenge-v1/clock/qualification.json \
  --output artifacts/jev-observed-race
```

Use `--course stadium_clockwise` for the other direction. Output must be a
new directory. The command runs exactly one three-lap race on the fixed 24 m,
12 m/s, 0.12 rad setup and never starts another race automatically. An optional
`--stop-at` accepts an absolute ISO8601 deadline with timezone. The default
800-decision ceiling bounds this single race. The MCP URL defaults to
`http://127.0.0.1:8765/mcp`; `--url` overrides it.

The engine clock qualification must belong to the current source, boot and
server process, and include the complete pause, control and long-clock gates.
A new environment needs a fresh qualification. With many recordings, explicitly
warm the idle `/api/replays` catalog before the first MCPstart; see the recovery
note in [cloud-development.md](cloud-development.md). The October20new-boot
qualification includes that warm-cache condition. For experiment collection,
complete the exact-interface free controls and native compatibility checks
specified in the study before paid use; this command does not run or invent
those qualification results. See [0054](experiments/0054-versioned-driver-smoke.md)
for the extracted wrapper's integration qualification and current status.

## Recordings and domain

`trial.json` contains the ordinary race and full physics samples. Its request
records retain raw observations, projected facts and actual wire questions.
The race header contains question templates. `query-*.json` and `calls/`
save the actual per-query questions, raw request/response bodies, native
records and budget transitions. Authentication headers are excluded. Source
hashes for all three controller modules are separate from the existing core
engine fingerprint, which does not include these new modules.

With the default guarded domain, a nonforward 15 m preview or a positive
uncredited required gate ends the attempt before a further model POST.
The explicit goal-only extension admits these poses; malformed, nonfinite
or zero-range geometry still stops before spend. Invalid native
answers, identity mismatches or uncertain accounting stop the driver without
returning a control. A stopped driver cannot resume. The server's existing
three-second off-road rescue remains part of the recorded game rules.
