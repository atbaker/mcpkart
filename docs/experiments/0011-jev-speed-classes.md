# Jev speed classes, simpler courses and visual observations

Status at this experiment's conclusion: paused at the saved request allowance.
The user subsequently approved 50,000 requests with the same $10 cap; see the
[resumed prompt experiment](0012-jev-prompting.md). The user authorized several hours of
experiments, including changes to course difficulty and kart speed, and explicitly
selected the isolated **Python** runtime. All work shares the existing $10 model
budget and 25,000-request ceiling. Starting charge: $0.991016380, 10,086 requests.

Best current setting: a radius-30 m circle, 16 m road, 18 m/s speed ceiling,
0.06 rad wheel range, `road_navigation` observations and `geometry` choice
descriptions. Six attempts across three starts in each direction all finished
three laps without rescues, in 32.38–32.55 s. Five are production-code follow-ups
to the initial screen; this is not ten-seed qualification. The original winding
course remains unsolved. A constant full turn also succeeds on this easy circle,
so the result establishes a novice configuration rather than general navigation.

## Questions and comparison rules

The earlier [Cloud screen](0010-jev-on-codex-cloud.md) had valid timing but only
68/120 gates. Its largest gate stall cost 63.53 seconds; repeated steering inputs
also carried the kart across the road before it could recover.

Test whether slower speed classes, simpler geometry, wider roads, a less sensitive
wheel range, or a more visual observation can establish direct driving. These
are deliberate new game configurations, not improvements claimed on the frozen
original winding course. Keep every setup fixed within a comparison and record
its complete configuration and paired reference. Avoid claims from one seed.

The original default remains the winding course, 9 m road, 24 m/s speed ceiling
and 0.32 rad maximum wheel angle. New CLI flags are `--course`, `--road-width`,
`--max-speed`, and `--max-steering-angle`. MCP `start_race` accepts the same
constructor fields in `race_setup`; the actual physics-child configuration is
saved and checked against the declaration. Custom setups use the Python engine.

| Initial setting | Course | Speed ceiling | Road width | Maximum wheel angle |
| --- | --- | ---: | ---: | ---: |
| Original control | Winding | 24 m/s | 9 m | 0.32 rad |
| Slower control | Winding | 8 m/s | 9 m | 0.32 rad |
| Simpler geometry | Symmetric oval | 8 m/s | 9 m | 0.32 rad |
| Wider geometry | Symmetric oval | 8 m/s | 16 m | 0.32 rad |
| Gentler steering | Symmetric oval | 8 m/s | 16 m | 0.12 rad |
| Novice fallback | Circle | 6 m/s | 16 m | 0.12 rad |
| Faster challenger | Symmetric oval | 12 m/s | 16 m | 0.12 rad |

The oval has semi-axes 45/30 m; the circle has radius 30 m. Each has a reflected
clockwise version for directional holdouts. They retain 256 centreline samples
and 40 ordered finite gates per lap. No course knows or chooses a driving input.
Steering remains an absolute held wheel angle, with the same fifteen normalized
steering/pedal combinations. Lower wheel range changes physical sensitivity,
not the number of choices or the model's control authority.

Retain continuous 60 Hz physics, three laps, three-second stopped rescue, stale
reply rejection, and the original 100/25/100 ms timing limits. The deadline is
three times each setup's own seed-matched scripted reference. Success still
requires eight completions in ten and median completed pace within twice that
reference; report rescue-assisted and zero-rescue completions separately.

## Visual evidence

