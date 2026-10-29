# 0089: one manually invoked regular-Activity demo race

The user requested switching off Local Activities and measuring performance.
Both registered 0088 Local Activity entries had already completed; they remain
closed and cannot be reused. Their original results and all charges/uncertainty
are preserved. The current change makes the next demo use regular Activities.

This prospective release permits ONE manually invoked regular-Activity race,
mcpkart-aws-regular-stage-20261029. It starts only when the operator command is
explicitly run; setup performs no paid rehearsal. No request retry, replacement
race, alternative model/provider, prompt tuning or fallback control is allowed.

Models, pinned providers, goal-only facts, seed zero, ghost grid -4/0/4, oval,
three laps, 180-second deadline, 1,100 requests per racer and the provider-DNF
policy are unchanged. Conventional workers and three child workflows remain.
Every kart_step uses the existing regular workflow.execute_activity path.
SDK eager dispatch retains its existing default. Real MCP controls and native
OpenRouter payload/response bytes through AgentCore are unchanged.

The existing complete EC2 clock must revalidate against the same source, boot
and server. The full regular-Activity Cloud mock interface must pass with this
release digest, export regular Activity events instead of Local Activity
markers, and verify every native byte, physics frame and budget transition.
No runtime/physics/prompt/UI source change is required. Reuse the same qualified
server rather than restarting it. All prior failed evidence remains retained.

The cumulative initial boundary is 100,603 requests / $11.786845266002775 /
337,074,715 charged tokens / 74 uncertainties, no pending. This includes the
already-completed 0088 stage run; nothing was refunded or removed. Caps remain
$20 / 110,000 requests / 500 million tokens. The same admission floors and
midnight Pacific expiry apply, with fifteen minutes required before starting.

Root must observe and audit any actual exit, including provider errors and
full uncertain reservations. This release provides no subsequent entry. A
provider error retires that kart while the other drivers continue; invalid
native answers and application errors still stop the race. A provider DNF is
an infrastructure outcome, not a model ranking.
