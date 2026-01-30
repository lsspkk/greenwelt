# Map-specific ECS components

from dataclasses import dataclass
from typing import List
import pygame


@dataclass
class MapBackground:
    """Background image for a map"""
    image_path: str = ""
    image: pygame.Surface = None  # Loaded at runtime


@dataclass
class RoadLayer:
    """Road data for a map - stores strokes and a walkable mask"""
    strokes: List = None  # List of {points: [(x,y),...], width: int}
    road_surface: pygame.Surface = None  # Rendered roads for display
    road_mask: pygame.Surface = None  # Binary mask for collision
    color: tuple = (100, 100, 100)
    alpha: int = 180

    def is_on_road(self, world_x: float, world_y: float) -> bool:
        """Check if a world position is on a road"""
        if self.road_mask is None:
            return True  # No roads = can walk anywhere

        # Convert to int for pixel lookup
        mask_x = int(world_x)
        mask_y = int(world_y)

        # Check bounds
        if mask_x < 0 or mask_y < 0:
            return False
        if mask_x >= self.road_mask.get_width():
            return False
        if mask_y >= self.road_mask.get_height():
            return False

        # Check if pixel is white (road) or black (not road)
        pixel = self.road_mask.get_at((mask_x, mask_y))
        return pixel[0] > 128  # Check red channel


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


@dataclass
class GreeneryLayer:
    """Green overlay that covers white areas of the map (not roads)"""
    surface: pygame.Surface = None  # The greenery surface with current opacity


@dataclass
class Camera:
    """Camera for viewing the map with zoom"""
    # Camera center position in world coordinates
    x: float = 0.0
    y: float = 0.0
    zoom: float = 2.0
    # Screen dimensions (set at runtime)
    screen_width: int = 1920
    screen_height: int = 1080

    def world_to_screen(self, world_x: float, world_y: float) -> tuple:
        """Convert world coordinates to screen coordinates"""
        screen_center_x = self.screen_width // 2
        screen_center_y = self.screen_height // 2

        screen_x = (world_x - self.x) * self.zoom + screen_center_x
        screen_y = (world_y - self.y) * self.zoom + screen_center_y

        return (int(screen_x), int(screen_y))

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple:
        """Convert screen coordinates to world coordinates"""
        screen_center_x = self.screen_width // 2
        screen_center_y = self.screen_height // 2

        world_x = (screen_x - screen_center_x) / self.zoom + self.x
        world_y = (screen_y - screen_center_y) / self.zoom + self.y

        return (world_x, world_y)
