from __future__ import annotations

from typing import TYPE_CHECKING

from states.game import Game

if TYPE_CHECKING:
    from typing import Tuple

    from game_state import State

GAME_STATES: Tuple[type[State], ...] = (Game,)
