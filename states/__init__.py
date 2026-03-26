from __future__ import annotations

from typing import TYPE_CHECKING

from states.game import Game

if TYPE_CHECKING:
    from states.base import BaseState

GAME_STATES: tuple[type[BaseState], ...] = (Game,)
