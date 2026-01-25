# Plant Courier - Main Entry Point
import asyncio
import pygame
import sys

# Import from shared modules
from shared.input.input_manager import InputManager
from shared.debug.debug_log import debug
from shared.debug.debug_overlay import DebugOverlay

# Import screens
from screens.map import MapScreen
from screens.dialog.components import Button, DialogChoice
from screens.dialog.base_dialog import BaseDialog
from screens.dialog.ui_renderer import UIRenderer


async def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    clock = pygame.time.Clock()
    pygame.display.set_caption("Plant Courier")

    # Exit button (top right corner)
    exit_font = pygame.font.Font(None, 36)
    exit_rect = pygame.Rect(1870, 10, 40, 40)

    # Initialize shared systems
    input_mgr = InputManager()
    ui = UIRenderer(screen)
    debug_overlay = DebugOverlay(screen)

    # Log startup info
    debug.info(f"Game started - Platform: {'WASM' if debug.is_wasm else 'Native'}")
    debug.info(f"Python version: {sys.version.split()[0]}")
    debug.info(f"Pygame version: {pygame.version.ver}")
    debug.info(f"Screen size: {screen.get_size()}")

    # Create the first map screen
    current_map = MapScreen(screen, "world")
    current_map.initialize()
    current_map.load_map_image("assets/map1.png")
    current_map.load_locations("data/map1_locations.json")

    # Set player starting position at the shop (home)
    start_x, start_y = current_map.get_start_position()
    current_map.set_player_position(start_x, start_y)

    debug.info("Map screen initialized")

    # UI elements
    dialog_btn = Button(
        rect=pygame.Rect(1680, 30, 200, 70),
        text="Dialog",
        color=(100, 60, 120),
        hover_color=(140, 80, 160)
    )

    test_dialog = BaseDialog(
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
            current_map.move_player_toward(target[0], target[1])
            if current_map.is_player_at_target(target[0], target[1]):
                current_map.stop_player()
                target = None

        if message_timer > 0:
            message_timer -= dt

        # Update and render map
        current_map.update(dt)

        # Draw exit button (always visible)
        exit_hover = input_mgr.is_point_in_rect(input_mgr.touch_pos, exit_rect)
        exit_color = (80, 40, 40) if exit_hover else (50, 30, 30)
        pygame.draw.rect(screen, exit_color, exit_rect, border_radius=6)
        exit_text = exit_font.render("X", True, (180, 180, 180))
        exit_text_rect = exit_text.get_rect(center=exit_rect.center)
        screen.blit(exit_text, exit_text_rect)
        if input_mgr.clicked_in_rect(exit_rect):
            running = False

        # Draw UI (only if overlay not covering)
        if not debug.overlay_visible:
            if ui.draw_button(dialog_btn, input_mgr):
                test_dialog.toggle()
                debug.info(f"Dialog {'opened' if test_dialog.visible else 'closed'}")

            choice = ui.draw_dialog(test_dialog, input_mgr)
            if choice is not None:
                debug.info(f"Dialog choice selected: {choice + 1} - {test_dialog.choices[choice].text}")
                message = f"Selected: {test_dialog.choices[choice].text}"
                message_timer = 2.0
                test_dialog.hide()

            if last_click and not test_dialog.visible:
                ui.draw_click_indicator(last_click)

            ui.draw_coordinates(input_mgr)

            # Check for nearby location and display in bottom right
            nearby = current_map.get_nearby_location()
            if nearby:
                loc_name = nearby["name"]
                loc_type = nearby["type"]
                type_labels = {
                    "shop": "Plant Shop",
                    "office": "Office",
                    "restaurant": "Restaurant",
                    "house": "Home"
                }
                type_label = type_labels.get(loc_type, loc_type)

                # Draw location info box in bottom right
                info_text = f"{loc_name}"
                type_text = f"({type_label})"

                name_surf = ui.font.render(info_text, True, (255, 255, 255))
                type_surf = ui.small_font.render(type_text, True, (180, 180, 180))

                box_w = max(name_surf.get_width(), type_surf.get_width()) + 40
                box_h = 80
                screen_w, screen_h = screen.get_size()
                box_x = screen_w - box_w - 30
                box_y = screen_h - box_h - 30

                # Background box
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
                pygame.draw.rect(screen, (30, 40, 50), box_rect, border_radius=10)
                pygame.draw.rect(screen, (80, 120, 160), box_rect, 2, border_radius=10)

                # Text
                screen.blit(name_surf, (box_x + 20, box_y + 15))
                screen.blit(type_surf, (box_x + 20, box_y + 48))

            if message_timer > 0:
                msg_surf = ui.font.render(message, True, (255, 255, 100))
                screen.blit(msg_surf, (200, 30))

        # Log periodic stats
        if frame_count % 300 == 0:
            fps = clock.get_fps()
            debug.debug(f"FPS: {fps:.1f}")

        pygame.display.flip()
        await asyncio.sleep(0)

    debug.info("Game shutting down")
    pygame.quit()


if __name__ == '__main__':
    asyncio.run(main())
