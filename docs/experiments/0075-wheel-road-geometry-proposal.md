> Archived proposal. The implemented four-race comparison is now [closed with results](0075-goal-only-wheel-road-geometry.md). The original design-only text below predates that work.

# Proposed wheel-local road geometry comparison

Design and constructed examples only, prepared after closing the eight-race
0074 repeatability check. No production code, validator or default changed;
no new free runtime qualification or model result is claimed. No paid window
or race admission is opened by this proposal.

Question: can current road orientation and edge clearances help Jev earn the
first required gate from the recovery start before a rescue, without supplied
action rules? 0074 produced zero such gate crossings across four recovery
races; the minimal arms did return to a forward preview before rescue.

Proposed treatment adds only `wheel_facts.road_frame`:
`road_minus_kart_heading_rad` copied from raw `track.heading_error`, plus left
and right edge clearances copied from the already supplied pedal road facts.
Units explain road-tangent-minus-kart-heading sign and negative edge clearance.
There are no recommendations, action rules, thresholds or predictions.

Both arms use minimal wheel facts with motion disabled. This isolates the
geometry bundle from the motion bundle, whose earlier apparent clockwise
advantage did not reproduce. Goal rules, full pedal question, physical menus,
native inverse, empty shared state, Python physics and all timings remain exact.

Proposed finite cohort: four recovery201 races at the existing stationary
−10 m/+124° start, ordered minimal/geometry/geometry/minimal. Two per arm;
no fresh track or pose introduced. Primary outcome is first gate before rescue;
secondary is a useful finish with zero rescues, plus clean finish, grass,
elapsed time, choices, token cost and natural latency exposure. All failures
remain; no retries, replacements, tuning or extra arms. A first forward preview
alone is not counted as successful recovery.

Before any future paid use: implement a separate goal-only opt-in flag with
strict finite/value validation and preserved defaults; reconstruct all 8,237
prior question sets and isolate the geometry addition on saved snapshots;
check all 15 native choices and prior stopped/passed-gate cases for both
profiles with mock responses; run and audit four exact-interface free controls
(one per entry) using the unchanged feasibility guide. Require zero rescues
in each free recovery control, grass reported. Reverify the complete engine
gate if only controller code changes; core/runtime changes require a fresh
complete gate. Freeze source/helper/route/evidence hashes before admission.

If subsequently executed, retain max 800 decisions/race, 3x reference deadline,
5 s timeout, one POST in flight, full reserves, root-observed exits and full
per-race audit. The existing $10/100,000-request/500-million-token caps and
1,000-request/5-million-token/15-minute floors remain; no charge or uncertainty
may be reset. Roughly $0.10 expected for four races, subject to hard caps.

[Constructed proposed questions](0075-wheel-road-geometry-proposed-prompts.json)
include stopped, moving and off-road observations from an actual minimal-facts
0074 run. They are reviewable hypothetical requests, not actual new replies.
