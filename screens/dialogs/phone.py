import pygame
from typing import Optional, List
from shared.shared_components import Order, OrderState
from shared.debug_log import debug
from screens.dialogs.phone_active_order import PhoneActiveOrderScreen
from screens.dialogs.phone_visible_order import PhoneVisibleOrderScreen


class PhoneScreen:
    """
    iPuhelin - A kids' watch/device UI overlay for viewing orders.

    Can be opened in two modes:
    - "incoming": Show visible incoming orders with accept buttons
    - "accepted": Show accepted orders and inventory

    Closed by clicking outside the device frame.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = False
        self.mode = "accepted"  # "incoming" or "accepted"

        # Phone frame dimensions (centered on screen)
        screen_w, screen_h = screen.get_size()
        phone_w = 600
        phone_h = 950  # <<<< PHONE TOTAL HEIGHT
        self.phone_rect = pygame.Rect(
            (screen_w - phone_w) // 2,
            (screen_h - phone_h) // 2,
            phone_w,
            phone_h
        )

        # Device frame (outer bezel)
        bezel_padding = 12
        self.bezel_rect = self.phone_rect.inflate(
            bezel_padding * 2, bezel_padding * 2)

        # Fonts
        self.logo_font = pygame.font.Font(None, 52)
        self.title_font = pygame.font.Font(None, 40)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.button_font = pygame.font.Font(None, 32)

        # Colors - device theme (greenish kids device)
        self.bezel_color = (60, 140, 100)  # Green bezel
        self.bezel_edge_color = (40, 100, 70)  # Darker edge
        self.screen_color = (30, 35, 45)  # Dark screen
        self.header_color = (40, 50, 60)
        self.text_color = (255, 255, 255)
        self.accent_color = (100, 180, 100)
        self.logo_color = (180, 255, 180)  # Light green for logo

        # Bottom navbar button rects
        self.nav_button_rect = pygame.Rect(0, 0, 0, 0)
        self.camera_button_rect = pygame.Rect(0, 0, 0, 0)

        self.accept_buttons: List[tuple[pygame.Rect, Order]] = []

        # Track clickable order cards for accepted orders
        self.order_cards: List[tuple[pygame.Rect, Order]] = []

        # Active order detail screen (for ACCEPTED orders - shows images)
        self.active_order_screen = PhoneActiveOrderScreen(self.phone_rect)

        # Visible order detail screen (for VISIBLE orders - shows text only)
        self.visible_order_screen = PhoneVisibleOrderScreen(self.phone_rect)

        # Callback for camera (to be set by parent)
        self.on_camera_click = None

        # Callback for navigation (to be set by parent)
        self.on_nav_click = None

    def open(self, mode: str = "accepted"):
        """Open the phone screen."""
        self.mode = mode
        self.visible = True
        debug.info(f"iPuhelin opened in '{mode}' mode")

    def close(self):
        """Close the phone screen."""
        self.visible = False
        self.active_order_screen.close()
        self.visible_order_screen.close()

    def handle_input(self, input_mgr, order_manager) -> Optional[str]:
        """
        Handle input while phone is open.
        Returns action string or None.
        """
        if not self.visible:
            return None

        # If visible order screen is showing (for VISIBLE orders before accepting)
        if self.visible_order_screen.visible:
            # Check if click is outside the device (bezel) - close phone entirely
            if input_mgr.clicked_this_frame:
                click_pos = input_mgr.click_pos
                if click_pos is not None:
                    if not self.bezel_rect.collidepoint(click_pos):
                        self.close()
                        return "phone_closed"

            result = self.visible_order_screen.handle_input(input_mgr)
            if result == "order_accepted":
                # User clicked OK - actually accept the order
                accepted_order = self.visible_order_screen.accepted_order
                if accepted_order is not None:
                    order_manager.accept_order(accepted_order)
                    debug.info(f"Order accepted via visible screen: {accepted_order.order_id}")
                return "order_accepted"
            if result == "back_to_orders":
                # User clicked X - return to order list without accepting
                return None
            if result is not None:
                return result
            # Visible order screen is showing, don't process other inputs
            return None

        # If active order screen is visible, handle its input first
        if self.active_order_screen.visible:
            # Check if click is outside the device (bezel) - close phone entirely
            if input_mgr.clicked_this_frame:
                click_pos = input_mgr.click_pos
                if click_pos is not None:
                    if not self.bezel_rect.collidepoint(click_pos):
                        self.close()
                        return "phone_closed"

            result = self.active_order_screen.handle_input(input_mgr)
            if result == "back_to_orders":
                # Returned to order list
                return None
            if result is not None:
                return result
            # Active order screen is showing, don't process other inputs
            return None

        # Check if click is outside the device (bezel) - close phone
        if input_mgr.clicked_this_frame:
            click_pos = input_mgr.click_pos
            if click_pos is not None:
                if not self.bezel_rect.collidepoint(click_pos):
                    self.close()
                    return "phone_closed"

        # Check bottom navbar buttons
        if input_mgr.clicked_in_rect(self.nav_button_rect):
            debug.info("Navigation button clicked")
            if self.on_nav_click:
                self.on_nav_click()
            return "nav_clicked"

        if input_mgr.clicked_in_rect(self.camera_button_rect):
            debug.info("Camera button clicked")
            if self.on_camera_click:
                self.on_camera_click()
            return "camera_clicked"

        # Check order card clicks (for accepted orders in "accepted" mode)
        if self.mode == "accepted":
            for card_rect, order in self.order_cards:
                if input_mgr.clicked_in_rect(card_rect):
                    debug.info(f"Order card clicked: {order.order_id}")
                    self.active_order_screen.open(order)
                    return "order_opened"

        # Check accept button clicks - opens visible order screen first
        for btn_rect, order in self.accept_buttons:
            if input_mgr.clicked_in_rect(btn_rect):
                debug.info(f"Accept button clicked for order {order.order_id} - opening details")
                self.visible_order_screen.open(order)
                return "order_details_opened"

        return None

    def draw(self, order_manager):
        """Draw the phone screen."""
        if not self.visible:
            return

        # Clear tracked buttons for click detection
        self.accept_buttons = []
        self.order_cards = []

        # Dim background
        dim_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dim_surface.fill((0, 0, 0, 150))
        self.screen.blit(dim_surface, (0, 0))

        # Draw device bezel (outer frame)
        self._draw_device_frame()

        # If visible order screen is showing (preview before accepting)
        if self.visible_order_screen.visible:
            self._draw_header_minimal()
            self.visible_order_screen.draw(self.screen)
            self._draw_bottom_navbar()
            return

        # If active order screen is visible, draw it instead of order list
        if self.active_order_screen.visible:
            self._draw_header_minimal()
            self.active_order_screen.draw(self.screen)
            self._draw_bottom_navbar()
            return

        # Draw header with logo
        self._draw_header()

        # Draw content based on mode
        if self.mode == "incoming":
            self._draw_incoming_orders(order_manager)
        else:
            self._draw_accepted_orders(order_manager)

        # Draw bottom navbar
        self._draw_bottom_navbar()

    def _draw_device_frame(self):
        """Draw the device bezel/frame to make it look like a kids' watch."""
        # Outer bezel shadow
        shadow_rect = self.bezel_rect.move(4, 4)
        pygame.draw.rect(self.screen, (20, 20, 20),
                         shadow_rect, border_radius=30)

        # Main bezel
        pygame.draw.rect(self.screen, self.bezel_color,
                         self.bezel_rect, border_radius=28)

        # Bezel edge highlight (top-left)
        highlight_rect = self.bezel_rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, (80, 160, 120),
                         highlight_rect, 2, border_radius=26)

        # Inner screen area
        pygame.draw.rect(self.screen, self.screen_color,
                         self.phone_rect, border_radius=16)

        # Screen edge (inset effect)
        pygame.draw.rect(self.screen, (20, 25, 35),
                         self.phone_rect, 2, border_radius=16)

        # Draw small decorative elements on bezel (like watch buttons)
        # Left side "button"
        left_btn = pygame.Rect(
            self.bezel_rect.left - 6,
            self.bezel_rect.centery - 30,
            8,
            60
        )
        pygame.draw.rect(self.screen, self.bezel_edge_color,
                         left_btn, border_radius=3)

        # Right side "button"
        right_btn = pygame.Rect(
            self.bezel_rect.right - 2,
            self.bezel_rect.centery - 20,
            8,
            40
        )
        pygame.draw.rect(self.screen, self.bezel_edge_color,
                         right_btn, border_radius=3)

    def _draw_header(self):
        """Draw header with iPuhelin logo."""
        header_rect = pygame.Rect(
            self.phone_rect.x,
            self.phone_rect.y,
            self.phone_rect.width,
            70
        )
        pygame.draw.rect(self.screen, self.header_color, header_rect,
                         border_top_left_radius=16, border_top_right_radius=16)

        # iPuhelin logo (stylized)
        self._draw_logo(self.phone_rect.x + 15, self.phone_rect.y + 12)

        # Mode indicator on the right
        if self.mode == "incoming":
            mode_text = "Viestit"
        else:
            mode_text = "Tilaukset"

        mode_surf = self.font.render(mode_text, True, (180, 180, 180))
        mode_x = self.phone_rect.right - mode_surf.get_width() - 20
        self.screen.blit(mode_surf, (mode_x, self.phone_rect.y + 25))

    def _draw_header_minimal(self):
        """Draw minimal header when active order screen is showing."""
        header_rect = pygame.Rect(
            self.phone_rect.x,
            self.phone_rect.y,
            self.phone_rect.width,
            70
        )
        pygame.draw.rect(self.screen, self.header_color, header_rect,
                         border_top_left_radius=16, border_top_right_radius=16)

        # iPuhelin logo
        self._draw_logo(self.phone_rect.x + 15, self.phone_rect.y + 12)

        # "Tilaus" on right
        mode_surf = self.font.render("Tilaus", True, (180, 180, 180))
        mode_x = self.phone_rect.right - mode_surf.get_width() - 20
        self.screen.blit(mode_surf, (mode_x, self.phone_rect.y + 25))

    def _draw_logo(self, x: int, y: int):
        """Draw the iPuhelin logo with stylized text."""
        # "i" in italic style
        i_surf = self.logo_font.render("i", True, self.logo_color)
        self.screen.blit(i_surf, (x, y))

        # "Puhelin" in regular style
        puhelin_surf = self.logo_font.render("Puhelin", True, self.text_color)
        self.screen.blit(puhelin_surf, (x + i_surf.get_width() - 2, y))

        # Small leaf decoration after the text
        leaf_x = x + i_surf.get_width() + puhelin_surf.get_width() + 5
        leaf_y = y + 2
        # Draw a simple leaf shape
        points = [
            (leaf_x, leaf_y + 8),
            (leaf_x + 6, leaf_y),
            (leaf_x + 12, leaf_y + 8),
            (leaf_x + 6, leaf_y + 16)
        ]
        pygame.draw.polygon(self.screen, self.accent_color, points)
        # Leaf stem
        pygame.draw.line(self.screen, (80, 140, 80),
                         (leaf_x + 6, leaf_y + 16), (leaf_x + 6, leaf_y + 22), 2)

    def _draw_bottom_navbar(self):
        """Draw bottom navigation bar with nav and camera buttons."""
        # <<<< PHONE BOTTOM NAVBAR HEIGHT AND POSITION
        navbar_height = 50
        navbar_y = self.phone_rect.bottom - navbar_height

        # Navbar background
        navbar_rect = pygame.Rect(
            self.phone_rect.x,
            navbar_y,
            self.phone_rect.width,
            navbar_height
        )
        pygame.draw.rect(self.screen, self.header_color, navbar_rect,
                         border_bottom_left_radius=16, border_bottom_right_radius=16)

        # Divider line
        pygame.draw.line(
            self.screen,
            (60, 70, 80),
            (self.phone_rect.x + 10, navbar_y),
            (self.phone_rect.right - 10, navbar_y),
            1
        )

        # Button dimensions
        button_w = 90
        button_h = 38
        button_y = navbar_y + (navbar_height - button_h) // 2

        # Navigation button (center-left)
        self.nav_button_rect = pygame.Rect(
            self.phone_rect.x + self.phone_rect.width // 4 - button_w // 2,
            button_y,
            button_w,
            button_h
        )
        self._draw_navbar_button(self.nav_button_rect,
                                 "[-]", self._draw_nav_icon)

        # Camera button (center-right)
        self.camera_button_rect = pygame.Rect(
            self.phone_rect.x + 3 * self.phone_rect.width // 4 - button_w // 2,
            button_y,
            button_w,
            button_h
        )
        self._draw_navbar_button(
            self.camera_button_rect, "[O]", self._draw_camera_icon)

    def _draw_navbar_button(self, rect: pygame.Rect, label: str, icon_func):
        """Draw a navbar button with icon and label."""
        # Button background
        pygame.draw.rect(self.screen, (50, 60, 70), rect, border_radius=10)
        pygame.draw.rect(self.screen, (70, 80, 90), rect, 2, border_radius=10)

        # Icon (small, at top of button)
        icon_x = rect.centerx - 10
        icon_y = rect.y + 6
        icon_func(icon_x, icon_y)

        # Label below icon
        label_surf = self.small_font.render(label, True, (200, 200, 200))
        label_rect = label_surf.get_rect(
            centerx=rect.centerx, bottom=rect.bottom - 4)
        self.screen.blit(label_surf, label_rect)

    def _draw_nav_icon(self, x: int, y: int):
        """Draw a simple navigation/map icon."""
        # Compass-like icon
        pygame.draw.circle(self.screen, (150, 200, 150),
                           (x + 10, y + 10), 10, 2)
        # North indicator
        pygame.draw.polygon(self.screen, (150, 200, 150), [
            (x + 10, y + 2),
            (x + 7, y + 10),
            (x + 13, y + 10)
        ])

    def _draw_camera_icon(self, x: int, y: int):
        """Draw a simple camera icon."""
        # Camera body
        pygame.draw.rect(self.screen, (150, 200, 150),
                         (x + 2, y + 5, 16, 12), border_radius=2)
        # Lens
        pygame.draw.circle(self.screen, (100, 150, 100), (x + 10, y + 11), 4)
        pygame.draw.circle(self.screen, (150, 200, 150), (x + 10, y + 11), 3)
        # Flash
        pygame.draw.rect(self.screen, (150, 200, 150), (x + 4, y + 2, 4, 3))

    def _draw_incoming_orders(self, order_manager):
        """Draw list of visible incoming orders."""
        orders = order_manager.visible_orders
        y = self.phone_rect.y + 85

        if not orders:
            no_orders = self.font.render(
                "Ei uusia tilauksia", True, (150, 150, 150))
            self.screen.blit(no_orders, (self.phone_rect.x + 20, y))
            return

        for order in orders:
            self._draw_order_card(order, y, show_timer=True)
            y += 110

    def _draw_accepted_orders(self, order_manager):
        """Draw list of accepted orders."""
        orders = order_manager.accepted_orders
        y = self.phone_rect.y + 85

        if not orders:
            no_orders = self.font.render(
                "Ei hyväksyttyjä tilauksia", True, (150, 150, 150))
            self.screen.blit(no_orders, (self.phone_rect.x + 20, y))
            return

        for order in orders:
            self._draw_order_card(
                order, y, show_timer=False, track_for_click=True)
            y += 110

    def _draw_order_card(self, order: Order, y: int, show_timer: bool, track_for_click: bool = False):
        """Draw a single order card."""
        card_rect = pygame.Rect(
            self.phone_rect.x + 12,
            y,
            self.phone_rect.width - 24,
            95
        )

        # Track for click detection if requested
        if track_for_click:
            self.order_cards.append((card_rect, order))

        # Card background
        pygame.draw.rect(self.screen, (45, 50, 60),
                         card_rect, border_radius=10)
        pygame.draw.rect(self.screen, (60, 70, 80),
                         card_rect, 1, border_radius=10)

        # Customer name
        name_surf = self.font.render(
            order.customer_location, True, self.text_color)
        self.screen.blit(name_surf, (card_rect.x + 12, card_rect.y + 10))

        # Plant count
        plant_count = sum(p.amount for p in order.plants)
        plants_text = f"{plant_count} kasvia"
        plants_surf = self.small_font.render(
            plants_text, True, (160, 160, 160))
        self.screen.blit(plants_surf, (card_rect.x + 12, card_rect.y + 42))

        # Timer bar (for incoming orders)
        if show_timer and order.countdown_to_available > 0:
            timer_width = 180
            timer_height = 6
            timer_x = card_rect.x + 12
            timer_y = card_rect.y + 70

            # Background bar
            pygame.draw.rect(self.screen, (30, 30, 30),
                             (timer_x, timer_y, timer_width, timer_height),
                             border_radius=3)

            # Fill bar (based on remaining time)
            max_time = 15.0
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
                             border_radius=3)

            # Accept button (only for incoming orders)
            btn_rect = pygame.Rect(
                card_rect.right - 95,
                card_rect.y + 28,
                80, 38
            )
            pygame.draw.rect(self.screen, self.accent_color,
                             btn_rect, border_radius=8)
            btn_text = self.small_font.render("Hyväksy", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            self.screen.blit(btn_text, btn_text_rect)

            # Track for click detection
            self.accept_buttons.append((btn_rect, order))
