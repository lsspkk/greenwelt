"""
Greenery System for Map

This system creates green patches on the map at delivery locations.
The map starts completely white (neutral) and gets greener as orders are delivered.

How it works:
1. A white surface is created the same size as the map
2. When an order is delivered, 5-10 green triangles are drawn
   near the delivery location
3. Triangles have random sizes (20 to 80 pixels) and rotations
4. Triangles are placed randomly within ~100 pixels of the location
5. White "cheese holes" are drawn on top of each triangle
6. The greenery surface is blitted on top of the map with BLEND_RGB_MULT
7. More deliveries = more green patches = greener map

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
        # Each patch is a list of triangle data tuples
        self.patches: List[List[Tuple[int, int, int, float]]] = []

        # Green color for the patches
        # Lower values = darker/more saturated green tint
        self.green_color = (180, 255, 180)

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
        Draws 5-10 triangles randomly placed near the location.
        Each triangle has white cheese-like holes on top.
        """
        if self.greenery_surface is None:
            return

        # Decide how many triangles to draw
        num_triangles = random.randint(10, 15)

        patch_shapes = []

        for i in range(num_triangles):
            # Random offset from location center (-200 to +200 pixels)
            offset_x = random.randint(-200, 200)
            offset_y = random.randint(-200, 200)

            center_x = int(location_x + offset_x)
            center_y = int(location_y + offset_y)

            # Random size for the triangle (60 to 140 pixels)
            size = random.randint(60, 140)

            # Random rotation angle (0 to 360 degrees)
            rotation = random.uniform(0, 2 * math.pi)

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
            patch_shapes.append((center_x, center_y, size, rotation))

            # Draw the triangle on the greenery surface
            self._draw_triangle(center_x, center_y, size, rotation)

            # Draw cheese holes on top
            self._draw_cheese_holes(center_x, center_y, size)

        # Store this patch for potential future use
        self.patches.append(patch_shapes)

    def _draw_triangle(self, center_x: int, center_y: int, size: int, rotation: float):
        """
        Draw a single green triangle on the greenery surface.
        Uses multiply blending so overlapping triangles get darker.
        """
        if self.greenery_surface is None:
            return

        # Calculate the three vertices of the triangle
        # Start with an equilateral triangle pointing up, then rotate
        vertices = []

        for i in range(3):
            # Angle for each vertex (120 degrees apart)
            angle = rotation + (i * 2 * math.pi / 3)

            # Calculate vertex position
            vx = center_x + size * math.cos(angle)
            vy = center_y + size * math.sin(angle)

            vertices.append((int(vx), int(vy)))

        # Find bounding box of the triangle
        min_x = min(v[0] for v in vertices)
        max_x = max(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_y = max(v[1] for v in vertices)

        # Add padding to avoid edge clipping
        padding = 2
        min_x = min_x - padding
        min_y = min_y - padding
        max_x = max_x + padding
        max_y = max_y + padding

        # Calculate temp surface size
        temp_width = max_x - min_x
        temp_height = max_y - min_y

        if temp_width <= 0 or temp_height <= 0:
            return

        # Create temp surface filled with white (neutral for multiply)
        temp_surface = pygame.Surface((temp_width, temp_height))
        temp_surface.fill((255, 255, 255))

        # Translate vertices to temp surface coordinates
        local_vertices = []
        for vx, vy in vertices:
            local_vertices.append((vx - min_x, vy - min_y))

        # Random green shade for variety (darker = more saturated)
        green_variation = random.randint(-30, 30)
        r = max(0, min(255, self.green_color[0] + green_variation))
        g = self.green_color[1]  # Keep green channel bright
        b = max(0, min(255, self.green_color[2] + green_variation))
        varied_green = (r, g, b)

        # Draw filled triangle on temp surface
        pygame.draw.polygon(temp_surface, varied_green, local_vertices)

        # Blit temp surface onto main surface with multiply blend
        # Overlapping areas will multiply together = darker green
        self.greenery_surface.blit(
            temp_surface,
            (min_x, min_y),
            special_flags=pygame.BLEND_RGB_MULT
        )

    def _draw_cheese_holes(self, center_x: int, center_y: int, size: int):
        """Draw white cheese-like holes on top of a triangle."""
        if self.greenery_surface is None:
            return

        # yellow color for the holes
        yellow_color = (255, 205, 40)
        red_color = (255, 40, 40)

        colors: List[Tuple[int, int, int]] = [yellow_color, red_color]

        for color in colors:
            # Number of holes depends on triangle size
            # Smaller triangles get fewer holes
            if size < 50:
                num_holes = 7
            elif size < 100:
                num_holes = 12
            else:
                num_holes = 20

            # Draw random holes within the triangle area
            for j in range(num_holes):
                # Random offset from center (within triangle bounds)
                max_offset = int(size * 0.5)
                hole_offset_x = random.randint(-max_offset, max_offset)
                hole_offset_y = random.randint(-max_offset, max_offset)

                hole_x = center_x + hole_offset_x
                hole_y = center_y + hole_offset_y

                # Random hole radius (smaller than the triangle)
                hole_radius = random.randint(2, 8)

                # Draw the white hole
                pygame.draw.circle(self.greenery_surface,
                                   color, (hole_x, hole_y), hole_radius)

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
            scaled_greenery = pygame.transform.scale(
                visible_greenery, (dest_w, dest_h))
        else:
            scaled_greenery = visible_greenery

        # Calculate destination position
        dest_x = int(-((camera_x - src_x) * zoom))
        dest_y = int(-((camera_y - src_y) * zoom))

        # Blit with multiply blend
        target_surface.blit(scaled_greenery, (dest_x, dest_y),
                            special_flags=pygame.BLEND_RGB_MULT)

    def apply_road_mask(self, road_mask: pygame.Surface):
        """
        Apply road mask to keep roads white (unaffected by greenery).

        The road mask is white where roads are, black elsewhere.
        We use BLEND_RGB_MAX to make road areas white on the greenery surface,
        so roads won't get the green tint from the multiply blend.
        """
        if self.greenery_surface is None:
            return

        if road_mask is None:
            return

        # BLEND_RGB_MAX takes the maximum of each color channel
        # Road mask is white (255,255,255) where roads are
        # This makes road areas white on greenery surface, keeping them neutral
        self.greenery_surface.blit(
            road_mask, (0, 0), special_flags=pygame.BLEND_RGB_MAX)

    def get_patch_count(self) -> int:
        """Get the number of delivery locations that have been greened."""
        return len(self.patches)

    def get_surface(self) -> Optional[pygame.Surface]:
        """Get the greenery surface (for custom rendering if needed)."""
        return self.greenery_surface
