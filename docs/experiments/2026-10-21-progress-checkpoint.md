# Driving progress checkpoint

Written October 21, 2026 UTC (October 20 Pacific). This is a saved-data
engineering summary and repository handoff, not a new experiment. Cleanup,
tests and publication make no model calls. Individual frozen reports remain
the source for each study's design, results, failures and limitations.

## What works

The current opt-in 15 m question-local driver completed 14/14 useful Jev
attempts, 13/14 clean, including 12 consecutive fresh clean starts across
0053/0054/0068. OpenAI GPT-6 Luna Decisions completed both matched 0068 starts
cleanly using exactly the same game, prompt, driver and benchmark. A useful
finish takes at most twice its matched reference; a clean finish additionally
requires zero rescues and zero grass time.

| Model/provider, study 0068 | Standard99 | Clockwise100 | Clean | API latency p50/p95 |
| --- | --- | --- | --- | --- |
| Jev / TypeSafe | 79.32 s | 79.00 s | 2/2 | 226.5 / 303.1 ms |
| GPT-6 Luna Decisions / OpenAI | 79.35 s | 79.10 s | 2/2 | 268.8 / 349.5 ms |
| Clef / Cloudflare | DNF at 22.38 s | DNF at 16.62 s | 0/2 | 487.3 / 884.2 ms |

Jev's earlier 0052 candidate pair had one clean finish and one rescue-assisted
finish; the latter remains in the 14-attempt total. The eight-start 0053 cohort
was 8/8 clean in 78.23–80.67 s. Seeds vary only initial lateral offset ±0.35 m
and heading ±0.025 rad. These are one solo stadium and its mirror, not different
tracks, opponents or broad recovery cases. OpenAI's transfer pilot has only
two starts and does not establish comparative model rankings.

## What changed, and what evidence supports it

### Track and handling

The experimental setup uses a 24 m road, two 60 m straights joined by radius-30 m
semicircles, a 12 m/s speed cap, 0.12 rad maximum wheel and three-second rescue.
Original application defaults remain the winding course, 9 m road, 24 m/s and
0.32 rad wheel. Python physics still runs independently at 60 Hz.

Moderate steering is 0.06 rad; the nominal bicycle radius with a 1.8 m wheelbase
is 1.8/tan(0.06), approximately 30 m, matching stadium bends before grip and
response transients. The configuration makes the physical task forgiving.
In [0013](0013-stadium-width.md), widening 16→24 m reduced total rescues across
three matched starts from 14 to 3, but only one 24 m attempt was fully clean.
Track changes alone did not establish the later consistent performance.

### Explicit feedback policy and factual geometry

The successful prompt supplies a fixed steering policy over the bearing of a
centreline point 15 m ahead: hard right below -22°, right from -22° to below
-7°, straight from -7° through +7°, left above +7° through +22°, hard left above
+22°. Positive means left of the current kart nose. The host supplies the
geometric bearing computed from the same rounded x/y preview sent to the model:

```python
theta = round(math.degrees(math.atan2(y, x)), 4)
```

In [0032](0032-bearing-policy.md), adding that factual bearing improved complete
supplied-rule agreement 10/30→28/30 on the same static cases. Reducing facts
improved 25/30→30/30 in [0034](0034-policy-facts.md), but later broader tests
retained errors. These are within-study comparisons, not comparable accuracy
points on a shared benchmark or proof of an internal model mechanism.

The pedal rule accelerates normally; coasts/brakes when off-road or close to
an edge while moving outward; and prioritizes acceleration below 2 m/s. Fixed
examples distinguish inward from outward motion. In the 0068 successful
races, Jev accelerated on 600/602 calls and OpenAI on all 520: these results
mostly exercise steering at the speed cap, with little braking-strategy evidence.

### Facts inside each decision question

One POST contains both native questions: five wheel options and three pedal
options. Shared `state` is empty. Each question's structured `instructions`
contains its own rules and current factual group. The current implementation
in `src/mcpkart/question_context.py` builds it as follows:

```python
result[head] = {
    "type": "choice",
    "instructions": {
        "rules": DRIVING_TASK_PREFIX + definitions[head] + task,
        "current_facts": {head + "_facts": copy.deepcopy(facts[head + "_facts"])},
    },
    "criteria": {name: description + " " + clauses[name]
                 for name, description in physical.items()},
}
```

In [0050](0050-factual-relocation-replication.md), shared facts produced 71/78
complete correct policy pairs; full facts inside questions 77/78; component
facts inside questions 77/78. Both local variants had 78/78 wheel agreement.
Component facts were selected for smaller input, not an accuracy advantage.

