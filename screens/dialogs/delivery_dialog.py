# Delivery dialog - full screen dialog for delivering orders
import pygame
from pathlib import Path
from typing import Optional, List
from shared.shared_components import Order, PlantOrder
from shared.debug_log import debug


class DeliveryDialog:
    """
    Full screen delivery dialog shown when player arrives at delivery location.

    Layout:
    - Top left: Location name
    - Top left (right of name): Face graphics
    - Top right: "Toimituksenne, olkaa hyvä!"
    - Middle: List of order items (text left, plant images right)
    - Bottom right: Up arrow, Down arrow (scroll), Mask face (OK/complete)
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.visible = False
        self.order: Optional[Order] = None
        self.location_name = ""

        # Scroll state for order rows
        self.scroll_offset = 0
        self.max_visible_rows = 5

        # Fonts
        self.title_font = pygame.font.Font(None, 64)
        self.header_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 52)

        # Colors
        self.bg_color = (30, 40, 50)
        self.header_bg_color = (40, 55, 70)
        self.text_color = (255, 255, 255)
        self.secondary_text_color = (180, 180, 180)
        self.button_color = (60, 80, 100)
        self.button_hover_color = (80, 100, 120)
        self.accent_color = (100, 180, 120)

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

        # Calculate plant area width to fit 7 plants
        self.plant_area_width = self.max_plants_per_row * (self.plant_size + 8) + 20

        # Cache for loaded plant images
        self.plant_image_cache = {}

        # Callback for when order is completed
        self.on_order_completed = None

    def open(self, order: Order, location_name: str):
        """Open the delivery dialog for an order."""
        self.order = order
        self.location_name = location_name
        self.scroll_offset = 0
        self.visible = True
        debug.info(f"DeliveryDialog opened for {location_name}")

    def close(self):
        """Close the delivery dialog."""
        self.visible = False
        self.order = None
        self.location_name = ""
        debug.info("DeliveryDialog closed")

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        plant_path = Path(__file__).parent.parent.parent / "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            # Scale to plant_size
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
        """Mark the order as completed."""
        if self.order is not None:
            debug.info(f"Order {self.order.order_id} completed via delivery dialog")
            if self.on_order_completed:
                self.on_order_completed(self.order)
        self.close()

    def handle_input(self, input_mgr) -> Optional[str]:
        """
        Handle input while dialog is open.
        Returns action string or None.
        """
        if not self.visible:
            return None

        # Check scroll buttons
        if input_mgr.clicked_in_rect(self.up_button_rect):
            self._scroll_up()
            return "scroll_up"

        if input_mgr.clicked_in_rect(self.down_button_rect):
            self._scroll_down()
            return "scroll_down"

        # Check OK button
        if input_mgr.clicked_in_rect(self.ok_button_rect):
            self._complete_order()
            return "order_completed"

        return None

    def draw(self):
        """Draw the full delivery dialog."""
        if not self.visible:
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
        """Draw the header section with location name, face, and title."""
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

        # "Toimituksenne, olkaa hyvä!" (top right)
        delivery_text = "Toimituksenne, olkaa hyvä!"
        delivery_surf = self.header_font.render(delivery_text, True, self.accent_color)
        delivery_x = self.screen_width - delivery_surf.get_width() - 40
        self.screen.blit(delivery_surf, (delivery_x, 40))

    def _draw_face(self, x: int, y: int):
        """Draw a simple happy face next to the location name."""
        # Face circle (yellow)
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

        # Smile
        smile_rect = pygame.Rect(cx - 15, cy - 5, 30, 25)
        pygame.draw.arc(self.screen, (60, 40, 30), smile_rect, 3.5, 6.0, 3)

        # Rosy cheeks
        pygame.draw.circle(self.screen, (255, 160, 120), (cx - 18, cy + 5), 5)
        pygame.draw.circle(self.screen, (255, 160, 120), (cx + 18, cy + 5), 5)

    def _draw_order_rows(self):
        """Draw the list of order items."""
        if self.order is None:
            return

        # Calculate content area
        content_y = self.header_height + 20
        content_height = self.screen_height - self.header_height - 140  # Leave space for buttons

        # Calculate how many rows we can show
        visible_rows = min(self.max_visible_rows, len(self.order.plants))

        # Draw each visible row
        for i in range(visible_rows):
            plant_index = i + self.scroll_offset
            if plant_index >= len(self.order.plants):
                break

            plant = self.order.plants[plant_index]
            row_y = content_y + i * self.row_height

            self._draw_order_row(plant, row_y, plant_index + 1)

    def _draw_order_row(self, plant: PlantOrder, y: int, row_number: int):
        """Draw a single order row with text on left and plant images on right."""
        # Row background
        row_rect = pygame.Rect(20, y, self.screen_width - 40, self.row_height - 10)
        pygame.draw.rect(self.screen, (45, 55, 65), row_rect, border_radius=12)

        # Left side: Plant info text
        text_x = 40
        text_y = y + 15

        # Row number and plant name
        name_text = f"{row_number}. {plant.name_fi}"
        name_surf = self.text_font.render(name_text, True, self.text_color)
        self.screen.blit(name_surf, (text_x, text_y))

        # Amount text
        amount_text = f"Määrä: {plant.amount} kpl"
        amount_surf = self.text_font.render(amount_text, True, self.secondary_text_color)
        self.screen.blit(amount_surf, (text_x, text_y + 35))

        # English name
        en_text = f"({plant.name_en})"
        en_surf = self.text_font.render(en_text, True, (120, 120, 120))
        self.screen.blit(en_surf, (text_x, text_y + 65))

        # Right side: Plant images
        plant_image = self._load_plant_image(plant.filename)
        if plant_image is not None:
            # Calculate starting x position for plants (right aligned)
            plants_start_x = self.screen_width - self.plant_area_width - 20

            # Draw plant images based on amount (max 7)
            plants_to_draw = min(plant.amount, self.max_plants_per_row)
            for j in range(plants_to_draw):
                img_x = plants_start_x + j * (self.plant_size + 8)
                img_y = y + (self.row_height - self.plant_size) // 2 - 5
                self.screen.blit(plant_image, (img_x, img_y))

            # If more than 7, show "+X" indicator
            if plant.amount > self.max_plants_per_row:
                extra_count = plant.amount - self.max_plants_per_row
                extra_text = f"+{extra_count}"
                extra_surf = self.text_font.render(extra_text, True, self.accent_color)
                extra_x = plants_start_x + self.max_plants_per_row * (self.plant_size + 8) + 5
                extra_y = y + self.row_height // 2 - 10
                self.screen.blit(extra_surf, (extra_x, extra_y))

    def _draw_buttons(self):
        """Draw the bottom right buttons: up, down, and OK."""
        # Button area in bottom right
        button_y = self.screen_height - self.button_size - 30
        button_x_start = self.screen_width - (self.button_size * 3 + self.button_margin * 2) - 40

        # Up arrow button
        self.up_button_rect = pygame.Rect(
            button_x_start,
            button_y,
            self.button_size,
            self.button_size
        )

        # Down arrow button
        self.down_button_rect = pygame.Rect(
            button_x_start + self.button_size + self.button_margin,
            button_y,
            self.button_size,
            self.button_size
        )

        # OK (mask face) button
        self.ok_button_rect = pygame.Rect(
            button_x_start + (self.button_size + self.button_margin) * 2,
            button_y,
            self.button_size,
            self.button_size
        )

        needs_scroll = self._needs_scroll()

        # Draw scroll buttons only if needed
        if needs_scroll:
            # Up button
            can_scroll_up = self.scroll_offset > 0
            up_color = self.button_color if can_scroll_up else (40, 50, 60)
            pygame.draw.rect(self.screen, up_color, self.up_button_rect, border_radius=12)
            self._draw_up_arrow(self.up_button_rect, can_scroll_up)

            # Down button
            max_scroll = max(0, self._get_total_rows() - self.max_visible_rows)
            can_scroll_down = self.scroll_offset < max_scroll
            down_color = self.button_color if can_scroll_down else (40, 50, 60)
            pygame.draw.rect(self.screen, down_color, self.down_button_rect, border_radius=12)
            self._draw_down_arrow(self.down_button_rect, can_scroll_down)

        # OK button (always shown)
        pygame.draw.rect(self.screen, self.accent_color, self.ok_button_rect, border_radius=12)
        self._draw_mask_face(self.ok_button_rect)

    def _draw_up_arrow(self, rect: pygame.Rect, enabled: bool):
        """Draw an up arrow in the button."""
        color = self.text_color if enabled else (80, 90, 100)
        cx = rect.centerx
        cy = rect.centery

        # Triangle pointing up
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

        # Triangle pointing down
        points = [
            (cx, cy + 20),
            (cx - 18, cy - 15),
            (cx + 18, cy - 15)
        ]
        pygame.draw.polygon(self.screen, color, points)

    def _draw_mask_face(self, rect: pygame.Rect):
        """Draw a mask/happy face (O.O) in the OK button."""
        cx = rect.centerx
        cy = rect.centery

        # Face color
        face_color = (255, 255, 255)

        # Draw simple face: (O.O)
        # Left eye (O)
        pygame.draw.circle(self.screen, face_color, (cx - 18, cy - 5), 12, 3)
        pygame.draw.circle(self.screen, face_color, (cx - 18, cy - 5), 4)

        # Dot in middle
        pygame.draw.circle(self.screen, face_color, (cx, cy + 8), 4)

        # Right eye (O)
        pygame.draw.circle(self.screen, face_color, (cx + 18, cy - 5), 12, 3)
        pygame.draw.circle(self.screen, face_color, (cx + 18, cy - 5), 4)
