# MCP Kart

MCP Kart is a competitive kart racing game in which AI drivers race autonomously while people watch and compare their performance.

## Language

**Racer**:
A competitor entered in a race, with an identity used for standings and results.
_Avoid_: Player when it could mean the human spectator.

**Kart**:
The vehicle a racer controls on the track.

**Driver**:
The AI agent controlling a racer's kart.
_Avoid_: Model when referring to the whole agent.

**Driving model**:
The LLM a driver uses to select kart controls.
_Avoid_: Driver when referring only to the model.

**Observation**:
A view of the kart and track available to a driver when choosing its next control input.

**Telemetry profile**:
A named way of presenting an observation, such as raw coordinates or explicit road-relative bend summaries. It supplies facts without selecting controls.

**Bend summary**:
The direction, extent, heading change, and tightest radius of a continuous curved road region ahead. Distances follow the centreline from the kart's nearest road projection.

**Rescue**:
An automatic return to the road near the point a kart departed after it remains off-road for too long. A rescued kart stops facing along the road, and the race clock continues.

**Racing strategy**:
Instructions supplied by a human to guide their driver's choices during a race.

**Bot**:
A racer whose driver is operated by the game service rather than a participating user.

**Spectator**:
A person watching a race as it unfolds.

**Direct control**:
Driving by selecting steering, throttle, and braking inputs rather than asking an automatic controller to perform a maneuver.

**Realtime race**:
A race that advances with elapsed time while drivers make decisions, including while a driver is waiting for its model.
_Avoid_: Turn-based race, decision tick.
