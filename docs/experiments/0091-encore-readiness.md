# Encore readiness and closeout, 10–11 November 2026

Status: complete. The user reported that the demo worked great and requested
cleanup, commit and push on November 11. The November 10 release has expired.
No additional races were run for cleanup.

All six manually invoked executions have saved SSM Success/exit 0 and completed
independent Linux reviews. All uncertainties and incomplete kart outcomes are
retained. The [machine-readable closeout](0091-encore-closeout.json) records each
execution and the final cumulative ledger.

| Run | Jev finish | OpenAI finish | Clef finish | Native requests |
| --- | ---: | ---: | ---: | ---: |
| 0001 | 115.08s | 137.20s | 154.48s | 669 |
| 0002 | 106.17s | 119.85s | 162.33s | 673 |
| 0003 | 102.60s | Time limit | 158.78s | 754 |
| 0004 | 146.55s | 137.37s | 179.25s | 818 |
| 0005 | 100.10s | 145.93s | Provider DNF | 629 |
| 0006 | 97.17s | Time limit | Time limit | 819 |

The six runs used 4,362 native requests and 10,846,220 charged tokens, adding
$1.166092696 in reserved/charged model accounting. Run 0005 retained the full
reservation for its missing Clef reply, adding one uncertainty. No model request
was retried. Successful process exits establish completed execution and audit;
the table separately shows each kart's outcome. These demo races are not a
controlled model-ranking study.

Final cumulative ledger: **107,748 requests / $13.71908846000279 /
356,809,871 charged tokens / 78 uncertainties**, pending empty. The versioned
budget snapshot matches the last reviewed ledger. All original artifacts and
prior failed audit attempts remain intact.

The spectator now includes model branding, larger kart icons, replay loading
feedback, aligned dropdown chevrons and live snapshot interpolation. A local
recorded-feed check rendered at 120 Hz from an 8–10 Hz feed, with 0.5–0.9ms
p95 drawing cost; that is local rendering evidence, not a general benchmark.
The SSM tunnel watcher reconnects after drops, and the replay menu retries after
transient failures. A separate test forward recovered in 3.06s without touching
the primary spectator or submitting a race.

Cleanup validation: **838 tests passed, 16 skips; Ruff passed**.
Credentials and bulk recordings remain ignored. Existing AWS infrastructure
was preserved. The following sections retain the original readiness evidence
from November 10, before the event.

## Original readiness checkpoint

The user requested checking the existing demo for a 16:00 Pacific tech check
and an event ending at 21:00.

The existing dedicated EC2 instance is healthy and SSM is online. Its game
container has remained running since29October, with no restarts or OOM event.
The physics/MCP source matches the previous manual release exactly. Temporal
namespace `mcpkart-dev.iuiaz` accepts the existing private credentials. Public
OpenRouter discovery still returns the same three model versions, providers
and prices. Local and remote cumulative accounting match exactly, with no
pending reservations.

The October release expired. The new prospective release is
`artifacts/aws-demo-encore-release-20261110-v1`, digest
`f1c7b120d0aaafb6c7897e733467d93706d77b730b06d71f5b8766b121f03c65`.
AgentCore Runtime11 is READY. Only authorization digest and expiry changed;
adapter code, role, network, secret reference and lifecycle settings are
preserved. Expiry is22:00 Pacific on10November, allowing an hour after the
event. The fifteen-minute admission floor remains.

There are ten fresh prospective identities, `mcpkart-demo-20261110-0001`
through `-0010`. One is for the verification rehearsal; remaining races require
individual manual invocation. There is no automatic race loop or model-call
retry. The new session enforces the existing caps and full outcome audits
between entries. October's day-specific audit/budget waivers are not reused.
Ghost physics, prompts, routes, native controls, regular Activities, MCP and
provider-failure retirement are unchanged.

Initial ledger:103386requests /$12.552995764002763 /345963651charged tokens /
77uncertainties; pending empty. Caps remain$20 /110000requests /500000000tokens.
All historical evidence and charges are retained.

Free checks and the rehearsal have separate dated artifact
directories. No original race is resubmitted. The SSM forward17773 and updated
read-only spectator17774 have been restored. The dedicated game server has
not been restarted. Other demos' infrastructure was not modified.

