from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from game_state import StateManager
from pygame import KEYDOWN, MOUSEBUTTONDOWN, QUIT
from pygame.locals import DOUBLEBUF

from core.settings import Display
from states import GAME_STATES
from states.base import BaseState

if TYPE_CHECKING:
    from pygame import Clock, Surface


__version__ = "2.1.0b"


pygame.mixer.init()
pygame.init()
pygame.display.init()
pygame.display.set_caption("Dew Valley v" + __version__)
pygame.event.set_allowed((QUIT, KEYDOWN, MOUSEBUTTONDOWN))


class Main:
    def __init__(self) -> None:
        self.clock: Clock = pygame.time.Clock()
        self.screen: Surface = pygame.display.set_mode(
            Display.SCREEN_RESOLUTION, DOUBLEBUF
        )
        self.state_manager: StateManager[BaseState] = StateManager(
            bound_state_type=BaseState, window=self.screen
        )

        self.screen.set_alpha(None)
        self.state_manager.load_states(*GAME_STATES)

    def run(self) -> None:
        self.state_manager.change_state("Game")

        assert self.state_manager.current_state

        while self.state_manager.is_running:
            dt = self.clock.tick(Display.FPS) / 1000

            for event in pygame.event.get():
                self.state_manager.current_state.process_event(event)

            self.state_manager.current_state.process_update(dt)


if __name__ == "__main__":
    game = Main()
    game.run()
