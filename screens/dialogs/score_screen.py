"""
End Game Score Screen - Shows final stats after completing all maps.

Features:
- Total deliveries count
- Plant grid (5 columns) with delivery counts
- Auto-scrolling plant area
- Plant names under images
"""

import pygame
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from shared.debug_log import debug


class ScoreScreen:
    """
    Full screen dialog showing final game stats with plant delivery grid.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.visible = False

        # Stats to display
        self.total_orders = 0
        self.total_plants = 0
        self.total_score = 0

        # Plant delivery counts: filename -> (name_fi, count)
        self.plant_counts: Dict[str, Tuple[str, int]] = {}

        # Dialog bounds (same size as delivery dialog)
        self.dialog_rect = pygame.Rect(
            (self.screen_width - 1400) // 2,
            (self.screen_height - 900) // 2,
            1400,
            900
        )

        # Plant grid area
        self.grid_area = pygame.Rect(
            self.dialog_rect.left + 50,
            self.dialog_rect.top + 200,
            self.dialog_rect.width - 100,
            self.dialog_rect.height - 300
        )

        # Grid layout
        self.plant_size = 200
        self.plant_width = int(self.plant_size / 3 * 2.5)
        self.columns = 5
        self.row_height = 240  # plant + name + spacing
        self.column_width = self.grid_area.width // self.columns

        # Scrolling state
        self.scroll_offset = 0.0
        self.scroll_speed = 20.0  # pixels per second

        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.header_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.button_font = pygame.font.Font(None, 52)

        # Colors
        self.bg_color = (30, 45, 60)
        self.text_color = (255, 255, 255)
        self.accent_color = (100, 200, 150)
        self.secondary_color = (180, 180, 180)
        self.button_color = (60, 100, 140)
        self.button_hover_color = (80, 120, 160)
        self.grid_bg_color = (40, 55, 70)
        self.count_color = (205, 220, 100)

        # Button
        self.ok_button_rect = pygame.Rect(0, 0, 0, 0)

        # Plant image cache
        self.plant_image_cache: Dict[str, pygame.Surface] = {}

        # Callback for when dialog is closed
        self.on_close = None

        # Scroll direction: 1 = down, -1 = up
        self.scroll_direction = 1


    def open(self, total_orders: int, total_plants: int, total_score: int,
             plant_counts: Dict[str, Tuple[str, int]]):
        """
        Open the dialog with final stats.

        Args:
            total_orders: Total orders completed across all maps
            total_plants: Total plants delivered
            total_score: Total score
            plant_counts: Dict of filename -> (name_fi, count)
        """
        self.visible = True
        self.total_orders = total_orders
        self.total_plants = total_plants
        self.total_score = total_score
        self.plant_counts = plant_counts
        self.scroll_offset = 0.0
        self.scroll_direction = 1  # Always start scrolling down

        debug.info(f"ScoreScreen opened: {total_orders} orders, {total_plants} plants, {total_score} score")

    def close(self):
        """Close the dialog."""
        self.visible = False

        if self.on_close is not None:
            self.on_close()

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        plant_path = Path(__file__).parent.parent.parent / "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            scaled = pygame.transform.smoothscale(image, (self.plant_width, self.plant_size))
            self.plant_image_cache[filename] = scaled
            return scaled
        except Exception as e:
            debug.error(f"Failed to load plant image {filename}: {e}")
            return None

    def _get_total_rows(self) -> int:
        """Calculate total rows needed for all plants."""
        plant_count = len(self.plant_counts)
        return (plant_count + self.columns - 1) // self.columns

    def _get_max_scroll(self) -> float:
        """Calculate maximum scroll offset."""
        total_height = self._get_total_rows() * self.row_height + 30
        visible_height = self.grid_area.height
        return max(0, total_height - visible_height)

    def handle_input(self, input_mgr) -> Optional[str]:
        """Handle input. Returns action string or None."""
        if not self.visible:
            return None

        if input_mgr.clicked_in_rect(self.ok_button_rect):
            self.close()
            return "score_closed"

        return None

    def update(self, dt: float):
        """Update animations."""
        if not self.visible:
            return

        # auto-scroll
        max_scroll = self._get_max_scroll()
        if max_scroll > 0:
            self.scroll_offset += self.scroll_direction * self.scroll_speed * dt
            # Clamp and reverse direction if needed
            if self.scroll_offset >= max_scroll:
                self.scroll_offset = max_scroll
                if self.scroll_direction == 1:
                    self.scroll_direction = -1
            elif self.scroll_offset <= 0:
                self.scroll_offset = 0
                if self.scroll_direction == -1:
                    self.scroll_direction = 1

    def draw(self, input_mgr):
        """Draw the dialog."""
        if not self.visible:
            return

        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Dialog background
        pygame.draw.rect(self.screen, self.bg_color, self.dialog_rect, border_radius=7)
        pygame.draw.rect(self.screen, self.accent_color, self.dialog_rect, width=4, border_radius=15)

        # Title
        title_text = "PELI LÄPI - Maailma pelastettu!"
        title_surface = self.title_font.render(title_text, True, self.accent_color)
        title_rect = title_surface.get_rect(centerx=self.dialog_rect.centerx, top=self.dialog_rect.top + 30)
        self.screen.blit(title_surface, title_rect)

        # Stats row
        stats_y = title_rect.bottom + 20
        stats = [
            f"Tilauksia: {self.total_orders}",
            f"Kasveja: {self.total_plants}",
            f"Pisteet: {self.total_score}"
        ]

        stat_x = self.dialog_rect.left + 150
        for stat in stats:
            stat_surface = self.header_font.render(stat, True, self.text_color)
            self.screen.blit(stat_surface, (stat_x, stats_y))
            stat_x += 400

        # Grid area background
        pygame.draw.rect(self.screen, self.grid_bg_color, self.grid_area, border_radius=8)

        # Create clipping surface for grid
        grid_surface = pygame.Surface((self.grid_area.width, self.grid_area.height), pygame.SRCALPHA)
        grid_surface.fill((0, 0, 0, 0))

        # Draw plants in grid
        plant_list = list(self.plant_counts.items())
        plant_list.sort(key=lambda x: x[1][1], reverse=True)  # Sort by count descending

        for idx, (filename, (name_fi, count)) in enumerate(plant_list):
            col = idx % self.columns
            row = idx // self.columns

            # Calculate position
            x = col * self.column_width + (self.column_width - self.plant_width) // 2
            y = row * self.row_height + 10 - int(self.scroll_offset)

            # Skip if not visible
            if y + self.row_height < 0 or y > self.grid_area.height:
                continue

            # Draw plant image
            image = self._load_plant_image(filename)
            if image:
                grid_surface.blit(image, (x, y))

            # Draw count badge
            count_text = str(count)
            count_surface = self.text_font.render(count_text, True, self.count_color)
            count_rect = count_surface.get_rect(right=x + self.plant_width - 5, top=y + 5)

            # Badge background
            badge_rect = count_rect.inflate(10, 4)
            pygame.draw.rect(grid_surface, (100, 100, 100, 180), badge_rect, border_radius=2)
            grid_surface.blit(count_surface, count_rect)

            # Draw plant name
            name_y = y + self.plant_size + 5
            if len(name_fi) > 12:
                display_name = name_fi[:11] + "..."
            else:
                display_name = name_fi
            name_surface = self.small_font.render(display_name, True, self.secondary_color)
            name_rect = name_surface.get_rect(centerx=x + self.plant_size // 2, top=name_y)
            grid_surface.blit(name_surface, name_rect)

        # Blit grid surface
        self.screen.blit(grid_surface, self.grid_area.topleft)

        # Draw grid border
        pygame.draw.rect(self.screen, self.accent_color, self.grid_area, width=1, border_radius=2)

        # Draw OK button
        button_width = 120
        button_height = 60
        self.ok_button_rect = pygame.Rect(
            self.dialog_rect.bottomright[0] - button_width - 40,
            self.dialog_rect.bottom - 90,
            button_width,
            button_height
        )

        hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, self.ok_button_rect)
        button_color = self.button_hover_color if hover else self.button_color
        pygame.draw.rect(self.screen, button_color, self.ok_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.accent_color, self.ok_button_rect, width=3, border_radius=10)

        ok_text = self.button_font.render(" -.^ ", True, self.text_color)
        ok_rect = ok_text.get_rect(center=self.ok_button_rect.center)
        self.screen.blit(ok_text, ok_rect)
