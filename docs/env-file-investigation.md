# Investigation of the root .env resets

29 October 2026. No credential values are included here or in the diagnostic
metadata under ignored `artifacts/env-reset-investigation/`.

The root `.env` was found with blank credential fields and a 185-byte size at
12:42:04 and 12:58:39 Pacific. The current restored file is 706 bytes, last saved
at 14:20:25. Its Temporal settings were immediately preserved in an ignored
0600 file and successfully authenticated from the demo worker.

## What was checked

- The only process holding `.env` during inspection was Docker's macOS
  Virtualization helper, with a **read-only** descriptor. That is expected for
  the read-only project bind mount and is not evidence that it wrote the file.
- VS Code local history contains credential-bearing saves at 12:34 and 12:35
  and an Undo/Redo save at 12:53. Historical contents were inspected only for
  metadata; no credential values were printed. These records do not attribute
  either blank-file overwrite.
- The Git hooks directory contains only inactive sample hooks. Project Codex
  hooks invoke Entire only if it is installed; its CLI was absent, making those
  hooks no-ops. No relevant shell-profile template-copy rule was found.
- Recorded tool calls around the reset windows contain no matching overwrite.
  The original template creation at 12:33 used `O_CREAT | O_EXCL`, so that
  operation could not overwrite an existing credential file.
- The relevant dev processes' working directories belonged either to this
  spectator or separate demo projects. No process was stopped on suspicion.
- A bounded ten-minute kqueue watch observed **zero write/rename events** after
  the latest restoration. This cannot identify a process that wrote earlier.

**The historical writer is not conclusively identified.** A current open-file
list is not a historical write audit. Administrator filesystem tracing was not
available (`sudo -n` required a password). If another reset occurs, a trace
started beforehand can identify the writing process, for example:

```sh
sudo fs_usage -w -f filesys -t 60 | rg --line-buffered 'mcpkart/\.env'
```

This prints file operations and process names, not file contents. The user must
authorize the local administrator prompt; do not paste passwords into chat.

## Separate Docker shutdown

During the subsequent free Cloud rehearsal, Docker Desktop's Electron process
requested backend shutdown at **14:28:10 Pacific**. The backend stopped the
whole Linux VM; the MCP Kart container ended at 14:28:14 with exit 137 and
`OOMKilled=false`. Host logs show an orderly shutdown and `app.exit(104)`,
not an OOM indication. Other local Docker work was also affected and later
restarted Docker Desktop.

The logs do not identify who initiated the desktop quit. This is a separate
incident from the earlier `.env` resets. The partial mock collection and
Temporal histories were retained. No paid entry was consumed, and the old
boot's qualification was retired. A fresh full qualification is required.

Keep Docker Desktop running throughout the demo. The operator helper uses its
private Temporal copy and refreshes only this demo's AWS session credentials;
no unrelated AWS resources, local containers, editor settings, or security
software were changed as part of this investigation.
