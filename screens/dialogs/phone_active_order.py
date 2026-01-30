import pygame
import random
from pathlib import Path
from typing import Optional
from shared.shared_components import Order
from shared.debug_log import debug


class PhoneActiveOrderScreen:
    """
    Screen that shows plants of an active order one at a time.

    Displays inside the phone frame with:
    - Random colored lines at top and bottom
    - Plant image scaled to fit
    - Plant name and amount below the image
    - Bottom navbar with: <- (prev), Takaisin (back), -> (next)
    """

    def __init__(self, phone_rect: pygame.Rect):
        self.phone_rect = phone_rect
        self.visible = False
        self.order: Optional[Order] = None
        self.current_plant_index = 0

        # Random colors for the decorative lines (generated fresh each time)
        self.top_line_color = (100, 100, 100)
        self.bottom_line_color = (100, 100, 100)

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.name_font = pygame.font.Font(None, 42)
        self.amount_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 32)

        # Colors
        self.bg_color = (40, 44, 52)
        self.text_color = (255, 255, 255)
        self.button_color = (70, 74, 82)
        self.button_hover_color = (90, 94, 102)

        # Cache for loaded plant images
        self.plant_image_cache = {}

        # Button rects (set during draw)
        self.prev_button_rect = pygame.Rect(0, 0, 0, 0)
        self.next_button_rect = pygame.Rect(0, 0, 0, 0)
        self.back_button_rect = pygame.Rect(0, 0, 0, 0)

    def open(self, order: Order):
        """Open the screen showing the first plant of the order."""
        self.order = order
        self.current_plant_index = 0
        self.visible = True
        self._generate_random_colors()
        debug.info(f"PhoneActiveOrderScreen opened for order {order.order_id}")

    def close(self):
        """Close this screen and return to order list."""
        self.visible = False
        self.order = None

    def _generate_random_colors(self):
        """Generate random colors for the decorative lines."""
        # Generate bright, varied colors
        self.top_line_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        self.bottom_line_color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        # Build path to plant image
        plant_path = Path(__file__).parent.parent.parent / "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            self.plant_image_cache[filename] = image
            debug.info(f"Loaded plant image: {filename}")
            return image
        except Exception as e:
            debug.error(f"Failed to load plant image {filename}: {e}")
            return None

    def _scale_image_to_fit(self, image: pygame.Surface, max_width: int, max_height: int) -> pygame.Surface:
        """Scale image to fit within bounds while maintaining aspect ratio."""
        img_width = image.get_width()
        img_height = image.get_height()

        # Calculate scale factor
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale = min(width_ratio, height_ratio)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        return pygame.transform.smoothscale(image, (new_width, new_height))

    def show_previous(self):
        """Show the previous plant in the order."""
        if self.order is None:
            return

        if self.current_plant_index > 0:
            self.current_plant_index -= 1
            self._generate_random_colors()

    def show_next(self):
        """Show the next plant in the order."""
        if self.order is None:
            return

        if self.current_plant_index < len(self.order.plants) - 1:
            self.current_plant_index += 1
            self._generate_random_colors()

    def handle_input(self, input_mgr) -> Optional[str]:
        """
        Handle input while this screen is open.
        Returns action string or None.
        """
        if not self.visible:
            return None

        # Check prev button
        if input_mgr.clicked_in_rect(self.prev_button_rect):
            self.show_previous()
            return "prev_plant"

        # Check next button
        if input_mgr.clicked_in_rect(self.next_button_rect):
            self.show_next()
            return "next_plant"

        # Check back button
        if input_mgr.clicked_in_rect(self.back_button_rect):
            self.close()
            return "back_to_orders"

        return None

    def draw(self, screen: pygame.Surface):
        """Draw the active order plant view."""
        if not self.visible or self.order is None:
            return

        if len(self.order.plants) == 0:
            return

        # Get current plant
        plant = self.order.plants[self.current_plant_index]

        # Calculate areas within phone
        content_x = self.phone_rect.x + 20
        content_y = self.phone_rect.y + 70  # Below phone header
        content_width = self.phone_rect.width - 40

        navbar_height = 70
        navbar_y = self.phone_rect.bottom - navbar_height - 10

        # Draw order location name at top
        location_surf = self.name_font.render(self.order.customer_location, True, self.text_color)
        location_rect = location_surf.get_rect(centerx=self.phone_rect.centerx, top=content_y)
        screen.blit(location_surf, location_rect)

        # Draw top decorative line below location
        line_height = 8
        line_y = content_y + 50
        pygame.draw.rect(
            screen,
            self.top_line_color,
            (content_x, line_y, content_width, line_height),
            border_radius=4
        )

        # Calculate image area (between top line and text area)
        image_area_y = line_y + line_height + 20
        text_area_height = 100  # Space for name and amount
        bottom_line_y = navbar_y - 20 - line_height
        image_area_height = bottom_line_y - image_area_y - text_area_height - 20

        # Load and draw plant image
        plant_image = self._load_plant_image(plant.filename)
        if plant_image is not None:
            scaled_image = self._scale_image_to_fit(
                plant_image,
                content_width - 40,
                image_area_height
            )

            # Center the image
            img_x = content_x + (content_width - scaled_image.get_width()) // 2
            img_y = image_area_y + (image_area_height - scaled_image.get_height()) // 2
            screen.blit(scaled_image, (img_x, img_y))
        else:
            # Draw placeholder if image not found
            placeholder_rect = pygame.Rect(
                content_x + 50,
                image_area_y + 20,
                content_width - 100,
                image_area_height - 40
            )
            pygame.draw.rect(screen, (60, 64, 72), placeholder_rect, border_radius=10)
            placeholder_text = self.name_font.render("(kuva puuttuu)", True, (150, 150, 150))
            text_rect = placeholder_text.get_rect(center=placeholder_rect.center)
            screen.blit(placeholder_text, text_rect)

        # Draw plant name
        text_y = bottom_line_y - text_area_height
        plant_name_text = f"{plant.name_fi} {plant.amount} kpl"

        name_surf = self.name_font.render(plant_name_text, True, self.text_color)
        name_rect = name_surf.get_rect(centerx=self.phone_rect.centerx, top=text_y)
        screen.blit(name_surf, name_rect)

        # Draw bottom decorative line
        pygame.draw.rect(
            screen,
            self.bottom_line_color,
            (content_x, bottom_line_y, content_width, line_height),
            border_radius=4
        )

        # Draw navbar
        self._draw_navbar(screen, navbar_y)

    def _draw_navbar(self, screen: pygame.Surface, navbar_y: int):
        """Draw the bottom navigation bar with prev, back, and next buttons."""
        button_height = 50
        button_margin = 15

        # Calculate button positions
        navbar_width = self.phone_rect.width - 40
        button_width = (navbar_width - button_margin * 2) // 3

        start_x = self.phone_rect.x + 20

        # Prev button (<-)
        self.prev_button_rect = pygame.Rect(
            start_x,
            navbar_y,
            button_width,
            button_height
        )

        # Determine if button should be disabled
        prev_enabled = self.current_plant_index > 0
        prev_color = self.button_color if prev_enabled else (50, 54, 62)
        prev_text_color = self.text_color if prev_enabled else (100, 100, 100)

        pygame.draw.rect(screen, prev_color, self.prev_button_rect, border_radius=8)
        prev_text = self.button_font.render("<=]", True, prev_text_color)
        prev_text_rect = prev_text.get_rect(center=self.prev_button_rect.center)
        screen.blit(prev_text, prev_text_rect)

        # Back button (Takaisin)
        self.back_button_rect = pygame.Rect(
            start_x + button_width + button_margin,
            navbar_y,
            button_width,
            button_height
        )

        pygame.draw.rect(screen, self.button_color, self.back_button_rect, border_radius=8)
        back_text = self.button_font.render("_o.o_", True, self.text_color)
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        screen.blit(back_text, back_text_rect)

        # Next button (->)
        self.next_button_rect = pygame.Rect(
            start_x + (button_width + button_margin) * 2,
            navbar_y,
            button_width,
            button_height
        )

        # Determine if button should be disabled
        next_enabled = self.order is not None and self.current_plant_index < len(self.order.plants) - 1
        next_color = self.button_color if next_enabled else (50, 54, 62)
        next_text_color = self.text_color if next_enabled else (100, 100, 100)

        pygame.draw.rect(screen, next_color, self.next_button_rect, border_radius=8)
        next_text = self.button_font.render("[=>", True, next_text_color)
        next_text_rect = next_text.get_rect(center=self.next_button_rect.center)
        screen.blit(next_text, next_text_rect)
