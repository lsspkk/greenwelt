# Input manager for mouse and touch input
import pygame
from typing import Optional


class InputManager:
    """Handles mouse and touch input for both desktop and mobile"""

    def __init__(self):
        self.click_pos: Optional[tuple] = None
        self.touch_pos: Optional[tuple] = None
        self.clicked_this_frame: bool = False

    def process_events(self, events):
        """Process pygame events and update input state"""
        self.clicked_this_frame = False
        self.click_pos = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click_pos = event.pos
                self.clicked_this_frame = True
            elif event.type == pygame.FINGERDOWN:
                screen = pygame.display.get_surface()
                x = int(event.x * screen.get_width())
                y = int(event.y * screen.get_height())
                self.click_pos = (x, y)
                self.clicked_this_frame = True

        self.touch_pos = pygame.mouse.get_pos()

    def is_point_in_rect(self, point: tuple, rect: pygame.Rect) -> bool:
        """Check if a point is inside a rectangle"""
        if point is None:
            return False
        return rect.collidepoint(point)

    def clicked_in_rect(self, rect: pygame.Rect) -> bool:
        """Check if the user clicked inside a rectangle this frame"""
        return self.clicked_this_frame and self.is_point_in_rect(self.click_pos, rect)
