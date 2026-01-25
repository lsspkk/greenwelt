# Dialog-specific ECS components
from dataclasses import dataclass
from typing import Optional, Callable, List


@dataclass
class Button:
    """A clickable button"""
    rect: object  # pygame.Rect
    text: str
    color: tuple = (60, 120, 180)
    hover_color: tuple = (80, 150, 220)
    text_color: tuple = (255, 255, 255)
    callback: Optional[Callable] = None
    is_hovered: bool = False


@dataclass
class DialogChoice:
    """A single choice option in a dialog"""
    text: str
    callback: Optional[Callable] = None
