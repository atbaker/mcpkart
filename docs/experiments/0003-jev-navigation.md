# Jev navigation: compact observations and control language

October 18, 2026. Continue the user's Jev-only PoC. The best previous screen reached 108/120 checkpoints and two completed laps, with 26 rescues, before the 170.1 s deadline. It did not pass.

## Hypotheses

1. The large road/physics report draws attention toward future curve direction instead of the kart's immediate heading, motion, and edge clearance. A compact view with present pose clearly separated from upcoming road may make correction easier.
2. The original criteria describe controls as “Steer +0.5; accelerate.” Explicit descriptions of an absolute held wheel angle may be easier to interpret. Both descriptions map to exactly the same fifteen physical inputs.
3. Some saved failure observations are already beyond recovery after a typical response delay. Evaluate earlier moments as well as late failures, rather than expecting an impossible recovery.

Track, handling, action values, 60 Hz clock, three-second stopped rescue, MCP transport, route, and race deadline remain fixed. There is no automatic steering, racing line, computed target speed, or selected-control recommendation in these observations.

## Candidates

| Profile | Evidence |
| --- | --- |
| `road_physics` | Previous best observation; retained as a control. |
| `compact` | Current lane position/clearances, kart nose and velocity relative to the road, road-frame lateral velocity, wheel/yaw state, six nearby centreline points, and the next two bend summaries with current-speed grip demand and constant-speed time to their peaks. |
| `compact_text` | The same compact factual evidence with pose and road facts expressed in short prose. |
| `compact_inputs` | `compact` with the current action's label replaced by its physical steering/throttle/brake values. This tests a possible lexical anchor while retaining the held-input information. |
| `road_compass` | A further factual view describing the road centre and tangent relative to the kart, with explicit left/right bearings for nearby points. Current velocity, wheel and yaw remain numeric; bend summaries are selected within a 22 m preview window and any full-bend extent beyond it is labelled. |

Control language is a separate factor. `numeric` preserves existing criterion descriptions. `explicit` names left/right, absolute wheel angle, and throttle/brake values. The model still chooses the complete steering/pedal input; the adapter supplies no driving policy. Changing control wording alone leaves the racing instructions identical; the separately labelled instruction experiments below change those instructions deliberately.

## Diagnostic evidence

An exact replay of the previous Jev run confirms that countersteering helps. At the early left-drift state (tick 200), a fixed 200 ms response delay followed by 400 ms of hard-right braking leaves 0.826 m road margin. Left acceleration instead leaves the road. At the later tick 212, every available action leaves the road under that delay; it is useful for comparing harm, but cannot demonstrate successful prevention.

At right drift tick 503, left braking leaves 1.045 m margin and reduces nose error to 2.1°; left acceleration leaves only 0.265 m margin and 10.1° error. Right acceleration leaves the road. These are short open-loop diagnostic alternatives, not unique ground-truth labels or a controller used during racing.

The brake audit also rules out a permanent on-road stopping loop: all 71 previously observed slow on-road decisions selected acceleration. Most time stopped with braking held occurred on grass. Earlier slowdown, steering correction, and timely brake release remain relevant.

## Protocol

Use six fixed situations: first bend approach, synthetic left-drift correction, and the recorded left/right correction states both early and late. Early cases are exactly twelve ticks before the late cases, reconstructed from original commands and rescues and validated against runtime pose/progress samples. Do not select cases by a newly optimized control policy.

Run three interleaved repeats per profile for Jev, retaining every request, response, error, action distribution, confidence/probabilities when returned, input size, latency, and cost. Use repeated samples to check whether a promising one-off action persists. Static short-rollout effects and reference agreement remain diagnostics, not proof of successful driving.

First compare the three observation profiles with original numeric control wording. Then compare explicit control wording on a selected candidate using the same states and repeats. Promote a promising configuration to a separately recorded live screen at seed zero, against the unchanged 56.7 s scripted reference and 170.1 s deadline. Record actual checkpoint progress, off-road time, rescues, completion and timing validity. A promising single screen still does not establish the eight-of-ten completion/pace target.

All stages share the existing $10 budget ledger and the saved TypeSafe route. No paid calls to other models. Preserve previous results and use a fresh artifact directory for each configuration.

## Results

The previous [telemetry iteration](0002-track-telemetry.md) remains the baseline. The first 54 repeated requests all succeeded. Compact structured telemetry chose hard-left braking at the first bend in all three repetitions; road physics selected left acceleration in all three, and compact prose selected straight coasting. Compact structured telemetry also chose straight acceleration in all three synthetic left-drift cases, where the road profile selected left acceleration twice.

However, every profile still chose left acceleration in both recorded left-oversteer states on every repetition. Smaller reports did not solve the central correction problem. Exact held-action labels were repeated in 44/54 answers (13/18 road physics, 13/18 compact, 18/18 compact prose). This correlation motivates the held-input representation test; it does not prove that copying causes the mistakes.

The 18-request explicit-control follow-up also returned valid choices throughout. It preserved braking at the first bend but changed all three synthetic drift corrections back to left acceleration. It did not fix either recorded left-oversteer state. More verbose control wording has no demonstrated advantage and is not selected merely for being more descriptive.

The held-input diagnostic returned 18 valid choices, without fixing left-oversteer correction. It also changed the right-oversteer cases to wrong-way right braking. Removing the label alone is insufficient, and exact copying is not an established cause.

