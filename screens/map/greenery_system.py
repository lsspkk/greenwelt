"""
Greenery System for Map

This system creates green patches on the map at delivery locations.
The map starts completely white (neutral) and gets greener as orders are delivered.

How it works:
1. A white surface is created the same size as the map
2. When an order is delivered, 5-10 green circles/ellipses are drawn
   near the delivery location
3. Circle radii range from 10 to 70 pixels
4. Circles are placed randomly within ~100 pixels of the location
5. The greenery surface is blitted on top of the map with BLEND_RGB_MULT
6. More deliveries = more green patches = greener map

The multiply blend effect:
- White (255,255,255) = neutral, no change to map colors
- Green tint = darkens red/blue channels, keeps green bright
- This creates natural-looking green patches over the map

Usage:
    greenery = GreenerySystem()
    greenery.initialize(map_width, map_height)

    # When order is delivered:
    greenery.add_greenery_at_location(x, y)

    # In render loop:
    greenery.render(surface, camera_x, camera_y, zoom)
"""

import pygame
import random
import math
from typing import Optional, List, Tuple


class GreenerySystem:
    """
    Manages green patches that appear on the map at delivery locations.
    Starts white (neutral) and gets greener with each delivery.
    """

    def __init__(self):
        # The greenery overlay surface
        self.greenery_surface: Optional[pygame.Surface] = None

        # Map dimensions
        self.map_width = 0
        self.map_height = 0

        # List of all green patches added
        # Each patch is a list of (x, y, radius_x, radius_y) tuples
        self.patches: List[List[Tuple[int, int, int, int]]] = []

        # Green color for the patches
        # Lower values = darker/more saturated green tint
        self.green_color = (140, 255, 140)

    def initialize(self, map_width: int, map_height: int):
        """
        Initialize the greenery surface with map dimensions.
        Call this after the map is loaded. Resets to white (no greenery).
        """
        self.map_width = map_width
        self.map_height = map_height

        # Create the greenery surface filled with white (neutral for multiply)
        self.greenery_surface = pygame.Surface((map_width, map_height))
        self.greenery_surface.fill((255, 255, 255))

        # Clear all patches
        self.patches = []

    def add_greenery_at_location(self, location_x: float, location_y: float):
        """
        Add green patches near a delivery location.
        Draws 5-10 circles/ellipses randomly placed near the location.
        """
        if self.greenery_surface is None:
            return

        # Decide how many circles to draw (5 to 10)
        num_circles = random.randint(5, 10)

        patch_shapes = []

        for i in range(num_circles):
            # Random offset from location center (-100 to +100 pixels)
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)

            center_x = int(location_x + offset_x)
            center_y = int(location_y + offset_y)

            # Random radius (10 to 70)
            radius_x = random.randint(10, 70)
            radius_y = random.randint(10, 70)

            # Clamp to map bounds
            if center_x < 0:
                center_x = 0
            if center_y < 0:
                center_y = 0
            if center_x >= self.map_width:
                center_x = self.map_width - 1
            if center_y >= self.map_height:
                center_y = self.map_height - 1

            # Store the shape data
            patch_shapes.append((center_x, center_y, radius_x, radius_y))

            # Draw the ellipse on the greenery surface
            self._draw_ellipse(center_x, center_y, radius_x, radius_y)

        # Store this patch for potential future use
        self.patches.append(patch_shapes)

    def _draw_ellipse(self, center_x: int, center_y: int, radius_x: int, radius_y: int):
        """Draw a single green ellipse on the greenery surface."""
        if self.greenery_surface is None:
            return

        # Calculate bounding rect for the ellipse
        left = center_x - radius_x
        top = center_y - radius_y
        width = radius_x * 2
        height = radius_y * 2

        rect = pygame.Rect(left, top, width, height)

        # Draw filled ellipse
        pygame.draw.ellipse(self.greenery_surface, self.green_color, rect)

    def render(self, target_surface: pygame.Surface, camera_x: float, camera_y: float, zoom: float):
        """
        Render the greenery overlay onto the target surface.

        This should be called AFTER the map is rendered but BEFORE
        other elements (player, UI, etc).

        Uses BLEND_RGB_MULT for multiply effect.
        """
        if self.greenery_surface is None:
            return

        # Calculate the visible portion of the greenery based on camera
        screen_width = target_surface.get_width()
        screen_height = target_surface.get_height()

        # Source rectangle (what part of greenery to draw)
        src_x = int(camera_x)
        src_y = int(camera_y)
        src_w = int(screen_width / zoom)
        src_h = int(screen_height / zoom)

        # Clamp to greenery surface bounds
        if src_x < 0:
            src_x = 0
        if src_y < 0:
            src_y = 0
        if src_x + src_w > self.map_width:
            src_w = self.map_width - src_x
        if src_y + src_h > self.map_height:
            src_h = self.map_height - src_y

        if src_w <= 0 or src_h <= 0:
            return

        # Extract the visible portion
        src_rect = pygame.Rect(src_x, src_y, src_w, src_h)
        visible_greenery = self.greenery_surface.subsurface(src_rect)

        # Scale if zoomed
        if zoom != 1.0:
            dest_w = int(src_w * zoom)
            dest_h = int(src_h * zoom)
            scaled_greenery = pygame.transform.scale(visible_greenery, (dest_w, dest_h))
        else:
            scaled_greenery = visible_greenery

        # Calculate destination position
        dest_x = int(-((camera_x - src_x) * zoom))
        dest_y = int(-((camera_y - src_y) * zoom))

        # Blit with multiply blend
        target_surface.blit(scaled_greenery, (dest_x, dest_y), special_flags=pygame.BLEND_RGB_MULT)

    def get_patch_count(self) -> int:
        """Get the number of delivery locations that have been greened."""
        return len(self.patches)

    def get_surface(self) -> Optional[pygame.Surface]:
        """Get the greenery surface (for custom rendering if needed)."""
        return self.greenery_surface
