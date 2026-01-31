#!/usr/bin/env python3
"""
Road Painter Tool - Draw roads on the map

Controls:
  - T: Switch to Line mode (default) - click start, click end
  - A: Switch to Paint mode - click and drag to paint
  - Mouse Wheel / +/-: Change brush width
  - U: Undo last stroke
  - C: Clear all roads
  - S: Save roads to JSON
  - L: Load existing roads
  - Q/Escape: Quit

Roads are drawn with gray color and semi-transparency.
"""

import pygame
import json
import os
import sys

# Add parent directory to path so we can find assets
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
MAP_IMAGE = "assets/map2.png"
OUTPUT_FILE = "data/map2_roads.json"

# Road settings
ROAD_COLOR = (100, 100, 100)
ROAD_ALPHA = 180
MIN_WIDTH = 10
MAX_WIDTH = 100
DEFAULT_WIDTH = 30

# State variables
strokes = []  # List of {points: [(x,y),...], width: int}
current_stroke = None
brush_width = DEFAULT_WIDTH
message = ""
message_timer = 0
show_help = False
running = True
is_drawing = False
draw_mode = "line"  # "line" or "paint"
click_start = None  # For line mode


def set_message(text, duration=90):
    """Set a temporary message to display"""
    global message, message_timer
    message = text
    message_timer = duration


def load_roads():
    """Load roads from JSON file"""y
    global strokes
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
            strokes = data.get("strokes", [])
        set_message(f"Loaded {len(strokes)} strokes", 120)


