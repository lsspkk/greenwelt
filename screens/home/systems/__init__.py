# Home-specific ECS systems
import esper
import pygame
from shared.components import Position, DotRenderable, RectangleRenderable
from screens.home.components import HomeBackground, InteractableObject


class HomeRenderSystem(esper.Processor):
    """Renders the home interior and entities"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def process(self, dt: float):
        # Draw background first
        for ent, (bg,) in esper.get_components(HomeBackground):
            if bg.image is not None:
                self.screen.blit(bg.image, (0, 0))
            else:
                self.screen.fill((30, 25, 20))  # Warm interior color

        # Draw interactable objects
        for ent, (pos, rect, obj) in esper.get_components(Position, RectangleRenderable, InteractableObject):
            color = rect.color
            if obj.is_highlighted:
                # Brighter color when highlighted
                color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))

            draw_rect = pygame.Rect(int(pos.x), int(pos.y), rect.width, rect.height)
            pygame.draw.rect(self.screen, color, draw_rect, border_radius=8)

        # Draw player
        for ent, (pos, dot) in esper.get_components(Position, DotRenderable):
            pygame.draw.circle(
                self.screen,
                dot.color,
                (int(pos.x), int(pos.y)),
                dot.radius
            )


class InteractionSystem(esper.Processor):
    """Handles player proximity to interactable objects"""

    def __init__(self, interaction_distance: float = 120.0):
        self.interaction_distance = interaction_distance
        self.nearby_object = None  # Entity ID of nearest interactable

    def process(self, dt: float):
        # Find player position
        player_pos = None
        for ent, (pos, dot) in esper.get_components(Position, DotRenderable):
            player_pos = pos
            break

        if player_pos is None:
            return

        # Reset all highlights and find nearest
        nearest_ent = None
        nearest_dist = float('inf')

        for ent, (pos, obj) in esper.get_components(Position, InteractableObject):
            obj.is_highlighted = False

            dx = pos.x - player_pos.x
            dy = pos.y - player_pos.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < self.interaction_distance and dist < nearest_dist:
                nearest_dist = dist
                nearest_ent = ent

        # Highlight nearest
        if nearest_ent is not None:
            obj = esper.component_for_entity(nearest_ent, InteractableObject)
            obj.is_highlighted = True

        self.nearby_object = nearest_ent
