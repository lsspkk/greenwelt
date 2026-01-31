# Map UI components - location indicator, phone buttons, player portrait, etc.

import random
import pygame
from typing import Optional, Dict

from screens.dialogs.phone import PhoneScreen
from screens.dialogs.delivery_dialog import DeliveryDialog
from screens.map.order_manager import OrderManager
from shared.shared_components import Order


class MapUI:
    """Handles all UI elements specific to the map screen"""

    def __init__(self, screen: pygame.Surface, order_manager: OrderManager):
        self.screen = screen
        self.order_manager = order_manager
        self.phone = PhoneScreen(screen)    # Phone screen overlay
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 36)
        self.emoji_font = pygame.font.Font(None, 56)

        # Location type display labels
        self.type_labels = {
            "shop": "Kotipuutarha",
            "office": "Toimisto",
            "restaurant": "Ravintola",
            "house": "Talo"
        }

        # Player portrait - stores the selfie image or None for default emoji
        self.player_portrait: Optional[pygame.Surface] = None
        self.portrait_rect = pygame.Rect(24, 24, 72, 72)
        self.portrait_border = self.portrait_rect.inflate(8, 8)

        # Load phone icons (64x64 pixels)
        self.phone_icon = pygame.image.load(
            "assets/ui/phone.png").convert_alpha()
        self.phone_alert_icon = pygame.image.load(
            "assets/ui/phone_alert.png").convert_alpha()

        # Top icon: accepted orders (main phone) - moved down to make room for portrait
        self.accepted_phone_rect = pygame.Rect(32, 120, 84, 84)
        self.accepted_phone_border = self.accepted_phone_rect.inflate(12, 12)
        self.phone_icon = pygame.transform.smoothscale(
            self.phone_icon, (84, 84))
        # Below: incoming orders (alert phone)
        self.incoming_phone_rect = pygame.Rect(32, 250, 84, 84)
        self.incoming_phone_border = self.incoming_phone_rect.inflate(12, 12)
        self.phone_alert_icon = pygame.transform.smoothscale(
            self.phone_alert_icon, (84, 84))

        # Greenhouse icon (when near greenhouse location)
        index = random.randint(1, 3)
        icon_path = f"assets/ui/greenhouse{index}-icon.png"
        self.greenhouse_icon = pygame.image.load(icon_path).convert_alpha()
        self.greenhouse_icon = pygame.transform.smoothscale(
            self.greenhouse_icon, (84, 84))
        self.greenhouse_icon_rect = pygame.Rect(32, 380, 84, 84)
        self.greenhouse_icon_border = self.greenhouse_icon_rect.inflate(12, 12)

        # Door button (below accepted phone icon) - for delivery when at order location
        self.door_button_rect = pygame.Rect(32, 220, 84, 84)
        self.door_button_border = self.door_button_rect.inflate(12, 12)

        # Delivery dialog
        self.delivery_dialog = DeliveryDialog(screen)
        self.delivery_dialog.on_order_completed = self._on_order_completed

        # Layout constants
        self.padding = 30
        self.box_height = 80

        # Track nearby location for delivery check
        self.current_nearby_location: Optional[Dict] = None

        # Set up phone callbacks
        self.phone.on_camera_click = self._on_camera_click

    def set_player_portrait(self, image: pygame.Surface):
        """Set the player portrait from a captured selfie."""
        # Scale to fit portrait size
        scaled = pygame.transform.smoothscale(image, (72, 72))
        self.player_portrait = scaled

    def _on_camera_click(self):
        """Called when camera button is clicked on the phone."""
        # This would trigger the camera capture via JavaScript in WASM
        # For now, just log it - the actual implementation requires JS integration
        from shared.debug_log import debug
        debug.info("Camera button clicked - selfie capture requested")

    def _on_order_completed(self, order: Order):
        """Called when an order is completed via delivery dialog."""
        from shared.debug_log import debug
        plants_count = sum(p.amount for p in order.plants)
        self.order_manager.complete_order(order, plants_count)
        debug.info(
            f"Order {order.order_id} completed with {plants_count} plants")

    def _get_order_for_location(self, location_name: str) -> Optional[Order]:
        """Get accepted order for a specific location, if any."""
        for order in self.order_manager.accepted_orders:
            if order.customer_location == location_name:
                return order
        return None

    def draw(self, map_screen, input_mgr) -> Optional[str]:
        """
        Draw all map UI elements.
        Returns an action string if a button was clicked, None otherwise.
        """
        action = None

        nearby = map_screen.get_nearby_location()
        self.current_nearby_location = nearby
        if nearby:
            self._draw_location_indicator(nearby)

        self._draw_greenhouse_icon()

        # If delivery dialog is open, handle it (blocks other UI)
        if self.delivery_dialog.visible:
            self.delivery_dialog.draw()
            action = self.delivery_dialog.handle_input(input_mgr)
            return action

        # If phone is open, handle it (blocks other UI)
        # Draw first to populate accept_buttons, then handle input
        if self.phone.visible:
            self.phone.draw(self.order_manager)
            action = self.phone.handle_input(input_mgr, self.order_manager)
            return action

        # Draw player portrait (always visible when phone is closed)
        self._draw_player_portrait()

        # Normal UI when phone is closed
        action = self._draw_phone_icons(input_mgr, nearby)
        if action == "open_incoming_orders":
            self.phone.open("incoming")
        elif action == "open_main_phone":
            self.phone.open("accepted")
        elif action == "open_delivery":
            # Open delivery dialog for the order at nearby location
            if nearby:
                order = self._get_order_for_location(nearby["name"])
                if order:
                    self.delivery_dialog.open(order, nearby["name"])

        return action

    def _draw_player_portrait(self):
        """Draw player portrait in top left corner."""
        # Background circle with border
        border_color = (60, 140, 100)  # Green to match iPuhelin
        bg_color = (40, 50, 60)

        # Draw border circle
        center = self.portrait_border.center
        pygame.draw.circle(self.screen, border_color, center, 42)
        pygame.draw.circle(self.screen, bg_color, center, 36)

        if self.player_portrait is not None:
            # Draw the captured selfie
            # Create circular mask for the portrait
            portrait_x = self.portrait_rect.x
            portrait_y = self.portrait_rect.y

            # Draw the portrait (already scaled to 72x72)
            self.screen.blit(self.player_portrait, (portrait_x, portrait_y))

            # Draw circular border on top to create rounded effect
            pygame.draw.circle(self.screen, border_color, center, 36, 3)
        else:
            # Draw happy face emoji when no portrait
            self._draw_happy_face(center[0], center[1])

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

    def _draw_greenhouse_icon(self):
        """Draw greenhouse icon when near greenhouse location."""
        bg_color = (80, 120, 50)
        pygame.draw.rect(self.screen, bg_color,
                         self.greenhouse_icon_border, border_radius=12)
        self.screen.blit(self.greenhouse_icon,
                         self.greenhouse_icon_rect.topleft)

    def _draw_phone_icons(self, input_mgr, nearby: Optional[Dict]):
        """Draw phone icons and handle clicks. Returns action string or None."""
        bg_color = (80, 80, 100)

        # Top icon: Accepted orders (main phone) - always visible
        pygame.draw.rect(self.screen, bg_color,
                         self.accepted_phone_border, border_radius=12)
        self.screen.blit(self.phone_icon, self.accepted_phone_rect.topleft)

        accepted_count = self.order_manager.get_accepted_count()
        if accepted_count > 0:
            self._draw_badge(self.accepted_phone_rect, accepted_count)

        if input_mgr.clicked_in_rect(self.accepted_phone_rect):
            return "open_main_phone"

        # Door button: Show when nearby location has an accepted order
        show_door_button = False
        if nearby is not None:
            order = self._get_order_for_location(nearby["name"])
            if order is not None:
                show_door_button = True

        if show_door_button:
            door_color = (100, 160, 100)  # Green tint for delivery
            pygame.draw.rect(self.screen, door_color,
                             self.door_button_border, border_radius=12)
            self._draw_door_icon(self.door_button_rect)

            if input_mgr.clicked_in_rect(self.door_button_rect):
                return "open_delivery"

        # Bottom icon: Incoming orders (alert phone) - only if visible orders exist
        # Position it below the door button if door is shown
        visible_count = self.order_manager.get_visible_count()
        if visible_count > 0:
            # Adjust incoming phone position based on door button visibility
            if show_door_button:
                incoming_rect = pygame.Rect(32, 320, 84, 84)
                incoming_border = incoming_rect.inflate(12, 12)
            else:
                incoming_rect = self.incoming_phone_rect
                incoming_border = self.incoming_phone_border

            pygame.draw.rect(self.screen, bg_color,
                             incoming_border, border_radius=12)
            self.screen.blit(self.phone_alert_icon,
                             incoming_rect.topleft)
            self._draw_badge(incoming_rect, visible_count)

            if input_mgr.clicked_in_rect(incoming_rect):
                return "open_incoming_orders"

        return None

    def _draw_badge(self, icon_rect: pygame.Rect, count: int):
        """Draw a red notification badge on top-right of icon."""
        badge_radius = 14
        badge_x = icon_rect.right - badge_radius + 4
        badge_y = icon_rect.top + badge_radius - 4

        # Red circle
        pygame.draw.circle(self.screen, (220, 60, 60),
                           (badge_x, badge_y), badge_radius)

        # White text
        badge_text = self.small_font.render(str(count), True, (255, 255, 255))
        text_rect = badge_text.get_rect(center=(badge_x, badge_y))
        self.screen.blit(badge_text, text_rect)

    def _draw_happy_face(self, cx: int, cy: int):
        """Draw a simple happy face emoji as default player portrait."""
        # Face color (warm yellow)
        face_color = (255, 210, 80)

        # Draw face circle
        pygame.draw.circle(self.screen, face_color, (cx, cy), 30)

        # Eyes (simple black dots)
        eye_y = cy - 8
        left_eye_x = cx - 10
        right_eye_x = cx + 10
        pygame.draw.circle(self.screen, (60, 40, 30), (left_eye_x, eye_y), 5)
        pygame.draw.circle(self.screen, (60, 40, 30), (right_eye_x, eye_y), 5)

        # Eye highlights
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (left_eye_x + 1, eye_y - 2), 2)
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (right_eye_x + 1, eye_y - 2), 2)

        # Smile (arc)
        smile_rect = pygame.Rect(cx - 15, cy - 5, 30, 25)
        pygame.draw.arc(self.screen, (60, 40, 30), smile_rect, 3.5, 6.0, 3)

        # Rosy cheeks
        pygame.draw.circle(self.screen, (255, 160, 120), (cx - 18, cy + 5), 6)
        pygame.draw.circle(self.screen, (255, 160, 120), (cx + 18, cy + 5), 6)

    def _draw_door_icon(self, rect: pygame.Rect):
        """Draw a door icon for the delivery button."""
        cx = rect.centerx
        cy = rect.centery
        icon_color = (255, 255, 255)

        # Door frame (rectangle)
        door_width = 36
        door_height = 50
        door_rect = pygame.Rect(
            cx - door_width // 2,
            cy - door_height // 2,
            door_width,
            door_height
        )
        pygame.draw.rect(self.screen, icon_color,
                         door_rect, 3, border_radius=3)

        # Door handle (circle on right side)
        handle_x = cx + door_width // 2 - 10
        handle_y = cy + 2
        pygame.draw.circle(self.screen, icon_color, (handle_x, handle_y), 5)

        # Arrow pointing into door (from left)
        arrow_start_x = cx - door_width // 2 - 20
        arrow_end_x = cx - door_width // 2 - 5
        arrow_y = cy

        # Arrow line
        pygame.draw.line(self.screen, icon_color,
                         (arrow_start_x, arrow_y),
                         (arrow_end_x, arrow_y), 3)

        # Arrow head
        pygame.draw.polygon(self.screen, icon_color, [
            (arrow_end_x + 5, arrow_y),
            (arrow_end_x - 5, arrow_y - 7),
            (arrow_end_x - 5, arrow_y + 7)
        ])
