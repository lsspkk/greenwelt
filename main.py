# Plant Courier - Minimal with Input & Debug System
import asyncio
import pygame
import esper
from dataclasses import dataclass, field
import random
import sys
from typing import Optional, Callable, List
from collections import deque

# ============ Debug/Log System ============
class DebugLog:
    """Cross-platform debug logging system"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.messages: deque = deque(maxlen=100)  # Keep last 100 messages
        self.is_wasm = sys.platform == "emscripten"
        self.overlay_visible = False
        self.scroll_offset = 0

    def log(self, msg: str, level: str = "INFO"):
        """Log a message"""
        entry = f"[{level}] {msg}"
        self.messages.append(entry)

        # On native Python, also print to terminal
        if not self.is_wasm:
            print(entry, flush=True)

    def info(self, msg: str):
        self.log(msg, "INFO")

    def warn(self, msg: str):
        self.log(msg, "WARN")

    def error(self, msg: str):
        self.log(msg, "ERROR")

    def debug(self, msg: str):
        self.log(msg, "DEBUG")

    def get_messages(self, count: int = 20) -> List[str]:
        """Get the last N messages"""
        msgs = list(self.messages)
        start = max(0, len(msgs) - count - self.scroll_offset)
        end = len(msgs) - self.scroll_offset
        return msgs[start:end]

    def get_all_text(self) -> str:
        """Get all messages as a single string (for copy/paste)"""
        return "\n".join(self.messages)

    def clear(self):
        """Clear all messages"""
        self.messages.clear()
        self.scroll_offset = 0

    def scroll_up(self):
        max_scroll = max(0, len(self.messages) - 20)
        self.scroll_offset = min(self.scroll_offset + 5, max_scroll)

    def scroll_down(self):
        self.scroll_offset = max(0, self.scroll_offset - 5)


# Global debug instance
debug = DebugLog()


class DebugOverlay:
    """In-game debug overlay renderer"""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 24)

        # Icon button (top-left corner)
        self.icon_rect = pygame.Rect(10, 10, 30, 30)

        # Overlay panel
        sw, sh = screen.get_size()
        self.panel_rect = pygame.Rect(10, 50, sw - 20, sh - 100)

        # Buttons inside overlay
        self.close_rect = pygame.Rect(0, 0, 60, 25)
        self.copy_rect = pygame.Rect(0, 0, 60, 25)
        self.clear_rect = pygame.Rect(0, 0, 60, 25)
        self.scroll_up_rect = pygame.Rect(0, 0, 30, 25)
        self.scroll_down_rect = pygame.Rect(0, 0, 30, 25)

        self._update_button_positions()

    def _update_button_positions(self):
        """Position buttons relative to panel"""
        pr = self.panel_rect
        self.close_rect.topright = (pr.right - 10, pr.top + 5)
        self.copy_rect.topright = (self.close_rect.left - 10, pr.top + 5)
        self.clear_rect.topright = (self.copy_rect.left - 10, pr.top + 5)
        self.scroll_up_rect.topright = (pr.right - 10, pr.bottom - 30)
        self.scroll_down_rect.topright = (self.scroll_up_rect.left - 5, pr.bottom - 30)

    def draw_icon(self, input_mgr) -> bool:
        """Draw debug icon button, return True if clicked"""
        # Draw icon background
        is_hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, self.icon_rect)
        color = (80, 80, 100) if is_hover else (50, 50, 70)
        pygame.draw.rect(self.screen, color, self.icon_rect, border_radius=5)

        # Draw "bug" icon (simple representation)
        cx, cy = self.icon_rect.center
        # Bug body
        pygame.draw.ellipse(self.screen, (200, 100, 100),
                          (cx - 8, cy - 6, 16, 12))
        # Bug head
        pygame.draw.circle(self.screen, (200, 100, 100), (cx, cy - 10), 5)
        # Antenna
        pygame.draw.line(self.screen, (200, 100, 100), (cx - 3, cy - 14), (cx - 6, cy - 18), 2)
        pygame.draw.line(self.screen, (200, 100, 100), (cx + 3, cy - 14), (cx + 6, cy - 18), 2)

        # Message count badge
        count = len(debug.messages)
        if count > 0:
            badge_text = str(min(count, 99))
            badge_surf = self.font.render(badge_text, True, (255, 255, 255))
            badge_rect = badge_surf.get_rect()
            badge_bg = pygame.Rect(self.icon_rect.right - 12, self.icon_rect.top - 2,
                                   max(14, badge_rect.width + 4), 14)
            pygame.draw.rect(self.screen, (200, 50, 50), badge_bg, border_radius=7)
            self.screen.blit(badge_surf, (badge_bg.centerx - badge_rect.width // 2,
                                         badge_bg.centery - badge_rect.height // 2))

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
        pygame.draw.rect(self.screen, (100, 120, 150), self.panel_rect, 2, border_radius=8)

        # Title
        title = self.title_font.render("Debug Log", True, (255, 220, 100))
        self.screen.blit(title, (self.panel_rect.x + 10, self.panel_rect.y + 8))

        # Platform indicator
        platform = "WASM" if debug.is_wasm else "Native"
        plat_surf = self.font.render(f"[{platform}]", True, (150, 150, 150))
        self.screen.blit(plat_surf, (self.panel_rect.x + 100, self.panel_rect.y + 10))

        # Draw buttons
        should_close = self._draw_button("Close", self.close_rect, input_mgr, (150, 60, 60))
        if self._draw_button("Copy", self.copy_rect, input_mgr, (60, 120, 60)):
            self._copy_to_clipboard()
        if self._draw_button("Clear", self.clear_rect, input_mgr, (100, 100, 60)):
            debug.clear()

        # Scroll buttons
        if self._draw_button("▲", self.scroll_up_rect, input_mgr, (70, 70, 90)):
            debug.scroll_up()
        if self._draw_button("▼", self.scroll_down_rect, input_mgr, (70, 70, 90)):
            debug.scroll_down()

        # Draw messages
        messages = debug.get_messages(20)
        y = self.panel_rect.y + 35
        for msg in messages:
            # Color based on level
            if "[ERROR]" in msg:
                color = (255, 100, 100)
            elif "[WARN]" in msg:
                color = (255, 200, 100)
            elif "[DEBUG]" in msg:
                color = (150, 150, 200)
            else:
                color = (200, 200, 200)

            # Truncate long messages
            display_msg = msg[:70] + "..." if len(msg) > 70 else msg
            text_surf = self.font.render(display_msg, True, color)
            self.screen.blit(text_surf, (self.panel_rect.x + 10, y))
            y += 16

        # Scroll indicator
        total = len(debug.messages)
        if total > 20:
            scroll_info = f"Showing {total - debug.scroll_offset - 20 + 1}-{total - debug.scroll_offset} of {total}"
            scroll_surf = self.font.render(scroll_info, True, (120, 120, 140))
            self.screen.blit(scroll_surf, (self.panel_rect.x + 10, self.panel_rect.bottom - 25))

        return should_close

    def _draw_button(self, text: str, rect: pygame.Rect, input_mgr, color: tuple) -> bool:
        """Draw a small button and return if clicked"""
        is_hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, rect)
        btn_color = tuple(min(255, c + 30) for c in color) if is_hover else color

        pygame.draw.rect(self.screen, btn_color, rect, border_radius=4)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 1, border_radius=4)

        text_surf = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

        return input_mgr.clicked_in_rect(rect)

    def _copy_to_clipboard(self):
        """Copy log to clipboard"""
        text = debug.get_all_text()
        try:
            if debug.is_wasm:
                # Try using JavaScript clipboard API via platform module
                import platform
                # In WASM, we can try pygame's scrap module
                try:
                    pygame.scrap.init()
                    pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
                    debug.info("Copied to clipboard (pygame.scrap)")
                except:
                    # Fallback: just log that copy isn't available
                    debug.warn("Clipboard not available in WASM - see browser console")
                    print(text)  # At least print to console
            else:
                # Native: use pygame scrap
                pygame.scrap.init()
                pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
                debug.info("Copied to clipboard")
        except Exception as e:
            debug.error(f"Copy failed: {e}")


# ============ Input System ============
class InputManager:
    """Handles mouse and touch input for both desktop and mobile"""
    def __init__(self):
        self.click_pos: Optional[tuple] = None
        self.touch_pos: Optional[tuple] = None
        self.clicked_this_frame: bool = False

    def process_events(self, events):
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
        if point is None:
            return False
        return rect.collidepoint(point)

    def clicked_in_rect(self, rect: pygame.Rect) -> bool:
        return self.clicked_this_frame and self.is_point_in_rect(self.click_pos, rect)


# ============ UI Components ============
@dataclass
class Button:
    rect: pygame.Rect
    text: str
    color: tuple = (60, 120, 180)
    hover_color: tuple = (80, 150, 220)
    text_color: tuple = (255, 255, 255)
    callback: Optional[Callable] = None
    is_hovered: bool = False

@dataclass
class DialogChoice:
    text: str
    callback: Optional[Callable] = None

@dataclass
class Dialog:
    title: str
    content: str
    choices: List[DialogChoice] = field(default_factory=list)
    visible: bool = False
    rect: pygame.Rect = None

    def __post_init__(self):
        if self.rect is None:
            self.rect = pygame.Rect(40, 60, 400, 200)


# ============ ECS Components ============
@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    vx: float
    vy: float

@dataclass
class DotRenderable:
    radius: int = 6

@dataclass
class RectangleRenderable:
    width: int = 48
    height: int = 32


# ============ ECS Systems ============
class MovementSystem(esper.Processor):
    def process(self, dt: float):
        for ent, (p, v) in esper.get_components(Position, Velocity):
            p.x += v.vx * dt
            p.y += v.vy * dt


class RenderSystem(esper.Processor):
    def __init__(self, screen):
        self.screen = screen

    def process(self, dt: float):
        self.screen.fill((16, 22, 30))
        for ent, (p, r) in esper.get_components(Position, RectangleRenderable):
            rect = pygame.Rect(int(p.x), int(p.y), r.width, r.height)
            pygame.draw.rect(self.screen, (60, 180, 90), rect, border_radius=8)
        for ent, (p, r) in esper.get_components(Position, DotRenderable):
            pygame.draw.circle(self.screen, (200, 240, 200), (int(p.x), int(p.y)), r.radius)


# ============ UI Renderer ============
class UIRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

    def draw_button(self, button: Button, input_mgr: InputManager) -> bool:
        button.is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, button.rect)
        color = button.hover_color if button.is_hovered else button.color
        pygame.draw.rect(self.screen, color, button.rect, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), button.rect, 2, border_radius=6)
        text_surf = self.font.render(button.text, True, button.text_color)
        text_rect = text_surf.get_rect(center=button.rect.center)
        self.screen.blit(text_surf, text_rect)
        if input_mgr.clicked_in_rect(button.rect):
            if button.callback:
                button.callback()
            return True
        return False

    def draw_dialog(self, dialog: Dialog, input_mgr: InputManager) -> Optional[int]:
        if not dialog.visible:
            return None
        pygame.draw.rect(self.screen, (30, 40, 50), dialog.rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 150, 200), dialog.rect, 3, border_radius=10)
        title_surf = self.font.render(dialog.title, True, (255, 220, 100))
        self.screen.blit(title_surf, (dialog.rect.x + 15, dialog.rect.y + 10))
        content_surf = self.small_font.render(dialog.content, True, (200, 200, 200))
        self.screen.blit(content_surf, (dialog.rect.x + 15, dialog.rect.y + 40))
        choice_y = dialog.rect.y + 80
        clicked_choice = None
        for i, choice in enumerate(dialog.choices):
            choice_rect = pygame.Rect(dialog.rect.x + 15, choice_y, dialog.rect.width - 30, 30)
            is_hovered = input_mgr.is_point_in_rect(input_mgr.touch_pos, choice_rect)
            bg_color = (50, 70, 90) if is_hovered else (40, 55, 70)
            pygame.draw.rect(self.screen, bg_color, choice_rect, border_radius=5)
            choice_text = f"{i + 1}. {choice.text}"
            text_surf = self.small_font.render(choice_text, True, (220, 240, 255))
            self.screen.blit(text_surf, (choice_rect.x + 10, choice_rect.y + 7))
            if input_mgr.clicked_in_rect(choice_rect):
                clicked_choice = i
                if choice.callback:
                    choice.callback()
            choice_y += 35
        return clicked_choice

    def draw_click_indicator(self, pos: tuple):
        if pos:
            pygame.draw.circle(self.screen, (255, 100, 100), pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), pos, 5)

    def draw_coordinates(self, input_mgr: InputManager):
        if input_mgr.touch_pos:
            text = f"Pos: {input_mgr.touch_pos}"
            text_surf = self.small_font.render(text, True, (150, 150, 150))
            self.screen.blit(text_surf, (10, 300))


# ============ Main ============
async def main():
    pygame.init()
    screen = pygame.display.set_mode((480, 320))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Plant Courier - Debug Demo")

    # Initialize systems
    input_mgr = InputManager()
    ui = UIRenderer(screen)
    debug_overlay = DebugOverlay(screen)

    # Log startup info
    debug.info(f"Game started - Platform: {'WASM' if debug.is_wasm else 'Native'}")
    debug.info(f"Python version: {sys.version.split()[0]}")
    debug.info(f"Pygame version: {pygame.version.ver}")
    debug.info(f"Screen size: {screen.get_size()}")

    # Set up esper
    esper.switch_world("main")
    esper.clear_database()
    esper.add_processor(MovementSystem())
    esper.add_processor(RenderSystem(screen))
    debug.info("ECS world initialized")

    # Create game entities
    for i in range(3):
        x = random.randint(20, 480 - 68)
        y = random.randint(20, 320 - 52)
        esper.create_entity(
            Position(float(x), float(y)),
            RectangleRenderable(width=48, height=32),
        )
        debug.debug(f"Created rectangle {i+1} at ({x}, {y})")

    player = esper.create_entity(
        Position(60.0, 160.0),
        Velocity(0.0, 0.0),
        DotRenderable(radius=8),
    )
    debug.info(f"Player entity created: {player}")

    # UI elements
    dialog_btn = Button(
        rect=pygame.Rect(380, 10, 90, 30),
        text="Dialog",
        color=(100, 60, 120),
        hover_color=(140, 80, 160)
    )

    test_dialog = Dialog(
        title="Traveler's Rest",
        content="A weary merchant offers you a deal...",
        choices=[
            DialogChoice("Accept the offer"),
            DialogChoice("Decline politely"),
            DialogChoice("Ask for more details"),
        ]
    )

    # Game state
    running = True
    target = None
    last_click = None
    message = ""
    message_timer = 0
    frame_count = 0

    debug.info("Entering main loop")

    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        input_mgr.process_events(events)

        # Debug icon click (always check first)
        if debug_overlay.draw_icon(input_mgr):
            debug.overlay_visible = not debug.overlay_visible
            debug.info(f"Debug overlay {'opened' if debug.overlay_visible else 'closed'}")

        # If overlay is open, handle its input
        if debug.overlay_visible:
            if debug_overlay.draw_overlay(input_mgr):
                debug.overlay_visible = False
        else:
            # Normal game input (only when overlay closed)
            if input_mgr.clicked_this_frame:
                # Check if clicked on dialog button
                if not input_mgr.is_point_in_rect(input_mgr.click_pos, dialog_btn.rect):
                    if not test_dialog.visible:
                        last_click = input_mgr.click_pos
                        target = input_mgr.click_pos
                        debug.debug(f"Map click at {input_mgr.click_pos}")

        # Move player toward target
        if target:
            pos = esper.component_for_entity(player, Position)
            vel = esper.component_for_entity(player, Velocity)
            tx, ty = target
            dx = tx - pos.x
            dy = ty - pos.y
            dist2 = dx * dx + dy * dy
            if dist2 < 16:
                vel.vx, vel.vy = 0.0, 0.0
                target = None
            else:
                dist = dist2 ** 0.5
                speed = 160.0
                vel.vx = speed * dx / dist
                vel.vy = speed * dy / dist

        if message_timer > 0:
            message_timer -= dt

        # Process ECS
        esper.process(dt)

        # Draw UI (only if overlay not covering)
        if not debug.overlay_visible:
            if ui.draw_button(dialog_btn, input_mgr):
                test_dialog.visible = not test_dialog.visible
                debug.info(f"Dialog {'opened' if test_dialog.visible else 'closed'}")

            choice = ui.draw_dialog(test_dialog, input_mgr)
            if choice is not None:
                debug.info(f"Dialog choice selected: {choice + 1} - {test_dialog.choices[choice].text}")
                message = f"Selected: {test_dialog.choices[choice].text}"
                message_timer = 2.0
                test_dialog.visible = False

            if last_click and not test_dialog.visible:
                ui.draw_click_indicator(last_click)

            ui.draw_coordinates(input_mgr)

            if message_timer > 0:
                msg_surf = ui.font.render(message, True, (255, 255, 100))
                screen.blit(msg_surf, (50, 10))

        # Log periodic stats (every 5 seconds)
        if frame_count % 300 == 0:
            fps = clock.get_fps()
            debug.debug(f"FPS: {fps:.1f}, Entities: {len(list(esper.get_components(Position)))}")

        pygame.display.flip()
        await asyncio.sleep(0)

    debug.info("Game shutting down")
    pygame.quit()

if __name__ == '__main__':
    asyncio.run(main())
