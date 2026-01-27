import pygame


def draw_fullscreen_button(screen, rect, hover, icon_color):
    """
    Draws a fullscreen button at 1.5x the given rect size.
    :param screen: pygame.Surface
    :param rect: pygame.Rect
    :param hover: bool
    :param icon_color: tuple (R, G, B)
    """
    # Scale rect by 1.5x from its center
    scale = 1.5
    center = rect.center
    new_width = int(rect.width * scale)
    new_height = int(rect.height * scale)
    big_rect = pygame.Rect(0, 0, new_width, new_height)
    big_rect.center = center

    fs_color = (60, 120, 180) if hover else icon_color
    pygame.draw.rect(screen, fs_color, big_rect, border_radius=9)
    # Draw a simple rectangle icon for fullscreen
    fullscreen_size = big_rect.width
    pygame.draw.rect(
        screen,
        (200, 200, 200),
        big_rect.inflate(-int(fullscreen_size * 0.35), -
                         int(fullscreen_size * 0.35)),
        2,
        border_radius=4
    )
    # Optionally, add arrows to indicate fullscreen
    pygame.draw.polygon(screen, (200, 200, 200), [
        (big_rect.left + int(fullscreen_size * 0.17),
         big_rect.top + int(fullscreen_size * 0.17)),
        (big_rect.left + int(fullscreen_size * 0.3),
         big_rect.top + int(fullscreen_size * 0.17)),
        (big_rect.left + int(fullscreen_size * 0.17),
         big_rect.top + int(fullscreen_size * 0.3))
    ])
    pygame.draw.polygon(screen, (200, 200, 200), [
        (big_rect.right - int(fullscreen_size * 0.17),
         big_rect.bottom - int(fullscreen_size * 0.17)),
        (big_rect.right - int(fullscreen_size * 0.3),
         big_rect.bottom - int(fullscreen_size * 0.17)),
        (big_rect.right - int(fullscreen_size * 0.17),
         big_rect.bottom - int(fullscreen_size * 0.3))
    ])
