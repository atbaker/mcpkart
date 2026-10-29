# Two-kart delivery checks

These are software, free-runtime and presentation checks after the paid cohorts
closed. They do not add model trials or improve a model's driving score.
The [findings checkpoint](2026-10-22-two-kart-checkpoint.md) reports the actual
24 duels separately.

## Changes after collection

- Retain the DecisionClient's implicitly loaded credential for exact redaction
  when a mock error body echoes it. Authentication headers are never captured.
- Close a failed finish/transport session before a replacement admission while
  leaving a running duel intact after an invalid owner capability.
- Report actual `/proc` worker RSS/high-water mark separately from Linux
  `resource.ru_maxrss`, which can include the parent's pre-exec peak. The final
  recording explicitly marks memory measured before transfer/serialization.
- Give the spectator safe labels, model-call timelines, clickable event markers,
  live/replay controls, highlighted gates and a bounded replay catalog. Queued
  catalog reads recheck the active clock after acquiring the catalog lock.
- Export compact standalone visual HTML at 20 Hz while preserving complete
  60 Hz audit masters. Native controls and physics samples are not resimulated
  or replaced for presentation.
- Add one-match and complete free-clock commands. Paid admission preserves all
  saved ledger caps, rejects pending/exhausted ledgers and stale qualification,
  and performs no retry. Optional spectator-status write failures are warnings
  and do not interrupt the model loops.
- Update Cloud setup's snapshot ceiling from $10 to the user-authorized $20;
  its exclusive-create behavior continues to preserve an existing ledger.

Physics, the physical menu, the factual prompt builder and goal-only rules
were not tuned based on model comparison outcomes. Original actual collection
source remains under `artifacts/two-kart-session-v1/collected-source/`.
The final 26-file source archive is `final-source-v3/` under the same root.

## Software and browser checks

The latest complete suite passed **602 tests**, with three optional Rust skips
and zero warnings. Ruff, JavaScript syntax and `git diff --check` passed. An
earlier full run emitted one Python 3.14
multiprocessing `BytesIO` finalizer `BufferError` warning during cancellation
cleanup. The affected runtime/web group then passed 17 tests with that warning
made fatal; it did not recur there or in the final full suite. These reruns are
not proof the intermittent warning has been eliminated.

New cases cover independent racer capabilities and replies, pending-command
cancellation/failure, held inputs during disconnect, one finisher continuing
alongside the other racer, rotated opponent coordinates, glancing contact's
speed cap, separation without checkpoint credit, implicit-key redaction and
shared-budget settlement. Command checks reject stale evidence, source/boot/
server changes, escaped evidence paths and invalid/exhausted budgets while
preserving charges and the expanded caps.

Two actual-MCP free command smokes passed exact audits: an ordinary 0.7 s
deadline, and another with an intentionally unwritable spectator-status path.
Both are deliberately incomplete races, not counted model finishes. The latter
retained its `FileExistsError` warning while both drivers and the recording
continued correctly. The real ledger was unchanged.

Fifty additional finite free start/stop attempts each opened a fresh real-HTTP
MCP session, applied one command to both karts, stopped and verified that its
child exited. All passed, with zero read errors and no real-ledger change.
This is a lifecycle smoke, not a general reliability estimate, a timing gate
or fifty new model races.

Final presentation checks found and fixed two gaps: the live result caption
now names the winner or same-tick tie, and direct replay downloads preserve
the matching model labels without mutating cached records or attaching stale
labels from another race. The new web/export cases passed eight focused tests.

The public free one-match command then ran with Chromium watching from 0.6 s
through completion. Both karts finished cleanly, all 674 mocked questions and
saved frames passed reconstruction, correct scripted labels were visible,
the live winner appeared and controls remained disabled in live mode. The
download retained labels and excluded capabilities; rewinding hid the result,
seeking beyond the first finish restored it, and sixteen event markers were
available. The tie caption passed a clearly separate rendering fixture. There
were no browser exceptions. Maximum lateness was 6.533 ms, p95 1.628 ms and
drift 0.821 ms. This is scripted practice, not a model performance trial.

Chromium checks passed for the featured replay, event seek, no early winner,
disabled live replay controls, stale asynchronous file load, safe text labels,
embedded data and continued playback after all networking was blocked. There
were no browser exceptions. Managed Chromium policy blocked `file:` URLs;
the identical standalone page was tested over local HTTP before blocking
networking. This is not a claim that the managed browser permitted a local-file
open. See `browser-checks.json` and `duel-ui-reviewed.png` in the artifact root.

