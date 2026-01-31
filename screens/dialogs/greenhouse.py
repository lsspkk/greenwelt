"""
Greenhouse Dialog - View and manage plants at the greenhouse.

This dialog shows:
- Available plants in the greenhouse (how many of each type)
- Plants the player is currently carrying
- Plus/minus buttons to pick up or drop plants (only when inside pick radius)

When player is inside greenhouse pick_radius:
- Title: "Valitse kasvit"
- Can pick up plants from greenhouse
- Can drop plants back to greenhouse

When player is outside the radius:
- Title: "Kasvitilanne"
- Can only view current inventory status
- Plus/minus buttons are disabled
"""

import pygame
import random
from pathlib import Path
from typing import Optional, List, Dict

from shared.debug_log import debug


class GreenhouseScreen:
    """
    Full screen greenhouse dialog for viewing and managing plants.

    Shows a greenhouse background image that fades to 10% opacity,
    then shows a grid of available plants and the player's inventory.
    Pick/drop functionality is only available when near the greenhouse.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        self.visible = False

        # Is player inside the greenhouse pick radius?
        self.can_interact = False

        # Fade animation state
        self.fade_timer = 0.0
        self.fade_duration = 1.6
        self.background_alpha = 255
        self.fade_complete = False

        # Background image
        self.background_image: Optional[pygame.Surface] = None
        self.background_scaled: Optional[pygame.Surface] = None

        # Pick a random greenhouse image (1-7)
        self.greenhouse_index = random.randint(1, 7)

        # Fonts
        self.title_font = pygame.font.Font(None, 52)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 32)
        self.button_font = pygame.font.Font(None, 42)

        # Colors
        self.bg_color = (30, 40, 50)
        self.panel_color = (40, 55, 70)
        self.text_color = (255, 255, 255)
        self.button_color = (60, 100, 80)
        self.button_hover_color = (80, 120, 100)
        self.button_disabled_color = (50, 50, 60)
        self.accent_color = (100, 180, 120)

        # Plant grid settings
        self.plants_per_row = 5
        self.visible_rows = 2
        self.scroll_row = 0
        self.plant_size = 240

        # Load all available plant filenames
        self.all_plants: List[str] = []
        self._load_plant_list()

        # Cache for loaded plant images
        self.plant_image_cache: Dict[str, pygame.Surface] = {}

        # Button rects (set during draw)
        self.scroll_up_rect = pygame.Rect(0, 0, 0, 0)
        self.scroll_down_rect = pygame.Rect(0, 0, 0, 0)
        self.close_button_rect = pygame.Rect(0, 0, 0, 0)
        self.plus_button_rects: List[pygame.Rect] = []
        self.minus_button_rects: List[pygame.Rect] = []

        # References to inventory and callbacks (set when opened)
        self.player_inventory: Optional[Dict[str, int]] = None
        self.greenhouse_inventory: Optional[Dict[str, int]] = None
        self.pick_plant_callback = None
        self.drop_plant_callback = None
        self.can_pick_callback = None

    def _load_plant_list(self):
        """Load the list of all available plant image filenames."""
        plant_folder = Path(__file__).parent.parent.parent / \
            "assets" / "plants" / "one"

        try:
            files = list(plant_folder.glob("*.png"))
            for f in files:
                self.all_plants.append(f.name)
            self.all_plants.sort()
            debug.info(
                f"Loaded {len(self.all_plants)} plant types for greenhouse")
        except Exception as e:
            debug.error(f"Failed to load plant list: {e}")

    def _load_background(self):
        """Load the greenhouse background image."""
        image_path = Path(__file__).parent.parent.parent / "assets" / \
            "images" / f"greenhouse{self.greenhouse_index}.png"

        try:
            self.background_image = pygame.image.load(
                str(image_path)).convert()
            self.background_scaled = self._scale_to_fit(
                self.background_image,
                self.screen_width,
                self.screen_height
            )
            debug.info(
                f"Loaded greenhouse background: greenhouse{self.greenhouse_index}.png")
        except Exception as e:
            debug.error(f"Failed to load greenhouse background: {e}")

    def _scale_to_fit(self, image: pygame.Surface, max_width: int, max_height: int) -> pygame.Surface:
        """Scale image to fit within bounds while keeping aspect ratio."""
        img_width = image.get_width()
        img_height = image.get_height()

        scale_w = max_width / img_width
        scale_h = max_height / img_height
        scale = min(scale_w, scale_h)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        return pygame.transform.smoothscale(image, (new_width, new_height))

    def _load_plant_image(self, filename: str) -> Optional[pygame.Surface]:
        """Load and cache a plant image."""
        if filename in self.plant_image_cache:
            return self.plant_image_cache[filename]

        plant_path = Path(__file__).parent.parent.parent / \
            "assets" / "plants" / "one" / filename

        try:
            image = pygame.image.load(str(plant_path)).convert_alpha()
            width_ratio = self.plant_size / image.get_width()
            height_ratio = self.plant_size / image.get_height()
            scale = min(width_ratio, height_ratio)

            plant_width = int(image.get_width() * scale)
            plant_height = int(image.get_height() * scale)

            scaled = pygame.transform.smoothscale(
                image, (plant_width, plant_height))
            self.plant_image_cache[filename] = scaled
            return scaled
        except Exception as e:
            debug.error(f"Failed to load plant image {filename}: {e}")
            return None

    def open(self, player_inventory: Dict[str, int],
             greenhouse_inventory: Dict[str, int],
             pick_callback, drop_callback, can_pick_callback,
             is_inside_radius: bool):
        """
        Open the greenhouse dialog.

        Args:
            player_inventory: Reference to the player's carried plants
            greenhouse_inventory: Reference to the greenhouse's plant stock
            pick_callback: Function to call when picking up a plant (takes filename)
            drop_callback: Function to call when dropping a plant (takes filename)
            can_pick_callback: Function to check if player can pick more plants
            is_inside_radius: Whether player is close enough to pick/drop plants
        """
        self.player_inventory = player_inventory
        self.greenhouse_inventory = greenhouse_inventory
        self.pick_plant_callback = pick_callback
        self.drop_plant_callback = drop_callback
        self.can_pick_callback = can_pick_callback
        self.can_interact = is_inside_radius

        # Reset fade animation
        self.fade_timer = 0.0
        self.background_alpha = 255
        self.fade_complete = False
        self.scroll_row = 0

        # Clear plant image cache
        self.plant_image_cache = {}

        # Load background image
        self._load_background()

        self.visible = True

        # Log what mode we're in
        if is_inside_radius:
            debug.info("Greenhouse opened - can pick/drop plants")
        else:
            debug.info("Greenhouse opened - view only (outside radius)")

    def close(self):
        """Close the greenhouse dialog."""
        self.visible = False
        self.player_inventory = None
        self.greenhouse_inventory = None
        debug.info("Greenhouse closed")

    def _get_total_rows(self) -> int:
        """Get total number of rows of plants."""
        if len(self.all_plants) == 0:
            return 0
        return (len(self.all_plants) + self.plants_per_row - 1) // self.plants_per_row

    def _get_max_scroll(self) -> int:
        """Get maximum scroll position."""
        total = self._get_total_rows()
        max_scroll = total - self.visible_rows
        if max_scroll < 0:
            max_scroll = 0
        return max_scroll

    def _get_inventory_total(self) -> int:
        """Get total plants in player inventory."""
        if self.player_inventory is None:
            return 0
        total = 0
        for count in self.player_inventory.values():
            total = total + count
        return total

    def _get_greenhouse_count(self, plant_filename: str) -> int:
        """Get count of a specific plant in greenhouse inventory."""
        if self.greenhouse_inventory is None:
            return 0
        return self.greenhouse_inventory.get(plant_filename, 0)

    def update(self, dt: float):
        """Update the greenhouse (fade animation)."""
        if not self.visible:
            return

        if not self.fade_complete:
            self.fade_timer = self.fade_timer + dt
            if self.fade_timer >= self.fade_duration:
                self.fade_timer = self.fade_duration
                self.fade_complete = True

            progress = self.fade_timer / self.fade_duration
            self.background_alpha = int(255 - (255 - 100) * progress)

    def handle_input(self, input_mgr) -> Optional[str]:
        """
        Handle input while greenhouse is open.
        Returns action string or None.
        """
        if not self.visible:
            return None

        # If fade not complete, don't handle UI input yet
        if not self.fade_complete:
            return None

        # Close button
        if input_mgr.clicked_in_rect(self.close_button_rect):
            self.close()
            return "close_greenhouse"

        # Page up (move 2 rows)
        if input_mgr.clicked_in_rect(self.scroll_up_rect):
            if self.scroll_row > 0:
                self.scroll_row = self.scroll_row - 2
                if self.scroll_row < 0:
                    self.scroll_row = 0
            return "page_up"

        # Page down (move 2 rows)
        if input_mgr.clicked_in_rect(self.scroll_down_rect):
            max_scroll = self._get_max_scroll()
            if self.scroll_row < max_scroll:
                self.scroll_row = self.scroll_row + 2
                if self.scroll_row > max_scroll:
                    self.scroll_row = max_scroll
            return "page_down"

        # Only handle pick/drop if player is inside radius
        if not self.can_interact:
            return None

        # Plus buttons (pick up plant from greenhouse)
        for i in range(len(self.plus_button_rects)):
            if input_mgr.clicked_in_rect(self.plus_button_rects[i]):
                plant_index = self.scroll_row * self.plants_per_row + i
                if plant_index < len(self.all_plants):
                    plant_file = self.all_plants[plant_index]
                    if self.pick_plant_callback is not None:
                        self.pick_plant_callback(plant_file)
                return "pick_plant"

        # Minus buttons (drop plant back to greenhouse)
        for i in range(len(self.minus_button_rects)):
            if input_mgr.clicked_in_rect(self.minus_button_rects[i]):
                plant_index = self.scroll_row * self.plants_per_row + i
                if plant_index < len(self.all_plants):
                    plant_file = self.all_plants[plant_index]
                    if self.drop_plant_callback is not None:
                        self.drop_plant_callback(plant_file)
                return "drop_plant"

        return None

    def draw(self):
        """Draw the greenhouse dialog."""
        if not self.visible:
            return

        # Fill entire screen with black background
        self.screen.fill((0, 0, 0))

        # Clear button rects
        self.plus_button_rects = []
        self.minus_button_rects = []

        # Draw background image centered
        if self.background_scaled is not None:
            bg_surface = self.background_scaled.copy()
            bg_surface.set_alpha(self.background_alpha)

            bg_x = (self.screen_width - bg_surface.get_width()) // 2
            bg_y = (self.screen_height - bg_surface.get_height()) // 2

            self.screen.blit(bg_surface, (bg_x, bg_y))

        # If fade not complete, just show the image
        if not self.fade_complete:
            return

        # Draw UI panels on top
        self._draw_plant_grid()
        self._draw_inventory_panel()
        self._draw_close_button()

    def _draw_plant_grid(self):
        """Draw the grid of plants with counts and +/- buttons."""
        panel_x = 50
        panel_y = 100

        # Title changes based on whether player can interact
        if self.can_interact:
            title = "Valitse kasvit"
        else:
            title = "Kasvitilanne"

        title_text = self.title_font.render(title, True, self.text_color)
        self.screen.blit(title_text, (panel_x + 20, panel_y + 15))

        # Scroll buttons at bottom
        button_size = 60
        scroll_x = self.screen_width - 100 - 60 - 20 - 60 - 100
        scroll_down_x = self.screen_width - 100 - 60 - 100
        scroll_y = self.screen_height - 100

        # Draw scroll up button
        self.scroll_up_rect = pygame.Rect(
            scroll_x, scroll_y, button_size, button_size)
        can_scroll_up = self.scroll_row > 0
        up_color = self.button_color if can_scroll_up else self.button_disabled_color
        pygame.draw.rect(self.screen, up_color,
                         self.scroll_up_rect, border_radius=10)
        up_text = self.button_font.render("^", True, self.text_color)
        up_text_rect = up_text.get_rect(center=self.scroll_up_rect.center)
        self.screen.blit(up_text, up_text_rect)

        # Draw scroll down button
        self.scroll_down_rect = pygame.Rect(
            scroll_down_x, scroll_y, button_size, button_size)
        can_scroll_down = self.scroll_row < self._get_max_scroll()
        down_color = self.button_color if can_scroll_down else self.button_disabled_color
        pygame.draw.rect(self.screen, down_color,
                         self.scroll_down_rect, border_radius=10)
        down_text = self.button_font.render("v", True, self.text_color)
        down_text_rect = down_text.get_rect(
            center=self.scroll_down_rect.center)
        self.screen.blit(down_text, down_text_rect)

        # Draw plants grid
        grid_start_x = panel_x + 30
        grid_start_y = panel_y + 70
        item_width = self.plant_size + 20
        item_height = self.plant_size + 80

        # Check if player can pick more plants
        can_pick = False
        if self.can_interact and self.can_pick_callback is not None:
            can_pick = self.can_pick_callback()

        for row in range(self.visible_rows):
            for col in range(self.plants_per_row):
                plant_index = (self.scroll_row + row) * \
                    self.plants_per_row + col

                if plant_index >= len(self.all_plants):
                    continue

                plant_file = self.all_plants[plant_index]
                item_x = grid_start_x + col * item_width
                item_y = grid_start_y + row * item_height

                # Draw plant image
                plant_img = self._load_plant_image(plant_file)
                if plant_img is not None:
                    self.screen.blit(plant_img, (item_x, item_y))

                # Draw greenhouse stock count on top-left of plant image
                greenhouse_count = self._get_greenhouse_count(plant_file)
                count_text = self.small_font.render(
                    f"x{greenhouse_count}", True, (255, 255, 100))
                count_bg = pygame.Rect(
                    item_x, item_y, count_text.get_width() + 10, 28)
                pygame.draw.rect(self.screen, (0, 0, 0, 180),
                                 count_bg, border_radius=5)
                self.screen.blit(count_text, (item_x + 5, item_y + 2))

                # Draw +/- buttons below plant
                btn_width = 50
                btn_height = 40
                btn_y = item_y + self.plant_size + 5

                # Plus button - only enabled if player can pick and greenhouse has stock
                plus_rect = pygame.Rect(item_x, btn_y, btn_width, btn_height)
                plus_enabled = can_pick and greenhouse_count > 0
                plus_color = self.button_color if plus_enabled else self.button_disabled_color
                pygame.draw.rect(self.screen, plus_color,
                                 plus_rect, border_radius=8)
                plus_text = self.text_font.render("+", True, self.text_color)
                plus_text_rect = plus_text.get_rect(center=plus_rect.center)
                self.screen.blit(plus_text, plus_text_rect)
                self.plus_button_rects.append(plus_rect)

                # Minus button - only enabled if player has this plant and can interact
                minus_rect = pygame.Rect(
                    item_x + btn_width + 10, btn_y, btn_width, btn_height)
                has_plant = False
                if self.player_inventory is not None:
                    if plant_file in self.player_inventory:
                        if self.player_inventory[plant_file] > 0:
                            has_plant = True

                minus_enabled = self.can_interact and has_plant
                minus_color = self.button_color if minus_enabled else self.button_disabled_color
                pygame.draw.rect(self.screen, minus_color,
                                 minus_rect, border_radius=8)
                minus_text = self.text_font.render("-", True, self.text_color)
                minus_text_rect = minus_text.get_rect(center=minus_rect.center)
                self.screen.blit(minus_text, minus_text_rect)
                self.minus_button_rects.append(minus_rect)

    def _draw_inventory_panel(self):
        """Draw the panel showing what the player is carrying."""
        panel_width = 400
        panel_height = 600
        panel_x = self.screen_width - panel_width - 50
        panel_y = 100

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, self.panel_color,
                         panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.accent_color,
                         panel_rect, 3, border_radius=15)

        # Title
        total = self._get_inventory_total()
        title_text = self.title_font.render(
            f"Kantamus ({total}/15)", True, self.text_color)
        self.screen.blit(title_text, (panel_x + 20, panel_y + 15))

        # List of plants being carried
        list_y = panel_y + 70

        if self.player_inventory is None:
            return

        if len(self.player_inventory) == 0:
            empty_text = self.text_font.render(
                "Ei kasveja", True, (150, 150, 150))
            self.screen.blit(empty_text, (panel_x + 20, list_y))
            return

        # Sort by plant name for consistent display
        sorted_plants = sorted(self.player_inventory.keys())

        for plant_file in sorted_plants:
            count = self.player_inventory[plant_file]
            if count <= 0:
                continue

            # Get plant name from filename (remove -01.png etc)
            plant_name = plant_file.split("-")[0]

            # Draw plant entry
            entry_text = f"{plant_name}: {count}"
            text_surface = self.text_font.render(
                entry_text, True, self.text_color)
            self.screen.blit(text_surface, (panel_x + 20, list_y))

            list_y = list_y + 35

            # Stop if we run out of space
            if list_y > panel_y + panel_height - 50:
                more_text = self.small_font.render(
                    "...", True, (150, 150, 150))
                self.screen.blit(more_text, (panel_x + 20, list_y))
                break

    def _draw_close_button(self):
        """Draw the close button."""
        btn_width = 120
        btn_height = 60
        btn_x = self.screen_width - 100 - 50
        btn_y = self.screen_height - 100

        self.close_button_rect = pygame.Rect(
            btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, self.button_color,
                         self.close_button_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.accent_color,
                         self.close_button_rect, 3, border_radius=12)

        close_text = self.button_font.render("--O.O--", True, self.text_color)
        text_rect = close_text.get_rect(center=self.close_button_rect.center)
        self.screen.blit(close_text, text_rect)
