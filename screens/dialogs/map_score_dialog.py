"""
Map Score Dialog - Shows score and stats after completing a map.

Features:
- Animated plant balls that move toward center, then bounce like billiard balls
- Order delivery stats
- Semi-transparent plant backgrounds
- OK button to proceed to next map or end game
"""

import pygame
import random
import math
from pathlib import Path
from typing import Optional, List, Dict
from shared.debug_log import debug


class PlantBall:
    """A plant image that moves and bounces like a billiard ball."""

    def __init__(self, image: pygame.Surface, start_x: float, start_y: float,
                 target_x: float, target_y: float, speed: float):
        self.original_image = image
        self.x = start_x
        self.y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed

        # Movement phase: "moving_to_center" or "bouncing"
        self.phase = "moving_to_center"

        # Velocity for bouncing phase
        self.vx = 0.0
        self.vy = 0.0

        # Rotation
        self.angle = 0.0
        self.spin_speed = 0.0  # degrees per second

        # Ball size (diameter for clipping)
        self.radius = 50

        # Create circular clipped image
        self.clipped_image = self._create_circular_image(image)
        self.rotated_image = self.clipped_image

    def _create_circular_image(self, image: pygame.Surface) -> pygame.Surface:
        """Create a circular clipped version of the plant image."""
        size = self.radius * 2

        # Scale image to fit in circle
        scaled = pygame.transform.smoothscale(image, (size, size))

        # Create surface with alpha
        circular = pygame.Surface((size, size), pygame.SRCALPHA)

        # Draw circle mask
        pygame.draw.circle(circular, (255, 255, 255, 255), (self.radius, self.radius), self.radius)

        # Blit scaled image and apply mask
        circular.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        return circular

    def update(self, dt: float, bounds: pygame.Rect):
        """Update ball position and rotation."""
        if self.phase == "moving_to_center":
            # Move toward center
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 10:
                # Reached center, start bouncing
                self.phase = "bouncing"
                # Random angle for bounce direction
                angle = random.uniform(0, 2 * math.pi)
                bounce_speed = random.uniform(200, 400)
                self.vx = math.cos(angle) * bounce_speed
                self.vy = math.sin(angle) * bounce_speed
                self.spin_speed = random.uniform(180, 360)
                if random.random() < 0.5:
                    self.spin_speed = -self.spin_speed
            else:
                # Move toward center
                move_dist = self.speed * dt
                if move_dist > dist:
                    move_dist = dist
                self.x += (dx / dist) * move_dist
                self.y += (dy / dist) * move_dist

        elif self.phase == "bouncing":
            # Update position
            self.x += self.vx * dt
            self.y += self.vy * dt

            # Bounce off walls
            if self.x - self.radius < bounds.left:
                self.x = bounds.left + self.radius
                self.vx = abs(self.vx)
            elif self.x + self.radius > bounds.right:
                self.x = bounds.right - self.radius
                self.vx = -abs(self.vx)

            if self.y - self.radius < bounds.top:
                self.y = bounds.top + self.radius
                self.vy = abs(self.vy)
            elif self.y + self.radius > bounds.bottom:
                self.y = bounds.bottom - self.radius
                self.vy = -abs(self.vy)

            # Update rotation
            self.angle += self.spin_speed * dt
            self.rotated_image = pygame.transform.rotate(self.clipped_image, self.angle)

    def draw(self, surface: pygame.Surface):
        """Draw the ball on the surface."""
        # Center the rotated image
        rect = self.rotated_image.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(self.rotated_image, rect)


