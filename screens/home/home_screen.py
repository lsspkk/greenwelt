# Home screen - top-down interior view
import pygame
import esper
from typing import Optional

from shared.components import Position, Velocity, DotRenderable, RectangleRenderable
from shared.systems import MovementSystem
from screens.home.components import HomeBackground, InteractableObject, NPC, PlayerInHome
from screens.home.systems import HomeRenderSystem, InteractionSystem


class HomeScreen:
    """Top-down interior/home screen"""

    def __init__(self, screen: pygame.Surface, home_name: str = "default"):
        self.screen = screen
        self.home_name = home_name
        self.world_name = f"home_{home_name}"
        self.player_entity = None
        self.home_entity = None
        self.interaction_system = None
        self.is_initialized = False

    def initialize(self):
        """Set up the ECS world for this home"""
        esper.switch_world(self.world_name)
        esper.clear_database()

        # Add systems
        self.interaction_system = InteractionSystem()
        esper.add_processor(self.interaction_system, priority=3)
        esper.add_processor(MovementSystem(), priority=2)
        esper.add_processor(HomeRenderSystem(self.screen), priority=1)

        # Create home entity with background
        self.home_entity = esper.create_entity(
            HomeBackground()
        )

        # Create player entity (sized for 1920x1080)
        self.player_entity = esper.create_entity(
            Position(400.0, 400.0),
            Velocity(0.0, 0.0),
            DotRenderable(radius=24, color=(200, 240, 200)),
            PlayerInHome()
        )

        self.is_initialized = True

    def load_background(self, image_path: str):
        """Load the background image for this home"""
        try:
            image = pygame.image.load(image_path).convert()
            bg = esper.component_for_entity(self.home_entity, HomeBackground)
            bg.image_path = image_path
            bg.image = image
        except Exception as e:
            print(f"Failed to load home background: {e}")

    def add_interactable(
        self,
        name: str,
        x: float,
        y: float,
        width: int = 80,
        height: int = 80,
        interaction_type: str = "examine",
        color: tuple = (100, 80, 60)
    ):
        """Add an interactable object to the home"""
        esper.create_entity(
            Position(x, y),
            RectangleRenderable(width=width, height=height, color=color),
            InteractableObject(name=name, interaction_type=interaction_type)
        )

    def add_npc(
        self,
        name: str,
        x: float,
        y: float,
        dialog_id: str = "",
        portrait_path: str = ""
    ):
        """Add an NPC to the home"""
        npc = NPC(name=name, dialog_id=dialog_id, portrait_path=portrait_path)

        if portrait_path:
            try:
                npc.portrait = pygame.image.load(portrait_path).convert_alpha()
            except Exception as e:
                print(f"Failed to load NPC portrait: {e}")

        esper.create_entity(
            Position(x, y),
            RectangleRenderable(width=60, height=60, color=(180, 140, 100)),
            InteractableObject(name=name, interaction_type="talk"),
            npc
        )

    def set_player_position(self, x: float, y: float):
        """Set the player's position"""
        if self.player_entity is not None:
            pos = esper.component_for_entity(self.player_entity, Position)
            pos.x = x
            pos.y = y

    def move_player_toward(self, target_x: float, target_y: float, speed: float = 400.0):
        """Start moving the player toward a target position"""
        if self.player_entity is None:
            return

        pos = esper.component_for_entity(self.player_entity, Position)
        vel = esper.component_for_entity(self.player_entity, Velocity)

        dx = target_x - pos.x
        dy = target_y - pos.y
        dist_squared = dx * dx + dy * dy

        if dist_squared < 64:
            vel.vx = 0.0
            vel.vy = 0.0
            return

        dist = dist_squared ** 0.5
        vel.vx = speed * dx / dist
        vel.vy = speed * dy / dist

    def stop_player(self):
        """Stop the player's movement"""
        if self.player_entity is not None:
            vel = esper.component_for_entity(self.player_entity, Velocity)
            vel.vx = 0.0
            vel.vy = 0.0

    def get_nearby_interactable(self) -> Optional[str]:
        """Get the name of the nearby interactable object, if any"""
        if self.interaction_system is None:
            return None
        if self.interaction_system.nearby_object is None:
            return None

        obj = esper.component_for_entity(
            self.interaction_system.nearby_object,
            InteractableObject
        )
        return obj.name

    def get_nearby_npc(self) -> Optional[NPC]:
        """Get the nearby NPC component, if player is near one"""
        if self.interaction_system is None:
            return None
        if self.interaction_system.nearby_object is None:
            return None

        try:
            npc = esper.component_for_entity(
                self.interaction_system.nearby_object,
                NPC
            )
            return npc
        except KeyError:
            return None

    def update(self, dt: float):
        """Update the home screen (process ECS systems)"""
        esper.switch_world(self.world_name)
        esper.process(dt)

    def enter(self):
        """Called when entering this screen"""
        if not self.is_initialized:
            self.initialize()
        esper.switch_world(self.world_name)

    def exit(self):
        """Called when leaving this screen"""
        self.stop_player()
