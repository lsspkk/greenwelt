# Road collision system - prevents movement off roads

import esper
from shared.components import Position, Velocity
from screens.map.components import RoadLayer, PlayerOnMap


class RoadCollisionSystem(esper.Processor):
    """Prevents entities from moving off roads (works in world coordinates)"""

    def process(self, dt: float):
        # Get road layer
        road_layer = None
        for ent, (road,) in esper.get_components(RoadLayer):
            road_layer = road
            break

        if road_layer is None or road_layer.road_mask is None:
            return

        # Check player movement against roads
        for ent, (pos, vel, player) in esper.get_components(Position, Velocity, PlayerOnMap):
            if vel.vx == 0.0 and vel.vy == 0.0:
                continue

            # Calculate next position (in world coordinates)
            next_x = pos.x + vel.vx * dt
            next_y = pos.y + vel.vy * dt

            # Check if next position is on a road
            if not road_layer.is_on_road(next_x, next_y):
                # Stop movement
                vel.vx = 0.0
                vel.vy = 0.0
