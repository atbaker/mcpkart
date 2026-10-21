# Free feasibility of rounded current angles for yaw damping

Prospective registration, October 20, 2026. 0058's k=0.25 engineering guide
was physically feasible at 500 ms, but both decimal-arithmetic prompts in 0059
failed native execution. This new free screen checks whether whole-degree
current measurements preserve the physical benefit before another model test.
It does not resume or qualify the failed 0059 prompts.

Compare `float025`, the exact selected 0058 rule, with `quantized`: round the
same current four-decimal bearing to the nearest whole degree and the same
current four-decimal actual yaw to the nearest whole degree/second (Python
round-to-even ties), then compute private H=4*theta_integer-omega_integer.
Use native wheel bins at ±28/±88, with ties choosing the smaller wheel. This
is exactly equivalent to theta_integer-0.25*omega_integer with bins ±7/±22.
The pedal rule and physics remain unchanged. H and eligible actions are only
free host-guide calculations; any later model receives current measurements,
not H, D or a recommended control.

Run six new starts 57–62, alternating standard and clockwise, at first-affected
step delays 16 and 31 ticks: 24 fixed cells. Preserve the prior input during
latency and discard if rescue intervenes. End at finish, three times reference
or the same unsupported-preview/required-gate domain boundary. Retain all
failures and exact commands/physics digests. Python, 24 m, 12 m/s, 0.12 rad,
three laps and three-second rescue remain fixed.

The quantized representation passes only if all six ordinary controls and
all six 500 ms controls are clean and useful, with a separate full-physics
and command audit and an unchanged real ledger. This is an engineering
feasibility screen, not a model result or promotion. A passing result can
motivate a new fixed native comparison of equivalent arithmetic formulations;
no paid request is admitted here. Deadline remains 11:38:01 UTC, shared caps
unchanged, application default and existing experimental driver unchanged.

## Results

The free physical gate passed: both float and quantized guides finished all
six ordinary and all six 500 ms cells cleanly and usefully, with no rescues,
grass time or domain stop. The separate audit reconstructed all 118,776
physics steps and 5,582 query actions across 24 cells. No model call or real
ledger change occurred. The later native test remains separate.

Evidence is under `artifacts/jev-quantized-yaw-v1`; the
[versioned summary](0060-quantized-yaw-feasibility-summary.json) preserves all
outcomes, source/plan hashes and the separate audit. This establishes free
engineering feasibility at these starts, not model arithmetic or racing ability.
