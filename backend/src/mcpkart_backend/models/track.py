"""Track and Tile models for MCP Kart."""

from enum import Enum
from pydantic import BaseModel


class TileType(str, Enum):
    """Type of track tile."""

    STRAIGHT = "straight"
    TURN_LEFT = "turn_left"


class Tile(BaseModel):
    """A single tile on the track."""

    index: int
    tile_type: TileType
    has_item_box: bool = False


class Track(BaseModel):
    """The race track, composed of tiles in a loop."""

    tiles: list[Tile]

    @property
    def total_tiles(self) -> int:
        """Total number of tiles in the track."""
        return len(self.tiles)

    @classmethod
    def create_oval(cls) -> "Track":
        """Create the PoC oval track: 20 tiles, 4 turns, 4 item boxes.

        Layout:
        - Tiles 0-3: straight (item box at 0)
        - Tile 4: turn_left
        - Tiles 5-8: straight (item box at 5)
        - Tile 9: turn_left
        - Tiles 10-13: straight (item box at 10)
        - Tile 14: turn_left
        - Tiles 15-18: straight (item box at 15)
        - Tile 19: turn_left
        """
        tiles = []
        turn_indices = {4, 9, 14, 19}
        item_box_indices = {0, 5, 10, 15}

        for i in range(20):
            tile_type = TileType.TURN_LEFT if i in turn_indices else TileType.STRAIGHT
            has_item_box = i in item_box_indices
            tiles.append(Tile(index=i, tile_type=tile_type, has_item_box=has_item_box))

        return cls(tiles=tiles)
