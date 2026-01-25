# Map screen - top-down world map view
import pygame
import esper
from typing import Optional, List

from shared.components import Position, Velocity, DotRenderable
from shared.systems import MovementSystem
from screens.map.components import MapBackground, CollisionLayer, PlayerOnMap, MapMarker
from screens.map.systems import MapRenderSystem, CollisionSystem


class MapScreen:
    """Top-down world map screen"""

    def __init__(self, screen: pygame.Surface, map_name: str = "default"):
        self.screen = screen
        self.map_name = map_name
        self.world_name = f"map_{map_name}"
        self.player_entity = None
        self.map_entity = None
        self.is_initialized = False

    def initialize(self):
        """Set up the ECS world for this map"""
        # Create a new esper world for this map
        esper.switch_world(self.world_name)
        esper.clear_database()

        # Add systems
        esper.add_processor(CollisionSystem(), priority=3)
        esper.add_processor(MovementSystem(), priority=2)
        esper.add_processor(MapRenderSystem(self.screen), priority=1)

        # Create map entity with background and collision
        self.map_entity = esper.create_entity(
            MapBackground(),
            CollisionLayer()
        )

        # Create player entity (sized for 1920x1080)
        self.player_entity = esper.create_entity(
            Position(400.0, 400.0),
            Velocity(0.0, 0.0),
            DotRenderable(radius=24, color=(200, 240, 200)),
            PlayerOnMap()
        )

        self.is_initialized = True

    def load_map_image(self, image_path: str):
        """Load the background image for this map"""
        try:
            image = pygame.image.load(image_path).convert()
            bg = esper.component_for_entity(self.map_entity, MapBackground)
            bg.image_path = image_path
            bg.image = image
        except Exception as e:
            print(f"Failed to load map image: {e}")

    def load_collision_grid(self, grid: List[List[int]], tile_width: int = 64, tile_height: int = 64):
        """Load collision data for this map"""
        col = esper.component_for_entity(self.map_entity, CollisionLayer)
        col.grid = grid
        col.tile_width = tile_width
        col.tile_height = tile_height

    def add_marker(self, name: str, x: float, y: float, marker_type: str = "city"):
        """Add a point of interest marker to the map"""
        esper.create_entity(
            Position(x, y),
            DotRenderable(radius=18, color=(255, 200, 100)),
            MapMarker(name=name, x=x, y=y, marker_type=marker_type)
        )

    def set_player_position(self, x: float, y: float):
        """Set the player's position on the map"""
        if self.player_entity is not None:
            pos = esper.component_for_entity(self.player_entity, Position)
            pos.x = x
            pos.y = y

    def move_player_toward(self, target_x: float, target_y: float, speed: float = 500.0):
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

    def get_player_position(self) -> Optional[tuple]:
        """Get the player's current position"""
        if self.player_entity is None:
            return None
        pos = esper.component_for_entity(self.player_entity, Position)
        return (pos.x, pos.y)

    def is_player_at_target(self, target_x: float, target_y: float, threshold: float = 12.0) -> bool:
        """Check if player has reached a target position"""
        if self.player_entity is None:
            return False

        pos = esper.component_for_entity(self.player_entity, Position)
        dx = target_x - pos.x
        dy = target_y - pos.y
        dist_squared = dx * dx + dy * dy

        return dist_squared < threshold * threshold

    def update(self, dt: float):
        """Update the map (process ECS systems)"""
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
