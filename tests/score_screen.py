"""
Visual test for ScoreScreen (End Game).

Run with: uv run tests/score_screen.py

Shows the end game score screen with mock plant delivery data.
Features auto-scrolling plant grid with delivery counts.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from screens/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from screens.dialogs.score_screen import ScoreScreen
from shared.input_manager import InputManager


def create_mock_plant_counts():
    """Create mock plant delivery counts for testing."""
    # filename -> (name_fi, count)
    # Using actual plant filenames from assets/plants/one/
    plant_counts = {
        "köynnösvehka-01.png": ("Köynnösvehka", 12),
        "kultaköynnös-01.png": ("Kultaköynnös", 8),
        "peikonlehti-08.png": ("Peikonlehti", 15),
        "kalathea-01.png": ("Kalathea", 6),
        "rahapuu-01.png": ("Rahapuu", 9),
        "viirivehka-03.png": ("Viirivehka", 11),
        "palmuvehka-04.png": ("Palmuvehka", 4),
        "arekapalmu-02.png": ("Arekapalmu", 7),
        "kumiviikuna-01.png": ("Kumiviikuna", 3),
        "tulilatva-03.png": ("Tulilatva", 5),
        "muorinkukka-01.png": ("Muorinkukka", 2),
        "viulunlehtiviikuna-01.png": ("Viulunlehtiviikuna", 8),
    }
    return plant_counts


def main():
    # Initialize pygame
    pygame.init()

    # Screen dimensions (same as game)
    screen_width = 1920
    screen_height = 1080

    # Create window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("ScoreScreen (End Game) Visual Test")
    clock = pygame.time.Clock()

    # Create input manager
    input_mgr = InputManager()

    # Create screen
    score_screen = ScoreScreen(screen)

    # Create mock data
    plant_counts = create_mock_plant_counts()

    # Calculate totals
    total_plants = sum(count for _, count in plant_counts.values())
    total_orders = 8  # Mock number of orders
    total_score = total_plants * 10 + total_orders * 20  # Mock scoring

    # Open screen with mock data
    score_screen.open(
        total_orders=total_orders,
        total_plants=total_plants,
        total_score=total_score,
        plant_counts=plant_counts
    )

    # Main loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    # Reset - reopen screen
                    score_screen.open(
                        total_orders=total_orders,
                        total_plants=total_plants,
                        total_score=total_score,
                        plant_counts=plant_counts
                    )

        input_mgr.process_events(events)

        # Update screen
        score_screen.update(dt)

        # Clear screen with dark background
        screen.fill((20, 30, 40))

        # Draw screen
        score_screen.draw(input_mgr)

        # Handle input
        action = score_screen.handle_input(input_mgr)
        if action == "score_closed":
            print("Screen closed! Press R to reopen or ESC to quit.")

        # Draw help text
        font = pygame.font.Font(None, 36)
        help_text = font.render("Press R to reset, ESC to quit", True, (150, 150, 150))
        screen.blit(help_text, (20, screen_height - 50))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
