# Prompt experiments on the approved 24 m stadium

Keep **24 m width and the existing `damped` baseline**. Neither added paragraph
improved this two-start comparison. The alignment rule needed **7 and 6 rescues**
versus **4 and 0** for `damped`. The early-braking reminder slowed one finish
beyond twice reference and left the other kart stationary until its deadline.
The fresh baseline included one complete race with no rescues or grass time;
reliable clean driving remains unproven. No new production preset is promoted.

Status: complete, October 19, 2026. The user selected 24 m full road width
for the next prompt experiments after the [width comparison](0013-stadium-width.md).
Keep this course fixed while comparing instructions. The previous 24 m starts
needed 2, 1 and 0 rescues; those development results are historical context,
not new paired controls or qualification evidence.

## Results

All six attempts passed timing and independent exact replay, with no endpoint
errors or changed model/provider identities. These are two paired initial poses
per wording, with unseeded model responses and no claim of statistical
qualification. The failed race is retained.

| Instructions | Start | Gates | Time / deadline | Rescues | Grass time | Within twice reference |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `damped` | 3 | 120 | 96.40 s | 4 | 12 s | Yes |
| `damped` | 4 | 120 | 101.82 s | 0 | 0 s | Yes |
| `corridor_veto` | 3 | 120 | 112.77 s | 7 | 21 s | Yes |
| `corridor_veto` | 4 | 120 | 118.80 s | 6 | 18 s | Yes |
| `early_margin` | 3 | 120 | 166.50 s | 1 | 3 s | No: 2.15× |
| `early_margin` | 4 | 20 | 231.55 s deadline | 0 | 0 s | Unfinished |

The fresh baseline finished 2/2, including 1/2 without grass or rescues, with
median time 99.11 s (1.28× reference) and four total rescues. The alignment
candidate finished 2/2 but needed thirteen total rescues and median 115.78 s
(1.50× reference). Its thirteen departures were all rightward, versus two left
and two right for the baseline. These direction counts describe the outcomes;
they do not prove which phrase caused a directional error.

The braking candidate's single finish had median on-road speed 5.76 m/s. On its
other start, checkpoint progress stopped at 20/120 after 21.22 seconds. It stayed
at exactly the same saved position and heading, speed zero, from 22.37 s until
the 231.55 s deadline. Its following 750 decisions were 668 `right_brake` and 82
`left_brake`. The kart remained on-road, with 0.362 m of left clearance and the
road facing 22.80 degrees right of the nose. Rescue could not help because it
only triggers off-road. Zero rescues here describe a stalled failure.

This suggests a useful future diagnostic: safe braking must preserve a way to
resume motion, and steering cannot rotate a stationary kart. The candidate's
explicit stopped-recovery paragraph covered off-road states, whereas this stall
was on-road. A revised instruction needs new testing; these results do not
establish a repair. Keep the full race and its 210.33 s checkpoint stall in the
data rather than treating low rescue counts as a driving improvement.

The source, setup, observations and all native control criteria remained fixed.
All 3,011 real replies returned `typesafe/jev-1.14-20261014` / `TypeSafe`; all
2,989 accepted commands were attributed to their native replies. Worst clock
lateness was 42.319436 ms, within the unchanged limits. The additional free live
control finished in 77.2833 s with no grass or rescues and 18.849379 ms maximum
lateness. All five offline references finished without grass or rescues.

New charges were **$0.374642352**, 9,418,512 charged tokens and zero new uncertain
requests. Final shared ledger: **49,762/50,000 requests**, **$6.221778952/$10**,
210,940,833/250,000,000 charged tokens, 69 historical uncertain requests and no
pending reservations. There are **238 request slots** remaining. No limit was
raised and no prior charge was reset. The latest versioned snapshot matches
the live ledger. The owned server and all model processes are stopped.

## Budget-admission deviation

The original batch runner paused after five cases because the last baseline
had fewer than its conservative 1,000-slot admission buffer remaining. It had
**618 already-authorized slots** available. Before that unrun case, an explicit
administrative amendment admitted only the planned final baseline under the
unchanged per-request 50,000/$10/250-million-token hard caps. Its minimum headroom
was 535 slots: the maximum previous 24 m baseline count, 435, plus 100. The
baseline used 380 calls and finished with 238 slots still available.

