__version__ = "1.0"

import pygame

from pygame import QUIT, KEYDOWN, MOUSEBUTTONDOWN
from pygame.locals import DOUBLEBUF

from game_state import StateManager
from game_state.errors import ExitGame, ExitState

from core.settings import Display
from states import GAME_STATES


# icon = pygame.image.load("assets/icon.ico")
# pygame.display.set_icon(icon)
pygame.mixer.init()
pygame.init()
pygame.display.init()
pygame.display.set_caption("Dew Valley v" + __version__)
pygame.event.set_allowed((QUIT, KEYDOWN, MOUSEBUTTONDOWN))


class Main:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(Display.SCREEN_RESOLUTION, DOUBLEBUF)
        self.screen.set_alpha(None)
        self.state_manager = StateManager(self.screen)
        self.state_manager.load_states(*GAME_STATES)

        # This doesn't work when converting to exe using nuitka-
        # state_paths = get_paths("states/")
        # for state_path in state_paths:
        #    self.state_manager.connect_state_hook(state_path)

    def run(self) -> None:
        self.state_manager.change_state("Game")

        while True:
            try:
                self.state_manager.run_state()
            except ExitState:
                # Stuff you can do before a state is going to be changed / reset.
                pass


if __name__ == "__main__":
    try:
        game = Main()
        game.run()
    except ExitGame:
        pygame.quit()