def save_roads():
    """Save roads to JSON file"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    data = {
        "strokes": strokes,
        "color": ROAD_COLOR,
        "alpha": ROAD_ALPHA
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    set_message(f"Saved {len(strokes)} strokes to {OUTPUT_FILE}", 180)


def undo_last_stroke():
    """Remove the last stroke"""
    global strokes
    if strokes:
        strokes.pop()
        set_message(f"Undo - {len(strokes)} strokes remaining", 90)


def clear_all():
    """Clear all strokes"""
    global strokes
    strokes = []
    set_message("Cleared all roads", 90)


def change_width(delta):
    """Change brush width"""
    global brush_width
    brush_width = max(MIN_WIDTH, min(MAX_WIDTH, brush_width + delta))
    set_message(f"Brush width: {brush_width}", 60)


def start_stroke(pos):
    """Start a new stroke"""
    global current_stroke, is_drawing
    current_stroke = {
        "points": [pos],
        "width": brush_width
    }
    is_drawing = True


def add_point(pos):
    """Add a point to the current stroke"""
    if current_stroke and is_drawing:
        last = current_stroke["points"][-1]
        # Only add if moved enough
        dx = pos[0] - last[0]
        dy = pos[1] - last[1]
        if dx * dx + dy * dy > 4:
            current_stroke["points"].append(pos)


def finish_stroke():
    """Finish the current stroke"""
    global current_stroke, is_drawing, strokes
    if current_stroke and len(current_stroke["points"]) > 1:
        strokes.append(current_stroke)
    current_stroke = None
    is_drawing = False


def handle_event(event):
    """Handle a single pygame event"""
    global running, show_help, draw_mode, is_drawing, click_start, current_stroke, strokes

    if event.type == pygame.QUIT:
        running = False

    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
            running = False
        elif event.key == pygame.K_h:
            show_help = not show_help
        elif event.key == pygame.K_s:
            save_roads()
        elif event.key == pygame.K_l:
            load_roads()
        elif event.key == pygame.K_u:
            undo_last_stroke()
        elif event.key == pygame.K_c:
            clear_all()
        elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
            change_width(5)
        elif event.key == pygame.K_MINUS:
            change_width(-5)
        elif event.key == pygame.K_t:
            draw_mode = "line"
            is_drawing = False
            click_start = None
            current_stroke = None
            set_message("Line mode: click start, click end", 120)
        elif event.key == pygame.K_a:
            draw_mode = "paint"
            is_drawing = False
            click_start = None
            current_stroke = None
            set_message("Paint mode: click and drag to paint", 120)

    elif event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            if draw_mode == "line":
                # Line mode: first click sets start, second click draws line
                if not is_drawing:
                    click_start = event.pos
                    is_drawing = True
                else:
                    # Second click: finish line
                    stroke = {
                        "points": [click_start, event.pos],
                        "width": brush_width
                    }
                    strokes.append(stroke)
                    is_drawing = False
                    click_start = None
            else:
                # Paint mode: start a new stroke
                start_stroke(event.pos)
        elif event.button == 4:  # Scroll up
            change_width(5)
        elif event.button == 5:  # Scroll down
            change_width(-5)

    elif event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            if draw_mode == "paint":
                # Paint mode: finish the stroke on mouse upy
                finish_stroke()

    elif event.type == pygame.MOUSEMOTION:
        if draw_mode == "paint" and is_drawing:
            # Paint mode: add points while dragging
            add_point(event.pos)

    elif event.type == pygame.MOUSEWHEEL:
        change_width(event.y * 5)


def draw_stroke(surface, stroke, alpha=ROAD_ALPHA):
    """Draw a single stroke on a surface"""
    points = stroke["points"]
    width = stroke["width"]

    if len(points) < 2:
        return

    # Draw circles at each point and lines between them
    for i, point in enumerate(points):
        pygame.draw.circle(surface, ROAD_COLOR, point, width // 2)
        if i > 0:
            pygame.draw.line(surface, ROAD_COLOR, points[i - 1], point, width)


def draw_roads(screen, img_w, img_h):
    """Draw all roads with transparency"""
    # Create a surface for roads with alpha
    road_surface = pygame.Surface((img_w, img_h), pygame.SRCALPHA)

    # Draw all completed strokes
    for stroke in strokes:
        draw_stroke(road_surface, stroke)

    # Draw preview line if start point is set
    if is_drawing and click_start is not None:
        mx, my = pygame.mouse.get_pos()
        preview_stroke = {
            "points": [click_start, (mx, my)],
            "width": brush_width
        }
        draw_stroke(road_surface, preview_stroke)

    # Draw current stroke being drawn
    if current_stroke and len(current_stroke["points"]) > 0:
        draw_stroke(road_surface, current_stroke)

    # Apply alpha and blit
    road_surface.set_alpha(ROAD_ALPHA)
    screen.blit(road_surface, (0, 0))


def draw_brush_preview(screen):
    """Draw brush preview at cursor"""
    mx, my = pygame.mouse.get_pos()
    # Draw outline circle
    pygame.draw.circle(screen, (255, 255, 255), (mx, my), brush_width // 2, 2)
    pygame.draw.circle(screen, (0, 0, 0), (mx, my), brush_width // 2, 1)


def draw_ui_panel(screen, font):
    """Draw the info panel"""
    global message_timer

    panel_rect = pygame.Rect(10, 10, 250, 125)
    panel_surf = pygame.Surface((panel_rect.width, panel_rect.height))
    panel_surf.fill((20, 25, 35))
    panel_surf.set_alpha(220)
    screen.blit(panel_surf, panel_rect.topleft)
    pygame.draw.rect(screen, (80, 90, 110), panel_rect, 2, border_radius=6)

    y = 18
    mode_name = "Line" if draw_mode == "line" else "Paint"
    mode_text = font.render(f"Mode: {mode_name} (T/A)", True, (255, 220, 100))
    screen.blit(mode_text, (20, y))

    y += 26
    width_text = font.render(f"Brush: {brush_width}px", True, (200, 200, 200))
    screen.blit(width_text, (20, y))

    y += 26
    count_text = font.render(f"Strokes: {len(strokes)}", True, (200, 200, 200))
    screen.blit(count_text, (20, y))

    y += 26
    if message_timer > 0:
        msg_surf = font.render(message, True, (180, 220, 180))
        screen.blit(msg_surf, (20, y))
        message_timer -= 1


def draw_help_overlay(screen, font, img_w, img_h):
    """Draw the help overlay"""
    help_lines = [
        "=== ROAD PAINTER ===",
        "",
        "T = Line mode (click start, click end)",
        "A = Paint mode (click and drag)",
        "Mouse Wheel / +/- = Change brush width",
        "U = Undo last stroke",
        "C = Clear all roads",
        "S = Save roads to JSON",
        "L = Load roads from JSON",
        "H = Toggle this help",
        "Q/Esc = Quit",
    ]
    help_h = len(help_lines) * 26 + 20
    help_rect = pygame.Rect(img_w // 2 - 180, img_h // 2 - help_h // 2, 360, help_h)
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
    hint = "T=Line  A=Paint  H=Help  S=Save  U=Undo  C=Clear  Wheel=Size  Q=Quit"
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
    pygame.display.set_caption("Road Painter - Press H for help")

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)
    clock = pygame.time.Clock()

    # Load existing roads
    if os.path.exists(OUTPUT_FILE):
        load_roads()

    set_message("Line mode: click start, click end (A=paint)", 180)

    while running:
        for event in pygame.event.get():
            handle_event(event)

        # Draw
        screen.blit(map_image, (0, 0))
        draw_roads(screen, img_w, img_h)
        draw_brush_preview(screen)
        draw_ui_panel(screen, font)

        if show_help:
            draw_help_overlay(screen, font, img_w, img_h)

        draw_hint(screen, small_font, img_w, img_h)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

    # Ask to save on exit
    if strokes:
        print(f"\nYou have {len(strokes)} strokes.")
        save = input("Save before exit? (y/n): ").strip().lower()
        if save == 'y':
            save_roads()
            print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