This is a documented deviation from the original financial admission buffer;
the original protocol was not fully followed in that respect. The course,
handling, prompt texts, case order, race deadline and timing limits stayed fixed.
No failed attempt was retried or replaced. `admission-amendment.json` records
the decision and full pre-case ledger before the case's protocol was saved.
The audit reports this deviation explicitly while separately verifying data,
frozen inputs, commands and complete ledger accounting.

Evidence: `artifacts/jev-prompts-v3/` contains frozen helpers and hashes, local
mock proof, every trial, exact replay analyses, the admission amendment,
`report/driving-results.csv` / `.json`, per-variant summary and final audit.
There are no new runtime source changes; the existing complete timing gate and
349-test source validation remain applicable. No Rust was used.

## Hypotheses

Each candidate prepends one fixed paragraph to the exact production `damped`
instructions. The full observation, all 15 geometry-menu choices, kart, speed,
steering, track, checkpoint and rescue rules remain identical. No observations
gain a selected input, controller recommendation or computed racing line.
The [exact instruction texts](0014-stadium-prompt-texts.json) are versioned.

- `corridor_veto`: explicitly resolve a conflict between the nearby road and a
  future bend in favour of current alignment. In the earlier 24 m seed-zero
  recording, Jev repeatedly accelerated left while the road tangent and nearby
  centreline lay right of its nose, until left clearance was nearly exhausted.
- `early_margin`: choose pedals according to recovery risk before crossing an
  edge, and resume motion rather than staying on the brake when stopped on
  grass. Earlier seed one began steering right but kept accelerating as left
  clearance fell from 3.67 m to almost zero; all three recorded departures ended
  in rescue. These are hypotheses about complete added paragraphs, not proven
  optimal actions or isolated sentence effects.

## Frozen comparison

Use the Python process runtime with asyncio pacing and continuous 60 Hz physics.
The stadium has two 60 m straights joined by radius-30 m semicircles, a 24 m road,
12 m/s speed ceiling and 0.12 rad maximum wheel angle. Keep `road_navigation`
observations, geometry choice descriptions, three laps, 40 ordered finite gates
per lap, the three-second rescue rule and stale reply rejection. The deadline
is three times each exact seed-matched scripted reference.

Use fresh initial poses 3 and 4, in this order:

1. Start 3: `damped`, `corridor_veto`, `early_margin`.
2. Start 4: `early_margin`, `corridor_veto`, `damped`.

There is one request in flight, no hidden retry or provider fallback, and no
retuning between attempts. Keep every attempted case. Stop the batch on endpoint
or timing errors and investigate before any continuation. Jev responses are
not seeded; these are paired initial poses, not deterministic responses.

Rank candidates descriptively by completing both races within twice reference,
then rescue-free completions, total rescues and pace. Two starts alone do not
justify promoting a production preset; a promising candidate needs held-out
qualification. Do not combine historical and fresh baseline results into an
apparently larger paired comparison.

The shared ledger starts at 46,751/50,000 requests, $5.847136600/$10 and
201,522,321/250,000,000 charged tokens, with 69 historical uncertain requests and
no pending reservations. The phase has 3,249 request slots available and raises
no limits. Stop admitting another race with fewer than 1,000 request slots or
18 million charged-token slots remaining; preserve any unrun cases explicitly.

The frozen runtime fingerprint is
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
Its complete free timing gate and 349-test validation still apply on the same
machine boot and unchanged runtime source. New offline references cover starts
0–4; a free live 24 m control checks start 3. A local HTTP mock captured twelve
payloads across three recorded states, confirming the research baseline matches
production and the candidates change only instruction text, with all 15 native
criteria and state unchanged. This makes zero real model calls and leaves the
shared ledger unchanged.

The refreshed route retains requested alias `typesafe/jev-1.14`, resolved model
`typesafe/jev-1.14-20261014`, provider `TypeSafe`, and previous prices. Verify
every actual successful reply against this identity. Frozen helpers, hashes,
protocol, raw trials and audits live under `artifacts/jev-prompts-v3/`.
