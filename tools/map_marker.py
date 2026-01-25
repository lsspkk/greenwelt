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
TOLERANCE = 50

# Marker type colors
MARKER_TYPES = {
    "shop": {"color": (50, 200, 80), "key": pygame.K_1},
    "office": {"color": (80, 120, 220), "key": pygame.K_2},
    "restaurant": {"color": (240, 150, 50), "key": pygame.K_3},
    "house": {"color": (240, 220, 80), "key": pygame.K_4},
}

# State variables (module level for simple access)
markers = []
current_type = "house"
typing_name = False
current_name = ""
pending_pos = None
message = ""
message_timer = 0
show_help = False
running = True


def set_message(text, duration=90):
    """Set a temporary message to display"""
    global message, message_timer
    message = text
    message_timer = duration


def load_markers():
    """Load markers from JSON file"""
    global markers
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            markers = json.load(f)
        set_message(f"Loaded {len(markers)} markers", 120)


def save_markers():
    """Save markers to JSON file"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(markers, f, indent=2)
    set_message(f"Saved {len(markers)} markers to {OUTPUT_FILE}", 180)


def undo_last_marker():
    """Remove the last added marker"""
    global markers
    if markers:
        removed = markers.pop()
        set_message(f"Removed: {removed['name']}", 90)


def select_type(type_name):
    """Select the current marker type"""
    global current_type
    current_type = type_name
    set_message(f"Selected: {type_name.upper()}", 90)


def start_typing(pos):
    """Start typing a name for a new marker"""
    global typing_name, current_name, pending_pos
    pending_pos = pos
    typing_name = True
    current_name = ""


def cancel_typing():
    """Cancel the current name input"""
    global typing_name, current_name, pending_pos
    typing_name = False
    current_name = ""
    pending_pos = None


def finish_typing():
    """Finish typing and add the marker"""
    global typing_name, current_name, pending_pos, markers
    if current_name.strip():
        markers.append({
            "name": current_name.strip(),
            "x": pending_pos[0],
            "y": pending_pos[1],
            "type": current_type,
            "tolerance": TOLERANCE
        })
        set_message(f"Added: {current_name.strip()} ({current_type})", 120)
    cancel_typing()


def handle_typing_key(event):
    """Handle keyboard input while typing a name"""
    global current_name
    if event.key == pygame.K_RETURN:
        finish_typing()
    elif event.key == pygame.K_ESCAPE:
        cancel_typing()
    elif event.key == pygame.K_BACKSPACE:
        current_name = current_name[:-1]
    elif event.unicode.isprintable():
        current_name += event.unicode


def handle_tool_key(event):
    """Handle keyboard input for tool controls"""
    global running, show_help
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
        running = False
    elif event.key == pygame.K_h:
        show_help = not show_help
    elif event.key == pygame.K_1:
        select_type("shop")
    elif event.key == pygame.K_2:
        select_type("office")
    elif event.key == pygame.K_3:
        select_type("restaurant")
    elif event.key == pygame.K_4:
        select_type("house")
    elif event.key == pygame.K_s:
        save_markers()
    elif event.key == pygame.K_l:
        load_markers()
    elif event.key == pygame.K_u:
        undo_last_marker()


def handle_event(event):
    """Handle a single pygame event"""
    global running
    if event.type == pygame.QUIT:
        running = False
    elif event.type == pygame.KEYDOWN:
        if typing_name:
            handle_typing_key(event)
        else:
            handle_tool_key(event)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        if not typing_name and event.button == 1:
            start_typing(event.pos)


def draw_markers(screen, small_font):
    """Draw all markers on the screen"""
    for marker in markers:
        color = MARKER_TYPES[marker["type"]]["color"]
        x, y = marker["x"], marker["y"]
        tolerance = marker.get("tolerance", TOLERANCE)

        pygame.draw.circle(screen, (*color, 100), (x, y), tolerance, 2)
        pygame.draw.circle(screen, color, (x, y), 8)

        name_surf = small_font.render(marker["name"], True, (255, 255, 255))
        name_bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 2))
        name_bg.fill((0, 0, 0))
        name_bg.set_alpha(180)
        screen.blit(name_bg, (x - name_surf.get_width() // 2 - 3, y + 12))
        screen.blit(name_surf, (x - name_surf.get_width() // 2, y + 13))


def draw_pending_marker(screen):
    """Draw the marker being placed"""
    if pending_pos:
        color = MARKER_TYPES[current_type]["color"]
        pygame.draw.circle(screen, color, pending_pos, TOLERANCE, 2)
        pygame.draw.circle(screen, color, pending_pos, 8)


def draw_ui_panel(screen, font):
    """Draw the info panel in top left"""
    global message_timer

    panel_rect = pygame.Rect(10, 10, 280, 130)
    panel_surf = pygame.Surface((panel_rect.width, panel_rect.height))
    panel_surf.fill((20, 25, 35))
    panel_surf.set_alpha(220)
    screen.blit(panel_surf, panel_rect.topleft)
    pygame.draw.rect(screen, (80, 90, 110), panel_rect, 2, border_radius=6)

    y = 18
    type_text = font.render(f"Type: {current_type.upper()}", True, MARKER_TYPES[current_type]["color"])
    screen.blit(type_text, (20, y))

    y += 28
    count_text = font.render(f"Markers: {len(markers)}", True, (200, 200, 200))
    screen.blit(count_text, (20, y))

    y += 28
    mx, my = pygame.mouse.get_pos()
    pos_text = font.render(f"Pos: ({mx}, {my})", True, (150, 150, 150))
    screen.blit(pos_text, (20, y))

    y += 28
    if typing_name:
        prompt = f"Name: {current_name}_"
        prompt_surf = font.render(prompt, True, (255, 220, 100))
        screen.blit(prompt_surf, (20, y))
    elif message_timer > 0:
        msg_surf = font.render(message, True, (180, 220, 180))
        screen.blit(msg_surf, (20, y))
        message_timer -= 1


def draw_help_overlay(screen, font, img_w, img_h):
    """Draw the help overlay"""
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


def draw_hint(screen, small_font, img_w, img_h):
    """Draw controls hint at bottom"""
    hint = "H=Help  S=Save  1-4=Type  Click=Add  Q=Quit"
    hint_surf = small_font.render(hint, True, (120, 120, 120))
    screen.blit(hint_surf, (img_w // 2 - hint_surf.get_width() // 2, img_h - 25))


def main():
    global running

    pygame.init()

    # Load map image
    try:
        map_image = pygame.image.load(MAP_IMAGE)
    except Exception as e:
        print(f"Error loading {MAP_IMAGE}: {e}")
        sys.exit(1)

    img_w, img_h = map_image.get_size()
    screen = pygame.display.set_mode((img_w, img_h))
    pygame.display.set_caption("Map Marker Tool - Press H for help")

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()

    # Load existing markers
    if os.path.exists(OUTPUT_FILE):
        load_markers()

    set_message("Press 1-4 to select type, click to place marker", 180)

    while running:
        for event in pygame.event.get():
            handle_event(event)

        # Draw
        screen.blit(map_image, (0, 0))
        draw_markers(screen, small_font)
        draw_pending_marker(screen)
        draw_ui_panel(screen, font)

        if show_help:
            draw_help_overlay(screen, font, img_w, img_h)

        draw_hint(screen, small_font, img_w, img_h)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    # Ask to save on exit
    if markers:
        print(f"\nYou have {len(markers)} markers.")
        save = input("Save before exit? (y/n): ").strip().lower()
        if save == 'y':
            save_markers()
            print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
