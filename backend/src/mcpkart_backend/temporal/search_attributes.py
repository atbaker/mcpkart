"""Search attribute keys for Temporal workflow discovery.

These attributes enable querying for open public lobbies during matchmaking.
Search attributes must be registered with the Temporal cluster before use:

    temporal operator search-attribute create \
      --namespace default \
      --name IsPublic --type Bool \
      --name Phase --type Keyword \
      --name RacerCount --type Int
"""

from temporalio.common import SearchAttributeKey

# Whether this is a public matchmaking lobby (vs private invite-only)
IS_PUBLIC = SearchAttributeKey.for_bool("IsPublic")

# Current race phase: LOBBY, MATCHMAKING, PLANNING, RACING, FINISHED
PHASE = SearchAttributeKey.for_keyword("Phase")

# Number of racers currently in the lobby
RACER_COUNT = SearchAttributeKey.for_int("RacerCount")
