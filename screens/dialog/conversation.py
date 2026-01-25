# NPC conversation dialog
import pygame
from typing import List, Optional
from screens.dialog.base_dialog import BaseDialog
from screens.dialog.components import DialogChoice


class ConversationDialog(BaseDialog):
    """Dialog for NPC conversations with portrait support"""

    def __init__(
        self,
        title: str,
        content: str,
        choices: List[DialogChoice] = None,
        portrait_image: pygame.Surface = None
    ):
        super().__init__(
            title=title,
            content=content,
            choices=choices if choices else []
        )
        self.portrait_image = portrait_image
        self.speaker_name = title

    def set_portrait(self, image: pygame.Surface):
        """Set the portrait image for the speaker"""
        self.portrait_image = image

    def set_speaker(self, name: str):
        """Set the speaker name"""
        self.speaker_name = name
        self.title = name

    def set_text(self, text: str):
        """Set the dialog text"""
        self.content = text

    def set_choices(self, choices: List[DialogChoice]):
        """Set the available choices"""
        self.choices = choices
