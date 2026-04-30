from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core.settings import Display
from entities.player import Player

if TYPE_CHECKING:
    from typing import Callable
    from pygame import Surface


class Transition:
    def __init__(
        self, reset: Callable[[], None], player: Player, window: pygame.Surface
    ) -> None:
        self.window: Surface = window
        self.reset: Callable[[], None] = reset
        self.player: Player = player

        self.image: Surface = pygame.Surface(Display.SCREEN_RESOLUTION)
        self.color: int = 255
        self.speed: int = -2

    def run(self) -> None:
        self.color += self.speed
        if self.color <= 0:
            self.speed *= -1
            self.color = 0
            self.reset()

        if self.color > 255:
            self.color = 255
            self.player.sleep = False
            self.speed = -2

        self.image.fill((self.color, self.color, self.color))
        self.window.blit(
            self.image, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )
