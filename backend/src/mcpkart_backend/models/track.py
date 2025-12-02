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
        """Create the oblong oval track: 40 tiles, 4 turns, 3 item boxes.

        Layout (start at tile 0, centered in first long straightaway):
        - Tiles 34-39, 0-5: long straight (12 tiles, item box at 3)
        - Tile 6: turn_left
        - Tiles 7-12: short straight (6 tiles, item box at 10)
        - Tile 13: turn_left
        - Tiles 14-25: long straight (12 tiles, item box at 20)
        - Tile 26: turn_left
        - Tiles 27-32: short straight (6 tiles)
        - Tile 33: turn_left
        """
        tiles = []
        turn_indices = {6, 13, 26, 33}
        item_box_indices = {3, 10, 20}

        for i in range(40):
            tile_type = TileType.TURN_LEFT if i in turn_indices else TileType.STRAIGHT
            has_item_box = i in item_box_indices
            tiles.append(Tile(index=i, tile_type=tile_type, has_item_box=has_item_box))

        return cls(tiles=tiles)
