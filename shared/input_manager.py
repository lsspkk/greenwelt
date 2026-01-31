# Input manager for mouse and touch input
import pygame
from typing import Optional

# Try to import JavaScript interop for browser environment
try:
    import js
    IS_BROWSER = True
except ImportError:
    js = None
    IS_BROWSER = False


class InputManager:
    """Handles mouse and touch input for both desktop and mobile"""

    def __init__(self):
        self.click_pos: Optional[tuple] = None
        self.touch_pos: Optional[tuple] = None
        self.clicked_this_frame: bool = False

    def get_viewport_size(self) -> tuple:
        """
        Get the actual viewport/window size.

        In browser: gets the canvas element's CSS size (actual displayed size)
        On desktop: gets the pygame window size
        """
        if IS_BROWSER and js is not None:
            # In browser, get the actual canvas display size from CSS
            try:
                canvas = js.document.getElementById("canvas")
                if canvas:
                    # getBoundingClientRect gives actual rendered size
                    rect = canvas.getBoundingClientRect()
                    return (int(rect.width), int(rect.height))
            except Exception:
                pass

        # Desktop or fallback: use pygame window size
        try:
            return pygame.display.get_window_size()
        except Exception:
            surface = pygame.display.get_surface()
            return (surface.get_width(), surface.get_height())

    def screen_to_game_coords(self, screen_x: float, screen_y: float) -> tuple:
        """
        Transform screen coordinates to game surface coordinates.

        When the game runs fullscreen on a device with different aspect ratio,
        the game surface is centered with black bars (letterboxing).
        This function transforms from actual screen position to game position.
        """
        surface = pygame.display.get_surface()
        game_width = surface.get_width()
        game_height = surface.get_height()

        # Get actual viewport/window size
        window_width, window_height = self.get_viewport_size()

        # If window matches game size, no transformation needed
        if window_width == game_width and window_height == game_height:
            return (int(screen_x), int(screen_y))

        # Calculate scale factor (maintaining aspect ratio)
        scale_x = window_width / game_width
        scale_y = window_height / game_height
        scale = min(scale_x, scale_y)

        # Calculate the actual rendered game area size
        rendered_width = game_width * scale
        rendered_height = game_height * scale

        # Calculate offset (black bar size on each side)
        offset_x = (window_width - rendered_width) / 2
        offset_y = (window_height - rendered_height) / 2

        # Transform screen coordinates to game coordinates
        game_x = (screen_x - offset_x) / scale
        game_y = (screen_y - offset_y) / scale

        return (int(game_x), int(game_y))

    def process_events(self, events):
        """Process pygame events and update input state"""
        self.clicked_this_frame = False
        self.click_pos = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Mouse events also need transformation when letterboxed
                screen_x, screen_y = event.pos
                self.click_pos = self.screen_to_game_coords(screen_x, screen_y)
                self.clicked_this_frame = True
            elif event.type == pygame.FINGERDOWN:
                # Touch events give normalized coordinates (0.0 to 1.0)
                # relative to the actual viewport/window size
                window_width, window_height = self.get_viewport_size()

                # Convert normalized touch coords to screen coords
                screen_x = event.x * window_width
                screen_y = event.y * window_height

                # Transform to game coordinates
                self.click_pos = self.screen_to_game_coords(screen_x, screen_y)
                self.clicked_this_frame = True

        # Transform current mouse position as well
        raw_mouse_pos = pygame.mouse.get_pos()
        self.touch_pos = self.screen_to_game_coords(raw_mouse_pos[0], raw_mouse_pos[1])

    def is_point_in_rect(self, point: tuple, rect: pygame.Rect) -> bool:
        """Check if a point is inside a rectangle"""
        if point is None:
            return False
        return rect.collidepoint(point)

    def clicked_in_rect(self, rect: pygame.Rect) -> bool:
        """Check if the user clicked inside a rectangle this frame"""
        return self.clicked_this_frame and self.is_point_in_rect(self.click_pos, rect)
