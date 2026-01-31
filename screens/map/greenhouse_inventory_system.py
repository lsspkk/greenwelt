"""
Greenhouse Inventory System - Manages plant inventory and growth in the greenhouse.

This system controls:
- The greenhouse's plant inventory (separate from player's carried inventory)
- Plant growth over time (timer-based with random intervals)
- Which plants are available for the player to pick up

The inventory is a dict mapping plant filenames to their current count.
Plants grow automatically over time, up to a maximum per plant type.
"""

import random
from pathlib import Path
from typing import Dict, List, Optional

from shared.debug_log import debug


class GreenhouseInventorySystem:
    """
    Manages the greenhouse's plant inventory and growth mechanics.

    This is the supply of plants that the player can pick up when
    they visit the greenhouse location.
    """

    def __init__(self):
        # Plant inventory: filename -> count
        self.inventory: Dict[str, int] = {}

        # List of all available plant filenames
        self.all_plants: List[str] = []

        # Config values (set via set_config)
        self.initial_amount = 1
        self.grow_amount = 3
        self.grow_time_min = 30.0
        self.grow_time_max = 60.0
        self.inventory_max = 7

        # Growth timer
        self.grow_timer = 0.0
        self.next_grow_time = 0.0

        # Is the system initialized?
        self.is_initialized = False

    def set_config(self, initial_amount: int, grow_amount: int,
                   grow_time_min: float, grow_time_max: float,
                   inventory_max: int):
        """
        Set greenhouse configuration from map config.

        Args:
            initial_amount: Starting plants per type when game begins
            grow_amount: How many plants grow each growth cycle
            grow_time_min: Minimum seconds between growth cycles
            grow_time_max: Maximum seconds between growth cycles
            inventory_max: Maximum plants per type in inventory
        """
        self.initial_amount = initial_amount
        self.grow_amount = grow_amount
        self.grow_time_min = grow_time_min
        self.grow_time_max = grow_time_max
        self.inventory_max = inventory_max
        debug.info(f"Greenhouse config: initial={initial_amount}, grow={grow_amount}, "
                   f"time={grow_time_min}-{grow_time_max}s, max={inventory_max}")

    def initialize(self):
        """
        Initialize the greenhouse inventory.

        Loads plant list and sets initial inventory amounts.
        """
        self._load_plant_list()
        self._initialize_inventory()
        self._roll_next_grow_time()
        self.is_initialized = True
        debug.info(f"Greenhouse initialized with {len(self.all_plants)} plant types")

    def _load_plant_list(self):
        """Load all available plant filenames from assets folder."""
        plant_folder = Path(__file__).parent.parent.parent / "assets" / "plants" / "one"

        try:
            files = list(plant_folder.glob("*.png"))
            for f in files:
                self.all_plants.append(f.name)
            self.all_plants.sort()
        except Exception as e:
            debug.error(f"Failed to load plant list: {e}")

    def _initialize_inventory(self):
        """Set up starting inventory with initial_amount per plant type."""
        for plant_file in self.all_plants:
            self.inventory[plant_file] = self.initial_amount

    def _roll_next_grow_time(self):
        """Roll a random time until the next growth cycle."""
        self.next_grow_time = random.uniform(self.grow_time_min, self.grow_time_max)
        self.grow_timer = 0.0

    def update(self, dt: float):
        """
        Update the greenhouse system.

        Manages growth timer and triggers plant growth when timer expires.
        """
        if not self.is_initialized:
            return

        self.grow_timer = self.grow_timer + dt

        # Check if growth cycle should trigger
        if self.grow_timer >= self.next_grow_time:
            self._grow_plants()
            self._roll_next_grow_time()

    def _grow_plants(self):
        """
        Grow plants by adding to random plant types.

        Only plants that haven't reached inventory_max can be selected.
        Selects grow_amount random plants to increase by 1.
        """
        # Find plants that still have room to grow
        growable_plants = []
        for plant_file in self.all_plants:
            current_count = self.inventory.get(plant_file, 0)
            if current_count < self.inventory_max:
                growable_plants.append(plant_file)

        if len(growable_plants) == 0:
            debug.debug("No plants can grow - all at max inventory")
            return

        # Select random plants to grow (up to grow_amount)
        grow_count = min(self.grow_amount, len(growable_plants))
        selected_plants = random.sample(growable_plants, grow_count)

        # Grow each selected plant by 1
        for plant_file in selected_plants:
            self.inventory[plant_file] = self.inventory.get(plant_file, 0) + 1

        debug.debug(f"Grew {grow_count} plants: {[p.split('-')[0] for p in selected_plants]}")

    def get_plant_count(self, plant_filename: str) -> int:
        """Get current count of a specific plant in greenhouse inventory."""
        return self.inventory.get(plant_filename, 0)

    def get_total_plants(self) -> int:
        """Get total number of plants in greenhouse inventory."""
        total = 0
        for count in self.inventory.values():
            total = total + count
        return total

    def can_take_plant(self, plant_filename: str) -> bool:
        """Check if a plant can be taken from greenhouse."""
        return self.get_plant_count(plant_filename) > 0

    def take_plant(self, plant_filename: str) -> bool:
        """
        Take a plant from greenhouse inventory.

        Returns True if successful, False if plant not available.
        """
        if not self.can_take_plant(plant_filename):
            return False

        self.inventory[plant_filename] = self.inventory[plant_filename] - 1
        debug.debug(f"Took plant: {plant_filename}, remaining: {self.inventory[plant_filename]}")
        return True

    def return_plant(self, plant_filename: str) -> bool:
        """
        Return a plant to greenhouse inventory.

        Returns True if successful, False if at max capacity.
        """
        current_count = self.inventory.get(plant_filename, 0)

        if current_count >= self.inventory_max:
            debug.debug(f"Cannot return {plant_filename} - at max inventory")
            return False

        self.inventory[plant_filename] = current_count + 1
        debug.debug(f"Returned plant: {plant_filename}, now: {self.inventory[plant_filename]}")
        return True

    def get_inventory_copy(self) -> Dict[str, int]:
        """Get a copy of the current inventory for display purposes."""
        return dict(self.inventory)
