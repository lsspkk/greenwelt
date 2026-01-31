# Phone screen for viewing VISIBLE order details before accepting

import pygame
import random
from typing import Optional
from shared.shared_components import Order
from shared.debug_log import debug


class PhoneVisibleOrderScreen:
    """
    Screen that shows text descriptions of plants in a VISIBLE order.

    User sees plant_text and amount_text for each plant, but NOT the image.
    User can navigate between plants and click OK to accept the order.

    Displays inside the phone frame with:
    - Location name at top
    - Decorative lines
    - Plant text (what plant is wanted)
    - Amount text (how many are wanted)
    - Page indicator (e.g., "1/3")
    - Bottom navbar with: <= (prev), OK (accept), => (next)
    """

    def __init__(self, phone_rect: pygame.Rect):
        self.phone_rect = phone_rect
        self.visible = False
        self.order: Optional[Order] = None
        self.current_plant_index = 0

        # Random colors for the decorative lines
        self.top_line_color = (100, 150, 100)
        self.bottom_line_color = (100, 130, 100)

        # Fonts
        self.title_font = pygame.font.Font(None, 42)
        self.text_font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 28)
        self.button_font = pygame.font.Font(None, 32)

        # Colors
        self.bg_color = (40, 44, 52)
        self.text_color = (255, 255, 255)
        self.text_secondary_color = (200, 200, 200)
        self.button_color = (70, 74, 82)
        self.ok_button_color = (80, 160, 80)
        self.disabled_color = (50, 54, 62)
        self.disabled_text_color = (100, 100, 100)

        # Button rects (set during draw)
        self.prev_button_rect = pygame.Rect(0, 0, 0, 0)
        self.next_button_rect = pygame.Rect(0, 0, 0, 0)
        self.ok_button_rect = pygame.Rect(0, 0, 0, 0)
        self.back_button_rect = pygame.Rect(0, 0, 0, 0)

        # Flag to signal order was accepted
        self.accepted_order: Optional[Order] = None

    def open(self, order: Order):
        """Open the screen showing the first plant of the order."""
        self.order = order
        self.current_plant_index = 0
        self.visible = True
        self.accepted_order = None
        self._generate_random_colors()
        debug.info(f"PhoneVisibleOrderScreen opened for order {order.order_id}")

    def close(self):
        """Close this screen and return to order list."""
        self.visible = False
        self.order = None

    def _generate_random_colors(self):
        """Generate random colors for the decorative lines."""
        self.top_line_color = (
            random.randint(80, 180),
            random.randint(120, 200),
            random.randint(80, 180)
        )
        self.bottom_line_color = (
            random.randint(80, 180),
            random.randint(120, 200),
            random.randint(80, 180)
        )

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

    def accept_order(self):
        """Accept the current order."""
        if self.order is not None:
            self.accepted_order = self.order
            debug.info(f"Order accepted via visible screen: {self.order.order_id}")

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

        # Check OK button (accept order)
        if input_mgr.clicked_in_rect(self.ok_button_rect):
            self.accept_order()
            self.close()
            return "order_accepted"

        # Check back button (cancel without accepting)
        if input_mgr.clicked_in_rect(self.back_button_rect):
            self.close()
            return "back_to_orders"

        return None

    def draw(self, screen: pygame.Surface):
        """Draw the visible order plant text view."""
        if not self.visible or self.order is None:
            return

        if len(self.order.plants) == 0:
            return

        # Get current plant
        plant = self.order.plants[self.current_plant_index]

        # Calculate areas within phone
        content_x = self.phone_rect.x + 20
        content_y = self.phone_rect.y + 80  # Below phone header
        content_width = self.phone_rect.width - 40

        navbar_height = 120
        navbar_y = self.phone_rect.bottom - navbar_height - 10

        # Draw order location name at top
        location_surf = self.title_font.render(
            self.order.customer_location, True, self.text_color)
        location_rect = location_surf.get_rect(
            centerx=self.phone_rect.centerx, top=content_y)
        screen.blit(location_surf, location_rect)

        # Draw top decorative line below location
        line_height = 6
        line_y = content_y + 50
        pygame.draw.rect(
            screen,
            self.top_line_color,
            (content_x, line_y, content_width, line_height),
            border_radius=3
        )

        # Calculate text area
        text_area_y = line_y + line_height + 30
        bottom_line_y = navbar_y - 30 - line_height

        # Draw plant text (what plant is wanted)
        plant_text = plant.plant_text
        if not plant_text:
            plant_text = f"Haluan {plant.name_fi} -kasvin."

        # Word wrap the plant text
        wrapped_plant_lines = self._wrap_text(plant_text, content_width - 20)
        current_y = text_area_y

        for line in wrapped_plant_lines:
            line_surf = self.text_font.render(line, True, self.text_color)
            line_rect = line_surf.get_rect(centerx=self.phone_rect.centerx, top=current_y)
            screen.blit(line_surf, line_rect)
            current_y += 40

        # Draw amount text (how many)
        amount_text = plant.amount_text
        if not amount_text:
            amount_text = f"Määrä: {plant.amount} kpl"

        # Add some space before amount text
        current_y += 30

        wrapped_amount_lines = self._wrap_text(amount_text, content_width - 20)
        for line in wrapped_amount_lines:
            line_surf = self.text_font.render(line, True, self.text_secondary_color)
            line_rect = line_surf.get_rect(centerx=self.phone_rect.centerx, top=current_y)
            screen.blit(line_surf, line_rect)
            current_y += 40

        # Draw page indicator
        page_text = f"{self.current_plant_index + 1}/{len(self.order.plants)}"
        page_surf = self.small_font.render(page_text, True, (150, 150, 150))
        page_rect = page_surf.get_rect(
            centerx=self.phone_rect.centerx,
            bottom=bottom_line_y - 10
        )
        screen.blit(page_surf, page_rect)

        # Draw bottom decorative line
        pygame.draw.rect(
            screen,
            self.bottom_line_color,
            (content_x, bottom_line_y, content_width, line_height),
            border_radius=3
        )

        # Draw navbar with buttons
        self._draw_navbar(screen, navbar_y)

    def _wrap_text(self, text: str, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surf = self.text_font.render(test_line, True, (255, 255, 255))

            if test_surf.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _draw_navbar(self, screen: pygame.Surface, navbar_y: int):
        """Draw the bottom navigation bar with prev, OK, next, and back buttons."""
        button_height = 60
        button_margin = 20

        # Calculate button positions - 4 buttons now
        small_button_width = 60
        ok_button_width = 90

        # Layout: [<=] [X] [OK] [=>]
        total_width = small_button_width * 3 + ok_button_width + button_margin * 3
        start_x = self.phone_rect.x + (self.phone_rect.width - total_width) // 2

        # Prev button (<=)
        self.prev_button_rect = pygame.Rect(
            start_x,
            navbar_y,
            small_button_width,
            button_height
        )

        prev_enabled = self.current_plant_index > 0
        prev_color = self.button_color if prev_enabled else self.disabled_color
        prev_text_color = self.text_color if prev_enabled else self.disabled_text_color

        pygame.draw.rect(screen, prev_color, self.prev_button_rect, border_radius=8)
        prev_text = self.button_font.render("<=", True, prev_text_color)
        prev_text_rect = prev_text.get_rect(center=self.prev_button_rect.center)
        screen.blit(prev_text, prev_text_rect)

        # Back button (X) - cancel without accepting
        self.back_button_rect = pygame.Rect(
            start_x + small_button_width + button_margin,
            navbar_y,
            small_button_width,
            button_height
        )

        pygame.draw.rect(screen, self.button_color, self.back_button_rect, border_radius=8)
        back_text = self.button_font.render("X", True, self.text_color)
        back_text_rect = back_text.get_rect(center=self.back_button_rect.center)
        screen.blit(back_text, back_text_rect)

        # OK button (accept order)
        self.ok_button_rect = pygame.Rect(
            start_x + (small_button_width + button_margin) * 2,
            navbar_y,
            ok_button_width,
            button_height
        )

        pygame.draw.rect(screen, self.ok_button_color, self.ok_button_rect, border_radius=8)
        ok_text = self.button_font.render("OK", True, self.text_color)
        ok_text_rect = ok_text.get_rect(center=self.ok_button_rect.center)
        screen.blit(ok_text, ok_text_rect)

        # Next button (=>)
        self.next_button_rect = pygame.Rect(
            start_x + (small_button_width + button_margin) * 2 + ok_button_width + button_margin,
            navbar_y,
            small_button_width,
            button_height
        )

        next_enabled = self.order is not None and self.current_plant_index < len(self.order.plants) - 1
        next_color = self.button_color if next_enabled else self.disabled_color
        next_text_color = self.text_color if next_enabled else self.disabled_text_color

        pygame.draw.rect(screen, next_color, self.next_button_rect, border_radius=8)
        next_text = self.button_font.render("=>", True, next_text_color)
        next_text_rect = next_text.get_rect(center=self.next_button_rect.center)
        screen.blit(next_text, next_text_rect)