## Final free clock qualification

The initial post-collection attempt in `final-clock/` passed its first complete
free duel, then stopped with `httpx.ReadError` on the next `start_duel` response.
The server had accepted that start, but the client had received no capability
and sent no driver/model request. The server remained alive, no cgroup OOM
event was recorded, and the neutral race ran to its 240 s deadline. Its full
recording and failure descriptor are preserved. The transport cause remains
unresolved. This attempt did not qualify the clock and was not silently retried.

The first successful post-collection full attempt in `final-clock-v2/` passed four full
free controls, actual physics advancement during a 350 ms HTTP-parent pause,
and a 600 s neutral recording with 30 s worker-memory observations. All source,
server/process-start, boot and evidence hashes are bound in its qualification.
The original maximum-lateness/p95/drift limits remain 100/25/100 ms. No builds,
tests, video rendering or heavy analysis run alongside its timed collection.

The process exited successfully and its absence was verified. All 18,878
control physics frames and 2,677 mocked questions reconstructed exactly; both
karts finished all four controls cleanly. The parent pause contained 21 physics
frames. The neutral deadline produced 600.0167 s at fixed-step resolution and
36,002 exact frames. Maximum wake lateness was 53.590 ms, p95 4.495 ms and
absolute drift 6.203 ms; the stricter saved post-step sample maximum was
53.800 ms. There were zero cyclic collections. The final worker `/proc` RSS
and high-water mark before recording transfer were 439,356 KiB (429.1 MiB).
Transfer/serialization peak memory is not included in that measurement.

The qualification SHA-256 is
`c272d3ea119412d2bc785500d041f68e709244a6269974e89a421382ecd4616f`.
Source, runtime, boot, parent process start and every evidence hash were checked
again after exit. All 26 source files then matched `final-source-v2/`. The real
model ledger remained byte-for-byte equivalent to the paid closure. A saved
gate is specific to that source, machine, boot and HTTP server; it is not
transferable to a rebuilt Cloud environment. The later live-winner and
downloaded-label changes require a new complete source binding; they do not
inherit this gate. The final `final-clock-v3/` run binds the completed
presentation source in `final-source-v3/`.

That final gate passed and was independently revalidated after observed
process exit. Its four full controls had eight clean finishes, 2,679 exact
mocked questions and 18,892 exact frames. The parent pause again contained
21 physics frames. The neutral trace had 36,002 exact frames over 600.0167 s;
maximum wake lateness was 39.234 ms, p95 3.943 ms and drift 0.704 ms. The saved
post-step sample maximum was 39.431 ms, with zero cyclic collections. Worker
RSS/high-water mark before transfer was 439,608 KiB (429.3 MiB). The final
qualification SHA-256 is
`adf99cbc968e28ae9b20f623818bbcb919b86a65e1b59149dc57866d1a3de252`.
All 26 source files match the final archive and the real ledger is unchanged.
[Machine-readable delivery proof](0076-0078-two-kart-delivery-checks.json)
retains the metrics, source hashes, software/browser checks and earlier failures.

The setup snapshot change also passed an isolated smoke of the script's exact
embedded seeding block: a fresh temporary workspace received the exact $20
snapshot, an existing ledger remained byte-for-byte unchanged, and the real
ledger was untouched. Shell syntax passed. No dependency installation or
setup job ran alongside timed collection.

No additional paid calls occur in these delivery checks. All 70 historical
uncertainties, charges and cumulative limits remain preserved.

## Portable review bundle

`artifacts/two-kart-session-v1/mcpkart-two-kart-review.zip` contains a local
review page, three actual H.264 videos, three embedded interactive replays,
all 48 outcome rows as CSV/JSON, six captured native examples with verified
application ticks, reports, selected source and a hash manifest. It contains
no API credential or private driver/owner capability. Complete 60 Hz audit
masters and all raw calls remain separately in the workspace.

ZIP integrity, all 65 payload-file hashes and 21 local asset links passed.
Chromium desktop and 390 px mobile layouts had no horizontal overflow. All
three videos decoded, sought to two seconds and advanced through rendered
frames with no dropped frames in that check. All three 20 Hz embedded replays
loaded, hid early winners, reached their saved final states and continued
animating after all networking was blocked. There were no browser exceptions.
These are presentation checks, not extra model trials. The archive's exact
digest is in its adjacent `.zip.sha256` file; the compact bundle omits full
raw audit masters. Extract it and open `index.html`, or serve the directory
locally as described in its README if browser file policy requires HTTP.
