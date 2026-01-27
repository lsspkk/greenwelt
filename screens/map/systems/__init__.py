# Map-specific ECS systems
import esper
import pygame
from shared.components import Position, Velocity, DotRenderable, RectangleRenderable
from screens.map.components import MapBackground, RoadLayer, PlayerOnMap


class MapRenderSystem(esper.Processor):
    """Renders the map background and entities"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def process(self, dt: float):
        # Fill background first (in case image doesn't cover full screen)
        self.screen.fill((16, 22, 30))

        # Draw map background image centered
        for ent, (bg,) in esper.get_components(MapBackground):
            if bg.image is not None:
                screen_w, screen_h = self.screen.get_size()
                draw_x = (0 - bg.camera_pos_x) * bg.zoom + screen_w // 2
                draw_y = (0 - bg.camera_pos_y) * bg.zoom + screen_h // 2

                self.screen.blit(bg.image, (draw_x, draw_y))

        # Draw roads on top of background
        for ent, (road,) in esper.get_components(RoadLayer):
            if road.road_surface is not None:

                scaled_road_surface = pygame.transform.smoothscale(
                    road.road_surface,
                    (int(road.road_surface.get_width() * bg.zoom),
                     int(road.road_surface.get_height() * bg.zoom))
                )
                draw_x = (0 - bg.camera_pos_x) * bg.zoom + screen_w // 2
                draw_y = (0 - bg.camera_pos_y) * bg.zoom + screen_h // 2
                self.screen.blit(scaled_road_surface, (draw_x, draw_y))

        # Draw rectangles
        for ent, (pos, rect) in esper.get_components(Position, RectangleRenderable):
            draw_rect = pygame.Rect(int(pos.x), int(
                pos.y), rect.width, rect.height)
            pygame.draw.rect(self.screen, rect.color,
                             draw_rect, border_radius=16)

        # Draw dots (player, markers)
        for ent, (pos, dot) in esper.get_components(Position, DotRenderable):
            # Transform world position to screen position
            screen_x = int((pos.x - bg.camera_pos_x) * bg.zoom + screen_w // 2)
            screen_y = int((pos.y - bg.camera_pos_y) * bg.zoom + screen_h // 2)
            radius = int(dot.radius * bg.zoom)
            pygame.draw.circle(
                self.screen,
                dot.color,
                (screen_x, screen_y),
                radius
            )


class RoadCollisionSystem(esper.Processor):
    """Prevents entities from moving off roads"""

    def process(self, dt: float):
        # Get road layer
        road_layer = None
        for ent, (road,) in esper.get_components(RoadLayer):
            road_layer = road
            break

        if road_layer is None or road_layer.road_mask is None:
            return

        # Check player movement against roads
        for ent, (pos, vel, player) in esper.get_components(Position, Velocity, PlayerOnMap):
            if vel.vx == 0.0 and vel.vy == 0.0:
                continue

            # Calculate next position
            next_x = pos.x + vel.vx * dt
            next_y = pos.y + vel.vy * dt

            # Check if next position is on a road
            if not road_layer.is_on_road(next_x, next_y):
                # Stop movement
                vel.vx = 0.0
                vel.vy = 0.0
