"""
Game Score Tracker - Tracks scores across all maps and orders.

Stores detailed information about:
- Each map's completed orders
- Plants delivered per order
- Score earned per order
- Per-map and total game statistics
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class OrderScore:
    """Score data for a single completed order."""
    order_id: str
    customer_location: str
    plants_delivered: int
    plants_requested: int
    is_full_delivery: bool
    score_earned: int
    # Plant details: list of (filename, name_fi, amount_delivered)
    plant_details: List[Tuple[str, str, int]] = field(default_factory=list)


@dataclass
class MapScore:
    """Score data for a completed map."""
    map_number: int
    map_name: str
    orders_completed: int
    plants_delivered: int
    total_score: int
    # List of all order scores for this map
    order_scores: List[OrderScore] = field(default_factory=list)


class GameScore:
    """
    Global game score tracker.

    Tracks all scores across multiple maps with detailed per-order breakdown.
    """

    def __init__(self):
        # List of completed map scores
        self.map_scores: List[MapScore] = []

        # Aggregate plant counts across all maps: filename -> (name_fi, total_count)
        self.plant_totals: Dict[str, Tuple[str, int]] = {}

    def reset(self):
        """Reset all scores for a new game."""
        self.map_scores = []
        self.plant_totals = {}

    def add_map_score(self, map_score: MapScore):
        """Add a completed map's score data."""
        self.map_scores.append(map_score)

        # Update plant totals
        for order_score in map_score.order_scores:
            for filename, name_fi, amount in order_score.plant_details:
                if filename in self.plant_totals:
                    old_name, old_count = self.plant_totals[filename]
                    self.plant_totals[filename] = (old_name, old_count + amount)
                else:
                    self.plant_totals[filename] = (name_fi, amount)

    def add_completed_map(self, map_number: int, order_manager) -> MapScore:
        """
        Record a completed map's scores from its OrderManager.

        Reads all necessary data from order_manager internally.

        Args:
            map_number: The map number (1, 2, etc.)
            order_manager: The OrderManager with completed orders

        Returns:
            The created MapScore
        """
        # Read scoring config from order_manager
        points_per_plant = order_manager.points_per_plant
        full_order_bonus = order_manager.full_order_bonus

        order_scores = []

        for order in order_manager.completed_orders:
            # Calculate plants delivered and requested
            plants_requested = sum(p.amount for p in order.plants)

            # For now, assume full delivery based on order state
            # TODO: Track actual delivered amounts during delivery
            plants_delivered = plants_requested
            is_full = True

            # Calculate score for this order
            score = plants_delivered * points_per_plant
            if is_full:
                score += full_order_bonus

            # Build plant details
            plant_details = []
            for plant in order.plants:
                plant_details.append((plant.filename, plant.name_fi, plant.amount))

            order_score = OrderScore(
                order_id=order.order_id,
                customer_location=order.customer_location,
                plants_delivered=plants_delivered,
                plants_requested=plants_requested,
                is_full_delivery=is_full,
                score_earned=score,
                plant_details=plant_details
            )
            order_scores.append(order_score)

        map_score = MapScore(
            map_number=map_number,
            map_name=f"Map {map_number}",
            orders_completed=len(order_scores),
            plants_delivered=sum(o.plants_delivered for o in order_scores),
            total_score=sum(o.score_earned for o in order_scores),
            order_scores=order_scores
        )

        # Add to our list and update totals
        self.add_map_score(map_score)

        return map_score

    def get_total_orders(self) -> int:
        """Get total orders completed across all maps."""
        return sum(m.orders_completed for m in self.map_scores)

    def get_total_plants(self) -> int:
        """Get total plants delivered across all maps."""
        return sum(m.plants_delivered for m in self.map_scores)

    def get_total_score(self) -> int:
        """Get total score across all maps."""
        return sum(m.total_score for m in self.map_scores)

    def get_maps_completed(self) -> int:
        """Get number of maps completed."""
        return len(self.map_scores)

    def get_plant_counts(self) -> Dict[str, Tuple[str, int]]:
        """Get aggregate plant delivery counts for end game display."""
        return self.plant_totals.copy()

    def get_map_summary(self, map_number: int) -> str:
        """Get a text summary for a specific map."""
        for map_score in self.map_scores:
            if map_score.map_number == map_number:
                lines = [
                    f"Map {map_number}: {map_score.map_name}",
                    f"  Orders: {map_score.orders_completed}",
                    f"  Plants: {map_score.plants_delivered}",
                    f"  Score: {map_score.total_score}",
                    "  Orders:"
                ]
                for order in map_score.order_scores:
                    full_text = "FULL" if order.is_full_delivery else "PARTIAL"
                    lines.append(f"    {order.customer_location}: {order.plants_delivered} plants, +{order.score_earned} ({full_text})")
                return "\n".join(lines)
        return f"Map {map_number} not found"


# Global game score instance
game_score = GameScore()
