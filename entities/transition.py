from typing import Callable

import pygame

from core.settings import Display
from entities.player import Player


class Transition:
    def __init__(
        self, reset: Callable, player: Player, window: pygame.Surface
    ) -> None:
        self.window = window
        self.reset = reset
        self.player = player

        self.image = pygame.Surface(Display.SCREEN_RESOLUTION)
        self.color = 255
        self.speed = -2

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
