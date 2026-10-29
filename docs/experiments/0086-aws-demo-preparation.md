# Three kart AWS demo free preparation

29 October 2026. Branch `codex/aws-temporal-demo`. The user approved OpenRouter,
MCP, conventional Temporal workers, and ghost karts. This is free infrastructure
preparation. **No paid collection has been admitted or performed.** Studies
through 0085 remain closed.

## Implemented and exercised

The explicit trio configuration uses red, blue and green, a shared 60 Hz Python
process, the existing handling/gates/rescue rule, and ghost contact. Default
two-kart configuration and solid contact remain supported. Trio observations
contain both opponents; all drivers receive the same goal-only construction.

A conventional Temporal worker runs one race workflow and three concurrent driver
workflows. Regular and Local Activities both call the single-writer race broker.
SQLite receipts bind a logical race, racer and decision sequence. Replaying a
completed step returns its saved receipt. A started-but-unresolved operation
cannot dispatch again automatically. Native controls are submitted through the
existing MCP interface; the model does not discover or generate MCP calls.

The isolated AgentCore Runtime is deployed in us-west-2 under
`mcpkart_aws_demo_20261029`. Only its dedicated code bucket and execution role
were created; the exact resource receipt is ignored under
`artifacts/aws-demo-package-v3/aws-resources.json`. The handler supports scripted
mocks only and has no provider dispatch implementation or API key. Invocation
retries are disabled. Completed rehearsal sessions were confirmed already ended
by the time cleanup ran. The Runtime definition remains for subsequent work.

## Complete mock rehearsals

Root observed both collector processes exit 0, then reviewed their complete
audits and preserved matching source snapshots. These outcomes are scripted
infrastructure controls, not Jev/OpenAI/Clef results.

| Field | Local Temporal and MCP | Local Temporal, AgentCore and MCP |
| --- | ---: | ---: |
| Red finish | 78.95 s | 92.30 s |
| Blue finish | 78.7167 s | 99.9667 s |
| Green finish | 79.40 s | 89.2167 s |
| Rescues, red / blue / green | 0 / 0 / 0 | 1 / 2 / 0 |
| Saved physics frames | 4,765 | 5,999 |
| Exact native mock queries | 912 | 712 |
| Budget transitions | 1,824 | 1,424 |
| Peak concurrent reservations | 3 | 3 |
| Maximum derived frame lateness | 5.425 ms | 6.901 ms |
| Actual provider/model calls | 0 | 0 |

The AgentCore run also made three mock prewarm invocations before the physics
epoch. All 715 outer AWS requests have unique saved request IDs and matching
request/response hashes. Separate initial contract probes added three other
mock AWS invocations. The 712 driving round trips included a fixed 200 ms scripted
delay: median 331.77 ms, p95 384.85 ms, maximum 575.53 ms. This is an observed
infrastructure comparison, not an isolated causal estimate or model latency.

The auditor reconstructs every saved physics frame, observation, question set,
native choice, applied command and shared budget transition. Root additionally
checked every outer AWS envelope against the exact inner request bytes and its
zero-cost mock reply. Parent and child Temporal histories, full recordings,
standalone HTML replays, and frozen source are saved with the attempts:

- `artifacts/aws-demo-free-v1/trial/`
- `artifacts/aws-demo-agentcore-free-v1/trial/`
- `artifacts/aws-demo-agentcore-probe-v1/`

The spectator was inspected in the in-app browser during both live collection
and playback. An output/replay-root mismatch initially hid the second run's
model labels; the live-status path is now configurable and the saved mock labels
were verified. Browser error logs were empty during the inspected live run.

## Software and failure evidence

The full free suite passed 809 tests with 15 skips on this Mac. Nine skips are
Linux `/proc` qualification fixtures, three are optional Rust, and three are
the separately invoked Temporal integration tests. The three opt-in integration
tests passed against a real local Temporal service, including deliberate failure
after a Local Activity returned but before its workflow marker was persisted:
the wrapper executed again while the broker's mock request and MCP command
occurred once. Ruff and diff checks passed at the checkpoint.

Development uses the available Python 3.14.3, not the historical 3.14.8. The
initial unrestricted suite failures were Linux-only fixtures and loopback socket
restrictions; socket tests passed with loopback access. Linux qualification
fixtures now skip explicitly on macOS; the production qualification gate still
requires Linux and has not been bypassed.

Packaging attempts v1 and v2 failed before any AWS resource mutation: v1 could
not resolve the historical interpreter; v2 unnecessarily included a Pillow wheel
unavailable for the selected ARM64 target. v3 contains only the mock adapter and
its locked SDK dependencies, passed ZIP CRC validation, and executed successfully
on AgentCore. Initial deployment stopped before mutation because AWS login
credentials required `botocore[crt]`; that dependency is now locked. The first
broker unit audit exposed a derived-budget-summary mismatch, fixed before either
complete rehearsal. All rehearsal rescues and preparation failures are retained.

## Paid boundary and remaining gates

The missing ledger was seeded byte-for-byte from the versioned migration snapshot:
99,403 requests, $11.520516764002778, 333,848,829 charged tokens,
71 uncertainties, no pending. Caps remain $20 / 110,000 / 500 million.
Both rehearsal budgets are separate mock files; no actual ledger charge occurred.
A newer authoritative ledger, if one exists, takes precedence.

The executable demo CLI is free-only. Before live models, configure the Temporal
Cloud connection and OpenRouter secret, qualify the final source/server on Linux
with four complete trio controls, parent-pause evidence and the neutral run, then
validate the exact Temporal/AgentCore native interface and freeze a finite paid
registration. The existing qualifier now has an explicit `--trio` mode; it has
not been run as a complete Linux gate on this Mac. No paid adapter or secret
access has been deployed. Neither the remaining budget nor these mocks authorize
reuse of a closed study.
