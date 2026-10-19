# PoC planning doc for MCP Kart

This is a PoC planning doc for a new project I'm calling "MCP Kart".

MCP Kart is a real time (ish) kart racing game played over MCP, inspired by Mario Kart. The AI assistants drive the "racers" using their MCP clients, following high-level directions they receive from their human users.

The goal of the project is to create a unique and entertaining experience for software engineers which inspires them to learn more about MCP and the tools I use to build MCP Kart.

It's primarily implemented in Python, using FastMCP and Temporal.

## Feature ideas

Here's a loosely structured list of feature ideas:

### MCP Kart game

MCP clients today are barely capable of sleeping between MCP tool calls, much less steering a kart in realtime. So I'm thinking our best approach, both to make the game playable for the AI assistants and easier for us to implement, is to implement each race as a series of turn-based "steps":

- We should aim for each race to be maybe 2-3 minutes long
- The race should consist of "steps" / "clock ticks" which occur every one second
- In between each of these "ticks", AI assistants can use the MCP Kart MCP client to send instructions to the server for controlling their racer.
    - For example: the instruction could be to press / depress the accleration pedal, turn the steering wheel left or right, or use an item acquired from an item box
    - When we receive new input from via our MCP server, we should incorporate those into the game state before the next "tick"
    - When the next "tick" occurs, we should then apply our current set of inputs to the previous step's game state (e.g. if a racer's new input this tick was to press the accleration pedal, we should increase their racer's speed by 1)
    - The game does not require new input from racers every tick, however. If we receive no new input this tick, we simply apply the input controls for that racer as they were at the start of the previous tick. This is intentionally part of the challenge I want to give AI assistants: the best ones will win races by balancing speed + frequency of input commands with good strategy
- Each race should have 8 racers. When we don't have enough human-controlled racers in a race, we should fill it out with fully "AI" (NPC) racers so the humans have other racers they can compete against
- The race course is comprised of a finite set of "tiles" arranged in a loop, so that each race can consist of three laps. To start, let's just focus on a simple oval race track with four 90-degree left turns and straightaways in-between. Maybe each loop is 20-ish tiles?
    - Later, I might want to introduce more complex courses / courses which are procedurally generated so that AI assistants don't have vision of the course ahead of time and can't simply write a script which preemptively anticipates each turn
- For speed and steering, let's try to keep things relatively simple:
    - Maybe a kart's speed ranges from 0-3, where 0 is "stopped" and 3 is "top speed"
    - Maybe we can keep the relationship between the course and karts' speed simple too: perhaps each "tile" consists of three distance subunits. A kart going at speed 1 needs 3 ticks to move through a tile. A kart going at full speed needs just one tick to traverse a tile
    - For steering, let's not try to simulate different degrees of steering - let's just allow values of "left", "right", or "straight". But I do want to make it a little challenging for AI assistants to keep their racers on the course. So how about, to start, in order for a kart to successfully navigate one of our 90-degree turns, it must be traveling at speed 1 and must send a "left" steering command while the kart is traversing the turn tile. Otherwise, the kart goes off the race course and is reset at speed 0 in the previous tile after a short penalty
        - We can get more complicated later by perhaps mixing long vs. short turns, but let's not overcomplicate things for our PoC
    - For now, let's not worry about simulating karts colliding with each other. Except for how racers use power-ups, karts don't really interact with each other
- For power-ups, I want to implement a simple version of Mario Kart-style item boxes and power ups:
    - We should put item boxes in 4 equidistant tiles in our PoC loop race course
    - When racers traverse a tile with an item box, they automatically trigger the power up "slot machine"
    - To start, let's just include three power ups: a temporary speed boost, a missle, and a homing missle. These roughly correspond to the mushroom, green turtle shell, and red turtle shell in Mario Kart
        - The speed boost should increase the racer's speed to 5 for maybe 2-3 ticks
        - Let's wait to implement the missle and homing missle until after the PoC
    - After traversing a tile with an item box, we should randomly select a power up for the racer among the available options and then include that in our next response to their MCP client containing the game's state
    - The racer's power up is stored until it is invoked via an MCP client input. If a racer doesn't use their power up before they encounter the next item box, they retain their existing power up and don't receive a new one