One matched synthetic pose had bearing +0.9183°, requiring straight+coast:
shared facts returned hard_left+coast; both question-local variants returned
straight+coast. The corresponding saved response excerpts and source hashes
are in [current-driver-examples.json](current-driver-examples.json).

Splitting wheel/pedal alone had not solved driving in 0025. The later live
package comparison [0052](0052-native-compatibility-driving.md) reduced rescues
from 1→0 and 10→1 on its two matched starts. That is a complete-controller
comparison; it does not isolate a single clause's contribution. All these
prompt ablations used Jev. OpenAI was tested on the final package only.

## Actual prompt and response excerpts

The wheel prompt says:

> DRIVING POLICY. Choose the next native input by executing the supplied policy exactly.

Its moderate-left option says:

> Hold wheels LEFT at 3.44 degrees; a nominal bicycle turn radius of 30.0 metres before grip/response transients. FIXED POLICY ELIGIBILITY: choose this wheel exactly when +7 < theta <= +22 degrees.

A recorded Jev query contained this road row:

```json
{
  "preview_15m_bearing_deg": 13.1855,
  "preview_columns": ["ahead_m", "ego_x_m", "ego_y_m"],
  "preview": [[15.0, 15.315, 3.588]]
}
```

Jev returned in 202.754318 ms (response excerpt, probabilities/billing/ID omitted):

```json
{
  "model": "typesafe/jev-1.14-20261014",
  "answers": {
    "wheel": {"type": "choice", "choice": "left"},
    "pedal": {"type": "choice", "choice": "accelerate"}
  }
}
```

A separate OpenAI race query had bearing +16.8095° and returned the same native
pair in 242.592302 ms:

```json
{
  "model": "openai/gpt-6-luna-decisions-20261006",
  "answers": {
    "wheel": {"type": "choice", "choice": "left"},
    "pedal": {"type": "choice", "choice": "accelerate"}
  }
}
```

These are different trajectory states, not a matched-input model comparison.
The [portable excerpts](current-driver-examples.json) preserve both complete
questions, native choice excerpts and hashes of the ignored source records.
They are curated examples, not complete raw race evidence.

## Timing, validation and capability limits

The previous native input remains applied while the model is thinking. At
12 m/s, a 250 ms request spans 3 m of travel. Fast inference is part of the working
setup. [0055](0055-latency-governor-feasibility.md)'s free engineering-guide
simulation finished 6/6 clean at 250 ms + frame but 0/6 at sustained 500 ms + frame with
the unchanged policy. This is a physical feasibility result, not a model test
or causal diagnosis of a particular failed race.

The host projects geometry, sends rules/facts and applies the returned native
pair. It does not evaluate the current policy branch, choose a substitute or
filter controls in paid driving. Domain exits stop and count as quality
failures; all five wheel and three pedal choices remain available. All clean
finishes used zero rescues. Raw/native/factual/physics/clock/accounting replay
and independent Python physics make the measurements inspectable.

The demonstrated task is consistent execution of an engineered feedback
policy. Arbitrary-track planning, traffic, strategy and recovery remain open.
The 22 m steering-frame/focused-pedal alternative passed free/static screens in
0063/0065, but actual 500 ms Jev driving remains unrun after the 0066 cloud reboot;
0067's free controls do not establish model performance. Failed gates remain
failed and no experimental alternative is silently promoted.

## Clef, budget and handoff

The user set Clef aside. Its 0068 failures occurred at 20/120 gates. In the new
post-top-up [0069](0069-clef-topup-rerun.md) attempt, two valid replies took
646.8/842.4 ms and the third timed out at 5007.9 ms. The race stopped 6.55 s into
standard 99; clockwise 100 was never admitted. No cache fields were returned,
so account-balance/cache effects are unknown. Timing and saved-data integrity
passed; the strict zero-error/native gate failed.

Keep the timeout's full 75,366-token/$0.00393216 reservation; actual billing is
unknown. The latest versioned [snapshot](model-budget-snapshot.json) is 71,160
requests / 267,423,949 charged tokens / $8.563495772000609, pending empty and 70
uncertainties. Caps remain $10 / 75,000 requests / 500 million tokens. All paid windows
are closed; this checkpoint authorizes no new paid attempt. Preserve and
transfer the current ledger, including historical uncertainty, between hosts.

Cleanup validation: 474 tests passed, 3 optional Rust tests skipped; full Ruff and
an offline lockfile consistency check passed. No application source changed
during this cleanup. See the [driver guide](../question-context-driver.md),
[Cloud guide](../cloud-development.md), and [index](README.md) before continuing.
