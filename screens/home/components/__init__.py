# Home-specific ECS components
from dataclasses import dataclass
import pygame


@dataclass
class HomeBackground:
    """Background image for a home/interior"""
    image_path: str = ""
    image: pygame.Surface = None


@dataclass
class InteractableObject:
    """An object the player can interact with"""
    name: str = ""
    interaction_type: str = "examine"  # examine, use, talk, pickup
    is_highlighted: bool = False


@dataclass
class NPC:
    """Non-player character that can be talked to"""
    name: str = ""
    portrait_path: str = ""
    portrait: pygame.Surface = None
    dialog_id: str = ""  # Reference to dialog data


@dataclass
class PlayerInHome:
    """Tag component to identify player entity in home screen"""
    pass
