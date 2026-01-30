# In-game debug overlay renderer
import pygame
from shared.debug_log import debug


class DebugOverlay:
    """In-game debug overlay renderer"""

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 52)


        # Overlay panel
        sw, sh = screen.get_size()
        # Icon button (bottom-left corner)
        self.icon_rect = pygame.Rect(30, sh - 100, 70, 70)
        self.panel_rect = pygame.Rect(30, 120, sw - 60, sh - 200)

        # Buttons inside overlay
        self.close_rect = pygame.Rect(0, 0, 140, 55)
        self.copy_rect = pygame.Rect(0, 0, 140, 55)
        self.clear_rect = pygame.Rect(0, 0, 140, 55)
        self.scroll_up_rect = pygame.Rect(0, 0, 70, 55)
        self.scroll_down_rect = pygame.Rect(0, 0, 70, 55)

        self._update_button_positions()

    def _update_button_positions(self):
        """Position buttons relative to panel"""
        pr = self.panel_rect
        self.close_rect.topright = (pr.right - 25, pr.top + 15)
        self.copy_rect.topright = (self.close_rect.left - 20, pr.top + 15)
        self.clear_rect.topright = (self.copy_rect.left - 20, pr.top + 15)
        self.scroll_up_rect.topright = (pr.right - 25, pr.bottom - 70)
        self.scroll_down_rect.topright = (self.scroll_up_rect.left - 15, pr.bottom - 70)

    def draw_icon(self, input_mgr) -> bool:
        """Draw debug icon button, return True if clicked"""
        is_hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, self.icon_rect)
        color = (80, 80, 100) if is_hover else (50, 50, 70)
        pygame.draw.rect(self.screen, color, self.icon_rect, border_radius=12)

        # Draw "bug" icon
        cx, cy = self.icon_rect.center
        pygame.draw.ellipse(self.screen, (200, 100, 100), (cx - 18, cy - 12, 36, 24))
        pygame.draw.circle(self.screen, (200, 100, 100), (cx, cy - 20), 12)
        pygame.draw.line(self.screen, (200, 100, 100), (cx - 7, cy - 30), (cx - 14, cy - 40), 4)
        pygame.draw.line(self.screen, (200, 100, 100), (cx + 7, cy - 30), (cx + 14, cy - 40), 4)

        # Message count badge
        count = len(debug.messages)
        if count > 0:
            badge_text = str(min(count, 99))
            badge_surf = self.font.render(badge_text, True, (255, 255, 255))
            badge_rect = badge_surf.get_rect()
            badge_bg = pygame.Rect(
                self.icon_rect.right - 25,
                self.icon_rect.top - 5,
                max(32, badge_rect.width + 10),
                32
            )
            pygame.draw.rect(self.screen, (200, 50, 50), badge_bg, border_radius=16)
            self.screen.blit(
                badge_surf,
                (badge_bg.centerx - badge_rect.width // 2, badge_bg.centery - badge_rect.height // 2)
            )

        return input_mgr.clicked_in_rect(self.icon_rect)

    def draw_overlay(self, input_mgr) -> bool:
        """Draw the debug overlay panel. Returns True if should close."""
        if not debug.overlay_visible:
            return False

        # Semi-transparent background
        overlay_surf = pygame.Surface((self.panel_rect.width, self.panel_rect.height))
        overlay_surf.fill((20, 25, 35))
        overlay_surf.set_alpha(240)
        self.screen.blit(overlay_surf, self.panel_rect.topleft)

        # Border
        pygame.draw.rect(self.screen, (100, 120, 150), self.panel_rect, 3, border_radius=16)

        # Title
        title = self.title_font.render("Debug Log", True, (255, 220, 100))
        self.screen.blit(title, (self.panel_rect.x + 25, self.panel_rect.y + 20))

        # Platform indicator
        platform = "WASM" if debug.is_wasm else "Native"
        plat_surf = self.font.render(f"[{platform}]", True, (150, 150, 150))
        self.screen.blit(plat_surf, (self.panel_rect.x + 250, self.panel_rect.y + 28))

        # Draw buttons
        should_close = self._draw_button("Close", self.close_rect, input_mgr, (150, 60, 60))
        if self._draw_button("Copy", self.copy_rect, input_mgr, (60, 120, 60)):
            self._copy_to_clipboard()
        if self._draw_button("Clear", self.clear_rect, input_mgr, (100, 100, 60)):
            debug.clear()

        # Scroll buttons
        if self._draw_button("^", self.scroll_up_rect, input_mgr, (70, 70, 90)):
            debug.scroll_up()
        if self._draw_button("v", self.scroll_down_rect, input_mgr, (70, 70, 90)):
            debug.scroll_down()

        # Draw messages
        messages = debug.get_messages(20)
        y = self.panel_rect.y + 90
        for msg in messages:
            if "[ERROR]" in msg:
                color = (255, 100, 100)
            elif "[WARN]" in msg:
                color = (255, 200, 100)
            elif "[DEBUG]" in msg:
                color = (150, 150, 200)
            else:
                color = (200, 200, 200)

            display_msg = msg[:100] + "..." if len(msg) > 100 else msg
            text_surf = self.font.render(display_msg, True, color)
            self.screen.blit(text_surf, (self.panel_rect.x + 25, y))
            y += 38

        # Scroll indicator
        total = len(debug.messages)
        if total > 20:
            scroll_info = f"Showing {total - debug.scroll_offset - 20 + 1}-{total - debug.scroll_offset} of {total}"
            scroll_surf = self.font.render(scroll_info, True, (120, 120, 140))
            self.screen.blit(scroll_surf, (self.panel_rect.x + 25, self.panel_rect.bottom - 55))

        return should_close

    def _draw_button(self, text: str, rect: pygame.Rect, input_mgr, color: tuple) -> bool:
        """Draw a small button and return if clicked"""
        is_hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, rect)
        btn_color = tuple(min(255, c + 30) for c in color) if is_hover else color

        pygame.draw.rect(self.screen, btn_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2, border_radius=8)

        text_surf = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

        return input_mgr.clicked_in_rect(rect)

    def _copy_to_clipboard(self):
        """Copy log to clipboard"""
        text = debug.get_all_text()
        try:
            if debug.is_wasm:
                try:
                    pygame.scrap.init()
                    pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
                    debug.info("Copied to clipboard (pygame.scrap)")
                except:
                    debug.warn("Clipboard not available in WASM")
                    print(text)
            else:
                pygame.scrap.init()
                pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
                debug.info("Copied to clipboard")
        except Exception as e:
            debug.error(f"Copy failed: {e}")
