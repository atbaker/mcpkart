# 0088 stage outcome: closed

The registered stage entry ran with Local Activities at 22:58:55–23:01:53 UTC
on 29 October, before the user's subsequent request to switch activity modes.
Both 0088 entries are now consumed and CLOSED. They cannot be reused.

Jev finished first in 103.50 seconds with two rescues and 260 requests.
OpenAI finished in 136.78 seconds with nine rescues and 249 requests.
Clef retired after request 33 produced a transport failure at approximately
59.88 seconds; it had five rescues. The other drivers continued. No native
reply/status/usage exists for that last Clef request; its full reservation is
preserved. No request retry, replacement race or fallback driving occurred.

The operator's saved exit and a fresh read of its SSM invocation both report
success/exit 0. Root independently reconstructed 8,252 exact physics frames,
542 native requests and 1,084 budget transitions on the qualified host.
Maximum derived lateness was 2.999 ms. All 545 AgentCore attempts were audited:
544 returned envelopes, including three mock warmups, plus one preserved
missing response. Available native bytes matched, no observed SDK retry
occurred, and current source/clock/server bindings revalidated.

This stage added 542 requests / $0.105897926 / 1,445,427 charged tokens /
one uncertainty. The ledger is 100,603 requests / $11.786845266002775 /
337,074,715 charged tokens / 74 uncertainties, pending empty. All earlier
charges/failures/uncertainties and the $20 / 110k / 500m caps remain intact.

The first subsequent regular-Activity review correctly refused the stale
100,061-request boundary. Nothing was overwritten or refunded. Root then
reviewed this actual completed stage and used its exact reconciled boundary.
Raw evidence remains under artifacts/aws-demo-dnf-live-stage-v1; independent
review under artifacts/aws-demo-ec2-regular-review-v2.

The [regular-Activity comparison](0088-regular-activity-amendment.md) makes zero
paid calls. A new [single-entry 0089 registration](0089-regular-activity-registration.md)
covers a future manually invoked regular-Activity run.
