# Map-specific ECS components
from dataclasses import dataclass
from typing import List
import pygame


@dataclass
class MapBackground:
    """Background image for a map"""
    image_path: str = ""
    image: pygame.Surface = None  # Loaded at runtime
    offset_x: int = 0  # For centering non-fullscreen images
    offset_y: int = 0


@dataclass
class CollisionLayer:
    """Collision data for a map - stores walkable/blocked areas"""
    # The collision map is a 2D grid where:
    # 0 = walkable
    # 1 = blocked
    grid: List[List[int]] = None
    tile_width: int = 64
    tile_height: int = 64

    def is_walkable(self, x: float, y: float) -> bool:
        """Check if a world position is walkable"""
        if self.grid is None:
            return True

        tile_x = int(x / self.tile_width)
        tile_y = int(y / self.tile_height)

        # Out of bounds is not walkable
        if tile_y < 0 or tile_y >= len(self.grid):
            return False
        if tile_x < 0 or tile_x >= len(self.grid[tile_y]):
            return False

        return self.grid[tile_y][tile_x] == 0


@dataclass
class MapMarker:
    """A point of interest on the map (city, location, etc.)"""
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    marker_type: str = "city"  # city, village, landmark, etc.


@dataclass
class PlayerOnMap:
    """Tag component to identify the player entity on the map"""
    pass
