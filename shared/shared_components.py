# Shared ECS components used across multiple screens
from dataclasses import dataclass, field
from enum import Enum
from typing import List


@dataclass
class Position:
    """World position of an entity"""
    x: float
    y: float


@dataclass
class Velocity:
    """Movement velocity of an entity"""
    vx: float
    vy: float


@dataclass
class DotRenderable:
    """Renders entity as a circle/dot"""
    radius: int = 18
    color: tuple = (200, 240, 200)


@dataclass
class RectangleRenderable:
    """Renders entity as a rectangle"""
    width: int = 120
    height: int = 80
    color: tuple = (60, 180, 90)


@dataclass
class SpriteRenderable:
    """Renders entity using a sprite image"""
    image_path: str = ""
    image: object = None  # pygame.Surface, loaded at runtime
    width: int = 80
    height: int = 80


# =============================================================================
# Order System Types
# =============================================================================

class OrderState(Enum):
    """
    Order lifecycle states.

    Flow: AVAILABLE -> INCOMING -> VISIBLE -> ACCEPTED -> COMPLETED

    VISIBLE can also go back to AVAILABLE if accept timer expires.
    """
    AVAILABLE = "available"    # Can be selected for incoming batch
    INCOMING = "incoming"      # In current batch, waiting for send_time
    VISIBLE = "visible"        # Notification shown, accept timer counting down
    ACCEPTED = "accepted"      # Player accepted the order
    COMPLETED = "completed"    # Order was delivered successfully


@dataclass
class PlantOrder:
    """A single plant request within an order"""
    filename: str          # Image filename (e.g., "köynnösvehka-01.png")
    name_fi: str           # Finnish name (e.g., "Köynnösvehka")
    name_en: str           # English name (e.g., "Pothos")
    amount: int            # How many plants requested


@dataclass
class Order:
    """
    A customer order containing one or more plant requests.

    Managed by order_system.
    """
    order_id: str                              # Unique identifier
    customer_location: str                     # Location name from map
    customer_email: str                        # Email address for display
    plants: List[PlantOrder] = field(default_factory=list)
    state: OrderState = OrderState.AVAILABLE
    # Delay before becoming visible (from JSON, does not change)
    send_time: float = 0.0
    # Countdown to change state from INCOMING to VISIBLE (-1 if not INCOMING)
    countdown_to_visible: float = -1.0
    # Countdown to change state from VISIBLE to AVAILABLE (-1 if not VISIBLE)
    countdown_to_available: float = -1.0
    generated_text: str = ""                   # Cached email text
