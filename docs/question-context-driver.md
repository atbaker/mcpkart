# Experimental Jev question-context driver

The question-local prompt places the current wheel facts inside the wheel
question and the current pedal facts inside the pedal question. Both questions
are answered in one Decisions API POST. The wheel has five choices and the
pedal has three; their original native inverse produces one of the same
fifteen controls. Jev selects both answers. The host supplies geometry and
motion facts, including a bearing computed from the supplied coordinates,
and does not evaluate a policy condition to select the kart's controls.

The unchanged research prompt completed eight fresh solo stadium starts
cleanly in [0053](experiments/0053-fresh-start-validation.md), following the
positive [paired pilot](experiments/0052-native-compatibility-driving.md).
It follows a supplied fixed bearing/edge policy. This is evidence for a
24 m solo stadium in two directions with small start-pose variations;
other tracks, opponents and recovery outside its domain remain untested.
The application default and joint `damped` baseline are unchanged.

The subsequent versioned-driver smoke and model comparison bring the Jev
record to 14/14 useful, 13/14 clean finishes. OpenAI completed both matched
comparison starts cleanly with this unchanged setup. See the
[current findings](experiments/2026-10-21-progress-checkpoint.md) and
[portable examples](experiments/current-driver-examples.json). All prior paid
windows are closed; Clef is set aside after the separate 0069 timeout.

## Run one race

Start the process-isolated Python spectator/MCP server as usual. Configure
`OPENROUTER_API_KEY` through the environment's secret binding. Preserve the
shared `artifacts/budget.json`; the command requires an existing ledger and
preserves its saved request and token authorizations.

After a new authorized experiment window is established, the command in this
qualified cloud checkout is:

```bash
.venv/bin/python -m mcpkart.question_context_run \
  --seed 43 --course stadium \
  --clock-qualification artifacts/jev-six-hour-v2/restart-clock-v2/qualification.json \
  --output artifacts/jev-observed-race
```

Use `--course stadium_clockwise` for the other direction. Output must be a
new directory. The command runs exactly one three-lap race on the fixed 24 m,
12 m/s, 0.12 rad setup and never starts another race automatically. An optional
`--stop-at` accepts an absolute ISO8601 deadline with timezone. The default
800-decision ceiling bounds this single race. The MCP URL defaults to
`http://127.0.0.1:8765/mcp`; `--url` overrides it.

The engine clock qualification must belong to the current source, boot and
server process, and include the complete pause, control and long-clock gates.
A new environment needs a fresh qualification. With many recordings, explicitly
warm the idle `/api/replays` catalog before the first MCPstart; see the recovery
note in [cloud-development.md](cloud-development.md). The October20new-boot
qualification includes that warm-cache condition. For experiment collection,
complete the exact-interface free controls and native compatibility checks
specified in the study before paid use; this command does not run or invent
those qualification results. See [0054](experiments/0054-versioned-driver-smoke.md)
for the extracted wrapper's integration qualification and current status.

## Recordings and domain

`trial.json` contains the ordinary race and full physics samples. Its request
records retain raw observations, projected facts and actual wire questions.
The race header contains question templates. `query-*.json` and `calls/`
save the actual per-query questions, raw request/response bodies, native
records and budget transitions. Authentication headers are excluded. Source
hashes for all three controller modules are separate from the existing core
engine fingerprint, which does not include these new modules.

A nonforward 15 m preview or a positive uncredited required gate ends the
attempt as a quality failure, before a further model POST. Invalid native
answers, identity mismatches or uncertain accounting stop the driver without
returning a control. A stopped driver cannot resume. The server's existing
three-second off-road rescue remains part of the recorded game rules.
