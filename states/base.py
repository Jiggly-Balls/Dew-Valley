from __future__ import annotations

from typing import TYPE_CHECKING

from game_state import State
from game_state.utils import MISSING

if TYPE_CHECKING:
    from pygame import Surface


class BaseState(State["BaseState"]):
    window: Surface = MISSING
