# Shared ECS systems used across multiple screens
import esper
from shared.components import Position, Velocity


class MovementSystem(esper.Processor):
    """Updates entity positions based on velocity"""

    def process(self, dt: float):
        for ent, (pos, vel) in esper.get_components(Position, Velocity):
            pos.x = pos.x + vel.vx * dt
            pos.y = pos.y + vel.vy * dt
