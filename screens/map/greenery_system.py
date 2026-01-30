"""
Greenery System for Map

This system creates a green tint overlay that darkens the entire map.
The green tint intensity decreases as orders are completed.

How it works:
1. A solid green surface is created the same size as the map
2. The green overlay is blitted on top of the map with BLEND_RGB_MULT
3. This creates a "multiply" effect where:
   - Black stays black
   - White becomes green
   - Gray becomes darker green
   - All colors get a green tint
4. The intensity decreases as orders are completed:
   - 0 orders completed = full green tint
   - All orders completed = no green tint (original map colors)

The formula: intensity = 1 - (completed_orders / total_orders)

This creates a visual representation of the city being "overgrown" with plants
that clears up as the player delivers more orders.

Usage:
    greenery = GreenerySystem(order_manager)
    greenery.initialize(map_width, map_height)
    # In render loop:
    greenery.update()
    greenery.render(surface, camera_x, camera_y, zoom)
"""

import pygame
from typing import Optional


class GreenerySystem:
    """
    Manages the green tint overlay that darkens the entire map.
    The tint fades as orders are completed.
    """

    def __init__(self, order_manager, total_orders: int = 20):
        self.order_manager = order_manager
        self.total_orders = total_orders

        # The greenery overlay surface
        self.greenery_surface: Optional[pygame.Surface] = None

        # Map dimensions
        self.map_width = 0
        self.map_height = 0

        # Current intensity (0.0 to 1.0)
        # 1.0 = full green tint, 0.0 = no tint
        self.current_intensity = 1.0

        # Green color for the tint
        # This is the color that will be multiplied with the map
        # Values closer to 255 mean less darkening for that channel
        # Lower green value = more green tint
        self.base_green_color = (180, 255, 180)  # Light green tint

        # Cached color based on intensity
        self.current_color = self.base_green_color

    def initialize(self, map_width: int, map_height: int):
        """
        Initialize the greenery surface with map dimensions.
        Call this after the map is loaded.
        """
        self.map_width = map_width
        self.map_height = map_height

        # Create the greenery surface (no alpha needed for multiply blend)
        self.greenery_surface = pygame.Surface((map_width, map_height))
        self.greenery_surface.fill(self.base_green_color)

        # Update with initial intensity
        self._update_color()

    def _update_color(self):
        """
        Update the greenery surface color based on current intensity.

        At intensity 1.0: use base_green_color (greenish tint)
        At intensity 0.0: use (255, 255, 255) which is neutral in multiply blend
        """
        if self.greenery_surface is None:
            return

        # Interpolate between white (neutral) and green tint based on intensity
        base_r, base_g, base_b = self.base_green_color

        # Calculate color: lerp from (255,255,255) to base_green_color
        r = int(255 - (255 - base_r) * self.current_intensity)
        g = int(255 - (255 - base_g) * self.current_intensity)
        b = int(255 - (255 - base_b) * self.current_intensity)

        self.current_color = (r, g, b)
        self.greenery_surface.fill(self.current_color)

    def update(self):
        """
        Update the greenery intensity based on completed orders.
        Call this each frame or when orders change.
        """
        if self.order_manager is None:
            return

        completed = self.order_manager.orders_completed_count

        if self.total_orders <= 0:
            new_intensity = 0.0
        else:
            progress = completed / self.total_orders
            progress = min(1.0, progress)  # Cap at 1.0
            new_intensity = 1.0 - progress

        # Only update if intensity changed significantly
        if abs(new_intensity - self.current_intensity) > 0.001:
            self.current_intensity = new_intensity
            self._update_color()

    def render(self, target_surface: pygame.Surface, camera_x: float, camera_y: float, zoom: float):
        """
        Render the greenery overlay onto the target surface.

        This should be called AFTER the map is rendered but BEFORE
        other elements (player, UI, etc).

        Uses BLEND_RGB_MULT for multiply effect:
        - Black stays black
        - White becomes the overlay color
        - Colors in between are darkened/tinted
        """
        if self.greenery_surface is None:
            return

        # Skip if no tint (intensity is 0)
        if self.current_intensity < 0.001:
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

    def get_surface(self) -> Optional[pygame.Surface]:
        """Get the greenery surface (for custom rendering if needed)."""
        return self.greenery_surface

    def get_intensity(self) -> float:
        """Get the current intensity (0.0 to 1.0)."""
        return self.current_intensity

    def get_progress_percent(self) -> float:
        """Get the greenery removal progress as a percentage (0-100)."""
        if self.order_manager is None:
            return 0.0

        completed = self.order_manager.orders_completed_count
        if self.total_orders <= 0:
            return 100.0

        return (completed / self.total_orders) * 100

    def set_intensity(self, intensity: float):
        """Manually set the intensity (for testing/debugging)."""
        self.current_intensity = max(0.0, min(1.0, intensity))
        self._update_color()
