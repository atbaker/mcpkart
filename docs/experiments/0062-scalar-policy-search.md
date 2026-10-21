# Free scalar-bearing policy search with separate physical holdouts

Prospective registration, October 20, 2026. The original scalar bearing prompt
has strong actual driving/rule agreement. Yaw-damped engineering guides were
physically promising, but both native arithmetic screens failed. Test whether
physical delay robustness can improve while keeping the model's task to one
supplied bearing and fixed comparisons. No failed native version is promoted.

Cross two factual reference frames (kart nose; kart-centred axes aligned with
the CURRENT ACTUAL steering direction) with straight deadbands 3,5,7,9 degrees
and full-wheel thresholds 22,30 degrees: sixteen fixed guides. In the steering
frame, rotate the same current rounded 15 m body-frame coordinates by minus
the current raw actual steering angle, round new coordinates to three decimals
and compute atan2 bearing to four decimals. This is another current measured
coordinate frame, not a future prediction, evaluated condition or recommended
wheel. Retain the original body-forward/required-gate operating domain.

For each supplied bearing, use the original five-wheel bin structure with
inward threshold ties and the chosen fixed bounds. Keep the pedal rule and all
physical settings unchanged: Python, 24 m, 12 m/s, 0.12 rad, three laps and
three-second rescue. All policy choices here are free engineering-guide
calculations, never Jev results or paid facts.

Search starts 63–68, alternating directions, under first-affected-step delays
16 and31 physics ticks (250/500 ms plus a frame):192 fixed cells. Preserve old
input during delay, discard if rescued, and stop at finish, three times the
fresh reference or the existing domain exit. Keep every failure. An eligible
guide must have six clean/useful ordinary controls, at least four clean500ms
controls including at least two per direction, and at least four clean stress
gains net over the original nose/7/22 guide, without net useful-finish loss.

Rank eligible guides by clean500ms count descending, then prefer nose frame,
then median clean500ms finish time ascending, then total threshold deviation from7/22
ascending, then guide ID. Freeze this before seeing outcomes. Choose once;
do not substitute a runner-up after holdout failure.

For the selected guide only, run separate starts69–74, alternating directions,
at both delays:12 holdout cells. The overall physical-selection gate requires
all twelve holdouts clean and useful, plus a separate exact command/physics
audit. If no guide is eligible, preserve the unrun holdout suffix. All source,
plan, selection and outcome hashes stay recorded, with zero model calls and
an unchanged real ledger. Any later native/driving work needs a new protocol.
The current application/driver and all global caps stay unchanged; deadline
11:38:01 UTC. Root alone reviews and collects.

Results: selected `steer_d9_f30`. Separate holdouts were 10/12 clean; physical gate failed. Exact audit passed 204 cells, 827,407 physics steps and 41,482 query actions. No model calls; engineering feasibility only. The failed holdout remains failed; no runner-up substitution or native admission.
