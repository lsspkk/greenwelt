"""
Visual test for GreenerySystem.

Run with: uv run tests/greenery_system.py

Shows how greenery looks when three orders are delivered.
Draws on a white background at full screen resolution (1920x1080).
"""

import sys
from pathlib import Path

# Add project root to path so we can import from screens/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from screens.map.greenery_system import GreenerySystem


def main():
    # Initialize pygame
    pygame.init()

    # Screen dimensions (same as game)
    screen_width = 1920
    screen_height = 1080

    # Create window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("GreenerySystem Visual Test")

    # Fill with white
    screen.fill((255, 255, 255))

    # Create and initialize greenery system
    greenery = GreenerySystem()
    greenery.initialize(screen_width, screen_height)

    # Add greenery at three locations (simulating three deliveries)
    # Place them in different areas so we can see all three
    location_1_x = screen_width // 4
    location_1_y = screen_height // 2

    location_2_x = screen_width // 2
    location_2_y = screen_height // 2

    location_3_x = (screen_width * 3) // 4
    location_3_y = screen_height // 2

    greenery.add_greenery_at_location(location_1_x, location_1_y)
    greenery.add_greenery_at_location(location_2_x, location_2_y)
    greenery.add_greenery_at_location(location_3_x, location_3_y)

    # Render greenery onto the screen
    # Camera at 0,0 with zoom 1.0 (no transformation)
    greenery.render(screen, camera_x=0, camera_y=0, zoom=1.0)

    # Update display
    pygame.display.flip()

    # Wait for user to close window
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

    pygame.quit()


if __name__ == "__main__":
    main()
