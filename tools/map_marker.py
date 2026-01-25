#!/usr/bin/env python3
"""
Map Marker Tool - Click on the map to add location markers

Controls:
  - Click: Add a marker at that position
  - 1-4: Select marker type before clicking
  - S: Save markers to JSON
  - L: Load existing markers
  - U: Undo last marker
  - Q/Escape: Quit

Marker Types:
  1 = shop (player's plant shop/home) - Green
  2 = office (delivery destination) - Blue
  3 = restaurant (delivery destination) - Orange
  4 = house (customer home) - Yellow
"""

import pygame
import json
import os
import sys

# Add parent directory to path so we can find assets
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
MAP_IMAGE = "assets/map1.png"
OUTPUT_FILE = "data/map1_locations.json"
TOLERANCE = 50  # Default interaction radius

# Marker type colors and names
MARKER_TYPES = {
    "shop": {"color": (50, 200, 80), "key": pygame.K_1},
    "office": {"color": (80, 120, 220), "key": pygame.K_2},
    "restaurant": {"color": (240, 150, 50), "key": pygame.K_3},
    "house": {"color": (240, 220, 80), "key": pygame.K_4},
}


def main():
    pygame.init()

    # Load map image
    try:
        map_image = pygame.image.load(MAP_IMAGE)
    except Exception as e:
        print(f"Error loading {MAP_IMAGE}: {e}")
        sys.exit(1)

    img_w, img_h = map_image.get_size()

    # Create window sized to image
    screen = pygame.display.set_mode((img_w, img_h))
    pygame.display.set_caption("Map Marker Tool - Press H for help")

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    # State
    markers = []
    current_type = "house"
    typing_name = False
    current_name = ""
    pending_pos = None
    message = "Press 1-4 to select type, click to place marker"
    message_timer = 0
    show_help = False

    # Load existing markers if file exists
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                markers = json.load(f)
            message = f"Loaded {len(markers)} markers from {OUTPUT_FILE}"
            message_timer = 180
        except Exception as e:
            print(f"Could not load existing markers: {e}")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if typing_name:
                    # Handle name input
                    if event.key == pygame.K_RETURN:
                        if current_name.strip():
                            markers.append({
                                "name": current_name.strip(),
                                "x": pending_pos[0],
                                "y": pending_pos[1],
                                "type": current_type,
                                "tolerance": TOLERANCE
                            })
                            message = f"Added: {current_name.strip()} ({current_type})"
                            message_timer = 120
                        typing_name = False
                        current_name = ""
                        pending_pos = None
                    elif event.key == pygame.K_ESCAPE:
                        typing_name = False
                        current_name = ""
                        pending_pos = None
                    elif event.key == pygame.K_BACKSPACE:
                        current_name = current_name[:-1]
                    else:
                        if event.unicode.isprintable():
                            current_name += event.unicode
                else:
                    # Handle tool controls
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        running = False

                    elif event.key == pygame.K_h:
                        show_help = not show_help

                    elif event.key == pygame.K_1:
                        current_type = "shop"
                        message = "Selected: SHOP (green)"
                        message_timer = 90

                    elif event.key == pygame.K_2:
                        current_type = "office"
                        message = "Selected: OFFICE (blue)"
                        message_timer = 90

                    elif event.key == pygame.K_3:
                        current_type = "restaurant"
                        message = "Selected: RESTAURANT (orange)"
                        message_timer = 90

                    elif event.key == pygame.K_4:
                        current_type = "house"
                        message = "Selected: HOUSE (yellow)"
                        message_timer = 90

                    elif event.key == pygame.K_s:
                        # Save markers
                        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
                        with open(OUTPUT_FILE, "w") as f:
                            json.dump(markers, f, indent=2)
                        message = f"Saved {len(markers)} markers to {OUTPUT_FILE}"
                        message_timer = 180

                    elif event.key == pygame.K_l:
                        # Load markers
                        if os.path.exists(OUTPUT_FILE):
                            with open(OUTPUT_FILE, "r") as f:
                                markers = json.load(f)
                            message = f"Loaded {len(markers)} markers"
                            message_timer = 120

                    elif event.key == pygame.K_u:
                        # Undo last marker
                        if markers:
                            removed = markers.pop()
                            message = f"Removed: {removed['name']}"
                            message_timer = 90

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not typing_name and event.button == 1:
                    pending_pos = event.pos
                    typing_name = True
                    current_name = ""

        # Draw
        screen.blit(map_image, (0, 0))

        # Draw existing markers
        for marker in markers:
            color = MARKER_TYPES[marker["type"]]["color"]
            x, y = marker["x"], marker["y"]
            tolerance = marker.get("tolerance", TOLERANCE)

            # Draw tolerance circle
            pygame.draw.circle(screen, (*color, 100), (x, y), tolerance, 2)
            # Draw center dot
            pygame.draw.circle(screen, color, (x, y), 8)
            # Draw name
            name_surf = small_font.render(marker["name"], True, (255, 255, 255))
            name_bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 2))
            name_bg.fill((0, 0, 0))
            name_bg.set_alpha(180)
            screen.blit(name_bg, (x - name_surf.get_width() // 2 - 3, y + 12))
            screen.blit(name_surf, (x - name_surf.get_width() // 2, y + 13))

        # Draw pending marker
        if pending_pos:
            color = MARKER_TYPES[current_type]["color"]
            pygame.draw.circle(screen, color, pending_pos, TOLERANCE, 2)
            pygame.draw.circle(screen, color, pending_pos, 8)

        # Draw UI panel
        panel_rect = pygame.Rect(10, 10, 280, 130)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height))
        panel_surf.fill((20, 25, 35))
        panel_surf.set_alpha(220)
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (80, 90, 110), panel_rect, 2, border_radius=6)

        # Draw current type indicator
        y_offset = 18
        type_text = font.render(f"Type: {current_type.upper()}", True, MARKER_TYPES[current_type]["color"])
        screen.blit(type_text, (20, y_offset))

        # Draw marker count
        y_offset += 28
        count_text = font.render(f"Markers: {len(markers)}", True, (200, 200, 200))
        screen.blit(count_text, (20, y_offset))

        # Draw mouse position
        y_offset += 28
        mx, my = pygame.mouse.get_pos()
        pos_text = font.render(f"Pos: ({mx}, {my})", True, (150, 150, 150))
        screen.blit(pos_text, (20, y_offset))

        # Draw message or input prompt
        y_offset += 28
        if typing_name:
            prompt = f"Name: {current_name}_"
            prompt_surf = font.render(prompt, True, (255, 220, 100))
            screen.blit(prompt_surf, (20, y_offset))
        elif message_timer > 0:
            msg_surf = font.render(message, True, (180, 220, 180))
            screen.blit(msg_surf, (20, y_offset))
            message_timer -= 1

        # Draw help overlay
        if show_help:
            help_lines = [
                "=== MAP MARKER TOOL ===",
                "",
                "1 = Shop (green) - player's home",
                "2 = Office (blue) - delivery destination",
                "3 = Restaurant (orange) - delivery destination",
                "4 = House (yellow) - customer home",
                "",
                "Click = Place marker (then type name + Enter)",
                "S = Save markers to JSON",
                "L = Load markers from JSON",
                "U = Undo last marker",
                "H = Toggle this help",
                "Q/Esc = Quit",
            ]
            help_h = len(help_lines) * 26 + 20
            help_rect = pygame.Rect(img_w // 2 - 200, img_h // 2 - help_h // 2, 400, help_h)
            help_surf = pygame.Surface((help_rect.width, help_rect.height))
            help_surf.fill((20, 25, 35))
            help_surf.set_alpha(240)
            screen.blit(help_surf, help_rect.topleft)
            pygame.draw.rect(screen, (100, 150, 200), help_rect, 2, border_radius=8)

            for i, line in enumerate(help_lines):
                color = (255, 220, 100) if i == 0 else (200, 200, 200)
                line_surf = font.render(line, True, color)
                screen.blit(line_surf, (help_rect.x + 20, help_rect.y + 10 + i * 26))

        # Draw controls hint at bottom
        hint = "H=Help  S=Save  1-4=Type  Click=Add  Q=Quit"
        hint_surf = small_font.render(hint, True, (120, 120, 120))
        screen.blit(hint_surf, (img_w // 2 - hint_surf.get_width() // 2, img_h - 25))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    # Ask to save on exit if there are unsaved markers
    if markers:
        print(f"\nYou have {len(markers)} markers.")
        save = input("Save before exit? (y/n): ").strip().lower()
        if save == 'y':
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w") as f:
                json.dump(markers, f, indent=2)
            print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
