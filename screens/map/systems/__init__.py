# Map-specific ECS systems
import esper
import pygame
from shared.components import Position, Velocity, DotRenderable, RectangleRenderable
from screens.map.components import MapBackground, CollisionLayer, PlayerOnMap


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
                self.screen.blit(bg.image, (bg.offset_x, bg.offset_y))

        # Draw rectangles
        for ent, (pos, rect) in esper.get_components(Position, RectangleRenderable):
            draw_rect = pygame.Rect(int(pos.x), int(pos.y), rect.width, rect.height)
            pygame.draw.rect(self.screen, rect.color, draw_rect, border_radius=16)

        # Draw dots (player, markers)
        for ent, (pos, dot) in esper.get_components(Position, DotRenderable):
            pygame.draw.circle(
                self.screen,
                dot.color,
                (int(pos.x), int(pos.y)),
                dot.radius
            )


class CollisionSystem(esper.Processor):
    """Prevents entities from moving into blocked areas"""

    def process(self, dt: float):
        # Get collision layer
        collision_layer = None
        for ent, (col,) in esper.get_components(CollisionLayer):
            collision_layer = col
            break

        if collision_layer is None:
            return

        # Check player movement against collision
        for ent, (pos, vel, player) in esper.get_components(Position, Velocity, PlayerOnMap):
            # Calculate next position
            next_x = pos.x + vel.vx * dt
            next_y = pos.y + vel.vy * dt

            # Check if next position is walkable
            if not collision_layer.is_walkable(next_x, next_y):
                # Stop movement
                vel.vx = 0.0
                vel.vy = 0.0