- As for how users play the game: long-term I want them to be able to anonymous join a lobby for an imminent race, kind of like online FPS matchmaking. Maybe we start new races every 2 minutes. If we have more than 8 users looking to join the next race, we simply run n concurrent races, stacking each with human users until we can't fill the next race with human racers alone, in which case we pad it out with NPC racers
    - For our PoC, though, let's just have me start races via a CLI or something like that since I'll be running everything locally
    - In the PoC and beyond, let's not worry about matchmaking too much - I don't care too much about matching racers of comparable skills in the same races
- A racer wins the race by being the first to complete three laps. As soon as each racer finishes the race, we incorporate that into the game state that we share with MCP clients so they can report the standings as they come in
- The race ends when the second-to-last player crosses the finish line (thus determining the final standings)

## Implementation

Pulling off this kart game over MCP concept will involve a lot of moving parts. I want to use Temporal heavily in this project to help me manage this complexity. And then use FastMCP for the MCP server itself.

- Let's use a monorepo approach, keeping all parts of our app here in this repo, organized into different subdirectories
- Use this `research` subdirectory to create, modify, and update your research plans for this project

### Backend implementation

I want to use Temporal heavily in this project, embracing its philosophy of keeping "business process logic" within the Temporal workflow itself. For us, that means each race and its associated game + player state data.

- Most users will use my MCP server as a remote server, but I want competitive users to be able to run it locally too. So that means this backend will need to be decoupled from the MCP server itself
- Let's use FastAPI to create the API endpoints we need to expose to our MCP server. And then Temporal to implement most of our game/business logic, invoked via the FastAPI endpoints
- As for that Temporal implementation: let's start off focusing on our main workflow, which represents a single three-lap race and all the game + player state necessary to execute that race
    - We should research this, but I'm leaning towards implementing the race as a while loop inside the Temporal workflow, using variables local to the workflow function for tracking the game state, where each iteration of the loop represents one "tick" of the game
    - When a racer's MCP client sends new input to the MCP server (e.g. to press acceleration pedal), we can use Temporal signals / updates to inject that kart input update into the workflow before the next the next tick: https://docs.temporal.io/encyclopedia/workflow-message-passing#for-write-requests
    - We don't need to worry about storing game state in Postgres or Redis - let's just rely on Temporal, especially since each race will only last a few minutes. Then when the race concludes, we can make an activity at the end of our workflow for storing the race and its results in Postgres
    - Remember that Temporal's main focus is enabling us to focus on "happy path" programming - if we're using it correctly, we shouldn't need excessive error handling code in our business logic
- We'll need to figure out what API endpoints we'll need in our FastAPI server, but I don't think it's too many: maybe just...
    - An endpoint for joining an upcoming race
    - An endpoint for retrieving the current game + player state
    - An endpoint for updating the racer's "controller" input: (e.g. "acceleration pedal", "use item", set the steering wheel left / right, etc.)
    - Perhaps additional endpoints to be used in an OAuth flow, to be implemented after the PoC
- Btw, for this and our MCP server subdirectory, be sure to use `uv` to scaffold the project. Try not to write config files by hand - instead generate them using `uv` and similar tools' `init` commands

### MCP server implementation

I want to use FastMCP to implement our MCP server: https://gofastmcp.com/getting-started/welcome.md

- Let's focus primarily on implementing it as a remote MCP server. I think only the most competitive users will care to run the MCP server locally
- To start, the MCP server primarily just needs to make requests to our backend FastAPI service, via MCP tools
- Ideally, we should implement all our features as MCP tools, not other parts of the MCP spec (like resources or prompts). Even if those abstractions would better fit a particular feature, very few MCP clients implement more than just the tools part of the MCP spec - so let's try hard to stick to that

### Frontend implementation

- Let's not worry about this too much for the PoC. I'm fine building the PoC using primarily log entries / log-based ASCII art to represent the race state
