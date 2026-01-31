"""
Delivery dialog - Full screen dialog for delivering orders.

Shows the order details with plant requirements and calculates what
the player can deliver based on their current inventory.

Scoring system:
- Each plant delivered = points_per_plant (default 10)
- Full order completed = full_order_bonus (default 20) extra points

Player can deliver if they have at least one matching plant.
Partial deliveries give proportional points but no bonus.
"""

import pygame
import random
import math
from pathlib import Path
from typing import Optional, List, Dict, Callable
from shared.shared_components import Order, PlantOrder
from shared.debug_log import debug


class DeliveryDialog:
    """
    Full screen delivery dialog shown when player arrives at delivery location.

    Layout:
    - Top left: Location name
    - Top left (right of name): Face graphics
    - Top right: Delivery status (full/partial) and points preview
    - Middle: List of order items with delivery status
    - Bottom right: Up arrow, Down arrow (scroll), OK button (deliver)
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.visible = False
        self.order: Optional[Order] = None
        self.location_name = ""

        # Player inventory reference (set when opened)
        self.player_inventory: Optional[Dict[str, int]] = None

        # Scoring config (set when opened)
        self.points_per_plant = 10
        self.full_order_bonus = 20

        # Calculated delivery info
        self.deliverable_amounts: Dict[str, int] = {}  # plant filename -> amount can deliver
        self.total_deliverable = 0
        self.total_requested = 0
        self.is_full_delivery = False
        self.can_deliver = False
        self.points_preview = 0

        # Scroll state for order rows
        self.scroll_offset = 0
        self.max_visible_rows = 5

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.header_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 52)
        self.small_font = pygame.font.Font(None, 32)

        # Colors
        self.bg_color = (30, 40, 50)
        self.header_bg_color = (40, 55, 70)
        self.text_color = (255, 255, 255)
        self.secondary_text_color = (180, 180, 180)
        self.button_color = (60, 80, 100)
        self.button_hover_color = (80, 100, 120)
        self.accent_color = (100, 180, 120)
        self.warning_color = (220, 160, 80)
        self.missing_color = (180, 80, 80)
        self.success_color = (80, 180, 100)

        # Button rects (set during draw)
        self.up_button_rect = pygame.Rect(0, 0, 0, 0)
        self.down_button_rect = pygame.Rect(0, 0, 0, 0)
        self.ok_button_rect = pygame.Rect(0, 0, 0, 0)

        # Layout constants
        self.header_height = 120
        self.row_height = 120
        self.plant_size = 80
        self.max_plants_per_row = 7
        self.button_size = 80
        self.button_margin = 20

        self.plant_area_width = self.max_plants_per_row * (self.plant_size + 8) + 20

        # Cache for loaded plant images
        self.plant_image_cache = {}

        # Callback for when order is completed (receives order, plants_delivered, is_full)
        self.on_order_completed: Optional[Callable] = None

        # Callback to remove plants from player inventory after delivery
        self.on_plants_delivered: Optional[Callable] = None

        # Celebration animation state
        self.celebrating = False
        self.celebration_timer = 0.0
        self.celebration_duration = 2.0
        self.celebration_bursts = []  # List of burst animations, one per plant
        self.celebration_points = 0
        self.celebration_show_text = False  # Show text after animations
        self.celebration_can_close = False  # User can click to close

    def open(self, order: Order, location_name: str,
             player_inventory: Dict[str, int],
             points_per_plant: int = 10,
             full_order_bonus: int = 20):
        """
        Open the delivery dialog for an order.

        Args:
            order: The order to deliver
            location_name: Name of the delivery location
            player_inventory: Current player inventory (plant filename -> count)
            points_per_plant: Points awarded per plant delivered
            full_order_bonus: Bonus points for completing full order
        """
        self.order = order
        self.location_name = location_name
        self.player_inventory = player_inventory
        self.points_per_plant = points_per_plant
        self.full_order_bonus = full_order_bonus
        self.scroll_offset = 0
        self.visible = True
        self.celebrating = False
        self.celebration_timer = 0.0
        self.celebration_lines = []
        self.celebration_points = 0

        # Calculate what can be delivered
        self._calculate_delivery()

        debug.info(f"DeliveryDialog opened for {location_name}, can deliver: {self.total_deliverable}/{self.total_requested}")

    def _calculate_delivery(self):
        """Calculate how many plants can be delivered based on inventory."""
        self.deliverable_amounts = {}
        self.total_deliverable = 0
        self.total_requested = 0

        if self.order is None or self.player_inventory is None:
            self.can_deliver = False
            self.is_full_delivery = False
            self.points_preview = 0
            return

        # For each plant in the order, calculate how many we can deliver
        for plant in self.order.plants:
            requested = plant.amount
            available = self.player_inventory.get(plant.filename, 0)
            deliverable = min(requested, available)

            self.deliverable_amounts[plant.filename] = deliverable
            self.total_deliverable = self.total_deliverable + deliverable
            self.total_requested = self.total_requested + requested

        # Check if we can deliver at all (at least one plant)
        self.can_deliver = self.total_deliverable > 0

        # Check if this is a full delivery
        self.is_full_delivery = (self.total_deliverable == self.total_requested)

        # Calculate points preview
        self.points_preview = self.total_deliverable * self.points_per_plant
        if self.is_full_delivery:
            self.points_preview = self.points_preview + self.full_order_bonus

    def close(self):
        """Close the delivery dialog."""
        self.visible = False
        self.order = None
        self.location_name = ""
        self.player_inventory = None
        self.celebrating = False
        debug.info("DeliveryDialog closed")

    def _start_celebration(self):
        """Start the celebration animation with one burst per plant delivered."""
        self.celebrating = True
        self.celebration_timer = 0.0
        self.celebration_points = self.points_preview
        self.celebration_show_text = False
        self.celebration_can_close = False

        # Create one burst animation for each plant delivered
        self.celebration_bursts = []
        num_bursts = max(1, self.total_deliverable)

        # Track used positions to avoid too much overlap
        used_positions = []
        margin = 150  # Minimum distance between burst centers

        for burst_index in range(num_bursts):
            # Roll position, trying to avoid overlap
            center_x, center_y = self._roll_burst_position(used_positions, margin)
            used_positions.append((center_x, center_y))

            # Random green color with 10% variation
            base_green = 200
            variation = int(base_green * 0.1)
            r = random.randint(30, 70)
            g = random.randint(base_green - variation, min(255, base_green + variation))
            b = random.randint(60, 120)
            color = (r, g, b)

            # Random opacity with 10% variation (base 255)
            base_alpha = 230
            alpha_variation = int(base_alpha * 0.1)
            alpha = random.randint(base_alpha - alpha_variation, min(255, base_alpha + alpha_variation))

            # Create lines for this burst
            lines = []
            num_lines = random.randint(16, 24)
            for i in range(num_lines):
                angle = (2 * math.pi / num_lines) * i
                # Add small angle variation
                angle = angle + random.uniform(-0.1, 0.1)
                max_length = random.randint(200, 400)
                speed = random.randint(600, 1000)
                lines.append([angle, 0, max_length, speed])

            burst = {
                "center_x": center_x,
                "center_y": center_y,
                "color": color,
                "alpha": alpha,
                "lines": lines
            }
            self.celebration_bursts.append(burst)

        debug.info(f"Celebration started with {num_bursts} bursts")

    def _roll_burst_position(self, used_positions, margin):
        """Roll a random position for a burst, trying to avoid overlap."""
        # Define area where bursts can appear (leave space for text in center)
        min_x = 150
        max_x = self.screen_width - 150
        min_y = 150
        max_y = self.screen_height - 200

        # Try up to 10 times to find a non-overlapping position
        for attempt in range(10):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)

            # Check distance to all used positions
            too_close = False
            for used_x, used_y in used_positions:
                dx = x - used_x
                dy = y - used_y
                distance = (dx * dx + dy * dy) ** 0.5
                if distance < margin:
                    too_close = True
                    break

            if not too_close:
                return x, y

        # If we couldn't find a good spot, just return a random position
        return random.randint(min_x, max_x), random.randint(min_y, max_y)

    def update(self, dt: float):
        """Update the delivery dialog (celebration animation)."""
        if not self.visible:
            return

        if not self.celebrating:
            return

        self.celebration_timer = self.celebration_timer + dt

        # Update all burst animations
        all_complete = True
        for burst in self.celebration_bursts:
            for line in burst["lines"]:
                current_length = line[1]
                max_length = line[2]
                speed = line[3]

                if current_length < max_length:
                    new_length = current_length + speed * dt
                    if new_length > max_length:
                        new_length = max_length
                    line[1] = new_length
                    all_complete = False

        # Show text after animations complete
        if all_complete and not self.celebration_show_text:
            self.celebration_show_text = True

        # Allow closing after text is shown for a moment
        if self.celebration_show_text and self.celebration_timer >= self.celebration_duration:
            self.celebration_can_close = True

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        plant_path = Path(__file__).parent.parent.parent / "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            scaled = pygame.transform.smoothscale(image, (self.plant_size, self.plant_size))
            self.plant_image_cache[filename] = scaled
            return scaled
        except Exception as e:
            debug.error(f"Failed to load plant image {filename}: {e}")
            return None

    def _get_total_rows(self) -> int:
        """Get total number of rows in the order."""
        if self.order is None:
            return 0
        return len(self.order.plants)

    def _needs_scroll(self) -> bool:
        """Check if scrolling is needed."""
        return self._get_total_rows() > self.max_visible_rows

    def _scroll_up(self):
        """Scroll up one row."""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1

    def _scroll_down(self):
        """Scroll down one row."""
        max_scroll = max(0, self._get_total_rows() - self.max_visible_rows)
        if self.scroll_offset < max_scroll:
            self.scroll_offset += 1

    def _complete_order(self):
        """Complete the delivery and remove plants from inventory."""
        if self.order is None:
            return

        if not self.can_deliver:
            return

        # Remove delivered plants from inventory
        if self.on_plants_delivered is not None:
            self.on_plants_delivered(self.deliverable_amounts)

        # Notify order completion
        if self.on_order_completed is not None:
            self.on_order_completed(self.order, self.total_deliverable, self.is_full_delivery)

        debug.info(f"Order {self.order.order_id} delivered: {self.total_deliverable}/{self.total_requested} plants, +{self.points_preview} points")

        self._start_celebration()

    def handle_input(self, input_mgr) -> Optional[str]:
        """Handle input while dialog is open. Returns action string or None."""
        if not self.visible:
            return None

        # During celebration, only allow closing when ready
        if self.celebrating:
            if self.celebration_can_close:
                if input_mgr.clicked_in_rect(self.ok_button_rect):
                    self.close()
                    return "celebration_closed"
            return None

        # Check scroll buttons
        if input_mgr.clicked_in_rect(self.up_button_rect):
            self._scroll_up()
            return "scroll_up"

        if input_mgr.clicked_in_rect(self.down_button_rect):
            self._scroll_down()
            return "scroll_down"

        # Check OK button - only if delivery is possible
        if input_mgr.clicked_in_rect(self.ok_button_rect):
            if self.can_deliver:
                self._complete_order()
                return "order_completed"
            else:
                return "cannot_deliver"

        return None

    def draw(self):
        """Draw the full delivery dialog."""
        if not self.visible:
            return

        # If celebrating, draw celebration animation
        if self.celebrating:
            self._draw_celebration()
            return

        # Fill background
        self.screen.fill(self.bg_color)

        # Draw header
        self._draw_header()

        # Draw order rows
        self._draw_order_rows()

        # Draw buttons
        self._draw_buttons()

    def _draw_header(self):
        """Draw the header section with location name, status, and points preview."""
        # Header background
        header_rect = pygame.Rect(0, 0, self.screen_width, self.header_height)
        pygame.draw.rect(self.screen, self.header_bg_color, header_rect)

        # Location name (top left)
        name_surf = self.title_font.render(self.location_name, True, self.text_color)
        self.screen.blit(name_surf, (40, 35))

        # Face graphics (right of name)
        face_x = 40 + name_surf.get_width() + 30
        face_y = 30
        self._draw_face(face_x, face_y)

        # Delivery status and points (top right)
        if self.is_full_delivery:
            status_text = "Täysi toimitus!"
            status_color = self.success_color
        elif self.can_deliver:
            status_text = f"Osittainen: {self.total_deliverable}/{self.total_requested}"
            status_color = self.warning_color
        else:
            status_text = "Ei kasveja!"
            status_color = self.missing_color

        status_surf = self.header_font.render(status_text, True, status_color)
        status_x = self.screen_width - status_surf.get_width() - 40
        self.screen.blit(status_surf, (status_x, 25))

        # Points preview
        if self.can_deliver:
            bonus_text = f" (+{self.full_order_bonus} bonus)" if self.is_full_delivery else ""
            points_text = f"+{self.points_preview} pistettä{bonus_text}"
            points_surf = self.text_font.render(points_text, True, self.accent_color)
            points_x = self.screen_width - points_surf.get_width() - 40
            self.screen.blit(points_surf, (points_x, 75))

    def _draw_face(self, x: int, y: int):
        """Draw a simple face next to the location name."""
        face_color = (255, 210, 80)
        face_radius = 30
        cx = x + face_radius
        cy = y + face_radius

        pygame.draw.circle(self.screen, face_color, (cx, cy), face_radius)

        # Eyes
        eye_y = cy - 8
        left_eye_x = cx - 10
        right_eye_x = cx + 10
        pygame.draw.circle(self.screen, (60, 40, 30), (left_eye_x, eye_y), 5)
        pygame.draw.circle(self.screen, (60, 40, 30), (right_eye_x, eye_y), 5)

        # Smile or sad face based on delivery status
        if self.can_deliver:
            smile_rect = pygame.Rect(cx - 15, cy - 5, 30, 25)
            pygame.draw.arc(self.screen, (60, 40, 30), smile_rect, 3.5, 6.0, 3)
        else:
            # Sad face
            sad_rect = pygame.Rect(cx - 15, cy + 5, 30, 20)
            pygame.draw.arc(self.screen, (60, 40, 30), sad_rect, 0.3, 2.8, 3)

        # Rosy cheeks
        pygame.draw.circle(self.screen, (255, 160, 120), (cx - 18, cy + 5), 5)
        pygame.draw.circle(self.screen, (255, 160, 120), (cx + 18, cy + 5), 5)

    def _draw_order_rows(self):
        """Draw the list of order items with delivery status."""
        if self.order is None:
            return

        content_y = self.header_height + 20
        visible_rows = min(self.max_visible_rows, len(self.order.plants))

        for i in range(visible_rows):
            plant_index = i + self.scroll_offset
            if plant_index >= len(self.order.plants):
                break

            plant = self.order.plants[plant_index]
            row_y = content_y + i * self.row_height

            self._draw_order_row(plant, row_y, plant_index + 1)

    def _draw_order_row(self, plant: PlantOrder, y: int, row_number: int):
        """Draw a single order row with plant images showing delivery status."""
        requested = plant.amount
        deliverable = self.deliverable_amounts.get(plant.filename, 0)

        # Row background color based on delivery status
        if deliverable >= requested:
            row_bg = (45, 65, 55)  # Green tint - full
        elif deliverable > 0:
            row_bg = (55, 55, 45)  # Yellow tint - partial
        else:
            row_bg = (55, 45, 45)  # Red tint - none

        row_rect = pygame.Rect(20, y, self.screen_width - 40, self.row_height - 10)
        pygame.draw.rect(self.screen, row_bg, row_rect, border_radius=12)

        # Left side: Plant info
        text_x = 40
        text_y = y + 15

        # Row number and plant name
        name_text = f"{row_number}. {plant.name_fi}"
        name_surf = self.text_font.render(name_text, True, self.text_color)
        self.screen.blit(name_surf, (text_x, text_y))

        # Delivery status text
        if deliverable >= requested:
            status_text = f"Toimitetaan: {deliverable}/{requested} kpl"
            status_color = self.success_color
        elif deliverable > 0:
            status_text = f"Toimitetaan: {deliverable}/{requested} kpl (puuttuu {requested - deliverable})"
            status_color = self.warning_color
        else:
            status_text = f"Puuttuu: {requested} kpl"
            status_color = self.missing_color

        status_surf = self.text_font.render(status_text, True, status_color)
        self.screen.blit(status_surf, (text_x, text_y + 35))

        # English name
        en_text = f"({plant.name_en})"
        en_surf = self.small_font.render(en_text, True, (120, 120, 120))
        self.screen.blit(en_surf, (text_x, text_y + 65))

        # Right side: Plant images - show ALL requested plants
        # Plants player can deliver are shown normally
        # Plants player can't deliver have red X on top
        plant_image = self._load_plant_image(plant.filename)
        if plant_image is not None:
            plants_start_x = self.screen_width - self.plant_area_width - 20
            plants_to_draw = min(requested, self.max_plants_per_row)

            for j in range(plants_to_draw):
                img_x = plants_start_x + j * (self.plant_size + 8)
                img_y = y + (self.row_height - self.plant_size) // 2 - 5

                # Draw the plant image
                self.screen.blit(plant_image, (img_x, img_y))

                # If this plant can't be delivered, draw red X on top
                if j >= deliverable:
                    self._draw_red_x(img_x, img_y, self.plant_size, self.plant_size)

            # Show "+X" if more than 7 requested
            if requested > self.max_plants_per_row:
                extra_count = requested - self.max_plants_per_row
                extra_missing = max(0, extra_count - max(0, deliverable - self.max_plants_per_row))
                if extra_missing > 0:
                    extra_text = f"+{extra_count} ({extra_missing} puuttuu)"
                    extra_color = self.missing_color
                else:
                    extra_text = f"+{extra_count}"
                    extra_color = self.accent_color
                extra_surf = self.small_font.render(extra_text, True, extra_color)
                extra_x = plants_start_x + self.max_plants_per_row * (self.plant_size + 8) + 5
                extra_y = y + self.row_height // 2 - 10
                self.screen.blit(extra_surf, (extra_x, extra_y))

    def _draw_red_x(self, x: int, y: int, width: int, height: int):
        """Draw a red X cross over a plant image to indicate it can't be delivered."""
        # Red color with some transparency effect
        red_color = (220, 60, 60)
        line_width = 6

        # Draw X from corner to corner with padding
        padding = 8
        x1 = x + padding
        y1 = y + padding
        x2 = x + width - padding
        y2 = y + height - padding

        # Draw the two lines of the X
        pygame.draw.line(self.screen, red_color, (x1, y1), (x2, y2), line_width)
        pygame.draw.line(self.screen, red_color, (x2, y1), (x1, y2), line_width)

    def _draw_buttons(self):
        """Draw the bottom buttons: up, down, and deliver."""
        button_y = self.screen_height - self.button_size - 30
        button_x_start = self.screen_width - (self.button_size * 3 + self.button_margin * 2) - 40

        # Up arrow button
        self.up_button_rect = pygame.Rect(
            button_x_start, button_y,
            self.button_size, self.button_size
        )

        # Down arrow button
        self.down_button_rect = pygame.Rect(
            button_x_start + self.button_size + self.button_margin, button_y,
            self.button_size, self.button_size
        )

        # OK/Deliver button
        self.ok_button_rect = pygame.Rect(
            button_x_start + (self.button_size + self.button_margin) * 2, button_y,
            self.button_size, self.button_size
        )

        needs_scroll = self._needs_scroll()

        # Draw scroll buttons if needed
        if needs_scroll:
            can_scroll_up = self.scroll_offset > 0
            up_color = self.button_color if can_scroll_up else (40, 50, 60)
            pygame.draw.rect(self.screen, up_color, self.up_button_rect, border_radius=12)
            self._draw_up_arrow(self.up_button_rect, can_scroll_up)

            max_scroll = max(0, self._get_total_rows() - self.max_visible_rows)
            can_scroll_down = self.scroll_offset < max_scroll
            down_color = self.button_color if can_scroll_down else (40, 50, 60)
            pygame.draw.rect(self.screen, down_color, self.down_button_rect, border_radius=12)
            self._draw_down_arrow(self.down_button_rect, can_scroll_down)

        # OK button - green if can deliver, gray if not
        if self.can_deliver:
            ok_color = self.accent_color
        else:
            ok_color = (60, 60, 70)

        pygame.draw.rect(self.screen, ok_color, self.ok_button_rect, border_radius=12)
        self._draw_mask_face(self.ok_button_rect)

    def _draw_up_arrow(self, rect: pygame.Rect, enabled: bool):
        """Draw an up arrow in the button."""
        color = self.text_color if enabled else (80, 90, 100)
        cx = rect.centerx
        cy = rect.centery

        points = [
            (cx, cy - 20),
            (cx - 18, cy + 15),
            (cx + 18, cy + 15)
        ]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_down_arrow(self, rect: pygame.Rect, enabled: bool):
        """Draw a down arrow in the button."""
        color = self.text_color if enabled else (80, 90, 100)
        cx = rect.centerx
        cy = rect.centery

        points = [
            (cx, cy + 20),
            (cx - 18, cy - 15),
            (cx + 18, cy - 15)
        ]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_mask_face(self, rect: pygame.Rect):
        """Draw a mask/face (O.O) in the OK button."""
        cx = rect.centerx
        cy = rect.centery

        face_color = (255, 255, 255)

        # Left eye (O)
        pygame.draw.circle(self.screen, face_color, (cx - 18, cy - 5), 12, 3)
        pygame.draw.circle(self.screen, face_color, (cx - 18, cy - 5), 4)

        # Dot in middle
        pygame.draw.circle(self.screen, face_color, (cx, cy + 8), 4)

        # Right eye (O)
        pygame.draw.circle(self.screen, face_color, (cx + 18, cy - 5), 12, 3)
        pygame.draw.circle(self.screen, face_color, (cx + 18, cy - 5), 4)

    def _draw_celebration(self):
        """Draw the celebration animation with multiple bursts and points display."""
        self.screen.fill((20, 30, 40))

        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Draw all burst animations
        for burst in self.celebration_bursts:
            burst_x = burst["center_x"]
            burst_y = burst["center_y"]
            color = burst["color"]
            alpha = burst["alpha"]
            line_width = 4

            # Create a surface for this burst with alpha support
            for line in burst["lines"]:
                angle = line[0]
                current_length = line[1]

                if current_length > 0:
                    end_x = burst_x + int(math.cos(angle) * current_length)
                    end_y = burst_y + int(math.sin(angle) * current_length)

                    # Draw line with alpha by creating color with adjusted brightness
                    alpha_factor = alpha / 255.0
                    adjusted_color = (
                        int(color[0] * alpha_factor),
                        int(color[1] * alpha_factor),
                        int(color[2] * alpha_factor)
                    )
                    pygame.draw.line(self.screen, adjusted_color, (burst_x, burst_y), (end_x, end_y), line_width)

        # Only show text after animations are mostly done
        if self.celebration_show_text:
            pink_color = (255, 120, 180)
            big_font = pygame.font.Font(None, 120)
            medium_font = pygame.font.Font(None, 72)

            # Semi-transparent background for text readability
            text_bg_rect = pygame.Rect(center_x - 400, center_y - 100, 800, 250)
            text_bg_surface = pygame.Surface((800, 250), pygame.SRCALPHA)
            text_bg_surface.fill((20, 30, 40, 200))
            self.screen.blit(text_bg_surface, text_bg_rect.topleft)

            # Main celebration text
            if self.is_full_delivery:
                main_text = "UPEAA!"
            else:
                main_text = "KIITOS!"

            main_surf = big_font.render(main_text, True, pink_color)
            main_rect = main_surf.get_rect(center=(center_x, center_y - 50))
            self.screen.blit(main_surf, main_rect)

            # Points earned
            points_text = f"+{self.celebration_points} pistettä"
            points_surf = medium_font.render(points_text, True, self.accent_color)
            points_rect = points_surf.get_rect(center=(center_x, center_y + 30))
            self.screen.blit(points_surf, points_rect)

            # Bonus text for full delivery
            if self.is_full_delivery:
                bonus_text = f"(sisältää +{self.full_order_bonus} bonuksen)"
                bonus_surf = self.text_font.render(bonus_text, True, (180, 180, 180))
                bonus_rect = bonus_surf.get_rect(center=(center_x, center_y + 80))
                self.screen.blit(bonus_surf, bonus_rect)

        # Draw close button when user can close
        if self.celebration_can_close:
            # Position close button at bottom right
            button_y = self.screen_height - self.button_size - 30
            button_x = self.screen_width - self.button_size - 40

            self.ok_button_rect = pygame.Rect(button_x, button_y, self.button_size, self.button_size)
            pygame.draw.rect(self.screen, self.accent_color, self.ok_button_rect, border_radius=12)
            self._draw_mask_face(self.ok_button_rect)

            # Hint text
            hint_text = "Paina sulkeaksesi"
            hint_surf = self.small_font.render(hint_text, True, (150, 150, 150))
            hint_rect = hint_surf.get_rect(center=(self.ok_button_rect.centerx, self.ok_button_rect.top - 20))
            self.screen.blit(hint_surf, hint_rect)
