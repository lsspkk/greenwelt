# Character sprite with animation and rotation
import math
import pygame


class Character:
    """Handles loading, animating, and drawing the player character sprite.

    The sprite images should face UP (toward top center of image).
    The character rotates to face its movement direction.
    When moving, it alternates between two frames for animation.
    When stopped, it shows frame 1.
    """

    def __init__(self, frame1_path: str, frame2_path: str, size: int = 48):
        self.size = size
        self.frame1_original = self._load_frame(frame1_path, size)
        self.frame2_original = self._load_frame(frame2_path, size)
        self.angle_degrees = 0.0
        self.anim_timer = 0.0
        self.anim_speed = 0.15  # seconds per frame
        self.current_frame_index = 0

    def _load_frame(self, path: str, size: int) -> pygame.Surface:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.scale(image, (size, size))
        return image

    def update(self, vx: float, vy: float, dt: float, facing_dx: float = None, facing_dy: float = None):
        """Update rotation angle and animation frame.

        Args:
            vx: velocity x
            vy: velocity y
            dt: delta time in seconds
            facing_dx: direction to face (x component)
            facing_dy: direction to face (y component)
        """
        is_moving = abs(vx) > 0.1 or abs(vy) > 0.1

        # Use facing direction for angle (falls back to velocity if not provided)
        if facing_dx is not None and facing_dy is not None:
            # Calculate angle from facing direction
            self.angle_degrees = -math.degrees(math.atan2(facing_dx, -facing_dy))
        elif is_moving:
            # Fall back to velocity-based rotation
            self.angle_degrees = -math.degrees(math.atan2(vx, -vy))

        if is_moving:

            # Animate between frames
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                self.current_frame_index = 1 - self.current_frame_index
        else:
            # Stopped: show frame 1, keep last angle
            self.current_frame_index = 0
            self.anim_timer = 0.0

    def draw(self, surface: pygame.Surface, screen_x: int, screen_y: int, zoom: float):
        """Draw the character at the given screen position.

        Args:
            surface: screen to draw on
            screen_x: screen x position (center)
            screen_y: screen y position (center)
            zoom: camera zoom factor
        """
        # Pick frame
        if self.current_frame_index == 0:
            frame = self.frame1_original
        else:
            frame = self.frame2_original

        # Scale by zoom
        scaled_size = int(self.size * zoom)
        if scaled_size < 4:
            return
        scaled = pygame.transform.scale(frame, (scaled_size, scaled_size))

        # Rotate
        rotated = pygame.transform.rotate(scaled, self.angle_degrees)

        # Center on position
        rect = rotated.get_rect(center=(screen_x, screen_y))
        surface.blit(rotated, rect)
