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
        """Create the PoC oval track: 20 tiles, 4 turns, 3 item boxes.

        Layout (start at tile 0, centered in straightaway):
        - Tiles 18, 19, 0, 1: straight (no item at start)
        - Tile 2: turn_left
        - Tiles 3, 4, 5, 6: straight (item box at 5)
        - Tile 7: turn_left
        - Tiles 8, 9, 10, 11: straight (item box at 10)
        - Tile 12: turn_left
        - Tiles 13, 14, 15, 16: straight (item box at 15)
        - Tile 17: turn_left
        """
        tiles = []
        turn_indices = {2, 7, 12, 17}
        item_box_indices = {5, 10, 15}

        for i in range(20):
            tile_type = TileType.TURN_LEFT if i in turn_indices else TileType.STRAIGHT
            has_item_box = i in item_box_indices
            tiles.append(Tile(index=i, tile_type=tile_type, has_item_box=has_item_box))

        return cls(tiles=tiles)
