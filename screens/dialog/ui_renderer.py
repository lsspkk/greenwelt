# UI renderer for dialog screens
import pygame
from typing import Optional
from screens.dialog.components import Button, DialogChoice
from screens.dialog.base_dialog import BaseDialog


class UIRenderer:
    """Renders UI elements for dialog screens"""

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 52)
        self.small_font = pygame.font.Font(None, 42)

    def draw_button(self, button: Button, input_mgr) -> bool:
        """Draw a button and return True if clicked"""
        button.is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, button.rect)
        color = button.hover_color if button.is_hovered else button.color

        pygame.draw.rect(self.screen, color, button.rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), button.rect, 3, border_radius=12)

        text_surf = self.font.render(button.text, True, button.text_color)
        text_rect = text_surf.get_rect(center=button.rect.center)
        self.screen.blit(text_surf, text_rect)

        if input_mgr.clicked_in_rect(button.rect):
            if button.callback:
                button.callback()
            return True
        return False

    def draw_dialog(self, dialog: BaseDialog, input_mgr) -> Optional[int]:
        """Draw a dialog and return the clicked choice index, or None"""
        if not dialog.visible:
            return None

        # Background
        pygame.draw.rect(self.screen, (30, 40, 50), dialog.rect, border_radius=20)
        pygame.draw.rect(self.screen, (100, 150, 200), dialog.rect, 4, border_radius=20)

        # Title
        title_surf = self.font.render(dialog.title, True, (255, 220, 100))
        self.screen.blit(title_surf, (dialog.rect.x + 40, dialog.rect.y + 30))

        # Content
        content_surf = self.small_font.render(dialog.content, True, (200, 200, 200))
        self.screen.blit(content_surf, (dialog.rect.x + 40, dialog.rect.y + 100))

        # Choices
        choice_y = dialog.rect.y + 200
        clicked_choice = None

        for i, choice in enumerate(dialog.choices):
            choice_rect = pygame.Rect(
                dialog.rect.x + 40,
                choice_y,
                dialog.rect.width - 80,
                70
            )

            is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, choice_rect)
            bg_color = (50, 70, 90) if is_hovered else (40, 55, 70)
            pygame.draw.rect(self.screen, bg_color, choice_rect, border_radius=10)

            choice_text = f"{i + 1}. {choice.text}"
            text_surf = self.small_font.render(choice_text, True, (220, 240, 255))
            self.screen.blit(text_surf, (choice_rect.x + 25, choice_rect.y + 18))

            if input_mgr.clicked_in_rect(choice_rect):
                clicked_choice = i
                if choice.callback:
                    choice.callback()

            choice_y += 90

        return clicked_choice

    def draw_click_indicator(self, pos: tuple):
        """Draw a visual indicator at the click position"""
        if pos:
            pygame.draw.circle(self.screen, (255, 100, 100), pos, 40, 4)
            pygame.draw.circle(self.screen, (255, 100, 100), pos, 12)

    def draw_coordinates(self, input_mgr):
        """Draw current mouse/touch coordinates"""
        if input_mgr.touch_pos:
            text = f"Pos: {input_mgr.touch_pos}"
            text_surf = self.small_font.render(text, True, (150, 150, 150))
            self.screen.blit(text_surf, (30, 1020))