The current TypeSafe Jev route advertises text and image inputs. OpenRouter's
[multimodal Decisions documentation](https://openrouter.ai/docs/guides/community/multimodal-decisions)
documents PNG/JPEG support for Jev, including nested `image_url` parts in state.
Images require at least 78,400 total pixels, with each side at least 256 pixels.
Every request containing an image uses TypeSafe's long-context mode, so measure
its latency rather than assuming the smaller observation is faster.

`scene_svg` supplies SVG markup as **text**. `scene_image` supplies an actual
384×384 PNG of the same geometry. Both retain identical compact numeric facts
and gate geometry while replacing the numeric future-road preview. The camera
is egocentric: yellow kart points up; grey is road, white marks its boundaries,
cyan marks the next finite gate, and blue shows half a second of present velocity.
The blue segment is a factual velocity vector, not a recommended trajectory.
Neither representation includes a chosen steering input or computed speed target.

Image requests conservatively reserve the route's complete advertised input
context, since compressed file length does not bound expanded image tokens.
The normal $10 ledger and request/token ceilings remain enforced. SVG and image
profiles have explicit larger request guards; existing numeric limits stay fixed.

## Qualification and evidence

Before new live screens, run the complete free timing gate on the updated source.
Run appropriate free scripted controls for changed physical setups and preserve
their paired offline references. Stop on a timing failure; retain every attempt
and investigate before further paid driving. Finish builds, tests and analysis
before timed trials.

The initial code passes 317 tests, with three optional Rust skips, and Ruff.
Tests cover unchanged original configuration, symmetric/mirrored geometry,
speed clamping without automatic steering, custom reference validity, settings
reaching the real Python child through MCP, configuration-aware replay, camera
transforms, valid image dimensions, and conservative multimodal budget admission.

Ignored evidence belongs under `artifacts/jev-leagues-v1/` and separately named
screen directories. The initial protocol records a maximum five-hour work window,
the shared starting ledger, exact source fingerprint and stop conditions. Select
fixed snapshots before viewing candidate answers; compare repeated static choices
before promoting a representation. Keep static rollouts diagnostic, then use
recorded closed-loop trials and cross-seed checks to assess actual navigation.

## Initial single-seed screens

These are exploratory seed-zero attempts, not qualification results. Every row
uses the isolated Python engine and retains the original direct fifteen-choice
control menu. Width is 9 m and wheel range 0.32 rad unless shown otherwise.

| Configuration / observation | Gates | Elapsed (s) | Rescues |
| --- | ---: | ---: | ---: |
| Winding, 24 m/s, numeric | 95 | 170.10 (deadline) | 24 |
| Winding, 8 m/s, numeric | 96 | 286.40 (deadline) | 38 |
| Oval, 8 m/s, numeric | 120 | 223.60 | 32 |
| Oval, 8 m/s, width 16 m, numeric | 120 | 211.43 | 29 |
| Oval, 8 m/s, width 16 m, wheel 0.12 rad, numeric | 120 | 112.42 | 5 |
| Oval, 12 m/s, width 16 m, wheel 0.12 rad, numeric | 120 | 83.97 | 5 |
| Circle, 6 m/s, width 16 m, wheel 0.12 rad, numeric | 120 | 94.78 | 0 |
| Circle, 12 m/s, width 16 m, wheel 0.12 rad, numeric | 120 | 47.93 | 0 |
| Circle, 18 m/s, width 16 m, wheel 0.12 rad, numeric | 120 | 76.93 | 7 |
| Gentle oval, 8 m/s, SVG text | 120 | 177.05 | 11 |
| Gentle oval, 8 m/s, PNG input | 105 | 272.15 (deadline) | 21 |

All have valid timing and independently verified exact replay. The narrow oval
and 18 m/s circle each had one five-second endpoint timeout, with no retry. The
runner stopped each batch after its affected trial for investigation. The first
timeout was followed by 217 successful calls in that same race; the second was
the final request, with the held control completing the race during its wait.
Both conservative reservations remain charged.

Reducing speed alone did not solve the winding course. Gentler wheel range made
the largest improvement on the oval, but Jev still commonly held left steering
while departing the left boundary. The 6 m/s circle used moderate-left
acceleration for 373 of 378 on-road decisions, so its success is a narrow
course/handling result rather than evidence of general navigation.

The live visual comparison did not improve performance. PNG and SVG preserve the
same compact numeric facts and drawing geometry; the richer numeric control has
a different road preview, so this is a comparison of complete representations,
not a clean estimate of image content alone. PNG had a 53.55 s gate stall and SVG
a 62.57 s stall. Both had zero endpoint errors and valid clocks. Retain numeric
driving as the candidate.

## Reference correction and second phase

Inspection found that the scripted comparison driver divided its desired wheel
angle by the original 0.32 rad range even for custom handling. It now receives
the declared maximum wheel angle in offline references, free live controls and
latency fixtures. Its default behavior remains unchanged. Preserve the first
references under `references-v1-assumed-steering`; the initial recordings retain
their original declared references rather than silently rewriting their scores.

Corrected seed-zero references are 89.45 s for the gentle 8 m/s oval, 59.92 s for
the 12 m/s oval, 94.40 s for the 6 m/s circle and 47.57 s for the 12 m/s circle.
The main screening conclusions survive this correction. A full second timing
gate qualifies the updated source before paid racing resumes.

The second phase adds a stadium: two 60 m straights joined tangentially by radius
30 m semicircles, plus its reflected clockwise version. It preserves the ordered
gates and requires steering changes that a constant circle input cannot supply.
Its corrected free references finish with zero rescues at 8 and 12 m/s. A
`near_field` observation supplies only observed centreline points through 15 m,
actual kart motion/pose, declared handling, progress and the next gate. It derives
no steering choice, selected path or speed target. Tests cover its coordinate
invariance and the reference correction; 326 pass with three optional Rust skips.

The frozen initial qualification candidate is the 12 m/s, 16 m wide circle with
0.12 rad wheel range and original numeric `road_navigation` observations. Seed
zero remains screening evidence; seeds 1–10 are reserved for qualification.

The completed circle qualification achieved **10/10 completions, 7/10 without
rescues**, and median time 47.8583 s (1.00578× its paired reference). All clocks
passed; worst lateness was 9.3477 ms. There were four rescues, one timeout among
2,072 calls, and $0.201523644 charged. The timeout race retained its result; three
subsequent requests succeeded before the remaining declared seeds continued.
All ten recordings passed independent exact replay. This meets the assisted
criterion, while missing the stricter eight-of-ten zero-rescue criterion.

A free constant-`left_accelerate` diagnostic also finishes all three tested
circle seeds without rescues. On the stadium it finishes all three with 18
rescues in about 146 s, within twice the reference. Therefore completion/pace
with unlimited rescues is too weak to establish navigation even on this stadium.
Keep zero-rescue counts and the constant-control baseline visible; do not present
the circle result as learned general driving or a solution on the winding track.

The clockwise holdout used the same physical settings, original numeric
observations, and three declared seeds. All finished, in 94.18, 60.68 and 47.80 s,
with seven, three and zero rescues respectively. All clocks and endpoint calls
passed. The stadium screen finished in 101.48 s (1.313× reference), with six
rescues and no endpoint errors. This beats its constant-left baseline's 18
rescues, but still does not establish clean straight/curve transitions.

## Additional observation and control diagnostics

A 120-call fixed-state comparison of rich numeric, short numeric, explicit
control wording, road-compass wording and a general driving guide found no
general correction improvement. The guide improved some left-drift cases but
continued to mishandle right drift. These cases were selected before candidate
answers; later follow-ups reuse previously inspected diagnostics and are not
held-out validation.

Another 120-call comparison tested literal road-position prose and factorized
steering/pedal questions. Both questions are answered by Jev in **one** HTTP
request; their pair maps deterministically to one of the existing fifteen
physical inputs. No partial answer, probability blend or coded steering policy
is applied. Native requests/answers, component choices, composed action and
helper hashes are retained. Local mock checks cover all fifteen combinations,
refusal, invalid components, provider identity and admission before oversized
requests.

The combined word/factorized profile corrected all six selected drift snapshots,
but regressed in the real oval: 247.58 s, eleven rescues and an 81.68 s gate stall.
The joint-choice word profile finished in 155.87 s, with seven rescues and a
40.43 s stall. Both had valid timing and zero endpoint errors. Neither is promoted.

A separate forward-model prototype exposes conditional forecasts for **every**
allowed input. It reconstructs rounded public pose/velocity and published physics,
holds the old input for a declared 0.30 s, then simulates each candidate for 0.5
and 1.0 s. The hypotheses disable rescue and clearly state that assumption. Code
does not rank, filter, score or select an input; Jev still chooses the complete
native joint action. This is Jev with a supplied forward model, distinct from
perception-only observations and from the unchanged direct-driving benchmark.

Local checks cover all fifteen actions in nine fixtures against actual simulation
forks, public-state rounding tolerances and non-mutation. Forecast computation
cost about 62 ms per decision. A free live control with this load completed in
89.53 s without rescues, worst clock lateness 4.00 ms. A 48-call static follow-up
was mixed. The actual oval screen finished in 115.82 s with four rescues,
versus 112.42 s and five rescues for the original numeric screen. Its median
API latency was 221.85 ms, but median action age rose to 316.51 ms and p95 to
400.59 ms. Timing/replay passed and there were no endpoint errors. A single
slightly lower rescue count does not establish an advantage; it is not promoted.

## Free latency sensitivity

Ninety offline geometric-reference trials cover six setups, three seeds and
fixed delays of 0, 200, 350, 600 and 1,000 ms. All novice configurations complete
without rescues at 200 ms; the original winding course does so in two of three
seeds. At 350 ms none of the tested configurations achieves a zero-rescue
completion with this fixed reference controller. This is controller-specific
sensitivity, not a universal driveability limit or real-time scheduling result.
It makes additional observation computation a material tradeoff: better cues
must offset older actions. Detailed free results remain in `offline-delay-sweep`.

## Handling interpretation

Speed and wheel range must be considered together. Ideal nominal body yaw is
`speed / wheelbase * tan(wheel_angle)`, capped by the current grip divided by
speed. At 24 m/s the original full wheel setting is grip-limited to about
31 degrees/s. At 8 m/s it can approach 84 degrees/s. Therefore a lower speed cap
can increase turning sensitivity and make held-input mistakes worse, despite
reducing distance travelled during inference. These are physical bounds, not
measured steady trajectories or a recommended driving policy.

With a 0.12 rad maximum wheel angle, the moderate choice is 0.06 rad, whose
nominal bicycle radius is 29.96 m—almost exactly the novice circle's 30 m.
The original moderate choice, 0.16 rad, has an 11.15 m nominal radius. This
explains why the circle/handling match helps even a constant input. It also
limits what that result says about Jev's ability to correct arbitrary poses.

## Bounded steering and fixed geometry in the choice menu

An intermediate winding setup (12 m/s, 16 m width, 0.20 rad wheel range) had clean
free references but timed out at 55/120 gates with 25 rescues. Its longest gate
stall was 64.22 s. Its timing and exact replay passed, with no endpoint errors.
This setting is not promoted as a solution on the winding course.

A new circle setting limits the maximum wheel angle to 0.06 rad. Its **full**
wheel choice now has a nominal 29.96 m radius; its moderate choice has a 59.98 m
radius. At 18 m/s a constant full turn completes the circle in 32.18 s without
rescues on all three tested seeds. This is explicit handling calibration, not
an improvement claimed on the original vehicle or winding course.

With original numeric choice descriptions Jev timed out at 99/120 gates in
120.57 s, with twenty rescues. It kept choosing moderate steering despite the
changed wheel range. That attempt had one timeout followed by 334 successful
calls; timing/replay passed and the uncertain reservation remains charged.

The `geometry` control language puts each input's actual fixed wheel angle and
nominal bicycle radius in its criterion description. It uses **only vehicle
handling and the input definition**—no current pose, road geometry, future state,
ranking, target or selected control. Racing instructions and all fifteen native
choice IDs remain unchanged. For this vehicle, full left is described as
3.44 degrees / 30.0 m, and moderate left as 1.72 degrees / 60.0 m, before grip
and steering-response transients. This moves existing physical facts into the
choice descriptions rather than asking Jev to associate a separate numeric table.

The seed-zero screen with those descriptions completed in **32.43 s with zero
rescues**, versus the numeric-menu timeout on the same configuration. It used
135 calls with no errors, and worst clock lateness was 5.90 ms. The constant-turn
baseline remains essential: this is a deliberately easy course/handling match,
not proof of general navigation. Replication and directional checks are recorded
separately from the screening attempt.

The five declared production follow-ups also finished without rescues: two more
counterclockwise starts and three clockwise starts. Including the screen, the
six attempts take 32.3833–32.5500 s, median **32.4250 s**, median **0.80613×**
their seed-matched scripted references. All 820 model calls succeeded, every
clock passed (worst 13.2594 ms), and independent exact replay passed for all six.
Total charge for these attempts: $0.093033108. The scripted reference uses a
conservative speed policy; beating it does not establish an optimal racing line.
These are six descriptive replications across two directions, not a ten-seed
qualification. All configurations retain the stopped three-second rescue and
ordered finite gates; zero rescues means recovery was available but unused.

The description generator is now available through `--control-language geometry`.
It requires declared vehicle handling, preserves native provider choices and
racing instructions, and uses an explicit larger text admission guard. Tests
cover the actual geometry, missing/invalid handling, all native choice IDs and
wire instructions, and payload guards across every observation profile. The
promoted descriptions match the screen's prototype byte-for-byte for all fifteen
inputs. Validation: 347 tests pass, three optional Rust tests skip, and Ruff passes.
The probe CLI also retains the environment proxy and reserves image contexts.
Its standard fixture collection remains for the original frozen course; the
custom-course static experiments here use the saved configuration explicitly in
their separate helpers. The benchmark CLI above supports the declared custom
courses and handling directly.

Reproduce the configuration with a fresh output directory and the existing shared
ledger. These commands require available request/token/dollar allowance and do
not reset any spending. Qualify timing in each new environment first.

```sh
.venv/bin/python -m mcpkart.bench reference --course circle --road-width 16 \
  --max-speed 18 --max-steering-angle 0.06 --seeds 3 --delays 0 \
  --output artifacts/bounded-circle-reference.json
.venv/bin/python -m mcpkart.bench live-reference --course circle --road-width 16 \
  --max-speed 18 --max-steering-angle 0.06 \
  --reference artifacts/bounded-circle-reference.json \
  --output artifacts/bounded-circle-free
.venv/bin/python -m mcpkart.bench compare --models typesafe/jev-1.14 \
  --course circle --road-width 16 --max-speed 18 --max-steering-angle 0.06 \
  --telemetry road_navigation --control-language geometry --trials 3 \
  --reference artifacts/bounded-circle-reference.json \
  --output artifacts/bounded-circle-model
```

Use `circle_clockwise` in all three commands for the reflected course. The course
and handling arguments must match the paired reference and actual Python worker.

## Final audit and handoff

All 36 paid driving attempts are retained, including failures. Each passed
independent exact replay and the original clock limits, with a verified isolated
Python physics worker. Worst paid-trial lateness was 50.461936 ms. All 14,363
successful driving responses identify `typesafe/jev-1.14-20261014` / `TypeSafe`;
the other four requests timed out. The additional 480 static requests are
accounted separately. The final audit reconciles all **14,847 new requests**
and **$1.508110044** of new conservative charges exactly to the shared ledger.

The final source is
`2a743f475ed06537b8a7332e41a0ab0c8eb0f043a147917accb979527dd9f164`.
Its complete free gate passed three scripted races and a 170.1 s neutral-control
check, including the declared HTTP-parent pause. Worst race lateness was
13.74059 ms; the long check had 20.905167 ms maximum, 1.588868 ms p95 and
0.347398 ms drift. Separate free controls qualified both directions of the
bounded-circle setting on this source. Unit tests and lint remain 347 passed,
three optional Rust skips, Ruff clean. No Rust worker was used or required.

The shared ledger ends at **24,933 / 25,000 requests**, **$2.499126424 / $10**,
117,233,513 / 250,000,000 charged tokens, and no pending reservations. The saved
request guard leaves 67 calls—less than another complete race—despite remaining
dollar allowance. At this experiment boundary the guard had not yet been raised. Its exact
[boundary ledger](0011-budget-boundary.json) preserves all earlier charges and
uncertain calls. The user subsequently approved 50,000 requests with the same
$10 cap for the [prompt continuation](0012-jev-prompting.md).
`model-budget-snapshot.json` always tracks the latest shared ledger, including
that continuation; it is the snapshot to preserve across rebuilds.

Evidence under ignored `artifacts/jev-leagues-v1/` includes the three clock gates,
paired references, all native records, exact replays, declared protocols and
helper hashes. `final-audit.json` reconciles identities, direct choice mapping,
worker identity, timings and spending. `report/driving-results.csv` contains all
36 driving attempts; `report/trajectories.png` plots six representative examples.
The figure uses Matplotlib for analysis; it is not a race-runtime dependency.

The next paid checks should apply the new geometry menu to the original winding
course and the stadium, then qualify any promising fixed configuration on ten
declared starts. Additional replicas of this circle alone cannot establish
general driving, because its constant-turn baseline is already successful.
