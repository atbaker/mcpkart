# Native validation of the yaw-damped bearing rule

Prospective registration, October 20, 2026. The separate 0058 free engineering
screen passed and selected k=0.25 by its frozen tie-break. This study asks
whether Jev can execute that supplied wheel rule, retaining the same pedal
rule and complete original native menus. It does not turn free controller
outcomes into model results or change the working opt-in driver.

Use exactly D=round(theta-0.25*omega,4), with theta from the existing current
15 m bearing and omega=round(degrees(raw current kart.yaw_rate),4). Keep
original ±7/±22 wheel bins, inward ties and the existing pedal definitions and
examples. Supply only the current bearing/coordinates, original units/gate
facts, current actual yaw in degrees/second, and the unchanged pedal facts.
Never supply D, an evaluated policy condition, risk label or eligible wheel in
paid facts. Both native heads stay in one original Decisions API POST, with
current component facts inside their questions and state={}.

Compare `plain` with `worked`, which adds seven fixed arithmetic examples:
(30,0)->30 hard_left; (20,20)->15 left; (10,40)->0 straight;
(-20,-20)->-15 right; (-30,0)->-30 hard_right;
(0,40)->-10 right; (0,-40)->10 left. Each pair is (theta,omega), followed by D.
They are fixed examples, never the current query's evaluated answer.

Build 84 fresh native cases: 24 natural current states (four per each of the
six completed selected-guide 500 ms free rollouts in 0058), plus 60 bounded
synthetic current poses in 30 reflected pairs. Reconstruct the natural prefixes
and all current facts exactly; these are free guide trajectories, not Jev
trajectories. Exclude prior fixture 15 m coordinate pairs and duplicate current
coordinates. Synthetic cases cross all five prescribed wheel classes and all
three pedal classes twice before reflection, with bounded current yaw and
pose variation. Exact current rendered values determine private policy labels;
the wheel arithmetic is checked separately. Exclude synthetic cases within
0.25 degrees of a D threshold. Record all selection/source/projection evidence.
No future trajectory, optimal-action label or host steering enters requests.

Each case receives both arms, for 168 fixed calls. Balance first arm and
criterion/menu reversal within each source stratum as closely as its size
allows, shuffle with seed 2026102059, and hold physical menu order identical
within a pair. Freeze cases, exact questions/order, route, all source/helper
hashes, ledger, private label checks and MockTransport evidence before paid
collection. One root-launched bounded static batch, one POST in flight, no
retries/fallbacks/replacements; stop at the first technical failure and retain
all attempted and unrun entries. No controls are applied in this study.

An arm qualifies for a separately registered driving pilot only with at least
80/84 native pairs, 81/84 wheels, 83/84 pedals, 23/24 natural pairs and 57/60
synthetic pairs, all ordinary native/identity/accounting checks valid. Rank
qualifying arms by pair accuracy, then wheel accuracy, then smaller payload
(the plain arm wins an otherwise exact tie). This is supplied-rule execution,
not an optimality claim or driving qualification. Any later actual driving
needs a new protocol, exact timed controls and per-race root admission.

Retain Python, 24 m, 12 m/s, 0.12 rad, three laps and three-second rescue.
Shared caps remain $10 / 75,000 requests / 500 million cumulative tokens,
full per-POST reservation and deadline 11:38:01 UTC. Root alone reviews and
collects. Application defaults, joint damped baseline and prior failures remain.

Precollection setup note, 10:14 UTC: root accidentally reissued the already
successful public-input and free-preflight commands. Exclusive-create refused
to overwrite the original order and mock call 00000. The original successful
receipt, all helper hashes and all 168 saved mock calls remain intact; its
first process exit was observed as zero. The duplicate free attempt made one
extra MockTransport POST before the protected evidence write failed, so its
isolated mock ledger now has 169 requests. No real model POST or real ledger
change occurred. The duplicate failure logs and an explicit provenance note
are retained; the original 0→168 saved mock budget prefix was checked again.
This is a local duplicate execution, not a new model trial or a replacement.

## Results

The native execution gate failed for both arms. All 168 model requests were
ordinary valid native responses and passed full technical, identity, budget
and provenance audit. All 84 current snapshots and 30,633 natural-prefix
physics steps reconstructed exactly; separate decimal arithmetic agreed on
all native labels. No controls were applied.

| Arm | Native pairs | Wheel | Pedal | Natural pairs | Synthetic pairs |
|---|---:|---:|---:|---:|---:|
| Plain | 69/84 | 72/84 | 81/84 | 13/24 | 56/60 |
| Fixed examples | 70/84 | 73/84 | 79/84 | 14/24 | 56/60 |

The examples produced five paired gains and four losses, net one. Neither arm
qualified, and no actual-driving study was admitted for this version. The
successful free physical rule is not a successful model controller. Current
state selection, near-boundary arithmetic and representation remain possible
contributors; these results do not isolate one cause of the natural-state
errors. Retain all failures and the original working driver.

Delta: 168 requests / 387,153 tokens / $0.015583764, no new uncertainty.
Evidence and the explicit duplicate-free-execution note remain under
`artifacts/jev-yaw-native-v1`. See [the summary](0059-yaw-native-rule-summary.json).
Protocol SHA256:
`e6ca68a485ceede2cbec838d93bab7af00bf13d2645478b0bc904a9e8f30fa19`.
