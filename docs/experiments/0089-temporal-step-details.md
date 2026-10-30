# 0089 metadata amendment: descriptive kart steps

The user requested more descriptive kart_step Activities and results that show
the model's experience. This changes only presentation metadata and the durable
result of the same unconsumed manual regular-Activity run. No paid setup race
or additional paid entry is introduced. The earlier 0087/0088 entries remain
closed. All budgets, failures and uncertainties are preserved.

## What the audience can see

Each Activity has a summary such as “Jev: choose steering and pedals - decision
321” and a stable Activity ID. Each child Workflow identifies its model and
kart, and its Current Details shows either the pending decision or the latest
factual step summary. The kart_step Activity Type remains unchanged.

The completed Activity result retains applied/done/seq/step_ms and adds:

- driver, kart, model and a one-based decision number;
- model_saw: the actual facts sent to the model, including lap/gates, speed,
  on-road status, offset, edge clearances, preview-point bearing, signed
  next-gate plane position, observation time and rescue count;
- model_chose: the native steering and pedal choices and their combined held
  input, without a host-selected replacement;
- model_response: valid-decision flag, native HTTP status when available and
  measured reply latency;
- game_acknowledgement: whether the input was applied, its reason/tick, state
  when acknowledged, gate progress since the observation and whether rescue
  happened while waiting;
- summary: a short readable description of those recorded facts.

The acknowledgement state describes when the command was acknowledged. It does
not claim that the newly selected input caused all changes while the model was
waiting. The road-preview bearing is a bearing to the supplied preview point,
not a road-curvature measurement. Positive offset/bearing means left. No
rationale or chain of thought is invented.

A provider DNF has model_chose=null, invalid-decision status and an explicit
“no replacement control” summary. The original full uncertain reservation and
native error evidence remain intact.

The enriched result is saved inside the existing durable SQLite receipt before
returning to Temporal. Re-executing a completed step returns the exact same
description without observing a later game state or dispatching another
request. No full prompts, API keys, owner tokens or driver capabilities enter
the receipt.

## Verification and deployment

Only demo_broker.py and demo_workflows.py runtime files changed. Physics,
handling, model questions, routes, native controls, limits, no-retry behavior
and provider retirement are unchanged. Targeted Linux receipt tests and four
real Temporal integration tests passed, including metadata in actual Activity
history, result provenance, duplicate receipt stability and privacy.

The fresh clock and exact Cloud mock qualification bind the new source to the
same dedicated server. The former read-error attempt and its accepted orphan
start are preserved; the command was never resent. No OOM/server exit was
observed. The subsequent complete free gate is saved separately.

The metadata release uses artifacts/aws-demo-ui-release-v1 and Runtime8, with
the same adapter code/role/network/secret and only its authorization hash
changed. The manual entry is still mcpkart-aws-regular-stage-20261029.
Ledger remains 100,603 requests / $11.786845266002775 / 337,074,715 charged tokens /
74 uncertainties, no pending; all caps/floors/expiry unchanged.

The separate spectator UI work uses local read-only viewer17774. Its dirty
HTML, preview script and guide edits are preserved, while the remote qualified
UI remains frozen. This release includes only the two Temporal metadata files.

Temporal documents the
[Activity summaries and their display in the UI](https://docs.temporal.io/develop/python/platform/enriching-ui).
Labels are fixed when scheduling; the factual result and Current Details supply
the completed model-choice context.

## Completed qualification

The full fresh gate passed four complete controls with twelve clean finishes,
21 physics frames during the HTTP-parent pause and 170.1 seconds of neutral
physics. All source/boot/server bindings and evidence hashes revalidated.

The exact regular-Activity Cloud mock completed all three karts by 124.77 s.
Root independently reconstructed 7,487 physics frames, 800 native requests and
1,600 budget transitions. Maximum derived lateness was 4.180 ms. All 803
AgentCore exchanges, including three free warmups, matched native bytes with
no observed SDK retry or missing response.

Every one of the 800 completed descriptive results matched its native input
facts, returned steering/pedal choices and saved SQLite receipt. Where a next
observation existed, it also matched the acknowledgement-state fields. Every
Activity summary and stable ID matched the driver and decision number.
Maximum serialized result size was 1,158 bytes. No model calls or charges were
added, and the same single manual entry remains unstarted.

See [an actual scripted Cloud result](0089-step-result-example.json) and
[the complete root audit](0089-step-details-root-audit.json). Existing recorded
histories keep their old result shape; these changes apply to fresh executions.
The next manual run still uses the same operator command.
