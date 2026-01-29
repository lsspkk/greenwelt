import pygame
from typing import Optional, List
from shared.shared_components import Order, OrderState


class PhoneScreen:
    """
    Phone UI overlay for viewing orders.

    Can be opened in two modes:
    - "incoming": Show visible incoming orders with accept buttons
    - "accepted": Show accepted orders and inventory
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.mode = "accepted"  # "incoming" or "accepted"

        # Phone frame dimensions (centered on screen)
        screen_w, screen_h = screen.get_size()
        phone_w = 600
        phone_h = 800
        self.phone_rect = pygame.Rect(
            (screen_w - phone_w) // 2,
            (screen_h - phone_h) // 2,
            phone_w,
            phone_h
        )

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)

        # Colors
        self.bg_color = (40, 44, 52)
        self.header_color = (60, 64, 72)
        self.text_color = (255, 255, 255)
        self.accent_color = (100, 180, 100)

    def open(self, mode: str = "accepted"):
        """Open the phone screen."""
        self.mode = mode
        self.visible = True

    def close(self):
        """Close the phone screen."""
        self.visible = False

    def handle_input(self, input_mgr, order_manager) -> Optional[str]:
        """
        Handle input while phone is open.
        Returns action string or None.
        """
        if not self.visible:
            return None

        # Close button (top right of phone)
        close_rect = pygame.Rect(
            self.phone_rect.right - 50,
            self.phone_rect.top + 10,
            40, 40
        )
        if input_mgr.clicked_in_rect(close_rect):
            self.close()
            return "phone_closed"

        # TODO: Handle order item clicks
        # TODO: Handle accept button clicks

        return None

    def draw(self, order_manager):
        """Draw the phone screen."""
        if not self.visible:
            return

        # Dim background
        dim_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 150))
        self.screen.blit(dim_surface, (0, 0))

        # Phone background
        pygame.draw.rect(self.screen, self.bg_color,
                         self.phone_rect, border_radius=20)
        pygame.draw.rect(self.screen, self.header_color,
                         self.phone_rect, 3, border_radius=20)

        # Header
        header_rect = pygame.Rect(
            self.phone_rect.x,
            self.phone_rect.y,
            self.phone_rect.width,
            60
        )
        pygame.draw.rect(self.screen, self.header_color, header_rect,
                         border_top_left_radius=20, border_top_right_radius=20)

        # Title and glyphs
        if self.mode == "incoming":
            title = "@)--,--⁻-- Viestit"
            self._draw_incoming_orders(order_manager)
            glyph_type = "phone"
        else:
            title = "@)--,--⁻-- Tilaukset"
            self._draw_accepted_orders(order_manager)
            glyph_type = "flower"

        # Draw glyph (phone or flower) to left of title
        glyph_x = self.phone_rect.x + 20
        glyph_y = self.phone_rect.y + 15
        if glyph_type == "phone":
            # Draw a simple phone glyph (handset)
            # Handset body
            pygame.draw.arc(self.screen, (180, 220, 180),
                            (glyph_x, glyph_y, 32, 32), 3.8, 5.5, 5)
            # Left earpiece
            pygame.draw.circle(self.screen, (180, 220, 180),
                               (glyph_x + 6, glyph_y + 26), 5)
            # Right mouthpiece
            pygame.draw.circle(self.screen, (180, 220, 180),
                               (glyph_x + 26, glyph_y + 6), 5)
        elif glyph_type == "flower":
            # Draw a simple flower glyph
            center = (glyph_x + 16, glyph_y + 16)
            petal_color = (220, 180, 220)
            center_color = (200, 220, 120)
            for angle in range(0, 360, 72):
                rad = angle * 3.14159 / 180
                px = int(center[0] + 12 *
                         pygame.math.Vector2(1, 0).rotate(angle).x)
                py = int(center[1] + 12 *
                         pygame.math.Vector2(1, 0).rotate(angle).y)
                pygame.draw.ellipse(self.screen, petal_color,
                                    (px-6, py-10, 12, 20))
            pygame.draw.circle(self.screen, center_color, center, 7)

        # Draw the title text to the right of the glyph
        title_surf = self.title_font.render(title, True, self.text_color)
        self.screen.blit(title_surf, (self.phone_rect.x +
                         60, self.phone_rect.y + 15))

        # Close button (X)
        close_rect = pygame.Rect(
            self.phone_rect.right - 50, self.phone_rect.top + 10, 40, 40)
        pygame.draw.rect(self.screen, (80, 40, 40),
                         close_rect, border_radius=5)
        close_text = self.font.render("X", True, (200, 200, 200))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.screen.blit(close_text, close_text_rect)

    def _draw_incoming_orders(self, order_manager):
        """Draw list of visible incoming orders."""
        orders = order_manager.visible_orders
        y = self.phone_rect.y + 80

        if not orders:
            no_orders = self.font.render(
                "Ei uusia tilauksia", True, (150, 150, 150))
            self.screen.blit(no_orders, (self.phone_rect.x + 20, y))
            return

        for order in orders:
            self._draw_order_card(order, y, show_timer=True)
            y += 120

    def _draw_accepted_orders(self, order_manager):
        """Draw list of accepted orders."""
        orders = order_manager.accepted_orders
        y = self.phone_rect.y + 80

        if not orders:
            no_orders = self.font.render(
                "Ei hyväksyttyjä tilauksia", True, (150, 150, 150))
            self.screen.blit(no_orders, (self.phone_rect.x + 20, y))
            return

        for order in orders:
            self._draw_order_card(order, y, show_timer=False)
            y += 120

    def _draw_order_card(self, order: Order, y: int, show_timer: bool):
        """Draw a single order card."""
        card_rect = pygame.Rect(
            self.phone_rect.x + 15,
            y,
            self.phone_rect.width - 30,
            100
        )

        # Card background
        pygame.draw.rect(self.screen, (50, 54, 62),
                         card_rect, border_radius=10)

        # Customer name
        name_surf = self.font.render(
            order.customer_location, True, self.text_color)
        self.screen.blit(name_surf, (card_rect.x + 15, card_rect.y + 10))

        # Plant count
        plant_count = sum(p.amount for p in order.plants)
        plants_text = f"{plant_count} kasvia"
        plants_surf = self.small_font.render(
            plants_text, True, (180, 180, 180))
        self.screen.blit(plants_surf, (card_rect.x + 15, card_rect.y + 45))

        # Timer bar (for incoming orders)
        if show_timer and order.countdown_to_available > 0:
            timer_width = 200
            timer_height = 8
            timer_x = card_rect.x + 15
            timer_y = card_rect.y + 75

            # Background bar
            pygame.draw.rect(self.screen, (30, 30, 30),
                             (timer_x, timer_y, timer_width, timer_height),
                             border_radius=4)

            # Fill bar (based on remaining time)
            # Assume max accept_time is stored or use a default
            max_time = 15.0  # Could get this from order_manager.accept_time
            fill_ratio = order.countdown_to_available / max_time
            fill_width = int(timer_width * fill_ratio)

            # Color changes from green to red
            if fill_ratio > 0.5:
                bar_color = (100, 180, 100)
            elif fill_ratio > 0.25:
                bar_color = (200, 180, 50)
            else:
                bar_color = (200, 80, 80)

            pygame.draw.rect(self.screen, bar_color,
                             (timer_x, timer_y, fill_width, timer_height),
                             border_radius=4)
