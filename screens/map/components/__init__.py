# Map-specific ECS components

from dataclasses import dataclass
from typing import List
import pygame
from shared.debug.debug_log import debug


@dataclass
class MapBackground:
    """Background image for a map"""
    image_path: str = ""
    image: pygame.Surface = None  # Loaded at runtime
    offset_x: int = 0  # For centering non-fullscreen images
    offset_y: int = 0
    zoom: float = 2.0
    camera_pos_x: int = 0
    camera_pos_y: int = 0


@dataclass
class RoadLayer:
    """Road data for a map - stores strokes and a walkable mask"""
    strokes: List = None  # List of {points: [(x,y),...], width: int}
    road_surface: pygame.Surface = None  # Rendered roads for display
    road_mask: pygame.Surface = None  # Binary mask for collision
    color: tuple = (100, 100, 100)
    alpha: int = 180
    offset_x: int = 0
    offset_y: int = 0
    zoom: float = 2.0
    camera_pos_x: int = 0
    camera_pos_y: int = 0

    def is_on_road(self, x: float, y: float) -> bool:
        """Check if a position is on a road, with debug logging"""
        debug.debug(
            f"is_on_road check: input=({x:.2f}, {y:.2f}) offset=({self.offset_x}, {self.offset_y})")
        if self.road_mask is None:
            debug.debug(
                "road_mask is None: returning True (no roads, can walk anywhere)")
            return True  # No roads = can walk anywhere

        # Adjust for map offset
        mask_x = int(x - self.offset_x)
        mask_y = int(y - self.offset_y)
        debug.debug(f"Adjusted mask coords: ({mask_x}, {mask_y})")

        # Check bounds
        if mask_x < 0 or mask_y < 0:
            debug.debug("Out of bounds (negative): returning False")
            return False
        if mask_x >= self.road_mask.get_width():
            debug.debug(
                f"Out of bounds (mask_x >= width): {mask_x} >= {self.road_mask.get_width()}")
            return False
        if mask_y >= self.road_mask.get_height():
            debug.debug(
                f"Out of bounds (mask_y >= height): {mask_y} >= {self.road_mask.get_height()}")
            return False

        # Check if pixel is white (road) or black (not road)
        pixel = self.road_mask.get_at((mask_x, mask_y))
        on_road = pixel[0] > 128  # Check red channel
        debug.debug(
            f"Pixel at ({mask_x}, {mask_y}) = {pixel}, on_road={on_road}")
        return on_road


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
