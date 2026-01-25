# Base class for all dialog screens
import pygame
from dataclasses import dataclass, field
from typing import List
from screens.dialog.components import DialogChoice


@dataclass
class BaseDialog:
    """Base class for dialog screens"""
    title: str
    content: str
    choices: List[DialogChoice] = field(default_factory=list)
    visible: bool = False
    rect: pygame.Rect = None

    def __post_init__(self):
        if self.rect is None:
            # Centered dialog for 1920x1080
            self.rect = pygame.Rect(260, 200, 1400, 600)

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def toggle(self):
        self.visible = not self.visible