An 18-request follow-up prefixed the same instructions with an explicit question asking which input should be applied **next**. This factor is labelled `question_first`; the original remains available and unchanged. The prefix adds no computed steering, per-state recommendation, or driving rule. It still did not fix the left-oversteer states. All actual instructions and criteria are retained in the request evidence.

A separate `driving_guide` instruction style adds general driving principles: correct heading/motion toward the road, unwind steering while slowing, and release braking to keep moving. This deliberately changes strategy instructions, which are part of the planned human-guided experience; it is distinct from the pure observation comparisons. No code chooses or overrides a control. Across 18 valid requests it corrected steering direction in both recorded left-drift states on all repeats, but selected wrong-way right steering in the right-drift cases on every repeat. This is not a general solution and the guide is not promoted on that evidence.

The final factual candidate describes the **road's** direction from the kart instead of describing the **kart's** direction from the road. The former says “road to your right” when the latter says “kart left of the road.” Across 18 valid requests, it corrected the synthetic left drift on every repetition, but still chose left acceleration in both recorded left-drift states. It also changed first-bend braking to straight acceleration. Equivalent spatial wording alone did not resolve the harder failures.

All 144 static requests returned admissible choices. The eight configurations each saw the same six situations three times. These small repeated samples demonstrate persistent mistakes in these particular states, not a general model success rate. Identical earlier first-bend payloads have also produced different answers across batches; three matching answers are not proof of deterministic behavior or a causal improvement.

### Live screen

`compact`, numeric controls and original instructions were selected for a live screen because they preserved first-bend braking and avoided accelerating farther left in the mild synthetic drift. The more difficult recorded corrections were still unresolved before this trial. Both screens below use seed zero, the same pinned Jev/TypeSafe route, identical simulation/rescue settings, a 56.7 s reference, and a 170.1 s deadline.

| Metric | Previous `road_physics` | New `compact` |
| --- | ---: | ---: |
| Ordered checkpoints | 108/120 | 52/120 |
| Completed laps | 2 | 1 |
| First lap | 60.70 s | 54.42 s |
| Off-road time | 78.00 s | 66.33 s |
| Rescues | 26 | 21 |
| Requests / errors | 805 / 0 | 693 / 0 |
| Median API latency | 170.60 ms | 197.36 ms |
| Median observation-to-application age | 184.35 ms | 217.15 ms |
| Maximum physics lateness | 87.05 ms | 90.70 ms |
| Timing valid | yes | yes |
| Completed three laps | no | no |

The compact screen improved its first-lap time and reduced off-road time and rescues, but made substantially less ordered progress overall. Driving farther (992 m versus 923 m) did not translate into checkpoint credit. Two stalls dominate: checkpoint 46 to 47 took 60.43 s (race time 66.13 to 126.57 s), and after checkpoint 52 at 135.57 s there was no further credit before the deadline. In 128/426 on-road observations the required checkpoint was behind the kart, versus 0/433 in the previous road-physics screen. The model kept circulating without satisfying the next required gate.

It is not promoted: **`road_physics` with original instructions and numeric controls remains the default.** One screen per configuration cannot separate observation effects from response variation and route latency, which was higher in this run. Neither configuration meets the completion or pace criterion. A useful next experiment is making missed-gate status and time since credited progress explicit, alongside short observation history to expose growing heading error. These would be factual additions; the model would still choose every control, and checkpoint rules would remain unchanged. They are proposals, not tested improvements.

The new run's clock advanced 170.1 s in 170.1012 s wall time, with 2.55 ms p95 lateness, within the existing clock limits. No physics, action values, rescue behavior, checkpoint rules, or deadline were relaxed to obtain these results.

### Reproduction and evidence

Ignored local artifacts preserve every call and configuration:

| Directory under `artifacts/` | Configuration | Requests |
| --- | --- | ---: |
| `jev-compact-numeric-v1` | Road physics, compact JSON, compact prose; original numeric controls/instructions | 54 |
| `jev-compact-explicit-v1` | Compact JSON, explicit controls, original instructions | 18 |
| `jev-held-inputs-v1` | Compact physical held inputs, original controls/instructions | 18 |
| `jev-next-question-v1` | Compact physical held inputs, next-input question prefix | 18 |
| `jev-driving-guide-v1` | Compact physical held inputs, general driving guide | 18 |
| `jev-road-compass-v1` | Road-relative compass facts, original controls/instructions | 18 |
| `jev-compact-live-v1` | Compact JSON, original numeric controls/instructions, seed zero live screen | 693 |

Probe manifests preserve exact wire instructions/criteria, repeat order, source fingerprints, fixtures and pinned routes. The live report preserves its criteria and source fingerprint; its `experiment.json` sidecar records the unchanged original instruction text after the trial without rewriting original evidence. Future live reports also save exact instructions directly, and resume checks reject incompatible simulation settings, baseline duration or route.

This iteration used about $0.0664, including the static probes and live screen. The persistent ledger now conservatively charges **$0.53214 of the $10 cap** across all experiments, including uncertain earlier requests. Provider-reported total cost is $0.48312; no reservations remain pending.

Validation: 171 tests pass and Ruff is clean. New tests cover compact-frame geometry and signs, equivalent factual prose, road-relative compass transforms, unchanged physical action mappings, provider-choice preservation, repeated fixture ordering, source/instruction provenance, and refusal to resume incompatible experiments. Live timing validity is assessed separately from unit tests.

## API note

The [OpenRouter Decisions reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) documents typed choices and optional probability/confidence data. We retain those diagnostics without overriding the returned choice. No undocumented sampling or temperature controls are added.
