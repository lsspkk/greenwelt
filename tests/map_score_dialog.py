"""
Visual test for MapScoreDialog.

Run with: uv run tests/map_score_dialog.py

Shows the map completion dialog with mock order data.
Features animated plant balls that bounce like billiard balls.
"""

import sys
from pathlib import Path

# Add project root to path so we can import from screens/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pygame
from screens.dialogs.map_score_dialog import MapScoreDialog
from shared.input_manager import InputManager
from shared.shared_components import Order, PlantOrder, OrderState


def create_mock_orders():
    """Create mock completed orders for testing."""
    orders = []

    # Order 1: Multiple plants
    order1 = Order(
        order_id="test-order-1",
        customer_location="Ravintola Vihreä",
        customer_email="vihrea@example.com",
        state=OrderState.COMPLETED
    )
    order1.plants = [
        PlantOrder(
            filename="köynnösvehka-01.png",
            name_fi="Köynnösvehka",
            name_en="Pothos",
            amount=3
        ),
        PlantOrder(
            filename="kultaköynnös-01.png",
            name_fi="Kultaköynnös",
            name_en="Golden Pothos",
            amount=2
        )
    ]
    orders.append(order1)

    # Order 2: Single plant type
    order2 = Order(
        order_id="test-order-2",
        customer_location="Toimisto Oy",
        customer_email="toimisto@example.com",
        state=OrderState.COMPLETED
    )
    order2.plants = [
        PlantOrder(
            filename="peikonlehti-08.png",
            name_fi="Peikonlehti",
            name_en="Monstera",
            amount=2
        )
    ]
    orders.append(order2)

    # Order 3: Mix of plants
    order3 = Order(
        order_id="test-order-3",
        customer_location="Kahvila Kukka",
        customer_email="kukka@example.com",
        state=OrderState.COMPLETED
    )
    order3.plants = [
        PlantOrder(
            filename="kalathea-01.png",
            name_fi="Kalathea",
            name_en="Calathea",
            amount=1
        ),
        PlantOrder(
            filename="rahapuu-01.png",
            name_fi="Rahapuu",
            name_en="Money Tree",
            amount=2
        )
    ]
    orders.append(order3)

    # Order 4
    order4 = Order(
        order_id="test-order-4",
        customer_location="Hotelli Palmu",
        customer_email="palmu@example.com",
        state=OrderState.COMPLETED
    )
    order4.plants = [
        PlantOrder(
            filename="viirivehka-03.png",
            name_fi="Viirivehka",
            name_en="Peace Lily",
            amount=4
        )
    ]
    orders.append(order4)

    return orders


def main():
    # Initialize pygame
    pygame.init()

    # Screen dimensions (same as game)
    screen_width = 1920
    screen_height = 1080

    # Create window
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("MapScoreDialog Visual Test")
    clock = pygame.time.Clock()

    # Create input manager
    input_mgr = InputManager()

    # Create dialog
    dialog = MapScoreDialog(screen)

    # Create mock data
    mock_orders = create_mock_orders()

    # Calculate totals
    total_orders = len(mock_orders)
    total_plants = 0
    for order in mock_orders:
        for plant in order.plants:
            total_plants += plant.amount

    total_score = total_plants * 10 + total_orders * 20  # Mock scoring

    # Open dialog with mock data
    dialog.open(
        orders_completed=total_orders,
        plants_delivered=total_plants,
        total_score=total_score,
        completed_orders=mock_orders,
        map_name="Test Map"
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
                    # Reset - reopen dialog
                    dialog.open(
                        orders_completed=total_orders,
                        plants_delivered=total_plants,
                        total_score=total_score,
                        completed_orders=mock_orders,
                        map_name="Test Map"
                    )

        input_mgr.process_events(events)

        # Update dialog
        dialog.update(dt)

        # Clear screen with dark background
        screen.fill((20, 30, 40))

        # Draw dialog
        dialog.draw(input_mgr)

        # Handle input
        action = dialog.handle_input(input_mgr)
        if action == "map_score_closed":
            print("Dialog closed! Press R to reopen or ESC to quit.")

        # Draw help text
        font = pygame.font.Font(None, 36)
        help_text = font.render("Press R to reset, ESC to quit", True, (150, 150, 150))
        screen.blit(help_text, (20, screen_height - 50))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
