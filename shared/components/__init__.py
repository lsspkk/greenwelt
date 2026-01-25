# Shared ECS components used across multiple screens
from dataclasses import dataclass


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
