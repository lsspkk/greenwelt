# Map UI components - location indicator, phone buttons, etc.

import pygame
from typing import Optional, Dict

from screens.dialogs.phone import PhoneScreen
from screens.map.order_manager import OrderManager


class MapUI:
    """Handles all UI elements specific to the map screen"""

    def __init__(self, screen: pygame.Surface, order_manager: OrderManager):
        self.screen = screen
        self.order_manager = order_manager
        self.phone = PhoneScreen(screen)    # Phone screen overlay
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 36)

        # Location type display labels
        self.type_labels = {
            "shop": "Kotipuutarha",
            "office": "Toimisto",
            "restaurant": "Ravintola",
            "house": "Talo"
        }

        # Load phone icons (64x64 pixels)
        self.phone_icon = pygame.image.load(
            "assets/ui/phone.png").convert_alpha()
        self.phone_alert_icon = pygame.image.load(
            "assets/ui/phone_alert.png").convert_alpha()

        self.phone_icon_rect = pygame.Rect(32, 112, 64, 64)
        self.phone_icon_border_rect = self.phone_icon_rect.inflate(8, 8)

        # Layout constants
        self.padding = 30
        self.box_height = 80

    def draw(self, map_screen, input_mgr) -> Optional[str]:
        """
        Draw all map UI elements.
        Returns an action string if a button was clicked, None otherwise.
        """
        action = None

        nearby = map_screen.get_nearby_location()
        if nearby:
            self._draw_location_indicator(nearby)

         # If phone is open, handle it first (blocks other UI)
        if self.phone.visible:
            action = self.phone.handle_input(
                input_mgr, self.order_manager)
            self.phone.draw(self.order_manager)
            return action

        # Normal UI when phone is closed
        action = self._draw_phone_icons(input_mgr)
        if action == "open_incoming_orders":
            self.phone.open("incoming")
        elif action == "open_main_phone":
            self.phone.open("accepted")

        return action

    def _draw_location_indicator(self, nearby):
        """Draw the nearby location info box in bottom right"""

        loc_name = nearby["name"]
        loc_type = nearby["type"]
        type_label = self.type_labels.get(loc_type, loc_type)

        # Render text
        name_surf = self.font.render(loc_name, True, (255, 255, 255))
        type_surf = self.small_font.render(
            f"({type_label})", True, (180, 180, 180))

        # Calculate box size and position
        box_w = max(name_surf.get_width(), type_surf.get_width()) + 40
        box_h = self.box_height
        screen_w, screen_h = self.screen.get_size()

        # Position in bottom right, with space for fullscreen button (60px + padding)
        box_x = screen_w - box_w - 60 - self.padding - 10
        box_y = screen_h - box_h - self.padding

        # Draw background box
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (30, 40, 50), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (80, 120, 160),
                         box_rect, 2, border_radius=10)

        # Draw text
        self.screen.blit(name_surf, (box_x + 20, box_y + 15))
        self.screen.blit(type_surf, (box_x + 20, box_y + 48))

    def _draw_phone_icons(self, input_mgr):
        """Draw phone icons and handle clicks. Returns action string or None."""

        color = (80, 80, 100)
        # Only draw alert phone if there are visible orders
        visible_count = self.order_manager.get_visible_count()
        if visible_count > 0:

            pygame.draw.rect(self.screen, color,
                             self.phone_icon_border_rect, border_radius=12)

            self.screen.blit(self.phone_alert_icon,
                             self.phone_icon_rect.topleft)
            self._draw_badge(self.phone_icon_rect, visible_count)

            # Check for click on alert phone
            if input_mgr.clicked_in_rect(self.phone_icon_rect):
                return "open_incoming_orders"
        else:
            pygame.draw.rect(self.screen, color,
                             self.phone_icon_border_rect, border_radius=12)

            self.screen.blit(self.phone_icon, self.phone_icon_rect.topleft)
            # Draw accepted orders count badge
            accepted_count = self.order_manager.get_accepted_count()
            if accepted_count > 0:
                self._draw_badge(self.main_phone_rect, accepted_count)
            # Check for click on main phone
            if input_mgr.clicked_in_rect(self.phone_icon_rect):
                return "open_main_phone"

        return None
