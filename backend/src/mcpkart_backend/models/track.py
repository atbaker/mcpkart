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
        """Create the oblong oval track: 44 tiles, 4 turns, 3 item boxes.

        Layout (start at tile 0, centered in first long straightaway):
        - Tiles 38-43, 0-6: long straight (13 tiles, start/finish at 0)
        - Tile 7: turn_left
        - Tiles 8-14: short straight (7 tiles, item box at 11)
        - Tile 15: turn_left
        - Tiles 16-28: long straight (13 tiles, item box at 22)
        - Tile 29: turn_left
        - Tiles 30-36: short straight (7 tiles, item box at 33)
        - Tile 37: turn_left
        """
        tiles = []
        turn_indices = {7, 15, 29, 37}
        item_box_indices = {11, 22, 33}

        for i in range(44):
            tile_type = TileType.TURN_LEFT if i in turn_indices else TileType.STRAIGHT
            has_item_box = i in item_box_indices
            tiles.append(Tile(index=i, tile_type=tile_type, has_item_box=has_item_box))

        return cls(tiles=tiles)
