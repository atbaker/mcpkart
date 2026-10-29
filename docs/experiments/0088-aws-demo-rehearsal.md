# 0088: live rehearsal with provider retirement

The registered rehearsal is complete and CLOSED. The separate stage entry has
not started and remains available for one manual launch after this root review.
No request retry, replacement race, fallback control, model change or tuning
occurred. All older paid windows remain closed.

The conventional Temporal worker, broker, real MCP server and independent 60 Hz
Python physics process ran on this demo's dedicated Amazon Linux ARM64 host.
Temporal Cloud namespace: mcpkart-dev.iuiaz. AgentCore Runtime version 6 preserved
the native OpenRouter request and response bytes. Local Activities coordinated
three independent child workflows with durable dispatch receipts.

| Driver | Outcome | Finish | Rescues | Native requests |
| --- | --- | ---: | ---: | ---: |
| Jev | Finished first | 99.03 s | 2 | 257 |
| OpenAI Decisions | Finished | 151.52 s | 12 | 285 |
| Clef | Provider/transport DNF | — | 11 | 109 |

Clef retired at approximately 118.14 seconds after its 109th request produced
an AgentCore RuntimeClientError without a native reply, after 5.10 seconds.
No native HTTP status or usage report exists for that request. The saved
exception type does not establish the underlying provider failure mechanism;
it must not be relabeled as a confirmed HTTP 429 or model refusal. The kart
held its last model-selected input under unchanged physics and rescue rules.
The other drivers continued. Clef had reached 80/120 gates at the endpoint.

This run demonstrates the approved retirement behavior. It is one comparison
with unequal observed latency and rescues, not a general model ranking.
Jev median/p95 round-trip latency was 239/291 ms, OpenAI 364/584 ms, and Clef
629/3,101 ms. These include the AgentCore bridge. The models chose every applied
wheel/pedal action; no supplied driving policy or host replacement controls
entered the paid path.

## Qualification and root review

A fresh complete EC2 clock gate passed four full controls with twelve clean
kart finishes, 21 physics frames during an HTTP-parent pause and 170.1 seconds
of neutral physics. All control maximum reported lateness values were below
4 ms. The server and source/boot bindings were independently revalidated.

A complete free Temporal retirement control injected a 429 on Clef's second
mock request. It made exactly two green requests, retired that driver and let
the other two finish. Root audit: 5,325 frames / 519 exact queries / 1,038 budget
transitions; maximum derived lateness 2.690 ms. No real model calls.

The exact free Cloud interface passed all three mock finishes, 6,388 physics
frames / 743 native queries / 1,486 budget transitions. All 746 AgentCore
envelopes matched the saved native bytes, with zero SDK retries. Maximum derived
lateness: 9.708 ms. All 2,247 interface payload hashes and all twelve clock
manifest payload hashes were verified after archive retrieval.

Root observed the paid SSM/process exit 0, then independently reconstructed all
9,112 frames, 651 exact native requests and 1,302 shared budget transitions on
the qualified Linux host. Maximum derived lateness was 6.413 ms. The outer
audit covered 654 invocation attempts: 653 returned envelopes, including the
three free warmups, and one preserved missing response. Every available native
byte matched, response IDs and operation IDs were unique, and observed SDK
retry counts were zero. Source and current server bindings remained exact.

All four exported Temporal histories ended COMPLETED, with zero failed or
timed-out events. Slow workflow-task warnings are retained in the log; no
duplicate model dispatch was found. The full review is saved in
[the root audit](0088-root-audit.json). Selected
[actual native responses](0088-native-responses.json) are separate from prepared
examples.

## Accounting and operator state

The rehearsal added 651 requests / 1,690,574 charged tokens / $0.155255912.
Reported usage accounts for $0.151323752; the missing Clef reply retains its
entire $0.00393216 / 75,366-token reservation and adds one uncertainty.

The cumulative ledger is 100,061 requests / $11.680947340002783 /
335,629,288 charged tokens / 73 uncertainties, with no pending reservation.
Caps remain $20 / 110,000 requests / 500 million tokens. No historical charge,
failure or uncertainty was removed. Infrastructure costs are separate.

The local operator held its paid-writer lock throughout the EC2 run, checked
matching initial ledgers, observed the remote exit, fetched the complete archive
and atomically restored the full remote cumulative ledger locally. Root's exact
reviewed ledger enables only the remaining registered stage entry. Unknown SSM
submissions cannot be resubmitted.

Keep the dedicated host/server running for tonight. The spectator is available
through the local SSM tunnel at http://127.0.0.1:17773/. See
[the operator guide](../aws-demo.md). Original recordings, raw calls, histories,
budget transitions, earlier failures and archive hashes remain under ignored
artifacts. The stage entry expires at midnight Pacific; its admission requires
fifteen minutes remaining.

The 20-fps presentation export retains all 3,038 selected visual frames and
every rendered field byte-for-value, omitting only unused per-kart telemetry
facts. Its JSON is 5,831,664 bytes; the 60-Hz master is unchanged. Standalone
playback, start/end seeking, winner, pre-retirement state and final provider DNF
were checked in the browser, with no console errors. The original larger export
and the first failed catalog-size check remain preserved. No runtime/UI/model
source changed during packaging.
