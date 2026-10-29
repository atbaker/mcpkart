# Two-kart competitive prototype

The user authorized a 4–5 hour implementation session: start Jev versus Jev,
then add Jev versus OpenAI once working; use simple physical contact that slows
or deflects karts. The cumulative dollar cap is now $20. Existing request/token
caps and all historical charges/uncertainty remain.

## First playable contract

- Python, process-isolated shared 60 Hz physics; independent model loops with
  one POST per racer (up to two in flight globally). One root paid writer and
  one shared atomic budget ledger. Faster drivers can act more frequently.
- Two circular kart footprints of radius 1 m on the existing 24 m stadium or
  mirror, max speed 12 m/s, maximum wheel .12 rad, 15 direct native controls.
- Equal-mass normal contact impulses with restitution .15; no automatic steering,
  target line, avoidance policy, input filtering or response repair. Contact
  is resolved before gate/rescue bookkeeping and recorded for deterministic replay.
- The full footprint determines on-road status and finite-gate clearance. Raw
  observations state body radius and opponent geometry; edge clearances refer
  to the body boundary. Facts and game mechanics contain no action advice.
- Three laps, 40 ordered gates per lap, three-second off-road rescue, no teleport
  checkpoint credit. Respawns are visibly phased for at least one second and
  until separated, preventing a respawn from imparting an artificial collision.
  Finished karts stop and become non-colliding. Both may finish; same-tick finishes tie.
- Common start epoch, side-by-side or declared staggered grid. Lane/grid swaps
  accompany comparisons. Rank uses credited gates then within-gate progress;
  event logs distinguish lead changes, contact and rescues.
- Each racer has its own control capability and command sequence. Rescue
  invalidates only that racer's older replies. Errors remain visible and retain
  prior controls until the race stops; no hidden fallback driver.
- Goal-only wheel/pedal questions retain the existing physical menus and native
  inverse. Both questions receive factual opponent/race state and the competitive
  objective. No supplied driving policy. New prompts/config are frozen per study.
- Live two-kart spectator, saved replay, finish order, contact/rescue markers,
  latency and model identities. Produce a portable visual recording for review.

## Validation before model races

Meaningful contact/progress/footprint tests; solo deterministic parity after
shared-core refactoring; concurrent command/capability/stale-reply tests;
exact multiplayer replay and global budget-event chain. Complete new clock
qualification: three consecutive full free dual-driver controls, parent-pause
isolation, and 170.1 s neutral run. Fresh mocked native checks and real-MCP
interface controls. Freeze source, runtime/boot, routes, prompts and finite
cohort; observe each actual root process exit and audit before the next duel.

Existing solo studies remain closed, and their source/evidence are preserved.
Free tests never use the model key or change the global ledger. No paid calls
are admitted by this design document alone; each new study needs its frozen
protocol within the user's current authorization.
