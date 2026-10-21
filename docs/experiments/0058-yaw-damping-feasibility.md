# Free feasibility: damping the supplied bearing rule with current yaw

Prospective registration, October 20, 2026. The existing question-local guide
has strong ordinary-latency driving results, but 0055's perfect-guide free
simulations failed under sustained 500 ms+ decision delays. Forecast additions
have not passed their capability gates. Test a simpler engineering-policy
change without model spending: damp the bearing rule using actual current yaw.

Keep all physical settings and the pedal rule unchanged. Let theta be the same
four-decimal bearing from the current rounded 15 m target, and omega be
round(degrees(current raw kart.yaw_rate),4). Compare the unchanged guide with
three fixed guides using D=round(theta-k*omega,4), for k=0.25,0.50,0.75 seconds.
Apply the original ±7/±22 degree wheel bins to D, with exact ties choosing the
smaller absolute wheel. These are engineering rules, not claims of optimality.
Only current theta and omega would be eligible model facts in any later study;
D, eligible wheels and free host-selected answers may never enter paid facts.

This phase has no Jev calls. Run starts 51–56, alternating standard/clockwise,
with first-affected-step delays of 16,31,46 physics ticks (250,500,750 ms plus
one 60 Hz step), for all four guides: 72 fixed cells. Hold the old input during
latency; discard a reply if rescue intervened. End at finish, three times the
fresh reference, or the same declared prompt-domain boundary. Keep every cell,
including failures, with commands and full-physics reconstruction hashes.
Use Python, 24 m, 12 m/s physical maximum, 0.12 rad steering, three laps and
three-second rescue throughout. Preserve the real model ledger unchanged.

A coefficient is physically eligible only if all six ordinary 16-tick controls
are clean and useful, at least four of six 31-tick controls are clean (at least
two in each direction), and it gains at least four clean stress finishes net
with no net useful-finish loss. Rank eligible coefficients by clean 31-tick
finishes, then clean 46-tick finishes, then smaller coefficient. This chooses
an engineering hypothesis, not a model-qualified controller. Freeze the order,
source/plan hashes and exact criteria before simulating, then separately audit
all actions and physics. Any later static/native/timed/model comparison needs
a new prospective protocol and its existing budget/runtime gates. No paid
request, application default change or driver promotion is admitted here.

## Results

The free physical-selection gate passed. Every damped coefficient retained
6/6 clean ordinary controls and achieved 6/6 clean controls at 500 ms plus one
frame, versus 0/6 for the unchanged guide. All four guides had 0/6 useful or
clean finishes at 750 ms plus one frame; their domain exits remain retained.
The predeclared tie-break selected k=0.25 because the clean counts tied and
it was the smallest coefficient. This is not a claim that it was uniquely
best: k=0.50 was somewhat faster at 500 ms in these free simulations.

| Guide | Clean 250 ms | Clean 500 ms | Clean 750 ms |
|---|---:|---:|---:|
| Original bearing | 6/6 | 0/6 | 0/6 |
| k=0.25 s | 6/6 | 6/6 | 0/6 |
| k=0.50 s | 6/6 | 6/6 | 0/6 |
| k=0.75 s | 6/6 | 6/6 | 0/6 |

Selected k=0.25 finished the 500 ms cells in 83.48–87.08 seconds. It finished
ordinary cells in 79.57–80.15 seconds, a small pace cost relative to the
unchanged guide's 78.48–78.83 seconds. The separate free audit reconstructed
247,341 physics steps and 11,215 query actions across all 72 cells. No model
requests or real ledger changes occurred. Full results and source/plan hashes
are in `artifacts/jev-yaw-damping-v1` and [the summary](0058-yaw-damping-feasibility-summary.json).
The later native screen is separate; this result alone qualifies no Jev driver.
