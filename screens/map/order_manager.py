# Order system - manages order lifecycle on the map screen

from shared.audio_manager import AudioManager
import esper
import random
from typing import List, Dict
from shared.shared_components import Order, OrderState, PlantOrder
from shared.debug_log import debug
from screens.map.order_text_roller import OrderTextRoller


class OrderManager:
    """
    Manages all order state for a map.

    This is a plain Python class, not an ECS component.
    Orders don't need ECS - they have a fixed structure.
    """

    def __init__(self, audio: AudioManager):
        self.audio = audio
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
        self.active_order_limit: int = 6

        # Progress tracking
        self.orders_completed_count: int = 0
        self.plants_delivered_count: int = 0
        self.total_score: int = 0

        # Completion requirements (set from map config)
        self.orders_required: int = 10
        self.plants_required: int = 0
        self.score_required: int = 0

        # Scoring config (set from map config)
        self.points_per_plant: int = 10
        self.full_order_bonus: int = 20

        # Flag for map completion
        self.map_completed: bool = False

        # Text roller for generating order text
        self.text_roller = OrderTextRoller()

    def load_orders(self, orders_data: Dict[str, List[dict]], locations_data: List[dict] = None):
        """
        Load orders from JSON data.

        Expected format:
        {
            "LocationName": [
                {
                    "order_id": "loc1_order1",
                    "send_time": 5.0,
                    "plants": [
                        {"plant_filename": "plant.png", "plant_name_fi": "Kasvi", "plant_name_en": "Plant", "amount": 2}
                    ]
                }
            ]
        }

        Args:
            orders_data: Orders keyed by location name
            locations_data: List of location dicts with name and email fields
        """
        self.all_orders = {}
        self.available_orders = []

        # Build location name -> email lookup
        email_lookup = {}
        if locations_data is not None:
            for loc in locations_data:
                loc_name = loc.get("name", "")
                loc_email = loc.get("email", "")
                if loc_name:
                    email_lookup[loc_name] = loc_email

        total_orders = 0
        for location_name, order_list in orders_data.items():
            self.all_orders[location_name] = []

            # Look up email for this location
            customer_email = email_lookup.get(location_name, "")

            for order_data in order_list:
                plants = []
                for plant_data in order_data.get("plants", []):
                    # Support both old and new key formats
                    plant = PlantOrder(
                        filename=plant_data.get("plant_filename", plant_data.get("filename", "")),
                        name_fi=plant_data.get("plant_name_fi", plant_data.get("name_fi", "")),
                        name_en=plant_data.get("plant_name_en", plant_data.get("name_en", "")),
                        amount=plant_data.get("amount", 1)
                    )
                    plants.append(plant)

                order = Order(
                    order_id=order_data.get("order_id", ""),
                    customer_location=location_name,
                    customer_email=customer_email,
                    plants=plants,
                    state=OrderState.AVAILABLE,
                    send_time=order_data.get("send_time", 0.0),
                    countdown_to_visible=-1.0,
                    countdown_to_available=-1.0,
                    generated_text=""
                )

                self.all_orders[location_name].append(order)
                self.available_orders.append(order)
                total_orders += 1

        debug.info(f"Orders loaded: {total_orders} orders from {len(self.all_orders)} locations")
        debug.info(f"Orders in available pool: {len(self.available_orders)}")

        # Generate random text for all plants in orders
        self.text_roller.roll_for_orders(self.available_orders)

    def set_config(self, batch_size: int, batch_delay: float, accept_time: float,
                   orders_required: int = 0, plants_required: int = 0,
                   active_order_limit: int = 6, score_required: int = 0,
                   points_per_plant: int = 10, full_order_bonus: int = 20):
        """Set timing, completion, and scoring config from map settings."""
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.accept_time = accept_time
        self.orders_required = orders_required
        self.plants_required = plants_required
        self.active_order_limit = active_order_limit
        self.score_required = score_required
        self.points_per_plant = points_per_plant
        self.full_order_bonus = full_order_bonus

    def select_next_batch(self):
        """Select next batch of orders from available pool, avoiding same location."""
        if not self.available_orders:
            debug.debug("No available orders for next batch")
            return

        # Don't select new batch if player has too many active orders
        if len(self.accepted_orders) >= self.active_order_limit:
            debug.debug(f"Active order limit reached ({len(self.accepted_orders)}/{self.active_order_limit})")
            self.countdown_to_incoming = 1.0  # Check again soon
            return

        batch_count = min(self.batch_size, len(self.available_orders))
        debug.info(f"Selecting batch of {batch_count} orders (available: {len(self.available_orders)})")

        selected_locations = set()
        selected_orders = []

        # First pass: pick orders from unique locations
        for order in self.available_orders[:]:
            if len(selected_orders) >= batch_count:
                break
            if order.customer_location not in selected_locations:
                selected_locations.add(order.customer_location)
                selected_orders.append(order)

        # Second pass: if we still need more, allow duplicates
        if len(selected_orders) < batch_count:
            for order in self.available_orders[:]:
                if len(selected_orders) >= batch_count:
                    break
                if order not in selected_orders:
                    selected_orders.append(order)

        # Move selected orders to incoming
        for order in selected_orders:
            self.available_orders.remove(order)
            order.state = OrderState.INCOMING

            # Roll random delay based on send_time (between send_time/2 and send_time)
            min_delay = order.send_time / 2.0
            max_delay = order.send_time
            order.rolled_send_time = random.uniform(min_delay, max_delay)
            order.countdown_to_visible = order.rolled_send_time

            self.incoming_orders.append(order)
            debug.info(f"  -> INCOMING: {order.order_id} ({order.customer_location}) countdown={order.rolled_send_time:.1f}s (rolled from {order.send_time}s)")

        self.countdown_to_incoming = self.batch_delay

    def move_to_visible(self, order: Order):
        """Move order from incoming to visible state."""
        if order in self.incoming_orders:
            self.incoming_orders.remove(order)

        order.state = OrderState.VISIBLE
        order.countdown_to_visible = -1.0
        order.countdown_to_available = self.accept_time
        self.visible_orders.append(order)
        debug.info(f"Order VISIBLE: {order.order_id} ({order.customer_location}) - accept within {self.accept_time}s")

    def move_to_available(self, order: Order):
        """Move expired order back to available pool."""
        if order in self.visible_orders:
            self.visible_orders.remove(order)

        order.state = OrderState.AVAILABLE
        order.countdown_to_visible = -1.0
        order.countdown_to_available = -1.0
        self.available_orders.append(order)
        debug.info(f"Order EXPIRED: {order.order_id} returned to available pool")

    def accept_order(self, order: Order):
        """Player accepts an order."""
        if order in self.visible_orders:
            self.visible_orders.remove(order)

        order.state = OrderState.ACCEPTED
        order.countdown_to_visible = -1.0
        order.countdown_to_available = -1.0
        self.accepted_orders.append(order)
        debug.info(f"Order ACCEPTED: {order.order_id} ({order.customer_location})")

    def complete_order(self, order: Order, plants_delivered: int, is_full_delivery: bool):
        """
        Mark order as completed after delivery.

        Args:
            order: The order being completed
            plants_delivered: Number of plants actually delivered
            is_full_delivery: Whether all requested plants were delivered
        """
        if order in self.accepted_orders:
            self.accepted_orders.remove(order)

        order.state = OrderState.COMPLETED
        self.completed_orders.append(order)

        self.orders_completed_count += 1
        self.plants_delivered_count += plants_delivered

        # Calculate score: points per plant + bonus for full delivery
        earned_points = plants_delivered * self.points_per_plant
        if is_full_delivery:
            earned_points = earned_points + self.full_order_bonus

        self.total_score = self.total_score + earned_points
        debug.info(f"Order completed: {plants_delivered} plants, full={is_full_delivery}, +{earned_points} points (total: {self.total_score})")

    def check_completion(self) -> bool:
        """Check if map completion requirements are met."""
        if self.map_completed:
            return True

        orders_met = False
        plants_met = False
        score_met = False

        if self.orders_required > 0:
            orders_met = self.orders_completed_count >= self.orders_required

        if self.plants_required > 0:
            plants_met = self.plants_delivered_count >= self.plants_required

        if self.score_required > 0:
            score_met = self.total_score >= self.score_required

        # Meet ANY requirement (OR logic)
        if self.orders_required > 0 and orders_met:
            self.map_completed = True
        elif self.plants_required > 0 and plants_met:
            self.map_completed = True
        elif self.score_required > 0 and score_met:
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
        self.status_log_timer = 0.0
        self.status_log_interval = 5.0  # Log status every 5 seconds

    def process(self, dt: float):
        # Periodic status logging
        self.status_log_timer += dt
        if self.status_log_timer >= self.status_log_interval:
            self.status_log_timer = 0.0
            m = self.order_manager
            debug.debug(f"Orders: avail={len(m.available_orders)} incoming={len(m.incoming_orders)} visible={len(m.visible_orders)} accepted={len(m.accepted_orders)}")
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

        if len(orders_to_make_visible) > 0:
            # play alert sound for new visible orders
            manager.audio.play("ordervisiblealert")

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
