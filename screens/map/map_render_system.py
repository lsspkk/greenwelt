# Map rendering system with camera zoom

import esper
import pygame
from shared.components import Position, DotRenderable
from screens.map.components import MapBackground, RoadLayer, Camera


class MapRenderSystem(esper.Processor):
    """Renders the map background and entities with camera zoom"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def process(self, dt: float):
        # Fill background first
        self.screen.fill((16, 22, 30))

        # Get camera
        camera = None
        for ent, (cam,) in esper.get_components(Camera):
            camera = cam
            break

        if camera is None:
            return

        # Get map background
        bg_image = None
        for ent, (bg,) in esper.get_components(MapBackground):
            bg_image = bg.image
            break

        # Get road surface
        road_surface = None
        for ent, (road,) in esper.get_components(RoadLayer):
            road_surface = road.road_surface
            break

        # Calculate what part of the world is visible
        half_screen_w = camera.screen_width // 2
        half_screen_h = camera.screen_height // 2
        view_width = camera.screen_width / camera.zoom
        view_height = camera.screen_height / camera.zoom

        # World coordinates of the top-left corner of the view
        view_left = camera.x - view_width / 2
        view_top = camera.y - view_height / 2

        # Draw map background with zoom
        if bg_image is not None:
            self._draw_zoomed_surface(bg_image, camera, view_left, view_top)

        # Draw roads on top
        if road_surface is not None:
            self._draw_zoomed_surface(road_surface, camera, view_left, view_top)

        # Draw dots (player, markers)
        for ent, (pos, dot) in esper.get_components(Position, DotRenderable):
            screen_x, screen_y = camera.world_to_screen(pos.x, pos.y)
            scaled_radius = int(dot.radius * camera.zoom)
            pygame.draw.circle(
                self.screen,
                dot.color,
                (screen_x, screen_y),
                scaled_radius
            )

    def _draw_zoomed_surface(self, surface: pygame.Surface, camera: Camera,
                              view_left: float, view_top: float):
        """Draw a surface with camera zoom and offset"""
        surf_w = surface.get_width()
        surf_h = surface.get_height()

        # Calculate the source rect (what part of the surface to draw)
        # Clamp to surface bounds
        src_left = max(0, int(view_left))
        src_top = max(0, int(view_top))
        src_right = min(surf_w, int(view_left + camera.screen_width / camera.zoom))
        src_bottom = min(surf_h, int(view_top + camera.screen_height / camera.zoom))

        src_width = src_right - src_left
        src_height = src_bottom - src_top

        if src_width <= 0 or src_height <= 0:
            return

        # Create source rect
        src_rect = pygame.Rect(src_left, src_top, src_width, src_height)

        # Extract the visible portion
        visible_portion = surface.subsurface(src_rect)

        # Scale it up by zoom factor
        scaled_width = int(src_width * camera.zoom)
        scaled_height = int(src_height * camera.zoom)
        scaled_surface = pygame.transform.scale(visible_portion, (scaled_width, scaled_height))

        # Calculate where to draw on screen
        # The offset from screen edge depends on how much of the map is off-screen
        dest_x = int((src_left - view_left) * camera.zoom)
        dest_y = int((src_top - view_top) * camera.zoom)

        self.screen.blit(scaled_surface, (dest_x, dest_y))
