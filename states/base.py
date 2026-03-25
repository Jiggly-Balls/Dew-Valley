from __future__ import annotations

from typing import TYPE_CHECKING

from game_state import State
from game_state.utils import MISSING

if TYPE_CHECKING:
    from pygame import Event, Surface


class BaseState(State["BaseState"]):
    window: Surface = MISSING

    def process_event(self, event: Event) -> None: ...

    def process_update(self, dt: float) -> None: ...
