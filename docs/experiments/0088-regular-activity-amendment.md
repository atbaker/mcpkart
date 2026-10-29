# Regular Activity switch and free comparison

The user requested switching off Local Activities and seeing how regular
Activities perform. Inspection confirmed that both 0088 Local Activity entries,
including the stage run at 22:58:55–23:01:53 UTC, had already completed before
this change. They remain closed and unchanged. No 0088 entry can be reused.

The operator now omits --local and requires a regular-Activity Cloud interface.
The existing workflow.execute_activity path is used for every kart_step;
start/finish were already regular Activities. Models, providers, physics,
prompts, controls, three child workflows and provider retirement stay fixed.
No runtime or workflow source changes were needed. SDK eager dispatch retains
its existing default.

One complete free Cloud regular-Activity race was compared with the earlier
exact Local Activity Cloud mock race. These tests make zero real model calls.
The already-qualified clock is revalidated on the same boot/source/server.
The cumulative ledger includes the intervening completed stage run: 100,603
requests / $11.786845266002775 / 337,074,715 tokens / 74 uncertainties,
no pending; all caps unchanged. Root's first review refused an outdated
100,061-request boundary, preserving the mismatch evidence; the stage records
were then independently reviewed against the actual ledger.

The new [0089 registration](0089-regular-activity-registration.md) defines one
future manually invoked regular-Activity demo run. No extra paid rehearsal
is launched during this switch.

References: [Temporal Local Activities](https://docs.temporal.io/local-activity)
and [latency tradeoffs](https://docs.temporal.io/design-patterns/local-activities),
retrieved with Exa and Temporal's documentation connector on 29 October.
Generic estimates from those docs are not measurements of this application.

## Measured result

Both runs used the same source, boot/server, seed/grid, three scripted model
policies, 200-ms mock work, AgentCore Runtime and Temporal namespace. These are
sequential free Cloud runs, not a matched paid model comparison.

| Measure | Earlier Local Activities | Regular Activities |
| --- | ---: | ---: |
| Median native request cadence | 333.45 ms | 381.36 ms |
| p95 native request cadence | 1,203.04 ms | 419.33 ms |
| Median reply-to-next-request gap | 50.46 ms | 104.86 ms |
| p95 reply-to-next-request gap | 906.87 ms | 128.87 ms |
| Median mock API/bridge latency | 279.39 ms | 272.72 ms |
| All three mock karts finished by | 106.45 s | 96.47 s |
| Total rescues | 10 | 0 |
| Native mock requests | 743 | 720 |

Regular Activities added roughly 48 ms to the median request cadence but had a
much smaller p95. All 68 reply-to-next-request gaps over 500 ms in the Local
Activity run occurred after sequence positions 7 modulo 8, coinciding with the
existing every-eight-step marker-flush timer. This is an association in this
configuration; it is not a general claim that regular Activities have better
latency. Their slower but steadier cadence also changed the scripted trajectory.

Regular Activity schedule-to-start latency measured from history was median
11.446 ms / p95 13.778 ms / maximum 50.429 ms, all attempt one. The full
reply-to-next-request gap is broader than that server-history metric.

The three regular child histories contain 720 ActivityTaskScheduled, 720
ActivityTaskStarted and 720 ActivityTaskCompleted events, no Local Activity
markers, and all completed without failed/timed-out events. The earlier Local
Activity children have 743 Local Activity markers and no regular Activity
events. Total child-history events rose from 1,213 to 4,335.

The full regular race audit passed 5,789 physics frames / 720 exact native
queries / 1,440 budget transitions, with maximum derived lateness 4.250 ms.
All 723 AgentCore invocation envelopes matched their native bytes; no SDK
retries or missing responses occurred. All three mock karts finished with zero
rescues. The real ledger remains exactly unchanged, with zero paid calls.

See [the complete measured data](0088-regular-activity-comparison.json).
The operator command is unchanged, and the remaining stage entry stays manual.

## Release-bound repeat

A second full regular-Activity run qualified the new 0089 release on Runtime
version 7. All three mock karts again finished without rescues. Median cadence
381.95 ms and p95 419.45 ms closely matched the first regular run. Mock bridge
latency was median 272.13 ms / p95 299.48 ms; reply-to-next-request gap median
107.26 ms / p95 134.71 ms. All three finished by 123.68 seconds, showing that
finish times can vary even with similar cadence. No general speedup claim is
supported by two sequential scripted runs.

The repeat audited 7,422 physics frames / 782 exact native packets / 1,564 budget
transitions, max derived lateness 3.414 ms. Its 785 outer AgentCore exchanges
matched native bytes with no observed SDK retries or missing responses.
The same clock/source/server binding was revalidated, and the real ledger
remained exactly at the closed stage boundary. The new one-entry release is
manual; no new paid driving was performed.

See [the repeat measurements](0089-regular-activity-qualification.json).
