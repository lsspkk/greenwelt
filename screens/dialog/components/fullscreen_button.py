import pygame


def draw_fullscreen_button(screen, rect, hover, icon_color):
    """
    Draws a fullscreen button at the given rect.
    :param screen: pygame.Surface
    :param rect: pygame.Rect
    :param hover: bool
    :param icon_color: tuple (R, G, B)
    """
    fs_color = (60, 120, 180) if hover else icon_color
    pygame.draw.rect(screen, fs_color, rect, border_radius=6)
    # Draw a simple rectangle icon for fullscreen
    fullscreen_size = rect.width
    pygame.draw.rect(
        screen,
        (200, 200, 200),
        rect.inflate(-int(fullscreen_size * 0.35), -
                     int(fullscreen_size * 0.35)),
        2,
        border_radius=3
    )
    # Optionally, add arrows to indicate fullscreen
    pygame.draw.polygon(screen, (200, 200, 200), [
        (rect.left + int(fullscreen_size * 0.17),
         rect.top + int(fullscreen_size * 0.17)),
        (rect.left + int(fullscreen_size * 0.3),
         rect.top + int(fullscreen_size * 0.17)),
        (rect.left + int(fullscreen_size * 0.17),
         rect.top + int(fullscreen_size * 0.3))
    ])
    pygame.draw.polygon(screen, (200, 200, 200), [
        (rect.right - int(fullscreen_size * 0.17),
         rect.bottom - int(fullscreen_size * 0.17)),
        (rect.right - int(fullscreen_size * 0.3),
         rect.bottom - int(fullscreen_size * 0.17)),
        (rect.right - int(fullscreen_size * 0.17),
         rect.bottom - int(fullscreen_size * 0.3))
    ])
