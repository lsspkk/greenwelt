# Start dialog - game title screen with menu buttons
import pygame


class StartDialog:
    """
    Start screen with three buttons:
    - Map icon: Start playing map1
    - Exit icon: Quit the game (desktop only)
    - Fullscreen icon: Toggle fullscreen
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # Fonts
        self.title_font = pygame.font.Font(None, 120)
        self.subtitle_font = pygame.font.Font(None, 52)

        # Button size and spacing
        self.button_size = 120
        self.button_spacing = 60

        # Calculate button positions (centered horizontally)
        total_width = self.button_size * 3 + self.button_spacing * 2
        start_x = (self.screen_width - total_width) // 2
        button_y = self.screen_height // 2 + 50

        # Button rectangles
        self.map_button_rect = pygame.Rect(
            start_x,
            button_y,
            self.button_size,
            self.button_size
        )
        self.fullscreen_button_rect = pygame.Rect(
            start_x + self.button_size + self.button_spacing,
            button_y,
            self.button_size,
            self.button_size
        )
        self.exit_button_rect = pygame.Rect(
            start_x + (self.button_size + self.button_spacing) * 2,
            button_y,
            self.button_size,
            self.button_size
        )

        # Colors
        self.bg_color = (25, 35, 45)
        self.button_color = (50, 70, 90)
        self.button_hover_color = (70, 100, 130)
        self.icon_color = (200, 220, 240)
        self.title_color = (100, 180, 120)
        self.subtitle_color = (150, 150, 150)

        # Result state
        self.result = None  # "map", "exit", "fullscreen", or None

    def handle_event(self, input_mgr) -> str:
        """
        Handle input and return action if button clicked.
        Returns: "map", "exit", "fullscreen", or None
        """
        if input_mgr.clicked_this_frame:
            if input_mgr.clicked_in_rect(self.map_button_rect):
                return "map"
            if input_mgr.clicked_in_rect(self.fullscreen_button_rect):
                return "fullscreen"
            if input_mgr.clicked_in_rect(self.exit_button_rect):
                return "exit"
        return None

    def draw(self, input_mgr):
        """Draw the start dialog"""
        # Background
        self.screen.fill(self.bg_color)

        # Title
        title_text = "Viherpesu"
        title_surf = self.title_font.render(title_text, True, self.title_color)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_surf, title_rect)

        # Subtitle
        subtitle_text = "Paranna kaupunkeja kasvien voimalla!"
        subtitle_surf = self.subtitle_font.render(subtitle_text, True, self.subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, 280))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Draw buttons
        self._draw_map_button(input_mgr)
        self._draw_fullscreen_button(input_mgr)
        self._draw_exit_button(input_mgr)

    def _draw_map_button(self, input_mgr):
        """Draw the map/play button with a simple map icon"""
        rect = self.map_button_rect
        is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, rect)
        color = self.button_hover_color if is_hovered else self.button_color

        # Button background
        pygame.draw.rect(self.screen, color, rect, border_radius=16)
        pygame.draw.rect(self.screen, self.icon_color, rect, 3, border_radius=16)

        # Map icon: simple grid/map symbol
        cx = rect.centerx
        cy = rect.centery
        icon_size = 50

        # Draw a folded map shape
        points = [
            (cx - icon_size // 2, cy - icon_size // 2),
            (cx - icon_size // 6, cy - icon_size // 2 + 8),
            (cx + icon_size // 6, cy - icon_size // 2),
            (cx + icon_size // 2, cy - icon_size // 2 + 8),
            (cx + icon_size // 2, cy + icon_size // 2),
            (cx + icon_size // 6, cy + icon_size // 2 - 8),
            (cx - icon_size // 6, cy + icon_size // 2),
            (cx - icon_size // 2, cy + icon_size // 2 - 8),
        ]
        pygame.draw.polygon(self.screen, self.icon_color, points, 3)

        # Draw location marker
        marker_x = cx
        marker_y = cy - 5
        pygame.draw.circle(self.screen, (200, 100, 100), (marker_x, marker_y), 12)
        pygame.draw.circle(self.screen, self.icon_color, (marker_x, marker_y), 8)

    def _draw_fullscreen_button(self, input_mgr):
        """Draw the fullscreen toggle button"""
        rect = self.fullscreen_button_rect
        is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, rect)
        color = self.button_hover_color if is_hovered else self.button_color

        # Button background
        pygame.draw.rect(self.screen, color, rect, border_radius=16)
        pygame.draw.rect(self.screen, self.icon_color, rect, 3, border_radius=16)

        # Fullscreen icon: rectangle with corner arrows
        cx = rect.centerx
        cy = rect.centery
        inner_rect = pygame.Rect(cx - 25, cy - 20, 50, 40)
        pygame.draw.rect(self.screen, self.icon_color, inner_rect, 3, border_radius=4)

        # Corner arrows
        arrow_size = 12
        # Top-left arrow
        pygame.draw.polygon(self.screen, self.icon_color, [
            (inner_rect.left - 5, inner_rect.top - 5),
            (inner_rect.left - 5 + arrow_size, inner_rect.top - 5),
            (inner_rect.left - 5, inner_rect.top - 5 + arrow_size)
        ])
        # Bottom-right arrow
        pygame.draw.polygon(self.screen, self.icon_color, [
            (inner_rect.right + 5, inner_rect.bottom + 5),
            (inner_rect.right + 5 - arrow_size, inner_rect.bottom + 5),
            (inner_rect.right + 5, inner_rect.bottom + 5 - arrow_size)
        ])

    def _draw_exit_button(self, input_mgr):
        """Draw the exit/quit button"""
        rect = self.exit_button_rect
        is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, rect)
        color = self.button_hover_color if is_hovered else self.button_color

        # Button background
        pygame.draw.rect(self.screen, color, rect, border_radius=16)
        pygame.draw.rect(self.screen, self.icon_color, rect, 3, border_radius=16)

        # Exit icon: door with arrow
        cx = rect.centerx
        cy = rect.centery

        # Door frame
        door_rect = pygame.Rect(cx - 15, cy - 25, 30, 50)
        pygame.draw.rect(self.screen, self.icon_color, door_rect, 3, border_radius=2)

        # Door handle
        pygame.draw.circle(self.screen, self.icon_color, (cx + 8, cy), 4)

        # Arrow pointing out
        arrow_x = cx - 30
        pygame.draw.line(self.screen, self.icon_color, (arrow_x, cy), (arrow_x - 20, cy), 3)
        pygame.draw.polygon(self.screen, self.icon_color, [
            (arrow_x - 25, cy),
            (arrow_x - 15, cy - 8),
            (arrow_x - 15, cy + 8)
        ])
