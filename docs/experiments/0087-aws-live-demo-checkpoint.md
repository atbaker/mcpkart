# 0087 demo checkpoint — 29 October 2026

Implementation is on `codex/aws-temporal-demo`. The
[prospective registration](0087-aws-live-demo-registration.md) admits one
rehearsal and one later manually launched stage race, with no retries or
replacements. Neither entry has been consumed. There have been zero new paid
model calls; all previous studies remain closed.

## Completed verification

Final Linux software checks passed **825 tests**, with six optional/separately
run skips. Three real Temporal integration checks passed separately, including
workflow-task replay after a Local Activity returned and before its marker was
persisted. Broker receipts allowed one model dispatch and one MCP command.
Ruff and diff checks passed.

The final environment is official Python **3.14.8** in the dedicated
`mcpkart-demo-linux-20261029` container. The final server is PID **295** in that
Linux boot. Host loopback port **8773** maps to its spectator/MCP port 8771.
Preserve this server and boot; validation checks their exact identities.

The complete free qualification in `artifacts/aws-demo-linux-clock-v4/` passed:

- Four full ghost-trio controls, twelve clean kart finishes, 18,901 physics
  frames and 3,937 exact mock native queries.
- Twenty-one physics samples during the deliberate HTTP-parent pause.
- The full 170.1-second neutral trace, 10,207 exactly replayed frames,
  maximum late wake 21.720286 ms and p95 8.443402 ms.
- Maximum derived sample lateness across driving controls: 36.901059 ms.
- The neutral worker reported 232,296 KiB RSS before recording transfer and
  cyclic GC disabled. External trio memory samples were also captured.

Root observed the successful collector exit and revalidated complete evidence,
source, boot and server bindings on Linux. The model ledger was unchanged.
The spectator's three-card layout, explicit mock labels and replay controls were
inspected in the in-app browser.

The final live-capable AgentCore release is version **4** of the dedicated
Runtime. Its release and deployment receipts are under
`artifacts/aws-demo-live-release-v3/`. Three independent mock warmup probes passed
against that exact release, including access to its dedicated OpenRouter secret.
These probes made zero provider requests.

## Preparation failures retained

The initial floating Docker tag supplied Python 3.14.10. Its first complete
attempt passed all twelve driving finishes but failed the neutral trace with a
221.715 ms late wake. A second attempt failed a control with 133.748 ms maximum
lateness. Neither run qualified. No cyclic GC was recorded in those stalls.

A bounded watchdog diagnostic captured a delay while building spectator state;
it did not establish the full cause. Trio observation construction was then
changed to build each kart's own telemetry once instead of three times while
assembling opponent facts. All four earlier Linux controls were independently
reconstructed afterward: **3,985 question/native packets and every physics
frame stayed exact**. Handling, track, menus, prompts and direct control mapping
were unchanged. A Mac-side reconstruction rejected Linux track config because
of cross-platform libm differences; it was rerun successfully on Linux.

One later free collector was deliberately interrupted with observed exit 130
before fixing admission overhead. Full archive hashes are now checked before
physics starts; the live loop checks source and three manifest identities
without hashing large recordings. The partial attempt is preserved under
`artifacts/aws-demo-linux-clock-v3/`. The final v4 gate used the tested fix.
Earlier releases were unused and superseded without enlarging the two entries.

The earlier qualifier's external memory discovery recognized only the two-kart
worker module. Its own pre-transfer worker memory report remained available;
an extra /proc snapshot was preserved. Discovery now recognizes the trio
module, and the final gate contains the full external samples.

## Credentials and next steps

Root `.env` credentials authenticated successfully, then the file reverted to
its blank 185-byte template twice, at 12:42 and 12:58 Pacific. The cause is not
established. The OpenRouter key was safely stored in this demo's dedicated AWS
Secrets Manager secret before the second reset. The Cloud-interface command
stopped before starting a workflow or physics because Temporal fields were blank.
Its failure log is retained; it made no model request.

The operator helper now snapshots restored Temporal settings into ignored
`artifacts/aws-demo-temporal-private.json`, mode 0600, and reads it inside the
worker process. No credential values enter arguments or logs. A fixture check
confirmed the private copy survives another blank root `.env`. The Cloud mock
race and paid rehearsal remain pending the restored Temporal key/address.

The ledger is still **99,403 requests / $11.520516764002778 /
333,848,829 charged tokens / 71 uncertainties / no pending**, with caps
$20 / 110,000 / 500 million unchanged. No mock finish order is a model result.

After credentials are available: complete the exact Temporal Cloud / AgentCore /
MCP free interface, admit the single rehearsal, observe its process exit and
fully audit raw/native, factual, physics, timing and shared accounting evidence.
Only then may root create the review receipt enabling the stage command in the
[operator runbook](../aws-demo.md).