class MapScoreDialog:
    """
    Full screen dialog showing map completion stats with animated plant balls.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.visible = False

        # Stats to display
        self.orders_completed = 0
        self.plants_delivered = 0
        self.total_score = 0
        self.completed_orders = []  # List of Order objects
        self.map_name = ""

        # Animation state
        self.animation_timer = 0.0
        self.plant_balls: List[PlantBall] = []

        # Dialog bounds (like billiard table)
        self.dialog_rect = pygame.Rect(
            (self.screen_width - 1400) // 2,
            (self.screen_height - 700) // 2,
            1400,
            700
        )

        # Inner bounds for ball bouncing (with padding for border)
        self.bounce_bounds = pygame.Rect(
            self.dialog_rect.left + 20,
            self.dialog_rect.top + 20,
            self.dialog_rect.width - 40,
            self.dialog_rect.height - 40
        )

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.header_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 52)

        # Colors
        self.bg_color = (25, 60, 40)  # Dark green like billiard table
        self.border_color = (80, 50, 30)  # Brown border
        self.text_color = (255, 255, 255)
        self.accent_color = (100, 200, 120)
        self.button_color = (60, 120, 80)
        self.button_hover_color = (80, 150, 100)

        # Button
        self.ok_button_rect = pygame.Rect(0, 0, 0, 0)

        # Plant image cache
        self.plant_image_cache: Dict[str, pygame.Surface] = {}

        # Callback for when dialog is closed
        self.on_close = None

    def open(self, orders_completed: int, plants_delivered: int, total_score: int,
             completed_orders: list, map_name: str = ""):
        """Open the dialog with stats."""
        self.visible = True
        self.orders_completed = orders_completed
        self.plants_delivered = plants_delivered
        self.total_score = total_score
        self.completed_orders = completed_orders
        self.map_name = map_name
        self.animation_timer = 0.0

        # Create plant balls from completed orders
        self._create_plant_balls()

        debug.info(f"MapScoreDialog opened: {orders_completed} orders, {plants_delivered} plants, {total_score} score")

    def close(self):
        """Close the dialog."""
        self.visible = False
        self.plant_balls = []

        if self.on_close is not None:
            self.on_close()

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        plant_path = Path(__file__).parent.parent.parent / "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            self.plant_image_cache[filename] = image
            return image
        except Exception as e:
            debug.error(f"Failed to load plant image {filename}: {e}")
            return None

    def _create_plant_balls(self):
        """Create animated plant balls from delivered plants."""
        self.plant_balls = []

        # Collect all plant filenames from completed orders
        plant_filenames = []
        for order in self.completed_orders:
            for plant in order.plants:
                plant_filenames.append(plant.filename)

        # Take up to 5 random plants
        if len(plant_filenames) > 5:
            selected = random.sample(plant_filenames, 5)
        else:
            selected = plant_filenames[:5]

        # Create balls
        center_x = self.dialog_rect.centerx
        center_y = self.dialog_rect.centery

        for i, filename in enumerate(selected):
            image = self._load_plant_image(filename)
            if image is None:
                continue

            # Start position: random side of dialog
            side = random.choice(["left", "right", "top", "bottom"])
            if side == "left":
                start_x = self.dialog_rect.left - 100
                start_y = random.randint(self.dialog_rect.top, self.dialog_rect.bottom)
            elif side == "right":
                start_x = self.dialog_rect.right + 100
                start_y = random.randint(self.dialog_rect.top, self.dialog_rect.bottom)
            elif side == "top":
                start_x = random.randint(self.dialog_rect.left, self.dialog_rect.right)
                start_y = self.dialog_rect.top - 100
            else:  # bottom
                start_x = random.randint(self.dialog_rect.left, self.dialog_rect.right)
                start_y = self.dialog_rect.bottom + 100

            # Random speed
            speed = random.uniform(300, 500)

            ball = PlantBall(image, start_x, start_y, center_x, center_y, speed)
            self.plant_balls.append(ball)

    def _get_delivery_summary(self) -> List[str]:
        """Get list of delivery summary lines."""
        lines = []

        for order in self.completed_orders:
            location = order.customer_location
            plant_count = sum(p.amount for p in order.plants)
            lines.append(f"  {location}: {plant_count} kasvia")

        return lines

    def handle_input(self, input_mgr) -> Optional[str]:
        """Handle input. Returns action string or None."""
        if not self.visible:
            return None

        if input_mgr.clicked_in_rect(self.ok_button_rect):
            self.close()
            return "map_score_closed"

        return None

    def update(self, dt: float):
        """Update animations."""
        if not self.visible:
            return

        self.animation_timer += dt

        # Update plant balls
        for ball in self.plant_balls:
            ball.update(dt, self.bounce_bounds)

    def draw(self, input_mgr):
        """Draw the dialog."""
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw dialog background (billiard table style)
        # Outer border (wood frame)
        border_rect = self.dialog_rect.inflate(20, 20)
        pygame.draw.rect(self.screen, self.border_color, border_rect, border_radius=15)

        # Inner green felt
        pygame.draw.rect(self.screen, self.bg_color, self.dialog_rect, border_radius=10)

        # Inner edge highlight
        inner_edge = self.dialog_rect.inflate(-10, -10)
        pygame.draw.rect(self.screen, (35, 80, 55), inner_edge, width=3, border_radius=8)

        # Draw plant balls (behind text)
        for ball in self.plant_balls:
            ball.draw(self.screen)

        # Draw semi-transparent panel for text
        text_panel = pygame.Rect(
            self.dialog_rect.left + 100,
            self.dialog_rect.top + 80,
            self.dialog_rect.width - 200,
            400
        )
        panel_surface = pygame.Surface((text_panel.width, text_panel.height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 120))
        self.screen.blit(panel_surface, text_panel.topleft)

        # Draw title
        title_text = "KARTTA LÄPÄISTY!"
        title_surface = self.title_font.render(title_text, True, self.accent_color)
        title_rect = title_surface.get_rect(centerx=self.dialog_rect.centerx, top=self.dialog_rect.top + 100)
        self.screen.blit(title_surface, title_rect)

        # Draw stats
        y = title_rect.bottom + 40

        stats = [
            f"Tilauksia toimitettu: {self.orders_completed}",
            f"Kasveja toimitettu: {self.plants_delivered}",
            f"Pisteet: {self.total_score}"
        ]

        for stat in stats:
            stat_surface = self.header_font.render(stat, True, self.text_color)
            stat_rect = stat_surface.get_rect(centerx=self.dialog_rect.centerx, top=y)
            self.screen.blit(stat_surface, stat_rect)
            y += 50

        # Draw delivery summary
        y += 20
        summary_label = self.text_font.render("Toimitukset:", True, self.accent_color)
        self.screen.blit(summary_label, (self.dialog_rect.left + 120, y))
        y += 35

        summary_lines = self._get_delivery_summary()
        for line in summary_lines[:6]:  # Max 6 lines
            line_surface = self.text_font.render(line, True, self.text_color)
            self.screen.blit(line_surface, (self.dialog_rect.left + 120, y))
            y += 30

        # Draw OK button
        button_width = 140
        button_height = 60
        self.ok_button_rect = pygame.Rect(
            self.dialog_rect.bottomright[0] - button_width - 40,
            self.dialog_rect.bottom - 100,
            button_width,
            button_height
        )

        hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, self.ok_button_rect)
        button_color = self.button_hover_color if hover else self.button_color
        pygame.draw.rect(self.screen, button_color, self.ok_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.accent_color, self.ok_button_rect, width=3, border_radius=10)

        ok_text = self.button_font.render("-O.x-", True, self.text_color)
        ok_rect = ok_text.get_rect(center=self.ok_button_rect.center)
        self.screen.blit(ok_text, ok_rect)