Operator changes point the existing race/resume command at the new release,
require a full successful outcome audit before the next entry, and reject
expired releases locally before allocating an attempt or submitting an AWS
command. Targeted accounting/operator checks passed; initial two loopback proxy
tests were blocked by the filesystem sandbox's socket restriction and all46
then passed with local binding allowed. After adding expiry and audit-failure
coverage, all16 operator/admission tests passed. Ruff passed. No game source
was changed.

The complete free clock passed four full races and12 clean kart finishes,
21 physics frames through the parent-process pause, and170.1seconds of neutral
clock. Maximum derived lateness across controls was7.445ms; neutral maximum was
2.611ms. Evidence: `artifacts/aws-demo-encore-clock-20261110-v1`.
Observed SSM Success/exit0,22:08:02–22:18:19UTC.

The exact Cloud mock passed all three finishes by103.77s, with one scripted Jev
rescue. All714 native requests and717 outer AgentCore exchanges matched, with
zero retries or missing responses. Maximum sample lateness was5.580ms. All714
descriptive Activity results matched native facts, choices and SQLite receipts;
largest result was1141bytes. Evidence:
`artifacts/aws-demo-encore-cloud-free-20261110-v1` and
`artifacts/aws-demo-encore-root-review-20261110-v1`. Both jobs exited0.

| Scripted Cloud metric | October29 | November10 |
| --- | ---: | ---: |
| Temporal schedule-to-start median | 11.15ms | 11.16ms |
| Temporal schedule-to-start p95 | 13.34ms | 13.26ms |
| Full request cadence median | 398.33ms | 411.14ms |
| Full request cadence p95 | 447.98ms | 455.66ms |

These are sequential scripted races with different trajectories and service
load. Scheduling remains comparable; this is no controlled speedup comparison
or model ranking.

The live rehearsal used the ordinary operator command once, identity
`mcpkart-demo-20261110-0001`. All three models finished:

| Driver | Finish | Rescues | Native requests | API median / p95 |
| --- | ---: | ---: | ---: | ---: |
| Jev | 115.08s | 3 | 222 | 294 /964ms |
| OpenAI Decisions | 137.20s | 8 | 261 | 377 /565ms |
| Clef | 154.48s | 13 | 186 | 618 /1013ms |

No provider failure occurred. Jev and Clef had slower tail latency than the
October manual race (p95 then304/549ms); OpenAI p95 was622ms then. Model latency
and outcomes can vary. Physics and orchestration remain unchanged.

Root observed SSM Success/exit0 for command
`6cb7ce4f-341d-4ccf-b0ff-59481423b8e3`. The independent qualified-Linux audit
replayed9270 frames,669 exact native questions,1338 budget transitions and all
672 AgentCore exchanges. Every native reply wasHTTP200; no retries or missing
responses. All669 descriptive receipts matched. Maximum derived sample
lateness was4.618ms. All four Temporal workflows completed without failed or
timed-out events. Evidence:
`artifacts/aws-demo-live-mcpkart-demo-20261110-0001` and its `-audit-v2` directory.

The first local post-race audit refused Linux track checkpoints that differ by
floating-point rounding on macOS. The full audit therefore now runs inside the
same qualified Linux container. Its first attempt exposed an independent
auditor bug: it compared full-precision master-frame time with the API's
four-decimal observation time. The corrected auditor derives the existing API
format exactly, without changing engine state, model inputs or saved results.
Audit-v2 passed. Both failures and the diagnostic are preserved. No race or
model request was repeated. A native-observation regression test covers this
case;20 operator/admission/audit tests and Ruff passed after the fixes, plus the
33 previously passing Decisions tests. The audit binds every downloaded trial
payload hash, including the receipt database, before enabling another entry.

The rehearsal charged$0.185042144 and1641308tokens. Ledger after qualification:
104055requests /$12.738037908002774 /347604959charged tokens /
77uncertainties; pending empty. No historical reservation was released and no
new uncertainty was added. The next fresh identity at that checkpoint was
`mcpkart-demo-20261110-0002`. A `resume` confirmed no pending recovery then.

The updated spectator rendered the actual live race and finish, with no browser
errors. The large kart icons, model names and live winner banner worked.
Viewer17774 and original embedded offline fallback17875 both returnedHTTP200.
The browser is left on the completed real rehearsal; selecting Live follows the
next manually invoked race. Restart commands are in the main demo guide.
