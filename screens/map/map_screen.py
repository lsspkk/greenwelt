# Map screen - top-down world map view
import pygame
import esper
import json
from typing import Optional, List, Dict

from screens.map.order_manager import OrderManager, OrderSystem
from screens.map.greenery_system import GreenerySystem
from screens.map.greenhouse_inventory_system import GreenhouseInventorySystem
from shared.audio_manager import AudioManager
from shared.shared_components import Position, Velocity, DotRenderable, FaceRenderable, MaskState
from .components import MapBackground, RoadLayer, PlayerOnMap, MapMarker, Camera, GreeneryLayer
from .road_collision_system import RoadCollisionSystem
from .map_render_system import MapRenderSystem


class MapScreen:
    """Top-down world map screen"""

    def __init__(self, screen: pygame.Surface, map_name: str = "default", audio: AudioManager = None):
        self.screen = screen
        self.map_name = map_name
        self.world_name = f"map_{map_name}"
        self.player_entity = None
        self.map_entity = None
        self.camera_entity = None
        self.is_initialized = False
        self.locations: List[Dict] = []
        self.map_offset_x = 0
        self.map_offset_y = 0
        self.zoom = 2.0
        self.camera_pos_x = 0
        self.camera_pos_y = 0
        self.order_manager = None
        self.greenery_system = None
        self.greenery_entity = None
        self.map_config = {}
        self.audio = audio

        # Greenhouse inventory system - manages plant supply and growth
        self.greenhouse_inventory_system = None

    def initialize(self):
        """Set up the ECS world for this map"""
        esper.switch_world(self.world_name)
        esper.clear_database()
        # Only add the render system (no movement/collision systems for player)
        esper.add_processor(MapRenderSystem(self.screen), priority=1)
        self.map_entity = esper.create_entity(
            MapBackground(),
            RoadLayer()
        )
        self.player_entity = esper.create_entity(
            Position(400.0, 400.0),
            Velocity(0.0, 0.0),
            DotRenderable(radius=24, color=(200, 240, 200)),
            PlayerOnMap()
        )
        # Create camera entity for rendering
        screen_w, screen_h = self.screen.get_size()
        self.camera_entity = esper.create_entity(
            Camera(
                x=self.camera_pos_x,
                y=self.camera_pos_y,
                zoom=self.zoom,
                screen_width=screen_w,
                screen_height=screen_h
            )
        )

        # Create greenery entity (surface will be set later)
        self.greenery_entity = esper.create_entity(
            GreeneryLayer()
        )

        # Create order manager
        self.order_manager = OrderManager(self.audio)

        # Add order system to ECS
        esper.add_processor(OrderSystem(self.order_manager), priority=2)

        self.is_initialized = True

    def load_config(self, json_path: str, difficulty: str = "medium"):
        """
        Load map configuration from JSON file.

        Args:
            json_path: Path to the JSON config file
            difficulty: Difficulty level - "easy", "medium", or "hard"
        """
        from shared.debug_log import debug
        try:
            with open(json_path, "r") as f:
                self.map_config = json.load(f)

            # Get difficulty-specific settings
            difficulty_key = f"difficulty_{difficulty}"
            difficulty_config = self.map_config.get(difficulty_key, {})

            # Store current difficulty for order generation
            self.current_difficulty = difficulty
            self.difficulty_config = difficulty_config

            # Apply config to order manager (use difficulty overrides if present)
            if self.order_manager is not None:
                self.order_manager.set_config(
                    batch_size=self.map_config.get("batch_size", 3),
                    batch_delay=self.map_config.get("batch_delay", 10.0),
                    accept_time=self.map_config.get("accept_time", 15.0),
                    orders_required=difficulty_config.get(
                        "orders_required", self.map_config.get("orders_required", 10)),
                    plants_required=self.map_config.get("plants_required", 0),
                    active_order_limit=self.map_config.get(
                        "active_order_limit", 6),
                    score_required=difficulty_config.get(
                        "score_required", self.map_config.get("score_required", 0)),
                    points_per_plant=self.map_config.get(
                        "points_per_plant", 10),
                    full_order_bonus=self.map_config.get(
                        "full_order_bonus", 20)
                )

            debug.info(
                f"Loaded map config from {json_path} (difficulty: {difficulty})")
            debug.info(
                f"Difficulty settings: orders_required={difficulty_config.get('orders_required')}, score_required={difficulty_config.get('score_required')}")
        except Exception as e:
            debug.error(f"Failed to load map config: {e}")

    def load_orders(self, json_path: str):
        """Load orders from JSON file"""
        from shared.debug_log import debug
        try:
            with open(json_path, "r") as f:
                orders_data = json.load(f)
            # Pass locations data so order manager can look up emails
            self.order_manager.load_orders(orders_data, self.locations)
            debug.info(f"Loaded orders from {json_path}")
        except Exception as e:
            debug.error(f"Failed to load orders: {e}")

    def load_map_image(self, image_path: str):
        """Load the background image for this map (render system handles zoom)"""
        try:
            image = pygame.image.load(image_path).convert()
            bg = esper.component_for_entity(self.map_entity, MapBackground)
            # Store original size image - MapRenderSystem handles zoom
            bg.image = image
            bg.image_path = image_path
        except Exception as e:
            print(f"Failed to load map image: {e}")

    def load_roads(self, json_path: str):
        """Load roads from JSON and create render surface and collision mask"""
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            strokes = data.get("strokes", [])
            color = tuple(data.get("color", (100, 100, 100)))
            alpha = data.get("alpha", 180)

            if not strokes:
                return

            road_layer = esper.component_for_entity(self.map_entity, RoadLayer)
            road_layer.strokes = strokes
            road_layer.color = color
            road_layer.alpha = alpha

            # Get map image size for surface creation
            bg = esper.component_for_entity(self.map_entity, MapBackground)
            if bg.image is None:
                return

            # bg.image is now at original size (not pre-scaled)
            img_w = bg.image.get_width()
            img_h = bg.image.get_height()

            # Create road display surface with transparency
            road_surface = pygame.Surface(
                (img_w, img_h), pygame.SRCALPHA)

            # Create road mask (white = road, black = no road)
            road_mask = pygame.Surface((img_w, img_h))
            road_mask.fill((0, 0, 0))

            # Draw all strokes
            for stroke in strokes:
                points = stroke["points"]
                width = stroke["width"]

                if len(points) < 2:
                    continue

                # Convert to int for drawing
                int_points = [(int(point[0]), int(point[1]))
                              for point in points]
                int_width = int(width)

                # Draw on display surface
                for i, point in enumerate(int_points):
                    pygame.draw.circle(road_surface, color,
                                       point, int_width // 2)
                    if i > 0:
                        pygame.draw.line(
                            road_surface, color, int_points[i - 1], point, int_width)

                # Draw on mask (white)
                for i, point in enumerate(int_points):
                    pygame.draw.circle(
                        road_mask, (255, 255, 255), point, int_width // 2)
                    if i > 0:
                        pygame.draw.line(
                            road_mask, (255, 255, 255), int_points[i - 1], point, int_width)

            road_surface.set_alpha(alpha)
            road_layer.road_surface = road_surface
            road_layer.road_mask = road_mask

        except Exception as e:
            print(f"Failed to load roads: {e}")

    def initialize_greenhouse_inventory(self):
        """Initialize the greenhouse inventory system after config is loaded."""
        from shared.debug_log import debug

        # Create the greenhouse inventory system
        self.greenhouse_inventory_system = GreenhouseInventorySystem()

        # Apply config if present
        greenhouse_config = self.map_config.get("greenhouse", {})
        self.greenhouse_inventory_system.set_config(
            initial_amount=greenhouse_config.get("plant_initial_amount", 1),
            grow_amount=greenhouse_config.get("plant_grow_amount", 3),
            grow_time_min=greenhouse_config.get("plant_grow_time_min", 30.0),
            grow_time_max=greenhouse_config.get("plant_grow_time_max", 60.0),
            inventory_max=greenhouse_config.get("plant_inventory_max", 7)
        )

        # Initialize the system (loads plant list and sets initial inventory)
        self.greenhouse_inventory_system.initialize()
        debug.info("Greenhouse inventory system initialized")

    def get_greenhouse_location(self) -> Optional[Dict]:
        """Get the shop/greenhouse location from the locations list."""
        for loc in self.locations:
            if loc.get("type") == "shop":
                return loc
        return None

    def get_greenhouse_pick_radius(self) -> float:
        """Get the greenhouse pick radius from config."""
        greenhouse_config = self.map_config.get("greenhouse", {})
        return greenhouse_config.get("pick_radius", 100.0)

    def initialize_greenery(self):
        """Initialize the greenery system after map and roads are loaded"""
        from shared.debug_log import debug

        # Create greenery system (starts white, gets greener with deliveries)
        self.greenery_system = GreenerySystem()

        # Apply greenery config if present
        greenery_config = self.map_config.get("greenery", {})
        if greenery_config.get("enabled", True):
            if "green_color" in greenery_config:
                self.greenery_system.green_color = tuple(
                    greenery_config["green_color"])

        # Get map image dimensions
        bg = esper.component_for_entity(self.map_entity, MapBackground)

        if bg.image is not None:
            map_width = bg.image.get_width()
            map_height = bg.image.get_height()

            # Initialize the greenery system with map dimensions
            self.greenery_system.initialize(map_width, map_height)

            # Set the surface on the greenery entity
            if self.greenery_entity is not None:
                greenery_layer = esper.component_for_entity(
                    self.greenery_entity, GreeneryLayer)
                greenery_layer.surface = self.greenery_system.get_surface()

            debug.info("Greenery system initialized (starts white)")

    def add_greenery_at_delivery(self, location_name: str):
        """Add green patches at a delivery location when order is completed."""
        from shared.debug_log import debug

        if self.greenery_system is None:
            return

        # Find the location coordinates by name
        location_x = None
        location_y = None

        for loc in self.locations:
            if loc.get("name") == location_name:
                location_x = loc.get("x", 0)
                location_y = loc.get("y", 0)
                break

        if location_x is None or location_y is None:
            debug.warning(f"Location '{location_name}' not found for greenery")
            return

        # Add greenery patches at this location
        self.greenery_system.add_greenery_at_location(location_x, location_y)

        # Apply road mask to keep roads unaffected by greenery
        road_layer = esper.component_for_entity(self.map_entity, RoadLayer)
        if road_layer.road_mask is not None:
            self.greenery_system.apply_road_mask(road_layer.road_mask)

        # Update the greenery entity surface
        if self.greenery_entity is not None:
            greenery_layer = esper.component_for_entity(
                self.greenery_entity, GreeneryLayer)
            greenery_layer.surface = self.greenery_system.get_surface()

        debug.info(
            f"Added greenery at {location_name} ({location_x}, {location_y})")

    def load_locations(self, json_path: str):
        """Load location markers from JSON file"""
        try:
            with open(json_path, "r") as f:
                self.locations = json.load(f)
        except Exception as e:
            print(f"Failed to load locations: {e}")

    def initialize_start_position(self) -> tuple:
        """Get the starting position (shop location) adjusted for map offset"""
        x, y = 400.0, 400.0  # Default start position
        for loc in self.locations:
            if loc["type"] == "shop":
                # Adjust coordinates for centered map
                x = loc["x"] + self.map_offset_x
                y = loc["y"] + self.map_offset_y

        if self.player_entity is not None:
            pos = esper.component_for_entity(self.player_entity, Position)
            pos.x = x
            pos.y = y
            # Sync camera immediately
            self.camera_pos_x = x
            self.camera_pos_y = y
            if self.camera_entity is not None:
                camera = esper.component_for_entity(self.camera_entity, Camera)
                camera.x = x
                camera.y = y

    def get_nearby_location(self) -> Optional[Dict]:
        """Return the closest location within tolerance, or None if none are close."""
        if self.player_entity is None:
            return None

        esper.switch_world(self.world_name)
        pos = esper.component_for_entity(self.player_entity, Position)
        closest_loc = None
        closest_dist = None
        for loc in self.locations:
            loc_x = loc["x"] + self.map_offset_x
            loc_y = loc["y"] + self.map_offset_y
            tolerance = loc.get("tolerance", 50)
            dx = pos.x - loc_x
            dy = pos.y - loc_y
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= tolerance:
                if closest_loc is None or distance < closest_dist:
                    closest_loc = loc
                    closest_dist = distance
        return closest_loc

    def add_marker(self, name: str, x: float, y: float, marker_type: str = "city"):
        """Add a point of interest marker to the map"""
        esper.create_entity(
            Position(x, y),
            DotRenderable(radius=18, color=(255, 200, 100)),
            MapMarker(name=name, x=x, y=y, marker_type=marker_type)
        )

    def move_player_toward(self, target_x: float, target_y: float, speed: float = 200.0, dt: float = 1/60):
        """Move the player a single step toward the target, checking collision."""
        if self.player_entity is None:
            return
        esper.switch_world(self.world_name)
        pos = esper.component_for_entity(self.player_entity, Position)
        vel = esper.component_for_entity(self.player_entity, Velocity)
        road_layer = esper.component_for_entity(self.map_entity, RoadLayer)
        dx = target_x - pos.x
        dy = target_y - pos.y
        dist_squared = dx * dx + dy * dy
        dist = dist_squared ** 0.5
        
        # Always update facing direction
        if dist > 0.01:
            vel.facing_dx = dx / dist
            vel.facing_dy = dy / dist
        
        if dist < 1.0:
            pos.x = target_x
            pos.y = target_y
            vel.vx = 0.0
            vel.vy = 0.0
            return
        # Calculate step
        step = min(speed * dt, dist)
        step_x = dx / dist * step
        step_y = dy / dist * step
        next_x = pos.x + step_x
        next_y = pos.y + step_y
        # Check collision along the step
        steps = int(max(abs(step_x), abs(step_y)) // 2) + 1
        collision = False
        for i in range(1, steps + 1):
            t = i / steps
            x = pos.x + step_x * t
            y = pos.y + step_y * t
            if not road_layer.is_on_road(x, y):
                collision = True
                break
        if not collision:
            pos.x = next_x
            pos.y = next_y
            vel.vx = step_x / dt
            vel.vy = step_y / dt
            vel.facing_dx = dx / dist
            vel.facing_dy = dy / dist
        else:
            vel.vx = 0.0
            vel.vy = 0.0

    def stop_player(self):
        """Stop the player's movement"""
        if self.player_entity is not None:
            esper.switch_world(self.world_name)
            vel = esper.component_for_entity(self.player_entity, Velocity)
            vel.vx = 0.0
            vel.vy = 0.0

    def get_player_position(self) -> Optional[tuple]:
        """Get the player's current position"""
        if self.player_entity is None:
            return None
        esper.switch_world(self.world_name)
        pos = esper.component_for_entity(self.player_entity, Position)
        return (pos.x, pos.y)

    def is_player_at_target(self, target_x: float, target_y: float, threshold: float = 12.0) -> bool:
        """Check if player has reached a target position"""
        if self.player_entity is None:
            return False

        esper.switch_world(self.world_name)
        pos = esper.component_for_entity(self.player_entity, Position)
        dx = target_x - pos.x
        dy = target_y - pos.y
        dist_squared = dx * dx + dy * dy

        return dist_squared < threshold * threshold

    def update(self, dt: float):
        """Update the map (process ECS systems)"""
        # Sync camera position with player before processing
        if self.player_entity is not None:
            self.camera_pos_x, self.camera_pos_y = self.get_player_position()

            # Update Camera entity
            if self.camera_entity is not None:
                camera = esper.component_for_entity(self.camera_entity, Camera)
                camera.x = self.camera_pos_x
                camera.y = self.camera_pos_y

        # Update greenhouse inventory system (handles plant growth timer)
        if self.greenhouse_inventory_system is not None:
            self.greenhouse_inventory_system.update(dt)

        esper.process(dt)
        esper.switch_world(self.world_name)

    def enter(self):
        """Called when entering this screen"""
        if not self.is_initialized:
            self.initialize()
        esper.switch_world(self.world_name)

    def exit(self):
        """Called when leaving this screen"""
        self.stop_player()
