# Plant Courier - Main Entry Point
import asyncio
import pygame
import sys

from screens.dialogs.start_dialog import StartDialog
from screens.map import MapScreen
from screens.map.map_ui import MapUI
from screens.map.order_manager import OrderManager
from shared.debug_overlay import DebugOverlay
from shared.debug_log import debug
from shared.input_manager import InputManager
from shared.audio_manager import AudioManager

# Add this for browser JS interop (Pyodide/pygbag)
try:
    import js
except ImportError:
    js = None

# Fullscreen toggle utilities
from shared.fullscreen import toggle_fullscreen_browser, toggle_fullscreen_desktop


async def main():
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Plant Courier")

    # Initialize audio
    audio = AudioManager()
    audio.initialize()
    audio.load_sounds()
    debug.info(f"Audio: {audio.get_status()}")

    # Exit button (top right corner)
    exit_font = pygame.font.Font(None, 36)
    exit_rect = pygame.Rect(1870, 10, 40, 40)

    # Fullscreen button (bottom right corner, 1.5x size)
    fullscreen_size = int(40 * 1.5)  # 60
    fullscreen_rect = pygame.Rect(
        1920 - fullscreen_size - 10, 1080 - fullscreen_size - 10, fullscreen_size, fullscreen_size)
    fullscreen_icon_color = (40, 80, 120)

    # Initialize shared systems
    input_mgr = InputManager()
    debug_overlay = DebugOverlay(screen)

    # Log startup info
    debug.info(
        f"Game started - Platform: {'WASM' if debug.is_wasm else 'Native'}")
    debug.info(f"Python version: {sys.version.split()[0]}")
    debug.info(f"Pygame version: {pygame.version.ver}")
    debug.info(f"Screen size: {screen.get_size()}")

    # Game state: "start" or "map"
    game_state = "start"
    start_dialog = StartDialog(screen)
    current_map = None
    map_ui = None
    map_overlay_action = None

    # Game state
    running = True
    target = None
    frame_count = 0

    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        input_mgr.process_events(events)

        # Handle start screen
        if game_state == "start":
            action = start_dialog.handle_event(input_mgr)
            if action == "map":
                # Play start sound
                audio.play("alkaa-nyt")
                # Initialize map screen
                current_map = MapScreen(screen, "world")
                current_map.initialize()
                current_map.load_config("data/map1_config.json")
                current_map.load_map_image("assets/map1.png")
                current_map.load_roads("data/map1_roads.json")
                current_map.load_locations("data/map1_locations.json")
                current_map.load_orders("data/map1_orders.json")
                current_map.initialize_greenery()
                current_map.initialize_start_position()
                map_ui = MapUI(screen, current_map.order_manager)
                map_ui.on_greenery_add = current_map.add_greenery_at_delivery
                game_state = "map"
                debug.info("Map screen initialized")
            elif action == "exit":
                running = False
            elif action == "fullscreen":
                if debug.is_wasm and js is not None:
                    toggle_fullscreen_browser()
                else:
                    toggle_fullscreen_desktop()
                debug.info("Fullscreen toggled")

            start_dialog.draw(input_mgr)
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        # Map screen logic below
        # If overlay is open, handle its input
        if debug.overlay_visible:
            if debug_overlay.draw_overlay(input_mgr):
                debug.overlay_visible = False
        elif map_overlay_action is None and not map_ui.greenhouse.visible:
            # Normal game input (only when overlay closed and greenhouse not open)
            if input_mgr.clicked_this_frame:
                mouse_x, mouse_y = input_mgr.click_pos
                # Convert screen to world coordinates using camera position and zoom
                world_x = (mouse_x - screen.get_width() // 2) / \
                    current_map.zoom + current_map.camera_pos_x
                world_y = (mouse_y - screen.get_height() // 2) / \
                    current_map.zoom + current_map.camera_pos_y

                target = (world_x, world_y)
                debug.debug(
                    f"Map click at {input_mgr.click_pos}, target set to ({world_x:.2f}, {world_y:.2f})")

        # Move player toward target
        if target:
            current_map.move_player_toward(target[0], target[1])
            if current_map.is_player_at_target(target[0], target[1]):
                current_map.stop_player()
                target = None

        # Update and render map
        if not debug.overlay_visible:
            current_map.update(dt)

        # Draw exit button (always visible)
        if not debug.is_wasm:  # Only show exit button in desktop/native
            exit_hover = input_mgr.is_point_in_rect(
                input_mgr.touch_pos, exit_rect)
            exit_color = (80, 40, 40) if exit_hover else (50, 30, 30)
            pygame.draw.rect(screen, exit_color, exit_rect, border_radius=6)
            exit_text = exit_font.render("X", True, (180, 180, 180))
            exit_text_rect = exit_text.get_rect(center=exit_rect.center)
            screen.blit(exit_text, exit_text_rect)
            if input_mgr.clicked_in_rect(exit_rect):
                running = False

        # Draw UI (only if overlay not covering)
        if not debug.overlay_visible:
            # Draw map-specific UI (location indicator, etc.)
            map_action = map_ui.draw(current_map, input_mgr, dt)
            if map_action == "open_incoming_orders":
                debug.info("Incoming orders phone clicked")
                map_overlay_action = "open_incoming_orders"
            elif map_action == "open_main_phone":
                debug.info("Main phone clicked")
                map_overlay_action = "open_main_phone"
            elif map_action == "phone_closed":
                debug.info("Phone closed")
                map_overlay_action = None

        # Draw debug icon last so it's always on top
        if debug_overlay.draw_icon(input_mgr):
            debug.overlay_visible = not debug.overlay_visible
            debug.info(
                f"Debug overlay {'opened' if debug.overlay_visible else 'closed'}")

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
