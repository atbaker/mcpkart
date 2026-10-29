# 0080 — fresh baseline attempt after provider overload

The 529 did not recur: **all 575 native requests returned HTTP 200 and valid
Jev replies**, and both karts finished. This establishes successful service
for this attempt; it is not a general availability estimate. The one-attempt
window is CLOSED. The original interrupted 0079 race and its uncertain
reservation remain unchanged.

| Kart | Finish | Rescues | API median | API p95 | API maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Red | 97.47 s | 2 | 244.3 ms | 885.8 ms | 3,209.7 ms |
| Blue | 110.25 s | 3 | 239.9 ms | 809.4 ms | 3,722.0 ms |

Both earned all 120 required gate credits. Neither finish was clean: red
spent six seconds off-road and blue nine seconds. There were zero contacts
and three credited-progress lead changes. Twenty-two API replies took at
least one second; three took at least three seconds. Same held-input behavior,
rescue rules and direct native choice mapping applied throughout.

The earlier geometry duel on this exact grid finished both cleanly in
82.48/83.30 s, with API p95 about 303/297 ms and a 550 ms maximum. The new
baseline run had substantially different response timing. We cannot attribute
the driving contrast confidently to the added gate facts, or attribute each
rescue to latency, without a controlled intervention. Across the two starts,
completed baseline attempts are descriptively 1/4 clean and geometry 4/4 clean;
the two original provider-interrupted baseline attempts remain separately
censored. These interacting, small, non-contemporaneous comparisons do not
establish a reliability advantage. The default profile remains unchanged.

The user explicitly asked to try again after the 529. The prospective
[registration](0080-jev-overload-retry-registration.json) admitted one fresh
clockwise-diagonal baseline duel: same seed 522, explicit grid, goal-only
instructions, source, model/provider pin, Python physics and handling as the
interrupted entry. Gate geometry stayed disabled. No standalone paid health
probe, model-call retry, fallback, supplied policy, tuning or additional duel
was used. Current model metadata matched every pinned field other than the
catalog observation timestamp.

The existing complete clock gate and exact-start free control were revalidated
against all 26 unchanged source files, the same boot, HTTP server PID/start
ticks and evidence hashes. The source-identical 0079 software/native checks
(623 passed tests, three optional Rust skips) were reused, not rerun. Root
observed process exit, then reconstructed **all 6,616 physics frames, 575
native requests and 1,150 shared-budget transitions**. Exact request/response
bytes, route identities, direct input application, unique response IDs across
the original study and this attempt, and usage within full reservations all
passed. Maximum saved-frame lateness was 7.309 ms under the unchanged 100 ms
limit. No reply error, new uncertain charge or pending reservation occurred.

This attempt added **$0.062056008**, **575 requests** and **1,532,814 charged
tokens**. Closing totals are **$11.290856144002776 / $20**, **97,353 / 100,000
requests** and **328,183,549 / 500,000,000 charged tokens**, with the same
**71 uncertainties** and no pending reservation. Preserve the original
529 reservation of $0.000688128 / 252,313 tokens; its billing remains unknown.
The [results](0080-jev-overload-retry-results.json) and current
[budget snapshot](model-budget-snapshot.json) retain the new boundary.

Complete recordings, per-call wire evidence and audits are under
`artifacts/jev-gate-retry-v1/`. The standalone
`baseline-retry-replay.html` uses the same spectator UI, with saved 20 Hz
visual data; the 60 Hz master remains the audit source. No paid calls remain
active and no further race is admitted by this window.
