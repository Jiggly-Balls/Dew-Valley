from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from game_state import State
from game_state.utils import MISSING

if TYPE_CHECKING:
    from pygame import Event, Surface


__all__ = ("BaseState",)


class BaseState(State["BaseState"]):
    window: Surface = MISSING

    def process_event(self, event: Event) -> None:
        if event.type == pygame.QUIT:
            self.manager.is_running = False

    def process_update(self, dt: float) -> None: ...
