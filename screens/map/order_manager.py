# Order system - manages order lifecycle on the map screen

import esper
from typing import List, Dict
from shared.shared_components import Order, OrderState, PlantOrder


class OrderManager:
    """
    Manages all order state for a map.

    This is a plain Python class, not an ECS component.
    Orders don't need ECS - they have a fixed structure.
    """

    def __init__(self):
        # All orders loaded from JSON, keyed by location name
        self.all_orders: Dict[str, List[Order]] = {}

        # Orders in different states
        self.available_orders: List[Order] = []
        self.incoming_orders: List[Order] = []
        self.visible_orders: List[Order] = []
        self.accepted_orders: List[Order] = []
        self.completed_orders: List[Order] = []

        # Time until next orders are selected to INCOMING state
        self.countdown_to_incoming: float = 0.0

        # Config values (set from map config)
        self.batch_size: int = 3
        self.batch_delay: float = 10.0
        self.accept_time: float = 15.0

        # Progress tracking
        self.orders_completed_count: int = 0
        self.plants_delivered_count: int = 0

        # Completion requirements (set from map config)
        self.orders_required: int = 10
        self.plants_required: int = 0

        # Flag for map completion
        self.map_completed: bool = False

    def load_orders(self, orders_data: Dict[str, List[dict]]):
        """
        Load orders from JSON data.

        Expected format:
        {
            "LocationName": [
                {
                    "order_id": "loc1_order1",
                    "send_time": 5.0,
                    "plants": [
                        {"filename": "plant.png", "name_fi": "Kasvi", "name_en": "Plant", "amount": 2}
                    ]
                }
            ]
        }
        """
        self.all_orders = {}
        self.available_orders = []

        for location_name, order_list in orders_data.items():
            self.all_orders[location_name] = []

            for order_data in order_list:
                plants = []
                for plant_data in order_data.get("plants", []):
                    plant = PlantOrder(
                        filename=plant_data.get("filename", ""),
                        name_fi=plant_data.get("name_fi", ""),
                        name_en=plant_data.get("name_en", ""),
                        amount=plant_data.get("amount", 1)
                    )
                    plants.append(plant)

                order = Order(
                    order_id=order_data.get("order_id", ""),
                    customer_location=location_name,
                    customer_email=order_data.get("customer_email", ""),
                    plants=plants,
                    state=OrderState.AVAILABLE,
                    send_time=order_data.get("send_time", 0.0),
                    countdown_to_visible=-1.0,
                    countdown_to_available=-1.0,
                    generated_text=""
                )

                self.all_orders[location_name].append(order)
                self.available_orders.append(order)

    def set_config(self, batch_size: int, batch_delay: float, accept_time: float,
                   orders_required: int = 0, plants_required: int = 0):
        """Set timing and completion config from map settings."""
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.accept_time = accept_time
        self.orders_required = orders_required
        self.plants_required = plants_required

    def select_next_batch(self):
        """Select next batch of orders from available pool."""
        if not self.available_orders:
            return

        batch_count = min(self.batch_size, len(self.available_orders))

        for _ in range(batch_count):
            order = self.available_orders.pop(0)
            order.state = OrderState.INCOMING
            # Set countdown from the order's send_time
            order.countdown_to_visible = order.send_time
            self.incoming_orders.append(order)

        self.countdown_to_incoming = self.batch_delay

    def move_to_visible(self, order: Order):
        """Move order from incoming to visible state."""
        if order in self.incoming_orders:
            self.incoming_orders.remove(order)

        order.state = OrderState.VISIBLE
        order.countdown_to_visible = -1.0
        order.countdown_to_available = self.accept_time
        self.visible_orders.append(order)

    def move_to_available(self, order: Order):
        """Move expired order back to available pool."""
        if order in self.visible_orders:
            self.visible_orders.remove(order)

        order.state = OrderState.AVAILABLE
        order.countdown_to_visible = -1.0
        order.countdown_to_available = -1.0
        self.available_orders.append(order)

    def accept_order(self, order: Order):
        """Player accepts an order."""
        if order in self.visible_orders:
            self.visible_orders.remove(order)

        order.state = OrderState.ACCEPTED
        order.countdown_to_visible = -1.0
        order.countdown_to_available = -1.0
        self.accepted_orders.append(order)

    def complete_order(self, order: Order, plants_count: int):
        """Mark order as completed after delivery."""
        if order in self.accepted_orders:
            self.accepted_orders.remove(order)

        order.state = OrderState.COMPLETED
        self.completed_orders.append(order)

        self.orders_completed_count += 1
        self.plants_delivered_count += plants_count

    def check_completion(self) -> bool:
        """Check if map completion requirements are met."""
        if self.map_completed:
            return True

        orders_met = False
        plants_met = False

        if self.orders_required > 0:
            orders_met = self.orders_completed_count >= self.orders_required

        if self.plants_required > 0:
            plants_met = self.plants_delivered_count >= self.plants_required

        # Meet ANY requirement (OR logic)
        if self.orders_required > 0 and orders_met:
            self.map_completed = True
        elif self.plants_required > 0 and plants_met:
            self.map_completed = True

        return self.map_completed

    def get_visible_count(self) -> int:
        """Get count of visible incoming orders (for notification badge)."""
        return len(self.visible_orders)

    def get_accepted_count(self) -> int:
        """Get count of accepted orders."""
        return len(self.accepted_orders)


class OrderSystem(esper.Processor):
    """
    ECS System that updates order timers and state transitions.

    Handles:
    - countdown_to_incoming countdown and batch selection
    - countdown_to_visible countdown for incoming orders
    - countdown_to_available countdown for visible orders
    - State transitions based on timers
    - Map completion checking
    """

    def __init__(self, order_manager: OrderManager):
        self.order_manager = order_manager

    def process(self, dt: float):
        manager = self.order_manager

        # If no incoming or visible orders, count down to next batch
        if not manager.incoming_orders and not manager.visible_orders:
            manager.countdown_to_incoming -= dt
            if manager.countdown_to_incoming <= 0:
                manager.select_next_batch()

        # Update incoming orders - countdown_to_visible
        orders_to_make_visible = []
        for order in manager.incoming_orders:
            order.countdown_to_visible -= dt
            if order.countdown_to_visible <= 0:
                orders_to_make_visible.append(order)

        for order in orders_to_make_visible:
            manager.move_to_visible(order)

        # Update visible orders - countdown_to_available
        orders_to_expire = []
        for order in manager.visible_orders:
            order.countdown_to_available -= dt
            if order.countdown_to_available <= 0:
                orders_to_expire.append(order)

        for order in orders_to_expire:
            manager.move_to_available(order)

        # Check map completion
        manager.check_completion()
