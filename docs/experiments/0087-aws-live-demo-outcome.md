# 0087 closed: live AgentCore rehearsal stopped on Clef provider concurrency limit

The single live rehearsal is **closed**. It ran through conventional Temporal
Cloud workers, Local Activities, AgentCore, OpenRouter and real MCP controls,
then stopped after 1.8833 seconds on an upstream provider error. It did not
complete a race or establish a model ranking. No retry or replacement occurred.
The planned stage admission is blocked by the new billing uncertainty.

## Actual outcome

There were seven native Decisions requests: three Jev, two OpenAI Decisions and
two Clef. The first six returned HTTP 200 with exact pinned model/provider
identities and valid native wheel/pedal choices. Clef's second request returned
HTTP 429, carrying an upstream error: “Too many concurrent hosted model
requests. Try again shortly.” The native error contains no usage/billing report.

AWS invocation itself succeeded; the HTTP 429 was inside the original provider
response returned by the adapter. This distinguishes the observed provider
rejection from an AgentCore service quota error. One request per racer was in
flight; the evidence does not establish the provider's numerical concurrency
limit, whether slots remained occupied after response delivery, or whether
other hosted traffic contributed. Adding a delay or retry is not a proven fix.

All karts had zero checkpoint credits, zero grass and zero rescues when the
race stopped. There is no winner. Jev's three round trips were 480/336/305 ms;
OpenAI's were 468/523 ms; Clef's were 601/375 ms, including the rejected request.
These timings include the full AgentCore path and do not establish driving
performance from this short start.

## Root audit and accounting

Root observed process exit **1**, then audited all seven original requests and
replies, ten outer AWS invocations (three free warmups plus seven actual calls),
114 exact physics frames and fourteen shared budget transitions. The native
429 was never decoded into or applied as a control. Concurrent replies were
drained before finalization. The failed collection's own audit and the separate
outer-envelope audit passed. Source was unchanged; maximum derived sample
lateness was 5.557 ms. No fallback controls or silent reply repair were used.

The full Clef reservation is retained: **$0.00393216 / 75,366 tokens**. Billing
for that request is unknown; an HTTP 429 does not justify refunding the ledger.
The other six replies reported $0.001242504 and 14,519 tokens. Total added charge
is **$0.005174664 / 89,885 tokens / seven requests / one uncertainty**.

The authoritative cumulative ledger is now:

| Field | Value |
| --- | ---: |
| Requests | 99,410 |
| Charged dollars | $11.525691428002778 |
| Charged tokens | 333,938,714 |
| Uncertainties | 72 |
| Pending | none |

Caps remain $20 / 110,000 requests / 500 million tokens. All previous charges
and uncertainties remain. The versioned budget snapshot now reflects this
boundary. Remaining budget does not authorize another admission.

Evidence is under `artifacts/aws-demo-live-rehearsal-v1/trial/`, including raw
queries/replies, the original failed response, frames, accounting transitions,
parent/child Temporal histories, an offline HTML replay and root review. The
[seven native replies](0087-native-responses.json) are separately versioned.

## Final free readiness before the attempt

After Docker Desktop's UI requested a whole-VM shutdown during an earlier free
Cloud run, that interrupted recording and its histories were retained. Root
restarted only this demo's container and qualified the new boot and server.
The complete v5 gate passed four full trio controls / twelve clean finishes,
21 parent-pause physics samples and the 170.1-second neutral trace. Its source,
boot and server identities were revalidated before live admission.

The subsequent complete free Cloud interface passed 6,703 physics frames,
680 exact mock native packets, 1,360 budget transitions and all 683 AWS
invocations including warmups. All three scripted karts finished, with
four/five/five rescues. Maximum derived lateness was 16.154 ms. These remain
mock outcomes, not model results.

See [the environment investigation](../env-file-investigation.md) for the
separate unresolved `.env` resets and confirmed Docker Desktop shutdown.

## Next step

A proposed demo-hardening change would retire only a kart whose provider fails,
keep its DNF visibly labeled, and let the other models finish without retrying
or inventing controls. That would require a new prospective release, fresh free
validation, and explicit live admission after this closed attempt is reviewed.
No such new paid race has been run.
